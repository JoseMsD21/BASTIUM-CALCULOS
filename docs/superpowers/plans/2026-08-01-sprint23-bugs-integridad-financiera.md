# Sprint 23 — Bugs críticos de integridad financiera y auditoría — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir dos bugs reales de auditoría de código (2026-07-21) en `bastium.db`/producción: (1) un sobrepago (`PAYMENT` que excede la deuda total) desaparece silenciosamente del `LiquidationResult` en vez de reflejarse como saldo a favor, y (2) `reconstruir_liquidacion()` lanza `KeyError: 'rate_source'` sobre cualquier `AuditLog` guardado antes de que ese campo existiera, rompiendo la garantía de reconstrucción exacta del Sprint 9.

**Architecture:** Bug 1 se corrige en el núcleo del motor (`LiquidationCore._process_event`, rama `PAYMENT`): se captura el `remainder` que ya calcula `AllocationEngine.allocate` y se expone en un nuevo campo `saldo_a_favor` de `LiquidationItem`/`LiquidationResult`; `payment_amount` pasa a reflejar lo realmente aplicado a la deuda (`allocation.total_payment`), no el monto nominal recibido. Además, siguiendo la decisión de diseño del usuario ("ambas: aceptar en el motor y advertir en la GUI"), `AbonoFormDialog.guardar()` (`app/views/abonos.py`) agrega una advertencia no bloqueante (heurística simple: suma de abonos vs. `Obligacion.valor`, sin recalcular intereses) cuando un abono parece exceder el valor de la obligación — nunca bloquea el guardado. Bug 2 se corrige en `app/engine/audit/serialization.py` cambiando un acceso directo a diccionario (`data["rate_source"]`) por `.get()` con el mismo default `"N/A"` que ya usa el resto del motor cuando no hay `rate_provider`.

**Tech Stack:** Python 3, dataclasses, SQLAlchemy 2.0 (`Session.get`), PySide6 (`QMessageBox`), pytest + pytest-qt.

---

## Task 1: Nuevo campo `saldo_a_favor` en `LiquidationItem`

**Files:**
- Modify: `app/engine/liquidation/models.py:53-68`
- Test: `tests/liquidation/test_models.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar al final de `tests/liquidation/test_models.py`:

```python
def test_liquidation_item_saldo_a_favor_por_defecto_es_cero():
    debt = PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="PAYMENT")
    item = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Pago",
        capital_base=Decimal("0.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("7000000.00"),
        balance=balance,
    )
    assert item.saldo_a_favor == Decimal("0.00")


def test_liquidation_item_acepta_saldo_a_favor_explicito():
    debt = PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="PAYMENT")
    item = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Pago con excedente",
        capital_base=Decimal("0.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("7000000.00"),
        balance=balance,
        saldo_a_favor=Decimal("3000000.00"),
    )
    assert item.saldo_a_favor == Decimal("3000000.00")
```

- [ ] **Step 2: Confirmar que falla**

Run: `pytest tests/liquidation/test_models.py -v`
Expected: FAIL — `TypeError: LiquidationItem.__init__() got an unexpected keyword argument 'saldo_a_favor'` (y el primer test falla con `AttributeError: 'LiquidationItem' object has no attribute 'saldo_a_favor'`).

- [ ] **Step 3: Agregar el campo**

En `app/engine/liquidation/models.py`, el `LiquidationItem` actual termina así (líneas 53-68):

```python
@dataclass(frozen=True)
class LiquidationItem:
    """
    Es la fila histórica definitiva. La salida (Output) que el motor 
    entregará al Result y posteriormente a la interfaz/PDF para que
    el juez pueda auditar la trazabilidad.
    """
    date: date
    concept: str
    capital_base: Decimal
    interest_rate: Decimal
    interest_amount: Decimal
    indexation_amount: Decimal
    payment_amount: Decimal
    balance: RunningBalance
    rate_source: str = "N/A"
