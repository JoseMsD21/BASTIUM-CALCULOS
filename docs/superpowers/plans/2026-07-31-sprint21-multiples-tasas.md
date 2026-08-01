# Sprint 21 — Múltiples tasas de interés simultáneas por expediente — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hacer que un expediente con 2+ obligaciones a tasas de interés distintas (incluso con fechas
solapadas) liquide cada obligación con su propia tasa, en vez de que todo el expediente use la tasa de la
primera obligación (o, en Comercial, que tramos de distintas obligaciones se tapen entre sí por fecha).

**Architecture:** `LiquidationCore`/`BalanceEngine`/`AllocationEngine` no se tocan. Se agregan dos
funciones de módulo nuevas en `app/services/area_strategy.py` — `_liquidar_por_obligacion` (corre un
`LiquidationCore` independiente por obligación, cada uno con su propia tasa y solo sus propios abonos vía
`Abono.obligacion_id`) y `_fusionar_resultados` (intercala los N historiales en una sola línea de tiempo
cronológica, recalculando el saldo consolidado del expediente en cada fila). Las 4 estrategias afectadas
(`CivilFamiliaStrategy`, `ComercialStrategy`, `SancionatorioStrategy`, `HonorariosStrategy`) se reescriben
para usar esta orquestación en vez de construir un único `rate_provider`/lista de eventos compartida.
`LaboralStrategy` y `TributarioStrategy` no se tocan (no aplica, ver spec). Ver el diseño completo en
`docs/superpowers/specs/2026-07-31-sprint21-multiples-tasas-design.md`.

**Tech Stack:** Python, pytest, SQLAlchemy (solo para los modelos `Obligacion`/`Abono` en memoria en los
tests, sin tocar base de datos real).

---

## Antes de empezar

Todos los comandos de este plan se ejecutan desde la raíz del repo:
`c:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS`.

Corre la suite completa una vez para tener una línea base verde antes de tocar nada:

```bash
python -m pytest -q
```

Expected: todos los tests pasan (0 failures). Si algo falla antes de empezar, detente y repórtalo — no es
parte de este plan.

---

### Task 1: Helpers compartidos (`_liquidar_por_obligacion` / `_fusionar_resultados`) + `CivilFamiliaStrategy`

**Files:**
- Modify: `app/services/area_strategy.py` (imports, dos funciones de módulo nuevas, `CivilFamiliaStrategy.liquidar`, `CivilFamiliaStrategy._construir_rate_provider` → `_construir_rate_provider_obligacion`)
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir los 4 tests que fallan**

En `tests/services/test_area_strategy.py`, busca el final de la función
`test_civil_familia_genera_evento_de_costas_si_esta_configurado` (termina con la línea
`assert resultado.final_balance().principal == _Decimal("132145000.00")  # 123.500.000 + 8.645.000`,
seguida de dos líneas en blanco y luego `from app.engine.liquidation.engine import LiquidationCore`).
Inserta los 4 tests siguientes justo ahí, antes de ese `import`:

```python
def test_civil_familia_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa():
    fecha_corte = date(2026, 1, 11)
    obligacion_a = Obligacion(
        id=101, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Obligacion A",
        categoria="DANO_EMERGENTE", fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"), tasa_efectiva_anual=Decimal("12.00"),
    )
    obligacion_b = Obligacion(
        id=102, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Obligacion B",
        categoria="DANO_EMERGENTE", fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"), tasa_efectiva_anual=Decimal("24.00"),
    )

    resultado_combinado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
    )
    resultado_solo_a = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a], abonos=[], fecha_corte=fecha_corte
    )
    resultado_solo_b = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
    )

    assert resultado_combinado.final_balance().principal == Decimal("2000000.00")
    # El interes combinado debe ser exactamente la suma de cada obligacion liquidada con
    # su propia tasa por separado -- no depende de interacciones entre obligaciones porque
    # no hay abonos en este caso.
    interes_esperado = resultado_solo_a.final_balance().interest + resultado_solo_b.final_balance().interest
    assert resultado_combinado.final_balance().interest == interes_esperado
    # Si el bug de "toma la tasa de la primera obligacion para todo el expediente" siguiera
    # presente, el interes combinado seria 2 * interes_solo_a (ambas al 12%) en vez de la
    # suma de cada una a su propia tasa -- como B esta al doble de tasa que A, estos dos
    # valores son observablemente distintos, asi que esta asercion por si sola detecta el bug.
    assert resultado_combinado.final_balance().interest != Decimal("2") * resultado_solo_a.final_balance().interest


def test_civil_familia_abono_de_una_obligacion_no_afecta_el_saldo_de_otra():
    fecha_corte = date(2026, 1, 11)
    obligacion_a = Obligacion(
        id=103, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Obligacion A",
        categoria="DANO_EMERGENTE", fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"), tasa_efectiva_anual=Decimal("12.00"),
    )
    obligacion_b = Obligacion(
        id=104, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Obligacion B",
        categoria="DANO_EMERGENTE", fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"), tasa_efectiva_anual=Decimal("12.00"),
    )
    abono_a = Abono(
        id=201, obligacion_id=103, fecha=date(2026, 1, 5), monto=Decimal("300000.00"), referencia="pago-a"
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a, obligacion_b], abonos=[abono_a], fecha_corte=fecha_corte
    )
    resultado_solo_b_sin_abono = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
    )
    resultado_solo_a_con_abono = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a], abonos=[abono_a], fecha_corte=fecha_corte
    )

    assert resultado.total_payments_applied() == Decimal("300000.00")
    # El interes de B no debe verse afectado por el abono registrado contra A: el interes
    # combinado debe ser exactamente A-con-abono + B-sin-abono, no una mezcla donde el abono
    # de A tambien reduce lo que B acumula.
    interes_esperado = (
        resultado_solo_a_con_abono.final_balance().interest + resultado_solo_b_sin_abono.final_balance().interest
    )
    assert resultado.final_balance().interest == interes_esperado


def test_civil_familia_abono_con_obligacion_id_ajeno_al_expediente_lanza_value_error():
    obligacion = _obligacion_puntual()
    abono_huerfano = Abono(
        id=202, obligacion_id=999, fecha=date(2025, 12, 1), monto=Decimal("1000.00"), referencia="huerfano"
    )

    with pytest.raises(ValueError):
        CivilFamiliaStrategy().liquidar(
            obligaciones=[obligacion], abonos=[abono_huerfano], fecha_corte=date(2026, 1, 1)
        )


def test_civil_familia_dos_obligaciones_producen_una_sola_fila_de_cierre_consolidada():
    fecha_corte = date(2026, 1, 11)
    obligacion_a = Obligacion(
        id=105, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Obligacion A",
        categoria="DANO_EMERGENTE", fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"), tasa_efectiva_anual=Decimal("12.00"),
    )
    obligacion_b = Obligacion(
        id=106, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Obligacion B",
        categoria="DANO_EMERGENTE", fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"), tasa_efectiva_anual=Decimal("24.00"),
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
    )

    filas_de_cierre = [item for item in resultado.items if item.balance.event_type == "LIQUIDATION_CUTOFF"]
    assert len(filas_de_cierre) == 1
    assert resultado.final_balance().principal == Decimal("2000000.00")
```

- [ ] **Step 2: Correr los tests nuevos y verificar que fallan**

Run: `python -m pytest tests/services/test_area_strategy.py -k "dos_obligaciones_tasas_distintas or abono_de_una_obligacion_no_afecta or abono_con_obligacion_id_ajeno or una_sola_fila_de_cierre" -v`

Expected: los 4 tests fallan. El primero (`dos_obligaciones_tasas_distintas...`) falla con un
`AssertionError` en la comparación de interés (hoy el motor usa la tasa de la primera obligación para
todo el expediente, así que `resultado_combinado.final_balance().interest` da el mismo valor que
`2 * interes_solo_a`, no la suma correcta). El de abonos falla igual porque hoy los abonos se aplican
como bolsa única. El de guard falla porque hoy no existe ninguna validación de `obligacion_id` huérfano
(no lanza `ValueError`, o lanza uno distinto por otra razón). El de "una sola fila de cierre" puede pasar
ya por casualidad (siempre hay una sola fila de cierre hoy porque solo hay un `LiquidationCore`) pero el
`assert resultado.final_balance().principal == Decimal("2000000.00")` en ese mismo test seguirá pasando
también — lo importante es que los dos primeros fallen antes de continuar.

- [ ] **Step 3: Agregar los imports necesarios**

En `app/services/area_strategy.py`, reemplaza:

```python
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional
```

por:

```python
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from typing import Callable, List, Optional
```

Luego, reemplaza:

```python
from app.engine.liquidation.result import LiquidationResult
```

por:

```python
from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
```

- [ ] **Step 4: Agregar `_liquidar_por_obligacion` y `_fusionar_resultados`**

En `app/services/area_strategy.py`, justo después de la función `_evento_costas_procesales` (termina en
la línea `return Event(date=obligacion.fecha_origen, payload={...}, event_type="COSTAS_PROCESALES")` y
el `)` de cierre, antes de `class AreaStrategy(ABC):`), agrega:

```python
def _liquidar_por_obligacion(
    obligaciones: List,
    abonos: List,
    fecha_corte: date,
    eventos_fn: Callable[[object], List[Event]],
    rate_provider_fn: Callable[[object, date], MemoryRateProvider],
) -> LiquidationResult:
    """Corre un LiquidationCore independiente por obligacion -- cada una con su propia
    tasa (via rate_provider_fn) y solo sus propios abonos (Abono.obligacion_id) -- y
    fusiona los historiales en una sola linea de tiempo consolidada para el reporte del
    expediente. Ver docs/superpowers/specs/2026-07-31-sprint21-multiples-tasas-design.md
    (Sprint 21): LiquidationCore mantiene un solo PendingDebt agregado por instancia, asi
    que la unica forma de que dos obligaciones acumulen interes a tasas distintas
    simultaneamente es correrlas en instancias separadas."""
    ids_obligaciones = {obligacion.id for obligacion in obligaciones}
    for abono in abonos:
        if abono.obligacion_id not in ids_obligaciones:
            raise ValueError(
                f"El abono '{abono.referencia or abono.id}' (obligacion_id={abono.obligacion_id}) "
                f"no corresponde a ninguna obligacion de este expediente."
            )

    resultados = []
    for obligacion in obligaciones:
        abonos_obligacion = [abono for abono in abonos if abono.obligacion_id == obligacion.id]
        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos_obligacion
        ]
        service = UniversalLiquidationService()
        resultados.append(service.liquidar(
            eventos_causacion=eventos_fn(obligacion),
            pagos=pagos,
            fecha_corte=fecha_corte,
            rate_provider=rate_provider_fn(obligacion, fecha_corte),
        ))

    return _fusionar_resultados(resultados, fecha_corte)


def _fusionar_resultados(resultados: List[LiquidationResult], fecha_corte: date) -> LiquidationResult:
    """Intercala los items de N LiquidationResult (uno por obligacion) en una sola linea
    de tiempo cronologica, recalculando el saldo consolidado del expediente en cada fila.
    Colapsa a la identidad cuando hay una sola obligacion (garantiza que los expedientes
    de una sola obligacion no cambien de resultado)."""
    if len(resultados) == 1:
        return resultados[0]

    filas_regulares = []
    for indice_obligacion, resultado in enumerate(resultados):
        for posicion, item in enumerate(resultado.items):
            if item.balance.event_type == "LIQUIDATION_CUTOFF":
                continue
            filas_regulares.append((item.date, indice_obligacion, posicion, item))
    filas_regulares.sort(key=lambda fila: (fila[0], fila[1], fila[2]))

    saldo_cero = PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
    ultimo_estado = {indice: saldo_cero for indice in range(len(resultados))}
    items_fusionados: List[LiquidationItem] = []
    for _fecha, indice_obligacion, _posicion, item in filas_regulares:
        ultimo_estado[indice_obligacion] = item.balance.debt
        saldo_consolidado = PendingDebt(
            principal=sum((estado.principal for estado in ultimo_estado.values()), Decimal("0.00")),
            interest=sum((estado.interest for estado in ultimo_estado.values()), Decimal("0.00")),
            indexation=sum((estado.indexation for estado in ultimo_estado.values()), Decimal("0.00")),
        )
        items_fusionados.append(replace(
            item,
            capital_base=saldo_consolidado.principal,
            balance=RunningBalance(
                date=item.date, debt=saldo_consolidado, event_type=item.balance.event_type
            ),
        ))

    hubo_cierre = any(
        any(item.balance.event_type == "LIQUIDATION_CUTOFF" for item in resultado.items)
        for resultado in resultados
    )
    if hubo_cierre:
        saldo_final = PendingDebt(
            principal=sum((r.final_balance().principal for r in resultados), Decimal("0.00")),
            interest=sum((r.final_balance().interest for r in resultados), Decimal("0.00")),
            indexation=sum((r.final_balance().indexation for r in resultados), Decimal("0.00")),
        )
        items_fusionados.append(LiquidationItem(
            date=fecha_corte,
            concept="Corte final de liquidación",
            capital_base=saldo_final.principal,
            interest_rate=Decimal("0.00"),
            interest_amount=Decimal("0.00"),
            indexation_amount=Decimal("0.00"),
            payment_amount=Decimal("0.00"),
            balance=RunningBalance(date=fecha_corte, debt=saldo_final, event_type="LIQUIDATION_CUTOFF"),
            rate_source="Varias tasas — ver detalle por fila arriba",
        ))

    return LiquidationResult(items_fusionados)
```

- [ ] **Step 5: Reescribir `CivilFamiliaStrategy.liquidar` y `_construir_rate_provider`**

En `app/services/area_strategy.py`, dentro de `class CivilFamiliaStrategy`, reemplaza el método
`liquidar` completo:

```python
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

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
        )
```

por:

```python
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        return _liquidar_por_obligacion(
            obligaciones=obligaciones,
            abonos=abonos,
            fecha_corte=fecha_corte,
            eventos_fn=lambda obligacion: self._eventos_de_obligacion(obligacion, fecha_corte),
            rate_provider_fn=self._construir_rate_provider_obligacion,
        )
```

Luego reemplaza el método `_construir_rate_provider` completo:

```python
    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        fecha_mas_antigua = min(
            o.fecha_origen if o.tipo.value == "PUNTUAL" else o.fecha_inicio for o in obligaciones
        )
        # Usamos la tasa de la primera obligacion como tasa unica del expediente.
        # (Multiples tasas simultaneas por obligacion quedan fuera de alcance de este sprint.)
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligaciones[0].tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_mas_antigua - timedelta(days=1),
            end=fecha_corte,
            rate=tasa_diaria,
            source="Tasa pactada en la obligación (Art. 1617 C.C.)",
        )
        return provider
```

por:

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

- [ ] **Step 6: Correr los 4 tests nuevos y verificar que pasan**

Run: `python -m pytest tests/services/test_area_strategy.py -k "dos_obligaciones_tasas_distintas or abono_de_una_obligacion_no_afecta or abono_con_obligacion_id_ajeno or una_sola_fila_de_cierre" -v`

Expected: PASS (4 passed).

- [ ] **Step 7: Correr toda la suite de CivilFamiliaStrategy para confirmar que no hay regresión**

Run: `python -m pytest tests/services/test_area_strategy.py -k "civil_familia" -v`

Expected: todos PASS, incluyendo los tests preexistentes de una sola obligación (indexación, costas,
recurrente, abono simple) sin cambios de resultado.

- [ ] **Step 8: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "$(cat <<'EOF'
feat: liquidar cada obligacion con su propia tasa (Sprint 21, Civil/Familia)

