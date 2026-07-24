# Diseño: Sprint 15 — Tributario completo (cierre del Sprint 11b)

**Fecha:** 2026-07-24
**Origen:** Sprint 15 de `Pendientes.md` — continuación directa del Sprint 11 (11a, completado
2026-07-20, construyó `moratory_interest.py` y `renta_liquida.py` como motores puros standalone; 11b
cierra sanciones, imputación tributaria, y — a diferencia de 11a — conecta todo a un área operable
end-to-end en la GUI).

**Depende de:** Sprint 14 (tabla histórica UVT, 2006-2026), ya completado — la sanción mínima (10 UVT)
la necesita directamente.

## Decisiones tomadas con el usuario durante el brainstorming

1. **Alcance: `TributarioStrategy` completo end-to-end**, no solo motores standalone (a diferencia de
   11a). Esto obliga a resolver ahora el modelo de datos y el choque de arquitectura descrito abajo, en
   vez de aplazarlos a un futuro Sprint 11c.
2. **Reutilizar `LiquidationCore`/`AllocationEngine`/`UniversalLiquidationService` tal como existen**, en
   vez de construir un motor de imputación tributaria dedicado. Ver sección "Arquitectura" para la
   justificación completa.
3. **Renta Líquida Gravable (11a) también se conecta** este sprint, pero como bloque informativo
   separado del balance de deuda (no participa en el pipeline de eventos/pagos).
4. **Renta Líquida Gravable no se mezcla con el saldo de deuda**: es un número de base gravable, no una
   deuda exigible: forzarlo por el mismo pipeline de balance corromperia el saldo total (mezclaría
   "pesos de renta" con "pesos efectivamente adeudados").

## Arquitectura: por qué reutilizar el motor genérico en vez de uno dedicado

`LiquidationCore` (usado hoy por las 5 áreas operables) ya tiene exactamente 3 buckets de deuda
(`PendingDebt.principal/interest/indexation`), pagados en un orden fijo cuando llega un pago
(`AllocationEngine.allocate`: indexación → intereses → capital). Ese orden coincide **exactamente**, en
forma y posición, con el que exige el PDF para tributario: sanciones → intereses →
impuestos/anticipos/retenciones.

Se investigó el riesgo de "mal-etiquetar" un monto (ej. que un reporte legal muestre una sanción bajo la
columna "Indexación"): se confirmó por lectura directa del código que el bucket `indexation` **hoy no se
muestra en ningún lado** — ni en la tabla de la GUI (`app/views/liquidaciones.py`, 7 columnas fijas sin
indexación), ni en la tabla de cronología del PDF/Word (`app/reports/pdf.py`/`word.py`, mismos 7
encabezados), ni siquiera en el resumen ejecutivo del PDF (`ReportSummaryBuilder.build_summary()` calcula
`saldo_final_indexacion` pero `filas_resumen` en `pdf.py` nunca lo incluye). Es una laguna de reporting
preexistente (la indexación IPC de Civil/Familia ya sufre este mismo vacío), no algo que este sprint
introduzca. Por lo tanto, reutilizar ese bucket para sanciones no agrega ningún riesgo de mal-etiquetado
que no exista ya — y de paso, este sprint corrige la laguna (sección "Reporting" abajo), porque Tributario
sí necesita que las sanciones sean visibles.

**Ventajas de reutilizar el motor genérico:**
- Acumulación automática de interés diario (`LiquidationCore._accrue_time_passage`) reutilizando el
  `rate_provider` que ya construye 11a (`construir_rate_provider_moratorio_tributario`), sin reescribir
  ese bucle.
- `AllocationEngine.allocate()` resuelve la imputación en el orden correcto sin código nuevo.
- Integración inmediata con GUI (`ExpedienteDetallePage`), historial de auditoría
  (`AuditLog`/`serialization.py`), y exportación PDF/Word — el mismo camino que ya usan las 5 áreas
  existentes.

**Costo aceptado:** los nombres internos (`indexation_amount`, `PendingDebt.indexation`) no reflejan el
dominio tributario. Se documenta con un comentario explícito en `TributarioStrategy` (no se renombra el
motor genérico, que sigue sirviendo a Civil/Familia con su semántica original).

## Modelo de datos

### Categorías nuevas (`CATEGORIAS_TRIBUTARIO`, `app/core/constants.py`)

