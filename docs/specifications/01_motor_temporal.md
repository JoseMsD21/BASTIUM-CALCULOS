# Motor Temporal

## Que hace
Genera la cronologia de eventos (`Event`) que alimenta al motor de liquidacion, a partir de reglas de
recurrencia (mensual o anual), y resuelve calendario de dias habiles, terminos procesales y
prescripcion/caducidad.

## Componentes
- `app/engine/temporal/schedulers/base.py`: `Event(date, payload, event_type)` y la interfaz `Scheduler`.
- `app/engine/temporal/schedulers/recurring.py`: `RecurringRule(amount, frequency, day, month)` y
  `RecurringScheduler`, que expande una regla mensual/anual en una lista de `Event` entre `start` y `end`,
  usando `CalendarUtils.safe_create_date` para evitar fechas invalidas (ej. 30 de febrero).
- `app/engine/temporal/schedulers/family.py`: `FamilyScheduler`, especializado en Derecho de Familia.
  `add_monthly_obligation(amount, concept, due_day, category="CHILD_SUPPORT")` registra una cuota mensual;
  `generate(start, end)` la expande y ordena cronologicamente.
- `app/engine/temporal/schedulers/civil.py`: `CivilIndemnityScheduler`, para sentencias de Responsabilidad
  Civil Extracontractual — consolida los rubros indemnizatorios en la fecha del hecho danoso.
- `app/engine/temporal/schedulers/labor.py`: `LaborScheduler`, genera las 5 prestaciones sociales
  estatutarias de una liquidacion final de contrato (cesantias, intereses a cesantias, prima junio/
  diciembre, vacaciones), todas exigibles en la fecha de terminacion (Art. 65 CST).
- `app/engine/time/calendar.py`: `CalendarUtils` — calendario de dias habiles judiciales con festivos
  colombianos (`es_dia_habil`, `sumar_dias_habiles`, `dias_habiles_entre`, `notificacion_surtida_el`,
  `vencimiento_calendario`), ademas de `safe_create_date` para desbordes de mes.
- `app/engine/temporal/terminos.py`: `EstadoTermino` (inmutable) y las funciones puras
  `iniciar_termino`/`dias_restantes`/`esta_vencido`/`interrumpir`/`suspender`/`reanudar`, para el manejo de
  terminos procesales con interrupcion y suspension.
- `app/engine/temporal/prescripcion.py`: motor de prescripcion y caducidad, con los plazos legales
  consultables via `parametro_service` (Sprint 13).

## Como se usa en el MVP
`CivilFamiliaStrategy` (`app/services/area_strategy.py`) usa `FamilyScheduler` para expandir obligaciones
de tipo `RECURRENTE` en eventos mensuales antes de pasarlos al motor de liquidacion. `LaboralStrategy` usa
`LaborScheduler` para el finiquito de un contrato terminado.

## Pendiente (no implementado aun)
- Modulo pensional (IBL, tasa de reemplazo, densidad de semanas) — ver `Pendientes.md`, Sprint 17.
- `EstadoTermino`/`terminos.py` todavia no esta conectado a ninguna pantalla de la GUI — hoy sirve como base
  interna para el motor de prescripcion y caducidad.

Ver `Pendientes.md` para el orden de implementacion.
