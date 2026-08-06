# Sprint 31 — Sistema de diseño visual: tema, color, tipografía e íconos en la GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** La GUI en vivo de BASTIUM (hoy renderizada con el chrome nativo de Qt/Windows, sin
ninguna identidad visual) adopta un sistema de diseño único y coherente: la paleta burdeos/crema
que hoy solo vive en `app/reports/pdf.py`, la tipografía `AncizarSans` que hoy solo está incluida
en `app/assets/fonts/` sin cargarse nunca, y un set mínimo de íconos SVG hechos a mano
reemplazando los emoji de navegación y los botones de acción más frecuentes (Guardar, Eliminar,
Exportar). Se aplica de forma centralizada (una vez, en `main.py`) a las 8 vistas existentes con
contenido real (`expedientes.py`, `obligaciones.py`, `abonos.py`, `configuracion.py`,
`eventos_laborales.py`, `expediente_detalle.py`, `liquidaciones.py`, `main_window.py`) sin tocar
la disposición de ninguna pantalla (eso es Sprint 32-35) ni construir modo oscuro/claro (fuera de
alcance de este sprint).

**Architecture:** Mecanismo técnico elegido — `.qss` centralizado (`resources/theme.qss`) para
spacing/bordes/estados hover-pressed-disabled, complementado con `QPalette` programática
(`app/core/apariencia.py`) para los colores base nativos de Qt (fondo de ventana, texto, campos,
selección) — tal como recomienda el hallazgo del sprint. Un único punto de entrada,
`aplicar_tema(app: QApplication) -> str`, se llama una sola vez desde `main.py` después de crear
la `QApplication` y antes de instanciar `MainWindow`; registra las 3 fuentes `AncizarSans`
(`app/assets/fonts.py`), aplica la `QPalette` de marca y carga el `.qss`. Los colores de marca
viven en un único módulo Python (`app/core/theme_colors.py`) como fuente de verdad reutilizable
desde código (ej. series de gráficos de matplotlib en el dashboard del Sprint 33) — el `.qss` no
puede importar esas constantes (Qt QSS no soporta variables), así que las repite como literales
hex con un comentario que referencia el módulo para mantenerlos sincronizados a mano.

Para íconos: se descartó cualquier librería de íconos de terceros (Feather/Lucide/Material
Symbols) porque el/la implementador/a no tiene acceso a internet en este sprint y descargar
assets de terceros a mitad de la implementación es poco confiable y un riesgo de licenciamiento.
En su lugar, este plan define 7 SVG de línea simples (viewBox `24x24`, `stroke="currentColor"`,
un puñado de `<path>`/`<line>`/`<circle>`/`<polyline>` cada uno) escritos a mano y completos en
los Steps de la Task 1, cargados vía `QIcon(ruta)`. Se confirmó que `PySide6-Addons` (que incluye
`QtSvg`) ya es una dependencia transitiva instalada de `PySide6` en `requirements.txt` — no hace
falta agregar nada a `requirements.txt`. Se confirmó en este mismo entorno
(`QT_QPA_PLATFORM=offscreen`) que `from PySide6.QtSvg import QSvgRenderer` importa sin error, y
que `QIcon(ruta_svg)` funciona directamente una vez que `PySide6.QtSvg` fue importado en algún
punto del proceso (registra el icon-engine de SVG) — por eso `app/views/icons.py` importa
`PySide6.QtSvg` aunque no use ningún símbolo de ese módulo directamente. Nota honesta sobre
`currentColor`: Qt no cascada un `color` CSS dinámico dentro del render estático de SVG de
`QIcon`/`QSvgRenderer` — sin un atributo `color` explícito en el SVG, `currentColor` resuelve al
valor por defecto del spec de SVG (negro). Los 7 íconos de este sprint renderizan como línea negra
sólida sobre los fondos claros de la paleta (buen contraste); un reteñido dinámico real vía QSS
queda fuera de alcance de este sprint (se anota como posible mejora futura, no bloquea la
Definición de Hecho).

Convención de clase de `QPushButton` (mínima, para que la reutilicen Sprints 32-36): un botón sin
la propiedad dinámica `"class"` es neutral/secundario (estilo por defecto). `boton.setProperty(
"class", "primary")` lo marca como acción principal de la pantalla (fondo burdeos). `boton.
setProperty("class", "destructive")` lo marca como acción irreversible (fondo rojo, distinto del
burdeos de marca para no confundir "acción principal" con "acción peligrosa"). El QSS selecciona
estos casos con `QPushButton[class="primary"]` / `QPushButton[class="destructive"]` — atributo
Qt dinámico, no CSS `class` real. Se asigna siempre en el `__init__` del widget, antes de que se
muestre por primera vez, así que no hace falta `unpolish()`/`polish()` manual (Qt aplica el
stylesheet la primera vez que el widget se pinta).

Riesgo conocido del sprint (selectores QSS demasiado genéricos rompiendo widgets nativos, ej. el
calendario emergente de `QDateEdit`): `resources/theme.qss` NO estiliza `QCalendarWidget` ni
`QToolButton` a propósito (los botones de navegación de mes/año del popup de `QDateEdit` son
`QToolButton`, no `QPushButton`) — quedan con el chrome nativo de Windows deliberadamente. Se deja
como recordatorio explícito en la Task 6 una verificación visual manual de cada pantalla (no
automatizable con `pytest-qt`, que no puede aserciones sobre "se ve bien").

**Tech Stack:** Python 3.14, PySide6 6.11 (`QtGui.QFontDatabase`, `QtGui.QPalette`, `QtSvg`,
`QtWidgets.QApplication`), pytest + pytest-qt (`qtbot`), ruff (line-length 99, `target-version =
"py314"`, reglas `E`/`F`/`I`/`UP`/`B`).

---

### Contexto compartido entre tareas — no repetir en cada una

