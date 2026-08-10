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

- [x] `test_botones_navegacion_ocultos_en_pagina_inicial` actualizado con `qtbot.wait(1)` tras `show()`
      (`qtbot.wait(0)` resultó ser un no-op en esta versión de pytest-qt — salta `qt_api.exec(self._loop)`
      cuando `timeout==0` — así que no servía para reproducir el bug). Confirmado rojo antes de corregir.
      Nota de verificación adicional (2026-08-09): reproducido también de forma independiente con un
      script standalone (`app.exec()` real, sin pytest-qt) contra el código pre-fix.

### Task 2: Corregir la causa raíz

- [x] Opción 2 elegida (migración a `QAction`): `boton_volver`/`boton_inicio`/`boton_parametros` pasan de
      `QPushButton` + `barra.addWidget()` a `QAction` + `barra.addAction()`. `self.boton_*` sigue apuntando
      al `QToolButton` que `QToolBar` autogenera (`barra.widgetForAction(...)`), así que el resto del código
      y los tests existentes que ya usaban `.isVisible()`/`.setProperty()`/`.style()` no necesitaron cambios.
      La visibilidad se controla ahora sobre la `QAction` (`self._accion_*`), que `QToolBarLayout` sí
      respeta de forma consistente a través de layouts repetidos. `showEvent()` (el fix anterior, que solo
      cubría el instante síncrono) ya no hace falta y se eliminó — la causa raíz queda resuelta, no
      parchada.
- [x] Test de la Task 1 pasa en verde con la corrección (confirmado estable en 15+ corridas).
- [x] Confirmado con tests dedicados (`tests/views/test_main_window.py -k "parametros or clase o
      estado_activo"`) que el estilo `primary`/`secondary` de `boton_parametros` sigue funcionando —
      `resources/theme.qss` gana selectores `QToolButton[class="..."]` acotados por el atributo `class`
      (ningún `QToolButton` nativo de Qt, como los del popup de `QDateEdit`, tiene esa propiedad, así que
      no los afecta — documentado en el comentario de riesgo ya existente al inicio del archivo).

### Task 3: Verificación final

- [x] Script standalone (`app.exec()` real vía `QTimer.singleShot` + 20 ciclos de `processEvents()`, sin
      `pytest-qt`) confirma que los botones permanecen ocultos en la pantalla inicial tras la corrección.
- [x] Suite completa de tests (`pytest`) en verde: 953 passed.