Agrega _liquidar_por_obligacion/_fusionar_resultados: corre un
LiquidationCore independiente por obligacion (con su propia tasa y solo
sus propios abonos via Abono.obligacion_id) y fusiona los historiales en
una linea de tiempo consolidada. CivilFamiliaStrategy es la primera de 4
areas migradas a este patron.
EOF
)"
```

---

### Task 2: `ComercialStrategy`

**Files:**
- Modify: `app/services/area_strategy.py` (`ComercialStrategy.liquidar`, `_construir_rate_provider` → `_construir_rate_provider_obligacion`)
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir el test que falla**

Dentro de `class TestComercialStrategy` en `tests/services/test_area_strategy.py`, después del método
`test_soporta_indexacion_ipc_es_false` (el último de la clase), agrega:

```python
    def test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa(self):
        fecha_corte = date(2025, 1, 11)  # antes del vencimiento (2025-06-01) de ambas
        obligacion_a = _obligacion_comercial(
            fecha_origen=date(2025, 1, 1), fecha_vencimiento=date(2025, 6, 1),
            tasa_remuneratoria=Decimal("6.00"),
        )
        obligacion_a.id = 111
        obligacion_b = _obligacion_comercial(
            fecha_origen=date(2025, 1, 1), fecha_vencimiento=date(2025, 6, 1),
            tasa_remuneratoria=Decimal("18.00"),
        )
        obligacion_b.id = 112

        resultado_combinado = ComercialStrategy().liquidar(
            obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_a = ComercialStrategy().liquidar(
            obligaciones=[obligacion_a], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_b = ComercialStrategy().liquidar(
            obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado_combinado.final_balance().principal == Decimal("2000000.00")
        interes_esperado = resultado_solo_a.final_balance().interest + resultado_solo_b.final_balance().interest
        assert resultado_combinado.final_balance().interest == interes_esperado
        assert resultado_combinado.final_balance().interest != Decimal("2") * resultado_solo_a.final_balance().interest
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python -m pytest tests/services/test_area_strategy.py -k "test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa and TestComercialStrategy" -v`

Expected: FAIL en el `assert resultado_combinado.final_balance().interest == interes_esperado` — hoy el
`MemoryRateProvider` compartido de `ComercialStrategy._construir_rate_provider` mezcla los tramos de
ambas obligaciones (mismo rango de fechas, tasas distintas) y el primero insertado "gana" en el scan por
fecha de `MemoryRateProvider.get_rate`.

- [ ] **Step 3: Reescribir `ComercialStrategy.liquidar` y `_construir_rate_provider`**

En `app/services/area_strategy.py`, dentro de `class ComercialStrategy`, reemplaza el método `liquidar`
completo:

```python
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_comercial(obligacion)

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
        )
```

por:

```python
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_comercial(obligacion)

        return _liquidar_por_obligacion(
            obligaciones=obligaciones,
            abonos=abonos,
            fecha_corte=fecha_corte,
            eventos_fn=lambda obligacion: self._eventos_de_obligacion(obligacion, fecha_corte),
            rate_provider_fn=self._construir_rate_provider_obligacion,
        )
```

Luego reemplaza el método `_construir_rate_provider` completo:

```python
    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        provider = MemoryRateProvider()

        for obligacion in obligaciones:
            tasa_moratoria_diaria = EffectiveRateConverter.annual_to_daily(obligacion.tasa_moratoria_anual)

            if obligacion.tipo.value == "PUNTUAL":
                tasa_remuneratoria_diaria = EffectiveRateConverter.annual_to_daily(obligacion.tasa_efectiva_anual)
                inicio_remuneratorio = obligacion.fecha_origen - timedelta(days=1)
                fin_remuneratorio = min(obligacion.fecha_vencimiento, fecha_corte)
                provider.add_rate_period(
                    start=inicio_remuneratorio,
                    end=fin_remuneratorio,
                    rate=tasa_remuneratoria_diaria,
                    source="Tasa remuneratoria pactada (Art. 884 C.Co.)",
                )
                if obligacion.fecha_vencimiento < fecha_corte:
                    inicio_moratorio = obligacion.fecha_vencimiento + timedelta(days=1)
                    provider.add_rate_period(
                        start=inicio_moratorio,
                        end=fecha_corte,
                        rate=tasa_moratoria_diaria,
                        source="Tasa moratoria pactada (Art. 884 C.Co.)",
                    )
            else:
                # RECURRENTE: sin split por cuota individual (alcance reducido, ver spec).
                inicio = obligacion.fecha_inicio - timedelta(days=1)
                provider.add_rate_period(
                    start=inicio,
                    end=fecha_corte,
                    rate=tasa_moratoria_diaria,
                    source="Tasa moratoria pactada (Art. 884 C.Co.)",
                )

        return provider
```

por:

```python
    def _construir_rate_provider_obligacion(self, obligacion, fecha_corte: date) -> MemoryRateProvider:
        provider = MemoryRateProvider()
        tasa_moratoria_diaria = EffectiveRateConverter.annual_to_daily(obligacion.tasa_moratoria_anual)

        if obligacion.tipo.value == "PUNTUAL":
            tasa_remuneratoria_diaria = EffectiveRateConverter.annual_to_daily(obligacion.tasa_efectiva_anual)
            inicio_remuneratorio = obligacion.fecha_origen - timedelta(days=1)
            fin_remuneratorio = min(obligacion.fecha_vencimiento, fecha_corte)
            provider.add_rate_period(
                start=inicio_remuneratorio,
                end=fin_remuneratorio,
                rate=tasa_remuneratoria_diaria,
                source="Tasa remuneratoria pactada (Art. 884 C.Co.)",
            )
            if obligacion.fecha_vencimiento < fecha_corte:
                inicio_moratorio = obligacion.fecha_vencimiento + timedelta(days=1)
                provider.add_rate_period(
                    start=inicio_moratorio,
                    end=fecha_corte,
                    rate=tasa_moratoria_diaria,
                    source="Tasa moratoria pactada (Art. 884 C.Co.)",
                )
        else:
            # RECURRENTE: sin split por cuota individual (alcance reducido, ver spec).
            inicio = obligacion.fecha_inicio - timedelta(days=1)
            provider.add_rate_period(
                start=inicio,
                end=fecha_corte,
                rate=tasa_moratoria_diaria,
                source="Tasa moratoria pactada (Art. 884 C.Co.)",
            )

        return provider
```

- [ ] **Step 4: Correr el test nuevo y verificar que pasa**

Run: `python -m pytest tests/services/test_area_strategy.py -k "test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa and TestComercialStrategy" -v`

Expected: PASS.

- [ ] **Step 5: Correr toda la suite de ComercialStrategy para confirmar que no hay regresión**

Run: `python -m pytest tests/services/test_area_strategy.py -k "TestComercialStrategy" -v`

Expected: todos PASS (incluye `test_usa_tasa_moratoria_tras_el_vencimiento_acumula_mas_interes_que_solo_remuneratoria`, `test_sin_mora_usa_solo_tasa_remuneratoria`, `test_recurrente_no_hace_split_usa_tasa_moratoria_unica`, todos de una sola obligación, sin cambios de resultado).

- [ ] **Step 6: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "$(cat <<'EOF'
feat: liquidar cada obligacion con su propia tasa (Sprint 21, Comercial)

ComercialStrategy migra a _liquidar_por_obligacion -- elimina el bug de
tramos remuneratorio/moratorio de distintas obligaciones tapandose entre
si cuando sus fechas se solapan.
EOF
)"
```

---

### Task 3: `SancionatorioStrategy`

**Files:**
- Modify: `app/services/area_strategy.py` (`SancionatorioStrategy.liquidar`, `_construir_rate_provider` → `_construir_rate_provider_obligacion`)
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir el test que falla**

Dentro de `class TestSancionatorioStrategy` en `tests/services/test_area_strategy.py`, después del método
`test_sancionatorio_genera_evento_de_costas_si_esta_configurado` (el último de la clase), agrega:

```python
    def test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa(self):
        fecha_corte = date(2019, 6, 11)
        obligacion_a = _obligacion_sancionatoria(tasa_efectiva_anual=Decimal("12.00"))
        obligacion_a.id = 121
        obligacion_b = _obligacion_sancionatoria(tasa_efectiva_anual=Decimal("24.00"))
        obligacion_b.id = 122

        resultado_combinado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_a = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion_a], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_b = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
        )

        interes_esperado = resultado_solo_a.final_balance().interest + resultado_solo_b.final_balance().interest
        assert resultado_combinado.final_balance().interest == interes_esperado
        assert resultado_combinado.final_balance().interest != Decimal("2") * resultado_solo_a.final_balance().interest
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python -m pytest tests/services/test_area_strategy.py -k "test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa and TestSancionatorioStrategy" -v`

Expected: FAIL en el `assert resultado_combinado.final_balance().interest == interes_esperado` — hoy
`SancionatorioStrategy._construir_rate_provider` usa `obligaciones[0].tasa_efectiva_anual` (12%) para
todo el expediente, así que el interés combinado da `2 * interes_solo_a`, no la suma correcta.

- [ ] **Step 3: Reescribir `SancionatorioStrategy.liquidar` y `_construir_rate_provider`**

En `app/services/area_strategy.py`, dentro de `class SancionatorioStrategy`, reemplaza el método
`liquidar` completo:

```python
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_sancionatoria(obligacion)

        eventos_causacion = []
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
```

por:

```python
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_sancionatoria(obligacion)

        return _liquidar_por_obligacion(
            obligaciones=obligaciones,
            abonos=abonos,
            fecha_corte=fecha_corte,
            eventos_fn=self._eventos_de_obligacion,
            rate_provider_fn=self._construir_rate_provider_obligacion,
        )
```

Luego reemplaza el método `_construir_rate_provider` completo:

```python
    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        fecha_mas_antigua = min(o.fecha_origen for o in obligaciones)
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligaciones[0].tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_mas_antigua - timedelta(days=1), end=fecha_corte, rate=tasa_diaria
        )
        return provider
```

por:

```python
    def _construir_rate_provider_obligacion(self, obligacion, fecha_corte: date) -> MemoryRateProvider:
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligacion.tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=obligacion.fecha_origen - timedelta(days=1), end=fecha_corte, rate=tasa_diaria
        )
        return provider
```

- [ ] **Step 4: Correr el test nuevo y verificar que pasa**

Run: `python -m pytest tests/services/test_area_strategy.py -k "test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa and TestSancionatorioStrategy" -v`

Expected: PASS.

- [ ] **Step 5: Correr toda la suite de SancionatorioStrategy para confirmar que no hay regresión**

Run: `python -m pytest tests/services/test_area_strategy.py -k "TestSancionatorioStrategy" -v`

Expected: todos PASS.

- [ ] **Step 6: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "$(cat <<'EOF'
feat: liquidar cada obligacion con su propia tasa (Sprint 21, Sancionatorio)

SancionatorioStrategy migra a _liquidar_por_obligacion -- ya no ignora
la tasa_efectiva_anual de todas las obligaciones salvo la primera.
EOF
)"
```

---

### Task 4: `HonorariosStrategy`

**Files:**
- Modify: `app/services/area_strategy.py` (`HonorariosStrategy.liquidar`, `_construir_rate_provider` → `_construir_rate_provider_obligacion`)
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir el test que falla**

Dentro de `class TestHonorariosStrategy` en `tests/services/test_area_strategy.py`, después del método
`test_soporta_indexacion_ipc_es_false` (el último de la clase), agrega:

```python
    def test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa(self):
        fecha_corte = date(2026, 1, 11)
        obligacion_a = _obligacion_honorarios(
            cuota_litis_pactada_pct=Decimal("10.00"), tasa_efectiva_anual=Decimal("12.00")
        )
        obligacion_a.id = 131
        obligacion_b = _obligacion_honorarios(
            cuota_litis_pactada_pct=Decimal("10.00"), tasa_efectiva_anual=Decimal("24.00")
        )
        obligacion_b.id = 132

        resultado_combinado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_a = HonorariosStrategy().liquidar(
            obligaciones=[obligacion_a], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_b = HonorariosStrategy().liquidar(
            obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
        )

        interes_esperado = resultado_solo_a.final_balance().interest + resultado_solo_b.final_balance().interest
        assert resultado_combinado.final_balance().interest == interes_esperado
        assert resultado_combinado.final_balance().interest != Decimal("2") * resultado_solo_a.final_balance().interest
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python -m pytest tests/services/test_area_strategy.py -k "test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa and TestHonorariosStrategy" -v`

Expected: FAIL en el `assert resultado_combinado.final_balance().interest == interes_esperado` — mismo
patrón que Sancionatorio: `HonorariosStrategy._construir_rate_provider` usa
`obligaciones[0].tasa_efectiva_anual` para todo el expediente.

- [ ] **Step 3: Reescribir `HonorariosStrategy.liquidar` y `_construir_rate_provider`**

En `app/services/area_strategy.py`, dentro de `class HonorariosStrategy`, reemplaza el método `liquidar`
completo:

```python
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
```

por:

```python
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_honorarios(obligacion)

        return _liquidar_por_obligacion(
            obligaciones=obligaciones,
            abonos=abonos,
            fecha_corte=fecha_corte,
            eventos_fn=self._eventos_de_obligacion,
            rate_provider_fn=self._construir_rate_provider_obligacion,
        )
```

Luego reemplaza el método `_construir_rate_provider` completo:

```python
    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        fecha_mas_antigua = min(o.fecha_origen for o in obligaciones)
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligaciones[0].tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_mas_antigua - timedelta(days=1), end=fecha_corte, rate=tasa_diaria
        )
        return provider
```

por:

```python
    def _construir_rate_provider_obligacion(self, obligacion, fecha_corte: date) -> MemoryRateProvider:
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligacion.tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=obligacion.fecha_origen - timedelta(days=1), end=fecha_corte, rate=tasa_diaria
        )
        return provider
