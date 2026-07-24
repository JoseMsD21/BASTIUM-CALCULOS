# Sprint 15 — Tributario completo (cierre 11b) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the sixth operable area, `TributarioStrategy` (impuesto a cargo, 3 sanciones tributarias,
imputación tributaria, y Renta Líquida Gravable informativa), reutilizando el motor de liquidación
genérico existente en vez de construir uno dedicado.

**Architecture:** Reutiliza `LiquidationCore`/`AllocationEngine`/`UniversalLiquidationService` sin cambios
estructurales — el impuesto a cargo se enruta al bucket `principal` (mismo patrón que cada área anterior:
su propio código de categoría se agrega a `_capital_concepts`), las 3 sanciones se normalizan a un único
`event_type="SANCION_TRIBUTARIA"` que cae en el bucket `indexation` (mismo orden de pago exigido:
sanciones → intereses → impuesto), y el interés automático E.T. 635 reutiliza el `rate_provider` ya
construido en el Sprint 11a. Renta Líquida Gravable se mantiene fuera del balance de deuda, expuesta como
un campo opcional nuevo en `LiquidationResult`.

**Tech Stack:** Python, SQLAlchemy, PySide6 (Qt), pytest, pytest-qt, reportlab, python-docx.

**Design spec:** `docs/superpowers/specs/2026-07-24-sprint15-tributario-11b-design.md` (leer antes de
empezar — documenta las decisiones de arquitectura y por qué se descartó un motor de imputación
dedicado).

---

### Task 1: Motor de sanciones tributarias (`app/engine/tax/sanciones.py`)

**Files:**
- Create: `app/engine/tax/sanciones.py`
- Modify: `app/services/parametro_service.py:112` (agregar 4 entradas al catálogo, antes del `}` que
  cierra `CATALOGO_PARAMETROS`)
- Test: `tests/engine/tax/test_sanciones.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/engine/tax/test_sanciones.py`:

```python
from datetime import date
from datetime import datetime as _dt
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.engine.indexation.historical_index import _UVT_POR_ANIO
from app.engine.tax.sanciones import (
    aplicar_piso_sancion_minima,
    calcular_sancion_error_aritmetico,
    calcular_sancion_extemporaneidad,
    calcular_sancion_inexactitud,
)
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _parametros_sanciones_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="EXTEMPORANEIDAD_PCT_MENSUAL", valor=Decimal("5"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.add(ParametroLegal(
        clave="INEXACTITUD_PCT", valor=Decimal("160"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.add(ParametroLegal(
        clave="INEXACTITUD_AGRAVADA_PCT", valor=Decimal("200"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.add(ParametroLegal(
        clave="ERROR_ARITMETICO_PCT", valor=Decimal("30"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    for anio, valor in _UVT_POR_ANIO.items():
        session.add(ParametroLegal(
            clave="UVT", valor=valor, vigente_desde=date(anio, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    session.commit()
    session.close()


def test_piso_sancion_minima_no_afecta_montos_por_encima_de_10_uvt():
    # UVT 2024 = 47065.00 (ver historical_index.py) -> piso = 470650.00
    assert aplicar_piso_sancion_minima(Decimal("1000000.00"), date(2024, 6, 1)) == Decimal("1000000.00")


def test_piso_sancion_minima_eleva_montos_por_debajo_de_10_uvt():
    assert aplicar_piso_sancion_minima(Decimal("100000.00"), date(2024, 6, 1)) == Decimal("470650.00")


def test_extemporaneidad_5_pct_mensual_por_cada_mes():
    # Impuesto a cargo 10,000,000, 2 meses de atraso: 5% x 2 = 10% = 1,000,000 (por encima del piso).
    resultado = calcular_sancion_extemporaneidad(
        impuesto_a_cargo=Decimal("10000000.00"), meses_o_fraccion=2, fecha_referencia=date(2024, 6, 1)
    )
    assert resultado == Decimal("1000000.00")


def test_extemporaneidad_topada_en_100_pct_del_impuesto_a_cargo():
    # 5% x 30 meses = 150%, debe quedar topado en el 100% del impuesto a cargo.
    resultado = calcular_sancion_extemporaneidad(
        impuesto_a_cargo=Decimal("10000000.00"), meses_o_fraccion=30, fecha_referencia=date(2024, 6, 1)
    )
    assert resultado == Decimal("10000000.00")


def test_extemporaneidad_por_debajo_del_piso_queda_en_10_uvt():
    resultado = calcular_sancion_extemporaneidad(
        impuesto_a_cargo=Decimal("1000000.00"), meses_o_fraccion=1, fecha_referencia=date(2024, 6, 1)
    )
    assert resultado == Decimal("470650.00")


def test_inexactitud_160_pct_de_la_diferencia_sin_agravante():
    resultado = calcular_sancion_inexactitud(
        diferencia=Decimal("5000000.00"), agravada=False, fecha_referencia=date(2024, 6, 1)
    )
    assert resultado == Decimal("8000000.00")


def test_inexactitud_200_pct_de_la_diferencia_agravada():
    resultado = calcular_sancion_inexactitud(
        diferencia=Decimal("5000000.00"), agravada=True, fecha_referencia=date(2024, 6, 1)
    )
    assert resultado == Decimal("10000000.00")


def test_error_aritmetico_30_pct_de_la_diferencia():
    resultado = calcular_sancion_error_aritmetico(
        diferencia=Decimal("5000000.00"), fecha_referencia=date(2024, 6, 1)
    )
    assert resultado == Decimal("1500000.00")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/engine/tax/test_sanciones.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.engine.tax.sanciones'`

- [ ] **Step 3: Add the 4 catalog entries**

In `app/services/parametro_service.py`, add to `CATALOGO_PARAMETROS` (después de la entrada `"UVT"`, antes
del `}` que cierra el diccionario en la línea 112):

```python
    "EXTEMPORANEIDAD_PCT_MENSUAL": InfoParametro(
        "Sanción por extemporaneidad, porcentaje mensual del impuesto a cargo", "Topes legales",
        "Estatuto Tributario (PDF pág. 39)", ModoResolucion.ABIERTO,
    ),
    "INEXACTITUD_PCT": InfoParametro(
        "Sanción por inexactitud, porcentaje de la diferencia (sin agravante)", "Topes legales",
        "Estatuto Tributario (PDF pág. 39)", ModoResolucion.ABIERTO,
    ),
    "INEXACTITUD_AGRAVADA_PCT": InfoParametro(
        "Sanción por inexactitud, porcentaje agravado (omisión de activos/pasivos inexistentes)",
        "Topes legales", "Estatuto Tributario (PDF pág. 39)", ModoResolucion.ABIERTO,
    ),
    "ERROR_ARITMETICO_PCT": InfoParametro(
        "Sanción por error aritmético, porcentaje de la diferencia generada", "Topes legales",
        "Estatuto Tributario (PDF pág. 39)", ModoResolucion.ABIERTO,
    ),
```

- [ ] **Step 4: Create `app/engine/tax/sanciones.py`**

```python
"""
Sanciones tributarias (Estatuto Tributario, PDF pag. 39): extemporaneidad,
inexactitud y error aritmetico. Las tres comparten un piso legal -- ninguna
sancion puede ser inferior a 10 UVT (aplicar_piso_sancion_minima) -- que se
aplica una sola vez, aqui, en vez de repetir la logica en cada funcion.

Ver docs/superpowers/specs/2026-07-24-sprint15-tributario-11b-design.md.
"""

from datetime import date
from decimal import Decimal

from app.engine.indexation.historical_index import get_uvt_for_year
from app.engine.math.rounding import Rounding
from app.services.parametro_service import get_parametro


def aplicar_piso_sancion_minima(monto_sancion: Decimal, fecha_referencia: date) -> Decimal:
    """Ninguna sancion tributaria puede ser inferior a 10 UVT del año de referencia."""
    piso = Decimal("10") * get_uvt_for_year(fecha_referencia.year)
    return max(monto_sancion, piso)


def calcular_sancion_extemporaneidad(
    impuesto_a_cargo: Decimal, meses_o_fraccion: int, fecha_referencia: date
) -> Decimal:
    """5% mensual (o fraccion de mes) del impuesto a cargo, tope 100% del impuesto a cargo."""
    pct_mensual = get_parametro("EXTEMPORANEIDAD_PCT_MENSUAL", fecha_referencia)
    monto = impuesto_a_cargo * pct_mensual / Decimal("100") * Decimal(meses_o_fraccion)
    monto = min(monto, impuesto_a_cargo)
    monto = aplicar_piso_sancion_minima(monto, fecha_referencia)
    return Rounding.money(monto)


def calcular_sancion_inexactitud(diferencia: Decimal, agravada: bool, fecha_referencia: date) -> Decimal:
    """160% (o 200% si agravada -- omision de activos o inclusion de pasivos inexistentes) de la
    diferencia entre el saldo determinado y el declarado."""
    clave = "INEXACTITUD_AGRAVADA_PCT" if agravada else "INEXACTITUD_PCT"
    pct = get_parametro(clave, fecha_referencia)
    monto = diferencia * pct / Decimal("100")
    monto = aplicar_piso_sancion_minima(monto, fecha_referencia)
    return Rounding.money(monto)


def calcular_sancion_error_aritmetico(diferencia: Decimal, fecha_referencia: date) -> Decimal:
    """30% de la diferencia generada por el error aritmetico."""
    pct = get_parametro("ERROR_ARITMETICO_PCT", fecha_referencia)
    monto = diferencia * pct / Decimal("100")
    monto = aplicar_piso_sancion_minima(monto, fecha_referencia)
    return Rounding.money(monto)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/engine/tax/test_sanciones.py -v`
Expected: PASS (9 tests)

- [ ] **Step 6: Commit**

