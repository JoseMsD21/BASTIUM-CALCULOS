# Sprint 20 — Indexación sobre capital ya indexado (algoritmo "Suma Única") — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cuando una obligación de Civil/Familia tiene indexación IPC activa Y el nuevo flag "Suma Única"
marcado, el interés civil (6% EA, Art. 1617 C.C.) debe calcularse sobre el capital **ya indexado**
(`principal + indexation`), no solo sobre el capital histórico — algoritmo "Suma Única" del PDF de
requisitos, pág. 21-22.

**Architecture:** `LiquidationCore` recibe un nuevo flag `usar_suma_unica: bool = False` que cambia la
base de capital usada en `_accrue_time_passage` (línea 101 de `app/engine/liquidation/engine.py`) de
`principal` a `principal + indexation`. `UniversalLiquidationService` reenvía el flag sin lógica propia.
`CivilFamiliaStrategy` lo deriva de un nuevo campo por obligación (`Obligacion.interes_sobre_capital_indexado`,
default `False`) y valida que no se mezclen criterios distintos dentro del mismo expediente (el interés se
calcula sobre un único `PendingDebt` acumulado para todo el expediente, no por obligación). Ninguna otra
estrategia (`Comercial`, `Laboral`, `Sancionatorio`, `Honorarios`, `Tributario`) pasa este flag — quedan en
el default `False`, comportamiento idéntico al actual. No se toca `PendingDebt`, `BalanceEngine` ni
`AllocationEngine`.

**Tech Stack:** Python, SQLAlchemy (SQLite), pytest, PySide6/pytest-qt para el checkbox de la GUI.

**Spec:** `docs/superpowers/specs/2026-07-31-sprint20-suma-unica-design.md`

**Nota operativa sobre git:** antes de cualquier paso "Commit" de este plan, correr `git status`. Si
aparece "You have unmerged paths" (hay un merge de otra sesión/worktree en curso), **no comitear** — dejar
los cambios en el working tree y avisar al usuario en vez de forzar una resolución del merge ajeno.

---

### Task 1: Columna `Obligacion.interes_sobre_capital_indexado` + migración

**Files:**
- Modify: `database/models.py`
- Create: `scripts/migrate_interes_sobre_capital_indexado.py`
- Test: `tests/scripts/test_migrate_interes_sobre_capital_indexado.py`

`bastium.db` ya tiene 1 obligación existente (confirmado: `SELECT count(*) FROM obligaciones` → `(1,)`).
`Base.metadata.create_all()` no altera tablas existentes, así que la columna nueva no llega a la base real
sin un `ALTER TABLE` explícito — mismo patrón que `scripts/migrate_aplica_indexacion_ipc.py` (Sprint 8).

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/scripts/test_migrate_interes_sobre_capital_indexado.py`:

```python
import sqlite3

import pytest

from scripts.migrate_interes_sobre_capital_indexado import migrar


@pytest.fixture
def db_sin_columna(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY, concepto TEXT)")
    con.execute("INSERT INTO obligaciones (id, concepto) VALUES (1, 'Gastos medicos')")
    con.commit()
    con.close()
    return db_path


def test_migrar_agrega_la_columna_y_retorna_true(db_sin_columna):
    aplicada = migrar(db_sin_columna)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columna)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert "interes_sobre_capital_indexado" in columnas


def test_migrar_preserva_las_filas_existentes(db_sin_columna):
    migrar(db_sin_columna)

    con = sqlite3.connect(db_sin_columna)
    fila = con.execute(
        "SELECT concepto, interes_sobre_capital_indexado FROM obligaciones WHERE id = 1"
    ).fetchone()
    con.close()
    assert fila == ("Gastos medicos", 0)


def test_migrar_es_idempotente_segunda_corrida_retorna_false(db_sin_columna):
    primera = migrar(db_sin_columna)
    segunda = migrar(db_sin_columna)
    assert primera is True
    assert segunda is False
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `pytest tests/scripts/test_migrate_interes_sobre_capital_indexado.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'scripts.migrate_interes_sobre_capital_indexado'`

- [ ] **Step 3: Agregar la columna al modelo**

En `database/models.py`, dentro de `class Obligacion(Base)`, inmediatamente después de la línea
`aplica_indexacion_ipc: Mapped[bool] = mapped_column(Boolean, default=False)` (línea 118):

