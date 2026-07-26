# Sprint 17 — Módulo pensional (IBL, tasa de reemplazo, densidad de semanas) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three pure calculation functions (IBL, tasa de reemplazo, densidad de semanas) to
`app/engine/labor/ibl.py`, covering the pension-liquidation module that `Pendientes.md` Sprint 17
describes, with TDD tests including a real jurisprudence case (SL138-2024).

**Architecture:** Three standalone functions in one new file, no shared state, no new database tables, no
`PensionalStrategy`/GUI wiring (same standalone pattern as `app/engine/tax/*` from Sprint 11a). Reuses
`IPCIndexation.calculate`, `get_ipc_interpolado_for_date`, and `Rounding.money` — no new engine primitives.

**Tech Stack:** Python, `Decimal` for money-safe arithmetic, `pytest`, existing SQLAlchemy in-memory SQLite
test fixture pattern (for `IPC_INDICE_ACUMULADO` lookups via `parametro_service`).

**Reference:** Full design in
`docs/superpowers/specs/2026-07-26-sprint17-modulo-pensional-design.md`.

---

### Task 1: `calcular_ibl`

**Files:**
- Create: `app/engine/labor/ibl.py`
- Test: `tests/engine/labor/test_ibl.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/engine/labor/test_ibl.py`:

```python
from datetime import date, datetime as _dt, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _ipc_en_memoria(monkeypatch):
    # calcular_ibl usa get_ipc_interpolado_for_date, que lee IPC_INDICE_ACUMULADO
    # via parametro_service en cada llamada -- misma fixture aislada de disco
    # que tests/engine/labor/test_seguridad_social.py.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    indices = {
        2017: Decimal("100"), 2018: Decimal("105"), 2019: Decimal("110"),
        2020: Decimal("115"), 2021: Decimal("120"), 2022: Decimal("125"),
        2023: Decimal("130"), 2024: Decimal("135"), 2025: Decimal("140"),
        2026: Decimal("145"),
    }
    for anio, valor in indices.items():
        session.add(ParametroLegal(
            clave="IPC_INDICE_ACUMULADO", valor=valor, vigente_desde=date(anio, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    session.commit()
    session.close()


def test_calcular_ibl_historial_10_anios_con_ipc_variable():
    from app.engine.labor.ibl import calcular_ibl

    historial = [(date(anio, 12, 31), Decimal("1000000.00")) for anio in range(2017, 2027)]

    resultado = calcular_ibl(historial, fecha_calculo=date(2026, 12, 31))

    assert resultado == Decimal("1200351.01")


def test_calcular_ibl_historial_vacio_lanza_error():
    from app.engine.labor.ibl import calcular_ibl

    with pytest.raises(ValueError):
        calcular_ibl([], fecha_calculo=date(2026, 12, 31))
```

The expected value `1200351.01` comes from indexing a constant $1,000,000.00 monthly salary from each of
the 10 year-end dates (2017-12-31 .. 2026-12-31) up to 2026-12-31, using the seeded IPC index (100, 105,
110, ..., 145), then averaging. Each per-year indexed value (capital + `IPCIndexation.calculate` delta,
already rounded to cents):

| Año  | Índice | Indexado        |
|------|--------|-----------------|
| 2017 | 100    | 1,450,000.00    |
| 2018 | 105    | 1,380,952.38    |
| 2019 | 110    | 1,318,181.82    |
| 2020 | 115    | 1,260,869.57    |
| 2021 | 120    | 1,208,333.33    |
| 2022 | 125    | 1,160,000.00    |
| 2023 | 130    | 1,115,384.62    |
| 2024 | 135    | 1,074,074.07    |
| 2025 | 140    | 1,035,714.29    |
| 2026 | 145    | 1,000,000.00    |

Sum = 12,003,510.08 → ÷ 10 = 1,200,351.008 → `Rounding.money` (ROUND_HALF_UP) → **1,200,351.01**.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/engine/labor/test_ibl.py -v`
Expected: FAIL (or ERROR) with `ModuleNotFoundError: No module named 'app.engine.labor.ibl'`

- [ ] **Step 3: Write the implementation**

Create `app/engine/labor/ibl.py`:

```python
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.engine.indexation.historical_index import get_ipc_interpolado_for_date
from app.engine.indexation.ipc import IPCIndexation
from app.engine.math.rounding import Rounding