```bash
git add app/engine/tax/sanciones.py app/services/parametro_service.py tests/engine/tax/test_sanciones.py
git commit -m "feat: add tributario sanciones engine (extemporaneidad, inexactitud, error aritmetico)"
```

---

### Task 2: Esquema — `AreaDerecho`, columnas nuevas en `Obligacion`, migración

**Files:**
- Modify: `database/models.py:52` (agregar `TRIBUTARIO` a `AreaDerecho`), `database/models.py:106-107`
  (agregar columnas nuevas a `Obligacion`, antes de la relación `expediente`)
- Create: `scripts/migrate_tributario.py`
- Test: `tests/scripts/test_migrate_tributario.py`

- [ ] **Step 1: Write the failing migration tests**

Create `tests/scripts/test_migrate_tributario.py`:

```python
import sqlite3

import pytest

from scripts.migrate_tributario import migrar

_COLUMNAS_NUEVAS = {
    "base_sancion_tributaria", "meses_extemporaneidad", "sancion_agravada",
    "ingresos_brutos", "devoluciones_rebajas_descuentos", "costos", "deducciones", "rentas_exentas",
}


@pytest.fixture
def db_sin_columnas(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY, concepto TEXT)")
    con.execute("INSERT INTO obligaciones (id, concepto) VALUES (1, 'Impuesto de renta 2024')")
    con.commit()
    con.close()
    return db_path


def test_migrar_agrega_las_ocho_columnas_y_retorna_true(db_sin_columnas):
    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert _COLUMNAS_NUEVAS <= columnas


def test_migrar_preserva_las_filas_existentes_con_sancion_agravada_falso_por_defecto(db_sin_columnas):
    migrar(db_sin_columnas)

    con = sqlite3.connect(db_sin_columnas)
    fila = con.execute("SELECT concepto, sancion_agravada FROM obligaciones WHERE id = 1").fetchone()
    con.close()
    assert fila == ("Impuesto de renta 2024", 0)


def test_migrar_es_idempotente_segunda_corrida_retorna_false(db_sin_columnas):
    primera = migrar(db_sin_columnas)
    segunda = migrar(db_sin_columnas)
    assert primera is True
    assert segunda is False


def test_migrar_es_idempotente_si_ya_existe_solo_una_de_las_ocho_columnas(db_sin_columnas):
    con = sqlite3.connect(db_sin_columnas)
    con.execute("ALTER TABLE obligaciones ADD COLUMN base_sancion_tributaria NUMERIC(18, 2)")
    con.commit()
    con.close()

    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert _COLUMNAS_NUEVAS <= columnas
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/scripts/test_migrate_tributario.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.migrate_tributario'`

- [ ] **Step 3: Add `TRIBUTARIO` to `AreaDerecho`**

In `database/models.py`, line 52, change:
```python
class AreaDerecho(enum.Enum):
    CIVIL_FAMILIA = "CIVIL_FAMILIA"
    COMERCIAL = "COMERCIAL"
    LABORAL = "LABORAL"
    SANCIONATORIO = "SANCIONATORIO"
    HONORARIOS = "HONORARIOS"
```
to:
```python
class AreaDerecho(enum.Enum):
    CIVIL_FAMILIA = "CIVIL_FAMILIA"
    COMERCIAL = "COMERCIAL"
    LABORAL = "LABORAL"
    SANCIONATORIO = "SANCIONATORIO"
    HONORARIOS = "HONORARIOS"
    TRIBUTARIO = "TRIBUTARIO"
```

- [ ] **Step 4: Add the 8 new columns to `Obligacion`**

In `database/models.py`, line 106 (justo antes de la línea 108, `expediente: Mapped["Expediente"] =
relationship(...)`), agregar:

```python
    base_sancion_tributaria: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    meses_extemporaneidad: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sancion_agravada: Mapped[bool] = mapped_column(Boolean, default=False)
    ingresos_brutos: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    devoluciones_rebajas_descuentos: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    costos: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    deducciones: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    rentas_exentas: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
```

- [ ] **Step 5: Create `scripts/migrate_tributario.py`**

```python
"""Migracion de esquema (Sprint 15): agrega las columnas propias del area
Tributario a la tabla obligaciones (base_sancion_tributaria,
meses_extemporaneidad, sancion_agravada, y los 5 campos de Renta Liquida
Gravable). Idempotente -- mismo patron que scripts/migrate_moneda_trm.py
(Sprint 12): verifica con PRAGMA table_info antes de alterar cada columna."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "base_sancion_tributaria": "NUMERIC(18, 2)",
    "meses_extemporaneidad": "INTEGER",
    "sancion_agravada": "BOOLEAN NOT NULL DEFAULT 0",
    "ingresos_brutos": "NUMERIC(18, 2)",
    "devoluciones_rebajas_descuentos": "NUMERIC(18, 2)",
    "costos": "NUMERIC(18, 2)",
    "deducciones": "NUMERIC(18, 2)",
    "rentas_exentas": "NUMERIC(18, 2)",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas tributarias si no existen. Retorna True si aplico al menos
    un ALTER TABLE, False si las ocho columnas ya existian."""
    con = sqlite3.connect(db_path)
    try:
        columnas_existentes = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        aplico_alguna = False
        for nombre, definicion in _COLUMNAS.items():
            if nombre in columnas_existentes:
                continue
            con.execute(f"ALTER TABLE obligaciones ADD COLUMN {nombre} {definicion}")
            aplico_alguna = True
        con.commit()
        return aplico_alguna
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columnas tributarias agregadas a obligaciones.")
    else:
        print("Las columnas ya existian, no se hizo nada.")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/scripts/test_migrate_tributario.py -v`
Expected: PASS (4 tests)

- [ ] **Step 7: Run the full suite to confirm nothing else broke**

