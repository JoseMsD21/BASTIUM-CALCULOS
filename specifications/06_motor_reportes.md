# Motor de Reportes

## Que hace
Provee metricas listas para presentar (interes acumulado, pagos aplicados, saldo final) a partir de un
`LiquidationResult`, y (por separado, no conectado aun) genera graficas y documentos PDF.

## Componentes
- `app/engine/liquidation/result.py`: `LiquidationResult.total_interest_accrued()`,
  `.total_payments_applied()`, `.final_balance()`.
- `app/engine/reports/summary.py`, `table_builder.py`, `chart_builder.py`: utilidades de reportes de mas
  bajo nivel, usadas por los tests existentes (`tests/reports/`) pero no conectadas a la GUI.
- `app/reports/charts.py` (`BastiumChartGenerator`), `app/reports/pdf.py` (`JudicialPDFGenerator`),
  `app/reports/word.py` (vacio): generacion de graficas y documentos. Usados antes por el script de
  consola (`main.py` original); **no estan conectados a la GUI en este MVP**.

## Estado en el MVP
La pantalla "Resultado de Liquidacion" (`app/views/liquidaciones.py`) muestra la tabla y los totales
directamente en pantalla. No hay boton de exportar a PDF/Word todavia.

## Pendiente (no implementado aun)
- Boton "Exportar a PDF" en la pantalla de resultado, reutilizando `JudicialPDFGenerator`.
- Boton "Exportar a Word", implementando `app/reports/word.py` (vacio hoy).

Ver `Pendientes.md`.
