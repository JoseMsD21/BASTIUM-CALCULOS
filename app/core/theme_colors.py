"""Paleta de color de marca BASTIUM (Sprint 31).

Fuente unica de verdad para los colores en codigo Python (ej. series de un
grafico de matplotlib en el dashboard del Sprint 33). `resources/theme.qss`
usa estos mismos valores hardcodeados en el stylesheet -- Qt QSS no soporta
variables ni importar constantes de Python, asi que si un valor cambia aqui
hay que actualizar tambien el .qss a mano (ver el comentario al inicio de ese
archivo).

PRIMARIO y SECUNDARIO ya se usaban en `app/reports/pdf.py` (`c_burgundy` /
`c_cream`) para las tablas del PDF antes de este sprint; el resto de la
paleta se deriva de esos dos colores de ancla.
"""

PRIMARIO = "#AE1C21"
PRIMARIO_HOVER = "#931116"
PRIMARIO_PRESSED = "#7A0D12"
PRIMARIO_DISABLED = "#D9A8AA"

SECUNDARIO = "#F5F1E9"
SECUNDARIO_HOVER = "#ECE4D4"
SECUNDARIO_PRESSED = "#E0D5BD"
SECUNDARIO_BORDE = "#D8CDBB"

DESTRUCTIVO = "#D32F2F"
DESTRUCTIVO_HOVER = "#B71C1C"
DESTRUCTIVO_PRESSED = "#961515"
DESTRUCTIVO_DISABLED = "#E8B4B0"

EXITO = "#2E7D32"
EXITO_HOVER = "#256628"
ADVERTENCIA = "#ED6C02"
ERROR = DESTRUCTIVO

FONDO = "#FAF8F4"
SUPERFICIE = "#FFFFFF"
SUPERFICIE_ALTERNA = "#F5F1E9"
BORDE = "#D8CDBB"

TEXTO_PRIMARIO = "#2B2320"
TEXTO_SECUNDARIO = "#6B5F57"
TEXTO_SOBRE_PRIMARIO = "#F5F1E9"
TEXTO_DESHABILITADO = "#A69C92"
