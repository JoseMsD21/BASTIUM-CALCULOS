# Sprint 4 — Área Sancionatorio y Honorarios — Diseño

**Fecha:** 2026-07-17
**Estado:** Aprobado por el usuario, pendiente de plan de implementación.
**Fuente del requerimiento:** `Pendientes.md`, sección "Sprint 4 — Área Sancionatorio y Honorarios".

## Contexto

Este sprint habilita dos áreas del derecho que hoy lanzan `AreaNoImplementadaError`:
`SancionatorioStrategy` y `HonorariosStrategy` (`app/services/area_strategy.py`, líneas ~106 y
~113). A diferencia de Civil/Comercial/Laboral (obligaciones que devengan interés en el tiempo),
estas dos áreas son fundamentalmente un cálculo puntual: convertir una multa expresada en
SMLMV/UVT a pesos, o validar un cobro de honorarios contra topes legales. Se decidió con el
usuario reutilizar el mismo pipeline `Event → Payment → UniversalLiquidationService` que usan las
demás áreas (en vez de un calculador aislado), para que si la multa u honorario queda en mora,
el interés moratorio se calcule gratis con el motor ya existente.

## Decisiones tomadas con el usuario (puntos que el Sprint 4 marcaba como bloqueantes)

1. **Forma del cálculo:** reutilizar el pipeline Event/Payment existente, no un calculador aislado.
2. **Tope de cuota litis** (inconsistencia real confirmada en el PDF: pág. 10 dice 50% de la suma
   honorarios fijos + cuota litis; pág. 67 dice 30% de la cuota litis sola, citando CPC
   viejo/Ley 1123 de 2007): se aplican **ambos topes simultáneamente**, no son excluyentes.
3. **Datos UVT:** el PDF no trae tabla histórica completa (confirmado, ver Sprint 5). Se
   implementa solo el tramo pre-2020-01-01 (usa SMLMV, ya cargado en `historical_index.py`).
   Fechas posteriores lanzan una excepción explícita en vez de inventar valores.
4. **Modelo de datos:** se agregan columnas nullable a `Obligacion` (mismo patrón que el Sprint 2
   usó para Comercial), no una estructura paralela. La base de datos local está vacía (0
   expedientes), sin riesgo de migración.
5. **Costas judiciales:** no existe una tabla estructurada del Acuerdo PCSJA20-11556 en el PDF
   (solo un ejemplo "3% al 7%"). Se implementa como un porcentaje manual que ingresa quien
   liquida (el juez ya lo fijó en el auto respectivo) — no se hardcodea ninguna tabla de rangos.
   Pendiente explícito: cargar la tabla real si se consigue la fuente.
6. **Alcance GUI:** este sprint incluye motor + GUI end-to-end (extender
   `ObligacionFormDialog`), siguiendo el patrón del Sprint 2, no solo el motor.

## 1. Modelo de datos

Nuevas columnas nullable en `Obligacion` (`database/models.py`):

| Columna | Tipo | Área | Uso |
|---|---|---|---|
| `cantidad_smlmv_uvt` | `Numeric(9,4)`, nullable | Sancionatorio | Cuántos SMLMV/UVT vale la multa |
| `honorarios_fijos_pactados` | `Numeric(18,2)`, nullable | Honorarios | Tarifa fija/retainer pactada |
| `cuota_litis_pactada_pct` | `Numeric(5,2)`, nullable | Honorarios | % pactado de cuota litis |
| `beneficio_obtenido` | `Numeric(18,2)`, nullable | Honorarios | Base para validar topes de cuota litis y calcular costas |
| `costas_pct_manual` | `Numeric(5,2)`, nullable | Honorarios | % de costas/agencias fijado por el juez (opcional) |

No se requiere migración con Alembic (el proyecto no usa uno); basta con recrear
`bastium.db` vía `Base.metadata.create_all()` ya que está vacía.

## 2. Conversor SMLMV↔UVT — `app/engine/indexation/smlmv_to_uvt.py`

```python
def resolver_base_sancion(fecha_hecho: date, cantidad: Decimal) -> Decimal:
    if fecha_hecho < date(2020, 1, 1):
        smlmv = get_smlmv_for_year(fecha_hecho.year)
        return SMMLVCalculator.to_pesos(cantidad, smlmv)
    raise UVTNoDisponibleError(
        "No hay tabla historica de UVT cargada para fechas posteriores a 2020-01-01. "
        "Ver Pendientes.md Sprint 5."
    )
```

Reutiliza `get_smlmv_for_year` (`app/engine/indexation/historical_index.py`, Sprint 5) y
`SMMLVCalculator.to_pesos` (`app/engine/indexation/smmlv.py`, ya existente).

## 3. `SancionatorioStrategy.liquidar()`

- Solo soporta obligaciones `PUNTUAL` (una multa es un hecho único, no un flujo recurrente).
- Por cada obligación: valida que `cantidad_smlmv_uvt` esté presente, la convierte a pesos con
  `resolver_base_sancion(obligacion.fecha_origen, obligacion.cantidad_smlmv_uvt)`, y genera un
  `Event(date=fecha_origen, payload={"amount": monto_pesos, ...}, event_type="MULTA_SANCIONATORIA")`.
- Delega a `UniversalLiquidationService` igual que `CivilFamiliaStrategy` (mismo
  `_construir_rate_provider`, reutilizando `tasa_efectiva_anual` si se quiere interés moratorio
  sobre la multa impaga).
- `soporta_indexacion_ipc = False`: el monto ya está expresado en una unidad actualizada
  (SMLMV/UVT), indexarlo otra vez por IPC sería doble indexación (misma regla documentada en el
  Sprint 8).

