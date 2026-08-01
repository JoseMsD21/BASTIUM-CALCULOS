# Diseño — Sprint 21: Múltiples tasas de interés simultáneas por expediente

**Fecha:** 2026-07-31
**Origen:** `Pendientes.md`, sección "Sprint 21 — Múltiples tasas de interés simultáneas por expediente"
(línea 1608). Limitación documentada desde el Sprint 2 (ver
`docs/superpowers/specs/2026-07-15-area-comercial-design.md`, sección "Limitación arquitectónica
conocida").
**Estado:** Aprobado por el usuario, listo para plan de implementación.

## Contexto

`Pendientes.md` describe el síntoma así: "`CivilFamiliaStrategy` toma la tasa de la primera obligación y
la usa para todo el expediente" y sugiere como arreglo extender `MemoryRateProvider` para indexar por
`obligacion_id` además de por fecha.

Al revisar el motor real (`app/engine/liquidation/engine.py`), el problema es más profundo que eso:

- `LiquidationCore` mantiene **un solo saldo agregado** (`PendingDebt`: principal/interés/indexación) para
  *todo* el expediente — no uno por obligación.
- `_accrue_time_passage()` busca **una sola tasa por día de calendario** (`rate_provider.get_rate(fecha)`)
  y la aplica a ese principal agregado. No hay ninguna noción de "a qué obligación pertenece cada peso del
  principal acumulado".
- `Event` (lo que produce cada obligación al generar sus eventos de causación) no lleva `obligacion_id` —
  se pierde el rastro de origen apenas se generan los eventos.
- `Abono` (el modelo de base de datos, `database/models.py:148`) **sí** tiene `obligacion_id`, pero se
  descarta al construir el `Payment` de dominio (`app/domain/obligation/payment.py`) en las 4 estrategias
  afectadas — hoy todos los abonos del expediente se aplican como una sola bolsa contra el saldo agregado,
  sin importar a qué obligación se registraron.

Por esto, simplemente indexar `MemoryRateProvider` por obligación **no** resuelve el caso de fechas
solapadas: aunque se supiera "la tasa de la obligación X hoy", solo existe **un** principal agregado al
que aplicarla — no hay forma de aplicar 12% a una porción y 20% a otra porción del mismo número
simultáneamente. La Definición de Hecho del sprint (2+ obligaciones, tasas distintas, fechas solapadas,
cada una liquidando con su propia tasa) exige separar el seguimiento de saldo **por obligación** dentro
del motor.

Se verificó además, por búsqueda exhaustiva en `tests/`, que **no existe ningún test hoy que combine 2+
obligaciones con abonos** en la misma liquidación — el comportamiento de "bolsa única de abonos entre
obligaciones" nunca estuvo validado por regresión, así que cambiarlo no rompe ninguna expectativa
existente.

## Decisiones tomadas con el usuario

1. **Un `LiquidationCore` por obligación, fusionados al reportar** (en vez de rediseñar
   `LiquidationCore` para sub-cuentas internas por `obligacion_id`). Razón: reutiliza el núcleo ya
   probado en los Sprints 1, 2, 3, 4, 8, 9 sin tocarlo → riesgo de regresión bajo. El costo es una
   fusión de historiales, que vive en una capa nueva por fuera del núcleo.
2. **Cada abono paga solo su propia obligación**, usando el `obligacion_id` que ya existe en `Abono`
   — no una regla nueva de reparto (más antiguo primero, prorrateo, etc.). Es la lectura jurídica más
   defendible (un pago se imputa a la deuda que salda) y coincide con un dato que la base de datos ya
   modela pero que el motor ignoraba.

## Arquitectura

`LiquidationCore`, `BalanceEngine` y `AllocationEngine` **no se modifican**. Se añade una capa de
orquestación nueva, a nivel de módulo en `app/services/area_strategy.py` (mismo patrón que la función
compartida `_evento_costas_procesales` ya existente), usada por las 4 estrategias afectadas:

```python
def _liquidar_por_obligacion(
    obligaciones: List,
    abonos: List,
    fecha_corte: date,
    eventos_fn: Callable[[Obligacion], List[Event]],
    rate_provider_fn: Callable[[Obligacion, date], RateProvider],
) -> LiquidationResult:
    ...

def _fusionar_resultados(resultados: List[LiquidationResult], fecha_corte: date) -> LiquidationResult:
    ...
```

Flujo por estrategia (reemplaza la construcción actual de `eventos_causacion`/`rate_provider` únicos):

1. Por cada obligación `o`: se arma su propia lista de eventos (`eventos_fn(o)`, reutilizando los métodos
   `_eventos_de_obligacion` ya existentes, sin cambios), su propio `RateProvider` de una sola obligación
   (`rate_provider_fn(o, fecha_corte)`), y sus propios abonos
   (`[a for a in abonos if a.obligacion_id == o.id]`).
2. Se corre `UniversalLiquidationService().liquidar(...)` **una vez por obligación** → N
   `LiquidationResult` independientes, cada uno con su saldo correcto a su propia tasa.
3. `_fusionar_resultados` combina los N historiales en una sola línea de tiempo cronológica, para que el
   reporte del expediente se siga viendo como una sola tabla (igual que hoy).

### Algoritmo de fusión

- **Orden:** todas las filas "regulares" (no de cierre) de los N resultados se intercalan por fecha.
  Empate → orden de la obligación en la lista recibida, luego orden de emisión original dentro de esa
  obligación (determinista, usando `sorted()` estable).
- **Montos puntuales sin cambio:** `interest_amount`, `indexation_amount` y `payment_amount` de cada fila
  ya son montos de ese evento puntual — sumarlos sobre la lista fusionada sigue dando el total correcto
  del expediente. `LiquidationResult.total_interest_accrued()` / `total_payments_applied()` no requieren
  cambios.
- **Saldo consolidado por fila:** `capital_base` y `balance.debt` son fotos de saldo en un instante, así
  que sí se recalculan. Se mantiene un diccionario `{indice_obligacion: PendingDebt}` con el último
  estado conocido de cada obligación; al procesar cada fila fusionada (en orden cronológico) se actualiza
  la entrada de esa obligación y se recalcula el saldo consolidado de la fila como la suma de las N
  últimas entradas conocidas (`PendingDebt(0,0,0)` para obligaciones que aún no han tenido ningún
  evento).
- **Cierre único:** cada sub-resultado genera su propia fila "Corte final de liquidación"
  (`event_type == "LIQUIDATION_CUTOFF"`). Esas N filas se descartan de la intercalación y se sintetiza
  **una sola** fila de cierre consolidada al final, usando `resultado_i.final_balance()` de cada
  sub-resultado (que ya incluye el interés acumulado hasta el corte, catch-up incluido). Como distintas
  obligaciones pueden tener tasas distintas vigentes en el corte, esa fila no reporta "una tasa": deja
  `interest_rate = 0.00` y `rate_source = "Varias tasas — ver detalle por fila arriba"`. Esta fila solo
  se agrega si al menos un sub-resultado tuvo su propia fila de cierre (mismo criterio que
  `LiquidationCore.process()` usa hoy: `last_event_date < fecha_corte`).
- **Guard nuevo:** un abono cuyo `obligacion_id` no corresponde a ninguna obligación de las pasadas a
  `liquidar()` → `ValueError` explícito. No debería ocurrir por la FK de la base de datos, pero es una
  validación barata y evita que un abono se pierda silenciosamente.
- **Caso N=1 (una sola obligación, el caso de hoy):** la fusión de un solo resultado es la identidad — no
  hay intercalación real que hacer, y la única fila de cierre de esa obligación pasa a ser la fila de
  cierre consolidada tal cual (mismo `interest_rate`/`rate_source` que hoy, porque solo hay una tasa).
  Esto **garantiza estructuralmente** — no como algo a verificar aparte — que los expedientes de una sola
  obligación producen resultados idénticos a los actuales.

## Alcance por área

| Estrategia | ¿Afectada? | Razón |
|---|---|---|
| `CivilFamiliaStrategy` | Sí | `_construir_rate_provider` hoy usa `obligaciones[0].tasa_efectiva_anual` para todo el expediente, ignorando el resto. |
| `ComercialStrategy` | Sí | Ya arma tramos remuneratorio/moratorio por obligación, pero un solo `MemoryRateProvider` compartido causa que tramos de distintas obligaciones que se solapan en fecha se "tapen" entre sí (el primer tramo que matchea por fecha gana, sin importar la obligación). |
| `SancionatorioStrategy` | Sí | Mismo patrón que Civil: usa `obligaciones[0].tasa_efectiva_anual` para todas. |
| `HonorariosStrategy` | Sí | Mismo patrón que Civil/Sancionatorio. |
| `LaboralStrategy` | No | Por diseño liquida un solo contrato (una obligación) por expediente — ya lanza `ValueError` si hay más de una. Nunca tuvo esta limitación. |
| `TributarioStrategy` | No | Su tasa moratoria (E.T. art. 635) es una tasa legal automática, igual para todas las obligaciones del expediente — no viene de `obligacion.tasa_efectiva_anual`. No existe el concepto de "tasas distintas por obligación" en esta área. |

En las 4 áreas afectadas, `_construir_rate_provider(obligaciones, fecha_corte)` (que arma un provider
para todo el expediente) se reemplaza por `_construir_rate_provider_obligacion(obligacion, fecha_corte)`
(una sola obligación) — más simple que la versión actual, no más compleja. En `ComercialStrategy` esto
además elimina el bucle sobre `obligaciones` dentro de la construcción del provider.

**Nota de coordinación con Sprint 22** (`Pendientes.md`, tarea 4, línea 1686-1692): ese punto ya anticipaba
que si el Sprint 21 se hace primero, `_construir_rate_provider` "cambia de fondo". Con este diseño,
`_construir_rate_provider_obligacion` sigue siendo candidato a subir a la clase base o extraerse como
función compartida entre Civil/Sancionatorio/Honorarios (que comparten el mismo patrón de "un solo tramo
plano por obligación") — se deja explícitamente para el Sprint 22, no se hace aquí para no mezclar un
cambio estructural con limpieza de duplicación.

## Alcance explícitamente excluido

- Cambiar el modelo de datos de `Obligacion` (cada obligación ya tiene su propia `tasa_efectiva_anual`).
- Tocar `LiquidationCore`, `BalanceEngine` o `AllocationEngine`.
- `LaboralStrategy` y `TributarioStrategy` (no afectadas, ver tabla de alcance).
- Cualquier regla de reparto de abonos entre obligaciones distinta de "cada abono paga la obligación a la
  que fue registrado" (decisión ya tomada).
- Subir `_construir_rate_provider_obligacion` a la clase base / deduplicarla entre estrategias (queda para
  Sprint 22, coordinación explícita arriba).

## Plan de pruebas / Definición de Hecho

- Test por cada una de las 4 áreas afectadas: expediente con 2+ obligaciones a tasas distintas y fechas
  solapadas, verificando que cada una acumula interés con su propia tasa (no la de la primera obligación,
  no una tasa "ganadora" por orden de fecha).
- Test de abonos: un abono registrado contra la obligación A no debe afectar el saldo de la obligación B
  en el mismo expediente.
- Test de guard: abono con `obligacion_id` que no pertenece a ninguna obligación del expediente →
  `ValueError`.
- Test de fila de cierre consolidada: expediente con 2 obligaciones a tasas distintas, verificar que
  `resultado.final_balance()` es la suma correcta de ambas y que solo hay una fila de cierre en
  `resultado.items`.
- Suite completa en verde, **sin cambios de resultado en los tests existentes de expedientes de una sola
  obligación** (garantizado estructuralmente por el caso N=1 de la fusión, ver arriba — se verifica
  corriendo la suite, no se espera tener que tocar ningún test existente).

## Riesgos

- Bajo para el núcleo compartido (`LiquidationCore` no se toca).
- Cambio de comportamiento para expedientes multi-obligación **con abonos**: hoy los abonos se aplican
  como bolsa única del expediente; después del cambio, cada abono paga solo su propia obligación. Es un
  cambio de resultado numérico para ese caso específico, pero es un cambio deliberado (decisión tomada con
  el usuario) y no hay ningún test existente que dependa del comportamiento anterior.
