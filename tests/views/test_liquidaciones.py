from dataclasses import replace
from datetime import date
from decimal import Decimal

from docx import Document
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database.session as session_module
from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.views.liquidaciones import ResultadoLiquidacionView
from database.models import AreaDerecho, Base, Expediente


def _resultado_de_prueba() -> LiquidationResult:
    debt = PendingDebt(
        principal=Decimal("427900.00"), interest=Decimal("1200.50"), indexation=Decimal("300.00")
    )
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="LIQUIDATION_CUTOFF")
    item = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Corte final de liquidacion",
        capital_base=Decimal("427900.00"),
        interest_rate=Decimal("6.00"),
        interest_amount=Decimal("1200.50"),
        indexation_amount=Decimal("300.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
    )
    return LiquidationResult(items=[item])


def _resultado_de_prueba_con_alertas(alertas: list[str]) -> LiquidationResult:
    resultado = _resultado_de_prueba()
    return LiquidationResult(items=resultado.items, alertas=alertas)


def test_muestra_una_fila_por_item_de_liquidacion(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 1).text() == "Corte final de liquidacion"


def _resultado_con_obligacion_prescrita() -> LiquidationResult:
    debt = PendingDebt(
        principal=Decimal("1000000.00"), interest=Decimal("0.00"), indexation=Decimal("0.00")
    )
    balance = RunningBalance(date=date(2015, 1, 1), debt=debt, event_type="INSTALLMENT")
    item = LiquidationItem(
        date=date(2015, 1, 1),
        concept="Capital antiguo",
        capital_base=Decimal("1000000.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
        prescrita=True,
    )
    return LiquidationResult(items=[item])


def _resultado_de_prueba_con_alertas(alertas: list[str]) -> LiquidationResult:
    resultado = _resultado_de_prueba()
    return LiquidationResult(items=resultado.items, alertas=alertas)


def test_marca_visualmente_las_filas_prescritas(qtbot):
    # Sprint 42: decision del despacho -- la obligacion prescrita se sigue
    # incluyendo en la tabla (el saldo no cambia), solo se marca con un
    # indicador visual (aqui: texto + color rojo) para que el abogado la note.
    from PySide6.QtGui import QColor

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_con_obligacion_prescrita(), expediente_id=1)

    celda_concepto = view.tabla.item(0, 1)
    assert "capital antiguo" in celda_concepto.text().lower()
    assert "prescrita" in celda_concepto.text().lower()
    assert celda_concepto.foreground().color() == QColor("red")


def test_no_marca_visualmente_las_filas_vigentes(qtbot):
    from PySide6.QtGui import QColor

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    celda_concepto = view.tabla.item(0, 1)
    assert celda_concepto.text() == "Corte final de liquidacion"
    assert celda_concepto.foreground().color() != QColor("red")


