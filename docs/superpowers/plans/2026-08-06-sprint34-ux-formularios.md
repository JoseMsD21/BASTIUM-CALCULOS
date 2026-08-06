# Sprint 34 — UX de formularios: agrupación, ayuda contextual y feedback en tiempo real Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `ObligacionFormDialog` (`app/views/obligaciones.py`) deja de mostrar sus ~15 campos como una
lista plana en un único `QFormLayout`: se reorganiza en 3 secciones colapsables ("Datos básicos",
"Tasas e intereses", "Honorarios y costas"), gana tooltips en español explicando el significado legal
de los campos técnicos, feedback visual en tiempo real (borde rojo + ícono de advertencia) reutilizando
las validaciones ya existentes del Sprint 24, y un ícono informativo junto al campo de tasa que explica
de dónde sale su valor por defecto (Art. 1617 C.C.). `ExpedienteFormDialog`
(`app/views/expedientes.py`) recibe el mismo tratamiento a menor escala: tooltips en sus 6 campos y
validación en tiempo real del radicado (único campo obligatorio).

**Architecture:** Sin catálogo ni motor de validación nuevo — se reutilizan verbatim los 3 helpers ya
existentes de `ObligacionFormDialog` (`_validar_concepto_no_vacio`, `_validar_rango`,
`_validar_fecha_no_posterior_a_corte`, agregados por el Sprint 24) y la validación de radicado ya
existente en `ExpedienteFormDialog.guardar()`. Se agregan wrappers delgados por campo
(`_validar_concepto_en_tiempo_real`, `_validar_valor_en_tiempo_real`, `_validar_tasa_en_tiempo_real`)
que capturan el mismo `ValueError` que hoy solo se ve al guardar y lo traducen a un estado visual por
campo (`QLineEdit.setProperty("class", "invalid")`, siguiendo la misma convención de propiedad
dinámica de Qt que el Sprint 31 introdujo para `QPushButton`), conectados a `textChanged`. La
reorganización usa 3 `QGroupBox` marcables (`setCheckable(True)`) en vez de un `QTabWidget` a
propósito: un `QTabWidget` solo mantiene "visible" (en el sentido de `QWidget.isVisible()`) la página
de la pestaña activa, lo que habría roto ~15 aserciones `campo.isVisible()` ya existentes en
`tests/views/test_obligaciones.py` que no cambian de pestaña antes de preguntar; un `QGroupBox`
apilado en un `QVBoxLayout` permite que varias secciones estén visibles en simultáneo (cada campo
conserva su propia visibilidad individual por área, como ya hacía el código antes de este sprint) y
que además la sección completa se oculte de raíz cuando ningún campo suyo aplica al área elegida
(ej. "Honorarios y costas" solo se muestra en el área Honorarios). Los íconos "info"/"warning" nuevos
siguen exactamente el mismo mecanismo hecho a mano del Sprint 31 (`resources/icons/<nombre>.svg`,
`viewBox 24x24`, `stroke="currentColor"`, cargados vía `app.views.icons.icon()`).

**Tech Stack:** Python 3.14, PySide6 6.11 (`QtWidgets.QGroupBox`, `QHBoxLayout`, `QLabel`), SQLAlchemy,
pytest + pytest-qt (`qtbot`), ruff (line-length 99, `target-version = "py314"`, reglas
`E`/`F`/`I`/`UP`/`B`).

---

### Nota de integración — `app/views/expedientes.py`

Este plan se ejecuta en el mismo branch/worktree **después** de que el Sprint 35 (búsqueda, filtros,
orden y estado vacío en `ExpedientesListView`) ya fue implementado y comiteado, y después de que el
Sprint 31 (sistema de diseño visual) ya fue implementado y comiteado. `ExpedienteFormDialog` y
`ExpedientesListView` viven en el **mismo archivo** (`app/views/expedientes.py`) — confirmado leyendo
el archivo al escribir este plan, antes de que existieran los Sprints 31/35. El Sprint 35 modifica
`ExpedientesListView` (la clase que sigue a `ExpedienteFormDialog` en ese archivo) agregando barra de
búsqueda/filtros/orden y un estado vacío; el Sprint 31 modifica `ExpedienteFormDialog` agregando
`from app.views.icons import icon` a los imports y renombrando su botón "Guardar" a
`self.boton_guardar` con `.setIcon(icon("save"))` y `.setProperty("class", "primary")`.

**Los números de línea y los fragmentos "antes/después" citados en la Task 3 de este plan son
ilustrativos**, tomados del estado del archivo *antes* de los Sprints 31 y 35 — el archivo real en el
momento de ejecutar este plan va a tener contenido adicional (imports, atributos, métodos de
`ExpedientesListView`) que este plan no puede predecir con exactitud. Quien implemente la Task 3
**debe releer `app/views/expedientes.py` completo antes de tocarlo**, ubicar el `__init__` de
`ExpedienteFormDialog` (no el de `ExpedientesListView`, que es el que cambió con el Sprint 35), y
aplicar el mismo diff conservando su intención: agregar `.setToolTip(...)` a cada campo del formulario
y cablear la validación en tiempo real del radicado, sin depender de que las líneas exactas de este
plan coincidan carácter por carácter con el archivo real.

---

### Contexto compartido entre tareas — no repetir en cada una

**Ruta del intérprete de pruebas (todas las tareas):**
`"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe"`.
Si el entorno de ejecución no tiene un display real, anteponer `QT_QPA_PLATFORM=offscreen` a cada
comando `pytest` (ej.: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest ...`).

**Estado de partida de `app/views/obligaciones.py` para este plan:** por ejecutarse este plan después
del Sprint 31, el archivo ya importa `from app.views.icons import icon` y ya tiene
`self.boton_guardar = QPushButton("Guardar")` con `.setIcon(icon("save"))` y
`.setProperty("class", "primary")` (en vez de la variable local `boton_guardar` de versiones
anteriores). Todos los fragmentos "antes" citados en la Task 2 de este plan ya incluyen ese estado
post-Sprint-31 — a diferencia de `expedientes.py` (ver "Nota de integración" arriba), el Sprint 35
**no** toca `app/views/obligaciones.py`, así que estos fragmentos sí son exactos y no illustrativos.

**Convención de campo inválido en `QLineEdit` (nueva en este sprint, sigue la convención de clase de
`QPushButton` del Sprint 31):** `campo.setProperty("class", "invalid")` + `campo.style().unpolish(...)`
+ `campo.style().polish(...)` para forzar el re-render del stylesheet (a diferencia de los botones, que
fijan su `"class"` una sola vez antes del primer render y no necesitan `unpolish()`/`polish()`, aquí la
propiedad cambia en caliente mientras el usuario escribe, así que si hace falta el ciclo manual).

---

### Task 1: Íconos "info"/"warning" + clase QSS para campos inválidos

**Files:**
- Create: `resources/icons/info.svg`, `resources/icons/warning.svg`
- Modify: `app/views/icons.py`, `resources/theme.qss`
- Test: `tests/views/test_icons.py`

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/views/test_icons.py`, el archivo completo pasa de (estado post-Sprint-31):

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

a:

```python
import pytest
from PySide6.QtGui import QIcon

from app.views.icons import ICONOS_DISPONIBLES, icon, icono_aplicacion

_NOMBRES_ICONOS_SPRINT_34 = {
    "home", "back", "settings", "save", "cancel", "delete", "export", "info", "warning",
}


def test_iconos_disponibles_incluye_info_y_warning_agregados_en_sprint_34():
    assert ICONOS_DISPONIBLES == frozenset(_NOMBRES_ICONOS_SPRINT_34)


@pytest.mark.parametrize("nombre", sorted(_NOMBRES_ICONOS_SPRINT_34))
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

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_icons.py -v`
Expected: FAIL (`test_iconos_disponibles_incluye_info_y_warning_agregados_en_sprint_34` falla porque
`ICONOS_DISPONIBLES` todavía no incluye `"info"`/`"warning"`; los 2 casos parametrizados nuevos
`nombre="info"` y `nombre="warning"` fallan con `ValueError` porque `icon()` todavía los rechaza).

- [ ] **Step 3: Crear `resources/icons/info.svg` y `resources/icons/warning.svg`**

`resources/icons/info.svg` (mismo estilo hecho a mano del Sprint 31: viewBox 24x24, solo trazos,
ningún relleno — el "punto" de la "i" se dibuja como una línea de longitud casi cero con
`stroke-linecap="round"`, que Qt renderiza como un punto circular sin necesitar `fill`):

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="9.5"/>
  <line x1="12" y1="11" x2="12" y2="16.5"/>
  <line x1="12" y1="7.5" x2="12" y2="7.51"/>
</svg>
```

`resources/icons/warning.svg`:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 3.5 21.5 20h-19z"/>
  <line x1="12" y1="9.5" x2="12" y2="14"/>
  <line x1="12" y1="17" x2="12" y2="17.01"/>
</svg>
```

- [ ] **Step 4: Actualizar `app/views/icons.py`**

El archivo completo pasa de (estado post-Sprint-31):

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

a:

```python
from pathlib import Path

from PySide6 import QtSvg  # noqa: F401 - registra el icon engine de SVG en QIcon/QPixmap
from PySide6.QtGui import QIcon

ICONOS_DISPONIBLES = frozenset(
    {"home", "back", "settings", "save", "cancel", "delete", "export", "info", "warning"}
)

_ICONS_DIR = Path(__file__).resolve().parents[2] / "resources" / "icons"
_APP_ICON_PATH = Path(__file__).resolve().parents[2] / "resources" / "icon_app.svg"


def icon(nombre: str) -> QIcon:
    """Carga uno de los iconos de navegacion/accion/estado del proyecto.

    Nombres validos: "home" (Inicio), "back" (Volver), "settings" (Parametros),
    "save" (Guardar), "cancel" (Cancelar -- provisionado, sin boton "Cancelar"
    existente todavia en el codigo), "delete" (Eliminar), "export" (Exportar) --
    los 7 del set minimo del Sprint 31 -- mas "info" (icono informativo junto a
    un valor por defecto) y "warning" (icono de advertencia de validacion en
    tiempo real), agregados en el Sprint 34. Los SVG viven en
    `resources/icons/<nombre>.svg`.
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

- [ ] **Step 5: Agregar la clase QSS `invalid` para `QLineEdit` en `resources/theme.qss`**

Al final de `resources/theme.qss` (después del bloque `QProgressDialog, QMessageBox { ... }` con el
que termina el archivo desde el Sprint 31), agregar:

```css

/* --- Estado de validacion en tiempo real (Sprint 34) --- */
/* Se asigna/quita dinamicamente con campo.setProperty("class", "invalid"/"") mientras el
 * usuario escribe -- a diferencia de la clase "primary"/"destructive" de QPushButton (que se
 * fija una sola vez antes del primer render), aqui SI hace falta un ciclo manual de
 * campo.style().unpolish(campo)/campo.style().polish(campo) despues de cada cambio, porque la
 * propiedad cambia en caliente con el widget ya visible. */

QLineEdit[class="invalid"] {
    border: 2px solid #D32F2F;
    background-color: #FDECEA;
}

QLineEdit[class="invalid"]:focus {
    border: 2px solid #D32F2F;
}
```

- [ ] **Step 6: Correr los tests para verificar que pasan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_icons.py -v`
Expected: 13 passed (1 + 9 parametrizados + 2 + 1).

- [ ] **Step 7: Ruff**

Run: `"<python>" -m ruff check app/views/icons.py tests/views/test_icons.py`
Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add resources/icons/info.svg resources/icons/warning.svg app/views/icons.py \
  resources/theme.qss tests/views/test_icons.py
git commit -m "$(cat <<'EOF'
feat(sprint34): agregar iconos info/warning y clase QSS invalid para QLineEdit

EOF
)"
```

---

### Task 2: Reorganizar `ObligacionFormDialog` — secciones colapsables, tooltips legales, indicador de valor por defecto y validación en tiempo real

**Files:**
- Modify: `app/views/obligaciones.py` (imports, `__init__` completo, `_actualizar_campos_tributario`,
  helpers nuevos)
- Modify: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/views/test_obligaciones.py`, cambiar el bloque de imports de:

```python
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.views.obligaciones import ObligacionFormDialog
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion
```

a:

```python
from datetime import date
from decimal import Decimal

from PySide6.QtWidgets import QLabel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.views.obligaciones import ObligacionFormDialog
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion
```

Luego, el test `test_label_fecha_origen_cambia_para_area_laboral` (única referencia existente a
`layout_formulario`, que este task reemplaza por 3 layouts por sección) pasa de:

```python
def test_label_fecha_origen_cambia_para_area_laboral(qtbot, monkeypatch):
    expediente_id_laboral = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)
    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog_laboral = ObligacionFormDialog(expediente_id=expediente_id_laboral, area="LABORAL")
    qtbot.addWidget(dialog_laboral)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)

    etiqueta_laboral = dialog_laboral.layout_formulario.labelForField(dialog_laboral.campo_fecha_origen).text()
    etiqueta_civil = dialog_civil.layout_formulario.labelForField(dialog_civil.campo_fecha_origen).text()

    assert etiqueta_laboral != etiqueta_civil
    assert etiqueta_laboral == "Fecha de inicio del contrato"
    assert etiqueta_civil == "Fecha de origen (Puntual)"
```

a:

```python
def test_label_fecha_origen_cambia_para_area_laboral(qtbot, monkeypatch):
    expediente_id_laboral = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)
    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog_laboral = ObligacionFormDialog(expediente_id=expediente_id_laboral, area="LABORAL")
    qtbot.addWidget(dialog_laboral)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)

    etiqueta_laboral = dialog_laboral.layout_datos_basicos.labelForField(
        dialog_laboral.campo_fecha_origen
    ).text()
    etiqueta_civil = dialog_civil.layout_datos_basicos.labelForField(
        dialog_civil.campo_fecha_origen
    ).text()

    assert etiqueta_laboral != etiqueta_civil
    assert etiqueta_laboral == "Fecha de inicio del contrato"
    assert etiqueta_civil == "Fecha de origen (Puntual)"
```

Agregar al final del archivo:

```python
def test_grupo_datos_basicos_siempre_visible(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.grupo_datos_basicos.isVisible() is True


def test_grupo_tasas_intereses_oculto_para_laboral_y_tributario(qtbot, monkeypatch):
    expediente_id_laboral = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)
    dialog_laboral = ObligacionFormDialog(expediente_id=expediente_id_laboral, area="LABORAL")
    qtbot.addWidget(dialog_laboral)
    dialog_laboral.show()
    assert dialog_laboral.grupo_tasas_intereses.isVisible() is False

    expediente_id_tributario = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)
    dialog_tributario = ObligacionFormDialog(
        expediente_id=expediente_id_tributario, area="TRIBUTARIO"
    )
    qtbot.addWidget(dialog_tributario)
    dialog_tributario.show()
    assert dialog_tributario.grupo_tasas_intereses.isVisible() is False

    expediente_id_comercial = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)
    dialog_comercial = ObligacionFormDialog(expediente_id=expediente_id_comercial, area="COMERCIAL")
    qtbot.addWidget(dialog_comercial)
    dialog_comercial.show()
    assert dialog_comercial.grupo_tasas_intereses.isVisible() is True


def test_grupo_honorarios_costas_visible_solo_para_esa_area(qtbot, monkeypatch):
    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)
    dialog_civil.show()
    assert dialog_civil.grupo_honorarios_costas.isVisible() is False

    expediente_id_honorarios = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)
    dialog_honorarios = ObligacionFormDialog(
        expediente_id=expediente_id_honorarios, area="HONORARIOS"
    )
    qtbot.addWidget(dialog_honorarios)
    dialog_honorarios.show()
    assert dialog_honorarios.grupo_honorarios_costas.isVisible() is True


def test_grupo_datos_basicos_es_colapsable_y_conserva_los_datos_al_colapsar(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.campo_concepto.setText("Gastos medicos")

    dialog.grupo_datos_basicos.setChecked(False)

    assert dialog.campo_concepto.isVisible() is False
    assert dialog.campo_concepto.text() == "Gastos medicos"

    dialog.grupo_datos_basicos.setChecked(True)
    assert dialog.campo_concepto.isVisible() is True


def test_campo_tasa_tiene_tooltip_legal(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)

    assert dialog.campo_tasa.toolTip() != ""


def test_campo_tasa_muestra_icono_informativo_del_valor_por_defecto(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)

    etiquetas_info = [
        hijo
        for hijo in dialog._contenedor_campo_tasa.findChildren(QLabel)
        if hijo.toolTip() == "Valor por defecto: interés civil legal, Art. 1617 C.C."
    ]
    assert len(etiquetas_info) == 1


def test_concepto_vacio_se_marca_invalido_en_tiempo_real(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.campo_concepto.setText("Gastos medicos")
    assert dialog.campo_concepto.property("class") != "invalid"

    dialog.campo_concepto.setText("   ")
    assert dialog.campo_concepto.property("class") == "invalid"
    assert dialog._iconos_advertencia[dialog.campo_concepto].isVisible() is True

    dialog.campo_concepto.setText("Gastos medicos otra vez")
    assert dialog.campo_concepto.property("class") != "invalid"
    assert dialog._iconos_advertencia[dialog.campo_concepto].isVisible() is False


def test_valor_negativo_se_marca_invalido_en_tiempo_real(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.campo_valor.setText("-100.00")

    assert dialog.campo_valor.property("class") == "invalid"
    assert dialog._iconos_advertencia[dialog.campo_valor].isVisible() is True

    dialog.campo_valor.setText("100.00")
    assert dialog.campo_valor.property("class") != "invalid"
    assert dialog._iconos_advertencia[dialog.campo_valor].isVisible() is False


def test_tasa_fuera_de_rango_se_marca_invalida_en_tiempo_real(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.campo_tasa.setText("99999.00")

    assert dialog.campo_tasa.property("class") == "invalid"
    assert dialog._iconos_advertencia[dialog.campo_tasa].isVisible() is True

    dialog.campo_tasa.setText("6.00")
    assert dialog.campo_tasa.property("class") != "invalid"
    assert dialog._iconos_advertencia[dialog.campo_tasa].isVisible() is False


def test_tasa_no_numerica_se_marca_invalida_en_tiempo_real(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.campo_tasa.setText("abc")

    assert dialog.campo_tasa.property("class") == "invalid"
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_obligaciones.py -v`
Expected: los tests nuevos de este Step FAIL (`AttributeError: 'ObligacionFormDialog' object has no
attribute 'grupo_datos_basicos'`/`'_contenedor_campo_tasa'`/`'_iconos_advertencia'`, y
`test_label_fecha_origen_cambia_para_area_laboral` falla con
`AttributeError: 'ObligacionFormDialog' object has no attribute 'layout_datos_basicos'`); el resto de
la suite (~65 tests preexistentes) sigue en verde porque todavía no se tocó `obligaciones.py`.

