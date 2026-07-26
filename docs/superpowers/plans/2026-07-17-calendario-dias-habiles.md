# Sprint 6 — Calendario de días hábiles judiciales y términos procesales — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extender `CalendarUtils` con cómputo de días hábiles judiciales (festivos colombianos vía la
librería `holidays`), notificación digital y vencimiento de plazos de meses/años; y construir un modelador
de términos procesales puro (`EstadoTermino` + interrupción/suspensión/reanudación) en
`app/engine/temporal/terminos.py`.

**Architecture:** Dos módulos. `app/engine/time/calendar.py` gana cinco métodos estáticos nuevos sobre
`CalendarUtils` (aritmética pura de fechas, sin estado). `app/engine/temporal/terminos.py` es nuevo:
un dataclass inmutable `EstadoTermino` más cinco funciones puras que reciben un estado y devuelven uno
nuevo, reutilizando `CalendarUtils.dias_habiles_entre` para el cómputo de días transcurridos.

**Tech Stack:** Python 3.14, `holidays` (nueva dependencia, festivos Colombia con Ley Emiliani), pytest.

**Referencia de diseño:** `docs/superpowers/specs/2026-07-17-calendario-dias-habiles-design.md` — leer
antes de ejecutar si algo en este plan no queda claro; ahí están las decisiones y su justificación.

---

## Contexto que el ejecutor necesita saber antes de empezar

- Todo el proyecto corre en un venv en `.venv/`. Usar `.venv/Scripts/python.exe -m pytest ...` (Windows) o
  activar el venv, no `python` del sistema.
- `pytest.ini` ya está configurado con `--import-mode=importlib` y `consider_namespace_packages = true`.
  No tocar esa configuración.
- **Regla de conteo de días crítica (confirmada con el usuario, ver spec decisión 4):** en
  `sumar_dias_habiles(fecha_inicio, n)` y `dias_habiles_entre(fecha_inicio, fecha_fin)`, `fecha_inicio`
  **nunca** cuenta como día 1, sea o no hábil. Solo cuentan los días hábiles estrictamente posteriores.
- Los valores esperados de fechas en los tests de este plan fueron verificados de forma independiente
  (script Python ejecutado fuera del código de producción, contando festivos reales de `holidays.CO` para
  2025/2026) — no son inventados. Si algún test falla, el bug está en la implementación, no en el valor
  esperado.
- Al cerrar el sprint (Task 11), `Pendientes.md` exige actualizar `docs/GUIA_USUARIO.md` — no lo saltes.

---

### Task 1: Agregar la dependencia `holidays`

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Agregar la línea al archivo**

Abrir `requirements.txt` y agregar una línea nueva (cualquier posición, se sugiere después de `pytest-qt`):

```
holidays
```

- [ ] **Step 2: Instalar en el venv del proyecto**

Run: `.venv/Scripts/python.exe -m pip install holidays`
Expected: `Successfully installed holidays-<version>` (o `Requirement already satisfied` si ya estaba).

- [ ] **Step 3: Verificar que importa y que Colombia trae festivos móviles correctos**

Run:
```
.venv/Scripts/python.exe -c "import holidays; d = holidays.CO(years=2026); print(len(d)); from datetime import date; print(date(2026,1,12) in d, date(2026,1,6) in d)"
```
Expected: imprime un número > 0, luego `True False` (Reyes Magos se observa el lunes 12 de enero de 2026,
no el martes 6 que es la fecha real del festivo — confirma que la Ley Emiliani está aplicada por la
librería).

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "build: add holidays dependency for Colombian judicial calendar"
```

---

### Task 2: `CalendarUtils.es_dia_habil`

**Files:**
- Modify: `app/engine/time/calendar.py`
- Test: `tests/temporal/test_calendar.py` (nuevo)

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/temporal/test_calendar.py`:

```python
from datetime import date

from app.engine.time.calendar import CalendarUtils


def test_es_dia_habil_fin_de_semana():
    assert CalendarUtils.es_dia_habil(date(2026, 1, 3)) is False  # sábado
    assert CalendarUtils.es_dia_habil(date(2026, 1, 4)) is False  # domingo


def test_es_dia_habil_dia_normal():
    assert CalendarUtils.es_dia_habil(date(2026, 1, 13)) is True  # martes normal


def test_es_dia_habil_festivo_fijo():
    assert CalendarUtils.es_dia_habil(date(2026, 1, 1)) is False  # Año Nuevo


def test_es_dia_habil_ley_emiliani():
    # Reyes Magos (6 de enero) se traslada por Ley Emiliani al lunes siguiente,
    # 12 de enero de 2026. La fecha real del festivo (martes 6) queda hábil;
    # la fecha observada (lunes 12) queda inhábil.
    assert CalendarUtils.es_dia_habil(date(2026, 1, 6)) is True
    assert CalendarUtils.es_dia_habil(date(2026, 1, 12)) is False
```

- [ ] **Step 2: Ejecutar y confirmar que falla**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_calendar.py -v`
Expected: `FAILED` — `AttributeError: type object 'CalendarUtils' has no attribute 'es_dia_habil'`.

- [ ] **Step 3: Implementar**

Reemplazar el contenido completo de `app/engine/time/calendar.py`:

```python
import calendar
from datetime import date
from functools import lru_cache

import holidays


class CalendarUtils:
    """
    Motor de resolución de anomalías temporales.
    Garantiza que el software nunca colapse por inconsistencias
    en el calendario gregoriano (años bisiestos, meses de 30/31 días)
    y provee el cómputo de días hábiles judiciales colombianos.
    """

    @staticmethod
    def safe_create_date(year: int, month: int, desired_day: int) -> date:
        # Extrae el último día real del mes en ese año específico
        _, last_real_day = calendar.monthrange(year, month)

        # Si el día deseado (ej. 31) excede el día real (ej. 28), se topa al día real.
        actual_day = min(desired_day, last_real_day)

        return date(year, month, actual_day)

    @staticmethod
    @lru_cache(maxsize=None)
    def _festivos_colombia(anio: int) -> frozenset:
        return frozenset(holidays.CO(years=anio).keys())

    @staticmethod
    def es_dia_habil(fecha: date) -> bool:
        if fecha.weekday() >= 5:  # 5=sábado, 6=domingo
            return False
        return fecha not in CalendarUtils._festivos_colombia(fecha.year)
```

- [ ] **Step 4: Ejecutar y confirmar que pasa**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_calendar.py -v`
Expected: 4 `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add app/engine/time/calendar.py tests/temporal/test_calendar.py
git commit -m "feat(time): add CalendarUtils.es_dia_habil with Colombian holidays"
```

---

### Task 3: `CalendarUtils.sumar_dias_habiles`

**Files:**
- Modify: `app/engine/time/calendar.py`
- Modify: `tests/temporal/test_calendar.py`

- [ ] **Step 1: Agregar el test que falla**

Agregar al final de `tests/temporal/test_calendar.py`:

```python
def test_sumar_dias_habiles_no_cuenta_fecha_inicio():
    # fecha_inicio es lunes hábil, sin festivos cerca. sumar 1 día hábil debe
    # devolver el martes, NUNCA el mismo lunes (fecha_inicio no cuenta como día 1).
    lunes = date(2026, 1, 13)
    assert CalendarUtils.sumar_dias_habiles(lunes, 1) == date(2026, 1, 14)


def test_sumar_dias_habiles_cruza_fin_de_semana_y_festivo():
    # Verificado independientemente: 10 días hábiles desde el lunes 2025-12-22
    # (sin contar ese día) caen en miércoles 2026-01-07, cruzando Navidad
    # (2025-12-25), un fin de semana (27-28 dic), Año Nuevo (2026-01-01) y
    # otro fin de semana (3-4 ene).
    inicio = date(2025, 12, 22)
    assert CalendarUtils.sumar_dias_habiles(inicio, 10) == date(2026, 1, 7)


def test_sumar_dias_habiles_rechaza_n_negativo():
    import pytest

    with pytest.raises(ValueError):
        CalendarUtils.sumar_dias_habiles(date(2026, 1, 13), -1)
```

