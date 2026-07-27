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
- `docs/specifications/01_motor_temporal.md` … `07_motor_juridico_familia.md` — qué hace cada motor hoy.
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf` (raíz del repo) — documento maestro de
  requisitos de TODO el sistema jurídico previsto (todas las áreas, motor de reglas **EFDJ** —
  **E**specificación **F**uncional del **D**ominio **J**urídico, el nombre que el propio PDF usa en su
  página 63 para el catálogo de reglas versionadas —, datos históricos, tributario, auditoría). El MVP
  solo implementó una fracción pequeña de este documento (interés civil sin indexación). Cada sprint abajo
  cita las páginas exactas de este PDF que aplican.
- Suite de tests: 81 passed a fecha 2026-07-15 (`pytest.ini` usa `--import-mode=importlib` +
  `consider_namespace_packages=true` para evitar colisión de nombre `tests/database` vs `database/` — no
  tocar esa config sin necesidad). 367 passed, 1 skipped a fecha 2026-07-21, tras cerrar los Sprints 2-13.

**Sprints 14-22 (nuevos, 2026-07-21):** los Sprints 2-13 quedaron todos completados, pero cada cierre dejó
pendientes explícitos (decisiones de alcance sin confirmar, fuentes de datos no conseguidas, o cambios de
fondo aplazados a propósito). Los Sprints 14-22 son exactamente esos pendientes, convertidos en sprints
autocontenidos para poder trabajarlos uno por uno: Sprint 14 (tabla UVT, desbloqueador común), Sprint 15
(cierre del Sprint 11b tributario), Sprint 16 (seguridad social/incapacidades laborales), Sprint 17
(módulo pensional), Sprint 18 (costas judiciales con tabla real), Sprint 19 (anatocismo comercial
condicionado), Sprint 20 (indexación sobre capital indexado, "Suma Única"), Sprint 21 (múltiples tasas
simultáneas por expediente) y Sprint 22 (limpieza técnica acumulada, sin relación con el PDF de
requisitos). Varios de estos (16, 20) requieren una conversación previa con el usuario antes de codificar,
igual que exigió el Sprint 13 con el EFDJ — no arrancarlos sin esa validación.

**Sprints 23-30 (nuevos, 2026-07-21):** auditoría transversal de calidad de código y documentación (bugs
de ejecución, lógica, concurrencia, dependencias, rendimiento, seguridad, escalabilidad, mantenibilidad,
gaps funcionales, validación de datos, UX, CI/CD, versionado, y calidad de la documentación), hecha con 4
agentes en paralelo y verificada manualmente en los hallazgos de mayor severidad antes de documentarla acá.
No tiene relación con el PDF de requisitos — son defectos y deuda encontrados en el código/documentación
ya existente, no funcionalidad jurídica faltante. Los más urgentes: Sprint 23 (dos bugs reales: sobrepago
que desaparece silenciosamente del resultado, y reconstrucción de auditoría que puede lanzar `KeyError` en
liquidaciones históricas), Sprint 24 (formularios y `parametro_service` aceptan datos absurdos sin
validar) y Sprint 29 (rutas rotas `specifications/` en README/GUIA/Pendientes, numeración duplicada en
GUIA_USUARIO.md que rompe un enlace interno, y 4 specs de motores desactualizadas).

**Sprints 31-37 (nuevos, 2026-07-21): UX/UI de la GUI.** BASTIUM hoy es funcional pero visualmente es 100%
el estilo nativo de Qt/Windows sin ninguna identidad propia: cero `setStyleSheet`/`QPalette` en toda la
app, la tipografía de marca (`AncizarSans`, en `app/assets/fonts/`) y los colores de marca (burdeos/crema,
ya definidos en `app/reports/pdf.py` para los reportes) nunca se aplican a la GUI en vivo, no hay íconos
(solo emoji sueltos en la navegación), y `app/views/dashboard.py` sigue vacío pese a que la app abre
directo a un listado plano sin ningún resumen. Los Sprints 31-37 cubren, en orden de dependencia: Sprint 31
(tema visual base: color/tipografía/íconos — los demás dependen de este), Sprint 32 (navegación con
breadcrumb y atajos), Sprint 33 (dashboard real de inicio), Sprint 34 (UX de formularios), Sprint 35
(búsqueda/filtros/estados vacíos en listados), Sprint 36 (feedback no bloqueante y jerarquía de botones) y
Sprint 37 (persistencia de ventana y accesibilidad de teclado). Ninguno depende del PDF de requisitos — son
mejoras de experiencia de usuario sobre una app ya funcional.

---

## Índice de sprints

- [Sprint 2 — Área Comercial ✅ Completado](#sprint-2--área-comercial--completado)
- [Sprint 3 — Área Laboral ✅ Completado](#sprint-3--área-laboral--completado)
- [Sprint 4 — Área Sancionatorio y Honorarios ✅ Completado](#sprint-4--área-sancionatorio-y-honorarios--completado)
- [Sprint 5 — Carga de datos históricos (IPC, SMLMV, IBC, Tasa de Usura, UVT) ✅ Completado](#sprint-5--carga-de-datos-históricos-ipc-smlmv-ibc-tasa-de-usura-uvt--completado)
- [Sprint 6 — Calendario de días hábiles judiciales y términos procesales ✅ Completado](#sprint-6--calendario-de-días-hábiles-judiciales-y-términos-procesales--completado)
- [Sprint 7 — Motor de prescripción y caducidad ✅ Completado](#sprint-7--motor-de-prescripción-y-caducidad--completado)
- [Sprint 8 — Conectar indexación IPC al área Civil/Familia ✅ Completado](#sprint-8--conectar-indexación-ipc-al-área-civilfamilia--completado)
- [Sprint 9 — Motor de auditoría / bitácora ✅ Completado](#sprint-9--motor-de-auditoría--bitácora--completado)
- [Sprint 10 — Exportación de liquidación a PDF/Word ✅ Completado](#sprint-10--exportación-de-liquidación-a-pdfword--completado)
- [Sprint 11 — Derecho Tributario (DIAN) ✅ Completado (11a)](#sprint-11--derecho-tributario-dian--completado-11a)
- [Sprint 12 — TRM y obligaciones en moneda extranjera ✅ Completado](#sprint-12--trm-y-obligaciones-en-moneda-extranjera--completado)
- [Sprint 13 — Arquitectura de motor de reglas versionado (EFDJ) ✅ Completado](#sprint-13--arquitectura-de-motor-de-reglas-versionado-efdj--completado)
- [Sprint 14 — Tabla histórica de UVT (DIAN) ✅ Completado](#sprint-14--tabla-histórica-de-uvt-dian--completado)
- [Sprint 15 — Tributario completo: sanciones, imputación y modelo de Obligación Tributaria (cierre del Sprint 11b) ✅ Completado](#sprint-15--tributario-completo-sanciones-imputación-y-modelo-de-obligación-tributaria-cierre-del-sprint-11b--completado)
- [Sprint 16 — Seguridad social, incapacidades y suspensiones contractuales (Laboral) ✅ Completado](#sprint-16--seguridad-social-incapacidades-y-suspensiones-contractuales-laboral--completado)
- [Sprint 17 — Módulo pensional (IBL, tasa de reemplazo, densidad de semanas) ✅ Completado](#sprint-17--módulo-pensional-ibl-tasa-de-reemplazo-densidad-de-semanas--completado)
- [Sprint 18 — Costas judiciales con tabla real de rangos (Acuerdo PCSJA20-11556)](#sprint-18--costas-judiciales-con-tabla-real-de-rangos-acuerdo-pcsja20-11556)
- [Sprint 19 — Anatocismo comercial condicionado (Art. 886 C.Co.) ✅ Completado](#sprint-19--anatocismo-comercial-condicionado-art-886-cco--completado)
- [Sprint 20 — Indexación sobre capital ya indexado (algoritmo "Suma Única")](#sprint-20--indexación-sobre-capital-ya-indexado-algoritmo-suma-única)
- [Sprint 21 — Múltiples tasas de interés simultáneas por expediente](#sprint-21--múltiples-tasas-de-interés-simultáneas-por-expediente)
- [Sprint 22 — Limpieza técnica acumulada](#sprint-22--limpieza-técnica-acumulada)
- [Sprint 23 — Bugs críticos de integridad financiera y auditoría](#sprint-23--bugs-críticos-de-integridad-financiera-y-auditoría)
- [Sprint 24 — Validación de datos: formularios de obligaciones y parámetros legales versionados](#sprint-24--validación-de-datos-formularios-de-obligaciones-y-parámetros-legales-versionados)
- [Sprint 25 — Rendimiento del motor de tasas, índices e historial](#sprint-25--rendimiento-del-motor-de-tasas-índices-e-historial)
- [Sprint 26 — Responsividad de la interfaz: liquidar/exportar sin congelar la UI](#sprint-26--responsividad-de-la-interfaz-liquidarexportar-sin-congelar-la-ui)
- [Sprint 27 — Limpieza de dependencias no usadas y código muerto adicional](#sprint-27--limpieza-de-dependencias-no-usadas-y-código-muerto-adicional)
- [Sprint 28 — CI/CD, versionado, housekeeping de repositorio e higiene de tests](#sprint-28--cicd-versionado-housekeeping-de-repositorio-e-higiene-de-tests)
- [Sprint 29 — Corrección de documentación desactualizada, inconsistente y con enlaces rotos ✅ Completado](#sprint-29--corrección-de-documentación-desactualizada-inconsistente-y-con-enlaces-rotos--completado)
- [Sprint 30 — Verificación de reglas de dominio con posible error de un día](#sprint-30--verificación-de-reglas-de-dominio-con-posible-error-de-un-día)
- [Sprint 31 — Sistema de diseño visual: tema, color, tipografía e íconos en la GUI](#sprint-31--sistema-de-diseño-visual-tema-color-tipografía-e-íconos-en-la-gui)
- [Sprint 32 — Navegación: barra mejorada, breadcrumb y atajos de teclado](#sprint-32--navegación-barra-mejorada-breadcrumb-y-atajos-de-teclado)
- [Sprint 33 — Pantalla de inicio real: dashboard con resumen y alertas](#sprint-33--pantalla-de-inicio-real-dashboard-con-resumen-y-alertas)
- [Sprint 34 — UX de formularios: agrupación, ayuda contextual y feedback en tiempo real](#sprint-34--ux-de-formularios-agrupación-ayuda-contextual-y-feedback-en-tiempo-real)
- [Sprint 35 — Búsqueda, filtros y estados vacíos en listados](#sprint-35--búsqueda-filtros-y-estados-vacíos-en-listados)
- [Sprint 36 — Feedback no bloqueante y jerarquía visual de botones](#sprint-36--feedback-no-bloqueante-y-jerarquía-visual-de-botones)
- [Sprint 37 — Comportamiento de ventana y accesibilidad de teclado](#sprint-37--comportamiento-de-ventana-y-accesibilidad-de-teclado)
- [Sprint 38 — Elegir licencia de código abierto y publicar `LICENSE`](#sprint-38--elegir-licencia-de-código-abierto-y-publicar-license)

---

## Sprint 2 — Área Comercial ✅ Completado

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

## Sprint 3 — Área Laboral ✅ Completado

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

**Estado:** Implementado (2026-07-19) — ver `docs/superpowers/plans/2026-07-19-area-laboral.md` y
`docs/superpowers/specs/2026-07-18-area-laboral-design.md`. Verificado durante el diseño: la fórmula de
`INTERESES_CESANTIAS` que este documento marcaba como sospechosa de bug en realidad coincide exactamente
con el PDF (pág. 51) — no se modificó. Pendientes explícitos que quedaron fuera de este sprint (decisión
tomada con el usuario, no un olvido): seguridad social (cotizaciones IBC, pensión, salud, ARL, FSP),
incapacidades y suspensiones contractuales, y el módulo pensional (IBL, densidad de semanas). También
queda documentado como limitación conocida: `dias_trabajados` se calcula como diferencia de calendario
simple, no con la convención comercial exacta de meses de 30 días que usa la nómina real (sobre-causa
prestaciones en ~1-2% para un año calendario completo).

**Definición de Hecho:**
- `LaboralStrategy` liquida con TDD (obligación puntual = liquidación al terminar contrato, con cesantías
  + intereses + prima + vacaciones + indemnización moratoria si aplica).
- Test específico del punto de quiebre día 720/721 del Art. 65 CST.
- Suite completa en verde.

---

## Sprint 4 — Área Sancionatorio y Honorarios ✅ Completado

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

## Sprint 5 — Carga de datos históricos (IPC, SMLMV, IBC, Tasa de Usura, UVT) ✅ Completado

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

## Sprint 6 — Calendario de días hábiles judiciales y términos procesales ✅ Completado

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

**Estado:** Implementado (2026-07-19) — `CalendarUtils` (`app/engine/time/calendar.py`) ganó
`es_dia_habil/sumar_dias_habiles/dias_habiles_entre/notificacion_surtida_el/vencimiento_calendario`
usando la librería `holidays` (festivos colombianos con Ley Emiliani ya aplicada por la librería, sin
mantener tabla propia). El modelador de términos (`EstadoTermino` + `iniciar_termino/dias_restantes/
esta_vencido/interrumpir/suspender/reanudar`) vive en `app/engine/temporal/terminos.py`, nuevo. 30 tests
nuevos (`tests/temporal/test_calendar.py`, `tests/temporal/test_terminos.py`), suite completa en 226
verde. Code review encontró y se corrigió en el mismo sprint: `interrumpir`/`reanudar` no validaban que
`fecha` fuera posterior al `checkpoint` vigente (permitía retroceder el reloj procesal silenciosamente) —
ahora las cuatro funciones (`dias_restantes`/`interrumpir`/`suspender`/`reanudar`) comparten un guard
único que rechaza fechas anteriores al checkpoint.

Dos limitaciones conocidas quedan documentadas (no corregidas en este sprint, por ser fuera de alcance
de lo que Sprint 6 pedía, pero relevantes para quien tome el Sprint 7):
- `dias_restantes`/`suspender` tienen `CalendarUtils.dias_habiles_entre` (conteo en días hábiles)
  cableado directamente como unidad de tiempo consumido. El Sprint 7 (prescripción/caducidad) son
  términos de años calendario (5/10/3/1 años), no de días hábiles judiciales — reusar `EstadoTermino`
  verbatim como sugiere la nota de este plan subestimaría el tiempo transcurrido (día hábil ≈ 250/año vs.
  día calendario ≈ 365/año). Antes de que Sprint 7 importe esta máquina de estados, evaluar hacer el
  contador de días un parámetro inyectable en vez de una llamada fija a `dias_habiles_entre`.
- `notificacion_surtida_el` (regla nombrada y citada del PDF) quedó como método de la clase genérica
  `CalendarUtils`, en vez de seguir el patrón ya establecido en `app/engine/interest/` de separar
  matemática genérica (`rate_conversion.py`) de reglas nombradas con cita legal propia
  (`usury_validator.py`, `legal_rates.py`). Si Sprint 7 agrega más reglas nombradas de este tipo, vale la
  pena extraerlas a un módulo propio en vez de seguir creciendo `CalendarUtils`.

---

## Sprint 7 — Motor de prescripción y caducidad ✅ Completado

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

**Estado:** Implementado (2026-07-19) — ver
`docs/superpowers/plans/2026-07-19-sprint7-prescripcion-caducidad.md` y
`docs/superpowers/specs/2026-07-19-sprint7-prescripcion-caducidad-design.md`. El motor vive en
`app/engine/temporal/prescripcion.py`, independiente de `EstadoTermino` (Sprint 6) por decisión tomada
con el usuario: prescripción/caducidad son plazos calendario (años/meses), no de días hábiles, y no
necesitan pausar/reanudar un reloj — solo una fecha límite calculada desde
`CalendarUtils.vencimiento_calendario`. Decisiones tomadas con el usuario durante el brainstorming
previo (no asumidas unilateralmente):
- Los tres subtipos de prescripción cambiaria del PDF (pág. 32 y pág. 45) se modelan como tres valores
  distintos de `TipoAccion` (directa 3 años, de regreso del tenedor 1 año, entre obligados de regreso 6
  meses), reconciliando la mención de "6 meses" de la pág. 32 como el tercer supuesto real del C.Co.
  (art. 791) en vez de tratarla como un error aislado del documento.
- `calcular_caducidad` solo trae hardcodeado el único caso con plazo confirmado en el PDF (impugnación
  de ineficacia societaria, 5 años); cualquier otro `tipo_proceso` exige un `plazo_meses_manual`
  explícito o lanza `ValueError` — mismo patrón que `costas_pct_manual` del Sprint 4, para no inventar
  plazos sin fuente documental.
- No se agregaron excepciones de dominio (`ObligacionPrescritaError`/`DemandaCaducadaError`): el motor
  es cálculo puro, ya que este sprint excluye explícitamente la integración con la GUI y con
  `area_strategy.py`.

Pendiente explícito que quedó fuera de este sprint (documentado, no un olvido): la suspensión de
caducidad por conciliación extrajudicial (máximo 3 meses, PDF pág. 25) no se modela — no hay ningún caso
de uso en el sprint que la requiera todavía.

**Definición de Hecho:**
- Tests con los plazos de cada tipo de acción mencionados en el PDF.
- Test específico de prescripción parcial en una obligación recurrente tipo `CHILD_SUPPORT` con cuotas de
  hace más de 5 años mezcladas con cuotas recientes.
- Suite completa en verde.

---

## Sprint 8 — Conectar indexación IPC al área Civil/Familia ✅ Completado

**Prioridad sugerida:** Media.
**Depende de:** Sprint 5 (sin datos históricos de IPC, no hay forma de resolver `IPC_inicial`/`IPC_final`
automáticamente a partir de una fecha).

**Documentos a consultar:**
- `docs/specifications/03_motor_indexacion.md` (ya documenta el estado actual: implementado y probado, pero
  no conectado).
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

**Estado:** Implementado (2026-07-19) — ver
`docs/superpowers/plans/2026-07-19-sprint8-indexacion-ipc-civil-familia.md` y
`docs/superpowers/specs/2026-07-19-sprint8-indexacion-ipc-civil-familia-design.md`. Decisiones tomadas
con el usuario durante el brainstorming previo: (a) la activación es **opt-in por obligación**
(`aplica_indexacion_ipc`), no automática por área — es un juicio legal del abogado; (b) la interpolación
del PDF (entre meses certificados) se aproxima con interpolación entre **índices de cierre de año**,
porque la fuente transcrita en el Sprint 5 nunca tuvo granularidad mensual; (c) fechas de 2026 en
adelante usan el índice de 2025 como aproximación, para no bloquear liquidaciones con la fecha actual del
sistema; (d) la regla "no doble indexación" del PDF se documentó en vez de codificarse como guard, porque
ningún campo de `Obligacion` usado por Civil/Familia puede representar la combinación que esa regla
prohíbe. Queda documentado como limitación conocida (no corregida en este sprint): el interés sigue
calculándose solo sobre el capital, no sobre el capital ya indexado, a diferencia del algoritmo de "Suma
Única" del PDF (pág. 22) — cambiar eso afecta el motor core para las 5 áreas.

Dos hallazgos de la revisión final de rama, resueltos o documentados antes de cerrar el sprint:
- **Migración de esquema**: `init_db()` (`database/database.py`) solo crea tablas nuevas, no altera las
  existentes — sin correr `scripts/migrate_aplica_indexacion_ipc.py` sobre un `bastium.db` preexistente,
  la app falla al leer o guardar cualquier obligación (`no such column: aplica_indexacion_ipc`). Ya se
  corrió el script sobre el `bastium.db` real de este equipo (2026-07-20); queda documentado en
  `README.md` (sección "Instalación rápida") para quien clone el repo con un `bastium.db` de antes de
  este sprint.
- **Pendiente explícito, no bloqueante**: `ResultadoLiquidacionView` (`app/views/liquidaciones.py`, no
  tocada en este sprint) no tiene columna "Indexación" en la tabla en pantalla — el monto indexado sí
  queda en `LiquidationItem.indexation_amount` y sí aparece en las exportaciones a PDF/Word
  (`app/engine/reports/table_builder.py`), pero en pantalla solo se ve reflejado en el Saldo acumulado,
  no como cifra propia. Agregar esa columna es trabajo de un sprint/tarea aparte sobre la vista de
  resultados, no de este sprint de conexión del motor.

**Definición de Hecho:**
- Los tests de `CivilFamiliaStrategy` (Task 6 del plan MVP) siguen pasando y se agregan casos nuevos con
  indexación activada, verificando el resultado numérico contra un cálculo manual con la fórmula del PDF.
- Suite completa en verde.

---

## Sprint 9 — Motor de auditoría / bitácora ✅ Completado

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
- `docs/specifications/05_motor_auditoria.md` (documenta el motor completo, actualizado en el Sprint 9).

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

**Estado:** Implementado (2026-07-19). La infraestructura base (rate_source
por tramo, modelo `AuditLog`, serialización JSON exacta) se había construido
en sesiones previas; la última pieza del motor
(`registrar_liquidacion`/`reconstruir_liquidacion`/`historial_de_expediente`
en `app/engine/audit/service.py`) quedó completa y probada en una rama
huérfana (`sprint9-task8-audit-service`) que nunca se fusionó — se recuperó
por cherry-pick al inicio de esta sesión. Lo que faltaba y se agregó ahora es
el wiring a la GUI:
`ExpedienteDetallePage` registra cada liquidación ejecutada y muestra un
historial de auditoría con reconstrucción de una liquidación pasada al
hacer doble clic (ver
`docs/superpowers/plans/2026-07-19-motor-auditoria-gui-wiring.md` y
`docs/superpowers/specs/2026-07-19-motor-auditoria-gui-design.md`).

---

## Sprint 10 — Exportación de liquidación a PDF/Word ✅ Completado

**Prioridad sugerida:** Media (valor visible para el usuario final, útil para presentar en juzgado).

**Depende de:** Nada (usa el `LiquidationResult` que ya existe).

**Documentos a consultar:**
- `docs/specifications/06_motor_reportes.md`.
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

## Sprint 11 — Derecho Tributario (DIAN) ✅ Completado (11a)

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

**Estado:** Sprint 11a implementado (2026-07-20) — ver
`docs/superpowers/plans/2026-07-20-sprint11a-tributario-interes-renta-liquida.md` y
`docs/superpowers/specs/2026-07-20-sprint11a-tributario-interes-renta-liquida-design.md`. Decisión tomada
con el usuario durante el brainstorming previo: de las 5 piezas sugeridas arriba, este sprint construyó
únicamente las dos sin bloqueo de datos — `app/engine/tax/moratory_interest.py` (interés moratorio
tributario, E.T. art. 635, resuelto automáticamente por tramos históricos de usura vía
`historical_index.get_tramos_ibc_usura_between`) y `app/engine/tax/renta_liquida.py` (depuración de Renta
Líquida Gravable, pipeline de 8 pasos). Son motores de cálculo puros — sin `TributarioStrategy`, sin
registrar el área en `AREAS_DERECHO`, sin wiring de GUI — mismo patrón que `IPCIndexation` quedó
standalone hasta que el Sprint 8 lo conectó. **Sprint 11b** (motor de sanciones, imputación tributaria de
pagos, modelo de "Obligación Tributaria") sigue pendiente, bloqueado por la misma tabla histórica de UVT
que el Sprint 5 dejó sin conseguir.

---

## Sprint 12 — TRM y obligaciones en moneda extranjera ✅ Completado

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

**Estado:** Implementado (2026-07-20) — ver
`docs/superpowers/plans/2026-07-20-sprint12-trm-moneda-extranjera.md` y
`docs/superpowers/specs/2026-07-20-sprint12-trm-moneda-extranjera-design.md`. Decisiones tomadas con el
usuario durante el brainstorming previo: (a) alcance limitado a **solo el área Comercial y solo USD** —
el PDF ata la TRM a títulos valores comerciales (Art. 874 C.Co.), y USD cubre los casos reales
confirmados con el usuario; (b) el PDF **no trae una serie histórica de TRM diaria** (a diferencia de
SMLMV/IPC/IBC del Sprint 5) — verificado extrayendo el texto completo de las páginas 8 y 21 del PDF —, así
que la TRM se ingresa manualmente por obligación (`trm_aplicable`, `trm_fecha_referencia`) detrás de una
interfaz `TRMProvider` reemplazable por una fuente histórica real más adelante, sin tocar
`ComercialStrategy`; (c) la conversión del capital a pesos es **única, al inicio de la liquidación** (antes
de construir los eventos de causación), no una reconversión continua por cada abono — el resto del motor
de interés/mora/usura sigue operando 100% en pesos sin ningún cambio.

Hallazgo técnico importante detectado durante la planificación (documentado al inicio del plan): los
objetos `Obligacion` construidos directamente en tests (sin sesión de base de datos, patrón usado en todos
los fixtures de `tests/services/test_area_strategy.py`) no reciben el default `"COP"` de SQLAlchemy —
`mapped_column(default=...)` solo se aplica al hacer `session.commit()`. Por eso todo el código de este
sprint trata `moneda in (None, "COP")` como "sin conversión", nunca una comparación `== "COP"` sola, para
no romper ninguna obligación Comercial existente en la suite de pruebas.

**Definición de Hecho:**
- `ComercialStrategy` liquida obligaciones en USD convirtiendo el capital a pesos con la TRM ingresada por
  el abogado, antes de aplicar interés/mora/usura — verificado con tests que comparan el resultado contra
  el mismo caso armado manualmente en pesos (mismo interés, mismo capital convertido).
- Formulario de obligación (`ObligacionFormDialog`) operable end-to-end para el flujo Comercial + USD:
  smoke test end-to-end scriptado (diálogo real de PySide6 con widgets/señales reales, guardado real en
  base de datos, liquidación vía el mismo `AreaRegistry.get_strategy()` que usa el botón "Liquidar" real de
  la app) confirmó que una obligación de USD 10.000 con TRM 4.150,25 liquida con un capital de
  $41.502.500,00 pesos, sin errores.
- `README.md` y `docs/GUIA_USUARIO.md` actualizados (sección 5.7 ampliada, nueva sección 7.8, sección 8
  corregida).
- Suite completa en verde (314 passed, 1 skipped — el mismo skip preexistente de antes del sprint).
- Migración de esquema (`scripts/migrate_moneda_trm.py`, mismo patrón idempotente que
  `migrate_aplica_indexacion_ipc.py` del Sprint 8) — pendiente de correr contra el `bastium.db` real del
  equipo, ya que ese archivo no está versionado y no existe dentro del worktree de este sprint; queda como
  el último paso al fusionar esta rama a `main` (documentado en `README.md`, "Instalación rápida").

---

## Sprint 13 — Arquitectura de motor de reglas versionado (EFDJ) ✅ Completado

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

**Estado:** Evaluado y cerrado sin construir nada (2026-07-20), tras la conversación de brainstorming que
este mismo sprint pedía tener antes de planificar tareas técnicas. Motivación real detrás de la pregunta:
que alguien sin conocimientos de Python pueda editar reglas — pero (a) esa persona no existe todavía, es
una capacidad a futuro sin fecha ni usuario concreto asignado, y (b) lo que necesitaría editar son
**valores/parámetros** (tasas, topes, plazos, tarifas), no condiciones ni fórmulas completas. El catálogo
EFDJ del PDF (24 campos por regla, reglas-como-datos con fórmula y compatibilidades incluidas) está
diseñado para un escenario mucho más exigente que este. Con esa combinación (sin urgencia + alcance
reducido a solo parámetros) no se justifica el costo de migrar; se decidió con el usuario no construir
nada ahora en vez de sobre-construir una capacidad sin caso de uso real.

Si en el futuro aparece una necesidad concreta, la puerta de entrada recomendada **no es** el catálogo
EFDJ completo, sino un paso intermedio mucho más barato: extraer los valores hoy hardcodeados dentro de
`area_strategy.py` y los motores (`usury_validator.py`, topes de cuota litis, plazos de
`prescripcion.py`, etc.) a una capa de datos versionada (YAML/JSON o tabla simple) con una función de
consulta por nombre + fecha de vigencia, dejando la lógica/condiciones en Python. Eso resuelve "editar un
número sin redeploy" sin construir un motor de reglas-como-datos completo.

**Actualización (2026-07-20, misma sesión):** esa necesidad concreta apareció en la misma conversación —
el usuario aclaró que sí quiere que un abogado (sin fecha ni identidad fija todavía, capacidad a futuro)
pueda editar tasas/topes/porcentajes desde la GUI, porque esos datos sí cambian. Es exactamente el paso
intermedio descrito arriba (parámetros como datos versionados, no reglas completas como datos), así que
se retomó como un sprint nuevo, más chico y concreto que el EFDJ original: **"Parámetros legales
versionados"**, diseño completo en
`docs/superpowers/specs/2026-07-20-parametros-legales-versionados-design.md`. Cubre tanto los topes
legales sueltos (usura, cuota litis, prescripción/caducidad, E.T. 635, tasa civil legal) como las 3 series
que ya vivían versionadas en `historical_index.py` (SMLMV, IPC, IBC/usura) pero solo editables por
Python — todo en una tabla `parametros_legales` append-only con pantalla nueva en
`app/views/configuracion.py` (hoy vacío). El motor EFDJ completo (reglas con fórmulas/condiciones como
datos) sigue cerrado sin construir, sin cambios sobre esa parte de la decisión.

**Cierre de implementación (2026-07-20):** Completado — ver
`docs/superpowers/plans/2026-07-20-parametros-legales-versionados.md`. Tabla `parametros_legales`
(append-only) con tres modos de resolución: `ABIERTO` (topes y plazos legales, aplican desde su fecha de
vigencia sin fecha de corte), `ANUAL_EXACTO` (SMLMV e IPC, exige que la fecha de vigencia sea exactamente
el 1 de enero del año — sin coincidencia exacta, no hay error, el valor simplemente no queda disponible
para ese año) y `TRAMO_CERRADO` (IBC/usura, exige un rango de fechas cerrado). Servicio
`app/services/parametro_service.py`, script de siembra `scripts/migrate_parametros_legales.py`, seis
motores re-cableados (`usury_validator`, `HonorariosStrategy`, `prescripcion`, `moratory_interest`,
`legal_rates`, `historical_index`) sin cambiar ningún resultado de cálculo existente, y pantalla nueva
"⚙ Parámetros" en la GUI. Las constantes Python originales se conservan deliberadamente (no se borraron)
como transcripción congelada y fuente del script de siembra — ver la spec, sección "Motores a re-cablear".

**Nota importante para quien extienda el catálogo:** en modo `ANUAL_EXACTO`, cargar un valor con una
fecha que no sea el 1 de enero exacto no produce ningún error — el valor se guarda pero nunca queda
"vigente" para ningún cálculo; esto motivó una advertencia dedicada en `docs/GUIA_USUARIO.md` (sección
5.13) y una entrada de FAQ (sección 9).

De paso, se encontró y corrigió un bug de esquema preexistente no relacionado con el catálogo de reglas:
SQLite truncaba silenciosamente valores `Decimal` de alta precisión al guardarlos como `float64`; se
corrigió con un `TypeDecorator` `DecimalExacto` a nivel de columna (usado en `parametros_legales.valor`).

`README.md` y `docs/GUIA_USUARIO.md` actualizados. Suite completa en verde (367 passed, 1 skipped).

---

## Sprint 14 — Tabla histórica de UVT (DIAN) ✅ Completado

**Prioridad sugerida:** Alta — es el desbloqueador común de dos piezas ya pendientes: la conversión
SMLMV→UVT del Sprint 4 (hoy lanza `UVTNoDisponibleError` para hechos posteriores a 2020-01-01) y el
Sprint 15 (Tributario 11b), que necesita UVT para la sanción mínima (10 UVT) y para expresar cuantías.

**Depende de:** Nada técnicamente. El bloqueador real es conseguir la fuente: el PDF (páginas 8, 21, 38,
53, 69) describe el mecanismo (la UVT se fija anualmente por resolución DIAN en noviembre/diciembre, rige
desde el 1 de enero, se ajusta según variación IPC oct-oct) pero nunca trae una tabla año por año
completa — solo un ejemplo aislado en la página 69 ("UVT 2023 ≈ $38.004"), insuficiente para una serie
histórica real.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`: pág. 8 (ficha del indicador UVT,
  periodicidad anual nov/dic), pág. 21 ("D. UVT... se incrementa según la cifra del DANE por ingresos
  medios de año a año"), pág. 38 ("se reajusta anualmente cada 1 de enero según la variación del IPC
  oct-oct"), pág. 53 (repite la ficha), pág. 69 (único valor numérico citado, solo ejemplo ilustrativo, no
  tabla).
