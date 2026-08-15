# Sprint 75 — Cuotas recurrentes en todas las áreas, con selección de pago por rango e imputación en cascada

**Fecha:** 2026-08-14
**Origen:** `docs/Pendientes.md`, sección "Sprint 75" (reporte del usuario 2026-08-13). Diseño discutido con
el usuario en brainstorming el 2026-08-14 antes de codificar, por indicación explícita de Pendientes.md
("alta complejidad, no asumir").

## Problema

El Sprint 41 construyó generación real de cuotas mensuales (`Obligacion` PUNTUAL hijas de una obligación
RECURRENTE, con reajuste anual SMMLV/IPC) y abonos por cuota individual, pero **limitado a
Civil/Familia** — las otras 5 áreas siguen usando `RecurringScheduler`, que expande la recurrencia solo
de forma efímera dentro de `liquidar()`, nunca como filas persistidas y seleccionables antes de liquidar.
Tampoco existe hoy: (1) selección de pago por rango de cuotas (solo cuota-por-cuota), ni (2) una lógica de
imputación en cascada donde un abono grande cubre capital de la cuota más reciente primero, luego
capital+interés de las anteriores, dejando intereses ya generados "congelados" sin seguir acumulando sobre
capital ya pagado — distinta del orden general que usa `AllocationEngine.allocate()` hoy
(indexación→interés→capital, `app/engine/liquidation/allocation.py:16-64`).

## Decisiones de diseño tomadas con el usuario (2026-08-14)

1. **Reajuste anual opcional al generalizar:** `generar_cuotas_mensuales` deja de exigir
   `tipo_reajuste_anual` SMMLV/IPC. Si la obligación no tiene reajuste, el capital se repite igual cada
   mes — necesario porque fuera de Familia lo común es capital fijo (salarios, arriendos, cuotas
   comerciales), no reajuste indexado.
2. **La cascada aplica solo a cuotas-hija, nunca al orden general:** `AllocationEngine`/`LiquidationCore`
   mantienen su comportamiento actual (indexación→interés→capital) para toda obligación que NO sea una
   cuota-hija. La estrategia capital-primero es exclusiva de obligaciones PUNTUAL con
   `obligacion_padre_id` seteado (cuota generada por recurrencia) — aplica a **todos** los abonos de esa
   cuota, sin importar si se registraron por el flujo de rango nuevo o por `AbonoFormDialog` individual ya
   existente. El comportamiento depende del tipo de obligación, no de cómo se cargó el pago.
3. **Selección por rango y selección individual conviven:** el rango es una forma más rápida de marcar
   varias cuotas a la vez; `AbonoFormDialog` (Sprint 41) se mantiene intacto para abonos sobre una sola
   cuota.
4. **Un `Abono` real por cuota tocada, sin cambiar el modelo `Abono`:** el usuario ingresa un monto total y
   una fecha; el motor de cascada calcula cuánto corresponde a cada cuota y crea automáticamente un
   `Abono` por cada una tocada (FK normal a su cuota, editable/eliminable individualmente después, igual
   que hoy). No se introduce ninguna entidad de agrupación ("pago compuesto").
5. **Orden de imputación intercambiable, split calculado en el momento de liquidar (no precalculado
   aparte):** se agrega un parámetro de estrategia a `LiquidationCore`/`AllocationEngine`. La estrategia
   por defecto (indexación→interés→capital) no cambia para ninguna de las 6 áreas. La nueva estrategia
   capital-primero se activa según el punto 2. El motor de cascada usa la misma estrategia en modo
   solo-lectura para *proyectar* cuánto le tocará a cada cuota antes de crear los `Abono`; cuando esos
   `Abono` se liquidan después en la corrida real, el mismo motor con la misma estrategia reproduce
   exactamente la misma cifra — una sola fuente de verdad.

## Alcance

### 1. `app/services/reajuste_anual.py` — generalizar a las 6 áreas

- `generar_cuotas_mensuales`: quitar el `raise ValueError` cuando `tipo_reajuste_anual == NINGUNO`; en ese
  caso `capital_actual` nunca se reajusta (se salta la llamada a `_reajustar_capital`, el resto del bucle
  mensual no cambia).
- Sin cambios en la firma pública ni en la idempotencia ya existente (cuotas ya generadas se retornan tal
  cual).

### 2. `app/services/area_strategy.py` — extender el patrón de `CivilFamiliaStrategy` a las 5 áreas restantes

- `ComercialStrategy`, `LaboralStrategy`, `SancionatorioStrategy`, `HonorariosStrategy`,
  `TributarioStrategy` ganan el mismo bloque que hoy solo tiene `CivilFamiliaStrategy.liquidar()`
  (`area_strategy.py:290-316`): detectar `ids_con_cuotas_generadas` (padres con hijas ya persistidas) y
  no emitir eventos de capital duplicados para el padre cuando ya tiene cuotas hijas
  (`_eventos_de_obligacion`, mismo criterio que `area_strategy.py:383-388`).
- Reutiliza `_liquidar_por_obligacion`/`_fusionar_resultados` ya existentes — no se duplica ese mecanismo
  por área.

### 3. `app/engine/liquidation/allocation.py` y `app/engine/liquidation/engine.py` — estrategia intercambiable

- `AllocationEngine` gana un segundo método (o una estrategia parametrizable) `allocate_capital_primero`:
  capital primero, luego interés, sin indexación tratada aparte (las cuotas-hija no llevan indexación
  propia — heredan la de su obligación padre si aplica, fuera de alcance recalcularla aquí).
