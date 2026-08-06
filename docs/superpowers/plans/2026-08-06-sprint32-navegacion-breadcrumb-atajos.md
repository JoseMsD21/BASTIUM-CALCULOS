# Sprint 32 — Navegación: barra mejorada, breadcrumb y atajos de teclado Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** El `QToolBar` de `MainWindow` (`app/views/main_window.py`) — hoy 3 botones con ícono
(Sprint 31) pero sin contexto de "dónde estoy" ni forma de navegar sin mouse — gana tres cosas: (1)
un breadcrumb contextual ("Expedientes › Radicado 2024-00123 › Liquidación") que se actualiza según
la pantalla activa y el expediente abierto, (2) atajos de teclado globales de navegación
(`Alt+Izquierda`/`Backspace` → Volver, `Ctrl+Home` → Inicio) más `Ctrl+S`/`Esc` en los 5 diálogos de
formulario del proyecto, y (3) un estado visual "activo" en el botón "Parámetros" cuando esa es la
pantalla que se está viendo. La máquina de estados de navegación existente (`_pages`/`show_page`/
`_history`) no se toca — este sprint mejora presentación y accesibilidad de teclado sobre ella, no la
rehace.

**Architecture:** **Decisión de diseño (sidebar vs. toolbar reforzado):** este plan mantiene el
`QToolBar` superior existente en vez de construir un sidebar de navegación completo. La app aloja
hoy 4 pantallas en `MainWindow` (expedientes, detalle, resultado, parametros) y el Sprint 33
(dashboard) sumaría una quinta — un panel lateral con 4-5 ítems fijos no aporta suficiente valor de
agrupación frente a un toolbar horizontal con breadcrumb explícito, y además obligaría a
reestructurar `QMainWindow.setCentralWidget` (que hoy asume que toda la navegación vive en el
`QToolBar`, no en un panel dentro del central widget), un costo de refactor que el hallazgo del
sprint no justifica: lo que se pide es *contexto* ("dónde estoy") y *velocidad* (atajos), no una
jerarquía de navegación nueva. Si un sprint futuro agrega una sexta pantalla o introduce
sub-secciones jerárquicas dentro de un expediente, ahí sí conviene reevaluar un sidebar — queda
anotado como candidato de un sprint futuro, no de este.

**Breadcrumb:** se implementa como un único `QLabel` (`self.etiqueta_breadcrumb`, con
`objectName="etiqueta_breadcrumb"` para poder seleccionarlo desde `resources/theme.qss`) agregado al
mismo `QToolBar` de navegación, después de un `addSeparator()`. `MainWindow` guarda
`self._radicado_actual: str | None` (poblado en `_abrir_detalle()` con una consulta directa a
`Expediente.radicado`, limpiado en `show_page()` cada vez que la pantalla destino es
"expedientes"), y un método `_texto_breadcrumb()` deriva el texto exacto a partir de
`self._current_page_name` + `self._radicado_actual`. `show_page()` llama a `_actualizar_breadcrumb()`
en cada navegación (incluida `_volver()`, que ya delega en `show_page()`), así que el breadcrumb
queda correcto sin impactar ningún otro call site.

**Atajos de teclado:** se usan `QShortcut`/`QKeySequence` de `PySide6.QtGui` con el contexto por
defecto (`Qt.ShortcutContext.WindowShortcut`): un atajo con ese contexto solo se dispara si su
widget padre es (o pertenece a) la ventana activa (`isActiveWindow()`). Esto es lo que hace seguro
enlazar `Backspace` a "Volver" a nivel de `MainWindow` sin que interfiera con la edición de texto:
los 5 diálogos de formulario (`ExpedienteFormDialog`, `ObligacionFormDialog`, `AbonoFormDialog`,
`EventoLaboralFormDialog`, `ParametroFormDialog`) son ventanas modales top-level separadas — mientras
alguno está abierto, es él (no `MainWindow`) quien es la ventana activa, así que el atajo de
`MainWindow` no compite con el `Backspace` nativo de un `QLineEdit` dentro del formulario. Se
confirmó empíricamente en este entorno (`QT_QPA_PLATFORM=offscreen`, PySide6 6.11.1) que
`QShortcut` con contexto por defecto SÍ se dispara bajo `pytest-qt` siempre que la ventana se muestre
y active explícitamente antes del `qtbot.keyClick(...)` — ver la receta exacta en "Contexto
compartido" más abajo; sin ella (`show()` solo, o incluso `qtbot.waitActive()`) el atajo no se
dispara en modo offscreen porque `isActiveWindow()` no queda en `True`.

Para `Ctrl+S`/`Esc` en los formularios: `Ctrl+S` se implementa con un `QShortcut` nuevo por diálogo,
conectado al mismo slot `_guardar_y_cerrar` que ya usa el botón "Guardar". `Esc` **no requiere código
nuevo**: `QDialog` ya implementa `keyPressEvent()` para llamar a `reject()` cuando se presiona Escape
(comportamiento nativo de Qt, confirmado en este entorno) — este plan agrega un test de regresión
por diálogo que fija ese comportamiento explícitamente (útil porque ningún test del proyecto lo
verificaba hasta ahora), sin tocar producción para lograrlo.

**Estado activo/inactivo:** se reutiliza la convención `QPushButton.setProperty("class", "primary")`
del Sprint 31 (`resources/theme.qss`, ya trae los selectores `QPushButton[class="primary"]`). Solo
`boton_parametros` recibe el tratamiento de "activo/inactivo": es el único botón de la barra que
representa una pantalla fija a la que el usuario puede "estar" — `boton_volver` es una acción sin
pantalla propia (depende de `_history`) y `boton_inicio` se oculta justo cuando el usuario ya está en
"expedientes" (su propio destino), así que ninguno de los dos tiene un estado "activo" con sentido.
`show_page()` llama a un nuevo `_actualizar_estado_activo_navegacion()` en cada navegación, que fija
la propiedad `class` a `"primary"` si `self._current_page_name == "parametros"` y a `""` en cualquier
otro caso, seguido de `style().unpolish()`/`style().polish()` — a diferencia del Sprint 31 (que solo
asignaba la propiedad una vez en `__init__`, antes del primer show), aquí el cambio ocurre en
tiempo de ejecución después de que la ventana ya se mostró, así que si hace falta el
`unpolish()`/`polish()` manual para que Qt vuelva a evaluar el selector QSS.

**Tech Stack:** Python 3.14, PySide6 6.11 (`QtCore.Qt`, `QtGui.QShortcut`/`QKeySequence`,
`QtWidgets.QLabel`/`QToolBar`), SQLAlchemy (consulta directa de `Expediente.radicado` para el
breadcrumb), pytest + pytest-qt (`qtbot`), ruff (line-length 99, `target-version = "py314"`, reglas
`E`/`F`/`I`/`UP`/`B`).

