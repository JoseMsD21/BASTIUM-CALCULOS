# Sprint 11a — Motores de Interés Moratorio Tributario y Renta Líquida Gravable Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two standalone, tested calculation engines for BASTIUM's tax domain (Derecho Tributario/DIAN) — interés moratorio tributario (E.T. art. 635) and depuración de Renta Líquida Gravable — with no GUI wiring and no `TributarioStrategy`.

**Architecture:** Two new pure-calculation modules under a new `app/engine/tax/` package. The interest engine extends the existing historical IBC/Usura series (`app/engine/indexation/historical_index.py`, Sprint 5) with a new range-query function, then reuses the existing `MemoryRateProvider` + `EffectiveRateConverter` + `DailyInterest` building blocks (same pattern as `ComercialStrategy._construir_rate_provider` and `LiquidationCore._accrue_time_passage`) to resolve the tax moratory rate automatically by historical month instead of a manually pacted rate. The renta líquida engine is a dependency-free 8-step arithmetic pipeline.

**Tech Stack:** Python, `Decimal` for all money math, `pytest` for TDD.

**Spec:** `docs/superpowers/specs/2026-07-20-sprint11a-tributario-interes-renta-liquida-design.md`

---

### Task 1: `get_tramos_ibc_usura_between` in `historical_index.py`

**Files:**
- Modify: `app/engine/indexation/historical_index.py:518-529` (add new function right after `get_ibc_usura_for_date`)
- Test: `tests/engine/test_historical_index.py` (append at end of file, after line 173)

- [x] **Step 1: Write the failing tests**

Append to `tests/engine/test_historical_index.py`:

```python
from app.engine.indexation.historical_index import get_tramos_ibc_usura_between


def test_tramos_entre_rango_dentro_de_un_solo_tramo():
    tramos = get_tramos_ibc_usura_between(date(2026, 6, 5), date(2026, 6, 20))
    assert len(tramos) == 1
    assert tramos[0].inicio == date(2026, 6, 1)
    assert tramos[0].fin == date(2026, 6, 30)
    assert tramos[0].usura_anual == Decimal("28.79")


def test_tramos_entre_rango_que_cruza_dos_meses():
    tramos = get_tramos_ibc_usura_between(date(2026, 4, 29), date(2026, 5, 2))
    assert len(tramos) == 2
    assert tramos[0].inicio == date(2026, 4, 1) and tramos[0].fin == date(2026, 4, 30)
    assert tramos[0].usura_anual == Decimal("26.76")
    assert tramos[1].inicio == date(2026, 5, 1) and tramos[1].fin == date(2026, 5, 31)
    assert tramos[1].usura_anual == Decimal("28.17")


def test_tramos_fin_anterior_a_inicio_lanza_value_error():
    with pytest.raises(ValueError):
        get_tramos_ibc_usura_between(date(2026, 5, 2), date(2026, 4, 29))


def test_tramos_fuera_de_rango_disponible_lanza_value_error():
    with pytest.raises(ValueError):
        get_tramos_ibc_usura_between(date(1990, 1, 1), date(1990, 1, 5))
```

The file already imports `pytest`, `date`, `timedelta`, `Decimal` at the top (lines 1-2, 4) — only the new `get_tramos_ibc_usura_between` import needs adding, next to the existing `from app.engine.indexation.historical_index import (...)` block at lines 6-12 (add it to that same import tuple instead of a separate import line).

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/engine/test_historical_index.py -v -k tramos`
Expected: FAIL with `ImportError: cannot import name 'get_tramos_ibc_usura_between'`

- [x] **Step 3: Write minimal implementation**

Add to `app/engine/indexation/historical_index.py`, immediately after `get_ibc_usura_for_date` (after line 529):

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

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/engine/test_historical_index.py -v -k tramos`
Expected: 4 passed

- [x] **Step 5: Commit**

```bash
git add app/engine/indexation/historical_index.py tests/engine/test_historical_index.py
git commit -m "feat(tax): add get_tramos_ibc_usura_between for range queries over IBC/Usura history"
```

---

### Task 2: `app/engine/tax` package + `construir_rate_provider_moratorio_tributario`

**Files:**
- Create: `app/engine/tax/__init__.py` (empty, matches `app/engine/labor/__init__.py`)
- Create: `app/engine/tax/moratory_interest.py`
- Create: `tests/engine/tax/__init__.py` (empty, matches `tests/engine/labor/__init__.py`)
- Create: `tests/engine/tax/test_moratory_interest.py`

- [x] **Step 1: Create the empty package files**

```bash
mkdir -p app/engine/tax tests/engine/tax
touch app/engine/tax/__init__.py tests/engine/tax/__init__.py
```

