# Sprint 7 — Motor de prescripción y caducidad — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un módulo de cálculo puro (`app/engine/temporal/prescripcion.py`) que resuelva
fechas límite de prescripción y caducidad por tipo de acción, soporte prescripción parcial cuota-a-cuota
en obligaciones de tracto sucesivo, y modele la interrupción del plazo por demanda notificada en tiempo.

**Architecture:** Módulo nuevo e independiente de `EstadoTermino` (Sprint 6) — no hay máquina de
estados que pausar/reanudar, solo fechas calendario. Se apoya en `CalendarUtils.vencimiento_calendario`
(ya existe, ya resuelve desborde de fin de mes y traslado a día hábil si el vencimiento cae en festivo).
Todas las funciones son puras (sin efectos secundarios, sin excepciones de dominio nuevas): reciben
fechas/enums, devuelven fechas o listas. Diseño completo en
`docs/superpowers/specs/2026-07-19-sprint7-prescripcion-caducidad-design.md`.

**Tech Stack:** Python puro, `datetime.date`, `enum.Enum`, pytest. Reutiliza `CalendarUtils` (Sprint 6)
y `Event`/`FamilyScheduler` (MVP) sin modificarlos.

---

### Task 1: `TipoAccion` + `calcular_prescripcion`

**Files:**
- Create: `app/engine/temporal/prescripcion.py`
- Test: `tests/temporal/test_prescripcion.py`

- [ ] **Step 1: Write the failing tests**

```python
from datetime import date

from app.engine.temporal.prescripcion import TipoAccion, calcular_prescripcion


def test_calcular_prescripcion_ejecutiva_5_anios():
    # 2020-03-15 + 60 meses -> raw 2025-03-15 (sábado, inhábil) -> corre al
    # siguiente hábil, 2025-03-17 (lunes).
    assert calcular_prescripcion(date(2020, 3, 15), TipoAccion.EJECUTIVA) == date(2025, 3, 17)


def test_calcular_prescripcion_ordinaria_10_anios():
    # 2016-06-20 + 120 meses -> raw 2026-06-20 (sábado, inhábil) -> corre al
    # siguiente hábil, 2026-06-22 (lunes).
    assert calcular_prescripcion(date(2016, 6, 20), TipoAccion.ORDINARIA) == date(2026, 6, 22)


def test_calcular_prescripcion_honorarios_profesionales_3_anios():
    # 2023-02-10 + 36 meses -> 2026-02-10, martes hábil, sin corrimiento.
    assert calcular_prescripcion(date(2023, 2, 10), TipoAccion.HONORARIOS_PROFESIONALES) == date(2026, 2, 10)


def test_calcular_prescripcion_cambiaria_directa_3_anios():
    # Art. 789 C.Co. 2023-05-05 + 36 meses -> 2026-05-05, martes hábil.
    assert calcular_prescripcion(date(2023, 5, 5), TipoAccion.CAMBIARIA_DIRECTA) == date(2026, 5, 5)


def test_calcular_prescripcion_cambiaria_regreso_tenedor_1_anio():
    # Art. 790 C.Co. 2025-03-01 + 12 meses -> raw 2026-03-01 (domingo, inhábil)
    # -> corre al siguiente hábil, 2026-03-02 (lunes).
    assert calcular_prescripcion(date(2025, 3, 1), TipoAccion.CAMBIARIA_REGRESO_TENEDOR) == date(2026, 3, 2)


def test_calcular_prescripcion_cambiaria_regreso_entre_obligados_6_meses():
    # Art. 791 C.Co. 2025-09-01 + 6 meses -> 2026-03-01, domingo inhábil ->
    # corre al siguiente hábil, 2026-03-02 (lunes).
    assert calcular_prescripcion(date(2025, 9, 1), TipoAccion.CAMBIARIA_REGRESO_ENTRE_OBLIGADOS) == date(2026, 3, 2)


def test_calcular_prescripcion_desborde_fin_de_mes():
    # 2025-08-31 + 6 meses -> mes destino es febrero de 2026 (28 días, no
    # bisiesto): topa a 2026-02-28 (sábado, inhábil) -> corre al siguiente
    # hábil, 2026-03-02 (lunes, ya que domingo 1 de marzo también es inhábil).
    assert calcular_prescripcion(
        date(2025, 8, 31), TipoAccion.CAMBIARIA_REGRESO_ENTRE_OBLIGADOS
    ) == date(2026, 3, 2)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/temporal/test_prescripcion.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.engine.temporal.prescripcion'`

- [ ] **Step 3: Write minimal implementation**

