# Sprint 26 — Responsividad de la interfaz: liquidar/exportar sin congelar la UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `estrategia.liquidar()` (`app/views/expediente_detalle.py`) y la exportación a
PDF/Word (`app/views/liquidaciones.py`) dejan de ejecutarse de forma síncrona en el hilo de UI.
Ambas operaciones se mueven a `QThreadPool` con un `QProgressDialog` indeterminado visible
mientras corren, y el botón que las dispara queda deshabilitado hasta que terminan (evitando
doble liquidación/exportación concurrente sobre el mismo expediente).

**Architecture:** Una infraestructura reutilizable mínima (`app/views/concurrency.py`,
`TareaEnHilo` + `SenalesTareaEnHilo`) envuelve cualquier función en un `QRunnable` ejecutado en
`QThreadPool.globalInstance()`, reportando resultado/excepción de vuelta al hilo principal vía
señales Qt. `ExpedienteDetallePage._liquidar()` y `ResultadoLiquidacionView._exportar_pdf()` /
`_exportar_word()` empaquetan su trabajo (que hoy corre inline) en funciones a nivel de módulo
que abren y cierran su propia sesión de SQLAlchemy dentro del hilo de fondo — nunca se pasa una
sesión ya abierta entre hilos. El manejo de excepciones de dominio (`AreaNoImplementadaError`,
`CuotaLitisExcedeTopeError`, etc.) que hoy vive en un `try/except` inline se reubica en un slot
(`_on_liquidar_fallo`) que recibe la excepción vía señal y aplica la misma lógica de despacho por
tipo. El motor interno (`estrategia.liquidar()`) no se toca ni se paraleliza — solo se saca del
hilo de UI la llamada completa.

**Tech Stack:** Python, PySide6 (Qt: `QThreadPool`, `QRunnable`, `QObject`/`Signal`,
`QProgressDialog`), SQLAlchemy, pytest + pytest-qt.

---

### Contexto compartido entre tareas — no repetir en cada una

**Riesgo de hilos + SQLite en memoria (afecta Tasks 2 y 3):** los tests de este proyecto usan
`create_engine("sqlite:///:memory:")` sin `poolclass`. Para una URL `:memory:`, SQLAlchemy usa
por defecto un pool que asigna **una conexión distinta por hilo** — así que un hilo de fondo que
llama a `session_module.get_session()` vería una base de datos en memoria completamente vacía,
no la que sembró el hilo principal en el fixture del test (aunque en producción esto no aplica,
porque `bastium.db` es un archivo real, no `:memory:`, y cada conexión nueva sí ve los mismos
datos). La corrección es agregar `poolclass=StaticPool, connect_args={"check_same_thread":
False}` a `create_engine("sqlite:///:memory:")` en los tests que ejercitan el nuevo flujo en
hilo — una sola conexión compartida por todos los hilos. Cada tarea de este plan que lo necesite
lo indica explícitamente con el diff exacto.

---

### Task 1: Infraestructura reutilizable `TareaEnHilo` (QRunnable + señales)

**Files:**
- Create: `app/views/concurrency.py`
- Test: `tests/views/test_concurrency.py`

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/views/test_concurrency.py`:

```python
import threading

from PySide6.QtCore import QThreadPool

from app.views.concurrency import TareaEnHilo


def test_tarea_en_hilo_emite_completada_con_el_resultado_de_la_funcion(qtbot):
    tarea = TareaEnHilo(lambda x, y: x + y, 2, 3)

    with qtbot.waitSignal(tarea.senales.completada, timeout=2000) as blocker:
        QThreadPool.globalInstance().start(tarea)

    assert blocker.args == [5]


def test_tarea_en_hilo_emite_fallo_con_la_excepcion_si_la_funcion_lanza(qtbot):
    def funcion_que_falla():
        raise ValueError("boom")

    tarea = TareaEnHilo(funcion_que_falla)

    with qtbot.waitSignal(tarea.senales.fallo, timeout=2000) as blocker:
        QThreadPool.globalInstance().start(tarea)

    assert isinstance(blocker.args[0], ValueError)
    assert str(blocker.args[0]) == "boom"


def test_tarea_en_hilo_se_ejecuta_en_un_hilo_distinto_al_principal(qtbot):
    hilo_de_ejecucion = []
    tarea = TareaEnHilo(lambda: hilo_de_ejecucion.append(threading.current_thread().ident))

    with qtbot.waitSignal(tarea.senales.completada, timeout=2000):
        QThreadPool.globalInstance().start(tarea)

    assert hilo_de_ejecucion[0] != threading.main_thread().ident


def test_tarea_en_hilo_pasa_kwargs_a_la_funcion(qtbot):
    tarea = TareaEnHilo(lambda base, exponente=1: base**exponente, 2, exponente=10)

    with qtbot.waitSignal(tarea.senales.completada, timeout=2000) as blocker:
        QThreadPool.globalInstance().start(tarea)

    assert blocker.args == [1024]
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_concurrency.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.views.concurrency'` — el módulo no
existe todavía).

- [ ] **Step 3: Crear `app/views/concurrency.py`**