- [ ] **Step 2: Ejecutar y confirmar que falla**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_calendar.py -v -k sumar_dias_habiles`
Expected: `FAILED` — `AttributeError: ... no attribute 'sumar_dias_habiles'`.

- [ ] **Step 3: Implementar**

Modificar el import en la parte superior de `app/engine/time/calendar.py` (agregar `timedelta`):

```python
from datetime import date, timedelta
```

Agregar el método al final de la clase `CalendarUtils`:

```python
    @staticmethod
    def sumar_dias_habiles(fecha_inicio: date, n: int) -> date:
        if n < 0:
            raise ValueError("sumar_dias_habiles no admite n negativo")

        fecha = fecha_inicio
        dias_contados = 0
        while dias_contados < n:
            fecha += timedelta(days=1)
            if CalendarUtils.es_dia_habil(fecha):
                dias_contados += 1
        return fecha
```

- [ ] **Step 4: Ejecutar y confirmar que pasa**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_calendar.py -v`
Expected: 7 `PASSED` (los 4 de Task 2 + los 3 nuevos).

- [ ] **Step 5: Commit**

```bash
git add app/engine/time/calendar.py tests/temporal/test_calendar.py
git commit -m "feat(time): add CalendarUtils.sumar_dias_habiles"
```

---

### Task 4: `CalendarUtils.dias_habiles_entre`

**Files:**
- Modify: `app/engine/time/calendar.py`
- Modify: `tests/temporal/test_calendar.py`

- [ ] **Step 1: Agregar el test que falla**

Agregar al final de `tests/temporal/test_calendar.py`:

```python
def test_dias_habiles_entre_no_cuenta_fecha_inicio():
    lunes = date(2026, 1, 13)
    martes = date(2026, 1, 14)
    assert CalendarUtils.dias_habiles_entre(lunes, martes) == 1
    assert CalendarUtils.dias_habiles_entre(lunes, lunes) == 0


def test_dias_habiles_entre_es_inverso_de_sumar_dias_habiles():
    inicio = date(2025, 12, 22)
    fin = CalendarUtils.sumar_dias_habiles(inicio, 10)
    assert CalendarUtils.dias_habiles_entre(inicio, fin) == 10


def test_dias_habiles_entre_rechaza_fin_anterior_a_inicio():
    import pytest

    with pytest.raises(ValueError):
        CalendarUtils.dias_habiles_entre(date(2026, 1, 14), date(2026, 1, 13))
```

- [ ] **Step 2: Ejecutar y confirmar que falla**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_calendar.py -v -k dias_habiles_entre`
Expected: `FAILED` — `AttributeError: ... no attribute 'dias_habiles_entre'`.

- [ ] **Step 3: Implementar**

Agregar el método al final de la clase `CalendarUtils`:

```python
    @staticmethod
    def dias_habiles_entre(fecha_inicio: date, fecha_fin: date) -> int:
        if fecha_fin < fecha_inicio:
            raise ValueError("fecha_fin no puede ser anterior a fecha_inicio")

        fecha = fecha_inicio
        dias = 0
        while fecha < fecha_fin:
            fecha += timedelta(days=1)
            if CalendarUtils.es_dia_habil(fecha):
                dias += 1
        return dias
```

- [ ] **Step 4: Ejecutar y confirmar que pasa**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_calendar.py -v`
Expected: 10 `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add app/engine/time/calendar.py tests/temporal/test_calendar.py
git commit -m "feat(time): add CalendarUtils.dias_habiles_entre"
```

---

### Task 5: `CalendarUtils.notificacion_surtida_el`

