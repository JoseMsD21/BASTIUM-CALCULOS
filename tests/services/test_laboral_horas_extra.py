"""Sprint 95 (conexion a la UI): horas extra (HED/HEN/HEFD/HEFN) registradas
en una liquidacion Laboral -- `LaboralStrategy` las suma como rubro propio
(evento HORAS_EXTRA) con el factor del motor `app/engine/labor/horas_extra.py`
vigente en la fecha de causacion, sin cambiar los demas rubros laborales.

Valores esperados calculados a mano:
- Contrato base 01/01/2020-31/12/2020, salario 3.000.000: prestaciones =
  7.860.000,00 (ver TestLaboralStrategy en test_area_strategy.py).
- HED 10 h x 10.000 x 1,25 = 125.000,00.
- HEN 4 h x 10.000 x 1,75 = 70.000,00.
- HEFD Tramo 1 (2025-08-10): 3 h x 8.000 x 2,05 = 49.200,00.
- HEFN Tramo 2 (2026-07-05): 2 h x 8.000 x 2,65 = 42.400,00.
- HEFD 2020 (sin factor confirmado) con 100 % digitado: 2 h x 10.000 x 2 = 40.000,00.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.engine.labor.horas_extra import HoraExtraFestivaSinFactorConfirmadoError
from app.services.area_strategy import LaboralStrategy
from database.models import (
    HoraExtraLaboral,
    Obligacion,
    TipoContratoLaboral,
    TipoObligacion,
    TipoReajusteAnual,
)


def _obligacion(
    fecha_inicio=date(2020, 1, 1),
    fecha_fin=date(2020, 12, 31),
    fecha_pago_total=date(2020, 12, 31),
    categoria="LIQUIDACION_CONTRATO_LABORAL",
    tipo=TipoObligacion.PUNTUAL,
):
    return Obligacion(
        id=1,
        expediente_id=1,
        tipo=tipo,
        concepto="Liquidacion de contrato",
        categoria=categoria,
        fecha_origen=fecha_inicio,
        valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        pagada=fecha_pago_total is not None,
        fecha_pago_total=fecha_pago_total,
        despido_injustificado=False,
        tipo_contrato_laboral=TipoContratoLaboral.INDEFINIDO,
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )


def _hora_extra(concepto, fecha, horas, valor_hora, porcentaje_manual=None):
    return HoraExtraLaboral(
        obligacion_id=1,
        concepto=concepto,
        fecha_causacion=fecha,
        numero_horas=Decimal(horas),
        valor_hora=Decimal(valor_hora),
        porcentaje_manual=None if porcentaje_manual is None else Decimal(porcentaje_manual),
    )


def _liquidar(obligacion, fecha_corte=date(2021, 6, 1)):
    return LaboralStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
    )


def _items_horas_extra(resultado):
    return [item for item in resultado.items if item.balance.event_type == "HORAS_EXTRA"]


def test_sin_horas_extra_la_liquidacion_no_cambia():
    resultado = _liquidar(_obligacion())

    assert _items_horas_extra(resultado) == []
    assert resultado.final_balance().principal == Decimal("7860000.00")


def test_hed_y_hen_se_suman_como_rubro_propio_con_los_factores_del_motor():
    obligacion = _obligacion()
    obligacion.horas_extra_laborales = [
        _hora_extra("HED", date(2020, 3, 15), "10", "10000"),
        _hora_extra("HEN", date(2020, 4, 20), "4", "10000"),
    ]

    resultado = _liquidar(obligacion)

    items = _items_horas_extra(resultado)
    # Saldo de capital acumulado tras cada fila: HED (15/03) y luego HEN
    # (20/04), ambas antes de las prestaciones (causadas el 31/12/2020).
    saldos = [item.balance.debt.principal for item in items]
    assert saldos == [Decimal("125000.00"), Decimal("195000.00")]
    assert resultado.final_balance().principal == Decimal("7860000.00") + Decimal("195000.00")
    assert "Horas extra HED" in items[0].concept
    assert "1.25" in items[0].concept
    assert "Horas extra HEN" in items[1].concept
    assert "15/03/2020" in items[0].concept


def test_hefd_y_hefn_usan_el_tramo_de_la_ley_2466_segun_la_fecha_de_causacion():
    def _contrato():
        return _obligacion(
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2026, 12, 31),
            fecha_pago_total=date(2026, 12, 31),
        )

    sin = _liquidar(_contrato(), fecha_corte=date(2027, 1, 31))
    con_horas = _contrato()
    con_horas.horas_extra_laborales = [
        _hora_extra("HEFD", date(2025, 8, 10), "3", "8000"),
        _hora_extra("HEFN", date(2026, 7, 5), "2", "8000"),
    ]
    con = _liquidar(con_horas, fecha_corte=date(2027, 1, 31))

    diferencia = con.final_balance().principal - sin.final_balance().principal
    assert diferencia == Decimal("49200.00") + Decimal("42400.00")
    conceptos = [item.concept for item in _items_horas_extra(con)]
    assert "2.05" in conceptos[0]
    assert "2.65" in conceptos[1]


def test_hora_extra_festiva_antes_del_tramo_1_sin_porcentaje_lanza_error_explicativo():
    obligacion = _obligacion()
    obligacion.horas_extra_laborales = [_hora_extra("HEFD", date(2020, 5, 1), "2", "10000")]

    with pytest.raises(HoraExtraFestivaSinFactorConfirmadoError, match="porcentaje"):
        _liquidar(obligacion)


def test_hora_extra_festiva_antes_del_tramo_1_usa_el_porcentaje_digitado():
    obligacion = _obligacion()
    obligacion.horas_extra_laborales = [
        _hora_extra("HEFD", date(2020, 5, 1), "2", "10000", porcentaje_manual="100")
    ]

    resultado = _liquidar(obligacion)

    items = _items_horas_extra(resultado)
    assert len(items) == 1
    assert resultado.final_balance().principal == Decimal("7860000.00") + Decimal("40000.00")
    assert "digitado" in items[0].concept.lower()


def test_hora_extra_fuera_del_rango_del_contrato_lanza_error():
    obligacion = _obligacion()
    obligacion.horas_extra_laborales = [_hora_extra("HED", date(2021, 2, 1), "2", "10000")]

    with pytest.raises(ValueError, match="fuera del rango del contrato"):
        _liquidar(obligacion)


def test_salarios_dejados_de_percibir_no_admite_horas_extra():
    obligacion = _obligacion(
        categoria="SALARIOS_DEJADOS_DE_PERCIBIR",
        tipo=TipoObligacion.RECURRENTE,
        fecha_pago_total=None,
    )
    obligacion.horas_extra_laborales = [_hora_extra("HED", date(2020, 3, 15), "2", "10000")]

    with pytest.raises(ValueError, match="horas extra"):
        _liquidar(obligacion)


def test_horas_extra_no_cambian_la_indemnizacion_moratoria_ni_las_prestaciones():
    # Pagado 30 dias despues de terminar: moratoria fase 1 = 3.000.000,00 en
    # ambos casos (la base de la moratoria y de las prestaciones no cambia).
    def _contrato():
        return _obligacion(fecha_pago_total=date(2021, 1, 30))

    sin = _liquidar(_contrato())
    con_horas = _contrato()
    con_horas.horas_extra_laborales = [_hora_extra("HED", date(2020, 3, 15), "10", "10000")]
    con = _liquidar(con_horas)

    def _montos_no_horas_extra(resultado):
        return [
            (item.concept, item.balance.event_type)
            for item in resultado.items
            if item.balance.event_type != "HORAS_EXTRA"
        ]

    assert _montos_no_horas_extra(con) == _montos_no_horas_extra(sin)
    assert con.final_balance().principal == Decimal("10860000.00") + Decimal("125000.00")


def test_etiqueta_del_rubro_muestra_horas_valor_factor_y_porcentaje_digitado():
    obligacion = _obligacion()
    obligacion.horas_extra_laborales = [
        _hora_extra("HEFD", date(2020, 5, 1), "2", "10000", porcentaje_manual="100.00")
    ]

    concepto = _items_horas_extra(_liquidar(obligacion))[0].concept

    assert concepto == (
        "Horas extra HEFD (2 h x valor hora $10,000.00 x factor 2, porcentaje digitado "
        "100 % -- sin factor confirmado antes del 01/07/2025, causadas el 01/05/2020)"
    )


def test_rubro_horas_extra_llega_a_la_tabla_del_reporte_pdf_word():
    # ReportTableBuilder.build_matrix alimenta la cronologia de PDF y Word.
    from app.engine.reports.table_builder import ReportTableBuilder

    obligacion = _obligacion()
    obligacion.horas_extra_laborales = [_hora_extra("HED", date(2020, 3, 15), "10", "10000")]

    matriz = ReportTableBuilder().build_matrix(_liquidar(obligacion))

    filas = [fila for fila in matriz if fila["concepto"].startswith("Horas extra HED")]
    assert len(filas) == 1
    assert filas[0]["fecha"] == "15/03/2020"
    assert filas[0]["saldo_capital"] == "$125,000.00"
