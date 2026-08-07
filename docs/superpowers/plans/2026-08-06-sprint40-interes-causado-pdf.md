# Sprint 40 — El interés causado no aparece en la tabla del PDF Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Decisión de diseño ya tomada (verificada leyendo `app/engine/liquidation/engine.py` el 2026-08-06):** de
las dos opciones que planteaba `Pendientes.md` — (a) evento sintético "INTEREST" por cada causación, o (b)
`interest_amount` como delta —, se implementa una variante correcta de (b): **cada `LiquidationItem` recibe
como `interest_amount` el interés que se causó por paso del tiempo inmediatamente antes de ese evento**
(no un delta crudo de `balance.debt.interest`, que iría negativo en filas de pago — ver razonamiento
abajo). Se descarta (a) explícitamente: agregar un evento sintético nuevo interactúa con el motor de
auditoría (Sprint 9, `reconstruir_liquidacion()`) y es más riesgoso sin necesidad.

**Por qué no un delta crudo de `balance.debt.interest`:** un evento `PAYMENT` puede reducir
`debt.interest` (abono aplicado a intereses) y `CAPITALIZACION_INTERESES_ANATOCISMO` mueve interés a
capital (también reduce `debt.interest`). Si `interest_amount` fuera literalmente
`current.debt.interest - previous.debt.interest`, esas filas mostrarían un interés **negativo** en el PDF,
lo cual no tiene sentido para "interés causado en este período" y confundiría al juez que audita el
documento. En cambio, capturar el interés efectivamente causado por `_accrue_time_passage` en el tramo
justo antes de cada evento es siempre `>= 0` y representa correctamente "cuánto interés se generó desde el
evento anterior hasta este".

**Goal:** La tabla de detalle del PDF/Word (vía `table_builder.py`/`pdf.py`) deja de mostrar 0 en la
columna de interés en todas las filas donde sí se causó interés por mora. El resumen ejecutivo
(`saldo_final_intereses`) no cambia (ya era correcto). `total_interest_accrued()` (usado en
`total_intereses_generados` del resumen) pasa a reflejar el interés real acumulado, no 0.

**Architecture:** En `LiquidationCore.process()` (`app/engine/liquidation/engine.py:50-83`), justo antes de
cada llamada a `self._accrue_time_passage(event.date)` (línea 57), capturar
`interes_antes = self._current_debt.interest`. Después de la llamada, `interes_causado_periodo =
self._current_debt.interest - interes_antes` (siempre `>= 0`, porque `_accrue_time_passage` solo suma
interés, nunca lo resta). Pasar ese valor a `self._process_event(event, interes_causado_periodo)` (nueva
firma) para que se sume al `interest_amount` que ya calcula el método (el branch `event_type == "INTEREST"`
sigue existiendo tal cual para compatibilidad con los tests que lo usan explícitamente — ambos valores se
suman, ya que son conceptualmente aditivos: interés causado automáticamente por el tiempo + interés
inyectado manualmente por un evento explícito de tipo INTEREST, que en producción nunca ocurre). Aplicar el
mismo cálculo para el `closing_item` final (línea 62-81): capturar el interés antes de la última llamada a
`self._accrue_time_passage(cutoff_date)` y usarlo en vez del `Decimal("0.00")` hardcodeado de la línea 75.
No modificar `table_builder.py`/`pdf.py` — ya imprimen `item.interest_amount` tal cual, que pasa a tener el
valor correcto sin cambios ahí.

**Riesgo conocido a verificar (Sprint 9, motor de auditoría):** `reconstruir_liquidacion()` debe seguir
reproduciendo exactamente las mismas cifras al reconstruir liquidaciones históricas — como este cambio no
agrega ningún evento nuevo (solo cambia qué valor se asigna a un campo ya existente de `LiquidationItem` a
partir de estado que el motor ya calculaba), no debería afectar la reconstrucción, pero hay que confirmarlo
corriendo la suite de tests de auditoría existente.

**Tech Stack:** Python 3.14, `Decimal`, pytest (incluye `tests/liquidation/test_engine.py`,
`tests/services/test_area_strategy.py`, tests de auditoría/reconstrucción).

---

### Contexto compartido entre tareas

- No tocar `app/reports/pdf.py` ni `app/engine/reports/table_builder.py` salvo que la verificación de Task
  2 encuentre que sí hace falta (no debería).
- `total_interest_accrued()` (`app/engine/liquidation/result.py:23-24`) ya separa correctamente por suma de
  `item.interest_amount` — no requiere cambios, se corrige automáticamente al corregir el campo en origen.

### Task 1: Atribuir interés causado por paso del tiempo a cada LiquidationItem

- [ ] Modificar `LiquidationCore.process()` y `_process_event()` (`app/engine/liquidation/engine.py`) según
      el diseño de arriba: capturar el interés causado por `_accrue_time_passage` inmediatamente antes de
      cada evento y sumarlo al `interest_amount` de la fila resultante (incluida la fila de cierre final).
- [ ] Test de integración: liquidar una obligación con al menos dos períodos de mora (sin pagos que
      reduzcan intereses) y confirmar que cada fila relevante de la tabla de detalle tiene
      `interest_amount > 0` coherente con los días transcurridos y la tasa aplicada.
- [ ] Test de regresión: la suma de la columna "Interés" de todas las filas coincide exactamente con
      `final_debt.interest` (`saldo_final_intereses` del resumen) en un caso sin pagos que reduzcan
      intereses ni capitalización de intereses.
- [ ] Test que confirme que el branch `event_type == "INTEREST"` explícito (usado hoy solo en tests)
      sigue funcionando y se suma correctamente al interés causado por tiempo, no lo reemplaza.
- [ ] Correr la suite completa de tests de las 6 `AreaStrategy` (Civil/Familia, Comercial, Laboral,
      Sancionatorio, Honorarios, Tributario) y del motor de auditoría (Sprint 9,
      `reconstruir_liquidacion()`) — confirmar que ninguna cifra de saldo final cambió (el bug es solo de
      desglose por fila, el saldo final ya era correcto) y que la reconstrucción histórica sigue
      reproduciendo las mismas cifras.

### Task 2: Confirmar que table_builder.py/pdf.py no necesitan cambios

- [ ] Verificar (leyendo el código, no asumiendo) que `table_builder.py:21` y `pdf.py` efectivamente solo
      imprimen `item.interest_amount` sin lógica adicional que dependiera del bug anterior (ej. algún
      fallback que calculaba el interés de otra forma porque `interest_amount` era 0) — si existe tal
      fallback, eliminarlo ahora que el campo es correcto en origen.

### Task 3: Verificación final

- [ ] Suite completa de tests (`pytest`) en verde.
- [ ] Confirmar las 3 verificaciones de la Definición de Hecho del sprint en `Pendientes.md`.