```

Cambiar la última línea agregando el nuevo campo con default `Decimal("0.00")` (mismo patrón que `rate_source`, para no romper ninguna construcción existente por keyword):

```python
    rate_source: str = "N/A"
    saldo_a_favor: Decimal = Decimal("0.00")
```

- [ ] **Step 4: Confirmar que pasa**

Run: `pytest tests/liquidation/test_models.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/engine/liquidation/models.py tests/liquidation/test_models.py
git commit -m "feat(sprint23): agregar campo saldo_a_favor a LiquidationItem"
```

---

## Task 2: `LiquidationCore` expone el remanente de un sobrepago y corrige `payment_amount`

**Files:**
- Modify: `app/engine/liquidation/engine.py:129-178`
- Test: `tests/liquidation/test_engine.py`

- [ ] **Step 1: Escribir el test de integración que falla**

Agregar al final de `tests/liquidation/test_engine.py`:

```python
def test_engine_sobrepago_expone_remanente_como_saldo_a_favor():
    # Escenario del bug real (auditoria 2026-07-21): un abono de $10.000.000 contra
    # una deuda de $7.000.000. Antes de esta correccion, payment_amount guardaba el
    # monto nominal completo ($10.000.000) y el excedente de $3.000.000 desaparecia
    # sin dejar rastro en el LiquidationResult.
    events = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("7000000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2026, 1, 10), payload={"amount": Decimal("10000000.00")}, event_type="PAYMENT"),
    ]
    control_rate = Rate.from_percent(Decimal("0.0"))
    engine = LiquidationCore(default_daily_rate=control_rate)

    result = engine.process(events, cutoff_date=date(2026, 1, 10))

    item_pago = next(i for i in result.items if i.balance.event_type == "PAYMENT")
    assert item_pago.payment_amount == Decimal("7000000.00")
    assert item_pago.saldo_a_favor == Decimal("3000000.00")
    assert result.total_payments_applied() == Decimal("7000000.00")
    assert result.final_balance().total() == Decimal("0.00")


def test_engine_pago_exacto_no_genera_saldo_a_favor():
    events = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("500000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2026, 1, 10), payload={"amount": Decimal("500000.00")}, event_type="PAYMENT"),
    ]
    control_rate = Rate.from_percent(Decimal("0.0"))
    engine = LiquidationCore(default_daily_rate=control_rate)

    result = engine.process(events, cutoff_date=date(2026, 1, 10))

    item_pago = next(i for i in result.items if i.balance.event_type == "PAYMENT")
    assert item_pago.payment_amount == Decimal("500000.00")
    assert item_pago.saldo_a_favor == Decimal("0.00")
```

- [ ] **Step 2: Confirmar que falla**

Run: `pytest tests/liquidation/test_engine.py -v -k sobrepago`
Expected: FAIL — `assert item_pago.saldo_a_favor == Decimal("3000000.00")` falla porque `saldo_a_favor` siempre es `0.00` (default) y `payment_amount` es `10000000.00` en vez de `7000000.00`.

- [ ] **Step 3: Corregir `_process_event`**

En `app/engine/liquidation/engine.py`, el método actual (líneas 129-178):

```python
    def _process_event(self, event: Event) -> LiquidationItem:
        concept = event.payload.get("label", event.event_type)
        payment_amount = Decimal("0.00")
        interest_amount = Decimal("0.00")
        indexation_amount = Decimal("0.00")
```

Cambiar para inicializar también `saldo_a_favor`:

```python
    def _process_event(self, event: Event) -> LiquidationItem:
        concept = event.payload.get("label", event.event_type)
        payment_amount = Decimal("0.00")
        interest_amount = Decimal("0.00")
        indexation_amount = Decimal("0.00")
        saldo_a_favor = Decimal("0.00")
```

La rama `PAYMENT` actual:

```python
        elif event.event_type == "PAYMENT":
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            payment_amount = amount
            allocation, new_debt, remainder = AllocationEngine.allocate(amount, self._current_debt, event.date)
            self._current_debt = new_debt