def test_muestra_columna_de_indexacion_sanciones(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert view.tabla.columnCount() == 8
    header_indexacion = view.tabla.horizontalHeaderItem(5).text()
    assert "ndexaci" in header_indexacion or "anci" in header_indexacion
    assert view.tabla.item(0, 5).text() == "300.00"


def test_muestra_los_totales(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert "1200.50" in view.etiqueta_interes_total.text()
    # NOTA (bug detectado durante implementación): el plan original esperaba "427900.00"
    # aquí, pero PendingDebt.total() = principal + interest + indexation, no solo el
    # principal. El saldo final correcto incluye el interés acumulado y la indexación,
    # por lo que se corrige la aserción para reflejar el comportamiento real y
    # matemáticamente correcto de final_balance().total(), en vez de forzar la vista a un
    # cálculo erróneo. Con indexation_amount = 300.00 (Task 6), el total pasa de
    # 429100.50 a 429400.50 (427900.00 + 1200.50 + 300.00).
    assert "429400.50" in view.etiqueta_saldo_final.text()


def _resultado_con_sobrepago() -> LiquidationResult:
    # Sprint 46: mismo escenario del bug real usado en
    # tests/liquidation/test_engine.py::test_engine_sobrepago_expone_remanente_como_saldo_a_favor
    debt = PendingDebt(
        principal=Decimal("0.00"), interest=Decimal("0.00"), indexation=Decimal("0.00")
    )
    balance = RunningBalance(date=date(2026, 1, 10), debt=debt, event_type="PAYMENT")
    item = LiquidationItem(
        date=date(2026, 1, 10),
        concept="Pago",
        capital_base=Decimal("7000000.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("7000000.00"),
        balance=balance,
        saldo_a_favor=Decimal("3000000.00"),
    )
    return LiquidationResult(items=[item])


def _resultado_de_prueba_con_alertas(alertas: list[str]) -> LiquidationResult:
    resultado = _resultado_de_prueba()
    return LiquidationResult(items=resultado.items, alertas=alertas)


def test_muestra_saldo_a_favor_cuando_hay_sobrepago(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.show()

    view.mostrar(_resultado_con_sobrepago(), expediente_id=1)

    assert view.etiqueta_saldo_a_favor.isVisible()
    assert "3000000.00" in view.etiqueta_saldo_a_favor.text()


def test_oculta_saldo_a_favor_cuando_no_hay_sobrepago(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.show()

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert not view.etiqueta_saldo_a_favor.isVisible()


def _resultado_con_alertas() -> LiquidationResult:
    resultado = _resultado_de_prueba()
    return LiquidationResult(
        items=resultado.items,
        alertas=[
            "Doble Actualización Prohibida: hay indemnización moratoria vigente.",
            "Techo de usura alcanzado en 'Impuesto de renta 2024'.",
        ],
    )


def test_muestra_alertas_no_bloqueantes_cuando_estan_presentes(qtbot):
    # Revision de calidad tras el Sprint 43: un toast (expediente_detalle.py) se
    # desvanece a los 6 segundos -- esta etiqueta deja las alertas legalmente
    # relevantes (LiquidationResult.alertas) visibles de forma durable mientras el
    # resultado siga en pantalla, mismo criterio que ya usa el marcado de una
    # obligacion prescrita (prefijo "⚠").
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.show()

    view.mostrar(_resultado_con_alertas(), expediente_id=1)

    assert view.etiqueta_alertas.isVisible()
    texto = view.etiqueta_alertas.text()
    assert "⚠" in texto
    assert "Doble Actualización Prohibida" in texto
    assert "Techo de usura alcanzado" in texto


def test_oculta_alertas_cuando_no_hay_ninguna(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.show()

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert not view.etiqueta_alertas.isVisible()
    assert view.etiqueta_alertas.text() == ""


def test_mostrar_de_nuevo_sin_alertas_oculta_las_del_resultado_anterior(qtbot):
    # Regresion: mostrar() se reutiliza para cada liquidacion nueva en la misma
    # instancia de la vista -- si el resultado anterior tenia alertas y el nuevo no,
    # la etiqueta debe ocultarse (no quedarse pegada con el texto viejo).
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.show()

    view.mostrar(_resultado_con_alertas(), expediente_id=1)
    assert view.etiqueta_alertas.isVisible()

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert not view.etiqueta_alertas.isVisible()
    assert view.etiqueta_alertas.text() == ""


def test_muestra_bloque_de_renta_liquida_cuando_esta_presente(qtbot):
    from app.engine.tax.renta_liquida import RentaLiquidaGravableResult

    renta = RentaLiquidaGravableResult(
        ingresos_netos=Decimal("100000000.00"),
        renta_bruta=Decimal("60000000.00"),
        renta_liquida=Decimal("40000000.00"),
        hubo_perdida_liquida=False,
        renta_liquida_gravable=Decimal("35000000.00"),
    )
    resultado = LiquidationResult(items=[], renta_liquida=renta)

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.show()
    view.mostrar(resultado, expediente_id=1)

    assert view.grupo_renta_liquida.isVisible()
    assert "35000000.00" in view.etiqueta_renta_liquida_gravable.text()


def test_oculta_bloque_de_renta_liquida_cuando_no_esta_presente(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.show()
    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert not view.grupo_renta_liquida.isVisible()


def _expediente_para_exportar(monkeypatch) -> int:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

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

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id)

    with qtbot.waitSignal(view.exportacion_finalizada, timeout=5000):
        view._exportar_pdf()

    assert ruta_destino.exists()
    assert ruta_destino.stat().st_size > 0


def test_exportar_pdf_muestra_toast_no_bloqueante_en_vez_de_dialogo_modal(
    qtbot, monkeypatch, tmp_path
):
    expediente_id = _expediente_para_exportar(monkeypatch)
    ruta_destino = tmp_path / "salida.pdf"
    monkeypatch.setattr(
        "app.views.liquidaciones.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(ruta_destino), "PDF (*.pdf)"),
    )
    llamadas_toast = []
    monkeypatch.setattr(
        "app.views.liquidaciones.mostrar_toast",
        lambda parent, mensaje, **kwargs: llamadas_toast.append((parent, mensaje)),
    )

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id)

    with qtbot.waitSignal(view.exportacion_finalizada, timeout=5000):
        view._exportar_pdf()

    assert len(llamadas_toast) == 1
    parent, mensaje = llamadas_toast[0]
    assert parent is view
    assert str(ruta_destino) in mensaje


def test_exportar_word_crea_archivo_en_la_ruta_elegida(qtbot, monkeypatch, tmp_path):
    expediente_id = _expediente_para_exportar(monkeypatch)
    ruta_destino = tmp_path / "salida.docx"
    monkeypatch.setattr(
        "app.views.liquidaciones.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(ruta_destino), "Word (*.docx)"),
    )

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id)

    with qtbot.waitSignal(view.exportacion_finalizada, timeout=5000):
        view._exportar_word()

    assert ruta_destino.exists()
    assert ruta_destino.stat().st_size > 0


def test_exportar_pdf_incluye_las_alertas_de_la_liquidacion(qtbot, monkeypatch, tmp_path):
    # Sprint 77: LiquidationResult.alertas (Sprint 43) ya se mostraba en pantalla
    # (ver test_muestra_alertas_no_bloqueantes_cuando_estan_presentes arriba)
    # pero no llegaba al PDF exportado -- un abogado que exportara sin volver a
    # abrir la app nunca veia la advertencia.
    from reportlab.platypus import Paragraph

    parrafo_real = Paragraph
    parrafos_capturados = []

    def _parrafo_capturado(texto, *args, **kwargs):
        parrafos_capturados.append(texto)
        return parrafo_real(texto, *args, **kwargs)

    monkeypatch.setattr("app.reports.pdf.Paragraph", _parrafo_capturado)

    expediente_id = _expediente_para_exportar(monkeypatch)
    ruta_destino = tmp_path / "salida_alertas.pdf"
    monkeypatch.setattr(
        "app.views.liquidaciones.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(ruta_destino), "PDF (*.pdf)"),
    )

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(
        _resultado_de_prueba_con_alertas(["Techo de usura alcanzado"]), expediente_id
    )

    with qtbot.waitSignal(view.exportacion_finalizada, timeout=5000):
        view._exportar_pdf()

    assert ruta_destino.exists()
    assert any("Techo de usura alcanzado" in texto for texto in parrafos_capturados)


def test_exportar_word_incluye_las_alertas_de_la_liquidacion(qtbot, monkeypatch, tmp_path):
    expediente_id = _expediente_para_exportar(monkeypatch)
    ruta_destino = tmp_path / "salida_alertas.docx"
    monkeypatch.setattr(
        "app.views.liquidaciones.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(ruta_destino), "Word (*.docx)"),
    )

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(
        _resultado_de_prueba_con_alertas(["Techo de usura alcanzado"]), expediente_id
    )

    with qtbot.waitSignal(view.exportacion_finalizada, timeout=5000):
        view._exportar_word()

    documento = Document(str(ruta_destino))
    texto_completo = "\n".join(p.text for p in documento.paragraphs)
    assert "Techo de usura alcanzado" in texto_completo


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

    with qtbot.waitSignal(view.exportacion_finalizada, timeout=5000):
        view._exportar_pdf()

    assert len(errores) == 1
    assert errores[0][0] == "No se pudo exportar"


def test_sanitizar_nombre_archivo_reemplaza_caracteres_invalidos():
    from app.views.liquidaciones import _sanitizar_nombre_archivo

    assert _sanitizar_nombre_archivo("2026/030 A") == "2026_030_A"


def test_exportar_pdf_deshabilita_ambos_botones_mientras_esta_en_curso(
    qtbot, monkeypatch, tmp_path
):
    expediente_id = _expediente_para_exportar(monkeypatch)
    ruta_destino = tmp_path / "salida.pdf"
    monkeypatch.setattr(
        "app.views.liquidaciones.QFileDialog.getSaveFileName",
        lambda *args, **kwargs: (str(ruta_destino), "PDF (*.pdf)"),
    )

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id)

    assert view.boton_exportar_pdf.isEnabled() is True
    assert view.boton_exportar_word.isEnabled() is True

    with qtbot.waitSignal(view.exportacion_finalizada, timeout=5000):
        view._exportar_pdf()
        assert view.boton_exportar_pdf.isEnabled() is False
        assert view.boton_exportar_word.isEnabled() is False

    assert view.boton_exportar_pdf.isEnabled() is True
    assert view.boton_exportar_word.isEnabled() is True


def test_exportar_pdf_ignora_llamada_concurrente_mientras_hay_una_en_curso(
    qtbot, monkeypatch, tmp_path
):
    expediente_id = _expediente_para_exportar(monkeypatch)
    ruta_destino = tmp_path / "salida.pdf"
    llamadas_dialogo = []

    def _dialogo_falso(*args, **kwargs):
        llamadas_dialogo.append(1)
        return str(ruta_destino), "PDF (*.pdf)"

    monkeypatch.setattr("app.views.liquidaciones.QFileDialog.getSaveFileName", _dialogo_falso)

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id)

    with qtbot.waitSignal(view.exportacion_finalizada, timeout=5000):
        view._exportar_pdf()
        view._exportar_pdf()  # concurrente -- debe ser ignorada, el boton ya esta deshabilitado

    assert len(llamadas_dialogo) == 1


def test_botones_exportar_tienen_icono_y_clase_primaria(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    assert not view.boton_exportar_pdf.icon().isNull()
    assert view.boton_exportar_pdf.property("class") == "primary"
    assert not view.boton_exportar_word.icon().isNull()
    assert view.boton_exportar_word.property("class") == "primary"


def _resultado_con_costas() -> LiquidationResult:
    # Sprint 79: costas como componente propio (no generan interes).
    resultado = _resultado_de_prueba()
    item = resultado.items[0]
    debt = PendingDebt(
        principal=Decimal("427900.00"),
        interest=Decimal("1200.50"),
        indexation=Decimal("300.00"),
        costas=Decimal("5000.00"),
    )
    balance = RunningBalance(date=item.date, debt=debt, event_type="LIQUIDATION_CUTOFF")
    return LiquidationResult(items=[replace(item, balance=balance)])


def test_muestra_costas_como_rubro_propio_cuando_existen(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.show()

    view.mostrar(_resultado_con_costas(), expediente_id=1)

    assert view.etiqueta_costas.isVisible()
    assert "5000.00" in view.etiqueta_costas.text()
    # 427900.00 + 1200.50 + 300.00 + 5000.00 (costas en seco) = 434400.50
    assert "434400.50" in view.etiqueta_saldo_final.text()


def test_oculta_costas_cuando_no_hay(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.show()

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert not view.etiqueta_costas.isVisible()


# --- Sprint 107: interruptor "Ver con/sin indexación" (vista de sensibilidad) ---


def _expediente_sprint107(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA, **extra):
    from datetime import datetime

    from app.engine.indexation.historical_index import _IPC_INDICE_ACUMULADO
    from database.models import Obligacion, ParametroLegal, TipoObligacion

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )
    session = session_module.get_session()
    for anio, valor in _IPC_INDICE_ACUMULADO.items():
        session.add(
            ParametroLegal(
                clave="IPC_INDICE_ACUMULADO",
                valor=valor,
                vigente_desde=date(anio, 1, 1),
                vigente_hasta=None,
                usuario="test",
                motivo=None,
                creado_en=datetime.now(),
            )
        )
    expediente = Expediente(
        radicado="2026-107",
        demandante="Ana",
        demandado="Luis",
        area_derecho=area,
        juzgado="Juzgado 1",
        fecha_corte_default=date(2025, 12, 31),
    )
    session.add(expediente)
    session.flush()
    campos = {"aplica_indexacion_ipc": True, "interes_sobre_capital_indexado": True}
    campos.update(extra)
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Dano emergente",
            categoria="DANO_EMERGENTE",
            fecha_origen=date(2024, 7, 1),
            valor=Decimal("1000000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
            **campos,
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def _banderas_y_auditoria(expediente_id: int):
    from database.models import AuditLog, Obligacion

    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    banderas = (obligacion.aplica_indexacion_ipc, obligacion.interes_sobre_capital_indexado)
    cantidad_logs = session.query(AuditLog).count()
    session.close()
    return banderas, cantidad_logs


def _elegir_sentido(view, con_indexacion: bool) -> None:
    selector = view.selector_indexacion_sensibilidad
    selector.setCurrentIndex(selector.findData(con_indexacion))


def test_interruptor_sensibilidad_deshabilitado_sin_fecha_de_corte(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert not view.check_vista_sensibilidad.isEnabled()
    assert view.etiqueta_vista_sensibilidad.isHidden()


def test_interruptor_sensibilidad_recalcula_sin_indexacion_y_vuelve_a_la_oficial(
    qtbot, monkeypatch
):
    from app.services.vista_sensibilidad_indexacion import liquidar_vista_sensibilidad

    expediente_id = _expediente_sprint107(monkeypatch)
    fecha_corte = date(2025, 12, 31)
    # Resultado oficial = lo guardado (la obligacion ya tiene indexacion marcada).
    oficial = liquidar_vista_sensibilidad(expediente_id, fecha_corte, con_indexacion=True)

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(oficial, expediente_id, fecha_corte=fecha_corte)

    # 1.000.000 + interes Suma Unica 95.658,88 + indexacion 61.933,78.
    assert view.etiqueta_saldo_final.text() == "Saldo final: 1157592.66"
    assert view.check_vista_sensibilidad.isEnabled()

    _elegir_sentido(view, False)
    with qtbot.waitSignal(view.vista_sensibilidad_actualizada, timeout=5000):
        view.check_vista_sensibilidad.setChecked(True)

    # Sin indexacion: 1.000.000 + 164,38 x 548 dias = 1.090.080,24.
    assert view.etiqueta_saldo_final.text() == "Saldo final: 1090080.24"
    assert not view.etiqueta_vista_sensibilidad.isHidden()
    assert "SIN indexación" in view.etiqueta_vista_sensibilidad.text()
    assert not view.boton_exportar_pdf.isEnabled()
    assert not view.boton_exportar_word.isEnabled()
    # La obligacion guardada y el AuditLog quedan intactos.
    assert _banderas_y_auditoria(expediente_id) == ((True, True), 0)

    view.check_vista_sensibilidad.setChecked(False)

    assert view.etiqueta_saldo_final.text() == "Saldo final: 1157592.66"
    assert view.etiqueta_vista_sensibilidad.isHidden()
    assert view.boton_exportar_pdf.isEnabled()
    assert view.boton_exportar_word.isEnabled()
    assert _banderas_y_auditoria(expediente_id) == ((True, True), 0)


def test_interruptor_sensibilidad_con_indexacion_sobre_obligacion_sin_indexar(
    qtbot, monkeypatch
):
    from app.services.vista_sensibilidad_indexacion import liquidar_vista_sensibilidad

    expediente_id = _expediente_sprint107(
        monkeypatch, aplica_indexacion_ipc=False, interes_sobre_capital_indexado=False
    )
    fecha_corte = date(2025, 12, 31)
    oficial = liquidar_vista_sensibilidad(expediente_id, fecha_corte, con_indexacion=False)

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(oficial, expediente_id, fecha_corte=fecha_corte)
    assert view.etiqueta_saldo_final.text() == "Saldo final: 1090080.24"

    _elegir_sentido(view, True)
    with qtbot.waitSignal(view.vista_sensibilidad_actualizada, timeout=5000):
        view.check_vista_sensibilidad.setChecked(True)

    # Con IPC y sin Suma Unica guardada: el interes civil queda sobre el capital
    # historico (90.080,24) y se suma la indexacion (61.933,78).
    assert view.etiqueta_saldo_final.text() == "Saldo final: 1152014.02"
    assert "CON indexación" in view.etiqueta_vista_sensibilidad.text()
    assert _banderas_y_auditoria(expediente_id) == ((False, False), 0)


def test_cambiar_el_selector_con_la_vista_activa_recalcula(qtbot, monkeypatch):
    from app.services.vista_sensibilidad_indexacion import liquidar_vista_sensibilidad

    expediente_id = _expediente_sprint107(monkeypatch)
    fecha_corte = date(2025, 12, 31)
    oficial = liquidar_vista_sensibilidad(expediente_id, fecha_corte, con_indexacion=True)

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(oficial, expediente_id, fecha_corte=fecha_corte)
    _elegir_sentido(view, False)
    with qtbot.waitSignal(view.vista_sensibilidad_actualizada, timeout=5000):
        view.check_vista_sensibilidad.setChecked(True)
    assert view.etiqueta_saldo_final.text() == "Saldo final: 1090080.24"

    with qtbot.waitSignal(view.vista_sensibilidad_actualizada, timeout=5000):
        _elegir_sentido(view, True)

    assert view.etiqueta_saldo_final.text() == "Saldo final: 1157592.66"
    assert not view.etiqueta_vista_sensibilidad.isHidden()


def test_mostrar_un_resultado_nuevo_apaga_la_vista_de_sensibilidad(qtbot, monkeypatch):
    from app.services.vista_sensibilidad_indexacion import liquidar_vista_sensibilidad

    expediente_id = _expediente_sprint107(monkeypatch)
    fecha_corte = date(2025, 12, 31)
    oficial = liquidar_vista_sensibilidad(expediente_id, fecha_corte, con_indexacion=True)

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(oficial, expediente_id, fecha_corte=fecha_corte)
    _elegir_sentido(view, False)
    with qtbot.waitSignal(view.vista_sensibilidad_actualizada, timeout=5000):
        view.check_vista_sensibilidad.setChecked(True)

    view.mostrar(oficial, expediente_id, fecha_corte=fecha_corte)

    assert not view.check_vista_sensibilidad.isChecked()
    assert view.etiqueta_vista_sensibilidad.isHidden()
    assert view.boton_exportar_pdf.isEnabled()
    assert view.etiqueta_saldo_final.text() == "Saldo final: 1157592.66"


def test_error_en_la_vista_de_sensibilidad_avisa_y_vuelve_a_la_oficial(qtbot, monkeypatch):
    # Comercial con IPC exige pacto expreso en el titulo (Sprint 43): forzar "Con
    # indexación" sobre una obligacion sin ese pacto no se puede calcular -- se
    # informa el error de la estrategia tal cual y se vuelve a la vista oficial.
    expediente_id = _expediente_sprint107(
        monkeypatch,
        area=AreaDerecho.COMERCIAL,
        aplica_indexacion_ipc=False,
        interes_sobre_capital_indexado=False,
        tasa_moratoria_anual=Decimal("9.00"),
        fecha_vencimiento=date(2024, 8, 1),
        ibc_vigente_anual=Decimal("20.00"),
        pacto_expreso_indexacion=False,
    )
    advertencias = []
    monkeypatch.setattr(
        "app.views.liquidaciones.QMessageBox.warning",
        lambda parent, titulo, mensaje: advertencias.append(mensaje),
    )

    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.mostrar(_resultado_de_prueba(), expediente_id, fecha_corte=date(2025, 12, 31))
    texto_oficial = view.etiqueta_saldo_final.text()
    _elegir_sentido(view, True)

    with qtbot.waitSignal(view.vista_sensibilidad_actualizada, timeout=5000):
        view.check_vista_sensibilidad.setChecked(True)

    assert len(advertencias) == 1
    assert "Pacto expreso" in advertencias[0]
    assert not view.check_vista_sensibilidad.isChecked()
    assert view.etiqueta_vista_sensibilidad.isHidden()
    assert view.etiqueta_saldo_final.text() == texto_oficial
    assert view.boton_exportar_pdf.isEnabled()
    assert _banderas_y_auditoria(expediente_id) == ((False, False), 0)


# --- Sprint 100: fruto civil como rubro propio ---


def _resultado_con_fruto_civil() -> LiquidationResult:
    # Dos meses de fruto civil (905.765,41 + 910.139,17 = 1.815.904,58), sin
    # interes, seguidos del corte.
    filas = []
    principal = Decimal("0.00")
    for fecha, neto in (
        (date(2019, 2, 28), Decimal("905765.41")),
        (date(2019, 3, 31), Decimal("910139.17")),
    ):
        principal += neto
        debt = PendingDebt(principal=principal, interest=Decimal("0.00"), indexation=Decimal("0"))
        filas.append(
            LiquidationItem(
                date=fecha,
                concept=f"Fruto civil {fecha.month:02d}/2019",
                capital_base=principal,
                interest_rate=Decimal("0.00"),
                interest_amount=Decimal("0.00"),
                indexation_amount=Decimal("0.00"),
                payment_amount=Decimal("0.00"),
                balance=RunningBalance(date=fecha, debt=debt, event_type="FRUTO_CIVIL"),
            )
        )
    return LiquidationResult(items=filas)


def test_muestra_fruto_civil_como_rubro_propio_cuando_existe(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.show()

    view.mostrar(_resultado_con_fruto_civil(), expediente_id=1)

    assert view.etiqueta_fruto_civil.isVisible()
    assert "1815904.58" in view.etiqueta_fruto_civil.text()
    assert "sin intereses" in view.etiqueta_fruto_civil.text()


def test_oculta_fruto_civil_cuando_no_hay(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)
    view.show()

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert not view.etiqueta_fruto_civil.isVisible()