```python
    interes_sobre_capital_indexado: Mapped[bool] = mapped_column(Boolean, default=False)
```

- [ ] **Step 4: Implementar el script de migración**

Crear `scripts/migrate_interes_sobre_capital_indexado.py`:

```python
"""Migracion de esquema (Sprint 20): agrega la columna
interes_sobre_capital_indexado a la tabla obligaciones. Idempotente -- verifica
con PRAGMA table_info antes de alterar, para poder correrse mas de una vez
(ej. en otra maquina de desarrollo o en CI) sin fallar. Mismo patron que
scripts/migrate_aplica_indexacion_ipc.py (Sprint 8)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega la columna interes_sobre_capital_indexado si no existe.
    Retorna True si aplico el ALTER TABLE, False si la columna ya existia."""
    con = sqlite3.connect(db_path)
    try:
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        if "interes_sobre_capital_indexado" in columnas:
            return False
        con.execute(
            "ALTER TABLE obligaciones ADD COLUMN interes_sobre_capital_indexado "
            "BOOLEAN NOT NULL DEFAULT 0"
        )
        con.commit()
        return True
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columna interes_sobre_capital_indexado agregada a obligaciones.")
    else:
        print("La columna interes_sobre_capital_indexado ya existia, no se hizo nada.")
```

- [ ] **Step 5: Correr el test para confirmar que pasa**

Run: `pytest tests/scripts/test_migrate_interes_sobre_capital_indexado.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Correr la migración contra la base real**

Run: `python scripts/migrate_interes_sobre_capital_indexado.py`
Expected: `Columna interes_sobre_capital_indexado agregada a obligaciones.`

Verificar que la fila existente se preservó:

Run: `python -c "import sqlite3; con = sqlite3.connect('bastium.db'); print(con.execute('SELECT count(*) FROM obligaciones').fetchone())"`
Expected: `(1,)`

- [ ] **Step 7: Commit**

```bash
git status
git add database/models.py scripts/migrate_interes_sobre_capital_indexado.py tests/scripts/test_migrate_interes_sobre_capital_indexado.py
git commit -m "feat(db): add Obligacion.interes_sobre_capital_indexado column and migration"
```

Nota: `bastium.db` no se comitea. Confirmar con `git status` que no aparece en "Changes to be committed".

---

### Task 2: `LiquidationCore.usar_suma_unica` (motor core)

**Files:**
- Modify: `app/engine/liquidation/engine.py`
- Test: `tests/liquidation/test_engine.py`

Cambia la base de capital que alimenta el interés diario cuando `usar_suma_unica=True`. No se toca
`PendingDebt`, `BalanceEngine` ni `AllocationEngine` — el orden de imputación de pagos no depende de dónde
se computa el interés (ver spec, decisión 4).

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/liquidation/test_engine.py`:

```python
def test_engine_usar_suma_unica_false_interes_solo_sobre_principal():
    events = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"),
    ]
    rate = Rate.from_percent(Decimal("1.00"))  # 1% diario plano, tasa de control
    engine = LiquidationCore(default_daily_rate=rate, usar_suma_unica=False)

    result = engine.process(events, cutoff_date=date(2026, 1, 11))

    fb = result.final_balance()
    assert fb.principal == Decimal("1000.00")
    assert fb.indexation == Decimal("500.00")
    # 10 dias * 1000.00 * 1% = 100.00 -- solo sobre principal, indexation no cuenta
    assert fb.interest == Decimal("100.00")


def test_engine_usar_suma_unica_true_interes_sobre_principal_mas_indexation():
    events = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"),
    ]
    rate = Rate.from_percent(Decimal("1.00"))
    engine = LiquidationCore(default_daily_rate=rate, usar_suma_unica=True)

    result = engine.process(events, cutoff_date=date(2026, 1, 11))

    fb = result.final_balance()
    assert fb.principal == Decimal("1000.00")
    assert fb.indexation == Decimal("500.00")
    # 10 dias * (1000.00 + 500.00) * 1% = 150.00 -- interes sobre capital ya indexado
    assert fb.interest == Decimal("150.00")


def test_engine_usar_suma_unica_default_es_false():
    events = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"),
    ]
    rate = Rate.from_percent(Decimal("1.00"))
    engine = LiquidationCore(default_daily_rate=rate)  # sin pasar usar_suma_unica

    result = engine.process(events, cutoff_date=date(2026, 1, 11))

    assert result.final_balance().interest == Decimal("100.00")
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/liquidation/test_engine.py -k usar_suma_unica -v`
Expected: FAIL con `TypeError: LiquidationCore.__init__() got an unexpected keyword argument 'usar_suma_unica'`

