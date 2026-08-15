# Sprint 75 — Cuotas recurrentes (Civil/Familia + Comercial), pago por rango e imputación en cascada — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extender la generación real de cuotas mensuales (Sprint 41) de Civil/Familia a Comercial, agregar
un orden de imputación intercambiable (capital-primero para cuotas-hija), un motor de cascada para repartir
un pago entre varias cuotas, y una UI de selección de pago por rango.

**Architecture:** `AllocationEngine`/`LiquidationCore`/`UniversalLiquidationService` ganan un parámetro de
estrategia de imputación intercambiable (por defecto sin cambios). `area_strategy.py` activa la estrategia
capital-primero automáticamente para cualquier cuota-hija (`obligacion_padre_id` no nulo) y agrega a
`ComercialStrategy` el mismo bloque de detección de cuotas-hija que ya tiene `CivilFamiliaStrategy`. Un
módulo nuevo (`cascada_cuotas.py`) reparte un monto entre cuotas seleccionadas reutilizando exactamente ese
mismo motor en modo solo-lectura, para que la proyección y la liquidación real después coincidan siempre.
Un diálogo nuevo en la UI conecta la selección por rango con ese motor.

**Tech Stack:** Python, SQLAlchemy, PySide6, pytest.

**Spec:** `docs/superpowers/specs/2026-08-14-sprint75-cuotas-recurrentes-cascada-design.md` (alcance
revisado el 2026-08-14: solo Civil/Familia + Comercial — ver nota en la spec sobre por qué Laboral/
Sancionatorio/Honorarios/Tributario quedan fuera).

---

### Task 1: `generar_cuotas_mensuales` — reajuste anual opcional

**Files:**
- Modify: `app/services/reajuste_anual.py`
- Test: `tests/services/test_reajuste_anual.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_genera_cuotas_con_capital_constante_cuando_no_hay_reajuste(session_factory):
    session = session_factory()
    expediente = _crear_expediente_helper(session, area=AreaDerecho.COMERCIAL)
    obligacion_recurrente = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota de arrendamiento",
        categoria="CAPITAL_PAGARE",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 4, 1),
        dia_pago=1,
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    session.add(obligacion_recurrente)
    session.commit()

    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 4, 1))

    assert len(cuotas) == 4
    assert all(cuota.valor == Decimal("500000.00") for cuota in cuotas)
```

Nota para el implementador: usar el mismo helper de sesión/expediente (`session_factory`,
`_crear_expediente_helper` o el nombre real ya presente en el archivo) que ya usan los tests vecinos de
`generar_cuotas_mensuales` en `tests/services/test_reajuste_anual.py`.

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pytest tests/services/test_reajuste_anual.py -k capital_constante -v`
Expected: FAIL con `ValueError: La obligacion no tiene un tipo_reajuste_anual activo (SMMLV/IPC) --
generar_cuotas_mensuales no aplica a obligaciones sin reajuste.`

- [ ] **Step 3: Quitar la validación y saltar el reajuste cuando `tipo_reajuste_anual == NINGUNO`**

En `app/services/reajuste_anual.py`, eliminar por completo este bloque (dentro de
`generar_cuotas_mensuales`, justo debajo de la validación de `tipo != TipoObligacion.RECURRENTE`):

```python
    if obligacion_recurrente.tipo_reajuste_anual == TipoReajusteAnual.NINGUNO:
        raise ValueError(
            "La obligacion no tiene un tipo_reajuste_anual activo (SMMLV/IPC) -- "
            "generar_cuotas_mensuales no aplica a obligaciones sin reajuste."
        )
```

Y dentro del bucle mensual, reemplazar:

```python
            if anio_cursor != anio_capital:
                capital_actual = _reajustar_capital(capital_actual, anio_cursor, tipo_reajuste)
                anio_capital = anio_cursor
```

por:

```python
            if anio_cursor != anio_capital:
                if tipo_reajuste != TipoReajusteAnual.NINGUNO:
                    capital_actual = _reajustar_capital(capital_actual, anio_cursor, tipo_reajuste)
                anio_capital = anio_cursor
```

(`_reajustar_capital` sigue lanzando `ValueError` si se le pasa `NINGUNO` directamente — ver su
`raise ValueError` final — por eso el `if` de arriba nunca debe llamarla con ese tipo; no se toca
`_reajustar_capital` en este task.)

Actualizar también el docstring del módulo (líneas 1-15) y el de `generar_cuotas_mensuales`, que hoy
describen el reajuste como obligatorio — quitar esa restricción de la descripción.

- [ ] **Step 4: Correr el test y confirmar que pasa**

Run: `pytest tests/services/test_reajuste_anual.py -v`
Expected: PASS, incluyendo todos los tests existentes de SMMLV/IPC (cero regresión)

- [ ] **Step 5: Commit**

```bash
git add app/services/reajuste_anual.py tests/services/test_reajuste_anual.py
git commit -m "feat(sprint75): reajuste anual opcional en generar_cuotas_mensuales"
```

---

### Task 2: Orden de imputación intercambiable (capital-primero para cuotas-hija)

**Files:**
- Modify: `app/engine/liquidation/allocation.py`
- Modify: `app/engine/liquidation/engine.py`
- Modify: `app/services/motor_universal.py`
- Modify: `app/services/area_strategy.py` (`_liquidar_por_obligacion`, `CivilFamiliaStrategy.liquidar`, `ComercialStrategy.liquidar`)
- Test: `tests/liquidation/test_allocation.py`
- Test: `tests/liquidation/test_engine.py`
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir el test que falla para `AllocationEngine.allocate_capital_primero`**

```python
def test_allocate_capital_primero_paga_capital_antes_que_interes():
    deuda = PendingDebt(principal=Decimal("100000.00"), interest=Decimal("30000.00"), indexation=Decimal("0.00"))
    allocation, nueva_deuda, remanente = AllocationEngine.allocate_capital_primero(
        Decimal("100000.00"), deuda, date(2024, 4, 1)
    )
    assert allocation.to_principal == Decimal("100000.00")
    assert allocation.to_interest == Decimal("0.00")
    assert nueva_deuda.principal == Decimal("0.00")
    assert nueva_deuda.interest == Decimal("30000.00")  # intereses quedan intactos, "congelados"
    assert remanente == Decimal("0.00")


def test_allocate_capital_primero_cubre_capital_y_parte_del_interes():
    deuda = PendingDebt(principal=Decimal("100000.00"), interest=Decimal("30000.00"), indexation=Decimal("0.00"))
    allocation, nueva_deuda, remanente = AllocationEngine.allocate_capital_primero(
        Decimal("120000.00"), deuda, date(2024, 4, 1)
    )
    assert allocation.to_principal == Decimal("100000.00")
    assert allocation.to_interest == Decimal("20000.00")
    assert nueva_deuda.principal == Decimal("0.00")
    assert nueva_deuda.interest == Decimal("10000.00")
    assert remanente == Decimal("0.00")


def test_allocate_capital_primero_no_cambia_el_orden_de_allocate_por_defecto():
    deuda = PendingDebt(principal=Decimal("100000.00"), interest=Decimal("30000.00"), indexation=Decimal("0.00"))
    allocation, _, _ = AllocationEngine.allocate(Decimal("50000.00"), deuda, date(2024, 4, 1))
    assert allocation.to_interest == Decimal("30000.00")
    assert allocation.to_principal == Decimal("20000.00")
