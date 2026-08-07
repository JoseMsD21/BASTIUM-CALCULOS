# Sprint 36 — Feedback no bloqueante y jerarquía visual de botones Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar el uso de `QMessageBox` modal para confirmaciones de bajo riesgo (ej. "Obligación
guardada") por una notificación no bloqueante tipo toast/snackbar, reservando `QMessageBox` para errores y
confirmaciones destructivas/irreversibles. Además, dar jerarquía visual clara a los botones de las 8 vistas
(`app/views/*.py`): primario (acción principal, color de marca), secundario (neutro) y destructivo
(rojo/advertencia), usando el sistema `.qss` del Sprint 31.

**Architecture:** El Sprint 31 ya estableció `resources/theme.qss` + `app/core/apariencia.py` como el punto
único de estilos, y el Sprint 35 ya usa `boton.setProperty("class", "primary")` como convención de botón
primario (ver `ExpedientesListView`, botón de estado vacío). Este sprint generaliza esa convención: agrega
selectores QSS para `[class="secondary"]` y `[class="destructive"]` junto al `[class="primary"]` ya
existente (confirmar en `resources/theme.qss` si ya existe alguno de los tres; si no, crearlos con la
paleta burdeos/crema del Sprint 31 — primario = color de marca, secundario = neutro/gris, destructivo =
rojo/advertencia), y aplica `setProperty("class", ...)` a los botones relevantes de las 8 vistas según su
riesgo/importancia semántica (Guardar/Liquidar = primary, Cancelar = secondary, Eliminar = destructive).
El toast se implementa como un widget nuevo (`app/views/` o `app/core/`, decidir ubicación siguiendo la
convención existente del proyecto — los widgets de vista viven en `app/views/`) — un `QLabel` flotante con
auto-ocultado vía `QTimer.singleShot`, posicionado sobre la ventana/vista activa, sin bloquear el hilo ni
requerir click para cerrarse. Sustituir únicamente los `QMessageBox.information(...)` de confirmación de
éxito de bajo riesgo (guardar/actualizar) por el toast; dejar intactos los `QMessageBox` de error y de
confirmación de borrado/acciones destructivas (esos deben seguir siendo modales, es la app la que decide
qué es "bajo riesgo").

**Tech Stack:** Python 3.14, PySide6 6.11 (`QtWidgets.QLabel`, `QtCore.QTimer`, `QtWidgets.QGraphicsOpacityEffect`
opcional para fade), pytest + pytest-qt (`qtbot`), ruff (line-length 99, `target-version = "py314"`).

---

### Contexto compartido entre tareas

- Antes de tocar cualquier vista, correr `git grep -n "QMessageBox.information" app/views/` y
  `git grep -n "QPushButton(" app/views/` para inventariar exactamente qué confirmaciones y qué botones
  existen hoy — el Sprint 34/35 ya modificaron `obligaciones.py` y `expedientes.py`, así que no asumas los
  números de línea de los Hallazgos originales en `Pendientes.md`, verifica el estado actual.
- No crear un sistema de notificaciones persistente/centro de notificaciones (fuera de alcance explícito).
- Reservar `QMessageBox` modal para: errores (siempre) y confirmaciones de acciones destructivas/
  irreversibles (ej. "¿Eliminar expediente?"). Todo lo demás que hoy sea `QMessageBox.information` de
  éxito puntual pasa a toast.

### Task 1: Widget de notificación toast reutilizable

- [ ] Crear el widget toast (`QLabel` flotante, auto-ocultado con `QTimer.singleShot`, sin robar el foco
      del teclado ni bloquear interacción con la ventana) con una función/clase reutilizable desde
      cualquier vista (ej. `mostrar_toast(parent, mensaje, tipo="success")`).
- [ ] Tests de GUI (`qtbot`) que confirmen: el toast aparece con el mensaje correcto, se autooculta tras su
      timeout, y no bloquea la interacción con el resto de la ventana mientras está visible.
- [ ] Self-review: TDD seguido (test antes de implementación), sin código muerto, nombres en español
      consistentes con el resto del proyecto.

### Task 2: Clases de estilo QSS para jerarquía de botones (primary/secondary/destructive)

- [ ] En `resources/theme.qss`, confirmar o agregar los 3 selectores de clase de botón con la paleta del
      Sprint 31 (`app/core/theme_colors.py`), consistentes en modo claro/oscuro si aplica.
- [ ] Test (si existe infraestructura de test de estilos) o verificación manual documentada de que las 3
      clases producen colores visualmente distinguibles.

### Task 3: Aplicar jerarquía de botones y sustituir confirmaciones de bajo riesgo por toast en las 8 vistas

- [ ] Recorrer cada archivo de `app/views/` (excluyendo `icons.py`, que no tiene botones): asignar
      `setProperty("class", "primary"|"secondary"|"destructive")` a cada `QPushButton` según su semántica,
      y sustituir cada `QMessageBox.information(...)` de éxito de bajo riesgo por `mostrar_toast(...)`.
- [ ] Dejar sin tocar los `QMessageBox` de error y de confirmación destructiva.
- [ ] Tests de GUI existentes siguen en verde; agregar/actualizar los que dependían del `QMessageBox` de
      éxito reemplazado (deben ahora esperar el toast, no un diálogo modal).
- [ ] Self-review: confirmar que ningún botón quedó sin clase asignada, y que ninguna confirmación
      destructiva fue degradada a toast por error (sería una regresión de seguridad de UX).

### Task 4: Verificación final

- [ ] Suite completa de tests (`pytest`) en verde.
- [ ] Verificación manual/documentada: guardar una obligación no requiere cerrar un diálogo modal para
      seguir trabajando; los botones destructivos son visualmente distinguibles en toda la app.
