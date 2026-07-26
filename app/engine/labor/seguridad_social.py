from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.engine.indexation.historical_index import get_smlmv_for_year
from app.engine.math.rounding import Rounding
from app.services.parametro_service import get_parametro


@dataclass(frozen=True)
class CotizacionesResult:
    ibc_mensual: Decimal
    monto_pension: Decimal
    monto_salud: Decimal
    monto_arl: Decimal
    monto_fsp: Decimal
    total: Decimal


class SeguridadSocialCalculator:
    """
    Cotizaciones de seguridad social (pension, salud, ARL, FSP) sobre el IBC
    de un contrato laboral, para reclamarlas como aportes dejados de pagar
    dentro de una liquidacion judicial (PDF pags. 51-52, "Middleware de
    Seguridad Social: Cotizaciones").

    Base de aporte: monto total (empleador + trabajador), no solo la porcion
    del empleador -- decision tomada con el usuario, ver spec del Sprint 16.
    """

    @staticmethod
    def calcular(
        salario_base: Decimal,
        dias_trabajados: int,
        dias_suspension: int,
        nivel_riesgo_arl: str,
        fecha_referencia: date,
    ) -> "CotizacionesResult":
        dias_trab = Decimal(str(dias_trabajados))
        dias_susp = Decimal(str(dias_suspension))

        smmlv = get_smlmv_for_year(fecha_referencia.year)
        ibc = min(max(salario_base, smmlv), smmlv * Decimal("25"))  # PDF pag. 51: 1-25 SMMLV

        monto_pension = Rounding.money(
            ibc * get_parametro("SS_PENSION_PCT", fecha_referencia) * dias_trab / Decimal("30")
        )
        monto_salud = Rounding.money(
            ibc * get_parametro("SS_SALUD_PCT", fecha_referencia) * dias_trab / Decimal("30")
        )

        dias_con_arl = dias_trab - dias_susp  # suspension excluye SOLO ARL (PDF pag. 52)
        arl_pct = get_parametro(f"SS_ARL_NIVEL_{nivel_riesgo_arl}_PCT", fecha_referencia)
        monto_arl = Rounding.money(ibc * arl_pct * dias_con_arl / Decimal("30"))

        monto_fsp = Decimal("0.00")
        if ibc >= smmlv * Decimal("4"):
            fsp_pct = _resolver_tramo_fsp(ibc, smmlv, fecha_referencia)
            monto_fsp = Rounding.money(ibc * fsp_pct * dias_trab / Decimal("30"))

        total = monto_pension + monto_salud + monto_arl + monto_fsp
        return CotizacionesResult(
            ibc_mensual=ibc, monto_pension=monto_pension, monto_salud=monto_salud,
            monto_arl=monto_arl, monto_fsp=monto_fsp, total=total,
        )


def _resolver_tramo_fsp(ibc: Decimal, smmlv: Decimal, fecha: date) -> Decimal:
    # Tramos del Fondo de Solidaridad Pensional, Ley 797/2003 art. 8, en
    # multiplos de SMMLV del IBC (el PDF solo describe "escala progresiva
    # desde 1% hasta 2%", sin tramos exactos -- ver spec del Sprint 16).
    tramos = [
        (Decimal("16"), "SS_FSP_TRAMO_1_PCT"),   # 4  - 16 SMMLV
        (Decimal("17"), "SS_FSP_TRAMO_2_PCT"),   # 16 - 17 SMMLV
        (Decimal("18"), "SS_FSP_TRAMO_3_PCT"),   # 17 - 18 SMMLV
        (Decimal("19"), "SS_FSP_TRAMO_4_PCT"),   # 18 - 19 SMMLV
        (Decimal("20"), "SS_FSP_TRAMO_5_PCT"),   # 19 - 20 SMMLV
    ]
    for limite_superior, clave in tramos:
        if ibc < smmlv * limite_superior:
            return get_parametro(clave, fecha)
    return get_parametro("SS_FSP_TRAMO_6_PCT", fecha)  # > 20 SMMLV
