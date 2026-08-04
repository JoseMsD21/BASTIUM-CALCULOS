from datetime import date
from datetime import datetime as _dt
from decimal import Decimal

import pytest

import database.session as session_module
from database.models import ParametroLegal


@pytest.fixture(autouse=True)
def _parametros_seguridad_social_en_memoria():
    # SeguridadSocialCalculator.calcular lee SMLMV y las 7 claves SS_* via
    # parametro_service en cada llamada -- fixture aislada de disco, mismo
    # criterio que tests/engine/labor/test_moratory_indemnity.py.
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="SMLMV", valor=Decimal("877803.00"), vigente_desde=date(2020, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    valores_abiertos = {
        "SS_PENSION_PCT": Decimal("0.16"),
        "SS_SALUD_PCT": Decimal("0.125"),
        "SS_ARL_NIVEL_I_PCT": Decimal("0.00522"),
        "SS_ARL_NIVEL_II_PCT": Decimal("0.01044"),
        "SS_ARL_NIVEL_III_PCT": Decimal("0.02436"),
        "SS_ARL_NIVEL_IV_PCT": Decimal("0.04350"),
        "SS_ARL_NIVEL_V_PCT": Decimal("0.06960"),
        "SS_FSP_TRAMO_1_PCT": Decimal("0.01"),
        "SS_FSP_TRAMO_2_PCT": Decimal("0.012"),
        "SS_FSP_TRAMO_3_PCT": Decimal("0.014"),
        "SS_FSP_TRAMO_4_PCT": Decimal("0.016"),
        "SS_FSP_TRAMO_5_PCT": Decimal("0.018"),
        "SS_FSP_TRAMO_6_PCT": Decimal("0.02"),
    }
    for clave, valor in valores_abiertos.items():
        session.add(ParametroLegal(
            clave=clave, valor=valor, vigente_desde=date(1900, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    session.commit()
    session.close()


def test_cotizacion_basica_sin_suspension_ni_fsp():
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("3000000.00"), dias_trabajados=30, dias_suspension=0,
        nivel_riesgo_arl="I", fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.ibc_mensual == Decimal("3000000.00")
    assert resultado.monto_pension == Decimal("480000.00")
    assert resultado.monto_salud == Decimal("375000.00")
    assert resultado.monto_arl == Decimal("15660.00")
    assert resultado.monto_fsp == Decimal("0.00")
    assert resultado.total == Decimal("870660.00")


def test_suspension_parcial_excluye_solo_arl_de_esos_dias():
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("3000000.00"), dias_trabajados=30, dias_suspension=15,
        nivel_riesgo_arl="I", fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.monto_pension == Decimal("480000.00")  # sin cambio
    assert resultado.monto_salud == Decimal("375000.00")  # sin cambio
    assert resultado.monto_arl == Decimal("7830.00")  # mitad de dias con ARL
    assert resultado.total == Decimal("862830.00")


@pytest.mark.parametrize("nivel,arl_esperado,total_esperado", [
    ("I", Decimal("15660.00"), Decimal("870660.00")),
    ("II", Decimal("31320.00"), Decimal("886320.00")),
    ("III", Decimal("73080.00"), Decimal("928080.00")),
    ("IV", Decimal("130500.00"), Decimal("985500.00")),
    ("V", Decimal("208800.00"), Decimal("1063800.00")),
])
def test_cada_nivel_de_riesgo_arl(nivel, arl_esperado, total_esperado):
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("3000000.00"), dias_trabajados=30, dias_suspension=0,
        nivel_riesgo_arl=nivel, fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.monto_arl == arl_esperado
    assert resultado.total == total_esperado


def test_arl_se_topa_al_8_7_por_ciento_ley_1562_de_2012():
    # Respuesta del despacho (Preguntas-Para-Abogado.md, Sprint 16): tope legal maximo
    # del 8.7% para cualquier nivel de riesgo ARL (Ley 1562/2012), sin importar el
    # porcentaje cargado en parametros_legales -- si alguien sube SS_ARL_NIVEL_V_PCT por
    # encima de eso desde la pantalla de Parametros (Sprint 13), el motor debe seguir
    # respetando el tope legal, no el valor cargado.
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="SMLMV", valor=Decimal("1300000.00"), vigente_desde=date(2025, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.add(ParametroLegal(
        clave="SS_ARL_NIVEL_V_PCT", valor=Decimal("0.10"), vigente_desde=date(2025, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.commit()
    session.close()

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("3000000.00"), dias_trabajados=30, dias_suspension=0,
        nivel_riesgo_arl="V", fecha_referencia=date(2025, 6, 1),
    )

    # 3.000.000 x 8.7% = 261.000.00 (no 3.000.000 x 10% = 300.000.00).
    assert resultado.monto_arl == Decimal("261000.00")


def test_ibc_se_ajusta_al_piso_de_1_smmlv():
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("500000.00"), dias_trabajados=30, dias_suspension=0,
        nivel_riesgo_arl="I", fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.ibc_mensual == Decimal("877803.00")
    assert resultado.monto_pension == Decimal("140448.48")
    assert resultado.monto_salud == Decimal("109725.38")
    assert resultado.monto_arl == Decimal("4582.13")
    assert resultado.monto_fsp == Decimal("0.00")


def test_ibc_se_ajusta_al_techo_de_25_smmlv():
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("30000000.00"), dias_trabajados=30, dias_suspension=0,
        nivel_riesgo_arl="I", fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.ibc_mensual == Decimal("21945075.00")
    assert resultado.monto_pension == Decimal("3511212.00")
    assert resultado.monto_salud == Decimal("2743134.38")
    assert resultado.monto_arl == Decimal("114553.29")
    assert resultado.monto_fsp == Decimal("438901.50")  # IBC cae en tramo 6 (>20 SMMLV)
    assert resultado.total == Decimal("6807801.17")


def test_fsp_no_aplica_justo_debajo_del_umbral_de_4_smmlv():
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("3511211.00"), dias_trabajados=30, dias_suspension=0,
        nivel_riesgo_arl="I", fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.monto_fsp == Decimal("0.00")


def test_fsp_aplica_justo_en_el_umbral_exacto_de_4_smmlv():
    from app.engine.labor.seguridad_social import SeguridadSocialCalculator

    resultado = SeguridadSocialCalculator.calcular(
        salario_base=Decimal("3511212.00"), dias_trabajados=30, dias_suspension=0,
        nivel_riesgo_arl="I", fecha_referencia=date(2020, 12, 31),
    )

    assert resultado.monto_fsp == Decimal("35112.12")  # 3511212.00 * 1% (tramo 1)


@pytest.mark.parametrize("multiplo_smmlv,tramo_pct_esperado", [
    (Decimal("4"), Decimal("0.01")),
    (Decimal("16"), Decimal("0.012")),
    (Decimal("17"), Decimal("0.014")),
    (Decimal("18"), Decimal("0.016")),
    (Decimal("19"), Decimal("0.018")),
    (Decimal("20"), Decimal("0.02")),
    (Decimal("25"), Decimal("0.02")),
])
def test_resolver_tramo_fsp_en_cada_frontera(multiplo_smmlv, tramo_pct_esperado):
    from app.engine.labor.seguridad_social import _resolver_tramo_fsp

    smmlv = Decimal("877803.00")
    ibc = smmlv * multiplo_smmlv

    assert _resolver_tramo_fsp(ibc, smmlv, date(2020, 12, 31)) == tramo_pct_esperado
