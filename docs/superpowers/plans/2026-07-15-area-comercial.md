# Área Comercial (Sprint 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `ComercialStrategy.liquidar()` so the "Comercial" area calculates real liquidations (Art. 884 C.Co. remuneratorio/moratorio interest with a per-obligación rate split, usury cap validation, IPC-indexation incompatibility), and enable it end-to-end in the GUI.

**Architecture:** Reuses the existing `AreaStrategy`/`UniversalLiquidationService`/`MemoryRateProvider` infrastructure exactly like `CivilFamiliaStrategy`. Three new nullable columns on `Obligacion` (`tasa_moratoria_anual`, `fecha_vencimiento`, `ibc_vigente_anual`) carry the Comercial-specific data. A new `usury_validator` module enforces the 1.5×IBC cap. No changes to `LiquidationCore`, `AllocationEngine`, or `UniversalLiquidationService`.

**Tech Stack:** Python 3.14, SQLAlchemy (declarative models, SQLite), PySide6 (GUI), pytest + pytest-qt.

**Design doc:** `docs/superpowers/specs/2026-07-15-area-comercial-design.md` — read it first if anything below is unclear; it has the full rationale (including the known `MemoryRateProvider` single-timeline limitation).

---

### Task 1: Data model — add Comercial fields to `Obligacion`

**Files:**
- Modify: `database/models.py:44-64`
- Delete: `bastium.db` (repo root)

- [ ] **Step 1: Add the three new columns to `Obligacion`**

In `database/models.py`, inside `class Obligacion(Base):`, add these three lines directly after the existing `fecha_fin` column (line 59):

```python
    fecha_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    tasa_moratoria_anual: Mapped[Decimal | None] = mapped_column(Numeric(9, 4), nullable=True)
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    ibc_vigente_anual: Mapped[Decimal | None] = mapped_column(Numeric(9, 4), nullable=True)
```

All three are nullable at the schema level (Civil/Familia obligaciones never set them); `ComercialStrategy` enforces they're present at liquidation time (Task 4).

- [ ] **Step 2: Verify the model change doesn't break existing tests**

