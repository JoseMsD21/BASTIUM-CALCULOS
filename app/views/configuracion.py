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

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.services.areas_parametro import AREA_UNIDAD_POR_CLAVE, deserializar_areas
from app.services.parametro_service import (
    CATALOGO_PARAMETROS,
    CLAVE_CRUDA_DE,
    ModoResolucion,
    agregar_valor,
    editar_valor,
    eliminar_valor,
    historial,
    valor_vigente_hoy,
    vigencia_hasta_mostrar,
)
from app.views.form_utils import agregar_ayuda, hacer_redimensionable
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
    def __init__(self, parent=None, parametro_id: int | None = None):
        super().__init__(parent)
        hacer_redimensionable(self)
        # Task 7 (sprint "Parametros: editar/eliminar de usuario"): pasar
        # `parametro_id` conmuta el dialogo a modo edicion -- precarga los
        # campos de la fila existente (_precargar_desde_parametro, al final de
        # este __init__) y hace que guardar() llame a editar_valor() en vez de
        # agregar_valor(). None (por defecto) preserva el comportamiento de
        # creacion de siempre.
        self._parametro_id = parametro_id
        self.setWindowTitle(
            "Editar valor de parametro" if parametro_id else "Agregar valor de parametro"
        )

        self.combo_clave = QComboBox()
        for clave, info in CATALOGO_PARAMETROS.items():
            self.combo_clave.addItem(f"{info.descripcion} ({clave})", userData=clave)

        self.campo_valor = QLineEdit()
        self.campo_vigente_desde = QDateEdit(QDate.currentDate())
        self.campo_vigente_desde.setCalendarPopup(True)
        self.campo_vigente_hasta = QDateEdit(QDate.currentDate())
        self.campo_vigente_hasta.setCalendarPopup(True)
        self.campo_vigente_hasta.setToolTip(
            "Fecha hasta la que este valor rige; solo aplica a parametros con un "
            "rango de vigencia cerrado (ej. tramos historicos de tasas certificadas)."
        )
        self.casilla_indefinido = QCheckBox("Indefinido")
        self.casilla_indefinido.setToolTip(
            "Este parametro requiere una fecha de fin (modo TRAMO_CERRADO) -- no puede "
            "quedar indefinido."
        )
        self._nota_vigente_hasta = QLabel()
        self._nota_vigente_hasta.setWordWrap(True)

        _contenedor_vigente_hasta = QWidget()
        _layout_vigente_hasta = QVBoxLayout(_contenedor_vigente_hasta)
        _layout_vigente_hasta.setContentsMargins(0, 0, 0, 0)
        _fila_fecha_e_indefinido = QHBoxLayout()
        _fila_fecha_e_indefinido.addWidget(self.campo_vigente_hasta)
        _fila_fecha_e_indefinido.addWidget(self.casilla_indefinido)
        _layout_vigente_hasta.addLayout(_fila_fecha_e_indefinido)
        _layout_vigente_hasta.addWidget(self._nota_vigente_hasta)

        # Casillas de area del derecho (Sprint 57): una por AreaDerecho,
        # preseleccionadas segun AREA_UNIDAD_POR_CLAVE cuando cambia la clave
        # elegida (_actualizar_area_unidad_sugeridas), pero editables antes de
        # guardar -- el usuario puede ajustar la propuesta. Guardadas en un
        # dict (no una lista) para poder leer/escribir por AreaDerecho sin
        # depender del orden de iteracion.
        self.casillas_area: dict[AreaDerecho, QCheckBox] = {}
        self._contenedor_areas = QWidget()
        _layout_areas = QVBoxLayout(self._contenedor_areas)
        _layout_areas.setContentsMargins(0, 0, 0, 0)
        for codigo, etiqueta, _habilitada in AREAS_DERECHO:
            casilla = QCheckBox(etiqueta)
            self.casillas_area[AreaDerecho(codigo)] = casilla
            _layout_areas.addWidget(casilla)

        # "Unidad" es un desplegable con las unidades conocidas del catalogo
        # mas un escape hatch "Otros..." para el resto (Sprint "Parametros:
        # editar/eliminar de usuario", Task 5): antes era un QLineEdit libre,
        # lo que permitia errores de tipeo (ej. "COP" vs "cop" vs "pesos")
        # para el mismo significado. El campo de texto _campo_unidad_otros
        # solo se revela cuando se elige "Otros..." (_actualizar_visibilidad_
        # unidad_otros), y campo_unidad.findText(...) devuelve -1 para
        # cualquier valor fuera de la lista fija -- usado tanto para
        # preseleccionar segun la clave (_actualizar_area_unidad_sugeridas)
        # como, en el futuro, para precargar una unidad guardada en modo
        # edicion.
        self.campo_unidad = QComboBox()
        self.campo_unidad.addItems(["%", "COP", "meses", "índice", "veces", "puntos", "Otros..."])
        self._campo_unidad_otros = QLineEdit()
        self._campo_unidad_otros.setPlaceholderText("Escribe la unidad")
        self.campo_unidad.currentTextChanged.connect(self._actualizar_visibilidad_unidad_otros)

        self.campo_usuario = QLineEdit()
        self.campo_motivo = QLineEdit()

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

        # Guardado como atributo (en vez de variable local `layout`) por si
        # otros metodos de la clase necesitan referenciar filas del formulario.
        self._layout_formulario = QFormLayout()
        # Task 6 (sprint "Parametros: editar/eliminar de usuario"): homologa
        # TODOS los campos del formulario a agregar_ayuda -- antes solo
        # "Unidad" (Task 5) y, de sprints previos, "Área(s) del derecho"
        # (envuelta abajo) usaban el icono (i); el resto tenia el tooltip
        # puesto directamente en el widget via .setToolTip(), inconsistente
        # con el resto. Cada .setToolTip() suelto sobre estos widgets se
        # elimino arriba: el tooltip vive ahora solo en el icono devuelto por
        # agregar_ayuda.
        self._contenedor_combo_clave = agregar_ayuda(
            self._layout_formulario,
            "Parametro",
            self.combo_clave,
            tooltip=(
                "Clave del parametro legal a versionar; la descripcion entre parentesis "
                "identifica que mide (ej. 'Tasa de interes civil legal anual "
                "(CIVIL_ANNUAL_RATE)')."
            ),
        )
        self._contenedor_campo_valor = agregar_ayuda(
            self._layout_formulario,
            "Valor",
            self.campo_valor,
            tooltip=(
                "Valor numerico vigente para la clave elegida, en la unidad indicada abajo. "
                "Ejemplo: 6.00 para una tasa del 6%, o 1300000 para un SMLMV en pesos."
            ),
        )
        self._contenedor_campo_vigente_desde = agregar_ayuda(
            self._layout_formulario,
            "Vigente desde",
            self.campo_vigente_desde,
            tooltip=(
                "Fecha desde la que este valor empieza a regir (normalmente la fecha del "
                "decreto o resolucion). Ejemplo: 2024-01-01."
            ),
        )
        self._contenedor_vigente_hasta_con_ayuda = agregar_ayuda(
            self._layout_formulario,
            "Vigente hasta",
            _contenedor_vigente_hasta,
            tooltip=(
                "Fecha hasta la que este valor rige; solo aplica a parametros con un "
                "rango de vigencia cerrado (ej. tramos historicos de tasas certificadas)."
            ),
        )
        self._contenedor_areas_con_ayuda = agregar_ayuda(
            self._layout_formulario,
            "Área(s) del derecho",
            self._contenedor_areas,
            tooltip=(
                "Area(s) del derecho a las que aplica este valor (puede marcar varias). Se "
                "preselecciona segun la clave elegida. Para un valor de fabrica no se puede "
                "editar despues de guardar; para uno que agregues tu, si podras editarla "
                "despues desde el historial (boton Editar)."
            ),
        )
        # "Unidad" recibe el icono (i) explicito (Sprint 59, helper compartido
        # agregar_ayuda): se pre-rellena segun la clave elegida
        # (_actualizar_area_unidad_sugeridas), asi que el icono deja claro que es una
        # propuesta editable, no un valor fijo -- mismo patron que "Tasa efectiva
        # anual" en ObligacionFormDialog para un campo con valor por defecto.
        # El contenedor agrupa el desplegable y el campo "Otros..." (oculto salvo
        # que se elija esa opcion) para que ambos viajen juntos como un solo
        # widget de fila (Task 5) -- agregar_ayuda no necesita saber que hay dos
        # controles adentro, solo envuelve lo que se le pase.
        _contenedor_unidad_y_otros = QWidget()
        _layout_unidad_y_otros = QVBoxLayout(_contenedor_unidad_y_otros)
        _layout_unidad_y_otros.setContentsMargins(0, 0, 0, 0)
        _layout_unidad_y_otros.addWidget(self.campo_unidad)
        _layout_unidad_y_otros.addWidget(self._campo_unidad_otros)
        self._campo_unidad_otros.setVisible(False)
        self._contenedor_campo_unidad = agregar_ayuda(
            self._layout_formulario,
            "Unidad",
            _contenedor_unidad_y_otros,
            tooltip=(
                "Unidad de medida del valor, sugerida automaticamente segun la clave "
                "elegida. Si no aparece en la lista, elige 'Otros...' y escribela. Para "
                "un valor de fabrica no se puede editar despues de guardar; para uno que "
                "agregues tu, si podras editarla despues desde el historial."
            ),
            ejemplo="%, COP, meses, índice",
        )
        self._contenedor_campo_usuario = agregar_ayuda(
            self._layout_formulario,
            "Usuario",
            self.campo_usuario,
            tooltip=(
                "Nombre de quien registra este valor, para la bitacora de auditoria del "
                "parametro. Los valores de fabrica quedan protegidos para siempre; un "
                "valor que agregues tu si podras editarlo o eliminarlo despues desde el "
                "historial."
            ),
        )
        self._contenedor_campo_motivo = agregar_ayuda(
            self._layout_formulario,
            "Motivo (opcional)",
            self.campo_motivo,
            tooltip=(
                "Justificacion o fuente del cambio, para dejar constancia del porque de "
                "este valor. Ejemplo: 'Decreto 2613 de 2023, ajuste SMLMV 2024'."
            ),
        )
        self._layout_formulario.addRow(self.boton_guardar)
        self.setLayout(self._layout_formulario)

        self.combo_clave.currentIndexChanged.connect(self._actualizar_visibilidad_vigente_hasta)
        self.combo_clave.currentIndexChanged.connect(self._actualizar_area_unidad_sugeridas)
        self._actualizar_visibilidad_vigente_hasta()
        self._actualizar_area_unidad_sugeridas()

        if parametro_id is not None:
            self._precargar_desde_parametro(parametro_id)

    def _precargar_desde_parametro(self, parametro_id: int) -> None:
        """Precarga todos los campos del formulario desde una `ParametroLegal`
        ya guardada (Task 7) -- espejo, campo por campo, de lo que guardar()
        ya lee del formulario para construir los kwargs de editar_valor().
        Se llama una sola vez, al final de __init__, despues de que
        _actualizar_area_unidad_sugeridas() ya corrio (disparada por el
        combo_clave.setCurrentIndex() de abajo) para poder pisar su propuesta
        automatica con los valores REALES ya guardados en la fila -- mismo
        orden de "override" que usa ObligacionFormDialog._precargar_desde_obligacion
        (el manejo de la sesion en si difiere: aqui se extraen los campos y se
        cierra la sesion antes de tocar los widgets, en vez de mantenerla
        abierta mientras se pueblan). La clave (`clave`) no es editable en
        modo edicion (editar_valor() no la recibe), asi que combo_clave se
        deshabilita tras fijar su valor."""
        session = session_module.get_session()
        try:
            fila = session.get(ParametroLegal, parametro_id)
            clave, valor, vigente_desde = fila.clave, fila.valor, fila.vigente_desde
            vigente_hasta, usuario, motivo = fila.vigente_hasta, fila.usuario, fila.motivo
            unidad, areas = fila.unidad, deserializar_areas(fila.areas_derecho or "[]")
        finally:
            session.close()

        self.combo_clave.setCurrentIndex(self.combo_clave.findData(clave))
        self.combo_clave.setEnabled(False)
        self.campo_valor.setText(str(valor))
        self.campo_vigente_desde.setDate(
            QDate(vigente_desde.year, vigente_desde.month, vigente_desde.day)
        )
        if vigente_hasta is not None:
            self.campo_vigente_hasta.setDate(
                QDate(vigente_hasta.year, vigente_hasta.month, vigente_hasta.day)
            )
        self.campo_usuario.setText(usuario)
        self.campo_motivo.setText(motivo or "")
        areas_set = set(areas)
        for area, casilla in self.casillas_area.items():
            casilla.setChecked(area in areas_set)
        if unidad is not None:
            indice_unidad = self.campo_unidad.findText(unidad)
            if indice_unidad >= 0:
                self.campo_unidad.setCurrentIndex(indice_unidad)
            else:
                self.campo_unidad.setCurrentText("Otros...")
                self._campo_unidad_otros.setText(unidad)

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
        indice_unidad = self.campo_unidad.findText(unidad_sugerida)
        self.campo_unidad.setCurrentIndex(indice_unidad if indice_unidad >= 0 else 0)

    def _actualizar_visibilidad_unidad_otros(self, texto: str) -> None:
        """Revela `_campo_unidad_otros` solo cuando se elige 'Otros...' en el
        desplegable -- escape hatch para unidades fuera de la lista fija
        (Task 5)."""
        self._campo_unidad_otros.setVisible(texto == "Otros...")

    def _actualizar_visibilidad_vigente_hasta(self) -> None:
        """Nombre del método sin cambios (evita re-cablear sus 2 call sites:
        __init__ y combo_clave.currentIndexChanged), pero el comportamiento sí
        cambió (Sprint "Parametros: editar/eliminar de usuario"): la fila
        "Vigente hasta" ya NO se oculta según el modo -- se deshabilita, con
        una nota explicando por qué,
        para que el usuario entienda la regla en vez de ver el campo
        desaparecer sin explicación. `casilla_indefinido` (TRAMO_CERRADO)
        queda siempre deshabilitada porque ese modo siempre exige una fecha
        real (agregar_valor la rechaza si falta) -- existe solo para que las
        3 combinaciones de modo compartan un mismo patrón visual (campo +
        nota), no porque hoy sea usable."""
        clave = self.combo_clave.currentData()
        info = CATALOGO_PARAMETROS[clave]
        es_tramo_cerrado = info.modo == ModoResolucion.TRAMO_CERRADO
        self.campo_vigente_hasta.setEnabled(es_tramo_cerrado)
        self.casilla_indefinido.setEnabled(False)
        if es_tramo_cerrado:
            self._nota_vigente_hasta.setText("")
        else:
            self._nota_vigente_hasta.setText(
                f"Este parámetro no vence en una fecha fija (modo {info.modo.value}) — "
                "el valor rige indefinidamente hasta que se cargue uno nuevo con una "
                "fecha 'Vigente desde' posterior."
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
        if self.campo_unidad.currentText() == "Otros...":
            unidad = self._campo_unidad_otros.text().strip()
        else:
            unidad = self.campo_unidad.currentText()

        if self._parametro_id is not None:
            return editar_valor(
                self._parametro_id,
                valor=valor,
                vigente_desde=vigente_desde,
                usuario=usuario,
                areas_derecho=areas_derecho,
                unidad=unidad,
                motivo=motivo,
                vigente_hasta=vigente_hasta,
            )
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

        # Task 8 (sprint "Parametros: editar/eliminar de usuario"): 2 columnas
        # finales, Editar/Eliminar, agregadas SIEMPRE despues de la columna
        # opcional de dato crudo (si la clave la tiene) -- los indices se
        # calculan una sola vez aqui (self._indice_columna_editar/eliminar) en
        # vez de hardcodear 5/6 en _refrescar(), para que la posicion siga
        # siendo correcta tanto para claves con dato crudo (6 columnas antes +
        # estas 2 = indices 6/7) como sin el (5 columnas antes + estas 2 =
        # indices 5/6).
        columnas = ["Valor", "Vigente desde", "Vigente hasta", "Usuario", "Motivo"]
        if etiqueta_columna_cruda is not None:
            columnas = [*columnas, etiqueta_columna_cruda]
        columnas = [*columnas, "Editar", "Eliminar"]
        self._indice_columna_editar = len(columnas) - 2
        self._indice_columna_eliminar = len(columnas) - 1
        self.tabla = QTableWidget(0, len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self._clave = clave
        self._info = info
        self._clave_cruda = clave_cruda
        self._variacion_por_anio: dict[int, str] = {}
        if clave_cruda is not None:
            self._variacion_por_anio = {
                fila_cruda.vigente_desde.year: str(fila_cruda.valor)
                for fila_cruda in historial(clave_cruda)
            }
        self._refrescar()

        layout = QVBoxLayout()
        layout.addWidget(self.tabla)
        if formula_texto is not None:
            nota_formula = QLabel(formula_texto)
            nota_formula.setWordWrap(True)
            layout.addWidget(nota_formula)
        self.setLayout(layout)

    def _refrescar(self) -> None:
        """Repuebla `self.tabla` desde cero (historial(self._clave)) --
        extraido de __init__ (Task 8) para que _editar_valor/_eliminar_valor
        puedan refrescar la tabla in place tras actuar sobre una fila, sin
        cerrar y reabrir el dialogo."""
        filas = historial(self._clave)
        self.tabla.setRowCount(len(filas))
        for fila_idx, fila in enumerate(filas):
            self.tabla.setItem(fila_idx, 0, QTableWidgetItem(str(fila.valor)))
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(fila.vigente_desde.isoformat()))
            self.tabla.setItem(
                fila_idx, 2, QTableWidgetItem(vigencia_hasta_mostrar(fila, self._info))
            )
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(fila.usuario))
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(fila.motivo or ""))
            if self._clave_cruda is not None:
                variacion = self._variacion_por_anio.get(fila.vigente_desde.year, "")
                self.tabla.setItem(fila_idx, 5, QTableWidgetItem(variacion))
            # QTableWidget.setRowCount(N) con el mismo N que ya tenia NO limpia
            # los cellWidget existentes de filas que conservan su indice --
            # solo setCellWidget(nueva_widget) los reemplaza. historial()
            # ordena por vigente_desde descendente, asi que editar la fecha de
            # una fila de usuario puede cambiar su posicion relativa a otra
            # fila (incluida una de sistema) entre dos llamadas a
            # _refrescar(). Sin este removeCellWidget explicito, una fila de
            # sistema que hereda el indice que antes ocupaba una fila de
            # usuario con botones quedaria mostrando esos botones "fantasma"
            # -- justo la fuga que el gate de abajo busca evitar. Se limpia
            # incondicionalmente ANTES de decidir si esta fila (la actual en
            # este indice) merece botones nuevos.
            self.tabla.removeCellWidget(fila_idx, self._indice_columna_editar)
            self.tabla.removeCellWidget(fila_idx, self._indice_columna_eliminar)
            # REQUISITO DE SEGURIDAD (Task 8): esta condicion es la unica
            # puerta que decide si una fila recibe los botones Editar/Eliminar
            # -- una fila sembrada por el sistema (creado_por_sistema=True)
            # jamas debe entrar aqui. Es defensa en profundidad sobre la
            # verdadera barrera (editar_valor()/eliminar_valor() en
            # parametro_service.py, Task 3, que rechazan tocar filas de
            # sistema con ValueError incluso si esta condicion tuviera un
            # bug) -- pero un usuario no deberia ni VER el boton junto a una
            # fila de sistema.
            if not fila.creado_por_sistema:
                boton_editar = QPushButton("Editar")
                boton_editar.setProperty("class", "secondary")
                boton_editar.clicked.connect(
                    lambda _checked=False, id_=fila.id: self._editar_valor(id_)
                )
                self.tabla.setCellWidget(fila_idx, self._indice_columna_editar, boton_editar)

                boton_eliminar = QPushButton("Eliminar")
                boton_eliminar.setIcon(icon("delete"))
                boton_eliminar.setProperty("class", "destructive")
                boton_eliminar.clicked.connect(
                    lambda _checked=False, id_=fila.id: self._eliminar_valor(id_)
                )
                self.tabla.setCellWidget(fila_idx, self._indice_columna_eliminar, boton_eliminar)

    def _editar_valor(self, parametro_id: int) -> None:
        """Abre ParametroFormDialog en modo edicion (Task 7) para esta fila; si
        el usuario guarda (exec() devuelve True/Accepted), refresca la tabla
        para reflejar el cambio sin cerrar HistorialParametroDialog."""
        dialogo = ParametroFormDialog(self, parametro_id=parametro_id)
        if dialogo.exec():
            self._refrescar()

    def _eliminar_valor(self, parametro_id: int) -> None:
        """Pide confirmacion (QMessageBox.question) antes de borrar -- accion
        irreversible. eliminar_valor() (Task 3) ya rechaza filas de sistema
        con ValueError, pero esta fila nunca deberia llegar aqui porque
        _refrescar() no le crea el boton Eliminar en primer lugar."""
        respuesta = QMessageBox.question(
            self,
            "Eliminar valor de parámetro",
            "¿Eliminar este valor de parámetro? Esta acción no se puede deshacer.",
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        eliminar_valor(parametro_id)
        self._refrescar()


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
        # Task 6 (sprint "Parametros: editar/eliminar de usuario"): tooltip
        # por columna, en el mismo orden que `columnas` arriba -- homologa la
        # tabla resumen con los iconos (i) del formulario (agregar_ayuda).
        _tooltips_columnas = [
            "Grupo temático del parámetro (Topes legales, Plazos de prescripción y "
            "caducidad, Indicadores históricos, Seguridad social).",
            "Nombre del parámetro legal versionado.",
            "Valor resuelto para la fecha de hoy, según el modo de resolución de la clave.",
            "Fecha desde la que rige el valor vigente hoy.",
            "Fecha hasta la que rige el valor vigente hoy (o 'Indefinido' si no aplica).",
            "Área(s) del derecho a las que aplica este parámetro.",
            "Unidad de medida del valor (%, COP, meses, índice, veces, puntos).",
        ]
        for indice, texto in enumerate(_tooltips_columnas):
            self.tabla.horizontalHeaderItem(indice).setToolTip(texto)
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
        # Task 8: siempre refresca la tabla resumen al cerrar el historial --
        # el dialogo pudo haber editado/eliminado filas de usuario mientras
        # estuvo abierto (Editar/Eliminar por fila); refrescar
        # incondicionalmente es lo mas simple y correcto (evita rastrear si
        # algo cambio realmente adentro).
        HistorialParametroDialog(clave, self).exec()
        self.refrescar()
