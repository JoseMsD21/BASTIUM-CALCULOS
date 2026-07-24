# Sprint 16 — Seguridad social, incapacidades y suspensiones (Laboral) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `LaboralStrategy` so a Laboral expediente can claim, as part of the judicial liquidation,
unpaid social-security contributions (pension, salud, ARL, FSP) plus the exact common/occupational
incapacidad and suspensión rules from the requirements PDF — without changing behavior for existing
Laboral expedientes that don't use these new fields.

**Architecture:** Two new pure calculators (`SeguridadSocialCalculator`, `IncapacidadCalculator`) in
`app/engine/labor/`, following the exact pattern already used by `MoratoryIndemnityCalculator`: they
compute amounts, `LaboralStrategy.liquidar()` turns those amounts into `Event`s, and the existing generic
`LiquidationCore`/`UniversalLiquidationService` engine processes them completely unchanged. A new
`eventos_laborales` table (polymorphic: suspensión / incapacidad común / incapacidad laboral) captures the
per-contract events; two new nullable columns on `obligaciones` (`incluir_seguridad_social`,
`nivel_riesgo_arl`) opt a contract into the cotización calculation.

**Tech Stack:** Python, SQLAlchemy (declarative models, SQLite), PySide6 (Qt GUI), pytest.

**Spec:** `docs/superpowers/specs/2026-07-24-seguridad-social-laboral-design.md` — read it before starting
if anything below is ambiguous; this plan implements it task-by-task.

---

### Task 1: `EventoLaboral` model (new table, new enums)

**Files:**
- Modify: `database/models.py`
- Test: `tests/database/test_models.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/database/test_models.py` (after `test_abono_asociado_a_obligacion`, before
`test_borrar_expediente_borra_en_cascada_obligaciones_y_abonos`):

```python
def test_evento_laboral_suspension_asociado_a_obligacion(session):
    expediente = Expediente(
        radicado="2026-00200",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.LABORAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1),
        valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=date(2020, 1, 1),
        fecha_fin=date(2020, 12, 31),
    )
    session.add(obligacion)
    session.flush()

    evento = EventoLaboral(
        obligacion_id=obligacion.id,
        tipo=TipoEventoLaboral.SUSPENSION,
        fecha_inicio=date(2020, 3, 1),
        fecha_fin=date(2020, 3, 15),
        motivo_suspension=MotivoSuspension.HUELGA,
    )
    session.add(evento)
    session.commit()

    assert obligacion.eventos_laborales[0].tipo == TipoEventoLaboral.SUSPENSION
    assert obligacion.eventos_laborales[0].motivo_suspension == MotivoSuspension.HUELGA


def test_evento_laboral_incapacidad_no_requiere_motivo_suspension(session):
    expediente = Expediente(
        radicado="2026-00201",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.LABORAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1),
        valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=date(2020, 1, 1),
        fecha_fin=date(2020, 12, 31),
    )
    session.add(obligacion)
    session.flush()

    evento = EventoLaboral(
        obligacion_id=obligacion.id,
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
        fecha_inicio=date(2020, 5, 1),
        fecha_fin=date(2020, 5, 3),
    )
    session.add(evento)
    session.commit()

    assert obligacion.eventos_laborales[0].motivo_suspension is None
```

Update the import line at the top of the file:

```python
from database.models import (
    Base, Expediente, Obligacion, Abono, AuditLog, AreaDerecho, TipoObligacion,
    EventoLaboral, TipoEventoLaboral, MotivoSuspension,
)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/database/test_models.py -k evento_laboral -v`
Expected: FAIL with `ImportError: cannot import name 'EventoLaboral' from 'database.models'`

- [ ] **Step 3: Implement `EventoLaboral` in `database/models.py`**

Add after `class TipoObligacion(enum.Enum): ...` (around line 58):

```python
class TipoEventoLaboral(enum.Enum):
    SUSPENSION = "SUSPENSION"
    INCAPACIDAD_COMUN = "INCAPACIDAD_COMUN"
    INCAPACIDAD_LABORAL = "INCAPACIDAD_LABORAL"


class MotivoSuspension(enum.Enum):
    HUELGA = "HUELGA"
    LICENCIA_NO_REMUNERADA = "LICENCIA_NO_REMUNERADA"
    DISCIPLINARIA = "DISCIPLINARIA"
```

Add `eventos_laborales` relationship to `Obligacion` (after the `abonos` relationship, around line 111):

```python
    eventos_laborales: Mapped[list["EventoLaboral"]] = relationship(
        back_populates="obligacion", cascade="all, delete-orphan"
    )
```

Add the new model class after `class Abono(Base): ...` (around line 124):

```python
class EventoLaboral(Base):
    """Suspension contractual o incapacidad (comun/laboral) dentro de un
    contrato Laboral -- tabla polimorfica, no dos tablas separadas: un mismo
    contrato puede tener varios eventos de cualquier tipo. `motivo_suspension`
    solo se llena cuando `tipo == SUSPENSION` (validado en
    LaboralStrategy, no aqui)."""
    __tablename__ = "eventos_laborales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    obligacion_id: Mapped[int] = mapped_column(ForeignKey("obligaciones.id"))
    tipo: Mapped[TipoEventoLaboral] = mapped_column(SAEnum(TipoEventoLaboral))
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    motivo_suspension: Mapped[MotivoSuspension | None] = mapped_column(
        SAEnum(MotivoSuspension), nullable=True
    )

    obligacion: Mapped["Obligacion"] = relationship(back_populates="eventos_laborales")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/database/test_models.py -v`
Expected: PASS (all tests in the file, including the 2 new ones)

- [ ] **Step 5: Commit**

```bash
git add database/models.py tests/database/test_models.py
git commit -m "feat: add EventoLaboral model for suspensiones e incapacidades laborales"
```

---

### Task 2: `incluir_seguridad_social` / `nivel_riesgo_arl` columns + migration script

**Files:**
- Modify: `database/models.py`
- Create: `scripts/migrate_seguridad_social_laboral.py`
- Test: `tests/scripts/test_migrate_seguridad_social_laboral.py`
- Test: `tests/database/test_models.py`

- [ ] **Step 1: Write the failing model test**

Append to `tests/database/test_models.py`:

```python
def test_obligacion_incluir_seguridad_social_default_false(session):
    expediente = Expediente(
        radicado="2026-00202",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.LABORAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1),
        valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=date(2020, 1, 1),
        fecha_fin=date(2020, 12, 31),
    )
    session.add(obligacion)
    session.commit()

    fetched = session.query(Obligacion).one()
    assert fetched.incluir_seguridad_social is False
    assert fetched.nivel_riesgo_arl is None


def test_obligacion_incluir_seguridad_social_con_nivel_riesgo(session):
    expediente = Expediente(
        radicado="2026-00203",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.LABORAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1),
        valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=date(2020, 1, 1),
        fecha_fin=date(2020, 12, 31),
        incluir_seguridad_social=True,
        nivel_riesgo_arl="I",
    )
    session.add(obligacion)
    session.commit()

    fetched = session.query(Obligacion).one()
    assert fetched.incluir_seguridad_social is True
    assert fetched.nivel_riesgo_arl == "I"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/database/test_models.py -k incluir_seguridad_social -v`
Expected: FAIL with `TypeError: 'incluir_seguridad_social' is an invalid keyword argument for Obligacion`

- [ ] **Step 3: Add the columns to `Obligacion` in `database/models.py`**

Add after the `trm_fecha_referencia` column (around line 106):

```python
    incluir_seguridad_social: Mapped[bool] = mapped_column(Boolean, default=False)
    nivel_riesgo_arl: Mapped[str | None] = mapped_column(String(2), nullable=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/database/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Write the failing migration test**

Create `tests/scripts/test_migrate_seguridad_social_laboral.py`:

```python
import sqlite3

import pytest

from scripts.migrate_seguridad_social_laboral import migrar


@pytest.fixture
def db_sin_columnas(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY, concepto TEXT)")
    con.execute("INSERT INTO obligaciones (id, concepto) VALUES (1, 'Liquidacion de contrato')")
    con.commit()
    con.close()
    return db_path


def test_migrar_agrega_las_dos_columnas_y_retorna_true(db_sin_columnas):
    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert {"incluir_seguridad_social", "nivel_riesgo_arl"} <= columnas


def test_migrar_preserva_las_filas_existentes_con_default_false(db_sin_columnas):
    migrar(db_sin_columnas)

    con = sqlite3.connect(db_sin_columnas)
    fila = con.execute(
        "SELECT concepto, incluir_seguridad_social, nivel_riesgo_arl FROM obligaciones WHERE id = 1"
    ).fetchone()
    con.close()
    assert fila == ("Liquidacion de contrato", 0, None)


def test_migrar_es_idempotente_segunda_corrida_retorna_false(db_sin_columnas):
    primera = migrar(db_sin_columnas)
    segunda = migrar(db_sin_columnas)
    assert primera is True
    assert segunda is False


def test_migrar_es_idempotente_si_ya_existe_solo_una_de_las_dos_columnas(db_sin_columnas):
    con = sqlite3.connect(db_sin_columnas)
    con.execute("ALTER TABLE obligaciones ADD COLUMN incluir_seguridad_social BOOLEAN NOT NULL DEFAULT 0")
    con.commit()
    con.close()

    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert {"incluir_seguridad_social", "nivel_riesgo_arl"} <= columnas
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/scripts/test_migrate_seguridad_social_laboral.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.migrate_seguridad_social_laboral'`