```python
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal


class SenalesTareaEnHilo(QObject):
    """Señales para reportar resultado/error de una `TareaEnHilo` al hilo principal.

    Viven en un QObject aparte (no en el QRunnable) porque QRunnable no hereda de
    QObject y por lo tanto no puede declarar señales de Qt directamente.
    """

    completada = Signal(object)
    fallo = Signal(object)


class TareaEnHilo(QRunnable):
    """QRunnable generico (Sprint 26): ejecuta `funcion(*args, **kwargs)` en el
    QThreadPool global y reporta el resultado (o la excepcion) de vuelta al hilo
    principal via señales Qt, en vez de bloquear el hilo de UI.

    La `funcion` recibida debe abrir y cerrar su propia sesion de SQLAlchemy con
    `database.session.get_session()` si necesita la base de datos -- SQLAlchemy no
    es thread-safe si se comparte una sesion ya abierta entre hilos.
    """

    def __init__(self, funcion: Callable[..., Any], *args: Any, **kwargs: Any):
        super().__init__()
        self.senales = SenalesTareaEnHilo()
        self._funcion = funcion
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            resultado = self._funcion(*self._args, **self._kwargs)
        except Exception as error:  # noqa: BLE001 - se reenvia tal cual al hilo principal
            self.senales.fallo.emit(error)
        else:
            self.senales.completada.emit(resultado)
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_concurrency.py -v`
Expected: 4 passed.

- [ ] **Step 5: Ruff**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check app/views/concurrency.py tests/views/test_concurrency.py`
Expected: no errors (si `BLE001` no está en el ruleset seleccionado — `select = ["E", "F", "I",
"UP", "B"]` en `pyproject.toml` — el `# noqa: BLE001` es inofensivo, ruff ignora noqa de reglas
no activas).

- [ ] **Step 6: Commit**

```bash
git add app/views/concurrency.py tests/views/test_concurrency.py
git commit -m "$(cat <<'EOF'
feat(sprint26): agregar TareaEnHilo, envoltorio reutilizable de QRunnable con señales

EOF
)"
```

---

### Task 2: `ExpedienteDetallePage._liquidar()` corre en `QThreadPool`, con `QProgressDialog` y botón deshabilitado

**Files:**
- Modify: `app/views/expediente_detalle.py` (imports, `__init__`, reemplazar `_liquidar`)
- Modify: `tests/views/test_expediente_detalle.py` (fixtures de engine + 11 call sites existentes
  + 3 tests nuevos)
- Test: `tests/views/test_expediente_detalle.py`

- [ ] **Step 1: Adaptar el primer test existente al nuevo flujo asíncrono (test que falla)**

En `tests/views/test_expediente_detalle.py`, el test `test_liquidar_invoca_callback_con_resultado`
pasa de:

```python
def test_liquidar_invoca_callback_con_resultado(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    page._liquidar()

    assert len(resultados_recibidos) == 1
    resultado, exp_id = resultados_recibidos[0]
    assert exp_id == expediente_id
    assert resultado.final_balance().principal == Decimal("427900.00")
```

a:

```python
def test_liquidar_invoca_callback_con_resultado(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()

    assert len(resultados_recibidos) == 1
    resultado, exp_id = resultados_recibidos[0]
    assert exp_id == expediente_id
    assert resultado.final_balance().principal == Decimal("427900.00")
```

