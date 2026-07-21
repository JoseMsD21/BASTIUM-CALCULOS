# Parámetros legales versionados — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a non-programmer (a lawyer) edit legal rates/caps/terms and the historical indicator series (SMLMV, IPC, IBC/usura) from inside BASTIUM's GUI, without touching Python or redeploying, while preserving every currently-tested calculation result exactly.

**Architecture:** A new append-only `parametros_legales` table plus `app/services/parametro_service.py` (a closed code-catalog of valid keys, each with a resolution mode — `ABIERTO`/`ANUAL_EXACTO`/`TRAMO_CERRADO` — and `get_parametro(clave, fecha)`/`agregar_valor(...)`/`historial(...)`). A migration script seeds the table from the existing hardcoded Python constants (which are **not deleted** — they stay as the git-verified reference the migration reads from). Six calculation modules are re-wired, one at a time, to call `get_parametro` instead of touching their local constant. A new GUI screen (`app/views/configuracion.py`, currently empty) lists every parameter's current value and lets a lawyer add a new dated value.

**Tech Stack:** Python, SQLAlchemy 2.0 (declarative `Mapped`/`mapped_column`), SQLite, PySide6, pytest (`--import-mode=importlib`).

**Design doc:** `docs/superpowers/specs/2026-07-20-parametros-legales-versionados-design.md` (read the "Adenda de diseño" section before starting — it explains why three resolution modes exist and why the source constants are kept, not deleted).

---

### Task 1: `ParametroLegal` model

**Files:**
- Modify: `database/models.py`

- [ ] **Step 1: Add the model**

Add this class at the end of `database/models.py` (after `AuditLog`):

```python
class ParametroLegal(Base):
    __tablename__ = "parametros_legales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clave: Mapped[str] = mapped_column(String(100))
    valor: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    vigente_desde: Mapped[date] = mapped_column(Date)
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    usuario: Mapped[str] = mapped_column(String(200))
    motivo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime)
```

No relationships, no foreign keys — this table is intentionally standalone (see design doc, "no depende del motor de auditoría del Sprint 9"). `Numeric(24, 10)` is generous on purpose: this single `valor` column holds everything from SMLMV amounts (~1,750,905) to percentages (30) to compounding IPC indices — on SQLite, SQLAlchemy's `Numeric` type stores `Decimal` as text and parses it back, so no precision is lost regardless of the declared scale; it's informational here, not enforced.

- [ ] **Step 2: Verify the app still starts and creates the table**

Run: `python -c "from database.database import init_db; init_db(); from database.models import ParametroLegal; print(ParametroLegal.__tablename__)"`
Expected: prints `parametros_legales`, no errors. (This runs against the real `bastium.db` — harmless, `init_db()` only adds new tables, never alters existing ones.)

- [ ] **Step 3: Commit**

```bash
git add database/models.py
git commit -m "feat: add ParametroLegal model for versioned legal parameters"
```

---

### Task 2: `ParametroNoDisponibleError`

**Files:**
- Modify: `app/core/exceptions.py`

- [ ] **Step 1: Add the exception**

Add at the end of `app/core/exceptions.py`:

```python


class ParametroNoDisponibleError(Exception):
    """Se lanza cuando no hay un valor de un parametro legal versionado disponible
    para la fecha pedida (ver app/services/parametro_service.py)."""
```

- [ ] **Step 2: Commit**

```bash
git add app/core/exceptions.py
git commit -m "feat: add ParametroNoDisponibleError"
```

---

### Task 3: `parametro_service` — catalog and `get_parametro` (modo ABIERTO)

**Files:**
- Create: `app/services/parametro_service.py`
- Test: `tests/services/test_parametro_service.py`

- [ ] **Step 1: Write the failing test**

Create `tests/services/test_parametro_service.py`:

```python
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.exceptions import ParametroNoDisponibleError
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _db_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    return engine


def _insertar(clave, valor, vigente_desde, vigente_hasta=None):
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave=clave, valor=Decimal(valor), vigente_desde=vigente_desde, vigente_hasta=vigente_hasta,
        usuario="test", motivo=None, creado_en=datetime.now(),
    ))
    session.commit()
    session.close()


def test_get_parametro_modo_abierto_toma_la_fila_mas_reciente_antes_de_la_fecha():
    from app.services.parametro_service import get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))
    _insertar("USURA_MULTIPLICADOR", "2.0", date(2030, 1, 1))

    assert get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20)) == Decimal("1.5")
    assert get_parametro("USURA_MULTIPLICADOR", date(2031, 1, 1)) == Decimal("2.0")


def test_get_parametro_modo_abierto_extrapola_hacia_adelante_sin_tope():
    from app.services.parametro_service import get_parametro

    _insertar("CUOTA_LITIS_INDIVIDUAL_PCT", "30", date(2007, 1, 1))
    assert get_parametro("CUOTA_LITIS_INDIVIDUAL_PCT", date(2099, 1, 1)) == Decimal("30")


def test_get_parametro_sin_ninguna_fila_anterior_a_la_fecha_lanza_error():
    from app.services.parametro_service import get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))
    with pytest.raises(ParametroNoDisponibleError):
        get_parametro("USURA_MULTIPLICADOR", date(1990, 1, 1))


def test_get_parametro_clave_desconocida_lanza_value_error():
    from app.services.parametro_service import get_parametro

    with pytest.raises(ValueError):
        get_parametro("NO_EXISTE", date(2026, 1, 1))
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/services/test_parametro_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.parametro_service'`

- [ ] **Step 3: Create `app/services/parametro_service.py`**

```python
"""
Servicio de parametros legales versionados: valores/tasas/topes/plazos que
antes vivian como constantes Python sueltas (usura, cuota litis, prescripcion,
E.T. 635, tasa civil legal) o como series versionadas solo en codigo (SMLMV,
IPC, IBC/usura, ver historical_index.py) pasan a vivir en la tabla
parametros_legales, editable desde la GUI (app/views/configuracion.py) sin
tocar Python ni redesplegar.

Ver docs/superpowers/specs/2026-07-20-parametros-legales-versionados-design.md
para el diseno completo, en particular la Adenda de modos de resolucion.

Tabla append-only: nunca se edita ni se borra una fila existente. Una
correccion o un cambio de vigencia se hace agregando una fila nueva -- las
columnas usuario/motivo/creado_en de cada fila son, en conjunto, la bitacora
completa (no depende de AuditLog, que exige un expediente_id).
"""

from __future__ import annotations

import enum
from datetime import date
from decimal import Decimal
from typing import NamedTuple

import database.session as session_module
from app.core.exceptions import ParametroNoDisponibleError
from database.models import ParametroLegal


class ModoResolucion(enum.Enum):
    ABIERTO = "ABIERTO"
    ANUAL_EXACTO = "ANUAL_EXACTO"
    TRAMO_CERRADO = "TRAMO_CERRADO"


class InfoParametro(NamedTuple):
    descripcion: str
    categoria: str
    fuente_legal: str
    modo: ModoResolucion


CATALOGO_PARAMETROS: dict[str, InfoParametro] = {
    "USURA_MULTIPLICADOR": InfoParametro(
        "Multiplicador del tope de usura sobre el IBC", "Topes legales",
        "Ley 45/1990, art. 72", ModoResolucion.ABIERTO,
    ),
    "CUOTA_LITIS_INDIVIDUAL_PCT": InfoParametro(
        "Tope de cuota litis individual (% del beneficio obtenido)", "Topes legales",
        "Ley 1123/2007", ModoResolucion.ABIERTO,
    ),
    "HONORARIOS_TOTAL_PCT": InfoParametro(
        "Tope de honorarios fijos + cuota litis (% del beneficio obtenido)", "Topes legales",
        "Criterio jurisprudencial/etico", ModoResolucion.ABIERTO,
    ),
    "ET635_PUNTOS_DESCUENTO": InfoParametro(
        "Puntos que se restan a la usura vigente para el interes moratorio tributario",
        "Topes legales", "Estatuto Tributario, art. 635", ModoResolucion.ABIERTO,
    ),
    "CIVIL_ANNUAL_RATE": InfoParametro(
        "Tasa de interes civil legal anual", "Topes legales",
        "Art. 1617 Codigo Civil", ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_EJECUTIVA_MESES": InfoParametro(
        "Plazo de prescripcion de la accion ejecutiva (meses)", "Plazos de prescripcion y caducidad",
        "PDF paginas 16/19, 42, 43, 45", ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_ORDINARIA_MESES": InfoParametro(
        "Plazo de prescripcion de la accion ordinaria (meses)", "Plazos de prescripcion y caducidad",
        "Art. 2536 Codigo Civil", ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_HONORARIOS_MESES": InfoParametro(
        "Plazo de prescripcion de honorarios profesionales (meses)", "Plazos de prescripcion y caducidad",
        "PDF pagina 35", ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_CAMBIARIA_DIRECTA_MESES": InfoParametro(
        "Plazo de prescripcion cambiaria directa (meses)", "Plazos de prescripcion y caducidad",
        "Art. 789 C.Co.", ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES": InfoParametro(
        "Plazo de prescripcion cambiaria de regreso del tenedor (meses)",
        "Plazos de prescripcion y caducidad", "Art. 790 C.Co.", ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES": InfoParametro(
        "Plazo de prescripcion cambiaria entre obligados de regreso (meses)",
        "Plazos de prescripcion y caducidad", "Art. 791 C.Co.", ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_IMPUGNACION_INEFICACIA_SOCIETARIA_MESES": InfoParametro(
        "Plazo de caducidad de impugnacion de ineficacia societaria (meses)",
        "Plazos de prescripcion y caducidad", "PDF pagina 40", ModoResolucion.ABIERTO,
    ),
    "SMLMV": InfoParametro(
        "Salario Minimo Legal Mensual Vigente", "Indicadores historicos",
        "PDF paginas 55-57", ModoResolucion.ANUAL_EXACTO,
    ),
    "IPC_INDICE_ACUMULADO": InfoParametro(
        "Indice de Precios al Consumidor acumulado (cierre de ano, base 100 en 1966)",
        "Indicadores historicos", "PDF pagina 62", ModoResolucion.ANUAL_EXACTO,
    ),
    "IBC_CONSUMO_ORDINARIO": InfoParametro(
        "Interes Bancario Corriente, linea Consumo y Ordinario (% anual)",
        "Indicadores historicos", "PDF paginas 58-61 (SFC)", ModoResolucion.TRAMO_CERRADO,
    ),
    "USURA_CONSUMO_ORDINARIO": InfoParametro(
        "Tasa de usura, linea Consumo y Ordinario (% anual)",
        "Indicadores historicos", "PDF paginas 58-61 (SFC)", ModoResolucion.TRAMO_CERRADO,
    ),
}


def _validar_clave(clave: str) -> InfoParametro:
    info = CATALOGO_PARAMETROS.get(clave)
    if info is None:
        raise ValueError(f"'{clave}' no es una clave de parametro reconocida.")
    return info


def _resolver_fila(clave: str, fecha: date) -> ParametroLegal | None:
    info = _validar_clave(clave)
    session = session_module.get_session()
    try:
        query = session.query(ParametroLegal).filter(ParametroLegal.clave == clave)
        if info.modo == ModoResolucion.ANUAL_EXACTO:
            query = query.filter(ParametroLegal.vigente_desde == date(fecha.year, 1, 1))
        elif info.modo == ModoResolucion.TRAMO_CERRADO:
            query = query.filter(
                ParametroLegal.vigente_desde <= fecha,
                ParametroLegal.vigente_hasta.is_not(None),
                ParametroLegal.vigente_hasta >= fecha,
            )
        else:
            query = query.filter(ParametroLegal.vigente_desde <= fecha)
        return query.order_by(
            ParametroLegal.vigente_desde.desc(), ParametroLegal.creado_en.desc()
        ).first()
    finally:
        session.close()


def get_parametro(clave: str, fecha: date) -> Decimal:
    """Resuelve el valor de `clave` vigente en `fecha`, segun el modo_resolucion
    declarado en CATALOGO_PARAMETROS (ver Adenda de diseno de la spec)."""
    fila = _resolver_fila(clave, fecha)
    if fila is None:
        raise ParametroNoDisponibleError(
            f"No hay valor de '{clave}' disponible para la fecha {fecha}."
        )
    return fila.valor
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/services/test_parametro_service.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/services/parametro_service.py tests/services/test_parametro_service.py
git commit -m "feat: add parametro_service with catalog and ABIERTO resolution mode"
```

