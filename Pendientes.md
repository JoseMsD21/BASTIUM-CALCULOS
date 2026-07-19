# Pendientes de BASTIUM

Backlog técnico completo de todo lo que queda fuera del MVP de captura manual (área Civil/Familia,
cerrado el 2026-07-15). Cada sección de abajo es un **sprint autocontenido**: trae objetivo, dependencias,
qué documentos y código consultar, qué reutilizar, qué construir y cuándo darlo por terminado. La idea es
que una sesión nueva de Claude (sin memoria de esta conversación) pueda abrir este archivo, leer un solo
sprint, y ponerse a trabajar sin tener que releer todo el proyecto desde cero.

**Cómo usar este archivo:** copia el nombre del sprint (ej. "Sprint 2 — Área Comercial") y pide "trabaja en
el Sprint 2 de Pendientes.md". Cada sprint dice explícitamente qué leer antes de tocar código.

**Regla obligatoria al cerrar cualquier sprint:** además de la "Definición de Hecho" propia de cada
sprint, hay que actualizar `README.md` y `docs/GUIA_USUARIO.md` para reflejar el nuevo estado —
sacar el módulo correspondiente de la lista "🚧 en desarrollo"/"🚧 no todavía" y describir cómo usarlo
igual que se documentó Civil/Familia. Estos dos documentos nunca deben quedar desactualizados respecto
al código real.

**Contexto ya construido (no repetir):**
- `docs/superpowers/specs/2026-07-14-mvp-captura-liquidacion-civil-familia-design.md` — diseño del MVP.
- `docs/superpowers/plans/2026-07-14-mvp-captura-liquidacion-civil-familia.md` — plan TDD tarea por tarea,
  las 17 tareas están marcadas `✅ COMPLETADA` con notas de ejecución real (bugs encontrados y cómo se
  resolvieron).