**Ruta del intérprete de pruebas (todas las tareas):**
`"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe"`.
Si el entorno de ejecución no tiene un display real, anteponer `QT_QPA_PLATFORM=offscreen` a cada
comando `pytest` (ej.: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest ...`).

**Familia de fuente confirmada:** se cargaron los 3 `.ttf` de `app/assets/fonts/` con
`QFontDatabase.addApplicationFont()` en este mismo entorno y los 3 reportan la familia
**`"Ancizar Sans"`** (con espacio) — no `"AncizarSans"` ni `"Ancizar-Sans"`. Todo el código de
este plan usa ese valor literal.

**`QtSvg` ya disponible:** `PySide6-Addons` (que incluye `QtSvg`) es una dependencia transitiva
que ya trae `PySide6` en `requirements.txt` — confirmado con `pip show PySide6` (`Requires:
PySide6_Addons, PySide6_Essentials, shiboken6`) y con una importación directa exitosa de
`PySide6.QtSvg.QSvgRenderer`. No se toca `requirements.txt`.

**No existe ningún botón "Cancelar" hoy:** se confirmó con una búsqueda (`grep -rn "Cancelar\|
QDialogButtonBox" app/views/*.py`) que no hay resultados — todos los diálogos de este proyecto se
cierran con la `X` nativa de la ventana, sin un botón "Cancelar" explícito. `resources/icons/
cancel.svg` se crea igual (es parte del set mínimo pedido por el sprint y lo van a necesitar los
Sprints 32-36 cuando construyan la jerarquía completa de botones), pero **no se conecta a ningún
botón existente en este plan** — queda documentado así, explícitamente, para que no se interprete
como un olvido.

**Las 8 vistas con contenido real** (confirmado con `Glob app/views/*.py`, excluyendo
`concurrency.py` que no tiene UI y `reportes.py`/`about.py`/`dashboard.py` que son placeholders
vacíos documentados para sprints futuros): `abonos.py`, `configuracion.py`, `eventos_laborales.py`,
`expediente_detalle.py`, `expedientes.py`, `liquidaciones.py`, `main_window.py`, `obligaciones.py`.
La paleta/tipografía se aplican a las 8 de una sola vez porque el mecanismo es centralizado
(`app.setPalette()`/`app.setStyleSheet()` en `main.py` alcanza a toda la `QApplication`, no hace
falta tocar cada archivo de vista para eso); los íconos sí requieren tocar cada archivo de vista
puntualmente, porque cada botón es un widget concreto.

---

### Task 1: Íconos SVG hechos a mano + helper `app/views/icons.py`

**Files:**
- Create: `resources/icons/home.svg`, `resources/icons/back.svg`,
  `resources/icons/settings.svg`, `resources/icons/save.svg`, `resources/icons/cancel.svg`,
  `resources/icons/delete.svg`, `resources/icons/export.svg`
- Create: `resources/icon_app.svg`
- Create: `app/views/icons.py`
- Test: `tests/views/test_icons.py`

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/views/test_icons.py`:

```python
import pytest
from PySide6.QtGui import QIcon

from app.views.icons import ICONOS_DISPONIBLES, icon, icono_aplicacion


def test_iconos_disponibles_tiene_exactamente_el_set_minimo_del_sprint_31():
    assert ICONOS_DISPONIBLES == frozenset(
        {"home", "back", "settings", "save", "cancel", "delete", "export"}
    )


@pytest.mark.parametrize("nombre", sorted({"home", "back", "settings", "save", "cancel", "delete", "export"}))
def test_icon_carga_cada_icono_del_set_minimo_sin_estar_vacio(qtbot, nombre):
    resultado = icon(nombre)

    assert isinstance(resultado, QIcon)
    assert not resultado.isNull()


def test_icon_con_nombre_desconocido_lanza_valueerror(qtbot):
    with pytest.raises(ValueError):
        icon("no_existe")


def test_icono_aplicacion_carga_el_icono_de_ventana(qtbot):
    resultado = icono_aplicacion()

    assert isinstance(resultado, QIcon)
    assert not resultado.isNull()
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_icons.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.views.icons'`).

- [ ] **Step 3: Crear los 7 SVG del set mínimo en `resources/icons/`**

`resources/icons/home.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M3 11.5 12 4l9 7.5"/>
  <path d="M5.5 10v9a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1v-9"/>
  <path d="M9.5 20v-6h5v6"/>
</svg>
```

`resources/icons/back.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <line x1="19" y1="12" x2="5" y2="12"/>
  <polyline points="11 6 5 12 11 18"/>
</svg>
```

`resources/icons/settings.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="3.2"/>
  <line x1="12" y1="2.5" x2="12" y2="5.5"/>
  <line x1="12" y1="18.5" x2="12" y2="21.5"/>
  <line x1="2.5" y1="12" x2="5.5" y2="12"/>
  <line x1="18.5" y1="12" x2="21.5" y2="12"/>
  <line x1="5.1" y1="5.1" x2="7.2" y2="7.2"/>
  <line x1="16.8" y1="16.8" x2="18.9" y2="18.9"/>
  <line x1="18.9" y1="5.1" x2="16.8" y2="7.2"/>
  <line x1="7.2" y1="16.8" x2="5.1" y2="18.9"/>
</svg>
```

`resources/icons/save.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M4 4.5A1.5 1.5 0 0 1 5.5 3h11l3.5 3.5v13a1.5 1.5 0 0 1-1.5 1.5H5.5A1.5 1.5 0 0 1 4 19.5z"/>
  <path d="M7.5 3v5.5h8.5V3"/>
  <path d="M7 21v-7h10v7"/>
</svg>
```

`resources/icons/cancel.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="9.5"/>
  <line x1="8.5" y1="8.5" x2="15.5" y2="15.5"/>
  <line x1="15.5" y1="8.5" x2="8.5" y2="15.5"/>
</svg>
```

`resources/icons/delete.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <line x1="4" y1="7" x2="20" y2="7"/>
  <path d="M9 7V4.5A1.5 1.5 0 0 1 10.5 3h3A1.5 1.5 0 0 1 15 4.5V7"/>
  <path d="M6 7l1 13a1.5 1.5 0 0 0 1.5 1.4h7a1.5 1.5 0 0 0 1.5-1.4l1-13"/>
  <line x1="10" y1="11" x2="10" y2="17"/>
  <line x1="14" y1="11" x2="14" y2="17"/>
</svg>
```

`resources/icons/export.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M4 15v4.5A1.5 1.5 0 0 0 5.5 21h13a1.5 1.5 0 0 0 1.5-1.5V15"/>
  <line x1="12" y1="14" x2="12" y2="3"/>
  <polyline points="7.5 7.5 12 3 16.5 7.5"/>
</svg>
```

`resources/icon_app.svg` (roundel de marca, para `MainWindow.setWindowIcon()` — Step de la Task 4):

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <circle cx="32" cy="32" r="30" fill="#AE1C21"/>
  <circle cx="32" cy="32" r="30" fill="none" stroke="#F5F1E9" stroke-width="2"/>
  <text x="32" y="43" font-family="Georgia, 'Times New Roman', serif" font-size="34" font-weight="bold" fill="#F5F1E9" text-anchor="middle">B</text>
</svg>
```

- [ ] **Step 4: Crear `app/views/icons.py`**

```python
from pathlib import Path

from PySide6 import QtSvg  # noqa: F401 - registra el icon engine de SVG en QIcon/QPixmap
from PySide6.QtGui import QIcon

ICONOS_DISPONIBLES = frozenset({"home", "back", "settings", "save", "cancel", "delete", "export"})

_ICONS_DIR = Path(__file__).resolve().parents[2] / "resources" / "icons"
_APP_ICON_PATH = Path(__file__).resolve().parents[2] / "resources" / "icon_app.svg"


def icon(nombre: str) -> QIcon:
    """Carga uno de los iconos de navegacion/accion del set minimo del Sprint 31.

    Nombres validos: "home" (Inicio), "back" (Volver), "settings" (Parametros),
    "save" (Guardar), "cancel" (Cancelar -- provisionado, sin boton "Cancelar"
    existente todavia en el codigo), "delete" (Eliminar), "export" (Exportar).
    Los SVG viven en `resources/icons/<nombre>.svg`.
    """
    if nombre not in ICONOS_DISPONIBLES:
        raise ValueError(
            f"'{nombre}' no es un icono valido. Disponibles: {sorted(ICONOS_DISPONIBLES)}"
        )
    return QIcon(str(_ICONS_DIR / f"{nombre}.svg"))


def icono_aplicacion() -> QIcon:
    """Icono de marca de BASTIUM para `MainWindow.setWindowIcon()` (Sprint 31)."""
    return QIcon(str(_APP_ICON_PATH))
```

- [ ] **Step 5: Correr el test para verificar que pasa**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_icons.py -v`
Expected: 10 passed (1 + 7 parametrizados + 2).

- [ ] **Step 6: Ruff**

Run: `"<python>" -m ruff check app/views/icons.py tests/views/test_icons.py`
Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add resources/icons/home.svg resources/icons/back.svg resources/icons/settings.svg \
  resources/icons/save.svg resources/icons/cancel.svg resources/icons/delete.svg \
  resources/icons/export.svg resources/icon_app.svg app/views/icons.py tests/views/test_icons.py
git commit -m "$(cat <<'EOF'
feat(sprint31): agregar set minimo de iconos SVG y helper icon()/icono_aplicacion()

EOF
)"
```

---

### Task 2: Carga de la tipografía `AncizarSans`

**Files:**
- Create: `app/assets/fonts.py`
- Test: `tests/views/test_fonts.py`

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/views/test_fonts.py`:

```python
from app.assets.fonts import FAMILIA_ANCIZAR_SANS, cargar_fuentes_ancizar_sans


def test_familia_ancizar_sans_es_el_nombre_registrado_por_qt():
    assert FAMILIA_ANCIZAR_SANS == "Ancizar Sans"


def test_cargar_fuentes_ancizar_sans_registra_la_familia_esperada(qtbot):
    familia = cargar_fuentes_ancizar_sans()

    assert familia == FAMILIA_ANCIZAR_SANS


def test_cargar_fuentes_ancizar_sans_es_idempotente(qtbot):
    primera = cargar_fuentes_ancizar_sans()
    segunda = cargar_fuentes_ancizar_sans()

    assert primera == segunda == FAMILIA_ANCIZAR_SANS
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_fonts.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.assets.fonts'`).

- [ ] **Step 3: Crear `app/assets/fonts.py`**

```python
from pathlib import Path

from PySide6.QtGui import QFontDatabase

FAMILIA_ANCIZAR_SANS = "Ancizar Sans"

_FONTS_DIR = Path(__file__).resolve().parent / "fonts"
_ARCHIVOS_ANCIZAR_SANS = (
    "AncizarSans-Regular.ttf",
    "AncizarSans-Medium.ttf",
    "AncizarSans-ExtraBold.ttf",
)


def cargar_fuentes_ancizar_sans() -> str:
    """Registra los 3 pesos de AncizarSans en QFontDatabase (Sprint 31).

    Debe llamarse despues de crear la QApplication (QFontDatabase necesita una
    QApplication/QGuiApplication activa). Devuelve el nombre de familia que Qt
    reporto al leer los metadatos internos de los .ttf -- confirmado como
    "Ancizar Sans" para los 3 archivos al escribir este sprint, pero se
    devuelve el valor real en vez de asumirlo, por si algun peso declarara un
    nombre de familia distinto.
    """
    nombre_familia = None
    for nombre_archivo in _ARCHIVOS_ANCIZAR_SANS:
        ruta = _FONTS_DIR / nombre_archivo
        id_fuente = QFontDatabase.addApplicationFont(str(ruta))
        if id_fuente == -1:
            raise RuntimeError(f"No se pudo cargar la fuente {nombre_archivo} desde {ruta}")
        familias = QFontDatabase.applicationFontFamilies(id_fuente)
        if familias:
            nombre_familia = familias[0]

    if nombre_familia is None:
        raise RuntimeError("No se registro ninguna familia de AncizarSans")
    return nombre_familia
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_fonts.py -v`
Expected: 3 passed.

- [ ] **Step 5: Ruff**

Run: `"<python>" -m ruff check app/assets/fonts.py tests/views/test_fonts.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add app/assets/fonts.py tests/views/test_fonts.py
git commit -m "$(cat <<'EOF'
feat(sprint31): cargar AncizarSans con QFontDatabase.addApplicationFont()

EOF
)"
```

---

### Task 3: Paleta de marca (`app/core/theme_colors.py`) + `resources/theme.qss` + `app/core/apariencia.py` + wiring en `main.py`

**Files:**
- Create: `app/core/theme_colors.py`
- Create: `resources/theme.qss`
- Create: `app/core/apariencia.py`
- Modify: `main.py`
- Test: `tests/core/test_theme_colors.py`, `tests/views/test_apariencia.py`

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/core/test_theme_colors.py`:

```python
import re

from app.core import theme_colors as colores

_HEX = re.compile(r"^#[0-9A-F]{6}$")


def test_todas_las_constantes_de_color_son_hex_de_6_digitos_en_mayusculas():
    valores = [
        v for k, v in vars(colores).items() if k.isupper() and isinstance(v, str)
    ]
    assert len(valores) >= 20
    for valor in valores:
        assert _HEX.match(valor), f"{valor!r} no es un hex #RRGGBB en mayusculas"


def test_primario_y_secundario_coinciden_con_los_colores_ya_usados_en_pdf():
    # app/reports/pdf.py define c_burgundy = "#ae1c21" y c_cream = "#f5f1e9"
    # (Sprint 31 los reutiliza como ancla de marca, en vez de inventar otros).
    assert colores.PRIMARIO == "#AE1C21"
    assert colores.SECUNDARIO == "#F5F1E9"


def test_destructivo_es_distinto_del_primario():
    assert colores.DESTRUCTIVO != colores.PRIMARIO
```

Crear `tests/views/test_apariencia.py`:

```python
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

from app.core import theme_colors as colores
from app.core.apariencia import aplicar_tema, construir_paleta


def test_construir_paleta_usa_los_colores_de_marca(qtbot):
    paleta = construir_paleta()

    assert paleta.color(QPalette.ColorRole.Window).name().upper() == colores.FONDO
    assert paleta.color(QPalette.ColorRole.Highlight).name().upper() == colores.PRIMARIO
    assert paleta.color(QPalette.ColorRole.ButtonText).name().upper() == colores.PRIMARIO


def test_aplicar_tema_registra_la_fuente_y_carga_el_stylesheet(qtbot):
    app = QApplication.instance()

    familia = aplicar_tema(app)

    assert familia == "Ancizar Sans"
    assert app.font().family() == "Ancizar Sans"
    assert "QPushButton" in app.styleSheet()
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/core/test_theme_colors.py tests/views/test_apariencia.py -v`
Expected: FAIL (`ModuleNotFoundError` para `app.core.theme_colors` y `app.core.apariencia`).

- [ ] **Step 3: Crear `app/core/theme_colors.py`**

```python
"""Paleta de color de marca BASTIUM (Sprint 31).

Fuente unica de verdad para los colores en codigo Python (ej. series de un
grafico de matplotlib en el dashboard del Sprint 33). `resources/theme.qss`
usa estos mismos valores hardcodeados en el stylesheet -- Qt QSS no soporta
variables ni importar constantes de Python, asi que si un valor cambia aqui
hay que actualizar tambien el .qss a mano (ver el comentario al inicio de ese
archivo).

PRIMARIO y SECUNDARIO ya se usaban en `app/reports/pdf.py` (`c_burgundy` /
`c_cream`) para las tablas del PDF antes de este sprint; el resto de la
paleta se deriva de esos dos colores de ancla.
"""

PRIMARIO = "#AE1C21"
PRIMARIO_HOVER = "#931116"
PRIMARIO_PRESSED = "#7A0D12"
PRIMARIO_DISABLED = "#D9A8AA"

SECUNDARIO = "#F5F1E9"
SECUNDARIO_HOVER = "#ECE4D4"
SECUNDARIO_PRESSED = "#E0D5BD"
SECUNDARIO_BORDE = "#D8CDBB"

DESTRUCTIVO = "#D32F2F"
DESTRUCTIVO_HOVER = "#B71C1C"
DESTRUCTIVO_PRESSED = "#961515"
DESTRUCTIVO_DISABLED = "#E8B4B0"

