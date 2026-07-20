from datetime import date

import pytest

from app.engine.temporal.prescripcion import (
    TipoAccion,
    calcular_caducidad,
    calcular_prescripcion,
)


def test_calcular_prescripcion_ejecutiva_5_anios():
    # 2020-03-15 + 60 meses -> raw 2025-03-15 (sábado, inhábil) -> corre al
    # siguiente hábil, 2025-03-17 (lunes).
    assert calcular_prescripcion(date(2020, 3, 15), TipoAccion.EJECUTIVA) == date(2025, 3, 17)


def test_calcular_prescripcion_ordinaria_10_anios():
    # 2016-06-20 + 120 meses -> raw 2026-06-20 (sábado, inhábil) -> corre al
    # siguiente hábil, 2026-06-22 (lunes).
    assert calcular_prescripcion(date(2016, 6, 20), TipoAccion.ORDINARIA) == date(2026, 6, 22)


def test_calcular_prescripcion_honorarios_profesionales_3_anios():
    # 2023-02-10 + 36 meses -> 2026-02-10, martes hábil, sin corrimiento.
    assert calcular_prescripcion(date(2023, 2, 10), TipoAccion.HONORARIOS_PROFESIONALES) == date(2026, 2, 10)


def test_calcular_prescripcion_cambiaria_directa_3_anios():
    # Art. 789 C.Co. 2023-05-05 + 36 meses -> 2026-05-05, martes hábil.
    assert calcular_prescripcion(date(2023, 5, 5), TipoAccion.CAMBIARIA_DIRECTA) == date(2026, 5, 5)


def test_calcular_prescripcion_cambiaria_regreso_tenedor_1_anio():
    # Art. 790 C.Co. 2025-03-01 + 12 meses -> raw 2026-03-01 (domingo, inhábil)
    # -> corre al siguiente hábil, 2026-03-02 (lunes).
    assert calcular_prescripcion(date(2025, 3, 1), TipoAccion.CAMBIARIA_REGRESO_TENEDOR) == date(2026, 3, 2)


def test_calcular_prescripcion_cambiaria_regreso_entre_obligados_6_meses():
    # Art. 791 C.Co. 2025-09-01 + 6 meses -> 2026-03-01, domingo inhábil ->
    # corre al siguiente hábil, 2026-03-02 (lunes).
    assert calcular_prescripcion(date(2025, 9, 1), TipoAccion.CAMBIARIA_REGRESO_ENTRE_OBLIGADOS) == date(2026, 3, 2)


def test_calcular_prescripcion_desborde_fin_de_mes():
    # 2025-08-31 + 6 meses -> mes destino es febrero de 2026 (28 días, no
    # bisiesto): topa a 2026-02-28 (sábado, inhábil) -> corre al siguiente
    # hábil, 2026-03-02 (lunes, ya que domingo 1 de marzo también es inhábil).
    assert calcular_prescripcion(
        date(2025, 8, 31), TipoAccion.CAMBIARIA_REGRESO_ENTRE_OBLIGADOS
    ) == date(2026, 3, 2)


def test_calcular_caducidad_tipo_conocido_impugnacion_societaria():
    # 2021-04-12 + 60 meses -> 2026-04-12, domingo inhábil -> corre al
    # siguiente hábil, 2026-04-13 (lunes).
    assert calcular_caducidad(
        date(2021, 4, 12), "IMPUGNACION_INEFICACIA_SOCIETARIA"
    ) == date(2026, 4, 13)


def test_calcular_caducidad_tipo_desconocido_con_plazo_manual():
    # 2025-01-15 + 8 meses -> 2025-09-15, lunes hábil.
    assert calcular_caducidad(
        date(2025, 1, 15), "TUTELA_INCIDENTE_DESACATO", plazo_meses_manual=8
    ) == date(2025, 9, 15)


def test_calcular_caducidad_tipo_desconocido_sin_plazo_manual_lanza_error():
    with pytest.raises(ValueError):
        calcular_caducidad(date(2025, 1, 15), "TUTELA_INCIDENTE_DESACATO")
