from datetime import date
from decimal import Decimal

from app.engine.currency.trm_provider import TRMProvider
from app.engine.math.rounding import Rounding


def convertir_a_pesos(
    valor: Decimal,
    moneda: str | None,
    provider: TRMProvider | None,
    fecha_referencia: date,
) -> Decimal:
    """
    Convierte `valor` a pesos colombianos segun `moneda`. Si `moneda` es "COP"
    o None (obligaciones sin moneda extranjera explicita), retorna `valor` sin
    tocar y sin requerir provider. Para cualquier otra moneda, requiere un
    TRMProvider -- Art. 874 C.Co. permite elegir entre la TRM de la fecha de la
    obligacion o la del pago; cual de las dos se usa es una decision del
    abogado (reflejada en `fecha_referencia`), no de esta funcion.
    """
    if moneda is None or moneda == "COP":
        return valor
    if provider is None:
        raise ValueError(f"Una obligacion en {moneda} requiere una TRM aplicable para convertir a pesos.")
    return Rounding.money(valor * provider.get_trm(fecha_referencia))