Run: `pytest -q`
Expected: all passing (adding an enum member and nullable columns doesn't affect existing rows/tests).

- [ ] **Step 8: Commit**

```bash
git add database/models.py scripts/migrate_tributario.py tests/scripts/test_migrate_tributario.py
git commit -m "feat: add TRIBUTARIO area and tributario columns to Obligacion (schema)"
```

---

### Task 3: Constantes de GUI — `CATEGORIAS_TRIBUTARIO`, `AREAS_DERECHO`

**Files:**
- Modify: `app/core/constants.py:47` (agregar `CATEGORIAS_TRIBUTARIO`), `app/core/constants.py:48-54`
  (agregar `TRIBUTARIO` a `AREAS_DERECHO`)

No hay test dedicado para este archivo (es una lista de constantes de UI, ya cubierta indirectamente por
las pruebas de `obligaciones.py`/`area_strategy.py` de tareas posteriores). Verificar leyendo el archivo
después de editar.

- [ ] **Step 1: Add `CATEGORIAS_TRIBUTARIO`**

En `app/core/constants.py`, justo antes de `AREAS_DERECHO` (línea 48), agregar:

```python
CATEGORIAS_TRIBUTARIO = [
    ("IMPUESTO_A_CARGO", "Impuesto a cargo"),
    ("SANCION_EXTEMPORANEIDAD", "Sancion por extemporaneidad"),
    ("SANCION_INEXACTITUD", "Sancion por inexactitud"),
    ("SANCION_ERROR_ARITMETICO", "Sancion por error aritmetico"),
    ("RENTA_LIQUIDA", "Depuracion de renta liquida gravable"),
]
# "IMPUESTO_A_CARGO" es el unico codigo de esta lista que debe existir tambien en
# app.engine.liquidation.engine.LiquidationCore._capital_concepts (genera un evento de
# capital). Las 3 sanciones generan un evento "SANCION_TRIBUTARIA" normalizado (ver
# TributarioStrategy._evento_de_obligacion, Tarea 5) y "RENTA_LIQUIDA" no genera ningun
# evento -- se procesa aparte (ver depurar_renta_liquida_gravable).

```

- [ ] **Step 2: Add `TRIBUTARIO` to `AREAS_DERECHO`**

En `app/core/constants.py`, cambiar:
```python
AREAS_DERECHO = [
    ("CIVIL_FAMILIA", "Civil / Familia", True),
    ("COMERCIAL", "Comercial", True),
    ("LABORAL", "Laboral", True),
    ("SANCIONATORIO", "Sancionatorio", True),
    ("HONORARIOS", "Honorarios / Litigio", True),
]
```
a:
```python
AREAS_DERECHO = [
    ("CIVIL_FAMILIA", "Civil / Familia", True),
    ("COMERCIAL", "Comercial", True),
    ("LABORAL", "Laboral", True),
    ("SANCIONATORIO", "Sancionatorio", True),
    ("HONORARIOS", "Honorarios / Litigio", True),
    ("TRIBUTARIO", "Tributario", True),
]
```

- [ ] **Step 3: Commit**

```bash
git add app/core/constants.py
git commit -m "feat: add CATEGORIAS_TRIBUTARIO and register TRIBUTARIO in AREAS_DERECHO"
```

---

### Task 4: `LiquidationResult.renta_liquida`, `_capital_concepts`, serialización de auditoría

**Files:**
- Modify: `app/engine/liquidation/engine.py:28-34` (agregar `"IMPUESTO_A_CARGO"` a `_capital_concepts`)
- Modify: `app/engine/liquidation/result.py` (agregar campo `renta_liquida`)
- Modify: `app/engine/audit/serialization.py` (serializar/deserializar el campo nuevo)
- Test: `tests/audit/test_serialization.py` (archivo ya existente — 6 pruebas actuales, ver contenido
  completo antes de editar; esta tarea agrega 3 pruebas nuevas al final, sin tocar las existentes)

- [ ] **Step 1: Write the failing round-trip tests**

Agrega estas 3 funciones al final de `tests/audit/test_serialization.py` (el archivo ya importa
`date`, `Decimal`, `deserializar_resultado`, `serializar_resultado`, `LiquidationItem`, `PendingDebt`,
`RunningBalance`, `LiquidationResult` — agrega un import nuevo para `RentaLiquidaGravableResult` junto a
los existentes):

```python
from app.engine.tax.renta_liquida import RentaLiquidaGravableResult


def _item_de_prueba() -> LiquidationItem:
    debt = PendingDebt(Decimal("1000000.00"), Decimal("0.00"), Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="IMPUESTO_A_CARGO")
    return LiquidationItem(
        date=date(2026, 1, 1),
        concept="Impuesto de renta 2024",
        capital_base=Decimal("1000000.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
        rate_source="N/A",
    )


def test_round_trip_sin_renta_liquida_preserva_none():
    resultado = LiquidationResult(items=[_item_de_prueba()])

    reconstruido = deserializar_resultado(serializar_resultado(resultado))

    assert reconstruido.renta_liquida is None
    assert len(reconstruido.items) == 1


def test_round_trip_con_renta_liquida_preserva_el_resultado_completo():
    renta_liquida = RentaLiquidaGravableResult(
        ingresos_netos=Decimal("100000000.00"),
        renta_bruta=Decimal("60000000.00"),
        renta_liquida=Decimal("40000000.00"),
        hubo_perdida_liquida=False,
        renta_liquida_gravable=Decimal("35000000.00"),
    )
    resultado = LiquidationResult(items=[_item_de_prueba()], renta_liquida=renta_liquida)

    reconstruido = deserializar_resultado(serializar_resultado(resultado))

    assert reconstruido.renta_liquida == renta_liquida


def test_deserializar_snapshot_antiguo_sin_clave_renta_liquida_no_lanza_keyerror():
    # Snapshot como los que ya existen en bastium.db, guardados ANTES de este sprint --
    # no tienen la clave "renta_liquida" en el JSON. deserializar_resultado debe seguir
    # funcionando (regresion equivalente a la ya conocida en Sprint 23 con otras claves).
    import json
    snapshot_antiguo = json.dumps({"items": [
        {
            "date": "2026-01-01", "concept": "Abono a capital", "capital_base": "1000000.00",
            "interest_rate": "0.00", "interest_amount": "0.00", "indexation_amount": "0.00",
            "payment_amount": "0.00", "rate_source": "N/A",
            "balance": {
                "date": "2026-01-01",
                "debt": {"principal": "1000000.00", "interest": "0.00", "indexation": "0.00"},
                "event_type": "IMPUESTO_A_CARGO",
            },
        }
    ]})

    reconstruido = deserializar_resultado(snapshot_antiguo)

    assert reconstruido.renta_liquida is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/audit/test_serialization.py -v`
Expected: FAIL — `TypeError: LiquidationResult.__init__() got an unexpected keyword argument
'renta_liquida'`

- [ ] **Step 3: Add `"IMPUESTO_A_CARGO"` to `_capital_concepts`, and route `"SANCION_TRIBUTARIA"` to the indexation bucket**

In `app/engine/liquidation/engine.py`, línea 33, change:
```python
            "MULTA_SANCIONATORIA", "HONORARIOS_PROFESIONALES", "COSTAS_PROCESALES", "VACACIONES"
        }
```
to:
```python
            "MULTA_SANCIONATORIA", "HONORARIOS_PROFESIONALES", "COSTAS_PROCESALES", "VACACIONES",
            "IMPUESTO_A_CARGO"
        }
```

En el mismo archivo, `_process_event` (línea 120) solo reconoce el bucket de indexación para el string
literal `"INDEXATION"` — las 3 sanciones tributarias emiten `event_type="SANCION_TRIBUTARIA"` (Task 5),
que necesita caer en ese mismo bucket sin perder su propio nombre (para que quede correctamente
etiquetado en `RunningBalance.event_type`, usado por el historial de auditoría). Cambiar:
```python
        elif event.event_type == "INDEXATION":
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            indexation_amount = amount
            self._current_debt = BalanceEngine.add_indexation(self._current_debt, amount)
```
a:
```python
        elif event.event_type in ("INDEXATION", "SANCION_TRIBUTARIA"):
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            indexation_amount = amount
            self._current_debt = BalanceEngine.add_indexation(self._current_debt, amount)
```

Esto no es un set nuevo tipo `_indexation_concepts` (que sí habría sido un cambio estructural) — es
ensanchar una comparación de string literal existente a una tupla de dos strings literales, mínimo y
localizado en una sola línea.

- [ ] **Step 4: Add `renta_liquida` field to `LiquidationResult`**

Replace the full content of `app/engine/liquidation/result.py` with:

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from app.engine.liquidation.models import LiquidationItem, PendingDebt
from app.engine.tax.renta_liquida import RentaLiquidaGravableResult

@dataclass(frozen=True)
class LiquidationResult:
    """
    Representa el veredicto y cronología final del proceso de liquidación.
    Expone métodos para extraer métricas listas para interfaces y PDFs.

    `renta_liquida` (Sprint 15): resultado opcional de depurar_renta_liquida_gravable(),
    poblado solo por TributarioStrategy cuando el expediente tiene una obligacion
    "RENTA_LIQUIDA". No participa del balance de deuda (items/PendingDebt) -- es
    informativo, deliberadamente separado (ver design spec, seccion "Renta Liquida
    Gravable no se mezcla con el saldo de deuda").
    """
    items: List[LiquidationItem]
    renta_liquida: Optional[RentaLiquidaGravableResult] = None

    def total_interest_accrued(self) -> Decimal:
        return sum((item.interest_amount for item in self.items), Decimal("0.00"))

    def total_payments_applied(self) -> Decimal:
        return sum((item.payment_amount for item in self.items), Decimal("0.00"))

    def final_balance(self) -> PendingDebt:
        if not self.items:
            return PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
        return self.items[-1].balance.debt

    def is_empty(self) -> bool:
        return len(self.items) == 0
```

- [ ] **Step 5: Update `serialization.py` to serialize/deserialize `renta_liquida`**

Replace the full content of `app/engine/audit/serialization.py` with:

```python
import json
from dataclasses import asdict
from datetime import date
from decimal import Decimal

from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.engine.tax.renta_liquida import RentaLiquidaGravableResult


def _encode(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Tipo no serializable en snapshot de auditoría: {type(value)!r}")


def serializar_resultado(resultado: LiquidationResult) -> str:
    """Snapshot JSON exacto de un LiquidationResult, para reconstrucción sin recalcular."""
    items = [asdict(item) for item in resultado.items]
    renta_liquida = asdict(resultado.renta_liquida) if resultado.renta_liquida is not None else None
    return json.dumps(
        {"items": items, "renta_liquida": renta_liquida}, default=_encode, ensure_ascii=False
    )


def deserializar_resultado(json_str: str) -> LiquidationResult:
    """Reconstruye un LiquidationResult exactamente desde un snapshot de serializar_resultado.
    Usa .get() para 'renta_liquida' porque los snapshots guardados antes del Sprint 15 no
    tienen esa clave -- debe seguir reconstruyendo sin KeyError (misma cautela que ya motivo
    el bug de auditoria documentado en el Sprint 23)."""
    data = json.loads(json_str)
    items = [_item_desde_dict(item) for item in data["items"]]
    renta_liquida = _renta_liquida_desde_dict(data.get("renta_liquida"))
    return LiquidationResult(items=items, renta_liquida=renta_liquida)


def _item_desde_dict(data: dict) -> LiquidationItem:
    balance_data = data["balance"]
    debt_data = balance_data["debt"]

    debt = PendingDebt(
        principal=Decimal(debt_data["principal"]),
        interest=Decimal(debt_data["interest"]),
        indexation=Decimal(debt_data["indexation"]),
    )
    balance = RunningBalance(
        date=date.fromisoformat(balance_data["date"]),
        debt=debt,
        event_type=balance_data["event_type"],
    )
    return LiquidationItem(
        date=date.fromisoformat(data["date"]),
        concept=data["concept"],
        capital_base=Decimal(data["capital_base"]),
        interest_rate=Decimal(data["interest_rate"]),
        interest_amount=Decimal(data["interest_amount"]),
        indexation_amount=Decimal(data["indexation_amount"]),
        payment_amount=Decimal(data["payment_amount"]),
        balance=balance,
        rate_source=data["rate_source"],
    )


def _renta_liquida_desde_dict(data: dict | None) -> RentaLiquidaGravableResult | None:
    if data is None:
        return None
    return RentaLiquidaGravableResult(
        ingresos_netos=Decimal(data["ingresos_netos"]),
        renta_bruta=Decimal(data["renta_bruta"]),
        renta_liquida=Decimal(data["renta_liquida"]),
        hubo_perdida_liquida=data["hubo_perdida_liquida"],
        renta_liquida_gravable=Decimal(data["renta_liquida_gravable"]),
    )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/audit/test_serialization.py -v`
Expected: PASS (9 tests — 6 preexistentes + 3 nuevas)

- [ ] **Step 7: Run the full suite to confirm nothing else broke**

Run: `pytest -q`
Expected: all passing — `LiquidationResult(items=[...])` (positional/keyword sin `renta_liquida`) sigue
funcionando en todas las pruebas existentes porque el campo nuevo tiene default `None`.

- [ ] **Step 8: Commit**

```bash
git add app/engine/liquidation/engine.py app/engine/liquidation/result.py app/engine/audit/serialization.py tests/audit/test_serialization.py
git commit -m "feat: add optional renta_liquida field to LiquidationResult, wire IMPUESTO_A_CARGO capital concept"
```

---

### Task 5: `TributarioStrategy` (`app/services/area_strategy.py`)

**Files:**
- Modify: `app/services/area_strategy.py:1-23` (imports), `app/services/area_strategy.py:600` (agregar
  la clase al final del archivo)
- Modify: `app/engine/liquidation/registry.py:27-43` (registrar la estrategia)
- Test: `tests/services/test_area_strategy.py` (fixture + nueva clase `TestTributarioStrategy` + corregir
  `test_registry_expone_las_5_areas`)

- [ ] **Step 1: Write the failing tests**

En `tests/services/test_area_strategy.py`, cambiar el import de `area_strategy` (busca la línea con
`from app.services.area_strategy import (`) para incluir `TributarioStrategy`:

```python
from app.services.area_strategy import (
    CivilFamiliaStrategy,
    ComercialStrategy,
    HonorariosStrategy,
    LaboralStrategy,
    SancionatorioStrategy,
    TributarioStrategy,
)
```

Corregir `test_registry_expone_las_5_areas` (renombrarla y agregar `"TRIBUTARIO"`):

```python
def test_registry_expone_las_6_areas():
    areas = AreaRegistry.get_available_areas()
    assert set(areas.keys()) == {
        "CIVIL_FAMILIA",
        "COMERCIAL",
        "LABORAL",
        "SANCIONATORIO",
        "HONORARIOS",
        "TRIBUTARIO",
    }
```

Al final del archivo, agregar una nueva sección de pruebas:

```python
def _obligacion_tributaria(
    expediente_id=1,
    categoria="IMPUESTO_A_CARGO",
    fecha_origen=date(2024, 3, 1),
    valor=Decimal("0.00"),
    base_sancion_tributaria=None,
    meses_extemporaneidad=None,
    sancion_agravada=False,
    ingresos_brutos=None,
    devoluciones_rebajas_descuentos=None,
    costos=None,
    deducciones=None,
    rentas_exentas=None,
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Impuesto de renta 2024",
        categoria=categoria,
        fecha_origen=fecha_origen,
        valor=valor,
        tasa_efectiva_anual=Decimal("0.00"),
        base_sancion_tributaria=base_sancion_tributaria,
        meses_extemporaneidad=meses_extemporaneidad,
        sancion_agravada=sancion_agravada,
        ingresos_brutos=ingresos_brutos,
        devoluciones_rebajas_descuentos=devoluciones_rebajas_descuentos,
        costos=costos,
        deducciones=deducciones,
        rentas_exentas=rentas_exentas,
    )


class TestTributarioStrategy:
    def test_impuesto_a_cargo_sin_sanciones_ni_abonos_liquida_el_valor(self):
        obligacion = _obligacion_tributaria(categoria="IMPUESTO_A_CARGO", valor=Decimal("10000000.00"))

        resultado = TributarioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
        )

        assert resultado.final_balance().principal == Decimal("10000000.00")

    def test_sancion_extemporaneidad_liquida_el_monto_calculado(self):
        obligacion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD",
            base_sancion_tributaria=Decimal("10000000.00"),
            meses_extemporaneidad=2,
            fecha_origen=date(2024, 3, 1),
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
        )

        # 5% x 2 meses = 10% de 10,000,000 = 1,000,000 (por encima del piso de 10 UVT).
        assert resultado.final_balance().indexation == Decimal("1000000.00")

    def test_falta_categoria_no_reconocida_lanza_value_error(self):
        obligacion = _obligacion_tributaria(categoria="CATEGORIA_INEXISTENTE")

        with pytest.raises(ValueError):
            TributarioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
            )

    def test_falta_base_sancion_en_extemporaneidad_lanza_value_error(self):
        obligacion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD", base_sancion_tributaria=None, meses_extemporaneidad=2
        )

        with pytest.raises(ValueError):
            TributarioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
            )

    def test_obligacion_recurrente_lanza_value_error(self):
        obligacion = _obligacion_tributaria(categoria="IMPUESTO_A_CARGO", valor=Decimal("100.00"))
        obligacion.tipo = TipoObligacion.RECURRENTE

        with pytest.raises(ValueError):
            TributarioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
            )

    def test_orden_de_imputacion_sanciones_intereses_impuesto(self):
        # Impuesto a cargo de 1,000,000 y sancion de extemporaneidad de 1,000,000 (5% x 1
        # mes = 50,000, muy por debajo del piso de 10 UVT 2024 = 470,650.00, asi que la
        # sancion efectiva queda en 470,650.00), ambos con fecha_origen 2024-03-01. El abono
        # tambien cae el 2024-03-01 (mismo dia que fecha_corte) para que la acumulacion
        # automatica de interes (que corre por dias transcurridos) no aplique -- asi el
        # resultado es 100% aritmetica de imputacion, sin depender de tasas historicas de
        # usura para un rango de fechas.
        impuesto = _obligacion_tributaria(
            categoria="IMPUESTO_A_CARGO", valor=Decimal("1000000.00"), fecha_origen=date(2024, 3, 1)
        )
        sancion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD", base_sancion_tributaria=Decimal("1000000.00"),
            meses_extemporaneidad=1, fecha_origen=date(2024, 3, 1),
        )
        abono = Abono(
            id=1, obligacion_id=1, fecha=date(2024, 3, 1), monto=Decimal("500000.00"),
            referencia="Abono parcial",
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[impuesto, sancion], abonos=[abono], fecha_corte=date(2024, 3, 1)
        )

        saldo = resultado.final_balance()
        # El abono de 500,000 paga primero la sancion completa (470,650.00, bucket
        # 'indexation'), y el remanente (500,000 - 470,650 = 29,350) va al impuesto (bucket
        # 'principal', pagado de ultimo): 1,000,000 - 29,350 = 970,650.00. Sin intereses
        # (mismo dia, cero dias transcurridos), asi que el bucket 'interest' no interviene.
        assert saldo.indexation == Decimal("0.00")
        assert saldo.interest == Decimal("0.00")
        assert saldo.principal == Decimal("970650.00")

    def test_renta_liquida_no_genera_evento_y_queda_en_resultado_renta_liquida(self):
        obligacion = _obligacion_tributaria(
            categoria="RENTA_LIQUIDA",
            ingresos_brutos=Decimal("100000000.00"),
            devoluciones_rebajas_descuentos=Decimal("0.00"),
            costos=Decimal("40000000.00"),
            deducciones=Decimal("20000000.00"),
            rentas_exentas=Decimal("5000000.00"),
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
        )

        assert resultado.is_empty()
        assert resultado.renta_liquida is not None
        assert resultado.renta_liquida.renta_liquida_gravable == Decimal("35000000.00")
        assert resultado.final_balance().total() == Decimal("0.00")

    def test_dos_obligaciones_renta_liquida_en_el_mismo_expediente_lanza_value_error(self):
        renta_1 = _obligacion_tributaria(
            categoria="RENTA_LIQUIDA", ingresos_brutos=Decimal("1.00"),
            devoluciones_rebajas_descuentos=Decimal("0.00"), costos=Decimal("0.00"),
            deducciones=Decimal("0.00"), rentas_exentas=Decimal("0.00"),
        )
        renta_2 = _obligacion_tributaria(
            categoria="RENTA_LIQUIDA", ingresos_brutos=Decimal("2.00"),
            devoluciones_rebajas_descuentos=Decimal("0.00"), costos=Decimal("0.00"),
            deducciones=Decimal("0.00"), rentas_exentas=Decimal("0.00"),
        )

        with pytest.raises(ValueError):
            TributarioStrategy().liquidar(
                obligaciones=[renta_1, renta_2], abonos=[], fecha_corte=date(2024, 3, 1)
            )
