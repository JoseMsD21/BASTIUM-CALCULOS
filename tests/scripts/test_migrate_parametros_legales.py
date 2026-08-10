from datetime import date
from decimal import Decimal

import pytest

import database.session as session_module
from database.models import ParametroLegal


def test_migrar_siembra_las_39_claves_del_catalogo():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    claves = {fila.clave for fila in session.query(ParametroLegal).all()}
    session.close()
    assert claves == {
        "USURA_MULTIPLICADOR",
        "HONORARIOS_TOTAL_PCT",
        "ET635_PUNTOS_DESCUENTO",
        "CIVIL_ANNUAL_RATE",
        "PRESCRIPCION_EJECUTIVA_MESES",
        "PRESCRIPCION_ORDINARIA_MESES",
        "PRESCRIPCION_HONORARIOS_MESES",
        "PRESCRIPCION_CAMBIARIA_DIRECTA_MESES",
        "PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES",
        "PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES",
        "CADUCIDAD_IMPUGNACION_INEFICACIA_SOCIETARIA_MESES",
        "CADUCIDAD_CHEQUES_MESES",
        "CADUCIDAD_ENRIQUECIMIENTO_SIN_CAUSA_MESES",
        "CADUCIDAD_TRANSPORTE_MESES",
        "CADUCIDAD_SEGURO_ORDINARIA_MESES",
        "CADUCIDAD_SEGURO_EXTRAORDINARIA_MESES",
        "CADUCIDAD_IMPUGNACION_ACTAS_SOCIALES_MESES",
        "SMLMV",
        "IPC_INDICE_ACUMULADO",
        "IBC_CONSUMO_ORDINARIO",
        "USURA_CONSUMO_ORDINARIO",
        "UVT",
        "EXTEMPORANEIDAD_PCT_MENSUAL",
        "INEXACTITUD_PCT",
        "INEXACTITUD_AGRAVADA_PCT",
        "ERROR_ARITMETICO_PCT",
        "SS_PENSION_PCT",
        "SS_SALUD_PCT",
        "SS_ARL_NIVEL_I_PCT",
        "SS_ARL_NIVEL_II_PCT",
        "SS_ARL_NIVEL_III_PCT",
        "SS_ARL_NIVEL_IV_PCT",
        "SS_ARL_NIVEL_V_PCT",
        "SS_FSP_TRAMO_1_PCT",
        "SS_FSP_TRAMO_2_PCT",
        "SS_FSP_TRAMO_3_PCT",
        "SS_FSP_TRAMO_4_PCT",
        "SS_FSP_TRAMO_5_PCT",
        "SS_FSP_TRAMO_6_PCT",
    }


def test_migrar_smlmv_2026_coincide_con_el_valor_conocido():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    fila = (
        session.query(ParametroLegal)
        .filter(ParametroLegal.clave == "SMLMV", ParametroLegal.vigente_desde == date(2026, 1, 1))
        .one()
    )
    session.close()
    assert fila.valor == Decimal("1750905.00")


def test_migrar_uvt_2026_coincide_con_el_valor_conocido():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    fila = (
        session.query(ParametroLegal)
        .filter(ParametroLegal.clave == "UVT", ParametroLegal.vigente_desde == date(2026, 1, 1))
        .one()
    )
    session.close()
    assert fila.valor == Decimal("52374.00")


def test_migrar_ibc_usura_primer_tramo_1997_coincide_con_inicio_y_fin():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    fila = (
        session.query(ParametroLegal)
        .filter(
            ParametroLegal.clave == "IBC_CONSUMO_ORDINARIO",
            ParametroLegal.vigente_desde == date(1997, 7, 1),
        )
        .one()
    )
    session.close()
    assert fila.valor == Decimal("36.50")
    assert fila.vigente_hasta == date(1997, 8, 31)


def test_migrar_usura_multiplicador_coincide_con_la_constante_actual():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    fila = (
        session.query(ParametroLegal).filter(ParametroLegal.clave == "USURA_MULTIPLICADOR").one()
    )
    session.close()
    assert fila.valor == Decimal("1.5")


def test_migrar_es_idempotente():
    from scripts.migrate_parametros_legales import migrar

    primera = migrar()
    segunda = migrar()
    assert primera == 39
    assert segunda == 0


def test_migrar_sancion_extemporaneidad_pct_mensual_coincide_con_el_valor_conocido():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    fila = (
        session.query(ParametroLegal)
        .filter(ParametroLegal.clave == "EXTEMPORANEIDAD_PCT_MENSUAL")
        .one()
    )
    session.close()
    assert fila.valor == Decimal("5")


@pytest.mark.parametrize(
    "clave,valor_esperado",
    [
        ("SS_PENSION_PCT", Decimal("0.16")),
        ("SS_SALUD_PCT", Decimal("0.125")),
        ("SS_ARL_NIVEL_I_PCT", Decimal("0.00522")),
        ("SS_ARL_NIVEL_II_PCT", Decimal("0.01044")),
        ("SS_ARL_NIVEL_III_PCT", Decimal("0.02436")),
        ("SS_ARL_NIVEL_IV_PCT", Decimal("0.04350")),
        ("SS_ARL_NIVEL_V_PCT", Decimal("0.06960")),
        ("SS_FSP_TRAMO_1_PCT", Decimal("0.01")),
        ("SS_FSP_TRAMO_2_PCT", Decimal("0.012")),
        ("SS_FSP_TRAMO_3_PCT", Decimal("0.014")),
        ("SS_FSP_TRAMO_4_PCT", Decimal("0.016")),
        ("SS_FSP_TRAMO_5_PCT", Decimal("0.018")),
        ("SS_FSP_TRAMO_6_PCT", Decimal("0.02")),
    ],
)
def test_migrar_valores_seguridad_social_coinciden_con_el_pdf(clave, valor_esperado):
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    fila = session.query(ParametroLegal).filter_by(clave=clave).one()
    session.close()
    assert fila.valor == valor_esperado
