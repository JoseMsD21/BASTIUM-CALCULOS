# Sprint 4 — Área Sancionatorio y Honorarios Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `SancionatorioStrategy.liquidar()` (multas administrativas convertidas desde SMLMV, con tope pre-2020) y `HonorariosStrategy.liquidar()` (honorarios fijos + cuota litis validados contra ambos topes legales, con costas judiciales opcionales), habilitando ambas áreas end-to-end en la GUI.

**Architecture:** Reutiliza la infraestructura existente `AreaStrategy` / `UniversalLiquidationService` / `MemoryRateProvider` / `Event` / `Payment` exactamente como `CivilFamiliaStrategy` y `ComercialStrategy` — ninguna de las dos áreas nuevas toca `LiquidationCore` ni `UniversalLiquidationService`. Cinco columnas nuevas nullable en `Obligacion` cargan los datos específicos de estas dos áreas. Un conversor nuevo (`smlmv_to_uvt.py`) resuelve SMLMV→pesos para hechos anteriores a 2020-01-01 y lanza un error explícito para fechas posteriores (no hay tabla UVT histórica todavía). Dos excepciones de dominio nuevas (`UVTNoDisponibleError`, `CuotaLitisExcedeTopeError`) siguen el patrón de `TasaUsurariaError` del Sprint 2.

**Tech Stack:** Python 3.14, SQLAlchemy (declarative models, SQLite), PySide6 (GUI), pytest + pytest-qt.

**Design doc:** `docs/superpowers/specs/2026-07-17-sprint4-sancionatorio-honorarios-design.md` — léelo primero si algo abajo no queda claro; ahí está el razonamiento completo (incluyendo por qué se resolvió el 30%/50% de cuota litis como topes simultáneos, no excluyentes).

---

### Task 1: Nuevas excepciones de dominio

**Files:**
- Modify: `app/core/exceptions.py`

- [ ] **Step 1: Agregar las dos excepciones**

`app/core/exceptions.py` hoy tiene `AreaNoImplementadaError` y `TasaUsurariaError`. Añade al final:

```python
class UVTNoDisponibleError(Exception):
    """Se lanza cuando se necesita el valor de UVT para una fecha posterior a 2020-01-01
    y no hay tabla historica cargada (ver Pendientes.md Sprint 5)."""


class CuotaLitisExcedeTopeError(Exception):
    """Se lanza cuando honorarios fijos + cuota litis exceden el tope legal (30% cuota
    litis sola, 50% suma total del beneficio obtenido)."""
```

Archivo completo después del cambio:

```python
class AreaNoImplementadaError(Exception):
    """Se lanza cuando se intenta liquidar un area del derecho aun no implementada."""


class TasaUsurariaError(Exception):
    """Se lanza cuando una tasa pactada (remuneratoria o moratoria) supera 1.5x el IBC vigente."""


class UVTNoDisponibleError(Exception):
    """Se lanza cuando se necesita el valor de UVT para una fecha posterior a 2020-01-01
    y no hay tabla historica cargada (ver Pendientes.md Sprint 5)."""


class CuotaLitisExcedeTopeError(Exception):
    """Se lanza cuando honorarios fijos + cuota litis exceden el tope legal (30% cuota
    litis sola, 50% suma total del beneficio obtenido)."""
```

- [ ] **Step 2: Commit**

```bash
git add app/core/exceptions.py
git commit -m "feat(core): add UVTNoDisponibleError and CuotaLitisExcedeTopeError"
```

---

### Task 2: Datos — nuevas columnas en `Obligacion`

**Files:**
- Modify: `database/models.py:44-62`
- Delete: `bastium.db` (repo root)

- [ ] **Step 1: Agregar las cinco columnas nuevas**

En `database/models.py`, dentro de `class Obligacion(Base):`, agrega estas líneas justo después de `ibc_vigente_anual` (línea 62):

```python
    ibc_vigente_anual: Mapped[Decimal | None] = mapped_column(Numeric(9, 4), nullable=True)
    cantidad_smlmv_uvt: Mapped[Decimal | None] = mapped_column(Numeric(9, 4), nullable=True)
    honorarios_fijos_pactados: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    cuota_litis_pactada_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    beneficio_obtenido: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    costas_pct_manual: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
```

Las cinco son nullable a nivel de esquema (Civil/Familia/Comercial nunca las usan); `SancionatorioStrategy` y `HonorariosStrategy` exigen que estén presentes al momento de liquidar (Tasks 5 y 6).

- [ ] **Step 2: Verificar que el cambio de modelo no rompe nada existente**

Run: `python -m pytest tests/services/test_area_strategy.py tests/views/test_obligaciones.py -q`
Expected: mismo conteo de pass que antes de este cambio (todos los tests existentes usan SQLite en memoria creado con `Base.metadata.create_all`, así que las columnas nuevas no requieren tocar ningún test todavía).

- [ ] **Step 3: Borrar la base de datos local para que se recree con el esquema nuevo**

```bash
rm bastium.db
```

`bastium.db` está vacía (0 expedientes, confirmado antes de empezar este sprint) y se recrea automáticamente la próxima vez que corra `python main.py` (llama a `init_db()`, que llama a `Base.metadata.create_all(engine)`).

- [ ] **Step 4: Commit**

```bash
git add database/models.py
git commit -m "feat(db): add cantidad_smlmv_uvt, honorarios_fijos_pactados, cuota_litis_pactada_pct, beneficio_obtenido, costas_pct_manual to Obligacion"
```

(`bastium.db` ya está en `.gitignore` — confirma con `git status` que no aparece antes de comitear; si aparece, no lo agregues.)

---

### Task 3: Conversor SMLMV↔UVT

**Files:**
- Create: `app/engine/indexation/smlmv_to_uvt.py`
- Test: `tests/engine/test_smlmv_to_uvt.py`

- [ ] **Step 1: Escribir los tests que fallan**

Crea `tests/engine/test_smlmv_to_uvt.py`:

```python
from datetime import date
from decimal import Decimal

import pytest

from app.core.exceptions import UVTNoDisponibleError
from app.engine.indexation.smlmv_to_uvt import resolver_base_sancion


def test_hecho_pre_2020_usa_smlmv_del_anio_del_hecho():
    # SMLMV 2019 = 828116.00 (ver historical_index.py, verificado contra el PDF pag. 55-57).
    resultado = resolver_base_sancion(date(2019, 6, 1), Decimal("2"))
    assert resultado == Decimal("1656232.00")


def test_hecho_dia_anterior_al_corte_2020_usa_smlmv_2019():
    resultado = resolver_base_sancion(date(2019, 12, 31), Decimal("1"))
    assert resultado == Decimal("828116.00")


def test_hecho_exactamente_2020_01_01_ya_requiere_uvt_y_lanza_error():
    with pytest.raises(UVTNoDisponibleError):
        resolver_base_sancion(date(2020, 1, 1), Decimal("1"))


def test_hecho_posterior_a_2020_lanza_uvt_no_disponible_error():
    with pytest.raises(UVTNoDisponibleError):
        resolver_base_sancion(date(2021, 1, 1), Decimal("1"))
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `python -m pytest tests/engine/test_smlmv_to_uvt.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.engine.indexation.smlmv_to_uvt'`

- [ ] **Step 3: Implementar el conversor**

Crea `app/engine/indexation/smlmv_to_uvt.py`:

```python
from datetime import date
from decimal import Decimal

from app.core.exceptions import UVTNoDisponibleError
from app.engine.indexation.historical_index import get_smlmv_for_year
from app.engine.indexation.smmlv import SMMLVCalculator

FECHA_CORTE_SMLMV_A_UVT = date(2020, 1, 1)


def resolver_base_sancion(fecha_hecho: date, cantidad: Decimal) -> Decimal:
    """
    Convierte una cantidad de SMLMV o UVT a pesos, segun la fecha del hecho sancionatorio
    (Ley 1955 de 2019, art. 49): antes del 2020-01-01 la base es el SMLMV del año del
    hecho; desde esa fecha, la base es la UVT vigente de la DIAN.

    La tabla historica de UVT aun no existe (ver Pendientes.md Sprint 5 -- el PDF de
    requisitos no trae una serie completa por año, solo menciones dispersas). Por eso,
    fechas posteriores al corte lanzan UVTNoDisponibleError en vez de inventar un valor.
    """
    if fecha_hecho < FECHA_CORTE_SMLMV_A_UVT:
        smlmv_del_anio = get_smlmv_for_year(fecha_hecho.year)
        return SMMLVCalculator.to_pesos(cantidad, smlmv_del_anio)

    raise UVTNoDisponibleError(
        f"No hay tabla historica de UVT cargada para calcular el hecho sancionatorio "
        f"del {fecha_hecho} (posterior a 2020-01-01). Ver Pendientes.md, Sprint 5."
    )
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `python -m pytest tests/engine/test_smlmv_to_uvt.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/engine/indexation/smlmv_to_uvt.py tests/engine/test_smlmv_to_uvt.py
git commit -m "feat(indexation): add SMLMV-to-UVT converter for pre-2020 hechos sancionatorios"
```

---

### Task 4: Registrar los códigos de capital nuevos

**Files:**
- Modify: `app/engine/liquidation/engine.py:28-33`
- Modify: `app/core/constants.py`

- [ ] **Step 1: Escribir el test que falla**

En `tests/services/test_area_strategy.py`, junto al test existente `test_capital_concepts_incluye_los_codigos_comerciales_nuevos` (línea 126), agrega:

```python
def test_capital_concepts_incluye_los_codigos_sancionatorio_y_honorarios():
    core = LiquidationCore()
    assert "MULTA_SANCIONATORIA" in core._capital_concepts
    assert "HONORARIOS_PROFESIONALES" in core._capital_concepts
    assert "COSTAS_PROCESALES" in core._capital_concepts
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `python -m pytest tests/services/test_area_strategy.py::test_capital_concepts_incluye_los_codigos_sancionatorio_y_honorarios -v`
Expected: FAIL — `AssertionError`

- [ ] **Step 3: Agregar los códigos a `_capital_concepts`**

En `app/engine/liquidation/engine.py`, el set actual (líneas 28-33) es:

```python
        self._capital_concepts = {
            "INSTALLMENT", "CHILD_SUPPORT", "CLOTHING", "MULTA",
            "CESANTIAS", "INTERESES_CESANTIAS", "PRIMA_JUNIO", "PRIMA_DICIEMBRE", "SANCION_MORATORIA",
            "DANO_EMERGENTE", "LUCRO_CESANTE_CONSOLIDADO", "DANOS_MORALES", "CAPITAL_PAGARE",
            "CAPITAL_LETRA_CAMBIO", "CAPITAL_CHEQUE", "CAPITAL_FACTURA"
        }
```

Cámbialo a:

```python
        self._capital_concepts = {
            "INSTALLMENT", "CHILD_SUPPORT", "CLOTHING", "MULTA",
            "CESANTIAS", "INTERESES_CESANTIAS", "PRIMA_JUNIO", "PRIMA_DICIEMBRE", "SANCION_MORATORIA",
            "DANO_EMERGENTE", "LUCRO_CESANTE_CONSOLIDADO", "DANOS_MORALES", "CAPITAL_PAGARE",
            "CAPITAL_LETRA_CAMBIO", "CAPITAL_CHEQUE", "CAPITAL_FACTURA",
            "MULTA_SANCIONATORIA", "HONORARIOS_PROFESIONALES", "COSTAS_PROCESALES"
        }
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `python -m pytest tests/services/test_area_strategy.py::test_capital_concepts_incluye_los_codigos_sancionatorio_y_honorarios -v`
Expected: PASS

- [ ] **Step 5: Agregar las listas de categorías y habilitar las áreas en `constants.py`**

`app/core/constants.py` hoy termina así:

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

Reemplázalo por:

```python
CATEGORIAS_COMERCIAL = [
    ("CAPITAL_PAGARE", "Capital de pagare"),
    ("CAPITAL_LETRA_CAMBIO", "Capital de letra de cambio"),
    ("CAPITAL_CHEQUE", "Capital de cheque"),
    ("CAPITAL_FACTURA", "Capital de factura"),
]
# Nota: igual que CATEGORIAS_CIVIL_FAMILIA, cada codigo debe existir en
# app.engine.liquidation.engine.LiquidationCore._capital_concepts.

CATEGORIAS_SANCIONATORIO = [
    ("MULTA_SANCIONATORIA", "Multa sancionatoria (SMLMV/UVT)"),
]
# Solo una categoria: una obligacion Sancionatorio siempre genera un unico evento de
# capital ("MULTA_SANCIONATORIA"), convertido desde cantidad_smlmv_uvt.

CATEGORIAS_HONORARIOS = [
    ("HONORARIOS_PROFESIONALES", "Honorarios profesionales (fijo + cuota litis)"),
]
# "COSTAS_PROCESALES" no aparece aqui: no es una categoria que el usuario elija, se
# genera automaticamente como un segundo evento si costas_pct_manual esta seteado
# (ver HonorariosStrategy._eventos_de_obligacion).

AREAS_DERECHO = [
    ("CIVIL_FAMILIA", "Civil / Familia", True),
    ("COMERCIAL", "Comercial", True),
    ("LABORAL", "Laboral", False),
    ("SANCIONATORIO", "Sancionatorio", True),
    ("HONORARIOS", "Honorarios / Litigio", True),
]
# El tercer valor de cada tupla indica si el area esta habilitada para calcular
# en este sprint. Ver Pendientes.md para el orden de habilitacion de las demas.
```

- [ ] **Step 6: Correr toda la suite para confirmar que nada se rompió**

Run: `python -m pytest -q`
Expected: todos los tests pasan (nada distinto de lo que pasaba antes, `AREAS_DERECHO` habilitado en `True` no cambia ningún test existente).

- [ ] **Step 7: Commit**

```bash
git add app/engine/liquidation/engine.py app/core/constants.py tests/services/test_area_strategy.py
git commit -m "feat(core): register MULTA_SANCIONATORIA, HONORARIOS_PROFESIONALES, COSTAS_PROCESALES capital concepts and enable both areas"
```

---

### Task 5: `SancionatorioStrategy.liquidar()`

**Files:**
- Modify: `app/services/area_strategy.py:1-16` (imports), `:216-220` (clase)
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/services/test_area_strategy.py`, agrega (usa el import de `date`/`Decimal` ya existente en el archivo):

