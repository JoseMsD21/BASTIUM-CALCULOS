from pathlib import Path

from PySide6.QtGui import QFontDatabase

FAMILIA_ANCIZAR_SANS = "Ancizar Sans"

_FONTS_DIR = Path(__file__).resolve().parent / "fonts"
_ARCHIVOS_ANCIZAR_SANS = (
    "AncizarSans-Regular.ttf",
    "AncizarSans-Medium.ttf",
    "AncizarSans-ExtraBold.ttf",
)


def cargar_fuentes_ancizar_sans() -> str:
    """Registra los 3 pesos de AncizarSans en QFontDatabase (Sprint 31).

    Debe llamarse despues de crear la QApplication (QFontDatabase necesita una
    QApplication/QGuiApplication activa). Devuelve el nombre de familia que Qt
    reporto al leer los metadatos internos de los .ttf -- confirmado como
    "Ancizar Sans" para los 3 archivos al escribir este sprint, pero se
    devuelve el valor real en vez de asumirlo, por si algun peso declarara un
    nombre de familia distinto.
    """
    nombre_familia = None
    for nombre_archivo in _ARCHIVOS_ANCIZAR_SANS:
        ruta = _FONTS_DIR / nombre_archivo
        id_fuente = QFontDatabase.addApplicationFont(str(ruta))
        if id_fuente == -1:
            raise RuntimeError(f"No se pudo cargar la fuente {nombre_archivo} desde {ruta}")
        familias = QFontDatabase.applicationFontFamilies(id_fuente)
        if familias:
            nombre_familia = familias[0]

    if nombre_familia is None:
        raise RuntimeError("No se registro ninguna familia de AncizarSans")
    return nombre_familia