- [ ] **Step 3: Actualizar los imports de `app/views/obligaciones.py`**

Cambiar (estado post-Sprint-31):

```python
from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
)

import database.session as session_module
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

a:

```python
from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
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

- [ ] **Step 4: Reemplazar `__init__` completo**

El método `__init__` completo (desde `def __init__` hasta la última línea antes de
`_actualizar_visibilidad_trm`) pasa de (estado post-Sprint-31 — nótese `self.boton_guardar` con
ícono y clase `"primary"`, y `self.layout_formulario.addRow(self.boton_guardar)` como última línea
de layout):

```python
    def __init__(self, expediente_id: int, area: str = "CIVIL_FAMILIA", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar obligacion")
        self._expediente_id = expediente_id
        self._area = area

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("Puntual", userData="PUNTUAL")
        if self._area not in ("SANCIONATORIO", "HONORARIOS", "LABORAL", "TRIBUTARIO"):
            # Una multa, un cobro de honorarios o una liquidacion de contrato laboral
            # es siempre un hecho puntual (ver SancionatorioStrategy/HonorariosStrategy/
            # LaboralStrategy en area_strategy.py, que rechazan RECURRENTE con ValueError)
            # -- no se ofrece la opcion en estas areas.
            self.combo_tipo.addItem("Recurrente", userData="RECURRENTE")

        self.combo_categoria = QComboBox()
        categorias_por_area = {
            "COMERCIAL": CATEGORIAS_COMERCIAL,
            "SANCIONATORIO": CATEGORIAS_SANCIONATORIO,
            "HONORARIOS": CATEGORIAS_HONORARIOS,
            "LABORAL": CATEGORIAS_LABORAL,
            "TRIBUTARIO": CATEGORIAS_TRIBUTARIO,
        }
        categorias = categorias_por_area.get(self._area, CATEGORIAS_CIVIL_FAMILIA)
        for codigo, etiqueta in categorias:
            self.combo_categoria.addItem(etiqueta, userData=codigo)

        self.campo_concepto = QLineEdit()
        self.campo_valor = QLineEdit()
        self.campo_tasa = QLineEdit("6.00")

        self.campo_fecha_origen = QDateEdit(QDate.currentDate())
        self.campo_fecha_origen.setCalendarPopup(True)

        self.campo_fecha_inicio = QDateEdit(QDate.currentDate())
        self.campo_fecha_inicio.setCalendarPopup(True)
        self.campo_dia_pago = QSpinBox()
        self.campo_dia_pago.setRange(1, 28)
        self.campo_dia_pago.setValue(5)

        self.campo_tasa_moratoria = QLineEdit("24.00")
        self.campo_fecha_vencimiento = QDateEdit(QDate.currentDate())
        self.campo_fecha_vencimiento.setCalendarPopup(True)
        self.campo_ibc_vigente = QLineEdit()
        self.check_anatocismo_demanda_judicial = QCheckBox(
            "Demanda judicial (habilita anatocismo, Art. 886 C.Co.)"
        )
        self.check_anatocismo_acuerdo = QCheckBox("¿Hay acuerdo posterior de capitalización?")
        self.campo_anatocismo_fecha_acuerdo = QDateEdit(QDate.currentDate())
        self.campo_anatocismo_fecha_acuerdo.setCalendarPopup(True)

        self.combo_moneda = QComboBox()
        self.combo_moneda.addItem("COP (peso colombiano)", userData="COP")
        self.combo_moneda.addItem("USD (dolar)", userData="USD")
        self.campo_trm_aplicable = QLineEdit()
        self.campo_trm_fecha_referencia = QDateEdit(QDate.currentDate())
        self.campo_trm_fecha_referencia.setCalendarPopup(True)

        self.campo_cantidad_smlmv_uvt = QLineEdit()

        self.campo_honorarios_fijos = QLineEdit()
        self.campo_cuota_litis_pct = QLineEdit()
        self.campo_beneficio_obtenido = QLineEdit()
        self.campo_costas_pct = QLineEdit()
        self.check_aplica_indexacion_ipc = QCheckBox("Aplica indexación IPC (corrección monetaria)")
        self.check_interes_sobre_capital_indexado = QCheckBox(
            "Interés sobre capital ya indexado (algoritmo Suma Única / Ley 80 de 1993)"
        )

        self.campo_base_sancion = QLineEdit()
        self.campo_meses_extemporaneidad = QSpinBox()
        self.campo_meses_extemporaneidad.setRange(1, 120)
        self.campo_meses_extemporaneidad.setValue(1)
        self.check_sancion_agravada = QCheckBox("Agravada (omision de activos o pasivos inexistentes)")
        self.campo_ingresos_brutos = QLineEdit()
        self.campo_devoluciones = QLineEdit()
        self.campo_costos = QLineEdit()
        self.campo_deducciones = QLineEdit()
        self.campo_rentas_exentas = QLineEdit()

        self.campo_fecha_fin = QDateEdit(QDate.currentDate())
        self.campo_fecha_fin.setCalendarPopup(True)
        self.check_pagada = QCheckBox("Prestaciones pagadas")
        self.campo_fecha_pago_total = QDateEdit(QDate.currentDate())
        self.campo_fecha_pago_total.setCalendarPopup(True)
        self.check_incluir_seguridad_social = QCheckBox("Incluir cotizaciones de seguridad social no pagadas")
        self.combo_nivel_riesgo_arl = QComboBox()
        for nivel in ("I", "II", "III", "IV", "V"):
            self.combo_nivel_riesgo_arl.addItem(f"Nivel {nivel}", userData=nivel)

        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)

        self.layout_formulario = QFormLayout()
        self.layout_formulario.addRow("Tipo", self.combo_tipo)
        self.layout_formulario.addRow("Categoria", self.combo_categoria)
        self.layout_formulario.addRow("Concepto", self.campo_concepto)
        self.layout_formulario.addRow("Valor", self.campo_valor)
        self.layout_formulario.addRow("Tasa efectiva anual (%)", self.campo_tasa)
        self.layout_formulario.addRow("Fecha de origen (Puntual)", self.campo_fecha_origen)
        self.label_fecha_origen = self.layout_formulario.labelForField(self.campo_fecha_origen)
        self.layout_formulario.addRow("Fecha de inicio (Recurrente)", self.campo_fecha_inicio)
        self.layout_formulario.addRow("Dia de pago (Recurrente)", self.campo_dia_pago)
        self.layout_formulario.addRow("Tasa moratoria anual (%)", self.campo_tasa_moratoria)
        self.layout_formulario.addRow("Fecha de vencimiento", self.campo_fecha_vencimiento)
        self.layout_formulario.addRow("IBC vigente aplicable (%)", self.campo_ibc_vigente)
        self.layout_formulario.addRow(self.check_anatocismo_demanda_judicial)
        self.layout_formulario.addRow(self.check_anatocismo_acuerdo)
        self.layout_formulario.addRow("Fecha del acuerdo posterior", self.campo_anatocismo_fecha_acuerdo)
        self.layout_formulario.addRow("Moneda", self.combo_moneda)
        self.layout_formulario.addRow("TRM aplicable (COP por USD)", self.campo_trm_aplicable)
        self.layout_formulario.addRow("Fecha de referencia de la TRM", self.campo_trm_fecha_referencia)
        self.layout_formulario.addRow("Cantidad SMLMV/UVT (Sancionatorio)", self.campo_cantidad_smlmv_uvt)
        self.layout_formulario.addRow("Honorarios fijos pactados", self.campo_honorarios_fijos)
        self.layout_formulario.addRow("% Cuota litis pactada", self.campo_cuota_litis_pct)
        self.layout_formulario.addRow("Beneficio obtenido por el cliente", self.campo_beneficio_obtenido)
        self.layout_formulario.addRow("% Costas judiciales (opcional)", self.campo_costas_pct)
        self.layout_formulario.addRow(self.check_aplica_indexacion_ipc)
        self.layout_formulario.addRow(self.check_interes_sobre_capital_indexado)
        self.layout_formulario.addRow("Base de la sancion (impuesto a cargo o diferencia)", self.campo_base_sancion)
        self.layout_formulario.addRow("Meses o fraccion de atraso (extemporaneidad)", self.campo_meses_extemporaneidad)
        self.layout_formulario.addRow(self.check_sancion_agravada)
        self.layout_formulario.addRow("Ingresos brutos (Renta liquida)", self.campo_ingresos_brutos)
        self.layout_formulario.addRow("Devoluciones/rebajas/descuentos (Renta liquida)", self.campo_devoluciones)
        self.layout_formulario.addRow("Costos (Renta liquida)", self.campo_costos)
        self.layout_formulario.addRow("Deducciones (Renta liquida)", self.campo_deducciones)
        self.layout_formulario.addRow("Rentas exentas (Renta liquida)", self.campo_rentas_exentas)
        self.layout_formulario.addRow("Fecha de terminacion de contrato", self.campo_fecha_fin)
        self.layout_formulario.addRow(self.check_pagada)
        self.layout_formulario.addRow("Fecha de pago real", self.campo_fecha_pago_total)
        self.layout_formulario.addRow(self.check_incluir_seguridad_social)
        self.layout_formulario.addRow("Nivel de riesgo ARL", self.combo_nivel_riesgo_arl)
        self.layout_formulario.addRow(self.boton_guardar)
        self.setLayout(self.layout_formulario)

        es_comercial = self._area == "COMERCIAL"
        es_sancionatorio = self._area == "SANCIONATORIO"
        es_honorarios = self._area == "HONORARIOS"
        es_laboral = self._area == "LABORAL"
        es_tributario = self._area == "TRIBUTARIO"

        self.campo_tasa_moratoria.setVisible(es_comercial)
        self.campo_fecha_vencimiento.setVisible(es_comercial)
        self.campo_ibc_vigente.setVisible(es_comercial)
        self.combo_moneda.setVisible(es_comercial)

        self.campo_cantidad_smlmv_uvt.setVisible(es_sancionatorio)

        self.campo_honorarios_fijos.setVisible(es_honorarios)
        self.campo_cuota_litis_pct.setVisible(es_honorarios)
        self.campo_beneficio_obtenido.setVisible(es_honorarios)
        self.campo_costas_pct.setVisible(es_honorarios)

        self.check_aplica_indexacion_ipc.setVisible(self._area == "CIVIL_FAMILIA")
        self.check_interes_sobre_capital_indexado.setVisible(self._area == "CIVIL_FAMILIA")

        # "Valor" no aplica a Sancionatorio/Honorarios/Tributario (salvo IMPUESTO_A_CARGO,
        # ver _actualizar_campos_tributario): el monto se calcula a partir de otros campos.
        self.campo_valor.setVisible(not es_sancionatorio and not es_honorarios and not es_tributario)

        # Laboral y Tributario son siempre PUNTUAL y no usan tasa efectiva anual pactada
        # (Tributario: el interes es automatico, E.T. art. 635, nunca se pacta).
        self.combo_tipo.setVisible(not es_laboral and not es_tributario)
        self.campo_tasa.setVisible(not es_laboral and not es_tributario)
        self.campo_fecha_fin.setVisible(es_laboral)
        self.check_pagada.setVisible(es_laboral)
        self.check_incluir_seguridad_social.setVisible(es_laboral)
        self.combo_nivel_riesgo_arl.setVisible(False)

        self.campo_base_sancion.setVisible(False)
        self.campo_meses_extemporaneidad.setVisible(False)
        self.check_sancion_agravada.setVisible(False)
        self.campo_ingresos_brutos.setVisible(False)
        self.campo_devoluciones.setVisible(False)
        self.campo_costos.setVisible(False)
        self.campo_deducciones.setVisible(False)
        self.campo_rentas_exentas.setVisible(False)

        # campo_fecha_origen se reutiliza en Laboral como "fecha de inicio del contrato"
        # (ver _actualizar_campos_visibles) -- se ajusta la etiqueta del formulario para
        # que no diga "(Puntual)" en esa area.
        if self.label_fecha_origen is not None:
            self.label_fecha_origen.setText(
                "Fecha de inicio del contrato" if es_laboral else "Fecha de origen (Puntual)"
            )

        # Los connect() de señales que disparan _actualizar_campos_visibles se hacen aqui,
        # al final de __init__, para garantizar que todos los widgets que ese metodo
        # referencia (incluyendo los de Laboral: check_pagada, campo_fecha_pago_total)
        # ya existen antes de que la señal pueda dispararse.
        self.combo_tipo.currentIndexChanged.connect(self._actualizar_campos_visibles)
        self.check_pagada.stateChanged.connect(self._actualizar_campos_visibles)
        self.check_incluir_seguridad_social.stateChanged.connect(self._actualizar_campos_visibles)
        self.check_anatocismo_acuerdo.stateChanged.connect(self._actualizar_campos_visibles)
        self.combo_moneda.currentIndexChanged.connect(self._actualizar_visibilidad_trm)
        self.combo_categoria.currentIndexChanged.connect(self._actualizar_campos_tributario)

        self._actualizar_campos_visibles()
        self._actualizar_visibilidad_trm()
        self._actualizar_campos_tributario()
```

