# Configuraciones + Apariencia Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the sidebar entry "Parametros" to "Configuraciones", turn it into a Settings-style screen with a left submenu (Parámetros / Apariencia, room for more later), and move the dark/light mode toggle out of the parameters table into the new "Apariencia" section.

**Architecture:** Two new PySide6 widget files (`AparienciaView`, `ConfiguracionesView`) compose the existing `ParametrosView` unchanged (minus its theme checkbox). `MainWindow` swaps its `boton_parametros`/`parametros_page` for `boton_configuraciones`/`configuraciones_page`, and the breadcrumb reads the active sub-section from `ConfiguracionesView` via a Qt signal.

**Tech Stack:** Python, PySide6 (Qt for Python), pytest + pytest-qt.

**Design doc:** `docs/superpowers/specs/2026-08-13-configuraciones-apariencia-design.md`

---

## Task dependency graph (for parallel execution)

```
Task 1 (AparienciaView)  ─┐
                           ├─→ Task 3 (ConfiguracionesView) ─→ Task 4 (MainWindow wiring) ─→ Task 5 (Docs + Pendientes.md)
Task 2 (strip ParametrosView)─┘
```

- **Task 1** and **Task 2** touch disjoint files and share no state — dispatch them **in parallel**.
- **Task 3** must wait for both 1 and 2 (it imports both `AparienciaView` and the cleaned-up `ParametrosView`).
- **Task 4** must wait for Task 3 (it imports `ConfiguracionesView`).
- **Task 5** must wait for Task 4 (it documents the final button/breadcrumb text) — run it alone, not in parallel with anything.

All commands below assume the repo root as working directory and the project's virtualenv. On a machine without a display, prefix pytest with `QT_QPA_PLATFORM=offscreen` (see `CONTRIBUTING.md`).

---

### Task 1: `AparienciaView` (new "Apariencia" section)

**Files:**
- Create: `app/views/apariencia.py`
- Test: `tests/views/test_apariencia.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/views/test_apariencia.py`:

```python
from PySide6.QtWidgets import QApplication, QLabel

from app.core.apariencia import MODO_CLARO, MODO_OSCURO, cargar_modo_tema, guardar_modo_tema
from app.views.apariencia import AparienciaView


def test_apariencia_view_casilla_modo_oscuro_arranca_desmarcada_por_defecto(qtbot):
    # Sin QSettings previo (tmp_path vacio por test) el modo por defecto es "claro".
    vista = AparienciaView()
    qtbot.addWidget(vista)

    assert vista.casilla_modo_oscuro.isChecked() is False


def test_apariencia_view_casilla_modo_oscuro_refleja_el_modo_persistido(qtbot):
    guardar_modo_tema(MODO_OSCURO)

    vista = AparienciaView()
    qtbot.addWidget(vista)

    assert vista.casilla_modo_oscuro.isChecked() is True


def test_marcar_casilla_modo_oscuro_aplica_el_tema_en_caliente(qtbot):
    vista = AparienciaView()
    qtbot.addWidget(vista)

    vista.casilla_modo_oscuro.setChecked(True)

    assert "#1E1A18" in QApplication.instance().styleSheet()
    # Vuelve al modo claro para no filtrar estado hacia otros tests.
    vista.casilla_modo_oscuro.setChecked(False)


def test_marcar_casilla_modo_oscuro_persiste_la_eleccion(qtbot):
    vista = AparienciaView()
    qtbot.addWidget(vista)

    vista.casilla_modo_oscuro.setChecked(True)

    assert cargar_modo_tema() == MODO_OSCURO

    vista.casilla_modo_oscuro.setChecked(False)

    assert cargar_modo_tema() == MODO_CLARO


def test_apariencia_view_muestra_descripcion_del_interruptor(qtbot):
    vista = AparienciaView()
    qtbot.addWidget(vista)

    etiquetas = [hijo for hijo in vista.findChildren(QLabel)]
    assert any("tema" in etiqueta.text().lower() for etiqueta in etiquetas)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest tests/views/test_apariencia.py -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'app.views.apariencia'`

- [ ] **Step 3: Write the implementation**

Create `app/views/apariencia.py`:

```python
from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QVBoxLayout, QWidget

from app.core.apariencia import (
    MODO_CLARO,
    MODO_OSCURO,
    aplicar_tema,
    cargar_modo_tema,
    guardar_modo_tema,
)


class AparienciaView(QWidget):
    """Seccion "Apariencia" de Configuraciones (Sprint 66): aloja el interruptor
    de modo oscuro/claro, movido aqui desde ParametrosView (donde vivia de forma
    temporal desde el Sprint 50 -- ver app/views/configuracion.py)."""

    def __init__(self):
        super().__init__()

        self.casilla_modo_oscuro = QCheckBox("Modo oscuro")
        self.casilla_modo_oscuro.setChecked(cargar_modo_tema() == MODO_OSCURO)
        self.casilla_modo_oscuro.toggled.connect(self._alternar_modo_tema)

        descripcion = QLabel(
            "Cambia los colores de toda la aplicacion entre el tema claro (por defecto) y "
            "el tema oscuro, incluida la grafica del Dashboard. El cambio se aplica de "
            "inmediato, sin reiniciar el programa, y se recuerda la proxima vez que abras "
            "BASTIUM."
        )
        descripcion.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.casilla_modo_oscuro)
        layout.addWidget(descripcion)
        layout.addStretch()
        self.setLayout(layout)

    def _alternar_modo_tema(self, marcado: bool) -> None:
        """Aplica el tema en caliente (sin reiniciar la app) y persiste la
        eleccion -- ver `app.core.apariencia.aplicar_tema()`/`guardar_modo_tema()`."""
        modo = MODO_OSCURO if marcado else MODO_CLARO
        aplicar_tema(QApplication.instance(), modo)
        guardar_modo_tema(modo)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest tests/views/test_apariencia.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add app/views/apariencia.py tests/views/test_apariencia.py
git commit -m "feat: agregar AparienciaView con el interruptor de modo oscuro/claro"
```

---

### Task 2: Strip the theme checkbox out of `ParametrosView`