| Categoría | Descripción | Bucket de `PendingDebt` / `event_type` |
|---|---|---|
| `IMPUESTO_A_CARGO` | El impuesto mismo (capital sobre el que corre mora) | `principal` — se agrega `"IMPUESTO_A_CARGO"` (el propio código de categoría) a `_capital_concepts`, mismo patrón exacto que `"MULTA_SANCIONATORIA"`/`"HONORARIOS_PROFESIONALES"` |
| `SANCION_EXTEMPORANEIDAD` | 5% mensual del impuesto a cargo, tope 100% | `indexation` — evento emitido con `event_type="SANCION_TRIBUTARIA"` (normalizado, ver nota abajo) |
| `SANCION_INEXACTITUD` | 160% (200% si agravada) de la diferencia declarado/determinado | `indexation` — ídem `"SANCION_TRIBUTARIA"` |
| `SANCION_ERROR_ARITMETICO` | 30% de la diferencia generada por el error | `indexation` — ídem `"SANCION_TRIBUTARIA"` |
| `RENTA_LIQUIDA` | Depuración de renta líquida gravable (informativo, ver abajo) | Ninguno — no genera evento |

**Nota sobre `event_type` de las 3 sanciones:** a diferencia de `IMPUESTO_A_CARGO` (cuyo `categoria` se
agrega directamente a `_capital_concepts`, igual que hacen las demás áreas), `LiquidationCore._process_event`
solo reconoce el bucket `indexation` para el string literal `"INDEXATION"` — no existe un set equivalente a
`_capital_concepts` para ese bucket. En vez de modificar `LiquidationCore` (motor compartido por las 5
áreas existentes) para agregar ese set, `TributarioStrategy` normaliza las 3 categorías de sanción a un
único `event_type="SANCION_TRIBUTARIA"` al emitir el evento — la categoría real (cuál de las 3 sanciones
es) se preserva en `obligacion.categoria`/el `label` del evento (el `concepto` capturado), que es lo que
igual se muestra en el reporte. `LiquidationCore._process_event` no requiere ningún cambio estructural
(no se agrega un set nuevo tipo `_indexation_concepts`): se tocan dos líneas puntuales en `engine.py` —
agregar `"IMPUESTO_A_CARGO"` a `_capital_concepts` (exactamente como ya hizo cada área anterior con sus
propias categorías), y ensanchar la comparación literal `elif event.event_type == "INDEXATION":` a
`elif event.event_type in ("INDEXATION", "SANCION_TRIBUTARIA"):` — sigue siendo una comparación de
strings literales, no una lista de conceptos configurable como `_capital_concepts`.

### Columnas nuevas en `Obligacion` (migración de esquema, mismo patrón que
`scripts/migrate_moneda_trm.py` — `ALTER TABLE` idempotente vía `PRAGMA table_info`)

- `base_sancion_tributaria: Numeric(18,2)` nullable — compartida por las 3 sanciones: impuesto a cargo
  (extemporaneidad) o diferencia declarado/determinado (inexactitud, error aritmético).
- `meses_extemporaneidad: Integer` nullable — solo `SANCION_EXTEMPORANEIDAD`.
- `sancion_agravada: Boolean` nullable, default `False` — solo `SANCION_INEXACTITUD` (omisión de activos
  o inclusión de pasivos inexistentes → 200% en vez de 160%).
- `ingresos_brutos`, `devoluciones_rebajas_descuentos`, `costos`, `deducciones`, `rentas_exentas`:
  `Numeric(18,2)` nullable — solo `RENTA_LIQUIDA`, alimentan directamente
  `depurar_renta_liquida_gravable()` (11a, sin cambios).

Campos reutilizados sin cambios: `valor` (monto del impuesto a cargo cuando `categoria ==
IMPUESTO_A_CARGO`), `fecha_origen` (fecha de exigibilidad/vencimiento, igual rol que ya cumple para
Sancionatorio — punto de partida de la mora y año de referencia para la UVT de la sanción mínima),
`categoria`, `abonos` (modelo `Abono` existente, sin cambios).

### `AreaDerecho` / `AREAS_DERECHO`

Sexta entrada: `"TRIBUTARIO"` en `database/models.py` (`AreaDerecho`) y `app/core/constants.py`
(`AREAS_DERECHO`), habilitada (`True`) desde el principio — a diferencia de 11a, este sprint sí expone el
área en el selector de la GUI.

