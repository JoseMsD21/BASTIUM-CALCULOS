# Sprint 25 — Rendimiento del motor de tasas, índices e historial Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar los 4 cuellos de botella señalados en la auditoría de rendimiento de 2026-07-21 (Pendientes.md, Sprint 25) sin cambiar ningún resultado numérico de liquidación: scan lineal de `MemoryRateProvider`, reconsulta de `get_parametro` (nueva sesión SQLAlchemy) dentro de loops por obligación/cuota, ausencia de índices en columnas de filtrado frecuente, y carga sin paginar de la tabla de expedientes (esta última solo se evalúa, no se implementa — ver "Alcance explícitamente excluido").

**Arquitectura:**
1. `MemoryRateProvider.get_rate`/`get_rate_source` pasan de scan O(n) a búsqueda binaria (`bisect`) sobre la lista de periodos, que ya se mantiene ordenada por `start_date`.
2. `parametro_service.get_parametro` gana una cache opcional, activada por un `ContextVar` que un nuevo context manager `cache_de_liquidacion()` prende/apaga. La cache vive solo por la duración de una liquidación (nunca persiste entre llamadas), así que un `agregar_valor` hecho desde la GUI entre dos liquidaciones nunca puede servir un valor desactualizado. Como `contextlib.contextmanager` hereda de `ContextDecorator`, el mismo objeto sirve como decorador (`@cache_de_liquidacion()`) — cada llamada decorada abre su propio bloque nuevo.
3. Los 6 métodos `liquidar()` concretos de `AreaStrategy` (uno por área del derecho) se decoran con `@cache_de_liquidacion()`, cubriendo de forma transparente todo el árbol de llamadas de una liquidación (incluye `historical_index.get_smlmv_for_year`/`get_ipc_for_date`, `moratory_interest`, `sanciones`, `seguridad_social`, etc. — todos ya pasan por `get_parametro`).
4. 4 columnas de filtrado frecuente ganan `index=True` en `database/models.py` (aplica solo a bases de datos nuevas) más un script de migración de esquema idempotente para `bastium.db` (aplica a la base existente), mismo patrón que `scripts/migrate_costas_tipo_proceso.py`.

**Tech Stack:** Python 3, SQLAlchemy 2.0 (`Mapped`/`mapped_column`), SQLite, pytest, `bisect` (stdlib), `contextvars`/`contextlib` (stdlib).

---

## Alcance explícitamente excluido

- No se cambia el diseño en memoria de `MemoryRateProvider` a una base de datos indexada — solo se optimiza el lookup dentro del diseño actual (instrucción explícita de Pendientes.md).
- No se implementa paginación en `app/views/expedientes.py`. El volumen actual (un solo abogado) no lo justifica; Pendientes.md lo enmarca como "evaluar... si el volumen lo justifica", no como entregable. Queda documentado aquí como decisión consciente, no como olvido.
- La cache de `get_parametro` deduplica por `(clave, fecha)` exacto, no por rango de vigencia. Para `HONORARIOS_TOTAL_PCT` (hallazgo 2), esto solo dedupliza cuando dos obligaciones comparten el mismo `fecha_origen` exacto — un rediseño que cachee por rango de vigencia cambiaría la superficie de riesgo de la resolución `ABIERTO` (ver Task 2) y no es necesario para cumplir "no cambia ningún resultado numérico". Para `IPC_INDICE_ACUMULADO`/`SMLMV` (hallazgo 3), el beneficio es completo porque la clave de resolución ya es por año, no por fecha exacta (ver Task 2, nota de diseño).

## File Structure

- `app/engine/interest/provider.py` — reescribe `MemoryRateProvider` con búsqueda binaria (Task 1).
- `tests/engine/test_rate_provider.py` — casos nuevos para huecos entre periodos y fronteras exactas (Task 1).
- `app/services/parametro_service.py` — agrega `cache_de_liquidacion()` y modifica `get_parametro` (Task 2).
- `tests/services/test_parametro_service.py` — casos nuevos de cache activa/inactiva (Task 2).
- `app/services/area_strategy.py` — decora los 6 `liquidar()` concretos (Task 3).
- `tests/services/test_area_strategy.py` — casos nuevos que cuentan consultas a `_resolver_fila` (Task 3).
- `database/models.py` — `index=True` en 4 columnas (Task 4).
- `scripts/migrate_add_indices_rendimiento.py` — migración de esquema nueva (Task 4).
- `tests/scripts/test_migrate_add_indices_rendimiento.py` — nuevo (Task 4).
- `tests/database/test_models.py` — caso nuevo que verifica los índices vía `sqlalchemy.inspect` (Task 4).
- `scripts/benchmark_motor_rendimiento.py` — script de benchmark manual nuevo (Task 5).
- `Pendientes.md` — cierre del sprint con los números medidos (Task 6).

