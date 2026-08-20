from datetime import date, datetime
from decimal import Decimal

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDialog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.services.reajuste_anual import generar_cuotas_mensuales
from app.views.pago_por_rango import PagoPorRangoDialog
from database.models import (
    Abono,
    AreaDerecho,
    Base,
    Expediente,
    Obligacion,
    ParametroLegal,
    TipoObligacion,
    TipoReajusteAnual,
)


def _sesion_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )
    # Sprint 61: tasa_efectiva_anual=0.00 (usada en todo este archivo para que
    # el ejemplo sea deterministico) ahora activa el fallback a
    # CIVIL_ANNUAL_RATE en CivilFamiliaStrategy -- se siembra en 0.00 para
    # preservar exactamente el mismo comportamiento (cero interes) sin que
    # _calcular_preview capture un ParametroNoDisponibleError.
    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave="CIVIL_ANNUAL_RATE",
            valor=Decimal("0.00"),
            vigente_desde=date(1900, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    session.commit()
    session.close()


def _obligacion_civil_familia_recurrente_helper(
    valor: Decimal,
    fecha_inicio: date,
    tasa_efectiva_anual: Decimal,
    tipo_reajuste_anual: TipoReajusteAnual,
) -> Obligacion:
    """Persiste un expediente Civil/Familia con una obligacion RECURRENTE lista
    para generar_cuotas_mensuales -- mismo patron que
    tests/services/test_cascada_cuotas.py::_obligacion_civil_familia_recurrente_persistida,
    pero con un Expediente real (en vez de un expediente_id=1 sin fila) para
    calzar con el patron que ya usan tests/views/test_abonos.py y
    tests/views/test_expediente_detalle.py."""
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-100",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2024, 4, 1),
    )
    session.add(expediente)
    session.flush()
    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="CUOTA ALIMENTARIA",
        categoria="CHILD_SUPPORT",
        fecha_origen=fecha_inicio,
        fecha_inicio=fecha_inicio,
        dia_pago=fecha_inicio.day,
        valor=valor,
        tasa_efectiva_anual=tasa_efectiva_anual,
        tipo_reajuste_anual=tipo_reajuste_anual,
    )
    session.add(obligacion)
    session.commit()
    session.close()
    return obligacion