```python
from app.core.exceptions import UVTNoDisponibleError


def _obligacion_sancionatoria(
    expediente_id=1,
    cantidad_smlmv_uvt=Decimal("2"),
    fecha_origen=date(2019, 6, 1),
    tasa_efectiva_anual=Decimal("0.00"),
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Multa SIC",
        categoria="MULTA_SANCIONATORIA",
        fecha_origen=fecha_origen,
        valor=Decimal("0.00"),
        tasa_efectiva_anual=tasa_efectiva_anual,
        cantidad_smlmv_uvt=cantidad_smlmv_uvt,
    )


class TestSancionatorioStrategy:
    def test_liquida_multa_pre_2020_convirtiendo_smlmv_a_pesos(self):
        obligacion = _obligacion_sancionatoria()

        resultado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2019, 6, 1)
        )

        # SMLMV 2019 = 828116.00 (ver historical_index.py); 2 SMLMV = 1656232.00.
        assert resultado.final_balance().principal == Decimal("1656232.00")

    def test_liquida_multa_posterior_a_2020_lanza_uvt_no_disponible_error(self):
        obligacion = _obligacion_sancionatoria(fecha_origen=date(2021, 1, 1))

        with pytest.raises(UVTNoDisponibleError):
            SancionatorioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_falta_cantidad_smlmv_uvt_lanza_value_error(self):
        obligacion = _obligacion_sancionatoria(cantidad_smlmv_uvt=None)

        with pytest.raises(ValueError):
            SancionatorioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2019, 6, 1)
            )

    def test_obligacion_recurrente_lanza_value_error(self):
        obligacion = _obligacion_sancionatoria()
        obligacion.tipo = TipoObligacion.RECURRENTE

        with pytest.raises(ValueError):
            SancionatorioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2019, 6, 1)
            )

    def test_multa_impaga_acumula_interes_moratorio_si_se_pacto_tasa(self):
        obligacion = _obligacion_sancionatoria(tasa_efectiva_anual=Decimal("24.00"))

        resultado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2020, 6, 1)
        )

        assert resultado.final_balance().interest > Decimal("0.00")

    def test_soporta_indexacion_ipc_es_false(self):
        assert SancionatorioStrategy().soporta_indexacion_ipc is False
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `python -m pytest tests/services/test_area_strategy.py::TestSancionatorioStrategy -v`
Expected: FAIL — `AreaNoImplementadaError` en vez de los resultados/errores esperados (la clase actual solo lanza esa excepción siempre).

- [ ] **Step 3: Implementar `SancionatorioStrategy`**

En `app/services/area_strategy.py`, agrega este import junto a los demás (línea 14, después de `usury_validator`):

```python
from app.engine.indexation.smlmv_to_uvt import resolver_base_sancion
```

Reemplaza el stub actual (líneas 216-220):

```python
class SancionatorioStrategy(AreaStrategy):
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise AreaNoImplementadaError(
            "El area Sancionatorio (conversion SMLMV a UVT) esta pendiente. Ver Pendientes.md."
        )
```

por:

```python
class SancionatorioStrategy(AreaStrategy):
    """
    Area Sancionatorio (multas SIC/Penal/Ambiental/Urbano en SMLMV o UVT, Ley 1955/2019
    art. 49). Cada obligacion es un hecho puntual: `cantidad_smlmv_uvt` se convierte a
    pesos segun la fecha del hecho (`fecha_origen`) via `resolver_base_sancion` -- SMLMV
    si es anterior a 2020-01-01, UVT (todavia no disponible) si es posterior.

    No soporta obligaciones RECURRENTE (una multa es un hecho unico).
    No es compatible con indexacion IPC: el monto ya esta expresado en una unidad
    actualizada (SMLMV/UVT), indexarlo otra vez seria doble indexacion.
    """

    soporta_indexacion_ipc = False

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_sancionatoria(obligacion)

        eventos_causacion = [self._evento_de_obligacion(obligacion) for obligacion in obligaciones]

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

    def _validar_obligacion_sancionatoria(self, obligacion) -> None:
        if obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion sancionatoria '{obligacion.concepto}' debe ser PUNTUAL "
                f"(una multa es un hecho unico, no admite RECURRENTE)."
            )
        if obligacion.cantidad_smlmv_uvt is None:
            raise ValueError(
                f"La obligacion sancionatoria '{obligacion.concepto}' necesita el campo "
                f"'cantidad_smlmv_uvt' para liquidar."
            )

    def _evento_de_obligacion(self, obligacion) -> Event:
        monto_pesos = resolver_base_sancion(obligacion.fecha_origen, obligacion.cantidad_smlmv_uvt)
        return Event(
            date=obligacion.fecha_origen,
            payload={"amount": monto_pesos, "label": obligacion.concepto},
            event_type=obligacion.categoria,
        )

    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        fecha_mas_antigua = min(o.fecha_origen for o in obligaciones)
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligaciones[0].tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_mas_antigua - timedelta(days=1), end=fecha_corte, rate=tasa_diaria
        )
        return provider
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `python -m pytest tests/services/test_area_strategy.py::TestSancionatorioStrategy -v`
Expected: 6 passed

- [ ] **Step 5: Correr toda la suite**

Run: `python -m pytest -q`
Expected: todos pasan (nótese que `test_areas_no_implementadas_lanzan_error_claro_al_liquidar`, parametrizado con `SANCIONATORIO`, ahora debe quedar solo con `LABORAL` y `HONORARIOS` — ver Step 6).

- [ ] **Step 6: Quitar `SANCIONATORIO` del test parametrizado de "áreas no implementadas"**

En `tests/services/test_area_strategy.py`, el test (línea 30) hoy es:

```python
@pytest.mark.parametrize(
    "area_name,strategy_cls",
    [
        ("LABORAL", LaboralStrategy),
        ("SANCIONATORIO", SancionatorioStrategy),
        ("HONORARIOS", HonorariosStrategy),
    ],
)
def test_areas_no_implementadas_lanzan_error_claro_al_liquidar(area_name, strategy_cls):
```

Cámbialo a (quita solo la entrada `SANCIONATORIO`; `HONORARIOS` se quita en el Task 6):

```python
@pytest.mark.parametrize(
    "area_name,strategy_cls",
    [
        ("LABORAL", LaboralStrategy),
        ("HONORARIOS", HonorariosStrategy),
    ],
)
def test_areas_no_implementadas_lanzan_error_claro_al_liquidar(area_name, strategy_cls):
```

- [ ] **Step 7: Correr toda la suite otra vez**

Run: `python -m pytest -q`
Expected: todos pasan.

- [ ] **Step 8: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat(sancionatorio): implement SancionatorioStrategy.liquidar with SMLMV conversion"
```

---

### Task 6: `HonorariosStrategy.liquidar()`

**Files:**
- Modify: `app/services/area_strategy.py:1-16` (imports), `:~230-234` (clase, número de línea cambia tras Task 5)
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/services/test_area_strategy.py`, agrega:

```python
from app.core.exceptions import CuotaLitisExcedeTopeError


def _obligacion_honorarios(
    expediente_id=1,
    honorarios_fijos_pactados=Decimal("1000000.00"),
    cuota_litis_pactada_pct=Decimal("20.00"),
    beneficio_obtenido=Decimal("10000000.00"),
    costas_pct_manual=None,
    fecha_origen=date(2026, 1, 1),
    tasa_efectiva_anual=Decimal("0.00"),
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Honorarios proceso ejecutivo",
        categoria="HONORARIOS_PROFESIONALES",
        fecha_origen=fecha_origen,
        valor=Decimal("0.00"),
        tasa_efectiva_anual=tasa_efectiva_anual,
        honorarios_fijos_pactados=honorarios_fijos_pactados,
        cuota_litis_pactada_pct=cuota_litis_pactada_pct,
        beneficio_obtenido=beneficio_obtenido,
        costas_pct_manual=costas_pct_manual,
    )


class TestHonorariosStrategy:
    def test_liquida_honorarios_dentro_de_ambos_topes(self):
        # cuota litis = 10M * 20% = 2M (20% <= 30% tope individual, OK).
        # total = 1M + 2M = 3M (30% <= 50% tope total, OK).
        obligacion = _obligacion_honorarios()

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
        )

        assert resultado.final_balance().principal == Decimal("3000000.00")

    def test_cuota_litis_sola_excede_30_por_ciento_lanza_error(self):
        # cuota litis = 10M * 35% = 3.5M > 3M (30% de 10M).
        obligacion = _obligacion_honorarios(
            honorarios_fijos_pactados=Decimal("0.00"), cuota_litis_pactada_pct=Decimal("35.00")
        )

        with pytest.raises(CuotaLitisExcedeTopeError):
            HonorariosStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1))

    def test_suma_total_excede_50_por_ciento_aunque_cuota_litis_sola_no_exceda_30(self):
        # cuota litis = 10M * 25% = 2.5M (25% <= 30%, OK individualmente).
        # total = 3M + 2.5M = 5.5M > 5M (50% de 10M) -> debe fallar por el tope total.
        obligacion = _obligacion_honorarios(
            honorarios_fijos_pactados=Decimal("3000000.00"), cuota_litis_pactada_pct=Decimal("25.00")
        )

        with pytest.raises(CuotaLitisExcedeTopeError):
            HonorariosStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1))

    def test_genera_evento_de_costas_si_costas_pct_manual_esta_seteado(self):
        # honorarios = 1M + (10M*10%=1M) = 2M. costas = 10M * 5% = 500000.
        obligacion = _obligacion_honorarios(
            cuota_litis_pactada_pct=Decimal("10.00"), costas_pct_manual=Decimal("5.00")
        )

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
        )

        assert resultado.final_balance().principal == Decimal("2500000.00")

    def test_sin_costas_pct_manual_no_genera_evento_de_costas(self):
        obligacion = _obligacion_honorarios(cuota_litis_pactada_pct=Decimal("10.00"))

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
        )

        # honorarios = 1M + (10M*10%=1M) = 2M, sin costas.
        assert resultado.final_balance().principal == Decimal("2000000.00")

    @pytest.mark.parametrize(
        "campo", ["honorarios_fijos_pactados", "cuota_litis_pactada_pct", "beneficio_obtenido"]
    )
    def test_falta_un_campo_obligatorio_lanza_value_error(self, campo):
        obligacion = _obligacion_honorarios()
        setattr(obligacion, campo, None)

        with pytest.raises(ValueError):
            HonorariosStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1))

    def test_obligacion_recurrente_lanza_value_error(self):
        obligacion = _obligacion_honorarios()
        obligacion.tipo = TipoObligacion.RECURRENTE

        with pytest.raises(ValueError):
            HonorariosStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1))

    def test_soporta_indexacion_ipc_es_false(self):
        assert HonorariosStrategy().soporta_indexacion_ipc is False
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `python -m pytest tests/services/test_area_strategy.py::TestHonorariosStrategy -v`
Expected: FAIL — `AreaNoImplementadaError` en vez de los resultados/errores esperados.

- [ ] **Step 3: Implementar `HonorariosStrategy`**

En `app/services/area_strategy.py`, agrega este import junto a los demás:

```python
from app.core.exceptions import AreaNoImplementadaError, CuotaLitisExcedeTopeError
```

(reemplaza la línea 6 existente `from app.core.exceptions import AreaNoImplementadaError` por la línea de arriba, que ahora importa las dos).

Reemplaza el stub actual de `HonorariosStrategy`:

```python
class HonorariosStrategy(AreaStrategy):
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise AreaNoImplementadaError(
            "El area Honorarios (cuota litis) esta pendiente. Ver Pendientes.md."
        )
```

por:

```python
class HonorariosStrategy(AreaStrategy):
    """
    Area Honorarios / Litigio (cobro de honorarios profesionales y costas judiciales).
    Cada obligacion es un hecho puntual que resulta en 1 o 2 eventos de capital:
    honorarios profesionales (tarifa fija + cuota litis, validados contra ambos topes
    legales) y, si se pacto un porcentaje de costas, un evento adicional de costas
    procesales. No hay tabla hardcodeada de rangos del Consejo Superior de la
    Judicatura (Acuerdo PCSJA20-11556): el porcentaje de costas lo ingresa quien
    liquida, fijado por el juez en el auto respectivo (ver Pendientes.md).

    Tope de cuota litis (ambos simultaneos -- ver design spec 2026-07-17, el PDF trae
    un 50% en una seccion y un 30% en otra, se aplican los dos):
    - cuota litis sola <= 30% del beneficio obtenido (Ley 1123/2007, CPC).
    - honorarios fijos + cuota litis <= 50% del beneficio obtenido (limite
      jurisprudencial y etico).

    No soporta obligaciones RECURRENTE. No es compatible con indexacion IPC.
    """

    TOPE_CUOTA_LITIS_INDIVIDUAL_PCT = Decimal("30")
    TOPE_HONORARIOS_TOTAL_PCT = Decimal("50")

    soporta_indexacion_ipc = False

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_honorarios(obligacion)

        eventos_causacion: List[Event] = []
        for obligacion in obligaciones:
            eventos_causacion.extend(self._eventos_de_obligacion(obligacion))

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

    def _validar_obligacion_honorarios(self, obligacion) -> None:
        if obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion de honorarios '{obligacion.concepto}' debe ser PUNTUAL."
            )
        campos_requeridos = {
            "honorarios_fijos_pactados": obligacion.honorarios_fijos_pactados,
            "cuota_litis_pactada_pct": obligacion.cuota_litis_pactada_pct,
            "beneficio_obtenido": obligacion.beneficio_obtenido,
        }
        for nombre_campo, valor in campos_requeridos.items():
            if valor is None:
                raise ValueError(
                    f"La obligacion de honorarios '{obligacion.concepto}' necesita el campo "
                    f"'{nombre_campo}' para liquidar."
                )

        cuota_litis_monto = self._cuota_litis_monto(obligacion)
        tope_individual = obligacion.beneficio_obtenido * self.TOPE_CUOTA_LITIS_INDIVIDUAL_PCT / Decimal("100")
        if cuota_litis_monto > tope_individual:
            raise CuotaLitisExcedeTopeError(
                f"La cuota litis pactada ({obligacion.cuota_litis_pactada_pct}%) de "
                f"'{obligacion.concepto}' equivale a {cuota_litis_monto}, que excede el tope "
                f"del 30% del beneficio obtenido ({tope_individual})."
            )

        total_honorarios = obligacion.honorarios_fijos_pactados + cuota_litis_monto
        tope_total = obligacion.beneficio_obtenido * self.TOPE_HONORARIOS_TOTAL_PCT / Decimal("100")
        if total_honorarios > tope_total:
            raise CuotaLitisExcedeTopeError(
                f"La suma de honorarios fijos + cuota litis de '{obligacion.concepto}' "
                f"({total_honorarios}) excede el tope del 50% del beneficio obtenido ({tope_total})."
            )

    def _cuota_litis_monto(self, obligacion) -> Decimal:
        return obligacion.beneficio_obtenido * obligacion.cuota_litis_pactada_pct / Decimal("100")

    def _eventos_de_obligacion(self, obligacion) -> List[Event]:
        cuota_litis_monto = self._cuota_litis_monto(obligacion)
        total_honorarios = obligacion.honorarios_fijos_pactados + cuota_litis_monto

        eventos = [
            Event(
                date=obligacion.fecha_origen,
                payload={"amount": total_honorarios, "label": obligacion.concepto},
                event_type="HONORARIOS_PROFESIONALES",
            )
        ]
        if obligacion.costas_pct_manual is not None:
            costas_monto = obligacion.beneficio_obtenido * obligacion.costas_pct_manual / Decimal("100")
            eventos.append(
                Event(
                    date=obligacion.fecha_origen,
                    payload={
                        "amount": costas_monto,
                        "label": f"Costas procesales - {obligacion.concepto}",
                    },
                    event_type="COSTAS_PROCESALES",
                )
            )
        return eventos

    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        fecha_mas_antigua = min(o.fecha_origen for o in obligaciones)
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligaciones[0].tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_mas_antigua - timedelta(days=1), end=fecha_corte, rate=tasa_diaria
        )
        return provider
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `python -m pytest tests/services/test_area_strategy.py::TestHonorariosStrategy -v`
Expected: 8 passed