- `specifications/01_motor_temporal.md` … `07_motor_juridico_familia.md` — qué hace cada motor hoy.
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf` (raíz del repo) — documento maestro de
  requisitos de TODO el sistema jurídico previsto (todas las áreas, motor de reglas EFDJ, datos
  históricos, tributario, auditoría). El MVP solo implementó una fracción pequeña de este documento
  (interés civil sin indexación). Cada sprint abajo cita las páginas exactas de este PDF que aplican.
- Suite de tests: 81 passed a fecha 2026-07-15 (`pytest.ini` usa `--import-mode=importlib` +
  `consider_namespace_packages=true` para evitar colisión de nombre `tests/database` vs `database/` — no
  tocar esa config sin necesidad).

---

## Sprint 2 — Área Comercial

**Prioridad sugerida:** Alta (ya tiene entrada en el registry, es el área con más demanda real).
**Depende de:** Nada estrictamente. Idealmente correr después del Sprint 5 (datos históricos) para tener
tramos reales de IBC/usura en vez de una sola tasa vigente, pero puede implementarse con una tasa única
igual que hace `CivilFamiliaStrategy` hoy y luego mejorarse.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, sección "OBLIGACIONES EN DERECHO COMERCIAL"
  (páginas 44-46) y "B. Derecho Comercial y Financiero" dentro de "INDICADORES DE CÁLCULO" (páginas 9-10).
- Mismo PDF, tabla histórica IBC/Tasa de Usura de la Superintendencia Financiera (páginas 58-61) — útil
  para pruebas con datos reales y para el Sprint 5.

**Código existente a reutilizar (no reinventar):**
- `app/engine/interest/rate_conversion.py` → `EffectiveRateConverter.annual_to_daily(annual_percent)` ya
  convierte EA a diaria; se usa igual que en `CivilFamiliaStrategy`.
- `app/engine/interest/provider.py` → `MemoryRateProvider` ya soporta tramos de tasa por fecha.
- `app/engine/interest/compound_interest.py` → `CompoundInterest.calculate(capital, period_rate: Rate,
  periods: int)` YA EXISTE y está implementado, pero **huérfano**: ningún motor lo invoca hoy. Es lo que
  se necesita para el anatocismo comercial condicionado (Art. 886 C.Co.).
- `app/services/area_strategy.py` → seguir el patrón exacto de `CivilFamiliaStrategy.liquidar()` (mapeo de
  obligaciones a `Event`, `Payment`, `MemoryRateProvider`, delegación a `UniversalLiquidationService`).
- `app/core/exceptions.py` → `AreaNoImplementadaError` ya existe si hace falta una sub-excepción propia.

**Código nuevo a crear:**
- Reemplazar el cuerpo de `ComercialStrategy` en `app/services/area_strategy.py` (hoy lanza
  `AreaNoImplementadaError`, línea ~95).
- Validador de tope de usura: nueva función/clase (sugerido `app/engine/interest/usury_validator.py`) que
  reciba la tasa pactada y el IBC vigente, y lance una excepción de dominio propia (ej.
  `TasaUsurariaError`) o trunque al tope — **decidir con el usuario cuál de las dos** antes de implementar,
  el PDF menciona ambas variantes en distintas secciones (p.8: "lanzar una excepción o truncar").
- Regla de incompatibilidad interés-comercial + indexación IPC: si la obligación es comercial, no debe
  poder combinarse con `IPCIndexation` (a diferencia de Civil, donde sí son compatibles). Documentar esta
  regla como validación explícita, no solo como comentario.
- Wiring condicional de `CompoundInterest` para anatocismo: solo si hay más de un año de intereses
  vencidos y (demanda judicial O acuerdo posterior) — el PDF (pág. 45, "C. Anatocismo") es explícito en
  que estas dos condiciones son obligatorias, no basta con que exista mora.

**Alcance incluido:**
- Interés remuneratorio comercial = IBC si no se pacta; interés moratorio = 1.5×IBC si no se pacta.
- Validación/truncamiento de usura.
- `ComercialStrategy.liquidar()` real, cableada al registry (ya registrada en
  `app/engine/liquidation/registry.py`, solo cambia la clase que instancia).
- Habilitar el área "Comercial" en `app/core/constants.py` (`AREAS_DERECHO`, tercer valor de la tupla a
  `True`) y en el selector de la GUI (`NuevoExpedienteDialog`, ya lee de esa constante, no requiere tocar
  la vista).

**Alcance explícitamente excluido (va a otros sprints):**
- TRM / moneda extranjera en títulos valores comerciales → Sprint 12.
- Costas y agencias en derecho → Sprint 4.
- Carga automática de tramos históricos de IBC/usura → Sprint 5 (aquí basta una tasa vigente única, igual
  que Civil/Familia en el MVP).

**Riesgos / notas técnicas conocidas:**
- El PDF advierte explícitamente: "el sistema no puede simplemente dividir por 12 o 365" para convertir
  EA a diaria — ya resuelto porque `EffectiveRateConverter` usa la fórmula correcta
  `(1+i_EA)^(1/365) - 1`. No reinventar esto.
- Los datos de IBC/usura reales desde 1997 hasta 2026 ya están transcritos en el PDF (páginas 58-61) por
  si se necesitan para tests con escenarios históricos reales.

**Estado:** Implementado (2026-07-15) — ver `docs/superpowers/plans/2026-07-15-area-comercial.md` y
`docs/superpowers/specs/2026-07-15-area-comercial-design.md`. Pendiente explícito que quedó fuera de
este sprint (decisión tomada con el usuario, no un olvido): el anatocismo condicionado del Art. 886
C.Co. — `CompoundInterest` (`app/engine/interest/compound_interest.py`) sigue huérfano porque requiere
modelar si hubo demanda judicial o acuerdo posterior de capitalización, campos que no existen hoy en
`Obligacion`. También queda documentado como limitación conocida (heredada de Civil, no introducida
aquí): `MemoryRateProvider` da resultados correctos por obligación solo cuando el expediente tiene una
sola obligación comercial, o cuando (con varias) los tramos de fecha de las obligaciones no se solapan
con tasas distintas — la tasa se busca por fecha calendario, no por obligación.

**Definición de Hecho:**
- `ComercialStrategy` liquida obligaciones comerciales reales (con y sin abonos) con TDD siguiendo el
  mismo patrón que `tests/services/test_area_strategy.py` para `CivilFamiliaStrategy`.
- Tests de validación de usura (tasa pactada > 1.5×IBC).
- Área "Comercial" seleccionable y operable desde la GUI end-to-end (smoke test manual como el de la
  Tarea 17 del MVP).
- Suite completa sigue en verde.

---

## Sprint 3 — Área Laboral

**Prioridad sugerida:** Alta.
**Depende de:** Nada estrictamente. Se beneficia del Sprint 5 (SMLMV histórico) para liquidaciones de años
anteriores, pero puede arrancar con el SMLMV vigente hardcodeado como parámetro de entrada.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, sección "OBLIGACIONES EN DERECHO LABORAL"
  (páginas 51-52) y "C. Derecho Laboral" dentro de "INDICADORES DE CÁLCULO" (página 9).
- Mismo PDF, tabla histórica de Salario Mínimo 1984-2027 (páginas 55-57).

**Código existente a reutilizar (¡leer antes de escribir nada nuevo!):**
- `app/engine/temporal/schedulers/labor.py` → `LaborScheduler(salario_base, dias_trabajados, anio)` **ya
  existe y ya genera 4 eventos**: `CESANTIAS`, `INTERESES_CESANTIAS`, `PRIMA_JUNIO`, `PRIMA_DICIEMBRE`.
  Cubierto por `tests/temporal/test_labor.py` (2 tests, ambos pasan).
  - ⚠️ **Posible bug a verificar primero**: el cálculo de `INTERESES_CESANTIAS` multiplica
    `monto_cesantias * dias * 0.12 / 360` (interés sobre cesantías, aplicado otra vez por los mismos días
    trabajados) en vez de `monto_cesantias * 0.12` directo (12% anual simple sobre el saldo de cesantías,
    como pide el PDF pág. 51: `(Cesantías × 0.12 × días)/360`). Con 360 días exactos ambas fórmulas
    coinciden por casualidad (por eso el test actual no lo revela) — con días parciales (ej. 180) van a
    dar resultados distintos. Verificar contra la fórmula del PDF antes de construir encima.
  - **Falta**: no genera evento de `VACACIONES` (divisor 720 según el PDF pág. 51, tabla de prestaciones)
    — hay que agregarlo al scheduler.
- `app/services/area_strategy.py` → mismo patrón que `CivilFamiliaStrategy`, pero la fuente de eventos acá
  es `LaborScheduler.generate()` en vez de `FamilyScheduler`.
- `app/engine/indexation/smmlv.py` → `SMMLVCalculator.to_pesos(smmlv_quantity, current_year_smmlv)` ya
  existe para conversiones SMLMV→pesos si se necesitan (ej. topes de IBC de seguridad social 1-25 SMMLV).

**Código nuevo a crear:**
- Agregar generación de `VACACIONES` a `LaborScheduler` (divisor 720, no 360).
- Corregir (si se confirma el bug) la fórmula de `INTERESES_CESANTIAS`.
- Implementar `LaboralStrategy.liquidar()` en `app/services/area_strategy.py` (hoy lanza
  `AreaNoImplementadaError`, línea ~99).
- Motor de Indemnización Moratoria Art. 65 CST — **régimen bifásico**, no existe hoy en ningún lado:
  - Fase 1 (día 1 a día 720 / mes 25): un día de salario por cada día de retardo.
  - Fase 2 (día 721 en adelante): cesa el "día de salario", empiezan a correr intereses moratorios a la
    tasa máxima legal (SFC) sobre salarios y cesantías adeudadas.
  - Sugerido: nueva clase `app/engine/labor/moratory_indemnity.py` o método dedicado en
    `LaboralStrategy`, con tests explícitos para el punto de quiebre exacto (día 720 vs 721).
- Middleware de seguridad social (cotizaciones IBC, pensión 16%, salud 12.5%, ARL por nivel de riesgo,
  FSP si IBC≥4 SMMLV) — el PDF (pág. 51-52) lo describe con detalle; **evaluar con el usuario si esto
  entra en el alcance del área Laboral de BASTIUM (liquidación de procesos judiciales) o si es un módulo
  de nómina fuera de alcance del producto** — no asumir, preguntar antes de construir.

**Alcance incluido:**
- Cesantías, intereses a cesantías (corregidos), prima (junio/diciembre), vacaciones.
- Indemnización moratoria Art. 65 CST bifásica.
- `LaboralStrategy` cableada al registry.
- Habilitar área "Laboral" en `app/core/constants.py`.

**Alcance explícitamente excluido:**
- Seguridad social / cotizaciones (pendiente de confirmar alcance con el usuario, ver arriba).
- Conteo real de calendario (365/366) vs año comercial de 360 para densidad de semanas de pensión (PDF
  pág. 52 menciona la Sentencia SL138-2024 de la Corte Suprema que cambió esto) — Régimen de Prima Media
  y pensiones quedan fuera de este sprint, son un dominio aparte.

**Riesgos / notas técnicas conocidas:**
- El PDF exige un flag `use_360_days_standard: boolean` por perfil de cálculo (año comercial 360 vs año
  civil 365/366) porque Laboral usa 360 pero Comercial normalmente usa 365. Si el Sprint 2 (Comercial) ya
  se hizo, revisar cómo resolvió esto para no duplicar el mecanismo.

**Definición de Hecho:**
- `LaboralStrategy` liquida con TDD (obligación puntual = liquidación al terminar contrato, con cesantías
  + intereses + prima + vacaciones + indemnización moratoria si aplica).
- Test específico del punto de quiebre día 720/721 del Art. 65 CST.
- Suite completa en verde.

---

## Sprint 4 — Área Sancionatorio y Honorarios

**Prioridad sugerida:** Media.
**Depende de:** Nada estrictamente; se beneficia del Sprint 5 (UVT/SMLMV históricos) pero puede arrancar
con los valores vigentes actuales como parámetros.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, "D. Derecho Sancionatorio" y "E. Litigio y
  Cobro de Honorarios" (páginas 10, dentro de "INDICADORES DE CÁLCULO").
- Mismo PDF, sección "OBLIGACIONES EN DERECHO COMERCIAL" → "Insolvencia de Persona Natural" (página 46)
  para tarifas de Centro de Conciliación en fracciones de SMLMV (no es Sancionatorio/Honorarios estricto
  pero usa la misma lógica de conversión).

**Código existente a reutilizar:**
- `app/engine/indexation/smmlv.py` → `SMMLVCalculator.to_pesos()` reutilizable para la pata SMLMV de la
  conversión SMLMV→UVT.
- Mismo patrón `area_strategy.py` que los sprints anteriores.

**Código nuevo a crear:**
- Conversor SMLMV↔UVT por vigencia histórica: nueva clase (sugerido
  `app/engine/indexation/smlmv_to_uvt.py`), regla exacta del PDF: si el hecho es anterior al 2020-01-01,
  la base es el SMLMV de ese año; si es posterior, la UVT histórica de la DIAN vigente. Requiere datos
  históricos de UVT (ver Sprint 5 — sin esos datos, este conversor no se puede probar con casos reales
  anteriores a la fecha actual).
- `SancionatorioStrategy.liquidar()` (hoy lanza `AreaNoImplementadaError`, línea ~106).
- `HonorariosStrategy.liquidar()` (hoy lanza `AreaNoImplementadaError`, línea ~113):
  - Tarifa fija (retainer).
  - Cuota litis: validación de que `honorarios_fijos + cuota_litis <= 50% del beneficio obtenido` (el PDF
    en una sección dice 50%, en otra —"E. Litigio y Cobro de Honorarios" del documento EFDJ final— dice
    30%; **hay una inconsistencia real entre dos secciones del mismo PDF, resolver con el usuario cuál
    tope usar antes de codificarlo**, no asumir un valor).
  - Costas judiciales / agencias en derecho: porcentajes según rangos del Consejo Superior de la
    Judicatura (ej. Acuerdo PCSJA20-11556, 3%-7% de las pretensiones reconocidas) — estos rangos no están
    en el PDF como tabla estructurada, solo mencionados; hay que buscar el acuerdo real o pedir al
    usuario que aporte la tabla de rangos vigente.

**Alcance incluido:**
- `SancionatorioStrategy` y `HonorariosStrategy` reales.
- Conversor SMLMV→UVT con vigencia histórica.
- Validación de tope de cuota litis (una vez resuelta la inconsistencia 50%/30% con el usuario).

**Alcance explícitamente excluido:**
- Carga completa de series históricas UVT/SMLMV → Sprint 5.
- Costas/agencias con tabla completa de rangos del Consejo Superior si no se consigue la fuente exacta —
  documentar como pendiente explícito en vez de inventar porcentajes.

**Riesgos / notas técnicas conocidas:**
- Inconsistencia de tope de cuota litis (30% vs 50%) detectada en el PDF — **no elegir unilateralmente**,
  preguntar al usuario primero (es una decisión de negocio/legal, no técnica).

**Definición de Hecho:**
- Ambas estrategias liquidan con TDD.
- Tests de conversión SMLMV→UVT para fechas antes y después de 2020-01-01.
- Test de validación de tope de cuota litis con el valor que confirme el usuario.
- Suite completa en verde.

**Estado:** Implementado (2026-07-19) — ver
`docs/superpowers/plans/2026-07-17-sprint4-sancionatorio-honorarios.md` y
`docs/superpowers/specs/2026-07-17-sprint4-sancionatorio-honorarios-design.md`. Decisiones tomadas con el
usuario durante el brainstorming previo (no asumidas unilateralmente):
- (a) los dos topes de cuota litis (30% individual sobre la cuota litis sola, 50% total sobre honorarios
  fijos + cuota litis) se aplican **simultáneamente**, no como alternativas — el PDF los menciona en
  secciones distintas y no como excluyentes entre sí.
- (b) las costas judiciales se capturan como un **porcentaje manual** por obligación
  (`costas_pct_manual`), en vez de una tabla estructurada de rangos del Consejo Superior de la
  Judicatura (Acuerdo PCSJA20-11556), porque no se consiguió una fuente confiable con esos rangos
  completos.
- (c) la conversión SMLMV→UVT sigue sin cubrir hechos posteriores al 2020-01-01: al no existir todavía la
  tabla histórica de UVT (pendiente del Sprint 5), `resolver_base_sancion` lanza `UVTNoDisponibleError`
  en vez de adivinar un valor.

---

## Sprint 5 — Carga de datos históricos (IPC, SMLMV, IBC, Tasa de Usura, UVT)

**Prioridad sugerida:** Alta — es la dependencia común de los Sprints 2, 3, 4 y 8 para liquidaciones
históricamente exactas (aunque ninguno de ellos está estrictamente bloqueado por este, todos mejoran
mucho con datos reales en vez de un solo valor "vigente").

**Depende de:** Nada.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`:
  - Página 55-57: Salario Mínimo Legal 1984-2027 (tabla completa año por año).
  - Páginas 58-61: IBC e Interés de Usura de la Superintendencia Financiera, tramos desde 1997-07-01
    hasta 2026-07-31 (por rango de fechas "DESDE"/"HASTA", separado por línea de crédito: comercial,
    consumo, microcrédito, popular productivo rural — la tabla tiene columnas distintas según el período,
    leer con cuidado el cambio de estructura a partir de 2007).
  - Página 62: IPC (Índice de Precios al Consumidor) anual 1967-2025 — nota: esta tabla trae la
    **variación porcentual anual**, no el índice base 100 acumulado; para usar la fórmula
    `Va = Vh × (IPC_final / IPC_inicial)` de `IPCIndexation.calculate()` hace falta convertir estas
    variaciones anuales a un índice acumulado (base fija en algún año), no se pueden usar los porcentajes
    directos como si fueran el índice.

