# Motor de Reportes

## Que hace
Provee metricas listas para presentar (interes acumulado, pagos aplicados, saldo final) a partir de un
`LiquidationResult`, y genera graficas y documentos PDF/Word, conectados a la GUI desde el Sprint 10.

## Componentes
- `app/engine/liquidation/result.py`: `LiquidationResult.total_interest_accrued()`,
  `.total_payments_applied()`, `.final_balance()`.
- `app/engine/reports/summary.py`, `table_builder.py`, `chart_builder.py`: `ReportSummaryBuilder` y
  `ReportTableBuilder` construyen las filas/totales (incluida la fila de indexacion) que muestran tanto la
  pantalla de Resultado como los exportadores PDF/Word.
- `app/reports/charts.py` (`BastiumChartGenerator`), `app/reports/pdf.py` (`JudicialPDFGenerator`),
  `app/reports/word.py`: generacion de graficas y documentos, conectados a los botones "Exportar a PDF" y
  "Exportar a Word" de la pantalla de resultado.

## Estado en el MVP
La pantalla "Resultado de Liquidacion" (`app/views/liquidaciones.py`) muestra la tabla y los totales en
pantalla, con botones **"Exportar a PDF"** y **"Exportar a Word"** que generan el documento con
`QFileDialog.getSaveFileName` para elegir la ruta de guardado. Los 3 canales (GUI, PDF, Word) muestran las
mismas filas, incluida la de indexacion (bucket usado por Civil/Familia y por las sanciones tributarias).

## Pendiente (no implementado aun)
- Rendimiento del motor de tasas, indices e historial para reportes grandes — ver `docs/Pendientes.md`,
  Sprint 25.
- Responsividad de la UI al exportar (liquidar/exportar sin congelar la interfaz) — ver `docs/Pendientes.md`,
  Sprint 26.

Ver `docs/Pendientes.md`.
