# Motor Financiero (Interes)

## Que hace
Calcula intereses simples dia a dia sobre un capital, calcula y sanciona el exceso sobre el tope de
usura, y mantiene el estado inmutable de una deuda (capital + interes + indexacion) a lo largo del
tiempo.

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
- `app/engine/interest/usury_validator.py`: `calcular_tope_usura` — calcula el tope de usura (multiplicador
  vigente x IBC, Ley 45/1990 art. 72) contra un IBC consultado en `parametro_service` (Sprint 13). Corregido
  en el Sprint 2 (2026-08-01) tras la respuesta del despacho: una tasa pactada por encima del tope ya no se
  rechaza ni se recorta silenciosamente — `ComercialStrategy._calcular_sancion_usura` liquida con la tasa
  realmente pactada, calcula el exceso de interes cobrado frente al tope, y resta del saldo el doble de ese
  exceso (puede dejar saldo a favor del deudor). Solo se invoca desde el area Comercial.
- `app/engine/tax/moratory_interest.py`: interes moratorio del E.T. art. 635 para el area Tributario,
  reutilizando el mismo motor de tramos historicos.
- `app/engine/liquidation/models.py`: `PendingDebt(principal, interest, indexation)` — inmutable, con
  `.total()`.
- `app/engine/liquidation/balance.py`: `BalanceEngine` — funciones puras `add_principal`, `add_interest`,
  `add_indexation` que devuelven un nuevo `PendingDebt`.
- `app/engine/liquidation/engine.py`: `LiquidationCore` — orquesta el paso del tiempo dia a dia
  (`_accrue_time_passage`) y el procesamiento de cada `Event` (`_process_event`), acumulando el historial
  en `LiquidationItem`.
- Anatocismo comercial condicionado (Art. 886 C.Co., Sprint 19): `LiquidationCore`/`BalanceEngine` ganaron
  el evento `CAPITALIZACION_INTERESES_ANATOCISMO`, que traslada el interes simple ya devengado al capital
  en cada aniversario desde la fecha de capitalizacion (en vez de usar `CompoundInterest.calculate()`,
  que sigue huerfano). `ComercialStrategy` lo activa solo si hay demanda judicial y/o acuerdo posterior de
  capitalizacion con al menos un año de intereses vencidos; el resto de la liquidacion sigue en interes
  simple.
- Multiples tasas de interes simultaneas por expediente (Sprint 21): cada `Obligacion` corre su propio
  `LiquidationCore` independiente (`_liquidar_por_obligacion` en `app/services/area_strategy.py`), con su
  propia tasa y solo sus propios abonos, y los historiales se fusionan en una sola linea de tiempo
  consolidada. Aplica a `CivilFamiliaStrategy`, `ComercialStrategy`, `SancionatorioStrategy`,
  `HonorariosStrategy` y `TributarioStrategy` (no a `LaboralStrategy`, que no tiene tasa por obligacion).

## Como se usa en el MVP
Cada `AreaStrategy` construye un `MemoryRateProvider` con la(s) tasa(s) efectiva(s) anual(es) pactadas
(convertidas a diaria), y delega en `UniversalLiquidationService.liquidar(...)`.

## Pendiente (no implementado aun)
- `CompoundInterest.calculate()` (`app/engine/interest/compound_interest.py`) sigue huerfano: el
  anatocismo comercial (arriba) se resolvio con eventos de capitalizacion periodica en vez de esta
  formula cerrada de una sola pasada.

Ver `Pendientes.md`.
