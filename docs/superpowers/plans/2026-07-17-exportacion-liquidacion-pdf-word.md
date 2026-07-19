# Exportación de liquidación a PDF/Word — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a user export the "Resultado de Liquidación" screen to a PDF and to a Word document, with an
encabezado (radicado/partes/juzgado), from the GUI.

**Architecture:** Reuse the existing `LiquidationResult` → `ReportSummaryBuilder`/`ReportTableBuilder` →
dict pipeline. Fix `JudicialPDFGenerator.generate()` to include the missing "Interés" column and accept an
optional `encabezado` block. Build a new `WordReportGenerator` (`app/reports/word.py`, empty today) that
mirrors the same interface. Wire two export buttons into `ResultadoLiquidacionView`, which need
`expediente_id` (today discarded by `MainWindow._mostrar_resultado`) to look up the `Expediente` for the
encabezado.

**Tech Stack:** Python, PySide6 (Qt GUI), SQLAlchemy (existing `Expediente` model), reportlab (existing
PDF generator), `python-docx` (new Word generator, already in `requirements.txt`), pytest + pytest-qt.

**Spec:** `docs/superpowers/specs/2026-07-17-exportacion-liquidacion-pdf-word-design.md`

---

### Task 1: `build_encabezado()` — bloque de radicado/partes/juzgado

**Files:**
- Create: `app/reports/header.py`
- Test: `tests/reports/test_header.py`

- [ ] **Step 1: Write the failing test**

```python
from app.reports.header import build_encabezado


def test_build_encabezado_incluye_radicado_partes_y_juzgado():
    encabezado = build_encabezado("2026-030", "Ana", "Luis", "Juzgado 5 Civil del Circuito")

    assert encabezado == {
        "radicado": "2026-030",
        "partes": "Ana vs. Luis",
        "juzgado": "Juzgado 5 Civil del Circuito",
    }


def test_build_encabezado_sin_juzgado_queda_en_none():
    encabezado = build_encabezado("2026-030", "Ana", "Luis", None)

    assert encabezado["juzgado"] is None
    assert encabezado["partes"] == "Ana vs. Luis"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/reports/test_header.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.reports.header'`

- [ ] **Step 3: Write minimal implementation**

```python
def build_encabezado(radicado: str, demandante: str, demandado: str, juzgado: str | None) -> dict:
    """Arma el bloque de encabezado (radicado/partes/juzgado) para PDF y Word."""
    return {
        "radicado": radicado,
        "partes": f"{demandante} vs. {demandado}",
        "juzgado": juzgado,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/reports/test_header.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add app/reports/header.py tests/reports/test_header.py
git commit -m "feat(reports): add build_encabezado for PDF/Word radicado block"
```

---

### Task 2: `JudicialPDFGenerator.generate()` — columna Interés + encabezado opcional

**Files:**
- Modify: `app/reports/pdf.py:83-145` (método `generate`, no tocar `generar_documento`)
- Test: `tests/reports/test_pdf.py`

- [ ] **Step 1: Write the failing test**

```python
from app.reports.header import build_encabezado
from app.reports.pdf import JudicialPDFGenerator


def _table_data():
    return [{
        "fecha": "15/04/2026",
        "concepto": "Abono a capital",
        "base_capital": "$1,500,000.50",
        "tasa": "1.50%",
        "interes": "$10,000.00",
        "indexacion": "$0.00",
        "pago": "$500,000.00",
        "saldo_capital": "$1,500,000.50",
        "saldo_interes": "$125,000.00",
        "saldo_total": "$1,625,000.50",
    }]


def _summary():
    return {
        "total_abonos": "$500,000.00",
        "total_intereses_generados": "$10,000.00",
        "saldo_final_capital": "$1,500,000.50",
        "saldo_final_intereses": "$125,000.00",
        "saldo_final_indexacion": "$0.00",
        "gran_total_adeudado": "$1,625,000.50",
    }


def test_generate_crea_pdf_no_vacio(tmp_path):
    ruta = tmp_path / "liquidacion.pdf"
    generador = JudicialPDFGenerator(str(ruta))

    generador.generate("LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), _table_data())

    assert ruta.exists()
    assert ruta.stat().st_size > 0


def test_generate_acepta_encabezado_opcional(tmp_path):
    ruta = tmp_path / "liquidacion_con_encabezado.pdf"
    generador = JudicialPDFGenerator(str(ruta))
    encabezado = build_encabezado("2026-030", "Ana", "Luis", "Juzgado 5 Civil del Circuito")

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), _table_data(), encabezado
    )

    assert ruta.exists()
    assert ruta.stat().st_size > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/reports/test_pdf.py -v`