- [ ] **Step 5: Quitar `HONORARIOS` del test parametrizado de "áreas no implementadas"**

En `tests/services/test_area_strategy.py`, el test (ajustado en el Task 5, Step 6) queda ahora sin ningún elemento salvo `LABORAL`:

```python
@pytest.mark.parametrize(
    "area_name,strategy_cls",
    [
        ("LABORAL", LaboralStrategy),
    ],
)
def test_areas_no_implementadas_lanzan_error_claro_al_liquidar(area_name, strategy_cls):
```

- [ ] **Step 6: Correr toda la suite**

Run: `python -m pytest -q`
Expected: todos pasan.

- [ ] **Step 7: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat(honorarios): implement HonorariosStrategy.liquidar with dual cuota-litis cap validation"
```

---

### Task 7: GUI — extender `ObligacionFormDialog`

**Files:**
- Modify: `app/views/obligaciones.py`
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/views/test_obligaciones.py`, agrega (usa `_expediente_de_prueba` ya definido en el archivo):

```python
def test_guarda_obligacion_sancionatoria(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.SANCIONATORIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="SANCIONATORIO")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Multa SIC")
    dialog.campo_tasa.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2019, 6, 1))
    dialog.campo_cantidad_smlmv_uvt.setText("2")

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.cantidad_smlmv_uvt == Decimal("2")
    session.close()


def test_guarda_obligacion_honorarios_con_costas(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="HONORARIOS")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Honorarios proceso ejecutivo")
    dialog.campo_tasa.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2026, 1, 1))
    dialog.campo_honorarios_fijos.setText("1000000.00")
    dialog.campo_cuota_litis_pct.setText("20.00")
    dialog.campo_beneficio_obtenido.setText("10000000.00")
    dialog.campo_costas_pct.setText("5.00")

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.honorarios_fijos_pactados == Decimal("1000000.00")
    assert guardada.cuota_litis_pactada_pct == Decimal("20.00")
    assert guardada.beneficio_obtenido == Decimal("10000000.00")
    assert guardada.costas_pct_manual == Decimal("5.00")
    session.close()


def test_guarda_obligacion_honorarios_sin_costas_queda_en_none(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="HONORARIOS")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Honorarios sin costas")
    dialog.campo_tasa.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2026, 1, 1))
    dialog.campo_honorarios_fijos.setText("500000.00")
    dialog.campo_cuota_litis_pct.setText("10.00")
    dialog.campo_beneficio_obtenido.setText("5000000.00")

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.costas_pct_manual is None
    session.close()


def test_campos_sancionatorio_y_honorarios_ocultos_para_area_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_cantidad_smlmv_uvt.isVisible() is False
    assert dialog.campo_honorarios_fijos.isVisible() is False
    assert dialog.campo_cuota_litis_pct.isVisible() is False
    assert dialog.campo_beneficio_obtenido.isVisible() is False
    assert dialog.campo_costas_pct.isVisible() is False
    assert dialog.campo_valor.isVisible() is True


def test_campos_sancionatorio_visibles_solo_para_esa_area(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.SANCIONATORIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="SANCIONATORIO")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_cantidad_smlmv_uvt.isVisible() is True
    assert dialog.campo_valor.isVisible() is False
    assert dialog.campo_honorarios_fijos.isVisible() is False


def test_campos_honorarios_visibles_solo_para_esa_area(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="HONORARIOS")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_honorarios_fijos.isVisible() is True
    assert dialog.campo_cuota_litis_pct.isVisible() is True
    assert dialog.campo_beneficio_obtenido.isVisible() is True
    assert dialog.campo_costas_pct.isVisible() is True
    assert dialog.campo_valor.isVisible() is False
    assert dialog.campo_cantidad_smlmv_uvt.isVisible() is False
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `python -m pytest tests/views/test_obligaciones.py -v`
Expected: FAIL — `AttributeError: 'ObligacionFormDialog' object has no attribute 'campo_cantidad_smlmv_uvt'` (y similares para los otros campos nuevos).

- [ ] **Step 3: Importar las listas de categorías nuevas**

En `app/views/obligaciones.py`, línea 17, cambia:

```python
from app.core.constants import CATEGORIAS_CIVIL_FAMILIA, CATEGORIAS_COMERCIAL
```

por:

```python
from app.core.constants import (
    CATEGORIAS_CIVIL_FAMILIA,
    CATEGORIAS_COMERCIAL,
    CATEGORIAS_HONORARIOS,
    CATEGORIAS_SANCIONATORIO,
)
```

- [ ] **Step 4: Seleccionar la lista de categorías correcta por área**

Reemplaza la línea 34:

```python
        categorias = CATEGORIAS_COMERCIAL if self._area == "COMERCIAL" else CATEGORIAS_CIVIL_FAMILIA
```

por:

```python
        categorias_por_area = {
            "COMERCIAL": CATEGORIAS_COMERCIAL,
            "SANCIONATORIO": CATEGORIAS_SANCIONATORIO,
            "HONORARIOS": CATEGORIAS_HONORARIOS,
        }
        categorias = categorias_por_area.get(self._area, CATEGORIAS_CIVIL_FAMILIA)
```

- [ ] **Step 5: Agregar los campos de formulario nuevos**

Después de la línea `self.campo_ibc_vigente = QLineEdit()` (línea 54), agrega:

```python
        self.campo_cantidad_smlmv_uvt = QLineEdit()

        self.campo_honorarios_fijos = QLineEdit()
        self.campo_cuota_litis_pct = QLineEdit()
        self.campo_beneficio_obtenido = QLineEdit()
        self.campo_costas_pct = QLineEdit()