EXITO = "#2E7D32"
EXITO_HOVER = "#256628"
ADVERTENCIA = "#ED6C02"
ERROR = DESTRUCTIVO

FONDO = "#FAF8F4"
SUPERFICIE = "#FFFFFF"
SUPERFICIE_ALTERNA = "#F5F1E9"
BORDE = "#D8CDBB"

TEXTO_PRIMARIO = "#2B2320"
TEXTO_SECUNDARIO = "#6B5F57"
TEXTO_SOBRE_PRIMARIO = "#F5F1E9"
TEXTO_DESHABILITADO = "#A69C92"
```

- [ ] **Step 4: Crear `resources/theme.qss`**

```css
/*
 * BASTIUM - Sistema de diseno visual (Sprint 31)
 *
 * Paleta de marca (debe mantenerse sincronizada a mano con
 * app/core/theme_colors.py -- Qt QSS no soporta variables ni importar
 * constantes de Python):
 *
 *   Primario (burdeos):  #AE1C21  hover #931116  pressed #7A0D12  disabled #D9A8AA
 *   Secundario (crema):  #F5F1E9  hover #ECE4D4  pressed #E0D5BD  borde #D8CDBB
 *   Destructivo:         #D32F2F  hover #B71C1C  pressed #961515  disabled #E8B4B0
 *   Fondo / superficie:  #FAF8F4 / #FFFFFF  (superficie alterna #F5F1E9)
 *   Texto:               primario #2B2320  secundario #6B5F57
 *                        sobre-primario #F5F1E9  deshabilitado #A69C92
 *
 * Convencion de clase para QPushButton (Sprint 31, ampliada por Sprint 36):
 *   sin "class"          -> boton secundario/neutral (por defecto)
 *   class="primary"      -> accion principal de la pantalla (Guardar, Liquidar, Exportar)
 *   class="destructive"  -> accion irreversible (Eliminar)
 * Se asigna en Python con `boton.setProperty("class", "primary")` ANTES de
 * mostrar el widget -- Qt aplica el stylesheet la primera vez que el widget
 * se pinta, asi que no hace falta un unpolish()/polish() manual en ese caso.
 *
 * Riesgo conocido (Pendientes.md Sprint 31): selectores demasiado genericos
 * pueden romper widgets nativos que dependen del estilo del SO, como el
 * calendario emergente de QDateEdit. Por eso este archivo NO estiliza
 * QCalendarWidget ni QToolButton (los botones de navegacion de mes/anio del
 * popup de QDateEdit son QToolButton, no QPushButton) -- quedan con el
 * chrome nativo de Windows a proposito.
 */

QWidget {
    background-color: #FAF8F4;
    color: #2B2320;
    font-family: "Ancizar Sans";
    font-size: 10pt;
}

QMainWindow, QDialog {
    background-color: #FAF8F4;
}

QLabel {
    color: #2B2320;
    background: transparent;
}

QToolBar {
    background-color: #F5F1E9;
    border-bottom: 1px solid #D8CDBB;
    padding: 4px;
    spacing: 6px;
}

QGroupBox {
    border: 1px solid #D8CDBB;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
    color: #AE1C21;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}

/* --- Botones --- */

QPushButton {
    background-color: #F5F1E9;
    color: #AE1C21;
    border: 1px solid #AE1C21;
    border-radius: 4px;
    padding: 6px 14px;
}

QPushButton:hover {
    background-color: #ECE4D4;
}

QPushButton:pressed {
    background-color: #E0D5BD;
}

QPushButton:disabled {
    background-color: #F5F1E9;
    color: #A69C92;
    border-color: #D8CDBB;
}

QPushButton[class="primary"] {
    background-color: #AE1C21;
    color: #F5F1E9;
    border: 1px solid #AE1C21;
}

QPushButton[class="primary"]:hover {
    background-color: #931116;
}

QPushButton[class="primary"]:pressed {
    background-color: #7A0D12;
}

QPushButton[class="primary"]:disabled {
    background-color: #D9A8AA;
    color: #F5F1E9;
    border-color: #D9A8AA;
}

QPushButton[class="destructive"] {
    background-color: #D32F2F;
    color: #F5F1E9;
    border: 1px solid #D32F2F;
}

QPushButton[class="destructive"]:hover {
    background-color: #B71C1C;
}

QPushButton[class="destructive"]:pressed {
    background-color: #961515;
}

QPushButton[class="destructive"]:disabled {
    background-color: #E8B4B0;
    color: #F5F1E9;
    border-color: #E8B4B0;
}

/* --- Campos de entrada --- */

QLineEdit, QComboBox, QDateEdit, QSpinBox {
    background-color: #FFFFFF;
    color: #2B2320;
    border: 1px solid #D8CDBB;
    border-radius: 3px;
    padding: 4px 6px;
    selection-background-color: #AE1C21;
    selection-color: #F5F1E9;
}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {
    border: 1px solid #AE1C21;
}

QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled, QSpinBox:disabled {
    background-color: #F5F1E9;
    color: #A69C92;
}

/* --- Tablas (misma identidad de encabezado que los PDF de app/reports/pdf.py) --- */

QTableWidget {
    background-color: #FFFFFF;
    alternate-background-color: #F5F1E9;
    gridline-color: #D8CDBB;
    border: 1px solid #D8CDBB;
}

QTableWidget::item:selected {
    background-color: #AE1C21;
    color: #F5F1E9;
}

QHeaderView::section {
    background-color: #AE1C21;
    color: #F5F1E9;
    padding: 6px;
    border: none;
    border-right: 1px solid #931116;
    font-weight: bold;
}

/* --- Dialogos de progreso/mensaje --- */

QProgressDialog, QMessageBox {
    background-color: #FAF8F4;
}
```

- [ ] **Step 5: Crear `app/core/apariencia.py`**

```python
from pathlib import Path

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

from app.assets.fonts import cargar_fuentes_ancizar_sans
from app.core import theme_colors as colores

_THEME_QSS_PATH = Path(__file__).resolve().parents[2] / "resources" / "theme.qss"


def construir_paleta() -> QPalette:
    """QPalette base de BASTIUM (Sprint 31): fija los colores nativos de Qt
    (fondo de ventana, texto, campos de entrada, seleccion) a partir de
    `app.core.theme_colors`. `resources/theme.qss` se aplica encima para
    spacing/bordes/estados hover-pressed-disabled que QPalette no cubre.
    """
    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor(colores.FONDO))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor(colores.TEXTO_PRIMARIO))
    paleta.setColor(QPalette.ColorRole.Base, QColor(colores.SUPERFICIE))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor(colores.SUPERFICIE_ALTERNA))
    paleta.setColor(QPalette.ColorRole.Text, QColor(colores.TEXTO_PRIMARIO))
    paleta.setColor(QPalette.ColorRole.Button, QColor(colores.SECUNDARIO))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor(colores.PRIMARIO))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor(colores.PRIMARIO))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor(colores.TEXTO_SOBRE_PRIMARIO))
    paleta.setColor(QPalette.ColorRole.PlaceholderText, QColor(colores.TEXTO_SECUNDARIO))
    paleta.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(colores.TEXTO_DESHABILITADO)
    )
    paleta.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor(colores.TEXTO_DESHABILITADO),
    )
    return paleta


def aplicar_tema(app: QApplication) -> str:
    """Aplica el sistema de diseño visual de BASTIUM (Sprint 31) a `app`:
    registra AncizarSans y la fija como fuente por defecto, aplica la
    QPalette de marca y carga `resources/theme.qss` encima. Devuelve el
    nombre de familia de fuente registrado.
    """
    familia = cargar_fuentes_ancizar_sans()
    app.setFont(QFont(familia, 10))
    app.setPalette(construir_paleta())
    app.setStyleSheet(_THEME_QSS_PATH.read_text(encoding="utf-8"))
    return familia