Expected: FAIL on `test_generate_acepta_encabezado_opcional` with
`TypeError: generate() takes from 4 to 4 positional arguments but 5 were given` (current `generate()` only
accepts `title, summary, table_data`, not a fourth `encabezado` argument).

- [ ] **Step 3: Write minimal implementation**

Replace the `generate` method in `app/reports/pdf.py` (lines 83-145) with:

```python
    def generate(self, title: str, summary: dict, table_data: list, encabezado: dict | None = None):
        """Genera el dictamen a partir de la salida del motor LiquidationCore
        (ReportSummaryBuilder.build_summary + ReportTableBuilder.build_matrix)."""
        doc = SimpleDocTemplate(self.output_path, pagesize=letter)
        elementos = []

        elementos.append(Paragraph(f"<b>{title}</b>", self.styles['BastiumTitle']))

        if encabezado:
            if encabezado.get("radicado"):
                elementos.append(Paragraph(f"Radicado: {encabezado['radicado']}", self.styles['Normal']))
            if encabezado.get("partes"):
                elementos.append(Paragraph(encabezado["partes"], self.styles['Normal']))
            if encabezado.get("juzgado"):
                elementos.append(Paragraph(f"Juzgado: {encabezado['juzgado']}", self.styles['Normal']))
            elementos.append(Spacer(1, 12))

        # Tabla de resumen ejecutivo
        filas_resumen = [
            ("Total Abonos Aplicados", summary["total_abonos"]),
            ("Intereses Generados", summary["total_intereses_generados"]),
            ("Saldo Final Capital", summary["saldo_final_capital"]),
            ("Saldo Final Intereses", summary["saldo_final_intereses"]),
            ("GRAN TOTAL ADEUDADO", summary["gran_total_adeudado"]),
        ]
        datos_resumen = [["Rubro Financiero", "Monto Liquidado"]]
        datos_resumen.extend(list(fila) for fila in filas_resumen)

        tabla_resumen = Table(datos_resumen, colWidths=[250, 150])
        tabla_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.c_black),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.c_cream),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, -1), self.c_cream),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.c_black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, self.c_burgundy),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elementos.append(tabla_resumen)
        elementos.append(Spacer(1, 30))

        # Tabla de cronología detallada
        elementos.append(Paragraph("<b>Cronología Detallada de Imputaciones y Saldos</b>", self.styles['BastiumTitle']))

        datos_cronologia = [[
            "Fecha", "Concepto", "Base Capital", "Tasa", "Interés", "Pago",
            "Saldo Capital", "Saldo Interés", "Saldo Total",
        ]]
        for fila in table_data:
            datos_cronologia.append([
                fila["fecha"],
                fila["concepto"],
                fila["base_capital"],
                fila["tasa"],
                fila["interes"],
                fila["pago"],
                fila["saldo_capital"],
                fila["saldo_interes"],
                fila["saldo_total"],
            ])

        tabla_cronologia = Table(datos_cronologia, repeatRows=1)
        tabla_cronologia.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.c_black),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.c_cream),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), self.c_cream),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.c_black),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.c_burgundy),
        ]))
        elementos.append(tabla_cronologia)

        doc.build(elementos)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/reports/test_pdf.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Run the full reports suite to check nothing else broke**

Run: `python -m pytest tests/reports/ -v`
Expected: all PASS (existing `test_summary.py`, `test_table_builder.py` untouched, still green)

- [ ] **Step 6: Commit**

```bash
git add app/reports/pdf.py tests/reports/test_pdf.py
git commit -m "fix(reports): add Interes column and optional encabezado to JudicialPDFGenerator.generate"
```

---

### Task 3: `WordReportGenerator` (`app/reports/word.py`, hoy vacío)

**Files:**
- Modify: `app/reports/word.py` (hoy 0 bytes)
- Test: `tests/reports/test_word.py`

- [ ] **Step 1: Write the failing test**

```python
from docx import Document

