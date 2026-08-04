# Sprint 27 — Limpieza de dependencias no usadas y código muerto adicional — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve the 7 findings in `Pendientes.md` Sprint 27: drop 7 unused packages from `requirements.txt`, delete 20 zero-byte dead files (14 source + 6 test) and 1 dead test with an empty `parametrize`, fix two real bugs in code that is being **kept** (`FinancialParser.parse_money`'s incorrect assumption of Colombian number format, and `LegalTextExtractor.validate_and_fill`'s blocking `stdin` read), fix `BastiumChartGenerator`'s `os.getcwd()` usage to use `pathlib.Path`, and leave `app/views/about.py` / `app/views/reportes.py` as documented placeholders (same treatment as `app/views/dashboard.py`, claimed by Sprint 33).

**Architecture:** Mix of pure deletions (no behavior change, existing suite is the regression net) and two real bug fixes done via TDD (new tests written first, confirmed failing, then implementation). No new features. Every task is independently committable. `Pendientes.md` is NOT touched — the human orchestrator updates it centrally after merging all parallel sprints.

**Tech Stack:** Python 3.14, PySide6 (Qt), pytest, SQLAlchemy, ruff (line-length 99, rules E/F/I/UP/B).

**Baseline (must reproduce before Task 1):**
```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q
```
Expected: `687 passed, 1 skipped` (the 1 skip is `test_areas_no_implementadas_lanzan_error_claro_al_liquidar`, `SKIPPED (got empty parameter set)` — this is exactly the test Task 1 removes).

