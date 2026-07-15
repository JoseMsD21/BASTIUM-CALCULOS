from decimal import Decimal

class LegalRates:
    """
    Catálogo centralizado de tasas por ministerio de la ley.
    El motor consulta aquí, nunca al usuario.
    """
    # Artículo 1617 Código Civil: 6% anual
    CIVIL_ANNUAL_RATE = Decimal("0.06")
    
    @staticmethod
    def get_civil_daily_rate(use_360_days: bool = False) -> Decimal:
        """
        Calcula la tasa diaria simple.
        Por defecto en civil se usa el año calendario (365/366).
        """
        days_in_year = Decimal("360") if use_360_days else Decimal("365")
        # 0.06 / 365 = 0.00016438... (0.0164%)
        return LegalRates.CIVIL_ANNUAL_RATE / days_in_year