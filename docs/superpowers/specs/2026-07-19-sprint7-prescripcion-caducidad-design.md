# Diseño — Sprint 7: Motor de prescripción y caducidad

**Fecha:** 2026-07-19
**Origen:** `Pendientes.md`, Sprint 7 — Motor de prescripción y caducidad.

## Contexto

Ningún motor de prescripción/caducidad existe hoy en el código (confirmado por grep). El Sprint 6
(calendario de días hábiles) dejó dos notas explícitas relevantes para este sprint:

1. `EstadoTermino` (`app/engine/temporal/terminos.py`) tiene el conteo de días hábiles
   (`CalendarUtils.dias_habiles_entre`) cableado directamente. Prescripción/caducidad son plazos en
   años/meses **calendario**, no días hábiles judiciales — reutilizar `EstadoTermino` tal cual
   subestimaría el tiempo transcurrido.
2. `CalendarUtils.vencimiento_calendario(fecha_inicio, meses)` ya existe y ya resuelve exactamente la
   regla que necesita este sprint: vence el mismo día numérico del mes/año destino, topa al último día
   real del mes si el día no existe (ej. 30 de febrero), y traslada al siguiente día hábil si el
   vencimiento cae en festivo/fin de semana (PDF pág. 24).

## Decisión de arquitectura

`app/engine/temporal/prescripcion.py` es un módulo **nuevo e independiente**, no una extensión de
`EstadoTermino`. No comparte la máquina de estados interrumpir/suspender/reanudar de Sprint 6 — expone
funciones puras basadas en fechas calendario, construidas sobre `CalendarUtils.vencimiento_calendario`.
Se prefirió esto sobre generalizar `EstadoTermino` con un contador de días inyectable porque prescripción/
caducidad no necesitan pausar y reanudar un reloj de días consumidos — solo necesitan una fecha límite
calculada desde una fecha de origen, más una función de recálculo cuando hay interrupción por demanda.
Generalizar `EstadoTermino` habría sido sobre-ingeniería para un caso de uso que no la necesita.

## Tabla de prescripción consolidada

El PDF trae estos plazos dispersos en varias secciones (págs. 16/19, 32, 35, 40, 42-45). Se consolidan
en un solo `enum TipoAccion` y un diccionario de meses:

| `TipoAccion` | Plazo | Fuente |
|---|---|---|
| `EJECUTIVA` | 5 años (60 meses) | PDF págs. 16/19, 42, 43, 45 |
| `ORDINARIA` | 10 años (120 meses) | Art. 2536 C.C. (conocimiento jurídico general — el PDF no lo trae explícito en una tabla propia, pero `Pendientes.md` ya lo asume y es la regla real vigente) |
| `HONORARIOS_PROFESIONALES` | 3 años (36 meses) | PDF pág. 35 |
| `CAMBIARIA_DIRECTA` | 3 años (36 meses) | PDF pág. 45; Art. 789 C.Co. |
| `CAMBIARIA_REGRESO_TENEDOR` | 1 año (12 meses) | PDF pág. 45; Art. 790 C.Co. |
| `CAMBIARIA_REGRESO_ENTRE_OBLIGADOS` | 6 meses | PDF pág. 32 ("en el cheque, la acción cambiaria caduca en 6 meses") + Art. 791 C.Co. |

**Nota sobre la inconsistencia detectada:** la pág. 32 del PDF llama "caducidad" al plazo de 6 meses del
cheque, mientras que la pág. 45 da cifras específicas de **prescripción** cambiaria (directa 3 años,
regreso 1 año) que coinciden con los arts. 789-790 C.Co. El Código de Comercio real tiene un tercer
supuesto (art. 791): la acción de quien pagó como obligado de regreso contra los demás obligados de
regreso, que prescribe en 6 meses. Se decidió con el usuario modelar los tres como subtipos de
**prescripción** (no de caducidad), reconciliando la mención de la pág. 32 como este tercer supuesto real
del C.Co., en vez de tratarla como un error aislado del documento.

## Funciones públicas

### `calcular_prescripcion(fecha_exigibilidad: date, tipo_accion: TipoAccion) -> date`

Delega en `CalendarUtils.vencimiento_calendario(fecha_exigibilidad, PLAZOS_PRESCRIPCION_MESES[tipo_accion])`.

### `calcular_caducidad(fecha_hecho: date, tipo_proceso: str, plazo_meses_manual: int | None = None) -> date`

El PDF solo confirma un caso concreto de caducidad con plazo explícito fuera del ya cubierto por
prescripción cambiaria: impugnación de ineficacia societaria, 5 años (pág. 40). Catálogo hardcodeado:

```python
PLAZOS_CADUCIDAD_MESES_CONOCIDOS = {
    "IMPUGNACION_INEFICACIA_SOCIETARIA": 60,
}
```