**Files:**
- Modify: `app/engine/time/calendar.py`
- Modify: `tests/temporal/test_calendar.py`

- [ ] **Step 1: Agregar el test que falla**

Agregar al final de `tests/temporal/test_calendar.py`:

```python
def test_notificacion_surtida_el_cruza_festivo():
    # Verificado independientemente: envío el miércoles 2025-12-24. El primer
    # día hábil siguiente es viernes 2025-12-26 (jueves 25 es Navidad); el
    # segundo es lunes 2025-12-29 (fin de semana 27-28 no cuenta).
    envio = date(2025, 12, 24)
    assert CalendarUtils.notificacion_surtida_el(envio) == date(2025, 12, 29)
```

- [ ] **Step 2: Ejecutar y confirmar que falla**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_calendar.py -v -k notificacion`
Expected: `FAILED` — `AttributeError: ... no attribute 'notificacion_surtida_el'`.

- [ ] **Step 3: Implementar**

Agregar el método al final de la clase `CalendarUtils`:

```python
    @staticmethod
    def notificacion_surtida_el(fecha_envio: date) -> date:
        # Regla pág. 4 del PDF: la notificación digital se entiende surtida
        # 2 días hábiles después del envío.
        return CalendarUtils.sumar_dias_habiles(fecha_envio, 2)
```

- [ ] **Step 4: Ejecutar y confirmar que pasa**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_calendar.py -v`
Expected: 11 `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add app/engine/time/calendar.py tests/temporal/test_calendar.py
git commit -m "feat(time): add CalendarUtils.notificacion_surtida_el"
```

---

### Task 6: `CalendarUtils.vencimiento_calendario`

**Files:**
- Modify: `app/engine/time/calendar.py`
- Modify: `tests/temporal/test_calendar.py`

- [ ] **Step 1: Agregar el test que falla**

Agregar al final de `tests/temporal/test_calendar.py`:

```python
def test_vencimiento_calendario_desborde_fin_de_mes():
    # 30 de enero + 1 mes: febrero de 2025 (no bisiesto) solo tiene 28 días.
    # El 28 de febrero de 2025 es viernes hábil, no requiere corrimiento.
    inicio = date(2025, 1, 30)
    assert CalendarUtils.vencimiento_calendario(inicio, 1) == date(2025, 2, 28)


def test_vencimiento_calendario_corre_a_dia_habil_por_fin_de_semana():
    # 28 de febrero de 2026 + 1 mes -> 28 de marzo de 2026, que es sábado.
    # Corre al siguiente hábil: domingo 29 también inhábil, lunes 30 sí.
    inicio = date(2026, 2, 28)
    assert CalendarUtils.vencimiento_calendario(inicio, 1) == date(2026, 3, 30)


def test_vencimiento_calendario_corre_a_dia_habil_por_festivo():
    # 1 de abril de 2026 + 1 mes -> 1 de mayo de 2026 (Día del Trabajo,
    # viernes, festivo). Corre al siguiente hábil: fin de semana 2-3 mayo
    # inhábil, lunes 4 de mayo sí.
    inicio = date(2026, 4, 1)
    assert CalendarUtils.vencimiento_calendario(inicio, 1) == date(2026, 5, 4)


def test_vencimiento_calendario_rechaza_meses_menor_a_uno():
    import pytest

    with pytest.raises(ValueError):
        CalendarUtils.vencimiento_calendario(date(2026, 1, 1), 0)
```

- [ ] **Step 2: Ejecutar y confirmar que falla**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_calendar.py -v -k vencimiento_calendario`
Expected: `FAILED` — `AttributeError: ... no attribute 'vencimiento_calendario'`.

- [ ] **Step 3: Implementar**

Agregar el método al final de la clase `CalendarUtils`:

```python
    @staticmethod
    def vencimiento_calendario(fecha_inicio: date, meses: int) -> date:
        if meses < 1:
            raise ValueError("meses debe ser al menos 1")

        total_meses = fecha_inicio.month - 1 + meses
        anio_destino = fecha_inicio.year + total_meses // 12
        mes_destino = total_meses % 12 + 1

        fecha_objetivo = CalendarUtils.safe_create_date(
            anio_destino, mes_destino, fecha_inicio.day
        )

        while not CalendarUtils.es_dia_habil(fecha_objetivo):
            fecha_objetivo += timedelta(days=1)

        return fecha_objetivo
