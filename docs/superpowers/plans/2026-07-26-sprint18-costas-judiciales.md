# Sprint 18 — Costas judiciales (Acuerdo PSAA16-10554) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar el hueco documentado del Sprint 4 (`costas_pct_manual` como único mecanismo) con
cálculo automático de agencias en derecho basado en la tabla real y completa del Acuerdo PSAA16-10554
(2016) del Consejo Superior de la Judicatura, cableado en las cinco áreas de litigio judicial de BASTIUM.

**Architecture:** Un módulo de motor puro nuevo (`app/engine/costs/agencias_en_derecho.py`) transcribe la
tabla de tarifas como constantes Python y expone `calcular_agencias_en_derecho(...)`, que resuelve el tier
de cuantía (CGP art. 25), busca el rango aplicable, interpola linealmente dentro de él (ponderación
inversa) y aplica el tope de 20 SMLMV. Dos campos nuevos en `Obligacion` (`costas_tipo_proceso`,
`costas_instancia`) activan el cálculo automático por obligación; `costas_pct_manual` sigue existiendo como
override de mayor prioridad. Un helper compartido en `area_strategy.py` conecta ambos mecanismos a las
cinco estrategias de área que litigan en un proceso judicial (Civil/Familia, Comercial, Laboral,
Sancionatorio, Honorarios) — Tributario queda fuera.

**Tech Stack:** Python 3, SQLAlchemy/SQLite, pytest, `Decimal` para todo el dinero (nunca float).

**Spec de referencia:**
`docs/superpowers/specs/2026-07-26-sprint18-costas-judiciales-design.md` — leer antes de empezar. Este plan
refina dos detalles de esa spec que solo se volvieron visibles al transcribir la tabla completa (documentado
en la Nota de Task 1): (a) `CuantiaTier` termina siendo `{MINIMA, MENOR, MAYOR}` en vez de incluir
`SIN_CUANTIA` — el caso "sin pretensión pecuniaria" se resuelve con el parámetro booleano
`tiene_pretension_pecuniaria`, no con un cuarto valor de tier; (b) `TipoProceso` termina en 18 miembros, no
16 — dos categorías del acuerdo (liquidación de sociedad conyugal, insolvencia de persona natural) mezclan
dos resultados con tarifas numéricamente distintas bajo el mismo epígrafe del acuerdo, y cada uno necesita
su propio miembro de enum para no perder la distinción legal.

---

## Task 1: Módulo base + tabla de Procesos Declarativos en General

**Files:**
- Create: `app/engine/costs/__init__.py`
- Create: `app/engine/costs/agencias_en_derecho.py`
- Modify: `app/core/exceptions.py`
- Test: `tests/engine/costs/__init__.py`
- Test: `tests/engine/costs/test_agencias_en_derecho.py`

- [ ] **Step 1: Crear el paquete vacío**

```bash
mkdir -p app/engine/costs tests/engine/costs
touch app/engine/costs/__init__.py tests/engine/costs/__init__.py
```

- [ ] **Step 2: Agregar la excepción de dominio**

En `app/core/exceptions.py`, agregar al final del archivo:

```python
class TarifaNoDisponibleError(Exception):
    """Se lanza cuando no hay una tarifa de agencias en derecho registrada (Acuerdo
    PSAA16-10554) para la combinacion tipo_proceso/instancia/cuantia pedida -- nunca
    se inventa un rango."""
```

- [ ] **Step 3: Escribir el test de la tabla de datos (falla: el módulo no existe)**

Crear `tests/engine/costs/test_agencias_en_derecho.py`:

```python
from decimal import Decimal

from app.engine.costs.agencias_en_derecho import (
    CuantiaTier,
    Instancia,
    RangoTarifa,
    TipoProceso,
    TOPE_MAXIMO_SMLMV,
    UMBRAL_MENOR_CUANTIA_SMLMV,
    UMBRAL_MINIMA_CUANTIA_SMLMV,
    UnidadTarifa,
    TARIFAS_AGENCIAS_EN_DERECHO,
)


def test_umbrales_cgp_articulo_25():
    # Verificados contra Ley 1564 de 2012 art. 25 (ver spec, "Fuentes externas").
    assert UMBRAL_MINIMA_CUANTIA_SMLMV == Decimal("40")
    assert UMBRAL_MENOR_CUANTIA_SMLMV == Decimal("150")


def test_tope_maximo_paragrafo_3_articulo_3():
    assert TOPE_MAXIMO_SMLMV == Decimal("20")


def test_declarativo_general_unica_instancia_pecuniaria():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DECLARATIVO_GENERAL, Instancia.UNICA, CuantiaTier.MINIMA, True)
    ]
    assert rango == RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE)


def test_declarativo_general_unica_instancia_no_pecuniaria():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DECLARATIVO_GENERAL, Instancia.UNICA, None, False)
    ]
    assert rango == RangoTarifa(Decimal("1"), Decimal("8"), UnidadTarifa.SMLMV)


def test_declarativo_general_primera_instancia_menor_cuantia():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, CuantiaTier.MENOR, True)
    ]
    assert rango == RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE)


def test_declarativo_general_primera_instancia_mayor_cuantia():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, CuantiaTier.MAYOR, True)
    ]
    assert rango == RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE)


def test_declarativo_general_primera_instancia_no_pecuniaria():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, None, False)
    ]
    assert rango == RangoTarifa(Decimal("1"), Decimal("10"), UnidadTarifa.SMLMV)


def test_declarativo_general_segunda_instancia():
    for pecuniaria in (True, False):
        rango = TARIFAS_AGENCIAS_EN_DERECHO[
            (TipoProceso.DECLARATIVO_GENERAL, Instancia.SEGUNDA, None, pecuniaria)
        ]
        assert rango == RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV)
```

- [ ] **Step 4: Correr el test y verificar que falla**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.engine.costs.agencias_en_derecho'`

- [ ] **Step 5: Crear el módulo con los enums, el dataclass y la primera categoría**

Crear `app/engine/costs/agencias_en_derecho.py`:

```python
"""Tarifas de agencias en derecho (costas judiciales), Acuerdo PSAA16-10554 del
5 de agosto de 2016, Consejo Superior de la Judicatura -- texto oficial
completo verificado durante el Sprint 18 (ver design spec, "Fuentes externas").
La cita "PCSJA20-11556" del PDF de requisitos de BASTIUM no corresponde a
ningun acuerdo real localizable; este es el acuerdo vigente que sí regula la
materia.

Los umbrales de cuantia (minima/menor/mayor) no vienen de este acuerdo sino
del articulo 25 de la Ley 1564 de 2012 (Codigo General del Proceso), tambien
verificado en 2 fuentes independientes durante este sprint."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from app.core.exceptions import TarifaNoDisponibleError
from app.engine.indexation.historical_index import get_smlmv_for_year
from app.engine.math.rounding import Rounding


class TipoProceso(str, Enum):
    DECLARATIVO_GENERAL = "declarativo_general"
    EXPROPIACION = "expropiacion"
    DESLINDE_AMOJONAMIENTO = "deslinde_amojonamiento"
    DIVISORIO = "divisorio"
    MONITORIO = "monitorio"
    EJECUTIVO = "ejecutivo"
    SUCESION = "sucesion"
    LIQUIDACION_SOCIEDAD_CONYUGAL = "liquidacion_sociedad_conyugal"
    LIQUIDACION_SOCIEDAD_CONYUGAL_EXCEPCIONES = "liquidacion_sociedad_conyugal_excepciones"
    LIQUIDACION_SOCIEDADES = "liquidacion_sociedades"
    INSOLVENCIA_PERSONA_NATURAL = "insolvencia_persona_natural"
    INSOLVENCIA_PERSONA_NATURAL_LIQUIDACION_PATRIMONIAL = (
        "insolvencia_persona_natural_liquidacion_patrimonial"
    )
    OTROS_LIQUIDACION = "otros_liquidacion"
    JURISDICCION_VOLUNTARIA = "jurisdiccion_voluntaria"
    RECURSO_CONTRA_AUTOS = "recurso_contra_autos"
    INCIDENTE = "incidente"
    RECURSO_EXTRAORDINARIO = "recurso_extraordinario"
    EXEQUATUR = "exequatur"


class Instancia(str, Enum):
    UNICA = "unica"
    PRIMERA = "primera"
    SEGUNDA = "segunda"


class CuantiaTier(str, Enum):
    MINIMA = "minima"
    MENOR = "menor"
    MAYOR = "mayor"


class UnidadTarifa(str, Enum):
    PORCENTAJE = "porcentaje"
    SMLMV = "smlmv"


@dataclass(frozen=True)
class RangoTarifa:
    minimo: Decimal
    maximo: Decimal
    unidad: UnidadTarifa


UMBRAL_MINIMA_CUANTIA_SMLMV = Decimal("40")   # CGP art. 25: pretensiones <= 40 SMLMV
UMBRAL_MENOR_CUANTIA_SMLMV = Decimal("150")   # CGP art. 25: 40 < pretensiones <= 150 SMLMV
                                                # (mayor cuantia: > 150 SMLMV, sin techo)
TOPE_MAXIMO_SMLMV = Decimal("20")             # Acuerdo PSAA16-10554, Paragrafo 3 art. 3

# Clave: (TipoProceso, Instancia, CuantiaTier | None, tiene_pretension_pecuniaria)
# CuantiaTier es None cuando la categoria no distingue por cuantia dentro de esa
# instancia (segunda instancia, recursos, incidentes, y varias categorias de
# liquidacion que el acuerdo tarifa con un solo rango sin importar el monto).
TARIFAS_AGENCIAS_EN_DERECHO: dict[
    tuple[TipoProceso, Instancia, CuantiaTier | None, bool], RangoTarifa
] = {
    # 1. PROCESOS DECLARATIVOS EN GENERAL (art. 5.1)
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.UNICA, CuantiaTier.MINIMA, True):
        RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.UNICA, None, False):
        RangoTarifa(Decimal("1"), Decimal("8"), UnidadTarifa.SMLMV),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, CuantiaTier.MENOR, True):
        RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, CuantiaTier.MAYOR, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, None, False):
        RangoTarifa(Decimal("1"), Decimal("10"), UnidadTarifa.SMLMV),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.SEGUNDA, None, False):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
}
```