from app.reports.header import build_encabezado
from app.reports.word import WordReportGenerator


def _table_data():
    return [{
        "fecha": "15/04/2026",
        "concepto": "Abono a capital",
        "base_capital": "$1,500,000.50",
        "tasa": "1.50%",
        "interes": "$10,000.00",
        "indexacion": "$0.00",
        "pago": "$500,000.00",
        "saldo_capital": "$1,500,000.50",
        "saldo_interes": "$125,000.00",
        "saldo_total": "$1,625,000.50",
    }]


def _summary():
    return {
        "total_abonos": "$500,000.00",
        "total_intereses_generados": "$10,000.00",
        "saldo_final_capital": "$1,500,000.50",
        "saldo_final_intereses": "$125,000.00",
        "saldo_final_indexacion": "$0.00",
        "gran_total_adeudado": "$1,625,000.50",
    }


def test_generate_incluye_titulo_encabezado_y_tabla_cronologica(tmp_path):
    ruta = tmp_path / "liquidacion.docx"
    generador = WordReportGenerator(str(ruta))
    encabezado = build_encabezado("2026-030", "Ana", "Luis", "Juzgado 5 Civil del Circuito")

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), _table_data(), encabezado
    )

    assert ruta.exists()
    documento = Document(str(ruta))
    texto_completo = "\n".join(parrafo.text for parrafo in documento.paragraphs)

    assert "LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA" in texto_completo
    assert "Radicado: 2026-030" in texto_completo
    assert "Ana vs. Luis" in texto_completo
    assert "Juzgado: Juzgado 5 Civil del Circuito" in texto_completo

    tabla_cronologia = documento.tables[1]
    encabezados_columna = [celda.text for celda in tabla_cronologia.rows[0].cells]
    assert encabezados_columna == [
        "Fecha", "Concepto", "Base Capital", "Tasa", "Interés", "Pago",
        "Saldo Capital", "Saldo Interés", "Saldo Total",
    ]
    fila_datos = [celda.text for celda in tabla_cronologia.rows[1].cells]
    assert fila_datos[4] == "$10,000.00"