```

Nota para años: llamar con `meses=12 * n_anios` (ej. 3 años = `meses=36`).

- [ ] **Step 4: Ejecutar y confirmar que pasa**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_calendar.py -v`
Expected: 15 `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add app/engine/time/calendar.py tests/temporal/test_calendar.py
git commit -m "feat(time): add CalendarUtils.vencimiento_calendario"
```

---

### Task 7: `EstadoTermino` + `iniciar_termino` + `dias_restantes` + `esta_vencido`

**Files:**
- Create: `app/engine/temporal/terminos.py`
- Test: `tests/temporal/test_terminos.py` (nuevo)

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/temporal/test_terminos.py`:

```python
from datetime import date

from app.engine.temporal.terminos import (
    EstadoTermino,
    iniciar_termino,
    dias_restantes,
    esta_vencido,
)


def test_iniciar_termino_construye_estado_base():
    estado = iniciar_termino(date(2025, 12, 22), 10)
    assert estado == EstadoTermino(
        dias_totales=10,
        dias_consumidos=0,
        checkpoint=date(2025, 12, 22),
        suspendido=False,
    )


def test_iniciar_termino_rechaza_dias_totales_menor_a_uno():
    import pytest

    with pytest.raises(ValueError):
        iniciar_termino(date(2025, 12, 22), 0)


def test_dias_restantes_sin_modificadores():
    # Mismo escenario verificado en Task 3: 10 días hábiles desde
    # 2025-12-22 caen exactamente en 2026-01-07.
    estado = iniciar_termino(date(2025, 12, 22), 10)
    assert dias_restantes(estado, date(2026, 1, 6)) == 1
    assert dias_restantes(estado, date(2026, 1, 7)) == 0


def test_esta_vencido_sin_modificadores():
    estado = iniciar_termino(date(2025, 12, 22), 10)
    assert esta_vencido(estado, date(2026, 1, 6)) is False
    assert esta_vencido(estado, date(2026, 1, 7)) is True
```

- [ ] **Step 2: Ejecutar y confirmar que falla**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_terminos.py -v`
Expected: `FAILED` — `ModuleNotFoundError: No module named 'app.engine.temporal.terminos'`.

- [ ] **Step 3: Implementar**

Crear `app/engine/temporal/terminos.py`:

```python
"""
Modelador puro de términos procesales: representa el "reloj" de un plazo
judicial y sus 4 dinámicas de alteración de cómputo (PDF pág. 25):
interrupción (reset), suspensión (pausa), reanudación (resume) y expiración.

Cada función recibe un EstadoTermino y devuelve uno nuevo — ninguna muta el
estado que recibe. Ver docs/superpowers/specs/2026-07-17-calendario-dias-habiles-design.md
para el detalle de diseño.
"""

from dataclasses import dataclass, replace
from datetime import date

from app.engine.time.calendar import CalendarUtils


@dataclass(frozen=True)
class EstadoTermino:
    dias_totales: int
    dias_consumidos: int
    checkpoint: date
    suspendido: bool = False


def iniciar_termino(fecha_inicio: date, dias_totales: int) -> EstadoTermino:
    if dias_totales < 1:
        raise ValueError("dias_totales debe ser al menos 1")

    return EstadoTermino(
        dias_totales=dias_totales,
        dias_consumidos=0,
        checkpoint=fecha_inicio,
        suspendido=False,
    )


def dias_restantes(estado: EstadoTermino, fecha_actual: date) -> int:
    if estado.suspendido:
        consumidos = estado.dias_consumidos
    else:
        consumidos = estado.dias_consumidos + CalendarUtils.dias_habiles_entre(
            estado.checkpoint, fecha_actual
        )
    return estado.dias_totales - consumidos


def esta_vencido(estado: EstadoTermino, fecha_actual: date) -> bool:
    return dias_restantes(estado, fecha_actual) <= 0
```

