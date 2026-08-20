from decimal import Decimal

from app.engine.financial.rate import Rate


class EffectiveRateConverter:
    """
    Convierte una tasa efectiva anual (EA, como se certifican las tasas
    legales/comerciales) a una tasa de periodo equivalente que consume el
    motor.

    Formula diaria: i_diario = (1 + i_EA) ** (1/365) - 1

    Formula mensual: i_mensual = (1 + i_EA) ** (1/12) - 1 -- misma familia de
    conversion "efectiva compuesta" que la diaria, pero en base mensual. Es
    la convencion que usan las plantillas i1/i2/i7/i9/i13 del despacho (ej.
    i7.INTERESES-CIVILES-6-ANUAL.md: EA=6% -> tasa mensual "0,49%"), luego
    prorrateada linealmente sobre 30 dias fijos por periodo parcial -- ver
    Sprint 83 en docs/Pendientes.md y la pregunta ampliada del Sprint 76 en
    docs/Preguntas-Para-Abogado-Abiertas.md (Opcion C). Esta conversion NO
    esta conectada todavia a ningun area/calculo real: eso queda condicionado
    a la respuesta del despacho sobre cual de las 3 convenciones (lineal
    diaria, efectiva compuesta diaria, o esta mensual con prorrateo de 30
    dias) debe aplicar.
    """

    @staticmethod
    def annual_to_daily(annual_percent: Decimal) -> Rate:
        annual_fraction = Decimal(str(annual_percent)) / Decimal("100")
        daily_fraction = (Decimal("1") + annual_fraction) ** (
            Decimal("1") / Decimal("365")
        ) - Decimal("1")
        return Rate(daily_fraction)

    @staticmethod
    def annual_to_monthly(annual_percent: Decimal) -> Rate:
        annual_fraction = Decimal(str(annual_percent)) / Decimal("100")
        monthly_fraction = (Decimal("1") + annual_fraction) ** (
            Decimal("1") / Decimal("12")
        ) - Decimal("1")
        return Rate(monthly_fraction)
