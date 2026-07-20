# Diseño — Sprint 11a: Motores de Interés Moratorio Tributario y Renta Líquida Gravable

**Fecha:** 2026-07-20
**Origen:** `Pendientes.md`, Sprint 11 — Derecho Tributario (DIAN).

## Contexto y decisión de alcance

El Sprint 11 completo (modelo de Obligación Tributaria, depuración de renta líquida, sanciones,
interés moratorio, imputación tributaria) es un dominio jurídico nuevo para BASTIUM (0% implementado,
ningún archivo bajo `app/engine/tax/` existe hoy — confirmado por grep). El propio `Pendientes.md`
marca este sprint como el menos detallado a propósito, pidiendo confirmar alcance con el usuario antes
de planificar en detalle.

Decisiones tomadas con el usuario durante el brainstorming (no asumidas unilateralmente):

1. **Recorte de alcance ("Sprint 11a")**: de las 5 piezas sugeridas en `Pendientes.md`, este sprint
   construye únicamente las dos que no tienen ningún bloqueo de datos: el motor de interés moratorio
   tributario (E.T. art. 635) y el motor de depuración de Renta Líquida Gravable. El motor de sanciones
   (bloqueado por la tabla histórica de UVT, pendiente desde el Sprint 5) y la imputación tributaria de
   pagos quedan explícitamente diferidos a un futuro "Sprint 11b".
2. **Sin wiring de área**: este sprint construye solo los motores de cálculo, sin `TributarioStrategy`,
   sin registrar el área "Tributario" en `AREAS_DERECHO` (`app/core/constants.py`), y sin tocar la GUI —
   mismo patrón que `IPCIndexation` (Sprint 5) quedó standalone hasta que el Sprint 8 lo conectó. Evita
   exponer al usuario final un área a medias en el selector de la GUI.
3. **Pérdida líquida**: si la Renta Líquida (antes de restar rentas exentas) da negativa, la Renta
   Líquida Gravable se fija en 0 en vez de dejar que el resultado quede negativo — refleja la práctica
   real de que no puede existir una base gravable negativa. Este mismo tope se aplica también si el
   resultado quedara negativo después de restar las rentas exentas (extensión directa del mismo
   principio, no una decisión nueva).

## Código existente a reutilizar (confirmado por lectura directa, no por Pendientes.md)

- `app/engine/indexation/historical_index.py` → `get_ibc_usura_for_date(fecha) -> Tuple[Decimal,
  Decimal]` y la tabla privada `_TRAMOS_IBC_USURA: List[TramoIBCUsura]` (263 tramos mensuales desde
  1997-07-01, `usura_anual == 1.5 x ibc_anual` en todas las filas, verificado en el Sprint 5). Es la
  fuente real que resuelve la tasa de usura vigente por fecha.
- `app/engine/interest/rate_conversion.py` → `EffectiveRateConverter.annual_to_daily(annual_percent) ->
  Rate` ya usa la fórmula correcta `(1+i_EA)^(1/365) - 1` con base 365 fija (correcto para tributario,
  que sigue la convención calendario del Código Civil, no el año comercial de 360 días).
- `app/engine/interest/provider.py` → `MemoryRateProvider.add_rate_period(start, end, rate, source)` ya
  modela tramos con vigencia y fuente citable para auditoría.
- `app/engine/interest/daily_interest.py` → `DailyInterest.calculate(capital, daily_rate: Rate, days:
  int) -> Decimal` ya hace la suma de interés simple con redondeo legal (`Rounding.money`).
- `app/services/area_strategy.py` → `ComercialStrategy._construir_rate_provider()` (líneas 189-223) es
  el precedente directo de cómo construir un `MemoryRateProvider` por tramos con `source` citado; se
  sigue el mismo patrón aquí, pero resolviendo la tasa automáticamente desde datos históricos en vez de
  un campo manual pactado (ver razón abajo).

## Módulo 1: `app/engine/tax/moratory_interest.py`

### Por qué resolución automática y no tasa manual