**Código existente a reutilizar:**
- `app/engine/indexation/historical_index.py` — el archivo destino, hoy vacío (0 bytes).
- `app/engine/interest/provider.py` → `MemoryRateProvider` / `RatePeriod` ya tiene el modelo de "tramos
  con vigencia" que puede inspirar el diseño de la tabla histórica (o reutilizarse directamente si el
  historial se carga como una serie de `RatePeriod`).
- `database/models.py` — si se decide persistir esto en SQLite en vez de en código Python estático (ver
  decisión abajo), seguir el mismo patrón de `Base`/`Mapped`/`mapped_column` ya usado ahí.

**Decisión de diseño a tomar antes de codificar (consultar con el usuario o decidir con criterio propio
y documentarlo):**
- ¿Los datos históricos viven como constantes Python en `historical_index.py` (simple, versionado en
  git, pero requiere redeploy para actualizar) o como tabla SQLite poblada por una migración/seed (más
  flexible, permite actualizar sin tocar código, pero es más trabajo)? El PDF (pág. 8) sugiere tablas
  `macro_indicators` e `indicator_historical_rates` consultadas idealmente vía cron/API oficiales — eso
  es una arquitectura más grande que lo que este sprint necesita. Para BASTIUM hoy (app de escritorio de
  un solo usuario, sin backend/API), lo pragmático es constantes Python versionadas, con una función
  clara para "agregar el dato del próximo mes/año" cuando se publique.

