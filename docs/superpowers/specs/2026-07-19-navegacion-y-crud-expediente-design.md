# Diseño: Navegación (Volver/Inicio) y CRUD completo de Expediente

Fecha: 2026-07-19

## Contexto

BASTIUM es una app de escritorio en PySide6 (Qt) con SQLAlchemy. `MainWindow`
aloja un `QStackedWidget` con 3 páginas (`expedientes` → `detalle` →
`resultado`) navegadas mediante callbacks pasados a los constructores de las
vistas. Hoy no existe forma de volver a una pantalla anterior ni de regresar
al inicio: `show_page()` simplemente reemplaza el widget central sin llevar
historial.

Por otro lado, `Expediente` (la entidad caso/expediente) solo tiene Crear y
Leer implementados. No existe ninguna forma de editar ni eliminar un
expediente, ni en la UI ni en la capa de datos. El modelo ya tiene
`cascade="all, delete-orphan"` configurado en sus relaciones con
`Obligacion` y `AuditLog`, así que un `session.delete()` sobre un
`Expediente` ya borraría correctamente sus datos asociados.

Este documento cubre dos features relacionadas pero independientes:

1. Botones de navegación **Volver** y **Inicio**.
2. Botones de **Editar** y **Eliminar** por fila en la lista de expedientes.

## 1. Navegación: Volver / Inicio

### Componentes

- `app/views/main_window.py` — se modifica `MainWindow`.

### Diseño

Se agrega una `QToolBar` fija en la parte superior de la ventana (mecanismo
nativo de `QMainWindow`, vía `self.addToolBar(...)`), con dos botones de
texto (sin iconos gráficos — la app no usa assets de íconos en ningún otro
lugar):

- **"← Volver"**
- **"🏠 Inicio"**

`MainWindow` mantiene una pila de historial de nombres de página:

```python
self._history: list[str] = []
self._current_page_name: str = "expedientes"
```

`show_page` se extiende con un parámetro `add_to_history`:

- Al navegar hacia adelante (`_abrir_detalle`, `_mostrar_resultado`), se
  llama con `add_to_history=True` (comportamiento por defecto): empuja el
  nombre de la página actual a `self._history` antes de cambiar de widget.
- **Volver** (`_volver`): si `self._history` no está vacío, hace `pop()` y
  navega a esa página con `add_to_history=False` (para no volver a apilar y
  evitar bucles).
- **Inicio** (`_ir_inicio`): vacía `self._history` por completo y navega a
  `"expedientes"` con `add_to_history=False`.

Después de cada navegación se llama `_actualizar_botones_nav()`, que oculta
(`setVisible(False)`) — no deshabilita — cada botón cuando no aplica:

- **"🏠 Inicio"** se oculta cuando la página actual ya es `"expedientes"`.
- **"← Volver"** se oculta cuando `self._history` está vacío.

Como `detalle_page` y `resultado_page` son widgets persistentes (no se
recrean en cada navegación), volver a ellos conserva el estado ya cargado
(ej. el expediente abierto en detalle).

### Casos de uso verificados

- `expedientes` → `detalle(A)` → Volver → vuelve a `expedientes` (pila vacía
  de nuevo, ambos botones ocultos).
- `expedientes` → `detalle(A)` → `resultado` → Volver → vuelve a `detalle(A)`
  con el expediente A todavía cargado → Volver otra vez → vuelve a
  `expedientes`.
- Desde cualquier página profunda, Inicio siempre limpia la pila y regresa
  directo a `expedientes`.

## 2. Editar y Eliminar expediente

### Componentes

- `app/views/expedientes.py` — se modifica `NuevoExpedienteDialog` y
  `ExpedientesListView`.

### Tabla de expedientes

`ExpedientesListView.tabla` pasa de 4 a 6 columnas:

```
Radicado | Demandante | Demandado | Área | Editar | Eliminar
```

Las columnas "Editar" y "Eliminar" no muestran texto de dato: cada celda
aloja un `QPushButton` ("✏️ Editar" / "🗑️ Eliminar") vía
`self.tabla.setCellWidget(fila, col, boton)`, siguiendo el mismo mapeo
`self._expediente_ids_por_fila[fila]` que ya usa `_abrir_seleccionado` para
el doble clic. El doble clic en la fila sigue abriendo el detalle sin
cambios.

Cada botón se conecta capturando la fila correctamente en el momento de
creación (evitando el problema de captura tardía de `fila` en el closure de
Python, p. ej. con un default arg `fila=fila` en el lambda o
`functools.partial`).

### Editar (reutiliza el diálogo existente)

`NuevoExpedienteDialog` se generaliza para aceptar un `Expediente` opcional:

```python
class ExpedienteFormDialog(QDialog):
    def __init__(self, parent=None, expediente: Expediente | None = None):
        ...
```

- Si `expediente` es `None`: comportamiento actual sin cambios (título
  "Nuevo expediente", campos vacíos, `guardar()` crea un registro nuevo).
- Si se pasa un `expediente`: título "Editar expediente", los campos
  (`radicado`, `demandante`, `demandado`, `area_derecho`, `juzgado`,
  `fecha_corte_default`) se pre-llenan con los valores actuales del objeto.
  Todos los campos son editables, incluido el radicado. Al guardar, en vez
  de `session.add(...)`, se hace `session.get(Expediente, expediente.id)`,
  se reasignan los campos desde el formulario y se llama `session.commit()`.

El nombre de clase se actualiza de `NuevoExpedienteDialog` a
`ExpedienteFormDialog` en su único punto de uso actual
(`_abrir_dialogo_nuevo`) y en el nuevo `_editar_expediente`. Ambos flujos
siguen el patrón ya existente: `dialogo.exec()` → si acepta,
`self.refrescar()`.

### Eliminar (confirmación reforzada)

Handler `_eliminar_expediente(expediente_id)`:

1. `QMessageBox.question` (Sí/No) advirtiendo que se eliminará el expediente
   **junto con todas sus obligaciones, abonos y registros de auditoría
   asociados**, de forma permanente. Si el usuario responde "No", se aborta.
2. Si confirma, se pide reforzar la confirmación: `QInputDialog.getText`
   solicitando escribir el número de radicado exacto del expediente a
   eliminar. Se compara (case-sensitive, sin espacios extra) contra el
   radicado real:
   - Si no coincide (o cancela), se muestra `QMessageBox.warning` y se
     aborta sin borrar nada.
   - Si coincide, se procede a eliminar.
3. Eliminación: `session.delete(expediente); session.commit()`. La cascada
   ya configurada en `database/models.py`
   (`cascade="all, delete-orphan"` en las relaciones `obligaciones` y
   `audit_logs`) se encarga de borrar los registros asociados.
4. Se llama `self.refrescar()` para reflejar la tabla actualizada.

No se introduce una capa de repositorio/servicio nueva: se sigue el patrón
ya existente en el archivo (lógica de base de datos inline dentro de la
vista, vía `session_module.get_session()`), igual que hoy hacen Crear y
Leer.

## Fuera de alcance

- No se agregan botones Editar/Eliminar en `ExpedienteDetallePage` (el
  usuario pidió explícitamente que vivan solo por fila en la lista).
- No se toca la lógica de `liquidaciones.py`, `obligaciones.py` ni
  `abonos.py`.
- No se introduce un sistema de "deshacer" eliminación; es una operación
  permanente respaldada solo por la confirmación reforzada.
