# Diseño — Sprint 10: Exportación de liquidación a PDF/Word

**Fecha:** 2026-07-17
**Origen:** `Pendientes.md`, sección "Sprint 10 — Exportación de liquidación a PDF/Word".
**Estado:** Aprobado por el usuario, listo para plan de implementación.

## Contexto

`Pendientes.md` describe este sprint asumiendo que el "adaptador" entre `LiquidationResult` y el formato
de entrada de `JudicialPDFGenerator` no existe. Al revisar el código eso resultó ser parcialmente
incorrecto: `app/engine/reports/summary.py` (`ReportSummaryBuilder.build_summary()`) y
`app/engine/reports/table_builder.py` (`ReportTableBuilder.build_matrix()`) ya convierten un
`LiquidationResult` a diccionarios genéricos, y `app/reports/pdf.py` ya tiene un método
`JudicialPDFGenerator.generate(title, summary, table_data)` genérico (no acoplado a "Alimentos") que
consume exactamente ese formato. Ambos builders están cubiertos por tests (`tests/reports/`).

Lo que de verdad falta:
1. La tabla de cronología de `generate()` omite la columna "Interés" por fila (sí está en `table_data`,
   pero el método no la renderiza) — inconsistente con lo que muestra la GUI (`ResultadoLiquidacionView`,
   que sí tiene columna "Interes").
2. No hay ningún encabezado con datos del expediente (radicado, partes, juzgado) en el documento — hoy
   solo lleva un título.
3. `app/reports/word.py` está vacío — no existe generación de Word.
4. No hay botones de exportar en la GUI, y `MainWindow._mostrar_resultado` recibe `expediente_id` pero lo
   descarta en vez de pasarlo a `ResultadoLiquidacionView`.
