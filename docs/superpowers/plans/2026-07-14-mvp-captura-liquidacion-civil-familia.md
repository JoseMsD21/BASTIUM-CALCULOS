# MVP Captura Manual + Liquidación (Área Civil/Familia) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the user create an Expediente (área Civil/Familia), register its Obligaciones (Puntual o Recurrente) and Abonos through a PySide6 desktop GUI, persist everything in SQLite, and see a real liquidación (calculated by the existing `LiquidationCore` engine) on screen.

**Architecture:** GUI (PySide6) → Servicio de estrategia (`CivilFamiliaStrategy`) → Motor de cálculo existente (`UniversalLiquidationService` / `LiquidationCore`) → Persistencia (SQLAlchemy 2.0 / SQLite). The GUI never computes; it only captures data, persists it, and displays the `LiquidationResult` the strategy returns.

**Tech Stack:** Python 3.14, PySide6 6.11 (GUI), SQLAlchemy 2.0 (ORM/SQLite), pytest + pytest-qt (tests), Decimal for all money/rate math (existing project convention).

**Reference spec:** `docs/superpowers/specs/2026-07-14-mvp-captura-liquidacion-civil-familia-design.md`

---

## Key facts about the existing engine (read before starting)

- `app/engine/temporal/schedulers/base.py`: `Event(date, payload: dict, event_type: str)`.
- `app/domain/obligation/payment.py`: `Payment(date, amount: Decimal, reference: str)` — **positional order is `date, amount, reference`**.
- `app/engine/financial/rate.py`: `Rate(value: Decimal)` wraps a **fraction** (e.g. `Decimal("0.06")` = 6%), not a percent number. `Rate.from_percent(x)` divides `x` by 100 to build the fraction.
- `app/engine/liquidation/engine.py` `LiquidationCore`: recognizes capital concepts in `self._capital_concepts` (a hardcoded instance set including `"CHILD_SUPPORT"`, `"DANO_EMERGENTE"`, `"CAPITAL_PAGARE"`, `"CLOTHING"`, `"MULTA"`, etc.). Any `Event` whose `event_type` is in that set is treated as capital; `"PAYMENT"` triggers `AllocationEngine.allocate`; any other `event_type` raises `ValueError`.
- `app/services/motor_universal.py` `UniversalLiquidationService.liquidar(eventos_causacion, pagos, fecha_corte, tasa_estatica=Decimal("0.0"), rate_provider=None)`: merges causación events + payments, builds `LiquidationCore(default_daily_rate=Rate.from_percent(tasa_estatica), rate_provider=rate_provider)`, and calls `.process(...)`. **If `rate_provider` is given it takes total precedence over `tasa_estatica`** (see `LiquidationCore._get_rate_for_date`).
- `app/engine/interest/provider.py`: `MemoryRateProvider.add_rate_period(start, end, rate: Rate)` — `get_rate(date)` **raises `ValueError` if the date isn't covered by any period**, so the period must span from the earliest obligación date through `fecha_corte` inclusive.
- `app/engine/temporal/schedulers/family.py` `FamilyScheduler.add_monthly_obligation(amount, concept, due_day, category="CHILD_SUPPORT")` + `.generate(start, end) -> List[Event]` — expands a recurring monthly obligation into one `Event` per month, `event_type=category`, `payload={"amount":..., "label": concept}`.
- `app/engine/liquidation/result.py` `LiquidationResult`: `.total_interest_accrued()`, `.total_payments_applied()`, `.final_balance() -> PendingDebt` (has `.principal`, `.interest`, `.indexation`, `.total()`).
- Verified manually: `(1 + Decimal("0.06")) ** (Decimal("1")/Decimal("365")) - 1` evaluates correctly under Python's default `Decimal` context (prec=28) to `0.000159653587...` — no special context setup needed.

---

## File structure (what gets created/modified)

```
database/models.py                      # NEW content: Expediente, Obligacion, Abono, enums
database/database.py                    # NEW content: engine + init_db()
database/session.py                     # NEW content: SessionLocal + get_session()
app/engine/interest/rate_conversion.py  # NEW file: EA -> daily Rate converter
app/core/exceptions.py                  # NEW content: AreaNoImplementadaError
app/core/constants.py                   # NEW content: dropdown lists for the GUI
app/services/area_strategy.py           # NEW file: AreaStrategy ABC + CivilFamiliaStrategy + 4 stub strategies
app/engine/liquidation/registry.py      # REWRITE: real AreaRegistry wiring (was: empty pass-classes)
app/views/main_window.py                # NEW content: QMainWindow + QStackedWidget navigation
app/views/expedientes.py                # NEW content: ExpedientesListView + NuevoExpedienteDialog
app/views/expediente_detalle.py         # NEW file: ExpedienteDetallePage (obligaciones + abonos + Liquidar)
app/views/obligaciones.py               # NEW content: ObligacionFormDialog
app/views/abonos.py                     # NEW content: AbonoFormDialog
app/views/liquidaciones.py              # NEW content: ResultadoLiquidacionView
main.py                                 # REWRITE: launches the PySide6 app instead of the console demo
specifications/01_motor_temporal.md     # NEW content
specifications/02_motor_financiero.md   # NEW content
specifications/03_motor_indexacion.md   # NEW content
specifications/04_motor_pagos.md        # NEW content
specifications/05_motor_auditoria.md    # NEW content
specifications/06_motor_reportes.md     # NEW content
specifications/07_motor_juridico_familia.md  # NEW content
Pendientes.md                           # NEW file: phased backlog
requirements.txt                        # MODIFY: add PySide6, pytest, pytest-qt
tests/database/test_models.py           # NEW
tests/engine/test_rate_conversion.py    # NEW
tests/services/test_area_strategy.py    # NEW
tests/views/test_main_window.py         # NEW
tests/views/test_expedientes.py         # NEW
tests/views/test_expediente_detalle.py  # NEW
tests/views/test_obligaciones.py        # NEW
tests/views/test_abonos.py              # NEW
tests/views/test_liquidaciones.py       # NEW
```

