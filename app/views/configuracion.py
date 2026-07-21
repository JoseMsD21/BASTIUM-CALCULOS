from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.parametro_service import CATALOGO_PARAMETROS, valor_vigente_hoy


class ParametrosView(QWidget):
    def __init__(self):
        super().__init__()
        self._claves_por_fila: list[str] = []

        columnas = ["Categoria", "Parametro", "Valor vigente hoy", "Vigente desde"]
        self.tabla = QTableWidget(0, len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        boton_agregar = QPushButton("+ Agregar valor nuevo")
        boton_agregar.clicked.connect(self._abrir_dialogo_agregar)

        botones = QHBoxLayout()
        botones.addWidget(boton_agregar)

        layout = QVBoxLayout()
        layout.addLayout(botones)
        layout.addWidget(self.tabla)
        self.setLayout(layout)

        self.refrescar()

    def refrescar(self) -> None:
        claves = list(CATALOGO_PARAMETROS.items())
        self.tabla.setRowCount(len(claves))
        self._claves_por_fila = []
        for fila_idx, (clave, info) in enumerate(claves):
            vigente = valor_vigente_hoy(clave)
            self.tabla.setItem(fila_idx, 0, QTableWidgetItem(info.categoria))
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(info.descripcion))
            self.tabla.setItem(
                fila_idx, 2, QTableWidgetItem(str(vigente.valor) if vigente else "(sin dato)")
            )
            self.tabla.setItem(
                fila_idx, 3,
                QTableWidgetItem(vigente.vigente_desde.isoformat() if vigente else ""),
            )
            self._claves_por_fila.append(clave)

    def _abrir_dialogo_agregar(self) -> None:
        pass  # implementado en la siguiente tarea