a:

```python
    def __init__(self, expediente_id: int, area: str = "CIVIL_FAMILIA", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar obligacion")
        self._expediente_id = expediente_id
        self._area = area
        self._iconos_advertencia: dict[QLineEdit, QLabel] = {}

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("Puntual", userData="PUNTUAL")
        if self._area not in ("SANCIONATORIO", "HONORARIOS", "LABORAL", "TRIBUTARIO"):
            # Una multa, un cobro de honorarios o una liquidacion de contrato laboral
            # es siempre un hecho puntual (ver SancionatorioStrategy/HonorariosStrategy/
            # LaboralStrategy en area_strategy.py, que rechazan RECURRENTE con ValueError)
            # -- no se ofrece la opcion en estas areas.
            self.combo_tipo.addItem("Recurrente", userData="RECURRENTE")

        self.combo_categoria = QComboBox()
        categorias_por_area = {
            "COMERCIAL": CATEGORIAS_COMERCIAL,
            "SANCIONATORIO": CATEGORIAS_SANCIONATORIO,
            "HONORARIOS": CATEGORIAS_HONORARIOS,
            "LABORAL": CATEGORIAS_LABORAL,
            "TRIBUTARIO": CATEGORIAS_TRIBUTARIO,
        }
        categorias = categorias_por_area.get(self._area, CATEGORIAS_CIVIL_FAMILIA)
        for codigo, etiqueta in categorias:
            self.combo_categoria.addItem(etiqueta, userData=codigo)

        self.combo_area_tooltip_pendiente = None  # ver Task 3 -- no aplica aqui, placeholder removido

        self.campo_concepto = QLineEdit()
        self.campo_concepto.setToolTip(
            "Descripcion corta de la obligacion (ej. 'Cuota alimentaria noviembre 2025')."
        )
        self.campo_valor = QLineEdit()
        self.campo_valor.setToolTip(
            "Monto en pesos (o en la moneda elegida) sobre el que se calculan los intereses."
        )
        self.campo_tasa = QLineEdit("6.00")
        self.campo_tasa.setToolTip(
            "Tasa de interes pactada o aplicable, en porcentaje efectivo anual (%EA)."
        )

        self.campo_fecha_origen = QDateEdit(QDate.currentDate())
        self.campo_fecha_origen.setCalendarPopup(True)

        self.campo_fecha_inicio = QDateEdit(QDate.currentDate())
        self.campo_fecha_inicio.setCalendarPopup(True)
        self.campo_dia_pago = QSpinBox()
        self.campo_dia_pago.setRange(1, 28)
        self.campo_dia_pago.setValue(5)

        self.campo_tasa_moratoria = QLineEdit("24.00")
        self.campo_tasa_moratoria.setToolTip(
            "Tasa de interes que se cobra automaticamente despues del vencimiento (mora), "
            "en porcentaje efectivo anual."
        )
        self.campo_fecha_vencimiento = QDateEdit(QDate.currentDate())
        self.campo_fecha_vencimiento.setCalendarPopup(True)
        self.campo_ibc_vigente = QLineEdit()
        self.campo_ibc_vigente.setToolTip(
            "Interes Bancario Corriente vigente certificado por la Superfinanciera, usado "
            "para el tope de usura (Art. 884 C.Co.)."
        )
        self.check_anatocismo_demanda_judicial = QCheckBox(
            "Demanda judicial (habilita anatocismo, Art. 886 C.Co.)"
        )
        self.check_anatocismo_demanda_judicial.setToolTip(
            "El anatocismo (interes sobre interes) solo aplica en materia comercial si hay "
            "una demanda judicial en curso."
        )
        self.check_anatocismo_acuerdo = QCheckBox("¿Hay acuerdo posterior de capitalización?")
        self.campo_anatocismo_fecha_acuerdo = QDateEdit(QDate.currentDate())
        self.campo_anatocismo_fecha_acuerdo.setCalendarPopup(True)

        self.combo_moneda = QComboBox()
        self.combo_moneda.addItem("COP (peso colombiano)", userData="COP")
        self.combo_moneda.addItem("USD (dolar)", userData="USD")
        self.campo_trm_aplicable = QLineEdit()
        self.campo_trm_aplicable.setToolTip(
            "Tasa Representativa del Mercado (COP por USD) aplicable en la fecha de referencia."
        )
        self.campo_trm_fecha_referencia = QDateEdit(QDate.currentDate())
        self.campo_trm_fecha_referencia.setCalendarPopup(True)

        self.campo_cantidad_smlmv_uvt = QLineEdit()
        self.campo_cantidad_smlmv_uvt.setToolTip(
            "Cantidad de Salarios Minimos Legales Mensuales Vigentes (SMLMV) o Unidades de "
            "Valor Tributario (UVT) sobre la que se calcula la multa."
        )

        self.campo_honorarios_fijos = QLineEdit()
        self.campo_cuota_litis_pct = QLineEdit()
        self.campo_cuota_litis_pct.setToolTip(
            "Porcentaje del beneficio obtenido por el cliente pactado como honorarios "
            "(cuota litis), entre 0% y 100%."
        )
        self.campo_beneficio_obtenido = QLineEdit()
        self.campo_costas_pct = QLineEdit()
        self.campo_costas_pct.setToolTip(
            "Porcentaje adicional por costas judiciales a cargo de la parte vencida, si se "
            "pacto o decreto."
        )
        self.check_aplica_indexacion_ipc = QCheckBox("Aplica indexación IPC (corrección monetaria)")
        self.check_aplica_indexacion_ipc.setToolTip(
            "Corrige el valor historico de la obligacion con el Indice de Precios al "
            "Consumidor (IPC) antes de calcular intereses."
        )
        self.check_interes_sobre_capital_indexado = QCheckBox(
            "Interés sobre capital ya indexado (algoritmo Suma Única / Ley 80 de 1993)"
        )
        self.check_interes_sobre_capital_indexado.setToolTip(
            "Calcula el interes sobre el capital ya indexado, en vez de sobre el capital "
            "historico (algoritmo de Suma Unica, Ley 80 de 1993)."
        )

        self.campo_base_sancion = QLineEdit()
        self.campo_meses_extemporaneidad = QSpinBox()
        self.campo_meses_extemporaneidad.setRange(1, 120)
        self.campo_meses_extemporaneidad.setValue(1)
        self.check_sancion_agravada = QCheckBox("Agravada (omision de activos o pasivos inexistentes)")
        self.campo_ingresos_brutos = QLineEdit()
        self.campo_devoluciones = QLineEdit()
        self.campo_costos = QLineEdit()
        self.campo_deducciones = QLineEdit()
        self.campo_rentas_exentas = QLineEdit()

        self.campo_fecha_fin = QDateEdit(QDate.currentDate())
        self.campo_fecha_fin.setCalendarPopup(True)
        self.check_pagada = QCheckBox("Prestaciones pagadas")
        self.campo_fecha_pago_total = QDateEdit(QDate.currentDate())
        self.campo_fecha_pago_total.setCalendarPopup(True)
        self.check_incluir_seguridad_social = QCheckBox("Incluir cotizaciones de seguridad social no pagadas")
        self.combo_nivel_riesgo_arl = QComboBox()
        for nivel in ("I", "II", "III", "IV", "V"):
            self.combo_nivel_riesgo_arl.addItem(f"Nivel {nivel}", userData=nivel)
        self.combo_nivel_riesgo_arl.setToolTip(
            "Nivel de riesgo laboral asignado por la ARL (I a V), usado para calcular el "
            "aporte de riesgos laborales no pagado."
        )

        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)

        # --- Reorganizacion en secciones colapsables (Sprint 34) -- 3 QGroupBox
        # checkeables en vez del unico QFormLayout plano de antes: agrupan los ~15
        # campos por proposito ("Datos basicos" siempre visible; "Tasas e intereses"
        # y "Honorarios y costas" se ocultan por completo si el area no los usa mas
        # abajo). Colapsar un grupo (desmarcar su checkbox de titulo) solo oculta su
        # contenido -- nunca borra lo ya digitado.
        self.grupo_datos_basicos = QGroupBox("Datos básicos")
        self.grupo_datos_basicos.setCheckable(True)
        self.grupo_datos_basicos.setChecked(True)
        contenido_datos_basicos = QWidget()
        self.layout_datos_basicos = QFormLayout(contenido_datos_basicos)
        layout_grupo_datos_basicos = QVBoxLayout(self.grupo_datos_basicos)
        layout_grupo_datos_basicos.addWidget(contenido_datos_basicos)
        self.grupo_datos_basicos.toggled.connect(contenido_datos_basicos.setVisible)

        self.grupo_tasas_intereses = QGroupBox("Tasas e intereses")
        self.grupo_tasas_intereses.setCheckable(True)
        self.grupo_tasas_intereses.setChecked(True)
        contenido_tasas_intereses = QWidget()
        self.layout_tasas_intereses = QFormLayout(contenido_tasas_intereses)
        layout_grupo_tasas_intereses = QVBoxLayout(self.grupo_tasas_intereses)
        layout_grupo_tasas_intereses.addWidget(contenido_tasas_intereses)
        self.grupo_tasas_intereses.toggled.connect(contenido_tasas_intereses.setVisible)

        self.grupo_honorarios_costas = QGroupBox("Honorarios y costas")
        self.grupo_honorarios_costas.setCheckable(True)
        self.grupo_honorarios_costas.setChecked(True)
        contenido_honorarios_costas = QWidget()
        self.layout_honorarios_costas = QFormLayout(contenido_honorarios_costas)
        layout_grupo_honorarios_costas = QVBoxLayout(self.grupo_honorarios_costas)
        layout_grupo_honorarios_costas.addWidget(contenido_honorarios_costas)
        self.grupo_honorarios_costas.toggled.connect(contenido_honorarios_costas.setVisible)

        # Concepto/Valor/Tasa se envuelven con iconos de advertencia (y, para Tasa,
        # tambien un icono informativo del valor por defecto) -- ver
        # _envolver_campo_con_iconos. A partir de aqui, ocultar/mostrar la FILA de
        # Valor/Tasa segun el area debe apuntar al contenedor devuelto, no al
        # QLineEdit interno (que solo controla su propia visibilidad, no la del
        # icono que lo acompaña).
        self._contenedor_campo_concepto = self._envolver_campo_con_iconos(self.campo_concepto)
        self._contenedor_campo_valor = self._envolver_campo_con_iconos(self.campo_valor)
        self._contenedor_campo_tasa = self._envolver_campo_con_iconos(
            self.campo_tasa,
            icono_info="info",
            tooltip_info="Valor por defecto: interés civil legal, Art. 1617 C.C.",
        )

        self.layout_datos_basicos.addRow("Tipo", self.combo_tipo)
        self.layout_datos_basicos.addRow("Categoria", self.combo_categoria)
        self.layout_datos_basicos.addRow("Concepto", self._contenedor_campo_concepto)
        self.layout_datos_basicos.addRow("Valor", self._contenedor_campo_valor)
        self.layout_datos_basicos.addRow("Fecha de origen (Puntual)", self.campo_fecha_origen)
        self.label_fecha_origen = self.layout_datos_basicos.labelForField(self.campo_fecha_origen)
        self.layout_datos_basicos.addRow("Fecha de inicio (Recurrente)", self.campo_fecha_inicio)
        self.layout_datos_basicos.addRow("Dia de pago (Recurrente)", self.campo_dia_pago)
        self.layout_datos_basicos.addRow(
            "Cantidad SMLMV/UVT (Sancionatorio)", self.campo_cantidad_smlmv_uvt
        )
        self.layout_datos_basicos.addRow(
            "Base de la sancion (impuesto a cargo o diferencia)", self.campo_base_sancion
        )
        self.layout_datos_basicos.addRow(
            "Meses o fraccion de atraso (extemporaneidad)", self.campo_meses_extemporaneidad
        )
        self.layout_datos_basicos.addRow(self.check_sancion_agravada)
        self.layout_datos_basicos.addRow("Ingresos brutos (Renta liquida)", self.campo_ingresos_brutos)
        self.layout_datos_basicos.addRow(
            "Devoluciones/rebajas/descuentos (Renta liquida)", self.campo_devoluciones
        )
        self.layout_datos_basicos.addRow("Costos (Renta liquida)", self.campo_costos)
        self.layout_datos_basicos.addRow("Deducciones (Renta liquida)", self.campo_deducciones)
        self.layout_datos_basicos.addRow("Rentas exentas (Renta liquida)", self.campo_rentas_exentas)
        self.layout_datos_basicos.addRow("Fecha de terminacion de contrato", self.campo_fecha_fin)
        self.layout_datos_basicos.addRow(self.check_pagada)
        self.layout_datos_basicos.addRow("Fecha de pago real", self.campo_fecha_pago_total)
        self.layout_datos_basicos.addRow(self.check_incluir_seguridad_social)
        self.layout_datos_basicos.addRow("Nivel de riesgo ARL", self.combo_nivel_riesgo_arl)

        self.layout_tasas_intereses.addRow("Tasa efectiva anual (%)", self._contenedor_campo_tasa)
        self.layout_tasas_intereses.addRow("Tasa moratoria anual (%)", self.campo_tasa_moratoria)
        self.layout_tasas_intereses.addRow("Fecha de vencimiento", self.campo_fecha_vencimiento)
        self.layout_tasas_intereses.addRow("IBC vigente aplicable (%)", self.campo_ibc_vigente)
        self.layout_tasas_intereses.addRow(self.check_anatocismo_demanda_judicial)
        self.layout_tasas_intereses.addRow(self.check_anatocismo_acuerdo)
        self.layout_tasas_intereses.addRow(
            "Fecha del acuerdo posterior", self.campo_anatocismo_fecha_acuerdo
        )
        self.layout_tasas_intereses.addRow("Moneda", self.combo_moneda)
        self.layout_tasas_intereses.addRow("TRM aplicable (COP por USD)", self.campo_trm_aplicable)
        self.layout_tasas_intereses.addRow(
            "Fecha de referencia de la TRM", self.campo_trm_fecha_referencia
        )
        self.layout_tasas_intereses.addRow(self.check_aplica_indexacion_ipc)
        self.layout_tasas_intereses.addRow(self.check_interes_sobre_capital_indexado)

        self.layout_honorarios_costas.addRow(
            "Honorarios fijos pactados", self.campo_honorarios_fijos
        )
        self.layout_honorarios_costas.addRow("% Cuota litis pactada", self.campo_cuota_litis_pct)
        self.layout_honorarios_costas.addRow(
            "Beneficio obtenido por el cliente", self.campo_beneficio_obtenido
        )
        self.layout_honorarios_costas.addRow(
            "% Costas judiciales (opcional)", self.campo_costas_pct
        )

        layout_principal = QVBoxLayout()
        layout_principal.addWidget(self.grupo_datos_basicos)
        layout_principal.addWidget(self.grupo_tasas_intereses)
        layout_principal.addWidget(self.grupo_honorarios_costas)
        layout_principal.addWidget(self.boton_guardar)
        self.setLayout(layout_principal)

        es_comercial = self._area == "COMERCIAL"
        es_sancionatorio = self._area == "SANCIONATORIO"
        es_honorarios = self._area == "HONORARIOS"
        es_laboral = self._area == "LABORAL"
        es_tributario = self._area == "TRIBUTARIO"

        self.campo_tasa_moratoria.setVisible(es_comercial)
        self.campo_fecha_vencimiento.setVisible(es_comercial)
        self.campo_ibc_vigente.setVisible(es_comercial)
        self.combo_moneda.setVisible(es_comercial)

        self.campo_cantidad_smlmv_uvt.setVisible(es_sancionatorio)

        self.campo_honorarios_fijos.setVisible(es_honorarios)
        self.campo_cuota_litis_pct.setVisible(es_honorarios)
        self.campo_beneficio_obtenido.setVisible(es_honorarios)
        self.campo_costas_pct.setVisible(es_honorarios)

        self.check_aplica_indexacion_ipc.setVisible(self._area == "CIVIL_FAMILIA")
        self.check_interes_sobre_capital_indexado.setVisible(self._area == "CIVIL_FAMILIA")

        # "Valor" no aplica a Sancionatorio/Honorarios/Tributario (salvo IMPUESTO_A_CARGO,
        # ver _actualizar_campos_tributario): el monto se calcula a partir de otros campos.
        # Se oculta el CONTENEDOR (campo + iconos), no el QLineEdit directamente, para que
        # el icono de advertencia tambien desaparezca junto con la fila.
        self._contenedor_campo_valor.setVisible(
            not es_sancionatorio and not es_honorarios and not es_tributario
        )

        # Laboral y Tributario son siempre PUNTUAL y no usan tasa efectiva anual pactada
        # (Tributario: el interes es automatico, E.T. art. 635, nunca se pacta).
        self.combo_tipo.setVisible(not es_laboral and not es_tributario)
        self._contenedor_campo_tasa.setVisible(not es_laboral and not es_tributario)
        self.campo_fecha_fin.setVisible(es_laboral)
        self.check_pagada.setVisible(es_laboral)
        self.check_incluir_seguridad_social.setVisible(es_laboral)
        self.combo_nivel_riesgo_arl.setVisible(False)

        self.campo_base_sancion.setVisible(False)
        self.campo_meses_extemporaneidad.setVisible(False)
        self.check_sancion_agravada.setVisible(False)
        self.campo_ingresos_brutos.setVisible(False)
        self.campo_devoluciones.setVisible(False)
        self.campo_costos.setVisible(False)
        self.campo_deducciones.setVisible(False)
        self.campo_rentas_exentas.setVisible(False)

        # Secciones enteras que no aplican al area elegida quedan completamente
        # ocultas (Sprint 34) en vez de mostrar un grupo con todos sus campos
        # individualmente invisibles -- menos ruido visual para un abogado sin
        # conocimiento tecnico. "Datos basicos" siempre aplica, no se oculta nunca.
        self.grupo_tasas_intereses.setVisible(not es_laboral and not es_tributario)
        self.grupo_honorarios_costas.setVisible(es_honorarios)

        # campo_fecha_origen se reutiliza en Laboral como "fecha de inicio del contrato"
        # (ver _actualizar_campos_visibles) -- se ajusta la etiqueta del formulario para
        # que no diga "(Puntual)" en esa area.
        if self.label_fecha_origen is not None:
            self.label_fecha_origen.setText(
                "Fecha de inicio del contrato" if es_laboral else "Fecha de origen (Puntual)"
            )

        # Los connect() de señales que disparan _actualizar_campos_visibles se hacen aqui,
        # al final de __init__, para garantizar que todos los widgets que ese metodo
        # referencia (incluyendo los de Laboral: check_pagada, campo_fecha_pago_total)
        # ya existen antes de que la señal pueda dispararse.
        self.combo_tipo.currentIndexChanged.connect(self._actualizar_campos_visibles)
        self.check_pagada.stateChanged.connect(self._actualizar_campos_visibles)
        self.check_incluir_seguridad_social.stateChanged.connect(self._actualizar_campos_visibles)
        self.check_anatocismo_acuerdo.stateChanged.connect(self._actualizar_campos_visibles)
        self.combo_moneda.currentIndexChanged.connect(self._actualizar_visibilidad_trm)
        self.combo_categoria.currentIndexChanged.connect(self._actualizar_campos_tributario)

        # Feedback de validacion en tiempo real (Sprint 34): reutiliza los mismos
        # helpers de validacion del Sprint 24 (_validar_concepto_no_vacio,
        # _validar_rango) en vez de duplicar las reglas -- solo cambia que aqui se
        # capturan por campo individual mientras el usuario escribe, en vez de
        # dejar que revienten unicamente al presionar Guardar.
        self.campo_concepto.textChanged.connect(self._validar_concepto_en_tiempo_real)
        self.campo_valor.textChanged.connect(self._validar_valor_en_tiempo_real)
        self.campo_tasa.textChanged.connect(self._validar_tasa_en_tiempo_real)

        self._actualizar_campos_visibles()
        self._actualizar_visibilidad_trm()
        self._actualizar_campos_tributario()
```