```

- [ ] **Step 4: Correr el test nuevo y verificar que pasa**

Run: `python -m pytest tests/services/test_area_strategy.py -k "test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa and TestHonorariosStrategy" -v`

Expected: PASS.

- [ ] **Step 5: Correr toda la suite de HonorariosStrategy para confirmar que no hay regresión**

Run: `python -m pytest tests/services/test_area_strategy.py -k "TestHonorariosStrategy" -v`

Expected: todos PASS.

- [ ] **Step 6: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "$(cat <<'EOF'
feat: liquidar cada obligacion con su propia tasa (Sprint 21, Honorarios)

HonorariosStrategy migra a _liquidar_por_obligacion, ultima de las 4
areas afectadas por el bug de "tasa de la primera obligacion para todo
el expediente". LaboralStrategy y TributarioStrategy no aplican (ver
docs/superpowers/specs/2026-07-31-sprint21-multiples-tasas-design.md).
EOF
)"
```

---

### Task 5: Suite completa + cierre de Sprint 21 en `Pendientes.md`

**Files:**
- Modify: `Pendientes.md`

- [ ] **Step 1: Correr la suite completa**

Run: `python -m pytest -q`

Expected: todos los tests pasan (0 failures), incluyendo los ~2600+ tests preexistentes de las 6 áreas,
sin ningún cambio de resultado fuera de los 6 tests nuevos de este plan.

