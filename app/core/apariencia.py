from pathlib import Path

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

from app.assets.fonts import cargar_fuentes_ancizar_sans
from app.core import theme_colors as colores

_THEME_QSS_PATH = Path(__file__).resolve().parents[2] / "resources" / "theme.qss"


def construir_paleta() -> QPalette:
    """QPalette base de BASTIUM (Sprint 31): fija los colores nativos de Qt
    (fondo de ventana, texto, campos de entrada, seleccion) a partir de
    `app.core.theme_colors`. `resources/theme.qss` se aplica encima para
    spacing/bordes/estados hover-pressed-disabled que QPalette no cubre.
    """
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


def aplicar_tema(app: QApplication) -> str:
    """Aplica el sistema de diseño visual de BASTIUM (Sprint 31) a `app`:
    registra AncizarSans y la fija como fuente por defecto, aplica la
    QPalette de marca y carga `resources/theme.qss` encima. Devuelve el
    nombre de familia de fuente registrado.
    """
    familia = cargar_fuentes_ancizar_sans()
    app.setFont(QFont(familia, 10))
    app.setPalette(construir_paleta())
    app.setStyleSheet(_THEME_QSS_PATH.read_text(encoding="utf-8"))
    return familia
