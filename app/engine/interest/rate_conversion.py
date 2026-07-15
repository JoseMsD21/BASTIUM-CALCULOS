from decimal import Decimal

from app.engine.financial.rate import Rate


class EffectiveRateConverter:
    """
    Convierte una tasa efectiva anual (EA, como se certifican las tasas
    legales/comerciales) a la tasa diaria equivalente que consume el motor.

    Formula: i_diario = (1 + i_EA) ** (1/365) - 1
    """

    @staticmethod
    def annual_to_daily(annual_percent: Decimal) -> Rate:
        annual_fraction = Decimal(str(annual_percent)) / Decimal("100")
        daily_fraction = (Decimal("1") + annual_fraction) ** (Decimal("1") / Decimal("365")) - Decimal("1")
        return Rate(daily_fraction)