### `CATALOGO_PARAMETROS` (`app/services/parametro_service.py`)

Cuatro entradas nuevas, modo `ABIERTO` (topes fijos del Estatuto Tributario, no series por vigencia
anual/mensual como SMLMV/UVT):

- `EXTEMPORANEIDAD_PCT_MENSUAL` (5)
- `INEXACTITUD_PCT` (160)
- `INEXACTITUD_AGRAVADA_PCT` (200)
- `ERROR_ARITMETICO_PCT` (30)

## Código nuevo

### `app/engine/tax/sanciones.py`

Cuatro funciones puras, cada una retorna el monto de la sanción ya con el piso de sanción mínima (10 UVT)
aplicado:

```python
def calcular_sancion_extemporaneidad(
    impuesto_a_cargo: Decimal, meses_o_fraccion: int, fecha_referencia: date
) -> Decimal:
    """5% mensual (get_parametro EXTEMPORANEIDAD_PCT_MENSUAL) del impuesto a cargo por cada mes o
    fracción, tope 100% del impuesto a cargo. Piso de 10 UVT (get_uvt_for_year(fecha_referencia.year))."""

def calcular_sancion_inexactitud(
    diferencia: Decimal, agravada: bool, fecha_referencia: date
) -> Decimal:
    """160% (o 200% si agravada) de la diferencia entre el saldo determinado y el declarado
    (ya calculada por el llamador -- ver 'base_sancion_tributaria' en Modelo de datos). Piso de 10 UVT."""

def calcular_sancion_error_aritmetico(
    diferencia: Decimal, fecha_referencia: date
) -> Decimal:
    """30% de la diferencia generada por el error (ya calculada por el llamador). Piso de 10 UVT."""

def aplicar_piso_sancion_minima(monto_sancion: Decimal, fecha_referencia: date) -> Decimal:
    """max(monto_sancion, 10 * get_uvt_for_year(fecha_referencia.year)) -- función compartida por
    las tres anteriores, no se repite la lógica del piso tres veces."""
```

Todos los montos pasan por `Rounding.money()`. Fuente legal de cada porcentaje: `get_parametro(clave,
fecha_referencia)` (no constantes hardcodeadas), siguiendo el patrón ya establecido por
`ET635_PUNTOS_DESCUENTO`.

### `TributarioStrategy` (`app/services/area_strategy.py`)

Sigue el mismo esqueleto que las 5 estrategias existentes (`liquidar()` → construye eventos + pagos +
rate_provider → `UniversalLiquidationService`), con estas particularidades:

- `soporta_indexacion_ipc = False` (igual que Sancionatorio/Honorarios — el monto ya está en una unidad
  fiscal propia).
- Valida cada obligación según su `categoria` (mismo patrón que `_validar_obligacion_honorarios`): campos
  requeridos según el tipo de sanción.
- `_evento_de_obligacion()`: para `IMPUESTO_A_CARGO` emite un evento con `event_type =
  obligacion.categoria` (es decir, `"IMPUESTO_A_CARGO"`, agregado a `_capital_concepts` en `engine.py`,
  mismo patrón que las demás áreas) y `amount = obligacion.valor`. Para las 3 sanciones, calcula el monto
  con la función correspondiente de `sanciones.py` y emite un evento con `event_type =
  "SANCION_TRIBUTARIA"` (normalizado, bucket `indexation` — ver nota en "Modelo de datos"), preservando la
  categoría real de la sanción en el `label`/`concepto` del evento. Para `RENTA_LIQUIDA`, **no emite
  evento**: se procesa aparte (ver abajo).
- `_construir_rate_provider()`: reutiliza `construir_rate_provider_moratorio_tributario` de 11a
  directamente (tasa automática E.T. 635, nunca pactada) en vez del patrón manual de las otras 4
  estrategias.
- Al final de `liquidar()`, si hay alguna obligación `RENTA_LIQUIDA` entre las obligaciones del
  expediente, llama `depurar_renta_liquida_gravable()` con sus 5 campos y adjunta el resultado al
  `LiquidationResult` (ver siguiente sección). Si hay más de una obligación `RENTA_LIQUIDA` en el mismo
  expediente, es un error de validación (`ValueError`) — un expediente tributario modela un solo período
  gravable a la vez, no varios años en la misma liquidación.

### `LiquidationResult` (`app/engine/liquidation/result.py`) — nuevo campo opcional

