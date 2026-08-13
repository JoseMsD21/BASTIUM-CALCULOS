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

### Added
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

### Fixed
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
- Deuda técnica de `ruff` eliminada por completo (Sprint 48): 447 errores preexistentes (mayoritariamente
  líneas demasiado largas) limpiados sin cambiar comportamiento; `ruff check .` agregado como paso
  obligatorio del pipeline de CI (`.github/workflows/ci.yml`), antes de la suite de tests.
- `docs/GUIA_USUARIO.md` y 2 `docs/specifications/*.md` actualizados (Sprint 54): describían la barra de
  navegación superior en vez del sidebar del Sprint 50, no mencionaban el modo oscuro ni la gráfica del
  Dashboard, afirmaban que prescripción/caducidad seguía sin conectarse (ya lo estaba desde el Sprint 42),
  y que la UVT seguía sin cargar (cargada desde los Sprints 5/14). `CONTRIBUTING.md` actualizado con los
  prefijos de commit realmente usados en el repo (`merge:`, `refactor:`, `perf:`, `style:`, `build:`).

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