---

### Task 4: `get_parametro` — modos `ANUAL_EXACTO` y `TRAMO_CERRADO`

**Files:**
- Test: `tests/services/test_parametro_service.py` (append)

The implementation from Task 3 already handles all three modes (the `if/elif/else` in `_resolver_fila`) — this task is pure test coverage to lock in the other two modes before anything depends on them.

- [ ] **Step 1: Write the failing tests**

Append to `tests/services/test_parametro_service.py`:

```python
def test_get_parametro_modo_anual_exacto_requiere_el_mismo_anio():
    from app.services.parametro_service import get_parametro

    _insertar("SMLMV", "1750905.00", date(2026, 1, 1))
    _insertar("SMLMV", "1423500.00", date(2025, 1, 1))

    assert get_parametro("SMLMV", date(2026, 7, 20)) == Decimal("1750905.00")
    assert get_parametro("SMLMV", date(2025, 12, 31)) == Decimal("1423500.00")


def test_get_parametro_modo_anual_exacto_no_extrapola():
    from app.services.parametro_service import get_parametro

    _insertar("SMLMV", "1750905.00", date(2026, 1, 1))
    with pytest.raises(ParametroNoDisponibleError):
        get_parametro("SMLMV", date(2027, 1, 1))


def test_get_parametro_modo_tramo_cerrado_encuentra_el_tramo_correcto():
    from app.services.parametro_service import get_parametro

    _insertar("IBC_CONSUMO_ORDINARIO", "16.24", date(2026, 1, 1), vigente_hasta=date(2026, 1, 31))
    _insertar("IBC_CONSUMO_ORDINARIO", "16.82", date(2026, 2, 1), vigente_hasta=date(2026, 2, 28))

    assert get_parametro("IBC_CONSUMO_ORDINARIO", date(2026, 1, 15)) == Decimal("16.24")
    assert get_parametro("IBC_CONSUMO_ORDINARIO", date(2026, 2, 15)) == Decimal("16.82")


def test_get_parametro_modo_tramo_cerrado_no_extrapola_mas_alla_del_ultimo_tramo():
    from app.services.parametro_service import get_parametro

    _insertar("IBC_CONSUMO_ORDINARIO", "16.24", date(2026, 1, 1), vigente_hasta=date(2026, 1, 31))
    with pytest.raises(ParametroNoDisponibleError):
        get_parametro("IBC_CONSUMO_ORDINARIO", date(2026, 2, 1))
```

- [ ] **Step 2: Run to verify they pass already**

Run: `python -m pytest tests/services/test_parametro_service.py -v`
Expected: 8 passed (the resolution logic from Task 3 already covers both modes)

- [ ] **Step 3: Commit**

```bash
git add tests/services/test_parametro_service.py
git commit -m "test: lock in ANUAL_EXACTO and TRAMO_CERRADO resolution modes"
```

---

### Task 5: `agregar_valor`, `historial`, `valor_vigente_hoy`, `ultimo_anio_disponible`

**Files:**
- Modify: `app/services/parametro_service.py`
- Test: `tests/services/test_parametro_service.py` (append)

- [ ] **Step 1: Write the failing tests**

Append to `tests/services/test_parametro_service.py`:

```python
from datetime import datetime as _datetime  # noqa: E402  (kept near top-level imports style of this repo)


def test_agregar_valor_modo_abierto_no_admite_vigente_hasta():
    from app.services.parametro_service import agregar_valor

    with pytest.raises(ValueError):
        agregar_valor(
            "USURA_MULTIPLICADOR", Decimal("1.5"), date(2026, 1, 1), "abogado1",
            vigente_hasta=date(2026, 12, 31),
        )


def test_agregar_valor_modo_tramo_cerrado_exige_vigente_hasta():
    from app.services.parametro_service import agregar_valor

    with pytest.raises(ValueError):
        agregar_valor("IBC_CONSUMO_ORDINARIO", Decimal("16.24"), date(2026, 8, 1), "abogado1")


def test_agregar_valor_guarda_y_queda_disponible_para_get_parametro():
    from app.services.parametro_service import agregar_valor, get_parametro

    agregar_valor(
        "SMLMV", Decimal("1900000.00"), date(2027, 1, 1), "abogado1",
        motivo="Publicado por el Gobierno",
    )
    assert get_parametro("SMLMV", date(2027, 3, 1)) == Decimal("1900000.00")


def test_historial_ordena_del_mas_reciente_al_mas_antiguo():
    from app.services.parametro_service import agregar_valor, historial

    agregar_valor("SMLMV", Decimal("1423500.00"), date(2025, 1, 1), "abogado1")
    agregar_valor("SMLMV", Decimal("1750905.00"), date(2026, 1, 1), "abogado1")

    filas = historial("SMLMV")
    assert [f.vigente_desde for f in filas] == [date(2026, 1, 1), date(2025, 1, 1)]


def test_valor_vigente_hoy_retorna_none_sin_datos():
    from app.services.parametro_service import valor_vigente_hoy

    assert valor_vigente_hoy("SMLMV") is None


def test_valor_vigente_hoy_retorna_la_fila_resuelta_para_hoy():
    from app.services.parametro_service import agregar_valor, valor_vigente_hoy

    agregar_valor("CUOTA_LITIS_INDIVIDUAL_PCT", Decimal("30"), date(2007, 1, 1), "abogado1")
    fila = valor_vigente_hoy("CUOTA_LITIS_INDIVIDUAL_PCT")
    assert fila is not None
    assert fila.valor == Decimal("30")


def test_ultimo_anio_disponible_retorna_el_mayor_anio_cargado():
    from app.services.parametro_service import agregar_valor, ultimo_anio_disponible

    agregar_valor("IPC_INDICE_ACUMULADO", Decimal("100"), date(1967, 1, 1), "sistema")
    agregar_valor("IPC_INDICE_ACUMULADO", Decimal("500"), date(2025, 1, 1), "sistema")
    assert ultimo_anio_disponible("IPC_INDICE_ACUMULADO") == 2025


def test_ultimo_anio_disponible_rechaza_claves_que_no_son_anuales():
    from app.services.parametro_service import ultimo_anio_disponible

    with pytest.raises(ValueError):
        ultimo_anio_disponible("USURA_MULTIPLICADOR")


def test_ultimo_anio_disponible_sin_datos_lanza_parametro_no_disponible():
    from app.services.parametro_service import ultimo_anio_disponible

    with pytest.raises(ParametroNoDisponibleError):
        ultimo_anio_disponible("SMLMV")
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/services/test_parametro_service.py -v`
Expected: FAIL — `ImportError: cannot import name 'agregar_valor'` (and similar for the other three)

- [ ] **Step 3: Implement**

Append to `app/services/parametro_service.py` (after `get_parametro`):

```python


def agregar_valor(
    clave: str,
    valor: Decimal,
    vigente_desde: date,
    usuario: str,
    motivo: str | None = None,
    vigente_hasta: date | None = None,
) -> ParametroLegal:
    """Inserta una fila nueva (append-only: nunca modifica ni borra filas
    existentes). Usada por la GUI (app/views/configuracion.py)."""
    info = _validar_clave(clave)
    if info.modo == ModoResolucion.TRAMO_CERRADO and vigente_hasta is None:
        raise ValueError(f"'{clave}' requiere 'vigente_hasta' (modo TRAMO_CERRADO).")
    if info.modo != ModoResolucion.TRAMO_CERRADO and vigente_hasta is not None:
        raise ValueError(f"'{clave}' no admite 'vigente_hasta' (modo {info.modo.value}).")

    session = session_module.get_session()
    try:
        fila = ParametroLegal(
            clave=clave,
            valor=valor,
            vigente_desde=vigente_desde,
            vigente_hasta=vigente_hasta,
            usuario=usuario,
            motivo=motivo,
            creado_en=datetime.now(),
        )
        session.add(fila)
        session.commit()
        session.refresh(fila)
        return fila
    finally:
        session.close()


def historial(clave: str) -> list[ParametroLegal]:
    """Todas las filas de una clave, mas reciente primero -- alimenta la vista
    de historial de la GUI."""
    _validar_clave(clave)
    session = session_module.get_session()
    try:
        return (
            session.query(ParametroLegal)
            .filter(ParametroLegal.clave == clave)
            .order_by(ParametroLegal.vigente_desde.desc(), ParametroLegal.creado_en.desc())
            .all()
        )
    finally:
        session.close()


def valor_vigente_hoy(clave: str) -> ParametroLegal | None:
    """Fila resuelta para la fecha de hoy -- alimenta la tabla resumen de la GUI."""
    return _resolver_fila(clave, date.today())


def ultimo_anio_disponible(clave: str) -> int:
    """Maximo ano con datos cargados para una clave ANUAL_EXACTO. Usado por
    get_ipc_interpolado_for_date (historical_index.py) para su aproximacion ya
    documentada: fechas posteriores al ultimo ano disponible usan el indice de
    ese ultimo ano (Sprint 8, decision 3)."""
    info = _validar_clave(clave)
    if info.modo != ModoResolucion.ANUAL_EXACTO:
        raise ValueError(f"'{clave}' no es una serie anual (modo {info.modo.value}).")
    session = session_module.get_session()
    try:
        fila = (
            session.query(ParametroLegal)
            .filter(ParametroLegal.clave == clave)
            .order_by(ParametroLegal.vigente_desde.desc())
            .first()
        )
        if fila is None:
            raise ParametroNoDisponibleError(f"No hay ningun valor cargado para '{clave}'.")
        return fila.vigente_desde.year
    finally:
        session.close()
```