(esto todavía no alcanza para que pase — `page.liquidacion_finalizada` no existe hasta el Step
4 — pero fija el contrato que va a exponer la página: una señal que se emite cuando la
liquidación en segundo plano termina, sea con éxito o con error).

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_expediente_detalle.py -k test_liquidar_invoca_callback_con_resultado -v`
Expected: FAIL (`AttributeError: 'ExpedienteDetallePage' object has no attribute
'liquidacion_finalizada'`).

- [ ] **Step 3: Agregar 2 tests nuevos que fijan el comportamiento de responsividad pedido por el
  sprint (botón deshabilitado + sin doble liquidación concurrente)**

Agregar al final de `tests/views/test_expediente_detalle.py`:

```python
def test_liquidar_deshabilita_el_boton_mientras_esta_en_curso(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    assert page.boton_liquidar.isEnabled() is True

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()
        assert page.boton_liquidar.isEnabled() is False

    assert page.boton_liquidar.isEnabled() is True


def test_liquidar_ignora_llamada_concurrente_mientras_hay_una_en_curso(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    llamadas = []

    def capturar(resultado, exp_id):
        llamadas.append((resultado, exp_id))

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()
        page._liquidar()  # concurrente -- debe ser ignorada, el boton ya esta deshabilitado

    assert len(llamadas) == 1
```

- [ ] **Step 4: Actualizar imports y `__init__` en `app/views/expediente_detalle.py`**

Cambiar el bloque de imports (líneas 1-32) de:

```python
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.exceptions import (
    AreaNoImplementadaError,
    CostasFueraDeRangoError,
    CuotaLitisExcedeTopeError,
    ParametroNoDisponibleError,
    TarifaNoDisponibleError,
    TRMNoDisponibleError,
    UVTNoDisponibleError,
)
from app.engine.audit.service import (
    historial_de_expediente,
    reconstruir_liquidacion,
    registrar_liquidacion,
)
from app.engine.liquidation.registry import AreaRegistry
from app.views.abonos import AbonoFormDialog
from app.views.eventos_laborales import EventoLaboralFormDialog
from app.views.obligaciones import ObligacionFormDialog
from database.models import AreaDerecho, Expediente
```

a:

```python
from PySide6.QtCore import Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.exceptions import (
    AreaNoImplementadaError,
    CostasFueraDeRangoError,
    CuotaLitisExcedeTopeError,
    ParametroNoDisponibleError,
    TarifaNoDisponibleError,
    TRMNoDisponibleError,
    UVTNoDisponibleError,
)
from app.engine.audit.service import (
    historial_de_expediente,
    reconstruir_liquidacion,
    registrar_liquidacion,
)
from app.engine.liquidation.registry import AreaRegistry
from app.views.abonos import AbonoFormDialog
from app.views.concurrency import TareaEnHilo
from app.views.eventos_laborales import EventoLaboralFormDialog
from app.views.obligaciones import ObligacionFormDialog
from database.models import AreaDerecho, Expediente


def _liquidar_en_hilo_de_fondo(expediente_id: int):
    """Se ejecuta en el QThreadPool (Sprint 26), no en el hilo de UI.

    Abre y cierra su propia sesion de SQLAlchemy dentro de este mismo hilo -- no
    recibe una sesion ya abierta del hilo principal, porque SQLAlchemy no es
    thread-safe si una sesion se comparte entre hilos.
    """
    session = session_module.get_session()
    expediente = session.get(Expediente, expediente_id)
    obligaciones = list(expediente.obligaciones)
    abonos = [abono for obligacion in obligaciones for abono in obligacion.abonos]
    for obligacion in obligaciones:
        list(obligacion.eventos_laborales)  # fuerza el lazy-load antes de session.close()
    fecha_corte = expediente.fecha_corte_default
    area = expediente.area_derecho.value
    session.close()

    estrategia = AreaRegistry.get_strategy(area)
    resultado = estrategia.liquidar(
        obligaciones=obligaciones, abonos=abonos, fecha_corte=fecha_corte
    )

    session = session_module.get_session()
    registrar_liquidacion(
        session,
        expediente_id=expediente_id,
        area_derecho=area,
        fecha_corte=fecha_corte,
        resultado=resultado,
    )
    session.close()
    return resultado
```

Luego, en la clase, agregar la señal justo después de `class ExpedienteDetallePage(QWidget):`:

```python
class ExpedienteDetallePage(QWidget):
    liquidacion_finalizada = Signal()

    def __init__(self, on_liquidado=None):
```

Y en `__init__`, cambiar (línea ~75-76):

```python
        boton_liquidar = QPushButton("Liquidar")
        boton_liquidar.clicked.connect(self._liquidar)
```

a:

```python
        self.boton_liquidar = QPushButton("Liquidar")
        self.boton_liquidar.clicked.connect(self._liquidar)
```

Y más abajo (línea ~98):

```python
        layout_principal.addWidget(boton_liquidar)
```

a:

```python
        layout_principal.addWidget(self.boton_liquidar)
```

- [ ] **Step 5: Reemplazar el método `_liquidar` completo**

El método `_liquidar` (líneas 215-266 del archivo original) pasa de su implementación síncrona
actual a:

```python
    def _liquidar(self) -> None:
        if not self.boton_liquidar.isEnabled():
            return  # ya hay una liquidacion en curso: evita doble liquidacion concurrente
        self.boton_liquidar.setEnabled(False)

        self._dialogo_progreso_liquidar = QProgressDialog("Liquidando...", None, 0, 0, self)
        self._dialogo_progreso_liquidar.setWindowModality(Qt.WindowModality.WindowModal)
        self._dialogo_progreso_liquidar.setCancelButton(None)
        self._dialogo_progreso_liquidar.setMinimumDuration(0)
        self._dialogo_progreso_liquidar.show()

        self._tarea_liquidar = TareaEnHilo(_liquidar_en_hilo_de_fondo, self._expediente_id)
        self._tarea_liquidar.senales.completada.connect(self._on_liquidar_completado)
        self._tarea_liquidar.senales.fallo.connect(self._on_liquidar_fallo)
        QThreadPool.globalInstance().start(self._tarea_liquidar)

    def _finalizar_liquidacion_en_curso(self) -> None:
        self._dialogo_progreso_liquidar.close()
        self.boton_liquidar.setEnabled(True)

    def _on_liquidar_completado(self, resultado) -> None:
        self._finalizar_liquidacion_en_curso()
        self._refrescar_historial()
        if self._on_liquidado:
            self._on_liquidado(resultado, self._expediente_id)
        self.liquidacion_finalizada.emit()

    def _on_liquidar_fallo(self, error: Exception) -> None:
        self._finalizar_liquidacion_en_curso()
        titulos_por_error = {
            AreaNoImplementadaError: "Area no implementada",
            CuotaLitisExcedeTopeError: "Cuota litis excede el tope",
            CostasFueraDeRangoError: "Costas fuera de rango",
            TarifaNoDisponibleError: "Tarifa de costas no disponible",
            UVTNoDisponibleError: "UVT no disponible",
            TRMNoDisponibleError: "TRM no disponible",
            ParametroNoDisponibleError: "Parámetro legal no configurado",
        }
        for tipo_error, titulo in titulos_por_error.items():
            if isinstance(error, tipo_error):
                QMessageBox.warning(self, titulo, str(error))
                self.liquidacion_finalizada.emit()
                return
        if isinstance(error, ValueError):
            QMessageBox.warning(self, "No se pudo liquidar", str(error))
            self.liquidacion_finalizada.emit()
            return
        raise error
```

(el orden de `titulos_por_error` importa: `CuotaLitisExcedeTopeError` y `CostasFueraDeRangoError`
son subclases directas de `ValueError` igual que las demás, así que deben resolverse por
`isinstance` contra su tipo específico antes de caer al `isinstance(error, ValueError)` genérico
— confirmar la jerarquía real en `app/core/exceptions.py` antes de este paso; si alguna de ellas
NO hereda de `ValueError`, el orden del diccionario de todas formas las cubre primero y no
cambia nada).

- [ ] **Step 6: Correr el test del Step 1 para verificar que pasa**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_expediente_detalle.py -k "test_liquidar_invoca_callback_con_resultado or test_liquidar_deshabilita_el_boton_mientras_esta_en_curso or test_liquidar_ignora_llamada_concurrente_mientras_hay_una_en_curso" -v`
Expected: 3 passed.

- [ ] **Step 7: Adaptar los 11 call sites restantes de `page._liquidar()` al patrón asíncrono**

El resto del archivo tiene 11 llamadas más a `page._liquidar()`, todas con uno de estos 3 textos
literales (verificar con
`grep -n "page._liquidar()" tests/views/test_expediente_detalle.py` antes y después). Usar la
herramienta Edit con `replace_all=True` para las dos primeras variantes (cada una aparece 5
veces con texto idéntico) y una edición puntual para la tercera (aparece 1 vez):

Variante A (5 apariciones, sin comentario) — old_string/new_string exactos:

```
    page._liquidar()

    assert
```
→ **no usar este patrón** (el texto que sigue a cada `page._liquidar()` varía). En su lugar,
reemplazar únicamente esta línea exacta, con `replace_all=True`:

old_string:
```
    page._liquidar()
```
new_string:
```
    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()
```

(Esta variante A tiene 5 apariciones en total en el archivo original; la que estaba en
`test_liquidar_invoca_callback_con_resultado` ya fue editada individualmente en el Step 1, así
que a esta altura del Step 7 quedan exactamente 4 apariciones de esta variante, ubicadas — al
momento de escribir este plan — en `test_liquidar_area_civil_con_indexacion_ipc_incluye_evento_de_indexacion`,
`test_liquidar_area_comercial_con_tasa_usuraria_no_muestra_advertencia_y_aplica_sancion`,
`test_liquidar_registra_auditoria_y_refresca_historial` y
`test_doble_clic_en_historial_reconstruye_liquidacion` — correr el `grep` primero y confirmar el
conteo real antes de aplicar `replace_all`, por si el estado del archivo cambió).

Variante B (5 apariciones, con comentario `# no debe lanzar/crashear`) — old_string/new_string
con `replace_all=True`:

old_string:
```
    page._liquidar()  # no debe lanzar/crashear
```
new_string:
```
    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()  # no debe lanzar/crashear
```

Variante C (1 aparición, comentario distinto):

old_string:
```
    page._liquidar()  # no debe lanzar DetachedInstanceError
```
new_string:
```
    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()  # no debe lanzar DetachedInstanceError
```

Después de las 3 ediciones, correr `grep -n "page._liquidar()" tests/views/test_expediente_detalle.py`
y confirmar que **todas** las líneas restantes que invocan `page._liquidar()` están indentadas 8
espacios (dentro de un bloque `with qtbot.waitSignal(...)`), sin excepción — no debe quedar
ninguna llamada suelta a 4 espacios de indentación.

- [ ] **Step 8: Corregir el pool de conexiones SQLite en memoria para que sea visible entre
  hilos**

Este archivo crea el engine de pruebas con `create_engine("sqlite:///:memory:")` en 10 lugares
distintos (helpers `_expediente_con_obligacion`, `_expediente_comercial_con_obligacion_usuraria`,
`_expediente_civil_con_obligacion_indexada`, `_expediente_honorarios_con_cuota_litis_excesiva`,
`_expediente_sancionatorio_con_hecho_posterior_a_2026`,
`_expediente_tributario_sin_parametros_de_sancion`, `_expediente_laboral_con_mora_fase1`,
`_expediente_laboral_pagado_a_tiempo`, `_expediente_laboral_con_seguridad_social`,
`_expediente_laboral_sin_mora`). Ahora que `_liquidar()` corre en un hilo de fondo real, cada uno
de estos engines necesita compartir una única conexión entre hilos (ver "Contexto compartido"
arriba).

Agregar el import al inicio del archivo, después de `from sqlalchemy import create_engine`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
```

Luego, usando Edit con `replace_all=True` sobre todo el archivo:

old_string:
```
    engine = create_engine("sqlite:///:memory:")
```
new_string:
```
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
```

(esta cadena literal `    engine = create_engine("sqlite:///:memory:")` aparece exactamente 10
veces en el archivo, con la misma indentación de 4 espacios en todos los helpers — confirmar el
conteo con `grep -c` antes de aplicar `replace_all=True`, y que después de la edición ya no queda
ninguna aparición sin los `connect_args`/`poolclass`).

- [ ] **Step 9: Correr toda la suite del archivo para verificar que pasa**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_expediente_detalle.py -v`
Expected: todos PASS (los ~29 tests originales + los 2 nuevos del Step 3). Prestar atención
especial a `test_liquidar_registra_auditoria_y_refresca_historial` (línea ~438 original) — si el
Step 8 no se aplicó correctamente, este test falla con `tabla_historial.rowCount() == 0` en vez
de `1`, porque el hilo de fondo no vería la obligación sembrada por el hilo principal (esta es la
prueba concreta de que el fix de `StaticPool` funciona).

- [ ] **Step 10: Ruff**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check app/views/expediente_detalle.py tests/views/test_expediente_detalle.py`
Expected: **estos dos archivos ya tenían deuda de lint previa a este sprint** (confirmado al
escribir este plan: `app/views/expediente_detalle.py` tenía 7 `E501` preexistentes —
p.ej. líneas 65, 146, 152-153, 168, 193 y la línea 228 original que este task reemplaza — y
`tests/views/test_expediente_detalle.py` tenía ~18 `E501`/`E402` preexistentes en líneas que
este task no toca, como los `def test_...(qtbot, monkeypatch):` largos y los imports tardíos de
`registrar_liquidacion`/`AreaRegistry` cerca de la línea 710). Ninguna de esas líneas fue escrita
ni modificada por este plan — no corregirlas (fuera de alcance de Sprint 26). El criterio de
aceptación real es: **ninguna línea nueva o modificada por este task** (las que tocan los Steps
4, 5, 7 y 8 de esta tarea) aparece en la salida de `ruff check`. Si el número total de errores
del archivo bajó o se mantuvo igual respecto a la corrida de la Task 4 (baseline del repo antes
de este plan), y ninguna línea reportada cae dentro del código agregado en esta tarea, el check
pasa.

- [ ] **Step 11: Commit**

```bash
git add app/views/expediente_detalle.py tests/views/test_expediente_detalle.py
git commit -m "$(cat <<'EOF'
feat(sprint26): ejecutar liquidar() en QThreadPool para no congelar la UI

EOF
)"
```

---

### Task 3: `ResultadoLiquidacionView._exportar_pdf()` / `_exportar_word()` corren en `QThreadPool`, con `QProgressDialog` y botones deshabilitados

**Files:**
- Modify: `app/views/liquidaciones.py` (imports, `__init__`, reemplazar
  `_construir_datos_reporte`/`_exportar_pdf`/`_exportar_word`)
- Modify: `tests/views/test_liquidaciones.py` (fixture de engine + 4 call sites existentes + 2
  tests nuevos)
- Test: `tests/views/test_liquidaciones.py`

- [ ] **Step 1: Adaptar el primer test existente al nuevo flujo asíncrono (test que falla)**

En `tests/views/test_liquidaciones.py`, `test_exportar_pdf_crea_archivo_en_la_ruta_elegida` pasa
de:

```python
def test_exportar_pdf_crea_archivo_en_la_ruta_elegida(qtbot, monkeypatch, tmp_path):
    expediente_id = _expediente_para_exportar(monkeypatch)
    ruta_destino = tmp_path / "salida.pdf"
    monkeypatch.setattr(
        "app.views.liquidaciones.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(ruta_destino), "PDF (*.pdf)"),
    )
    monkeypatch.setattr("app.views.liquidaciones.QMessageBox.information", lambda *args, **kwargs: None)

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id)

    view._exportar_pdf()

    assert ruta_destino.exists()
    assert ruta_destino.stat().st_size > 0
