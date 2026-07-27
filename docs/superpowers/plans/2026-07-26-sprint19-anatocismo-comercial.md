# Sprint 19 — Anatocismo comercial condicionado (Art. 886 C.Co.) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Activar el anatocismo comercial (interés sobre interés, Art. 886 C.Co.) en `ComercialStrategy`, pero solo cuando se cumplan las dos condiciones legales (demanda judicial, o acuerdo posterior con al menos un año de intereses vencidos), manteniendo interés simple como comportamiento por defecto.

**Architecture:** El motor sigue acumulando interés simple día a día (mecanismo ya existente, que ya maneja abonos intermedios vía `AllocationEngine`). Se agrega un nuevo tipo de evento `CAPITALIZACION_INTERESES_ANATOCISMO` que traslada el interés ya devengado al capital, insertado por `ComercialStrategy` en la fecha de capitalización y cada aniversario hasta la fecha de corte. Repetir la capitalización anualmente reproduce el efecto de interés compuesto exacto — `CompoundInterest.calculate()` (fórmula cerrada, huérfana) no se usa en este sprint; ver spec para el porqué.

**Tech Stack:** Python, SQLAlchemy (SQLite), PySide6 (GUI), pytest.

**Spec:** `docs/superpowers/specs/2026-07-26-sprint19-anatocismo-comercial-design.md`

---

### Task 1: `BalanceEngine.capitalize_interest`

**Files:**
- Modify: `app/engine/liquidation/balance.py`
- Test: `tests/liquidation/test_balance.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/liquidation/test_balance.py`:

```python
def test_capitalize_interest_mueve_el_interes_al_capital():
    initial_debt = PendingDebt(Decimal("1000.00"), Decimal("300.00"), Decimal("50.00"))
    new_debt = BalanceEngine.capitalize_interest(initial_debt)

    assert new_debt.principal == Decimal("1300.00")
    assert new_debt.interest == Decimal("0.00")
    assert new_debt.indexation == Decimal("50.00")  # no se toca
    assert initial_debt.interest == Decimal("300.00")  # garantiza inmutabilidad


def test_capitalize_interest_con_interes_en_cero_no_cambia_nada():
    initial_debt = PendingDebt(Decimal("1000.00"), Decimal("0.00"), Decimal("0.00"))
    new_debt = BalanceEngine.capitalize_interest(initial_debt)

    assert new_debt.principal == Decimal("1000.00")
    assert new_debt.interest == Decimal("0.00")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/liquidation/test_balance.py -v`
Expected: FAIL with `AttributeError: type object 'BalanceEngine' has no attribute 'capitalize_interest'`

- [ ] **Step 3: Write minimal implementation**

In `app/engine/liquidation/balance.py`, add after `add_indexation`:

```python
    @staticmethod
    def capitalize_interest(debt: PendingDebt) -> PendingDebt:
        return PendingDebt(
            principal=debt.principal + debt.interest,
            interest=Decimal("0.00"),
            indexation=debt.indexation
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/liquidation/test_balance.py -v`
Expected: PASS (5 tests total in this file)

- [ ] **Step 5: Commit**

```bash
git add app/engine/liquidation/balance.py tests/liquidation/test_balance.py
git commit -m "feat: add BalanceEngine.capitalize_interest for anatocismo comercial"
```

---

### Task 2: `LiquidationCore` — nuevo evento `CAPITALIZACION_INTERESES_ANATOCISMO`

**Files:**
- Modify: `app/engine/liquidation/engine.py:111-143` (método `_process_event`)
- Test: `tests/liquidation/test_engine.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/liquidation/test_engine.py`:

```python
def test_capitalizacion_intereses_anatocismo_traslada_interes_devengado_al_capital():
    events = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2026, 1, 31), payload={}, event_type="CAPITALIZACION_INTERESES_ANATOCISMO"),
    ]
    # 1% diario sobre 1000.00 durante 30 dias (2026-01-02 a 2026-01-31) = 300.00 exacto
    engine = LiquidationCore(default_daily_rate=Rate.from_percent(Decimal("1.0")))

    result = engine.process(events, cutoff_date=date(2026, 1, 31))

    final_debt = result.final_balance()
    assert final_debt.principal == Decimal("1300.00")
    assert final_debt.interest == Decimal("0.00")


def test_capitalizacion_intereses_anatocismo_con_interes_ya_pagado_no_capitaliza_nada():
    events = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("1000.00"), "reference": ""}, event_type="PAYMENT"),
        Event(date=date(2026, 1, 31), payload={}, event_type="CAPITALIZACION_INTERESES_ANATOCISMO"),
    ]
    engine = LiquidationCore(default_daily_rate=Rate.from_percent(Decimal("1.0")))

    result = engine.process(events, cutoff_date=date(2026, 1, 31))

    final_debt = result.final_balance()
    assert final_debt.principal == Decimal("0.00")
    assert final_debt.interest == Decimal("0.00")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/liquidation/test_engine.py -v`