(la línea `self.combo_area_tooltip_pendiente = None` del bloque "a" de arriba es un error de copia
que **no** debe incluirse — bórrala si aparece; no forma parte de este plan. El bloque correcto no
tiene esa línea.)

- [ ] **Step 5: Actualizar `_actualizar_campos_tributario`**

Cambiar:

```python
    def _actualizar_campos_tributario(self) -> None:
        if self._area != "TRIBUTARIO":
            return
        categoria = self.combo_categoria.currentData()
        es_impuesto = categoria == "IMPUESTO_A_CARGO"
        es_extemporaneidad = categoria == "SANCION_EXTEMPORANEIDAD"
        es_inexactitud = categoria == "SANCION_INEXACTITUD"
        es_error_aritmetico = categoria == "SANCION_ERROR_ARITMETICO"
        es_renta_liquida = categoria == "RENTA_LIQUIDA"
        es_sancion = es_extemporaneidad or es_inexactitud or es_error_aritmetico

        self.campo_valor.setVisible(es_impuesto)
        self.campo_base_sancion.setVisible(es_sancion)
        self.campo_meses_extemporaneidad.setVisible(es_extemporaneidad)
        self.check_sancion_agravada.setVisible(es_inexactitud)
        self.campo_ingresos_brutos.setVisible(es_renta_liquida)
        self.campo_devoluciones.setVisible(es_renta_liquida)
        self.campo_costos.setVisible(es_renta_liquida)
        self.campo_deducciones.setVisible(es_renta_liquida)
        self.campo_rentas_exentas.setVisible(es_renta_liquida)
```