**Files:**
- Modify: `app/views/configuracion.py`
- Modify: `tests/views/test_configuracion.py`

This task only *removes* code that Task 1 already reproduced in `AparienciaView` — there is no new behavior to TDD here, so the verification step is "delete, then run the full file's suite and confirm everything else still passes."

- [ ] **Step 1: Remove the 4 obsolete tests from `tests/views/test_configuracion.py`**

Delete this block (currently right before `def test_enter_guarda_y_cierra_el_dialogo`):

```python
def test_parametros_view_casilla_modo_oscuro_arranca_desmarcada_por_defecto(qtbot):
    # Sin QSettings previo (tmp_path vacio por test) el modo por defecto es "claro".
    vista = ParametrosView()
    qtbot.addWidget(vista)

    assert vista.casilla_modo_oscuro.isChecked() is False


def test_parametros_view_casilla_modo_oscuro_refleja_el_modo_persistido(qtbot):
    guardar_modo_tema(MODO_OSCURO)

    vista = ParametrosView()
    qtbot.addWidget(vista)

    assert vista.casilla_modo_oscuro.isChecked() is True


def test_marcar_casilla_modo_oscuro_aplica_el_tema_en_caliente(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)

    vista.casilla_modo_oscuro.setChecked(True)

    assert "#1E1A18" in QApplication.instance().styleSheet()
    # Vuelve al modo claro para no filtrar estado hacia otros tests.
    vista.casilla_modo_oscuro.setChecked(False)


def test_marcar_casilla_modo_oscuro_persiste_la_eleccion(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)

    vista.casilla_modo_oscuro.setChecked(True)

    assert cargar_modo_tema() == MODO_OSCURO

    vista.casilla_modo_oscuro.setChecked(False)

    assert cargar_modo_tema() == MODO_CLARO


```

Also remove the now-unused import (line 9 of the file):

```python
from app.core.apariencia import MODO_CLARO, MODO_OSCURO, cargar_modo_tema, guardar_modo_tema
```

and the now-unused `QApplication` import from the `PySide6.QtWidgets` import block (it was only used by the deleted tests).

- [ ] **Step 2: Remove the checkbox and its handler from `app/views/configuracion.py`**

Replace:

```python
        self.boton_agregar = QPushButton("+ Agregar valor nuevo")
        self.boton_agregar.setProperty("class", "primary")
        self.boton_agregar.clicked.connect(self._abrir_dialogo_agregar)

        # Control de modo oscuro/claro (Sprint 50): vive en Parametros (no en la
        # barra/sidebar de navegacion) para que el Sprint 50 no tenga que moverlo
        # de nuevo si el sidebar de esa misma tarea reorganiza la navegacion.
        # Arranca reflejando el modo persistido via QSettings (mismo patron de
        # app.core.apariencia.cargar_modo_tema(), que reutiliza
        # MainWindow._crear_settings() del Sprint 37).
        self.casilla_modo_oscuro = QCheckBox("Modo oscuro")
        self.casilla_modo_oscuro.setChecked(cargar_modo_tema() == MODO_OSCURO)
        self.casilla_modo_oscuro.toggled.connect(self._alternar_modo_tema)

        botones = QHBoxLayout()
        botones.addWidget(self.boton_agregar)
        botones.addStretch()
        botones.addWidget(self.casilla_modo_oscuro)

        layout = QVBoxLayout()
        layout.addLayout(botones)
        layout.addWidget(self.tabla)
        self.setLayout(layout)

        self.refrescar()

    def _alternar_modo_tema(self, marcado: bool) -> None:
        """Aplica el tema en caliente (sin reiniciar la app) y persiste la
        eleccion -- ver `app.core.apariencia.aplicar_tema()`/`guardar_modo_tema()`
        (Sprint 50)."""
        modo = MODO_OSCURO if marcado else MODO_CLARO
        aplicar_tema(QApplication.instance(), modo)
        guardar_modo_tema(modo)

    def refrescar(self) -> None:
```

with:

```python
        self.boton_agregar = QPushButton("+ Agregar valor nuevo")
        self.boton_agregar.setProperty("class", "primary")
        self.boton_agregar.clicked.connect(self._abrir_dialogo_agregar)

        botones = QHBoxLayout()
        botones.addWidget(self.boton_agregar)

        layout = QVBoxLayout()
        layout.addLayout(botones)
        layout.addWidget(self.tabla)
        self.setLayout(layout)

        self.refrescar()

    def refrescar(self) -> None:
```

And remove the now-unused import block at the top of the file:

```python
from app.core.apariencia import (
    MODO_CLARO,
    MODO_OSCURO,
    aplicar_tema,
    cargar_modo_tema,
    guardar_modo_tema,
)
```

`QCheckBox` stays imported (still used by `ParametroFormDialog.casillas_area`). `QApplication` is removed from the `PySide6.QtWidgets` import list in this file (no longer used here).

- [ ] **Step 3: Run the file's test suite to confirm nothing else depended on the checkbox**

Run: `QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest tests/views/test_configuracion.py -v`
Expected: PASS (all remaining tests green, no `AttributeError: 'ParametrosView' object has no attribute 'casilla_modo_oscuro'` anywhere)

- [ ] **Step 4: Commit**

```bash
git add app/views/configuracion.py tests/views/test_configuracion.py
git commit -m "refactor: sacar el interruptor de modo oscuro/claro de ParametrosView"
```

---

### Task 3: `ConfiguracionesView` (submenu + content stack)

**Depends on:** Task 1 and Task 2 both merged.

**Files:**
- Create: `app/views/configuraciones.py`
- Test: `tests/views/test_configuraciones.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/views/test_configuraciones.py`:

```python
from app.views.configuraciones import ConfiguracionesView


def test_configuraciones_view_arranca_en_la_seccion_parametros(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    assert vista.seccion_actual == "parametros"
    assert vista._stack_secciones.currentWidget() is vista.parametros_view


def test_configuraciones_view_mostrar_apariencia_cambia_de_seccion(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    vista.mostrar_apariencia()

    assert vista.seccion_actual == "apariencia"
    assert vista._stack_secciones.currentWidget() is vista.apariencia_view


def test_configuraciones_view_click_en_boton_apariencia_cambia_de_seccion(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    vista.boton_seccion_apariencia.click()

    assert vista.seccion_actual == "apariencia"


def test_configuraciones_view_click_en_boton_parametros_vuelve_a_parametros(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)
    vista.mostrar_apariencia()

    vista.boton_seccion_parametros.click()

    assert vista.seccion_actual == "parametros"


def test_configuraciones_view_mostrar_parametros_refresca_la_tabla(qtbot, monkeypatch):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    llamadas = []
    monkeypatch.setattr(vista.parametros_view, "refrescar", lambda: llamadas.append(1))

    vista.mostrar_parametros()

    assert llamadas == [1]


def test_configuraciones_view_emite_seccion_cambiada_al_cambiar_de_seccion(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    recibidas = []
    vista.seccion_cambiada.connect(recibidas.append)

    vista.mostrar_apariencia()
    vista.mostrar_parametros()

    assert recibidas == ["apariencia", "parametros"]


def test_configuraciones_view_boton_parametros_activo_por_defecto(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    assert vista.boton_seccion_parametros.property("class") == "primary"
    assert vista.boton_seccion_apariencia.property("class") == "secondary"


def test_configuraciones_view_boton_apariencia_activo_al_seleccionarla(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    vista.mostrar_apariencia()

    assert vista.boton_seccion_apariencia.property("class") == "primary"
    assert vista.boton_seccion_parametros.property("class") == "secondary"


def test_configuraciones_view_etiqueta_seccion_actual(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    assert vista.etiqueta_seccion_actual() == "Parámetros"

    vista.mostrar_apariencia()

    assert vista.etiqueta_seccion_actual() == "Apariencia"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest tests/views/test_configuraciones.py -v`
Expected: FAIL/ERROR — `ModuleNotFoundError: No module named 'app.views.configuraciones'`

- [ ] **Step 3: Write the implementation**

Create `app/views/configuraciones.py`:

```python
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.views.apariencia import AparienciaView
from app.views.configuracion import ParametrosView

SECCION_PARAMETROS = "parametros"
SECCION_APARIENCIA = "apariencia"

_ETIQUETA_POR_SECCION = {
    SECCION_PARAMETROS: "Parámetros",
    SECCION_APARIENCIA: "Apariencia",
}


class ConfiguracionesView(QWidget):
    """Pantalla "Configuraciones" (Sprint 66): submenu lateral estilo Ajustes
    (Parametros, Apariencia, con espacio para futuras secciones) + panel de
    contenido que alterna entre ellas segun la seccion elegida. Reemplaza el
    acceso directo que antes llevaba de un clic del sidebar principal
    directamente a ParametrosView."""

    # Emitida cada vez que cambia la seccion activa (mostrar_parametros()/
    # mostrar_apariencia()), con el nombre de la nueva seccion -- MainWindow la
    # usa para mantener el breadcrumb sincronizado sin que esta clase conozca
    # nada sobre breadcrumbs.
    seccion_cambiada = Signal(str)

    def __init__(self):
        super().__init__()
        self._seccion_actual = SECCION_PARAMETROS

        self.parametros_view = ParametrosView()
        self.apariencia_view = AparienciaView()

        self.boton_seccion_parametros = QPushButton(" Parámetros")
        self.boton_seccion_parametros.clicked.connect(self.mostrar_parametros)

        self.boton_seccion_apariencia = QPushButton(" Apariencia")
        self.boton_seccion_apariencia.clicked.connect(self.mostrar_apariencia)

        submenu = QWidget()
        layout_submenu = QVBoxLayout(submenu)
        layout_submenu.addWidget(self.boton_seccion_parametros)
        layout_submenu.addWidget(self.boton_seccion_apariencia)
        layout_submenu.addStretch()

        self._stack_secciones = QStackedWidget()
        self._stack_secciones.addWidget(self.parametros_view)
        self._stack_secciones.addWidget(self.apariencia_view)

        layout = QHBoxLayout()
        layout.addWidget(submenu)
        layout.addWidget(self._stack_secciones, stretch=1)
        self.setLayout(layout)

        self._actualizar_estado_activo_submenu()

    @property
    def seccion_actual(self) -> str:
        return self._seccion_actual

    def etiqueta_seccion_actual(self) -> str:
        return _ETIQUETA_POR_SECCION[self._seccion_actual]

    def mostrar_parametros(self) -> None:
        self._seccion_actual = SECCION_PARAMETROS
        self._stack_secciones.setCurrentWidget(self.parametros_view)
        self.parametros_view.refrescar()
        self._actualizar_estado_activo_submenu()
        self.seccion_cambiada.emit(self._seccion_actual)

    def mostrar_apariencia(self) -> None:
        self._seccion_actual = SECCION_APARIENCIA
        self._stack_secciones.setCurrentWidget(self.apariencia_view)
        self._actualizar_estado_activo_submenu()
        self.seccion_cambiada.emit(self._seccion_actual)

    def _actualizar_estado_activo_submenu(self) -> None:
        # Misma convencion class="primary"/"secondary" que usa el sidebar
        # principal (MainWindow._actualizar_estado_activo_navegacion) para
        # resaltar la seccion activa -- unpolish()/polish() manual porque el
        # cambio ocurre en tiempo de ejecucion, despues del primer show().
        self.boton_seccion_parametros.setProperty(
            "class", "primary" if self._seccion_actual == SECCION_PARAMETROS else "secondary"
        )
        self.boton_seccion_parametros.style().unpolish(self.boton_seccion_parametros)
        self.boton_seccion_parametros.style().polish(self.boton_seccion_parametros)
        self.boton_seccion_apariencia.setProperty(
            "class", "primary" if self._seccion_actual == SECCION_APARIENCIA else "secondary"
        )
        self.boton_seccion_apariencia.style().unpolish(self.boton_seccion_apariencia)
        self.boton_seccion_apariencia.style().polish(self.boton_seccion_apariencia)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest tests/views/test_configuraciones.py -v`
Expected: PASS (9 passed)

- [ ] **Step 5: Run the full suite once to catch cross-file regressions**

Run: `QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest -q`
Expected: PASS (`main_window.py` still imports `ParametrosView` directly at this point, so it is untouched and unaffected by this task)

