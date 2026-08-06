# Sprint 33 — Pantalla de inicio real: dashboard con resumen y alertas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `app/views/dashboard.py` (hoy un archivo vacío de 0 bytes que nadie importa) pasa a
contener `DashboardView`: una pantalla de inicio real que muestra, sin que el usuario tenga que
abrir ningún expediente puntual, (1) el conteo de expedientes por área del derecho, (2) una lista
de obligaciones con plazos de prescripción próximos a vencer (o ya vencidos) en cualquier
expediente, y (3) las últimas liquidaciones ejecutadas en cualquier expediente. `MainWindow` pasa a
abrir en `DashboardView` en vez de abrir directo en `ExpedientesListView` — el listado plano de
expedientes sigue existiendo tal cual, ahora accesible con un clic desde el dashboard (botón
"Ver todos los expedientes") o con el botón "🏠 Inicio" para volver al dashboard.

**Architecture:** `DashboardView` (QWidget) hace 3 consultas sobre la sesión de SQLAlchemy actual
al refrescarse: expedientes por área (`session.query(Expediente).all()` + conteo en Python, mismo
patrón que `ExpedientesListView.refrescar()`), alertas de vencimiento (recorre las obligaciones no
pagadas de todos los expedientes y calcula la fecha límite de prescripción de la acción ejecutiva
con `calcular_prescripcion(obligacion.fecha_origen, TipoAccion.EJECUTIVA)`, reutilizando el motor
del Sprint 7), y actividad reciente (reutiliza `historial_de_expediente` del Sprint 9, una vez por
expediente, y fusiona/recorta el resultado a los N más recientes).

*Por qué `TipoAccion.EJECUTIVA` para todas las áreas y no un mapeo área→tipo de acción:* el modelo
`Obligacion` no tiene ningún campo que indique el tipo de acción procesal (ejecutiva, ordinaria,
cambiaria, etc.) — esa clasificación no existe hoy en el esquema, y no hay ningún mapeo
`AreaDerecho` → `TipoAccion` establecido en el código existente para inventar uno con autoridad.
`TipoAccion.EJECUTIVA` ya es el default explícito que usa `filtrar_cuotas_prescritas` en
`app/engine/temporal/prescripcion.py` cuando no se especifica un tipo de acción — este sprint seguía
ese mismo precedente como heurística razonable y explícitamente documentada en el código (no
silenciosa), no como una regla legal nueva. Si el despacho confirma después un mapeo área→tipo de
acción más preciso, es un hallazgo para un sprint futuro, no de este.

*Por qué carga síncrona y no `TareaEnHilo` (Sprint 26):* las 3 consultas de arriba son *SELECT*
livianos (sin joins pesados) más aritmética de fechas sobre, como mucho, unas pocas centenas de
expedientes/obligaciones para un despacho de este tamaño — nada comparable en costo a
`estrategia.liquidar()` (el motor de liquidación día-a-día, potencialmente miles de eventos) o a
generar un PDF/Word completo, que sí ameritaron sacar del hilo de UI en el Sprint 26. Añadir
`QProgressDialog` + deshabilitar botones + manejo de excepciones vía señales para una operación que
hoy toma milisegundos sería complejidad sin beneficio medible. Si el volumen de expedientes crece
varios órdenes de magnitud y `refrescar()` se vuelve perceptiblemente lento, la migración a
`TareaEnHilo` (`app/views/concurrency.py`, ya construida y reutilizable) queda documentada aquí como
el camino a seguir — pero no se implementa en este sprint sin evidencia de que hace falta.

**Tech Stack:** Python, PySide6 (Qt: `QWidget`, `QGroupBox`, `QTableWidget`, `QPushButton`,
`QLabel`), SQLAlchemy, pytest + pytest-qt (`qtbot`).

---

### Nota de integración (leer antes de ejecutar la Task 4)

Este plan fue escrito leyendo el `app/views/main_window.py` **actual** del repositorio al momento
de redactar este documento. En el orden real de ejecución de sprints, el Sprint 32 (breadcrumbs,
atajos de teclado, botones de navegación con ícono) se implementa y se commitea en esta misma rama
**antes** de que la Task 4 de este plan se ejecute — así que para cuando llegues a la Task 4,
`app/views/main_window.py` casi seguro ya no tiene exactamente el contenido mostrado abajo. Los
números de línea y los bloques "old_string" de la Task 4 son **ilustrativos, no literales**: antes
de tocar ese archivo, vuelve a leerlo completo con la herramienta de lectura, localiza los mismos
puntos de inserción por *intención* (dónde se crean las páginas y se agregan al `QStackedWidget`,
dónde vive el diccionario `_pages`, dónde se decide la página inicial, dónde vive `_ir_inicio` y
`_actualizar_botones_navegacion`) y aplica el mismo cambio conceptual — agregar `DashboardView`
como una página más, hacerla la página inicial, y hacer que "🏠 Inicio" navegue a ella — adaptado a
la estructura real que encuentres. El resto de las Tasks (1, 2, 3, 5) no dependen de
`main_window.py` y no tienen este problema: `app/views/dashboard.py` es un archivo nuevo (hoy vacío)
que ningún sprint intermedio toca.

---

### Task 1: `DashboardView` — esqueleto, conteo de expedientes por área y botón "Ver todos los expedientes"

**Files:**
- Create: `app/views/dashboard.py`
- Create: `tests/views/test_dashboard.py`

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/views/test_dashboard.py`:

```python
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.views.dashboard import DashboardView
from database.models import AreaDerecho, Base, Expediente


def _sesion_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )


def _crear_expediente(session, radicado: str, area: AreaDerecho) -> Expediente:
    expediente = Expediente(
        radicado=radicado,
        demandante="Ana",
        demandado="Luis",
        area_derecho=area,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    return expediente


def test_dashboard_sin_expedientes_muestra_conteo_en_cero(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    view = DashboardView()
    qtbot.addWidget(view)

    assert view.etiqueta_total_expedientes.text() == "Total de expedientes: 0"
    assert view.tabla_por_area.rowCount() == len(AREAS_DERECHO)
    for fila in range(view.tabla_por_area.rowCount()):
        assert view.tabla_por_area.item(fila, 1).text() == "0"


def test_dashboard_muestra_el_total_y_el_conteo_por_area(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _crear_expediente(session, "2026-001", AreaDerecho.CIVIL_FAMILIA)
    _crear_expediente(session, "2026-002", AreaDerecho.CIVIL_FAMILIA)
    _crear_expediente(session, "2026-003", AreaDerecho.COMERCIAL)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)

    assert view.etiqueta_total_expedientes.text() == "Total de expedientes: 3"

    fila_civil = next(
        fila
        for fila, (codigo, _et, _hab) in enumerate(AREAS_DERECHO)
        if codigo == "CIVIL_FAMILIA"
    )
    fila_comercial = next(
        fila for fila, (codigo, _et, _hab) in enumerate(AREAS_DERECHO) if codigo == "COMERCIAL"
    )
    assert view.tabla_por_area.item(fila_civil, 1).text() == "2"
    assert view.tabla_por_area.item(fila_comercial, 1).text() == "1"


def test_dashboard_boton_ver_expedientes_invoca_callback(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    llamadas = []

    view = DashboardView(on_ver_expedientes=lambda: llamadas.append(1))
    qtbot.addWidget(view)

    view.boton_ver_expedientes.click()

    assert llamadas == [1]


def test_dashboard_boton_ver_expedientes_tiene_clase_primary(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    view = DashboardView()
    qtbot.addWidget(view)

    assert view.boton_ver_expedientes.property("class") == "primary"
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_dashboard.py -v`
Expected: FAIL (`ImportError: cannot import name 'DashboardView' from 'app.views.dashboard'` —
el módulo existe como archivo vacío pero no define nada).

- [ ] **Step 3: Crear `app/views/dashboard.py`**

```python
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from database.models import Expediente


class DashboardView(QWidget):
    """Pantalla de inicio (Sprint 33): resumen agregado de todos los expedientes,
    en vez de abrir directo al listado plano de expedientes
    (`app/views/expedientes.py`, que sigue existiendo como pantalla "expedientes",
    alcanzable desde aquí con el botón "Ver todos los expedientes").

    Carga sus datos de forma síncrona -- sin `TareaEnHilo`/`QThreadPool` (Sprint
    26) -- porque son consultas SQL livianas más aritmética de fechas sobre, como
    mucho, unas pocas centenas de expedientes/obligaciones: no es la clase de
    operación pesada (`liquidar()`, exportar PDF/Word) que el Sprint 26 sacó del
    hilo de UI. Ver la sección Architecture del plan de este sprint para el
    detalle completo de esta decisión.
    """

    def __init__(self, on_expediente_abierto=None, on_ver_expedientes=None):
        super().__init__()
        self._on_expediente_abierto = on_expediente_abierto
        self._on_ver_expedientes = on_ver_expedientes

        self.boton_ver_expedientes = QPushButton("Ver todos los expedientes")
        self.boton_ver_expedientes.setProperty("class", "primary")
        self.boton_ver_expedientes.clicked.connect(self._emitir_ver_expedientes)

        self.etiqueta_total_expedientes = QLabel()

        self.tabla_por_area = QTableWidget(len(AREAS_DERECHO), 2)
        self.tabla_por_area.setHorizontalHeaderLabels(["Área", "Expedientes"])

        grupo_resumen = QGroupBox("Expedientes por área")
        layout_resumen = QVBoxLayout()
        layout_resumen.addWidget(self.etiqueta_total_expedientes)
        layout_resumen.addWidget(self.tabla_por_area)
        grupo_resumen.setLayout(layout_resumen)

        layout_cta = QHBoxLayout()
        layout_cta.addStretch()
        layout_cta.addWidget(self.boton_ver_expedientes)

        layout_principal = QVBoxLayout()
        layout_principal.addLayout(layout_cta)
        layout_principal.addWidget(grupo_resumen)
        self.setLayout(layout_principal)

        self.refrescar()

    def _emitir_ver_expedientes(self) -> None:
        if self._on_ver_expedientes:
            self._on_ver_expedientes()

    def refrescar(self) -> None:
        session = session_module.get_session()
        expedientes = session.query(Expediente).all()

        self._refrescar_conteo_por_area(expedientes)

        session.close()

    def _refrescar_conteo_por_area(self, expedientes: list[Expediente]) -> None:
        self.etiqueta_total_expedientes.setText(f"Total de expedientes: {len(expedientes)}")

        conteo_por_area = dict.fromkeys((codigo for codigo, _et, _hab in AREAS_DERECHO), 0)
        for expediente in expedientes:
            conteo_por_area[expediente.area_derecho.value] += 1

        for fila, (codigo, etiqueta, _habilitada) in enumerate(AREAS_DERECHO):
            self.tabla_por_area.setItem(fila, 0, QTableWidgetItem(etiqueta))
            self.tabla_por_area.setItem(
                fila, 1, QTableWidgetItem(str(conteo_por_area[codigo]))
            )
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_dashboard.py -v`
Expected: 4 passed.

- [ ] **Step 5: Ruff**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check app/views/dashboard.py tests/views/test_dashboard.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add app/views/dashboard.py tests/views/test_dashboard.py
git commit -m "$(cat <<'EOF'
feat(sprint33): crear DashboardView con resumen de expedientes por area

EOF
)"
```

---

### Task 2: Alertas de plazos próximos a vencer

**Files:**
- Modify: `app/views/dashboard.py` (imports, constante `DIAS_ALERTA_VENCIMIENTO`, `__init__`,
  `refrescar`, método nuevo `_refrescar_alertas_vencimiento`, método nuevo
  `_abrir_expediente_de_alerta`)
- Modify: `tests/views/test_dashboard.py` (imports, helpers nuevos, tests nuevos)

- [ ] **Step 1: Escribir los tests que fallan**

Reemplazar el contenido completo de `tests/views/test_dashboard.py` por:

```python
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.engine.temporal.prescripcion import TipoAccion, calcular_prescripcion
from app.views.dashboard import DashboardView
from database.models import (
    AreaDerecho,
    Base,
    Expediente,
    Obligacion,
    ParametroLegal,
    TipoObligacion,
)


def _sesion_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )


def _crear_expediente(session, radicado: str, area: AreaDerecho) -> Expediente:
    expediente = Expediente(
        radicado=radicado,
        demandante="Ana",
        demandado="Luis",
        area_derecho=area,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    return expediente


def _sembrar_parametro_prescripcion_ejecutiva(session, meses: int = 60) -> None:
    session.add(
        ParametroLegal(
            clave="PRESCRIPCION_EJECUTIVA_MESES",
            valor=Decimal(meses),
            vigente_desde=date(1900, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    session.commit()


def _crear_obligacion(
    session, expediente_id: int, fecha_origen: date, pagada: bool = False
) -> Obligacion:
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Capital pagare",
        categoria="CAPITAL_PAGARE",
        fecha_origen=fecha_origen,
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        pagada=pagada,
    )
    session.add(obligacion)
    session.commit()
    return obligacion


def test_dashboard_sin_expedientes_muestra_conteo_en_cero(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    view = DashboardView()
    qtbot.addWidget(view)

    assert view.etiqueta_total_expedientes.text() == "Total de expedientes: 0"
    assert view.tabla_por_area.rowCount() == len(AREAS_DERECHO)
    for fila in range(view.tabla_por_area.rowCount()):
        assert view.tabla_por_area.item(fila, 1).text() == "0"


def test_dashboard_muestra_el_total_y_el_conteo_por_area(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _crear_expediente(session, "2026-001", AreaDerecho.CIVIL_FAMILIA)
    _crear_expediente(session, "2026-002", AreaDerecho.CIVIL_FAMILIA)
    _crear_expediente(session, "2026-003", AreaDerecho.COMERCIAL)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)

    assert view.etiqueta_total_expedientes.text() == "Total de expedientes: 3"

    fila_civil = next(
        fila
        for fila, (codigo, _et, _hab) in enumerate(AREAS_DERECHO)
        if codigo == "CIVIL_FAMILIA"
    )
    fila_comercial = next(
        fila for fila, (codigo, _et, _hab) in enumerate(AREAS_DERECHO) if codigo == "COMERCIAL"
    )
    assert view.tabla_por_area.item(fila_civil, 1).text() == "2"
    assert view.tabla_por_area.item(fila_comercial, 1).text() == "1"


def test_dashboard_boton_ver_expedientes_invoca_callback(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    llamadas = []

    view = DashboardView(on_ver_expedientes=lambda: llamadas.append(1))
    qtbot.addWidget(view)

    view.boton_ver_expedientes.click()

    assert llamadas == [1]


def test_dashboard_boton_ver_expedientes_tiene_clase_primary(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    view = DashboardView()
    qtbot.addWidget(view)

    assert view.boton_ver_expedientes.property("class") == "primary"


def test_dashboard_muestra_alerta_de_obligacion_proxima_a_prescribir(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro_prescripcion_ejecutiva(session)
    expediente = _crear_expediente(session, "2026-010", AreaDerecho.CIVIL_FAMILIA)
    _crear_obligacion(session, expediente.id, date(2021, 1, 4))

    fecha_limite = calcular_prescripcion(date(2021, 1, 4), TipoAccion.EJECUTIVA)
    hoy = fecha_limite - timedelta(days=30)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)
    view.refrescar(hoy=hoy)

    assert view.tabla_alertas.rowCount() == 1
    assert view.tabla_alertas.item(0, 0).text() == "2026-010"
    assert view.tabla_alertas.item(0, 1).text() == "Capital pagare"
    assert view.tabla_alertas.item(0, 2).text() == fecha_limite.isoformat()
    assert view.tabla_alertas.item(0, 3).text() == "Vence en 30 días"


def test_dashboard_marca_vencido_cuando_la_fecha_limite_ya_paso(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro_prescripcion_ejecutiva(session)
    expediente = _crear_expediente(session, "2026-011", AreaDerecho.CIVIL_FAMILIA)
    _crear_obligacion(session, expediente.id, date(2021, 1, 4))

    fecha_limite = calcular_prescripcion(date(2021, 1, 4), TipoAccion.EJECUTIVA)
    hoy = fecha_limite + timedelta(days=10)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)
    view.refrescar(hoy=hoy)

    assert view.tabla_alertas.rowCount() == 1
    assert view.tabla_alertas.item(0, 3).text() == "Vencido"


def test_dashboard_no_alerta_obligacion_pagada(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro_prescripcion_ejecutiva(session)
    expediente = _crear_expediente(session, "2026-012", AreaDerecho.CIVIL_FAMILIA)
    _crear_obligacion(session, expediente.id, date(2021, 1, 4), pagada=True)

    fecha_limite = calcular_prescripcion(date(2021, 1, 4), TipoAccion.EJECUTIVA)
    hoy = fecha_limite - timedelta(days=30)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)
    view.refrescar(hoy=hoy)

    assert view.tabla_alertas.rowCount() == 0


def test_dashboard_no_alerta_fuera_de_la_ventana_de_90_dias(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro_prescripcion_ejecutiva(session)
    expediente = _crear_expediente(session, "2026-013", AreaDerecho.CIVIL_FAMILIA)
    _crear_obligacion(session, expediente.id, date(2021, 1, 4))

    fecha_limite = calcular_prescripcion(date(2021, 1, 4), TipoAccion.EJECUTIVA)
    hoy = fecha_limite - timedelta(days=200)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)
    view.refrescar(hoy=hoy)

    assert view.tabla_alertas.rowCount() == 0


def test_dashboard_omite_obligacion_sin_parametro_configurado(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    # deliberadamente no se siembra PRESCRIPCION_EJECUTIVA_MESES
    expediente = _crear_expediente(session, "2026-014", AreaDerecho.CIVIL_FAMILIA)
    _crear_obligacion(session, expediente.id, date(2021, 1, 4))
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)
    view.refrescar(hoy=date(2026, 1, 1))  # no debe lanzar ParametroNoDisponibleError

    assert view.tabla_alertas.rowCount() == 0


def test_dashboard_doble_clic_en_alerta_abre_el_expediente(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro_prescripcion_ejecutiva(session)
    expediente = _crear_expediente(session, "2026-015", AreaDerecho.CIVIL_FAMILIA)
    _crear_obligacion(session, expediente.id, date(2021, 1, 4))
    expediente_id = expediente.id

    fecha_limite = calcular_prescripcion(date(2021, 1, 4), TipoAccion.EJECUTIVA)
    hoy = fecha_limite - timedelta(days=30)
    session.close()

    abiertos = []
    view = DashboardView(on_expediente_abierto=lambda id_: abiertos.append(id_))
    qtbot.addWidget(view)
    view.refrescar(hoy=hoy)

    view.tabla_alertas.cellDoubleClicked.emit(0, 0)

    assert abiertos == [expediente_id]
```

- [ ] **Step 2: Correr los tests nuevos para verificar que fallan**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_dashboard.py -k "alerta or vencido or vencimiento" -v`
Expected: FAIL (`AttributeError: 'DashboardView' object has no attribute 'tabla_alertas'` y
`TypeError: refrescar() got an unexpected keyword argument 'hoy'`).

- [ ] **Step 3: Reemplazar el contenido completo de `app/views/dashboard.py`**

```python
from datetime import date, timedelta

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.core.exceptions import ParametroNoDisponibleError
from app.engine.temporal.prescripcion import TipoAccion, calcular_prescripcion
from database.models import Expediente

DIAS_ALERTA_VENCIMIENTO = 90


class DashboardView(QWidget):
    """Pantalla de inicio (Sprint 33): resumen agregado de todos los expedientes,
    en vez de abrir directo al listado plano de expedientes
    (`app/views/expedientes.py`, que sigue existiendo como pantalla "expedientes",
    alcanzable desde aquí con el botón "Ver todos los expedientes").

    Carga sus datos de forma síncrona -- sin `TareaEnHilo`/`QThreadPool` (Sprint
    26) -- porque son consultas SQL livianas más aritmética de fechas sobre, como
    mucho, unas pocas centenas de expedientes/obligaciones: no es la clase de
    operación pesada (`liquidar()`, exportar PDF/Word) que el Sprint 26 sacó del
    hilo de UI. Ver la sección Architecture del plan de este sprint para el
    detalle completo de esta decisión.
    """

    def __init__(self, on_expediente_abierto=None, on_ver_expedientes=None):
        super().__init__()
        self._on_expediente_abierto = on_expediente_abierto
        self._on_ver_expedientes = on_ver_expedientes

        self.boton_ver_expedientes = QPushButton("Ver todos los expedientes")
        self.boton_ver_expedientes.setProperty("class", "primary")
        self.boton_ver_expedientes.clicked.connect(self._emitir_ver_expedientes)

        self.etiqueta_total_expedientes = QLabel()

        self.tabla_por_area = QTableWidget(len(AREAS_DERECHO), 2)
        self.tabla_por_area.setHorizontalHeaderLabels(["Área", "Expedientes"])

        grupo_resumen = QGroupBox("Expedientes por área")
        layout_resumen = QVBoxLayout()
        layout_resumen.addWidget(self.etiqueta_total_expedientes)
        layout_resumen.addWidget(self.tabla_por_area)
        grupo_resumen.setLayout(layout_resumen)

        self.tabla_alertas = QTableWidget(0, 4)
        self.tabla_alertas.setHorizontalHeaderLabels(
            ["Radicado", "Concepto", "Fecha límite", "Estado"]
        )
        self.tabla_alertas.cellDoubleClicked.connect(self._abrir_expediente_de_alerta)
        self._expediente_ids_por_fila_alerta: list[int] = []

        grupo_alertas = QGroupBox("Plazos próximos a vencer")
        layout_alertas = QVBoxLayout()
        layout_alertas.addWidget(self.tabla_alertas)
        grupo_alertas.setLayout(layout_alertas)

        layout_cta = QHBoxLayout()
        layout_cta.addStretch()
        layout_cta.addWidget(self.boton_ver_expedientes)

        layout_principal = QVBoxLayout()
        layout_principal.addLayout(layout_cta)
        layout_principal.addWidget(grupo_resumen)
        layout_principal.addWidget(grupo_alertas)
        self.setLayout(layout_principal)

        self.refrescar()

    def _emitir_ver_expedientes(self) -> None:
        if self._on_ver_expedientes:
            self._on_ver_expedientes()

    def _abrir_expediente_de_alerta(self, fila: int, _columna: int) -> None:
        if self._on_expediente_abierto:
            self._on_expediente_abierto(self._expediente_ids_por_fila_alerta[fila])

    def refrescar(self, hoy: date | None = None) -> None:
        hoy = hoy or date.today()
        session = session_module.get_session()
        expedientes = session.query(Expediente).all()

        self._refrescar_conteo_por_area(expedientes)
        self._refrescar_alertas_vencimiento(expedientes, hoy)

        session.close()

    def _refrescar_conteo_por_area(self, expedientes: list[Expediente]) -> None:
        self.etiqueta_total_expedientes.setText(f"Total de expedientes: {len(expedientes)}")

        conteo_por_area = dict.fromkeys((codigo for codigo, _et, _hab in AREAS_DERECHO), 0)
        for expediente in expedientes:
            conteo_por_area[expediente.area_derecho.value] += 1

        for fila, (codigo, etiqueta, _habilitada) in enumerate(AREAS_DERECHO):
            self.tabla_por_area.setItem(fila, 0, QTableWidgetItem(etiqueta))
            self.tabla_por_area.setItem(
                fila, 1, QTableWidgetItem(str(conteo_por_area[codigo]))
            )

    def _refrescar_alertas_vencimiento(
        self, expedientes: list[Expediente], hoy: date
    ) -> None:
        """Alerta si la prescripción de la acción ejecutiva (`TipoAccion.EJECUTIVA`
        -- el mismo default que usa `filtrar_cuotas_prescritas` en
        `app/engine/temporal/prescripcion.py`, ver Architecture del plan de este
        sprint) de alguna obligación no pagada cae dentro de los próximos
        `DIAS_ALERTA_VENCIMIENTO` días, o ya venció."""
        limite = hoy + timedelta(days=DIAS_ALERTA_VENCIMIENTO)
        alertas = []
        for expediente in expedientes:
            for obligacion in expediente.obligaciones:
                if obligacion.pagada:
                    continue
                try:
                    fecha_limite = calcular_prescripcion(
                        obligacion.fecha_origen, TipoAccion.EJECUTIVA
                    )
                except ParametroNoDisponibleError:
                    # Sin PRESCRIPCION_EJECUTIVA_MESES configurado en Parametros no
                    # se puede calcular la fecha limite de esta obligacion -- se
                    # omite de las alertas en vez de tumbar todo el dashboard.
                    continue
                if fecha_limite <= limite:
                    dias_restantes = (fecha_limite - hoy).days
                    if dias_restantes < 0:
                        estado = "Vencido"
                    else:
                        estado = f"Vence en {dias_restantes} días"
                    alertas.append((expediente, obligacion, fecha_limite, estado))

        alertas.sort(key=lambda item: item[2])

        self.tabla_alertas.setRowCount(len(alertas))
        self._expediente_ids_por_fila_alerta = []
        for fila, (expediente, obligacion, fecha_limite, estado) in enumerate(alertas):
            self.tabla_alertas.setItem(fila, 0, QTableWidgetItem(expediente.radicado))
            self.tabla_alertas.setItem(fila, 1, QTableWidgetItem(obligacion.concepto))
            self.tabla_alertas.setItem(fila, 2, QTableWidgetItem(fecha_limite.isoformat()))
            self.tabla_alertas.setItem(fila, 3, QTableWidgetItem(estado))
            self._expediente_ids_por_fila_alerta.append(expediente.id)
```

- [ ] **Step 4: Correr toda la suite del archivo para verificar que pasa**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_dashboard.py -v`
Expected: 10 passed (los 4 de la Task 1 + los 6 nuevos de esta task).

- [ ] **Step 5: Ruff**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check app/views/dashboard.py tests/views/test_dashboard.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add app/views/dashboard.py tests/views/test_dashboard.py
git commit -m "$(cat <<'EOF'
feat(sprint33): agregar alertas de plazos proximos a vencer al dashboard

EOF
)"
```

---

### Task 3: Actividad reciente (últimas liquidaciones ejecutadas en cualquier expediente)

**Files:**
- Modify: `app/views/dashboard.py` (imports, constante `MAX_LIQUIDACIONES_RECIENTES`, `__init__`,
  `refrescar`, método nuevo `_refrescar_actividad_reciente`)
- Modify: `tests/views/test_dashboard.py` (imports, tests nuevos)

- [ ] **Step 1: Agregar los tests que fallan**

Agregar al inicio de `tests/views/test_dashboard.py`, reemplazando el bloque de imports actual
(las primeras 17 líneas, hasta el `)` de cierre del `from database.models import (...)`) por:

```python
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.engine.audit.service import registrar_liquidacion
from app.engine.liquidation.result import LiquidationResult
from app.engine.temporal.prescripcion import TipoAccion, calcular_prescripcion
from app.views.dashboard import DashboardView
from database.models import (
    AreaDerecho,
    Base,
    Expediente,
    Obligacion,
    ParametroLegal,
    TipoObligacion,
)
```

Y agregar al final del archivo (después de `test_dashboard_doble_clic_en_alerta_abre_el_expediente`):

```python
def test_dashboard_muestra_liquidaciones_recientes_de_todos_los_expedientes(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = _crear_expediente(session, "2026-020", AreaDerecho.CIVIL_FAMILIA)
    registrar_liquidacion(
        session,
        expediente_id=expediente.id,
        area_derecho="CIVIL_FAMILIA",
        fecha_corte=date(2026, 1, 1),
        resultado=LiquidationResult(items=[]),
        fecha_ejecucion=datetime(2026, 1, 2, 10, 0),
    )
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)

    assert view.tabla_actividad.rowCount() == 1
    assert view.tabla_actividad.item(0, 1).text() == "2026-020"
    assert view.tabla_actividad.item(0, 2).text() == "CIVIL_FAMILIA"


def test_dashboard_actividad_reciente_ordena_recientes_primero_y_recorta_a_10(
    qtbot, monkeypatch
):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = _crear_expediente(session, "2026-021", AreaDerecho.CIVIL_FAMILIA)
    for dia in range(1, 13):
        registrar_liquidacion(
            session,
            expediente_id=expediente.id,
            area_derecho="CIVIL_FAMILIA",
            fecha_corte=date(2026, 1, 1),
            resultado=LiquidationResult(items=[]),
            fecha_ejecucion=datetime(2026, 1, dia, 10, 0),
        )
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)

    assert view.tabla_actividad.rowCount() == 10
    assert view.tabla_actividad.item(0, 0).text() == "2026-01-12 10:00"
    assert view.tabla_actividad.item(9, 0).text() == "2026-01-03 10:00"
```

- [ ] **Step 2: Correr los tests nuevos para verificar que fallan**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_dashboard.py -k actividad -v`
Expected: FAIL (`AttributeError: 'DashboardView' object has no attribute 'tabla_actividad'`).

- [ ] **Step 3: Reemplazar el contenido completo de `app/views/dashboard.py`**

```python
from datetime import date, timedelta

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.core.exceptions import ParametroNoDisponibleError
from app.engine.audit.service import historial_de_expediente
from app.engine.temporal.prescripcion import TipoAccion, calcular_prescripcion
from database.models import AuditLog, Expediente

DIAS_ALERTA_VENCIMIENTO = 90
MAX_LIQUIDACIONES_RECIENTES = 10


class DashboardView(QWidget):
    """Pantalla de inicio (Sprint 33): resumen agregado de todos los expedientes,
    en vez de abrir directo al listado plano de expedientes
    (`app/views/expedientes.py`, que sigue existiendo como pantalla "expedientes",
    alcanzable desde aquí con el botón "Ver todos los expedientes").

    Carga sus datos de forma síncrona -- sin `TareaEnHilo`/`QThreadPool` (Sprint
    26) -- porque son consultas SQL livianas más aritmética de fechas sobre, como
    mucho, unas pocas centenas de expedientes/obligaciones: no es la clase de
    operación pesada (`liquidar()`, exportar PDF/Word) que el Sprint 26 sacó del
    hilo de UI. Ver la sección Architecture del plan de este sprint para el
    detalle completo de esta decisión.
    """

    def __init__(self, on_expediente_abierto=None, on_ver_expedientes=None):
        super().__init__()
        self._on_expediente_abierto = on_expediente_abierto
        self._on_ver_expedientes = on_ver_expedientes

        self.boton_ver_expedientes = QPushButton("Ver todos los expedientes")
        self.boton_ver_expedientes.setProperty("class", "primary")
        self.boton_ver_expedientes.clicked.connect(self._emitir_ver_expedientes)

        self.etiqueta_total_expedientes = QLabel()

        self.tabla_por_area = QTableWidget(len(AREAS_DERECHO), 2)
        self.tabla_por_area.setHorizontalHeaderLabels(["Área", "Expedientes"])

        grupo_resumen = QGroupBox("Expedientes por área")
        layout_resumen = QVBoxLayout()
        layout_resumen.addWidget(self.etiqueta_total_expedientes)
        layout_resumen.addWidget(self.tabla_por_area)
        grupo_resumen.setLayout(layout_resumen)

        self.tabla_alertas = QTableWidget(0, 4)
        self.tabla_alertas.setHorizontalHeaderLabels(
            ["Radicado", "Concepto", "Fecha límite", "Estado"]
        )
        self.tabla_alertas.cellDoubleClicked.connect(self._abrir_expediente_de_alerta)
        self._expediente_ids_por_fila_alerta: list[int] = []

        grupo_alertas = QGroupBox("Plazos próximos a vencer")
        layout_alertas = QVBoxLayout()
        layout_alertas.addWidget(self.tabla_alertas)
        grupo_alertas.setLayout(layout_alertas)

        self.tabla_actividad = QTableWidget(0, 3)
        self.tabla_actividad.setHorizontalHeaderLabels(["Fecha", "Radicado", "Área"])

        grupo_actividad = QGroupBox("Actividad reciente")
        layout_actividad = QVBoxLayout()
        layout_actividad.addWidget(self.tabla_actividad)
        grupo_actividad.setLayout(layout_actividad)

        layout_cta = QHBoxLayout()
        layout_cta.addStretch()
        layout_cta.addWidget(self.boton_ver_expedientes)

        layout_principal = QVBoxLayout()
        layout_principal.addLayout(layout_cta)
        layout_principal.addWidget(grupo_resumen)
        layout_principal.addWidget(grupo_alertas)
        layout_principal.addWidget(grupo_actividad)
        self.setLayout(layout_principal)

        self.refrescar()

    def _emitir_ver_expedientes(self) -> None:
        if self._on_ver_expedientes:
            self._on_ver_expedientes()

    def _abrir_expediente_de_alerta(self, fila: int, _columna: int) -> None:
        if self._on_expediente_abierto:
            self._on_expediente_abierto(self._expediente_ids_por_fila_alerta[fila])

    def refrescar(self, hoy: date | None = None) -> None:
        hoy = hoy or date.today()
        session = session_module.get_session()
        expedientes = session.query(Expediente).all()

        self._refrescar_conteo_por_area(expedientes)
        self._refrescar_alertas_vencimiento(expedientes, hoy)
        self._refrescar_actividad_reciente(session, expedientes)

        session.close()

    def _refrescar_conteo_por_area(self, expedientes: list[Expediente]) -> None:
        self.etiqueta_total_expedientes.setText(f"Total de expedientes: {len(expedientes)}")

        conteo_por_area = dict.fromkeys((codigo for codigo, _et, _hab in AREAS_DERECHO), 0)
        for expediente in expedientes:
            conteo_por_area[expediente.area_derecho.value] += 1

        for fila, (codigo, etiqueta, _habilitada) in enumerate(AREAS_DERECHO):
            self.tabla_por_area.setItem(fila, 0, QTableWidgetItem(etiqueta))
            self.tabla_por_area.setItem(
                fila, 1, QTableWidgetItem(str(conteo_por_area[codigo]))
            )

    def _refrescar_alertas_vencimiento(
        self, expedientes: list[Expediente], hoy: date
    ) -> None:
        """Alerta si la prescripción de la acción ejecutiva (`TipoAccion.EJECUTIVA`
        -- el mismo default que usa `filtrar_cuotas_prescritas` en
        `app/engine/temporal/prescripcion.py`, ver Architecture del plan de este
        sprint) de alguna obligación no pagada cae dentro de los próximos
        `DIAS_ALERTA_VENCIMIENTO` días, o ya venció."""
        limite = hoy + timedelta(days=DIAS_ALERTA_VENCIMIENTO)
        alertas = []
        for expediente in expedientes:
            for obligacion in expediente.obligaciones:
                if obligacion.pagada:
                    continue
                try:
                    fecha_limite = calcular_prescripcion(
                        obligacion.fecha_origen, TipoAccion.EJECUTIVA
                    )
                except ParametroNoDisponibleError:
                    # Sin PRESCRIPCION_EJECUTIVA_MESES configurado en Parametros no
                    # se puede calcular la fecha limite de esta obligacion -- se
                    # omite de las alertas en vez de tumbar todo el dashboard.
                    continue
                if fecha_limite <= limite:
                    dias_restantes = (fecha_limite - hoy).days
                    if dias_restantes < 0:
                        estado = "Vencido"
                    else:
                        estado = f"Vence en {dias_restantes} días"
                    alertas.append((expediente, obligacion, fecha_limite, estado))

        alertas.sort(key=lambda item: item[2])

        self.tabla_alertas.setRowCount(len(alertas))
        self._expediente_ids_por_fila_alerta = []
        for fila, (expediente, obligacion, fecha_limite, estado) in enumerate(alertas):
            self.tabla_alertas.setItem(fila, 0, QTableWidgetItem(expediente.radicado))
            self.tabla_alertas.setItem(fila, 1, QTableWidgetItem(obligacion.concepto))
            self.tabla_alertas.setItem(fila, 2, QTableWidgetItem(fecha_limite.isoformat()))
            self.tabla_alertas.setItem(fila, 3, QTableWidgetItem(estado))
            self._expediente_ids_por_fila_alerta.append(expediente.id)

    def _refrescar_actividad_reciente(
        self, session, expedientes: list[Expediente]
    ) -> None:
        """Últimas liquidaciones ejecutadas en cualquier expediente, más recientes
        primero -- reutiliza `historial_de_expediente` (Sprint 9,
        `app/engine/audit/service.py`) una vez por expediente y fusiona/recorta el
        resultado combinado, en vez de duplicar la consulta a `AuditLog` aquí."""
        registros: list[AuditLog] = []
        for expediente in expedientes:
            registros.extend(historial_de_expediente(session, expediente.id))
        registros.sort(key=lambda log: log.fecha_ejecucion, reverse=True)
        registros = registros[:MAX_LIQUIDACIONES_RECIENTES]

        self.tabla_actividad.setRowCount(len(registros))
        for fila, registro in enumerate(registros):
            self.tabla_actividad.setItem(
                fila,
                0,
                QTableWidgetItem(registro.fecha_ejecucion.strftime("%Y-%m-%d %H:%M")),
            )
            self.tabla_actividad.setItem(
                fila, 1, QTableWidgetItem(registro.expediente.radicado)
            )
            self.tabla_actividad.setItem(fila, 2, QTableWidgetItem(registro.area_derecho))
```

- [ ] **Step 4: Correr toda la suite del archivo para verificar que pasa**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_dashboard.py -v`
Expected: 12 passed (los 10 de las Tasks 1-2 + los 2 nuevos de esta task).

- [ ] **Step 5: Ruff**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check app/views/dashboard.py tests/views/test_dashboard.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add app/views/dashboard.py tests/views/test_dashboard.py
git commit -m "$(cat <<'EOF'
feat(sprint33): agregar actividad reciente al dashboard

EOF
)"
```

---

### Task 4: Registrar `DashboardView` como pantalla de inicio en `MainWindow`

**Antes de empezar, leer de nuevo la Nota de integración al inicio de este plan.**

**Files:**
- Modify: `app/views/main_window.py` (ver Nota de integración -- el contenido real puede diferir
  del mostrado aquí porque el Sprint 32 ya se ejecutó en esta rama)
- Modify: `tests/views/test_main_window.py`

- [ ] **Step 0: Releer el `app/views/main_window.py` real antes de tocarlo**

Usar la herramienta de lectura sobre `app/views/main_window.py` completo. Confirmar dónde viven,
en el archivo real (pueden no ser las mismas líneas que abajo): la construcción de
`self.expedientes_page` y las demás páginas, `self.stacked_widget.addWidget(...)`, el diccionario
`self._pages`, la asignación inicial de `self._current_page_name`, la llamada final
`self.show_page(...)` de `__init__`, el método `_ir_inicio`, y la condición dentro de
`_actualizar_botones_navegacion` que decide la visibilidad de `boton_inicio`. Aplicar el cambio de
la Step 2 sobre la estructura real encontrada, preservando cualquier cambio del Sprint 32
(breadcrumbs, atajos, íconos en botones) que ya esté presente.

- [ ] **Step 1: Adaptar `tests/views/test_main_window.py` a que el dashboard sea la pantalla
  inicial (tests que fallan)**

Reemplazar el contenido completo de `tests/views/test_main_window.py` por:

```python
from app.views.main_window import MainWindow


def test_main_window_arranca_en_el_dashboard(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.stacked_widget.currentWidget() is window.dashboard_page


def test_main_window_navega_a_la_pagina_de_detalle(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("detalle")

    assert window.stacked_widget.currentWidget() is window.detalle_page


def test_main_window_navega_a_la_pagina_de_resultado(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("resultado")

    assert window.stacked_widget.currentWidget() is window.resultado_page


def test_main_window_pasa_expediente_id_a_la_pagina_de_resultado(qtbot):
    from datetime import date
    from decimal import Decimal

    from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
    from app.engine.liquidation.result import LiquidationResult

    window = MainWindow()
    qtbot.addWidget(window)

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

    window._mostrar_resultado(resultado, expediente_id=42)

    assert window.resultado_page._expediente_id == 42


def test_volver_regresa_a_la_pagina_anterior(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("detalle")
    window._volver()

    assert window.stacked_widget.currentWidget() is window.dashboard_page


def test_volver_respeta_el_orden_de_visitas(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("detalle")
    window.show_page("resultado")
    window._volver()

    assert window.stacked_widget.currentWidget() is window.detalle_page

    window._volver()

    assert window.stacked_widget.currentWidget() is window.dashboard_page


def test_volver_sin_historial_no_hace_nada(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window._volver()

    assert window.stacked_widget.currentWidget() is window.dashboard_page


def test_ir_inicio_limpia_el_historial_y_regresa_al_dashboard(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("detalle")
    window.show_page("resultado")
    window._ir_inicio()

    assert window.stacked_widget.currentWidget() is window.dashboard_page
    assert window._history == []


def test_ir_inicio_refresca_el_dashboard(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    llamadas = []
    monkeypatch.setattr(window.dashboard_page, "refrescar", lambda: llamadas.append(1))

    window.show_page("detalle")
    window._ir_inicio()

    assert llamadas == [1]


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

    assert window.stacked_widget.currentWidget() is window.dashboard_page


def test_click_en_inicio_regresa_al_dashboard_y_oculta_los_botones(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window.show_page("detalle")
    window.show_page("resultado")
    window.boton_inicio.click()

    assert window.stacked_widget.currentWidget() is window.dashboard_page
    assert window.boton_volver.isVisible() is False
    assert window.boton_inicio.isVisible() is False


def test_boton_parametros_navega_a_la_pantalla_de_parametros(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.boton_parametros.click()

    assert window.stacked_widget.currentWidget() is window.parametros_page


def test_main_window_dashboard_ver_expedientes_navega_a_la_lista(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.dashboard_page.boton_ver_expedientes.click()

    assert window.stacked_widget.currentWidget() is window.expedientes_page
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_main_window.py -v`
Expected: FAIL (`AttributeError: 'MainWindow' object has no attribute 'dashboard_page'`) en la
mayoría de los tests.

- [ ] **Step 3: Aplicar el cambio en `app/views/main_window.py`**

El contenido de referencia de este archivo, al momento de escribir este plan (antes del Sprint
32 -- ver Nota de integración), es:

```python
from PySide6.QtWidgets import QMainWindow, QPushButton, QStackedWidget, QToolBar

from app.views.configuracion import ParametrosView
from app.views.expediente_detalle import ExpedienteDetallePage
from app.views.expedientes import ExpedientesListView
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
    ...
```

**Reemplazar el archivo completo por** (aplicando el mismo cambio conceptual sobre la estructura
real que se haya encontrado en el Step 0 si difiere de la anterior):

```python
from PySide6.QtWidgets import QMainWindow, QPushButton, QStackedWidget, QToolBar

from app.views.configuracion import ParametrosView
from app.views.dashboard import DashboardView
from app.views.expediente_detalle import ExpedienteDetallePage
from app.views.expedientes import ExpedientesListView
from app.views.liquidaciones import ResultadoLiquidacionView


class MainWindow(QMainWindow):
    """Ventana principal: aloja las pantallas del flujo y la navegacion entre ellas."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BASTIUM - Ecosistema de Liquidacion Forense")

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.dashboard_page = DashboardView(
            on_expediente_abierto=self._abrir_detalle,
            on_ver_expedientes=self._ir_a_expedientes,
        )
        self.expedientes_page = ExpedientesListView(on_expediente_abierto=self._abrir_detalle)
        self.detalle_page = ExpedienteDetallePage(on_liquidado=self._mostrar_resultado)
        self.resultado_page = ResultadoLiquidacionView()
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

        self._history: list[str] = []
        self._current_page_name = "dashboard"

        self._crear_barra_navegacion()
        self.show_page("dashboard")

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

    def show_page(self, name: str, add_to_history: bool = True) -> None:
        if add_to_history and self._current_page_name != name:
            self._history.append(self._current_page_name)
        self.stacked_widget.setCurrentWidget(self._pages[name])
        self._current_page_name = name
        self._actualizar_botones_navegacion()

    def _actualizar_botones_navegacion(self) -> None:
        self.boton_volver.setVisible(bool(self._history))
        self.boton_inicio.setVisible(self._current_page_name != "dashboard")

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
        self.dashboard_page.refrescar()
        self.show_page("dashboard", add_to_history=False)

    def _ir_a_expedientes(self) -> None:
        self.expedientes_page.refrescar()
        self.show_page("expedientes")

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

Si el `app/views/main_window.py` real (post Sprint 32) tiene widgets/métodos adicionales
(breadcrumbs, atajos de teclado, íconos en los botones de navegación), **no eliminarlos** -- este
diff solo agrega `dashboard_page`, lo registra como página inicial, agrega `_ir_a_expedientes`, y
cambia las 2 comparaciones contra el string `"expedientes"` (inicial y en
`_actualizar_botones_navegacion`) por `"dashboard"`. Todo lo demás que el Sprint 32 haya agregado se
conserva intacto.

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_main_window.py -v`
Expected: 15 passed.

- [ ] **Step 5: Ruff**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check app/views/main_window.py tests/views/test_main_window.py`
Expected: no errors nuevos introducidos por este diff (si el archivo real, post Sprint 32, ya
tenía deuda de lint preexistente en líneas que este task no toca, no es responsabilidad de este
sprint corregirla -- mismo criterio que Sprint 26 Task 2 Step 10: solo importa que ninguna línea
nueva o modificada por este task aparezca en la salida).

- [ ] **Step 6: Commit**

```bash
git add app/views/main_window.py tests/views/test_main_window.py
git commit -m "$(cat <<'EOF'
feat(sprint33): registrar el dashboard como pantalla de inicio de la app

EOF
)"
```

---

### Task 5: Actualizar `docs/GUIA_USUARIO.md` — la app ya no arranca en la Lista de Expedientes

**Files:**
- Modify: `docs/GUIA_USUARIO.md`

`docs/GUIA_USUARIO.md` describe hoy, en la sección "4. Tour de la aplicación", que el programa
"tiene 4 pantallas" y que "Lista de Expedientes" es "la pantalla con la que arranca el programa",
y que "🏠 Inicio" "regresa directo a la Lista de Expedientes". Ambas afirmaciones quedan
factualmente incorrectas después de la Task 4 de este plan -- a diferencia del Sprint 26 (cambio
interno de responsividad, sin afectar ningún flujo documentado), este sprint sí cambia
comportamiento visible que la guía describe explícitamente. Corrección angosta: solo se toca la
sección 4 y la línea de fecha de última actualización del encabezado; no se renumeran ni se tocan
las demás secciones del documento (fuera de alcance de este sprint).

- [ ] **Step 1: Actualizar la fecha de "Última actualización" del encabezado**

En `docs/GUIA_USUARIO.md`, cambiar:

```
> **Última actualización:** 2026-08-03 — refleja el estado de Civil/Familia, Comercial, Sancionatorio,
> Honorarios/Litigio, Laboral, Tributario, exportación de liquidaciones a PDF/Word, los botones de
> navegación (Volver/Inicio) y de editar/eliminar expediente, y la pantalla "⚙ Parámetros" de parámetros
> legales versionados. Cada vez que se complete un sprint nuevo de [`Pendientes.md`](../Pendientes.md),
> esta guía se actualiza para que nunca quede desactualizada respecto al programa real.
```

a:

```
> **Última actualización:** 2026-08-06 — refleja el estado de Civil/Familia, Comercial, Sancionatorio,
> Honorarios/Litigio, Laboral, Tributario, exportación de liquidaciones a PDF/Word, los botones de
> navegación (Volver/Inicio) y de editar/eliminar expediente, la pantalla "⚙ Parámetros" de parámetros
> legales versionados, y el Dashboard de inicio con resumen de expedientes y alertas de vencimiento.
> Cada vez que se complete un sprint nuevo de [`Pendientes.md`](../Pendientes.md), esta guía se
> actualiza para que nunca quede desactualizada respecto al programa real.
```

- [ ] **Step 2: Actualizar la sección "4. Tour de la aplicación"**

Cambiar:

```
BASTIUM tiene **4 pantallas**. Te mueves entre las tres primeras automáticamente según lo que hagas (no
hay un menú de navegación separado); a la cuarta se entra con un botón de la barra superior:

1. **Lista de Expedientes** — la pantalla con la que arranca el programa. Muestra una tabla con todos los
   expedientes que ya creaste (radicado, demandante, demandado, área, y botones de **Editar** y
   **Eliminar** por fila) y un botón **"Nuevo expediente"**. Si haces doble clic sobre una fila, entras al
   detalle de ese expediente.

2. **Detalle de Expediente** — se abre al hacer doble clic en un expediente de la lista. Aquí ves dos
   tablas lado a lado: **Obligaciones** (las deudas del expediente) y **Abonos** (los pagos hechos), cada
   una con su botón de "Agregar". Abajo hay un botón grande **"Liquidar"**.

3. **Resultado de Liquidación** — se abre automáticamente después de presionar "Liquidar". Muestra una
   tabla con el detalle día por día de cómo se acumuló el interés, y al final tres totales: interés
   acumulado, pagos aplicados y saldo final.

4. **⚙ Parámetros** — la pantalla de parámetros legales versionados (tasas, topes, plazos e indicadores
   históricos). Se abre desde el botón **"⚙ Parámetros"** de la barra superior, disponible siempre, sin
   importar en qué otra pantalla estés. Ver [sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros)
   para el detalle completo.

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

```
BASTIUM tiene **5 pantallas**. Te mueves entre la mayoría automáticamente según lo que hagas (no hay un
menú de navegación separado); a la de Parámetros se entra con un botón de la barra superior:

1. **Dashboard (Inicio)** — la pantalla con la que arranca el programa (Sprint 33). Muestra el total de
   expedientes y su conteo por área, una tabla de **"Plazos próximos a vencer"** (obligaciones no pagadas
   cuya prescripción vence dentro de los próximos 90 días, o ya vencida — doble clic sobre una fila abre
   ese expediente), y una tabla de **"Actividad reciente"** con las últimas liquidaciones ejecutadas en
   cualquier expediente. El botón **"Ver todos los expedientes"** lleva a la Lista de Expedientes.

2. **Lista de Expedientes** — se abre desde el botón "Ver todos los expedientes" del Dashboard. Muestra
   una tabla con todos los expedientes que ya creaste (radicado, demandante, demandado, área, y botones de
   **Editar** y **Eliminar** por fila) y un botón **"Nuevo expediente"**. Si haces doble clic sobre una
   fila, entras al detalle de ese expediente.

3. **Detalle de Expediente** — se abre al hacer doble clic en un expediente de la lista o de la tabla de
   alertas del Dashboard. Aquí ves dos tablas lado a lado: **Obligaciones** (las deudas del expediente) y
   **Abonos** (los pagos hechos), cada una con su botón de "Agregar". Abajo hay un botón grande
   **"Liquidar"**.

4. **Resultado de Liquidación** — se abre automáticamente después de presionar "Liquidar". Muestra una
   tabla con el detalle día por día de cómo se acumuló el interés, y al final tres totales: interés
   acumulado, pagos aplicados y saldo final.

5. **⚙ Parámetros** — la pantalla de parámetros legales versionados (tasas, topes, plazos e indicadores
   históricos). Se abre desde el botón **"⚙ Parámetros"** de la barra superior, disponible siempre, sin
   importar en qué otra pantalla estés. Ver [sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros)
   para el detalle completo.

En la parte superior de la ventana hay botones de navegación:

- **← Volver** — regresa a la pantalla anterior (por ejemplo, de Resultado de Liquidación a Detalle de
  Expediente, y de ahí al Dashboard o a la Lista de Expedientes, según por dónde hayas entrado). Recuerda
  el orden exacto en que navegaste, no solo "la pantalla anterior en general". Está oculto cuando no hay a
  dónde volver (por ejemplo, recién abierto el programa).
- **🏠 Inicio** — regresa directo al Dashboard sin importar en qué pantalla estés, y refresca sus datos.
  Está oculto cuando ya estás en el Dashboard.
- **⚙ Parámetros** — siempre visible, en cualquier pantalla; te lleva a la pantalla de parámetros legales
  versionados (ver punto 5 arriba).
```

