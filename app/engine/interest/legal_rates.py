from datetime import date
from decimal import Decimal

from app.services.parametro_service import get_parametro


class LegalRates:
    """
    Catalogo centralizado de tasas por ministerio de la ley.
    El motor consulta aqui, nunca al usuario.
    """
    # Articulo 1617 Codigo Civil: 6% anual -- constante conservada como
    # referencia congelada y fuente de siembra de
    # scripts/migrate_parametros_legales.py; get_civil_daily_rate ya no la lee
    # directamente, consulta parametro_service (clave CIVIL_ANNUAL_RATE).
    CIVIL_ANNUAL_RATE = Decimal("0.06")

    @staticmethod
    def get_civil_daily_rate(fecha: date, use_360_days: bool = False) -> Decimal:
        """
        Calcula la tasa diaria simple a partir de la tasa civil legal vigente
        en `fecha`. Por defecto en civil se usa el año calendario (365/366).
        """
        tasa_anual = get_parametro("CIVIL_ANNUAL_RATE", fecha)
        days_in_year = Decimal("360") if use_360_days else Decimal("365")
        return tasa_anual / days_in_year
