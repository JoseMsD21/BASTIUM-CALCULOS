# Configuraciones + Apariencia — diseño

## Contexto

Hoy el botón lateral "Parametros" (`boton_parametros`, ícono de engranaje, en
`app/views/main_window.py`) navega directo a `ParametrosView`
(`app/views/configuracion.py`), una pantalla plana: tabla de parámetros
legales + botón "Agregar valor nuevo" + un `QCheckBox` "Modo oscuro" metido en
la misma barra de botones.

El propio código ya señalaba (comentario Sprint 50, `configuracion.py` líneas
368-373) que el checkbox de tema vivía ahí de forma temporal, a la espera de
que el sidebar se reorganizara. Esta spec ejecuta esa reorganización.

## Objetivo

1. Renombrar el punto de entrada del sidebar de "Parametros" a
   "Configuraciones".
2. Convertir esa pantalla en un contenedor con sub-navegación (submenú lateral
   estilo Ajustes) que hoy aloja dos secciones — "Parámetros" y "Apariencia" —
   y que puede crecer con más secciones en el futuro sin rediseño.
3. Mover el interruptor de modo oscuro/claro a la nueva sección "Apariencia",
   sacándolo de la tabla de parámetros legales.

## Diseño

### 1. Botón del sidebar

`boton_parametros` (`app/views/main_window.py`, líneas 136-139) cambia su
texto de `" Parametros"` a `" Configuraciones"`. Mismo ícono (`icon("settings")`),
misma posición en el sidebar, mismo wiring de click (solo cambia a dónde
navega). Al hacer clic, siempre entra mostrando la sub-sección "Parámetros"
por defecto — igual que el comportamiento actual de `_ir_a_parametros`, para
no romper el flujo existente de quien ya usa esa pantalla a diario.

### 2. `ConfiguracionesView` (nueva vista compuesta)

Nuevo archivo `app/views/configuraciones.py` con una clase
`ConfiguracionesView(QWidget)`:

- **Submenú lateral** (columna angosta, izquierda): lista vertical de
  secciones — "Parámetros", "Apariencia", con espacio visual para agregar
  más entradas después. Sigue el mismo patrón visual de estado
  activo/inactivo que ya usa el sidebar principal (`class="primary"` /
  `"secondary"` + `unpolish()/polish()`).
- **Panel de contenido** (derecha): un `QStackedWidget` interno que alterna
  entre la `ParametrosView` existente y la nueva `AparienciaView`, según la
  sección seleccionada en el submenú. Este stack es independiente del
  `QStackedWidget` de nivel superior que ya tiene `MainWindow`.
- Cambiar de sección dentro de Configuraciones es estado puramente interno
  de `ConfiguracionesView` — no empuja nada al `self._history` de
  `MainWindow` ni interactúa con el botón "Volver". "Volver" sigue operando
  solo sobre las pantallas de nivel superior (dashboard, expedientes,
  detalle, resultado, configuraciones).

### 3. `ParametrosView` (reutilizada, no reescrita)

Se mantiene la clase `ParametrosView` en `app/views/configuracion.py` con su
tabla y diálogos (`ParametroFormDialog`, `HistorialParametroDialog`) intactos.
Único cambio: se elimina el `QCheckBox` "Modo oscuro" y su método
`_alternar_modo_tema` de esta clase (líneas 368-381, 390-396) — esa
responsabilidad se muda a `AparienciaView`.

`ConfiguracionesView` sigue llamando a `parametros_page.refrescar()` cada vez
que la sección "Parámetros" se vuelve visible (al entrar por primera vez y
cada vez que el usuario la selecciona de nuevo en el submenú), preservando la
garantía de datos frescos que existe hoy.

### 4. `AparienciaView` (nueva)

Vive también en `app/views/configuraciones.py` (o un archivo separado si
crece). Contiene:

- El `QCheckBox` "Modo oscuro" movido literal desde `ParametrosView`, con la
  misma lógica de `_alternar_modo_tema` reapuntada a las mismas funciones de
  `app/core/apariencia.py` (`aplicar_tema`, `guardar_modo_tema`) — sin
  cambios de comportamiento, solo de ubicación.
- Un texto breve debajo explicando qué controla el interruptor (deja espacio
  natural para agregar más ajustes de apariencia después, sin necesitar otro
  rediseño).

### 5. Breadcrumb

`_texto_breadcrumb()` en `main_window.py` sigue el patrón `›` que ya usan
Expedientes/Detalle/Resultado:

- Sección Parámetros → `"Configuraciones › Parámetros"`
- Sección Apariencia → `"Configuraciones › Apariencia"`

`MainWindow` necesita saber qué sub-sección está activa dentro de
`ConfiguracionesView` para armar este texto (expone la sección actual, p.ej.
vía una señal o un getter simple).

### 6. Renombrados de código (para consistencia, no solo cosmética)

- Clave del diccionario `self._pages`: `"parametros"` → `"configuraciones"`.
- `self.parametros_page` → `self.configuraciones_page` (instancia de
  `ConfiguracionesView`, que internamente crea/posee la `ParametrosView`).
- `_ir_a_parametros()` → `_ir_a_configuraciones()`.
- Los tests existentes que dependen de los nombres de atributo
  (`tests/views/test_main_window.py`, ver comentario en
  `_crear_barra_navegacion`) se actualizan como parte de esta misma tarea —
  no se preservan nombres viejos por compatibilidad.

## Fuera de alcance

- No se agregan más opciones de apariencia (tamaño de fuente, densidad,
  acentos de color, etc.) — solo se traslada el interruptor existente.
- No se agregan más secciones al submenú de Configuraciones más allá de
  Parámetros y Apariencia; solo se deja el patrón preparado para que sea
  fácil sumar una después.
- No cambia la lógica de negocio de `ParametrosView` (tabla, diálogos,
  historial) ni la de `app/core/apariencia.py` — es una relocalización de UI,
  no una reescritura funcional.