All new test directories need an `__init__.py` (the project's existing test packages all have one, e.g. `tests/family/__init__.py`) — each task below creates the `__init__.py` alongside its first test file where the directory is new.

---

### Task 1: Add GUI and test dependencies ✅ COMPLETADA

**Files:**
- Modify: `requirements.txt`

- [x] **Step 1: Add the new dependencies**

Replace the contents of `requirements.txt` with:

```
fastapi
uvicorn
sqlalchemy
pandas
numpy
python-docx
reportlab
openpyxl
pydantic
alembic
rich
matplotlib
PySide6
pytest
pytest-qt
```

- [x] **Step 2: Install and verify**

Run: `.venv/Scripts/python.exe -m pip install -r requirements.txt`
Expected: all packages install without error (PySide6 6.11.x, pytest-qt visible in `pip list`).

Nota: la instalación falló inicialmente por el límite de rutas largas de Windows (proyecto dentro de
OneDrive). Se resolvió habilitando `LongPathsEnabled=1` en el registro (con confirmación del usuario). Ver
`Pendientes.md`.

- [x] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add PySide6, pytest and pytest-qt dependencies"
```

---

### Task 2: Database models (Expediente, Obligacion, Abono)

**Files:**
- Create: `database/models.py` (currently empty)
- Test: `tests/database/__init__.py` (new, empty)
- Test: `tests/database/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/database/__init__.py` (empty file).

Create `tests/database/test_models.py`:

```python
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.models import Base, Expediente, Obligacion, Abono, AreaDerecho, TipoObligacion


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_crea_expediente_con_area_civil_familia(session):
    expediente = Expediente(
        radicado="2026-00123",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        juzgado="Juzgado 3 de Familia de Bogota",
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.commit()

    fetched = session.query(Expediente).one()
    assert fetched.radicado == "2026-00123"
    assert fetched.area_derecho == AreaDerecho.CIVIL_FAMILIA


def test_obligacion_puntual_asociada_a_expediente(session):
    expediente = Expediente(
        radicado="2026-00124",
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

    assert expediente.obligaciones[0].concepto == "Gastos medicos"
    assert expediente.obligaciones[0].pagada is False


def test_obligacion_recurrente_tiene_campos_de_periodicidad(session):
    expediente = Expediente(
        radicado="2026-00125",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=None,
    )
    session.add(obligacion)
    session.commit()

    fetched = session.query(Obligacion).one()
    assert fetched.dia_pago == 5
    assert fetched.fecha_fin is None


def test_abono_asociado_a_obligacion(session):
    expediente = Expediente(
        radicado="2026-00126",
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
    session.flush()

    abono = Abono(
        obligacion_id=obligacion.id,
        fecha=date(2026, 1, 15),
        monto=Decimal("100000.00"),
        referencia="Consignacion Bancolombia",
    )
    session.add(abono)
    session.commit()

    assert obligacion.abonos[0].monto == Decimal("100000.00")


def test_borrar_expediente_borra_en_cascada_obligaciones_y_abonos(session):
    expediente = Expediente(
        radicado="2026-00127",
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
    session.flush()
    session.add(Abono(obligacion_id=obligacion.id, fecha=date(2026, 1, 15), monto=Decimal("100000.00")))
    session.commit()

    session.delete(expediente)
    session.commit()

    assert session.query(Obligacion).count() == 0
    assert session.query(Abono).count() == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/database/test_models.py -v`
Expected: FAIL with `ImportError: cannot import name 'Base' from 'database.models'` (file is empty).

- [ ] **Step 3: Write the implementation**

Replace the contents of `database/models.py`:

```python
from __future__ import annotations

import enum
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Enum as SAEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AreaDerecho(enum.Enum):
    CIVIL_FAMILIA = "CIVIL_FAMILIA"
    COMERCIAL = "COMERCIAL"
    LABORAL = "LABORAL"
    SANCIONATORIO = "SANCIONATORIO"
    HONORARIOS = "HONORARIOS"


class TipoObligacion(enum.Enum):
    PUNTUAL = "PUNTUAL"
    RECURRENTE = "RECURRENTE"


class Expediente(Base):
    __tablename__ = "expedientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    radicado: Mapped[str] = mapped_column(String(100))
    demandante: Mapped[str] = mapped_column(String(200))
    demandado: Mapped[str] = mapped_column(String(200))
    area_derecho: Mapped[AreaDerecho] = mapped_column(SAEnum(AreaDerecho))
    juzgado: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fecha_corte_default: Mapped[date] = mapped_column(Date)

    obligaciones: Mapped[list["Obligacion"]] = relationship(
        back_populates="expediente", cascade="all, delete-orphan"
    )


class Obligacion(Base):
    __tablename__ = "obligaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expediente_id: Mapped[int] = mapped_column(ForeignKey("expedientes.id"))
    tipo: Mapped[TipoObligacion] = mapped_column(SAEnum(TipoObligacion))
    concepto: Mapped[str] = mapped_column(String(200))
    categoria: Mapped[str] = mapped_column(String(50))
    fecha_origen: Mapped[date] = mapped_column(Date)
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    tasa_efectiva_anual: Mapped[Decimal] = mapped_column(Numeric(9, 4))
    pagada: Mapped[bool] = mapped_column(Boolean, default=False)
    fecha_pago_total: Mapped[date | None] = mapped_column(Date, nullable=True)
    dia_pago: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)

    expediente: Mapped["Expediente"] = relationship(back_populates="obligaciones")
    abonos: Mapped[list["Abono"]] = relationship(
        back_populates="obligacion", cascade="all, delete-orphan"
    )


class Abono(Base):
    __tablename__ = "abonos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    obligacion_id: Mapped[int] = mapped_column(ForeignKey("obligaciones.id"))
    fecha: Mapped[date] = mapped_column(Date)
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    referencia: Mapped[str | None] = mapped_column(String(200), nullable=True)

    obligacion: Mapped["Obligacion"] = relationship(back_populates="abonos")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/database/test_models.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add database/models.py tests/database/
git commit -m "feat: add SQLAlchemy models for Expediente, Obligacion and Abono"
```

---

### Task 3: Database engine and session helpers

**Files:**
- Create: `database/database.py` (currently empty)
- Create: `database/session.py` (currently empty)
- Test: `tests/database/test_session.py`

- [ ] **Step 1: Write the failing test**

Create `tests/database/test_session.py`:

```python
from datetime import date

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import AreaDerecho, Base, Expediente


def test_get_session_returns_a_working_sqlalchemy_session(tmp_path, monkeypatch):
    test_engine = create_engine(f"sqlite:///{tmp_path / 'inline.db'}")
    Base.metadata.create_all(test_engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=test_engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="X-1",
            demandante="A",
            demandado="B",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()

    assert session.query(Expediente).count() == 1
    session.close()


def test_init_db_creates_the_expedientes_table(tmp_path, monkeypatch):
    import database.database as database_module

    test_path = tmp_path / "test_bastium.db"
    test_engine = create_engine(f"sqlite:///{test_path}")
    monkeypatch.setattr(database_module, "engine", test_engine)

    database_module.init_db()

    assert "expedientes" in inspect(test_engine).get_table_names()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/database/test_session.py -v`
Expected: FAIL with `ImportError` (both `database/database.py` and `database/session.py` are empty).

- [ ] **Step 3: Write the implementation**

Replace the contents of `database/database.py`:

```python
from pathlib import Path

from sqlalchemy import create_engine

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


def init_db() -> None:
    from database.models import Base

    Base.metadata.create_all(engine)
```

Replace the contents of `database/session.py`:

```python
from sqlalchemy.orm import Session, sessionmaker

from database.database import engine

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Session:
    return SessionLocal()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/database/test_session.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add database/database.py database/session.py tests/database/test_session.py
git commit -m "feat: add SQLite engine and session factory for the database layer"
```

---

### Task 4: EA to daily Rate converter ✅ COMPLETADA (subagente en worktree, merge a main OK)

**Files:**
- Create: `app/engine/interest/rate_conversion.py`
- Test: `tests/engine/test_rate_conversion.py`

- [ ] **Step 1: Write the failing test**

Create `tests/engine/test_rate_conversion.py`:

```python
from decimal import Decimal

from app.engine.interest.rate_conversion import EffectiveRateConverter


def test_seis_por_ciento_anual_produce_la_tasa_diaria_civil_conocida():
    rate = EffectiveRateConverter.annual_to_daily(Decimal("6"))
    assert rate.decimal() == Decimal("0.000159653587")


def test_cero_por_ciento_anual_produce_tasa_diaria_cero():
    rate = EffectiveRateConverter.annual_to_daily(Decimal("0"))
    assert rate.decimal() == Decimal("0.000000000000")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/engine/test_rate_conversion.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.engine.interest.rate_conversion'`.

- [ ] **Step 3: Write the implementation**

Create `app/engine/interest/rate_conversion.py`:

```python
from decimal import Decimal

from app.engine.financial.rate import Rate


class EffectiveRateConverter:
    """
    Convierte una tasa efectiva anual (EA, como se certifican las tasas
    legales/comerciales) a la tasa diaria equivalente que consume el motor.

    Formula: i_diario = (1 + i_EA) ** (1/365) - 1
    """

    @staticmethod
    def annual_to_daily(annual_percent: Decimal) -> Rate:
        annual_fraction = Decimal(str(annual_percent)) / Decimal("100")
        daily_fraction = (Decimal("1") + annual_fraction) ** (Decimal("1") / Decimal("365")) - Decimal("1")
        return Rate(daily_fraction)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/engine/test_rate_conversion.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add app/engine/interest/rate_conversion.py tests/engine/test_rate_conversion.py
git commit -m "feat: add EA-to-daily interest rate converter"
```

---

### Task 5: Area strategy interface, exception, and registry rewrite ✅ COMPLETADA (subagente en worktree, merge a main OK)

**Files:**
- Modify: `app/core/exceptions.py` (currently empty)
- Create: `app/services/area_strategy.py` (interface + 4 stub strategies; `CivilFamiliaStrategy` body comes in Task 6)
- Modify: `app/engine/liquidation/registry.py` (rewrite; was empty `pass` classes)
- Test: `tests/services/__init__.py` (new, empty)
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Write the failing test**

Create `tests/services/__init__.py` (empty file).

Create `tests/services/test_area_strategy.py`:

```python
import pytest

from app.core.exceptions import AreaNoImplementadaError
from app.engine.liquidation.registry import AreaRegistry
from app.services.area_strategy import (
    CivilFamiliaStrategy,
    ComercialStrategy,
    HonorariosStrategy,
    LaboralStrategy,
    SancionatorioStrategy,
)


def test_registry_expone_las_5_areas():
    areas = AreaRegistry.get_available_areas()
    assert set(areas.keys()) == {
        "CIVIL_FAMILIA",
        "COMERCIAL",
        "LABORAL",
        "SANCIONATORIO",
        "HONORARIOS",
    }


def test_civil_familia_es_la_unica_area_operable():
    strategy = AreaRegistry.get_strategy("CIVIL_FAMILIA")
    assert isinstance(strategy, CivilFamiliaStrategy)


@pytest.mark.parametrize(
    "area_name,strategy_cls",
    [
        ("COMERCIAL", ComercialStrategy),
        ("LABORAL", LaboralStrategy),
        ("SANCIONATORIO", SancionatorioStrategy),
        ("HONORARIOS", HonorariosStrategy),
    ],
)
def test_areas_no_implementadas_lanzan_error_claro_al_liquidar(area_name, strategy_cls):
    strategy = AreaRegistry.get_strategy(area_name)
    assert isinstance(strategy, strategy_cls)
    with pytest.raises(AreaNoImplementadaError):
        strategy.liquidar(obligaciones=[], abonos=[], fecha_corte=None)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/services/test_area_strategy.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.area_strategy'`.

- [ ] **Step 3: Write the implementation**

Replace the contents of `app/core/exceptions.py`:

```python
class AreaNoImplementadaError(Exception):
    """Se lanza cuando se intenta liquidar un area del derecho aun no implementada."""
```

Create `app/services/area_strategy.py` (stub strategies only — `CivilFamiliaStrategy.liquidar` body
is fleshed out in Task 6; for now it can raise `NotImplementedError` so the module imports cleanly):

```python
from abc import ABC, abstractmethod
from datetime import date
from typing import List

from app.core.exceptions import AreaNoImplementadaError
from app.engine.liquidation.result import LiquidationResult


class AreaStrategy(ABC):
    """Contrato comun para el calculo de liquidacion por area del derecho."""

    @abstractmethod
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise NotImplementedError


class CivilFamiliaStrategy(AreaStrategy):
    """Unica estrategia operable en este sprint. Implementada en el Task 6 de este plan."""

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise NotImplementedError("Se implementa en el Task 6 de este plan.")


class ComercialStrategy(AreaStrategy):
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise AreaNoImplementadaError(
            "El area Comercial (interes 1.5x IBC + validacion de usura) esta pendiente. Ver Pendientes.md."
        )


class LaboralStrategy(AreaStrategy):
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise AreaNoImplementadaError(
            "El area Laboral (Art. 65 CST, vacaciones) esta pendiente. Ver Pendientes.md."
        )


class SancionatorioStrategy(AreaStrategy):
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise AreaNoImplementadaError(
            "El area Sancionatorio (conversion SMLMV a UVT) esta pendiente. Ver Pendientes.md."
        )


class HonorariosStrategy(AreaStrategy):
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise AreaNoImplementadaError(
            "El area Honorarios (cuota litis) esta pendiente. Ver Pendientes.md."
        )
```

Replace the contents of `app/engine/liquidation/registry.py`:

```python
class AreaRegistry:
    """
    Despacho central de areas juridicas.
    Registra que estrategia de calculo corresponde a cada area del derecho.
    """

    _areas = {}

    @classmethod
    def register(cls, area_name: str, description: str, strategy_class):
        cls._areas[area_name] = {
            "description": description,
            "strategy": strategy_class,
        }

    @classmethod
    def get_available_areas(cls) -> dict:
        return cls._areas

    @classmethod
    def get_strategy(cls, area_name: str):
        if area_name not in cls._areas:
            raise ValueError(f"El area juridica '{area_name}' no esta registrada.")
        return cls._areas[area_name]["strategy"]()


def _register_default_areas():
    from app.services.area_strategy import (
        CivilFamiliaStrategy,
        ComercialStrategy,
        HonorariosStrategy,
        LaboralStrategy,
        SancionatorioStrategy,
    )

    AreaRegistry.register(
        "CIVIL_FAMILIA", "Obligaciones Civiles y de Familia (Art. 1617 C.C.)", CivilFamiliaStrategy
    )
    AreaRegistry.register("COMERCIAL", "Obligaciones Comerciales (Art. 884 C.Co.)", ComercialStrategy)
    AreaRegistry.register("LABORAL", "Obligaciones Laborales (Cesantias, Art. 65 CST)", LaboralStrategy)
    AreaRegistry.register("SANCIONATORIO", "Sanciones administrativas (SMLMV / UVT)", SancionatorioStrategy)
    AreaRegistry.register("HONORARIOS", "Cobro de honorarios y cuota litis", HonorariosStrategy)


_register_default_areas()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/services/test_area_strategy.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add app/core/exceptions.py app/services/area_strategy.py app/engine/liquidation/registry.py tests/services/
git commit -m "feat: add AreaStrategy registry with 4 not-implemented-yet strategies"
```

---

### Task 6: CivilFamiliaStrategy — the real calculation path

**Files:**
- Modify: `app/services/area_strategy.py` (implement `CivilFamiliaStrategy.liquidar`)
- Modify: `tests/services/test_area_strategy.py` (add real-calculation tests)

- [ ] **Step 1: Write the failing test**

Append to `tests/services/test_area_strategy.py`:

```python
from datetime import date
from decimal import Decimal

from database.models import AreaDerecho, Abono, Expediente, Obligacion, TipoObligacion


def _obligacion_puntual(expediente_id=1, valor=Decimal("427900.00")):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Gastos medicos",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2025, 11, 20),
        valor=valor,
        tasa_efectiva_anual=Decimal("6.00"),
    )


def test_civil_familia_liquida_una_obligacion_puntual_sin_abonos():
    strategy = CivilFamiliaStrategy()
    obligacion = _obligacion_puntual()

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
    )

    # NOTA: `LiquidationResult.total_interest_accrued()` solo suma los items cuyo
    # `event_type` es explicitamente "INTEREST" (ver app/engine/liquidation/engine.py
    # LiquidationCore._process_event). El interes que se acumula dia a dia via
    # `_accrue_time_passage` NO pasa por ahi -- solo se refleja en `final_balance().interest`.
    # Verificado manualmente: para este mismo caso (427900.00 al 6% EA desde 2025-11-20
    # hasta 2026-01-01) el motor da total_interest_accrued() == 0.00 y
    # final_balance().interest == 2869.44. Por eso esta prueba verifica el saldo, no ese metodo.
    assert resultado.final_balance().principal == Decimal("427900.00")
    assert resultado.final_balance().interest > Decimal("0.00")
    assert resultado.total_payments_applied() == Decimal("0.00")


def test_civil_familia_aplica_un_abono_reduciendo_el_saldo():
    strategy = CivilFamiliaStrategy()
    obligacion = _obligacion_puntual()
    abono = Abono(
        id=1, obligacion_id=1, fecha=date(2025, 12, 1), monto=Decimal("100000.00"), referencia="ref-1"
    )

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2026, 1, 1)
    )

    assert resultado.total_payments_applied() == Decimal("100000.00")
    assert resultado.final_balance().total() < obligacion.valor


def test_civil_familia_expande_obligacion_recurrente_en_cuotas_mensuales():
    strategy = CivilFamiliaStrategy()
    obligacion = Obligacion(
        id=2,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 3, 5),
    )

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 5)
    )

    # 3 cuotas de 500000 causadas: enero, febrero, marzo
    assert resultado.final_balance().principal == Decimal("1500000.00")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/services/test_area_strategy.py -v`
Expected: FAIL — `test_civil_familia_liquida_una_obligacion_puntual_sin_abonos` and the other two new
tests fail with `NotImplementedError` (current stub body).

- [ ] **Step 3: Write the implementation**

Replace the `CivilFamiliaStrategy` class in `app/services/area_strategy.py` with:

```python
from datetime import date, timedelta
from decimal import Decimal
from typing import List

from app.core.exceptions import AreaNoImplementadaError
from app.domain.obligation.payment import Payment
from app.engine.financial.rate import Rate
from app.engine.interest.provider import MemoryRateProvider
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.engine.liquidation.result import LiquidationResult
from app.engine.temporal.schedulers.base import Event
from app.engine.temporal.schedulers.family import FamilyScheduler
from app.services.motor_universal import UniversalLiquidationService


class CivilFamiliaStrategy(AreaStrategy):
    """
    Unica area operable en este sprint.
    Interes fijo por obligacion (tasa efectiva anual pactada/legal, Art. 1617 C.C.),
    convertido a tasa diaria. No aplica indexacion IPC en este sprint (Ver Pendientes.md:
    depende de la carga de series historicas de IPC, que aun no existe).
    """

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        eventos_causacion: List[Event] = []
        for obligacion in obligaciones:
            eventos_causacion.extend(self._eventos_de_obligacion(obligacion, fecha_corte))

        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos
        ]

        rate_provider = self._construir_rate_provider(obligaciones, fecha_corte)

        service = UniversalLiquidationService()
        return service.liquidar(
            eventos_causacion=eventos_causacion,
            pagos=pagos,
            fecha_corte=fecha_corte,
            rate_provider=rate_provider,
        )

    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> List[Event]:
        if obligacion.tipo.value == "PUNTUAL":
            return [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": obligacion.valor, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]

        # RECURRENTE
        scheduler = FamilyScheduler()
        scheduler.add_monthly_obligation(
            amount=obligacion.valor,
            concept=obligacion.concepto,
            due_day=obligacion.dia_pago,
            category=obligacion.categoria,
        )
        fin = obligacion.fecha_fin or fecha_corte
        return scheduler.generate(start=obligacion.fecha_inicio, end=fin)

    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        fecha_mas_antigua = min(
            o.fecha_origen if o.tipo.value == "PUNTUAL" else o.fecha_inicio for o in obligaciones
        )
        # Usamos la tasa de la primera obligacion como tasa unica del expediente.
        # (Multiples tasas simultaneas por obligacion quedan fuera de alcance de este sprint.)
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligaciones[0].tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_mas_antigua - timedelta(days=1), end=fecha_corte, rate=tasa_diaria
        )
        return provider
```

Add the missing imports at the top of `app/services/area_strategy.py` if not already present (`date`,
`timedelta`, `Decimal`, `List` were already imported for the ABC in Task 5 — only add what's new: `Payment`,
`Rate`, `MemoryRateProvider`, `EffectiveRateConverter`, `FamilyScheduler`, `UniversalLiquidationService`).

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/services/test_area_strategy.py -v`
Expected: 9 passed (6 from Task 5 + 3 new).

- [ ] **Step 5: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat: implement CivilFamiliaStrategy wiring obligaciones/abonos into LiquidationCore"
```

---

### Task 7: GUI constants (categorias y areas) ✅ COMPLETADA

**Files:**
- Modify: `app/core/constants.py` (currently empty)

- [ ] **Step 1: Write the constants**

Replace the contents of `app/core/constants.py`:

```python
"""Listas y etiquetas usadas por los formularios de la GUI."""

CATEGORIAS_CIVIL_FAMILIA = [
    ("CHILD_SUPPORT", "Cuota alimentaria"),
    ("DANO_EMERGENTE", "Dano emergente"),
    ("LUCRO_CESANTE_CONSOLIDADO", "Lucro cesante consolidado"),
    ("DANOS_MORALES", "Danos morales"),
    ("CAPITAL_PAGARE", "Capital de pagare"),
    ("CLOTHING", "Gastos de vestuario"),
    ("MULTA", "Multa"),
]
# Nota: esta lista debe reflejar un subconjunto de
# app.engine.liquidation.engine.LiquidationCore._capital_concepts pertinente
# al area Civil/Familia. Si se agrega un concepto nuevo alla, agregarlo aqui tambien.

AREAS_DERECHO = [
    ("CIVIL_FAMILIA", "Civil / Familia", True),
    ("COMERCIAL", "Comercial", False),
    ("LABORAL", "Laboral", False),
    ("SANCIONATORIO", "Sancionatorio", False),
    ("HONORARIOS", "Honorarios / Litigio", False),
]
# El tercer valor de cada tupla indica si el area esta habilitada para calcular
# en este sprint. Ver Pendientes.md para el orden de habilitacion de las demas.
```

This is a plain constants module with no branching logic — no test is written for it (nothing to assert
beyond "the list exists", which the GUI tests in Tasks 9 and 11 already exercise indirectly by using it).

- [x] **Step 2: Commit**

```bash
git add app/core/constants.py
git commit -m "feat: add category and area dropdown constants for the GUI"
```

---

### Task 8: GUI shell — MainWindow with page navigation ✅ COMPLETADA (subagente en worktree, merge a main OK)

**Files:**
- Create: `app/views/main_window.py` (currently empty)
- Test: `tests/views/__init__.py` (new, empty)
- Test: `tests/views/test_main_window.py`

- [ ] **Step 1: Write the failing test**

Create `tests/views/__init__.py` (empty file).

Create `tests/views/test_main_window.py`:

```python
from app.views.main_window import MainWindow


def test_main_window_arranca_en_la_lista_de_expedientes(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.stacked_widget.currentWidget() is window.expedientes_page


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/views/test_main_window.py -v`
Expected: FAIL with `ModuleNotFoundError` (`app/views/main_window.py` is empty, no `MainWindow` class).

- [ ] **Step 3: Write the implementation**

Replace the contents of `app/views/main_window.py`:

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
        self.show_page("expedientes")

    def show_page(self, name: str) -> None:
        self.stacked_widget.setCurrentWidget(self._pages[name])

    def _abrir_detalle(self, expediente_id: int) -> None:
        self.detalle_page.cargar_expediente(expediente_id)
        self.show_page("detalle")

    def _mostrar_resultado(self, resultado, expediente_id: int) -> None:
        self.resultado_page.mostrar(resultado)
        self.show_page("resultado")
```

This references `ExpedientesListView`, `ExpedienteDetallePage`, and `ResultadoLiquidacionView`, which do
not exist yet — that's expected, they are built in Tasks 9, 10 and 13. To make **this task's test pass in
isolation**, create minimal placeholder versions now (they will be replaced/extended in later tasks):

Create `app/views/expediente_detalle.py`:

```python
from PySide6.QtWidgets import QWidget


class ExpedienteDetallePage(QWidget):
    def __init__(self, on_liquidado=None):
        super().__init__()
        self._on_liquidado = on_liquidado
        self._expediente_id = None

    def cargar_expediente(self, expediente_id: int) -> None:
        self._expediente_id = expediente_id
```

Replace the contents of `app/views/liquidaciones.py`:

```python
from PySide6.QtWidgets import QWidget


class ResultadoLiquidacionView(QWidget):
    def __init__(self):
        super().__init__()
        self._resultado = None

    def mostrar(self, resultado) -> None:
        self._resultado = resultado
```

Replace the contents of `app/views/expedientes.py`:

```python
from PySide6.QtWidgets import QWidget


class ExpedientesListView(QWidget):
    def __init__(self, on_expediente_abierto=None):
        super().__init__()
        self._on_expediente_abierto = on_expediente_abierto
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/views/test_main_window.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add app/views/main_window.py app/views/expediente_detalle.py app/views/liquidaciones.py app/views/expedientes.py tests/views/
git commit -m "feat: add MainWindow shell with page navigation and placeholder pages"
```

---

### Task 9: Expedientes list + Nuevo Expediente dialog

**Files:**
- Modify: `app/views/expedientes.py` (replace placeholder from Task 8 with the real view)
- Test: `tests/views/test_expedientes.py`

- [ ] **Step 1: Write the failing test**

Create `tests/views/test_expedientes.py`:

```python
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import AreaDerecho, Base, Expediente
from app.views.expedientes import ExpedientesListView, NuevoExpedienteDialog


def _sesion_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))


def test_lista_muestra_expedientes_existentes(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-001",
            demandante="Ana",
            demandado="Luis",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 0).text() == "2026-001"


def test_dialogo_crea_expediente_civil_familia(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = NuevoExpedienteDialog()
    qtbot.addWidget(dialog)
    dialog.campo_radicado.setText("2026-002")
    dialog.campo_demandante.setText("Ana")
    dialog.campo_demandado.setText("Luis")
    dialog.campo_fecha_corte.setDate(date(2026, 1, 1))

    expediente_id = dialog.guardar()

    session = session_module.get_session()
    guardado = session.get(Expediente, expediente_id)
    assert guardado.radicado == "2026-002"
    assert guardado.area_derecho == AreaDerecho.CIVIL_FAMILIA
    session.close()


def test_dialogo_deshabilita_areas_no_implementadas(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = NuevoExpedienteDialog()
    qtbot.addWidget(dialog)

    modelo = dialog.combo_area.model()
    # Indice 0 = Civil/Familia (habilitada), el resto deshabilitadas.
    assert modelo.item(0).isEnabled() is True
    assert modelo.item(1).isEnabled() is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/views/test_expedientes.py -v`
Expected: FAIL with `ImportError: cannot import name 'NuevoExpedienteDialog'` (only the placeholder
`ExpedientesListView` exists from Task 8).

- [ ] **Step 3: Write the implementation**

Replace the contents of `app/views/expedientes.py`:

```python
from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
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
from database.models import AreaDerecho, Expediente


class NuevoExpedienteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo expediente")

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
        expediente = Expediente(
            radicado=self.campo_radicado.text().strip(),
            demandante=self.campo_demandante.text().strip(),
            demandado=self.campo_demandado.text().strip(),
            area_derecho=AreaDerecho(self.combo_area.currentData()),
            juzgado=self.campo_juzgado.text().strip() or None,
            fecha_corte_default=fecha_corte,
        )
        session.add(expediente)
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

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Radicado", "Demandante", "Demandado", "Area"])
        self.tabla.cellDoubleClicked.connect(self._abrir_seleccionado)

        boton_nuevo = QPushButton("Nuevo expediente")
        boton_nuevo.clicked.connect(self._abrir_dialogo_nuevo)

        layout = QVBoxLayout()
        layout.addWidget(boton_nuevo)
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
            self._expediente_ids_por_fila.append(expediente.id)
        session.close()

    def _abrir_dialogo_nuevo(self) -> None:
        dialogo = NuevoExpedienteDialog(self)
        if dialogo.exec():
            self.refrescar()

    def _abrir_seleccionado(self, fila: int, _columna: int) -> None:
        if self._on_expediente_abierto:
            self._on_expediente_abierto(self._expediente_ids_por_fila[fila])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/views/test_expedientes.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add app/views/expedientes.py tests/views/test_expedientes.py
git commit -m "feat: add Expedientes list view and Nuevo Expediente dialog"
```

---

### Task 10: Obligación form dialog

**Files:**
- Modify: `app/views/obligaciones.py` (currently empty)
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Write the failing test**

Create `tests/views/test_obligaciones.py`:

```python
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion
from app.views.obligaciones import ObligacionFormDialog


def _expediente_de_prueba(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-010",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_guarda_obligacion_puntual(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Gastos medicos")
    dialog.campo_valor.setText("427900.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 11, 20))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.tipo == TipoObligacion.PUNTUAL
    assert guardada.concepto == "Gastos medicos"
    session.close()


def test_guarda_obligacion_recurrente_con_dia_de_pago(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE
    dialog.campo_concepto.setText("Cuota alimentaria")
    dialog.campo_valor.setText("500000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_inicio.setDate(date(2026, 1, 1))
    dialog.campo_dia_pago.setValue(5)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.tipo == TipoObligacion.RECURRENTE
    assert guardada.dia_pago == 5
    session.close()


def test_valor_negativo_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Gastos medicos")
    dialog.campo_valor.setText("-100.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 11, 20))

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/views/test_obligaciones.py -v`
Expected: FAIL with `ImportError` (file is empty).

- [ ] **Step 3: Write the implementation**

Replace the contents of `app/views/obligaciones.py`:

```python
from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
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
from app.core.constants import CATEGORIAS_CIVIL_FAMILIA
from database.models import Obligacion, TipoObligacion


class ObligacionFormDialog(QDialog):
    def __init__(self, expediente_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar obligacion")
        self._expediente_id = expediente_id

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("Puntual", userData="PUNTUAL")
        self.combo_tipo.addItem("Recurrente", userData="RECURRENTE")
        self.combo_tipo.currentIndexChanged.connect(self._actualizar_campos_visibles)

        self.combo_categoria = QComboBox()
        for codigo, etiqueta in CATEGORIAS_CIVIL_FAMILIA:
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

        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)

        self.layout_formulario = QFormLayout()
        self.layout_formulario.addRow("Tipo", self.combo_tipo)
        self.layout_formulario.addRow("Categoria", self.combo_categoria)
        self.layout_formulario.addRow("Concepto", self.campo_concepto)
        self.layout_formulario.addRow("Valor", self.campo_valor)
        self.layout_formulario.addRow("Tasa efectiva anual (%)", self.campo_tasa)
        self.layout_formulario.addRow("Fecha de origen (Puntual)", self.campo_fecha_origen)
        self.layout_formulario.addRow("Fecha de inicio (Recurrente)", self.campo_fecha_inicio)
        self.layout_formulario.addRow("Dia de pago (Recurrente)", self.campo_dia_pago)
        self.layout_formulario.addRow(boton_guardar)
        self.setLayout(self.layout_formulario)

        self._actualizar_campos_visibles()

    def _actualizar_campos_visibles(self) -> None:
        es_recurrente = self.combo_tipo.currentData() == "RECURRENTE"
        self.campo_fecha_origen.setVisible(not es_recurrente)
        self.campo_fecha_inicio.setVisible(es_recurrente)
        self.campo_dia_pago.setVisible(es_recurrente)

    def guardar(self) -> int:
        try:
            valor = Decimal(self.campo_valor.text())
            tasa = Decimal(self.campo_tasa.text())
        except InvalidOperation as error:
            raise ValueError("Valor y tasa deben ser numeros validos.") from error

        if valor <= Decimal("0"):
            raise ValueError("El valor de la obligacion debe ser mayor que cero.")

        tipo = TipoObligacion(self.combo_tipo.currentData())
        qdate_origen = self.campo_fecha_origen.date()
        fecha_origen = date(qdate_origen.year(), qdate_origen.month(), qdate_origen.day())
        qdate_inicio = self.campo_fecha_inicio.date()
        fecha_inicio = date(qdate_inicio.year(), qdate_inicio.month(), qdate_inicio.day())

        session = session_module.get_session()
        obligacion = Obligacion(
            expediente_id=self._expediente_id,
            tipo=tipo,
            concepto=self.campo_concepto.text().strip(),
            categoria=self.combo_categoria.currentData(),
            fecha_origen=fecha_origen if tipo == TipoObligacion.PUNTUAL else fecha_inicio,
            valor=valor,
            tasa_efectiva_anual=tasa,
            dia_pago=self.campo_dia_pago.value() if tipo == TipoObligacion.RECURRENTE else None,
            fecha_inicio=fecha_inicio if tipo == TipoObligacion.RECURRENTE else None,
            fecha_fin=None,
        )
        session.add(obligacion)
        session.commit()
        obligacion_id = obligacion.id
        session.close()
        return obligacion_id

    def _guardar_y_cerrar(self) -> None:
        try:
            self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos invalidos", str(error))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/views/test_obligaciones.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "feat: add Obligacion form dialog supporting Puntual and Recurrente"
```

---

### Task 11: Abono form dialog

**Files:**
- Modify: `app/views/abonos.py` (currently empty)
- Test: `tests/views/test_abonos.py`

- [ ] **Step 1: Write the failing test**

Create `tests/views/test_abonos.py`:

```python
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion, Abono
from app.views.abonos import AbonoFormDialog


def _obligacion_de_prueba(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-020",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 6, 1),
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
    obligacion_id = obligacion.id
    session.close()
    return obligacion_id


def test_guarda_abono_asociado_a_obligacion(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("100000.00")
    dialog.campo_referencia.setText("Consignacion Bancolombia")
    dialog.campo_fecha.setDate(date(2026, 1, 15))

    dialog.guardar()

    session = session_module.get_session()
    guardado = session.query(Abono).filter_by(obligacion_id=obligacion_id).one()
    assert guardado.monto == Decimal("100000.00")
    assert guardado.referencia == "Consignacion Bancolombia"
    session.close()


def test_monto_cero_lanza_error_de_validacion(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("0.00")

    with pytest.raises(ValueError):
        dialog.guardar()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/views/test_abonos.py -v`
Expected: FAIL with `ImportError` (file is empty).

- [ ] **Step 3: Write the implementation**

Replace the contents of `app/views/abonos.py`:

```python
from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDateEdit, QDialog, QFormLayout, QLineEdit, QMessageBox, QPushButton

import database.session as session_module
from database.models import Abono


class AbonoFormDialog(QDialog):
    def __init__(self, obligacion_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar abono")
        self._obligacion_id = obligacion_id

        self.campo_fecha = QDateEdit(QDate.currentDate())
        self.campo_fecha.setCalendarPopup(True)
        self.campo_monto = QLineEdit()
        self.campo_referencia = QLineEdit()

        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
        layout.addRow("Fecha", self.campo_fecha)
        layout.addRow("Monto", self.campo_monto)
        layout.addRow("Referencia", self.campo_referencia)
        layout.addRow(boton_guardar)
        self.setLayout(layout)

    def guardar(self) -> int:
        try:
            monto = Decimal(self.campo_monto.text())
        except InvalidOperation as error:
            raise ValueError("El monto debe ser un numero valido.") from error

        if monto <= Decimal("0"):
            raise ValueError("El monto del abono debe ser mayor que cero.")

        qdate = self.campo_fecha.date()
        fecha = date(qdate.year(), qdate.month(), qdate.day())

        session = session_module.get_session()
        abono = Abono(
            obligacion_id=self._obligacion_id,
            fecha=fecha,
            monto=monto,
            referencia=self.campo_referencia.text().strip() or None,
        )
        session.add(abono)
        session.commit()
        abono_id = abono.id
        session.close()
        return abono_id

    def _guardar_y_cerrar(self) -> None:
        try:
            self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos invalidos", str(error))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/views/test_abonos.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add app/views/abonos.py tests/views/test_abonos.py
git commit -m "feat: add Abono form dialog"
```

---

### Task 12: Resultado de Liquidación view

**Files:**
- Modify: `app/views/liquidaciones.py` (replace placeholder from Task 8)
- Test: `tests/views/test_liquidaciones.py`

- [ ] **Step 1: Write the failing test**

Create `tests/views/test_liquidaciones.py`:

```python
from datetime import date
from decimal import Decimal

from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.views.liquidaciones import ResultadoLiquidacionView


def _resultado_de_prueba() -> LiquidationResult:
    debt = PendingDebt(principal=Decimal("427900.00"), interest=Decimal("1200.50"), indexation=Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="LIQUIDATION_CUTOFF")
    item = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Corte final de liquidacion",
        capital_base=Decimal("427900.00"),
        interest_rate=Decimal("6.00"),
        interest_amount=Decimal("1200.50"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
    )
    return LiquidationResult(items=[item])


def test_muestra_una_fila_por_item_de_liquidacion(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba())

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 1).text() == "Corte final de liquidacion"


def test_muestra_los_totales(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba())

    assert "1200.50" in view.etiqueta_interes_total.text()
    assert "427900.00" in view.etiqueta_saldo_final.text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/views/test_liquidaciones.py -v`
Expected: FAIL — `ResultadoLiquidacionView` (placeholder from Task 8) has no `tabla` or
`etiqueta_interes_total` attributes.

- [ ] **Step 3: Write the implementation**

Replace the contents of `app/views/liquidaciones.py`:

```python
from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.engine.liquidation.result import LiquidationResult


class ResultadoLiquidacionView(QWidget):
    def __init__(self):
        super().__init__()

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "Concepto", "Capital base", "Tasa %", "Interes", "Pago", "Saldo"]
        )

        self.etiqueta_interes_total = QLabel("Interes acumulado: 0.00")
        self.etiqueta_pagos_total = QLabel("Pagos aplicados: 0.00")
        self.etiqueta_saldo_final = QLabel("Saldo final: 0.00")

        layout = QVBoxLayout()
        layout.addWidget(self.tabla)
        layout.addWidget(self.etiqueta_interes_total)
        layout.addWidget(self.etiqueta_pagos_total)
        layout.addWidget(self.etiqueta_saldo_final)
        self.setLayout(layout)

    def mostrar(self, resultado: LiquidationResult) -> None:
        self.tabla.setRowCount(len(resultado.items))
        for fila, item in enumerate(resultado.items):
            self.tabla.setItem(fila, 0, QTableWidgetItem(item.date.isoformat()))
            self.tabla.setItem(fila, 1, QTableWidgetItem(item.concept))
            self.tabla.setItem(fila, 2, QTableWidgetItem(str(item.capital_base)))
            self.tabla.setItem(fila, 3, QTableWidgetItem(str(item.interest_rate)))
            self.tabla.setItem(fila, 4, QTableWidgetItem(str(item.interest_amount)))
            self.tabla.setItem(fila, 5, QTableWidgetItem(str(item.payment_amount)))
            self.tabla.setItem(fila, 6, QTableWidgetItem(str(item.balance.debt.total())))

        self.etiqueta_interes_total.setText(f"Interes acumulado: {resultado.total_interest_accrued()}")
        self.etiqueta_pagos_total.setText(f"Pagos aplicados: {resultado.total_payments_applied()}")
        self.etiqueta_saldo_final.setText(f"Saldo final: {resultado.final_balance().total()}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/views/test_liquidaciones.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add app/views/liquidaciones.py tests/views/test_liquidaciones.py
git commit -m "feat: add Resultado de Liquidacion view with itemized table and totals"
```

---

### Task 13: Expediente Detalle page — wiring obligaciones, abonos and Liquidar

**Files:**
- Modify: `app/views/expediente_detalle.py` (replace placeholder from Task 8)
- Test: `tests/views/test_expediente_detalle.py`

- [ ] **Step 1: Write the failing test**

Create `tests/views/test_expediente_detalle.py`:

```python
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion, Abono
from app.views.expediente_detalle import ExpedienteDetallePage


def _expediente_con_obligacion(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-030",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.flush()
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Gastos medicos",
            categoria="DANO_EMERGENTE",
            fecha_origen=date(2025, 11, 20),
            valor=Decimal("427900.00"),
            tasa_efectiva_anual=Decimal("6.00"),
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_cargar_expediente_muestra_sus_obligaciones(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    assert page.tabla_obligaciones.rowCount() == 1
    assert page.tabla_obligaciones.item(0, 0).text() == "Gastos medicos"


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

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/views/test_expediente_detalle.py -v`
Expected: FAIL — placeholder `ExpedienteDetallePage` has no `tabla_obligaciones` or `_liquidar`.

- [ ] **Step 3: Write the implementation**

Replace the contents of `app/views/expediente_detalle.py`:

```python
from PySide6.QtWidgets import (
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
from app.core.exceptions import AreaNoImplementadaError
from app.engine.liquidation.registry import AreaRegistry
from app.views.abonos import AbonoFormDialog
from app.views.obligaciones import ObligacionFormDialog
from database.models import Expediente


class ExpedienteDetallePage(QWidget):
    def __init__(self, on_liquidado=None):
        super().__init__()
        self._on_liquidado = on_liquidado
        self._expediente_id = None
        self._obligacion_ids_por_fila = []

        self.tabla_obligaciones = QTableWidget(0, 3)
        self.tabla_obligaciones.setHorizontalHeaderLabels(["Concepto", "Tipo", "Valor"])
        boton_agregar_obligacion = QPushButton("Agregar obligacion")
        boton_agregar_obligacion.clicked.connect(self._abrir_dialogo_obligacion)

        grupo_obligaciones = QGroupBox("Obligaciones")
        layout_obligaciones = QVBoxLayout()
        layout_obligaciones.addWidget(boton_agregar_obligacion)
        layout_obligaciones.addWidget(self.tabla_obligaciones)
        grupo_obligaciones.setLayout(layout_obligaciones)

        self.tabla_abonos = QTableWidget(0, 3)
        self.tabla_abonos.setHorizontalHeaderLabels(["Fecha", "Monto", "Referencia"])
        boton_agregar_abono = QPushButton("Agregar abono")
        boton_agregar_abono.clicked.connect(self._abrir_dialogo_abono)

        grupo_abonos = QGroupBox("Abonos")
        layout_abonos = QVBoxLayout()
        layout_abonos.addWidget(boton_agregar_abono)
        layout_abonos.addWidget(self.tabla_abonos)
        grupo_abonos.setLayout(layout_abonos)

        boton_liquidar = QPushButton("Liquidar")
        boton_liquidar.clicked.connect(self._liquidar)

        columnas = QHBoxLayout()
        columnas.addWidget(grupo_obligaciones)
        columnas.addWidget(grupo_abonos)

        layout_principal = QVBoxLayout()
        layout_principal.addLayout(columnas)
        layout_principal.addWidget(boton_liquidar)
        self.setLayout(layout_principal)

    def cargar_expediente(self, expediente_id: int) -> None:
        self._expediente_id = expediente_id
        self._refrescar_obligaciones()
        self._refrescar_abonos()

    def _refrescar_obligaciones(self) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)
        obligaciones = list(expediente.obligaciones)

        self.tabla_obligaciones.setRowCount(len(obligaciones))
        self._obligacion_ids_por_fila = []
        for fila, obligacion in enumerate(obligaciones):
            self.tabla_obligaciones.setItem(fila, 0, QTableWidgetItem(obligacion.concepto))
            self.tabla_obligaciones.setItem(fila, 1, QTableWidgetItem(obligacion.tipo.value))
            self.tabla_obligaciones.setItem(fila, 2, QTableWidgetItem(str(obligacion.valor)))
            self._obligacion_ids_por_fila.append(obligacion.id)
        session.close()

    def _refrescar_abonos(self) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)
        abonos = [abono for obligacion in expediente.obligaciones for abono in obligacion.abonos]

        self.tabla_abonos.setRowCount(len(abonos))
        for fila, abono in enumerate(abonos):
            self.tabla_abonos.setItem(fila, 0, QTableWidgetItem(abono.fecha.isoformat()))
            self.tabla_abonos.setItem(fila, 1, QTableWidgetItem(str(abono.monto)))
            self.tabla_abonos.setItem(fila, 2, QTableWidgetItem(abono.referencia or ""))
        session.close()

    def _abrir_dialogo_obligacion(self) -> None:
        dialogo = ObligacionFormDialog(expediente_id=self._expediente_id, parent=self)
        if dialogo.exec():
            self._refrescar_obligaciones()

    def _abrir_dialogo_abono(self) -> None:
        fila_seleccionada = self.tabla_obligaciones.currentRow()
        if fila_seleccionada < 0:
            QMessageBox.warning(self, "Seleccion requerida", "Selecciona una obligacion antes de agregar un abono.")
            return

        obligacion_id = self._obligacion_ids_por_fila[fila_seleccionada]
        dialogo = AbonoFormDialog(obligacion_id=obligacion_id, parent=self)
        if dialogo.exec():
            self._refrescar_abonos()

    def _liquidar(self) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)
        obligaciones = list(expediente.obligaciones)
        abonos = [abono for obligacion in obligaciones for abono in obligacion.abonos]
        fecha_corte = expediente.fecha_corte_default
        area = expediente.area_derecho.value
        session.close()

        try:
            estrategia = AreaRegistry.get_strategy(area)
            resultado = estrategia.liquidar(obligaciones=obligaciones, abonos=abonos, fecha_corte=fecha_corte)
        except AreaNoImplementadaError as error:
            QMessageBox.warning(self, "Area no implementada", str(error))
            return
        except ValueError as error:
            QMessageBox.warning(self, "No se pudo liquidar", str(error))
            return

        if self._on_liquidado:
            self._on_liquidado(resultado, self._expediente_id)
```

Note: `AreaRegistry.get_strategy` expects the registered key names from Task 5
(`"CIVIL_FAMILIA"`, `"COMERCIAL"`, etc.), which match `Expediente.area_derecho.value` exactly
(`AreaDerecho.CIVIL_FAMILIA.value == "CIVIL_FAMILIA"`).

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/views/test_expediente_detalle.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add app/views/expediente_detalle.py tests/views/test_expediente_detalle.py
git commit -m "feat: wire Expediente Detalle page to obligaciones, abonos and Liquidar"
```

---

### Task 14: main.py launches the GUI

**Files:**
- Modify: `main.py` (replace the console demo entirely)

- [ ] **Step 1: Replace `main.py`**

```python
import sys

from PySide6.QtWidgets import QApplication

from database.database import init_db
from app.views.main_window import MainWindow


def main() -> None:
    init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

This removes the old `rich`-console demo (`iniciar_consola`, hardcoded `rubros_extraidos`,
`FamilyLawCalculator`, `BastiumChartGenerator`, `JudicialPDFGenerator` usage) since it's superseded by the
real GUI flow. `app/engine/liquidation/calculator.py` (`FamilyLawCalculator`), `app/reports/charts.py` and
`app/reports/pdf.py` are left untouched in the codebase — they're unused by the new `main.py` but not
deleted, since report export is explicitly out of scope for this MVP (see `Pendientes.md`, Task 16) and may
be wired back in later.

- [ ] **Step 2: Manual verification (no automated test for the entrypoint itself)**

Run: `.venv/Scripts/python.exe main.py`
Expected: A window titled "BASTIUM - Ecosistema de Liquidacion Forense" opens showing the empty
Expedientes list with a "Nuevo expediente" button. Close the window to end the process.

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: launch the PySide6 GUI from main.py instead of the console demo"
```

---

### Task 15: Fill in specifications/*.md ✅ COMPLETADA (todos los Steps 1-8)

**Files:**
- Modify: `specifications/01_motor_temporal.md`
- Modify: `specifications/02_motor_financiero.md`
- Modify: `specifications/03_motor_indexacion.md`
- Modify: `specifications/04_motor_pagos.md`
- Modify: `specifications/05_motor_auditoria.md`
- Modify: `specifications/06_motor_reportes.md`
- Modify: `specifications/07_motor_juridico_familia.md`

- [ ] **Step 1: Write `specifications/01_motor_temporal.md`**

```markdown
# Motor Temporal

## Que hace
Genera la cronologia de eventos (`Event`) que alimenta al motor de liquidacion, a partir de reglas de
recurrencia (mensual o anual).

## Componentes
- `app/engine/temporal/schedulers/base.py`: `Event(date, payload, event_type)` y la interfaz `Scheduler`.
- `app/engine/temporal/schedulers/recurring.py`: `RecurringRule(amount, frequency, day, month)` y
  `RecurringScheduler`, que expande una regla mensual/anual en una lista de `Event` entre `start` y `end`,
  usando `CalendarUtils.safe_create_date` para evitar fechas invalidas (ej. 30 de febrero).
- `app/engine/temporal/schedulers/family.py`: `FamilyScheduler`, especializado en Derecho de Familia.
  `add_monthly_obligation(amount, concept, due_day, category="CHILD_SUPPORT")` registra una cuota mensual;
  `generate(start, end)` la expande y ordena cronologicamente.
- `app/engine/temporal/schedulers/civil.py`, `labor.py`: existen como archivos pero aun no tienen logica
  equivalente para esas areas (ver `Pendientes.md`).

## Como se usa en el MVP
`CivilFamiliaStrategy` (`app/services/area_strategy.py`) usa `FamilyScheduler` para expandir obligaciones
de tipo `RECURRENTE` en eventos mensuales antes de pasarlos al motor de liquidacion.

## Pendiente (no implementado aun)
- Calendario de dias habiles / festivos (`app/engine/time/calendar.py` solo resuelve desbordes de mes).
- Suspension / interrupcion de terminos procesales.
- Motor de prescripcion y caducidad.

Ver `Pendientes.md` para el orden de implementacion.
```

- [ ] **Step 2: Write `specifications/02_motor_financiero.md`**

```markdown
# Motor Financiero (Interes)

## Que hace
Calcula intereses simples dia a dia sobre un capital, y mantiene el estado inmutable de una deuda
(capital + interes + indexacion) a lo largo del tiempo.

## Componentes
- `app/engine/financial/rate.py`: `Rate(value)` envuelve una **fraccion** (0.06 = 6%), no un numero de
  porcentaje. `Rate.from_percent(x)` construye una `Rate` dividiendo `x` entre 100.
- `app/engine/interest/daily_interest.py`: `DailyInterest.calculate(capital, daily_rate, days)` aplica
  `I = C * i * t` con redondeo monetario (`Rounding.money`).
- `app/engine/interest/rate_conversion.py`: `EffectiveRateConverter.annual_to_daily(annual_percent)`
  convierte una tasa efectiva anual (como se pactan/certifican legalmente) a la tasa diaria equivalente,
  usando `i_diario = (1 + i_EA) ** (1/365) - 1`.
- `app/engine/interest/provider.py`: `RateProvider` (interfaz) y `MemoryRateProvider`, que permite inyectar
  tramos de tasa (`RatePeriod`) para que el motor calcule interes por tramos historicos cuando la tasa
  cambia en el tiempo. **Si se usa un `rate_provider`, debe cubrir todo el rango de fechas de la
  liquidacion**, o `get_rate` lanza `ValueError`.
- `app/engine/liquidation/models.py`: `PendingDebt(principal, interest, indexation)` — inmutable, con
  `.total()`.
- `app/engine/liquidation/balance.py`: `BalanceEngine` — funciones puras `add_principal`, `add_interest`,
  `add_indexation` que devuelven un nuevo `PendingDebt`.
- `app/engine/liquidation/engine.py`: `LiquidationCore` — orquesta el paso del tiempo dia a dia
  (`_accrue_time_passage`) y el procesamiento de cada `Event` (`_process_event`), acumulando el historial
  en `LiquidationItem`.

## Como se usa en el MVP
`CivilFamiliaStrategy` construye un `MemoryRateProvider` con un unico tramo (la tasa efectiva anual pactada
de la primera obligacion del expediente, convertida a diaria) que cubre desde la obligacion mas antigua
hasta la fecha de corte.

## Pendiente (no implementado aun)
- Validacion de tope de usura (1.5x IBC) — necesaria para el area Comercial.
- Anatocismo (interes sobre interes) — prohibido por defecto, el motor actual no lo aplica en ningun caso
  (comportamiento correcto para Civil, pero el area Comercial necesitara habilitarlo bajo condiciones).
- Multiples tasas por obligacion dentro del mismo expediente (hoy se usa una sola tasa por expediente).

Ver `Pendientes.md`.
```

- [ ] **Step 3: Write `specifications/03_motor_indexacion.md`**

```markdown
# Motor de Indexacion (IPC)

## Que hace
Ajusta un capital historico a valor presente segun la variacion del Indice de Precios al Consumidor (IPC),
usando `Va = Vh * (IPC_final / IPC_inicial)`.

## Componentes
- `app/engine/indexation/ipc.py`: `IPCIndexation.calculate(capital, initial_index, final_index)`. Si hay
  deflacion (`final_index <= initial_index`), retorna 0 — la jurisprudencia no castiga al acreedor por
  deflacion.
- `app/engine/indexation/smmlv.py`: conversion de un valor expresado en SMMLV a pesos.
- `app/engine/indexation/historical_index.py`: **vacio**. Deberia contener las series historicas de IPC
  (y SMLMV/UVT/IBC) necesarias para resolver `initial_index`/`final_index` a partir de una fecha.

## Estado en el MVP
`IPCIndexation` esta implementado y probado, pero **no esta conectado a `CivilFamiliaStrategy` en este
sprint**: sin datos historicos de IPC (`historical_index.py` vacio) no hay forma de resolver los indices
inicial/final automaticamente. El expediente Civil/Familia de este MVP calcula solo interes, no indexacion.

## Pendiente (no implementado aun)
- Cargar series historicas de IPC/SMLMV/UVT/IBC en `historical_index.py` (o en una tabla de base de datos
  equivalente a `indicator_historical_rates`).
- Conectar `IPCIndexation` a `CivilFamiliaStrategy` una vez exista la fuente de datos.
- Interpolacion cuando la fecha de corte no coincide con un mes certificado.

Ver `Pendientes.md`.
```

- [ ] **Step 4: Write `specifications/04_motor_pagos.md`**

```markdown
# Motor de Pagos (Imputacion)

## Que hace
Aplica un pago recibido contra una deuda pendiente, siguiendo la prelacion legal estricta:
1. Indexacion
2. Intereses
3. Capital

## Componentes
- `app/engine/liquidation/allocation.py`: `AllocationEngine.allocate(payment_amount, current_debt,
  payment_date)` retorna `(PaymentAllocation, nuevo PendingDebt, remainder)`. El `remainder` es el
  sobrante si el pago excede toda la deuda.
- `app/domain/obligation/payment.py`: `Payment(date, amount, reference)` — la forma en que un abono
  entra al motor.
- `app/engine/liquidation/engine.py` (`LiquidationCore._process_event`): cuando un `Event` tiene
  `event_type == "PAYMENT"`, delega en `AllocationEngine.allocate`.

## Como se usa en el MVP
Cada `Abono` capturado en la GUI se convierte en un `Payment` (`CivilFamiliaStrategy`) y se mezcla
cronologicamente con los eventos de causacion antes de procesarse.

## Advertencia de deuda tecnica
Existe un segundo motor de allocation, `app/engine/allocation/allocator.py`, que opera sobre un modelo de
dominio distinto (`app.domain.obligation.base.Obligation`) y **no esta implementado**
(`raise NotImplementedError`). No se usa en este MVP ni se debe usar — es codigo huerfano. Ver
`Pendientes.md` para la decision de eliminarlo o completarlo.

## Pendiente (no implementado aun)
- Validadores de pago anomalo (pago mayor al saldo, duplicado, sin soporte).
- Reglas de imputacion alternativas por regimen (ej. tributario: sanciones -> intereses -> impuesto).
- Compensacion, novacion, remision, confusion.

Ver `Pendientes.md`.
```

- [ ] **Step 5: Write `specifications/05_motor_auditoria.md`**

```markdown
# Motor de Auditoria

## Estado actual
`app/engine/audit/` solo contiene un `__init__.py` vacio. No hay ninguna logica de auditoria implementada
todavia (trazabilidad de cambios, log de quien liquido que expediente y cuando, versionado de liquidaciones
recalculadas, etc.).

## Que provee el motor de liquidacion hoy, sin ser "auditoria" formal
`LiquidationResult` (`app/engine/liquidation/result.py`) guarda el historial completo de `LiquidationItem`
por evento, lo que da trazabilidad matematica de como se llego al saldo final — pero no hay una capa que
registre quien ejecuto la liquidacion, cuando, ni permita comparar versiones.

## Pendiente (no implementado aun)
Todo. Ver `Pendientes.md` para cuando priorizarlo (no es parte de ningun sprint fasado explicito;
depende de si el usuario necesita multi-usuario o solo uso individual).
```

- [ ] **Step 6: Write `specifications/06_motor_reportes.md`**

```markdown
# Motor de Reportes

## Que hace
Provee metricas listas para presentar (interes acumulado, pagos aplicados, saldo final) a partir de un
`LiquidationResult`, y (por separado, no conectado aun) genera graficas y documentos PDF.

## Componentes
- `app/engine/liquidation/result.py`: `LiquidationResult.total_interest_accrued()`,
  `.total_payments_applied()`, `.final_balance()`.
- `app/engine/reports/summary.py`, `table_builder.py`, `chart_builder.py`: utilidades de reportes de mas
  bajo nivel, usadas por los tests existentes (`tests/reports/`) pero no conectadas a la GUI.
- `app/reports/charts.py` (`BastiumChartGenerator`), `app/reports/pdf.py` (`JudicialPDFGenerator`),
  `app/reports/word.py` (vacio): generacion de graficas y documentos. Usados antes por el script de
  consola (`main.py` original); **no estan conectados a la GUI en este MVP**.

## Estado en el MVP
La pantalla "Resultado de Liquidacion" (`app/views/liquidaciones.py`) muestra la tabla y los totales
directamente en pantalla. No hay boton de exportar a PDF/Word todavia.

## Pendiente (no implementado aun)
- Boton "Exportar a PDF" en la pantalla de resultado, reutilizando `JudicialPDFGenerator`.
- Boton "Exportar a Word", implementando `app/reports/word.py` (vacio hoy).

Ver `Pendientes.md`.
```

- [ ] **Step 7: Write `specifications/07_motor_juridico_familia.md`**

```markdown
# Motor Juridico: Area Civil / Familia

## Que hace
Es la unica area del derecho con calculo real en este sprint. Convierte las Obligaciones y Abonos
capturados en la GUI en la liquidacion final, aplicando el interes fijo del Art. 1617 C.C. (6% anual, o la
tasa que el usuario pacte/certifique, convertida a diaria).

## Componentes
- `app/engine/liquidation/registry.py`: `AreaRegistry` — registra las 5 areas del derecho
  (`CIVIL_FAMILIA`, `COMERCIAL`, `LABORAL`, `SANCIONATORIO`, `HONORARIOS`) y su estrategia de calculo
  correspondiente. `AreaRegistry.get_strategy(area_name)` instancia la estrategia.
- `app/services/area_strategy.py`:
  - `AreaStrategy` (interfaz abstracta): `liquidar(obligaciones, abonos, fecha_corte) -> LiquidationResult`.
  - `CivilFamiliaStrategy`: unica implementacion real. Mapea cada `Obligacion` Puntual a un unico `Event`
    de capital; cada `Obligacion` Recurrente se expande con `FamilyScheduler` en eventos mensuales; cada
    `Abono` se convierte en un `Payment`. Construye un `MemoryRateProvider` con la tasa efectiva anual de
    la primera obligacion (convertida a diaria via `EffectiveRateConverter`), y delega en
    `UniversalLiquidationService.liquidar(...)`.
  - `ComercialStrategy`, `LaboralStrategy`, `SancionatorioStrategy`, `HonorariosStrategy`: registradas pero
    lanzan `AreaNoImplementadaError` (`app/core/exceptions.py`) si se invocan. La GUI nunca las llama
    porque el selector de area en `NuevoExpedienteDialog` (`app/views/expedientes.py`) las deshabilita.

## Flujo end-to-end
`ExpedienteDetallePage._liquidar()` (`app/views/expediente_detalle.py`) lee las Obligaciones/Abonos del
expediente desde la base de datos, obtiene la estrategia via `AreaRegistry.get_strategy(area)`, y muestra
el `LiquidationResult` en `ResultadoLiquidacionView`.

## Pendiente (no implementado aun)
Las 4 areas restantes (Comercial, Laboral, Sancionatorio, Honorarios) — ver `Pendientes.md` para el orden
de los proximos sprints.
```

- [x] **Step 8: Commit**

```bash
git add specifications/
git commit -m "docs: fill in specifications for all 7 engine modules"
```

---

### Task 16: Pendientes.md ✅ COMPLETADA

**Files:**
- Create: `Pendientes.md` (project root, new file)

- [x] **Step 1: Write the backlog**

```markdown
# Pendientes de BASTIUM

Backlog fasado de todo lo que quedo fuera del MVP de captura manual (área Civil/Familia). Ver
`docs/superpowers/specs/2026-07-14-mvp-captura-liquidacion-civil-familia-design.md` para el contexto
completo de lo que SI se construyo.

## Sprint 2 — Área Comercial
- Interes moratorio comercial = 1.5x IBC (Art. 884 C.Co.) cuando no se pacta.
- Validacion de tope de usura: lanzar error o truncar si la tasa pactada supera 1.5x IBC (Art. 72 Ley 45
  de 1990).
- Conversion general EA -> diaria ya existe (`app/engine/interest/rate_conversion.py`), reutilizable aqui.
- Regla de incompatibilidad: en Comercial, interes e indexacion IPC no pueden cobrarse simultaneamente.
- Implementar `ComercialStrategy` en `app/services/area_strategy.py` (hoy lanza `AreaNoImplementadaError`).

## Sprint 3 — Área Laboral
- Prestaciones sociales (cesantias, prima, vacaciones) basadas en SMLMV/Auxilio de Transporte vigente al
  momento de la causacion.
- Indemnizacion moratoria Art. 65 CST: un dia de salario por dia de retardo hasta el mes 25 (dia 721);
  desde ahi, interes moratorio a la tasa maxima legal (SFC) sobre salarios y cesantias adeudadas.
- Implementar `LaboralStrategy` (hoy lanza `AreaNoImplementadaError`). Hay un scheduler laboral parcial en
  `app/engine/temporal/schedulers/labor.py` que se puede extender.

## Sprint 4 — Área Sancionatorio y Honorarios
- Conversion SMLMV -> UVT por vigencia historica (Ley 1955 de 2019): si el hecho es anterior al
  2020-01-01 se usa el SMLMV de ese año; si es posterior, la UVT historica de la DIAN.
- Cuota litis: validar que honorarios fijos + cuota litis no superen el 50% del beneficio obtenido.
- Implementar `SancionatorioStrategy` y `HonorariosStrategy` (hoy lanzan `AreaNoImplementadaError`).

## Backlog transversal (sin sprint asignado aun)
- Calendario de dias habiles / festivos y motor de suspension-interrupcion de terminos procesales.
- Motor de prescripcion y caducidad.
- Carga de series historicas de IPC / SMLMV / UVT / IBC (`app/engine/indexation/historical_index.py` esta
  vacio) — bloquea conectar la indexacion IPC a `CivilFamiliaStrategy`.
- Conectar indexacion IPC al area Civil/Familia una vez exista la fuente de datos historica.
- Exportar la liquidacion a PDF/Word desde la GUI (`app/reports/pdf.py` existe pero no esta conectado;
  `app/reports/word.py` esta vacio).
- Resolver el motor de allocation huerfano `app/engine/allocation/allocator.py`
  (`raise NotImplementedError`, modelo de dominio distinto al usado por `LiquidationCore`) — decidir si se
  completa o se elimina.
- Motor de auditoria (`app/engine/audit/`) — hoy no existe ninguna logica (quien liquido que expediente,
  cuando, versionado de recalculos).
- Multiples tasas de interes simultaneas dentro de un mismo expediente (hoy `CivilFamiliaStrategy` usa una
  sola tasa por expediente, tomada de la primera obligacion).
- Validar/enable Windows "Long Paths" en la maquina de desarrollo: la instalacion de PySide6 mostro un
  aviso de ruta larga durante `pip install` por vivir dentro de una carpeta de OneDrive con ruta profunda;
  no bloqueo el uso de QtWidgets pero puede afectar actualizaciones futuras de paquetes grandes.
- Confirmar si conviene excluir `.venv/` de la sincronizacion de OneDrive (hoy esta en `.gitignore` pero
  OneDrive igual intenta sincronizar carpetas no versionadas dentro de la carpeta del proyecto).
```

- [x] **Step 2: Commit**

```bash
git add Pendientes.md
git commit -m "docs: add phased backlog (Pendientes.md)"
```

---

### Task 17: Full verification pass

**Files:** none (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: all tests pass — the 48 pre-existing tests plus every test added in Tasks 2–13.

- [ ] **Step 2: Manual smoke test of the real flow**

Run: `.venv/Scripts/python.exe main.py` and manually:
1. Click "Nuevo expediente", fill radicado/demandante/demandado/fecha de corte, leave area on
   "Civil / Familia" (default), save.
2. Double-click the new row to open the detail page.
3. Click "Agregar obligacion", create a Puntual obligacion (e.g. concepto "Gastos medicos", valor
   427900.00, tasa 6.00, fecha de origen in the past relative to the expediente's fecha de corte).
4. Click "Agregar abono" with that obligacion row selected, register a partial payment.
5. Click "Liquidar" and confirm the Resultado screen shows a row per event and non-zero
   "Interes acumulado".

Expected: no crash, no unhandled traceback, the displayed saldo final is lower than the original valor by
at least the abono amount.

- [ ] **Step 3: Commit (only if Step 2 uncovered fixes)**

If manual verification requires code fixes, make them, re-run the full suite, and commit with a message
describing the specific fix (do not bundle unrelated changes).

---

## Self-review notes (already applied above)

- **Spec coverage:** database layer (Task 2–3), GUI shell + all 3 screens (Task 8–13), area selection +
  Strategy pattern (Task 5–6), EA→daily conversion (Task 4), specifications docs (Task 15), Pendientes.md
  (Task 16) — all spec sections have a corresponding task.
- **Type consistency verified:** `Payment(date, amount, reference)` field order matches its dataclass
  definition; `Rate` always wraps a fraction, never a raw percent, across Tasks 4 and 6;
  `AreaRegistry.get_strategy` keys (`"CIVIL_FAMILIA"`, etc.) match `AreaDerecho` enum `.value`s used
  throughout Tasks 2, 9 and 13.
- **Explicitly out of scope, not silently dropped:** Comercial/Laboral/Sancionatorio/Honorarios
  calculation, IPC indexation wiring, PDF/Word export, prescripcion/caducidad, business-day calendar — all
  captured in `Pendientes.md` (Task 16), matching the spec's "Explícitamente fuera de alcance" section.
