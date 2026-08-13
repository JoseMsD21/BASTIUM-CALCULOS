# Checkbox con indicador invisible (claro y oscuro) — diseño

## Contexto

El usuario reportó que en "Agregar obligación" (`ObligacionFormDialog`) no
puede ver el recuadro de las casillas "Demanda judicial (habilita anatocismo,
Art. 886 C.Co.)" ni "¿Hay acuerdo posterior de capitalización?" — solo el
texto de la etiqueta, sin ningún indicador visual de marcado/desmarcado.
También reportó el mismo problema en modo oscuro para la vista de Parámetros.

Investigación confirmó la causa raíz: **ni `resources/theme.qss` (claro) ni
`resources/theme_dark.qss` (oscuro) tienen una sola regla `QCheckBox`** (0
resultados al buscar `CheckBox`/`indicator` en ambos archivos). Sin un
`QCheckBox::indicator` explícito, Qt recurre al indicador nativo del estilo
Fusion, que renderiza casi invisible contra la paleta custom de fondo/bordes
de la app — no es un problema de un color puntual mal elegido, es que nunca
se definió ningún estilo para este control.

Esto afecta a **todos** los `QCheckBox` de la aplicación, no solo a los dos
que el usuario notó. Grep de `QCheckBox(` en `app/views/` da 4 archivos:

- `app/views/obligaciones.py` — 8 casillas (`ObligacionFormDialog`): demanda
  judicial (línea 179), acuerdo de capitalización (186), indexación IPC
  (255), interés sobre capital indexado (262), sanción agravada (283),
  es_smmlv (324), pagada (329), incluir seguridad social (340).
- `app/views/configuracion.py` — casillas de área del derecho en
  `ParametroFormDialog` (línea 126, una por `AREAS_DERECHO`).
- `app/views/apariencia.py` — "Modo oscuro" (línea 20).
- `app/views/descuentos_laborales.py` — "Descuento legal (autorizado)"
  (línea 39).

Ninguno de estos widgets tiene `.setStyleSheet(...)` propio — todos dependen
100% del QSS global, así que el fix es un cambio centralizado en los 2
archivos de tema, sin tocar ningún `.py`.

## Objetivo

Que el indicador (el recuadro) de cualquier `QCheckBox` de la app sea
claramente visible, tanto sin marcar como marcado, en modo claro y en modo
oscuro, usando exclusivamente colores ya presentes en la paleta documentada
de cada tema (sin introducir tonos nuevos).

## Diseño

Agregar un bloque `QCheckBox::indicator` a `resources/theme.qss` y otro
equivalente a `resources/theme_dark.qss`, cerca de las reglas existentes de
`QPushButton`/`QLineEdit` (mismo estilo de organización que ya usa el
archivo). Tamaño de indicador: 18×18px con esquinas ligeramente redondeadas
(2px), consistente con el resto de bordes redondeados que ya usa la hoja de
estilos.

### Modo claro (`resources/theme.qss`)

Usa la paleta documentada en el encabezado del archivo (líneas 8-13):

| Estado | Borde | Fondo | Marca/check |
|---|---|---|---|
| Sin marcar | `#D8CDBB` (borde estándar) | `#FFFFFF` | — |
| Sin marcar + hover | `#AE1C21` (primario) | `#FFFFFF` | — |
| Marcado | `#AE1C21` | `#AE1C21` | `#F5F1E9` (check) |
| Marcado + hover | `#931116` (hover primario) | `#931116` | `#F5F1E9` |
| Deshabilitado (marcado o no) | `#D8CDBB` | `#F5F1E9` | `#A69C92` si marcado |

### Modo oscuro (`resources/theme_dark.qss`)

Usa la paleta documentada en el encabezado del archivo (líneas 10-15), mismo
esquema estructural que el claro:

| Estado | Borde | Fondo | Marca/check |
|---|---|---|---|
| Sin marcar | `#4A4039` (borde) | `#2A2422` (superficie) | — |
| Sin marcar + hover | `#D9484D` (primario claro) | `#2A2422` | — |
| Marcado | `#D9484D` | `#D9484D` | `#F5F1E9` (check) |
| Marcado + hover | `#C93338` (hover primario) | `#C93338` | `#F5F1E9` |
| Deshabilitado (marcado o no) | `#4A4039` | `#332C29` | `#6B5F57` si marcado |

El "check" (marca de verificación) se logra con `image:` apuntando a un
recurso SVG simple de check en el color indicado, o con
`background-color` + un carácter/ícono si el proyecto ya tiene un patrón
para esto (`app/views/icons.py` — revisar si ya expone un ícono de check
reutilizable antes de crear un asset nuevo).

## Fuera de alcance

- No cambia el tamaño de fuente, el texto ni el layout de ningún formulario
  que usa `QCheckBox` — solo el indicador.
- No se agrega estilo a otros controles (radio buttons, etc.) — no existen
  en la app hoy (grep de `QRadioButton` sin resultados).
- No se toca `app/core/theme_colors_dark.py` ni la lógica de aplicar/guardar
  tema (`app/core/apariencia.py`) — es un cambio puramente de hoja de
  estilos.
