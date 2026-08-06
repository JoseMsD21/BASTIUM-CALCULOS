# Sprint 35 — Búsqueda, filtros y estados vacíos en listados Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `ExpedientesListView` (`app/views/expedientes.py`) deja de cargar y mostrar la tabla
completa de expedientes sin ningún medio de acotarla: gana un campo de búsqueda (radicado,
demandante, demandado) y un filtro por área del derecho, ambos combinables y aplicados en vivo
sobre `refrescar()`; sus columnas ganan ordenamiento (`setSortingEnabled(True)`); y cuando la
tabla queda sin filas (base de datos vacía, o filtro/búsqueda sin resultados) se reemplaza la
tabla en blanco por un estado vacío explícito con mensaje y botón de acción contextual ("Crear
expediente" si la base de datos está realmente vacía, "Limpiar filtros" si hay expedientes pero
ninguno coincide con la búsqueda/filtro actual). No se agrega paginación (fuera de alcance
explícito del sprint, ver spec) ni se toca `ExpedienteFormDialog` (esa clase vive en el mismo
archivo pero el Sprint 34, que se ejecuta después de este plan en el mismo branch, depende de que
este plan no la modifique).

**Architecture:** Todo el filtrado ocurre en memoria dentro de `refrescar()` (se sigue trayendo
`session.query(Expediente).all()` completo, igual que hoy, y se filtra con una función Python
antes de poblar la tabla) — no se agrega ninguna cláusula `WHERE`/índice nuevo porque el sprint es
de UX de búsqueda/filtro/orden, no de rendimiento (eso es Sprint 25, no bloqueante). Habilitar
`setSortingEnabled(True)` en un `QTableWidget` reordena físicamente las filas cuando el usuario
hace clic en un encabezado de columna, lo que rompe silenciosamente cualquier código que asuma que
"la fila N sigue siendo el N-ésimo expediente insertado" — el código actual de
`_abrir_seleccionado` tiene exactamente ese supuesto (indexa una lista Python
`self._expediente_ids_por_fila` por número de fila). La corrección elegida es la idiomática de Qt:
guardar el `expediente.id` como `Qt.ItemDataRole.UserRole` en el `QTableWidgetItem` de la columna
0 (los `QTableWidgetItem` — con todos sus roles de datos — sí se mueven junto con la fila cuando
`QTableWidget` ordena; los *cell widgets* de Editar/Eliminar, indexados por índice de fila
persistente, también se mueven correctamente con Qt sin cambios adicionales) y leer el id desde
ahí en el doble clic, en vez de indexar la lista por posición. `self._expediente_ids_por_fila` se
conserva igual (una lista más, en el orden de inserción del último `refrescar()`) porque un test
existente (`test_boton_editar_abre_dialogo_con_el_expediente_de_la_fila`) ya la usa directamente
tras un `refrescar()` sin ordenar — sigue siendo válida en ese uso, simplemente deja de ser la
fuente de verdad para el doble clic. Para evitar que `QTableWidget` reordene filas a mitad de
población (otro gotcha conocido de Qt: poblar con `setSortingEnabled(True)` ya activo puede
mezclar filas mientras se llama a `setItem()` en un bucle), `refrescar()` desactiva el
ordenamiento antes de poblar y lo reactiva al final. El estado vacío es un widget hermano de la
tabla (`QLabel` + `QPushButton`) dentro del mismo `QVBoxLayout`, alternado con
`setVisible()`/`tabla.setVisible()` según el resultado del filtrado — no un `QStackedWidget`,
porque solo hay dos estados simples y ya existe precedente de alternar visibilidad de widgets
completos en este código base (ver `ObligacionFormDialog._actualizar_campos_visibles` en
`app/views/obligaciones.py`). Sobre el ícono de búsqueda: el set mínimo de íconos del Sprint 31
(`home`, `back`, `settings`, `save`, `cancel`, `delete`, `export`) no incluye uno de lupa/buscar, y
`QLineEdit` no tiene una API nativa sencilla para un ícono "leading" sin agregar un
`QAction`/`addAction()` con recorte de padding manual — una pieza de plomería adicional no pedida
por la Definición de Hecho del sprint (que solo exige encontrar un expediente sin scroll manual,
no un ícono específico). Se usa un `QLineEdit` con `placeholderText` descriptivo y sin ícono,
manteniendo el alcance ceñido a búsqueda/filtro/orden/estado-vacío. El botón de acción del estado
vacío reutiliza la convención de clase `QPushButton` del Sprint 31
(`boton.setProperty("class", "primary")`) para que se vea como la acción principal de la pantalla
vacía, consistente con `boton_nuevo`.

**Tech Stack:** Python 3.14, PySide6 6.11 (`QtCore.Qt.ItemDataRole`, `QtCore.Qt.SortOrder`,
`QtWidgets.QTableWidget.setSortingEnabled`, `QtWidgets.QComboBox`, `QtWidgets.QLineEdit`,
`QtWidgets.QLabel`), SQLAlchemy, pytest + pytest-qt (`qtbot`), ruff (line-length 99,
`target-version = "py314"`, reglas `E`/`F`/`I`/`UP`/`B`).

---

### Contexto compartido entre tareas — no repetir en cada una