def test_pago_por_rango_dialog_crea_un_abono_por_cuota_tocada(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    obligacion_recurrente = _obligacion_civil_familia_recurrente_helper(
        valor=Decimal("150000.00"),
        fecha_inicio=date(2022, 4, 1),
        tasa_efectiva_anual=Decimal("0.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 4, 1))
    cuotas_a_pagar = sorted(
        [c for c in cuotas if date(2024, 2, 1) <= c.fecha_origen <= date(2024, 4, 1)],
        key=lambda c: c.fecha_origen,
        reverse=True,
    )

    dialogo = PagoPorRangoDialog(cuotas=cuotas_a_pagar, area="CIVIL_FAMILIA", parent=None)
    qtbot.addWidget(dialogo)
    dialogo.campo_monto.setText("450000")
    dialogo.campo_fecha.setDate(QDate(2024, 4, 1))
    dialogo._calcular_preview()

    assert dialogo.tabla_preview.rowCount() == 3
    dialogo.confirmar()

    session = session_module.get_session()
    total_abonos = (
        session.query(Abono)
        .filter(Abono.obligacion_id.in_([c.id for c in cuotas_a_pagar]))
        .count()
    )
    session.close()
    assert total_abonos == 3


def test_pago_por_rango_dialog_con_remanente_no_confirma_ni_crea_abonos(qtbot, monkeypatch):
    """Requisito de manejo de error del plan: si sobra dinero sin cubrir en
    ninguna cuota de la seleccion (monto excede la deuda total), confirmar()
    debe bloquear -- no cerrar el dialogo ni crear ningun Abono."""
    _sesion_en_memoria(monkeypatch)
    obligacion_recurrente = _obligacion_civil_familia_recurrente_helper(
        valor=Decimal("150000.00"),
        fecha_inicio=date(2022, 4, 1),
        tasa_efectiva_anual=Decimal("0.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 4, 1))
    cuotas_a_pagar = sorted(
        [c for c in cuotas if date(2024, 3, 1) <= c.fecha_origen <= date(2024, 4, 1)],
        key=lambda c: c.fecha_origen,
        reverse=True,
    )

    dialogo = PagoPorRangoDialog(cuotas=cuotas_a_pagar, area="CIVIL_FAMILIA", parent=None)
    qtbot.addWidget(dialogo)
    # Deuda total de las 2 cuotas es 300.000; se paga de mas a proposito.
    dialogo.campo_monto.setText("500000")
    dialogo.campo_fecha.setDate(QDate(2024, 4, 1))
    dialogo._calcular_preview()

    assert dialogo._remanente == Decimal("200000.00")

    # confirmar() muestra un QMessageBox.warning modal antes de bloquear --
    # se mockea para no depender de un click real (mismo patron que el resto
    # de tests/views/*.py, ej. tests/views/test_abonos.py).
    monkeypatch.setattr("app.views.pago_por_rango.QMessageBox.warning", lambda *a, **k: None)
    dialogo.confirmar()

    # confirmar() debe retornar temprano (bloquear) sin llamar self.accept() --
    # el dialogo nunca llego a exec(), asi que result() sigue en su valor por
    # defecto (Rejected) en vez de Accepted.
    assert dialogo.result() != QDialog.DialogCode.Accepted
    session = session_module.get_session()
    total_abonos = (
        session.query(Abono)
        .filter(Abono.obligacion_id.in_([c.id for c in cuotas_a_pagar]))
        .count()
    )
    session.close()
    assert total_abonos == 0


def test_pago_por_rango_dialog_sin_parametro_ipc_no_crashea(qtbot, monkeypatch):
    """Una cuota con aplica_indexacion_ipc=True necesita IPC_INDICE_ACUMULADO
    cargado en Parametros para proyectar su deuda (ver Task 4,
    deuda_pendiente_cuota). Si no esta cargado, _calcular_preview no debe
    propagar la excepcion (crashearia el slot conectado a textChanged) --
    debe mostrarla en etiqueta_remanente, mismo criterio de fallo abierto
    que dashboard.py::_refrescar_alertas_vencimiento."""
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-101",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2024, 4, 1),
    )
    session.add(expediente)
    session.flush()
    obligacion_recurrente = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="CUOTA ALIMENTARIA",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2024, 1, 1),
        fecha_inicio=date(2024, 1, 1),
        dia_pago=1,
        valor=Decimal("150000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
        aplica_indexacion_ipc=True,
    )
    session.add(obligacion_recurrente)
    session.commit()
    session.close()

    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 3, 1))

    dialogo = PagoPorRangoDialog(cuotas=cuotas, area="CIVIL_FAMILIA", parent=None)
    qtbot.addWidget(dialogo)
    dialogo.campo_monto.setText("150000")
    dialogo._calcular_preview()  # no debe lanzar

    assert dialogo.tabla_preview.rowCount() == 0
    assert "No se pudo calcular la cascada" in dialogo.etiqueta_remanente.text()
    assert dialogo._asignaciones == []


def test_pago_por_rango_dialog_monto_invalido_no_crashea(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    obligacion_recurrente = _obligacion_civil_familia_recurrente_helper(
        valor=Decimal("150000.00"),
        fecha_inicio=date(2024, 1, 1),
        tasa_efectiva_anual=Decimal("0.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 3, 1))

    dialogo = PagoPorRangoDialog(cuotas=cuotas, area="CIVIL_FAMILIA", parent=None)
    qtbot.addWidget(dialogo)
    dialogo.campo_monto.setText("no es un numero")
    dialogo._calcular_preview()

    assert dialogo.tabla_preview.rowCount() == 0
    assert dialogo.etiqueta_remanente.text() == "Ingrese un monto valido."