def test_generate_sin_encabezado_no_falla(tmp_path):
    ruta = tmp_path / "liquidacion_sin_encabezado.docx"
    generador = WordReportGenerator(str(ruta))

    generador.generate("LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), _table_data())

    assert ruta.exists()
    assert ruta.stat().st_size > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/reports/test_word.py -v`
Expected: FAIL — `app/reports/word.py` is empty, so `from app.reports.word import WordReportGenerator`
raises `ImportError`.

- [ ] **Step 3: Write minimal implementation**

```python
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor


class WordReportGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.c_burgundy = RGBColor(0xAE, 0x1C, 0x21)

    def generate(self, title: str, summary: dict, table_data: list, encabezado: dict | None = None) -> None:
        documento = Document()

        parrafo_titulo = documento.add_paragraph()
        parrafo_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_titulo = parrafo_titulo.add_run(title)
        run_titulo.bold = True
        run_titulo.font.size = Pt(16)
        run_titulo.font.color.rgb = self.c_burgundy

        if encabezado:
            if encabezado.get("radicado"):
                documento.add_paragraph(f"Radicado: {encabezado['radicado']}")
            if encabezado.get("partes"):
                documento.add_paragraph(encabezado["partes"])
            if encabezado.get("juzgado"):
                documento.add_paragraph(f"Juzgado: {encabezado['juzgado']}")

        documento.add_paragraph()

        filas_resumen = [
            ("Total Abonos Aplicados", summary["total_abonos"]),
            ("Intereses Generados", summary["total_intereses_generados"]),
            ("Saldo Final Capital", summary["saldo_final_capital"]),
            ("Saldo Final Intereses", summary["saldo_final_intereses"]),
            ("GRAN TOTAL ADEUDADO", summary["gran_total_adeudado"]),
        ]
        tabla_resumen = documento.add_table(rows=1, cols=2)
        tabla_resumen.style = "Table Grid"
        celdas_encabezado = tabla_resumen.rows[0].cells
        celdas_encabezado[0].text = "Rubro Financiero"
        celdas_encabezado[1].text = "Monto Liquidado"
        for etiqueta, valor in filas_resumen:
            celdas_fila = tabla_resumen.add_row().cells
            celdas_fila[0].text = etiqueta
            celdas_fila[1].text = valor

        documento.add_paragraph()
        parrafo_subtitulo = documento.add_paragraph()
        run_subtitulo = parrafo_subtitulo.add_run("Cronología Detallada de Imputaciones y Saldos")
        run_subtitulo.bold = True
        run_subtitulo.font.color.rgb = self.c_burgundy

        columnas_cronologia = [
            "Fecha", "Concepto", "Base Capital", "Tasa", "Interés", "Pago",
            "Saldo Capital", "Saldo Interés", "Saldo Total",
        ]
        tabla_cronologia = documento.add_table(rows=1, cols=len(columnas_cronologia))
        tabla_cronologia.style = "Table Grid"
        for celda, texto in zip(tabla_cronologia.rows[0].cells, columnas_cronologia):
            celda.text = texto
        for fila_datos in table_data:
            celdas_fila = tabla_cronologia.add_row().cells
            celdas_fila[0].text = fila_datos["fecha"]
            celdas_fila[1].text = fila_datos["concepto"]
            celdas_fila[2].text = fila_datos["base_capital"]
            celdas_fila[3].text = fila_datos["tasa"]
            celdas_fila[4].text = fila_datos["interes"]
            celdas_fila[5].text = fila_datos["pago"]
            celdas_fila[6].text = fila_datos["saldo_capital"]
            celdas_fila[7].text = fila_datos["saldo_interes"]
            celdas_fila[8].text = fila_datos["saldo_total"]

        documento.save(self.output_path)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/reports/test_word.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add app/reports/word.py tests/reports/test_word.py
git commit -m "feat(reports): implement WordReportGenerator with python-docx"
```

---

### Task 4: Pasar `expediente_id` hasta `ResultadoLiquidacionView`

Hoy `MainWindow._mostrar_resultado(resultado, expediente_id)` recibe `expediente_id` pero lo descarta.
`ResultadoLiquidacionView.mostrar()` no lo guarda. Sin esto, no se puede consultar el `Expediente` para
armar el encabezado al exportar (Task 5).

**Files:**
- Modify: `app/views/liquidaciones.py:6-39` (constructor y `mostrar`)
- Modify: `app/views/main_window.py:40-42` (`_mostrar_resultado`)
- Test: `tests/views/test_liquidaciones.py`
- Test: `tests/views/test_main_window.py`

- [ ] **Step 1: Write the failing tests**

En `tests/views/test_liquidaciones.py`, cambiar las dos llamadas existentes a `mostrar`:

```python
def test_muestra_una_fila_por_item_de_liquidacion(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 1).text() == "Corte final de liquidacion"


def test_muestra_los_totales(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert "1200.50" in view.etiqueta_interes_total.text()
    assert "429100.50" in view.etiqueta_saldo_final.text()
```

En `tests/views/test_main_window.py`, agregar al final del archivo:

```python
def test_main_window_pasa_expediente_id_a_la_pagina_de_resultado(qtbot):
    from datetime import date
    from decimal import Decimal

    from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
    from app.engine.liquidation.result import LiquidationResult

    window = MainWindow()
    qtbot.addWidget(window)

    debt = PendingDebt(principal=Decimal("100.00"), interest=Decimal("0.00"), indexation=Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="LIQUIDATION_CUTOFF")
    item = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Prueba",
        capital_base=Decimal("100.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
    )
    resultado = LiquidationResult(items=[item])

    window._mostrar_resultado(resultado, expediente_id=42)

    assert window.resultado_page._expediente_id == 42
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/views/test_liquidaciones.py tests/views/test_main_window.py -v`
Expected: FAIL — `TypeError: mostrar() takes 2 positional arguments but 3 were given` (o similar) en
`test_liquidaciones.py`, y `AttributeError: 'ResultadoLiquidacionView' object has no attribute
'_expediente_id'` en `test_main_window.py`.

- [ ] **Step 3: Write minimal implementation**

En `app/views/liquidaciones.py`, en el constructor agregar antes de crear la tabla:

```python
        self._resultado = None
        self._expediente_id = None
```

Y cambiar la firma y primeras líneas de `mostrar`:

```python
    def mostrar(self, resultado: LiquidationResult, expediente_id: int) -> None:
        self._resultado = resultado
        self._expediente_id = expediente_id

        self.tabla.setRowCount(len(resultado.items))
```

(el resto del cuerpo de `mostrar` queda igual).

En `app/views/main_window.py`, cambiar `_mostrar_resultado`:

```python
    def _mostrar_resultado(self, resultado, expediente_id: int) -> None:
        self.resultado_page.mostrar(resultado, expediente_id)
        self.show_page("resultado")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/views/test_liquidaciones.py tests/views/test_main_window.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add app/views/liquidaciones.py app/views/main_window.py tests/views/test_liquidaciones.py tests/views/test_main_window.py
git commit -m "fix(gui): pass expediente_id through to ResultadoLiquidacionView"
```

---

### Task 5: Botones "Exportar a PDF" / "Exportar a Word"

**Files:**
- Modify: `app/views/liquidaciones.py` (imports, constructor, nuevos métodos)
- Test: `tests/views/test_liquidaciones.py`

- [ ] **Step 1: Write the failing tests**

Agregar al final de `tests/views/test_liquidaciones.py` (agregar también los imports nuevos al inicio del
archivo: `from datetime import date` ya existe; agregar los que falten):

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import AreaDerecho, Base, Expediente


def _expediente_para_exportar(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-030",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        juzgado="Juzgado 5 Civil del Circuito",
        fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_exportar_pdf_crea_archivo_en_la_ruta_elegida(qtbot, monkeypatch, tmp_path):
    expediente_id = _expediente_para_exportar(monkeypatch)
    ruta_destino = tmp_path / "salida.pdf"
    monkeypatch.setattr(
        "app.views.liquidaciones.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(ruta_destino), "PDF (*.pdf)"),
    )
    monkeypatch.setattr("app.views.liquidaciones.QMessageBox.information", lambda *args, **kwargs: None)

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id)

    view._exportar_pdf()

    assert ruta_destino.exists()
    assert ruta_destino.stat().st_size > 0


def test_exportar_word_crea_archivo_en_la_ruta_elegida(qtbot, monkeypatch, tmp_path):
    expediente_id = _expediente_para_exportar(monkeypatch)
    ruta_destino = tmp_path / "salida.docx"
    monkeypatch.setattr(
        "app.views.liquidaciones.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(ruta_destino), "Word (*.docx)"),
    )
    monkeypatch.setattr("app.views.liquidaciones.QMessageBox.information", lambda *args, **kwargs: None)

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id)

    view._exportar_word()

    assert ruta_destino.exists()
    assert ruta_destino.stat().st_size > 0


def test_exportar_pdf_cancelado_no_crea_archivo(qtbot, monkeypatch, tmp_path):
    expediente_id = _expediente_para_exportar(monkeypatch)
    monkeypatch.setattr(
        "app.views.liquidaciones.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: ("", ""),
    )

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id)

    view._exportar_pdf()

    assert list(tmp_path.iterdir()) == []


def test_exportar_pdf_con_error_muestra_mensaje_critico(qtbot, monkeypatch, tmp_path):
    expediente_id = _expediente_para_exportar(monkeypatch)
    ruta_destino = tmp_path / "salida.pdf"
    monkeypatch.setattr(
        "app.views.liquidaciones.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(ruta_destino), "PDF (*.pdf)"),
    )

    class _GeneradorQueFalla:
        def __init__(self, ruta):
            pass

        def generate(self, *args, **kwargs):
            raise PermissionError("archivo abierto en otro programa")

    monkeypatch.setattr("app.views.liquidaciones.JudicialPDFGenerator", _GeneradorQueFalla)

    errores = []
    monkeypatch.setattr(
        "app.views.liquidaciones.QMessageBox.critical",
        lambda parent, titulo, mensaje: errores.append((titulo, mensaje)),
    )

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id)

    view._exportar_pdf()

    assert len(errores) == 1
    assert errores[0][0] == "No se pudo exportar"


def test_sanitizar_nombre_archivo_reemplaza_caracteres_invalidos():
    from app.views.liquidaciones import _sanitizar_nombre_archivo

    assert _sanitizar_nombre_archivo("2026/030 A") == "2026_030_A"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/views/test_liquidaciones.py -v`
Expected: FAIL — `AttributeError: <ResultadoLiquidacionView...> has no attribute '_exportar_pdf'` (y
similares para `_exportar_word`, `_sanitizar_nombre_archivo` no existe todavía).

- [ ] **Step 3: Write minimal implementation**

Reemplazar el contenido completo de `app/views/liquidaciones.py` por:

```python
import re

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.engine.liquidation.result import LiquidationResult
from app.engine.reports.summary import ReportSummaryBuilder
from app.engine.reports.table_builder import ReportTableBuilder
from app.reports.header import build_encabezado
from app.reports.pdf import JudicialPDFGenerator
from app.reports.word import WordReportGenerator
from database.models import Expediente


def _sanitizar_nombre_archivo(texto: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", texto)


class ResultadoLiquidacionView(QWidget):
    def __init__(self):
        super().__init__()

        self._resultado = None
        self._expediente_id = None

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "Concepto", "Capital base", "Tasa %", "Interes", "Pago", "Saldo"]
        )

        self.etiqueta_interes_total = QLabel("Interes acumulado: 0.00")
        self.etiqueta_pagos_total = QLabel("Pagos aplicados: 0.00")
        self.etiqueta_saldo_final = QLabel("Saldo final: 0.00")

        self.boton_exportar_pdf = QPushButton("Exportar a PDF")
        self.boton_exportar_pdf.clicked.connect(self._exportar_pdf)
        self.boton_exportar_word = QPushButton("Exportar a Word")
        self.boton_exportar_word.clicked.connect(self._exportar_word)

        layout_botones = QHBoxLayout()
        layout_botones.addWidget(self.boton_exportar_pdf)
        layout_botones.addWidget(self.boton_exportar_word)

        layout = QVBoxLayout()
        layout.addWidget(self.tabla)
        layout.addWidget(self.etiqueta_interes_total)
        layout.addWidget(self.etiqueta_pagos_total)
        layout.addWidget(self.etiqueta_saldo_final)
        layout.addLayout(layout_botones)
        self.setLayout(layout)

    def mostrar(self, resultado: LiquidationResult, expediente_id: int) -> None:
        self._resultado = resultado
        self._expediente_id = expediente_id

        self.tabla.setRowCount(len(resultado.items))
        for fila, item in enumerate(resultado.items):
            self.tabla.setItem(fila, 0, QTableWidgetItem(item.date.isoformat()))
            self.tabla.setItem(fila, 1, QTableWidgetItem(item.concept))
            self.tabla.setItem(fila, 2, QTableWidgetItem(str(item.capital_base)))
            self.tabla.setItem(fila, 3, QTableWidgetItem(str(item.interest_rate)))
            self.tabla.setItem(fila, 4, QTableWidgetItem(str(item.interest_amount)))
            self.tabla.setItem(fila, 5, QTableWidgetItem(str(item.payment_amount)))
            self.tabla.setItem(fila, 6, QTableWidgetItem(str(item.balance.debt.total())))

        self.etiqueta_interes_total.setText(f"Interes acumulado: {resultado.total_interest_accrued()}")
        self.etiqueta_pagos_total.setText(f"Pagos aplicados: {resultado.total_payments_applied()}")
        self.etiqueta_saldo_final.setText(f"Saldo final: {resultado.final_balance().total()}")

    def _construir_datos_reporte(self):
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)

        area_label = expediente.area_derecho.value
        for codigo, etiqueta, _habilitada in AREAS_DERECHO:
            if codigo == expediente.area_derecho.value:
                area_label = etiqueta
                break

        title = f"LIQUIDACIÓN DE OBLIGACIONES — ÁREA {area_label.upper()}"
        encabezado = build_encabezado(
            expediente.radicado, expediente.demandante, expediente.demandado, expediente.juzgado
        )
        radicado = expediente.radicado
        session.close()

        summary = ReportSummaryBuilder().build_summary(self._resultado)
        table_data = ReportTableBuilder().build_matrix(self._resultado)

        return title, encabezado, summary, table_data, radicado

    def _exportar_pdf(self) -> None:
        title, encabezado, summary, table_data, radicado = self._construir_datos_reporte()
        nombre_sugerido = f"Liquidacion_{_sanitizar_nombre_archivo(radicado)}.pdf"

        ruta, _filtro = QFileDialog.getSaveFileName(self, "Exportar a PDF", nombre_sugerido, "PDF (*.pdf)")
        if not ruta:
            return

        try:
            JudicialPDFGenerator(ruta).generate(title, summary, table_data, encabezado)
        except Exception as error:
            QMessageBox.critical(self, "No se pudo exportar", str(error))
            return

        QMessageBox.information(self, "Exportación completa", f"PDF guardado en: {ruta}")

    def _exportar_word(self) -> None:
        title, encabezado, summary, table_data, radicado = self._construir_datos_reporte()
        nombre_sugerido = f"Liquidacion_{_sanitizar_nombre_archivo(radicado)}.docx"

        ruta, _filtro = QFileDialog.getSaveFileName(self, "Exportar a Word", nombre_sugerido, "Word (*.docx)")
        if not ruta:
            return

        try:
            WordReportGenerator(ruta).generate(title, summary, table_data, encabezado)
        except Exception as error:
            QMessageBox.critical(self, "No se pudo exportar", str(error))
            return

        QMessageBox.information(self, "Exportación completa", f"Word guardado en: {ruta}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/views/test_liquidaciones.py -v`
Expected: PASS (9 passed)

- [ ] **Step 5: Run the full suite**

Run: `python -m pytest -q`
Expected: all tests pass, no regressions in other view/engine tests.

- [ ] **Step 6: Commit**

```bash
git add app/views/liquidaciones.py tests/views/test_liquidaciones.py
git commit -m "feat(gui): add Exportar a PDF / Exportar a Word buttons to ResultadoLiquidacionView"
```

---

### Task 6: Actualizar README.md y docs/GUIA_USUARIO.md

Regla obligatoria del backlog (`Pendientes.md`, encabezado): al cerrar un sprint hay que sacar el módulo de
"🚧 en desarrollo" y documentar cómo usarlo.

**Files:**
- Modify: `README.md`
- Modify: `docs/GUIA_USUARIO.md`

- [ ] **Step 1: Actualizar `README.md`**

Cambiar el encabezado de estado (línea 12):

```markdown
## Estado actual (2026-07-17)
```

Cambiar el párrafo "✅ Funcional hoy" (líneas 14-17) agregando la mención de exportación al final:

```markdown
✅ **Funcional hoy:** captura manual de expedientes y liquidación real de las áreas **Civil / Familia**
(interés del Art. 1617 del Código Civil, 6% anual, sobre obligaciones puntuales y recurrentes, con
abonos) y **Comercial** (Art. 884 C.Co., tasas remuneratoria y moratoria pactadas por obligación con
split real antes/después del vencimiento, validación de tope de usura 1.5×IBC). El resultado de
cualquier liquidación se puede exportar a **PDF** y a **Word** desde la pantalla de Resultado de
Liquidación.
```

Quitar "exportación a PDF/Word," del párrafo "🚧 En desarrollo" (líneas 19-23):

```markdown
🚧 **En desarrollo:** las áreas Laboral, Sancionatorio y Honorarios están registradas en el sistema pero
todavía no calculan (el programa avisa "Área no implementada" si se intentan usar). Indexación por IPC,
prescripción/caducidad, anatocismo comercial condicionado (Art. 886 C.Co.) y varios módulos más también
están pendientes. El plan completo, sprint por sprint, está en **[Pendientes.md](Pendientes.md)**.
```

- [ ] **Step 2: Actualizar `docs/GUIA_USUARIO.md`**

Cambiar la fecha de "Última actualización" (línea 8):

```markdown
> **Última actualización:** 2026-07-17 — refleja el estado de Civil/Familia, Comercial y exportación de
> liquidaciones a PDF/Word. Cada vez que se complete un sprint nuevo de [`Pendientes.md`](../Pendientes.md),
> esta guía se actualiza para que nunca quede desactualizada respecto al programa real.
```

Insertar una nueva sección `5.8` después de la sección `5.7` (después de la línea "guardar la obligación
(la validación ocurre al calcular, no al capturar el dato)." y antes del separador `---` que sigue):

```markdown
### 5.8. Exportar la liquidación a PDF o Word

Desde la pantalla de **Resultado de Liquidación** (después de hacer clic en "Liquidar"), al final hay dos
botones: **"Exportar a PDF"** y **"Exportar a Word"**.

1. Haz clic en el botón del formato que necesites.
2. Se abre un diálogo de "Guardar como" con un nombre sugerido (ej. `Liquidacion_2026-030.pdf`) — puedes
   cambiar el nombre y la carpeta antes de guardar.
3. El documento generado incluye: el radicado del expediente, las partes (demandante vs. demandado) y el
   juzgado (si se registró), la tabla resumen (abonos aplicados, intereses generados, saldo final) y la
   tabla cronológica completa con la misma información que ves en pantalla (fecha, concepto, capital
   base, tasa, interés, pago y saldos).
4. Si el archivo no se pudo guardar (ej. ya está abierto en otro programa, o no tienes permiso de
   escritura en esa carpeta), el programa muestra el mensaje "No se pudo exportar" con el motivo, en vez
   de fallar sin explicación.

El documento Word tiene la misma información que el PDF, pero con un estilo visual más simple (Word no
soporta el mismo nivel de personalización de reportlab) — útil cuando necesitas editar el texto antes de
presentarlo.
```

Quitar la línea sobre exportación de la sección 8 ("Funciones pendientes o en desarrollo"):

Antes:
```markdown
- 🚧 **Exportar la liquidación a PDF o Word** — hoy el resultado solo se ve en pantalla, no se puede
  guardar como archivo todavía (`Pendientes.md`, Sprint 10).
```

Después: (línea eliminada por completo)

- [ ] **Step 3: Commit**

```bash
git add README.md docs/GUIA_USUARIO.md
git commit -m "docs: document PDF/Word export for liquidation results (Sprint 10)"
```

---

## Definición de hecho (verificación final, no automatizada)

Antes de cerrar el sprint, correr manualmente:

1. `python -m pytest -q` — suite completa en verde.
2. Arrancar la app (`python main.py`), liquidar un expediente Civil/Familia real con al menos una
   obligación y un abono, hacer clic en "Exportar a PDF" y luego en "Exportar a Word", confirmar que
   ambos archivos se abren correctamente y que los montos coinciden con lo mostrado en pantalla.