**Ruta del intérprete de pruebas (todas las tareas):**
`"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe"`.
Si el entorno de ejecución no tiene un display real, anteponer `QT_QPA_PLATFORM=offscreen` a cada
comando `pytest` (ej.: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest ...`).

**Orden de ejecución en el stream (crítico para este plan):** este plan se ejecuta en un branch
recién creado desde `main` **justo después** de que el Sprint 31 (sistema de diseño visual) fue
fusionado a `main`, y **antes** que el Sprint 34 (UX de formularios). Ningún otro sprint toca
`app/views/expedientes.py` antes que este. Por lo tanto el estado de partida real de
`app/views/expedientes.py` (confirmado leyendo el archivo en `main` al escribir este plan, más los
diffs ya fusionados del Sprint 31 sobre ese mismo archivo) es exactamente:

```python
from datetime import date

from PySide6.QtCore import QDate
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

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.views.icons import icon
from database.models import AreaDerecho, Expediente


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

        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
        layout.addRow("Radicado", self.campo_radicado)
        layout.addRow("Demandante", self.campo_demandante)
        layout.addRow("Demandado", self.campo_demandado)
        layout.addRow("Area del derecho", self.combo_area)
        layout.addRow("Juzgado", self.campo_juzgado)
        layout.addRow("Fecha de corte", self.campo_fecha_corte)
        layout.addRow(self.boton_guardar)
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


class ExpedientesListView(QWidget):
    def __init__(self, on_expediente_abierto=None):
        super().__init__()
        self._on_expediente_abierto = on_expediente_abierto

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["Radicado", "Demandante", "Demandado", "Area", "Editar", "Eliminar"]
        )
        self.tabla.cellDoubleClicked.connect(self._abrir_seleccionado)

        self.boton_nuevo = QPushButton("Nuevo expediente")
        self.boton_nuevo.setProperty("class", "primary")
        self.boton_nuevo.clicked.connect(self._abrir_dialogo_nuevo)

        layout = QVBoxLayout()
        layout.addWidget(self.boton_nuevo)
        layout.addWidget(self.tabla)
        self.setLayout(layout)

        self._expediente_ids_por_fila = []
        self.refrescar()

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
            boton_eliminar.setIcon(icon("delete"))
            boton_eliminar.setProperty("class", "destructive")
            boton_eliminar.clicked.connect(
                lambda _checked=False, id_=expediente.id: self._eliminar_expediente(id_)
            )
            self.tabla.setCellWidget(fila, 5, boton_eliminar)

            self._expediente_ids_por_fila.append(expediente.id)
        session.close()

    def _abrir_dialogo_nuevo(self) -> None:
        dialogo = ExpedienteFormDialog(self)
        if dialogo.exec():
            self.refrescar()

    def _abrir_seleccionado(self, fila: int, _columna: int) -> None:
        if self._on_expediente_abierto:
            self._on_expediente_abierto(self._expediente_ids_por_fila[fila])

    def _editar_expediente(self, expediente_id: int) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, expediente_id)
        dialogo = ExpedienteFormDialog(self, expediente=expediente)
        session.close()
        if dialogo.exec():
            self.refrescar()

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

Y el estado de partida de `tests/views/test_expedientes.py` es el archivo original (los 9 tests
que ya existían: `test_lista_muestra_expedientes_existentes`,
`test_dialogo_crea_expediente_civil_familia`, `test_dialogo_habilita_todas_las_areas`,
`test_dialogo_edita_expediente_existente`, `test_tabla_tiene_columnas_de_editar_y_eliminar`,
`test_boton_editar_abre_dialogo_con_el_expediente_de_la_fila`,
`test_eliminar_expediente_confirmado_borra_el_registro`,
`test_eliminar_expediente_con_radicado_incorrecto_no_borra`,
`test_eliminar_expediente_cancelado_en_primer_dialogo_no_borra`,
`test_eliminar_expediente_borra_en_cascada_sus_obligaciones`) más los 3 tests que agregó el Sprint
31 al final del archivo (`test_boton_guardar_del_formulario_tiene_icono_y_clase_primaria`,
`test_boton_nuevo_expediente_tiene_clase_primaria`,
`test_boton_eliminar_de_cada_fila_tiene_icono_y_clase_destructiva`) — releer el archivo real antes
de tocarlo para confirmar que efectivamente termina así; si algo no calza exactamente, conservar la
intención de cada diff de este plan (ubicar por nombre de método/clase, no por número de línea).

**Convención de campos del modelo usados (confirmado leyendo `database/models.py`):**
`Expediente.radicado: str`, `Expediente.demandante: str`, `Expediente.demandado: str`,
`Expediente.area_derecho: AreaDerecho` (enum, `.value` es el código string tipo `"CIVIL_FAMILIA"`).
**No existe ningún campo de "estado"** (abierto/cerrado, activo/archivado, etc.) en el modelo
`Expediente` — el hallazgo del sprint menciona "filtro por área/estado", pero el segundo filtro no
tiene contraparte real en el esquema actual de la base de datos. Este plan implementa el filtro por
área (real) y la búsqueda de texto libre por radicado/demandante/demandado (real, y explícitamente
pedida en "Código nuevo a crear" del spec); no inventa un campo "estado" inexistente. La Definición
de Hecho del sprint ("un usuario puede encontrar un expediente por radicado o filtrar por área")
queda cubierta sin ese campo.

---

### Task 1: Campo de búsqueda + filtro por área en `ExpedientesListView`

**Files:**
- Modify: `app/views/expedientes.py` (imports, `ExpedientesListView.__init__`,
  `ExpedientesListView.refrescar`)
- Modify: `tests/views/test_expedientes.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/views/test_expedientes.py`:

```python
def test_busqueda_filtra_por_radicado(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add_all(
        [
            Expediente(
                radicado="2026-100",
                demandante="Ana",
                demandado="Luis",
                area_derecho=AreaDerecho.CIVIL_FAMILIA,
                fecha_corte_default=date(2026, 1, 1),
            ),
            Expediente(
                radicado="2026-200",
                demandante="Carlos",
                demandado="Maria",
                area_derecho=AreaDerecho.COMERCIAL,
                fecha_corte_default=date(2026, 1, 1),
            ),
        ]
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()
    assert view.tabla.rowCount() == 2

    view.campo_busqueda.setText("2026-100")

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 0).text() == "2026-100"


def test_busqueda_filtra_por_demandante_o_demandado(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add_all(
        [
            Expediente(
                radicado="2026-101",
                demandante="Fernanda Gomez",
                demandado="Luis",
                area_derecho=AreaDerecho.CIVIL_FAMILIA,
                fecha_corte_default=date(2026, 1, 1),
            ),
            Expediente(
                radicado="2026-102",
                demandante="Carlos",
                demandado="Rodrigo Gomez",
                area_derecho=AreaDerecho.CIVIL_FAMILIA,
                fecha_corte_default=date(2026, 1, 1),
            ),
            Expediente(
                radicado="2026-103",
                demandante="Sofia",
                demandado="Pedro",
                area_derecho=AreaDerecho.CIVIL_FAMILIA,
                fecha_corte_default=date(2026, 1, 1),
            ),
        ]
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view.campo_busqueda.setText("Gomez")

    assert view.tabla.rowCount() == 2


def test_busqueda_es_insensible_a_mayusculas_y_a_espacios_al_inicio_o_final(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-104",
            demandante="Valentina",
            demandado="Camilo",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view.campo_busqueda.setText("  VALENTINA  ")

    assert view.tabla.rowCount() == 1


def test_filtro_area_muestra_solo_expedientes_del_area_seleccionada(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add_all(
        [
            Expediente(
                radicado="2026-300",
                demandante="A",
                demandado="B",
                area_derecho=AreaDerecho.CIVIL_FAMILIA,
                fecha_corte_default=date(2026, 1, 1),
            ),
            Expediente(
                radicado="2026-301",
                demandante="C",
                demandado="D",
                area_derecho=AreaDerecho.LABORAL,
                fecha_corte_default=date(2026, 1, 1),
            ),
        ]
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()
    assert view.tabla.rowCount() == 2

    indice_laboral = view.combo_filtro_area.findData("LABORAL")
    view.combo_filtro_area.setCurrentIndex(indice_laboral)

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 0).text() == "2026-301"


def test_combo_filtro_area_incluye_la_opcion_todas_las_areas_por_defecto(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    view = ExpedientesListView()
    qtbot.addWidget(view)

    assert view.combo_filtro_area.currentData() == ""
    assert view.combo_filtro_area.count() == len(AREAS_DERECHO) + 1


def test_busqueda_y_filtro_de_area_se_combinan(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add_all(
        [
            Expediente(
                radicado="2026-400",
                demandante="Pablo Ruiz",
                demandado="X",
                area_derecho=AreaDerecho.CIVIL_FAMILIA,
                fecha_corte_default=date(2026, 1, 1),
            ),
            Expediente(
                radicado="2026-401",
                demandante="Pablo Ruiz",
                demandado="Y",
                area_derecho=AreaDerecho.LABORAL,
                fecha_corte_default=date(2026, 1, 1),
            ),
        ]
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view.campo_busqueda.setText("Pablo Ruiz")
    indice_laboral = view.combo_filtro_area.findData("LABORAL")
    view.combo_filtro_area.setCurrentIndex(indice_laboral)

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 0).text() == "2026-401"
```

(`_sesion_en_memoria`, `session_module`, `Expediente`, `AreaDerecho`, `date`, `AREAS_DERECHO` ya
están importados al inicio de `tests/views/test_expedientes.py`).

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_expedientes.py -k "busqueda or filtro_area or combo_filtro" -v`
Expected: FAIL (`AttributeError: 'ExpedientesListView' object has no attribute 'campo_busqueda'` /
`'combo_filtro_area'` — todavía no existen).

- [ ] **Step 3: Editar imports de `app/views/expedientes.py`**

Cambiar:

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

a:

```python
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
```

(`QLabel` y el resto de `QHBoxLayout` se usan recién en la Task 3; se agregan aquí junto con `Qt`
y `QHBoxLayout` para no volver a tocar el bloque de imports en cada task — `Qt` se necesita ya en
esta Task 1 no, se necesita en la Task 2; se agrega ahora para evitar un tercer diff sobre el mismo
bloque de imports en la Task 2. Si se prefiere estrictamente incremental, `Qt` y `QLabel` pueden
diferirse a sus tasks respectivas — no cambia el resultado final).

- [ ] **Step 4: Reemplazar `ExpedientesListView.__init__` completo**

Cambiar:

```python
class ExpedientesListView(QWidget):
    def __init__(self, on_expediente_abierto=None):
        super().__init__()
        self._on_expediente_abierto = on_expediente_abierto

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["Radicado", "Demandante", "Demandado", "Area", "Editar", "Eliminar"]
        )
        self.tabla.cellDoubleClicked.connect(self._abrir_seleccionado)

        self.boton_nuevo = QPushButton("Nuevo expediente")
        self.boton_nuevo.setProperty("class", "primary")
        self.boton_nuevo.clicked.connect(self._abrir_dialogo_nuevo)

        layout = QVBoxLayout()
        layout.addWidget(self.boton_nuevo)
        layout.addWidget(self.tabla)
        self.setLayout(layout)

        self._expediente_ids_por_fila = []
        self.refrescar()