---

### Contexto compartido entre tareas — no repetir en cada una

**Ruta del intérprete de pruebas (todas las tareas):**
`"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe"`.
Si el entorno de ejecución no tiene un display real, anteponer `QT_QPA_PLATFORM=offscreen` a cada
comando `pytest` (ej.: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest ...`).

**Punto de partida asumido — Sprint 31 ya fusionado a `main`:** este plan se escribió explorando el
código *antes* de que el Sprint 31 (sistema de diseño visual: tema, íconos, `theme.qss`) se
implementara, pero se ejecuta *después*. Todos los `old_string`/estados "antes" citados en los Steps
de este plan asumen el estado que deja el Sprint 31, no el que tenía el repo al escribir este plan.
En particular, se asume que existen y tienen exactamente esta forma:

- `app/views/icons.py` — `icon(nombre: str) -> QIcon` (`ValueError` si `nombre` no está en
  `ICONOS_DISPONIBLES = frozenset({"home", "back", "settings", "save", "cancel", "delete",
  "export"})`) e `icono_aplicacion() -> QIcon`.
- `app/core/theme_colors.py` — `PRIMARIO = "#AE1C21"` (+ variantes), `SECUNDARIO = "#F5F1E9"` (+
  variantes), etc.
- `resources/theme.qss` — cargado una sola vez vía `app.core.apariencia.aplicar_tema(app)` desde
  `main.py`; termina (al momento de escribir este plan) con el bloque:
  ```css
  /* --- Dialogos de progreso/mensaje --- */

  QProgressDialog, QMessageBox {
      background-color: #FAF8F4;
  }
  ```
- `app/views/main_window.py` termina el Sprint 31 con este contenido exacto:
  ```python
  from PySide6.QtWidgets import QMainWindow, QPushButton, QStackedWidget, QToolBar

  from app.views.configuracion import ParametrosView
  from app.views.expediente_detalle import ExpedienteDetallePage
  from app.views.expedientes import ExpedientesListView
  from app.views.icons import icon, icono_aplicacion
  from app.views.liquidaciones import ResultadoLiquidacionView


  class MainWindow(QMainWindow):
      """Ventana principal: aloja las 3 pantallas del flujo y la navegacion entre ellas."""

      def __init__(self):
          super().__init__()
          self.setWindowTitle("BASTIUM - Ecosistema de Liquidacion Forense")
          self.setWindowIcon(icono_aplicacion())

          self.stacked_widget = QStackedWidget()
          self.setCentralWidget(self.stacked_widget)

          self.expedientes_page = ExpedientesListView(on_expediente_abierto=self._abrir_detalle)
          self.detalle_page = ExpedienteDetallePage(on_liquidado=self._mostrar_resultado)
          self.resultado_page = ResultadoLiquidacionView()
          self.parametros_page = ParametrosView()

          self.stacked_widget.addWidget(self.expedientes_page)
          self.stacked_widget.addWidget(self.detalle_page)
          self.stacked_widget.addWidget(self.resultado_page)
          self.stacked_widget.addWidget(self.parametros_page)

          self._pages = {
              "expedientes": self.expedientes_page,
              "detalle": self.detalle_page,
              "resultado": self.resultado_page,
              "parametros": self.parametros_page,
          }

          self._history: list[str] = []
          self._current_page_name = "expedientes"

          self._crear_barra_navegacion()
          self.show_page("expedientes")

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

      def show_page(self, name: str, add_to_history: bool = True) -> None:
          if add_to_history and self._current_page_name != name:
              self._history.append(self._current_page_name)
          self.stacked_widget.setCurrentWidget(self._pages[name])
          self._current_page_name = name
          self._actualizar_botones_navegacion()

      def _actualizar_botones_navegacion(self) -> None:
          self.boton_volver.setVisible(bool(self._history))
          self.boton_inicio.setVisible(self._current_page_name != "expedientes")

      def showEvent(self, event) -> None:
          # QToolBar resets the visibility of widgets added via addWidget() to True
          # the first time the toolbar itself becomes visible, overriding any
          # setVisible(False) applied while the window was not yet shown. Resync
          # the buttons' visibility once the window is actually shown.
          super().showEvent(event)
          self._actualizar_botones_navegacion()

      def _volver(self) -> None:
          if not self._history:
              return
          pagina_anterior = self._history.pop()
          self.show_page(pagina_anterior, add_to_history=False)

      def _ir_inicio(self) -> None:
          self._history.clear()
          self.show_page("expedientes", add_to_history=False)

      def _abrir_detalle(self, expediente_id: int) -> None:
          self.detalle_page.cargar_expediente(expediente_id)
          self.show_page("detalle")

      def _mostrar_resultado(self, resultado, expediente_id: int) -> None:
          self.resultado_page.mostrar(resultado, expediente_id)
          self.show_page("resultado")

      def _ir_a_parametros(self) -> None:
          self.parametros_page.refrescar()
          self.show_page("parametros")
  ```
- Los 5 diálogos de formulario terminan el Sprint 31 con su botón "Guardar" como `self.boton_guardar`
  (no una variable local), con `self.boton_guardar.setIcon(icon("save"))` y
  `self.boton_guardar.setProperty("class", "primary")` ya aplicados, en:
  `app/views/expedientes.py` (`ExpedienteFormDialog`), `app/views/obligaciones.py`
  (`ObligacionFormDialog`), `app/views/abonos.py` (`AbonoFormDialog`),
  `app/views/eventos_laborales.py` (`EventoLaboralFormDialog`), `app/views/configuracion.py`
  (`ParametroFormDialog`).

Si al ejecutar este plan el estado real de estos archivos difiere del citado arriba (porque el
Sprint 31 se implementó distinto a como lo planeó su propio plan), adaptar el `old_string` de cada
Step al contenido real antes de aplicar el `new_string` — la intención de cada cambio no depende de
los nombres de línea exactos, solo de que `boton_guardar`, `icon()`, `icono_aplicacion()` y las 4
claves de `self._pages` (`"expedientes"`, `"detalle"`, `"resultado"`, `"parametros"`) existan tal
como se describen.

**Receta de test verificada para que `QShortcut` se dispare bajo `pytest-qt` en modo offscreen:**
confirmado en este entorno (PySide6 6.11.1, `QT_QPA_PLATFORM=offscreen`) que **ni** `widget.show()`
solo **ni** `qtbot.waitActive(widget)` bastan para que `isActiveWindow()` quede en `True` — sin eso,
un `QShortcut` con el contexto por defecto (`WindowShortcut`) nunca se dispara aunque
`qtbot.keyClick()` sí llegue al widget. La secuencia que sí funciona de forma confiable, usada en
todos los tests de teclado de este plan:
```python
widget.show()
qtbot.waitExposed(widget)
widget.activateWindow()
qtbot.wait(50)
```
Después de eso, `qtbot.keyClick(widget, Qt.Key.Key_X, Qt.KeyboardModifier.AlgunModificador)` dispara
cualquier `QShortcut` cuyo padre sea `widget` (o un ancestro de `widget`).

**Aislamiento de base de datos automático:** `tests/conftest.py` define un fixture
`_db_en_memoria_por_defecto(monkeypatch)` con `autouse=True` que aísla **todos** los tests del árbol
`tests/` (incluido `tests/views/`) en un engine SQLite en memoria nuevo por test, sin que el test
tenga que declarar `monkeypatch` ni llamar a nada explícito — por eso los tests nuevos de
`tests/views/test_main_window.py` en este plan llaman a `session_module.get_session()` directamente,
sin repetir el patrón local `_sesion_en_memoria(monkeypatch)` que sí usan (de forma redundante pero
inofensiva, y por consistencia con el resto de cada archivo) `test_expedientes.py`,
`test_abonos.py`, `test_eventos_laborales.py` y `test_obligaciones.py` — este plan reutiliza los
helpers locales ya existentes en esos 4 archivos (`_sesion_en_memoria`, `_obligacion_de_prueba`,
`_obligacion_laboral_de_prueba`, `_expediente_de_prueba`) tal cual están, sin tocarlos.

---

### Task 1: Breadcrumb contextual en la barra de navegación

**Files:**
- Modify: `app/views/main_window.py`
- Modify: `resources/theme.qss`
- Modify: `tests/views/test_main_window.py`

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/views/test_main_window.py`, cambiar el import inicial de:

```python
from app.views.main_window import MainWindow
```

a:

```python
from datetime import date

import database.session as session_module
from app.views.main_window import MainWindow
from database.models import AreaDerecho, Expediente
```

Agregar al final del archivo:

```python
def test_breadcrumb_muestra_expedientes_en_pagina_inicial(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.etiqueta_breadcrumb.text() == "Expedientes"


def test_breadcrumb_muestra_parametros_en_la_pantalla_de_parametros(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("parametros")

    assert window.etiqueta_breadcrumb.text() == "Parámetros"


def test_breadcrumb_muestra_el_radicado_al_abrir_un_expediente(qtbot):
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-00123",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    window = MainWindow()
    qtbot.addWidget(window)

    window._abrir_detalle(expediente_id)

    assert window.etiqueta_breadcrumb.text() == "Expedientes › Radicado 2026-00123"


def test_breadcrumb_incluye_liquidacion_al_mostrar_el_resultado(qtbot):
    from decimal import Decimal

    from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
    from app.engine.liquidation.result import LiquidationResult

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-00124",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    window = MainWindow()
    qtbot.addWidget(window)
    window._abrir_detalle(expediente_id)

    debt = PendingDebt(principal=Decimal("100.00"), interest=Decimal("0.00"), indexation=Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="LIQUIDATION_CUTOFF")
    item = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Prueba",
        capital_base=Decimal("100.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
    )
    resultado = LiquidationResult(items=[item])

    window._mostrar_resultado(resultado, expediente_id)

    assert window.etiqueta_breadcrumb.text() == "Expedientes › Radicado 2026-00124 › Liquidación"


def test_breadcrumb_regresa_a_expedientes_al_ir_a_inicio(qtbot):
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-00125",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    window = MainWindow()
    qtbot.addWidget(window)
    window._abrir_detalle(expediente_id)

    window._ir_inicio()

    assert window.etiqueta_breadcrumb.text() == "Expedientes"
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_main_window.py -k breadcrumb -v`
Expected: FAIL (`AttributeError: 'MainWindow' object has no attribute 'etiqueta_breadcrumb'`).

- [ ] **Step 3: Implementar en `app/views/main_window.py`**

Imports — cambiar:

```python
from PySide6.QtWidgets import QMainWindow, QPushButton, QStackedWidget, QToolBar

from app.views.configuracion import ParametrosView
from app.views.expediente_detalle import ExpedienteDetallePage
from app.views.expedientes import ExpedientesListView
from app.views.icons import icon, icono_aplicacion
from app.views.liquidaciones import ResultadoLiquidacionView
```

a:

```python
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QStackedWidget, QToolBar

import database.session as session_module
from app.views.configuracion import ParametrosView
from app.views.expediente_detalle import ExpedienteDetallePage
from app.views.expedientes import ExpedientesListView
from app.views.icons import icon, icono_aplicacion
from app.views.liquidaciones import ResultadoLiquidacionView
from database.models import Expediente
```

En `__init__`, cambiar:

```python
        self._history: list[str] = []
        self._current_page_name = "expedientes"

        self._crear_barra_navegacion()
        self.show_page("expedientes")
```

a:

```python
        self._history: list[str] = []
        self._current_page_name = "expedientes"
        self._radicado_actual: str | None = None

        self._crear_barra_navegacion()
        self.show_page("expedientes")
```

`_crear_barra_navegacion` — cambiar:

```python
        self.boton_parametros = QPushButton(" Parametros")
        self.boton_parametros.setIcon(icon("settings"))
        self.boton_parametros.clicked.connect(self._ir_a_parametros)
        barra.addWidget(self.boton_parametros)

        self.addToolBar(barra)
        self._actualizar_botones_navegacion()
```

a:

```python
        self.boton_parametros = QPushButton(" Parametros")
        self.boton_parametros.setIcon(icon("settings"))
        self.boton_parametros.clicked.connect(self._ir_a_parametros)
        barra.addWidget(self.boton_parametros)

        barra.addSeparator()

        self.etiqueta_breadcrumb = QLabel()
        self.etiqueta_breadcrumb.setObjectName("etiqueta_breadcrumb")
        barra.addWidget(self.etiqueta_breadcrumb)

        self.addToolBar(barra)
        self._actualizar_botones_navegacion()
```

`show_page` — cambiar:

```python
    def show_page(self, name: str, add_to_history: bool = True) -> None:
        if add_to_history and self._current_page_name != name:
            self._history.append(self._current_page_name)
        self.stacked_widget.setCurrentWidget(self._pages[name])
        self._current_page_name = name
        self._actualizar_botones_navegacion()
```

a:

```python
    def show_page(self, name: str, add_to_history: bool = True) -> None:
        if add_to_history and self._current_page_name != name:
            self._history.append(self._current_page_name)
        if name == "expedientes":
            self._radicado_actual = None
        self.stacked_widget.setCurrentWidget(self._pages[name])
        self._current_page_name = name
        self._actualizar_botones_navegacion()
        self._actualizar_breadcrumb()
```

Agregar los métodos de breadcrumb — cambiar:

```python
    def _actualizar_botones_navegacion(self) -> None:
        self.boton_volver.setVisible(bool(self._history))
        self.boton_inicio.setVisible(self._current_page_name != "expedientes")

    def showEvent(self, event) -> None:
```

a:

```python
    def _actualizar_botones_navegacion(self) -> None:
        self.boton_volver.setVisible(bool(self._history))
        self.boton_inicio.setVisible(self._current_page_name != "expedientes")

    def _actualizar_breadcrumb(self) -> None:
        self.etiqueta_breadcrumb.setText(self._texto_breadcrumb())

    def _texto_breadcrumb(self) -> str:
        if self._current_page_name == "parametros":
            return "Parámetros"
        if self._current_page_name == "detalle":
            if self._radicado_actual:
                return f"Expedientes › Radicado {self._radicado_actual}"
            return "Expedientes › Detalle"
        if self._current_page_name == "resultado":
            if self._radicado_actual:
                return f"Expedientes › Radicado {self._radicado_actual} › Liquidación"
            return "Expedientes › Liquidación"
        return "Expedientes"

    def showEvent(self, event) -> None:
```

Agregar `_obtener_radicado` y poblar `_radicado_actual` en `_abrir_detalle` — cambiar:

```python
    def _abrir_detalle(self, expediente_id: int) -> None:
        self.detalle_page.cargar_expediente(expediente_id)
        self.show_page("detalle")
```

a:

```python
    def _obtener_radicado(self, expediente_id: int) -> str:
        session = session_module.get_session()
        expediente = session.get(Expediente, expediente_id)
        radicado = expediente.radicado
        session.close()
        return radicado

    def _abrir_detalle(self, expediente_id: int) -> None:
        self._radicado_actual = self._obtener_radicado(expediente_id)
        self.detalle_page.cargar_expediente(expediente_id)
        self.show_page("detalle")
```

- [ ] **Step 4: Actualizar `resources/theme.qss`**

Al final del archivo, cambiar:

```css
/* --- Dialogos de progreso/mensaje --- */

QProgressDialog, QMessageBox {
    background-color: #FAF8F4;
}
```

a:

```css
/* --- Dialogos de progreso/mensaje --- */

QProgressDialog, QMessageBox {
    background-color: #FAF8F4;
}

/* --- Breadcrumb de navegacion (Sprint 32) --- */

QLabel#etiqueta_breadcrumb {
    color: #6B5F57;
    font-weight: bold;
    padding-left: 10px;
}
```

- [ ] **Step 5: Correr los tests para verificar que pasan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_main_window.py -v`
Expected: todos PASS (los tests originales del archivo + los 5 nuevos de este Step).

- [ ] **Step 6: Ruff**

Run: `"<python>" -m ruff check app/views/main_window.py tests/views/test_main_window.py`
Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add app/views/main_window.py resources/theme.qss tests/views/test_main_window.py
git commit -m "$(cat <<'EOF'
feat(sprint32): agregar breadcrumb contextual a la barra de navegacion

EOF
)"
```

---

### Task 2: Atajos de teclado globales de navegación (`Alt+Izquierda`/`Backspace` → Volver, `Ctrl+Home` → Inicio)

**Files:**
- Modify: `app/views/main_window.py`
- Modify: `tests/views/test_main_window.py`

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/views/test_main_window.py`, cambiar el import de:

```python
from datetime import date

import database.session as session_module
from app.views.main_window import MainWindow
from database.models import AreaDerecho, Expediente
```

a:

```python
from datetime import date

from PySide6.QtCore import Qt

import database.session as session_module
from app.views.main_window import MainWindow
from database.models import AreaDerecho, Expediente
```

Agregar al final del archivo:

```python
def test_alt_izquierda_navega_a_la_pagina_anterior(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    window.activateWindow()
    qtbot.wait(50)

    window.show_page("detalle")
    qtbot.keyClick(window, Qt.Key.Key_Left, Qt.KeyboardModifier.AltModifier)

    assert window.stacked_widget.currentWidget() is window.expedientes_page


def test_backspace_navega_a_la_pagina_anterior(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    window.activateWindow()
    qtbot.wait(50)

    window.show_page("detalle")
    qtbot.keyClick(window, Qt.Key.Key_Backspace)

    assert window.stacked_widget.currentWidget() is window.expedientes_page


def test_ctrl_home_regresa_a_expedientes_y_limpia_el_historial(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    window.activateWindow()
    qtbot.wait(50)

    window.show_page("detalle")
    window.show_page("resultado")
    qtbot.keyClick(window, Qt.Key.Key_Home, Qt.KeyboardModifier.ControlModifier)

    assert window.stacked_widget.currentWidget() is window.expedientes_page
    assert window._history == []
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_main_window.py -k "alt_izquierda or backspace or ctrl_home" -v`
Expected: FAIL (`AssertionError` — `window.stacked_widget.currentWidget()` sigue siendo
`detalle_page`/`resultado_page`, ningún atajo está conectado todavía).

- [ ] **Step 3: Implementar en `app/views/main_window.py`**

Imports — cambiar:

```python
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QStackedWidget, QToolBar

import database.session as session_module
```

a:

```python
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QStackedWidget, QToolBar

import database.session as session_module
```

En `__init__`, cambiar:

```python
        self._crear_barra_navegacion()
        self.show_page("expedientes")
```

a:

```python
        self._crear_barra_navegacion()
        self._crear_atajos_teclado()
        self.show_page("expedientes")
```

Agregar el método `_crear_atajos_teclado` — cambiar:

```python
    def _crear_barra_navegacion(self) -> None:
```

a:

```python
    def _crear_atajos_teclado(self) -> None:
        # Contexto por defecto de QShortcut (Qt.ShortcutContext.WindowShortcut): solo se
        # dispara si `self` (MainWindow) es la ventana activa. Cuando un dialogo modal
        # (ej. ExpedienteFormDialog) esta abierto, ese dialogo es la ventana activa y
        # MainWindow no lo es -- por eso Backspace no interfiere con la edicion de texto
        # dentro de los formularios (que viven en dialogos separados, no en las 4
        # pantallas alojadas directamente por MainWindow).
        self.atajo_volver_alt_izquierda = QShortcut(QKeySequence("Alt+Left"), self)
        self.atajo_volver_alt_izquierda.activated.connect(self._volver)

        self.atajo_volver_backspace = QShortcut(QKeySequence(Qt.Key.Key_Backspace), self)
        self.atajo_volver_backspace.activated.connect(self._volver)

        self.atajo_inicio = QShortcut(QKeySequence("Ctrl+Home"), self)
        self.atajo_inicio.activated.connect(self._ir_inicio)

    def _crear_barra_navegacion(self) -> None:
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_main_window.py -v`
Expected: todos PASS (los tests de la Task 1 + los 3 nuevos de este Step + los originales).

- [ ] **Step 5: Ruff**

Run: `"<python>" -m ruff check app/views/main_window.py tests/views/test_main_window.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add app/views/main_window.py tests/views/test_main_window.py
git commit -m "$(cat <<'EOF'
feat(sprint32): agregar atajos de teclado Alt+Izquierda/Backspace (Volver) y Ctrl+Home (Inicio)

EOF
)"
```

---

### Task 3: Estado activo/inactivo del botón "Parámetros"

**Files:**
- Modify: `app/views/main_window.py`
- Modify: `tests/views/test_main_window.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/views/test_main_window.py`:

```python
def test_boton_parametros_activo_en_la_pantalla_de_parametros(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("parametros")

    assert window.boton_parametros.property("class") == "primary"


def test_boton_parametros_inactivo_en_otras_pantallas(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.boton_parametros.property("class") == ""

    window.show_page("detalle")

    assert window.boton_parametros.property("class") == ""


def test_boton_parametros_deja_de_estar_activo_al_salir_de_parametros(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("parametros")
    assert window.boton_parametros.property("class") == "primary"

    window._ir_inicio()

    assert window.boton_parametros.property("class") == ""
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_main_window.py -k boton_parametros -v`
Expected: FAIL (`property("class")` devuelve `None` porque `boton_parametros` nunca recibió esa
propiedad todavía — `None == "primary"` y `None == ""` son ambos `False`).

- [ ] **Step 3: Implementar en `app/views/main_window.py`**

`_crear_barra_navegacion` — cambiar:

```python
        self.boton_parametros = QPushButton(" Parametros")
        self.boton_parametros.setIcon(icon("settings"))
        self.boton_parametros.clicked.connect(self._ir_a_parametros)
        barra.addWidget(self.boton_parametros)
```

a:

```python
        self.boton_parametros = QPushButton(" Parametros")
        self.boton_parametros.setIcon(icon("settings"))
        self.boton_parametros.setProperty("class", "")
        self.boton_parametros.clicked.connect(self._ir_a_parametros)
        barra.addWidget(self.boton_parametros)
```

`show_page` — cambiar:

```python
        self._actualizar_botones_navegacion()
        self._actualizar_breadcrumb()
```

a:

```python
        self._actualizar_botones_navegacion()
        self._actualizar_breadcrumb()
        self._actualizar_estado_activo_navegacion()
```

Agregar el método `_actualizar_estado_activo_navegacion` — cambiar:

```python
        return "Expedientes"

    def showEvent(self, event) -> None:
```

a:

```python
        return "Expedientes"

    def _actualizar_estado_activo_navegacion(self) -> None:
        # boton_parametros es el unico boton de la barra que representa una pantalla fija
        # a la que el usuario puede "estar": Volver es una accion sin pantalla propia
        # (depende del historial) e Inicio se oculta justo cuando el usuario ya esta en
        # "expedientes" (nunca tendria sentido marcarlo "activo"). Se reutiliza la
        # convencion class="primary" del Sprint 31 (resources/theme.qss) para el estado
        # activo; fuera de "parametros" vuelve a la cadena vacia (estilo neutral). A
        # diferencia del Sprint 31 (que fijaba la propiedad una sola vez en __init__,
        # antes del primer show), aca el cambio ocurre en tiempo de ejecucion despues de
        # que la ventana ya se mostro, asi que hace falta unpolish()/polish() manual para
        # que Qt vuelva a evaluar el selector QSS.
        self.boton_parametros.setProperty(
            "class", "primary" if self._current_page_name == "parametros" else ""
        )
        self.boton_parametros.style().unpolish(self.boton_parametros)
        self.boton_parametros.style().polish(self.boton_parametros)

    def showEvent(self, event) -> None:
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_main_window.py -v`
Expected: todos PASS (Tasks 1-3 + originales).

- [ ] **Step 5: Ruff**

Run: `"<python>" -m ruff check app/views/main_window.py tests/views/test_main_window.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add app/views/main_window.py tests/views/test_main_window.py
git commit -m "$(cat <<'EOF'
feat(sprint32): resaltar el boton Parametros cuando esa es la pantalla activa

EOF
)"
```

---

### Task 4: Atajo `Ctrl+S` (guardar) y verificación de `Esc` (cancelar) en los 5 diálogos de formulario

**Files:**
- Modify: `app/views/expedientes.py`, `app/views/obligaciones.py`, `app/views/abonos.py`,
  `app/views/eventos_laborales.py`, `app/views/configuracion.py`
- Modify: `tests/views/test_expedientes.py`, `tests/views/test_obligaciones.py`,
  `tests/views/test_abonos.py`, `tests/views/test_eventos_laborales.py`,
  `tests/views/test_configuracion.py`

- [ ] **Step 1: Escribir todos los tests que fallan**

En `tests/views/test_expedientes.py`, cambiar el import de:

```python
from datetime import date
from decimal import Decimal

from PySide6.QtWidgets import QMessageBox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.views.expedientes import ExpedienteFormDialog, ExpedientesListView
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion
```

a:

```python
from datetime import date
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMessageBox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.views.expedientes import ExpedienteFormDialog, ExpedientesListView
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion
```

y agregar al final del archivo:

```python
def test_ctrl_s_guarda_y_cierra_el_dialogo(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)
    dialog.campo_radicado.setText("2026-050")
    dialog.campo_demandante.setText("Ana")
    dialog.campo_demandado.setText("Luis")
    dialog.campo_fecha_corte.setDate(date(2026, 1, 1))

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = session_module.get_session()
    guardado = session.query(Expediente).filter_by(radicado="2026-050").one_or_none()
    assert guardado is not None
    session.close()


def test_escape_cierra_el_dialogo_sin_guardar(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)
    dialog.campo_radicado.setText("2026-051")

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_Escape)

    assert dialog.result() == QDialog.DialogCode.Rejected
    session = session_module.get_session()
    guardado = session.query(Expediente).filter_by(radicado="2026-051").one_or_none()
    assert guardado is None
    session.close()
```

En `tests/views/test_obligaciones.py`, cambiar el import de:

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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.views.obligaciones import ObligacionFormDialog
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion
```

y agregar al final del archivo:

```python
def test_ctrl_s_guarda_y_cierra_el_dialogo(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Gastos medicos")
    dialog.campo_valor.setText("427900.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 11, 20))

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.concepto == "Gastos medicos"
    session.close()


def test_escape_cierra_el_dialogo_sin_guardar(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Gastos medicos")

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_Escape)

    assert dialog.result() == QDialog.DialogCode.Rejected
    session = session_module.get_session()
    cantidad = session.query(Obligacion).filter_by(expediente_id=expediente_id).count()
    assert cantidad == 0
    session.close()
```

En `tests/views/test_abonos.py`, cambiar el import de:

```python
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.views.abonos import AbonoFormDialog
from database.models import Abono, AreaDerecho, Base, Expediente, Obligacion, TipoObligacion
```

a:

```python
from datetime import date
from decimal import Decimal

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.views.abonos import AbonoFormDialog
from database.models import Abono, AreaDerecho, Base, Expediente, Obligacion, TipoObligacion
```

y agregar al final del archivo:

```python
def test_ctrl_s_guarda_y_cierra_el_dialogo(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_fecha.setDate(date(2026, 1, 15))
    dialog.campo_monto.setText("100000.00")

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert len(obligacion.abonos) == 1
    session.close()


def test_escape_cierra_el_dialogo_sin_guardar(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("100000.00")

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_Escape)

    assert dialog.result() == QDialog.DialogCode.Rejected
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert len(obligacion.abonos) == 0
    session.close()
```

En `tests/views/test_eventos_laborales.py`, cambiar el import de:

```python
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.views.eventos_laborales import EventoLaboralFormDialog
from database.models import (
    AreaDerecho,
    Base,
    Expediente,
    MotivoSuspension,
    Obligacion,
    TipoEventoLaboral,
    TipoObligacion,
)
```

a:

```python
from datetime import date
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.views.eventos_laborales import EventoLaboralFormDialog
from database.models import (
    AreaDerecho,
    Base,
    Expediente,
    MotivoSuspension,
    Obligacion,
    TipoEventoLaboral,
    TipoObligacion,
)
```

y agregar al final del archivo:

```python
def test_ctrl_s_guarda_y_cierra_el_dialogo(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # Suspension
    dialog.campo_fecha_inicio.setDate(date(2020, 3, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 3, 15))
    dialog.combo_motivo.setCurrentIndex(0)  # Huelga

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert len(obligacion.eventos_laborales) == 1
    session.close()


def test_escape_cierra_el_dialogo_sin_guardar(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # Suspension

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_Escape)

    assert dialog.result() == QDialog.DialogCode.Rejected
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert len(obligacion.eventos_laborales) == 0
    session.close()
```

En `tests/views/test_configuracion.py`, cambiar el import de:

```python
from datetime import date
from decimal import Decimal

from PySide6.QtCore import QDate

from app.services.parametro_service import agregar_valor, historial
from app.views.configuracion import (
    HistorialParametroDialog,
    ParametroFormDialog,
    ParametrosView,
)
```

a:

```python
from datetime import date
from decimal import Decimal

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QDialog

from app.services.parametro_service import agregar_valor, historial
from app.views.configuracion import (
    HistorialParametroDialog,
    ParametroFormDialog,
    ParametrosView,
)
```

y agregar al final del archivo:

```python
def test_ctrl_s_guarda_y_cierra_el_dialogo(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")

    dialogo.show()
    qtbot.waitExposed(dialogo)
    dialogo.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialogo, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert dialogo.result() == QDialog.DialogCode.Accepted
    filas = historial("USURA_MULTIPLICADOR")
    assert len(filas) == 1
    assert filas[0].valor == Decimal("1.5")


def test_escape_cierra_el_dialogo_sin_guardar(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")

    dialogo.show()
    qtbot.waitExposed(dialogo)
    dialogo.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialogo, Qt.Key.Key_Escape)

    assert dialogo.result() == QDialog.DialogCode.Rejected
    assert historial("USURA_MULTIPLICADOR") == []
```

- [ ] **Step 2: Correr los 5 archivos de test para verificar que fallan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_expedientes.py tests/views/test_obligaciones.py tests/views/test_abonos.py tests/views/test_eventos_laborales.py tests/views/test_configuracion.py -k "ctrl_s or escape" -v`
Expected: FAIL en los 5 `test_ctrl_s_guarda_y_cierra_el_dialogo` (`dialog.result()` queda en `0`
porque `Ctrl+S` no dispara nada todavía — `QDialog.DialogCode.Accepted == 1`). Los 5
`test_escape_cierra_el_dialogo_sin_guardar` **ya pasan** en este punto (comportamiento nativo de
`QDialog`, sin código de este sprint) — quedan como regresión documentada, no como test que se
espera roto.

- [ ] **Step 3: Implementar `Ctrl+S` en los 5 diálogos**

En `app/views/expedientes.py`, imports — cambiar:

```python
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
```

a:

```python
from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
```

y en `ExpedienteFormDialog.__init__`, cambiar:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
```

a:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
        # Ctrl+S = guardar (Sprint 32). Esc = cancelar ya viene gratis de
        # QDialog.keyPressEvent() (reject() por defecto) -- no requiere codigo aqui.
        self.atajo_guardar = QShortcut(QKeySequence("Ctrl+S"), self)
        self.atajo_guardar.activated.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
```

En `app/views/obligaciones.py`, imports — cambiar:

```python
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
```

a:

```python
from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
```

y en `ObligacionFormDialog.__init__`, cambiar:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)

        self.layout_formulario = QFormLayout()
```

a:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
        # Ctrl+S = guardar (Sprint 32). Esc = cancelar ya viene gratis de
        # QDialog.keyPressEvent() (reject() por defecto) -- no requiere codigo aqui.
        self.atajo_guardar = QShortcut(QKeySequence("Ctrl+S"), self)
        self.atajo_guardar.activated.connect(self._guardar_y_cerrar)

        self.layout_formulario = QFormLayout()
```

En `app/views/abonos.py`, imports — cambiar:

```python
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDateEdit, QDialog, QFormLayout, QLineEdit, QMessageBox, QPushButton
```

a:

```python
from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QDateEdit, QDialog, QFormLayout, QLineEdit, QMessageBox, QPushButton
```

y en `AbonoFormDialog.__init__`, cambiar:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
```

a:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
        # Ctrl+S = guardar (Sprint 32). Esc = cancelar ya viene gratis de
        # QDialog.keyPressEvent() (reject() por defecto) -- no requiere codigo aqui.
        self.atajo_guardar = QShortcut(QKeySequence("Ctrl+S"), self)
        self.atajo_guardar.activated.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
```

En `app/views/eventos_laborales.py`, imports — cambiar:

```python
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QComboBox, QDateEdit, QDialog, QFormLayout, QMessageBox, QPushButton
```

a:

```python
from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QComboBox, QDateEdit, QDialog, QFormLayout, QMessageBox, QPushButton
```

y en `EventoLaboralFormDialog.__init__`, cambiar:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
```

a:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
        # Ctrl+S = guardar (Sprint 32). Esc = cancelar ya viene gratis de
        # QDialog.keyPressEvent() (reject() por defecto) -- no requiere codigo aqui.
        self.atajo_guardar = QShortcut(QKeySequence("Ctrl+S"), self)
        self.atajo_guardar.activated.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
```

En `app/views/configuracion.py`, imports — cambiar:

```python
from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
```

a:

```python
from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
```

y en `ParametroFormDialog.__init__`, cambiar:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
```

a:

```python
        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
        # Ctrl+S = guardar (Sprint 32). Esc = cancelar ya viene gratis de
        # QDialog.keyPressEvent() (reject() por defecto) -- no requiere codigo aqui.
        self.atajo_guardar = QShortcut(QKeySequence("Ctrl+S"), self)
        self.atajo_guardar.activated.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
```

- [ ] **Step 4: Correr los 5 archivos de test para verificar que pasan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_expedientes.py tests/views/test_obligaciones.py tests/views/test_abonos.py tests/views/test_eventos_laborales.py tests/views/test_configuracion.py -v`
Expected: todos PASS (los 10 tests nuevos + todos los originales de los 5 archivos).

- [ ] **Step 5: Ruff**

Run: `"<python>" -m ruff check app/views/expedientes.py app/views/obligaciones.py app/views/abonos.py app/views/eventos_laborales.py app/views/configuracion.py tests/views/test_expedientes.py tests/views/test_obligaciones.py tests/views/test_abonos.py tests/views/test_eventos_laborales.py tests/views/test_configuracion.py`
Expected: ninguna línea **nueva o modificada** por este Step aparece en la salida (algunos de estos
archivos pueden tener deuda de lint preexistente en líneas que este task no toca — no es
responsabilidad de esta tarea corregirla).

- [ ] **Step 6: Commit**

```bash
git add app/views/expedientes.py app/views/obligaciones.py app/views/abonos.py \
  app/views/eventos_laborales.py app/views/configuracion.py \
  tests/views/test_expedientes.py tests/views/test_obligaciones.py tests/views/test_abonos.py \
  tests/views/test_eventos_laborales.py tests/views/test_configuracion.py
git commit -m "$(cat <<'EOF'
feat(sprint32): agregar atajo Ctrl+S a los 5 dialogos de formulario y fijar el comportamiento de Esc

EOF
)"
```

---

### Task 5: Actualizar la Guía de Usuario (breadcrumb, atajos, botón Parámetros activo)

**Files:**
- Modify: `docs/GUIA_USUARIO.md`

- [ ] **Step 1: Actualizar la sección de navegación**

Cambiar el encabezado de la guía de:

```markdown
> **Última actualización:** 2026-08-03 — refleja el estado de Civil/Familia, Comercial, Sancionatorio,
> Honorarios/Litigio, Laboral, Tributario, exportación de liquidaciones a PDF/Word, los botones de
> navegación (Volver/Inicio) y de editar/eliminar expediente, y la pantalla "⚙ Parámetros" de parámetros
> legales versionados. Cada vez que se complete un sprint nuevo de [`Pendientes.md`](../Pendientes.md),
> esta guía se actualiza para que nunca quede desactualizada respecto al programa real.
```

a:

```markdown
> **Última actualización:** 2026-08-06 — refleja el estado de Civil/Familia, Comercial, Sancionatorio,
> Honorarios/Litigio, Laboral, Tributario, exportación de liquidaciones a PDF/Word, los botones de
> navegación (Volver/Inicio/Parámetros) con íconos y estado activo, el breadcrumb de contexto y los
> atajos de teclado de navegación y de los formularios, la edición/eliminación de expediente, y la
> pantalla de parámetros legales versionados. Cada vez que se complete un sprint nuevo de
> [`Pendientes.md`](../Pendientes.md), esta guía se actualiza para que nunca quede desactualizada
> respecto al programa real.
```

Cambiar el bloque de la barra de navegación de:

```markdown
En la parte superior de la ventana hay botones de navegación:

- **← Volver** — regresa a la pantalla anterior (por ejemplo, de Resultado de Liquidación a Detalle de
  Expediente, y de ahí a la Lista de Expedientes). Recuerda el orden exacto en que navegaste, no solo "la
  pantalla anterior en general". Está oculto cuando no hay a dónde volver (por ejemplo, recién abierto el
  programa).
- **🏠 Inicio** — regresa directo a la Lista de Expedientes sin importar en qué pantalla estés. Está
  oculto cuando ya estás en la Lista de Expedientes.
- **⚙ Parámetros** — siempre visible, en cualquier pantalla; te lleva a la pantalla de parámetros legales
  versionados (ver punto 4 arriba).
```

a:

```markdown
En la parte superior de la ventana hay una barra de navegación con tres botones y, a su derecha, un
texto de "breadcrumb" que muestra en qué expediente y pantalla estás parado en cada momento (por
ejemplo, "Expedientes › Radicado 2026-00123 › Liquidación"):

- **Volver** — regresa a la pantalla anterior (por ejemplo, de Resultado de Liquidación a Detalle de
  Expediente, y de ahí a la Lista de Expedientes). Recuerda el orden exacto en que navegaste, no solo "la
  pantalla anterior en general". Está oculto cuando no hay a dónde volver (por ejemplo, recién abierto el
  programa). Atajo de teclado: **Alt+Izquierda** o **Retroceso (Backspace)**.
- **Inicio** — regresa directo a la Lista de Expedientes sin importar en qué pantalla estés. Está
  oculto cuando ya estás en la Lista de Expedientes. Atajo de teclado: **Ctrl+Inicio**.
- **Parámetros** — siempre visible, en cualquier pantalla; te lleva a la pantalla de parámetros legales
  versionados (ver punto 4 arriba). Se resalta con el color de marca de BASTIUM mientras estás dentro de
  esa pantalla, para que sea evidente cuál tienes abierta.

En los formularios (Nuevo expediente, Agregar obligación, Agregar abono, Agregar evento contractual,
Agregar valor de parámetro): **Ctrl+S** guarda y cierra el formulario (equivale a hacer clic en
"Guardar"), y **Esc** lo cierra sin guardar nada.
```

Nota: el resto del documento sigue mencionando "⚙ Parámetros" (con el emoji, ya retirado del botón
real desde el Sprint 31) en otras ~10 apariciones fuera de este bloque de navegación — esa limpieza
de deuda documental es del Sprint 31 (íconos), no de este; no se toca en este task para mantener el
commit angosto y enfocado en lo que Sprint 32 cambia de verdad (breadcrumb + atajos + estado activo).

- [ ] **Step 2: Commit**

```bash
git add docs/GUIA_USUARIO.md
git commit -m "$(cat <<'EOF'
docs: documentar el breadcrumb, los atajos de teclado y el boton Parametros activo

EOF
)"
```

---

### Task 6: Verificación final y cierre técnico del sprint

**Files:** ninguno nuevo — solo verificación.

- [ ] **Step 1: Correr toda la suite del proyecto**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest -v`
Expected: todos los tests en verde — los ~21 nuevos de este plan (5 de Task 1, 3 de Task 2, 3 de
Task 3, 10 de Task 4) más todos los existentes, sin cambios de comportamiento en los casos ya
cubiertos.

