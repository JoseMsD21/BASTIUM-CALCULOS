# Motor Financiero (Interes)

## Que hace
Calcula intereses simples dia a dia sobre un capital, valida el tope de usura, y mantiene el estado
inmutable de una deuda (capital + interes + indexacion) a lo largo del tiempo.

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
- `app/engine/interest/usury_validator.py`: `validar_tasa_usura` — valida el tope de usura (1.5x IBC, Ley
  45/1990 art. 72) contra un IBC consultado en `parametro_service` (Sprint 13). Se invoca automaticamente al
  liquidar para las areas Comercial y Tributario; lanza el error "Tasa usuraria" sin truncar nada
  silenciosamente.
- `app/engine/tax/moratory_interest.py`: interes moratorio del E.T. art. 635 para el area Tributario,
  reutilizando el mismo motor de tramos historicos.
- `app/engine/liquidation/models.py`: `PendingDebt(principal, interest, indexation)` — inmutable, con
  `.total()`.
- `app/engine/liquidation/balance.py`: `BalanceEngine` — funciones puras `add_principal`, `add_interest`,
  `add_indexation` que devuelven un nuevo `PendingDebt`.
- `app/engine/liquidation/engine.py`: `LiquidationCore` — orquesta el paso del tiempo dia a dia
  (`_accrue_time_passage`) y el procesamiento de cada `Event` (`_process_event`), acumulando el historial
  en `LiquidationItem`.

## Como se usa en el MVP
Cada `AreaStrategy` construye un `MemoryRateProvider` con la(s) tasa(s) efectiva(s) anual(es) pactadas
(convertidas a diaria), y delega en `UniversalLiquidationService.liquidar(...)`.

## Pendiente (no implementado aun)
- Anatocismo comercial condicionado (Art. 886 C.Co.) — el motor actual no aplica interes sobre interes en
  ningun caso (comportamiento correcto para Civil, pero el area Comercial lo necesitara bajo condiciones) —
  ver `Pendientes.md`, Sprint 19.
- Multiples tasas de interes simultaneas por expediente — ver `Pendientes.md`, Sprint 21.

Ver `Pendientes.md`.
