# Sprint 22 — Limpieza técnica acumulada — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve the 5 housekeeping items listed in `Pendientes.md` Sprint 22 with zero visible behavior change — verified by the existing suite (655 passed, 1 skipped as of this baseline) staying green throughout.

**Architecture:** Pure structural refactor. No new tests are written (this isn't new behavior); the existing suite is the regression net and must pass after every task. Each task is independently committable.

**Tech Stack:** Python, PySide6 (Qt), pytest, SQLAlchemy.

**Baseline (must reproduce before Task 1):**
```bash
python -m pytest -q
```
Expected: `655 passed, 1 skipped`

---

### Task 1: Remove the orphaned `AllocationEngine` (`app/engine/allocation/allocator.py`)

**Context:** Two classes named `AllocationEngine` exist. `app/engine/liquidation/allocation.py` is the real one (static `allocate(payment_amount, current_debt, payment_date)`, used by `LiquidationCore`). `app/engine/allocation/allocator.py` is dead code: instance method `allocate(self, payment, obligations)` that just does `raise NotImplementedError`, and nothing in `app/`, `tests/`, or `exports/` imports it (verified via grep for `engine.allocation.allocator` — zero hits outside itself).

It depends on `app.domain.obligation.base.Obligation`, a dataclass that — after this file is gone — has no other consumer anywhere in the repo (verified via grep for `domain.obligation.base` — the only hit is this orphan). Sprint 22's task description explicitly asks to confirm whether that domain model "justifies keeping" the orphan; since nothing else uses it, the answer is no — delete both together.

**Files:**
- Delete: `app/engine/allocation/allocator.py`
- Delete: `app/engine/allocation/` (the whole directory — becomes empty except `__pycache__`)
- Delete: `app/domain/obligation/base.py`
- Modify: `docs/specifications/04_motor_pagos.md:22-26` (remove the now-stale "Advertencia de deuda técnica" section)

- [ ] **Step 1: Delete the orphaned files and folder**

```bash
rm -f "app/domain/obligation/base.py"
rm -rf "app/engine/allocation"
```

- [ ] **Step 2: Remove the stale warning from the spec doc**

In `docs/specifications/04_motor_pagos.md`, delete lines 22-26 (the `## Advertencia de deuda tecnica` section) so the file reads:

```markdown
## Como se usa en el MVP
Cada `Abono` capturado en la GUI se convierte en un `Payment` (`CivilFamiliaStrategy`) y se mezcla
cronologicamente con los eventos de causacion antes de procesarse.

## Pendiente (no implementado aun)
- Validadores de pago anomalo (pago mayor al saldo, duplicado, sin soporte).
- Reglas de imputacion alternativas por regimen (ej. tributario: sanciones -> intereses -> impuesto).
- Compensacion, novacion, remision, confusion.

Ver `Pendientes.md`.
```

- [ ] **Step 3: Verify nothing else references the deleted modules**

```bash
grep -rE "engine\.allocation\.allocator|engine/allocation/allocator|domain\.obligation\.base|domain/obligation/base" app tests exports database
```

Expected: no output (exit code 1 / no matches).

- [ ] **Step 4: Run full suite**

```bash
python -m pytest -q
```

Expected: `655 passed, 1 skipped` (unchanged).

- [ ] **Step 5: Commit**

```bash
git add app/engine/allocation app/domain/obligation/base.py docs/specifications/04_motor_pagos.md
git commit -m "chore(sprint22): remove orphaned AllocationEngine and unused Obligation domain model"
```

(Note: `git add` on a deleted path stages the deletion.)

---

### Task 2: Remove the empty `app/engine/financial/allocation.py`

**Context:** This file is 0 bytes. Grep for any import of `engine.financial.allocation` across the repo returns zero hits — it's dead weight, likely abandoned mid-refactor per the sprint notes.

**Files:**
- Delete: `app/engine/financial/allocation.py`

- [ ] **Step 1: Verify it's truly unreferenced**

```bash
grep -rn "financial.allocation" app tests exports database docs
```

Expected: no `import` statements (docs mentioning the path historically in old plan/spec files from other sprints are fine to leave — they're historical records, not live references).

- [ ] **Step 2: Delete it**

```bash
rm -f "app/engine/financial/allocation.py"
```

- [ ] **Step 3: Run full suite**

```bash
python -m pytest -q
```

Expected: `655 passed, 1 skipped`.

- [ ] **Step 4: Commit**

```bash
git add app/engine/financial/allocation.py
git commit -m "chore(sprint22): remove empty, unused app/engine/financial/allocation.py"
```

---

### Task 3: `_eventos_de_obligacion` duplication — verify current state, no code change

**Context:** The sprint note (written after Sprint 2's code review, referencing `docs/superpowers/plans/2026-07-15-area-comercial.md`) says `_eventos_de_obligacion` is byte-identical between `CivilFamiliaStrategy` and `ComercialStrategy`. That was true in Sprint 2. Since then, Sprint 8 (IPC indexation) and Sprint 19 (anatocismo) gave each area genuinely different logic:
- `CivilFamiliaStrategy._eventos_de_obligacion` (app/services/area_strategy.py:256-303) branches on IPC indexation and uses `obligacion.valor` directly.
- `ComercialStrategy._eventos_de_obligacion` (app/services/area_strategy.py:590-615) converts to pesos via TRM, adds anatocismo events, no IPC.

These are no longer duplicates — they're two different area-specific methods that happen to share a superficial shape (an `Event` for capital + optional extra events + shared costas via the already-extracted `_evento_costas_procesales` module function at line 51). Forcing an extraction here would mean generalizing over genuinely different domain logic, which is the kind of premature abstraction that creates more risk (behavior coupling between areas that should stay independent) than it removes duplication. `Sancionatorio._eventos_de_obligacion` and `Honorarios._eventos_de_obligacion` are structurally similar to each other too, but differ in their amount calculation and in what they pass as `pretensiones_reconocidas` for costas — also not byte-identical.

**Decision: no code change for this item.** Document the finding in the Sprint 22 closure note (Task 6).

- [ ] **Step 1: Confirm the methods still differ (sanity check before closing this item)**

```bash
grep -n "_eventos_de_obligacion" app/services/area_strategy.py
```

Read each definition found and confirm none are byte-identical to another (already done during planning — CivilFamilia vs Comercial differ in IPC/anatocismo/pesos conversion; Sancionatorio vs Honorarios differ in amount source and costas base). No edit needed.

---

### Task 4: Deduplicate `_construir_rate_provider_obligacion` (real, verified duplication)

**Context:** Unlike Task 3, this one is real right now. Compare the three definitions in `app/services/area_strategy.py`:

- `SancionatorioStrategy` (line 915-922) and `HonorariosStrategy` (line 1011-1018) are **byte-identical**: both build a `MemoryRateProvider` with one flat rate period from `obligacion.fecha_origen - 1 day` to `fecha_corte`, using `obligacion.tasa_efectiva_anual`, no `source`.
- `CivilFamiliaStrategy` (line 319-332) does the same thing but picks `fecha_inicio` conditionally (`fecha_origen` if PUNTUAL else `fecha_inicio`) and passes a `source` string.

All three fit the pattern described in the sprint note: "un solo tramo de tasa plana desde la obligación hasta la fecha de corte." Extract it to `AreaStrategy` (the shared base class, `app/services/area_strategy.py:205`) as `_rate_provider_tasa_plana`, parameterized by `fecha_inicio` so `CivilFamiliaStrategy` can still compute it conditionally.

`MemoryRateProvider.add_rate_period`'s `source` parameter already defaults to `"N/A"` (`app/engine/interest/provider.py:39`), which is exactly what Sancionatorio/Honorarios relied on implicitly — so giving the shared helper the same default preserves their behavior exactly.

**Files:**
- Modify: `app/services/area_strategy.py:205-212` (add method to `AreaStrategy`)
- Modify: `app/services/area_strategy.py:319-332` (`CivilFamiliaStrategy._construir_rate_provider_obligacion`)
- Modify: `app/services/area_strategy.py:915-922` (`SancionatorioStrategy._construir_rate_provider_obligacion`)
- Modify: `app/services/area_strategy.py:1011-1018` (`HonorariosStrategy._construir_rate_provider_obligacion`)

- [ ] **Step 1: Add the shared helper to `AreaStrategy`**

Replace:
```python
class AreaStrategy(ABC):
    """Contrato comun para el calculo de liquidacion por area del derecho."""

    soporta_indexacion_ipc: bool = True

    @abstractmethod
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise NotImplementedError
```

With:
```python
class AreaStrategy(ABC):
    """Contrato comun para el calculo de liquidacion por area del derecho."""

    soporta_indexacion_ipc: bool = True

    @abstractmethod
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise NotImplementedError

    @staticmethod
    def _rate_provider_tasa_plana(
        fecha_inicio: date, fecha_corte: date, tasa_efectiva_anual: Decimal, source: str = "N/A"
    ) -> MemoryRateProvider:
        """Un solo tramo de tasa diaria plana desde `fecha_inicio` hasta `fecha_corte` --
        patron compartido por Sancionatorio, Honorarios y Civil/Familia (Sprint 22,
        deduplicacion de `_construir_rate_provider_obligacion`)."""
        tasa_diaria = EffectiveRateConverter.annual_to_daily(tasa_efectiva_anual)
        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_inicio - timedelta(days=1), end=fecha_corte, rate=tasa_diaria, source=source,
        )
        return provider
```

- [ ] **Step 2: Update `CivilFamiliaStrategy`**

Replace:
```python
    def _construir_rate_provider_obligacion(self, obligacion, fecha_corte: date) -> MemoryRateProvider:
        fecha_inicio = (
            obligacion.fecha_origen if obligacion.tipo.value == "PUNTUAL" else obligacion.fecha_inicio
        )
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligacion.tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_inicio - timedelta(days=1),
            end=fecha_corte,
            rate=tasa_diaria,
            source="Tasa pactada en la obligación (Art. 1617 C.C.)",
        )
        return provider
```

With:
```python
    def _construir_rate_provider_obligacion(self, obligacion, fecha_corte: date) -> MemoryRateProvider:
        fecha_inicio = (
            obligacion.fecha_origen if obligacion.tipo.value == "PUNTUAL" else obligacion.fecha_inicio
        )
        return self._rate_provider_tasa_plana(
            fecha_inicio, fecha_corte, obligacion.tasa_efectiva_anual,
            source="Tasa pactada en la obligación (Art. 1617 C.C.)",
        )
```

- [ ] **Step 3: Update `SancionatorioStrategy`**

Replace:
```python
    def _construir_rate_provider_obligacion(self, obligacion, fecha_corte: date) -> MemoryRateProvider:
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligacion.tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=obligacion.fecha_origen - timedelta(days=1), end=fecha_corte, rate=tasa_diaria
        )
        return provider


class HonorariosStrategy(AreaStrategy):
```

With:
```python
    def _construir_rate_provider_obligacion(self, obligacion, fecha_corte: date) -> MemoryRateProvider:
        return self._rate_provider_tasa_plana(obligacion.fecha_origen, fecha_corte, obligacion.tasa_efectiva_anual)


class HonorariosStrategy(AreaStrategy):
```

(This edit targets the `SancionatorioStrategy` definition specifically — match on the surrounding `class HonorariosStrategy(AreaStrategy):` line to disambiguate from the identical block in Step 4.)

- [ ] **Step 4: Update `HonorariosStrategy`**

Replace (the second, now-remaining occurrence of this exact block, inside `HonorariosStrategy`, followed by `class TributarioStrategy(AreaStrategy):`):
```python
    def _construir_rate_provider_obligacion(self, obligacion, fecha_corte: date) -> MemoryRateProvider:
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligacion.tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=obligacion.fecha_origen - timedelta(days=1), end=fecha_corte, rate=tasa_diaria
        )
        return provider


class TributarioStrategy(AreaStrategy):
```

With:
```python
    def _construir_rate_provider_obligacion(self, obligacion, fecha_corte: date) -> MemoryRateProvider:
        return self._rate_provider_tasa_plana(obligacion.fecha_origen, fecha_corte, obligacion.tasa_efectiva_anual)


class TributarioStrategy(AreaStrategy):
```

- [ ] **Step 5: Run the full suite (especially area_strategy + integration tests)**

```bash
python -m pytest -q tests/services tests/integration -v 2>&1 | tail -60
python -m pytest -q
```

Expected: `655 passed, 1 skipped`, same as baseline. Pay special attention to any Civil/Familia, Sancionatorio, or Honorarios liquidation test — a wrong `source` string or off-by-one on `fecha_inicio` would show up as a numeric or `rate_source` mismatch there.

- [ ] **Step 6: Commit**

```bash
git add app/services/area_strategy.py
git commit -m "refactor(sprint22): deduplicate _construir_rate_provider_obligacion into AreaStrategy._rate_provider_tasa_plana"
```

---

### Task 5: Break up `ObligacionFormDialog.guardar()`'s stacked branches

**Context:** `app/views/obligaciones.py`'s `guardar()` (currently lines 284-406) already delegates `LABORAL` and `TRIBUTARIO` to their own methods (`_guardar_laboral`, `_guardar_tributario`), but the remaining 4 areas (Civil/Familia, Comercial, Sancionatorio, Honorarios) share one ~120-line method with `es_sancionatorio`/`es_honorarios`/`self._area == "COMERCIAL"` branches stacked inside, each with its own `try/except InvalidOperation` block.

Naively splitting this into 4 full per-area methods (mirroring `_guardar_laboral`/`_guardar_tributario` exactly) would duplicate the ~20-line `Obligacion(...)` constructor call 4 times — trading one kind of duplication for a worse one. Instead: keep ONE shared `Obligacion(...)` call, and extract only the area-specific *parsing* into small methods that return a dict of overrides, merged over a class-level dict of defaults. This mirrors the separation `area_strategy.py` already has per strategy (one area, one place its quirks live) without duplicating the shared construction logic.

The existing test suite in `tests/views/test_obligaciones.py` has dedicated coverage for every area (Civil/Familia, Comercial incl. USD/TRM/anatocismo, Sancionatorio, Honorarios incl. optional costas) and for the validation error paths (negative valor) — this is the regression net for this task.

**Files:**
- Modify: `app/views/obligaciones.py` (imports, class body, `guardar()`)

- [ ] **Step 1: Add `List` to the typing import**

Replace:
```python
from datetime import date
from decimal import Decimal, InvalidOperation
```

With:
```python
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List
```

- [ ] **Step 2: Add the defaults dict as a class attribute**

Replace:
```python
class ObligacionFormDialog(QDialog):
    def __init__(self, expediente_id: int, area: str = "CIVIL_FAMILIA", parent=None):
```

With:
```python
class ObligacionFormDialog(QDialog):
    # Campos condicionales por area que `Obligacion` siempre espera recibir (aunque sea
    # en None) -- cada `_parse_campos_<area>()` solo devuelve las claves que esa area
    # necesita sobreescribir; el resto queda en su valor por defecto de aqui (Sprint 22,
    # deduplicacion de guardar()).
    _CAMPOS_AREA_POR_DEFECTO = {
        "tasa_moratoria_anual": None,
        "fecha_vencimiento": None,
        "ibc_vigente_anual": None,
        "cantidad_smlmv_uvt": None,
        "honorarios_fijos_pactados": None,
        "cuota_litis_pactada_pct": None,
        "beneficio_obtenido": None,
        "costas_pct_manual": None,
        "moneda": "COP",
        "trm_aplicable": None,
        "trm_fecha_referencia": None,
        "anatocismo_demanda_judicial": False,
        "anatocismo_fecha_acuerdo": None,
    }

    def __init__(self, expediente_id: int, area: str = "CIVIL_FAMILIA", parent=None):
```

- [ ] **Step 3: Replace `guardar()` and insert the new helper methods**

Replace the entire current `guardar()` method:
```python
    def guardar(self) -> int:
        if self._area == "LABORAL":
            return self._guardar_laboral()
        if self._area == "TRIBUTARIO":
            return self._guardar_tributario()

        es_sancionatorio = self._area == "SANCIONATORIO"
        es_honorarios = self._area == "HONORARIOS"

        try:
            tasa = Decimal(self.campo_tasa.text())
            if es_sancionatorio or es_honorarios:
                # No se usa: el motor calcula el monto desde cantidad_smlmv_uvt o
                # honorarios_fijos_pactados/cuota_litis_pactada_pct/beneficio_obtenido.
                valor = Decimal("0.00")
            else:
                valor = Decimal(self.campo_valor.text())
        except InvalidOperation as error:
            raise ValueError("Valor y tasa deben ser numeros validos.") from error

        if not es_sancionatorio and not es_honorarios and valor <= Decimal("0"):
            raise ValueError("El valor de la obligacion debe ser mayor que cero.")

        cantidad_smlmv_uvt = None
        if es_sancionatorio:
            try:
                cantidad_smlmv_uvt = Decimal(self.campo_cantidad_smlmv_uvt.text())
            except InvalidOperation as error:
                raise ValueError("Cantidad SMLMV/UVT debe ser un numero valido.") from error

        honorarios_fijos = None
        cuota_litis_pct = None
        beneficio_obtenido = None
        costas_pct = None
        if es_honorarios:
            try:
                honorarios_fijos = Decimal(self.campo_honorarios_fijos.text())
                cuota_litis_pct = Decimal(self.campo_cuota_litis_pct.text())
                beneficio_obtenido = Decimal(self.campo_beneficio_obtenido.text())
            except InvalidOperation as error:
                raise ValueError(
                    "Honorarios fijos, % cuota litis y beneficio obtenido deben ser numeros validos."
                ) from error
            texto_costas = self.campo_costas_pct.text().strip()
            if texto_costas:
                try:
                    costas_pct = Decimal(texto_costas)
                except InvalidOperation as error:
                    raise ValueError("% Costas judiciales debe ser un numero valido.") from error

        tasa_moratoria = None
        fecha_vencimiento = None
        ibc_vigente = None
        moneda = "COP"
        trm_aplicable = None
        trm_fecha_referencia = None
        anatocismo_demanda_judicial = False
        anatocismo_fecha_acuerdo = None
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
            moneda = self.combo_moneda.currentData()
            if moneda == "USD":
                try:
                    trm_aplicable = Decimal(self.campo_trm_aplicable.text())
                except InvalidOperation as error:
                    raise ValueError("La TRM aplicable debe ser un numero valido.") from error
                qdate_trm = self.campo_trm_fecha_referencia.date()
                trm_fecha_referencia = date(qdate_trm.year(), qdate_trm.month(), qdate_trm.day())

            anatocismo_demanda_judicial = self.check_anatocismo_demanda_judicial.isChecked()
            if self.check_anatocismo_acuerdo.isChecked():
                qdate_acuerdo = self.campo_anatocismo_fecha_acuerdo.date()
                anatocismo_fecha_acuerdo = date(
                    qdate_acuerdo.year(), qdate_acuerdo.month(), qdate_acuerdo.day()
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
            cantidad_smlmv_uvt=cantidad_smlmv_uvt,
            honorarios_fijos_pactados=honorarios_fijos,
            cuota_litis_pactada_pct=cuota_litis_pct,
            beneficio_obtenido=beneficio_obtenido,
            costas_pct_manual=costas_pct,
            aplica_indexacion_ipc=self.check_aplica_indexacion_ipc.isChecked(),
            interes_sobre_capital_indexado=self.check_interes_sobre_capital_indexado.isChecked(),
            moneda=moneda,
            trm_aplicable=trm_aplicable,
            trm_fecha_referencia=trm_fecha_referencia,
            anatocismo_demanda_judicial=anatocismo_demanda_judicial,
            anatocismo_fecha_acuerdo=anatocismo_fecha_acuerdo,
            dia_pago=self.campo_dia_pago.value() if tipo == TipoObligacion.RECURRENTE else None,
            fecha_inicio=fecha_inicio if tipo == TipoObligacion.RECURRENTE else None,
            fecha_fin=None,
        )
        session.add(obligacion)
        session.commit()
        obligacion_id = obligacion.id
        session.close()
        return obligacion_id
```

With:
```python
    def guardar(self) -> int:
        if self._area == "LABORAL":
            return self._guardar_laboral()
        if self._area == "TRIBUTARIO":
            return self._guardar_tributario()

        es_sancionatorio = self._area == "SANCIONATORIO"
        es_honorarios = self._area == "HONORARIOS"

        try:
            tasa = Decimal(self.campo_tasa.text())
            if es_sancionatorio or es_honorarios:
                # No se usa: el motor calcula el monto desde cantidad_smlmv_uvt o
                # honorarios_fijos_pactados/cuota_litis_pactada_pct/beneficio_obtenido.
                valor = Decimal("0.00")
            else:
                valor = Decimal(self.campo_valor.text())
        except InvalidOperation as error:
            raise ValueError("Valor y tasa deben ser numeros validos.") from error

        if not es_sancionatorio and not es_honorarios and valor <= Decimal("0"):
            raise ValueError("El valor de la obligacion debe ser mayor que cero.")

        parseo_por_area = {
            "SANCIONATORIO": self._parse_campos_sancionatorio,
            "HONORARIOS": self._parse_campos_honorarios,
            "COMERCIAL": self._parse_campos_comercial,
        }.get(self._area, self._parse_campos_civil_familia)
        campos_area = {**self._CAMPOS_AREA_POR_DEFECTO, **parseo_por_area()}

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
            aplica_indexacion_ipc=self.check_aplica_indexacion_ipc.isChecked(),
            interes_sobre_capital_indexado=self.check_interes_sobre_capital_indexado.isChecked(),
            dia_pago=self.campo_dia_pago.value() if tipo == TipoObligacion.RECURRENTE else None,
            fecha_inicio=fecha_inicio if tipo == TipoObligacion.RECURRENTE else None,
            fecha_fin=None,
            **campos_area,
        )
        session.add(obligacion)
        session.commit()
        obligacion_id = obligacion.id
        session.close()
        return obligacion_id

    def _parse_decimales(self, campos: List[QLineEdit], mensaje_error: str) -> List[Decimal]:
        """Parsea 1+ QLineEdit a Decimal bajo un solo mensaje de error compartido --
        replica el try/except conjunto que ya usaban los bloques por area de guardar()
        (ej. tasa moratoria + IBC bajo un mismo mensaje)."""
        try:
            return [Decimal(campo.text()) for campo in campos]
        except InvalidOperation as error:
            raise ValueError(mensaje_error) from error

    def _parse_campos_civil_familia(self) -> dict:
        return {}

    def _parse_campos_sancionatorio(self) -> dict:
        (cantidad_smlmv_uvt,) = self._parse_decimales(
            [self.campo_cantidad_smlmv_uvt], "Cantidad SMLMV/UVT debe ser un numero valido."
        )
        return {"cantidad_smlmv_uvt": cantidad_smlmv_uvt}

    def _parse_campos_honorarios(self) -> dict:
        honorarios_fijos, cuota_litis_pct, beneficio_obtenido = self._parse_decimales(
            [self.campo_honorarios_fijos, self.campo_cuota_litis_pct, self.campo_beneficio_obtenido],
            "Honorarios fijos, % cuota litis y beneficio obtenido deben ser numeros validos.",
        )
        costas_pct = None
        texto_costas = self.campo_costas_pct.text().strip()
        if texto_costas:
            (costas_pct,) = self._parse_decimales(
                [self.campo_costas_pct], "% Costas judiciales debe ser un numero valido."
            )
        return {
            "honorarios_fijos_pactados": honorarios_fijos,
            "cuota_litis_pactada_pct": cuota_litis_pct,
            "beneficio_obtenido": beneficio_obtenido,
            "costas_pct_manual": costas_pct,
        }

    def _parse_campos_comercial(self) -> dict:
        tasa_moratoria, ibc_vigente = self._parse_decimales(
            [self.campo_tasa_moratoria, self.campo_ibc_vigente],
            "Tasa moratoria e IBC vigente deben ser numeros validos.",
        )
        qdate_vencimiento = self.campo_fecha_vencimiento.date()
        fecha_vencimiento = date(
            qdate_vencimiento.year(), qdate_vencimiento.month(), qdate_vencimiento.day()
        )

        moneda = self.combo_moneda.currentData()
        trm_aplicable = None
        trm_fecha_referencia = None
        if moneda == "USD":
            (trm_aplicable,) = self._parse_decimales(
                [self.campo_trm_aplicable], "La TRM aplicable debe ser un numero valido."
            )
            qdate_trm = self.campo_trm_fecha_referencia.date()
            trm_fecha_referencia = date(qdate_trm.year(), qdate_trm.month(), qdate_trm.day())

        anatocismo_demanda_judicial = self.check_anatocismo_demanda_judicial.isChecked()
        anatocismo_fecha_acuerdo = None
        if self.check_anatocismo_acuerdo.isChecked():
            qdate_acuerdo = self.campo_anatocismo_fecha_acuerdo.date()
            anatocismo_fecha_acuerdo = date(
                qdate_acuerdo.year(), qdate_acuerdo.month(), qdate_acuerdo.day()
            )

        return {
            "tasa_moratoria_anual": tasa_moratoria,
            "fecha_vencimiento": fecha_vencimiento,
            "ibc_vigente_anual": ibc_vigente,
            "moneda": moneda,
            "trm_aplicable": trm_aplicable,
            "trm_fecha_referencia": trm_fecha_referencia,
            "anatocismo_demanda_judicial": anatocismo_demanda_judicial,
            "anatocismo_fecha_acuerdo": anatocismo_fecha_acuerdo,
        }
```

- [ ] **Step 4: Run the obligaciones view suite in isolation first**

```bash
python -m pytest -q tests/views/test_obligaciones.py -v
```

Expected: all tests pass (this file has ~40 tests covering every area's `guardar()` path and validation errors — the fastest signal if a kwarg got dropped or a default got swapped).

- [ ] **Step 5: Run the full suite**

```bash
python -m pytest -q
```

Expected: `655 passed, 1 skipped`.

- [ ] **Step 6: Commit**

```bash
git add app/views/obligaciones.py
git commit -m "refactor(sprint22): replace stacked if/try/except branches in ObligacionFormDialog.guardar() with per-area parse methods"
```

---

### Task 6: Close out Sprint 22 in `Pendientes.md`

**Files:**
- Modify: `Pendientes.md` (Sprint 22 section, currently lines 1930-1982)

- [ ] **Step 1: Mark the section header as completed**

Replace:
```markdown
## Sprint 22 — Limpieza técnica acumulada
```

With:
```markdown
## Sprint 22 — Limpieza técnica acumulada ✅ Completado
```

- [ ] **Step 2: Append a closure note after the "Definición de Hecho" block**, following the style used to close Sprints 20/21 (state what changed, what was found to no longer apply, and why).

Insert immediately before the `---` that ends the Sprint 22 section (after the "Suite completa en verde..." bullet):

```markdown

**Estado:** Implementado (2026-08-01). Los 5 puntos:

1. **`AllocationEngine` duplicado:** eliminado `app/engine/allocation/allocator.py` (código huérfano,
   `raise NotImplementedError`, nada lo importaba) junto con `app/domain/obligation/base.Obligation`
   (modelo de dominio que solo ese archivo huérfano usaba — no había nada que "justificara mantenerlo").
   Se retiró también la advertencia de deuda técnica correspondiente en
   `docs/specifications/04_motor_pagos.md`.
2. **Archivo vacío:** eliminado `app/engine/financial/allocation.py` (0 bytes, sin ningún import).
3. **`_eventos_de_obligacion` duplicado:** al revisar el código actual, la duplicación puntual detectada
   en el Sprint 2 entre `CivilFamiliaStrategy` y `ComercialStrategy` ya no existe — ambos métodos
   divergieron genuinamente con el Sprint 8 (indexación IPC) y el Sprint 19 (anatocismo comercial). Forzar
   una extracción compartida hoy generalizaría lógica de dominio que ya es distinta por diseño. Sin cambio
   de código en este punto.
4. **`_construir_rate_provider_obligacion` duplicado:** este sí seguía siendo real (Sancionatorio y
   Honorarios eran byte-idénticos; Civil/Familia el mismo patrón con una rama adicional). Extraído a
   `AreaStrategy._rate_provider_tasa_plana` (clase base, `app/services/area_strategy.py`).
5. **`ObligacionFormDialog.guardar()` god method:** reemplazadas las ramas `if/try/except` apiladas por
   `_parse_campos_<area>()` (uno por Sancionatorio/Honorarios/Comercial/Civil-Familia) que devuelven solo
   las claves que esa área sobreescribe sobre `_CAMPOS_AREA_POR_DEFECTO`, más un helper `_parse_decimales`
   para el patrón de parseo con mensaje de error compartido. Se mantuvo una sola construcción de
   `Obligacion(...)` en vez de duplicarla por área.

Suite completa verde tras cada paso (655 passed, 1 skipped, sin cambios de resultado).
```

- [ ] **Step 3: Update the table of contents entry**

Replace:
```markdown
- [Sprint 22 — Limpieza técnica acumulada](#sprint-22--limpieza-técnica-acumulada)
```

With:
```markdown
- [Sprint 22 — Limpieza técnica acumulada ✅ Completado](#sprint-22--limpieza-técnica-acumulada--completado)
```

- [ ] **Step 4: Commit**

```bash
git add Pendientes.md
git commit -m "docs: close out Sprint 22 (limpieza tecnica acumulada)"
```

---

## Self-review notes (already applied above)

- **Spec coverage:** all 5 numbered tasks from Pendientes.md are addressed — 2 deletions (Task 1, 2), 1 verified-and-declined-with-justification (Task 3), 1 real dedup (Task 4), 1 god-method split (Task 5), plus closing the tracker (Task 6).
- **Scope discipline:** Task 3 deliberately does *not* force a refactor the current code no longer needs — this matches the sprint's own "sin cambio de comportamiento visible" constraint better than a speculative extraction would, and matches the instruction to prefer three similar lines over a premature abstraction.
- **Type/behavior consistency:** Task 4's `_rate_provider_tasa_plana` default `source="N/A"` matches `MemoryRateProvider.add_rate_period`'s own default, so Sancionatorio/Honorarios (which never passed `source`) get byte-identical `RatePeriod` objects. Task 5's `_CAMPOS_AREA_POR_DEFECTO` values were cross-checked field-by-field against the original method's initialization defaults (all `None` except `moneda="COP"` and `anatocismo_demanda_judicial=False`).
