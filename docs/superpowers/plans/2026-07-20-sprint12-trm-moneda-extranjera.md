# Sprint 12 — TRM y obligaciones en moneda extranjera: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que `ComercialStrategy` liquide obligaciones pactadas en USD, convirtiendo el capital a
pesos con una TRM ingresada manualmente por el abogado, antes de aplicar interés/mora/usura.

**Architecture:** Tres columnas nuevas en `Obligacion` (`moneda`, `trm_aplicable`, `trm_fecha_referencia`).
Un módulo nuevo `app/engine/currency/` con `TRMProvider`/`ManualTRMProvider` (mismo patrón que
`RateProvider`/`MemoryRateProvider`) y una función pura `convertir_a_pesos`. `ComercialStrategy` convierte
`obligacion.valor` a pesos una sola vez, antes de construir los eventos de causación — el resto del motor
(`UniversalLiquidationService`, interés, mora, usura) no cambia. GUI: dos campos nuevos condicionales en
`ObligacionFormDialog`.

**Tech Stack:** Python, SQLAlchemy 2.0 (`Mapped`/`mapped_column`), pytest, PySide6 (`pytest-qt`/`qtbot`),
sqlite3 (script de migración manual, sin Alembic).

**Spec:** `docs/superpowers/specs/2026-07-20-sprint12-trm-moneda-extranjera-design.md`

---

### Decisión técnica encontrada durante la planificación (no está en el spec, léela antes de empezar)

