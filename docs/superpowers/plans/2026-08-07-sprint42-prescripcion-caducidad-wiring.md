# Sprint 42 — Conectar el motor de prescripción/caducidad al flujo real de liquidación Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Decisión de diseño ya tomada por el usuario (2026-08-07):** opción (b) del sprint original — **marcar
con advertencia visual, no excluir automáticamente**. Una obligación prescrita/caducada se sigue incluyendo
en el cálculo (el total NO cambia en silencio); queda marcada en pantalla y en el PDF/Word como "obligación
prescrita, no exigible" para que el abogado decida qué hacer con esa información.

**Goal:** Cualquier liquidación de cualquier área evalúa la prescripción/caducidad de cada obligación
(usando el motor ya existente y probado de `app/engine/temporal/prescripcion.py`) y expone ese estado en la
tabla de resultados y en el PDF/Word — sin excluir nada del total automáticamente.

**Architecture:** `app/engine/temporal/prescripcion.py` ya tiene `calcular_prescripcion(fecha_exigibilidad,
tipo_accion) -> date` y `filtrar_cuotas_prescritas(eventos, fecha_corte, tipo_accion) -> (vivas, prescritas)`
(esta última YA separa eventos en dos listas — reutilizarla tal cual para **detectar** cuáles están
prescritos, sin usar el resultado para excluirlos: procesar la unión de `vivas + prescritas` en
`LiquidationCore` igual que hoy, pero guardar el conjunto de eventos/fechas prescritos aparte para poder
marcar las filas correspondientes después). El `tipo_accion` a usar por defecto es `TipoAccion.EJECUTIVA`
— mismo default ya usado por el Dashboard del Sprint 33 (ver `Preguntas-Para-Abogado-Abiertas.md`, sección
"Sprint 33", pregunta todavía abierta sobre si cada área debería usar un tipo de acción distinto; este
sprint reutiliza el mismo default provisional, no duplicar la pregunta). Centralizar el wiring en
`UniversalLiquidationService` (o el punto común que ya usan las 6 `AreaStrategy` para invocar
`LiquidationCore`, verificar el nombre exacto leyendo `app/services/area_strategy.py`) en vez de repetirlo 6
veces. Agregar un campo `prescrita: bool` a `LiquidationItem` (`app/engine/liquidation/models.py`, con
default `False` para no romper construcciones existentes) que la capa de wiring puebla comparando la fecha
de cada evento contra `calcular_prescripcion()`. `table_builder.py`/`pdf.py`/`word.py` (verificar nombre
exacto del generador Word) muestran un indicador visual (ej. un ícono de advertencia o texto en rojo) en las
filas donde `prescrita is True`, y la vista de resultado en pantalla (`app/views/liquidaciones.py`) hace lo
mismo en la tabla.

**Tech Stack:** Python 3.14, `Decimal`/`date`, PySide6 (indicador visual en tabla), pytest.

---

### Contexto compartido entre tareas

- **No excluir nada del total** — es la decisión explícita del usuario. El `LiquidationResult` final
  (saldo, totales) no cambia respecto a hoy; solo se agrega información de estado por fila.
- **Alcance excluido:** no recalcular automáticamente los plazos de caducidad "manuales" que ya exige
  capturar el Sprint 7 — sigue siendo responsabilidad del abogado cargar ese dato.
- Verificar leyendo el código el punto exacto donde cada `AreaStrategy.liquidar()` invoca
  `LiquidationCore.process()` antes de decidir dónde centralizar el wiring — no asumas el nombre de
  `UniversalLiquidationService` sin confirmarlo.

### Task 1: Campo `prescrita` en LiquidationItem y wiring centralizado

- [ ] Agregar `prescrita: bool = False` a `LiquidationItem`.
- [ ] Wiring centralizado que usa `filtrar_cuotas_prescritas`/`calcular_prescripcion` para determinar, por
      evento/fila, si su obligación de origen ya venció su plazo de prescripción/caducidad a la fecha de
      corte de la liquidación, poblando el campo nuevo sin alterar el procesamiento normal de
      `LiquidationCore` (todo se sigue calculando igual, incluidas las filas prescritas).
- [ ] Test de integración: un expediente con una obligación cuyo plazo de prescripción ya venció aparece con
      `prescrita=True` en la fila correspondiente, y el total liquidado NO cambia respecto al mismo caso sin
      el wiring (mismo saldo final, con o sin la marca).

### Task 2: Indicador visual en pantalla y en PDF/Word

- [ ] Tabla de resultados en `app/views/liquidaciones.py` muestra un indicador visual (ícono/color/texto)
      en las filas con `prescrita=True`.
- [ ] `table_builder.py`/`pdf.py`/el generador de Word correspondiente muestran el mismo estado en el
      documento exportado.
- [ ] Tests que confirmen la marca visual en pantalla y en el PDF exportado (o en la estructura de datos que
      alimenta el PDF, si no hay forma directa de testear el render visual).

### Task 3: Verificación final

- [ ] Suite completa de tests (`pytest`) en verde, incluidas las 6 `AreaStrategy` (confirmar que ninguna
      quedó sin el wiring).
- [ ] Confirmar que ningún saldo final de ninguna liquidación existente cambió por este sprint (el cambio es
      puramente informativo).
