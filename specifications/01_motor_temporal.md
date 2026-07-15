# Motor Temporal

## Que hace
Genera la cronologia de eventos (`Event`) que alimenta al motor de liquidacion, a partir de reglas de
recurrencia (mensual o anual).

## Componentes
- `app/engine/temporal/schedulers/base.py`: `Event(date, payload, event_type)` y la interfaz `Scheduler`.
- `app/engine/temporal/schedulers/recurring.py`: `RecurringRule(amount, frequency, day, month)` y
  `RecurringScheduler`, que expande una regla mensual/anual en una lista de `Event` entre `start` y `end`,
  usando `CalendarUtils.safe_create_date` para evitar fechas invalidas (ej. 30 de febrero).
- `app/engine/temporal/schedulers/family.py`: `FamilyScheduler`, especializado en Derecho de Familia.
  `add_monthly_obligation(amount, concept, due_day, category="CHILD_SUPPORT")` registra una cuota mensual;
  `generate(start, end)` la expande y ordena cronologicamente.
- `app/engine/temporal/schedulers/civil.py`, `labor.py`: existen como archivos pero aun no tienen logica
  equivalente para esas areas (ver `Pendientes.md`).

## Como se usa en el MVP
`CivilFamiliaStrategy` (`app/services/area_strategy.py`) usa `FamilyScheduler` para expandir obligaciones
de tipo `RECURRENTE` en eventos mensuales antes de pasarlos al motor de liquidacion.

## Pendiente (no implementado aun)
- Calendario de dias habiles / festivos (`app/engine/time/calendar.py` solo resuelve desbordes de mes).
- Suspension / interrupcion de terminos procesales.
- Motor de prescripcion y caducidad.

Ver `Pendientes.md` para el orden de implementacion.
