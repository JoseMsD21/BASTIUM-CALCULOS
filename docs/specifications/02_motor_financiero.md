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
- `app/engine/interest/rate_conversion.py`: dos conversiones anual -> diaria (Sprint 76):
  - `EffectiveRateConverter.annual_to_daily(annual_percent)` — efectiva compuesta,
    `i_diario = (1 + i_EA) ** (1/365) - 1`. Para tasas certificadas o pactadas como efectivas anuales:
    IBC/usura, tasas remuneratoria/moratoria comerciales (Art. 884 C.Co.), mora laboral con usura
    (Art. 65 CST), DTF (condena administrativa) y Sancionatorio. (El E.T. 635 tiene su propia conversion
    en `app/engine/tax/moratory_interest.py`.)
  - `EffectiveRateConverter.annual_simple_to_daily(annual_percent)` — lineal simple sin anatocismo,
    `i_diario = i_anual / 365` (base 365 siempre). Para el interes civil legal del 6 % (Art. 1617/2232
    C.C.) y las tasas pactadas sin capitalizacion en obligaciones de dinero puro: Civil/Familia (tasa
    pactada y fallback `CIVIL_ANNUAL_RATE`), Honorarios (tasa pactada y modo IPC + civil 6 %) y Comercial
    solo en el modo (b) de la regla XOR (IPC + interes civil puro). Respuesta del despacho del 16/11/2026:
    "Obligacion Civil de Credito Ordinario (Simple): Debe usarse la Opcion A (Formula Lineal Simple:
    0.06 / 365)". Ejemplo: $10.000.000 x 6 % x 30/365 = $49.315,07 con
    `PoliticaCausacion.EXACTA_POR_PERIODO`; con la politica legada (predeterminada, redondeo diario y tasa
    cuantizada a 12 decimales) el motor da $49.315,20 (1.643,84/dia x 30).
  - La tasa pura actuarial mensual (0,0048676): conectada desde el Sprint 104 a la liquidacion tramo a
    tramo de Suma Unica con abonos en Civil/Familia (`TASA_INTERES_MENSUAL_PURA`,
    `app/engine/indexation/suma_unica_con_abonos.py`; interes compuesto `C x ((1+i)^meses - 1)` en meses
    comerciales 30/360). Para liquidacion de perjuicios sigue sin dominio propio (Sprint 97).
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
- `app/engine/tax/tope_suspensivo.py` (Sprint 84 seguimiento): tope suspensivo del interes moratorio
  tributario por demanda ante lo contencioso administrativo. Campos capturados en `Obligacion`:
  `fecha_admision_demanda`, `fecha_notificacion_sentencia` (columnas nuevas, migracion
  `scripts/migrate_tope_suspensivo_tributario_sprint84.py`). Calculados, nunca guardados:
  `fecha_tope_24m` = admision + 24 meses calendario (dia topado a fin de mes) y
  `fecha_reanudacion_interes` = notificacion + 11 dias calendario. `RateProviderConTopeSuspensivo`
  envuelve el rate provider E.T. 635 de la obligacion y deja a 0% los dias estrictamente posteriores
  al tope y estrictamente anteriores a la reanudacion (el dia del tope y el de reanudacion causan
  interes). Sin sentencia notificada, la suspension corre desde el tope hasta la fecha de corte; si
  la reanudacion cae en o antes del tope, no hay suspension. `TributarioStrategy` agrega una alerta
  informativa con el periodo suspendido. En el formulario, la casilla "Hay demanda ante lo
  contencioso administrativo" (no se guarda: se deduce de que haya fecha de admision) hace
  obligatorias las 2 fechas; sin la casilla se guardan nulas (interpretacion de "obligatorios en el
  formulario": una obligacion sin demanda no tiene esas fechas). El calculo del techo/actualizacion
  del Art. 867-1 (`calcular_interes_moratorio_tributario`) NO aplica el tope suspensivo.
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
  que sigue huerfano). `ComercialStrategy` lo activa solo si se cumple una de las dos condiciones (demanda
  judicial o acuerdo posterior de capitalizacion) con al menos un año de intereses vencidos; el resto de
  la liquidacion sigue en interes simple.
- Multiples tasas de interes simultaneas por expediente (Sprint 21): cada `Obligacion` corre su propio
  `LiquidationCore` independiente (`_liquidar_por_obligacion` en `app/services/area_strategy.py`), con su
  propia tasa y solo sus propios abonos, y los historiales se fusionan en una sola linea de tiempo
  consolidada. Aplica a `CivilFamiliaStrategy`, `ComercialStrategy`, `SancionatorioStrategy`,
  `HonorariosStrategy` y `TributarioStrategy` (no a `LaboralStrategy`, que no tiene tasa por obligacion).

## Como se usa en el MVP
Cada `AreaStrategy` construye un `MemoryRateProvider` con la(s) tasa(s) anual(es) pactadas o legales
(convertidas a diaria con la formula que corresponda, ver arriba — `AreaStrategy._rate_provider_tasa_plana`
recibe `lineal_simple=True` para el interes civil/pactado simple), y delega en
`UniversalLiquidationService.liquidar(...)`.

## Pendiente (no implementado aun)
- `CompoundInterest.calculate()` (`app/engine/interest/compound_interest.py`) sigue huerfano: el
  anatocismo comercial (arriba) se resolvio con eventos de capitalizacion periodica en vez de esta
  formula cerrada de una sola pasada.

Ver `docs/Pendientes.md`.