- [x] **Step 2: Write the failing tests**

Create `tests/engine/tax/test_moratory_interest.py`:

```python
from datetime import date

import pytest

from app.engine.tax.moratory_interest import (
    FUENTE_MORATORIO_TRIBUTARIO,
    construir_rate_provider_moratorio_tributario,
)


def test_sin_mora_si_fecha_corte_no_supera_la_exigibilidad():
    provider = construir_rate_provider_moratorio_tributario(
        fecha_exigibilidad=date(2026, 6, 15), fecha_corte=date(2026, 6, 15)
    )
    with pytest.raises(ValueError):
        provider.get_rate(date(2026, 6, 16))


def test_un_solo_tramo_agrega_un_periodo_con_tasa_usura_menos_dos_puntos():
    provider = construir_rate_provider_moratorio_tributario(
        fecha_exigibilidad=date(2026, 6, 1), fecha_corte=date(2026, 6, 2)
    )
    rate = provider.get_rate(date(2026, 6, 2))
    # usura junio 2026 = 28.79% EA -> tributario = 26.79% EA (mismo ejemplo del PDF pag. 39)
    assert rate.decimal() == Decimal("0.000650518313")
    assert provider.get_rate_source(date(2026, 6, 2)) == FUENTE_MORATORIO_TRIBUTARIO


def test_rango_que_cruza_dos_meses_agrega_dos_periodos_con_tasas_distintas():
    provider = construir_rate_provider_moratorio_tributario(
        fecha_exigibilidad=date(2026, 4, 29), fecha_corte=date(2026, 5, 2)
    )
    # abril 2026: usura 26.76% -> tributario 24.76%
    assert provider.get_rate(date(2026, 4, 30)).decimal() == Decimal("0.000606270573")
    # mayo 2026: usura 28.17% -> tributario 26.17%
    assert provider.get_rate(date(2026, 5, 1)).decimal() == Decimal("0.000637079611")
    assert provider.get_rate(date(2026, 5, 2)).decimal() == Decimal("0.000637079611")


def test_rango_fuera_de_datos_disponibles_propaga_value_error():
    with pytest.raises(ValueError):
        construir_rate_provider_moratorio_tributario(
            fecha_exigibilidad=date(2026, 8, 1), fecha_corte=date(2026, 8, 5)
        )
```

Add `from decimal import Decimal` to the imports at the top of the test file (needed for the `Decimal(...)` assertions above).

- [x] **Step 3: Run tests to verify they fail**

Run: `python -m pytest tests/engine/tax/test_moratory_interest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.engine.tax.moratory_interest'`

- [x] **Step 4: Write minimal implementation**

Create `app/engine/tax/moratory_interest.py`:

```python
"""
Interes moratorio tributario (Estatuto Tributario, art. 635): tasa de usura
vigente (linea Consumo y Ordinario) menos dos puntos porcentuales. A
diferencia del interes moratorio comercial (que puede pactarse), esta tasa
nunca se pacta -- se deriva mecanicamente de la serie historica de usura de
la SFC. Por eso este motor resuelve la tasa automaticamente por tramos
historicos en vez de recibir una tasa manual (comparar con
ComercialStrategy._construir_rate_provider en app/services/area_strategy.py,
que sí usa una tasa pactada).

Ver docs/superpowers/specs/2026-07-20-sprint11a-tributario-interes-renta-liquida-design.md.
"""

from datetime import date, timedelta
from decimal import Decimal

from app.engine.indexation.historical_index import get_tramos_ibc_usura_between
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.provider import MemoryRateProvider
from app.engine.interest.rate_conversion import EffectiveRateConverter

PUNTOS_DESCUENTO_ET_635 = Decimal("2")

FUENTE_MORATORIO_TRIBUTARIO = "Interes moratorio tributario (E.T. art. 635): usura vigente - 2 puntos"


def construir_rate_provider_moratorio_tributario(
    fecha_exigibilidad: date, fecha_corte: date
) -> MemoryRateProvider:
    """Un RatePeriod diario por cada tramo historico de usura que se solape
    con el rango de mora [fecha_exigibilidad + 1 dia, fecha_corte] (la mora
    empieza el dia siguiente a la exigibilidad, mismo criterio que
    R-CIV-003). Si fecha_corte no supera ese inicio de mora, no hay mora:
    retorna un provider vacio."""
    provider = MemoryRateProvider()

    inicio_mora = fecha_exigibilidad + timedelta(days=1)
    if fecha_corte < inicio_mora:
        return provider

    tramos = get_tramos_ibc_usura_between(inicio_mora, fecha_corte)
    for tramo in tramos:
        inicio_segmento = max(tramo.inicio, inicio_mora)
        fin_segmento = min(tramo.fin, fecha_corte)
        tasa_anual_tributaria = tramo.usura_anual - PUNTOS_DESCUENTO_ET_635
        tasa_diaria = EffectiveRateConverter.annual_to_daily(tasa_anual_tributaria)
        provider.add_rate_period(
            start=inicio_segmento,
            end=fin_segmento,
            rate=tasa_diaria,
            source=FUENTE_MORATORIO_TRIBUTARIO,
        )
    return provider
```

