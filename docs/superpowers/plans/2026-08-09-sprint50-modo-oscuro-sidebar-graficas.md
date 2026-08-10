# Sprint 50 — Mejoras de personalización y presentación diferidas (modo oscuro, sidebar, gráficas del dashboard) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Decisión del usuario (2026-08-09):** implementar las 3 mejoras diferidas, en orden: (1) modo oscuro/claro,
(2) sidebar de navegación completo, (3) gráficas en el Dashboard. Trabajar como 3 tareas secuenciales dentro
de este mismo sprint — no dividir en sprints separados. Corregir también la referencia cruzada rota que el
Sprint 31 dejó apuntando al Sprint 37 (que nunca cubrió modo oscuro).

---

## Tarea 1: Modo oscuro/claro

**Goal:** El usuario puede alternar entre tema claro (el actual, sin cambios visuales) y un tema oscuro
completo, con la elección persistida entre sesiones.

**Architecture:** `app/core/theme_colors.py` expone hoy constantes de módulo (`PRIMARIO`, `FONDO`, etc.)
consumidas por `construir_paleta()`/`aplicar_tema()` (`app/core/apariencia.py`) y hardcodeadas también en
`resources/theme.qss` (el propio docstring de `theme_colors.py` ya documenta que Qt QSS no soporta
variables, así que los dos deben mantenerse sincronizados a mano). Para el modo oscuro:
- Nuevo módulo `app/core/theme_colors_dark.py` con exactamente los mismos nombres de constante que
  `theme_colors.py`, valores oscuros (fondo oscuro, texto claro, misma familia de acento burdeos del
  Sprint 31 ajustada para contraste — no reinventar la identidad de marca, solo invertir luminancia).
- Nuevo archivo `resources/theme_dark.qss`, mismo contenido estructural que `resources/theme.qss` con los
  valores hex de `theme_colors_dark.py` (mismo patrón manual de sincronización que ya existe para el modo
  claro, documentado en el docstring del módulo).
- `construir_paleta(modo: str = "claro")` y `aplicar_tema(app, modo: str = "claro")` reciben el modo y
  seleccionan el módulo de colores/`.qss` correspondiente.
- Persistencia vía `QSettings` (mismo patrón `IniFormat`/namespace "BASTIUM" ya establecido en
  `MainWindow._crear_settings()`, Sprint 37 — reutilizarlo, no duplicar la lógica de aislamiento en tests).
- Control para alternar: un botón/checkbox en la pantalla de Parámetros (`app/views/configuracion.py`) o en
  la barra de navegación — decidir durante la implementación cuál encaja mejor con el sidebar de la Tarea 2
  (implementar la Tarea 1 primero, pero dejar el control en un lugar que la Tarea 2 no tenga que mover dos
  veces). Alternar el tema en caliente debe re-aplicar `aplicar_tema()` sin reiniciar la app.

### Sub-tareas

- [x] `theme_colors_dark.py` + `resources/theme_dark.qss`.
- [x] `construir_paleta()`/`aplicar_tema()` parametrizados por modo (`app/core/apariencia.py`).
- [x] Persistencia vía `QSettings` (`guardar_modo_tema()`/`cargar_modo_tema()`), reutilizando
      `app/core/settings.py::crear_settings()` (extraído de `MainWindow._crear_settings()` para no
      duplicar el patrón del Sprint 37).
- [x] Checkbox "Modo oscuro" en `ParametrosView` aplica el tema en caliente sin reiniciar la app.
- [x] Comentario del Sprint 31 corregido en `theme_colors.py`/`theme.qss` — ya no apunta al Sprint 37.

---

## Tarea 2: Sidebar de navegación completo

**Goal:** Reemplazar el `QToolBar` superior de `MainWindow` por un sidebar lateral, conservando toda la
funcionalidad de navegación actual (breadcrumb, atajos de teclado, estado activo de "Parámetros", los 5
botones/acciones existentes).

**Architecture:** `MainWindow._crear_barra_navegacion()` (`app/views/main_window.py`) construye hoy un
`QToolBar` con `boton_volver`/`boton_inicio`/`boton_parametros` + breadcrumb. Reemplazar por un panel lateral
(`QWidget` con `QVBoxLayout` dentro de un `QSplitter` horizontal junto al `QStackedWidget` de páginas, o un
`QDockWidget` fijo — preferir `QSplitter` si no hace falta que el usuario lo cierre/flote, más simple).
Mantener los mismos nombres de atributo (`boton_volver`, `boton_inicio`, `boton_parametros`,
`etiqueta_breadcrumb`) para no romper los tests existentes de `tests/views/test_main_window.py` que ya los
referencian, salvo que el plan de pruebas de esta tarea los actualice explícitamente. Reutilizar
`_actualizar_botones_navegacion()`/`_actualizar_breadcrumb()`/`_actualizar_estado_activo_navegacion()` tal
cual — son independientes de si los widgets viven en un `QToolBar` o un sidebar.

