from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Paragraph, Table, TableStyle

from app.reports.header import build_encabezado
from app.reports.pdf import FONT_HEADER, JudicialPDFGenerator


def _capturar_parrafos(monkeypatch):
    parrafo_real = Paragraph
    llamadas = []

    def _parrafo_capturado(texto, *args, **kwargs):
        llamadas.append(texto)
        return parrafo_real(texto, *args, **kwargs)

    monkeypatch.setattr("app.reports.pdf.Paragraph", _parrafo_capturado)
    return llamadas


def _capturar_tablas(monkeypatch):
    # Mismo patron que las pruebas de "prescrita": interceptamos la construccion
    # de las tablas de reportlab para inspeccionar los datos crudos que
    # generate() les pasa, sin depender de un lector de PDF externo.
    tabla_real = Table
    llamadas = []

    def _tabla_capturada(datos, *args, **kwargs):
        llamadas.append(datos)
        return tabla_real(datos, *args, **kwargs)

    monkeypatch.setattr("app.reports.pdf.Table", _tabla_capturada)
    return llamadas


def _capturar_estilos(monkeypatch):
    # Mismo patron que test_generate_resalta_en_rojo_las_filas_prescritas:
    # interceptar TableStyle para inspeccionar los comandos crudos que
    # generate()/generar_documento() les pasa a cada tabla, en orden.
    estilo_real = TableStyle
    llamadas = []

    def _estilo_capturado(comandos):
        llamadas.append(comandos)
        return estilo_real(comandos)

    monkeypatch.setattr("app.reports.pdf.TableStyle", _estilo_capturado)
    return llamadas


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


def test_generate_muestra_saldo_a_favor_en_el_resumen_cuando_esta_presente(tmp_path, monkeypatch):
    # Sprint 46: cuando ReportSummaryBuilder.build_summary agrega la clave
    # "saldo_a_favor" (solo si hay sobrepago), el PDF debe mostrar una linea
    # "Saldo a favor del deudor" en la tabla de resumen ejecutivo.
    llamadas = _capturar_tablas(monkeypatch)
    ruta = tmp_path / "liquidacion_saldo_a_favor.pdf"
    generador = JudicialPDFGenerator(str(ruta))
    summary = _summary()
    summary["saldo_a_favor"] = "$3,000,000.00"

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", summary, _table_data()
    )

    assert ruta.exists()
    # llamadas[0] es la tabla de resumen ejecutivo.
    datos_resumen = llamadas[0]
    assert any(
        fila[0] == "Saldo a favor del deudor" and fila[1] == "$3,000,000.00"
        for fila in datos_resumen
    )


def test_generate_no_muestra_saldo_a_favor_sin_sobrepago(tmp_path, monkeypatch):
    llamadas = _capturar_tablas(monkeypatch)
    ruta = tmp_path / "liquidacion_sin_saldo_a_favor.pdf"
    generador = JudicialPDFGenerator(str(ruta))

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), _table_data()
    )

    datos_resumen = llamadas[0]
    assert not any(fila[0] == "Saldo a favor del deudor" for fila in datos_resumen)


def test_generate_muestra_columna_de_saldo_a_favor_en_la_cronologia_cuando_hay_sobrepago(
    tmp_path, monkeypatch
):
    # ReportTableBuilder.build_matrix (Sprint 46) agrega "saldo_a_favor" a cada
    # fila -- el PDF agrega la columna solo cuando el resumen indica que hubo
    # sobrepago, para no romper el layout de las liquidaciones normales.
    llamadas = _capturar_tablas(monkeypatch)
    ruta = tmp_path / "liquidacion_cronologia_saldo_a_favor.pdf"
    generador = JudicialPDFGenerator(str(ruta))
    summary = _summary()
    summary["saldo_a_favor"] = "$3,000,000.00"
    datos = _table_data()
    datos[0]["saldo_a_favor"] = "$3,000,000.00"

    generador.generate("LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", summary, datos)

    # llamadas[1] es la tabla de cronologia detallada.
    datos_cronologia = llamadas[1]
    assert "Saldo a favor" in datos_cronologia[0]
    indice_columna = datos_cronologia[0].index("Saldo a favor")
    assert datos_cronologia[1][indice_columna] == "$3,000,000.00"


def test_generate_no_agrega_columna_de_saldo_a_favor_sin_sobrepago(tmp_path, monkeypatch):
    llamadas = _capturar_tablas(monkeypatch)
    ruta = tmp_path / "liquidacion_cronologia_sin_saldo_a_favor.pdf"
    generador = JudicialPDFGenerator(str(ruta))

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), _table_data()
    )

    datos_cronologia = llamadas[1]
    assert "Saldo a favor" not in datos_cronologia[0]
    assert len(datos_cronologia[0]) == 10


