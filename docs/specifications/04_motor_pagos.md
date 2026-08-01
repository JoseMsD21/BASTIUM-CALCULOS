# Motor de Pagos (Imputacion)

## Que hace
Aplica un pago recibido contra una deuda pendiente, siguiendo la prelacion legal estricta:
1. Indexacion
2. Intereses
3. Capital

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

Ver `Pendientes.md`.