```

`Abono` ya está importado en este archivo (línea 133: `from database.models import AreaDerecho, Abono,
Expediente, Obligacion, TipoObligacion`) — no requiere cambios.

La fixture `_parametros_legales_en_memoria` ya siembra `_UVT_POR_ANIO` (líneas 79-83, agregado en el
Sprint 14) — no requiere cambios ahí tampoco. Agrega el seed de las 4 claves nuevas de sanciones
inmediatamente después de ese bloque (después de la línea 83, antes del loop de
`_IPC_INDICE_ACUMULADO` en la línea 84):

```python
    for clave, valor in {
        "EXTEMPORANEIDAD_PCT_MENSUAL": Decimal("5"),
        "INEXACTITUD_PCT": Decimal("160"),
        "INEXACTITUD_AGRAVADA_PCT": Decimal("200"),
        "ERROR_ARITMETICO_PCT": Decimal("30"),
    }.items():
        session.add(ParametroLegal(
            clave=clave, valor=valor, vigente_desde=_date(1900, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/services/test_area_strategy.py -v -k Tributario`
Expected: FAIL — `ImportError: cannot import name 'TributarioStrategy'`

- [ ] **Step 3: Add imports to `area_strategy.py`**

En `app/services/area_strategy.py`, agregar a los imports existentes (después de la línea 23,
`from app.services.parametro_service import get_parametro`):

```python
from dataclasses import replace
from app.engine.tax.moratory_interest import construir_rate_provider_moratorio_tributario
from app.engine.tax.renta_liquida import depurar_renta_liquida_gravable
from app.engine.tax.sanciones import (
    calcular_sancion_error_aritmetico,
    calcular_sancion_extemporaneidad,
    calcular_sancion_inexactitud,
)
```

- [ ] **Step 4: Add `TributarioStrategy` at the end of `area_strategy.py`**

Al final del archivo (después de la línea 600, cierre de `HonorariosStrategy`), agregar:

```python


class TributarioStrategy(AreaStrategy):
    """
    Area Tributario (cierre del Sprint 11b): impuesto a cargo, 3 sanciones (extemporaneidad,
    inexactitud, error aritmetico) y Renta Liquida Gravable informativa.

    Reutiliza el motor generico de liquidacion (UniversalLiquidationService/LiquidationCore)
    en vez de un motor de imputacion dedicado: el impuesto a cargo cae en el bucket
    'principal' (event_type = obligacion.categoria = "IMPUESTO_A_CARGO", agregado a
    _capital_concepts igual que cada area anterior), las 3 sanciones se normalizan a un unico
    event_type "SANCION_TRIBUTARIA" que cae en el bucket 'indexation'. El orden de pago que
    ya aplica AllocationEngine (indexacion -> interes -> capital) coincide exactamente con el
    orden exigido para tributario (sanciones -> intereses -> impuesto) -- ver design spec,
    seccion "Arquitectura".

    El interes automatico (E.T. art. 635, nunca pactado) reutiliza
    construir_rate_provider_moratorio_tributario del Sprint 11a.

    "RENTA_LIQUIDA" no genera ningun evento de causacion -- es informativo (base gravable,
    no una deuda exigible) y se adjunta aparte en LiquidationResult.renta_liquida. Un
    expediente admite como maximo una obligacion "RENTA_LIQUIDA" (un solo periodo gravable
    por liquidacion).
    """

    soporta_indexacion_ipc = False

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        obligaciones_renta_liquida = [o for o in obligaciones if o.categoria == "RENTA_LIQUIDA"]
        if len(obligaciones_renta_liquida) > 1:
            raise ValueError(
                "Un expediente tributario admite una sola obligacion 'RENTA_LIQUIDA' "
                "(un solo periodo gravable por liquidacion)."
            )

        obligaciones_deuda = [o for o in obligaciones if o.categoria != "RENTA_LIQUIDA"]
        for obligacion in obligaciones_deuda:
            self._validar_obligacion_tributaria(obligacion)

        eventos_causacion = [self._evento_de_obligacion(o) for o in obligaciones_deuda]

        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos
        ]

        rate_provider = self._construir_rate_provider(obligaciones_deuda, fecha_corte)

        service = UniversalLiquidationService()
        resultado = service.liquidar(
            eventos_causacion=eventos_causacion,
            pagos=pagos,
            fecha_corte=fecha_corte,
            rate_provider=rate_provider,
        )

        if obligaciones_renta_liquida:
            obligacion_renta = obligaciones_renta_liquida[0]
            renta_liquida = depurar_renta_liquida_gravable(
                ingresos_brutos=obligacion_renta.ingresos_brutos,
                devoluciones_rebajas_descuentos=obligacion_renta.devoluciones_rebajas_descuentos,
                costos=obligacion_renta.costos,
                deducciones=obligacion_renta.deducciones,
                rentas_exentas=obligacion_renta.rentas_exentas,
            )
            resultado = replace(resultado, renta_liquida=renta_liquida)

        return resultado

    def _validar_obligacion_tributaria(self, obligacion) -> None:
        if obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion tributaria '{obligacion.concepto}' debe ser PUNTUAL "
                f"(un hecho tributario es un evento unico, no admite RECURRENTE)."
            )

        if obligacion.categoria == "IMPUESTO_A_CARGO":
            if obligacion.valor is None or obligacion.valor <= Decimal("0.00"):
                raise ValueError(
                    f"El impuesto a cargo '{obligacion.concepto}' debe tener 'valor' mayor que cero."
                )
            return

        if obligacion.categoria == "SANCION_EXTEMPORANEIDAD":
            if obligacion.base_sancion_tributaria is None or obligacion.meses_extemporaneidad is None:
                raise ValueError(
                    f"La sancion por extemporaneidad '{obligacion.concepto}' necesita "
                    f"'base_sancion_tributaria' y 'meses_extemporaneidad'."
                )
            return

        if obligacion.categoria == "SANCION_INEXACTITUD":
            if obligacion.base_sancion_tributaria is None:
                raise ValueError(
                    f"La sancion por inexactitud '{obligacion.concepto}' necesita "
                    f"'base_sancion_tributaria' (la diferencia entre el saldo determinado y el declarado)."
                )
            return

        if obligacion.categoria == "SANCION_ERROR_ARITMETICO":
            if obligacion.base_sancion_tributaria is None:
                raise ValueError(
                    f"La sancion por error aritmetico '{obligacion.concepto}' necesita "
                    f"'base_sancion_tributaria' (la diferencia generada por el error)."
                )
            return

        raise ValueError(
            f"Categoria tributaria desconocida: '{obligacion.categoria}'."
        )

    def _evento_de_obligacion(self, obligacion) -> Event:
        if obligacion.categoria == "IMPUESTO_A_CARGO":
            return Event(
                date=obligacion.fecha_origen,
                payload={"amount": obligacion.valor, "label": obligacion.concepto},
                event_type=obligacion.categoria,
            )

        monto_sancion = self._calcular_monto_sancion(obligacion)
        return Event(
            date=obligacion.fecha_origen,
            payload={"amount": monto_sancion, "label": obligacion.concepto},
            event_type="SANCION_TRIBUTARIA",
        )

    def _calcular_monto_sancion(self, obligacion) -> Decimal:
        if obligacion.categoria == "SANCION_EXTEMPORANEIDAD":
            return calcular_sancion_extemporaneidad(
                impuesto_a_cargo=obligacion.base_sancion_tributaria,
                meses_o_fraccion=obligacion.meses_extemporaneidad,
                fecha_referencia=obligacion.fecha_origen,
            )
        if obligacion.categoria == "SANCION_INEXACTITUD":
            return calcular_sancion_inexactitud(
                diferencia=obligacion.base_sancion_tributaria,
                agravada=bool(obligacion.sancion_agravada),
                fecha_referencia=obligacion.fecha_origen,
            )
        # SANCION_ERROR_ARITMETICO (unica categoria de sancion restante, ya validada arriba)
        return calcular_sancion_error_aritmetico(
            diferencia=obligacion.base_sancion_tributaria,
            fecha_referencia=obligacion.fecha_origen,
        )

    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        if not obligaciones:
            return MemoryRateProvider()
        fecha_mas_antigua = min(o.fecha_origen for o in obligaciones)
        return construir_rate_provider_moratorio_tributario(fecha_mas_antigua, fecha_corte)
```

- [ ] **Step 5: Register `TributarioStrategy` in `AreaRegistry`**

En `app/engine/liquidation/registry.py`, cambiar el import (línea 28):
```python
    from app.services.area_strategy import (
        CivilFamiliaStrategy,
        ComercialStrategy,
        HonorariosStrategy,
        LaboralStrategy,
        SancionatorioStrategy,
    )
```
a:
```python
    from app.services.area_strategy import (
        CivilFamiliaStrategy,
        ComercialStrategy,
        HonorariosStrategy,
        LaboralStrategy,
        SancionatorioStrategy,
        TributarioStrategy,
    )
```

Y agregar, después de la línea 42 (`AreaRegistry.register("HONORARIOS", ...)`):

```python
    AreaRegistry.register(
        "TRIBUTARIO", "Impuesto a cargo, sanciones tributarias y renta liquida", TributarioStrategy
    )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/services/test_area_strategy.py -v`
Expected: PASS (todas, incluyendo las de `TestTributarioStrategy` y `test_registry_expone_las_6_areas`).

- [ ] **Step 7: Commit**

```bash
git add app/services/area_strategy.py app/engine/liquidation/registry.py tests/services/test_area_strategy.py
git commit -m "feat: add TributarioStrategy (impuesto, sanciones, imputacion, renta liquida)"
```

---

### Task 6: Reporting — mostrar el bucket de sanciones/indexación (GUI, PDF, Word)

**Files:**
- Modify: `app/views/liquidaciones.py:37-39` (header + columna), `app/views/liquidaciones.py:67-75`
  (población de filas)
- Modify: `app/reports/pdf.py:101-107` (fila de resumen), `app/reports/pdf.py:128-143` (columna de
  cronología)
- Modify: `app/reports/word.py:31-37` (fila de resumen), `app/reports/word.py:54-72` (columna de
  cronología)
- Test: `tests/views/test_liquidaciones.py`, `tests/reports/test_pdf.py` (ya tiene los datos, solo hay
  que confirmar), `tests/reports/test_word.py` (nuevo test de contenido)

- [ ] **Step 1: Write the failing GUI test**

En `tests/views/test_liquidaciones.py`, modifica `_resultado_de_prueba()` para que el item tenga un
`indexation_amount` distinto de cero, y agrega un test nuevo:

```python
def _resultado_de_prueba() -> LiquidationResult:
    debt = PendingDebt(principal=Decimal("427900.00"), interest=Decimal("1200.50"), indexation=Decimal("300.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="LIQUIDATION_CUTOFF")
    item = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Corte final de liquidacion",
        capital_base=Decimal("427900.00"),
        interest_rate=Decimal("6.00"),
        interest_amount=Decimal("1200.50"),
        indexation_amount=Decimal("300.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
    )
    return LiquidationResult(items=[item])
```

(Reemplaza el `indexation=Decimal("0.00")`/`indexation_amount=Decimal("0.00")` originales por
`Decimal("300.00")` en ambos lugares de esa función.)

Agrega este test nuevo después de `test_muestra_una_fila_por_item_de_liquidacion`:

```python
def test_muestra_columna_de_indexacion_sanciones(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert view.tabla.columnCount() == 8
    header_indexacion = view.tabla.horizontalHeaderItem(5).text()
    assert "ndexaci" in header_indexacion or "anci" in header_indexacion
    assert view.tabla.item(0, 5).text() == "300.00"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/views/test_liquidaciones.py -v -k indexacion`
Expected: FAIL — `AssertionError: assert 7 == 8` (la tabla todavía tiene 7 columnas)

- [ ] **Step 3: Update `liquidaciones.py` — header y columna nueva**

In `app/views/liquidaciones.py`, cambiar (líneas 37-39):
```python
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "Concepto", "Capital base", "Tasa %", "Interes", "Pago", "Saldo"]
        )
```
a:
```python
        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "Concepto", "Capital base", "Tasa %", "Interes", "Indexacion/Sanciones", "Pago", "Saldo"]
        )
