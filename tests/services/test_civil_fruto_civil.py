"""Sprint 100 (wiring): obligacion "Fruto civil" (categoria FRUTO_CIVIL) del
area Civil/Familia liquidada con el motor `calcular_fruto_civil`
(app/engine/civil/fruto_civil.py).

Valores esperados calculados a mano con la serie IPC mensual real del DANE
(misma serie y mismos numeros de tests/engine/civil/test_fruto_civil.py):
referencia 31/01/2019 -> IPC ene-2019 = 100,60; feb = 101,18; mar = 101,62;
abr = 102,12. Canon 1.000.000, gasto de conservacion 100.000/mes:
  feb-2019: 1.005.765,41 - 100.000 = 905.765,41
  mar-2019: 1.010.139,17 - 100.000 = 910.139,17
  abr-2019: 1.015.109,34 - 100.000 = 915.109,34
  total = 2.731.013,92

Decision (no confirmada por el despacho, ver docs/Pendientes.md Sprint 100):
el fruto civil NO genera interes despues de su causacion -- se suma "en seco".
"""

from datetime import date
from decimal import Decimal

import pytest

from app.engine.reports.summary import ReportSummaryBuilder
from app.services.area_strategy import CivilFamiliaStrategy
from database.models import Abono, Obligacion, TipoObligacion


def _fruto_civil(**kwargs) -> Obligacion:
    campos = {
        "id": 1,
        "expediente_id": 1,
        "tipo": TipoObligacion.PUNTUAL,
        "concepto": "Frutos del apartamento 301",
        "categoria": "FRUTO_CIVIL",
        "valor": Decimal("1000000.00"),
        # La tasa capturada se ignora: el fruto civil no genera interes.
        "tasa_efectiva_anual": Decimal("6.00"),
        "fecha_origen": date(2019, 2, 1),
        "fecha_fin": date(2019, 4, 30),
        "fecha_referencia_canon": date(2019, 1, 31),
        "gasto_conservacion_mensual": Decimal("100000.00"),
        "aplica_indexacion_ipc": False,
        "interes_sobre_capital_indexado": False,
    }
    campos.update(kwargs)
    return Obligacion(**campos)


def _filas_fruto(resultado):
    return [i for i in resultado.items if i.balance.event_type == "FRUTO_CIVIL"]


def test_fruto_civil_genera_una_fila_por_mes_con_el_neto_del_motor():
    resultado = CivilFamiliaStrategy().liquidar([_fruto_civil()], [], date(2020, 1, 1))

    filas = _filas_fruto(resultado)
    assert [f.date for f in filas] == [date(2019, 2, 28), date(2019, 3, 31), date(2019, 4, 30)]
    # Saldo de capital acumulado fila a fila = suma de los netos mensuales.
    assert [f.balance.debt.principal for f in filas] == [
        Decimal("905765.41"),
        Decimal("1815904.58"),
        Decimal("2731013.92"),
    ]
    assert "02/2019" in filas[0].concept
    assert "Frutos del apartamento 301" in filas[0].concept
    assert resultado.final_balance().principal == Decimal("2731013.92")


def test_fruto_civil_no_genera_interes_aunque_la_obligacion_traiga_tasa():
    resultado = CivilFamiliaStrategy().liquidar([_fruto_civil()], [], date(2020, 1, 1))

    assert resultado.total_interest_accrued() == Decimal("0.00")
    assert resultado.final_balance().interest == Decimal("0.00")
    assert resultado.final_balance().total() == Decimal("2731013.92")


def test_fruto_civil_sin_gasto_de_conservacion():
    # 1.005.765,41 + 1.010.139,17 + 1.015.109,34 = 3.031.013,92
    obligacion = _fruto_civil(gasto_conservacion_mensual=None)
    resultado = CivilFamiliaStrategy().liquidar([obligacion], [], date(2020, 1, 1))

    assert resultado.final_balance().principal == Decimal("3031013.92")


def test_fruto_civil_con_abono_reduce_el_capital_sin_intereses():
    abono = Abono(
        id=1, obligacion_id=1, fecha=date(2019, 6, 1), monto=Decimal("1000000.00")
    )
    resultado = CivilFamiliaStrategy().liquidar([_fruto_civil()], [abono], date(2020, 1, 1))

    assert resultado.total_payments_applied() == Decimal("1000000.00")
    assert resultado.final_balance().principal == Decimal("1731013.92")
    assert resultado.final_balance().interest == Decimal("0.00")


def test_fruto_civil_se_corta_en_la_fecha_de_corte_con_alerta():
    # Corte 10/03/2019 dentro del periodo: feb completo 905.765,41 + mar 10/31:
    # canon 1.010.139,17 x 10/31 = 325.851,35 - gasto 100.000 x 10/31 = 32.258,06
    # -> 293.593,29. Total 1.199.358,70.
    resultado = CivilFamiliaStrategy().liquidar([_fruto_civil()], [], date(2019, 3, 10))

    filas = _filas_fruto(resultado)
    assert [f.date for f in filas] == [date(2019, 2, 28), date(2019, 3, 10)]
    assert resultado.final_balance().principal == Decimal("1199358.70")
    assert any("fecha de corte" in alerta for alerta in resultado.alertas)