- [ ] **Step 2: Ruff sobre todo el repo**

Run: `"<python>" -m ruff check .`
Expected: el repo puede tener deuda de lint preexistente no relacionada con este sprint (mismo
patrón documentado en los Sprints 26/27/28/31 — no usar "cero errores totales" como criterio). En
vez de eso:
1. Guardar la salida de este comando (ej. en el scratchpad de la sesión que ejecute este plan).
2. Correr `git stash`, volver a correr `ruff check .` sobre el estado previo a este plan, guardar esa
   salida también, y `git stash pop` para restaurar los cambios.
3. Diferenciar ambas salidas: confirmar que ninguna línea **nueva** aparece que mencione
   `app/views/main_window.py`, `app/views/expedientes.py`, `app/views/obligaciones.py`,
   `app/views/abonos.py`, `app/views/eventos_laborales.py`, `app/views/configuracion.py`,
   `resources/theme.qss`, `docs/GUIA_USUARIO.md`, o cualquiera de los 6 archivos de test tocados
   por este plan.

- [ ] **Step 3: Verificación manual (no automatizable) — recordatorio explícito**

La Definición de Hecho del sprint pide "el usuario puede navegar solo con teclado entre las
pantallas principales" y "la barra de navegación muestra claramente en qué expediente/pantalla se
está parado" — ambos puntos quedan cubiertos por tests automatizados en las Tasks 1-3, pero el
sprint también se beneficia de una pasada visual manual (no automatizable con `pytest-qt`, que no
puede aserciones sobre "se ve bien"): ejecutar `python main.py` y confirmar (a) el breadcrumb se lee
con claridad junto a los 3 botones sin quedar cortado en una ventana de 1000×700 (tamaño por defecto
de `main.py`), (b) el botón "Parámetros" cambia visualmente de color al entrar y salir de esa
pantalla, (c) `Tab` permite alcanzar los 3 botones de la barra y `Alt+Izquierda`/`Backspace`/
`Ctrl+Home` navegan sin usar el mouse, (d) dentro de cualquier formulario, escribir texto en un
campo y luego presionar `Backspace` para borrar un carácter funciona con normalidad (confirma que el
atajo de `MainWindow` no interfiere con la edición, tal como predice el Architecture). No se ejecuta
en este task; se documenta como pendiente explícito para quien haga la revisión manual antes de
fusionar.

