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

**Estados de sprint (actualizado 2026-08-19):** cada título de sprint —tanto en este índice como en su
propio encabezado `## Sprint N`— termina con exactamente uno de estos 7 estados, para que sea inmediato
saber qué hacer sin tener que leer el cuerpo completo. El estado va siempre pegado al título, nunca como
marca aparte dentro del cuerpo del sprint:

- ✅ **Completado** — implementado, probado, sin ningún bug de dominio confirmado y sin corregir.
- ⚠️ **Parcial** — una parte del alcance se implementó y funciona; el resto se difirió a propósito a
  otro sprint ya existente (el propio sprint dice a cuál).
- 🔴 **Bug confirmado sin corregir** — el despacho o una auditoría de código confirmó que el
  comportamiento actual es incorrecto, y ese comportamiento sigue en producción tal cual — máxima
  prioridad.
- 🔵 **Bloqueado — pendiente de confirmación/decisión** — no se puede avanzar (o no se puede cerrar del
  todo) sin una respuesta del despacho (ver `Preguntas-Para-Abogado-Abiertas.md`) o sin una decisión
  explícita del usuario.
- 📋 **Pendiente** — backlog puro: nadie lo ha empezado todavía, y no depende de ninguna respuesta o
  decisión externa para arrancar.
- 🟡 **En proceso** — la rutina autónoma (ver
  `docs/superpowers/specs/2026-08-19-rutina-autonoma-sprints-design.md`) lo empezó y no llegó a
  cerrarlo en su ventana; tiene una rama propia ya abierta y debe retomarse ahí, nunca abandonarse por
  empezar otro sprint nuevo.
- 🟠 **Reabierto** — un 🔵 Bloqueado que el usuario o el despacho ya contestaron, o un ✅ Completado
  donde apareció un bug/observación nueva después del cierre; entra a la cola de trabajo casi con la
  misma prioridad que un sprint 🟡 En proceso, antes que el backlog 📋 nuevo.

**Prioridad de la cola para trabajo autónomo:** 🟡 En proceso → 🟠 Reabierto → 🔴 Bug confirmado sin
corregir → 📋 Pendiente. Los estados ⚠️ Parcial y 🔵 Bloqueado nunca se toman directamente.

**Contexto ya construido (no repetir):**
- `docs/superpowers/specs/2026-07-14-mvp-captura-liquidacion-civil-familia-design.md` — diseño del MVP.
- `docs/superpowers/plans/2026-07-14-mvp-captura-liquidacion-civil-familia.md` — plan TDD tarea por tarea,
  las 17 tareas están marcadas `✅ COMPLETADA` con notas de ejecución real (bugs encontrados y cómo se
  resolvieron).
- `docs/specifications/01_motor_temporal.md` … `07_motor_juridico_familia.md` — qué hace cada motor hoy.
- `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf` (en `docs/`) — documento maestro de
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

**Auditoría cruzada contra las respuestas del despacho (2026-08-01):** los Sprints 2, 4, 6, 7, 8, 11, 12,
15, 16, 17, 18 y 30 estaban marcados "✅ Completado" antes de que el despacho respondiera
`Preguntas-Para-Abogado.md`. Se verificó, leyendo el código real (no solo el texto de cada sprint), si la
implementación coincide con lo que el despacho terminó confirmando. Resultado: **9 de 12 no coinciden**, 2
de ellas con impacto numérico real y confirmado en pruebas concretas (Sprint 8 — Indexación IPC: el motor
interpola por cierre de año en vez de mes a mes, calificado "jurídicamente inválido" por el propio
despacho, y es la base del Sprint 20/41; Sprint 17 — Módulo pensional: el piso de la tasa de reemplazo está
hardcodeado en 65% en vez de 55%, y el mínimo de semanas está fijo en 1.300 para cualquier año en vez de
variar históricamente, produciendo 75% en vez de 80% en el caso de prueba que trajo el propio despacho).
También el Sprint 30 (que ya esperaba esta confirmación como bloqueante) puede pasar de "pendiente de
confirmar" a "bug confirmado, sin corregir". Cada sprint afectado quedó marcado con ⚠️ en el índice y con un
bloque "**⚠️ Corrección pendiente**" dentro de su propia sección, citando la respuesta exacta del despacho
y el archivo:línea del código que no coincide — no se tocó ningún código todavía, solo se documentó.

**Sprints 39-45 (nuevos, 2026-08-01): QA real sobre el módulo de Familia recién cerrado (Sprint 20/21) y
áreas Laboral/Sancionatorio.** Un usuario probó la app con un caso real (obligaciones alimentarias
recurrentes) justo después de fusionar los Sprints 20-21, y reportó 9 observaciones puntuales. Cada una se
verificó leyendo el código (no se asumió nada) antes de convertirla en sprint: Sprint 39 (3 bugs de UI
confirmados y pequeños — etiquetas huérfanas en `QFormLayout`), Sprint 40 (bug transversal confirmado: la
tabla de detalle del PDF siempre muestra $0 de interés por fila en las 6 áreas, aunque el saldo final sí es
correcto), Sprint 41 (gap grande de alcance: obligaciones recurrentes sin reajuste anual ni cuotas
mensuales autónomas — requiere conversación previa con el usuario igual que exigieron los Sprints 13/16/20;
incluye una demanda real de alimentos aportada por el usuario como caso de prueba dorado), Sprint 42
(motor de prescripción/caducidad del Sprint 7 sigue sin conectarse al flujo real de liquidación, tal como
quedó documentado al cerrar ese sprint), Sprint 43 (indexación IPC solo existe hoy para Civil/Familia,
extenderla a otras áreas requiere decidir con el despacho dónde aplica sin duplicar mecanismos ya
existentes), Sprint 44 (varios gaps de UX en Laboral: SMMLV automático, edición de obligaciones/eventos,
descuentos del empleador, fecha de corte) y Sprint 45 (Sancionatorio: transparencia de unidad SMLMV/UVT
confirmada como mejora real; la queja de "capital creciendo exponencialmente" no se pudo reproducir en el
código y queda pendiente de un caso concreto antes de tratarla como bug).

**Sprints 47-48 (nuevos, 2026-08-06): seguimiento de lo que los Sprints 26-30 dejaron explícitamente fuera
de su propio alcance.** Sprint 47 (decidir con el usuario si se recalculan las liquidaciones históricas
afectadas por las dos correcciones de fecha/conteo del Sprint 30 — no arrancar sin esa decisión, mismo
patrón que los Sprints 13/16/20/41) y Sprint 48 (limpiar los ~400 errores preexistentes de `ruff` que el
Sprint 28 dejó fuera del pipeline de CI a propósito, y agregar `ruff check` como paso obligatorio una vez
limpio).

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

**Sprints 52-54 (nuevos, 2026-08-10): auditoría técnica transversal completa del repositorio** (barrido
automático de `ruff`/`pytest`/`pip-audit`, 2 agentes en paralelo sobre patrones de código riesgosos y
coherencia de documentación, y verificación manual de cada hallazgo releyendo el código real — mismo
método que los Sprints 23-30 y 47-48). `ruff check .` y la suite completa (984 tests) están en verde, sin
vulnerabilidades conocidas en `requirements.txt` (`pip-audit`). Los 3 hallazgos que sí ameritan sprint
propio: Sprint 52 (bug real y reproducido: `aplicar_migraciones_pendientes(db_path)` — la función que el
Sprint 51 construyó para blindar la app contra un esquema desactualizado — ignora `db_path` al sembrar
`parametros_legales`, y como efecto colateral la suite de tests toca la `bastium.db` real en cada corrida),
Sprint 53 (patrón N+1 de consultas, mismo tipo de problema que el Sprint 25 ya corrigió en
`AreaStrategy`, reintroducido sin protección en el Dashboard del Sprint 33) y Sprint 54 (`docs/GUIA_USUARIO.md`
y 2 `docs/specifications/*.md` describen comportamiento anterior a los Sprints 41/42/50, incluida una
afirmación incorrecta sobre prescripción/caducidad que sí le llega al usuario final).

**Sprints 56-61 (nuevos, 2026-08-11): reporte directo del usuario tras probar la app, con brainstorming
completo de diseño antes de escribir código** (ver
`docs/superpowers/specs/2026-08-11-parametros-ux-dialogos-crud-design.md` y
`docs/superpowers/plans/2026-08-11-parametros-ux-dialogos-crud.md`). Sprint 56 (los 7 `QDialog` del
proyecto ganan minimizar/maximizar/redimensionar). Sprints 57-58 (Parámetros: columnas de Área y Unidad
por fila, no editables después de creadas, con migración de las 683 filas existentes según una tabla
área-por-clave derivada del código real y revisada con el usuario; vigencia "inteligente" para
parámetros anuales de gobierno; IPC con su variación % cruda visible junto al índice ya calculado).
Sprint 59 (tooltips ⓘ de ayuda, hoy solo en 1 de ~15 campos de `ObligacionFormDialog`, extendidos a los
4 formularios principales de captura). Sprint 60 (Obligaciones y Abonos ganan "Eliminar"
completo/"Editar" que les faltaba, mismo patrón que ya tiene Eventos Laborales). Sprint 61 (placeholder,
sin implementar: conectar a futuro los 18 parámetros de prescripción/caducidad que hoy no tiene ningún
botón real que los dispare).

**Sprints 80-102 (nuevos, 2026-08-19): ~60 plantillas y documentos de referencia enviados por el despacho
(Ediciones Sistematizadas Equidad + Superintendencia Financiera), convertidos a Markdown con
[MarkItDown](https://github.com/microsoft/markitdown) y comparados contra el código real por 4
investigaciones en paralelo.** Los originales y su conversión viven en
`docs/Archivos de referencia abogado/` — **carpeta en `.gitignore`, nunca se sube al repo público**: trae
material con copyright de terceros (prohíben su reproducción) y al menos un caso real de cliente con
nombre completo; cada sprint de abajo cita la ruta exacta del archivo que hay que abrir localmente al
trabajarlo. Resultado por bloque: **Sprints 80-84** (tasas históricas de interés: la serie mensual real de
IPC 2003-2026 avanza el desbloqueo del Sprint 8; se descubrió que el interés civil del 6% que ya usa el
despacho en sus propias plantillas no es ninguna de las 2 fórmulas que contemplaba la pregunta abierta del
Sprint 76, sino una tercera — ver esa pregunta ampliada en `Preguntas-Para-Abogado-Abiertas.md`). **Sprints
85-91** (módulo pensional: retroactivos, bono pensional, indemnización sustitutiva, RAIS, régimen ISS
histórico y tasa de reemplazo para invalidez/1993-2003/transición — casi todo alcance jurídico nuevo,
bloqueado a la espera de confirmación del despacho, salvo el retroactivo que sí reutiliza motor existente).
**Sprints 92-96** (Laboral: indemnización por despido Art. 64 CST, salarios dejados de percibir con
reajuste anual — reabre una exclusión que el propio Sprint 75 había dejado a propósito fuera de alcance —,
contrato realidad, horas extra/recargos, y trabajo doméstico por jornada parcial). **Sprints 97-102**
(dominio completamente nuevo de responsabilidad civil extracontractual/lucro cesante, hoy inexistente en
BASTIUM — Sprint 97 es la decisión de arquitectura que bloquea 98-100 —, más 2 piezas menores de
indexación IPC que sí se pueden construir sin esa decisión). El caso real que venía adjunto con las
plantillas resultó ser el mismo "Radicado 2224" ya usado en el Sprint 76, no un caso nuevo.

---

## Índice de sprints

- [Sprint 2 — Área Comercial ✅ Completado](#sprint-2--área-comercial--completado)
- [Sprint 3 — Área Laboral ✅ Completado](#sprint-3--área-laboral--completado)
- [Sprint 4 — Área Sancionatorio y Honorarios ✅ Completado](#sprint-4--área-sancionatorio-y-honorarios--completado)
- [Sprint 5 — Carga de datos históricos (IPC, SMLMV, IBC, Tasa de Usura, UVT) ✅ Completado](#sprint-5--carga-de-datos-históricos-ipc-smlmv-ibc-tasa-de-usura-uvt--completado)
- [Sprint 6 — Calendario de días hábiles judiciales y términos procesales ✅ Completado](#sprint-6--calendario-de-días-hábiles-judiciales-y-términos-procesales--completado)
- [Sprint 7 — Motor de prescripción y caducidad ✅ Completado](#sprint-7--motor-de-prescripción-y-caducidad--completado)
- [Sprint 8 — Conectar indexación IPC al área Civil/Familia 🔵 Bloqueado — pendiente de confirmación](#sprint-8--conectar-indexación-ipc-al-área-civilfamilia--bloqueado--pendiente-de-confirmación) — mecanismo mensual listo y probado; ya se encontró la fuente real del DANE (Sprint 80), falta confirmar 2 detalles de alcance con el despacho
- [Sprint 9 — Motor de auditoría / bitácora ✅ Completado](#sprint-9--motor-de-auditoría--bitácora--completado)
- [Sprint 10 — Exportación de liquidación a PDF/Word ✅ Completado](#sprint-10--exportación-de-liquidación-a-pdfword--completado)
- [Sprint 11 — Derecho Tributario (DIAN) ✅ Completado (11a)](#sprint-11--derecho-tributario-dian--completado-11a) — ver corrección del Sprint 15 (11b)
- [Sprint 12 — TRM y obligaciones en moneda extranjera ✅ Completado](#sprint-12--trm-y-obligaciones-en-moneda-extranjera--completado)
- [Sprint 13 — Arquitectura de motor de reglas versionado (EFDJ) ✅ Completado](#sprint-13--arquitectura-de-motor-de-reglas-versionado-efdj--completado)
- [Sprint 14 — Tabla histórica de UVT (DIAN) ✅ Completado](#sprint-14--tabla-histórica-de-uvt-dian--completado)
- [Sprint 15 — Tributario completo: sanciones, imputación y modelo de Obligación Tributaria (cierre del Sprint 11b) ✅ Completado](#sprint-15--tributario-completo-sanciones-imputación-y-modelo-de-obligación-tributaria-cierre-del-sprint-11b--completado)
- [Sprint 16 — Seguridad social, incapacidades y suspensiones contractuales (Laboral) ✅ Completado](#sprint-16--seguridad-social-incapacidades-y-suspensiones-contractuales-laboral--completado)
- [Sprint 17 — Módulo pensional (IBL, tasa de reemplazo, densidad de semanas) ✅ Completado](#sprint-17--módulo-pensional-ibl-tasa-de-reemplazo-densidad-de-semanas--completado)
- [Sprint 18 — Costas judiciales con tabla real de rangos (Acuerdo PSAA16-10554) 🔵 Bloqueado — pendiente de confirmación](#sprint-18--costas-judiciales-con-tabla-real-de-rangos-acuerdo-psaa16-10554--bloqueado--pendiente-de-confirmación) — validación de rango manual implementada; pregunta abierta sobre si la tabla simple reemplaza la granular
- [Sprint 19 — Anatocismo comercial condicionado (Art. 886 C.Co.) ✅ Completado](#sprint-19--anatocismo-comercial-condicionado-art-886-cco--completado)
- [Sprint 20 — Indexación sobre capital ya indexado (algoritmo "Suma Única") ✅ Completado](#sprint-20--indexación-sobre-capital-ya-indexado-algoritmo-suma-única--completado)
- [Sprint 21 — Múltiples tasas de interés simultáneas por expediente ✅ Completado](#sprint-21--múltiples-tasas-de-interés-simultáneas-por-expediente--completado)
- [Sprint 22 — Limpieza técnica acumulada ✅ Completado](#sprint-22--limpieza-técnica-acumulada--completado)
- [Sprint 23 — Bugs críticos de integridad financiera y auditoría ✅ Completado](#sprint-23--bugs-críticos-de-integridad-financiera-y-auditoría--completado)
- [Sprint 24 — Validación de datos: formularios de obligaciones y parámetros legales versionados 📋 Pendiente](#sprint-24--validación-de-datos-formularios-de-obligaciones-y-parámetros-legales-versionados--pendiente)
- [Sprint 25 — Rendimiento del motor de tasas, índices e historial ✅ Completado](#sprint-25--rendimiento-del-motor-de-tasas-índices-e-historial--completado)
- [Sprint 26 — Responsividad de la interfaz: liquidar/exportar sin congelar la UI ✅ Completado](#sprint-26--responsividad-de-la-interfaz-liquidarexportar-sin-congelar-la-ui--completado)
- [Sprint 27 — Limpieza de dependencias no usadas y código muerto adicional ✅ Completado](#sprint-27--limpieza-de-dependencias-no-usadas-y-código-muerto-adicional--completado)
- [Sprint 28 — CI/CD, versionado, housekeeping de repositorio e higiene de tests ✅ Completado](#sprint-28--cicd-versionado-housekeeping-de-repositorio-e-higiene-de-tests--completado)
- [Sprint 29 — Corrección de documentación desactualizada, inconsistente y con enlaces rotos ✅ Completado](#sprint-29--corrección-de-documentación-desactualizada-inconsistente-y-con-enlaces-rotos--completado)
- [Sprint 30 — Verificación de reglas de dominio con posible error de un día ✅ Completado](#sprint-30--verificación-de-reglas-de-dominio-con-posible-error-de-un-día--completado)
- [Sprint 31 — Sistema de diseño visual: tema, color, tipografía e íconos en la GUI ✅ Completado](#sprint-31--sistema-de-diseño-visual-tema-color-tipografía-e-íconos-en-la-gui--completado)
- [Sprint 32 — Navegación: barra mejorada, breadcrumb y atajos de teclado ✅ Completado](#sprint-32--navegación-barra-mejorada-breadcrumb-y-atajos-de-teclado--completado)
- [Sprint 33 — Pantalla de inicio real: dashboard con resumen y alertas ✅ Completado](#sprint-33--pantalla-de-inicio-real-dashboard-con-resumen-y-alertas--completado)
- [Sprint 34 — UX de formularios: agrupación, ayuda contextual y feedback en tiempo real ✅ Completado](#sprint-34--ux-de-formularios-agrupación-ayuda-contextual-y-feedback-en-tiempo-real--completado)
- [Sprint 35 — Búsqueda, filtros y estados vacíos en listados ✅ Completado](#sprint-35--búsqueda-filtros-y-estados-vacíos-en-listados--completado)
- [Sprint 36 — Feedback no bloqueante y jerarquía visual de botones ✅ Completado](#sprint-36--feedback-no-bloqueante-y-jerarquía-visual-de-botones--completado)
- [Sprint 37 — Comportamiento de ventana y accesibilidad de teclado ✅ Completado](#sprint-37--comportamiento-de-ventana-y-accesibilidad-de-teclado--completado)
- [Sprint 38 — Elegir licencia de código abierto y publicar `LICENSE` ✅ Completado](#sprint-38--elegir-licencia-de-código-abierto-y-publicar-license--completado)
- [Sprint 39 — Bug de UI: etiquetas huérfanas en QFormLayout (Sancionatorio y Laboral) ✅ Completado](#sprint-39--bug-de-ui-etiquetas-huérfanas-en-qformlayout-sancionatorio-y-laboral--completado)
- [Sprint 40 — El interés causado no aparece en la tabla del PDF (bug transversal a todas las áreas) ✅ Completado](#sprint-40--el-interés-causado-no-aparece-en-la-tabla-del-pdf-bug-transversal-a-todas-las-áreas--completado)
- [Sprint 41 — Familia: obligaciones recurrentes con reajuste anual, concepto por mes y cuotas seleccionables para abono ✅ Completado](#sprint-41--familia-obligaciones-recurrentes-con-reajuste-anual-concepto-por-mes-y-cuotas-seleccionables-para-abono--completado)
- [Sprint 42 — Conectar el motor de prescripción/caducidad al flujo real de liquidación ✅ Completado](#sprint-42--conectar-el-motor-de-prescripcióncaducidad-al-flujo-real-de-liquidación--completado)
- [Sprint 43 — Indexación IPC como opción disponible en todas las áreas (hoy exclusiva de Civil/Familia) ✅ Completado](#sprint-43--indexación-ipc-como-opción-disponible-en-todas-las-áreas-hoy-exclusiva-de-civilfamilia--completado)
- [Sprint 44 — Laboral: salario mínimo automático, descuentos, edición de obligaciones/eventos y fecha de corte ✅ Completado](#sprint-44--laboral-salario-mínimo-automático-descuentos-edición-de-obligacioneseventos-y-fecha-de-corte--completado)
- [Sprint 45 — Sancionatorio: transparencia de la unidad SMLMV/UVT y aclaración del caso de capital creciente ✅ Completado](#sprint-45--sancionatorio-transparencia-de-la-unidad-smlmvuvt-y-aclaración-del-caso-de-capital-creciente--completado)
- [Sprint 46 — El saldo a favor de un sobrepago no aparece en el PDF/Word ni en la pantalla de resultado ✅ Completado](#sprint-46--el-saldo-a-favor-de-un-sobrepago-no-aparece-en-el-pdfword-ni-en-la-pantalla-de-resultado--completado)
- [Sprint 47 — Recalcular liquidaciones históricas afectadas por las correcciones del Sprint 30 ✅ Completado](#sprint-47--recalcular-liquidaciones-históricas-afectadas-por-las-correcciones-del-sprint-30--completado)
- [Sprint 48 — Limpiar la deuda de `ruff` preexistente y agregar el chequeo de lint al pipeline de CI ✅ Completado](#sprint-48--limpiar-la-deuda-de-ruff-preexistente-y-agregar-el-chequeo-de-lint-al-pipeline-de-ci--completado)
- [Sprint 49 — Bug de UI: los botones "Volver"/"Inicio" reaparecen visibles tras el primer render de la ventana ✅ Completado](#sprint-49--bug-de-ui-los-botones-volverinicio-reaparecen-visibles-tras-el-primer-render-de-la-ventana--completado)
- [Sprint 50 — Mejoras de personalización y presentación diferidas de los Sprints 31-33 (modo oscuro, sidebar, gráficas del dashboard) ✅ Completado](#sprint-50--mejoras-de-personalización-y-presentación-diferidas-de-los-sprints-31-33-modo-oscuro-sidebar-gráficas-del-dashboard--completado)
- [Sprint 51 — Migración automática de esquema y datos al arrancar la app ✅ Completado](#sprint-51--migración-automática-de-esquema-y-datos-al-arrancar-la-app--completado)
- [Sprint 52 — Bug de integridad: `aplicar_migraciones_pendientes` ignora `db_path` al sembrar `parametros_legales` ✅ Completado](#sprint-52--bug-de-integridad-aplicar_migraciones_pendientes-ignora-db_path-al-sembrar-parametros_legales--completado)
- [Sprint 53 — Rendimiento: patrón N+1 de consultas en el Dashboard ✅ Completado](#sprint-53--rendimiento-patrón-n1-de-consultas-en-el-dashboard--completado)
- [Sprint 54 — Corrección de documentación desactualizada tras los Sprints 41, 42, 50 y 51 ✅ Completado](#sprint-54--corrección-de-documentación-desactualizada-tras-los-sprints-41-42-50-y-51--completado)
- [Sprint 55 — 3 bugs de UI en el Dashboard: gráfica con colores viejos, etiquetas apretadas y tabla editable ✅ Completado](#sprint-55--3-bugs-de-ui-en-el-dashboard-gráfica-con-colores-viejos-etiquetas-apretadas-y-tabla-editable--completado)
- [Sprint 56 — Diálogos redimensionables/maximizables (los 7 QDialog del proyecto) ✅ Completado](#sprint-56--diálogos-redimensionablesmaximizables-los-7-qdialog-del-proyecto--completado)
- [Sprint 57 — Parámetros: columnas Área y Unidad por fila ✅ Completado](#sprint-57--parámetros-columnas-área-y-unidad-por-fila--completado)
- [Sprint 58 — Parámetros: presentación inteligente (vigencia, IPC crudo vs. calculado, historial) ✅ Completado](#sprint-58--parámetros-presentación-inteligente-vigencia-ipc-crudo-vs-calculado-historial--completado)
- [Sprint 59 — Tooltips ⓘ de ayuda en los 4 formularios principales ✅ Completado](#sprint-59--tooltips-de-ayuda-en-los-4-formularios-principales--completado)
- [Sprint 60 — Editar/eliminar Obligaciones y Abonos ✅ Completado](#sprint-60--editareliminar-obligaciones-y-abonos--completado)
- [Sprint 61 — Conectar los parámetros de prescripción/caducidad sin wiring a pantallas reales ✅ Completado](#sprint-61--conectar-los-parámetros-de-prescripcióncaducidad-sin-wiring-a-pantallas-reales--completado)
- [Sprint 62 — Corregir referencias rotas tras mover Pendientes/Preguntas-Para-Abogado/SECURITY/PDF a docs/ 📋 Pendiente](#sprint-62--corregir-referencias-rotas-tras-mover-pendientespreguntas-para-abogadosecuritypdf-a-docs--pendiente)
- [Sprint 63 — Documentar en README/GUIA_USUARIO las funciones de los Sprints 52-60 📋 Pendiente](#sprint-63--documentar-en-readmeguia_usuario-las-funciones-de-los-sprints-52-60--pendiente)
- [Sprint 64 — Reorganizar los backups de bastium.db en una carpeta backups/ ✅ Completado](#sprint-64--reorganizar-los-backups-de-bastiumdb-en-una-carpeta-backups--completado)
- [Sprint 65 — Lanzador de doble clic "Iniciar BASTIUM.bat" ✅ Completado](#sprint-65--lanzador-de-doble-clic-iniciar-bastiumbat--completado)
- [Sprint 66 — Reorganizar "Parametros" en "Configuraciones" con submenú Parámetros/Apariencia ✅ Completado](#sprint-66--reorganizar-parametros-en-configuraciones-con-submenú-parámetrosapariencia--completado)
- [Sprint 67 — Checkbox invisible en modo claro y oscuro (indicador de QCheckBox) ✅ Completado](#sprint-67--checkbox-invisible-en-modo-claro-y-oscuro-indicador-de-qcheckbox--completado)
- [Sprint 68 — Parámetros: editar/eliminar de usuario, vigencia clara, unidad desplegable y tooltips homologados ✅ Completado](#sprint-68--parámetros-editareliminar-de-usuario-vigencia-clara-unidad-desplegable-y-tooltips-homologados--completado)
- [Sprint 69 — Configuraciones: Restablecer datos de fábrica ✅ Completado](#sprint-69--configuraciones-restablecer-datos-de-fábrica--completado)
- [Sprint 70 — Motor de vigencia de leyes por año (Ley 100/1993, Ley 797/2003, Ley 2381/2024 y transiciones CST/CPT) 🔵 Bloqueado — pendiente de confirmación](#sprint-70--motor-de-vigencia-de-leyes-por-año-ley-1001993-ley-7972003-ley-23812024-y-transiciones-cstcpt--bloqueado--pendiente-de-confirmación)
- [Sprint 71 — Checkbox "aplica indexación IPC" invisible en Agregar Obligación (seguimiento Sprint 67) ✅ Completado](#sprint-71--checkbox-aplica-indexación-ipc-invisible-en-agregar-obligación-seguimiento-sprint-67--completado)
- [Sprint 72 — Rediseño del formulario "Agregar Obligación": tamaño inicial y layout responsivo ✅ Completado](#sprint-72--rediseño-del-formulario-agregar-obligación-tamaño-inicial-y-layout-responsivo--completado)
- [Sprint 73 — Obligaciones recurrentes con fechas personalizadas no mensuales (ej. gastos de vestuario) ✅ Completado](#sprint-73--obligaciones-recurrentes-con-fechas-personalizadas-no-mensuales-ej-gastos-de-vestuario--completado)
- [Sprint 74 — Familia: intake inicial de edad, beneficiario y tipo de alimentos (árbol de decisión) 📋 Pendiente](#sprint-74--familia-intake-inicial-de-edad-beneficiario-y-tipo-de-alimentos-árbol-de-decisión--pendiente)
- [Sprint 75 — Cuotas recurrentes en Civil/Familia y Comercial, con selección de pago por rango e imputación en cascada ✅ Completado](#sprint-75--cuotas-recurrentes-en-civilfamilia-y-comercial-con-selección-de-pago-por-rango-e-imputación-en-cascada--completado)
- [Sprint 76 — Hallazgos de una prueba práctica en Civil/Familia (reporte, reajuste anual, tasa diaria) ✅ Completado (4 hallazgos corregidos, 1 pregunta abierta)](#sprint-76--hallazgos-de-una-prueba-práctica-en-civilfamilia-reporte-reajuste-anual-tasa-diaria--completado-4-hallazgos-corregidos-1-pregunta-abierta)
- [Sprint 77 — Persistir `LiquidationResult.alertas` en las exportaciones PDF/Word 🟡 En proceso](#sprint-77--persistir-liquidationresultalertas-en-las-exportaciones-pdfword--en-proceso)
- [Sprint 78 — Conteo inclusivo (`+1`) en `calcular_densidad_semanas` — confirmar con el despacho 📋 Pendiente](#sprint-78--conteo-inclusivo-1-en-calcular_densidad_semanas--confirmar-con-el-despacho--pendiente)
- [Sprint 79 — Confirmar si las costas procesales deben entrar en la base de interés de "Suma Única" 📋 Pendiente](#sprint-79--confirmar-si-las-costas-procesales-deben-entrar-en-la-base-de-interés-de-suma-única--pendiente)
- [Sprint 80 — Cargar la serie mensual real de IPC (2003-2026) y avanzar el desbloqueo del Sprint 8 📋 Pendiente](#sprint-80--cargar-la-serie-mensual-real-de-ipc-2003-2026-y-avanzar-el-desbloqueo-del-sprint-8--pendiente)
- [Sprint 81 — Extender la serie de IBC/Usura ("Consumo y Ordinario") hacia atrás hasta 1971 con la certificación real de la Superfinanciera 📋 Pendiente](#sprint-81--extender-la-serie-de-ibcusura-consumo-y-ordinario-hacia-atrás-hasta-1971-con-la-certificación-real-de-la-superfinanciera--pendiente)
- [Sprint 82 — Cargar la serie histórica semanal de DTF (Banco de la República) como parámetro legal reutilizable 📋 Pendiente](#sprint-82--cargar-la-serie-histórica-semanal-de-dtf-banco-de-la-república-como-parámetro-legal-reutilizable--pendiente)
- [Sprint 83 — Documentar y decidir la convención "tasa mensual con prorrateo de 30 días" que usan la mayoría de plantillas del despacho (i1, i2, i7, i9, i13) 📋 Pendiente](#sprint-83--documentar-y-decidir-la-convención-tasa-mensual-con-prorrateo-de-30-días-que-usan-la-mayoría-de-plantillas-del-despacho-i1-i2-i7-i9-i13--pendiente)
- [Sprint 84 — Alinear el interés moratorio tributario (E.T. art. 635) con la convención literal de la DIAN (366 días, lineal) o confirmar que el cálculo actual es el correcto 📋 Pendiente](#sprint-84--alinear-el-interés-moratorio-tributario-et-art-635-con-la-convención-literal-de-la-dian-366-días-lineal-o-confirmar-que-el-cálculo-actual-es-el-correcto--pendiente)
- [Sprint 85 — Retroactivo y reliquidación pensional: mesada por mesada, incrementos e intereses de mora (Art. 141 Ley 100) ⚠️ Parcial](#sprint-85--retroactivo-y-reliquidación-pensional-mesada-por-mesada-incrementos-e-intereses-de-mora-art-141-ley-100--parcial)
- [Sprint 86 — Bono pensional Tipo A (modalidades 1 y 2) con intereses DTF pensional 🔵 Bloqueado — pendiente de confirmación](#sprint-86--bono-pensional-tipo-a-modalidades-1-y-2-con-intereses-dtf-pensional--bloqueado--pendiente-de-confirmación)
- [Sprint 87 — Cálculo actuarial de cotizaciones omisas, intereses de mora en cotizaciones y salario básico deflactado (Decreto 1225/2024) 🔵 Bloqueado — pendiente de confirmación](#sprint-87--cálculo-actuarial-de-cotizaciones-omisas-intereses-de-mora-en-cotizaciones-y-salario-básico-deflactado-decreto-12252024--bloqueado--pendiente-de-confirmación)
- [Sprint 88 — Indemnización sustitutiva de pensión 🔵 Bloqueado — pendiente de confirmación](#sprint-88--indemnización-sustitutiva-de-pensión--bloqueado--pendiente-de-confirmación)
- [Sprint 89 — Monto mensual de pensión en Régimen de Ahorro Individual (RAIS) 🔵 Bloqueado — pendiente de confirmación](#sprint-89--monto-mensual-de-pensión-en-régimen-de-ahorro-individual-rais--bloqueado--pendiente-de-confirmación)
- [Sprint 90 — IBL del régimen ISS anterior a la Ley 100: últimas 100 y 150 semanas 🔵 Bloqueado — pendiente de confirmación](#sprint-90--ibl-del-régimen-iss-anterior-a-la-ley-100-últimas-100-y-150-semanas--bloqueado--pendiente-de-confirmación)
- [Sprint 91 — Tasa de reemplazo: extender a pensión de invalidez (grados 1 y 2), régimen 1993-2003 y régimen de transición 🔵 Bloqueado — pendiente de confirmación](#sprint-91--tasa-de-reemplazo-extender-a-pensión-de-invalidez-grados-1-y-2-régimen-1993-2003-y-régimen-de-transición--bloqueado--pendiente-de-confirmación)
- [Sprint 92 — Laboral: indemnización por despido injustificado (Art. 64 CST) 📋 Pendiente](#sprint-92--laboral-indemnización-por-despido-injustificado-art-64-cst--pendiente)
- [Sprint 93 — Laboral: salarios y prestaciones dejadas de percibir con reajuste anual (IPC o SMMLV) — reabre la exclusión del Sprint 75 📋 Pendiente](#sprint-93--laboral-salarios-y-prestaciones-dejadas-de-percibir-con-reajuste-anual-ipc-o-smmlv--reabre-la-exclusión-del-sprint-75--pendiente)
- [Sprint 94 — Laboral: contrato realidad (privado y sector público) 📋 Pendiente](#sprint-94--laboral-contrato-realidad-privado-y-sector-público--pendiente)
- [Sprint 95 — Laboral: horas extra diurnas/nocturnas y recargos dominicales/festivos 📋 Pendiente](#sprint-95--laboral-horas-extra-diurnasnocturnas-y-recargos-dominicalesfestivos--pendiente)
- [Sprint 96 — Laboral: liquidación de prestaciones para trabajo doméstico por días/jornada parcial 📋 Pendiente](#sprint-96--laboral-liquidación-de-prestaciones-para-trabajo-doméstico-por-díasjornada-parcial--pendiente)
- [Sprint 97 — Nuevo dominio: Responsabilidad Civil Extracontractual / Indemnización de Perjuicios (decisión de alcance y arquitectura) 🔵 Bloqueado — pendiente de confirmación](#sprint-97--nuevo-dominio-responsabilidad-civil-extracontractual--indemnización-de-perjuicios-decisión-de-alcance-y-arquitectura--bloqueado--pendiente-de-confirmación)
- [Sprint 98 — Motor actuarial de lucro cesante (fórmula Baremo judicial + tablas de mortalidad Resolución 1555/2010) 🔵 Bloqueado — pendiente de confirmación](#sprint-98--motor-actuarial-de-lucro-cesante-fórmula-baremo-judicial--tablas-de-mortalidad-resolución-15552010--bloqueado--pendiente-de-confirmación)
- [Sprint 99 — Daño emergente consolidado: ledger mensual de gastos indexados por concepto 🔵 Bloqueado — pendiente de confirmación](#sprint-99--daño-emergente-consolidado-ledger-mensual-de-gastos-indexados-por-concepto--bloqueado--pendiente-de-confirmación)
- [Sprint 100 — Beneficio dejado de percibir como fruto civil 🔵 Bloqueado — pendiente de confirmación](#sprint-100--beneficio-dejado-de-percibir-como-fruto-civil--bloqueado--pendiente-de-confirmación)
- [Sprint 101 — Desindexación / deflactación de cantidad única (IPC inverso) 📋 Pendiente](#sprint-101--desindexación--deflactación-de-cantidad-única-ipc-inverso--pendiente)
- [Sprint 102 — Verificación: indexación de cantidad única con abonos secuenciales (Suma Única + abonos) 📋 Pendiente](#sprint-102--verificación-indexación-de-cantidad-única-con-abonos-secuenciales-suma-única--abonos--pendiente)

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

**✅ Corrección aplicada (2026-08-01, verificado contra la respuesta del despacho,
`Preguntas-Para-Abogado-Respondidas.md` Sprint 2):** el despacho descartó las dos opciones que se habían dejado
abiertas (rechazar / truncar) y exigió la tercera vía implementada ahora: `ComercialStrategy` ya no
rechaza la liquidación cuando una tasa pactada supera la usura. `usury_validator.py` pasó de
`validar_tasa_usura` (lanzaba `TasaUsurariaError`, eliminada) a `calcular_tope_usura` (solo calcula el
tope, no rechaza nada). `area_strategy.py` (`ComercialStrategy._calcular_sancion_usura` /
`_aplicar_sanciones_usura`) liquida con la tasa realmente pactada, corre una liquidación sombra con la
tasa recortada al tope legal (nunca devuelta al usuario, solo de referencia), calcula
`Intereses_Cobrados_En_Exceso = Intereses_Cobrados - Intereses_Cobrados_Con_Tasa_Usura`, y resta del saldo
`Sancion = Intereses_Cobrados_En_Exceso × 2` como un rubro adicional visible en el resultado (puede dejar
saldo a favor del deudor). `README.md`/`docs/GUIA_USUARIO.md`/`docs/specifications/02_motor_financiero.md`
actualizados. Suite completa en verde (619 passed, 1 skipped).
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

**Seguimiento de los pendientes diferidos:** los tres puntos explícitamente excluidos ya se cerraron por
su cuenta — seguridad social/incapacidades/suspensiones en el Sprint 16, el módulo pensional en el
Sprint 17, y la limitación de `dias_trabajados` (diferencia simple vs. convención comercial de 360 días)
en el Sprint 30. No queda ningún pendiente de este sprint sin sprint propio ya cerrado o en el índice.

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

**✅ Corrección aplicada (2026-08-01, verificado contra la respuesta del despacho,
`Preguntas-Para-Abogado-Respondidas.md` Sprint 4):** el despacho rechazó explícitamente la aplicación simultánea de
ambos topes: el único tope legal es del 50% acumulado sobre (honorarios fijos + cuota litis).
`HonorariosStrategy._validar_obligacion_honorarios()` ya no valida el tope individual del 30% sobre la
cuota litis sola (eliminado, junto con el parámetro `CUOTA_LITIS_INDIVIDUAL_PCT` del catálogo de
`parametro_service.py` — ya no tiene fundamento legal, se quedó sin uso). El mensaje de
`CuotaLitisExcedeTopeError` ahora cita textualmente "Honorarios Desproporcionados - Art. 35 Num. 4 Ley
1123/2007" al superar el 50% acumulado, y sigue bloqueando la liquidación (una de las dos vías que el
despacho autorizó explícitamente: "bloquear la liquidación o ajustar el excedente" — se mantuvo el
bloqueo, coherente con el patrón ya usado para el resto de topes duros del sistema, a diferencia de la
sanción de usura del Sprint 2 donde el despacho prohibió expresamente bloquear).
`README.md`/`docs/GUIA_USUARIO.md` actualizados. Suite completa en verde (619 passed, 1 skipped).
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

**Seguimiento:** la tabla histórica de UVT quedó completada en el Sprint 14 (serie 2006-2026, verificada
contra 3 fuentes independientes) — no queda ningún pendiente de este sprint sin resolver.

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
mantener tabla propia).

**✅ Corrección aplicada (2026-08-01, verificado contra la respuesta del despacho,
`Preguntas-Para-Abogado-Respondidas.md` Sprint 6):** el despacho confirmó que fines de semana + festivos NO bastan —
exige excluir también la vacancia judicial de fin de año (20 de diciembre a 11 de enero inclusive, 12 de
enero hábil salvo que caiga en fin de semana/festivo) y Semana Santa completa (lunes, martes y miércoles
santo, además del jueves/viernes santo que ya son festivos). `CalendarUtils.es_dia_habil()`
(`app/engine/time/calendar.py`) ahora también verifica la vacancia de fin de año
(`_en_vacancia_judicial_fin_de_anio`, chequeo directo de mes/día, sin necesidad de tabla) y la Semana Santa
extendida (`_vacancia_semana_santa`, derivada de "Jueves Santo" — festivo que la librería `holidays` ya
calcula por año — restando 1/2/3 días para obtener Miércoles/Martes/Lunes Santo, sin depender de una
librería nueva). Esto cambia el resultado de `dias_habiles_entre()`/`sumar_dias_habiles()` para cualquier
rango que cruce esas fechas — se actualizaron los tests existentes que cruzaban el cambio de año
(`tests/temporal/test_calendar.py`) y se reescribieron los de `tests/temporal/test_terminos.py` con fechas
fuera de esos rangos especiales (la máquina de estados de interrupción/suspensión/reanudación es agnóstica
a qué fechas exactas cuentan como hábiles; esas reglas ya se prueban directamente en `test_calendar.py`).
El modelador de términos (`EstadoTermino` + `iniciar_termino/dias_restantes/
esta_vencido/interrumpir/suspender/reanudar`) vive en `app/engine/temporal/terminos.py`. Suite completa en
verde (622 passed, 1 skipped). `docs/specifications/01_motor_temporal.md` actualizado. Code review del
sprint original encontró y corrigió: `interrumpir`/`reanudar` no validaban que `fecha` fuera posterior al
`checkpoint` vigente (permitía retroceder el reloj procesal silenciosamente) — las cuatro funciones
(`dias_restantes`/`interrumpir`/`suspender`/`reanudar`) comparten un guard único que rechaza fechas
anteriores al checkpoint.

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

**✅ Corrección aplicada (2026-08-01, verificado contra la respuesta del despacho,
`Preguntas-Para-Abogado-Respondidas.md` Sprint 7):** el despacho confirmó los 3 plazos cambiarios (COINCIDEN
exactamente: `CAMBIARIA_DIRECTA=36`, `CAMBIARIA_REGRESO_TENEDOR=12`,
`CAMBIARIA_REGRESO_ENTRE_OBLIGADOS=6`, `prescripcion.py`), y además pidió precargar plazos adicionales de
caducidad/prescripción fijos: Cheques (6 meses), Enriquecimiento sin causa (1 año), Transporte (2 años),
Seguro (2 y 5 años — modelado como dos `tipo_proceso` distintos, `SEGURO_ORDINARIA`/`SEGURO_EXTRAORDINARIA`,
mismo criterio que los tres plazos cambiarios) e Impugnación de Actas Sociales (2 meses).
`PLAZOS_CADUCIDAD_MESES_CONOCIDOS` (`prescripcion.py`) ahora trae las 6 claves nuevas (además de la
Impugnación de ineficacia societaria ya existente), cada una con su entrada en
`CATALOGO_PARAMETROS` (`parametro_service.py`) y sembrada automáticamente por
`scripts/migrate_parametros_legales.py` (lee directamente del diccionario, sin necesidad de tocar el
script). Suite completa en verde (628 passed, 1 skipped).
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

**Seguimiento:** el motor en sí (cálculo puro) está completo y probado, pero **sigue sin conectarse al
flujo real de liquidación** — cualquier liquidación de cualquier área hoy incluye obligaciones prescritas
o caducadas sin advertirlo ni excluirlas. Ese gap de integración (no de cálculo) ya está trackeado como
🔵 Sprint 42.

**Definición de Hecho:**
- Tests con los plazos de cada tipo de acción mencionados en el PDF.
- Test específico de prescripción parcial en una obligación recurrente tipo `CHILD_SUPPORT` con cuotas de
  hace más de 5 años mezcladas con cuotas recientes.
- Suite completa en verde.

---

## Sprint 8 — Conectar indexación IPC al área Civil/Familia 🔵 Bloqueado — pendiente de confirmación

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

**⚠️ Parcial (verificado contra la respuesta del despacho, `Preguntas-Para-Abogado-Respondidas.md`
Sprint 8, 2026-08-01):** el despacho calificó EXACTAMENTE las aproximaciones (b) y (c) de arriba como
"jurídicamente inválida... será objetada por un juez", y exige IPC **mensual** del DANE con interpolación
lineal de días dentro del mes, prohibiendo expresamente proyectar el año en curso con el IPC del año
anterior. Se buscó la serie mensual real por web (2026-08-01) y no se consiguió completa ni verificable en
un formato transcribible con confianza (solo variaciones % desde 2011, no el índice completo desde 1967) —
en vez de inventar valores, se agregó una pregunta de seguimiento en `Preguntas-Para-Abogado-Abiertas.md`
("Sprint 8 (seguimiento)") pidiéndole al despacho la fuente/tabla real.

Mientras tanto, se construyó y probó la parte de **código** de la corrección:
`historical_index.get_ipc_mensual_for_month`/`get_ipc_interpolado_mensual_for_date` (nuevas) implementan
exactamente la interpolación lineal de días entre el cierre del mes anterior y el del mes de la fecha, tal
como exige el despacho — pero la tabla de datos (`_IPC_MENSUAL`) queda deliberadamente vacía y lanza
`IPCMensualNoDisponibleError` para cualquier mes mientras no llegue la fuente real (mismo patrón que UVT
antes del Sprint 14). **`CivilFamiliaStrategy._evento_indexacion` (`area_strategy.py`) sigue usando
`get_ipc_interpolado_for_date` (la interpolación anual, todavía jurídicamente inválida)** — conectar la
función mensual ya lista requiere los datos reales primero; cambiar el wiring sin datos rompería toda
indexación IPC existente en la app (bloquearía cualquier liquidación con `aplica_indexacion_ipc=True`) en
vez de corregirla. Este motor es la base del Sprint 20 ("Suma Única") y de cualquier indexación IPC ya
calculada en Civil/Familia, así que hereda el mismo defecto en cualquier liquidación real ya generada
(incluyendo, potencialmente, la que motivó el Sprint 41) hasta que se complete la conexión.
`docs/specifications/03_motor_indexacion.md` actualizado. Suite completa en verde (633 passed, 1 skipped).

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

**Respuesta de seguimiento recibida (2026-08-13):** el despacho confirmó la metodología exacta para el IPC
mensual (Número Índice, no variación %; doble base diciembre 2008=100 / diciembre 2018=100 con Factor de
Enlace en el mes de traslape), pero **todavía no aportó los valores reales**. Sigue bloqueado por el mismo
motivo de siempre — falta el dato, no la decisión — y se agregó una nueva pregunta de seguimiento en
`Preguntas-Para-Abogado-Abiertas.md` ("Sprint 8 (seguimiento 2)") pidiendo la tabla real en las dos bases.
Detalle completo en `Preguntas-Para-Abogado-Respondidas.md`, sección Sprint 8. El usuario reportó además
(2026-08-13) que la página 62 del PDF de requisitos ("REGLAS DE CÁLCULO BASTIUM") no trae los datos de IPC
por año que esperaba encontrar ahí — verificado leyendo esa página directamente: **solo trae variación %
anual 1967-2025**, la misma fuente ya transcrita en `_IPC_VARIACION_ANUAL`, no el índice mensual con doble
base que ahora pide el despacho. No es un bug de lectura del PDF: es el mismo hueco de dato que este sprint
ya documentaba, confirmado de nuevo desde otra fuente. Adicionalmente, `areas_parametro.py` solo etiqueta
`IPC_INDICE_ACUMULADO` para las áreas Civil/Familia y Tributario (`["CIVIL_FAMILIA", "TRIBUTARIO"]`) — si
el usuario filtra la pantalla de Parámetros por otra área (Comercial, Laboral, Sancionatorio, Honorarios),
la fila de IPC no aparece en absoluto, lo cual puede ser otra causa de la misma percepción de "no aparecen
los datos de IPC". Esa lista de áreas debe revisarse junto con el Sprint 43 cuando se activen las 5 áreas
restantes.

**Actualización (2026-08-19): se encontró la fuente real del DANE — ver Sprint 80.** El despacho envió,
junto a un lote de plantillas de referencia, `docs/Archivos de referencia abogado/_markdown/Historico
IPC.md`, que trae el índice IPC **mensual** real (no variación %) de enero de 2003 a abril de 2026, base
diciembre 2018 = 100, fuente DANE — exactamente el dato que faltaba para poblar `_IPC_MENSUAL`
(`historical_index.py`) y conectar `get_ipc_interpolado_mensual_for_date` en
`CivilFamiliaStrategy._evento_indexacion`, el wiring que este sprint dejó pendiente. Se cambia el estado de
🔴 (bug confirmado, sin corregir, bloqueado por falta total de dato) a 🔵 (bloqueado, pendiente de
confirmación) porque ya no falta el dato — faltan dos detalles de alcance antes de conectar el wiring: (a)
la tabla viene en una sola base ya enlazada por el DANE, no en las dos bases separadas con Factor de Enlace
que pidió el despacho en su respuesta anterior; y (b) no cubre fechas anteriores a 2003. Ver Sprint 80 para
el plan de implementación completo, y la pregunta nueva "Sprint 80" en `Preguntas-Para-Abogado-Abiertas.md`
para esos dos detalles.

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

**Estado confirmado (2026-08-06):** implementado — esta sección nunca tuvo una nota de cierre explícita,
pero la implementación está confirmada por evidencia directa: `app/reports/pdf.py` y `app/reports/word.py`
existen con la generación real, los botones "Exportar a PDF"/"Exportar a Word" están cableados en
`ResultadoLiquidacionView` (`app/views/liquidaciones.py`), y el Sprint 26 (2026-08-04) movió exactamente
esas dos funciones de exportación a `QThreadPool` — no habría tenido nada que mover a un hilo si no
existieran y funcionaran ya.

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

**Nota (2026-08-01):** el Sprint 11b llegó después como el Sprint 15 (ver abajo) — su verificación contra
la respuesta del despacho está documentada ahí, no aquí.

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

**✅ Corrección aplicada (2026-08-01, verificado contra la respuesta del despacho,
`Preguntas-Para-Abogado-Respondidas.md` Sprint 12):** el despacho rechazó explícitamente la decisión (c) de arriba y
exigió convertir a pesos de forma **dinámica**, con la TRM de la fecha de **cada** pago/abono (consumiendo
la API de la Superintendencia Financiera), eliminando "la TRM congelada al inicio".

Se agregó `SFCTRMProvider` (`app/engine/currency/trm_provider.py`), cliente HTTP (via `urllib` de la
librería estándar, sin dependencia nueva) del dataset abierto de datos.gov.co que espeja el servicio
oficial de la SFC. `ComercialStrategy` ahora acepta `trm_provider` inyectable (default `SFCTRMProvider()`
en producción) y resuelve la TRM **por evento**: el capital con la TRM de `fecha_origen`, y — el cambio
central — **cada abono con la TRM de su propia fecha de pago** (`_monto_abono_en_pesos`, cableado a través
de un nuevo parámetro `monto_abono_fn` en `_liquidar_por_obligacion`, también usado por la liquidación
sombra de la sanción de usura del Sprint 2 para mantener consistencia).

Decisión de diseño documentada (no confirmada expresamente por el despacho, tomada con criterio propio
dado que la instrucción no especificaba la mecánica exacta): `trm_aplicable`/`trm_fecha_referencia` dejaron
de ser obligatorios pero se **conservan como anulación manual opcional** — si el abogado los diligencia,
esa obligación usa ese valor fijo para todo (capital y abonos), sin consultar la API; útil sin conexión a
internet o para reproducir liquidaciones anteriores a este sprint. Es la única TRM "congelada" que
sobrevive, y es una elección explícita por obligación, no el comportamiento por defecto. Si la API no
responde, `TRMNoDisponibleError` (nueva) se propaga a la GUI como advertencia "TRM no disponible" — no
aproxima ni usa un valor viejo.

`README.md`/`docs/GUIA_USUARIO.md` actualizados. Suite completa en verde (637 passed, 1 skipped) — los
tests de red usan un `TRMProvider` de prueba inyectado (nunca hacen llamadas HTTP reales).

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

**Respuesta recibida sobre la guía de uso de Parámetros (2026-08-13):** el despacho confirmó que SÍ hace
falta una guía corta, dirigida a un perfil "Abogado Junior / Estudiante de Consultorio Jurídico", en
lenguaje de "campos de hecho" con enfoque pedagógico para traducir el título ejecutivo al software.
`docs/GUIA_USUARIO.md` ya documenta la pantalla de Parámetros (Sprints 57/58/68) pero en tono general de
manual, no con ese enfoque pedagógico específico — pendiente ajustar o agregar una sección dedicada. Ver
`Preguntas-Para-Abogado-Respondidas.md`, sección Sprint 13.

**Cierre del ajuste de tono pedagógico (2026-08-14):** Completado — la sección 5.14 de
`docs/GUIA_USUARIO.md` ahora abre con una nota dirigida explícitamente al Abogado Junior / Estudiante de
Consultorio Jurídico, agrega un bloque "Cómo traducir un 'hecho del caso' a una fila de esta tabla" con
ejemplos reales de "Topes legales" y "Plazos de prescripción y caducidad" (incluido el ejemplo completo de
prescripción ejecutiva: hecho del caso → fila "Plazo de prescripción de la acción ejecutiva (meses)") y
una advertencia explícita de responsabilidad disciplinaria por un valor mal cargado. No se removió
contenido factual existente (columnas Área/Unidad/Vigente hasta de los Sprints 57/58/63 se conservan).
Suite completa en verde (1162 passed).

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

**✅ Corrección aplicada (2026-08-01, verificado contra la respuesta del despacho,
`Preguntas-Para-Abogado-Respondidas.md` Sprint 15):** el despacho confirmó dos puntos que YA COINCIDÍAN con el código:
el orden de imputación (Sanciones → Intereses → Impuesto) y el piso de 10 UVT
(`app/engine/tax/sanciones.py`). La regla especial de concurrencia para deudas con más de 3 años de mora
(Art. 867-1 E.T., Sentencia C-549/1993) sí faltaba — se agregó `app/engine/tax/actualizacion_867_1.py`:
- **Impuesto** (`IMPUESTO_A_CARGO`): conserva el interés E.T. 635 (sin cambios) y además se indexa por
  IPC, topando la suma (interés + indexación) al interés que produciría la tasa de usura **plena** (sin el
  descuento de 2 puntos del art. 635) sobre el mismo capital y período — verificado contra el ejemplo
  numérico exacto que aportó el despacho (impuesto $100.000.000, mora 2018-05-10 a 2023-05-10: interés
  $123.160.595,20, indexación sin topar $32.814.627,80, recortada a $7.773.307,41 para no superar el techo
  de $130.933.902,61).
- **Sanciones** (`SANCION_*`): no acumulan interés moratorio (nunca lo hicieron, en realidad — las
  sanciones caen en el bucket `indexation` de `LiquidationCore`, que nunca alimentó el cómputo de interés
  diario salvo bajo Suma Única; el "caso especial" del despacho ya estaba garantizado por la arquitectura
  existente) y se reemplazan íntegramente por la indexación IPC cuando la mora supera 3 años.

Implementar esto exigió migrar `TributarioStrategy` al mismo patrón de liquidación por obligación aislada
que Comercial/CivilFamilia usan desde el Sprint 21 (`_liquidar_por_obligacion`) — es la única forma de
darle 0% de interés a una sanción mientras el impuesto sigue acumulando la tasa E.T. 635, ya que
`LiquidationCore` solo soporta un `PendingDebt`/tasa por instancia. **Efecto secundario documentado**: un
abono ya no se imputa automáticamente contra el saldo combinado del expediente (sanciones primero,
impuesto después) — cada abono debe indicar, vía `obligacion_id`, cuál obligación paga, igual que en las
demás áreas desde el Sprint 21. `README.md`/`docs/GUIA_USUARIO.md` actualizados. Suite completa en verde
(647 passed, 1 skipped).

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

**✅ Corrección menor aplicada (2026-08-01, verificado contra la respuesta del despacho,
`Preguntas-Para-Abogado-Respondidas.md` Sprint 16):** las tablas de ARL (I=0.522%, II=1.044%, III=2.436%, IV=4.350%,
V=6.960%, `scripts/migrate_parametros_legales.py`) y de FSP (tramos 4-16/16-17/17-18/18-19/19-20/>20
SMMLV) YA COINCIDÍAN exactamente con lo confirmado por el despacho. Faltaba únicamente el tope legal del
8.7% para cualquier nivel de riesgo ARL (Ley 1562/2012) — se agregó `TOPE_ARL_PCT = Decimal("0.087")` en
`app/engine/labor/seguridad_social.py`, aplicado con `min()` sobre el porcentaje resuelto desde
`parametros_legales`, así que sigue rigiendo aunque alguien suba un nivel de riesgo por encima de ese tope
desde la pantalla de Parámetros (Sprint 13). Sin impacto numérico en los valores actuales (6.960% ya
estaba por debajo del tope). Suite completa en verde (648 passed, 1 skipped).

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

**✅ CORRECCIÓN URGENTE APLICADA (2026-08-01, verificado contra la respuesta del despacho,
`Preguntas-Para-Abogado-Respondidas.md` Sprint 17):** el despacho SÍ confirmó la fórmula, pero con una precisión que el
código había implementado mal: el piso de la tasa **inicial** (antes del bono) es **55%**, no 65%, y el
techo de esa misma tasa inicial es 65.5% — `calcular_tasa_reemplazo` (`app/engine/labor/ibl.py`) ahora
aplica `max(55, min(65.5, r_inicial))` **antes** de sumar el bono, y solo el techo final de 80% se aplica
después (el código viejo aplicaba un único clamp `max(65, min(80, r))` sobre el total ya con bono sumado,
mezclando ambas reglas). Además, el umbral de "semanas mínimas" para calcular el exceso ya no está fijo en
1300 para cualquier año: `semanas_minimas_requeridas(anio_causacion)` (nueva) reconstruye el
escalonamiento real de la Ley 797/2003 — 1000 semanas antes de 2005, 1050 en 2005, +25/año desde 2006
hasta llegar a 1300 en 2015, fija en 1300 desde entonces. `calcular_tasa_reemplazo` ahora exige
`anio_causacion` como parámetro obligatorio (cambio de firma). Verificado exactamente contra el caso de
prueba QA que trajo el despacho (IBL=$800.000, SMMLV=$400.000, semanas=1.664, año 2006, mínimo real de
1.075 semanas): tasa final = 80% (antes de la corrección, con el mínimo mal fijo en 1.300, el código
calculaba 75%). Módulo pensional sigue sin conectar a ninguna estrategia/GUI (ver Sprint 3), así que esta
corrección no tiene impacto en liquidaciones reales todavía, pero sí en cualquier uso directo del motor.
Suite completa en verde (653 passed, 1 skipped).

---

## Sprint 18 — Costas judiciales con tabla real de rangos (Acuerdo PSAA16-10554) ✅ Completado

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

**Estado:** Implementado (2026-07-27/28, ver rango de commits desde `d7faacf` hasta `11c0d60`) — ver
`docs/superpowers/specs/2026-07-26-sprint18-costas-judiciales-design.md` y
`docs/superpowers/plans/2026-07-26-sprint18-costas-judiciales.md`. La cita "PCSJA20-11556" del PDF de
requisitos de BASTIUM no corresponde a ningún acuerdo real localizable; el acuerdo vigente que sí regula
la materia es el **Acuerdo PSAA16-10554** del 5 de agosto de 2016 del Consejo Superior de la Judicatura,
identificado y verificado directamente contra la fuente oficial (ramajudicial.gov.co) durante este sprint.

Se implementaron las 18 categorías de `TipoProceso` del art. 5° del acuerdo
(`app/engine/costs/agencias_en_derecho.py`) — el alcance completo, no solo el subconjunto de
"declarativos" que se había considerado como opción más pequeña durante el brainstorming previo; el
usuario eligió el alcance completo. El cálculo automático quedó conectado en `CivilFamiliaStrategy`,
`ComercialStrategy`, `LaboralStrategy`, `SancionatorioStrategy` y `HonorariosStrategy`.
`TributarioStrategy` queda intencionalmente excluida: sus "sanciones" son sanciones administrativas de la
DIAN, no agencias en derecho judiciales — un dominio legal distinto. `costas_pct_manual` (Sprint 4) se
conserva como override siempre disponible y con prioridad máxima sobre el cálculo automático (ver
`_evento_costas_procesales` en `app/services/area_strategy.py`) — el comportamiento de quien ya lo usaba
no cambia.

Limitaciones conocidas, documentadas en vez de omitidas silenciosamente:
- `LIQUIDACION_SOCIEDAD_CONYUGAL_EXCEPCIONES` no tiene tarifa registrada para segunda instancia (el
  acuerdo no da un rango distinto del de la categoría base `LIQUIDACION_SOCIEDAD_CONYUGAL` para ese
  resultado); un caso que arranca como "excepciones" en primera instancia debe registrarse bajo la
  categoría base si/cuando llega a segunda instancia.
- Todavía no existen campos de formulario en la GUI para `costas_tipo_proceso`/`costas_instancia` — este
  sprint entregó el motor de cálculo y su wiring en las estrategias de liquidación, no una actualización
  de pantallas (solo existen las columnas de base de datos y el motor).
- ~~Por la misma razón anterior, `TarifaNoDisponibleError` tampoco está capturada todavía en el manejo de
  excepciones de la GUI.~~ Corregido junto con la corrección de este sprint (2026-08-01): ahora se captura
  en `expediente_detalle.py`, junto con la nueva `CostasFueraDeRangoError`.
- No hay validación que impida fijar `costas_tipo_proceso`/`costas_instancia` en más de una obligación
  del mismo expediente (contaría las costas doble) ni en un expediente Civil/Familia o Comercial compuesto
  solo de obligaciones `RECURRENTE` (no generaría costas sin avisar, ni siquiera vía `costas_pct_manual`
  manual): en ambas áreas solo las obligaciones `PUNTUAL` quedan conectadas a
  `_evento_costas_procesales`. Son huecos preexistentes de validación de entradas, comunes a todas las
  áreas, no introducidos por este sprint — queda pendiente una revisión de validaciones a futuro.

Preguntas abiertas para el despacho sobre las aproximaciones de implementación (ponderación inversa,
tramo de mayor cuantía sin techo, `fecha_origen` como aproximación de la fecha de radicación, y la base de
costas en Laboral frente al Art. 65 CST) quedaron registradas en `Preguntas-Para-Abogado-Abiertas.md`,
sección Sprint 18. `README.md` y `docs/GUIA_USUARIO.md` actualizados. Suite completa en verde.

**⚠️ Parcial (2026-08-01, verificado contra la respuesta del despacho,
`Preguntas-Para-Abogado-Abiertas.md` Sprint 18):** la tabla de 3 rangos simples que aportó el despacho (Mínima ≤40
SMMLV → 0%-10%, Menor 40-150 SMMLV → 3%-7%, Mayor >150 SMMLV → 1%-5%) **no coincide** numéricamente con la
tabla granular ya implementada (Acuerdo PSAA16-10554, `agencias_en_derecho.py`, ~18 tipos de proceso ×
instancia, cada uno con su propio rango distinto). En vez de asumir cuál de las dos manda, se implementó
únicamente lo inequívoco de la instrucción del despacho — "el sistema debe restringir el input del
usuario... lanzar un error de validación" — como una **validación nueva del porcentaje manual**
(`costas_pct_manual`), sin tocar la tabla granular del cálculo automático:
`validar_costas_pct_manual`/`RANGO_COSTAS_MANUAL_POR_TIER` (`agencias_en_derecho.py`) resuelve el tier de
cuantía (mínima/menor/mayor, mismo `resolver_cuantia_tier` que ya usaba el cálculo automático) y rechaza
—no trunca— un `costas_pct_manual` fuera del rango simple del despacho, lanzando `CostasFueraDeRangoError`
(nueva), ahora capturada en la GUI (`expediente_detalle.py`) igual que las demás excepciones de dominio.
Se agregó una pregunta de seguimiento en `Preguntas-Para-Abogado-Abiertas.md` (sección "Sprint 18 (seguimiento)")
preguntando explícitamente si la tabla simple reemplaza la granular o solo acota el valor manual — no
asumir ninguna de las dos sin confirmación. `docs/GUIA_USUARIO.md` actualizado (nueva sección 7.6.1).
Suite completa en verde (655 passed, 1 skipped).

**Respuesta de seguimiento recibida (2026-08-13):** el despacho confirmó opción (b) — la tabla simple es un
"Hard Cap" solo para el input manual; la tabla granular (PSAA16-10554) sigue gobernando el cálculo
automático, tal como ya está implementado, sin cambios de código necesarios por este punto. Trajo además la
lógica de ultraactividad CPC→CGP (Art. 624 CGP) todavía no implementada, y citó el acuerdo como
"PCSJA20-11556" — se agregó una nueva pregunta de seguimiento en `Preguntas-Para-Abogado-Abiertas.md`
("Sprint 18 (seguimiento 2)") para confirmar si es el mismo acuerdo que el PSAA16-10554 ya verificado o uno
distinto que actualiza la tabla granular. Ver el detalle completo en
`Preguntas-Para-Abogado-Respondidas.md`, sección Sprint 18. Pendiente de programar: la ultraactividad
CPC→CGP sobre la fecha de la providencia.

**Cierre de implementación de la ultraactividad CPC→CGP (2026-08-14):** Completado, vía
`superpowers:subagent-driven-development`. Campo nuevo, opcional, `Obligacion.fecha_providencia_costas:
date | None` (+ migración `scripts/migrate_fecha_providencia_costas.py`, mismo patrón idempotente que
`costas_tipo_proceso`/`costas_instancia`). Nueva excepción `TarifaPreCGPNoDisponibleError`
(`app/core/exceptions.py`). Nueva validación `validar_ultraactividad_cgp()` en
`agencias_en_derecho.py` (constante `FECHA_VIGENCIA_CGP = date(2016, 1, 1)`, citando Art. 627 CGP): si
`fecha_providencia_costas` está definida y es anterior al 1° de enero de 2016, lanza la excepción nueva en
vez de aproximar — **no existe ninguna tabla de tarifas pre-CGP (era CPC) en el proyecto**, mismo criterio
de "no inventar cifras sin fuente" de los Sprints 5/7/18 original. Completamente retrocompatible: si el
campo es `None` o la fecha es posterior a 2016-01-01, el comportamiento es idéntico al de antes de este
sprint (verificado con tests de regresión). Wiring a través del único punto compartido de cálculo de
costas (`_evento_costas_procesales`, `app/services/area_strategy.py`, usado por las 5 áreas que manejan
costas), y capturada en la GUI (`expediente_detalle.py`) junto con `TarifaNoDisponibleError`/
`CostasFueraDeRangoError`. Gradualidad por distrito judicial explícitamente NO modelada (el despacho la
mencionó sin dar fechas por distrito) — se usa solo la fecha general de vigencia nacional, documentado como
limitación conocida. No se agregó campo de captura en el formulario de UI (alcance excluido a propósito,
mismo criterio que `costas_tipo_proceso`/`costas_instancia` en su momento). Suite completa en verde (1162
tras el merge final del lote).

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

## Sprint 20 — Indexación sobre capital ya indexado (algoritmo "Suma Única") ✅ Completado

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

**Estado:** Implementado (2026-07-31) — ver
`docs/superpowers/plans/2026-07-31-sprint20-suma-unica.md` y
`docs/superpowers/specs/2026-07-31-sprint20-suma-unica-design.md`. Decisiones tomadas con el usuario
durante el brainstorming previo: (a) se migra al algoritmo exacto del PDF, no se deja como simplificación
del MVP; (b) `reconstruir_liquidacion()` (Sprint 9) deserializa un snapshot congelado y nunca recalcula, así
que el riesgo de retrocompatibilidad que anticipaba este sprint no aplicaba — no se necesitó ningún guard
especial para liquidaciones ya auditadas; (c) flag explícito por obligación
(`Obligacion.interes_sobre_capital_indexado`, default `False`), no un reemplazo global ni un parámetro a
nivel de expediente — mismo patrón que `aplica_indexacion_ipc`; (d) diseño original: un expediente que
mezclara obligaciones indexadas con criterios de interés distintos lanzaba `ValueError`, porque
`CivilFamiliaStrategy` liquidaba todo el expediente sobre un único `PendingDebt` compartido y mezclar
criterios en ese saldo era ambiguo. Hallazgo no anticipado en la redacción original de este sprint: el
bucket `PendingDebt.indexation` está compartido con `SANCION_TRIBUTARIA` (Tributario) — se descartó
separar el modelo de dominio porque el flag se resuelve por llamada a `liquidar()` y `TributarioStrategy`
nunca lo activa, así que las sanciones tributarias nunca entran a la base de interés aunque compartan el
bucket.

**Ajuste post-implementación (2026-07-31, al integrar con Sprint 21):** el Sprint 21 (múltiples tasas
simultáneas) se completó y mergeó a `main` mientras este sprint se trabajaba en un worktree aislado, y
cambió `CivilFamiliaStrategy` para liquidar **cada obligación en su propio `LiquidationCore`** (`PendingDebt`
independiente, ver `_liquidar_por_obligacion`/`_fusionar_resultados`) en vez de un único saldo compartido
por expediente. Eso volvió obsoleto el punto (d): ya no hay un saldo compartido que mezclar, así que
`_resolver_suma_unica` pasó a resolverse **por obligación** (`aplica_indexacion_ipc and
interes_sobre_capital_indexado`), sin validación de consistencia entre obligaciones del mismo expediente —
un expediente puede mezclar libremente obligaciones con y sin Suma Única, cada una liquida con su propio
criterio, y `_fusionar_resultados` suma los saldos individuales. El `ValueError` de "mismo criterio de
interés" se eliminó junto con el test que lo cubría.

**Definición de Hecho:**
- Test que reproduce el ejemplo numérico exacto del PDF (pág. 69: capital $50.000.000 de 2010 a 2025,
  indexado y luego con interés) y verifica el resultado contra el cálculo manual.
- Test de que liquidaciones auditadas antes de este sprint se siguen reconstruyendo idénticas.
- Suite completa en verde.

---

## Sprint 21 — Múltiples tasas de interés simultáneas por expediente ✅ Completado

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

**Estado:** Implementado (2026-07-31, ver rango de commits desde `47ce9cd` hasta `f326e1e`) —
ver `docs/superpowers/specs/2026-07-31-sprint21-multiples-tasas-design.md` y
`docs/superpowers/plans/2026-07-31-sprint21-multiples-tasas.md`.

El fix real fue más profundo que "indexar `MemoryRateProvider` por obligación": `LiquidationCore`
mantiene un solo saldo agregado por instancia, así que dos obligaciones no pueden acumular interés a
tasas distintas simultáneamente dentro del mismo núcleo. La solución fue correr un `LiquidationCore`
independiente por obligación (cada uno con su propia tasa y solo sus propios abonos, vía el
`obligacion_id` que `Abono` ya tenía en la base de datos pero que el motor ignoraba) y fusionar los
historiales en una sola línea de tiempo consolidada — sin tocar `LiquidationCore`/`BalanceEngine`/
`AllocationEngine`.

Áreas migradas: `CivilFamiliaStrategy`, `ComercialStrategy`, `SancionatorioStrategy`,
`HonorariosStrategy`. `LaboralStrategy` no aplica (liquida un solo contrato por expediente por diseño).
`TributarioStrategy` no aplica (su tasa moratoria del E.T. art. 635 es una tasa legal automática, igual
para todas las obligaciones del expediente, no viene de `tasa_efectiva_anual`).

Cambio de comportamiento deliberado: los abonos ahora se imputan solo a la obligación a la que fueron
registrados (antes se aplicaban como bolsa única del expediente) — coincide con lo que la GUI ya exigía
al capturar un abono (selección obligatoria de una obligación primero) pero que el motor de liquidación
no honraba. No había ningún test que dependiera del comportamiento anterior.

`_construir_rate_provider_obligacion` sigue duplicado entre `CivilFamiliaStrategy`, `SancionatorioStrategy`
y `HonorariosStrategy` (mismo patrón de "un solo tramo plano por obligación") — deduplicarlo queda para el
Sprint 22, como ya anticipaba la nota de coordinación en ese sprint.

---

## Sprint 22 — Limpieza técnica acumulada ✅ Completado

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
4. **Misma duplicación en `_construir_rate_provider_obligacion`**: `CivilFamiliaStrategy`,
   `SancionatorioStrategy` y `HonorariosStrategy` repiten, casi byte a byte, el patrón de "un solo tramo
   de tasa plana desde la obligación hasta la fecha de corte" (el método ya toma una sola obligación, no
   una lista, desde que el Sprint 21 lo migró — ver su cierre más arriba). Resolver junto con el punto 3
   la próxima vez que se toque `area_strategy.py`. Detectado en code review del Sprint 4
   (`docs/superpowers/plans/2026-07-17-sprint4-sancionatorio-honorarios.md`, Task 5); actualizado tras el
   cierre del Sprint 21 (2026-07-31).
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

**Estado:** Implementado (2026-08-01). Los 5 puntos:

1. **`AllocationEngine` duplicado:** eliminado `app/engine/allocation/allocator.py` (código huérfano,
   `raise NotImplementedError`, nada lo importaba) junto con `app/domain/obligation/base.Obligation`
   (modelo de dominio que solo ese archivo huérfano usaba — no había nada que "justificara mantenerlo").
   Se retiró también la advertencia de deuda técnica correspondiente en
   `docs/specifications/04_motor_pagos.md`.
2. **Archivo vacío:** eliminado `app/engine/financial/allocation.py` (0 bytes, sin ningún import).
3. **`_eventos_de_obligacion` duplicado:** al revisar el código actual, la duplicación puntual detectada
   en el Sprint 2 entre `CivilFamiliaStrategy` y `ComercialStrategy` ya no existe — ambos métodos
   divergieron genuinamente con el Sprint 8 (indexación IPC) y el Sprint 19 (anatocismo comercial). Forzar
   una extracción compartida hoy generalizaría lógica de dominio que ya es distinta por diseño. Sin cambio
   de código en este punto.
4. **`_construir_rate_provider_obligacion` duplicado:** este sí seguía siendo real (Sancionatorio y
   Honorarios eran byte-idénticos; Civil/Familia el mismo patrón con una rama adicional). Extraído a
   `AreaStrategy._rate_provider_tasa_plana` (clase base, `app/services/area_strategy.py`).
5. **`ObligacionFormDialog.guardar()` god method:** reemplazadas las ramas `if/try/except` apiladas por
   `_parse_campos_<area>()` (uno por Sancionatorio/Honorarios/Comercial/Civil-Familia) que devuelven solo
   las claves que esa área sobreescribe sobre `_CAMPOS_AREA_POR_DEFECTO`, más un helper `_parse_decimales`
   para el patrón de parseo con mensaje de error compartido. Se mantuvo una sola construcción de
   `Obligacion(...)` en vez de duplicarla por área.

Suite completa verde tras cada paso (657 passed, 1 skipped, sin cambios de resultado numérico —
2 tests nuevos se agregaron para cubrir el caso de falla parcial en `_parse_decimales`, ver punto 5).

---

## Sprint 23 — Bugs críticos de integridad financiera y auditoría ✅ Completado

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

**Estado confirmado (2026-08-06):** implementado — ver plan dedicado
`docs/superpowers/plans/2026-08-01-sprint23-bugs-integridad-financiera.md` (7 tareas, todas cerradas).
Ambos bugs corregidos: `LiquidationItem`/`LiquidationResult` ahora exponen `saldo_a_favor`,
`_item_desde_dict` deserializa con `.get(..., default)` para `rate_source` y `saldo_a_favor` sin lanzar
`KeyError`, y se agregó una advertencia no bloqueante en la GUI al guardar un abono que genera sobrepago.
Confirmado además indirectamente por el Sprint 46, que depende de este sprint "ya completado" y usa el
campo `saldo_a_favor` como algo ya existente.

---

## Sprint 24 — Validación de datos: formularios de obligaciones y parámetros legales versionados ✅ Completado

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

**Cierre (2026-08-17, hallazgo al auditar el código antes de arrancar los Sprints 72/73/43/47):** este sprint
ya estaba completo en el código, solo nunca se marcó aquí. `ObligacionFormDialog._validar_rango`/
`_validar_concepto_no_vacio`/`_validar_fecha_no_posterior_a_corte` (`app/views/obligaciones.py`) y la
validación compartida de `parametro_service.agregar_valor`/`editar_valor` (rango, positividad, solapamiento
de tramos `TRAMO_CERRADO`, `vigente_hasta >= vigente_desde`) ya existían y ya tenían tests cubriendo
exactamente esta Definición de Hecho — probablemente entraron como efecto colateral de la integración final
de los Sprints 56-60 (ver el comentario "Revision final de integracion (Sprints 56-60)" en
`parametro_service.py`) y del Sprint 34 (que ya citaba "reutilizando las reglas del Sprint 24" en su propio
cierre, ver `CHANGELOG.md`). No se tocó código para cerrar este sprint, solo se confirmó y documentó.

---

## Sprint 25 — Rendimiento del motor de tasas, índices e historial ✅ Completado

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

**Cierre (fecha real de la implementación):**
- `MemoryRateProvider.get_rate`/`get_rate_source`: búsqueda binaria (`bisect`) sobre la lista de periodos, ya
  ordenada por `start_date`.
- `get_parametro`: cache con alcance de una sola liquidación (`cache_de_liquidacion`, `ContextVar`), activada
  en los 6 `liquidar()` de `AreaStrategy`. Nunca persiste entre liquidaciones -- no hay riesgo de servir un
  valor desactualizado tras un `agregar_valor` desde la GUI.
- Índices agregados: `ix_obligaciones_expediente_id`, `ix_audit_logs_expediente_id`, `ix_abonos_obligacion_id`,
  `ix_parametros_legales_clave`. Migración idempotente en `scripts/migrate_add_indices_rendimiento.py`
  (probada contra bases temporales, incluye manejo de tablas faltantes). **Pendiente:** aplicar a la
  `bastium.db` real del usuario -- `bastium.db` está en `.gitignore` y no existe en el worktree de
  implementación, así que este paso queda para ejecutarse manualmente
  (`python scripts/migrate_add_indices_rendimiento.py` desde el checkout principal) después de fusionar esta
  rama.
- Paginación de `expedientes.py`: evaluada y descartada por ahora -- el volumen actual no la justifica (ver
  "Alcance explícitamente excluido" del plan de implementación).
- Benchmark (`scripts/benchmark_motor_rendimiento.py`, obligación con 29 años de mora / 348 cuotas con
  indexación), medido antes y después de este sprint sobre el mismo commit base (`5931b97`) vs. el estado
  final de esta rama:
  - Mora larga: 0.034s -> 0.034s (esta ruta concreta ya era rápida en el "antes"; el costo dominante no es
    el scan lineal de `MemoryRateProvider` sino el propio recorrido día a día del motor)
  - Recurrente con indexación: 0.841s -> 0.325s (~2.6x más rápido, mejora atribuible al cache de
    `get_parametro`/`get_smlmv_for_year`/`get_ipc_for_date` dentro del loop de indexación por cuota)
- Suite completa en verde (700 passed, 1 skipped), sin cambios de resultado numérico.

---

## Sprint 26 — Responsividad de la interfaz: liquidar/exportar sin congelar la UI ✅ Completado

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

**Cierre de implementación (2026-08-04):** Completado. `estrategia.liquidar()` y la exportación a PDF/Word
ahora corren en `QThreadPool` (vía `TareaEnHilo`, un envoltorio reutilizable de `QRunnable` con señales en
`app/views/concurrency.py`) con un `QProgressDialog` indeterminado y el botón de acción deshabilitado
mientras la operación está en curso; cada tarea de fondo abre y cierra su propia sesión SQLAlchemy dentro
del mismo hilo, sin compartir sesiones entre hilos. El manejo de excepciones de dominio (ej.
`CuotaLitisExcedeTopeError`, `UVTNoDisponibleError`) se preservó igual que antes, ahora vía un slot
disparado por señal. Suite completa en verde (`pytest-qt` cubre el nuevo flujo). Pendiente: el smoke test
manual interactivo (mover/redimensionar la ventana mientras liquida un expediente grande) no se pudo
automatizar en el entorno de la sesión que implementó esto y queda para confirmación manual del usuario.
Dos notas menores de la revisión de calidad, no bloqueantes: el diccionario de despacho de excepciones en
`_on_liquidar_fallo` depende del orden de inserción en vez de un match exacto por tipo (seguro hoy porque
las 7 excepciones de dominio son hermanas directas de `Exception`, pero podría volverse frágil si la
jerarquía cambia); y el `QProgressDialog` no tiene botón de cancelar ni timeout si una liquidación
realmente se cuelga (mismo riesgo que ya existía con la UI congelada, no es una regresión nueva).

---

## Sprint 27 — Limpieza de dependencias no usadas y código muerto adicional ✅ Completado

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

**Hallazgos adicionales (auditoría 2026-08-01, tras el cierre del Sprint 22):**

4. Test parametrizado con la lista de parámetros vacía:
   `test_areas_no_implementadas_lanzan_error_claro_al_liquidar`
   (`tests/services/test_area_strategy.py:155-164`, `@pytest.mark.parametrize("area_name,strategy_cls", [])`)
   verificaba que las áreas *aún no implementadas* lanzaran `AreaNoImplementadaError` — quedó con la lista
   vacía desde que las 6 áreas fueron implementadas (la última, Tributario, en el Sprint 15). pytest lo
   reporta como `SKIPPED (got empty parameter set)` en cada corrida de la suite; no verifica nada. Detectado
   porque el cierre del Sprint 22 (2026-08-01) confirmó que este es el único `SKIPPED` de las 657 pruebas.
5. 14 archivos fuente de 0 bytes, todos con fecha de creación 2026-07-04/05 (scaffold inicial del proyecto,
   anterior al Sprint 1) y sin ningún import real en todo el repo (confirmado con grep exhaustivo) — mismo
   patrón que `app/engine/allocation/allocator.py` y `app/engine/financial/allocation.py`, ya eliminados en
   el Sprint 22:
   - `app/core/settings.py`, `app/core/types.py`, `app/core/__init_.py` (nombre con typo — falta un guion
     bajo; nunca funcionó como inicializador de paquete, y el proyecto ya usa paquetes de namespace
     implícitos en otras carpetas sin `__init__.py`, así que tampoco hace falta reemplazarlo por uno bien
     nombrado).
   - `app/engine/financial/balance.py`, `date_range.py`, `event.py`, `period.py`, `statement.py`,
     `timeline.py` (6 archivos — superados por `entry.py`/`ledger.py`/`rate.py` en la misma carpeta, que sí
     tienen contenido real y sí se usan).
   - `app/engine/payments/fifo.py`, `payment_distribution.py`.
   - `app/engine/reports/chart_builder.py` (no confundir con `app/reports/charts.py`, el módulo real del
     hallazgo 2 de este mismo sprint).
   - `app/engine/time/dates.py`, `period.py` (superados por `app/engine/time/calendar.py`, con contenido
     real y fecha de modificación reciente).
6. 6 archivos de test de 0 bytes, mismo patrón y fecha, reflejo directo de los del punto 5: `tests/engine/
   test_dates.py`, `test_event.py`, `test_period.py`, `test_timeline.py`, `tests/financial/test_balance.py`,
   `test_statement.py`. pytest los recolecta sin error (un módulo vacío no genera advertencia por sí solo),
   pero no ejercitan nada.
7. Dos archivos adicionales de 0 bytes con el mismo patrón pero **sin una decisión clara todavía**:
   `app/views/about.py` y `app/views/reportes.py`. A diferencia de `app/views/dashboard.py` (también vacío,
   pero explícitamente reclamado como funcionalidad pendiente por el Sprint 33), estos dos no aparecen en
   ningún otro sprint de este documento — no está claro si son scaffold abandonado (mismo tratamiento que
   el punto 5) o pantallas planeadas sin documentar todavía (ej. una vista "Acerca de", y una vista
   "Reportes" en la GUI separada de `app/reports/`, que ya genera PDF/Word pero no tiene pantalla propia).

**Decisión de diseño a tomar antes de codificar:**
- Para `nlp_extractor.py` y `charts.py`: decidir con el usuario si (a) se eliminan por completo (nadie los
  usa, no están en el roadmap de los Sprints 14-22), o (b) se conservan porque hay intención de conectarlos
  a futuro — si se conservan, al menos corregir el bug de `os.getcwd()` y documentar por qué siguen
  huérfanos.
- Para `parsers.py`: mismo criterio — eliminar si no hay intención de usarlo, o corregir el bug de formato
  si se piensa conectar a futuro (ej. para importar montos desde texto libre).
- Para los hallazgos 4, 5 y 6: no hay decisión que tomar — código y tests muertos sin ambigüedad, eliminar
  directamente.
- Para el hallazgo 7 (`about.py`/`reportes.py`): sí requiere decisión del usuario antes de tocarlos (eliminar
  como scaffold abandonado, o dejarlos como placeholder documentado de una pantalla futura — igual que se
  hizo con `dashboard.py` en el Sprint 33).

**Código nuevo a crear (según la decisión):**
- Quitar de `requirements.txt` los paquetes no usados que se decida no conservar.
- Eliminar o corregir `nlp_extractor.py`, `charts.py`, `parsers.py` según la decisión de diseño.
- Eliminar el test con parametrize vacío (punto 4) y los 14 archivos fuente + 6 de test de 0 bytes sin
  ambigüedad (puntos 5 y 6).
- Resolver `about.py`/`reportes.py` (punto 7) según la decisión del usuario.

**Definición de Hecho:**
- `requirements.txt` solo lista paquetes con al menos un import real en el código fuente.
- Ningún archivo huérfano queda sin una decisión explícita documentada (eliminado, o conservado con
  motivo).
- Cero pruebas `SKIPPED` por lista de parámetros vacía; la suite solo tiene skips con una razón vigente
  (si los hay).
- Suite completa en verde tras cualquier eliminación.

**Cierre de implementación (2026-08-04):** Completado. Decisiones tomadas: `nlp_extractor.py` y
`charts.py` se conservaron y se corrigieron sus bugs (`validate_and_fill` ya no bloquea leyendo stdin,
acepta un `prompt_fn` inyectable; `BastiumChartGenerator` usa `pathlib.Path` en vez de
`os.path.join(os.getcwd(), ...)`); `parsers.py` se conservó y `FinancialParser.parse_money` ahora detecta
formato US vs. colombiano en vez de asumir siempre colombiano; `about.py`/`reportes.py` quedaron
documentados como placeholders intencionales de pantallas futuras, igual que `dashboard.py`. Se eliminaron
sin ambigüedad el test con parametrize vacío, los 14 archivos fuente y 6 de test de 0 bytes, y los 7
paquetes sin uso de `requirements.txt` (`rich` y `matplotlib` se conservan porque `nlp_extractor.py`/
`charts.py` siguen usándolos). Cero pruebas `SKIPPED` por parámetros vacíos. Suite completa en verde.
Nota de seguimiento no bloqueante de la revisión de calidad: `FinancialParser.parse_money` interpreta
`,` siempre como separador decimal en su rama de "solo coma" (regla explícita de este sprint), así que un
formato US de miles sin decimales (ej. `"5,000"`) se interpretaría como `5.000` — caso límite plausible
pero hoy inalcanzable (`parsers.py` sigue sin ningún caller en `app/`), a revisar si `nlp_extractor.py`
llega a conectarse alguna vez a texto libre real.

---

## Sprint 28 — CI/CD, versionado, housekeeping de repositorio e higiene de tests ✅ Completado

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

**Cierre de implementación (2026-08-04):** Completado, alcance original y ampliado. Se agregó un pipeline
de CI (GitHub Actions, corre `pytest` en cada push/PR a `main`), `__version__` (0.1.0, primer tag de git
`v0.1.0`, local — no empujado al remoto), `BASTIUM_DB_PATH` configurable por variable de entorno, y un
`conftest.py` raíz en `tests/` que centraliza la fixture de sesión en memoria antes duplicada en 14
archivos. Las 3 ramas huérfanas del hallazgo 5 ya no existen en el repositorio (confirmado con
`git branch -a` antes de arrancar este sprint) — se limpiaron en un paso anterior no documentado, nada que
hacer ahí. El hallazgo 6 (test muerto con parametrize vacío) se resolvió en el Sprint 27, en paralelo.
Alcance ampliado: `CONTRIBUTING.md`, `SECURITY.md` (con aviso legal — BASTIUM es una herramienta de apoyo,
no sustituye la asesoría de un abogado colegiado), badges de CI/versión/licencia + aviso legal corto en
`README.md`, plantillas de Issues/PR, y `CHANGELOG.md` (el badge de licencia queda "por definir" hasta que
cierre el Sprint 38). Suite completa en verde. Nota de seguimiento no bloqueante de la revisión de
calidad: `tests/services/test_area_strategy.py` quedó fuera de la migración al `conftest.py` raíz (fuera
de alcance de este sprint) y sigue con el bloque de fixture duplicado — limpieza cosmética menor para un
sprint de housekeeping futuro, no afecta el comportamiento de los tests. El `ruff check .` del repo
completo sigue mostrando ~400 errores preexistentes (no introducidos por este sprint) — deliberadamente
no se agregó como paso de CI porque haría fallar la primera corrida sin culpa de este sprint; ver
🔴 Sprint 48.

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

## Sprint 30 — Verificación de reglas de dominio con posible error de un día ✅ Completado

**Prioridad sugerida:** ~~Media~~ **Alta (actualizado 2026-08-01)** — la confirmación jurídica que este
sprint pedía como bloqueante ya llegó (ver bloque de abajo); pasa de "pendiente de confirmar" a "bug
confirmado, pendiente de codificar".

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

**⚠️ Confirmación jurídica recibida (`Preguntas-Para-Abogado-Respondidas.md`, secciones Sprint 30 y Sprint 3,
2026-08-01) — ambos puntos verificados contra el código real, siguen sin corregir:**
1. **Punto 1 (prescripción, CONFIRMADO como bug):** el despacho contestó que "un año" NO son 365 días
   matemáticos, sino fecha-a-fecha estricta de calendario
   (`Fecha_Vencimiento = Fecha_Notificacion.AddYears(1)`, con ajuste a 28-feb si no existe 29-feb, y
   desplazamiento al siguiente día hábil si la fecha cae en día no hábil). `fecha_interrupcion_efectiva`
   (`app/engine/temporal/prescripcion.py:106`) sigue usando literalmente
   `(fecha_notificacion - fecha_radicacion).days <= 365` — el bug original, sin corregir. Lo notable: la
   infraestructura correcta ya existe en el mismo módulo (`CalendarUtils.vencimiento_calendario`,
   `app/engine/time/calendar.py:70-85`, que sí suma años/meses con tope de fin de mes y corrimiento a día
   hábil, y que `calcular_prescripcion` — otra función del mismo archivo — sí usa) pero nunca se conectó a
   `fecha_interrupcion_efectiva`. Es la corrección más barata de todo este lote: reutilizar una función que
   ya existe y ya está probada.
2. **Punto 2 (conteo inclusivo, CONFIRMADO pero con matiz — no es un simple "+1" global):** el despacho
   confirmó conteo inclusivo (`Dias = (Fin - Inicio) + 1`), pero con dos bases distintas según el rubro, NO
   una regla única: para prestaciones sociales (cesantías/prima) se usa año comercial de 360 días
   (meses de 30 días); para densidad de semanas pensional (Sentencia SL138-2024) se usan días calendario
   reales (365/366), sin la ficción de 30 días — este segundo caso ya se abrió como corrección aparte en el
   Sprint 17 de arriba (semanas mínimas por año de causación), y comparte la misma causa raíz de "conteo no
   inclusivo" que aquí. `LaboralStrategy.liquidar` sigue usando resta simple sin sumar 1 en ningún punto
   revisado.

**Código nuevo a crear (confirmado — ya no es condicional a "si se confirma"):**
- Cambiar `fecha_interrupcion_efectiva` para reutilizar `CalendarUtils.vencimiento_calendario` (o
  equivalente) en vez de `<= 365` días fijos.
- Cambiar el cómputo de días a inclusivo (`+1`), con la base correcta por rubro: 360 días (año comercial)
  para prestaciones sociales, calendario real (365/366) para densidad de semanas pensional — no una sola
  convención global. Actualizar el test existente que hoy asume 365 para el caso de año completo.

**Alcance explícitamente excluido:**
- No tocar nada más de `LaborScheduler` ni de `prescripcion.py` — este sprint es exclusivamente la
  corrección puntual de estos dos cómputos, una vez confirmados.

**Riesgos / notas técnicas conocidas:**
- Si se corrige el punto 2, el cambio afecta el resultado numérico de todas las liquidaciones laborales
  existentes (aunque sea por un solo día) — requiere aviso explícito y posiblemente recalcular
  liquidaciones ya auditadas (interactúa con el Sprint 9).

**Definición de Hecho:**
- ~~Confirmación explícita... antes de tocar código~~ — **ya recibida** (ver bloque de arriba, 2026-08-01).
- Test que cubre explícitamente el caso bisiesto para prescripción, y el caso de contrato de año completo
  para `dias_trabajados` (con la base correcta: 360 comercial para prestaciones, calendario real para
  densidad pensional).
- Suite completa en verde.

**Cierre de implementación (2026-08-04):** Completado, ambos puntos corregidos según la confirmación
jurídica del despacho. `fecha_interrupcion_efectiva` (`app/engine/temporal/prescripcion.py`) ahora
reutiliza `CalendarUtils.vencimiento_calendario` en vez del proxy de `<= 365` días fijos, corrigiendo el
caso de años bisiestos. `LaboralStrategy.liquidar` (`app/services/area_strategy.py`) calcula los días de
prestaciones sociales con conteo inclusivo (`+1`) sobre base comercial de 360 días (12 meses de 30), usando
el nuevo `CalendarUtils.dias_comerciales_360`; la densidad de semanas pensional (base calendario real
365/366) queda fuera de este sprint, es responsabilidad del Sprint 17. Tests nuevos cubren el caso bisiesto
de prescripción y el contrato de año completo de prestaciones. **Importante:** este cambio afecta el monto
calculado de liquidaciones laborales y de prescripción de aquí en adelante; liquidaciones ya guardadas en
la base de datos no se recalculan automáticamente — quedó fuera de alcance de este sprint a propósito (ver
riesgo documentado arriba, interactúa con el Sprint 9 de auditoría). Suite completa en verde.

---

## Sprint 31 — Sistema de diseño visual: tema, color, tipografía e íconos en la GUI ✅ Completado

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

**Cierre de implementación (2026-08-06):** Completado. Ver
`docs/superpowers/plans/2026-08-06-sprint31-sistema-diseno-visual.md`. Paleta de marca centralizada en
`app/core/theme_colors.py` (burdeos/crema como ancla, con variantes hover/pressed/disabled), aplicada vía
`app/core/apariencia.py::aplicar_tema()` que carga `resources/theme.qss`, fija la `QPalette` base y
registra la tipografía `AncizarSans` (`app/assets/fonts.py`) como fuente por defecto de la aplicación. Se
descartó una librería de íconos de terceros (Feather/Lucide/Material Symbols) por falta de acceso a
internet del implementador y riesgo de licenciamiento a mitad de sprint — en su lugar, `resources/icons/`
tiene 7 SVG de línea hechos a mano (`home`, `back`, `settings`, `save`, `cancel`, `delete`, `export`),
más `resources/icon_app.svg` para el ícono de ventana, cargados vía el helper `app/views/icons.py`
(`icon(nombre)`/`icono_aplicacion()`). Se introdujo la convención `boton.setProperty("class", "primary"
/"destructive")` para botones de acción, reutilizada por los Sprints 32, 34 y 35. Implementado en un
worktree aislado y fusionado a `main` antes de los Sprints 32-35 (que dependen de sus íconos/tema),
ejecutados después en dos streams paralelos. Suite completa en verde tras el merge.

---

## Sprint 32 — Navegación: barra mejorada, breadcrumb y atajos de teclado ✅ Completado

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

**Cierre de implementación (2026-08-06):** Completado. Ver
`docs/superpowers/plans/2026-08-06-sprint32-navegacion-breadcrumb-atajos.md`. Se mantuvo el toolbar
superior enriquecido en vez de un sidebar completo (decisión de diseño explícita: 4-5 pantallas no lo
justifican todavía). Se agregó un breadcrumb contextual (`QLabel` en la barra de navegación,
`app/views/main_window.py`), atajos `Alt+Izquierda`/`Backspace` (Volver) y `Ctrl+Home` (Inicio) vía
`QShortcut`, estado visual activo/inactivo del botón "Parámetros" (misma convención `class="primary"`
del Sprint 31), y `Ctrl+S`/`Esc` en los 5 diálogos de formulario del proyecto (`Esc` no requirió código
nuevo, ya es comportamiento nativo de `QDialog`). Implementado junto con el Sprint 33 en un mismo stream
secuencial (32 antes de 33, ambos tocan `main_window.py`), y fusionado a `main` resolviendo manualmente
un conflicto de merge contra el otro stream paralelo (Sprint 35→34) en `app/views/expedientes.py` y
`resources/theme.qss` — ambos streams agregaron atajos `Ctrl+S`/estilos QSS de forma independiente sobre
los mismos archivos; se combinaron sin pérdida de ninguno de los dos lados. Suite completa en verde
(829 tests) tras el merge final.

---

## Sprint 33 — Pantalla de inicio real: dashboard con resumen y alertas ✅ Completado

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

**Cierre de implementación (2026-08-06):** Completado. Ver
`docs/superpowers/plans/2026-08-06-sprint33-dashboard-inicio.md`. `DashboardView`
(`app/views/dashboard.py`, antes vacío) muestra conteo de expedientes por área, alertas de plazos
próximos a vencer (reutilizando `calcular_prescripcion` del Sprint 7 con `TipoAccion.EJECUTIVA` como
heurística documentada — el modelo `Obligacion` no tiene un campo de tipo de acción procesal para un
mapeo área→tipo más preciso; pregunta abierta al despacho sobre esto en
[`Preguntas-Para-Abogado-Abiertas.md`](Preguntas-Para-Abogado-Abiertas.md#sprint-33--tipo-de-acción-procesal-para-las-alertas-de-prescripción-del-dashboard))
y actividad reciente (reutilizando `historial_de_expediente` del Sprint 9).
Registrada como pantalla de inicio en `MainWindow`, reemplazando al listado plano de expedientes como
primera pantalla (accesible con un clic vía "Ver todos los expedientes"). Carga de datos síncrona, sin
`TareaEnHilo` (Sprint 26): son consultas SQL livianas, sin comparación de costo con `liquidar()` o
exportar PDF/Word. Implementado junto con el Sprint 32 en el mismo stream (32 antes de 33, Sprint 33
releyó el `main_window.py` real post-Sprint-32 en vez de asumir su contenido, según indicaba su propio
plan). `docs/GUIA_USUARIO.md` actualizado para reflejar que la app ahora arranca en el Dashboard. Suite
completa en verde (829 tests) tras el merge final a `main`.

**Respuesta recibida (2026-08-13):** el despacho confirmó que "acción ejecutiva" NO es transversal y trajo
una tabla determinista completa de área → tipo de acción → plazo (Civil, Comercial, Laboral, Familia,
Sancionatorio, Honorarios, Administrativo/CPACA), con norma de respaldo para cada una — ver
`Preguntas-Para-Abogado-Respondidas.md`, sección Sprint 33. Pendiente de programar: (1) la tabla área→tipo
de acción→plazo en el motor (hoy `TipoAccion.EJECUTIVA` sigue siendo el único default en
`UniversalLiquidationService`), (2) el selector en UI que autocomplete el plazo al elegir área, y (3) la
lógica de ultraactividad CPC/Ley 794 de 2003 → CGP. Esto conecta directamente con el Sprint 61 (parámetros
de prescripción/caducidad sin wiring a pantallas reales), que ya identificó que la mayoría de estos plazos
existen en `parametros_legales` pero ningún botón los dispara.

---

## Sprint 34 — UX de formularios: agrupación, ayuda contextual y feedback en tiempo real ✅ Completado

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

**Cierre de implementación (2026-08-06):** Completado. Ver
`docs/superpowers/plans/2026-08-06-sprint34-ux-formularios.md`. `ObligacionFormDialog`
(`app/views/obligaciones.py`) reorganizado en 3 secciones colapsables (`QGroupBox` checkeable: "Datos
básicos", "Tasas e intereses", "Honorarios y costas") en vez de pestañas — un `QTabWidget` habría roto
las aserciones `isVisible()` ya existentes en la suite de tests, ya que solo mantiene visible la pestaña
activa. Tooltips legales agregados a los campos técnicos de `ObligacionFormDialog` y a los 6 campos de
`ExpedienteFormDialog`; feedback visual en tiempo real (borde rojo + ícono de advertencia,
`resources/icons/warning.svg`) conectado a las validaciones ya existentes del Sprint 24, sin duplicar
sus reglas; ícono informativo (`resources/icons/info.svg`) junto al campo de tasa con el tooltip exacto
del hallazgo ("Valor por defecto: interés civil legal, Art. 1617 C.C."). Validación en tiempo real
también agregada al radicado de `ExpedienteFormDialog`. Implementado junto con el Sprint 35 en un mismo
stream secuencial (35 antes de 34, ambos tocan `app/views/expedientes.py` — `ExpedienteFormDialog` y
`ExpedientesListView` viven en el mismo archivo). Suite completa en verde (829 tests) tras el merge
final a `main`.

---

## Sprint 35 — Búsqueda, filtros y estados vacíos en listados ✅ Completado

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

**Cierre de implementación (2026-08-06):** Completado. Ver
`docs/superpowers/plans/2026-08-06-sprint35-busqueda-filtros-listados.md`. `ExpedientesListView`
(`app/views/expedientes.py`) ganó un campo de búsqueda (radicado/demandante/demandado) y un filtro por
área, combinables, filtrados en memoria dentro de `refrescar()`; ordenamiento de columnas habilitado
(`setSortingEnabled(True)`); y un estado vacío explícito con mensaje y botón de acción contextual
("Crear expediente" si la base está realmente vacía, "Limpiar filtros" si hay expedientes pero ninguno
coincide). El campo "estado" mencionado en el hallazgo original no existe en el modelo `Expediente` — no
se inventó, el filtro real implementado es solo por área. Se corrigió un bug real que
`setSortingEnabled(True)` habría introducido de otro modo: el doble clic para abrir un expediente
indexaba una lista Python por posición de fila, que deja de ser válida en cuanto el usuario ordena una
columna; se corrigió guardando el id del expediente como `Qt.ItemDataRole.UserRole` en el
`QTableWidgetItem`, que sí se mueve junto con la fila al ordenar (con test de regresión dedicado). No se
agregó un ícono de búsqueda (fuera del set del Sprint 31, no justificado por la Definición de Hecho).
Implementado junto con el Sprint 34 en un mismo stream secuencial (35 antes de 34, mismo archivo
`expedientes.py`). Suite completa en verde (829 tests) tras el merge final a `main`.

---

## Sprint 36 — Feedback no bloqueante y jerarquía visual de botones ✅ Completado

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

**Cierre de implementación (2026-08-07):** Completado. Ver
`docs/superpowers/plans/2026-08-06-sprint36-feedback-jerarquia-botones.md`. Nuevo widget
`app/views/toast.py::mostrar_toast()` (`QLabel` hijo de la vista activa, auto-ocultado con
`QTimer.singleShot`, sin robar foco ni bloquear interacción) sustituye el único
`QMessageBox.information` de confirmación de bajo riesgo que existía en el código (exportación
completa en `liquidaciones.py`) — el resto de `QMessageBox` ya eran `.warning`/`.critical`/`.question`
(errores y confirmación destructiva de borrado de expediente) y se dejaron intactos. Clase QSS
`class="secondary"` agregada en `resources/theme.qss` junto a `primary`/`destructive` (Sprint 31) y
aplicada explícitamente a todo `QPushButton` que dependía del estilo implícito sin clase, en las 9
vistas con botones. El hallazgo de que "guardar una obligación" ya no mostraba ningún diálogo de éxito
(el flujo actual solo cierra el diálogo) se verificó leyendo el código antes de asumir cambios ahí.
Suite completa en verde (842 tests tras este sprint individual, 863 tras el merge final con los
Sprints 37/39/40).

---

## Sprint 37 — Comportamiento de ventana y accesibilidad de teclado ✅ Completado

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

**Cierre de implementación (2026-08-07):** Completado. Ver
`docs/superpowers/plans/2026-08-06-sprint37-ventana-teclado.md`. `MainWindow` persiste
tamaño/posición/maximizado entre sesiones vía `QSettings(IniFormat, UserScope, "BASTIUM", "BASTIUM")`
(`_restaurar_geometria()` en el arranque, `closeEvent()` al cerrar), con fallback a 1000x700 si no hay
valor guardado o `restoreGeometry()` lo rechaza — `main.py` ya no fija el tamaño incondicionalmente.
Nuevo fixture `autouse` `tests/conftest.py::_qsettings_aislado` redirige `QSettings.setPath()` a un
directorio temporal por test para no tocar el `.ini` real del sistema. Orden de tabulación fijado
explícitamente con `setTabOrder` encadenado en `ObligacionFormDialog` (post-reorganización del Sprint
34) y `ExpedienteFormDialog`. Se confirmó `setDefault(True)` en el botón "Guardar" de los 5 `QDialog`
de formulario del proyecto (no solo los 2 originalmente reportados: también `AbonoFormDialog`,
`EventoLaboralFormDialog`, `ParametroFormDialog`) y que `Esc` cierra los 5 sin guardar vía el
`reject()` nativo de Qt, sin interceptar en ninguno. Suite completa en verde (863 tests tras el merge
final). Merge con el Sprint 39 tuvo un conflicto textual en `tests/views/test_obligaciones.py` (git
alineó por coincidencia dos tests no relacionados de distinto sprint que compartían líneas idénticas)
resuelto reconstruyendo ambos tests completos por separado.

---

## Sprint 38 — Elegir licencia de código abierto y publicar `LICENSE` ✅ Completado

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
- El PDF fuente (`REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, en `docs/`) y cualquier
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

**Cierre de implementación (2026-08-07):** Completado. Decisión del usuario (2026-08-06): **Apache
License 2.0**. Ver `docs/superpowers/plans/2026-08-06-sprint38-licencia-apache.md`. Archivo `LICENSE`
publicado en la raíz con el texto oficial completo, titular de copyright
"Jose Miguel Silva Diaz (BASTIUM)" (inferido de `git config user.name` y del usuario de GitHub
`JoseMsD21` referenciado en `README.md` — pendiente que el usuario lo confirme o ajuste si prefiere otro
nombre legal/razón social). Badge de licencia en `README.md` y línea de licenciamiento de
`CONTRIBUTING.md` actualizados para apuntar a Apache 2.0. Trabajo puramente documental, sin cambios de
código.

---

## Sprint 39 — Bug de UI: etiquetas huérfanas en QFormLayout (Sancionatorio y Laboral) ✅ Completado

**Prioridad sugerida:** Alta — bug confirmado, de esfuerzo pequeño (una línea por caso), pero visible en
cada liquidación de dos áreas completas; reportado directamente por un usuario real probando la app
(2026-08-01).

**Depende de:** Nada — corrige código ya existente en producción.

**Contexto (reporte de usuario):** al usar el formulario de obligaciones en Sancionatorio y Laboral
aparecen etiquetas de campo visibles sin su control asociado (el campo se ve "vacío", sin nada para
diligenciar), y una etiqueta de Laboral queda fija con un texto que no corresponde al tipo de evento
seleccionado.

**Hallazgos (verificados leyendo el código, 2026-08-01):**
1. `app/views/obligaciones.py:186-188` — para Sancionatorio, `self.campo_valor.setVisible(False)` oculta el
   `QLineEdit` de "Valor" (el monto se calcula desde `cantidad_smlmv_uvt`), pero `QFormLayout.addRow("Valor",
   self.campo_valor)` (línea 127) crea un `QLabel` automático que `setVisible(False)` sobre el widget NO
   oculta. Resultado: la fila "Valor" queda visible con etiqueta pero sin casilla editable.
2. `app/views/obligaciones.py:197` — mismo patrón para "Nivel de riesgo ARL" (`combo_nivel_riesgo_arl`,
   `addRow` en línea 161): se oculta el combo para toda área que no sea Laboral, pero la etiqueta persiste
   visible al final del formulario en Sancionatorio (y cualquier otra área no laboral).
3. `app/views/eventos_laborales.py:38,45-46` — `layout.addRow("Motivo de suspension", self.combo_motivo)`;
   la visibilidad del combo sí está condicionada al tipo de evento
   (`combo_motivo.setVisible(combo_tipo.currentData() == TipoEventoLaboral.SUSPENSION)`), pero la etiqueta
   de texto "Motivo de suspension" queda visible siempre, incluso cuando el evento es Incapacidad u otro
   tipo distinto de Suspensión.
4. Ya existe el patrón correcto para copiar en el mismo archivo: `campo_fecha_origen`/`label_fecha_origen`
   (`obligaciones.py:130-214`) sí oculta explícitamente su propio `QLabel` junto con el widget — solo falta
   aplicar la misma solución en los 3 puntos de arriba.

**Código nuevo a crear:**
- En cada uno de los 3 puntos, guardar una referencia al `QLabel` que devuelve `QFormLayout.addRow(...)` (o
  usar `layout.labelForField(widget)` / `layout.setRowVisible(widget, bool)` si la versión de PySide6 en
  uso lo soporta) y sincronizar su visibilidad con la del widget correspondiente, igual que ya se hace con
  `fecha_origen`.

**Alcance incluido:** los 3 casos confirmados arriba. Antes de cerrar el sprint, revisar rápido el resto de
`app/views/` buscando otros `setVisible(False)` sobre un widget de un `addRow(str, widget)` sin ocultar
también la etiqueta, por si hay más casos del mismo patrón no reportados todavía.

**Hallazgo adicional (QA visual del Sprint 34, 2026-08-06):** al verificar visualmente
`ObligacionFormDialog` reorganizado en secciones colapsables (Sprint 34,
`docs/superpowers/plans/2026-08-06-sprint34-ux-formularios.md`), se confirmó que el patrón es mucho más
extendido de lo que documentaban los 3 casos originales — **no es exclusivo de Sancionatorio/Laboral**.
Con `area="CIVIL_FAMILIA"` (tipo Puntual), la sección "Datos básicos" muestra simultáneamente las
etiquetas huérfanas de "Fecha de inicio (Recurrente)", "Dia de pago (Recurrente)", "Cantidad SMLMV/UVT
(Sancionatorio)", "Base de la sancion (impuesto a cargo o diferencia)", "Meses o fraccion de atraso
(extemporaneidad)", "Ingresos brutos (Renta liquida)", "Devoluciones/rebajas/descuentos (Renta liquida)",
"Costos (Renta liquida)", "Deducciones (Renta liquida)", "Rentas exentas (Renta liquida)", "Fecha de
terminacion de contrato", "Fecha de pago real" y "Nivel de riesgo ARL" — es decir, prácticamente todos los
campos condicionales de `ObligacionFormDialog` que se ocultan según área/tipo dejan su etiqueta visible en
cualquier área donde no aplican, no solo los 3 campos puntuales ya documentados arriba. Captura de pantalla
de referencia tomada durante el cierre de los Sprints 31-35 (no versionada en el repo). El "Alcance
incluido" de este sprint debe ampliarse: aplicar `layout.labelForField(widget)` +
`setVisible()` sincronizado (o `QFormLayout.setRowVisible()` si la versión de PySide6 en uso lo soporta,
confirmar) a **todos** los `addRow(str, widget)` condicionales de `ObligacionFormDialog`
(`app/views/obligaciones.py`), no solo a los 2 originalmente listados ahí ("Valor" y "Nivel de riesgo
ARL").

**Definición de Hecho:**
- Verificación (test de GUI o manual documentada) de que al abrir el formulario de obligaciones con
  `area="SANCIONATORIO"` ni "Valor" ni "Nivel de riesgo ARL" quedan visibles como fila huérfana.
- Verificación de que al seleccionar un evento laboral tipo Incapacidad, la etiqueta "Motivo de suspension"
  no es visible.
- Verificación adicional (agregada 2026-08-06): con `area="CIVIL_FAMILIA"` (u otra área no Sancionatorio/
  Laboral/Tributario), ningún campo de las secciones "Datos básicos"/"Tasas e intereses"/"Honorarios y
  costas" que no aplique a esa área/tipo deja su etiqueta visible sin el widget correspondiente.
- Suite completa en verde.

**Cierre de implementación (2026-08-07):** Completado. Ver
`docs/superpowers/plans/2026-08-06-sprint39-labels-huerfanas-qformlayout.md`. Corregido con
`QFormLayout.setRowVisible()` (Qt 6.4+, disponible en el PySide6 6.11 del proyecto), centralizado en el
nuevo helper `app/views/form_utils.py::set_row_visible()` (con fallback automático al patrón manual
`labelForField()` si esa API no existiera). El alcance real resultó más amplio que los 3 casos
originales y que el "Hallazgo adicional" del Sprint 34: además de prácticamente todos los campos
condicionales de `ObligacionFormDialog` (centralizados con el nuevo `_aplicar_visibilidad_filas()`, que
itera pares widget/condición por `QFormLayout` en vez de repetir `setVisible()` suelto) y el combo
"Motivo de suspensión" de `EventoLaboralFormDialog`, se encontró y corrigió un caso no reportado:
`campo_vigente_hasta` en `ParametroFormDialog` (`app/views/configuracion.py`). Los `addRow(widget)` de
un solo argumento (checkboxes sin etiqueta separada) no generan `QLabel` y no sufren el bug — se
dejaron con `setVisible()` directo. Suite completa en verde (845 tests tras este sprint individual, 863
tras el merge final).

---

## Sprint 40 — El interés causado no aparece en la tabla del PDF (bug transversal a todas las áreas) ✅ Completado

**Prioridad sugerida:** Alta — bug real de cálculo/reporte, no de UI; afecta la credibilidad del documento
que se entrega al juzgado en las 6 áreas operables (Civil/Familia, Comercial, Laboral, Sancionatorio,
Honorarios, Tributario). Reportado por un usuario real: "en las tablas del PDF de todas las áreas aparece 0
pesos en intereses generados, pero aparece el saldo final de intereses" (con valor distinto de cero).

**Depende de:** Nada — corrige código ya existente en producción (`LiquidationCore`, usado por todas las
`AreaStrategy`).

**Hallazgos (verificados leyendo el código, 2026-08-01):**
- `app/engine/liquidation/engine.py`, `_process_event` (línea ~132): el campo `interest_amount` de cada
  `LiquidationItem` se inicializa en `Decimal("0.00")` y solo se le asigna un valor distinto de cero cuando
  `event.event_type == "INTEREST"` (línea ~140-143).
- Ninguna `AreaStrategy` real (Civil/Familia, Comercial, Laboral, Sancionatorio, Honorarios, Tributario)
  emite jamás un evento con `event_type="INTEREST"` — ese tipo de evento solo aparece en
  `tests/liquidation/test_engine.py` y `tests/services/test_area_strategy.py`, nunca en código de
  producción.
- El interés diario real sí se calcula correctamente y se acumula en el saldo (`_accrue_time_passage`,
  línea ~105-127, vía `BalanceEngine.add_interest`) **antes** de procesar cada evento siguiente, pero ese
  incremento nunca genera su propia fila (`LiquidationItem`) — queda "escondido" dentro de
  `balance.debt.interest` de la fila del próximo evento, cuyo propio `interest_amount` permanece en 0
  porque ese evento no es de tipo `"INTEREST"`.
- `app/reports/pdf.py` y `app/engine/reports/table_builder.py:21` simplemente imprimen `item.interest_amount`
  tal cual llega — el bug está más arriba, en `LiquidationCore`, no en el generador de PDF.
- El resumen ejecutivo del reporte sí muestra el número correcto (`app/engine/reports/summary.py`, vía
  `result.total_interest_accrued()` y `final_debt.interest`), lo que explica por qué el "Saldo Final de
  Intereses" del resumen es correcto mientras la tabla de detalle fila-por-fila muestra 0 en todas las
  filas.

**Decisión de diseño a tomar antes de codificar:**
- (a) Que `_accrue_time_passage` genere su propia fila/evento sintético de "interés causado" con
  `interest_amount` poblado cada vez que se causa interés entre dos eventos, o (b) que cada
  `LiquidationItem` calcule su `interest_amount` como el delta de `balance.debt.interest` respecto a la
  fila anterior, en vez de depender de un `event_type` que nunca se dispara en producción.

**Código nuevo a crear:**
- Implementar la opción elegida arriba.
- Ajustar `table_builder.py`/`pdf.py` si el nuevo campo cambia de nombre o de semántica.

**Riesgos / notas técnicas conocidas:**
- Cambiar cómo se calcula `interest_amount` por fila puede alterar el desglose visual de liquidaciones ya
  generadas y archivadas en PDF — no afecta el saldo final (que ya es correcto), solo la columna de detalle
  por período. Conviene una suite de regresión que compare el total de la columna nueva contra
  `total_interest_accrued()` para confirmar que cuadran exactamente.
- Interactúa con el motor de auditoría (Sprint 9): si se agrega un evento sintético nuevo, confirmar que
  `reconstruir_liquidacion()` lo reproduce igual al reconstruir liquidaciones históricas.

**Definición de Hecho:**
- Test de integración que liquide una obligación con al menos dos períodos de mora y confirme que la tabla
  de detalle tiene, para cada fila relevante, un `interest_amount` > 0 coherente con los días transcurridos.
- La suma de la columna "Interés" de la tabla de detalle coincide exactamente con el saldo final de
  intereses del resumen ejecutivo.
- Suite completa en verde.

**Cierre de implementación (2026-08-07):** Completado. Ver
`docs/superpowers/plans/2026-08-06-sprint40-interes-causado-pdf.md`. Se descartó la opción (a) del
plan (evento sintético "INTEREST") por su interacción innecesaria con el motor de auditoría; se
implementó una variante correcta de la opción (b): `LiquidationCore.process()` captura el interés
causado por `_accrue_time_passage` inmediatamente antes de cada evento (y antes del corte final) y lo
atribuye al `interest_amount` de esa fila — no un delta crudo de `balance.debt.interest` (que iría
negativo en filas de pago/capitalización), sino el interés efectivamente causado por paso del tiempo en
ese tramo, siempre `>= 0`. El branch preexistente `event_type == "INTEREST"` (usado solo en tests) se
mantiene y ahora suma en vez de sobrescribir, ya que ambos interés son conceptualmente aditivos. El
saldo final de intereses no cambió (ya era correcto); solo se corrigió el desglose por fila que llega
al PDF/Word. Confirmado por lectura (no solo por tests) que `reconstruir_liquidacion()` (Sprint 9)
nunca vuelve a ejecutar `LiquidationCore.process()` — solo deserializa el snapshot JSON ya guardado —
por lo que el cambio no puede alterar reconstrucciones históricas ya persistidas. `table_builder.py`,
`pdf.py` y `summary.py` no requirieron cambios: ya imprimían `item.interest_amount`/
`total_interest_accrued()` tal cual, sin lógica de fallback. Suite completa en verde (837 tests tras
este sprint individual, 863 tras el merge final).

---

## Sprint 41 — Familia: obligaciones recurrentes con reajuste anual, concepto por mes y cuotas seleccionables para abono ✅ Completado

**Prioridad sugerida:** Alta — reportado por un usuario real usando el módulo de Familia recién cerrado
(Sprint 20/21, "Suma Única"/múltiples tasas, 2026-07-31 → 2026-08-01), describe una funcionalidad central
del área (cuota alimentaria mensual con reajuste anual) que hoy no existe ni parcialmente.

**Depende de:** Sprint 8 (indexación IPC), Sprint 20 (Suma Única), Sprint 21 (múltiples tasas) — todos
completados; este sprint extiende el módulo Civil/Familia ya operable, no lo reemplaza.

**Contexto (reporte de usuario, 2026-08-01, probando el módulo con un caso real de cuota alimentaria):**
1. Al agregar una obligación recurrente hay confusión reiterativa entre "concepto" y "categoría": el
   concepto de una cuota alimentaria (recurrente) debería nombrar el mes exacto (ej. "CAPITAL DE LA CUOTA
   ALIMENTARIA DE MARZO" / "INTERÉS DE LA CUOTA ALIMENTARIA DE MARZO"), no quedar fijo. El capital de la
   cuota debe aumentar cada 1 de enero según el porcentaje de aumento salarial (SMMLV) o de IPC que
   contemple el acta/título ejecutivo, manteniéndose igual durante el resto del año.
2. El sistema calculó mal las obligaciones: dejó el capital de la primera cuota fijo pero "aumentó el
   valor" en las demás (en vez de mantenerlo constante dentro del año), no calculó intereses de mora por
   cuota, y solo calculó indexación por IPC de forma incorrecta. El reajuste correcto es:
   `cuota_nueva = cuota_anterior + (cuota_anterior × porcentaje_variación_anual / 100)`.
3. La casilla de "abonos" solo tiene sentido si el sistema genera automáticamente el listado mensual de
   obligaciones antes de liquidar (no solo al momento de liquidar): al ingresar fecha del acta + fecha de
   pago, el sistema debería detectar la recurrencia y producir todas las cuotas de cada año hasta la fecha
   de corte, ajustando cada 1 de enero según SMMLV o IPC, con intereses calculados de forma autónoma por
   cuota (capital propio + sus propios días de mora — ej. la cuota de diciembre 2025 tiene intereses
   distintos a la de enero 2026 porque en enero ya cambió el capital).

**Hallazgos (verificados leyendo el código, 2026-08-01):**
1. `database/models.py` tiene ambos campos (`concepto` texto libre, `categoria` clasificación fija que
   determina el `event_type` del motor, ver `app/core/constants.py:3-11`), pero para una obligación
   RECURRENTE el `concepto` se captura una sola vez en el alta y se copia literalmente en cada cuota mensual
   generada: `app/engine/temporal/schedulers/recurring.py` (`RecurringScheduler`) guarda un único `label`
   reutilizado como `payload["label"]` en todos los eventos mensuales — ninguna cuota dice "cuota
   alimentaria de marzo", todas dicen lo mismo; solo la columna de fecha distingue el mes en el PDF.
2. `RecurringRule.amount` (`recurring.py:9-13,46`) es un único `Decimal` fijo usado igual en las 12+ cuotas
   generadas — no existe ningún mecanismo de incremento anual (SMMLV o IPC) el 1 de enero, ni ningún
   resultado de búsqueda de "reajuste"/"incremento_anual"/"cuota_alimentaria" conectado al scheduler. Lo que
   el usuario interpretó como "el capital aumentó" es, en el código actual, el saldo acumulado
   (`capital_base`) creciendo por cuotas impagas que se suman al capital pendiente anterior — no el valor de
   cada cuota individual (que sí es constante, solo que no reajustable).
3. `app/services/area_strategy.py:291-304` (`_construir_rate_provider_obligacion`) fija una sola tasa diaria
   uniforme para toda la vida de la obligación recurrente — no hay tasa/mora calculada de forma autónoma por
   cuota.
4. No existe generación explícita/persistida de cuotas: el `RecurringScheduler` expande la obligación
   recurrente en eventos solo de forma efímera dentro de `liquidar()` (`area_strategy.py:251-260`), nunca
   como filas individuales visibles en la base de datos o en la UI antes de liquidar.
5. Los abonos son una lista plana sin vínculo a una cuota específica: `Abono` (`database/models.py:145-154`)
   solo tiene `fecha`, `monto`, `referencia` contra un `obligacion_id` — no hay forma de decir "este abono
   corresponde a la cuota de marzo" (`app/views/abonos.py`, `AbonoFormDialog`).

**Decisión de diseño a tomar con el usuario antes de codificar (no asumir — mismo criterio que exigieron
los Sprints 13, 16 y 20):**
- ¿El reajuste anual se modela como campo(s) nuevo(s) en `Obligacion` (ej.
  `tipo_reajuste_anual: "SMMLV" | "IPC" | "NINGUNO"`, tomado del Acta de Conciliación o título ejecutivo) que
  dispare la generación de cuotas con capital variable por año, constante dentro de cada año calendario?
- ¿Las cuotas mensuales se materializan como filas reales en base de datos (una `Obligacion` hija PUNTUAL
  por mes, generada automáticamente) o siguen siendo efímeras pero se exponen en una vista previa de la UI
  antes de liquidar, para poder seleccionar sobre cuáles hubo abono?
- Confirmar formalmente con el despacho la fórmula de reajuste (el usuario ya la trajo en conversación, pero
  no está todavía en `Preguntas-Para-Abogado-Abiertas.md`) — agregar esa pregunta al documento antes o al
  empezar este sprint.

**Caso de prueba real disponible (caso de oro para pruebas de regresión):** el usuario compartió una
demanda ejecutiva de alimentos real (Daniela Aranda Andrade c. Jorge Andrés Carvajal Córdoba, Juzgado de
Familia de Neiva, radicada 2026-06-28) con una liquidación completa hecha a mano por el despacho: capital,
intereses de mora día a día e indexación ya calculados. Cuota base $100.000 (Acta de Conciliación No.
036-2019, Comisaría de Familia de Yaguará, 2019-07-23, cláusula tercera: reajustable cada 1 de enero según
el % de incremento del SMMLV decretado por el Gobierno Nacional) creciendo hasta $212.450 vigente en 2026;
interés moratorio simple a la tasa legal del 6% efectivo anual (0,0001643835616 diario); mora calculada día
a día de forma independiente por cuota (ej. cuota de mayo 2026: 54 días de mora = $1.886,21; cuota de junio
2026: 23 días = $803,07); gastos extraordinarios de salud/educación con indexación IPC e intereses propios,
independientes de la cuota ordinaria. Es un caso ideal para verificar el algoritmo de reajuste anual y el
cálculo de mora por cuota autónoma que pide este sprint. Pendiente que JoseMsD agregue el PDF de la demanda
como fixture en el repo (ej. `tests/family/fixtures/demanda_alimentos_aranda_2026.pdf` — no se pudo escribir
el binario desde esta conversación) y construya un test de integración que reproduzca sus cifras exactas.

**Código nuevo a crear (una vez aprobado el diseño):**
- Campo(s) nuevos en `Obligacion` para el reajuste anual + migración de esquema (mismo patrón que los
  Sprints 8/12/19).
- Generador de cuotas mensuales con reajuste anual: capital constante dentro del año, reajustado cada 1° de
  enero según el índice que aplique.
- Interés de mora calculado de forma autónoma por cuota (capital propio de esa cuota × tasa diaria × sus
  propios días de mora), no sobre el saldo agregado del expediente completo.
- Etiqueta/concepto dinámico por cuota (interpolando mes y año), en vez de un texto fijo copiado a todas las
  filas.
- UI: vista previa de las cuotas generadas antes de liquidar, con selección de abono por cuota en vez de una
  lista plana sin vínculo.

**Alcance incluido:** Familia (cuota alimentaria y gastos extraordinarios). El mismo mecanismo de reajuste
anual queda como base reutilizable para el Sprint 44 (Laboral) si el usuario decide extenderlo ahí también.

**Alcance explícitamente excluido:** por ahora no incluye Laboral (queda en el Sprint 44, con su propia
decisión de diseño) ni retro-generar cuotas para obligaciones recurrentes ya creadas en expedientes
existentes — solo aplica hacia adelante salvo que el usuario pida explícitamente una migración de datos.

**Riesgos / notas técnicas conocidas:**
- Cambia el resultado numérico de cualquier liquidación de Familia con obligaciones recurrentes ya
  registradas — requiere el mismo cuidado de regresión que exigió el Sprint 20.
- Alta complejidad: toca el generador de eventos (`RecurringScheduler`), el motor de intereses (cálculo por
  cuota autónoma en vez de saldo agregado) y la UI de abonos — conviene partirlo en sub-tareas con
  `superpowers:writing-plans` antes de tocar código, y una conversación previa tipo
  `superpowers:brainstorming` con el usuario (igual que se hizo para el Sprint 20).

**Definición de Hecho:**
- Test de integración que reproduce exactamente las cifras de la demanda de Daniela Aranda (o al menos su
  lógica de reajuste anual y mora por cuota, si no se consigue el PDF como fixture a tiempo).
- Un expediente con obligación recurrente familiar de varios años genera cuotas con el capital correcto por
  año y mora calculada de forma independiente por cuota.
- Suite completa en verde.

**Cierre de implementación (2026-08-09):** Completado. Ver
`docs/superpowers/plans/2026-08-07-sprint41-familia-cuotas-reajuste-anual.md`. Decisión tomada con el
usuario (2026-08-07, sin sesión de brainstorming adicional): usar el diseño propuesto directamente. Nuevo
campo `Obligacion.tipo_reajuste_anual` (SMMLV/IPC/NINGUNO) y `obligacion_padre_id` (auto-referencial, sin
`ForeignKey()` real — SQLite rechaza `DROP COLUMN` sobre una columna con FK de tabla, verificado
empíricamente). Nuevo servicio `app/services/reajuste_anual.py::generar_cuotas_mensuales()` genera y
persiste las cuotas mensuales como `Obligacion` PUNTUAL hijas, capital constante dentro del año, reajustado
cada 1° de enero, concepto dinámico por mes/año; idempotente (no duplica si ya se generaron). Los abonos se
capturan por cuota individual reutilizando `AbonoFormDialog` contra el `obligacion_id` de la cuota, sin
campo nuevo en `Abono`, tal como proponía el diseño original. `CivilFamiliaStrategy` usa las cuotas hijas
reales en vez de expandir con `RecurringScheduler` cuando ya existen, evitando doble conteo de capital.
**Verificación matemática (Task 3, bloqueante para la UI):** se confirmó — no refutó — que el interés de
mora consolidado que produce el motor sobre las cuotas reales coincide exactamente con la suma de calcular
cada cuota de forma aislada (capital propio × sus propios días de mora); no hizo falta ningún motor de
interés "autónomo por cuota" nuevo, la linealidad del interés simple ya lo garantiza (Civil/Familia no tiene
wiring de anatocismo). No hay PDF real de la demanda de Daniela Aranda disponible todavía — el test de
integración final usa datos sintéticos equivalentes, no las cifras exactas del caso. La fórmula de reajuste
(`cuota_nueva = cuota_anterior + cuota_anterior × pct_variación_anual / 100`) queda pendiente de
confirmación formal del despacho — pregunta agregada a `Preguntas-Para-Abogado-Abiertas.md`, sección "Sprint
41". No se retro-generan cuotas para obligaciones recurrentes ya existentes; no se extiende a Laboral (ver
Sprint 44, punto 6, explícitamente excluido). Botón "Generar cuotas" nuevo en `ExpedienteDetallePage`,
visible solo para Civil/Familia. Suite completa en verde (953 tests tras el merge final, que tuvo conflictos
reales con el Sprint 44 sobre los mismos archivos, resueltos a mano).

**Respuesta recibida (2026-08-13):** el despacho confirmó la fórmula base (`CN = CA + CA × %V / 100`) ya
implementada, pero exige parametrizar varias excepciones que hoy **no existen** en el motor: (1) tope de
coerción — ningún embargo por alimentos puede exceder el 50% del salario/prestaciones del deudor
(verificado: no hay ninguna validación de este tope en el código), (2) campo `Fecha_Base_Titulo` para actas
que reajusten en un mes distinto a enero (hoy el reajuste está fijo al 1° de enero), (3) `Factor_Ponderación`
para actas que pacten solo un porcentaje parcial del incremento (ej. 50%), y (4) imputación jerárquica
estricta de pagos (1° intereses moratorios → 2° costas/cobranza → 3° capital del mes más antiguo) a
verificar contra el `AllocationEngine` general. Detalle completo en
`Preguntas-Para-Abogado-Respondidas.md`, sección Sprint 41. Ninguno de estos 4 puntos está construido —
queda como trabajo pendiente de un sprint de seguimiento.

---

## Sprint 42 — Conectar el motor de prescripción/caducidad al flujo real de liquidación ✅ Completado

**Prioridad sugerida:** Alta — el motor matemático (Sprint 7) es correcto y está probado, pero aislado; hoy
cualquier liquidación de cualquier área incluye obligaciones prescritas o caducadas sin advertirlo ni
excluirlas, lo cual es un riesgo real de mala praxis si el software se usa para presentar una demanda o
liquidar un proceso ante un juez.

**Depende de:** Sprint 7 (motor de prescripción y caducidad, ya completo).

**Hallazgos (verificados leyendo el código, 2026-08-01):**
- `app/engine/temporal/prescripcion.py` existe completo y correcto: `calcular_prescripcion` (línea ~50-52),
  `calcular_caducidad` (línea ~65-81), `filtrar_cuotas_prescritas` (línea ~84-97).
- Ninguna de esas funciones se importa fuera de su propio archivo: no aparecen en `area_strategy.py`, en
  `UniversalLiquidationService`, en ningún `app/views/`, ni en `app/reports/pdf.py`. El propio `Pendientes.md`
  (cierre del Sprint 7, línea ~536-537) ya documentaba esto como alcance explícitamente excluido en su
  momento ("Integración con la GUI... es un sprint de UI aparte") — este sprint es exactamente ese
  pendiente, ahora priorizado porque un usuario real lo notó liquidando un caso.
- Confirmado: ninguna `AreaStrategy` excluye ni marca de forma distinta las obligaciones
  prescritas/caducadas al liquidar; el PDF tampoco distingue ese estado en ninguna columna.

**Decisión de diseño a tomar con el usuario antes de codificar:**
- ¿El motor debe (a) excluir automáticamente del cálculo las obligaciones prescritas/caducadas, (b)
  incluirlas pero marcarlas visualmente en el PDF con una advertencia ("obligación prescrita, no exigible"),
  o (c) dejarlo a discreción del abogado con un checkbox por obligación ("ignorar prescripción")? El PDF de
  requisitos no resuelve esto de forma explícita para todas las áreas.

**Código nuevo a crear:**
- Wiring de `filtrar_cuotas_prescritas`/`calcular_prescripcion`/`calcular_caducidad` dentro de cada
  `AreaStrategy.liquidar()` (o centralizado en `UniversalLiquidationService`, para no repetir la lógica 6
  veces).
- Columna/indicador nuevo en la tabla de resultados y en el PDF que muestre el estado de prescripción de
  cada obligación.

**Alcance explícitamente excluido:** no incluye recalcular automáticamente los plazos de caducidad
"manuales" que hoy exige capturar al usuario (Sprint 7) — eso sigue siendo responsabilidad del abogado al
cargar el dato.

**Definición de Hecho:**
- Un expediente con una obligación cuyo plazo de prescripción ya venció queda excluida (o marcada, según lo
  decidido) del total liquidado, con test de integración que lo confirme.
- El PDF refleja el mismo estado.
- Suite completa en verde.

**Cierre de implementación (2026-08-09):** Completado. Ver
`docs/superpowers/plans/2026-08-07-sprint42-prescripcion-caducidad-wiring.md`. Decisión tomada con el
usuario (2026-08-07): opción (b) — marcar con advertencia visual, no excluir automáticamente. Nuevo campo
`LiquidationItem.prescrita` (default `False`), poblado centralizadamente en
`UniversalLiquidationService.liquidar()` (único punto por el que pasan las 6 `AreaStrategy` para invocar
`LiquidationCore`, confirmado leyendo el código en vez de asumir el nombre) reutilizando
`filtrar_cuotas_prescritas`/`calcular_prescripcion` ya existentes, con `TipoAccion.EJECUTIVA` como default
(mismo default provisional que ya usa el Dashboard del Sprint 33 — pregunta abierta compartida, no
duplicada). Falla abierto (sin marcar, sin tumbar la liquidación) si el plazo no está configurado en
Parámetros, mismo criterio que el Dashboard. Filas marcadas se resaltan en rojo con el texto "⚠ ...
Obligación prescrita, no exigible" en pantalla (`app/views/liquidaciones.py`), PDF (`app/reports/pdf.py`) y
Word (`app/reports/word.py`). El total liquidado no cambia — confirmado con tests dedicados que comparan el
saldo final con y sin la marca activa. Se encontró (y se dejó intacto, fuera de alcance) un archivo legado
sin registrar (`app/services/motor_liquidacion.py`) que también instancia `LiquidationCore` directamente
pero no forma parte de `AreaRegistry` ni de ninguna de las 6 `AreaStrategy`. Suite completa en verde (953
tests tras el merge final).

---

## Sprint 43 — Indexación IPC como opción disponible en todas las áreas (hoy exclusiva de Civil/Familia) ✅ Completado

**Prioridad sugerida:** Media — no es un bug, es un límite de alcance documentado desde el Sprint 8, pero el
usuario pide explícitamente que la indexación sea "opcional para cualquier liquidación de cualquier área",
y hoy el checkbox ni siquiera aparece fuera de Civil/Familia.

**Depende de:** Sprint 8 (indexación IPC ya construida y probada para Civil/Familia).

**Hallazgos (verificados leyendo el código, 2026-08-01):**
- `AreaStrategy.soporta_indexacion_ipc` (`app/services/area_strategy.py:180`) es `True` por defecto en la
  clase base, pero queda sobreescrito a `False` explícitamente en `ComercialStrategy` (línea ~323),
  `LaboralStrategy` (~530), `SancionatorioStrategy` (~719), `HonorariosStrategy` (~792) y
  `TributarioStrategy` (~909) — solo `CivilFamiliaStrategy` la deja en `True`.
- El checkbox `check_aplica_indexacion_ipc` en `app/views/obligaciones.py` solo es visible cuando
  `self._area == "CIVIL_FAMILIA"` (líneas 94, 147, 183) — para las otras 5 áreas ni siquiera se muestra, así
  que el campo queda en `False`/nulo implícito y por eso la columna de indexación siempre aparece en 0 en
  esas áreas.
- No es un bug de cálculo: donde el checkbox existe, la indexación funciona (Sprints 8/20). Es la ausencia
  de la opción en 5 de 6 áreas.

**Decisión de diseño a tomar con el usuario:** ¿tiene sentido jurídico permitir indexación IPC en las 6
áreas por igual, o hay áreas donde no aplica o entraría en conflicto con un mecanismo propio ya existente
(ej. Tributario ya tiene su propia actualización monetaria vía Art. 867-1 E.T., Sprint 15 en
`Preguntas-Para-Abogado-Respondidas.md`; Sancionatorio ya resuelve SMLMV/UVT con su propia lógica, ver
Sprint 45)?
Conviene revisar sprint por sprint antes de simplemente activar el flag en las 5 clases restantes.

**Código nuevo a crear (según lo que se decida):**
- Activar `soporta_indexacion_ipc = True` en las áreas donde el despacho confirme que aplica.
- Exponer el checkbox correspondiente en el formulario para esas áreas.
- Validar que no se dupliquen mecanismos de actualización monetaria ya existentes por área.

**Definición de Hecho:**
- El checkbox de indexación IPC aparece y funciona en cada área donde el despacho confirme que aplica, con
  test de integración por área.
- Ninguna área termina aplicando doble actualización monetaria (IPC genérico + su propio mecanismo) sin una
  validación explícita que lo impida o lo advierta.
- Suite completa en verde.

**Seguimiento (2026-08-07):** consultado el usuario sobre qué áreas activar, pidió explícitamente redactar
las preguntas correspondientes en `Preguntas-Para-Abogado-Abiertas.md` en vez de decidir directamente — ver
sección "Sprint 43" de ese documento (pregunta por las 5 áreas, con la advertencia de posible doble
actualización monetaria en Sancionatorio y Tributario). Sigue bloqueado hasta que el despacho responda; no
se tocó código de este sprint.

**Respuesta recibida (2026-08-13):** el despacho respondió las 5 áreas con reglas distintas por área — SÍ
en Tributario (ligado al Art. 867-1 E.T., mutuamente excluyente con el mecanismo propio), NO en Comercial
(XOR con interés comercial), SÍ en Honorarios (con fórmula propia, interés civil 6% **sobre el capital ya
indexado** — ver la nueva pregunta de seguimiento sobre si eso es válido en
`Preguntas-Para-Abogado-Abiertas.md`, sección "Sprint 43 (seguimiento)"), condicional en Laboral (excluyente
con moratorios, con dos excepciones) y condicional en Sancionatorio (excluyente con SMLMV/UVT actualizado,
con una excepción para faltas antiguas). Detalle completo en `Preguntas-Para-Abogado-Respondidas.md`,
sección Sprint 43. Nada de esto está implementado todavía: son 5 mecanismos de exclusión/coexistencia
distintos, no una sola bandera — queda pendiente de programar como sprint(s) de implementación.

**Cierre de implementación (2026-08-17):** Completado, las 5 áreas. `AreaStrategy.soporta_indexacion_ipc`
pasa a `True` en `TributarioStrategy`, `HonorariosStrategy`, `LaboralStrategy` y `SancionatorioStrategy`
(`ComercialStrategy` se mantiene `False` por diseño — no es un add-on libre, ver abajo). El checkbox
`check_aplica_indexacion_ipc` (`app/views/obligaciones.py`) ahora es visible en Civil/Familia, Comercial,
Laboral, Sancionatorio y Honorarios; TRIBUTARIO se deja oculto a propósito porque su IPC es automático (Art.
867-1 E.T., ya construido desde el Sprint 15), no una elección manual.

- **Tributario:** el trigger de mora > 3 años (`aplica_actualizacion_867_1`) y el techo de usura combinado
  (`calcular_indexacion_867_1_topada`) ya existían desde el Sprint 15 y se reutilizaron tal cual — lo nuevo
  es (1) una alerta no bloqueante ("Techo de usura alcanzado") cuando el techo realmente recorta la
  indexación, y (2) el nuevo campo `protegida_inflacion_uvr` (Obligacion), que bloquea con `ValueError` si
  se dispararía IPC sobre una obligación que ya trae su propia protección inflacionaria (ej. UVR).
- **Comercial:** XOR real, no solo documentado — nuevo campo `pacto_expreso_indexacion` (Obligacion). Marcar
  "Aplica indexación IPC" sin ese pacto se bloquea con `ValueError`. Con ambos marcados, la obligación (solo
  PUNTUAL, alcance reducido) liquida en modo (b): capital indexado por IPC + interés civil 6% puro sobre el
  capital ya indexado (Suma Única con tasa civil fija), en vez de la tasa comercial — la sanción por usura
  del Sprint 2 se salta esas obligaciones (la tasa realmente cobrada ya no es la pactada).
- **Honorarios:** fórmula exacta del despacho implementada tal cual (`Capital × IPC_Final/IPC_Inicial +
  Interés_Civil_6%(Capital_Actualizado)`), reutilizando Suma Única + una tasa civil fija
  (`AreaStrategy._tasa_civil_anual_pct`, clave `CIVIL_ANNUAL_RATE`) en vez de la tasa pactada de la
  obligación. Limitaciones documentadas en el docstring de la clase (no construidas): la distinción "de
  oficio"/"a petición de parte" (no existe un concepto de etapa procesal en el modelo) y la alerta
  "Improcedente por acumulación" (no existe un campo de "tipo de interés" civil/comercial en esta área). La
  pregunta abierta sobre el interés civil cobrado sobre capital ya indexado sigue sin resolverse
  (`Preguntas-Para-Abogado-Abiertas.md`).
- **Laboral:** excluyente con la indemnización moratoria del Art. 65 CST sobre el mismo rubro/periodo. Sin
  mora (excepción 1, buena fe) se indexa `monto_prestaciones`; con mora, la moratoria prevalece y se agrega
  la alerta no bloqueante "Doble Actualización Prohibida" (la liquidación no se bloquea). Excepción 2
  (reliquidaciones pensionales) queda documentada como limitación conocida, no construida: `calcular_ibl`
  (`app/engine/labor/ibl.py`, Sprint 17) ya indexa por IPC pero es una función aislada, nunca conectada a
  `AreaRegistry`/`LiquidationResult` — no existe un concepto de "reliquidación" como operación de liquidar()
  distinta de una liquidación normal. `LaboralStrategy` queda en estado limpio para el Sprint 47b (que
  tocará únicamente su lógica de densidad pensional en este mismo archivo).
- **Sancionatorio:** la prohibición general del despacho (IPC excluyente con SMLMV/UVT actualizado a la
  fecha de pago) resultó inalcanzable con el motor actual — `resolver_base_sancion` siempre resuelve la
  unidad según la fecha DEL HECHO, nunca la de pago, así que toda obligación cae en la excepción del
  despacho (documentado en el docstring de la clase, mismo criterio que ya usaba `CivilFamiliaStrategy` para
  su propia combinación inalcanzable). IPC se indexa desde `fecha_origen` hasta la fecha de corte sobre el
  capital ya convertido a pesos.

Mecanismo nuevo compartido: `LiquidationResult.alertas` (lista de strings, default vacía) para el "feedback
no bloqueante" que pedía el despacho en Laboral/Tributario — la vista (`expediente_detalle.py`) los muestra
con `mostrar_toast(tipo="warning")`, reutilizando el mecanismo del Sprint 36 en vez de inventar uno nuevo.
2 columnas nuevas en `Obligacion` (`pacto_expreso_indexacion`, `protegida_inflacion_uvr`), migradas via
`scripts/migrate_indexacion_ipc_areas_sprint43.py`. `IPC_INDICE_ACUMULADO`/`IPC_VARIACION_ANUAL`/
`CIVIL_ANNUAL_RATE` ampliadas en `app/services/areas_parametro.py` para que Parámetros muestre la fila
correcta de áreas. Suite completa en verde (1251 tests).

**2 correcciones de code review, aplicadas antes de cerrar (2026-08-18):**
1. `alertas` no se guardaba/recuperaba en la serialización de auditoría (`app/engine/audit/serialization.py`)
   — una liquidación histórica reconstruida desde `AuditLog` siempre volvía con `alertas=[]`, aunque la
   original sí tuviera advertencias. Corregido (commit `1906ebe`) con round-trip real, verificado con test.
2. El toast de alertas solo se disparaba en el cálculo en vivo (`_on_liquidar_completado`), no al reabrir una
   liquidación histórica (`_reconstruir_desde_historial`) ni en ningún lugar persistente. Corregido (commit
   `cf84ae7`): helper compartido `_mostrar_alertas_de_liquidacion` llamado desde ambos flujos, más un banner
   de advertencia persistente en `ResultadoLiquidacionView` (mismo patrón visual que el prefijo "⚠" ya usado
   para obligaciones prescritas), que se limpia correctamente en cada `mostrar()` para no arrastrar alertas
   de una liquidación anterior. **Quedó pendiente a propósito, documentado como seguimiento explícito, no
   perdido en el commit:** `app/reports/pdf.py`/`word.py` siguen sin leer `.alertas` — un abogado que exporte
   PDF/Word sin volver a abrir la app no ve advertencias como "Doble Actualización Prohibida" o "Techo de
   usura alcanzado" en el documento. Ver Sprint 77.

Suite completa en verde tras ambas correcciones (1258 tests).

---

## Sprint 44 — Laboral: salario mínimo automático, descuentos, edición de obligaciones/eventos y fecha de corte ✅ Completado

**Prioridad sugerida:** Media-alta — agrupa varios gaps de UX/alcance reales reportados por el usuario
probando el área Laboral; ninguno es un bug de cálculo del motor, todos son huecos de formulario/edición.

**Depende de:** Nada estrictamente (extiende `LaboralStrategy`, ya operable desde los Sprints 3/16).

**Hallazgos (verificados leyendo el código, 2026-08-01):**
1. **Checkbox "salario = SMMLV":** no existe. La infraestructura para resolverlo sí existe
   (`app/engine/indexation/historical_index.py::get_smlmv_for_year`, ya usada por Sancionatorio vía
   `smlmv_to_uvt.py`), pero `LaboralStrategy` nunca la importa; el campo `valor` de Laboral es siempre texto
   libre digitado a mano (`app/views/obligaciones.py:127`, `_guardar_laboral` ~línea 410-414).
2. **"Fecha de pago real" sin campo visible:** el campo sí existe en el modelo (`database/models.py:104`,
   `fecha_pago_total`) y sí tiene `QDateEdit` en el formulario (`obligaciones.py:113-114,159`), pero queda
   oculto salvo que se marque el checkbox "Prestaciones pagadas" (`check_pagada`, líneas 112,195,263) — y
   como **no existe ningún diálogo de edición de una obligación ya guardada**
   (`expediente_detalle.py:174-182` siempre abre el formulario en modo creación), si el abogado no marcó ese
   checkbox al crear el registro, no tiene forma de volver a diligenciar la fecha después sin borrar y
   recrear la obligación.
3. **"Descuentos" del empleador (legales o ilegales):** no existe ningún campo para modelar deducciones que
   el empleador le haga al salario del trabajador — el único campo con la palabra "descuento" en todo el
   esquema (`devoluciones_rebajas_descuentos`, `models.py:129`) pertenece al área Tributario (renta líquida
   gravable), sin relación con nómina.
4. **Eventos contractuales (incapacidad/suspensión) no editables, y error al recalcular:** no existe CRUD de
   edición/eliminación de `EventoLaboral` (`expediente_detalle.py` solo permite crear uno nuevo). El "error
   al calcular" que reportó el usuario corresponde a validaciones reales de
   `LaboralStrategy._validar_obligacion_laboral` (`area_strategy.py:681-704`): eventos sin
   `incluir_seguridad_social` marcado, eventos fuera del rango del contrato, o eventos solapados — no es un
   fallo técnico sino el comportamiento esperado de esas validaciones ante datos incoherentes, pero como no
   hay forma de editar el evento ya creado, corregir el dato obliga a borrar y recrear.
5. **"Fecha de corte" no editable desde la pantalla de liquidación:** `expediente_detalle.py:216` toma
   directo `expediente.fecha_corte_default`; no hay ningún `QDateEdit` propio en la pantalla de liquidación.
   El único lugar donde se edita es el diálogo separado "Editar expediente" (`app/views/expedientes.py`, sin
   restricciones de rango) — el usuario buscó el campo en el lugar equivocado (pantalla de liquidación)
   porque no hay ningún atajo ahí.
6. **Cuotas mensuales de salario pre-generadas con reajuste anual, igual que se pide para Familia (Sprint
   41):** no existe — Laboral fuerza `TipoObligacion.PUNTUAL` (`obligaciones.py:434`) y usa un único `valor`
   como salario base para todo el finiquito.

**Código nuevo a crear:**
- Punto 1: campo `es_smmlv: bool` en `Obligacion` (+ migración) y checkbox en el formulario Laboral;
  `LaboralStrategy` resuelve el valor desde `get_smlmv_for_year` cuando esté activo.
- Punto 2: CRUD de edición de `Obligacion` ya guardada (formulario de creación reutilizado en modo edición,
  precargando valores) — resuelve de raíz el problema de descubribilidad de "fecha de pago real" sin
  necesitar tocar la lógica de visibilidad condicional.
- Punto 3: campo(s) nuevos para modelar descuentos del empleador (monto, fecha, y una marca de si se alega
  legal/ilegal, útil tanto para el cálculo de la liquidación como para la narrativa probatoria del caso) —
  requiere decisión de diseño con el usuario sobre el modelo exacto de datos.
- Punto 4: CRUD de edición/eliminación de `EventoLaboral`.
- Punto 5: campo de fecha de corte editable (override) directamente en la pantalla de liquidación, o al
  menos un atajo visible hacia "Editar expediente" desde ahí.
- Punto 6: ver Sprint 41 — decidir con el usuario si se reutiliza el mismo mecanismo de reajuste anual ahí
  construido, extendido a Laboral.

**Alcance explícitamente excluido:** el punto 6 depende de la decisión de diseño del Sprint 41; si el
usuario decide no extenderlo a Laboral en la misma ronda, queda como sprint propio más adelante.

**Definición de Hecho:**
- Un abogado puede editar cualquier obligación o evento laboral ya guardado sin borrar y recrear.
- El campo "fecha de pago real" es accesible independientemente del checkbox "Prestaciones pagadas".
- Existe un campo de descuento del empleador que resta del neto adeudado y aparece en el reporte.
- Marcar "salario = SMMLV" resuelve automáticamente el valor correcto según el año.
- Suite completa en verde.

**Cierre de implementación (2026-08-09):** Completado. Ver
`docs/superpowers/plans/2026-08-07-sprint44-laboral-ux-edicion.md`. Punto 3 (descuentos) implementado según
decisión del usuario (2026-08-07): entidad propia `DescuentoLaboral` (mismo patrón que `Abono`: `fecha`,
`monto`, `es_legal`, `motivo`), inyectada como eventos `PAYMENT` adicionales que reutilizan el mecanismo de
`AllocationEngine`/`LiquidationCore` ya existente, sin motor nuevo. Punto 1: checkbox `es_smmlv` resuelve el
salario vía `get_smlmv_for_year(fecha_origen.year)` **en cada liquidación** (nunca persiste el valor
resuelto — el flujo cierra la sesión de SQLAlchemy antes de mutar `obligacion.valor` en memoria, evitando
que se filtre por accidente a la base de datos), así nunca queda desactualizado si el SMLMV se corrige
después. Punto 2 y 4 (edición de `Obligacion`/`EventoLaboral`): nuevo helper compartido
`app/views/form_utils.py::guardar_o_actualizar()` (extraído del patrón que ya usaba `ExpedienteFormDialog`)
evita duplicar la lógica de "editar sin borrar y recrear" entre los dos diálogos. Punto 5: fecha de corte
editable como override puntual en la pantalla de liquidación, sin tocar `expediente.fecha_corte_default`.
**Punto 6 (reajuste anual extendido a Laboral) quedó explícitamente fuera de alcance**, confirmado sin
tocar. Suite completa en verde (929 tests tras este sprint individual, 953 tras el merge final — tuvo un
conflicto real con el Sprint 41 sobre `obligaciones.py`/`expediente_detalle.py`, resuelto a mano).

---

## Sprint 45 — Sancionatorio: transparencia de la unidad SMLMV/UVT y aclaración del caso de capital creciente ✅ Completado

**Prioridad sugerida:** Media — un punto es una mejora de UX confirmada (transparencia de unidad), el otro
es una queja de usuario que **no se pudo reproducir** revisando el código; necesita más información antes
de tratarse como bug.

**Depende de:** Nada.

**Hallazgos (verificados leyendo el código, 2026-08-01):**
1. **Selector de unidad SMLMV/UVT:** el campo `cantidad_smlmv_uvt` (`database/models.py:111`) es un solo
   número sin columna de unidad; el sistema decide automáticamente SMLMV vs. UVT según la fecha del hecho
   (`app/engine/indexation/smlmv_to_uvt.py:8`, corte 2020-01-01, Ley 1955/2019 art. 49) — la regla legal en
   sí parece correcta, pero el formulario (`obligaciones.py:88,142,176`) no le muestra al abogado cuál de
   las dos unidades se va a aplicar según la fecha que capturó, así que no hay forma de verificar la
   interpretación antes de liquidar.
2. **Capital de una multa puntual "creciendo exponencialmente":** se revisó toda la cadena de cálculo de
   `SancionatorioStrategy.liquidar()` (`area_strategy.py:721-769`) y `LiquidationCore`
   (`engine.py`/`balance.py`/`daily_interest.py`) sin lograr reproducir el bug — una obligación PUNTUAL
   genera un único evento de capital, los pagos solo restan, el interés (simple, no compuesto —
   Sancionatorio no tiene wiring de anatocismo) se acumula en un campo separado del capital
   (`PendingDebt.interest`, nunca se suma a `principal`), y la columna "Capital base" de la tabla de
   resultados permanece constante; solo "Saldo" (capital + interés + indexación) crece, y de forma lineal,
   no exponencial.

**Qué se necesita del usuario antes de tratar el punto 2 como bug confirmado:** el expediente o captura de
pantalla exacta donde se vio el capital creciendo — hipótesis más probables a descartar primero: (a) que se
leyó la columna "Saldo" (total acumulado) como si fuera "Capital", o (b) que el expediente tenía varias
multas fusionadas en un solo resultado consolidado (`_fusionar_resultados`, `area_strategy.py:113-174`) que
sumó mal varias obligaciones como si fueran una sola creciendo.

**Código nuevo a crear (punto 1, confirmado):**
- Texto/indicador dinámico junto al campo `cantidad_smlmv_uvt` que muestre "se aplicará como UVT" o "se
  aplicará como SMLMV" según la `fecha_origen` capturada, sin necesidad de cambiar el modelo de datos (la
  regla de negocio ya es correcta, solo falta mostrarla).

**Alcance explícitamente excluido (punto 2):** no se codifica ningún fix hasta reproducir el caso con datos
reales — evitar "arreglar" algo que no está roto en el código revisado.

**Definición de Hecho:**
- El formulario de Sancionatorio muestra explícitamente qué unidad (SMLMV o UVT) se va a usar según la
  fecha capturada.
- El punto 2 queda documentado como pendiente de reproducir, con la pregunta explícita al usuario, hasta
  tener un caso concreto.

**Cierre de implementación (2026-08-09):** Completado (punto 1, único punto en alcance de código). Ver
`docs/superpowers/plans/2026-08-07-sprint45-sancionatorio-transparencia-unidad.md`. `QLabel` dinámico junto
a `campo_cantidad_smlmv_uvt` en `ObligacionFormDialog`, actualizado en vivo vía
`campo_fecha_origen.dateChanged`, que muestra "Se aplicará como: SMLMV" o "Se aplicará como: UVT"
reutilizando `FECHA_CORTE_SMLMV_A_UVT` de `app/engine/indexation/smlmv_to_uvt.py` sin duplicar la fecha de
corte (2020-01-01) en la UI. No se tocó ningún archivo de `app/engine/`/`area_strategy.py`, tal como pedía
el alcance. **Punto 2 (capital creciente) sigue sin reproducirse** — no es un bug confirmado, queda a la
espera de que el usuario aporte el expediente o captura de pantalla exacta donde lo vio. Suite completa en
verde (867 tests tras este sprint individual, 953 tras el merge final).

---

## Sprint 46 — El saldo a favor de un sobrepago no aparece en el PDF/Word ni en la pantalla de resultado ✅ Completado

**Prioridad sugerida:** Media-alta — sigue de cerca al Sprint 23: el dato ya no desaparece del modelo de
datos, pero sigue siendo invisible en todo documento que un abogado o un juez realmente lee. Detectado por
el revisor final de código del Sprint 23 (2026-08-01), no por un reporte de usuario.

**Depende de:** Sprint 23 (Bugs críticos de integridad financiera y auditoría) — ya completado. Este sprint
es el cierre real, de cara al usuario, del mismo bug: el Sprint 23 corrigió que `LiquidationCore` capturara
el remanente de un sobrepago en un campo nuevo `saldo_a_favor` (`LiquidationItem`/`LiquidationResult`), pero
ese campo nunca llegó a ningún lugar donde un humano lo vea.

**Hallazgos (revisión final del Sprint 23, 2026-08-01):**
- `app/engine/reports/summary.py` (`ReportSummaryBuilder.build_summary()`) no lee `saldo_a_favor` ni
  `LiquidationResult.total_saldo_a_favor()` en ningún punto — el resumen ejecutivo del PDF/Word no menciona
  el sobrepago aunque exista.
- `app/engine/reports/table_builder.py` (`ReportTableBuilder.build_matrix()`) tampoco agrega una columna ni
  una fila para `saldo_a_favor` — la tabla de detalle fila por fila no muestra el excedente en la fila del
  pago que sobrepagó.
- `app/reports/pdf.py` y `app/reports/word.py` heredan el mismo hueco por construcción, ya que ambos
  consumen la salida de `summary.py`/`table_builder.py` sin lógica propia de qué campos mostrar.
- `app/views/liquidaciones.py` (`ResultadoLiquidacionView`) tampoco muestra `saldo_a_favor` en ningún label
  ni columna de la tabla en pantalla.
- Consecuencia práctica: hoy, un pago de $10.000.000 contra una deuda de $7.000.000 ya no pierde el dato
  internamente (corregido en el Sprint 23), pero el PDF/Word entregado y la pantalla de resultado siguen
  mostrando el mismo total que si el excedente nunca hubiera existido — el bug original sigue siendo visible
  para el usuario final, solo que ahora el dato correcto sí existe en memoria y en el `AuditLog` para quien
  sepa consultarlo directamente.

**Código nuevo a crear:**
- `summary.py`: agregar una línea al resumen ejecutivo (ej. "Saldo a favor del deudor: $X") cuando
  `resultado.total_saldo_a_favor() > 0`, omitida por completo cuando es cero (no ensuciar el resumen de
  liquidaciones sin sobrepago).
- `table_builder.py`: mostrar el `saldo_a_favor` de la fila del evento `PAYMENT` correspondiente, igual que
  ya se muestra `payment_amount` — mismo formato de columna, sin fila/columna nueva si el patrón existente
  de la tabla no lo permite fácilmente (evaluar durante la implementación cuál encaja mejor sin romper el
  layout actual usado por las 6 áreas).
- `liquidaciones.py`: reflejar el mismo dato en la pantalla de resultado, junto al resto de totales ya
  mostrados (capital, interés, saldo final).

**Riesgos / notas técnicas conocidas:**
- No cambiar el significado de ninguna columna/total ya existente — este sprint solo agrega visibilidad de
  un dato que Sprint 23 ya calcula correctamente, no debe alterar ningún número ya mostrado hoy.
- Verificar que el PDF/Word de una liquidación con sobrepago real, generado antes de este sprint, se pueda
  seguir regenerando desde su `AuditLog` (Sprint 9) y ahora sí muestre el saldo a favor correctamente — el
  dato ya está en el snapshot histórico gracias al fix de deserialización del Sprint 23, así que no hace
  falta ningún backfill.

**Definición de Hecho:**
- Test de reporte que liquide un expediente con un sobrepago real y confirme que el PDF/Word generado
  incluye el saldo a favor, con el monto exacto.
- Test de GUI que confirme que `ResultadoLiquidacionView` muestra el saldo a favor cuando `total_saldo_a_favor() > 0`, y no muestra nada (ni una fila vacía) cuando es cero.
- Suite completa en verde.

**Cierre de implementación (2026-08-09):** Completado. Ver
`docs/superpowers/plans/2026-08-09-sprint46-saldo-a-favor-visible.md`. `ReportSummaryBuilder.build_summary()`
agrega la clave `"saldo_a_favor"` al resumen solo cuando `total_saldo_a_favor() > 0` (ausente por completo
del diccionario cuando es cero); `ReportTableBuilder.build_matrix()` expone `saldo_a_favor` por fila.
`pdf.py`/`word.py` muestran la línea del resumen y la columna de cronología condicionadas a la presencia de
la clave, sin romper el layout de las 6 áreas cuando no hay sobrepago. `ResultadoLiquidacionView` muestra el
mismo dato, oculto por completo (ni una fila vacía) cuando es cero. Confirmado que la reconstrucción desde
`AuditLog` (Sprint 9) no requirió backfill: `serialization.py` ya deserializaba `saldo_a_favor` desde el
Sprint 23. Puramente de reportes/presentación, no se tocó `LiquidationCore`/`AllocationEngine`; ningún total
ya existente cambió de valor. Suite completa en verde (970 tests tras este sprint).

---

## Sprint 47 — Recalcular liquidaciones históricas afectadas por las correcciones del Sprint 30 ✅ Completado

**Prioridad sugerida:** Media-alta si hay liquidaciones reales ya entregadas a un juzgado o cliente con los
valores antiguos; baja si el uso hasta ahora fue solo de prueba/desarrollo.

**Depende de:** Sprint 30 (ya completado — las dos correcciones de cómputo que este sprint evalúa
recalcular) y Sprint 9 (motor de auditoría, que es la fuente de verdad de qué liquidaciones existen y con
qué parámetros se generaron).

**Contexto:** el Sprint 30 (cerrado 2026-08-04) corrigió dos cómputos de fecha/conteo confirmados como
incorrectos por el despacho — `fecha_interrupcion_efectiva` (prescripción, ahora fecha-a-fecha real en vez
de `<= 365` días) y el conteo de días de prestaciones sociales en `LaboralStrategy.liquidar` (ahora
inclusivo sobre base comercial de 360 días). Esos cambios afectan el resultado numérico de cualquier
liquidación calculada **de ahora en adelante**, pero **por diseño explícito no tocaron ninguna liquidación
ya guardada** en `bastium.db` — el Sprint 30 documentó el riesgo pero dejó la decisión de si recalcular el
histórico fuera de su alcance.

**Hallazgos:**
- No existe hoy ningún script en `scripts/` que identifique qué `AuditLog`/liquidaciones guardadas
  quedaron calculadas con la lógica vieja (pre-Sprint-30) para poder distinguirlas de las nuevas.
- Recalcular una liquidación ya entregada (a un juzgado, a un cliente) no es solo un cambio de dato — puede
  tener implicación legal/práctica real (un documento ya presentado con un valor, y ahora otro valor
  "correcto" para el mismo periodo). Esto es una decisión de negocio/legal, no una decisión técnica.

**Decisión de diseño a tomar con el usuario antes de codificar (no arrancar sin esa validación, mismo
patrón que exigieron los Sprints 13/16/20/41):**
- ¿Se recalculan todas las liquidaciones históricas afectadas, solo las de expedientes todavía activos, o
  ninguna (dejar el histórico tal como se calculó en su momento, y que solo las liquidaciones nuevas usen
  la lógica corregida)?
- Si se recalculan: ¿se sobrescribe el registro existente, o se guarda como una liquidación nueva
  vinculada a la anterior (para no perder el rastro de auditoría de "qué se le entregó a quién y cuándo")?
- ¿Hace falta notificar a alguien (cliente, juzgado) si un valor ya entregado cambia?

**Código nuevo a crear (una vez tomada la decisión):**
- Script en `scripts/` que identifique, vía `AuditLog`, las liquidaciones afectadas por cualquiera de los
  dos cómputos del Sprint 30 (comparando fecha de cálculo original contra la fecha del commit de la
  corrección).
- Mecanismo de recálculo/regeneración según lo que decida el usuario arriba, con su propio registro de
  auditoría (no perder el historial de qué cambió y por qué).

**Definición de Hecho:**
- Confirmación explícita del usuario sobre el alcance del recálculo, documentada aquí, antes de tocar
  código.
- Si se decide recalcular: test que verifique que una liquidación histórica sintética con la lógica vieja
  se identifica y recalcula correctamente, preservando el rastro de auditoría original.
- Suite completa en verde.

**Seguimiento (2026-08-09):** el usuario pidió posponer la decisión de alcance por ahora. La pregunta
central para el despacho (¿hay alguna liquidación ya entregada con la lógica vieja de prescripción/
prestaciones sociales? y si la hay, ¿se recalcula toda o solo expedientes activos?) ya quedó redactada en
`Preguntas-Para-Abogado-Abiertas.md`, sección "Sprint 47", junto con el mecanismo técnico ya decidido para
cuando se retome (liquidación nueva vinculada a la anterior, no sobrescribir; flag de notificación manual
visible en el expediente). Este sprint sigue bloqueado hasta esa respuesta.

**Respuesta recibida (2026-08-13):** el despacho confirmó que SÍ existen liquidaciones entregadas con la
lógica defectuosa y que es obligatorio recalcular (principio de primacía de la realidad, Art. 53 CP), con
un protocolo detallado según el estado procesal de cada expediente (activo → recálculo obligatorio con
memorial de actualización; presentado en juzgado/CPACA → memorial de corrección de error aritmético; cosa
juzgada → NO recalcular). También exige un flag "OBSOLETO - REQUIERE RECÁLCULO", un log de diferencias
numérico, priorización por cercanía de prescripción, y adoptar la Sentencia SL138-2024 (días calendario
reales) como estándar del módulo de densidad pensional. Detalle completo en
`Preguntas-Para-Abogado-Respondidas.md`, sección Sprint 47. Nada de esto está construido — es un sprint de
implementación grande (script de identificación vía `AuditLog`, generación de los 2 tipos de memorial, log
de diferencias, y verificar si `LaboralStrategy` ya cumple SL138-2024 tras el Sprint 30 o necesita un ajuste
adicional).

**Cierre de implementación, parte A (2026-08-14, commits `3147d62`/`5eb57bd`):** script de
identificación/marcado de liquidaciones afectadas vía `AuditLog` (`app/services/recalculo_historico.py`,
`scripts/recalcular_historicas_sprint30.py`), generación de los 2 memoriales del protocolo
(`app/engine/reports/memoriales.py`) y log de diferencias numérico, todos construidos; corrección de code
review aplicó el enforcer de nunca-recalcular-cosa-juzgada dentro de la capa de escritura.

**Cierre de implementación, parte B (2026-08-18):** confirmado el último punto pendiente —
"Estandarización pensional" (Sentencia SL138-2024). `calcular_densidad_semanas`
(`app/engine/labor/ibl.py`) ya usaba días calendario reales (365/366) desde que se creó en el Sprint 17 —
**no** la base comercial de 360 días — así que **no requirió ningún cambio de código**. Es una función
aislada sin conectar a `LaboralStrategy` ni a la GUI (misma nota del Sprint 3 sobre el módulo pensional), por
lo que tampoco hay liquidaciones ya guardadas afectadas por este punto ni una fecha de corte nueva que
agregar al script de recálculo del Sprint 47a. El test que ya existía,
`tests/engine/labor/test_ibl.py::test_densidad_semanas_calendario_real_vs_ano_comercial_360`, pina este
comportamiento explícitamente (caso que cruza un año bisiesto: 57 semanas en calendario real vs. 56 bajo año
comercial de 360, documentando la diferencia). La base de 360 días de `LaboralStrategy.liquidar`
(prestaciones sociales) no se tocó — sigue siendo la correcta para ese rubro distinto, por diseño del
Sprint 3/30. Suite completa en verde (1258 passed).

---

## Sprint 48 — Limpiar la deuda de `ruff` preexistente y agregar el chequeo de lint al pipeline de CI ✅ Completado

**Prioridad sugerida:** Baja-media — housekeeping, no afecta comportamiento, pero cierra un hueco real de
la red de seguridad de CI que el Sprint 28 dejó documentado a propósito.

**Depende de:** Sprint 28 (CI/CD — el pipeline de GitHub Actions ya existe y corre `pytest`; este sprint
solo le agrega el paso de lint una vez que el repo esté limpio).

**Contexto:** el commit `5931b97` ("chore: configurar ruff como linter/formatter...") adoptó `ruff` como
linter/formatter del proyecto (`pyproject.toml`, reglas `E`/`F`/`I`/`UP`/`B`, line-length 99) justo antes
del arranque de los Sprints 26-30, pero no limpió todo el código existente de una vez — quedaron ~400
errores preexistentes repartidos por el repo (confirmado al cierre de cada uno de los Sprints 26-30: cada
uno verificó que no introdujo errores *nuevos*, pero ninguno tocó la deuda preexistente por estar fuera de
su alcance individual). El Sprint 28, al armar el pipeline de CI, decidió deliberadamente **no** incluir
`ruff check` como paso — lo documentó como que agregarlo haría fallar la primera corrida de CI sin que sea
culpa de ningún cambio nuevo.

**Hallazgos:**
- `ruff check .` sobre el repo completo (post-Sprint-30) reporta 400 errores, mayoritariamente `E501`
  (línea demasiado larga) y `E402` (import fuera de orden), concentrados en archivos de test más viejos que
  el commit que adoptó `ruff`.
- Sin un paso de lint en CI, un commit nuevo puede seguir agregando código que no respeta el estilo del
  repo sin que nada lo marque — el pipeline de CI del Sprint 28 solo protege contra romper tests, no contra
  degradar el estilo.

**Código nuevo a crear:**
- Limpiar (o suprimir explícitamente con justificación, si algún caso no vale la pena tocar) los ~400
  errores preexistentes, archivo por archivo o por categoría de regla.
- Agregar un paso `ruff check .` al workflow de GitHub Actions creado en el Sprint 28
  (`.github/workflows/ci.yml`), una vez que el repo esté limpio.

**Alcance explícitamente excluido:**
- No cambiar reglas de `ruff` ni relajar `pyproject.toml` para "hacer trampa" y que la deuda desaparezca
  sin limpiarla — el objetivo es limpiar el código, no bajar el estándar.

**Definición de Hecho:**
- `ruff check .` sobre el repo completo devuelve cero errores.
- El pipeline de CI incluye `ruff check .` como paso obligatorio y falla si alguien reintroduce una
  violación.
- Suite completa en verde (la limpieza de lint no debe cambiar comportamiento).

**Cierre de implementación (2026-08-09):** Completado. Ver
`docs/superpowers/plans/2026-08-09-sprint48-ruff-cleanup-ci.md`. Conteo real al arrancar: 447 errores (no
~400, el número subió por los Sprints 36-45 recientes), desglosados en `E501` (411, la gran mayoría),
`E402` (13), `B905`/`B011`/`UP042` (14, resueltos por `--unsafe-fixes` revisado caso por caso), `I001` (3),
`B904`/`E741` (4) y `B008` (1). Limpieza por categoría sin cambiar comportamiento: `ruff format .` resolvió
la mayoría de `E501`, las f-strings/literales que el formatter no reenvuelve se dividieron a mano; los 13
`E402` eran imports agregados a mitad de archivos de test grandes sin razón intencional, movidos al tope;
`B904` con `raise ... from err` para preservar el traceback al traducir excepciones internas a excepciones
de dominio; `B008` resuelto con un singleton de módulo (`Rate` es `frozen dataclass`, no cambia
comportamiento); `E741` renombrando la variable ambigua `l`. `ruff check .` agregado como paso obligatorio
en `.github/workflows/ci.yml`, antes de `pytest`. Al mezclar a `main` aparecieron 13 errores adicionales de
código de los Sprints 46/50 (creado después de que este branch arrancara, nunca antes limpiado) — corregidos
en el mismo commit del merge. `ruff check .` → **0 errores** en todo el repo. Suite completa en verde (984
tests tras el merge final), mismo conteo que antes de la limpieza.

---

## Sprint 49 — Bug de UI: los botones "Volver"/"Inicio" reaparecen visibles tras el primer render de la ventana ✅ Completado

**Prioridad sugerida:** Media — bug real y reproducible en cada arranque de la app, pero de bajo impacto
funcional (los botones funcionan igual, solo aparecen visibles cuando no deberían).

**Depende de:** Nada — corrige código ya existente (el intento de fix vía `showEvent()` es anterior al
Sprint 26).

**Contexto (hallazgo de QA visual durante el cierre de los Sprints 31-35, 2026-08-06):** al hacer la
verificación visual manual explícitamente pendiente en los planes de los Sprints 31/32/35 (lanzando la app
real con un script standalone, sin `pytest-qt`), se confirmó que `MainWindow.boton_volver` y
`MainWindow.boton_inicio` — que deberían estar ocultos al arrancar la app (pantalla inicial, sin
historial) — aparecen visibles en el primer render real de la ventana, a pesar de que `showEvent()` ya
llama a `_actualizar_botones_navegacion()` explícitamente para corregir justo este síntoma (ver el
comentario ya existente en ese método, que describe el mismo problema).

**Hallazgos (reproducido con un script que imita el arranque real de `main.py`, sin `pytest-qt`):**
- `window.show()` deja `boton_volver.isVisible()` y `boton_inicio.isVisible()` en `False` (correcto)
  inmediatamente después de llamarse.
- El primer `app.processEvents()` posterior — que ocurre de forma natural en el bucle de eventos real de
  `main.py` (`app.exec()`) pero que la suite de tests actual nunca ejerce después de `show()` — hace que
  ambos vuelvan a `True`, y el estado incorrecto persiste en llamadas posteriores (no es un parpadeo de un
  solo frame).
- **Confirmado que el bug es preexistente, no introducido por los Sprints 31-35:** se reproduce igual en
  el commit `5931b97` (anterior al Sprint 31, sin tema visual ni breadcrumb ni dashboard). El comentario ya
  existente en `showEvent()` sugiere que se intentó corregir este mismo síntoma antes, pero el fix solo
  cubre el instante síncrono de `showEvent()`, no un evento adicional en cola que `QToolBar` dispara
  después (posible causa: un reset asíncrono al agregar widgets vía `addWidget()`, o el primer
  `polish()`/`repolish()` del stylesheet — hace falta investigar la causa raíz exacta).
- La suite de tests existente (`test_botones_navegacion_ocultos_en_pagina_inicial`,
  `tests/views/test_main_window.py`) no detecta el bug porque llama `window.show()` y verifica
  `isVisible()` inmediatamente, sin ceder el control al bucle de eventos (`qtbot.wait(...)` o
  `app.processEvents()`) — el test pasa porque nunca llega al punto donde el síntoma se manifiesta.

**Código nuevo a crear:**
- Investigar la causa raíz exacta (revisar si `QToolBar` dispara el reset de visibilidad vía un evento en
  cola al agregar action widgets, o si es un efecto del primer `polish()` del stylesheet del Sprint 31).
- Corregir de forma que la visibilidad correcta sobreviva al menos un ciclo completo del bucle de eventos
  después de `show()` — candidato: reconectar `_actualizar_botones_navegacion()` a través de
  `QTimer.singleShot(0, self._actualizar_botones_navegacion)` dentro de `showEvent()`, o investigar si fijar
  la visibilidad sobre `QAction` (`QToolBar.actions()`) en vez de sobre el `QPushButton` directamente evita
  el reset.
- Actualizar `test_botones_navegacion_ocultos_en_pagina_inicial` (y cualquier otro test de
  `tests/views/test_main_window.py` que dependa de la visibilidad de estos botones tras `show()`) para
  ceder el control al bucle de eventos (`qtbot.wait(0)`/`app.processEvents()`) después de `show()`, de
  forma que ejerza el mismo camino que la app real — así, si el bug reaparece, el test lo atrapa.

**Alcance explícitamente excluido:**
- No se propone rediseñar la barra de navegación (ya cubierta por el Sprint 32) — es un fix puntual de
  timing/visibilidad sobre código ya existente.

**Definición de Hecho:**
- Un script que reproduce el arranque real de la app (`show()` + `processEvents()`, sin `pytest-qt`)
  confirma que `boton_volver`/`boton_inicio` permanecen ocultos en la pantalla inicial.
- `test_botones_navegacion_ocultos_en_pagina_inicial` actualizado para ejercer el mismo camino de
  ejecución y sigue en verde.
- Suite completa en verde.

**Cierre de implementación (2026-08-09):** Completado. Ver
`docs/superpowers/plans/2026-08-09-sprint49-botones-navegacion-reaparecen.md`. Causa raíz confirmada:
`QToolBar` resetea a `True` la visibilidad de widgets agregados vía `addWidget()` en un evento de layout
adicional que el bucle de eventos real dispara después de `show()` (`QToolBarLayout.performLayout()`) — el
fix anterior vía `showEvent()` solo cubría el instante síncrono. Solución elegida: migrar
`boton_volver`/`boton_inicio`/`boton_parametros` de `QPushButton`+`addWidget()` a `QAction`+`addAction()`,
que `QToolBarLayout` sí respeta de forma consistente. Reproducción independiente confirmada con `qtbot.wait(1)`
(no `qtbot.wait(0)`, que resultó ser un no-op en la versión de pytest-qt instalada) y con un script
standalone (`app.exec()` real). **Superado por el Sprint 50** (mezclado después): el sidebar de navegación
reemplaza `QToolBar` por completo para estos botones, así que el bug deja de aplicar por construcción —
verificado con el test de regresión de este sprint corriendo en verde de forma estable (8/8) sobre la
estructura final combinada, no por suposición. Suite completa en verde tras el merge final.

---

## Sprint 50 — Mejoras de personalización y presentación diferidas de los Sprints 31-33 (modo oscuro, sidebar, gráficas del dashboard) ✅ Completado

**Prioridad sugerida:** Baja — ninguno de los 3 puntos es un bug ni un gap funcional; son mejoras
explícitamente diferidas por decisión de diseño al cerrar los Sprints 31, 32 y 33, agrupadas aquí para que
no se pierdan.

**Depende de:** Nada técnicamente. Se beneficia de que los Sprints 31 (tema/paleta), 32 (navegación) y 33
(dashboard) ya estén cerrados — lo están, desde 2026-08-06.

**Contexto:** al cerrar los Sprints 31-35 se identificaron 3 mejoras que cada sprint dejó explícitamente
fuera de su propio alcance, con la intención de revisarlas después. Ninguna tenía un sprint propio que las
recogiera — este sprint corrige ese hueco documental agrupándolas:

1. **Modo oscuro/claro** — el "Alcance explícitamente excluido" del Sprint 31 decía "ver Sprint 37 para
   otras mejoras de personalización, si se decide agregar un modo oscuro en el futuro sería un sprint
   propio". **Corrección:** el Sprint 37 ("Comportamiento de ventana y accesibilidad de teclado"), ya
   escrito, **no menciona modo oscuro en ningún punto** — cubre persistencia de geometría de ventana y
   orden de tabulación, nada de tema visual. La referencia cruzada del Sprint 31 apuntaba a un lugar que no
   existía. Si se decide implementarlo: requiere una segunda paleta completa en
   `app/core/theme_colors.py` (o una estructura de temas intercambiable) y un mecanismo para alternar el
   `.qss` cargado en `app/core/apariencia.py::aplicar_tema()` en caliente.
2. **Sidebar de navegación completo** — el Sprint 32 decidió explícitamente mantener el `QToolBar`
   superior enriquecido en vez de construir un sidebar, justificado en que 5 pantallas (hoy: Dashboard,
   Expedientes, Detalle, Resultado, Parámetros) no lo ameritan. Revisar esta decisión si un sprint futuro
   agrega una sexta pantalla o introduce sub-secciones jerárquicas dentro de un expediente.
3. **Gráficas/visualizaciones en el Dashboard** — el Sprint 33 excluyó explícitamente cualquier gráfica
   (ej. con `matplotlib`, hoy huérfano de uso real según el Sprint 27) del Dashboard, dejándolo con datos
   tabulares/listas simples. Evaluar agregar una gráfica (ej. expedientes por área, o evolución de
   liquidaciones en el tiempo) una vez que el Dashboard base (ya construido) se valide como útil en uso
   real.

**Código nuevo a crear:** ninguno todavía — este sprint es un placeholder de seguimiento. Antes de
codificar cualquiera de los 3 puntos, confirmar con el usuario cuál (si alguno) vale la pena priorizar,
igual que se hizo con decisiones de diseño anteriores (Sprints 13/16/20/41).

**Definición de Hecho:** no aplica todavía — este sprint se cierra dividiéndose en sprints concretos (uno
por punto que el usuario decida priorizar) el día que se retome, no completando los 3 de una vez.

**Cierre de implementación (2026-08-09):** Completado. Ver
`docs/superpowers/plans/2026-08-09-sprint50-modo-oscuro-sidebar-graficas.md`. El usuario, consultado
directamente, decidió implementar los 3 puntos en esta misma ronda (en orden: modo oscuro → sidebar →
gráficas), en vez de priorizar uno solo o posponer — decisión distinta a la prevista originalmente en este
placeholder, documentada aquí para que quede el rastro de por qué se completaron los 3 de una vez.
1. **Modo oscuro/claro:** `app/core/theme_colors_dark.py` + `resources/theme_dark.qss` (misma paleta de
   marca burdeos, luminancia invertida). `construir_paleta()`/`aplicar_tema()` (`app/core/apariencia.py`)
   parametrizados por modo; persistencia vía `QSettings` (`app/core/settings.py::crear_settings()`,
   extraído del patrón del Sprint 37 para no duplicarlo). Checkbox "Modo oscuro" en `ParametrosView`
   alterna el tema en caliente sin reiniciar la app. Referencia cruzada rota del Sprint 31 (apuntaba al
   Sprint 37) corregida.
2. **Sidebar de navegación:** reemplaza el `QToolBar` superior del Sprint 32 por un panel lateral
   (`QWidget`/`QSplitter`), mismos nombres de atributo, sin romper tests existentes. Como efecto
   secundario deseable, elimina por construcción el bug de visibilidad que corregía el Sprint 49
   (`QToolBar.addWidget()`) — verificado con evidencia (el test de regresión del Sprint 49 en verde), no
   por suposición.
3. **Gráficas del Dashboard:** `FigureCanvasQTAgg` (matplotlib, ya en `requirements.txt` sin uso real
   desde el Sprint 27) embebido junto a la tabla de conteo por área existente — la complementa, no la
   reemplaza. Colores resueltos según el modo de tema activo.
Suite completa en verde (984 tests tras el merge final combinado con el Sprint 49).

---

## Sprint 51 — Migración automática de esquema y datos al arrancar la app ✅ Completado

**Prioridad sugerida:** Alta — bloqueaba el uso real de la app para el usuario (crash al abrir, y el motor
de cálculo entero sin parámetros legales sembrados).

**Depende de:** Nada técnicamente, pero es la causa raíz de un bug reportado en producción tras cerrar los
Sprints 31-35: `sqlite3.OperationalError: no such column: obligaciones.costas_tipo_proceso` al abrir
`main.py`, porque el Dashboard nuevo (Sprint 33) es la primera pantalla que carga *todas* las obligaciones
de *todos* los expedientes al arrancar.

**Contexto (reporte del usuario, 2026-08-06):** al correr `python main.py` la app crasheaba con un
traceback completo de SQLAlchemy terminando en `no such column: obligaciones.costas_tipo_proceso`.

**Hallazgos (auditoría completa de esquema, verificada leyendo la `bastium.db` real del usuario):**
1. El proyecto no usa Alembic — cada sprint que agrega una columna/índice trae su propio script
   idempotente en `scripts/migrate_*.py` (9 scripts: Sprints 8, 12, 15, 16, 18, 19, 20, 25, y el de
   `parametros_legales`), pero **nada los invoca automáticamente** — dependían de que alguien los
   recordara correr a mano, y `README.md` solo documentaba 4 de los 9 (huecos ya existían en la propia
   documentación).
2. Diff completo del esquema real de la `bastium.db` del usuario contra el modelo actual
   (`database/models.py`, las 6 tablas): la tabla `obligaciones` le faltaban 5 columnas
   (`costas_tipo_proceso`, `costas_instancia` del Sprint 18; `interes_sobre_capital_indexado` del Sprint
   20; `anatocismo_demanda_judicial`, `anatocismo_fecha_acuerdo` del Sprint 19) — exactamente los 3
   scripts que nunca se corrieron. Las otras 5 tablas coincidían.
3. **Hallazgo más grave que el bug reportado:** la tabla `parametros_legales` tenía **0 filas**. El script
   `scripts/migrate_parametros_legales.py` (que siembra las 39 claves de tasas/topes/plazos legales que
   `get_parametro()` usa en casi todos los motores: intereses, usura, prescripción, seguridad social,
   sanciones tributarias) tampoco se había corrido nunca. El Dashboard captura
   `ParametroNoDisponibleError` con gracia (Sprint 33), pero cualquier liquidación real habría fallado con
   esa misma excepción sin capturar en el motor — el software estaba, en la práctica, inutilizable para su
   propósito principal, no solo con el Dashboard roto.
4. Este patrón (una `bastium.db` existente que se queda atrás del modelo) le pasaría exactamente igual a
   **cualquiera que clone el repositorio y ya tuviera una `bastium.db` de una versión anterior** — y, de
   forma más sutil, incluso a un clon completamente nuevo, porque nada garantizaba que
   `migrate_parametros_legales.py` se corriera antes del primer uso real.

**Código nuevo a crear:**
- `database/database.py::aplicar_migraciones_pendientes(db_path=None)`: importa y ejecuta, en orden y con
  imports diferidos (evita import circular con `scripts/migrate_parametros_legales.py`, que importa
  `init_db` de este mismo módulo), los 9 scripts de migración existentes — cada uno ya verifica con
  `PRAGMA table_info`/`PRAGMA index_list` antes de alterar, así que correrlos de más en una base ya al día
  es gratis (una consulta, no un `ALTER TABLE`).
- `main.py`: llama a `aplicar_migraciones_pendientes()` justo después de `init_db()`, antes de crear
  `MainWindow` — ningún paso manual, ni para una `bastium.db` vieja ni para una recién creada.
- `tests/database/test_migrations.py` (5 tests nuevos): agrega columnas faltantes a un esquema viejo
  reproducido con SQL crudo, siembra `parametros_legales` (39 claves), es idempotente, agrega los 4
  índices de rendimiento, y un test de regresión directo que reproduce el crash exacto del Dashboard
  contra un esquema viejo y confirma que ya no lanza `OperationalError`.

**Aplicado sobre la `bastium.db` real del usuario (2026-08-06):** backup previo
(`bastium.db.bak-20260806193037`), migración aplicada, verificado que el expediente y la obligación que
ya tenía cargados siguen intactos (mismo `id`/contenido antes y después), esquema final coincide
exactamente con el modelo en las 6 tablas, `parametros_legales` sembrada (39 claves, 683 filas incluyendo
las series históricas de SMLMV/IPC/IBC/UVT), y se reprodujo el arranque real de `main.py` contra esa misma
base confirmando que ya no crashea.

**Alcance explícitamente excluido:**
- No se migró a Alembic — se mantiene el patrón de scripts idempotentes ya establecido en el proyecto,
  solo se automatizó su invocación. Adoptar una herramienta de migraciones formal, si se justifica más
  adelante, es un sprint aparte.
- Los 9 scripts individuales en `scripts/migrate_*.py` no se borraron — siguen siendo válidos para
  correrse de forma aislada o para auditar qué cambió en cada sprint; `README.md` se actualizó para dejar
  claro que ya no hace falta correrlos a mano.

**Definición de Hecho:**
- `python main.py` arranca sin errores contra una `bastium.db` de cualquier sprint anterior, sin ningún
  paso manual.
- Suite completa en verde, incluidos los 5 tests nuevos de `tests/database/test_migrations.py`.
- La `bastium.db` real del usuario quedó migrada, con sus datos existentes intactos y un backup previo.

---

## Sprint 52 — Bug de integridad: `aplicar_migraciones_pendientes` ignora `db_path` al sembrar `parametros_legales` ✅ Completado

**Prioridad sugerida:** Alta — es un bug en la propia infraestructura de migraciones que el Sprint 51
construyó para evitar exactamente este tipo de inconsistencia de datos. Hoy no afecta al usuario final
(`main.py` siempre llama a `aplicar_migraciones_pendientes()` sin argumentos, así que en producción todo
apunta a la misma `bastium.db`), pero contamina la suite de tests como efecto colateral y es una trampa
para cualquier uso futuro del parámetro `db_path` (backups, pruebas de integración con otra base, etc.).

**Depende de:** Sprint 51 (ya completado) — bug encontrado en su propia implementación durante esta
auditoría técnica transversal (barrido automático + agentes en paralelo + verificación manual).

**Hallazgos (auditoría 2026-08-10, reproducido de forma aislada, sin modificar la `bastium.db` real):**
1. `database/database.py::aplicar_migraciones_pendientes(db_path=None)` (línea 79) llama a
   `migrar_parametros_legales()` sin ningún argumento, mientras que las otras 10 llamadas de la misma
   función (líneas 69-78) sí reciben `ruta` explícitamente.
2. `scripts/migrate_parametros_legales.py::migrar()` es el único de los 11 scripts de migración que no
   acepta un parámetro de ruta: usa `init_db()` y `session_module.get_session()`, ambos atados al `engine`
   global de `database/database.py`, construido una sola vez al importar el módulo a partir de
   `_resolve_db_path()` (variable de entorno `BASTIUM_DB_PATH` o, por defecto, la `bastium.db` real en la
   raíz del repo) — nunca a la ruta que reciba `aplicar_migraciones_pendientes`.
3. **Reproducción confirmada:** se creó una base de datos temporal nueva con el esquema completo
   (`Base.metadata.create_all`) y se llamó a `aplicar_migraciones_pendientes(db_tmp)` directamente, sin
   parchear el engine global. Resultado: la tabla `parametros_legales` de `db_tmp` quedó con **0 filas**
   tras la migración (debería tener 39 claves, como confirma
   `test_aplicar_migraciones_pendientes_siembra_parametros_legales`), mientras que la `bastium.db` real del
   proyecto no cambió su conteo de filas (683 antes y después) porque ya estaba sembrada — confirmando que
   la siembra se ejecuta contra el engine global, no contra `db_tmp`.
4. **Efecto colateral ya presente en la suite de tests:** de los 6 tests de `tests/database/test_migrations.py`
   que llaman a `aplicar_migraciones_pendientes(db_path)`, 3 lo hacen **sin** parchear el engine global
   (`test_aplicar_migraciones_pendientes_agrega_las_columnas_faltantes_de_obligaciones`,
   `test_aplicar_migraciones_pendientes_agrega_es_smmlv`,
   `test_aplicar_migraciones_pendientes_agrega_los_indices_de_rendimiento`), a diferencia de los otros 2
   (`test_aplicar_migraciones_pendientes_siembra_parametros_legales`,
   `test_aplicar_migraciones_pendientes_es_idempotente`), que sí lo hacen vía el helper
   `_apuntar_session_module_a(engine, monkeypatch)` — precisamente para poder verificar la siembra, lo que
   confirma que este comportamiento ya era conocido implícitamente al escribir esos 2 tests, pero no se
   generalizó al resto ni se corrigió en el código de producción. Como consecuencia, cada corrida de
   `pytest` ejecuta `migrar_parametros_legales()` contra la `bastium.db` real del proyecto como efecto
   secundario no buscado en esos 3 tests. Hoy es inofensivo porque la siembra es idempotente y la base real
   ya tiene las 39 claves (verificado: 683 filas antes y después de correr la suite completa), pero un test
   que usa `tmp_path` no debería, bajo ninguna circunstancia, escribir en un archivo fuera de `tmp_path`.
5. **Impacto potencial futuro:** cualquier funcionalidad que dependa de que `db_path` aísle completamente
   la operación (p. ej. un comando de administración "restaurar backup y migrar", o una prueba de
   integración contra una base distinta a la real) dejaría la base destino con `parametros_legales` vacía,
   reproduciendo exactamente el bug original que motivó el Sprint 51 (`ParametroNoDisponibleError` en
   cualquier liquidación real) — solo que ahora silenciosamente, porque `aplicar_migraciones_pendientes`
   no lanza ningún error ni avisa que la siembra fue a otro lado.

**Código nuevo a crear:**
- `scripts/migrate_parametros_legales.py::migrar(db_path: Path | None = None)`: aceptar el mismo parámetro
  que los otros 10 scripts; cuando se reciba una ruta, operar contra esa ruta en vez de contra
  `init_db()`/`get_session()` globales (un engine/sesión SQLAlchemy ad hoc apuntando a `db_path`, o
  `sqlite3` crudo si se prefiere seguir el patrón de los scripts de esquema — a decidir según cuánto del
  código ORM existente de `migrar()` conviene conservar).
- `database/database.py` línea 79: pasar `ruta` a `migrar_parametros_legales(ruta)`.
- Actualizar los 3 tests de `test_migrations.py` listados en el hallazgo 4 para que parcheen el engine
  global igual que los otros 2 (o, mejor, para que ya no necesiten hacerlo porque `migrar()` respeta
  `db_path` directamente).
- Test de regresión nuevo: llamar `aplicar_migraciones_pendientes(db_tmp)` **sin** monkeypatch del engine
  global y verificar que `db_tmp` queda con las 39 claves de `parametros_legales` — hoy este test no existe
  y por eso el bug pasó inadvertido en el propio Sprint 51.

**Alcance explícitamente excluido:**
- No se propone migrar a Alembic ni cambiar el patrón general de scripts idempotentes (decisión ya tomada
  en el Sprint 51) — es un fix puntual de un script que rompe el contrato de `db_path` que los otros 10 sí
  cumplen.

**Definición de Hecho:**
- `aplicar_migraciones_pendientes(db_path)` deja sembrada `parametros_legales` en `db_path`, no en el
  engine global, verificado con un test que NO parchea `database.database.engine`.
- Los 3 tests de `test_migrations.py` que hoy tocan la `bastium.db` real como efecto secundario dejan de
  hacerlo.
- Suite completa en verde.

**Cierre de implementación (2026-08-11):** Completado, vía Subagent-Driven Development (implementador +
revisor de spec + revisor de calidad, con re-revisión tras cada corrección) sobre un worktree aislado.
`scripts/migrate_parametros_legales.py::migrar()` ahora acepta `db_path: Path | None = None`; cuando se
recibe una ruta, usa un engine SQLAlchemy ad hoc apuntando exactamente a esa ruta (nunca al engine global)
para sembrar `parametros_legales`, con la creación del engine dentro del `try/finally` para evitar fugas si
`create_all` falla. **Se conservó la rama sin `db_path`** (contra la sugerencia inicial de eliminarla): el
implementador verificó empíricamente que eliminarla rompía 42 tests, porque `tests/conftest.py` tiene una
fixture `autouse` (`_db_en_memoria_por_defecto`) que depende de que `migrar()` sin argumentos use el engine
global — no es código muerto, es un segundo camino real usado por la suite. Se igualó `autoflush=False` en
ambas ramas (inconsistencia real detectada en revisión) y se corrigió una fuga de conexiones SQLite en los
tests nuevos (`_sesion_para` ahora es un context manager que dispone el engine). Test de regresión nuevo
(`test_aplicar_migraciones_pendientes_siembra_parametros_legales_en_db_path`) confirmado que detecta el bug
original (falla contra el código pre-fix). Suite completa en verde (985 tests tras este sprint).

---

## Sprint 53 — Rendimiento: patrón N+1 de consultas en el Dashboard ✅ Completado

**Prioridad sugerida:** Media — no es un bug de resultado (el Dashboard sigue mostrando los datos
correctos), pero repite exactamente el patrón que el Sprint 25 ya identificó y corrigió para
`HonorariosStrategy`, y se dispara en la primera pantalla que ve el usuario en cada arranque de la app
(Sprint 51: el Dashboard es la primera pantalla que carga todas las obligaciones de todos los expedientes).

**Depende de:** Sprint 25 (ya completado) — introduce `cache_de_liquidacion()`, el mecanismo que este
sprint debe reutilizar. Sprint 33 (Dashboard, ya completado) — es donde se introdujo el patrón sin esa
protección.

**Hallazgos (auditoría técnica 2026-08-10, confirmados leyendo el código real):**
1. `app/views/dashboard.py::_refrescar_alertas_vencimiento` (líneas 168-197) recorre cada obligación no
   pagada de cada expediente y llama a `calcular_prescripcion(obligacion.fecha_origen, TipoAccion.EJECUTIVA)`
   (`app/engine/temporal/prescripcion.py:51`), que internamente llama a `get_parametro(...)`
   (`app/services/parametro_service.py:348`). Sin un bloque `cache_de_liquidacion()` activo, `get_parametro`
   cae en `_resolver_fila` (línea 299), que abre y cierra una sesión SQLAlchemy nueva por cada llamada. Con
   N obligaciones no pagadas, esto son N sesiones/consultas idénticas a `parametros_legales` en cada
   refresco del Dashboard — el mismo patrón que el Sprint 25 (hallazgo 2) corrigió para `HonorariosStrategy`
   introduciendo `cache_de_liquidacion()` en `app/services/area_strategy.py`, pero el Dashboard (construido
   después, en el Sprint 33) no lo usa.
2. `app/views/dashboard.py::_refrescar_actividad_reciente` (líneas 210-219) llama a
   `historial_de_expediente(session, expediente.id)` (`app/engine/audit/service.py`) una vez por expediente
   para armar el top-10 de actividad reciente, en vez de una sola consulta con
   `AuditLog.expediente_id.in_([...])`. Reutiliza la sesión ya abierta (a diferencia del punto 1, no abre
   una sesión nueva por llamada), pero sigue siendo un round-trip a SQLite por expediente.
3. No hay ningún test de regresión de rendimiento que hubiera atrapado esto: `tests/performance/` solo
   contiene `__init__.py` (vacía), y `scripts/benchmark_motor_rendimiento.py` (único benchmark del repo,
   ejecutado en esta auditoría: 0.038s / 0.288s en sus dos escenarios) no cubre pantallas de la GUI, solo el
   motor de liquidación puro.

**Código nuevo a crear:**
- Envolver el cuerpo de `_refrescar_alertas_vencimiento` en `with cache_de_liquidacion():` (mismo patrón
  que ya usan las 6 `AreaStrategy` en `app/services/area_strategy.py`).
- Reemplazar el bucle de `_refrescar_actividad_reciente` por una sola consulta que traiga los `AuditLog` de
  todos los `expediente.id` de una vez (`.filter(AuditLog.expediente_id.in_(...))`), ordenando y recortando
  a `MAX_LIQUIDACIONES_RECIENTES` en Python igual que hoy.
- Test nuevo (en el archivo de tests de `DashboardView` existente) que cree varios expedientes con
  obligaciones no pagadas y verifique, contando invocaciones a `session_module.get_session` (o con
  `sqlalchemy.event.listen` sobre `before_cursor_execute`), que `refrescar()` no abre una sesión adicional
  por cada obligación.

**Alcance explícitamente excluido:**
- No se propone paginar ni limitar el número de expedientes que carga el Dashboard (el conteo por área ya
  es agregado, no por fila, y el top-10 de actividad ya usa `MAX_LIQUIDACIONES_RECIENTES`) — es un fix
  puntual de las dos consultas en bucle, no un rediseño del Dashboard.

**Definición de Hecho:**
- Un test confirma que `DashboardView.refrescar()` no abre una sesión SQLAlchemy nueva por cada obligación
  no pagada.
- Suite completa en verde.

**Cierre de implementación (2026-08-11):** Completado, vía Subagent-Driven Development. El primer intento
(envolver `_refrescar_alertas_vencimiento` en `cache_de_liquidacion()`, tal como sugería este sprint)
resultó **insuficiente**: la revisión de spec verificó empíricamente que `PRESCRIPCION_EJECUTIVA_MESES`
usa `ModoResolucion.ABIERTO` y que la cache de `get_parametro` indexa por `(clave, fecha)` exacta — con
`fecha_origen` distinta por obligación (el caso real, no el caso de prueba con fechas repetidas), el fix
seguía abriendo 9 sesiones para 8 obligaciones, sin mejora. Fix final: `precargar_parametro(clave)` nueva
en `app/services/parametro_service.py`, que trae **todas** las filas de una clave en una sola consulta
(vía `historial(clave)`) y las guarda en un `ContextVar` (`_filas_precargadas_activa`) scoped por
`cache_de_liquidacion()`; `get_parametro` resuelve en memoria contra esas filas (`_resolver_entre_filas`,
que replica exactamente el criterio de `_resolver_fila` para los 3 `ModoResolucion`) en vez de golpear la
base por cada fecha distinta. Verificado con 8 obligaciones de `fecha_origen` distintas: 2 sesiones, no 9.
Un test de equivalencia parametrizado (`test_resolver_fila_y_resolver_entre_filas_dan_el_mismo_resultado`,
11 casos incluido un empate de `vigente_desde` con `creado_en` distinto) protege contra que ambos caminos
diverjan en el futuro — confirmado que detecta una rotura deliberada antes de aceptarse. `_refrescar_actividad_reciente`
también se corrigió con una consulta `IN` batched (`historial_de_expedientes` nueva en
`app/engine/audit/service.py`). Ningún otro caller de `get_parametro`/`cache_de_liquidacion()` (las 6
`AreaStrategy`, `historical_index.py`) cambia de comportamiento. Suite completa en verde (1006 tests tras
este sprint).

---

## Sprint 54 — Corrección de documentación desactualizada tras los Sprints 41, 42, 50 y 51 ✅ Completado

**Prioridad sugerida:** Media-alta — dos de los hallazgos (prescripción/caducidad y navegación) le dicen al
usuario final algo que ya no es cierto sobre una función jurídicamente relevante y sobre cómo usar la app;
el resto es housekeeping de mantenibilidad/documentación. Mismo patrón que el Sprint 29.

**Depende de:** Nada — es documentación pura. Los sprints referenciados (41, 42, 50, 51) ya están
completados; esto solo actualiza los documentos que quedaron atrás.

**Hallazgos (auditoría de documentación 2026-08-10, con 2 agentes en paralelo + verificación manual de
cada uno releyendo el archivo real, mismo método que los Sprints 23-30):**

1. **`docs/GUIA_USUARIO.md` describe una navegación que ya no existe.** Las secciones ~186-206 describen
   una "barra de navegación" superior con tres botones — cierto hasta el Sprint 32, pero el Sprint 50
   reemplazó ese `QToolBar` por un sidebar lateral fijo (`app/views/main_window.py`, líneas 115-159,
   `QSplitter`). `README.md` y `docs/local/GUIA_PRESENTACION.md` ya reflejan el cambio; `docs/GUIA_USUARIO.md`
   no.
2. **`docs/GUIA_USUARIO.md` no menciona el modo oscuro ni la gráfica del Dashboard** (ambos del Sprint 50)
   en ninguna sección — el checkbox "Modo oscuro" de `ParametrosView` y la gráfica de expedientes por área
   no tienen ninguna instrucción de uso en la guía del usuario final.
3. **`docs/GUIA_USUARIO.md` afirma, en la sección de prescripción/caducidad, que el motor "todavía no está
   conectado a ninguna pantalla ni bloquea la liquidación de un expediente"**, citando el Sprint 7 — pero
   el Sprint 42 ya lo conectó a `UniversalLiquidationService.liquidar()`, marcando obligaciones prescritas
   con advertencia visual en pantalla, PDF y Word (esto ya lo documenta correctamente el propio
   `README.md`). A diferencia de otros sprints (que sí registran "README.md y docs/GUIA_USUARIO.md
   actualizados" al cerrar), el cierre del Sprint 42 no lo hizo — es la sección más urgente de corregir de
   las 3, porque hoy le dice al usuario algo jurídicamente incorrecto sobre el propio software.
4. **`docs/specifications/07_motor_juridico_familia.md` describe `CivilFamiliaStrategy` sin el reajuste
   anual del Sprint 41.** La sección "Componentes" (líneas 14-17) solo describe obligaciones Puntuales (un
   `Event` de capital) y Recurrentes expandidas mensualmente con tasa fija — no menciona el reajuste anual
   SMMLV/IPC ni las cuotas individuales seleccionables para abono que el Sprint 41 (calificado en este
   mismo documento como "gap grande de alcance") agregó vía `app/services/reajuste_anual.py`.
5. **`docs/specifications/03_motor_indexacion.md` afirma que la UVT "sigue sin cargar"**, contradiciendo
   dos sprints ya completados (Sprint 5 y Sprint 14) y el propio README, que documenta su uso en producción
   (`app/engine/indexation/historical_index.py::_UVT_POR_ANIO`, datos 2006-2026). Solo la afirmación sobre
   UVR sigue siendo cierta — mezclarla con la de UVT en la misma frase hace que la afirmación completa
   induzca a error.
6. **`CONTRIBUTING.md` documenta una convención de commits incompleta.** Solo lista
   `feat:`/`fix:`/`docs:`/`test:`/`chore:`; el historial real del repo usa además `merge:` (31 commits),
   `refactor:` (10), `perf:` (5), `style:` (1) y `build:` (1) — `merge:` en particular es el prefijo de
   cierre de casi todos los sprints recientes (ej. `d157a04 merge: Sprint 50...`) y no aparece documentado.
7. **`CHANGELOG.md`, sección `## [Unreleased]`, párrafo resumen**: enumera los Sprints 31-50 pero omite el
   Sprint 51 (migración automática) — sí aparece correctamente más abajo, en el detalle `### Added`/
   `### Fixed`, pero no en el resumen inicial.

**Código nuevo a crear:** ninguno — son ediciones de texto en los 5 documentos listados arriba (ningún
archivo `.py` involucrado).

**Alcance explícitamente excluido:**
- No se reescribe `docs/GUIA_USUARIO.md` completa, solo las 3 secciones desactualizadas identificadas.
- No se re-audita el resto de `docs/superpowers/plans/`/`specs/` (son actas históricas de planeación de
  cada sprint, no documentación viva) más allá de lo ya encontrado aquí.

**Definición de Hecho:**
- Las 3 secciones de `docs/GUIA_USUARIO.md` reflejan el sidebar, el modo oscuro/gráfica y la conexión real
  de prescripción/caducidad.
- `docs/specifications/07_motor_juridico_familia.md` y `03_motor_indexacion.md` corregidos.
- `CONTRIBUTING.md` lista los prefijos de commit realmente usados en el repo.
- `CHANGELOG.md` menciona el Sprint 51 en el párrafo resumen de `[Unreleased]`.

**Cierre de implementación (2026-08-11):** Completado. Las 3 secciones de `docs/GUIA_USUARIO.md` (tour de
navegación, sección de Parámetros, sección 8) ahora describen el sidebar del Sprint 50 en vez del
`QToolBar` viejo, documentan el modo oscuro y la gráfica del Dashboard, y corrigen la afirmación sobre
prescripción/caducidad (era la más urgente: le decía al usuario algo jurídicamente incorrecto sobre el
propio software). `docs/specifications/07_motor_juridico_familia.md` ya describe el reajuste anual
SMMLV/IPC del Sprint 41; `03_motor_indexacion.md` ya no dice que la UVT "sigue sin cargar" (solo la UVR
sigue pendiente). `CONTRIBUTING.md` lista los 5 prefijos de commit que faltaban (`merge:`, `refactor:`,
`perf:`, `style:`, `build:`), verificados contra el historial real. Verificado que no queda ninguna mención
residual de "barra superior"/`QToolBar` como estado actual en `GUIA_USUARIO.md`, y que ningún encabezado
cambió (anclas internas intactas).

---

## Sprint 55 — 3 bugs de UI en el Dashboard: gráfica con colores viejos, etiquetas apretadas y tabla editable ✅ Completado

**Prioridad sugerida:** Media — ninguno rompe un cálculo ni pierde datos, pero los 3 son visibles de inmediato
en la primera pantalla que ve el usuario en cada arranque, y el tercero (tabla editable) puede hacerle creer
al usuario que cambió el conteo real de expedientes por área cuando no es así.

**Depende de:** Sprint 50 (modo oscuro/gráfica del Dashboard, ya completado) y Sprint 53 (ya completado en
esta misma ronda) — comparte archivo (`app/views/dashboard.py`) con el Sprint 53, pero ningún cambio de
ese sprint se superpone con estos 3 hallazgos (áreas de código distintas dentro del mismo archivo).

**Contexto:** reportado directamente por el usuario tras probar la app con modo oscuro activo. Los 3
hallazgos se verificaron leyendo el código real antes de escribir este sprint (no se asumió nada):

**Hallazgos (verificados 2026-08-10/11):**
1. **La gráfica del Dashboard se queda con los colores del tema anterior si se vuelve con el botón
   "Volver" en vez de "Inicio".** `MainWindow._ir_inicio()` (`app/views/main_window.py:237-240`) llama
   `self.dashboard_page.refrescar()` antes de mostrar la página — por eso entrar por "Inicio" sí repinta la
   gráfica con los colores correctos. `MainWindow._volver()` (líneas 231-235) NO llama a `refrescar()`, solo
   cambia de página (`show_page`). Si el usuario cambia el tema (modo oscuro) estando en otra pantalla y
   vuelve al Dashboard con "Volver" (no con "Inicio"), `_refrescar_grafica_por_area()` nunca se vuelve a
   ejecutar, así que la gráfica queda pintada con `theme_colors`/`theme_colors_dark` (el módulo resuelto en
   `apariencia.cargar_modo_tema()` la última vez que corrió) del modo viejo, mientras el resto de la
   interfaz (sidebar, tablas, QSS) ya cambió porque esos sí son estilos de Qt aplicados en caliente por
   `aplicar_tema()`. Mismo tipo de "refresco parcial al navegar" que ya causó el bug del Sprint 49.
2. **Las etiquetas de la gráfica de barras se ven apretadas/superpuestas y no se reacomodan al
   redimensionar la ventana.** `_refrescar_grafica_por_area()` (`app/views/dashboard.py:142-166`) llama
   `self.figura_por_area.tight_layout()` una sola vez, dentro del método que solo se ejecuta cuando cambian
   los datos (`refrescar()`). `FigureCanvasQTAgg` sí redimensiona el área de dibujo cuando cambia el tamaño
   del widget (es un `QWidget` normal dentro del layout), pero el espaciado/tamaño de fuente calculado por
   `tight_layout()` para las 6 etiquetas de área (`Civil / Familia`, `Comercial`, `Laboral`,
   `Sancionatorio`, `Honorarios / Litigio`, `Tributario`) no se recalcula — no hay ningún manejador de
   `resizeEvent` conectado al canvas ni a la vista.
3. **La tabla "Expedientes por área" del Dashboard es editable con doble clic, y el cambio no se revierte
   ni persiste — solo confunde.** Ninguna de las 3 tablas de `app/views/dashboard.py`
   (`tabla_por_area`, `tabla_alertas`, `tabla_actividad`) llama a
   `setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)`, a diferencia de las tablas de solo
   lectura en `app/views/configuracion.py` (líneas 153, 180) y `app/views/expediente_detalle.py` (línea
   187), que sí lo hacen — es una omisión respecto al patrón ya establecido en el resto del proyecto, no
   una decisión de diseño. Confirmado que doble-clic en una celda de "Expedientes" permite escribir
   cualquier texto; el valor editado desaparece en el siguiente `refrescar()` (no se guarda en la base de
   datos), pero mientras tanto el usuario ve un número que no representa nada real.

**Código nuevo a crear:**
- `app/views/main_window.py::_volver()`: llamar a `self.dashboard_page.refrescar()` cuando la página de
  destino sea `"dashboard"` (igual que ya hace `_ir_inicio()`), o refactorizar para que ambos métodos
  compartan la misma lógica de "entrar al dashboard" sin duplicar la llamada a `refrescar()`. Ojo: no
  refresques incondicionalmente en cada `_volver()` sin importar la página destino — sería una regresión de
  rendimiento/comportamiento en las otras pantallas del historial de navegación.
- `app/views/dashboard.py`: conectar un manejador al evento de resize del canvas/vista (ej. sobrescribir
  `resizeEvent` en `DashboardView` o conectar a la señal de resize del `QWidget` contenedor) que vuelva a
  llamar `self.figura_por_area.tight_layout()` + `self.canvas_por_area.draw_idle()` — sin re-consultar la
  base de datos ni recalcular los datos, solo el layout de la figura ya dibujada. Cuidado con no crear un
  bucle de resize-triggers-redibujo-triggers-resize; usar el patrón estándar de matplotlib para esto
  (`figure.canvas.mpl_connect('resize_event', ...)` o el equivalente de Qt).
- `app/views/dashboard.py::__init__`: agregar `self.tabla_por_area.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)`
  a las 3 tablas (`tabla_por_area`, `tabla_alertas`, `tabla_actividad`), mismo patrón que
  `configuracion.py`/`expediente_detalle.py`.
- Tests nuevos en `tests/views/test_dashboard.py` y/o `tests/views/test_main_window.py`: uno que verifique
  que `_volver()` hacia "dashboard" deja la gráfica con los colores del modo de tema activo (no el de la
  última vez que se llamó `refrescar()` antes de cambiar de tema); uno que confirme que las 3 tablas del
  Dashboard tienen `NoEditTriggers`. El caso de resize puede quedar como test manual/QA si no hay un patrón
  ya establecido en el repo para testear resize de matplotlib embebido (revisar `tests/views/` antes de
  decidir).

**Alcance explícitamente excluido:**
- No se propone ningún cambio a los diálogos `QDialog` sin botones de minimizar/maximizar (ej.
  `HistorialParametroDialog`) — es un hallazgo distinto, en un archivo distinto (`configuracion.py`), y
  potencialmente aplica a otros diálogos del proyecto además de Parámetros. Queda para un sprint aparte.
- No se rediseña la gráfica (tipo de gráfico, tamaño, colores) — solo se corrige que refleje el tema activo
  y que no se superponga al redimensionar.

**Definición de Hecho:**
- Cambiar el tema y volver al Dashboard con "Volver" deja la gráfica con los colores correctos, verificado
  con un test (no solo con "Inicio", que ya funcionaba).
- Redimensionar la ventana no dobla producir superposición de etiquetas en la gráfica (verificación manual
  aceptable si no hay patrón de test para esto en el repo).
- Ninguna celda de las 3 tablas del Dashboard es editable.
- Suite completa en verde.

**Cierre de implementación (2026-08-11):** Completado, vía Subagent-Driven Development.
`MainWindow._volver()` ahora llama a `dashboard_page.refrescar()` cuando la página destino del historial
es `"dashboard"` (mismo patrón que ya usaba `_ir_inicio()`), sin refrescar incondicionalmente para otras
páginas. Las 3 tablas del Dashboard tienen `setEditTriggers(NoEditTriggers)`. El fix del reacomodo de la
gráfica al redimensionar **cambió de enfoque durante la revisión de calidad**: el primer intento
(`installEventFilter` sobre `canvas_por_area`, interceptando `QEvent.Type.Resize`) resultó tener un bug de
orden de eventos verificado empíricamente — Qt despacha los event filters *antes* de que
`FigureCanvasQT.resizeEvent()` (código nativo de matplotlib) sincronice el tamaño de la figura, así que
`tight_layout()` calculaba los márgenes para el tamaño VIEJO del widget, reproduciendo el bug original
justo en el caso más común (un salto grande de tamaño, ej. maximizar la ventana). Corregido enganchando al
sistema de eventos propio de matplotlib (`canvas_por_area.mpl_connect("resize_event", ...)`, que sí corre
después de que el tamaño ya está sincronizado) en vez de interceptar el evento crudo de Qt — más idiomático
además para un canvas de matplotlib embebido. Verificado con un test que captura la geometría exacta en el
momento en que `tight_layout()` corre, confirmado que detecta el bug (falla contra la implementación vieja,
pasa contra la nueva). Suite completa en verde (1010 tests tras este sprint).

---

## Sprint 56 — Diálogos redimensionables/maximizables (los 7 QDialog del proyecto) ✅ Completado

**Prioridad sugerida:** Media — no bloquea ningún flujo, pero `HistorialParametroDialog` puede mostrar
cientos de filas (IPC: 683) sin ninguna forma cómoda de agrandar la ventana.

**Depende de:** Nada.

**Contexto:** reportado por el usuario (captura de `HistorialParametroDialog` solo con botón de cerrar).
Confirmado que los 7 `QDialog` del proyecto (`AbonoFormDialog`, `ParametroFormDialog`,
`HistorialParametroDialog`, `DescuentoLaboralFormDialog`, `EventoLaboralFormDialog`,
`ExpedienteFormDialog`, `ObligacionFormDialog`) usan los flags por defecto de Qt en Windows (solo
cerrar). El usuario decidió aplicar el fix a los 7 por consistencia, no solo al que más lo necesita hoy.

**Código nuevo a crear:** ver
`docs/superpowers/plans/2026-08-11-parametros-ux-dialogos-crud.md`, Sprint 56 — helper
`hacer_redimensionable(dialog)` nuevo en `app/views/form_utils.py`, aplicado en el `__init__` de los 7
diálogos.

**Alcance explícitamente excluido:**
- No cambia el tamaño inicial ni el contenido de ningún diálogo — solo agrega la capacidad de
  redimensionar/maximizar/minimizar.

**Definición de Hecho:**
- Los 7 `QDialog` tienen los flags de minimizar/maximizar activos, verificado con test.
- Suite completa en verde.

**Cierre de implementación (2026-08-12):** Completado, vía Subagent-Driven Development sobre un worktree
aislado. Helper `hacer_redimensionable(dialog)` en `app/views/form_utils.py` (`|=` sobre los flags
existentes, no los reemplaza), aplicado justo después de `super().__init__(parent)` en los 7 diálogos.
Test parametrizado nuevo (`tests/views/test_dialogos_redimensionables.py`) verificado con prueba de
mutación (comentar la llamada en un diálogo hace fallar solo su caso). Suite completa en verde (1018
tests tras este sprint).

---

## Sprint 57 — Parámetros: columnas Área y Unidad por fila ✅ Completado

**Prioridad sugerida:** Media-alta — el usuario no puede saber hoy a qué área del derecho corresponde
cada uno de los 39 parámetros legales, ni la unidad del valor que está viendo.

**Depende de:** Nada técnicamente.

**Contexto:** reportado por el usuario. Brainstorming completo con el usuario (ver
`docs/superpowers/specs/2026-08-11-parametros-ux-dialogos-crud-design.md`), incluyendo una investigación
completa de las 39 claves de `CATALOGO_PARAMETROS` para determinar su área real (21 confirmadas por
código en ejecución, 18 sin ningún botón real que las dispare todavía — motores construidos pero no
conectados, ver Sprint 61).

**Decisiones tomadas con el usuario (no re-derivar):**
- Área y unidad se guardan **por fila** en `parametros_legales` (no como metadato fijo en Python) y
  **no son editables** después de creada la fila — ni doble clic ni ningún otro mecanismo.
- Multi-área: casillas de verificación en el formulario, guardadas como lista (JSON), no como texto con
  separador.
- Las 18 claves sin wiring reciben la mejor propuesta por nombre/artículo legal igual que el resto; se
  corrige si hace falta cuando se conecten en el Sprint 61.
- `CADUCIDAD_ENRIQUECIMIENTO_SIN_CAUSA_MESES` recibe ambas áreas (Civil/Familia y Comercial) por ser
  doctrina aplicable en las dos, sin evidencia de código que incline a una sola.

**Código nuevo a crear:** ver el plan (Sprint 57, 5 tareas) y la spec (tabla completa de área/unidad por
las 39 claves, sección "Tabla de área propuesta por clave") para el detalle exacto — no se repite aquí
para no desincronizar dos copias de la misma tabla:
- `database/models.py::ParametroLegal`: columnas nuevas `areas_derecho`/`unidad`.
- `app/services/areas_parametro.py` (nuevo): `serializar_areas`/`deserializar_areas`.
- `app/services/parametro_service.py::agregar_valor()`: exige `areas_derecho`/`unidad`.
- `scripts/migrate_parametros_area_unidad.py` (nuevo): agrega las columnas y completa las 683 filas
  existentes según la tabla de la spec; registrado en `aplicar_migraciones_pendientes()`.
- `app/views/configuracion.py`: `ParametroFormDialog` con casillas de área (preseleccionadas según la
  clave) y campo de unidad; `ParametrosView.tabla` con las 2 columnas nuevas.

**Alcance explícitamente excluido:**
- No se agrega ninguna forma de editar área/unidad de una fila ya creada.
- No se conecta ninguno de los 18 parámetros sin wiring a una pantalla real (Sprint 61).

**Definición de Hecho:**
- Las 683 filas existentes quedan migradas según la tabla de la spec, verificado con test.
- `ParametroFormDialog` exige área(s) y unidad para guardar.
- La tabla de Parámetros muestra las 2 columnas nuevas.
- Suite completa en verde.

**Cierre de implementación (2026-08-12):** Completado. Las columnas `areas_derecho`/`unidad` de
`ParametroLegal` quedaron **nullable a nivel SQLite** (contra el snippet literal del plan, pero siguiendo
el criterio que el propio plan ya anticipaba para la migración): la obligatoriedad real la exige
`agregar_valor()`, no una restricción `NOT NULL` de la columna — verificado que `NOT NULL` real rompía
172 casos en 17 archivos de test preexistentes que construyen `ParametroLegal` sin estos campos, y que
`aplicar_migraciones_pendientes()` siempre corre la siembra y el backfill en la misma llamada, así que
una fila nunca queda huérfana en producción. `AREA_UNIDAD_POR_CLAVE` (`app/services/areas_parametro.py`)
tiene un test que compara su conjunto de claves contra `CATALOGO_PARAMETROS` para que no puedan
desincronizarse en silencio. Tras una ronda de revisión, se agregó manejo defensivo en
`_texto_areas()` (degrada a "?" por celda en vez de tumbar toda la pantalla si algún día hay datos
corruptos) y `resizeColumnsToContents()` en la tabla. Suite completa en verde (1043 tests tras este
sprint).

**🔴 Bug real en producción, encontrado y corregido (2026-08-12):** tras fusionar los Sprints 56-60, el
usuario reportó que `python main.py` crasheaba con `sqlite3.OperationalError: no such column:
parametros_legales.areas_derecho` — su `bastium.db` real ya tenía `parametros_legales` sembrada (Sprint
51) pero nunca había corrido la migración de este sprint. Causa raíz: `migrar_parametros_legales()`
verifica si una clave ya está sembrada vía `session.query(ParametroLegal)` (ORM), y el modelo ya declara
`areas_derecho`/`unidad` como columnas mapeadas — SQLAlchemy siempre selecciona esas columnas sin importar
qué migración "lógica" esté corriendo. Como `migrar_parametros_legales()` corría ANTES que
`migrar_parametros_area_unidad()` (quien agrega esas columnas), cualquier `bastium.db` sembrada antes de
este sprint crasheaba al arrancar. **Este es exactamente el mismo tipo de bug de desincronización esquema/
ORM que motivó el Sprint 51 — y ninguna de las revisiones de spec/calidad/integración de los Sprints 56-60
lo detectó porque todos los tests construían el esquema desde cero con `Base.metadata.create_all()` (que
ya incluye las columnas nuevas), nunca simulando una base real que ya tenía datos sembrados por el código
ANTERIOR a este sprint.** Corregido llamando `migrar_parametros_area_unidad()` también ANTES de
`migrar_parametros_legales()` (además de la llamada ya existente después, necesaria para completar filas
recién sembradas en una `bastium.db` nueva) — es idempotente, llamarla dos veces es gratis. Test de
regresión agregado que reproduce el escenario exacto (esquema viejo + fila ya sembrada a mano) y confirma
que no crashea; verificado que falla contra el código anterior al fix. `bastium.db` real del usuario
migrada (backup previo `bastium.db.bak-20260812221510`), datos existentes verificados intactos.

---

## Sprint 58 — Parámetros: presentación inteligente (vigencia, IPC crudo vs. calculado, historial) ✅ Completado

**Prioridad sugerida:** Media.

**Depende de:** Sprint 57 (comparte `app/views/configuracion.py`, se implementa justo después).

**Contexto:** 3 hallazgos del usuario, cada uno investigado antes de diseñar la solución (ver spec):
1. "Vigente hasta" vacío es correcto para parámetros sin fecha de fin real (`ModoResolucion.ABIERTO`),
   pero engañoso para los que el gobierno fija año a año (`ANUAL_EXACTO`: SMLMV, IPC, UVT) — cada valor
   solo rige ese año calendario. Confirmado con un ejemplo concreto del usuario (SMLMV 2025 vs. 2026).
2. `IPC_INDICE_ACUMULADO` es el único de los 39 parámetros calculado con fórmula
   (`indice = indice_anterior * (1 + variacion_anual/100)`) a partir de una tabla cruda que hoy no se
   siembra en la base — solo el resultado. El usuario la consultó con el abogado y quiere ver ambos.
3. Parámetros con muchas filas históricas no tienen ninguna acción visible más allá de un doble clic no
   documentado para ver su historial completo.

**Código nuevo a crear:** ver el plan (Sprint 58, 4 tareas) y la spec (sección "Diseño" del Sprint 58)
para el código exacto de `vigencia_hasta_mostrar()`, la siembra de `IPC_VARIACION_ANUAL`, y el enlace
"Ver historial".

**Alcance explícitamente excluido:**
- Es una regla de presentación pura — no cambia ningún dato guardado ni ningún cálculo de liquidación
  (verificar con la suite completa, especialmente `tests/family/`, `tests/engine/` de indexación).
- El desglose crudo-vs-calculado es solo para IPC — confirmado con el usuario que hoy es el único
  parámetro con fórmula; el mecanismo (`CLAVE_CRUDA_DE`) queda genérico por si aparece otro caso a futuro.

**Definición de Hecho:**
- SMLMV/IPC/UVT muestran "31 de diciembre de {año}" en vez de vacío; el resto sin fecha de fin real
  muestra "Indefinido".
- El historial de IPC muestra la variación % anual cruda junto al índice, con la fórmula explicada.
- Cualquier clave con más de 1 fila tiene una acción visible para ver su historial.
- Suite completa en verde, sin cambios de resultado en ninguna liquidación.

**Cierre de implementación (2026-08-12):** Completado. `vigencia_hasta_mostrar()` aplicada tanto en
`HistorialParametroDialog` como en `ParametrosView.tabla` — esta última ganó una columna "Vigente hasta"
que no existía antes del sprint (el plan lo pedía así; confirmado con el usuario que es la interpretación
correcta). `IPC_VARIACION_ANUAL` sembrada (59 filas, script propio
`scripts/migrate_ipc_variacion_anual.py`) como la 40ª clave del catálogo — mecanismo `CLAVE_CRUDA_DE`
inicialmente genérico solo en el dato, no en la presentación (etiqueta/fórmula fijas de IPC en la UI); se
generalizó tras revisión a `_PRESENTACION_DATO_CRUDO` indexado por clave, con indexación directa que falla
ruidosamente (`KeyError`) si se agrega una clave cruda sin su presentación correspondiente. **Hallazgo de
la revisión final de integración de los 5 sprints**: `agregar_valor()` rechazaba `valor <= 0` para
`IPC_VARIACION_ANUAL`, que legítimamente puede ser 0% o negativa en un año de deflación — corregido con
`CLAVES_VALOR_PUEDE_SER_NO_POSITIVO`, un set explícito de excepción (hoy solo esa clave), sin tocar la
validación de las demás 39. Confirmado sin cambios de resultado en ninguna liquidación
(`tests/family/`+`tests/engine/` en verde). Suite completa en verde (1060 tests al cierre del sprint
propio, 1086 tras el fix de integración final).

---

## Sprint 59 — Tooltips ⓘ de ayuda en los 4 formularios principales ✅ Completado

**Prioridad sugerida:** Media.

**Depende de:** Nada técnicamente, pero comparte archivos con 57/58 (`configuracion.py`) — se
implementa después de esos dos.

**Contexto:** el usuario vio el ícono ⓘ en el campo "Tasa efectiva anual" de `ObligacionFormDialog`
(único campo, de ~15, que lo tiene hoy) y pidió el mismo patrón en el resto de ese formulario, más en
`ExpedienteFormDialog`, `AbonoFormDialog` y `ParametroFormDialog` — los 4 formularios principales de
captura de datos.

**Código nuevo a crear:** ver el plan (Sprint 59, 3 tareas) — extraer el helper privado ya existente en
`obligaciones.py` a `app/views/form_utils.py::agregar_ayuda()` (reutilizable), aplicarlo al resto de
campos no autoexplicativos de `ObligacionFormDialog`, y a los 3 formularios restantes.

**Alcance explícitamente excluido:**
- No se agregan tooltips a pantallas de solo lectura (listados, resultado de liquidación) — solo a los 4
  formularios de captura.
- Campos autoexplicativos (ej. "Concepto", texto libre) no reciben tooltip forzado.

**Definición de Hecho:**
- Los 4 formularios usan el helper compartido, sin ninguna implementación duplicada del ícono ⓘ.
- Cada campo no autoexplicativo de los 4 formularios tiene tooltip con ejemplo.
- Suite completa en verde.

**Cierre de implementación (2026-08-12):** Completado. Al leer el código real se confirmó que la premisa
del hallazgo estaba parcialmente desactualizada: 16 de ~24 campos de `ObligacionFormDialog` (y 6 de
`ExpedienteFormDialog`) ya tenían `setToolTip()` simple de los Sprints 34/44 — solo "Tasa efectiva anual"
tenía el ícono ⓘ visible. Se aplicaron tooltips nuevos solo a los campos que genuinamente no tenían
ninguno, dejando cobertura completa en los 4 formularios. `_envolver_campo_con_iconos` (que mezclaba el
ícono de ayuda con el de advertencia de validación) se separó en responsabilidades limpias; el ícono de
advertencia sigue funcionando sin importar el anidamiento porque su lookup es por widget, no por
jerarquía de contenedores. Suite completa en verde (1070 tests tras este sprint).

---

## Sprint 60 — Editar/eliminar Obligaciones y Abonos ✅ Completado

**Prioridad sugerida:** Alta — gap funcional real: hoy no hay forma de corregir un error de captura sin
recrear el expediente.

**Depende de:** Nada.

**Contexto:** el usuario notó, mientras probaba el flujo de captura, que `tabla_obligaciones` tiene
"Editar" (Sprint 44) pero no "Eliminar", y `tabla_abonos` no tiene ninguno de los dos.
`tabla_eventos_laborales` ya tiene ambos (Sprint 44, punto 4) — es el patrón de referencia. Confirmado
leyendo `database/models.py` que `Obligacion.abonos`/`.eventos_laborales`/`.descuentos_laborales` ya
tienen `cascade="all, delete-orphan"`, así que eliminar una obligación ya los borra automáticamente. El
único caso especial es `obligacion_padre_id` (cuotas generadas por reajuste anual, Sprint 41): no es una
`relationship()` de SQLAlchemy, así que no se borra sola — confirmado con el usuario que se elimina junto
con la obligación padre, sin bloquear la operación.

**Código nuevo a crear:** ver el plan (Sprint 60, 2 tareas) — columna "Eliminar" en `tabla_obligaciones`
(`_eliminar_obligacion`, con cascada explícita de cuotas hijas antes del padre); `abono_id` opcional en
`AbonoFormDialog` para editar; columnas "Editar"/"Eliminar" en `tabla_abonos`.

**Alcance explícitamente excluido:**
- No se agrega una papelera/deshacer — la eliminación es definitiva tras confirmar, mismo criterio que
  ya usa Eventos Laborales.

**Definición de Hecho:**
- `tabla_obligaciones` tiene "Editar" y "Eliminar" por fila; eliminar una obligación con cuotas hijas las
  elimina a todas en la misma operación, verificado con test.
- `tabla_abonos` tiene "Editar" y "Eliminar" por fila.
- Suite completa en verde.

**Cierre de implementación (2026-08-12):** Completado. `_eliminar_obligacion` sigue el código de
referencia del plan al pie de la letra: consulta y borra las cuotas hijas (`obligacion_padre_id`) antes
del padre, en la misma sesión/transacción; verificado con un test de integración real que genera cuotas
de verdad vía `generar_cuotas_mensuales` (Sprint 41) y confirma 0 filas residuales tras eliminar (padre +
5 cuotas + abonos + eventos laborales). Al agregar `abono_id` opcional a `AbonoFormDialog` se encontró y
corrigió un bug real independiente: la heurística de detección de sobrepago contaba doble el valor del
abono en edición (sumaba el monto viejo Y el nuevo). El primer test de este fix no ejercitaba el caso real
del bug (montos muy por debajo del límite) — corregido con un test que sí lo reproduce, verificado
revirtiendo el fix y confirmando que el test nuevo falla con el falso positivo exacto antes de restaurar
el código correcto. Suite completa en verde (1083 tests al cierre del sprint propio; ver Sprint 58 para el
fix de integración final que llevó el total a 1086).

**🔴 Segundo bug real en producción, encontrado y corregido (2026-08-12):** el usuario reportó
`sqlalchemy.orm.exc.UnmappedInstanceError: Class 'builtins.NoneType' is not mapped` al pulsar "Eliminar"
sobre un abono, repetido varias veces. Causa raíz: `_eliminar_obligacion` borra en cascada
`abonos`/`eventos_laborales`/`descuentos_laborales` en la base de datos
(`cascade="all, delete-orphan"`), pero solo llamaba `_refrescar_obligaciones()` — las otras 3 tablas se
quedaban mostrando filas fantasma con botones "Editar"/"Eliminar" todavía conectados a ids ya inexistentes;
un clic ahí hacía `session.get(...)` → `None` → `session.delete(None)` → crash. Ninguno de los 5 métodos
de editar/eliminar de `expediente_detalle.py` verificaba que la fila siguiera existiendo antes de operar.
El test que ya existía para esta cascada (`test_eliminar_obligacion_con_abonos_los_elimina_en_cascada`)
solo verificaba el estado de la base de datos, nunca el estado de la tabla en pantalla — por eso pasó la
revisión de spec/calidad/integración sin detectar el problema. Corregido: `_eliminar_obligacion` ahora
refresca las 4 tablas relacionadas, no solo la propia; se agregó verificación defensiva (aviso amigable en
vez de traceback) en los 5 métodos de editar/eliminar (`_eliminar_obligacion`, `_editar_abono`,
`_eliminar_abono`, `_editar_evento_laboral`, `_eliminar_evento_laboral`). 5 tests de regresión nuevos,
verificados fallando contra el código anterior con el mismo error exacto reportado. Suite completa en
verde (1092 tests).

**Nota (2026-08-13):** el usuario volvió a reportar como "novedad" que hace falta un botón de editar y
eliminar para obligaciones y abonos — ya está implementado exactamente en este sprint (cerrado un día
antes, 2026-08-12). Probablemente el reporte es de una build sin actualizar o de no haber notado los
botones en la tabla. No requiere trabajo nuevo; si al probarlo el botón sigue sin aparecer, es un bug de
regresión sobre este sprint, no un gap nuevo.

---

## Sprint 61 — Conectar los parámetros de prescripción/caducidad sin wiring a pantallas reales ✅ Completado

**Prioridad sugerida:** Baja-media — ninguno de los 18 parámetros afectados bloqueaba el uso actual de la
app (solo `PRESCRIPCION_EJECUTIVA_MESES`, el default de `UniversalLiquidationService`, estaba realmente
conectado antes de este sprint).

**Depende de:** Nada técnicamente, pero requería una conversación de alcance con el usuario antes de
codificar — mismo patrón que otros gaps grandes de este proyecto (Sprints 13/16/20/41).

**Contexto:** al investigar el Sprint 57 (área por parámetro) se confirmó que 18 de las 39 claves de
`CATALOGO_PARAMETROS` (12 de prescripción/caducidad no-ejecutiva + `CIVIL_ANNUAL_RATE`, más el uso
parcial de `IBC_CONSUMO_ORDINARIO`) tenían motores completos y probados
(`app/engine/temporal/prescripcion.py`, `app/engine/interest/legal_rates.py`) pero ningún botón de la
app los disparaba — solo se ejercitaban en tests. Este sprint quedó como placeholder hasta retomarlo con
el usuario.

**Decisión de diseño tomada con el usuario (2026-08-14, brainstorming antes de codificar):** campo
genérico único ("Tipo de acción/proceso") en el formulario de Obligación, en vez de 18 decisiones de
pantalla independientes; generalizar la alerta ya existente del Dashboard (antes solo EJECUTIVA) en vez
de construir una pantalla nueva; `CIVIL_ANNUAL_RATE` resuelto como fallback automático silencioso (sin
campo nuevo) cuando la tasa pactada se deja en 0. Diseño completo en
`docs/superpowers/specs/2026-08-14-sprint61-wiring-parametros-prescripcion-design.md`, plan de
implementación en `docs/superpowers/plans/2026-08-14-sprint61-wiring-parametros-prescripcion.md`.

**Código nuevo:**
- `scripts/migrate_tipo_accion_proceso.py` + columna `tipo_accion_proceso: str | None` en `Obligacion`
  (`database/models.py`).
- `app/services/areas_parametro.py::opciones_tipo_accion_proceso_por_area()`: unifica los 6 `TipoAccion`
  de prescripción y las 7 claves de `PLAZOS_CADUCIDAD_MESES_CONOCIDOS`, filtrado por área reutilizando
  `AREA_UNIDAD_POR_CLAVE` (Sprint 57). Import perezoso de `app.engine.temporal.prescripcion` para evitar
  un ciclo de imports con `parametro_service.py`.
- Combo "Tipo de acción/proceso" en `ObligacionFormDialog` (`app/views/obligaciones.py`), opcional,
  poblado una vez por área al construir el diálogo.
- `app/views/dashboard.py::_refrescar_alertas_vencimiento`: generalizada de EJECUTIVA fija a resolver
  prescripción o caducidad según `obligacion.tipo_accion_proceso` (EJECUTIVA por defecto si es `None`,
  mismo comportamiento que antes de este sprint).
- `CivilFamiliaStrategy._construir_rate_provider_obligacion` (`app/services/area_strategy.py`): usa
  `CIVIL_ANNUAL_RATE` cuando `tasa_efectiva_anual == 0`.

**Definición de Hecho:**
- Las 12 claves de prescripción/caducidad + `CIVIL_ANNUAL_RATE` son alcanzables desde una pantalla real.
- Ninguna obligación existente cambia de comportamiento sin que el usuario elija explícitamente el campo
  nuevo o deje la tasa en 0.
- Suite completa en verde.

**Cierre de implementación (2026-08-18):** Completado, vía `superpowers:subagent-driven-development` en
worktree dedicado (`worktree-sprints-75-61`, compartido con el Sprint 75 — mismo worktree por tocar ambos
`app/services/area_strategy.py`, ejecutados en secuencia, no en paralelo, para evitar conflictos). Al
correr la suite completa después de este sprint se encontró y corrigió una interacción real entre ambos:
los tests de `PagoPorRangoDialog` (Sprint 75) usaban `tasa_efectiva_anual=0.00` en cuotas de Civil/Familia
para que el ejemplo fuera determinístico, sin saber que el fallback de `CIVIL_ANNUAL_RATE` de este sprint
activaría una excepción capturada silenciosamente — corregido sembrando `CIVIL_ANNUAL_RATE=0.00` en esos
tests para preservar el mismo comportamiento (cero interés). Suite completa en verde (1208 passed),
`ruff check .` limpio (solo 3 errores `E501` preexistentes, ajenos a ambos sprints, confirmados con
`git log -S`). **Segundo hallazgo, al fusionar con `main`** (que en paralelo ya había integrado el
Sprint 43, indexación IPC en las 6 áreas): el Sprint 43 introdujo `AreaStrategy._tasa_civil_anual_pct`,
que confirma —contra `scripts/migrate_parametros_legales.py`, la fuente real de siembra— que
`CIVIL_ANNUAL_RATE` se guarda como **fracción** (`0.06`), no como porcentaje (`6.00`). El fallback de este
sprint leía `get_parametro("CIVIL_ANNUAL_RATE", ...)` directo y lo pasaba sin convertir a
`_rate_provider_tasa_plana` (que espera forma porcentual) — un error de unidades de 100× que el test propio
del sprint no detectó porque sembraba el parámetro con el valor equivocado (`6.00`), ocultándose a sí
mismo. Corregido reutilizando `_tasa_civil_anual_pct` (la conversión ×100 ya construida por el Sprint 43)
en vez de leer el parámetro directo; los tests se ajustaron al valor real sembrado por la fixture
compartida del archivo (`0.06`). Suite completa en verde tras la fusión (1319 passed, combinando ambos
branches), `ruff check .` limpio.

---

## Sprint 62 — Corregir referencias rotas tras mover Pendientes/Preguntas-Para-Abogado/SECURITY/PDF a docs/ ✅ Completado

**Prioridad sugerida:** Alta — hay ~130 archivos que citan la ruta vieja de estos 5 documentos; varios son
documentación viva que el usuario final (README, Guía de Usuario) o un colaborador (CONTRIBUTING, plantilla
de PR) sí llega a leer.

**Depende de:** Nada — el usuario ya movió los 5 archivos físicamente (`Pendientes.md`,
`Preguntas-Para-Abogado-Abiertas.md`, `Preguntas-Para-Abogado-Respondidas.md`, `SECURITY.md`,
`REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`, todos ahora en `docs/`). Este sprint solo
corrige las referencias que ese movimiento dejó rotas.

**Contexto:** grep exhaustivo confirmó referencias a las rutas viejas (raíz del repo) en:
`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `docs/GUIA_USUARIO.md`, `docs/local/GUIA_PRESENTACION.md`,
`.github/PULL_REQUEST_TEMPLATE.md`, los 7 `docs/specifications/*.md`, y ~30 archivos `.py` (comentarios
que citan estos documentos como referencia de contexto, ej. `app/core/constants.py`,
`app/services/area_strategy.py`, varios `app/engine/*`, y sus tests).

**Alcance explícitamente excluido:**
- `docs/superpowers/plans/*.md` y `docs/superpowers/specs/*.md` (~90 archivos): son actas históricas de
  planeación de cada sprint ya cerrado, no documentación viva — decisión ya tomada en el Sprint 54
  ("no se re-audita el resto de plans/specs... más allá de lo ya encontrado"), se mantiene aquí. Corregir
  esas ~90 referencias reescribiría historia que debe quedar tal como se escribió en su momento.

**Código nuevo a crear:** ninguno — son ediciones de texto (rutas). Reemplazar, en los archivos listados
arriba (documentación viva + `.py`), toda referencia a `Pendientes.md`/`Preguntas-Para-Abogado-*.md`/
`SECURITY.md`/`REQUERIMIENTOS DE CALCULO...pdf` en la raíz por la ruta `docs/...` correspondiente. Cuidado
con no duplicar el prefijo si algún archivo ya dice `docs/Pendientes.md` correctamente en algún lado.

**Definición de Hecho:**
- `grep` de las rutas viejas sobre los archivos en alcance (excluyendo `docs/superpowers/`) no devuelve
  ningún resultado.
- Los enlaces relativos desde `docs/GUIA_USUARIO.md`/`docs/local/GUIA_PRESENTACION.md` a los archivos
  movidos (ahora hermanos en el mismo `docs/`) usan rutas relativas correctas, no `docs/docs/...`.
- Suite completa en verde (no debería haber tests que dependan de estas rutas de documentación, pero se
  verifica).

**Cierre de implementación (2026-08-14):** Completado, vía `superpowers:subagent-driven-development` en
worktree dedicado (`worktree-sprints-71-18-62-63-13`). Reemplazadas 37 referencias al archivo viejo
`Preguntas-Para-Abogado.md` (nombre anterior a la división en Abiertas/Respondidas) por
`docs/Preguntas-Para-Abogado-Respondidas.md` en comentarios/docstrings de 20 archivos `.py` (10 en `app/`,
10 en `tests/`), verificando sprint por sprint que cada cita realmente corresponde a ese archivo. Las
referencias en `README.md`/`CONTRIBUTING.md`/`.github/PULL_REQUEST_TEMPLATE.md` ya usaban el prefijo
`docs/` correcto; los enlaces relativos dentro de `docs/GUIA_USUARIO.md` (hermanos en el mismo directorio)
se dejaron sin tocar por ya ser correctos. `docs/superpowers/plans/` y `docs/superpowers/specs/` excluidos
del alcance, sin tocar. La revisión final del lote completo (ver Sprint 71/18/13 abajo) encontró que este
cambio, al alargar las rutas citadas, empujó 13 líneas de comentario a superar el límite de 99 columnas de
`ruff` — corregido en el mismo lote con un simple reflow de texto, sin cambios de lógica. Suite completa en
verde (1162 passed), `ruff check .` limpio.

---

## Sprint 63 — Documentar en README/GUIA_USUARIO las funciones de los Sprints 52-60 ✅ Completado

**Prioridad sugerida:** Alta — viola la regla obligatoria que el propio `Pendientes.md` se puso al cerrar
cualquier sprint ("hay que actualizar README.md y docs/GUIA_USUARIO.md... nunca deben quedar
desactualizados"). Confirmado con grep que ninguna de estas funciones aparece documentada hoy.

**Depende de:** Nada.

**Contexto:** los Sprints 52-60 (auditoría técnica + Parámetros/diálogos/CRUD, 2026-08-10 a 2026-08-12)
agregaron funcionalidad real que el usuario final puede usar hoy, pero nunca se documentó:
- Columnas Área y Unidad en Parámetros, no editables tras crearse (Sprint 57).
- Vigencia "inteligente" e IPC con variación % cruda visible (Sprint 58).
- Tooltips ⓘ de ayuda en los 4 formularios principales de captura (Sprint 59).
- Editar/eliminar Obligaciones y Abonos, con cascada de cuotas hijas (Sprint 60).
- Los 7 diálogos del proyecto se pueden minimizar/maximizar/redimensionar (Sprint 56).
- Migración automática de esquema corregida para bases anteriores al Sprint 57, y refresco de tablas
  corregido al eliminar una obligación (2 bugs de producción encontrados y corregidos el 2026-08-12/13,
  ya documentados en `docs/Pendientes.md` Sprints 57/60 pero no en `CHANGELOG.md`).

**Código nuevo a crear:** ninguno — ediciones de texto en `README.md`, `docs/GUIA_USUARIO.md` y
`CHANGELOG.md`. En `GUIA_USUARIO.md`, seguir el estilo y nivel de detalle ya usado para funciones
similares (ej. la sección de Parámetros existente, la sección de navegación) — no reescribir el
documento completo, solo agregar/actualizar las secciones afectadas. En `CHANGELOG.md`, agregar entradas
`### Fixed` para los 2 bugs de producción del 2026-08-12/13 (`aplicar_migraciones_pendientes` fallaba en
bases anteriores al Sprint 57; eliminar una obligación no refrescaba abonos/eventos laborales), mismo
estilo que las entradas `Fixed` ya existentes.

**Alcance explícitamente excluido:**
- No se documenta el Sprint 61 (bloqueado, sin implementar todavía).
- No se tocan los `docs/specifications/*.md` (esos son specs técnicas de motores, no guía de usuario —
  fuera de alcance de este sprint específico).

**Definición de Hecho:**
- `README.md` y `docs/GUIA_USUARIO.md` mencionan las 5 funciones nuevas listadas arriba.
- `CHANGELOG.md` tiene entradas `Fixed` para los 2 bugs de producción.
- Suite completa en verde.

**Cierre de implementación (2026-08-13):** Completado — commits `4aa2236` ("docs: documentar en
README/GUIA_USUARIO las funciones de los Sprints 52-60") y `d6f16bf` (corrección de alcance sobre diálogos
redimensionables). `docs/GUIA_USUARIO.md` documenta Sprint 56 (§4, diálogos redimensionables/maximizables),
Sprint 57 (§5.14, columnas Área/Unidad), Sprint 58 (§5.14, "Vigente hasta" inteligente y desglose IPC
crudo-vs-calculado), Sprint 59 (§4, tooltips ⓘ) y Sprint 60 (§5.16 nueva, editar/eliminar obligación o
abono); `README.md` refleja lo mismo en su sección "Estado actual"; `CHANGELOG.md` con las 2 entradas
`Fixed` de los bugs de producción. Sprints 52/53 (internos) correctamente sin sección de usuario. Este
cierre quedó hecho antes de que arrancara el lote de los Sprints 62/71/18/13 (2026-08-14) — verificado que
sigue vigente y sin contenido duplicado.

---

## Sprint 64 — Reorganizar los backups de bastium.db en una carpeta backups/ ✅ Completado

**Prioridad sugerida:** Media — housekeeping puro, no afecta comportamiento de la app.

**Depende de:** Nada.

**Contexto:** 6 archivos `bastium.db.bak-*` acumulados en la raíz del repo desde julio (respaldos
manuales hechos antes de aplicar migraciones riesgosas, incluidos los 2 hotfixes del 2026-08-12). Ya están
en `.gitignore` (`*.db.bak-*`), así que no son un problema de control de versiones, pero sí de orden visual
en la raíz. Decisión tomada (sin preguntar, por ser no-destructiva y reversible): **no se borra ninguno**
— son la red de seguridad del usuario ante una migración que salga mal — se organizan en una carpeta
nueva.

**Código nuevo a crear:** ninguno — mover los 6 archivos `bastium.db.bak-*` (no `bastium.db` en sí, esa
sigue en la raíz, es la base activa) a una carpeta nueva `backups/` en la raíz del repo. Agregar
`backups/` a `.gitignore` (mismo patrón que `.venv/`/`.worktrees/`). Si `database/database.py` o algún
script tiene lógica que genera backups automáticos apuntando a la raíz, actualizarla para que apunte a
`backups/` (revisar primero si existe tal lógica automática, o si los 6 backups existentes son todos
manuales — en cuyo caso no hay código que tocar, solo mover archivos).

**Definición de Hecho:**
- Los 6 `bastium.db.bak-*` existentes viven en `backups/`, con su contenido intacto (mismo tamaño/hash).
- `bastium.db` (la base activa) sigue en la raíz, sin tocar.
- `backups/` está en `.gitignore`.
- Si existía lógica de backup automático, ahora escribe en `backups/`.

**Cierre de implementación (2026-08-13):** Completado. Solo había 5 `bastium.db.bak-*` en la raíz (no 6
— el conteo original incluía uno que ya no existía), todos manuales: no se encontró ninguna lógica de
backup automático en el código (`grep` sobre `*.py` sin resultados para `.bak-`/`db.bak`/`shutil.copy`
de `bastium.db`), así que no hubo código que actualizar. Los 5 archivos se movieron a `backups/` con
verificación de hash MD5 antes/después de cada uno (los 5 coinciden); `bastium.db` no se tocó. El
movimiento físico se hizo fuera de este worktree, directo en la raíz del repo principal, porque estos
archivos no están versionados y no existen en ninguna copia de git (ver commit de la convención en
`.gitignore`, hecho antes dentro de este worktree).

---

## Sprint 65 — Lanzador de doble clic "Iniciar BASTIUM.bat" ✅ Completado

**Prioridad sugerida:** Media-alta — el usuario (abogado, sin experiencia en terminal) reportó que
`.venv\Scripts\python.exe main.py` en una terminal no es intuitivo para el público real de la app.

**Depende de:** Nada.

**Contexto:** hoy la única forma documentada de abrir BASTIUM es abrir una terminal, navegar a la carpeta
del proyecto, y escribir la ruta completa del intérprete + `main.py`. Decisión tomada: en vez de un
"comando más fácil" para escribir en terminal (lo que el usuario sugirió textualmente), un archivo
`.bat` de doble clic es más simple todavía para el público real (un abogado) — no requiere abrir ninguna
terminal. Se puede seguir invocando desde una terminal también si se prefiere (un `.bat` acepta ambos
usos).

**Código nuevo a crear:**
- `Iniciar BASTIUM.bat` en la raíz del repo: cambia al directorio del script (`cd /d %~dp0`, para que
  funcione sin importar desde dónde se haga doble clic), corre `.venv\Scripts\python.exe main.py`, y si
  el proceso termina con código de error (ej. `.venv` no existe todavía, o una excepción no capturada),
  deja la ventana abierta con un mensaje (`pause`) en vez de cerrarse de inmediato — para que el usuario
  pueda leer el error y reportarlo, en vez de ver un parpadeo de consola vacío.
- Actualizar `README.md` y `docs/GUIA_USUARIO.md` (sección de cómo abrir la app) para mencionar el doble
  clic en `Iniciar BASTIUM.bat` como la forma recomendada, dejando el comando de terminal como alternativa
  para quien lo prefiera.

**Alcance explícitamente excluido:**
- No se empaqueta la app como un `.exe` standalone (ej. con PyInstaller) — eso es un cambio mucho más
  grande (empaquetado, firma, distribución) que no se pidió y no está en el alcance de este sprint.

**Definición de Hecho:**
- Doble clic en `Iniciar BASTIUM.bat` abre la app igual que el comando de terminal actual.
- Si el `.venv` no existe o `main.py` falla, la ventana de consola no se cierra sola — muestra el error.
- README/GUIA_USUARIO documentan el doble clic como forma recomendada de abrir la app.

**Cierre de implementación (2026-08-13):** Completado. `Iniciar BASTIUM.bat` cambia al directorio del
script con `cd /d %~dp0`, valida que `.venv\Scripts\python.exe` exista antes de intentar nada (mensaje
guiado hacia la sección de instalación si falta), corre `main.py`, y usa `pause` tanto en el caso de
`.venv` faltante como en el de un `errorlevel` distinto de 0 al salir — la ventana nunca se cierra sola
sin que el usuario alcance a leer el error. README.md (sección "Instalación rápida") y
`docs/GUIA_USUARIO.md` (sección 3, "Cómo iniciar el programa") documentan el doble clic como forma
recomendada, dejando el comando de terminal como alternativa.

---

## Sprint 66 — Reorganizar "Parametros" en "Configuraciones" con submenú Parámetros/Apariencia ✅ Completado

**Prioridad sugerida:** Media — mejora de organización de la navegación; no bloquea uso actual (la tabla
de parámetros y el interruptor de tema ya funcionaban, solo cambian de ubicación).

**Depende de:** Nada.

**Contexto:** el botón lateral "Parametros" (ícono de engranaje) navegaba directo a la tabla de parámetros
legales, que además alojaba el interruptor de modo oscuro/claro desde el Sprint 50 — el propio código
señalaba (comentario en `app/views/configuracion.py`) que esa ubicación era temporal, a la espera de que
el sidebar se reorganizara. El usuario pidió, mediante brainstorming con companion visual: renombrar el
botón a "Configuraciones", convertir esa pantalla en un contenedor con submenú lateral estilo Ajustes
(Parámetros, Apariencia, con espacio para más secciones futuras), y mover el interruptor de tema a la
nueva sección "Apariencia". Diseño completo en
`docs/superpowers/specs/2026-08-13-configuraciones-apariencia-design.md`, plan de implementación en
`docs/superpowers/plans/2026-08-13-configuraciones-apariencia.md`, ejecutado con
superpowers:subagent-driven-development en un worktree dedicado.

**Código nuevo a crear:**
- `app/views/apariencia.py` (nuevo): `AparienciaView`, con el `QCheckBox` "Modo oscuro" movido desde
  `ParametrosView`.
- `app/views/configuraciones.py` (nuevo): `ConfiguracionesView`, submenú lateral + panel de contenido que
  alterna entre `ParametrosView` (existente, sin el checkbox) y `AparienciaView`.
- `app/views/configuracion.py`: se quita el checkbox de tema y `_alternar_modo_tema` de `ParametrosView`.
- `app/views/main_window.py`: `boton_parametros`/`parametros_page` se renombran a
  `boton_configuraciones`/`configuraciones_page` ("Configuraciones", mismo ícono de engranaje), navegan a
  `ConfiguracionesView`, y el breadcrumb pasa a "Configuraciones › Parámetros"/"Configuraciones ›
  Apariencia" según la sección activa dentro de esa pantalla.
- Tests nuevos/actualizados: `tests/views/test_apariencia.py`, `tests/views/test_configuraciones.py`,
  `tests/views/test_configuracion.py`, `tests/views/test_main_window.py`.
- Documentación: `README.md`, `docs/GUIA_USUARIO.md`, `CHANGELOG.md`.

**Definición de Hecho:**
- El sidebar principal muestra "Configuraciones" (no "Parametros"), mismo ícono de engranaje.
- Entrar a Configuraciones muestra por defecto la sección Parámetros con la tabla de parámetros legales
  intacta (mismo comportamiento de siempre).
- La sección Apariencia tiene el interruptor "Modo oscuro" funcionando igual que antes (aplica el tema en
  caliente y lo persiste).
- El submenú permite alternar entre ambas secciones sin perder el resto de la navegación (Volver/Inicio/
  breadcrumb siguen funcionando).
- README.md y docs/GUIA_USUARIO.md ya no describen "Parámetros" como el punto de entrada del sidebar,
  sino "Configuraciones".
- Suite completa en verde.

**Cierre de implementación (2026-08-13):** Completado. Suite completa: 1103 passed, 0 failed
(`pytest -q`, `QT_QPA_PLATFORM=offscreen`). Las 4 tareas de implementación (Tasks 1-4 del plan) se
ejecutaron con 4 despachos separados de subagent-driven-development, cada uno superando una revisión en
dos etapas (cumplimiento de spec + calidad de código) antes de aceptarse; las Tasks 1 y 2 se despacharon
en paralelo por tocar archivos disjuntos (sin conflictos). Hallazgos de las revisiones que vale la pena
dejar registrados: el implementador de la Task 1 dejó inicialmente 2 imports a mitad de archivo (ruff
E402), corregido en una ronda de seguimiento antes de aprobarse; el implementador de la Task 4 corrigió
además un comentario obsoleto en `MainWindow._volver()` que todavía citaba los nombres viejos
`parametros_page`/`_ir_a_parametros` — el texto literal del plan no lo señalaba explícitamente, pero
quedó huérfano por el mismo rename y se corrigió de una vez, igual que la nota de cierre del Sprint 64
señala sus propios hallazgos de alcance. `ruff check .` queda limpio al final ("All checks passed!").

---

## Sprint 67 — Checkbox invisible en modo claro y oscuro (indicador de QCheckBox) ✅ Completado

**Prioridad sugerida:** Alta — bug visual real que afecta el flujo de captura en todas las pantallas con
checkboxes (Agregar obligación, Agregar valor de parámetro, Modo oscuro).

**Depende de:** Nada.

**Contexto:** el usuario reportó, mientras probaba "Agregar obligación", que no podía ver el recuadro de
las casillas "Demanda judicial" ni "¿Hay acuerdo posterior de capitalización?" — ni en modo claro ni en
modo oscuro (este último en la vista de Parámetros). Investigación confirmó que ni `resources/theme.qss`
ni `resources/theme_dark.qss` tenían jamás una sola regla `QCheckBox::indicator` — afecta a los 4 archivos
de `app/views/` que usan `QCheckBox` (`obligaciones.py`, `configuracion.py`, `apariencia.py`,
`descuentos_laborales.py`), no solo a los 2 que el usuario notó. Diseño en
`docs/superpowers/specs/2026-08-13-checkbox-indicador-visible-design.md`, plan en
`docs/superpowers/plans/2026-08-13-checkbox-indicador-visible.md`, ejecutado con
superpowers:subagent-driven-development en un worktree dedicado.

**Código nuevo a crear:** bloques `QCheckBox`/`QCheckBox::indicator` (normal, hover, checked,
checked:hover, disabled, checked:disabled) en `resources/theme.qss` y `resources/theme_dark.qss`, usando
solo los colores de marca ya documentados en cada archivo — el estado "marcado" se representa con relleno
de color sólido (sin glifo de tilde dibujado encima, para no depender de un asset SVG nuevo). Test nuevo:
`tests/core/test_theme_qss.py`.

**Definición de Hecho:**
- El indicador de cualquier `QCheckBox` de la app es visible, marcado o sin marcar, en modo claro y en modo
  oscuro.
- Suite completa en verde.

**Cierre de implementación (2026-08-13):** Completado. 4 commits (test que falla + implementación, para
cada tema), cada uno con revisión de spec y de calidad. Suite completa: 1107 passed (número justo después
de mergear este sprint); `ruff check .` limpio. La revisión final encontró 2 notas no bloqueantes:
`QCheckBox::indicator:checked:disabled` reutiliza el color de "texto deshabilitado" en vez de un tono
"primario disabled" dedicado (sigue siendo un color de marca documentado, solo una inconsistencia menor de
patrón), y 3 `QGroupBox` marcables en `obligaciones.py` usan un subcontrol distinto
(`QGroupBox::indicator`), no cubierto por este fix — posible seguimiento futuro, fuera del alcance de este
bug. **Pendiente de verificación manual:** el agente que ejecutó el plan corrió en modo headless y no pudo
confirmar visualmente el renderizado real en la app (clic a través de "Agregar obligación" en ambos temas)
— queda para que el usuario lo confirme la próxima vez que abra la app.

---

## Sprint 68 — Parámetros: editar/eliminar de usuario, vigencia clara, unidad desplegable y tooltips homologados ✅ Completado

**Prioridad sugerida:** Alta — gap funcional real: el usuario no tenía forma de corregir parámetros de
prueba mal cargados.

**Depende de:** Nada.

**Contexto:** el usuario, probando el flujo de captura de parámetros, cargó valores de prueba que
"quedaron mal" y no tenía forma de eliminarlos ni editarlos — `parametros_legales` era estrictamente
append-only en la UI, sin ningún flag real que distinguiera los valores de sistema/semilla de los creados
por un usuario (el campo `usuario` era solo texto libre). Además reportó 3 problemas más en el mismo
formulario: "Vigente hasta" desaparecía sin explicación según el modo del parámetro elegido, "Unidad" era
texto libre en vez de un desplegable, y solo el campo "Unidad" tenía el ícono ⓘ de ayuda visual (el resto
tenía tooltip solo al pasar el mouse directo sobre el campo, sin ícono). Diseño en
`docs/superpowers/specs/2026-08-13-parametros-crud-usuario-design.md`, plan en
`docs/superpowers/plans/2026-08-13-parametros-crud-usuario.md`, ejecutado con
superpowers:subagent-driven-development en un worktree dedicado, 10 tareas secuenciales (comparten archivo
con `app/views/configuracion.py`, no paralelizables entre sí sin riesgo de conflicto).

**Código nuevo a crear:**
- `database/models.py`: columna `creado_por_sistema: bool` en `ParametroLegal`. Migración nueva
  `scripts/migrate_creado_por_sistema.py` (idempotente, con backfill de las filas ya sembradas con
  `usuario='sistema'`).
- `app/services/parametro_service.py`: `editar_valor`/`eliminar_valor` nuevos, protegidos (nunca operan
  sobre `creado_por_sistema=True`); `agregar_valor` refactorizado (`_validar_y_preparar` compartida) y
  ahora marca `creado_por_sistema=False` siempre.
- `app/views/configuracion.py`: `ParametroFormDialog` soporta modo edición (`parametro_id`); "Vigente
  hasta" se deshabilita con nota explicativa en vez de ocultarse; "Unidad" pasa a `QComboBox` con opción
  "Otros..."; todos los campos usan el ícono ⓘ (`agregar_ayuda`); `HistorialParametroDialog` gana columnas
  Editar/Eliminar (solo para filas de usuario); `ParametrosView.tabla` gana tooltips de columna.
- Tests nuevos/actualizados en `tests/scripts/test_migrate_creado_por_sistema.py`,
  `tests/services/test_parametro_service.py`, `tests/views/test_configuracion.py`.
- Documentación: `README.md`, `docs/GUIA_USUARIO.md`, `CHANGELOG.md`.

**Definición de Hecho:**
- Un usuario puede editar/eliminar solo los valores de parámetro que él mismo cargó; los de sistema quedan
  protegidos en cada camino de código (servicio y UI), no solo ocultos en pantalla.
- "Vigente hasta" explica en la propia UI cuándo aplica, sin cambiar el motor de resolución de parámetros.
- "Unidad" es un desplegable con las 6 unidades ya usadas + "Otros...".
- Todos los campos del formulario y las columnas de la tabla resumen tienen tooltip ⓘ.
- Suite completa en verde.

**Cierre de implementación (2026-08-13):** Completado. 16 commits a través de las 10 tareas del plan, cada
una con revisión de spec y de calidad, más una revisión holística final centrada en verificar la invariante
de protección de filas de sistema en cada camino nuevo de código. Suite completa: 1127 passed en la rama,
1131 tras mergear a main junto con el Sprint 67; `ruff check .` limpio. Un hallazgo real durante la Task 1:
los scripts de migración con SQL crudo que verificaban columnas de `parametros_legales` se rompieron al
agregar la columna nueva — se corrigieron como parte de la misma tarea, no señalado explícitamente en el
plan pero necesario para no dejar la suite roja. La Task 8 encontró y corrigió un bug real durante el
auto-review del implementador: `QTableWidget` no limpia los `cellWidget` de una fila al reordenarse, lo que
podía dejar botones Editar/Eliminar "fantasma" en una fila de sistema tras un cambio de orden — corregido
con un test de regresión que lo reproduce. La Task 10 (revisión final) encontró y corrigió 3 tooltips ⓘ
residuales (Área, Unidad, Usuario) que todavía decían "no se puede editar después de guardar", texto que
había quedado obsoleto desde que la Task 7 habilitó la edición. **Pendiente de verificación manual:** el
clic a través real de la pantalla de Parámetros (revelado de "Otros...", estados habilitado/deshabilitado
de "Vigente hasta", flujo de Editar/Eliminar) no se pudo confirmar de forma headless — queda para que el
usuario lo revise.

---

## Sprint 69 — Configuraciones: Restablecer datos de fábrica ✅ Completado

**Prioridad sugerida:** Media — feature nueva pedida por el usuario para poder empezar de cero tras cargar
datos de prueba, sin bloquear el uso actual.

**Depende de:** Sprint 68 (columna `creado_por_sistema`, usada para no borrar los parámetros de sistema al
restablecer).

**Contexto:** el usuario pidió una forma de volver la app al estado "recién instalada" desde la propia UI
— motivado por los mismos datos de prueba mencionados en el Sprint 68, pero a nivel de toda la base
(expedientes incluidos), no solo parámetros. Diseño en
`docs/superpowers/specs/2026-08-13-restablecer-datos-fabrica-design.md`, plan en
`docs/superpowers/plans/2026-08-13-restablecer-datos-fabrica.md`, ejecutado con
superpowers:subagent-driven-development en un worktree dedicado, despachado después de que el Sprint 68
mergeara a main (dependencia real de esquema, no solo de orden narrativo).

**Código nuevo a crear:**
- `app/services/restablecer_service.py` (nuevo): `crear_backup_de_base_de_datos()` (copia `bastium.db` a
  `backups/`, mismo patrón de nombre que los backups manuales del Sprint 64) + `restablecer_datos_fabrica()`
  (borra expedientes en cascada vía ORM + parámetros con `creado_por_sistema=False`, deja los de sistema
  intactos).
- `app/views/restablecer.py` (nuevo): `ConfirmarRestablecerDialog` (exige escribir "RESTABLECER" para
  habilitar el botón de confirmar) + `RestablecerView` (orquesta diálogo → backup → borrado → reset de tema
  a claro → mensaje de éxito con la ruta del backup; aborta sin borrar nada si el backup falla).
- `app/views/configuraciones.py`: tercera sección "Restablecer" en el submenú, junto a Parámetros y
  Apariencia.
- Tests nuevos: `tests/services/test_restablecer_service.py`, `tests/views/test_restablecer.py`, casos
  nuevos en `tests/views/test_configuraciones.py`.
- Documentación: `README.md`, `docs/GUIA_USUARIO.md`, `CHANGELOG.md`.

**Definición de Hecho:**
- Configuraciones → Restablecer borra todos los expedientes y los parámetros de usuario, deja los de
  sistema y crea un backup automático antes de borrar.
- La confirmación exige escribir "RESTABLECER" exacto; si el backup falla, no se borra nada.
- Suite completa en verde.

**Cierre de implementación (2026-08-13):** Completado. 7 commits a través de las 7 tareas del plan, cada
una con revisión de spec y de calidad, más revisión holística final centrada en la garantía de orden
(backup exitoso antes de cualquier borrado), verificada trazando el código real 3 veces (implementador,
revisor de spec, revisor final). Suite completa: 1145 passed tras mergear a main; `ruff check .` limpio.
Una interrupción por límite de sesión del agente ocurrió justo antes de despachar la Task 3 — se verificó
que no quedó trabajo a medio commitear antes de reanudar, sin pérdida ni duplicación. **Hallazgo no
bloqueante, no corregido** (fuera del alcance literal del plan): `RestablecerView._restablecer()` no
captura excepciones después de un backup exitoso — si `restablecer_datos_fabrica()` lanzara una excepción
en ese punto, el usuario vería un traceback crudo en vez de un diálogo de error (el backup ya está a salvo,
no hay riesgo de pérdida de datos, solo degradación de UX ante un caso hoy no observado en ningún test).
**Pendiente de verificación manual:** el clic a través real (confirmar el texto de advertencia, el botón
destructivo, el gate de confirmación, y el flujo completo de restablecimiento con datos de prueba) no se
pudo confirmar de forma headless — queda para que el usuario lo revise.

---

## Sprint 70 — Motor de vigencia de leyes por año (Ley 100/1993, Ley 797/2003, Ley 2381/2024 y transiciones CST/CPT) 🔵 Bloqueado — pendiente de confirmación

**Prioridad sugerida:** Alta — afecta directamente la corrección jurídica de cualquier liquidación
pensional o laboral cuyo hecho generador haya ocurrido bajo una ley distinta a la que el motor usa hoy.

**Depende de:** Sprint 17 (módulo pensional, fórmula de tasa de reemplazo ya implementada) y Sprint 13
(infraestructura de `parametros_legales` versionados por fecha de vigencia — ya existe el patrón, falta
extenderlo a fórmulas completas, no solo cifras sueltas).

**Contexto (reportado por el usuario, 2026-08-13):** el sistema debe saber qué ley aplica (la fórmula y las
cifras de cada ley) dependiendo del año en que ocurrió el hecho del caso, no de la fecha actual. Ejemplo
dado por el usuario: quien se pensionó en 1997 se rige por la Ley 100 de 1993; quien se pensionó en 2024 se
rige por la Ley 797 de 2003; quien se pensione desde la entrada en vigencia de la Ley 2381 de 2024 se rige
por esa ley nueva. Lo mismo aplica en Derecho Laboral y Seguridad Social, donde el CST y el CPT han tenido
varias reformas con vigencias propias.

**Hallazgos (verificados leyendo el código, 2026-08-13):** `app/services/parametro_service.py` (Sprint 13)
versiona **valores** (tasas, topes, cifras) por fecha de vigencia — eso ya está resuelto para números
sueltos. Pero `calcular_tasa_reemplazo`/`CALCULAR_R` (Sprint 17, `r = 65.5 − 0.5·s`, con piso 55%/techo
65.5% y bono de 1.5% cada 50 semanas sobre 1.300 mínimas) es una única fórmula fija en Python, sin ninguna
noción de "esta fórmula rige solo entre la fecha X y la fecha Y". El propio cierre del Sprint 13 documentó
esta distinción a propósito (versionar **parámetros**, no reglas/fórmulas completas como el catálogo EFDJ
del PDF) porque en ese momento no había un caso de uso concreto que lo exigiera — este reporte es
exactamente ese caso de uso concreto.

**Decisión de diseño a tomar con el usuario antes de codificar (no asumir):**
- ¿Se modela como un catálogo de "fórmulas versionadas" (una tabla que asocia rango de fechas → función/
  parámetros de la fórmula), o basta con condicionales explícitos en el código por rango de fecha para las
  pocas leyes que hoy se conocen (Ley 100/1993, Ley 797/2003, Ley 2381/2024)?
- ¿Aplica solo al módulo pensional (Sprint 17), o también a otras fórmulas de Laboral/Seguridad Social que
  hayan cambiado por reforma del CST/CPT? El usuario menciona ambos dominios pero solo da el ejemplo
  pensional en detalle.

**Código nuevo a crear (una vez conseguida la fuente y tomada la decisión):**
- Tabla o estructura versionada de Ley → fecha de vigencia → fórmula/cifra aplicable, empezando por las 3
  leyes pensionales mencionadas.
- Selector de fórmula por fecha del hecho generador (no la fecha actual del sistema) en el módulo pensional,
  y en cualquier otro módulo que el despacho confirme afectado.

**Alcance explícitamente excluido (por ahora):** no se está pidiendo migrar al catálogo EFDJ completo (24
campos por regla, ya evaluado y cerrado sin construir en el Sprint 13) — es un paso intermedio, igual de
acotado que el que ya se hizo para parámetros, pero para fórmulas.

**Definición de Hecho:**
- Una liquidación pensional con hecho generador en 1997 usa la fórmula/cifras de la Ley 100 de 1993; una
  con hecho generador en 2024 usa la Ley 797 de 2003; una posterior a la entrada en vigencia de la Ley 2381
  de 2024 usa esa ley — verificado con tests que reproduzcan un caso real de cada ley.
- Suite completa en verde.

**Bloqueado por:** pregunta agregada a `Preguntas-Para-Abogado-Abiertas.md`, sección "Sprint 70" — se
necesita la tabla completa de leyes, fecha de vigencia y fórmula/cifra aplicable antes de codificar nada,
mismo criterio de rigor que Sprint 5/7/18.

**Actualización (2026-08-19):** el Sprint 91 encontró, en una plantilla comercial de referencia del
despacho (`P9.TASA-DE-REEMPLAZO-LEY-797-2003.md`), un borrador de tabla con al menos 2 fórmulas de tasa de
reemplazo pensional anteriores a la que ya implementa el código (vigente desde 2004) — exactamente el tipo
de "caso de uso concreto" que este sprint necesitaba. La pregunta de este sprint en
`Preguntas-Para-Abogado-Abiertas.md` se amplió con ese borrador para que el despacho lo confirme/corrija en
vez de partir de cero. Sigue bloqueado — la fuente es una plantilla comercial de terceros, no verificación
directa de la norma.

---

## Sprint 71 — Checkbox "aplica indexación IPC" invisible en Agregar Obligación (seguimiento Sprint 67) ✅ Completado

**Prioridad sugerida:** Alta — el Sprint 67 (cerrado 2026-08-13) corrigió la falta de estilos
`QCheckBox::indicator` mismo día, pero cerró con una nota explícita de "pendiente de verificación manual...
queda para que el usuario lo confirme la próxima vez que abra la app". Este reporte es exactamente esa
verificación, y encontró que el problema sigue presente.

**Depende de:** Sprint 67 (ya completado, es la corrección que este sprint debe verificar/extender).

**Contexto (reportado por el usuario, 2026-08-13):** en "Agregar obligación", la casilla "aplica
indexación IPC (corrección monetaria)" no se ve porque se confunde con el fondo color crema del resto del
formulario.

**Hallazgos (verificados leyendo el código, 2026-08-13):** `check_aplica_indexacion_ipc`
(`app/views/obligaciones.py:255`) es un `QCheckBox` real — en teoría ya cubierto por las reglas
`QCheckBox::indicator` que el Sprint 67 agregó a `theme.qss`/`theme_dark.qss`. Pero vive dentro de
`self.grupo_tasas_intereses` (línea 384), un `QGroupBox` creado con `setCheckable(True)` — y el propio
cierre del Sprint 67 dejó documentado, como hallazgo no resuelto: "3 `QGroupBox` marcables en
`obligaciones.py` usan un subcontrol distinto (`QGroupBox::indicator`), no cubierto por este fix". Es
decir: puede que el checkbox interno sí esté bien estilado y el problema real sea el indicador del
`QGroupBox` contenedor (que si tampoco se ve, hace más difícil distinguir visualmente dónde está cada
control dentro de la sección "Tasas e intereses"), o puede que el fix de Sprint 67 no se esté aplicando
correctamente sobre este control específico — hace falta reproducir visualmente en la app (no solo con
tests headless, que es justo lo que el Sprint 67 no pudo hacer) para diagnosticar cuál de las dos cosas es.

**Código nuevo a crear:** diagnóstico visual primero (abrir la app, "Agregar obligación", área
Civil/Familia, sección "Tasas e intereses"); según lo que se confirme, extender las reglas QSS de
`QGroupBox::indicator` (mismo patrón que `QCheckBox::indicator` del Sprint 67) a los 3 `QGroupBox`
marcables de `obligaciones.py`, o corregir la regla existente si el checkbox interno es el que sigue mal.

**Definición de Hecho:**
- El checkbox de indexación IPC (y los 3 `QGroupBox` marcables) son visibles, marcados o sin marcar, en
  modo claro y oscuro — verificado visualmente en la app real, no solo con test headless.
- Suite completa en verde.

**Cierre de implementación (2026-08-14):** Completado, vía `superpowers:subagent-driven-development`. El
diagnóstico confirmó que el problema era el segundo de los dos escenarios previstos: `check_aplica_indexacion_ipc`
en sí es un `QCheckBox` real, ya cubierto por el fix del Sprint 67 — lo que faltaba era el indicador del
`QGroupBox` contenedor (`grupo_tasas_intereses`, marcable). Se agregaron reglas `QGroupBox::indicator` (6
estados: normal, hover, checked, checked:hover, disabled, checked:disabled) a `resources/theme.qss` y
`resources/theme_dark.qss`, reutilizando exactamente los mismos colores y tamaño que `QCheckBox::indicator`
en cada archivo. 4 tests nuevos en `tests/core/test_theme_qss.py`, mismo patrón que los 4 tests existentes
del Sprint 67. **Pendiente de verificación manual** (mismo criterio que el Sprint 67): un test headless no
puede confirmar el render final en Qt — queda para que el usuario lo confirme abriendo "Agregar obligación"
en ambos temas. Suite completa en verde (1149 tras este sprint individual, 1162 tras el merge final del
lote).

---

## Sprint 72 — Rediseño del formulario "Agregar Obligación": tamaño inicial y layout responsivo ✅ Completado

**Prioridad sugerida:** Media-alta — no es un bug de cálculo, pero afecta la usabilidad de la pantalla más
usada del software (Sprint 56 ya permitió redimensionar el diálogo, pero no corrigió el tamaño inicial ni
la disposición del contenido).

**Depende de:** Sprint 56 (diálogos redimensionables, ya completo — este sprint es sobre el contenido/
tamaño por defecto, no sobre la capacidad de redimensionar en sí).

**Contexto (reportado por el usuario, 2026-08-13):** la ventana de "Agregar obligación" es muy grande y no
tiene forma fácil de achicarla, al punto de que el botón "Guardar" no aparece a simple vista. El usuario
pide además que, al ampliar la ventana, los campos no queden como barras largas en una sola columna, sino
en un layout armónico — específicamente que la sección "Tasas e intereses" pase a la derecha de "Datos
básicos" en vez de debajo, para que funcione bien en cualquier tamaño de pantalla.

**Hallazgos (verificados leyendo el código, 2026-08-13):** `ObligacionFormDialog` (`app/views/obligaciones.py`)
organiza sus 3 `QGroupBox` colapsables (Datos básicos, Tasas e intereses, Honorarios y costas, Sprint 34) en
un único layout vertical (`QVBoxLayout` o equivalente) — no hay ningún `QGridLayout`/`QHBoxLayout` que
ponga secciones una junto a otra. El Sprint 56 solo agregó la capacidad de redimensionar/maximizar (flags de
Qt), sin tocar el tamaño inicial (`resize()`/`setMinimumSize()`) ni el contenido del formulario — está
documentado explícitamente como alcance excluido de ese sprint.

**Decisión de diseño a tomar con el usuario antes de codificar:** confirmar el layout deseado (ej. 2
columnas: Datos básicos + Honorarios/costas a la izquierda, Tasas e intereses a la derecha, o alguna otra
distribución) y si debe ser responsivo (colapsar a una columna en pantallas angostas) o fijo de 2 columnas
siempre.

**Código nuevo a crear:**
- Reestructurar el layout de `ObligacionFormDialog` a un `QGridLayout` (o `QHBoxLayout` de 2 columnas)
  entre los `QGroupBox` existentes, sin tocar los campos internos de cada sección.
- Ajustar el tamaño inicial del diálogo para que el botón "Guardar" sea visible sin necesidad de
  redimensionar manualmente.

**Alcance explícitamente excluido:** no cambia ningún campo ni validación existente — solo la disposición
visual y el tamaño por defecto.

**Definición de Hecho:**
- El botón "Guardar" es visible sin redimensionar la ventana, en una resolución de pantalla estándar
  (ej. 1366×768).
- Las secciones "Datos básicos" y "Tasas e intereses" quedan una junto a otra (no una debajo de otra) en el
  tamaño por defecto del diálogo.
- Suite completa en verde.

**Cierre (2026-08-17, commits `6b3ffea`/`1be69c5`):** `layout_principal` pasó a `QGridLayout` (Datos básicos
arriba-izquierda, Honorarios y costas abajo-izquierda, Tasas e intereses a la derecha; la primera versión
(`6b3ffea`) le daba `rowSpan=2` para alinearla con las dos filas de la izquierda, pero el fix `1be69c5`
quitó ese `rowSpan` — ver el motivo abajo — así que en el estado final Tasas e intereses ocupa solo la fila
0, igual que Datos básicos; Guardar queda abajo abarcando las 2 columnas). La primera versión (`6b3ffea`)
fijaba `self.resize(900, 650)`, pero
el code review encontró que Qt recalcula el ancho mínimo real al mostrar el diálogo (`.exec()`), y 4 de 6
áreas terminaban más anchas que 1366px (hasta 1660px en Honorarios) — peor que el layout de una sola
columna que tenía antes. La corrección (`1be69c5`) envolvió las 3 secciones en un `QScrollArea`
(`area_desplazable_secciones`) para desacoplar el tamaño mínimo del contenido del tamaño de la ventana, y
sacó el botón Guardar del grid hacia el layout exterior para que quede siempre visible sin importar el
scroll. Con `self.resize(1300, 650)`, las 6 áreas quedan exactamente en 1300×650 (verificado con
`QT_QPA_PLATFORM=offscreen` + `.show()`, igual que corre la CI) — Civil/Familia sigue necesitando scroll
horizontal para ver todo "Tasas e intereses" (contenido ~1620px, sobre todo por la etiqueta larga del
checkbox de interés sobre capital indexado), tradeoff aceptado en vez de restructurar ese `QFormLayout`
interno (fuera de alcance de este sprint). Suite completa en verde (1196 tests en el momento del cierre).

---

## Sprint 73 — Obligaciones recurrentes con fechas personalizadas no mensuales (ej. gastos de vestuario) ✅ Completado

**Prioridad sugerida:** Media — extiende un mecanismo ya construido (Sprint 41) a un patrón de recurrencia
distinto, no es un bug.

**Depende de:** Sprint 41 (generador de cuotas mensuales con reajuste anual, ya completo — este sprint
necesita el mismo tipo de mecanismo pero con fechas arbitrarias en vez de "cada mes").

**Contexto (reportado por el usuario, 2026-08-13):** los gastos de vestuario no se repiten mes a mes, sino
en fechas puntuales del año (ej. junio, diciembre, y el cumpleaños del niño). El usuario pide que solo esas
fechas específicas queden registradas en el calendario de obligaciones, no una cuota mensual.

**Hallazgos (a verificar antes de codificar):** el generador de cuotas del Sprint 41
(`app/services/reajuste_anual.py::generar_cuotas_mensuales()`) y el `RecurringScheduler`
(`app/engine/temporal/schedulers/recurring.py`) están diseñados para cadencia **mensual** fija — no hay
ningún mecanismo para una lista arbitraria de fechas por año (ej. "15 de junio, 15 de diciembre, y la fecha
de cumpleaños de X persona, cada año").

**Decisión de diseño a tomar con el usuario antes de codificar:**
- ¿Se modela como un nuevo tipo de recurrencia (`TipoRecurrencia.FECHAS_ANUALES_FIJAS` o similar) con una
  lista de fechas MM-DD por año, reutilizando el resto del mecanismo de reajuste/abonos del Sprint 41?
- ¿La fecha de cumpleaños del niño se ingresa como una fecha MM-DD fija dentro de esa lista, o se deriva
  automáticamente de la fecha de nacimiento del beneficiario (ver Sprint 74)?

**Código nuevo a crear (una vez decidido):**
- Nuevo tipo de recurrencia con lista de fechas por año, reutilizando el generador de obligaciones hijas y
  el sistema de abonos por cuota ya construido en el Sprint 41.
- Campo(s) en el formulario de obligación recurrente para capturar las fechas (o derivarlas de la fecha de
  cumpleaños si aplica).

**Definición de Hecho:**
- Una obligación de "gastos de vestuario" con fechas junio/diciembre/cumpleaños genera exactamente esas
  ocurrencias por año, no 12 cuotas mensuales.
- Suite completa en verde.

**Cierre (2026-08-17, commit `b03210d`):** decisión de diseño tomada — nuevo `TipoRecurrencia`
(`MENSUAL`/`FECHAS_ANUALES_FIJAS`) con lista de fechas MM-DD en formato JSON (`Obligacion.fechas_anuales_fijas`,
`String(300)`). El cumpleaños del beneficiario se ingresa como una fecha MM-DD manual más en la lista —
**no** se deriva de una fecha de nacimiento, porque el Sprint 74 (intake de beneficiario/fecha de nacimiento)
sigue sin implementar; documentado en 3 lugares (docstring del modelo, del servicio, y tooltip del campo) como
limitación a revisar cuando el Sprint 74 se construya. `app/services/recurrencia_fechas_fijas.py` (nuevo)
reutiliza genuinamente el contrato de `generar_cuotas_mensuales()` del Sprint 41 (mismo patrón de obligación
hija/`obligacion_padre_id`, misma idempotencia, misma sesión propia) — el reajuste anual es opcional en este
generador (a diferencia del mensual, donde es obligatorio), porque gastos de fecha fija como vestuario no
necesariamente reajustan cada año. Verificado con test end-to-end: 3 fechas → exactamente 3 ocurrencias por
año, no 12. Sin invasión de alcance del Sprint 73/74 (confirmado por grep: no se creó ninguna entidad
`Beneficiario` ni campo de fecha de nacimiento). El nuevo combo/campo en `ObligacionFormDialog` es aditivo,
no tocó el `QGridLayout`/`QScrollArea` que acababa de dejar el Sprint 72. Suite completa en verde (1230
tests en el momento del cierre).

---

## Sprint 74 — Familia: intake inicial de edad, beneficiario y tipo de alimentos (árbol de decisión) 📋 Pendiente

**Prioridad sugerida:** Alta — es información base que condiciona hasta cuándo es exigible cualquier
obligación alimentaria; sin esto, el sistema no puede calcular automáticamente la fecha de terminación de
una cuota alimentaria.

**Depende de:** Nada técnicamente, pero bloqueado por la pregunta legal de Sprint 74 en
`Preguntas-Para-Abogado-Abiertas.md` (reglas de vigencia exactas por tipo de beneficiario).

**Contexto (reportado por el usuario, 2026-08-13, 3 hallazgos relacionados del mismo reporte):**
1. Al inicio de un caso de Civil/Familia se debe capturar la fecha de nacimiento del demandante (o del
   beneficiario) para que el sistema calcule automáticamente su edad — relevante porque una cuota
   alimentaria para un niño sin discapacidad termina a los 18 años si no estudia, o se extiende hasta los
   25 si estudia una carrera profesional/técnica/tecnológica.
2. El sistema debe preguntar si existe un beneficiario distinto del demandante (el beneficiario es quien
   tiene el derecho real sobre la obligación) — si existe, se debe capturar su nombre y fecha de nacimiento
   para el mismo cálculo automático de edad.
3. No solo los niños reciben alimentos: el sistema debe preguntar, como primer paso, si el beneficiario es
   un niño, un niño con discapacidad, el cónyuge, los padres, u otra persona (donante, abuelos, etc.), y
   presentar los campos siguientes como un árbol de decisión que cambia según esa respuesta (ej. niño sin
   discapacidad → fecha de nacimiento + "¿estudia?"; niño con discapacidad → si es permanente, obligación
   vitalicia; cónyuge → hasta que supere su condición de vulnerabilidad; padres → hasta la muerte de
   cualquiera de las partes).

**Hallazgos (verificados leyendo el código, 2026-08-13):** no existe hoy ningún campo de fecha de
nacimiento, ni de tipo de beneficiario, ni de relación demandante/beneficiario en `database/models.py` —
confirmado con búsqueda de "beneficiario"/"fecha de nacimiento"/"discapacidad"/"cónyuge" en todo el
proyecto (`Pendientes.md`, código, specs): cero resultados antes de este reporte. Es una funcionalidad
enteramente nueva, no una corrección.

**Decisión de diseño a tomar con el usuario antes de codificar:**
- Confirmar las reglas exactas de vigencia por tipo de beneficiario con el despacho (ver pregunta en
  `Preguntas-Para-Abogado-Abiertas.md`, sección "Sprint 74") antes de construir el árbol de decisión, para
  no codificar una regla legal sin confirmar (mismo criterio que Sprints 13/16/20/41).
- Modelo de datos: ¿un campo `tipo_beneficiario` (enum) + campos condicionales según el tipo en el mismo
  `Expediente`/`Obligacion`, o una entidad `Beneficiario` propia (nombre, fecha de nacimiento, tipo,
  relación con el demandante) referenciada desde el expediente?

**Código nuevo a crear (una vez confirmadas las reglas y el modelo):**
- Campo(s) de fecha de nacimiento + cálculo automático de edad, tanto para el demandante como para un
  beneficiario distinto si existe.
- Selector de tipo de beneficiario (niño / niño con discapacidad / cónyuge / padres / otro) con campos que
  aparecen o desaparecen según la selección (árbol de decisión).
- Cálculo automático de la fecha de terminación de la obligación según el tipo de beneficiario y las reglas
  confirmadas por el despacho.

**Definición de Hecho:**
- Un caso de Familia con un niño beneficiario sin discapacidad calcula automáticamente si la obligación
  sigue vigente a los 18/25 años según si estudia.
- Un caso con beneficiario cónyuge/padres no aplica el límite de edad de los niños.
- Suite completa en verde.

---

## Sprint 75 — Cuotas recurrentes en Civil/Familia y Comercial, con selección de pago por rango e imputación en cascada ✅ Completado

**Prioridad sugerida:** Alta — extiende a Comercial un mecanismo que antes solo existía para Familia
(Sprint 41), y agrega una capacidad de imputación de pagos parciales más rica que la que existía antes en
cualquier área.

**Depende de:** Sprint 41 (generador de cuotas mensuales con reajuste anual, antes exclusivo de Civil/
Familia) y Sprint 44 punto 6 (extensión a Laboral, explícitamente excluida en su momento y dejada para
"cuando el usuario decida extenderlo").

**Contexto (reportado por el usuario, 2026-08-13):** para **todas las categorías de todas las áreas del
derecho**, el sistema debe detectar que una obligación es recurrente y generar automáticamente el listado
de obligaciones mensuales (con sus sub-obligaciones de intereses) desde la fecha pactada. Sobre ese
listado, el abogado debe poder seleccionar por rangos o manualmente qué cuotas ya se pagaron completas, y
si hubo abonos parciales, el sistema debe imputar el pago desde la fecha del abono hacia atrás en el tiempo
según una lógica de cascada: ejemplo dado por el usuario — un abono de $500.000 el 1 de abril de 2024 paga
primero el capital de la cuota de abril, luego el capital e intereses de la cuota de marzo, y luego solo
una parte de los intereses de la cuota de febrero (el resto de esos intereses se sigue debiendo, pero como
el capital de febrero ya quedó pagado, no sigue generando intereses nuevos); o si el abono alcanza para
pagar solo una parte del capital de una cuota atrasada, los intereses ya generados hasta la fecha del abono
se mantienen, pero los intereses nuevos se calculan sobre el capital insoluto restante.

**Decisión de diseño tomada con el usuario (2026-08-14, brainstorming antes de codificar):** reajuste
anual opcional al generalizar (una obligación sin reajuste también genera cuotas reales, con capital
constante); la cascada capital-primero aplica solo a cuotas-hija (nunca al orden legal general de las
demás obligaciones), activada automáticamente por tipo de obligación sin importar cómo se cargó el pago;
la selección por rango convive con la selección individual del Sprint 41, sin reemplazarla; un `Abono`
real por cuota tocada, sin cambiar el modelo `Abono`; orden de imputación intercambiable en el motor,
calculado en el momento de liquidar (no precalculado aparte). **Alcance revisado durante la planeación**:
al investigar el código real de las 5 estrategias restantes se confirmó que Sancionatorio/Honorarios/
Tributario rechazan `RECURRENTE` a propósito (razón legal explícita: una multa/sanción/impuesto es un
hecho único) y Laboral es estructuralmente incompatible (una obligación = un contrato completo, no una
serie de cuotas) — este sprint generaliza únicamente a **Civil/Familia (ya existía) y Comercial (nuevo)**;
las otras 4 áreas quedan pendientes, condicionadas a confirmar con el despacho si tiene sentido legal
extenderlas. Diseño completo en `docs/superpowers/specs/2026-08-14-sprint75-cuotas-recurrentes-cascada-design.md`,
plan de implementación en `docs/superpowers/plans/2026-08-14-sprint75-cuotas-recurrentes-cascada.md`.

**Código nuevo:**
- `app/services/reajuste_anual.py::generar_cuotas_mensuales`: reajuste anual opcional (soporta
  `TipoReajusteAnual.NINGUNO`); copia también `tasa_moratoria_anual`/`ibc_vigente_anual`/
  `fecha_vencimiento` a cada cuota (bug encontrado en revisión: sin esto, generar cuotas para una
  obligación Comercial real habría fallado al liquidar).
- `AllocationEngine.allocate_capital_primero` (`app/engine/liquidation/allocation.py`) + parámetro
  `estrategia_imputacion` intercambiable en `LiquidationCore`/`UniversalLiquidationService`, activado
  automáticamente para toda cuota-hija vía `_estrategia_imputacion_por_obligacion`
  (`app/services/area_strategy.py`).
- `ComercialStrategy` detecta cuotas-hija ya generadas (mismo patrón que `CivilFamiliaStrategy`, cuyo
  propio guard tenía un bug preexistente relacionado, corregido en el mismo sprint) — evita doble conteo
  de capital y de la sanción de usura.
- `app/services/cascada_cuotas.py` (nuevo): `distribuir_pago_en_cascada` (función pura) y
  `deuda_pendiente_cuota` (reutiliza `UniversalLiquidationService`, incluye indexación IPC cuando aplica).
- `app/views/pago_por_rango.py` (nuevo): `PagoPorRangoDialog`, con preview de la cascada antes de
  confirmar. Selección múltiple contigua en `tabla_obligaciones` (primer precedente de este patrón en el
  proyecto) y botón "Pagar cuotas seleccionadas" en `ExpedienteDetallePage`, visible para Civil/Familia y
  Comercial (el botón "Generar cuotas" también se generalizó a esas 2 áreas, hallazgo de revisión
  posterior a la Task 3 original).

**Definición de Hecho:**
- Un expediente de Civil/Familia o Comercial con obligación recurrente genera el listado completo de
  cuotas antes de liquidar, seleccionable por rango o individualmente.
- El ejemplo numérico del usuario (abono de $500.000 el 1 de abril de 2024 sobre cuotas de $150.000
  mensuales desde el 1 de abril de 2022) se reproduce exactamente en un test de integración.
- Suite completa en verde.

**Cierre de implementación (2026-08-18):** Completado, vía `superpowers:subagent-driven-development` en
worktree dedicado (`worktree-sprints-75-61`). Además de las 7 tareas del plan, las revisiones de spec/
calidad encontraron y corrigieron 6 problemas reales antes del cierre: (1) guard obsoleto en
`CivilFamiliaStrategy` que duplicaba capital para cuotas sin reajuste (efecto colateral de la Task 1); (2)
la sanción de usura de `ComercialStrategy` se aplicaba dos veces sobre una obligación recurrente con
cuotas ya generadas; (3) `generar_cuotas_mensuales` no copiaba los campos que Comercial exige, rompiendo
el flujo real de "Generar cuotas" para esa área; (4) `deuda_pendiente_cuota` no incluía el evento de
indexación IPC en su proyección, divergiendo de la liquidación real; (5) el botón "Generar cuotas" seguía
oculto para Comercial pese a que el motor ya lo soportaba; (6) `PagoPorRangoDialog` podía propagar una
excepción no capturada si faltaba un parámetro IPC, dado que `_calcular_preview` corre en cada tecla.
Suite completa en verde (1208 passed, compartido con el cierre del Sprint 61), `ruff check .` limpio
(incluye una limpieza de 3 líneas que superaban el límite de 99 columnas, coladas en un commit anterior
sin que ninguna revisión previa corriera `ruff check .` sobre el repo completo).

---

## Sprint 76 — Hallazgos de una prueba práctica en Civil/Familia (reporte, reajuste anual, tasa diaria) ✅ Completado (4 hallazgos corregidos, 1 pregunta abierta)

**Contexto:** el usuario probó el flujo completo de Civil/Familia con un caso real (Radicado 2224),
comparando los resultados de BASTIUM contra un Excel real del despacho para el mismo caso. La prueba
sacó a la luz 5 hallazgos.

**Hallazgos y estado:**

1. **Concepto "PAYMENT" en la cronología en vez de un texto legible** — la fila de un abono mostraba
   literalmente la palabra "PAYMENT" como concepto, en vez de algo como "Abono — {referencia}". Causa: el
   evento de pago nunca llevaba un `label` en su payload. ✅ Corregido en
   `app/services/motor_universal.py` (aplica a las 6 áreas, no solo Civil/Familia).
2. **"Intereses Generados" subestimaba el interés real en expedientes con 2+ obligaciones** — el resumen
   ejecutivo del PDF/Word mostraba un subtotal de interés más bajo que el real (el "Saldo Final de
   Intereses" sí era correcto) porque `_fusionar_resultados` fijaba en `$0.00` el interés de la fila de
   cierre consolidada en vez de sumar el interés de cierre real de cada obligación aislada. ✅ Corregido en
   `app/services/area_strategy.py`.
3. **La tabla de cronología del PDF/Word se salía de los márgenes de la página** — con 10-11 columnas y
   sin ancho fijo, reportlab (PDF) y `Table Grid` en autofit-to-contents (Word) desbordaban el margen
   impreso. ✅ Corregido en `app/reports/pdf.py` y `app/reports/word.py`: página horizontal, anchos de
   columna proporcionales explícitos, y "Concepto" con word-wrap en el PDF.
4. **El combo "Reajuste anual" no se precargaba al editar una obligación ya guardada** — siempre mostraba
   "Ninguno" sin importar el valor real, y volver a guardar sin tocar ese campo revertía silenciosamente
   `tipo_reajuste_anual` a `NINGUNO` en la base de datos (el guardado en sí funcionaba bien; el problema
   era solo la precarga al editar). ✅ Corregido en `app/views/obligaciones.py::_precargar_desde_obligacion`,
   con 2 tests de regresión nuevos en `tests/views/test_obligaciones.py` (uno verifica la precarga, otro
   verifica que re-guardar ya no revierte el reajuste).
5. **El paso "Generar cuotas" (obligatorio para que el reajuste anual tenga efecto real al liquidar)
   nunca estaba documentado** — marcar "Reajuste anual" en la obligación no aplica nada por sí solo; hay
   que además seleccionar la obligación y hacer clic en "Generar cuotas" para que se persistan las cuotas
   mensuales con el capital ya escalado. Sin ese paso, el motor sigue expandiendo con capital constante
   como si el reajuste estuviera en "Ninguno" (`_eventos_de_obligacion`,
   `app/services/area_strategy.py`, líneas ~358-382). ✅ Corregido: paso agregado a
   `docs/GUIA_USUARIO.md`, sección 5.4.
6. **La fórmula de conversión de tasa anual → diaria no coincide con la del documento de requisitos del
   despacho** — BASTIUM usa la fórmula "efectiva compuesta" `(1+i)^(1/365)-1`; el documento de requisitos
   trae la fórmula lineal `i/365` (`0,0164` diario). Verificado con el caso real: usando la fórmula lineal,
   BASTIUM queda a solo 0,04% del Excel del despacho, vs. 0,11% con la fórmula compuesta actual. 🔵
   **Pregunta abierta** — ver `Preguntas-Para-Abogado-Abiertas.md`, Sprint 76, con el desarrollo completo
   pensado para que lo entienda alguien sin trasfondo técnico/financiero. **Actualización (2026-08-19,
   Sprint 83):** ninguna de las 2 opciones que contemplaba esta pregunta es, en realidad, la que usa el
   propio despacho en su plantilla comercial para este mismo interés civil del 6% — es una tercera fórmula
   (tasa mensual nominal con prorrateo de 30 días). La pregunta se amplió con esa "Opción C" en
   `Preguntas-Para-Abogado-Abiertas.md`; ver Sprint 83 para el detalle técnico completo.

**Verificación:** cada hallazgo se diagnosticó reproduciendo el caso real en un script aislado (sesión
SQLite en memoria, mismas fechas/montos/configuración que el expediente del usuario) antes de tocar
código, no solo por lectura. Suite completa tras los 4 fixes de código: 1147/1147 tests en verde.

**Archivos tocados:** `app/services/motor_universal.py`, `app/services/area_strategy.py`,
`app/reports/pdf.py`, `app/reports/word.py`, `app/views/obligaciones.py`,
`tests/views/test_obligaciones.py`, `docs/GUIA_USUARIO.md`.

---

## Sprint 77 — Persistir `LiquidationResult.alertas` en las exportaciones PDF/Word 🟡 En proceso

**Rama:** `sprint-77-alertas-en-exportaciones` (rutina autónoma, 2026-08-20).

**Prioridad sugerida:** Media — no es un error de cálculo (ningún saldo queda mal), pero es la pérdida de una
advertencia legal explícita que el despacho pidió (Sprint 43: "Doble Actualización Prohibida", "Techo de
usura alcanzado") en el canal más probable de terminar en manos de un juzgado o un cliente.

**Depende de:** Sprint 43 (ya completo — `LiquidationResult.alertas` existe, se serializa/deserializa
correctamente, y se muestra en pantalla vía toast + banner persistente en `ResultadoLiquidacionView`).

**Contexto:** durante el code review del Sprint 43 se encontró (y se corrigió parcialmente, commit `cf84ae7`)
que las alertas no bloqueantes de liquidación no llegaban al usuario en todos los caminos. Se corrigieron los
2 caminos de pantalla (cálculo en vivo y reconstrucción desde el historial de auditoría), pero
`app/reports/pdf.py`/`app/reports/word.py` siguen sin leer `.alertas` — un abogado que exporte el PDF/Word de
una liquidación con alertas y no vuelva a abrir la app nunca ve la advertencia.

**Código nuevo a crear:** exponer `resultado.alertas` a `ReportSummaryBuilder`/`ReportTableBuilder` (o el
mecanismo equivalente que ya arma el resumen ejecutivo de PDF/Word) y renderizarlas como una sección de
advertencias visible en ambos formatos — mismo criterio visual que ya usa el "⚠" de obligaciones prescritas
en esos mismos reportes (Sprint 42).

**Definición de Hecho:**
- Un PDF/Word exportado desde una liquidación con `alertas` no vacío muestra el texto de cada alerta.
- Un PDF/Word sin alertas no muestra la sección (no agregar ruido visual cuando no aplica).
- Suite completa en verde.

---

## Sprint 78 — Conteo inclusivo (`+1`) en `calcular_densidad_semanas` — confirmar con el despacho 📋 Pendiente

**Prioridad sugerida:** Baja — hallazgo de auditoría, no un reporte de bug del usuario; el código actual ya
está verificado contra el caso de prueba real citado en el test existente.

**Depende de:** Sprint 47 (parte B, ya completo — este sprint nace de un hallazgo hecho al confirmar la
Sentencia SL138-2024 en `calcular_densidad_semanas`).

**Contexto (hallazgo del cierre del Sprint 47 parte B, 2026-08-18):** la fórmula general de conteo de días
que confirmó el despacho en el Sprint 3 es inclusiva: `Dias = (Fecha_Fin - Fecha_Inicio) + 1`. Sin embargo,
`calcular_densidad_semanas` (`app/engine/labor/ibl.py`, Sprint 17) usa `(fin - inicio).days` directo, **sin**
el `+1`. Esto coincide exactamente con el caso de prueba judicial citado en el test existente
(`tests/engine/labor/test_ibl.py`, 348 días → 50 semanas, no 349) — es decir, el código de hoy está
verificado contra una fuente real, no es un bug evidente. Pero tampoco está confirmado explícitamente con el
despacho si la regla general "+1" del Sprint 3 aplica también aquí o si la densidad pensional es
deliberadamente la excepción (dado que el caso de prueba citado ya funciona sin el +1).

**Decisión de diseño a tomar con el despacho antes de tocar código:** ¿el conteo de días para densidad
pensional (semanas cotizadas) debe ser inclusivo (`+1`, igual que el resto de las reglas del Sprint 3), o el
caso de prueba judicial ya citado confirma que aquí NO aplica el +1? No cambiar el código sin esta
confirmación — mismo criterio de rigor que el resto del proyecto (Sprints 5/7/18/70).

**Definición de Hecho:**
- Respuesta del despacho registrada en `Preguntas-Para-Abogado-Respondidas.md` o
  `Preguntas-Para-Abogado-Abiertas.md` según corresponda.
- Si se confirma que sí aplica el +1: corrección en `calcular_densidad_semanas` con test que verifique que
  el caso de prueba judicial ya citado sigue dando el resultado correcto (o se documenta por qué ese caso
  específico es una excepción).
- Suite completa en verde.

---

## Sprint 79 — Confirmar si las costas procesales deben entrar en la base de interés de "Suma Única" 📋 Pendiente

**Prioridad sugerida:** Media — no es un bug confirmado (nadie ha dicho que esté mal), pero es un
comportamiento no documentado explícitamente en ninguna de las dos fórmulas que lo producen.

**Depende de:** Sprint 18 (costas procesales, ya completo) y Sprint 20/43 (algoritmo "Suma Única", ya
completo en Civil/Familia y ahora también alcanzable en Comercial modo (b) y Honorarios).

**Contexto (hallazgo de la revisión de integración cruzada entre los batches de Sprints 18/62/71/13 y
24/72/73/43/47, 2026-08-18):** `COSTAS_PROCESALES` comparte el mismo "bucket" de capital
(`_capital_concepts`, `app/engine/liquidation/engine.py:61`) que el capital propio de la obligación. Bajo
Suma Única (`usar_suma_unica=True`), la base de interés diario es `principal + indexación` — así que un
monto de costas termina generando interés civil del 6% junto con el capital, aunque ni la fórmula del
despacho para Honorarios (`Capital_Honorarios × IPC... + Interés_Civil_6%(Capital_Actualizado)`, Sprint 43)
ni el diseño original de Suma Única (Sprint 20) mencionan costas como parte de esa base. Ya existía en
Civil/Familia desde antes del Sprint 43; ese sprint solo hizo alcanzable la misma combinación en dos áreas
más (Comercial modo (b), Honorarios).

**Pregunta para el despacho:** cuando una obligación tiene costas procesales Y usa Suma Única/interés sobre
capital indexado, ¿las costas deben generar ese interés civil junto con el capital, o deben quedar fuera de
esa base (sumadas al final, sin generar interés adicional)?

**Definición de Hecho:**
- Pregunta registrada y respondida en `Preguntas-Para-Abogado-Abiertas.md`/`Respondidas.md`.
- Si el despacho confirma que costas NO debe estar en la base de Suma Única: separar `COSTAS_PROCESALES` de
  `_capital_concepts` con su propio test de regresión numérico.
- Si confirma que SÍ debe estarlo (comportamiento actual): documentar la decisión explícitamente en el
  docstring de `_evento_costas_procesales`/Suma Única, sin cambiar código.
- Suite completa en verde.

---

## Sprint 80 — Cargar la serie mensual real de IPC (2003-2026) y avanzar el desbloqueo del Sprint 8 📋 Pendiente

**Prioridad sugerida:** Alta — Sprint 8 lleva bloqueado desde 2026-08-01 exclusivamente por falta de este dato real; esta serie lo resuelve para el 90%+ de los casos recientes.
**Depende de:** Sprint 5 (series históricas), Sprint 8 (motor de interpolación mensual ya construido y probado, solo falta la tabla de datos).

**Contexto:** `app/engine/indexation/historical_index.py`, líneas 234-257, documenta que `_IPC_MENSUAL: dict[tuple[int, int], Decimal] = {}` está deliberadamente vacía porque no se consiguió "una tabla transcribible con confianza" (nota del 2026-08-01 en el Sprint 8 de `Pendientes.md`, líneas 802-805). `docs/Archivos de referencia abogado/_markdown/Historico IPC.md`, hoja `IndicesIPC`, trae exactamente ese dato: una grilla Mes (filas Enero-Diciembre) × Año (columnas 2003-2026) del índice IPC del DANE, con la fila "Base Diciembre de 2018 = 100,00" confirmando la base (columna 2018, fila Diciembre = 100.00 exacto), y el pie "Índices - Serie de empalme 2003 - 2026 / Fuente: DANE / Actualizado el 9 de Abril de 2026". Cubre Enero-2003 (Enero=50.42) hasta Abril-2026 (Abril=149.66); mayo-diciembre 2026 vienen en blanco (aún no certificados). A diferencia de lo que pidió el despacho en su respuesta del Sprint 8 (dos bases, Dic-2008=100 y Dic-2018=100, enlazadas por un Factor de Enlace calculado por el software en el mes de traslape — `Preguntas-Para-Abogado-Respondidas.md`, Sprint 8), esta tabla **ya viene enlazada por el DANE en una sola base continua** (2018=100) — es decir, el trabajo de "Factor de Enlace" que el despacho pidió que el software hiciera ya está resuelto en el origen. No cubre 1967-2002: para esas fechas la única fuente que existe sigue siendo `_IPC_VARIACION_ANUAL` (variación % anual, ya cargada desde el Sprint 5).

**Código existente a reutilizar:**
- `app/engine/indexation/historical_index.py:260-270` — `get_ipc_mensual_for_month(anio, mes)`, ya implementada y probada, solo lee de `_IPC_MENSUAL`.
- `app/engine/indexation/historical_index.py:273-295` — `get_ipc_interpolado_mensual_for_date(fecha)`, interpolación lineal por días dentro del mes, ya implementada exactamente como exige el despacho.
- `app/services/area_strategy.py` (`CivilFamiliaStrategy._evento_indexacion`, referenciada en `Pendientes.md` línea 813) — hoy llama a `get_ipc_interpolado_for_date` (interpolación anual, inválida); este sprint la cambia a `get_ipc_interpolado_mensual_for_date` **solo para el rango cubierto**.

**Código nuevo a crear:**
- Poblar `_IPC_MENSUAL` con los 280 pares `(año, mes) → Decimal` de la tabla (2003-01 a 2026-04).
- Lógica de fallback explícita para fechas fuera de rango (antes de 2003-01 o después del último mes cargado): decidir si se usa `IPCMensualNoDisponibleError` (bloquea la liquidación, seguro pero puede frustrar al usuario en casos viejos) o si se permite un fallback documentado a la interpolación anual solo para esas fechas — ver pregunta nueva en `Preguntas-Para-Abogado-Abiertas.md`, no asumir.
- Actualizar el wiring de `CivilFamiliaStrategy._evento_indexacion` para usar la función mensual dentro del rango cubierto.

**Definición de Hecho:**
- `_IPC_MENSUAL` deja de estar vacía para 2003-01 a 2026-04, con valores verificables uno a uno contra `Historico IPC.md`.
- Tests nuevos que verifiquen `get_ipc_interpolado_mensual_for_date` contra al menos 5 fechas reales de la tabla (incluyendo un 15 de mes, para probar la interpolación).
- `CivilFamiliaStrategy` usa la función mensual para fechas dentro de rango; el comportamiento para fechas fuera de rango queda documentado explícitamente (no en silencio).
- `docs/specifications/03_motor_indexacion.md` actualizado.
- Suite completa en verde.

---

## Sprint 81 — Extender la serie de IBC/Usura ("Consumo y Ordinario") hacia atrás hasta 1971 con la certificación real de la Superfinanciera 📋 Pendiente

**Prioridad sugerida:** Media — no bloquea nada activo, pero cierra una laguna real (1971-1997) con una fuente primaria verificable, y el rango actual (desde 1997-07-01) ya cubre la gran mayoría de casos de un despacho civil/comercial.
**Depende de:** Sprint 5 (`_TRAMOS_IBC_USURA` ya existe y este sprint solo la extiende, no la rediseña).

**Contexto:** `app/engine/indexation/historical_index.py:316-588` (`_TRAMOS_IBC_USURA`) empieza el 1997-07-01 (`TramoIBCUsura(date(1997, 7, 1), date(1997, 8, 31), Decimal("36.50"), Decimal("54.75"))`, línea 325). `docs/Archivos de referencia abogado/_markdown/Historicocertificacionsuperfinancieratasasdeinteres.md` trae una tabla con Resolución/Fecha/Vigencia Desde-Hasta/Tasa desde el **29-Oct-1971** (Resolución 2865, "CORRIENTE" 18.00%, "BANCARIO CORRIENTE" 14.00%, línea 12) hasta el 30-Abr-2026 (línea 446, IBC=17.84%, que coincide exacto con la Resolución 0517 de 2026 transcrita en `Ultima-Resolucion-que-certifica-tasas-de-interes-Superfinanciera.md`: "Certificar en un 17.84% efectivo anual el interés bancario corriente para la modalidad de crédito de consumo y ordinario", línea 80-81). Los valores de 1997-2006 de este archivo (ej. 2002-05: IBC=20.00%, línea 209) coinciden exacto con los ya cargados en `_TRAMOS_IBC_USURA` (`TramoIBCUsura(date(2002, 5, 1), date(2002, 5, 31), Decimal("20.00"), Decimal("30.00"))`, línea 383) — confirma que la fuente actual del código y este archivo son consistentes, no contradictorias. Antes de 1997 la tabla usa tres columnas distintas ("Corriente" / "Bancario Corriente" / "Créditos Ordinarios Libre Asignación") en vez de la columna única "Comercial→Consumo y Ordinario" que usa el código desde 1997 — requiere la misma decisión de mapeo de columnas que ya documentó el design spec del Sprint 5 para el cambio de estructura de 2007.

**Código existente a reutilizar:**
- `app/engine/indexation/historical_index.py:316-323` (`TramoIBCUsura` dataclass) y `:591-644` (`get_ibc_usura_for_date`, `get_tramos_ibc_usura_between`) — sin cambios de forma, solo más filas.

**Código nuevo a crear:**
- ~90 tramos nuevos en `_TRAMOS_IBC_USURA` para 1971-10-29 a 1997-06-30.
- Decisión de diseño documentada: qué columna de la fuente pre-1997 (Corriente/Bancario Corriente/Créditos Ordinarios) mapea a la línea "IBC" que el motor usa hoy — probablemente "Bancario Corriente" por continuidad conceptual con el Art. 884 C.Co., pero debe quedar explícito en el design doc, no implícito.
- Opcional (fuera de alcance salvo que el despacho lo pida): cargar también la línea "Microcrédito" como una serie paralela — el calculador `i13.INTERESES-CORRIENTES-Y-DE-MORA-PARA-MICROCREDITOS.md` la usa y hoy BASTIUM solo modela "Consumo y Ordinario" (documentado como fuera de alcance en `historical_index.py:304-307`).

**Definición de Hecho:**
- `_TRAMOS_IBC_USURA` cubre sin huecos desde 1971-10-29.
- Tests que verifiquen al menos 3 tramos anteriores a 1997 contra el archivo fuente.
- Suite completa en verde.

---

## Sprint 82 — Cargar la serie histórica semanal de DTF (Banco de la República) como parámetro legal reutilizable 📋 Pendiente

**Prioridad sugerida:** Baja — DTF no se usa hoy en ningún cálculo de BASTIUM; el único caso de uso identificado (`i10`, condenas administrativas) no tiene un área clara dentro de las 6 áreas actuales. Se propone cargar el dato de todas formas (bajo costo, fuente ya lista) pero sin construir el calculador hasta resolver la pregunta de área.
**Depende de:** Nada para la carga de datos; el uso real depende de la respuesta a la pregunta nueva de este sprint.

**Contexto:** `docs/Archivos de referencia abogado/_markdown/historicodtf.md`, hoja `Datos`, trae la serie semanal real "Tasa de Depósitos a Término Fijo (DTF) a 90 días" desde 1984-01-20 hasta 2026-02-27 (columna 2, ej. fila `1984/01/20 | 36.45`), con fuente "Banco de la República con información de la Superintendencia Financiera de Colombia" (hoja `Información`, línea 2209). Grep confirma que "DTF" no aparece en ningún archivo bajo `app/` salvo un comentario de lista en `app/engine/financial/rate.py:15` — es decir, no hay ningún motor de DTF hoy, ni placeholder. El calculador `i10.INTERESES-TASADOS-A-LA-DTF-CONDENAS-ADMINISTRATIVAS.md` usa esta serie para liquidar intereses de mora en condenas contra el Estado bajo el Art. 195 núm. 4 de la Ley 1437 de 2011 (CPACA) — un escenario de "litigio contra una entidad pública" que no encaja claramente en ninguna de las 6 áreas de BASTIUM (`CIVIL_FAMILIA, COMERCIAL, LABORAL, SANCIONATORIO, HONORARIOS, TRIBUTARIO`).

**Código existente a reutilizar:**
- `app/engine/interest/provider.py` (`MemoryRateProvider`/`RatePeriod`) — mismo patrón que ya usa `historical_index.py` para tramos con vigencia; DTF es semanal, no mensual, así que la resolución por fecha necesitaría redondear al viernes/semana vigente, no reutilizar tal cual `get_ibc_usura_for_date`.

**Código nuevo a crear:**
- `app/engine/indexation/historical_index.py` (o módulo nuevo `historical_dtf.py`): serie DTF semanal 1984-2026 + función `get_dtf_for_date(fecha) -> Decimal`.
- Ningún calculador nuevo todavía — depende de la pregunta nueva de este sprint.

**Alcance explícitamente excluido:** implementar el calculador de intereses DTF para condenas administrativas — eso requiere primero saber si el despacho litiga contra entidades públicas y en qué área de BASTIUM debería vivir ese flujo.

**Definición de Hecho:**
- Serie DTF cargada y consultable por fecha, con tests contra al menos 5 valores puntuales del archivo fuente.
- Suite completa en verde.

---

## Sprint 83 — Documentar y decidir la convención "tasa mensual con prorrateo de 30 días" que usan la mayoría de plantillas del despacho (i1, i2, i7, i9, i13) 📋 Pendiente

**Prioridad sugerida:** Alta — afecta directamente la pregunta abierta del Sprint 76 (que hoy solo contempla 2 opciones) y toca el motor central de conversión de tasas que usan las 6 áreas.
**Depende de:** Sprint 76 (pregunta abierta existente — ampliada con este hallazgo).

**Contexto:** `app/engine/interest/rate_conversion.py:14-20` (`EffectiveRateConverter.annual_to_daily`) implementa hoy `(1+i)^(1/365)-1` para TODAS las tasas anuales del sistema (civil, comercial, laboral, tributaria — confirmado por los 6 call-sites: `app/services/area_strategy.py:278,1017,1020`, `app/engine/labor/moratory_indemnity.py:67`, `app/engine/tax/moratory_interest.py:50`, `app/engine/tax/actualizacion_867_1.py:73`). Sin embargo, al leer los calculadores reales del despacho para exactamente el mismo interés civil del 6% (`i7.INTERESES-CIVILES-6-ANUAL.md`, hoja `Liquidación`, línea 956: *"TASA NOMINAL ANUAL=[(1+TASA EFECTIVA ANUAL)Elevada a la(1/12)-1) x 12]"*) y verificando numéricamente contra la tabla de ejemplo (capital $5.000.000, tasa mensual mostrada "0,49%", interés de junio/2025 (30 días) = $24.500,00, interés de julio/2025 (31 días) = $25.316,67 = $24.500×31/30), la fórmula real que aplican es: **tasa mensual nominal = `[(1+EA)^(1/12)-1]×12`, prorrateada por `días_del_período/30`** (no por 365 ni 366, un mes comercial fijo de 30 días) — ni la Opción A (lineal `÷365`) ni la Opción B (compuesta `^(1/365)`) que ya contempla la pregunta del Sprint 76. Se verificó el mismo patrón numérico en `i1` (365 días, línea 885-889), `i2` (360 días, línea 884-892 — idéntico a i1 pese al nombre distinto), `i9` (tasa pactada, línea 845-864) y `i13` (microcrédito). Solo `i3.INTERESES-CORRIENTES-Y-DE-MORA-TASA-DIARIA-LEGAL-VIGENTE.md` (línea 868, fórmula `TND=[(1+TEA)^(1/365)-1]`) coincide exactamente con la fórmula que BASTIUM usa hoy — pero **BASTIUM no distingue estos casos**: aplica la fórmula de `i3` a todo, incluyendo el escenario (civil 6%) donde el propio despacho usa la de `i7`. El motor `app/engine/interest/monthly_interest.py` (clase `MonthlyInterest`, fórmula `I = C × i × t` sobre una tasa mensual ya dada) existe en el código pero tiene **cero llamadores** en `app/` (confirmado por grep) — está construido pero nunca conectado, y tampoco existe un `EffectiveRateConverter.annual_to_monthly`.

**Código existente a reutilizar:**
- `app/engine/interest/monthly_interest.py` (`MonthlyInterest.calculate`) — ya implementa `I=C×i×t`, solo le falta quien le pase la tasa mensual correcta y quien lo invoque.
- `app/engine/interest/rate_conversion.py` — agregar `annual_to_monthly` junto a `annual_to_daily`, mismo patrón.

**Código nuevo a crear:**
- `EffectiveRateConverter.annual_to_monthly(annual_percent) -> Rate` con la fórmula `[(1+EA)^(1/12)-1]×12` (nominal mensual), replicando `i1/i2/i7/i9/i13`.
- Prorrateo por 30 días fijos para períodos parciales dentro de un mes (nueva función o parámetro en `MonthlyInterest`/`DailyInterest`).
- Flag/config para decidir, por tipo de tasa, cuál de las 3 convenciones aplica — **no implementar el cambio de comportamiento real hasta tener respuesta del despacho** (ver Sprint 76).

**Definición de Hecho:**
- `annual_to_monthly` implementada y probada contra al menos 3 valores de `i1`/`i7` (ej. tasa mensual "0,49%" para EA=6%).
- El hallazgo queda documentado en el código (docstring) y enlazado a la pregunta ampliada del Sprint 76 — sin cambiar el comportamiento real de ninguna área todavía (eso es un sprint de implementación posterior, condicionado a la respuesta del despacho).
- Suite completa en verde.

---

## Sprint 84 — Alinear el interés moratorio tributario (E.T. art. 635) con la convención literal de la DIAN (366 días, lineal) o confirmar que el cálculo actual es el correcto 📋 Pendiente

**Prioridad sugerida:** Media — toca solo el área Tributario, pero es una discrepancia concreta y cuantificable entre lo que hace BASTIUM y lo que hacen las propias plantillas del despacho para el mismo escenario legal (E.T. art. 635 / Concepto DIAN 415 de 2021).
**Depende de:** Sprint 11a (motor de interés tributario), Sprint 15 (techo de usura Art. 867-1).

**Contexto:** `app/engine/tax/moratory_interest.py:1-9` documenta que el interés moratorio tributario es "tasa de usura vigente (línea Consumo y Ordinario) menos dos puntos porcentuales" — esto coincide exactamente con la premisa de `i4.INTERESES-DE-MORA-DIAN-ULTIMA-TASA-MENSUAL.md` e `i4A.INTERESES-DE-MORA-DIAN-DIFERENTES-TASAS-MENSUALES.md` (hoja `Liquidación`, línea 859/860: *"...a la tasa efectiva certificada por la superfinanciera, le resta 2 puntos y sin convertir esta tasa efectiva a nominal... la divide por 366 días"*). Pero el paso siguiente difiere: `moratory_interest.py:49-50` calcula `tasa_anual_tributaria = tramo.usura_anual - puntos_descuento` y luego `EffectiveRateConverter.annual_to_daily(tasa_anual_tributaria)` — es decir, aplica la fórmula **compuesta** de 365 días (`(1+i)^(1/365)-1`). Las plantillas i4/i4A del despacho, en cambio, dividen esa tasa (ya restados los 2 puntos) **linealmente entre 366** (verificado en i4A, línea 866: tasa diaria mostrada "-0.005479%" para una tasa mensual pactada baja — coherente con una división lineal simple, no compuesta). El propio archivo del despacho califica esta fórmula de "la ilógica matemática de la DIAN" (i4A línea 860), lo cual sugiere que el despacho **no necesariamente quiere que BASTIUM la replique** — pero si el objetivo es litigar/objetar liquidaciones DIAN usando la misma metodología que la autoridad tributaria aplica, la discrepancia (365-compuesto vs. 366-lineal) sí importa y debe ser una decisión explícita, no un accidente del motor genérico.

**Código existente a reutilizar:**
- `app/engine/tax/moratory_interest.py` completo — la resta de 2 puntos ya está correctamente implementada (`PUNTOS_DESCUENTO_ET_635`, línea 23, y el parámetro versionado `ET635_PUNTOS_DESCUENTO`, línea 48); solo la conversión anual→diaria (línea 50) está en discusión.

**Código nuevo a crear:**
- Ninguno hasta la respuesta del despacho — este sprint es de documentación/decisión, no de implementación (mismo criterio que Sprint 83).

**Definición de Hecho:**
- Discrepancia documentada en el docstring de `moratory_interest.py` con referencia cruzada a la pregunta nueva de este sprint.
- Suite completa en verde (sin cambios de comportamiento).

---

## Sprint 85 — Retroactivo y reliquidación pensional: mesada por mesada, incrementos e intereses de mora (Art. 141 Ley 100) ⚠️ Parcial

**Prioridad sugerida:** Alta — es la funcionalidad más solicitada de las 16 plantillas (4 de 16 la implementan: P1, P1A, P2, P7) y reutiliza en un 60% código que ya existe.
**Depende de:** Sprint 17 (IBL/tasa de reemplazo, ya implementado) y Sprint 13 (parametros_legales versionados).

**Contexto:** las plantillas `P1.RETROACTIVO-PENSIONAL-SALARIO-MINIMO.md`, `P1A.RETROACTIVO-PENSIONAL-SALARIO-MINIMO-INDEXADO-O-INCREMENTO-PENSIONAL-DEL-14-o-7.md`,
`P2.RETROACTIVO-PENSIONAL-CON-SALARIO-SUPERIOR-AL-MINIMO.md` y `P7.RELIQUIDACIÒN-PENSIONAL.md` comparten la misma estructura de 3 piezas, ninguna de las cuales
existe hoy conectada a una liquidación real:
1. **Recálculo mesada a mesada** de una pensión ya reconocida, ajustando cada mesada (incluida Mesada 13/14) contra el SMLMV vigente de cada año (P1, hoja `PH`,
   fila 12: "Mesadas incrementadas a salario mínimo actual", tabla informativa SMMLV 1992–2026 embebida) o contra un incremento porcentual pactado (P1A, hoja
   `PH`, fila 16: "Escriba al lado 100, si es la pensión completa o el porcentaje de incremento que corresponda (**conyuge: 14 — hijo: 7**)" — el incremento
   pensional del 14%/7% de sustitución pensional; P1A cita las sentencias **SU-140-19 y SL-2334-19** para verificar vigencia de esa prestación, fila 6).
2. **Indexación IPC de cada mesada** (Art. 21 Ley 100/1993) — esta pieza SÍ existe (`app/engine/indexation/ipc.py` → `IPCIndexation.calculate()`, ya reutilizado
   por `calcular_ibl` en `app/engine/labor/ibl.py:9-26`), fórmula citada igual en las 4 plantillas ("Mesada x (IPCF / IPCI)", ej. P1.md línea 536).
3. **Intereses de mora del Art. 141 Ley 100 de 1993** — "en caso de mora en el pago de las mesadas pensionales... la entidad reconocerá y pagará... la tasa
   máxima de interés moratorio vigente en el momento en que se efectué el pago" (texto literal citado en las 4 plantillas, ej. P1.md línea 998, P7.md línea
   1008). Esto **NO existe hoy** — es una tasa distinta al interés civil del 6% (Art. 1617 C.C.) o al usura comercial; es la tasa de usura vigente a la fecha
   de pago (no de causación), aplicada a mesadas pensionales impagas.

**Decisión de diseño a tomar con el usuario antes de codificar:** (a) ¿el recálculo mesada-por-mesada debe ser una función nueva independiente, o una
extensión de `calcular_ibl`/nueva `retroactivo_pensional.py`? (b) confirmar que "tasa máxima de interés moratorio vigente al momento del pago" del Art. 141
Ley 100 es equivalente al tope de usura que ya calcula `calcular_tope_usura` (ver abajo) y no una tasa distinta (interés bancario corriente puro, sin
multiplicador); (c) el incremento 14%/7% de P1A — confirmar con el despacho si sigue vigente tras SU-140-19/SL-2334-19 antes de ofrecerlo como opción en la
UI (la propia plantilla lo marca como dudoso).

**Código existente a reutilizar:**
- `app/engine/indexation/ipc.py` → `IPCIndexation.calculate()` (indexación IPC, ya usado en `ibl.py:24`).
- `app/engine/indexation/historical_index.py:83` → `get_smlmv_for_year()` (tabla SMLMV, ya carga los mismos valores 1992–2026 que trae P1).
- `app/engine/interest/usury_validator.py:13-24` → `calcular_tope_usura(ibc_vigente, fecha)` — ya resuelve "tasa máxima de interés moratorio vigente en
  `fecha`" vía `parametro_service`/`USURA_MULTIPLICADOR`; es el candidato natural para el Art. 141, evitando construir una tabla de tasas nueva.

**Código nuevo a crear:**
- `app/engine/labor/retroactivo_pensional.py`: `calcular_retroactivo_mesadas(...)` (recálculo mesada a mesada contra SMLMV o incremento %) e
  `interes_mora_pensional(mesadas_impagas, fecha_pago) -> Decimal` (Art. 141 Ley 100, reutilizando `calcular_tope_usura`).

**Definición de Hecho:**
- Test de recálculo de mesadas contra SMLMV histórico con al menos 3 años distintos.
- Test de interés de mora Art. 141 comparado contra un caso con tasa de usura conocida.
- Suite completa en verde.

---

## Sprint 86 — Bono pensional Tipo A (modalidades 1 y 2) con intereses DTF pensional 🔵 Bloqueado — pendiente de confirmación

**Prioridad sugerida:** Media-Alta — funcionalidad jurídica completamente nueva y de alta complejidad actuarial; no hay código previo del que partir.
**Depende de:** Nada del código actual; comparte maquinaria potencial con Sprint 87 (ver nota de reutilización cruzada abajo).

**Contexto:** `P12.BONO-PENSIONAL-TIPO-A-1.md`, `P13.BONO-PENSIONAL-TIPO-A-2.md` y `P14.CALCULO-BONO-PENSIONAL-CON-INTERESES.md` implementan el cálculo del
bono pensional (título que reconoce el Estado a quien se traslada de régimen) con una fórmula de reserva actuarial:
`Valor Reserva Actuarial a Fecha de corte = (PR x F1 + AF x F2) x F3` (P12.md línea 30), donde PR es la "pensión de referencia" calculada según la **fórmula
financiera del Decreto 1296 de 2022** (P12.md línea 25). Los factores F1/F2/F3 y la definición exacta de AF **no se lograron extraer con certeza del export**
(tabla de mortalidad y coeficientes actuariales, probablemente en columnas/hojas que el conversor Excel→Markdown no preservó con etiquetas claras) — esto es
una limitación de lectura, no una confirmación de que no existan. El valor de la reserva se actualiza a la fecha de pago con la **DTF Pensional**
(P12.md línea 53: "Reserva al corte x (DTFP(FP) / DTFP(FC))", **Art. 10 Decreto 1299 de 1994**, capitalización anual vía **Art. 7 Decreto 1887 de 1994**), y
solo es liquidable desde enero de 1994 ("año desde donde se puede liquidar intereses a la DTF pensional", P12.md líneas 34-35; P14.md línea 4: "Liquida desde
Enero de 1994, con la vigencia de la Ley 100"). También citan **Decreto 1748 de 1995** y **Art. 2 Decreto 2779 de 1994** (tabla de salarios medios
nacionales) como soporte adicional. Esta es una de las funcionalidades **más grandes de alcance completamente ausente** del código — no hay ninguna mención
de "bono pensional" en el repositorio.

**Decisión de diseño a tomar con el usuario antes de codificar:** (a) conseguir del despacho o releer directamente el Excel original (no el .md) para extraer
los factores F1/F2/F3, la tabla de mortalidad usada, y la tabla histórica completa de DTF Pensional mes a mes — sin esto no se puede codificar la fórmula
central; (b) confirmar si el despacho realmente litiga bonos pensionales tipo A modalidad 1 y 2 con la frecuencia suficiente para justificar el esfuerzo
(es la plantilla de mayor complejidad matemática de las 16).

**Código nuevo a crear:** `app/engine/labor/bono_pensional.py` (bloqueado hasta resolver la decisión de diseño arriba).

**Definición de Hecho:**
- Reserva actuarial reproducida contra un caso de prueba real aportado por el despacho.
- Suite completa en verde.

---

## Sprint 87 — Cálculo actuarial de cotizaciones omisas, intereses de mora en cotizaciones y salario básico deflactado (Decreto 1225/2024) 🔵 Bloqueado — pendiente de confirmación

**Prioridad sugerida:** Media — feature nueva, pero de menor complejidad que Sprint 86 porque reutiliza gran parte de su misma maquinaria (reserva actuarial + DTF
Pensional) y del motor de IBL ya existente.
**Depende de:** Sprint 86 (comparte reserva actuarial + DTF Pensional) y Sprint 17 (IBL toda-la-vida-laboral, ver nota abajo).

**Contexto:** agrupa 3 plantillas relacionadas — el empleador que **no pagó** cotizaciones a pensión (a diferencia de Sprint 86, donde el trabajador se traslada de
régimen voluntariamente):
- `P10.CALCULO-ACTUARIAL-DE-COTIZACIONES-OMISAS.md`: misma fórmula de reserva actuarial y DTF Pensional que P12-P14 (**Decreto 1296 de 2022**, **Art. 7
  Decreto 1887 de 1994**, **Art. 10 Decreto 1299 de 1994**, **Art. 2 Decreto 2779 de 1994**) — código altamente reutilizable con Sprint 86 si Sprint 86 se construye
  primero.
- `P10.A-CALCULO-INTERESES-MORA-EN-COTIZACIONES-PENSIONES.md`: interés de mora simple día a día sobre el capital adeudado (tasa diaria fija, ej. 0.116822%),
  y una fórmula de conversión de tasa efectiva a nominal: `TASA NOMINAL ANUAL=[(1+TASA EFECTIVA ANUAL)^(1/12)-1] x 12` **(Art. 2.2.3.3.1 Decreto 1833 de
  2016)** — esta conversión ya tiene equivalente funcional en `app/engine/interest/rate_conversion.py` (`EffectiveRateConverter`, mencionado en la pregunta
  abierta del Sprint 76), reutilizable directamente.
- `P10B.CALCULO-DEL-SALARIO-BASICO-DEFLACTADO-ART-20-DECRETO 1225-DE 2024.md`: NO es una fórmula nueva — es la **misma metodología de promedio ponderado por
  días de P4** (toda la vida laboral, indexado por IPC), simplemente re-etiquetada como insumo obligatorio de P10 bajo el Art. 20 del Decreto 1225 de 2024
  (P10B.md línea 2: "TABLA PARA ESTABLECER EL SALARIO BASE DEFLACTADO (SB), DEL CÁLCULO ACTUARIAL, ESTABLECIDO EN EL ARTÍCULO 20 DEL DECRETO 1225 DE 2024").
  Esto significa que **`calcular_ibl` de `app/engine/labor/ibl.py:9-26` ya puede producir este insumo sin cambios de fórmula**, siempre que se le pase el
  historial completo de vida laboral en vez de acotado a 10 años (la propia función no filtra por fecha, según su docstring).

**Decisión de diseño a tomar con el usuario antes de codificar:** igual que Sprint 86 — se necesita la tabla histórica de DTF Pensional y confirmar si esta reserva
actuarial comparte de verdad el mismo motor con Sprint 86 o si hay diferencias sutiles entre "bono pensional" y "cálculo de cotizaciones omisas" que ameriten
motores separados.

**Código existente a reutilizar:** `app/engine/labor/ibl.py:9-26` (`calcular_ibl`, para el salario básico deflactado de P10B), `app/engine/interest/rate_conversion.py`
(`EffectiveRateConverter`, para la conversión EA→nominal de P10A).
**Código nuevo a crear:** `app/engine/labor/cotizaciones_omisas.py` (bloqueado por la misma razón que Sprint 86: falta la tabla DTF Pensional completa y los
factores de reserva actuarial).

**Definición de Hecho:**
- Caso de prueba real aportado por el despacho.
- Suite completa en verde.

---

## Sprint 88 — Indemnización sustitutiva de pensión 🔵 Bloqueado — pendiente de confirmación

**Prioridad sugerida:** Media — feature nueva, autocontenida, y con la fórmula y todos los datos necesarios ya disponibles en la plantilla (no requiere
factores actuariales indeterminados como Sprint 86/87).
**Depende de:** Nada.

**Contexto:** `P6.INDEMNIZACION-SUSTITUTIVA-DE-PENSION.md` implementa el **Art. 3 del Decreto 1730 de 2001** (que reglamentó el **Art. 37 de la Ley 100 de
1993**): `I = SBC x SC x PPC`, donde SBC = salario base de cotización semanal promediado e indexado por IPC, SC = suma de semanas cotizadas, y PPC =
promedio ponderado de los porcentajes de cotización histórica del afiliado (P6.md línea 465, fórmula completa transcrita literalmente). La plantilla trae
una **tabla histórica de % de cotización a pensión por año, desde diciembre de 1966 hasta 2024** (P6.md líneas 466-495), citando **Art. 33 Decreto 3041 de
1966, Art. 2 Decreto 2879 de 1985, Art. 1 Decreto 1476 de 1992, Art. 3 Decreto 1730 de 2001**, y dos sentencias de referencia (**SL-16178 del 24-01-2002**:
aportes de 1985 al 6,5%; **SL-24369 del 25-05-2005**: aportes de 1995 al 12,5%). Esta tabla es un insumo puro de datos (no de fórmula) reutilizable también
por Sprint 87 (cotizaciones omisas) si en algún punto se necesita el % de cotización histórico ahí también.

**Decisión de diseño a tomar con el usuario antes de codificar:** confirmar la tabla de % de cotización 1966-2024 contra la fuente oficial (Decreto por
Decreto) antes de codificarla como cifra legal, siguiendo el mismo rigor que el Sprint 14 (tabla UVT) — la plantilla es de un tercero comercial, no fuente
primaria.

**Código nuevo a crear:** `app/engine/labor/indemnizacion_sustitutiva.py`: `calcular_indemnizacion_sustitutiva(historial_ibc, historial_pct_cotizacion) ->
Decimal`.

**Definición de Hecho:**
- Test contra un caso con historial de cotización sintético cubriendo al menos 2 tramos de % distintos.
- Tabla de % de cotización por año confirmada contra fuente oficial (no solo la plantilla comercial).
- Suite completa en verde.

---

## Sprint 89 — Monto mensual de pensión en Régimen de Ahorro Individual (RAIS) 🔵 Bloqueado — pendiente de confirmación

**Prioridad sugerida:** Media — el propio Sprint 17 excluyó explícitamente RAIS de su alcance ("Régimen de Ahorro Individual con Solidaridad (RAIS) — el PDF
solo describe Prima Media"), así que esto cierra un hueco ya documentado, no una feature imprevista.
**Depende de:** Nada.

**Contexto:** `P11.MONTO-MENSUAL-DE-PENSION-REGIMEN-AHORRO-INDIVIDUAL.md` calcula una anualidad financiera clásica:
`MMP = VP x i x (1+i)^n / ((1+i)^n - 1)`, donde VP = valor ahorrado en la cuenta individual, i = interés técnico (**4% EA, fijado por Resolución 0610 de
1994 de la Superfinanciera**, actualizada por Resolución 1555 de 2010), n = años de disfrute proyectados según **tabla de mortalidad de rentistas**
(hombres/mujeres, edad 15-110, P11.md líneas 328-429, tabla completa transcrita). Soporte jurídico: **Ley 100 Arts. 80 y 81** (P11.md línea 35). La propia
plantilla se autocalifica como "SIMPLE SIMULACIÓN APROXIMADA... que puede presentar variaciones con la liquidación hecha por el Fondo de Pensiones y no está
ajustada a la compleja fórmula descrita en la **Resolución 3023 de 2017** del Ministerio de Hacienda" (P11.md línea 4) — es decir, incluso la fuente
comercial admite que es una aproximación, no la fórmula regulatoria completa.

**Decisión de diseño a tomar con el usuario antes de codificar:** ¿el despacho necesita la fórmula completa de la Resolución 3023/2017 (más precisa, más
compleja), o basta la anualidad simplificada de esta plantilla para los casos que maneja? Si se acepta la simplificada, debe quedar documentado como
limitación conocida en el código, igual que la propia plantilla lo advierte.

**Código nuevo a crear:** `app/engine/labor/rais.py`: `calcular_monto_mensual_pension_rais(valor_ahorro, interes_tecnico, edad, sexo) -> Decimal`
(tabla de mortalidad de rentistas como constante del módulo).

**Definición de Hecho:**
- Test con al menos 2 combinaciones edad/sexo usando la tabla de mortalidad.
- Suite completa en verde.

---

## Sprint 90 — IBL del régimen ISS anterior a la Ley 100: últimas 100 y 150 semanas 🔵 Bloqueado — pendiente de confirmación

**Prioridad sugerida:** Baja-Media — régimen histórico (aplica a hechos generadores anteriores a 1994), menos frecuente que el resto pero con una fórmula
genuinamente distinta a la que ya existe.
**Depende de:** Sprint 70 (vigencia de leyes por año) — es exactamente el tipo de "fórmula histórica distinta según la fecha del hecho" que ese sprint busca
resolver de forma estructural; puede adelantarse igual sin esperar a Sprint 70 si se trata como caso puntual.

**Contexto:** `P15.IBL-100-SEMANAS.md` y `P16.IBL-150-SEMANAS.md` implementan un mecanismo **completamente distinto** al de `calcular_ibl` actual: en vez de
promediar salarios indexados por IPC, dividen la suma de los salarios de las últimas 100 (o 150) semanas cotizadas por 100 (o 150), multiplican por un
**factor fijo de 4.33** (P15.md línea 32: "Factor por el que multiplica la 100ava parte"), y aplican una tasa base de **45%** más un adicional de **3% por
cada 50 semanas adicionales** (P15) o **1,2% por cada 50 semanas adicionales** (P16), con tope del **90%** (no 80% como el resto) — "si el total supera el
90% sobreescriba 90" (P15.md línea 37, P16.md línea 54). **Ninguna de las dos plantillas cita el artículo/decreto exacto** que respalda esta fórmula ni el
origen del factor 4.33 — es presumiblemente el régimen del **ISS (Acuerdo 049 de 1990 o similar, anterior a la Ley 100/1993)**, pero esto necesita
confirmación del despacho antes de codificar, no debe asumirse.

**Decisión de diseño a tomar con el usuario antes de codificar:** (a) confirmar la norma exacta que respalda esta fórmula (el 90% de tope y el factor 4.33
en particular); (b) confirmar en qué casos reales el despacho todavía liquida bajo este régimen (afiliados con historia laboral anterior a 1994).

**Código nuevo a crear:** `app/engine/labor/ibl.py` (extender): `calcular_ibl_regimen_iss(salarios_ultimas_n_semanas, n, factor, pct_base, pct_adicional_por_50,
tope) -> Decimal`.

**Definición de Hecho:**
- Norma legal exacta confirmada por el despacho antes de mergear.
- Test de 100 semanas y test de 150 semanas con datos sintéticos.
- Suite completa en verde.

---

## Sprint 91 — Tasa de reemplazo: extender a pensión de invalidez (grados 1 y 2), régimen 1993-2003 y régimen de transición 🔵 Bloqueado — pendiente de confirmación

**Prioridad sugerida:** Media-Alta — `calcular_tasa_reemplazo` de `app/engine/labor/ibl.py:60-89` **solo implementa la tabla "desde el año 2004 en
adelante"** de la Ley 797/2003; las otras 3 variantes que trae la misma plantilla de referencia (P9) no están cubiertas y producirían resultados
incorrectos si se aplicaran a un caso de invalidez o a un causante de 1993-2003.
**Depende de:** Sprint 70 (parcialmente — ver nota de impacto) y Sprint 17.

**Contexto:** `P9.TASA-DE-REEMPLAZO-LEY-797-2003.md` (hoja `Hoja1`) trae 5 tablas de tasa de reemplazo distintas, de las cuales el código de hoy solo
implementa la primera:
1. **"Con la Ley 797 de 2003, desde el año 2004 en adelante"** (P9.md fila 11): fórmula `r = 65.5 − 0.5·s`, con bono de 1,5% por cada 50 semanas — **esto
   SÍ está implementado** en `calcular_tasa_reemplazo`.
2. **"Con la Ley 797 de 2003, desde 1993 hasta 2003"** (P9.md fila 17): tabla sin columna SMLV/S×0,5 — **fórmula distinta, no implementada**.
3. **"Régimen de Transición"** (P9.md fila 23): tasa fija ("75%, 90% o la que corresponda", Mesada = IBL × tasa fija) — **no implementada**.
4. **Pensión de Invalidez Grado 1** (50%-65,99% de invalidez): base **45% del IBL + 1,5% por cada 50 semanas sobre las primeras 500, tope 75%**
   (confirmado con cifras exactas en P9.md filas 59-91: 500 semanas→45,0%, 550→46,5%... 1500→75,0%, incrementos de 1,5 cada 50 semanas) — **no implementada**.
5. **Pensión de Invalidez Grado 2** (≥66% de invalidez): base **54% del IBL + 2% por cada 50 semanas sobre las primeras 800, tope 75%** (P9.md filas 81-91:
   800→54,0%... 1400→75,0%, incrementos de 2,0 cada 50 semanas) — **no implementada**.

Nota positiva: la tabla de la tasa 2004+ (P9.md filas 184-535) **confirma exactamente** que `semanas_minimas_requeridas()` de `ibl.py:49-57` está bien
implementada — verificado año por año contra el diccionario `_SEMANAS_MINIMAS_POR_ANIO` del código: 2005→1050, 2006→1075, 2007→1100, 2008→1125,
2009→1150, 2010→1175, 2011→1200, 2012→1225 coinciden exactamente con "2005-1050", "2006-1075", "2007-1100"... de la plantilla. También se confirmó que el
código **ya cumple** el criterio de la sentencia CSJ 3501/2022 citada por la plantilla ("contabilizar las semanas por encima de las 1800 y hasta un tope del
80%"): `calcular_tasa_reemplazo` no trunca `semanas_cotizadas` en 1800, solo aplica el tope final de 80% al resultado — la tabla de P9 confirma esto contando
bloques de 50 semanas sin cortar en 1800 (llega hasta 2200 semanas = 27,0% de bono en 2026).

**Decisión de diseño a tomar con el usuario antes de codificar:** (a) confirmar la fórmula exacta 1993-2003 (la plantilla no la deja ver con datos, solo la
estructura de columnas); (b) confirmar los porcentajes fijos válidos del régimen de transición (75%/90%/"la que corresponda" — necesita la regla de cuándo
aplica cada uno); (c) confirmar si el software debe ofrecer pensión de invalidez como un tipo de caso separado del de vejez (afecta a `LaboralStrategy` /
futura `PensionalStrategy`).

**Código existente a reutilizar:** `app/engine/labor/ibl.py:60-89` (`calcular_tasa_reemplazo`, patrón de piso/techo/bono a replicar para invalidez).
**Código nuevo a crear:** `calcular_tasa_reemplazo_invalidez(ibl, grado, semanas_cotizadas) -> Decimal` en el mismo módulo.

**Definición de Hecho:**
- Tests de invalidez grado 1 y grado 2 reproduciendo exactamente las cifras de P9.md (ej. 800 semanas grado 2 → 54%, 1500 semanas grado 1 → 75%).
- Fórmula 1993-2003 y régimen de transición confirmados con el despacho antes de codificar.
- Suite completa en verde.

---

## Sprint 92 — Laboral: indemnización por despido injustificado (Art. 64 CST) 📋 Pendiente

**Prioridad sugerida:** Alta — es probablemente el tipo de proceso laboral más común (despido sin justa
causa), y hoy BASTIUM lo omite silenciosamente pese a tener un archivo con nombre similar
(`moratory_indemnity.py`) que podría hacer pensar que ya está cubierto.

**Depende de:** Sprint 3 (Área Laboral, ya completo — extiende `LaboralStrategy`) y Sprint 5 (SMLMV
histórico, ya completo — necesario para el umbral de 10 SMMLV que distingue las tablas).

**Contexto:** `L4.INDEMNIZACIONPORDESPIDOLABORALYSANCIONMORATORIA.md` (hoja `Hoja1`) trae en realidad DOS
cálculos distintos bajo el mismo nombre de archivo:
1. **"Cálculo Sanción Moratoria"** (filas 64-70): un día de salario por cada día de mora hasta 24 meses,
   luego intereses moratorios — esto SÍ está implementado, y coincide, en
   `app/engine/labor/moratory_indemnity.py` (`MoratoryIndemnityCalculator`, límite `LIMITE_FASE1_DIAS = 720`
   días, fase 2 con tasa de usura vía `get_ibc_usura_for_date`), wireado en
   `app/services/area_strategy.py:1240-1257` como evento `SANCION_MORATORIA`.
2. **"Indemnización por Despido"** (filas 4-60): esto es Art. 64 CST, un concepto legal completamente
   distinto (compensación por terminación sin justa causa, no por mora en el pago), y **no existe en ningún
   archivo del proyecto** (confirmado por `grep -i "despido"` en todo `app/`, único resultado en
   `app/views/obligaciones.py` sin relación). La plantilla trae varios regímenes de días de salario según:
   - Umbral de salario: menor o mayor/igual a 10 SMMLV.
   - Duración del contrato: ≤1 año, entre 1-5 años, 5-10 años, >10 años.
   - Fecha de ingreso relativa a la vigencia de la Ley 50/1990 (contratos anteriores tienen un régimen más
     favorable que los posteriores, regidos por la Ley 789/2002).
   - Ejemplos puntuales leídos directamente de la plantilla (no toda la tabla): término indefinido <10 SMMLV
     post-Ley 789/2002 con >1 año: "30 Días de salario Básico" el primer año + "20 Días... por cada año
     subsiguiente"; el mismo caso pre-Ley 50/1990: "45 Días... por el primer año y a 15 Días... por cada año
     subsiguiente"; término fijo/obra-labor: "el tiempo que faltare para cumplir el plazo... la indemnización
     no será inferior a quince (15) días".
   - **Inconsistencia detectada en la propia plantilla, no resuelta en esta investigación**: dos secciones
     citan la misma fecha "27 de diciembre de 1.992" pero una la atribuye a la "ley 789 de 2002" y la otra a
     la "ley 50 de 1990" (la Ley 50 es de 1990, no de 1992) — antes de codificar, hay que confirmar con el
     despacho la fecha de corte real (probablemente 1° de enero de 1991, vigencia de la Ley 50/1990).

**Decisión de diseño a tomar con el usuario antes de codificar:**
- Confirmar la fecha de corte real entre régimen Ley 50/1990 y Ley 789/2002 (ver inconsistencia arriba).
- Cómo capturar los datos que hoy `Obligacion` no tiene: tipo de contrato (indefinido/fijo/obra-labor),
  si el despido fue con o sin justa causa, y (para el régimen pre-1990) si el trabajador venía cotizando
  antes de esa fecha.
- Si esta indemnización coexiste con la `SANCION_MORATORIA` ya implementada (son conceptos distintos y
  compatibles legalmente — el despido injustificado no impide que además haya mora en el pago de
  prestaciones — pero conviene confirmarlo explícitamente antes de sumarlas en el mismo expediente).

**Código existente a reutilizar:** `app/engine/labor/moratory_indemnity.py` como patrón de diseño (un
calculador puro con `@dataclass(frozen=True)` de resultado); `app/engine/indexation/historical_index.py::get_smlmv_for_year`
para el umbral de 10 SMMLV; `LaboralStrategy` (`area_strategy.py:1052`) para el wiring.

**Código nuevo a crear:**
- `app/engine/labor/dismissal_indemnity.py` (sugerido): `DismissalIndemnityCalculator` con los regímenes
  de días por tramo de antigüedad/salario/fecha de ingreso.
- Campos nuevos en `Obligacion` (o modelo aparte): tipo de contrato, si el despido fue injustificado,
  fecha de ingreso para el corte legal.
- Wiring en `LaboralStrategy.liquidar()` como nuevo evento (ej. `INDEMNIZACION_DESPIDO`).

**Definición de Hecho:**
- Tests para cada quiebre de tramo (1 año, 5 años, 10 años, umbral de 10 SMMLV, contrato a término fijo con
  piso de 15 días).
- Confirmación del despacho sobre la fecha de corte 1990/1992 registrada en `Preguntas-Para-Abogado-Abiertas.md`.
- Suite completa en verde.

---

## Sprint 93 — Laboral: salarios y prestaciones dejadas de percibir con reajuste anual (IPC o SMMLV) — reabre la exclusión del Sprint 75 📋 Pendiente

**Prioridad sugerida:** Alta — reutiliza infraestructura que ya existe casi completa (bajo costo de
implementación) para un tipo de proceso común (reintegros, salarios caídos).

**Depende de:** Sprint 3 (Área Laboral), Sprint 41/75 (`app/services/reajuste_anual.py`, ya completos),
Sprint 5 (series históricas IPC/SMLMV, ya completo).

**Contexto:** `L5.SALARIOS-Y-PRESTACIONES-SOCIALES-DEJADAS-DE-PERCIBIR(incrementoinflacion).md` y
`L6...(incremento-salario-minimo).md` (hoja `CALCULO-IPC` en ambos) NO liquidan el finiquito de un
contrato — reconstruyen salario + prestaciones para un período en que el trabajador **no estuvo
contratado** (típicamente reintegro por despido declarado nulo, o el período de "salarios caídos"), año por
año, incrementando el salario anualmente según un índice. La estructura es idéntica en ambas plantillas
(columnas DESDE/HASTA por año, SALARIO INCREMENTADO ANUALMENTE, # DE MESES, CESANTIAS/INTERESES A LAS
CESANTIAS/PRIMAS/VACACIONES por bloque anual, sumado en un "GRAN TOTAL"), y solo difieren en el índice de
reajuste: L5 usa la tabla de variación IPC anual (hoja `DATOS`, serie 1967-2025, idéntica a la ya cargada en
`app/engine/indexation/historical_index.py` desde el Sprint 5); L6 usa la tabla histórica de SMMLV (hoja
`DATOS`, serie 1980-2026, también ya cargada en el mismo archivo).

El Sprint 75 (`docs/Pendientes.md`) excluyó a Laboral explícitamente de la generalización de
"cuotas recurrentes con reajuste anual" con la razón: *"Laboral es estructuralmente incompatible: una
obligación = un contrato completo, no una serie de cuotas"* — verificado en código,
`_validar_obligacion_laboral` (`app/services/area_strategy.py:1323-1328`) efectivamente bloquea
`TipoObligacion.RECURRENTE` con `ValueError`. Esa razón es correcta para el modelo del Sprint 3 (finiquito de
un contrato vigente-hasta-fecha_fin), pero **no aplica al patrón de L5/L6**: ahí no hay "cuotas de un
contrato", hay una reconstrucción retroactiva de lo que el trabajador habría devengado mes a mes si hubiera
seguido activo, con reajuste el 1° de enero de cada año — exactamente la forma que
`app/services/reajuste_anual.py::generar_cuotas_mensuales`/`reajustar_capital_anual` (Sprint 41/75) ya
resuelve para Civil/Familia y Comercial. Más aún: `database/models.py` ya define
`TipoReajusteAnual.IPC`/`TipoReajusteAnual.SMMLV` — exactamente las dos variantes que separan L5 de L6 — y
`reajustar_capital_anual` (`app/services/reajuste_anual.py:58-86`) ya implementa ambas fórmulas
(`IPCIndexation.calculate()` para IPC, `_pct_reajuste_smmlv` para SMMLV). Y los divisores 360/720 que usan
las cesantías/intereses/prima/vacaciones de L5/L6 por bloque anual son los mismos que ya usa `LaborScheduler`
(`app/engine/temporal/schedulers/labor.py`).

**Decisión de diseño a tomar con el usuario antes de codificar:**
- Cómo modelar esto sin romper el invariante "1 obligación = 1 contrato" del Sprint 3: ¿una categoría nueva
  (ej. `SALARIOS_DEJADOS_DE_PERCIBIR`) que sí admita generación de cuotas anuales dentro de
  `LaboralStrategy`, coexistiendo con `LIQUIDACION_CONTRATO_LABORAL` (`app/core/constants.py:25-27`) que
  sigue igual? ¿o un tipo de expediente/obligación aparte?
- Confirmar con el despacho en qué tipo de proceso se usa cada variante (reintegro con salarios caídos,
  contrato realidad con período sin reconocimiento, otro) y si la elección IPC vs. SMMLV es discrecional del
  abogado según el caso o depende de una regla fija.

**Código existente a reutilizar:** `app/services/reajuste_anual.py` (`generar_cuotas_mensuales`,
`reajustar_capital_anual`, `TipoReajusteAnual.IPC`/`SMMLV` ya soportados); `app/engine/temporal/schedulers/labor.py::LaborScheduler`
(mismos divisores 360/720 por bloque anual); `app/engine/indexation/historical_index.py` (`get_ipc_for_date`,
`get_smlmv_for_year`, Sprint 5, ya cubre los años de ambas tablas).

**Código nuevo a crear:** adaptar/extender el generador de cuotas para producir bloques anuales de salario
con `LaborScheduler` aplicado a cada bloque (en vez de una única liquidación de finiquito); nueva
categoría/submodo en `LaboralStrategy`; relajar `_validar_obligacion_laboral` específicamente para este
submodo nuevo (sin abrir `RECURRENTE` de forma general al área, que sigue siendo incorrecto para el resto de
categorías Laboral).

**Definición de Hecho:**
- Test de integración que reproduzca un caso sintético multi-año con incrementos IPC conocidos, verificando
  el "GRAN TOTAL" contra el patrón exacto de L5.
- Mismo test para L6 con incrementos SMMLV conocidos.
- Suite completa en verde.

---

## Sprint 94 — Laboral: contrato realidad (privado y sector público) 📋 Pendiente

**Prioridad sugerida:** Alta/Media — es un tipo de proceso muy frecuente en la práctica colombiana
(relación laboral disfrazada de prestación de servicios), pero es una feature jurídica grande que necesita
validación del despacho antes de codificar cifras.

**Depende de:** Sprint 3 (Área Laboral), Sprint 16 (Seguridad social, ya completo — para comparar contra los
porcentajes de aportes), Sprint 5/8 (series IPC históricas, ya completas).

**Contexto:** `L7.LIQUIDACIÒN DEPRESTACIONESSOCIALESENCONTRATOREALIDAD.md` (privado) y
`L8.LIQUIDACIONDEPRESTACIONESSOCIALESPUBLICOCONTRATOREALIDAD.md` (sector público) liquidan, año por año
hasta un "AÑO FINAL HASTA DONDE SE INDEXA", todas las prestaciones sociales que un trabajador NUNCA recibió
porque estaba disfrazado como contratista independiente, indexadas por IPC desde cada año hasta el año de
cierre elegido. L7: cesantías, intereses, primas, vacaciones + "APORTE SALUD (8,5%)" + "APORTE PENSIÓN
(12%)", todo indexado, consolidado en "TOTAL PRESTACIONES SOCIALES + SALARIOS". L8 (sector público) agrega
un catálogo más largo, propio del empleo público: prima de servicio, prima de navidad, vacación, prima de
vacación, bonificación por servicio, bonificación especial por recreación (todas indexadas), auxilios de
transporte/alimentación indexados, y aportes salud (8%)/pensión (12%). La plantilla L8 trae además una
anotación sin explicar del todo: la bonificación por servicio "corresponde al 35%, pero hasta 2 smmlv,
escriba 50%" — una regla escalonada que no es autoexplicativa desde el propio Excel.

`grep -i "contrato_realidad\|ContratoRealidad"` no encontró nada en `app/` — no existe ningún concepto de
"contrato realidad" en el código hoy. `_capital_concepts` (`app/engine/liquidation/engine.py`) y
`CATEGORIAS_LABORAL` (`app/core/constants.py:25-33`, una sola categoría: `LIQUIDACION_CONTRATO_LABORAL`) no
tienen ningún concepto relacionado. Un matiz importante para no codificar a ciegas: `SeguridadSocialCalculator`
(`app/engine/labor/seguridad_social.py`, Sprint 16) calcula la cotización **total** (empleador + trabajador,
16% pensión + 12.5% salud, decisión explícita del Sprint 16), mientras que L7/L8 muestran cifras distintas y
más bajas (8.5%/12% en L7, 8%/12% en L8) que parecen ser solo la porción del empleador — no son el mismo
cálculo, y no es evidente desde el Excel cuál es la fórmula jurídicamente correcta para un reclamo de
contrato realidad (el trabajador, como "independiente", ya pagaba su propio aporte completo por su cuenta).

**Decisión de diseño a tomar con el usuario antes de codificar:**
- Confirmar el fundamento y la fórmula exacta de la regla "35%/hasta 2 SMMLV escriba 50%" de la
  bonificación por servicio (L8).
- Confirmar si los aportes reclamables en un contrato realidad son el total (igual que Sprint 16) o solo la
  porción del empleador (8.5%/12% en L7, 8%/12% en L8) — son cifras distintas, no auto-explicativas.
- Decidir si esto se modela como una nueva categoría/submodo de `LaboralStrategy` (mismo patrón del Sprint
  Sprint 93) o como un flujo completamente aparte, dado el tamaño del catálogo de conceptos (especialmente en L8).

**Código existente a reutilizar:** motor de indexación IPC (`app/engine/indexation/historical_index.py`,
`app/engine/indexation/ipc.py`) que ya soporta la serie 1971-2026 que traen L7/L8 (ya cargada desde
Sprint 5/8); `LaborScheduler` como base de las prestaciones del régimen privado (L7); `SeguridadSocialCalculator`
como referencia de comparación (no necesariamente reutilizable tal cual, ver decisión de diseño arriba).

**Código nuevo a crear:** motor de "contrato realidad" — privado (L7: cesantías + intereses + primas +
vacaciones + aportes salud/pensión, todo indexado IPC año a año) y público (L8: + prima de navidad, prima de
vacación, bonificación por servicio con el tramo 35%/50%, bonificación especial de recreación, auxilios
transporte/alimentación indexados).

**Definición de Hecho:**
- Tests con un caso sintético multi-año que verifique el consolidado contra el patrón L7 por separado del
  patrón L8.
- Confirmación del despacho sobre la regla de bonificación por servicio y sobre la base de aportes,
  registrada en `Preguntas-Para-Abogado-Abiertas.md`.
- Suite completa en verde.

---

## Sprint 95 — Laboral: horas extra diurnas/nocturnas y recargos dominicales/festivos 📋 Pendiente

**Prioridad sugerida:** Media — gap real y acotado, pero no se debe fijar ningún porcentaje sin confirmar
vigencia por fecha, dado que la Ley 2466 de 2025 (reforma laboral) está migrando progresivamente entre
2025-2027 tanto el horario nocturno como el recargo dominical/festivo.

**Depende de:** Sprint 3 (Área Laboral, ya completo).

**Contexto:** `L3.HORASEXTRASYRECARGOS.md` (hoja `Hoja1`) liquida, a partir de un salario básico mensual y
número de horas laboradas al mes, siete conceptos independientes (cada uno con "Valor por hora" / "No. Horas
Laboradas Mensualmente" / "Valor Total"): Horas Extras Ordinarias Diurnas, Horas Extras Ordinarias
Nocturnas, Recargo Nocturno x Hora, Horas Extras Festivas Diurnas, Horas Extras Festivas Nocturnas, Recargo
Festivo Diurno x hora, Recargo Festivo Nocturno x hora. `grep -i "hora_extra\|recargo"` no encontró ningún
resultado en todo `app/` — es un gap total, no una variación de algo existente.

Los porcentajes legales tradicionales (HED 25%, HEN 75%, recargo nocturno 35%, HEFD 100%, HEFN 150%, recargo
dominical/festivo 75%) vienen de los Arts. 168-179 CST, pero la Ley 2466 de 2025 cambió recientemente tanto
la definición de "hora nocturna" (corrimiento progresivo del inicio de la jornada nocturna) como el
porcentaje del recargo dominical/festivo (subiendo escalonadamente hasta 100% en 2027) — por lo que fijar un
solo porcentaje sin vigencia por fecha replicaría el mismo tipo de error que ya se evitó en otras partes del
sistema (ej. tasa de usura por tramos de fecha, Sprint 5).

**Decisión de diseño a tomar con el usuario antes de codificar:** confirmar la tabla de transición exacta de
la Ley 2466/2025 (fechas de corte y porcentajes/horarios en cada tramo 2025-2027), siguiendo el mismo patrón
de "vigencia por fecha" que ya usa `parametro_service.py` para otros porcentajes legales.

**Código nuevo a crear:** `app/engine/labor/horas_extra.py` (calculador puro de los 7 conceptos); catálogo
de porcentajes con vigencia por fecha en `app/services/parametro_service.py`; campos nuevos para capturar
horas por concepto; wiring en `LaboralStrategy`.

**Definición de Hecho:**
- Tests para los 7 conceptos, con al menos 2 vigencias distintas de porcentaje si se confirma la transición
  de la Ley 2466/2025.
- Confirmación del despacho registrada en `Preguntas-Para-Abogado-Abiertas.md`.
- Suite completa en verde.

---

## Sprint 96 — Laboral: liquidación de prestaciones para trabajo doméstico por días/jornada parcial 📋 Pendiente

**Prioridad sugerida:** Baja/Media — es principalmente un gap de captura de datos, no necesariamente de
fórmula (pendiente de confirmar).

**Depende de:** Sprint 3 (Área Laboral, ya completo).

**Contexto:** `L2.COMPROBANTEDELIQUIDACIONDEPRESTACIONESSOCIALES.md` y
`L2A...EMPLEADADOMESTICA.md` (ambos hoja `liquidacion`) comparten exactamente la misma estructura de
CONCEPTO/DIAS/DEVENGADO para CESANTIAS/INTERESES CESANTIAS/VACACIONES/PRIMA — no se encontró ninguna fórmula
distinta entre ambas plantillas. La diferencia real de L2A es de **captura de datos**: en vez de un salario
mensual directo, pide "Salario diario" y "días laborados en la semana", y calcula un "Salario Base Mensual"
= `salario_diario × días_laborados_semana / 7 × 30` (y lo mismo para el auxilio de transporte diario), con
una nota explícita: *"El número de días corresponde a los días calendario que dura toda la relación laboral
y no a los dias laborados"* (para cesantías) y el cierre: *"el valor del salario corresponde al que se
recibe en el total por el mes, por lo tanto para efectos de prestaciones sociales se contabiliza como de 30
días"*.

`database/models.py` no tiene ningún campo `salario_diario`/`dias_laborados_semana` en `Obligacion`, y
`LaborScheduler`/`LaboralStrategy` siempre esperan un único `valor` mensual ya resuelto. Hoy, un abogado que
liquide un contrato de trabajo doméstico pagado por día (muy común: 1-3 días/semana) tiene que precalcular a
mano el equivalente mensual fuera de BASTIUM antes de digitarlo — perdiendo el rastro de auditoría que el
resto del sistema sí ofrece.

**Decisión de diseño/pregunta al despacho a resolver antes de codificar:** ¿existe alguna diferencia de
**fórmula** (no solo de captura de datos) entre las prestaciones de un trabajador doméstico y el régimen
general, después de la Ley 1788 de 2016 (que unificó la prima de servicios para el servicio doméstico)? Si
no hay diferencia de fórmula, este sprint es puramente de UX (agregar el conversor salario_diario→mensual al
formulario, sin motor nuevo); si sí la hay, hace falta identificarla antes de construir.

**Código nuevo a crear (si el despacho confirma que no hay diferencia de fórmula):** campos opcionales
`salario_diario`/`dias_laborados_semana`/`auxilio_transporte_diario` en el formulario Laboral, con
conversión automática al `valor` mensual que ya consume `LaborScheduler` — sin motor de cálculo nuevo.

**Definición de Hecho:**
- Confirmación del despacho sobre si hay diferencia de fórmula, registrada en
  `Preguntas-Para-Abogado-Abiertas.md`.
- Test de conversión salario_diario→mensual con el ejemplo de la plantilla L2A.
- Suite completa en verde.

---

## Sprint 97 — Nuevo dominio: Responsabilidad Civil Extracontractual / Indemnización de Perjuicios (decisión de alcance y arquitectura) 🔵 Bloqueado — pendiente de confirmación

**Prioridad sugerida:** Alta como decisión (bloquea Sprint 98-Sprint 100), Media como implementación — el despacho envió 8 plantillas completas (X1-X6, X8, X10) de un dominio jurídico que hoy no existe en BASTIUM ni siquiera como esqueleto activo.

**Depende de:** Nada. Bloquea Sprint 98, Sprint 99 y Sprint 100.

**Contexto:** BASTIUM hoy no tiene ningún soporte real para indemnización de perjuicios extracontractuales. Lo que existe (`DANO_EMERGENTE`, `LUCRO_CESANTE_CONSOLIDADO`, `DANOS_MORALES` en `app/core/constants.py` y `app/engine/liquidation/engine.py`) son solo etiquetas de un capital plano dentro de Civil/Familia — sin fórmula actuarial, sin tabla de mortalidad, sin distinción de beneficiario. `CivilIndemnityScheduler` (`app/engine/temporal/schedulers/civil.py`) es código muerto: su docstring habla de "sentencias de Responsabilidad Civil Extracontractual" pero ninguna `AreaStrategy` lo usa, solo aparece en `tests/temporal/test_civil.py` y `tests/integration/test_universal.py`.

Las 8 plantillas de Ediciones Sistematizadas Equidad que cubren este dominio (`X1.DAÑO-EMERGENTE.md`, `X2.LUCRO-CESANTE-VICTIMA-INCAPACITADO.md`, `X3.LUCRO-CESANTE-CONYUGE-E-HIJO.md`, `X4.LUCRO-CESANTE-PADRES.md`, `X5.LUCRO-CESANTE-PADRES-HIJO-MENOR-FALLECIDO.md`, `X6.LIQUIDACION-BENEFICIO-DEJADO-DE-PERCIBIR-COMO-FRUTO-CIVIL.md`, `X8.INDEMNIZACION-PERJUCIOS-OCASIONADOS-AL-PENSIONADO-FONDO-PRIVADO.md`, `X10.LUCRO-CESANTE-X BENEFICIO DEJADO DE PERCIBIR.md`) comparten un núcleo matemático (hoja `CalculosIndemnizacion` en X2-X5/X8/X10, hoja `PH` en X1/X6) que BASTIUM no tiene: una fórmula financiera de anualidad (`S = Ra × [(1+i)ⁿ-1]/i` para el periodo consolidado, `S = Ra × [(1+i)ⁿ-1]/[i(1+i)ⁿ]` para el periodo futuro, donde `i` es la tasa judicial mensual equivalente al 6% EA — 0,4867% nominal mensual, Art. 2232 C.C.), combinada con tablas de mortalidad de rentistas (Resolución 1555 de 2010 Superfinanciera, hoja `TablasMortalidad`, tabla separada por sexo, edad → años de expectativa de vida) para proyectar el periodo futuro.

**Código a reutilizar (ya existe, verificado):**
- `app/engine/indexation/smmlv.py` — tabla histórica SMMLV, la usan X2-X5 para la "Renta Actualizada" cuando el ingreso es el mínimo.
- `app/services/parametro_service.py` clave `CIVIL_ANNUAL_RATE` — el 6% EA del Art. 2232 C.C. ya es un parámetro versionado.
- `app/engine/indexation/ipc.py` (`IPCIndexation`) — el paso de indexación previo (`Ra = Índice_Final/Índice_Inicial × R`) es el mismo cálculo del Sprint 8/20.

**Código que NO existe y habría que construir desde cero:**
- Conversión de tasa EA a **mensual** (hoy solo existe `annual_to_daily` en `app/engine/interest/rate_conversion.py`).
- Fórmula financiera de anualidad (valor futuro y valor presente de renta), inexistente en cualquier forma en el motor.
- Tabla de mortalidad de rentistas (Resolución 1555/2010) por sexo/edad → años de expectativa de vida.
- Reglas de reparto por tipo de beneficiario: X3 usa 50%/cónyuge + 50%/hijo(s) (o 100% si solo se reclama para una parte) con 25% de descuento por "sostenimiento de la víctima"; X4/X5 usan 50%/padre + 50%/madre, cada uno con su propia expectativa de vida (tablas de mortalidad distintas por sexo); X5 además usa "años que le hacían falta a la víctima para 25" en vez de expectativa de vida de la víctima (hijo menor fallecido, no tenía ingreso propio, se usa SMMLV en vez de indexación IPC de un salario real).

**Decisión de diseño a tomar con el usuario antes de codificar (obligatorio, es una posible área nueva):**
1. ¿Esto se modela como una **7ª área de derecho** (`AreaDerecho.RESPONSABILIDAD_CIVIL` o similar) o como un **submodo dentro de CIVIL_FAMILIA** (reutilizando `DANO_EMERGENTE`/`LUCRO_CESANTE_CONSOLIDADO` pero dándoles un motor de cálculo propio en vez de tratarlos como capital plano)? Impacta el modelo de datos (`Obligacion`), la UI (`app/views/obligaciones.py`), y `AreaStrategy`/`AreaRegistry`.
2. ¿El despacho realmente litiga estos 6 tipos de indemnización (víctima incapacitado, cónyuge e hijo, padres, padres de hijo menor fallecido, pensionado de fondo privado, beneficio dejado de percibir), o solo un subconjunto? Construir las 6 variantes de reparto de beneficiario de una sola vez es un esfuerzo grande — conviene priorizar por uso real.
3. ¿Confirma el despacho que la tasa judicial a usar sigue siendo el mismo parámetro `CIVIL_ANNUAL_RATE` (6% EA, Art. 2232 C.C.) ya usado en Civil/Familia, o hay una tasa distinta para este dominio?
4. La tabla de mortalidad capturada en las plantillas (edades 15 en adelante, ver `X2.LUCRO-CESANTE-VICTIMA-INCAPACITADO.md` hoja `TablasMortalidad`) necesita transcribirse completa (no se leyó hasta el límite superior de edad) — ver pregunta nueva más abajo.

**Alcance explícitamente excluido de este sprint:** ninguna línea de código de cálculo — este sprint es solo la conversación de diseño (`superpowers:brainstorming`) y, si se aprueba, el esqueleto de arquitectura (modelo de datos, wiring de área/estrategia) sin las fórmulas de negocio, que quedan para Sprint 98/99/Sprint 100.

**Definición de Hecho:**
- Decisión documentada en `Preguntas-Para-Abogado-Respondidas.md` sobre área nueva vs. submodo de Civil/Familia, alcance real (qué variantes construir), y confirmación de tasa/tabla de mortalidad.
- Si se aprueba, esqueleto de `AreaStrategy`/modelo de datos creado y testeado, sin fórmulas de negocio todavía.
- Suite completa en verde.

---

## Sprint 98 — Motor actuarial de lucro cesante (fórmula Baremo judicial + tablas de mortalidad Resolución 1555/2010) 🔵 Bloqueado — pendiente de confirmación

**Prioridad sugerida:** Alta una vez resuelto Sprint 97 — es el núcleo matemático compartido por 6 de las 8 plantillas del dominio.

**Depende de:** Sprint 97 (decisión de arquitectura).

**Contexto:** X2 (`X2.LUCRO-CESANTE-VICTIMA-INCAPACITADO.md`, hoja `CalculosIndemnizacion`), X3 (`X3.LUCRO-CESANTE-CONYUGE-E-HIJO.md`), X4 (`X4.LUCRO-CESANTE-PADRES.md`), X5 (`X5.LUCRO-CESANTE-PADRES-HIJO-MENOR-FALLECIDO.md`), X8 (`X8.INDEMNIZACION-PERJUCIOS-OCASIONADOS-AL-PENSIONADO-FONDO-PRIVADO.md`) y X10 (`X10.LUCRO-CESANTE-X BENEFICIO DEJADO DE PERCIBIR.md`) comparten literalmente la misma metodología documentada en su hoja `CalculosIndemnizacion` (texto idéntico en las 6 plantillas, filas ~36-38 de X2/X8):

1. Indexar la renta histórica: `Ra = (IPC_Final / IPC_Inicial) × R`, más 25% de prestaciones sociales (cuando aplica ingreso laboral).
2. Periodo consolidado (debido): `S = Ra × [(1+i)ⁿ - 1] / i`, con `i` = interés judicial mensual (6% EA convertido a nominal mensual, 0,4867%, `TNA = [(1+TEA)^(1/12) - 1] × 12`) y `n` = meses desde el hecho dañoso hasta la fecha de tasación.
3. Periodo futuro (anticipado): `S = Ra × [(1+i)ⁿ - 1] / [i(1+i)ⁿ]`, con `n` = meses desde la tasación hasta el fin de la expectativa de vida de la víctima, tomada de la tabla de mortalidad de rentistas (Resolución 1555 de 2010 Superfinanciera, hoja `TablasMortalidad`: columnas Edad/Años esperados, separadas por sexo — vista hasta edad 38 en la lectura, la tabla completa no se transcribió).
4. Total = Indemnización consolidada + Indemnización futura.

Verificado con grep: **ninguna de estas piezas existe hoy** en `app/`. No hay conversión EA→mensual (solo EA→diaria en `app/engine/interest/rate_conversion.py`), no hay fórmula de anualidad/valor presente de renta en ningún módulo, y no hay tabla de mortalidad en ningún archivo de `app/` o `database/`.

Diferencias entre las 6 variantes (todas reutilizan el mismo núcleo de arriba, cambia solo el reparto):
- **X2** (víctima incapacitada): un solo beneficiario, aplica `% pérdida de capacidad laboral` sobre la renta actualizada.
- **X3** (cónyuge e hijos): si se reclama para ambos, reparto 50%/50%; si solo una parte, 100%; a la renta actualizada se le resta 25% por "sostenimiento de la víctima" antes de repartir.
- **X4** (padres, víctima adulta fallecida): reparto 50% padre/50% madre, cada uno con su propia expectativa de vida (tabla de mortalidad por sexo).
- **X5** (padres, hijo menor fallecido): en vez de expectativa de vida de la víctima, usa "años que le hacían falta a la víctima para cumplir 25" para fijar la fecha de liquidación; como el menor no tenía ingreso propio, usa la tabla SMMLV en vez de un salario indexado por IPC.
- **X8** (pensionado, fondo privado): la "renta" no es un salario sino la diferencia entre la mesada calculada para RPM y para RAI ("Diferencia entre mesadas... constituye la Renta sobre la cual se reclama la indemnización"), citando la Sentencia SL373-2021 CSJ Sala Laboral.
- **X10** (beneficio dejado de percibir): mismo núcleo, sin verificar en detalle el reparto específico — pendiente de lectura completa antes de codificar.

**Decisión de diseño a tomar con el usuario antes de codificar:** confirmar (a) que el despacho usa exactamente esta fórmula financiera y no otra variante jurisprudencial del lucro cesante; (b) qué variantes de beneficiario priorizar (¿construir las 6 de una vez o empezar por X2, la más simple, y extender?); (c) la tabla de mortalidad completa (ver pregunta nueva); (d) si el 25% de prestaciones sociales y el 25% de sostenimiento de la víctima son porcentajes fijos legales o parametrizables caso a caso.

**Definición de Hecho:**
- Módulo de conversión EA→mensual, con test que reproduce `0,4867%` a partir de `6%` EA.
- Módulo de anualidad (consolidada y futura) con test contra al menos un ejemplo numérico manual verificado independientemente (ninguna plantilla trae el ejemplo resuelto — todas las hojas leídas tenían las celdas de resultado en cero/vacías, así que el ejemplo de verificación no puede salir de las plantillas mismas).
- Tabla de mortalidad cargada y con lookup por sexo/edad, con test de al menos 3 edades contra la fuente oficial (Resolución 1555/2010 Superfinanciera).
- Al menos la variante X2 (víctima incapacitado) implementada y testeada end-to-end.
- Suite completa en verde.

---

## Sprint 99 — Daño emergente consolidado: ledger mensual de gastos indexados por concepto 🔵 Bloqueado — pendiente de confirmación

**Prioridad sugerida:** Media — más simple que Sprint 98 (no usa fórmula de anualidad ni mortalidad), pero depende de la misma decisión de arquitectura.

**Depende de:** Sprint 97.

**Contexto:** `X1.DAÑO-EMERGENTE.md`, hoja `PH` (la hoja `IPC` es solo la tabla de índices, no la lógica). Estructura real (filas 21-24 en adelante): una tabla mensual con columnas `DESDE | HASTA | IPC Inicial | IPC Final | CONCEPTOS DE GASTOS | CAPITAL MENSUAL | INDEXACIÓN | CAPITAL INDEXADO` — cada mes es una línea independiente con su propio gasto y su propia indexación individual (`IPC_mes` hasta la fecha de corte), no un solo capital consolidado como hoy trata `DANO_EMERGENTE` en el motor genérico. La plantilla trae filas prellenadas para ~22 años de meses, todas vacías (sin datos reales, es la plantilla en blanco — no hay ejemplo numérico que verificar).

Esto es estructuralmente distinto de la etiqueta `DANO_EMERGENTE` actual (`app/core/constants.py`), que trata todo como un único evento de capital en una fecha. Aquí cada "concepto de gasto" (ej. gastos médicos de enero, de febrero, etc.) es una entrada independiente con su propia fecha de causación y su propia indexación IPC desde esa fecha — en la práctica, esto **podría** lograrse hoy creando N obligaciones `PUNTUAL` (una por mes/gasto) con `aplica_indexacion_ipc=True`, sin necesidad de motor nuevo — solo falta confirmar si eso reproduce el resultado exacto de la plantilla, y si hace falta una UI dedicada (ledger mensual) en vez de obligar al abogado a crear N obligaciones sueltas.

**Decisión de diseño a tomar con el usuario antes de codificar:** (a) ¿la reconstrucción vía N obligaciones `PUNTUAL` independientes (ya soportado por el motor genérico) es aceptable, o el despacho necesita una UI de ledger mensual de un solo formulario, como en la plantilla? (b) ¿hace falta capturar el "concepto de gasto" como texto libre por línea (ej. "medicamentos", "transporte") para el reporte final, o basta con el monto?

**Definición de Hecho:**
- Confirmado y testeado que N obligaciones `DANO_EMERGENTE` PUNTUAL con indexación IPC, una por mes de gasto, producen el mismo total que sumar manualmente la fórmula de la plantilla (`VA = VH × IPC_Final/IPC_Inicial` por línea).
- Si el despacho pide UI de ledger dedicada: formulario nuevo que genera esas N obligaciones desde una sola pantalla.
- Suite completa en verde.

---

## Sprint 100 — Beneficio dejado de percibir como fruto civil 🔵 Bloqueado — pendiente de confirmación

**Prioridad sugerida:** Media/Baja — estructuralmente es el más parecido a mecánica ya existente en BASTIUM, pero sigue siendo una figura jurídica (frutos civiles) no modelada hoy.

**Depende de:** Sprint 97.

**Contexto:** `X6.LIQUIDACION-BENEFICIO-DEJADO-DE-PERCIBIR-COMO-FRUTO-CIVIL.md`, hoja `PH`. A diferencia de X1, esta plantilla parte de un `IBL:` y un `Porcentaje (%) Tasa de Reemplazo:` para fijar la `CUOTA Ó CAPITAL MENSUAL`, y luego repite la misma estructura de ledger mensual de X1 pero con una columna adicional `Incremento Anual` — es decir, la cuota mensual se reajusta una vez al año además de indexarse por IPC mes a mes.

Este patrón (cuota mensual + reajuste anual + indexación IPC mensual) es muy cercano a lo que **ya existe** para obligaciones `RECURRENTE` en Civil/Familia (Sprint 41/75: `generar_cuotas_mensuales`, `app/services/reajuste_anual.py`, con reajuste SMMLV/IPC/NINGUNO), y el cálculo de `IBL × Tasa de Reemplazo` ya existe para el módulo pensional (Sprint 17, `app/engine/labor/ibl.py`). Es decir: X6 probablemente necesita mucho menos motor nuevo que Sprint 98/99 — la pieza que falta es conectar "IBL × tasa de reemplazo" (hoy solo usado en Laboral/pensional) con la generación de una obligación `RECURRENTE` bajo la figura de "fruto civil" en el dominio nuevo, no un algoritmo distinto.

**Decisión de diseño a tomar con el usuario antes de codificar:** (a) confirmar que la mecánica de cuotas `RECURRENTE` + reajuste anual (Sprint 41/75) ya cubre este caso si se le agrega la fórmula `IBL × tasa de reemplazo` como origen de la cuota inicial; (b) confirmar la doctrina de "fruto civil" que sustenta esto (qué la distingue de una simple cuota alimentaria o pensional a efectos de reporte/etiquetado, si es que hay alguna diferencia legal más allá del nombre).

**Definición de Hecho:**
- Confirmado si el mecanismo `RECURRENTE` + reajuste anual existente reproduce la estructura de X6 sin motor nuevo, con test explícito.
- Si hace falta código nuevo: conectar `IBL × tasa de reemplazo` (ya existente para Laboral) como generador de la cuota inicial en este dominio.
- Suite completa en verde.

---

## Sprint 101 — Desindexación / deflactación de cantidad única (IPC inverso) 📋 Pendiente

**Prioridad sugerida:** Baja — pieza pequeña y aislada, no requiere la decisión de dominio nuevo de Sprint 97 (es una extensión del motor de indexación IPC ya existente en Civil/Familia, no una figura jurídica nueva).

**Depende de:** Nada nuevo — reutiliza `app/engine/indexation/ipc.py` (Sprint 8/20).

**Contexto:** `X7.INDEXACION-CANTIDAD-UNICA.md`, hoja `Hoja1`, filas 19-32: "LIQUIDADOR PARA DESINDEXAR CANTIDAD ÚNICA (DEFLACTACIÓN)", fórmula `VA = VH × (IPC_Inicial / IPC_Final)` — el inverso exacto de la indexación normal (`VA = VH × IPC_Final/IPC_Inicial`, fila 13, que **ya está cubierto** por el Sprint 20/Suma Única).

Verificado en el código: `IPCIndexation.calculate()` (`app/engine/indexation/ipc.py`, líneas 21-24) pone la deflación en cero deliberadamente ("Si hay deflación... la jurisprudencia dicta que no se castiga el capital histórico del acreedor"). Esa regla es correcta para su caso de uso (proteger al acreedor cuando el IPC baja durante la mora), pero es **distinta** al caso de uso de X7: aquí el usuario pide intencionalmente convertir una cifra a valor de una fecha **anterior** (deflactar hacia atrás), no protegerse de una deflación real durante la mora. No es un bug del código existente ni hay que tocarlo — es una calculadora nueva y aislada.

**Decisión de diseño a tomar con el usuario antes de codificar:** confirmar el caso de uso real (¿para qué se usa la deflactación en la práctica del despacho? ej. ¿retrotraer una condena a la fecha del hecho para aplicarle luego otra fórmula?), y si debe vivir como una utilidad de reporte suelta (no ligada a ninguna `Obligacion`/liquidación) o integrarse al flujo de captura de una obligación existente.

**Definición de Hecho:**
- Función `IPCIndexation.deflactar()` (o similar, nombre a decidir) con fórmula `VA = VH × IPC_Inicial/IPC_Final`, sin el guard de "deflación = 0" de la función existente (son casos de uso distintos, documentado explícitamente en el docstring de ambas para que no se confundan).
- Test con un ejemplo numérico verificado manualmente (la plantilla no trae ninguno resuelto).
- Suite completa en verde.

---

## Sprint 102 — Verificación: indexación de cantidad única con abonos secuenciales (Suma Única + abonos) 📋 Pendiente

**Prioridad sugerida:** Baja/exploratoria — probablemente ya funciona con el motor actual; este sprint es de verificación, no de motor nuevo.

**Depende de:** Sprint 20 (Suma Única, ✅ Completado), Sprint 75 (abonos e imputación en cascada, ✅ Completado). No depende de Sprint 97.

**Contexto:** `X9.INDEXACION-CON-ABONOS.md`, hoja `Hoja1`. El patrón (se repite por cada abono): indexar el capital inicial (`VA = VH × IPC_Final/IPC_Inicial`), restar el primer abono → `SALDO`, luego reindexar ese saldo desde la fecha del último movimiento hasta la fecha del siguiente abono, restar el siguiente abono, y así sucesivamente.

Esto es, en esencia, la misma secuencia que el motor genérico ya produce cuando una obligación tiene `interes_sobre_capital_indexado=True` (Suma Única) y recibe varios pagos parciales a través de `AllocationEngine`/`_estrategia_imputacion` (mismo mecanismo usado y testeado desde el Sprint 75 para cuotas de Civil/Familia). No parece requerir un algoritmo nuevo — pero **no se ha verificado explícitamente** contra este patrón concreto de "reindexar-el-saldo-tras-cada-abono", porque la plantilla `X9` en sí no trae ningún ejemplo numérico resuelto (todas las celdas de resultado están en cero/placeholder), así que no hay cifra de referencia para comparar hoy.

**Decisión de diseño a tomar con el usuario antes de codificar:** ninguna decisión de alcance nueva — pero sí se necesita un ejemplo numérico real para poder verificar (ver pregunta nueva más abajo). Si el despacho no puede aportar uno, se puede construir un caso sintético a mano y validarlo con el abogado antes de darlo por bueno.

**Definición de Hecho:**
- Test de integración en Civil/Familia: una obligación con Suma Única activa y 2-3 abonos en fechas distintas, verificado contra un cálculo manual paso a paso siguiendo exactamente la mecánica de X9.
- Si el test revela una discrepancia con el motor actual, documentar el gap y decidir si amerita un sprint de corrección aparte.
- Suite completa en verde.

---

## Notas de entorno (sin sprint asignado)

- ~~Validar/enable Windows "Long Paths" en la máquina de desarrollo~~ — **resuelto** (2026-07-15): se
  habilitó `LongPathsEnabled=1` en el registro de Windows para poder instalar PySide6 dentro de la ruta
  profunda de OneDrive, con confirmación previa del usuario.
- Confirmar si conviene excluir `.venv/` de la sincronización de OneDrive (hoy está en `.gitignore` pero
  OneDrive igual intenta sincronizar carpetas no versionadas dentro de la carpeta del proyecto).
- `requirements.txt` no fija versiones exactas (`sqlalchemy`, `PySide6`, etc. sin `==x.y.z`) — hoy
  `pip-audit -r requirements.txt` no reporta vulnerabilidades conocidas y la suite pasa completa, pero un
  build de CI futuro podría romperse sin aviso si una dependencia publica una versión nueva incompatible
  entre una corrida y otra (nadie decidiría deliberadamente el bump). No es un bug hoy — es una decisión de
  reproducibilidad sin tomar todavía; considerar `pip freeze`/`constraints.txt` si esto llega a morder en
  la práctica.
- El `.venv` local de esta máquina tiene instalados `fastapi`, `uvicorn`, `pandas`, `numpy`, `pymupdf`,
  `pypdf`, `alembic`, `pydantic` y otros paquetes que **ya no están** en `requirements.txt` desde que el
  Sprint 27 los identificó como no usados y los quitó — son residuo de antes de esa limpieza, nunca se
  desinstalaron del entorno local. No afecta a CI (que instala `requirements.txt` desde cero), pero vale
  la pena recrear el `.venv` local en algún momento para que coincida exactamente con lo declarado.
- El `.venv` local también tiene `markitdown[all]` y `pywin32` instalados desde 2026-08-19 (usados para
  convertir a Markdown las plantillas de referencia del despacho, ver Sprints 80-102) — tampoco están en
  `requirements.txt` porque no son dependencias de la app, solo herramienta puntual de conversión.