- [ ] **Step 6: Commit**

```bash
git add app/views/configuraciones.py tests/views/test_configuraciones.py
git commit -m "feat: agregar ConfiguracionesView con submenu Parametros/Apariencia"
```

---

### Task 4: Wire `MainWindow` to `ConfiguracionesView`

**Depends on:** Task 3 merged.

**Files:**
- Modify: `app/views/main_window.py`
- Modify: `app/views/icons.py:17` (docstring wording only)
- Modify: `tests/views/test_main_window.py`

- [ ] **Step 1: Update `tests/views/test_main_window.py` first (this is the "failing test" for this task)**

Replace the import line:

```python
from app.views.main_window import MainWindow
```

stays the same (no change needed there).

Replace this test:

```python
def test_boton_parametros_navega_a_la_pantalla_de_parametros(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.boton_parametros.click()

    assert window.stacked_widget.currentWidget() is window.parametros_page
```

with:

```python
def test_boton_configuraciones_navega_a_la_pantalla_de_configuraciones(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.boton_configuraciones.click()

    assert window.stacked_widget.currentWidget() is window.configuraciones_page
```

Replace this test:

```python
def test_botones_de_navegacion_tienen_icono(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert not window.boton_volver.icon().isNull()
    assert not window.boton_inicio.icon().isNull()
    assert not window.boton_parametros.icon().isNull()
```

with:

```python
def test_botones_de_navegacion_tienen_icono(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert not window.boton_volver.icon().isNull()
    assert not window.boton_inicio.icon().isNull()
    assert not window.boton_configuraciones.icon().isNull()
```

Replace this test:

```python
def test_breadcrumb_muestra_parametros_en_la_pantalla_de_parametros(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("parametros")

    assert window.etiqueta_breadcrumb.text() == "Parámetros"
```

with:

```python
def test_breadcrumb_muestra_configuraciones_parametros_en_la_pantalla_de_configuraciones(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("configuraciones")

    assert window.etiqueta_breadcrumb.text() == "Configuraciones › Parámetros"


def test_breadcrumb_actualiza_al_cambiar_de_seccion_dentro_de_configuraciones(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("configuraciones")
    window.configuraciones_page.mostrar_apariencia()

    assert window.etiqueta_breadcrumb.text() == "Configuraciones › Apariencia"
```

Replace this test:

```python
def test_boton_parametros_activo_en_la_pantalla_de_parametros(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("parametros")

    assert window.boton_parametros.property("class") == "primary"
```

with:

```python
def test_boton_configuraciones_activo_en_la_pantalla_de_configuraciones(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("configuraciones")

    assert window.boton_configuraciones.property("class") == "primary"
```

Replace this test:

```python
def test_boton_parametros_inactivo_en_otras_pantallas(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.boton_parametros.property("class") == "secondary"

    window.show_page("detalle")

    assert window.boton_parametros.property("class") == "secondary"
```

with:

```python
def test_boton_configuraciones_inactivo_en_otras_pantallas(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.boton_configuraciones.property("class") == "secondary"

    window.show_page("detalle")

    assert window.boton_configuraciones.property("class") == "secondary"
```

Replace this test:

```python
def test_boton_parametros_deja_de_estar_activo_al_salir_de_parametros(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("parametros")
    assert window.boton_parametros.property("class") == "primary"

    window._ir_inicio()

    assert window.boton_parametros.property("class") == "secondary"
```

with:

```python
def test_boton_configuraciones_deja_de_estar_activo_al_salir_de_configuraciones(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("configuraciones")
    assert window.boton_configuraciones.property("class") == "primary"

    window._ir_inicio()

    assert window.boton_configuraciones.property("class") == "secondary"
```

In `test_sidebar_aloja_los_botones_de_navegacion_y_el_stacked_widget_sigue_visible`, replace:

```python
    for boton in (window.boton_volver, window.boton_inicio, window.boton_parametros):
```

with:

```python
    for boton in (window.boton_volver, window.boton_inicio, window.boton_configuraciones):
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest tests/views/test_main_window.py -v`
Expected: FAIL — `AttributeError: 'MainWindow' object has no attribute 'boton_configuraciones'` (and similar) on the tests just changed.

- [ ] **Step 3: Update `app/views/main_window.py`**

Replace the import:

```python
from app.views.configuracion import ParametrosView
```

with:

```python
from app.views.configuraciones import ConfiguracionesView
```

Replace:

```python
        self.parametros_page = ParametrosView()

        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.expedientes_page)
        self.stacked_widget.addWidget(self.detalle_page)
        self.stacked_widget.addWidget(self.resultado_page)
        self.stacked_widget.addWidget(self.parametros_page)

        self._pages = {
            "dashboard": self.dashboard_page,
            "expedientes": self.expedientes_page,
            "detalle": self.detalle_page,
            "resultado": self.resultado_page,
            "parametros": self.parametros_page,
        }
```

with:

```python
        self.configuraciones_page = ConfiguracionesView()

        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.expedientes_page)
        self.stacked_widget.addWidget(self.detalle_page)
        self.stacked_widget.addWidget(self.resultado_page)
        self.stacked_widget.addWidget(self.configuraciones_page)

        self._pages = {
            "dashboard": self.dashboard_page,
            "expedientes": self.expedientes_page,
            "detalle": self.detalle_page,
            "resultado": self.resultado_page,
            "configuraciones": self.configuraciones_page,
        }
```

Replace:

```python
        self.boton_parametros = QPushButton(" Parametros")
        self.boton_parametros.setIcon(icon("settings"))
        self.boton_parametros.setProperty("class", "secondary")
        self.boton_parametros.clicked.connect(self._ir_a_parametros)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar_navegacion")
        layout_sidebar = QVBoxLayout(sidebar)
        layout_sidebar.addWidget(self.boton_inicio)
        layout_sidebar.addWidget(self.boton_volver)
        layout_sidebar.addWidget(self.boton_parametros)
        layout_sidebar.addStretch()
```

with:

```python
        self.boton_configuraciones = QPushButton(" Configuraciones")
        self.boton_configuraciones.setIcon(icon("settings"))
        self.boton_configuraciones.setProperty("class", "secondary")
        self.boton_configuraciones.clicked.connect(self._ir_a_configuraciones)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar_navegacion")
        layout_sidebar = QVBoxLayout(sidebar)
        layout_sidebar.addWidget(self.boton_inicio)
        layout_sidebar.addWidget(self.boton_volver)
        layout_sidebar.addWidget(self.boton_configuraciones)
        layout_sidebar.addStretch()
```

A few lines below, connect the breadcrumb to section changes inside Configuraciones (add this right after `self._actualizar_botones_navegacion()` at the end of `_crear_barra_navegacion`):

```python
        self._actualizar_botones_navegacion()
        self.configuraciones_page.seccion_cambiada.connect(
            lambda _seccion: self._actualizar_breadcrumb()
        )
```

Replace:

```python
    def _texto_breadcrumb(self) -> str:
        if self._current_page_name == "parametros":
            return "Parámetros"
```

with:

```python
    def _texto_breadcrumb(self) -> str:
        if self._current_page_name == "configuraciones":
            return f"Configuraciones › {self.configuraciones_page.etiqueta_seccion_actual()}"
```

Replace:

```python
        # boton_parametros es el unico boton de la barra que representa una pantalla fija
        # a la que el usuario puede "estar": Volver es una accion sin pantalla propia
        # (depende del historial) e Inicio se oculta justo cuando el usuario ya esta en
        # "expedientes" (nunca tendria sentido marcarlo "activo"). Se reutiliza la
        # convencion class="primary" del Sprint 31 (resources/theme.qss) para el estado
        # activo; fuera de "parametros" vuelve a "secondary" (su estilo neutral de
        # reposo, ver Sprint 36). A diferencia del Sprint 31 (que fijaba la propiedad
        # una sola vez en __init__, antes del primer show), aca el cambio ocurre en
        # tiempo de ejecucion despues de que la ventana ya se mostro, asi que hace falta
        # unpolish()/polish() manual para que Qt vuelva a evaluar el selector QSS.
        self.boton_parametros.setProperty(
            "class", "primary" if self._current_page_name == "parametros" else "secondary"
        )
        self.boton_parametros.style().unpolish(self.boton_parametros)
        self.boton_parametros.style().polish(self.boton_parametros)
```

with:

```python
        # boton_configuraciones es el unico boton de la barra que representa una pantalla
        # fija a la que el usuario puede "estar": Volver es una accion sin pantalla propia
        # (depende del historial) e Inicio se oculta justo cuando el usuario ya esta en
        # "expedientes" (nunca tendria sentido marcarlo "activo"). Se reutiliza la
        # convencion class="primary" del Sprint 31 (resources/theme.qss) para el estado
        # activo; fuera de "configuraciones" vuelve a "secondary" (su estilo neutral de
        # reposo, ver Sprint 36). A diferencia del Sprint 31 (que fijaba la propiedad
        # una sola vez en __init__, antes del primer show), aca el cambio ocurre en
        # tiempo de ejecucion despues de que la ventana ya se mostro, asi que hace falta
        # unpolish()/polish() manual para que Qt vuelva a evaluar el selector QSS.
        self.boton_configuraciones.setProperty(
            "class", "primary" if self._current_page_name == "configuraciones" else "secondary"
        )
        self.boton_configuraciones.style().unpolish(self.boton_configuraciones)
        self.boton_configuraciones.style().polish(self.boton_configuraciones)
```

Replace:

```python
    def _ir_a_parametros(self) -> None:
        self.parametros_page.refrescar()
        self.show_page("parametros")
```

with:

```python
    def _ir_a_configuraciones(self) -> None:
        self.configuraciones_page.mostrar_parametros()
        self.show_page("configuraciones")
```

Finally, update the docstring of `_crear_barra_navegacion` (currently lists `boton_volver`, `boton_inicio`, `boton_parametros`, `etiqueta_breadcrumb` as the attribute names kept stable for tests) to say `boton_configuraciones` instead of `boton_parametros`.

- [ ] **Step 4: Update the icon docstring in `app/views/icons.py:17`**

Replace:

```python
    Nombres validos: "home" (Inicio), "back" (Volver), "settings" (Parametros),
```

with:

```python
    Nombres validos: "home" (Inicio), "back" (Volver), "settings" (Configuraciones),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest tests/views/test_main_window.py -v`
Expected: PASS (all tests in the file green, including the 2 new/renamed breadcrumb tests)

- [ ] **Step 6: Run the full suite**

Run: `QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest -q`
Expected: PASS, 0 failed

- [ ] **Step 7: Lint**

Run: `.venv/Scripts/python.exe -m ruff check .`
Expected: no errors (unused imports removed in Tasks 2/4 should already prevent `F401`)

- [ ] **Step 8: Commit**

```bash
git add app/views/main_window.py app/views/icons.py tests/views/test_main_window.py
git commit -m "feat: renombrar el sidebar de Parametros a Configuraciones"
```

---

### Task 5: Documentation + `docs/Pendientes.md`

**Depends on:** Task 4 merged. Do not run in parallel with anything else — it's the closing task and needs the final, real state of the other four.

**Files:**
- Modify: `README.md`
- Modify: `docs/GUIA_USUARIO.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/Pendientes.md`

- [ ] **Step 1: `README.md`**

Replace:

```markdown
La interfaz tiene navegación por panel lateral fijo, modo oscuro/claro alternable desde "⚙ Parámetros"
(persistido entre sesiones), notificaciones no bloqueantes tipo toast para confirmaciones de bajo riesgo,
```

with:

```markdown
La interfaz tiene navegación por panel lateral fijo, modo oscuro/claro alternable desde "⚙ Configuraciones
→ Apariencia" (persistido entre sesiones), notificaciones no bloqueantes tipo toast para confirmaciones de
bajo riesgo,
```

Replace:

```markdown
✅ **Parámetros legales versionados:** desde la pantalla "⚙ Parámetros" cualquier abogado puede consultar
```

with:

```markdown
✅ **Parámetros legales versionados:** desde "⚙ Configuraciones → Parámetros" cualquier abogado puede consultar
```