5. El método legacy `JudicialPDFGenerator.generar_documento()` (título hardcodeado "LIQUIDACIÓN
   PROVISIONAL DE ALIMENTOS", usado antes por el script de consola descontinuado) no tiene otros
   llamadores hoy — se deja intacto, fuera de alcance.

## Decisiones tomadas con el usuario

1. **Agregar la columna "Interés" por fila** a la tabla de cronología del PDF (y su equivalente en Word),
   además de las columnas ya existentes (Fecha, Concepto, Base Capital, Tasa, Pago, Saldo Capital, Saldo
   Interés, Saldo Total) — 9 columnas en total. Más fiel a lo que el usuario ve en pantalla.
2. **Encabezado completo con datos del expediente**: título genérico por área + bloque con Radicado,
   Demandante vs. Demandado y Juzgado. Esto requiere pasar `expediente_id` desde `MainWindow` hasta
   `ResultadoLiquidacionView` (hoy se descarta) para poder consultar el `Expediente` al momento de
   exportar.
3. **Sin gráfica en este sprint.** La liquidación Civil/Familia produce filas cronológicas (eventos en el
   tiempo), no rubros independientes — la gráfica de barras de `BastiumChartGenerator` (pensada para
   distribución de capital por rubro) no encaja bien aquí. Se deja fuera; una gráfica de evolución de
   saldo en el tiempo puede evaluarse en un sprint futuro con diseño propio.
4. **Diálogo de guardar (`QFileDialog`)**: al hacer clic en "Exportar a PDF"/"Exportar a Word" se abre un
   diálogo nativo de "Guardar como" con un nombre sugerido, no una ruta fija automática.
5. **Los cinco puntos del "Protocolo de UI" de indexación** (PDF maestro, pág. 22 — citar fuente DANE/
   Banco de la República, listar Vh y fechas, desglosar índice inicial/final, mostrar operación
   aritmética, mencionar "hecho notorio") **quedan fuera de alcance de este sprint**: la indexación IPC
   no está conectada a ningún área todavía (Sprint 8 pendiente), por lo que `indexation_amount` es
   siempre `0.00` hoy. Construir ese protocolo formal ahora sería especular sobre datos que no existen
   todavía. Se retoma cuando el Sprint 8 conecte la indexación real.

## Cambios en `app/reports/pdf.py`

`JudicialPDFGenerator.generate(title, summary, table_data, encabezado=None)`:
- Nuevo parámetro opcional `encabezado: dict | None`. Si viene, se renderiza como un párrafo (estilo
  normal, no `BastiumTitle`) inmediatamente debajo del título, antes de la tabla de resumen. Formato:
  `Radicado: {radicado}` / `{demandante} vs. {demandado}` / `Juzgado: {juzgado}` (una línea por dato
  presente; si `juzgado` es `None`, se omite esa línea).
- La tabla de cronología (`datos_cronologia`) gana la columna "Interés" entre "Tasa" y "Pago":
  `["Fecha", "Concepto", "Base Capital", "Tasa", "Interés", "Pago", "Saldo Capital", "Saldo Interés",
  "Saldo Total"]`, leyendo `fila["interes"]` de `table_data` (la clave ya existe en
  `ReportTableBuilder.build_matrix()`, solo no se estaba usando).
- `generar_documento()` no se toca.

## Encabezado — `app/reports/header.py` (nuevo)

Módulo puro, sin dependencias de Qt ni SQLAlchemy, para que sea testable con valores simples:

```python
def build_encabezado(radicado: str, demandante: str, demandado: str, juzgado: str | None) -> dict:
    """Arma el diccionario de encabezado para JudicialPDFGenerator/WordReportGenerator."""
```

Retorna algo como `{"radicado": ..., "partes": f"{demandante} vs. {demandado}", "juzgado": juzgado}`.
Tanto `pdf.py` como `word.py` consumen este mismo dict, así el formato del encabezado es idéntico en
ambos documentos.

## `app/reports/word.py` (nuevo, hoy vacío)

`class WordReportGenerator`, misma interfaz que el PDF para que el código de la GUI no tenga que
distinguir entre ambos:

```python
class WordReportGenerator:
    def __init__(self, output_path: str): ...
    def generate(self, title: str, summary: dict, table_data: list, encabezado: dict | None = None) -> None: ...
```

Usa `python-docx` (ya en `requirements.txt`):
- Título: párrafo centrado, texto en color borgoña (`RGBColor(0xAE, 0x1C, 0x21)`), tamaño ~16pt, negrita.
- Encabezado (si viene): párrafos normales bajo el título, mismo contenido que en el PDF.
- Tabla de resumen: `document.add_table()` de 2 columnas (Rubro / Monto), fila de encabezado en negrita,
  bordes simples (estilo de tabla `Table Grid` de docx, la aproximación más cercana disponible sin
  manipular XML de bajo nivel para fondos de celda).
- Tabla de cronología: mismas 9 columnas que el PDF, fila de encabezado en negrita.
- No se replica el fondo crema de página (no soportado de forma simple en `python-docx`); se documenta
  como limitación conocida de fidelidad visual frente al PDF, aceptada por el usuario al aprobar "sin
  gráfica / mejor esfuerzo" en este sprint.

## Wiring GUI

`app/views/main_window.py`:
- `_mostrar_resultado(self, resultado, expediente_id)`: cambia
  `self.resultado_page.mostrar(resultado)` → `self.resultado_page.mostrar(resultado, expediente_id)`.

`app/views/liquidaciones.py` (`ResultadoLiquidacionView`):
- `mostrar(self, resultado: LiquidationResult, expediente_id: int) -> None`: guarda
  `self._resultado = resultado` y `self._expediente_id = expediente_id` además de poblar la tabla como
  hoy.
- Dos `QPushButton` nuevos: "Exportar a PDF" y "Exportar a Word", agregados al layout existente.
- Método privado común `_construir_datos_reporte(self) -> tuple[str, dict, dict, list]` (title,
  encabezado, summary, table_data):
  - `session = session_module.get_session()`
  - `expediente = session.get(Expediente, self._expediente_id)`
  - `area_label` = buscar en `AREAS_DERECHO` (`app/core/constants.py`) el label legible correspondiente a
    `expediente.area_derecho.value`.
  - `title = f"LIQUIDACIÓN DE OBLIGACIONES — ÁREA {area_label.upper()}"`
  - `encabezado = build_encabezado(expediente.radicado, expediente.demandante, expediente.demandado, expediente.juzgado)`
  - `summary = ReportSummaryBuilder().build_summary(self._resultado)`
  - `table_data = ReportTableBuilder().build_matrix(self._resultado)`
  - `session.close()`
  - retorna la tupla.
- `_exportar_pdf(self)`:
  - nombre sugerido: `Liquidacion_{radicado_saneado}.pdf` (saneo simple: reemplazar `/`, espacios y otros
    caracteres no válidos en nombre de archivo por `_`).
  - `QFileDialog.getSaveFileName(self, "Exportar a PDF", nombre_sugerido, "PDF (*.pdf)")`.
  - si el usuario elige ruta: `try`: construir datos vía `_construir_datos_reporte()`, llamar
    `JudicialPDFGenerator(ruta).generate(title, summary, table_data, encabezado)`, mostrar
    `QMessageBox.information` de éxito con la ruta. `except Exception`: `QMessageBox.critical` con el
    mensaje de error (ej. permiso denegado, disco lleno, archivo abierto en otro programa).
- `_exportar_word(self)`: mismo patrón, filtro `"Word (*.docx)"`, usa `WordReportGenerator`.

## Testing

- `tests/reports/test_header.py`: `build_encabezado()` con valores conocidos, incluyendo el caso
  `juzgado=None` → confirma que la línea de juzgado se omite.
- `tests/reports/test_pdf.py` (nuevo): con un `table_data`/`summary` fijo (fixture pequeña, reutilizando
  el patrón de `tests/reports/test_table_builder.py`), llamar `generate()` contra un archivo temporal
  (`tmp_path` de pytest) y verificar que el archivo se crea y no está vacío. No se testea el render visual
  interno de reportlab (fuera de alcance, según la Definición de Hecho del sprint).
- `tests/reports/test_word.py` (nuevo): mismo patrón, pero además reabre el `.docx` generado con
  `python-docx` para verificar que el título, las líneas de encabezado y algunos valores de la tabla
  (ej. un monto formateado) aparecen como texto en los párrafos/celdas — esto sí es inspeccionable a
  diferencia del PDF binario.
- Smoke test manual (Definición de Hecho del sprint): desde la GUI, liquidar un expediente Civil/Familia
  real y exportar a PDF y a Word, confirmando que los montos coinciden exactamente con lo mostrado en
  pantalla.

## Fuera de alcance (explícito)

- Gráfica de evolución de saldo u otra visualización — diferido a un sprint futuro.
- Protocolo formal de presentación de indexación ante autoridades (5 puntos del PDF maestro, pág. 22) —
  diferido hasta que el Sprint 8 conecte la indexación IPC real.
- Fidelidad visual completa del Word frente al PDF (fondo crema de página) — limitación conocida y
  aceptada de `python-docx`.
- Rediseño visual de las plantillas (se mantiene el estilo borgoña/crema ya definido).
- Exportación para áreas no operables todavía (Laboral, Sancionatorio, Honorarios) — el adaptador es
  genérico y funcionará para ellas en cuanto se habiliten, sin cambios adicionales.

## Definición de hecho

- Desde la GUI, liquidar un expediente Civil/Familia real y exportarlo a PDF y a Word sin errores, con
  los montos coincidiendo exactamente con lo mostrado en pantalla, y con el encabezado (radicado, partes,
  juzgado) correcto.
- `build_encabezado()`, y los adaptadores de `generate()` de PDF y Word, cubiertos por tests
  automatizados (no se testea reportlab/python-docx en sí, solo que los datos de entrada se arman y
  fluyen correctamente).
- Suite completa sigue en verde.
- `README.md` y `docs/GUIA_USUARIO.md` actualizados: documentar los botones "Exportar a PDF" y "Exportar
  a Word" en la pantalla de Resultado de Liquidación, igual que se documentó el resto del flujo
  Civil/Familia.
