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
    diaria via `EffectiveRateConverter`), y delega en `UniversalLiquidationService.liquidar(...)`. Desde el
    Sprint 41, una `Obligacion` Recurrente con `tipo_reajuste_anual` (SMMLV o IPC) activo puede generar y
    persistir sus cuotas mensuales reales como `Obligacion` Puntuales hijas (`obligacion_padre_id`
    apuntando a la Recurrente original) via `generar_cuotas_mensuales`
    (`app/services/reajuste_anual.py`): capital constante dentro de cada año calendario, reajustado el 1
    de enero de cada año siguiente segun el indice elegido, concepto dinamico por mes/año, y cada cuota
    individual queda seleccionable en la GUI para registrar su propio abono por separado. Una vez
    generadas, esas cuotas corren por el motor consolidado como Obligaciones Puntuales independientes (la
    Recurrente padre deja de aportar eventos de capital propios, para no duplicar el capital); mientras no
    se generen, la Recurrente sigue expandiendose de forma efimera con `FamilyScheduler` (capital
    constante, sin reajuste), el comportamiento anterior al Sprint 41.
  - **Beneficiario y vigencia de la obligacion alimentaria (Sprint 74):** `database/models.py::Beneficiario`
    -- entidad propia (relacion 1:1 con `Obligacion` via `obligacion_id` UNIQUE, tabla enteramente nueva sin
    migracion ALTER TABLE) con nombre, fecha de nacimiento, `TipoBeneficiario` (NINO / NINO_DISCAPACIDAD /
    CONYUGE / PADRES / OTRO -- arbol de decision del formulario de captura), y campos condicionales (si
    estudia, si la discapacidad es permanente, relacion con el demandante). `app/services/vigencia_alimentos.py`
    calcula automaticamente si la obligacion sigue vigente: NINO sin discapacidad hasta los 18 años (25 si
    estudia una carrera profesional/tecnica/tecnologica), NINO_DISCAPACIDAD con discapacidad permanente de
    forma vitalicia. CONYUGE, PADRES, OTRO, y NINO_DISCAPACIDAD sin marcar permanente quedan declarados
    explicitamente como "no determinable automaticamente" -- el software NUNCA les aplica el limite de edad
    de NINO ni inventa una fecha de fin (pregunta abierta sin responder del despacho sobre el criterio
    operacional exacto, ver `docs/Preguntas-Para-Abogado-Abiertas.md`, seccion Sprint 74). El calculo topa
    tanto la expansion efimera (`CivilFamiliaStrategy._eventos_de_obligacion`) como los 2 generadores de
    cuotas hijas reales (`generar_cuotas_mensuales`, `generar_cuotas_fechas_fijas`) -- una obligacion RECURRENTE
    con beneficiario NINO deja de causar cuotas automaticamente al superar la edad limite, sin necesitar
    fijar `fecha_fin` a mano. El formulario de captura (`ObligacionFormDialog`, Civil/Familia) muestra una
    vista previa en vivo del resultado del calculo.
  - `ComercialStrategy`: pagares, letras de cambio, cheques y facturas, con validacion de tope de usura
    (`usury_validator`) sobre la tasa remuneratoria y moratoria.
  - `SancionatorioStrategy`: multas administrativas expresadas en SMLMV o UVT, con conversion automatica
    segun la fecha del hecho (`smlmv_to_uvt.py`).
  - `HonorariosStrategy`: cobro de honorarios profesionales y cuota litis, validando el tope unico del 50%
    acumulado (honorarios fijos + cuota litis) del beneficio obtenido -- el doble tope en cascada (30%
    individual + 50% total) se elimino en el Sprint 4 -- leido como parametro legal versionado
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
  operables listadas arriba. Desde el Sprint 70/91 (2026-08-23), el mismo modulo tambien trae
  `calcular_tasa_reemplazo_regimen_1985_1989`, `calcular_tasa_reemplazo_iss_pre_ley_100`,
  `calcular_tasa_reemplazo_ley_100_original` y `calcular_tasa_reemplazo_invalidez_grado_2` — formulas de
  regimenes pensionales historicos confirmadas por el despacho, igual de aisladas, sin router por fecha de
  causacion (las fechas exactas de vigencia de cada regimen siguen sin confirmar) ni wiring a ninguna
  estrategia. La pension de invalidez grado 1 sigue sin funcion propia: su tope trae una discrepancia entre
  dos fuentes del despacho (60% vs. 75%) sin resolver — ver `docs/Pendientes.md`, Sprint 70/91.
- Costas judiciales con tabla real de rangos (hoy se ingresan como porcentaje manual en Honorarios) — ver
  `docs/Pendientes.md`, Sprint 18.
