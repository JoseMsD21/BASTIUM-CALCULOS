# Sprint 41 — Familia: obligaciones recurrentes con reajuste anual, concepto por mes y cuotas seleccionables para abono Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Decisión de diseño ya tomada por el usuario (2026-08-07):** usar la propuesta de diseño resumida abajo
(no hubo sesión de brainstorming adicional — el usuario aprobó directamente esta propuesta). La fórmula de
reajuste (`cuota_nueva = cuota_anterior + (cuota_anterior × porcentaje_variación_anual / 100)`) queda
pendiente de confirmación formal del despacho — ya se agregó la pregunta a
`Preguntas-Para-Abogado-Abiertas.md` (sección "Sprint 41"); se implementa igual mientras tanto porque el
usuario así lo pidió, con la fórmula tal como la trajo en su reporte original.

**No hay PDF de la demanda real (Aranda) disponible como fixture todavía** — el test de integración de este
plan usa datos **sintéticos equivalentes** (misma tasa 6% anual, misma mecánica de reajuste) en vez de
reproducir las cifras exactas de ese caso real.

**Goal:** Una obligación RECURRENTE de Familia (cuota alimentaria) puede marcarse con un tipo de reajuste
anual (SMMLV o IPC). Al guardarla, el sistema genera y persiste las cuotas mensuales reales (una
`Obligacion` PUNTUAL hija por mes, desde `fecha_origen` hasta la fecha de corte del expediente), con el
capital ajustado cada 1° de enero según el índice elegido (constante durante el resto del año) y un
`concepto` dinámico que nombra el mes y año exactos (ej. "CUOTA ALIMENTARIA DE MARZO 2026"). Los abonos se
capturan por cuota individual (reutilizando el `AbonoFormDialog` ya existente contra el `obligacion_id` de
la cuota hija específica, sin campo nuevo en `Abono`). El interés de mora de cada cuota queda calculado de
forma autónoma (capital propio de esa cuota × sus propios días de mora) **sin necesidad de ningún motor de
interés nuevo** — ver razonamiento matemático en "Architecture" abajo.

**Architecture:**

1. **Nuevo campo en `Obligacion`** (`database/models.py`): `tipo_reajuste_anual: TipoReajusteAnual` (enum
   nuevo en `app/core/constants.py`: `SMMLV`, `IPC`, `NINGUNO` — default `NINGUNO`), solo relevante cuando
   `tipo == TipoObligacion.RECURRENTE` y área es `CIVIL_FAMILIA`. Migración nueva en `scripts/` siguiendo el
   patrón exacto de `scripts/migrate_aplica_indexacion_ipc.py` (columna nueva + `ALTER TABLE` +
   backfill/default), y registrarla en `database/database.py::aplicar_migraciones_pendientes()` junto a las
   demás (mismo patrón que las 9 ya acumuladas — ver `CHANGELOG.md` "[Unreleased]" para la lista).
2. **Segundo campo:** `obligacion_padre_id: int | None` (FK auto-referencial a `obligaciones.id`, nullable)
   en `Obligacion` — marca una cuota PUNTUAL como generada automáticamente a partir de una obligación
   RECURRENTE padre. Se usa para (a) no volver a generar cuotas para la misma obligación padre dos veces, y
   (b) que la UI pueda agrupar/distinguir visualmente las cuotas generadas de las obligaciones normales.