- [ ] **Step 3: Implementar el cambio en `LiquidationCore`**

En `app/engine/liquidation/engine.py`, modificar `__init__` (líneas 20-25):

```python
    def __init__(
        self,
        default_daily_rate: Rate = Rate(Decimal("0.0")),
        rate_provider: Optional[RateProvider] = None,
        usar_suma_unica: bool = False,
    ):
        self._current_debt = PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
        self._history: List[LiquidationItem] = []
        self._default_rate = default_daily_rate
        self._rate_provider = rate_provider
        self._usar_suma_unica = usar_suma_unica
        self._last_event_date: Optional[date] = None
```

Y modificar `_accrue_time_passage` (líneas 88-109), la llamada a `DailyInterest.calculate` (líneas
100-104):

```python
        current_day = self._last_event_date + timedelta(days=1)
        total_interest_accumulated = Decimal("0.00")
        capital_base = self._current_debt.principal + (
            self._current_debt.indexation if self._usar_suma_unica else Decimal("0.00")
        )

        while current_day <= target_date:
            daily_rate = self._get_rate_for_date(current_day)
            daily_interest = DailyInterest.calculate(
                capital=capital_base,
                daily_rate=daily_rate,
                days=1
            )
            total_interest_accumulated += daily_interest
            current_day += timedelta(days=1)
```

Nota: `capital_base` se calcula **una sola vez antes del loop**, no dentro de él — igual que antes, el
loop asume capital constante durante toda la ventana de acumulación (ningún evento cambia `principal` ni
`indexation` entre `_last_event_date` y `target_date`, porque si hubiera un evento intermedio,
`_accrue_time_passage` se habría llamado con un `target_date` anterior primero). No cambiar la guarda de
la línea 92 (`if self._current_debt.principal <= Decimal("0.00"): return`) — sigue usando `principal` solo
para decidir si hay algo que acumular, no como base de cálculo.

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `pytest tests/liquidation/test_engine.py -v`
Expected: PASS en todos (los 3 nuevos + los existentes, que deben seguir en verde sin cambios)

- [ ] **Step 5: Commit**

```bash
git status
git add app/engine/liquidation/engine.py tests/liquidation/test_engine.py
git commit -m "feat(engine): add usar_suma_unica flag to LiquidationCore"
```

---

### Task 3: `UniversalLiquidationService` — pasar el parámetro

**Files:**
- Modify: `app/services/motor_universal.py`
- Test: `tests/services/test_motor_universal.py` (nuevo)

Facade sin lógica propia: solo reenvía `usar_suma_unica` al constructor de `LiquidationCore`.

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/services/test_motor_universal.py`:

```python
from datetime import date
from decimal import Decimal

from app.engine.temporal.schedulers.base import Event
from app.services.motor_universal import UniversalLiquidationService


def test_liquidar_reenvia_usar_suma_unica_al_motor_core():
    eventos = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"),
    ]

    resultado_legado = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos, pagos=[], fecha_corte=date(2026, 1, 11),
        tasa_estatica=Decimal("1.00"), usar_suma_unica=False,
    )
    resultado_suma_unica = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos, pagos=[], fecha_corte=date(2026, 1, 11),
        tasa_estatica=Decimal("1.00"), usar_suma_unica=True,
    )

    assert resultado_legado.final_balance().interest == Decimal("100.00")
    assert resultado_suma_unica.final_balance().interest == Decimal("150.00")


def test_liquidar_usar_suma_unica_default_es_false():
    eventos = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"),
    ]

    resultado = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos, pagos=[], fecha_corte=date(2026, 1, 11),
        tasa_estatica=Decimal("1.00"),
    )

    assert resultado.final_balance().interest == Decimal("100.00")
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `pytest tests/services/test_motor_universal.py -v`
Expected: FAIL con `TypeError: UniversalLiquidationService.liquidar() got an unexpected keyword argument 'usar_suma_unica'`

- [ ] **Step 3: Implementar el passthrough**

En `app/services/motor_universal.py`, modificar la firma de `liquidar` (líneas 18-25) y la construcción de
`LiquidationCore` (líneas 44-47):

