# Sprint 8 — Conectar indexación IPC al área Civil/Familia — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Conectar `IPCIndexation` (ya implementado) a `CivilFamiliaStrategy`, para que las obligaciones
que el abogado marque explícitamente generen eventos de indexación real usando las series históricas de
IPC ya cargadas (Sprint 5), en vez de no indexar nada.

**Architecture:** `LiquidationCore` ya sabe procesar eventos `event_type="INDEXATION"` de forma genérica
(no requiere cambios). El trabajo es: (1) una nueva función de consulta en `historical_index.py` que
interpola el IPC a cualquier fecha a partir de los índices de cierre de año ya cargados, (2) un nuevo
campo `Obligacion.aplica_indexacion_ipc` para que el opt-in sea por obligación, y (3) que
`CivilFamiliaStrategy` emita un evento `INDEXATION` hermano de cada evento de capital cuando ese campo
esté activo — una vez por obligación PUNTUAL, una vez por cuota en RECURRENTE (tracto sucesivo).

**Tech Stack:** Python, SQLAlchemy (SQLite), pytest, PySide6/pytest-qt para el checkbox de la GUI.

**Nota operativa sobre git:** antes de cualquier paso "Commit" de este plan, correr `git status`. Si
aparece "You have unmerged paths" (hay un merge de otra sesión/worktree en curso), **no comitear** —
dejar los cambios en el working tree y avisar al usuario en vez de forzar una resolución del merge ajeno.

---

### Task 1: `get_ipc_interpolado_for_date` en `historical_index.py`

**Files:**
- Modify: `app/engine/indexation/historical_index.py`
- Test: `tests/engine/test_historical_index.py`

El PDF (pág. 22) pide interpolar el IPC cuando la fecha no coincide con un cierre de mes certificado,
pero la fuente solo trae variación *anual* (ver `get_ipc_for_date`, que solo retorna el índice de
31-dic). Esta función interpola linealmente entre los dos índices de cierre de año que rodean la fecha,
con la fórmula del PDF `Vo = (t1×V2 + t2×V1)/(t1+t2)`, y usa el índice del último año disponible como
aproximación para fechas posteriores (decisión de diseño, ver
`docs/superpowers/specs/2026-07-19-sprint8-indexacion-ipc-civil-familia-design.md`, decisión 3).

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/engine/test_historical_index.py`:

```python
from app.engine.indexation.historical_index import get_ipc_interpolado_for_date


def test_ipc_interpolado_en_cierre_de_anio_coincide_con_get_ipc_for_date():
    assert get_ipc_interpolado_for_date(date(2025, 12, 31)) == get_ipc_for_date(date(2025, 12, 31))


def test_ipc_interpolado_en_2024_07_01_es_promedio_ponderado_por_dias():
    v_2023 = get_ipc_for_date(date(2023, 12, 31))
    v_2024 = get_ipc_for_date(date(2024, 12, 31))
    # 2024 es bisiesto (366 dias): del 31-dic-2023 al 1-jul-2024 hay 183 dias (t1),
    # del 1-jul-2024 al 31-dic-2024 hay otros 183 dias (t2).
    t1 = Decimal(183)
    t2 = Decimal(183)
    esperado = (t1 * v_2024 + t2 * v_2023) / (t1 + t2)
    assert get_ipc_interpolado_for_date(date(2024, 7, 1)) == esperado


def test_ipc_interpolado_fecha_posterior_al_ultimo_anio_usa_el_ultimo_indice_disponible():
    # La serie no tiene 2026 (la fuente del PDF no lo trae). Cualquier fecha de 2026
    # en adelante usa el indice de 2025 como aproximacion (ver design doc, decision 3).
    assert get_ipc_interpolado_for_date(date(2026, 7, 19)) == get_ipc_for_date(date(2025, 12, 31))
    assert get_ipc_interpolado_for_date(date(2030, 1, 1)) == get_ipc_for_date(date(2025, 12, 31))


def test_ipc_interpolado_fecha_anterior_a_1967_lanza_value_error():
    with pytest.raises(ValueError):
        get_ipc_interpolado_for_date(date(1966, 12, 31))