- [x] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/engine/tax/test_moratory_interest.py -v`
Expected: 4 passed

- [x] **Step 6: Commit**

```bash
git add app/engine/tax tests/engine/tax
git commit -m "feat(tax): add construir_rate_provider_moratorio_tributario (E.T. art. 635)"
```

---

### Task 3: `calcular_interes_moratorio_tributario`

**Files:**
- Modify: `app/engine/tax/moratory_interest.py` (append function)
- Test: `tests/engine/tax/test_moratory_interest.py` (append tests)

- [x] **Step 1: Write the failing tests**

Append to `tests/engine/tax/test_moratory_interest.py`:

```python
from app.engine.tax.moratory_interest import calcular_interes_moratorio_tributario


def test_capital_cero_o_negativo_retorna_cero_sin_consultar_tramos():
    assert calcular_interes_moratorio_tributario(
        capital=Decimal("0.00"), fecha_exigibilidad=date(2026, 6, 1), fecha_corte=date(2026, 6, 2)
    ) == Decimal("0.00")


def test_fecha_corte_igual_a_exigibilidad_da_cero_dias_de_mora():
    assert calcular_interes_moratorio_tributario(
        capital=Decimal("1000000.00"), fecha_exigibilidad=date(2026, 6, 15), fecha_corte=date(2026, 6, 15)
    ) == Decimal("0.00")


def test_un_dia_de_mora_coincide_con_el_ejemplo_del_pdf_usura_28_79_ea():
    # PDF pag. 39: usura 28.79% EA -> interes moratorio tributario 26.79% EA
    total = calcular_interes_moratorio_tributario(
        capital=Decimal("1000000.00"), fecha_exigibilidad=date(2026, 6, 1), fecha_corte=date(2026, 6, 2)
    )
    assert total == Decimal("650.52")


def test_mora_que_cruza_dos_meses_suma_interes_de_cada_tramo():
    total = calcular_interes_moratorio_tributario(
        capital=Decimal("1000000.00"), fecha_exigibilidad=date(2026, 4, 29), fecha_corte=date(2026, 5, 2)
    )
    # abril 30 (606.27) + mayo 1 (637.08) + mayo 2 (637.08)
    assert total == Decimal("1880.43")
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/engine/tax/test_moratory_interest.py -v -k interes_moratorio_tributario`
Expected: FAIL with `ImportError: cannot import name 'calcular_interes_moratorio_tributario'`

- [x] **Step 3: Write minimal implementation**

Append to `app/engine/tax/moratory_interest.py`:

```python
def calcular_interes_moratorio_tributario(
    capital: Decimal, fecha_exigibilidad: date, fecha_corte: date
) -> Decimal:
    """Suma el interes moratorio tributario dia a dia (mismo patron que
    LiquidationCore._accrue_time_passage en app/engine/liquidation/engine.py)
    desde el dia siguiente a fecha_exigibilidad hasta fecha_corte. Capital
    fijo, sin abonos ni imputacion de pagos -- eso es Sprint 11b."""
    if capital <= Decimal("0.00"):
        return Decimal("0.00")

    provider = construir_rate_provider_moratorio_tributario(fecha_exigibilidad, fecha_corte)

    total = Decimal("0.00")
    current_day = fecha_exigibilidad + timedelta(days=1)
    while current_day <= fecha_corte:
        daily_rate = provider.get_rate(current_day)
        total += DailyInterest.calculate(capital=capital, daily_rate=daily_rate, days=1)
        current_day += timedelta(days=1)
    return total
```

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/engine/tax/test_moratory_interest.py -v`
Expected: 8 passed

- [x] **Step 5: Commit**

```bash
git add app/engine/tax/moratory_interest.py tests/engine/tax/test_moratory_interest.py
git commit -m "feat(tax): add calcular_interes_moratorio_tributario"
```

---

### Task 4: `app/engine/tax/renta_liquida.py`

**Files:**
- Create: `app/engine/tax/renta_liquida.py`
- Create: `tests/engine/tax/test_renta_liquida.py`