```

- [ ] **Step 6: Agregar las filas al formulario**

Después de `self.layout_formulario.addRow("IBC vigente aplicable (%)", self.campo_ibc_vigente)` (línea 70), agrega:

```python
        self.layout_formulario.addRow("Cantidad SMLMV/UVT (Sancionatorio)", self.campo_cantidad_smlmv_uvt)
        self.layout_formulario.addRow("Honorarios fijos pactados", self.campo_honorarios_fijos)
        self.layout_formulario.addRow("% Cuota litis pactada", self.campo_cuota_litis_pct)
        self.layout_formulario.addRow("Beneficio obtenido por el cliente", self.campo_beneficio_obtenido)
        self.layout_formulario.addRow("% Costas judiciales (opcional)", self.campo_costas_pct)
```

- [ ] **Step 7: Controlar la visibilidad por área**

Reemplaza el bloque (líneas 74-77):

```python
        es_comercial = self._area == "COMERCIAL"
        self.campo_tasa_moratoria.setVisible(es_comercial)
        self.campo_fecha_vencimiento.setVisible(es_comercial)
        self.campo_ibc_vigente.setVisible(es_comercial)
```

por:

```python
        es_comercial = self._area == "COMERCIAL"
        es_sancionatorio = self._area == "SANCIONATORIO"
        es_honorarios = self._area == "HONORARIOS"

        self.campo_tasa_moratoria.setVisible(es_comercial)
        self.campo_fecha_vencimiento.setVisible(es_comercial)
        self.campo_ibc_vigente.setVisible(es_comercial)

        self.campo_cantidad_smlmv_uvt.setVisible(es_sancionatorio)

        self.campo_honorarios_fijos.setVisible(es_honorarios)
        self.campo_cuota_litis_pct.setVisible(es_honorarios)
        self.campo_beneficio_obtenido.setVisible(es_honorarios)
        self.campo_costas_pct.setVisible(es_honorarios)

        # "Valor" no aplica a Sancionatorio/Honorarios: el monto se calcula a partir de
        # los campos de arriba (cantidad_smlmv_uvt, o honorarios+cuota litis+costas).
        self.campo_valor.setVisible(not es_sancionatorio and not es_honorarios)
```

- [ ] **Step 8: Actualizar `guardar()` para leer y persistir los campos nuevos**

Reemplaza el método `guardar()` completo (líneas 87-137):

```python
    def guardar(self) -> int:
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
            cantidad_smlmv_uvt=cantidad_smlmv_uvt,
            honorarios_fijos_pactados=honorarios_fijos,
            cuota_litis_pactada_pct=cuota_litis_pct,
            beneficio_obtenido=beneficio_obtenido,
            costas_pct_manual=costas_pct,
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

- [ ] **Step 9: Correr los tests para confirmar que pasan**

Run: `python -m pytest tests/views/test_obligaciones.py -v`
Expected: todos pasan (los 6 tests existentes + los 6 nuevos).

- [ ] **Step 10: Correr toda la suite**

Run: `python -m pytest -q`
Expected: todos pasan.

- [ ] **Step 11: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "feat(gui): wire Sancionatorio and Honorarios fields into ObligacionFormDialog"
```

---

### Task 8: Verificación manual end-to-end y documentación

**Files:**
- Modify: `README.md`
- Modify: `docs/GUIA_USUARIO.md`
- Modify: `Pendientes.md`

- [ ] **Step 1: Correr la suite completa**

Run: `python -m pytest -q`
Expected: todos los tests pasan (los existentes antes de este sprint + todos los agregados en las Tasks 1-7).

- [ ] **Step 2: Smoke test manual — Sancionatorio**

```bash
python main.py
```

1. Clic en "Nuevo expediente". Radicado `2026-060`, Demandante `Estado`, Demandado `Empresa XYZ`,
   **Área del derecho = Sancionatorio** (debe ser seleccionable, no gris), Fecha de corte `2019-12-01`.
   Guardar.
2. Doble clic para abrir el detalle.
3. "Agregar obligación". Confirma que aparece el campo "Cantidad SMLMV/UVT (Sancionatorio)" y que
   "Valor" está oculto. Llena: Tipo = Puntual, Categoría = "Multa sancionatoria (SMLMV/UVT)",
   Concepto = "Multa SIC", Tasa efectiva anual = `0.00`, Fecha de origen = `2019-06-01`,
   Cantidad SMLMV/UVT = `2`. Guardar.
4. Clic en "Liquidar". Confirma que la pantalla de Resultado abre sin error, con capital
   `1,656,232.00` (2 × SMLMV 2019).

Expected: sin crash, sin mensaje "Área no implementada", capital coincide con el valor esperado.

- [ ] **Step 3: Smoke test manual — Honorarios con costas**

1. "Nuevo expediente". Radicado `2026-061`, Demandante `Cliente`, Demandado `Contraparte`,
   **Área del derecho = Honorarios / Litigio**, Fecha de corte `2026-01-01`. Guardar.
2. Doble clic para abrir el detalle.
3. "Agregar obligación". Confirma que aparecen los cuatro campos de Honorarios y que "Valor" y
   "Cantidad SMLMV/UVT" están ocultos. Llena: Tipo = Puntual, Categoría = "Honorarios profesionales",
   Concepto = "Honorarios proceso ejecutivo", Tasa efectiva anual = `0.00`, Fecha de origen =
   `2026-01-01`, Honorarios fijos = `1000000.00`, % Cuota litis = `20.00`, Beneficio obtenido =
   `10000000.00`, % Costas = `5.00`. Guardar.
4. Clic en "Liquidar". Confirma que el Resultado abre sin error, con capital `2,500,000.00`
   (2,000,000 honorarios + 500,000 costas).

Expected: sin crash, capital coincide, dos filas visibles en la tabla de resultado (una por cada
evento de capital: honorarios y costas).

- [ ] **Step 4: Smoke test manual — rechazo por tope de cuota litis**

Repite el paso 1-3 de arriba para un tercer expediente, pero con % Cuota litis = `35.00` (excede el
30% individual). Clic en "Liquidar".

Expected: aparece un mensaje de error en vez de un resultado de liquidación; el programa no crashea.

- [ ] **Step 5: Actualizar `README.md`**

En `README.md`, la sección "Estado actual" (líneas 12-26) hoy es:

```markdown
## Estado actual (2026-07-15)

✅ **Funcional hoy:** captura manual de expedientes y liquidación real de las áreas **Civil / Familia**
(interés del Art. 1617 del Código Civil, 6% anual, sobre obligaciones puntuales y recurrentes, con
abonos) y **Comercial** (Art. 884 C.Co., tasas remuneratoria y moratoria pactadas por obligación con
split real antes/después del vencimiento, validación de tope de usura 1.5×IBC).

🚧 **En desarrollo:** las áreas Laboral, Sancionatorio y Honorarios están registradas en el sistema pero
todavía no calculan (el programa avisa "Área no implementada" si se intentan usar). Indexación por IPC,
exportación a PDF/Word, prescripción/caducidad, anatocismo comercial condicionado (Art. 886 C.Co.) y
varios módulos más también están pendientes. Las series históricas de SMLMV, IPC e IBC/Tasa de Usura
(1984-2026, 1967-2025 y 1997-2026 respectivamente) ya están cargadas en
`app/engine/indexation/historical_index.py`, aunque todavía no están conectadas a ningún cálculo — esa
conexión es trabajo de otros sprints. El plan completo, sprint por sprint, está en
**[Pendientes.md](Pendientes.md)**.
```

Reemplázalo por:

```markdown
## Estado actual (2026-07-17)

