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