```

- [ ] **Step 6: Correr los tests para verificar que pasan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/core/test_theme_colors.py tests/views/test_apariencia.py -v`
Expected: 6 passed.

- [ ] **Step 7: Wiring en `main.py`**

Cambiar `main.py` completo de:

```python
import sys

from PySide6.QtWidgets import QApplication

from app._version import __version__
from app.views.main_window import MainWindow
from database.database import init_db


def main() -> None:
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("BASTIUM")
    app.setApplicationVersion(__version__)
    window = MainWindow()
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

a:

```python
import sys

from PySide6.QtWidgets import QApplication

from app._version import __version__
from app.core.apariencia import aplicar_tema
from app.views.main_window import MainWindow
from database.database import init_db


def main() -> None:
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("BASTIUM")
    app.setApplicationVersion(__version__)
    aplicar_tema(app)
    window = MainWindow()
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

(no hay test automatizado de `main.py` en este repo — `app/core/apariencia.py::aplicar_tema` ya
está cubierto por `tests/views/test_apariencia.py`; `main.py` solo la invoca).

- [ ] **Step 8: Ruff**

Run: `"<python>" -m ruff check app/core/theme_colors.py app/core/apariencia.py main.py tests/core/test_theme_colors.py tests/views/test_apariencia.py`
Expected: no errors.

- [ ] **Step 9: Commit**

```bash
git add app/core/theme_colors.py resources/theme.qss app/core/apariencia.py main.py \
  tests/core/test_theme_colors.py tests/views/test_apariencia.py
git commit -m "$(cat <<'EOF'
feat(sprint31): definir paleta de marca, theme.qss y aplicarlos desde main.py

EOF
)"
```

---

### Task 4: Ícono de ventana + iconos/clase en la barra de navegación (`app/views/main_window.py`)

**Files:**
- Modify: `app/views/main_window.py`
- Modify: `tests/views/test_main_window.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/views/test_main_window.py`:

```python
def test_ventana_principal_tiene_icono_de_aplicacion(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert not window.windowIcon().isNull()


def test_botones_de_navegacion_tienen_icono(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert not window.boton_volver.icon().isNull()
    assert not window.boton_inicio.icon().isNull()
    assert not window.boton_parametros.icon().isNull()
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_main_window.py -k "icono or icon" -v`
Expected: FAIL (`AttributeError: 'QIcon' object has no attribute 'isNull'` no ocurre; falla porque
`windowIcon()` es el ícono genérico de Qt/null y `boton_*.icon()` está vacío por defecto —
`assert not ...isNull()` da `False` contra `True`).

- [ ] **Step 3: Editar imports de `app/views/main_window.py`**

Cambiar:

```python
from PySide6.QtWidgets import QMainWindow, QPushButton, QStackedWidget, QToolBar

from app.views.configuracion import ParametrosView
from app.views.expediente_detalle import ExpedienteDetallePage
from app.views.expedientes import ExpedientesListView
from app.views.liquidaciones import ResultadoLiquidacionView
```

a:

```python
from PySide6.QtWidgets import QMainWindow, QPushButton, QStackedWidget, QToolBar

from app.views.configuracion import ParametrosView
from app.views.expediente_detalle import ExpedienteDetallePage
from app.views.expedientes import ExpedientesListView
from app.views.icons import icon, icono_aplicacion
from app.views.liquidaciones import ResultadoLiquidacionView
```

- [ ] **Step 4: `setWindowIcon` en `__init__`**

Cambiar:

```python
        super().__init__()
        self.setWindowTitle("BASTIUM - Ecosistema de Liquidacion Forense")

        self.stacked_widget = QStackedWidget()
```

a:

```python
        super().__init__()
        self.setWindowTitle("BASTIUM - Ecosistema de Liquidacion Forense")
        self.setWindowIcon(icono_aplicacion())

        self.stacked_widget = QStackedWidget()
```

- [ ] **Step 5: Íconos en los 3 botones de navegación (reemplazando los emoji)**

Cambiar `_crear_barra_navegacion` completo de:

```python
    def _crear_barra_navegacion(self) -> None:
        barra = QToolBar("Navegacion")
        barra.setMovable(False)

        self.boton_volver = QPushButton("← Volver")
        self.boton_volver.clicked.connect(self._volver)
        barra.addWidget(self.boton_volver)

        self.boton_inicio = QPushButton("\U0001F3E0 Inicio")
        self.boton_inicio.clicked.connect(self._ir_inicio)
        barra.addWidget(self.boton_inicio)

        self.boton_parametros = QPushButton("⚙ Parametros")
        self.boton_parametros.clicked.connect(self._ir_a_parametros)
        barra.addWidget(self.boton_parametros)

        self.addToolBar(barra)
        self._actualizar_botones_navegacion()
```

a:

```python
    def _crear_barra_navegacion(self) -> None:
        barra = QToolBar("Navegacion")
        barra.setMovable(False)

        self.boton_volver = QPushButton(" Volver")
        self.boton_volver.setIcon(icon("back"))
        self.boton_volver.clicked.connect(self._volver)
        barra.addWidget(self.boton_volver)

        self.boton_inicio = QPushButton(" Inicio")
        self.boton_inicio.setIcon(icon("home"))
        self.boton_inicio.clicked.connect(self._ir_inicio)
        barra.addWidget(self.boton_inicio)

        self.boton_parametros = QPushButton(" Parametros")
        self.boton_parametros.setIcon(icon("settings"))
        self.boton_parametros.clicked.connect(self._ir_a_parametros)
        barra.addWidget(self.boton_parametros)

        self.addToolBar(barra)
        self._actualizar_botones_navegacion()
```

(se confirmó con `grep -rn "← Volver\|Inicio\|⚙ Parametros" tests/` que ningún test hace
`assert`s sobre el texto literal de estos botones — el cambio de texto es seguro).

- [ ] **Step 6: Correr los tests para verificar que pasan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_main_window.py -v`
Expected: todos PASS (los ~14 originales + los 2 nuevos).

- [ ] **Step 7: Ruff**

Run: `"<python>" -m ruff check app/views/main_window.py tests/views/test_main_window.py`
Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add app/views/main_window.py tests/views/test_main_window.py
git commit -m "$(cat <<'EOF'
feat(sprint31): icono de ventana y reemplazar emoji de navegacion por iconos SVG

EOF
)"
```

---

### Task 5: Iconos + clase `primary`/`destructive` en botones Guardar/Nuevo/Eliminar/Exportar/Liquidar de las 7 vistas restantes

**Files:**
- Modify: `app/views/expedientes.py`, `app/views/configuracion.py`, `app/views/abonos.py`,
  `app/views/eventos_laborales.py`, `app/views/obligaciones.py`,
  `app/views/expediente_detalle.py`, `app/views/liquidaciones.py`
- Modify: `tests/views/test_expedientes.py`, `tests/views/test_configuracion.py`,
  `tests/views/test_abonos.py`, `tests/views/test_eventos_laborales.py`,
  `tests/views/test_obligaciones.py`, `tests/views/test_expediente_detalle.py`,
  `tests/views/test_liquidaciones.py`

- [ ] **Step 1: Escribir todos los tests que fallan**

Agregar al final de `tests/views/test_expedientes.py`:

```python
def test_boton_guardar_del_formulario_tiene_icono_y_clase_primaria(qtbot):
    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)

    assert not dialog.boton_guardar.icon().isNull()
    assert dialog.boton_guardar.property("class") == "primary"


def test_boton_nuevo_expediente_tiene_clase_primaria(qtbot, monkeypatch):
    from app.views.expedientes import ExpedientesListView

    _sesion_en_memoria(monkeypatch)

    view = ExpedientesListView()
    qtbot.addWidget(view)

    assert view.boton_nuevo.property("class") == "primary"


def test_boton_eliminar_de_cada_fila_tiene_icono_y_clase_destructiva(qtbot, monkeypatch):
    from app.views.expedientes import ExpedientesListView

    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-099",
            demandante="Ana",
            demandado="Luis",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    boton_eliminar = view.tabla.cellWidget(0, 5)
    assert not boton_eliminar.icon().isNull()
    assert boton_eliminar.property("class") == "destructive"
```

(`_sesion_en_memoria`, `session_module`, `Expediente`, `AreaDerecho`, `date` ya están importados
al inicio de `tests/views/test_expedientes.py`).

Agregar al final de `tests/views/test_configuracion.py`:

```python
def test_parametro_form_dialog_boton_guardar_tiene_icono_y_clase_primaria(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)

    assert not dialogo.boton_guardar.icon().isNull()
    assert dialogo.boton_guardar.property("class") == "primary"


def test_parametros_view_boton_agregar_tiene_clase_primaria(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)

    assert vista.boton_agregar.property("class") == "primary"
```

Agregar al final de `tests/views/test_abonos.py`:

```python
def test_boton_guardar_tiene_icono_y_clase_primaria(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)

    assert not dialog.boton_guardar.icon().isNull()
    assert dialog.boton_guardar.property("class") == "primary"
```

Agregar al final de `tests/views/test_eventos_laborales.py` (leer el archivo antes de este step
para confirmar el nombre del helper de fixture existente — sigue el mismo patrón de
`_obligacion_de_prueba` de `tests/views/test_abonos.py`):

```python
def test_boton_guardar_tiene_icono_y_clase_primaria(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)

    assert not dialog.boton_guardar.icon().isNull()
    assert dialog.boton_guardar.property("class") == "primary"
```

Agregar al final de `tests/views/test_obligaciones.py` (usar el helper de fixture existente en
ese archivo para crear un `expediente_id`; seguir el mismo patrón de construcción de
`ObligacionFormDialog(expediente_id=..., area=...)` ya usado en los tests de ese archivo):

```python
def test_boton_guardar_tiene_icono_y_clase_primaria(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)

    assert not dialog.boton_guardar.icon().isNull()
    assert dialog.boton_guardar.property("class") == "primary"
```

(si el helper de fixture de `tests/views/test_obligaciones.py` no se llama
`_expediente_de_prueba`, usar el nombre real que ya exista en ese archivo — confirmar con
`grep -n "^def _" tests/views/test_obligaciones.py` antes de escribir este test).

Agregar al final de `tests/views/test_expediente_detalle.py`:

```python
def test_boton_liquidar_tiene_clase_primaria(qtbot):
    page = ExpedienteDetallePage()
    qtbot.addWidget(page)

    assert page.boton_liquidar.property("class") == "primary"
```

Agregar al final de `tests/views/test_liquidaciones.py`:

```python
def test_botones_exportar_tienen_icono_y_clase_primaria(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    assert not view.boton_exportar_pdf.icon().isNull()
    assert view.boton_exportar_pdf.property("class") == "primary"
    assert not view.boton_exportar_word.icon().isNull()
    assert view.boton_exportar_word.property("class") == "primary"
```

- [ ] **Step 2: Correr todos los tests nuevos para verificar que fallan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_expedientes.py tests/views/test_configuracion.py tests/views/test_abonos.py tests/views/test_eventos_laborales.py tests/views/test_obligaciones.py tests/views/test_expediente_detalle.py tests/views/test_liquidaciones.py -k "icono or icon or clase or primaria or destructiva" -v`
Expected: FAIL (`AttributeError` en `dialogo.boton_guardar`/`vista.boton_agregar`/
`view.boton_nuevo` — todavía son variables locales, no atributos `self.*`; y `property("class")`
devuelve `None` en los que sí son atributos, como `page.boton_liquidar`).

- [ ] **Step 3: Editar `app/views/expedientes.py`**

Imports — cambiar:

```python
import database.session as session_module
from app.core.constants import AREAS_DERECHO
from database.models import AreaDerecho, Expediente
```

a:

```python
import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.views.icons import icon
from database.models import AreaDerecho, Expediente
```

Botón Guardar de `ExpedienteFormDialog` — cambiar:

```python
        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)
```

a:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
```

Y la línea `layout.addRow(boton_guardar)` que sigue, a `layout.addRow(self.boton_guardar)`.

Botón "Nuevo expediente" de `ExpedientesListView` — cambiar:

```python
        boton_nuevo = QPushButton("Nuevo expediente")
        boton_nuevo.clicked.connect(self._abrir_dialogo_nuevo)
```

a:

```python
        self.boton_nuevo = QPushButton("Nuevo expediente")
        self.boton_nuevo.setProperty("class", "primary")
        self.boton_nuevo.clicked.connect(self._abrir_dialogo_nuevo)
```

Y `layout.addWidget(boton_nuevo)` a `layout.addWidget(self.boton_nuevo)`.

Botón Eliminar por fila (dentro de `refrescar`) — cambiar:

```python
            boton_eliminar = QPushButton("Eliminar")
            boton_eliminar.clicked.connect(
                lambda _checked=False, id_=expediente.id: self._eliminar_expediente(id_)
            )
            self.tabla.setCellWidget(fila, 5, boton_eliminar)
```

a:

```python
            boton_eliminar = QPushButton("Eliminar")
            boton_eliminar.setIcon(icon("delete"))
            boton_eliminar.setProperty("class", "destructive")
            boton_eliminar.clicked.connect(
                lambda _checked=False, id_=expediente.id: self._eliminar_expediente(id_)
            )
            self.tabla.setCellWidget(fila, 5, boton_eliminar)
```

- [ ] **Step 4: Editar `app/views/configuracion.py`**

Imports — cambiar:

```python
from app.services.parametro_service import (
    CATALOGO_PARAMETROS,
    ModoResolucion,
    agregar_valor,
    historial,
    valor_vigente_hoy,
)
```

a:

```python
from app.services.parametro_service import (
    CATALOGO_PARAMETROS,
    ModoResolucion,
    agregar_valor,
    historial,
    valor_vigente_hoy,
)
from app.views.icons import icon
```

Botón Guardar de `ParametroFormDialog` — cambiar:

```python
        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)
```

a:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
```

Y `layout.addRow(boton_guardar)` a `layout.addRow(self.boton_guardar)`.

Botón "+ Agregar valor nuevo" de `ParametrosView` — cambiar:

```python
        boton_agregar = QPushButton("+ Agregar valor nuevo")
        boton_agregar.clicked.connect(self._abrir_dialogo_agregar)
```

a:

```python
        self.boton_agregar = QPushButton("+ Agregar valor nuevo")
        self.boton_agregar.setProperty("class", "primary")
        self.boton_agregar.clicked.connect(self._abrir_dialogo_agregar)
