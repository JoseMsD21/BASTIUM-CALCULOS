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

- [ ] En `main.py` (o `MainWindow`, decidir según dónde viva mejor el ciclo de vida — `MainWindow` es más
      testeable con `qtbot`), restaurar `QSettings` guardado al construir la ventana (con fallback a
      1000x700 si no existe valor previo) y guardarlo en el cierre (`closeEvent` de `MainWindow`, no en
      `main.py`, para poder testear con `qtbot` sin lanzar `sys.exit`).
- [ ] Test que confirme: al guardar una geometría y restaurarla en una nueva instancia de `QSettings`
      apuntando al mismo namespace, la ventana recupera tamaño/posición/estado maximizado.
- [ ] Self-review: confirmar que el fallback al tamaño por defecto sigue funcionando en un `QSettings`
      vacío (primer arranque / entorno de test limpio), y que los tests no dejan basura persistida en el
      `QSettings` real del sistema (usar un namespace/organización de test aislado en los tests, o
      `QSettings.setPath`/formato temporal).

### Task 2: Orden de tabulación explícito en ObligacionFormDialog y ExpedienteFormDialog

- [ ] Revisar el orden visual actual de campos en ambos diálogos (leyendo el código tal como está hoy,
      post-Sprint 34) y fijar `setTabOrder` encadenado para que coincida con el orden lógico/visual.
- [ ] Test (`qtbot.keyClick` con `Qt.Key_Tab` recorriendo el formulario, o inspección directa de
      `nextInFocusChain()`) que confirme el orden esperado en al menos un caso representativo de cada
      diálogo.

### Task 3: Enter dispara Guardar, Esc cancela — en todos los diálogos de formulario

- [ ] Confirmar/asegurar `QPushButton.setDefault(True)` en el botón "Guardar" (o equivalente) de cada
      `QDialog` de formulario del proyecto (no solo los dos mencionados en los Hallazgos — revisar todos
      los `QDialog` con formulario, ej. `AbonoFormDialog`, diálogos de eventos laborales, etc., si existen).
- [ ] Confirmar que `Esc` cierra cada uno de esos diálogos sin guardar (comportamiento nativo `reject()`,
      salvo que algún diálogo lo intercepte incorrectamente — corregir si es el caso).
- [ ] Tests (`qtbot.keyClick` con `Qt.Key_Return`/`Qt.Key_Escape`) que confirmen ambos comportamientos en
      al menos `ObligacionFormDialog` y `ExpedienteFormDialog`.

### Task 4: Verificación final

- [ ] Suite completa de tests (`pytest`) en verde.
- [ ] Verificación manual/documentada: un usuario puede completar y guardar un formulario usando solo
      teclado (Tab + Enter) en orden lógico, y la ventana recuerda tamaño/posición entre sesiones.