def _diferencia_recalculo():
    return {
        "audit_log_anterior": "AuditLog #12",
        "monto_anterior": "$7,830,000.00",
        "monto_recalculado": "$7,860,000.00",
        "diferencia_monto": "+$30,000.00 pesos",
        "dias_cubiertos_anterior": "1",
        "dias_cubiertos_recalculado": "1",
        "resumen": "Diferencia recuperada: +$30,000.00 pesos",
    }


def test_generate_incluye_bloque_de_diferencia_recalculo_cuando_se_provee(tmp_path, monkeypatch):
    # Sprint 47: log de diferencias del recalculo historico post-Sprint-30,
    # mismo patron aditivo que renta_liquida (Sprint 15) -- una tabla nueva
    # que solo aparece cuando se provee el dato.
    llamadas = _capturar_tablas(monkeypatch)
    ruta = tmp_path / "memorial_diferencia.pdf"
    generador = JudicialPDFGenerator(str(ruta))

    generador.generate(
        "MEMORIAL DE ACTUALIZACIÓN/CORRECCIÓN DE LIQUIDACIÓN",
        _summary(),
        _table_data(),
        diferencia_recalculo=_diferencia_recalculo(),
    )

    assert ruta.exists()
    # llamadas[0] resumen ejecutivo, [1] cronologia, [2] diferencia de recalculo.
    datos_diferencia = llamadas[2]
    assert ["Valor Anterior (Sprint 30, pre-corrección)", "$7,830,000.00"] in datos_diferencia
    assert ["Valor Recalculado", "$7,860,000.00"] in datos_diferencia
    assert ["Diferencia Recuperada", "+$30,000.00 pesos"] in datos_diferencia


def test_generate_sin_diferencia_recalculo_no_agrega_el_bloque(tmp_path, monkeypatch):
    llamadas = _capturar_tablas(monkeypatch)
    ruta = tmp_path / "liquidacion_sin_diferencia.pdf"
    generador = JudicialPDFGenerator(str(ruta))

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), _table_data()
    )

    # Solo 2 tablas: resumen ejecutivo y cronologia.
    assert len(llamadas) == 2


def test_generate_incluye_bloque_de_alertas_cuando_se_provee(tmp_path, monkeypatch):
    # Sprint 77: LiquidationResult.alertas (Sprint 43) no llegaba al PDF/Word --
    # un abogado que exportara sin volver a abrir la app nunca veia advertencias
    # como "Doble Actualización Prohibida" o "Techo de usura alcanzado".
    parrafos = _capturar_parrafos(monkeypatch)
    ruta = tmp_path / "liquidacion_alertas.pdf"
    generador = JudicialPDFGenerator(str(ruta))

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA LABORAL",
        _summary(),
        _table_data(),
        alertas=["Doble Actualización Prohibida", "Techo de usura alcanzado"],
    )

    assert ruta.exists()
    assert any("Doble Actualización Prohibida" in texto for texto in parrafos)
    assert any("Techo de usura alcanzado" in texto for texto in parrafos)


def test_generate_sin_alertas_no_agrega_el_bloque(tmp_path, monkeypatch):
    parrafos = _capturar_parrafos(monkeypatch)
    ruta = tmp_path / "liquidacion_sin_alertas.pdf"
    generador = JudicialPDFGenerator(str(ruta))

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), _table_data()
    )

    assert ruta.exists()
    assert not any("Advertencias" in texto for texto in parrafos)


def test_generate_con_alertas_vacia_no_agrega_el_bloque(tmp_path, monkeypatch):
    parrafos = _capturar_parrafos(monkeypatch)
    ruta = tmp_path / "liquidacion_alertas_vacias.pdf"
    generador = JudicialPDFGenerator(str(ruta))

    generador.generate(
        "LIQUIDACIÓN DE OBLIGACIONES — ÁREA CIVIL / FAMILIA", _summary(), _table_data(), alertas=[]
    )

    assert ruta.exists()
    assert not any("Advertencias" in texto for texto in parrafos)


def test_fuente_extrabold_de_encabezado_esta_registrada():
    # Sprint 108: la fuente de marca (Sprint 31) debe registrarse como fuente
    # de reportlab al importar el modulo, o el encabezado sigue cayendo en
    # Helvetica pese a que TableStyle pida FONT_HEADER.
    assert FONT_HEADER in pdfmetrics.getRegisteredFontNames()