```

a:

```python
class ExpedientesListView(QWidget):
    def __init__(self, on_expediente_abierto=None):
        super().__init__()
        self._on_expediente_abierto = on_expediente_abierto

        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText(
            "Buscar por radicado, demandante o demandado..."
        )
        self.campo_busqueda.textChanged.connect(self.refrescar)

        self.combo_filtro_area = QComboBox()
        self.combo_filtro_area.addItem("Todas las areas", userData="")
        for codigo, etiqueta, _habilitada in AREAS_DERECHO:
            self.combo_filtro_area.addItem(etiqueta, userData=codigo)
        self.combo_filtro_area.currentIndexChanged.connect(self.refrescar)

        layout_filtros = QHBoxLayout()
        layout_filtros.addWidget(self.campo_busqueda)
        layout_filtros.addWidget(self.combo_filtro_area)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["Radicado", "Demandante", "Demandado", "Area", "Editar", "Eliminar"]
        )
        self.tabla.cellDoubleClicked.connect(self._abrir_seleccionado)

        self.boton_nuevo = QPushButton("Nuevo expediente")
        self.boton_nuevo.setProperty("class", "primary")
        self.boton_nuevo.clicked.connect(self._abrir_dialogo_nuevo)

        layout = QVBoxLayout()
        layout.addWidget(self.boton_nuevo)
        layout.addLayout(layout_filtros)
        layout.addWidget(self.tabla)
        self.setLayout(layout)

        self._expediente_ids_por_fila = []
        self.refrescar()
```

(`self.campo_busqueda.textChanged.connect(self.refrescar)` y
`self.combo_filtro_area.currentIndexChanged.connect(self.refrescar)` conectan una señal con
argumento a un slot sin parámetros extra — patrón ya usado en este mismo código base, ej.
`self.combo_tipo.currentIndexChanged.connect(self._actualizar_campos_visibles)` en
`app/views/obligaciones.py`; PySide6 solo pasa los argumentos que el callable declara aceptar).

- [ ] **Step 5: Reemplazar `ExpedientesListView.refrescar` completo**

Cambiar:

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
            boton_eliminar.setIcon(icon("delete"))
            boton_eliminar.setProperty("class", "destructive")
            boton_eliminar.clicked.connect(
                lambda _checked=False, id_=expediente.id: self._eliminar_expediente(id_)
            )
            self.tabla.setCellWidget(fila, 5, boton_eliminar)

            self._expediente_ids_por_fila.append(expediente.id)
        session.close()
```

a:

```python
    def refrescar(self) -> None:
        session = session_module.get_session()
        expedientes = session.query(Expediente).all()

        expedientes_filtrados = self._filtrar(expedientes)

        self.tabla.setRowCount(len(expedientes_filtrados))
        self._expediente_ids_por_fila = []
        for fila, expediente in enumerate(expedientes_filtrados):
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
            boton_eliminar.setIcon(icon("delete"))
            boton_eliminar.setProperty("class", "destructive")
            boton_eliminar.clicked.connect(
                lambda _checked=False, id_=expediente.id: self._eliminar_expediente(id_)
            )
            self.tabla.setCellWidget(fila, 5, boton_eliminar)

            self._expediente_ids_por_fila.append(expediente.id)
        session.close()

    def _filtrar(self, expedientes: list[Expediente]) -> list[Expediente]:
        texto_busqueda = self.campo_busqueda.text().strip().lower()
        area_seleccionada = self.combo_filtro_area.currentData()

        def _coincide(expediente: Expediente) -> bool:
            if area_seleccionada and expediente.area_derecho.value != area_seleccionada:
                return False
            if texto_busqueda:
                campos = (expediente.radicado, expediente.demandante, expediente.demandado)
                if not any(texto_busqueda in (campo or "").lower() for campo in campos):
                    return False
            return True

        return [expediente for expediente in expedientes if _coincide(expediente)]
```

(`_filtrar` se extrae como método aparte, no inline, porque la Task 3 lo reutiliza para decidir el
mensaje del estado vacío sin duplicar la lógica de "hay filtros activos").

- [ ] **Step 6: Correr los tests para verificar que pasan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_expedientes.py -v`
Expected: todos PASS (los 12 preexistentes + los 6 nuevos de este Step 1 = 18).

- [ ] **Step 7: Ruff**

Run: `"<python>" -m ruff check app/views/expedientes.py tests/views/test_expedientes.py`
Expected: no errors nuevos introducidos por este task (si el archivo ya tenía deuda de lint
preexistente no relacionada con estas líneas, no es responsabilidad de este task — confirmar con
`ruff check` sobre el estado de partida de la Task antes de aplicar los cambios si hay dudas).

- [ ] **Step 8: Commit**

```bash
git add app/views/expedientes.py tests/views/test_expedientes.py
git commit -m "$(cat <<'EOF'
feat(sprint35): agregar busqueda por texto y filtro por area en ExpedientesListView

EOF
)"
```

---

### Task 2: Ordenamiento de columnas + mapeo fila→id robusto ante reordenamiento

**Files:**
- Modify: `app/views/expedientes.py` (`ExpedientesListView.refrescar`,
  `ExpedientesListView._abrir_seleccionado`)
- Modify: `tests/views/test_expedientes.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al inicio de `tests/views/test_expedientes.py`, en el bloque de imports, `Qt`:

Cambiar:

```python
from PySide6.QtWidgets import QMessageBox
```

a:

```python
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
```

Agregar al final del archivo:

```python
def test_tabla_de_expedientes_tiene_ordenamiento_de_columnas_habilitado(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    view = ExpedientesListView()
    qtbot.addWidget(view)

    assert view.tabla.isSortingEnabled() is True


def test_doble_clic_despues_de_ordenar_por_columna_abre_el_expediente_correcto(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente_zulema = Expediente(
        radicado="2026-900",
        demandante="Zulema",
        demandado="Ana",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    expediente_andres = Expediente(
        radicado="2026-901",
        demandante="Andres",
        demandado="Beto",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add_all([expediente_zulema, expediente_andres])
    session.commit()
    id_andres = expediente_andres.id
    session.close()

    abiertos = []
    view = ExpedientesListView(on_expediente_abierto=abiertos.append)
    qtbot.addWidget(view)
    view.refrescar()

    # Orden de insercion original: fila 0 = "Zulema" (2026-900), fila 1 = "Andres" (2026-901).
    assert view.tabla.item(0, 1).text() == "Zulema"

    # Se ordena por la columna "Demandante" (columna 1) ascendente: invierte el orden.
    view.tabla.sortItems(1, Qt.SortOrder.AscendingOrder)
    assert view.tabla.item(0, 1).text() == "Andres"

    view._abrir_seleccionado(0, 0)

    assert abiertos == [id_andres]


def test_eliminar_expediente_sigue_borrando_el_correcto_despues_de_ordenar(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente_z = Expediente(
        radicado="2026-902",
        demandante="Zulema",
        demandado="Ana",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    expediente_a = Expediente(
        radicado="2026-903",
        demandante="Andres",
        demandado="Beto",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add_all([expediente_z, expediente_a])
    session.commit()
    id_andres = expediente_a.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "app.views.expedientes.QInputDialog.getText",
        lambda *args, **kwargs: ("2026-903", True),
    )

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()
    view.tabla.sortItems(1, Qt.SortOrder.AscendingOrder)

    boton_eliminar_fila_0 = view.tabla.cellWidget(0, 5)
    boton_eliminar_fila_0.click()

    session = session_module.get_session()
    assert session.get(Expediente, id_andres) is None
    session.close()
```

(el último test confirma que los botones Editar/Eliminar por fila, conectados con el
`expediente.id` capturado directamente en el `lambda` al momento de crear el widget — no por
índice de fila — siguen apuntando al expediente correcto incluso después de ordenar; no dependen
del fix de `_abrir_seleccionado`, pero es la aserción de regresión más barata para confirmarlo
explícitamente).

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_expedientes.py -k "ordenamiento or doble_clic_despues_de_ordenar or sigue_borrando_el_correcto" -v`
Expected: FAIL (`test_tabla_de_expedientes_tiene_ordenamiento_de_columnas_habilitado` falla porque
`isSortingEnabled()` es `False`; `test_doble_clic_despues_de_ordenar_por_columna_abre_el_expediente_correcto`
falla porque `abiertos == [id_zulema]` en vez de `[id_andres]` — el bug real que corrige este
task).

- [ ] **Step 3: Reemplazar `ExpedientesListView.refrescar` completo (agrega
  `setSortingEnabled` + guarda el id como `UserRole` en la columna 0)**

Cambiar:

```python
    def refrescar(self) -> None:
        session = session_module.get_session()
        expedientes = session.query(Expediente).all()

        expedientes_filtrados = self._filtrar(expedientes)

        self.tabla.setRowCount(len(expedientes_filtrados))
        self._expediente_ids_por_fila = []
        for fila, expediente in enumerate(expedientes_filtrados):
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
            boton_eliminar.setIcon(icon("delete"))
            boton_eliminar.setProperty("class", "destructive")
            boton_eliminar.clicked.connect(
                lambda _checked=False, id_=expediente.id: self._eliminar_expediente(id_)
            )
            self.tabla.setCellWidget(fila, 5, boton_eliminar)

            self._expediente_ids_por_fila.append(expediente.id)
        session.close()
```

a:

```python
    def refrescar(self) -> None:
        session = session_module.get_session()
        expedientes = session.query(Expediente).all()

        expedientes_filtrados = self._filtrar(expedientes)

        # Se desactiva el ordenamiento mientras se puebla la tabla: con
        # setSortingEnabled(True) ya activo, cada setItem() dispararia un
        # re-ordenamiento a mitad de poblado y mezclaria filas con datos
        # incompletos (gotcha conocido de QTableWidget).
        self.tabla.setSortingEnabled(False)
        self.tabla.setRowCount(len(expedientes_filtrados))
        self._expediente_ids_por_fila = []
        for fila, expediente in enumerate(expedientes_filtrados):
            item_radicado = QTableWidgetItem(expediente.radicado)
            # El id se guarda como UserRole en el item de la columna 0 (no en
            # una lista Python indexada por fila) porque el item -- con todos
            # sus roles de datos -- se mueve junto con la fila cuando el
            # usuario ordena por columna; una lista indexada por posicion no.
            item_radicado.setData(Qt.ItemDataRole.UserRole, expediente.id)
            self.tabla.setItem(fila, 0, item_radicado)
            self.tabla.setItem(fila, 1, QTableWidgetItem(expediente.demandante))
            self.tabla.setItem(fila, 2, QTableWidgetItem(expediente.demandado))
            self.tabla.setItem(fila, 3, QTableWidgetItem(expediente.area_derecho.value))

            boton_editar = QPushButton("Editar")
            boton_editar.clicked.connect(
                lambda _checked=False, id_=expediente.id: self._editar_expediente(id_)
            )
            self.tabla.setCellWidget(fila, 4, boton_editar)

            boton_eliminar = QPushButton("Eliminar")
            boton_eliminar.setIcon(icon("delete"))
            boton_eliminar.setProperty("class", "destructive")
            boton_eliminar.clicked.connect(
                lambda _checked=False, id_=expediente.id: self._eliminar_expediente(id_)
            )
            self.tabla.setCellWidget(fila, 5, boton_eliminar)

            self._expediente_ids_por_fila.append(expediente.id)
        self.tabla.setSortingEnabled(True)
        session.close()