- [ ] **Step 6: Correr el test y verificar que pasa**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -v`
Expected: 7 passed

- [ ] **Step 7: Commit**

```bash
git add app/engine/costs tests/engine/costs app/core/exceptions.py
git commit -m "feat: add agencias en derecho tariff table (declarativo general)"
```

---

## Task 2: `resolver_cuantia_tier` (umbrales CGP art. 25)

**Files:**
- Modify: `app/engine/costs/agencias_en_derecho.py`
- Test: `tests/engine/costs/test_agencias_en_derecho.py`

- [ ] **Step 1: Escribir los tests (fallan: la función no existe)**

Agregar a `tests/engine/costs/test_agencias_en_derecho.py`:

```python
from app.engine.costs.agencias_en_derecho import resolver_cuantia_tier

_SMLMV_2024 = Decimal("1300000.00")  # historical_index._SMLMV_POR_ANIO[2024]


def test_resolver_cuantia_tier_minima_dentro_del_limite():
    # 40 SMLMV exactos = limite superior de minima cuantia (CGP art. 25: "no exceda").
    assert resolver_cuantia_tier(Decimal("52000000.00"), _SMLMV_2024) == CuantiaTier.MINIMA


def test_resolver_cuantia_tier_menor_justo_sobre_el_limite_de_minima():
    assert resolver_cuantia_tier(Decimal("52000001.00"), _SMLMV_2024) == CuantiaTier.MENOR


def test_resolver_cuantia_tier_menor_en_su_limite_superior():
    # 150 SMLMV exactos = limite superior de menor cuantia.
    assert resolver_cuantia_tier(Decimal("195000000.00"), _SMLMV_2024) == CuantiaTier.MENOR


def test_resolver_cuantia_tier_mayor_justo_sobre_el_limite_de_menor():
    assert resolver_cuantia_tier(Decimal("195000001.00"), _SMLMV_2024) == CuantiaTier.MAYOR


def test_resolver_cuantia_tier_mayor_valor_grande():
    assert resolver_cuantia_tier(Decimal("5000000000.00"), _SMLMV_2024) == CuantiaTier.MAYOR
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -k resolver_cuantia_tier -v`
Expected: FAIL con `ImportError: cannot import name 'resolver_cuantia_tier'`

- [ ] **Step 3: Implementar `resolver_cuantia_tier`**

Agregar a `app/engine/costs/agencias_en_derecho.py`, después de las constantes de umbral:

```python
def resolver_cuantia_tier(pretensiones_reconocidas: Decimal, smlmv_vigente: Decimal) -> CuantiaTier:
    """CGP art. 25: minima <= 40 SMLMV, menor entre 40 y 150 SMLMV, mayor > 150 SMLMV."""
    if pretensiones_reconocidas <= UMBRAL_MINIMA_CUANTIA_SMLMV * smlmv_vigente:
        return CuantiaTier.MINIMA
    if pretensiones_reconocidas <= UMBRAL_MENOR_CUANTIA_SMLMV * smlmv_vigente:
        return CuantiaTier.MENOR
    return CuantiaTier.MAYOR
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -k resolver_cuantia_tier -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add app/engine/costs/agencias_en_derecho.py tests/engine/costs/test_agencias_en_derecho.py
git commit -m "feat: add cuantia tier resolution (CGP art. 25)"
```

---

## Task 3: Interpolación lineal (ponderación inversa)

**Files:**
- Modify: `app/engine/costs/agencias_en_derecho.py`
- Test: `tests/engine/costs/test_agencias_en_derecho.py`

- [ ] **Step 1: Escribir los tests (fallan: la función no existe)**

Agregar a `tests/engine/costs/test_agencias_en_derecho.py`:

```python
from app.engine.costs.agencias_en_derecho import _interpolar_dentro_de_rango


def test_interpolar_en_el_piso_del_tier_da_el_porcentaje_maximo():
    resultado = _interpolar_dentro_de_rango(
        minimo=Decimal("3"), maximo=Decimal("7.5"),
        valor=Decimal("0"), floor=Decimal("0"), ceiling=Decimal("100"),
    )
    assert resultado == Decimal("7.5")


def test_interpolar_en_el_techo_del_tier_da_el_porcentaje_minimo():
    resultado = _interpolar_dentro_de_rango(
        minimo=Decimal("3"), maximo=Decimal("7.5"),
        valor=Decimal("100"), floor=Decimal("0"), ceiling=Decimal("100"),
    )
    assert resultado == Decimal("3")


def test_interpolar_en_el_punto_medio():
    resultado = _interpolar_dentro_de_rango(
        minimo=Decimal("3"), maximo=Decimal("7.5"),
        valor=Decimal("50"), floor=Decimal("0"), ceiling=Decimal("100"),
    )
    assert resultado == Decimal("5.25")


def test_interpolar_sin_techo_devuelve_siempre_el_minimo():
    # Tier "mayor cuantia" no tiene limite superior (CGP art. 25) -- no hay
    # base matematica para interpolar contra el infinito, se usa el minimo
    # del rango (el extremo de "a mayor valor, menor porcentaje" llevado al
    # limite). Documentado en el design spec como aproximacion explicita.
    resultado = _interpolar_dentro_de_rango(
        minimo=Decimal("3"), maximo=Decimal("7.5"),
        valor=Decimal("999999999"), floor=Decimal("100"), ceiling=None,
    )
    assert resultado == Decimal("3")
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -k interpolar -v`
Expected: FAIL con `ImportError`

- [ ] **Step 3: Implementar**

Agregar a `app/engine/costs/agencias_en_derecho.py`:

```python
def _interpolar_dentro_de_rango(
    minimo: Decimal, maximo: Decimal, valor: Decimal, floor: Decimal, ceiling: Decimal | None
) -> Decimal:
    """Paragrafo 3, articulo 3, Acuerdo PSAA16-10554: 'a mayor valor menor
    porcentaje, a menor valor mayor porcentaje'. Interpolacion lineal entre
    los limites del tier de cuantia -- el acuerdo exige el principio pero no
    da la formula matematica exacta (aproximacion documentada, ver design
    spec). Si el tier no tiene techo (mayor cuantia), no hay base para
    interpolar: se devuelve el minimo del rango."""
    if ceiling is None:
        return minimo
    posicion = (valor - floor) / (ceiling - floor)
    posicion = max(Decimal("0"), min(Decimal("1"), posicion))
    return maximo - posicion * (maximo - minimo)
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -k interpolar -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/engine/costs/agencias_en_derecho.py tests/engine/costs/test_agencias_en_derecho.py
git commit -m "feat: add linear interpolation for agencias en derecho ranges"
```

---

## Task 4: `calcular_agencias_en_derecho` (orquestación completa)

**Files:**
- Modify: `app/engine/costs/agencias_en_derecho.py`
- Test: `tests/engine/costs/test_agencias_en_derecho.py`

- [ ] **Step 1: Escribir los tests (fallan: la función no existe)**

Agregar a `tests/engine/costs/test_agencias_en_derecho.py`:

```python
from datetime import date