```

Y `botones.addWidget(boton_agregar)` a `botones.addWidget(self.boton_agregar)`.

- [ ] **Step 5: Editar `app/views/abonos.py`**

Imports — cambiar:

```python
import database.session as session_module
from database.models import Abono, Obligacion
```

a:

```python
import database.session as session_module
from app.views.icons import icon
from database.models import Abono, Obligacion
```

Botón Guardar — cambiar:

```python
        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)
```

a:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
```

Y `layout.addRow(boton_guardar)` a `layout.addRow(self.boton_guardar)`.

- [ ] **Step 6: Editar `app/views/eventos_laborales.py`**

Imports — cambiar:

```python
import database.session as session_module
from database.models import EventoLaboral, MotivoSuspension, TipoEventoLaboral
```

a:

```python
import database.session as session_module
from app.views.icons import icon
from database.models import EventoLaboral, MotivoSuspension, TipoEventoLaboral
```

Botón Guardar — cambiar:

```python
        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)
```

a:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
```

Y `layout.addRow(boton_guardar)` a `layout.addRow(self.boton_guardar)`.

- [ ] **Step 7: Editar `app/views/obligaciones.py`**

Imports — cambiar:

```python
from app.core.constants import (
    CATEGORIAS_CIVIL_FAMILIA,
    CATEGORIAS_COMERCIAL,
    CATEGORIAS_HONORARIOS,
    CATEGORIAS_LABORAL,
    CATEGORIAS_SANCIONATORIO,
    CATEGORIAS_TRIBUTARIO,
)
from database.models import Expediente, Obligacion, TipoObligacion
```

a:

```python
from app.core.constants import (
    CATEGORIAS_CIVIL_FAMILIA,
    CATEGORIAS_COMERCIAL,
    CATEGORIAS_HONORARIOS,
    CATEGORIAS_LABORAL,
    CATEGORIAS_SANCIONATORIO,
    CATEGORIAS_TRIBUTARIO,
)
from app.views.icons import icon
from database.models import Expediente, Obligacion, TipoObligacion
```

Botón Guardar — cambiar:

```python
        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)
```

a:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
```

Y `self.layout_formulario.addRow(boton_guardar)` a
`self.layout_formulario.addRow(self.boton_guardar)`.

- [ ] **Step 8: Editar `app/views/expediente_detalle.py` (solo clase, sin icono — "liquidar" no
  forma parte del set mínimo de íconos del sprint)**

Cambiar:

```python
        self.boton_liquidar = QPushButton("Liquidar")
        self.boton_liquidar.clicked.connect(self._liquidar)
```

a:

```python
        self.boton_liquidar = QPushButton("Liquidar")
        self.boton_liquidar.setProperty("class", "primary")
        self.boton_liquidar.clicked.connect(self._liquidar)
```

(no requiere import nuevo — no usa `icon()`).

- [ ] **Step 9: Editar `app/views/liquidaciones.py`**

Imports — cambiar:

```python
from app.views.concurrency import TareaEnHilo
from database.models import Expediente
```

a:

```python
from app.views.concurrency import TareaEnHilo
from app.views.icons import icon
from database.models import Expediente
```

Botones Exportar — cambiar:

```python
        self.boton_exportar_pdf = QPushButton("Exportar a PDF")
        self.boton_exportar_pdf.clicked.connect(self._exportar_pdf)
        self.boton_exportar_word = QPushButton("Exportar a Word")
        self.boton_exportar_word.clicked.connect(self._exportar_word)
```

a:

```python
        self.boton_exportar_pdf = QPushButton("Exportar a PDF")
        self.boton_exportar_pdf.setIcon(icon("export"))
        self.boton_exportar_pdf.setProperty("class", "primary")
        self.boton_exportar_pdf.clicked.connect(self._exportar_pdf)
        self.boton_exportar_word = QPushButton("Exportar a Word")
        self.boton_exportar_word.setIcon(icon("export"))
        self.boton_exportar_word.setProperty("class", "primary")
        self.boton_exportar_word.clicked.connect(self._exportar_word)
```

- [ ] **Step 10: Correr todos los tests para verificar que pasan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_expedientes.py tests/views/test_configuracion.py tests/views/test_abonos.py tests/views/test_eventos_laborales.py tests/views/test_obligaciones.py tests/views/test_expediente_detalle.py tests/views/test_liquidaciones.py -v`
Expected: todos PASS (todos los tests originales de esos 7 archivos + los 9 nuevos del Step 1).

- [ ] **Step 11: Ruff**

Run: `"<python>" -m ruff check app/views/expedientes.py app/views/configuracion.py app/views/abonos.py app/views/eventos_laborales.py app/views/obligaciones.py app/views/expediente_detalle.py app/views/liquidaciones.py tests/views/test_expedientes.py tests/views/test_configuracion.py tests/views/test_abonos.py tests/views/test_eventos_laborales.py tests/views/test_obligaciones.py tests/views/test_expediente_detalle.py tests/views/test_liquidaciones.py`
Expected: ninguna línea **nueva o modificada** por este task aparece en la salida (si alguno de
estos archivos ya tenía `E501`/deuda de lint preexistente en líneas que este task no toca —
confirmado que `app/views/expediente_detalle.py` y `app/views/liquidaciones.py` sí la tenían por
el Sprint 26 — no es responsabilidad de este task corregirla).

- [ ] **Step 12: Commit**

```bash
git add app/views/expedientes.py app/views/configuracion.py app/views/abonos.py \
  app/views/eventos_laborales.py app/views/obligaciones.py app/views/expediente_detalle.py \
  app/views/liquidaciones.py tests/views/test_expedientes.py tests/views/test_configuracion.py \
  tests/views/test_abonos.py tests/views/test_eventos_laborales.py \
  tests/views/test_obligaciones.py tests/views/test_expediente_detalle.py \
  tests/views/test_liquidaciones.py
git commit -m "$(cat <<'EOF'
feat(sprint31): aplicar iconos y clase primary/destructive a los botones de accion de las 7 vistas restantes

EOF
)"
```

---

### Task 6: Verificación final y cierre técnico del sprint

**Files:** ninguno nuevo — solo verificación.

- [ ] **Step 1: Correr toda la suite del proyecto**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest -v`
Expected: todos los tests en verde (los ~30 nuevos de este plan repartidos en las 6 tasks, más
todos los existentes, sin cambios de comportamiento funcional en los casos ya cubiertos).

- [ ] **Step 2: Ruff sobre todo el repo**

Run: `"<python>" -m ruff check .`
Expected: el repo puede tener deuda de lint preexistente no relacionada con este sprint (igual
que documentaron los Sprints 26/27/28). Criterio de aceptación: ninguna línea de los archivos
tocados por este plan (`app/views/icons.py`, `app/assets/fonts.py`, `app/core/theme_colors.py`,
`app/core/apariencia.py`, `main.py`, `app/views/main_window.py`, `app/views/expedientes.py`,
`app/views/configuracion.py`, `app/views/abonos.py`, `app/views/eventos_laborales.py`,
`app/views/obligaciones.py`, `app/views/expediente_detalle.py`, `app/views/liquidaciones.py`, y
sus 11 archivos de test) aparece en la salida.

- [ ] **Step 3: Verificación manual (no automatizable) — recordatorio explícito**