Expected: FAIL with `ValueError: Tipo de evento no reconocido: 'CAPITALIZACION_INTERESES_ANATOCISMO'...`

- [ ] **Step 3: Write minimal implementation**

In `app/engine/liquidation/engine.py`, in `_process_event`, add a new `elif` branch right before the final `else` (after the `PAYMENT` branch, currently lines 132-137):

```python
        elif event.event_type == "CAPITALIZACION_INTERESES_ANATOCISMO":
            self._current_debt = BalanceEngine.capitalize_interest(self._current_debt)

        else:
```

(The existing `else: raise ValueError(...)` stays as-is, just moves down one branch.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/liquidation/test_engine.py -v`
Expected: PASS (5 tests total in this file)

- [ ] **Step 5: Commit**

```bash
git add app/engine/liquidation/engine.py tests/liquidation/test_engine.py
git commit -m "feat: wire CAPITALIZACION_INTERESES_ANATOCISMO event in LiquidationCore"
```

---

### Task 3: Campos nuevos en `Obligacion`

**Files:**
- Modify: `database/models.py:116-119`
- Test: `tests/database/test_models.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/database/test_models.py`:

```python
def test_obligacion_anatocismo_defaults(session):
    expediente = Expediente(
        radicado="2026-00140",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.COMERCIAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Capital de pagare",
        categoria="CAPITAL_PAGARE",
        fecha_origen=date(2025, 1, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.commit()

    assert obligacion.anatocismo_demanda_judicial is False
    assert obligacion.anatocismo_fecha_acuerdo is None


def test_obligacion_anatocismo_activo_con_fecha_acuerdo(session):
    expediente = Expediente(
        radicado="2026-00141",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.COMERCIAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Capital de pagare",
        categoria="CAPITAL_PAGARE",
        fecha_origen=date(2025, 1, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        anatocismo_fecha_acuerdo=date(2026, 2, 15),
    )
    session.add(obligacion)
    session.commit()

    fetched = session.query(Obligacion).filter_by(id=obligacion.id).one()
    assert fetched.anatocismo_fecha_acuerdo == date(2026, 2, 15)
    assert fetched.anatocismo_demanda_judicial is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/database/test_models.py -v`
Expected: FAIL with `TypeError: 'anatocismo_fecha_acuerdo' is an invalid keyword argument for Obligacion`

- [ ] **Step 3: Write minimal implementation**

In `database/models.py`, in the `Obligacion` class, add after `trm_fecha_referencia` (line 119) and before `base_sancion_tributaria` (line 120):

```python
    anatocismo_demanda_judicial: Mapped[bool] = mapped_column(Boolean, default=False)
    anatocismo_fecha_acuerdo: Mapped[date | None] = mapped_column(Date, nullable=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/database/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add database/models.py tests/database/test_models.py
git commit -m "feat: add anatocismo_demanda_judicial/anatocismo_fecha_acuerdo to Obligacion"
```

---

### Task 4: Migración de esquema

**Files:**
- Create: `scripts/migrate_anatocismo_comercial.py`
- Test: `tests/scripts/test_migrate_anatocismo_comercial.py`

- [ ] **Step 1: Write the failing test**

Create `tests/scripts/test_migrate_anatocismo_comercial.py`:

```python
import sqlite3

import pytest

from scripts.migrate_anatocismo_comercial import migrar


@pytest.fixture
def db_sin_columnas(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY, concepto TEXT)")
    con.execute("INSERT INTO obligaciones (id, concepto) VALUES (1, 'Capital de pagare')")
    con.commit()
    con.close()
    return db_path


def test_migrar_agrega_las_dos_columnas_y_retorna_true(db_sin_columnas):
    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert {"anatocismo_demanda_judicial", "anatocismo_fecha_acuerdo"} <= columnas


def test_migrar_preserva_las_filas_existentes_con_defaults(db_sin_columnas):
    migrar(db_sin_columnas)

    con = sqlite3.connect(db_sin_columnas)
    fila = con.execute(
        "SELECT concepto, anatocismo_demanda_judicial, anatocismo_fecha_acuerdo FROM obligaciones WHERE id = 1"
    ).fetchone()
    con.close()
    assert fila == ("Capital de pagare", 0, None)


def test_migrar_es_idempotente_segunda_corrida_retorna_false(db_sin_columnas):
    primera = migrar(db_sin_columnas)
    segunda = migrar(db_sin_columnas)
    assert primera is True
    assert segunda is False


def test_migrar_es_idempotente_si_ya_existe_solo_una_de_las_dos_columnas(db_sin_columnas):
    con = sqlite3.connect(db_sin_columnas)
    con.execute("ALTER TABLE obligaciones ADD COLUMN anatocismo_demanda_judicial BOOLEAN NOT NULL DEFAULT 0")
    con.commit()
    con.close()

    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert {"anatocismo_demanda_judicial", "anatocismo_fecha_acuerdo"} <= columnas
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/scripts/test_migrate_anatocismo_comercial.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.migrate_anatocismo_comercial'`

- [ ] **Step 3: Write minimal implementation**

Create `scripts/migrate_anatocismo_comercial.py`:

```python
"""Migracion de esquema (Sprint 19): agrega las columnas
anatocismo_demanda_judicial y anatocismo_fecha_acuerdo a la tabla
obligaciones. Idempotente -- verifica con PRAGMA table_info antes de alterar
cada columna individualmente, mismo patron que
scripts/migrate_aplica_indexacion_ipc.py (Sprint 8) y
scripts/migrate_moneda_trm.py (Sprint 12)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "anatocismo_demanda_judicial": "BOOLEAN NOT NULL DEFAULT 0",
    "anatocismo_fecha_acuerdo": "DATE",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas anatocismo_demanda_judicial/anatocismo_fecha_acuerdo
    si no existen. Retorna True si aplico al menos un ALTER TABLE, False si
    las dos columnas ya existian."""
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
        print("Columnas anatocismo_demanda_judicial/anatocismo_fecha_acuerdo agregadas a obligaciones.")
    else:
        print("Las columnas ya existian, no se hizo nada.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/scripts/test_migrate_anatocismo_comercial.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/migrate_anatocismo_comercial.py tests/scripts/test_migrate_anatocismo_comercial.py
git commit -m "feat: add idempotent migration for anatocismo comercial columns"
```

---

### Task 5: `ComercialStrategy` — validación de condiciones de anatocismo

**Files:**
- Modify: `app/services/area_strategy.py:206-251` (método `_validar_obligacion_comercial`)
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Write the failing test**

In `tests/services/test_area_strategy.py`, first extend the shared helper `_obligacion_comercial` (around line 355) to accept the two new optional fields — replace:

```python
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
```

with:

```python
def _obligacion_comercial(
    expediente_id=1,
    valor=Decimal("1000000.00"),
    tasa_remuneratoria=Decimal("6.00"),
    tasa_moratoria=Decimal("24.00"),
    ibc=Decimal("20.00"),
    fecha_origen=date(2025, 1, 1),
    fecha_vencimiento=date(2025, 2, 1),
    anatocismo_demanda_judicial=False,
    anatocismo_fecha_acuerdo=None,
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
        anatocismo_demanda_judicial=anatocismo_demanda_judicial,
        anatocismo_fecha_acuerdo=anatocismo_fecha_acuerdo,
    )
```

Then add these tests inside `class TestComercialStrategy` (anywhere after `_obligacion_comercial` is defined):

```python
    def test_ambas_condiciones_de_anatocismo_a_la_vez_lanza_value_error(self):
        obligacion = _obligacion_comercial(
            anatocismo_demanda_judicial=True,
            anatocismo_fecha_acuerdo=date(2026, 2, 15),
        )

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 1))

    def test_recurrente_con_anatocismo_activo_lanza_value_error(self):
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
            anatocismo_demanda_judicial=True,
        )

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 5))

    def test_acuerdo_posterior_que_no_cumple_un_anio_lanza_value_error(self):
        # vencimiento 2025-02-01 + 365 dias = 2026-02-01; un acuerdo antes de esa fecha es invalido.
        obligacion = _obligacion_comercial(anatocismo_fecha_acuerdo=date(2026, 1, 15))

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 1))

    def test_acuerdo_posterior_que_cumple_exactamente_un_anio_no_lanza_error(self):
        obligacion = _obligacion_comercial(anatocismo_fecha_acuerdo=date(2026, 2, 1))

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 1)
        )

        assert resultado.final_balance().principal > obligacion.valor
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/services/test_area_strategy.py -v -k anatocismo or acuerdo or recurrente_con_anatocismo`
Expected: FAIL — `test_ambas_condiciones...` and `test_recurrente_con_anatocismo...` and `test_acuerdo_posterior_que_no_cumple...` fail because no `ValueError` is raised (the fields are silently ignored today); `test_acuerdo_posterior_que_cumple_exactamente_un_anio...` fails because `principal == obligacion.valor` (no capitalization happens yet).

- [ ] **Step 3: Write minimal implementation**

In `app/services/area_strategy.py`, first add `Optional` to the typing import at the top of the file — replace:

```python
from typing import List
```

with:

```python
from typing import List, Optional
```

Then, in `ComercialStrategy._validar_obligacion_comercial`, add at the very end of the method (after the existing `moneda`/`trm_aplicable` block, before the method ends):

```python
        if obligacion.anatocismo_demanda_judicial and obligacion.anatocismo_fecha_acuerdo is not None:
            raise ValueError(
                f"La obligacion comercial '{obligacion.concepto}' no puede tener "
                f"'anatocismo_demanda_judicial' y 'anatocismo_fecha_acuerdo' activos a la vez "
                f"(son dos vias habilitantes excluyentes del Art. 886 C.Co.)."
            )

        anatocismo_activo = (
            obligacion.anatocismo_demanda_judicial or obligacion.anatocismo_fecha_acuerdo is not None
        )
        if anatocismo_activo and obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion comercial '{obligacion.concepto}' tiene anatocismo activo, pero "
                f"el anatocismo solo aplica a obligaciones PUNTUAL (RECURRENTE no modela un "
                f"vencimiento por cuota individual)."
            )

        if obligacion.anatocismo_fecha_acuerdo is not None:
            fecha_minima_acuerdo = obligacion.fecha_vencimiento + timedelta(days=365)
            if obligacion.anatocismo_fecha_acuerdo < fecha_minima_acuerdo:
                raise ValueError(
                    f"La obligacion comercial '{obligacion.concepto}' tiene 'anatocismo_fecha_acuerdo' "
                    f"({obligacion.anatocismo_fecha_acuerdo}) que no cumple el año de anterioridad "
                    f"exigido por el Art. 886 C.Co. (debe ser >= {fecha_minima_acuerdo})."
                )
```

- [ ] **Step 4: Run test to verify it passes (validation tests only — capitalization tests still pending Task 6)**

Run: `python -m pytest tests/services/test_area_strategy.py -v -k "ambas_condiciones or recurrente_con_anatocismo or acuerdo_posterior_que_no_cumple"`
Expected: PASS (these 3 tests pass now). `test_acuerdo_posterior_que_cumple_exactamente_un_anio_no_lanza_error` still FAILS — that's expected, it needs Task 6.

- [ ] **Step 5: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat: validate anatocismo comercial enabling conditions in ComercialStrategy"
```

---

### Task 6: `ComercialStrategy` — generación de eventos de capitalización

**Files:**
- Modify: `app/services/area_strategy.py:263-283` (método `_eventos_de_obligacion`)
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Write the failing tests**

Add inside `class TestComercialStrategy`:

```python
    def test_anatocismo_se_activa_con_demanda_judicial_y_mora_mayor_a_un_anio(self):
        fecha_corte = date(2026, 3, 1)
        obligacion_anatocismo = _obligacion_comercial(anatocismo_demanda_judicial=True)
        resultado_anatocismo = ComercialStrategy().liquidar(
            obligaciones=[obligacion_anatocismo], abonos=[], fecha_corte=fecha_corte
        )

        obligacion_simple = _obligacion_comercial()
        resultado_simple = ComercialStrategy().liquidar(
            obligaciones=[obligacion_simple], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado_anatocismo.final_balance().principal > obligacion_anatocismo.valor
        assert resultado_anatocismo.final_balance().total() > resultado_simple.final_balance().total()

    def test_anatocismo_se_activa_con_acuerdo_posterior_valido(self):
        fecha_corte = date(2026, 3, 1)
        obligacion = _obligacion_comercial(anatocismo_fecha_acuerdo=date(2026, 2, 15))

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado.final_balance().principal > obligacion.valor

    def test_anatocismo_no_se_activa_sin_condicion_habilitante(self):
        fecha_corte = date(2026, 3, 1)
        obligacion = _obligacion_comercial()

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado.final_balance().principal == obligacion.valor

    def test_anatocismo_no_se_activa_si_fecha_corte_es_anterior_a_capitalizacion(self):
        fecha_corte = date(2025, 6, 1)  # vencimiento (2025-02-01) + 365 dias = 2026-02-01, aun no llega
        obligacion = _obligacion_comercial(anatocismo_demanda_judicial=True)

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado.final_balance().principal == obligacion.valor

    def test_abono_dentro_del_tramo_de_anatocismo_reduce_la_capitalizacion(self):
        fecha_corte = date(2026, 3, 1)

        obligacion_con_abono = _obligacion_comercial(anatocismo_demanda_judicial=True)
        abono = Abono(
            id=1, obligacion_id=1, fecha=date(2026, 1, 20), monto=Decimal("500000.00"), referencia="ref-1"
        )
        resultado_con_abono = ComercialStrategy().liquidar(
            obligaciones=[obligacion_con_abono], abonos=[abono], fecha_corte=fecha_corte
        )

        obligacion_sin_abono = _obligacion_comercial(anatocismo_demanda_judicial=True)
        resultado_sin_abono = ComercialStrategy().liquidar(
            obligaciones=[obligacion_sin_abono], abonos=[], fecha_corte=fecha_corte
        )

        # El abono (2026-01-20, antes de la capitalizacion en 2026-02-01) reduce el saldo
        # sobre el que se sigue devengando interes -- el total final con abono debe ser menor.
        assert resultado_con_abono.final_balance().total() < resultado_sin_abono.final_balance().total()
```

Also update `test_falta_un_campo_comercial_obligatorio_lanza_value_error` — no change needed there, it's unaffected.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/services/test_area_strategy.py -v -k anatocismo`
Expected: FAIL for `test_anatocismo_se_activa_con_demanda_judicial...`, `test_anatocismo_se_activa_con_acuerdo_posterior...`, `test_abono_dentro_del_tramo...`, and the Task 5 leftover `test_acuerdo_posterior_que_cumple_exactamente_un_anio_no_lanza_error` — all because `principal == obligacion.valor` (no capitalization event exists yet, capital never grows). `test_anatocismo_no_se_activa_sin_condicion_habilitante` and `test_anatocismo_no_se_activa_si_fecha_corte_es_anterior...` already PASS (no anatocismo is exactly today's behavior).

- [ ] **Step 3: Write minimal implementation**

In `app/services/area_strategy.py`, in `ComercialStrategy`, add two new helper methods right after `_valor_en_pesos` (before `_eventos_de_obligacion`):

```python
    def _fecha_capitalizacion_anatocismo(self, obligacion) -> Optional[date]:
        if obligacion.anatocismo_demanda_judicial:
            return obligacion.fecha_vencimiento + timedelta(days=365)
        if obligacion.anatocismo_fecha_acuerdo is not None:
            return obligacion.anatocismo_fecha_acuerdo
        return None

    def _eventos_anatocismo(self, obligacion, fecha_corte: date) -> List[Event]:
        fecha_capitalizacion = self._fecha_capitalizacion_anatocismo(obligacion)
        if fecha_capitalizacion is None or fecha_capitalizacion > fecha_corte:
            return []

        eventos: List[Event] = []
        fecha_evento = fecha_capitalizacion
        while fecha_evento <= fecha_corte:
            eventos.append(
                Event(
                    date=fecha_evento,
                    payload={
                        "label": "Capitalización de intereses (Art. 886 C.Co. — anatocismo comercial)"
                    },
                    event_type="CAPITALIZACION_INTERESES_ANATOCISMO",
                )
            )
            fecha_evento += timedelta(days=365)
        return eventos
```

Then modify `_eventos_de_obligacion` — replace:

```python
    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> List[Event]:
        valor_pesos = self._valor_en_pesos(obligacion)
        if obligacion.tipo.value == "PUNTUAL":
            return [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": valor_pesos, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]
```

with:

```python
    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> List[Event]:
        valor_pesos = self._valor_en_pesos(obligacion)
        if obligacion.tipo.value == "PUNTUAL":
            eventos = [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": valor_pesos, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]
            eventos.extend(self._eventos_anatocismo(obligacion, fecha_corte))
            return eventos
```

(The `RECURRENTE` branch right below is untouched — validation in Task 5 already guarantees `RECURRENTE` never reaches here with anatocismo active.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/services/test_area_strategy.py -v`
Expected: PASS — full file green, including all Task 5 and Task 6 tests.

- [ ] **Step 5: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat: generate periodic capitalization events for anatocismo comercial"
```

---

### Task 7: GUI — `app/views/obligaciones.py`

**Files:**
- Modify: `app/views/obligaciones.py`
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/views/test_obligaciones.py`:

```python
def test_campos_anatocismo_visibles_solo_para_comercial_puntual(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.check_anatocismo_demanda_judicial.isVisible() is True
    assert dialog.check_anatocismo_acuerdo.isVisible() is True

    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE
    assert dialog.check_anatocismo_demanda_judicial.isVisible() is False
    assert dialog.check_anatocismo_acuerdo.isVisible() is False


def test_campos_anatocismo_ocultos_para_area_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.check_anatocismo_demanda_judicial.isVisible() is False
    assert dialog.check_anatocismo_acuerdo.isVisible() is False


def test_campo_fecha_acuerdo_visible_solo_si_checkbox_marcado(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_anatocismo_fecha_acuerdo.isVisible() is False
    dialog.check_anatocismo_acuerdo.setChecked(True)
    assert dialog.campo_anatocismo_fecha_acuerdo.isVisible() is True
    dialog.check_anatocismo_acuerdo.setChecked(False)
    assert dialog.campo_anatocismo_fecha_acuerdo.isVisible() is False


def test_guarda_obligacion_comercial_con_anatocismo_demanda_judicial(qtbot, monkeypatch):
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
    dialog.check_anatocismo_demanda_judicial.setChecked(True)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.anatocismo_demanda_judicial is True
    assert guardada.anatocismo_fecha_acuerdo is None
    session.close()


def test_guarda_obligacion_comercial_con_anatocismo_acuerdo_posterior(qtbot, monkeypatch):
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
    dialog.check_anatocismo_acuerdo.setChecked(True)
    dialog.campo_anatocismo_fecha_acuerdo.setDate(date(2026, 2, 15))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.anatocismo_demanda_judicial is False
    assert guardada.anatocismo_fecha_acuerdo == date(2026, 2, 15)
    session.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/views/test_obligaciones.py -v -k anatocismo`
Expected: FAIL with `AttributeError: 'ObligacionFormDialog' object has no attribute 'check_anatocismo_demanda_judicial'`

- [ ] **Step 3: Write minimal implementation**

In `app/views/obligaciones.py`:

1. Add widget construction right after `self.campo_ibc_vigente = QLineEdit()` (line 73):

```python
        self.campo_ibc_vigente = QLineEdit()
        self.check_anatocismo_demanda_judicial = QCheckBox(
            "Demanda judicial (habilita anatocismo, Art. 886 C.Co.)"
        )
        self.check_anatocismo_acuerdo = QCheckBox("¿Hay acuerdo posterior de capitalización?")
        self.campo_anatocismo_fecha_acuerdo = QDateEdit(QDate.currentDate())
        self.campo_anatocismo_fecha_acuerdo.setCalendarPopup(True)
```

2. Add layout rows right after the `"IBC vigente aplicable (%)"` row (line 126):

```python
        self.layout_formulario.addRow("IBC vigente aplicable (%)", self.campo_ibc_vigente)
        self.layout_formulario.addRow(self.check_anatocismo_demanda_judicial)
        self.layout_formulario.addRow(self.check_anatocismo_acuerdo)
        self.layout_formulario.addRow("Fecha del acuerdo posterior", self.campo_anatocismo_fecha_acuerdo)
```

3. In `_actualizar_campos_visibles`, replace the method body:

```python
    def _actualizar_campos_visibles(self) -> None:
        if self._area == "LABORAL":
            self.campo_fecha_origen.setVisible(True)  # reutilizado como "fecha de inicio del contrato"
            self.campo_fecha_inicio.setVisible(False)
            self.campo_dia_pago.setVisible(False)
            self.campo_fecha_pago_total.setVisible(self.check_pagada.isChecked())
            self.combo_nivel_riesgo_arl.setVisible(self.check_incluir_seguridad_social.isChecked())
            return

        self.campo_fecha_pago_total.setVisible(False)
        es_recurrente = self.combo_tipo.currentData() == "RECURRENTE"
        self.campo_fecha_origen.setVisible(not es_recurrente)
        self.campo_fecha_inicio.setVisible(es_recurrente)
        self.campo_dia_pago.setVisible(es_recurrente)

        es_comercial = self._area == "COMERCIAL"
        mostrar_anatocismo = es_comercial and not es_recurrente
        self.check_anatocismo_demanda_judicial.setVisible(mostrar_anatocismo)
        self.check_anatocismo_acuerdo.setVisible(mostrar_anatocismo)
        self.campo_anatocismo_fecha_acuerdo.setVisible(
            mostrar_anatocismo and self.check_anatocismo_acuerdo.isChecked()
        )
```

4. Connect the acuerdo checkbox so toggling it updates `campo_anatocismo_fecha_acuerdo` visibility — add next to the other `.connect(...)` calls (right after `self.check_incluir_seguridad_social.stateChanged.connect(self._actualizar_campos_visibles)`):

```python
        self.check_anatocismo_acuerdo.stateChanged.connect(self._actualizar_campos_visibles)
```

5. In `guardar()`, add the two new local variables to the declaration block — replace:

```python
        tasa_moratoria = None
        fecha_vencimiento = None
        ibc_vigente = None
        moneda = "COP"
        trm_aplicable = None
        trm_fecha_referencia = None
        if self._area == "COMERCIAL":
```

with:

```python
        tasa_moratoria = None
        fecha_vencimiento = None
        ibc_vigente = None
        moneda = "COP"
        trm_aplicable = None
        trm_fecha_referencia = None
        anatocismo_demanda_judicial = False
        anatocismo_fecha_acuerdo = None
        if self._area == "COMERCIAL":
```

6. Still in `guardar()`, at the end of the `if self._area == "COMERCIAL":` block (right after the `if moneda == "USD":` sub-block that sets `trm_aplicable`/`trm_fecha_referencia`), add:

```python
            anatocismo_demanda_judicial = self.check_anatocismo_demanda_judicial.isChecked()
            if self.check_anatocismo_acuerdo.isChecked():
                qdate_acuerdo = self.campo_anatocismo_fecha_acuerdo.date()
                anatocismo_fecha_acuerdo = date(
                    qdate_acuerdo.year(), qdate_acuerdo.month(), qdate_acuerdo.day()
                )
```

7. In the `Obligacion(...)` constructor call inside `guardar()`, add the two new fields — replace:

```python
            aplica_indexacion_ipc=self.check_aplica_indexacion_ipc.isChecked(),
            moneda=moneda,
            trm_aplicable=trm_aplicable,
            trm_fecha_referencia=trm_fecha_referencia,
```

with:

```python
            aplica_indexacion_ipc=self.check_aplica_indexacion_ipc.isChecked(),
            moneda=moneda,
            trm_aplicable=trm_aplicable,
            trm_fecha_referencia=trm_fecha_referencia,
            anatocismo_demanda_judicial=anatocismo_demanda_judicial,
            anatocismo_fecha_acuerdo=anatocismo_fecha_acuerdo,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/views/test_obligaciones.py -v`
Expected: PASS — full file green.

- [ ] **Step 5: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "feat: wire anatocismo comercial fields into the obligacion GUI form"
```

---

### Task 8: Correr la migración real, cerrar el sprint en la documentación

**Files:**
- Modify: `Pendientes.md:1427-1486` (sección "Sprint 19")
- Modify: `README.md:17-19,48-49`
- Modify: `docs/GUIA_USUARIO.md` (sección 5.7, línea ~282-318)

- [ ] **Step 1: Correr la migración contra el `bastium.db` real (si existe)**

Run: `python scripts/migrate_anatocismo_comercial.py`
Expected output (si el archivo existe): `Columnas anatocismo_demanda_judicial/anatocismo_fecha_acuerdo agregadas a obligaciones.` — o `Las columnas ya existian, no se hizo nada.` si no hay `bastium.db` en este entorno (mensaje de error de archivo no encontrado es aceptable si el equipo aún no tiene el archivo local).

- [ ] **Step 2: Correr la suite completa**

Run: `python -m pytest`
Expected: todos los tests en verde (0 failures).

- [ ] **Step 3: Cerrar Sprint 19 en `Pendientes.md`**

En `Pendientes.md`, cambia el encabezado de la línea 1427 de:

```
## Sprint 19 — Anatocismo comercial condicionado (Art. 886 C.Co.)
```

a:

```
## Sprint 19 — Anatocismo comercial condicionado (Art. 886 C.Co.) ✅ Completado
```

Y en el índice (TOC), la línea:

```
- [Sprint 19 — Anatocismo comercial condicionado (Art. 886 C.Co.)](#sprint-19--anatocismo-comercial-condicionado-art-886-cco)
```

cambia a:

```
- [Sprint 19 — Anatocismo comercial condicionado (Art. 886 C.Co.) ✅ Completado](#sprint-19--anatocismo-comercial-condicionado-art-886-cco--completado)
```

Luego, justo antes de la línea `---` que cierra la sección del Sprint 19 (después de "Definición de Hecho"), agrega:

```markdown

**Estado:** Implementado (2026-07-26) — ver
`docs/superpowers/plans/2026-07-26-sprint19-anatocismo-comercial.md` y
`docs/superpowers/specs/2026-07-26-sprint19-anatocismo-comercial-design.md`. Desviación respecto al plan
original: en vez de usar `CompoundInterest.calculate()` (fórmula cerrada de una sola pasada), se
implementaron eventos de capitalización periódica (`CAPITALIZACION_INTERESES_ANATOCISMO`, nuevo en
`LiquidationCore`/`BalanceEngine`) que trasladan el interés simple ya devengado al capital cada aniversario
desde la fecha de capitalización. Esto reproduce el interés compuesto exacto y maneja correctamente abonos
que caigan a mitad del tramo (usando la maquinaria de `AllocationEngine` ya existente), a costa de que
`CompoundInterest.calculate()` sigue huérfano. Limitación conocida documentada en el spec: si un expediente
mezcla varias obligaciones comerciales y solo algunas cumplen las condiciones de anatocismo, la
capitalización actúa sobre el saldo de interés consolidado del expediente completo (el motor no separa
saldos por obligación) — heredado de la arquitectura ya existente, no introducido por este sprint.
```

- [ ] **Step 4: Actualizar `README.md`**

En `README.md`, dentro del párrafo "✅ Funcional hoy" (línea 17), cambia:

```
**Comercial** (Art. 884 C.Co., tasas remuneratoria y moratoria pactadas por obligación con
split real antes/después del vencimiento, validación de tope de usura 1.5×IBC, y obligaciones en USD
convertidas a pesos con la TRM ingresada por el abogado, Art. 874 C.Co.), **Sancionatorio**
```

a:

```
**Comercial** (Art. 884 C.Co., tasas remuneratoria y moratoria pactadas por obligación con
split real antes/después del vencimiento, validación de tope de usura 1.5×IBC, obligaciones en USD
convertidas a pesos con la TRM ingresada por el abogado (Art. 874 C.Co.), y anatocismo condicionado
(Art. 886 C.Co.: interés sobre interés, activado solo con demanda judicial o acuerdo posterior con al
menos un año de intereses vencidos, capitalizado periódicamente — nunca por defecto)), **Sancionatorio**
```

Y en el párrafo "🚧 En desarrollo" (línea 48), cambia:

```
🚧 **En desarrollo:** anatocismo comercial condicionado (Art. 886 C.Co.) y varios módulos más también
están pendientes. El motor de prescripción y caducidad
```

a:

```
🚧 **En desarrollo:** varios módulos más también están pendientes. El motor de prescripción y caducidad
```

- [ ] **Step 5: Actualizar `docs/GUIA_USUARIO.md`**

En `docs/GUIA_USUARIO.md`, dentro de la sección "5.7. Agregar una obligación comercial", justo después del
párrafo que empieza con "Si alguna tasa pactada..." (antes de la línea `### 5.8. Exportar la liquidación...`),
agrega:

```markdown

**Anatocismo condicionado (Art. 886 C.Co.):** por defecto, el interés siempre es simple. Si tu caso
cumple una de las dos condiciones legales que permiten cobrar interés sobre interés, marca uno de estos
dos campos (nunca ambos a la vez):

- **"Demanda judicial (habilita anatocismo, Art. 886 C.Co.)"**: si ya existe una demanda judicial. La
  capitalización empieza automáticamente un año después de la fecha de vencimiento.
- **"¿Hay acuerdo posterior de capitalización?"** + **"Fecha del acuerdo posterior"**: si en cambio hay un
  acuerdo entre las partes para capitalizar intereses, marca esta casilla e ingresa la fecha del acuerdo.
  Esa fecha debe ser al menos un año posterior a la fecha de vencimiento — si ingresas una fecha más
  temprana, el programa no deja liquidar y muestra el motivo.

Cuando el anatocismo está activo, el capital se recalcula capitalizando los intereses vencidos cada año
(desde la fecha habilitante) hasta la fecha de corte de la liquidación — el interés generado antes de ese
punto sigue siendo simple.
```

- [ ] **Step 6: Commit**

```bash
git add Pendientes.md README.md docs/GUIA_USUARIO.md
git commit -m "docs: close Sprint 19 (anatocismo comercial) in Pendientes.md, README and user guide"
```

---

## Plan Self-Review Notes

- **Spec coverage:** Task 1-2 cubren el motor (`BalanceEngine`/`LiquidationCore`); Task 3-4 cubren modelo +
  migración; Task 5 cubre validación (mutua exclusión, PUNTUAL-only, año de anterioridad del acuerdo); Task 6
  cubre la activación condicionada y el caso de abono intermedio; Task 7 cubre GUI; Task 8 cubre migración
  real + cierre de documentación. Todos los puntos de "Definición de hecho" del spec están cubiertos.
- **Placeholder scan:** ningún TBD/TODO; todo el código de cada paso está completo y ejecutable tal cual.
- **Type consistency:** `_fecha_capitalizacion_anatocismo` y `_eventos_anatocismo` (Task 6) reutilizan
  exactamente los mismos nombres de campo (`anatocismo_demanda_judicial`, `anatocismo_fecha_acuerdo`)
  definidos en Task 3, y el mismo `event_type` (`"CAPITALIZACION_INTERESES_ANATOCISMO"`) definido en Task 2.