- Sprint 5 y Sprint 4 de este mismo archivo (ambos dejaron la UVT como pendiente explícito por falta de
  fuente completa).

**Código existente a reutilizar:**
- `app/engine/indexation/historical_index.py` → mismo patrón que `get_smlmv_for_year(anio)` (línea 79)
  para el nuevo `get_uvt_for_year(anio)`; la UVT es anual como el SMLMV, no por tramos como IBC/usura.
- `app/services/parametro_service.py` → `CATALOGO_PARAMETROS` (línea 43) ya tiene el modo `ANUAL_EXACTO`
  diseñado exactamente para series "un valor por 1 de enero" (usado hoy por `SMLMV` e
  `IPC_INDICE_ACUMULADO`, líneas 92-99) — la UVT es del mismo tipo, se agrega una entrada más al catálogo,
  no un modo nuevo.
- `scripts/migrate_parametros_legales.py` → script de siembra ya existente, mismo patrón para poblar la
  serie UVT una vez transcrita.
- `app/engine/indexation/smlmv_to_uvt.py` → `resolver_base_sancion()` (línea 11) es quien debe dejar de
  lanzar `UVTNoDisponibleError` una vez este sprint exista.

**Decisión de diseño a tomar antes de codificar:**
- La fuente real debe venir de las resoluciones DIAN publicadas (ej. resolución de fijación de UVT de cada
  año) o pedirse directamente al usuario si tiene una tabla de referencia — **no inventar valores**. Si no
  se consigue la serie completa desde el año de creación de la UVT (2006, Ley 1111 de 2006) hasta 2026,
  decidir con el usuario desde qué año arrancar (ej. solo desde 2020, que es cuando el PDF explícitamente
  empieza a exigir la conversión SMLMV→UVT).

**Código nuevo a crear:**
- Serie UVT anual en `historical_index.py`, transcrita de la fuente confirmada (no del ejemplo aislado de
  la pág. 69).
- `get_uvt_for_year(anio: int) -> Decimal`, mismo contrato que `get_smlmv_for_year`.
- Entrada `"UVT"` en `CATALOGO_PARAMETROS` (`parametro_service.py`), modo `ANUAL_EXACTO`, fuente legal
  "DIAN, resolución anual (Ley 1111 de 2006)".
- Actualizar `scripts/migrate_parametros_legales.py` para sembrar la serie UVT igual que SMLMV/IPC.
- Actualizar `resolver_base_sancion()` (`smlmv_to_uvt.py`) para consultar `get_uvt_for_year`/
  `parametro_service.get_parametro("UVT", fecha)` en vez de lanzar `UVTNoDisponibleError` para fechas
  posteriores a 2020-01-01.

