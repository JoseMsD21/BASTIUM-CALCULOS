from dataclasses import dataclass
from decimal import Decimal

from app.engine.math.rounding import Rounding
from database.models import TipoEventoLaboral


@dataclass(frozen=True)
class TramoIncapacidad:
    dias: int
    pagador: str  # "EMPLEADOR" | "EPS" | "ARL"
    porcentaje: Decimal
    monto: Decimal


@dataclass(frozen=True)
class IncapacidadResult:
    tramos: list[TramoIncapacidad]
    monto_a_cargo_empleador: Decimal


class IncapacidadCalculator:
    """
    Desglose de pagadores de una incapacidad (PDF pag. 52, "4. Manejo de
    Eventos y Estados"):
      - Incapacidad comun: dias 1-2 empleador 66.67%, dias 3-90 EPS 66.67%,
        dias 91-180 EPS 50%.
      - Incapacidad laboral: ARL paga 100% desde el dia 1.

    Retorna el desglose COMPLETO de todos los pagadores (informativo, para
    auditoria del juez) pero solo `monto_a_cargo_empleador` es deuda real del
    expediente -- lo que paga la EPS o la ARL no es un hecho reclamable en
    este alcance (decision tomada con el usuario, ver spec del Sprint 16).
    """

    @staticmethod
    def calcular(
        tipo: TipoEventoLaboral, ibc_mensual: Decimal, dias_incapacidad: int
    ) -> "IncapacidadResult":
        ibc_diario = ibc_mensual / Decimal("30")

        if tipo == TipoEventoLaboral.INCAPACIDAD_LABORAL:
            if dias_incapacidad > 0:
                monto = Rounding.money(ibc_diario * dias_incapacidad)
                tramo = TramoIncapacidad(dias_incapacidad, "ARL", Decimal("1.00"), monto)
                return IncapacidadResult([tramo], Decimal("0.00"))
            return IncapacidadResult([], Decimal("0.00"))

        tramos = []
        dias_1_2 = min(dias_incapacidad, 2)
        if dias_1_2 > 0:
            monto = Rounding.money(ibc_diario * Decimal("0.6667") * dias_1_2)
            tramos.append(TramoIncapacidad(dias_1_2, "EMPLEADOR", Decimal("0.6667"), monto))

        dias_3_90 = max(0, min(dias_incapacidad, 90) - 2)
        if dias_3_90 > 0:
            monto = Rounding.money(ibc_diario * Decimal("0.6667") * dias_3_90)
            tramos.append(TramoIncapacidad(dias_3_90, "EPS", Decimal("0.6667"), monto))

        dias_91_180 = max(0, min(dias_incapacidad, 180) - 90)
        if dias_91_180 > 0:
            monto = Rounding.money(ibc_diario * Decimal("0.50") * dias_91_180)
            tramos.append(TramoIncapacidad(dias_91_180, "EPS", Decimal("0.50"), monto))

        monto_empleador = next(
            (t.monto for t in tramos if t.pagador == "EMPLEADOR"), Decimal("0.00")
        )
        return IncapacidadResult(tramos, monto_empleador)
