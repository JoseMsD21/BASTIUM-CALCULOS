# Sprint 39 — Bug de UI: etiquetas huérfanas en QFormLayout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ningún campo condicional de `ObligacionFormDialog` (`app/views/obligaciones.py`) ni de los
diálogos de eventos laborales (`app/views/eventos_laborales.py`) deja su `QLabel` de `QFormLayout` visible
cuando el widget asociado está oculto (`setVisible(False)`). El patrón correcto ya existe en el propio
`obligaciones.py` (par `campo_fecha_origen`/`label_fecha_origen`) — se generaliza a **todos** los
`addRow(str, widget)` condicionales del archivo, no solo a los originalmente reportados ("Valor" y "Nivel
de riesgo ARL").

**IMPORTANTE — el código ya cambió desde que se escribió el hallazgo original:** el Sprint 34
(`docs/superpowers/plans/2026-08-06-sprint34-ux-formularios.md`) reorganizó `ObligacionFormDialog` en
secciones colapsables, y una verificación visual posterior (QA del Sprint 34, 2026-08-06, documentada en
`Pendientes.md` bajo este mismo sprint) confirmó que el patrón de etiqueta huérfana es mucho más extendido
de lo que documentaban los 3 casos originales: prácticamente todos los campos condicionales del diálogo lo
sufren (ejemplos vistos con `area="CIVIL_FAMILIA"`: "Fecha de inicio (Recurrente)", "Dia de pago
(Recurrente)", "Cantidad SMLMV/UVT (Sancionatorio)", "Base de la sancion...", "Meses o fraccion de
atraso...", "Ingresos brutos (Renta liquida)", "Devoluciones/rebajas/descuentos (Renta liquida)", "Costos
(Renta liquida)", "Deducciones (Renta liquida)", "Rentas exentas (Renta liquida)", "Fecha de terminacion de
contrato", "Fecha de pago real", "Nivel de riesgo ARL"). **No confíes en los números de línea de
`Pendientes.md` (186-188, 127, 161, 197) — están desactualizados.** Lee el archivo completo actual antes de
tocar nada.

**Architecture:** Para cada `addRow(str, widget)` cuyo widget se oculta condicionalmente en algún punto del
código (`widget.setVisible(False)` o equivalente en un método de actualización de visibilidad como
`_actualizar_campos_visibles`), aplica una de estas dos soluciones (elegir la primera que la versión de
PySide6 instalada soporte, confirmar con `python -c "import PySide6; print(PySide6.__version__)"` y
revisando la documentación de `QFormLayout` de esa versión):

1. **Preferida si está disponible:** `layout.setRowVisible(widget, visible: bool)` — sincroniza automática
   y correctamente la fila completa (etiqueta + widget) en una sola llamada, sin necesidad de guardar una
   referencia al `QLabel`. Disponible desde Qt 6.4+.
2. **Fallback:** guardar la referencia al `QLabel` que devuelve `layout.addRow(...)` (o recuperarlo después
   vía `layout.labelForField(widget)`) y llamar `label.setVisible(visible)` en el mismo punto donde se
   llama `widget.setVisible(visible)` — exactamente el patrón que ya usa el par
   `campo_fecha_origen`/`label_fecha_origen` en el propio archivo.

Aplicar de forma sistemática y no ad-hoc: idealmente, refactorizar el método que centraliza la actualización
de visibilidad condicional (`_actualizar_campos_visibles` o como se llame en el código actual) para que
itere sobre una lista/diccionario de pares `(widget, condición)` y aplique la visibilidad de forma uniforme
a fila completa, en vez de repetir `widget.setVisible(...)` suelto por cada campo — esto previene que el
mismo bug reaparezca la próxima vez que se agregue un campo condicional nuevo.

**Tech Stack:** Python 3.14, PySide6 6.11 (`QtWidgets.QFormLayout.setRowVisible` o
`QtWidgets.QFormLayout.labelForField`), pytest + pytest-qt (`qtbot`).

---

### Contexto compartido entre tareas

- Alcance ampliado (confirmado en `Pendientes.md`, sección de este sprint, "Hallazgo adicional"): cubrir
  **todos** los campos condicionales de `ObligacionFormDialog`, no solo los 2-3 originalmente reportados.
- Antes de escribir código, correr `git grep -n "setVisible" app/views/obligaciones.py
  app/views/eventos_laborales.py` para inventariar cada caso real y confirmar cuáles corresponden a un
  `addRow(str, widget)` (con etiqueta de texto) vs. un widget sin etiqueta (ej. dentro de un `QVBoxLayout`,
  que no tiene este bug).
- Revisar también el resto de `app/views/` por si hay más archivos con el mismo patrón (el "Alcance
  incluido" original de `Pendientes.md` lo pide explícitamente), aunque el foco confirmado está en
  `obligaciones.py` y `eventos_laborales.py`.

### Task 1: Inventario y corrección de ObligacionFormDialog

- [ ] Listar cada `addRow(str, widget)` de `ObligacionFormDialog` cuyo widget se oculta condicionalmente en
      algún punto del código.
- [ ] Aplicar `setRowVisible` (o el patrón de referencia a `QLabel` si no está disponible) a cada uno,
      idealmente centralizado en el método que ya agrupa la lógica de visibilidad condicional.
- [ ] Test de GUI parametrizado (`qtbot`) que abra el diálogo con `area="SANCIONATORIO"` y confirme que
      "Valor" y "Nivel de riesgo ARL" no quedan visibles como fila huérfana; y con `area="CIVIL_FAMILIA"`
      (tipo Puntual) que ningún campo no aplicable a esa combinación área/tipo deja su etiqueta visible sin
      su widget.

### Task 2: Corrección de eventos_laborales.py

- [ ] Aplicar la misma solución al combo de "Motivo de suspension" (`app/views/eventos_laborales.py`), cuya
      etiqueta debe ocultarse junto con el combo cuando el tipo de evento no es Suspensión.
- [ ] Test de GUI que confirme que al seleccionar un evento tipo Incapacidad, la etiqueta "Motivo de
      suspension" no es visible.

### Task 3: Barrido del resto de app/views/

- [ ] Revisar rápido el resto de `app/views/` buscando otros `setVisible(False)` sobre un widget de un
      `addRow(str, widget)` sin ocultar también la etiqueta; corregir cualquier caso adicional encontrado
      con el mismo patrón.

### Task 4: Verificación final

- [ ] Suite completa de tests (`pytest`) en verde.
- [ ] Confirmar las 3 verificaciones de la Definición de Hecho del sprint en `Pendientes.md` (Sancionatorio,
      evento Incapacidad, Civil/Familia sin campos huérfanos).
