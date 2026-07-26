# Área Laboral (Sprint 3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `LaboralStrategy.liquidar()` so the "Laboral" area calculates real liquidations — a finiquito (final settlement) of one labor contract: cesantías, intereses a cesantías, prima (junio/diciembre), vacaciones, and the bi-phasic Art. 65 CST moratory indemnity — and enable it end-to-end in the GUI.

**Architecture:** `LaborScheduler` is rewritten so all five prestaciones are dated at the contract's termination date (finiquito model) instead of fixed calendar dates. A new `MoratoryIndemnityCalculator` computes the Art. 65 CST bi-phasic indemnity as a pure function and gets injected into the event list as a single `SANCION_MORATORIA` capital event. `LaboralStrategy` wires both into `UniversalLiquidationService`, with no `rate_provider` (all mora is already resolved by the calculator — a generic daily rate would double-count it). No schema migration: reuses existing `Obligacion` columns (`valor`, `fecha_inicio`, `fecha_fin`, `pagada`, `fecha_pago_total`) that today no code reads or writes.

**Tech Stack:** Python 3.14, SQLAlchemy (declarative models, SQLite), PySide6 (GUI), pytest + pytest-qt.

**Design doc:** `docs/superpowers/specs/2026-07-18-area-laboral-design.md` — read it first if anything below is unclear; it has the full rationale, including why the "bug" `Pendientes.md` flagged in `INTERESES_CESANTIAS` turned out not to be a bug, and why seguridad social is out of scope.

---

### Task 1: `LaborScheduler` — finiquito model + Vacaciones

`app/engine/temporal/schedulers/labor.py` currently generates 4 prestaciones (Cesantías, Intereses/Cesantías, Prima Junio, Prima Diciembre) at fixed calendar dates (14-feb, 31-ene, 30-jun, 20-dic of a given `anio`) — a model for an ongoing contract, not a final settlement. This task replaces it with a finiquito model: all events dated at `fecha_liquidacion`, plus a new `VACACIONES` event (divisor 720).

**Files:**
- Modify: `app/engine/temporal/schedulers/labor.py`
- Modify: `app/engine/liquidation/engine.py:28-33` (register `VACACIONES` as a capital concept)
- Test: `tests/temporal/test_labor.py`
- Test: `tests/services/test_area_strategy.py` (capital concepts test)

- [ ] **Step 1: Write the failing tests for the new `LaborScheduler`**

Replace the full contents of `tests/temporal/test_labor.py`:

```python
from datetime import date
from decimal import Decimal
from app.engine.temporal.schedulers.labor import LaborScheduler


def test_labor_scheduler_liquidacion_final_contrato_de_un_anio_completo():
    # Escenario: contrato de un año completo (360 dias trabajados en la
    # convencion comercial), terminado el 2025-12-31. En el modelo de
    # finiquito, TODAS las prestaciones son exigibles ese mismo dia.
    salario = Decimal("1500000.00")
    dias_trabajados = 360
    fecha_liquidacion = date(2025, 12, 31)

    scheduler = LaborScheduler(
        salario_base=salario, dias_trabajados=dias_trabajados, fecha_liquidacion=fecha_liquidacion
    )
    events = scheduler.generate()

    assert len(events) == 5
    assert all(e.date == fecha_liquidacion for e in events)

    cesantias = next(e for e in events if e.event_type == "CESANTIAS")
    assert cesantias.payload["amount"] == Decimal("1500000.00")

    int_cesantias = next(e for e in events if e.event_type == "INTERESES_CESANTIAS")
    assert int_cesantias.payload["amount"] == Decimal("180000.00")  # 1.5M * 12%

    prima_junio = next(e for e in events if e.event_type == "PRIMA_JUNIO")
    assert prima_junio.payload["amount"] == Decimal("750000.00")

    prima_dic = next(e for e in events if e.event_type == "PRIMA_DICIEMBRE")
    assert prima_dic.payload["amount"] == Decimal("750000.00")

    vacaciones = next(e for e in events if e.event_type == "VACACIONES")
    assert vacaciones.payload["amount"] == Decimal("750000.00")  # (1.5M*360)/720


def test_labor_scheduler_dias_proporcionales():
    # Escenario: trabajo parcial de 180 dias, contrato terminado el 2025-07-15.
    scheduler = LaborScheduler(
        salario_base=Decimal("1000000.00"), dias_trabajados=180, fecha_liquidacion=date(2025, 7, 15)
    )
    events = scheduler.generate()

    assert all(e.date == date(2025, 7, 15) for e in events)

    cesantias = next(e for e in events if e.event_type == "CESANTIAS")
    assert cesantias.payload["amount"] == Decimal("500000.00")  # (1M*180)/360

    vacaciones = next(e for e in events if e.event_type == "VACACIONES")
    assert vacaciones.payload["amount"] == Decimal("250000.00")  # (1M*180)/720
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/temporal/test_labor.py -v`
Expected: FAIL — `TypeError: LaborScheduler.__init__() missing 1 required positional argument: 'fecha_liquidacion'` (the current constructor takes `anio`, not `fecha_liquidacion`).

- [ ] **Step 3: Rewrite `LaborScheduler`**

Replace the full contents of `app/engine/temporal/schedulers/labor.py`:

```python
from datetime import date
from decimal import Decimal
from typing import List
from app.engine.temporal.schedulers.base import Scheduler, Event
from app.engine.math.rounding import Rounding

class LaborScheduler(Scheduler):
    """
    Generador de las prestaciones sociales estatutarias de un contrato laboral
    colombiano, en el modelo de liquidacion final (finiquito): las cinco
    prestaciones (Cesantias, Intereses/Cesantias, Prima Junio, Prima
    Diciembre, Vacaciones) se vuelven exigibles TODAS en la fecha de
    terminacion del contrato (Art. 65 CST), no en las fechas de calendario
    que aplicarian a un contrato vigente (14-feb, 31-ene, 30-jun, 20-dic).
    """

    def __init__(self, salario_base: Decimal, dias_trabajados: int, fecha_liquidacion: date):
        self.salario = salario_base
        self.dias = Decimal(str(dias_trabajados))
        self.fecha_liquidacion = fecha_liquidacion
        self.base_anual = Decimal("360")

    def generate(self, start: date = None, end: date = None) -> List[Event]:
        events = []

        # 1. Cesantias: 30 dias de salario por año laborado o proporcional.
        monto_cesantias = Rounding.money((self.salario * self.dias) / self.base_anual)
        events.append(Event(
            date=self.fecha_liquidacion,
            payload={"amount": monto_cesantias},
            event_type="CESANTIAS"
        ))

        # 2. Intereses a las cesantias: 12% anual sobre el saldo de cesantias,
        # prorrateado por los dias trabajados (formula verificada contra
        # REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf, pag. 51:
        # (Cesantias x 0.12 x dias) / 360 -- no habia bug aqui, Pendientes.md
        # sospechaba uno pero la propia cita del PDF ya coincidia con esto).
        monto_intereses = Rounding.money((monto_cesantias * self.dias * Decimal("0.12")) / self.base_anual)
        events.append(Event(
            date=self.fecha_liquidacion,
            payload={"amount": monto_intereses},
            event_type="INTERESES_CESANTIAS"
        ))

        # 3. Prima de servicios: 15 dias por semestre (junio y diciembre).
        dias_semestre = self.dias / Decimal("2")
        monto_prima_semestral = Rounding.money((self.salario * dias_semestre) / self.base_anual)

        if self.dias > Decimal("0.00"):
            events.append(Event(
                date=self.fecha_liquidacion,
                payload={"amount": monto_prima_semestral},
                event_type="PRIMA_JUNIO"
            ))
            events.append(Event(
                date=self.fecha_liquidacion,
                payload={"amount": monto_prima_semestral},
                event_type="PRIMA_DICIEMBRE"
            ))

        # 4. Vacaciones: descanso remunerado, NO es tecnicamente una
        # prestacion social, por eso su divisor es 720 (el doble del año
        # comercial de 360).
        monto_vacaciones = Rounding.money((self.salario * self.dias) / Decimal("720"))
        events.append(Event(
            date=self.fecha_liquidacion,
            payload={"amount": monto_vacaciones},
            event_type="VACACIONES"
        ))

        return sorted(events, key=lambda e: e.date)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/temporal/test_labor.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Write the failing test for the new `VACACIONES` capital concept**

Append to `tests/services/test_area_strategy.py` (near the existing `test_capital_concepts_incluye_los_codigos_comerciales_nuevos`):

```python
def test_capital_concepts_incluye_vacaciones():
    core = LiquidationCore()
    assert "VACACIONES" in core._capital_concepts
```

- [ ] **Step 6: Run the test to verify it fails**

Run: `python -m pytest tests/services/test_area_strategy.py::test_capital_concepts_incluye_vacaciones -v`
Expected: FAIL — `AssertionError` (`"VACACIONES"` not in the set yet).

- [ ] **Step 7: Register `VACACIONES` as a capital concept**

In `app/engine/liquidation/engine.py`, change the `_capital_concepts` set (lines 28-33) from:

```python
        self._capital_concepts = {
            "INSTALLMENT", "CHILD_SUPPORT", "CLOTHING", "MULTA",
            "CESANTIAS", "INTERESES_CESANTIAS", "PRIMA_JUNIO", "PRIMA_DICIEMBRE", "SANCION_MORATORIA",
            "DANO_EMERGENTE", "LUCRO_CESANTE_CONSOLIDADO", "DANOS_MORALES", "CAPITAL_PAGARE",
            "CAPITAL_LETRA_CAMBIO", "CAPITAL_CHEQUE", "CAPITAL_FACTURA"
        }
```

to:

```python
        self._capital_concepts = {
            "INSTALLMENT", "CHILD_SUPPORT", "CLOTHING", "MULTA",
            "CESANTIAS", "INTERESES_CESANTIAS", "PRIMA_JUNIO", "PRIMA_DICIEMBRE", "SANCION_MORATORIA",
            "DANO_EMERGENTE", "LUCRO_CESANTE_CONSOLIDADO", "DANOS_MORALES", "CAPITAL_PAGARE",
            "CAPITAL_LETRA_CAMBIO", "CAPITAL_CHEQUE", "CAPITAL_FACTURA", "VACACIONES"
        }
```

- [ ] **Step 8: Run the test to verify it passes**

Run: `python -m pytest tests/services/test_area_strategy.py::test_capital_concepts_incluye_vacaciones -v`
Expected: PASS

- [ ] **Step 9: Run the full suite to check for regressions**

Run: `python -m pytest -q`
Expected: all tests pass (no other test references the old `LaborScheduler(anio=...)` constructor — confirmed by `grep -rn "LaborScheduler" tests/ app/` before this task returning only `tests/temporal/test_labor.py`).

- [ ] **Step 10: Commit**

```bash
git add app/engine/temporal/schedulers/labor.py app/engine/liquidation/engine.py tests/temporal/test_labor.py tests/services/test_area_strategy.py
git commit -m "feat(labor): rewrite LaborScheduler as finiquito model, add Vacaciones"
```

---

### Task 2: `MoratoryIndemnityCalculator` — Art. 65 CST bi-phasic indemnity

New module computing the moratory indemnity as a pure function: Phase 1 (day 1-720, one day's salary per day of delay) and Phase 2 (day 721+, daily interest at the historical usura rate on the amount owed).

**Files:**
- Create: `app/engine/labor/__init__.py`
- Create: `app/engine/labor/moratory_indemnity.py`
- Create: `tests/engine/labor/__init__.py`
- Create: `tests/engine/labor/test_moratory_indemnity.py`

- [ ] **Step 1: Create the new packages**

Create `app/engine/labor/__init__.py` (empty file) and `tests/engine/labor/__init__.py` (empty file). Every existing package in this repo (`app/engine/interest/`, `tests/engine/`, etc.) has an empty `__init__.py` — `pytest.ini` uses `consider_namespace_packages = true` specifically to avoid import collisions, so this must not be skipped.

- [ ] **Step 2: Write the failing tests**

Create `tests/engine/labor/test_moratory_indemnity.py`:

```python
from datetime import date, timedelta
from decimal import Decimal

from app.engine.indexation.historical_index import get_ibc_usura_for_date
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.engine.labor.moratory_indemnity import MoratoryIndemnityCalculator


def test_pagado_a_tiempo_no_genera_indemnizacion():
    resultado = MoratoryIndemnityCalculator.calcular(
        salario_mensual=Decimal("3000000.00"),
        monto_adeudado=Decimal("5000000.00"),
        fecha_terminacion=date(2020, 1, 10),
        fecha_pago_o_corte=date(2020, 1, 5),  # antes de terminar el contrato
    )
    assert resultado.total == Decimal("0.00")
    assert resultado.dias_retardo == 0
    assert resultado.dias_fase1 == 0
    assert resultado.dias_fase2 == 0


def test_pago_exactamente_dia_720_solo_fase1():
    fecha_terminacion = date(2018, 1, 1)
    fecha_pago = fecha_terminacion + timedelta(days=720)

    resultado = MoratoryIndemnityCalculator.calcular(
        salario_mensual=Decimal("3000000.00"),
        monto_adeudado=Decimal("5000000.00"),
        fecha_terminacion=fecha_terminacion,
        fecha_pago_o_corte=fecha_pago,
    )

    assert resultado.dias_retardo == 720
    assert resultado.dias_fase1 == 720
    assert resultado.monto_fase1 == Decimal("72000000.00")  # (3M/30) * 720
    assert resultado.dias_fase2 == 0
    assert resultado.monto_fase2 == Decimal("0.00")
    assert resultado.total == Decimal("72000000.00")