- [ ] **Step 3: Commit**

```bash
git add docs/GUIA_USUARIO.md
git commit -m "$(cat <<'EOF'
docs(sprint33): actualizar guia de usuario -- la app ahora arranca en el Dashboard

EOF
)"
```

---

### Task 6: Suite completa, ruff y cierre técnico del sprint (sin tocar `Pendientes.md`)

**Files:** ninguno nuevo — solo verificación.

- [ ] **Step 1: Correr toda la suite del proyecto**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -v`
Expected: todos los tests en verde (los 12 nuevos de `tests/views/test_dashboard.py` + los ~15 de
`tests/views/test_main_window.py` reescritos en la Task 4 + el resto de la suite existente sin
cambios de comportamiento en los casos ya cubiertos). En un entorno sin display, exportar
`QT_QPA_PLATFORM=offscreen` antes de correr este comando.

- [ ] **Step 2: Ruff sobre todo el repo**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check .`
Expected: el repo puede seguir teniendo deuda de lint preexistente ajena a este sprint (documentada
ya en planes anteriores, p.ej. Sprint 26/27/28). No usar "cero errores totales" como criterio.
Confirmar en su lugar que ninguno de los archivos tocados por este plan
(`app/views/dashboard.py`, `app/views/main_window.py`, `tests/views/test_dashboard.py`,
`tests/views/test_main_window.py`) aparece en la salida — todos fueron escritos limpios desde
cero o reescritos por completo en las Tasks 1-4, así que no deberían arrastrar ningún error nuevo
ni preexistente.