---

### Task 1: `MemoryRateProvider` — búsqueda binaria en vez de scan lineal

**Files:**
- Modify: `app/engine/interest/provider.py`
- Test: `tests/engine/test_rate_provider.py`

**Contexto:** `_accrue_time_passage` (`app/engine/liquidation/engine.py:106-128`) llama a `rate_provider.get_rate(current_day)` una vez por cada día entre el último evento y la fecha objetivo (`while current_day <= target_date: ...`). Para una obligación con 28 años de mora eso son ~10.000 llamadas, cada una escaneando la lista completa de periodos. `add_rate_period` ya mantiene `self._periods` ordenada por `start_date` (línea `self._periods.sort(key=lambda p: p.start_date)`), así que basta con indexar esa invariante.

- [x] **Step 1: Agregar tests de frontera que ya deben pasar con el scan lineal actual (caracterización antes del refactor)**

- [x] **Step 2: Correr los tests para confirmar que pasan con la implementación actual (línea base antes del refactor)**

- [x] **Step 3: Reescribir `provider.py` con búsqueda binaria**

- [x] **Step 4: Correr los tests de nuevo para confirmar que el refactor no cambió ningún resultado**

- [x] **Step 5: Correr la suite completa del motor de liquidación (el consumidor real de `MemoryRateProvider`)**

- [x] **Step 6: Commit**

Implemented, spec-reviewed, and code-quality-reviewed (Approved) as commit `e3d3461` — "perf(sprint25): MemoryRateProvider usa busqueda binaria en vez de scan lineal".

---

### Task 2: Cache de `get_parametro` con alcance de una sola liquidación

**Files:**
- Modify: `app/services/parametro_service.py`
- Test: `tests/services/test_parametro_service.py`

**Contexto:** `get_parametro` (línea 247) llama a `_resolver_fila`, que abre y cierra una sesión SQLAlchemy nueva en cada invocación (`session_module.get_session()` ... `session.close()`). Se llama repetidamente con la misma `(clave, fecha)` dentro de loops por obligación/cuota (hallazgos 2 y 3): `HonorariosStrategy` la llama una vez por obligación con `HONORARIOS_TOTAL_PCT`, y `historical_index.get_ipc_for_date`/`get_smlmv_for_year` la llaman una vez por cuota mensual con una clave resuelta por *año* (`date(fecha.year, 1, 1)`) -- para una obligación RECURRENTE de varios años, todas las cuotas del mismo año colapsan a la misma clave de cache, así que el ahorro es completo por año, no solo por fecha exacta.

La cache debe vivir *solo* mientras dura una liquidación: la tabla `parametros_legales` es append-only y editable en caliente desde la GUI (`app/views/configuracion.py`) mientras la aplicación sigue corriendo -- una cache de proceso (sin expiración) podría servir un valor desactualizado si el usuario agrega un parámetro nuevo entre dos liquidaciones sin reiniciar la app. Por eso se usa un `ContextVar` que solo está "activo" dentro de un bloque `with cache_de_liquidacion():` (o su uso como decorador), nunca por defecto.

- [ ] **Step 1: Escribir los tests de la cache**

Agregar al final de `tests/services/test_parametro_service.py`:

```python
def test_cache_de_liquidacion_evita_reconsultar_la_misma_clave_y_fecha(monkeypatch):
    from app.services import parametro_service
    from app.services.parametro_service import cache_de_liquidacion, get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    with cache_de_liquidacion():
        primero = get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))
        segundo = get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))

    assert primero == segundo == Decimal("1.5")
    assert len(llamadas) == 1


def test_cache_de_liquidacion_no_persiste_entre_bloques(monkeypatch):
    from app.services import parametro_service
    from app.services.parametro_service import cache_de_liquidacion, get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    with cache_de_liquidacion():
        get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))
    with cache_de_liquidacion():
        get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))

    assert len(llamadas) == 2


def test_get_parametro_sin_cache_activa_sigue_consultando_cada_vez(monkeypatch):
    from app.services import parametro_service
    from app.services.parametro_service import get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))
    get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))

    assert len(llamadas) == 2


def test_cache_de_liquidacion_usada_como_decorador_crea_bloque_nuevo_por_llamada(monkeypatch):
    from app.services import parametro_service
    from app.services.parametro_service import cache_de_liquidacion, get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    @cache_de_liquidacion()
    def _dos_consultas_iguales():
        get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))
        get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))

    _dos_consultas_iguales()
    _dos_consultas_iguales()

    assert len(llamadas) == 2  # 1 por invocacion de _dos_consultas_iguales, no 4
```

- [ ] **Step 2: Correr los tests para confirmar que fallan (la cache todavía no existe)**

Run: `python -m pytest tests/services/test_parametro_service.py -v -k cache_de_liquidacion`
Expected: FAIL con `ImportError: cannot import name 'cache_de_liquidacion'`.

- [ ] **Step 3: Implementar la cache en `parametro_service.py`**

Modificar los imports al inicio del archivo (después de `from __future__ import annotations`):

```python
from __future__ import annotations

import enum
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime
from decimal import Decimal
from typing import NamedTuple

import database.session as session_module
from app.core.exceptions import ParametroNoDisponibleError
from database.models import ParametroLegal
```

Agregar, justo antes de `def get_parametro(...)` (después de `_resolver_fila`):

```python
_cache_liquidacion_activa: ContextVar[dict[tuple[str, date], Decimal] | None] = ContextVar(
    "_cache_liquidacion_activa", default=None
)


@contextmanager
def cache_de_liquidacion():
    """Activa una cache en memoria de get_parametro, valida solo por la
    duracion de este bloque -- nunca persiste entre llamadas, asi que un
    agregar_valor hecho desde la GUI (app/views/configuracion.py) entre dos
    liquidaciones nunca puede servir un valor desactualizado. Evita reabrir
    una sesion SQLAlchemy por cada (clave, fecha) repetido dentro de la misma
    liquidacion (Sprint 25, hallazgos 2/3: HonorariosStrategy consulta
    HONORARIOS_TOTAL_PCT una vez por obligacion; historical_index consulta
    IPC_INDICE_ACUMULADO/SMLMV una vez por cuota mensual, pero la clave de
    resolucion es por año -- todas las cuotas de un mismo año colapsan a la
    misma entrada de cache). contextlib.contextmanager hereda de
    ContextDecorator, asi que este mismo objeto tambien sirve como decorador
    (@cache_de_liquidacion()) -- cada invocacion decorada abre su propio
    bloque nuevo, nunca comparte cache con otra llamada."""
    token = _cache_liquidacion_activa.set({})
    try:
        yield
    finally:
        _cache_liquidacion_activa.reset(token)
```

Reemplazar `def get_parametro`:

```python
def get_parametro(clave: str, fecha: date) -> Decimal:
    """Resuelve el valor de `clave` vigente en `fecha`, segun el modo_resolucion
    declarado en CATALOGO_PARAMETROS (ver Adenda de diseno de la spec). Si hay
    una cache de liquidacion activa (cache_de_liquidacion), reutiliza el valor
    ya resuelto para el mismo (clave, fecha) en vez de abrir una sesion
    SQLAlchemy nueva."""
    cache = _cache_liquidacion_activa.get()
    clave_cache = (clave, fecha)
    if cache is not None and clave_cache in cache:
        return cache[clave_cache]

    fila = _resolver_fila(clave, fecha)
    if fila is None:
        info = _validar_clave(clave)
        raise ParametroNoDisponibleError(
            f"No hay valor configurado para '{info.descripcion}' (clave '{clave}') "
            f"en la fecha {fecha}."
        )
    if cache is not None:
        cache[clave_cache] = fila.valor
    return fila.valor
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `python -m pytest tests/services/test_parametro_service.py -v`
Expected: todos PASS (los existentes siguen igual, los 4 nuevos pasan).

- [ ] **Step 5: Correr la suite completa de parametro_service y sus consumidores directos**

Run: `python -m pytest tests/services/test_parametro_service.py tests/engine/indexation tests/engine/labor tests/engine/temporal -v`
Expected: todos PASS.

- [ ] **Step 6: Commit**

```bash
git add app/services/parametro_service.py tests/services/test_parametro_service.py
git commit -m "perf(sprint25): cache de get_parametro con alcance de una sola liquidacion"
```

---

### Task 3: Activar la cache en los 6 `liquidar()` de `AreaStrategy`

**Files:**
- Modify: `app/services/area_strategy.py:244,376,693,882,951,1070`
- Test: `tests/services/test_area_strategy.py`

**Contexto:** Task 2 dejó la cache lista pero apagada por defecto. Hay que activarla en el único punto donde arranca una liquidación completa (`AreaStrategy.liquidar()`, implementado 6 veces: `CivilFamiliaStrategy`, `ComercialStrategy`, `LaboralStrategy`, `SancionatorioStrategy`, `HonorariosStrategy`, `TributarioStrategy`). Decorar cada método concreto (en vez de tocar el contrato abstracto) es el cambio de menor riesgo: no requiere renombrar el método abstracto ni reindentar el cuerpo de cada implementación.

**Límite conocido (fuera de alcance de este task):** `historical_index.ultimo_anio_disponible` (usada por `get_ipc_interpolado_for_date`) abre su propia sesión SQLAlchemy directamente -- no pasa por `get_parametro`/`_resolver_fila`, así que no se beneficia de la cache de Task 2. Sigue consultándose una vez por cada llamada a `get_ipc_interpolado_for_date` (dos por cuota: `fecha_causacion` y `fecha_corte`). No estaba en los hallazgos de la auditoría original y no se corrige aquí para no ampliar el alcance del sprint; queda como candidato para una auditoría futura.

- [ ] **Step 1: Escribir el test que cuenta consultas reales a la base de datos para `HonorariosStrategy` (hallazgo 2)**

Agregar a `tests/services/test_area_strategy.py`, después de `_obligacion_honorarios` (línea ~1207):

```python
def test_honorarios_liquidar_reutiliza_honorarios_total_pct_entre_obligaciones_con_la_misma_fecha(monkeypatch):
    from app.services import parametro_service

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    obligaciones = [
        _obligacion_honorarios(fecha_origen=date(2026, 1, 1)),
        _obligacion_honorarios(fecha_origen=date(2026, 1, 1)),
        _obligacion_honorarios(fecha_origen=date(2026, 1, 1)),
    ]
    for indice, obligacion in enumerate(obligaciones, start=1):
        obligacion.id = indice

    HonorariosStrategy().liquidar(obligaciones=obligaciones, abonos=[], fecha_corte=date(2026, 1, 1))

    llamadas_honorarios = [l for l in llamadas if l[0] == "HONORARIOS_TOTAL_PCT"]
    assert len(llamadas_honorarios) == 1
```

Agregar también un test que cuenta consultas para `CivilFamiliaStrategy` RECURRENTE con indexación (hallazgo 3), después de `test_civil_familia_recurrente_con_indexacion_cada_cuota_indexa_desde_su_propia_fecha`:

```python
def test_civil_familia_recurrente_con_indexacion_reutiliza_ipc_entre_cuotas_del_mismo_anio(monkeypatch):
    from app.services import parametro_service

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    obligacion = Obligacion(
        id=99, expediente_id=1, tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria", categoria="CHILD_SUPPORT",
        fecha_origen=date(2025, 1, 1), valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"), dia_pago=5,
        fecha_inicio=date(2025, 1, 1), fecha_fin=date(2025, 12, 5),
        aplica_indexacion_ipc=True,
    )

    CivilFamiliaStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 5))

    llamadas_ipc = [l for l in llamadas if l[0] == "IPC_INDICE_ACUMULADO"]
    # 12 cuotas (una por mes de 2025) todas resuelven IPC_INDICE_ACUMULADO
    # contra date(2025,1,1) (fecha_causacion, mismo año) y date(2025,1,1)
    # (fecha_corte 2025-12-05, tambien 2025) -- con la cache activa, ambas
    # colapsan a una sola consulta real en vez de hasta 24.
    assert len(llamadas_ipc) <= 2