```

Cambiar a:

```python
        elif event.event_type == "PAYMENT":
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            allocation, new_debt, remainder = AllocationEngine.allocate(amount, self._current_debt, event.date)
            self._current_debt = new_debt
            payment_amount = allocation.total_payment
            saldo_a_favor = remainder
```

(`allocation.total_payment` ya es `payment_amount - remainder` — ver `AllocationEngine.allocate`, línea 51 de `allocation.py` — así que refleja exactamente lo que se aplicó a la deuda.)

Y el `return` final del método:

```python
        return LiquidationItem(
            date=event.date,
            concept=concept,
            capital_base=self._capital_base_actual(),
            interest_rate=self._get_rate_for_date(event.date).percent(),
            interest_amount=interest_amount,
            indexation_amount=indexation_amount,
            payment_amount=payment_amount,
            balance=rb,
            rate_source=self._get_rate_source_for_date(event.date),
        )
```

Cambiar a:

```python
        return LiquidationItem(
            date=event.date,
            concept=concept,
            capital_base=self._capital_base_actual(),
            interest_rate=self._get_rate_for_date(event.date).percent(),
            interest_amount=interest_amount,
            indexation_amount=indexation_amount,
            payment_amount=payment_amount,
            balance=rb,
            rate_source=self._get_rate_source_for_date(event.date),
            saldo_a_favor=saldo_a_favor,
        )
```

- [ ] **Step 4: Confirmar que pasa**

Run: `pytest tests/liquidation/test_engine.py -v`
Expected: PASS (los 2 tests nuevos y todos los existentes, incluido `test_engine_processes_chronological_events` que ya verifica `total_payments_applied() == Decimal("500.00")` con un pago que no sobrepasa la deuda — debe seguir en verde sin cambios).

- [ ] **Step 5: Commit**

```bash
git add app/engine/liquidation/engine.py tests/liquidation/test_engine.py
git commit -m "fix(sprint23): capturar remanente de sobrepago como saldo_a_favor en LiquidationCore"
```

---

## Task 3: `LiquidationResult.total_saldo_a_favor()`

**Files:**
- Modify: `app/engine/liquidation/result.py:22-26`
- Test: `tests/liquidation/test_result.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar al final de `tests/liquidation/test_result.py` (agregar también el import de `LiquidationItem`... ya está importado en la línea 3):

```python
def test_liquidation_result_total_saldo_a_favor():
    debt = PendingDebt(Decimal("0"), Decimal("0"), Decimal("0"))
    item_sin_excedente = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Pago exacto",
        capital_base=Decimal("0"),
        interest_rate=Decimal("0"),
        interest_amount=Decimal("0"),
        indexation_amount=Decimal("0"),
        payment_amount=Decimal("500000"),
        balance=RunningBalance(date(2026, 1, 1), debt, "PAYMENT"),
    )
    item_con_excedente = LiquidationItem(
        date=date(2026, 2, 1),
        concept="Pago con excedente",
        capital_base=Decimal("0"),
        interest_rate=Decimal("0"),
        interest_amount=Decimal("0"),
        indexation_amount=Decimal("0"),
        payment_amount=Decimal("7000000"),
        balance=RunningBalance(date(2026, 2, 1), debt, "PAYMENT"),
        saldo_a_favor=Decimal("3000000"),
    )

    result = LiquidationResult([item_sin_excedente, item_con_excedente])

    assert result.total_saldo_a_favor() == Decimal("3000000")
```

- [ ] **Step 2: Confirmar que falla**

Run: `pytest tests/liquidation/test_result.py -v`
Expected: FAIL — `AttributeError: 'LiquidationResult' object has no attribute 'total_saldo_a_favor'`

- [ ] **Step 3: Agregar el método**

En `app/engine/liquidation/result.py`, después de `total_payments_applied` (líneas 25-26):

```python
    def total_payments_applied(self) -> Decimal:
        return sum((item.payment_amount for item in self.items), Decimal("0.00"))
```

Agregar:

```python
    def total_payments_applied(self) -> Decimal:
        return sum((item.payment_amount for item in self.items), Decimal("0.00"))

    def total_saldo_a_favor(self) -> Decimal:
        return sum((item.saldo_a_favor for item in self.items), Decimal("0.00"))
```

- [ ] **Step 4: Confirmar que pasa**

Run: `pytest tests/liquidation/test_result.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/engine/liquidation/result.py tests/liquidation/test_result.py
git commit -m "feat(sprint23): agregar LiquidationResult.total_saldo_a_favor()"
```

---

## Task 4: `deserializar_resultado` ya no lanza `KeyError` con `AuditLog` históricos sin `rate_source`, y preserva `saldo_a_favor` en el round-trip

**Nota agregada tras la revisión de calidad de la Task 1:** `_item_desde_dict` reconstruye `LiquidationItem` con argumentos explícitos por keyword y NO lee `saldo_a_favor` del JSON — hoy es inofensivo porque el campo siempre vale `0.00`, pero en cuanto la Task 2 empiece a poblarlo, `serializar_resultado` (que usa `asdict()`) sí lo va a incluir en el snapshot, y `_item_desde_dict` lo va a descartar silenciosamente al reconstruir, reseteándolo a `0.00`. Eso es exactamente la clase de bug que este sprint corrige (un valor que desaparece sin aviso) — así que este task agrega también esa lectura, con el mismo patrón `.get()` con default que ya usa para snapshots viejos que no tienen la clave.

**Files:**
- Modify: `app/engine/audit/serialization.py:39-63`
- Test: `tests/audit/test_serialization.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/audit/test_serialization.py`:

```python
def test_deserializar_snapshot_antiguo_sin_clave_rate_source_no_lanza_keyerror():
    # Snapshot como los que ya existen en bastium.db, guardados ANTES de que
    # rate_source se agregara a LiquidationItem (commit posterior al que introdujo
    # el motor de auditoria del Sprint 9). AuditLog.resultado_json es append-only,
    # esas filas nunca se reescriben -- deserializar_resultado debe reconstruir con
    # rate_source="N/A" (mismo default que usa el motor sin rate_provider) en vez de
    # lanzar KeyError. Bug real de Sprint 23.
    import json
    snapshot_antiguo = json.dumps({"items": [
        {
            "date": "2026-01-01", "concept": "Abono a capital", "capital_base": "1000000.00",
            "interest_rate": "0.00", "interest_amount": "0.00", "indexation_amount": "0.00",
            "payment_amount": "0.00",
            "balance": {
                "date": "2026-01-01",
                "debt": {"principal": "1000000.00", "interest": "0.00", "indexation": "0.00"},
                "event_type": "IMPUESTO_A_CARGO",
            },
        }
    ]})

    reconstruido = deserializar_resultado(snapshot_antiguo)

    assert reconstruido.items[0].rate_source == "N/A"


def test_deserializar_snapshot_antiguo_sin_clave_saldo_a_favor_no_lanza_keyerror():
    # Mismo razonamiento que el test de rate_source: cualquier AuditLog guardado
    # ANTES de que saldo_a_favor se agregara a LiquidationItem (Sprint 23) no tiene
    # esa clave en su JSON. deserializar_resultado debe reconstruir con
    # saldo_a_favor=Decimal("0.00") (mismo default del dataclass) en vez de lanzar
    # KeyError.
    import json
    snapshot_antiguo = json.dumps({"items": [
        {
            "date": "2026-01-01", "concept": "Abono a capital", "capital_base": "1000000.00",
            "interest_rate": "0.00", "interest_amount": "0.00", "indexation_amount": "0.00",
            "payment_amount": "0.00", "rate_source": "N/A",
            "balance": {
                "date": "2026-01-01",
                "debt": {"principal": "1000000.00", "interest": "0.00", "indexation": "0.00"},
                "event_type": "IMPUESTO_A_CARGO",
            },
        }
    ]})

    reconstruido = deserializar_resultado(snapshot_antiguo)

    assert reconstruido.items[0].saldo_a_favor == Decimal("0.00")


def test_round_trip_preserva_saldo_a_favor_cuando_esta_presente():
    # Round-trip normal (snapshot nuevo, ya con la clave) -- el valor de saldo_a_favor
    # de un sobrepago real debe sobrevivir intacto, no resetearse a 0.00.
    debt = PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 10), debt=debt, event_type="PAYMENT")
    item = LiquidationItem(
        date=date(2026, 1, 10),
        concept="Pago con excedente",
        capital_base=Decimal("0.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("7000000.00"),
        balance=balance,
        saldo_a_favor=Decimal("3000000.00"),
    )
    resultado = LiquidationResult(items=[item])

    reconstruido = deserializar_resultado(serializar_resultado(resultado))

    assert reconstruido.items[0].saldo_a_favor == Decimal("3000000.00")
```