def test_pago_dia_721_entra_un_dia_en_fase2():
    fecha_terminacion = date(2018, 1, 1)
    fecha_pago = fecha_terminacion + timedelta(days=721)

    resultado = MoratoryIndemnityCalculator.calcular(
        salario_mensual=Decimal("3000000.00"),
        monto_adeudado=Decimal("5000000.00"),
        fecha_terminacion=fecha_terminacion,
        fecha_pago_o_corte=fecha_pago,
    )

    assert resultado.dias_fase1 == 720
    assert resultado.monto_fase1 == Decimal("72000000.00")
    assert resultado.dias_fase2 == 1

    dia_calculo = fecha_terminacion + timedelta(days=721)
    _, usura = get_ibc_usura_for_date(dia_calculo)
    tasa_diaria = EffectiveRateConverter.annual_to_daily(usura)
    esperado_fase2 = DailyInterest.calculate(Decimal("5000000.00"), tasa_diaria, 1)

    assert resultado.monto_fase2 == esperado_fase2
    assert resultado.total == resultado.monto_fase1 + esperado_fase2


def test_fase2_cruza_tramos_de_usura_distintos():
    # fecha_terminacion elegida para que el dia 721 caiga en 2018-01-31 y el
    # dia 722 en 2018-02-01 -- dos tramos de usura distintos en
    # historical_index (verificado: 31.04% vs 31.52% EA).
    fecha_terminacion = date(2016, 2, 10)
    fecha_pago = fecha_terminacion + timedelta(days=722)

    resultado = MoratoryIndemnityCalculator.calcular(
        salario_mensual=Decimal("3000000.00"),
        monto_adeudado=Decimal("5000000.00"),
        fecha_terminacion=fecha_terminacion,
        fecha_pago_o_corte=fecha_pago,
    )

    assert resultado.dias_fase2 == 2

    dia1 = fecha_terminacion + timedelta(days=721)
    dia2 = fecha_terminacion + timedelta(days=722)
    assert dia1 == date(2018, 1, 31)
    assert dia2 == date(2018, 2, 1)

    _, usura_dia1 = get_ibc_usura_for_date(dia1)
    _, usura_dia2 = get_ibc_usura_for_date(dia2)
    assert usura_dia1 != usura_dia2  # confirma que el tramo realmente cambia

    esperado_dia1 = DailyInterest.calculate(
        Decimal("5000000.00"), EffectiveRateConverter.annual_to_daily(usura_dia1), 1
    )
    esperado_dia2 = DailyInterest.calculate(
        Decimal("5000000.00"), EffectiveRateConverter.annual_to_daily(usura_dia2), 1
    )
    assert resultado.monto_fase2 == esperado_dia1 + esperado_dia2
    assert resultado.total == resultado.monto_fase1 + resultado.monto_fase2
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m pytest tests/engine/labor/test_moratory_indemnity.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.engine.labor.moratory_indemnity'`

- [ ] **Step 4: Implement `MoratoryIndemnityCalculator`**

Create `app/engine/labor/moratory_indemnity.py`:

```python
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from app.engine.indexation.historical_index import get_ibc_usura_for_date
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.engine.math.rounding import Rounding


@dataclass(frozen=True)
class MoratoryIndemnityResult:
    dias_retardo: int
    dias_fase1: int
    monto_fase1: Decimal
    dias_fase2: int
    monto_fase2: Decimal
    total: Decimal


class MoratoryIndemnityCalculator:
    """
    Indemnizacion moratoria del Art. 65 CST ("salarios caidos"), regimen
    bifasico:
      - Fase 1 (dia 1 a 720, 24 meses): un dia de salario por cada dia de
        retardo.
      - Fase 2 (dia 721 en adelante): cesa el dia de salario; corren
        intereses moratorios a la tasa maxima legal (SFC, tasa de usura)
        sobre los salarios y cesantias adeudadas.
    Verificado contra REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf,
    paginas 51 y 3427-3433.
    """

    LIMITE_FASE1_DIAS = 720

    @staticmethod
    def calcular(
        salario_mensual: Decimal,
        monto_adeudado: Decimal,
        fecha_terminacion: date,
        fecha_pago_o_corte: date,
    ) -> "MoratoryIndemnityResult":
        dias_retardo = (fecha_pago_o_corte - fecha_terminacion).days
        if dias_retardo <= 0:
            return MoratoryIndemnityResult(
                dias_retardo=0,
                dias_fase1=0,
                monto_fase1=Decimal("0.00"),
                dias_fase2=0,
                monto_fase2=Decimal("0.00"),
                total=Decimal("0.00"),
            )

        dias_fase1 = min(dias_retardo, MoratoryIndemnityCalculator.LIMITE_FASE1_DIAS)
        salario_diario = salario_mensual / Decimal("30")
        monto_fase1 = Rounding.money(salario_diario * Decimal(str(dias_fase1)))

        dias_fase2 = max(dias_retardo - MoratoryIndemnityCalculator.LIMITE_FASE1_DIAS, 0)
        monto_fase2 = Decimal("0.00")
        if dias_fase2 > 0:
            primer_dia_fase2 = fecha_terminacion + timedelta(
                days=MoratoryIndemnityCalculator.LIMITE_FASE1_DIAS + 1
            )
            for offset in range(dias_fase2):
                dia = primer_dia_fase2 + timedelta(days=offset)
                _, usura_anual = get_ibc_usura_for_date(dia)
                tasa_diaria = EffectiveRateConverter.annual_to_daily(usura_anual)
                monto_fase2 += DailyInterest.calculate(monto_adeudado, tasa_diaria, 1)

        return MoratoryIndemnityResult(
            dias_retardo=dias_retardo,
            dias_fase1=dias_fase1,
            monto_fase1=monto_fase1,
            dias_fase2=dias_fase2,
            monto_fase2=monto_fase2,
            total=monto_fase1 + monto_fase2,
        )
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/engine/labor/test_moratory_indemnity.py -v`
Expected: PASS (4 passed)

- [ ] **Step 6: Run the full suite**