from app.core.exceptions import TarifaNoDisponibleError
from app.engine.costs.agencias_en_derecho import calcular_agencias_en_derecho
```

Y una fixture de base de datos en memoria (mismo patrón que `tests/engine/test_smlmv_to_uvt.py`, porque
`get_smlmv_for_year` lee de `parametro_service`):

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

import database.session as session_module
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _db_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="SMLMV", valor=_SMLMV_2024, vigente_desde=date(2024, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
    ))
    session.commit()
    session.close()


def test_calcular_minima_cuantia_declarativo_unica_instancia():
    # Punto medio del tier minima (0 a 52.000.000): 26.000.000 -> posicion=0.5
    # -> pct = 15 - 0.5*10 = 10% -> 2.600.000
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.UNICA,
        pretensiones_reconocidas=Decimal("26000000.00"), fecha_radicacion=date(2024, 6, 1),
    )
    assert resultado == Decimal("2600000.00")


def test_calcular_menor_cuantia_cerca_del_piso_del_tier_da_un_porcentaje_alto():
    # 87.750.000 esta al 25% del recorrido del tier menor cuantia (52.000.000
    # a 195.000.000): posicion=0.25 -> pct = 10 - 0.25*6 = 8.5%. No se usa
    # exactamente el piso (52.000.000 = 40 SMLMV) porque ese valor cae en el
    # limite inclusivo de minima cuantia (resolver_cuantia_tier usa "<="), no
    # en menor cuantia -- la matematica exacta del piso/techo ya esta cubierta
    # por los tests puros de _interpolar_dentro_de_rango (Task 3).
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.PRIMERA,
        pretensiones_reconocidas=Decimal("87750000.00"), fecha_radicacion=date(2024, 6, 1),
    )
    assert resultado == Decimal("7458750.00")  # 87.750.000 * 8.5%


def test_calcular_menor_cuantia_en_el_techo_del_tier_da_el_porcentaje_minimo():
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.PRIMERA,
        pretensiones_reconocidas=Decimal("195000000.00"), fecha_radicacion=date(2024, 6, 1),
    )
    assert resultado == Decimal("7800000.00")  # 195.000.000 * 4%


def test_calcular_mayor_cuantia_usa_siempre_el_porcentaje_minimo():
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.PRIMERA,
        pretensiones_reconocidas=Decimal("300000000.00"), fecha_radicacion=date(2024, 6, 1),
    )
    assert resultado == Decimal("9000000.00")  # 300.000.000 * 3%


def test_calcular_aplica_tope_de_20_smlmv():
    # 3% de 1.000.000.000 = 30.000.000, pero el tope es 20 * 1.300.000 = 26.000.000.
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.PRIMERA,
        pretensiones_reconocidas=Decimal("1000000000.00"), fecha_radicacion=date(2024, 6, 1),
    )
    assert resultado == Decimal("26000000.00")


def test_calcular_no_pecuniaria_usa_punto_medio_en_smlmv():
    # Primera instancia, sin pretension pecuniaria: 1-10 SMLMV -> punto medio 5.5 SMLMV.
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.PRIMERA,
        pretensiones_reconocidas=Decimal("1.00"), fecha_radicacion=date(2024, 6, 1),
        tiene_pretension_pecuniaria=False,
    )
    assert resultado == Decimal("7150000.00")  # 5.5 * 1.300.000


def test_calcular_pretensiones_no_positivas_lanza_value_error():
    with pytest.raises(ValueError):
        calcular_agencias_en_derecho(
            tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.UNICA,
            pretensiones_reconocidas=Decimal("0.00"), fecha_radicacion=date(2024, 6, 1),
        )


def test_calcular_combinacion_no_registrada_lanza_tarifa_no_disponible():
    with pytest.raises(TarifaNoDisponibleError):
        calcular_agencias_en_derecho(
            tipo_proceso=TipoProceso.EXPROPIACION, instancia=Instancia.UNICA,
            pretensiones_reconocidas=Decimal("10000000.00"), fecha_radicacion=date(2024, 6, 1),
        )
```

Nota: la fixture de arriba debe reemplazar/fusionarse con la que ya exista en el archivo tras el Task 1 —
si `test_agencias_en_derecho.py` no tenía todavía una fixture de base de datos, esta es la primera; queda
como `autouse=True` para todo el archivo, igual que en `tests/engine/test_smlmv_to_uvt.py`. `_SMLMV_2024`
ya se definió en el Task 2, no se repite.

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -k calcular -v`
Expected: FAIL con `ImportError`

- [ ] **Step 3: Implementar**

Agregar a `app/engine/costs/agencias_en_derecho.py`:

```python
def _limites_pesos_tier(tier: CuantiaTier, smlmv_vigente: Decimal) -> tuple[Decimal, Decimal | None]:
    if tier == CuantiaTier.MINIMA:
        return Decimal("0"), UMBRAL_MINIMA_CUANTIA_SMLMV * smlmv_vigente
    if tier == CuantiaTier.MENOR:
        return UMBRAL_MINIMA_CUANTIA_SMLMV * smlmv_vigente, UMBRAL_MENOR_CUANTIA_SMLMV * smlmv_vigente
    return UMBRAL_MENOR_CUANTIA_SMLMV * smlmv_vigente, None  # MAYOR: sin techo


def calcular_agencias_en_derecho(
    tipo_proceso: TipoProceso,
    instancia: Instancia,
    pretensiones_reconocidas: Decimal,
    fecha_radicacion: date,
    tiene_pretension_pecuniaria: bool = True,
) -> Decimal:
    """Calcula agencias en derecho segun el Acuerdo PSAA16-10554. Busca primero
    la tarifa especifica del tier de cuantia resuelto; si la categoria no
    distingue por cuantia (la mayoria de segundas instancias, recursos,
    incidentes, y varias categorias de liquidacion), cae al registro sin tier.
    Lanza TarifaNoDisponibleError si ninguna de las dos claves esta registrada
    -- nunca inventa un rango."""
    if pretensiones_reconocidas is None or pretensiones_reconocidas <= Decimal("0.00"):
        raise ValueError("pretensiones_reconocidas debe ser mayor que cero.")

    smlmv_vigente = get_smlmv_for_year(fecha_radicacion.year)
    tier = resolver_cuantia_tier(pretensiones_reconocidas, smlmv_vigente) if tiene_pretension_pecuniaria else None

    rango = TARIFAS_AGENCIAS_EN_DERECHO.get((tipo_proceso, instancia, tier, tiene_pretension_pecuniaria))
    if rango is None and tier is not None:
        rango = TARIFAS_AGENCIAS_EN_DERECHO.get((tipo_proceso, instancia, None, tiene_pretension_pecuniaria))
    if rango is None:
        raise TarifaNoDisponibleError(
            f"No hay tarifa de agencias en derecho (Acuerdo PSAA16-10554) registrada para "
            f"{tipo_proceso.value}/{instancia.value} (pecuniaria={tiene_pretension_pecuniaria})."
        )

    if rango.unidad == UnidadTarifa.PORCENTAJE and tier is not None:
        floor, ceiling = _limites_pesos_tier(tier, smlmv_vigente)
        porcentaje = _interpolar_dentro_de_rango(rango.minimo, rango.maximo, pretensiones_reconocidas, floor, ceiling)
        monto = pretensiones_reconocidas * porcentaje / Decimal("100")
    elif rango.unidad == UnidadTarifa.PORCENTAJE:
        porcentaje = (rango.minimo + rango.maximo) / Decimal("2")
        monto = pretensiones_reconocidas * porcentaje / Decimal("100")
    else:  # SMLMV, sin tier de cuantia aplicable -> punto medio del rango
        cantidad_smlmv = (rango.minimo + rango.maximo) / Decimal("2")
        monto = cantidad_smlmv * smlmv_vigente

    tope = TOPE_MAXIMO_SMLMV * smlmv_vigente
    return Rounding.money(min(monto, tope))
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -v`
Expected: todos los tests del archivo pasan (Tasks 1-4 acumulados)

- [ ] **Step 5: Commit**

```bash
git add app/engine/costs/agencias_en_derecho.py tests/engine/costs/test_agencias_en_derecho.py
git commit -m "feat: add calcular_agencias_en_derecho orchestration"
```

---

## Task 5: Declarativos especiales (expropiación, deslinde, divisorio) + monitorio

**Files:**
- Modify: `app/engine/costs/agencias_en_derecho.py`
- Test: `tests/engine/costs/test_agencias_en_derecho.py`

- [ ] **Step 1: Escribir los tests (fallan: `KeyError` — las entradas no existen)**

Agregar a `tests/engine/costs/test_agencias_en_derecho.py`:

```python
def test_expropiacion_primera_instancia():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[(TipoProceso.EXPROPIACION, Instancia.PRIMERA, None, True)]
    assert rango == RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE)


def test_expropiacion_segunda_instancia():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[(TipoProceso.EXPROPIACION, Instancia.SEGUNDA, None, True)]
    assert rango == RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV)


def test_deslinde_amojonamiento_todas_las_instancias():
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DESLINDE_AMOJONAMIENTO, Instancia.UNICA, CuantiaTier.MINIMA, True)
    ] == RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DESLINDE_AMOJONAMIENTO, Instancia.PRIMERA, CuantiaTier.MENOR, True)
    ] == RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DESLINDE_AMOJONAMIENTO, Instancia.PRIMERA, CuantiaTier.MAYOR, True)
    ] == RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DESLINDE_AMOJONAMIENTO, Instancia.SEGUNDA, None, True)
    ] == RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV)


