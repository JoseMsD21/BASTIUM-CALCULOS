from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.engine.liquidation.result import LiquidationResult


class ResultadoLiquidacionView(QWidget):
    def __init__(self):
        super().__init__()

        self._resultado = None
        self._expediente_id = None

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "Concepto", "Capital base", "Tasa %", "Interes", "Pago", "Saldo"]
        )

        self.etiqueta_interes_total = QLabel("Interes acumulado: 0.00")
        self.etiqueta_pagos_total = QLabel("Pagos aplicados: 0.00")
        self.etiqueta_saldo_final = QLabel("Saldo final: 0.00")

        layout = QVBoxLayout()
        layout.addWidget(self.tabla)
        layout.addWidget(self.etiqueta_interes_total)
        layout.addWidget(self.etiqueta_pagos_total)
        layout.addWidget(self.etiqueta_saldo_final)
        self.setLayout(layout)

    def mostrar(self, resultado: LiquidationResult, expediente_id: int) -> None:
        self._resultado = resultado
        self._expediente_id = expediente_id

        self.tabla.setRowCount(len(resultado.items))
        for fila, item in enumerate(resultado.items):
            self.tabla.setItem(fila, 0, QTableWidgetItem(item.date.isoformat()))
            self.tabla.setItem(fila, 1, QTableWidgetItem(item.concept))
            self.tabla.setItem(fila, 2, QTableWidgetItem(str(item.capital_base)))
            self.tabla.setItem(fila, 3, QTableWidgetItem(str(item.interest_rate)))
            self.tabla.setItem(fila, 4, QTableWidgetItem(str(item.interest_amount)))
            self.tabla.setItem(fila, 5, QTableWidgetItem(str(item.payment_amount)))
            self.tabla.setItem(fila, 6, QTableWidgetItem(str(item.balance.debt.total())))

        self.etiqueta_interes_total.setText(f"Interes acumulado: {resultado.total_interest_accrued()}")
        self.etiqueta_pagos_total.setText(f"Pagos aplicados: {resultado.total_payments_applied()}")
        self.etiqueta_saldo_final.setText(f"Saldo final: {resultado.final_balance().total()}")
