from datetime import date

from app.engine.time.calendar import CalendarUtils


def test_es_dia_habil_fin_de_semana():
    assert CalendarUtils.es_dia_habil(date(2026, 1, 3)) is False  # sábado
    assert CalendarUtils.es_dia_habil(date(2026, 1, 4)) is False  # domingo


def test_es_dia_habil_dia_normal():
    assert CalendarUtils.es_dia_habil(date(2026, 1, 13)) is True  # martes normal


def test_es_dia_habil_festivo_fijo():
    assert CalendarUtils.es_dia_habil(date(2026, 1, 1)) is False  # Año Nuevo


def test_es_dia_habil_ley_emiliani():
    # Reyes Magos (6 de enero) se traslada por Ley Emiliani al lunes siguiente,
    # 12 de enero de 2026. La fecha real del festivo (martes 6) queda hábil;
    # la fecha observada (lunes 12) queda inhábil.
    assert CalendarUtils.es_dia_habil(date(2026, 1, 6)) is True
    assert CalendarUtils.es_dia_habil(date(2026, 1, 12)) is False


def test_sumar_dias_habiles_no_cuenta_fecha_inicio():
    # fecha_inicio es lunes hábil, sin festivos cerca. sumar 1 día hábil debe
    # devolver el martes, NUNCA el mismo lunes (fecha_inicio no cuenta como día 1).
    lunes = date(2026, 1, 13)
    assert CalendarUtils.sumar_dias_habiles(lunes, 1) == date(2026, 1, 14)


def test_sumar_dias_habiles_cruza_fin_de_semana_y_festivo():
    # Verificado independientemente: 10 días hábiles desde el lunes 2025-12-22
    # (sin contar ese día) caen en miércoles 2026-01-07, cruzando Navidad
    # (2025-12-25), un fin de semana (27-28 dic), Año Nuevo (2026-01-01) y
    # otro fin de semana (3-4 ene).
    inicio = date(2025, 12, 22)
    assert CalendarUtils.sumar_dias_habiles(inicio, 10) == date(2026, 1, 7)


def test_sumar_dias_habiles_rechaza_n_negativo():
    import pytest

    with pytest.raises(ValueError):
        CalendarUtils.sumar_dias_habiles(date(2026, 1, 13), -1)


def test_dias_habiles_entre_no_cuenta_fecha_inicio():
    lunes = date(2026, 1, 13)
    martes = date(2026, 1, 14)
    assert CalendarUtils.dias_habiles_entre(lunes, martes) == 1
    assert CalendarUtils.dias_habiles_entre(lunes, lunes) == 0


def test_dias_habiles_entre_es_inverso_de_sumar_dias_habiles():
    inicio = date(2025, 12, 22)
    fin = CalendarUtils.sumar_dias_habiles(inicio, 10)
    assert CalendarUtils.dias_habiles_entre(inicio, fin) == 10


def test_dias_habiles_entre_rechaza_fin_anterior_a_inicio():
    import pytest

    with pytest.raises(ValueError):
        CalendarUtils.dias_habiles_entre(date(2026, 1, 14), date(2026, 1, 13))


def test_notificacion_surtida_el_cruza_festivo():
    # Verificado independientemente: envío el miércoles 2025-12-24. El primer
    # día hábil siguiente es viernes 2025-12-26 (jueves 25 es Navidad); el
    # segundo es lunes 2025-12-29 (fin de semana 27-28 no cuenta).
    envio = date(2025, 12, 24)
    assert CalendarUtils.notificacion_surtida_el(envio) == date(2025, 12, 29)


def test_vencimiento_calendario_desborde_fin_de_mes():
    # 30 de enero + 1 mes: febrero de 2025 (no bisiesto) solo tiene 28 días.
    # El 28 de febrero de 2025 es viernes hábil, no requiere corrimiento.
    inicio = date(2025, 1, 30)
    assert CalendarUtils.vencimiento_calendario(inicio, 1) == date(2025, 2, 28)


def test_vencimiento_calendario_corre_a_dia_habil_por_fin_de_semana():
    # 28 de febrero de 2026 + 1 mes -> 28 de marzo de 2026, que es sábado.
    # Corre al siguiente hábil: domingo 29 también inhábil, lunes 30 sí.
    inicio = date(2026, 2, 28)
    assert CalendarUtils.vencimiento_calendario(inicio, 1) == date(2026, 3, 30)


def test_vencimiento_calendario_corre_a_dia_habil_por_festivo():
    # 1 de abril de 2026 + 1 mes -> 1 de mayo de 2026 (Día del Trabajo,
    # viernes, festivo). Corre al siguiente hábil: fin de semana 2-3 mayo
    # inhábil, lunes 4 de mayo sí.
    inicio = date(2026, 4, 1)
    assert CalendarUtils.vencimiento_calendario(inicio, 1) == date(2026, 5, 4)


def test_vencimiento_calendario_rechaza_meses_menor_a_uno():
    import pytest

    with pytest.raises(ValueError):
        CalendarUtils.vencimiento_calendario(date(2026, 1, 1), 0)
