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
    @lru_cache(maxsize=None)
    def _jueves_santo(anio: int) -> date:
        for fecha, nombre in holidays.CO(years=anio).items():
            if "Jueves Santo" in nombre:
                return fecha
        raise ValueError(
            f"La libreria 'holidays' no trajo 'Jueves Santo' para el año {anio} -- no se puede "
            "derivar la vacancia de Semana Santa sin esa fecha ancla."
        )

    @staticmethod
    @lru_cache(maxsize=None)
    def _vacancia_semana_santa(anio: int) -> frozenset:
        # Lunes, Martes y Miercoles Santo (Jueves y Viernes Santo ya son festivos
        # oficiales, cubiertos por _festivos_colombia). Respuesta del despacho,
        # Preguntas-Para-Abogado.md Sprint 6: excluir los tres dias adicionales.
        jueves_santo = CalendarUtils._jueves_santo(anio)
        return frozenset(
            jueves_santo - timedelta(days=dias) for dias in (1, 2, 3)
        )

    @staticmethod
    def _en_vacancia_judicial_fin_de_anio(fecha: date) -> bool:
        # Respuesta del despacho, Preguntas-Para-Abogado.md Sprint 6: 20 de
        # diciembre a 11 de enero de cada año, inclusive. El 12 de enero es
        # habil salvo que caiga en fin de semana/festivo -- no requiere caso
        # especial, ya que simplemente queda fuera de este rango y se evalua
        # por las reglas normales.
        return (fecha.month == 12 and fecha.day >= 20) or (fecha.month == 1 and fecha.day <= 11)

    @staticmethod
    def es_dia_habil(fecha: date) -> bool:
        if fecha.weekday() >= 5:  # 5=sábado, 6=domingo
            return False
        if fecha in CalendarUtils._festivos_colombia(fecha.year):
            return False
        if CalendarUtils._en_vacancia_judicial_fin_de_anio(fecha):
            return False
        return fecha not in CalendarUtils._vacancia_semana_santa(fecha.year)

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

    @staticmethod
    def notificacion_surtida_el(fecha_envio: date) -> date:
        # Regla pág. 4 del PDF: la notificación digital se entiende surtida
        # 2 días hábiles después del envío.
        return CalendarUtils.sumar_dias_habiles(fecha_envio, 2)

    @staticmethod
    def vencimiento_calendario(fecha_inicio: date, meses: int) -> date:
        if meses < 1:
            raise ValueError("meses debe ser al menos 1")

        total_meses = fecha_inicio.month - 1 + meses
        anio_destino = fecha_inicio.year + total_meses // 12
        mes_destino = total_meses % 12 + 1

        fecha_objetivo = CalendarUtils.safe_create_date(
            anio_destino, mes_destino, fecha_inicio.day
        )

        while not CalendarUtils.es_dia_habil(fecha_objetivo):
            fecha_objetivo += timedelta(days=1)

        return fecha_objetivo