Also update the top import line, adding `datetime`:

```python
from datetime import date, datetime
```

(replacing the existing `from datetime import date`).

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/services/test_parametro_service.py -v`
Expected: 17 passed

- [ ] **Step 5: Commit**

```bash
git add app/services/parametro_service.py tests/services/test_parametro_service.py
git commit -m "feat: add agregar_valor, historial, valor_vigente_hoy, ultimo_anio_disponible"
```

---

### Task 6: Migration script `scripts/migrate_parametros_legales.py`

**Files:**
- Create: `scripts/migrate_parametros_legales.py`
- Test: `tests/scripts/test_migrate_parametros_legales.py`

This script is a **self-contained snapshot**: it imports its seed values from the modules that currently hold them (`usury_validator.TOPE_MULTIPLICADOR`, `HonorariosStrategy.TOPE_CUOTA_LITIS_INDIVIDUAL_PCT`/`TOPE_HONORARIOS_TOTAL_PCT`, `prescripcion.PLAZOS_PRESCRIPCION_MESES`/`PLAZOS_CADUCIDAD_MESES_CONOCIDOS`, `moratory_interest.PUNTOS_DESCUENTO_ET_635`, `legal_rates.LegalRates.CIVIL_ANNUAL_RATE`, and `historical_index._SMLMV_POR_ANIO`/`_IPC_INDICE_ACUMULADO`/`_TRAMOS_IBC_USURA`). None of those constants get deleted in this plan (see Tasks 8-13) — they remain the git-verified reference this script reads from, so the import never breaks.

- [ ] **Step 1: Write the failing test**

Create `tests/scripts/test_migrate_parametros_legales.py`:

```python
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.database as database_module
import database.session as session_module
from database.models import ParametroLegal


@pytest.fixture(autouse=True)
def _db_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    return engine


def test_migrar_siembra_las_16_claves_del_catalogo():
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
    }


def test_migrar_smlmv_2026_coincide_con_el_valor_conocido():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    fila = session.query(ParametroLegal).filter(
        ParametroLegal.clave == "SMLMV", ParametroLegal.vigente_desde == date(2026, 1, 1)
    ).one()
    session.close()
    assert fila.valor == Decimal("1750905.00")


def test_migrar_ibc_usura_primer_tramo_1997_coincide_con_inicio_y_fin():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    fila = session.query(ParametroLegal).filter(
        ParametroLegal.clave == "IBC_CONSUMO_ORDINARIO", ParametroLegal.vigente_desde == date(1997, 7, 1)
    ).one()
    session.close()
    assert fila.valor == Decimal("36.50")
    assert fila.vigente_hasta == date(1997, 8, 31)


def test_migrar_usura_multiplicador_coincide_con_la_constante_actual():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    fila = session.query(ParametroLegal).filter(ParametroLegal.clave == "USURA_MULTIPLICADOR").one()
    session.close()
    assert fila.valor == Decimal("1.5")


def test_migrar_es_idempotente():
    from scripts.migrate_parametros_legales import migrar

    primera = migrar()
    segunda = migrar()
    assert primera == 16
    assert segunda == 0
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/scripts/test_migrate_parametros_legales.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.migrate_parametros_legales'`

- [ ] **Step 3: Create `scripts/migrate_parametros_legales.py`**

```python
"""Migracion de datos (no de esquema): siembra la tabla parametros_legales
(creada automaticamente por init_db(), ver database/database.py) con los
valores hoy hardcodeados en distintos motores, para que el sprint de
parametros legales versionados no cambie ningun resultado de calculo el dia
que se despliegue.

Los valores se leen directamente de las constantes Python existentes -- nunca
retranscritos a mano -- porque esas constantes NO se borran al re-cablear los
motores que las usan (ver design spec, seccion "Motores a re-cablear"): siguen
siendo la transcripcion congelada y verificada contra el PDF fuente, y esta
migracion es la unica lectora que las necesita despues del re-cableado.

Idempotente: si una clave ya tiene filas, no la vuelve a sembrar (mismo patron
que scripts/migrate_aplica_indexacion_ipc.py, Sprint 8)."""

from datetime import date, datetime
from decimal import Decimal

from database.database import init_db
from database.models import ParametroLegal
from database.session import get_session

from app.engine.indexation.historical_index import (
    _IPC_INDICE_ACUMULADO,
    _SMLMV_POR_ANIO,
    _TRAMOS_IBC_USURA,
)
from app.engine.interest.legal_rates import LegalRates
from app.engine.interest.usury_validator import TOPE_MULTIPLICADOR
from app.engine.tax.moratory_interest import PUNTOS_DESCUENTO_ET_635
from app.engine.temporal.prescripcion import (
    PLAZOS_CADUCIDAD_MESES_CONOCIDOS,
    PLAZOS_PRESCRIPCION_MESES,
    TipoAccion,
)
from app.services.area_strategy import HonorariosStrategy

USUARIO_MIGRACION = "sistema"
MOTIVO_MIGRACION = (
    "Dato migrado automaticamente al implementar parametros legales versionados."
)
ANCLA_SIN_FECHA_NORMA = date(1900, 1, 1)

_CLAVE_POR_TIPO_ACCION = {
    TipoAccion.EJECUTIVA: "PRESCRIPCION_EJECUTIVA_MESES",
    TipoAccion.ORDINARIA: "PRESCRIPCION_ORDINARIA_MESES",
    TipoAccion.HONORARIOS_PROFESIONALES: "PRESCRIPCION_HONORARIOS_MESES",
    TipoAccion.CAMBIARIA_DIRECTA: "PRESCRIPCION_CAMBIARIA_DIRECTA_MESES",
    TipoAccion.CAMBIARIA_REGRESO_TENEDOR: "PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES",
    TipoAccion.CAMBIARIA_REGRESO_ENTRE_OBLIGADOS: "PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES",
}


def _fila(clave: str, valor: Decimal, vigente_desde: date, vigente_hasta: date | None = None) -> ParametroLegal:
    return ParametroLegal(
        clave=clave, valor=valor, vigente_desde=vigente_desde, vigente_hasta=vigente_hasta,
        usuario=USUARIO_MIGRACION, motivo=MOTIVO_MIGRACION, creado_en=datetime.now(),
    )


def _clave_ya_sembrada(session, clave: str) -> bool:
    return session.query(ParametroLegal).filter(ParametroLegal.clave == clave).first() is not None


def migrar() -> int:
    """Siembra parametros_legales. Retorna cuantas claves se sembraron (0 si
    ya estaban todas cargadas)."""
    init_db()
    session = get_session()
    sembradas = 0
    try:
        valores_unicos = [
            ("USURA_MULTIPLICADOR", TOPE_MULTIPLICADOR, ANCLA_SIN_FECHA_NORMA),
            ("CUOTA_LITIS_INDIVIDUAL_PCT", HonorariosStrategy.TOPE_CUOTA_LITIS_INDIVIDUAL_PCT, date(2007, 1, 1)),
            ("HONORARIOS_TOTAL_PCT", HonorariosStrategy.TOPE_HONORARIOS_TOTAL_PCT, ANCLA_SIN_FECHA_NORMA),
            ("ET635_PUNTOS_DESCUENTO", PUNTOS_DESCUENTO_ET_635, ANCLA_SIN_FECHA_NORMA),
            ("CIVIL_ANNUAL_RATE", LegalRates.CIVIL_ANNUAL_RATE, ANCLA_SIN_FECHA_NORMA),
        ]
        for clave, valor, vigente_desde in valores_unicos:
            if _clave_ya_sembrada(session, clave):
                continue
            session.add(_fila(clave, valor, vigente_desde))
            sembradas += 1

        for tipo_accion, clave in _CLAVE_POR_TIPO_ACCION.items():
            if _clave_ya_sembrada(session, clave):
                continue
            session.add(_fila(clave, Decimal(PLAZOS_PRESCRIPCION_MESES[tipo_accion]), ANCLA_SIN_FECHA_NORMA))
            sembradas += 1

        for tipo_proceso, meses in PLAZOS_CADUCIDAD_MESES_CONOCIDOS.items():
            clave = f"CADUCIDAD_{tipo_proceso}_MESES"
            if _clave_ya_sembrada(session, clave):
                continue
            session.add(_fila(clave, Decimal(meses), ANCLA_SIN_FECHA_NORMA))
            sembradas += 1

        if not _clave_ya_sembrada(session, "SMLMV"):
            for anio, valor in _SMLMV_POR_ANIO.items():
                session.add(_fila("SMLMV", valor, date(anio, 1, 1)))
            sembradas += 1

        if not _clave_ya_sembrada(session, "IPC_INDICE_ACUMULADO"):
            for anio, valor in _IPC_INDICE_ACUMULADO.items():
                session.add(_fila("IPC_INDICE_ACUMULADO", valor, date(anio, 1, 1)))
            sembradas += 1

        if not _clave_ya_sembrada(session, "IBC_CONSUMO_ORDINARIO"):
            for tramo in _TRAMOS_IBC_USURA:
                session.add(_fila("IBC_CONSUMO_ORDINARIO", tramo.ibc_anual, tramo.inicio, tramo.fin))
            sembradas += 1

        if not _clave_ya_sembrada(session, "USURA_CONSUMO_ORDINARIO"):
            for tramo in _TRAMOS_IBC_USURA:
                session.add(_fila("USURA_CONSUMO_ORDINARIO", tramo.usura_anual, tramo.inicio, tramo.fin))
            sembradas += 1

        session.commit()
        return sembradas
    finally:
        session.close()


if __name__ == "__main__":
    n = migrar()
    if n:
        print(f"Se sembraron {n} claves nuevas en parametros_legales.")
    else:
        print("parametros_legales ya estaba sembrada, no se hizo nada.")
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/scripts/test_migrate_parametros_legales.py -v`
Expected: 5 passed

- [ ] **Step 5: Run the script against the real `bastium.db`**

Run: `python scripts/migrate_parametros_legales.py`
Expected: `Se sembraron 16 claves nuevas en parametros_legales.` (or `... ya estaba sembrada ...` if run twice)