def test_divisorio_todas_las_instancias():
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DIVISORIO, Instancia.UNICA, CuantiaTier.MINIMA, True)
    ] == RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DIVISORIO, Instancia.PRIMERA, CuantiaTier.MENOR, True)
    ] == RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DIVISORIO, Instancia.PRIMERA, CuantiaTier.MAYOR, True)
    ] == RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DIVISORIO, Instancia.SEGUNDA, None, True)
    ] == RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV)


def test_monitorio_hasta_5_por_ciento():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[(TipoProceso.MONITORIO, Instancia.UNICA, None, True)]
    assert rango == RangoTarifa(Decimal("0"), Decimal("5"), UnidadTarifa.PORCENTAJE)
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -k "expropiacion or deslinde or divisorio or monitorio" -v`
Expected: FAIL con `KeyError`

- [ ] **Step 3: Agregar las entradas al diccionario**

En `app/engine/costs/agencias_en_derecho.py`, agregar dentro de `TARIFAS_AGENCIAS_EN_DERECHO` (antes de la
llave de cierre `}`):

```python
    # 2.1. PROCESOS DE EXPROPIACION (art. 5.2.1)
    (TipoProceso.EXPROPIACION, Instancia.PRIMERA, None, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EXPROPIACION, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 2.2. PROCESOS DE DESLINDE Y AMOJONAMIENTO (art. 5.2.2)
    (TipoProceso.DESLINDE_AMOJONAMIENTO, Instancia.UNICA, CuantiaTier.MINIMA, True):
        RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DESLINDE_AMOJONAMIENTO, Instancia.PRIMERA, CuantiaTier.MENOR, True):
        RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DESLINDE_AMOJONAMIENTO, Instancia.PRIMERA, CuantiaTier.MAYOR, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DESLINDE_AMOJONAMIENTO, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 2.3. PROCESOS DIVISORIOS (art. 5.2.3)
    (TipoProceso.DIVISORIO, Instancia.UNICA, CuantiaTier.MINIMA, True):
        RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DIVISORIO, Instancia.PRIMERA, CuantiaTier.MENOR, True):
        RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DIVISORIO, Instancia.PRIMERA, CuantiaTier.MAYOR, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DIVISORIO, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 3. PROCESO MONITORIO (art. 5.3): "hasta el 5%" -- sin piso explicito en
    # el texto, se modela con piso 0 (lectura razonable de "hasta").
    (TipoProceso.MONITORIO, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("0"), Decimal("5"), UnidadTarifa.PORCENTAJE),
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -v`
Expected: todos pasan

- [ ] **Step 5: Commit**

```bash
git add app/engine/costs/agencias_en_derecho.py tests/engine/costs/test_agencias_en_derecho.py
git commit -m "feat: add expropiacion, deslinde, divisorio y monitorio tariffs"
```

---

## Task 6: Procesos ejecutivos

**Files:**
- Modify: `app/engine/costs/agencias_en_derecho.py`
- Test: `tests/engine/costs/test_agencias_en_derecho.py`

- [ ] **Step 1: Escribir los tests**

Agregar a `tests/engine/costs/test_agencias_en_derecho.py`:

```python
@pytest.mark.parametrize("instancia", [Instancia.UNICA, Instancia.PRIMERA])
def test_ejecutivo_minima_cuantia_unica_y_primera(instancia):
    rango = TARIFAS_AGENCIAS_EN_DERECHO[(TipoProceso.EJECUTIVO, instancia, CuantiaTier.MINIMA, True)]
    assert rango == RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE)


@pytest.mark.parametrize("instancia", [Instancia.UNICA, Instancia.PRIMERA])
def test_ejecutivo_menor_cuantia_unica_y_primera(instancia):
    rango = TARIFAS_AGENCIAS_EN_DERECHO[(TipoProceso.EJECUTIVO, instancia, CuantiaTier.MENOR, True)]
    assert rango == RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE)


@pytest.mark.parametrize("instancia", [Instancia.UNICA, Instancia.PRIMERA])
def test_ejecutivo_mayor_cuantia_unica_y_primera(instancia):
    rango = TARIFAS_AGENCIAS_EN_DERECHO[(TipoProceso.EJECUTIVO, instancia, CuantiaTier.MAYOR, True)]
    assert rango == RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE)


@pytest.mark.parametrize("instancia", [Instancia.UNICA, Instancia.PRIMERA])
def test_ejecutivo_sin_contenido_dinerario(instancia):
    rango = TARIFAS_AGENCIAS_EN_DERECHO[(TipoProceso.EJECUTIVO, instancia, None, False)]
    assert rango == RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV)


@pytest.mark.parametrize("pecuniaria", [True, False])
def test_ejecutivo_segunda_instancia(pecuniaria):
    rango = TARIFAS_AGENCIAS_EN_DERECHO[(TipoProceso.EJECUTIVO, Instancia.SEGUNDA, None, pecuniaria)]
    assert rango == RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV)
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -k ejecutivo -v`
Expected: FAIL con `KeyError`

- [ ] **Step 3: Agregar las entradas**

En `app/engine/costs/agencias_en_derecho.py`, dentro de `TARIFAS_AGENCIAS_EN_DERECHO`:

```python
    # 4. PROCESOS EJECUTIVOS (art. 5.4). El acuerdo agrupa "unica y primera
    # instancia" bajo el mismo encabezado con 3 tiers explicitos; los dos
    # resultados posibles (sentencia sigue adelante / excepciones favorables)
    # dan el mismo porcentaje por tier, se registra una sola vez por tier.
    (TipoProceso.EJECUTIVO, Instancia.UNICA, CuantiaTier.MINIMA, True):
        RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EJECUTIVO, Instancia.PRIMERA, CuantiaTier.MINIMA, True):
        RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EJECUTIVO, Instancia.UNICA, CuantiaTier.MENOR, True):
        RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EJECUTIVO, Instancia.PRIMERA, CuantiaTier.MENOR, True):
        RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EJECUTIVO, Instancia.UNICA, CuantiaTier.MAYOR, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EJECUTIVO, Instancia.PRIMERA, CuantiaTier.MAYOR, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EJECUTIVO, Instancia.UNICA, None, False):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.EJECUTIVO, Instancia.PRIMERA, None, False):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.EJECUTIVO, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.EJECUTIVO, Instancia.SEGUNDA, None, False):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -v`
Expected: todos pasan

- [ ] **Step 5: Commit**

```bash
git add app/engine/costs/agencias_en_derecho.py tests/engine/costs/test_agencias_en_derecho.py
git commit -m "feat: add procesos ejecutivos tariffs"
```

---

## Task 7: Procesos de liquidación (sucesión, sociedad conyugal, sociedades)

**Files:**
- Modify: `app/engine/costs/agencias_en_derecho.py`
- Test: `tests/engine/costs/test_agencias_en_derecho.py`

- [ ] **Step 1: Escribir los tests**

Agregar a `tests/engine/costs/test_agencias_en_derecho.py`:

```python
def test_sucesion_todas_las_instancias():
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.SUCESION, Instancia.UNICA, CuantiaTier.MINIMA, True)
    ] == RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.SUCESION, Instancia.PRIMERA, CuantiaTier.MENOR, True)
    ] == RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.SUCESION, Instancia.PRIMERA, CuantiaTier.MAYOR, True)
    ] == RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.SUCESION, Instancia.SEGUNDA, None, True)
    ] == RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV)


def test_liquidacion_sociedad_conyugal_objeciones():
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.LIQUIDACION_SOCIEDAD_CONYUGAL, Instancia.PRIMERA, None, True)
    ] == RangoTarifa(Decimal("3"), Decimal("15"), UnidadTarifa.PORCENTAJE)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.LIQUIDACION_SOCIEDAD_CONYUGAL, Instancia.SEGUNDA, None, True)
    ] == RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV)


def test_liquidacion_sociedad_conyugal_excepciones():
    # Distinto de las objeciones: 1-6 SMLMV en vez de 3%-15% -- por eso es un
    # TipoProceso separado (ver nota en la cabecera de este plan).
    rango = TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.LIQUIDACION_SOCIEDAD_CONYUGAL_EXCEPCIONES, Instancia.PRIMERA, None, True)
    ]
    assert rango == RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV)