```

a:

```python
def test_exportar_pdf_crea_archivo_en_la_ruta_elegida(qtbot, monkeypatch, tmp_path):
    expediente_id = _expediente_para_exportar(monkeypatch)
    ruta_destino = tmp_path / "salida.pdf"
    monkeypatch.setattr(
        "app.views.liquidaciones.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(ruta_destino), "PDF (*.pdf)"),
    )
    monkeypatch.setattr("app.views.liquidaciones.QMessageBox.information", lambda *args, **kwargs: None)

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id)

    with qtbot.waitSignal(view.exportacion_finalizada, timeout=5000):
        view._exportar_pdf()

    assert ruta_destino.exists()
    assert ruta_destino.stat().st_size > 0
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_liquidaciones.py -k test_exportar_pdf_crea_archivo_en_la_ruta_elegida -v`
Expected: FAIL (`AttributeError: 'ResultadoLiquidacionView' object has no attribute
'exportacion_finalizada'`).

- [ ] **Step 3: Agregar 2 tests nuevos (botones deshabilitados + sin exportación concurrente)**

Agregar al final de `tests/views/test_liquidaciones.py`:

```python
def test_exportar_pdf_deshabilita_ambos_botones_mientras_esta_en_curso(
    qtbot, monkeypatch, tmp_path
):
    expediente_id = _expediente_para_exportar(monkeypatch)
    ruta_destino = tmp_path / "salida.pdf"
    monkeypatch.setattr(
        "app.views.liquidaciones.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(ruta_destino), "PDF (*.pdf)"),
    )
    monkeypatch.setattr("app.views.liquidaciones.QMessageBox.information", lambda *args, **kwargs: None)

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id)

    assert view.boton_exportar_pdf.isEnabled() is True
    assert view.boton_exportar_word.isEnabled() is True

    with qtbot.waitSignal(view.exportacion_finalizada, timeout=5000):
        view._exportar_pdf()
        assert view.boton_exportar_pdf.isEnabled() is False
        assert view.boton_exportar_word.isEnabled() is False

    assert view.boton_exportar_pdf.isEnabled() is True
    assert view.boton_exportar_word.isEnabled() is True