def test_ipc_interpolado_primer_anio_usa_ancla_implicita_de_100():
    # 1967 es el primer año de la serie; el año anterior (1966) no está en el
    # diccionario, así que v1 debe ser el ancla implícita 100 (misma convención
    # que _construir_indice_ipc_acumulado, ver docstring del módulo).
    v_1967 = get_ipc_for_date(date(1967, 12, 31))
    t1 = Decimal(181)  # 31-dic-1966 -> 30-jun-1967
    t2 = Decimal(184)  # 30-jun-1967 -> 31-dic-1967
    esperado = (t1 * v_1967 + t2 * Decimal("100")) / (t1 + t2)
    assert get_ipc_interpolado_for_date(date(1967, 6, 30)) == esperado
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/engine/test_historical_index.py -k interpolado -v`
Expected: FAIL con `ImportError: cannot import name 'get_ipc_interpolado_for_date'`

- [ ] **Step 3: Implementar la función**

Agregar en `app/engine/indexation/historical_index.py`, inmediatamente después de `get_ipc_for_date`
(después de la línea 186 actual, antes del bloque de comentarios de IBC/Usura):

```python
def get_ipc_interpolado_for_date(fecha: date) -> Decimal:
    """Retorna el indice IPC interpolado linealmente para una fecha cualquiera,
    usando los dos indices de cierre de año (31-dic) que la rodean -- la formula
    del PDF (pag. 22) asume certificacion mensual, pero la fuente solo trae
    variacion anual (ver docstring de get_ipc_for_date), asi que se interpola
    entre años en vez de entre meses. Para fechas posteriores al ultimo año
    disponible en la serie, retorna el indice de ese ultimo año como
    aproximacion (ver Sprint 8 design doc, decision 3) en vez de lanzar
    ValueError -- de lo contrario ninguna liquidacion con fecha_corte actual
    podria activar indexacion."""
    anio_min = min(_IPC_INDICE_ACUMULADO)
    anio_max = max(_IPC_INDICE_ACUMULADO)

    if fecha.year < anio_min:
        raise ValueError(
            f"No hay indice IPC configurado para el año {fecha.year}. "
            f"Datos disponibles desde {anio_min}."
        )

    if fecha.year > anio_max:
        return _IPC_INDICE_ACUMULADO[anio_max]

    v2 = _IPC_INDICE_ACUMULADO[fecha.year]
    v1 = _IPC_INDICE_ACUMULADO.get(fecha.year - 1, Decimal("100"))

    dia_cierre_anterior = date(fecha.year - 1, 12, 31)
    dia_cierre_actual = date(fecha.year, 12, 31)
    t1 = (fecha - dia_cierre_anterior).days
    t2 = (dia_cierre_actual - fecha).days

    if t1 + t2 == 0:
        return v2

    return (Decimal(t1) * v2 + Decimal(t2) * v1) / Decimal(t1 + t2)
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `pytest tests/engine/test_historical_index.py -v`
Expected: PASS (todos, incluidos los 20 tests preexistentes del archivo — no deben romperse)

- [ ] **Step 5: Commit**

```bash
git status
git add app/engine/indexation/historical_index.py tests/engine/test_historical_index.py
git commit -m "feat(indexation): add get_ipc_interpolado_for_date for arbitrary dates"
```

---

### Task 2: Columna `Obligacion.aplica_indexacion_ipc`