- [ ] **Step 4: Ejecutar y confirmar que pasa**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_terminos.py -v`
Expected: 4 `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add app/engine/temporal/terminos.py tests/temporal/test_terminos.py
git commit -m "feat(temporal): add EstadoTermino base state and dias_restantes/esta_vencido"
```

---

### Task 8: `interrumpir`

**Files:**
- Modify: `app/engine/temporal/terminos.py`
- Modify: `tests/temporal/test_terminos.py`

- [ ] **Step 1: Agregar el test que falla**

Agregar al import de `tests/temporal/test_terminos.py` (`interrumpir` a la lista) y al final del archivo:

```python
from app.engine.temporal.terminos import (
    EstadoTermino,
    iniciar_termino,
    dias_restantes,
    esta_vencido,
    interrumpir,
)


def test_interrumpir_resetea_el_conteo():
    estado = iniciar_termino(date(2025, 12, 22), 10)
    # Avanza 3 días hábiles (verificado en Task 3: Dec23, Dec24, Dec26).
    fecha_interrupcion = date(2025, 12, 26)

    nuevo_estado = interrumpir(estado, fecha_interrupcion)

    assert nuevo_estado == EstadoTermino(
        dias_totales=10,
        dias_consumidos=0,
        checkpoint=fecha_interrupcion,
        suspendido=False,
    )
    # El estado original no se muta.
    assert estado.checkpoint == date(2025, 12, 22)


def test_interrumpir_reinicia_el_plazo_completo():
    estado = iniciar_termino(date(2025, 12, 22), 10)
    nuevo_estado = interrumpir(estado, date(2025, 12, 26))

    assert dias_restantes(nuevo_estado, date(2025, 12, 26)) == 10
```

- [ ] **Step 2: Ejecutar y confirmar que falla**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_terminos.py -v -k interrumpir`
Expected: `FAILED` — `ImportError: cannot import name 'interrumpir'`.

- [ ] **Step 3: Implementar**

Agregar al final de `app/engine/temporal/terminos.py`:

```python
def interrumpir(estado: EstadoTermino, fecha: date) -> EstadoTermino:
    return EstadoTermino(
        dias_totales=estado.dias_totales,
        dias_consumidos=0,
        checkpoint=fecha,
        suspendido=False,
    )
```

- [ ] **Step 4: Ejecutar y confirmar que pasa**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_terminos.py -v`
Expected: 6 `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add app/engine/temporal/terminos.py tests/temporal/test_terminos.py
git commit -m "feat(temporal): add interrumpir (reset) state transition"
```

---

### Task 9: `suspender`

**Files:**
- Modify: `app/engine/temporal/terminos.py`
- Modify: `tests/temporal/test_terminos.py`

- [ ] **Step 1: Agregar el test que falla**

Agregar `suspender` al import y al final del archivo:

```python
from app.engine.temporal.terminos import (
    EstadoTermino,
    iniciar_termino,
    dias_restantes,
    esta_vencido,
    interrumpir,
    suspender,
)


def test_suspender_congela_los_dias_consumidos():
    estado = iniciar_termino(date(2025, 12, 22), 10)
    # 3 días hábiles corridos hasta el 2025-12-26 (Dec23, Dec24, Dec26).
    suspendido = suspender(estado, date(2025, 12, 26))

    assert suspendido.suspendido is True
    assert suspendido.dias_consumidos == 3
    assert suspendido.checkpoint == date(2025, 12, 26)


