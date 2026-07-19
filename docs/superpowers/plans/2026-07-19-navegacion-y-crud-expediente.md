# Navegación (Volver/Inicio) y CRUD de Expediente Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add "Volver" / "Inicio" navigation buttons to the app shell, and "Editar" / "Eliminar" buttons per row in the expedientes list, so users can navigate back/home and fully manage (create, read, update, delete) an expediente.

**Architecture:** `MainWindow` gains a page-history stack (`list[str]`) and a fixed top `QToolBar` with two buttons wired to pop/clear that stack. `ExpedientesListView`'s table grows two action columns hosting per-row `QPushButton`s; the existing `NuevoExpedienteDialog` is generalized into `ExpedienteFormDialog` that pre-fills and updates when given an existing `Expediente`, and a reinforced two-step confirmation (Yes/No + type-the-radicado) guards deletion, which relies on the cascade already configured on the `Expediente` model.

**Tech Stack:** Python, PySide6 (Qt), SQLAlchemy, pytest + pytest-qt.

Design spec: `docs/superpowers/specs/2026-07-19-navegacion-y-crud-expediente-design.md`

---

## File Structure

- Modify: `app/views/main_window.py` — page-history stack, `_volver`/`_ir_inicio`, nav toolbar.
- Modify: `app/views/expedientes.py` — rename `NuevoExpedienteDialog` → `ExpedienteFormDialog` with edit support, add Editar/Eliminar columns and handlers.
- Modify: `tests/views/test_main_window.py` — history + toolbar tests.
- Modify: `tests/views/test_expedientes.py` — updated dialog import/name, edit/delete tests.

No new files, no repository/service layer introduced (per spec, follows the existing inline-session pattern).

---

### Task 1: Page-history stack in `MainWindow`

**Files:**
- Modify: `app/views/main_window.py`
- Test: `tests/views/test_main_window.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/views/test_main_window.py`:

```python
def test_volver_regresa_a_la_pagina_anterior(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("detalle")
    window._volver()

    assert window.stacked_widget.currentWidget() is window.expedientes_page


def test_volver_respeta_el_orden_de_visitas(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("detalle")
    window.show_page("resultado")
    window._volver()

    assert window.stacked_widget.currentWidget() is window.detalle_page

    window._volver()

    assert window.stacked_widget.currentWidget() is window.expedientes_page


def test_volver_sin_historial_no_hace_nada(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window._volver()

    assert window.stacked_widget.currentWidget() is window.expedientes_page


def test_ir_inicio_limpia_el_historial_y_regresa_a_expedientes(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("detalle")
    window.show_page("resultado")
    window._ir_inicio()

    assert window.stacked_widget.currentWidget() is window.expedientes_page
    assert window._history == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/views/test_main_window.py -v`
Expected: the 4 new tests FAIL with `AttributeError: 'MainWindow' object has no attribute '_volver'` (and `_ir_inicio`).

- [ ] **Step 3: Implement the history stack**

Replace the body of `app/views/main_window.py` with:

```python
from PySide6.QtWidgets import QMainWindow, QStackedWidget

from app.views.expedientes import ExpedientesListView
from app.views.expediente_detalle import ExpedienteDetallePage
from app.views.liquidaciones import ResultadoLiquidacionView


class MainWindow(QMainWindow):
    """Ventana principal: aloja las 3 pantallas del flujo y la navegacion entre ellas."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BASTIUM - Ecosistema de Liquidacion Forense")

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.expedientes_page = ExpedientesListView(on_expediente_abierto=self._abrir_detalle)
        self.detalle_page = ExpedienteDetallePage(on_liquidado=self._mostrar_resultado)
        self.resultado_page = ResultadoLiquidacionView()

        self.stacked_widget.addWidget(self.expedientes_page)
        self.stacked_widget.addWidget(self.detalle_page)
        self.stacked_widget.addWidget(self.resultado_page)

        self._pages = {
            "expedientes": self.expedientes_page,
            "detalle": self.detalle_page,
            "resultado": self.resultado_page,
        }

        self._history: list[str] = []
        self._current_page_name = "expedientes"

        self.show_page("expedientes")

    def show_page(self, name: str, add_to_history: bool = True) -> None:
        if add_to_history and self._current_page_name != name:
            self._history.append(self._current_page_name)
        self.stacked_widget.setCurrentWidget(self._pages[name])
        self._current_page_name = name

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/views/test_main_window.py -v`
Expected: all tests PASS (the 4 new ones plus the 4 pre-existing ones).

