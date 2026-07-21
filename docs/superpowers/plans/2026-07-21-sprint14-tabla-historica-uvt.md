# Sprint 14 — Tabla histórica de UVT (DIAN) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load a verified UVT (Unidad de Valor Tributario) historical series 2006-2026 into the versioned
parameters system, and unblock `resolver_base_sancion` so sanction facts on/after 2020-01-01 convert to
pesos via UVT instead of raising `UVTNoDisponibleError` unconditionally.

**Architecture:** Mirrors the existing SMLMV pattern exactly — a frozen `Dict[int, Decimal]` in
`historical_index.py`, a `get_uvt_for_year(anio)` reader with the same contract as `get_smlmv_for_year`,
an `ANUAL_EXACTO` catalog entry in `parametro_service.py`, and idempotent seeding in
`migrate_parametros_legales.py`. No new abstractions — `SMMLVCalculator.to_pesos` (already a generic
quantity×unit-value converter) is reused for the UVT conversion, no new calculator class.

**Tech Stack:** Python, SQLAlchemy, pytest, SQLite (in-memory for tests).

**Design spec:** `docs/superpowers/specs/2026-07-21-tabla-historica-uvt-design.md` (verified UVT table,
sources, and the decisions made with the user — read it before starting).

---

### Task 1: UVT series, catalog entry, seeding, and `get_uvt_for_year`

**Files:**
- Modify: `app/services/parametro_service.py:100-108` (add catalog entry)
- Modify: `app/engine/indexation/historical_index.py` (append new section at end, after line 575)
- Modify: `scripts/migrate_parametros_legales.py:45-49` (import) and `:132-141` (seeding block)
- Test: `tests/engine/test_historical_index.py`

- [ ] **Step 1: Write the failing tests**

Add `get_uvt_for_year` to the existing import block at the top of
`tests/engine/test_historical_index.py` (lines 10-17):

```python
from app.engine.indexation.historical_index import (
    _IPC_VARIACION_ANUAL,
    _TRAMOS_IBC_USURA,
    get_ibc_usura_for_date,
    get_ipc_for_date,
    get_smlmv_for_year,
    get_tramos_ibc_usura_between,
    get_uvt_for_year,
)
```

Then add these tests, right after `test_smlmv_2010_valor_conocido_interior_del_rango` (after line 47):

```python
def test_uvt_2006_primer_anio_disponible():
    # Ley 1111 de 2006 crea la UVT; primer valor fijado ($20.000).
    assert get_uvt_for_year(2006) == Decimal("20000.00")


def test_uvt_2026_valor_conocido():
    assert get_uvt_for_year(2026) == Decimal("52374.00")


def test_uvt_2021_valor_conocido_interior_del_rango():
    # Chequeo puntual en la mitad de la serie, no solo en los extremos.
    assert get_uvt_for_year(2021) == Decimal("36308.00")


def test_uvt_fuera_de_rango_lanza_value_error():
    with pytest.raises(ValueError):
        get_uvt_for_year(2027)
    with pytest.raises(ValueError):
        get_uvt_for_year(2005)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/engine/test_historical_index.py -v -k uvt`
Expected: FAIL/ERROR — `ImportError: cannot import name 'get_uvt_for_year'`

- [ ] **Step 3: Add the catalog entry**