```

- [ ] **Step 2: Correr los dos tests nuevos para confirmar que fallan (la cache todavía no está activa en `liquidar()`)**

Run: `python -m pytest tests/services/test_area_strategy.py -v -k "reutiliza"`
Expected: FAIL -- ambos assert de conteo fallan (más de 1/2 llamadas reales).

- [ ] **Step 3: Importar `cache_de_liquidacion` en `area_strategy.py`**

Modificar la línea 48 de `app/services/area_strategy.py`:

```python
from app.services.parametro_service import cache_de_liquidacion, get_parametro
```

- [ ] **Step 4: Decorar los 6 `liquidar()` concretos**

`CivilFamiliaStrategy.liquidar` (`app/services/area_strategy.py:244`):

```python
    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
```

`ComercialStrategy.liquidar` (`app/services/area_strategy.py:376`):

```python
    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
```

`LaboralStrategy.liquidar` (`app/services/area_strategy.py:693`):

```python
    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
```

`SancionatorioStrategy.liquidar` (`app/services/area_strategy.py:882`):

```python
    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
```

`HonorariosStrategy.liquidar` (`app/services/area_strategy.py:951`):

```python
    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
```

`TributarioStrategy.liquidar` (`app/services/area_strategy.py:1070`):

```python
    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
```

(Cada bloque solo agrega la línea `@cache_de_liquidacion()` inmediatamente antes de la firma existente del método -- el cuerpo del método no cambia ni se reindenta.)

- [ ] **Step 5: Correr los tests nuevos para confirmar que pasan**

Run: `python -m pytest tests/services/test_area_strategy.py -v -k "reutiliza"`
Expected: 2 tests PASS.

- [ ] **Step 6: Correr la suite completa de `area_strategy` y de vistas (consumidor GUI real)**

Run: `python -m pytest tests/services/test_area_strategy.py tests/views/test_expediente_detalle.py -v`
Expected: todos PASS, mismos resultados numéricos que antes de este task.

- [ ] **Step 7: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "perf(sprint25): activar la cache de get_parametro en los 6 liquidar() de AreaStrategy"
```

---

### Task 4: Índices en columnas de filtrado frecuente

**Files:**
- Modify: `database/models.py:97,150,182,196`
- Create: `scripts/migrate_add_indices_rendimiento.py`
- Test: `tests/scripts/test_migrate_add_indices_rendimiento.py`
- Modify: `tests/database/test_models.py`

**Contexto:** `Base.metadata.create_all(engine)` (`database/database.py:12`) solo crea tablas que todavía no existen -- nunca agrega una columna ni un índice a una tabla ya creada. Por eso `index=True` en `models.py` alcanza para bases de datos nuevas (tests, instalaciones nuevas) pero hace falta un script de migración de esquema aparte para `bastium.db`, mismo patrón que `scripts/migrate_costas_tipo_proceso.py` (`ALTER TABLE`/`CREATE INDEX`, idempotente vía introspección de `PRAGMA`).

- [ ] **Step 1: Escribir el test del script de migración (todavía no existe el script)**

Crear `tests/scripts/test_migrate_add_indices_rendimiento.py`:

```python
import sqlite3
import tempfile
from pathlib import Path

from scripts.migrate_add_indices_rendimiento import migrar


def _crear_tablas(con):
    con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY, expediente_id INTEGER)")
    con.execute("CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, expediente_id INTEGER)")
    con.execute("CREATE TABLE abonos (id INTEGER PRIMARY KEY, obligacion_id INTEGER)")
    con.execute("CREATE TABLE parametros_legales (id INTEGER PRIMARY KEY, clave TEXT)")
    con.commit()


def test_migrar_crea_los_4_indices_en_bd_sin_ellos():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        con = sqlite3.connect(db_path)
        _crear_tablas(con)
        con.close()

        aplico = migrar(db_path)
        assert aplico is True

        con = sqlite3.connect(db_path)
        nombres = {
            tabla: {fila[1] for fila in con.execute(f"PRAGMA index_list({tabla})")}
            for tabla in ("obligaciones", "audit_logs", "abonos", "parametros_legales")
        }
        con.close()
        assert "ix_obligaciones_expediente_id" in nombres["obligaciones"]
        assert "ix_audit_logs_expediente_id" in nombres["audit_logs"]
        assert "ix_abonos_obligacion_id" in nombres["abonos"]
        assert "ix_parametros_legales_clave" in nombres["parametros_legales"]


def test_migrar_es_idempotente():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        con = sqlite3.connect(db_path)
        _crear_tablas(con)
        con.close()

        migrar(db_path)
        aplico_segunda_vez = migrar(db_path)
        assert aplico_segunda_vez is False
```

