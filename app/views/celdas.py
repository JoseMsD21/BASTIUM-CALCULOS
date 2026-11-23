"""Celdas de tabla compartidas por las pantallas (Sprint 127).

Guía de identidad (`docs/identidad/GUIA_DE_IDENTIDAD.md`, "Tipografía"): las cifras
se alinean a la derecha para que se lean en columna, "como en un reloj suizo", y la
auditoría visual sea inmediata. El texto de la celda no cambia (mismo `str(valor)`
de antes), solo su alineación.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem

from app.core.constants import AREAS_DERECHO

ALINEACION_NUMERO = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

_ETIQUETA_POR_AREA = {codigo: etiqueta for codigo, etiqueta, _habilitada in AREAS_DERECHO}


def celda_numero(valor) -> QTableWidgetItem:
    """Celda para un monto, tasa o cantidad: el texto de siempre, alineado a la
    derecha."""
    celda = QTableWidgetItem(str(valor))
    celda.setTextAlignment(ALINEACION_NUMERO)
    return celda


def etiqueta_area(codigo: str) -> str:
    """Nombre legible del área ("Civil / Familia") para el código guardado en la
    base ("CIVIL_FAMILIA"). Si el código no está en el catálogo, se devuelve tal
    cual para no ocultar el dato."""
    return _ETIQUETA_POR_AREA.get(codigo, codigo)