- [ ] **Step 2: Confirmar que fallan**

Run: `pytest tests/audit/test_serialization.py -v -k "rate_source or saldo_a_favor"`
Expected: FAIL — el primer test nuevo con `KeyError: 'rate_source'`; el segundo con `KeyError: 'saldo_a_favor'`; el tercero con `AssertionError` (el valor vuelve como `Decimal("0.00")` en vez de `Decimal("3000000.00")`, porque `_item_desde_dict` todavía no lee esa clave).

- [ ] **Step 3: Corregir `_item_desde_dict`**

En `app/engine/audit/serialization.py`, línea 62:

```python
        rate_source=data["rate_source"],
```

Cambiar a (agregando también la lectura de `saldo_a_favor`, mismo patrón `.get()` con el mismo default que ya usa el dataclass):

```python
        rate_source=data.get("rate_source", "N/A"),
        saldo_a_favor=Decimal(data.get("saldo_a_favor", "0.00")),
```

- [ ] **Step 4: Confirmar que pasan**

Run: `pytest tests/audit/test_serialization.py -v`
Expected: PASS (incluido `test_deserializar_con_json_incompleto_lanza_key_error`, que sigue fallando con `KeyError` porque ese JSON tampoco tiene `concept`/`capital_base`/etc., que siguen accediéndose sin `.get()` — ese test verifica que datos genuinamente incompletos sigan fallando ruidosamente, solo `rate_source` y `saldo_a_favor` tienen un default legítimo conocido).

- [ ] **Step 5: Commit**

```bash
git add app/engine/audit/serialization.py tests/audit/test_serialization.py
git commit -m "fix(sprint23): reconstruir AuditLog historico sin rate_source ni saldo_a_favor sin lanzar KeyError"
```

---

## Task 5: Advertencia no bloqueante de posible sobrepago en `AbonoFormDialog`

**Decisión de diseño (confirmada con el usuario):** el motor siempre acepta y refleja el sobrepago como `saldo_a_favor` (Tasks 1-3, ya es la corrección real del bug). Adicionalmente, la GUI de captura de abonos muestra una advertencia **no bloqueante** (nunca impide guardar) cuando la suma de abonos de una obligación parece superar su valor registrado — heurística simple (suma de abonos vs. `Obligacion.valor`, sin recalcular intereses/indexación), documentada como aproximada.

**Files:**
- Modify: `app/views/abonos.py`
- Test: `tests/views/test_abonos.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/views/test_abonos.py`:

```python
def test_abono_que_supera_el_valor_de_la_obligacion_muestra_advertencia_no_bloqueante(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)  # valor=427900.00

    avisos = []
    monkeypatch.setattr(
        "app.views.abonos.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("500000.00")
    dialog.campo_fecha.setDate(date(2026, 1, 15))

    abono_id = dialog.guardar()

    # La advertencia se muestra...
    assert len(avisos) == 1
    assert "sobrepago" in avisos[0][0].lower()
    # ...pero NO bloquea el guardado.
    session = session_module.get_session()
    guardado = session.query(Abono).filter_by(obligacion_id=obligacion_id).one()
    assert guardado.monto == Decimal("500000.00")
    assert guardado.id == abono_id
    session.close()


def test_abono_dentro_del_valor_de_la_obligacion_no_muestra_advertencia(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)  # valor=427900.00

    avisos = []
    monkeypatch.setattr(
        "app.views.abonos.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("100000.00")
    dialog.campo_fecha.setDate(date(2026, 1, 15))

    dialog.guardar()

    assert len(avisos) == 0


def test_abonos_acumulados_que_superan_el_valor_muestran_advertencia(qtbot, monkeypatch):
    # El primer abono (300000) no supera el valor (427900). El segundo (200000) hace
    # que la suma acumulada (500000) si lo supere -- la heuristica debe sumar abonos
    # previos, no comparar solo el monto del abono nuevo contra el valor.
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    monkeypatch.setattr("app.views.abonos.QMessageBox.warning", lambda *a, **k: None)
    primer_dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(primer_dialog)
    primer_dialog.campo_monto.setText("300000.00")
    primer_dialog.campo_fecha.setDate(date(2026, 1, 10))
    primer_dialog.guardar()

    avisos = []
    monkeypatch.setattr(
        "app.views.abonos.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )
    segundo_dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(segundo_dialog)
    segundo_dialog.campo_monto.setText("200000.00")
    segundo_dialog.campo_fecha.setDate(date(2026, 1, 20))
    segundo_dialog.guardar()

    assert len(avisos) == 1
```

- [ ] **Step 2: Confirmar que fallan**

Run: `pytest tests/views/test_abonos.py -v`
Expected: FAIL — los 3 tests nuevos fallan porque `avisos` queda vacío en los casos que esperan advertencia (`assert len(avisos) == 1` con `len(avisos) == 0`); el test de "no advertencia" ya pasa hoy (todavía no rompe nada, pero se agrega para fijar el comportamiento antes del cambio).

- [ ] **Step 3: Implementar la advertencia**

En `app/views/abonos.py`, el import actual (línea 8):

```python
from database.models import Abono
```

Cambiar a:

```python
from database.models import Abono, Obligacion
```

El método `guardar()` actual (líneas 32-55):

```python
    def guardar(self) -> int:
        try:
            monto = Decimal(self.campo_monto.text())
        except InvalidOperation as error:
            raise ValueError("El monto debe ser un numero valido.") from error

        if monto <= Decimal("0"):
            raise ValueError("El monto del abono debe ser mayor que cero.")

        qdate = self.campo_fecha.date()
        fecha = date(qdate.year(), qdate.month(), qdate.day())

        session = session_module.get_session()
        abono = Abono(
            obligacion_id=self._obligacion_id,
            fecha=fecha,
            monto=monto,
            referencia=self.campo_referencia.text().strip() or None,
        )
        session.add(abono)
        session.commit()
        abono_id = abono.id
        session.close()
        return abono_id
```

Cambiar a:

```python
    def guardar(self) -> int:
        try:
            monto = Decimal(self.campo_monto.text())
        except InvalidOperation as error:
            raise ValueError("El monto debe ser un numero valido.") from error

        if monto <= Decimal("0"):
            raise ValueError("El monto del abono debe ser mayor que cero.")

        qdate = self.campo_fecha.date()
        fecha = date(qdate.year(), qdate.month(), qdate.day())

        session = session_module.get_session()
        obligacion = session.get(Obligacion, self._obligacion_id)
        abonos_previos = sum((a.monto for a in obligacion.abonos), Decimal("0.00"))
        if abonos_previos + monto > obligacion.valor:
            # Heuristica no bloqueante: compara solo capital contra abonos, sin
            # recalcular intereses/indexacion (eso requeriria correr el motor de
            # liquidacion completo). El sobrepago real, si lo hay, siempre queda
            # reflejado con precision como saldo_a_favor al liquidar (Sprint 23).
            QMessageBox.warning(
                self,
                "Posible sobrepago",
                "El total de abonos para esta obligación "
                f"(${abonos_previos + monto}) supera el valor registrado "
                f"(${obligacion.valor}). Verifique el monto antes de continuar: "
                "el excedente quedará reflejado como saldo a favor al liquidar.",
            )

        abono = Abono(
            obligacion_id=self._obligacion_id,
            fecha=fecha,
            monto=monto,
            referencia=self.campo_referencia.text().strip() or None,
        )
        session.add(abono)
        session.commit()
        abono_id = abono.id
        session.close()
        return abono_id
```