- [ ] **Step 3: Verificación manual (no automatizable en este plan)**

La Definición de Hecho del sprint pide "al abrir la app, el usuario ve un resumen útil antes de
tener que abrir un expediente puntual". Eso se cubre automáticamente por
`test_main_window_arranca_en_el_dashboard` (Task 4) y por los tests de conteo/alertas/actividad de
`test_dashboard.py` (Tasks 1-3) -- no hace falta un smoke test manual adicional para este sprint
(a diferencia del Sprint 26, que sí requería mover/redimensionar una ventana real mientras liquida,
algo que pytest-qt no puede verificar). Documentar en el reporte final de la sesión que ejecute
este plan que este paso quedó cubierto por tests automatizados, sin pendiente manual.

- [ ] **Step 4 — NO EJECUTAR: recordatorio explícito**

**No editar `Pendientes.md`** (ni el índice, ni la sección del Sprint 33, ni ningún marcador
`✅ Completado`) — el orquestador humano actualiza ese archivo centralmente una vez fusionados los
sprints paralelos. Este plan termina en el Step 2 de esta Task; no hay un commit de cierre de
`Pendientes.md` en este plan.

---

## Self-review notes

- **Cobertura del spec:** `DashboardView` nueva en `app/views/dashboard.py` (Task 1), con conteo
  de expedientes por área (Task 1), lista de plazos próximos a vencer reutilizando
  `calcular_prescripcion`/`app/engine/temporal/prescripcion.py` del Sprint 7 (Task 2), y últimas N
  liquidaciones ejecutadas reutilizando `historial_de_expediente` del Sprint 9 (Task 3);
  `DashboardView` registrada como pantalla de inicio en `MainWindow`, reemplazando la Lista de
  Expedientes como página inicial pero preservándola (accesible con un clic) tal como pide el
  spec ("reemplazando o precediendo") (Task 4); test de GUI que verifica conteo correcto y al
  menos una alerta de vencimiento con datos sintéticos (Task 2, múltiples tests con
  `ParametroLegal`/`Obligacion` sintéticos, sin tocar ninguna base de datos real). Explícitamente
  fuera de alcance, como pide el spec: ninguna gráfica ni dependencia de `matplotlib` -- solo
  `QLabel`/`QTableWidget`.
