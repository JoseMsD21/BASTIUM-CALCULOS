"""Sprint 74: calcula si una obligacion alimentaria de Civil/Familia sigue vigente
segun el tipo de beneficiario (arbol de decision pedido por el usuario, reporte
2026-08-13, ver docs/Pendientes.md Sprint 74).

Reglas implementadas (confirmadas como hecho conocido -- NO son la pregunta abierta
del sprint, ver docs/Preguntas-Para-Abogado-Abiertas.md, seccion Sprint 74):
- NINO sin discapacidad: vigente hasta los 18 anos si no estudia, hasta los 25 si
  estudia una carrera profesional/tecnica/tecnologica.
- NINO_DISCAPACIDAD con discapacidad_permanente=True: vitalicio.

Todo lo demas (CONYUGE, PADRES, OTRO, y NINO_DISCAPACIDAD sin marcar permanente)
debe quedar como "no determinable automaticamente" -- estos tests verifican
explicitamente que NUNCA se les aplique el limite de edad de NINO ni se les
invente un plazo."""

from datetime import date

import pytest

from app.services.vigencia_alimentos import (
    EDAD_LIMITE_NINO_ESTUDIA,
    EDAD_LIMITE_NINO_NO_ESTUDIA,
    calcular_edad,
    calcular_vigencia_alimentos,
    fecha_fin_efectiva_recurrente,
)
from database.models import Beneficiario, TipoBeneficiario


def _beneficiario(**kwargs) -> Beneficiario:
    base = dict(nombre="Test", fecha_nacimiento=date(2010, 1, 1), tipo=TipoBeneficiario.NINO)
    base.update(kwargs)
    return Beneficiario(**base)


# --- calcular_edad ----------------------------------------------------------


def test_calcular_edad_cumpleanos_ya_paso_este_anio():
    assert calcular_edad(date(2000, 1, 1), date(2026, 6, 1)) == 26


def test_calcular_edad_cumpleanos_no_ha_pasado_este_anio():
    assert calcular_edad(date(2000, 6, 15), date(2026, 6, 1)) == 25


def test_calcular_edad_exactamente_el_dia_del_cumpleanos():
    assert calcular_edad(date(2000, 6, 1), date(2026, 6, 1)) == 26


def test_calcular_edad_fecha_nacimiento_futura_lanza_error():
    with pytest.raises(ValueError):
        calcular_edad(date(2030, 1, 1), date(2026, 6, 1))


# --- NINO sin discapacidad ----------------------------------------------------


def test_nino_no_estudia_vigente_antes_de_cumplir_18():
    beneficiario = _beneficiario(
        fecha_nacimiento=date(2010, 5, 10), tipo=TipoBeneficiario.NINO, estudia=False
    )
    resultado = calcular_vigencia_alimentos(beneficiario, date(2028, 5, 9))
    assert resultado.determinable_automaticamente is True
    assert resultado.vigente is True
    assert resultado.fecha_fin_vigencia == date(2028, 5, 10)


def test_nino_no_estudia_deja_de_estar_vigente_al_cumplir_18():
    beneficiario = _beneficiario(
        fecha_nacimiento=date(2010, 5, 10), tipo=TipoBeneficiario.NINO, estudia=False
    )
    resultado = calcular_vigencia_alimentos(beneficiario, date(2028, 5, 10))
    assert resultado.vigente is False
    assert resultado.fecha_fin_vigencia == date(2028, 5, 10)


def test_nino_estudia_sigue_vigente_pasados_los_18():
    beneficiario = _beneficiario(
        fecha_nacimiento=date(2010, 5, 10), tipo=TipoBeneficiario.NINO, estudia=True
    )
    resultado = calcular_vigencia_alimentos(beneficiario, date(2028, 5, 10))
    assert resultado.vigente is True
    assert resultado.fecha_fin_vigencia == date(2035, 5, 10)


def test_nino_estudia_deja_de_estar_vigente_al_cumplir_25():
    beneficiario = _beneficiario(
        fecha_nacimiento=date(2010, 5, 10), tipo=TipoBeneficiario.NINO, estudia=True
    )
    resultado = calcular_vigencia_alimentos(beneficiario, date(2035, 5, 10))
    assert resultado.vigente is False
    assert resultado.fecha_fin_vigencia == date(2035, 5, 10)


def test_edades_limite_son_18_y_25():
    assert EDAD_LIMITE_NINO_NO_ESTUDIA == 18
    assert EDAD_LIMITE_NINO_ESTUDIA == 25


# --- NINO_DISCAPACIDAD ---------------------------------------------------------


def test_nino_discapacidad_permanente_es_vitalicio():
    beneficiario = _beneficiario(
        fecha_nacimiento=date(2000, 1, 1),
        tipo=TipoBeneficiario.NINO_DISCAPACIDAD,
        discapacidad_permanente=True,
    )
    resultado = calcular_vigencia_alimentos(beneficiario, date(2026, 8, 20))
    assert resultado.determinable_automaticamente is True
    assert resultado.vigente is True
    assert resultado.fecha_fin_vigencia is None


