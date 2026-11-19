from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from app.engine.indexation.historical_index import (
    get_ibc_usura_for_date,
    get_ultima_fecha_certificada_ibc_usura,
)
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
    # Sprint 110: dias de fase 2 posteriores al ultimo tramo de usura
    # certificado (no causan interes) y ese ultimo dia certificado -- None/0
    # cuando toda la fase 2 tiene tasa certificada.
    dias_fase2_pendientes_certificacion: int = 0
    ultima_fecha_usura_certificada: date | None = None


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

    Sprint 110 (respuesta del despacho, 26/08/2026: "NUNCA extrapolar. Opcion
    (b)"): la fase 2 solo causa interes hasta el ultimo dia con tasa de usura
    certificada (get_ultima_fecha_certificada_ibc_usura). Los dias posteriores
    se cuentan en `dias_fase2` (son retardo real) pero no suman nada a
    `monto_fase2`; se reportan en `dias_fase2_pendientes_certificacion` para
    que el llamador (LaboralStrategy) emita la alerta "Pendiente de
    Certificación Oficial". La fase 1 (dia de salario) no depende de la usura
    y se liquida completa siempre.
    """

    LIMITE_FASE1_DIAS = 720

    @staticmethod
    def calcular(
        salario_mensual: Decimal,
        monto_adeudado: Decimal,
        fecha_terminacion: date,
        fecha_pago_o_corte: date,
    ) -> MoratoryIndemnityResult:
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
        dias_pendientes = 0
        ultima_certificada = None
        if dias_fase2 > 0:
            primer_dia_fase2 = fecha_terminacion + timedelta(
                days=MoratoryIndemnityCalculator.LIMITE_FASE1_DIAS + 1
            )
            ultima_certificada = get_ultima_fecha_certificada_ibc_usura()
            for offset in range(dias_fase2):
                dia = primer_dia_fase2 + timedelta(days=offset)
                if ultima_certificada is not None and dia > ultima_certificada:
                    dias_pendientes = dias_fase2 - offset
                    break
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
            dias_fase2_pendientes_certificacion=dias_pendientes,
            ultima_fecha_usura_certificada=ultima_certificada if dias_pendientes else None,
        )