Si `tipo_proceso` está en el catálogo, se usa ese plazo (ignorando `plazo_meses_manual` si se pasó,
o validando que coincida — a decidir en implementación, ver Riesgos). Si no está en el catálogo,
`plazo_meses_manual` es obligatorio; si es `None`, se lanza `ValueError` explicando que no hay fuente
para ese tipo de proceso — mismo patrón que `costas_pct_manual` en `HonorariosStrategy` (Sprint 4): no
inventar plazos sin respaldo documental.

**Fuera de alcance de este sprint:** la suspensión de caducidad por conciliación extrajudicial (máximo 3
meses, PDF pág. 25) no se modela — no hay ningún caso de uso en el sprint que la requiera todavía.
Documentado como limitación conocida, no como omisión por descuido.

### `filtrar_cuotas_prescritas(eventos: List[Event], fecha_corte: date, tipo_accion: TipoAccion = TipoAccion.EJECUTIVA) -> tuple[List[Event], List[Event]]`

Soporta prescripción parcial en obligaciones de tracto sucesivo (PDF pág. 32: cuotas alimentarias/cánones,
cada una con su propio timestamp de vencimiento vía los `Event` que ya genera `FamilyScheduler`). Para
cada evento, calcula `calcular_prescripcion(evento.date, tipo_accion)`; si esa fecha límite es `<=
fecha_corte`, el evento va a la lista `prescritas`; si no, va a `vivas`. Devuelve `(vivas, prescritas)`,
sin mutar los eventos de entrada. `tipo_accion` por defecto es `EJECUTIVA` porque el PDF (pág. 32) usa el
plazo de 5 años como referencia para cuotas alimentarias vencidas.

### `fecha_interrupcion_efectiva(fecha_radicacion: date, fecha_notificacion: date) -> date`

Implementa la regla de retroactividad de la interrupción por demanda (PDF pág. 25 y pág. 68: "si se
notifica dentro del año, el efecto interruptor se retrotrae a la fecha de la demanda"). Si
`(fecha_notificacion - fecha_radicacion).days <= 365`, retorna `fecha_radicacion`; si no, retorna
`fecha_notificacion`. Lanza `ValueError` si `fecha_notificacion < fecha_radicacion`. El resultado se usa
como nueva `fecha_exigibilidad` para una segunda llamada a `calcular_prescripcion` (recompone el
cómputo desde cero, equivalente al "reset" que hace `interrumpir()` en `EstadoTermino`, pero en unidades
calendario).

## Excepciones de dominio

Ninguna nueva. Este sprint excluye explícitamente la integración con la GUI y con
`area_strategy.py`/`UniversalLiquidationService` (eso es un sprint de UI/integración aparte, según
`Pendientes.md`). Por tanto no se agregan `ObligacionPrescritaError`/`DemandaCaducadaError` — el motor
solo expone cálculo puro (fechas límite y listas filtradas); decidir si eso aborta una liquidación es
responsabilidad de una integración futura.

## Testing

`tests/temporal/test_prescripcion.py`, con TDD:

- Un test por cada valor de `TipoAccion` verificando la fecha límite exacta desde una fecha de
  exigibilidad conocida, incluyendo un caso de desborde de fin de mes (ej. exigibilidad 31 de enero +
  plazo en meses/años que cae en un mes más corto).
- `calcular_caducidad`: caso con el tipo conocido (impugnación societaria), caso con
  `plazo_meses_manual` para un tipo no catalogado, y caso que lanza `ValueError` si no se provee plazo
  para un tipo desconocido.
- `filtrar_cuotas_prescritas`: escenario con `FamilyScheduler` generando cuotas mensuales reales que
  mezclan cuotas de hace más de 5 años con cuotas recientes — verificar el split correcto (este es el
  test explícito que pide la Definición de Hecho del sprint en `Pendientes.md`).
- `fecha_interrupcion_efectiva`: caso `<= 365` días (retrotrae a la radicación), caso `> 365` días (no
  retrotrae), y caso de fechas invertidas (`ValueError`).
- Suite completa del proyecto en verde al cierre del sprint.

## Riesgos / notas abiertas para la fase de implementación

- Definir en el plan de implementación qué hacer si `calcular_caducidad` recibe simultáneamente un
  `tipo_proceso` catalogado **y** un `plazo_meses_manual` no `None` — ignorar el manual con una nota, o
  validar que coincidan y lanzar error si no. Es un detalle menor de implementación, no una decisión de
  producto.
- El plazo de `ORDINARIA` (10 años) se apoya en conocimiento jurídico general (Art. 2536 C.C.), no en una
  cita textual del PDF como los demás — dejar la referencia normativa explícita en el docstring de la
  constante para que quede auditable.