Run: `python -m pytest -q`
Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add app/engine/labor/ tests/engine/labor/
git commit -m "feat(labor): add MoratoryIndemnityCalculator for Art. 65 CST bi-phasic indemnity"
```

---

### Task 3: `LaboralStrategy.liquidar()`

`app/services/area_strategy.py` currently has `LaboralStrategy` as a stub (lines 223-227) that always raises `AreaNoImplementadaError`. This task replaces it with a real implementation wiring `LaborScheduler` + `MoratoryIndemnityCalculator`.

**Files:**
- Modify: `app/services/area_strategy.py`
- Modify: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Remove Laboral from the "not implemented" parametrize list**

In `tests/services/test_area_strategy.py`, change:

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

to:

```python
@pytest.mark.parametrize(
    "area_name,strategy_cls",
    [
        ("SANCIONATORIO", SancionatorioStrategy),
        ("HONORARIOS", HonorariosStrategy),
    ],
)
```

- [ ] **Step 2: Run the full test file to confirm it's currently green**

Run: `python -m pytest tests/services/test_area_strategy.py -v`
Expected: PASS (all existing tests still pass; `LaboralStrategy` isn't tested for "not implemented" anymore, and nothing tests its real behavior yet).

- [ ] **Step 3: Write the failing tests for `LaboralStrategy`**

Append to `tests/services/test_area_strategy.py`:

```python
from app.engine.labor.moratory_indemnity import MoratoryIndemnityCalculator


def _obligacion_laboral(
    expediente_id=1,
    salario=Decimal("3000000.00"),
    fecha_inicio=date(2020, 1, 1),
    fecha_fin=date(2020, 12, 31),
    pagada=False,
    fecha_pago_total=None,
    tipo=TipoObligacion.PUNTUAL,
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=tipo,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=fecha_inicio,
        valor=salario,
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        pagada=pagada,
        fecha_pago_total=fecha_pago_total,
    )


class TestLaboralStrategy:
    def test_liquida_sin_mora_si_se_pago_el_mismo_dia_de_terminacion(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SANCION_MORATORIA" not in tipos_evento
        # dias_trabajados = 365 (2020-01-01 a 2020-12-31): cesantias 3041666.67 +
        # intereses 370069.44 + prima x2 1520833.33 + vacaciones 1520833.33
        assert resultado.final_balance().principal == Decimal("7974236.10")

    def test_liquida_con_mora_solo_fase1(self):
        # Pagado 30 dias despues de terminar el contrato -- solo fase 1.
        obligacion = _obligacion_laboral(fecha_pago_total=date(2021, 1, 30))

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SANCION_MORATORIA" in tipos_evento
        # salario_diario = 3M/30 = 100000; 30 dias de retardo = 3000000.00
        assert resultado.final_balance().principal == Decimal("10974236.10")  # 7974236.10 + 3000000.00

    def test_liquida_con_mora_cruzando_a_fase2(self):
        # Sin pagar: fecha_corte muy posterior a la terminacion del contrato,
        # suficiente para cruzar a fase 2 (mas de 720 dias de retardo).
        obligacion = _obligacion_laboral()
        fecha_corte = obligacion.fecha_fin + timedelta(days=800)

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        monto_prestaciones = Decimal("7974236.10")
        mora_esperada = MoratoryIndemnityCalculator.calcular(
            salario_mensual=obligacion.valor,
            monto_adeudado=monto_prestaciones,
            fecha_terminacion=obligacion.fecha_fin,
            fecha_pago_o_corte=fecha_corte,
        )
        assert mora_esperada.dias_fase2 > 0
        assert resultado.final_balance().principal == monto_prestaciones + mora_esperada.total

    def test_aplica_un_abono_reduciendo_el_saldo(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        abono = Abono(
            id=1, obligacion_id=1, fecha=date(2021, 1, 15), monto=Decimal("1000000.00"), referencia="ref-1"
        )

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2021, 6, 1)
        )

        assert resultado.total_payments_applied() == Decimal("1000000.00")
        assert resultado.final_balance().total() < Decimal("7974236.10")

    def test_mas_de_una_obligacion_lanza_value_error(self):
        obligacion_1 = _obligacion_laboral(expediente_id=1)
        obligacion_2 = _obligacion_laboral(expediente_id=1)

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion_1, obligacion_2], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_tipo_recurrente_lanza_value_error(self):
        obligacion = _obligacion_laboral(tipo=TipoObligacion.RECURRENTE)

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1))

    def test_fecha_fin_anterior_a_fecha_inicio_lanza_value_error(self):
        obligacion = _obligacion_laboral(fecha_inicio=date(2020, 12, 31), fecha_fin=date(2020, 1, 1))

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1))

    def test_soporta_indexacion_ipc_es_false(self):
        assert LaboralStrategy().soporta_indexacion_ipc is False
```

Also add `from datetime import timedelta` to the imports at the top of `tests/services/test_area_strategy.py` if not already present (the file currently imports `from datetime import date` only, at line 45).

- [ ] **Step 4: Run the tests to verify they fail**

Run: `python -m pytest tests/services/test_area_strategy.py -v`
Expected: FAIL — the `TestLaboralStrategy` cases fail with `AreaNoImplementadaError` instead of the expected results/exceptions.

- [ ] **Step 5: Implement `LaboralStrategy`**

In `app/services/area_strategy.py`, add these imports at the top (alongside the existing ones):

```python
from app.engine.labor.moratory_indemnity import MoratoryIndemnityCalculator
from app.engine.temporal.schedulers.labor import LaborScheduler
```

Replace the `LaboralStrategy` stub (currently lines 223-227) with:

```python
class LaboralStrategy(AreaStrategy):
    """
    Area Laboral. Liquidacion final (finiquito) de UN contrato de trabajo por
    expediente: cesantias, intereses a cesantias, prima (junio/diciembre) y
    vacaciones (LaborScheduler), mas la indemnizacion moratoria bifasica del
    Art. 65 CST (MoratoryIndemnityCalculator) si el pago real o la fecha de
    corte quedan despues de la fecha de terminacion del contrato.

    No es compatible con indexacion IPC (soporta_indexacion_ipc = False): las
    prestaciones sociales se liquidan sobre el salario nominal vigente al
    momento de la causacion, no se indexan por perdida de poder adquisitivo.

    Seguridad social (cotizaciones IBC, pension, salud, ARL, FSP) queda fuera
    de alcance de este sprint -- ver Pendientes.md, Sprint 3, y
    docs/superpowers/specs/2026-07-18-area-laboral-design.md.
    """

    soporta_indexacion_ipc = False

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")
        if len(obligaciones) != 1:
            raise ValueError(
                "El area Laboral liquida un solo contrato (una obligacion) por expediente."
            )

        obligacion = obligaciones[0]
        self._validar_obligacion_laboral(obligacion)

        dias_trabajados = (obligacion.fecha_fin - obligacion.fecha_inicio).days
        eventos = LaborScheduler(
            salario_base=obligacion.valor,
            dias_trabajados=dias_trabajados,
            fecha_liquidacion=obligacion.fecha_fin,
        ).generate()

        # fecha_pago_total (si existe) es cuando realmente se extinguio la
        # deuda; nunca puede ser posterior a fecha_corte para efectos de este
        # reporte -- si el pago real fue despues del corte elegido, la mora
        # se calcula solo hasta el corte (foto historica), no hasta el pago.
        if obligacion.fecha_pago_total is not None:
            fecha_referencia_mora = min(obligacion.fecha_pago_total, fecha_corte)
        else:
            fecha_referencia_mora = fecha_corte

        if fecha_referencia_mora > obligacion.fecha_fin:
            monto_adeudado = sum((e.payload["amount"] for e in eventos), Decimal("0.00"))
            mora = MoratoryIndemnityCalculator.calcular(
                salario_mensual=obligacion.valor,
                monto_adeudado=monto_adeudado,
                fecha_terminacion=obligacion.fecha_fin,
                fecha_pago_o_corte=fecha_referencia_mora,
            )
            if mora.total > Decimal("0.00"):
                eventos.append(Event(
                    date=fecha_referencia_mora,
                    payload={"amount": mora.total, "label": "Indemnizacion moratoria Art. 65 CST"},
                    event_type="SANCION_MORATORIA",
                ))

        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos
        ]

        service = UniversalLiquidationService()
        return service.liquidar(
            eventos_causacion=eventos,
            pagos=pagos,
            fecha_corte=fecha_corte,
        )
        # Sin rate_provider: la tasa diaria generica de UniversalLiquidationService
        # queda en 0 por defecto. Toda la mora del area Laboral ya esta resuelta
        # en el evento SANCION_MORATORIA -- pasar un rate_provider aqui
        # duplicaria el castigo por mora.

    def _validar_obligacion_laboral(self, obligacion) -> None:
        if obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                "El area Laboral solo admite obligaciones de tipo PUNTUAL "
                "(un contrato completo); RECURRENTE no aplica a prestaciones sociales."
            )
        if obligacion.valor is None or obligacion.valor <= Decimal("0.00"):
            raise ValueError("El salario base de la obligacion laboral debe ser mayor que cero.")
        if obligacion.fecha_inicio is None or obligacion.fecha_fin is None:
            raise ValueError(
                "La obligacion laboral necesita 'fecha_inicio' y 'fecha_fin' del contrato."
            )
        if obligacion.fecha_fin <= obligacion.fecha_inicio:
            raise ValueError(
                f"La fecha de terminacion ({obligacion.fecha_fin}) debe ser posterior a la "
                f"fecha de inicio del contrato ({obligacion.fecha_inicio})."
            )