**Código nuevo a crear:**
- `app/engine/indexation/historical_index.py`: al menos tres estructuras (o clases) con los datos
  transcritos del PDF:
  - Serie de IPC anual (convertida a índice acumulado, no el % de variación crudo — ver nota arriba).
  - Serie de SMLMV anual 1984-2027 (transcripción directa de la tabla del PDF).
  - Serie de IBC/Usura por tramos de fecha (transcripción de las páginas 58-61; ojo con los tramos que
    cambian de columna a partir de 2011 cuando aparece la columna separada de "microcrédito").
- Funciones de consulta: `get_ipc_for_date(fecha) -> Decimal`, `get_smlmv_for_year(año) -> Decimal`,
  `get_ibc_usura_for_date(fecha) -> tuple[Decimal, Decimal]`.
- UVT histórica: el PDF no trae una tabla completa de valores UVT año por año (solo menciona que se
  actualiza cada 1 de enero según IPC oct-oct) — **puede que haya que pedir al usuario la tabla real de
  UVT por año, o derivarla, o buscarla** si se necesita para el Sprint 4.

**Alcance incluido:**
- Transcripción y estructuración de las 3 series de datos que el PDF sí trae completas (IPC, SMLMV,
  IBC/Usura).
- Funciones de consulta por fecha/año.
- Tests unitarios verificando algunos valores puntuales conocidos contra el PDF (ej. SMLMV 2026 =
  $1.750.905, IPC 2025 = 5.10%).

**Alcance explícitamente excluido:**
- Automatización de actualización mensual/anual vía scraping o API del DANE/SFC/Banco de la República
  (el PDF lo sugiere como "ideal" pero es un proyecto de integración aparte, no de este sprint).
- Tabla UVT histórica completa si no se consigue la fuente (documentar como pendiente).

**Estado:** Implementado (2026-07-15) para SMLMV, IPC e IBC/Tasa de Usura — ver
`docs/superpowers/plans/2026-07-15-carga-datos-historicos.md` y
`docs/superpowers/specs/2026-07-15-carga-datos-historicos-design.md`. La serie de IBC/Usura modela
únicamente la línea "Consumo y Ordinario" (sucesora de "Comercial" desde 2007) — Microcrédito y Crédito
Popular Productivo Rural quedan fuera de alcance, documentado, no omitido por descuido. UVT sigue
pendiente: el PDF no trae una tabla histórica completa, solo menciones dispersas (confirmado por
búsqueda de texto en las 80 páginas del documento) — bloquea parcialmente el Sprint 4 hasta conseguir la
fuente real.

**Definición de Hecho:**
- `historical_index.py` deja de estar vacío, con datos verificables contra el PDF.
- `IPCIndexation` puede recibir índices reales desde esta fuente en vez de valores hardcodeados de test.
- Suite completa en verde.

---

## Sprint 6 — Calendario de días hábiles judiciales y términos procesales

**Prioridad sugerida:** Media — es dependencia del Sprint 7 (prescripción/caducidad).

**Depende de:** Nada.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, secciones "El Régimen de Términos" (páginas
  5-6), "1. Unidades de Medida Temporal" y "2. Estructuras de Control del Tiempo Procesal" (páginas 23-24),
  y la nota puntual de "Lógica de Notificación Digital: 2 días hábiles tras el envío" (página 4).

**Código existente a reutilizar:**
- `app/engine/time/calendar.py` → `CalendarUtils.safe_create_date()` ya existe pero **solo** resuelve
  desbordes de fin de mes (ej. 30 de febrero → último día real). No tiene ningún concepto de día hábil.
  Extender este archivo, no crear uno paralelo.

