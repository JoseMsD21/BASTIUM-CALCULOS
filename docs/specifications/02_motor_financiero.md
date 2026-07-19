# Motor Financiero (Interes)

## Que hace
Calcula intereses simples dia a dia sobre un capital, y mantiene el estado inmutable de una deuda
(capital + interes + indexacion) a lo largo del tiempo.

## Componentes
- `app/engine/financial/rate.py`: `Rate(value)` envuelve una **fraccion** (0.06 = 6%), no un numero de
  porcentaje. `Rate.from_percent(x)` construye una `Rate` dividiendo `x` entre 100.
- `app/engine/interest/daily_interest.py`: `DailyInterest.calculate(capital, daily_rate, days)` aplica
  `I = C * i * t` con redondeo monetario (`Rounding.money`).
- `app/engine/interest/rate_conversion.py`: `EffectiveRateConverter.annual_to_daily(annual_percent)`
  convierte una tasa efectiva anual (como se pactan/certifican legalmente) a la tasa diaria equivalente,
  usando `i_diario = (1 + i_EA) ** (1/365) - 1`.
- `app/engine/interest/provider.py`: `RateProvider` (interfaz) y `MemoryRateProvider`, que permite inyectar
  tramos de tasa (`RatePeriod`) para que el motor calcule interes por tramos historicos cuando la tasa
  cambia en el tiempo. **Si se usa un `rate_provider`, debe cubrir todo el rango de fechas de la
  liquidacion**, o `get_rate` lanza `ValueError`.
- `app/engine/liquidation/models.py`: `PendingDebt(principal, interest, indexation)` — inmutable, con
  `.total()`.
- `app/engine/liquidation/balance.py`: `BalanceEngine` — funciones puras `add_principal`, `add_interest`,
  `add_indexation` que devuelven un nuevo `PendingDebt`.
- `app/engine/liquidation/engine.py`: `LiquidationCore` — orquesta el paso del tiempo dia a dia
  (`_accrue_time_passage`) y el procesamiento de cada `Event` (`_process_event`), acumulando el historial
  en `LiquidationItem`.

## Como se usa en el MVP
`CivilFamiliaStrategy` construye un `MemoryRateProvider` con un unico tramo (la tasa efectiva anual pactada
de la primera obligacion del expediente, convertida a diaria) que cubre desde la obligacion mas antigua
hasta la fecha de corte.

## Pendiente (no implementado aun)
- Validacion de tope de usura (1.5x IBC) — necesaria para el area Comercial.
- Anatocismo (interes sobre interes) — prohibido por defecto, el motor actual no lo aplica en ningun caso
  (comportamiento correcto para Civil, pero el area Comercial necesitara habilitarlo bajo condiciones).
- Multiples tasas por obligacion dentro del mismo expediente (hoy se usa una sola tasa por expediente).

Ver `Pendientes.md`.