```

Y cambiar el bucle de población de filas (líneas 67-75):
```python
        self.tabla.setRowCount(len(resultado.items))
        for fila, item in enumerate(resultado.items):
            self.tabla.setItem(fila, 0, QTableWidgetItem(item.date.isoformat()))
            self.tabla.setItem(fila, 1, QTableWidgetItem(item.concept))
            self.tabla.setItem(fila, 2, QTableWidgetItem(str(item.capital_base)))
            self.tabla.setItem(fila, 3, QTableWidgetItem(str(item.interest_rate)))
            self.tabla.setItem(fila, 4, QTableWidgetItem(str(item.interest_amount)))
            self.tabla.setItem(fila, 5, QTableWidgetItem(str(item.payment_amount)))
            self.tabla.setItem(fila, 6, QTableWidgetItem(str(item.balance.debt.total())))
```
a:
```python
        self.tabla.setRowCount(len(resultado.items))
        for fila, item in enumerate(resultado.items):
            self.tabla.setItem(fila, 0, QTableWidgetItem(item.date.isoformat()))
            self.tabla.setItem(fila, 1, QTableWidgetItem(item.concept))
            self.tabla.setItem(fila, 2, QTableWidgetItem(str(item.capital_base)))
            self.tabla.setItem(fila, 3, QTableWidgetItem(str(item.interest_rate)))
            self.tabla.setItem(fila, 4, QTableWidgetItem(str(item.interest_amount)))
            self.tabla.setItem(fila, 5, QTableWidgetItem(str(item.indexation_amount)))
            self.tabla.setItem(fila, 6, QTableWidgetItem(str(item.payment_amount)))
            self.tabla.setItem(fila, 7, QTableWidgetItem(str(item.balance.debt.total())))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/views/test_liquidaciones.py -v`
Expected: PASS (todas)

- [ ] **Step 5: Update `pdf.py` — fila de resumen y columna de cronología**

In `app/reports/pdf.py`, cambiar `filas_resumen` (líneas 101-107):
```python
        filas_resumen = [
            ("Total Abonos Aplicados", summary["total_abonos"]),
            ("Intereses Generados", summary["total_intereses_generados"]),
            ("Saldo Final Capital", summary["saldo_final_capital"]),
            ("Saldo Final Intereses", summary["saldo_final_intereses"]),
            ("GRAN TOTAL ADEUDADO", summary["gran_total_adeudado"]),
        ]