✅ **Funcional hoy:** captura manual de expedientes y liquidación real de las áreas **Civil / Familia**
(interés del Art. 1617 del Código Civil, 6% anual, sobre obligaciones puntuales y recurrentes, con
abonos), **Comercial** (Art. 884 C.Co., tasas remuneratoria y moratoria pactadas por obligación con
split real antes/después del vencimiento, validación de tope de usura 1.5×IBC), **Sancionatorio**
(multas convertidas de SMLMV a pesos según la fecha del hecho, solo para hechos anteriores a
2020-01-01 — ver limitación de UVT abajo) y **Honorarios / Litigio** (tarifa fija + cuota litis,
validada contra dos topes legales simultáneos —30% la cuota litis sola, 50% la suma total—, con costas
judiciales opcionales como porcentaje manual).

🚧 **En desarrollo:** el área Laboral está registrada en el sistema pero todavía no calcula (el programa
avisa "Área no implementada" si se intenta usar). Indexación por IPC, exportación a PDF/Word,
prescripción/caducidad, anatocismo comercial condicionado (Art. 886 C.Co.) y varios módulos más también
están pendientes. La conversión Sancionatorio SMLMV→UVT solo cubre hechos anteriores a 2020-01-01: no
existe todavía una tabla histórica de UVT (el PDF de requisitos no la trae completa), así que un hecho
posterior a esa fecha lanza un error explícito en vez de calcular con un valor inventado. Las series
históricas de SMLMV, IPC e IBC/Tasa de Usura (1984-2026, 1967-2025 y 1997-2026 respectivamente) ya
están cargadas en `app/engine/indexation/historical_index.py`. El plan completo, sprint por sprint,
está en **[Pendientes.md](Pendientes.md)**.
```

- [ ] **Step 6: Actualizar `docs/GUIA_USUARIO.md` — encabezado y sección 1**

La nota de encabezado (línea 8) hoy dice:

```markdown
> **Última actualización:** 2026-07-15 — refleja el estado de Civil/Familia y Comercial. Cada vez que se
```

Cámbiala a:

```markdown
> **Última actualización:** 2026-07-17 — refleja el estado de Civil/Familia, Comercial, Sancionatorio y
> Honorarios/Litigio. Cada vez que se
```

En la sección 1 (líneas 36-40), el párrafo hoy dice:

```markdown
Hoy en día, BASTIUM sabe calcular liquidaciones de las áreas **Civil y de Familia** (por ejemplo: cuotas
de alimentos, gastos médicos, deudas civiles con interés) y **Comercial** (pagarés, letras de cambio,
cheques y facturas, con tasa remuneratoria y moratoria). Otras áreas del derecho (Laboral, Sancionatorio,
Honorarios) están planeadas pero **todavía no calculan** — más detalle en la
[sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy).
```

Reemplázalo por:

```markdown
Hoy en día, BASTIUM sabe calcular liquidaciones de las áreas **Civil y de Familia** (por ejemplo: cuotas
de alimentos, gastos médicos, deudas civiles con interés), **Comercial** (pagarés, letras de cambio,
cheques y facturas, con tasa remuneratoria y moratoria), **Sancionatorio** (multas administrativas
expresadas en SMLMV o UVT) y **Honorarios / Litigio** (cobro de honorarios profesionales, cuota litis y
costas judiciales). El área Laboral está planeada pero **todavía no calcula** — más detalle en la
[sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy).
```

- [ ] **Step 7: Agregar secciones 5.8 y 5.9 en `docs/GUIA_USUARIO.md`**

Inserta lo siguiente justo después de la sección 5.7 (que termina en la línea 274, justo antes del
separador `---` de la línea 276):

```markdown
### 5.8. Agregar una obligación sancionatoria

Cuando el expediente tiene **Área del derecho = Sancionatorio**, el formulario de "Agregar obligación"
oculta el campo "Valor" (no aplica aquí) y muestra en su lugar:

1. Dentro del Detalle de un expediente Sancionatorio, haz clic en **"Agregar obligación"**.
2. Llena Tipo (siempre **Puntual** — una multa es un hecho único, no admite Recurrente), Categoría
   (única opción: "Multa sancionatoria"), Concepto, Tasa efectiva anual (déjala en `0.00` si no quieres
   que la multa impaga genere intereses moratorios) y Fecha de origen (la fecha exacta del hecho
   sancionable).
3. **Cantidad SMLMV/UVT**: cuántos salarios mínimos (o UVT) vale la multa, según la resolución o acto
   administrativo (ej. `2` para una multa de 2 SMLMV).
4. Haz clic en **"Guardar"**.

El programa convierte automáticamente esa cantidad a pesos al liquidar, usando el SMLMV vigente en el
año de la **fecha de origen** — pero **solo si esa fecha es anterior al 1 de enero de 2020**. Para
hechos posteriores, la ley exige usar la UVT (Unidad de Valor Tributario) en vez del SMLMV, y esa tabla
histórica todavía no está cargada en el programa (no hay una fuente completa disponible) — el programa
muestra el mensaje "UVT no disponible" en vez de inventar un valor.

### 5.9. Agregar una obligación de honorarios / litigio

Cuando el expediente tiene **Área del derecho = Honorarios / Litigio**, el formulario oculta "Valor" y
"Cantidad SMLMV/UVT", y muestra:

1. Dentro del Detalle de un expediente de Honorarios, haz clic en **"Agregar obligación"**.
2. Llena Tipo (siempre **Puntual**), Categoría (única opción: "Honorarios profesionales"), Concepto,
   Tasa efectiva anual (para intereses moratorios si el cliente no paga a tiempo) y Fecha de origen.
3. **Honorarios fijos pactados**: la tarifa fija o retainer acordado, en pesos.
4. **% Cuota litis pactada**: el porcentaje del resultado económico del litigio que se pactó como
   honorario de éxito.
5. **Beneficio obtenido por el cliente**: el monto que el cliente efectivamente ganó en el proceso —
   es la base sobre la que se calculan tanto la cuota litis como las costas.
6. **% Costas judiciales (opcional)**: dejar en blanco si no aplica. Si el juez fijó un porcentaje de
   costas/agencias en derecho en el auto correspondiente, ingrésalo aquí — el programa no trae una
   tabla de rangos precargada (no existe una fuente estructurada confiable todavía), así que este
   porcentaje siempre lo digita quien liquida.
7. Haz clic en **"Guardar"**.

Al liquidar, el programa valida automáticamente que la cuota litis no exceda el 30% del beneficio
obtenido, **y** que la suma de honorarios fijos + cuota litis no exceda el 50% del mismo beneficio
(ambos límites aplican a la vez). Si cualquiera de los dos se excede, el programa muestra un mensaje de
error en vez de liquidar. Si ingresaste un porcentaje de costas, el resultado incluye un segundo rubro
separado de "Costas procesales".
```

- [ ] **Step 8: Actualizar la tabla de la sección 6 en `docs/GUIA_USUARIO.md`**

Las líneas 283-289 hoy son:

```markdown
Al crear un expediente, el campo "Área del derecho" muestra 5 opciones, pero **solo dos calculan de
verdad hoy**:

| Área | ¿Funciona? |
|---|---|
| Civil / Familia | ✅ Sí — interés del Art. 1617 C.C. (6% anual o la tasa que se pacte), sobre obligaciones puntuales y recurrentes, con abonos. |
| Comercial | ✅ Sí — Art. 884 C.Co., tasa remuneratoria antes del vencimiento y tasa moratoria después, validación de tope de usura (1.5× el IBC que ingreses). Ver [sección 5.7](#57-agregar-una-obligación-comercial). |
| Laboral | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 3. |
| Sancionatorio | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 4. |
| Honorarios / Litigio | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 4. |
```

Reemplázalas por:

```markdown
Al crear un expediente, el campo "Área del derecho" muestra 5 opciones, pero **una todavía no calcula
de verdad**:

| Área | ¿Funciona? |
|---|---|
| Civil / Familia | ✅ Sí — interés del Art. 1617 C.C. (6% anual o la tasa que se pacte), sobre obligaciones puntuales y recurrentes, con abonos. |
| Comercial | ✅ Sí — Art. 884 C.Co., tasa remuneratoria antes del vencimiento y tasa moratoria después, validación de tope de usura (1.5× el IBC que ingreses). Ver [sección 5.7](#57-agregar-una-obligación-comercial). |
| Sancionatorio | ✅ Sí, con una limitación conocida — convierte multas de SMLMV a pesos solo para hechos anteriores a 2020-01-01 (falta la tabla histórica de UVT para hechos posteriores). Ver [sección 5.8](#58-agregar-una-obligación-sancionatoria). |
| Honorarios / Litigio | ✅ Sí — tarifa fija + cuota litis con validación de topes legales (30% individual, 50% total), costas judiciales como porcentaje manual. Ver [sección 5.9](#59-agregar-una-obligación-de-honorarios--litigio). |
| Laboral | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 3. |
```

- [ ] **Step 9: Agregar subsecciones en la sección 7 (valores legales) de `docs/GUIA_USUARIO.md`**

Después de la sección "7.4. Dónde queda guardada toda la información capturada" (línea 342-346, justo
antes del separador `---` de la línea 348), agrega:

```markdown
### 7.5. Conversión SMLMV→UVT para multas sancionatorias

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente
  Sancionatorio, el campo **"Cantidad SMLMV/UVT (Sancionatorio)"**.
- **Dónde vive la lógica en el código**: `app/engine/indexation/smlmv_to_uvt.py`, función
  `resolver_base_sancion`. Se invoca automáticamente al liquidar
  (`SancionatorioStrategy.liquidar()` en `app/services/area_strategy.py`).
- **Qué pasa con hechos posteriores a 2020-01-01**: el programa lanza el error "UVT no disponible" y
  no calcula nada — no existe todavía una tabla histórica completa de UVT por año (ver
  `Pendientes.md`, Sprint 5).

### 7.6. Tope de cuota litis y honorarios (30% / 50% del beneficio obtenido)

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente de
  Honorarios, los campos **"Honorarios fijos pactados"**, **"% Cuota litis pactada"** y
  **"Beneficio obtenido por el cliente"** — los porcentajes tope (30% y 50%) no son editables desde la
  app, son un límite legal fijo.
- **Dónde vive la lógica en el código**: `app/services/area_strategy.py`, clase `HonorariosStrategy`,
  constantes `TOPE_CUOTA_LITIS_INDIVIDUAL_PCT` (30) y `TOPE_HONORARIOS_TOTAL_PCT` (50).
- **Qué pasa si se excede cualquiera de los dos topes**: el programa lanza el error "Cuota litis
  excede el tope" y no calcula nada.
```

- [ ] **Step 10: Actualizar la sección 8 (pendientes) de `docs/GUIA_USUARIO.md`**

La línea 356-357 hoy es:

```markdown
- 🚧 **Cálculo en las áreas Laboral, Sancionatorio y Honorarios** — hoy funcionan Civil/Familia y
  Comercial (`Pendientes.md`, Sprints 3 y 4).
```

Reemplázala por:

```markdown
- 🚧 **Cálculo en el área Laboral** — hoy funcionan Civil/Familia, Comercial, Sancionatorio y
  Honorarios (`Pendientes.md`, Sprint 3).
- 🚧 **Tabla histórica de UVT** — sin ella, el área Sancionatorio solo puede convertir multas para
  hechos anteriores a 2020-01-01 (`Pendientes.md`, Sprint 5, sección UVT).
```

- [ ] **Step 11: Actualizar la FAQ de `docs/GUIA_USUARIO.md`**

Las líneas 388-390 hoy son:

```markdown
**"Seleccioné Laboral/Sancionatorio/Honorarios y no me deja."**
Es esperado — esas áreas todavía no calculan, por eso aparecen deshabilitadas en el formulario. Comercial
sí está habilitada. Ver [sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy).
```

Reemplázalas por:

```markdown
**"Seleccioné Laboral y no me deja."**
Es esperado — esa área todavía no calcula, por eso aparece deshabilitada en el formulario. Civil/Familia,
Comercial, Sancionatorio y Honorarios sí están habilitadas. Ver
[sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy).

**"Cargué una multa sancionatoria de 2021 y me sale 'UVT no disponible'."**
Es esperado — el programa solo convierte SMLMV a pesos para hechos anteriores al 1 de enero de 2020. No
existe todavía una tabla histórica de UVT por año (planeado en `Pendientes.md`, Sprint 5). Si necesitas
liquidar un hecho posterior a esa fecha, contacta a quien mantiene el programa para priorizar esa tabla.
```

- [ ] **Step 12: Agregar el estado de cierre en `Pendientes.md`**

Al final de la sección "Sprint 4 — Área Sancionatorio y Honorarios" (después de la "Definición de
Hecho" actual, antes del separador `---` que abre la sección del Sprint 5), agrega:

```markdown
**Estado:** Implementado (2026-07-17) — ver `docs/superpowers/plans/2026-07-17-sprint4-sancionatorio-honorarios.md`
y `docs/superpowers/specs/2026-07-17-sprint4-sancionatorio-honorarios-design.md`. Decisiones tomadas con
el usuario: tope de cuota litis aplica ambos límites simultáneamente (30% individual, 50% total, no son
excluyentes); costas judiciales se ingresan como porcentaje manual (no hay tabla estructurada del
Acuerdo PCSJA20-11556 disponible); UVT sigue sin tabla histórica (Sprint 5), así que la conversión
SMLMV→UVT solo cubre hechos anteriores a 2020-01-01 — hechos posteriores lanzan `UVTNoDisponibleError`
en vez de inventar un valor.
```

- [ ] **Step 13: Commit final**

```bash
git add README.md docs/GUIA_USUARIO.md Pendientes.md
git commit -m "docs: document Sancionatorio and Honorarios areas in README, Guia de Usuario, and Pendientes.md"
```

---

## Post-plan reminder

Este plan no implementa:
- Conversión SMLMV→UVT para hechos posteriores a 2020-01-01 (bloqueado hasta que exista una fuente real
  de UVT histórica — ver `Pendientes.md`, Sprint 5).
- Tabla estructurada de rangos de costas del Acuerdo PCSJA20-11556 (se usa un porcentaje manual en su
  lugar, a propósito).
- Obligaciones `RECURRENTE` en Sancionatorio/Honorarios (ambas áreas modelan hechos puntuales por
  diseño — una multa o un cobro de honorarios no son flujos recurrentes en este modelo).

Estas son decisiones de alcance acordadas con el usuario durante el brainstorming, no omisiones.