- [ ] **Step 2: Correr el test para confirmar que falla (el script todavía no existe)**

Run: `python -m pytest tests/scripts/test_migrate_add_indices_rendimiento.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'scripts.migrate_add_indices_rendimiento'`.

- [ ] **Step 3: Crear el script de migración**

Crear `scripts/migrate_add_indices_rendimiento.py`:

```python
"""Migracion de esquema (Sprint 25, hallazgo 4): agrega 4 indices a columnas
de filtrado frecuente de una bastium.db ya existente --
Base.metadata.create_all() (database/database.py) solo crea tablas que
todavia no existen, nunca agrega un indice a una tabla ya creada. Idempotente
via PRAGMA index_list, mismo patron que scripts/migrate_costas_tipo_proceso.py
(que usa PRAGMA table_info para columnas)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_INDICES = [
    ("ix_obligaciones_expediente_id", "obligaciones", "expediente_id"),
    ("ix_audit_logs_expediente_id", "audit_logs", "expediente_id"),
    ("ix_abonos_obligacion_id", "abonos", "obligacion_id"),
    ("ix_parametros_legales_clave", "parametros_legales", "clave"),
]


def migrar(db_path: Path = DB_PATH) -> bool:
    """Crea los 4 indices si no existen. Retorna True si creo alguno, False
    si los 4 ya existian."""
    con = sqlite3.connect(db_path)
    try:
        aplico = False
        for nombre_indice, tabla, columna in _INDICES:
            indices_existentes = {fila[1] for fila in con.execute(f"PRAGMA index_list({tabla})")}
            if nombre_indice in indices_existentes:
                continue
            con.execute(f"CREATE INDEX {nombre_indice} ON {tabla}({columna})")
            aplico = True
        con.commit()
        return aplico
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Indices de rendimiento agregados (obligaciones, audit_logs, abonos, parametros_legales).")
    else:
        print("Los 4 indices ya existian, no se hizo nada.")
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `python -m pytest tests/scripts/test_migrate_add_indices_rendimiento.py -v`
Expected: 2 tests PASS.

- [ ] **Step 5: Agregar `index=True` en `database/models.py`**

Línea 97 (`Obligacion.expediente_id`):

```python
    expediente_id: Mapped[int] = mapped_column(ForeignKey("expedientes.id"), index=True)
```

Línea 150 (`Abono.obligacion_id`):

```python
    obligacion_id: Mapped[int] = mapped_column(ForeignKey("obligaciones.id"), index=True)
```

Línea 182 (`AuditLog.expediente_id`):

```python
    expediente_id: Mapped[int] = mapped_column(ForeignKey("expedientes.id"), index=True)
```

Línea 196 (`ParametroLegal.clave`):

```python
    clave: Mapped[str] = mapped_column(String(100), index=True)
```

- [ ] **Step 6: Escribir el test que verifica los índices en `database/models.py`**

Agregar a `tests/database/test_models.py` (junto al import de `pytest`, agregar `from sqlalchemy import inspect`):

```python
def test_columnas_de_filtrado_frecuente_tienen_indice(session):
    inspector = inspect(session.get_bind())
    indices_obligaciones = {
        columna for idx in inspector.get_indexes("obligaciones") for columna in idx["column_names"]
    }
    indices_audit_logs = {
        columna for idx in inspector.get_indexes("audit_logs") for columna in idx["column_names"]
    }
    indices_abonos = {
        columna for idx in inspector.get_indexes("abonos") for columna in idx["column_names"]
    }
    indices_parametros = {
        columna for idx in inspector.get_indexes("parametros_legales") for columna in idx["column_names"]
    }

    assert "expediente_id" in indices_obligaciones
    assert "expediente_id" in indices_audit_logs
    assert "obligacion_id" in indices_abonos
    assert "clave" in indices_parametros