**Coordinación con el Sprint 49 (si corre en paralelo):** el Sprint 49 corrige un bug de timing de
visibilidad específico de `QToolBar.addWidget()`. Si el sidebar de esta tarea deja de usar `QToolBar`, ese
bug podría dejar de aplicar por construcción — no asumir esto sin verificarlo con el test que dejó el Sprint
49 (`test_botones_navegacion_ocultos_en_pagina_inicial` actualizado para ejercer el bucle de eventos real);
si ambos sprints se mezclan y ese test sigue en verde con el sidebar nuevo, no hace falta el fix del Sprint
49 en el código final — pero no eliminar el trabajo del Sprint 49 preventivamente, resolverlo en el momento
del merge con evidencia (el test corriendo), no por suposición.

### Sub-tareas

- [x] Sidebar nuevo (`QWidget` + `QVBoxLayout` dentro de un `QSplitter` horizontal junto al
      `QStackedWidget`) con los mismos botones/breadcrumb, mismos nombres de atributo
      (`boton_volver`/`boton_inicio`/`boton_parametros`/`etiqueta_breadcrumb`).
- [x] Tests existentes de `test_main_window.py` siguen en verde sin modificarse + 2 tests nuevos que
      verifican la estructura sidebar/splitter.
- [x] Coordinación con el Sprint 49 verificada al momento del merge (no en este worktree): el sidebar ya no
      usa `QToolBar` para estos botones, así que el bug de timing que corrigió el Sprint 49
      (`QToolBarLayout` reseteando la visibilidad de widgets vía `addWidget()`) deja de aplicar por
      construcción — confirmado con el test de regresión del Sprint 49 corriendo en verde sobre el
      resultado combinado.

---

## Tarea 3: Gráficas en el Dashboard

**Goal:** `DashboardView` (`app/views/dashboard.py`) gana al menos una visualización gráfica (ej.
expedientes por área), usando `matplotlib` (ya en `requirements.txt`, sin uso real en el código hoy).

**Architecture:** Widget `FigureCanvasQTAgg` (backend `matplotlib.backends.backend_qtagg`, el oficial para
PySide6/Qt6) embebido en el `layout_resumen` o un nuevo `QGroupBox` de `DashboardView`, junto al conteo
tabular por área ya existente (`_refrescar_conteo_por_area`) — no lo reemplaza, lo complementa. Reutilizar
`app.core.theme_colors` para los colores de la gráfica (consistente con la paleta de marca, y con el modo
oscuro/claro de la Tarea 1 si el dashboard se refresca tras alternar el tema — verificar). Gráfica de barras
simple (expedientes por área) es la opción más barata de construir sobre datos ya disponibles en
`refrescar()`; evaluar durante la implementación si agregar una segunda gráfica (evolución de liquidaciones
en el tiempo) cabe en el alcance sin sobrecargar el Dashboard.

### Sub-tareas

- [x] `FigureCanvasQTAgg` (`matplotlib.backends.backend_qtagg`) embebido en `DashboardView`
      (`figura_por_area`/`canvas_por_area`), gráfico de barras de expedientes por área poblado desde los
      mismos datos que `_refrescar_conteo_por_area` (sin volver a consultar la sesión), junto a la tabla
      existente en el mismo `QGroupBox` — la complementa, no la reemplaza.
- [x] Colores de la gráfica resueltos según `apariencia.cargar_modo_tema()` (`theme_colors`/
      `theme_colors_dark`), no fijos — combina con el tema claro/oscuro activo.
- [x] `_refrescar_grafica_por_area()` se llama desde `refrescar()`; test confirma que la gráfica se
      actualiza con datos nuevos (`tests/views/test_dashboard.py`, 3 tests nuevos).

---

## Verificación final (todas las tareas)

- [x] Suite completa de tests (`pytest`) en verde: 967 passed.
- [x] Verificación cubierta por los tests de cada tarea (cambio de tema en caliente, estructura del
      sidebar, actualización de la gráfica al refrescar).