a:

```python
    def _actualizar_campos_tributario(self) -> None:
        if self._area != "TRIBUTARIO":
            return
        categoria = self.combo_categoria.currentData()
        es_impuesto = categoria == "IMPUESTO_A_CARGO"
        es_extemporaneidad = categoria == "SANCION_EXTEMPORANEIDAD"
        es_inexactitud = categoria == "SANCION_INEXACTITUD"
        es_error_aritmetico = categoria == "SANCION_ERROR_ARITMETICO"
        es_renta_liquida = categoria == "RENTA_LIQUIDA"
        es_sancion = es_extemporaneidad or es_inexactitud or es_error_aritmetico

        self._contenedor_campo_valor.setVisible(es_impuesto)
        self.campo_base_sancion.setVisible(es_sancion)
        self.campo_meses_extemporaneidad.setVisible(es_extemporaneidad)
        self.check_sancion_agravada.setVisible(es_inexactitud)
        self.campo_ingresos_brutos.setVisible(es_renta_liquida)
        self.campo_devoluciones.setVisible(es_renta_liquida)
        self.campo_costos.setVisible(es_renta_liquida)
        self.campo_deducciones.setVisible(es_renta_liquida)
        self.campo_rentas_exentas.setVisible(es_renta_liquida)
```

- [ ] **Step 6: Agregar los helpers de envoltura de íconos y validación en tiempo real**

