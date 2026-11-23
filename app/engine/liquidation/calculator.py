from datetime import date
from decimal import Decimal

from app.engine.math.rounding import Rounding


class FamilyLawCalculator:
    """Motor de cálculo para obligaciones de familia (Alimentos, Salud, Educación).

    Auditoría 2026-11-12 (código sin consumidores en `app/`, conservado por compatibilidad):
    - La constante anterior `0.000159653587` era la tasa EFECTIVA compuesta diaria
      ((1,06)^(1/365) - 1) mientras el comentario decía "0.06 / 365" (lineal) -- dos
      convenciones distintas y contradictorias en la misma línea. Se alinea con lo que sí
      usa el motor en producción (`LegalRates.get_civil_daily_rate`): lineal 6 % / 365.
    - Usaba `round(Decimal, 2)` (redondeo bancario, ROUND_HALF_EVEN) en vez de la política
      oficial ROUND_HALF_UP (`Rounding.money`).
    """

    def __init__(self):
        # Art. 1617 C.C.: 6 % anual, lineal, base 365. Sin cuantizar la tasa.
        self.tasa_diaria = Decimal("0.06") / Decimal("365")

    def calcular_dias_mora(self, fecha_exigibilidad: date, fecha_corte: date) -> int:
        delta = fecha_corte - fecha_exigibilidad
        return max(0, delta.days)

    def procesar_rubro(
        self, concepto: str, capital: Decimal, fecha_exigibilidad: date, fecha_corte: date
    ) -> dict:
        dias_mora = self.calcular_dias_mora(fecha_exigibilidad, fecha_corte)

        # Intereses = Capital * Tasa Diaria * Días, redondeado UNA vez a centavos.
        interes_generado = Rounding.money(capital * self.tasa_diaria * Decimal(dias_mora))

        return {
            "concepto": concepto,
            "capital": capital,
            "dias_mora": dias_mora,
            "intereses": interes_generado,
            "total_rubro": Rounding.money(capital + interes_generado),
        }