```python
    def liquidar(
        self,
        eventos_causacion: List[Event],
        pagos: List[Payment],
        fecha_corte: date,
        tasa_estatica: Decimal = Decimal("0.0"),
        rate_provider: Optional[RateProvider] = None,
        usar_suma_unica: bool = False,
    ) -> LiquidationResult:
```

```python
        motor_calculo = LiquidationCore(
            default_daily_rate=tasa_mora,
            rate_provider=rate_provider,
            usar_suma_unica=usar_suma_unica,
        )
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `pytest tests/services/test_motor_universal.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git status
git add app/services/motor_universal.py tests/services/test_motor_universal.py
git commit -m "feat(services): thread usar_suma_unica through UniversalLiquidationService"
```

---

### Task 4: `CivilFamiliaStrategy._resolver_suma_unica` + wiring

**Files:**
- Modify: `app/services/area_strategy.py`
- Test: `tests/services/test_area_strategy.py`

Deriva el flag por expediente desde `Obligacion.interes_sobre_capital_indexado`, considerando solo las
obligaciones con `aplica_indexacion_ipc=True`, y rechaza combinaciones inconsistentes.

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/services/test_area_strategy.py`:

```python
def test_civil_familia_suma_unica_activa_interes_es_mayor_que_legado():
    obligacion_legado = Obligacion(
        id=6, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Dano emergente",
        categoria="DANO_EMERGENTE", fecha_origen=date(2024, 7, 1), valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=False,
    )
    obligacion_suma_unica = Obligacion(
        id=7, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Dano emergente",
        categoria="DANO_EMERGENTE", fecha_origen=date(2024, 7, 1), valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=True,
    )

    resultado_legado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_legado], abonos=[], fecha_corte=date(2025, 12, 31)
    )
    resultado_suma_unica = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_suma_unica], abonos=[], fecha_corte=date(2025, 12, 31)
    )

    # Mismo capital, misma indexacion (77633.53, ver test_civil_familia_puntual_con_indexacion_...),
    # misma tasa y periodo -- la unica diferencia es la base del interes.
    assert resultado_legado.final_balance().indexation == Decimal("77633.53")
    assert resultado_suma_unica.final_balance().indexation == Decimal("77633.53")
    assert resultado_legado.final_balance().interest == Decimal("87488.20")
    assert resultado_suma_unica.final_balance().interest == Decimal("94283.40")
    assert resultado_suma_unica.final_balance().interest > resultado_legado.final_balance().interest


def test_civil_familia_suma_unica_mezclada_en_el_expediente_lanza_value_error():
    obligacion_a = Obligacion(
        id=8, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Dano emergente A",
        categoria="DANO_EMERGENTE", fecha_origen=date(2024, 7, 1), valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=True,
    )
    obligacion_b = Obligacion(
        id=9, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Dano emergente B",
        categoria="DANO_EMERGENTE", fecha_origen=date(2024, 7, 1), valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=False,
    )

    with pytest.raises(ValueError, match="mismo criterio de interés"):
        CivilFamiliaStrategy().liquidar(
            obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=date(2025, 12, 31)
        )


def test_civil_familia_suma_unica_ignora_obligaciones_sin_indexacion_activa():
    obligacion_indexada = Obligacion(
        id=10, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Dano emergente",
        categoria="DANO_EMERGENTE", fecha_origen=date(2024, 7, 1), valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=True,
    )
    obligacion_sin_indexar = Obligacion(
        id=11, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Otro concepto",
        categoria="DANOS_MORALES", fecha_origen=date(2024, 7, 1), valor=Decimal("200000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=False,
        interes_sobre_capital_indexado=False,
    )

    # No debe lanzar ValueError: la obligacion sin indexacion activa no participa
    # en la validacion de consistencia, sin importar su propio valor del flag.
    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_indexada, obligacion_sin_indexar], abonos=[], fecha_corte=date(2025, 12, 31)
    )
    assert resultado.final_balance().indexation == Decimal("77633.53")
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/services/test_area_strategy.py -k suma_unica -v`
Expected: FAIL — `test_civil_familia_suma_unica_activa_interes_es_mayor_que_legado` falla porque
`resultado_suma_unica.final_balance().interest` da `87488.20` (igual al legado, el flag todavía no tiene
efecto); `test_civil_familia_suma_unica_mezclada_en_el_expediente_lanza_value_error` falla porque no se
lanza ningún `ValueError` (`DID NOT RAISE`).