```
a:
```python
        filas_resumen = [
            ("Total Abonos Aplicados", summary["total_abonos"]),
            ("Intereses Generados", summary["total_intereses_generados"]),
            ("Saldo Final Capital", summary["saldo_final_capital"]),
            ("Saldo Final Intereses", summary["saldo_final_intereses"]),
            ("Saldo Final Indexación/Sanciones", summary["saldo_final_indexacion"]),
            ("GRAN TOTAL ADEUDADO", summary["gran_total_adeudado"]),
        ]
```

Y cambiar la tabla de cronología (líneas 128-143):
```python
        datos_cronologia = [[
            "Fecha", "Concepto", "Base Capital", "Tasa", "Interés", "Pago",
            "Saldo Capital", "Saldo Interés", "Saldo Total",
        ]]
        for fila in table_data:
            datos_cronologia.append([
                fila["fecha"],
                fila["concepto"],
                fila["base_capital"],
                fila["tasa"],
                fila["interes"],
                fila["pago"],
                fila["saldo_capital"],
                fila["saldo_interes"],
                fila["saldo_total"],
            ])
```
a:
```python
        datos_cronologia = [[
            "Fecha", "Concepto", "Base Capital", "Tasa", "Interés", "Indexación/Sanciones", "Pago",
            "Saldo Capital", "Saldo Interés", "Saldo Total",
        ]]
        for fila in table_data:
            datos_cronologia.append([
                fila["fecha"],
                fila["concepto"],
                fila["base_capital"],
                fila["tasa"],
                fila["interes"],
                fila["indexacion"],
                fila["pago"],
                fila["saldo_capital"],
                fila["saldo_interes"],
                fila["saldo_total"],
            ])
```

- [ ] **Step 6: Update `word.py` — fila de resumen y columna de cronología**

In `app/reports/word.py`, cambiar `filas_resumen` (líneas 31-37):
```python
        filas_resumen = [
            ("Total Abonos Aplicados", summary["total_abonos"]),
            ("Intereses Generados", summary["total_intereses_generados"]),
            ("Saldo Final Capital", summary["saldo_final_capital"]),
            ("Saldo Final Intereses", summary["saldo_final_intereses"]),
            ("GRAN TOTAL ADEUDADO", summary["gran_total_adeudado"]),
        ]
```
a:
```python
        filas_resumen = [
            ("Total Abonos Aplicados", summary["total_abonos"]),
            ("Intereses Generados", summary["total_intereses_generados"]),
            ("Saldo Final Capital", summary["saldo_final_capital"]),
            ("Saldo Final Intereses", summary["saldo_final_intereses"]),
            ("Saldo Final Indexación/Sanciones", summary["saldo_final_indexacion"]),
            ("GRAN TOTAL ADEUDADO", summary["gran_total_adeudado"]),
        ]
```

Y cambiar la tabla de cronología (líneas 54-72):
```python
        columnas_cronologia = [
            "Fecha", "Concepto", "Base Capital", "Tasa", "Interés", "Pago",
            "Saldo Capital", "Saldo Interés", "Saldo Total",
        ]
        tabla_cronologia = documento.add_table(rows=1, cols=len(columnas_cronologia))
        tabla_cronologia.style = "Table Grid"
        for celda, texto in zip(tabla_cronologia.rows[0].cells, columnas_cronologia):
            celda.text = texto
        for fila_datos in table_data:
            celdas_fila = tabla_cronologia.add_row().cells
            celdas_fila[0].text = fila_datos["fecha"]
            celdas_fila[1].text = fila_datos["concepto"]
            celdas_fila[2].text = fila_datos["base_capital"]
            celdas_fila[3].text = fila_datos["tasa"]
            celdas_fila[4].text = fila_datos["interes"]
            celdas_fila[5].text = fila_datos["pago"]
            celdas_fila[6].text = fila_datos["saldo_capital"]
            celdas_fila[7].text = fila_datos["saldo_interes"]
            celdas_fila[8].text = fila_datos["saldo_total"]
```
a:
```python
        columnas_cronologia = [
            "Fecha", "Concepto", "Base Capital", "Tasa", "Interés", "Indexación/Sanciones", "Pago",
            "Saldo Capital", "Saldo Interés", "Saldo Total",
        ]
        tabla_cronologia = documento.add_table(rows=1, cols=len(columnas_cronologia))
        tabla_cronologia.style = "Table Grid"
        for celda, texto in zip(tabla_cronologia.rows[0].cells, columnas_cronologia):
            celda.text = texto
        for fila_datos in table_data:
            celdas_fila = tabla_cronologia.add_row().cells
            celdas_fila[0].text = fila_datos["fecha"]
            celdas_fila[1].text = fila_datos["concepto"]
            celdas_fila[2].text = fila_datos["base_capital"]
            celdas_fila[3].text = fila_datos["tasa"]
            celdas_fila[4].text = fila_datos["interes"]
            celdas_fila[5].text = fila_datos["indexacion"]
            celdas_fila[6].text = fila_datos["pago"]
            celdas_fila[7].text = fila_datos["saldo_capital"]
            celdas_fila[8].text = fila_datos["saldo_interes"]
            celdas_fila[9].text = fila_datos["saldo_total"]
```

- [ ] **Step 7: Add a content-verification test for Word (python-docx can read its own output)**

Agrega este test a `tests/reports/test_word.py`:

```python
def test_generate_incluye_columna_de_indexacion_sanciones(tmp_path):
    ruta = tmp_path / "liquidacion.docx"
    generador = WordReportGenerator(str(ruta))

    generador.generate("LIQUIDACIÓN DE OBLIGACIONES — ÁREA TRIBUTARIO", _summary(), _table_data())

    documento = Document(str(ruta))
    tabla_cronologia = documento.tables[1]
    encabezados = [celda.text for celda in tabla_cronologia.rows[0].cells]
    assert "Indexación/Sanciones" in encabezados
    fila_datos = [celda.text for celda in tabla_cronologia.rows[1].cells]
    assert "$0.00" in fila_datos
