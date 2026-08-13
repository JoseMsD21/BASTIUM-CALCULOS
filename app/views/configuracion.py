from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.constants import AREAS_DERECHO
from app.services.areas_parametro import AREA_UNIDAD_POR_CLAVE, deserializar_areas
from app.services.parametro_service import (
    CATALOGO_PARAMETROS,
    CLAVE_CRUDA_DE,
    ModoResolucion,
    agregar_valor,
    historial,
    valor_vigente_hoy,
    vigencia_hasta_mostrar,
)
from app.views.form_utils import agregar_ayuda, hacer_redimensionable, set_row_visible
from app.views.icons import icon
from database.models import AreaDerecho, ParametroLegal

# Etiqueta humana por codigo de AreaDerecho, reutilizada tanto para las
# casillas de ParametroFormDialog como para la columna "Área" de
# ParametrosView.tabla (Sprint 57) -- una sola fuente (AREAS_DERECHO en
# app/core/constants.py), no texto nuevo inventado aqui.
_ETIQUETA_POR_AREA = {
    AreaDerecho(codigo): etiqueta for codigo, etiqueta, _habilitada in AREAS_DERECHO
}


def _texto_areas(fila: ParametroLegal | None) -> str:
    """Etiquetas humanas (no codigos crudos) de `fila.areas_derecho`,
    separadas por coma, para la columna "Área" de ParametrosView.tabla.
    Cadena vacia si no hay fila vigente o si la fila todavia no tiene
    areas_derecho asignado (legado, no deberia pasar tras la migracion del
    Sprint 57, pero se maneja de forma defensiva).

    Ningun camino de escritura actual (agregar_valor(), la migracion) puede
    producir un `areas_derecho` corrupto -- ambos pasan por
    serializar_areas()/AREA_UNIDAD_POR_CLAVE, controlados. Pero
    ParametrosView.refrescar() itera las 40 claves de una sola pasada (39 mas
    IPC_VARIACION_ANUAL, Sprint 58): si
    algun dia una fila quedara con JSON invalido o un codigo de area que ya
    no existe en el enum (ej. tras retirar un AreaDerecho en el futuro), que
    esta funcion propague la excepcion tumbaria la carga de TODA la pantalla,
    no solo esa fila. json.JSONDecodeError hereda de ValueError, asi que un
    solo except cubre los dos casos (JSON malformado y codigo desconocido de
    AreaDerecho); KeyError cubre ademas un AreaDerecho valido que faltara en
    _ETIQUETA_POR_AREA -- se degrada solo esa celda a "?", el resto de la
    tabla sigue mostrandose."""
    if fila is None or not fila.areas_derecho:
        return ""
    try:
        return ", ".join(
            _ETIQUETA_POR_AREA[area] for area in deserializar_areas(fila.areas_derecho)
        )
    except (ValueError, KeyError):
        return "?"


class ParametroFormDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        hacer_redimensionable(self)
        self.setWindowTitle("Agregar valor de parametro")

        self.combo_clave = QComboBox()
        self.combo_clave.setToolTip(
            "Clave del parametro legal a versionar; la descripcion entre parentesis "
            "identifica que mide (ej. 'Tasa de interes civil legal anual "
            "(CIVIL_ANNUAL_RATE)')."
        )
        for clave, info in CATALOGO_PARAMETROS.items():
            self.combo_clave.addItem(f"{info.descripcion} ({clave})", userData=clave)

        self.campo_valor = QLineEdit()
        self.campo_valor.setToolTip(
            "Valor numerico vigente para la clave elegida, en la unidad indicada abajo. "
            "Ejemplo: 6.00 para una tasa del 6%, o 1300000 para un SMLMV en pesos."
        )
        self.campo_vigente_desde = QDateEdit(QDate.currentDate())
        self.campo_vigente_desde.setCalendarPopup(True)
        self.campo_vigente_desde.setToolTip(
            "Fecha desde la que este valor empieza a regir (normalmente la fecha del "
            "decreto o resolucion). Ejemplo: 2024-01-01."
        )
        self.campo_vigente_hasta = QDateEdit(QDate.currentDate())
        self.campo_vigente_hasta.setCalendarPopup(True)
        self.campo_vigente_hasta.setToolTip(
            "Fecha hasta la que este valor rigio; solo aplica a parametros con un "
            "rango de vigencia cerrado (ej. tramos historicos de tasas certificadas)."
        )

        # Casillas de area del derecho (Sprint 57): una por AreaDerecho,
        # preseleccionadas segun AREA_UNIDAD_POR_CLAVE cuando cambia la clave
        # elegida (_actualizar_area_unidad_sugeridas), pero editables antes de
        # guardar -- el usuario puede ajustar la propuesta. Guardadas en un
        # dict (no una lista) para poder leer/escribir por AreaDerecho sin
        # depender del orden de iteracion.
        self.casillas_area: dict[AreaDerecho, QCheckBox] = {}
        self._contenedor_areas = QWidget()
        self._contenedor_areas.setToolTip(
            "Area(s) del derecho a las que aplica este valor (puede marcar varias). Se "
            "preselecciona segun la clave elegida; no se puede editar despues de guardar."
        )
        _layout_areas = QVBoxLayout(self._contenedor_areas)
        _layout_areas.setContentsMargins(0, 0, 0, 0)
        for codigo, etiqueta, _habilitada in AREAS_DERECHO:
            casilla = QCheckBox(etiqueta)
            self.casillas_area[AreaDerecho(codigo)] = casilla
            _layout_areas.addWidget(casilla)

        self.campo_unidad = QLineEdit()

        self.campo_usuario = QLineEdit()
        self.campo_usuario.setToolTip(
            "Nombre de quien registra este valor, para la bitacora de auditoria del "
            "parametro (no se puede editar ni borrar despues)."
        )
        self.campo_motivo = QLineEdit()
        self.campo_motivo.setToolTip(
            "Justificacion o fuente del cambio, para dejar constancia del porque de "
            "este valor. Ejemplo: 'Decreto 2613 de 2023, ajuste SMLMV 2024'."
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

        # Guardado como atributo (en vez de variable local `layout`) para que
        # _actualizar_visibilidad_vigente_hasta pueda ocultar la fila completa
        # (etiqueta + campo) con set_row_visible (Sprint 39) en vez de solo el
        # QDateEdit.
        self._layout_formulario = QFormLayout()
        self._layout_formulario.addRow("Parametro", self.combo_clave)
        self._layout_formulario.addRow("Valor", self.campo_valor)
        self._layout_formulario.addRow("Vigente desde", self.campo_vigente_desde)
        self._layout_formulario.addRow("Vigente hasta", self.campo_vigente_hasta)
        self._layout_formulario.addRow("Área(s) del derecho", self._contenedor_areas)
        # "Unidad" recibe el icono (i) explicito (Sprint 59, helper compartido
        # agregar_ayuda): se pre-rellena segun la clave elegida
        # (_actualizar_area_unidad_sugeridas), asi que el icono deja claro que es una
        # propuesta editable, no un valor fijo -- mismo patron que "Tasa efectiva
        # anual" en ObligacionFormDialog para un campo con valor por defecto.
        self._contenedor_campo_unidad = agregar_ayuda(
            self._layout_formulario,
            "Unidad",
            self.campo_unidad,
            tooltip=(
                "Unidad de medida del valor, sugerida automaticamente segun la clave "
                "elegida. No se puede editar despues de guardar."
            ),
            ejemplo="%, COP, meses, índice",
        )
        self._layout_formulario.addRow("Usuario", self.campo_usuario)
        self._layout_formulario.addRow("Motivo (opcional)", self.campo_motivo)
        self._layout_formulario.addRow(self.boton_guardar)
        self.setLayout(self._layout_formulario)

        self.combo_clave.currentIndexChanged.connect(self._actualizar_visibilidad_vigente_hasta)
        self.combo_clave.currentIndexChanged.connect(self._actualizar_area_unidad_sugeridas)
        self._actualizar_visibilidad_vigente_hasta()
        self._actualizar_area_unidad_sugeridas()

    def _actualizar_area_unidad_sugeridas(self) -> None:
        """Preselecciona las casillas de area y pre-rellena la unidad segun
        AREA_UNIDAD_POR_CLAVE para la clave elegida -- el usuario puede
        ajustar ambos antes de guardar (Sprint 57, decision del usuario: la
        propuesta no es definitiva, solo un punto de partida)."""
        clave = self.combo_clave.currentData()
        areas_sugeridas, unidad_sugerida = AREA_UNIDAD_POR_CLAVE[clave]
        areas_sugeridas_set = set(areas_sugeridas)
        for area, casilla in self.casillas_area.items():
            casilla.setChecked(area in areas_sugeridas_set)
        self.campo_unidad.setText(unidad_sugerida)

    def _actualizar_visibilidad_vigente_hasta(self) -> None:
        clave = self.combo_clave.currentData()
        info = CATALOGO_PARAMETROS[clave]
        # set_row_visible (no campo_vigente_hasta.setVisible() suelto) para que la
        # etiqueta "Vigente hasta" generada por addRow(str, widget) se oculte junto
        # con el campo -- de lo contrario queda una fila huerfana (Sprint 39).
        set_row_visible(
            self._layout_formulario,
            self.campo_vigente_hasta,
            info.modo == ModoResolucion.TRAMO_CERRADO,
        )

    def guardar(self):
        clave = self.combo_clave.currentData()
        info = CATALOGO_PARAMETROS[clave]

        try:
            valor = Decimal(self.campo_valor.text())
        except InvalidOperation as error:
            raise ValueError("El valor debe ser un numero valido.") from error
        if not valor.is_finite():
            raise ValueError("El valor debe ser un numero finito.")

        usuario = self.campo_usuario.text().strip()
        if not usuario:
            raise ValueError("El campo Usuario es obligatorio.")

        qdate_desde = self.campo_vigente_desde.date()
        vigente_desde = date(qdate_desde.year(), qdate_desde.month(), qdate_desde.day())

        vigente_hasta = None
        if info.modo == ModoResolucion.TRAMO_CERRADO:
            qdate_hasta = self.campo_vigente_hasta.date()
            vigente_hasta = date(qdate_hasta.year(), qdate_hasta.month(), qdate_hasta.day())

        motivo = self.campo_motivo.text().strip() or None

        areas_derecho = [
            area for area, casilla in self.casillas_area.items() if casilla.isChecked()
        ]
        unidad = self.campo_unidad.text().strip()

        return agregar_valor(
            clave=clave,
            valor=valor,
            vigente_desde=vigente_desde,
            usuario=usuario,
            areas_derecho=areas_derecho,
            unidad=unidad,
            motivo=motivo,
            vigente_hasta=vigente_hasta,
        )

    def _guardar_y_cerrar(self) -> None:
        try:
            self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos invalidos", str(error))


class HistorialParametroDialog(QDialog):
    # Sprint 58: etiqueta de columna + nota de formula por CADA clave
    # calculada que tiene un dato crudo asociado (CLAVE_CRUDA_DE,
    # parametro_service.py). Separado de ese diccionario a proposito:
    # CLAVE_CRUDA_DE es DATO (que clave se deriva de cual), esto es TEXTO DE
    # PRESENTACION (como mostrarlo) -- si en el futuro aparece un segundo caso
    # con formula propia, agregar su entrada aqui (ademas de en
    # CLAVE_CRUDA_DE) es indispensable: `_presentacion_dato_crudo[clave]` mas
    # abajo es un indexado directo (no `.get()` con default), asi que agregar
    # una clave a CLAVE_CRUDA_DE sin agregar su presentacion aqui revienta
    # con KeyError en vez de mostrar en silencio la etiqueta/formula del IPC
    # para una clave que no es IPC.
    _PRESENTACION_DATO_CRUDO: dict[str, tuple[str, str]] = {
        "IPC_INDICE_ACUMULADO": (
            "Variación anual (%)",
            "Índice = índice del año anterior × (1 + variación anual / 100). "
            "Fuente: tabla de variación % anual del PDF de requerimientos, "
            "transcrita en historical_index.py.",
        ),
    }

    def __init__(self, clave: str, parent=None):
        super().__init__(parent)
        hacer_redimensionable(self)
        info = CATALOGO_PARAMETROS[clave]
        self.setWindowTitle(f"Historial: {info.descripcion}")

        # Sprint 58: si `clave` tiene un dato crudo asociado (CLAVE_CRUDA_DE),
        # se agrega una columna extra con ese valor cruda por año, mas una
        # nota fija explicando la formula -- ambos textos salen de
        # _PRESENTACION_DATO_CRUDO (arriba), nunca hardcodeados a IPC aqui.
        clave_cruda = CLAVE_CRUDA_DE.get(clave)
        etiqueta_columna_cruda: str | None = None
        formula_texto: str | None = None
        if clave_cruda is not None:
            etiqueta_columna_cruda, formula_texto = self._PRESENTACION_DATO_CRUDO[clave]

        columnas = ["Valor", "Vigente desde", "Vigente hasta", "Usuario", "Motivo"]
        if etiqueta_columna_cruda is not None:
            columnas = [*columnas, etiqueta_columna_cruda]
        self.tabla = QTableWidget(0, len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        filas = historial(clave)
        variacion_por_anio: dict[int, str] = {}
        if clave_cruda is not None:
            variacion_por_anio = {
                fila_cruda.vigente_desde.year: str(fila_cruda.valor)
                for fila_cruda in historial(clave_cruda)
            }

        self.tabla.setRowCount(len(filas))
        for fila_idx, fila in enumerate(filas):
            self.tabla.setItem(fila_idx, 0, QTableWidgetItem(str(fila.valor)))
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(fila.vigente_desde.isoformat()))
            self.tabla.setItem(fila_idx, 2, QTableWidgetItem(vigencia_hasta_mostrar(fila, info)))
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(fila.usuario))
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(fila.motivo or ""))
            if clave_cruda is not None:
                variacion = variacion_por_anio.get(fila.vigente_desde.year, "")
                self.tabla.setItem(fila_idx, 5, QTableWidgetItem(variacion))

        layout = QVBoxLayout()
        layout.addWidget(self.tabla)
        if formula_texto is not None:
            nota_formula = QLabel(formula_texto)
            nota_formula.setWordWrap(True)
            layout.addWidget(nota_formula)
        self.setLayout(layout)


