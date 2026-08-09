from reportlab.lib import colors
from reportlab.platypus import TableStyle

from app.reports.header import build_encabezado
from app.reports.pdf import JudicialPDFGenerator


def _table_data():
    return [
        {
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
        }
    ]


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

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), _table_data()
    )

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


def test_generate_incluye_bloque_de_renta_liquida_cuando_se_provee(tmp_path):
    ruta = tmp_path / "liquidacion_renta.pdf"
    generador = JudicialPDFGenerator(str(ruta))
    renta_liquida = {
        "ingresos_netos": "$100,000,000.00",
        "renta_bruta": "$60,000,000.00",
        "renta_liquida": "$40,000,000.00",
        "hubo_perdida_liquida": "No",
        "renta_liquida_gravable": "$35,000,000.00",
    }

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA TRIBUTARIO",
        _summary(),
        _table_data(),
        renta_liquida=renta_liquida,
    )

    assert ruta.exists()
    assert ruta.stat().st_size > 0


def test_generate_sin_renta_liquida_no_falla(tmp_path):
    ruta = tmp_path / "liquidacion_sin_renta.pdf"
    generador = JudicialPDFGenerator(str(ruta))

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), _table_data()
    )

    assert ruta.exists()


def test_generate_resalta_en_rojo_las_filas_prescritas(tmp_path, monkeypatch):
    # Sprint 42: ReportTableBuilder.build_matrix ya expone "prescrita" por fila
    # (ver tests/reports/test_table_builder.py) -- generate() debe resaltarla en
    # el PDF (indicador visual, aqui: texto en rojo) sin excluirla de la tabla ni
    # tocar ningun monto.
    estilo_real = TableStyle
    llamadas_estilo = []

    def _estilo_capturado(comandos):
        llamadas_estilo.append(comandos)
        return estilo_real(comandos)

    monkeypatch.setattr("app.reports.pdf.TableStyle", _estilo_capturado)

    ruta = tmp_path / "liquidacion_prescrita.pdf"
    generador = JudicialPDFGenerator(str(ruta))
    datos = _table_data()
    datos[0]["prescrita"] = True

    generador.generate("LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), datos)

    assert ruta.exists()
    # llamadas_estilo[0] es la tabla de resumen ejecutivo, [1] es la cronologia
    # detallada (unica que tiene filas de datos marcables por item).
    comandos_cronologia = llamadas_estilo[1]
    assert any(
        comando[0] == "TEXTCOLOR" and comando[1] == (0, 1) and comando[3] == colors.red
        for comando in comandos_cronologia
    )


def test_generate_no_resalta_filas_sin_marcar(tmp_path, monkeypatch):
    estilo_real = TableStyle
    llamadas_estilo = []

    def _estilo_capturado(comandos):
        llamadas_estilo.append(comandos)
        return estilo_real(comandos)

    monkeypatch.setattr("app.reports.pdf.TableStyle", _estilo_capturado)

    ruta = tmp_path / "liquidacion_sin_marca.pdf"
    generador = JudicialPDFGenerator(str(ruta))

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), _table_data()
    )

    comandos_cronologia = llamadas_estilo[1]
    assert not any(
        comando[0] == "TEXTCOLOR" and comando[3] == colors.red for comando in comandos_cronologia
    )
