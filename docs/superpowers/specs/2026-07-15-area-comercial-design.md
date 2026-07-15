# Diseño — Sprint 2: Área Comercial

**Fecha:** 2026-07-15
**Origen:** `Pendientes.md`, sección "Sprint 2 — Área Comercial".
**Estado:** Aprobado por el usuario, listo para plan de implementación.

## Contexto

El MVP (cerrado 2026-07-15) solo implementó el área Civil/Familia. `ComercialStrategy` existe como
stub en `app/services/area_strategy.py` (línea ~92) y lanza `AreaNoImplementadaError`. El área
"COMERCIAL" ya está registrada en `app/engine/liquidation/registry.py` y en el enum `AreaDerecho` de
`database/models.py` — solo falta la implementación real y habilitarla en la GUI.

Este sprint reutiliza toda la infraestructura ya construida para Civil/Familia (`EffectiveRateConverter`,
`MemoryRateProvider`, `UniversalLiquidationService`, patrón de `AreaStrategy`) y no requiere tocar el
núcleo de liquidación (`LiquidationCore`) ni el motor de asignación de pagos (`AllocationEngine`).

## Decisiones tomadas con el usuario

Estas decisiones estaban explícitamente abiertas en `Pendientes.md` o surgieron durante el diseño:

1. **Tope de usura → excepción, no truncamiento.** Si la tasa pactada (remuneratoria o moratoria)
   supera 1.5×IBC, se lanza `TasaUsurariaError` y la liquidación se rechaza. No se trunca
   silenciosamente.
2. **Sin IBC automático por defecto.** Cada obligación comercial debe traer sus propias tasas ya
   resueltas (remuneratoria y moratoria pactadas) — no hay fallback a una constante "IBC vigente" en
   código este sprint. Esto se documenta como pendiente hasta el Sprint 5 (datos históricos).
3. **IBC de referencia para el tope de usura → campo nuevo por obligación.** Como el tope legal es
   1.5×IBC (una tasa de mercado, no la tasa pactada entre las partes), se agrega un campo
   `ibc_vigente_anual` que el abogado diligencia manualmente con el IBC certificado por la
   Superfinanciera para la fecha del caso.
4. **Tasa moratoria → campo nuevo independiente**, no una regla fija de "1.5× la remuneratoria" —
   puede diferir en la realidad contractual.
5. **Split real remuneratorio/moratorio por obligación**, no un solo tramo de tasa por expediente como
   hace Civil hoy. Requiere un campo nuevo `fecha_vencimiento` (distinto de `fecha_origen`).
6. **Anatocismo (Art. 886 C.Co.) diferido.** `CompoundInterest` sigue huérfano. Los campos que haría
   falta agregar al modelo (`hay_demanda_judicial`, `acuerdo_capitalizacion`) y el diseño de UI para
   capturarlos no se resuelven en este sprint — se documenta como pendiente explícito, no se construye.
7. **`bastium.db` se borra y recrea** con el esquema nuevo (solo contenía el registro del smoke test del
   MVP, dato descartable).

## Limitación arquitectónica conocida (no se resuelve en este sprint)

`UniversalLiquidationService.liquidar()` recibe **un solo `rate_provider` compartido para todo el
expediente**, indexado únicamente por fecha calendario — no por obligación
(`app/services/motor_universal.py`, línea 44-47; `MemoryRateProvider.get_rate()` hace un scan lineal por
fecha, sin noción de a qué obligación pertenece un evento).

