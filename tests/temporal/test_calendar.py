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
    # San José (19 de marzo) se traslada por Ley Emiliani al lunes siguiente,
    # 23 de marzo de 2026. La fecha real del festivo (jueves 19) queda hábil;
    # la fecha observada (lunes 23) queda inhábil. (No se usa Reyes Magos/6 de
    # enero como ejemplo porque esa fecha cae siempre dentro de la vacancia
    # judicial de fin de año, Sprint 6 -- quedaría inhábil por esa razón
    # también, sin aislar el efecto de la Ley Emiliani.)
    assert CalendarUtils.es_dia_habil(date(2026, 3, 19)) is True
    assert CalendarUtils.es_dia_habil(date(2026, 3, 23)) is False


def test_es_dia_habil_vacancia_judicial_fin_de_anio():
    # Respuesta del despacho (Preguntas-Para-Abogado.md, Sprint 6): vacancia
    # judicial del 20 de diciembre al 11 de enero, inclusive.
    assert CalendarUtils.es_dia_habil(date(2025, 12, 19)) is True  # víspera, aún hábil
    assert CalendarUtils.es_dia_habil(date(2025, 12, 20)) is False  # primer día de vacancia
    assert CalendarUtils.es_dia_habil(date(2026, 1, 11)) is False  # último día de vacancia
    assert CalendarUtils.es_dia_habil(date(2026, 1, 13)) is True  # ya fuera de vacancia y sin festivo


def test_es_dia_habil_12_de_enero_habil_salvo_que_caiga_festivo_o_fin_de_semana():
    # El despacho es explícito: "El 12 de enero es hábil (salvo que caiga fin de
    # semana/festivo)". En 2026 cae festivo (Reyes Magos observado, Ley
    # Emiliani) por pura coincidencia de calendario, no por la vacancia -- en un
    # año donde el 12 de enero no sea festivo ni fin de semana, debe ser hábil.
    # 2033-01-12 es miércoles y no es festivo (verificado con la libreria
    # holidays: cuando el 12 de enero cae lunes, SIEMPRE coincide con Reyes
    # Magos observado, porque el 6 de enero cae martes esa misma semana).
    assert CalendarUtils.es_dia_habil(date(2033, 1, 12)) is True


def test_es_dia_habil_semana_santa_extendida():
    # Respuesta del despacho (Sprint 6): excluir también Lunes, Martes y
    # Miércoles Santo, además de Jueves/Viernes Santo (ya festivos). Semana
    # Santa 2026: Jueves Santo = 2026-04-02.
    assert CalendarUtils.es_dia_habil(date(2026, 3, 30)) is False  # Lunes Santo
    assert CalendarUtils.es_dia_habil(date(2026, 3, 31)) is False  # Martes Santo
    assert CalendarUtils.es_dia_habil(date(2026, 4, 1)) is False  # Miércoles Santo
    assert CalendarUtils.es_dia_habil(date(2026, 4, 2)) is False  # Jueves Santo (ya festivo)
    assert CalendarUtils.es_dia_habil(date(2026, 4, 3)) is False  # Viernes Santo (ya festivo)
    assert CalendarUtils.es_dia_habil(date(2026, 3, 16)) is True  # lunes anterior, fuera de semana santa


def test_sumar_dias_habiles_no_cuenta_fecha_inicio():
    # fecha_inicio es lunes hábil, sin festivos cerca. sumar 1 día hábil debe
    # devolver el martes, NUNCA el mismo lunes (fecha_inicio no cuenta como día 1).
    lunes = date(2026, 1, 13)
    assert CalendarUtils.sumar_dias_habiles(lunes, 1) == date(2026, 1, 14)