Create `app/engine/temporal/prescripcion.py`:

```python
"""
Motor de prescripcion y caducidad: calcula fechas limite a partir de una
fecha de origen y un tipo de accion/proceso, reutilizando
CalendarUtils.vencimiento_calendario (Sprint 6) para el computo calendario
(meses/anios, con topeo de fin de mes y corrimiento a dia habil).

Modulo independiente de EstadoTermino (Sprint 6): prescripcion/caducidad no
necesitan pausar/reanudar un reloj, solo una fecha limite calculada desde una
fecha de origen (ver docs/superpowers/specs/2026-07-19-sprint7-prescripcion-caducidad-design.md).
"""

from datetime import date
from enum import Enum

from app.engine.time.calendar import CalendarUtils


class TipoAccion(Enum):
    EJECUTIVA = "ejecutiva"
    ORDINARIA = "ordinaria"
    HONORARIOS_PROFESIONALES = "honorarios_profesionales"
    CAMBIARIA_DIRECTA = "cambiaria_directa"
    CAMBIARIA_REGRESO_TENEDOR = "cambiaria_regreso_tenedor"
    CAMBIARIA_REGRESO_ENTRE_OBLIGADOS = "cambiaria_regreso_entre_obligados"


PLAZOS_PRESCRIPCION_MESES = {
    TipoAccion.EJECUTIVA: 60,  # 5 anios (PDF pags. 16/19, 42, 43, 45)
    TipoAccion.ORDINARIA: 120,  # 10 anios (Art. 2536 C.C.)
    TipoAccion.HONORARIOS_PROFESIONALES: 36,  # 3 anios (PDF pag. 35)
    TipoAccion.CAMBIARIA_DIRECTA: 36,  # 3 anios (Art. 789 C.Co.)
    TipoAccion.CAMBIARIA_REGRESO_TENEDOR: 12,  # 1 anio (Art. 790 C.Co.)
    TipoAccion.CAMBIARIA_REGRESO_ENTRE_OBLIGADOS: 6,  # 6 meses (Art. 791 C.Co.)
}


def calcular_prescripcion(fecha_exigibilidad: date, tipo_accion: TipoAccion) -> date:
    meses = PLAZOS_PRESCRIPCION_MESES[tipo_accion]
    return CalendarUtils.vencimiento_calendario(fecha_exigibilidad, meses)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/temporal/test_prescripcion.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add app/engine/temporal/prescripcion.py tests/temporal/test_prescripcion.py
git commit -m "feat(temporal): add calcular_prescripcion with TipoAccion catalog"
```

---

### Task 2: `calcular_caducidad`

**Files:**
- Modify: `app/engine/temporal/prescripcion.py`
- Test: `tests/temporal/test_prescripcion.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/temporal/test_prescripcion.py`:

```python
import pytest

from app.engine.temporal.prescripcion import calcular_caducidad


def test_calcular_caducidad_tipo_conocido_impugnacion_societaria():
    # 2021-04-12 + 60 meses -> 2026-04-12, domingo inhábil -> corre al
    # siguiente hábil, 2026-04-13 (lunes).
    assert calcular_caducidad(
        date(2021, 4, 12), "IMPUGNACION_INEFICACIA_SOCIETARIA"
    ) == date(2026, 4, 13)


def test_calcular_caducidad_tipo_desconocido_con_plazo_manual():
    # 2025-01-15 + 8 meses -> 2025-09-15, lunes hábil.
    assert calcular_caducidad(
        date(2025, 1, 15), "TUTELA_INCIDENTE_DESACATO", plazo_meses_manual=8
    ) == date(2025, 9, 15)


def test_calcular_caducidad_tipo_desconocido_sin_plazo_manual_lanza_error():
    with pytest.raises(ValueError):
        calcular_caducidad(date(2025, 1, 15), "TUTELA_INCIDENTE_DESACATO")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/temporal/test_prescripcion.py -v`
Expected: 3 new FAIL with `ImportError: cannot import name 'calcular_caducidad'`

- [ ] **Step 3: Write minimal implementation**

Add a new import line right after `from enum import Enum` at the top of
`app/engine/temporal/prescripcion.py`:

```python
from typing import Optional
```

Append at the end of the file:

```python
PLAZOS_CADUCIDAD_MESES_CONOCIDOS = {
    # Impugnacion de ineficacia societaria, PDF pag. 40.
    "IMPUGNACION_INEFICACIA_SOCIETARIA": 60,
}


def calcular_caducidad(
    fecha_hecho: date,
    tipo_proceso: str,
    plazo_meses_manual: Optional[int] = None,
) -> date:
    if tipo_proceso in PLAZOS_CADUCIDAD_MESES_CONOCIDOS:
        meses = PLAZOS_CADUCIDAD_MESES_CONOCIDOS[tipo_proceso]
    elif plazo_meses_manual is not None:
        meses = plazo_meses_manual
    else:
        raise ValueError(
            f"No hay plazo de caducidad conocido para '{tipo_proceso}'; "
            "debe indicarse 'plazo_meses_manual' explicitamente."
        )
    return CalendarUtils.vencimiento_calendario(fecha_hecho, meses)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/temporal/test_prescripcion.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add app/engine/temporal/prescripcion.py tests/temporal/test_prescripcion.py
git commit -m "feat(temporal): add calcular_caducidad with known catalog + manual fallback"
```

---

### Task 3: `filtrar_cuotas_prescritas`

**Files:**
- Modify: `app/engine/temporal/prescripcion.py`
- Test: `tests/temporal/test_prescripcion.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/temporal/test_prescripcion.py`:

```python
from decimal import Decimal

from app.engine.temporal.schedulers.family import FamilyScheduler
from app.engine.temporal.prescripcion import filtrar_cuotas_prescritas


def test_filtrar_cuotas_prescritas_separa_viejas_de_recientes():
    scheduler = FamilyScheduler()
    scheduler.add_monthly_obligation(
        amount=Decimal("500000"),
        concept="Cuota alimentaria",
        due_day=1,
        category="CHILD_SUPPORT",
    )
    eventos = scheduler.generate(start=date(2015, 1, 1), end=date(2026, 1, 1))
    assert len(eventos) == 133  # 11 anios completos de cuotas mensuales

    fecha_corte = date(2026, 1, 1)
    vivas, prescritas = filtrar_cuotas_prescritas(eventos, fecha_corte, TipoAccion.EJECUTIVA)

    assert len(prescritas) == 72
    assert len(vivas) == 61
    assert len(vivas) + len(prescritas) == len(eventos)

    # Las prescritas son las causadas hace mas de 5 anios (hasta 2020-12-01
    # inclusive); las vivas arrancan en 2021-01-01.
    assert max(e.date for e in prescritas) == date(2020, 12, 1)
    assert min(e.date for e in vivas) == date(2021, 1, 1)


def test_filtrar_cuotas_prescritas_no_muta_la_lista_original():
    scheduler = FamilyScheduler()
    scheduler.add_monthly_obligation(
        amount=Decimal("500000"),
        concept="Cuota alimentaria",
        due_day=1,
        category="CHILD_SUPPORT",
    )
    eventos = scheduler.generate(start=date(2015, 1, 1), end=date(2016, 1, 1))
    total_original = len(eventos)

    filtrar_cuotas_prescritas(eventos, date(2026, 1, 1), TipoAccion.EJECUTIVA)

    assert len(eventos) == total_original
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/temporal/test_prescripcion.py -v`
Expected: 2 new FAIL with `ImportError: cannot import name 'filtrar_cuotas_prescritas'`

- [ ] **Step 3: Write minimal implementation**

Replace the `from typing import Optional` line (added in Task 2) at the top of
`app/engine/temporal/prescripcion.py` with:

```python
from typing import List, Optional, Tuple
```

Add a new import line right after `from app.engine.time.calendar import CalendarUtils`:

```python
from app.engine.temporal.schedulers.base import Event
```

Append at the end of the file:

```python
def filtrar_cuotas_prescritas(
    eventos: List[Event],
    fecha_corte: date,
    tipo_accion: TipoAccion = TipoAccion.EJECUTIVA,
) -> Tuple[List[Event], List[Event]]:
    vivas: List[Event] = []
    prescritas: List[Event] = []
    for evento in eventos:
        fecha_limite = calcular_prescripcion(evento.date, tipo_accion)
        if fecha_limite <= fecha_corte:
            prescritas.append(evento)
        else:
            vivas.append(evento)
    return vivas, prescritas
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/temporal/test_prescripcion.py -v`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add app/engine/temporal/prescripcion.py tests/temporal/test_prescripcion.py
git commit -m "feat(temporal): add filtrar_cuotas_prescritas for tracto sucesivo obligations"
```

---

### Task 4: `fecha_interrupcion_efectiva`

**Files:**
- Modify: `app/engine/temporal/prescripcion.py`
- Test: `tests/temporal/test_prescripcion.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/temporal/test_prescripcion.py`:

```python
from app.engine.temporal.prescripcion import fecha_interrupcion_efectiva