Ruff baseline (pre-existing, out of scope — do not fix unrelated errors): `412 errors` (383 `E501` line-too-long, 13 `E402`, 4 `B011`, 4 `UP042`, 3 `B904`, 3 `B905`, 1 `B008`, 1 `F841`), all in files this sprint does not touch except `app/engine/math/parsers.py` (2 of the 3 `B904` hits — both get fixed as a side effect of Task 4's rewrite) and `app/engine/text/nlp_extractor.py` / `app/reports/charts.py` (a handful of `E501` — fixed as a side effect of Tasks 5/6 rewriting those files).

---

### Task 1: Delete the dead empty-parametrize test (hallazgo 4)

**Context:** `tests/services/test_area_strategy.py:156-165` has `@pytest.mark.parametrize("area_name,strategy_cls", [])` — an empty parameter list. pytest reports this as `SKIPPED (got empty parameter set)`; it verifies nothing. It used to check that *unimplemented* areas raised `AreaNoImplementadaError`, but all 6 areas have been implemented since Sprint 15. `AreaNoImplementadaError` is imported at the top of the file (`app/core/exceptions.py`) solely for this test — grep confirms no other use in this file, so the import must be removed too or ruff's `F401` (unused import) will fire.

**Files:**
- Modify: `tests/services/test_area_strategy.py:10` (remove unused import)
- Modify: `tests/services/test_area_strategy.py:156-166` (remove the whole test + decorator)

- [ ] **Step 1: Confirm `AreaNoImplementadaError` has no other use in the file**

```bash
grep -n "AreaNoImplementadaError" "tests/services/test_area_strategy.py"
```

Expected: exactly two hits — the import line and the `pytest.raises(AreaNoImplementadaError)` line inside the test being deleted.

- [ ] **Step 2: Remove the import**

In `tests/services/test_area_strategy.py`, remove line 10:
```python
from app.core.exceptions import AreaNoImplementadaError
```
(Leave the rest of the `from app.core...`/`from app.engine...` import block untouched — only this one line goes.)

- [ ] **Step 3: Remove the dead test and its decorator**

Replace:
```python
def test_civil_familia_es_la_unica_area_operable():
    strategy = AreaRegistry.get_strategy("CIVIL_FAMILIA")
    assert isinstance(strategy, CivilFamiliaStrategy)


@pytest.mark.parametrize(
    "area_name,strategy_cls",
    [
    ],
)
def test_areas_no_implementadas_lanzan_error_claro_al_liquidar(area_name, strategy_cls):
    strategy = AreaRegistry.get_strategy(area_name)
    assert isinstance(strategy, strategy_cls)
    with pytest.raises(AreaNoImplementadaError):
        strategy.liquidar(obligaciones=[], abonos=[], fecha_corte=None)


from datetime import date, timedelta
```

With:
```python
def test_civil_familia_es_la_unica_area_operable():
    strategy = AreaRegistry.get_strategy("CIVIL_FAMILIA")
    assert isinstance(strategy, CivilFamiliaStrategy)


from datetime import date, timedelta
```

(The stray mid-file `from datetime import date, timedelta` import that immediately follows is pre-existing and out of scope for this sprint — leave it exactly as-is, just preserve it after the deletion.)

- [ ] **Step 4: Run the file's tests and confirm no more skips**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q tests/services/test_area_strategy.py
```

Expected: all tests pass, zero skipped.

- [ ] **Step 5: Run the full suite**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q
```

Expected: `686 passed, 0 skipped` (687 - 1 dead test, and the skip is gone).

- [ ] **Step 6: Run ruff on the modified file**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check tests/services/test_area_strategy.py
```

Expected: no new errors introduced (pre-existing `E501` lines elsewhere in the file, if any, are out of scope).

- [ ] **Step 7: Commit**

```bash
git add tests/services/test_area_strategy.py
git commit -m "test(sprint27): eliminar test con parametrize vacio que no verificaba nada"
```

---

### Task 2: Delete the 14 zero-byte source files and 6 zero-byte test files (hallazgos 5, 6)

**Context:** All 20 files are 0 bytes, dated 2026-07-04/05 (pre-Sprint-1 scaffold), and confirmed via grep to have zero references anywhere in the repo (`app`, `tests`, `docs`, `database`, `scripts`) — same pattern as `app/engine/allocation/allocator.py` and `app/engine/financial/allocation.py`, already deleted in Sprint 22. Re-verify before deleting, per the sprint's own instruction.

**Files to delete:**
- `app/core/settings.py`, `app/core/types.py`, `app/core/__init_.py`
- `app/engine/financial/balance.py`, `date_range.py`, `event.py`, `period.py`, `statement.py`, `timeline.py`
- `app/engine/payments/fifo.py`, `payment_distribution.py`
- `app/engine/reports/chart_builder.py`
- `app/engine/time/dates.py`, `period.py`
- `tests/engine/test_dates.py`, `test_event.py`, `test_period.py`, `test_timeline.py`
- `tests/financial/test_balance.py`, `test_statement.py`

- [ ] **Step 1: Re-verify zero references for every file about to be deleted**

```bash
grep -rn "core\.settings\|core\.types\|core\.__init_\|financial\.balance\|financial\.date_range\|financial\.event\|financial\.period\|financial\.statement\|financial\.timeline\|payments\.fifo\|payments\.payment_distribution\|reports\.chart_builder\|engine\.time\.dates\|engine\.time\.period" app tests database scripts docs Pendientes.md README.md 2>/dev/null
```

Expected: no output (already confirmed during planning — re-run here as the safety check the sprint brief requires).

- [ ] **Step 2: Confirm each file is genuinely 0 bytes right before deleting**

```bash
wc -c app/core/settings.py app/core/types.py "app/core/__init_.py" app/engine/financial/balance.py app/engine/financial/date_range.py app/engine/financial/event.py app/engine/financial/period.py app/engine/financial/statement.py app/engine/financial/timeline.py app/engine/payments/fifo.py app/engine/payments/payment_distribution.py app/engine/reports/chart_builder.py app/engine/time/dates.py app/engine/time/period.py tests/engine/test_dates.py tests/engine/test_event.py tests/engine/test_period.py tests/engine/test_timeline.py tests/financial/test_balance.py tests/financial/test_statement.py
```

Expected: `0` for every listed file.

- [ ] **Step 3: Delete the source files**

```bash
rm -f "app/core/settings.py" "app/core/types.py" "app/core/__init_.py"
rm -f "app/engine/financial/balance.py" "app/engine/financial/date_range.py" "app/engine/financial/event.py" "app/engine/financial/period.py" "app/engine/financial/statement.py" "app/engine/financial/timeline.py"
rm -f "app/engine/payments/fifo.py" "app/engine/payments/payment_distribution.py"
rm -f "app/engine/reports/chart_builder.py"
rm -f "app/engine/time/dates.py" "app/engine/time/period.py"
```

- [ ] **Step 4: Delete the test files**

```bash
rm -f "tests/engine/test_dates.py" "tests/engine/test_event.py" "tests/engine/test_period.py" "tests/engine/test_timeline.py"
rm -f "tests/financial/test_balance.py" "tests/financial/test_statement.py"
```

- [ ] **Step 5: Run the full suite**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q
```

Expected: `686 passed, 0 skipped` (unchanged from Task 1 — these files exercised nothing and were collected without contributing any test).

- [ ] **Step 6: Commit**

```bash
git add -A app/core/settings.py app/core/types.py "app/core/__init_.py" app/engine/financial/balance.py app/engine/financial/date_range.py app/engine/financial/event.py app/engine/financial/period.py app/engine/financial/statement.py app/engine/financial/timeline.py app/engine/payments/fifo.py app/engine/payments/payment_distribution.py app/engine/reports/chart_builder.py app/engine/time/dates.py app/engine/time/period.py tests/engine/test_dates.py tests/engine/test_event.py tests/engine/test_period.py tests/engine/test_timeline.py tests/financial/test_balance.py tests/financial/test_statement.py
git commit -m "chore(sprint27): eliminar 14 archivos fuente y 6 de test de 0 bytes (scaffold pre-Sprint-1 sin usar)"
```

(Note: `git add` on deleted paths stages the deletion.)

---

### Task 3: Remove 7 unused packages from `requirements.txt` (hallazgo 1)

**Context:** Grep across `app/`, `database/`, `scripts/`, `tests/` confirms zero imports of `fastapi`, `uvicorn`, `pandas`, `numpy`, `openpyxl`, `pydantic`, `alembic`. `alembic` has no `alembic.ini`/migrations folder — migrations are hand-written scripts, a decision already made in Sprint 5. `rich` and `matplotlib` stay (real imports in `nlp_extractor.py`/`charts.py`, which this sprint keeps and fixes, not deletes — see Tasks 5/6).

**Files:**
- Modify: `requirements.txt`

Current content:
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
holidays
ruff
```

- [ ] **Step 1: Re-verify zero imports for each package about to be removed**

```bash
grep -rEn "^\s*(import|from)\s+(fastapi|uvicorn|pandas|numpy|openpyxl|pydantic|alembic)\b" app database scripts tests
```

Expected: no output.

- [ ] **Step 2: Rewrite `requirements.txt`**

Replace the full file content with:
```
sqlalchemy
python-docx
reportlab
rich
matplotlib
PySide6
pytest
pytest-qt
holidays
ruff
```

- [ ] **Step 3: Confirm the app still imports cleanly (smoke import of the main packages actually used)**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -c "import sqlalchemy, docx, reportlab, rich, matplotlib, PySide6, pytest, holidays; print('ok')"
```

Expected: `ok` (this only proves the packages the venv already has installed still import — `requirements.txt` itself is just a declaration file, this sprint does not reinstall the venv).

- [ ] **Step 4: Run the full suite**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q
```

Expected: `686 passed, 0 skipped` (unchanged — `requirements.txt` is not imported by anything at runtime).

- [ ] **Step 5: Commit**

```bash
git add requirements.txt
git commit -m "chore(sprint27): quitar 7 paquetes sin uso de requirements.txt (fastapi, uvicorn, pandas, numpy, openpyxl, pydantic, alembic)"
```

---

### Task 4: Fix `FinancialParser.parse_money`'s Colombian-format-only bug (hallazgo 3, TDD)

**Context:** `app/engine/math/parsers.py:35-42` unconditionally strips every `.` (assuming it's a thousands separator) and converts `,` to `.` (assuming it's the decimal separator) — pure Colombian format. A US-formatted amount like `"5000000.00"` becomes `Decimal("500000000.00")` after `.replace('.', '')` — 100x too large. This is currently dead code (no caller in `app/`), but Task 5 wires `nlp_extractor.py`'s `FinancialParser.parse_money` calls back to life as a *kept, documented-orphan* module, so the bug must be fixed for real, not just noted. Per TDD, tests come first.

**Files:**
- Test: `tests/core/test_parsers.py` (new — mirrors the existing convention: `app/engine/math/*.py` is tested under `tests/core/`, see `tests/core/test_percentage.py`, `test_money.py`, `test_calculator.py`, `test_rounding.py`)
- Modify: `app/engine/math/parsers.py:34-42` (`FinancialParser.parse_money`)

- [ ] **Step 1: Write the failing tests**

Create `tests/core/test_parsers.py`:
```python
from decimal import Decimal

import pytest

from app.engine.math.parsers import FinancialParser


def test_parse_money_formato_colombiano_con_miles_y_decimales():
    assert FinancialParser.parse_money("$ 5.000.000,00") == Decimal("5000000.00")


def test_parse_money_formato_us_con_miles_y_decimales():
    assert FinancialParser.parse_money("$5,000,000.00") == Decimal("5000000.00")


def test_parse_money_formato_colombiano_solo_coma_decimal():
    assert FinancialParser.parse_money("5000000,50") == Decimal("5000000.50")


def test_parse_money_formato_us_solo_punto_decimal_no_se_infla_100x():
    # Bug real corregido en el Sprint 27: antes se interpretaba como
    # 500000000.00 (100x mas grande) al asumir formato colombiano siempre
    # y remover el punto como si fuera separador de miles.
    assert FinancialParser.parse_money("5000000.00") == Decimal("5000000.00")


def test_parse_money_formato_colombiano_solo_puntos_de_miles_sin_decimales():
    assert FinancialParser.parse_money("5.000.000") == Decimal("5000000")


def test_parse_money_un_solo_punto_de_miles_colombiano_tres_digitos():
    assert FinancialParser.parse_money("5.000") == Decimal("5000")


def test_parse_money_sin_separadores():
    assert FinancialParser.parse_money("5000000") == Decimal("5000000")


def test_parse_money_texto_invalido_lanza_value_error():
    with pytest.raises(ValueError):
        FinancialParser.parse_money("no es un monto")
```

- [ ] **Step 2: Run the tests and confirm the US-format one fails**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q tests/core/test_parsers.py -v
```

Expected: `test_parse_money_formato_us_solo_punto_decimal_no_se_infla_100x` FAILS (`Decimal('500000000.00') != Decimal('5000000.00')`); the rest pass by coincidence since the current unconditional-Colombian logic happens to also handle those inputs correctly.

- [ ] **Step 3: Rewrite `parse_money` with format detection**

Replace:
```python
    @staticmethod
    def parse_money(text: str) -> Decimal:
        # Remueve símbolos de moneda y separadores de miles (puntos), cambia coma decimal a punto
        clean_text = text.replace('$', '').replace(' ', '')
        # Si el formato colombiano es 5.000.000,00 -> removemos puntos y cambiamos coma a punto
        clean_text = clean_text.replace('.', '').replace(',', '.')
        try:
            return Decimal(clean_text)
        except InvalidOperation:
            raise ValueError(f"Monto financiero inválido: {text}")
```

With:
```python
    @staticmethod
    def parse_money(text: str) -> Decimal:
        """Convierte un monto en texto a Decimal exacto.

        Detecta el separador decimal en vez de asumir siempre el formato
        colombiano de forma incondicional (bug corregido en el Sprint 27: un
        monto en formato US como "5000000.00" se interpretaba 100x más
        grande al remover el punto como si fuera separador de miles).
        Reglas de detección (formato colombiano como valor por defecto en
        los casos ambiguos, igual que antes):

        - Si el texto trae punto Y coma, el que aparece más a la derecha es
          el separador decimal (ej. "5.000.000,50" -> colombiano;
          "5,000,000.50" -> US).
        - Si solo trae coma, se asume coma decimal (formato colombiano,
          ej. "5000000,50").
        - Si solo trae punto:
            - más de un punto -> son separadores de miles colombianos
              (ej. "5.000.000" -> 5000000).
            - un solo punto con exactamente 3 dígitos después -> separador
              de miles colombiano sin parte decimal (ej. "5.000" -> 5000).
            - un solo punto con 1, 2 o 4+ dígitos después -> punto decimal
              (ej. "5000000.00" -> 5000000.00).
        - Sin punto ni coma -> el texto ya es un número plano.
        """
        clean_text = text.replace('$', '').replace(' ', '').strip()

        has_dot = '.' in clean_text
        has_comma = ',' in clean_text

        if has_dot and has_comma:
            if clean_text.rfind(',') > clean_text.rfind('.'):
                normalized = clean_text.replace('.', '').replace(',', '.')
            else:
                normalized = clean_text.replace(',', '')
        elif has_comma:
            normalized = clean_text.replace(',', '.')
        elif has_dot:
            partes = clean_text.split('.')
            if len(partes) > 2 or len(partes[-1]) == 3:
                normalized = clean_text.replace('.', '')
            else:
                normalized = clean_text
        else:
            normalized = clean_text

        try:
            return Decimal(normalized)
        except InvalidOperation as error:
            raise ValueError(f"Monto financiero inválido: {text}") from error
```

- [ ] **Step 4: Run the tests again and confirm all pass**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q tests/core/test_parsers.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Run ruff on the modified file**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check app/engine/math/parsers.py tests/core/test_parsers.py
```

Expected: no errors (the `raise ... from error` fixes the pre-existing `B904` on this method; `parse_percentage`'s own `B904`, untouched, is out of scope).

- [ ] **Step 6: Run the full suite**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q
```

Expected: `694 passed, 0 skipped` (686 + 8 new tests).

- [ ] **Step 7: Commit**

```bash
git add app/engine/math/parsers.py tests/core/test_parsers.py
git commit -m "fix(sprint27): FinancialParser.parse_money detecta formato US vs colombiano en vez de asumir siempre colombiano"
```

---

### Task 5: Fix `LegalTextExtractor.validate_and_fill`'s blocking `stdin` read (hallazgo 2a, TDD)

**Context:** `app/engine/text/nlp_extractor.py` is a fully orphaned module (no caller in `app/`), kept intentionally for a future integration (importing legal facts from free text). `validate_and_fill` currently calls `rich.prompt.Prompt.ask()` directly, which blocks on `stdin` — if this class were ever wired to the GUI without changing it first, it would hang forever on a Windows executable with no attached console (no interactive `stdin`). Fix: accept an injectable `prompt_fn` callback so a future caller (CLI, GUI dialog, test) decides how to supply the missing value; the *default* `prompt_fn` still uses `rich.prompt.Prompt` for the CLI use case, but only calls it when `sys.stdin.isatty()` is true — otherwise it raises `DatoFaltanteError` immediately instead of blocking. This keeps `rich` genuinely used (consistent with keeping it in `requirements.txt`, Task 3) while eliminating the hang risk described in the sprint finding.

Per the project's convention, all custom exceptions live in `app/core/exceptions.py` (see the 7 existing `XxxError(Exception)` classes there) — `DatoFaltanteError` is added there, not defined locally in `nlp_extractor.py`.

**Files:**
- Modify: `app/core/exceptions.py` (add `DatoFaltanteError`)
- Test: `tests/engine/text/test_nlp_extractor.py` (new)
- Modify: `app/engine/text/nlp_extractor.py` (rewrite `validate_and_fill`, add module docstring)

- [ ] **Step 1: Add the new exception to `app/core/exceptions.py`**

Append to the end of the file:
```python


class DatoFaltanteError(ValueError):
    """Se lanza cuando LegalTextExtractor.validate_and_fill necesita un dato
    faltante (capital o fecha de exigibilidad) pero no hay una forma segura
    de pedirlo: no se inyecto un prompt_fn y tampoco hay stdin interactivo
    disponible (ver app/engine/text/nlp_extractor.py, Sprint 27) -- evita el
    bloqueo original en un ejecutable sin consola adjunta."""
```

- [ ] **Step 2: Write the failing tests**

Create `tests/engine/text/test_nlp_extractor.py`:
```python
from datetime import date
from decimal import Decimal

import pytest

from app.core.exceptions import DatoFaltanteError
from app.engine.text.nlp_extractor import LegalTextExtractor


def test_extract_facts_encuentra_capital_y_fecha():
    extractor = LegalTextExtractor()
    texto = "El deudor debe $ 5.000.000 desde el 15/03/2020."

    facts = extractor.extract_facts(texto)

    assert facts["capital"] == Decimal("5000000")
    assert facts["fecha_exigibilidad"] == date(2020, 3, 15)


def test_validate_and_fill_no_llama_prompt_fn_si_los_hechos_ya_estan_completos():
    extractor = LegalTextExtractor()
    facts = {"capital": Decimal("5000000"), "fecha_exigibilidad": date(2020, 3, 15)}

    def prompt_fn_que_no_deberia_llamarse(mensaje):
        raise AssertionError("No deberia pedirse nada si los hechos ya estan completos")

    resultado = extractor.validate_and_fill(facts, prompt_fn=prompt_fn_que_no_deberia_llamarse)

    assert resultado is facts


def test_validate_and_fill_usa_el_prompt_fn_inyectado_para_completar_datos_faltantes():
    extractor = LegalTextExtractor()
    facts = {"capital": None, "fecha_exigibilidad": None}
    respuestas = iter(["5.000.000", "15/03/2020"])

    resultado = extractor.validate_and_fill(facts, prompt_fn=lambda mensaje: next(respuestas))

    assert resultado["capital"] == Decimal("5000000")
    assert resultado["fecha_exigibilidad"] == date(2020, 3, 15)


def test_validate_and_fill_sin_prompt_fn_y_sin_stdin_interactivo_lanza_error_en_vez_de_bloquear(
    monkeypatch,
):
    from app.engine.text import nlp_extractor

    monkeypatch.setattr(nlp_extractor.sys.stdin, "isatty", lambda: False)
    extractor = LegalTextExtractor()
    facts = {"capital": None, "fecha_exigibilidad": None}

    with pytest.raises(DatoFaltanteError):
        extractor.validate_and_fill(facts)


def test_validate_and_fill_default_usa_rich_prompt_cuando_hay_stdin_interactivo(monkeypatch):
    from app.engine.text import nlp_extractor

    monkeypatch.setattr(nlp_extractor.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(nlp_extractor.Prompt, "ask", lambda mensaje: "5.000.000")

    extractor = LegalTextExtractor()
    facts = {"capital": None, "fecha_exigibilidad": date(2020, 3, 15)}

    resultado = extractor.validate_and_fill(facts)

    assert resultado["capital"] == Decimal("5000000")
```

- [ ] **Step 3: Run the tests and confirm they fail**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q tests/engine/text/test_nlp_extractor.py -v
```

Expected: import error / failures — `DatoFaltanteError` does not exist yet, `validate_and_fill` does not accept `prompt_fn` yet, and it would otherwise block on `Prompt.ask()` for the missing-data tests.

- [ ] **Step 4: Rewrite `app/engine/text/nlp_extractor.py`**

Replace the entire file with:
```python
import re
import sys
from collections.abc import Callable
from datetime import datetime

from rich.prompt import Prompt

from app.core.exceptions import DatoFaltanteError
from app.engine.math.parsers import FinancialParser


def _prompt_interactivo(mensaje: str) -> str:
    """Prompt por defecto de `validate_and_fill`: usa `rich.prompt.Prompt.ask`,
    pero solo si hay un stdin interactivo conectado. En un ejecutable Windows
    sin consola adjunta (o en cualquier proceso no interactivo, ej. si esta
    clase se conecta a la GUI sin cambiarla primero) `sys.stdin` no es
    interactivo -- ahi se lanza `DatoFaltanteError` en vez de bloquear
    esperando una entrada que nunca llega (Sprint 27)."""
    if not sys.stdin or not sys.stdin.isatty():
        raise DatoFaltanteError(
            f"No hay stdin interactivo disponible para solicitar: {mensaje!r}. "
            "Proporcione prompt_fn para completar este dato desde otro origen "
            "(ej. un dialogo de la GUI)."
        )
    return Prompt.ask(f"[bold red]{mensaje}[/bold red]")


class LegalTextExtractor:
    """Motor determinista para extraer hechos jurídicos de texto natural.

    NOTA (Sprint 27): módulo huérfano hoy -- nada en `app/` lo importa
    todavía. Se conserva intencionalmente para una futura integración (ej.
    importar hechos desde texto libre pegado en la GUI). `validate_and_fill`
    acepta un `prompt_fn` inyectable para que un futuro caller decida cómo
    pedir un dato faltante (diálogo de Qt, valor por defecto, etc.); sin
    `prompt_fn`, usa `rich` solo si hay stdin interactivo real (ver
    `_prompt_interactivo`), evitando el cuelgue original si esta clase se
    conectara a la GUI sin cambiarla primero.
    """

    def __init__(self):
        # Patrones para buscar dinero y fechas
        self.money_pattern = r'\$\s*[\d\.\,]+'
        self.date_pattern = r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'

    def extract_facts(self, natural_text: str) -> dict:
        facts = {
            "capital": None,
            "fecha_exigibilidad": None,
        }

        # 1. Extraer Capital
        money_matches = re.findall(self.money_pattern, natural_text)
        if money_matches:
            # Tomamos la primera coincidencia monetaria como capital base
            facts["capital"] = FinancialParser.parse_money(money_matches[0])

        # 2. Extraer Fecha
        date_matches = re.findall(self.date_pattern, natural_text)
        if date_matches:
            # Intentamos parsear la fecha (asumiendo formato DD/MM/YYYY)
            raw_date = date_matches[0].replace('-', '/')
            try:
                facts["fecha_exigibilidad"] = datetime.strptime(raw_date, "%d/%m/%Y").date()
            except ValueError:
                pass  # Fallback si el formato no coincide

        return facts

    def validate_and_fill(
        self, facts: dict, prompt_fn: Callable[[str], str] = _prompt_interactivo
    ) -> dict:
        """Verifica qué datos faltan. Si falta la fecha o el capital, los
        pide con `prompt_fn(mensaje) -> str` (por defecto, `_prompt_interactivo`,
        que solo bloquea si hay stdin interactivo real)."""
        if not facts["capital"]:
            raw_cap = prompt_fn("Capital no detectado en el texto. Ingrese el monto histórico")
            facts["capital"] = FinancialParser.parse_money(raw_cap)

        if not facts["fecha_exigibilidad"]:
            raw_date = prompt_fn("Fecha de inicio no detectada. Ingrese fecha (DD/MM/YYYY)")
            facts["fecha_exigibilidad"] = datetime.strptime(raw_date, "%d/%m/%Y").date()

        return facts
```

- [ ] **Step 5: Run the tests again and confirm all pass**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q tests/engine/text/test_nlp_extractor.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 6: Run ruff on the modified/new files**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check app/core/exceptions.py app/engine/text/nlp_extractor.py tests/engine/text/test_nlp_extractor.py
```

Expected: no errors (this also clears the two pre-existing `E501` lines in the old `nlp_extractor.py`, since the file is fully rewritten with lines under 99 chars).

- [ ] **Step 7: Run the full suite**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q
```

Expected: `699 passed, 0 skipped` (694 + 5 new tests).

- [ ] **Step 8: Commit**

```bash
git add app/core/exceptions.py app/engine/text/nlp_extractor.py tests/engine/text/test_nlp_extractor.py
git commit -m "fix(sprint27): LegalTextExtractor.validate_and_fill ya no bloquea leyendo stdin, acepta prompt_fn inyectable"
```

---

### Task 6: Fix `BastiumChartGenerator` to use `pathlib.Path` (hallazgo 2b)

**Context:** `app/reports/charts.py` is the only source file using `os.path.join(os.getcwd(), ...)` instead of `pathlib.Path`, inconsistent with the rest of the codebase. This is being kept (not deleted) as an intentionally orphaned module for a future dataviz integration (explicitly excluded from Sprint 33's dashboard scope — "evaluar una gráfica en un sprint aparte"). Fix the path construction and add the same kind of "intentionally orphaned" doc note as Task 5. Also force the `Agg` (non-interactive) matplotlib backend at import time — this module only ever calls `savefig`, never `show()`, so it doesn't need a GUI backend, and forcing `Agg` avoids any chance of this module's `matplotlib.pyplot` import fighting over a backend with the app's own PySide6 `QApplication` if it's ever imported in the same process as the GUI.

**Files:**
- Modify: `app/reports/charts.py`
- Test: `tests/reports/test_charts.py` (new)

- [ ] **Step 1: Write a regression test for the path fix**

Create `tests/reports/test_charts.py`:
```python
from pathlib import Path

from app.reports.charts import BastiumChartGenerator


def test_generar_grafica_distribucion_devuelve_path_en_directorio_actual(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    datos_rubros = [
        {"concepto": "Capital", "capital": "1000000"},
        {"concepto": "Intereses", "capital": "250000"},
    ]
    generador = BastiumChartGenerator()

    ruta = generador.generar_grafica_distribucion(datos_rubros, output_filename="prueba.png")

    assert isinstance(ruta, Path)
    assert ruta == tmp_path / "prueba.png"
    assert ruta.exists()
```

- [ ] **Step 2: Run the test and confirm it fails**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q tests/reports/test_charts.py -v
```

Expected: FAIL on `assert isinstance(ruta, Path)` — today `generar_grafica_distribucion` returns a `str` from `os.path.join`.

- [ ] **Step 3: Rewrite `app/reports/charts.py`**

Replace the entire file with:
```python
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Sin GUI: este modulo solo guarda archivos (savefig), nunca show().
import matplotlib.pyplot as plt


class BastiumChartGenerator:
    """Generador de evidencia gráfica inmutable para anexar a demandas.

    NOTA (Sprint 27): módulo huérfano hoy -- nada en `app/` lo importa
    todavía. Se conserva intencionalmente para una futura integración de
    gráficas en los reportes (ver `app/reports/`; explícitamente excluido
    del alcance del Sprint 33/dashboard). La ruta de salida se resuelve con
    `pathlib.Path` (antes usaba `os.path.join(os.getcwd(), ...)`, único
    archivo del código fuente con ese patrón).
    """

    def __init__(self):
        self.color_burgundy = "#ae1c21"
        self.color_black = "#000000"
        self.color_cream = "#f5f1e9"

    def generar_grafica_distribucion(
        self, datos_rubros: list, output_filename: str = "distribucion.png"
    ) -> Path:
        # Extraer nombres y valores para la gráfica
        conceptos = [r["concepto"] for r in datos_rubros]
        capitales = [float(r["capital"]) for r in datos_rubros]

        # Configurar el estilo gráfico
        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor(self.color_cream)
        ax.set_facecolor(self.color_cream)

        # Dibujar barras horizontales (La barra más grande en Borgoña, el resto en Negro)
        colores = [
            self.color_burgundy if i == 0 else self.color_black for i in range(len(conceptos))
        ]
        barras = ax.barh(conceptos, capitales, color=colores, height=0.6)

        # Añadir las etiquetas de valor al final de cada barra
        total_capital = sum(capitales)
        for barra in barras:
            ancho = barra.get_width()
            porcentaje = (ancho / total_capital) * 100 if total_capital > 0 else 0
            etiqueta = f"${ancho:,.0f}\n({porcentaje:.0f}%)".replace(",", ".")
            ax.text(
                ancho + (total_capital * 0.02),
                barra.get_y() + barra.get_height() / 2,
                etiqueta,
                va='center', ha='left', color=self.color_burgundy,
                fontsize=10, fontweight='bold',
            )

        # Limpiar bordes innecesarios para un look elegante
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(self.color_black)
        ax.spines['left'].set_color(self.color_black)

        # Invertir el eje Y para que el rubro mayor quede arriba
        ax.invert_yaxis()
        plt.tight_layout()

        ruta_grafica = Path.cwd() / output_filename
        plt.savefig(ruta_grafica, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close()

        return ruta_grafica
```

- [ ] **Step 4: Run the test again and confirm it passes**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q tests/reports/test_charts.py -v
```

Expected: PASS. If `matplotlib.use("Agg")` raises because pyplot was already imported with a different backend earlier in the same test session (backend switching must happen before `pyplot` is first imported anywhere in the process), move the `matplotlib.use("Agg")` call to run before any other test in the session imports `matplotlib.pyplot` — check whether any other test file already does `import matplotlib.pyplot` first; if so, note it in this test file with a comment and, if needed, guard with `matplotlib.use("Agg", force=True)` instead.

- [ ] **Step 5: Run ruff on the modified/new files**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check app/reports/charts.py tests/reports/test_charts.py
```

Expected: no errors (also clears the 3 pre-existing `E501` lines in the old `charts.py`).

- [ ] **Step 6: Run the full suite**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q
```

Expected: `700 passed, 0 skipped` (699 + 1 new test).

- [ ] **Step 7: Commit**

```bash
git add app/reports/charts.py tests/reports/test_charts.py
git commit -m "fix(sprint27): BastiumChartGenerator usa pathlib.Path en vez de os.path.join(os.getcwd(), ...)"
```

---

### Task 7: Document `about.py` / `reportes.py` as intentional placeholders (hallazgo 7)

**Context:** `app/views/about.py` and `app/views/reportes.py` are 0-byte files, same scaffold pattern as the files deleted in Task 2 — except the user has decided to **keep** these two as documented placeholders for future GUI screens, the same treatment `app/views/dashboard.py` gets (`dashboard.py` is explicitly claimed as pending work by Sprint 33 in `Pendientes.md`). `dashboard.py` itself is also 0 bytes today with no in-file docstring — its "documented" status lives entirely in `Pendientes.md`'s Sprint 33 section, which this sprint must not edit. Since `about.py`/`reportes.py` have no equivalent sprint claiming them yet, the only place left to document their placeholder status is a module docstring inside each file — that's what this task adds. `app/views/dashboard.py` itself is out of scope (belongs to Sprint 33, not touched here).

**Files:**
- Modify: `app/views/about.py` (add module docstring — file goes from 0 bytes to docstring-only)
- Modify: `app/views/reportes.py` (add module docstring — file goes from 0 bytes to docstring-only)

- [ ] **Step 1: Write `app/views/about.py`**

```python
"""Pantalla "Acerca de" -- placeholder intencional, todavía sin implementar.

Igual que `app/views/dashboard.py` (ver Sprint 33 en `Pendientes.md`), este
archivo existe como hueco de producto documentado, no como código muerto:
todavía no hay ninguna pantalla de "Acerca de" (versión de la app, licencia,
datos de contacto/soporte) en la GUI. A diferencia de `dashboard.py`, ningún
sprint del backlog reclama esta pantalla todavía (ver Sprint 27, hallazgo 7,
en `Pendientes.md`) -- se deja vacío hasta que se planee un sprint dedicado.
Cuando se construya, la clase de la vista debería vivir aquí.
"""
```

- [ ] **Step 2: Write `app/views/reportes.py`**

```python
"""Pantalla "Reportes" en la GUI -- placeholder intencional, todavía sin implementar.

Igual que `app/views/dashboard.py` (ver Sprint 33 en `Pendientes.md`), este
archivo existe como hueco de producto documentado, no como código muerto:
`app/reports/` ya genera PDF/Word para una liquidación puntual, pero no
existe todavía una pantalla propia en la GUI para listar, consultar o
regenerar reportes ya generados -- distinta de `app/reports/`, que es motor,
no vista. A diferencia de `dashboard.py`, ningún sprint del backlog reclama
esta pantalla todavía (ver Sprint 27, hallazgo 7, en `Pendientes.md`) -- se
deja vacía hasta que se planee un sprint dedicado. Cuando se construya, la
clase de la vista debería vivir aquí.
"""
```

- [ ] **Step 3: Confirm nothing imports these files (still true after adding a docstring — sanity check)**

```bash
grep -rn "views\.about\|views\.reportes\|views import about\|views import reportes" app tests
```

Expected: no output.

- [ ] **Step 4: Run ruff on both files**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check app/views/about.py app/views/reportes.py
```

Expected: no errors.

- [ ] **Step 5: Run the full suite**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q
```

Expected: `700 passed, 0 skipped` (unchanged — a module docstring doesn't add or remove any test).

- [ ] **Step 6: Commit**

```bash
git add app/views/about.py app/views/reportes.py
git commit -m "docs(sprint27): documentar about.py y reportes.py como placeholders intencionales, igual que dashboard.py"
```

---

### Task 8: Final full-suite and lint verification

**Files:** none (verification only).

- [ ] **Step 1: Run the full suite one more time from a clean state**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q
```

Expected: `700 passed, 0 skipped`. Confirm in particular that the spurious `SKIPPED (got empty parameter set)` from the baseline is gone.

- [ ] **Step 2: Run ruff on the whole repo and compare against the baseline**

```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m ruff check . --statistics
```

Expected: fewer than the baseline 412 errors (Tasks 4/5/6 clear a handful of pre-existing `E501`/`B904` hits in the 3 files they rewrite). No new error categories introduced. Any remaining errors should all be pre-existing ones in files this sprint didn't touch (e.g. `tests/views/test_obligaciones.py` line-length) — do not fix those, out of scope.

- [ ] **Step 3: Confirm the git log for this branch**

```bash
git log --oneline main..HEAD
```

Expected: 7 commits, one per task (Tasks 1-7; Task 8 has no commit, it's verification-only).

---

## Self-review notes (already applied above)

- **Spec coverage:** all 7 `Hallazgos` from Sprint 27 are addressed — hallazgo 1 (Task 3), hallazgo 2a/2b (Tasks 5/6), hallazgo 3 (Task 4), hallazgo 4 (Task 1), hallazgos 5/6 (Task 2), hallazgo 7 (Task 7). The "Definición de Hecho" bullets are all satisfied: `requirements.txt` only lists packages with a real import (Task 3), no orphaned file is left without an explicit documented decision (Tasks 5/6/7 add doc notes, Task 2 deletes cleanly), zero `SKIPPED` from empty parametrize (Task 1), suite green throughout.
- **Guardrails respected:** `Pendientes.md` is never modified by this plan (unlike the Sprint 22 plan template, there is no "close out the sprint" task here — that's the orchestrator's job). No file under `app/engine/temporal/prescripcion.py`, `app/services/area_strategy.py` day-count logic, `app/views/expediente_detalle.py`, `app/views/liquidaciones.py`, or CI/CD config is touched by any task.
- **TDD applied where mandated:** Task 4 (`parsers.py`) and Task 5 (`nlp_extractor.py`) both write failing tests first, confirm the failure, then implement — per the explicit instruction to follow TDD for these two bug fixes. Task 6 (`charts.py`) also follows write-test-first even though not explicitly mandated, since it's cheap and gives a real regression net for the path-handling fix.
- **Type/behavior consistency:** `DatoFaltanteError` (Task 5) is defined once in `app/core/exceptions.py` (matching the project's existing convention of centralizing custom exceptions there) and imported by both `nlp_extractor.py` and its test file — no duplicate definition. `validate_and_fill`'s new `prompt_fn: Callable[[str], str]` parameter and `_prompt_interactivo` default are used consistently across Task 5's implementation and its 5 tests.
- **Dependency consistency:** Task 3 keeps `rich` and `matplotlib` in `requirements.txt` specifically because Tasks 5 and 6 keep `nlp_extractor.py` and `charts.py` importing them for real (not vestigially) — `rich.prompt.Prompt` is still the default `prompt_fn` implementation (guarded by `isatty()`), and `matplotlib.pyplot` still renders the chart. Neither dependency becomes newly-orphaned as a side effect of the bug fixes.
