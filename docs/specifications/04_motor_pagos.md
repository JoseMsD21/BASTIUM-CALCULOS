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

### Tributario: imputacion proporcional (Art. 804 E.T., Sprint 84 seguimiento)
Respuesta del despacho (16/11/2026): "la imputacion proporcional es imperativa (no se imputa
primero a intereses como en lo civil)" y aplica a toda obligacion tributaria. Contexto de la
pregunta: "el abono se reparte proporcionalmente entre capital/sancion/interes segun el peso de
cada uno en la deuda total".

- `AllocationEngine.allocate_proporcional_art_804` (solo la usa `TributarioStrategy`; las demas
  areas siguen con `allocate`/`allocate_capital_primero`).
- Costas primero (Sprint 79). Con el resto (`disponible`):
  `imputado_i = disponible x saldo_i / (impuesto + sanciones + intereses)`, con los saldos de la
  obligacion en la fecha del abono (intereses causados hasta ese dia incluidos). Buckets:
  impuesto = `principal`; sanciones y actualizacion Art. 867-1 = `indexation`; intereses =
  `interest`.
- Redondeo: cada parte al centavo (HALF_UP); el centavo residual va al impuesto, de modo que la
  suma cuadra exactamente con el abono. Si el redondeo excediera el saldo del impuesto, el exceso
  pasa a intereses y luego a sanciones (nunca quedan saldos negativos).
- Si el abono cubre toda la deuda, se paga todo y el exceso es remanente (saldo a favor).
- Limite: el reparto es dentro de la obligacion a la que pertenece el abono
  (`Abono.obligacion_id`, Sprint 21). Un impuesto y su sancion capturados como 2 obligaciones
  no comparten el abono.
- Ejemplo verificado a mano (prueba `test_abono_parcial_se_imputa_proporcionalmente_...`):
  impuesto 10.000.000 exigible 2024-03-01, intereses 85.519,10 al 2024-03-11; abono 1.000.000
  -> 8.479,39 a intereses y 991.520,61 al impuesto.

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
- Reparto de un mismo abono entre varias obligaciones tributarias del expediente (hoy cada abono
  pertenece a una sola obligacion).
- Compensacion, novacion, remision, confusion.

Ver `docs/Pendientes.md`.
