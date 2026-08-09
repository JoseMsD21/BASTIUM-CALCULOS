# Sprint 37 — Comportamiento de ventana y accesibilidad de teclado Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `main.py` deja de fijar `window.resize(1000, 700)` en cada arranque — la geometría de ventana
(tamaño, posición, maximizado) se persiste entre sesiones vía `QSettings`. El orden de tabulación de
`ObligacionFormDialog` y `ExpedienteFormDialog` queda explícito y lógico. `Enter`/`Return` dispara el botón
por defecto ("Guardar") y `Esc` cierra sin guardar, de forma consistente en todos los diálogos de
formulario.

**Architecture:** `QSettings` con `QSettings.IniFormat` o el formato nativo por plataforma, usando
`QApplication.setOrganizationName`/`setApplicationName` (ya existe `app.setApplicationName("BASTIUM")` en
`main.py:16`) como namespace — guardar `saveGeometry()`/`saveState()` de `MainWindow` en `closeEvent` (o
`aboutToQuit`) y restaurar con `restoreGeometry()` en el arranque, con fallback al tamaño por defecto
1000x700 si no hay valor guardado (primer arranque). El orden de tabulación se fija explícitamente con
`QWidget.setTabOrder(a, b)` encadenado siguiendo el orden visual de cada formulario (de arriba hacia abajo,
izquierda a derecha dentro de cada fila). `Enter` como botón por defecto es una propiedad estándar de Qt
(`QPushButton.setDefault(True)` en el botón "Guardar" de cada `QDialog`) — confirmar que ya funciona
correctamente (Qt lo hace automático para el primer botón por defecto en muchos casos) o fijarlo
explícitamente donde falte. `Esc` cierra un `QDialog` sin guardar por comportamiento nativo de Qt
(`QDialog.reject()`) salvo que algo lo intercepte — confirmar, no asumir, leyendo el código de cada diálogo.

**Tech Stack:** Python 3.14, PySide6 6.11 (`QtCore.QSettings`, `QtWidgets.QWidget.setTabOrder`,
`QtWidgets.QPushButton.setDefault`, `QtWidgets.QDialog.reject`), pytest + pytest-qt (`qtbot`).

---

### Contexto compartido entre tareas

- No depende de nada, pero verificar el código actual de `ObligacionFormDialog` (`app/views/obligaciones.py`)
  y `ExpedienteFormDialog` (`app/views/expedientes.py`) — el Sprint 34 ya reorganizó `ObligacionFormDialog`
  en secciones colapsables, así que el orden de tabulación actual puede no coincidir con los Hallazgos
  originales de `Pendientes.md`; verifica leyendo el código, no asumas.
- No introducir modo oscuro/claro configurable (fuera de alcance, ver Sprint 31/37 en `Pendientes.md`) —
  este sprint es solo geometría de ventana + teclado.

### Task 1: Persistir geometría de ventana con QSettings

- [x] `MainWindow._restaurar_geometria()`/`closeEvent()` (`app/views/main_window.py`) persisten
      tamaño/posición/maximizado vía `QSettings(IniFormat, UserScope, "BASTIUM", "BASTIUM")`, con fallback a
      1000x700 si no hay valor guardado o `restoreGeometry()` lo rechaza. `main.py` ya no fija
      `resize(1000, 700)` incondicionalmente.
- [x] Test que guarda una geometría y confirma que una nueva instancia de `MainWindow` la restaura
      (`tests/views/test_main_window.py`).
- [x] Self-review: fallback verificado en `QSettings` vacío; `tests/conftest.py::_qsettings_aislado`
      (autouse) redirige `QSettings.setPath()` a `tmp_path` para que ningún test toque el `.ini` real del
      sistema.

### Task 2: Orden de tabulación explícito en ObligacionFormDialog y ExpedienteFormDialog

- [x] `ObligacionFormDialog._fijar_orden_de_tabulacion()` y el bloque equivalente en
      `ExpedienteFormDialog.__init__` (`app/views/expedientes.py`) encadenan `setTabOrder` siguiendo el
      orden visual actual (post-Sprint 34), incluyendo campos condicionales de todas las áreas.
- [x] Tests en `tests/views/test_obligaciones.py` y `tests/views/test_expedientes.py`.

### Task 3: Enter dispara Guardar, Esc cancela — en todos los diálogos de formulario

- [x] `setDefault(True)` explícito en el botón "Guardar" de los 5 `QDialog` de formulario del proyecto
      (`ObligacionFormDialog`, `ExpedienteFormDialog`, `AbonoFormDialog`, `EventoLaboralFormDialog`,
      `ParametroFormDialog`) — inventariados con `grep -rl "class.*QDialog" app/views/`, los 5 ya lo tienen.
- [x] `Esc` confirmado como comportamiento nativo de `QDialog.reject()` sin interceptar en ninguno (test
      preexistente `test_escape_cierra_el_dialogo_sin_guardar` + verificación de código).
- [x] Tests `Qt.Key_Return`/`Qt.Key_Escape` en `ObligacionFormDialog` y `ExpedienteFormDialog`.

### Task 4: Verificación final

- [x] Suite completa de tests (`pytest`) en verde: 844 passed.
- [x] Verificación cubierta por los tests de teclado (Tab + Enter en orden lógico) y de persistencia de
      geometría de las Tasks 1-3.
