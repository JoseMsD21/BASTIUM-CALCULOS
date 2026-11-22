# Motor de Pagos (Imputacion)

## Que hace
Aplica un pago recibido contra una deuda pendiente, siguiendo la prelacion legal estricta:
0. Costas procesales aprobadas (Sprint 79)
1. Indexacion
2. Intereses
3. Capital

### Costas procesales (Sprint 79)
Respuesta del despacho (16/11/2026): las costas procesales (expensas y agencias en derecho) NUNCA
generan interes, en ninguna area ni algoritmo (incluido "Suma Unica"), y se suman "en seco" al final:
`Gran_Total = Capital_Indexado + Intereses_Mora + Costas_Aprobadas`. En la imputacion se pagan
PRIMERO (Arts. 1629, 1653, 2495 C.C. y 446 CGP).

- `PendingDebt.costas` es un 4o componente (default `0.00`), fuera de `principal`; entra en
  `total()` pero nunca en `LiquidationCore._capital_base_actual()`.
- El evento `COSTAS_PROCESALES` ya no esta en `_capital_concepts`: tiene su propia rama en
  `LiquidationCore._process_event` (`BalanceEngine.add_costas`).
- `AllocationEngine.allocate` y `allocate_capital_primero` (Sprint 75) imputan primero a costas
  (`PaymentAllocation.to_costas`) y despues siguen su orden de siempre.
- La misma respuesta pone intereses ANTES que indexacion; eso contradice el orden vigente
  (indexacion -> intereses -> capital) y NO se cambio: queda pendiente de confirmacion aparte.
- Reportes: `ReportSummaryBuilder` agrega `saldo_final_costas` solo cuando hay costas; PDF/Word lo
  muestran como fila "Costas Procesales (no generan interés)" justo antes del gran total, y la
  pantalla de resultado una etiqueta equivalente. La columna "Saldo capital" de la cronologia ya no
  incluye costas; "Saldo total" si.
- Auditoria: `deserializar_resultado` lee `costas` con `.get(..., "0.00")` (snapshots anteriores).

### Suma Unica con abonos (Sprint 104)
`AllocationEngine.allocate_intereses_primero`: costas -> intereses -> indexacion -> capital (Art. 1653
C.C., algoritmo tramo a tramo del despacho). Solo la usa `CivilFamiliaStrategy` para obligaciones PUNTUAL
con Suma Unica y abonos (ver `03_motor_indexacion.md`); el resto conserva `allocate`/`allocate_capital_primero`.

## Componentes
- `app/engine/liquidation/allocation.py`: `AllocationEngine.allocate(payment_amount, current_debt,
  payment_date)` retorna `(PaymentAllocation, nuevo PendingDebt, remainder)`. El `remainder` es el
  sobrante si el pago excede toda la deuda.
- `app/domain/obligation/payment.py`: `Payment(date, amount, reference)` — la forma en que un abono
  entra al motor.
- `app/engine/liquidation/engine.py` (`LiquidationCore._process_event`): cuando un `Event` tiene
  `event_type == "PAYMENT"`, delega en `AllocationEngine.allocate`.

## Como se usa en el MVP
Cada `Abono` capturado en la GUI se convierte en un `Payment` (`CivilFamiliaStrategy`) y se mezcla
cronologicamente con los eventos de causacion antes de procesarse.

## Pendiente (no implementado aun)
- Validadores de pago anomalo (pago mayor al saldo, duplicado, sin soporte).
- Reglas de imputacion alternativas por regimen (ej. tributario: sanciones -> intereses -> impuesto).
- Compensacion, novacion, remision, confusion.

Ver `docs/Pendientes.md`.
