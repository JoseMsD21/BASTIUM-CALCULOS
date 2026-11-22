"""Sprint 106: datos del titulo ejecutivo capturados una sola vez por
expediente -- fecha_limite_prescripcion calculada (no guardada)."""

from datetime import date

from app.services.titulo_ejecutivo import (
    ETIQUETAS_TIPO_TITULO,
    calcular_fecha_limite_prescripcion_titulo,
)
from database.models import Expediente, TipoTituloEjecutivo


def test_tipo_titulo_incluye_los_tipos_del_despacho_y_otro():
    valores = {tipo.value for tipo in TipoTituloEjecutivo}
    assert {"SENTENCIA", "ACTA", "LAUDO", "OTRO"} <= valores
    assert set(ETIQUETAS_TIPO_TITULO) == set(TipoTituloEjecutivo)


def test_fecha_limite_se_cuenta_desde_la_exigibilidad_sumando_los_anios():
    # 2020-03-16 (lunes, habil) + 5 años = 2025-03-16 (domingo) -> corre al
    # siguiente dia habil, mismo computo calendario que calcular_prescripcion.
    assert calcular_fecha_limite_prescripcion_titulo(date(2020, 3, 16), 5) == date(2025, 3, 17)


def test_fecha_limite_en_dia_habil_no_se_corre():
    # 2021-06-01 + 5 años = 2026-06-01 (lunes, habil).
    assert calcular_fecha_limite_prescripcion_titulo(date(2021, 6, 1), 5) == date(2026, 6, 1)


def test_fecha_limite_29_de_febrero_se_topa_a_28_en_anio_no_bisiesto():
    # 2024-02-29 + 1 año -> 2025-02-28 (viernes, habil).
    assert calcular_fecha_limite_prescripcion_titulo(date(2024, 2, 29), 1) == date(2025, 2, 28)


def test_fecha_limite_es_none_sin_exigibilidad_o_sin_termino():
    assert calcular_fecha_limite_prescripcion_titulo(None, 5) is None
    assert calcular_fecha_limite_prescripcion_titulo(date(2020, 1, 1), None) is None
    assert calcular_fecha_limite_prescripcion_titulo(date(2020, 1, 1), 0) is None


def test_expediente_expone_fecha_limite_prescripcion_calculada():
    expediente = Expediente(
        fecha_exigibilidad=date(2021, 6, 1), termino_prescripcion_anos=5
    )
    assert expediente.fecha_limite_prescripcion == date(2026, 6, 1)
    assert Expediente().fecha_limite_prescripcion is None
