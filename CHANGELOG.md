# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/), y este proyecto usa
[Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

Sprints 31-37: primer sistema de diseño visual de la GUI y mejoras de UX construidas sobre él
(navegación, pantalla de inicio, formularios, listados, feedback no bloqueante, jerarquía de botones,
persistencia de ventana y accesibilidad de teclado). Sprints 39-40: dos bugs reales corregidos (etiquetas
huérfanas en formularios, interés causado ausente en la tabla del PDF). Sprint 38: licencia Apache 2.0
publicada. Sprints 41/42/44/45: cuotas alimentarias con reajuste anual en Familia, prescripción/caducidad
conectada al flujo real de liquidación, varios gaps de UX/alcance en Laboral, y transparencia de unidad en
Sancionatorio. Sprint 46: saldo a favor de un sobrepago visible en PDF/Word/pantalla. Sprint 49: bug de
timing de visibilidad en los botones de navegación corregido (y superado estructuralmente por el sidebar
del Sprint 50). Sprint 50: modo oscuro/claro, sidebar de navegación y gráfica del Dashboard. Sprint 51:
migración automática de esquema y datos al arrancar la app, sin pasos manuales para una `bastium.db`
existente ni para un clon nuevo del repositorio. Sprint 48:
deuda de `ruff` limpiada (447 → 0 errores) y lint agregado al pipeline de CI. Sprints 52-54 (auditoría
técnica transversal, 2026-08-10): bug real corregido en la siembra de `parametros_legales` cuando se pasa
una ruta de base de datos explícita (Sprint 52), patrón N+1 de consultas eliminado en el Dashboard
(Sprint 53), y documentación desactualizada corregida en `docs/GUIA_USUARIO.md` y 2 specs de motores
(Sprint 54). Sprint 55 (reportado por el usuario): 3 bugs de UI en el Dashboard (gráfica con colores del
tema anterior, etiquetas superpuestas al redimensionar, tabla "Expedientes por área" editable sin razón).
Sprints 56-60 (brainstorming completo con el usuario, 2026-08-11): diálogos redimensionables/maximizables
(Sprint 56); columnas de Área y Unidad por fila en Parámetros, no editables tras crearse, con migración de
las 683 filas existentes (Sprint 57); vigencia "inteligente" para parámetros anuales de gobierno, IPC con
su variación % cruda visible junto al índice calculado, y enlace a "Ver historial" (Sprint 58); tooltips ⓘ
de ayuda extendidos a los 4 formularios principales de captura (Sprint 59); Obligaciones y Abonos ganan
"Eliminar"/"Editar" completo, mismo patrón que ya tenía Eventos Laborales (Sprint 60). Ningún cambio de
saldo final ya calculado en ningún sprint — solo el desglose de interés por fila del Sprint 40 y el
desglose por cuota del Sprint 41 cambian de forma, no de total.
Sprint 66: el botón "Parametros" del sidebar se renombra a "Configuraciones" y se convierte en una
pantalla con submenú lateral (Parámetros/Apariencia, con espacio para futuras secciones); el interruptor
de modo oscuro/claro se muda de Parámetros a la nueva sección Apariencia. Esa pantalla gana después una
tercera sección, Restablecer, para borrar expedientes y parámetros legales propios con backup automático
y confirmación escrita. Sprint 76 (prueba práctica del usuario en Civil/Familia, 2026-08-14): 4 bugs reales
corregidos (concepto "PAYMENT" ilegible en la cronología, subestimación de "Intereses Generados" en
expedientes con 2+ obligaciones, tabla de cronología del PDF/Word desbordando los márgenes de la página, y
el combo "Reajuste anual" sin precargar al editar una obligación) más el paso "Generar cuotas" documentado
en la guía de usuario; queda 1 pregunta abierta sobre la fórmula de tasa diaria del Art. 1617 (ver
`Preguntas-Para-Abogado-Abiertas.md`, Sprint 76). Sprint 75 (brainstorming completo con el usuario,
2026-08-14): las cuotas recurrentes reales del Sprint 41 (antes exclusivas de Civil/Familia) se extienden a
Comercial, con o sin reajuste anual activo; nueva imputación en cascada (capital de la cuota más reciente
primero) para pagos que cubren varias cuotas a la vez, con un diálogo nuevo de selección por rango en el
Detalle del expediente. Explícitamente fuera de alcance: Laboral, Sancionatorio, Honorarios y Tributario —
esas áreas rechazan obligaciones recurrentes a propósito (una multa/sanción/impuesto es un hecho único por
diseño) o son estructuralmente incompatibles (Laboral liquida un solo contrato por expediente, no una
serie de cuotas) — queda pendiente confirmar con el despacho si tiene sentido legal extenderlas antes de
construirlo. Sprint 61 (bloqueado desde el Sprint 57, desbloqueado con el usuario el 2026-08-14): 12
claves más de prescripción/caducidad (más `CIVIL_ANNUAL_RATE`) dejan de estar "sin wiring" — un campo
nuevo y opcional "Tipo de acción/proceso" en el formulario de obligación (filtrado por área) alimenta la
misma alerta de vencimiento que ya existía en el Dashboard, generalizada de "solo prescripción ejecutiva"
a los 13 tipos; la tasa civil legal se resuelve automáticamente cuando la tasa pactada se deja en 0. Sprint
43 (indexación IPC, respuesta del despacho recibida 2026-08-13): habilitada con su propia regla de
exclusión/coexistencia por área en Tributario (ligada al Art. 867-1 E.T.), Comercial (XOR con la tasa
comercial, solo con pacto expreso), Honorarios (compatible con el interés civil, fórmula exacta del
despacho), Laboral (excluyente con la indemnización moratoria, con alerta) y Sancionatorio (condicional, ya
cubierto por la excepción del despacho con el motor actual) — antes solo existía para Civil/Familia. Sprint
47 (recálculo histórico, respuesta del despacho recibida 2026-08-13): script de identificación/marcado de
liquidaciones afectadas por el Sprint 30, generación de los 2 memoriales del protocolo (actualización/
corrección y error aritmético Art. 151 CPACA) y log de diferencias numérico; confirmado que el módulo de
densidad pensional (`calcular_densidad_semanas`) ya usaba días calendario reales desde el Sprint 17 y no
requería el ajuste de la Sentencia SL138-2024 que el despacho pidió verificar. Sprint 24 (validación de
datos): confirmado que ya estaba implementado desde una integración anterior (Sprints 34/56-60) — solo se
corrigió el estado en `Pendientes.md`, sin cambios de código. Sprint 72 (rediseño de "Agregar Obligación"):
layout de 2 columnas con `QScrollArea` para que el botón Guardar siempre sea visible en 1366×768 sin
importar el área elegida. Sprint 73 (obligaciones recurrentes con fechas personalizadas): nuevo tipo de
recurrencia por lista de fechas fijas anuales (ej. gastos de vestuario en junio/diciembre/cumpleaños),
alternativo a la cadencia mensual del Sprint 41. Sprint 18 (ultraactividad CPC→CGP, 2026-08-14): campo
opcional `fecha_providencia_costas` en Obligación — si la providencia que impone costas es anterior al 1°
de enero de 2016 (Art. 627 CGP), el sistema no aproxima con la tabla granular vigente (no existe fuente
confiable pre-CGP) y lanza un error explícito en vez de inventar una cifra; retrocompatible si el campo
queda vacío. Sprint 71 (checkbox de indexación IPC invisible, seguimiento del Sprint 67, 2026-08-14): el
`QGroupBox` marcable que contiene ese checkbox tampoco tenía estilo de indicador — reglas
`QGroupBox::indicator` agregadas a los 2 temas, mismo patrón que el `QCheckBox::indicator` del Sprint 67.
Sprint 62 (2026-08-14): 37 referencias rotas al archivo `Preguntas-Para-Abogado.md` (renombrado hace
tiempo) corregidas en comentarios/docstrings de 20 archivos `.py`. Sprint 13 (2026-08-14): la sección de
Parámetros en `docs/GUIA_USUARIO.md` gana un tono pedagógico dirigido a un perfil "Abogado Junior/Estudiante
de Consultorio Jurídico", con ejemplos de cómo traducir un hecho del caso a una fila de la tabla.
Sprint 77 (rutina autónoma, 2026-08-20): las alertas no bloqueantes de liquidación (`LiquidationResult.
alertas`, Sprint 43) llegan ahora también a las exportaciones PDF/Word, no solo a pantalla — quedaba
pendiente desde el code review del propio Sprint 43. Sprint 80 (2026-08-20/23): serie mensual real de IPC
(2003-2026) cargada desde una fuente DANE certificada, con `CivilFamiliaStrategy` usando interpolación
mensual en vez de anual dentro de ese rango (desbloquea el Sprint 8), y estimación por media geométrica para
fechas posteriores al último mes certificado. Sprint 81 (2026-08-20): serie de tasas IBC/Usura
(Superfinanciera) extendida hacia atrás hasta 1971-10-29, con la columna "Bancario Corriente" mapeada por
continuidad conceptual con el Art. 884 C.Co. para el tramo pre-1997. Sprint 83 (2026-08-20): función aislada
`EffectiveRateConverter.annual_to_monthly` que documenta la convención "mensual con prorrateo de 30 días" que
usa la mayoría de plantillas del despacho (i1/i2/i7/i9/i13) — no conectada a ningún cálculo real, condicionada
a la respuesta del despacho sobre la pregunta ampliada del Sprint 76. Sprint 78 (2026-08-23): confirmado con
el despacho que el conteo de días de `calcular_densidad_semanas` (módulo pensional) debe ser inclusivo (+1),
igual que el resto de reglas del Sprint 3; corregido en `app/engine/labor/ibl.py`. Sprint 90 (2026-08-23): el
despacho rechazó el mecanismo de las plantillas P15/P16 (factor fijo 4.33) para el IBL del régimen ISS
pre-Ley 100 — confirmó que ya está cubierto por la función existente del Sprint 70/91, cerrado sin cambios de
código. Sprint 92 (2026-08-20): indemnización por despido injustificado (Art. 64 CST) en Laboral —
`DismissalIndemnityCalculator` (`app/engine/labor/dismissal_indemnity.py`) cubre contrato indefinido (30+20
días o 45+15 según la fecha de la Ley 50/1990) y término fijo/obra-labor, con el caso ≥10 SMMLV explícitamente
no soportado. Sprint 93 (2026-08-20/23): nueva categoría `SALARIOS_DEJADOS_DE_PERCIBIR` en Laboral reconstruye
salario y prestaciones año por año para períodos sin contrato vigente (reintegros, salarios caídos), con
reajuste IPC o SMMLV según una regla confirmada por el despacho (SMMLV solo si el salario base coincide
exactamente con el SMLMV del año de causación). Sprint 101 (2026-08-20): calculadora aislada de deflactación
IPC (`IPCIndexation.deflactar`, fórmula inversa de la indexación) — sin conectar a ningún flujo real, a la
espera del caso de uso concreto del despacho. Sprint 102 (2026-08-20): verificación confirmó que el motor de
Suma Única con abonos secuenciales NO reproduce el patrón esperado por las plantillas del despacho (diferencia
de $29.084,08 en el caso sintético probado) — bug de dominio documentado y diferido al Sprint 104 (parcial),
sin cambios en `app/` en este sprint. Sprint 103 (2026-08-20): corregido un test
(`test_pago_por_rango_dialog_con_remanente_no_confirma_ni_crea_abonos`) que colgaba la suite completa
indefinidamente por no mockear un `QMessageBox.warning` modal, mismo patrón ya usado en el resto del proyecto.
Sprint 108 (reportado por el despacho, cerrado 2026-08-26): 3 mismatches de identidad visual en las tablas de
cronología del PDF/Word — bordes en negro (antes borgoña), fila de TOTALES en borgoña (antes negro), y
encabezado con la fuente `AncizarSans-ExtraBold` en ambos formatos. Sprint 109 (2026-08-26): estándar de color
para futuras gráficas de línea/curva (ejes y texto negro puro, curva principal borgoña con degradado, curva
secundaria negra) documentado en `docs/DISENO_UI_UX.md` — ninguna gráfica de curva existe todavía en el
proyecto. Sprint 111 (auditoría 2026-08-25, cerrado 2026-08-26): 3 regresiones del criterio de validación del
Sprint 24 en formularios agregados después de su cierre — Tributario sin validar signo/rango de sus campos
numéricos, `fecha_fin_pactada` de un contrato a término fijo solo validada al liquidar (no al guardar), y
`DescuentoLaboralFormDialog` sin la advertencia de sobrepago que sí tiene `AbonoFormDialog`; más una
inconsistencia de título de diálogo homologada. Sprint 112 (auditoría 2026-08-25, cerrado 2026-08-26): 4
hallazgos de concurrencia/rendimiento — "Restablecer datos de fábrica" y "Generar cuotas" ahora corren en hilo
de fondo con `QProgressDialog` (antes congelaban la UI sin aviso), el preview de "Pago por rango" deja de
abrir una sesión SQL nueva por cada cuota al teclear, y 3 columnas nuevas de `audit_logs` (Sprint 47) ganan
índice para evitar un full table scan en cada corrida del script de recálculo histórico.

### Added
- Laboral: indemnización por despido injustificado, Art. 64 CST (Sprint 92): `DismissalIndemnityCalculator`
  (`app/engine/labor/dismissal_indemnity.py`) calcula contrato indefinido con salario <10 SMMLV (30 días
  primer año + 20 días/año subsiguiente si el contrato inició después del 1° de enero de 1991 — Ley 50/1990
  — o 45+15 días si es anterior) y contrato a término fijo/obra-labor (tiempo restante del plazo pactado,
  piso de 15 días); wireado en `LaboralStrategy` como el evento `INDEMNIZACION_DESPIDO`, independiente de
  `SANCION_MORATORIA` (Art. 65 CST). El caso de contrato indefinido con salario ≥10 SMMLV queda
  explícitamente sin soportar (`RegimenNoSoportadoError`, alerta no bloqueante).
- Laboral: salarios y prestaciones dejadas de percibir, con reajuste anual (Sprint 93): nueva categoría
  `SALARIOS_DEJADOS_DE_PERCIBIR` (coexiste con `LIQUIDACION_CONTRATO_LABORAL` sin romper el invariante "1
  obligación = 1 contrato" del Sprint 3) reconstruye en `app/services/salarios_dejados_de_percibir.py` un
  bloque anual de salario reajustado (IPC o SMMLV, vía `reajustar_capital_anual`, Sprint 41/75) y las 4
  prestaciones (cesantías, intereses a las cesantías, primas, vacaciones) con los mismos divisores 360/720
  de `LaborScheduler`, para períodos sin contrato vigente (reintegros, salarios caídos). La elección del
  índice no es discrecional: `determinar_tipo_reajuste_salarios_dejados_de_percibir` exige SMMLV solo cuando
  el salario base coincide exactamente con el SMLMV del año de causación, IPC en cualquier otro caso —
  validado al guardar.
- Serie mensual real de IPC 2003-2026 (Sprint 80): `_IPC_MENSUAL` poblada con 279 pares año/mes desde una
  fuente DANE certificada (base diciembre-2018=100), desbloqueando el Sprint 8 — `CivilFamiliaStrategy.
  _evento_indexacion` usa `get_ipc_interpolado_mensual_for_date` (interpolación lineal por día) dentro del
  rango cubierto, con estimación por media geométrica para fechas posteriores al último mes certificado y
  fallback a interpolación anual documentado para fechas anteriores a 2003.
- Serie de tasas IBC/Usura extendida hasta 1971 (Sprint 81): ~90 tramos nuevos en `_TRAMOS_IBC_USURA` desde
  1971-10-29 (antes empezaba en 1997-07-01), con la columna "Bancario Corriente" de la fuente pre-1997
  mapeada como `ibc_anual` por continuidad conceptual con el Art. 884 C.Co.
- `EffectiveRateConverter.annual_to_monthly` (Sprint 83): fórmula `[(1+EA)^(1/12)-1]×12` que replica la
  convención "tasa mensual con prorrateo de 30 días" que usan la mayoría de las plantillas del despacho
  (i1/i2/i7/i9/i13) — documentada y probada, pero deliberadamente no conectada a ningún área todavía; cuál
  de las 3 convenciones de conversión de tasa aplica en cada caso sigue condicionado a la respuesta del
  despacho a la pregunta ampliada del Sprint 76.
- `IPCIndexation.deflactar()` (Sprint 101): calculadora aislada de deflactación de cantidad única (`VA = VH
  × IPC_Inicial/IPC_Final`, el inverso exacto de la indexación normal), sin el guard de "deflación = 0" de
  `calculate()` — no conectada a ningún flujo de captura o liquidación real todavía.
- Alertas de liquidación en las exportaciones PDF/Word (Sprint 77): `JudicialPDFGenerator.generate()` y
  `WordReportGenerator.generate()` aceptan un parámetro `alertas: list[str] | None` y agregan una sección
  "Advertencias" (⚠, mismo naranja que ya usa la pantalla de resultado) cuando `LiquidationResult.alertas`
  (Sprint 43) no está vacío — antes solo se veían en pantalla, nunca en el documento exportado.
- Wiring de 18 parámetros de prescripción/caducidad/tasa sin conectar (Sprint 61): columna nueva
  `tipo_accion_proceso` en `Obligacion` (opcional, nulo por defecto), con un combo en el formulario de
  obligación filtrado por área (`opciones_tipo_accion_proceso_por_area`, reutiliza el mapeo de área del
  Sprint 57) que unifica los 6 tipos de prescripción y las 7 claves de caducidad conocidas en un solo
  catálogo. La alerta de vencimiento del Dashboard, antes hardcodeada a la prescripción ejecutiva, ahora
  resuelve el plazo aplicable de cada obligación según ese campo (o ejecutiva por defecto si se deja en
  blanco, sin cambio de comportamiento). `CivilFamiliaStrategy` cae automáticamente a la tasa legal civil
  (`CIVIL_ANNUAL_RATE`) cuando la tasa pactada de una obligación se deja en `0`, sin campo nuevo en la UI.
- Cuotas recurrentes en Comercial y pago por rango con imputación en cascada (Sprint 75): `generar_cuotas_mensuales`
  ya no exige reajuste anual activo (SMMLV/IPC) — una obligación recurrente sin reajuste también genera
  cuotas mensuales reales, con capital constante. `ComercialStrategy` detecta cuotas-hija ya generadas
  igual que `CivilFamiliaStrategy`, evitando el doble conteo de capital. Nuevo botón "Pagar cuotas
  seleccionadas" en el Detalle del expediente (Civil/Familia y Comercial): selecciona un rango de cuotas
  consecutivas en la tabla, ingresa un monto total, y el pago se reparte automáticamente en cascada —
  capital de la cuota más reciente primero, luego capital e interés de las anteriores, dejando los
  intereses no cubiertos de la cuota más antigua "congelados" (no siguen generando interés nuevo sobre el
  capital ya pagado). El orden de imputación es ahora intercambiable en el motor de liquidación
  (`AllocationEngine`/`LiquidationCore`), activándose la estrategia capital-primero automáticamente para
  cualquier cuota-hija sin afectar el orden legal general (indexación→interés→capital) del resto de
  obligaciones. Fuera de alcance de este sprint: Laboral, Sancionatorio, Honorarios y Tributario.
- Ultraactividad CPC→CGP en costas judiciales (Sprint 18): campo opcional `fecha_providencia_costas` en
  Obligación; si la providencia es anterior al 1° de enero de 2016 (Art. 627 CGP), lanza
  `TarifaPreCGPNoDisponibleError` en vez de aplicar la tabla granular vigente (no existe tabla pre-CGP
  confiable) — sin campo de captura en la GUI todavía, ver `Pendientes.md`.
- Sección "Restablecer" en Configuraciones: borra todos los expedientes y los parámetros legales
  creados por el usuario (deja los de sistema intactos), con backup automático previo y confirmación
  escrita.
- Área(s) del derecho y unidad de medida por valor de parámetro legal (Sprint 57): nuevas columnas
  `areas_derecho`/`unidad` en `parametros_legales`, capturables al agregar un valor nuevo desde
  Parámetros y no editables después — migración aplica la clasificación a las 683 filas existentes.
- Presentación inteligente en Parámetros (Sprint 58): "Vigente hasta" calculado automáticamente para
  parámetros que el gobierno fija año a año (SMLMV, IPC, UVT) en vez de mostrarse vacío; variación % anual
  cruda del IPC visible junto al índice ya calculado, con la fórmula explicada; enlace para ver el
  historial completo de cualquier parámetro con más de un valor.
- Tooltips ⓘ de ayuda en los 4 formularios principales de captura — Obligación, Expediente, Abono y
  Parámetro (Sprint 59): antes solo 1 de ~15 campos de `ObligacionFormDialog` tenía el ícono visible.
- Editar y eliminar Obligaciones y Abonos (Sprint 60): mismo patrón ya usado en Eventos Laborales;
  eliminar una obligación con cuotas generadas por reajuste anual (Sprint 41) las elimina también.
- Diálogos redimensionables y maximizables (Sprint 56): los 7 `QDialog` del proyecto ganan botones de
  minimizar/maximizar, antes solo tenían cerrar.
- Modo oscuro/claro, sidebar de navegación y gráfica del Dashboard (Sprint 50): tema oscuro completo
  (`app/core/theme_colors_dark.py`, `resources/theme_dark.qss`) alternable en caliente desde Parámetros y
  persistido vía `QSettings`; `QToolBar` superior reemplazado por un sidebar lateral (mismos nombres de
  atributo, sin romper tests); gráfica de expedientes por área (`matplotlib`/`FigureCanvasQTAgg`) junto a
  la tabla existente en el Dashboard.
- Saldo a favor de un sobrepago visible en reportes (Sprint 46): el resumen ejecutivo, la tabla de
  detalle del PDF/Word y la pantalla de resultado muestran el saldo a favor calculado desde el Sprint 23,
  antes invisible para el usuario final.
- Familia: cuotas alimentarias con reajuste anual (Sprint 41): una obligación RECURRENTE de Civil/Familia
  puede marcarse con reajuste `SMMLV` o `IPC`; el sistema genera y persiste las cuotas mensuales reales
  (`app/services/reajuste_anual.py`), con capital constante dentro del año y reajustado cada 1° de enero,
  concepto dinámico por mes/año, y abonos capturables por cuota individual.
- Prescripción/caducidad conectada al flujo real de liquidación (Sprint 42): cualquier obligación cuyo
  plazo ya venció se marca (no se excluye) con advertencia visual en pantalla, PDF y Word.
- Laboral (Sprint 44): checkbox "salario = SMMLV" resuelve el valor automáticamente por año; edición de
  obligaciones y eventos laborales ya guardados sin borrar y recrear; nueva entidad `DescuentoLaboral`
  para descuentos del empleador; fecha de corte editable por liquidación puntual.
- Sancionatorio (Sprint 45): indicador dinámico que muestra si un valor se aplicará como SMLMV o UVT según
  la fecha de origen capturada.
- Notificación no bloqueante tipo toast (Sprint 36): `app/views/toast.py::mostrar_toast()` sustituye la
  única confirmación de éxito de bajo riesgo que usaba `QMessageBox` modal (exportación completa);
  `QMessageBox` se mantiene para errores y confirmaciones destructivas. Nueva clase QSS `secondary`
  junto a `primary`/`destructive` (Sprint 31), aplicada explícitamente a todos los botones de las 9
  vistas con botones.
- Persistencia de ventana y accesibilidad de teclado (Sprint 37): `MainWindow` recuerda
  tamaño/posición/maximizado entre sesiones vía `QSettings`; orden de tabulación explícito en
  `ObligacionFormDialog` y `ExpedienteFormDialog`; confirmado `Enter`=Guardar y `Esc`=Cancelar en los 5
  diálogos de formulario del proyecto.
- Licencia Apache License 2.0 (Sprint 38): archivo `LICENSE` en la raíz, badge de `README.md` y línea de
  `CONTRIBUTING.md` actualizados.
- Sistema de diseño visual centralizado (Sprint 31): paleta de marca burdeos/crema
  (`app/core/theme_colors.py`), stylesheet `resources/theme.qss` y `QPalette` aplicados una sola vez
  vía `app/core/apariencia.py::aplicar_tema()`, tipografía `AncizarSans` cargada como fuente por
  defecto, y un set de 9 íconos SVG hechos a mano (`resources/icons/`) reemplazando los emoji sueltos
  de navegación, cargados vía `app/views/icons.py`.
- Dashboard de inicio (Sprint 33): `DashboardView` (`app/views/dashboard.py`, antes vacío) con conteo
  de expedientes por área, alertas de plazos próximos a vencer y actividad reciente; registrado como
  pantalla inicial de la aplicación en vez del listado plano de expedientes.
- Navegación mejorada (Sprint 32): breadcrumb contextual, atajos de teclado
  (`Alt+Izquierda`/`Backspace`/`Ctrl+Home` para navegar, `Ctrl+S`/`Esc` en los 5 diálogos de
  formulario), y estado visual activo/inactivo del botón "Parámetros".
- Búsqueda, filtros y estados vacíos (Sprint 35): campo de búsqueda y filtro por área en
  `ExpedientesListView`, ordenamiento de columnas, y un estado vacío explícito con acción contextual
  cuando la tabla no tiene filas.
- UX de formularios (Sprint 34): `ObligacionFormDialog` reorganizado en secciones colapsables con
  tooltips legales y feedback de validación en tiempo real (reutilizando las reglas del Sprint 24);
  tooltips y validación en tiempo real del radicado en `ExpedienteFormDialog`.
- Migración automática de esquema y datos al arrancar la app (Sprint 51):
  `database/database.py::aplicar_migraciones_pendientes()`, llamada desde `main.py` en cada arranque,
  compone los 9 scripts de `scripts/migrate_*.py` acumulados sprint a sprint — agrega cualquier
  columna/índice que una `bastium.db` existente todavía no tenga y siembra `parametros_legales` si está
  vacía. Ya no hace falta ningún paso manual de migración, ni para una base existente de un sprint
  anterior ni para un clon nuevo del repositorio.
- Editar y eliminar valores de parámetro creados por un usuario (los del sistema quedan protegidos),
  desde el historial de cada clave en Configuraciones → Parámetros.
- Campo "Unidad" como desplegable (con opción "Otros...") al agregar un valor de parámetro.
- Tooltips ⓘ en todos los campos del formulario de parámetros y en las columnas de la tabla.
- Indexación IPC en Comercial, Laboral, Honorarios, Sancionatorio y Tributario (Sprint 43), cada una con su
  propia regla de exclusión/coexistencia en vez de un solo flag genérico: XOR real en Comercial (nuevo campo
  `pacto_expreso_indexacion`, capital indexado + interés civil 6% puro en vez de la tasa comercial); fórmula
  exacta del despacho en Honorarios (`Capital × IPC_Final/IPC_Inicial + Interés_Civil_6%(Capital_Actualizado)`);
  excluyente con la indemnización moratoria en Laboral, con alerta no bloqueante "Doble Actualización
  Prohibida" si coinciden; nuevo campo `protegida_inflacion_uvr` en Tributario (prohibición de doble cobro
  sobre el Art. 867-1 E.T.) y alerta "Techo de usura alcanzado" cuando el tope combinado recorta la
  indexación. Nuevo `LiquidationResult.alertas` (feedback no bloqueante, mostrado con el mismo `toast` del
  Sprint 36, y con un banner persistente en la pantalla de resultado) para las alertas que no bloquean la
  liquidación.
- Recálculo de liquidaciones históricas afectadas por las correcciones del Sprint 30 (Sprint 47):
  identificación/marcado vía `AuditLog` (flag "OBSOLETO - REQUIERE RECÁLCULO"), recálculo sin sobrescribir
  el registro original (liquidación nueva vinculada a la anterior), log de diferencias numérico
  ("Diferencia recuperada: +X días / +$Z pesos"), generación de los 2 tipos de memorial del protocolo del
  despacho (Actualización/Corrección y corrección de error aritmético Art. 151 CPACA), y priorización por
  cercanía de prescripción. Nunca recalcula un expediente en cosa juzgada.
- Familia: obligaciones recurrentes con fechas anuales fijas en vez de mensuales (Sprint 73) — para gastos
  que no se repiten mes a mes (ej. vestuario en junio/diciembre/cumpleaños), un nuevo tipo de recurrencia
  genera exactamente las ocurrencias configuradas por año, reutilizando el mismo mecanismo de cuotas
  hijas/abonos del Sprint 41.

### Fixed
- 4 hallazgos de concurrencia y rendimiento (Sprint 112): "Restablecer datos de fábrica" (`app/views/
  restablecer.py`) congelaba la UI sin ningún indicio visual durante el backup y el borrado en cascada —
  ahora corre en `QThreadPool` con `QProgressDialog`, mismo patrón del Sprint 26. "Generar cuotas"
  (`ExpedienteDetallePage`) abría una sesión SQLAlchemy nueva por cada transición de año en una obligación
  recurrente larga — ahora corre bajo `cache_de_liquidacion()` con `precargar_parametro`, además de moverse
  a `TareaEnHilo`. El preview de "Pago por rango" (`pago_por_rango.py::_calcular_preview`) reconstruía el
  `rate_provider` y reliquidaba completo por cada tecla sin cache — corregido, con un test que confirma que
  el número de sesiones ya no crece con el tamaño del rango. Las columnas `audit_logs.fecha_ejecucion`/
  `obsoleto_requiere_recalculo`/`liquidacion_anterior_id` (Sprint 47) ganan índice
  (`scripts/migrate_add_indices_recalculo_historico.py`) para evitar un full table scan en cada corrida del
  script de recálculo histórico.
- 3 regresiones del criterio de validación del Sprint 24 en formularios agregados después de su cierre
  (Sprint 111): `_guardar_tributario` no validaba signo/rango de `valor`, `base_sancion` ni los 5 campos de
  renta líquida gravable (ahora exigen `>0`/`>=0` según el campo); `fecha_fin_pactada` de un contrato a
  término fijo/obra-labor (Sprint 92) solo se validaba al liquidar, nunca al guardar (ahora se compara
  contra `fecha_fin` al guardar); y `DescuentoLaboralFormDialog` no tenía la advertencia de "posible
  sobrepago" que ya tiene `AbonoFormDialog` pese a seguir el mismo patrón — agregada. También homologado el
  título `"Datos invalidos"` en `expedientes.py`, que decía `"Datos incompletos"`.
- 3 mismatches de identidad visual en las tablas de cronología del PDF y del Word (Sprint 108, reportado por
  el despacho): el borde/grid de las 5 tablas de `app/reports/pdf.py` estaba en borgoña (debía ser negro),
  la fila de TOTALES en negro (debía ser borgoña de marca) y el encabezado sin la fuente
  `AncizarSans-ExtraBold` (registrada ahora con `pdfmetrics.registerFont`). `app/reports/word.py` no tenía
  ningún color/relleno propio en sus tablas (ni fondo negro/texto crema en encabezados, ni borgoña en
  totales) — corregido con sombreado de celda vía XML (`_sombrear_celda`) y runs con color/negrita/fuente
  explícitos (`_escribir_celda`). De paso se corrigió un bug de `_escribir_celda` que dejaba el texto con
  estilo como el segundo run de la celda (invisible para cualquier lector que solo mirara `runs[0]`) por
  llamar `celda.text = ""` antes de `add_run()`.
- Test que colgaba la suite completa indefinidamente (Sprint 103):
  `test_pago_por_rango_dialog_con_remanente_no_confirma_ni_crea_abonos` llamaba a
  `PagoPorRangoDialog.confirmar()` sin mockear el `QMessageBox.warning` modal que se dispara con remanente
  sin cubrir — `pytest` sin filtros nunca terminaba. Corregido agregando el mismo `monkeypatch` que ya usa
  el resto del proyecto para ese patrón; sin cambios en `app/`.
- El conteo de días de `calcular_densidad_semanas` (densidad pensional, IBL) no era inclusivo (Sprint 78):
  usaba `(fin - inicio).days` en vez de `+1`, a diferencia de la regla general confirmada por el despacho
  desde el Sprint 3. Corregido en `app/engine/labor/ibl.py`; el caso de prueba judicial ya citado (348 días)
  sigue dando 50 semanas con el +1 (coincidencia de redondeo, no una excepción real).
- El checkbox "Aplica indexación IPC" seguía invisible en Civil/Familia tras el fix del Sprint 67 (Sprint
  71): el checkbox en sí ya estaba bien estilado, pero el `QGroupBox` marcable que lo contiene
  (`grupo_tasas_intereses`) usa un subcontrol distinto (`QGroupBox::indicator`), no cubierto por esas
  reglas — agregadas para los 3 `QGroupBox` marcables del proyecto, en ambos temas.
- El diálogo "Agregar obligación" era tan grande que el botón "Guardar" no aparecía a simple vista, y sus 3
  secciones quedaban apiladas en una sola columna sin importar el tamaño de la ventana (Sprint 72).
  Reorganizado en un `QGridLayout` de 2 columnas ("Tasas e intereses" a la derecha de "Datos básicos")
  envuelto en un `QScrollArea`, con tamaño inicial fijo (1300×650) que deja el botón "Guardar" siempre
  visible en una pantalla estándar (1366×768) en las 6 áreas del derecho.
- El combo "Reajuste anual" de una obligación Recurrente Civil/Familia no se precargaba al editar (Sprint
  76): siempre mostraba "Ninguno" sin importar el valor real guardado, y volver a dar clic en "Guardar" sin
  tocar ese campo revertía silenciosamente `tipo_reajuste_anual` a `NINGUNO` en la base de datos (el
  guardado original sí funcionaba bien — el problema era solo la precarga al editar). Corregido en
  `app/views/obligaciones.py::_precargar_desde_obligacion`, con 2 tests de regresión nuevos.
- La tabla de cronología del PDF y del Word se salía de los márgenes de la página (Sprint 76): con 10-11
  columnas y sin ancho fijo, reportlab (PDF, sin `colWidths`) y `Table Grid` en modo autofit-to-contents
  (Word) ensanchaban cada columna al ancho de su texto sin wrap, ignorando el margen impreso. Corregido con
  orientación horizontal, anchos de columna proporcionales explícitos en ambos formatos, y "Concepto" con
  word-wrap en el PDF.
- "Intereses Generados" en el resumen ejecutivo del PDF/Word/pantalla quedaba por debajo del interés real
  en cualquier expediente con 2 o más obligaciones (Sprint 76): la fila de cierre consolidada que fusiona
  varias obligaciones aisladas fijaba su interés en `$0.00` en vez de sumar el interés de cierre real de
  cada una. El "Saldo Final de Intereses" y el "Gran Total Adeudado" siempre fueron correctos — solo el
  subtotal informativo estaba mal. Corregido en `app/services/area_strategy.py::_fusionar_resultados`.
- La fila de un abono mostraba el texto literal "PAYMENT" como concepto en la cronología liquidada, en vez
  de un texto legible (Sprint 76) — el evento de pago nunca llevaba un `label` en su payload. Corregido en
  `app/services/motor_universal.py`: ahora muestra "Abono — {referencia}" (o solo "Abono" sin referencia).
- `aplicar_migraciones_pendientes()` fallaba con `sqlite3.OperationalError: no such column:
  parametros_legales.areas_derecho` en cualquier `bastium.db` real sembrada antes del Sprint 57: como
  `migrar_parametros_legales()` corría antes que `migrar_parametros_area_unidad()` (quien agrega esas
  columnas), y el modelo ORM ya las declaraba como mapeadas, la primera consulta a `ParametroLegal` las
  seleccionaba sin importar que la migración que las crea todavía no hubiera corrido. Corregido llamando
  `migrar_parametros_area_unidad()` también antes de `migrar_parametros_legales()` (además de la llamada ya
  existente después, necesaria para completar filas recién sembradas) — es idempotente, llamarla dos veces
  es gratis.
- Eliminar una Obligación no refrescaba las tablas de Abonos/Eventos Laborales en pantalla:
  `_eliminar_obligacion` ya borraba en cascada sus abonos/eventos/descuentos laborales en la base de
  datos, pero solo refrescaba `tabla_obligaciones` — las otras 3 tablas quedaban mostrando filas fantasma
  con botones Editar/Eliminar conectados a ids ya inexistentes; un clic ahí disparaba `session.delete(None)` y
  `sqlalchemy.orm.exc.UnmappedInstanceError`. Corregido refrescando las 4 tablas relacionadas tras eliminar,
  y agregando verificación defensiva (aviso amigable en vez de traceback) en los 5 métodos de
  editar/eliminar de `expediente_detalle.py`.
- Al editar un abono, la detección de sobrepago contaba doble su propio valor anterior (Sprint 60):
  sumaba el monto viejo y el nuevo del mismo abono, disparando una advertencia de sobrepago falsa en
  casos donde el total real seguía dentro del valor de la obligación.
- 3 bugs de UI en el Dashboard (Sprint 55): la gráfica de expedientes por área se quedaba con los colores
  del tema anterior al volver a la pantalla con el botón "Volver" (solo "Inicio" la refrescaba); las
  etiquetas de la gráfica se superponían al redimensionar la ventana (el layout no se recalculaba); y las
  3 tablas del Dashboard eran editables con doble clic sin persistir el cambio.
- `aplicar_migraciones_pendientes(db_path)` ignoraba `db_path` al sembrar `parametros_legales` (Sprint 52):
  el script de siembra usaba siempre el engine global en vez de la ruta recibida — inofensivo en producción
  (donde siempre apunta a la misma `bastium.db`), pero hacía que la suite de tests tocara la base real como
  efecto secundario, y era una trampa para cualquier uso futuro de `db_path` con una base distinta.
- Patrón N+1 de consultas en el Dashboard (Sprint 53): calcular las alertas de plazos próximos a vencer
  abría una sesión SQLAlchemy nueva por cada obligación no pagada (una por cada `fecha_origen` distinta);
  armar la actividad reciente consultaba una vez por expediente. Corregido con una precarga de parámetros
  en memoria (`app/services/parametro_service.py::precargar_parametro()`) y una consulta `IN` batched
  (`app/engine/audit/service.py::historial_de_expedientes()`).
- `sqlite3.OperationalError: no such column: obligaciones.costas_tipo_proceso` al abrir la app con una
  `bastium.db` creada antes de los Sprints 18-20 (Sprint 51) — causa raíz: 3 scripts de migración de
  esquema nunca se habían corrido, y además la tabla `parametros_legales` estaba completamente vacía
  (el motor de cálculo entero dependía de ella). Ambos huecos se cierran automáticamente ahora.
- Etiquetas huérfanas en `QFormLayout` (Sprint 39): campos condicionales de `ObligacionFormDialog`,
  `EventoLaboralFormDialog` y `ParametroFormDialog` dejaban su etiqueta de texto visible sin el campo
  editable al ocultarse (`widget.setVisible(False)` no sincroniza el `QLabel` que genera
  `addRow(str, widget)`). Corregido de forma centralizada con
  `app/views/form_utils.py::set_row_visible()`.
- La tabla de detalle del PDF/Word mostraba $0 de interés causado en todas las filas de las 6 áreas,
  aunque el saldo final de intereses ya era correcto (Sprint 40) — `LiquidationCore` nunca atribuía el
  interés causado por paso del tiempo a la fila de su evento. No afecta ningún saldo final ya calculado
  ni liquidaciones archivadas, solo el desglose de detalle por período.
- Los botones "Volver"/"Inicio" de `MainWindow` reaparecían visibles tras el primer render real de la
  ventana pese a estar en la pantalla inicial (Sprint 49) — `QToolBar` reseteaba su visibilidad en un
  evento de layout que el bucle de eventos real dispara después de `show()`. Corregido migrando esos
  botones a `QAction`; superado además por construcción al reemplazar el `QToolBar` por el sidebar del
  Sprint 50.

### Changed
- Navegación de "Parametros" reorganizada en "Configuraciones" (Sprint 66): el botón del sidebar pasa a
  llamarse "Configuraciones" y abre una pantalla con submenú lateral (Parámetros/Apariencia, con espacio
  para futuras secciones); el interruptor de modo oscuro/claro, antes alojado en Parámetros, se mueve a la
  nueva sección Apariencia. Sin cambios de comportamiento en la tabla de parámetros legales ni en la
  lógica de tema — solo de ubicación.
- Deuda técnica de `ruff` eliminada por completo (Sprint 48): 447 errores preexistentes (mayoritariamente
  líneas demasiado largas) limpiados sin cambiar comportamiento; `ruff check .` agregado como paso
  obligatorio del pipeline de CI (`.github/workflows/ci.yml`), antes de la suite de tests.
- `docs/GUIA_USUARIO.md` y 2 `docs/specifications/*.md` actualizados (Sprint 54): describían la barra de
  navegación superior en vez del sidebar del Sprint 50, no mencionaban el modo oscuro ni la gráfica del
  Dashboard, afirmaban que prescripción/caducidad seguía sin conectarse (ya lo estaba desde el Sprint 42),
  y que la UVT seguía sin cargar (cargada desde los Sprints 5/14). `CONTRIBUTING.md` actualizado con los
  prefijos de commit realmente usados en el repo (`merge:`, `refactor:`, `perf:`, `style:`, `build:`).
- El campo "Vigente hasta" ahora explica en la propia UI por qué está deshabilitado cuando el parámetro
  no usa fecha de fin, en vez de desaparecer sin explicación.

## [0.1.0] - 2026-08-04

Primera versión etiquetada del proyecto. BASTIUM ya calcula liquidaciones completas en las áreas
Civil/Familia, Comercial, Sancionatorio, Honorarios/Litigio, Laboral y Tributario, con exportación a
PDF/Word, historial de auditoría por expediente, y parámetros legales versionados editables desde la
interfaz. Este sprint (28) no agrega funcionalidad de cálculo — profesionaliza el repositorio de cara
a su publicación pública en GitHub.

### Added
- Integración continua (GitHub Actions) que corre la suite de `pytest` en cada push/PR a `main`.
- `__version__` (`app/_version.py`), primera versión etiquetada del proyecto.
- Variable de entorno `BASTIUM_DB_PATH` para configurar la ruta de `bastium.db` sin editar código
  fuente.
- `conftest.py` raíz en `tests/` con la fixture de sesión en memoria compartida, reemplazando su
  duplicación en 13+ archivos de test.
- `CONTRIBUTING.md`, `SECURITY.md` (con aviso legal), plantillas de Issues/PR
  (`.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`).
- Badges de CI, versión y licencia, y aviso legal corto, en `README.md`.

[0.1.0]: https://github.com/JoseMsD21/BASTIUM-CALCULOS/releases/tag/v0.1.0
