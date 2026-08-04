# Motor Juridico: Areas del Derecho

## Que hace
Convierte las Obligaciones y Abonos capturados en la GUI en la liquidacion final, aplicando la logica
propia de cada una de las 6 areas del derecho operables hoy: Civil/Familia (interes fijo del Art. 1617
C.C.), Comercial, Sancionatorio, Honorarios/Litigio, Laboral y Tributario.

## Componentes
- `app/engine/liquidation/registry.py`: `AreaRegistry` — registra las 6 areas del derecho
  (`CIVIL_FAMILIA`, `COMERCIAL`, `LABORAL`, `SANCIONATORIO`, `HONORARIOS`, `TRIBUTARIO`) y su estrategia de
  calculo correspondiente. `AreaRegistry.get_strategy(area_name)` instancia la estrategia.
- `app/services/area_strategy.py`:
  - `AreaStrategy` (interfaz abstracta): `liquidar(obligaciones, abonos, fecha_corte) -> LiquidationResult`.
  - `CivilFamiliaStrategy`: mapea cada `Obligacion` Puntual a un unico `Event` de capital; cada
    `Obligacion` Recurrente se expande con `FamilyScheduler` en eventos mensuales; cada `Abono` se convierte
    en un `Payment`. Construye un `MemoryRateProvider` con la tasa efectiva anual pactada (convertida a
    diaria via `EffectiveRateConverter`), y delega en `UniversalLiquidationService.liquidar(...)`.
  - `ComercialStrategy`: pagares, letras de cambio, cheques y facturas, con validacion de tope de usura
    (`usury_validator`) sobre la tasa remuneratoria y moratoria.
  - `SancionatorioStrategy`: multas administrativas expresadas en SMLMV o UVT, con conversion automatica
    segun la fecha del hecho (`smlmv_to_uvt.py`).
  - `HonorariosStrategy`: cobro de honorarios profesionales y cuota litis, validando los topes del 30%
    (cuota litis sola) y 50% (total) del beneficio obtenido, leidos como parametros legales versionados
    (`parametro_service`, Sprint 13).
  - `LaboralStrategy`: liquidacion final (finiquito) de un contrato — cesantias, intereses a cesantias,
    prima, vacaciones e indemnizacion moratoria bifasica del Art. 65 CST, con cotizaciones de seguridad
    social, incapacidades y suspensiones contractuales opcionales (opt-in, Sprint 16).
  - `TributarioStrategy`: impuesto a cargo, las 3 sanciones (extemporaneidad, inexactitud, error
    aritmetico, con piso legal de 10 UVT), imputacion de pagos propia via el motor generico de liquidacion,
    interes moratorio automatico del E.T. art. 635, y depuracion de Renta Liquida Gravable informativa
    (Sprint 15).
  - Todas las estrategias estan cableadas: no hay ninguna que lance `AreaNoImplementadaError`.

## Flujo end-to-end
`ExpedienteDetallePage._liquidar()` (`app/views/expediente_detalle.py`) lee las Obligaciones/Abonos del
expediente desde la base de datos, obtiene la estrategia via `AreaRegistry.get_strategy(area)`, y muestra
el `LiquidationResult` en `ResultadoLiquidacionView`. Las 6 areas son seleccionables y operables end-to-end
desde `ExpedienteFormDialog` (`app/views/expedientes.py`).

## Pendiente (no implementado aun)
- Wiring del modulo pensional (`app/engine/labor/ibl.py`, implementado como funciones puras standalone
  desde el Sprint 17: `calcular_ibl`, `calcular_tasa_reemplazo`, `calcular_densidad_semanas`,
  `semanas_minimas_requeridas`) a una `PensionalStrategy`/pantalla de GUI — hoy no es una de las 6 areas
  operables listadas arriba.
- Costas judiciales con tabla real de rangos (hoy se ingresan como porcentaje manual en Honorarios) — ver
  `Pendientes.md`, Sprint 18.
