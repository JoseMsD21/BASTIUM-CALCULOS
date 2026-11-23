from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

import database.session as session_module
from app.engine.labor.horas_extra import (
    FECHA_INICIO_TRAMO_1_LEY_2466,
    ConceptoHoraExtra,
    factor_hora_extra,
    requiere_porcentaje_manual,
)
from app.views.fecha_widgets import crear_campo_fecha, formatear_fecha
from app.views.form_utils import FormDialogBase, hacer_redimensionable, set_row_visible
from app.views.icons import icon
from database.models import HoraExtraLaboral

ETIQUETAS_CONCEPTO_HORA_EXTRA = {
    ConceptoHoraExtra.HED: "Hora extra diurna (HED)",
    ConceptoHoraExtra.HEN: "Hora extra nocturna (HEN)",
    ConceptoHoraExtra.HEFD: "Hora extra dominical/festiva diurna (HEFD)",
    ConceptoHoraExtra.HEFN: "Hora extra dominical/festiva nocturna (HEFN)",
}


def _decimal_positivo(texto: str, nombre: str) -> Decimal:
    try:
        valor = Decimal(texto.strip())
    except InvalidOperation as error:
        raise ValueError(f"{nombre} debe ser un numero valido.") from error
    if not valor.is_finite() or valor <= Decimal("0"):
        raise ValueError(f"{nombre} debe ser mayor que cero.")
    return valor


def _formatear_factor(factor: Decimal) -> str:
    return f"{factor.normalize():f}".replace(".", ",")


class HoraExtraLaboralFormDialog(FormDialogBase):
    """Horas extra de un contrato Laboral (Sprint 95, conexion a la UI) --
    mismo patron que `DescuentoLaboralFormDialog`: cada fila guardada es un
    `HoraExtraLaboral` hijo de la obligacion, y `LaboralStrategy` la liquida
    como rubro propio con el factor del motor `app/engine/labor/horas_extra.py`
    vigente en la fecha de causacion.

    El valor de la hora ordinaria se digita: el codigo no tiene una conversion
    salario mensual -> valor hora (depende de la jornada maxima vigente, que
    no esta parametrizada).

    HEFD/HEFN causadas antes del 01/07/2025 no tienen factor confirmado por el
    despacho: solo en ese caso aparece el campo "Porcentaje de la hora extra"
    con la explicacion, y es obligatorio. En cualquier otro caso el campo se
    oculta y el porcentaje no se guarda (manda el factor del motor).
    """

    def __init__(self, obligacion_id: int, parent=None):
        super().__init__(parent)
        hacer_redimensionable(self)
        self.setWindowTitle("Agregar horas extra")
        self._obligacion_id = obligacion_id

        self.combo_concepto = QComboBox()
        for concepto, etiqueta in ETIQUETAS_CONCEPTO_HORA_EXTRA.items():
            self.combo_concepto.addItem(etiqueta, userData=concepto.value)

        self.campo_fecha_causacion = crear_campo_fecha()
        self.campo_fecha_causacion.setCalendarPopup(True)
        self.campo_fecha_causacion.setToolTip(
            "Fecha en que se causaron las horas: define el factor de la Ley 2466 de 2025. "
            "Si un periodo cruza un cambio de tramo (1 de julio), registre una fila por tramo."
        )
        self.campo_horas = QLineEdit()
        self.campo_horas.setToolTip("Cantidad de horas extra de este concepto (ej. 10 o 2.5).")
        self.campo_valor_hora = QLineEdit()
        self.campo_valor_hora.setToolTip(
            "Valor de la hora ordinaria de trabajo, sin recargo (ej. 10000)."
        )
        self.etiqueta_factor = QLabel()
        self.etiqueta_factor.setWordWrap(True)
        self.campo_porcentaje_manual = QLineEdit()
        self.campo_porcentaje_manual.setToolTip(
            "Porcentaje de la hora extra festiva (ej. 100 para pagar la hora x 2)."
        )
        self.etiqueta_explicacion_porcentaje = QLabel(
            "El despacho solo confirmó el factor de las horas extra dominicales/festivas "
            "(HEFD/HEFN) desde el "
            f"{formatear_fecha(FECHA_INICIO_TRAMO_1_LEY_2466)} (Tramo 1 de la Ley 2466 de "
            "2025). Para horas causadas antes de esa fecha, digite el porcentaje que "
            "corresponde al caso."
        )
        self.etiqueta_explicacion_porcentaje.setWordWrap(True)

        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.setDefault(True)
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
        self.atajo_guardar = QShortcut(QKeySequence("Ctrl+S"), self)
        self.atajo_guardar.activated.connect(self._guardar_y_cerrar)

        self._layout_formulario = QFormLayout()
        self._layout_formulario.addRow("Concepto", self.combo_concepto)
        self._layout_formulario.addRow("Fecha de causación", self.campo_fecha_causacion)
        self._layout_formulario.addRow("Cantidad de horas", self.campo_horas)
        self._layout_formulario.addRow("Valor hora ordinaria", self.campo_valor_hora)
        self._layout_formulario.addRow("Factor aplicado", self.etiqueta_factor)
        self._layout_formulario.addRow(self.etiqueta_explicacion_porcentaje)
        self._layout_formulario.addRow(
            "Porcentaje de la hora extra (%)", self.campo_porcentaje_manual
        )
        self._layout_formulario.addRow(self.boton_guardar)
        self.setLayout(self._layout_formulario)

        self.combo_concepto.currentIndexChanged.connect(self._actualizar_factor)
        self.campo_fecha_causacion.dateChanged.connect(self._actualizar_factor)
        self._actualizar_factor()

    def _fecha_causacion(self) -> date:
        qdate = self.campo_fecha_causacion.date()
        return date(qdate.year(), qdate.month(), qdate.day())

    def _requiere_porcentaje(self) -> bool:
        return requiere_porcentaje_manual(
            self.combo_concepto.currentData(), self._fecha_causacion()
        )

    def _actualizar_factor(self) -> None:
        requiere = self._requiere_porcentaje()
        set_row_visible(self._layout_formulario, self.campo_porcentaje_manual, requiere)
        set_row_visible(self._layout_formulario, self.etiqueta_explicacion_porcentaje, requiere)
        if requiere:
            self.etiqueta_factor.setText("1 + porcentaje digitado / 100")
        else:
            factor = factor_hora_extra(self.combo_concepto.currentData(), self._fecha_causacion())
            self.etiqueta_factor.setText(
                f"{_formatear_factor(factor)} (valor hora x {_formatear_factor(factor)})"
            )

    def guardar(self) -> int:
        numero_horas = _decimal_positivo(self.campo_horas.text(), "La cantidad de horas")
        valor_hora = _decimal_positivo(self.campo_valor_hora.text(), "El valor de la hora")
        porcentaje_manual = None
        if self._requiere_porcentaje():
            if not self.campo_porcentaje_manual.text().strip():
                raise ValueError(
                    "Falta el porcentaje de la hora extra festiva: "
                    + self.etiqueta_explicacion_porcentaje.text()
                )
            porcentaje_manual = _decimal_positivo(
                self.campo_porcentaje_manual.text(), "El porcentaje"
            )

        session = session_module.get_session()
        try:
            hora_extra = HoraExtraLaboral(
                obligacion_id=self._obligacion_id,
                concepto=self.combo_concepto.currentData(),
                fecha_causacion=self._fecha_causacion(),
                numero_horas=numero_horas,
                valor_hora=valor_hora,
                porcentaje_manual=porcentaje_manual,
            )
            session.add(hora_extra)
            session.commit()
            return hora_extra.id
        finally:
            session.close()