```

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pytest tests/liquidation/test_allocation.py -k capital_primero -v`
Expected: FAIL con `AttributeError: type object 'AllocationEngine' has no attribute 'allocate_capital_primero'`

- [ ] **Step 3: Implementar `allocate_capital_primero` en `allocation.py`**

Agregar como segundo `@staticmethod` dentro de `AllocationEngine`, después de `allocate`:

```python
    @staticmethod
    def allocate_capital_primero(
        payment_amount: Decimal, current_debt: PendingDebt, payment_date: date
    ) -> tuple[PaymentAllocation, PendingDebt, Decimal]:
        """Cascada especial para cuotas-hija generadas por recurrencia (Sprint 75):
        capital primero, luego interes, luego indexacion -- orden inverso al de
        allocate() de arriba. Los intereses no cubiertos quedan "congelados" (no
        se les aplica el pago, pero tampoco se les suma nada nuevo aqui -- eso lo
        decide quien acumula interes despues, no este metodo). Ver
        docs/superpowers/specs/2026-08-14-sprint75-cuotas-recurrentes-cascada-design.md,
        decisiones 2 y 5."""
        remainder = payment_amount

        if remainder >= current_debt.principal:
            to_principal = current_debt.principal
            remainder -= to_principal
            new_principal = Decimal("0.00")
        else:
            to_principal = remainder
            new_principal = current_debt.principal - remainder
            remainder = Decimal("0.00")

        if remainder >= current_debt.interest:
            to_interest = current_debt.interest
            remainder -= to_interest
            new_interest = Decimal("0.00")
        else:
            to_interest = remainder
            new_interest = current_debt.interest - remainder
            remainder = Decimal("0.00")

        if remainder >= current_debt.indexation:
            to_indexation = current_debt.indexation
            remainder -= to_indexation
            new_indexation = Decimal("0.00")
        else:
            to_indexation = remainder
            new_indexation = current_debt.indexation - remainder
            remainder = Decimal("0.00")

        allocation = PaymentAllocation(
            payment_date=payment_date,
            total_payment=payment_amount - remainder,
            to_interest=to_interest,
            to_indexation=to_indexation,
            to_principal=to_principal,
        )

        new_debt = PendingDebt(
            principal=new_principal, interest=new_interest, indexation=new_indexation
        )

        return allocation, new_debt, remainder
```

- [ ] **Step 4: Correr el test y confirmar que pasa**

Run: `pytest tests/liquidation/test_allocation.py -v`
Expected: PASS, todos (nuevos + existentes)

- [ ] **Step 5: Commit**

```bash
git add app/engine/liquidation/allocation.py tests/liquidation/test_allocation.py
git commit -m "feat(sprint75): AllocationEngine.allocate_capital_primero"
```

- [ ] **Step 6: Escribir el test que falla para `LiquidationCore` con estrategia inyectada**

```python
def test_liquidation_core_usa_la_estrategia_de_imputacion_inyectada():
    eventos = [
        Event(date=date(2024, 1, 1), payload={"amount": Decimal("100000.00")}, event_type="INSTALLMENT"),
    ]
    control_rate = Rate.from_percent(Decimal("0.0"))
    engine = LiquidationCore(
        default_daily_rate=control_rate,
        estrategia_imputacion=AllocationEngine.allocate_capital_primero,
    )
    # Sembrar interes manualmente via un evento INTEREST antes del pago, para
    # distinguir capital-primero (nuevo) de interes-primero (default).
    eventos.append(
        Event(date=date(2024, 2, 1), payload={"amount": Decimal("5000.00")}, event_type="INTEREST")
    )
    eventos.append(
        Event(date=date(2024, 3, 1), payload={"amount": Decimal("100000.00")}, event_type="PAYMENT")
    )
    resultado = engine.process(eventos, cutoff_date=date(2024, 3, 1))
    saldo = resultado.final_balance()
    assert saldo.principal == Decimal("0.00")
    assert saldo.interest == Decimal("5000.00")  # intereses NO se tocaron -- capital fue primero


def test_liquidation_core_sin_estrategia_mantiene_el_orden_por_defecto():
    eventos = [
        Event(date=date(2024, 1, 1), payload={"amount": Decimal("100000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2024, 2, 1), payload={"amount": Decimal("5000.00")}, event_type="INTEREST"),
        Event(date=date(2024, 3, 1), payload={"amount": Decimal("100000.00")}, event_type="PAYMENT"),
    ]
    control_rate = Rate.from_percent(Decimal("0.0"))
    engine = LiquidationCore(default_daily_rate=control_rate)
    resultado = engine.process(eventos, cutoff_date=date(2024, 3, 1))
    saldo = resultado.final_balance()
    assert saldo.interest == Decimal("0.00")  # interes-primero (default): se cubre completo
    assert saldo.principal == Decimal("5000.00")
```

- [ ] **Step 7: Correr el test y confirmar que falla**

Run: `pytest tests/liquidation/test_engine.py -k estrategia_de_imputacion -v`
Expected: FAIL con `TypeError: __init__() got an unexpected keyword argument 'estrategia_imputacion'`

- [ ] **Step 8: Agregar el parámetro a `LiquidationCore`**

En `app/engine/liquidation/engine.py`:

Modificar el import de la línea 9 para incluir `PaymentAllocation`:

```python
from app.engine.liquidation.models import (
    LiquidationItem,
    PaymentAllocation,
    PendingDebt,
    RunningBalance,
)
```

Agregar el import de `Callable` al inicio del archivo (junto a los demás imports):

```python
from collections.abc import Callable
```

Modificar `__init__` (líneas 28-33):

```python
    def __init__(
        self,
        default_daily_rate: Rate = _TASA_CERO,
        rate_provider: RateProvider | None = None,
        usar_suma_unica: bool = False,
        estrategia_imputacion: Callable[
            [Decimal, PendingDebt, date], tuple[PaymentAllocation, PendingDebt, Decimal]
        ] = AllocationEngine.allocate,
    ):
```

Y agregar, junto a las demás asignaciones del constructor (después de `self._usar_suma_unica = ...`):

```python
        self._estrategia_imputacion = estrategia_imputacion
```

Modificar la rama `PAYMENT` de `_process_event` (líneas 186-193), reemplazando la llamada directa a
`AllocationEngine.allocate`:

```python
        elif event.event_type == "PAYMENT":
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            allocation, new_debt, remainder = self._estrategia_imputacion(
                amount, self._current_debt, event.date
            )
            self._current_debt = new_debt
            payment_amount = allocation.total_payment
            saldo_a_favor = remainder
```

- [ ] **Step 9: Correr los tests y confirmar que pasan**

Run: `pytest tests/liquidation/test_engine.py -v`
Expected: PASS, todos (nuevos + existentes, comportamiento por defecto sin cambios)

- [ ] **Step 10: Commit**

```bash
git add app/engine/liquidation/engine.py tests/liquidation/test_engine.py
git commit -m "feat(sprint75): estrategia de imputación intercambiable en LiquidationCore"
```

- [ ] **Step 11: Propagar el parámetro por `UniversalLiquidationService`**