- [ ] **Step 6: Commit**

```bash
git add scripts/migrate_parametros_legales.py tests/scripts/test_migrate_parametros_legales.py
git commit -m "feat: add migration script seeding parametros_legales from existing constants"
```

---

### Task 7: Re-wire `usury_validator.py`

**Files:**
- Modify: `app/engine/interest/usury_validator.py`
- Modify: `app/services/area_strategy.py:215-216`
- Test: `tests/engine/test_usury_validator.py`

- [ ] **Step 1: Write the failing test**

Replace the content of `tests/engine/test_usury_validator.py` with (adds a `fecha` param and a DB fixture seeding the parameter it needs):

```python
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.exceptions import TasaUsurariaError
from app.engine.interest.usury_validator import validar_tasa_usura
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _db_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="USURA_MULTIPLICADOR", valor=Decimal("1.5"), vigente_desde=date(1997, 7, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
    ))
    session.commit()
    session.close()


def test_tasa_por_debajo_del_tope_no_lanza_error():
    validar_tasa_usura(Decimal("20.00"), Decimal("20.00"), "remuneratoria", date(2026, 1, 1))


def test_tasa_exactamente_en_el_tope_no_lanza_error():
    validar_tasa_usura(Decimal("30.00"), Decimal("20.00"), "moratoria", date(2026, 1, 1))


def test_tasa_por_encima_del_tope_lanza_tasa_usuraria_error():
    with pytest.raises(TasaUsurariaError):
        validar_tasa_usura(Decimal("30.01"), Decimal("20.00"), "moratoria", date(2026, 1, 1))


def test_mensaje_de_error_nombra_la_etiqueta_y_el_tope():
    with pytest.raises(TasaUsurariaError, match="moratoria"):
        validar_tasa_usura(Decimal("35.00"), Decimal("20.00"), "moratoria", date(2026, 1, 1))
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/engine/test_usury_validator.py -v`
Expected: FAIL — `TypeError: validar_tasa_usura() missing 1 required positional argument: 'fecha'`

- [ ] **Step 3: Re-wire `validar_tasa_usura`**

Replace the content of `app/engine/interest/usury_validator.py`:

```python
from datetime import date
from decimal import Decimal

from app.core.exceptions import TasaUsurariaError
from app.services.parametro_service import get_parametro

TOPE_MULTIPLICADOR = Decimal("1.5")
# NOTA: constante conservada como referencia congelada (Ley 45/1990, art. 72) y
# como fuente de siembra de scripts/migrate_parametros_legales.py -- ya no la
# lee validar_tasa_usura, que consulta el valor vigente por fecha via
# parametro_service (clave USURA_MULTIPLICADOR).


def validar_tasa_usura(tasa_pactada: Decimal, ibc_vigente: Decimal, etiqueta: str, fecha: date) -> None:
    """Lanza TasaUsurariaError si tasa_pactada supera el multiplicador de usura
    vigente en `fecha` (parametro USURA_MULTIPLICADOR, Ley 45/1990 art. 72) x
    ibc_vigente."""
    multiplicador = get_parametro("USURA_MULTIPLICADOR", fecha)
    tope = ibc_vigente * multiplicador
    if tasa_pactada > tope:
        exceso = tasa_pactada - tope
        raise TasaUsurariaError(
            f"La tasa {etiqueta} pactada ({tasa_pactada}%) supera el tope de usura "
            f"({multiplicador} x IBC = {tope}%) por {exceso} puntos porcentuales."
        )
```

- [ ] **Step 4: Update the one caller in `area_strategy.py`**

In `app/services/area_strategy.py`, replace lines 215-216:

```python
        validar_tasa_usura(obligacion.tasa_efectiva_anual, obligacion.ibc_vigente_anual, "remuneratoria")
        validar_tasa_usura(obligacion.tasa_moratoria_anual, obligacion.ibc_vigente_anual, "moratoria")
```

with:

```python
        validar_tasa_usura(
            obligacion.tasa_efectiva_anual, obligacion.ibc_vigente_anual, "remuneratoria",
            obligacion.fecha_origen,
        )
        validar_tasa_usura(
            obligacion.tasa_moratoria_anual, obligacion.ibc_vigente_anual, "moratoria",
            obligacion.fecha_origen,
        )
```

- [ ] **Step 5: Run to verify it passes**