```

Note: the validator does not check `pagada` — the liquidation logic reads `fecha_pago_total` directly (`None` means "not yet paid as of the cutoff"), so `pagada` is a display/audit-only flag the GUI keeps in sync with `fecha_pago_total`, never consulted here. This is a small simplification found while implementing the design spec's pseudocode (which mentioned validating `pagada`/`fecha_pago_total` consistency) — since the strategy never reads `pagada`, that particular check would be dead code.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest tests/services/test_area_strategy.py -v`
Expected: PASS (all cases, including the new `TestLaboralStrategy` class)

- [ ] **Step 7: Run the full suite to check for regressions**

Run: `python -m pytest -q`
Expected: all tests pass

- [ ] **Step 8: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat(labor): implement LaboralStrategy.liquidar() with Art. 65 CST moratory indemnity"
```

---

### Task 4: Enable Laboral in constants

**Files:**
- Modify: `app/core/constants.py`

- [ ] **Step 1: Add `CATEGORIAS_LABORAL` and enable the area**

In `app/core/constants.py`, add the new list after `CATEGORIAS_COMERCIAL` and flip the Laboral tuple:

```python
CATEGORIAS_LABORAL = [
    ("LIQUIDACION_CONTRATO_LABORAL", "Liquidacion de contrato laboral"),
]
# Nota: a diferencia de CATEGORIAS_CIVIL_FAMILIA/CATEGORIAS_COMERCIAL, esta
# categoria es solo una etiqueta de UI -- el event_type real de cada linea de
# la liquidacion (CESANTIAS, INTERESES_CESANTIAS, PRIMA_JUNIO, PRIMA_DICIEMBRE,
# VACACIONES, SANCION_MORATORIA) lo define LaborScheduler/
# MoratoryIndemnityCalculator internamente en app/services/area_strategy.py,
# no este codigo.

AREAS_DERECHO = [
    ("CIVIL_FAMILIA", "Civil / Familia", True),
    ("COMERCIAL", "Comercial", True),
    ("LABORAL", "Laboral", True),
    ("SANCIONATORIO", "Sancionatorio", False),
    ("HONORARIOS", "Honorarios / Litigio", False),
]
# El tercer valor de cada tupla indica si el area esta habilitada para calcular
# en este sprint. Ver Pendientes.md para el orden de habilitacion de las demas.
```

(Only the `AREAS_DERECHO` tuple for `"LABORAL"` changes its third value from `False` to `True`; `CATEGORIAS_LABORAL` is new.)

- [ ] **Step 2: Run the full suite**

Run: `python -m pytest -q`
Expected: all tests pass (`test_registry_expone_las_5_areas` in `tests/services/test_area_strategy.py` already asserts all 5 area keys exist regardless of the enabled flag, so it stays green).

- [ ] **Step 3: Commit**

```bash
git add app/core/constants.py
git commit -m "feat(labor): enable Laboral area and add CATEGORIAS_LABORAL"
```

---

### Task 5: GUI — `ObligacionFormDialog` becomes Laboral-aware

`app/views/obligaciones.py` already branches on `self._area` for Comercial-only fields. This task adds the Laboral-only fields (`fecha_fin`, `pagada`, `fecha_pago_total`) and forces `tipo = PUNTUAL` for Laboral.

**Files:**
- Modify: `app/views/obligaciones.py`
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/views/test_obligaciones.py`:

```python
def test_guarda_obligacion_laboral_con_fechas_de_contrato(qtbot, monkeypatch):
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
    assert guardada.tipo == TipoObligacion.PUNTUAL
    assert guardada.fecha_inicio == date(2020, 1, 1)
    assert guardada.fecha_fin == date(2020, 12, 31)
    assert guardada.tasa_efectiva_anual == Decimal("0.00")
    assert guardada.pagada is False
    assert guardada.fecha_pago_total is None
    session.close()


def test_guarda_obligacion_laboral_marcada_como_pagada(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Liquidacion de contrato")
    dialog.campo_valor.setText("3000000.00")
    dialog.campo_fecha_origen.setDate(date(2020, 1, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 12, 31))
    dialog.check_pagada.setChecked(True)
    dialog.campo_fecha_pago_total.setDate(date(2021, 1, 15))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.pagada is True
    assert guardada.fecha_pago_total == date(2021, 1, 15)
    session.close()


def test_campos_laborales_ocultos_para_area_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_fecha_fin.isVisible() is False
    assert dialog.check_pagada.isVisible() is False


def test_campos_laborales_visibles_para_area_laboral(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_fecha_fin.isVisible() is True
    assert dialog.check_pagada.isVisible() is True
    assert dialog.combo_tipo.isVisible() is False
    assert dialog.campo_tasa.isVisible() is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/views/test_obligaciones.py -v`