Esto significa que el split remuneratorio/moratorio por obligación (decisión #5) da resultados correctos
cuando:
- El expediente tiene una sola obligación comercial, o
- Todas las obligaciones del expediente comparten tramos de fecha que no se solapan con tasas distintas.

Si dos obligaciones del mismo expediente tienen `fecha_vencimiento` distintas y tasas distintas, y sus
períodos remuneratorio/moratorio se solapan en el calendario, el `MemoryRateProvider` devolverá la tasa
del primer período que matchee (orden de inserción/orden por `start_date`), no necesariamente la tasa
correcta para esa obligación específica. Esta es la misma limitación que ya tiene `CivilFamiliaStrategy`
hoy (documentada en el backlog técnico de `Pendientes.md`: "Múltiples tasas de interés simultáneas por
expediente"). No se resuelve aquí — resolverla requeriría que `LiquidationCore`/`UniversalLiquidationService`
asocien tasa a evento en vez de a fecha global, un cambio de arquitectura compartida fuera del alcance de
este sprint.

**Mitigación de alcance:** los tests y el smoke test de este sprint cubren el caso de una obligación por
expediente (el caso de uso real más común: un pagaré, una factura). El caso multi-obligación con tasas
solapadas queda como limitación documentada, igual que en Civil.

## Cambios de modelo de datos

`database/models.py`, clase `Obligacion` — tres campos nuevos:

| Campo | Tipo | Nullable | Notas |
|---|---|---|---|
| `tasa_moratoria_anual` | `Numeric(9,4)` | Sí (obligatorio solo para Comercial, validado en `ComercialStrategy`) | Tasa moratoria pactada, % efectivo anual |
| `fecha_vencimiento` | `Date` | Sí (obligatorio solo para Comercial) | Fecha en que la obligación se hace exigible / termina el remuneratorio |
| `ibc_vigente_anual` | `Numeric(9,4)` | Sí (obligatorio solo para Comercial) | IBC certificado por la Superfinanciera para la fecha del caso, usado solo para el tope de usura |

Los tres campos son genéricos a nivel de tabla (no exclusivos de Comercial) para no requerir una tabla
separada, pero solo `ComercialStrategy` los exige como obligatorios — Civil/Familia los ignora.

`database/bastium.db` se borra; `init_db()` lo recrea con el esquema nuevo en el próximo arranque.

## Excepciones nuevas

`app/core/exceptions.py`:

```python
class TasaUsurariaError(Exception):
    """Se lanza cuando una tasa pactada (remuneratoria o moratoria) supera 1.5x el IBC vigente."""
```

## Validador de usura

Nuevo archivo `app/engine/interest/usury_validator.py`:

```python
def validar_tasa_usura(tasa_pactada: Decimal, ibc_vigente: Decimal, etiqueta: str) -> None:
    """Lanza TasaUsurariaError si tasa_pactada > 1.5 * ibc_vigente."""
```

Se llama dos veces por obligación comercial: una para `tasa_efectiva_anual` (remuneratoria) y otra para
`tasa_moratoria_anual` (moratoria) — la ley de usura colombiana (Ley 45/1990 art. 72) topa ambas, no solo
la moratoria. El mensaje de la excepción debe nombrar cuál tasa (`etiqueta`) excede el tope y por cuánto.

## `ComercialStrategy.liquidar()`

`app/services/area_strategy.py`, reemplaza el stub actual (línea ~92-96).

Flujo por obligación, antes de construir eventos:
1. Validar que `tasa_efectiva_anual`, `tasa_moratoria_anual`, `fecha_vencimiento`, `ibc_vigente_anual`
   no sean `None` → `ValueError` con mensaje claro si falta alguno (mismo patrón que el guard de lista
   vacía que ya usa `CivilFamiliaStrategy`, línea 34-35).
2. `validar_tasa_usura(tasa_efectiva_anual, ibc_vigente_anual, "remuneratoria")`.
3. `validar_tasa_usura(tasa_moratoria_anual, ibc_vigente_anual, "moratoria")`.

Construcción de eventos: igual patrón que `CivilFamiliaStrategy._eventos_de_obligacion` (PUNTUAL → un
evento en `fecha_origen`; RECURRENTE → reutiliza el mismo scheduler de cuotas mensuales por `dia_pago`).

Construcción del rate provider (reemplaza `_construir_rate_provider` de Civil por una versión Comercial):
para cada obligación, se agregan hasta dos `RatePeriod` al `MemoryRateProvider` compartido:
- Remuneratorio: `[fecha_origen, fecha_vencimiento]` a `EffectiveRateConverter.annual_to_daily(tasa_efectiva_anual)`.
- Moratorio: `[fecha_vencimiento + 1 día, fecha_corte]` a `EffectiveRateConverter.annual_to_daily(tasa_moratoria_anual)` —
  se omite este tramo si `fecha_vencimiento >= fecha_corte` (la obligación todavía no está en mora).

Pagos: igual que Civil (`Payment` por cada abono).

Delegación final: igual que Civil, `UniversalLiquidationService().liquidar(eventos_causacion=...,
pagos=..., fecha_corte=..., rate_provider=...)`.

**Alcance del split remuneratorio/moratorio — solo `PUNTUAL`.** El caso comercial real y frecuente es
puntual (pagaré, factura, letra de cambio): `fecha_vencimiento` tiene un sentido claro de 1 a 1 con la
obligación. Para `RECURRENTE` (poco común en Comercial — ej. venta a plazos), el scheduler genera una
cuota por mes con su propia fecha, y un solo `fecha_vencimiento` a nivel de `Obligacion` no representa
el vencimiento de cada cuota individual. Este sprint no resuelve ese caso: si `tipo == RECURRENTE`,
`ComercialStrategy` usa el mismo patrón de tasa única que `CivilFamiliaStrategy` (un solo tramo con la
tasa moratoria, ya que toda cuota generada se considera exigible desde su fecha) y documenta el split
per-cuota como pendiente explícito, no como bug. La validación de los cuatro campos obligatorios y de
usura aplica igual para ambos tipos.

## Incompatibilidad con indexación IPC

`AreaStrategy` (clase base) gana un atributo de clase `soporta_indexacion_ipc: bool = True`.
`ComercialStrategy` lo sobreescribe a `False`. `CivilFamiliaStrategy` queda con el default `True`
(explícito, no implícito).

Esto no bloquea nada hoy en tiempo de ejecución (la indexación IPC no está conectada a ningún área
todavía — Sprint 8), pero deja la regla como dato consultable y con test explícito, en vez de solo un
comentario, tal como pide `Pendientes.md`. Cuando el Sprint 8 conecte la indexación, debe consultar este
atributo antes de aplicarla.

## GUI

- `app/core/constants.py`:
  - `AREAS_DERECHO`: cambiar `("COMERCIAL", "Comercial", False)` → `("COMERCIAL", "Comercial", True)`.
  - Nueva constante `CATEGORIAS_COMERCIAL`: lista de categorías comerciales (capital de pagaré, capital
    de letra de cambio, capital de cheque, capital de factura). Reutiliza el código `CAPITAL_PAGARE` que
    ya existe en `LiquidationCore._capital_concepts`; los códigos nuevos (`CAPITAL_LETRA_CAMBIO`,
    `CAPITAL_CHEQUE`, `CAPITAL_FACTURA`) se agregan a ese set (`app/engine/liquidation/engine.py`, línea
    ~28-32) para que cuenten como capital.
- `app/views/obligaciones.py` (`ObligacionFormDialog`):
  - El constructor pasa a aceptar el área del expediente (o el propio `Expediente`) además de
    `expediente_id`, para saber qué lista de categorías mostrar y si mostrar los campos Comercial.
  - Cuando el área es "COMERCIAL": usa `CATEGORIAS_COMERCIAL` en vez de `CATEGORIAS_CIVIL_FAMILIA`, y
    muestra tres campos adicionales: "Tasa moratoria anual (%)", "Fecha de vencimiento", "IBC vigente
    aplicable (%)". Estos tres campos quedan ocultos (y no se envían) para Civil/Familia.
  - `guardar()` incluye los tres campos nuevos en el `Obligacion(...)` construido cuando aplica.
- `app/views/expediente_detalle.py` (`ExpedienteDetallePage`):
  - `_abrir_dialogo_obligacion` pasa el área del expediente al diálogo.
  - `_liquidar()`: agrega un `except TasaUsurariaError` junto al `except AreaNoImplementadaError` ya
    existente, mostrando el mensaje en el mismo `QMessageBox`.

## Testing

- `tests/services/test_area_strategy.py`:
  - Quitar `("COMERCIAL", ComercialStrategy)` del parametrize de
    `test_areas_no_implementadas_lanzan_error_claro_al_liquidar`.
  - Nueva clase `TestComercialStrategy` con casos (mismo estilo que los de Civil):
    - Obligación puntual sin abonos, con remuneratoria/moratoria distintas y `fecha_corte` posterior a
      `fecha_vencimiento` — verificar que el tramo antes del vencimiento usa la tasa remuneratoria y el
      tramo después usa la moratoria (comparar interés acumulado contra un cálculo manual).
    - Obligación puntual con abono parcial.
    - Tasa moratoria pactada por encima de 1.5×IBC → `TasaUsurariaError`.
    - Tasa remuneratoria pactada por encima de 1.5×IBC → `TasaUsurariaError`.
    - Falta alguno de los cuatro campos comerciales obligatorios → `ValueError`.
    - `fecha_corte` anterior a `fecha_vencimiento` (obligación aún no en mora) → sin tramo moratorio, solo
      interés remuneratorio.
    - Obligación `RECURRENTE` comercial → confirma que usa tasa única (moratoria) igual que Civil, sin
      split por cuota (comportamiento documentado como alcance reducido, no bug).
- Nuevo `tests/engine/interest/test_usury_validator.py`: casos límite (exactamente en el tope, justo
  encima, justo debajo).
- `tests/views/test_obligaciones.py`: actualizar para el nuevo constructor de `ObligacionFormDialog` y
  agregar un caso que guarda una obligación Comercial con los tres campos nuevos.
- Smoke test manual (igual patrón que la Tarea 17 del MVP): crear expediente Comercial, agregar
  obligación (pagaré, remuneratoria/moratoria/IBC/vencimiento), agregar abono, liquidar, confirmar
  resultado sin error y con saldo menor al valor original. Repetir con una tasa que exceda el tope de
  usura y confirmar que la GUI muestra el error en vez de crashear.

## Fuera de alcance (explícito)

- TRM/moneda extranjera (Sprint 12).
- Costas y agencias en derecho (Sprint 4).
- Carga automática de tramos históricos de IBC/usura (Sprint 5).
- Anatocismo condicionado Art. 886 C.Co. (diferido, ver decisión #6).
- Resolver la limitación de "una tasa por fecha, no por obligación" en `MemoryRateProvider`/
  `UniversalLiquidationService` para expedientes multi-obligación con tramos solapados (limitación
  heredada de Civil, no introducida por este sprint).

## Definición de hecho

- `ComercialStrategy` liquida obligaciones comerciales reales (puntuales, con y sin abonos, con split
  remuneratorio/moratorio) con TDD, siguiendo el patrón de `tests/services/test_area_strategy.py`.
- Tests de validación de usura (remuneratoria y moratoria) pasando y fallando en los límites correctos.
- Área "Comercial" seleccionable y operable end-to-end desde la GUI (smoke test manual).
- Suite completa (81 tests actuales + los nuevos de este sprint) sigue en verde.
- `README.md` y `docs/GUIA_USUARIO.md` actualizados: sacar Comercial de "🚧 en desarrollo" y documentar
  cómo capturar una obligación comercial (remuneratoria, moratoria, vencimiento, IBC) igual que se
  documentó Civil/Familia.
- `Pendientes.md`: marcar el anatocismo condicionado como pendiente explícito separado (no resuelto en
  este sprint) para que quede claro que `CompoundInterest` sigue huérfano a propósito.