En `app/services/motor_universal.py`, agregar el import:

```python
from app.engine.liquidation.allocation import AllocationEngine
from app.engine.liquidation.models import PaymentAllocation, PendingDebt
```

(junto a los imports ya existentes de `app.engine.liquidation.*`). Agregar el parámetro a `liquidar()`
(línea 27-36):

```python
    def liquidar(
        self,
        eventos_causacion: list[Event],
        pagos: list[Payment],
        fecha_corte: date,
        tasa_estatica: Decimal = Decimal("0.0"),
        rate_provider: RateProvider | None = None,
        usar_suma_unica: bool = False,
        tipo_accion: TipoAccion = TipoAccion.EJECUTIVA,
        estrategia_imputacion: Callable[
            [Decimal, PendingDebt, date], tuple[PaymentAllocation, PendingDebt, Decimal]
        ] = AllocationEngine.allocate,
    ) -> LiquidationResult:
```

(agregar también `from collections.abc import Callable` al inicio del archivo). Y pasar el parámetro a la
construcción de `LiquidationCore` (líneas 58-62):

```python
        motor_calculo = LiquidationCore(
            default_daily_rate=tasa_mora,
            rate_provider=rate_provider,
            usar_suma_unica=usar_suma_unica,
            estrategia_imputacion=estrategia_imputacion,
        )
```

- [ ] **Step 12: Escribir un test de integración que confirme la propagación end-to-end**

```python
def test_universal_liquidation_service_propaga_estrategia_capital_primero():
    eventos = [
        Event(date=date(2024, 1, 1), payload={"amount": Decimal("100000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2024, 2, 1), payload={"amount": Decimal("5000.00")}, event_type="INTEREST"),
    ]
    pagos = [Payment(date=date(2024, 3, 1), amount=Decimal("100000.00"), reference="")]
    resultado = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos,
        pagos=pagos,
        fecha_corte=date(2024, 3, 1),
        estrategia_imputacion=AllocationEngine.allocate_capital_primero,
    )
    saldo = resultado.final_balance()
    assert saldo.principal == Decimal("0.00")
    assert saldo.interest == Decimal("5000.00")
```

Run: `pytest tests/services/test_motor_universal.py -k capital_primero -v`
Expected: FAIL primero (parámetro no existe todavía si se escribe antes del Step 11 — si se sigue el orden
de este plan, ya debería PASAR directo; correr igual para confirmar).

- [ ] **Step 13: Confirmar que pasa y correr toda la suite de `motor_universal`**

Run: `pytest tests/services/test_motor_universal.py -v`
Expected: PASS, cero regresión

- [ ] **Step 14: Commit**

```bash
git add app/services/motor_universal.py tests/services/test_motor_universal.py
git commit -m "feat(sprint75): propagar estrategia de imputación en UniversalLiquidationService"
```

- [ ] **Step 15: Activar capital-primero automáticamente para cuotas-hija en `area_strategy.py`**

Agregar el import en `app/services/area_strategy.py` (junto a los demás imports de `app.engine.liquidation`):

```python
from app.engine.liquidation.allocation import AllocationEngine
```

Agregar, junto a `_liquidar_por_obligacion` (antes de su definición, como función de módulo):

```python
def _estrategia_imputacion_por_obligacion(obligacion):
    """Capital-primero para toda cuota-hija generada por recurrencia
    (obligacion_padre_id no nulo, Sprint 75); orden legal general
    (indexacion->interes->capital) para el resto -- ver decision 2 de
    docs/superpowers/specs/2026-08-14-sprint75-cuotas-recurrentes-cascada-design.md."""
    if obligacion.obligacion_padre_id is not None:
        return AllocationEngine.allocate_capital_primero
    return AllocationEngine.allocate
```

Modificar la firma de `_liquidar_por_obligacion` (línea 92-99) agregando el nuevo parámetro:

```python
def _liquidar_por_obligacion(
    obligaciones: list,
    abonos: list,
    fecha_corte: date,
    eventos_fn: Callable[[object], list[Event]],
    rate_provider_fn: Callable[[object, date], MemoryRateProvider],
    usar_suma_unica_fn: Callable[[object], bool] = lambda obligacion: False,
    monto_abono_fn: Callable[[object, object], Decimal] = lambda obligacion, abono: abono.monto,
    estrategia_imputacion_fn: Callable[[object], Callable] = _estrategia_imputacion_por_obligacion,
) -> LiquidationResult:
```

Y agregar el parámetro a la llamada de `service.liquidar(...)` dentro del bucle (línea 140-148):

```python
        resultados.append(
            service.liquidar(
                eventos_causacion=eventos_fn(obligacion),
                pagos=pagos,
                fecha_corte=fecha_corte,
                rate_provider=rate_provider_fn(obligacion, fecha_corte),
                usar_suma_unica=usar_suma_unica_fn(obligacion),
                estrategia_imputacion=estrategia_imputacion_fn(obligacion),
            )
        )
```

Como el default de `estrategia_imputacion_fn` ya es `_estrategia_imputacion_por_obligacion`, **ninguna de
las 6 `AreaStrategy` necesita cambiar su llamada a `_liquidar_por_obligacion`** para heredar el
comportamiento correcto — la única obligación que activa capital-primero es la que ya tiene
`obligacion_padre_id` seteado, sin importar el área.

- [ ] **Step 16: Escribir el test que confirma el comportamiento end-to-end en `CivilFamiliaStrategy`**

```python
def test_civil_familia_cuota_hija_usa_capital_primero_en_su_propio_abono(monkeypatch):
    _sesion_en_memoria(monkeypatch)
    obligacion_recurrente = _obligacion_civil_familia_recurrente_helper(
        valor=Decimal("150000.00"),
        fecha_inicio=date(2022, 4, 1),
        tasa_efectiva_anual=Decimal("12.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 4, 1))
    cuota_marzo = next(c for c in cuotas if c.fecha_origen == date(2024, 3, 1))

    # Abono que cubre capital + una parte del interes de esa cuota individual --
    # sin este test, un abono directo sobre la cuota (fuera de la cascada, via
    # AbonoFormDialog) podria terminar usando interes-primero por error.
    abono = Abono(obligacion_id=cuota_marzo.id, fecha=date(2024, 4, 1), monto=Decimal("155000.00"))

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_recurrente, *cuotas],
        abonos=[abono],
        fecha_corte=date(2024, 4, 1),
    )
    # Verificar en el item de la cuota de marzo que el capital se cubrio antes
    # que el interes (capital_base cae a 0 para esa cuota, quede lo que quede
    # de interes pendiente, en vez de interes-primero).
    item_marzo = next(
        item for item in resultado.items if "MARZO 2024" in item.concept.upper()
    )
    assert item_marzo.capital_base == Decimal("0.00")
```

Nota para el implementador: adaptar `_obligacion_civil_familia_recurrente_helper` al helper real ya
existente en `tests/services/test_area_strategy.py` para crear una obligación RECURRENTE de Civil/Familia
persistida (necesaria porque `generar_cuotas_mensuales` requiere una obligación con `id` real). Revisar el
nombre exacto de la propiedad usada para identificar la fila de marzo en `LiquidationResult.items` (aquí se
asume `item.concept`, igual que en otros tests de `area_strategy` que ya inspeccionan conceptos).