Expected: FAIL — `AttributeError: 'ObligacionFormDialog' object has no attribute 'campo_fecha_fin'`

- [ ] **Step 3: Update `ObligacionFormDialog`**

Replace the full contents of `app/views/obligaciones.py`:

```python
from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
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
from app.core.constants import CATEGORIAS_CIVIL_FAMILIA, CATEGORIAS_COMERCIAL, CATEGORIAS_LABORAL
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
        if self._area == "COMERCIAL":
            categorias = CATEGORIAS_COMERCIAL
        elif self._area == "LABORAL":
            categorias = CATEGORIAS_LABORAL
        else:
            categorias = CATEGORIAS_CIVIL_FAMILIA
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

        self.campo_fecha_fin = QDateEdit(QDate.currentDate())
        self.campo_fecha_fin.setCalendarPopup(True)
        self.check_pagada = QCheckBox("Prestaciones pagadas")
        self.check_pagada.stateChanged.connect(self._actualizar_campos_visibles)
        self.campo_fecha_pago_total = QDateEdit(QDate.currentDate())
        self.campo_fecha_pago_total.setCalendarPopup(True)

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
        self.layout_formulario.addRow("Fecha de terminacion de contrato", self.campo_fecha_fin)
        self.layout_formulario.addRow(self.check_pagada)
        self.layout_formulario.addRow("Fecha de pago real", self.campo_fecha_pago_total)
        self.layout_formulario.addRow(boton_guardar)
        self.setLayout(self.layout_formulario)

        es_comercial = self._area == "COMERCIAL"
        self.campo_tasa_moratoria.setVisible(es_comercial)
        self.campo_fecha_vencimiento.setVisible(es_comercial)
        self.campo_ibc_vigente.setVisible(es_comercial)

        es_laboral = self._area == "LABORAL"
        self.campo_fecha_fin.setVisible(es_laboral)
        self.check_pagada.setVisible(es_laboral)
        self.combo_tipo.setVisible(not es_laboral)
        self.campo_tasa.setVisible(not es_laboral)
        if es_laboral:
            self.combo_tipo.setCurrentIndex(0)  # Puntual, forzado -- Laboral no admite Recurrente

        self._actualizar_campos_visibles()

    def _actualizar_campos_visibles(self) -> None:
        if self._area == "LABORAL":
            self.campo_fecha_origen.setVisible(True)  # reutilizado como "fecha de inicio del contrato"
            self.campo_fecha_inicio.setVisible(False)
            self.campo_dia_pago.setVisible(False)
            self.campo_fecha_pago_total.setVisible(self.check_pagada.isChecked())
            return

        self.campo_fecha_pago_total.setVisible(False)
        es_recurrente = self.combo_tipo.currentData() == "RECURRENTE"
        self.campo_fecha_origen.setVisible(not es_recurrente)
        self.campo_fecha_inicio.setVisible(es_recurrente)
        self.campo_dia_pago.setVisible(es_recurrente)

    def guardar(self) -> int:
        try:
            valor = Decimal(self.campo_valor.text())
        except InvalidOperation as error:
            raise ValueError("Valor y tasa deben ser numeros validos.") from error

        if valor <= Decimal("0"):
            raise ValueError("El valor de la obligacion debe ser mayor que cero.")

        if self._area == "LABORAL":
            return self._guardar_laboral(valor)

        try:
            tasa = Decimal(self.campo_tasa.text())
        except InvalidOperation as error:
            raise ValueError("Valor y tasa deben ser numeros validos.") from error

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

    def _guardar_laboral(self, valor: Decimal) -> int:
        qdate_inicio = self.campo_fecha_origen.date()
        fecha_inicio = date(qdate_inicio.year(), qdate_inicio.month(), qdate_inicio.day())
        qdate_fin = self.campo_fecha_fin.date()
        fecha_fin = date(qdate_fin.year(), qdate_fin.month(), qdate_fin.day())

        fecha_pago_total = None
        pagada = False
        if self.check_pagada.isChecked():
            qdate_pago = self.campo_fecha_pago_total.date()
            fecha_pago_total = date(qdate_pago.year(), qdate_pago.month(), qdate_pago.day())
            pagada = True

        session = session_module.get_session()
        obligacion = Obligacion(
            expediente_id=self._expediente_id,
            tipo=TipoObligacion.PUNTUAL,
            concepto=self.campo_concepto.text().strip(),
            categoria=self.combo_categoria.currentData(),
            fecha_origen=fecha_inicio,
            valor=valor,
            tasa_efectiva_anual=Decimal("0.00"),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            pagada=pagada,
            fecha_pago_total=fecha_pago_total,
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

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/views/test_obligaciones.py -v`
Expected: PASS (all tests: the 7 existing + the 4 new Laboral ones)

- [ ] **Step 5: Run the full suite**

Run: `python -m pytest -q`
Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "feat(gui): make ObligacionFormDialog Laboral-aware (fecha_fin, pagada, fecha_pago_total)"
```

---

### Task 6: Documentation — README, Guía de Usuario, Pendientes.md

**Files:**
- Modify: `README.md`
- Modify: `docs/GUIA_USUARIO.md`
- Modify: `Pendientes.md`

- [ ] **Step 1: Update `README.md`**

Replace the "Estado actual" section (lines 12-28) from:

```markdown
## Estado actual (2026-07-17)

✅ **Funcional hoy:** captura manual de expedientes y liquidación real de las áreas **Civil / Familia**
(interés del Art. 1617 del Código Civil, 6% anual, sobre obligaciones puntuales y recurrentes, con
abonos) y **Comercial** (Art. 884 C.Co., tasas remuneratoria y moratoria pactadas por obligación con
split real antes/después del vencimiento, validación de tope de usura 1.5×IBC). El resultado de
cualquier liquidación se puede exportar a **PDF** y a **Word** desde la pantalla de Resultado de
Liquidación.

🚧 **En desarrollo:** las áreas Laboral, Sancionatorio y Honorarios están registradas en el sistema pero
todavía no calculan (el programa avisa "Área no implementada" si se intentan usar). Indexación por IPC,
prescripción/caducidad, anatocismo comercial condicionado (Art. 886 C.Co.) y varios módulos más también
están pendientes. Las series históricas de SMLMV, IPC e IBC/Tasa de Usura
(1984-2026, 1967-2025 y 1997-2026 respectivamente) ya están cargadas en
`app/engine/indexation/historical_index.py`, aunque todavía no están conectadas a ningún cálculo — esa
conexión es trabajo de otros sprints. El plan completo, sprint por sprint, está en
**[Pendientes.md](Pendientes.md)**.
```

to:

```markdown
## Estado actual (2026-07-19)