def test_sumar_dias_habiles_cruza_fin_de_semana_y_festivo():
    # Verificado independientemente (script standalone con la libreria holidays,
    # sin reusar CalendarUtils): 10 días hábiles desde el lunes 2025-12-22 (sin
    # contar ese día) caen en lunes 2026-01-26. Todo el rango 2025-12-23 a
    # 2026-01-11 queda inhábil por la vacancia judicial de fin de año (Sprint 6,
    # Preguntas-Para-Abogado.md), y 2026-01-12 tambien es inhábil (Reyes Magos
    # observado, Ley Emiliani) -- el primer día hábil real es 2026-01-13.
    inicio = date(2025, 12, 22)
    assert CalendarUtils.sumar_dias_habiles(inicio, 10) == date(2026, 1, 26)


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
    # Verificado independientemente: envío el miércoles 2025-12-24, dentro de la
    # vacancia judicial de fin de año (20 dic - 11 ene, Sprint 6). Todo lo que
    # sigue hasta 2026-01-11 queda inhábil, y 2026-01-12 también (Reyes Magos
    # observado, Ley Emiliani) -- el primer día hábil real es 2026-01-13, el
    # segundo 2026-01-14.
    envio = date(2025, 12, 24)
    assert CalendarUtils.notificacion_surtida_el(envio) == date(2026, 1, 14)


def test_vencimiento_calendario_desborde_fin_de_mes():
    # 30 de enero + 1 mes: febrero de 2025 (no bisiesto) solo tiene 28 días.
    # El 28 de febrero de 2025 es viernes hábil, no requiere corrimiento.
    inicio = date(2025, 1, 30)
    assert CalendarUtils.vencimiento_calendario(inicio, 1) == date(2025, 2, 28)


def test_vencimiento_calendario_corre_a_dia_habil_por_fin_de_semana():
    # 28 de febrero de 2026 + 1 mes -> 28 de marzo de 2026, que es sábado. El
    # lunes 30 (antes el primer hábil) ahora es Lunes Santo, martes 31 Martes
    # Santo, miércoles 1 de abril Miércoles Santo (Sprint 6: los tres quedan
    # inhábiles), jueves 2 y viernes 3 ya eran festivos (Jueves/Viernes Santo),
    # y el fin de semana 4-5 tampoco cuenta -- el primer hábil real es
    # lunes 2026-04-06.
    inicio = date(2026, 2, 28)
    assert CalendarUtils.vencimiento_calendario(inicio, 1) == date(2026, 4, 6)


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


def test_dias_comerciales_360_mismo_dia_cuenta_como_1():
    dia = date(2025, 6, 10)
    assert CalendarUtils.dias_comerciales_360(dia, dia) == 1


def test_dias_comerciales_360_un_ano_completo_da_360_dias():
    # Contrato de un año calendario completo (2020, bisiesto): bajo la
    # premisa comercial de meses de 30 días, el 31 de diciembre se topa a
    # "día 30" -- un año completo da exactamente 360 días comerciales
    # (12 meses x 30 días), no 365/366 días reales. Verificado también
    # ejecutando el código real antes de escribir este plan.
    assert CalendarUtils.dias_comerciales_360(date(2020, 1, 1), date(2020, 12, 31)) == 360


def test_dias_comerciales_360_topa_dia_31_a_30():
    # Enero completo (31 días reales) cuenta como 30 días comerciales: el
    # día 31 se topa a "día 30" del mes de 30 días.
    assert CalendarUtils.dias_comerciales_360(date(2025, 1, 1), date(2025, 1, 31)) == 30


def test_dias_comerciales_360_febrero_bisiesto_no_se_topa():
    # Febrero de un año bisiesto (2024, 29 días reales) no excede 30 -- no
    # hay topeo, cuenta sus 29 días reales + 1 (inclusivo) = 29. Confirma
    # que el topeo a 30 solo actúa sobre el día 31, no sobre meses cortos.
    assert CalendarUtils.dias_comerciales_360(date(2024, 2, 1), date(2024, 2, 29)) == 29


def test_dias_comerciales_360_periodo_parcial_cinco_meses():
    # 2024-01-01 a 2024-06-01: 5 meses completos bajo la premisa comercial
    # (5 x 30 = 150 días) + 1 (inclusivo) = 151. Verificado también
    # ejecutando el código real antes de escribir este plan.
    assert CalendarUtils.dias_comerciales_360(date(2024, 1, 1), date(2024, 6, 1)) == 151


def test_dias_comerciales_360_rechaza_fin_anterior_a_inicio():
    import pytest

    with pytest.raises(ValueError):
        CalendarUtils.dias_comerciales_360(date(2025, 1, 2), date(2025, 1, 1))
