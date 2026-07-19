from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from app.engine.indexation.historical_index import get_ibc_usura_for_date
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.engine.math.rounding import Rounding


@dataclass(frozen=True)
class MoratoryIndemnityResult:
    dias_retardo: int
    dias_fase1: int
    monto_fase1: Decimal
    dias_fase2: int
    monto_fase2: Decimal
    total: Decimal


class MoratoryIndemnityCalculator:
    """
    Indemnizacion moratoria del Art. 65 CST ("salarios caidos"), regimen
    bifasico:
      - Fase 1 (dia 1 a 720, 24 meses): un dia de salario por cada dia de
        retardo.
      - Fase 2 (dia 721 en adelante): cesa el dia de salario; corren
        intereses moratorios a la tasa maxima legal (SFC, tasa de usura)
        sobre los salarios y cesantias adeudadas.
    Verificado contra REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf,
    paginas 51 y 3427-3433.
    """

    LIMITE_FASE1_DIAS = 720

    @staticmethod
    def calcular(
        salario_mensual: Decimal,
        monto_adeudado: Decimal,
        fecha_terminacion: date,
        fecha_pago_o_corte: date,
    ) -> "MoratoryIndemnityResult":
        dias_retardo = (fecha_pago_o_corte - fecha_terminacion).days
        if dias_retardo <= 0:
            return MoratoryIndemnityResult(
                dias_retardo=0,
                dias_fase1=0,
                monto_fase1=Decimal("0.00"),
                dias_fase2=0,
                monto_fase2=Decimal("0.00"),
                total=Decimal("0.00"),
            )

        dias_fase1 = min(dias_retardo, MoratoryIndemnityCalculator.LIMITE_FASE1_DIAS)
        salario_diario = salario_mensual / Decimal("30")
        monto_fase1 = Rounding.money(salario_diario * Decimal(str(dias_fase1)))

        dias_fase2 = max(dias_retardo - MoratoryIndemnityCalculator.LIMITE_FASE1_DIAS, 0)
        monto_fase2 = Decimal("0.00")
        if dias_fase2 > 0:
            primer_dia_fase2 = fecha_terminacion + timedelta(
                days=MoratoryIndemnityCalculator.LIMITE_FASE1_DIAS + 1
            )
            for offset in range(dias_fase2):
                dia = primer_dia_fase2 + timedelta(days=offset)
                _, usura_anual = get_ibc_usura_for_date(dia)
                tasa_diaria = EffectiveRateConverter.annual_to_daily(usura_anual)
                monto_fase2 += DailyInterest.calculate(monto_adeudado, tasa_diaria, 1)

        return MoratoryIndemnityResult(
            dias_retardo=dias_retardo,
            dias_fase1=dias_fase1,
            monto_fase1=monto_fase1,
            dias_fase2=dias_fase2,
            monto_fase2=monto_fase2,
            total=monto_fase1 + monto_fase2,
        )