✅ **Funcional hoy:** captura manual de expedientes y liquidación real de las áreas **Civil / Familia**
(interés del Art. 1617 del Código Civil, 6% anual, sobre obligaciones puntuales y recurrentes, con
abonos), **Comercial** (Art. 884 C.Co., tasas remuneratoria y moratoria pactadas por obligación con
split real antes/después del vencimiento, validación de tope de usura 1.5×IBC) y **Laboral**
(liquidación final de un contrato: cesantías, intereses a cesantías, prima, vacaciones, e indemnización
moratoria bifásica del Art. 65 CST). El resultado de cualquier liquidación se puede exportar a **PDF** y
a **Word** desde la pantalla de Resultado de Liquidación.

🚧 **En desarrollo:** las áreas Sancionatorio y Honorarios están registradas en el sistema pero todavía
no calculan (el programa avisa "Área no implementada" si se intentan usar). Seguridad social en el área
Laboral, indexación por IPC, prescripción/caducidad, anatocismo comercial condicionado (Art. 886 C.Co.) y
varios módulos más también están pendientes. Las series históricas de SMLMV, IPC e IBC/Tasa de Usura
(1984-2026, 1967-2025 y 1997-2026 respectivamente) ya están cargadas en
`app/engine/indexation/historical_index.py` — la de IBC/Usura ya se usa en la fase 2 de la indemnización
moratoria laboral; las otras dos todavía no están conectadas a ningún cálculo. El plan completo, sprint
por sprint, está en **[Pendientes.md](Pendientes.md)**.
```

- [ ] **Step 2: Update `docs/GUIA_USUARIO.md` — header note**

Change lines 8-9 from:

```markdown
> **Última actualización:** 2026-07-17 — refleja el estado de Civil/Familia, Comercial y exportación de
> liquidaciones a PDF/Word. Cada vez que se complete un sprint nuevo de [`Pendientes.md`](../Pendientes.md),
```

to:

```markdown
> **Última actualización:** 2026-07-19 — refleja el estado de Civil/Familia, Comercial, Laboral y
> exportación de liquidaciones a PDF/Word. Cada vez que se complete un sprint nuevo de [`Pendientes.md`](../Pendientes.md),
```

(Line 10, `esta guía se actualiza para que nunca quede desactualizada respecto al programa real.`, stays unchanged.)

- [ ] **Step 3: Update `docs/GUIA_USUARIO.md` — section 6 (áreas del derecho)**

Change line 301-302 from:

```markdown
Al crear un expediente, el campo "Área del derecho" muestra 5 opciones, pero **solo dos calculan de
verdad hoy**:
```

to:

```markdown
Al crear un expediente, el campo "Área del derecho" muestra 5 opciones, pero **solo tres calculan de
verdad hoy**:
```

Then replace the table at lines 304-310 from:

```markdown
| Área | ¿Funciona? |
|---|---|
| Civil / Familia | ✅ Sí — interés del Art. 1617 C.C. (6% anual o la tasa que se pacte), sobre obligaciones puntuales y recurrentes, con abonos. |
| Comercial | ✅ Sí — Art. 884 C.Co., tasa remuneratoria antes del vencimiento y tasa moratoria después, validación de tope de usura (1.5× el IBC que ingreses). Ver [sección 5.7](#57-agregar-una-obligación-comercial). |
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
| Laboral | ✅ Sí — liquidación final (finiquito) de un contrato: cesantías, intereses a cesantías, prima, vacaciones, e indemnización moratoria bifásica del Art. 65 CST si hubo retardo en el pago. Ver [sección 5.9](#59-agregar-una-obligación-laboral-y-liquidar-un-contrato-terminado). Seguridad social no está incluida (ver sección 8). |
| Sancionatorio | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 4. |
| Honorarios / Litigio | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 4. |
```

- [ ] **Step 4: Add a new section 5.9 documenting the Laboral obligation form**

In `docs/GUIA_USUARIO.md`, insert a new subsection right after section 5.8 ("Exportar la liquidación a PDF o Word"), before the `---` separator that precedes "## 6. Áreas del derecho: cuáles funcionan hoy":

```markdown
### 5.9. Agregar una obligación laboral y liquidar un contrato terminado

Cuando el expediente tiene **Área del derecho = Laboral**, el formulario de "Agregar obligación" cambia
de forma: representa un contrato de trabajo completo, no una deuda puntual o una cuota recurrente — por
eso el campo "Tipo" se oculta (siempre se guarda como Puntual) y la Tasa efectiva anual tampoco aplica
(se guarda en 0, sin mostrarse).

1. Dentro del Detalle de un expediente Laboral, haz clic en **"Agregar obligación"**.
2. Llena:
   - **Concepto**: por ejemplo, "Liquidación de contrato — Juan Pérez".
   - **Valor**: el salario base mensual.
   - **Fecha de origen (Puntual)**: aquí representa la **fecha de inicio del contrato**.
   - **Fecha de terminación de contrato**: el día en que el contrato terminó. A partir de esta fecha se
     calculan las prestaciones (todas se vuelven exigibles ese mismo día — es una liquidación final, no
     un contrato en curso) y, si hubo retardo en el pago, empieza a correr la indemnización moratoria del
     Art. 65 CST.
   - **Prestaciones pagadas** (casilla): si el empleador ya pagó la liquidación completa, marca esta
     casilla y llena **Fecha de pago real** con el día en que se pagó. Si no se ha pagado, deja la
     casilla sin marcar — el programa calculará la mora hasta la fecha de corte del expediente.
3. Haz clic en **"Guardar"**.
4. Haz clic en **"Liquidar"**. El resultado incluye: Cesantías, Intereses/Cesantías, Prima (junio y
   diciembre), Vacaciones y, si hubo retardo en el pago, un rubro "Indemnización moratoria Art. 65 CST".

**Sobre la indemnización moratoria (Art. 65 CST):** si el pago se hizo (o el corte del expediente cae)
más de 720 días (24 meses) después de la terminación del contrato, el programa cambia automáticamente de
fase — hasta el día 720 cobra un día de salario por cada día de retardo; del día 721 en adelante, cobra
intereses sobre lo adeudado a la tasa de usura histórica certificada por la Superintendencia Financiera
(la misma serie de datos que usa el área Comercial). No hay nada que configurar manualmente para esto.

**Qué NO calcula todavía esta área:** cotizaciones a seguridad social (pensión, salud, ARL, fondo de
solidaridad pensional), incapacidades, suspensiones contractuales, ni nada relacionado con pensiones —
ver [sección 8](#8-funciones-pendientes-o-en-desarrollo).
```

- [ ] **Step 5: Update `docs/GUIA_USUARIO.md` — section 8 (pendientes) and section 9 (FAQ)**

In section 8 (currently lines 377-378), change:

```markdown
- 🚧 **Cálculo en las áreas Laboral, Sancionatorio y Honorarios** — hoy funcionan Civil/Familia y
  Comercial (`Pendientes.md`, Sprints 3 y 4).
```

to:

```markdown
- 🚧 **Cálculo en las áreas Sancionatorio y Honorarios** — hoy funcionan Civil/Familia, Comercial y
  Laboral (`Pendientes.md`, Sprint 4).
- 🚧 **Seguridad social en el área Laboral** (cotizaciones a pensión, salud, ARL, fondo de solidaridad
  pensional) — decisión tomada con el usuario de dejarlo fuera del Sprint 3: BASTIUM liquida procesos
  judiciales, no es un sistema de nómina corriente (`Pendientes.md`, Sprint 3).
- 🚧 **Incapacidades y suspensiones contractuales en el área Laboral** — no modeladas (`Pendientes.md`,
  Sprint 3).
```

In section 9 (currently lines 407-409), change:

```markdown
**"Seleccioné Laboral/Sancionatorio/Honorarios y no me deja."**
Es esperado — esas áreas todavía no calculan, por eso aparecen deshabilitadas en el formulario. Comercial
sí está habilitada. Ver [sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy).
```

to:

```markdown
**"Seleccioné Sancionatorio/Honorarios y no me deja."**
Es esperado — esas áreas todavía no calculan, por eso aparecen deshabilitadas en el formulario. Comercial
y Laboral sí están habilitadas. Ver [sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy).
```

- [ ] **Step 6: Update `Pendientes.md`**

In the "Sprint 3 — Área Laboral" section, add a `**Estado:**` block right before `**Definición de Hecho:**`, matching the pattern already used to close out Sprint 2 and Sprint 5:

```markdown
**Estado:** Implementado (2026-07-19) — ver `docs/superpowers/plans/2026-07-19-area-laboral.md` y
`docs/superpowers/specs/2026-07-18-area-laboral-design.md`. Verificado durante el diseño: la fórmula de
`INTERESES_CESANTIAS` que este documento marcaba como sospechosa de bug en realidad coincide exactamente
con el PDF (pág. 51) — no se modificó. Pendientes explícitos que quedaron fuera de este sprint (decisión
tomada con el usuario, no un olvido): seguridad social (cotizaciones IBC, pensión, salud, ARL, FSP),
incapacidades y suspensiones contractuales, y el módulo pensional (IBL, densidad de semanas). También
queda documentado como limitación conocida: `dias_trabajados` se calcula como diferencia de calendario
simple, no con la convención comercial exacta de meses de 30 días que usa la nómina real (sobre-causa
prestaciones en ~1-2% para un año calendario completo).
```

- [ ] **Step 7: Commit**

```bash
git add README.md docs/GUIA_USUARIO.md Pendientes.md
git commit -m "docs: document Área Laboral in README, Guía de Usuario, and Pendientes.md"
```

---

### Task 7: Full verification pass

**Files:** none (verification only)

- [ ] **Step 1: Run the full automated suite**

Run: `python -m pytest -q`
Expected: all tests pass, no failures.

- [ ] **Step 2: Manual smoke test — happy path with moratory indemnity**

```bash
python main.py
```

1. Click "Nuevo expediente". Fill Radicado `2026-060`, Demandante `Juan Perez`, Demandado `Empresa SAS`,
   **Área del derecho = Laboral** (should now be selectable, not greyed out), Fecha de corte
   `2021-06-01`. Save.
2. Double-click the new expediente to open its detail page.
3. Click "Agregar obligación". Confirm "Tipo" and "Tasa efectiva anual (%)" are hidden, and "Fecha de
   terminación de contrato" / "Prestaciones pagadas" are visible. Fill: Concepto = "Liquidacion de
   contrato", Valor = `3000000.00`, Fecha de origen (Puntual) = `2020-01-01`, Fecha de terminación de
   contrato = `2020-12-31`. Leave "Prestaciones pagadas" unchecked. Save.
4. Click "Liquidar". Confirm the Resultado de Liquidación screen opens without error and shows rows for
   Cesantías, Intereses/Cesantías, Prima Junio, Prima Diciembre, Vacaciones, and "Indemnizacion moratoria
   Art. 65 CST" (fecha de corte `2021-06-01` is more than 720 days... actually verify: `2020-12-31` to
   `2021-06-01` is about 152 days, so only Fase 1 applies — expect a `SANCION_MORATORIA` row with a
   nonzero amount, not zero).

Expected: no crash, no "Área no implementada" message, a `SANCION_MORATORIA` line item present with the
label "Indemnizacion moratoria Art. 65 CST".

- [ ] **Step 3: Manual smoke test — paid on time (no moratory indemnity)**

Repeat steps 1-3 above for a second expediente, but check "Prestaciones pagadas" and set "Fecha de pago
real" = `2020-12-31` (same day as termination). Click "Liquidar".

Expected: the result shows Cesantías/Intereses/Prima/Vacaciones but no "Indemnizacion moratoria Art. 65
CST" row.

- [ ] **Step 4: Confirm docs match reality**

Re-read `README.md` "Estado actual" and `docs/GUIA_USUARIO.md` section 6 — confirm both describe Laboral
as functional, matching what was just verified manually.

- [ ] **Step 5: Final commit (only if any fixups were needed in steps 1-4)**

If everything passed with no code changes, there is nothing to commit here — Task 6's commit already
covers the documentation. If the manual smoke test surfaced a bug, fix it, add a regression test in the
relevant file from Tasks 1/2/3/5, rerun `python -m pytest -q`, and commit with a `fix:` message
describing the bug found during smoke testing.

---

## Post-plan reminder

This plan does not implement:
- Seguridad social (cotizaciones IBC, pensión, salud, ARL, FSP) — confirmed out of scope with the user
  during brainstorming.
- Incapacidades y suspensiones contractuales — not in this sprint's included scope per `Pendientes.md`.
- Régimen de Prima Media, IBL, pensiones — separate domain per `Pendientes.md`.
- Exact 30/360 day-count convention for `dias_trabajados` — documented known limitation, calendar-day
  difference used instead.
- Multi-year contracts with varying historical SMLMV — `LaborScheduler` doesn't consume SMLMV at all, so
  this doesn't block the sprint, but a multi-year contract liquidates as one block of days worked, not
  year by year.
- More than one Laboral obligación per expediente — `LaboralStrategy` rejects this with a `ValueError`.

These are intentional scope boundaries agreed with the user during brainstorming, not omissions.