def test_generate_usa_bordes_negros_y_encabezado_extrabold_en_todas_las_tablas(
    tmp_path, monkeypatch
):
    # Sprint 108 (pedido del despacho, 2026-08-22): el grid de las tablas debe
    # ser negro (antes borgoña) y el encabezado de columnas debe usar la
    # fuente extrabold de marca (antes Helvetica por defecto).
    llamadas_estilo = _capturar_estilos(monkeypatch)
    ruta = tmp_path / "liquidacion_colores.pdf"
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
        diferencia_recalculo=_diferencia_recalculo(),
    )

    # resumen ejecutivo, cronologia, renta liquida, diferencia de recalculo.
    assert len(llamadas_estilo) == 4
    for comandos in llamadas_estilo:
        comandos_grid = [c for c in comandos if c[0] == "GRID"]
        assert comandos_grid, "cada tabla debe tener un comando GRID"
        for comando in comandos_grid:
            assert comando[-1] == generador.c_black
            assert comando[-1] != generador.c_burgundy

        comandos_fuente_encabezado = [
            c for c in comandos if c[0] == "FONTNAME" and c[1] == (0, 0) and c[2] == (-1, 0)
        ]
        assert comandos_fuente_encabezado, "cada tabla debe fijar la fuente del encabezado"
        assert comandos_fuente_encabezado[0][3] == FONT_HEADER


def test_generate_pinta_de_borgona_la_fila_de_totales(tmp_path, monkeypatch):
    # Sprint 108: la fila de totales/gran total debe quedar en borgoña de
    # marca -- antes heredaba el negro del resto del cuerpo, sin ningun
    # TEXTCOLOR propio.
    llamadas_estilo = _capturar_estilos(monkeypatch)
    ruta = tmp_path / "liquidacion_totales_borgona.pdf"
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
        diferencia_recalculo=_diferencia_recalculo(),
    )

    # llamadas_estilo[0] resumen ejecutivo, [2] renta liquida, [3] diferencia
    # de recalculo -- las 3 tablas con fila de totales/gran-total en negrita.
    # [1] es la cronologia detallada, que no tiene fila de totales.
    for indice in (0, 2, 3):
        comandos = llamadas_estilo[indice]
        assert any(
            comando[0] == "TEXTCOLOR"
            and comando[1] == (0, -1)
            and comando[2] == (-1, -1)
            and comando[3] == generador.c_burgundy
            for comando in comandos
        )


def test_generar_documento_usa_bordes_negros_y_totales_en_borgona(tmp_path, monkeypatch):
    # generar_documento() es el metodo legado (LIQUIDACIÓN PROVISIONAL DE
    # ALIMENTOS) -- tiene su propia tabla con fila "TOTALES", separada de
    # generate().
    llamadas_estilo = _capturar_estilos(monkeypatch)
    ruta = tmp_path / "provisional_alimentos.pdf"
    generador = JudicialPDFGenerator(str(ruta))

    generador.generar_documento(
        [
            {
                "concepto": "Cuota alimentaria",
                "capital": 100,
                "dias_mora": 10,
                "intereses": 5,
                "total_rubro": 105,
            }
        ],
        ruta_grafica="",
    )

    assert len(llamadas_estilo) == 1
    comandos = llamadas_estilo[0]
    comandos_grid = [c for c in comandos if c[0] == "GRID"]
    assert comandos_grid
    assert all(comando[-1] == generador.c_black for comando in comandos_grid)
    assert any(
        comando[0] == "TEXTCOLOR"
        and comando[1] == (0, -1)
        and comando[2] == (-1, -1)
        and comando[3] == generador.c_burgundy
        for comando in comandos
    )
    comandos_fuente_encabezado = [
        c for c in comandos if c[0] == "FONTNAME" and c[1] == (0, 0) and c[2] == (-1, 0)
    ]
    assert comandos_fuente_encabezado[0][3] == FONT_HEADER


def test_generate_incluye_cuerpo_legal_cuando_se_provee(tmp_path):
    # Sprint 47: parrafo de fundamento legal para los memoriales de
    # recalculo (Art. 53 C.P. / Art. 151 CPACA), mismo patron aditivo.
    ruta = tmp_path / "memorial_cuerpo_legal.pdf"
    generador = JudicialPDFGenerator(str(ruta))

    generador.generate(
        "MEMORIAL DE CORRECCIÓN DE ERROR ARITMÉTICO (ART. 151 CPACA)",
        _summary(),
        _table_data(),
        cuerpo_legal="Solicito la corrección del error aritmético, Art. 151 CPACA.",
    )

    assert ruta.exists()
    assert ruta.stat().st_size > 0
