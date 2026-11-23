"""Rutas de los logos oficiales de BASTIUM (Sprint 122).

Los archivos viven en `app/assets/marca/` (versiones recortadas y optimizadas
para usar en la app y en los reportes) y los originales tal como los entrego el
equipo, en `app/assets/marca/originales/`. Reglas de uso en
`docs/identidad/GUIA_DE_IDENTIDAD.md`, seccion "Logos".

No depende de Qt ni de reportlab: solo expone rutas y el lema, para que lo
usen igual la GUI (PySide6), el PDF (reportlab) y el Word (python-docx).
"""

from pathlib import Path

DIRECTORIO_MARCA = Path(__file__).resolve().parent / "marca"

LEMA = "La ciencia de resolver lo complejo"

# Logo completo: mascota + "Bastium." + lema. Membrete de PDF/Word.
LOGO_HORIZONTAL = DIRECTORIO_MARCA / "bastium-logo-horizontal.png"
# Solo la mascota (oso con sombrero). Estados vacios / ilustracion.
MASCOTA = DIRECTORIO_MARCA / "bastium-mascota.png"
# Solo la palabra "Bastium" en serif. Portadas y encabezados sin mascota.
WORDMARK = DIRECTORIO_MARCA / "bastium-wordmark.png"
# Monograma "B." con el punto rojo, fondo blanco. Panel lateral de la app.
MONOGRAMA = DIRECTORIO_MARCA / "bastium-monograma.png"
# Monograma con fondo transparente, para fondos que no son blancos.
MONOGRAMA_TRANSPARENTE = DIRECTORIO_MARCA / "bastium-monograma-transparente.png"
# Icono cuadrado de ventana / barra de tareas.
ICONO_APP_PNG = DIRECTORIO_MARCA / "bastium-icono-256.png"
ICONO_APP_ICO = DIRECTORIO_MARCA / "bastium-icono.ico"

TODOS_LOS_LOGOS = (
    LOGO_HORIZONTAL,
    MASCOTA,
    WORDMARK,
    MONOGRAMA,
    MONOGRAMA_TRANSPARENTE,
    ICONO_APP_PNG,
    ICONO_APP_ICO,
)