- `LiquidationCore.__init__` gana un parámetro opcional (ej. `estrategia_imputacion`, por defecto la
  actual) que `_process_event` usa en vez de llamar `AllocationEngine.allocate` directo
  (`engine.py:186-193`).
- `_liquidar_por_obligacion` (`area_strategy.py:92-150`) pasa la estrategia capital-primero cuando la
  `Obligacion` que está procesando tiene `obligacion_padre_id` no nulo.

### 4. Motor de cascada nuevo — `app/services/cascada_cuotas.py`

- Función `distribuir_pago_en_cascada(cuotas: list[Obligacion], monto_total: Decimal, fecha_pago: date) ->
  list[tuple[Obligacion, Decimal]]`. `cuotas` ya vienen ordenadas de más reciente a más antigua (lo decide
  el caller, según el rango/selección del usuario).
- Por cada cuota, en orden: consulta su deuda pendiente a `fecha_pago` (vía `UniversalLiquidationService`
  en modo solo-lectura, sin persistir), aplica `AllocationEngine.allocate_capital_primero` con el monto
  restante, registra `(cuota, monto_asignado)` si > 0, resta del remanente. Se detiene cuando el remanente
  llega a 0 o se acaban las cuotas de la lista.
- Si sobra remanente después de recorrer todas las cuotas seleccionadas: se retorna aparte (no se reparte
  fuera de la selección) para que el caller decida qué hacer (ver "Manejo de errores").
- Por cada tupla con `monto_asignado > 0`, el caller (diálogo de UI) crea un `Abono` real vía el mismo
  helper `guardar_o_actualizar` que ya usa `AbonoFormDialog` (`app/views/abonos.py`).

### 5. UI — `app/views/expediente_detalle.py` y diálogo nuevo `PagoPorRangoDialog`

- `tabla_obligaciones` gana selección múltiple contigua (rango) — primera vez que este patrón se usa en el
  proyecto (confirmado por investigación: ninguna tabla existente tiene multi-select ni checkboxes de
  fila). `setSelectionMode(QAbstractItemView.ContiguousSelection)` sobre las filas que correspondan a
  cuotas-hija de una misma obligación recurrente (deshabilitar/ignorar selección mixta con obligaciones no
  relacionadas).
- Botón nuevo junto a "Agregar abono" (ej. "Pagar cuotas seleccionadas") abre `PagoPorRangoDialog(cuotas
  seleccionadas)`: monto + fecha → llama `distribuir_pago_en_cascada` → muestra preview tabular (cuota,
  monto asignado) antes de confirmar → al aceptar, persiste los `Abono` y refresca
  `_refrescar_obligaciones()`/`_refrescar_abonos()` igual que el flujo existente.

## Manejo de errores

- Cuota ya completamente pagada dentro del rango seleccionado: recibe `monto_asignado = 0` de forma
  natural (su deuda pendiente es 0), no requiere manejo especial.
- Remanente sobrante tras cubrir todas las cuotas seleccionadas: `PagoPorRangoDialog` muestra el remanente
  en el preview y bloquea la confirmación hasta que el usuario reduzca el monto o amplíe la selección —
  mismo criterio conservador que la validación de sobre-pago ya existente en `AbonoFormDialog`
  (`app/views/abonos.py:90-135`), no se inventa un mecanismo de crédito a favor nuevo.
- Selección de filas que no son todas cuotas-hija de la misma obligación recurrente: el botón "Pagar
  cuotas seleccionadas" se deshabilita (mismo patrón que otros botones condicionados a la selección actual
  en `expediente_detalle.py`).

## Pruebas

- Unitarias sobre `distribuir_pago_en_cascada`: un pago que cubre exactamente una cuota; un pago que cruza
  2 cuotas; el ejemplo del usuario completo (3 cuotas, intereses parcialmente congelados); un pago que deja
  remanente sin cuotas que cubrir.
- Unitarias sobre `AllocationEngine.allocate_capital_primero` (capital antes que interés) vs.
  `allocate` (sin cambios, sigue interés antes que capital) — confirmar que no hay regresión en el
  comportamiento por defecto.
- Integración: expediente en cada una de las 5 áreas nuevas genera cuotas hijas reales igual que Familia
  hoy, sin reajuste (capital constante) y con reajuste (SMMLV/IPC) donde aplique al área.
- Integración: el ejemplo numérico exacto del usuario (cuotas de $150.000 mensuales desde 1-abr-2022,
  abono de $500.000 el 1-abr-2024) reproduce la cifra descrita — cuota de abril paga capital completo,
  marzo paga capital+interés completo, febrero paga capital completo + parte de sus intereses, con el
  resto de esos intereses quedando debido sin generar intereses nuevos sobre el capital ya pagado de
  febrero.
- Suite completa en verde, `ruff check .` limpio.

## Definición de Hecho

- Un expediente de cualquiera de las 6 áreas con obligación recurrente genera el listado completo de
  cuotas antes de liquidar, seleccionable por rango o individualmente.
- El ejemplo numérico del usuario se reproduce exactamente en un test de integración.
- Ninguna de las 6 áreas cambia su comportamiento de imputación para obligaciones que no son cuotas-hija
  (regresión cero sobre lo ya construido y probado).
- Suite completa en verde.