**Alcance incluido:**
- Transcripción de la serie UVT (desde el año que se confirme con el usuario) hasta 2026.
- Función de consulta + entrada en el catálogo de parámetros versionados.
- Desbloqueo real de `resolver_base_sancion()` para fechas posteriores a 2020.

**Alcance explícitamente excluido:**
- Automatización de actualización anual vía scraping DIAN (fuera de alcance, igual que el resto de series
  del Sprint 5).
- El Sprint 15 en sí — este sprint solo entrega el dato, no el motor de sanciones que lo consume.

**Riesgos / notas técnicas conocidas:**
- Si no se consigue una fuente confiable y completa, no inventar valores por interpolación o estimación —
  documentar el hueco explícito por año, mismo criterio que ya se usó en Sprint 4/7 con
  `plazo_meses_manual`/`costas_pct_manual` (exigir un valor manual en vez de adivinar).

**Definición de Hecho:**
- `get_uvt_for_year` retorna valores verificables contra la fuente citada para al menos 2020-2026.
- `resolver_base_sancion` liquida correctamente un caso con fecha posterior a 2020-01-01 sin lanzar
  `UVTNoDisponibleError`.
- Suite completa en verde.

**Cierre de implementación (2026-07-21):** Completado — ver
`docs/superpowers/specs/2026-07-21-tabla-historica-uvt-design.md` y
`docs/superpowers/plans/2026-07-21-sprint14-tabla-historica-uvt.md`. Se agregó la serie UVT 2006-2026 a
`historical_index.py` (`get_uvt_for_year`), una entrada nueva `"UVT"` en el catálogo de
`parametro_service.py` (modo `ANUAL_EXACTO`, mismo patrón que SMLMV/IPC), siembra en
`scripts/migrate_parametros_legales.py`, y `resolver_base_sancion` (`smlmv_to_uvt.py`) ahora convierte vía
UVT para hechos con fecha posterior o igual a 2020-01-01 en vez de lanzar `UVTNoDisponibleError` sin
condición.

Como el PDF de requisitos no trae una tabla UVT completa (solo un valor aislado de ejemplo, página 69), la
serie se obtuvo de fuente externa y se verificó cruzando 3 fuentes independientes antes de transcribirla —
ver la spec para el detalle de fuentes y la tabla verificada.

`UVTNoDisponibleError` sigue existiendo y sigue lanzándose, pero ahora solo para años fuera del rango
cargado 2006-2026 (p. ej. un año futuro que la DIAN aún no ha publicado), no de forma incondicional para
cualquier fecha posterior a 2020 como antes.

`README.md` y `docs/GUIA_USUARIO.md` actualizados. Suite completa en verde (373 passed, 1 skipped).

---

## Sprint 15 — Tributario completo: sanciones, imputación y modelo de Obligación Tributaria (cierre del Sprint 11b) ✅ Completado

**Prioridad sugerida:** Media — es la continuación directa y ya presupuestada del Sprint 11 (11a se
completó el 2026-07-20; esta es la segunda mitad, aplazada a propósito para trabajarla con calma en su
propio sprint).

**Depende de:** Sprint 14 (tabla UVT) — la sanción mínima (10 UVT) y la conversión de cuantías
tributarias a UVT no se pueden probar con casos reales sin esa serie.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, "OBLIGACIONES EN DERECHO TRIBUTARIO..."
  completa (págs. 38-40): elementos del hecho gravable (sujeto activo, sujeto pasivo, hecho gravado, base
  gravable, tarifa — pág. 38), sanciones (pág. 39: extemporaneidad 5% mensual tope 100%, inexactitud
  160%/200%, error aritmético 30%, sanción mínima 10 UVT), imputación tributaria de pagos (pág. 40:
  sanciones → intereses → impuestos/anticipos/retenciones, distinta del orden civil que es intereses →
  capital).
- Pág. 70-71 (catálogo EFDJ): confirma "Tributaria y sancionatoria" como tipología propia del motor, con
  "impuesto, sanción, extemporaneidad, inexactitud, error aritmético, UVT, mora fiscal, cobro coactivo,
  multas públicas".
- Pág. 74, sección "10) Reglas tributarias y sancionatorias": exige explícitamente "motores específicos
  para sanciones por extemporaneidad, inexactitud, error aritmético y sanción mínima" y que "la
  imputación tributaria debe ser independiente del régimen civil".
- `docs/superpowers/plans/2026-07-20-sprint11a-tributario-interes-renta-liquida.md` y su spec — documentan
  lo ya construido (11a) y explícitamente dejan 11b como pendiente.

**Código existente a reutilizar:**
- `app/engine/tax/moratory_interest.py` y `app/engine/tax/renta_liquida.py` (Sprint 11a) — motores puros
  ya implementados y probados; este sprint los complementa, no los reemplaza.
- `app/services/area_strategy.py` — seguir el mismo patrón de las 5 estrategias existentes
  (`CivilFamiliaStrategy` línea 36, `ComercialStrategy` línea 152, `LaboralStrategy` línea 312,
  `SancionatorioStrategy` línea 412, `HonorariosStrategy` línea 481) para la nueva `TributarioStrategy`.
- `database/models.py` → `AreaDerecho` (línea 47) y `app/core/constants.py` → `AREAS_DERECHO` (línea 48) —
  agregar `"TRIBUTARIO"` a ambos, mismo patrón usado por las 5 áreas actuales (todas ya están en `True`,
  este sprint agrega la sexta).
- `app/engine/liquidation/allocation.py` — el motor de imputación civil (`LiquidationCore`) usa un orden
  fijo (intereses → capital); la imputación tributaria necesita su propio orden y probablemente su propia
  función, no reutilizar la civil directamente.
- `app/services/parametro_service.py` → agregar entradas nuevas al catálogo para los porcentajes de
  sanción, siguiendo el mismo patrón de `USURA_MULTIPLICADOR`/`ET635_PUNTOS_DESCUENTO` (modo `ABIERTO`,
  porque son topes legales fijos que solo cambian por reforma tributaria, no por vigencia mensual/anual).

**Decisión de diseño a tomar antes de codificar:**
- Modelo de "Obligación Tributaria": ¿extender la tabla `Obligacion` existente con campos nuevos
  (sujeto_activo, hecho_gravado, base_gravable, tarifa) o crear un modelo separado? El PDF (pág. 70) la
  describe como una entidad con parámetros propios distintos de una obligación civil/comercial — evaluar
  con el usuario antes de elegir, ya que afecta migración de esquema (mismo patrón de
  `scripts/migrate_*.py` ya usado en Sprints 8/12).
- Confirmar con el usuario si `TributarioStrategy` se habilita en la GUI de una vez (área operable
  end-to-end) o si, como 11a, se deja como motor standalone por ahora.

**Código nuevo a crear:**
- `app/engine/tax/sanciones.py` (sugerido): cuatro funciones/clases, una por sanción — extemporaneidad
  (5% del impuesto a cargo por cada mes o fracción de mes de retraso, tope 100%), inexactitud (160% de la
  diferencia entre saldo a pagar determinado y declarado; 200% si hay omisión de activos o inclusión de
  pasivos inexistentes), error aritmético (30% de la diferencia generada por el error), sanción mínima
  (ninguna sanción puede ser inferior a 10 UVT, usa `get_uvt_for_year`/`parametro_service` del Sprint 14).
- `app/engine/tax/imputacion.py` (sugerido): jerarquía de imputación tributaria (sanciones → intereses →
  impuestos/anticipos/retenciones), como función pura independiente de
  `app/engine/liquidation/allocation.py`.
- Modelo de "Obligación Tributaria" (según la decisión de diseño de arriba).
- `TributarioStrategy.liquidar()` en `area_strategy.py`, cableando `moratory_interest.py` +
  `renta_liquida.py` (ya existentes) + los dos motores nuevos de este sprint.
- Registro de `"TRIBUTARIO"` en `AreaDerecho` y `AREAS_DERECHO`, con migración de esquema si aplica.
- Entradas nuevas en `CATALOGO_PARAMETROS`: `EXTEMPORANEIDAD_PCT_MENSUAL`, `INEXACTITUD_PCT`,
  `INEXACTITUD_AGRAVADA_PCT`, `ERROR_ARITMETICO_PCT` (todas modo `ABIERTO`, fuente Estatuto Tributario).

**Alcance incluido:**
- Los componentes que 11a no cubrió: modelo de Obligación Tributaria, motor de sanciones completo,
  imputación tributaria propia.
- `TributarioStrategy` real, cableada al registry, con el área habilitada si así se decide con el usuario.

**Alcance explícitamente excluido:**
- Integración en vivo con la DIAN (radicación, formularios oficiales) — fuera de alcance de un motor de
  liquidación de litigio.
- Cobro coactivo administrativo como proceso propio — el PDF lo menciona (pág. 71) pero es un
  procedimiento, no una fórmula de cálculo.

**Riesgos / notas técnicas conocidas:**
- La sanción mínima (10 UVT) depende 100% de que el Sprint 14 ya esté cerrado — no empezar este sprint sin
  esa dependencia resuelta.
- El PDF (pág. 40) advierte: "no se pueden cobrar simultáneamente intereses moratorios y actualización
  monetaria si esto conduce a una tasa usuraria o doble pago por el mismo concepto" — documentar esta
  validación explícitamente en `TributarioStrategy`, no solo como comentario (mismo criterio ya exigido en
  Sprint 2 para la incompatibilidad interés-comercial + IPC).

**Definición de Hecho:**
- Tests de cada uno de los 4 tipos de sanción con casos conocidos del PDF (pág. 39).
- Test de imputación tributaria verificando el orden sanciones → intereses → impuesto, distinto del test
  equivalente civil.
- `TributarioStrategy` liquida con TDD siguiendo el mismo patrón que `tests/services/test_area_strategy.py`.
- Suite completa en verde.

**Cierre de implementación (2026-07-25):** Completado — ver
`docs/superpowers/specs/2026-07-24-sprint15-tributario-11b-design.md` y
`docs/superpowers/plans/2026-07-24-sprint15-tributario-11b.md`. Se agregó el motor de sanciones
(`app/engine/tax/sanciones.py`) con las tres funciones puras del PDF —
`calcular_sancion_extemporaneidad` (5% mensual del impuesto a cargo, tope 100%),
`calcular_sancion_inexactitud` (160%, o 200% si es agravada, de la diferencia determinada) y
`calcular_sancion_error_aritmetico` (30% de la diferencia) — más `aplicar_piso_sancion_minima`, que
centraliza el piso legal de 10 UVT en un solo lugar en vez de repetirlo en cada función.

El modelo de "Obligación Tributaria" no se separó en una tabla nueva: se extendió la tabla `Obligacion`
existente con 8 columnas (`base_sancion_tributaria`, `meses_extemporaneidad`, `sancion_agravada`,
`ingresos_brutos`, `devoluciones_rebajas_descuentos`, `costos`, `deducciones`, `rentas_exentas`), migradas
vía `scripts/migrate_tributario.py`, y se registró `AreaDerecho.TRIBUTARIO` junto con `"TRIBUTARIO"` en
`AREAS_DERECHO`. `TributarioStrategy` queda operable en la GUI como sexta área del sistema, con 5
categorías de obligación: `IMPUESTO_A_CARGO`, las 3 sanciones (`SANCION_EXTEMPORANEIDAD`,
`SANCION_INEXACTITUD`, `SANCION_ERROR_ARITMETICO`) y `RENTA_LIQUIDA`.

Contra lo previsto en el plan original de este sprint, no se construyó un motor de imputación tributaria
dedicado (`app/engine/tax/imputacion.py`): se reutiliza el motor genérico de liquidación
(`UniversalLiquidationService`/`LiquidationCore`) sin modificarlo. El impuesto a cargo se agrega a
`_capital_concepts` y cae en el bucket `principal`; las 3 sanciones se normalizan a un único
`event_type` `"SANCION_TRIBUTARIA"` que cae en el bucket `indexation`. El orden de pago que ya aplica
`AllocationEngine` (indexación → interés → capital) coincide exactamente con el orden exigido por el PDF
para tributario (sanciones → intereses → impuesto), así que no hacía falta un motor de imputación aparte
— ver la spec, sección "Arquitectura", para el detalle de esa decisión. La Renta Líquida Gravable
(`depurar_renta_liquida_gravable`, ya existente desde el Sprint 11a) es puramente informativa: no genera
evento de causación, se adjunta aparte en `LiquidationResult.renta_liquida` y un expediente admite como
máximo una obligación `RENTA_LIQUIDA` por liquidación.

De paso se corrigió un defecto de reporting preexistente: el bucket de indexación (el mismo que usan las
sanciones tributarias) se calculaba desde Civil/Familia en `ReportTableBuilder`/`ReportSummaryBuilder`
pero nunca se mostraba en ningún canal. Tributario es la primera área donde ese bucket contiene montos
relevantes, así que se agregó la columna/fila faltante en los 3 canales: la tabla de la GUI
(`app/views/liquidaciones.py`), el PDF (`app/reports/pdf.py`) y el Word (`app/reports/word.py`).

`README.md` y `docs/GUIA_USUARIO.md` actualizados. Suite completa en verde (415 passed, 1 skipped tras la
revisión final de rama completa y sus correcciones: bloque de Renta Líquida Gravable visible en GUI/PDF/
Word, siembra de los 4 parámetros de sanciones y manejo amigable de `ParametroNoDisponibleError`, y dos
ajustes menores de documentación/pruebas).

---

## Sprint 16 — Seguridad social, incapacidades y suspensiones contractuales (Laboral) ✅ Completado

**Prioridad sugerida:** Media — el Sprint 3 (Laboral) dejó esto fuera a propósito, pendiente de decisión
de alcance con el usuario.

**Depende de:** Sprint 3 (Área Laboral, ya completo) — extiende `LaboralStrategy`, no la reemplaza.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, pág. 51-52 ("C. Derecho Laboral" + sección
  de Riesgos Laborales/ARL/Incapacidades): cotizaciones IBC, pensión 16%, salud 12.5%, ARL por nivel de
  riesgo (I: 0.522% a V: 6.960%), FSP si IBC ≥ 4 SMMLV.
- Pág. 52, "4. Manejo de Eventos y Estados: Suspensiones e Incapacidades" (texto exacto): suspensión
  (licencia no remunerada/huelga/disciplinaria) → el empleador NO cotiza ARL pero SÍ mantiene aportes a
  Salud y Pensión; incapacidad de origen común → días 1-2 el empleador paga 66.67%, días 3-90 la EPS paga
  66.67%, día 91-180 la EPS paga 50%; incapacidad de origen laboral → la ARL paga 100% del IBC desde el
  día 1.
- Pág. 74, "8) Reglas laborales": el catálogo EFDJ exige "Seguridad social: debe soportarse IBC, límites
  mínimos y máximos, distribución empleador/trabajador y aportes diferenciales como FSP y ARL" y "eventos
  de suspensión contractual, licencias no remuneradas e incapacidades comunes o laborales con sus
  pagadores y porcentajes" — es decir, el PDF sí ubica esto dentro del motor de cálculo, no como módulo de
  nómina aparte (matiz relevante para la decisión de alcance que el Sprint 3 dejó abierta).
- Pág. 71 (tipología EFDJ): "Laboral: salarios, prestaciones, cesantías, intereses a cesantías, prima,
  vacaciones, seguridad social, indemnización moratoria..." — lista "seguridad social" como parte
  constitutiva del área Laboral, no como feature opcional.

**Código existente a reutilizar:**
- `app/engine/temporal/schedulers/labor.py` → `LaborScheduler` ya genera los eventos de prestaciones; este
  sprint agrega eventos nuevos (cotizaciones, incapacidades, suspensiones) al mismo generador o a uno
  paralelo.
- `app/services/area_strategy.py` → `LaboralStrategy` (línea 312).
- `app/engine/indexation/smmlv.py` → `SMMLVCalculator` para topes de IBC expresados en SMMLV (1-25 SMMLV
  es el rango típico de IBC de seguridad social en Colombia).
- `app/services/parametro_service.py` → los porcentajes de cotización (pensión 16%, salud 12.5%, ARL por
  nivel I-V, FSP) son candidatos naturales al catálogo `CATALOGO_PARAMETROS`, modo `ABIERTO` (cambian por
  reforma, no por vigencia calendario).

**Decisión de diseño a tomar antes de codificar (con el usuario, no asumir):**
- Confirmar si esto entra en el alcance de BASTIUM como **liquidación de procesos judiciales** (ej. cuando
  un juez condena a pagar aportes no consignados, o para calcular cuánto se le debe a un trabajador
  incluyendo seguridad social dejada de pagar) o si es un módulo de **nómina corriente** fuera del
  producto. La nota del Sprint 3 dejó esto sin resolver — el matiz nuevo encontrado en este sprint (la
  pág. 74 del PDF sí lo incluye en el catálogo EFDJ del motor) es un argumento a favor de que sí es parte
  del motor de cálculo, pero la decisión de negocio sigue siendo del usuario. Recomendado: una
  conversación corta tipo `superpowers:brainstorming` antes de construir, igual que se hizo con el Sprint
  13 (EFDJ) antes de invertir tiempo de planificación fina.

**Código nuevo a crear (si se aprueba el alcance):**
- Función de cotizaciones de seguridad social: dado un IBC, retorna pensión (16%, típicamente 12%
  empleador + 4% trabajador), salud (12.5%, típicamente 8.5%/4%), ARL (según nivel de riesgo I-V) y FSP
  (si IBC ≥ 4 SMMLV).
- Eventos de estado de contrato: `SUSPENSION` (con motivo: huelga/licencia no remunerada/disciplinaria)
  que desactiva ARL pero mantiene Salud/Pensión; `INCAPACIDAD_COMUN` e `INCAPACIDAD_LABORAL` con los
  pagadores/porcentajes exactos de la pág. 52.
- Wiring en `LaboralStrategy.liquidar()` para que estos eventos afecten el resultado cuando la obligación
  los tenga registrados.