- [ ] **Step 4 — NO EJECUTAR: recordatorio explícito**

**No editar `Pendientes.md`** (ni el índice, ni la sección del Sprint 32, ni ningún marcador
`✅ Completado`) — el orquestador humano actualiza ese archivo centralmente una vez fusionado el
sprint, siguiendo el mismo patrón que los Sprints 26 y 31. Este plan termina en el Step 3 de esta
Task.

**No editar `README.md`**: Sprint 32 es un cambio de navegación/UI interno sin impacto en la
descripción funcional de alto nivel del proyecto que vive en `README.md` — la actualización
user-facing relevante ya se hizo de forma angosta en la Task 5 sobre `docs/GUIA_USUARIO.md`.

---

## Self-review notes

- **Cobertura del spec:** breadcrumb contextual que se actualiza según la pantalla activa (Task 1,
  con el ejemplo textual exacto del hallazgo — "Expedientes › Radicado ... › Liquidación" —
  reproducido en `test_breadcrumb_incluye_liquidacion_al_mostrar_el_resultado`); atajos de teclado
  básicos `Alt+Izquierda`/`Backspace` (Volver) y `Ctrl+Home` (Inicio) (Task 2); `Ctrl+S`/`Esc` en los
  5 diálogos de formulario existentes (Task 4, `Esc` fijado como test de regresión sin código nuevo
  porque ya es comportamiento nativo de `QDialog`); reemplazo de texto+emoji por ícono+texto con
  estado "activo"/"inactivo" — la parte de ícono+texto ya la dejó hecha el Sprint 31, este plan
  agrega la parte de estado activo/inactivo que faltaba (Task 3). Decisión de diseño
  sidebar-vs-toolbar resuelta explícitamente en el Architecture, con justificación y nota de
  reevaluación futura, tal como pedía el spec.
