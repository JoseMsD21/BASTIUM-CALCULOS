from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QDateEdit, QDialog, QFormLayout, QLineEdit, QMessageBox, QPushButton

import database.session as session_module
from app.views.form_utils import agregar_ayuda, guardar_o_actualizar, hacer_redimensionable
from app.views.icons import icon
from database.models import Abono, Obligacion


class AbonoFormDialog(QDialog):
    def __init__(self, obligacion_id: int, parent=None, abono_id: int | None = None):
        super().__init__(parent)
        hacer_redimensionable(self)
        self.setWindowTitle("Editar abono" if abono_id else "Agregar abono")
        self._obligacion_id = obligacion_id
        self._abono_id = abono_id

        self.campo_fecha = QDateEdit(QDate.currentDate())
        self.campo_fecha.setCalendarPopup(True)
        self.campo_fecha.setToolTip(
            "Fecha en que se realizo el pago. Ejemplo: si el abono se hizo el "
            "15/03/2024, seleccione esa fecha aunque se registre despues."
        )
        self.campo_monto = QLineEdit()
        self.campo_monto.setToolTip(
            "Valor efectivamente pagado por el cliente o deudor en la fecha indicada."
        )
        self.campo_referencia = QLineEdit()
        self.campo_referencia.setToolTip(
            "Referencia de pago opcional (ej. numero de consignacion, cheque o "
            "transaccion)."
        )

        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        # Enter/Return dispara Guardar (Sprint 37): Qt ya trata automaticamente al
        # unico QPushButton de un QDialog como boton por defecto, pero se fija
        # explicitamente para no depender de ese comportamiento implicito si en el
        # futuro se agrega otro boton (ej. "Cancelar").
        self.boton_guardar.setDefault(True)
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
        # Ctrl+S = guardar (Sprint 32). Esc = cancelar ya viene gratis de
        # QDialog.keyPressEvent() (reject() por defecto) -- no requiere codigo aqui.
        self.atajo_guardar = QShortcut(QKeySequence("Ctrl+S"), self)
        self.atajo_guardar.activated.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
        layout.addRow("Fecha", self.campo_fecha)
        # "Monto" recibe ademas el icono (i) explicito (Sprint 59, helper compartido
        # agregar_ayuda): es el campo con efecto no obvio -- interactua con la
        # heuristica de sobrepago que compara la suma de abonos contra el valor de la
        # obligacion (ver guardar()).
        self._contenedor_campo_monto = agregar_ayuda(
            layout,
            "Monto",
            self.campo_monto,
            tooltip=(
                "Valor efectivamente pagado por el cliente o deudor; se resta al "
                "saldo pendiente al liquidar."
            ),
            ejemplo="$500.000 si el deudor abono esa suma en la fecha indicada.",
        )
        layout.addRow("Referencia", self.campo_referencia)
        layout.addRow(self.boton_guardar)
        self.setLayout(layout)

        if abono_id is not None:
            self._precargar_desde_abono(abono_id)

    def _precargar_desde_abono(self, abono_id: int) -> None:
        """Precarga los campos del formulario desde un `Abono` ya guardado
        (Sprint 60) -- mismo patron que `_precargar_desde_evento`
        (app/views/eventos_laborales.py) y `_precargar_desde_obligacion`
        (app/views/obligaciones.py): espejo, campo por campo, de lo que
        `guardar()` lee del formulario."""
        session = session_module.get_session()
        try:
            abono = session.get(Abono, abono_id)
            self.campo_fecha.setDate(QDate(abono.fecha.year, abono.fecha.month, abono.fecha.day))
            self.campo_monto.setText(str(abono.monto))
            self.campo_referencia.setText(abono.referencia or "")
        finally:
            session.close()

    def guardar(self) -> int:
        try:
            monto = Decimal(self.campo_monto.text())
        except InvalidOperation as error:
            raise ValueError("El monto debe ser un numero valido.") from error

        if monto <= Decimal("0"):
            raise ValueError("El monto del abono debe ser mayor que cero.")

        qdate = self.campo_fecha.date()
        fecha = date(qdate.year(), qdate.month(), qdate.day())

        session = session_module.get_session()
        obligacion = session.get(Obligacion, self._obligacion_id)
        # Al editar (self._abono_id no es None), excluye el propio abono de la
        # suma -- de lo contrario su valor anterior se contaria dos veces (una
        # vez como parte de `obligacion.abonos` ya guardado, otra vez en
        # `monto`, el valor nuevo que lo va a reemplazar).
        abonos_previos = sum(
            (a.monto for a in obligacion.abonos if a.id != self._abono_id), Decimal("0.00")
        )
        if abonos_previos + monto > obligacion.valor:
            # Heuristica no bloqueante: compara solo capital contra abonos, sin
            # recalcular intereses/indexacion (eso requeriria correr el motor de
            # liquidacion completo). El sobrepago real, si lo hay, siempre queda
            # reflejado con precision como saldo_a_favor al liquidar (Sprint 23).
            QMessageBox.warning(
                self,
                "Posible sobrepago",
                "El total de abonos para esta obligación "
                f"(${abonos_previos + monto:,.2f}) supera el valor registrado "
                f"(${obligacion.valor:,.2f}). Verifique el monto antes de continuar: "
                "el excedente quedará reflejado como saldo a favor al liquidar.",
            )

        abono_id = guardar_o_actualizar(
            session,
            Abono,
            self._abono_id,
            obligacion_id=self._obligacion_id,
            fecha=fecha,
            monto=monto,
            referencia=self.campo_referencia.text().strip() or None,
        )
        session.close()
        return abono_id

    def _guardar_y_cerrar(self) -> None:
        try:
            self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos invalidos", str(error))
