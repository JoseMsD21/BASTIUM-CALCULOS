from datetime import date
from decimal import Decimal

from app.services.parametro_service import get_parametro

TOPE_MULTIPLICADOR = Decimal("1.5")
# NOTA: constante conservada como referencia congelada (Ley 45/1990, art. 72) y
# como fuente de siembra de scripts/migrate_parametros_legales.py -- ya no la
# lee calcular_tope_usura, que consulta el valor vigente por fecha via
# parametro_service (clave USURA_MULTIPLICADOR).


def calcular_tope_usura(ibc_vigente: Decimal, fecha: date) -> Decimal:
    """Tope legal de usura vigente en `fecha` (parametro USURA_MULTIPLICADOR, Ley
    45/1990 art. 72) x ibc_vigente.

    No lanza ni rechaza nada: la respuesta del despacho
    (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 2) fue explicita en que
    superar este tope no se rechaza ni se recorta
    silenciosamente -- la sancion es la perdida del exceso cobrado, doblado, a favor
    del deudor (ver ComercialStrategy._calcular_sancion_usura). Esta funcion solo
    calcula el tope; quien la llama decide que hacer con la comparacion.
    """
    multiplicador = get_parametro("USURA_MULTIPLICADOR", fecha)
    return ibc_vigente * multiplicador
