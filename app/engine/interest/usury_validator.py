from datetime import date
from decimal import Decimal

from app.core.exceptions import TasaUsurariaError
from app.services.parametro_service import get_parametro

TOPE_MULTIPLICADOR = Decimal("1.5")
# NOTA: constante conservada como referencia congelada (Ley 45/1990, art. 72) y
# como fuente de siembra de scripts/migrate_parametros_legales.py -- ya no la
# lee validar_tasa_usura, que consulta el valor vigente por fecha via
# parametro_service (clave USURA_MULTIPLICADOR).


def validar_tasa_usura(tasa_pactada: Decimal, ibc_vigente: Decimal, etiqueta: str, fecha: date) -> None:
    """Lanza TasaUsurariaError si tasa_pactada supera el multiplicador de usura
    vigente en `fecha` (parametro USURA_MULTIPLICADOR, Ley 45/1990 art. 72) x
    ibc_vigente."""
    multiplicador = get_parametro("USURA_MULTIPLICADOR", fecha)
    tope = ibc_vigente * multiplicador
    if tasa_pactada > tope:
        exceso = tasa_pactada - tope
        raise TasaUsurariaError(
            f"La tasa {etiqueta} pactada ({tasa_pactada}%) supera el tope de usura "
            f"({multiplicador} x IBC = {tope}%) por {exceso} puntos porcentuales."
        )