def calcular_ibl(
    historial_salarios: list[tuple[date, Decimal]],
    fecha_calculo: date,
) -> Decimal:
    """Promedio de los salarios cotizados, cada uno indexado por IPC desde su
    fecha hasta fecha_calculo (PDF pag. 52). El historial ya debe venir acotado
    a los ultimos 10 anios cotizados -- esta funcion no filtra por fecha, solo
    indexa y promedia lo que reciba."""
    if not historial_salarios:
        raise ValueError("El historial de salarios no puede estar vacio.")

    indice_final = get_ipc_interpolado_for_date(fecha_calculo)
    total = Decimal("0.00")
    for fecha, salario in historial_salarios:
        indice_inicial = get_ipc_interpolado_for_date(fecha)
        total += salario + IPCIndexation.calculate(salario, indice_inicial, indice_final)

    return Rounding.money(total / len(historial_salarios))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/engine/labor/test_ibl.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/engine/labor/ibl.py tests/engine/labor/test_ibl.py
git commit -m "feat: add calcular_ibl (Sprint 17, IPC-indexed pension income base)"
```

---

### Task 2: `calcular_tasa_reemplazo`

**Files:**
- Modify: `app/engine/labor/ibl.py`
- Test: `tests/engine/labor/test_ibl.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/engine/labor/test_ibl.py`:

```python
def test_tasa_reemplazo_s_uno_sin_bono_toca_el_piso_exacto():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("1000000.00"), smlmv_vigente=Decimal("1000000.00"), semanas_cotizadas=1300,
    )

    assert resultado == Decimal("65.00")


def test_tasa_reemplazo_s_uno_con_bono_de_dos_bloques():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("1000000.00"), smlmv_vigente=Decimal("1000000.00"), semanas_cotizadas=1400,
    )

    assert resultado == Decimal("68.00")


def test_tasa_reemplazo_s_alto_sin_bono_no_baja_del_piso_65():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("10000000.00"), smlmv_vigente=Decimal("1000000.00"), semanas_cotizadas=1300,
    )

    assert resultado == Decimal("65.00")


def test_tasa_reemplazo_bono_grande_no_sube_del_techo_80():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("2000000.00"), smlmv_vigente=Decimal("1000000.00"), semanas_cotizadas=3800,
    )

    assert resultado == Decimal("80.00")


def test_tasa_reemplazo_smlmv_cero_lanza_error():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    with pytest.raises(ValueError):
        calcular_tasa_reemplazo(
            ibl=Decimal("1000000.00"), smlmv_vigente=Decimal("0.00"), semanas_cotizadas=1300,
        )
