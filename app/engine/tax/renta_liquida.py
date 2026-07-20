"""
Depuracion de Renta Liquida Gravable (Impuesto sobre la Renta): pipeline
aritmetico de 8 pasos, sin dependencias de tasas ni de UVT
(REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf, paginas 38-39).

Si la Renta Liquida (paso 6, antes de restar rentas exentas) da negativa, es
perdida liquida: la Renta Liquida Gravable se fija en 0 y no se restan
rentas exentas sobre un numero negativo (decision tomada con el usuario
durante el brainstorming). El mismo tope en 0 aplica si el resultado
quedara negativo despues de restar rentas exentas -- una renta liquida
gravable nunca es negativa en la practica real.

No modela compensacion de perdidas fiscales de anios anteriores (fuera de
alcance, no hay caso de uso que lo requiera en este sprint).

Ver docs/superpowers/specs/2026-07-20-sprint11a-tributario-interes-renta-liquida-design.md.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.engine.math.rounding import Rounding


@dataclass(frozen=True)
class RentaLiquidaGravableResult:
    ingresos_netos: Decimal
    renta_bruta: Decimal
    renta_liquida: Decimal
    hubo_perdida_liquida: bool
    renta_liquida_gravable: Decimal


def depurar_renta_liquida_gravable(
    ingresos_brutos: Decimal,
    devoluciones_rebajas_descuentos: Decimal,
    costos: Decimal,
    deducciones: Decimal,
    rentas_exentas: Decimal,
) -> RentaLiquidaGravableResult:
    ingresos_netos = Rounding.money(ingresos_brutos - devoluciones_rebajas_descuentos)
    renta_bruta = Rounding.money(ingresos_netos - costos)
    renta_liquida = Rounding.money(renta_bruta - deducciones)

    if renta_liquida < Decimal("0.00"):
        return RentaLiquidaGravableResult(
            ingresos_netos=ingresos_netos,
            renta_bruta=renta_bruta,
            renta_liquida=renta_liquida,
            hubo_perdida_liquida=True,
            renta_liquida_gravable=Decimal("0.00"),
        )

    renta_liquida_gravable = Rounding.money(max(Decimal("0.00"), renta_liquida - rentas_exentas))
    return RentaLiquidaGravableResult(
        ingresos_netos=ingresos_netos,
        renta_bruta=renta_bruta,
        renta_liquida=renta_liquida,
        hubo_perdida_liquida=False,
        renta_liquida_gravable=renta_liquida_gravable,
    )