```python
@dataclass(frozen=True)
class LiquidationResult:
    items: List[LiquidationItem]
    renta_liquida: RentaLiquidaGravableResult | None = None  # nuevo, default None
```

Campo con default `None`, así que las 5 áreas existentes no cambian ni un byte de su comportamiento ni de
sus pruebas actuales (nunca lo pueblan).

## Reporting: corregir la laguna del tercer bucket

Necesario porque Tributario sí necesita que las sanciones sean visibles (a diferencia del vacío
preexistente con indexación IPC, que este sprint no busca arreglar por sí mismo pero corrige de paso al
tocar el mismo código compartido):

- `app/views/liquidaciones.py`: agregar una 8ª columna a la tabla, encabezado **"Indexación / Sanciones"**,
  poblada desde `item.indexation_amount`.
- `app/reports/pdf.py` y `app/reports/word.py`: agregar la misma columna a la tabla de cronología
  detallada, y agregar la fila faltante **"Saldo Final Indexación/Sanciones"** a `filas_resumen` (ya
  calculado por `ReportSummaryBuilder`, solo no incluido en la lista renderizada).
- Si `resultado.renta_liquida is not None`: agregar un bloque nuevo, separado de la tabla de cronología,
  titulado "Depuración de Renta Líquida Gravable" con los 5 campos intermedios del resultado — en GUI
  (`ResultadoLiquidacionView`), PDF y Word. No se mezcla con `filas_resumen`/la tabla de saldo.

## Alcance explícitamente excluido

- Cálculo del impuesto a partir de una tarifa aplicada a la renta líquida gravable (ej. 35% renta
  corporativa) — el usuario ingresa `IMPUESTO_A_CARGO` como un monto ya determinado (mismo criterio que
  `ibc_vigente_anual` manual en Comercial); las tarifas varían por tipo de contribuyente y año, fuera de
  alcance de este sprint.
- Compensación de pérdidas fiscales de años anteriores (ya excluido explícitamente por 11a).
- Integración en vivo con la DIAN, cobro coactivo administrativo (excluidos explícitamente por
  `Pendientes.md`).
- Múltiples períodos gravables (`RENTA_LIQUIDA`) en un mismo expediente — un expediente tributario modela
  un solo período.

## Testing

TDD, mismo patrón que 11a y que `tests/services/test_area_strategy.py`:

- `tests/engine/tax/test_sanciones.py`: casos conocidos del PDF (pág. 39) para las 3 sanciones, el tope
  del 100% en extemporaneidad, la diferencia 160%/200% en inexactitud, y el piso de 10 UVT (un caso donde
  la sanción calculada da menos de 10 UVT y debe quedar en 10 UVT).
- `tests/services/test_area_strategy.py`: nueva `TestTributarioStrategy` — validación de campos
  requeridos por categoría, cada categoría liquidando el monto correcto, un caso multi-obligación
  verificando el orden de imputación real (sanciones → intereses → impuesto) al aplicar un abono parcial,
  y un caso con obligación `RENTA_LIQUIDA` confirmando que `resultado.renta_liquida` queda poblado y que
  el saldo de deuda no se contamina con ese monto.
- `tests/scripts/test_migrate_*.py` (nuevo archivo, mismo patrón que `test_migrate_moneda_trm.py`):
  columnas se agregan, filas existentes se preservan, idempotencia.
- `tests/engine/reports/` o equivalente: confirma que la fila "Saldo Final Indexación/Sanciones" aparece
  en `ReportSummaryBuilder.build_summary()` y que `pdf.py`/`word.py` la incluyen.
- Suite completa en verde.

## Definición de Hecho

- Tests de los 3 tipos de sanción con casos conocidos del PDF (pág. 39), incluyendo el piso de 10 UVT.
- Test de imputación tributaria verificando el orden sanciones → intereses → impuesto con un abono
  parcial, distinto del test equivalente civil.
- `TributarioStrategy` liquida con TDD, habilitada en `AREAS_DERECHO`, visible en el selector de la GUI.
- `RENTA_LIQUIDA` se muestra como bloque informativo sin afectar el saldo de deuda.
- Reporting (GUI/PDF/Word) muestra la columna y el resumen de sanciones/indexación, antes ausentes.
- `README.md` y `docs/GUIA_USUARIO.md` actualizados (sexta área operable).
- Suite completa en verde.
