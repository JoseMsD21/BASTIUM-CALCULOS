"""
Configuración global de precisión decimal para LEXIA.

Este módulo define la política oficial de precisión y redondeo
utilizada por todo el Motor Matemático Universal.

NUNCA utilizar float para cálculos financieros.

Autor:
Proyecto LEXIA
"""

from decimal import getcontext
from decimal import ROUND_HALF_UP

# Precisión interna alta para evitar errores acumulativos.
getcontext().prec = 28

# Redondeo oficial.
getcontext().rounding = ROUND_HALF_UP