- [ ] **Step 7: Create `scripts/migrate_seguridad_social_laboral.py`**

```python
"""Migracion de esquema (Sprint 16): agrega las columnas incluir_seguridad_social
y nivel_riesgo_arl a la tabla obligaciones. Idempotente -- verifica con PRAGMA
table_info antes de alterar cada columna individualmente, mismo patron exacto
que scripts/migrate_moneda_trm.py (Sprint 12)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "incluir_seguridad_social": "BOOLEAN NOT NULL DEFAULT 0",
    "nivel_riesgo_arl": "VARCHAR(2)",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas incluir_seguridad_social/nivel_riesgo_arl si no
    existen. Retorna True si aplico al menos un ALTER TABLE, False si las dos
    columnas ya existian."""
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
        print("Columnas incluir_seguridad_social/nivel_riesgo_arl agregadas a obligaciones.")
    else:
        print("Las columnas ya existian, no se hizo nada.")
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `pytest tests/scripts/test_migrate_seguridad_social_laboral.py -v`
Expected: PASS (4 tests)

- [ ] **Step 9: Commit**

```bash
git add database/models.py tests/database/test_models.py scripts/migrate_seguridad_social_laboral.py tests/scripts/test_migrate_seguridad_social_laboral.py
git commit -m "feat: add incluir_seguridad_social/nivel_riesgo_arl columns to obligaciones"
```

---

### Task 3: `SeguridadSocialCalculator` — cotizaciones basicas, suspension, niveles ARL

**Files:**
- Create: `app/engine/labor/seguridad_social.py`
- Test: `tests/engine/labor/test_seguridad_social.py`

This calculator calls `get_parametro()`, which needs a database session. Follow the exact isolated-DB
fixture pattern already used in `tests/engine/labor/test_moratory_indemnity.py`.

- [ ] **Step 1: Write the failing tests**

Create `tests/engine/labor/test_seguridad_social.py`:

```python
from datetime import date, datetime as _dt
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _parametros_seguridad_social_en_memoria(monkeypatch):
    # SeguridadSocialCalculator.calcular lee SMLMV y las 7 claves SS_* via
    # parametro_service en cada llamada -- fixture aislada de disco, mismo
    # criterio que tests/engine/labor/test_moratory_indemnity.py.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="SMLMV", valor=Decimal("877803.00"), vigente_desde=date(2020, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    valores_abiertos = {
        "SS_PENSION_PCT": Decimal("0.16"),
        "SS_SALUD_PCT": Decimal("0.125"),
        "SS_ARL_NIVEL_I_PCT": Decimal("0.00522"),
        "SS_ARL_NIVEL_II_PCT": Decimal("0.01044"),
        "SS_ARL_NIVEL_III_PCT": Decimal("0.02436"),
        "SS_ARL_NIVEL_IV_PCT": Decimal("0.04350"),
        "SS_ARL_NIVEL_V_PCT": Decimal("0.06960"),
        "SS_FSP_TRAMO_1_PCT": Decimal("0.01"),
        "SS_FSP_TRAMO_2_PCT": Decimal("0.012"),
        "SS_FSP_TRAMO_3_PCT": Decimal("0.014"),
        "SS_FSP_TRAMO_4_PCT": Decimal("0.016"),
        "SS_FSP_TRAMO_5_PCT": Decimal("0.018"),
        "SS_FSP_TRAMO_6_PCT": Decimal("0.02"),
    }
    for clave, valor in valores_abiertos.items():
        session.add(ParametroLegal(
            clave=clave, valor=valor, vigente_desde=date(1900, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    session.commit()
    session.close()


def test_cotizacion_basica_sin_suspension_ni_fsp():
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("3000000.00"), dias_trabajados=30, dias_suspension=0,
        nivel_riesgo_arl="I", fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.ibc_mensual == Decimal("3000000.00")
    assert resultado.monto_pension == Decimal("480000.00")
    assert resultado.monto_salud == Decimal("375000.00")
    assert resultado.monto_arl == Decimal("15660.00")
    assert resultado.monto_fsp == Decimal("0.00")
    assert resultado.total == Decimal("870660.00")


def test_suspension_parcial_excluye_solo_arl_de_esos_dias():
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("3000000.00"), dias_trabajados=30, dias_suspension=15,
        nivel_riesgo_arl="I", fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.monto_pension == Decimal("480000.00")  # sin cambio
    assert resultado.monto_salud == Decimal("375000.00")  # sin cambio
    assert resultado.monto_arl == Decimal("7830.00")  # mitad de dias con ARL
    assert resultado.total == Decimal("862830.00")


@pytest.mark.parametrize("nivel,arl_esperado,total_esperado", [
    ("I", Decimal("15660.00"), Decimal("870660.00")),
    ("II", Decimal("31320.00"), Decimal("886320.00")),
    ("III", Decimal("73080.00"), Decimal("928080.00")),
    ("IV", Decimal("130500.00"), Decimal("985500.00")),
    ("V", Decimal("208800.00"), Decimal("1063800.00")),
])
def test_cada_nivel_de_riesgo_arl(nivel, arl_esperado, total_esperado):
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("3000000.00"), dias_trabajados=30, dias_suspension=0,
        nivel_riesgo_arl=nivel, fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.monto_arl == arl_esperado
    assert resultado.total == total_esperado


def test_ibc_se_ajusta_al_piso_de_1_smmlv():
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("500000.00"), dias_trabajados=30, dias_suspension=0,
        nivel_riesgo_arl="I", fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.ibc_mensual == Decimal("877803.00")
    assert resultado.monto_pension == Decimal("140448.48")
    assert resultado.monto_salud == Decimal("109725.38")
    assert resultado.monto_arl == Decimal("4582.13")
    assert resultado.monto_fsp == Decimal("0.00")


def test_ibc_se_ajusta_al_techo_de_25_smmlv():
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("30000000.00"), dias_trabajados=30, dias_suspension=0,
        nivel_riesgo_arl="I", fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.ibc_mensual == Decimal("21945075.00")
    assert resultado.monto_pension == Decimal("3511212.00")
    assert resultado.monto_salud == Decimal("2743134.38")
    assert resultado.monto_arl == Decimal("114553.29")
    assert resultado.monto_fsp == Decimal("438901.50")  # IBC cae en tramo 6 (>20 SMMLV)
    assert resultado.total == Decimal("6807801.17")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/engine/labor/test_seguridad_social.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.engine.labor.seguridad_social'`

- [ ] **Step 3: Implement `app/engine/labor/seguridad_social.py`**

```python
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.engine.math.rounding import Rounding
from app.services.parametro_service import get_parametro


@dataclass(frozen=True)
class CotizacionesResult:
    ibc_mensual: Decimal
    monto_pension: Decimal
    monto_salud: Decimal
    monto_arl: Decimal
    monto_fsp: Decimal
    total: Decimal


class SeguridadSocialCalculator:
    """
    Cotizaciones de seguridad social (pension, salud, ARL, FSP) sobre el IBC
    de un contrato laboral, para reclamarlas como aportes dejados de pagar
    dentro de una liquidacion judicial (PDF pags. 51-52, "Middleware de
    Seguridad Social: Cotizaciones").

    Base de aporte: monto total (empleador + trabajador), no solo la porcion
    del empleador -- decision tomada con el usuario, ver spec del Sprint 16.
    """

    @staticmethod
    def calcular(
        salario_base: Decimal,
        dias_trabajados: int,
        dias_suspension: int,
        nivel_riesgo_arl: str,
        fecha_referencia: date,
    ) -> "CotizacionesResult":
        dias_trab = Decimal(str(dias_trabajados))
        dias_susp = Decimal(str(dias_suspension))

        smmlv = get_parametro("SMLMV", date(fecha_referencia.year, 1, 1))
        ibc = min(max(salario_base, smmlv), smmlv * Decimal("25"))  # PDF pag. 51: 1-25 SMMLV

        monto_pension = Rounding.money(
            ibc * get_parametro("SS_PENSION_PCT", fecha_referencia) * dias_trab / Decimal("30")
        )
        monto_salud = Rounding.money(
            ibc * get_parametro("SS_SALUD_PCT", fecha_referencia) * dias_trab / Decimal("30")
        )

        dias_con_arl = dias_trab - dias_susp  # suspension excluye SOLO ARL (PDF pag. 52)
        arl_pct = get_parametro(f"SS_ARL_NIVEL_{nivel_riesgo_arl}_PCT", fecha_referencia)
        monto_arl = Rounding.money(ibc * arl_pct * dias_con_arl / Decimal("30"))

        monto_fsp = Decimal("0.00")
        if ibc >= smmlv * Decimal("4"):
            fsp_pct = _resolver_tramo_fsp(ibc, smmlv, fecha_referencia)
            monto_fsp = Rounding.money(ibc * fsp_pct * dias_trab / Decimal("30"))

        total = monto_pension + monto_salud + monto_arl + monto_fsp
        return CotizacionesResult(
            ibc_mensual=ibc, monto_pension=monto_pension, monto_salud=monto_salud,
            monto_arl=monto_arl, monto_fsp=monto_fsp, total=total,
        )


def _resolver_tramo_fsp(ibc: Decimal, smmlv: Decimal, fecha: date) -> Decimal:
    # Tramos del Fondo de Solidaridad Pensional, Ley 797/2003 art. 8, en
    # multiplos de SMMLV del IBC (el PDF solo describe "escala progresiva
    # desde 1% hasta 2%", sin tramos exactos -- ver spec del Sprint 16).
    tramos = [
        (Decimal("16"), "SS_FSP_TRAMO_1_PCT"),   # 4  - 16 SMMLV
        (Decimal("17"), "SS_FSP_TRAMO_2_PCT"),   # 16 - 17 SMMLV
        (Decimal("18"), "SS_FSP_TRAMO_3_PCT"),   # 17 - 18 SMMLV
        (Decimal("19"), "SS_FSP_TRAMO_4_PCT"),   # 18 - 19 SMMLV
        (Decimal("20"), "SS_FSP_TRAMO_5_PCT"),   # 19 - 20 SMMLV
    ]
    for limite_superior, clave in tramos:
        if ibc < smmlv * limite_superior:
            return get_parametro(clave, fecha)
    return get_parametro("SS_FSP_TRAMO_6_PCT", fecha)  # > 20 SMMLV
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/engine/labor/test_seguridad_social.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add app/engine/labor/seguridad_social.py tests/engine/labor/test_seguridad_social.py
git commit -m "feat: add SeguridadSocialCalculator (cotizaciones pension/salud/ARL)"
```

---

### Task 4: `SeguridadSocialCalculator` — FSP (tramos exactos y umbral)

**Files:**
- Modify: `tests/engine/labor/test_seguridad_social.py`

FSP logic was already implemented in Task 3; this task adds the boundary tests the Definicion de Hecho
requires (exact tramo transitions), calling the private `_resolver_tramo_fsp` helper directly.

- [ ] **Step 1: Write the failing tests**

Append to `tests/engine/labor/test_seguridad_social.py`:

```python
def test_fsp_no_aplica_justo_debajo_del_umbral_de_4_smmlv():
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("3511211.00"), dias_trabajados=30, dias_suspension=0,
        nivel_riesgo_arl="I", fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.monto_fsp == Decimal("0.00")


def test_fsp_aplica_justo_en_el_umbral_exacto_de_4_smmlv():
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("3511212.00"), dias_trabajados=30, dias_suspension=0,
        nivel_riesgo_arl="I", fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.monto_fsp == Decimal("35112.12")  # 3511212.00 * 1% (tramo 1)


@pytest.mark.parametrize("multiplo_smmlv,tramo_pct_esperado", [
    (Decimal("4"), Decimal("0.01")),
    (Decimal("16"), Decimal("0.012")),
    (Decimal("17"), Decimal("0.014")),
    (Decimal("18"), Decimal("0.016")),
    (Decimal("19"), Decimal("0.018")),
    (Decimal("20"), Decimal("0.02")),
    (Decimal("25"), Decimal("0.02")),
])
def test_resolver_tramo_fsp_en_cada_frontera(multiplo_smmlv, tramo_pct_esperado):
    from app.engine.labor.seguridad_social import _resolver_tramo_fsp

    smmlv = Decimal("877803.00")
    ibc = smmlv * multiplo_smmlv

    assert _resolver_tramo_fsp(ibc, smmlv, date(2020, 12, 31)) == tramo_pct_esperado
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/engine/labor/test_seguridad_social.py -k "fsp or tramo" -v`
Expected: These specific assertions should already PASS given Task 3's implementation — if any FAILS,
it means the tramo boundary logic (`ibc < smmlv * limite_superior`) does not match; re-check the
`_resolver_tramo_fsp` loop order and comparison operator before proceeding.

- [ ] **Step 3: No implementation change expected**

If Step 2 passed already, there is nothing to implement — this task exists purely to lock in the boundary
behavior with explicit tests, per the Definicion de Hecho requirement ("fronteras de tramos FSP en
SMMLV"). If it failed, fix `_resolver_tramo_fsp` in `app/engine/labor/seguridad_social.py` until all
assertions pass, re-running the same command.

- [ ] **Step 4: Run the whole file to confirm no regressions**

Run: `pytest tests/engine/labor/test_seguridad_social.py -v`
Expected: PASS (all tests, 9 from Task 3 + 9 from this task)

- [ ] **Step 5: Commit**

```bash
git add tests/engine/labor/test_seguridad_social.py
git commit -m "test: lock in FSP tramo boundaries for SeguridadSocialCalculator"
```

---

### Task 5: `IncapacidadCalculator`

**Files:**
- Create: `app/engine/labor/incapacidad.py`
- Test: `tests/engine/labor/test_incapacidad.py`

This calculator does not call `get_parametro` (percentages are fixed constants straight from the PDF, not
subject to normative reform the way cotizacion rates are) — no database fixture needed.

- [ ] **Step 1: Write the failing tests**

Create `tests/engine/labor/test_incapacidad.py`:

```python
from decimal import Decimal

from app.engine.labor.incapacidad import IncapacidadCalculator
from database.models import TipoEventoLaboral


def test_incapacidad_comun_un_dia_solo_empleador():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN, ibc_mensual=Decimal("3000000.00"), dias_incapacidad=1,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("66670.00")
    assert len(resultado.tramos) == 1
    assert resultado.tramos[0].pagador == "EMPLEADOR"
    assert resultado.tramos[0].dias == 1


def test_incapacidad_comun_dos_dias_solo_empleador():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN, ibc_mensual=Decimal("3000000.00"), dias_incapacidad=2,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("133340.00")
    assert len(resultado.tramos) == 1
    assert resultado.tramos[0].pagador == "EMPLEADOR"


def test_incapacidad_comun_tres_dias_cruza_a_eps():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN, ibc_mensual=Decimal("3000000.00"), dias_incapacidad=3,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("133340.00")  # solo dias 1-2
    assert len(resultado.tramos) == 2
    assert resultado.tramos[1].pagador == "EPS"
    assert resultado.tramos[1].dias == 1
    assert resultado.tramos[1].monto == Decimal("66670.00")


def test_incapacidad_comun_dia_90_ultimo_dia_del_tramo_eps_66pct():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN, ibc_mensual=Decimal("3000000.00"), dias_incapacidad=90,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("133340.00")
    assert len(resultado.tramos) == 2
    assert resultado.tramos[1].dias == 88
    assert resultado.tramos[1].monto == Decimal("5866960.00")


def test_incapacidad_comun_dia_91_entra_tramo_eps_50pct():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN, ibc_mensual=Decimal("3000000.00"), dias_incapacidad=91,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("133340.00")
    assert len(resultado.tramos) == 3
    assert resultado.tramos[2].pagador == "EPS"
    assert resultado.tramos[2].dias == 1
    assert resultado.tramos[2].porcentaje == Decimal("0.50")
    assert resultado.tramos[2].monto == Decimal("50000.00")


def test_incapacidad_comun_dia_180_ultimo_dia_modelado():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN, ibc_mensual=Decimal("3000000.00"), dias_incapacidad=180,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("133340.00")
    assert len(resultado.tramos) == 3
    assert resultado.tramos[2].dias == 90
    assert resultado.tramos[2].monto == Decimal("4500000.00")


def test_incapacidad_laboral_arl_paga_100pct_desde_dia_1_nada_a_cargo_empleador():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_LABORAL, ibc_mensual=Decimal("3000000.00"), dias_incapacidad=10,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("0.00")
    assert len(resultado.tramos) == 1
    assert resultado.tramos[0].pagador == "ARL"
    assert resultado.tramos[0].porcentaje == Decimal("1.00")
    assert resultado.tramos[0].monto == Decimal("1000000.00")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/engine/labor/test_incapacidad.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.engine.labor.incapacidad'`

- [ ] **Step 3: Implement `app/engine/labor/incapacidad.py`**

```python
from dataclasses import dataclass
from decimal import Decimal

from app.engine.math.rounding import Rounding
from database.models import TipoEventoLaboral


@dataclass(frozen=True)
class TramoIncapacidad:
    dias: int
    pagador: str  # "EMPLEADOR" | "EPS" | "ARL"
    porcentaje: Decimal
    monto: Decimal


@dataclass(frozen=True)
class IncapacidadResult:
    tramos: list
    monto_a_cargo_empleador: Decimal


class IncapacidadCalculator:
    """
    Desglose de pagadores de una incapacidad (PDF pag. 52, "4. Manejo de
    Eventos y Estados"):
      - Incapacidad comun: dias 1-2 empleador 66.67%, dias 3-90 EPS 66.67%,
        dias 91-180 EPS 50%.
      - Incapacidad laboral: ARL paga 100% desde el dia 1.

    Retorna el desglose COMPLETO de todos los pagadores (informativo, para
    auditoria del juez) pero solo `monto_a_cargo_empleador` es deuda real del
    expediente -- lo que paga la EPS o la ARL no es un hecho reclamable en
    este alcance (decision tomada con el usuario, ver spec del Sprint 16).
    """

    @staticmethod
    def calcular(
        tipo: TipoEventoLaboral, ibc_mensual: Decimal, dias_incapacidad: int
    ) -> "IncapacidadResult":
        ibc_diario = ibc_mensual / Decimal("30")

        if tipo == TipoEventoLaboral.INCAPACIDAD_LABORAL:
            monto = Rounding.money(ibc_diario * dias_incapacidad)
            tramo = TramoIncapacidad(dias_incapacidad, "ARL", Decimal("1.00"), monto)
            return IncapacidadResult([tramo], Decimal("0.00"))

        tramos = []
        dias_1_2 = min(dias_incapacidad, 2)
        if dias_1_2 > 0:
            monto = Rounding.money(ibc_diario * Decimal("0.6667") * dias_1_2)
            tramos.append(TramoIncapacidad(dias_1_2, "EMPLEADOR", Decimal("0.6667"), monto))

        dias_3_90 = max(0, min(dias_incapacidad, 90) - 2)
        if dias_3_90 > 0:
            monto = Rounding.money(ibc_diario * Decimal("0.6667") * dias_3_90)
            tramos.append(TramoIncapacidad(dias_3_90, "EPS", Decimal("0.6667"), monto))

        dias_91_180 = max(0, min(dias_incapacidad, 180) - 90)
        if dias_91_180 > 0:
            monto = Rounding.money(ibc_diario * Decimal("0.50") * dias_91_180)
            tramos.append(TramoIncapacidad(dias_91_180, "EPS", Decimal("0.50"), monto))

        monto_empleador = next(
            (t.monto for t in tramos if t.pagador == "EMPLEADOR"), Decimal("0.00")
        )
        return IncapacidadResult(tramos, monto_empleador)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/engine/labor/test_incapacidad.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add app/engine/labor/incapacidad.py tests/engine/labor/test_incapacidad.py
git commit -m "feat: add IncapacidadCalculator (dias 1-2/3-90/91-180 comun, 100% laboral)"
```

---

### Task 6: Catalogo de parametros + script de siembra (12 claves nuevas)

**Files:**
- Modify: `app/services/parametro_service.py`
- Modify: `scripts/migrate_parametros_legales.py`
- Modify: `tests/scripts/test_migrate_parametros_legales.py`

- [ ] **Step 1: Write the failing test**

Modify `tests/scripts/test_migrate_parametros_legales.py`: rename the test and update its expected set.
Replace the whole `test_migrar_siembra_las_17_claves_del_catalogo` function with:

```python
def test_migrar_siembra_las_29_claves_del_catalogo():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    claves = {fila.clave for fila in session.query(ParametroLegal).all()}
    session.close()
    assert claves == {
        "USURA_MULTIPLICADOR", "CUOTA_LITIS_INDIVIDUAL_PCT", "HONORARIOS_TOTAL_PCT",
        "ET635_PUNTOS_DESCUENTO", "CIVIL_ANNUAL_RATE",
        "PRESCRIPCION_EJECUTIVA_MESES", "PRESCRIPCION_ORDINARIA_MESES",
        "PRESCRIPCION_HONORARIOS_MESES", "PRESCRIPCION_CAMBIARIA_DIRECTA_MESES",
        "PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES",
        "PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES",
        "CADUCIDAD_IMPUGNACION_INEFICACIA_SOCIETARIA_MESES",
        "SMLMV", "IPC_INDICE_ACUMULADO", "IBC_CONSUMO_ORDINARIO", "USURA_CONSUMO_ORDINARIO",
        "UVT",
        "SS_PENSION_PCT", "SS_SALUD_PCT",
        "SS_ARL_NIVEL_I_PCT", "SS_ARL_NIVEL_II_PCT", "SS_ARL_NIVEL_III_PCT",
        "SS_ARL_NIVEL_IV_PCT", "SS_ARL_NIVEL_V_PCT",
        "SS_FSP_TRAMO_1_PCT", "SS_FSP_TRAMO_2_PCT", "SS_FSP_TRAMO_3_PCT",
        "SS_FSP_TRAMO_4_PCT", "SS_FSP_TRAMO_5_PCT", "SS_FSP_TRAMO_6_PCT",
    }
```

Also append a new test at the end of the file:

```python
def test_migrar_ss_pension_pct_coincide_con_el_pdf():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    fila = session.query(ParametroLegal).filter_by(clave="SS_PENSION_PCT").one()
    session.close()
    assert fila.valor == Decimal("0.16")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/scripts/test_migrate_parametros_legales.py -k "29_claves or ss_pension" -v`
Expected: FAIL — `test_migrar_siembra_las_29_claves_del_catalogo` fails because the current catalog only
has 17 keys; `test_migrar_ss_pension_pct_coincide_con_el_pdf` fails with `NoResultFound`.

- [ ] **Step 3: Add the 12 new keys to `CATALOGO_PARAMETROS`**

In `app/services/parametro_service.py`, add before the closing `}` of `CATALOGO_PARAMETROS` (after the
`"UVT"` entry):

```python
    "SS_PENSION_PCT": InfoParametro(
        "Cotizacion total a pension (% del IBC, empleador + trabajador)", "Seguridad social",
        "PDF pagina 51", ModoResolucion.ABIERTO,
    ),
    "SS_SALUD_PCT": InfoParametro(
        "Cotizacion total a salud (% del IBC, empleador + trabajador)", "Seguridad social",
        "PDF pagina 51", ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_I_PCT": InfoParametro(
        "Cotizacion ARL nivel de riesgo I (% del IBC)", "Seguridad social",
        "PDF pagina 52", ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_II_PCT": InfoParametro(
        "Cotizacion ARL nivel de riesgo II (% del IBC)", "Seguridad social",
        "Decreto 1607/2002 (PDF solo cita los extremos I y V)", ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_III_PCT": InfoParametro(
        "Cotizacion ARL nivel de riesgo III (% del IBC)", "Seguridad social",
        "Decreto 1607/2002 (PDF solo cita los extremos I y V)", ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_IV_PCT": InfoParametro(
        "Cotizacion ARL nivel de riesgo IV (% del IBC)", "Seguridad social",
        "Decreto 1607/2002 (PDF solo cita los extremos I y V)", ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_V_PCT": InfoParametro(
        "Cotizacion ARL nivel de riesgo V (% del IBC)", "Seguridad social",
        "PDF pagina 52", ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_1_PCT": InfoParametro(
        "FSP: tramo 4-16 SMMLV (% del IBC)", "Seguridad social",
        "Ley 797/2003 art. 8 (PDF solo describe 'desde 1% hasta 2%')", ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_2_PCT": InfoParametro(
        "FSP: tramo 16-17 SMMLV (% del IBC)", "Seguridad social",
        "Ley 797/2003 art. 8", ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_3_PCT": InfoParametro(
        "FSP: tramo 17-18 SMMLV (% del IBC)", "Seguridad social",
        "Ley 797/2003 art. 8", ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_4_PCT": InfoParametro(
        "FSP: tramo 18-19 SMMLV (% del IBC)", "Seguridad social",
        "Ley 797/2003 art. 8", ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_5_PCT": InfoParametro(
        "FSP: tramo 19-20 SMMLV (% del IBC)", "Seguridad social",
        "Ley 797/2003 art. 8", ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_6_PCT": InfoParametro(
        "FSP: tramo mayor a 20 SMMLV (% del IBC)", "Seguridad social",
        "Ley 797/2003 art. 8", ModoResolucion.ABIERTO,
    ),
```

- [ ] **Step 4: Seed the 12 new keys in `scripts/migrate_parametros_legales.py`**

Add to the `valores_unicos` list inside `migrar()` (after `("CIVIL_ANNUAL_RATE", ...)`):

```python
            ("SS_PENSION_PCT", Decimal("0.16"), ANCLA_SIN_FECHA_NORMA),
            ("SS_SALUD_PCT", Decimal("0.125"), ANCLA_SIN_FECHA_NORMA),
            ("SS_ARL_NIVEL_I_PCT", Decimal("0.00522"), ANCLA_SIN_FECHA_NORMA),
            ("SS_ARL_NIVEL_II_PCT", Decimal("0.01044"), ANCLA_SIN_FECHA_NORMA),
            ("SS_ARL_NIVEL_III_PCT", Decimal("0.02436"), ANCLA_SIN_FECHA_NORMA),
            ("SS_ARL_NIVEL_IV_PCT", Decimal("0.04350"), ANCLA_SIN_FECHA_NORMA),
            ("SS_ARL_NIVEL_V_PCT", Decimal("0.06960"), ANCLA_SIN_FECHA_NORMA),
            ("SS_FSP_TRAMO_1_PCT", Decimal("0.01"), ANCLA_SIN_FECHA_NORMA),
            ("SS_FSP_TRAMO_2_PCT", Decimal("0.012"), ANCLA_SIN_FECHA_NORMA),
            ("SS_FSP_TRAMO_3_PCT", Decimal("0.014"), ANCLA_SIN_FECHA_NORMA),
            ("SS_FSP_TRAMO_4_PCT", Decimal("0.016"), ANCLA_SIN_FECHA_NORMA),
            ("SS_FSP_TRAMO_5_PCT", Decimal("0.018"), ANCLA_SIN_FECHA_NORMA),
            ("SS_FSP_TRAMO_6_PCT", Decimal("0.02"), ANCLA_SIN_FECHA_NORMA),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/scripts/test_migrate_parametros_legales.py -v`
Expected: PASS (all tests in the file)

- [ ] **Step 6: Run the full parametro_service test suite for regressions**

Run: `pytest tests/services/test_parametro_service.py tests/views/test_configuracion.py -v`
Expected: PASS (the configuracion view test reads `len(CATALOGO_PARAMETROS)` dynamically, so it adapts
automatically)

- [ ] **Step 7: Commit**

```bash
git add app/services/parametro_service.py scripts/migrate_parametros_legales.py tests/scripts/test_migrate_parametros_legales.py
git commit -m "feat: add 12 seguridad social parametros to CATALOGO_PARAMETROS"
```

---

### Task 7: `_capital_concepts` + validacion de `nivel_riesgo_arl`

**Files:**
- Modify: `app/engine/liquidation/engine.py`
- Modify: `app/services/area_strategy.py`
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Write the failing test**

In `tests/services/test_area_strategy.py`, append inside `class TestLaboralStrategy:` (after
`test_fecha_fin_anterior_a_fecha_inicio_lanza_value_error`):

```python
    def test_incluir_seguridad_social_sin_nivel_riesgo_lanza_value_error(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = None

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_area_strategy.py -k incluir_seguridad_social_sin_nivel -v`
Expected: FAIL — no `ValueError` is raised today (the field doesn't exist yet on the validation path, so
this liquidates successfully instead of raising)

- [ ] **Step 3: Add the validation to `LaboralStrategy._validar_obligacion_laboral`**

In `app/services/area_strategy.py`, inside `_validar_obligacion_laboral` (around line 406, after the
`pagada`/`fecha_pago_total` check), add:

```python
        if obligacion.incluir_seguridad_social and not obligacion.nivel_riesgo_arl:
            raise ValueError(
                "Si se incluyen cotizaciones de seguridad social, 'nivel_riesgo_arl' "
                "(I-V) es obligatorio."
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/services/test_area_strategy.py -k TestLaboralStrategy -v`
Expected: PASS (all `TestLaboralStrategy` tests, including the new one)

- [ ] **Step 5: Add the new event types to `_capital_concepts`**

In `app/engine/liquidation/engine.py`, update the `_capital_concepts` set (line ~28-34):

```python
        self._capital_concepts = {
            "INSTALLMENT", "CHILD_SUPPORT", "CLOTHING", "MULTA",
            "CESANTIAS", "INTERESES_CESANTIAS", "PRIMA_JUNIO", "PRIMA_DICIEMBRE", "SANCION_MORATORIA",
            "DANO_EMERGENTE", "LUCRO_CESANTE_CONSOLIDADO", "DANOS_MORALES", "CAPITAL_PAGARE",
            "CAPITAL_LETRA_CAMBIO", "CAPITAL_CHEQUE", "CAPITAL_FACTURA",
            "MULTA_SANCIONATORIA", "HONORARIOS_PROFESIONALES", "COSTAS_PROCESALES", "VACACIONES",
            "COTIZACION_PENSION", "COTIZACION_SALUD", "COTIZACION_ARL", "COTIZACION_FSP",
            "INCAPACIDAD_EMPLEADOR", "SUSPENSION_INFORMATIVA", "INCAPACIDAD_INFORMATIVA",
        }
```

(`SUSPENSION_INFORMATIVA`/`INCAPACIDAD_INFORMATIVA` always carry `amount=0.00` — they land in
`_capital_concepts` purely so the engine accepts them and records them in the audit trace, same
mechanism the engine already uses for its own zero-impact `LIQUIDATION_CUTOFF` closing item.)

- [ ] **Step 6: Run the full liquidation engine test suite for regressions**

Run: `pytest tests/liquidation/ tests/services/test_area_strategy.py -v`
Expected: PASS (no existing test references these new event types, so this is purely additive)

- [ ] **Step 7: Commit**

```bash
git add app/engine/liquidation/engine.py app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat: recognize seguridad social/incapacidad event types, validate nivel_riesgo_arl"
```

---

### Task 8: Wiring en `LaboralStrategy` — cotizaciones de seguridad social

**Files:**
- Modify: `app/services/area_strategy.py`
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Write the failing test**

Append inside `class TestLaboralStrategy:`:

```python
    def test_incluir_seguridad_social_agrega_cotizaciones_a_la_deuda(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "COTIZACION_PENSION" in tipos_evento
        assert "COTIZACION_SALUD" in tipos_evento
        assert "COTIZACION_ARL" in tipos_evento
        # 7974236.10 (prestaciones existentes) + cotizaciones sobre 365 dias,
        # IBC 3000000.00, nivel I, sin suspension ni FSP (ver SeguridadSocialCalculator):
        # pension = 3000000*0.16*365/30 = 5840000.00
        # salud   = 3000000*0.125*365/30 = 4562500.00
        # arl     = 3000000*0.00522*365/30 = 190530.00
        assert resultado.final_balance().principal == Decimal("18567266.10")

    def test_sin_incluir_seguridad_social_no_hay_regresion(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        # incluir_seguridad_social queda en su default (False)

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "COTIZACION_PENSION" not in tipos_evento
        assert resultado.final_balance().principal == Decimal("7974236.10")
```

Also, near the top of `tests/services/test_area_strategy.py`, extend the autouse
`_parametros_legales_en_memoria` fixture (this file's tests share it, so the new `TestLaboralStrategy`
cases need the SS_* keys seeded too) — add right before the final `session.commit()`:

```python
    session.add(ParametroLegal(
        clave="SS_PENSION_PCT", valor=_Decimal("0.16"), vigente_desde=_date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.add(ParametroLegal(
        clave="SS_SALUD_PCT", valor=_Decimal("0.125"), vigente_desde=_date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    for nivel, valor in {
        "I": _Decimal("0.00522"), "II": _Decimal("0.01044"), "III": _Decimal("0.02436"),
        "IV": _Decimal("0.04350"), "V": _Decimal("0.06960"),
    }.items():
        session.add(ParametroLegal(
            clave=f"SS_ARL_NIVEL_{nivel}_PCT", valor=valor, vigente_desde=_date(1900, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    for i, valor in enumerate(
        [_Decimal("0.01"), _Decimal("0.012"), _Decimal("0.014"), _Decimal("0.016"),
         _Decimal("0.018"), _Decimal("0.02")], start=1
    ):
        session.add(ParametroLegal(
            clave=f"SS_FSP_TRAMO_{i}_PCT", valor=valor, vigente_desde=_date(1900, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_area_strategy.py -k incluir_seguridad_social_agrega -v`
Expected: FAIL — `AttributeError` or the assertion fails because `LaboralStrategy.liquidar` does not read
`incluir_seguridad_social` yet, so no `COTIZACION_*` events are produced.

- [ ] **Step 3: Wire `SeguridadSocialCalculator` into `LaboralStrategy.liquidar`**

In `app/services/area_strategy.py`, add the import at the top (next to the existing
`MoratoryIndemnityCalculator` import):

```python
from app.engine.labor.seguridad_social import SeguridadSocialCalculator
```

Inside `LaboralStrategy.liquidar`, after the existing `eventos = LaborScheduler(...).generate()` line and
before the `fecha_referencia_mora` block, add:

```python
        if obligacion.incluir_seguridad_social:
            dias_suspension = sum(
                (evento.fecha_fin - evento.fecha_inicio).days
                for evento in obligacion.eventos_laborales
                if evento.tipo.value == "SUSPENSION"
            )
            cotizaciones = SeguridadSocialCalculator.calcular(
                salario_base=obligacion.valor,
                dias_trabajados=dias_trabajados,
                dias_suspension=dias_suspension,
                nivel_riesgo_arl=obligacion.nivel_riesgo_arl,
                fecha_referencia=obligacion.fecha_fin,
            )
            for concepto, monto in [
                ("COTIZACION_PENSION", cotizaciones.monto_pension),
                ("COTIZACION_SALUD", cotizaciones.monto_salud),
                ("COTIZACION_ARL", cotizaciones.monto_arl),
                ("COTIZACION_FSP", cotizaciones.monto_fsp),
            ]:
                if monto > Decimal("0.00"):
                    eventos.append(Event(
                        date=obligacion.fecha_fin, payload={"amount": monto}, event_type=concepto,
                    ))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/services/test_area_strategy.py -k TestLaboralStrategy -v`
Expected: PASS (all `TestLaboralStrategy` tests)

- [ ] **Step 5: Run the full suite for regressions**

Run: `pytest tests/ -v`
Expected: PASS (no test elsewhere constructs a Laboral `Obligacion` with `incluir_seguridad_social=True`,
so this is purely additive)

- [ ] **Step 6: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat: wire SeguridadSocialCalculator into LaboralStrategy.liquidar"
```

---

### Task 9: Wiring en `LaboralStrategy` — incapacidades y suspensiones

**Files:**
- Modify: `app/services/area_strategy.py`
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Write the failing test**

Append inside `class TestLaboralStrategy:`:

```python
    def test_incapacidad_comun_agrega_solo_el_monto_del_empleador_a_la_deuda(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [EventoLaboral(
            obligacion_id=1, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
            fecha_inicio=date(2020, 5, 1), fecha_fin=date(2020, 5, 4),  # 3 dias
        )]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "INCAPACIDAD_EMPLEADOR" in tipos_evento
        assert "INCAPACIDAD_INFORMATIVA" in tipos_evento
        # IBC = 3000000.00 (sin suspension, sin FSP); dias 1-2 empleador
        # 66.67% = 133340.00; dia 3 EPS 66.67% = 66670.00 (informativo, no suma).
        eventos_incapacidad_empleador = [
            item for item in resultado.items if item.balance.event_type == "INCAPACIDAD_EMPLEADOR"
        ]
        assert eventos_incapacidad_empleador[0].capital_base >= Decimal("133340.00")

    def test_incapacidad_laboral_no_agrega_nada_a_la_deuda_pero_deja_traza(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [EventoLaboral(
            obligacion_id=1, tipo=TipoEventoLaboral.INCAPACIDAD_LABORAL,
            fecha_inicio=date(2020, 5, 1), fecha_fin=date(2020, 5, 11),  # 10 dias
        )]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "INCAPACIDAD_INFORMATIVA" in tipos_evento
        assert "INCAPACIDAD_EMPLEADOR" not in tipos_evento

    def test_suspension_excluye_arl_de_esos_dias_y_deja_traza(self):
        from database.models import EventoLaboral, MotivoSuspension, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [EventoLaboral(
            obligacion_id=1, tipo=TipoEventoLaboral.SUSPENSION,
            fecha_inicio=date(2020, 3, 1), fecha_fin=date(2020, 3, 31),  # 30 dias
            motivo_suspension=MotivoSuspension.HUELGA,
        )]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SUSPENSION_INFORMATIVA" in tipos_evento
        assert "COTIZACION_ARL" in tipos_evento
        eventos_arl = [item for item in resultado.items if item.balance.event_type == "COTIZACION_ARL"]
        # dias_trabajados=365, dias_suspension=30: arl = 3000000*0.00522*(365-30)/30
        assert eventos_arl[0].capital_base > Decimal("0.00")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_area_strategy.py -k "incapacidad or suspension" -v`
Expected: FAIL — `LaboralStrategy.liquidar` doesn't read `obligacion.eventos_laborales` yet, so no
`INCAPACIDAD_*`/`SUSPENSION_INFORMATIVA` events are produced.

- [ ] **Step 3: Wire `IncapacidadCalculator` and the suspension trace into `LaboralStrategy.liquidar`**

Add the import at the top of `app/services/area_strategy.py`:

```python
from app.engine.labor.incapacidad import IncapacidadCalculator
```

Immediately after the `COTIZACION_*` block added in Task 8 (still inside the
`if obligacion.incluir_seguridad_social:` block), add:

```python
            for evento in obligacion.eventos_laborales:
                if evento.tipo.value == "SUSPENSION":
                    eventos.append(Event(
                        date=evento.fecha_fin,
                        payload={
                            "amount": Decimal("0.00"),
                            "label": (
                                f"Suspension ({evento.motivo_suspension.value}) "
                                f"{evento.fecha_inicio}-{evento.fecha_fin}: no causa ARL"
                            ),
                        },
                        event_type="SUSPENSION_INFORMATIVA",
                    ))
                else:
                    dias_incapacidad = (evento.fecha_fin - evento.fecha_inicio).days
                    desglose = IncapacidadCalculator.calcular(
                        tipo=evento.tipo, ibc_mensual=cotizaciones.ibc_mensual,
                        dias_incapacidad=dias_incapacidad,
                    )
                    for tramo in desglose.tramos:
                        es_empleador = tramo.pagador == "EMPLEADOR"
                        eventos.append(Event(
                            date=evento.fecha_fin,
                            payload={
                                "amount": tramo.monto if es_empleador else Decimal("0.00"),
                                "label": (
                                    f"Incapacidad {evento.tipo.value} dias {tramo.dias} - "
                                    f"{tramo.pagador} ({tramo.porcentaje:.2%}): ${tramo.monto}"
                                ),
                            },
                            event_type="INCAPACIDAD_EMPLEADOR" if es_empleador else "INCAPACIDAD_INFORMATIVA",
                        ))
```

Note this loop lives inside the `if obligacion.incluir_seguridad_social:` block because it depends on
`cotizaciones.ibc_mensual` — incapacidad/suspension events without seguridad social activated have no IBC
to compute against, which matches the opt-in design (a case that doesn't claim seguridad social doesn't
model incapacidad payer breakdowns either).

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/services/test_area_strategy.py -k TestLaboralStrategy -v`
Expected: PASS (all `TestLaboralStrategy` tests)

- [ ] **Step 5: Run the full suite for regressions**

Run: `pytest tests/ -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat: wire IncapacidadCalculator and suspension trace into LaboralStrategy.liquidar"
```

---

### Task 10: GUI — checkbox y nivel de riesgo ARL en `ObligacionFormDialog`

**Files:**
- Modify: `app/views/obligaciones.py`
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/views/test_obligaciones.py`:

```python
def test_guarda_obligacion_laboral_con_seguridad_social(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Liquidacion de contrato")
    dialog.campo_valor.setText("3000000.00")
    dialog.campo_fecha_origen.setDate(date(2020, 1, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 12, 31))
    dialog.check_incluir_seguridad_social.setChecked(True)
    dialog.combo_nivel_riesgo_arl.setCurrentIndex(0)  # "I"

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.incluir_seguridad_social is True
    assert guardada.nivel_riesgo_arl == "I"
    session.close()


def test_guarda_obligacion_laboral_sin_seguridad_social_por_defecto(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Liquidacion de contrato")
    dialog.campo_valor.setText("3000000.00")
    dialog.campo_fecha_origen.setDate(date(2020, 1, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 12, 31))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.incluir_seguridad_social is False
    assert guardada.nivel_riesgo_arl is None
    session.close()


def test_combo_nivel_riesgo_arl_visible_solo_si_checkbox_activo(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.combo_nivel_riesgo_arl.isVisible() is False
    dialog.check_incluir_seguridad_social.setChecked(True)
    assert dialog.combo_nivel_riesgo_arl.isVisible() is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/views/test_obligaciones.py -k seguridad_social -v`
Expected: FAIL with `AttributeError: 'ObligacionFormDialog' object has no attribute 'check_incluir_seguridad_social'`

- [ ] **Step 3: Add the widgets to `ObligacionFormDialog`**

In `app/views/obligaciones.py`, add `QCheckBox` and `QComboBox` are already imported. After
`self.check_pagada = QCheckBox("Prestaciones pagadas")` (line 90), add:

```python
        self.check_incluir_seguridad_social = QCheckBox("Incluir cotizaciones de seguridad social no pagadas")
        self.combo_nivel_riesgo_arl = QComboBox()
        for nivel in ("I", "II", "III", "IV", "V"):
            self.combo_nivel_riesgo_arl.addItem(f"Nivel {nivel}", userData=nivel)
```

After `self.layout_formulario.addRow("Fecha de pago real", self.campo_fecha_pago_total)` (line 121), add:

```python
        self.layout_formulario.addRow(self.check_incluir_seguridad_social)
        self.layout_formulario.addRow("Nivel de riesgo ARL", self.combo_nivel_riesgo_arl)
```

In the visibility block (after `self.check_pagada.setVisible(es_laboral)`, line 154), add:

```python
        self.check_incluir_seguridad_social.setVisible(es_laboral)
        self.combo_nivel_riesgo_arl.setVisible(False)
```

Connect the checkbox to a visibility toggle. Near the other `.connect(...)` calls (after
`self.check_pagada.stateChanged.connect(self._actualizar_campos_visibles)`, line 169), add:

```python
        self.check_incluir_seguridad_social.stateChanged.connect(self._actualizar_campos_visibles)
```

In `_actualizar_campos_visibles`, inside the `if self._area == "LABORAL":` branch (before the `return`),
add:

```python
            self.combo_nivel_riesgo_arl.setVisible(self.check_incluir_seguridad_social.isChecked())
```

- [ ] **Step 4: Wire the fields into `_guardar_laboral`**

In `_guardar_laboral`, before `session = session_module.get_session()`, add:

```python
        incluir_seguridad_social = self.check_incluir_seguridad_social.isChecked()
        nivel_riesgo_arl = self.combo_nivel_riesgo_arl.currentData() if incluir_seguridad_social else None
```

In the `Obligacion(...)` constructor call inside `_guardar_laboral`, add two new keyword arguments:

```python
            incluir_seguridad_social=incluir_seguridad_social,
            nivel_riesgo_arl=nivel_riesgo_arl,
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/views/test_obligaciones.py -v`
Expected: PASS (all tests in the file)

- [ ] **Step 6: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "feat: add seguridad social checkbox and ARL risk level to ObligacionFormDialog"
```

---

### Task 11: GUI — `EventoLaboralFormDialog` nuevo

**Files:**
- Create: `app/views/eventos_laborales.py`
- Test: `tests/views/test_eventos_laborales.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/views/test_eventos_laborales.py`:

```python
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.views.eventos_laborales import EventoLaboralFormDialog
from database.models import (
    AreaDerecho, Base, Expediente, MotivoSuspension, Obligacion, TipoEventoLaboral, TipoObligacion,
)


def _obligacion_laboral_de_prueba(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-020", demandante="Ana", demandado="Luis",
        area_derecho=AreaDerecho.LABORAL, fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.flush()
    obligacion = Obligacion(
        expediente_id=expediente.id, tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato", categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1), valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"), fecha_inicio=date(2020, 1, 1), fecha_fin=date(2020, 12, 31),
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()
    return obligacion_id


def test_guarda_evento_suspension(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # Suspension
    dialog.campo_fecha_inicio.setDate(date(2020, 3, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 3, 15))
    dialog.combo_motivo.setCurrentIndex(0)  # Huelga

    dialog.guardar()

    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    evento = obligacion.eventos_laborales[0]
    assert evento.tipo == TipoEventoLaboral.SUSPENSION
    assert evento.motivo_suspension == MotivoSuspension.HUELGA
    session.close()


def test_guarda_evento_incapacidad_comun_sin_motivo(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(1)  # Incapacidad comun
    dialog.campo_fecha_inicio.setDate(date(2020, 5, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 5, 4))

    dialog.guardar()

    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    evento = obligacion.eventos_laborales[0]
    assert evento.tipo == TipoEventoLaboral.INCAPACIDAD_COMUN
    assert evento.motivo_suspension is None
    session.close()


def test_combo_motivo_oculto_si_tipo_no_es_suspension(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.combo_motivo.isVisible() is True  # Suspension es el default (indice 0)
    dialog.combo_tipo.setCurrentIndex(2)  # Incapacidad laboral
    assert dialog.combo_motivo.isVisible() is False


def test_fecha_fin_anterior_o_igual_a_fecha_inicio_lanza_value_error(qtbot, monkeypatch):
    import pytest

    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_fecha_inicio.setDate(date(2020, 5, 10))
    dialog.campo_fecha_fin.setDate(date(2020, 5, 10))

    with pytest.raises(ValueError):
        dialog.guardar()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/views/test_eventos_laborales.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.views.eventos_laborales'`

- [ ] **Step 3: Implement `app/views/eventos_laborales.py`**

```python
from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QComboBox, QDateEdit, QDialog, QFormLayout, QMessageBox, QPushButton

import database.session as session_module
from database.models import EventoLaboral, MotivoSuspension, TipoEventoLaboral


class EventoLaboralFormDialog(QDialog):
    def __init__(self, obligacion_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar evento contractual")
        self._obligacion_id = obligacion_id

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("Suspension", userData=TipoEventoLaboral.SUSPENSION)
        self.combo_tipo.addItem("Incapacidad comun", userData=TipoEventoLaboral.INCAPACIDAD_COMUN)
        self.combo_tipo.addItem("Incapacidad laboral", userData=TipoEventoLaboral.INCAPACIDAD_LABORAL)

        self.campo_fecha_inicio = QDateEdit(QDate.currentDate())
        self.campo_fecha_inicio.setCalendarPopup(True)
        self.campo_fecha_fin = QDateEdit(QDate.currentDate())
        self.campo_fecha_fin.setCalendarPopup(True)

        self.combo_motivo = QComboBox()
        self.combo_motivo.addItem("Huelga", userData=MotivoSuspension.HUELGA)
        self.combo_motivo.addItem("Licencia no remunerada", userData=MotivoSuspension.LICENCIA_NO_REMUNERADA)
        self.combo_motivo.addItem("Disciplinaria", userData=MotivoSuspension.DISCIPLINARIA)

        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
        layout.addRow("Tipo de evento", self.combo_tipo)
        layout.addRow("Fecha de inicio", self.campo_fecha_inicio)
        layout.addRow("Fecha de fin", self.campo_fecha_fin)
        layout.addRow("Motivo de suspension", self.combo_motivo)
        layout.addRow(boton_guardar)
        self.setLayout(layout)

        self.combo_tipo.currentIndexChanged.connect(self._actualizar_visibilidad_motivo)
        self._actualizar_visibilidad_motivo()

    def _actualizar_visibilidad_motivo(self) -> None:
        self.combo_motivo.setVisible(self.combo_tipo.currentData() == TipoEventoLaboral.SUSPENSION)

    def guardar(self) -> int:
        qdate_inicio = self.campo_fecha_inicio.date()
        fecha_inicio = date(qdate_inicio.year(), qdate_inicio.month(), qdate_inicio.day())
        qdate_fin = self.campo_fecha_fin.date()
        fecha_fin = date(qdate_fin.year(), qdate_fin.month(), qdate_fin.day())

        if fecha_fin <= fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio del evento.")

        tipo = self.combo_tipo.currentData()
        motivo = self.combo_motivo.currentData() if tipo == TipoEventoLaboral.SUSPENSION else None

        session = session_module.get_session()
        evento = EventoLaboral(
            obligacion_id=self._obligacion_id,
            tipo=tipo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            motivo_suspension=motivo,
        )
        session.add(evento)
        session.commit()
        evento_id = evento.id
        session.close()
        return evento_id

    def _guardar_y_cerrar(self) -> None:
        try:
            self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos invalidos", str(error))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/views/test_eventos_laborales.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add app/views/eventos_laborales.py tests/views/test_eventos_laborales.py
git commit -m "feat: add EventoLaboralFormDialog for suspensiones e incapacidades"
```

---

### Task 12: GUI — grupo "Eventos contractuales" en `expediente_detalle.py`

**Files:**
- Modify: `app/views/expediente_detalle.py`
- Modify: `tests/views/test_expediente_detalle.py` (the file already exists — see its
  `_expediente_laboral_con_mora_fase1`/`_expediente_laboral_pagado_a_tiempo` helpers around line 400 for
  the established Laboral fixture style; add a new helper alongside them, don't redefine the existing
  ones)

- [ ] **Step 1: Write the failing test**

Append to the end of `tests/views/test_expediente_detalle.py`:

```python
def _expediente_laboral_sin_mora(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-070", demandante="Trabajador", demandado="Empleador SAS",
        area_derecho=AreaDerecho.LABORAL, fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.flush()
    obligacion = Obligacion(
        expediente_id=expediente.id, tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato", categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1), valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"), fecha_inicio=date(2020, 1, 1), fecha_fin=date(2020, 12, 31),
    )
    session.add(obligacion)
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_grupo_eventos_contractuales_visible_solo_para_area_laboral(qtbot, monkeypatch):
    expediente_id = _expediente_laboral_sin_mora(monkeypatch)

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.show()
    pagina.cargar_expediente(expediente_id)

    assert pagina.grupo_eventos_laborales.isVisible() is True


def test_grupo_eventos_contractuales_oculto_para_area_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)  # CIVIL_FAMILIA, ya existe en este archivo

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.show()
    pagina.cargar_expediente(expediente_id)

    assert pagina.grupo_eventos_laborales.isVisible() is False


def test_refrescar_eventos_laborales_lista_los_eventos_de_todas_las_obligaciones(qtbot, monkeypatch):
    from database.models import EventoLaboral, TipoEventoLaboral

    expediente_id = _expediente_laboral_sin_mora(monkeypatch)
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    session.add(EventoLaboral(
        obligacion_id=obligacion.id, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
        fecha_inicio=date(2020, 5, 1), fecha_fin=date(2020, 5, 4),
    ))
    session.commit()
    session.close()

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.cargar_expediente(expediente_id)

    assert pagina.tabla_eventos_laborales.rowCount() == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/views/test_expediente_detalle.py -v`
Expected: FAIL with `AttributeError: 'ExpedienteDetallePage' object has no attribute 'grupo_eventos_laborales'`

- [ ] **Step 3: Add the group box and table to `ExpedienteDetallePage`**

In `app/views/expediente_detalle.py`, add the import:

```python
from app.views.eventos_laborales import EventoLaboralFormDialog
```

After the `grupo_abonos` block (after line 54, before `boton_liquidar = QPushButton("Liquidar")`), add:

```python
        self.tabla_eventos_laborales = QTableWidget(0, 3)
        self.tabla_eventos_laborales.setHorizontalHeaderLabels(["Tipo", "Fecha inicio", "Fecha fin"])
        boton_agregar_evento_laboral = QPushButton("Agregar evento")
        boton_agregar_evento_laboral.clicked.connect(self._abrir_dialogo_evento_laboral)

        self.grupo_eventos_laborales = QGroupBox("Eventos contractuales")
        layout_eventos_laborales = QVBoxLayout()
        layout_eventos_laborales.addWidget(boton_agregar_evento_laboral)
        layout_eventos_laborales.addWidget(self.tabla_eventos_laborales)
        self.grupo_eventos_laborales.setLayout(layout_eventos_laborales)
```

Add it to the `columnas` layout (line ~72-74):

```python
        columnas = QHBoxLayout()
        columnas.addWidget(grupo_obligaciones)
        columnas.addWidget(grupo_abonos)
        columnas.addWidget(self.grupo_eventos_laborales)
```

In `cargar_expediente`, add a visibility check and refresh call:

```python
    def cargar_expediente(self, expediente_id: int) -> None:
        self._expediente_id = expediente_id
        session = session_module.get_session()
        expediente = session.get(Expediente, expediente_id)
        es_laboral = expediente.area_derecho == AreaDerecho.LABORAL
        session.close()

        self.grupo_eventos_laborales.setVisible(es_laboral)
        self._refrescar_obligaciones()
        self._refrescar_abonos()
        self._refrescar_historial()
        if es_laboral:
            self._refrescar_eventos_laborales()
```

Import `AreaDerecho` at the top (extend the existing `from database.models import Expediente` line):

```python
from database.models import AreaDerecho, Expediente
```

Add the refresh method (after `_refrescar_abonos`):

```python
    def _refrescar_eventos_laborales(self) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)
        eventos = [
            evento for obligacion in expediente.obligaciones for evento in obligacion.eventos_laborales
        ]

        self.tabla_eventos_laborales.setRowCount(len(eventos))
        for fila, evento in enumerate(eventos):
            self.tabla_eventos_laborales.setItem(fila, 0, QTableWidgetItem(evento.tipo.value))
            self.tabla_eventos_laborales.setItem(fila, 1, QTableWidgetItem(evento.fecha_inicio.isoformat()))
            self.tabla_eventos_laborales.setItem(fila, 2, QTableWidgetItem(evento.fecha_fin.isoformat()))
        session.close()
```

Add the dialog-opening method (after `_abrir_dialogo_abono`):

```python
    def _abrir_dialogo_evento_laboral(self) -> None:
        fila_seleccionada = self.tabla_obligaciones.currentRow()
        if fila_seleccionada < 0:
            QMessageBox.warning(
                self, "Seleccion requerida",
                "Selecciona una obligacion antes de agregar un evento contractual.",
            )
            return

        obligacion_id = self._obligacion_ids_por_fila[fila_seleccionada]
        dialogo = EventoLaboralFormDialog(obligacion_id=obligacion_id, parent=self)
        if dialogo.exec():
            self._refrescar_eventos_laborales()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/views/test_expediente_detalle.py -v`
Expected: PASS

- [ ] **Step 5: Run the full views test suite for regressions**

Run: `pytest tests/views/ -v`
Expected: PASS (existing tests for Civil/Familia and other areas don't touch
`grupo_eventos_laborales`/`tabla_eventos_laborales`, and the group is simply invisible for them)

- [ ] **Step 6: Commit**

```bash
git add app/views/expediente_detalle.py tests/views/test_expediente_detalle.py
git commit -m "feat: add eventos contractuales group to ExpedienteDetallePage for area Laboral"
```

---

### Task 13: Documentacion — README, GUIA_USUARIO, Pendientes.md

**Files:**
- Modify: `docs/GUIA_USUARIO.md`
- Modify: `README.md`
- Modify: `Pendientes.md`

No tests in this task — pure documentation updates, verified by manual review.

- [ ] **Step 1: Update `docs/GUIA_USUARIO.md` section 5.11**

Replace the paragraph at lines 426-428 (`**Qué NO calcula todavía esta área:** ...`) with:

```markdown
**Cotizaciones de seguridad social no pagadas (opcional):** si el caso incluye una reclamación de
aportes que el empleador nunca consignó, marca la casilla **"Incluir cotizaciones de seguridad social no
pagadas"** y elige el **Nivel de riesgo ARL** (I a V, según la actividad). El resultado agrega Pensión
(16%), Salud (12.5%), ARL (según el nivel elegido) y, si el salario base es de al menos 4 salarios
mínimos, el Fondo de Solidaridad Pensional (FSP). Si no marcas la casilla, el expediente se liquida
exactamente igual que antes (solo prestaciones sociales y, si aplica, la indemnización moratoria).

**Suspensiones e incapacidades (opcional, requiere la casilla anterior activada):** en el Detalle del
expediente, el grupo **"Eventos contractuales"** permite registrar suspensiones (huelga, licencia no
remunerada, disciplinaria) e incapacidades (común o laboral) del contrato. Una suspensión excluye el
aporte a ARL de esos días (Salud y Pensión se siguen cotizando). Una incapacidad muestra en la
liquidación el desglose completo de quién paga cada tramo de días (empleador, EPS o ARL, según las reglas
legales) — solo la porción a cargo del empleador se suma a la deuda del expediente.

**Qué NO calcula todavía esta área:** régimen pensional (IBL, densidad de semanas, tasa de reemplazo) —
ver [sección 8](#8-funciones-pendientes-o-en-desarrollo).
```

- [ ] **Step 2: Update `docs/GUIA_USUARIO.md` section 8**

Replace lines 709-713 (the two 🚧 bullets for seguridad social / incapacidades) with:

```markdown
- ✅ **Seguridad social, incapacidades y suspensiones en el área Laboral** — cotizaciones de pensión,
  salud, ARL y FSP, más incapacidades (común/laboral) y suspensiones contractuales, ya calculan como
  parte de la liquidación judicial de un contrato Laboral. Ver
  [sección 5.11](#511-agregar-una-obligación-laboral-y-liquidar-un-contrato-terminado)
  (`Pendientes.md`, Sprint 16).
```

- [ ] **Step 3: Update `docs/GUIA_USUARIO.md` línea 559 (tabla resumen de áreas)**

Replace:

```markdown
| Laboral | ✅ Sí — liquidación final (finiquito) de un contrato: cesantías, intereses a cesantías, prima, vacaciones, e indemnización moratoria bifásica del Art. 65 CST si hubo retardo en el pago. Ver [sección 5.11](#511-agregar-una-obligación-laboral-y-liquidar-un-contrato-terminado). Seguridad social no está incluida (ver sección 8). |
```

with:

```markdown
| Laboral | ✅ Sí — liquidación final (finiquito) de un contrato: cesantías, intereses a cesantías, prima, vacaciones, indemnización moratoria bifásica del Art. 65 CST, y opcionalmente cotizaciones de seguridad social (pensión, salud, ARL, FSP) más incapacidades y suspensiones contractuales. Ver [sección 5.11](#511-agregar-una-obligación-laboral-y-liquidar-un-contrato-terminado). |
```

- [ ] **Step 4: Update `README.md`**

Replace (lines 26-28):

```markdown
del Consejo Superior de la Judicatura) y **Laboral** (liquidación final —finiquito— de un contrato:
cesantías, intereses a cesantías, prima de junio y diciembre, vacaciones, e indemnización moratoria
bifásica del Art. 65 CST si hubo retardo en el pago). El resultado de cualquier liquidación se puede
```

with:

```markdown
del Consejo Superior de la Judicatura) y **Laboral** (liquidación final —finiquito— de un contrato:
cesantías, intereses a cesantías, prima de junio y diciembre, vacaciones, indemnización moratoria
bifásica del Art. 65 CST si hubo retardo en el pago y, opcionalmente, cotizaciones de seguridad social
—pensión, salud, ARL, FSP— más incapacidades y suspensiones contractuales). El resultado de cualquier
liquidación se puede
```

Replace (lines 41-43, the "En desarrollo" bullet — removes seguridad social from the pending list since
it now works):

```markdown
🚧 **En desarrollo:** seguridad social (cotizaciones a pensión, salud, ARL, fondo de solidaridad
pensional) en el área Laboral, anatocismo comercial condicionado (Art. 886 C.Co.) y varios módulos más
también están pendientes. El motor de prescripción y caducidad
```

with:

```markdown
🚧 **En desarrollo:** anatocismo comercial condicionado (Art. 886 C.Co.) y varios módulos más también
están pendientes. El motor de prescripción y caducidad
```

- [ ] **Step 5: Mark Sprint 16 as completed in `Pendientes.md`**

In `Pendientes.md`, change the heading at line 1109 from:

```markdown
## Sprint 16 — Seguridad social, incapacidades y suspensiones contractuales (Laboral)
```

to:

```markdown
## Sprint 16 — Seguridad social, incapacidades y suspensiones contractuales (Laboral) ✅ Completado
```

Immediately before the closing `---` that ends the Sprint 16 section (right after its existing
"Definición de Hecho" bullet list, in the same position as Sprint 14's "Cierre de implementación"), add
— matching that exact pattern:

```markdown
**Cierre de implementación (2026-07-24):** Completado — ver
`docs/superpowers/specs/2026-07-24-seguridad-social-laboral-design.md` y
`docs/superpowers/plans/2026-07-24-seguridad-social-laboral.md`. Se confirmó con el usuario que esto es
liquidación judicial de aportes/prestaciones dejados de pagar (no un módulo de nómina corriente),
cerrando la nota que el Sprint 3 había dejado abierta. Se agregó la tabla `eventos_laborales`
(polimórfica: suspensión/incapacidad común/incapacidad laboral), 2 columnas nuevas en `obligaciones`
(`incluir_seguridad_social`, `nivel_riesgo_arl`), los calculadores puros `SeguridadSocialCalculator` e
`IncapacidadCalculator` (`app/engine/labor/`), 12 parámetros nuevos en `CATALOGO_PARAMETROS` (pensión,
salud, ARL por nivel I-V, FSP por tramo de SMMLV), y el wiring correspondiente en
`LaboralStrategy.liquidar()`. Activación por checkbox opt-in: un expediente Laboral sin la casilla
marcada se liquida exactamente igual que antes del Sprint 16, sin regresión.

Incapacidades: el sistema muestra el desglose informativo completo de todos los pagadores (empleador,
EPS, ARL) pero solo la porción a cargo del empleador se suma a la deuda del expediente — reclamar lo que
le correspondía pagar a la EPS o a la ARL es un hecho distinto (ej. no afiliación), fuera de alcance.

Fuentes complementarias al PDF, ambas aprobadas explícitamente por el usuario antes de codificar: la
tabla completa de niveles de riesgo ARL II-IV (Decreto 1607/2002 — el PDF solo cita los extremos I y V) y
la escala progresiva completa del FSP por tramos de SMMLV (Ley 797/2003 art. 8 — el PDF solo describe
"desde 1% hasta 2%" sin tramos exactos).

`README.md` y `docs/GUIA_USUARIO.md` actualizados. Suite completa en verde.
```

- [ ] **Step 6: Commit**

```bash
git add docs/GUIA_USUARIO.md README.md Pendientes.md
git commit -m "docs: document seguridad social/incapacidades/suspensiones for area Laboral (Sprint 16)"
```

---

### Task 14: Suite completa y smoke test manual

**Files:** none (verification only)

- [ ] **Step 1: Run the entire test suite**

Run: `pytest tests/ -v`
Expected: PASS, zero failures, zero errors

- [ ] **Step 2: Manual smoke test**

Run the app (see the project's `run` skill or its normal launch command), then:
1. Create an expediente with área = Laboral.
2. Add an obligación: salario 3,000,000.00, contrato 2020-01-01 a 2020-12-31, marca "Incluir
   cotizaciones de seguridad social no pagadas", nivel de riesgo ARL = I.
3. In "Eventos contractuales", add a suspensión (huelga, 2020-03-01 a 2020-03-31) and an incapacidad
   común (2020-05-01 a 2020-05-04).
4. Click "Liquidar". Confirm the result includes: Cesantías, Intereses/Cesantías, Prima Junio, Prima
   Diciembre, Vacaciones, Cotización Pensión, Cotización Salud, Cotización ARL, a "Suspension..."
   informational line, and "Incapacidad..." lines (employer + informational EPS line).
5. Export to PDF/Word and confirm the informational lines render with their descriptive labels.

- [ ] **Step 3: Final commit if anything was adjusted during smoke test**

```bash
git add -A
git commit -m "fix: address issues found during Sprint 16 manual smoke test"
```

(Skip this step entirely if the smoke test needed no code changes.)
