"""Sprint 106: formato de fecha unico dia/mes/año en toda la app y widgets de
fecha estructurados.

Pedido del despacho (docs/Pendientes.md, Sprint 106): "PARA TODO EL
DESARROLLO DEBE TENERSE UN SOLO FORMATO DE FECHA: DÍA/MES/AÑO". Antes de este
sprint ningun `QDateEdit` fijaba `setDisplayFormat`, asi que el formato
dependia de la configuracion regional del sistema operativo. Toda vista crea
ahora sus campos de fecha con `crear_campo_fecha` (una prueba de guardia en
tests/views/test_fecha_widgets.py lo exige).

`SelectorFechasAnuales` reemplaza el texto libre "MM-DD" del campo de fechas
anuales fijas (Sprint 73) por un widget estructurado Dia/Mes, segun la
respuesta del despacho (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint
106). El formato GUARDADO no cambia: sigue siendo la lista JSON de "MM-DD" que
consume app/services/recurrencia_fechas_fijas.py -- solo cambia lo que el
usuario ve y escribe (dia antes que mes), asi que no hace falta migrar datos.
El 29 de febrero se acepta; en los años no bisiestos la cuota se genera el 28
de febrero (`CalendarUtils.safe_create_date`, mismo tratamiento que el motor de
recurrencia ya le daba desde el Sprint 73).
"""

import calendar
from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

FORMATO_FECHA_UI = "dd/MM/yyyy"

# 2000 es bisiesto: año de referencia para saber cuantos dias tiene cada mes
# sin rechazar el 29 de febrero (mismo criterio que
# recurrencia_fechas_fijas._ANIO_BISIESTO_REFERENCIA).
_ANIO_BISIESTO_REFERENCIA = 2000

NOMBRES_MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def formatear_fecha(fecha: date | None) -> str:
    """Fecha en formato dia/mes/año para mostrar en pantalla ("—" si no hay)."""
    return fecha.strftime("%d/%m/%Y") if fecha is not None else "—"


def crear_campo_fecha(fecha: QDate | date | None = None) -> QDateEdit:
    """QDateEdit con formato dd/MM/yyyy fijo (independiente del sistema
    operativo). Sin `fecha`, arranca en la fecha de hoy."""
    if fecha is None:
        fecha = QDate.currentDate()
    elif isinstance(fecha, date):
        fecha = QDate(fecha.year, fecha.month, fecha.day)
    campo = QDateEdit(fecha)
    campo.setDisplayFormat(FORMATO_FECHA_UI)
    return campo


def _ultimo_dia_del_mes(mes: int) -> int:
    return calendar.monthrange(_ANIO_BISIESTO_REFERENCIA, mes)[1]


class CampoFechaOpcional(QWidget):
    """Fecha que puede quedar vacia: una casilla habilita el QDateEdit.
    `fecha()` retorna None mientras la casilla este desmarcada."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.check = QCheckBox("Registrar")
        self.campo_fecha = crear_campo_fecha()
        self.campo_fecha.setCalendarPopup(True)
        self.campo_fecha.setEnabled(False)
        self.check.toggled.connect(self.campo_fecha.setEnabled)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.check)
        layout.addWidget(self.campo_fecha, 1)
        self.setLayout(layout)
        self.setFocusProxy(self.check)

    def fecha(self) -> date | None:
        if not self.check.isChecked():
            return None
        return self.campo_fecha.date().toPython()

    def establecer_fecha(self, fecha: date | None) -> None:
        if fecha is None:
            self.check.setChecked(False)
            return
        self.campo_fecha.setDate(QDate(fecha.year, fecha.month, fecha.day))
        self.check.setChecked(True)


class SelectorFechasAnuales(QWidget):
    """Lista de pares dia-mes (sin año) con agregar/quitar. Se muestra como
    "DD/MM (d de mes)"; `fechas_mm_dd()` entrega el formato de almacenamiento
    "MM-DD" que espera serializar_fechas_anuales."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fechas: list[tuple[int, int]] = []  # (dia, mes)

        self.spin_dia = QSpinBox()
        self.spin_dia.setRange(1, 31)
        self.spin_dia.setToolTip("Dia del mes")
        self.combo_mes = QComboBox()
        self.combo_mes.setToolTip("Mes")
        for numero, nombre in enumerate(NOMBRES_MESES, start=1):
            self.combo_mes.addItem(nombre.capitalize(), userData=numero)
        self.combo_mes.currentIndexChanged.connect(self._ajustar_maximo_dia)
        self._ajustar_maximo_dia()

        self.boton_agregar = QPushButton("Agregar")
        self.boton_agregar.setProperty("class", "secondary")
        self.boton_agregar.clicked.connect(self._agregar_desde_controles)
        self.boton_quitar = QPushButton("Quitar seleccionada")
        self.boton_quitar.setProperty("class", "secondary")
        self.boton_quitar.clicked.connect(self._quitar_seleccionada)

        self.lista = QListWidget()
        self.lista.setMaximumHeight(110)

        fila_controles = QHBoxLayout()
        fila_controles.setContentsMargins(0, 0, 0, 0)
        fila_controles.addWidget(self.spin_dia)
        fila_controles.addWidget(self.combo_mes, 1)
        fila_controles.addWidget(self.boton_agregar)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(fila_controles)
        layout.addWidget(self.lista)
        layout.addWidget(self.boton_quitar)
        self.setLayout(layout)

    def widgets_en_orden_de_tabulacion(self) -> list[QWidget]:
        """Controles internos en orden visual, para que el formulario
        contenedor los encadene en su setTabOrder()."""
        return [
            self.spin_dia,
            self.combo_mes,
            self.boton_agregar,
            self.lista,
            self.boton_quitar,
        ]

    def _ajustar_maximo_dia(self) -> None:
        mes = self.combo_mes.currentData()
        if mes is not None:
            self.spin_dia.setMaximum(_ultimo_dia_del_mes(mes))

    def _agregar_desde_controles(self) -> None:
        self.agregar_fecha(self.spin_dia.value(), self.combo_mes.currentData())

    def _quitar_seleccionada(self) -> None:
        fila = self.lista.currentRow()
        if 0 <= fila < len(self._fechas):
            del self._fechas[fila]
            self._refrescar_lista()

    def agregar_fecha(self, dia: int, mes: int) -> None:
        """Agrega el par dia-mes (ignora duplicados). Lanza ValueError si el
        dia no existe en ese mes (29 de febrero si se acepta)."""
        if not 1 <= mes <= 12:
            raise ValueError(f"Mes {mes} invalido -- debe estar entre 1 y 12.")
        if not 1 <= dia <= _ultimo_dia_del_mes(mes):
            raise ValueError(f"{NOMBRES_MESES[mes - 1].capitalize()} no tiene dia {dia}.")
        if (dia, mes) not in self._fechas:
            self._fechas.append((dia, mes))
            self._refrescar_lista()

    def establecer_fechas_mm_dd(self, fechas_mm_dd: list[str]) -> None:
        self._fechas = []
        for fecha_mm_dd in fechas_mm_dd:
            mes, dia = (int(parte) for parte in fecha_mm_dd.split("-"))
            if (dia, mes) not in self._fechas:
                self._fechas.append((dia, mes))
        self._refrescar_lista()

    def fechas_mm_dd(self) -> list[str]:
        return [f"{mes:02d}-{dia:02d}" for dia, mes in self._fechas]

    def _refrescar_lista(self) -> None:
        self.lista.clear()
        for dia, mes in self._fechas:
            self.lista.addItem(f"{dia:02d}/{mes:02d} ({dia} de {NOMBRES_MESES[mes - 1]})")