- [ ] **Step 5: Commit**

```bash
git add app/views/main_window.py tests/views/test_main_window.py
git commit -m "feat: add page-history stack to MainWindow for back/home navigation"
```

---

### Task 2: Nav toolbar (Volver / Inicio buttons) in `MainWindow`

**Files:**
- Modify: `app/views/main_window.py`
- Test: `tests/views/test_main_window.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/views/test_main_window.py`:

```python
def test_botones_navegacion_ocultos_en_pagina_inicial(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert window.boton_volver.isVisible() is False
    assert window.boton_inicio.isVisible() is False


def test_botones_navegacion_visibles_al_entrar_a_detalle(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window.show_page("detalle")

    assert window.boton_volver.isVisible() is True
    assert window.boton_inicio.isVisible() is True


def test_click_en_volver_navega_a_la_pagina_anterior(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window.show_page("detalle")
    window.boton_volver.click()

    assert window.stacked_widget.currentWidget() is window.expedientes_page


def test_click_en_inicio_regresa_a_expedientes_y_oculta_los_botones(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window.show_page("detalle")
    window.show_page("resultado")
    window.boton_inicio.click()

    assert window.stacked_widget.currentWidget() is window.expedientes_page
    assert window.boton_volver.isVisible() is False
    assert window.boton_inicio.isVisible() is False
```

Note: `window.show()` is required here — `isVisible()` only reflects real on-screen visibility (inherited from ancestors) once the top-level window has actually been shown, otherwise `setVisible(True)` calls would pass vacuously (same pattern already used in `tests/views/test_obligaciones.py`).

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/views/test_main_window.py -v`
Expected: the 4 new tests FAIL with `AttributeError: 'MainWindow' object has no attribute 'boton_volver'`.

- [ ] **Step 3: Implement the toolbar**

In `app/views/main_window.py`, change the import line:

```python
from PySide6.QtWidgets import QMainWindow, QPushButton, QStackedWidget, QToolBar
```

Add a call to `self._crear_barra_navegacion()` right before `self.show_page("expedientes")` in `__init__`:

```python
        self._history: list[str] = []
        self._current_page_name = "expedientes"

        self._crear_barra_navegacion()
        self.show_page("expedientes")
```

Add the new method and update `show_page` to refresh button visibility (insert `_crear_barra_navegacion` right after `__init__`, and add the call to `_actualizar_botones_navegacion` at the end of `show_page`):

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
```