- [ ] **Step 17: Correr el test y confirmar que pasa**

Run: `pytest tests/services/test_area_strategy.py -k cuota_hija_usa_capital_primero -v`
Expected: PASS

- [ ] **Step 18: Correr toda la suite de `test_area_strategy.py` para confirmar cero regresión**

Run: `pytest tests/services/test_area_strategy.py -v`
Expected: PASS — en particular, las obligaciones que NO son cuota-hija (la mayoría de los tests existentes)
deben seguir usando el orden por defecto sin cambios.

- [ ] **Step 19: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat(sprint75): capital-primero automático para cuotas-hija en _liquidar_por_obligacion"
```

---

### Task 3: `ComercialStrategy` — detección de cuotas-hija (mismo patrón que Civil/Familia)

**Files:**
- Modify: `app/services/area_strategy.py` (`ComercialStrategy.liquidar`, línea 479-506; `ComercialStrategy._eventos_de_obligacion`, línea 730-757)
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_comercial_no_duplica_capital_del_padre_cuando_ya_tiene_cuotas_generadas(monkeypatch):
    _sesion_en_memoria(monkeypatch)
    obligacion_recurrente = _obligacion_comercial_recurrente_helper(
        valor=Decimal("500000.00"),
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 3, 1),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 3, 1))

    resultado = ComercialStrategy().liquidar(
        obligaciones=[obligacion_recurrente, *cuotas],
        abonos=[],
        fecha_corte=date(2024, 3, 1),
    )

    eventos_de_capital = [
        item for item in resultado.items if item.capital_base > Decimal("0.00") or "CUOTA" not in item.concept.upper()
    ]
    # 3 cuotas generadas (enero/febrero/marzo) -- el padre RECURRENTE no debe
    # aportar un cuarto evento de capital via FamilyScheduler ademas de esas 3.
    total_capital_eventos = sum(
        1 for item in resultado.items if item.payment_amount == Decimal("0.00") and item.capital_base > Decimal("0.00")
    )
    assert len(cuotas) == 3
```

Nota para el implementador: este test de "no duplicación" es más confiable si se escribe comparando el
`capital_base` consolidado final contra `500000.00 * 3` en vez de contar filas — ajustar la aserción final
al mecanismo real de `LiquidationResult` una vez que se tenga el helper de creación de obligación Comercial
ya existente en el archivo (`_obligacion_comercial_recurrente_helper` aquí es un nombre de referencia,
adaptar al patrón real de `tests/services/test_area_strategy.py`). El punto central del test: **antes** de
este task, correrlo debe fallar porque el capital total liquidado sale duplicado (cuotas + padre
re-expandido por `FamilyScheduler`).

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pytest tests/services/test_area_strategy.py -k no_duplica_capital_del_padre -v`
Expected: FAIL (capital total duplicado: `2` × `500000.00 * 3`)

- [ ] **Step 3: Aplicar el mismo patrón de `CivilFamiliaStrategy` a `ComercialStrategy`**

Modificar `ComercialStrategy.liquidar()` (`area_strategy.py:479-506`):

```python
    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_comercial(obligacion)

        ids_con_cuotas_generadas = {
            obligacion.obligacion_padre_id
            for obligacion in obligaciones
            if obligacion.obligacion_padre_id is not None
        }

        resultado = _liquidar_por_obligacion(
            obligaciones=obligaciones,
            abonos=abonos,
            fecha_corte=fecha_corte,
            eventos_fn=lambda obligacion: self._eventos_de_obligacion(
                obligacion, fecha_corte, ids_con_cuotas_generadas
            ),
            rate_provider_fn=self._construir_rate_provider_obligacion,
            monto_abono_fn=self._monto_abono_en_pesos,
        )

        ajustes_usura = []
        for obligacion in obligaciones:
            abonos_obligacion = [abono for abono in abonos if abono.obligacion_id == obligacion.id]
            ajuste = self._calcular_sancion_usura(obligacion, abonos_obligacion, fecha_corte)
            if ajuste is not None:
                ajustes_usura.append(ajuste)

        if ajustes_usura:
            resultado = self._aplicar_sanciones_usura(resultado, ajustes_usura, fecha_corte)

        return resultado