## 4. `HonorariosStrategy.liquidar()`

Por cada obligación `PUNTUAL` (igual, no soporta RECURRENTE):

```
cuota_litis_monto = beneficio_obtenido * cuota_litis_pactada_pct / 100

# Validación de topes (ambos simultáneos):
if cuota_litis_monto > beneficio_obtenido * 30/100:
    raise CuotaLitisExcedeTopeError("cuota litis excede el 30% del beneficio obtenido")
if (honorarios_fijos_pactados + cuota_litis_monto) > beneficio_obtenido * 50/100:
    raise CuotaLitisExcedeTopeError("honorarios totales exceden el 50% del beneficio obtenido")

total_honorarios = honorarios_fijos_pactados + cuota_litis_monto
```

- Genera `Event(date=fecha_origen, payload={"amount": total_honorarios}, event_type="HONORARIOS_PROFESIONALES")`.
- Si `costas_pct_manual` no es `None`: genera un segundo
  `Event(date=fecha_origen, payload={"amount": beneficio_obtenido * costas_pct_manual / 100}, event_type="COSTAS_PROCESALES")`.
- `soporta_indexacion_ipc = False` (mismo razonamiento que Sancionatorio).
- Reutiliza `tasa_efectiva_anual` para mora en el pago del honorario si aplica, igual patrón que
  las demás áreas.

## 5. Excepciones nuevas — `app/core/exceptions.py`

```python
class UVTNoDisponibleError(Exception):
    """Se lanza cuando se necesita el valor de UVT para una fecha posterior a 2020-01-01
    y no hay tabla historica cargada (ver Pendientes.md Sprint 5)."""

class CuotaLitisExcedeTopeError(Exception):
    """Se lanza cuando honorarios fijos + cuota litis exceden el tope legal (30% cuota
    litis sola, 50% suma total del beneficio obtenido)."""
```

## 6. Constantes y GUI

- `app/core/constants.py`: nuevas listas
  - `CATEGORIAS_SANCIONATORIO = [("MULTA_SANCIONATORIA", "Multa sancionatoria (SMLMV/UVT)")]`
  - `CATEGORIAS_HONORARIOS = [("HONORARIOS_PROFESIONALES", "Honorarios profesionales"), ("COSTAS_PROCESALES", "Costas procesales / agencias en derecho")]`
  - `AREAS_DERECHO`: cambiar `SANCIONATORIO` y `HONORARIOS` a `True`.
- `app/engine/liquidation/engine.py`: agregar `"MULTA_SANCIONATORIA"`, `"HONORARIOS_PROFESIONALES"`,
  `"COSTAS_PROCESALES"` a `_capital_concepts`.
- `app/views/obligaciones.py` (`ObligacionFormDialog`): extender el mismo patrón de
  mostrar/ocultar campos que ya usa `es_comercial`, agregando:
  - Campo "Cantidad SMLMV/UVT" visible solo si área == SANCIONATORIO.
  - Campos "Honorarios fijos", "% Cuota litis", "Beneficio obtenido", "% Costas (opcional)"
    visibles solo si área == HONORARIOS.
- `NuevoExpedienteDialog` no requiere cambios (ya lee de `AREAS_DERECHO`).

## 7. Testing (TDD)

- `tests/services/test_area_strategy.py`:
  - Sancionatorio: multa con hecho pre-2020 (verificar contra SMLMV real conocido de ese año).
  - Sancionatorio: multa con hecho posterior a 2020-01-01 → debe lanzar `UVTNoDisponibleError`.
  - Honorarios: caso válido dentro de ambos topes.
  - Honorarios: cuota litis sola excede 30% → `CuotaLitisExcedeTopeError`.
  - Honorarios: cuota litis individual ≤30% pero suma total excede 50% → `CuotaLitisExcedeTopeError`.
  - Honorarios: caso con costas judiciales (`costas_pct_manual` seteado).
- `tests/engine/indexation/test_smlmv_to_uvt.py`: tests unitarios directos del conversor.
- Suite completa en verde al cerrar el sprint.
- Smoke test manual GUI end-to-end (mismo patrón que la Tarea 17 del MVP y el smoke test del
  Sprint 2): crear expediente Sancionatorio y uno Honorarios desde la GUI, capturar
  obligación, liquidar, verificar montos.

## Alcance explícitamente excluido (documentado, no un olvido)

- Tabla histórica completa de UVT para fechas posteriores a 2020-01-01 (bloqueado hasta que
  exista una fuente real — ver Pendientes.md Sprint 5).
- Tabla estructurada de rangos de costas del Acuerdo PCSJA20-11556 (se usa % manual en su lugar).
- Obligaciones RECURRENTE en Sancionatorio/Honorarios (ambas áreas modelan hechos puntuales).
- Cierre de sprint: actualizar `README.md` y `docs/GUIA_USUARIO.md` para sacar Sancionatorio y
  Honorarios de "🚧 no todavía" y documentar cómo usarlos (regla obligatoria de `Pendientes.md`).

## Definición de Hecho

- `SancionatorioStrategy` y `HonorariosStrategy` liquidan con TDD, siguiendo el patrón de
  `tests/services/test_area_strategy.py`.
- Tests de conversión SMLMV→UVT para fechas antes y después de 2020-01-01.
- Test de validación de ambos topes de cuota litis (30% individual, 50% total).
- Ambas áreas seleccionables y operables desde la GUI end-to-end.
- Suite completa en verde.
- `README.md` y `docs/GUIA_USUARIO.md` actualizados.
