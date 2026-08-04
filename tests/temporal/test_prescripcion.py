from datetime import date
from datetime import datetime as _dt
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.engine.temporal.prescripcion import (
    TipoAccion,
    calcular_caducidad,
    calcular_prescripcion,
    fecha_interrupcion_efectiva,
    filtrar_cuotas_prescritas,
)
from app.engine.temporal.schedulers.family import FamilyScheduler
from database.models import Base, ParametroLegal

_PLAZOS_MESES = {
    "PRESCRIPCION_EJECUTIVA_MESES": 60,
    "PRESCRIPCION_ORDINARIA_MESES": 120,
    "PRESCRIPCION_HONORARIOS_MESES": 36,
    "PRESCRIPCION_CAMBIARIA_DIRECTA_MESES": 36,
    "PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES": 12,
    "PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES": 6,
    "CADUCIDAD_IMPUGNACION_INEFICACIA_SOCIETARIA_MESES": 60,
    "CADUCIDAD_CHEQUES_MESES": 6,
    "CADUCIDAD_ENRIQUECIMIENTO_SIN_CAUSA_MESES": 12,
    "CADUCIDAD_TRANSPORTE_MESES": 24,
    "CADUCIDAD_SEGURO_ORDINARIA_MESES": 24,
    "CADUCIDAD_SEGURO_EXTRAORDINARIA_MESES": 60,
    "CADUCIDAD_IMPUGNACION_ACTAS_SOCIALES_MESES": 2,
}


