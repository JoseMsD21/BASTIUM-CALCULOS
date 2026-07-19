import calendar
from datetime import date, timedelta
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

    @staticmethod
    def sumar_dias_habiles(fecha_inicio: date, n: int) -> date:
        if n < 0:
            raise ValueError("sumar_dias_habiles no admite n negativo")

        fecha = fecha_inicio
        dias_contados = 0
        while dias_contados < n:
            fecha += timedelta(days=1)
            if CalendarUtils.es_dia_habil(fecha):
                dias_contados += 1
        return fecha

    @staticmethod
    def dias_habiles_entre(fecha_inicio: date, fecha_fin: date) -> int:
        if fecha_fin < fecha_inicio:
            raise ValueError("fecha_fin no puede ser anterior a fecha_inicio")

        fecha = fecha_inicio
        dias = 0
        while fecha < fecha_fin:
            fecha += timedelta(days=1)
            if CalendarUtils.es_dia_habil(fecha):
                dias += 1
        return dias