3. **Nuevo servicio `app/services/reajuste_anual.py`** (nombre sugerido, ajustar si hay una convención
   mejor en `app/services/`): función `generar_cuotas_mensuales(obligacion_recurrente: Obligacion,
   fecha_corte: date) -> list[Obligacion]` que:
   - Recorre mes a mes desde `fecha_origen` de la obligación padre hasta `fecha_corte` (reutilizar
     `CalendarUtils` para la aritmética de fechas, igual que `RecurringScheduler`).
   - Mantiene el capital constante dentro de cada año calendario; el 1° de enero de cada año siguiente al de
     `fecha_origen`, reajusta: para `SMMLV`, `pct = (get_smlmv_for_year(anio) -
     get_smlmv_for_year(anio - 1)) / get_smlmv_for_year(anio - 1) * 100` (reutilizar
     `app/engine/indexation/historical_index.py::get_smlmv_for_year`, ya usado por Sancionatorio); para
     `IPC`, usar el mecanismo de indexación ya existente para Civil/Familia (`app/engine/indexation/ipc.py`
     — verificar su API exacta, reutilizarlo tal cual en vez de reimplementar el cálculo de variación anual).
   - Genera un `concepto` dinámico por cuota interpolando el nombre del mes en español y el año (ej. "CUOTA
     ALIMENTARIA DE MARZO 2026" si el concepto original de la obligación padre era "CUOTA ALIMENTARIA").
   - Crea una `Obligacion` PUNTUAL hija por mes con `obligacion_padre_id` apuntando a la obligación
     RECURRENTE original, mismo `expediente_id`, `categoria`, `tasa_efectiva_anual` y demás campos legales
     heredados de la obligación padre.
   - Persiste las cuotas generadas (esto reemplaza, para obligaciones con `tipo_reajuste_anual != NINGUNO`,
     la expansión efímera de `RecurringScheduler` dentro de `liquidar()` — ver punto 5).
4. **Por qué NO hace falta un motor de interés "autónomo por cuota" nuevo (justificación matemática,
   verificar con un test antes de asumir que aplica):** el interés simple (no compuesto — Civil/Familia no
   tiene wiring de anatocismo, eso es exclusivo de Comercial) sobre un capital que crece por escalones
   (cada cuota nueva suma su propio capital en su propia fecha) es **linealmente equivalente** a sumar el
   interés simple calculado de forma independiente por cada tramo de capital sobre sus propios días —
   porque el interés simple es aditivo día a día sobre el capital vigente ESE día. Concretamente: si la
   cuota de mayo se suma el día D1 y la cuota de junio el día D2 > D1, el interés acumulado entre D1 y D2 es
   `capital_mayo × tasa` (solo mayo existe todavía) — igual que su cálculo "autónomo" aislado. Después de
   D2, el interés acumulado por día es `(capital_mayo + capital_junio) × tasa`, que es exactamente la suma
   de los dos cálculos autónomos para ese mismo día. Esto significa que **generar las cuotas como
   `Obligacion` reales dentro del mismo expediente y dejar que el motor consolidado existente
   (`LiquidationCore`, vía `AreaStrategy.liquidar()`) las procese junto con las demás obligaciones y abonos
   del expediente ya produce el resultado matemáticamente correcto**, sin duplicar lógica de interés. La
   Tarea 3 de este plan exige un test de integración que verifique esta equivalencia explícitamente (comparar
   el interés de una cuota calculado de forma aislada vs. su contribución dentro del cálculo consolidado)
   antes de dar por buena esta simplificación — si el test la refuta, escalar antes de continuar, no forzar
   el resultado.
5. **Wiring en `CivilFamiliaStrategy`/`area_strategy.py`:** cuando una obligación RECURRENTE tiene
   `tipo_reajuste_anual != NINGUNO` y ya tiene cuotas hijas generadas (`obligacion_padre_id` apuntando a
   ella desde al menos una fila), `liquidar()` debe usar esas cuotas hijas reales (como cualquier obligación
   PUNTUAL normal) **en vez de** expandir la obligación padre con `RecurringScheduler` — evitar contar el
   capital dos veces. Si no tiene reajuste (`NINGUNO`), el comportamiento actual (expansión efímera) se
   mantiene sin cambios.
6. **UI:** en `ExpedienteDetallePage` (`app/views/expediente_detalle.py`), al agregar/editar una obligación
   RECURRENTE de Civil/Familia con reajuste, ofrecer una acción "Generar cuotas" que llama al servicio
   nuevo, persiste las filas y refresca la tabla de Obligaciones mostrando las cuotas generadas (agrupadas o
   con alguna marca visual de que son cuotas de una obligación padre). Los abonos se agregan igual que hoy
   (`AbonoFormDialog`) pero seleccionando la cuota específica de la lista en vez de la obligación padre.

**Tech Stack:** Python 3.14, SQLAlchemy (columna + FK auto-referencial + migración manual estilo
`scripts/migrate_*.py`), PySide6 6.11, pytest.

---

### Contexto compartido entre tareas

- **Alcance excluido, no implementar:** retro-generar cuotas para obligaciones recurrentes ya existentes en
  la base de datos (solo aplica hacia adelante); extender el reajuste anual a Laboral (eso es el punto 6 del
  Sprint 44, explícitamente diferido — no se decidió incluirlo en esta ronda); reproducir el caso Aranda con
  el PDF real (no está disponible, usar datos sintéticos).
- Este es el sprint de mayor riesgo/complejidad de la tanda — parte primero el trabajo en sub-tareas
  pequeñas con TDD estricto, y no avances a la Tarea 4 (UI) sin que la Tarea 3 (verificación matemática del
  interés autónomo) esté en verde.

### Task 1: Schema — tipo_reajuste_anual y obligacion_padre_id

- [ ] Enum `TipoReajusteAnual` (`SMMLV`, `IPC`, `NINGUNO`) en `app/core/constants.py`.
- [ ] Columnas nuevas en `Obligacion` (`tipo_reajuste_anual`, `obligacion_padre_id` con FK
      auto-referencial) + migración en `scripts/migrate_*.py` siguiendo el patrón existente, registrada en
      `aplicar_migraciones_pendientes()`.
- [ ] Test de migración (mismo patrón que las migraciones anteriores) confirmando que una BD sin estas
      columnas las gana al migrar, con default `NINGUNO`/`NULL`.

### Task 2: Servicio generador de cuotas mensuales con reajuste anual

- [ ] `generar_cuotas_mensuales()` según el diseño de la sección Architecture — capital constante dentro
      del año, reajustado cada 1° de enero según SMMLV o IPC, concepto dinámico por mes/año.
- [ ] Test unitario que reproduce la mecánica de reajuste con cifras sintéticas simples (ej. cuota base
      $100.000, SMMLV con variación anual conocida) y confirma el capital exacto de cada año.
- [ ] Test que confirma que NO se generan cuotas duplicadas si el servicio se llama dos veces sobre la
      misma obligación padre (usar `obligacion_padre_id` para detectar cuotas ya generadas).

### Task 3: Verificación matemática del interés autónomo por cuota (bloqueante para la Tarea 4)

- [ ] Test de integración: liquidar un expediente con 2-3 cuotas generadas por el servicio de la Tarea 2 (u
      obligaciones PUNTUAL creadas a mano simulando cuotas), a una tasa fija conocida, y comparar el
      interés total resultante contra la suma de calcular cada cuota de forma aislada (capital propio ×
      tasa × sus propios días de mora, usando `DailyInterest.calculate` directamente). Deben coincidir
      exactamente. Si no coinciden, detener el sprint y escalar — no continuar con la Tarea 4 hasta resolver
      la discrepancia.
- [ ] Documentar el resultado (coincide o no) como comentario en el test, citando el razonamiento de la
      sección Architecture.

### Task 4: Wiring en CivilFamiliaStrategy y UI

- [ ] `liquidar()` usa las cuotas hijas reales en vez de la expansión efímera de `RecurringScheduler` cuando
      `tipo_reajuste_anual != NINGUNO` y ya existen cuotas generadas — sin duplicar capital.
- [ ] Acción "Generar cuotas" en `ExpedienteDetallePage` que llama al servicio y refresca la tabla.
- [ ] Abonos capturables por cuota individual (reutilizar `AbonoFormDialog` contra el `obligacion_id` de la
      cuota hija).
- [ ] Tests de GUI para el flujo completo: crear obligación recurrente con reajuste → generar cuotas → ver
      cuotas en la tabla → agregar abono a una cuota específica.

### Task 5: Verificación final

- [ ] Test de integración con datos sintéticos equivalentes al caso Aranda (cuota base, reajuste SMMLV
      multi-año, mora por cuota) que confirme capital correcto por año y mora independiente por cuota.
- [ ] Suite completa de tests (`pytest`) en verde.