In `app/services/parametro_service.py`, add to `CATALOGO_PARAMETROS` (right after the
`"USURA_CONSUMO_ORDINARIO"` entry, before the dict's closing `}` at line 108):

```python
    "UVT": InfoParametro(
        "Unidad de Valor Tributario (UVT)", "Indicadores historicos",
        "DIAN, resolución anual (Ley 1111 de 2006)", ModoResolucion.ANUAL_EXACTO,
    ),
```

- [ ] **Step 4: Add the series and `get_uvt_for_year`**

Append this new section at the end of `app/engine/indexation/historical_index.py` (after the
`get_tramos_ibc_usura_between` function, i.e. after line 575):

```python


# ---------------------------------------------------------------------------
# UVT (Unidad de Valor Tributario), 2006-2026.
# El PDF de requisitos NO trae una tabla completa para esta serie (a diferencia
# de SMLMV/IPC/IBC-Usura) -- solo describe el mecanismo (paginas 8, 21, 38, 53)
# y cita un valor aislado (pagina 69, "UVT 2023 ~ $38.004") que en realidad
# corresponde al valor oficial de 2022, no 2023. Serie verificada cruzando 3
# fuentes externas independientes -- ver
# docs/superpowers/specs/2026-07-21-tabla-historica-uvt-design.md para la
# tabla completa con resolucion DIAN por año y las URLs consultadas.
# ---------------------------------------------------------------------------

_UVT_POR_ANIO: Dict[int, Decimal] = {
    2006: Decimal("20000.00"),
    2007: Decimal("20974.00"),
    2008: Decimal("22054.00"),
    2009: Decimal("23763.00"),
    2010: Decimal("24555.00"),
    2011: Decimal("25132.00"),
    2012: Decimal("26049.00"),
    2013: Decimal("26841.00"),
    2014: Decimal("27485.00"),
    2015: Decimal("28279.00"),
    2016: Decimal("29753.00"),
    2017: Decimal("31859.00"),
    2018: Decimal("33156.00"),
    2019: Decimal("34270.00"),
    2020: Decimal("35607.00"),
    2021: Decimal("36308.00"),
    2022: Decimal("38004.00"),
    2023: Decimal("42412.00"),
    2024: Decimal("47065.00"),
    2025: Decimal("49799.00"),
    2026: Decimal("52374.00"),
}


def get_uvt_for_year(anio: int) -> Decimal:
    """Retorna la Unidad de Valor Tributario (UVT) vigente para el año dado,
    consultando la tabla parametros_legales (clave UVT, editable desde la
    GUI). _UVT_POR_ANIO sigue siendo la referencia congelada de origen (ver
    scripts/migrate_parametros_legales.py)."""
    try:
        return get_parametro("UVT", date(anio, 1, 1))
    except ParametroNoDisponibleError as error:
        raise ValueError(
            f"No hay UVT configurada para el año {anio}. "
            f"Datos disponibles: {min(_UVT_POR_ANIO)}-{max(_UVT_POR_ANIO)}."
        ) from error
```

- [ ] **Step 5: Wire up seeding in the migration script**

In `scripts/migrate_parametros_legales.py`, add `_UVT_POR_ANIO` to the import block (lines 45-49):

```python
from app.engine.indexation.historical_index import (
    _IPC_INDICE_ACUMULADO,
    _SMLMV_POR_ANIO,
    _TRAMOS_IBC_USURA,
    _UVT_POR_ANIO,
)
```

Then add this seeding block right after the `USURA_CONSUMO_ORDINARIO` block (after line 140, still
before `session.commit()`):

```python

        if not _clave_ya_sembrada(session, "UVT"):
            for anio, valor in _UVT_POR_ANIO.items():
                session.add(_fila("UVT", valor, date(anio, 1, 1)))
            sembradas += 1
```

- [ ] **Step 6: Update the module docstring in the migration script**

In `scripts/migrate_parametros_legales.py`, line 16, change:
```python
las 3 series historicas de historical_index.py (SMLMV, IPC, IBC/usura).
```
to:
```python
las 4 series historicas de historical_index.py (SMLMV, IPC, IBC/usura, UVT).
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/engine/test_historical_index.py -v`
Expected: PASS (all tests in the file, including the 4 new `uvt` ones — the fixture in this file calls
`migrar()` from `scripts.migrate_parametros_legales`, so the seeding block from Step 5 is required for
these tests to pass, not just the function itself).

- [ ] **Step 8: Commit**

```bash
git add app/services/parametro_service.py app/engine/indexation/historical_index.py scripts/migrate_parametros_legales.py tests/engine/test_historical_index.py
git commit -m "$(cat <<'EOF'
feat: add historical UVT series (2006-2026) and get_uvt_for_year

Verified against 3 independent sources since the requirements PDF has
no complete UVT table (see design spec). Seeded via the existing
parametros_legales migration, same ANUAL_EXACTO pattern as SMLMV/IPC.
EOF
)"
```

---

### Task 2: Unblock `resolver_base_sancion` for post-2020 facts

**Files:**
- Modify: `app/engine/indexation/smlmv_to_uvt.py` (full rewrite, currently 29 lines)
- Test: `tests/engine/test_smlmv_to_uvt.py` (fixture + 2 existing tests must change, not just add)
- Test: `tests/services/test_area_strategy.py:27-87` (fixture), `:557-563` (existing test must change)

- [ ] **Step 1: Update the fixture and rewrite the obsolete tests in `test_smlmv_to_uvt.py`**

Replace the entire contents of `tests/engine/test_smlmv_to_uvt.py` with:

```python
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.exceptions import UVTNoDisponibleError
from app.engine.indexation.historical_index import _UVT_POR_ANIO
from app.engine.indexation.smlmv_to_uvt import resolver_base_sancion
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _db_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="SMLMV", valor=Decimal("828116.00"), vigente_desde=date(2019, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
    ))
    for anio, valor in _UVT_POR_ANIO.items():
        session.add(ParametroLegal(
            clave="UVT", valor=valor, vigente_desde=date(anio, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
        ))
    session.commit()
    session.close()


def test_hecho_pre_2020_usa_smlmv_del_anio_del_hecho():
    # SMLMV 2019 = 828116.00 (ver historical_index.py, verificado contra el PDF pag. 55-57).
    resultado = resolver_base_sancion(date(2019, 6, 1), Decimal("2"))
    assert resultado == Decimal("1656232.00")


def test_hecho_dia_anterior_al_corte_2020_usa_smlmv_2019():
    resultado = resolver_base_sancion(date(2019, 12, 31), Decimal("1"))
    assert resultado == Decimal("828116.00")


def test_hecho_exactamente_2020_01_01_usa_uvt_2020():
    # UVT 2020 = 35607.00 (ver historical_index.py, verificado contra 3 fuentes externas).
    resultado = resolver_base_sancion(date(2020, 1, 1), Decimal("1"))
    assert resultado == Decimal("35607.00")


def test_hecho_posterior_a_2020_usa_uvt_del_anio_del_hecho():
    # UVT 2021 = 36308.00; 2 UVT = 72616.00.
    resultado = resolver_base_sancion(date(2021, 1, 1), Decimal("2"))
    assert resultado == Decimal("72616.00")


def test_hecho_con_anio_uvt_aun_no_publicada_lanza_uvt_no_disponible_error():
    # La serie llega hasta 2026 (ultimo año con resolucion DIAN publicada al
    # momento de este sprint) -- 2027 todavia no existe, sigue lanzando el
    # error de siempre en vez de adivinar.
    with pytest.raises(UVTNoDisponibleError):
        resolver_base_sancion(date(2027, 1, 1), Decimal("1"))
```

- [ ] **Step 2: Update the fixture and the obsolete test in `test_area_strategy.py`**

In `tests/services/test_area_strategy.py`, add `_UVT_POR_ANIO` to the import block (lines 10-14):

```python
from app.engine.indexation.historical_index import (
    _IPC_INDICE_ACUMULADO,
    _SMLMV_POR_ANIO,
    _TRAMOS_IBC_USURA,
    _UVT_POR_ANIO,
)
```

Add this loop to the `_parametros_legales_en_memoria` fixture, right after the `SMLMV` loop (after
line 71, before the `_IPC_INDICE_ACUMULADO` loop — order doesn't matter, just keep it grouped with the
other annual series):

```python
    for anio, valor in _UVT_POR_ANIO.items():
        session.add(ParametroLegal(
            clave="UVT", valor=valor, vigente_desde=_date(anio, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
```

Replace `test_liquida_multa_posterior_a_2020_lanza_uvt_no_disponible_error` (lines 557-563) with:

```python
    def test_liquida_multa_posterior_a_2020_convirtiendo_uvt_a_pesos(self):
        obligacion = _obligacion_sancionatoria(fecha_origen=date(2021, 1, 1))

        resultado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        # UVT 2021 = 36308.00; cantidad_smlmv_uvt por defecto en el factory es 2.
        assert resultado.final_balance().principal == Decimal("72616.00")
```

- [ ] **Step 3: Run tests to verify the new/changed ones fail**

Run: `.venv\Scripts\python.exe -m pytest tests/engine/test_smlmv_to_uvt.py tests/services/test_area_strategy.py -v -k "2020 or 2021 or uvt or Uvt"`
Expected: FAIL — `resolver_base_sancion` still raises `UVTNoDisponibleError` unconditionally for
`fecha_hecho >= 2020-01-01`, so the tests expecting a peso amount fail.

- [ ] **Step 4: Rewrite `resolver_base_sancion`**

Replace the entire contents of `app/engine/indexation/smlmv_to_uvt.py` with:

```python
from datetime import date
from decimal import Decimal

from app.core.exceptions import UVTNoDisponibleError
from app.engine.indexation.historical_index import get_smlmv_for_year, get_uvt_for_year
from app.engine.indexation.smmlv import SMMLVCalculator

FECHA_CORTE_SMLMV_A_UVT = date(2020, 1, 1)


def resolver_base_sancion(fecha_hecho: date, cantidad: Decimal) -> Decimal:
    """
    Convierte una cantidad de SMLMV o UVT a pesos, segun la fecha del hecho sancionatorio
    (Ley 1955 de 2019, art. 49): antes del 2020-01-01 la base es el SMLMV del año del
    hecho; desde esa fecha, la base es la UVT vigente de la DIAN (tabla historica
    2006-2026, ver docs/superpowers/specs/2026-07-21-tabla-historica-uvt-design.md).
    """
    if fecha_hecho < FECHA_CORTE_SMLMV_A_UVT:
        smlmv_del_anio = get_smlmv_for_year(fecha_hecho.year)
        return SMMLVCalculator.to_pesos(cantidad, smlmv_del_anio)

    try:
        uvt_del_anio = get_uvt_for_year(fecha_hecho.year)
    except ValueError as error:
        raise UVTNoDisponibleError(
            f"No hay UVT publicada por la DIAN para calcular el hecho sancionatorio "
            f"del {fecha_hecho}. {error}"
        ) from error

    return SMMLVCalculator.to_pesos(cantidad, uvt_del_anio)
```

- [ ] **Step 5: Run tests to verify they all pass**

Run: `.venv\Scripts\python.exe -m pytest tests/engine/test_smlmv_to_uvt.py tests/services/test_area_strategy.py -v`
Expected: PASS — all tests, including the ones that pre-existed for other areas in
`test_area_strategy.py` (make sure nothing else in that file broke).

- [ ] **Step 6: Commit**

```bash
git add app/engine/indexation/smlmv_to_uvt.py tests/engine/test_smlmv_to_uvt.py tests/services/test_area_strategy.py
git commit -m "$(cat <<'EOF'
feat: unblock resolver_base_sancion for facts on/after 2020-01-01

Converts via the UVT of the fact's year instead of raising
UVTNoDisponibleError unconditionally. Reuses SMMLVCalculator.to_pesos
(quantity x unit value, rounded) -- no UVT-specific calculator needed.
Updates the 2 existing tests whose old assertions (error expected)
were made obsolete by this change.
EOF
)"
```

---

### Task 3: Documentation — `README.md` and `docs/GUIA_USUARIO.md`

**Files:**
- Modify: `README.md:12, 19-22, 52-57`
- Modify: `docs/GUIA_USUARIO.md` (7 spots — see below)

No tests in this task (documentation only). Verify by re-reading each changed section after editing.

- [ ] **Step 1: `README.md` — status date**

Change line 12 from:
```markdown
## Estado actual (2026-07-20)
```
to:
```markdown
## Estado actual (2026-07-21)
```

- [ ] **Step 2: `README.md` — Sancionatorio description (lines 19-22)**

Change:
```markdown
(multas SIC/Penal/Ambiental/Urbano en SMLMV o UVT, Ley 1955/2019 art. 49 — solo cubre hechos anteriores
a 2020-01-01, porque todavía no hay tabla histórica de UVT cargada; hechos posteriores avisan "UVT no
disponible" en vez de arriesgar un valor incorrecto), **Honorarios / Litigio**
```
to:
```markdown
(multas SIC/Penal/Ambiental/Urbano en SMLMV o UVT, Ley 1955/2019 art. 49, con la base convertida a pesos
según la fecha del hecho: SMLMV antes del 2020-01-01, UVT desde esa fecha, con tabla histórica de UVT
2006-2026 cargada), **Honorarios / Litigio**
```

- [ ] **Step 3: `README.md` — historical series paragraph (lines 52-57)**

Change:
```markdown
series históricas de SMLMV, IPC e IBC/Tasa de Usura (1984-2026, 1967-2025 y 1997-2026 respectivamente)
ya están cargadas en `app/engine/indexation/historical_index.py` — IBC/Usura se usa en Comercial y en la
fase 2 de la indemnización moratoria laboral, e IPC ya está conectado a la indexación de Civil/Familia
(Sprint 8); SMLMV sigue sin un consumidor propio. La tabla histórica de UVT es un caso aparte: ni
siquiera está cargada todavía. El plan completo, sprint por sprint, está en
**[Pendientes.md](Pendientes.md)**.
```
to:
```markdown
series históricas de SMLMV, IPC, IBC/Tasa de Usura y UVT (1984-2026, 1967-2025, 1997-2026 y 2006-2026
respectivamente) ya están cargadas en `app/engine/indexation/historical_index.py` — IBC/Usura se usa en
Comercial y en la fase 2 de la indemnización moratoria laboral, IPC ya está conectado a la indexación de
Civil/Familia (Sprint 8), y UVT ya está conectada a la conversión SMLMV→UVT del área Sancionatorio
(Sprint 14); SMLMV sigue sin un consumidor propio. El plan completo, sprint por sprint, está en
**[Pendientes.md](Pendientes.md)**.
```

- [ ] **Step 4: `GUIA_USUARIO.md` — section 5.9 (lines 358-362)**

Change:
```markdown
La conversión a pesos usa el SMLMV vigente en el año del hecho si la fecha de origen es **anterior al
2020-01-01**; para fechas posteriores necesitaría la tabla histórica de UVT, que todavía no está cargada
(ver [sección 7.5](#75-conversión-smlmvuvt-para-multas-sancionatorias)). Si intentas liquidar un hecho
posterior a esa fecha, el programa muestra el mensaje "UVT no disponible" en vez de arriesgar un valor
incorrecto.
```
to:
```markdown
La conversión a pesos usa el SMLMV vigente en el año del hecho si la fecha de origen es **anterior al
2020-01-01**, y la UVT vigente en el año del hecho si es **igual o posterior** a esa fecha (tabla
histórica UVT 2006-2026, ver [sección 7.5](#75-conversión-smlmvuvt-para-multas-sancionatorias)). Si el
hecho es de un año para el que todavía no exista UVT publicada por la DIAN (por ejemplo, un año futuro
que la DIAN aún no ha fijado), el programa muestra el mensaje "UVT no disponible" en vez de arriesgar un
valor incorrecto.
```

- [ ] **Step 5: `GUIA_USUARIO.md` — section 6 table row (line 559)**

Change:
```markdown
| Sancionatorio | ✅ Sí, con una limitación — multas en SMLMV o UVT (Ley 1955/2019 art. 49), pero solo para hechos **anteriores al 2020-01-01**: todavía no hay tabla histórica de UVT cargada, y el programa se rehúsa a adivinar el valor para hechos posteriores ("UVT no disponible"). Ver [sección 5.9](#59-agregar-una-obligación-sancionatoria). |
```
to:
```markdown
| Sancionatorio | ✅ Sí — multas en SMLMV o UVT (Ley 1955/2019 art. 49): SMLMV para hechos anteriores al 2020-01-01, UVT (tabla histórica 2006-2026) desde esa fecha en adelante. Ver [sección 5.9](#59-agregar-una-obligación-sancionatoria). |
```

- [ ] **Step 6: `GUIA_USUARIO.md` — section 7.5 (lines 625-638)**

Change:
```markdown
### 7.5. Conversión SMLMV→UVT para multas sancionatorias

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente
  Sancionatorio, el campo **"Cantidad SMLMV/UVT (Sancionatorio)"** — ver
  [sección 5.9](#59-agregar-una-obligación-sancionatoria). No hay valores por defecto: cada multa trae su
  propia cantidad de salarios mínimos o UVT.
- **Dónde vive la lógica en el código**: `app/engine/indexation/smlmv_to_uvt.py`, función
  `resolver_base_sancion`. Se invoca automáticamente al liquidar (`SancionatorioStrategy.liquidar()` en
  `app/services/area_strategy.py`). Los valores de SMLMV por año están en
  `app/engine/indexation/historical_index.py`.
- **Qué pasa si el hecho es posterior al 2020-01-01**: la ley pasó de expresar estas multas en SMLMV a
  expresarlas en UVT a partir de esa fecha, y todavía no existe una tabla histórica de UVT cargada en el
  programa (ver `Pendientes.md`, Sprint 5). En vez de adivinar un valor, el programa lanza el error "UVT
  no disponible" y no calcula nada.
```
to:
```markdown
### 7.5. Conversión SMLMV→UVT para multas sancionatorias

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente
  Sancionatorio, el campo **"Cantidad SMLMV/UVT (Sancionatorio)"** — ver
  [sección 5.9](#59-agregar-una-obligación-sancionatoria). No hay valores por defecto: cada multa trae su
  propia cantidad de salarios mínimos o UVT.
- **Dónde vive la lógica en el código**: `app/engine/indexation/smlmv_to_uvt.py`, función
  `resolver_base_sancion`. Se invoca automáticamente al liquidar (`SancionatorioStrategy.liquidar()` en
  `app/services/area_strategy.py`). Los valores de SMLMV y de UVT por año están en
  `app/engine/indexation/historical_index.py` (funciones `get_smlmv_for_year` y `get_uvt_for_year`), y
  también se pueden consultar o corregir desde la pantalla "⚙ Parámetros" (claves `SMLMV` y `UVT`, ver
  [sección 5.13](#513-editar-tasas-y-topes-legales-pantalla--parámetros)).
- **Qué pasa si el hecho es posterior al 2020-01-01**: la ley pasó de expresar estas multas en SMLMV a
  expresarlas en UVT a partir de esa fecha; el programa ya tiene cargada la tabla histórica de UVT
  (2006-2026, ver `Pendientes.md`, Sprint 14) y convierte automáticamente. Solo lanza el error "UVT no
  disponible" si el hecho es de un año que la DIAN todavía no ha publicado (por ejemplo, un año futuro
  aún sin resolución) — en ese caso, en vez de adivinar un valor, no calcula nada.
```

- [ ] **Step 7: `GUIA_USUARIO.md` — section 5.13 warning box (lines 500-501 and 515-516)**

Change line 500-501:
```markdown
   - **Valor**: el número nuevo (ej. `1.5` para el multiplicador de usura, o `1300000` para un SMLMV).
   - **Vigente desde**: la fecha a partir de la cual rige este valor (para SMLMV o el índice IPC, lee la
     advertencia más abajo **antes** de guardar).
```
to:
```markdown
   - **Valor**: el número nuevo (ej. `1.5` para el multiplicador de usura, o `1300000` para un SMLMV).
   - **Vigente desde**: la fecha a partir de la cual rige este valor (para SMLMV, IPC o UVT, lee la
     advertencia más abajo **antes** de guardar).
```

Change lines 515-516:
```markdown
> Los dos parámetros de "Indicadores históricos" marcados como series **anuales** — el **SMLMV** y el
> **índice IPC acumulado** — solo quedan "vigentes" para un año si el campo **"Vigente desde" es
```
to:
```markdown
> Los tres parámetros de "Indicadores históricos" marcados como series **anuales** — el **SMLMV**, el
> **índice IPC acumulado** y la **UVT** — solo quedan "vigentes" para un año si el campo **"Vigente desde" es
```

- [ ] **Step 8: `GUIA_USUARIO.md` — section 8 bullet (lines 710-713)**

Change:
```markdown
- 🚧 **Tabla histórica de UVT** — el área Sancionatorio solo convierte a pesos los hechos anteriores al
  2020-01-01 (vía SMLMV); los hechos posteriores necesitan una tabla histórica de UVT que todavía no
  está cargada, y por ahora el programa avisa "UVT no disponible" en vez de calcular (`Pendientes.md`,
  Sprint 5).
```
to:
```markdown
- ✅ **Tabla histórica de UVT** (2006-2026) ya está cargada y conectada — el área Sancionatorio convierte
  a pesos tanto los hechos anteriores al 2020-01-01 (vía SMLMV) como los posteriores (vía UVT). Ver
  [sección 7.5](#75-conversión-smlmvuvt-para-multas-sancionatorias) (`Pendientes.md`, Sprint 14).
```

- [ ] **Step 9: `GUIA_USUARIO.md` — section 8, Derecho Tributario bullet (lines 731-737)**

Change:
```markdown
- 🚧 **Derecho Tributario** — dos motores de cálculo ya existen y están probados: interés moratorio
  tributario (E.T. art. 635, tasa de usura vigente menos dos puntos, resuelta automáticamente por tramos
  históricos) y depuración de Renta Líquida Gravable (el flujo de 8 pasos del impuesto de renta). Ninguno
  está conectado todavía a un área operable — no existe una estrategia de liquidación tributaria ni el
  área aparece en el selector de la GUI. Sanciones (extemporaneidad, inexactitud) e imputación tributaria
  de pagos siguen sin construir, bloqueadas por la falta de una tabla histórica de UVT (`Pendientes.md`,
  Sprint 11).
```
to:
```markdown
- 🚧 **Derecho Tributario** — dos motores de cálculo ya existen y están probados: interés moratorio
  tributario (E.T. art. 635, tasa de usura vigente menos dos puntos, resuelta automáticamente por tramos
  históricos) y depuración de Renta Líquida Gravable (el flujo de 8 pasos del impuesto de renta). Ninguno
  está conectado todavía a un área operable — no existe una estrategia de liquidación tributaria ni el
  área aparece en el selector de la GUI. Sanciones (extemporaneidad, inexactitud) e imputación tributaria
  de pagos siguen sin construir; la tabla histórica de UVT que las bloqueaba ya está disponible
  (`Pendientes.md`, Sprint 14), quedan pendientes del Sprint 15 (Tributario 11b).
```

- [ ] **Step 10: `GUIA_USUARIO.md` — FAQ section 9 (lines 761-765)**

Change:
```markdown
**"Al liquidar un expediente Sancionatorio me sale 'UVT no disponible'."**
Es esperado si la "Fecha de origen" de la multa es **posterior al 2020-01-01**: desde esa fecha, la ley
expresa estas multas en UVT en vez de SMLMV, y todavía no hay una tabla histórica de UVT cargada en el
programa (ver [sección 7.5](#75-conversión-smlmvuvt-para-multas-sancionatorias) y `Pendientes.md`,
Sprint 5). Por ahora, esta área solo liquida hechos anteriores a esa fecha.
```
to:
```markdown
**"Al liquidar un expediente Sancionatorio me sale 'UVT no disponible'."**
Desde el Sprint 14, esto solo ocurre si la "Fecha de origen" de la multa cae en un año para el que la
DIAN todavía no ha publicado la UVT (por ejemplo, un año futuro sin resolución vigente) — la tabla
histórica cubre 2006-2026. Revisa la fecha de origen, o agrega el valor de UVT del año faltante desde la
pantalla "⚙ Parámetros" en cuanto la DIAN lo publique (ver
[sección 7.5](#75-conversión-smlmvuvt-para-multas-sancionatorias)).
```

- [ ] **Step 11: Commit**

```bash
git add README.md docs/GUIA_USUARIO.md
git commit -m "docs: document Sprint 14 UVT unblock in README and GUIA_USUARIO"
```

---

### Task 4: Full suite verification

**Files:** none (verification only)

- [ ] **Step 1: Run the complete test suite**

Run: `.venv\Scripts\python.exe -m pytest -q`
Expected: all tests pass (`N passed`), 0 failed. Compare `N` against the last known count
(367 passed, 1 skipped per the Sprint 13 closeout note in `Pendientes.md`) — it should now be higher by
the number of tests added in Tasks 1 and 2 (4 new in `test_historical_index.py`, 1 new in
`test_smlmv_to_uvt.py`), with the same 2 modified tests still counted once each.

- [ ] **Step 2: Update `Pendientes.md` Sprint 14 entry**

Mark the Sprint 14 section as completed, following the same closeout style as Sprint 13 (see the text
right above "## Sprint 14" in `Pendientes.md` for the pattern: what was built, what was verified, suite
status). Keep it brief — a short paragraph, not a rewrite of the whole sprint section.

- [ ] **Step 3: Commit**

```bash
git add Pendientes.md
git commit -m "docs: mark Sprint 14 (tabla historica de UVT) completed"
```

---

## Self-Review Notes

- **Spec coverage:** series 2006-2026 (Task 1), `get_uvt_for_year` (Task 1), catalog entry (Task 1),
  migration seeding (Task 1), `resolver_base_sancion` unblock (Task 2), the 2 obsolete tests corrected
  rather than deleted (Task 2), README/GUIA_USUARIO updated (Task 3), full suite green (Task 4) — all
  Definición de Hecho items from the design spec are covered.
- **Scope:** intentionally excludes the Sprint 15 tax-penalty engine itself (out of scope per spec) and
  DIAN scraping automation (explicitly excluded per spec).