def test_fecha_interrupcion_efectiva_retrotrae_si_notifica_dentro_del_anio():
    # 214 dias entre radicacion y notificacion (<= 365) -> retrotrae a la radicacion.
    assert fecha_interrupcion_efectiva(
        date(2024, 3, 1), date(2024, 10, 1)
    ) == date(2024, 3, 1)


def test_fecha_interrupcion_efectiva_no_retrotrae_si_notifica_fuera_del_anio():
    # 457 dias entre radicacion y notificacion (> 365) -> no retrotrae.
    assert fecha_interrupcion_efectiva(
        date(2024, 3, 1), date(2025, 6, 1)
    ) == date(2025, 6, 1)


def test_fecha_interrupcion_efectiva_limite_exacto_365_dias_retrotrae():
    # 2024-03-01 -> 2025-03-01 es exactamente 365 dias (incluye el 29 de
    # febrero de 2024, bisiesto) -> retrotrae por el limite inclusivo <=.
    assert fecha_interrupcion_efectiva(
        date(2024, 3, 1), date(2025, 3, 1)
    ) == date(2024, 3, 1)


def test_fecha_interrupcion_efectiva_366_dias_no_retrotrae():
    # Un dia mas que el limite (366 dias) -> ya no retrotrae.
    assert fecha_interrupcion_efectiva(
        date(2024, 3, 1), date(2025, 3, 2)
    ) == date(2025, 3, 2)


def test_fecha_interrupcion_efectiva_rechaza_notificacion_anterior_a_radicacion():
    with pytest.raises(ValueError):
        fecha_interrupcion_efectiva(date(2024, 3, 1), date(2024, 1, 1))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/temporal/test_prescripcion.py -v`
Expected: 4 new FAIL with `ImportError: cannot import name 'fecha_interrupcion_efectiva'`

- [ ] **Step 3: Write minimal implementation**

Append to `app/engine/temporal/prescripcion.py`:

```python
def fecha_interrupcion_efectiva(fecha_radicacion: date, fecha_notificacion: date) -> date:
    if fecha_notificacion < fecha_radicacion:
        raise ValueError(
            f"fecha_notificacion ({fecha_notificacion}) no puede ser anterior a "
            f"fecha_radicacion ({fecha_radicacion})."
        )
    if (fecha_notificacion - fecha_radicacion).days <= 365:
        return fecha_radicacion
    return fecha_notificacion
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/temporal/test_prescripcion.py -v`
Expected: 16 passed

- [ ] **Step 5: Commit**

```bash
git add app/engine/temporal/prescripcion.py tests/temporal/test_prescripcion.py
git commit -m "feat(temporal): add fecha_interrupcion_efectiva for lawsuit interruption"
```

---

### Task 5: Verificación de suite completa y actualización de documentación

**Files:**
- Modify: `README.md:31-32`
- Modify: `docs/GUIA_USUARIO.md:573-574`
- Modify: `Pendientes.md:419` (encabezado del Sprint 7) y su bloque de cierre

- [ ] **Step 1: Correr la suite completa**

Run: `python -m pytest -q`
Expected: `274 passed, 1 skipped` (258 pasaban antes de este sprint + 16 tests nuevos de
`test_prescripcion.py`)

- [ ] **Step 2: Actualizar `README.md`**

En `README.md:31-32`, el texto actual dice:

```
🚧 **En desarrollo:** seguridad social (cotizaciones a pensión, salud, ARL, fondo de solidaridad
pensional) en el área Laboral, indexación por IPC, prescripción/caducidad, anatocismo comercial
condicionado (Art. 886 C.Co.) y varios módulos más también están pendientes. Las series históricas de
```

Reemplazar por:

```
🚧 **En desarrollo:** seguridad social (cotizaciones a pensión, salud, ARL, fondo de solidaridad
pensional) en el área Laboral, indexación por IPC, anatocismo comercial condicionado (Art. 886 C.Co.) y
varios módulos más también están pendientes. El motor de prescripción y caducidad
(`app/engine/temporal/prescripcion.py`) ya existe y está probado — calcula fechas límite por tipo de
acción (ejecutiva, ordinaria, honorarios profesionales, cambiaria directa/de regreso), soporta
prescripción parcial cuota a cuota en obligaciones de tracto sucesivo e interrupción por demanda — pero
todavía no está conectado a ninguna pantalla ni al motor de liquidación (`Pendientes.md`, Sprint 7). Las
series históricas de
```

- [ ] **Step 3: Actualizar `docs/GUIA_USUARIO.md`**

En `docs/GUIA_USUARIO.md:573-574`, el texto actual dice:

```
- 🚧 **Prescripción y caducidad** (saber si una deuda ya "venció" el plazo legal para cobrarla) — no
  existe ese cálculo todavía (`Pendientes.md`, Sprint 7).