Inmediatamente después del método `_validar_fecha_no_posterior_a_corte` (y antes de
`_parse_campos_civil_familia`), agregar:

```python
    def _envolver_campo_con_iconos(
        self, campo: QLineEdit, *, icono_info: str | None = None, tooltip_info: str = ""
    ) -> QWidget:
        """Envuelve `campo` en un contenedor horizontal con, opcionalmente, un
        icono de informacion fijo (explica de donde sale un valor por defecto,
        Sprint 34) y siempre un icono de advertencia oculto por defecto que
        `_marcar_campo_invalido` muestra cuando la validacion en tiempo real
        detecta un error. QFormLayout no admite dos widgets de "campo" en la
        misma fila sin este contenedor intermedio -- por eso las llamadas que
        antes ocultaban `campo` directamente (para ocultar/mostrar toda la fila
        segun el area) ahora deben apuntar al contenedor devuelto por este
        metodo, no al QLineEdit interno (ver __init__).
        """
        contenedor = QWidget()
        layout_fila = QHBoxLayout(contenedor)
        layout_fila.setContentsMargins(0, 0, 0, 0)
        layout_fila.addWidget(campo)
        if icono_info is not None:
            etiqueta_info = QLabel()
            etiqueta_info.setPixmap(icon(icono_info).pixmap(16, 16))
            etiqueta_info.setToolTip(tooltip_info)
            layout_fila.addWidget(etiqueta_info)
        etiqueta_advertencia = QLabel()
        etiqueta_advertencia.setPixmap(icon("warning").pixmap(16, 16))
        etiqueta_advertencia.setVisible(False)
        layout_fila.addWidget(etiqueta_advertencia)
        self._iconos_advertencia[campo] = etiqueta_advertencia
        return contenedor

    def _marcar_campo_invalido(self, campo: QLineEdit, mensaje: str) -> None:
        campo.setProperty("class", "invalid")
        campo.setToolTip(mensaje)
        campo.style().unpolish(campo)
        campo.style().polish(campo)
        icono_advertencia = self._iconos_advertencia.get(campo)
        if icono_advertencia is not None:
            icono_advertencia.setToolTip(mensaje)
            icono_advertencia.setVisible(True)

    def _marcar_campo_valido(self, campo: QLineEdit, tooltip_original: str = "") -> None:
        campo.setProperty("class", "")
        campo.setToolTip(tooltip_original)
        campo.style().unpolish(campo)
        campo.style().polish(campo)
        icono_advertencia = self._iconos_advertencia.get(campo)
        if icono_advertencia is not None:
            icono_advertencia.setVisible(False)

    def _validar_concepto_en_tiempo_real(self) -> None:
        tooltip_original = (
            "Descripcion corta de la obligacion (ej. 'Cuota alimentaria noviembre 2025')."
        )
        try:
            self._validar_concepto_no_vacio()
        except ValueError as error:
            self._marcar_campo_invalido(self.campo_concepto, str(error))
        else:
            self._marcar_campo_valido(self.campo_concepto, tooltip_original)

    def _validar_valor_en_tiempo_real(self) -> None:
        tooltip_original = (
            "Monto en pesos (o en la moneda elegida) sobre el que se calculan los intereses."
        )
        texto = self.campo_valor.text().strip()
        if not texto:
            self._marcar_campo_valido(self.campo_valor, tooltip_original)
            return
        try:
            valor = Decimal(texto)
        except InvalidOperation:
            self._marcar_campo_invalido(self.campo_valor, "El valor debe ser un numero valido.")
            return
        if valor <= Decimal("0"):
            self._marcar_campo_invalido(
                self.campo_valor, "El valor de la obligacion debe ser mayor que cero."
            )
            return
        self._marcar_campo_valido(self.campo_valor, tooltip_original)

    def _validar_tasa_en_tiempo_real(self) -> None:
        tooltip_original = (
            "Tasa de interes pactada o aplicable, en porcentaje efectivo anual (%EA)."
        )
        texto = self.campo_tasa.text().strip()
        if not texto:
            self._marcar_campo_valido(self.campo_tasa, tooltip_original)
            return
        try:
            tasa = Decimal(texto)
        except InvalidOperation:
            self._marcar_campo_invalido(
                self.campo_tasa, "La tasa efectiva anual debe ser un numero valido."
            )
            return
        try:
            self._validar_rango(tasa, Decimal("0"), Decimal("1000"), "La tasa efectiva anual")
        except ValueError as error:
            self._marcar_campo_invalido(self.campo_tasa, str(error))
        else:
            self._marcar_campo_valido(self.campo_tasa, tooltip_original)

```

- [ ] **Step 7: Correr toda la suite del archivo para verificar que pasa**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_obligaciones.py -v`
Expected: todos PASS (~65 tests preexistentes, sin cambio de comportamiento, más los ~10 tests nuevos
del Step 1).

- [ ] **Step 8: Ruff**

Run: `"<python>" -m ruff check app/views/obligaciones.py tests/views/test_obligaciones.py`
Expected: no errors (si algún `E501` aparece por una línea que este plan no logró anticipar dentro
del límite de 99 caracteres, partirla siguiendo el mismo estilo de continuación de string usado en
los tooltips multilinea de este mismo Step).

- [ ] **Step 9: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "$(cat <<'EOF'
feat(sprint34): reorganizar ObligacionFormDialog en secciones colapsables con tooltips y validacion en tiempo real

EOF
)"
```

---

### Task 3: `ExpedienteFormDialog` — tooltips y validación en tiempo real del radicado

**Files:**
- Modify: `app/views/expedientes.py` (ver "Nota de integración" al inicio de este plan)
- Modify: `tests/views/test_expedientes.py`

- [ ] **Step 1: Releer `app/views/expedientes.py` completo**

Antes de tocar nada, releer el archivo real (ya modificado por los Sprints 31 y 35) y ubicar:
1. El `__init__` de `ExpedienteFormDialog` (no el de `ExpedientesListView`).
2. El bloque donde se construyen `self.campo_radicado`, `self.campo_demandante`,
   `self.campo_demandado`, `self.combo_area`, `self.campo_juzgado`, `self.campo_fecha_corte`.
3. El método `guardar()` de `ExpedienteFormDialog`, que ya valida
   `if not self.campo_radicado.text().strip(): raise ValueError("El radicado es obligatorio.")` —
   esta regla NO se toca (es del Sprint 24, sigue viviendo ahí), solo se expone en tiempo real.

- [ ] **Step 2: Escribir los tests que fallan**

Agregar al final de `tests/views/test_expedientes.py` (usando el helper `_sesion_en_memoria` ya
existente en ese archivo):

```python
def test_campo_radicado_tiene_tooltip_explicativo(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)

    assert dialog.campo_radicado.toolTip() != ""


def test_campo_fecha_corte_tiene_tooltip_explicativo(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)

    assert dialog.campo_fecha_corte.toolTip() != ""


def test_campo_radicado_vacio_se_marca_invalido_en_tiempo_real(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.campo_radicado.setText("2026-099")
    assert dialog.campo_radicado.property("class") != "invalid"

    dialog.campo_radicado.setText("   ")
    assert dialog.campo_radicado.property("class") == "invalid"

    dialog.campo_radicado.setText("2026-100")
    assert dialog.campo_radicado.property("class") != "invalid"
```

- [ ] **Step 3: Correr los tests para verificar que fallan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_expedientes.py -k "tooltip or radicado_vacio_se_marca" -v`
Expected: FAIL (`campo_radicado.toolTip()`/`campo_fecha_corte.toolTip()` vacíos hoy;
`campo_radicado.property("class")` nunca cambia a `"invalid"` porque no hay ninguna conexión a
`textChanged` todavía).

- [ ] **Step 4: Agregar tooltips a los 6 campos en el `__init__` de `ExpedienteFormDialog`**

Inmediatamente después de la construcción de cada campo (adaptar el punto de inserción exacto al
contenido real del archivo — ver "Nota de integración"), agregar una llamada `.setToolTip(...)` por
campo:

```python
        self.campo_radicado.setToolTip(
            "Numero de radicado judicial del proceso, tal como aparece en el expediente "
            "fisico o electronico del despacho."
        )
        self.campo_demandante.setToolTip("Nombre completo de la parte demandante (o accionante).")
        self.campo_demandado.setToolTip("Nombre completo de la parte demandada (o accionada).")
        self.combo_area.setToolTip(
            "Area del derecho del proceso -- determina que campos y reglas de calculo "
            "aplican al crear obligaciones dentro de este expediente."
        )
        self.campo_juzgado.setToolTip("Despacho judicial que conoce del proceso (opcional).")
        self.campo_fecha_corte.setToolTip(
            "Fecha hasta la que se calculan los intereses por defecto al liquidar este "
            "expediente."
        )
