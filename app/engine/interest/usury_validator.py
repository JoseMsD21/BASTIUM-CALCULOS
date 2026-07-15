from decimal import Decimal

from app.core.exceptions import TasaUsurariaError

TOPE_MULTIPLICADOR = Decimal("1.5")


def validar_tasa_usura(tasa_pactada: Decimal, ibc_vigente: Decimal, etiqueta: str) -> None:
    """Lanza TasaUsurariaError si tasa_pactada supera 1.5 x ibc_vigente (Ley 45/1990, art. 72)."""
    tope = ibc_vigente * TOPE_MULTIPLICADOR
    if tasa_pactada > tope:
        exceso = tasa_pactada - tope
        raise TasaUsurariaError(
            f"La tasa {etiqueta} pactada ({tasa_pactada}%) supera el tope de usura "
            f"(1.5 x IBC = {tope}%) por {exceso} puntos porcentuales."
        )