**Alcance incluido:**
- Cotizaciones de seguridad social (pensión, salud, ARL, FSP) como parte de una liquidación laboral
  judicial.
- Incapacidades (común y laboral) con sus pagadores y porcentajes exactos por rango de días.
- Suspensiones contractuales con su efecto diferencial sobre ARL vs. Salud/Pensión.

**Alcance explícitamente excluido:**
- Módulo de nómina corriente (generación periódica de planillas PILA, afiliaciones, etc.).
- Régimen pensional (IBL, densidad de semanas) — va en el Sprint 17.

**Riesgos / notas técnicas conocidas:**
- Mismo tipo de decisión previa que tuvo el Sprint 13 con el motor EFDJ completo: no construir sin
  confirmar antes que esto es parte del producto.

**Definición de Hecho:**
- Tests con los porcentajes exactos de cada escenario de incapacidad (días 1-2, 3-90, 91-180) y de
  suspensión (con/sin ARL).
- Suite completa en verde.

**Cierre de implementación (2026-07-25):** Completado — ver
`docs/superpowers/specs/2026-07-24-seguridad-social-laboral-design.md` y
`docs/superpowers/plans/2026-07-24-seguridad-social-laboral.md`. Se confirmó con el usuario que esto es
liquidación judicial de aportes/prestaciones dejados de pagar (no un módulo de nómina corriente),
cerrando la nota que el Sprint 3 había dejado abierta. Se agregó la tabla `eventos_laborales`
(polimórfica: suspensión/incapacidad común/incapacidad laboral), 2 columnas nuevas en `obligaciones`
(`incluir_seguridad_social`, `nivel_riesgo_arl`), los calculadores puros `SeguridadSocialCalculator` e
`IncapacidadCalculator` (`app/engine/labor/`), 13 parámetros nuevos en `CATALOGO_PARAMETROS` (pensión,
salud, ARL por nivel I-V, FSP por tramo de SMMLV), y el wiring correspondiente en
`LaboralStrategy.liquidar()`. Activación por checkbox opt-in: un expediente Laboral sin la casilla
marcada se liquida exactamente igual que antes del Sprint 16, sin regresión.

Incapacidades: el sistema muestra el desglose informativo completo de todos los pagadores (empleador,
EPS, ARL) pero solo la porción a cargo del empleador se suma a la deuda del expediente — reclamar lo que
le correspondía pagar a la EPS o a la ARL es un hecho distinto (ej. no afiliación), fuera de alcance.

Fuentes complementarias al PDF, ambas aprobadas explícitamente por el usuario antes de codificar: la
tabla completa de niveles de riesgo ARL II-IV (Decreto 1607/2002 — el PDF solo cita los extremos I y V) y
la escala progresiva completa del FSP por tramos de SMMLV (Ley 797/2003 art. 8 — el PDF solo describe
"desde 1% hasta 2%" sin tramos exactos).

`README.md` y `docs/GUIA_USUARIO.md` actualizados. Suite completa en verde.

---

## Sprint 17 — Módulo pensional (IBL, tasa de reemplazo, densidad de semanas) ✅ Completado

**Prioridad sugerida:** Baja — el propio Sprint 3 lo señaló como "un dominio aparte", y el PDF lo trata
como un régimen de liquidación mucho más largo (vida laboral completa) que el resto de obligaciones
puntuales que BASTIUM liquida hoy.

**Depende de:** Sprint 6 (calendario de días hábiles) — ya documenta la limitación conocida relevante:
`dias_habiles_entre` cuenta días hábiles (~250/año), pero el conteo de semanas de pensión que exige este
sprint es en días calendario (~365/año) desde la Sentencia SL138-2024; no reusar directamente esa función
sin adaptarla.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, pág. 52, "5. Liquidaciones Especiales: IBL y
  Pensiones": IBL (Ingreso Base de Liquidación) = promedio de los salarios sobre los cuales se cotizó en
  los últimos 10 años, actualizados anualmente con el IPC; Tasa de Reemplazo (Fórmula R) = `r = 65.5 −
  0.5·s`, donde `s` es el número de salarios mínimos contenidos en el IBL.
- Pág. 52, "7. Indicador Crítico de Tiempo: El Calendario": la Sentencia SL138-2024 de la Corte Suprema
  (Sala Laboral) cambió el conteo de semanas de pensión a días reales de calendario (365/366), no al año
  comercial de 360 usado antes.
- Pág. 74, "8) Reglas laborales": "El módulo pensional debe separar densidad temporal, IBL, actualización
  por IPC y reglas especiales de conteo real del calendario para semanas cuando proceda" — confirma que
  son 4 piezas separadas, no una sola fórmula.

**Código existente a reutilizar:**
- `app/engine/indexation/ipc.py` → `IPCIndexation.calculate()` para actualizar anualmente los salarios
  históricos que entran al promedio del IBL.
- `app/engine/indexation/historical_index.py` → `get_smlmv_for_year()` para expresar el IBL en salarios
  mínimos (variable `s` de la fórmula R).
- `app/engine/time/calendar.py` → como base de conteo de días calendario (no `dias_habiles_entre`, ver
  riesgo del Sprint 6 arriba).

**Código nuevo a crear:**
- `app/engine/labor/ibl.py` (sugerido): `calcular_ibl(historial_salarios_10_anios) -> Decimal`, aplicando
  indexación IPC año por año antes de promediar.
- `calcular_tasa_reemplazo(ibl: Decimal, smlmv_vigente: Decimal) -> Decimal`, fórmula `r = 65.5 − 0.5·s`.
- `calcular_densidad_semanas(periodos_cotizados: list[tuple[date, date]]) -> int`, contando días calendario
  reales (365/366) según SL138-2024, no días hábiles ni año comercial de 360.

**Alcance incluido:**
- Las 4 piezas que el PDF exige por separado: IBL, tasa de reemplazo, densidad de semanas (con el criterio
  post-SL138-2024), actualización IPC del historial salarial.

**Alcance explícitamente excluido:**
- Régimen de Ahorro Individual con Solidaridad (RAIS) — el PDF solo describe Prima Media.
- Integración con Colpensiones/AFP para traer el historial real de cotizaciones — el input es manual.

**Riesgos / notas técnicas conocidas:**
- Sprint de mayor incertidumbre de dominio de todo el backlog nuevo: el PDF da la fórmula pero no ejemplos
  numéricos completos para verificar contra un caso real — conviene pedir al usuario un caso pensional
  real (con IBL/semanas conocidos) para usar como test de referencia antes de dar el sprint por terminado.

**Definición de Hecho:**
- Tests de IBL con un historial salarial sintético de 10 años con IPC variable.
- Test de tasa de reemplazo con al menos 3 valores de `s` distintos.
- Test de densidad de semanas que compare explícitamente el resultado en días calendario vs. el año
  comercial de 360, documentando la diferencia.
- Suite completa en verde.

**Estado:** Implementado (2026-07-26) — ver
`docs/superpowers/plans/2026-07-26-sprint17-modulo-pensional.md` y
`docs/superpowers/specs/2026-07-26-sprint17-modulo-pensional-design.md`. Se agregaron las 3 funciones puras
en `app/engine/labor/ibl.py` (`calcular_ibl`, `calcular_tasa_reemplazo`, `calcular_densidad_semanas`), sin
`PensionalStrategy` ni wiring de GUI (mismo patrón standalone que `app/engine/tax/*` del Sprint 11a).
Decisiones tomadas con el usuario durante el brainstorming previo: (a) el IBL recibe historial mensual
(hasta 120 registros), no anual; (b) la densidad de semanas une periodos solapados antes de contar, para no
cotizar "doble" el mismo día; (c) la tasa de reemplazo implementa la fórmula completa real (Ley 100 art.
34: piso 65%, techo 80%, bono +1.5% por cada 50 semanas sobre 1.300), no solo la línea base que trae el PDF
de BASTIUM — el hueco entre ambas quedó documentado en `Preguntas-Para-Abogado.md` (sección Sprint 17) para
confirmación jurídica formal; (d) el caso de validación real usado en los tests es la Sentencia SL138-2024
(348 días calendario → 49,71 semanas → 50), en vez de un caso aportado directamente por el usuario. Se creó
además `Preguntas-Para-Abogado.md` (documento nuevo en la raíz del proyecto), que recoge esta brecha junto
con todas las decisiones/huecos legales sin confirmar de los Sprints 2-16, 18 y 30.

---

## Sprint 18 — Costas judiciales con tabla real de rangos (Acuerdo PCSJA20-11556)

**Prioridad sugerida:** Media — el Sprint 4 ya dejó `costas_pct_manual` como solución temporal por no
conseguir la fuente; este sprint es exclusivamente conseguir y estructurar esa fuente.

**Depende de:** Sprint 4 (Sancionatorio/Honorarios, ya completo) — reemplaza/complementa
`costas_pct_manual` sin quitarlo (mantenerlo como fallback cuando no haya tabla aplicable).

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, pág. 9-10 y pág. 55: "Costas Judiciales
  (Agencias en Derecho): las fija el juez mediante auto, basadas en los rangos del Consejo Superior de la
  Judicatura (ej. Acuerdo PCSJA20-11556), que establece porcentajes (ej. 3% al 7% de las pretensiones
  reconocidas)" — el PDF cita el acuerdo por nombre pero no transcribe la tabla completa de rangos.
- El acuerdo real (PCSJA20-11556 u otro vigente del Consejo Superior de la Judicatura) no viene en el PDF
  ni se consiguió durante el Sprint 4 — este sprint depende de conseguir esa fuente externa (pedir al
  usuario, o buscar el texto oficial del acuerdo).

**Código existente a reutilizar:**
- `database/models.py` → `Obligacion.costas_pct_manual` (línea 102) — campo ya existente, este sprint no
  lo reemplaza, lo complementa con una tabla automática cuando aplique.
- `app/services/parametro_service.py` → los 3 modos existentes (`ABIERTO`, `ANUAL_EXACTO`,
  `TRAMO_CERRADO`) no calzan bien con una tabla de rangos por **cuantía** (no por fecha) — este sprint
  probablemente necesita decidir si extiende el catálogo con un modo nuevo o si la tabla de rangos vive
  aparte, como estructura de datos simple (lista de tuplas rango_desde/rango_hasta/porcentaje) sin pasar
  por `parametros_legales`.
- `app/services/area_strategy.py` → `HonorariosStrategy` (línea 481) es quien hoy usa `costas_pct_manual`.

**Decisión de diseño a tomar antes de codificar:**
- Conseguir el texto real del Acuerdo PCSJA20-11556 (o el que esté vigente) — sin esta fuente, no se puede
  construir la tabla sin inventar porcentajes, mismo criterio de rigor ya aplicado en Sprint 4/5/7.
- Decidir si la tabla de rangos vive en `parametros_legales` (requeriría un modo de resolución nuevo, "por
  rango de cuantía" en vez de "por fecha") o en una estructura Python simple versionada como las de
  `historical_index.py`.

**Código nuevo a crear (una vez conseguida la fuente):**
- Tabla de rangos de costas por cuantía de las pretensiones reconocidas.
- Función `calcular_costas_por_rango(pretensiones_reconocidas: Decimal) -> Decimal`.
- Wiring en `HonorariosStrategy` para usar esta función cuando la obligación no tenga `costas_pct_manual`
  explícito, conservando el campo manual como override/fallback.

**Alcance incluido:**
- Tabla real de rangos del Consejo Superior de la Judicatura, una vez conseguida la fuente.
- Función de cálculo automático de costas por cuantía.

**Alcance explícitamente excluido:**
- Si no se consigue una fuente confiable, este sprint se cierra documentando el hueco (igual que el
  Sprint 5 con UVT) en vez de inventar porcentajes.

**Riesgos / notas técnicas conocidas:**
- Único sprint nuevo bloqueado por una fuente 100% externa que no es un dato público fácil de encontrar en
  una sola búsqueda — puede requerir que el usuario aporte el texto del acuerdo vigente directamente.

**Definición de Hecho:**
- Tests con al menos 2-3 rangos de cuantía reales contra el acuerdo confirmado.
- `HonorariosStrategy` sigue funcionando igual que antes cuando se usa `costas_pct_manual` (no debe romper
  el comportamiento del Sprint 4).
- Suite completa en verde.

---

## Sprint 19 — Anatocismo comercial condicionado (Art. 886 C.Co.) ✅ Completado

**Prioridad sugerida:** Media — pendiente explícito documentado desde el cierre del Sprint 2, con el
motor matemático (`CompoundInterest`) ya implementado y huérfano desde antes del MVP.

**Depende de:** Sprint 2 (Área Comercial, ya completo) — extiende `ComercialStrategy`, no la reemplaza.

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, pág. 45, "C. Anatocismo (Intereses sobre
  Intereses)": "Solo se permite cobrar intereses sobre intereses si: 1) Hay demanda judicial, o 2) Hay
  acuerdo posterior al vencimiento, siempre que se trate de intereses debidos con al menos un año de
  anterioridad."
- Pág. 10 y pág. 52-53 (repetición de la misma regla): "El algoritmo no debe aplicar interés compuesto por
  defecto en las liquidaciones judiciales" — el default siempre debe ser interés simple; el anatocismo es
  la excepción condicionada, nunca el comportamiento base.
- Pág. 70 (catálogo EFDJ): "Comercial y financiera: ... anatocismo condicionado" — confirmado como pieza
  propia de la tipología Comercial del motor.

**Código existente a reutilizar:**
- `app/engine/interest/compound_interest.py` → `CompoundInterest.calculate(capital, period_rate: Rate,
  periods: int)` — YA implementado y probado, huérfano desde antes del MVP; este sprint es 100% de
  wiring/condiciones, no de construir matemática nueva.
- `app/services/area_strategy.py` → `ComercialStrategy.liquidar()` (línea 170).
- `database/models.py` → `Obligacion` (línea 79) necesita campos nuevos para modelar las dos condiciones
  habilitantes (ver abajo).

**Decisión de diseño a tomar antes de codificar:**
- Qué campos nuevos agregar a `Obligacion` para representar "hay demanda judicial" y/o "hay acuerdo
  posterior de capitalización" — sugerido: `anatocismo_demanda_judicial: bool` y
  `anatocismo_fecha_acuerdo: date | None` (si hay acuerdo posterior, se necesita la fecha para validar que
  los intereses capitalizables ya llevan al menos un año). Requiere migración de esquema, mismo patrón que
  `scripts/migrate_aplica_indexacion_ipc.py` (Sprint 8) y `scripts/migrate_moneda_trm.py` (Sprint 12).

**Código nuevo a crear:**
- Migración de esquema para los campos nuevos de `Obligacion`.
- Validación en `ComercialStrategy.liquidar()`: el anatocismo solo se activa si (a) los intereses vencidos
  llevan más de un año Y (b) existe demanda judicial O acuerdo posterior — las dos condiciones son
  obligatorias siempre, no basta con que exista mora (nota ya dejada en el Sprint 2 original).
- Wiring de `CompoundInterest.calculate()` en el tramo de intereses vencidos que cumpla la condición,
  mientras el resto de la liquidación sigue en interés simple.

**Alcance incluido:**
- Activación condicionada del anatocismo comercial exactamente con las dos reglas del PDF.
- Campos nuevos en `Obligacion` + migración.

**Alcance explícitamente excluido:**
- Anatocismo civil (Art. 1617 C.C. lo prohíbe de forma general) — no aplica fuera de Comercial.
- Anatocismo tributario o laboral — no mencionados en el PDF para esas áreas.

**Riesgos / notas técnicas conocidas:**
- Migración de esquema pendiente de correr contra el `bastium.db` real del equipo al fusionar la rama,
  mismo patrón documentado ya en Sprints 8 y 12.

**Definición de Hecho:**
- Test que activa anatocismo con demanda judicial + >1 año de mora, y otro que lo deniega sin alguna de
  las dos condiciones.
- `ComercialStrategy` sigue liquidando en interés simple por defecto cuando no se cumplen las condiciones.
- Suite completa en verde.

**Estado:** Implementado (2026-07-26) — ver
`docs/superpowers/plans/2026-07-26-sprint19-anatocismo-comercial.md` y
`docs/superpowers/specs/2026-07-26-sprint19-anatocismo-comercial-design.md`. Desviación respecto al plan
original: en vez de usar `CompoundInterest.calculate()` (fórmula cerrada de una sola pasada), se
implementaron eventos de capitalización periódica (`CAPITALIZACION_INTERESES_ANATOCISMO`, nuevo en
`LiquidationCore`/`BalanceEngine`) que trasladan el interés simple ya devengado al capital cada aniversario
desde la fecha de capitalización. Esto reproduce el interés compuesto exacto y maneja correctamente abonos
que caigan a mitad del tramo (usando la maquinaria de `AllocationEngine` ya existente), a costa de que
`CompoundInterest.calculate()` sigue huérfano. Limitación conocida documentada en el spec: si un expediente
mezcla varias obligaciones comerciales y solo algunas cumplen las condiciones de anatocismo, la
capitalización actúa sobre el saldo de interés consolidado del expediente completo (el motor no separa
saldos por obligación) — heredado de la arquitectura ya existente, no introducido por este sprint.

---

## Sprint 20 — Indexación sobre capital ya indexado (algoritmo "Suma Única")

**Prioridad sugerida:** Baja/exploratoria — es un cambio de fondo en el motor core que afecta las 5 áreas
operables hoy; el Sprint 8 documentó esta limitación deliberadamente sin corregirla porque el impacto es
transversal, no local a Civil/Familia.

**Depende de:** Sprint 8 (Indexación IPC conectada, ya completo).