def test_fruto_civil_no_altera_la_liquidacion_de_otra_obligacion_del_expediente():
    dano = Obligacion(
        id=2,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente",
        categoria="DANO_EMERGENTE",
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        fecha_origen=date(2019, 1, 1),
        aplica_indexacion_ipc=False,
        interes_sobre_capital_indexado=False,
    )
    solo_dano = CivilFamiliaStrategy().liquidar([dano], [], date(2020, 1, 1))
    mixto = CivilFamiliaStrategy().liquidar([dano, _fruto_civil()], [], date(2020, 1, 1))

    assert solo_dano.total_interest_accrued() > Decimal("0.00")
    assert mixto.total_interest_accrued() == solo_dano.total_interest_accrued()
    assert mixto.final_balance().principal == Decimal("1000000.00") + Decimal("2731013.92")


def test_fruto_civil_ignora_la_indexacion_de_la_obligacion():
    # El canon ya se indexa mes a mes; no hay segunda actualizacion a la fecha
    # de corte (no confirmada). La vista de sensibilidad "con indexacion"
    # (Sprint 107) fuerza aplica_indexacion_ipc=True en todo el expediente y
    # debe dar el mismo resultado en vez de fallar.
    obligacion = _fruto_civil(aplica_indexacion_ipc=True, interes_sobre_capital_indexado=True)
    resultado = CivilFamiliaStrategy().liquidar([obligacion], [], date(2020, 1, 1))

    assert not any(i.balance.event_type == "INDEXATION" for i in resultado.items)
    assert resultado.final_balance().total() == Decimal("2731013.92")


def test_resumen_expone_el_total_de_fruto_civil_como_rubro_propio():
    dano = Obligacion(
        id=2,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente",
        categoria="DANO_EMERGENTE",
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        fecha_origen=date(2019, 1, 1),
        aplica_indexacion_ipc=False,
        interes_sobre_capital_indexado=False,
    )
    resultado = CivilFamiliaStrategy().liquidar([dano, _fruto_civil()], [], date(2020, 1, 1))

    assert resultado.total_fruto_civil() == Decimal("2731013.92")
    summary = ReportSummaryBuilder().build_summary(resultado)
    assert summary["total_fruto_civil"] == "$2,731,013.92"


def test_resumen_omite_fruto_civil_cuando_no_hay():
    dano = Obligacion(
        id=2,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente",
        categoria="DANO_EMERGENTE",
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        fecha_origen=date(2019, 1, 1),
        aplica_indexacion_ipc=False,
        interes_sobre_capital_indexado=False,
    )
    resultado = CivilFamiliaStrategy().liquidar([dano], [], date(2020, 1, 1))

    assert resultado.total_fruto_civil() == Decimal("0.00")
    assert "total_fruto_civil" not in ReportSummaryBuilder().build_summary(resultado)


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"fecha_fin": None}, "fecha final"),
        ({"fecha_referencia_canon": None}, "fecha de referencia"),
        ({"tipo": TipoObligacion.RECURRENTE}, "Puntual"),
        ({"fecha_fin": date(2019, 1, 31)}, "anterior"),
    ],
)
def test_fruto_civil_rechaza_datos_incompletos_o_incompatibles(cambios, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        CivilFamiliaStrategy().liquidar([_fruto_civil(**cambios)], [], date(2020, 1, 1))


def test_fruto_civil_guardado_en_bd_se_liquida_y_admite_la_vista_de_sensibilidad():
    # Recorrido completo desde la BD (columnas nuevas del Sprint 100) hasta la
    # liquidacion oficial y la vista "con/sin indexacion" del Sprint 107.
    import database.session as session_module
    from app.services.vista_sensibilidad_indexacion import (
        cargar_datos_de_liquidacion,
        liquidar_vista_sensibilidad,
    )
    from database.models import AreaDerecho, Expediente

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-100",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2020, 1, 1),
    )
    session.add(expediente)
    session.commit()
    obligacion = _fruto_civil(id=None, expediente_id=expediente.id, tasa_efectiva_anual=0)
    session.add(obligacion)
    session.commit()
    expediente_id = expediente.id
    session.close()

    obligaciones, abonos, _area = cargar_datos_de_liquidacion(expediente_id)
    oficial = CivilFamiliaStrategy().liquidar(obligaciones, abonos, date(2020, 1, 1))
    con_indexacion = liquidar_vista_sensibilidad(expediente_id, date(2020, 1, 1), True)

    assert oficial.final_balance().total() == Decimal("2731013.92")
    assert con_indexacion.final_balance().total() == Decimal("2731013.92")