`_actualizar_botones_navegacion` is called both from `_crear_barra_navegacion` (to set the correct initial hidden state before the first `show_page` call) and from every `show_page` call thereafter. Since `_crear_barra_navegacion` runs before the first `show_page("expedientes")` call, and `show_page` itself also calls `_actualizar_botones_navegacion`, the buttons stay correctly hidden/shown after that first call too — no ordering issue.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/views/test_main_window.py -v`
Expected: all tests PASS (8 total in the file).

- [ ] **Step 5: Commit**

```bash
git add app/views/main_window.py tests/views/test_main_window.py
git commit -m "feat: add Volver/Inicio toolbar buttons to MainWindow"
```

---

### Task 3: Generalize `NuevoExpedienteDialog` into `ExpedienteFormDialog` (edit support)

**Files:**
- Modify: `app/views/expedientes.py`
- Test: `tests/views/test_expedientes.py`

- [ ] **Step 1: Update existing tests to the new class name, and add the failing edit-mode test**

In `tests/views/test_expedientes.py`, change the import line:

```python
from app.views.expedientes import ExpedientesListView, ExpedienteFormDialog
```

Replace every `NuevoExpedienteDialog(` call in the file (in `test_dialogo_crea_expediente_civil_familia` and `test_dialogo_deshabilita_areas_no_implementadas`) with `ExpedienteFormDialog(`.

Then append this new test to the same file:

```python
def test_dialogo_edita_expediente_existente(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-003",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        juzgado="Juzgado 5",
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    expediente_a_editar = session.get(Expediente, expediente_id)

    dialog = ExpedienteFormDialog(expediente=expediente_a_editar)
    qtbot.addWidget(dialog)
    session.close()

    assert dialog.windowTitle() == "Editar expediente"
    assert dialog.campo_radicado.text() == "2026-003"
    assert dialog.campo_juzgado.text() == "Juzgado 5"

    dialog.campo_demandante.setText("Ana Maria")
    resultado_id = dialog.guardar()

    assert resultado_id == expediente_id

    session = session_module.get_session()
    assert session.query(Expediente).count() == 1
    actualizado = session.get(Expediente, expediente_id)
    assert actualizado.demandante == "Ana Maria"
    assert actualizado.radicado == "2026-003"
    session.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/views/test_expedientes.py -v`
Expected: all tests in the file FAIL with `ImportError: cannot import name 'ExpedienteFormDialog'`.

- [ ] **Step 3: Implement the generalized dialog**

In `app/views/expedientes.py`, replace the `NuevoExpedienteDialog` class with:

```python
class ExpedienteFormDialog(QDialog):
    def __init__(self, parent=None, expediente: Expediente | None = None):
        super().__init__(parent)
        self._expediente_id = expediente.id if expediente else None
        self.setWindowTitle("Editar expediente" if expediente else "Nuevo expediente")

        self.campo_radicado = QLineEdit()
        self.campo_demandante = QLineEdit()
        self.campo_demandado = QLineEdit()
        self.campo_juzgado = QLineEdit()
        self.campo_fecha_corte = QDateEdit(QDate.currentDate())
        self.campo_fecha_corte.setCalendarPopup(True)

        self.combo_area = QComboBox()
        for codigo, etiqueta, habilitada in AREAS_DERECHO:
            self.combo_area.addItem(etiqueta, userData=codigo)
            if not habilitada:
                indice = self.combo_area.count() - 1
                item = self.combo_area.model().item(indice)
                item.setEnabled(False)
                item.setToolTip("Proximamente")

        if expediente:
            self.campo_radicado.setText(expediente.radicado)
            self.campo_demandante.setText(expediente.demandante)
            self.campo_demandado.setText(expediente.demandado)
            self.campo_juzgado.setText(expediente.juzgado or "")
            self.campo_fecha_corte.setDate(
                QDate(
                    expediente.fecha_corte_default.year,
                    expediente.fecha_corte_default.month,
                    expediente.fecha_corte_default.day,
                )
            )
            indice_area = self.combo_area.findData(expediente.area_derecho.value)
            if indice_area >= 0:
                self.combo_area.setCurrentIndex(indice_area)

        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
        layout.addRow("Radicado", self.campo_radicado)
        layout.addRow("Demandante", self.campo_demandante)
        layout.addRow("Demandado", self.campo_demandado)
        layout.addRow("Area del derecho", self.combo_area)
        layout.addRow("Juzgado", self.campo_juzgado)
        layout.addRow("Fecha de corte", self.campo_fecha_corte)
        layout.addRow(boton_guardar)
        self.setLayout(layout)

        self._expediente_id_creado = None

    def guardar(self) -> int:
        if not self.campo_radicado.text().strip():
            raise ValueError("El radicado es obligatorio.")

        qdate = self.campo_fecha_corte.date()
        fecha_corte = date(qdate.year(), qdate.month(), qdate.day())

        session = session_module.get_session()
        if self._expediente_id is not None:
            expediente = session.get(Expediente, self._expediente_id)
        else:
            expediente = Expediente()
            session.add(expediente)

        expediente.radicado = self.campo_radicado.text().strip()
        expediente.demandante = self.campo_demandante.text().strip()
        expediente.demandado = self.campo_demandado.text().strip()
        expediente.area_derecho = AreaDerecho(self.combo_area.currentData())
        expediente.juzgado = self.campo_juzgado.text().strip() or None
        expediente.fecha_corte_default = fecha_corte

        session.commit()
        expediente_id = expediente.id
        session.close()
        return expediente_id

    def _guardar_y_cerrar(self) -> None:
        try:
            self._expediente_id_creado = self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos incompletos", str(error))
```

Then update the one call site further down in the same file, inside `ExpedientesListView._abrir_dialogo_nuevo`:

```python
    def _abrir_dialogo_nuevo(self) -> None:
        dialogo = ExpedienteFormDialog(self)
        if dialogo.exec():
            self.refrescar()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/views/test_expedientes.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/views/expedientes.py tests/views/test_expedientes.py
git commit -m "refactor: generalize NuevoExpedienteDialog into ExpedienteFormDialog with edit support"
```

---

### Task 4: Editar/Eliminar columns and Editar wiring in `ExpedientesListView`

**Files:**
- Modify: `app/views/expedientes.py`
- Test: `tests/views/test_expedientes.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/views/test_expedientes.py`:

```python
def test_tabla_tiene_columnas_de_editar_y_eliminar(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-005",
            demandante="Pedro",
            demandado="Rosa",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    assert view.tabla.columnCount() == 6
    assert view.tabla.cellWidget(0, 4) is not None
    assert view.tabla.cellWidget(0, 5) is not None


def test_boton_editar_abre_dialogo_con_el_expediente_de_la_fila(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-004",
            demandante="Carlos",
            demandado="Maria",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    dialogos_creados = []

    class _DialogStub:
        def __init__(self, parent, expediente):
            dialogos_creados.append(expediente.radicado)

        def exec(self):
            return False

    monkeypatch.setattr("app.views.expedientes.ExpedienteFormDialog", _DialogStub)

    view._editar_expediente(view._expediente_ids_por_fila[0])

    assert dialogos_creados == ["2026-004"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/views/test_expedientes.py -v`
Expected: `test_tabla_tiene_columnas_de_editar_y_eliminar` FAILS on `assert view.tabla.columnCount() == 6` (currently 4); `test_boton_editar_abre_dialogo_con_el_expediente_de_la_fila` FAILS with `AttributeError: 'ExpedientesListView' object has no attribute '_editar_expediente'`.

- [ ] **Step 3: Implement the action columns**

In `app/views/expedientes.py`, inside `ExpedientesListView.__init__`, change the table construction:

```python
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["Radicado", "Demandante", "Demandado", "Area", "Editar", "Eliminar"]
        )
```

Replace `refrescar` with:

```python
    def refrescar(self) -> None:
        session = session_module.get_session()
        expedientes = session.query(Expediente).all()

        self.tabla.setRowCount(len(expedientes))
        self._expediente_ids_por_fila = []
        for fila, expediente in enumerate(expedientes):
            self.tabla.setItem(fila, 0, QTableWidgetItem(expediente.radicado))
            self.tabla.setItem(fila, 1, QTableWidgetItem(expediente.demandante))
            self.tabla.setItem(fila, 2, QTableWidgetItem(expediente.demandado))
            self.tabla.setItem(fila, 3, QTableWidgetItem(expediente.area_derecho.value))

            boton_editar = QPushButton("Editar")
            boton_editar.clicked.connect(
                lambda _checked=False, id_=expediente.id: self._editar_expediente(id_)
            )
            self.tabla.setCellWidget(fila, 4, boton_editar)

            boton_eliminar = QPushButton("Eliminar")
            boton_eliminar.clicked.connect(
                lambda _checked=False, id_=expediente.id: self._eliminar_expediente(id_)
            )
            self.tabla.setCellWidget(fila, 5, boton_eliminar)

            self._expediente_ids_por_fila.append(expediente.id)
        session.close()

    def _editar_expediente(self, expediente_id: int) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, expediente_id)
        dialogo = ExpedienteFormDialog(self, expediente=expediente)
        session.close()
        if dialogo.exec():
            self.refrescar()
```

`_eliminar_expediente` is referenced by the button wiring above but implemented in Task 5 — add a placeholder-free minimal stub now so this task's tests (which don't touch delete) still pass and the file stays valid Python:

```python
    def _eliminar_expediente(self, expediente_id: int) -> None:
        raise NotImplementedError
```

(Task 5 replaces this stub with the real implementation in its own Step 3 — it is not left in the codebase.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/views/test_expedientes.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/views/expedientes.py tests/views/test_expedientes.py
git commit -m "feat: add Editar/Eliminar columns to expedientes table with Editar wiring"
```

---

### Task 5: Eliminar handler with reinforced confirmation

**Files:**
- Modify: `app/views/expedientes.py`
- Test: `tests/views/test_expedientes.py`

- [ ] **Step 1: Write the failing tests**

Add `from decimal import Decimal` and `from PySide6.QtWidgets import QMessageBox` to the imports at the top of `tests/views/test_expedientes.py`, and replace the existing `from database.models import AreaDerecho, Base, Expediente` line with:

```python
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion
```

(`Base` must stay — it's already used by `_sesion_en_memoria` in this file.)

Append these tests:

```python
def test_eliminar_expediente_confirmado_borra_el_registro(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-006",
        demandante="Sofia",
        demandado="Diego",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "app.views.expedientes.QInputDialog.getText",
        lambda *args, **kwargs: ("2026-006", True),
    )

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view._eliminar_expediente(expediente_id)

    session = session_module.get_session()
    assert session.query(Expediente).count() == 0
    session.close()
    assert view.tabla.rowCount() == 0


def test_eliminar_expediente_con_radicado_incorrecto_no_borra(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-007",
        demandante="Laura",
        demandado="Mario",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "app.views.expedientes.QInputDialog.getText",
        lambda *args, **kwargs: ("radicado-equivocado", True),
    )
    monkeypatch.setattr("app.views.expedientes.QMessageBox.warning", lambda *args, **kwargs: None)

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view._eliminar_expediente(expediente_id)

    session = session_module.get_session()
    assert session.query(Expediente).count() == 1
    session.close()


def test_eliminar_expediente_cancelado_en_primer_dialogo_no_borra(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-008",
        demandante="Elena",
        demandado="Pablo",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view._eliminar_expediente(expediente_id)

    session = session_module.get_session()
    assert session.query(Expediente).count() == 1
    session.close()


def test_eliminar_expediente_borra_en_cascada_sus_obligaciones(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-009",
        demandante="Ines",
        demandado="Tomas",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()

    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Capital",
            categoria="CAPITAL",
            fecha_origen=date(2026, 1, 1),
            valor=Decimal("1000000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "app.views.expedientes.QInputDialog.getText",
        lambda *args, **kwargs: ("2026-009", True),
    )

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view._eliminar_expediente(expediente_id)

    session = session_module.get_session()
    assert session.query(Expediente).count() == 0
    assert session.query(Obligacion).count() == 0
    session.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/views/test_expedientes.py -v`
Expected: the 4 new tests FAIL with `NotImplementedError` (raised by the Task 4 stub).

- [ ] **Step 3: Implement the reinforced-confirmation delete**

In `app/views/expedientes.py`, add `QInputDialog` to the PySide6 import block:

```python
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
```

Replace the `_eliminar_expediente` stub with:

```python
    def _eliminar_expediente(self, expediente_id: int) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, expediente_id)
        radicado = expediente.radicado
        session.close()

        respuesta = QMessageBox.question(
            self,
            "Eliminar expediente",
            f"¿Eliminar el expediente '{radicado}'? Se borraran tambien todas sus "
            "obligaciones, abonos y registros de auditoria asociados. Esta accion "
            "no se puede deshacer.",
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return

        texto, ok = QInputDialog.getText(
            self,
            "Confirmar eliminacion",
            f"Escribe el radicado '{radicado}' para confirmar:",
        )
        if not ok or texto.strip() != radicado:
            QMessageBox.warning(
                self, "Eliminacion cancelada", "El radicado no coincide. No se elimino el expediente."
            )
            return

        session = session_module.get_session()
        expediente = session.get(Expediente, expediente_id)
        session.delete(expediente)
        session.commit()
        session.close()

        self.refrescar()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/views/test_expedientes.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Run the full test suite**

Run: `python -m pytest -v`
Expected: all tests PASS (no regressions in `tests/views/test_main_window.py` or elsewhere from the `show_page` signature change or the dialog rename).

- [ ] **Step 6: Commit**

```bash
git add app/views/expedientes.py tests/views/test_expedientes.py
git commit -m "feat: add reinforced-confirmation Eliminar handler for expedientes"
```

---

## Self-Review Notes

- **Spec coverage:** Section 1 (Volver/Inicio, history stack, hide-not-disable) → Tasks 1–2. Section 2 (Editar/Eliminar columns, dialog reuse with pre-fill, reinforced delete confirmation, cascade reliance, no new repository layer) → Tasks 3–5.
- **Placeholder scan:** the only stub (`_eliminar_expediente` raising `NotImplementedError` at the end of Task 4) is intentional and explicitly removed in Task 5 Step 3 — it exists for exactly one task boundary so Task 4's tests run against valid, importable code.
- **Type/name consistency:** `ExpedienteFormDialog(parent=None, expediente=None)` signature is identical across Tasks 3, 4, and its call sites (`_abrir_dialogo_nuevo`, `_editar_expediente`); `_expediente_ids_por_fila`, `show_page(name, add_to_history=True)`, `boton_volver`/`boton_inicio` names are consistent everywhere they're referenced.
