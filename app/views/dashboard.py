from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from database.models import Expediente


class DashboardView(QWidget):
    """Pantalla de inicio (Sprint 33): resumen agregado de todos los expedientes,
    en vez de abrir directo al listado plano de expedientes
    (`app/views/expedientes.py`, que sigue existiendo como pantalla "expedientes",
    alcanzable desde aquí con el botón "Ver todos los expedientes").

    Carga sus datos de forma síncrona -- sin `TareaEnHilo`/`QThreadPool` (Sprint
    26) -- porque son consultas SQL livianas más aritmética de fechas sobre, como
    mucho, unas pocas centenas de expedientes/obligaciones: no es la clase de
    operación pesada (`liquidar()`, exportar PDF/Word) que el Sprint 26 sacó del
    hilo de UI. Ver la sección Architecture del plan de este sprint para el
    detalle completo de esta decisión.
    """

    def __init__(self, on_expediente_abierto=None, on_ver_expedientes=None):
        super().__init__()
        self._on_expediente_abierto = on_expediente_abierto
        self._on_ver_expedientes = on_ver_expedientes

        self.boton_ver_expedientes = QPushButton("Ver todos los expedientes")
        self.boton_ver_expedientes.setProperty("class", "primary")
        self.boton_ver_expedientes.clicked.connect(self._emitir_ver_expedientes)

        self.etiqueta_total_expedientes = QLabel()

        self.tabla_por_area = QTableWidget(len(AREAS_DERECHO), 2)
        self.tabla_por_area.setHorizontalHeaderLabels(["Área", "Expedientes"])

        grupo_resumen = QGroupBox("Expedientes por área")
        layout_resumen = QVBoxLayout()
        layout_resumen.addWidget(self.etiqueta_total_expedientes)
        layout_resumen.addWidget(self.tabla_por_area)
        grupo_resumen.setLayout(layout_resumen)

        layout_cta = QHBoxLayout()
        layout_cta.addStretch()
        layout_cta.addWidget(self.boton_ver_expedientes)

        layout_principal = QVBoxLayout()
        layout_principal.addLayout(layout_cta)
        layout_principal.addWidget(grupo_resumen)
        self.setLayout(layout_principal)

        self.refrescar()

    def _emitir_ver_expedientes(self) -> None:
        if self._on_ver_expedientes:
            self._on_ver_expedientes()

    def refrescar(self) -> None:
        session = session_module.get_session()
        expedientes = session.query(Expediente).all()

        self._refrescar_conteo_por_area(expedientes)

        session.close()

    def _refrescar_conteo_por_area(self, expedientes: list[Expediente]) -> None:
        self.etiqueta_total_expedientes.setText(f"Total de expedientes: {len(expedientes)}")

        conteo_por_area = dict.fromkeys((codigo for codigo, _et, _hab in AREAS_DERECHO), 0)
        for expediente in expedientes:
            conteo_por_area[expediente.area_derecho.value] += 1

        for fila, (codigo, etiqueta, _habilitada) in enumerate(AREAS_DERECHO):
            self.tabla_por_area.setItem(fila, 0, QTableWidgetItem(etiqueta))
            self.tabla_por_area.setItem(
                fila, 1, QTableWidgetItem(str(conteo_por_area[codigo]))
            )