- **Decisión de concurrencia justificada:** Architecture documenta por qué `DashboardView` carga
  de forma síncrona en vez de usar `TareaEnHilo` (Sprint 26) -- 3 consultas SQL livianas sobre un
  volumen de datos pequeño, sin comparación de costo con `liquidar()`/exportar PDF -- y deja
  explícito el camino de migración si el volumen crece.
- **Riesgo de `ParametroNoDisponibleError` no documentado en el spec, encontrado al explorar el
  código real:** `calcular_prescripcion` depende de que `PRESCRIPCION_EJECUTIVA_MESES` esté
  configurado en la tabla `parametros_legales` (`app/services/parametro_service.py`) -- si no lo
  está, lanza `ParametroNoDisponibleError`. Sin manejarlo, una sola obligación sin este parámetro
  tumbaría el dashboard completo al abrir la app. La Task 2 lo captura por obligación individual
  (`test_dashboard_omite_obligacion_sin_parametro_configurado`), degradando con gracia en vez de
  fallar.
- **Mapeo `AreaDerecho` → `TipoAccion` no inventado:** el modelo `Obligacion` no tiene ningún
  campo que indique tipo de acción procesal, y no hay ningún mapeo área→tipo de acción con
  respaldo legal en el código existente. Se usa `TipoAccion.EJECUTIVA` para todas las áreas,
  documentado explícitamente como heurística (mismo default que
  `filtrar_cuotas_prescritas`), no como regla legal nueva -- ver Architecture para la justificación
  completa y la recomendación de abrir un hallazgo futuro si el despacho confirma un mapeo más
  preciso.
- **Nota de integración explícita:** dado que este plan se escribió contra el
  `app/views/main_window.py` anterior al Sprint 32 (que se ejecuta antes que este plan en la
  misma rama), la Task 4 incluye un Step 0 dedicado a releer el archivo real antes de aplicar el
  diff, y el diff mostrado se presenta explícitamente como ilustrativo, no literal.
- **Documentación de usuario actualizada donde quedó desactualizada:** a diferencia del Sprint 26
  (cambio interno, sin tocar docs), este sprint sí cambia un flujo que `docs/GUIA_USUARIO.md`
  describe explícitamente (pantalla inicial, comportamiento de "🏠 Inicio") -- Task 5 corrige eso
  con un commit `docs:` angosto, sin renumerar ni tocar el resto del documento.
- **Sin placeholders:** cada Task reemplaza el contenido completo de los archivos que toca (no
  diffs parciales frágiles de líneas sueltas, salvo la Task 5 sobre un archivo Markdown donde el
  bloque a reemplazar es autocontenido y se muestra completo en ambos lados, antes/después).

### Critical Files for Implementation
- app/views/dashboard.py
- app/views/main_window.py
- tests/views/test_dashboard.py
- tests/views/test_main_window.py
- app/engine/temporal/prescripcion.py