**Código nuevo a crear:**
- Lista de festivos colombianos (fijos + móviles con ley Emiliani) — necesita una fuente de datos (no
  viene en el PDF; hay librerías Python de festivos colombianos, ej. `holidays` con `country="CO"`, o
  transcribir manualmente; **evaluar agregar una dependencia externa vs. mantener una tabla propia** —
  decisión a tomar, documentar el porqué).
- `CalendarUtils.es_dia_habil(fecha) -> bool`.
- `CalendarUtils.sumar_dias_habiles(fecha_inicio, n) -> date`.
- `CalendarUtils.dias_habiles_entre(fecha_inicio, fecha_fin) -> int`.
- Lógica de notificación digital: función que dado un `fecha_envio`, retorne la fecha en que se entiende
  surtida la notificación (2 días hábiles después).
- Modelador de términos con sus 4 modificadores de estado (interrupción = reset, suspensión = pausa,
  reanudación = resume, expiración) — el PDF (pág. 25) los describe como funciones puras sobre un estado
  de "reloj procesal"; sugerido como una pequeña máquina de estados, no como fechas sueltas.

**Alcance incluido:**
- Cómputo de días hábiles judiciales excluyendo sábados, domingos y festivos.
- Cómputo de meses/años de fecha a fecha (con la regla de "si el día no existe, vence el último día del
  mes" — ya cubierta parcialmente por `safe_create_date`, verificar que aplique igual aquí).
- Lógica de notificación digital a 2 días hábiles.

**Alcance explícitamente excluido:**
- Vacancia judicial / vacaciones colectivas del sistema judicial (el PDF las menciona como "pausa
  automática" pero no da fechas exactas — pedir al usuario si hace falta modelarlas con precisión o basta
  con festivos + fines de semana).

**Definición de Hecho:**
- Tests con casos conocidos (ej. un término de 10 días hábiles que cruza un fin de semana y un festivo,
  verificar la fecha de vencimiento exacta).
- Suite completa en verde.

---

## Sprint 7 — Motor de prescripción y caducidad

**Prioridad sugerida:** Media.
**Depende de:** Sprint 6 (calendario de días hábiles) para cómputo preciso de plazos.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, sección "3. Estados de Extinción de
  Derechos" (páginas 24-25, Caducidad y Prescripción) y "II. Módulo de Tiempo y Extinción de la Acción" en
  "EXCEPCIONES A LAS OBLIGACIONES" (páginas 32-33).

**Código existente a reutilizar:**
- Ninguno — este motor no existe hoy en ningún archivo `.py` (confirmado por grep en toda la base de
  código).
- `app/core/exceptions.py` → seguir el patrón de `AreaNoImplementadaError` para una nueva
  `ObligacionPrescritaError` / `DemandaCaducadaError` si aplica.

**Código nuevo a crear:**
- Sugerido: `app/engine/temporal/prescripcion.py` con:
  - `calcular_prescripcion(fecha_exigibilidad, tipo_accion) -> date` (fecha límite; 5 años ejecutiva, 10
    años ordinaria, 3 años honorarios profesionales, 1 año cheque acción de regreso, 3 años acción
    cambiaria directa — todos estos plazos están dispersos en varias secciones del PDF, consolidar en una
    sola tabla de constantes).
  - Soporte de **prescripción parcial en obligaciones de tracto sucesivo** (ej. cuotas alimentarias): cada
    cuota tiene su propio timestamp de vencimiento, se debe poder excepcionar la prescripción de cuotas
    individuales sin afectar las recientes — esto interactúa directamente con `FamilyScheduler` (las
    cuotas ya se generan como eventos individuales con fecha, así que la lógica de "cuál cuota
    prescribió" puede filtrar sobre esa lista de eventos).
  - `calcular_caducidad(fecha_hecho, tipo_proceso) -> date` (plazo fatal, no admite suspensión salvo
    conciliación extrajudicial hasta 3 meses).
  - Interrupción de prescripción por demanda notificada en tiempo (requiere fecha de radicación y fecha
    de notificación, con la regla de "si se notifica dentro del año, el efecto interruptor se retrotrae a
    la fecha de la demanda").

**Alcance incluido:**
- Cálculo de fecha límite de prescripción/caducidad según tipo de acción.
- Prescripción parcial por cuota en obligaciones periódicas.
- Interrupción por demanda.

**Alcance explícitamente excluido:**
- Integración con la GUI (bloquear el botón "Liquidar" si hay prescripción) — eso es un sprint de UI
  aparte una vez el motor exista y esté probado.

**Definición de Hecho:**
- Tests con los plazos de cada tipo de acción mencionados en el PDF.
- Test específico de prescripción parcial en una obligación recurrente tipo `CHILD_SUPPORT` con cuotas de
  hace más de 5 años mezcladas con cuotas recientes.
- Suite completa en verde.

---

## Sprint 8 — Conectar indexación IPC al área Civil/Familia

**Prioridad sugerida:** Media.
**Depende de:** Sprint 5 (sin datos históricos de IPC, no hay forma de resolver `IPC_inicial`/`IPC_final`
automáticamente a partir de una fecha).

**Documentos a consultar:**
- `specifications/03_motor_indexacion.md` (ya documenta el estado actual: implementado y probado, pero no
  conectado).
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, sección "SISTEMA DE CLASIFICACIÓN TÉCNICA DE
  INDEXACIÓN" completa (páginas 20-22) — trae la fórmula, cuándo procede, cuándo NO procede, y el
  protocolo de interpolación cuando la fecha no coincide con el cierre de un mes certificado.

**Código existente a reutilizar:**
- `app/engine/indexation/ipc.py` → `IPCIndexation.calculate(capital, initial_index, final_index)` YA
  ESTÁ IMPLEMENTADO Y PROBADO. Este sprint es 100% de integración, no de construir el motor matemático.
- `app/services/area_strategy.py` → `CivilFamiliaStrategy._construir_rate_provider()` es el lugar natural
  para, además de la tasa, resolver los índices IPC inicial/final por fecha (una vez exista Sprint 5).

**Código nuevo a crear:**
- Wiring en `CivilFamiliaStrategy.liquidar()`: para cada obligación, resolver `IPCIndexation.calculate()`
  usando el IPC de `fecha_origen` y el IPC de `fecha_corte` (vía las funciones de consulta del Sprint 5),
  y sumar el resultado como `indexation_amount` en el evento/resultado correspondiente.
- Interpolación cuando `fecha_corte` no coincide con el cierre de un mes certificado (PDF pág. 22,
  fórmula `Vo = (t1×V2 + t2×V1) / (t1+t2)`).
- Regla de "no doble indexación" si el monto ya viene expresado en una unidad ya actualizada (ej. SMMLV
  vigente) — validación explícita, no solo un comentario.

**Alcance incluido:**
- Indexación real conectada, opcional por obligación (algunas categorías la usan, otras no según el PDF).
- Interpolación de índices intermedios.

**Alcance explícitamente excluido:**
- Indexación para áreas Comercial (incompatible con intereses bancarios per el PDF) — eso es una
  validación de exclusión en Sprint 2, no una implementación aquí.

**Definición de Hecho:**
- Los tests de `CivilFamiliaStrategy` (Task 6 del plan MVP) siguen pasando y se agregan casos nuevos con
  indexación activada, verificando el resultado numérico contra un cálculo manual con la fórmula del PDF.
- Suite completa en verde.

---

## Sprint 9 — Motor de auditoría / bitácora

**Prioridad sugerida:** Baja (solo relevante si el producto pasa a multi-usuario; para uso individual de
un solo abogado, el valor es menor).

**Depende de:** Nada.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, "Requisitos de auditoría" (página 77) del
  documento EFDJ: toda liquidación debe exponer fórmula, fuente, fecha de consulta, vigencia usada, tramo
  aplicado y soporte documental; toda decisión automática debe guardar "por qué" eligió una regla; todo
  redondeo debe ser parametrizable y registrarse; todo cambio manual debe generar bitácora (usuario,
  fecha, motivo, evidencia); debe existir reconstrucción exacta de una liquidación histórica aunque las
  tasas hayan cambiado desde entonces.
- `specifications/05_motor_auditoria.md` (documenta el estado actual: vacío).

**Código existente a reutilizar:**
- `app/engine/audit/` — hoy solo tiene un `__init__.py` vacío, es el punto de partida.
- `app/engine/liquidation/result.py` → `LiquidationResult` ya guarda el historial completo de
  `LiquidationItem` por evento, lo cual da trazabilidad matemática (pero no de "quién" ni "cuándo se
  ejecutó la liquidación").
- `database/models.py` → seguir el mismo patrón de modelos SQLAlchemy para una nueva tabla de auditoría.

**Código nuevo a crear:**
- Decisión de diseño primero: ¿auditoría a nivel de aplicación (quién liquidó qué expediente y cuándo,
  tabla `AuditLog` en `database/models.py`) o auditoría a nivel de motor de cálculo (qué regla/tasa se
  usó en cada tramo, embebido en `LiquidationResult`)? El PDF pide ambas, pero son dos features distintas
  — consultar con el usuario cuál es más urgente si hay que priorizar.
- Modelo `AuditLog` (o similar): expediente_id, usuario, fecha, acción, motivo, snapshot del resultado.
- Extender `LiquidationItem`/`LiquidationResult` para exponer explícitamente qué regla/tasa/fuente se usó
  en cada tramo (parcialmente ya existe vía `interest_rate` por item, pero falta la fuente/vigencia).

**Alcance incluido:**
- Registro de quién ejecutó cada liquidación y cuándo.
- Trazabilidad de qué tasa/índice se usó por tramo (reutilizando lo que `LiquidationItem` ya expone,
  extendiéndolo si falta algo).

**Alcance explícitamente excluido:**
- Sistema de usuarios/roles (BASTIUM hoy no tiene autenticación ni multi-usuario; si se necesita
  auditoría por usuario, ese es un prerequisito de producto más grande a discutir primero).

**Definición de Hecho:**
- Tests de que una liquidación queda registrada con timestamp y puede reconstruirse.
- Suite completa en verde.

---

## Sprint 10 — Exportación de liquidación a PDF/Word

**Prioridad sugerida:** Media (valor visible para el usuario final, útil para presentar en juzgado).

**Depende de:** Nada (usa el `LiquidationResult` que ya existe).

**Documentos a consultar:**
- `specifications/06_motor_reportes.md`.
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, "7. Presentación ante Autoridades (Protocolo
  de UI)" (página 22) — requisitos formales para que una indexación sea aceptada por una autoridad:
  citar la fuente (DANE/Banco de la República), listar variables (Vh, fechas), desglosar el índice
  inicial/final, mostrar la operación aritmética completa antes del resultado final, y recordar que los
  indicadores económicos son "hecho notorio" (no requieren prueba documental adicional). El documento
  PDF exportado debería cumplir estos 5 puntos si incluye indexación.

**Código existente a reutilizar (¡y a generalizar, no reescribir desde cero!):**
- `app/reports/pdf.py` → `JudicialPDFGenerator(output_path).generar_documento(datos_rubros,
  ruta_grafica)` YA EXISTE y genera un PDF con reportlab, pero está **acoplado al dominio de Alimentos**:
  el título está hardcodeado como `"LIQUIDACIÓN PROVISIONAL DE ALIMENTOS"` y las columnas de la tabla son
  `CONCEPTO, CAPITAL EXIGIBLE, DÍAS MORA, INTERESES, TOTAL` (no calzan 1:1 con las columnas de
  `ResultadoLiquidacionView`, que son `Fecha, Concepto, Capital base, Tasa %, Interes, Pago, Saldo`).
  Generalizar el título y las columnas para que sirvan para cualquier área, o crear una segunda clase
  específica para liquidaciones civiles/comerciales reutilizando los estilos (`c_burgundy`, `c_cream`,
  etc.) ya definidos.
- `app/reports/charts.py` → `BastiumChartGenerator` (usado por el `main.py` viejo antes de la GUI) genera
  gráficas que `JudicialPDFGenerator.generar_documento()` embebe — revisar si sigue siendo compatible con
  la forma de los datos de `LiquidationResult` o si necesita un adaptador.
- `app/reports/word.py` — vacío, no hay nada que reutilizar; es 100% código nuevo. Sugerido usar
  `python-docx` (ya está en `requirements.txt`).

**Código nuevo a crear:**
- Adaptador entre `LiquidationResult` (formato interno del motor) y el formato de entrada que espera
  `JudicialPDFGenerator.generar_documento()` (lista de diccionarios con `concepto`, `capital`,
  `dias_mora`, etc.) — hoy no existe ese puente, el PDF viejo se alimentaba directo de
  `FamilyLawCalculator` (el código de consola descontinuado).
- Botón "Exportar a PDF" en `app/views/liquidaciones.py` (`ResultadoLiquidacionView`), que arme el
  adaptador de arriba y llame a `JudicialPDFGenerator`.
- Implementación completa de `app/reports/word.py` con `python-docx`, espejando la estructura del PDF.
- Botón "Exportar a Word" en la misma vista.

**Alcance incluido:**
- Exportar la pantalla de Resultado de Liquidación a PDF y a Word, para cualquier área operable (hoy solo
  Civil/Familia, pero el adaptador debe ser genérico para cuando se sumen Comercial/Laboral/etc.).

**Alcance explícitamente excluido:**
- Rediseño visual de las plantillas PDF/Word (mantener el estilo burdeos/crema ya definido en
  `JudicialPDFGenerator` salvo que el usuario pida otra cosa).

**Definición de Hecho:**
- Desde la GUI, liquidar un expediente real y exportarlo a PDF y a Word sin errores, con los montos
  coincidiendo exactamente con lo mostrado en pantalla.
- Test automatizado del adaptador `LiquidationResult` → formato de reporte (no hace falta testear
  reportlab/python-docx en sí, solo que el adaptador arme los datos correctos).

---

## Sprint 11 — Derecho Tributario (DIAN)

**Prioridad sugerida:** Baja / exploratoria — es un dominio jurídico completamente nuevo para BASTIUM
(hoy 0% implementado, ni un archivo), no una extensión de algo existente. Antes de planificarlo en detalle
como los sprints anteriores, **conviene confirmar con el usuario si esto es prioritario para el producto**
o si BASTIUM debe seguir enfocado en litigio civil/comercial/laboral/familia.

**Depende de:** Nada técnicamente, pero es una decisión de alcance de producto antes que técnica.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, "OBLIGACIONES EN DERECHO TRIBUTARIO,
  FINANCIERO, ECONÓMICO" completa (páginas 38-40): elementos del hecho gravable, depuración de Renta
  Líquida Gravable (flujo de 8 pasos: ingresos brutos → devoluciones → costos → renta bruta → deducciones
  → renta líquida → rentas exentas → renta líquida gravable), UVT, sanciones (extemporaneidad 5%
  mensual tope 100%, inexactitud 160%/200%, error aritmético 30%, sanción mínima 10 UVT), imputación
  tributaria de pagos (sanciones → intereses → impuesto, distinta del orden civil).

**Código existente a reutilizar:**
- Ninguno confirmado — no hay ningún módulo tributario, ni siquiera un directorio `app/engine/tax/` o
  similar. Este sería el primer sprint que crea ese árbol de directorios desde cero.
- `app/engine/interest/rate_conversion.py`, `MemoryRateProvider` — reutilizables para el interés
  moratorio tributario (Estatuto Tributario art. 635: tasa de usura vigente menos dos puntos
  porcentuales).

**Alcance sugerido si se aprueba el sprint:**
- Modelo de "Obligación Tributaria" (sujeto activo, sujeto pasivo, hecho gravado, base gravable, tarifa).
- Motor de depuración de Renta Líquida Gravable (los 8 pasos).
- Motor de sanciones (extemporaneidad, inexactitud, error aritmético, mínima).
- Interés moratorio tributario (usura - 2 puntos).
- Imputación tributaria de pagos con su propio orden (distinto del civil).

**Nota:** este sprint es el que menos detalle técnico tiene de los doce, a propósito — antes de invertir
tiempo de planificación fina, hay que confirmar que entra en el roadmap del producto.

---

## Sprint 12 — TRM y obligaciones en moneda extranjera

**Prioridad sugerida:** Baja.
**Depende de:** Nada.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, menciones de TRM dispersas en "INDICADORES
  DE CÁLCULO" (página 8, tabla de entidades — Banco de la República certifica la TRM diaria) y en
  "SISTEMA DE CLASIFICACIÓN TÉCNICA DE INDEXACIÓN", sección "E. TRM (Tasa Representativa del Mercado)"
  (página 21): funciona como mecanismo de revalorización cuando el pago se hace en el equivalente en
  pesos de curso legal, según la tasa de la fecha de la obligación o del pago (Art. 874 C.Co.).

**Código existente a reutilizar:**
- Ninguno — cero coincidencias de "TRM" o "moneda extranjera" en todo el código Python.
- El patrón de `historical_index.py` del Sprint 5 es el lugar natural para agregar una serie histórica de
  TRM diaria, si se aprueba este sprint.

**Alcance sugerido si se aprueba el sprint:**
- Campo de moneda en `Obligacion` (`database/models.py`) — hoy todas las obligaciones son implícitamente
  en pesos colombianos.
- Conversor TRM histórica por fecha (obligación) y por fecha (pago), ya que el PDF indica que ambas
  fechas son relevantes según el caso.
- Wiring en el motor de liquidación para que el capital se convierta a pesos antes de aplicar interés.

**Nota:** de menor prioridad que los sprints 2-4 (áreas del derecho) — es una feature transversal para
casos específicos de comercio internacional, poco frecuente en la práctica de un despacho promedio.
Confirmar con el usuario si vale la pena antes de planificar en detalle.

---

## Sprint 13 — Arquitectura de motor de reglas versionado (EFDJ)

**Prioridad sugerida:** Decisión arquitectónica, no un sprint de features — leer la nota antes de
planificar nada.

**Depende de:** Idealmente los Sprints 2-4 ya deberían estar hechos (para tener 5 áreas reales operando
como referencia de qué reglas existen) antes de decidir si vale la pena migrar a este patrón.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, la sección final completa "REGLAS DE
  CÁLCULO" (páginas 70-80): entidades maestras (Obligación, Sujeto, Evento jurídico, Rubro liquidable,
  Regla, Indicador externo, Soporte probatorio), estados funcionales, el catálogo de más de 40 reglas
  propuestas con prefijos `R-CIV-*`, `R-COM-*`, `R-FAM-*`, `R-LAB-*`, `R-TRI-*`, `R-SAN-*`, `R-PAG-*`,
  `R-EXT-*`, `R-PROC-*`, `R-COS-*`, `R-HON-*`; el "Esquema canónico de regla EFDJ" (página 78, con 24
  campos por regla: id, hecho_disparador, condiciones_de_entrada/exclusión, vigencia, fórmula,
  compatibilidades, prueba_requerida, etc.); y el algoritmo abstracto de liquidación por tramos
  (`Timeline → Segmentos → por cada segmento: ReglaVigente/Base/Duración/Fórmula/Resultado`).

**Qué es esto realmente:** el PDF describe una arquitectura donde las reglas jurídicas viven como **datos
versionados y consultables** (una tabla/catálogo con vigencia, condiciones, fórmula) en vez de como
**código Python hardcodeado por estrategia**, que es como está construido BASTIUM hoy (`area_strategy.py`
con una clase por área, cada una con su propia lógica en Python). Migrar a un motor de reglas data-driven
es un cambio arquitectónico grande: permitiría, por ejemplo, agregar una regla nueva sin desplegar código,
o auditar "por qué se aplicó esta regla y no otra" de forma automática (esto conecta directo con el
Sprint 9 de auditoría). Pero también es mucho más trabajo y complejidad que seguir agregando estrategias
Python, y el beneficio solo se nota si BASTIUM va a tener MUCHAS reglas cambiando con frecuencia (varias
por año) o si se necesita que alguien sin conocimientos de Python pueda modificar reglas.

**Recomendación:** no planificar tareas técnicas de este sprint todavía. Lo primero es una conversación
con el usuario (tipo `superpowers:brainstorming`) para decidir si el patrón actual de estrategias Python
(que ya funciona, ya tiene 5 áreas registradas, y es simple de entender y testear) es suficiente para el
tamaño real de BASTIUM, o si de verdad hace falta la complejidad de un catálogo de reglas versionado.
Construir esto sin esa conversación previa es el riesgo de sobre-ingeniería más grande de todo este
backlog.

---

## Backlog técnico / limpieza (sin sprint asignado, tareas pequeñas e independientes)

- **Resolver el motor de allocation duplicado**: hay DOS clases `AllocationEngine` con firmas
  distintas — `app/engine/allocation/allocator.py` (método de instancia `allocate(self, payment:
  Payment, obligations: list[Obligation])`, `raise NotImplementedError`, código huérfano que nadie
  importa) vs. `app/engine/liquidation/allocation.py` (método estático `allocate(payment_amount,
  current_debt, payment_date)`, implementación real usada por `LiquidationCore`). Decidir: ¿eliminar
  `app/engine/allocation/allocator.py` por completo (y su carpeta si queda vacía), o hay algún caso de
  uso futuro (el modelo de dominio `app.domain.obligation.base.Obligation` que usa) que lo justifique?
- **Archivo vacío sin uso**: `app/engine/financial/allocation.py` está vacío (0 bytes) y coincide de
  nombre con los dos de arriba — probablemente un archivo abandonado a mitad de refactor. Confirmar que
  nada lo importa y eliminarlo.
- **Wiring de `CompoundInterest`**: `app/engine/interest/compound_interest.py` tiene una implementación
  completa y correcta de interés compuesto, pero ningún motor la invoca hoy — queda relevante recién en
  el Sprint 2 (anatocismo comercial condicionado).
- **Múltiples tasas de interés simultáneas por expediente**: hoy `CivilFamiliaStrategy` usa una sola tasa
  para todo el expediente (tomada de la primera obligación) — si un expediente real tiene obligaciones a
  tasas distintas, eso no se soporta todavía. Evaluar si esto amerita su propio sprint o se resuelve como
  parte del Sprint 2/3 al construir las otras estrategias.
- ~~Validar/enable Windows "Long Paths" en la máquina de desarrollo~~ — **resuelto** (2026-07-15): se
  habilitó `LongPathsEnabled=1` en el registro de Windows para poder instalar PySide6 dentro de la ruta
  profunda de OneDrive, con confirmación previa del usuario.
- Confirmar si conviene excluir `.venv/` de la sincronización de OneDrive (hoy está en `.gitignore` pero
  OneDrive igual intenta sincronizar carpetas no versionadas dentro de la carpeta del proyecto).
- **Duplicación de `_eventos_de_obligacion` entre `CivilFamiliaStrategy` y `ComercialStrategy`**: el
  método que mapea una `Obligacion` PUNTUAL/RECURRENTE a `Event`(s) es idéntico byte a byte en las dos
  clases (`app/services/area_strategy.py`) — no tiene nada específico del área, solo depende de `tipo`.
  Vale la pena subirlo a `AreaStrategy` (o extraerlo a una función compartida) antes de escribir la
  tercera estrategia real (`LaboralStrategy`, Sprint 3), para no triplicar el copy-paste. Detectado en
  code review del Sprint 2 (`docs/superpowers/plans/2026-07-15-area-comercial.md`).
- **Misma duplicación en `_construir_rate_provider`**: `SancionatorioStrategy` y `HonorariosStrategy`
  (Sprint 4) repiten, casi byte a byte, el mismo patrón de "un solo tramo de tasa plana desde la
  obligación más antigua hasta la fecha de corte" que ya existe en `CivilFamiliaStrategy` y
  `ComercialStrategy`. Es la misma clase de problema que el punto anterior (`_eventos_de_obligacion`) y
  debería resolverse junto con él la próxima vez que se toque `area_strategy.py`, en vez de seguir
  copiando el método por cada estrategia nueva. Detectado en code review del Sprint 4
  (`docs/superpowers/plans/2026-07-17-sprint4-sancionatorio-honorarios.md`, Task 5).
- **`ObligacionFormDialog.guardar()` creciendo hacia "god method"**: cada área nueva (Comercial,
  Sancionatorio, Honorarios) le agrega su propio bloque `if es_X: try: ... except: raise ValueError(...)`
  dentro de `app/views/obligaciones.py`. Hoy (después del Sprint 4) tiene 4 ramas implícitas y ~90 líneas;
  sigue siendo legible, pero cada área nueva lo empeora. Si se agrega Laboral (Sprint 3) u otra área más,
  vale la pena extraer un `_parse_area_campos()` (o una tabla de specs por campo: nombre, kwarg, mensaje
  de error, requerido) en vez de seguir apilando ramas, espejando la separación que `area_strategy.py` ya
  tiene por estrategia. Detectado en code review del Sprint 4
  (`docs/superpowers/plans/2026-07-17-sprint4-sancionatorio-honorarios.md`, Task 7).