def test_liquidacion_sociedades():
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.LIQUIDACION_SOCIEDADES, Instancia.PRIMERA, None, True)
    ] == RangoTarifa(Decimal("3"), Decimal("15"), UnidadTarifa.PORCENTAJE)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.LIQUIDACION_SOCIEDADES, Instancia.SEGUNDA, None, True)
    ] == RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV)
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -k "sucesion or sociedad_conyugal or sociedades" -v`
Expected: FAIL con `KeyError`

- [ ] **Step 3: Agregar las entradas**

En `app/engine/costs/agencias_en_derecho.py`, dentro de `TARIFAS_AGENCIAS_EN_DERECHO`:

```python
    # 5.1. PROCESOS DE SUCESION (art. 5.5.1). Objeciones a inventarios/avaluos
    # y objeciones a la particion tienen identico rango por tier -- se
    # registran una sola vez.
    (TipoProceso.SUCESION, Instancia.UNICA, CuantiaTier.MINIMA, True):
        RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.SUCESION, Instancia.PRIMERA, CuantiaTier.MENOR, True):
        RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.SUCESION, Instancia.PRIMERA, CuantiaTier.MAYOR, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.SUCESION, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 5.2. LIQUIDACION DE SOCIEDADES CONYUGALES O PATRIMONIALES (art. 5.5.2).
    # "Objeciones a inventarios/avaluos" y "objeciones a la particion" (ambas
    # 3%-15%) se registran juntas como LIQUIDACION_SOCIEDAD_CONYUGAL; "cuando
    # prosperan o fracasan las excepciones" (1-6 SMLMV, un resultado distinto
    # del mismo epigrafe del acuerdo) es LIQUIDACION_SOCIEDAD_CONYUGAL_EXCEPCIONES.
    (TipoProceso.LIQUIDACION_SOCIEDAD_CONYUGAL, Instancia.PRIMERA, None, True):
        RangoTarifa(Decimal("3"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.LIQUIDACION_SOCIEDAD_CONYUGAL, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.LIQUIDACION_SOCIEDAD_CONYUGAL_EXCEPCIONES, Instancia.PRIMERA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 5.3. LIQUIDACION DE SOCIEDADES (art. 5.5.3). Objeciones al inventario y
    # objeciones a la propuesta de distribucion, ambas 3%-15% -- se registran juntas.
    (TipoProceso.LIQUIDACION_SOCIEDADES, Instancia.PRIMERA, None, True):
        RangoTarifa(Decimal("3"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.LIQUIDACION_SOCIEDADES, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -v`
Expected: todos pasan

- [ ] **Step 5: Commit**

```bash
git add app/engine/costs/agencias_en_derecho.py tests/engine/costs/test_agencias_en_derecho.py
git commit -m "feat: add sucesion y liquidacion de sociedades tariffs"
```

---

## Task 8: Insolvencia de persona natural + otros procesos de liquidación

**Files:**
- Modify: `app/engine/costs/agencias_en_derecho.py`
- Test: `tests/engine/costs/test_agencias_en_derecho.py`

- [ ] **Step 1: Escribir los tests**

Agregar a `tests/engine/costs/test_agencias_en_derecho.py`:

```python
def test_insolvencia_persona_natural():
    # Los 6 items del art. 5.5.4 con rango 1/2-6 SMLMV (negociacion de deudas,
    # reforma del acuerdo, convalidacion, impugnacion, cumplimiento, objeciones
    # a creditos) comparten identico rango -- una sola entrada.
    rango = TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.INSOLVENCIA_PERSONA_NATURAL, Instancia.UNICA, None, True)
    ]
    assert rango == RangoTarifa(Decimal("0.5"), Decimal("6"), UnidadTarifa.SMLMV)


def test_insolvencia_persona_natural_liquidacion_patrimonial():
    # Objeciones a inventarios/avaluos y al proyecto de adjudicacion dentro de
    # la liquidacion patrimonial: 3%-15%, distinto del resto del art. 5.5.4.
    rango = TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.INSOLVENCIA_PERSONA_NATURAL_LIQUIDACION_PATRIMONIAL, Instancia.UNICA, None, True)
    ]
    assert rango == RangoTarifa(Decimal("3"), Decimal("15"), UnidadTarifa.PORCENTAJE)


def test_otros_procesos_de_liquidacion():
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.OTROS_LIQUIDACION, Instancia.PRIMERA, None, True)
    ] == RangoTarifa(Decimal("3"), Decimal("15"), UnidadTarifa.PORCENTAJE)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.OTROS_LIQUIDACION, Instancia.SEGUNDA, None, True)
    ] == RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV)
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -k "insolvencia or otros_procesos" -v`
Expected: FAIL con `KeyError`

- [ ] **Step 3: Agregar las entradas**

En `app/engine/costs/agencias_en_derecho.py`, dentro de `TARIFAS_AGENCIAS_EN_DERECHO`:

```python
    # 5.4. INSOLVENCIA DE PERSONA NATURAL NO COMERCIANTE (art. 5.5.4). El
    # acuerdo no indica instancia para esta categoria -- se usa Instancia.UNICA
    # por convencion de modelado (el valor y el texto legal son exactos, solo
    # la etiqueta de instancia es una convencion, ver design spec).
    (TipoProceso.INSOLVENCIA_PERSONA_NATURAL, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("0.5"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.INSOLVENCIA_PERSONA_NATURAL_LIQUIDACION_PATRIMONIAL, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("3"), Decimal("15"), UnidadTarifa.PORCENTAJE),

    # 5.5. OTROS PROCESOS DE LIQUIDACION (art. 5.5.5).
    (TipoProceso.OTROS_LIQUIDACION, Instancia.PRIMERA, None, True):
        RangoTarifa(Decimal("3"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.OTROS_LIQUIDACION, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -v`
Expected: todos pasan

- [ ] **Step 5: Commit**

```bash
git add app/engine/costs/agencias_en_derecho.py tests/engine/costs/test_agencias_en_derecho.py
git commit -m "feat: add insolvencia de persona natural y otros procesos de liquidacion"
```

---

## Task 9: Jurisdicción voluntaria, recursos, incidentes, recursos extraordinarios, exequátur

**Files:**
- Modify: `app/engine/costs/agencias_en_derecho.py`
- Test: `tests/engine/costs/test_agencias_en_derecho.py`

- [ ] **Step 1: Escribir los tests**

Agregar a `tests/engine/costs/test_agencias_en_derecho.py`:

```python
def test_jurisdiccion_voluntaria():
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.JURISDICCION_VOLUNTARIA, Instancia.UNICA, None, True)
    ] == RangoTarifa(Decimal("0.5"), Decimal("6"), UnidadTarifa.SMLMV)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.JURISDICCION_VOLUNTARIA, Instancia.PRIMERA, None, True)
    ] == RangoTarifa(Decimal("0.5"), Decimal("6"), UnidadTarifa.SMLMV)
    assert TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.JURISDICCION_VOLUNTARIA, Instancia.SEGUNDA, None, True)
    ] == RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV)


def test_recurso_contra_autos():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[(TipoProceso.RECURSO_CONTRA_AUTOS, Instancia.UNICA, None, True)]
    assert rango == RangoTarifa(Decimal("0.5"), Decimal("4"), UnidadTarifa.SMLMV)


def test_incidente():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[(TipoProceso.INCIDENTE, Instancia.UNICA, None, True)]
    assert rango == RangoTarifa(Decimal("0.5"), Decimal("4"), UnidadTarifa.SMLMV)


def test_recurso_extraordinario():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[(TipoProceso.RECURSO_EXTRAORDINARIO, Instancia.UNICA, None, True)]
    assert rango == RangoTarifa(Decimal("1"), Decimal("20"), UnidadTarifa.SMLMV)


def test_exequatur():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[(TipoProceso.EXEQUATUR, Instancia.UNICA, None, True)]
    assert rango == RangoTarifa(Decimal("1"), Decimal("20"), UnidadTarifa.SMLMV)


