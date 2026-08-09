# Sprint 46 — El saldo a favor de un sobrepago no aparece en el PDF/Word ni en la pantalla de resultado Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** El saldo a favor de un sobrepago (ya calculado correctamente por `LiquidationCore`/`AllocationEngine`
desde el Sprint 23, en `LiquidationItem.saldo_a_favor` y `LiquidationResult.total_saldo_a_favor()`) se
vuelve visible en el resumen ejecutivo del PDF/Word, en la tabla de detalle, y en la pantalla de resultado —
sin cambiar el significado de ningún total ya existente.

**Architecture:** `ReportSummaryBuilder.build_summary()` (`app/engine/reports/summary.py`) agrega la clave
`"saldo_a_favor"` al diccionario retornado **solo cuando** `result.total_saldo_a_favor() > Decimal("0.00")`
— omitida por completo del diccionario cuando es cero (no como string `"$0.00"`), para que cada consumidor
(`pdf.py`, `word.py`, `liquidaciones.py`) sepa mostrar la línea con un simple `if "saldo_a_favor" in
summary:` en vez of duplicar la comparación con cero en cada uno. `ReportTableBuilder.build_matrix()`
(`app/engine/reports/table_builder.py`) agrega la clave `"saldo_a_favor"` a cada fila del diccionario
(formateada igual que `"pago"`), reutilizando `item.saldo_a_favor` que ya existe en `LiquidationItem` —
consistente con el patrón ya usado para `"prescrita"` (Sprint 42): siempre presente en la fila, formateada
en `$0.00` cuando no aplica, y los consumidores deciden si la muestran solo cuando no es cero. `pdf.py`/
`word.py` agregan la línea "Saldo a favor del deudor" a la lista de tuplas (etiqueta, valor) del resumen
ejecutivo (mismo patrón que `"GRAN TOTAL ADEUDADO"`), condicionada a la presencia de la clave. La tabla de
detalle en PDF/Word ya itera las claves de `build_matrix()` genéricamente (verificar leyendo el código antes
de asumir) — si no lo hace, agregar la columna "Saldo a favor" al layout existente sin romper el de las 6
áreas. `liquidaciones.py` (`ResultadoLiquidacionView`) agrega un `QLabel` junto a `etiqueta_saldo_final`,
visible solo cuando `resultado.total_saldo_a_favor() > 0`.

**Tech Stack:** Python 3.14, `Decimal`, PySide6 6.11, `python-docx`/generador PDF existentes, pytest.

---

### Contexto compartido entre tareas

- No cambiar el significado de ninguna columna/total ya existente — verificar con un test que ningún número
  ya mostrado hoy cambie de valor, solo se agrega visibilidad de un dato nuevo.
- `LiquidationItem.saldo_a_favor` y `LiquidationResult.total_saldo_a_favor()` YA EXISTEN y ya calculan
  correctamente (Sprint 23) — este sprint es puramente de reportes/presentación, no toca `LiquidationCore`
  ni `AllocationEngine`.
- Verificar que una liquidación con sobrepago reconstruida desde su `AuditLog` (Sprint 9) también muestre el
  saldo a favor correctamente — no hace falta backfill, el dato ya está en el snapshot histórico.

### Task 1: Resumen ejecutivo (summary.py + consumidores)

- [ ] `build_summary()` agrega `"saldo_a_favor"` al diccionario solo cuando `total_saldo_a_favor() > 0`.
- [ ] `pdf.py`/`word.py` muestran "Saldo a favor del deudor" en el resumen cuando la clave está presente.
- [ ] Test que confirme: liquidación con sobrepago → la línea aparece con el monto exacto; liquidación sin
      sobrepago → la clave no está en el diccionario y la línea no aparece en el PDF/Word generado.

### Task 2: Tabla de detalle (table_builder.py + consumidores)

- [ ] `build_matrix()` agrega `"saldo_a_favor"` a cada fila (formateada, igual patrón que `"pago"`).
- [ ] La tabla de detalle del PDF/Word muestra el valor en la fila del evento `PAYMENT` que sobrepagó, sin
      romper el layout ya usado por las 6 áreas (evaluar durante la implementación si conviene una columna
      nueva o reutilizar espacio existente).
- [ ] Test que confirme el valor exacto en la fila correspondiente.

### Task 3: Pantalla de resultado

- [ ] `ResultadoLiquidacionView` muestra el saldo a favor junto a los demás totales, visible solo cuando es
      mayor a cero (nada, ni una fila vacía, cuando es cero).
- [ ] Test de GUI que confirme ambos casos (con y sin sobrepago).

### Task 4: Verificación final

- [ ] Test de integración: liquidar un expediente con un sobrepago real (pago mayor a la deuda) y confirmar
      que PDF, Word y pantalla muestran el saldo a favor con el monto exacto.
- [ ] Confirmar que ningún total/columna ya existente cambió de valor en ningún test preexistente.
- [ ] Suite completa de tests (`pytest`) en verde.
