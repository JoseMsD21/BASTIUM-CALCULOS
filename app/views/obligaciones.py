from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
)

import database.session as session_module
from app.core.constants import CATEGORIAS_CIVIL_FAMILIA, CATEGORIAS_COMERCIAL
from database.models import Obligacion, TipoObligacion


class ObligacionFormDialog(QDialog):
    def __init__(self, expediente_id: int, area: str = "CIVIL_FAMILIA", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar obligacion")
        self._expediente_id = expediente_id
        self._area = area

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("Puntual", userData="PUNTUAL")
        self.combo_tipo.addItem("Recurrente", userData="RECURRENTE")
        self.combo_tipo.currentIndexChanged.connect(self._actualizar_campos_visibles)

        self.combo_categoria = QComboBox()
        categorias = CATEGORIAS_COMERCIAL if self._area == "COMERCIAL" else CATEGORIAS_CIVIL_FAMILIA
        for codigo, etiqueta in categorias:
            self.combo_categoria.addItem(etiqueta, userData=codigo)

        self.campo_concepto = QLineEdit()
        self.campo_valor = QLineEdit()
        self.campo_tasa = QLineEdit("6.00")

        self.campo_fecha_origen = QDateEdit(QDate.currentDate())
        self.campo_fecha_origen.setCalendarPopup(True)

        self.campo_fecha_inicio = QDateEdit(QDate.currentDate())
        self.campo_fecha_inicio.setCalendarPopup(True)
        self.campo_dia_pago = QSpinBox()
        self.campo_dia_pago.setRange(1, 28)
        self.campo_dia_pago.setValue(5)

        self.campo_tasa_moratoria = QLineEdit("24.00")
        self.campo_fecha_vencimiento = QDateEdit(QDate.currentDate())
        self.campo_fecha_vencimiento.setCalendarPopup(True)
        self.campo_ibc_vigente = QLineEdit()

        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)

        self.layout_formulario = QFormLayout()
        self.layout_formulario.addRow("Tipo", self.combo_tipo)
        self.layout_formulario.addRow("Categoria", self.combo_categoria)
        self.layout_formulario.addRow("Concepto", self.campo_concepto)
        self.layout_formulario.addRow("Valor", self.campo_valor)
        self.layout_formulario.addRow("Tasa efectiva anual (%)", self.campo_tasa)
        self.layout_formulario.addRow("Fecha de origen (Puntual)", self.campo_fecha_origen)
        self.layout_formulario.addRow("Fecha de inicio (Recurrente)", self.campo_fecha_inicio)
        self.layout_formulario.addRow("Dia de pago (Recurrente)", self.campo_dia_pago)
        self.layout_formulario.addRow("Tasa moratoria anual (%)", self.campo_tasa_moratoria)
        self.layout_formulario.addRow("Fecha de vencimiento", self.campo_fecha_vencimiento)
        self.layout_formulario.addRow("IBC vigente aplicable (%)", self.campo_ibc_vigente)
        self.layout_formulario.addRow(boton_guardar)
        self.setLayout(self.layout_formulario)

        es_comercial = self._area == "COMERCIAL"
        self.campo_tasa_moratoria.setVisible(es_comercial)
        self.campo_fecha_vencimiento.setVisible(es_comercial)
        self.campo_ibc_vigente.setVisible(es_comercial)

        self._actualizar_campos_visibles()

    def _actualizar_campos_visibles(self) -> None:
        es_recurrente = self.combo_tipo.currentData() == "RECURRENTE"
        self.campo_fecha_origen.setVisible(not es_recurrente)
        self.campo_fecha_inicio.setVisible(es_recurrente)
        self.campo_dia_pago.setVisible(es_recurrente)

    def guardar(self) -> int:
        try:
            valor = Decimal(self.campo_valor.text())
            tasa = Decimal(self.campo_tasa.text())
        except InvalidOperation as error:
            raise ValueError("Valor y tasa deben ser numeros validos.") from error

        if valor <= Decimal("0"):
            raise ValueError("El valor de la obligacion debe ser mayor que cero.")

        tasa_moratoria = None
        fecha_vencimiento = None
        ibc_vigente = None
        if self._area == "COMERCIAL":
            try:
                tasa_moratoria = Decimal(self.campo_tasa_moratoria.text())
                ibc_vigente = Decimal(self.campo_ibc_vigente.text())
            except InvalidOperation as error:
                raise ValueError("Tasa moratoria e IBC vigente deben ser numeros validos.") from error
            qdate_vencimiento = self.campo_fecha_vencimiento.date()
            fecha_vencimiento = date(
                qdate_vencimiento.year(), qdate_vencimiento.month(), qdate_vencimiento.day()
            )

        tipo = TipoObligacion(self.combo_tipo.currentData())
        qdate_origen = self.campo_fecha_origen.date()
        fecha_origen = date(qdate_origen.year(), qdate_origen.month(), qdate_origen.day())
        qdate_inicio = self.campo_fecha_inicio.date()
        fecha_inicio = date(qdate_inicio.year(), qdate_inicio.month(), qdate_inicio.day())

        session = session_module.get_session()
        obligacion = Obligacion(
            expediente_id=self._expediente_id,
            tipo=tipo,
            concepto=self.campo_concepto.text().strip(),
            categoria=self.combo_categoria.currentData(),
            fecha_origen=fecha_origen if tipo == TipoObligacion.PUNTUAL else fecha_inicio,
            valor=valor,
            tasa_efectiva_anual=tasa,
            tasa_moratoria_anual=tasa_moratoria,
            fecha_vencimiento=fecha_vencimiento,
            ibc_vigente_anual=ibc_vigente,
            dia_pago=self.campo_dia_pago.value() if tipo == TipoObligacion.RECURRENTE else None,
            fecha_inicio=fecha_inicio if tipo == TipoObligacion.RECURRENTE else None,
            fecha_fin=None,
        )
        session.add(obligacion)
        session.commit()
        obligacion_id = obligacion.id
        session.close()
        return obligacion_id

    def _guardar_y_cerrar(self) -> None:
        try:
            self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos invalidos", str(error))
