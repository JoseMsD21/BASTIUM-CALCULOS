"""Sprint 75: dialogo de pago por rango de cuotas-hija, con preview de la
cascada antes de confirmar. Ver docs/superpowers/specs/
2026-08-14-sprint75-cuotas-recurrentes-cascada-design.md, seccion "Alcance",
punto 5.

`_ESTRATEGIA_POR_AREA` solo tiene entradas para CIVIL_FAMILIA y COMERCIAL --
las dos areas que este sprint soporta para cuotas-hija recurrentes
(generar_cuotas_mensuales, Sprint 41/75). El caller (ExpedienteDetallePage)
es responsable de no ofrecer este dialogo para ninguna otra area."""

from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

import database.session as session_module
from app.core.exceptions import IPCMensualNoDisponibleError, ParametroNoDisponibleError
from app.services.area_strategy import CivilFamiliaStrategy, ComercialStrategy
from app.services.cascada_cuotas import deuda_pendiente_cuota, distribuir_pago_en_cascada
from app.views.form_utils import guardar_o_actualizar, hacer_redimensionable
from database.models import Abono

_ESTRATEGIA_POR_AREA = {
    "CIVIL_FAMILIA": CivilFamiliaStrategy,
    "COMERCIAL": ComercialStrategy,
}


class PagoPorRangoDialog(QDialog):
    """`cuotas` debe venir ordenada de la mas reciente a la mas antigua (lo
    decide el caller, segun el rango/seleccion del usuario en la tabla de
    obligaciones -- ver ExpedienteDetallePage._abrir_dialogo_pago_por_rango).
    """

    def __init__(self, cuotas: list, area: str, parent=None):
        super().__init__(parent)
        hacer_redimensionable(self)
        self.setWindowTitle("Pagar cuotas seleccionadas")
        self._cuotas = cuotas
        self._area = area
        self._asignaciones: list[tuple[object, Decimal]] = []
        self._remanente = Decimal("0.00")

        layout = QVBoxLayout(self)
        formulario = QFormLayout()
        self.campo_monto = QLineEdit()
        self.campo_monto.setToolTip(
            "Monto total del pago a repartir entre las cuotas seleccionadas, de la mas "
            "reciente a la mas antigua (capital primero en cada cuota, luego su interes)."
        )
        self.campo_fecha = QDateEdit()
        self.campo_fecha.setCalendarPopup(True)
        self.campo_fecha.setDate(QDate.currentDate())
        formulario.addRow("Monto total del pago", self.campo_monto)
        formulario.addRow("Fecha del pago", self.campo_fecha)
        layout.addLayout(formulario)

        self.tabla_preview = QTableWidget(0, 2)
        self.tabla_preview.setHorizontalHeaderLabels(["Cuota", "Monto asignado"])
        layout.addWidget(self.tabla_preview)

        self.etiqueta_remanente = QLabel("")
        layout.addWidget(self.etiqueta_remanente)

        self.campo_monto.textChanged.connect(self._calcular_preview)
        self.campo_fecha.dateChanged.connect(self._calcular_preview)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.confirmar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _fecha_pago(self) -> date:
        return self.campo_fecha.date().toPython()

    def _calcular_preview(self) -> None:
        self.tabla_preview.setRowCount(0)
        self._asignaciones = []
        self._remanente = Decimal("0.00")
        try:
            monto_total = Decimal(self.campo_monto.text())
        except InvalidOperation:
            self.etiqueta_remanente.setText("Ingrese un monto valido.")
            return

        if monto_total <= Decimal("0.00"):
            self.etiqueta_remanente.setText("El monto debe ser mayor que cero.")
            return

        strategy_cls = _ESTRATEGIA_POR_AREA[self._area]
        strategy = strategy_cls()
        fecha_pago = self._fecha_pago()

        session = session_module.get_session()
        try:
            cuotas_y_deuda = []
            for cuota in self._cuotas:
                abonos_existentes = (
                    session.query(Abono).filter(Abono.obligacion_id == cuota.id).all()
                )
                rate_provider = strategy._construir_rate_provider_obligacion(cuota, fecha_pago)
                deuda = deuda_pendiente_cuota(
                    cuota, abonos_existentes, fecha_pago, rate_provider
                )
                cuotas_y_deuda.append((cuota, deuda))
        except (ParametroNoDisponibleError, IPCMensualNoDisponibleError) as error:
            # Mismo criterio de fallo abierto que _refrescar_alertas_vencimiento en
            # app/views/dashboard.py: una cuota con aplica_indexacion_ipc=True puede
            # necesitar un parametro (IPC_INDICE_ACUMULADO, etc.) que el usuario no
            # cargo todavia en Parametros. Como _calcular_preview corre en cada
            # tecla (textChanged), esto no puede ser un QMessageBox por cada letra --
            # se muestra inline, igual que los demas casos de entrada invalida de
            # este metodo (monto vacio/negativo).
            self.etiqueta_remanente.setText(f"No se pudo calcular la cascada: {error}")
            return
        finally:
            session.close()

        self._asignaciones, self._remanente = distribuir_pago_en_cascada(
            cuotas_y_deuda, monto_total, fecha_pago
        )

        self.tabla_preview.setRowCount(len(self._asignaciones))
        for fila, (cuota, monto) in enumerate(self._asignaciones):
            self.tabla_preview.setItem(fila, 0, QTableWidgetItem(cuota.concepto))
            self.tabla_preview.setItem(fila, 1, QTableWidgetItem(f"{monto:,.2f}"))

        if self._remanente > Decimal("0.00"):
            self.etiqueta_remanente.setText(
                f"Sobran ${self._remanente:,.2f} sin cubrir en las cuotas seleccionadas. "
                "Reduzca el monto o amplíe la selección para confirmar."
            )
        else:
            self.etiqueta_remanente.setText("")

    def confirmar(self) -> None:
        if not self._asignaciones or self._remanente > Decimal("0.00"):
            QMessageBox.warning(
                self,
                "Pago incompleto",
                "El monto debe repartirse por completo entre las cuotas seleccionadas antes "
                "de confirmar.",
            )
            return

        fecha_pago = self._fecha_pago()
        # Una sola sesion para todos los Abono de esta cascada (a diferencia de
        # abrir/cerrar una por cuota): guardar_o_actualizar sigue el mismo
        # patron que AbonoFormDialog.guardar() -- no cierra la sesion, el
        # llamador sigue siendo dueño de su ciclo de vida (ver docstring de
        # guardar_o_actualizar, app/views/form_utils.py).
        session = session_module.get_session()
        try:
            for cuota, monto in self._asignaciones:
                guardar_o_actualizar(
                    session,
                    Abono,
                    None,
                    obligacion_id=cuota.id,
                    fecha=fecha_pago,
                    monto=monto,
                    referencia="Pago por rango (cascada)",
                )
        finally:
            session.close()
        self.accept()