def test_exportar_pdf_ignora_llamada_concurrente_mientras_hay_una_en_curso(
    qtbot, monkeypatch, tmp_path
):
    expediente_id = _expediente_para_exportar(monkeypatch)
    ruta_destino = tmp_path / "salida.pdf"
    llamadas_dialogo = []

    def _dialogo_falso(*args, **kwargs):
        llamadas_dialogo.append(1)
        return str(ruta_destino), "PDF (*.pdf)"

    monkeypatch.setattr("app.views.liquidaciones.QFileDialog.getSaveFileName", _dialogo_falso)
    monkeypatch.setattr("app.views.liquidaciones.QMessageBox.information", lambda *args, **kwargs: None)

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id)

    with qtbot.waitSignal(view.exportacion_finalizada, timeout=5000):
        view._exportar_pdf()
        view._exportar_pdf()  # concurrente -- debe ser ignorada, el boton ya esta deshabilitado

    assert len(llamadas_dialogo) == 1
```

- [ ] **Step 4: Actualizar imports en `app/views/liquidaciones.py`**

Cambiar el bloque de imports (líneas 1-24) de:

```python
import re

from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.engine.liquidation.result import LiquidationResult
from app.engine.reports.summary import ReportSummaryBuilder
from app.engine.reports.table_builder import ReportTableBuilder
from app.reports.header import build_encabezado
from app.reports.pdf import JudicialPDFGenerator
from app.reports.word import WordReportGenerator
from database.models import Expediente
```

a:

```python
import re

