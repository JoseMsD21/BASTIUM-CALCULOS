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