- [ ] **Step 4: Confirmar que pasan**

Run: `pytest tests/views/test_abonos.py -v`
Expected: PASS (los 5 tests: los 2 originales + los 3 nuevos).

- [ ] **Step 5: Commit**

```bash
git add app/views/abonos.py tests/views/test_abonos.py
git commit -m "feat(sprint23): advertencia no bloqueante de posible sobrepago al guardar un abono"
```

---

## Task 6: Documentar en `README.md` el comportamiento de `rate_source` en reconstrucciones históricas

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Agregar la nota**

En `README.md`, dentro de la sección `## Estado actual (2026-07-31)`, después del párrafo que termina en (línea 48):

```
queda registrada en un historial de auditoría por expediente (quién, cuándo, con qué área y fecha de
corte), con reconstrucción exacta de un cálculo pasado con solo hacer doble clic sobre su fila.
```

Agregar un párrafo nuevo inmediatamente después (antes de `✅ **Parámetros legales versionados:**`):

```markdown

ℹ️ **Nota sobre auditorías históricas:** las liquidaciones auditadas antes de que el campo
`rate_source` se agregara al motor (posterior al Sprint 9) se reconstruyen con `rate_source="N/A"`
en vez de fallar — `AuditLog.resultado_json` es append-only por diseño, esas filas nunca se
reescriben, así que no existe (ni se planea) un script de backfill que edite el JSON histórico sin
romper esa garantía de append-only (Sprint 23).
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(sprint23): documentar reconstruccion de AuditLog historico sin rate_source"
```

---

## Task 7: Suite completa en verde

**Files:** Ninguno (verificación final).

- [ ] **Step 1: Correr toda la suite**

Run: `pytest`
Expected: todos los tests en verde, incluidos los 9 tests nuevos de este sprint (2 en `test_models.py`, 2 en `test_engine.py`, 1 en `test_result.py`, 1 en `test_serialization.py`, 3 en `test_abonos.py`).

- [ ] **Step 2: Verificar manualmente el alcance real del bug de `rate_source` (recomendado por el spec, no bloqueante para cerrar el sprint)**

Abrir la app contra el `bastium.db` real de producción, ir al historial de auditoría de un expediente con liquidaciones anteriores a la fecha del commit que agregó `rate_source`, y hacer doble clic para reconstruir. Confirmar que ya no lanza error y que las tasas de esas filas se muestran como "N/A" (no un valor inventado).

---

## Self-Review (spec coverage)

- Bug 1 (sobrepago descartado): cubierto por Tasks 1-3 — campo nuevo, corrección de `_process_event`, agregado a `LiquidationResult`, test de integración end-to-end en `LiquidationCore.process()` (Task 2) tal como exige la Definición de Hecho.
- Bug 2 (`KeyError` en reconstrucción): cubierto por Task 4 — `.get()` con default, test con `AuditLog` sintético sin la clave, tal como exige la Definición de Hecho. Ampliado (hallazgo del revisor de calidad de la Task 1) para también deserializar `saldo_a_favor`, evitando que el round-trip de auditoría resetee silenciosamente el saldo a favor de un sobrepago real a `0.00`.
- Decisión de diseño con el usuario: resuelta (aceptar en el motor + advertir no bloqueante en la GUI) y cubierta por Task 5.
- Nota de documentación sugerida por el spec (`README.md` sobre backfill): cubierta por Task 6.
- Riesgo/nota técnica del spec (verificar alcance real en `bastium.db` de producción): cubierto por Task 7, Step 2.