from PySide6.QtCore import Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.engine.liquidation.result import LiquidationResult
from app.engine.reports.summary import ReportSummaryBuilder
from app.engine.reports.table_builder import ReportTableBuilder
from app.reports.header import build_encabezado
from app.reports.pdf import JudicialPDFGenerator
from app.reports.word import WordReportGenerator
from app.views.concurrency import TareaEnHilo
from database.models import Expediente


def _construir_datos_reporte_en_hilo_de_fondo(resultado: LiquidationResult, expediente_id: int):
    session = session_module.get_session()
    expediente = session.get(Expediente, expediente_id)

    area_label = expediente.area_derecho.value
    for codigo, etiqueta, _habilitada in AREAS_DERECHO:
        if codigo == expediente.area_derecho.value:
            area_label = etiqueta
            break

    title = f"LIQUIDACIÓN DE OBLIGACIONES — ÁREA {area_label.upper()}"
    encabezado = build_encabezado(
        expediente.radicado, expediente.demandante, expediente.demandado, expediente.juzgado
    )
    session.close()

    summary = ReportSummaryBuilder().build_summary(resultado)
    table_data = ReportTableBuilder().build_matrix(resultado)
    renta_liquida = ReportSummaryBuilder().build_renta_liquida(resultado)

    return title, encabezado, summary, table_data, renta_liquida


def _generar_pdf_en_hilo_de_fondo(
    resultado: LiquidationResult, expediente_id: int, ruta: str
) -> str:
    """Se ejecuta en el QThreadPool (Sprint 26): construye el reporte y genera el
    PDF fuera del hilo de UI, con su propia sesion de SQLAlchemy."""
    title, encabezado, summary, table_data, renta_liquida = (
        _construir_datos_reporte_en_hilo_de_fondo(resultado, expediente_id)
    )
    JudicialPDFGenerator(ruta).generate(
        title, summary, table_data, encabezado, renta_liquida=renta_liquida
    )
    return ruta


def _generar_word_en_hilo_de_fondo(
    resultado: LiquidationResult, expediente_id: int, ruta: str
) -> str:
    """Version Word de _generar_pdf_en_hilo_de_fondo (Sprint 26)."""
    title, encabezado, summary, table_data, renta_liquida = (
        _construir_datos_reporte_en_hilo_de_fondo(resultado, expediente_id)
    )
    WordReportGenerator(ruta).generate(
        title, summary, table_data, encabezado, renta_liquida=renta_liquida
    )
    return ruta
```

- [ ] **Step 5: Agregar la señal de clase y reemplazar `_construir_datos_reporte` /
  `_exportar_pdf` / `_exportar_word`**

Cambiar `class ResultadoLiquidacionView(QWidget):` a:

```python
class ResultadoLiquidacionView(QWidget):
    exportacion_finalizada = Signal()

    def __init__(self):
```

Eliminar el método `_construir_datos_reporte` completo (líneas 114-135 del archivo original — ya
no se usa, su lógica se movió a `_construir_datos_reporte_en_hilo_de_fondo` a nivel de módulo en
el Step 4). Reemplazar `_exportar_pdf` y `_exportar_word` (líneas 137-167 del archivo original)
por:

```python
    def _obtener_radicado(self) -> str:
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)
        radicado = expediente.radicado
        session.close()
        return radicado

    def _exportar_pdf(self) -> None:
        if not self.boton_exportar_pdf.isEnabled():
            return
        nombre_sugerido = f"Liquidacion_{_sanitizar_nombre_archivo(self._obtener_radicado())}.pdf"

        ruta, _filtro = QFileDialog.getSaveFileName(
            self, "Exportar a PDF", nombre_sugerido, "PDF (*.pdf)"
        )
        if not ruta:
            return

        self._iniciar_exportacion(_generar_pdf_en_hilo_de_fondo, ruta, "PDF")

    def _exportar_word(self) -> None:
        if not self.boton_exportar_word.isEnabled():
            return
        nombre_sugerido = f"Liquidacion_{_sanitizar_nombre_archivo(self._obtener_radicado())}.docx"

        ruta, _filtro = QFileDialog.getSaveFileName(
            self, "Exportar a Word", nombre_sugerido, "Word (*.docx)"
        )
        if not ruta:
            return

        self._iniciar_exportacion(_generar_word_en_hilo_de_fondo, ruta, "Word")

    def _iniciar_exportacion(self, funcion_generadora, ruta: str, etiqueta: str) -> None:
        self.boton_exportar_pdf.setEnabled(False)
        self.boton_exportar_word.setEnabled(False)

        self._dialogo_progreso_exportar = QProgressDialog(
            f"Exportando a {etiqueta}...", None, 0, 0, self
        )
        self._dialogo_progreso_exportar.setWindowModality(Qt.WindowModality.WindowModal)
        self._dialogo_progreso_exportar.setCancelButton(None)
        self._dialogo_progreso_exportar.setMinimumDuration(0)
        self._dialogo_progreso_exportar.show()

        self._tarea_exportar = TareaEnHilo(
            funcion_generadora, self._resultado, self._expediente_id, ruta
        )
        self._tarea_exportar.senales.completada.connect(
            lambda ruta_generada: self._on_exportar_completado(ruta_generada, etiqueta)
        )
        self._tarea_exportar.senales.fallo.connect(self._on_exportar_fallo)
        QThreadPool.globalInstance().start(self._tarea_exportar)

    def _finalizar_exportacion_en_curso(self) -> None:
        self._dialogo_progreso_exportar.close()
        self.boton_exportar_pdf.setEnabled(True)
        self.boton_exportar_word.setEnabled(True)

    def _on_exportar_completado(self, ruta: str, etiqueta: str) -> None:
        self._finalizar_exportacion_en_curso()
        QMessageBox.information(self, "Exportación completa", f"{etiqueta} guardado en: {ruta}")
        self.exportacion_finalizada.emit()

    def _on_exportar_fallo(self, error: Exception) -> None:
        self._finalizar_exportacion_en_curso()
        QMessageBox.critical(self, "No se pudo exportar", str(error))
        self.exportacion_finalizada.emit()