- **Máquina de estados de navegación intacta:** ningún Step de este plan modifica `_pages`,
  `_history` o la firma de `show_page()`/`_volver()`/`_ir_inicio()` — todas las adiciones son nuevos
  métodos (`_actualizar_breadcrumb`, `_texto_breadcrumb`, `_obtener_radicado`,
  `_crear_atajos_teclado`, `_actualizar_estado_activo_navegacion`) y nuevas líneas dentro de métodos
  existentes, nunca una reescritura de la lógica de navegación ya probada.
- **Riesgo de `QShortcut` no disparándose bajo pytest-qt en modo offscreen:** identificado y resuelto
  empíricamente en "Contexto compartido" (receta `show()` + `waitExposed()` + `activateWindow()` +
  `wait(50)`, confirmada en este entorno con PySide6 6.11.1) — sin documentar esto, alguien
  implementando este plan perdería tiempo con tests que fallan de forma confusa (el `keyClick` llega
  al widget pero el atajo nunca se activa porque `isActiveWindow()` quedó en `False`).
- **Sin placeholders:** cada Step trae el `old_string`/`new_string` completo a aplicar o el bloque de
  test completo a agregar — ninguno dice "similar al de arriba" sin el código real, incluidos los 5
  diálogos casi idénticos de la Task 4 (cada uno con su propio diff exacto, porque el texto que lo
  rodea difiere ligeramente entre archivos).
- **Consistencia de tipos:** `QShortcut`/`QKeySequence` se usan con la misma forma en las 4 tareas
  que los tocan (`QShortcut(QKeySequence(...), <parent>)` + `.activated.connect(<slot>)`); la
  convención `setProperty("class", "primary"/"")` reutiliza exactamente la introducida por el
  Sprint 31, sin inventar un tercer valor.

### Critical Files for Implementation
- app/views/main_window.py
- resources/theme.qss
- tests/views/test_main_window.py
- app/views/expedientes.py
- docs/GUIA_USUARIO.md