def test_nino_discapacidad_no_permanente_no_es_determinable():
    """El sprint solo confirma la regla de vigencia vitalicia para discapacidad
    PERMANENTE -- no se reutiliza sin confirmacion la regla de NINO sin
    discapacidad (18/25) para este caso."""
    beneficiario = _beneficiario(
        fecha_nacimiento=date(2000, 1, 1),
        tipo=TipoBeneficiario.NINO_DISCAPACIDAD,
        discapacidad_permanente=False,
    )
    resultado = calcular_vigencia_alimentos(beneficiario, date(2026, 8, 20))
    assert resultado.determinable_automaticamente is False
    assert resultado.vigente is None
    assert resultado.fecha_fin_vigencia is None


def test_nino_discapacidad_permanente_none_no_es_determinable():
    beneficiario = _beneficiario(
        fecha_nacimiento=date(2000, 1, 1),
        tipo=TipoBeneficiario.NINO_DISCAPACIDAD,
        discapacidad_permanente=None,
    )
    resultado = calcular_vigencia_alimentos(beneficiario, date(2026, 8, 20))
    assert resultado.determinable_automaticamente is False


# --- CONYUGE / PADRES / OTRO: nunca determinable, nunca limite de edad --------


@pytest.mark.parametrize(
    "tipo", [TipoBeneficiario.CONYUGE, TipoBeneficiario.PADRES, TipoBeneficiario.OTRO]
)
def test_tipos_sin_criterio_confirmado_no_son_determinables(tipo):
    beneficiario = _beneficiario(fecha_nacimiento=date(1990, 1, 1), tipo=tipo)
    resultado = calcular_vigencia_alimentos(beneficiario, date(2026, 8, 20))
    assert resultado.determinable_automaticamente is False
    assert resultado.vigente is None
    assert resultado.fecha_fin_vigencia is None
    assert resultado.motivo  # debe explicar por que, no queda vacio


@pytest.mark.parametrize(
    "tipo", [TipoBeneficiario.CONYUGE, TipoBeneficiario.PADRES, TipoBeneficiario.OTRO]
)
def test_tipos_sin_criterio_confirmado_nunca_aplican_limite_18_25(tipo):
    """Aunque el beneficiario tenga, por casualidad, la misma fecha de nacimiento
    que haria a un NINO dejar de estar vigente, CONYUGE/PADRES/OTRO nunca deben
    quedar cortados por edad -- Definicion de Hecho del Sprint 74."""
    beneficiario = _beneficiario(fecha_nacimiento=date(2000, 1, 1), tipo=tipo)
    resultado = calcular_vigencia_alimentos(beneficiario, date(2030, 1, 1))  # tendria 30 anos
    assert resultado.fecha_fin_vigencia is None
    assert resultado.determinable_automaticamente is False


# --- fecha_fin_efectiva_recurrente (helper de wiring) --------------------------


def test_fecha_fin_efectiva_usa_la_de_vigencia_si_no_hay_manual():
    beneficiario = _beneficiario(
        fecha_nacimiento=date(2010, 5, 10), tipo=TipoBeneficiario.NINO, estudia=False
    )
    fin = fecha_fin_efectiva_recurrente(None, beneficiario, date(2020, 1, 1))
    assert fin == date(2028, 5, 10)


def test_fecha_fin_efectiva_usa_la_mas_temprana_entre_manual_y_vigencia():
    beneficiario = _beneficiario(
        fecha_nacimiento=date(2010, 5, 10), tipo=TipoBeneficiario.NINO, estudia=False
    )
    fin = fecha_fin_efectiva_recurrente(date(2027, 1, 1), beneficiario, date(2020, 1, 1))
    assert fin == date(2027, 1, 1)

    fin_2 = fecha_fin_efectiva_recurrente(date(2029, 1, 1), beneficiario, date(2020, 1, 1))
    assert fin_2 == date(2028, 5, 10)


def test_fecha_fin_efectiva_sin_beneficiario_devuelve_solo_la_manual():
    assert fecha_fin_efectiva_recurrente(date(2027, 1, 1), None, date(2020, 1, 1)) == date(
        2027, 1, 1
    )
    assert fecha_fin_efectiva_recurrente(None, None, date(2020, 1, 1)) is None


def test_fecha_fin_efectiva_conyuge_no_aporta_ninguna_fecha():
    beneficiario = _beneficiario(fecha_nacimiento=date(1990, 1, 1), tipo=TipoBeneficiario.CONYUGE)
    assert fecha_fin_efectiva_recurrente(None, beneficiario, date(2026, 1, 1)) is None
    assert fecha_fin_efectiva_recurrente(
        date(2030, 1, 1), beneficiario, date(2026, 1, 1)
    ) == date(2030, 1, 1)


def test_fecha_fin_efectiva_nino_discapacidad_permanente_no_aporta_fecha():
    beneficiario = _beneficiario(
        fecha_nacimiento=date(2000, 1, 1),
        tipo=TipoBeneficiario.NINO_DISCAPACIDAD,
        discapacidad_permanente=True,
    )
    assert fecha_fin_efectiva_recurrente(None, beneficiario, date(2026, 1, 1)) is None