@pytest.fixture(autouse=True)
def _parametros_prescripcion_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    for clave, meses in _PLAZOS_MESES.items():
        session.add(ParametroLegal(
            clave=clave, valor=Decimal(meses), vigente_desde=date(1900, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    session.commit()
    session.close()


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


def test_calcular_caducidad_cheques_6_meses():
    # Respuesta del despacho (Preguntas-Para-Abogado.md, Sprint 7): Cheques, 6 meses.
    # 2025-05-10 + 6 meses -> 2025-11-10, lunes hábil.
    assert calcular_caducidad(date(2025, 5, 10), "CHEQUES") == date(2025, 11, 10)


def test_calcular_caducidad_enriquecimiento_sin_causa_1_anio():
    # Respuesta del despacho, Sprint 7: Enriquecimiento sin causa, 1 año.
    # 2024-06-01 + 12 meses -> raw 2025-06-01 (domingo, inhábil) -> corre al
    # siguiente hábil, 2025-06-03.
    assert calcular_caducidad(date(2024, 6, 1), "ENRIQUECIMIENTO_SIN_CAUSA") == date(2025, 6, 3)


def test_calcular_caducidad_transporte_2_anios():
    # Respuesta del despacho, Sprint 7: Transporte, 2 años.
    # 2023-09-15 + 24 meses -> 2025-09-15, lunes hábil.
    assert calcular_caducidad(date(2023, 9, 15), "TRANSPORTE") == date(2025, 9, 15)


def test_calcular_caducidad_seguro_ordinaria_2_anios():
    # Respuesta del despacho, Sprint 7: Seguro, 2 años (prescripción ordinaria) y
    # 5 años (extraordinaria) -- dos tipos_proceso distintos, mismo criterio que
    # los tres plazos cambiarios.
    assert calcular_caducidad(date(2023, 9, 15), "SEGURO_ORDINARIA") == date(2025, 9, 15)


def test_calcular_caducidad_seguro_extraordinaria_5_anios():
    assert calcular_caducidad(date(2020, 9, 15), "SEGURO_EXTRAORDINARIA") == date(2025, 9, 15)


def test_calcular_caducidad_impugnacion_actas_sociales_2_meses():
    # Respuesta del despacho, Sprint 7: Impugnación de Actas Sociales, 2 meses.
    # 2025-10-01 + 2 meses -> 2025-12-01, lunes hábil.
    assert calcular_caducidad(date(2025, 10, 1), "IMPUGNACION_ACTAS_SOCIALES") == date(2025, 12, 1)


def test_calcular_caducidad_tipo_desconocido_con_plazo_manual():
    # 2025-01-15 + 8 meses -> 2025-09-15, lunes hábil.
    assert calcular_caducidad(
        date(2025, 1, 15), "TUTELA_INCIDENTE_DESACATO", plazo_meses_manual=8
    ) == date(2025, 9, 15)


def test_calcular_caducidad_tipo_desconocido_sin_plazo_manual_lanza_error():
    with pytest.raises(ValueError):
        calcular_caducidad(date(2025, 1, 15), "TUTELA_INCIDENTE_DESACATO")


def test_calcular_caducidad_tipo_conocido_ignora_plazo_manual_si_ambos_se_pasan():
    # El catalogo conocido tiene prioridad: plazo_meses_manual se ignora si
    # tipo_proceso ya esta en PLAZOS_CADUCIDAD_MESES_CONOCIDOS.
    assert calcular_caducidad(
        date(2021, 4, 12), "IMPUGNACION_INEFICACIA_SOCIETARIA", plazo_meses_manual=1
    ) == date(2026, 4, 13)


def test_filtrar_cuotas_prescritas_separa_viejas_de_recientes():
    scheduler = FamilyScheduler()
    scheduler.add_monthly_obligation(
        amount=Decimal("500000"),
        concept="Cuota alimentaria",
        due_day=1,
        category="CHILD_SUPPORT",
    )
    eventos = scheduler.generate(start=date(2015, 1, 1), end=date(2026, 1, 1))
    assert len(eventos) == 133  # 11 anios completos de cuotas mensuales

    fecha_corte = date(2026, 1, 1)
    vivas, prescritas = filtrar_cuotas_prescritas(eventos, fecha_corte, TipoAccion.EJECUTIVA)

    assert len(prescritas) == 72
    assert len(vivas) == 61
    assert len(vivas) + len(prescritas) == len(eventos)

    # Las prescritas son las causadas hace mas de 5 anios (hasta 2020-12-01
    # inclusive); las vivas arrancan en 2021-01-01.
    assert max(e.date for e in prescritas) == date(2020, 12, 1)
    assert min(e.date for e in vivas) == date(2021, 1, 1)


def test_filtrar_cuotas_prescritas_no_muta_la_lista_original():
    scheduler = FamilyScheduler()
    scheduler.add_monthly_obligation(
        amount=Decimal("500000"),
        concept="Cuota alimentaria",
        due_day=1,
        category="CHILD_SUPPORT",
    )
    eventos = scheduler.generate(start=date(2015, 1, 1), end=date(2016, 1, 1))
    total_original = len(eventos)

    filtrar_cuotas_prescritas(eventos, date(2026, 1, 1), TipoAccion.EJECUTIVA)

    assert len(eventos) == total_original


def test_fecha_interrupcion_efectiva_retrotrae_si_notifica_dentro_del_anio():
    # 2024-03-01 + 1 año calendario -> vencimiento 2025-03-01 (sábado) corre
    # al siguiente hábil, 2025-03-03 (lunes, ver CalendarUtils.vencimiento_
    # calendario). Notificación 2024-10-01 cae muy dentro de ese plazo ->
    # retrotrae a la radicación.
    assert fecha_interrupcion_efectiva(
        date(2024, 3, 1), date(2024, 10, 1)
    ) == date(2024, 3, 1)


def test_fecha_interrupcion_efectiva_no_retrotrae_si_notifica_fuera_del_anio():
    # Notificación muy posterior al vencimiento fecha-a-fecha (2025-03-03,
    # ver test anterior) -> no retrotrae.
    assert fecha_interrupcion_efectiva(
        date(2024, 3, 1), date(2025, 6, 1)
    ) == date(2025, 6, 1)


def test_fecha_interrupcion_efectiva_notifica_el_dia_exacto_del_vencimiento_retrotrae():
    # Vencimiento fecha-a-fecha de 2024-03-01 + 1 año: 2025-03-01 es sábado,
    # corre al siguiente hábil (CalendarUtils.vencimiento_calendario),
    # 2025-03-03 (lunes) -- verificado ejecutando el código real antes de
    # escribir este plan, y cubierto de forma independiente en
    # tests/temporal/test_calendar.py. Notificar justo ese día límite
    # (inclusive) retrotrae.
    assert fecha_interrupcion_efectiva(
        date(2024, 3, 1), date(2025, 3, 3)
    ) == date(2024, 3, 1)


def test_fecha_interrupcion_efectiva_notifica_un_dia_despues_del_vencimiento_no_retrotrae():
    # Un día calendario después del vencimiento (2025-03-03, ver test
    # anterior) -- ya no retrotrae.
    assert fecha_interrupcion_efectiva(
        date(2024, 3, 1), date(2025, 3, 4)
    ) == date(2025, 3, 4)


def test_fecha_interrupcion_efectiva_bisiesto_366_dias_reales_pero_un_anio_calendario_retrotrae():
    # Bug corregido (Sprint 30): 2024-01-15 -> 2025-01-15 son 366 días reales
    # corridos (el 29 de febrero de 2024, bisiesto, cae dentro del rango),
    # pero es EXACTAMENTE un año fecha-a-fecha (AddYears(1); ambas fechas son
    # miércoles, día hábil, sin corrimiento -- verificado ejecutando el
    # código real antes de escribir este plan). La regla vieja
    # ((notificacion - radicacion).days <= 365) decía "366 > 365, NO
    # retrotrae" -- un día antes de lo que corresponde jurídicamente
    # (confirmación del despacho: "un año" es fecha a fecha, no 365 días
    # matemáticos). La regla corregida sí retrotrae, porque la notificación
    # llegó justo al año, ni un día tarde.
    assert fecha_interrupcion_efectiva(
        date(2024, 1, 15), date(2025, 1, 15)
    ) == date(2024, 1, 15)


def test_fecha_interrupcion_efectiva_bisiesto_367_dias_reales_un_dia_despues_del_anio_no_retrotrae():
    # Un día calendario después del caso anterior -- ya pasó el año
    # fecha-a-fecha, no retrotrae.
    assert fecha_interrupcion_efectiva(
        date(2024, 1, 15), date(2025, 1, 16)
    ) == date(2025, 1, 16)


def test_fecha_interrupcion_efectiva_rechaza_notificacion_anterior_a_radicacion():
    with pytest.raises(ValueError):
        fecha_interrupcion_efectiva(date(2024, 3, 1), date(2024, 1, 1))