```

- [ ] **Step 6: Correr el test del Step 1 para verificar que pasa**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_liquidaciones.py -k "test_exportar_pdf_crea_archivo_en_la_ruta_elegida or test_exportar_pdf_deshabilita_ambos_botones_mientras_esta_en_curso or test_exportar_pdf_ignora_llamada_concurrente_mientras_hay_una_en_curso" -v`
Expected: 3 passed.

- [ ] **Step 7: Adaptar los 3 call sites restantes que sí inician una exportación real**

`test_muestra_una_fila_por_item_de_liquidacion`, `test_muestra_columna_de_indexacion_sanciones`,
`test_muestra_los_totales`, `test_muestra_bloque_de_renta_liquida_cuando_esta_presente` y
`test_oculta_bloque_de_renta_liquida_cuando_no_esta_presente` **no** llaman a `_exportar_pdf`ni a
`_exportar_word` — no se tocan.

`test_exportar_word_crea_archivo_en_la_ruta_elegida` pasa de:

```python
    view._exportar_word()

    assert ruta_destino.exists()
    assert ruta_destino.stat().st_size > 0
```

a:

```python
    with qtbot.waitSignal(view.exportacion_finalizada, timeout=5000):
        view._exportar_word()

    assert ruta_destino.exists()
    assert ruta_destino.stat().st_size > 0
```

`test_exportar_pdf_con_error_muestra_mensaje_critico` pasa de:

```python
    view._exportar_pdf()

    assert len(errores) == 1
    assert errores[0][0] == "No se pudo exportar"
```

a:

```python
    with qtbot.waitSignal(view.exportacion_finalizada, timeout=5000):
        view._exportar_pdf()

    assert len(errores) == 1
    assert errores[0][0] == "No se pudo exportar"
```

`test_exportar_pdf_cancelado_no_crea_archivo` **no** se toca: el diálogo devuelve `("", "")`, así
que `_exportar_pdf()` retorna antes de disparar ninguna tarea en segundo plano (ninguna señal se
va a emitir, `qtbot.waitSignal` colgaría esperando algo que nunca ocurre) — permanece como una
llamada síncrona directa:

```python
    view._exportar_pdf()

    assert list(tmp_path.iterdir()) == []
```

- [ ] **Step 8: Corregir el pool de conexiones SQLite en memoria (`_expediente_para_exportar`)**

Agregar el import al inicio del archivo, después de `from sqlalchemy import create_engine`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
```

En `_expediente_para_exportar`, cambiar:

```python
    engine = create_engine("sqlite:///:memory:")
```

a:

```python
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
```

(esta es la única aparición de `create_engine("sqlite:///:memory:")` en este archivo — no hace
falta `replace_all`).

- [ ] **Step 9: Correr toda la suite del archivo para verificar que pasa**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest tests/views/test_liquidaciones.py -v`
Expected: todos PASS (los 9 tests originales + los 2 nuevos del Step 3 = 11).

- [ ] **Step 10: Ruff**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check app/views/liquidaciones.py tests/views/test_liquidaciones.py`
Expected: igual que en la Task 2 Step 10, **estos dos archivos ya tenían deuda de lint previa a
este sprint** (confirmado al escribir este plan: `app/views/liquidaciones.py` tenía 7 `E501`
preexistentes en líneas que este task reemplaza por completo — 40, 95, 138, 141, 146, 154, 157,
162 del archivo original — y `tests/views/test_liquidaciones.py` tenía 3 `E501` preexistentes,
incluida la línea 15 de `_resultado_de_prueba()` que este task no toca). El criterio de
aceptación es el mismo: ninguna línea nueva o modificada por los Steps 4, 5, 7 y 8 de esta tarea
aparece en la salida de `ruff check` — las líneas de `_construir_datos_reporte`/`_exportar_pdf`/
`_exportar_word` que estaban en la lista de errores original desaparecen porque ese código se
reescribió por completo con líneas más cortas.

- [ ] **Step 11: Commit**

```bash
git add app/views/liquidaciones.py tests/views/test_liquidaciones.py
git commit -m "$(cat <<'EOF'
feat(sprint26): ejecutar exportacion PDF/Word en QThreadPool para no congelar la UI

EOF
)"
```

---

### Task 4: Suite completa, ruff y cierre técnico del sprint (sin tocar `Pendientes.md`)

**Files:** ninguno nuevo — solo verificación.

- [ ] **Step 1: Correr toda la suite del proyecto**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -v`
Expected: todos los tests en verde (los ~9 nuevos de este plan — 4 de Task 1, 3 de Task 2, 2 de
Task 3 — más los existentes, sin cambios de comportamiento en los casos ya cubiertos).

