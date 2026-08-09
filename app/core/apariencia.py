from pathlib import Path

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

from app.assets.fonts import cargar_fuentes_ancizar_sans
from app.core import theme_colors as colores_claro
from app.core import theme_colors_dark as colores_oscuro
from app.core.settings import crear_settings

_RESOURCES_DIR = Path(__file__).resolve().parents[2] / "resources"
_THEME_QSS_PATH = _RESOURCES_DIR / "theme.qss"
_THEME_DARK_QSS_PATH = _RESOURCES_DIR / "theme_dark.qss"

# Modos de tema soportados (Sprint 50). "claro" es el tema original del Sprint 31,
# sin cambios visuales, y sigue siendo el default en toda la API de este modulo.
MODO_CLARO = "claro"
MODO_OSCURO = "oscuro"

_MODULOS_DE_COLOR = {MODO_CLARO: colores_claro, MODO_OSCURO: colores_oscuro}
_RUTAS_QSS = {MODO_CLARO: _THEME_QSS_PATH, MODO_OSCURO: _THEME_DARK_QSS_PATH}

_CLAVE_MODO_TEMA = "apariencia/modo_tema"


def _colores_para(modo: str):
    if modo not in _MODULOS_DE_COLOR:
        raise ValueError(f"Modo de tema invalido: {modo!r}. Validos: {sorted(_MODULOS_DE_COLOR)}")
    return _MODULOS_DE_COLOR[modo]


def construir_paleta(modo: str = MODO_CLARO) -> QPalette:
    """QPalette base de BASTIUM (Sprint 31, parametrizada por `modo` en el Sprint
    50): fija los colores nativos de Qt (fondo de ventana, texto, campos de
    entrada, seleccion) a partir de `app.core.theme_colors` (modo "claro") o
    `app.core.theme_colors_dark` (modo "oscuro"). `resources/theme.qss` o
    `resources/theme_dark.qss` se aplica encima para spacing/bordes/estados
    hover-pressed-disabled que QPalette no cubre.
    """
    colores = _colores_para(modo)
    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, QColor(colores.FONDO))
    paleta.setColor(QPalette.ColorRole.WindowText, QColor(colores.TEXTO_PRIMARIO))
    paleta.setColor(QPalette.ColorRole.Base, QColor(colores.SUPERFICIE))
    paleta.setColor(QPalette.ColorRole.AlternateBase, QColor(colores.SUPERFICIE_ALTERNA))
    paleta.setColor(QPalette.ColorRole.Text, QColor(colores.TEXTO_PRIMARIO))
    paleta.setColor(QPalette.ColorRole.Button, QColor(colores.SECUNDARIO))
    paleta.setColor(QPalette.ColorRole.ButtonText, QColor(colores.PRIMARIO))
    paleta.setColor(QPalette.ColorRole.Highlight, QColor(colores.PRIMARIO))
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor(colores.TEXTO_SOBRE_PRIMARIO))
    paleta.setColor(QPalette.ColorRole.PlaceholderText, QColor(colores.TEXTO_SECUNDARIO))
    paleta.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(colores.TEXTO_DESHABILITADO)
    )
    paleta.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor(colores.TEXTO_DESHABILITADO),
    )
    return paleta


def aplicar_tema(app: QApplication, modo: str = MODO_CLARO) -> str:
    """Aplica el sistema de diseño visual de BASTIUM a `app` en el modo pedido
    ("claro", Sprint 31, default; "oscuro", Sprint 50): registra AncizarSans y
    la fija como fuente por defecto, aplica la QPalette del modo y carga el
    `.qss` correspondiente encima. Devuelve el nombre de familia de fuente
    registrado. Puede llamarse de nuevo con la app ya en ejecucion para
    alternar el tema en caliente, sin reiniciar la app.
    """
    _colores_para(modo)  # valida el modo antes de usarlo
    ruta_qss = _RUTAS_QSS[modo]
    familia = cargar_fuentes_ancizar_sans()
    app.setFont(QFont(familia, 10))
    app.setPalette(construir_paleta(modo))
    app.setStyleSheet(ruta_qss.read_text(encoding="utf-8"))
    return familia


def guardar_modo_tema(modo: str) -> None:
    """Persiste el modo de tema elegido via QSettings (Sprint 50), reutilizando
    el mismo patron de `MainWindow._crear_settings()` (Sprint 37) a traves de
    `app.core.settings.crear_settings()` -- no se duplica esa logica aqui."""
    _colores_para(modo)  # valida el modo antes de persistirlo
    settings = crear_settings()
    settings.setValue(_CLAVE_MODO_TEMA, modo)


def cargar_modo_tema() -> str:
    """Modo de tema persistido, con fallback a "claro" en el primer arranque
    (sin QSettings previo) o si el valor guardado no es reconocido."""
    settings = crear_settings()
    modo = settings.value(_CLAVE_MODO_TEMA, MODO_CLARO)
    return modo if modo in _MODULOS_DE_COLOR else MODO_CLARO