def test_suspender_congela_dias_restantes_pase_el_tiempo_que_pase():
    estado = iniciar_termino(date(2025, 12, 22), 10)
    suspendido = suspender(estado, date(2025, 12, 26))

    # Aunque pasen muchos días hábiles más, mientras esté suspendido no cambia.
    assert dias_restantes(suspendido, date(2026, 3, 1)) == 7
    assert dias_restantes(suspendido, date(2026, 6, 1)) == 7


def test_suspender_rechaza_termino_ya_suspendido():
    import pytest

    estado = iniciar_termino(date(2025, 12, 22), 10)
    suspendido = suspender(estado, date(2025, 12, 26))

    with pytest.raises(ValueError):
        suspender(suspendido, date(2026, 1, 5))
```

- [ ] **Step 2: Ejecutar y confirmar que falla**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_terminos.py -v -k suspender`
Expected: `FAILED` — `ImportError: cannot import name 'suspender'`.

- [ ] **Step 3: Implementar**

Agregar al final de `app/engine/temporal/terminos.py`:

```python
def suspender(estado: EstadoTermino, fecha: date) -> EstadoTermino:
    if estado.suspendido:
        raise ValueError("el término ya está suspendido")

    dias_corridos = CalendarUtils.dias_habiles_entre(estado.checkpoint, fecha)
    return replace(
        estado,
        dias_consumidos=estado.dias_consumidos + dias_corridos,
        checkpoint=fecha,
        suspendido=True,
    )
```

- [ ] **Step 4: Ejecutar y confirmar que pasa**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_terminos.py -v`
Expected: 9 `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add app/engine/temporal/terminos.py tests/temporal/test_terminos.py
git commit -m "feat(temporal): add suspender (pause) state transition"
```

---

### Task 10: `reanudar`

**Files:**
- Modify: `app/engine/temporal/terminos.py`
- Modify: `tests/temporal/test_terminos.py`

- [ ] **Step 1: Agregar el test que falla**

Agregar `reanudar` al import y al final del archivo:

```python
from app.engine.temporal.terminos import (
    EstadoTermino,
    iniciar_termino,
    dias_restantes,
    esta_vencido,
    interrumpir,
    suspender,
    reanudar,
)


def test_reanudar_retoma_el_conteo_sin_perder_lo_congelado():
    estado = iniciar_termino(date(2025, 12, 22), 10)
    suspendido = suspender(estado, date(2025, 12, 26))  # 3 días congelados
    reanudado = reanudar(suspendido, date(2026, 1, 5))

    assert reanudado.suspendido is False
    assert reanudado.dias_consumidos == 3  # lo congelado no se toca
    assert reanudado.checkpoint == date(2026, 1, 5)

    # Desde el 2026-01-05, 2 días hábiles más son 2026-01-06 y 2026-01-07.
    assert dias_restantes(reanudado, date(2026, 1, 7)) == 10 - (3 + 2)


def test_reanudar_rechaza_termino_no_suspendido():
    import pytest

    estado = iniciar_termino(date(2025, 12, 22), 10)

    with pytest.raises(ValueError):
        reanudar(estado, date(2026, 1, 5))


def test_ciclo_completo_suspender_reanudar_hasta_vencer():
    # Verificado independientemente: reanudado con checkpoint 2026-01-05 y
    # 3 días ya congelados (de 10 totales) necesita 7 días hábiles más para
    # vencer. 7 días hábiles después de 2026-01-05 caen en 2026-01-15;
    # 6 días hábiles después caen en 2026-01-14 (un día antes de vencer).
    estado = iniciar_termino(date(2025, 12, 22), 10)
    suspendido = suspender(estado, date(2025, 12, 26))  # 3 congelados
    reanudado = reanudar(suspendido, date(2026, 1, 5))

    assert esta_vencido(reanudado, date(2026, 1, 14)) is False
    assert dias_restantes(reanudado, date(2026, 1, 14)) == 1
    assert esta_vencido(reanudado, date(2026, 1, 15)) is True