Run: `python -m pytest tests/services/test_area_strategy.py tests/views/test_obligaciones.py -q`
Expected: same pass count as before this change (all existing tests use in-memory SQLite created fresh via `Base.metadata.create_all`, so the new nullable columns don't require any test changes yet).

- [ ] **Step 3: Delete and let the dev database recreate itself**

```bash
rm bastium.db
```

`bastium.db` only held the MVP smoke-test row (1 expediente, 1 obligación, 1 abono) — it gets recreated automatically with the new schema the next time `python main.py` runs (`main.py` calls `init_db()` on startup, which calls `Base.metadata.create_all(engine)`).

- [ ] **Step 4: Commit**

```bash
git add database/models.py
git commit -m "feat(db): add tasa_moratoria_anual, fecha_vencimiento, ibc_vigente_anual to Obligacion"
```

(`bastium.db` is already gitignored — confirm with `git status` that it doesn't show up before committing; if it does, do not add it.)

---

### Task 2: `TasaUsurariaError` exception

**Files:**
- Modify: `app/core/exceptions.py`

- [ ] **Step 1: Add the exception**

`app/core/exceptions.py` currently only has `AreaNoImplementadaError`. Append:

```python
class TasaUsurariaError(Exception):
    """Se lanza cuando una tasa pactada (remuneratoria o moratoria) supera 1.5x el IBC vigente."""
```

Full file after this change:

```python
class AreaNoImplementadaError(Exception):
    """Se lanza cuando se intenta liquidar un area del derecho aun no implementada."""


class TasaUsurariaError(Exception):
    """Se lanza cuando una tasa pactada (remuneratoria o moratoria) supera 1.5x el IBC vigente."""
```

- [ ] **Step 2: Commit**

```bash
git add app/core/exceptions.py
git commit -m "feat(core): add TasaUsurariaError exception"
```

---

### Task 3: Usury cap validator

**Files:**
- Create: `app/engine/interest/usury_validator.py`
- Test: `tests/engine/test_usury_validator.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/engine/test_usury_validator.py`:

```python
from decimal import Decimal

import pytest

from app.core.exceptions import TasaUsurariaError
from app.engine.interest.usury_validator import validar_tasa_usura


def test_tasa_por_debajo_del_tope_no_lanza_error():
    validar_tasa_usura(Decimal("20.00"), Decimal("20.00"), "remuneratoria")


def test_tasa_exactamente_en_el_tope_no_lanza_error():
    validar_tasa_usura(Decimal("30.00"), Decimal("20.00"), "moratoria")


def test_tasa_por_encima_del_tope_lanza_tasa_usuraria_error():
    with pytest.raises(TasaUsurariaError):
        validar_tasa_usura(Decimal("30.01"), Decimal("20.00"), "moratoria")


def test_mensaje_de_error_nombra_la_etiqueta_y_el_tope():
    with pytest.raises(TasaUsurariaError, match="moratoria"):
        validar_tasa_usura(Decimal("35.00"), Decimal("20.00"), "moratoria")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/engine/test_usury_validator.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.engine.interest.usury_validator'`

- [ ] **Step 3: Implement the validator**

Create `app/engine/interest/usury_validator.py`:

```python
from decimal import Decimal

from app.core.exceptions import TasaUsurariaError

TOPE_MULTIPLICADOR = Decimal("1.5")


def validar_tasa_usura(tasa_pactada: Decimal, ibc_vigente: Decimal, etiqueta: str) -> None:
    """Lanza TasaUsurariaError si tasa_pactada supera 1.5 x ibc_vigente (Ley 45/1990, art. 72)."""
    tope = ibc_vigente * TOPE_MULTIPLICADOR
    if tasa_pactada > tope:
        exceso = tasa_pactada - tope
        raise TasaUsurariaError(
            f"La tasa {etiqueta} pactada ({tasa_pactada}%) supera el tope de usura "
            f"(1.5 x IBC = {tope}%) por {exceso} puntos porcentuales."
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/engine/test_usury_validator.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add app/engine/interest/usury_validator.py tests/engine/test_usury_validator.py
git commit -m "feat(interest): add usury cap validator (1.5x IBC)"
```

---

### Task 4: `ComercialStrategy.liquidar()`

This is the core of the sprint. `app/services/area_strategy.py` currently has `ComercialStrategy` as a stub that always raises `AreaNoImplementadaError` (line 92-96), and a parametrized test asserts that. We replace the stub with a real implementation, which means that old test case must be removed as part of this task (it would otherwise fail red once the stub is gone).

**Files:**
- Modify: `app/services/area_strategy.py`
- Modify: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Remove Comercial from the "not implemented" parametrize list**

In `tests/services/test_area_strategy.py`, change:

```python
@pytest.mark.parametrize(
    "area_name,strategy_cls",
    [
        ("COMERCIAL", ComercialStrategy),
        ("LABORAL", LaboralStrategy),
        ("SANCIONATORIO", SancionatorioStrategy),
        ("HONORARIOS", HonorariosStrategy),
    ],
)
```

to:

```python
@pytest.mark.parametrize(
    "area_name,strategy_cls",
    [
        ("LABORAL", LaboralStrategy),
        ("SANCIONATORIO", SancionatorioStrategy),
        ("HONORARIOS", HonorariosStrategy),
    ],
)
```

- [ ] **Step 2: Run the full test file to confirm it's currently green**

Run: `python -m pytest tests/services/test_area_strategy.py -v`
Expected: PASS (all existing tests still pass; `ComercialStrategy` isn't tested for "not implemented" anymore, and nothing tests its real behavior yet)

- [ ] **Step 3: Write the failing tests for `ComercialStrategy`**

Append to `tests/services/test_area_strategy.py`:

```python
from app.core.exceptions import TasaUsurariaError


def _obligacion_comercial(
    expediente_id=1,
    valor=Decimal("1000000.00"),
    tasa_remuneratoria=Decimal("6.00"),
    tasa_moratoria=Decimal("24.00"),
    ibc=Decimal("20.00"),
    fecha_origen=date(2025, 1, 1),
    fecha_vencimiento=date(2025, 2, 1),
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Capital de pagare",
        categoria="CAPITAL_PAGARE",
        fecha_origen=fecha_origen,
        valor=valor,
        tasa_efectiva_anual=tasa_remuneratoria,
        tasa_moratoria_anual=tasa_moratoria,
        fecha_vencimiento=fecha_vencimiento,
        ibc_vigente_anual=ibc,
    )


class TestComercialStrategy:
    def test_liquida_una_obligacion_puntual_sin_abonos(self):
        strategy = ComercialStrategy()
        obligacion = _obligacion_comercial()

        resultado = strategy.liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        assert resultado.final_balance().principal == Decimal("1000000.00")
        assert resultado.final_balance().interest > Decimal("0.00")
        assert resultado.total_payments_applied() == Decimal("0.00")

    def test_aplica_un_abono_reduciendo_el_saldo(self):
        strategy = ComercialStrategy()
        obligacion = _obligacion_comercial()
        abono = Abono(
            id=1, obligacion_id=1, fecha=date(2025, 2, 15), monto=Decimal("200000.00"), referencia="ref-1"
        )

        resultado = strategy.liquidar(
            obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2025, 3, 1)
        )

        assert resultado.total_payments_applied() == Decimal("200000.00")
        assert resultado.final_balance().total() < obligacion.valor

    def test_usa_tasa_moratoria_tras_el_vencimiento_acumula_mas_interes_que_solo_remuneratoria(self):
        fecha_corte = date(2025, 3, 1)
        obligacion_comercial = _obligacion_comercial()
        resultado_comercial = ComercialStrategy().liquidar(
            obligaciones=[obligacion_comercial], abonos=[], fecha_corte=fecha_corte
        )

        # Misma obligacion liquidada solo con la tasa remuneratoria (6%) durante todo el periodo,
        # via CivilFamiliaStrategy, que unicamente lee tasa_efectiva_anual.
        obligacion_solo_remuneratoria = _obligacion_comercial()
        resultado_solo_remuneratoria = CivilFamiliaStrategy().liquidar(
            obligaciones=[obligacion_solo_remuneratoria], abonos=[], fecha_corte=fecha_corte
        )

        # La obligacion vence 2025-02-01 y la tasa moratoria (24%) es mayor que la
        # remuneratoria (6%), asi que el interes acumulado en Comercial (que aplica la
        # moratoria desde el vencimiento) debe ser mayor que si se hubiera usado la
        # remuneratoria durante todo el periodo.
        assert resultado_comercial.final_balance().interest > resultado_solo_remuneratoria.final_balance().interest

    def test_sin_mora_usa_solo_tasa_remuneratoria(self):
        fecha_corte = date(2025, 1, 20)  # antes del vencimiento (2025-02-01)

        obligacion_comercial = _obligacion_comercial()
        resultado_comercial = ComercialStrategy().liquidar(
            obligaciones=[obligacion_comercial], abonos=[], fecha_corte=fecha_corte
        )

        obligacion_civil = _obligacion_comercial()
        resultado_civil = CivilFamiliaStrategy().liquidar(
            obligaciones=[obligacion_civil], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado_comercial.final_balance().interest == resultado_civil.final_balance().interest

    def test_tasa_moratoria_excede_tope_de_usura_lanza_error(self):
        obligacion = _obligacion_comercial(tasa_moratoria=Decimal("35.00"), ibc=Decimal("20.00"))

        with pytest.raises(TasaUsurariaError):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1))

    def test_tasa_remuneratoria_excede_tope_de_usura_lanza_error(self):
        obligacion = _obligacion_comercial(tasa_remuneratoria=Decimal("35.00"), ibc=Decimal("20.00"))

        with pytest.raises(TasaUsurariaError):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1))

    @pytest.mark.parametrize(
        "campo", ["tasa_moratoria_anual", "fecha_vencimiento", "ibc_vigente_anual", "tasa_efectiva_anual"]
    )
    def test_falta_un_campo_comercial_obligatorio_lanza_value_error(self, campo):
        obligacion = _obligacion_comercial()
        setattr(obligacion, campo, None)

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1))

    def test_recurrente_no_hace_split_usa_tasa_moratoria_unica(self):
        obligacion = Obligacion(
            id=2,
            expediente_id=1,
            tipo=TipoObligacion.RECURRENTE,
            concepto="Cuotas de pagare a plazos",
            categoria="CAPITAL_PAGARE",
            fecha_origen=date(2025, 1, 1),
            valor=Decimal("500000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
            tasa_moratoria_anual=Decimal("24.00"),
            fecha_vencimiento=date(2025, 1, 1),
            ibc_vigente_anual=Decimal("20.00"),
            dia_pago=5,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 3, 5),
        )

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 5)
        )

        # 3 cuotas de 500000 causadas: enero, febrero, marzo
        assert resultado.final_balance().principal == Decimal("1500000.00")

    def test_soporta_indexacion_ipc_es_false(self):
        assert ComercialStrategy().soporta_indexacion_ipc is False


def test_civil_familia_soporta_indexacion_ipc_es_true():
    assert CivilFamiliaStrategy().soporta_indexacion_ipc is True
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `python -m pytest tests/services/test_area_strategy.py -v`
Expected: FAIL — the `TestComercialStrategy` cases fail with `AreaNoImplementadaError` instead of the expected results/exceptions; `test_soporta_indexacion_ipc_es_false` and `test_civil_familia_soporta_indexacion_ipc_es_true` fail with `AttributeError: 'ComercialStrategy' object has no attribute 'soporta_indexacion_ipc'`.

- [ ] **Step 5: Implement `ComercialStrategy`**

In `app/services/area_strategy.py`, add these imports at the top (alongside the existing ones):

```python
from app.engine.interest.usury_validator import validar_tasa_usura
```

Add `soporta_indexacion_ipc: bool = True` as a class attribute on `AreaStrategy`:

```python
class AreaStrategy(ABC):
    """Contrato comun para el calculo de liquidacion por area del derecho."""

    soporta_indexacion_ipc: bool = True

    @abstractmethod
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise NotImplementedError
```

Replace the `ComercialStrategy` stub (currently lines 92-96) with:

```python
class ComercialStrategy(AreaStrategy):
    """
    Area Comercial (Art. 884 C.Co.). Cada obligacion debe traer su propia tasa
    remuneratoria (tasa_efectiva_anual), tasa moratoria (tasa_moratoria_anual),
    fecha de vencimiento y el IBC vigente aplicable (ibc_vigente_anual) -- no hay
    fallback automatico a un IBC de referencia en este sprint (ver Pendientes.md,
    Sprint 2 y Sprint 5).

    Split real de tasa remuneratoria (antes del vencimiento) / moratoria (despues)
    solo aplica a obligaciones PUNTUAL. RECURRENTE usa una sola tasa moratoria para
    todo el periodo, igual que CivilFamiliaStrategy, porque el vencimiento de cada
    cuota individual no esta modelado (ver docs/superpowers/specs/2026-07-15-area-comercial-design.md).

    No es compatible con indexacion IPC (soporta_indexacion_ipc = False).
    """

    soporta_indexacion_ipc = False

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_comercial(obligacion)

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

    def _validar_obligacion_comercial(self, obligacion) -> None:
        campos_requeridos = {
            "tasa_efectiva_anual": obligacion.tasa_efectiva_anual,
            "tasa_moratoria_anual": obligacion.tasa_moratoria_anual,
            "fecha_vencimiento": obligacion.fecha_vencimiento,
            "ibc_vigente_anual": obligacion.ibc_vigente_anual,
        }
        for nombre_campo, valor in campos_requeridos.items():
            if valor is None:
                raise ValueError(
                    f"La obligacion comercial '{obligacion.concepto}' necesita el campo "
                    f"'{nombre_campo}' para liquidar."
                )

        validar_tasa_usura(obligacion.tasa_efectiva_anual, obligacion.ibc_vigente_anual, "remuneratoria")
        validar_tasa_usura(obligacion.tasa_moratoria_anual, obligacion.ibc_vigente_anual, "moratoria")

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
        provider = MemoryRateProvider()

        for obligacion in obligaciones:
            tasa_moratoria_diaria = EffectiveRateConverter.annual_to_daily(obligacion.tasa_moratoria_anual)

            if obligacion.tipo.value == "PUNTUAL":
                tasa_remuneratoria_diaria = EffectiveRateConverter.annual_to_daily(obligacion.tasa_efectiva_anual)
                inicio_remuneratorio = obligacion.fecha_origen - timedelta(days=1)
                fin_remuneratorio = min(obligacion.fecha_vencimiento, fecha_corte)
                provider.add_rate_period(
                    start=inicio_remuneratorio, end=fin_remuneratorio, rate=tasa_remuneratoria_diaria
                )
                if obligacion.fecha_vencimiento < fecha_corte:
                    inicio_moratorio = obligacion.fecha_vencimiento + timedelta(days=1)
                    provider.add_rate_period(
                        start=inicio_moratorio, end=fecha_corte, rate=tasa_moratoria_diaria
                    )
            else:
                # RECURRENTE: sin split por cuota individual (alcance reducido, ver spec).
                inicio = obligacion.fecha_inicio - timedelta(days=1)
                provider.add_rate_period(start=inicio, end=fecha_corte, rate=tasa_moratoria_diaria)

        return provider
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python -m pytest tests/services/test_area_strategy.py -v`
Expected: PASS (all cases, including the new `TestComercialStrategy` class)

- [ ] **Step 7: Run the full suite to check for regressions**

Run: `python -m pytest -q`
Expected: all tests pass (81 previous + the new ones from Tasks 1-4)

- [ ] **Step 8: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat(comercial): implement ComercialStrategy.liquidar() with remuneratorio/moratorio split and usury validation"
```

---

### Task 5: Enable Comercial in constants and capital concepts

**Files:**
- Modify: `app/core/constants.py`
- Modify: `app/engine/liquidation/engine.py:28-32`
- Test: `tests/services/test_area_strategy.py` (registry test), new test in `tests/engine/test_liquidation_core.py` or existing engine test file for `_capital_concepts`

- [ ] **Step 1: Write the failing test for the new capital concepts**

Check whether a test file already asserts on `_capital_concepts` contents:

Run: `python -m pytest tests -k capital_concepts -v`

If nothing is found (expected), add this test to `tests/services/test_area_strategy.py`:

```python
from app.engine.liquidation.engine import LiquidationCore


def test_capital_concepts_incluye_los_codigos_comerciales_nuevos():
    core = LiquidationCore()
    assert "CAPITAL_LETRA_CAMBIO" in core._capital_concepts
    assert "CAPITAL_CHEQUE" in core._capital_concepts
    assert "CAPITAL_FACTURA" in core._capital_concepts
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/services/test_area_strategy.py::test_capital_concepts_incluye_los_codigos_comerciales_nuevos -v`
Expected: FAIL — `AssertionError` (codes not in the set yet)

- [ ] **Step 3: Add the new capital concepts**

In `app/engine/liquidation/engine.py`, change the `_capital_concepts` set (line 28-32) from:

```python
        self._capital_concepts = {
            "INSTALLMENT", "CHILD_SUPPORT", "CLOTHING", "MULTA",
            "CESANTIAS", "INTERESES_CESANTIAS", "PRIMA_JUNIO", "PRIMA_DICIEMBRE", "SANCION_MORATORIA",
            "DANO_EMERGENTE", "LUCRO_CESANTE_CONSOLIDADO", "DANOS_MORALES", "CAPITAL_PAGARE"
        }
```

to:

```python
        self._capital_concepts = {
            "INSTALLMENT", "CHILD_SUPPORT", "CLOTHING", "MULTA",
            "CESANTIAS", "INTERESES_CESANTIAS", "PRIMA_JUNIO", "PRIMA_DICIEMBRE", "SANCION_MORATORIA",
            "DANO_EMERGENTE", "LUCRO_CESANTE_CONSOLIDADO", "DANOS_MORALES", "CAPITAL_PAGARE",
            "CAPITAL_LETRA_CAMBIO", "CAPITAL_CHEQUE", "CAPITAL_FACTURA"
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/services/test_area_strategy.py::test_capital_concepts_incluye_los_codigos_comerciales_nuevos -v`
Expected: PASS

- [ ] **Step 5: Add `CATEGORIAS_COMERCIAL` and enable the area**

In `app/core/constants.py`, add the new list after `CATEGORIAS_CIVIL_FAMILIA` (after line 14) and flip the Comercial tuple:

```python
CATEGORIAS_COMERCIAL = [
    ("CAPITAL_PAGARE", "Capital de pagare"),
    ("CAPITAL_LETRA_CAMBIO", "Capital de letra de cambio"),
    ("CAPITAL_CHEQUE", "Capital de cheque"),
    ("CAPITAL_FACTURA", "Capital de factura"),
]
# Nota: igual que CATEGORIAS_CIVIL_FAMILIA, cada codigo debe existir en
# app.engine.liquidation.engine.LiquidationCore._capital_concepts.

AREAS_DERECHO = [
    ("CIVIL_FAMILIA", "Civil / Familia", True),
    ("COMERCIAL", "Comercial", True),
    ("LABORAL", "Laboral", False),
    ("SANCIONATORIO", "Sancionatorio", False),
    ("HONORARIOS", "Honorarios / Litigio", False),
]
# El tercer valor de cada tupla indica si el area esta habilitada para calcular
# en este sprint. Ver Pendientes.md para el orden de habilitacion de las demas.
```

(Only the `AREAS_DERECHO` tuple for `"COMERCIAL"` changes its third value from `False` to `True`; `CATEGORIAS_COMERCIAL` is new.)

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest -q`
Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add app/core/constants.py app/engine/liquidation/engine.py tests/services/test_area_strategy.py
git commit -m "feat(comercial): enable Comercial area and add commercial capital concepts"
```

---

### Task 6: GUI — `ObligacionFormDialog` becomes area-aware

**Files:**
- Modify: `app/views/obligaciones.py`
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Write the failing test**

In `tests/views/test_obligaciones.py`, add `from decimal import Decimal` to the imports at the top (it's not currently imported there), and change `_expediente_de_prueba` to accept an area:

```python
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion
from app.views.obligaciones import ObligacionFormDialog


def _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-010",
        demandante="Ana",
        demandado="Luis",
        area_derecho=area,
        fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id
```

Then append this new test at the end of the file:

```python
def test_guarda_obligacion_comercial_con_tasa_moratoria_y_ibc(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Capital de pagare")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 1, 1))
    dialog.campo_tasa_moratoria.setText("24.00")
    dialog.campo_ibc_vigente.setText("20.00")
    dialog.campo_fecha_vencimiento.setDate(date(2025, 2, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.tasa_moratoria_anual == Decimal("24.00")
    assert guardada.ibc_vigente_anual == Decimal("20.00")
    assert guardada.fecha_vencimiento == date(2025, 2, 1)
    session.close()


def test_campos_comerciales_ocultos_para_area_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)

    assert dialog.campo_tasa_moratoria.isVisible() is False
    assert dialog.campo_fecha_vencimiento.isVisible() is False
    assert dialog.campo_ibc_vigente.isVisible() is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/views/test_obligaciones.py -v`
Expected: FAIL — `TypeError: ObligacionFormDialog.__init__() got an unexpected keyword argument 'area'`

- [ ] **Step 3: Make `ObligacionFormDialog` area-aware**

Replace the full contents of `app/views/obligaciones.py` with:

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
from app.core.constants import CATEGORIAS_CIVIL_FAMILIA, CATEGORIAS_COMERCIAL
from database.models import Obligacion, TipoObligacion


class ObligacionFormDialog(QDialog):
    def __init__(self, expediente_id: int, area: str = "CIVIL_FAMILIA", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar obligacion")
        self._expediente_id = expediente_id
        self._area = area

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("Puntual", userData="PUNTUAL")
        self.combo_tipo.addItem("Recurrente", userData="RECURRENTE")
        self.combo_tipo.currentIndexChanged.connect(self._actualizar_campos_visibles)

        self.combo_categoria = QComboBox()
        categorias = CATEGORIAS_COMERCIAL if self._area == "COMERCIAL" else CATEGORIAS_CIVIL_FAMILIA
        for codigo, etiqueta in categorias:
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

        self.campo_tasa_moratoria = QLineEdit("24.00")
        self.campo_fecha_vencimiento = QDateEdit(QDate.currentDate())
        self.campo_fecha_vencimiento.setCalendarPopup(True)
        self.campo_ibc_vigente = QLineEdit()

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
        self.layout_formulario.addRow("Tasa moratoria anual (%)", self.campo_tasa_moratoria)
        self.layout_formulario.addRow("Fecha de vencimiento", self.campo_fecha_vencimiento)
        self.layout_formulario.addRow("IBC vigente aplicable (%)", self.campo_ibc_vigente)
        self.layout_formulario.addRow(boton_guardar)
        self.setLayout(self.layout_formulario)

        es_comercial = self._area == "COMERCIAL"
        self.campo_tasa_moratoria.setVisible(es_comercial)
        self.campo_fecha_vencimiento.setVisible(es_comercial)
        self.campo_ibc_vigente.setVisible(es_comercial)

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

        tasa_moratoria = None
        fecha_vencimiento = None
        ibc_vigente = None
        if self._area == "COMERCIAL":
            try:
                tasa_moratoria = Decimal(self.campo_tasa_moratoria.text())
                ibc_vigente = Decimal(self.campo_ibc_vigente.text())
            except InvalidOperation as error:
                raise ValueError("Tasa moratoria e IBC vigente deben ser numeros validos.") from error
            qdate_vencimiento = self.campo_fecha_vencimiento.date()
            fecha_vencimiento = date(
                qdate_vencimiento.year(), qdate_vencimiento.month(), qdate_vencimiento.day()
            )

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
            tasa_moratoria_anual=tasa_moratoria,
            fecha_vencimiento=fecha_vencimiento,
            ibc_vigente_anual=ibc_vigente,
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

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/views/test_obligaciones.py -v`
Expected: PASS (all 5 tests: the 3 original + the 2 new ones)

- [ ] **Step 5: Run the full suite**

Run: `python -m pytest -q`
Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "feat(gui): make ObligacionFormDialog area-aware for Comercial fields"
```

---

### Task 7: GUI — wire the area through and handle `TasaUsurariaError`

**Files:**
- Modify: `app/views/expediente_detalle.py`
- Test: `tests/views/test_expediente_detalle.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/views/test_expediente_detalle.py`:

```python
from app.core.exceptions import TasaUsurariaError


def _expediente_comercial_con_obligacion_usuraria(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-040",
        demandante="Comercial SAS",
        demandado="Deudor SAS",
        area_derecho=AreaDerecho.COMERCIAL,
        fecha_corte_default=date(2025, 3, 1),
    )
    session.add(expediente)
    session.flush()
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Capital de pagare",
            categoria="CAPITAL_PAGARE",
            fecha_origen=date(2025, 1, 1),
            valor=Decimal("1000000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
            tasa_moratoria_anual=Decimal("35.00"),
            fecha_vencimiento=date(2025, 2, 1),
            ibc_vigente_anual=Decimal("20.00"),
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_liquidar_area_comercial_con_tasa_usuraria_muestra_advertencia(qtbot, monkeypatch):
    expediente_id = _expediente_comercial_con_obligacion_usuraria(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    page._liquidar()

    assert len(resultados_recibidos) == 0
    assert len(avisos) == 1
    assert avisos[0][0] == "Tasa usuraria"


def test_abrir_dialogo_obligacion_pasa_el_area_del_expediente(qtbot, monkeypatch):
    expediente_id = _expediente_comercial_con_obligacion_usuraria(monkeypatch)

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    dialogos_creados = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.ObligacionFormDialog",
        lambda expediente_id, area, parent: dialogos_creados.append(area) or _DialogStub(),
    )

    page._abrir_dialogo_obligacion()

    assert dialogos_creados == ["COMERCIAL"]


class _DialogStub:
    def exec(self):
        return False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/views/test_expediente_detalle.py -v`
Expected: FAIL — `test_liquidar_area_comercial_con_tasa_usuraria_muestra_advertencia` fails because `TasaUsurariaError` propagates uncaught out of `_liquidar()`; `test_abrir_dialogo_obligacion_pasa_el_area_del_expediente` fails because `ObligacionFormDialog` is called with only `expediente_id`/`parent`, not `area`.

- [ ] **Step 3: Update `ExpedienteDetallePage`**

In `app/views/expediente_detalle.py`, update the import line (line 13) from:

```python
from app.core.exceptions import AreaNoImplementadaError
```

to:

```python
from app.core.exceptions import AreaNoImplementadaError, TasaUsurariaError
```

Replace `_abrir_dialogo_obligacion` (lines 92-95) with:

```python
    def _abrir_dialogo_obligacion(self) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)
        area = expediente.area_derecho.value
        session.close()

        dialogo = ObligacionFormDialog(expediente_id=self._expediente_id, area=area, parent=self)
        if dialogo.exec():
            self._refrescar_obligaciones()
```

Replace `_liquidar` (lines 108-129) with:

```python
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
        except TasaUsurariaError as error:
            QMessageBox.warning(self, "Tasa usuraria", str(error))
            return
        except ValueError as error:
            QMessageBox.warning(self, "No se pudo liquidar", str(error))
            return

        if self._on_liquidado:
            self._on_liquidado(resultado, self._expediente_id)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/views/test_expediente_detalle.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Run the full suite**

Run: `python -m pytest -q`
Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add app/views/expediente_detalle.py tests/views/test_expediente_detalle.py
git commit -m "feat(gui): pass expediente area to ObligacionFormDialog and handle TasaUsurariaError"
```

---

### Task 8: Documentation — README, Guía de Usuario, Pendientes.md

**Files:**
- Modify: `README.md`
- Modify: `docs/GUIA_USUARIO.md`
- Modify: `Pendientes.md`

- [ ] **Step 1: Update `README.md`**

Replace the "Estado actual" section (lines 12-21) from:

```markdown
## Estado actual (2026-07-15)

✅ **Funcional hoy:** captura manual de expedientes y liquidación real del área **Civil / Familia**
(interés del Art. 1617 del Código Civil, 6% anual, sobre obligaciones puntuales y recurrentes, con
abonos).

🚧 **En desarrollo:** las áreas Comercial, Laboral, Sancionatorio y Honorarios están registradas en el
sistema pero todavía no calculan (el programa avisa "Área no implementada" si se intentan usar).
Indexación por IPC, exportación a PDF/Word, prescripción/caducidad y varios módulos más también están
pendientes. El plan completo, sprint por sprint, está en **[Pendientes.md](Pendientes.md)**.
```

to:

```markdown
## Estado actual (2026-07-15)

✅ **Funcional hoy:** captura manual de expedientes y liquidación real de las áreas **Civil / Familia**
(interés del Art. 1617 del Código Civil, 6% anual, sobre obligaciones puntuales y recurrentes, con
abonos) y **Comercial** (Art. 884 C.Co., tasas remuneratoria y moratoria pactadas por obligación con
split real antes/después del vencimiento, validación de tope de usura 1.5×IBC).

🚧 **En desarrollo:** las áreas Laboral, Sancionatorio y Honorarios están registradas en el sistema pero
todavía no calculan (el programa avisa "Área no implementada" si se intentan usar). Indexación por IPC,
exportación a PDF/Word, prescripción/caducidad, anatocismo comercial condicionado (Art. 886 C.Co.) y
varios módulos más también están pendientes. El plan completo, sprint por sprint, está en
**[Pendientes.md](Pendientes.md)**.
```

- [ ] **Step 2: Update `docs/GUIA_USUARIO.md` — header note**

Change line 8 from:

```markdown
> **Última actualización:** 2026-07-15 — refleja el estado del MVP de Civil/Familia. Cada vez que se
```

to:

```markdown
> **Última actualización:** 2026-07-15 — refleja el estado de Civil/Familia y Comercial. Cada vez que se
```

- [ ] **Step 3: Update `docs/GUIA_USUARIO.md` — section 6 (áreas del derecho)**

Replace the table at lines 253-259 from:

```markdown
| Área | ¿Funciona? |
|---|---|
| Civil / Familia | ✅ Sí — interés del Art. 1617 C.C. (6% anual o la tasa que se pacte), sobre obligaciones puntuales y recurrentes, con abonos. |
| Comercial | 🚧 No todavía — aparece "gris" en el formulario, no se puede seleccionar. Planeado en `Pendientes.md`, Sprint 2. |
| Laboral | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 3. |
| Sancionatorio | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 4. |
| Honorarios / Litigio | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 4. |
```

to:

```markdown
| Área | ¿Funciona? |
|---|---|
| Civil / Familia | ✅ Sí — interés del Art. 1617 C.C. (6% anual o la tasa que se pacte), sobre obligaciones puntuales y recurrentes, con abonos. |
| Comercial | ✅ Sí — Art. 884 C.Co., tasa remuneratoria antes del vencimiento y tasa moratoria después, validación de tope de usura (1.5× el IBC que ingreses). Ver [sección 5.7](#57-agregar-una-obligación-comercial). |
| Laboral | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 3. |
| Sancionatorio | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 4. |
| Honorarios / Litigio | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 4. |
```

- [ ] **Step 4: Add a new section 5.7 documenting the Comercial obligation form**

In `docs/GUIA_USUARIO.md`, insert a new subsection right after section 5.4 ("Agregar una obligación recurrente", which currently ends at line 215, right before section 5.5 at line 217):

```markdown
### 5.7. Agregar una obligación comercial

Cuando el expediente tiene **Área del derecho = Comercial**, el formulario de "Agregar obligación"
muestra tres campos adicionales, específicos de esta área:

1. Dentro del Detalle de un expediente Comercial, haz clic en **"Agregar obligación"**.
2. Llena los campos comunes (Tipo, Categoría, Concepto, Valor, Tasa efectiva anual, Fecha de origen)
   igual que en Civil/Familia — ver [sección 5.3](#53-agregar-una-obligación-puntual-una-deuda-de-una-sola-vez).
   La "Tasa efectiva anual (%)" aquí representa la **tasa remuneratoria** pactada.
3. Llena además:
   - **Tasa moratoria anual (%)**: la tasa que aplica después de que la obligación vence y no se paga.
     Si no se pactó una distinta, la ley comercial (Art. 884 C.Co.) sugiere 1.5× el IBC vigente, pero el
     campo siempre se diligencia manualmente — no hay cálculo automático todavía (ver `Pendientes.md`,
     Sprint 5).
   - **Fecha de vencimiento**: la fecha en que la obligación se hace exigible. Antes de esta fecha se
     usa la tasa remuneratoria; después, la moratoria.
   - **IBC vigente aplicable (%)**: el Interés Bancario Corriente certificado por la Superintendencia
     Financiera para la fecha del caso. Se usa únicamente para validar que ninguna de las dos tasas
     pactadas supere el tope legal de usura (1.5× este valor).
4. Haz clic en **"Guardar"**.

Si alguna tasa pactada (remuneratoria o moratoria) supera 1.5× el IBC que ingresaste, el programa no
deja liquidar el expediente y muestra el mensaje "Tasa usuraria" al hacer clic en "Liquidar" — no al
guardar la obligación (la validación ocurre al calcular, no al capturar el dato).
```

- [ ] **Step 5: Update `docs/GUIA_USUARIO.md` — section 7 (valores legales), add a Comercial subsection**

Insert a new subsection after 7.1 (which ends at line 281, right before section 7.2 at line 283):

```markdown
### 7.1.1. Tope de usura comercial (1.5x IBC, Ley 45/1990 art. 72)

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente Comercial,
  el campo **"IBC vigente aplicable (%)"** — lo diligencias tú con el IBC certificado por la
  Superfinanciera para la fecha del caso, no hay un valor por defecto.
- **Dónde vive la lógica en el código**: `app/engine/interest/usury_validator.py`, función
  `validar_tasa_usura`. Se invoca automáticamente al liquidar (`ComercialStrategy.liquidar()` en
  `app/services/area_strategy.py`), tanto para la tasa remuneratoria como para la moratoria.
- **Qué pasa si se excede el tope**: el programa lanza el error "Tasa usuraria" y no calcula nada —
  nunca trunca la tasa silenciosamente.
```

- [ ] **Step 6: Update `docs/GUIA_USUARIO.md` — section 8 (pendientes) and section 9 (FAQ)**

Change the first bullet of section 8 (lines 315-316) from:

```markdown
- 🚧 **Cálculo en las áreas Comercial, Laboral, Sancionatorio y Honorarios** — hoy solo funciona Civil/
  Familia (`Pendientes.md`, Sprints 2, 3 y 4).
```

to:

```markdown
- 🚧 **Cálculo en las áreas Laboral, Sancionatorio y Honorarios** — hoy funcionan Civil/Familia y
  Comercial (`Pendientes.md`, Sprints 3 y 4).
- 🚧 **Anatocismo comercial condicionado (Art. 886 C.Co.)** — el motor de interés compuesto
  (`CompoundInterest`) existe pero no está conectado; requiere modelar si hubo demanda judicial o
  acuerdo posterior de capitalización, algo que el modelo de datos todavía no captura (`Pendientes.md`,
  Sprint 2, nota de alcance diferido).
```

Change the FAQ entry at lines 343-345 from:

```markdown
**"Seleccioné Comercial/Laboral/Sancionatorio/Honorarios y no me deja."**
Es esperado — esas áreas todavía no calculan, por eso aparecen deshabilitadas en el formulario. Ver
[sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy).
```

to:

```markdown
**"Seleccioné Laboral/Sancionatorio/Honorarios y no me deja."**
Es esperado — esas áreas todavía no calculan, por eso aparecen deshabilitadas en el formulario. Comercial
sí está habilitada. Ver [sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy).
```

- [ ] **Step 7: Update `Pendientes.md`**

In the "Sprint 2 — Área Comercial" section, replace the `**Riesgos / notas técnicas conocidas:**` block
(currently the bullet starting "El PDF advierte explícitamente..." followed by the IBC/usura data bullet)
by appending a closing note right after it, before the `**Definición de Hecho:**` heading:

```markdown
**Estado:** Implementado (2026-07-15) — ver `docs/superpowers/plans/2026-07-15-area-comercial.md` y
`docs/superpowers/specs/2026-07-15-area-comercial-design.md`. Pendiente explícito que quedó fuera de
este sprint (decisión tomada con el usuario, no un olvido): el anatocismo condicionado del Art. 886
C.Co. — `CompoundInterest` (`app/engine/interest/compound_interest.py`) sigue huérfano porque requiere
modelar si hubo demanda judicial o acuerdo posterior de capitalización, campos que no existen hoy en
`Obligacion`. También queda documentado como limitación conocida (heredada de Civil, no introducida
aquí): `MemoryRateProvider` da resultados correctos por obligación solo cuando el expediente tiene una
obligación comercial o cuando los tramos de fecha de las obligaciones no se solapan con tasas distintas.
```

- [ ] **Step 8: Commit**

```bash
git add README.md docs/GUIA_USUARIO.md Pendientes.md
git commit -m "docs: document Área Comercial in README, Guía de Usuario, and Pendientes.md"
```

---

### Task 9: Full verification pass

**Files:** none (verification only)

- [ ] **Step 1: Run the full automated suite**

Run: `python -m pytest -q`
Expected: all tests pass, no failures (81 original + all tests added in Tasks 1-8)

- [ ] **Step 2: Manual smoke test — happy path**

```bash
python main.py
```

1. Click "Nuevo expediente". Fill Radicado `2026-050`, Demandante `Comercial SAS`, Demandado `Deudor SAS`,
   **Área del derecho = Comercial** (should now be selectable, not greyed out), Fecha de corte
   `2025-03-01`. Save.
2. Double-click the new expediente to open its detail page.
3. Click "Agregar obligación". Confirm the three new fields (Tasa moratoria anual, Fecha de vencimiento,
   IBC vigente aplicable) are visible. Fill: Tipo = Puntual, Categoría = "Capital de pagare", Concepto =
   "Pagare #1", Valor = `1000000.00`, Tasa efectiva anual = `6.00`, Fecha de origen = `2025-01-01`, Tasa
   moratoria anual = `24.00`, Fecha de vencimiento = `2025-02-01`, IBC vigente aplicable = `20.00`. Save.
4. Click "Agregar abono" (select the obligación row first). Fecha = `2025-02-15`, Monto = `200000.00`.
   Save.
5. Click "Liquidar". Confirm the Resultado de Liquidación screen opens without error, with a saldo final
   below `1000000.00`.

Expected: no crash, no "Área no implementada" message, saldo final lower than the original valor.

- [ ] **Step 3: Manual smoke test — usury rejection**

Repeat steps 1-3 above for a second expediente, but set Tasa moratoria anual = `35.00` and IBC vigente
aplicable = `20.00` (35 > 1.5×20 = 30). Click "Liquidar".

Expected: a "Tasa usuraria" warning dialog appears instead of a liquidation result; the program does not
crash.

- [ ] **Step 4: Confirm docs match reality**

Re-read `README.md` "Estado actual" and `docs/GUIA_USUARIO.md` section 6 — confirm both describe Comercial
as functional, matching what was just verified manually.

- [ ] **Step 5: Final commit (only if any fixups were needed in steps 1-4)**

If everything passed with no code changes, there is nothing to commit here — Task 8's commit already
covers the documentation. If the manual smoke test surfaced a bug, fix it, add a regression test in the
relevant file from Tasks 4/6/7, rerun `python -m pytest -q`, and commit with a `fix:` message describing
the bug found during smoke testing.

---

## Post-plan reminder

This plan does not implement:
- Anatocismo condicionado (Art. 886 C.Co.) — deferred, see Task 8 Step 7's note in `Pendientes.md`.
- Per-cuota remuneratorio/moratorio split for `RECURRENTE` obligaciones — narrower scope, see Task 4's
  docstring on `ComercialStrategy`.
- Multi-obligación expedientes with overlapping, differently-rated timelines — inherited
  `MemoryRateProvider` limitation, not solved by this sprint (same as Civil today).

These are intentional scope boundaries agreed with the user during brainstorming, not omissions.