```

Reemplazar por:

```
- 🚧 **Prescripción y caducidad** (saber si una deuda ya "venció" el plazo legal para cobrarla) — el
  motor de cálculo ya existe y está probado (`app/engine/temporal/prescripcion.py`: fechas límite por
  tipo de acción, prescripción parcial cuota a cuota para cuotas alimentarias, e interrupción por
  demanda), pero todavía no está conectado a ninguna pantalla ni bloquea la liquidación de un expediente
  (`Pendientes.md`, Sprint 7).
```

Y en `docs/GUIA_USUARIO.md:575-580`, el texto actual dice:

```
- 🚧 **Calendario de días hábiles y términos procesales** — el motor ya existe y está probado
  (`CalendarUtils.es_dia_habil/sumar_dias_habiles/dias_habiles_entre/notificacion_surtida_el/
  vencimiento_calendario` en `app/engine/time/calendar.py`, y el modelador de términos con
  interrupción/suspensión/reanudación en `app/engine/temporal/terminos.py`), pero todavía no está
  conectado a ninguna pantalla — hoy sirve como base interna para el Sprint 7 de prescripción y
  caducidad (`Pendientes.md`, Sprint 6).
```

Reemplazar la última línea (`conectado a ninguna pantalla...`) por:

```
  conectado a ninguna pantalla — hoy sirve como base interna para el motor de prescripción y caducidad
  del Sprint 7 (`Pendientes.md`, Sprint 6).
```

- [ ] **Step 4: Actualizar `Pendientes.md`**

En `Pendientes.md:419`, cambiar el encabezado:

```
## Sprint 7 — Motor de prescripción y caducidad 🔴 Pendiente
```

por:

```
## Sprint 7 — Motor de prescripción y caducidad ✅ Completado
```

Y agregar, inmediatamente antes de la sección `**Definición de Hecho:**` (después de la línea 459 con
"eso es un sprint de UI aparte una vez el motor exista y esté probado."), un bloque de cierre siguiendo
el mismo formato que los sprints anteriores:

```markdown
**Estado:** Implementado (2026-07-19) — ver
`docs/superpowers/plans/2026-07-19-sprint7-prescripcion-caducidad.md` y
`docs/superpowers/specs/2026-07-19-sprint7-prescripcion-caducidad-design.md`. El motor vive en
`app/engine/temporal/prescripcion.py`, independiente de `EstadoTermino` (Sprint 6) por decisión tomada
con el usuario: prescripción/caducidad son plazos calendario (años/meses), no de días hábiles, y no
necesitan pausar/reanudar un reloj — solo una fecha límite calculada desde
`CalendarUtils.vencimiento_calendario`. Decisiones tomadas con el usuario durante el brainstorming
previo (no asumidas unilateralmente):
- Los tres subtipos de prescripción cambiaria del PDF (pág. 32 y pág. 45) se modelan como tres valores
  distintos de `TipoAccion` (directa 3 años, de regreso del tenedor 1 año, entre obligados de regreso 6
  meses), reconciliando la mención de "6 meses" de la pág. 32 como el tercer supuesto real del C.Co.
  (art. 791) en vez de tratarla como un error aislado del documento.
- `calcular_caducidad` solo trae hardcodeado el único caso con plazo confirmado en el PDF (impugnación
  de ineficacia societaria, 5 años); cualquier otro `tipo_proceso` exige un `plazo_meses_manual`
  explícito o lanza `ValueError` — mismo patrón que `costas_pct_manual` del Sprint 4, para no inventar
  plazos sin fuente documental.
- No se agregaron excepciones de dominio (`ObligacionPrescritaError`/`DemandaCaducadaError`): el motor
  es cálculo puro, ya que este sprint excluye explícitamente la integración con la GUI y con
  `area_strategy.py`.

Pendiente explícito que quedó fuera de este sprint (documentado, no un olvido): la suspensión de
caducidad por conciliación extrajudicial (máximo 3 meses, PDF pág. 25) no se modela — no hay ningún caso
de uso en el sprint que la requiera todavía.
```

- [ ] **Step 5: Commit**

```bash
git add README.md docs/GUIA_USUARIO.md Pendientes.md
git commit -m "docs: mark Sprint 7 prescripcion/caducidad as completed"
```
