from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database.session as session_module
from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.views.liquidaciones import ResultadoLiquidacionView
from database.models import AreaDerecho, Base, Expediente


def _resultado_de_prueba() -> LiquidationResult:
    debt = PendingDebt(principal=Decimal("427900.00"), interest=Decimal("1200.50"), indexation=Decimal("300.00"))
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


def test_muestra_una_fila_por_item_de_liquidacion(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 1).text() == "Corte final de liquidacion"


def _resultado_con_obligacion_prescrita() -> LiquidationResult:
    debt = PendingDebt(principal=Decimal("1000000.00"), interest=Decimal("0.00"), indexation=Decimal("0.00"))
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
    debt = PendingDebt(principal=Decimal("0.00"), interest=Decimal("0.00"), indexation=Decimal("0.00"))
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


def test_muestra_bloque_de_renta_liquida_cuando_esta_presente(qtbot):
    from app.engine.tax.renta_liquida import RentaLiquidaGravableResult

    renta = RentaLiquidaGravableResult(
        ingresos_netos=Decimal("100000000.00"), renta_bruta=Decimal("60000000.00"),
        renta_liquida=Decimal("40000000.00"), hubo_perdida_liquida=False,
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