Este sprint pide explícitamente recorrer manualmente las 8 pantallas después de aplicar el
stylesheet, por el riesgo documentado de selectores QSS demasiado genéricos rompiendo widgets
nativos (ej. el calendario emergente de `QDateEdit` en los formularios de `obligaciones.py`,
`abonos.py`, `eventos_laborales.py`, `configuracion.py`, `expedientes.py`). `pytest-qt` no puede
aserciones sobre "se ve bien" — este paso requiere una sesión interactiva con `python main.py` y
una ventana real en pantalla. No se ejecuta en este task; se documenta como pendiente explícito
para quien haga la revisión manual antes de fusionar, ejecutando `python main.py` y
verificando: (a) el ícono de la app aparece en la barra de tareas de Windows, (b) los 3 botones
de navegación muestran ícono en vez de emoji, (c) el popup del calendario de cualquier
`QDateEdit` se abre y se ve con el chrome nativo del SO (no roto), (d) las 8 pantallas comparten
la misma paleta y tipografía a simple vista.

- [ ] **Step 4 — NO EJECUTAR: recordatorio explícito**

**No editar `Pendientes.md`** (ni el índice, ni la sección del Sprint 31, ni ningún marcador
`✅ Completado`) — siguiendo el mismo patrón que el Sprint 26: el orquestador humano actualiza ese
archivo centralmente. Este plan termina en el Step 2 de este Task.

**No editar `README.md` ni `docs/GUIA_USUARIO.md`** salvo que, al ejecutar este plan, se
encuentre una captura de pantalla o descripción textual desactualizada por este cambio visual
específico — en ese caso, corregirla con un commit `docs:` separado y angosto, documentando por
qué en el mensaje de commit.

---

## Self-review notes

- **Cobertura del spec:** paleta completa derivada de burdeos/crema con variantes
  hover/pressed/disabled (Task 3, `app/core/theme_colors.py`); mecanismo `.qss` + `QPalette`
  recomendado por el hallazgo (Task 3); las 3 fuentes AncizarSans cargadas con
  `QFontDatabase.addApplicationFont()` (Task 2); ícono de aplicación en `resources/` aplicado con
  `setWindowIcon` (Task 4); set mínimo de íconos SVG hechos a mano reemplazando los emoji de
  navegación y cubriendo Guardar/Eliminar/Exportar (Tasks 1, 4, 5) — Cancelar creado pero no
  wireado por no existir el botón todavía, documentado explícitamente; las 8 vistas con contenido
  real reciben la paleta/tipografía de forma centralizada vía `main.py` (Task 3) y los íconos vista
  por vista donde corresponde (Tasks 4-5); modo oscuro/claro y rediseño de disposición
  explícitamente fuera de alcance, no tocados por ningún task.
- **Sin placeholders:** cada Step trae el SVG/QSS/Python completo a crear, o el
  old_string/new_string exacto a reemplazar — ninguno dice "similar a la Task N" sin el código
  real.
- **Consistencia de tipos:** `icon(nombre: str) -> QIcon` y `icono_aplicacion() -> QIcon` se
  definen una sola vez en Task 1 y se reutilizan verbatim (mismo import
  `from app.views.icons import icon`) en Tasks 4 y 5. La convención de clase
  (`setProperty("class", "primary"/"destructive")`) se define una sola vez en el comentario de
  `resources/theme.qss` (Task 3) y se aplica de forma idéntica en Tasks 4 y 5.
- **Riesgo de QSS genérico:** identificado explícitamente en el Architecture y en el comentario
  de cabecera de `resources/theme.qss` — mitigado no estilizando `QCalendarWidget`/`QToolButton`,
  y con un paso de verificación manual explícito en la Task 6 (no automatizable con `pytest-qt`).

---

## Deliverables for downstream sprints

- **Íconos (`resources/icons/<nombre>.svg`, cargados vía `app.views.icons.icon(nombre: str) ->
  QIcon`):**
  - `home` — Inicio (usado en `main_window.py`, `boton_inicio`)
  - `back` — Volver (usado en `main_window.py`, `boton_volver`)
  - `settings` — Parámetros (usado en `main_window.py`, `boton_parametros`)
  - `save` — Guardar (usado en los 5 diálogos de formulario: `ExpedienteFormDialog`,
    `ParametroFormDialog`, `AbonoFormDialog`, `EventoLaboralFormDialog`, `ObligacionFormDialog`,
    todos vía `self.boton_guardar`)
  - `cancel` — Cancelar (creado, **no conectado a ningún botón todavía** — no existe un botón
    "Cancelar" en el código base a la fecha de este sprint; disponible para cuando Sprint 32-36
    agreguen uno)
  - `delete` — Eliminar (usado en `expedientes.py`, botón por fila `boton_eliminar` de la tabla)
  - `export` — Exportar (usado en `liquidaciones.py`, `boton_exportar_pdf` y
    `boton_exportar_word`)
- **Ícono de aplicación:** `resources/icon_app.svg`, cargado vía
  `app.views.icons.icono_aplicacion() -> QIcon`. Aplicado con `MainWindow.setWindowIcon()` en
  `app/views/main_window.py`.
- **Helper de íconos:** `app/views/icons.py` — `icon(nombre: str) -> QIcon` (lanza `ValueError` si
  `nombre` no está en `ICONOS_DISPONIBLES`) e `icono_aplicacion() -> QIcon`.
  `ICONOS_DISPONIBLES = frozenset({"home", "back", "settings", "save", "cancel", "delete",
  "export"})`.
- **Archivo QSS:** `resources/theme.qss`, aplicado una sola vez en `main.py` vía
  `app.core.apariencia.aplicar_tema(app)` (que también aplica la `QPalette` de marca y registra la
  fuente).
- **Familia de fuente registrada:** `"Ancizar Sans"` (con espacio — constante
  `app.assets.fonts.FAMILIA_ANCIZAR_SANS`). Se registra con
  `app.assets.fonts.cargar_fuentes_ancizar_sans() -> str`.
- **Paleta de color (Python, fuente de verdad):** `app/core/theme_colors.py` — constantes
  `PRIMARIO="#AE1C21"` (+ `_HOVER`/`_PRESSED`/`_DISABLED`), `SECUNDARIO="#F5F1E9"` (+
  `_HOVER`/`_PRESSED`/`_BORDE`), `DESTRUCTIVO="#D32F2F"` (+ `_HOVER`/`_PRESSED`/`_DISABLED`),
  `EXITO="#2E7D32"`, `ADVERTENCIA="#ED6C02"`, `ERROR` (alias de `DESTRUCTIVO`),
  `FONDO="#FAF8F4"`, `SUPERFICIE="#FFFFFF"`, `SUPERFICIE_ALTERNA="#F5F1E9"`, `BORDE="#D8CDBB"`,
  `TEXTO_PRIMARIO="#2B2320"`, `TEXTO_SECUNDARIO="#6B5F57"`, `TEXTO_SOBRE_PRIMARIO="#F5F1E9"`,
  `TEXTO_DESHABILITADO="#A69C92"`. **Nota:** estos mismos valores están hardcodeados como
  literales en `resources/theme.qss` (Qt QSS no soporta variables) — si un valor cambia en un
  sprint futuro, hay que actualizar ambos archivos a mano.
- **Convención de clase QSS para `QPushButton`:** propiedad dinámica `"class"`, asignada con
  `boton.setProperty("class", "primary")` o `boton.setProperty("class", "destructive")` **antes**
  de mostrar el widget. Sin la propiedad = botón neutral/secundario (estilo por defecto). Selectores
  QSS: `QPushButton[class="primary"]`, `QPushButton[class="destructive"]`, `QPushButton` (default).
  Esta convención cubre solo botones a la fecha de este sprint — la jerarquía completa de botones
  (más variantes, tamaños, estados adicionales) es trabajo del Sprint 36.