Run: `python -m pytest tests/engine/test_usury_validator.py tests/services/test_area_strategy.py -v`
Expected: all passed (the `_db_en_memoria` fixture in `test_area_strategy.py`'s comercial tests must also seed `USURA_MULTIPLICADOR` — if any comercial test fails with `ParametroNoDisponibleError`, add the same three-line `ParametroLegal` insert used in Step 1 to that test file's fixture/setup before the failing test's obligations are liquidated)

- [ ] **Step 6: Commit**

```bash
git add app/engine/interest/usury_validator.py app/services/area_strategy.py tests/engine/test_usury_validator.py tests/services/test_area_strategy.py
git commit -m "refactor: usury_validator reads USURA_MULTIPLICADOR from parametro_service"
```

---

### Task 8: Re-wire `HonorariosStrategy` cuota litis caps

**Files:**
- Modify: `app/services/area_strategy.py:493-494, 542, 551` (the `TOPE_*` class attributes and their two usages inside `_validar_obligacion_honorarios`)
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Confirm the current Honorarios tests pass before touching anything**

Run: `python -m pytest tests/services/test_area_strategy.py -k Honorarios -v`
Expected: all passed (baseline before the change)

- [ ] **Step 2: Add a DB-seeding fixture for the two Honorarios claves**

In `tests/services/test_area_strategy.py`, add (near the top, alongside existing imports/fixtures — follow whatever DB fixture pattern the file already uses for other seeded-parameter tests; if none exists yet, add):

```python
from datetime import datetime as _dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _parametros_honorarios_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="CUOTA_LITIS_INDIVIDUAL_PCT", valor=Decimal("30"), vigente_desde=date(2007, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.add(ParametroLegal(
        clave="HONORARIOS_TOTAL_PCT", valor=Decimal("50"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.commit()
    session.close()
```

(`Decimal` and `date` are already imported at the top of this test file per the existing test suite; do not re-import if already present.)

- [ ] **Step 3: Run to verify the existing tests still pass with the fixture in place but before the source change**

Run: `python -m pytest tests/services/test_area_strategy.py -v`
Expected: all still passed (the fixture doesn't change behavior yet, `HonorariosStrategy` still reads its own class attributes)

- [ ] **Step 4: Re-wire `HonorariosStrategy`**

In `app/services/area_strategy.py`, remove these two lines (493-494):

```python
    TOPE_CUOTA_LITIS_INDIVIDUAL_PCT = Decimal("30")
    TOPE_HONORARIOS_TOTAL_PCT = Decimal("50")
```

Add this import near the top of the file (alongside the other `app.engine`/`app.services` imports):

```python
from app.services.parametro_service import get_parametro
```

Replace the two usages inside `_validar_obligacion_honorarios`:

```python
        tope_individual = obligacion.beneficio_obtenido * self.TOPE_CUOTA_LITIS_INDIVIDUAL_PCT / Decimal("100")
```

with:

```python
        tope_individual_pct = get_parametro("CUOTA_LITIS_INDIVIDUAL_PCT", obligacion.fecha_origen)
        tope_individual = obligacion.beneficio_obtenido * tope_individual_pct / Decimal("100")
```

and:

```python
        tope_total = obligacion.beneficio_obtenido * self.TOPE_HONORARIOS_TOTAL_PCT / Decimal("100")
```

with:

```python
        tope_total_pct = get_parametro("HONORARIOS_TOTAL_PCT", obligacion.fecha_origen)
        tope_total = obligacion.beneficio_obtenido * tope_total_pct / Decimal("100")
```

Note: `usury_validator.py` keeps its own `TOPE_MULTIPLICADOR` module constant as a frozen reference (Task 7). `HonorariosStrategy`'s two `TOPE_*` values are different — they lived only as class attributes with no separate "reference module" role, so they are removed outright here; the migration script (Task 6) already captured their values by reading `HonorariosStrategy.TOPE_CUOTA_LITIS_INDIVIDUAL_PCT`/`TOPE_HONORARIOS_TOTAL_PCT` **before** this task ran (Task 6 comes first in this plan) — do not reorder these two tasks.

- [ ] **Step 5: Run to verify it passes**

Run: `python -m pytest tests/services/test_area_strategy.py -v`
Expected: all passed, same count as Step 1's baseline

- [ ] **Step 6: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "refactor: HonorariosStrategy reads cuota litis caps from parametro_service"
```

---

### Task 9: Re-wire `prescripcion.py`

**Files:**
- Modify: `app/engine/temporal/prescripcion.py`
- Test: `tests/temporal/test_prescripcion.py`

- [ ] **Step 1: Confirm baseline**

Run: `python -m pytest tests/temporal/test_prescripcion.py -v`
Expected: all passed (note the count)

- [ ] **Step 2: Add a DB-seeding autouse fixture to the test file**

Add near the top of `tests/temporal/test_prescripcion.py` (adjust existing imports if `Decimal`/`date`/etc. are already present):

```python
from datetime import datetime as _dt
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import Base, ParametroLegal

_PLAZOS_MESES = {
    "PRESCRIPCION_EJECUTIVA_MESES": 60,
    "PRESCRIPCION_ORDINARIA_MESES": 120,
    "PRESCRIPCION_HONORARIOS_MESES": 36,
    "PRESCRIPCION_CAMBIARIA_DIRECTA_MESES": 36,
    "PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES": 12,
    "PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES": 6,
    "CADUCIDAD_IMPUGNACION_INEFICACIA_SOCIETARIA_MESES": 60,
}


@pytest.fixture(autouse=True)
def _parametros_prescripcion_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    for clave, meses in _PLAZOS_MESES.items():
        session.add(ParametroLegal(
            clave=clave, valor=Decimal(meses), vigente_desde=date(1900, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    session.commit()
    session.close()
```

- [ ] **Step 3: Run — should still pass (fixture only, no source change yet)**

Run: `python -m pytest tests/temporal/test_prescripcion.py -v`
Expected: same count as Step 1

- [ ] **Step 4: Re-wire `prescripcion.py`**

In `app/engine/temporal/prescripcion.py`, add the import:

```python
from app.services.parametro_service import get_parametro
```

Add a mapping right after the `PLAZOS_PRESCRIPCION_MESES` dict (keep that dict — it stays as the frozen reference, see Task 6):

```python
_CLAVE_POR_TIPO_ACCION = {
    TipoAccion.EJECUTIVA: "PRESCRIPCION_EJECUTIVA_MESES",
    TipoAccion.ORDINARIA: "PRESCRIPCION_ORDINARIA_MESES",
    TipoAccion.HONORARIOS_PROFESIONALES: "PRESCRIPCION_HONORARIOS_MESES",
    TipoAccion.CAMBIARIA_DIRECTA: "PRESCRIPCION_CAMBIARIA_DIRECTA_MESES",
    TipoAccion.CAMBIARIA_REGRESO_TENEDOR: "PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES",
    TipoAccion.CAMBIARIA_REGRESO_ENTRE_OBLIGADOS: "PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES",
}
```

Replace:

```python
def calcular_prescripcion(fecha_exigibilidad: date, tipo_accion: TipoAccion) -> date:
    meses = PLAZOS_PRESCRIPCION_MESES[tipo_accion]
    return CalendarUtils.vencimiento_calendario(fecha_exigibilidad, meses)
```

with:

```python
def calcular_prescripcion(fecha_exigibilidad: date, tipo_accion: TipoAccion) -> date:
    meses = int(get_parametro(_CLAVE_POR_TIPO_ACCION[tipo_accion], fecha_exigibilidad))
    return CalendarUtils.vencimiento_calendario(fecha_exigibilidad, meses)
```

Add, right after the `PLAZOS_CADUCIDAD_MESES_CONOCIDOS` dict (keep that dict too — same reasoning):

```python
_TIPOS_CADUCIDAD_CONOCIDOS = set(PLAZOS_CADUCIDAD_MESES_CONOCIDOS)
```

Replace the body of `calcular_caducidad`:

```python
def calcular_caducidad(
    fecha_hecho: date,
    tipo_proceso: str,
    plazo_meses_manual: Optional[int] = None,
) -> date:
    # El catalogo conocido tiene prioridad sobre plazo_meses_manual por
    # diseno: si tipo_proceso ya esta confirmado, el valor manual se ignora.
    if tipo_proceso in PLAZOS_CADUCIDAD_MESES_CONOCIDOS:
        meses = PLAZOS_CADUCIDAD_MESES_CONOCIDOS[tipo_proceso]
    elif plazo_meses_manual is not None:
        meses = plazo_meses_manual
    else:
        raise ValueError(
            f"No hay plazo de caducidad conocido para '{tipo_proceso}'; "
            "debe indicarse 'plazo_meses_manual' explicitamente."
        )
    return CalendarUtils.vencimiento_calendario(fecha_hecho, meses)
```

with:

```python
def calcular_caducidad(
    fecha_hecho: date,
    tipo_proceso: str,
    plazo_meses_manual: Optional[int] = None,
) -> date:
    # El catalogo conocido tiene prioridad sobre plazo_meses_manual por
    # diseno: si tipo_proceso ya esta confirmado, el valor manual se ignora.
    if tipo_proceso in _TIPOS_CADUCIDAD_CONOCIDOS:
        meses = int(get_parametro(f"CADUCIDAD_{tipo_proceso}_MESES", fecha_hecho))
    elif plazo_meses_manual is not None:
        meses = plazo_meses_manual
    else:
        raise ValueError(
            f"No hay plazo de caducidad conocido para '{tipo_proceso}'; "
            "debe indicarse 'plazo_meses_manual' explicitamente."
        )
    return CalendarUtils.vencimiento_calendario(fecha_hecho, meses)
```

- [ ] **Step 5: Run to verify it passes**

Run: `python -m pytest tests/temporal/test_prescripcion.py -v`
Expected: same count as Step 1, all passed

- [ ] **Step 6: Commit**

```bash
git add app/engine/temporal/prescripcion.py tests/temporal/test_prescripcion.py
git commit -m "refactor: prescripcion.py reads plazos from parametro_service"
```

---

### Task 10: Re-wire `moratory_interest.py`

**Files:**
- Modify: `app/engine/tax/moratory_interest.py`
- Test: `tests/engine/tax/test_moratory_interest.py`

- [ ] **Step 1: Confirm baseline**

Run: `python -m pytest tests/engine/tax/test_moratory_interest.py -v`
Expected: all passed (note the count)

- [ ] **Step 2: Add a DB-seeding autouse fixture**

Add near the top of `tests/engine/tax/test_moratory_interest.py`:

```python
from datetime import datetime as _dt

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _parametro_et635_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="ET635_PUNTOS_DESCUENTO", valor=Decimal("2"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.commit()
    session.close()
```

(`Decimal` and `date` should already be imported at the top of this test file; do not duplicate if present.)

- [ ] **Step 3: Run — should still pass**

Run: `python -m pytest tests/engine/tax/test_moratory_interest.py -v`
Expected: same count as Step 1

- [ ] **Step 4: Re-wire**

In `app/engine/tax/moratory_interest.py`, add the import:

```python
from app.services.parametro_service import get_parametro
```

Replace this line inside `construir_rate_provider_moratorio_tributario`:

```python
        tasa_anual_tributaria = tramo.usura_anual - PUNTOS_DESCUENTO_ET_635
```

with:

```python
        puntos_descuento = get_parametro("ET635_PUNTOS_DESCUENTO", inicio_segmento)
        tasa_anual_tributaria = tramo.usura_anual - puntos_descuento
```

(`PUNTOS_DESCUENTO_ET_635` stays defined at module level — frozen reference used by Task 6's migration script.)

- [ ] **Step 5: Run to verify it passes**

Run: `python -m pytest tests/engine/tax/test_moratory_interest.py -v`
Expected: same count as Step 1, all passed

- [ ] **Step 6: Commit**

```bash
git add app/engine/tax/moratory_interest.py tests/engine/tax/test_moratory_interest.py
git commit -m "refactor: moratory_interest.py reads ET635 discount from parametro_service"
```

---

### Task 11: Re-wire `legal_rates.py`

**Files:**
- Modify: `app/engine/interest/legal_rates.py`
- Test: `tests/engine/test_legal_rates.py` (new — this module currently has no dedicated test file, confirmed by grep: it has zero callers today)

- [ ] **Step 1: Write the failing test**

Create `tests/engine/test_legal_rates.py`:

```python
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.engine.interest.legal_rates import LegalRates
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _db_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="CIVIL_ANNUAL_RATE", valor=Decimal("0.06"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
    ))
    session.commit()
    session.close()


def test_get_civil_daily_rate_365_dias():
    tasa = LegalRates.get_civil_daily_rate(date(2026, 1, 1))
    assert tasa == Decimal("0.06") / Decimal("365")


def test_get_civil_daily_rate_360_dias():
    tasa = LegalRates.get_civil_daily_rate(date(2026, 1, 1), use_360_days=True)
    assert tasa == Decimal("0.06") / Decimal("360")
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/engine/test_legal_rates.py -v`
Expected: FAIL — `TypeError: get_civil_daily_rate() missing 1 required positional argument: 'fecha'`

- [ ] **Step 3: Re-wire**

Replace the content of `app/engine/interest/legal_rates.py`:

```python
from datetime import date
from decimal import Decimal

from app.services.parametro_service import get_parametro


class LegalRates:
    """
    Catalogo centralizado de tasas por ministerio de la ley.
    El motor consulta aqui, nunca al usuario.
    """
    # Articulo 1617 Codigo Civil: 6% anual -- constante conservada como
    # referencia congelada y fuente de siembra de
    # scripts/migrate_parametros_legales.py; get_civil_daily_rate ya no la lee
    # directamente, consulta parametro_service (clave CIVIL_ANNUAL_RATE).
    CIVIL_ANNUAL_RATE = Decimal("0.06")

    @staticmethod
    def get_civil_daily_rate(fecha: date, use_360_days: bool = False) -> Decimal:
        """
        Calcula la tasa diaria simple a partir de la tasa civil legal vigente
        en `fecha`. Por defecto en civil se usa el año calendario (365/366).
        """
        tasa_anual = get_parametro("CIVIL_ANNUAL_RATE", fecha)
        days_in_year = Decimal("360") if use_360_days else Decimal("365")
        return tasa_anual / days_in_year
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/engine/test_legal_rates.py -v`
Expected: 2 passed

- [ ] **Step 5: Confirm nothing else in the codebase calls the old zero-arg signature**

Run: `python -m pytest -v` (full suite)
Expected: no new failures anywhere (this function had zero callers before this change, confirmed by grep in the design doc — this run is a sanity check, not expected to surface anything)

- [ ] **Step 6: Commit**

```bash
git add app/engine/interest/legal_rates.py tests/engine/test_legal_rates.py
git commit -m "refactor: legal_rates.py reads CIVIL_ANNUAL_RATE from parametro_service"
```

---

### Task 12: Re-wire `historical_index.py` — SMLMV and IPC

**Files:**
- Modify: `app/engine/indexation/historical_index.py`
- Test: `tests/engine/test_historical_index.py`

The module-level dicts (`_SMLMV_POR_ANIO`, `_IPC_VARIACION_ANUAL`, `_IPC_INDICE_ACUMULADO`) are **not touched** in this task — they stay exactly as-is (Task 6's migration script already reads them, and the existing tests asserting against them directly keep passing unchanged). Only the five public functions change internally.

- [ ] **Step 1: Confirm baseline**

Run: `python -m pytest tests/engine/test_historical_index.py -v`
Expected: all passed (note the count — this is the regression net for this task)

- [ ] **Step 2: Add a fixture that seeds the DB from the migration script**

Add near the top of `tests/engine/test_historical_index.py` (this reuses Task 6's `migrar()` instead of re-seeding by hand, so the test DB always matches exactly what production would have):

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.database as database_module
import database.session as session_module


@pytest.fixture(autouse=True)
def _parametros_legales_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    from scripts.migrate_parametros_legales import migrar
    migrar()
```

- [ ] **Step 3: Run — should still pass (fixture only, no source change yet)**

Run: `python -m pytest tests/engine/test_historical_index.py -v`
Expected: same count as Step 1

- [ ] **Step 4: Re-wire `get_smlmv_for_year`, `get_ipc_for_date`, `get_ipc_interpolado_for_date`**

In `app/engine/indexation/historical_index.py`, add the imports (near the top, after the existing `from typing import ...` line):

```python
from app.core.exceptions import ParametroNoDisponibleError
from app.services.parametro_service import get_parametro, ultimo_anio_disponible
```

Replace:

```python
def get_smlmv_for_year(anio: int) -> Decimal:
    """Retorna el Salario Minimo Legal Mensual Vigente para el año dado.
    Datos disponibles: 1984-2026 (2027 aun no definido por el Gobierno a la fecha
    del documento fuente)."""
    if anio not in _SMLMV_POR_ANIO:
        raise ValueError(
            f"No hay SMLMV configurado para el año {anio}. "
            f"Datos disponibles: {min(_SMLMV_POR_ANIO)}-{max(_SMLMV_POR_ANIO)}."
        )
    return _SMLMV_POR_ANIO[anio]
```

with:

```python
def get_smlmv_for_year(anio: int) -> Decimal:
    """Retorna el Salario Minimo Legal Mensual Vigente para el año dado,
    consultando la tabla parametros_legales (clave SMLMV, editable desde la
    GUI). Antes de la migracion de este sprint, el año debia existir en
    _SMLMV_POR_ANIO (que sigue siendo la referencia congelada de origen, ver
    scripts/migrate_parametros_legales.py)."""
    try:
        return get_parametro("SMLMV", date(anio, 1, 1))
    except ParametroNoDisponibleError as error:
        raise ValueError(
            f"No hay SMLMV configurado para el año {anio}."
        ) from error
```

Replace:

```python
def get_ipc_for_date(fecha: date) -> Decimal:
    """Retorna el indice IPC acumulado de cierre de año (31-dic) del año de `fecha`.
    Datos disponibles: 1967-2025. La fuente solo trae variacion ANUAL -- no hay
    granularidad mensual; interpolar a un mes especifico dentro del año es
    responsabilidad del Sprint 8 (indexacion IPC conectada a Civil/Familia)."""
    anio = fecha.year
    if anio not in _IPC_INDICE_ACUMULADO:
        raise ValueError(
            f"No hay indice IPC configurado para el año {anio}. "
            f"Datos disponibles: {min(_IPC_INDICE_ACUMULADO)}-{max(_IPC_INDICE_ACUMULADO)}."
        )
    return _IPC_INDICE_ACUMULADO[anio]
```

with:

```python
def get_ipc_for_date(fecha: date) -> Decimal:
    """Retorna el indice IPC acumulado de cierre de año (31-dic) del año de
    `fecha`, consultando parametros_legales (clave IPC_INDICE_ACUMULADO). La
    fuente solo trae variacion ANUAL -- no hay granularidad mensual; interpolar
    a un mes especifico dentro del año es responsabilidad de
    get_ipc_interpolado_for_date."""
    try:
        return get_parametro("IPC_INDICE_ACUMULADO", date(fecha.year, 1, 1))
    except ParametroNoDisponibleError as error:
        raise ValueError(
            f"No hay indice IPC configurado para el año {fecha.year}."
        ) from error
```

Replace the body of `get_ipc_interpolado_for_date` (keep its docstring):

```python
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
```

with:

```python
    anio_max = ultimo_anio_disponible("IPC_INDICE_ACUMULADO")

    if fecha.year > anio_max:
        return get_parametro("IPC_INDICE_ACUMULADO", date(anio_max, 1, 1))

    v2 = get_ipc_for_date(date(fecha.year, 12, 31))
    try:
        v1 = get_ipc_for_date(date(fecha.year - 1, 12, 31))
    except ValueError:
        v1 = Decimal("100")
```

(the `if t1 + t2 == 0: return v2` and final interpolation `return` lines stay unchanged — only the variable-resolution lines above them change. The old explicit `anio_min` lower-bound check is gone because `get_ipc_for_date` inside the `v1`/`v2` resolution now raises `ValueError` itself for years before the data starts, via `ParametroNoDisponibleError` → `ValueError`, which is caught for `v1` and left to propagate for `v2` — same externally-visible behavior as before.)

- [ ] **Step 5: Run to verify it passes**

Run: `python -m pytest tests/engine/test_historical_index.py -v`
Expected: same count as Step 1, all passed. If `test_ipc_fuera_de_rango_lanza_value_error` or `test_smlmv_fuera_de_rango_lanza_value_error` fail, check that `_parametros_legales_en_memoria`'s `migrar()` call actually ran before the assertion (autouse fixtures run once per test function, so this should already be the case) — do not weaken the test's assertion to make it pass.

- [ ] **Step 6: Commit**

```bash
git add app/engine/indexation/historical_index.py tests/engine/test_historical_index.py
git commit -m "refactor: get_smlmv_for_year/get_ipc_for_date/get_ipc_interpolado_for_date read from parametro_service"
```

---

### Task 13: Re-wire `historical_index.py` — IBC/usura

**Files:**
- Modify: `app/engine/indexation/historical_index.py`
- Test: `tests/engine/test_historical_index.py`

- [ ] **Step 1: Confirm baseline**

Run: `python -m pytest tests/engine/test_historical_index.py -v`
Expected: all passed (same count as Task 12 left it — the fixture from Task 12 already covers this task, no new fixture needed)

- [ ] **Step 2: Re-wire `get_ibc_usura_for_date`**

Replace:

```python
def get_ibc_usura_for_date(fecha: date) -> Tuple[Decimal, Decimal]:
    """Retorna (ibc_anual, usura_anual) certificados por la SFC para la linea
    'Consumo y Ordinario' (sucesora de 'Comercial' desde 2007) vigentes en `fecha`.
    Datos disponibles: 1997-07-01 a 2026-07-31."""
    for tramo in _TRAMOS_IBC_USURA:
        if tramo.inicio <= fecha <= tramo.fin:
            return (tramo.ibc_anual, tramo.usura_anual)
    raise ValueError(
        f"No hay tramo de IBC/Usura configurado para la fecha {fecha}. "
        f"Datos disponibles: {min(t.inicio for t in _TRAMOS_IBC_USURA)} a "
        f"{max(t.fin for t in _TRAMOS_IBC_USURA)}."
    )
```

with:

```python
def get_ibc_usura_for_date(fecha: date) -> Tuple[Decimal, Decimal]:
    """Retorna (ibc_anual, usura_anual) certificados por la SFC para la linea
    'Consumo y Ordinario' (sucesora de 'Comercial' desde 2007) vigentes en
    `fecha`, consultando parametros_legales (claves IBC_CONSUMO_ORDINARIO y
    USURA_CONSUMO_ORDINARIO, modo TRAMO_CERRADO -- no extrapola fuera de los
    tramos cargados)."""
    try:
        ibc = get_parametro("IBC_CONSUMO_ORDINARIO", fecha)
        usura = get_parametro("USURA_CONSUMO_ORDINARIO", fecha)
    except ParametroNoDisponibleError as error:
        raise ValueError(
            f"No hay tramo de IBC/Usura configurado para la fecha {fecha}."
        ) from error
    return (ibc, usura)
```

- [ ] **Step 3: Re-wire `get_tramos_ibc_usura_between`**

This function returns `TramoIBCUsura` objects with `inicio`/`fin` boundaries (not single point values), which `parametro_service` doesn't expose directly — reconstruct them from the frozen `_TRAMOS_IBC_USURA` reference list, but validate availability through `get_parametro` first so a tramo edited later via the GUI is still honored as "available or not." Replace:

```python
def get_tramos_ibc_usura_between(inicio: date, fin: date) -> List[TramoIBCUsura]:
    """Tramos de _TRAMOS_IBC_USURA que se solapan con [inicio, fin], en orden
    cronologico (la tabla ya esta ordenada por construccion, verificado en el
    Sprint 5: sin vacios en todo el rango). Lanza ValueError si fin < inicio, o
    si ningun tramo se solapa con el rango pedido (fuera de los datos
    disponibles: 1997-07-01 a 2026-07-31)."""
    if fin < inicio:
        raise ValueError(f"Rango invalido: fin ({fin}) es anterior a inicio ({inicio}).")

    tramos = [t for t in _TRAMOS_IBC_USURA if t.inicio <= fin and t.fin >= inicio]
    if not tramos:
        raise ValueError(
            f"No hay tramos de IBC/Usura configurados para el rango [{inicio}, {fin}]. "
            f"Datos disponibles: {min(t.inicio for t in _TRAMOS_IBC_USURA)} a "
            f"{max(t.fin for t in _TRAMOS_IBC_USURA)}."
        )
    return tramos
```

with:

```python
def get_tramos_ibc_usura_between(inicio: date, fin: date) -> List[TramoIBCUsura]:
    """Tramos de IBC/usura que se solapan con [inicio, fin], en orden
    cronologico, reconstruidos desde parametros_legales (clave
    USURA_CONSUMO_ORDINARIO, la que trae el ibc_anual asociado se resuelve por
    tramo via get_ibc_usura_for_date para que ambas claves se mantengan
    consistentes). Lanza ValueError si fin < inicio, o si ningun tramo se
    solapa con el rango pedido."""
    if fin < inicio:
        raise ValueError(f"Rango invalido: fin ({fin}) es anterior a inicio ({inicio}).")

    session = session_module.get_session()
    try:
        filas = (
            session.query(ParametroLegal)
            .filter(
                ParametroLegal.clave == "USURA_CONSUMO_ORDINARIO",
                ParametroLegal.vigente_desde <= fin,
                ParametroLegal.vigente_hasta.is_not(None),
                ParametroLegal.vigente_hasta >= inicio,
            )
            .order_by(ParametroLegal.vigente_desde)
            .all()
        )
    finally:
        session.close()

    if not filas:
        raise ValueError(
            f"No hay tramos de IBC/Usura configurados para el rango [{inicio}, {fin}]."
        )

    tramos = []
    for fila in filas:
        ibc_anual, usura_anual = get_ibc_usura_for_date(fila.vigente_desde)
        tramos.append(TramoIBCUsura(fila.vigente_desde, fila.vigente_hasta, ibc_anual, usura_anual))
    return tramos
```

Add the two imports this needs at the top of the module:

```python
import database.session as session_module
from database.models import ParametroLegal
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/engine/test_historical_index.py -v`
Expected: same count as Task 12's baseline, all passed — including `test_tramos_entre_rango_dentro_de_un_solo_tramo`, `test_tramos_entre_rango_que_cruza_dos_meses`, and `test_ibc_usura_limite_solape_septiembre_2017` (these exercise the exact boundary-preservation this reconstruction depends on).

- [ ] **Step 5: Run the full suite for a final regression check on this module**

Run: `python -m pytest tests/engine/tax/test_moratory_interest.py tests/services/test_area_strategy.py -v`
Expected: all passed (`moratory_interest.py` calls `get_tramos_ibc_usura_between`, and `ComercialStrategy` uses IBC/usura indirectly through obligation fields — this confirms the reconstruction didn't break either consumer)

- [ ] **Step 6: Commit**

```bash
git add app/engine/indexation/historical_index.py tests/engine/test_historical_index.py
git commit -m "refactor: get_ibc_usura_for_date/get_tramos_ibc_usura_between read from parametro_service"
```

---

### Task 14: GUI — `ParametrosView` (list screen)

**Files:**
- Modify: `app/views/configuracion.py` (currently empty)
- Test: `tests/views/test_configuracion.py`

- [ ] **Step 1: Write the failing test**

Create `tests/views/test_configuracion.py` (relies on the autouse `_db_en_memoria_por_defecto` fixture already provided by `tests/views/conftest.py`):

```python
from datetime import date

from app.services.parametro_service import agregar_valor
from app.views.configuracion import ParametrosView


def test_parametros_view_lista_todas_las_claves_del_catalogo():
    from app.services.parametro_service import CATALOGO_PARAMETROS

    vista = ParametrosView()
    assert vista.tabla.rowCount() == len(CATALOGO_PARAMETROS)


def test_parametros_view_muestra_sin_dato_cuando_no_hay_valor_cargado():
    vista = ParametrosView()
    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 2).text() == "(sin dato)"


def test_parametros_view_muestra_el_valor_vigente_cuando_hay_dato():
    agregar_valor("USURA_MULTIPLICADOR", "1.5", date(1900, 1, 1), "test")
    vista = ParametrosView()
    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 2).text() == "1.5"
```

(Note: `agregar_valor`'s `valor` parameter is typed `Decimal` in the service, but the test passes a plain string — fix the test to `Decimal("1.5")` per the imports; add `from decimal import Decimal` to the test file.)

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/views/test_configuracion.py -v`
Expected: FAIL — `ImportError: cannot import name 'ParametrosView'`

- [ ] **Step 3: Implement `ParametrosView`**

Write `app/views/configuracion.py`:

```python
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.parametro_service import CATALOGO_PARAMETROS, valor_vigente_hoy


class ParametrosView(QWidget):
    def __init__(self):
        super().__init__()
        self._claves_por_fila: list[str] = []

        columnas = ["Categoria", "Parametro", "Valor vigente hoy", "Vigente desde"]
        self.tabla = QTableWidget(0, len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        boton_agregar = QPushButton("+ Agregar valor nuevo")
        boton_agregar.clicked.connect(self._abrir_dialogo_agregar)

        botones = QHBoxLayout()
        botones.addWidget(boton_agregar)

        layout = QVBoxLayout()
        layout.addLayout(botones)
        layout.addWidget(self.tabla)
        self.setLayout(layout)

        self.refrescar()

    def refrescar(self) -> None:
        claves = list(CATALOGO_PARAMETROS.items())
        self.tabla.setRowCount(len(claves))
        self._claves_por_fila = []
        for fila_idx, (clave, info) in enumerate(claves):
            vigente = valor_vigente_hoy(clave)
            self.tabla.setItem(fila_idx, 0, QTableWidgetItem(info.categoria))
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(info.descripcion))
            self.tabla.setItem(
                fila_idx, 2, QTableWidgetItem(str(vigente.valor) if vigente else "(sin dato)")
            )
            self.tabla.setItem(
                fila_idx, 3,
                QTableWidgetItem(vigente.vigente_desde.isoformat() if vigente else ""),
            )
            self._claves_por_fila.append(clave)

    def _abrir_dialogo_agregar(self) -> None:
        pass  # implementado en la siguiente tarea
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/views/test_configuracion.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/views/configuracion.py tests/views/test_configuracion.py
git commit -m "feat: add ParametrosView list screen"
```

---

### Task 15: GUI — `ParametroFormDialog` (add a value)

**Files:**
- Modify: `app/views/configuracion.py`
- Test: `tests/views/test_configuracion.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/views/test_configuracion.py`:

```python
from decimal import Decimal

from app.services.parametro_service import historial
from app.views.configuracion import ParametroFormDialog


def test_parametro_form_dialog_guarda_un_valor_abierto():
    dialogo = ParametroFormDialog()
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")
    dialogo.guardar()

    filas = historial("USURA_MULTIPLICADOR")
    assert len(filas) == 1
    assert filas[0].valor == Decimal("1.5")
    assert filas[0].usuario == "abogado1"


def test_parametro_form_dialog_valor_invalido_lanza_value_error():
    dialogo = ParametroFormDialog()
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("no-es-un-numero")
    dialogo.campo_usuario.setText("abogado1")
    try:
        dialogo.guardar()
        assert False, "se esperaba ValueError"
    except ValueError:
        pass


def test_parametro_form_dialog_usuario_vacio_lanza_value_error():
    dialogo = ParametroFormDialog()
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    try:
        dialogo.guardar()
        assert False, "se esperaba ValueError"
    except ValueError:
        pass


def test_parametro_form_dialog_muestra_vigente_hasta_solo_para_tramo_cerrado():
    dialogo = ParametroFormDialog()

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    assert dialogo.campo_vigente_hasta.isVisible() is False

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("IBC_CONSUMO_ORDINARIO"))
    assert dialogo.campo_vigente_hasta.isVisible() is True
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/views/test_configuracion.py -v`
Expected: FAIL — `ImportError: cannot import name 'ParametroFormDialog'`

- [ ] **Step 3: Implement `ParametroFormDialog`**

Add to `app/views/configuracion.py` (imports first, then the new class before `ParametrosView`):

Replace the top import block:

```python
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.parametro_service import CATALOGO_PARAMETROS, valor_vigente_hoy
```

with:

```python
from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.parametro_service import (
    CATALOGO_PARAMETROS,
    ModoResolucion,
    agregar_valor,
    valor_vigente_hoy,
)
```

Add this class before `class ParametrosView(QWidget):`:

```python
class ParametroFormDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar valor de parametro")

        self.combo_clave = QComboBox()
        for clave, info in CATALOGO_PARAMETROS.items():
            self.combo_clave.addItem(f"{info.descripcion} ({clave})", userData=clave)

        self.campo_valor = QLineEdit()
        self.campo_vigente_desde = QDateEdit(QDate.currentDate())
        self.campo_vigente_desde.setCalendarPopup(True)
        self.campo_vigente_hasta = QDateEdit(QDate.currentDate())
        self.campo_vigente_hasta.setCalendarPopup(True)
        self.campo_usuario = QLineEdit()
        self.campo_motivo = QLineEdit()

        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
        layout.addRow("Parametro", self.combo_clave)
        layout.addRow("Valor", self.campo_valor)
        layout.addRow("Vigente desde", self.campo_vigente_desde)
        layout.addRow("Vigente hasta", self.campo_vigente_hasta)
        layout.addRow("Usuario", self.campo_usuario)
        layout.addRow("Motivo (opcional)", self.campo_motivo)
        layout.addRow(boton_guardar)
        self.setLayout(layout)

        self.combo_clave.currentIndexChanged.connect(self._actualizar_visibilidad_vigente_hasta)
        self._actualizar_visibilidad_vigente_hasta()

    def _actualizar_visibilidad_vigente_hasta(self) -> None:
        clave = self.combo_clave.currentData()
        info = CATALOGO_PARAMETROS[clave]
        self.campo_vigente_hasta.setVisible(info.modo == ModoResolucion.TRAMO_CERRADO)

    def guardar(self):
        clave = self.combo_clave.currentData()
        info = CATALOGO_PARAMETROS[clave]

        try:
            valor = Decimal(self.campo_valor.text())
        except InvalidOperation as error:
            raise ValueError("El valor debe ser un numero valido.") from error

        usuario = self.campo_usuario.text().strip()
        if not usuario:
            raise ValueError("El campo Usuario es obligatorio.")

        qdate_desde = self.campo_vigente_desde.date()
        vigente_desde = date(qdate_desde.year(), qdate_desde.month(), qdate_desde.day())

        vigente_hasta = None
        if info.modo == ModoResolucion.TRAMO_CERRADO:
            qdate_hasta = self.campo_vigente_hasta.date()
            vigente_hasta = date(qdate_hasta.year(), qdate_hasta.month(), qdate_hasta.day())

        motivo = self.campo_motivo.text().strip() or None

        return agregar_valor(
            clave=clave,
            valor=valor,
            vigente_desde=vigente_desde,
            usuario=usuario,
            motivo=motivo,
            vigente_hasta=vigente_hasta,
        )

    def _guardar_y_cerrar(self) -> None:
        try:
            self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos invalidos", str(error))
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/views/test_configuracion.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add app/views/configuracion.py tests/views/test_configuracion.py
git commit -m "feat: add ParametroFormDialog"
```

---

### Task 16: GUI — wire the "+ Agregar valor nuevo" button and the historial dialog

**Files:**
- Modify: `app/views/configuracion.py`
- Test: `tests/views/test_configuracion.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/views/test_configuracion.py`:

```python
from app.views.configuracion import HistorialParametroDialog


def test_historial_parametro_dialog_lista_todas_las_filas_de_una_clave():
    agregar_valor("SMLMV", Decimal("1423500.00"), date(2025, 1, 1), "abogado1")
    agregar_valor("SMLMV", Decimal("1750905.00"), date(2026, 1, 1), "abogado1")

    dialogo = HistorialParametroDialog("SMLMV")
    assert dialogo.tabla.rowCount() == 2
    assert dialogo.tabla.item(0, 0).text() == "1750905.00"


def test_parametros_view_abrir_dialogo_agregar_refresca_la_tabla(monkeypatch):
    from PySide6.QtWidgets import QDialog

    vista = ParametrosView()
    monkeypatch.setattr(ParametroFormDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(ParametroFormDialog, "guardar", lambda self: agregar_valor(
        "USURA_MULTIPLICADOR", Decimal("1.5"), date(1900, 1, 1), "abogado1",
    ))

    vista._abrir_dialogo_agregar()

    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 2).text() == "1.5"
```

(add `from app.views.configuracion import ParametroFormDialog, ParametrosView` to the top imports if not already present as separate lines).

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/views/test_configuracion.py -v`
Expected: FAIL — `ImportError: cannot import name 'HistorialParametroDialog'`, and the second test fails because `_abrir_dialogo_agregar` is a no-op

- [ ] **Step 3: Implement**

In `app/views/configuracion.py`, add `historial` to the import from `app.services.parametro_service`:

```python
from app.services.parametro_service import (
    CATALOGO_PARAMETROS,
    ModoResolucion,
    agregar_valor,
    historial,
    valor_vigente_hoy,
)
```

Add this class after `ParametroFormDialog` and before `ParametrosView`:

```python
class HistorialParametroDialog(QDialog):
    def __init__(self, clave: str, parent=None):
        super().__init__(parent)
        info = CATALOGO_PARAMETROS[clave]
        self.setWindowTitle(f"Historial: {info.descripcion}")

        columnas = ["Valor", "Vigente desde", "Vigente hasta", "Usuario", "Motivo"]
        self.tabla = QTableWidget(0, len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        filas = historial(clave)
        self.tabla.setRowCount(len(filas))
        for fila_idx, fila in enumerate(filas):
            self.tabla.setItem(fila_idx, 0, QTableWidgetItem(str(fila.valor)))
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(fila.vigente_desde.isoformat()))
            self.tabla.setItem(
                fila_idx, 2,
                QTableWidgetItem(fila.vigente_hasta.isoformat() if fila.vigente_hasta else ""),
            )
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(fila.usuario))
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(fila.motivo or ""))

        layout = QVBoxLayout()
        layout.addWidget(self.tabla)
        self.setLayout(layout)
```

In `ParametrosView.__init__`, after `self.tabla.setEditTriggers(...)`, add:

```python
        self.tabla.cellDoubleClicked.connect(self._abrir_historial)
```

Replace the `_abrir_dialogo_agregar` placeholder:

```python
    def _abrir_dialogo_agregar(self) -> None:
        pass  # implementado en la siguiente tarea
```

with:

```python
    def _abrir_dialogo_agregar(self) -> None:
        dialogo = ParametroFormDialog(self)
        if dialogo.exec():
            self.refrescar()

    def _abrir_historial(self, fila: int, _columna: int) -> None:
        clave = self._claves_por_fila[fila]
        HistorialParametroDialog(clave, self).exec()
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/views/test_configuracion.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add app/views/configuracion.py tests/views/test_configuracion.py
git commit -m "feat: wire agregar-valor button and historial dialog in ParametrosView"
```

---

### Task 17: Wire `ParametrosView` into `main_window.py` navigation

**Files:**
- Modify: `app/views/main_window.py`
- Test: `tests/views/test_main_window.py`

- [ ] **Step 1: Confirm baseline**

Run: `python -m pytest tests/views/test_main_window.py -v`
Expected: all passed (note the count — the file uses the `qtbot` fixture from `pytest-qt` and the pattern `window = MainWindow(); qtbot.addWidget(window)` in every test, e.g. `test_main_window_navega_a_la_pagina_de_resultado`)

- [ ] **Step 2: Write the failing test**

Append to `tests/views/test_main_window.py`, matching the file's existing style exactly:

```python
def test_boton_parametros_navega_a_la_pantalla_de_parametros(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.boton_parametros.click()

    assert window.stacked_widget.currentWidget() is window.parametros_page
```

- [ ] **Step 3: Run to verify it fails**

Run: `python -m pytest tests/views/test_main_window.py -v`
Expected: FAIL — `AttributeError: 'MainWindow' object has no attribute 'boton_parametros'`

- [ ] **Step 4: Wire it up**

In `app/views/main_window.py`, add the import:

```python
from app.views.configuracion import ParametrosView
```

In `__init__`, after `self.resultado_page = ResultadoLiquidacionView()`, add:

```python
        self.parametros_page = ParametrosView()
```

After `self.stacked_widget.addWidget(self.resultado_page)`, add:

```python
        self.stacked_widget.addWidget(self.parametros_page)
```

In the `self._pages = {...}` dict, add the new key:

```python
        self._pages = {
            "expedientes": self.expedientes_page,
            "detalle": self.detalle_page,
            "resultado": self.resultado_page,
            "parametros": self.parametros_page,
        }
```

In `_crear_barra_navegacion`, after the `self.boton_inicio` block (before `self.addToolBar(barra)`), add:

```python
        self.boton_parametros = QPushButton("⚙ Parametros")
        self.boton_parametros.clicked.connect(self._ir_a_parametros)
        barra.addWidget(self.boton_parametros)
```

Add this method, near `_abrir_detalle`/`_mostrar_resultado`:

```python
    def _ir_a_parametros(self) -> None:
        self.parametros_page.refrescar()
        self.show_page("parametros")
```

- [ ] **Step 5: Run to verify it passes**

Run: `python -m pytest tests/views/test_main_window.py -v`
Expected: all passed, one more than the Step 1 baseline

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest -v`
Expected: all passed, zero failures anywhere in the project

- [ ] **Step 7: Commit**

```bash
git add app/views/main_window.py tests/views/test_main_window.py
git commit -m "feat: wire ParametrosView into main window navigation"
```

---

### Task 18: Manual smoke test

**Files:** none (manual verification only)

- [ ] **Step 1: Run the app against the real database**

Run: `python main.py`

- [ ] **Step 2: Walk through the flow**

1. Click "⚙ Parametros" in the toolbar — confirm the table lists all 16 parameters (grouped informally by the "Categoria" column), and that the ones seeded by Task 6's migration (run against the real `bastium.db` in Task 6, Step 5) show a value under "Valor vigente hoy" instead of "(sin dato)".
2. Click "+ Agregar valor nuevo", pick `SMLMV`, enter a value, a `vigente_desde` of `2027-01-01`, a usuario, and save. Confirm the table's `SMLMV` row now shows the new value (since `2027-01-01 <= hoy`... note: if the system date is before 2027, "Valor vigente hoy" for SMLMV will *not* show the new value yet — that's correct `ANUAL_EXACTO` behavior, not a bug. Verify instead by double-clicking the `SMLMV` row and confirming the new entry appears in the historial dialog).
3. Pick `IBC_CONSUMO_ORDINARIO`, confirm the "Vigente hasta" field becomes visible; pick `USURA_MULTIPLICADOR`, confirm it hides again.
4. Go liquidate a Comercial obligation end-to-end (same smoke path as prior sprints) and confirm the result is unchanged from before this sprint — the usury validation and any IBC/usura-driven interest must produce identical numbers to before, since Task 6 seeded from the exact same source data.

- [ ] **Step 3: Report findings**

If anything in the manual walkthrough doesn't match, stop and fix it before proceeding to Task 19 — do not paper over a real discrepancy with a documentation note.

---

### Task 19: Update `README.md` and `docs/GUIA_USUARIO.md`

**Files:**
- Modify: `README.md`
- Modify: `docs/GUIA_USUARIO.md`

Mandatory per `Pendientes.md`'s sprint-closure rule: these two docs must reflect the new capability.

- [ ] **Step 1: Update `README.md`'s "Estado actual" section**

In `README.md`, after the paragraph ending "...con reconstrucción exacta de un cálculo pasado con solo hacer doble clic sobre su fila." (line 31), add a new paragraph:

```markdown

✅ **Parámetros legales versionados:** desde la pantalla "⚙ Parámetros" cualquier abogado puede consultar
y agregar, sin tocar código, los valores/tasas/topes que antes solo un desarrollador podía cambiar: el
multiplicador de usura, los topes de cuota litis, los plazos de prescripción/caducidad, el descuento del
interés moratorio tributario (E.T. art. 635), la tasa civil legal, y las series históricas de SMLMV, IPC
e IBC/Tasa de Usura. Cada valor queda con su fecha de vigencia, quién lo agregó y por qué — nunca se edita
ni se borra una fila, solo se agregan valores nuevos, así que el historial completo de cada parámetro
queda siempre disponible con doble clic.
```

- [ ] **Step 2: Add the migration note in the "Instalación rápida" section**

In `README.md`, after the paragraph ending "...Igual que el script del Sprint 8, es idempotente y solo hace falta una vez por instalación." (around line 70), add:

```markdown

**Si ya tenías `bastium.db` creado antes de este sprint**, corre una vez
`python scripts/migrate_parametros_legales.py` antes de abrir la app — crea y siembra la tabla
`parametros_legales` con los valores hoy vigentes (usura, cuota litis, prescripción/caducidad, SMLMV,
IPC, IBC/usura), para que la pantalla "⚙ Parámetros" y todos los motores que ahora la consultan tengan
datos desde el primer arranque. Es idempotente y solo hace falta una vez por instalación.
```

- [ ] **Step 3: Update `docs/GUIA_USUARIO.md`**

Read `docs/GUIA_USUARIO.md` first to find where other screens are documented (it's written "step by step, assuming nothing", per `README.md`'s own description) and add a new section following the same structure/tone as the existing screen sections (likely titled something like "Cómo editar tasas y topes legales"), covering: where the screen lives (toolbar button "⚙ Parámetros"), what the table shows, how to add a new value (the form fields, and that `vigente_hasta` only appears for the two IBC/usura parameters), and that values are never deleted — only added, with the full history reachable by double-clicking a row.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/GUIA_USUARIO.md
git commit -m "docs: document Parametros legales versionados screen"
```

---

### Task 20: Close out `Pendientes.md`

**Files:**
- Modify: `Pendientes.md`

- [ ] **Step 1: Update the Sprint 13 status**

In `Pendientes.md`, find the section header (currently `## Sprint 13 — Arquitectura de motor de reglas versionado (EFDJ) ⛔ Cerrado (EFDJ completo), 🔄 reemplazado por "Parámetros legales versionados"`) and change it to:

```markdown
## Sprint 13 — Arquitectura de motor de reglas versionado (EFDJ) ⛔ Cerrado (EFDJ completo), ✅ "Parámetros legales versionados" implementado
```

At the end of the "Actualización (2026-07-20, misma sesión)" paragraph (after "...sin cambios sobre esa parte de la decisión."), add:

```markdown

**Estado de la implementación:** Completado — ver
`docs/superpowers/plans/2026-07-20-parametros-legales-versionados.md`. Tabla `parametros_legales`
(append-only, 3 modos de resolución: `ABIERTO`/`ANUAL_EXACTO`/`TRAMO_CERRADO`), servicio
`app/services/parametro_service.py`, script de siembra `scripts/migrate_parametros_legales.py`, seis
motores re-cableados (`usury_validator`, `HonorariosStrategy`, `prescripcion`, `moratory_interest`,
`legal_rates`, `historical_index`) sin cambiar ningún resultado de cálculo existente, y pantalla nueva
"⚙ Parámetros" en la GUI. Las constantes Python originales se conservan deliberadamente (no se borraron)
como transcripción congelada y fuente del script de siembra — ver la spec, sección "Motores a re-cablear".
```

- [ ] **Step 2: Commit**

```bash
git add Pendientes.md
git commit -m "docs: mark parametros legales versionados sprint completed"
```

---

## Self-review notes (for whoever executes this plan)

- **Spec coverage:** Tasks 1-6 cover the data model, service, and migration. Tasks 7-13 cover all six consuming modules named in the spec's "Motores a re-cablear" section. Tasks 14-17 cover the GUI section. Task 19 covers the mandatory docs rule. Task 20 closes the loop in `Pendientes.md`. Nothing in the spec is left unaddressed.
- **Ordering matters:** Task 6 (migration script) must run before Tasks 7-13 (rewiring) — the migration script's test suite and its real run against `bastium.db` both depend on the source constants still being read live at that point, which is true throughout this plan since none of the rewiring tasks delete those constants.
- **If a step's "Expected" doesn't match:** stop and investigate before moving to the next step — per this project's `superpowers:systematic-debugging` norms, do not adjust a test's assertion just to make it pass without understanding why it originally failed.
