# Parámetros: editar/eliminar de usuario, vigencia clara, unidad y tooltips — diseño

## Contexto

Cuatro pedidos del usuario, todos concentrados en `ParametroFormDialog` /
`HistorialParametroDialog` / `ParametrosView` (`app/views/configuracion.py`),
por lo que van en un solo spec/plan/worktree (evita que 4 worktrees separados
se pisen editando el mismo archivo):

1. Cargó parámetros de prueba que "quedaron mal" y no tiene forma de
   corregirlos ni borrarlos — hoy `parametros_legales` es estrictamente
   append-only, sin editar ni eliminar en ningún punto de la UI.
2. Quiere que esa edición/eliminación solo aplique a lo que él mismo cargó,
   no a los valores de sistema/semilla — hoy no existe ningún flag real que
   distinga ambos; el campo `usuario` es texto libre.
3. Al agregar un parámetro nuevo, no se le pide "vigente hasta" — el campo
   está oculto salvo que el modo de resolución de la clave sea
   `TRAMO_CERRADO` (`ModoResolucion`, `app/services/parametro_service.py`).
   Investigación confirma que esto es una regla de negocio real (`agregar_valor`
   línea 518 rechaza `vigente_hasta` fuera de `TRAMO_CERRADO`), no un bug de
   UI — se resuelve aclarando la interfaz, no cambiando el motor de cálculo
   (decisión tomada con el usuario: el riesgo de tocar la resolución de
   parámetros en modo `ABIERTO`/`ANUAL_EXACTO` no se justifica para este pedido).
4. El campo "Unidad" es un `QLineEdit` libre; quiere un desplegable con las
   unidades ya usadas más una opción "Otros" que revele un campo de texto.
5. Solo "Unidad" tiene el ícono ⓘ visual (vía el helper `agregar_ayuda`,
   `app/views/form_utils.py`) — el resto de campos tiene `.setToolTip()` pero
   sin el ícono, y las columnas de `ParametrosView.tabla` no tienen tooltip
   alguno.

## Objetivo

- Distinguir de verdad parámetros creados por el sistema (semilla/migración)
  de los creados por un usuario desde la UI.
- Permitir editar y eliminar valores individuales de parámetro, solo para los
  creados por usuario.
- Que el formulario de agregar parámetro explique con claridad cuándo aplica
  "vigente hasta" y cuándo no, en vez de ocultar el campo sin explicación.
- Que "Unidad" sea un desplegable con las unidades existentes + "Otros".
- Que todos los campos del formulario y todas las columnas de la tabla
  resumen tengan tooltip ⓘ visible.

## Diseño

### 1. `creado_por_sistema` — distinción real sistema/usuario

Migración nueva: columna `creado_por_sistema: bool NOT NULL DEFAULT false`
en `parametros_legales` (`database/models.py::ParametroLegal`). Backfill en
la propia migración: `UPDATE parametros_legales SET creado_por_sistema = true
WHERE usuario = 'sistema'` (mismo criterio ya usado consistentemente por
`scripts/migrate_parametros_legales.py` y `scripts/migrate_ipc_variacion_anual.py`,
ambos con `USUARIO_MIGRACION = "sistema"`).

Ambos scripts de migración/siembra se actualizan para pasar
`creado_por_sistema=True` explícitamente al crear filas, en vez de depender
del valor de `usuario` para inferirlo después.

`agregar_valor()` (`parametro_service.py`), el único punto de escritura que
usa la UI (`ParametroFormDialog.guardar()`), sigue creando filas con
`creado_por_sistema=False` siempre — el campo "Usuario" del formulario sigue
siendo texto libre de auditoría (quién lo cargó), pero ya no determina el
flag. Ningún camino de la UI puede crear una fila con `creado_por_sistema=True`.

### 2. Editar/eliminar en `HistorialParametroDialog`