```

(`_summary()`/`_table_data()` en ese archivo ya incluyen `saldo_final_indexacion`/`indexacion` — ver
`tests/reports/test_word.py` líneas 7-28 — no hace falta modificarlas.)

- [ ] **Step 8: Run tests to verify they pass**

Run: `pytest tests/views/test_liquidaciones.py tests/reports/ -v`
Expected: PASS (todas)

- [ ] **Step 9: Run the full suite to confirm nothing else broke**

Run: `pytest -q`
Expected: all passing.

- [ ] **Step 10: Commit**

```bash
git add app/views/liquidaciones.py app/reports/pdf.py app/reports/word.py tests/views/test_liquidaciones.py tests/reports/test_word.py
git commit -m "fix: surface the indexacion/sanciones bucket in GUI table, PDF and Word reports"
```

---

### Task 7: Formulario de obligación (`app/views/obligaciones.py`)

**Files:**
- Modify: `app/views/obligaciones.py` (varios puntos: imports, widgets nuevos, visibilidad, `guardar()`)
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Write the failing tests**

Agrega estos tests al final de `tests/views/test_obligaciones.py` (y agrega `CATEGORIAS_TRIBUTARIO` /
`AreaDerecho.TRIBUTARIO` a los imports existentes si hace falta — confirma primero qué ya está
importado):

```python
def test_guarda_obligacion_tributaria_impuesto_a_cargo(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    dialog.combo_categoria.setCurrentIndex(0)  # IMPUESTO_A_CARGO
    dialog.campo_concepto.setText("Impuesto de renta 2024")
    dialog.campo_valor.setText("10000000.00")
    dialog.campo_fecha_origen.setDate(date(2024, 3, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.categoria == "IMPUESTO_A_CARGO"
    assert guardada.valor == Decimal("10000000.00")
    session.close()


def test_guarda_sancion_extemporaneidad_con_meses_de_atraso(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    indice = dialog.combo_categoria.findData("SANCION_EXTEMPORANEIDAD")
    dialog.combo_categoria.setCurrentIndex(indice)
    dialog.campo_concepto.setText("Sancion extemporaneidad renta 2024")
    dialog.campo_base_sancion.setText("10000000.00")
    dialog.campo_meses_extemporaneidad.setValue(2)
    dialog.campo_fecha_origen.setDate(date(2024, 3, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.categoria == "SANCION_EXTEMPORANEIDAD"
    assert guardada.base_sancion_tributaria == Decimal("10000000.00")
    assert guardada.meses_extemporaneidad == 2
    session.close()


def test_guarda_sancion_inexactitud_agravada(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    indice = dialog.combo_categoria.findData("SANCION_INEXACTITUD")
    dialog.combo_categoria.setCurrentIndex(indice)
    dialog.campo_concepto.setText("Sancion inexactitud renta 2024")
    dialog.campo_base_sancion.setText("5000000.00")
    dialog.check_sancion_agravada.setChecked(True)
    dialog.campo_fecha_origen.setDate(date(2024, 3, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.categoria == "SANCION_INEXACTITUD"
    assert guardada.sancion_agravada is True
    session.close()


def test_guarda_renta_liquida_con_los_5_campos(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    indice = dialog.combo_categoria.findData("RENTA_LIQUIDA")
    dialog.combo_categoria.setCurrentIndex(indice)
    dialog.campo_concepto.setText("Renta liquida gravable 2024")
    dialog.campo_ingresos_brutos.setText("100000000.00")
    dialog.campo_devoluciones.setText("0.00")
    dialog.campo_costos.setText("40000000.00")
    dialog.campo_deducciones.setText("20000000.00")
    dialog.campo_rentas_exentas.setText("5000000.00")
    dialog.campo_fecha_origen.setDate(date(2024, 3, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.categoria == "RENTA_LIQUIDA"
    assert guardada.ingresos_brutos == Decimal("100000000.00")
    assert guardada.rentas_exentas == Decimal("5000000.00")
    session.close()


def test_campos_de_sancion_ocultos_al_elegir_impuesto_a_cargo(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    indice = dialog.combo_categoria.findData("IMPUESTO_A_CARGO")
    dialog.combo_categoria.setCurrentIndex(indice)

    assert dialog.campo_valor.isVisible()
    assert not dialog.campo_base_sancion.isVisible()
    assert not dialog.campo_ingresos_brutos.isVisible()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/views/test_obligaciones.py -v -k tributari`
Expected: FAIL — `AttributeError: 'ObligacionFormDialog' object has no attribute 'campo_base_sancion'`

- [ ] **Step 3: Add the `CATEGORIAS_TRIBUTARIO` import and new widgets**

In `app/views/obligaciones.py`, cambiar el import (línea 18):
```python
from app.core.constants import (
    CATEGORIAS_CIVIL_FAMILIA,
    CATEGORIAS_COMERCIAL,
    CATEGORIAS_HONORARIOS,
    CATEGORIAS_LABORAL,
    CATEGORIAS_SANCIONATORIO,
)
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
```

En el `__init__`, línea 37, cambiar:
```python
        if self._area not in ("SANCIONATORIO", "HONORARIOS", "LABORAL"):
```
a:
```python
        if self._area not in ("SANCIONATORIO", "HONORARIOS", "LABORAL", "TRIBUTARIO"):
```

Línea 45-51, cambiar el diccionario `categorias_por_area`:
```python
        categorias_por_area = {
            "COMERCIAL": CATEGORIAS_COMERCIAL,
            "SANCIONATORIO": CATEGORIAS_SANCIONATORIO,
            "HONORARIOS": CATEGORIAS_HONORARIOS,
            "LABORAL": CATEGORIAS_LABORAL,
        }
```
a:
```python
        categorias_por_area = {
            "COMERCIAL": CATEGORIAS_COMERCIAL,
            "SANCIONATORIO": CATEGORIAS_SANCIONATORIO,
            "HONORARIOS": CATEGORIAS_HONORARIOS,
            "LABORAL": CATEGORIAS_LABORAL,
            "TRIBUTARIO": CATEGORIAS_TRIBUTARIO,
        }
```

Después de la línea 85 (`self.check_aplica_indexacion_ipc = QCheckBox(...)`), agregar los widgets nuevos:

```python
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
```

- [ ] **Step 4: Add the new fields to the form layout**

Después de la línea `self.layout_formulario.addRow(self.check_aplica_indexacion_ipc)` (línea 118),
agregar:

```python
        self.layout_formulario.addRow("Base de la sancion (impuesto a cargo o diferencia)", self.campo_base_sancion)
        self.layout_formulario.addRow("Meses o fraccion de atraso (extemporaneidad)", self.campo_meses_extemporaneidad)
        self.layout_formulario.addRow(self.check_sancion_agravada)
        self.layout_formulario.addRow("Ingresos brutos (Renta liquida)", self.campo_ingresos_brutos)
        self.layout_formulario.addRow("Devoluciones/rebajas/descuentos (Renta liquida)", self.campo_devoluciones)
        self.layout_formulario.addRow("Costos (Renta liquida)", self.campo_costos)
        self.layout_formulario.addRow("Deducciones (Renta liquida)", self.campo_deducciones)
        self.layout_formulario.addRow("Rentas exentas (Renta liquida)", self.campo_rentas_exentas)
```

- [ ] **Step 5: Add the `es_tributario` visibility rules**

Cambiar (líneas 125-146):
```python
        es_comercial = self._area == "COMERCIAL"
        es_sancionatorio = self._area == "SANCIONATORIO"
        es_honorarios = self._area == "HONORARIOS"
        es_laboral = self._area == "LABORAL"

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

        # "Valor" no aplica a Sancionatorio/Honorarios: el monto se calcula a partir de
        # los campos de arriba (cantidad_smlmv_uvt, o honorarios+cuota litis+costas).
        self.campo_valor.setVisible(not es_sancionatorio and not es_honorarios)

        # Laboral es siempre PUNTUAL (ver combo_tipo arriba) y no usa tasa efectiva
        # anual (la liquidacion no es un interes compuesto) -- se ocultan combo_tipo
        # y campo_tasa, y se muestran los campos propios de contrato laboral.
        self.combo_tipo.setVisible(not es_laboral)
        self.campo_tasa.setVisible(not es_laboral)
        self.campo_fecha_fin.setVisible(es_laboral)
        self.check_pagada.setVisible(es_laboral)
```
a:
```python
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

        # "Valor" no aplica a Sancionatorio/Honorarios/Tributario (salvo IMPUESTO_A_CARGO,
        # ver _actualizar_campos_tributario): el monto se calcula a partir de otros campos.
        self.campo_valor.setVisible(not es_sancionatorio and not es_honorarios and not es_tributario)

        # Laboral y Tributario son siempre PUNTUAL y no usan tasa efectiva anual pactada
        # (Tributario: el interes es automatico, E.T. art. 635, nunca se pacta).
        self.combo_tipo.setVisible(not es_laboral and not es_tributario)
        self.campo_tasa.setVisible(not es_laboral and not es_tributario)
        self.campo_fecha_fin.setVisible(es_laboral)
        self.check_pagada.setVisible(es_laboral)

        self.campo_base_sancion.setVisible(False)
        self.campo_meses_extemporaneidad.setVisible(False)
        self.check_sancion_agravada.setVisible(False)
        self.campo_ingresos_brutos.setVisible(False)
        self.campo_devoluciones.setVisible(False)
        self.campo_costos.setVisible(False)
        self.campo_deducciones.setVisible(False)
        self.campo_rentas_exentas.setVisible(False)
```

- [ ] **Step 6: Add `_actualizar_campos_tributario` and wire it up**

Después del método `_actualizar_visibilidad_trm` (antes de `_actualizar_campos_visibles`, línea 181),
agregar:

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

Y conectar la señal (junto a los otros `.connect()` cerca del final del `__init__`, línea 168-170):
```python
        self.combo_tipo.currentIndexChanged.connect(self._actualizar_campos_visibles)
        self.check_pagada.stateChanged.connect(self._actualizar_campos_visibles)
        self.combo_moneda.currentIndexChanged.connect(self._actualizar_visibilidad_trm)
```
a:
```python
        self.combo_tipo.currentIndexChanged.connect(self._actualizar_campos_visibles)
        self.check_pagada.stateChanged.connect(self._actualizar_campos_visibles)
        self.combo_moneda.currentIndexChanged.connect(self._actualizar_visibilidad_trm)
        self.combo_categoria.currentIndexChanged.connect(self._actualizar_campos_tributario)
```

Y llamarlo una vez al final del `__init__`, junto a las otras llamadas iniciales (línea 172-173):
```python
        self._actualizar_campos_visibles()
        self._actualizar_visibilidad_trm()
```
a:
```python
        self._actualizar_campos_visibles()
        self._actualizar_visibilidad_trm()
        self._actualizar_campos_tributario()
```

- [ ] **Step 7: Add `_guardar_tributario` and wire it into `guardar()`**

Cambiar el inicio de `guardar()` (línea 195-197):
```python
    def guardar(self) -> int:
        if self._area == "LABORAL":
            return self._guardar_laboral()
```
a:
```python
    def guardar(self) -> int:
        if self._area == "LABORAL":
            return self._guardar_laboral()
        if self._area == "TRIBUTARIO":
            return self._guardar_tributario()
```

Y agregar el método nuevo, después de `_guardar_laboral` (antes de `_guardar_y_cerrar`, línea 345):

```python
    def _guardar_tributario(self) -> int:
        categoria = self.combo_categoria.currentData()

        qdate_origen = self.campo_fecha_origen.date()
        fecha_origen = date(qdate_origen.year(), qdate_origen.month(), qdate_origen.day())

        valor = Decimal("0.00")
        base_sancion = None
        meses_extemporaneidad = None
        sancion_agravada = False
        ingresos_brutos = None
        devoluciones = None
        costos = None
        deducciones = None
        rentas_exentas = None

        if categoria == "IMPUESTO_A_CARGO":
            try:
                valor = Decimal(self.campo_valor.text())
            except InvalidOperation as error:
                raise ValueError("El valor del impuesto a cargo debe ser un numero valido.") from error

        elif categoria == "SANCION_EXTEMPORANEIDAD":
            try:
                base_sancion = Decimal(self.campo_base_sancion.text())
            except InvalidOperation as error:
                raise ValueError("La base de la sancion debe ser un numero valido.") from error
            meses_extemporaneidad = self.campo_meses_extemporaneidad.value()

        elif categoria in ("SANCION_INEXACTITUD", "SANCION_ERROR_ARITMETICO"):
            try:
                base_sancion = Decimal(self.campo_base_sancion.text())
            except InvalidOperation as error:
                raise ValueError("La base de la sancion debe ser un numero valido.") from error
            if categoria == "SANCION_INEXACTITUD":
                sancion_agravada = self.check_sancion_agravada.isChecked()

        elif categoria == "RENTA_LIQUIDA":
            try:
                ingresos_brutos = Decimal(self.campo_ingresos_brutos.text())
                devoluciones = Decimal(self.campo_devoluciones.text())
                costos = Decimal(self.campo_costos.text())
                deducciones = Decimal(self.campo_deducciones.text())
                rentas_exentas = Decimal(self.campo_rentas_exentas.text())
            except InvalidOperation as error:
                raise ValueError(
                    "Los 5 campos de renta liquida gravable deben ser numeros validos."
                ) from error

        session = session_module.get_session()
        obligacion = Obligacion(
            expediente_id=self._expediente_id,
            tipo=TipoObligacion.PUNTUAL,
            concepto=self.campo_concepto.text().strip(),
            categoria=categoria,
            fecha_origen=fecha_origen,
            valor=valor,
            tasa_efectiva_anual=Decimal("0.00"),
            base_sancion_tributaria=base_sancion,
            meses_extemporaneidad=meses_extemporaneidad,
            sancion_agravada=sancion_agravada,
            ingresos_brutos=ingresos_brutos,
            devoluciones_rebajas_descuentos=devoluciones,
            costos=costos,
            deducciones=deducciones,
            rentas_exentas=rentas_exentas,
        )
        session.add(obligacion)
        session.commit()
        obligacion_id = obligacion.id
        session.close()
        return obligacion_id
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `pytest tests/views/test_obligaciones.py -v`
Expected: PASS (todas)

- [ ] **Step 9: Run the full suite to confirm nothing else broke**

Run: `pytest -q`
Expected: all passing.

- [ ] **Step 10: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "feat: add Tributario fields to the obligation form (impuesto, sanciones, renta liquida)"
```

---

### Task 8: Documentación — `README.md` y `docs/GUIA_USUARIO.md`

**Files:**
- Modify: `README.md` (estado actual, lista de áreas operables)
- Modify: `docs/GUIA_USUARIO.md` (sección 6 tabla de áreas, nueva sección "5.X Agregar una obligación
  tributaria", sección 8 pendientes)

No hay tests en esta tarea (solo documentación). Verificar releyendo cada sección después de editar.

- [ ] **Step 1: Read the current content of both files first**

Ejecuta `grep -n "Tributario\|TRIBUTARIO\|Sprint 11\|Sprint 15" README.md docs/GUIA_USUARIO.md` para
ubicar el texto exacto actual antes de editar (puede haber cambiado de línea desde que se escribió este
plan).

- [ ] **Step 2: Update `README.md` — estado actual**

Actualiza la fecha de "Estado actual" a la fecha de cierre real, agrega **Tributario** a la lista de
áreas operables en el primer párrafo ("✅ Funcional hoy: ... y **Laboral** ...") describiendo brevemente:
impuesto a cargo, 3 sanciones (extemporaneidad, inexactitud, error aritmético) con piso de 10 UVT,
imputación tributaria propia (sanciones → intereses → impuesto), y Renta Líquida Gravable informativa.
Quita cualquier mención de "Tributario" de la sección "🚧 En desarrollo" si existe (el motor de interés
moratorio y renta líquida ya se mencionaban ahí desde el Sprint 11a — ahora están conectados, no
standalone).

- [ ] **Step 3: Update `docs/GUIA_USUARIO.md` — sección 6, tabla de áreas**

Agrega una fila a la tabla de áreas (sección 6, "Áreas del derecho: cuáles funcionan hoy"):

```markdown
| Tributario | ✅ Sí — impuesto a cargo, sanciones por extemporaneidad/inexactitud/error aritmético (con piso de 10 UVT), imputación propia (sanciones → intereses → impuesto, distinta del orden civil), y depuración de Renta Líquida Gravable informativa. Ver [sección 5.X](#5x-agregar-una-obligación-tributaria). |
```

(Ajusta el número de sección `5.X` al que realmente le corresponda al insertarla, siguiendo la numeración
consecutiva ya existente — revisa qué número de sección sigue después de la última "5.N" en el archivo
actual.)

- [ ] **Step 4: Add a new section documenting the Tributario form**

Agrega una sección nueva (numerada consecutivamente, siguiendo el patrón de la sección 5.9
"Agregar una obligación sancionatoria" ya existente) explicando las 5 categorías, qué campos pide cada
una, y qué hace el piso de 10 UVT. Sigue el mismo estilo didáctico (numerado, sin jerga) que el resto de
la Guía de Usuario.

- [ ] **Step 5: Update section 8 (Funciones pendientes) if it still lists Tributario as pending**

Si la sección 8 tiene un bullet "🚧 Derecho Tributario" (agregado en el Sprint 14/15 anteriores),
cámbialo a "✅ Derecho Tributario" describiendo lo que ya está construido, y aclara qué queda
explícitamente fuera de alcance (cálculo de tarifa sobre renta líquida gravable, compensación de
pérdidas de años anteriores, integración en vivo con la DIAN — ver design spec, sección "Alcance
explícitamente excluido").

- [ ] **Step 6: Commit**

```bash
git add README.md docs/GUIA_USUARIO.md
git commit -m "docs: document Tributario as the sixth operable area"
```

---

### Task 9: Verificación final y cierre en `Pendientes.md`

**Files:** `Pendientes.md`

- [ ] **Step 1: Run the complete test suite**

Run: `pytest -q`
Expected: all passing, 0 failed.

- [ ] **Step 2: Add a closeout note to the Sprint 15 section of `Pendientes.md`**

Sigue el mismo estilo que el cierre del Sprint 14 (busca "**Cierre de implementación (2026-07-21):**" en
`Pendientes.md` para ver el precedente inmediato). El párrafo de cierre para Sprint 15 debe:
- Referenciar el design spec y el plan por nombre de archivo.
- Resumir lo construido: motor de sanciones, esquema nuevo, `TributarioStrategy` operable en la GUI,
  reutilización del motor genérico (sin motor de imputación dedicado), Renta Líquida Gravable
  informativa, y el arreglo de reporting para el bucket de indexación/sanciones.
- Cerrar con la misma frase fija: "`README.md` y `docs/GUIA_USUARIO.md` actualizados. Suite completa en
  verde (N passed, M skipped)." con el N/M real observado en el Step 1.

- [ ] **Step 3: Commit**

```bash
git add Pendientes.md
git commit -m "docs: mark Sprint 15 (Tributario completo, cierre 11b) completed"
```

---

## Self-Review Notes

- **Spec coverage:** motor de sanciones (Task 1), esquema/migración (Task 2), constantes de GUI (Task 3),
  `LiquidationResult.renta_liquida` + `_capital_concepts` + serialización con compatibilidad hacia atrás
  (Task 4), `TributarioStrategy` completa con las 4 categorías de deuda + Renta Líquida separada + orden
  de imputación verificado (Task 5), reporting corregido en los 3 canales (Task 6), formulario de GUI
  (Task 7), documentación (Task 8), cierre (Task 9) — cubre íntegramente la Definición de Hecho del
  design spec.
- **Consistencia de tipos:** `calcular_sancion_inexactitud`/`calcular_sancion_error_aritmetico` reciben
  un único argumento `diferencia: Decimal` en Task 1, y `TributarioStrategy._calcular_monto_sancion`
  (Task 5) los invoca exactamente con esa firma — corregido respecto a una inconsistencia detectada y
  arreglada en el propio design spec antes de escribir este plan.
- **Riesgo de auditoría conocido:** Task 4 incluye explícitamente una prueba de deserialización de un
  snapshot JSON *sin* la clave `renta_liquida` (formato pre-Sprint-15), replicando la cautela que ya
  motivó el bug de reconstrucción de auditoría documentado en el Sprint 23 — no se repite ese error con
  el campo nuevo.
- **Fuera de alcance (documentado, no un olvido):** cálculo de impuesto a partir de tarifa sobre renta
  líquida gravable, compensación de pérdidas de años anteriores, integración en vivo con la DIAN,
  múltiples períodos gravables por expediente.