- [ ] **Step 3: Implementar `_resolver_suma_unica` y el wiring**

En `app/services/area_strategy.py`, dentro de `CivilFamiliaStrategy`, modificar `liquidar` (líneas 88-109):

```python
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        usar_suma_unica = self._resolver_suma_unica(obligaciones)

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
            usar_suma_unica=usar_suma_unica,
        )

    def _resolver_suma_unica(self, obligaciones: List) -> bool:
        """Determina si el expediente completo liquida con el algoritmo "Suma
        Única" (interes sobre capital ya indexado, PDF pag. 21-22, incluye la
        variante Ley 80/1993 para contratos estatales -- misma mecanica, sin
        campo propio) en vez del legado (interes solo sobre capital historico).
        El interes se acumula sobre un unico PendingDebt para todo el
        expediente, asi que el criterio no puede variar obligacion por
        obligacion dentro del mismo expediente -- si dos obligaciones
        indexadas traen valores distintos de interes_sobre_capital_indexado,
        es un error de captura, no una combinacion valida."""
        valores = {
            bool(o.interes_sobre_capital_indexado)
            for o in obligaciones
            if o.aplica_indexacion_ipc
        }
        if len(valores) > 1:
            raise ValueError(
                "Todas las obligaciones con indexación IPC del expediente deben usar el mismo "
                "criterio de interés (Suma Única o legado); no se puede mezclar dentro del mismo "
                "expediente."
            )
        return valores == {True}
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `pytest tests/services/test_area_strategy.py -v`
Expected: PASS en todos (los 3 nuevos + los existentes de este archivo, que deben seguir en verde sin
cambios de resultado)

- [ ] **Step 5: Commit**

```bash
git status
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat(civil-familia): wire Suma Única interest via interes_sobre_capital_indexado"
```

---

### Task 5: Test del ejemplo numérico del PDF (pág. 69) — Definición de Hecho

**Files:**
- Test: `tests/services/test_area_strategy.py`

El PDF (pág. 69) certifica un crédito de $50.000.000 firmado el 1/1/2010 y liquidado el 1/1/2025, con el
resultado de la indexación ($71.428.571) calculado sobre índices IPC **ilustrativos** (140 → 200) que el
propio PDF usa solo como ejemplo pedagógico — no son los valores reales certificados por el DANE. La serie
real usada por el motor (`historical_index.py`, transcrita de las págs. 55-62 del mismo PDF) da un índice
distinto para esas fechas, así que el resultado de este test **no** coincide con el número ilustrativo de
la pág. 69 — coincide con lo que el motor calcula usando datos reales para las mismas fechas y el mismo
capital que cita el ejemplo. Ver spec, sección "Testing", para la justificación completa de esta distinción.

- [ ] **Step 1: Escribir el test que falla**

Agregar al final de `tests/services/test_area_strategy.py`:

```python
def test_pdf_pagina_69_ejemplo_credito_indexado_50_millones_2010_a_2025():
    # PDF pag. 69, "Actualizacion por IPC": capital $50.000.000 firmado el 1/1/2010,
    # liquidado el 1/1/2025. El PDF usa indices ilustrativos (140 -> 200, Va=$71.428.571)
    # solo como ejemplo pedagogico; este test usa la serie IPC real del motor
    # (historical_index.py, transcrita de las paginas 55-62 del mismo PDF) para las
    # mismas fechas y el mismo capital, por lo que el resultado numerico es distinto
    # del ilustrativo de la pag. 69 -- ver docstring del test y spec de este sprint.
    obligacion = Obligacion(
        id=12, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Credito indexado",
        categoria="DANO_EMERGENTE", fecha_origen=date(2010, 1, 1), valor=Decimal("50000000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=True,
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 1, 1)
    )

    fb = resultado.final_balance()
    # Va (capital ya indexado) = principal + indexation, calculado con la serie IPC
    # real: Va = 50.000.000 x (IPC(2025-01-01) / IPC(2010-01-01)).
    assert fb.principal == Decimal("50000000.00")
    assert fb.indexation == Decimal("51762113.73")
    va = fb.principal + fb.indexation
    assert va == Decimal("101762113.73")
    # Paso 2 (Suma Unica): interes civil 6% EA aplicado sobre Va, no sobre el capital
    # historico -- verificado independientemente replicando la acumulacion diaria del
    # motor (DailyInterest + EffectiveRateConverter) con capital=Va constante durante
    # todo el periodo (la indexacion se causa el mismo dia que el capital).
    assert fb.interest == Decimal("89015614.51")

    # Contraste: con el algoritmo legado (interes solo sobre el capital historico),
    # el mismo caso da un interes bastante menor -- confirma que Suma Unica
    # efectivamente cambia el resultado, no solo que el motor no truena.
    obligacion_legado = Obligacion(
        id=13, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Credito indexado",
        categoria="DANO_EMERGENTE", fecha_origen=date(2010, 1, 1), valor=Decimal("50000000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=False,
    )
    resultado_legado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_legado], abonos=[], fecha_corte=date(2025, 1, 1)
    )
    assert resultado_legado.final_balance().interest == Decimal("43737103.72")
    assert fb.interest > resultado_legado.final_balance().interest
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `pytest tests/services/test_area_strategy.py -k pdf_pagina_69 -v`
Expected: FAIL — `fb.interest` da `43737103.72` (Suma Única todavía no tenía efecto antes de la Task 4;
si la Task 4 ya está aplicada, este test debe ir directo a PASS).