- [x] **Step 1: Write the failing tests**

Create `tests/engine/tax/test_renta_liquida.py`:

```python
from decimal import Decimal

from app.engine.tax.renta_liquida import depurar_renta_liquida_gravable


def test_flujo_base_sin_perdida_calcula_cada_paso_intermedio():
    resultado = depurar_renta_liquida_gravable(
        ingresos_brutos=Decimal("1000000.00"),
        devoluciones_rebajas_descuentos=Decimal("50000.00"),
        costos=Decimal("300000.00"),
        deducciones=Decimal("200000.00"),
        rentas_exentas=Decimal("100000.00"),
    )
    assert resultado.ingresos_netos == Decimal("950000.00")
    assert resultado.renta_bruta == Decimal("650000.00")
    assert resultado.renta_liquida == Decimal("450000.00")
    assert resultado.hubo_perdida_liquida is False
    assert resultado.renta_liquida_gravable == Decimal("350000.00")


def test_perdida_liquida_fija_renta_gravable_en_cero_sin_restar_exentas():
    resultado = depurar_renta_liquida_gravable(
        ingresos_brutos=Decimal("100000.00"),
        devoluciones_rebajas_descuentos=Decimal("0.00"),
        costos=Decimal("50000.00"),
        deducciones=Decimal("80000.00"),
        rentas_exentas=Decimal("10000.00"),
    )
    assert resultado.renta_liquida == Decimal("-30000.00")
    assert resultado.hubo_perdida_liquida is True
    assert resultado.renta_liquida_gravable == Decimal("0.00")


def test_rentas_exentas_mayores_a_renta_liquida_topa_en_cero_sin_quedar_negativa():
    resultado = depurar_renta_liquida_gravable(
        ingresos_brutos=Decimal("500000.00"),
        devoluciones_rebajas_descuentos=Decimal("0.00"),
        costos=Decimal("100000.00"),
        deducciones=Decimal("100000.00"),
        rentas_exentas=Decimal("400000.00"),
    )
    assert resultado.renta_liquida == Decimal("300000.00")
    assert resultado.hubo_perdida_liquida is False
    assert resultado.renta_liquida_gravable == Decimal("0.00")
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/engine/tax/test_renta_liquida.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.engine.tax.renta_liquida'`

- [x] **Step 3: Write minimal implementation**

Create `app/engine/tax/renta_liquida.py`:

```python
"""
Depuracion de Renta Liquida Gravable (Impuesto sobre la Renta): pipeline
aritmetico de 8 pasos, sin dependencias de tasas ni de UVT
(REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf, paginas 38-39).

Si la Renta Liquida (paso 6, antes de restar rentas exentas) da negativa, es
perdida liquida: la Renta Liquida Gravable se fija en 0 y no se restan
rentas exentas sobre un numero negativo (decision tomada con el usuario
durante el brainstorming). El mismo tope en 0 aplica si el resultado
quedara negativo despues de restar rentas exentas -- una renta liquida
gravable nunca es negativa en la practica real.

No modela compensacion de perdidas fiscales de anios anteriores (fuera de
alcance, no hay caso de uso que lo requiera en este sprint).

Ver docs/superpowers/specs/2026-07-20-sprint11a-tributario-interes-renta-liquida-design.md.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.engine.math.rounding import Rounding


@dataclass(frozen=True)
class RentaLiquidaGravableResult:
    ingresos_netos: Decimal
    renta_bruta: Decimal
    renta_liquida: Decimal
    hubo_perdida_liquida: bool
    renta_liquida_gravable: Decimal


def depurar_renta_liquida_gravable(
    ingresos_brutos: Decimal,
    devoluciones_rebajas_descuentos: Decimal,
    costos: Decimal,
    deducciones: Decimal,
    rentas_exentas: Decimal,
) -> RentaLiquidaGravableResult:
    ingresos_netos = Rounding.money(ingresos_brutos - devoluciones_rebajas_descuentos)
    renta_bruta = Rounding.money(ingresos_netos - costos)
    renta_liquida = Rounding.money(renta_bruta - deducciones)

    if renta_liquida < Decimal("0.00"):
        return RentaLiquidaGravableResult(
            ingresos_netos=ingresos_netos,
            renta_bruta=renta_bruta,
            renta_liquida=renta_liquida,
            hubo_perdida_liquida=True,
            renta_liquida_gravable=Decimal("0.00"),
        )

    renta_liquida_gravable = Rounding.money(max(Decimal("0.00"), renta_liquida - rentas_exentas))
    return RentaLiquidaGravableResult(
        ingresos_netos=ingresos_netos,
        renta_bruta=renta_bruta,
        renta_liquida=renta_liquida,
        hubo_perdida_liquida=False,
        renta_liquida_gravable=renta_liquida_gravable,
    )
```

