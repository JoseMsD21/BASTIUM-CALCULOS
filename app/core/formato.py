"""Formato de cifras para mostrar (Sprint 129).

Única fuente del formato de moneda y porcentaje que ven los usuarios, en pantalla y
en los reportes PDF/Word. Hoy: `$1,500,000.00` (coma de miles, punto decimal), el
mismo que usaban los reportes desde el Sprint 9. Si el despacho decide pasar al
formato colombiano (`$1.500.000,00`; Preguntas Abiertas, Sprint 129), se cambia
aquí y lo heredan pantalla, PDF y Word.

El redondeo a 2 decimales es SIEMPRE ROUND_HALF_UP (política oficial del proyecto),
explícito y sin depender del contexto `Decimal` activo: el formateo de Python por sí
solo redondeaba 0.125 a 0.12 (redondeo bancario). Solo es presentación: nunca se usa
para calcular.
"""

from decimal import ROUND_HALF_UP, Decimal

_CENTAVOS = Decimal("0.01")


def _a_decimal(valor) -> Decimal:
    numero = valor if isinstance(valor, Decimal) else Decimal(str(valor))
    return numero.quantize(_CENTAVOS, rounding=ROUND_HALF_UP)


def formatear_moneda(valor) -> str:
    """`Decimal("1500000")` -> `"$1,500,000.00"`."""
    return f"${_a_decimal(valor):,.2f}"


def formatear_porcentaje(valor) -> str:
    """`Decimal("6")` -> `"6.00%"`."""
    return f"{_a_decimal(valor):,.2f}%"
