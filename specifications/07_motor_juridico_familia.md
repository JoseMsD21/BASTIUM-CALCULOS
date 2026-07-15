# Motor Juridico: Area Civil / Familia

## Que hace
Es la unica area del derecho con calculo real en este sprint. Convierte las Obligaciones y Abonos
capturados en la GUI en la liquidacion final, aplicando el interes fijo del Art. 1617 C.C. (6% anual, o la
tasa que el usuario pacte/certifique, convertida a diaria).

## Componentes
- `app/engine/liquidation/registry.py`: `AreaRegistry` — registra las 5 areas del derecho
  (`CIVIL_FAMILIA`, `COMERCIAL`, `LABORAL`, `SANCIONATORIO`, `HONORARIOS`) y su estrategia de calculo
  correspondiente. `AreaRegistry.get_strategy(area_name)` instancia la estrategia.
- `app/services/area_strategy.py`:
  - `AreaStrategy` (interfaz abstracta): `liquidar(obligaciones, abonos, fecha_corte) -> LiquidationResult`.
  - `CivilFamiliaStrategy`: unica implementacion real. Mapea cada `Obligacion` Puntual a un unico `Event`
    de capital; cada `Obligacion` Recurrente se expande con `FamilyScheduler` en eventos mensuales; cada
    `Abono` se convierte en un `Payment`. Construye un `MemoryRateProvider` con la tasa efectiva anual de
    la primera obligacion (convertida a diaria via `EffectiveRateConverter`), y delega en
    `UniversalLiquidationService.liquidar(...)`.
  - `ComercialStrategy`, `LaboralStrategy`, `SancionatorioStrategy`, `HonorariosStrategy`: registradas pero
    lanzan `AreaNoImplementadaError` (`app/core/exceptions.py`) si se invocan. La GUI nunca las llama
    porque el selector de area en `NuevoExpedienteDialog` (`app/views/expedientes.py`) las deshabilita.

## Flujo end-to-end
`ExpedienteDetallePage._liquidar()` (`app/views/expediente_detalle.py`) lee las Obligaciones/Abonos del
expediente desde la base de datos, obtiene la estrategia via `AreaRegistry.get_strategy(area)`, y muestra
el `LiquidationResult` en `ResultadoLiquidacionView`.

## Pendiente (no implementado aun)
Las 4 areas restantes (Comercial, Laboral, Sancionatorio, Honorarios) — ver `Pendientes.md` para el orden
de los proximos sprints.