**Documentos a consultar:**
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, pág. 21-22, "Caso de Suma Única (Daño
  Emergente Consolidado)": Paso 1 (Indexar) → actualizar el desembolso histórico con la fórmula del IPC,
  obtiene `Va`; Paso 2 (Intereses) → sobre ese valor **ya actualizado** (`Va`), aplicar el interés civil
  puro del 6% anual (0.4867% mensual) por el tiempo transcurrido; Resultado: `Dec = Va × (1 + i)^n` — el
  interés se compone sobre el capital ya indexado, no sobre el capital histórico sin indexar (que es como
  funciona BASTIUM hoy).
- Misma página, "6. Coexistencia con Intereses": confirma que el interés civil (6%, "interés puro") es
  plenamente compatible con la indexación, y añade el caso especial de "Intereses de la Ley 80 de 1993
  (Contratos Estatales)", que permite explícitamente "ajustar el capital con el IPC y cobrar
  simultáneamente intereses moratorios sobre el capital ya indexado" — el mismo patrón "Suma Única" pero
  con nombre y fuente normativa propia para contratación estatal.

**Código existente a reutilizar:**
- `app/engine/indexation/ipc.py` → `IPCIndexation.calculate()` ya calcula `Va`; el cambio es **dónde** se
  usa ese resultado dentro del motor de intereses, no la fórmula de indexación en sí.
- `app/services/area_strategy.py` → `CivilFamiliaStrategy._construir_rate_provider()` y el wiring de
  indexación del Sprint 8 son el punto exacto donde hoy el interés se calcula solo sobre capital sin
  indexar.

**Decisión de diseño a tomar antes de codificar (con el usuario, no asumir):**
- Este cambio altera el resultado numérico de liquidaciones existentes con indexación activada — antes de
  tocar el motor core, confirmar con el usuario si el comportamiento actual (interés solo sobre capital)
  fue una simplificación consciente del MVP o si de verdad hace falta migrar al algoritmo "Suma Única"
  exacto del PDF. Dado que afecta las 5 áreas, conviene una conversación breve tipo
  `superpowers:brainstorming` antes de escribir código, igual que se hizo para el Sprint 13 y se recomienda
  para el Sprint 16.

**Código nuevo a crear (si se aprueba):**
- Modificar el motor de intereses para que, cuando una obligación tenga `aplica_indexacion_ipc=True`, el
  interés civil se calcule sobre `Va` (capital ya indexado) en vez de sobre el capital histórico.
- Flag o parámetro explícito para distinguir el algoritmo "Suma Única" del comportamiento actual, para no
  romper retrocompatibilidad de liquidaciones ya auditadas (Sprint 9) que se reconstruyan con el algoritmo
  viejo.

**Alcance incluido:**
- Algoritmo "Suma Única" completo: indexar primero, luego aplicar interés sobre el valor ya indexado.
- Caso especial Ley 80/1993 (contratos estatales) documentado como variante con la misma mecánica.

**Alcance explícitamente excluido:**
- Migrar automáticamente liquidaciones históricas ya registradas en `AuditLog` (Sprint 9) al nuevo
  algoritmo — la reconstrucción exacta de una liquidación pasada debe seguir usando el algoritmo vigente
  en el momento en que se ejecutó.

**Riesgos / notas técnicas conocidas:**
- Alto riesgo de romper resultados numéricos ya validados en Sprints 2, 3, 4, 8 si se aplica sin cuidado —
  requiere suite de regresión explícita comparando el resultado viejo vs. nuevo antes de cambiar el
  default.
- Interactúa directamente con el motor de auditoría (Sprint 9): `reconstruir_liquidacion()` debe poder
  reproducir el algoritmo que estaba vigente en la fecha de cada liquidación histórica.

**Definición de Hecho:**
- Test que reproduce el ejemplo numérico exacto del PDF (pág. 69: capital $50.000.000 de 2010 a 2025,
  indexado y luego con interés) y verifica el resultado contra el cálculo manual.
- Test de que liquidaciones auditadas antes de este sprint se siguen reconstruyendo idénticas.
- Suite completa en verde.

---

## Sprint 21 — Múltiples tasas de interés simultáneas por expediente

**Prioridad sugerida:** Media — limitación conocida desde el Sprint 2, documentada como pendiente en el
backlog técnico desde entonces.

**Depende de:** Sprints 2, 3, 4 (todas las estrategias existentes comparten esta limitación).

**Documentos a consultar:**
- Este sprint no depende de una sección nueva del PDF — es una limitación de implementación encontrada
  durante el Sprint 2 (`CivilFamiliaStrategy` toma la tasa de la primera obligación y la usa para todo el
  expediente).
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, pág. 76, "Algoritmo abstracto de
  liquidación": "Segmentos = partir(Timeline, cuando cambie tasa/base/vigencia/estado/saldo)" — el
  algoritmo maestro del PDF sí espera que la tasa pueda cambiar por tramo dentro de un mismo caso.

**Código existente a reutilizar:**
- `app/engine/interest/provider.py` → `MemoryRateProvider`/`RatePeriod` ya soporta tramos de tasa **por
  fecha calendario**; la limitación documentada en el Sprint 2 es que dos obligaciones del mismo
  expediente con tasas distintas pero fechas que se solapan no se resuelven correctamente porque la tasa
  se busca por fecha, no por obligación.
- `app/services/area_strategy.py` → `_construir_rate_provider()` (duplicado entre varias estrategias, ver
  Sprint 22) es el punto de entrada a modificar.

**Decisión de diseño a tomar antes de codificar:**
- Decidir si `MemoryRateProvider` pasa a indexarse por `obligacion_id` además de por fecha (permitiendo
  tasas distintas simultáneas), o si se construye un `RateProvider` por obligación en vez de uno solo por
  expediente.

**Código nuevo a crear:**
- Extensión de `MemoryRateProvider` (o proveedor nuevo) que resuelva la tasa por combinación de obligación
  + fecha, no solo por fecha.
- Wiring en las estrategias existentes para pasar la tasa correcta por obligación en vez de una sola tasa
  para todo el expediente.

**Alcance incluido:**
- Soporte correcto para expedientes con varias obligaciones a tasas distintas, incluyendo el caso de
  fechas que se solapan.

**Alcance explícitamente excluido:**
- Cambiar el modelo de datos de `Obligacion` — cada obligación ya tiene su propia `tasa_efectiva_anual`
  (línea 89 de `database/models.py`); el problema es solo de cómo el motor la usa.

**Riesgos / notas técnicas conocidas:**
- Tocar `MemoryRateProvider` es un cambio compartido por las 5 áreas — requiere regresión completa de la
  suite existente para confirmar que ningún expediente con una sola obligación cambia de resultado.

**Definición de Hecho:**
- Test con un expediente de 2+ obligaciones a tasas distintas y fechas solapadas, verificando que cada una
  liquida con su propia tasa.
- Suite completa en verde, sin cambios de resultado en los tests existentes de expedientes de una sola
  obligación.

---

## Sprint 22 — Limpieza técnica acumulada

**Prioridad sugerida:** Baja — deuda técnica de calidad de código, no funcionalidad faltante del PDF de
requisitos; conviene agruparla en un solo sprint de "housekeeping" antes de que crezca más con cada área
nueva.

**Depende de:** Nada bloqueante, pero toca código compartido por los Sprints 2, 3, 4 y sus estrategias.

**Tareas** (cada una detectada en code review de un sprint anterior, ver la cita puntual):
1. **Motor de allocation duplicado**: hay DOS clases `AllocationEngine` con firmas distintas —
   `app/engine/allocation/allocator.py` (método de instancia `allocate(self, payment: Payment,
   obligations: list[Obligation])`, `raise NotImplementedError`, código huérfano que nadie importa) vs.
   `app/engine/liquidation/allocation.py` (método estático `allocate(payment_amount, current_debt,
   payment_date)`, implementación real usada por `LiquidationCore`). Decidir: eliminar
   `app/engine/allocation/allocator.py` por completo (y su carpeta si queda vacía), o confirmar si el
   modelo de dominio `app.domain.obligation.base.Obligation` que usa justifica mantenerlo.
2. **Archivo vacío sin uso**: `app/engine/financial/allocation.py` (0 bytes), nombre similar a los dos de
   arriba, probablemente abandonado a mitad de refactor. Confirmar que nada lo importa y eliminarlo.
3. **Duplicación de `_eventos_de_obligacion`** entre `CivilFamiliaStrategy` y `ComercialStrategy`
   (`app/services/area_strategy.py`): método idéntico byte a byte, no tiene nada específico del área, solo
   depende de `tipo`. Ya se repitió una tercera vez en `LaboralStrategy` (Sprint 3) — subirlo a
   `AreaStrategy` (clase base, línea 26) o extraerlo a función compartida antes de que se repita en
   `TributarioStrategy` (Sprint 15). Detectado en code review del Sprint 2
   (`docs/superpowers/plans/2026-07-15-area-comercial.md`).
4. **Misma duplicación en `_construir_rate_provider`**: `SancionatorioStrategy` y `HonorariosStrategy`
   (Sprint 4) repiten, casi byte a byte, el patrón de "un solo tramo de tasa plana desde la obligación más
   antigua hasta la fecha de corte" que ya existe en `CivilFamiliaStrategy` y `ComercialStrategy`.
   Resolver junto con el punto 3 la próxima vez que se toque `area_strategy.py` — nota: si el Sprint 21
   (múltiples tasas simultáneas) se hace primero, este método cambia de fondo, conviene coordinar el
   orden. Detectado en code review del Sprint 4
   (`docs/superpowers/plans/2026-07-17-sprint4-sancionatorio-honorarios.md`, Task 5).
5. **`ObligacionFormDialog.guardar()` creciendo hacia "god method"**: cada área nueva (Comercial,
   Sancionatorio, Honorarios) agrega su propio bloque `if es_X: try: ... except: raise ValueError(...)` en
   `app/views/obligaciones.py` — hoy (después del Sprint 4) tiene 4 ramas implícitas y ~90 líneas. Con
   Laboral (Sprint 3) y Tributario (Sprint 15) ya son o serán 6 ramas. Extraer `_parse_area_campos()` (o
   una tabla de specs por campo: nombre, kwarg, mensaje de error, requerido) en vez de seguir apilando
   ramas, espejando la separación que `area_strategy.py` ya tiene por estrategia. Detectado en code review
   del Sprint 4 (`docs/superpowers/plans/2026-07-17-sprint4-sancionatorio-honorarios.md`, Task 7).

**Alcance incluido:** los 5 puntos de arriba.

**Alcance explícitamente excluido:** cualquier cambio de comportamiento visible al usuario — este sprint
es puramente estructural, la suite existente no debe cambiar de resultado en ningún test.

**Definición de Hecho:**
- Un solo `AllocationEngine` real en el código, sin huérfanos ni archivos vacíos.
- `_eventos_de_obligacion` y `_construir_rate_provider` viven en un solo lugar (clase base o función
  compartida), no duplicados por estrategia.
- `ObligacionFormDialog.guardar()` reducido a una tabla de specs por campo en vez de ramas
  `if/try/except` apiladas.
- Suite completa en verde, sin ningún cambio de resultado numérico.

---

## Sprint 23 — Bugs críticos de integridad financiera y auditoría

**Prioridad sugerida:** Alta — son bugs reales de ejecución encontrados en auditoría de código
(2026-07-21), no gaps de alcance; afectan la exactitud de liquidaciones en áreas ya operables y la
garantía de reconstrucción exacta que promete el motor de auditoría (Sprint 9).

**Depende de:** Nada — corrige código ya existente en producción (Sprints 1 y 9).

**Documentos a consultar:** Ninguno del PDF de requisitos — son bugs de implementación, no huecos de
alcance. Consultar directamente el código citado abajo.

**Hallazgos (auditoría de código, 2026-07-21, verificados leyendo el código real):**

1. **Sobrepago silenciosamente descartado** — `app/engine/liquidation/engine.py`, método
   `_process_event`, rama `elif event.event_type == "PAYMENT"`: `allocation, new_debt, remainder =
   AllocationEngine.allocate(amount, self._current_debt, event.date)` calcula correctamente el
   `remainder` cuando un pago excede la deuda total, pero la variable nunca se usa después — no se
   refleja en el `LiquidationItem` ni en ningún campo de "saldo a favor" del `LiquidationResult`. Además,
   `payment_amount = amount` guarda el pago nominal completo (lo que entró), no lo que realmente se aplicó
   a la deuda. Escenario de fallo: un abono de $10.000.000 contra una deuda de $7.000.000 se registra como
   si los $10.000.000 se hubieran aplicado íntegramente, y los $3.000.000 de exceso desaparecen del
   resultado sin ningún error ni advertencia. `AllocationEngine.allocate()` en sí está bien probado
   (`tests/liquidation/test_allocation.py::test_overpayment_generates_remainder`), pero no existe ningún
   test de integración de `LiquidationCore.process()` que ejercite un sobrepago end-to-end — ese hueco de
   cobertura ocultó el bug.
