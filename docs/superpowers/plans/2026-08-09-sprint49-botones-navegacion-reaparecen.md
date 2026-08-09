# Sprint 49 — Bug de UI: los botones "Volver"/"Inicio" reaparecen visibles tras el primer render de la ventana Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `MainWindow.boton_volver`/`boton_inicio` permanecen ocultos en la pantalla inicial (sin historial)
a través de todo el bucle de eventos real de la app (`show()` + `processEvents()`/`app.exec()`), no solo en
el instante síncrono de `showEvent()`.

**Causa raíz confirmada (verificado leyendo `app/views/main_window.py`, líneas ~110-195 actuales):**
`_crear_barra_navegacion()` agrega `boton_volver`/`boton_inicio`/`boton_parametros` a un `QToolBar` vía
`barra.addWidget(...)` (no `QAction`). El comentario ya existente en `showEvent()` documenta correctamente
que `QToolBar` resetea la visibilidad de widgets agregados así a `True` la primera vez que el toolbar mismo
se vuelve visible — pero el fix actual (`_actualizar_botones_navegacion()` llamado síncronamente dentro de
`showEvent()`) solo cubre el instante inmediato de `showEvent()`; el reset real de `QToolBar` ocurre en un
evento adicional en cola que se dispara en el primer `processEvents()` posterior a `show()` (el bucle de
eventos real de `main.py` vía `app.exec()`, que la suite de tests actual nunca ejerce después de `show()`).

**Architecture:** Dos soluciones candidatas, evaluar cuál corrige el síntoma con el test de reproducción de
la Task 1 antes de decidir (preferir la primera si funciona, es el cambio más pequeño):
1. **`QTimer.singleShot(0, self._actualizar_botones_navegacion)` dentro de `showEvent()`** — reprograma la
   resincronización para el próximo ciclo del bucle de eventos, después de que `QToolBar` ya haya hecho su
   reset interno, en vez de competir con él síncronamente.
2. **Migrar `boton_volver`/`boton_inicio`/`boton_parametros` de `QPushButton` vía `addWidget()` a
   `QAction`** — si `QToolBar` no aplica el mismo reset de visibilidad a `QAction`, esto elimina la causa
   raíz en vez de parchear el síntoma. Riesgo: `QAction` no tiene exactamente la misma API que
   `QPushButton` (ej. `setProperty("class", ...)` para el estilo QSS del Sprint 31/36 puede no aplicar
   igual sobre el botón que `QToolBar` renderiza para un `QAction`) — verificar que el estilo visual
   (`primary`/`secondary`) siga funcionando antes de preferir esta opción sobre la 1.

**Tech Stack:** Python 3.14, PySide6 6.11 (`QtCore.QTimer`, `QtWidgets.QToolBar`, `QtWidgets.QAction`),
pytest + pytest-qt (`qtbot`).

---

### Contexto compartido entre tareas

- **No rediseñar la barra de navegación** (fuera de alcance, ya cubierta por el Sprint 32) — es un fix
  puntual de timing/visibilidad.
- El bug es preexistente (reproducido incluso en el commit anterior al Sprint 31) — no es una regresión de
  ningún sprint reciente.
- **Riesgo de conflicto:** el Sprint 50 (si se ejecuta en paralelo) también toca `app/views/main_window.py`
  extensamente (posible sidebar). Verificar al momento del merge que ambos cambios sigan siendo coherentes
  entre sí.

### Task 1: Reproducir el bug con un test que ejerce el bucle de eventos real

- [ ] Actualizar `test_botones_navegacion_ocultos_en_pagina_inicial`
      (`tests/views/test_main_window.py`) para ceder el control al bucle de eventos después de `show()`
      (`qtbot.wait(0)` o `app.processEvents()`), de forma que ejerza el mismo camino que la app real.
      Confirmar que el test FALLA con el código actual (reproduce el bug) antes de corregir nada — esto es
      TDD: rojo primero.

### Task 2: Corregir la causa raíz

- [ ] Implementar la solución elegida (Task de Architecture arriba) para que
      `boton_volver`/`boton_inicio` permanezcan ocultos después del ciclo adicional del bucle de eventos.
- [ ] El test de la Task 1 pasa (verde) con la corrección.
- [ ] Si se opta por la migración a `QAction` (opción 2): confirmar con un test que el estado visual
      `primary`/`secondary` de `boton_parametros` (Sprint 32/36) sigue funcionando igual.

### Task 3: Verificación final

- [ ] Script standalone que reproduce el arranque real de la app (`show()` + `processEvents()`, sin
      `pytest-qt`) confirma que los botones permanecen ocultos en la pantalla inicial — documentar cómo se
      corrió (no hace falta dejarlo como archivo permanente en el repo si no sigue la convención de tests).
- [ ] Suite completa de tests (`pytest`) en verde.