- [ ] **Step 2: Ruff sobre todo el repo**

Run: `"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check .`
Expected: **el repo entero ya tenía 412 errores de lint preexistentes antes de este plan**
(confirmado al escribir este plan, corriendo `ruff check .` sobre el estado de partida del
worktree — sobre todo `E501` de líneas largas, deuda documentada como pendiente de limpieza
técnica en sprints paralelos como el 27/28, no algo que Sprint 26 deba resolver). No usar "cero
errores totales" como criterio. En vez de eso:
1. Guardar la salida de este comando en un archivo temporal, ej.
   `... ruff check . > /tmp/ruff_final.txt` (o el equivalente en el scratchpad de la sesión).
2. Correr `git stash` para volver momentáneamente al estado previo a este plan, correr
   `ruff check . > /tmp/ruff_baseline.txt`, y `git stash pop` para restaurar los cambios.
3. Con `diff /tmp/ruff_baseline.txt /tmp/ruff_final.txt`, confirmar que las únicas diferencias
   son líneas que **desaparecen** (por el código reescrito en `app/views/liquidaciones.py`
   durante la Task 3) — no debe haber ninguna línea **nueva** en el diff, y ninguna línea nueva
   ni del diff debe mencionar `app/views/concurrency.py`, `app/views/expediente_detalle.py`,
   `app/views/liquidaciones.py`, `tests/views/test_concurrency.py`,
   `tests/views/test_expediente_detalle.py` o `tests/views/test_liquidaciones.py` como archivo
   con un error que no existía antes.

- [ ] **Step 3: Verificación manual de que no quedó ningún placeholder de smoke test automatizable**

Este sprint pide explícitamente un "smoke test manual: liquidar un expediente con muchas
obligaciones/años de mora sin que la ventana deje de responder (se puede mover/redimensionar
mientras liquida)". Ese paso requiere una sesión interactiva con una ventana real en pantalla —
no se automatiza en este plan ni se ejecuta en este task (documentar esto tal cual en el reporte
final de la sesión que ejecute este plan, como pendiente explícito para quien haga la revisión
manual antes de fusionar).

- [ ] **Step 4 — NO EJECUTAR: recordatorio explícito**

**No editar `Pendientes.md`** (ni el índice, ni la sección del Sprint 26, ni ningún marcador
`✅ Completado`) — el orquestador humano actualiza ese archivo centralmente una vez fusionados
los 5 sprints paralelos. Este plan termina en el Step 2 de este Task; no hay un commit de cierre
de `Pendientes.md` en este plan (a diferencia del patrón usado en planes de sprints anteriores
como el Sprint 24).

**No editar `README.md` ni `docs/GUIA_USUARIO.md`**: Sprint 26 es un cambio de comportamiento
interno (responsividad de la UI durante liquidar/exportar), no agrega ni cambia ningún módulo o
flujo visible que esos documentos describan funcionalmente — no hay nada fácticamente incorrecto
en ellos que este sprint provoque. Si al ejecutar este plan se encuentra algo que sí quedó
desactualizado por este cambio específico, corregirlo con un commit `docs:` separado y angosto,
documentando por qué en el mensaje de commit.

---

## Self-review notes

- **Cobertura del spec:** `QRunnable`/`QThreadPool` reutilizable (Task 1); `estrategia.liquidar()`
  fuera del hilo de UI (Task 2); exportación PDF/Word fuera del hilo de UI (Task 3);
  `QProgressDialog` indeterminado en ambos flujos (Tasks 2 y 3, `QProgressDialog(..., 0, 0, ...)`);
  botón deshabilitado durante la operación + guard contra doble ejecución concurrente (Tasks 2 y
  3, con test dedicado para cada uno); `get_session()` abierta y cerrada dentro del hilo de fondo,
  nunca compartida entre hilos (Tasks 2 y 3, funciones `_liquidar_en_hilo_de_fondo` /
  `_generar_pdf_en_hilo_de_fondo` / `_generar_word_en_hilo_de_fondo`); motor interno sin
  paralelizar (ningún task toca `app/engine/liquidation/engine.py` ni
  `app/engine/tax/moratory_interest.py`); suite completa con pytest-qt cubriendo el nuevo flujo
  (Task 4).
- **Riesgo de SQLite en memoria entre hilos:** identificado explícitamente en el "Contexto
  compartido" y corregido en el Step 8 de Tasks 2 y 3 con `StaticPool` +
  `check_same_thread=False` — sin este fix, `test_liquidar_registra_auditoria_y_refresca_historial`
  (Task 2) y los tests de exportación (Task 3) fallarían de forma confusa (datos vacíos), no por
  un error de threading obvio.
- **Sin placeholders:** cada paso trae el código completo a pegar; los 3 call-sites "mecánicos"
  de Task 2 Step 7 traen los 3 textos literales exactos a buscar/reemplazar, no una descripción
  genérica.
- **Consistencia de tipos:** `TareaEnHilo`/`SenalesTareaEnHilo` se definen una sola vez en Task 1
  y se reutilizan verbatim (mismo import `from app.views.concurrency import TareaEnHilo`, misma
  API `senales.completada`/`senales.fallo`) en Tasks 2 y 3. Las señales `liquidacion_finalizada`
  (Task 2) y `exportacion_finalizada` (Task 3) siguen el mismo patrón: se emiten al final de
  **ambos** slots (`_on_..._completado` y `_on_..._fallo`), así que `qtbot.waitSignal` sirve para
  esperar el fin de la operación sin importar si tuvo éxito o falló.