2. **Reconstrucción de auditoría rompe con `KeyError` en registros históricos** —
   `app/engine/audit/serialization.py`, función `_item_desde_dict`: `rate_source=data["rate_source"]`
   accede al diccionario sin `.get()` con valor por defecto. El campo `rate_source` se agregó a
   `LiquidationItem` en un commit posterior al que introdujo el motor de auditoría (Sprint 9); cualquier
   fila de `AuditLog.resultado_json` guardada antes de ese commit no tiene esa clave en su JSON (la tabla
   es append-only, esas filas nunca se reescriben). Escenario de fallo: `reconstruir_liquidacion()` sobre
   cualquier liquidación auditada antes de que se agregara `rate_source` lanza `KeyError: 'rate_source'` —
   rompe exactamente la garantía que el PDF exige y que el Sprint 9 implementó ("debe existir
   reconstrucción exacta de una liquidación histórica"). No existe script de backfill en `scripts/` para
   poblar el campo faltante en registros viejos.

**Código nuevo a crear / corregir:**
- En `engine.py`: capturar el `remainder` del sobrepago y exponerlo explícitamente (nuevo campo en
  `LiquidationItem`/`LiquidationResult`, ej. `saldo_a_favor`); corregir `payment_amount` para que refleje
  lo realmente aplicado si se decide distinguirlo de lo recibido.
- En `serialization.py`: cambiar a `data.get("rate_source", "N/A")` (mismo default que usa el resto del
  código cuando no se conoce la fuente); evaluar si hace falta documentar en `README.md` que los
  `AuditLog` anteriores a cierto commit reconstruyen con `rate_source="N/A"` en vez de intentar un backfill
  real (la tabla es append-only, no se puede editar el JSON histórico sin romper esa garantía).

**Alcance incluido:**
- Corrección de ambos bugs con tests de regresión explícitos.
- Decisión de diseño (con el usuario) de qué hacer con un sobrepago: ¿rechazarlo con validación en la GUI
  antes de liquidar, o aceptarlo y reflejarlo como saldo a favor del deudor?

**Riesgos / notas técnicas conocidas:**
- El bug de `rate_source` es silencioso hasta que alguien intente reconstruir una liquidación vieja desde
  la GUI (Sprint 9, doble clic en el historial) — vale la pena una prueba manual reconstruyendo una
  liquidación anterior a la fecha del commit que agregó el campo, para confirmar el alcance real del
  problema en el `bastium.db` de producción del usuario.

**Definición de Hecho:**
- Test de integración de un sobrepago real en `LiquidationCore.process()` que verifique explícitamente qué
  pasa con el excedente.
- Test que reconstruye un `AuditLog` sintético sin la clave `rate_source` en su JSON y confirma que no
  lanza `KeyError`.
- Suite completa en verde.

---

## Sprint 24 — Validación de datos: formularios de obligaciones y parámetros legales versionados

**Prioridad sugerida:** Alta — hoy es posible guardar datos absurdos (tasas negativas, fechas invertidas,
tramos de parámetros solapados) sin ningún aviso, y el error solo aparece más tarde como un resultado de
liquidación incorrecto sin explicación.

**Depende de:** Nada — corrige código existente de varios sprints (formularios de obligaciones,
`parametro_service.py` del Sprint 13).

**Hallazgos (auditoría de código, 2026-07-21):**
1. `app/views/obligaciones.py` (`ObligacionFormDialog.guardar()`, 351 líneas):
   - `tasa_efectiva_anual`, `tasa_moratoria_anual`, `ibc_vigente_anual`, `cuota_litis_pactada_pct`,
     `costas_pct_manual` solo se validan como `Decimal` parseable — nunca se rechaza un valor negativo ni
     absurdamente alto (ej. 99999%). La validación de usura sí existe (`usury_validator.py`) pero se
     dispara solo al liquidar, no al guardar — el usuario puede guardar datos inválidos y enterarse recién
     al intentar liquidar el expediente.
   - `cantidad_smlmv_uvt` sin validar signo/positividad.
   - No hay ninguna comparación entre `fecha_origen`/`fecha_inicio` de la obligación y la
     `fecha_corte_default` del expediente — se puede guardar una obligación con fecha de origen posterior a
     la fecha de corte.
   - `concepto` se guarda con `.strip()` pero nunca se valida no-vacío — inconsistente con
     `expedientes.py`, que sí exige `radicado` no vacío.
   - Único control real hoy: `valor <= 0` rechazado.
2. `app/services/parametro_service.py` (`agregar_valor`, verificado línea por línea): no valida que
   `valor` sea positivo/razonable para ninguna clave, ni que la nueva fila no se solape con un tramo
   `TRAMO_CERRADO` ya cargado para la misma `clave`, ni que `vigente_desde` sea posterior a las filas
   existentes. La única validación real es de modo (`TRAMO_CERRADO` exige `vigente_hasta`). Como
   `_resolver_fila` ordena por `vigente_desde desc, creado_en desc` y toma la primera fila, un solapamiento
   no lanza error — resuelve de forma ambigua según el orden de desempate, contradiciendo la premisa
   "append-only cronológico" que documenta el propio docstring del módulo. Además, `vigente_hasta >=
   vigente_desde` solo se valida en la GUI (`app/views/configuracion.py`), no en el service — cualquier
   otro caller (tests, scripts, un futuro sprint) puede insertar datos inconsistentes sin que nada lo
   impida.

**Código nuevo a crear:**
- Rangos de validación explícitos por campo de tasa/porcentaje en `obligaciones.py` (ej. tasa entre 0% y
  un tope razonable configurable, porcentajes entre 0% y 100% salvo donde el dominio permita más).
- Validación cruzada de fechas (origen/inicio vs. fecha de corte del expediente).
- Validación de `concepto` no vacío, igual que `radicado` en `expedientes.py`.
- Mover la validación `vigente_hasta >= vigente_desde` al service `agregar_valor` (no solo a la GUI), y
  agregar validación de solapamiento con tramos `TRAMO_CERRADO` existentes de la misma clave, y de
  signo/rango razonable en `valor` (al menos rechazar negativos para claves que nunca deberían serlo, ej.
  tasas y SMLMV).

**Alcance explícitamente excluido:**
- No se propone un catálogo de rangos por campo tipo EFDJ (sería sobre-ingeniería para este alcance) —
  bastan validaciones simples de sentido común por campo.

**Definición de Hecho:**
- Tests que confirman que `ObligacionFormDialog` rechaza tasa negativa, porcentaje fuera de rango, y fecha
  de origen posterior a la fecha de corte.
- Test que confirma que `parametro_service.agregar_valor` rechaza un valor negativo para una clave de
  tasa/indicador, y rechaza un tramo `TRAMO_CERRADO` que se solape con uno existente.
- Suite completa en verde.

---

## Sprint 25 — Rendimiento del motor de tasas, índices e historial

**Prioridad sugerida:** Media — no degrada hoy con el volumen actual de un solo abogado, pero son mejoras
baratas que evitan degradación futura conforme crezcan expedientes y años de historial.

**Depende de:** Nada.

**Hallazgos (auditoría de código, 2026-07-21):**
1. `app/engine/interest/provider.py` (`MemoryRateProvider.get_rate`) hace un scan lineal O(n) de
   `self._periods` en cada llamada, invocado día por día dentro de `app/engine/liquidation/engine.py`
   (`_accrue_time_passage`) y `app/engine/tax/moratory_interest.py`. Para procesos con años de mora
   (prescripción ejecutiva a 5 años, usura tributaria desde 1997) esto son miles de llamadas.
2. `app/services/area_strategy.py` (validación de `HonorariosStrategy`, ~líneas 506-556) llama a
   `get_parametro(...)` dos veces por obligación dentro de un loop, y cada llamada abre y cierra una sesión
   SQLAlchemy nueva (`parametro_service.py`). Los parámetros no cambian durante una misma liquidación — no
   hace falta reconsultarlos por cada obligación.
3. El mismo patrón (consulta a `get_parametro`, que abre sesión DB) ocurre dentro de
   `historical_index.get_smlmv_for_year`/`get_ipc_for_date`, llamadas repetidamente dentro de loops de
   indexación por cuota (`CivilFamiliaStrategy._evento_indexacion`, para obligaciones RECURRENTE mensuales
   con muchos meses).
4. `database/models.py` no define ningún `index=True` en columnas de filtrado frecuente:
   `Obligacion.expediente_id`, `AuditLog.expediente_id`, `Abono.obligacion_id`, `ParametroLegal.clave`. Con
   SQLite y volúmenes actuales el costo es bajo, pero es la mejora más barata y de mayor retorno si
   `parametros_legales` (ya ~350+ filas) o las tablas de expedientes/auditoría crecen con años de uso.
5. `app/views/expedientes.py` carga la tabla completa (`session.query(Expediente).all()`) sin paginar ni
   filtrar.

**Código nuevo a crear:**
- Cachear el resultado de `get_parametro` (o los valores usados repetidamente) fuera de los loops que
  iteran por obligación/cuota dentro de una misma liquidación.
- Reemplazar el scan lineal de `MemoryRateProvider` por búsqueda binaria (`bisect`) sobre la lista ya
  ordenada de tramos.
- Agregar `index=True` a las 4 columnas señaladas en `database/models.py` (requiere migración de esquema,
  mismo patrón `scripts/migrate_*.py` ya usado).
- Evaluar paginación o filtro por defecto en `expedientes.py` si el volumen lo justifica.

**Alcance explícitamente excluido:**
- No se propone cambiar `MemoryRateProvider` de diseño en memoria a una base de datos indexada — solo
  optimizar el lookup dentro del diseño actual.

**Definición de Hecho:**
- Benchmark simple (test o script) que compare tiempo de liquidación antes/después en un expediente con
  muchos años de mora.
- Migración de índices aplicada y verificada contra `bastium.db` real.
- Suite completa en verde, sin cambios de resultado numérico.

---

## Sprint 26 — Responsividad de la interfaz: liquidar/exportar sin congelar la UI

**Prioridad sugerida:** Media-alta — impacto directo de UX en operaciones que ya son lentas por diseño
(loops día a día en el motor).

**Depende de:** Nada, aunque se beneficia del Sprint 25 (un motor más rápido hace el problema menos
frecuente, pero no lo elimina para expedientes grandes).

**Hallazgos (auditoría de código, 2026-07-21):**
- Confirmado: no existe ningún `QThread`, `QRunnable`, `threading.Thread` ni `asyncio` en todo `app/`.
  `estrategia.liquidar(...)` (`app/views/expediente_detalle.py`) y la exportación a PDF/Word
  (`app/views/liquidaciones.py`) se ejecutan de forma síncrona y directa en el hilo de la UI, desde el
  manejador del botón.
- El motor de intereses (`app/engine/liquidation/engine.py`, `_accrue_time_passage`) y el interés
  moratorio tributario (`app/engine/tax/moratory_interest.py`) iteran día por día en Python puro entre
  eventos — para procesos de varios años esto son miles de iteraciones síncronas.
- No existe ningún `QProgressDialog`/`QProgressBar`/`processEvents` en ninguna vista — para expedientes con
  muchas obligaciones/abonos, la ventana puede quedar sin respuesta visible mientras liquida o exporta, sin
  ninguna señal de que está trabajando.

**Código nuevo a crear:**
- Mover la llamada a `estrategia.liquidar()` y a los generadores de PDF/Word a un `QRunnable`/`QThread`
  (patrón estándar de PySide6: `QThreadPool` + señales para reportar progreso/resultado).
- Agregar un `QProgressDialog` (modal, indeterminado si no se puede calcular progreso exacto) mientras la
  operación corre en background.
- Deshabilitar el botón de acción mientras la operación está en curso, para evitar doble liquidación
  concurrente sobre el mismo expediente.

**Alcance explícitamente excluido:**
- No se propone paralelizar el cálculo interno del motor (varias obligaciones en threads distintos) — solo
  sacar la operación completa del hilo de UI.

**Riesgos / notas técnicas conocidas:**
- Mover trabajo a un hilo secundario que además abre sesiones SQLAlchemy requiere cuidado: cada sesión debe
  crearse y cerrarse dentro del mismo hilo que la usa (SQLAlchemy no es thread-safe si se comparte una
  sesión entre hilos) — usar `get_session()` dentro del `QRunnable`, no pasar una sesión ya abierta desde
  el hilo principal.

**Definición de Hecho:**
- Smoke test manual: liquidar un expediente con muchas obligaciones/años de mora sin que la ventana deje
  de responder (se puede mover/redimensionar mientras liquida).
- Suite completa en verde (tests de GUI con `pytest-qt` cubriendo el nuevo flujo).

---

## Sprint 27 — Limpieza de dependencias no usadas y código muerto adicional

**Prioridad sugerida:** Baja — housekeeping, no afecta comportamiento, pero reduce superficie de
mantenimiento y tamaño de instalación. Complementa al Sprint 22 con hallazgos nuevos de la auditoría
2026-07-21.

**Depende de:** Nada.

**Hallazgos:**
1. `requirements.txt` — de 16 paquetes declarados, 7 no se usan en ningún archivo de `app/`, `database/`,
   `scripts/` ni `tests/` (confirmado con grep exhaustivo de imports): `fastapi`, `uvicorn`, `pandas`,
   `numpy`, `openpyxl`, `pydantic`, `alembic`. Nota: `alembic` no tiene ni `alembic.ini` ni carpeta de
   migraciones — las migraciones se hacen a mano vía `scripts/migrate_*.py`, consistente con la decisión ya
   documentada en el Sprint 5 de mantener BASTIUM simple sin esa infraestructura.
2. `rich` y `matplotlib` sí tienen un import real (no son falsos positivos de grep), pero solo los usan dos
   módulos completamente huérfanos que nadie más importa:
   - `app/engine/text/nlp_extractor.py` (`from rich.prompt import Prompt`) — además, `Prompt.ask()` hace
     una lectura bloqueante de stdin; si `LegalTextExtractor.validate_and_fill` se conectara alguna vez a
     la GUI sin cambiarlo, colgaría la app (un ejecutable Windows sin consola adjunta no tiene stdin
     interactivo).
   - `app/reports/charts.py` (`BastiumChartGenerator`) — además usa `os.path.join(os.getcwd(), ...)` en vez
     de `pathlib.Path` (único archivo del código fuente con ese patrón), dependiente del directorio de
     lanzamiento del proceso.
3. `app/engine/math/parsers.py` (`FinancialParser.parse_money`) asume siempre formato colombiano de
   miles/decimales (`.`/`,`) de forma incondicional — un texto en formato US (ej. `"5000000.00"`) se
   interpretaría 100x más grande. Bug real, pero hoy inalcanzable: no hay ningún caller de este parser en
   `app/` (código muerto).

**Decisión de diseño a tomar antes de codificar:**
- Para `nlp_extractor.py` y `charts.py`: decidir con el usuario si (a) se eliminan por completo (nadie los
  usa, no están en el roadmap de los Sprints 14-22), o (b) se conservan porque hay intención de conectarlos
  a futuro — si se conservan, al menos corregir el bug de `os.getcwd()` y documentar por qué siguen
  huérfanos.
- Para `parsers.py`: mismo criterio — eliminar si no hay intención de usarlo, o corregir el bug de formato
  si se piensa conectar a futuro (ej. para importar montos desde texto libre).

**Código nuevo a crear (según la decisión):**
- Quitar de `requirements.txt` los paquetes no usados que se decida no conservar.
- Eliminar o corregir `nlp_extractor.py`, `charts.py`, `parsers.py` según la decisión de diseño.

**Definición de Hecho:**
- `requirements.txt` solo lista paquetes con al menos un import real en el código fuente.
- Ningún archivo huérfano queda sin una decisión explícita documentada (eliminado, o conservado con
  motivo).
- Suite completa en verde tras cualquier eliminación.

---

## Sprint 28 — CI/CD, versionado, housekeeping de repositorio e higiene de tests

**Prioridad sugerida:** Media-alta para CI (protege contra regresiones subidas sin querer); baja para el
resto (housekeeping).

**Depende de:** Nada.

**Hallazgos (auditoría organizacional, 2026-07-21):**
1. **Sin CI/CD**: no existe `.github/`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `Jenkinsfile`, `tox.ini`
   ni `.pre-commit-config.yaml`. Los 367 tests solo corren si alguien ejecuta `pytest` manualmente — nada
   impide subir un commit que rompa la suite.
2. **Sin versión de la aplicación**: no hay `__version__` en ningún archivo, ni `pyproject.toml`/
   `setup.py`, ni tags de git (`git tag` vacío). Si el usuario reporta un bug, no hay forma de identificar
   qué build está corriendo.
3. **`config/` no es configuración real de runtime**: `config/decimal_config.py` solo fija precisión de
   `Decimal` al importarse (es código, no config editable). La ruta de `bastium.db` está hardcodeada en
   `database/database.py` — cambiarla requiere editar código fuente, no hay variable de entorno ni archivo
   `.env`/`config.ini`.
4. **`.gitignore` no cubre backups de base de datos**: cubre `*.db` pero no `*.db.bak-*` — confirmado,
   `bastium.db.bak-2026-07-19` y `bastium.db.bak-2026-07-20-pre-sprint12` aparecen como untracked sueltos
   en la raíz. Riesgo: un `git add .` accidental comitearía backups pesados con datos reales de clientes.
5. **3 ramas locales huérfanas sin fusionar**: `specs-en-progreso`, `sprint10-exportacion-pdf-word-backup`,
   `sprint3-4-docs-recuperados` (últimos commits 2026-07-17/18) — parecen planeación duplicada tras crear
   worktrees; limpiar o documentar por qué siguen ahí.
6. **Test "1 skipped" es en realidad un test muerto, no un skip intencional**: `tests/services/
   test_area_strategy.py`, `test_areas_no_implementadas_lanzan_error_claro_al_liquidar`, decorado con
   `@pytest.mark.parametrize("area_name,strategy_cls", [])` — lista vacía (verificado). El test dejó de
   ejercitar nada desde que Comercial/Laboral/Sancionatorio/Honorarios se implementaron (Sprints 2-4);
   nadie lo actualizó ni lo eliminó, y pytest lo reporta como "skipped" (parameter set vacío), dando una
   falsa sensación de que hay un skip intencional y documentado.
7. **Fixture de base de datos en memoria duplicada en 13+ archivos de test** fuera de `tests/views/`: el
   bloque `create_engine("sqlite:///:memory:")` + `monkeypatch.setattr(session_module, "SessionLocal",
   ...)` se repite literalmente en cada archivo nuevo (`test_usury_validator.py`, `test_smlmv_to_uvt.py`,
   `test_parametro_service.py`, etc.) en vez de vivir en un `conftest.py` raíz — ya existe el patrón
   centralizado correcto en `tests/views/conftest.py`, pero no se replicó para el resto del árbol de tests.

**Código nuevo a crear:**
- Pipeline de CI mínimo (ej. GitHub Actions) que corra `pytest` en cada push/PR a `main`.
- `__version__` en `main.py` o un módulo dedicado, más un primer tag de git.
- Variable de entorno o archivo de configuración simple para la ruta de `bastium.db` (sin
  sobre-ingeniería).
- Ampliar `.gitignore` con un patrón `*.db.bak*` (✅ ya hecho el 2026-07-26, ver más abajo).
- Decidir con el usuario qué hacer con las 3 ramas huérfanas (fusionar lo que aún sirva, borrar el resto).
- Eliminar o reescribir `test_areas_no_implementadas_lanzan_error_claro_al_liquidar` (ya no aplica) y
  quitar el `@pytest.mark.parametrize` vacío.
- Crear un `conftest.py` raíz en `tests/` con la fixture de sesión en memoria compartida, y migrar los
  archivos duplicados a usarla.

**Definición de Hecho:**
- CI corriendo y en verde en al menos un push de prueba.
- `pytest` deja de reportar "1 skipped" sin que sea por un motivo real y documentado.
- Suite completa en verde tras consolidar los fixtures duplicados.

**Progreso (2026-07-26):** `.gitignore` ya cubre `*.db.bak-*` (commit `40e5b9e`). Se limpiaron además 2
worktrees obsoletos y sus ramas (`worktree-feature+mvp-civil-familia`,
`worktree-sprint6-calendario-dias-habiles`) y una rama remota huérfana en GitHub
(`worktree-sprint4-sancionatorio-honorarios`, ya fusionada en `main`) — quedan pendientes las 3 ramas
locales huérfanas listadas en el hallazgo 5 (`specs-en-progreso`, `sprint10-exportacion-pdf-word-backup`,
`sprint3-4-docs-recuperados`), no tocadas todavía porque no se ha confirmado con el usuario si tienen
contenido único que rescatar.

**Alcance ampliado (2026-07-26, a pedido del usuario — el repo se va a publicar en GitHub para que
cualquier persona externa, estudiante, abogado o programador, pueda entenderlo y potencialmente
contribuir):**
8. **Sin documentos de cara a colaboradores externos**: no existe `CONTRIBUTING.md` (cómo levantar el
   entorno, correr tests, proponer un cambio) ni `SECURITY.md` (cómo reportar una vulnerabilidad). Tampoco
   hay ningún aviso visible de que BASTIUM calcula montos con efectos jurídicos reales (intereses,
   sanciones, liquidaciones laborales) y que es una herramienta de apoyo, no un sustituto de asesoría
   legal profesional — relevante justamente porque el repo va a quedar público y cualquiera podría
   ejecutarlo sin supervisión de un abogado.
9. **`README.md` sin badges**: no muestra estado de CI, versión ni licencia — comparado con proyectos como
   `thedotmack/claude-mem` (licencia, versión, CI, badge de reconocimiento de la comunidad), el README de
   BASTIUM no comunica de un vistazo que el proyecto está mantenido y probado.
10. **Sin plantillas de Issues/PR**: `.github/ISSUE_TEMPLATE/` y `.github/PULL_REQUEST_TEMPLATE.md` no
    existen — sin ellas, un reporte externo de bug o una propuesta de PR no tiene una estructura mínima
    que guíe qué información incluir.
11. **Sin `CHANGELOG.md`**: no hay un historial de versiones legible para alguien que no quiera leer los
    285+ commits o los 37 sprints de `Pendientes.md` completos.
12. **Licencia deliberadamente fuera de este sprint**: el usuario pidió posponer la decisión de licencia
    (afecta qué puede hacer legalmente un tercero con el código) — se movió a un sprint propio, ver
    **Sprint 38**. Este sprint prepara el badge de licencia en README apuntando a "pendiente" hasta que el
    Sprint 38 se cierre.

**Explícitamente excluido de este sprint (a pedido del usuario, 2026-07-26):** documentación traducida a
múltiples idiomas, servidor de Discord/comunidad externa, sitio de documentación aparte — infraestructura
de comunidad que solo se justifica si BASTIUM efectivamente atrae colaboradores externos activos, no antes.

**Código nuevo a crear (alcance ampliado):**
- `CONTRIBUTING.md`: cómo levantar el entorno (`.venv`, `pip install -r requirements.txt`), correr
  `pytest`, convención de commits del repo (`feat:`/`fix:`/`docs:`/`test:`/`chore:`, ya usada en todo el
  historial), y cómo proponer un sprint nuevo siguiendo el formato de `Pendientes.md`.
- `SECURITY.md`: cómo reportar una vulnerabilidad de seguridad del código, más el aviso legal — BASTIUM es
  una herramienta de apoyo para el cálculo de liquidaciones, no sustituye la asesoría de un abogado
  colegiado ni garantiza exactitud jurídica; quien lo use debe verificar los resultados contra la norma
  vigente antes de usarlos en un proceso real.
- El mismo aviso legal, en versión corta, visible cerca del inicio de `README.md`.
- Badges en el encabezado de `README.md`: estado de CI (una vez exista el pipeline de este mismo sprint),
  versión (`__version__`, una vez exista), y licencia (apuntando a "por definir — ver Sprint 38" hasta que
  se cierre).
- `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md` y
  `.github/PULL_REQUEST_TEMPLATE.md`.
- `CHANGELOG.md` en formato [Keep a Changelog](https://keepachangelog.com/), arrancando en la primera
  versión etiquetada de este mismo sprint.

**Definición de Hecho (alcance ampliado):**
- `CONTRIBUTING.md` y `SECURITY.md` existen en la raíz y GitHub los reconoce (aparecen enlazados
  automáticamente al abrir un issue nuevo o en la pestaña "Community Standards" del repo).
- El aviso legal aparece de forma visible en `README.md` y en `SECURITY.md`.
- `README.md` muestra al menos los badges de CI y versión (el de licencia puede decir "por definir" hasta
  que cierre el Sprint 38).

---

## Sprint 29 — Corrección de documentación desactualizada, inconsistente y con enlaces rotos ✅ Completado

**Prioridad sugerida:** Alta para las rutas rotas y la numeración duplicada de la guía (afectan
directamente al usuario final); media para el resto.

**Depende de:** Nada — es documentación pura, sin relación con código de motor.

**Hallazgos (auditoría de documentación, 2026-07-21, todos verificados releyendo los archivos reales):**
1. **Ruta `specifications/` rota en 3 documentos**: `README.md` (línea 100), `docs/GUIA_USUARIO.md`
   (línea 800) y `Pendientes.md` (líneas 23, 511, 589, 643) referencian `specifications/...` sin el prefijo
   `docs/`. La ruta real, desde que se movió el 2026-07-19 (commit `0b4cf5e`), es `docs/specifications/`.
   La migración corrigió una referencia interna dentro de `07_motor_juridico_familia.md` pero nunca tocó
   README, GUIA ni Pendientes — las 4 apariciones en Pendientes.md son consistentemente incorrectas.
2. **`docs/GUIA_USUARIO.md` tiene numeración de encabezados duplicada**: existen DOS secciones `### 5.12`
   — "Editar o eliminar un expediente" (línea 429) y "Ver el historial de auditoría y reconstruir una
   liquidación pasada" (línea 455) — lo que desplaza toda la numeración siguiente (la sección de
   Parámetros, hoy "5.13", debería ser "5.14").
3. **Enlace interno roto como consecuencia directa del punto 2**: línea 472 de GUIA_USUARIO.md dice "ver
   sección 5.11" refiriéndose a "Editar o eliminar un expediente", pero esa sección está numerada 5.12.
4. **`docs/GUIA_USUARIO.md` desactualizada en al menos 2 puntos verificables**:
   - Sección 2.6 dice que `pytest` debe mostrar `"81 passed"` — el número real hoy es 367 passed, 1
     skipped (Pendientes.md sí tiene el número correcto).
   - Sección 7.6 (líneas ~645-646) cita constantes `TOPE_CUOTA_LITIS_INDIVIDUAL_PCT` y
     `TOPE_HONORARIOS_TOTAL_PCT` en `area_strategy.py` — esas constantes ya no existen, fueron reemplazadas
     por `get_parametro("CUOTA_LITIS_INDIVIDUAL_PCT", ...)`/`get_parametro("HONORARIOS_TOTAL_PCT", ...)`
     desde el Sprint 13. La guía describe código pre-Sprint-13 pese a decir que refleja el estado
     posterior.
5. **4 de los 7 `docs/specifications/*.md` describen un estado anterior al real**:
   - `01_motor_temporal.md`: lista prescripción/caducidad y calendario de días hábiles como "no
     implementado" — existen y están probados desde los Sprints 6-7.
   - `02_motor_financiero.md`: lista la validación de tope de usura como pendiente — implementada desde el
     Sprint 2.
   - `06_motor_reportes.md`: dice que no hay botón de exportar a PDF/Word — existe desde el Sprint 10.
   - `07_motor_juridico_familia.md`: dice que `ComercialStrategy`/`LaboralStrategy`/
     `SancionatorioStrategy`/`HonorariosStrategy` lanzan `AreaNoImplementadaError` y que la GUI nunca las
     llama — las 4 tienen `liquidar()` real desde los Sprints 2-4.
6. **El acrónimo "EFDJ"** se usa más de 15 veces en `Pendientes.md` (incluido el título del Sprint 13) sin
   definirse nunca en ningún documento del repo — contradice el propósito explícito del propio archivo (que
   una sesión nueva de Claude pueda trabajar sin releer todo el proyecto).
7. **Hallazgos menores**: `Pendientes.md` (1500+ líneas, 22+ sprints) no tiene tabla de contenidos al
   inicio, solo un párrafo de "cómo usar este archivo"; el encabezado del Sprint 13 usa un formato de
   estado distinto al resto ("⛔ Cerrado... ✅ ... implementado" en vez de "✅ Completado"); la nota del
   Sprint 9 sobre `05_motor_auditoria.md` sigue diciendo "documenta el estado actual: vacío" pese a que el
   spec ya tiene contenido completo; las secciones con fórmulas legales en GUIA_USUARIO.md (7.1, 7.7, 7.8,
   5.11) no incluyen ningún ejemplo numérico completo de principio a fin, solo qué escribir en un campo de
   formulario.

**Código/documentación nueva a crear:**
- Corregir las 6 apariciones de `specifications/` sin prefijo (README, GUIA, 4x Pendientes.md) a
  `docs/specifications/`.
- Renumerar `docs/GUIA_USUARIO.md` a partir de la sección 5.12 duplicada (todo lo que sigue corre +1), y
  corregir el enlace roto de la línea 472.
- Actualizar sección 2.6 (conteo de tests) y sección 7.6 (constantes reemplazadas por `parametro_service`)
  de GUIA_USUARIO.md.
- Actualizar los 4 specs desactualizados (`01`, `02`, `06`, `07`) para reflejar el estado real post-Sprints
  2-10.
- Agregar una definición breve de "EFDJ" (Especificación Funcional del Dominio Jurídico, nombre que el
  propio PDF de requisitos usa en su página 63) la primera vez que aparece en `Pendientes.md`.
- Agregar un índice/tabla de contenidos al inicio de `Pendientes.md`.
- Uniformar el encabezado del Sprint 13 al mismo formato "✅ Completado" que el resto.
- Agregar al menos un ejemplo numérico completo en las secciones de GUIA_USUARIO.md que explican fórmulas
  legales.

**Definición de Hecho:**
- `grep -rn "specifications/"` en README/GUIA/Pendientes ya no devuelve ninguna ruta sin el prefijo
  `docs/`.
- `docs/GUIA_USUARIO.md` no tiene números de sección duplicados (verificar con `grep -n "^### "`).
- Los 4 specs actualizados coinciden con el código real.

**Cierre de implementación (2026-07-26):** Completado — los 7 hallazgos corregidos. Rutas `specifications/`
arregladas a `docs/specifications/` en README, GUIA_USUARIO y las 4 apariciones de Pendientes.md.
`docs/GUIA_USUARIO.md` renumerado desde la sección 5.12 duplicada (todo lo que seguía corrió +1, hasta
5.15), con los 8 enlaces internos que apuntaban a esas secciones corregidos uno por uno. Sección 2.6
actualizada al conteo de tests real (489 passed, 1 skipped) con una nota de que el número exacto sube con
cada sprint. Sección 7.6 actualizada: ya no cita las constantes `TOPE_CUOTA_LITIS_INDIVIDUAL_PCT`/
`TOPE_HONORARIOS_TOTAL_PCT` (no existen desde el Sprint 13), describe el `get_parametro(...)` real. Los 4
specs (`01`, `02`, `06`, `07`) reescritos para reflejar el estado post-Sprint 16: calendario de días
hábiles, prescripción/caducidad, validación de usura, exportación PDF/Word y las 6 áreas del derecho
operables, todos conectados y probados. "EFDJ" definido la primera vez que aparece (línea 24-27). Índice de
sprints agregado al inicio del archivo. Encabezado del Sprint 13 uniformado a "✅ Completado". Nota del
Sprint 9 sobre `05_motor_auditoria.md` corregida (ya no dice "vacío"). Ejemplos numéricos completos
agregados en GUIA_USUARIO.md secciones 7.1 (interés civil), 7.7 (indexación IPC), 7.8 (TRM) y 5.11
(liquidación laboral).

---

## Sprint 30 — Verificación de reglas de dominio con posible error de un día

**Prioridad sugerida:** Media — son bugs sutiles de un día, con bajo impacto individual pero que requieren
confirmación jurídica antes de decidir si se corrigen.

**Depende de:** Sprint 7 (prescripción/caducidad) y Sprint 3 (Área Laboral), ambos ya completos — este
sprint es de verificación/corrección puntual, no de construcción nueva.

**Hallazgos (auditoría de código, 2026-07-21):**
1. `app/engine/temporal/prescripcion.py` (`fecha_interrupcion_efectiva`): usa `(fecha_notificacion -
   fecha_radicacion).days <= 365` como proxy de "dentro de un año" para decidir si el efecto interruptor de
   la prescripción se retrotrae a la fecha de la demanda. En años bisiestos entre ambas fechas, 365 días
   puede ser un día calendario menos que "un año" real, activando la regla de "notificación tardía" un día
   antes de lo que correspondería jurídicamente.
2. `app/services/area_strategy.py` (`LaboralStrategy.liquidar`): `dias_trabajados = (obligacion.fecha_fin
   - obligacion.fecha_inicio).days` no suma 1 — para un contrato de 2020-01-01 a 2020-12-31 (año bisiesto
   completo) da 365, no 366 (verificado). El test existente (`tests/services/test_area_strategy.py`)
   documenta y asume ese mismo valor (365), así que el sistema es autoconsistente, pero es una convención
   de "días transcurridos" (resta cruda de fechas) distinta de "días trabajados inclusive" (contar el
   primer día).

**Documentos a consultar:**
- Para el punto 1: verificar contra la fuente exacta de la regla de interrupción de prescripción (Código
  Civil/Código General del Proceso, la que el Sprint 7 haya citado en su spec) si "un año" debe computarse
  como año calendario (fecha a fecha) o como 365 días corridos — el PDF de requisitos (pág. 40) dice
  explícitamente "Meses/Años: De fecha a fecha... Si no hay día equivalente en el mes de vencimiento,
  expira el último día de ese mes", lo cual sugiere que el cómputo correcto es fecha-a-fecha, no una resta
  de días fija.
- Para el punto 2: verificar contra la fuente laboral (CST) si el primer día de labor debe contarse como
  "trabajado" al calcular cesantías/prestaciones proporcionales.

**Código nuevo a crear (si se confirma que hay que corregir):**
- Cambiar `fecha_interrupcion_efectiva` para comparar fecha-a-fecha (ej. usando
  `CalendarUtils.vencimiento_calendario` o una comparación de "un año después" real) en vez de `<= 365`
  días fijos.
- Cambiar `dias_trabajados` a inclusive (`+1`) si se confirma que así lo exige la práctica laboral,
  actualizando el test existente que hoy asume 365 para el caso de año completo.

**Alcance explícitamente excluido:**
- No tocar nada más de `LaborScheduler` ni de `prescripcion.py` — este sprint es exclusivamente la
  corrección puntual de estos dos cómputos, una vez confirmados.

**Riesgos / notas técnicas conocidas:**
- Si se corrige el punto 2, el cambio afecta el resultado numérico de todas las liquidaciones laborales
  existentes (aunque sea por un solo día) — requiere aviso explícito y posiblemente recalcular
  liquidaciones ya auditadas (interactúa con el Sprint 9).

**Definición de Hecho:**
- Confirmación explícita (con el usuario o con la fuente normativa exacta) de cuál de los dos
  comportamientos es el correcto en cada caso, antes de tocar código.
- Si se corrige: test que cubre explícitamente el caso bisiesto para prescripción, y el caso de contrato de
  año completo para `dias_trabajados`.
- Suite completa en verde.

---

## Sprint 31 — Sistema de diseño visual: tema, color, tipografía e íconos en la GUI

**Prioridad sugerida:** Alta — es la base de la que dependen casi todos los demás sprints de UX (32-37);
sin un sistema de estilos centralizado, cada pantalla seguiría viéndose distinta.

**Depende de:** Nada técnicamente.

**Hallazgos (auditoría de código, 2026-07-21):**
- La app hoy no tiene NINGÚN `setStyleSheet`, `QPalette` personalizada ni archivo `.qss` en todo `app/` —
  toda la GUI se renderiza con el estilo nativo por defecto de Qt/Windows, sin ninguna identidad visual
  propia.
- Sí existe una identidad de marca ya definida y en uso — pero solo en los reportes exportados:
  `app/reports/pdf.py` define `c_burgundy = "#ae1c21"` y `c_cream = "#f5f1e9"` para las tablas del PDF. La
  GUI en vivo nunca usa estos colores.
- `app/assets/fonts/` tiene 3 pesos de una tipografía propia (`AncizarSans-Regular/Medium/ExtraBold.ttf`)
  que **nunca se cargan** con `QFontDatabase` en ningún punto de la app — la GUI corre con la fuente por
  defecto del sistema operativo.
- No hay ningún ícono en toda la app (`QIcon` no aparece en ningún `.py` de `app/views/`) — la navegación
  usa emoji sueltos (🏠, ⚙, ←) como único lenguaje visual, y todos los botones son `QPushButton` con el
  chrome nativo del SO.
- `resources/` es un paquete vacío (`resources/__init__.py`, 0 líneas más) — un scaffold que nunca se
  llenó, sugiere que hubo intención de centralizar assets ahí.
- La ventana principal no tiene ícono propio (`setWindowIcon` nunca se llama) — muestra el ícono genérico
  de Qt en la barra de tareas/título.

**Código existente a reutilizar:**
- Los colores de marca ya definidos en `app/reports/pdf.py` (`c_burgundy`, `c_cream`) — punto de partida
  obvio para la paleta de la GUI, en vez de inventar colores nuevos.
- Las 3 fuentes ya incluidas en `app/assets/fonts/`.

**Decisión de diseño a tomar antes de codificar:**
- Definir una paleta completa (no solo los 2 colores del PDF): primario, secundario, superficie/fondo,
  texto, éxito/error/advertencia, y sus variantes hover/disabled/pressed — usando burdeos/crema como ancla
  de marca.
- Decidir el mecanismo técnico: un único archivo `.qss` cargado con `app.setStyleSheet(...)` en `main.py`
  (más simple, más parecido a CSS) vs. `QPalette` programática (más nativo de Qt pero menos expresivo).
  Recomendado: `.qss` para spacing/bordes/estados, complementado con `QPalette` para los colores base del
  sistema.

**Código nuevo a crear:**
- `resources/theme.qss` (o similar): stylesheet centralizado con la paleta de marca, aplicado una sola vez
  en `main.py` vía `app.setStyleSheet(...)`.
- Carga de `AncizarSans` con `QFontDatabase.addApplicationFont()` en el arranque (`main.py`), aplicada
  como fuente por defecto de la `QApplication`.
- Un ícono de aplicación (`.ico`/`.png`) en `resources/`, aplicado con `setWindowIcon` en `MainWindow`.
- Set mínimo de íconos reemplazando los emoji de navegación (Inicio, Volver, Parámetros) y los botones de
  acción más frecuentes (Guardar, Cancelar, Eliminar, Exportar) — pueden ser SVG/PNG de una librería libre
  (ej. Feather, Lucide, Material Symbols) empaquetados en `resources/icons/`.

**Alcance incluido:**
- Paleta de color y tipografía de marca aplicadas de forma consistente a las 8 vistas existentes
  (`expedientes.py`, `obligaciones.py`, `abonos.py`, `configuracion.py`, `expediente_detalle.py`,
  `liquidaciones.py`, `main_window.py`).
- Ícono de aplicación y de navegación básicos.

**Alcance explícitamente excluido:**
- Modo oscuro/claro — este sprint solo entrega un tema único coherente (ver Sprint 37 para otras mejoras
  de personalización, si se decide agregar un modo oscuro en el futuro sería un sprint propio).
- Rediseño de la disposición de cada pantalla (eso es Sprint 32-35) — este sprint es solo la capa visual
  (color/tipografía/íconos), no la estructura.

**Riesgos / notas técnicas conocidas:**
- Un `.qss` mal alcanzado (selectores demasiado genéricos, ej. `QPushButton { ... }` sin scoping) puede
  romper widgets nativos que dependen del estilo del SO (ej. el calendario emergente de `QDateEdit`) —
  probar visualmente cada pantalla tras aplicar el stylesheet.

**Definición de Hecho:**
- Las 8 vistas existentes se ven visualmente consistentes (misma paleta, misma tipografía) al recorrerlas
  manualmente.
- Ícono de aplicación visible en la barra de tareas de Windows.
- Suite de tests de GUI (`pytest-qt`) sigue en verde tras aplicar el stylesheet.

---

## Sprint 32 — Navegación: barra mejorada, breadcrumb y atajos de teclado

**Prioridad sugerida:** Alta — la navegación es el primer punto de contacto con la app y hoy es mínima.

**Depende de:** Sprint 31 (para que los íconos de navegación ya existan).

**Hallazgos:**
- `MainWindow` (`app/views/main_window.py`) usa un único `QToolBar` no movible con 3 `QPushButton` de
  texto (`← Volver`, `🏠 Inicio`, `⚙ Parametros`) — no hay sidebar, no hay menú (`QMenuBar` no se usa en
  ningún archivo), no hay indicación de "dónde estoy" (qué expediente/área está abierta) más allá del
  contenido de la pantalla misma.
- La navegación es un historial lineal (`self._history: list[str]`) — no hay forma de saltar directo a una
  pantalla intermedia si el flujo se profundiza.
- No hay atajos de teclado en ningún punto de la navegación (no se encontró `QShortcut`/`setShortcut` en
  `app/views/`).

**Código existente a reutilizar:**
- El patrón de `_pages`/`show_page`/`_history` de `MainWindow` ya funciona y no hace falta rehacerlo — este
  sprint mejora la presentación, no la máquina de estados de navegación en sí.

**Decisión de diseño a tomar antes de codificar:**
- Confirmar con el usuario si prefiere una barra lateral fija (sidebar) o mantener el toolbar superior pero
  enriquecido (íconos + breadcrumb). Con solo 4 pantallas hoy, un sidebar puede ser excesivo — evaluar si
  conviene esperar a que el Sprint 33 (dashboard) agregue una sección más antes de invertir en un sidebar
  completo.

**Código nuevo a crear:**
- Breadcrumb/título contextual en la barra de navegación (ej. "Expedientes › Radicado 2024-00123 ›
  Liquidación") que se actualiza según la pantalla activa.
- Atajos de teclado básicos: `Alt+Izquierda`/`Backspace` para "Volver", `Ctrl+Home` para "Inicio", y
  atajos de guardar (`Ctrl+S`)/cancelar (`Esc`) en los diálogos de formulario.
- Reemplazar los botones de texto+emoji por botones con ícono (del Sprint 31) + texto, con estilo
  consistente de "activo"/"inactivo" según la pantalla actual.

**Alcance explícitamente excluido:**
- Un sidebar completo, si la decisión de diseño concluye que 4 pantallas no lo ameritan todavía — en ese
  caso el alcance se reduce a breadcrumb + atajos + íconos sobre el toolbar existente.

**Definición de Hecho:**
- El usuario puede navegar solo con teclado entre las pantallas principales.
- La barra de navegación muestra claramente en qué expediente/pantalla se está parado.
- Suite de tests de GUI en verde.

---

## Sprint 33 — Pantalla de inicio real: dashboard con resumen y alertas

**Prioridad sugerida:** Media-alta — hoy `app/views/dashboard.py` está vacío (0 bytes) y no se usa; la app
abre directo a un listado plano de expedientes sin ningún resumen ni contexto.

**Depende de:** Sprint 7 (motor de prescripción/caducidad, para alertas de vencimientos próximos) y
Sprint 9 (auditoría, para mostrar actividad reciente) — ambos ya completos, este sprint solo los expone en
la GUI.

**Hallazgos:**
- `app/views/dashboard.py` existe como archivo pero está completamente vacío y no lo importa nadie
  (confirmado en auditoría anterior) — es un hueco real de producto, no solo código muerto: hoy no hay
  ninguna pantalla de "vista general".
- El motor de prescripción (`app/engine/temporal/prescripcion.py`) y el de auditoría
  (`app/engine/audit/service.py`) ya calculan justo el tipo de información que un dashboard necesitaría
  (fechas límite, historial de liquidaciones), pero hoy solo se consumen desde dentro del detalle de cada
  expediente, uno por uno — no hay una vista agregada de "qué necesita mi atención hoy" a través de todos
  los expedientes.

**Código existente a reutilizar:**
- `app/engine/temporal/prescripcion.py` (`calcular_prescripcion`/`calcular_caducidad`) para alertas de
  "vence pronto" por expediente.
- `app/engine/audit/service.py` (`historial_de_expediente`) para una sección de "actividad reciente".
- `app/views/expedientes.py` como referencia de cómo se consulta la tabla `Expediente` hoy.

**Código nuevo a crear:**
- Construir `DashboardView` en `app/views/dashboard.py` (hoy vacío) con: conteo de expedientes por área,
  lista de expedientes con plazos próximos a vencer, y las últimas N liquidaciones ejecutadas.
- Registrar `DashboardView` como pantalla de inicio en `MainWindow` (reemplazando o precediendo al listado
  plano de expedientes).

**Alcance explícitamente excluido:**
- Gráficas/visualizaciones complejas (ej. usar `matplotlib`, hoy huérfano según el Sprint 27) — este
  sprint es de datos tabulares/listas simples, no de dataviz; evaluar una gráfica en un sprint aparte una
  vez que el dashboard base exista y se valide que es útil.

**Riesgos / notas técnicas conocidas:**
- Calcular alertas de vencimiento para TODOS los expedientes al abrir la app podría ser lento si el
  volumen crece (relacionado con el Sprint 25) — considerar cachear o calcular de forma perezosa/asíncrona
  (relacionado con el Sprint 26).

**Definición de Hecho:**
- Al abrir la app, el usuario ve un resumen útil antes de tener que abrir un expediente puntual.
- Test de GUI que verifica que el dashboard muestra el conteo correcto de expedientes y al menos una
  alerta de vencimiento con datos sintéticos.

---

## Sprint 34 — UX de formularios: agrupación, ayuda contextual y feedback en tiempo real

**Prioridad sugerida:** Media-alta — los formularios (`ObligacionFormDialog`, `ExpedienteFormDialog`) son
donde el abogado pasa más tiempo y hoy son una lista plana de campos sin jerarquía visual.

**Depende de:** Sprint 24 (validación de datos) — este sprint expone visualmente esas validaciones, no las
reemplaza; se benefician mutuamente pero pueden ejecutarse en cualquier orden.

**Hallazgos:**
- `ObligacionFormDialog` (`app/views/obligaciones.py`, 351 líneas) usa un único `QFormLayout` plano con
  ~15 campos seguidos (concepto, valor, tasa, fechas, cuota litis, costas, etc.) sin ninguna agrupación
  visual — todos los campos se muestran siempre, incluso los que no aplican según el área/tipo elegido
  (ej. campos de honorarios se ven aunque el área sea Civil).
- No hay placeholder text visible ni tooltips explicando qué significa cada campo legal para un usuario no
  técnico (ej. "tasa_efectiva_anual" vs. un label simple "Tasa de interés").
- La validación (Sprint 24) hoy solo se dispara al presionar "Guardar" (`QMessageBox` de error) — no hay
  feedback en tiempo real mientras el usuario escribe.
- Valor por defecto de tasa hardcodeado en el campo (`"6.00"`) sin explicar de dónde sale (es el interés
  civil legal del Art. 1617, pero el usuario no lo sabe sin leer la guía aparte).

**Código nuevo a crear:**
- Reorganizar `ObligacionFormDialog` en secciones colapsables o pestañas (ej. "Datos básicos", "Tasas e
  intereses", "Honorarios/Costas" — mostrando solo la sección relevante según el área/tipo elegido).
- Tooltips o texto de ayuda inline en los campos con nombres técnicos, explicando su significado legal en
  una frase simple.
- Feedback visual en tiempo real (ej. `QLineEdit` con borde rojo + ícono de advertencia) conectado a la
  validación del Sprint 24, en vez de solo un `QMessageBox` al guardar.
- Indicar visualmente de dónde sale un valor por defecto (ej. ícono de información junto al campo de tasa
  con tooltip "Valor por defecto: interés civil legal, Art. 1617 C.C.").

**Alcance explícitamente excluido:**
- No se propone rediseñar el modelo de datos ni las reglas de validación (eso es Sprint 24) — este sprint
  es puramente de presentación/interacción sobre los campos ya existentes.

**Definición de Hecho:**
- Un abogado sin conocimiento técnico puede completar el formulario de obligación entendiendo qué
  significa cada campo sin consultar la guía de usuario aparte.
- Los campos inválidos se marcan visualmente antes de intentar guardar.
- Suite de tests de GUI en verde.

---

## Sprint 35 — Búsqueda, filtros y estados vacíos en listados

**Prioridad sugerida:** Media.

**Depende de:** Se beneficia del Sprint 25 (índices de BD) si el volumen crece, pero no es bloqueante.

**Hallazgos:**
- `ExpedientesListView` (`app/views/expedientes.py`) carga y muestra la tabla completa de expedientes sin
  ningún campo de búsqueda ni filtro por área/estado (`session.query(Expediente).all()`, ya señalado en el
  Sprint 25 desde el ángulo de rendimiento; este sprint lo aborda desde el ángulo de UX).
- No existe ningún "estado vacío" diseñado — si un usuario nuevo abre la app sin expedientes cargados, ve
  una tabla en blanco sin ninguna guía de qué hacer primero.
- No hay ordenamiento de columnas en las tablas (`QTableWidget` sin `setSortingEnabled(True)`).

**Código nuevo a crear:**
- Campo de búsqueda/filtro (por radicado, demandante, demandado, área) sobre `ExpedientesListView`.
- Ordenamiento de columnas habilitado (`setSortingEnabled(True)`) en las tablas relevantes.
- Estado vacío diseñado explícitamente (mensaje + llamado a la acción) cuando la tabla no tiene filas, en
  vez de una tabla en blanco.

**Alcance explícitamente excluido:**
- Paginación (eso es una decisión de rendimiento, Sprint 25) — este sprint es UX de búsqueda/filtro/orden,
  no de paginación de datos.

**Definición de Hecho:**
- Un usuario puede encontrar un expediente por radicado o filtrar por área sin tener que hacer scroll
  manual sobre toda la lista.
- Una base de datos vacía muestra un mensaje útil, no una tabla en blanco.
- Suite de tests de GUI en verde.

---

## Sprint 36 — Feedback no bloqueante y jerarquía visual de botones

**Prioridad sugerida:** Media.

**Depende de:** Sprint 26 (threading/progreso) y Sprint 31 (tema visual) — se complementan.

**Hallazgos:**
- Toda comunicación con el usuario hoy pasa por `QMessageBox` modal (éxito, error y confirmación de
  borrado usan el mismo patrón de diálogo bloqueante) — no hay ninguna notificación no intrusiva (tipo
  "toast"/snackbar) para confirmaciones simples (ej. "Obligación guardada"), que hoy interrumpen el flujo
  con un diálogo que hay que cerrar a mano.
- Todos los botones de la app son `QPushButton` estándar sin distinción visual entre acción primaria (ej.
  "Guardar", "Liquidar"), secundaria (ej. "Cancelar") y destructiva (ej. "Eliminar expediente") — todos se
  ven exactamente igual, dependiendo solo del texto para transmitir su importancia/riesgo.

**Código nuevo a crear:**
- Un widget de notificación no bloqueante (toast/snackbar simple, ej. un `QLabel` flotante con
  auto-ocultado) para confirmaciones de bajo riesgo (guardar, actualizar), reservando `QMessageBox` modal
  solo para errores y confirmaciones de acciones destructivas/irreversibles.
- Clases de estilo (vía el `.qss` del Sprint 31) para 3 niveles de botón: primario (color de marca),
  secundario (neutro) y destructivo (rojo/advertencia) — aplicadas consistentemente en las 8 vistas.

**Alcance explícitamente excluido:**
- No se propone un sistema de notificaciones persistente/centro de notificaciones — solo feedback
  inmediato de acciones puntuales.

**Definición de Hecho:**
- Guardar una obligación exitosamente no requiere cerrar un diálogo modal para seguir trabajando.
- Los botones destructivos (eliminar) son visualmente distinguibles de los botones normales en toda la
  app.
- Suite de tests de GUI en verde.

---

## Sprint 37 — Comportamiento de ventana y accesibilidad de teclado

**Prioridad sugerida:** Baja-media.

**Depende de:** Nada.

**Hallazgos:**
- `main.py` fija `window.resize(1000, 700)` sin persistir tamaño/posición entre sesiones — cada vez que se
  abre la app, la ventana vuelve al mismo tamaño por defecto, sin recordar preferencias del usuario ni el
  estado de maximizado.
- No se verificó ningún control explícito de orden de tabulación (`setTabOrder`) en los formularios — el
  orden de foco depende del orden de creación de los widgets en código, que puede no coincidir con el orden
  visual/lógico para el usuario.
- No hay confirmación explícita de que `Enter`/`Return` dispare el botón por defecto ni que `Esc` cancele
  el diálogo de forma consistente en todos los formularios.

**Código nuevo a crear:**
- Persistir geometría de ventana (tamaño, posición, maximizado) entre sesiones usando `QSettings`.
- Revisar y fijar el orden de tabulación en los formularios más usados (`ObligacionFormDialog`,
  `ExpedienteFormDialog`).
- Confirmar/asegurar que `Enter` dispare el botón por defecto ("Guardar") y `Esc` cierre el diálogo sin
  guardar, en todos los diálogos de formulario.

**Definición de Hecho:**
- La ventana recuerda su tamaño/posición entre una sesión y la siguiente.
- Un usuario puede completar y guardar un formulario usando solo el teclado (Tab + Enter) en un orden
  lógico.
- Suite de tests de GUI en verde.

---

## Sprint 38 — Elegir licencia de código abierto y publicar `LICENSE`

**Prioridad sugerida:** Baja — no bloquea nada técnico; el usuario pidió explícitamente posponer esta
decisión (2026-07-26) para pensarla con calma, separada del resto de la profesionalización del repo
(Sprint 28).

**Depende de:** Nada técnicamente, pero idealmente se cierra después del Sprint 28 (para no dejar el badge
de licencia del README a medias más tiempo del necesario).

**Contexto:** el repositorio de BASTIUM se va a dejar público en GitHub para que cualquier persona
(estudiante, abogado, programador) pueda entenderlo y, potencialmente, contribuir o reutilizarlo. Hoy no
tiene archivo `LICENSE` — legalmente eso significa "todos los derechos reservados": cualquiera puede *ver*
el código porque el repo es público, pero nadie puede *reutilizarlo* legalmente sin permiso explícito,
aunque lo parezca por estar en GitHub.

**Opciones evaluadas en la conversación del 2026-07-26 (para retomar, no una decisión ya tomada):**
- **MIT**: la más simple y más común en proyectos individuales/educativos de GitHub. Permite a cualquiera
  usar, copiar, modificar y hasta vender el código, con la única condición de conservar el aviso de
  copyright. Máxima adopción, mínima fricción para que estudiantes o abogados-programadores lo miren y
  aprendan de él.
- **Apache 2.0**: tan permisiva como MIT, pero suma una concesión explícita de patentes y protege más al
  autor si alguien litiga por patentes. Es la que usa `thedotmack/claude-mem` (la referencia que citó el
  usuario) y es común en proyectos respaldados por empresas (Google, Microsoft, Apache Software
  Foundation).
- **GPL-3.0 (copyleft)**: cualquiera puede usar y modificar el código, pero si distribuye una versión
  modificada, está obligado a publicarla también bajo GPL. Evita que una empresa tome el motor de cálculo
  de BASTIUM y lo cierre dentro de un producto propietario sin devolver nada a la comunidad.
- **Ninguna todavía**: dejar el repo sin `LICENSE` indefinidamente (equivale legalmente a "todos los
  derechos reservados" pese a ser público).

**Preguntas a resolver con el usuario antes de decidir (no asumir):**
- ¿BASTIUM tiene o podría tener a futuro un modelo de negocio (venderlo, ofrecerlo como SaaS a despachos
  de abogados)? Una licencia permisiva (MIT/Apache) permite que un tercero tome el código y compita
  comercialmente sin restricción; GPL lo dificulta bastante más.
- ¿Le importa al usuario que alguien tome el motor de cálculo y lo use dentro de un producto cerrado sin
  aportar nada a cambio? Si le importa, GPL encaja mejor que MIT/Apache; si no, MIT es más simple.
- El PDF fuente (`REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, raíz del repo) y cualquier
  dato jurídico derivado de él pueden tener restricciones de autor propias, independientes de la licencia
  del código — confirmar que licenciar el código no implica licenciar el contenido de ese documento.

**Código nuevo a crear (según la decisión):**
- Archivo `LICENSE` en la raíz con el texto completo de la licencia elegida.
- Actualizar el badge de licencia agregado en el Sprint 28 (`README.md`) para que apunte a la licencia
  real en vez de "por definir".
- Agregar una línea en `CONTRIBUTING.md` (Sprint 28) del tipo "al contribuir, aceptas que tu contribución
  se licencie bajo los mismos términos del proyecto".

**Definición de Hecho:**
- Existe un archivo `LICENSE` en la raíz, reconocido por GitHub (aparece en la barra lateral del repo, en
  la sección "About").
- El badge de licencia en `README.md` y la sección correspondiente de `CONTRIBUTING.md` coinciden con la
  licencia real elegida.

---

## Notas de entorno (sin sprint asignado)

- ~~Validar/enable Windows "Long Paths" en la máquina de desarrollo~~ — **resuelto** (2026-07-15): se
  habilitó `LongPathsEnabled=1` en el registro de Windows para poder instalar PySide6 dentro de la ruta
  profunda de OneDrive, con confirmación previa del usuario.
- Confirmar si conviene excluir `.venv/` de la sincronización de OneDrive (hoy está en `.gitignore` pero
  OneDrive igual intenta sincronizar carpetas no versionadas dentro de la carpeta del proyecto).
