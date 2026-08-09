# Sprint 44 — Laboral: salario mínimo automático, descuentos, edición de obligaciones/eventos y fecha de corte Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Decisión de diseño ya tomada por el usuario (2026-08-07) para el punto 3 (descuentos):** entidad propia
tipo `Abono` — nueva tabla `DescuentoLaboral` (monto, fecha, marca legal/ilegal) ligada a la `Obligacion`,
permitiendo varios descuentos independientes por obligación.

**Punto 6 (cuotas mensuales con reajuste anual, igual que el Sprint 41) queda explícitamente EXCLUIDO de
este sprint** — el usuario no decidió extenderlo a Laboral en esta ronda; queda como sprint propio más
adelante si se decide después. No implementar nada de ese punto aquí.

**Goal:** Cubrir los puntos 1, 2, 3, 4 y 5 de los hallazgos originales del sprint — checkbox "salario =
SMMLV", edición de obligaciones y eventos laborales ya guardados, descuentos del empleador, y fecha de
corte editable desde la pantalla de liquidación.

**Architecture:**
- **Punto 1 (SMMLV automático):** `LaboralStrategy` no importa `get_smlmv_for_year`
  (`app/engine/indexation/historical_index.py`) pese a que Sancionatorio ya lo usa vía `smlmv_to_uvt.py` —
  reutilizar la misma función. Nuevo campo `es_smmlv: bool` en `Obligacion` (+ migración, mismo patrón que
  las anteriores) y checkbox en el formulario Laboral (`app/views/obligaciones.py`); cuando está activo,
  `LaboralStrategy` resuelve `valor` desde `get_smlmv_for_year(fecha_origen.year)` en vez del texto libre
  digitado a mano.
- **Punto 2 (edición de Obligacion ya guardada):** hoy `expediente_detalle.py` siempre abre
  `ObligacionFormDialog` en modo creación. Extender el diálogo para que acepte una `Obligacion` existente
  opcional y precargue todos sus campos (reutilizar el mismo formulario, no duplicar UI) — al guardar,
  actualiza en vez de insertar. Esto resuelve de raíz el problema de "fecha de pago real" inaccesible sin
  tocar la lógica de visibilidad condicional del Sprint 39 (que ya centraliza correctamente qué campos se
  muestran según checkboxes/área — reutilizarla, no duplicarla).
- **Punto 3 (descuentos):** nueva tabla `DescuentoLaboral` (`database/models.py`, mismo patrón que `Abono`:
  `id`, `obligacion_id` FK, `fecha`, `monto`, `es_legal: bool`, `motivo: str | None`) + migración. Nuevo
  diálogo `DescuentoLaboralFormDialog` (mismo patrón que `AbonoFormDialog`) accesible desde
  `ExpedienteDetallePage` para obligaciones Laboral. `LaboralStrategy.liquidar()` resta los descuentos del
  neto adeudado (verificar el punto exacto de la cadena de cálculo donde debe restarse — probablemente como
  un evento adicional tipo `PAYMENT` o una resta directa sobre el capital, decidir leyendo cómo
  `LiquidationCore` ya maneja `PAYMENT`/`AllocationEngine` y reutilizar ese mecanismo en vez de inventar uno
  nuevo). El reporte (`table_builder.py`/`pdf.py`) muestra los descuentos aplicados.
- **Punto 4 (CRUD de EventoLaboral):** hoy `expediente_detalle.py` solo permite crear. Agregar
  editar/eliminar `EventoLaboral` ya guardado (mismo patrón que el punto 2, reutilizando
  `EventoLaboralFormDialog` en modo edición).
- **Punto 5 (fecha de corte editable desde liquidación):** `expediente_detalle.py:216` (verificar línea
  actual) toma `expediente.fecha_corte_default` directo. Agregar un `QDateEdit` en la pantalla de
  liquidación que permita un override puntual de la fecha de corte para esa liquidación específica, sin
  necesidad de ir al diálogo separado "Editar expediente".

**Tech Stack:** Python 3.14, SQLAlchemy (tabla nueva + migración), PySide6 6.11, pytest + pytest-qt.

---

### Contexto compartido entre tareas

- **Punto 6 explícitamente fuera de alcance** (ver arriba) — no construir nada de reajuste anual/cuotas
  mensuales para Laboral en este sprint.
- Reutilizar el CRUD de edición que construyas para `Obligacion` (punto 2) y `EventoLaboral` (punto 4) con
  el mismo patrón de diálogo — no dupliques la lógica entre los dos.
- Verificar leyendo el código actual los números de línea citados en los Hallazgos de `Pendientes.md`
  (Sprint 44) antes de asumir que siguen vigentes — pueden haber cambiado en sprints anteriores.

### Task 1: Salario = SMMLV automático

- [ ] Campo `es_smmlv` en `Obligacion` + migración + checkbox en el formulario Laboral.
- [ ] `LaboralStrategy` resuelve el valor vía `get_smlmv_for_year` cuando está activo.
- [ ] Test de integración: una obligación Laboral con `es_smmlv=True` en un año conocido liquida con el
      valor correcto de SMMLV de ese año.

### Task 2: Edición de Obligacion ya guardada

- [ ] `ObligacionFormDialog` acepta una obligación existente opcional, precarga sus valores, y actualiza en
      vez de insertar al guardar.
- [ ] Punto de entrada en `ExpedienteDetallePage` (ej. botón "Editar" en la fila de la tabla de
      Obligaciones, si no existe ya — verificar, Sprint 36 ya trabajó jerarquía de botones ahí).
- [ ] Test de GUI: editar una obligación existente, cambiar un campo, guardar, y confirmar que se actualizó
      (no se creó una fila nueva).

### Task 3: Descuentos del empleador (DescuentoLaboral)

- [ ] Tabla `DescuentoLaboral` + migración.
- [ ] `DescuentoLaboralFormDialog` (patrón `AbonoFormDialog`) y punto de entrada en la UI.
- [ ] `LaboralStrategy.liquidar()` resta los descuentos del neto adeudado, reutilizando el mecanismo de
      pagos/allocation ya existente en `LiquidationCore` en vez de uno nuevo.
- [ ] El reporte (PDF/Word/pantalla) muestra los descuentos aplicados.
- [ ] Test de integración: una obligación Laboral con descuentos reduce el neto adeudado en el monto
      correcto, y el descuento aparece en el reporte.

### Task 4: Edición/eliminación de EventoLaboral

- [ ] `EventoLaboralFormDialog` acepta un evento existente opcional (editar) y punto de entrada para
      eliminar.
- [ ] Test de GUI: editar y eliminar un evento laboral existente.

### Task 5: Fecha de corte editable desde la pantalla de liquidación

- [ ] `QDateEdit` en la pantalla de liquidación que permite override puntual de la fecha de corte para esa
      liquidación, sin modificar `expediente.fecha_corte_default`.
- [ ] Test que confirme que el override afecta solo esa liquidación puntual, no el expediente.

### Task 6: Verificación final

- [ ] Suite completa de tests (`pytest`) en verde.
- [ ] Confirmar los 4 puntos de la Definición de Hecho original (editar sin borrar/recrear, fecha de pago
      real accesible, descuento resta del neto y aparece en el reporte, SMMLV automático resuelve el valor
      correcto).