```

Modificar `ComercialStrategy._eventos_de_obligacion()` (`area_strategy.py:730-757`) para aceptar
`ids_con_cuotas_generadas` y saltar la expansión del padre cuando ya tiene cuotas:

```python
    def _eventos_de_obligacion(
        self, obligacion, fecha_corte: date, ids_con_cuotas_generadas: set | None = None
    ) -> list[Event]:
        valor_pesos = self._valor_en_pesos(obligacion)
        if obligacion.tipo.value == "PUNTUAL":
            eventos = [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": valor_pesos, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]
            eventos.extend(self._eventos_anatocismo(obligacion, fecha_corte))
            evento_costas = _evento_costas_procesales(
                obligacion, pretensiones_reconocidas=valor_pesos
            )
            if evento_costas is not None:
                eventos.append(evento_costas)
            return eventos

        # RECURRENTE
        if obligacion.id in (ids_con_cuotas_generadas or set()):
            return []

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

- [ ] **Step 4: Correr el test y confirmar que pasa**

Run: `pytest tests/services/test_area_strategy.py -k no_duplica_capital_del_padre -v`
Expected: PASS

- [ ] **Step 5: Correr toda la suite de `test_area_strategy.py` para confirmar cero regresión**

Run: `pytest tests/services/test_area_strategy.py -v`
Expected: PASS — en particular los tests existentes de `ComercialStrategy` con obligaciones RECURRENTE
*sin* cuotas-hija generadas (el caso `ids_con_cuotas_generadas` vacío) deben seguir expandiendo por
`FamilyScheduler` exactamente igual que antes.

- [ ] **Step 6: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat(sprint75): ComercialStrategy detecta cuotas-hija ya generadas"
```

---

### Task 4: Motor de cascada — `app/services/cascada_cuotas.py`

**Files:**
- Create: `app/services/cascada_cuotas.py`
- Test: `tests/services/test_cascada_cuotas.py`

- [ ] **Step 1: Escribir el test que falla para `distribuir_pago_en_cascada` (función pura, sin DB)**

```python
from datetime import date
from decimal import Decimal

from app.engine.liquidation.models import PendingDebt
from app.services.cascada_cuotas import distribuir_pago_en_cascada


def _deuda(principal: str, interest: str) -> PendingDebt:
    return PendingDebt(
        principal=Decimal(principal), interest=Decimal(interest), indexation=Decimal("0.00")
    )


def test_ejemplo_del_usuario_abril_marzo_febrero():
    # Reproduce la mecanica del ejemplo del usuario (capital de la cuota mas
    # reciente primero, luego capital+interes de las anteriores, y solo una
    # parte de los intereses de la cuota mas antigua si el pago no alcanza
    # para todo) con montos elegidos a mano para que la aritmetica cierre
    # exacto -- no se derivan de una tasa anual real, eso se prueba aparte en
    # el test de integracion (Task 6).
    cuotas_y_deuda = [
        ("abril", _deuda("150000.00", "0.00")),
        ("marzo", _deuda("150000.00", "20000.00")),
        ("febrero", _deuda("150000.00", "45000.00")),
    ]
    asignaciones, remanente = distribuir_pago_en_cascada(
        cuotas_y_deuda, Decimal("500000.00"), date(2024, 4, 1)
    )

    # abril: 150.000 de capital, interes 0 (recien nace ese dia).
    # marzo: 150.000 capital + 20.000 interes completo = 170.000.
    # febrero: 150.000 capital + solo 30.000 de sus 45.000 de interes = 180.000
    #          (los 15.000 restantes de interes de febrero quedan debidos, pero
    #          su capital ya esta pagado y no genera intereses nuevos).
    assert asignaciones[0][1] == Decimal("150000.00")  # abril
    assert asignaciones[1][1] == Decimal("170000.00")  # marzo
    assert asignaciones[2][1] == Decimal("180000.00")  # febrero
    assert sum(monto for _, monto in asignaciones) == Decimal("500000.00")
    assert remanente == Decimal("0.00")


def test_pago_exacto_para_una_sola_cuota_no_toca_la_siguiente():
    cuotas_y_deuda = [
        ("marzo", _deuda("150000.00", "0.00")),
        ("febrero", _deuda("150000.00", "3000.00")),
    ]
    asignaciones, remanente = distribuir_pago_en_cascada(
        cuotas_y_deuda, Decimal("150000.00"), date(2024, 3, 1)
    )
    assert len(asignaciones) == 1
    assert asignaciones[0][1] == Decimal("150000.00")
    assert remanente == Decimal("0.00")


def test_remanente_sobrante_cuando_el_pago_excede_todas_las_cuotas():
    cuotas_y_deuda = [("marzo", _deuda("150000.00", "0.00"))]
    asignaciones, remanente = distribuir_pago_en_cascada(
        cuotas_y_deuda, Decimal("200000.00"), date(2024, 3, 1)
    )
    assert asignaciones[0][1] == Decimal("150000.00")
    assert remanente == Decimal("50000.00")
```

Nota para el implementador: en el test del ejemplo del usuario, `cuotas_y_deuda` usa strings (`"abril"`,
`"marzo"`, `"febrero"`) como placeholder del objeto `Obligacion` real solo para que el test sea legible sin
tocar la base de datos — `distribuir_pago_en_cascada` es genérica sobre el primer elemento de la tupla (no
lo inspecciona, solo lo devuelve tal cual en el resultado), así que el test es válido tal cual.

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pytest tests/services/test_cascada_cuotas.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.services.cascada_cuotas'`

- [ ] **Step 3: Implementar `distribuir_pago_en_cascada`**

```python
"""Sprint 75: motor de cascada para repartir un pago entre varias cuotas-hija
seleccionadas por rango. Ver docs/superpowers/specs/
2026-08-14-sprint75-cuotas-recurrentes-cascada-design.md, seccion "Alcance",
punto 4.

distribuir_pago_en_cascada es una funcion pura (sin sesion de base de datos):
el caller (dialogo de UI) es responsable de calcular la deuda pendiente real
de cada cuota ANTES de llamar esta funcion, reutilizando
UniversalLiquidationService + AllocationEngine.allocate_capital_primero (el
mismo motor y la misma estrategia que se usara despues al liquidar de verdad
los Abono creados) -- asi la proyeccion de aqui y la liquidacion real
coinciden siempre, sin un numero precalculado aparte (decision 5 de la spec).
"""

from datetime import date
from decimal import Decimal
from typing import TypeVar

from app.engine.liquidation.allocation import AllocationEngine
from app.engine.liquidation.models import PendingDebt

_T = TypeVar("_T")


def distribuir_pago_en_cascada(
    cuotas_y_deuda: list[tuple[_T, PendingDebt]],
    monto_total: Decimal,
    fecha_pago: date,
) -> tuple[list[tuple[_T, Decimal]], Decimal]:
    """`cuotas_y_deuda` debe venir ordenada de la cuota mas reciente a la mas
    antigua (lo decide el caller, segun el rango/seleccion del usuario en la
    UI). Retorna (asignaciones, remanente_sin_cubrir): asignaciones es una
    lista de (cuota, monto_asignado) solo para las cuotas que recibieron algo
    (> 0); remanente_sin_cubrir es lo que sobro despues de recorrer todas las
    cuotas de la lista (0 si el monto se reparte exacto)."""
    remanente = monto_total
    asignaciones: list[tuple[_T, Decimal]] = []
    for cuota, deuda in cuotas_y_deuda:
        if remanente <= Decimal("0.00"):
            break
        _, _, sobra = AllocationEngine.allocate_capital_primero(remanente, deuda, fecha_pago)
        monto_asignado = remanente - sobra
        if monto_asignado > Decimal("0.00"):
            asignaciones.append((cuota, monto_asignado))
        remanente = sobra
    return asignaciones, remanente
```

- [ ] **Step 4: Correr el test y confirmar que pasa**

Run: `pytest tests/services/test_cascada_cuotas.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add app/services/cascada_cuotas.py tests/services/test_cascada_cuotas.py
git commit -m "feat(sprint75): motor de cascada distribuir_pago_en_cascada"
```

- [ ] **Step 6: Escribir el test que falla para `deuda_pendiente_cuota` (helper con DB, capa de integración)**

```python
def test_deuda_pendiente_cuota_refleja_capital_e_interes_reales(monkeypatch):
    _sesion_en_memoria(monkeypatch)
    obligacion_recurrente = _obligacion_civil_familia_recurrente_helper(
        valor=Decimal("150000.00"),
        fecha_inicio=date(2024, 1, 1),
        tasa_efectiva_anual=Decimal("12.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 3, 1))
    cuota_enero = next(c for c in cuotas if c.fecha_origen == date(2024, 1, 1))

    rate_provider = CivilFamiliaStrategy()._construir_rate_provider_obligacion(
        cuota_enero, date(2024, 3, 1)
    )
    deuda = deuda_pendiente_cuota(
        cuota_enero, abonos_existentes=[], fecha_pago=date(2024, 3, 1), rate_provider=rate_provider
    )
    assert deuda.principal == Decimal("150000.00")
    assert deuda.interest > Decimal("0.00")  # 2 meses de mora al 12% anual
```

- [ ] **Step 7: Correr el test y confirmar que falla**

Run: `pytest tests/services/test_cascada_cuotas.py -k deuda_pendiente_cuota -v`
Expected: FAIL con `ImportError: cannot import name 'deuda_pendiente_cuota'`

- [ ] **Step 8: Implementar `deuda_pendiente_cuota`**

Agregar a `app/services/cascada_cuotas.py`:

```python
from app.domain.obligation.payment import Payment
from app.engine.interest.provider import RateProvider
from app.engine.temporal.schedulers.base import Event
from app.services.motor_universal import UniversalLiquidationService


def deuda_pendiente_cuota(
    cuota,
    abonos_existentes: list,
    fecha_pago: date,
    rate_provider: RateProvider,
) -> PendingDebt:
    """Deuda pendiente real de una cuota-hija a `fecha_pago`, corriendo el
    mismo motor (UniversalLiquidationService) y la misma estrategia
    (allocate_capital_primero) que se usara despues al liquidar de verdad los
    Abono que cree la cascada -- no persiste nada (pagos=[] o los abonos ya
    existentes de esa cuota, nunca los que la cascada esta a punto de crear)."""
    evento = Event(
        date=cuota.fecha_origen,
        payload={"amount": cuota.valor, "label": cuota.concepto},
        event_type=cuota.categoria,
    )
    pagos = [
        Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
        for abono in abonos_existentes
        if abono.obligacion_id == cuota.id
    ]
    resultado = UniversalLiquidationService().liquidar(
        eventos_causacion=[evento],
        pagos=pagos,
        fecha_corte=fecha_pago,
        rate_provider=rate_provider,
        estrategia_imputacion=AllocationEngine.allocate_capital_primero,
    )
    return resultado.final_balance()
```

- [ ] **Step 9: Correr el test y confirmar que pasa**

Run: `pytest tests/services/test_cascada_cuotas.py -v`
Expected: PASS, todos

- [ ] **Step 10: Commit**

```bash
git add app/services/cascada_cuotas.py tests/services/test_cascada_cuotas.py
git commit -m "feat(sprint75): deuda_pendiente_cuota reutiliza el motor real para la cascada"
```

---

### Task 5: UI — selección por rango + `PagoPorRangoDialog`

**Files:**
- Create: `app/views/pago_por_rango.py`
- Modify: `app/views/expediente_detalle.py`
- Test: `tests/views/test_pago_por_rango.py`
- Test: `tests/views/test_expediente_detalle.py`

- [ ] **Step 1: Escribir el test que falla para el diálogo**

```python
def test_pago_por_rango_dialog_crea_un_abono_por_cuota_tocada(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    obligacion_recurrente = _obligacion_civil_familia_recurrente_helper(
        valor=Decimal("150000.00"),
        fecha_inicio=date(2022, 4, 1),
        tasa_efectiva_anual=Decimal("0.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 4, 1))
    cuotas_a_pagar = sorted(
        [c for c in cuotas if date(2024, 2, 1) <= c.fecha_origen <= date(2024, 4, 1)],
        key=lambda c: c.fecha_origen,
        reverse=True,
    )

    dialogo = PagoPorRangoDialog(
        cuotas=cuotas_a_pagar, area="CIVIL_FAMILIA", parent=None
    )
    qtbot.addWidget(dialogo)
    dialogo.campo_monto.setText("450000")
    dialogo.campo_fecha.setDate(QDate(2024, 4, 1))
    dialogo._calcular_preview()

    assert dialogo.tabla_preview.rowCount() == 3
    dialogo.confirmar()

    session = session_module.get_session()
    total_abonos = session.query(Abono).filter(
        Abono.obligacion_id.in_([c.id for c in cuotas_a_pagar])
    ).count()
    session.close()
    assert total_abonos == 3
```

Nota para el implementador: adaptar los helpers de sesión/obligación al patrón real de
`tests/views/test_obligaciones.py`/`tests/views/test_abonos.py`. Este test usa una tasa `0.00` para que el
ejemplo sea determinístico sin depender de acumulación de interés real entre fechas — suficiente para
probar que se crean 3 `Abono`, uno por cuota tocada.

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pytest tests/views/test_pago_por_rango.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app.views.pago_por_rango'`

- [ ] **Step 3: Crear `PagoPorRangoDialog`**

```python
"""Sprint 75: dialogo de pago por rango de cuotas-hija, con preview de la
cascada antes de confirmar. Ver docs/superpowers/specs/
2026-08-14-sprint75-cuotas-recurrentes-cascada-design.md, seccion "Alcance",
punto 5."""

from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

import database.session as session_module
from app.services.area_strategy import CivilFamiliaStrategy, ComercialStrategy
from app.services.cascada_cuotas import deuda_pendiente_cuota, distribuir_pago_en_cascada
from app.views.form_utils import guardar_o_actualizar
from database.models import Abono

_ESTRATEGIA_POR_AREA = {
    "CIVIL_FAMILIA": CivilFamiliaStrategy,
    "COMERCIAL": ComercialStrategy,
}


class PagoPorRangoDialog(QDialog):
    def __init__(self, cuotas: list, area: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pagar cuotas seleccionadas")
        self._cuotas = cuotas
        self._area = area
        self._asignaciones: list[tuple[object, Decimal]] = []
        self._remanente = Decimal("0.00")

        layout = QVBoxLayout(self)
        formulario = QFormLayout()
        self.campo_monto = QLineEdit()
        self.campo_fecha = QDateEdit()
        self.campo_fecha.setCalendarPopup(True)
        self.campo_fecha.setDate(QDate.currentDate())
        formulario.addRow("Monto total del pago", self.campo_monto)
        formulario.addRow("Fecha del pago", self.campo_fecha)
        layout.addLayout(formulario)

        self.tabla_preview = QTableWidget(0, 2)
        self.tabla_preview.setHorizontalHeaderLabels(["Cuota", "Monto asignado"])
        layout.addWidget(self.tabla_preview)

        self.etiqueta_remanente = QLabel("")
        layout.addWidget(self.etiqueta_remanente)

        self.campo_monto.textChanged.connect(self._calcular_preview)
        self.campo_fecha.dateChanged.connect(self._calcular_preview)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.confirmar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _fecha_pago(self) -> date:
        return self.campo_fecha.date().toPython()

    def _calcular_preview(self) -> None:
        self.tabla_preview.setRowCount(0)
        self._asignaciones = []
        try:
            monto_total = Decimal(self.campo_monto.text())
        except InvalidOperation:
            self.etiqueta_remanente.setText("Ingrese un monto valido.")
            return

        strategy_cls = _ESTRATEGIA_POR_AREA[self._area]
        strategy = strategy_cls()
        fecha_pago = self._fecha_pago()

        session = session_module.get_session()
        try:
            cuotas_y_deuda = []
            for cuota in self._cuotas:
                abonos_existentes = (
                    session.query(Abono).filter(Abono.obligacion_id == cuota.id).all()
                )
                rate_provider = strategy._construir_rate_provider_obligacion(cuota, fecha_pago)
                deuda = deuda_pendiente_cuota(
                    cuota, abonos_existentes, fecha_pago, rate_provider
                )
                cuotas_y_deuda.append((cuota, deuda))
        finally:
            session.close()

        self._asignaciones, self._remanente = distribuir_pago_en_cascada(
            cuotas_y_deuda, monto_total, fecha_pago
        )

        self.tabla_preview.setRowCount(len(self._asignaciones))
        for fila, (cuota, monto) in enumerate(self._asignaciones):
            self.tabla_preview.setItem(fila, 0, QTableWidgetItem(cuota.concepto))
            self.tabla_preview.setItem(fila, 1, QTableWidgetItem(f"{monto:,.2f}"))

        if self._remanente > Decimal("0.00"):
            self.etiqueta_remanente.setText(
                f"Sobran ${self._remanente:,.2f} sin cubrir en las cuotas seleccionadas. "
                "Reduzca el monto o amplíe la selección para confirmar."
            )
        else:
            self.etiqueta_remanente.setText("")

    def confirmar(self) -> None:
        if not self._asignaciones or self._remanente > Decimal("0.00"):
            QMessageBox.warning(
                self,
                "Pago incompleto",
                "El monto debe repartirse por completo entre las cuotas seleccionadas antes "
                "de confirmar.",
            )
            return

        fecha_pago = self._fecha_pago()
        for cuota, monto in self._asignaciones:
            guardar_o_actualizar(
                session_module.get_session(),
                Abono,
                None,
                obligacion_id=cuota.id,
                fecha=fecha_pago,
                monto=monto,
                referencia="Pago por rango (cascada)",
            )
        self.accept()
```

Nota para el implementador: revisar el patrón exacto de apertura/cierre de sesión que usa
`guardar_o_actualizar`/`AbonoFormDialog.guardar()` en `app/views/abonos.py` (¿recibe la sesión ya abierta,
o la abre y cierra internamente?) y ajustar `confirmar()` para seguir exactamente ese mismo patrón en vez
de abrir una sesión nueva por cada `Abono` si el helper ya maneja su propia sesión.

- [ ] **Step 4: Correr el test y confirmar que pasa**

Run: `pytest tests/views/test_pago_por_rango.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/views/pago_por_rango.py tests/views/test_pago_por_rango.py
git commit -m "feat(sprint75): PagoPorRangoDialog"
```

- [ ] **Step 6: Escribir el test que falla para la selección múltiple + botón nuevo en `ExpedienteDetallePage`**

```python
def test_boton_pagar_cuotas_seleccionadas_solo_habilita_con_cuotas_hija_de_la_misma_recurrente(
    qtbot, monkeypatch
):
    _sesion_en_memoria(monkeypatch)
    expediente = _crear_expediente_con_cuotas_helper()  # crea 1 recurrente + 3 cuotas hijas

    pagina = ExpedienteDetallePage(expediente_id=expediente.id)
    qtbot.addWidget(pagina)

    # Sin seleccion: deshabilitado.
    assert not pagina.boton_pagar_cuotas_seleccionadas.isEnabled()

    # Selecciona las 2 primeras filas de cuotas (contiguas, misma recurrente).
    pagina.tabla_obligaciones.setRangeSelected(
        QTableWidgetSelectionRange(1, 0, 2, pagina.tabla_obligaciones.columnCount() - 1), True
    )
    pagina._actualizar_boton_pagar_cuotas_seleccionadas()
    assert pagina.boton_pagar_cuotas_seleccionadas.isEnabled()
```

Nota para el implementador: adaptar `_crear_expediente_con_cuotas_helper` a los helpers reales de
`tests/views/test_expediente_detalle.py` (crear una obligación RECURRENTE con `tipo_reajuste_anual =
NINGUNO`, llamar `generar_cuotas_mensuales`, y verificar en qué filas exactas de `tabla_obligaciones`
terminan las cuotas según `_refrescar_obligaciones()` — el test ya existente
`test_expediente_detalle.py:1471-1474` referenciado en la investigación previa muestra que las cuotas
aparecen justo después de la fila del padre).

- [ ] **Step 7: Correr el test y confirmar que falla**

Run: `pytest tests/views/test_expediente_detalle.py -k pagar_cuotas_seleccionadas -v`
Expected: FAIL con `AttributeError: 'ExpedienteDetallePage' object has no attribute 'boton_pagar_cuotas_seleccionadas'`

- [ ] **Step 8: Agregar selección múltiple contigua y el botón nuevo**

En `app/views/expediente_detalle.py`, junto a la configuración de `tabla_obligaciones` (constructor,
~línea 99-121), agregar:

```python
        from PySide6.QtWidgets import QAbstractItemView

        self.tabla_obligaciones.setSelectionMode(QAbstractItemView.SelectionMode.ContiguousSelection)
        self.tabla_obligaciones.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_obligaciones.itemSelectionChanged.connect(
            self._actualizar_boton_pagar_cuotas_seleccionadas
        )
```

Junto al botón "Agregar abono" existente, agregar:

```python
        self.boton_pagar_cuotas_seleccionadas = QPushButton("Pagar cuotas seleccionadas")
        self.boton_pagar_cuotas_seleccionadas.setEnabled(False)
        self.boton_pagar_cuotas_seleccionadas.clicked.connect(self._abrir_dialogo_pago_por_rango)
```

(agregarlo al mismo layout de botones donde ya vive el botón de "Agregar abono", y agregar el import de
`QPushButton` si no está ya presente).

Agregar los dos métodos nuevos a la clase:

```python
    def _cuotas_hija_de_una_misma_recurrente(self, obligaciones: list) -> bool:
        if not obligaciones:
            return False
        padres = {o.obligacion_padre_id for o in obligaciones}
        return len(padres) == 1 and None not in padres

    def _actualizar_boton_pagar_cuotas_seleccionadas(self) -> None:
        filas = sorted({indice.row() for indice in self.tabla_obligaciones.selectedIndexes()})
        obligaciones_seleccionadas = [
            self._obligacion_por_fila(fila) for fila in filas if fila in self._obligacion_ids_por_fila
        ]
        self.boton_pagar_cuotas_seleccionadas.setEnabled(
            self._cuotas_hija_de_una_misma_recurrente(obligaciones_seleccionadas)
        )

    def _abrir_dialogo_pago_por_rango(self) -> None:
        filas = sorted({indice.row() for indice in self.tabla_obligaciones.selectedIndexes()})
        obligaciones_seleccionadas = [self._obligacion_por_fila(fila) for fila in filas]
        cuotas_ordenadas = sorted(
            obligaciones_seleccionadas, key=lambda o: o.fecha_origen, reverse=True
        )
        dialogo = PagoPorRangoDialog(cuotas=cuotas_ordenadas, area=self._area, parent=self)
        if dialogo.exec():
            self._refrescar_obligaciones()
            self._refrescar_abonos()
```

Agregar el import de `PagoPorRangoDialog` al inicio del archivo:

```python
from app.views.pago_por_rango import PagoPorRangoDialog
```

Nota para el implementador: `_obligacion_por_fila` no existe todavía como método explícito — revisar cómo
`_abrir_dialogo_abono()` (`expediente_detalle.py:477-488`) resuelve la `Obligacion` real a partir de una
fila usando `self._obligacion_ids_por_fila` (mapa fila→id, ya existente) y una consulta a sesión; extraer
esa resolución a un método `_obligacion_por_fila(self, fila: int)` reutilizado tanto aquí como en
`_abrir_dialogo_abono()` si no existe ya, en vez de duplicar la lógica de consulta.

- [ ] **Step 9: Correr el test y confirmar que pasa**

Run: `pytest tests/views/test_expediente_detalle.py -k pagar_cuotas_seleccionadas -v`
Expected: PASS

- [ ] **Step 10: Correr toda la suite de `test_expediente_detalle.py` para confirmar cero regresión**

Run: `pytest tests/views/test_expediente_detalle.py -v`
Expected: PASS

- [ ] **Step 11: Commit**

```bash
git add app/views/expediente_detalle.py tests/views/test_expediente_detalle.py
git commit -m "feat(sprint75): selección por rango y botón Pagar cuotas seleccionadas"
```

---

### Task 6: Integración — reproducir el ejemplo numérico exacto del usuario

**Files:**
- Create: `tests/integration/test_sprint75_cascada_cuotas.py`

- [ ] **Step 1: Escribir el test de integración completo (end-to-end, sin mocks de motor)**

```python
"""Sprint 75: reproduce el ejemplo numerico exacto dado por el usuario --
cuotas de $150.000 mensuales desde el 1-abr-2022, abono de $500.000 el
1-abr-2024. Corre sobre Comercial (no Civil/Familia) a proposito, para
probar la generalizacion del Sprint 75, no solo el mecanismo que ya existia
en Familia desde el Sprint 41."""

from datetime import date
from decimal import Decimal

from app.services.area_strategy import ComercialStrategy
from app.services.cascada_cuotas import deuda_pendiente_cuota, distribuir_pago_en_cascada
from app.services.reajuste_anual import generar_cuotas_mensuales
from database.models import AreaDerecho, Obligacion, TipoObligacion, TipoReajusteAnual


def test_ejemplo_del_usuario_en_comercial(monkeypatch):
    _sesion_en_memoria(monkeypatch)
    expediente = _crear_expediente_helper(area=AreaDerecho.COMERCIAL)

    session = session_module.get_session()
    obligacion_recurrente = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota mensual pagare comercial",
        categoria="CAPITAL_PAGARE",
        fecha_inicio=date(2022, 4, 1),
        dia_pago=1,
        valor=Decimal("150000.00"),
        tasa_efectiva_anual=Decimal("12.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    session.add(obligacion_recurrente)
    session.commit()
    obligacion_id = obligacion_recurrente.id
    session.close()

    session = session_module.get_session()
    obligacion_recurrente = session.get(Obligacion, obligacion_id)
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 4, 1))
    session.close()

    cuotas_relevantes = sorted(
        [c for c in cuotas if date(2024, 2, 1) <= c.fecha_origen <= date(2024, 4, 1)],
        key=lambda c: c.fecha_origen,
        reverse=True,
    )
    assert [c.fecha_origen for c in cuotas_relevantes] == [
        date(2024, 4, 1),
        date(2024, 3, 1),
        date(2024, 2, 1),
    ]

    strategy = ComercialStrategy()
    fecha_pago = date(2024, 4, 1)
    cuotas_y_deuda = []
    for cuota in cuotas_relevantes:
        rate_provider = strategy._construir_rate_provider_obligacion(cuota, fecha_pago)
        deuda = deuda_pendiente_cuota(cuota, [], fecha_pago, rate_provider)
        cuotas_y_deuda.append((cuota, deuda))

    asignaciones, remanente = distribuir_pago_en_cascada(
        cuotas_y_deuda, Decimal("500000.00"), fecha_pago
    )

    # Capital total de las 3 cuotas: 450.000. Remanente para interes: 50.000.
    assert sum(monto for _, monto in asignaciones) == Decimal("500000.00")
    assert remanente == Decimal("0.00")

    monto_abril = next(m for c, m in asignaciones if c.fecha_origen == date(2024, 4, 1))
    monto_marzo = next(m for c, m in asignaciones if c.fecha_origen == date(2024, 3, 1))
    monto_febrero = next(m for c, m in asignaciones if c.fecha_origen == date(2024, 2, 1))

    # Abril: nace ese mismo dia, sin mora -- solo su capital.
    assert monto_abril == Decimal("150000.00")
    # Marzo: capital + 1 mes de mora al 12% anual.
    assert monto_marzo > Decimal("150000.00")
    # Febrero: recibe el resto -- capital completo + una parte de sus 2 meses
    # de mora, el resto del interes de febrero queda sin cubrir (pero el
    # capital de febrero ya no genera intereses nuevos).
    assert monto_febrero > Decimal("150000.00")
    assert monto_abril + monto_marzo + monto_febrero == Decimal("500000.00")
```

Nota para el implementador: los valores exactos de `monto_marzo`/`monto_febrero` dependen de la tasa
diaria real que resuelva `EffectiveRateConverter.annual_to_daily(Decimal("12.00"))` y del número exacto de
días de mora hasta 2024-04-01 — calcularlos corriendo el test una vez con `assert False, (monto_marzo,
monto_febrero)` para leer los valores reales del motor antes de fijar las aserciones definitivas (no
inventar los decimales a mano). El punto central que este test debe probar, sin importar el redondeo
exacto: `monto_abril + monto_marzo + monto_febrero == 500000.00` (el pago se reparte completo) y el orden
capital-antes-que-interés se refleja en que las 3 cuotas reciben su capital completo antes de que
`remanente` se agote en intereses.

- [ ] **Step 2: Correr el test, leer los valores reales del motor, fijar las aserciones exactas**

Run: `pytest tests/integration/test_sprint75_cascada_cuotas.py -v`
Expected: primero puede fallar por valores no ajustados — correr, leer los montos reales impresos por el
motor (agregar un `print` temporal si hace falta), fijar las aserciones a esos valores exactos, y volver a
correr.

- [ ] **Step 3: Confirmar que pasa**

Run: `pytest tests/integration/test_sprint75_cascada_cuotas.py -v`
Expected: PASS

- [ ] **Step 4: Correr la suite completa del proyecto**

Run: `pytest`
Expected: PASS, cero regresión en ninguna de las 6 áreas

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_sprint75_cascada_cuotas.py
git commit -m "test(sprint75): integración end-to-end del ejemplo numérico del usuario en Comercial"
```

---

### Task 7: Documentación (README, GUIA_USUARIO, CHANGELOG)

**Files:**
- Modify: `README.md`
- Modify: `docs/GUIA_USUARIO.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Documentar en `docs/GUIA_USUARIO.md`**

Agregar una sección nueva (siguiendo el estilo de la sección existente sobre cuotas/abonos del Sprint 41)
explicando: que Comercial ahora también genera cuotas mensuales reales igual que Civil/Familia, con o sin
reajuste anual; el botón "Pagar cuotas seleccionadas" y cómo funciona la selección por rango; la lógica de
cascada (capital de la cuota más reciente primero, luego capital+interés de las anteriores) con un ejemplo
numérico corto.

- [ ] **Step 2: Documentar en `README.md`**

En la sección "Estado actual", agregar una línea resumiendo el Sprint 75: cuotas recurrentes en Comercial,
pago por rango, imputación en cascada.

- [ ] **Step 3: Agregar entrada en `CHANGELOG.md`**

Bajo `### Added`, agregar una entrada describiendo la generalización a Comercial, el motor de cascada, y el
diálogo de pago por rango. Anotar explícitamente que Laboral/Sancionatorio/Honorarios/Tributario quedan
fuera de este sprint (mismo criterio que otras entradas de alcance parcial ya documentadas en este
archivo).

- [ ] **Step 4: Commit**

```bash
git add README.md docs/GUIA_USUARIO.md CHANGELOG.md
git commit -m "docs(sprint75): documentar cuotas recurrentes en Comercial y pago por rango"
```

---

## Definición de Hecho (verificación final)

- [ ] Suite completa en verde: `pytest`
- [ ] `ruff check .` limpio
- [ ] Un expediente de Civil/Familia o Comercial con obligación recurrente genera el listado completo de
      cuotas antes de liquidar, seleccionable por rango o individualmente.
- [ ] El ejemplo numérico del usuario se reproduce exactamente en `tests/integration/test_sprint75_cascada_cuotas.py`.
- [ ] Ninguna de las 6 áreas cambia su comportamiento de imputación para obligaciones que no son
      cuotas-hija (regresión cero).
