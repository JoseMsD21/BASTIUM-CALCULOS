from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.views.liquidaciones import ResultadoLiquidacionView
from database.models import AreaDerecho, Base, Expediente


def _resultado_de_prueba() -> LiquidationResult:
    debt = PendingDebt(principal=Decimal("427900.00"), interest=Decimal("1200.50"), indexation=Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="LIQUIDATION_CUTOFF")
    item = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Corte final de liquidacion",
        capital_base=Decimal("427900.00"),
        interest_rate=Decimal("6.00"),
        interest_amount=Decimal("1200.50"),
        indexation_amount=Decimal("0.00"),
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


def test_muestra_los_totales(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba(), expediente_id=1)

    assert "1200.50" in view.etiqueta_interes_total.text()
    # NOTA (bug detectado durante implementación): el plan original esperaba "427900.00"
    # aquí, pero PendingDebt.total() = principal + interest + indexation = 429100.50, no
    # solo el principal. El saldo final correcto incluye el interés acumulado, por lo que
    # se corrige la aserción para reflejar el comportamiento real y matemáticamente
    # correcto de final_balance().total(), en vez de forzar la vista a un cálculo erróneo.
    assert "429100.50" in view.etiqueta_saldo_final.text()


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