class ParametrosView(QWidget):
    def __init__(self):
        super().__init__()
        self._claves_por_fila: list[str] = []

        columnas = [
            "Categoria",
            "Parametro",
            "Valor vigente hoy",
            "Vigente desde",
            "Vigente hasta",
            "Área",
            "Unidad",
        ]
        self.tabla = QTableWidget(0, len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.cellDoubleClicked.connect(self._abrir_historial)

        self.boton_agregar = QPushButton("+ Agregar valor nuevo")
        self.boton_agregar.setProperty("class", "primary")
        self.boton_agregar.clicked.connect(self._abrir_dialogo_agregar)

        botones = QHBoxLayout()
        botones.addWidget(self.boton_agregar)

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
            texto_valor = str(vigente.valor) if vigente else "(sin dato)"
            if vigente is not None:
                # Sprint 58: enlace descubrible al historial completo cuando
                # una clave tiene mas de 1 fila -- antes solo el doble clic
                # (no documentado) lo abria. No duplica la logica de apertura:
                # sigue siendo _abrir_historial via cellDoubleClicked, este
                # texto solo la hace visible.
                n_historicas = len(historial(clave))
                if n_historicas > 1:
                    texto_valor = f"{texto_valor} — Ver {n_historicas} valores históricos"
            self.tabla.setItem(fila_idx, 2, QTableWidgetItem(texto_valor))
            self.tabla.setItem(
                fila_idx, 3,
                QTableWidgetItem(vigente.vigente_desde.isoformat() if vigente else ""),
            )
            self.tabla.setItem(
                fila_idx, 4,
                QTableWidgetItem(vigencia_hasta_mostrar(vigente, info) if vigente else ""),
            )
            self.tabla.setItem(fila_idx, 5, QTableWidgetItem(_texto_areas(vigente)))
            self.tabla.setItem(
                fila_idx, 6, QTableWidgetItem(vigente.unidad if vigente and vigente.unidad else "")
            )
            self._claves_por_fila.append(clave)
        # La columna "Área" (Sprint 57) puede mostrar hasta las 6 etiquetas
        # concatenadas (ej. PRESCRIPCION_EJECUTIVA_MESES) -- sin esto el ancho
        # fijo por defecto de QTableWidget la trunca.
        self.tabla.resizeColumnsToContents()

    def _abrir_dialogo_agregar(self) -> None:
        dialogo = ParametroFormDialog(self)
        if dialogo.exec():
            self.refrescar()

    def _abrir_historial(self, fila: int, _columna: int) -> None:
        clave = self._claves_por_fila[fila]
        HistorialParametroDialog(clave, self).exec()
