import calendar
from datetime import date
from functools import lru_cache

import holidays


class CalendarUtils:
    """
    Motor de resolución de anomalías temporales.
    Garantiza que el software nunca colapse por inconsistencias
    en el calendario gregoriano (años bisiestos, meses de 30/31 días)
    y provee el cómputo de días hábiles judiciales colombianos.
    """

    @staticmethod
    def safe_create_date(year: int, month: int, desired_day: int) -> date:
        # Extrae el último día real del mes en ese año específico
        _, last_real_day = calendar.monthrange(year, month)

        # Si el día deseado (ej. 31) excede el día real (ej. 28), se topa al día real.
        actual_day = min(desired_day, last_real_day)

        return date(year, month, actual_day)

    @staticmethod
    @lru_cache(maxsize=None)
    def _festivos_colombia(anio: int) -> frozenset:
        return frozenset(holidays.CO(years=anio).keys())

    @staticmethod
    def es_dia_habil(fecha: date) -> bool:
        if fecha.weekday() >= 5:  # 5=sábado, 6=domingo
            return False
        return fecha not in CalendarUtils._festivos_colombia(fecha.year)