- [ ] **Step 3: Correr el test para confirmar que pasa**

Run: `pytest tests/services/test_area_strategy.py -k pdf_pagina_69 -v`
Expected: PASS (no requiere cambios de código — este test valida el comportamiento ya implementado en la
Task 4; si falla aquí, hay una diferencia entre el cálculo manual y el motor real que hay que investigar
con `superpowers:systematic-debugging` antes de continuar)

- [ ] **Step 4: Commit**

```bash
git status
git add tests/services/test_area_strategy.py
git commit -m "test(civil-familia): verify Suma Única against PDF page 69 example (real IPC series)"
```

---

### Task 6: Checkbox "Suma Única" en la GUI

**Files:**
- Modify: `app/views/obligaciones.py`
- Test: `tests/views/test_obligaciones.py`

Checkbox hermano de `check_aplica_indexacion_ipc`, mismo patrón exacto (visibilidad, lectura en
`guardar()`).

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/views/test_obligaciones.py`:

```python
def test_check_interes_sobre_capital_indexado_visible_solo_en_civil_familia(qtbot, monkeypatch):
    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)
    dialog_civil.show()
    assert dialog_civil.check_interes_sobre_capital_indexado.isVisible() is True

    expediente_id_comercial = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)
    dialog_comercial = ObligacionFormDialog(expediente_id=expediente_id_comercial, area="COMERCIAL")
    qtbot.addWidget(dialog_comercial)
    dialog_comercial.show()
    assert dialog_comercial.check_interes_sobre_capital_indexado.isVisible() is False