**Files:**
- Modify: `database/models.py:70` (después de `costas_pct_manual`)
- Test: `tests/database/test_models.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar al final de `tests/database/test_models.py`:

```python
def test_obligacion_aplica_indexacion_ipc_default_false(session):
    expediente = Expediente(
        radicado="2026-00130",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Gastos medicos",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2025, 11, 20),
        valor=Decimal("427900.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.commit()

    assert obligacion.aplica_indexacion_ipc is False


def test_obligacion_aplica_indexacion_ipc_true_cuando_se_activa(session):
    expediente = Expediente(
        radicado="2026-00131",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Gastos medicos",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2025, 11, 20),
        valor=Decimal("427900.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=True,
    )
    session.add(obligacion)
    session.commit()

    fetched = session.query(Obligacion).filter_by(id=obligacion.id).one()
    assert fetched.aplica_indexacion_ipc is True
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `pytest tests/database/test_models.py -k aplica_indexacion_ipc -v`
Expected: FAIL con `TypeError: 'aplica_indexacion_ipc' is an invalid keyword argument for Obligacion`

- [ ] **Step 3: Agregar la columna**

En `database/models.py`, dentro de `class Obligacion(Base):`, inmediatamente después de la línea
`costas_pct_manual: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)`:

```python
    aplica_indexacion_ipc: Mapped[bool] = mapped_column(Boolean, default=False)
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `pytest tests/database/test_models.py -v`
Expected: PASS (todos, incluidos los tests preexistentes)

- [ ] **Step 5: Commit**

```bash
git status
git add database/models.py tests/database/test_models.py
git commit -m "feat(db): add Obligacion.aplica_indexacion_ipc column"
```

---

### Task 3: Migración de `bastium.db`

**Files:**
- Create: `scripts/migrate_aplica_indexacion_ipc.py`
- Test: `tests/scripts/test_migrate_aplica_indexacion_ipc.py`
- Create: `tests/scripts/__init__.py`

`bastium.db` ya tiene 1 expediente / 1 obligación / 1 abono existentes (confirmado con el usuario:
preservarlos, no recrear la base). `Base.metadata.create_all()` no altera tablas existentes, así que la
columna nueva de la Task 2 no llega a la base real sin un `ALTER TABLE` explícito.

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/scripts/__init__.py` (vacío) y `tests/scripts/test_migrate_aplica_indexacion_ipc.py`:

```python
import sqlite3

import pytest

from scripts.migrate_aplica_indexacion_ipc import migrar


@pytest.fixture
def db_sin_columna(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY, concepto TEXT)")
    con.execute("INSERT INTO obligaciones (id, concepto) VALUES (1, 'Gastos medicos')")
    con.commit()
    con.close()
    return db_path


def test_migrar_agrega_la_columna_y_retorna_true(db_sin_columna):
    aplicada = migrar(db_sin_columna)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columna)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert "aplica_indexacion_ipc" in columnas


def test_migrar_preserva_las_filas_existentes(db_sin_columna):
    migrar(db_sin_columna)

    con = sqlite3.connect(db_sin_columna)
    fila = con.execute("SELECT concepto, aplica_indexacion_ipc FROM obligaciones WHERE id = 1").fetchone()
    con.close()
    assert fila == ("Gastos medicos", 0)


def test_migrar_es_idempotente_segunda_corrida_retorna_false(db_sin_columna):
    primera = migrar(db_sin_columna)
    segunda = migrar(db_sin_columna)
    assert primera is True
    assert segunda is False
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `pytest tests/scripts/test_migrate_aplica_indexacion_ipc.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'scripts.migrate_aplica_indexacion_ipc'`

- [ ] **Step 3: Implementar el script**

Crear `scripts/migrate_aplica_indexacion_ipc.py`:

```python
"""Migracion de esquema (Sprint 8): agrega la columna aplica_indexacion_ipc a
la tabla obligaciones. Idempotente -- verifica con PRAGMA table_info antes de
alterar, para poder correrse mas de una vez (ej. en otra maquina de desarrollo
o en CI) sin fallar. No usa Alembic porque el proyecto todavia no tiene
migraciones formales (ver Pendientes.md, Sprint 8 design doc)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega la columna aplica_indexacion_ipc si no existe.
    Retorna True si aplico el ALTER TABLE, False si la columna ya existia."""
    con = sqlite3.connect(db_path)
    try:
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        if "aplica_indexacion_ipc" in columnas:
            return False
        con.execute(
            "ALTER TABLE obligaciones ADD COLUMN aplica_indexacion_ipc BOOLEAN NOT NULL DEFAULT 0"
        )
        con.commit()
        return True
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columna aplica_indexacion_ipc agregada a obligaciones.")
    else:
        print("La columna aplica_indexacion_ipc ya existia, no se hizo nada.")
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `pytest tests/scripts/test_migrate_aplica_indexacion_ipc.py -v`
Expected: PASS

- [ ] **Step 5: Correr la migración contra la base real**

Run: `python scripts/migrate_aplica_indexacion_ipc.py`
Expected: `Columna aplica_indexacion_ipc agregada a obligaciones.`

Verificar que la fila existente se preservó:

Run: `python -c "import sqlite3; con = sqlite3.connect('bastium.db'); print(con.execute('SELECT count(*) FROM obligaciones').fetchone())"`
Expected: `(1,)`

- [ ] **Step 6: Commit**

```bash
git status
git add scripts/migrate_aplica_indexacion_ipc.py tests/scripts/
git commit -m "feat(db): add migration script for aplica_indexacion_ipc column"
```

Nota: `bastium.db` no se comitea (ya está fuera de control de versiones o es data local); solo se
comitea el script. Confirmar con `git status` que `bastium.db` no aparece en "Changes to be committed"
antes de este commit.

---

### Task 4: Indexación para obligaciones PUNTUAL en `CivilFamiliaStrategy`

**Files:**
- Modify: `app/services/area_strategy.py:1-98`
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar en `tests/services/test_area_strategy.py`, después de
`test_civil_familia_expande_obligacion_recurrente_en_cuotas_mensuales` (línea ~117):

```python
def test_civil_familia_puntual_sin_indexacion_no_genera_evento_indexation():
    strategy = CivilFamiliaStrategy()
    obligacion = _obligacion_puntual()  # aplica_indexacion_ipc no seteado -> falsy

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
    )

    assert all(item.balance.event_type != "INDEXATION" for item in resultado.items)
    assert resultado.final_balance().indexation == Decimal("0.00")


def test_civil_familia_puntual_con_indexacion_genera_evento_indexation_con_monto_correcto():
    obligacion = Obligacion(
        id=3,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2024, 7, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=True,
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 31)
    )

    eventos_indexacion = [item for item in resultado.items if item.balance.event_type == "INDEXATION"]
    assert len(eventos_indexacion) == 1
    # Calculado manualmente con get_ipc_interpolado_for_date(2024-07-01) y
    # get_ipc_interpolado_for_date(2025-12-31) via IPCIndexation.calculate (ver
    # design doc, seccion Testing) -- 1,000,000 indexado de jul-2024 a dic-2025.
    assert eventos_indexacion[0].indexation_amount == Decimal("77633.53")
    assert eventos_indexacion[0].concept == "Indexación IPC — Dano emergente"
    assert resultado.final_balance().indexation == Decimal("77633.53")
```

Estos tests requieren los imports que ya existen en el archivo (`Obligacion`, `TipoObligacion`, `date`,
`Decimal`, `CivilFamiliaStrategy`) — no hace falta agregar ninguno nuevo.

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/services/test_area_strategy.py -k "puntual_con_indexacion or puntual_sin_indexacion" -v`
Expected: FAIL — el primero falla en el assert (`indexation == 0.00` puede pasar por casualidad si no
se implementa nada, pero el segundo falla porque `eventos_indexacion` está vacío,
`assert len(eventos_indexacion) == 1` da `0 == 1`).

- [ ] **Step 3: Implementar la generación del evento de indexación**

En `app/services/area_strategy.py`:

1. Agregar imports (después de la línea 17, junto a los demás imports de `app.engine.indexation`):

```python
from app.engine.indexation.historical_index import get_ipc_interpolado_for_date
from app.engine.indexation.ipc import IPCIndexation
```

2. Reemplazar el docstring de `CivilFamiliaStrategy` (líneas 32-37) para que ya no diga que no aplica
   indexación:

```python
class CivilFamiliaStrategy(AreaStrategy):
    """
    Unica area operable en el MVP original; ahora tambien soporta indexacion IPC
    opcional por obligacion (Sprint 8). Interes fijo por obligacion (tasa
    efectiva anual pactada/legal, Art. 1617 C.C.), convertido a tasa diaria.
    Indexacion (Art. corrección monetaria, PDF pag. 20-22): solo se activa por
    obligacion via `aplica_indexacion_ipc` -- es un juicio legal del abogado, no
    una regla automatica por categoria. La regla "no doble indexacion" del PDF
    (incompatible con SMMLV ya actualizado) no requiere un guard en tiempo de
    ejecucion: ningun campo de Obligacion usado por Civil/Familia representa un
    valor ya anclado a SMMLV (eso es exclusivo de Sancionatorio, que ya tiene
    soporta_indexacion_ipc=False), asi que la combinacion que la regla prohibe
    no es alcanzable con el modelo de datos actual.
    """
```

3. Reemplazar `_eventos_de_obligacion` (líneas 62-81) por:

```python
    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> List[Event]:
        if obligacion.tipo.value == "PUNTUAL":
            eventos = [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": obligacion.valor, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]
            if obligacion.aplica_indexacion_ipc:
                eventos.append(
                    self._evento_indexacion(
                        fecha_causacion=obligacion.fecha_origen,
                        capital=obligacion.valor,
                        concepto=obligacion.concepto,
                        fecha_corte=fecha_corte,
                    )
                )
            return eventos

        # RECURRENTE
        scheduler = FamilyScheduler()
        scheduler.add_monthly_obligation(
            amount=obligacion.valor,
            concept=obligacion.concepto,
            due_day=obligacion.dia_pago,
            category=obligacion.categoria,
        )
        fin = obligacion.fecha_fin or fecha_corte
        eventos_capital = scheduler.generate(start=obligacion.fecha_inicio, end=fin)

        if not obligacion.aplica_indexacion_ipc:
            return eventos_capital

        eventos = list(eventos_capital)
        for cuota in eventos_capital:
            eventos.append(
                self._evento_indexacion(
                    fecha_causacion=cuota.date,
                    capital=cuota.payload["amount"],
                    concepto=obligacion.concepto,
                    fecha_corte=fecha_corte,
                )
            )
        return eventos

    def _evento_indexacion(
        self, fecha_causacion: date, capital: Decimal, concepto: str, fecha_corte: date
    ) -> Event:
        monto = IPCIndexation.calculate(
            capital=capital,
            initial_index=get_ipc_interpolado_for_date(fecha_causacion),
            final_index=get_ipc_interpolado_for_date(fecha_corte),
        )
        return Event(
            date=fecha_causacion,
            payload={"amount": monto, "label": f"Indexación IPC — {concepto}"},
            event_type="INDEXATION",
        )
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `pytest tests/services/test_area_strategy.py -v`
Expected: PASS (todos, incluidos los tests preexistentes de `CivilFamiliaStrategy`, `ComercialStrategy`,
etc. — ninguno pasa `aplica_indexacion_ipc`, así que siguen sin generar eventos `INDEXATION`)

- [ ] **Step 5: Commit**

```bash
git status
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat(civil-familia): wire IPC indexation for obligaciones PUNTUAL"
```

---

### Task 5: Indexación por cuota en obligaciones RECURRENTE

**Files:**
- Test: `tests/services/test_area_strategy.py`

La implementación ya quedó lista en la Task 4 (`_eventos_de_obligacion` ya cubre la rama RECURRENTE).
Esta tarea es puramente de verificación TDD: confirmar con un test explícito que cada cuota indexa desde
**su propia fecha**, no desde `fecha_inicio` de la obligación completa (el requisito de "tracto sucesivo,
mes a mes" del PDF pág. 20).

- [ ] **Step 1: Escribir el test que falla**

Agregar en `tests/services/test_area_strategy.py`, después de los tests de la Task 4:

```python
def test_civil_familia_recurrente_con_indexacion_cada_cuota_indexa_desde_su_propia_fecha():
    obligacion = Obligacion(
        id=4,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2025, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2025, 1, 1),
        fecha_fin=date(2025, 2, 5),
        aplica_indexacion_ipc=True,
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 31)
    )

    eventos_indexacion = sorted(
        (item for item in resultado.items if item.balance.event_type == "INDEXATION"),
        key=lambda item: item.date,
    )
    # 2 cuotas (5-ene y 5-feb-2025), cada una con su propio monto de indexacion
    # porque cada una arranca a indexar desde una fecha distinta -- si ambas
    # dieran el mismo monto, seria señal de que se esta usando fecha_inicio de
    # la obligacion en vez de la fecha de cada cuota.
    assert len(eventos_indexacion) == 2
    assert eventos_indexacion[0].date == date(2025, 1, 5)
    assert eventos_indexacion[1].date == date(2025, 2, 5)
    assert eventos_indexacion[0].indexation_amount == Decimal("25133.13")
    assert eventos_indexacion[1].indexation_amount == Decimal("22869.89")
    assert eventos_indexacion[0].indexation_amount != eventos_indexacion[1].indexation_amount
```

- [ ] **Step 2: Correr el test**

Run: `pytest tests/services/test_area_strategy.py -k recurrente_con_indexacion -v`
Expected: PASS de inmediato (la implementación de la Task 4 ya cubre esta rama) — si falla, revisar que
`_evento_indexacion` en la Task 4 use `cuota.date` y `cuota.payload["amount"]`, no
`obligacion.fecha_inicio`/`obligacion.valor`.

- [ ] **Step 3: Commit**

```bash
git status
git add tests/services/test_area_strategy.py
git commit -m "test(civil-familia): verify per-cuota IPC indexation on obligaciones RECURRENTE"
```

---

### Task 6: Checkbox "Aplica indexación IPC" en la GUI

**Files:**
- Modify: `app/views/obligaciones.py`
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar a `tests/views/test_obligaciones.py`, usando el mismo helper `_expediente_de_prueba(monkeypatch,
area=...)` y el mismo patrón `session_module.get_session()` que ya usan todos los tests existentes del
archivo (ver por ejemplo `test_guarda_obligacion_comercial_con_tasa_moratoria_y_ibc`):

```python
def test_check_indexacion_visible_solo_en_civil_familia(qtbot, monkeypatch):
    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)
    dialog_civil.show()
    assert dialog_civil.check_aplica_indexacion_ipc.isVisible() is True

    expediente_id_comercial = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)
    dialog_comercial = ObligacionFormDialog(expediente_id=expediente_id_comercial, area="COMERCIAL")
    qtbot.addWidget(dialog_comercial)
    dialog_comercial.show()
    assert dialog_comercial.check_aplica_indexacion_ipc.isVisible() is False


def test_guarda_obligacion_con_indexacion_ipc_marcada(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Dano emergente")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2024, 7, 1))
    dialog.check_aplica_indexacion_ipc.setChecked(True)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.aplica_indexacion_ipc is True
    session.close()


def test_guarda_obligacion_sin_marcar_indexacion_queda_en_false(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Dano emergente")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2024, 7, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.aplica_indexacion_ipc is False
    session.close()
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/views/test_obligaciones.py -k indexacion -v`
Expected: FAIL con `AttributeError: 'ObligacionFormDialog' object has no attribute 'check_aplica_indexacion_ipc'`

- [ ] **Step 3: Implementar el checkbox**

En `app/views/obligaciones.py`:

1. Después de la línea `self.campo_costas_pct = QLineEdit()` (línea 78), agregar:

```python
        self.check_aplica_indexacion_ipc = QCheckBox("Aplica indexación IPC (corrección monetaria)")
```

2. Después de `self.layout_formulario.addRow("% Costas judiciales (opcional)", self.campo_costas_pct)`
   (línea 106), agregar:

```python
        self.layout_formulario.addRow(self.check_aplica_indexacion_ipc)
```

3. Junto a las demás líneas `setVisible` por área (después de la línea 127
   `self.campo_costas_pct.setVisible(es_honorarios)`), agregar:

```python
        self.check_aplica_indexacion_ipc.setVisible(self._area == "CIVIL_FAMILIA")
```

4. En `guardar()`, dentro de la construcción de `Obligacion(...)` (líneas 241-260, la rama no-Laboral),
   agregar el kwarg:

```python
            aplica_indexacion_ipc=self.check_aplica_indexacion_ipc.isChecked(),
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `pytest tests/views/test_obligaciones.py -v`
Expected: PASS (todos, incluidos los tests preexistentes de visibilidad condicional por área)

- [ ] **Step 5: Smoke test manual end-to-end**

Run: `python main.py`

1. Abrir (o crear) un expediente de área "Civil / Familia".
2. Clic en "Agregar obligación" — confirmar que aparece el checkbox "Aplica indexación IPC (corrección
   monetaria)", sin marcar por defecto.
3. Cargar una obligación PUNTUAL con fecha de origen anterior a la fecha de corte del expediente
   (ej. 2024-07-01), marcar el checkbox, guardar.
4. Clic en "Liquidar" — confirmar en la tabla de resultado que aparece una fila adicional con concepto
   `Indexación IPC — <concepto>` y que el saldo final es mayor que si se liquida la misma obligación sin
   marcar el checkbox.
5. Abrir un expediente de área "Comercial" y confirmar que el checkbox NO aparece en el formulario.

- [ ] **Step 6: Commit**

```bash
git status
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "feat(gui): add 'Aplica indexación IPC' checkbox to ObligacionFormDialog"
```

---

### Task 7: Documentación

**Files:**
- Modify: `README.md`
- Modify: `docs/GUIA_USUARIO.md`
- Modify: `docs/specifications/03_motor_indexacion.md`
- Modify: `Pendientes.md`

Regla obligatoria de `Pendientes.md` (línea 12-16): al cerrar un sprint, `README.md` y
`docs/GUIA_USUARIO.md` deben reflejar el nuevo estado.

- [ ] **Step 1: Actualizar `README.md`**

En la sección "Estado actual", mover la indexación IPC de la lista 🚧 a la lista ✅. Reemplazar el
párrafo que empieza en la línea 14 (`✅ **Funcional hoy:** ...`) agregando, después de la mención de
Civil/Familia (línea 14-16, antes de "**Comercial**"):

```
, indexación IPC opcional por obligación (Art. corrección monetaria; el abogado marca caso por caso si
aplica, con interpolación entre índices de cierre de año para fechas intermedias)
```

Y en el párrafo "🚧 En desarrollo" (línea 31-40), quitar "indexación por IPC" de la lista de pendientes,
y ajustar la frase sobre las series históricas (línea 34-38) para reflejar que IPC ya está conectado:

```
🚧 **En desarrollo:** seguridad social (cotizaciones a pensión, salud, ARL, fondo de solidaridad
pensional) en el área Laboral, prescripción/caducidad, anatocismo comercial condicionado (Art. 886
C.Co.) y varios módulos más también están pendientes. Las series históricas de SMLMV, IPC e IBC/Tasa de
Usura (1984-2026, 1967-2025 y 1997-2026 respectivamente) ya están cargadas en
`app/engine/indexation/historical_index.py` — IBC/Usura se usa en Comercial y en la fase 2 de la
indemnización moratoria laboral, e IPC ya está conectado a la indexación de Civil/Familia (Sprint 8);
SMLMV sigue sin un consumidor propio. La tabla histórica de UVT es un caso aparte: ni siquiera está
cargada todavía. El plan completo, sprint por sprint, está en **[Pendientes.md](Pendientes.md)**.
```

- [ ] **Step 2: Actualizar `docs/GUIA_USUARIO.md`**

1. En la sección 5.3 (Agregar una obligación puntual), después del punto "Fecha de origen" (línea 213),
   agregar:

```
   - **Aplica indexación IPC**: marca esta casilla si la obligación debe corregirse monetariamente por
     inflación (indexación, Art. corrección monetaria) además del interés. Es una decisión del abogado
     caso por caso — no todas las obligaciones se indexan. Ver
     [sección 7.7](#77-indexación-ipc-corrección-monetaria) para el detalle de cómo se calcula.
```

2. Reemplazar el bullet de la sección 8 (líneas 570-572, "🚧 **Indexación por IPC**") por:

```
- ✅ **Indexación por IPC** ya está conectada a Civil/Familia (Sprint 8) — ver
  [sección 7.7](#77-indexación-ipc-corrección-monetaria).
```

3. Agregar una nueva sección 7.7 después de la sección 7.6 (después de la línea 547, antes del `---` de
   la línea 549):

```markdown
### 7.7. Indexación IPC (corrección monetaria)

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente Civil/
  Familia, la casilla **"Aplica indexación IPC (corrección monetaria)"** — ver
  [sección 5.3](#53-agregar-una-obligación-puntual-una-deuda-de-una-sola-vez). No viene marcada por
  defecto: el abogado decide caso por caso si la obligación debe indexarse, además de generar intereses.
- **Dónde vive la lógica en el código**: `app/engine/indexation/ipc.py` (`IPCIndexation.calculate`) y
  `app/engine/indexation/historical_index.py` (`get_ipc_interpolado_for_date`), invocados desde
  `CivilFamiliaStrategy._evento_indexacion` en `app/services/area_strategy.py`.
- **Cómo se calcula**: `Va = Vh × (IPC_final / IPC_inicial)`. Para una obligación **Puntual**, se indexa
  una sola vez desde la fecha de origen hasta la fecha de corte del expediente. Para una obligación
  **Recurrente** (cuotas mensuales), cada cuota se indexa individualmente desde su propia fecha de
  vencimiento — no todas desde el inicio de la obligación — porque cada cuota se deprecia un tiempo
  distinto.
- **Limitación conocida**: la fuente de datos (Sprint 5) solo trae el IPC de cierre de cada año, no mes a
  mes como certifica el DANE en la vida real. Para una fecha intermedia dentro del año, el programa
  interpola linealmente entre el índice de cierre del año anterior y el del año actual — es una
  aproximación razonable, pero no es el valor mensual exacto que certificaría el DANE. Para fechas de
  2026 en adelante (la serie no llega hasta ahí), se usa el índice de 2025 como aproximación.
- **Qué NO hace todavía**: los intereses (Art. 1617 C.C.) se siguen calculando solo sobre el capital, no
  sobre el capital ya indexado — el algoritmo de "Suma Única" del PDF (interés sobre el valor indexado)
  requeriría cambiar el motor de liquidación para las 5 áreas, fuera del alcance de este sprint.
```

- [ ] **Step 3: Actualizar `docs/specifications/03_motor_indexacion.md`**

Reemplazar el archivo completo por:

```markdown
# Motor de Indexacion (IPC)

## Que hace
Ajusta un capital historico a valor presente segun la variacion del Indice de Precios al Consumidor (IPC),
usando `Va = Vh * (IPC_final / IPC_inicial)`. Conectado a `CivilFamiliaStrategy` desde el Sprint 8, con
activacion opcional por obligacion.

## Componentes
- `app/engine/indexation/ipc.py`: `IPCIndexation.calculate(capital, initial_index, final_index)`. Si hay
  deflacion (`final_index <= initial_index`), retorna 0 -- la jurisprudencia no castiga al acreedor por
  deflacion.
- `app/engine/indexation/smmlv.py`: conversion de un valor expresado en SMMLV a pesos.
- `app/engine/indexation/historical_index.py`: series historicas de SMLMV (1984-2026), IPC (1967-2025,
  variacion anual + indice acumulado derivado) e IBC/Tasa de Usura (1997-07-01 a 2026-07-31). Expone
  `get_smlmv_for_year`, `get_ipc_for_date` (indice exacto de cierre de año), `get_ipc_interpolado_for_date`
  (Sprint 8: interpola entre cierres de año para cualquier fecha, con fallback al ultimo año disponible
  para fechas futuras), `get_ibc_usura_for_date`. UVT sigue pendiente (sin fuente completa).
- `app/services/area_strategy.py`, `CivilFamiliaStrategy._evento_indexacion` (Sprint 8): genera un evento
  `INDEXATION` por cada evento de capital cuando `Obligacion.aplica_indexacion_ipc` es `True` -- uno para
  obligaciones PUNTUAL, uno por cuota para RECURRENTE (tracto sucesivo).

## Estado
Conectado a `CivilFamiliaStrategy` (Sprint 8). Opt-in por obligacion via el campo
`aplica_indexacion_ipc`, expuesto como checkbox en `ObligacionFormDialog` solo para el area Civil/
Familia.

## Limitaciones conocidas (documentadas, no bloqueantes)
- La interpolacion es entre indices de **cierre de año**, no entre meses certificados como en la vida
  real (el DANE certifica mensualmente, pero la fuente transcrita en el Sprint 5 solo trae variacion
  anual) -- ver `get_ipc_interpolado_for_date`.
- Fechas de 2026 en adelante usan el indice de 2025 como aproximacion (la serie no tiene 2026).
- El interes (Art. 1617 C.C.) se sigue calculando solo sobre el capital, no sobre el capital ya
  indexado -- el algoritmo de "Suma Única" del PDF (pag. 22) pide interes sobre el valor indexado; eso
  requeriria cambiar `LiquidationCore`/`BalanceEngine` para las 5 areas, fuera de alcance de este sprint.
- UVT y UVR siguen sin cargar (fuera de alcance, ver Sprint 5).

Ver `Pendientes.md`, Sprint 8.
```

- [ ] **Step 4: Actualizar `Pendientes.md`**

En la sección "## Sprint 8 — Conectar indexación IPC al área Civil/Familia" (línea 469), cambiar el
título de `🔴 Pendiente` a `✅ Completado`, y agregar antes de la "**Definición de Hecho:**" final (antes
de la línea 505) un bloque `**Estado:**` con el mismo formato usado en los Sprints 2-6:

```markdown
**Estado:** Implementado (2026-07-19) — ver
`docs/superpowers/plans/2026-07-19-sprint8-indexacion-ipc-civil-familia.md` y
`docs/superpowers/specs/2026-07-19-sprint8-indexacion-ipc-civil-familia-design.md`. Decisiones tomadas
con el usuario durante el brainstorming previo: (a) la activación es **opt-in por obligación**
(`aplica_indexacion_ipc`), no automática por área — es un juicio legal del abogado; (b) la interpolación
del PDF (entre meses certificados) se aproxima con interpolación entre **índices de cierre de año**,
porque la fuente transcrita en el Sprint 5 nunca tuvo granularidad mensual; (c) fechas de 2026 en
adelante usan el índice de 2025 como aproximación, para no bloquear liquidaciones con la fecha actual del
sistema; (d) la regla "no doble indexación" del PDF se documentó en vez de codificarse como guard, porque
ningún campo de `Obligacion` usado por Civil/Familia puede representar la combinación que esa regla
prohíbe. Queda documentado como limitación conocida (no corregida en este sprint): el interés sigue
calculándose solo sobre el capital, no sobre el capital ya indexado, a diferencia del algoritmo de "Suma
Única" del PDF (pág. 22) — cambiar eso afecta el motor core para las 5 áreas.
```

- [ ] **Step 5: Commit**

```bash
git status
git add README.md docs/GUIA_USUARIO.md docs/specifications/03_motor_indexacion.md Pendientes.md
git commit -m "docs: close out Sprint 8 (indexación IPC → Civil/Familia)"
```

---

### Task 8: Verificación final de la suite completa

**Files:** ninguno (solo verificación)

- [ ] **Step 1: Correr la suite completa**

Run: `pytest -v`
Expected: PASS en todos los tests (el conteo base era 226+ tests en verde antes de este sprint; debe
seguir en verde, con los tests nuevos de las Tasks 1-6 sumados).

- [ ] **Step 2: Si algo falla, diagnosticar antes de continuar**

No commitear ni cerrar el sprint con tests rotos. Si algo falla, usar
`superpowers:systematic-debugging` antes de proponer un fix.

- [ ] **Step 3: Commit final (si Step 1 quedó limpio y no hubo cambios adicionales que commitear)**

Si todos los commits de las Tasks 1-7 ya se hicieron y la suite pasa, no hay nada adicional que
commitear en este paso — es solo la verificación de cierre del sprint.