```

- [ ] **Step 4: Corregir `_abrir_seleccionado` para leer el id desde el item, no desde la lista
  por posición**

Cambiar:

```python
    def _abrir_seleccionado(self, fila: int, _columna: int) -> None:
        if self._on_expediente_abierto:
            self._on_expediente_abierto(self._expediente_ids_por_fila[fila])
```

a:

```python
    def _abrir_seleccionado(self, fila: int, _columna: int) -> None:
        if self._on_expediente_abierto:
            expediente_id = self.tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole)
            self._on_expediente_abierto(expediente_id)
```

- [ ] **Step 5: Correr los tests para verificar que pasan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_expedientes.py -v`
Expected: todos PASS (los 18 de la Task 1 + los 3 nuevos de este task = 21).

- [ ] **Step 6: Ruff**

Run: `"<python>" -m ruff check app/views/expedientes.py tests/views/test_expedientes.py`
Expected: no errors nuevos.

- [ ] **Step 7: Commit**

```bash
git add app/views/expedientes.py tests/views/test_expedientes.py
git commit -m "$(cat <<'EOF'
feat(sprint35): habilitar ordenamiento de columnas en la tabla de expedientes

EOF
)"
```

---

### Task 3: Estado vacío explícito (mensaje + botón de acción contextual)

**Files:**
- Modify: `app/views/expedientes.py` (imports, `ExpedientesListView.__init__`,
  `ExpedientesListView.refrescar`, métodos nuevos)
- Modify: `tests/views/test_expedientes.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/views/test_expedientes.py`:

```python
def test_base_de_datos_vacia_muestra_estado_vacio_con_boton_crear_expediente(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.show()

    assert view.tabla.isVisible() is False
    assert view.widget_estado_vacio.isVisible() is True
    assert "no hay expedientes" in view.etiqueta_estado_vacio.text().lower()
    assert view.boton_accion_estado_vacio.isVisible() is True
    assert view.boton_accion_estado_vacio.text() == "Crear expediente"


def test_estado_vacio_se_oculta_y_la_tabla_se_muestra_cuando_hay_resultados(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-960",
            demandante="Ines",
            demandado="Tomas",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.show()
    view.refrescar()

    assert view.tabla.isVisible() is True
    assert view.widget_estado_vacio.isVisible() is False


def test_filtro_sin_resultados_muestra_estado_vacio_con_boton_limpiar_filtros(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-950",
            demandante="Fernanda",
            demandado="Ricardo",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.show()
    view.refrescar()
    assert view.tabla.isVisible() is True

    view.campo_busqueda.setText("no-existe-este-radicado")

    assert view.tabla.isVisible() is False
    assert view.widget_estado_vacio.isVisible() is True
    assert "coincide" in view.etiqueta_estado_vacio.text().lower()
    assert view.boton_accion_estado_vacio.text() == "Limpiar filtros"


def test_boton_limpiar_filtros_del_estado_vacio_restaura_la_lista_completa(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-951",
            demandante="Gustavo",
            demandado="Helena",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.show()
    view.campo_busqueda.setText("no-existe-este-radicado")
    assert view.tabla.rowCount() == 0

    view.boton_accion_estado_vacio.click()

    assert view.campo_busqueda.text() == ""
    assert view.combo_filtro_area.currentData() == ""
    assert view.tabla.rowCount() == 1
    assert view.tabla.isVisible() is True


def test_boton_crear_expediente_del_estado_vacio_abre_el_dialogo_de_nuevo_expediente(
    qtbot, monkeypatch
):
    _sesion_en_memoria(monkeypatch)

    dialogos_creados = []

    class _DialogStub:
        def __init__(self, parent):
            dialogos_creados.append(1)

        def exec(self):
            return False

    monkeypatch.setattr("app.views.expedientes.ExpedienteFormDialog", _DialogStub)

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.show()

    view.boton_accion_estado_vacio.click()

    assert dialogos_creados == [1]
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_expedientes.py -k "estado_vacio" -v`
Expected: FAIL (`AttributeError: 'ExpedientesListView' object has no attribute
'widget_estado_vacio'` — todavía no existe).

- [ ] **Step 3: Reemplazar `ExpedientesListView.__init__` completo (agrega el widget de estado
  vacío)**

Cambiar:

```python
class ExpedientesListView(QWidget):
    def __init__(self, on_expediente_abierto=None):
        super().__init__()
        self._on_expediente_abierto = on_expediente_abierto

        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText(
            "Buscar por radicado, demandante o demandado..."
        )
        self.campo_busqueda.textChanged.connect(self.refrescar)

        self.combo_filtro_area = QComboBox()
        self.combo_filtro_area.addItem("Todas las areas", userData="")
        for codigo, etiqueta, _habilitada in AREAS_DERECHO:
            self.combo_filtro_area.addItem(etiqueta, userData=codigo)
        self.combo_filtro_area.currentIndexChanged.connect(self.refrescar)

        layout_filtros = QHBoxLayout()
        layout_filtros.addWidget(self.campo_busqueda)
        layout_filtros.addWidget(self.combo_filtro_area)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["Radicado", "Demandante", "Demandado", "Area", "Editar", "Eliminar"]
        )
        self.tabla.cellDoubleClicked.connect(self._abrir_seleccionado)

        self.boton_nuevo = QPushButton("Nuevo expediente")
        self.boton_nuevo.setProperty("class", "primary")
        self.boton_nuevo.clicked.connect(self._abrir_dialogo_nuevo)

        layout = QVBoxLayout()
        layout.addWidget(self.boton_nuevo)
        layout.addLayout(layout_filtros)
        layout.addWidget(self.tabla)
        self.setLayout(layout)

        self._expediente_ids_por_fila = []
        self.refrescar()
```

a:

```python
class ExpedientesListView(QWidget):
    def __init__(self, on_expediente_abierto=None):
        super().__init__()
        self._on_expediente_abierto = on_expediente_abierto
        self._estado_vacio_es_por_filtros = False

        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText(
            "Buscar por radicado, demandante o demandado..."
        )
        self.campo_busqueda.textChanged.connect(self.refrescar)

        self.combo_filtro_area = QComboBox()
        self.combo_filtro_area.addItem("Todas las areas", userData="")
        for codigo, etiqueta, _habilitada in AREAS_DERECHO:
            self.combo_filtro_area.addItem(etiqueta, userData=codigo)
        self.combo_filtro_area.currentIndexChanged.connect(self.refrescar)

        layout_filtros = QHBoxLayout()
        layout_filtros.addWidget(self.campo_busqueda)
        layout_filtros.addWidget(self.combo_filtro_area)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["Radicado", "Demandante", "Demandado", "Area", "Editar", "Eliminar"]
        )
        self.tabla.cellDoubleClicked.connect(self._abrir_seleccionado)

        self.boton_nuevo = QPushButton("Nuevo expediente")
        self.boton_nuevo.setProperty("class", "primary")
        self.boton_nuevo.clicked.connect(self._abrir_dialogo_nuevo)

        self.etiqueta_estado_vacio = QLabel()
        self.etiqueta_estado_vacio.setWordWrap(True)
        self.etiqueta_estado_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.etiqueta_estado_vacio.setStyleSheet(
            f"color: {colores.TEXTO_SECUNDARIO}; padding: 24px; font-size: 11pt;"
        )

        self.boton_accion_estado_vacio = QPushButton()
        self.boton_accion_estado_vacio.setProperty("class", "primary")
        self.boton_accion_estado_vacio.clicked.connect(self._accion_estado_vacio)

        layout_estado_vacio = QVBoxLayout()
        layout_estado_vacio.addWidget(self.etiqueta_estado_vacio)
        layout_estado_vacio.addWidget(
            self.boton_accion_estado_vacio, alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.widget_estado_vacio = QWidget()
        self.widget_estado_vacio.setLayout(layout_estado_vacio)
        self.widget_estado_vacio.setVisible(False)

        layout = QVBoxLayout()
        layout.addWidget(self.boton_nuevo)
        layout.addLayout(layout_filtros)
        layout.addWidget(self.tabla)
        layout.addWidget(self.widget_estado_vacio)
        self.setLayout(layout)

        self._expediente_ids_por_fila = []
        self.refrescar()
```

- [ ] **Step 4: Agregar el import de `theme_colors` (paleta del Sprint 31)**

Cambiar:

```python
import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.views.icons import icon
from database.models import AreaDerecho, Expediente
```

a:

```python
import database.session as session_module
from app.core import theme_colors as colores
from app.core.constants import AREAS_DERECHO
from app.views.icons import icon
from database.models import AreaDerecho, Expediente
```

- [ ] **Step 5: Agregar la llamada a `_actualizar_estado_vacio` al final de `refrescar`, y los 3
  métodos nuevos**

Cambiar el final de `refrescar` (después del `for` que puebla la tabla):

```python
            self._expediente_ids_por_fila.append(expediente.id)
        self.tabla.setSortingEnabled(True)
        session.close()

    def _filtrar(self, expedientes: list[Expediente]) -> list[Expediente]:
```

a:

```python
            self._expediente_ids_por_fila.append(expediente.id)
        self.tabla.setSortingEnabled(True)
        total_en_base_de_datos = len(expedientes)
        session.close()

        self._actualizar_estado_vacio(
            total_en_base_de_datos=total_en_base_de_datos,
            hay_resultados=bool(expedientes_filtrados),
        )

    def _actualizar_estado_vacio(
        self, *, total_en_base_de_datos: int, hay_resultados: bool
    ) -> None:
        if hay_resultados:
            self.tabla.setVisible(True)
            self.widget_estado_vacio.setVisible(False)
            return

        self.tabla.setVisible(False)
        self.widget_estado_vacio.setVisible(True)

        if total_en_base_de_datos == 0:
            self._estado_vacio_es_por_filtros = False
            self.etiqueta_estado_vacio.setText(
                "Todavia no hay expedientes cargados.\n"
                "Crea el primero para empezar a liquidar."
            )
            self.boton_accion_estado_vacio.setText("Crear expediente")
        else:
            self._estado_vacio_es_por_filtros = True
            self.etiqueta_estado_vacio.setText(
                "Ningun expediente coincide con la busqueda o el filtro actual."
            )
            self.boton_accion_estado_vacio.setText("Limpiar filtros")

    def _accion_estado_vacio(self) -> None:
        if self._estado_vacio_es_por_filtros:
            self._limpiar_filtros()
        else:
            self._abrir_dialogo_nuevo()

    def _limpiar_filtros(self) -> None:
        self.campo_busqueda.blockSignals(True)
        self.combo_filtro_area.blockSignals(True)
        self.campo_busqueda.clear()
        self.combo_filtro_area.setCurrentIndex(0)
        self.campo_busqueda.blockSignals(False)
        self.combo_filtro_area.blockSignals(False)
        self.refrescar()

    def _filtrar(self, expedientes: list[Expediente]) -> list[Expediente]:
```

(`blockSignals` evita que `_limpiar_filtros` dispare `refrescar()` dos veces por señal —
`campo_busqueda.clear()` emite `textChanged` y `combo_filtro_area.setCurrentIndex(0)` emite
`currentIndexChanged` — antes de la llamada explícita y única a `self.refrescar()` al final del
método).