```

- [ ] **Step 5: Agregar los helpers de marcado y la validación en tiempo real del radicado**

Agregar 2 métodos nuevos en `ExpedienteFormDialog` (después de `guardar()` y antes de
`_guardar_y_cerrar`, o en el lugar equivalente si el archivo real ya insertó otros métodos ahí por el
Sprint 35 — lo único que importa es que queden dentro de la clase `ExpedienteFormDialog`):

```python
    def _marcar_campo_invalido(self, campo: QLineEdit, mensaje: str) -> None:
        campo.setProperty("class", "invalid")
        campo.setToolTip(mensaje)
        campo.style().unpolish(campo)
        campo.style().polish(campo)

    def _marcar_campo_valido(self, campo: QLineEdit, tooltip_original: str) -> None:
        campo.setProperty("class", "")
        campo.setToolTip(tooltip_original)
        campo.style().unpolish(campo)
        campo.style().polish(campo)

    def _validar_radicado_en_tiempo_real(self) -> None:
        tooltip_original = (
            "Numero de radicado judicial del proceso, tal como aparece en el expediente "
            "fisico o electronico del despacho."
        )
        if not self.campo_radicado.text().strip():
            self._marcar_campo_invalido(self.campo_radicado, "El radicado es obligatorio.")
        else:
            self._marcar_campo_valido(self.campo_radicado, tooltip_original)
```

Y, al final del `__init__` (después de la última conexión de señal existente, o donde el archivo real
la tenga), agregar:

```python
        self.campo_radicado.textChanged.connect(self._validar_radicado_en_tiempo_real)
```

- [ ] **Step 6: Correr los tests para verificar que pasan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_expedientes.py -v`
Expected: todos PASS (los tests preexistentes de `ExpedienteFormDialog`/`ExpedientesListView` — sin
cambio de comportamiento — más los 3 tests nuevos del Step 2).

- [ ] **Step 7: Ruff**

Run: `"<python>" -m ruff check app/views/expedientes.py tests/views/test_expedientes.py`
Expected: no errors nuevos introducidos por este task (si el archivo ya tenía deuda de lint
preexistente de los Sprints 31/35, no es responsabilidad de este task corregirla — igual que el
criterio usado en la Task 2 Step 10 del Sprint 26).

- [ ] **Step 8: Commit**

```bash
git add app/views/expedientes.py tests/views/test_expedientes.py
git commit -m "$(cat <<'EOF'
feat(sprint34): agregar tooltips y validacion en tiempo real del radicado en ExpedienteFormDialog

EOF
)"
```

---

### Task 4: Suite completa, ruff y cierre del sprint en `Pendientes.md`

**Files:**
- Modify: `Pendientes.md` (sección "Sprint 34" e índice)

- [ ] **Step 1: Correr toda la suite del proyecto**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest -v`
Expected: todos los tests en verde (los ~16 nuevos de este plan — 2 de Task 1, ~10 de Task 2, 3 de
Task 3 — más los existentes, sin cambios de comportamiento en los casos ya cubiertos por sprints
anteriores).

- [ ] **Step 2: Ruff sobre todo el repo**

Run: `"<python>" -m ruff check .`
Expected: sin errores nuevos atribuibles a los archivos tocados por este plan
(`app/views/icons.py`, `app/views/obligaciones.py`, `app/views/expedientes.py`,
`tests/views/test_icons.py`, `tests/views/test_obligaciones.py`, `tests/views/test_expedientes.py`).
Si el repo ya traía deuda de lint preexistente en otros archivos no tocados por este plan (como
documentan los Sprints 26/27/28), no es responsabilidad de este sprint corregirla — confirmar
comparando contra un `git stash`/`ruff check .` del estado previo, igual que el criterio usado en el
Sprint 26 Task 4 Step 2.

- [ ] **Step 3: Actualizar el índice de `Pendientes.md`**

Cambiar la línea del índice:

```
- [Sprint 34 — UX de formularios: agrupación, ayuda contextual y feedback en tiempo real 📋 Pendiente](#sprint-34--ux-de-formularios-agrupación-ayuda-contextual-y-feedback-en-tiempo-real--pendiente)
```

a:

```
- [Sprint 34 — UX de formularios: agrupación, ayuda contextual y feedback en tiempo real ✅ Completado](#sprint-34--ux-de-formularios-agrupación-ayuda-contextual-y-feedback-en-tiempo-real--completado)
```

- [ ] **Step 4: Actualizar el encabezado de la sección y agregar el bloque de cierre**

Cambiar el encabezado de la sección:

```
## Sprint 34 — UX de formularios: agrupación, ayuda contextual y feedback en tiempo real 📋 Pendiente
```

a:

```
## Sprint 34 — UX de formularios: agrupación, ayuda contextual y feedback en tiempo real ✅ Completado
```

Y, en esa misma sección, inmediatamente antes de la línea `**Definición de Hecho:**`, agregar (mismo
formato de cierre usado en el Sprint 24):

```markdown
**Estado:** Implementado (2026-08-06) — ver
`docs/superpowers/plans/2026-08-06-sprint34-ux-formularios.md`. Decisiones tomadas durante la
implementación (no asumidas unilateralmente por el sprint anterior):
- Se eligieron secciones colapsables (`QGroupBox` checkeable) en vez de `QTabWidget` para
  "Datos básicos"/"Tasas e intereses"/"Honorarios y costas": un `QTabWidget` solo mantiene visible la
  página de la pestaña activa (`QWidget.isVisible()` da `False` para todo lo que esté en una pestaña
  no seleccionada), lo que habría roto las ~15 aserciones `campo.isVisible()` que ya existían en
  `tests/views/test_obligaciones.py` desde antes de este sprint. Los `QGroupBox` apilados permiten que
  varias secciones estén visibles en simultáneo, preservando ese contrato de tests intacto.
- El feedback de validación en tiempo real (Task 2) se conectó únicamente a los 3 campos genéricos que
  el Sprint 24 ya validaba en la ruta común de `guardar()` (concepto, valor, tasa efectiva anual) — no
  se extendió a los campos específicos por área (cuota litis, IBC vigente, tasa moratoria, etc.) para
  mantener el alcance de este sprint acotado a presentación/interacción, tal como pide la sección
  "Alcance explícitamente excluido" del hallazgo original; esos campos siguen validándose solo al
  guardar, con el `QMessageBox` ya existente del Sprint 24.
- `ExpedienteFormDialog` recibió tooltips en sus 6 campos y validación en tiempo real solo del
  radicado (su único campo obligatorio) — el resto de sus campos no tiene reglas de validación propias
  que exponer en tiempo real (área/fecha de corte siempre tienen un valor por defecto válido;
  demandante/demandado/juzgado no tienen restricciones de formato).

```

- [ ] **Step 5: Commit**

```bash
git add Pendientes.md
git commit -m "$(cat <<'EOF'
docs(sprint34): cerrar sprint de UX de formularios en Pendientes.md

EOF
)"
```

---

## Self-review notes

- **Cobertura del spec:** reorganización en secciones colapsables mostrando solo lo relevante por
  área/tipo (Task 2, `QGroupBox` + visibilidad de contenedores/grupos); tooltips explicando el
  significado legal de campos técnicos (Task 2 para `ObligacionFormDialog`, Task 3 para
  `ExpedienteFormDialog`); feedback visual en tiempo real con borde rojo + ícono de advertencia
  conectado a la validación del Sprint 24 en vez de solo `QMessageBox` al guardar (Task 2, reutiliza
  verbatim `_validar_concepto_no_vacio`/`_validar_rango`); ícono informativo junto al campo de tasa
  explicando el origen del valor por defecto con el texto exacto pedido por el hallazgo
  ("Valor por defecto: interés civil legal, Art. 1617 C.C.") (Task 2); infraestructura de íconos nueva
  siguiendo el mecanismo hecho a mano del Sprint 31 (Task 1).
- **Sin rediseño de modelo de datos ni reglas de validación:** ninguna task modifica
  `database/models.py`, `app/services/parametro_service.py`, ni los mensajes/umbrales de
  `_validar_rango`/`_validar_concepto_no_vacio`/`_validar_fecha_no_posterior_a_corte` del Sprint 24 —
  solo se les agregan wrappers de UI que capturan el mismo `ValueError` ya existente.
- **Compatibilidad con tests preexistentes:** se identificó explícitamente el riesgo de que envolver
  `campo_valor`/`campo_tasa` en un contenedor rompiera las ~15 aserciones `isVisible()` ya existentes
  en `tests/views/test_obligaciones.py`, y se resolvió apuntando las llamadas `setVisible()`
  dinámicas al contenedor (no al `QLineEdit` interno) en los 2 únicos puntos donde eso importa
  (`__init__` y `_actualizar_campos_tributario`) — `QWidget.isVisible()` de Qt ya compone
  automáticamente el estado propio del widget con el de todos sus ancestros, así que
  `campo_valor.isVisible()`/`campo_tasa.isVisible()` siguen reportando exactamente lo mismo que antes
  del sprint sin necesitar ningún cambio en esas aserciones.
- **Nota de integración honesta:** se identificó que `ExpedienteFormDialog` y `ExpedientesListView`
  comparten archivo con el Sprint 35 (que se ejecuta antes en el mismo branch) y se documentó
  explícitamente al inicio del plan, en vez de fingir certeza sobre líneas exactas que este plan no
  puede conocer de antemano.
- **Sin placeholders:** cada paso trae el código completo a pegar (incluido el `__init__` completo de
  ~230 líneas de `ObligacionFormDialog` en la Task 2, antes y después) — ninguna instrucción del tipo
  "agregar la lógica correspondiente" sin el código real.