- [ ] **Step 2: `docs/GUIA_USUARIO.md` — header block (lines ~10-11)**

Replace:

```markdown
> navegación lateral fijo (sidebar) con los botones Volver/Inicio/Parámetros con íconos y estado activo,
> el modo oscuro/claro alternable desde Parámetros, el breadcrumb de contexto y los atajos de teclado de
```

with:

```markdown
> navegación lateral fijo (sidebar) con los botones Volver/Inicio/Configuraciones con íconos y estado
> activo, la pantalla "Configuraciones" con submenú Parámetros/Apariencia (el modo oscuro/claro se movió a
> Apariencia en el Sprint 66), el breadcrumb de contexto y los atajos de teclado de
```

- [ ] **Step 3: `docs/GUIA_USUARIO.md` — section 4 tour intro**

Replace:

```markdown
BASTIUM tiene **5 pantallas**. Te mueves entre la mayoría automáticamente según lo que hagas; a la de
Parámetros se entra con un botón del panel lateral de navegación (sidebar), siempre visible a la
izquierda de la ventana:
```

with:

```markdown
BASTIUM tiene **5 pantallas**. Te mueves entre la mayoría automáticamente según lo que hagas; a la de
Configuraciones se entra con un botón del panel lateral de navegación (sidebar), siempre visible a la
izquierda de la ventana:
```

- [ ] **Step 4: `docs/GUIA_USUARIO.md` — item 5 of the tour**

Replace:

```markdown
5. **⚙ Parámetros** — la pantalla de parámetros legales versionados (tasas, topes, plazos e indicadores
   históricos). Se abre desde el botón **"⚙ Parámetros"** del panel lateral de navegación, disponible
   siempre, sin importar en qué otra pantalla estés. Ver [sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros)
   para el detalle completo.
```

with:

```markdown
5. **⚙ Configuraciones** — pantalla con dos secciones, elegibles desde un submenú lateral propio:
   **Parámetros** (tasas, topes, plazos e indicadores históricos legales) y **Apariencia** (el interruptor
   de modo oscuro/claro). Se abre desde el botón **"⚙ Configuraciones"** del panel lateral de navegación,
   disponible siempre, sin importar en qué otra pantalla estés, y entra mostrando Parámetros por defecto.
   Ver [sección 5.14](#514-editar-tasas-y-topes-legales-configuraciones--parámetros) para el detalle
   completo de Parámetros.
```

- [ ] **Step 5: `docs/GUIA_USUARIO.md` — sidebar bullet list**

Replace:

```markdown
- **Parámetros** — siempre visible, en cualquier pantalla; te lleva a la pantalla de parámetros legales
  versionados (ver punto 5 arriba). Se resalta con el color de marca de BASTIUM mientras estás dentro de
  esa pantalla, para que sea evidente cuál tienes abierta.
```

with:

```markdown
- **Configuraciones** (Sprint 66 — antes se llamaba "Parámetros") — siempre visible, en cualquier
  pantalla; te lleva a la pantalla de Configuraciones (ver punto 5 arriba), que abre mostrando la sección
  Parámetros. Un submenú propio, dentro de esa misma pantalla, permite cambiar a la sección Apariencia sin
  volver a pasar por este botón. Se resalta con el color de marca de BASTIUM mientras estás dentro de esa
  pantalla, para que sea evidente cuál tienes abierta.
```

Also, in the same block, update the breadcrumb example sentence. Replace:

```markdown
qué expediente y pantalla estás parado en cada momento (por ejemplo, "Expedientes › Radicado
2026-00123 › Liquidación"):
```

with:

```markdown
qué expediente y pantalla estás parado en cada momento (por ejemplo, "Expedientes › Radicado
2026-00123 › Liquidación", o "Configuraciones › Apariencia"):
```

- [ ] **Step 6: `docs/GUIA_USUARIO.md` — tooltips paragraph**

Replace:

```markdown
abono** y **Agregar valor de parámetro** (pantalla "⚙ Parámetros") — muestran un ícono **ⓘ** junto a cada
```

with:

```markdown
abono** y **Agregar valor de parámetro** (sección "Parámetros" de "⚙ Configuraciones") — muestran un ícono
**ⓘ** junto a cada
```

- [ ] **Step 7: `docs/GUIA_USUARIO.md` — section 5.14 heading + intro + "Dónde está"**

Replace:

```markdown
### 5.14. Editar tasas y topes legales (pantalla "⚙ Parámetros")

Antes, si el multiplicador de usura, un tope de cuota litis, un plazo de prescripción o el valor del
SMLMV de un año nuevo cambiaban, había que pedirle a un programador que editara el código. Ya no: desde
la pantalla **"⚙ Parámetros"** cualquier abogado puede consultar y agregar esos valores directamente.

**Dónde está:** haz clic en el botón **"⚙ Parámetros"** del panel lateral de navegación (sidebar) — está
siempre visible, sin importar en qué pantalla estés (Lista de Expedientes, Detalle de Expediente o
Resultado de Liquidación).
```

with:

```markdown
### 5.14. Editar tasas y topes legales (Configuraciones → Parámetros)

Antes, si el multiplicador de usura, un tope de cuota litis, un plazo de prescripción o el valor del
SMLMV de un año nuevo cambiaban, había que pedirle a un programador que editara el código. Ya no: desde
la sección **"Parámetros"** de la pantalla **"⚙ Configuraciones"** cualquier abogado puede consultar y
agregar esos valores directamente.

**Dónde está:** haz clic en el botón **"⚙ Configuraciones"** del panel lateral de navegación (sidebar) —
está siempre visible, sin importar en qué pantalla estés (Lista de Expedientes, Detalle de Expediente o
Resultado de Liquidación), y entra mostrando la sección "Parámetros" por defecto. Si estás viendo la
sección "Apariencia", haz clic en **"Parámetros"** en el submenú de la izquierda.
```

- [ ] **Step 8: `docs/GUIA_USUARIO.md` — "Modo oscuro / claro" paragraph**

Replace:

```markdown
**Modo oscuro / claro (Sprint 50):** en la misma pantalla "⚙ Parámetros", junto al botón "+ Agregar valor
nuevo", hay una casilla **"Modo oscuro"**. Márcala para cambiar toda la aplicación a un tema oscuro
(incluida la gráfica del Dashboard, que recalcula sus colores para seguir siendo legible), o desmárcala
para volver al tema claro de siempre — el cambio se aplica de inmediato, sin reiniciar el programa, y
queda recordado para la próxima vez que lo abras.
```

with:

```markdown
**Modo oscuro / claro (Sprint 50, movido a Apariencia en el Sprint 66):** el interruptor **"Modo oscuro"**
ya no vive en esta pantalla — se movió a la sección **"Apariencia"** de "⚙ Configuraciones" (haz clic en
**"Apariencia"** en el submenú de la izquierda). Márcalo para cambiar toda la aplicación a un tema oscuro
(incluida la gráfica del Dashboard, que recalcula sus colores para seguir siendo legible), o desmárcalo
para volver al tema claro de siempre — el cambio se aplica de inmediato, sin reiniciar el programa, y
queda recordado para la próxima vez que abras BASTIUM.
```

- [ ] **Step 9: `docs/GUIA_USUARIO.md` — remaining 5 cross-references**

Replace (line ~846):

```markdown
pantalla **"⚙ Parámetros"**, ver [sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros).
```

with:

```markdown
sección "Parámetros" de la pantalla **"⚙ Configuraciones"**, ver
[sección 5.14](#514-editar-tasas-y-topes-legales-configuraciones--parámetros).
```

Replace (line ~910-911):

```markdown
  también se pueden consultar o corregir desde la pantalla "⚙ Parámetros" (claves `SMLMV` y `UVT`, ver
  [sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros)).
```

with:

```markdown
  también se pueden consultar o corregir desde la sección "Parámetros" de "⚙ Configuraciones" (claves
  `SMLMV` y `UVT`, ver [sección 5.14](#514-editar-tasas-y-topes-legales-configuraciones--parámetros)).
```

Replace (line ~926-927):

```markdown
  consultable y editable desde la pantalla "⚙ Parámetros" (ver
  [sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros)) sin tocar código.
```

with:

```markdown
  consultable y editable desde la sección "Parámetros" de "⚙ Configuraciones" (ver
  [sección 5.14](#514-editar-tasas-y-topes-legales-configuraciones--parámetros)) sin tocar código.
```

Replace (line ~1093-1096):

```markdown
- ✅ **Parámetros legales versionados** (pantalla "⚙ Parámetros") — el Sprint 13, planeado originalmente
  como un motor de reglas configurable de alcance mucho mayor, se reemplazó por este dominio más acotado:
  tasas, topes, plazos e indicadores históricos editables desde la GUI, con historial completo. Ver
  [sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros).
```

with:

```markdown
- ✅ **Parámetros legales versionados** (sección "Parámetros" de "⚙ Configuraciones") — el Sprint 13,
  planeado originalmente como un motor de reglas configurable de alcance mucho mayor, se reemplazó por
  este dominio más acotado: tasas, topes, plazos e indicadores históricos editables desde la GUI, con
  historial completo. Ver [sección 5.14](#514-editar-tasas-y-topes-legales-configuraciones--parámetros).
```

Replace (line ~1118-1119):

```markdown
pantalla "⚙ Parámetros" en cuanto la DIAN lo publique (ver
[sección 7.5](#75-conversión-smlmvuvt-para-multas-sancionatorias)).
```

with:

```markdown
sección "Parámetros" de "⚙ Configuraciones" en cuanto la DIAN lo publique (ver
[sección 7.5](#75-conversión-smlmvuvt-para-multas-sancionatorias)).
```

Replace (line ~1125-1127):

```markdown
avisar del error — ábrelo con doble clic en la tabla de "⚙ Parámetros" para revisar la fecha exacta con
la que quedó, y si está mal, agrega un valor nuevo con la fecha correcta. Ver la advertencia completa en
[sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros).
```

with:

```markdown
avisar del error — ábrelo con doble clic en la tabla de la sección "Parámetros" (dentro de "⚙
Configuraciones") para revisar la fecha exacta con la que quedó, y si está mal, agrega un valor nuevo con
la fecha correcta. Ver la advertencia completa en
[sección 5.14](#514-editar-tasas-y-topes-legales-configuraciones--parámetros).
```

**Explicitly out of scope:** `docs/superpowers/plans/2026-08-06-sprint33-dashboard-inicio.md` also links to the old `#514-editar-tasas-y-topes-legales-pantalla--parámetros` anchor. Per the Sprint 62 precedent already recorded in `docs/Pendientes.md` ("`docs/superpowers/plans/*.md` y `docs/superpowers/specs/*.md`... son actas históricas de planeación... no se re-audita"), do **not** edit it — closed planning documents keep the wording they had when they were written.

- [ ] **Step 10: `CHANGELOG.md`**

In the `[Unreleased]` narrative paragraph, after the sentence ending "...cambian de forma, no de total." (end of that paragraph), append:

```markdown
Sprint 66: el botón "Parametros" del sidebar se renombra a "Configuraciones" y se convierte en una
pantalla con submenú lateral (Parámetros/Apariencia, con espacio para futuras secciones); el interruptor
de modo oscuro/claro se muda de Parámetros a la nueva sección Apariencia.
```

Under the `### Changed` heading (the one right before `## [0.1.0] - 2026-08-04`), add a new bullet:

```markdown
- Navegación de "Parametros" reorganizada en "Configuraciones" (Sprint 66): el botón del sidebar pasa a
  llamarse "Configuraciones" y abre una pantalla con submenú lateral (Parámetros/Apariencia, con espacio
  para futuras secciones); el interruptor de modo oscuro/claro, antes alojado en Parámetros, se mueve a la
  nueva sección Apariencia. Sin cambios de comportamiento en la tabla de parámetros legales ni en la
  lógica de tema — solo de ubicación.
```

- [ ] **Step 11: `docs/Pendientes.md` — add the Sprint 66 entry**

Add this new entry right after the Sprint 65 section (after its closing `---`) and before `## Notas de entorno (sin sprint asignado)`:

```markdown
## Sprint 66 — Reorganizar "Parametros" en "Configuraciones" con submenú Parámetros/Apariencia ✅ Completado

**Prioridad sugerida:** Media — mejora de organización de la navegación; no bloquea uso actual (la tabla
de parámetros y el interruptor de tema ya funcionaban, solo cambian de ubicación).

**Depende de:** Nada.

**Contexto:** el botón lateral "Parametros" (ícono de engranaje) navegaba directo a la tabla de parámetros
legales, que además alojaba el interruptor de modo oscuro/claro desde el Sprint 50 — el propio código
señalaba (comentario en `app/views/configuracion.py`) que esa ubicación era temporal, a la espera de que
el sidebar se reorganizara. El usuario pidió, mediante brainstorming con companion visual: renombrar el
botón a "Configuraciones", convertir esa pantalla en un contenedor con submenú lateral estilo Ajustes
(Parámetros, Apariencia, con espacio para más secciones futuras), y mover el interruptor de tema a la
nueva sección "Apariencia". Diseño completo en
`docs/superpowers/specs/2026-08-13-configuraciones-apariencia-design.md`, plan de implementación en
`docs/superpowers/plans/2026-08-13-configuraciones-apariencia.md`, ejecutado con
superpowers:subagent-driven-development en un worktree dedicado.

**Código nuevo a crear:**
- `app/views/apariencia.py` (nuevo): `AparienciaView`, con el `QCheckBox` "Modo oscuro" movido desde
  `ParametrosView`.
- `app/views/configuraciones.py` (nuevo): `ConfiguracionesView`, submenú lateral + panel de contenido que
  alterna entre `ParametrosView` (existente, sin el checkbox) y `AparienciaView`.
- `app/views/configuracion.py`: se quita el checkbox de tema y `_alternar_modo_tema` de `ParametrosView`.
- `app/views/main_window.py`: `boton_parametros`/`parametros_page` se renombran a
  `boton_configuraciones`/`configuraciones_page` ("Configuraciones", mismo ícono de engranaje), navegan a
  `ConfiguracionesView`, y el breadcrumb pasa a "Configuraciones › Parámetros"/"Configuraciones ›
  Apariencia" según la sección activa dentro de esa pantalla.
- Tests nuevos/actualizados: `tests/views/test_apariencia.py`, `tests/views/test_configuraciones.py`,
  `tests/views/test_configuracion.py`, `tests/views/test_main_window.py`.
- Documentación: `README.md`, `docs/GUIA_USUARIO.md`, `CHANGELOG.md`.

**Definición de Hecho:**
- El sidebar principal muestra "Configuraciones" (no "Parametros"), mismo ícono de engranaje.
- Entrar a Configuraciones muestra por defecto la sección Parámetros con la tabla de parámetros legales
  intacta (mismo comportamiento de siempre).
- La sección Apariencia tiene el interruptor "Modo oscuro" funcionando igual que antes (aplica el tema en
  caliente y lo persiste).
- El submenú permite alternar entre ambas secciones sin perder el resto de la navegación (Volver/Inicio/
  breadcrumb siguen funcionando).
- README.md y docs/GUIA_USUARIO.md ya no describen "Parámetros" como el punto de entrada del sidebar,
  sino "Configuraciones".
- Suite completa en verde.

**Cierre de implementación (2026-08-13):** [[completar al ejecutar este paso: confirmar que los 4 tests de
`test_apariencia.py`, los 9 de `test_configuraciones.py`, y la suite completa de `test_configuracion.py` y
`test_main_window.py` pasan; mencionar el total de tests de la suite completa (`pytest -q`, línea final
"N passed"); confirmar que `ruff check .` no reporta errores; y describir brevemente si hubo alguna
desviación respecto a este plan (debería no haberla, pero si algún nombre de método o test cambió durante
la implementación por una razón concreta, dejarlo anotado aquí, igual que en el cierre del Sprint 64).]]**

---
```

Then update the table of contents near the top of the file: replace

```markdown
- [Sprint 65 — Lanzador de doble clic "Iniciar BASTIUM.bat" ✅ Completado](#sprint-65--lanzador-de-doble-clic-iniciar-bastiumbat--completado)
```

with:

```markdown
- [Sprint 65 — Lanzador de doble clic "Iniciar BASTIUM.bat" ✅ Completado](#sprint-65--lanzador-de-doble-clic-iniciar-bastiumbat--completado)
- [Sprint 66 — Reorganizar "Parametros" en "Configuraciones" con submenú Parámetros/Apariencia ✅ Completado](#sprint-66--reorganizar-parametros-en-configuraciones-con-submenú-parámetrosapariencia--completado)
```

(The anchor was hand-derived following the same slugging pattern already used by every other entry in this TOC — lowercase, punctuation/emoji stripped, spaces collapsed to hyphens, double space around the stripped em-dash/emoji becomes a double hyphen. Cross-check it against the Sprint 64/65 anchors immediately above it before committing; if it doesn't match GitHub's actual rendering, fix the anchor text only, not the heading.)

- [ ] **Step 12: Run the full suite one last time**

Run: `QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest -q`
Expected: PASS, 0 failed. Note the final "N passed" count for the `[[...]]` placeholder in Step 11 and fill it in now (replace the whole `**Cierre de implementación...**` bracketed placeholder with real prose — no `[[...]]` markers may remain in the committed file).

- [ ] **Step 13: Commit**

```bash
git add README.md docs/GUIA_USUARIO.md CHANGELOG.md docs/Pendientes.md
git commit -m "docs: cerrar Sprint 66 (Configuraciones + Apariencia) en Pendientes.md y actualizar README/GUIA_USUARIO/CHANGELOG"
```

---

## Final integration (after Task 5)

This is orchestration, not a subagent task — done by whoever is driving `subagent-driven-development` once Task 5's commit is in:

- [ ] Review the worktree's full diff and commit log against this plan and the design doc.
- [ ] Run `QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest -q` and `.venv/Scripts/python.exe -m ruff check .` one more time from a clean checkout of the worktree branch.
- [ ] Merge the branch into `main` (per `CONTRIBUTING.md`, sprint-closing merges use the `merge:` commit prefix), then remove the worktree.