Este diálogo (no `ParametrosView.tabla`, que es un resumen de "1 fila por
clave") es donde vive cada valor histórico individual — cada fila de su
`QTableWidget` es una fila real de `parametros_legales`. Se agregan 2
columnas nuevas, "Editar" y "Eliminar", mismo patrón ya usado en
`expediente_detalle.py` para obligaciones/abonos/eventos (Sprint 44/60):
`QPushButton` por celda vía `setCellWidget`, conectado por `id` de fila con
`lambda _checked=False, id_=fila.id: ...`.

- Para filas con `creado_por_sistema=True`: ambas celdas quedan vacías (sin
  botón) — no editable, no eliminable, sin necesidad de deshabilitar nada
  porque el botón simplemente no existe en esa fila.
- **Editar:** abre `ParametroFormDialog` en modo edición (nuevo parámetro
  opcional `parametro_id: int | None` en el constructor, mismo patrón que
  `abono_id` en `AbonoFormDialog`, Sprint 60), precargado con los valores
  actuales de esa fila. Editable: Valor, Vigente desde, Vigente hasta,
  Área(s) del derecho, Unidad, Usuario, Motivo. **No editable:** el
  "Parámetro" (clave) — el combo se muestra deshabilitado/fijo en modo
  edición, porque cambiarlo equivaldría a borrar una fila y crear otra de
  una clave distinta. Guardar en modo edición hace `UPDATE` sobre la fila
  existente (mismo patrón `guardar_o_actualizar` de `form_utils.py` que ya
  usan Obligación/Abono), no un `INSERT` nuevo.
- **Eliminar:** `QMessageBox.question` con texto
  "¿Eliminar este valor de parámetro? Esta acción no se puede deshacer.",
  igual formato que los diálogos de confirmación ya existentes. Sin papelera,
  eliminación definitiva tras confirmar (mismo criterio que Sprint 60).
- Tras editar o eliminar, se refresca tanto la tabla del propio
  `HistorialParametroDialog` como `ParametrosView.tabla` (que muestra "valor
  vigente hoy" y podría cambiar si la fila editada/eliminada era la vigente)
  — mismo cuidado que el hotfix del Sprint 60 sobre tablas relacionadas
  desactualizadas.

### 3. "Vigente hasta" — aclaración de UI, sin tocar el motor de cálculo

Se mantiene sin cambios la regla de negocio (`vigente_hasta` solo se
persiste de verdad en modo `TRAMO_CERRADO`). Cambios solo visuales en
`ParametroFormDialog`:

- Cuando el modo de la clave elegida es `ABIERTO` o `ANUAL_EXACTO`, en vez de
  ocultar la fila completa con `set_row_visible(..., False)`, se muestra
  **deshabilitada** con una `QLabel` explicativa debajo:
  "Este parámetro no vence en una fecha fija (modo {texto legible del modo})
  — el valor rige indefinidamente hasta que se cargue uno nuevo con una
  fecha 'Vigente desde' posterior."
- Cuando el modo es `TRAMO_CERRADO`, se agrega un `QCheckBox` "Indefinido"
  junto al `QDateEdit` de "Vigente hasta" — pero como este modo siempre
  exige un `vigente_hasta` real (regla ya validada en `agregar_valor`), ese
  checkbox aparece deshabilitado con una nota corta ("Este parámetro
  requiere una fecha de fin — no puede quedar indefinido"), para que las
  3 combinaciones de modo se vean con un mismo patrón visual consistente
  (campo + nota explicativa) en vez de que uno tenga UI distinta a los
  otros dos.
- `guardar()` no cambia su lógica de negocio — sigue mandando
  `vigente_hasta=None` salvo en `TRAMO_CERRADO`, ahora con el usuario
  entendiendo por qué antes de intentar guardar.

### 4. "Unidad" como desplegable

`self.campo_unidad` pasa de `QLineEdit` a `QComboBox` editable=False, con
7 ítems: las 6 unidades ya usadas en `AREA_UNIDAD_POR_CLAVE`
(`app/services/areas_parametro.py`) — `%`, `COP`, `meses`, `índice`,
`veces`, `puntos` — más `"Otros..."` al final. Al seleccionar `"Otros..."`
aparece una fila nueva con `QLineEdit` (vía `set_row_visible`, mismo patrón
que "Vigente hasta") para escribir la unidad manualmente; para cualquier
otra selección esa fila permanece oculta.

`_actualizar_area_unidad_sugeridas()` sigue preseleccionando automáticamente
según `AREA_UNIDAD_POR_CLAVE[clave]`, ahora buscando el índice del combo que
coincide con la unidad sugerida (siempre existe hoy, las 6 unidades del
catálogo son un subconjunto exacto de las 6 del combo) en vez de
`setText(...)`.

`guardar()` usa el texto del `QLineEdit` de "Otros" cuando el combo tiene
`"Otros..."` seleccionado; si no, usa el texto del ítem del combo
seleccionado.

### 5. Tooltips ⓘ homologados

Todos los campos de `ParametroFormDialog` (Parámetro, Valor, Vigente desde,
Vigente hasta, Área(s) del derecho, Unidad, Usuario, Motivo) pasan a
agregarse con `agregar_ayuda(...)` en vez de `addRow(str, widget)` +
`.setToolTip()` suelto — reusando el texto de tooltip que cada campo ya
tiene hoy, sin inventar contenido nuevo. El campo "Unidad" (ya usa
`agregar_ayuda`) mantiene su tooltip, actualizado para reflejar que ahora es
un desplegable ("Unidad de medida del valor, sugerida automáticamente según
la clave elegida; elija 'Otros...' para escribir una unidad distinta.").

En `ParametrosView.tabla`, cada encabezado de columna (Categoría, Parámetro,
Valor vigente hoy, Vigente desde, Vigente hasta, Área, Unidad) recibe
tooltip vía `self.tabla.horizontalHeaderItem(i).setToolTip(...)` — sin ícono
ⓘ (un `QTableWidget` no soporta widgets custom por columna de encabezado sin
una reescritura mayor a `QHeaderView` personalizado, fuera de alcance), pero
descubrible al pasar el mouse, igual que ya funciona hoy para las celdas de
datos con texto largo truncado.

## Fuera de alcance

- No se re-habilita "Vigente hasta" para modos `ABIERTO`/`ANUAL_EXACTO` a
  nivel de motor de cálculo — decisión explícita, ver Contexto punto 3.
- No se permite editar la clave (Parámetro) de una fila existente.
- No se agrega edición/eliminación a filas `creado_por_sistema=True` bajo
  ninguna circunstancia, ni siquiera con una confirmación extra — quedan
  completamente protegidas por diseño.
- No se toca `ParametrosView.tabla` (la vista resumen "1 fila por clave")
  más allá de agregarle tooltips a los encabezados y refrescarla tras
  editar/eliminar — su lógica de "valor vigente hoy" no cambia.
- No se re-implementa `QHeaderView` para poner íconos ⓘ reales en los
  encabezados de columna — solo tooltip de texto.
