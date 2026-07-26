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
        "Fecha", "Concepto", "Base Capital", "Tasa", "Interés", "Indexación/Sanciones", "Pago",
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


def test_generate_incluye_bloque_de_renta_liquida_cuando_se_provee(tmp_path):
    ruta = tmp_path / "liquidacion_renta.docx"
    generador = WordReportGenerator(str(ruta))
    renta_liquida = {
        "ingresos_netos": "$100,000,000.00", "renta_bruta": "$60,000,000.00",
        "renta_liquida": "$40,000,000.00", "hubo_perdida_liquida": "No",
        "renta_liquida_gravable": "$35,000,000.00",
    }

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA TRIBUTARIO", _summary(), _table_data(),
        renta_liquida=renta_liquida,
    )

    documento = Document(str(ruta))
    texto_completo = "\n".join(p.text for p in documento.paragraphs)
    assert "Depuración de Renta Líquida Gravable" in texto_completo
    tabla_renta_liquida = documento.tables[2]
    fila_gravable = [celda.text for celda in tabla_renta_liquida.rows[-1].cells]
    assert "$35,000,000.00" in fila_gravable


def test_generate_sin_renta_liquida_no_agrega_el_bloque(tmp_path):
    ruta = tmp_path / "liquidacion_sin_renta.docx"
    generador = WordReportGenerator(str(ruta))

    generador.generate("LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), _table_data())

    documento = Document(str(ruta))
    assert len(documento.tables) == 2


def test_generate_incluye_columna_de_indexacion_sanciones(tmp_path):
    ruta = tmp_path / "liquidacion.docx"
    generador = WordReportGenerator(str(ruta))

    generador.generate("LIQUIDACIÓN DE OBLIGACIONES — ÁREA TRIBUTARIO", _summary(), _table_data())

    documento = Document(str(ruta))
    tabla_cronologia = documento.tables[1]
    encabezados = [celda.text for celda in tabla_cronologia.rows[0].cells]
    assert "Indexación/Sanciones" in encabezados
    fila_datos = [celda.text for celda in tabla_cronologia.rows[1].cells]
    assert "$0.00" in fila_datos