`Obligacion.moneda` tendrá `default="COP"` en `mapped_column`, pero ese default de SQLAlchemy **solo se
aplica al hacer `session.commit()`/flush** — un objeto `Obligacion(...)` construido directamente en un
test, sin sesión, queda con `obligacion.moneda is None` (verificado: así se comporta ya
`aplica_indexacion_ipc` hoy, ver comentario en `tests/services/test_area_strategy.py:122`, "aplica_indexacion_ipc
no seteado -> falsy"). Todos los fixtures de `tests/services/test_area_strategy.py` construyen `Obligacion`
así, sin sesión.

**Por eso, en todo el código de este sprint, `moneda in (None, "COP")` se trata como "sin conversión"** —
nunca solo `moneda == "COP"`. Si se usara solo `== "COP"`, cualquier obligación Comercial existente en los
tests (que no setean `moneda`) pasaría a requerir `trm_aplicable` y fallaría con `ValueError`, rompiendo
toda la suite de `TestComercialStrategy`.

---

### Task 1: Modelo de datos — columnas `moneda`, `trm_aplicable`, `trm_fecha_referencia`

**Files:**
- Modify: `database/models.py:47-76` (clase `Obligacion`)
- Test: `tests/database/test_models.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/database/test_models.py`:

```python
def test_obligacion_moneda_default_cop_al_no_especificarla(session):
    expediente = Expediente(
        radicado="2026-00132",
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

    assert obligacion.moneda == "COP"
    assert obligacion.trm_aplicable is None
    assert obligacion.trm_fecha_referencia is None


def test_obligacion_en_usd_guarda_trm_aplicable_y_fecha_referencia(session):
    expediente = Expediente(
        radicado="2026-00133",
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
        concepto="Capital de pagare en USD",
        categoria="CAPITAL_PAGARE",
        fecha_origen=date(2025, 1, 1),
        valor=Decimal("10000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        moneda="USD",
        trm_aplicable=Decimal("4150.2500"),
        trm_fecha_referencia=date(2025, 1, 1),
    )
    session.add(obligacion)
    session.commit()

    fetched = session.query(Obligacion).filter_by(id=obligacion.id).one()
    assert fetched.moneda == "USD"
    assert fetched.trm_aplicable == Decimal("4150.2500")
    assert fetched.trm_fecha_referencia == date(2025, 1, 1)
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/database/test_models.py -k "moneda" -v`
Expected: FAIL con `TypeError: 'moneda' is an invalid keyword argument for Obligacion` (la columna no existe
todavía).

- [ ] **Step 3: Agregar las columnas al modelo**

En `database/models.py`, dentro de la clase `Obligacion`, justo después de la línea
`aplica_indexacion_ipc: Mapped[bool] = mapped_column(Boolean, default=False)` (línea 71) y antes de la
línea en blanco que sigue:

```python
    moneda: Mapped[str] = mapped_column(String(3), default="COP")
    trm_aplicable: Mapped[Decimal | None] = mapped_column(Numeric(9, 4), nullable=True)
    trm_fecha_referencia: Mapped[date | None] = mapped_column(Date, nullable=True)
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `pytest tests/database/test_models.py -v`
Expected: PASS (todos, incluyendo los preexistentes — no debe romperse ninguno)

- [ ] **Step 5: Commit**

```bash
git add database/models.py tests/database/test_models.py
git commit -m "feat(db): add moneda/trm_aplicable/trm_fecha_referencia to Obligacion"
```

---

### Task 2: Script de migración de esquema

**Files:**
- Create: `scripts/migrate_moneda_trm.py`
- Test: `tests/scripts/test_migrate_moneda_trm.py`

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/scripts/test_migrate_moneda_trm.py`:

```python
import sqlite3

import pytest

from scripts.migrate_moneda_trm import migrar


@pytest.fixture
def db_sin_columnas(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY, concepto TEXT)")
    con.execute("INSERT INTO obligaciones (id, concepto) VALUES (1, 'Capital de pagare')")
    con.commit()
    con.close()
    return db_path


def test_migrar_agrega_las_tres_columnas_y_retorna_true(db_sin_columnas):
    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert {"moneda", "trm_aplicable", "trm_fecha_referencia"} <= columnas


def test_migrar_preserva_las_filas_existentes_con_moneda_cop_por_defecto(db_sin_columnas):
    migrar(db_sin_columnas)

    con = sqlite3.connect(db_sin_columnas)
    fila = con.execute(
        "SELECT concepto, moneda, trm_aplicable, trm_fecha_referencia FROM obligaciones WHERE id = 1"
    ).fetchone()
    con.close()
    assert fila == ("Capital de pagare", "COP", None, None)


def test_migrar_es_idempotente_segunda_corrida_retorna_false(db_sin_columnas):
    primera = migrar(db_sin_columnas)
    segunda = migrar(db_sin_columnas)
    assert primera is True
    assert segunda is False


def test_migrar_es_idempotente_si_ya_existe_solo_una_de_las_tres_columnas(db_sin_columnas):
    con = sqlite3.connect(db_sin_columnas)
    con.execute("ALTER TABLE obligaciones ADD COLUMN moneda VARCHAR(3) NOT NULL DEFAULT 'COP'")
    con.commit()
    con.close()

    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert {"moneda", "trm_aplicable", "trm_fecha_referencia"} <= columnas
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `pytest tests/scripts/test_migrate_moneda_trm.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'scripts.migrate_moneda_trm'`

- [ ] **Step 3: Implementar el script**

Crear `scripts/migrate_moneda_trm.py`:

```python
"""Migracion de esquema (Sprint 12): agrega las columnas moneda, trm_aplicable
y trm_fecha_referencia a la tabla obligaciones. Idempotente -- verifica con
PRAGMA table_info antes de alterar cada columna individualmente, para poder
correrse mas de una vez (ej. en otra maquina de desarrollo, en CI, o si una
corrida anterior quedo a medias) sin fallar. No usa Alembic porque el proyecto
todavia no tiene migraciones formales (mismo patron que
scripts/migrate_aplica_indexacion_ipc.py, Sprint 8)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "moneda": "VARCHAR(3) NOT NULL DEFAULT 'COP'",
    "trm_aplicable": "NUMERIC(9, 4)",
    "trm_fecha_referencia": "DATE",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas moneda/trm_aplicable/trm_fecha_referencia si no
    existen. Retorna True si aplico al menos un ALTER TABLE, False si las tres
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
        print("Columnas moneda/trm_aplicable/trm_fecha_referencia agregadas a obligaciones.")
    else:
        print("Las columnas ya existian, no se hizo nada.")
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `pytest tests/scripts/test_migrate_moneda_trm.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/migrate_moneda_trm.py tests/scripts/test_migrate_moneda_trm.py
git commit -m "feat(db): add migration script for moneda/trm_aplicable/trm_fecha_referencia"
```

---

### Task 3: `TRMProvider` / `ManualTRMProvider`

**Files:**
- Create: `app/engine/currency/__init__.py` (vacío)
- Create: `app/engine/currency/trm_provider.py`
- Test: `tests/engine/test_trm_provider.py`

- [ ] **Step 1: Crear el paquete**

Crear `app/engine/currency/__init__.py` vacío (mismo patrón que `app/engine/interest/__init__.py`).

- [ ] **Step 2: Escribir el test que falla**

Crear `tests/engine/test_trm_provider.py`:

```python
from datetime import date
from decimal import Decimal

import pytest

from app.engine.currency.trm_provider import ManualTRMProvider, TRMProvider


def test_manual_trm_provider_retorna_el_valor_sembrado():
    provider = ManualTRMProvider(Decimal("4150.2500"))
    assert provider.get_trm(date(2025, 1, 1)) == Decimal("4150.2500")


def test_manual_trm_provider_retorna_el_mismo_valor_para_cualquier_fecha():
    provider = ManualTRMProvider(Decimal("4000.0000"))
    assert provider.get_trm(date(2020, 1, 1)) == Decimal("4000.0000")
    assert provider.get_trm(date(2026, 12, 31)) == Decimal("4000.0000")


def test_trm_provider_es_abstracto_no_se_puede_instanciar():
    with pytest.raises(TypeError):
        TRMProvider()
```

- [ ] **Step 3: Correr el test para confirmar que falla**

Run: `pytest tests/engine/test_trm_provider.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.engine.currency.trm_provider'`

- [ ] **Step 4: Implementar `TRMProvider`/`ManualTRMProvider`**

Crear `app/engine/currency/trm_provider.py`:

```python
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal


class TRMProvider(ABC):
    """
    Contrato para cualquier fuente de TRM (Tasa Representativa del Mercado,
    Art. 874 C.Co.) usada para convertir obligaciones en moneda extranjera a
    pesos colombianos. Mismo patron que RateProvider (app/engine/interest/provider.py).
    """

    @abstractmethod
    def get_trm(self, fecha_referencia: date) -> Decimal:
        pass


class ManualTRMProvider(TRMProvider):
    """
    Proveedor MVP (Sprint 12): la TRM ya viene decidida por el abogado
    (Obligacion.trm_aplicable) -- no se busca en ninguna serie historica,
    porque el PDF fuente de BASTIUM no trae una (a diferencia de SMLMV/IPC/IBC,
    ver docs/superpowers/specs/2026-07-20-sprint12-trm-moneda-extranjera-design.md).
    Reemplazable por un HistoricalTRMProvider el dia que exista una serie real,
    sin tocar ComercialStrategy.
    """

    def __init__(self, trm: Decimal):
        self._trm = trm

    def get_trm(self, fecha_referencia: date) -> Decimal:
        return self._trm
```

- [ ] **Step 5: Correr el test para confirmar que pasa**

Run: `pytest tests/engine/test_trm_provider.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/engine/currency/__init__.py app/engine/currency/trm_provider.py tests/engine/test_trm_provider.py
git commit -m "feat(currency): add TRMProvider and ManualTRMProvider"
```

---

### Task 4: `convertir_a_pesos`

**Files:**
- Create: `app/engine/currency/converter.py`
- Test: `tests/engine/test_converter.py`

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/engine/test_converter.py`:

```python
from datetime import date
from decimal import Decimal

import pytest

from app.engine.currency.converter import convertir_a_pesos
from app.engine.currency.trm_provider import ManualTRMProvider


def test_moneda_cop_retorna_el_valor_sin_conversion_ni_provider():
    resultado = convertir_a_pesos(
        valor=Decimal("1000000.00"), moneda="COP", provider=None, fecha_referencia=date(2025, 1, 1)
    )
    assert resultado == Decimal("1000000.00")


def test_moneda_none_se_trata_igual_que_cop():
    resultado = convertir_a_pesos(
        valor=Decimal("1000000.00"), moneda=None, provider=None, fecha_referencia=date(2025, 1, 1)
    )
    assert resultado == Decimal("1000000.00")


def test_moneda_usd_convierte_multiplicando_por_la_trm():
    provider = ManualTRMProvider(Decimal("4150.2500"))
    resultado = convertir_a_pesos(
        valor=Decimal("10000.00"), moneda="USD", provider=provider, fecha_referencia=date(2025, 1, 1)
    )
    assert resultado == Decimal("41502500.00")


def test_moneda_usd_sin_provider_lanza_value_error():
    with pytest.raises(ValueError, match="requiere una TRM aplicable"):
        convertir_a_pesos(
            valor=Decimal("10000.00"), moneda="USD", provider=None, fecha_referencia=date(2025, 1, 1)
        )
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `pytest tests/engine/test_converter.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.engine.currency.converter'`

- [ ] **Step 3: Implementar `convertir_a_pesos`**

Crear `app/engine/currency/converter.py`:

```python
from datetime import date
from decimal import Decimal

from app.engine.currency.trm_provider import TRMProvider
from app.engine.math.rounding import Rounding


def convertir_a_pesos(
    valor: Decimal,
    moneda: str | None,
    provider: TRMProvider | None,
    fecha_referencia: date,
) -> Decimal:
    """
    Convierte `valor` a pesos colombianos segun `moneda`. Si `moneda` es "COP"
    o None (obligaciones sin moneda extranjera explicita), retorna `valor` sin
    tocar y sin requerir provider. Para cualquier otra moneda, requiere un
    TRMProvider -- Art. 874 C.Co. permite elegir entre la TRM de la fecha de la
    obligacion o la del pago; cual de las dos se usa es una decision del
    abogado (reflejada en `fecha_referencia`), no de esta funcion.
    """
    if moneda is None or moneda == "COP":
        return valor
    if provider is None:
        raise ValueError(f"Una obligacion en {moneda} requiere una TRM aplicable para convertir a pesos.")
    return Rounding.money(valor * provider.get_trm(fecha_referencia))
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `pytest tests/engine/test_converter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/engine/currency/converter.py tests/engine/test_converter.py
git commit -m "feat(currency): add convertir_a_pesos"
```

---

### Task 5: Wiring en `ComercialStrategy`

**Files:**
- Modify: `app/services/area_strategy.py:1-21` (imports), `:193-235` (`_validar_obligacion_comercial`,
  `_eventos_de_obligacion`)
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar dentro de `class TestComercialStrategy:` en `tests/services/test_area_strategy.py`, después del
método `test_items_tienen_rate_source_por_tramo` (antes de la línea en blanco que separa la clase de
`test_civil_familia_soporta_indexacion_ipc_es_true`):

```python
    def test_obligacion_en_usd_convierte_el_capital_a_pesos_antes_de_liquidar(self):
        obligacion_usd = _obligacion_comercial(valor=Decimal("10000.00"))
        obligacion_usd.moneda = "USD"
        obligacion_usd.trm_aplicable = Decimal("4000.0000")
        obligacion_usd.trm_fecha_referencia = date(2025, 1, 1)

        resultado_usd = ComercialStrategy().liquidar(
            obligaciones=[obligacion_usd], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        obligacion_cop = _obligacion_comercial(valor=Decimal("40000000.00"))
        resultado_cop = ComercialStrategy().liquidar(
            obligaciones=[obligacion_cop], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        assert resultado_usd.final_balance().principal == Decimal("40000000.00")
        assert resultado_usd.final_balance().interest == resultado_cop.final_balance().interest

    def test_obligacion_usd_sin_trm_aplicable_lanza_value_error(self):
        obligacion = _obligacion_comercial()
        obligacion.moneda = "USD"
        obligacion.trm_fecha_referencia = date(2025, 1, 1)

        with pytest.raises(ValueError, match="trm_aplicable"):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1))

    def test_obligacion_usd_sin_trm_fecha_referencia_lanza_value_error(self):
        obligacion = _obligacion_comercial()
        obligacion.moneda = "USD"
        obligacion.trm_aplicable = Decimal("4000.0000")

        with pytest.raises(ValueError, match="trm_fecha_referencia"):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1))

    def test_obligacion_sin_moneda_seteada_se_trata_como_cop(self):
        obligacion = _obligacion_comercial()
        assert obligacion.moneda is None  # atributo no seteado en construccion directa, sin sesion

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        assert resultado.final_balance().principal == obligacion.valor
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/services/test_area_strategy.py -k "usd or sin_moneda" -v`
Expected: FAIL — `test_obligacion_en_usd_convierte_el_capital_a_pesos_antes_de_liquidar` falla porque el
capital no se convierte (`final_balance().principal` da `10000.00`, no `40000000.00`); los dos tests de
`ValueError` fallan porque no se lanza ningún error (`moneda`/`trm_*` todavía no se validan).

- [ ] **Step 3: Agregar los imports nuevos**

En `app/services/area_strategy.py`, después de la línea `from app.engine.interest.rate_conversion import
EffectiveRateConverter` (línea 10):

```python
from app.engine.currency.converter import convertir_a_pesos
from app.engine.currency.trm_provider import ManualTRMProvider
```

- [ ] **Step 4: Extender `_validar_obligacion_comercial`**

En `app/services/area_strategy.py`, al final del método `_validar_obligacion_comercial` (después de las
dos líneas `validar_tasa_usura(...)`, antes del método `_eventos_de_obligacion`):

```python
        if obligacion.moneda not in (None, "COP"):
            if obligacion.trm_aplicable is None:
                raise ValueError(
                    f"La obligacion comercial '{obligacion.concepto}' esta en "
                    f"{obligacion.moneda} y necesita el campo 'trm_aplicable' para liquidar."
                )
            if obligacion.trm_fecha_referencia is None:
                raise ValueError(
                    f"La obligacion comercial '{obligacion.concepto}' esta en "
                    f"{obligacion.moneda} y necesita el campo 'trm_fecha_referencia' para liquidar."
                )
```

- [ ] **Step 5: Agregar `_valor_en_pesos` y usarlo en `_eventos_de_obligacion`**

Reemplazar el método `_eventos_de_obligacion` completo (líneas 216-235 del archivo original) por:

```python
    def _valor_en_pesos(self, obligacion) -> Decimal:
        if obligacion.moneda in (None, "COP"):
            return obligacion.valor
        provider = ManualTRMProvider(obligacion.trm_aplicable)
        return convertir_a_pesos(
            valor=obligacion.valor,
            moneda=obligacion.moneda,
            provider=provider,
            fecha_referencia=obligacion.trm_fecha_referencia,
        )

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

        # RECURRENTE
        scheduler = FamilyScheduler()
        scheduler.add_monthly_obligation(
            amount=valor_pesos,
            concept=obligacion.concepto,
            due_day=obligacion.dia_pago,
            category=obligacion.categoria,
        )
        fin = obligacion.fecha_fin or fecha_corte
        return scheduler.generate(start=obligacion.fecha_inicio, end=fin)
```

- [ ] **Step 6: Correr los tests para confirmar que pasan**

Run: `pytest tests/services/test_area_strategy.py -v`
Expected: PASS (todos, incluyendo los preexistentes de `TestComercialStrategy` y del resto del archivo —
ninguno debe romperse)

- [ ] **Step 7: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat(comercial): convert USD obligations to pesos before liquidating"
```

---

### Task 6: GUI — campos de moneda y TRM en `ObligacionFormDialog`

**Files:**
- Modify: `app/views/obligaciones.py`
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/views/test_obligaciones.py`:

```python
def test_combo_moneda_visible_solo_para_area_comercial(qtbot, monkeypatch):
    expediente_id_comercial = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)
    dialog_comercial = ObligacionFormDialog(expediente_id=expediente_id_comercial, area="COMERCIAL")
    qtbot.addWidget(dialog_comercial)
    dialog_comercial.show()
    assert dialog_comercial.combo_moneda.isVisible() is True

    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)
    dialog_civil.show()
    assert dialog_civil.combo_moneda.isVisible() is False


def test_campos_trm_visibles_solo_si_moneda_es_usd_en_comercial(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)
    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.combo_moneda.currentData() == "COP"
    assert dialog.campo_trm_aplicable.isVisible() is False
    assert dialog.campo_trm_fecha_referencia.isVisible() is False

    indice_usd = dialog.combo_moneda.findData("USD")
    dialog.combo_moneda.setCurrentIndex(indice_usd)
    assert dialog.campo_trm_aplicable.isVisible() is True
    assert dialog.campo_trm_fecha_referencia.isVisible() is True

    dialog.combo_moneda.setCurrentIndex(dialog.combo_moneda.findData("COP"))
    assert dialog.campo_trm_aplicable.isVisible() is False
    assert dialog.campo_trm_fecha_referencia.isVisible() is False


def test_guarda_obligacion_comercial_en_usd_con_trm(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Capital de pagare en USD")
    dialog.campo_valor.setText("10000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 1, 1))
    dialog.campo_tasa_moratoria.setText("24.00")
    dialog.campo_ibc_vigente.setText("20.00")
    dialog.campo_fecha_vencimiento.setDate(date(2025, 2, 1))
    dialog.combo_moneda.setCurrentIndex(dialog.combo_moneda.findData("USD"))
    dialog.campo_trm_aplicable.setText("4150.2500")
    dialog.campo_trm_fecha_referencia.setDate(date(2025, 1, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.moneda == "USD"
    assert guardada.trm_aplicable == Decimal("4150.2500")
    assert guardada.trm_fecha_referencia == date(2025, 1, 1)
    session.close()


def test_guarda_obligacion_comercial_en_cop_deja_trm_en_none(qtbot, monkeypatch):
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
    assert guardada.moneda == "COP"
    assert guardada.trm_aplicable is None
    assert guardada.trm_fecha_referencia is None
    session.close()
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/views/test_obligaciones.py -k "moneda or trm or usd" -v`
Expected: FAIL con `AttributeError: 'ObligacionFormDialog' object has no attribute 'combo_moneda'`

- [ ] **Step 3: Agregar los widgets nuevos**

En `app/views/obligaciones.py`, después de la línea `self.campo_ibc_vigente = QLineEdit()` (línea 71):

```python
        self.combo_moneda = QComboBox()
        self.combo_moneda.addItem("COP (peso colombiano)", userData="COP")
        self.combo_moneda.addItem("USD (dolar)", userData="USD")
        self.campo_trm_aplicable = QLineEdit()
        self.campo_trm_fecha_referencia = QDateEdit(QDate.currentDate())
        self.campo_trm_fecha_referencia.setCalendarPopup(True)
```

- [ ] **Step 4: Agregarlos al layout del formulario**

Después de la línea `self.layout_formulario.addRow("IBC vigente aplicable (%)", self.campo_ibc_vigente)`
(línea 102):

```python
        self.layout_formulario.addRow("Moneda", self.combo_moneda)
        self.layout_formulario.addRow("TRM aplicable (COP por USD)", self.campo_trm_aplicable)
        self.layout_formulario.addRow("Fecha de referencia de la TRM", self.campo_trm_fecha_referencia)
```

- [ ] **Step 5: Visibilidad estática de `combo_moneda` (por área)**

Después de la línea `self.campo_ibc_vigente.setVisible(es_comercial)` (línea 122):

```python
        self.combo_moneda.setVisible(es_comercial)
```

- [ ] **Step 6: Visibilidad dinámica de los campos TRM (por moneda seleccionada)**

Agregar un nuevo método, justo antes de `_actualizar_campos_visibles` (línea 162):

```python
    def _actualizar_visibilidad_trm(self) -> None:
        es_comercial = self._area == "COMERCIAL"
        es_usd = self.combo_moneda.currentData() == "USD"
        self.campo_trm_aplicable.setVisible(es_comercial and es_usd)
        self.campo_trm_fecha_referencia.setVisible(es_comercial and es_usd)
```

En el bloque de `connect()` al final de `__init__` (después de
`self.check_pagada.stateChanged.connect(self._actualizar_campos_visibles)`, línea 158, antes de
`self._actualizar_campos_visibles()`):

```python
        self.combo_moneda.currentIndexChanged.connect(self._actualizar_visibilidad_trm)
```

Y después de la llamada `self._actualizar_campos_visibles()` (línea 160):

```python
        self._actualizar_visibilidad_trm()
```

- [ ] **Step 7: Parsear y guardar los campos nuevos en `guardar()`**

Reemplazar el bloque (líneas 224-236 del archivo original):

```python
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
```

por:

```python
        tasa_moratoria = None
        fecha_vencimiento = None
        ibc_vigente = None
        moneda = "COP"
        trm_aplicable = None
        trm_fecha_referencia = None
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
```

- [ ] **Step 8: Pasar los campos nuevos al constructor de `Obligacion`**

En el mismo método `guardar()`, dentro del `Obligacion(...)` (después de la línea
`aplica_indexacion_ipc=self.check_aplica_indexacion_ipc.isChecked(),`):

```python
            moneda=moneda,
            trm_aplicable=trm_aplicable,
            trm_fecha_referencia=trm_fecha_referencia,
```

- [ ] **Step 9: Correr los tests para confirmar que pasan**

Run: `pytest tests/views/test_obligaciones.py -v`
Expected: PASS (todos, incluyendo los preexistentes)

- [ ] **Step 10: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "feat(gui): add moneda/TRM fields to ObligacionFormDialog"
```

---

### Task 7: Migrar `bastium.db` real

**Files:** ninguno (solo ejecución)

- [ ] **Step 1: Correr la migración contra la base real**

Run: `python scripts/migrate_moneda_trm.py`
Expected: `Columnas moneda/trm_aplicable/trm_fecha_referencia agregadas a obligaciones.`

- [ ] **Step 2: Verificar que las filas existentes se preservaron**

Run:
```bash
python -c "import sqlite3; con = sqlite3.connect('bastium.db'); print(con.execute('SELECT id, concepto, moneda FROM obligaciones').fetchall()); con.close()"
```
Expected: la(s) fila(s) existente(s) aparecen con `moneda == 'COP'`, sin perder ningún dato.

- [ ] **Step 3: Arrancar la app y confirmar que abre sin error**

Run: `python main.py` (verificar manualmente que la Lista de Expedientes carga sin excepción, luego
cerrar la app)

No hay commit en este paso — `bastium.db` no está bajo control de versiones (mismo criterio que
`scripts/migrate_aplica_indexacion_ipc.py`, Sprint 8).

---

### Task 8: Documentación (`README.md`, `docs/GUIA_USUARIO.md`)

**Files:**
- Modify: `README.md:17`, `README.md` (después de línea 60, nota de migración)
- Modify: `docs/GUIA_USUARIO.md:272-298` (sección 5.7), `docs/GUIA_USUARIO.md` (nueva sección 7.8),
  `docs/GUIA_USUARIO.md:615-616` (sección 8)

- [ ] **Step 1: `README.md` — mencionar TRM en la descripción de Comercial**

En `README.md:17`, reemplazar:

```
**Comercial** (Art. 884 C.Co., tasas remuneratoria y moratoria pactadas por obligación con
split real antes/después del vencimiento, validación de tope de usura 1.5×IBC), **Sancionatorio**
```

por:

```
**Comercial** (Art. 884 C.Co., tasas remuneratoria y moratoria pactadas por obligación con
split real antes/después del vencimiento, validación de tope de usura 1.5×IBC, y obligaciones en USD
convertidas a pesos con la TRM ingresada por el abogado, Art. 874 C.Co.), **Sancionatorio**
```

- [ ] **Step 2: `README.md` — nota de migración**

Después del párrafo que termina en "...solo hace falta una vez por instalación." (línea 60), agregar:

```markdown

**Si ya tenías `bastium.db` creado antes del Sprint 12**, corre una vez
`python scripts/migrate_moneda_trm.py` antes de abrir la app — agrega las columnas `moneda`,
`trm_aplicable` y `trm_fecha_referencia` que necesitan las obligaciones comerciales en moneda extranjera.
Igual que el script del Sprint 8, es idempotente y solo hace falta una vez por instalación.
```

- [ ] **Step 3: `docs/GUIA_USUARIO.md` — ampliar sección 5.7 (obligación comercial)**

En `docs/GUIA_USUARIO.md`, dentro de la sección `### 5.7. Agregar una obligación comercial`, reemplazar el
punto 3 completo (líneas 281-293) por:

```markdown
3. Llena además:
   - **Tasa moratoria anual (%)**: la tasa que aplica después de que la obligación vence y no se paga.
     Si no se pactó una distinta, la ley comercial (Art. 884 C.Co.) sugiere 1.5× el IBC vigente, pero el
     campo siempre se diligencia manualmente — no hay cálculo automático todavía (ver `Pendientes.md`,
     Sprint 5).
   - **Fecha de vencimiento**: la fecha en que la obligación se hace exigible. Para obligaciones
     **Puntuales**, antes de esta fecha se usa la tasa remuneratoria y después la moratoria. Para
     obligaciones **Recurrentes**, este split todavía no aplica por cuota — se usa la tasa moratoria
     durante todo el período (alcance reducido de este sprint, ver `Pendientes.md`, Sprint 2). El campo
     igual es obligatorio para ambos tipos.
   - **IBC vigente aplicable (%)**: el Interés Bancario Corriente certificado por la Superintendencia
     Financiera para la fecha del caso. Se usa únicamente para validar que ninguna de las dos tasas
     pactadas supere el tope legal de usura (1.5× este valor).
   - **Moneda**: "COP" por defecto. Si la obligación está pactada en dólares, elige "USD" — aparecen dos
     campos adicionales (ver punto 4).
4. Si elegiste **Moneda = USD**, llena también:
   - **TRM aplicable (COP por USD)**: cuántos pesos vale un dólar para este caso (Art. 874 C.Co.: se
     puede pactar la TRM de la fecha de la obligación o la del pago — el abogado decide cuál usar y la
     ingresa directamente aquí, no hay una serie histórica cargada en el programa — ver
     [sección 7.8](#78-trm-y-obligaciones-en-moneda-extranjera)).
   - **Fecha de referencia de la TRM**: la fecha que sustenta el valor anterior, solo para trazabilidad —
     el programa no vuelve a buscar nada con esta fecha, es un dato de auditoría.
5. Haz clic en **"Guardar"**.
```

Y actualizar el último párrafo de la sección (línea 296-298, "Si alguna tasa pactada...") renumerando el
paso final de "4." a "6." si el generador de la guía usa numeración automática de pasos — revisar
visualmente el render final.

- [ ] **Step 4: `docs/GUIA_USUARIO.md` — nueva sección 7.8**

Después de la sección `### 7.7. Indexación IPC (corrección monetaria)` (después de la línea 579, antes de
la línea `---` que la separa de la sección 8), agregar:

```markdown

### 7.8. TRM y obligaciones en moneda extranjera

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente Comercial,
  el campo **"Moneda"** y, si se elige "USD", los campos **"TRM aplicable (COP por USD)"** y **"Fecha de
  referencia de la TRM"** — ver [sección 5.7](#57-agregar-una-obligación-comercial).
- **Dónde vive la lógica en el código**: `app/engine/currency/converter.py` (`convertir_a_pesos`) y
  `app/engine/currency/trm_provider.py` (`ManualTRMProvider`), invocados desde
  `ComercialStrategy._valor_en_pesos` en `app/services/area_strategy.py`.
- **Cómo se calcula**: el capital de la obligación se convierte a pesos **una sola vez**, multiplicando el
  valor en dólares por la TRM que ingresó el abogado, antes de que empiece a correr cualquier interés. A
  partir de ahí, la obligación se liquida exactamente igual que cualquier obligación comercial en pesos —
  interés remuneratorio, mora y validación de usura no cambian.
- **De dónde sale la TRM**: el abogado la ingresa directamente. El PDF fuente de BASTIUM (a diferencia de
  SMLMV, IPC e IBC/Usura) no trae una serie histórica de TRM diaria, así que el programa no la busca
  automáticamente — Art. 874 C.Co. permite usar la TRM de la fecha de la obligación o la de la fecha de
  pago, y esa elección queda en manos del abogado según el caso.
- **Qué NO hace todavía**: no soporta otras monedas extranjeras distintas de USD, no reconvierte el
  capital pendiente en cada abono (la conversión es única, al inicio), y no existe todavía una serie
  histórica de TRM precargada en el programa.
```

- [ ] **Step 5: `docs/GUIA_USUARIO.md` — actualizar sección 8 (funciones pendientes)**

En `docs/GUIA_USUARIO.md:615-616`, reemplazar:

```markdown
- 🚧 **Derecho Tributario, TRM/moneda extranjera, motor de reglas configurable** — dominios nuevos, de
  menor prioridad, ver `Pendientes.md`, Sprints 11, 12 y 13.
```

por:

```markdown
- ✅ **TRM y obligaciones en moneda extranjera** ya está conectada al área Comercial (Sprint 12) — ver
  [sección 7.8](#78-trm-y-obligaciones-en-moneda-extranjera).
- 🚧 **Derecho Tributario, motor de reglas configurable** — dominios nuevos, de menor prioridad, ver
  `Pendientes.md`, Sprints 11 y 13.
```

- [ ] **Step 6: Commit**

```bash
git add README.md docs/GUIA_USUARIO.md
git commit -m "docs: document Sprint 12 (TRM y moneda extranjera)"
```

---

### Task 9: Suite completa y cierre

**Files:** ninguno

- [ ] **Step 1: Correr toda la suite**

Run: `pytest -v`
Expected: PASS en todos los tests (los preexistentes y los agregados en este plan). Ninguna regresión.

- [ ] **Step 2: Confirmar smoke test manual end-to-end (GUI real)**

Run: `python main.py`
- Crear (o abrir) un expediente con Área del derecho = Comercial.
- Agregar una obligación: Tipo Puntual, Valor `10000.00`, Tasa efectiva anual `6.00`, Tasa moratoria
  `24.00`, IBC vigente `20.00`, Fecha de vencimiento posterior a la fecha de origen, Moneda = USD, TRM
  aplicable `4150.25`, Fecha de referencia = fecha de origen.
- Guardar, luego hacer clic en "Liquidar".
- Confirmar que el resultado no lanza error y que el capital que aparece corresponde a `10000.00 ×
  4150.25 = 41,502,500.00` pesos (no a `10000.00`).
- Cerrar la app.

- [ ] **Step 3: Actualizar `Pendientes.md`**

Marcar el Sprint 12 como hecho: cambiar `## Sprint 12 — TRM y obligaciones en moneda extranjera 🔴
Pendiente` (línea 717) a `## Sprint 12 — TRM y obligaciones en moneda extranjera ✅ Hecho` — revisar cómo
se marcaron sprints anteriores ya cerrados (ej. Sprint 8) en el mismo archivo para seguir exactamente el
mismo formato de cierre (fecha, resumen breve, etc.) antes de escribir el cambio.

- [ ] **Step 4: Commit final**

```bash
git add Pendientes.md
git commit -m "docs: mark Sprint 12 (TRM y moneda extranjera) as done"
```