- [x] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/engine/tax/test_renta_liquida.py -v`
Expected: 3 passed

- [x] **Step 5: Commit**

```bash
git add app/engine/tax/renta_liquida.py tests/engine/tax/test_renta_liquida.py
git commit -m "feat(tax): add depurar_renta_liquida_gravable (8-step renta liquida gravable pipeline)"
```

---

### Task 5: Update `Pendientes.md` and `docs/GUIA_USUARIO.md`

**Files:**
- Modify: `Pendientes.md:684-686`
- Modify: `docs/GUIA_USUARIO.md:615-616`

- [x] **Step 1: Update `Pendientes.md`**

Find this text (end of the Sprint 11 section, right before the `---` separator to Sprint 12):

```markdown
**Nota:** este sprint es el que menos detalle técnico tiene de los doce, a propósito — antes de invertir
tiempo de planificación fina, hay que confirmar que entra en el roadmap del producto.

---
```

Replace with:

```markdown
**Nota:** este sprint es el que menos detalle técnico tiene de los doce, a propósito — antes de invertir
tiempo de planificación fina, hay que confirmar que entra en el roadmap del producto.

**Estado:** Sprint 11a implementado (2026-07-20) — ver
`docs/superpowers/plans/2026-07-20-sprint11a-tributario-interes-renta-liquida.md` y
`docs/superpowers/specs/2026-07-20-sprint11a-tributario-interes-renta-liquida-design.md`. Decisión tomada
con el usuario durante el brainstorming previo: de las 5 piezas sugeridas arriba, este sprint construyó
únicamente las dos sin bloqueo de datos — `app/engine/tax/moratory_interest.py` (interés moratorio
tributario, E.T. art. 635, resuelto automáticamente por tramos históricos de usura vía
`historical_index.get_tramos_ibc_usura_between`) y `app/engine/tax/renta_liquida.py` (depuración de Renta
Líquida Gravable, pipeline de 8 pasos). Son motores de cálculo puros — sin `TributarioStrategy`, sin
registrar el área en `AREAS_DERECHO`, sin wiring de GUI — mismo patrón que `IPCIndexation` quedó
standalone hasta que el Sprint 8 lo conectó. **Sprint 11b** (motor de sanciones, imputación tributaria de
pagos, modelo de "Obligación Tributaria") sigue pendiente, bloqueado por la misma tabla histórica de UVT
que el Sprint 5 dejó sin conseguir.

---
```

- [x] **Step 2: Update `docs/GUIA_USUARIO.md`**

Find this text (section 8, "Funciones pendientes o en desarrollo"):

```markdown
- 🚧 **Derecho Tributario, TRM/moneda extranjera, motor de reglas configurable** — dominios nuevos, de
  menor prioridad, ver `Pendientes.md`, Sprints 11, 12 y 13.
```

Replace with:

```markdown
- 🚧 **Derecho Tributario** — dos motores de cálculo ya existen y están probados: interés moratorio
  tributario (E.T. art. 635, tasa de usura vigente menos dos puntos, resuelta automáticamente por tramos
  históricos) y depuración de Renta Líquida Gravable (el flujo de 8 pasos del impuesto de renta). Ninguno
  está conectado todavía a un área operable — no existe una estrategia de liquidación tributaria ni el
  área aparece en el selector de la GUI. Sanciones (extemporaneidad, inexactitud) e imputación tributaria
  de pagos siguen sin construir, bloqueadas por la falta de una tabla histórica de UVT (`Pendientes.md`,
  Sprint 11).
- 🚧 **TRM/moneda extranjera, motor de reglas configurable** — dominios nuevos, de menor prioridad, ver
  `Pendientes.md`, Sprints 12 y 13.
```

- [x] **Step 3: Commit**

```bash
git add Pendientes.md docs/GUIA_USUARIO.md
git commit -m "docs: mark Sprint 11a as implemented, document Sprint 11b as pending (UVT blocker)"
```

---

### Task 6: Full suite verification

**Files:** none (verification only)

- [x] **Step 1: Run the complete test suite**

Run: `python -m pytest -q`
Expected: all tests pass (no failures, no errors), including the new `tests/engine/tax/` package and the extended `tests/engine/test_historical_index.py`.

Result: 308 passed, 1 skipped (pre-existing, unrelated).

- [x] **Step 2: If everything is green, this plan is complete.** No further commit needed for this step — Task 5's commit is the closing commit of the sprint.