def test_guarda_obligacion_con_interes_sobre_capital_indexado_marcado(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Dano emergente")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2024, 7, 1))
    dialog.check_aplica_indexacion_ipc.setChecked(True)
    dialog.check_interes_sobre_capital_indexado.setChecked(True)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.interes_sobre_capital_indexado is True
    session.close()


def test_guarda_obligacion_sin_marcar_interes_sobre_capital_indexado_queda_en_false(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Dano emergente")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2024, 7, 1))
    dialog.check_aplica_indexacion_ipc.setChecked(True)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.interes_sobre_capital_indexado is False
    session.close()
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/views/test_obligaciones.py -k interes_sobre_capital_indexado -v`
Expected: FAIL con `AttributeError: 'ObligacionFormDialog' object has no attribute 'check_interes_sobre_capital_indexado'`

- [ ] **Step 3: Agregar el checkbox al formulario**

En `app/views/obligaciones.py`, inmediatamente después de la línea 94
(`self.check_aplica_indexacion_ipc = QCheckBox(...)`):

```python
        self.check_interes_sobre_capital_indexado = QCheckBox(
            "Interés sobre capital ya indexado (algoritmo Suma Única / Ley 80 de 1993)"
        )
```

Inmediatamente después de la línea 144 (`self.layout_formulario.addRow(self.check_aplica_indexacion_ipc)`):

```python
        self.layout_formulario.addRow(self.check_interes_sobre_capital_indexado)
```

Inmediatamente después de la línea 179 (`self.check_aplica_indexacion_ipc.setVisible(self._area == "CIVIL_FAMILIA")`):

```python
        self.check_interes_sobre_capital_indexado.setVisible(self._area == "CIVIL_FAMILIA")
```

Inmediatamente después de la línea 386 (`aplica_indexacion_ipc=self.check_aplica_indexacion_ipc.isChecked(),`
dentro del constructor `Obligacion(...)` de `guardar()`):

```python
            interes_sobre_capital_indexado=self.check_interes_sobre_capital_indexado.isChecked(),
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `pytest tests/views/test_obligaciones.py -v`
Expected: PASS en todos (los 3 nuevos + los existentes de este archivo)

- [ ] **Step 5: Commit**

```bash
git status
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "feat(gui): add 'Interés sobre capital ya indexado' checkbox to ObligacionFormDialog"
```

---

### Task 7: Documentación

**Files:**
- Modify: `README.md`
- Modify: `docs/GUIA_USUARIO.md`
- Modify: `docs/specifications/03_motor_indexacion.md`
- Modify: `Pendientes.md`

Regla obligatoria de `Pendientes.md` (línea 12-16): al cerrar un sprint, `README.md` y
`docs/GUIA_USUARIO.md` deben reflejar el nuevo estado.

- [ ] **Step 1: Actualizar `README.md`**

En la sección "Estado actual" (línea 12, actualizar la fecha del encabezado a `2026-07-31`), dentro del
paréntesis de indexación IPC de Civil/Familia (línea 16), agregar después de "...para fechas
intermedias)":

```
, con la opción de aplicar el algoritmo "Suma Única" (Art. corrección monetaria + interés civil, PDF pág.
21-22: interés sobre el capital ya indexado en vez de sobre el capital histórico, también válido para
intereses de la Ley 80 de 1993 en contratos estatales)
```

Agregar un nuevo bloque de migración después del bloque del Sprint 12 (después de la línea 83, antes de
"**Si ya tenías `bastium.db` creado antes de este sprint**" del Sprint de parámetros legales):

```
**Si ya tenías `bastium.db` creado antes del Sprint 20**, corre una vez
`python scripts/migrate_interes_sobre_capital_indexado.py` antes de abrir la app — agrega la columna
`interes_sobre_capital_indexado` que el algoritmo "Suma Única" necesita. Igual que los scripts anteriores,
es idempotente y solo hace falta una vez por instalación.
```

- [ ] **Step 2: Actualizar `docs/GUIA_USUARIO.md`**

1. En la sección 5.3 (Agregar una obligación puntual), después del bullet "Aplica indexación IPC" (línea
   224-227), agregar:

```
   - **Interés sobre capital ya indexado**: marca esta casilla, además de "Aplica indexación IPC", si
     quieres el algoritmo "Suma Única" del PDF (pág. 21-22): primero se indexa el capital por IPC, y el
     interés del 6% se calcula sobre ese valor ya indexado, no sobre el capital histórico. Sin esta
     casilla, el interés se sigue calculando solo sobre el capital histórico (comportamiento anterior a
     este sprint). Ver [sección 7.7](#77-indexación-ipc-corrección-monetaria) para el detalle.
```

2. En la sección 5.4 (Agregar una obligación recurrente), después del bullet "Aplica indexación IPC"
   (línea 243-247), agregar el mismo bullet.

3. Reemplazar el bullet "**Qué NO hace todavía**" de la sección 7.7 (líneas 787-789) por:

```
- **Interés sobre capital ya indexado (algoritmo "Suma Única")**: desde el Sprint 20, marcando la casilla
  adicional **"Interés sobre capital ya indexado (algoritmo Suma Única / Ley 80 de 1993)"** junto a "Aplica
  indexación IPC", el interés del 6% (Art. 1617 C.C.) se calcula sobre el capital ya indexado (`Va`), no
  sobre el capital histórico — el algoritmo "Suma Única" del PDF (pág. 21-22), que también aplica a los
  intereses de la Ley 80 de 1993 para contratos estatales (misma mecánica, sin campo propio). Sin esta
  casilla marcada, el comportamiento es el mismo de antes de este sprint (interés solo sobre el capital
  histórico). No se puede mezclar dentro del mismo expediente: si dos obligaciones indexadas traen valores
  distintos de esta casilla, el programa rechaza la liquidación con un mensaje claro.
```

- [ ] **Step 3: Actualizar `docs/specifications/03_motor_indexacion.md`**

Reemplazar el bullet "El interes (Art. 1617 C.C.) se sigue calculando..." de la sección "Limitaciones
conocidas" (líneas 32-34) por:

```
- El interes (Art. 1617 C.C.) se calcula sobre el capital ya indexado ("Suma Única", PDF pag. 21-22) solo
  cuando `Obligacion.interes_sobre_capital_indexado` esta activo (ademas de `aplica_indexacion_ipc`) --
  opt-in explicito por obligacion, Sprint 20. Sin ese flag, el comportamiento es el mismo de antes: interes
  solo sobre el capital historico.
```

Y agregar al final de la sección "Componentes" (después de la línea 20):

```
- `LiquidationCore` (`app/engine/liquidation/engine.py`, Sprint 20): recibe `usar_suma_unica: bool` en el
  constructor; cuando es `True`, `_accrue_time_passage` calcula el interes diario sobre
  `principal + indexation` en vez de solo `principal`. `CivilFamiliaStrategy._resolver_suma_unica`
  (`app/services/area_strategy.py`) deriva el flag desde `Obligacion.interes_sobre_capital_indexado` y
  valida que no se mezclen criterios dentro del mismo expediente.
```

Actualizar la última línea (`Ver Pendientes.md, Sprint 8.`) a:

```
Ver `Pendientes.md`, Sprints 8 y 20.
```

- [ ] **Step 4: Actualizar `Pendientes.md`**

En la sección "## Sprint 20 — Indexación sobre capital ya indexado (algoritmo 'Suma Única')" (línea 1541),
agregar antes de la "**Definición de Hecho:**" final (antes de la línea 1600) un bloque `**Estado:**`:

```markdown
**Estado:** Implementado (2026-07-31) — ver
`docs/superpowers/plans/2026-07-31-sprint20-suma-unica.md` y
`docs/superpowers/specs/2026-07-31-sprint20-suma-unica-design.md`. Decisiones tomadas con el usuario
durante el brainstorming previo: (a) se migra al algoritmo exacto del PDF, no se deja como simplificación
del MVP; (b) `reconstruir_liquidacion()` (Sprint 9) deserializa un snapshot congelado y nunca recalcula, así
que el riesgo de retrocompatibilidad que anticipaba este sprint no aplicaba — no se necesitó ningún guard
especial para liquidaciones ya auditadas; (c) flag explícito por obligación
(`Obligacion.interes_sobre_capital_indexado`, default `False`), no un reemplazo global ni un parámetro a
nivel de expediente — mismo patrón que `aplica_indexacion_ipc`; (d) un expediente que mezcle obligaciones
indexadas con criterios de interés distintos lanza `ValueError` en vez de aplicar el criterio de una sola
obligación a todo el expediente en silencio. Hallazgo no anticipado en la redacción original de este
sprint: el bucket `PendingDebt.indexation` está compartido con `SANCION_TRIBUTARIA` (Tributario) — se
descartó separar el modelo de dominio porque el flag se resuelve por llamada a `liquidar()` y
`TributarioStrategy` nunca lo activa, así que las sanciones tributarias nunca entran a la base de interés
aunque compartan el bucket.
```

- [ ] **Step 5: Commit**

```bash
git status
git add README.md docs/GUIA_USUARIO.md docs/specifications/03_motor_indexacion.md Pendientes.md
git commit -m "docs: close out Sprint 20 (algoritmo Suma Única)"
```

---

### Task 8: Verificación final de la suite completa

**Files:** ninguno (solo verificación)

- [ ] **Step 1: Correr la suite completa**

Run: `pytest -v`
Expected: PASS en todos los tests (baseline antes de este sprint: 593 passed, 1 skipped; debe seguir en
verde, con los tests nuevos de las Tasks 1-6 sumados y ningún cambio de resultado en los existentes).

- [ ] **Step 2: Si algo falla, diagnosticar antes de continuar**

No commitear ni cerrar el sprint con tests rotos. Si algo falla, usar `superpowers:systematic-debugging`
antes de proponer un fix.

- [ ] **Step 3: Confirmar que no quedan cambios sin commitear**

Run: `git status`
Expected: `nothing to commit, working tree clean` (aparte de `bastium.db`, que no se versiona)