- [ ] **Step 6: Correr los tests para verificar que pasan**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest tests/views/test_expedientes.py -v`
Expected: todos PASS (los 21 de las Tasks 1-2 + los 5 nuevos de este task = 26).

- [ ] **Step 7: Ruff**

Run: `"<python>" -m ruff check app/views/expedientes.py tests/views/test_expedientes.py`
Expected: no errors nuevos.

- [ ] **Step 8: Commit**

```bash
git add app/views/expedientes.py tests/views/test_expedientes.py
git commit -m "$(cat <<'EOF'
feat(sprint35): mostrar estado vacio con accion contextual cuando la tabla no tiene filas

EOF
)"
```

---

### Task 4: Suite completa, ruff y cierre técnico del sprint (sin tocar `Pendientes.md`)

**Files:** ninguno nuevo — solo verificación.

- [ ] **Step 1: Correr toda la suite del proyecto**

Run: `QT_QPA_PLATFORM=offscreen "<python>" -m pytest -v`
Expected: todos los tests en verde (los ~14 nuevos de este plan — 6 de Task 1, 3 de Task 2, 5 de
Task 3 — más todos los existentes, sin cambios de comportamiento en los casos ya cubiertos por
Sprint 31 sobre este mismo archivo).

- [ ] **Step 2: Ruff sobre todo el repo**

Run: `"<python>" -m ruff check .`
Expected: siguiendo el mismo criterio que sprints anteriores sobre este repositorio (ver Sprint
26/31/34 Task de cierre): si el repo ya tenía errores de lint preexistentes antes de este plan, no
es objetivo de este sprint resolverlos. El criterio de aceptación real es que **ninguna línea
nueva o modificada por este plan** (los Steps de `app/views/expedientes.py` y
`tests/views/test_expedientes.py` en las Tasks 1-3) aparezca en la salida de `ruff check`. Si hace
falta confirmarlo con precisión: guardar la salida de `ruff check .` en el scratchpad de la
sesión, correr `git stash`, correr `ruff check .` de nuevo sobre el estado previo a este plan,
`git stash pop`, y diffear ambas salidas — no debe haber ninguna línea nueva que mencione
`app/views/expedientes.py` o `tests/views/test_expedientes.py` con un error que no existiera
antes.

- [ ] **Step 3: Verificación manual de coherencia visual (no automatizable)**

Este sprint depende informalmente de que el Sprint 31 (sistema de diseño visual) ya esté
fusionado, para que el estado vacío se vea coherente con el resto de la aplicación (color
`TEXTO_SECUNDARIO` del mensaje, botón `class="primary"` con el burdeos de marca). `pytest-qt` no
puede aserciones sobre "se ve bien" — queda como pendiente explícito de revisión visual manual
antes de fusionar: abrir la app con una base de datos vacía y confirmar que el estado vacío se ve
integrado (no un bloque de texto plano descolgado), y que buscar/filtrar/ordenar en la lista de
expedientes real se siente instantáneo con el volumen de datos de prueba disponible.

- [ ] **Step 4 — NO EJECUTAR: recordatorio explícito**

**No editar `Pendientes.md`** (ni el índice, ni la sección del Sprint 35, ni ningún marcador
`✅ Completado`) — el orquestador humano actualiza ese archivo centralmente una vez fusionados los
sprints paralelos de este stream (31, 32, 33, 34, 35, 36). Este plan termina en el Step 2 de este
Task.

**No editar `README.md` ni `docs/GUIA_USUARIO.md`**: si al ejecutar este plan se encuentra algo
concreto que quedó desactualizado por este cambio específico (ej. una captura o descripción del
listado de expedientes que ya no refleja la UI), corregirlo con un commit `docs:` separado y
angosto, documentando en el mensaje por qué.

---

## Self-review notes

- **Cobertura del spec:** campo de búsqueda por radicado/demandante/demandado (Task 1); filtro por
  área (Task 1, combinable con la búsqueda — test dedicado); ordenamiento de columnas habilitado
  con `setSortingEnabled(True)` (Task 2), incluyendo el fix necesario para que el doble clic siga
  abriendo el expediente correcto después de ordenar (Task 2, con test de regresión explícito);
  estado vacío diseñado con mensaje + CTA quenot es solo "base de datos vacía" sino también
  "filtro sin resultados" con una acción distinta en cada caso (Task 3); ninguna paginación
  agregada (excluida explícitamente del spec, no se toca `refrescar()` para limitar filas). El
  campo "estado" del hallazgo original ("filtro por área/estado") se documenta explícitamente como
  inexistente en el modelo de datos real (`database/models.py`) — no se inventa.
- **Sin placeholders:** cada step trae el código completo del método reemplazado (siguiendo el
  mismo patrón de reemplazo íntegro de métodos que usó el Sprint 26, más robusto que diffs de
  líneas sueltas cuando el mismo método se edita en tasks consecutivas).
- **Consistencia con Sprint 31:** se reutiliza `app.views.icons.icon("delete")` verbatim (ya
  presente en el baseline), `app.core.theme_colors.TEXTO_SECUNDARIO` para el mensaje del estado
  vacío, y `boton.setProperty("class", "primary")` para el botón de acción del estado vacío —
  ningún nombre nuevo inventado fuera de lo que Sprint 31 ya expone.
- **Sin colisión con Sprint 34:** todos los cambios de este plan quedan dentro de
  `ExpedientesListView` (imports compartidos aparte); `ExpedienteFormDialog` no se toca en ningún
  Step, tal como exige la nota de integración del plan de Sprint 34.
- **Icono de búsqueda:** decisión explícita de no agregarlo (justificada en la sección
  **Architecture**) — se usa `QLineEdit` con `placeholderText`, sin ícono ni SVG nuevo.