- [ ] **Step 2: Anotar el rango de commits de este sprint**

Run: `git log --oneline -6`

Guarda el hash del commit más antiguo (Task 1) y el más reciente (Task 4) de la salida — los vas a usar
en el Step 3 en el mismo formato que el cierre del Sprint 18 (`Pendientes.md`, línea 1425: "ver rango de
commits desde `d7faacf` hasta `11c0d60`").

- [ ] **Step 3: Marcar el Sprint 21 como completado en `Pendientes.md`**

Reemplaza la línea 1608:

```markdown
## Sprint 21 — Múltiples tasas de interés simultáneas por expediente
```

por:

```markdown
## Sprint 21 — Múltiples tasas de interés simultáneas por expediente ✅ Completado
```

Reemplaza la línea 91 (entrada correspondiente en la tabla de contenidos):

```markdown
- [Sprint 21 — Múltiples tasas de interés simultáneas por expediente](#sprint-21--múltiples-tasas-de-interés-simultáneas-por-expediente)
```

por:

```markdown
- [Sprint 21 — Múltiples tasas de interés simultáneas por expediente ✅ Completado](#sprint-21--múltiples-tasas-de-interés-simultáneas-por-expediente--completado)
```

Luego, busca el final de la sección del Sprint 21 (después de "Suite completa en verde, sin cambios de
resultado en los tests existentes de expedientes de una sola obligación." y antes del separador `---` que
la separa del Sprint 22), y agrega el bloque de cierre. Reemplaza:

```markdown
**Definición de Hecho:**
- Test con un expediente de 2+ obligaciones a tasas distintas y fechas solapadas, verificando que cada una
  liquida con su propia tasa.
- Suite completa en verde, sin cambios de resultado en los tests existentes de expedientes de una sola
  obligación.

---

## Sprint 22 — Limpieza técnica acumulada
```

por (reemplazando `<hash-inicial>`/`<hash-final>` con los hashes reales obtenidos en el Step 2):

```markdown
**Definición de Hecho:**
- Test con un expediente de 2+ obligaciones a tasas distintas y fechas solapadas, verificando que cada una
  liquida con su propia tasa.
- Suite completa en verde, sin cambios de resultado en los tests existentes de expedientes de una sola
  obligación.

**Estado:** Implementado (2026-07-31, ver rango de commits desde `<hash-inicial>` hasta `<hash-final>`) —
ver `docs/superpowers/specs/2026-07-31-sprint21-multiples-tasas-design.md` y
`docs/superpowers/plans/2026-07-31-sprint21-multiples-tasas.md`.

El fix real fue más profundo que "indexar `MemoryRateProvider` por obligación": `LiquidationCore`
mantiene un solo saldo agregado por instancia, así que dos obligaciones no pueden acumular interés a
tasas distintas simultáneamente dentro del mismo núcleo. La solución fue correr un `LiquidationCore`
independiente por obligación (cada uno con su propia tasa y solo sus propios abonos, vía el
`obligacion_id` que `Abono` ya tenía en la base de datos pero que el motor ignoraba) y fusionar los
historiales en una sola línea de tiempo consolidada — sin tocar `LiquidationCore`/`BalanceEngine`/
`AllocationEngine`.

Áreas migradas: `CivilFamiliaStrategy`, `ComercialStrategy`, `SancionatorioStrategy`,
`HonorariosStrategy`. `LaboralStrategy` no aplica (liquida un solo contrato por expediente por diseño).
`TributarioStrategy` no aplica (su tasa moratoria del E.T. art. 635 es una tasa legal automática, igual
para todas las obligaciones del expediente, no viene de `tasa_efectiva_anual`).

Cambio de comportamiento deliberado: los abonos ahora se imputan solo a la obligación a la que fueron
registrados (antes se aplicaban como bolsa única del expediente) — coincide con lo que la GUI ya exigía
al capturar un abono (selección obligatoria de una obligación primero) pero que el motor de liquidación
no honraba. No había ningún test que dependiera del comportamiento anterior.

`_construir_rate_provider_obligacion` sigue duplicado entre `CivilFamiliaStrategy`, `SancionatorioStrategy`
y `HonorariosStrategy` (mismo patrón de "un solo tramo plano por obligación") — deduplicarlo queda para el
Sprint 22, como ya anticipaba la nota de coordinación en ese sprint.

---

## Sprint 22 — Limpieza técnica acumulada
```

- [ ] **Step 4: Commit**

```bash
git add Pendientes.md
git commit -m "$(cat <<'EOF'
docs: close Sprint 21 (multiples tasas simultaneas) in Pendientes.md
EOF
)"
```

---

## Self-Review (completado durante la redacción de este plan)

**Cobertura de la spec:**
- Arquitectura (un `LiquidationCore` por obligación, fusión al reportar) → Task 1, Step 4.
- Imputación de abonos por `obligacion_id` → Task 1, Steps 1/4 (test + guard).
- Guard de abono huérfano → Task 1, Step 1 (tercer test) + Step 4 (validación en `_liquidar_por_obligacion`).
- Fila de cierre consolidada única → Task 1, Step 1 (cuarto test) + Step 4 (`_fusionar_resultados`).
- Caso N=1 idéntico al actual → garantizado estructuralmente en `_fusionar_resultados` (early return),
  verificado en el Step 7 de cada Task (suite completa de la estrategia sin regresión).
- Las 4 áreas afectadas → Tasks 1-4. Laboral/Tributario explícitamente no tocadas → documentado en el
  cierre de Task 5.
- Suite completa en verde → Task 5, Step 1.
- Cierre de `Pendientes.md` → Task 5, Steps 2-4.

**Sin placeholders:** cada step tiene código completo o un comando exacto con su resultado esperado; no
hay "TBD" ni "similar al anterior" sin el código repetido.

**Consistencia de tipos/nombres:** `_construir_rate_provider_obligacion(self, obligacion, fecha_corte)` es
el mismo nombre y firma en las 4 estrategias (Tasks 1-4); `eventos_fn`/`rate_provider_fn` en
`_liquidar_por_obligacion` (Task 1, Step 4) coinciden con como se invocan en cada `liquidar()` (Tasks 1-4,
Step 3/lambda vs. bound method según si la estrategia necesita `fecha_corte` en `_eventos_de_obligacion`).