def test_recurso_extraordinario_en_el_techo_del_rango_toca_exactamente_el_tope():
    # Punto medio de 1-20 SMLMV = 10.5 SMLMV, muy por debajo del tope de 20 --
    # este test confirma que el propio rango de esta categoria puede llegar
    # hasta el tope maximo sin necesitar interpolacion adicional.
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.RECURSO_EXTRAORDINARIO, instancia=Instancia.UNICA,
        pretensiones_reconocidas=Decimal("1.00"), fecha_radicacion=date(2024, 6, 1),
    )
    assert resultado == Decimal("13650000.00")  # 10.5 * 1.300.000
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -k "jurisdiccion_voluntaria or recurso_contra_autos or test_incidente or recurso_extraordinario or exequatur" -v`
Expected: FAIL con `KeyError`

- [ ] **Step 3: Agregar las entradas**

En `app/engine/costs/agencias_en_derecho.py`, dentro de `TARIFAS_AGENCIAS_EN_DERECHO`:

```python
    # 6. JURISDICCION VOLUNTARIA Y ASIMILABLES (art. 5.6, cuando hay oposicion).
    (TipoProceso.JURISDICCION_VOLUNTARIA, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("0.5"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.JURISDICCION_VOLUNTARIA, Instancia.PRIMERA, None, True):
        RangoTarifa(Decimal("0.5"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.JURISDICCION_VOLUNTARIA, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 7. RECURSOS CONTRA AUTOS (art. 5.7). Instancia no distinguida en el texto.
    (TipoProceso.RECURSO_CONTRA_AUTOS, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("0.5"), Decimal("4"), UnidadTarifa.SMLMV),

    # 8. INCIDENTES Y ASUNTOS ASIMILABLES (art. 5.8). Instancia no distinguida.
    (TipoProceso.INCIDENTE, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("0.5"), Decimal("4"), UnidadTarifa.SMLMV),

    # 9. RECURSOS EXTRAORDINARIOS (art. 5.9). Instancia no distinguida.
    (TipoProceso.RECURSO_EXTRAORDINARIO, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("1"), Decimal("20"), UnidadTarifa.SMLMV),

    # 10. EXEQUATUR (art. 5.10). Instancia no distinguida.
    (TipoProceso.EXEQUATUR, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("1"), Decimal("20"), UnidadTarifa.SMLMV),
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/engine/costs/test_agencias_en_derecho.py -v`
Expected: todos pasan (tabla completa: 18 tipos de proceso transcritos)

- [ ] **Step 5: Commit**

```bash
git add app/engine/costs/agencias_en_derecho.py tests/engine/costs/test_agencias_en_derecho.py
git commit -m "feat: complete agencias en derecho tariff table (all 18 tipos de proceso)"
```

---

## Task 10: Campos nuevos en `Obligacion` + migración

**Files:**
- Modify: `database/models.py:115` (justo después de `costas_pct_manual`)
- Create: `scripts/migrate_costas_tipo_proceso.py`
- Test: `tests/database/test_migrate_costas_tipo_proceso.py`

- [ ] **Step 1: Agregar los campos al modelo**

En `database/models.py`, después de la línea `costas_pct_manual: Mapped[Decimal | None] = ...`:

```python
    costas_tipo_proceso: Mapped[str | None] = mapped_column(String(60), nullable=True)
    costas_instancia: Mapped[str | None] = mapped_column(String(10), nullable=True)
```

- [ ] **Step 2: Escribir el test de migración (falla: el script no existe)**

Crear `tests/database/test_migrate_costas_tipo_proceso.py`:

```python
import sqlite3
import tempfile
from pathlib import Path

from scripts.migrate_costas_tipo_proceso import migrar


def test_migrar_agrega_las_dos_columnas_en_bd_sin_ellas():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY)")
        con.commit()
        con.close()

        aplico = migrar(db_path)
        assert aplico is True

        con = sqlite3.connect(db_path)
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        con.close()
        assert "costas_tipo_proceso" in columnas
        assert "costas_instancia" in columnas


def test_migrar_es_idempotente():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY)")
        con.commit()
        con.close()

        migrar(db_path)
        aplico_segunda_vez = migrar(db_path)
        assert aplico_segunda_vez is False
```

- [ ] **Step 3: Correr y verificar que falla**

Run: `pytest tests/database/test_migrate_costas_tipo_proceso.py -v`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 4: Escribir el script de migración**

Crear `scripts/migrate_costas_tipo_proceso.py` (mismo patrón que
`scripts/migrate_aplica_indexacion_ipc.py`):

```python
"""Migracion de esquema (Sprint 18): agrega las columnas costas_tipo_proceso y
costas_instancia a la tabla obligaciones. Idempotente -- verifica con
PRAGMA table_info antes de alterar."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las dos columnas si no existen. Retorna True si aplico algun
    ALTER TABLE, False si ambas columnas ya existian."""
    con = sqlite3.connect(db_path)
    try:
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        aplico = False
        if "costas_tipo_proceso" not in columnas:
            con.execute("ALTER TABLE obligaciones ADD COLUMN costas_tipo_proceso VARCHAR(60)")
            aplico = True
        if "costas_instancia" not in columnas:
            con.execute("ALTER TABLE obligaciones ADD COLUMN costas_instancia VARCHAR(10)")
            aplico = True
        con.commit()
        return aplico
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columnas costas_tipo_proceso/costas_instancia agregadas a obligaciones.")
    else:
        print("Las columnas costas_tipo_proceso/costas_instancia ya existian, no se hizo nada.")
```

- [ ] **Step 5: Correr y verificar que pasan**

Run: `pytest tests/database/test_migrate_costas_tipo_proceso.py -v`
Expected: 2 passed

- [ ] **Step 6: Correr la migración contra el `bastium.db` real**

Run: `python scripts/migrate_costas_tipo_proceso.py`
Expected: `Columnas costas_tipo_proceso/costas_instancia agregadas a obligaciones.`

- [ ] **Step 7: Commit**

```bash
git add database/models.py scripts/migrate_costas_tipo_proceso.py tests/database/test_migrate_costas_tipo_proceso.py
git commit -m "feat: add costas_tipo_proceso/costas_instancia fields + migration"
```

---

## Task 11: Helper compartido de wiring + refactor de `HonorariosStrategy`

**Files:**
- Modify: `app/services/area_strategy.py`
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir el test del helper compartido (falla: no existe)**

Agregar a `tests/services/test_area_strategy.py`, cerca de los tests de `HonorariosStrategy` (después de
`_obligacion_honorarios`, línea ~656):

```python
from app.services.area_strategy import _evento_costas_procesales


def test_evento_costas_procesales_usa_costas_pct_manual_si_esta_presente():
    obligacion = _obligacion_honorarios(costas_pct_manual=_Decimal("5.00"))
    evento = _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("10000000.00"))
    assert evento is not None
    assert evento.payload["amount"] == _Decimal("500000.00")
    assert evento.event_type == "COSTAS_PROCESALES"


def test_evento_costas_procesales_usa_calculo_automatico_si_hay_tipo_e_instancia():
    # fecha_origen se fuerza a 2024-06-01 (SMLMV 2024 = 1.300.000.00) para que
    # 123.500.000 caiga exactamente en el punto medio del tier menor cuantia
    # (52.000.000 a 195.000.000) -> pct = 10 - 0.5*6 = 7%. El default de
    # _obligacion_honorarios (fecha_origen=2026-01-01) tambien funcionaria,
    # pero forzar el año mantiene el mismo caso de referencia usado en el
    # resto del plan (Tasks 4, 12, 13).
    obligacion = _obligacion_honorarios()
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"
    evento = _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("123500000.00"))
    assert evento is not None
    assert evento.payload["amount"] == _Decimal("8645000.00")


def test_evento_costas_procesales_manual_gana_sobre_automatico():
    obligacion = _obligacion_honorarios(costas_pct_manual=_Decimal("2.00"))
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"
    evento = _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("123500000.00"))
    assert evento.payload["amount"] == _Decimal("2470000.00")  # 2% manual, no el 7% automatico


def test_evento_costas_procesales_sin_ninguno_de_los_dos_retorna_none():
    obligacion = _obligacion_honorarios()
    evento = _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("10000000.00"))
    assert evento is None
```

Nota: `_obligacion_honorarios` (línea 656) usa `fecha_origen` por defecto de 2024 (verificar el valor
exacto en el fixture existente; si usa otro año, ajustar el SMLMV esperado en estos asserts al valor de
`_SMLMV_POR_ANIO` de ese año — la fixture autouse del archivo ya siembra todos los años).

- [ ] **Step 2: Correr y verificar que falla**

Run: `pytest tests/services/test_area_strategy.py -k evento_costas_procesales -v`
Expected: FAIL con `ImportError`

- [ ] **Step 3: Implementar el helper y refactorizar `HonorariosStrategy`**

En `app/services/area_strategy.py`, agregar el import al inicio del archivo:

```python
from app.engine.costs.agencias_en_derecho import Instancia, TipoProceso, calcular_agencias_en_derecho
```

Agregar la función a nivel de módulo, antes de `class AreaStrategy(ABC):`:

```python
def _evento_costas_procesales(obligacion, pretensiones_reconocidas: Decimal) -> Event | None:
    """Costas procesales (agencias en derecho) para cualquier area de litigio
    judicial. costas_pct_manual (Sprint 4) tiene siempre prioridad sobre el
    calculo automatico del Acuerdo PSAA16-10554 (Sprint 18) -- si el auto
    judicial real ya fijo un porcentaje, ese manda. Retorna None si la
    obligacion no tiene ninguno de los dos mecanismos activado (comportamiento
    identico al de antes de este sprint)."""
    if obligacion.costas_pct_manual is not None:
        costas_monto = pretensiones_reconocidas * obligacion.costas_pct_manual / Decimal("100")
    elif obligacion.costas_tipo_proceso is not None and obligacion.costas_instancia is not None:
        costas_monto = calcular_agencias_en_derecho(
            tipo_proceso=TipoProceso(obligacion.costas_tipo_proceso),
            instancia=Instancia(obligacion.costas_instancia),
            pretensiones_reconocidas=pretensiones_reconocidas,
            fecha_radicacion=obligacion.fecha_origen,
        )
    else:
        return None

    return Event(
        date=obligacion.fecha_origen,
        payload={"amount": costas_monto, "label": f"Costas procesales - {obligacion.concepto}"},
        event_type="COSTAS_PROCESALES",
    )