```

- [ ] **Step 2: Ejecutar y confirmar que falla**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_terminos.py -v -k reanudar`
Expected: `FAILED` — `ImportError: cannot import name 'reanudar'`.

- [ ] **Step 3: Implementar**

Agregar al final de `app/engine/temporal/terminos.py`:

```python
def reanudar(estado: EstadoTermino, fecha: date) -> EstadoTermino:
    if not estado.suspendido:
        raise ValueError("el término no está suspendido")

    return replace(estado, checkpoint=fecha, suspendido=False)
```

- [ ] **Step 4: Ejecutar y confirmar que pasa**

Run: `.venv/Scripts/python.exe -m pytest tests/temporal/test_terminos.py -v`
Expected: 12 `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add app/engine/temporal/terminos.py tests/temporal/test_terminos.py
git commit -m "feat(temporal): add reanudar (resume) state transition"
```

---

### Task 11: Actualizar `docs/GUIA_USUARIO.md`

**Files:**
- Modify: `docs/GUIA_USUARIO.md:369-370`

- [ ] **Step 1: Reemplazar el bullet de "pendiente" por el estado real**

En la sección "8. Funciones pendientes o en desarrollo", reemplazar:

```markdown
- 🚧 **Calendario de días hábiles** para contar plazos legales — hoy el programa no distingue días
  hábiles de festivos (`Pendientes.md`, Sprint 6).
```

por:

```markdown
- 🚧 **Calendario de días hábiles y términos procesales** — el motor ya existe y está probado
  (`CalendarUtils.es_dia_habil/sumar_dias_habiles/dias_habiles_entre/notificacion_surtida_el/
  vencimiento_calendario` en `app/engine/time/calendar.py`, y el modelador de términos con
  interrupción/suspensión/reanudación en `app/engine/temporal/terminos.py`), pero todavía no está
  conectado a ninguna pantalla — hoy sirve como base interna para el Sprint 7 de prescripción y
  caducidad (`Pendientes.md`, Sprint 6).
```

- [ ] **Step 2: Verificar visualmente el cambio**

Run: `grep -n "Calendario de días" "docs/GUIA_USUARIO.md"` (o abrir el archivo) y confirmar que el texto
nuevo aparece y ya no dice "el programa no distingue días hábiles de festivos".

- [ ] **Step 3: Commit**

```bash
git add docs/GUIA_USUARIO.md
git commit -m "docs: reflect Sprint 6 calendar engine status in user guide"
```

---

### Task 12: Verificación final de la suite completa

**Files:** ninguno (solo verificación)

- [ ] **Step 1: Correr toda la suite**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: todos los tests en verde (los ~81+ preexistentes más los ~25 nuevos de este sprint), 0 `failed`,
0 `error`.

- [ ] **Step 2: Si algo falla, diagnosticar antes de continuar**

No hay paso de "arreglar" genérico aquí — si algo falla, es una regresión real y hay que leer el traceback
completo, identificar la causa (ej. una colisión de nombres, un import circular entre
`app/engine/temporal/terminos.py` y `app/engine/time/calendar.py`) y corregirla en el archivo
correspondiente antes de dar el sprint por cerrado.

---

## Notas para quien ejecute esto

- No hay Task de "actualizar `README.md`" porque el README no menciona el calendario de días hábiles en
  ningún bullet específico (se verificó con `grep` antes de escribir este plan) — solo la lista genérica
  de `Pendientes.md`. Si al ejecutar este plan el README sí lo menciona explícitamente en algún punto,
  actualízalo igual que se hizo con `GUIA_USUARIO.md` en la Task 11.
- Este sprint no toca la GUI ni la base de datos a propósito (alcance excluido, ver spec). No agregues
  pantallas ni modelos SQLAlchemy — eso es de otro sprint futuro no asignado.
- El Sprint 7 (prescripción y caducidad) va a importar directamente `EstadoTermino` y las funciones de
  `app/engine/temporal/terminos.py` — no dupliques esta lógica al planificar ese sprint.
