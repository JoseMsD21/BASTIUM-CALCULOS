# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/), y este proyecto usa
[Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

Sprints 31-37: primer sistema de diseño visual de la GUI y mejoras de UX construidas sobre él
(navegación, pantalla de inicio, formularios, listados, feedback no bloqueante, jerarquía de botones,
persistencia de ventana y accesibilidad de teclado). Sprints 39-40: dos bugs reales corregidos (etiquetas
huérfanas en formularios, interés causado ausente en la tabla del PDF). Sprint 38: licencia Apache 2.0
publicada. Ningún cambio de lógica de cálculo salvo el desglose de interés por fila del Sprint 40 (el
saldo final ya era correcto).

### Added
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