```

Reemplazar el bloque `if obligacion.costas_pct_manual is not None:` de
`HonorariosStrategy._eventos_de_obligacion` (líneas 679-690) por:

```python
        evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=obligacion.beneficio_obtenido)
        if evento_costas is not None:
            eventos.append(evento_costas)
        return eventos
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/services/test_area_strategy.py -v`
Expected: todos pasan, incluyendo los tests preexistentes de `HonorariosStrategy`
(`test_genera_evento_de_costas_si_costas_pct_manual_esta_seteado`,
`test_sin_costas_pct_manual_no_genera_evento_de_costas`) — el refactor no debe romperlos.

- [ ] **Step 5: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat: add shared costas procesales wiring helper, refactor HonorariosStrategy"
```

---

## Task 12: Wiring en `CivilFamiliaStrategy`

**Files:**
- Modify: `app/services/area_strategy.py`
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir el test (falla: no genera el evento)**

Buscar `_obligacion_puntual` (línea 172) en `tests/services/test_area_strategy.py` y agregar un test cerca
de los tests existentes de `CivilFamiliaStrategy`:

```python
def test_civil_familia_genera_evento_de_costas_si_esta_configurado():
    # valor = 123.500.000, fecha_origen forzada a 2024-06-01 (SMLMV 2024 =
    # 1.300.000.00): punto medio exacto del tier menor cuantia (52.000.000 a
    # 195.000.000) -> pct = 7% -> costas = 8.645.000,00. Mismo caso de
    # referencia usado en Tasks 4, 11, 13 y 14.
    obligacion = _obligacion_puntual(valor=_Decimal("123500000.00"))
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.tasa_efectiva_anual = _Decimal("0.00")
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"

    resultado = CivilFamiliaStrategy().liquidar(
        [obligacion], [], fecha_corte=obligacion.fecha_origen,
    )
    tipos_evento = {item.balance.event_type for item in resultado.items}
    assert "COSTAS_PROCESALES" in tipos_evento
    assert resultado.final_balance().principal == _Decimal("132145000.00")  # 123.500.000 + 8.645.000
```

Nota sobre la API: `LiquidationItem` (`app/engine/liquidation/models.py`) no expone `.event_type`/`.amount`
directamente — el tipo de evento vive en `item.balance.event_type` (`RunningBalance`, ya usado así en
`test_liquida_sin_mora_si_se_pago_el_mismo_dia_de_terminacion`, línea ~791 de este mismo archivo) y el
monto se verifica agregado vía `resultado.final_balance().principal`, igual que
`test_genera_evento_de_costas_si_costas_pct_manual_esta_seteado` (línea ~712).

- [ ] **Step 2: Correr y verificar que falla**

Run: `pytest tests/services/test_area_strategy.py -k civil_familia_genera_evento_de_costas -v`
Expected: FAIL (el saldo final no incluye el monto de costas — el atributo `event_type` en el assert de
`tipos_evento` no aparece)

- [ ] **Step 3: Implementar el wiring**

En `app/services/area_strategy.py`, dentro de `CivilFamiliaStrategy._eventos_de_obligacion` (línea 84),
justo antes del `return eventos` de la rama `PUNTUAL` (línea 102):

```python
            evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=obligacion.valor)
            if evento_costas is not None:
                eventos.append(evento_costas)
            return eventos
```

Nota: solo se cablea para obligaciones `PUNTUAL`, no `RECURRENTE` — las costas se fijan una vez por
proceso, no por cuota individual de una obligación de tracto sucesivo (ver Task 12 del plan / spec,
sección "Fuera de alcance").

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/services/test_area_strategy.py -v`
Expected: todos pasan

- [ ] **Step 5: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat: wire costas procesales into CivilFamiliaStrategy"
```

---

## Task 13: Wiring en `ComercialStrategy`

**Files:**
- Modify: `app/services/area_strategy.py`
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir el test**

Buscar `_obligacion_comercial` (línea 355) y agregar:

```python
def test_comercial_genera_evento_de_costas_si_esta_configurado():
    # Mismo caso de referencia que Tasks 4/11/12/14: 123.500.000 en el punto
    # medio del tier menor cuantia de 2024 -> costas = 8.645.000,00.
    obligacion = _obligacion_comercial(valor=_Decimal("123500000.00"))
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.fecha_vencimiento = _date(2024, 7, 1)  # debe ser posterior a fecha_origen
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"

    resultado = ComercialStrategy().liquidar([obligacion], [], fecha_corte=obligacion.fecha_origen)
    tipos_evento = {item.balance.event_type for item in resultado.items}
    assert "COSTAS_PROCESALES" in tipos_evento
    assert resultado.final_balance().principal == _Decimal("132145000.00")  # 123.500.000 + 8.645.000
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `pytest tests/services/test_area_strategy.py -k comercial_genera_evento_de_costas -v`
Expected: FAIL

- [ ] **Step 3: Implementar el wiring**

En `ComercialStrategy._eventos_de_obligacion` (línea 263), dentro de la rama `PUNTUAL` (línea 265-272):

```python
        valor_pesos = self._valor_en_pesos(obligacion)
        if obligacion.tipo.value == "PUNTUAL":
            eventos = [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": valor_pesos, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]
            evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=valor_pesos)
            if evento_costas is not None:
                eventos.append(evento_costas)
            return eventos
```

(Reemplaza el `return [...]` de una sola expresión que existía antes por esta versión con la lista
intermedia `eventos`.)

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/services/test_area_strategy.py -v`
Expected: todos pasan

- [ ] **Step 5: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat: wire costas procesales into ComercialStrategy"
```

---

## Task 14: Wiring en `LaboralStrategy`

**Files:**
- Modify: `app/services/area_strategy.py`
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir el test**

Buscar `_obligacion_laboral` (línea 758) y agregar:

```python
def test_laboral_genera_evento_de_costas_si_esta_configurado():
    # _obligacion_laboral no acepta 'valor' como parametro (usa 'salario'), y
    # LaboralStrategy genera varios eventos ademas de costas (cesantias,
    # prima, vacaciones) -- final_balance().principal mezclaria todo. Se aisla
    # el monto de costas comparando el capital_base acumulado justo antes y
    # justo despues del item de costas, en vez de sumar todo el saldo.
    obligacion = _obligacion_laboral(
        salario=_Decimal("123500000.00"), fecha_inicio=_date(2024, 1, 1), fecha_fin=_date(2024, 6, 1),
    )
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"

    resultado = LaboralStrategy().liquidar([obligacion], [], fecha_corte=obligacion.fecha_fin)

    tipos_evento = [item.balance.event_type for item in resultado.items]
    assert "COSTAS_PROCESALES" in tipos_evento
    indice_costas = tipos_evento.index("COSTAS_PROCESALES")
    capital_previo = (
        resultado.items[indice_costas - 1].capital_base if indice_costas > 0 else _Decimal("0.00")
    )
    monto_costas = resultado.items[indice_costas].capital_base - capital_previo
    # fecha_origen (= fecha_inicio) 2024-01-01 -> SMLMV 2024 -> mismo caso de
    # referencia que Tasks 4/11/12/13: 123.500.000 -> costas = 8.645.000,00.
    assert monto_costas == _Decimal("8645000.00")
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `pytest tests/services/test_area_strategy.py -k laboral_genera_evento_de_costas -v`
Expected: FAIL

- [ ] **Step 3: Implementar el wiring**

En `LaboralStrategy.liquidar` (línea 342), justo después del bloque que genera `eventos` con
`LaborScheduler` (línea 354-360, después de `monto_prestaciones = sum(...)`):

```python
        evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=obligacion.valor)
        if evento_costas is not None:
            eventos.append(evento_costas)
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/services/test_area_strategy.py -v`
Expected: todos pasan

- [ ] **Step 5: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat: wire costas procesales into LaboralStrategy"
```

---

## Task 15: Wiring en `SancionatorioStrategy`

**Files:**
- Modify: `app/services/area_strategy.py`
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir el test**

Buscar `_obligacion_sancionatoria` (línea 583) y agregar:

```python
def test_sancionatorio_genera_evento_de_costas_si_esta_configurado():
    # cantidad_smlmv_uvt=1000 con el fecha_origen por defecto del fixture
    # (2019-06-01, pre-2020 -> usa SMLMV, no UVT): monto_pesos = 1000 *
    # 828116.00 = 828.116.000,00 -- muy por encima de 150 SMLMV(2019) =
    # 124.217.400,00, cae en el tier "mayor cuantia" (sin techo), que siempre
    # usa el porcentaje minimo del rango (3%) sin necesidad de interpolar.
    # costas = 828.116.000 * 3% = 24.843.480,00, pero el tope de 20 SMLMV(2019)
    # = 16.562.320,00 es menor -> se aplica el tope. Este caso ademas ejercita
    # el tope de la Task 4 con un ejemplo end-to-end real.
    obligacion = _obligacion_sancionatoria(cantidad_smlmv_uvt=_Decimal("1000"))
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"

    resultado = SancionatorioStrategy().liquidar([obligacion], [], fecha_corte=obligacion.fecha_origen)
    tipos_evento = {item.balance.event_type for item in resultado.items}
    assert "COSTAS_PROCESALES" in tipos_evento
    assert resultado.final_balance().principal == _Decimal("844678320.00")  # 828.116.000 + 16.562.320
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `pytest tests/services/test_area_strategy.py -k sancionatorio_genera_evento_de_costas -v`
Expected: FAIL