`ComercialStrategy` recibe la tasa moratoria como campo manual de la obligación porque en derecho
comercial la tasa puede pactarse. En derecho tributario, el E.T. art. 635 no deja espacio a pacto: la
tasa **siempre** es "usura vigente − 2 puntos", derivada mecánicamente de la serie histórica de la SFC.
Por eso este motor resuelve los tramos automáticamente en vez de exigir un input manual — y porque el
PDF (pág. 8, "Inmutabilidad Histórica") exige explícitamente segmentar la mora por la tasa vigente en
cada mes, algo que un único valor manual no podría representar para deudas de varios meses.

### Función nueva en `historical_index.py` (extensión, no archivo paralelo)

```python
def get_tramos_ibc_usura_between(inicio: date, fin: date) -> List[TramoIBCUsura]:
    """Tramos de _TRAMOS_IBC_USURA que se solapan con [inicio, fin], en orden cronológico."""
```

Lanza `ValueError` si `fin < inicio` (mismo guard que ya usan `interrumpir`/`suspender` en
`app/engine/temporal/terminos.py`, Sprint 6). Si el rango cae fuera de los datos disponibles
(anterior a 1997-07-01 o posterior al último tramo cargado), lanza `ValueError` explícito en vez de
devolver una lista vacía silenciosa — mismo espíritu que `MemoryRateProvider.get_rate()` cuando no
encuentra tramo.

### Funciones nuevas en `moratory_interest.py`

```python
def construir_rate_provider_moratorio_tributario(
    fecha_exigibilidad: date, fecha_corte: date
) -> MemoryRateProvider:
    """Un RatePeriod diario por cada tramo histórico solapado, tasa = usura_anual - 2 puntos."""

def calcular_interes_moratorio_tributario(
    capital: Decimal, fecha_exigibilidad: date, fecha_corte: date
) -> Decimal:
    """Suma DailyInterest.calculate() sobre cada tramo del provider. Capital fijo (sin abonos)."""
```

- `source` de cada `RatePeriod`: `"Interés moratorio tributario (E.T. art. 635): usura vigente - 2
  puntos"`.
- Cada tramo aporta `EffectiveRateConverter.annual_to_daily(tramo.usura_anual - Decimal("2"))` como
  tasa diaria, acotado a la intersección real de fechas entre el tramo y `[fecha_exigibilidad,
  fecha_corte]`.
- `calcular_interes_moratorio_tributario` no modela abonos parciales ni imputación — capital fijo desde
  `fecha_exigibilidad` hasta `fecha_corte`. Modelar pagos parciales con imputación tributaria propia
  (sanciones → intereses → impuesto) es la pieza 5 del Sprint 11, diferida a 11b.
- Si `capital <= 0`, sigue la misma convención que `DailyInterest.calculate` (retorna `Decimal("0.00")`
  sin lanzar error).

## Módulo 2: `app/engine/tax/renta_liquida.py`

Pipeline aritmético puro (sin tasas, sin UVT, sin dependencias externas):

```python
@dataclass(frozen=True)
class RentaLiquidaGravableResult:
    ingresos_netos: Decimal
    renta_bruta: Decimal
    renta_liquida: Decimal
    hubo_perdida_liquida: bool
    renta_liquida_gravable: Decimal

def depurar_renta_liquida_gravable(
    ingresos_brutos: Decimal,
    devoluciones_rebajas_descuentos: Decimal,
    costos: Decimal,
    deducciones: Decimal,
    rentas_exentas: Decimal,
) -> RentaLiquidaGravableResult:
    ...
```

Flujo (PDF págs. 38-39, "Lógica de Depuración: Impuesto sobre la Renta"):

```
ingresos_netos = ingresos_brutos - devoluciones_rebajas_descuentos
renta_bruta     = ingresos_netos - costos
renta_liquida   = renta_bruta - deducciones

si renta_liquida < 0:
    hubo_perdida_liquida = True
    renta_liquida_gravable = Decimal("0.00")   # no se restan rentas exentas sobre una pérdida
si no:
    hubo_perdida_liquida = False
    renta_liquida_gravable = max(Decimal("0.00"), renta_liquida - rentas_exentas)
```