```

Expected-value check: `s = ibl / smlmv_vigente`, `r = 65.5 - 0.5*s`, bono `= ((semanas - 1300) // 50) * 1.5`
when `semanas > 1300`, then clamp to `[65, 80]`.
- Case 1: `s=1` → `r=65.0` (already at floor, no clamp needed) → `65.00`.
- Case 2: `s=1`, semanas=1400 → bono = `(100 // 50) * 1.5 = 3.0` → `r = 65.0 + 3.0 = 68.00`.
- Case 3: `s=10`, semanas=1300 (no bono) → `r_base = 65.5 - 5.0 = 60.5` → floor clamps to `65.00`.
- Case 4: `s=2`, semanas=3800 → bono = `(2500 // 50) * 1.5 = 75.0` → `r_base = 65.5 - 1.0 = 64.5` →
  `64.5 + 75.0 = 139.5` → cap clamps to `80.00`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/engine/labor/test_ibl.py -v -k tasa_reemplazo`
Expected: FAIL with `ImportError: cannot import name 'calcular_tasa_reemplazo'`

- [ ] **Step 3: Write the implementation**

Append to `app/engine/labor/ibl.py`:

```python
def calcular_tasa_reemplazo(
    ibl: Decimal,
    smlmv_vigente: Decimal,
    semanas_cotizadas: int,
) -> Decimal:
    """Formula R completa (Ley 100 de 1993, art. 34; el PDF de BASTIUM solo
    trae la linea base r = 65.5 - 0.5*s, ver Preguntas-Para-Abogado.md, Sprint
    17): piso 65%, techo 80%, bono +1.5% por cada 50 semanas sobre 1300."""
    if smlmv_vigente <= Decimal("0.00"):
        raise ValueError("El SMLMV vigente debe ser positivo.")

    s = ibl / smlmv_vigente
    r = Decimal("65.5") - Decimal("0.5") * s

    if semanas_cotizadas > 1300:
        bloques_50_semanas = (semanas_cotizadas - 1300) // 50
        r += Decimal(bloques_50_semanas) * Decimal("1.5")

    r = max(Decimal("65"), min(Decimal("80"), r))
    return Rounding.money(r)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/engine/labor/test_ibl.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add app/engine/labor/ibl.py tests/engine/labor/test_ibl.py
git commit -m "feat: add calcular_tasa_reemplazo (Sprint 17, Ley 100 art. 34 formula)"
```

---

### Task 3: `calcular_densidad_semanas`

**Files:**
- Modify: `app/engine/labor/ibl.py`
- Test: `tests/engine/labor/test_ibl.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/engine/labor/test_ibl.py`:

```python
def test_densidad_semanas_calendario_real_vs_ano_comercial_360():
    from app.engine.labor.ibl import calcular_densidad_semanas

    periodo = [(date(2024, 1, 1), date(2025, 2, 1))]  # 13 meses cruzando un ano bisiesto (2024)

    semanas_calendario_real = calcular_densidad_semanas(periodo)

    # Metodo pre-SL138-2024 (ano comercial de 360, mes de 30 dias): 13*30=390 dias.
    dias_ano_comercial_360 = 13 * 30
    semanas_ano_comercial_360 = round(dias_ano_comercial_360 / 7)

    assert semanas_calendario_real == 57  # (2025-02-01 - 2024-01-01).days == 397; 397/7 = 56.71 -> 57
    assert semanas_ano_comercial_360 == 56
    assert semanas_calendario_real != semanas_ano_comercial_360  # documenta la diferencia real de 1 semana


def test_densidad_semanas_caso_real_sentencia_sl138_2024():
    from app.engine.labor.ibl import calcular_densidad_semanas

    inicio = date(2020, 1, 1)
    fin = inicio + timedelta(days=348)  # caso citado en la Sentencia SL138-2024

    resultado = calcular_densidad_semanas([(inicio, fin)])

    assert resultado == 50  # 348/7 = 49.71 -> redondea a 50 (segun la sentencia)


def test_densidad_semanas_periodos_solapados_no_se_cuentan_doble():
    from app.engine.labor.ibl import calcular_densidad_semanas

    periodos = [
        (date(2023, 1, 1), date(2023, 1, 31)),
        (date(2023, 1, 15), date(2023, 2, 15)),  # se solapa 17 dias con el anterior
    ]

    resultado = calcular_densidad_semanas(periodos)

    assert resultado == 6  # union (2023-01-01, 2023-02-15) = 45 dias -> 45/7 = 6.43 -> 6, no 9


def test_densidad_semanas_lista_vacia_retorna_cero():
    from app.engine.labor.ibl import calcular_densidad_semanas

    assert calcular_densidad_semanas([]) == 0


def test_densidad_semanas_periodo_invalido_lanza_error():
    from app.engine.labor.ibl import calcular_densidad_semanas

    with pytest.raises(ValueError):
        calcular_densidad_semanas([(date(2023, 2, 1), date(2023, 1, 1))])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/engine/labor/test_ibl.py -v -k densidad_semanas`
Expected: FAIL with `ImportError: cannot import name 'calcular_densidad_semanas'`

- [ ] **Step 3: Write the implementation**

Append to `app/engine/labor/ibl.py`:

```python
def calcular_densidad_semanas(periodos_cotizados: list[tuple[date, date]]) -> int:
    """Semanas de cotizacion en dias calendario reales (365/366), no dias
    habiles ni ano comercial de 360 (Sentencia SL138-2024). Los periodos
    solapados se unen antes de contar, para no cotizar "doble" el mismo dia
    calendario."""
    if not periodos_cotizados:
        return 0
    for inicio, fin in periodos_cotizados:
        if fin < inicio:
            raise ValueError(f"Periodo invalido: fin ({fin}) es anterior a inicio ({inicio}).")

    periodos_ordenados = sorted(periodos_cotizados)
    fusionados: list[tuple[date, date]] = [periodos_ordenados[0]]
    for inicio, fin in periodos_ordenados[1:]:
        ultimo_inicio, ultimo_fin = fusionados[-1]
        if inicio <= ultimo_fin:
            fusionados[-1] = (ultimo_inicio, max(ultimo_fin, fin))
        else:
            fusionados.append((inicio, fin))

    dias_totales = sum((fin - inicio).days for inicio, fin in fusionados)
    semanas = (Decimal(dias_totales) / Decimal("7")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(semanas)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/engine/labor/test_ibl.py -v`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add app/engine/labor/ibl.py tests/engine/labor/test_ibl.py
git commit -m "feat: add calcular_densidad_semanas (Sprint 17, SL138-2024 calendar-day count)"
```

---

### Task 4: Close out the sprint — update `Pendientes.md` and run the full suite

**Files:**
- Modify: `Pendientes.md` (Sprint 17 section)

- [ ] **Step 1: Add the "Estado" note to Sprint 17**

In `Pendientes.md`, find the Sprint 17 section's `**Definición de Hecho:**` block (ends with "Suite
completa en verde.") and the `---` separator right after it, right before "## Sprint 18". Insert a new
`**Estado:**` paragraph between them (same pattern as every other completed sprint in this file):

```markdown
**Estado:** Implementado (2026-07-26) — ver
`docs/superpowers/plans/2026-07-26-sprint17-modulo-pensional.md` y
`docs/superpowers/specs/2026-07-26-sprint17-modulo-pensional-design.md`. Se agregaron las 3 funciones puras
en `app/engine/labor/ibl.py` (`calcular_ibl`, `calcular_tasa_reemplazo`, `calcular_densidad_semanas`), sin
`PensionalStrategy` ni wiring de GUI (mismo patrón standalone que `app/engine/tax/*` del Sprint 11a).
Decisiones tomadas con el usuario durante el brainstorming previo: (a) el IBL recibe historial mensual
(hasta 120 registros), no anual; (b) la densidad de semanas une periodos solapados antes de contar, para no
cotizar "doble" el mismo día; (c) la tasa de reemplazo implementa la fórmula completa real (Ley 100 art.
34: piso 65%, techo 80%, bono +1.5% por cada 50 semanas sobre 1.300), no solo la línea base que trae el PDF
de BASTIUM — el hueco entre ambas quedó documentado en `Preguntas-Para-Abogado.md` (sección Sprint 17) para
confirmación jurídica formal; (d) el caso de validación real usado en los tests es la Sentencia SL138-2024
(348 días calendario → 49,71 semanas → 50), en vez de un caso aportado directamente por el usuario. Se creó
además `Preguntas-Para-Abogado.md` (documento nuevo en la raíz del proyecto), que recoge esta brecha junto
con todas las decisiones/huecos legales sin confirmar de los Sprints 2-16, 18 y 30.
```

- [ ] **Step 2: Run the full test suite**

Run: `python -m pytest -q`
Expected: All tests pass (previous suite count + 12 new tests), 0 failed.

- [ ] **Step 3: Commit**

```bash
git add Pendientes.md
git commit -m "docs: close Sprint 17 (modulo pensional) in Pendientes.md"
```

---

## Self-review notes

- **Spec coverage:** `calcular_ibl` (Task 1), `calcular_tasa_reemplazo` with piso/techo/bono (Task 2),
  `calcular_densidad_semanas` with the calendar-vs-360 comparison and the SL138-2024 real case (Task 3),
  and the `Pendientes.md` close-out (Task 4) — all four Definición de Hecho items from the design spec are
  covered.
- **No placeholders:** every step has literal code and exact expected values (no "add tests for the
  above").
- **Type consistency:** `calcular_ibl(historial_salarios: list[tuple[date, Decimal]], fecha_calculo: date)
  -> Decimal`, `calcular_tasa_reemplazo(ibl: Decimal, smlmv_vigente: Decimal, semanas_cotizadas: int) ->
  Decimal`, `calcular_densidad_semanas(periodos_cotizados: list[tuple[date, date]]) -> int` are used
  identically across Tasks 1-3 and match the design spec.