- [ ] **Step 3: Implementar el wiring**

En `SancionatorioStrategy._evento_de_obligacion` (línea 563), cambiar la firma y el cuerpo para devolver
una lista en vez de un solo `Event`, y actualizar el `liquidar` que la llama:

```python
    def _eventos_de_obligacion(self, obligacion) -> List[Event]:
        monto_pesos = resolver_base_sancion(obligacion.fecha_origen, obligacion.cantidad_smlmv_uvt)
        eventos = [
            Event(
                date=obligacion.fecha_origen,
                payload={"amount": monto_pesos, "label": obligacion.concepto},
                event_type=obligacion.categoria,
            )
        ]
        evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=monto_pesos)
        if evento_costas is not None:
            eventos.append(evento_costas)
        return eventos
```

Y en `liquidar` (línea 534), cambiar:

```python
        eventos_causacion = [self._evento_de_obligacion(obligacion) for obligacion in obligaciones]
```

por:

```python
        eventos_causacion = []
        for obligacion in obligaciones:
            eventos_causacion.extend(self._eventos_de_obligacion(obligacion))
```

(Renombra el método de `_evento_de_obligacion` — singular — a `_eventos_de_obligacion` — plural — porque
ahora puede devolver más de un evento; actualizar también cualquier otra referencia al nombre viejo dentro
de la clase.)

- [ ] **Step 4: Correr y verificar que pasan**

Run: `pytest tests/services/test_area_strategy.py -v`
Expected: todos pasan

- [ ] **Step 5: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat: wire costas procesales into SancionatorioStrategy"
```

---

## Task 16: Documentación de cierre

**Files:**
- Modify: `Preguntas-Para-Abogado.md` (sección "Sprint 18", líneas 340-361)
- Modify: `Pendientes.md` (sección "Sprint 18", líneas 1367-1425)
- Modify: `README.md`
- Modify: `docs/GUIA_USUARIO.md`

- [ ] **Step 1: Actualizar `Preguntas-Para-Abogado.md`**

Reemplazar el contenido completo de la sección "## Sprint 18 — Costas judiciales (tabla de rangos)"
(líneas 340-361) por:

```markdown
## Sprint 18 — Costas judiciales (tabla de rangos)

**Contexto:** La pregunta original de esta sección (conseguir la tabla real de rangos) ya no aplica: se
encontró y verificó el texto oficial completo del Acuerdo PSAA16-10554 (2016) del Consejo Superior de la
Judicatura directamente en `ramajudicial.gov.co` — el PDF de requisitos de BASTIUM citaba
"PCSJA20-11556", que no existe. La tabla completa (18 tipos de proceso) ya está implementada en
`app/engine/costs/agencias_en_derecho.py`.

Quedan 3 aproximaciones técnicas hechas durante la implementación que sí valdría la pena confirmar con el
despacho:

**Pregunta 1:** La "ponderación inversa" del Parágrafo 3° art. 3° (a mayor valor, menor porcentaje dentro
del rango) se implementó como interpolación lineal automática, con la opción de que quien liquida
sobreescriba el resultado manualmente. ¿Es una aproximación razonable para uso interno, o el despacho
prefiere que el sistema no proponga automáticamente ningún porcentaje y siempre exija el valor manual del
auto judicial real?

**Pregunta 2:** Para el tier de "mayor cuantía" (más de 150 SMLMV, sin techo definido por la ley), el
sistema siempre usa el porcentaje mínimo del rango de esa categoría (no hay una cuantía "techo" contra la
cual interpolar). ¿Les parece razonable, o prefieren otro criterio para cuantías muy grandes?

**Pregunta 3:** El sistema usa la fecha del hecho generador de la obligación (`fecha_origen`) como
aproximación de la "fecha de radicación de la demanda" (que es la fecha que exige el CGP art. 25 para fijar
el SMLMV de referencia de los umbrales de cuantía). En la mayoría de los casos ambas fechas coinciden o
están muy cerca, pero no siempre. ¿Es una aproximación aceptable?

**Respuesta del despacho:**


**Fecha:**

---
```

- [ ] **Step 2: Actualizar `Pendientes.md`**

En la línea 88 del índice, cambiar:
```
- [Sprint 18 — Costas judiciales con tabla real de rangos (Acuerdo PCSJA20-11556)](#sprint-18--costas-judiciales-con-tabla-real-de-rangos-acuerdo-pcsja20-11556)
```
por:
```
- [Sprint 18 — Costas judiciales con tabla real de rangos (Acuerdo PSAA16-10554) ✅ Completado](#sprint-18--costas-judiciales-con-tabla-real-de-rangos-acuerdo-psaa16-10554--completado)
```

En el encabezado de la sección (línea 1367), cambiar:
```
## Sprint 18 — Costas judiciales con tabla real de rangos (Acuerdo PCSJA20-11556)
```
por:
```
## Sprint 18 — Costas judiciales con tabla real de rangos (Acuerdo PSAA16-10554) ✅ Completado
```

Al final de la sección (antes del separador `---` de la línea 1425), agregar un párrafo **Estado:** con el
mismo formato que los sprints anteriores ya cerrados (ver Sprint 17 como referencia, línea ~cercana): fecha
de implementación, corrección del número de acuerdo (PCSJA20-11556 → PSAA16-10554), mención de los 18 tipos
de proceso, las 5 áreas cableadas (Tributario excluido), y referencia a
`docs/superpowers/specs/2026-07-26-sprint18-costas-judiciales-design.md` y
`docs/superpowers/plans/2026-07-26-sprint18-costas-judiciales.md`.

- [ ] **Step 3: Actualizar `README.md` y `docs/GUIA_USUARIO.md`**

Buscar las menciones de costas judiciales / "🚧 no todavía" relacionadas con este sprint en ambos
documentos (`grep -n "costas" README.md docs/GUIA_USUARIO.md`) y describir cómo usarlo — capturar
`costas_tipo_proceso`/`costas_instancia` en el formulario de obligación para cálculo automático, o
`costas_pct_manual` para un valor fijado directamente por el juez — siguiendo el mismo formato ya usado
para describir Civil/Familia y los demás módulos ya cerrados.

- [ ] **Step 4: Commit**

```bash
git add Preguntas-Para-Abogado.md Pendientes.md README.md docs/GUIA_USUARIO.md
git commit -m "docs: close Sprint 18 (costas judiciales) in Pendientes.md"
```

---

## Task 17: Verificación final

**Files:** Ninguno nuevo — solo verificación.

- [ ] **Step 1: Correr la suite completa**

Run: `pytest`
Expected: todos los tests pasan (los ~367+ preexistentes más los nuevos de este sprint: ~45 en
`tests/engine/costs/test_agencias_en_derecho.py`, 2 en `tests/database/test_migrate_costas_tipo_proceso.py`,
~9 en `tests/services/test_area_strategy.py`)

- [ ] **Step 2: Confirmar que la migración ya corrió contra `bastium.db`**

Run: `python scripts/migrate_costas_tipo_proceso.py`
Expected: `Las columnas costas_tipo_proceso/costas_instancia ya existian, no se hizo nada.` (ya se corrió en
el Task 10)

- [ ] **Step 3: Commit final si queda algo pendiente de staging**

```bash
git status
```

Si hay cambios sin commitear (no debería, cada task ya commiteó lo suyo), revisar con `git diff` antes de
decidir si van en un commit adicional.

---

## Self-Review (completado antes de entregar el plan)

**1. Cobertura de la spec:** los 18 tipos de proceso del art. 5° están cubiertos (Tasks 1, 5-9); los
umbrales CGP art. 25 (Task 2); la interpolación/ponderación inversa (Task 3); el tope de 20 SMLMV (Task 4,
test dedicado); los campos nuevos + migración (Task 10); el wiring en las 5 áreas de litigio, no Tributario
(Tasks 11-15); la actualización de `Preguntas-Para-Abogado.md`/`Pendientes.md`/docs (Task 16). Los dos
puntos de "Fuera de alcance" de la spec (condena en costas parcial, valoración favorable violencia de
género) no tienen tarea — correcto, están explícitamente fuera.

**2. Placeholders:** ninguno — cada paso trae código completo, valores numéricos reales verificados contra
el texto del acuerdo, y comandos exactos.

**3. Consistencia de tipos:** `calcular_agencias_en_derecho` (Task 4) es la única función pública nueva del
motor y su firma se usa igual en el Task 11 (`_evento_costas_procesales`) y en los tests de las Tasks
12-15. `TipoProceso`/`Instancia` se instancian desde string (`TipoProceso(obligacion.costas_tipo_proceso)`)
consistentemente — los valores de enum (`"declarativo_general"`, `"primera"`, etc.) coinciden entre el
Task 1 (definición) y las Tasks 11-15 (uso en tests, asignando el string directamente al campo del
modelo).