```

- [ ] **Step 7: Correr toda la suite de base de datos**

Run: `python -m pytest tests/database/test_models.py tests/scripts/test_migrate_add_indices_rendimiento.py -v`
Expected: todos PASS.

- [ ] **Step 8: Commit**

```bash
git add database/models.py scripts/migrate_add_indices_rendimiento.py tests/scripts/test_migrate_add_indices_rendimiento.py tests/database/test_models.py
git commit -m "perf(sprint25): indices en columnas de filtrado frecuente (obligaciones, audit_logs, abonos, parametros_legales)"
```

---

### Task 5: Benchmark manual (Definición de Hecho)

**Files:**
- Create: `scripts/benchmark_motor_rendimiento.py`

**Contexto:** La Definición de Hecho del sprint pide "Benchmark simple (test o script) que compare tiempo de liquidación antes/después en un expediente con muchos años de mora". Los tiempos de reloj son ruidosos para un umbral pass/fail automatizado en CI, así que este es un script que se corre a mano -- una vez en el commit *antes* de Task 1 (línea base) y otra vez después de Task 3 (con las tres optimizaciones de código ya aplicadas), y los dos números impresos se registran en Task 6.

- [ ] **Step 1: Crear el script de benchmark**

Crear `scripts/benchmark_motor_rendimiento.py`:

```python
"""Benchmark manual (Sprint 25, Definicion de Hecho): mide el tiempo de una
liquidacion con muchos anios de mora, para comparar antes/despues de los
hallazgos 1 y 3 del audit de rendimiento (scan lineal de MemoryRateProvider,
reconsulta de get_parametro por cuota). No es una prueba automatizada -- se
corre a mano con `python scripts/benchmark_motor_rendimiento.py` antes y
despues de aplicar los cambios de este sprint, y los dos numeros impresos se
registran en Pendientes.md al cerrar el sprint (ver Task 6 del plan)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.services.area_strategy import CivilFamiliaStrategy
from database.models import Base, Obligacion, ParametroLegal, TipoObligacion


def _preparar_db_en_memoria() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_module.SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_module.get_session()
    for anio in range(1997, 2027):
        session.add(ParametroLegal(
            clave="IPC_INDICE_ACUMULADO", valor=Decimal("100") * Decimal("1.05") ** (anio - 1997),
            vigente_desde=date(anio, 1, 1), vigente_hasta=None,
            usuario="benchmark", motivo=None, creado_en=datetime.now(),
        ))
    session.commit()
    session.close()


def _benchmark_mora_larga() -> float:
    """Hallazgo 1: MemoryRateProvider.get_rate escaneado dia a dia durante 29
    anios de mora (1997-01-01 a 2026-12-31, ~10950 llamadas)."""
    obligacion = Obligacion(
        id=1, expediente_id=1, tipo=TipoObligacion.PUNTUAL,
        concepto="Benchmark mora larga", categoria="DANO_EMERGENTE",
        fecha_origen=date(1997, 1, 1), valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    inicio = time.perf_counter()
    CivilFamiliaStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 12, 31))
    return time.perf_counter() - inicio


def _benchmark_recurrente_con_indexacion() -> float:
    """Hallazgos 2/3: get_ipc_interpolado_for_date consultado una vez por
    cuota mensual (348 cuotas = 29 anios x 12 meses)."""
    obligacion = Obligacion(
        id=2, expediente_id=1, tipo=TipoObligacion.RECURRENTE,
        concepto="Benchmark cuotas con indexacion", categoria="CHILD_SUPPORT",
        fecha_origen=date(1997, 1, 1), valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"), dia_pago=5,
        fecha_inicio=date(1997, 1, 1), fecha_fin=date(2025, 12, 5),
        aplica_indexacion_ipc=True,
    )
    inicio = time.perf_counter()
    CivilFamiliaStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 5))
    return time.perf_counter() - inicio


if __name__ == "__main__":
    _preparar_db_en_memoria()
    tiempo_mora = _benchmark_mora_larga()
    tiempo_recurrente = _benchmark_recurrente_con_indexacion()
    print(f"Mora larga (29 anios, ~10950 dias): {tiempo_mora:.3f}s")
    print(f"Recurrente con indexacion (348 cuotas): {tiempo_recurrente:.3f}s")
```

- [ ] **Step 2: Correr el benchmark para confirmar que ejecuta sin errores**

Run: `python scripts/benchmark_motor_rendimiento.py`
Expected: imprime las dos líneas con tiempos en segundos, sin traceback. Guardar estos dos números -- son la línea base *después* de Tasks 1-4 (ya no hay línea base "antes" disponible en este punto del plan salvo que se corra este mismo script contra el commit anterior a Task 1, con `git stash`/`git worktree` si se quiere el número exacto de comparación).

- [ ] **Step 3: Commit**

```bash
git add scripts/benchmark_motor_rendimiento.py
git commit -m "perf(sprint25): agregar benchmark manual de liquidacion con muchos años de mora"
```

---

### Task 6: Aplicar la migración a `bastium.db`, correr la suite completa y cerrar el sprint

**Files:**
- Modify: `Pendientes.md` (sección Sprint 25)

- [ ] **Step 1: Aplicar la migración de índices a la base de datos real**

Run: `python scripts/migrate_add_indices_rendimiento.py`
Expected: imprime `"Indices de rendimiento agregados..."` (o `"...ya existian..."` si ya se habían aplicado). Confirmar con:

Run: `python -c "import sqlite3; con = sqlite3.connect('bastium.db'); [print(t, [f[1] for f in con.execute(f'PRAGMA index_list({t})')]) for t in ('obligaciones','audit_logs','abonos','parametros_legales')]"`
Expected: los 4 nombres `ix_*` de la Task 4 aparecen en la salida.

- [ ] **Step 2: Correr la suite completa del proyecto**

Run: `python -m pytest`
Expected: todos los tests PASS, ningún cambio de resultado numérico respecto al estado antes de este sprint.

- [ ] **Step 3: Correr el benchmark manual una vez más contra el estado final, para confirmar el número que se registrará en Pendientes.md**

Run: `python scripts/benchmark_motor_rendimiento.py`
Expected: imprime los dos tiempos finales (post Tasks 1-5).

- [ ] **Step 4: Cerrar el sprint en `Pendientes.md`**

Editar la sección `## Sprint 25 — Rendimiento del motor de tasas, índices e historial` (líneas 2132-2178 al momento de escribir este plan) agregando, justo antes de la línea `---` de cierre de sección, una subsección de cierre con los números reales obtenidos en el Step 3 (formato consistente con el cierre de sprints anteriores, ej. el commit `d64a554` que cerró los Sprints 23/24):

```markdown
**Cierre (fecha real de la implementación):**
- `MemoryRateProvider.get_rate`/`get_rate_source`: búsqueda binaria (`bisect`) sobre la lista de periodos, ya ordenada por `start_date`.
- `get_parametro`: cache con alcance de una sola liquidación (`cache_de_liquidacion`, `ContextVar`), activada en los 6 `liquidar()` de `AreaStrategy`. Nunca persiste entre liquidaciones -- no hay riesgo de servir un valor desactualizado tras un `agregar_valor` desde la GUI.
- Índices agregados: `ix_obligaciones_expediente_id`, `ix_audit_logs_expediente_id`, `ix_abonos_obligacion_id`, `ix_parametros_legales_clave`. Aplicados a `bastium.db` con `scripts/migrate_add_indices_rendimiento.py` (idempotente).
- Paginación de `expedientes.py`: evaluada y descartada por ahora -- el volumen actual no la justifica (ver "Alcance explícitamente excluido" del plan de implementación).
- Benchmark (`scripts/benchmark_motor_rendimiento.py`, obligación con 29 años de mora / 348 cuotas con indexación): [rellenar con los tiempos reales del Step 3].
- Suite completa en verde, sin cambios de resultado numérico.
```

- [ ] **Step 5: Commit**

```bash
git add bastium.db Pendientes.md
git commit -m "docs(sprint25): cerrar sprint de rendimiento del motor con los indices aplicados a bastium.db"
```