Todos los montos de salida pasan por `Rounding.money()` (mismo embudo de redondeo legal que usa
`DailyInterest`). No valida que los inputs sean no-negativos: son responsabilidad del llamador
(frontera de confianza igual que el resto del motor — ver `CLAUDE.md`/convención del proyecto de no
validar donde no hace falta).

**Fuera de alcance, documentado (no un olvido):** compensación de pérdidas fiscales de años anteriores
contra renta líquida de años futuros — no hay ningún caso de uso en este sprint que lo requiera.

## Excepciones de dominio

Ninguna nueva. `get_tramos_ibc_usura_between` reutiliza `ValueError` simple, siguiendo el mismo patrón
que `MemoryRateProvider.get_rate()`. No se agrega ninguna excepción tipo `AreaNoImplementadaError`
porque este sprint no toca `area_strategy.py`.

## Testing

TDD, siguiendo el precedente de `tests/engine/labor/` (subcarpeta por dominio nuevo):

- `tests/engine/tax/test_moratory_interest.py`:
  - Caso puntual del ejemplo del PDF (usura 28.79% EA → tasa moratoria tributaria 26.79% EA) verificado
    contra un cálculo manual de interés simple diario.
  - Caso multi-tramo: una deuda que cruza dos meses con usura distinta, verificando que el interés total
    sea la suma correcta por segmento (no un promedio ni la tasa de un solo mes aplicada a todo el
    rango).
  - Caso límite: `fecha_exigibilidad == fecha_corte` (cero días de mora → interés 0).
  - Caso de error: rango fuera de los datos históricos disponibles.
- `tests/engine/tax/test_renta_liquida.py`:
  - Caso base sin pérdida (todos los pasos positivos, verificar cada campo intermedio del resultado).
  - Caso de pérdida líquida (`renta_liquida < 0` → `renta_liquida_gravable == 0`, `hubo_perdida_liquida
    is True`).
  - Caso límite: `rentas_exentas > renta_liquida` (positiva) → `renta_liquida_gravable` topada en 0 sin
    quedar negativa.
- Suite completa del proyecto en verde al cierre del sprint.

## Definición de Hecho

- `app/engine/tax/moratory_interest.py` y `app/engine/tax/renta_liquida.py` existen, con TDD, sin tocar
  `area_strategy.py`, `constants.py` ni ninguna vista de la GUI.
- `historical_index.get_tramos_ibc_usura_between` nueva y probada.
- Suite completa en verde.
- `Pendientes.md` actualizado: Sprint 11 pasa a reflejar que 11a está completado y documentar 11b
  (sanciones + imputación) como pendiente explícito, con la misma nota de bloqueo por UVT que ya
  documentó el Sprint 5.

## Riesgos / notas abiertas para la fase de implementación

- Definir en el plan si `get_tramos_ibc_usura_between` debe clonar los `TramoIBCUsura` que solo se
  solapan parcialmente con `[inicio, fin]` recortando sus fechas al rango pedido, o devolver los tramos
  completos tal como están en la tabla (dejando que `construir_rate_provider_moratorio_tributario` sea
  quien intersecte las fechas al armar cada `RatePeriod`). Se recomienda la segunda opción: mantiene
  `get_tramos_ibc_usura_between` como una consulta simple de la tabla, y la lógica de intersección de
  fechas vive donde ya se necesita (junto al cálculo de tasa), igual que hace
  `ComercialStrategy._construir_rate_provider` con `min()`/`max()` sobre fechas de obligación.
- Regla explícita de redondeo (`Rounding.money`, 2 decimales) para cada valor de `RentaLiquidaGravableResult`,
  no solo para el total final — a confirmar en el plan si el redondeo debe aplicarse en cada paso
  intermedio o solo antes de retornar el resultado (afecta si acumula error de redondeo distinto a un
  cálculo manual paso a paso).
