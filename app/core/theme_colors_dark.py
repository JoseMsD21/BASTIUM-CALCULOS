"""Paleta de color de marca BASTIUM -- modo oscuro (Sprint 50).

Mismos nombres de constante que `theme_colors.py` (modo claro, Sprint 31) con la
luminancia invertida: fondos oscuros, texto claro, y la misma familia de acento
burdeos ajustada para contraste sobre fondo oscuro (no se reinventa la identidad
de marca, solo se aclara el burdeos/rojo/verde/naranja lo suficiente para que
sigan siendo legibles sobre `FONDO`/`SUPERFICIE` oscuros).

`resources/theme_dark.qss` usa estos mismos valores hardcodeados en el
stylesheet -- igual que con `theme_colors.py`/`resources/theme.qss`, Qt QSS no
soporta variables ni importar constantes de Python, asi que si un valor cambia
aqui hay que actualizar tambien `theme_dark.qss` a mano.
"""

PRIMARIO = "#D9484D"
PRIMARIO_HOVER = "#C93338"
PRIMARIO_PRESSED = "#AE1C21"
PRIMARIO_DISABLED = "#5C3234"

SECUNDARIO = "#332C29"
SECUNDARIO_HOVER = "#3D3532"
SECUNDARIO_PRESSED = "#463C38"
SECUNDARIO_BORDE = "#4A4039"

DESTRUCTIVO = "#E57373"
DESTRUCTIVO_HOVER = "#EF5350"
DESTRUCTIVO_PRESSED = "#D32F2F"
DESTRUCTIVO_DISABLED = "#5C3B3B"

EXITO = "#66BB6A"
EXITO_HOVER = "#4CAF50"
ADVERTENCIA = "#FFA726"
ERROR = DESTRUCTIVO

FONDO = "#1E1A18"
SUPERFICIE = "#2A2422"
SUPERFICIE_ALTERNA = "#332C29"
BORDE = "#4A4039"

TEXTO_PRIMARIO = "#F5F1E9"
TEXTO_SECUNDARIO = "#C9BFB4"
TEXTO_SOBRE_PRIMARIO = "#F5F1E9"
TEXTO_DESHABILITADO = "#6B5F57"
