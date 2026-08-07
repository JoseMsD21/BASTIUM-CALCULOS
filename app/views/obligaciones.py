from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.constants import (
    CATEGORIAS_CIVIL_FAMILIA,
    CATEGORIAS_COMERCIAL,
    CATEGORIAS_HONORARIOS,
    CATEGORIAS_LABORAL,
    CATEGORIAS_SANCIONATORIO,
    CATEGORIAS_TRIBUTARIO,
)
from app.views.icons import icon
from database.models import Expediente, Obligacion, TipoObligacion


class ObligacionFormDialog(QDialog):
    # Campos condicionales por area que `Obligacion` siempre espera recibir (aunque sea
    # en None) -- cada `_parse_campos_<area>()` solo devuelve las claves que esa area
    # necesita sobreescribir; el resto queda en su valor por defecto de aqui (Sprint 22,
    # deduplicacion de guardar()).
    _CAMPOS_AREA_POR_DEFECTO = {
        "tasa_moratoria_anual": None,
        "fecha_vencimiento": None,
        "ibc_vigente_anual": None,
        "cantidad_smlmv_uvt": None,
        "honorarios_fijos_pactados": None,
        "cuota_litis_pactada_pct": None,
        "beneficio_obtenido": None,
        "costas_pct_manual": None,
        "moneda": "COP",
        "trm_aplicable": None,
        "trm_fecha_referencia": None,
        "anatocismo_demanda_judicial": False,
        "anatocismo_fecha_acuerdo": None,
    }

    def __init__(self, expediente_id: int, area: str = "CIVIL_FAMILIA", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar obligacion")
        self._expediente_id = expediente_id
        self._area = area
        self._iconos_advertencia: dict[QLineEdit, QLabel] = {}

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("Puntual", userData="PUNTUAL")
        if self._area not in ("SANCIONATORIO", "HONORARIOS", "LABORAL", "TRIBUTARIO"):
            # Una multa, un cobro de honorarios o una liquidacion de contrato laboral
            # es siempre un hecho puntual (ver SancionatorioStrategy/HonorariosStrategy/
            # LaboralStrategy en area_strategy.py, que rechazan RECURRENTE con ValueError)
            # -- no se ofrece la opcion en estas areas.
            self.combo_tipo.addItem("Recurrente", userData="RECURRENTE")

        self.combo_categoria = QComboBox()
        categorias_por_area = {
            "COMERCIAL": CATEGORIAS_COMERCIAL,
            "SANCIONATORIO": CATEGORIAS_SANCIONATORIO,
            "HONORARIOS": CATEGORIAS_HONORARIOS,
            "LABORAL": CATEGORIAS_LABORAL,
            "TRIBUTARIO": CATEGORIAS_TRIBUTARIO,
        }
        categorias = categorias_por_area.get(self._area, CATEGORIAS_CIVIL_FAMILIA)
        for codigo, etiqueta in categorias:
            self.combo_categoria.addItem(etiqueta, userData=codigo)

        self.campo_concepto = QLineEdit()
        self.campo_concepto.setToolTip(
            "Descripcion corta de la obligacion (ej. 'Cuota alimentaria noviembre 2025')."
        )
        self.campo_valor = QLineEdit()
        self.campo_valor.setToolTip(
            "Monto en pesos (o en la moneda elegida) sobre el que se calculan los intereses."
        )
        self.campo_tasa = QLineEdit("6.00")
        self.campo_tasa.setToolTip(
            "Tasa de interes pactada o aplicable, en porcentaje efectivo anual (%EA)."
        )

        self.campo_fecha_origen = QDateEdit(QDate.currentDate())
        self.campo_fecha_origen.setCalendarPopup(True)

        self.campo_fecha_inicio = QDateEdit(QDate.currentDate())
        self.campo_fecha_inicio.setCalendarPopup(True)
        self.campo_dia_pago = QSpinBox()
        self.campo_dia_pago.setRange(1, 28)
        self.campo_dia_pago.setValue(5)

        self.campo_tasa_moratoria = QLineEdit("24.00")
        self.campo_tasa_moratoria.setToolTip(
            "Tasa de interes que se cobra automaticamente despues del vencimiento (mora), "
            "en porcentaje efectivo anual."
        )
        self.campo_fecha_vencimiento = QDateEdit(QDate.currentDate())
        self.campo_fecha_vencimiento.setCalendarPopup(True)
        self.campo_ibc_vigente = QLineEdit()
        self.campo_ibc_vigente.setToolTip(
            "Interes Bancario Corriente vigente certificado por la Superfinanciera, usado "
            "para el tope de usura (Art. 884 C.Co.)."
        )
        self.check_anatocismo_demanda_judicial = QCheckBox(
            "Demanda judicial (habilita anatocismo, Art. 886 C.Co.)"
        )
        self.check_anatocismo_demanda_judicial.setToolTip(
            "El anatocismo (interes sobre interes) solo aplica en materia comercial si hay "
            "una demanda judicial en curso."
        )
        self.check_anatocismo_acuerdo = QCheckBox("¿Hay acuerdo posterior de capitalización?")
        self.campo_anatocismo_fecha_acuerdo = QDateEdit(QDate.currentDate())
        self.campo_anatocismo_fecha_acuerdo.setCalendarPopup(True)

        self.combo_moneda = QComboBox()
        self.combo_moneda.addItem("COP (peso colombiano)", userData="COP")
        self.combo_moneda.addItem("USD (dolar)", userData="USD")
        self.campo_trm_aplicable = QLineEdit()
        self.campo_trm_aplicable.setToolTip(
            "Tasa Representativa del Mercado (COP por USD) aplicable en la fecha de referencia."
        )
        self.campo_trm_fecha_referencia = QDateEdit(QDate.currentDate())
        self.campo_trm_fecha_referencia.setCalendarPopup(True)

        self.campo_cantidad_smlmv_uvt = QLineEdit()
        self.campo_cantidad_smlmv_uvt.setToolTip(
            "Cantidad de Salarios Minimos Legales Mensuales Vigentes (SMLMV) o Unidades de "
            "Valor Tributario (UVT) sobre la que se calcula la multa."
        )

        self.campo_honorarios_fijos = QLineEdit()
        self.campo_cuota_litis_pct = QLineEdit()
        self.campo_cuota_litis_pct.setToolTip(
            "Porcentaje del beneficio obtenido por el cliente pactado como honorarios "
            "(cuota litis), entre 0% y 100%."
        )
        self.campo_beneficio_obtenido = QLineEdit()
        self.campo_costas_pct = QLineEdit()
        self.campo_costas_pct.setToolTip(
            "Porcentaje adicional por costas judiciales a cargo de la parte vencida, si se "
            "pacto o decreto."
        )
        self.check_aplica_indexacion_ipc = QCheckBox("Aplica indexación IPC (corrección monetaria)")
        self.check_aplica_indexacion_ipc.setToolTip(
            "Corrige el valor historico de la obligacion con el Indice de Precios al "
            "Consumidor (IPC) antes de calcular intereses."
        )
        self.check_interes_sobre_capital_indexado = QCheckBox(
            "Interés sobre capital ya indexado (algoritmo Suma Única / Ley 80 de 1993)"
        )
        self.check_interes_sobre_capital_indexado.setToolTip(
            "Calcula el interes sobre el capital ya indexado, en vez de sobre el capital "
            "historico (algoritmo de Suma Unica, Ley 80 de 1993)."
        )

        self.campo_base_sancion = QLineEdit()
        self.campo_meses_extemporaneidad = QSpinBox()
        self.campo_meses_extemporaneidad.setRange(1, 120)
        self.campo_meses_extemporaneidad.setValue(1)
        self.check_sancion_agravada = QCheckBox("Agravada (omision de activos o pasivos inexistentes)")
        self.campo_ingresos_brutos = QLineEdit()
        self.campo_devoluciones = QLineEdit()
        self.campo_costos = QLineEdit()
        self.campo_deducciones = QLineEdit()
        self.campo_rentas_exentas = QLineEdit()

        self.campo_fecha_fin = QDateEdit(QDate.currentDate())
        self.campo_fecha_fin.setCalendarPopup(True)
        self.check_pagada = QCheckBox("Prestaciones pagadas")
        self.campo_fecha_pago_total = QDateEdit(QDate.currentDate())
        self.campo_fecha_pago_total.setCalendarPopup(True)
        self.check_incluir_seguridad_social = QCheckBox("Incluir cotizaciones de seguridad social no pagadas")
        self.combo_nivel_riesgo_arl = QComboBox()
        for nivel in ("I", "II", "III", "IV", "V"):
            self.combo_nivel_riesgo_arl.addItem(f"Nivel {nivel}", userData=nivel)
        self.combo_nivel_riesgo_arl.setToolTip(
            "Nivel de riesgo laboral asignado por la ARL (I a V), usado para calcular el "
            "aporte de riesgos laborales no pagado."
        )

        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
        # Ctrl+S = guardar (Sprint 32). Esc = cancelar ya viene gratis de
        # QDialog.keyPressEvent() (reject() por defecto) -- no requiere codigo aqui.
        self.atajo_guardar = QShortcut(QKeySequence("Ctrl+S"), self)
        self.atajo_guardar.activated.connect(self._guardar_y_cerrar)

        # --- Reorganizacion en secciones colapsables (Sprint 34) -- 3 QGroupBox
        # checkeables en vez del unico QFormLayout plano de antes: agrupan los ~15
        # campos por proposito ("Datos basicos" siempre visible; "Tasas e intereses"
        # y "Honorarios y costas" se ocultan por completo si el area no los usa mas
        # abajo). Colapsar un grupo (desmarcar su checkbox de titulo) solo oculta su
        # contenido -- nunca borra lo ya digitado.
        self.grupo_datos_basicos = QGroupBox("Datos básicos")
        self.grupo_datos_basicos.setCheckable(True)
        self.grupo_datos_basicos.setChecked(True)
        contenido_datos_basicos = QWidget()
        self.layout_datos_basicos = QFormLayout(contenido_datos_basicos)
        layout_grupo_datos_basicos = QVBoxLayout(self.grupo_datos_basicos)
        layout_grupo_datos_basicos.addWidget(contenido_datos_basicos)
        self.grupo_datos_basicos.toggled.connect(contenido_datos_basicos.setVisible)

        self.grupo_tasas_intereses = QGroupBox("Tasas e intereses")
        self.grupo_tasas_intereses.setCheckable(True)
        self.grupo_tasas_intereses.setChecked(True)
        contenido_tasas_intereses = QWidget()
        self.layout_tasas_intereses = QFormLayout(contenido_tasas_intereses)
        layout_grupo_tasas_intereses = QVBoxLayout(self.grupo_tasas_intereses)
        layout_grupo_tasas_intereses.addWidget(contenido_tasas_intereses)
        self.grupo_tasas_intereses.toggled.connect(contenido_tasas_intereses.setVisible)

        self.grupo_honorarios_costas = QGroupBox("Honorarios y costas")
        self.grupo_honorarios_costas.setCheckable(True)
        self.grupo_honorarios_costas.setChecked(True)
        contenido_honorarios_costas = QWidget()
        self.layout_honorarios_costas = QFormLayout(contenido_honorarios_costas)
        layout_grupo_honorarios_costas = QVBoxLayout(self.grupo_honorarios_costas)
        layout_grupo_honorarios_costas.addWidget(contenido_honorarios_costas)
        self.grupo_honorarios_costas.toggled.connect(contenido_honorarios_costas.setVisible)

        # Concepto/Valor/Tasa se envuelven con iconos de advertencia (y, para Tasa,
        # tambien un icono informativo del valor por defecto) -- ver
        # _envolver_campo_con_iconos. A partir de aqui, ocultar/mostrar la FILA de
        # Valor/Tasa segun el area debe apuntar al contenedor devuelto, no al
        # QLineEdit interno (que solo controla su propia visibilidad, no la del
        # icono que lo acompaña).
        self._contenedor_campo_concepto = self._envolver_campo_con_iconos(self.campo_concepto)
        self._contenedor_campo_valor = self._envolver_campo_con_iconos(self.campo_valor)
        self._contenedor_campo_tasa = self._envolver_campo_con_iconos(
            self.campo_tasa,
            icono_info="info",
            tooltip_info="Valor por defecto: interés civil legal, Art. 1617 C.C.",
        )

        self.layout_datos_basicos.addRow("Tipo", self.combo_tipo)
        self.layout_datos_basicos.addRow("Categoria", self.combo_categoria)
        self.layout_datos_basicos.addRow("Concepto", self._contenedor_campo_concepto)
        self.layout_datos_basicos.addRow("Valor", self._contenedor_campo_valor)
        self.layout_datos_basicos.addRow("Fecha de origen (Puntual)", self.campo_fecha_origen)
        self.label_fecha_origen = self.layout_datos_basicos.labelForField(self.campo_fecha_origen)
        self.layout_datos_basicos.addRow("Fecha de inicio (Recurrente)", self.campo_fecha_inicio)
        self.layout_datos_basicos.addRow("Dia de pago (Recurrente)", self.campo_dia_pago)
        self.layout_datos_basicos.addRow(
            "Cantidad SMLMV/UVT (Sancionatorio)", self.campo_cantidad_smlmv_uvt
        )
        self.layout_datos_basicos.addRow(
            "Base de la sancion (impuesto a cargo o diferencia)", self.campo_base_sancion
        )
        self.layout_datos_basicos.addRow(
            "Meses o fraccion de atraso (extemporaneidad)", self.campo_meses_extemporaneidad
        )
        self.layout_datos_basicos.addRow(self.check_sancion_agravada)
        self.layout_datos_basicos.addRow("Ingresos brutos (Renta liquida)", self.campo_ingresos_brutos)
        self.layout_datos_basicos.addRow(
            "Devoluciones/rebajas/descuentos (Renta liquida)", self.campo_devoluciones
        )
        self.layout_datos_basicos.addRow("Costos (Renta liquida)", self.campo_costos)
        self.layout_datos_basicos.addRow("Deducciones (Renta liquida)", self.campo_deducciones)
        self.layout_datos_basicos.addRow("Rentas exentas (Renta liquida)", self.campo_rentas_exentas)
        self.layout_datos_basicos.addRow("Fecha de terminacion de contrato", self.campo_fecha_fin)
        self.layout_datos_basicos.addRow(self.check_pagada)
        self.layout_datos_basicos.addRow("Fecha de pago real", self.campo_fecha_pago_total)
        self.layout_datos_basicos.addRow(self.check_incluir_seguridad_social)
        self.layout_datos_basicos.addRow("Nivel de riesgo ARL", self.combo_nivel_riesgo_arl)

        self.layout_tasas_intereses.addRow("Tasa efectiva anual (%)", self._contenedor_campo_tasa)
        self.layout_tasas_intereses.addRow("Tasa moratoria anual (%)", self.campo_tasa_moratoria)
        self.layout_tasas_intereses.addRow("Fecha de vencimiento", self.campo_fecha_vencimiento)
        self.layout_tasas_intereses.addRow("IBC vigente aplicable (%)", self.campo_ibc_vigente)
        self.layout_tasas_intereses.addRow(self.check_anatocismo_demanda_judicial)
        self.layout_tasas_intereses.addRow(self.check_anatocismo_acuerdo)
        self.layout_tasas_intereses.addRow(
            "Fecha del acuerdo posterior", self.campo_anatocismo_fecha_acuerdo
        )
        self.layout_tasas_intereses.addRow("Moneda", self.combo_moneda)
        self.layout_tasas_intereses.addRow("TRM aplicable (COP por USD)", self.campo_trm_aplicable)
        self.layout_tasas_intereses.addRow(
            "Fecha de referencia de la TRM", self.campo_trm_fecha_referencia
        )
        self.layout_tasas_intereses.addRow(self.check_aplica_indexacion_ipc)
        self.layout_tasas_intereses.addRow(self.check_interes_sobre_capital_indexado)

        self.layout_honorarios_costas.addRow(
            "Honorarios fijos pactados", self.campo_honorarios_fijos
        )
        self.layout_honorarios_costas.addRow("% Cuota litis pactada", self.campo_cuota_litis_pct)
        self.layout_honorarios_costas.addRow(
            "Beneficio obtenido por el cliente", self.campo_beneficio_obtenido
        )
        self.layout_honorarios_costas.addRow(
            "% Costas judiciales (opcional)", self.campo_costas_pct
        )

        layout_principal = QVBoxLayout()
        layout_principal.addWidget(self.grupo_datos_basicos)
        layout_principal.addWidget(self.grupo_tasas_intereses)
        layout_principal.addWidget(self.grupo_honorarios_costas)
        layout_principal.addWidget(self.boton_guardar)
        self.setLayout(layout_principal)

        es_comercial = self._area == "COMERCIAL"
        es_sancionatorio = self._area == "SANCIONATORIO"
        es_honorarios = self._area == "HONORARIOS"
        es_laboral = self._area == "LABORAL"
        es_tributario = self._area == "TRIBUTARIO"

        self.campo_tasa_moratoria.setVisible(es_comercial)
        self.campo_fecha_vencimiento.setVisible(es_comercial)
        self.campo_ibc_vigente.setVisible(es_comercial)
        self.combo_moneda.setVisible(es_comercial)

        self.campo_cantidad_smlmv_uvt.setVisible(es_sancionatorio)

        self.campo_honorarios_fijos.setVisible(es_honorarios)
        self.campo_cuota_litis_pct.setVisible(es_honorarios)
        self.campo_beneficio_obtenido.setVisible(es_honorarios)
        self.campo_costas_pct.setVisible(es_honorarios)

        self.check_aplica_indexacion_ipc.setVisible(self._area == "CIVIL_FAMILIA")
        self.check_interes_sobre_capital_indexado.setVisible(self._area == "CIVIL_FAMILIA")

        # "Valor" no aplica a Sancionatorio/Honorarios/Tributario (salvo IMPUESTO_A_CARGO,
        # ver _actualizar_campos_tributario): el monto se calcula a partir de otros campos.
        # Se oculta el CONTENEDOR (campo + iconos), no el QLineEdit directamente, para que
        # el icono de advertencia tambien desaparezca junto con la fila.
        self._contenedor_campo_valor.setVisible(
            not es_sancionatorio and not es_honorarios and not es_tributario
        )

        # Laboral y Tributario son siempre PUNTUAL y no usan tasa efectiva anual pactada
        # (Tributario: el interes es automatico, E.T. art. 635, nunca se pacta).
        self.combo_tipo.setVisible(not es_laboral and not es_tributario)
        self._contenedor_campo_tasa.setVisible(not es_laboral and not es_tributario)
        self.campo_fecha_fin.setVisible(es_laboral)
        self.check_pagada.setVisible(es_laboral)
        self.check_incluir_seguridad_social.setVisible(es_laboral)
        self.combo_nivel_riesgo_arl.setVisible(False)

        self.campo_base_sancion.setVisible(False)
        self.campo_meses_extemporaneidad.setVisible(False)
        self.check_sancion_agravada.setVisible(False)
        self.campo_ingresos_brutos.setVisible(False)
        self.campo_devoluciones.setVisible(False)
        self.campo_costos.setVisible(False)
        self.campo_deducciones.setVisible(False)
        self.campo_rentas_exentas.setVisible(False)

        # Secciones enteras que no aplican al area elegida quedan completamente
        # ocultas (Sprint 34) en vez de mostrar un grupo con todos sus campos
        # individualmente invisibles -- menos ruido visual para un abogado sin
        # conocimiento tecnico. "Datos basicos" siempre aplica, no se oculta nunca.
        self.grupo_tasas_intereses.setVisible(not es_laboral and not es_tributario)
        self.grupo_honorarios_costas.setVisible(es_honorarios)

        # campo_fecha_origen se reutiliza en Laboral como "fecha de inicio del contrato"
        # (ver _actualizar_campos_visibles) -- se ajusta la etiqueta del formulario para
        # que no diga "(Puntual)" en esa area.
        if self.label_fecha_origen is not None:
            self.label_fecha_origen.setText(
                "Fecha de inicio del contrato" if es_laboral else "Fecha de origen (Puntual)"
            )

        # Los connect() de señales que disparan _actualizar_campos_visibles se hacen aqui,
        # al final de __init__, para garantizar que todos los widgets que ese metodo
        # referencia (incluyendo los de Laboral: check_pagada, campo_fecha_pago_total)
        # ya existen antes de que la señal pueda dispararse.
        self.combo_tipo.currentIndexChanged.connect(self._actualizar_campos_visibles)
        self.check_pagada.stateChanged.connect(self._actualizar_campos_visibles)
        self.check_incluir_seguridad_social.stateChanged.connect(self._actualizar_campos_visibles)
        self.check_anatocismo_acuerdo.stateChanged.connect(self._actualizar_campos_visibles)
        self.combo_moneda.currentIndexChanged.connect(self._actualizar_visibilidad_trm)
        self.combo_categoria.currentIndexChanged.connect(self._actualizar_campos_tributario)

        # Feedback de validacion en tiempo real (Sprint 34): reutiliza los mismos
        # helpers de validacion del Sprint 24 (_validar_concepto_no_vacio,
        # _validar_rango) en vez de duplicar las reglas -- solo cambia que aqui se
        # capturan por campo individual mientras el usuario escribe, en vez de
        # dejar que revienten unicamente al presionar Guardar.
        self.campo_concepto.textChanged.connect(self._validar_concepto_en_tiempo_real)
        self.campo_valor.textChanged.connect(self._validar_valor_en_tiempo_real)
        self.campo_tasa.textChanged.connect(self._validar_tasa_en_tiempo_real)

        self._actualizar_campos_visibles()
        self._actualizar_visibilidad_trm()
        self._actualizar_campos_tributario()
        self._fijar_orden_de_tabulacion()

    def _fijar_orden_de_tabulacion(self) -> None:
        """Encadena el orden de tabulacion explicitamente (Sprint 37) siguiendo el
        orden visual de arriba hacia abajo de cada seccion (mismo orden en que se
        llamo addRow() mas arriba). Sin esto, Tab salta a los QGroupBox colapsables
        (son checkable, por lo tanto focusable) en vez de entrar a "Tasas e intereses"
        u "Honorarios y costas" -- QFormLayout encadena el tab order automaticamente
        entre filas de un mismo layout, pero no hay encadenamiento automatico ENTRE
        los 3 QFormLayout separados de las 3 secciones colapsables (Sprint 34). El
        orden completo se fija una sola vez, incluyendo campos que solo aplican a
        otras areas: al tabular de verdad, Qt salta los widgets ocultos y usa el
        siguiente visible en esta misma secuencia, asi que sirve para cualquier area.
        """
        orden = [
            self.combo_tipo,
            self.combo_categoria,
            self.campo_concepto,
            self.campo_valor,
            self.campo_fecha_origen,
            self.campo_fecha_inicio,
            self.campo_dia_pago,
            self.campo_cantidad_smlmv_uvt,
            self.campo_base_sancion,
            self.campo_meses_extemporaneidad,
            self.check_sancion_agravada,
            self.campo_ingresos_brutos,
            self.campo_devoluciones,
            self.campo_costos,
            self.campo_deducciones,
            self.campo_rentas_exentas,
            self.campo_fecha_fin,
            self.check_pagada,
            self.campo_fecha_pago_total,
            self.check_incluir_seguridad_social,
            self.combo_nivel_riesgo_arl,
            self.campo_tasa,
            self.campo_tasa_moratoria,
            self.campo_fecha_vencimiento,
            self.campo_ibc_vigente,
            self.check_anatocismo_demanda_judicial,
            self.check_anatocismo_acuerdo,
            self.campo_anatocismo_fecha_acuerdo,
            self.combo_moneda,
            self.campo_trm_aplicable,
            self.campo_trm_fecha_referencia,
            self.check_aplica_indexacion_ipc,
            self.check_interes_sobre_capital_indexado,
            self.campo_honorarios_fijos,
            self.campo_cuota_litis_pct,
            self.campo_beneficio_obtenido,
            self.campo_costas_pct,
            self.boton_guardar,
        ]
        for anterior, siguiente in zip(orden, orden[1:]):
            self.setTabOrder(anterior, siguiente)

    def _actualizar_visibilidad_trm(self) -> None:
        es_comercial = self._area == "COMERCIAL"
        es_usd = self.combo_moneda.currentData() == "USD"
        self.campo_trm_aplicable.setVisible(es_comercial and es_usd)
        self.campo_trm_fecha_referencia.setVisible(es_comercial and es_usd)

    def _actualizar_campos_tributario(self) -> None:
        if self._area != "TRIBUTARIO":
            return
        categoria = self.combo_categoria.currentData()
        es_impuesto = categoria == "IMPUESTO_A_CARGO"
        es_extemporaneidad = categoria == "SANCION_EXTEMPORANEIDAD"
        es_inexactitud = categoria == "SANCION_INEXACTITUD"
        es_error_aritmetico = categoria == "SANCION_ERROR_ARITMETICO"
        es_renta_liquida = categoria == "RENTA_LIQUIDA"
        es_sancion = es_extemporaneidad or es_inexactitud or es_error_aritmetico

        self._contenedor_campo_valor.setVisible(es_impuesto)
        self.campo_base_sancion.setVisible(es_sancion)
        self.campo_meses_extemporaneidad.setVisible(es_extemporaneidad)
        self.check_sancion_agravada.setVisible(es_inexactitud)
        self.campo_ingresos_brutos.setVisible(es_renta_liquida)
        self.campo_devoluciones.setVisible(es_renta_liquida)
        self.campo_costos.setVisible(es_renta_liquida)
        self.campo_deducciones.setVisible(es_renta_liquida)
        self.campo_rentas_exentas.setVisible(es_renta_liquida)

    def _actualizar_campos_visibles(self) -> None:
        if self._area == "LABORAL":
            self.campo_fecha_origen.setVisible(True)  # reutilizado como "fecha de inicio del contrato"
            self.campo_fecha_inicio.setVisible(False)
            self.campo_dia_pago.setVisible(False)
            self.campo_fecha_pago_total.setVisible(self.check_pagada.isChecked())
            self.combo_nivel_riesgo_arl.setVisible(self.check_incluir_seguridad_social.isChecked())
            self.check_anatocismo_demanda_judicial.setVisible(False)
            self.check_anatocismo_acuerdo.setVisible(False)
            self.campo_anatocismo_fecha_acuerdo.setVisible(False)
            return

        self.campo_fecha_pago_total.setVisible(False)
        es_recurrente = self.combo_tipo.currentData() == "RECURRENTE"
        self.campo_fecha_origen.setVisible(not es_recurrente)
        self.campo_fecha_inicio.setVisible(es_recurrente)
        self.campo_dia_pago.setVisible(es_recurrente)

        es_comercial = self._area == "COMERCIAL"
        mostrar_anatocismo = es_comercial and not es_recurrente
        self.check_anatocismo_demanda_judicial.setVisible(mostrar_anatocismo)
        self.check_anatocismo_acuerdo.setVisible(mostrar_anatocismo)
        self.campo_anatocismo_fecha_acuerdo.setVisible(
            mostrar_anatocismo and self.check_anatocismo_acuerdo.isChecked()
        )

    def guardar(self) -> int:
        if self._area == "LABORAL":
            return self._guardar_laboral()
        if self._area == "TRIBUTARIO":
            return self._guardar_tributario()

        es_sancionatorio = self._area == "SANCIONATORIO"
        es_honorarios = self._area == "HONORARIOS"

        try:
            tasa = Decimal(self.campo_tasa.text())
            if es_sancionatorio or es_honorarios:
                # No se usa: el motor calcula el monto desde cantidad_smlmv_uvt o
                # honorarios_fijos_pactados/cuota_litis_pactada_pct/beneficio_obtenido.
                valor = Decimal("0.00")
            else:
                valor = Decimal(self.campo_valor.text())
        except InvalidOperation as error:
            raise ValueError("Valor y tasa deben ser numeros validos.") from error

        if not es_sancionatorio and not es_honorarios and valor <= Decimal("0"):
            raise ValueError("El valor de la obligacion debe ser mayor que cero.")

        self._validar_rango(tasa, Decimal("0"), Decimal("1000"), "La tasa efectiva anual")
        self._validar_concepto_no_vacio()

        parseo_por_area = {
            "SANCIONATORIO": self._parse_campos_sancionatorio,
            "HONORARIOS": self._parse_campos_honorarios,
            "COMERCIAL": self._parse_campos_comercial,
        }.get(self._area, self._parse_campos_civil_familia)
        campos_area = {**self._CAMPOS_AREA_POR_DEFECTO, **parseo_por_area()}

        tipo = TipoObligacion(self.combo_tipo.currentData())
        qdate_origen = self.campo_fecha_origen.date()
        fecha_origen = date(qdate_origen.year(), qdate_origen.month(), qdate_origen.day())
        qdate_inicio = self.campo_fecha_inicio.date()
        fecha_inicio = date(qdate_inicio.year(), qdate_inicio.month(), qdate_inicio.day())

        fecha_relevante = fecha_origen if tipo == TipoObligacion.PUNTUAL else fecha_inicio
        self._validar_fecha_no_posterior_a_corte(fecha_relevante)

        session = session_module.get_session()
        obligacion = Obligacion(
            expediente_id=self._expediente_id,
            tipo=tipo,
            concepto=self.campo_concepto.text().strip(),
            categoria=self.combo_categoria.currentData(),
            fecha_origen=fecha_origen if tipo == TipoObligacion.PUNTUAL else fecha_inicio,
            valor=valor,
            tasa_efectiva_anual=tasa,
            aplica_indexacion_ipc=self.check_aplica_indexacion_ipc.isChecked(),
            interes_sobre_capital_indexado=self.check_interes_sobre_capital_indexado.isChecked(),
            dia_pago=self.campo_dia_pago.value() if tipo == TipoObligacion.RECURRENTE else None,
            fecha_inicio=fecha_inicio if tipo == TipoObligacion.RECURRENTE else None,
            fecha_fin=None,
            **campos_area,
        )
        session.add(obligacion)
        session.commit()
        obligacion_id = obligacion.id
        session.close()
        return obligacion_id

    def _parse_decimales(self, campos: list[QLineEdit], mensaje_error: str) -> list[Decimal]:
        """Parsea 1+ QLineEdit a Decimal bajo un solo mensaje de error compartido --
        replica el try/except conjunto que ya usaban los bloques por area de guardar()
        (ej. tasa moratoria + IBC bajo un mismo mensaje)."""
        try:
            return [Decimal(campo.text()) for campo in campos]
        except InvalidOperation as error:
            raise ValueError(mensaje_error) from error

    def _validar_rango(self, valor: Decimal, minimo: Decimal, maximo: Decimal, nombre_campo: str) -> None:
        """Rechaza valores fuera de un rango de sentido comun (Sprint 24) -- no es la
        validacion de usura (esa sigue viviendo en usury_validator.py y corre solo al
        liquidar), es solo para atajar errores de tecleo al guardar (ej. una tasa
        pactada de 99999%)."""
        if valor < minimo or valor > maximo:
            raise ValueError(f"{nombre_campo} debe estar entre {minimo} y {maximo}.")

    def _validar_concepto_no_vacio(self) -> None:
        if not self.campo_concepto.text().strip():
            raise ValueError("El concepto es obligatorio.")

    def _validar_fecha_no_posterior_a_corte(self, fecha: date) -> None:
        """La fecha de origen/inicio de una obligacion no puede quedar despues de la
        fecha de corte del expediente (Sprint 24): de lo contrario la liquidacion no
        tendria ningun dia que acumular intereses, y el dato casi siempre es un error
        de captura (ano equivocado, dia/mes invertido)."""
        session = session_module.get_session()
        try:
            expediente = session.get(Expediente, self._expediente_id)
        finally:
            session.close()
        if fecha > expediente.fecha_corte_default:
            raise ValueError(
                "La fecha de origen/inicio no puede ser posterior a la fecha de corte "
                f"del expediente ({expediente.fecha_corte_default.isoformat()})."
            )

    def _envolver_campo_con_iconos(
        self, campo: QLineEdit, *, icono_info: str | None = None, tooltip_info: str = ""
    ) -> QWidget:
        """Envuelve `campo` en un contenedor horizontal con, opcionalmente, un
        icono de informacion fijo (explica de donde sale un valor por defecto,
        Sprint 34) y siempre un icono de advertencia oculto por defecto que
        `_marcar_campo_invalido` muestra cuando la validacion en tiempo real
        detecta un error. QFormLayout no admite dos widgets de "campo" en la
        misma fila sin este contenedor intermedio -- por eso las llamadas que
        antes ocultaban `campo` directamente (para ocultar/mostrar toda la fila
        segun el area) ahora deben apuntar al contenedor devuelto por este
        metodo, no al QLineEdit interno (ver __init__).
        """
        contenedor = QWidget()
        layout_fila = QHBoxLayout(contenedor)
        layout_fila.setContentsMargins(0, 0, 0, 0)
        layout_fila.addWidget(campo)
        if icono_info is not None:
            etiqueta_info = QLabel()
            etiqueta_info.setPixmap(icon(icono_info).pixmap(16, 16))
            etiqueta_info.setToolTip(tooltip_info)
            layout_fila.addWidget(etiqueta_info)
        etiqueta_advertencia = QLabel()
        etiqueta_advertencia.setPixmap(icon("warning").pixmap(16, 16))
        etiqueta_advertencia.setVisible(False)
        layout_fila.addWidget(etiqueta_advertencia)
        self._iconos_advertencia[campo] = etiqueta_advertencia
        return contenedor

    def _marcar_campo_invalido(self, campo: QLineEdit, mensaje: str) -> None:
        campo.setProperty("class", "invalid")
        campo.setToolTip(mensaje)
        campo.style().unpolish(campo)
        campo.style().polish(campo)
        icono_advertencia = self._iconos_advertencia.get(campo)
        if icono_advertencia is not None:
            icono_advertencia.setToolTip(mensaje)
            icono_advertencia.setVisible(True)

    def _marcar_campo_valido(self, campo: QLineEdit, tooltip_original: str = "") -> None:
        campo.setProperty("class", "")
        campo.setToolTip(tooltip_original)
        campo.style().unpolish(campo)
        campo.style().polish(campo)
        icono_advertencia = self._iconos_advertencia.get(campo)
        if icono_advertencia is not None:
            icono_advertencia.setVisible(False)

    def _validar_concepto_en_tiempo_real(self) -> None:
        tooltip_original = (
            "Descripcion corta de la obligacion (ej. 'Cuota alimentaria noviembre 2025')."
        )
        try:
            self._validar_concepto_no_vacio()
        except ValueError as error:
            self._marcar_campo_invalido(self.campo_concepto, str(error))
        else:
            self._marcar_campo_valido(self.campo_concepto, tooltip_original)

    def _validar_valor_en_tiempo_real(self) -> None:
        tooltip_original = (
            "Monto en pesos (o en la moneda elegida) sobre el que se calculan los intereses."
        )
        texto = self.campo_valor.text().strip()
        if not texto:
            self._marcar_campo_valido(self.campo_valor, tooltip_original)
            return
        try:
            valor = Decimal(texto)
        except InvalidOperation:
            self._marcar_campo_invalido(self.campo_valor, "El valor debe ser un numero valido.")
            return
        if valor <= Decimal("0"):
            self._marcar_campo_invalido(
                self.campo_valor, "El valor de la obligacion debe ser mayor que cero."
            )
            return
        self._marcar_campo_valido(self.campo_valor, tooltip_original)

    def _validar_tasa_en_tiempo_real(self) -> None:
        tooltip_original = (
            "Tasa de interes pactada o aplicable, en porcentaje efectivo anual (%EA)."
        )
        texto = self.campo_tasa.text().strip()
        if not texto:
            self._marcar_campo_valido(self.campo_tasa, tooltip_original)
            return
        try:
            tasa = Decimal(texto)
        except InvalidOperation:
            self._marcar_campo_invalido(
                self.campo_tasa, "La tasa efectiva anual debe ser un numero valido."
            )
            return
        try:
            self._validar_rango(tasa, Decimal("0"), Decimal("1000"), "La tasa efectiva anual")
        except ValueError as error:
            self._marcar_campo_invalido(self.campo_tasa, str(error))
        else:
            self._marcar_campo_valido(self.campo_tasa, tooltip_original)

    def _parse_campos_civil_familia(self) -> dict:
        return {}

    def _parse_campos_sancionatorio(self) -> dict:
        (cantidad_smlmv_uvt,) = self._parse_decimales(
            [self.campo_cantidad_smlmv_uvt], "Cantidad SMLMV/UVT debe ser un numero valido."
        )
        if cantidad_smlmv_uvt <= Decimal("0"):
            raise ValueError("La cantidad de SMLMV/UVT debe ser mayor que cero.")
        return {"cantidad_smlmv_uvt": cantidad_smlmv_uvt}

    def _parse_campos_honorarios(self) -> dict:
        honorarios_fijos, cuota_litis_pct, beneficio_obtenido = self._parse_decimales(
            [self.campo_honorarios_fijos, self.campo_cuota_litis_pct, self.campo_beneficio_obtenido],
            "Honorarios fijos, % cuota litis y beneficio obtenido deben ser numeros validos.",
        )
        self._validar_rango(cuota_litis_pct, Decimal("0"), Decimal("100"), "El % de cuota litis pactada")
        costas_pct = None
        texto_costas = self.campo_costas_pct.text().strip()
        if texto_costas:
            (costas_pct,) = self._parse_decimales(
                [self.campo_costas_pct], "% Costas judiciales debe ser un numero valido."
            )
            self._validar_rango(costas_pct, Decimal("0"), Decimal("100"), "El % de costas judiciales")
        return {
            "honorarios_fijos_pactados": honorarios_fijos,
            "cuota_litis_pactada_pct": cuota_litis_pct,
            "beneficio_obtenido": beneficio_obtenido,
            "costas_pct_manual": costas_pct,
        }

    def _parse_campos_comercial(self) -> dict:
        tasa_moratoria, ibc_vigente = self._parse_decimales(
            [self.campo_tasa_moratoria, self.campo_ibc_vigente],
            "Tasa moratoria e IBC vigente deben ser numeros validos.",
        )
        self._validar_rango(tasa_moratoria, Decimal("0"), Decimal("1000"), "La tasa moratoria anual")
        self._validar_rango(ibc_vigente, Decimal("0"), Decimal("1000"), "El IBC vigente anual")
        qdate_vencimiento = self.campo_fecha_vencimiento.date()
        fecha_vencimiento = date(
            qdate_vencimiento.year(), qdate_vencimiento.month(), qdate_vencimiento.day()
        )

        moneda = self.combo_moneda.currentData()
        trm_aplicable = None
        trm_fecha_referencia = None
        if moneda == "USD":
            (trm_aplicable,) = self._parse_decimales(
                [self.campo_trm_aplicable], "La TRM aplicable debe ser un numero valido."
            )
            qdate_trm = self.campo_trm_fecha_referencia.date()
            trm_fecha_referencia = date(qdate_trm.year(), qdate_trm.month(), qdate_trm.day())

        anatocismo_demanda_judicial = self.check_anatocismo_demanda_judicial.isChecked()
        anatocismo_fecha_acuerdo = None
        if self.check_anatocismo_acuerdo.isChecked():
            qdate_acuerdo = self.campo_anatocismo_fecha_acuerdo.date()
            anatocismo_fecha_acuerdo = date(
                qdate_acuerdo.year(), qdate_acuerdo.month(), qdate_acuerdo.day()
            )

        return {
            "tasa_moratoria_anual": tasa_moratoria,
            "fecha_vencimiento": fecha_vencimiento,
            "ibc_vigente_anual": ibc_vigente,
            "moneda": moneda,
            "trm_aplicable": trm_aplicable,
            "trm_fecha_referencia": trm_fecha_referencia,
            "anatocismo_demanda_judicial": anatocismo_demanda_judicial,
            "anatocismo_fecha_acuerdo": anatocismo_fecha_acuerdo,
        }

    def _guardar_laboral(self) -> int:
        try:
            valor = Decimal(self.campo_valor.text())
        except InvalidOperation as error:
            raise ValueError("El valor (salario base) debe ser un numero valido.") from error
        if valor <= Decimal("0"):
            raise ValueError("El valor de la obligacion debe ser mayor que cero.")
        self._validar_concepto_no_vacio()

        qdate_inicio = self.campo_fecha_origen.date()
        fecha_inicio = date(qdate_inicio.year(), qdate_inicio.month(), qdate_inicio.day())
        self._validar_fecha_no_posterior_a_corte(fecha_inicio)
        qdate_fin = self.campo_fecha_fin.date()
        fecha_fin = date(qdate_fin.year(), qdate_fin.month(), qdate_fin.day())

        fecha_pago_total = None
        pagada = False
        if self.check_pagada.isChecked():
            qdate_pago = self.campo_fecha_pago_total.date()
            fecha_pago_total = date(qdate_pago.year(), qdate_pago.month(), qdate_pago.day())
            pagada = True

        incluir_seguridad_social = self.check_incluir_seguridad_social.isChecked()
        nivel_riesgo_arl = self.combo_nivel_riesgo_arl.currentData() if incluir_seguridad_social else None

        session = session_module.get_session()
        obligacion = Obligacion(
            expediente_id=self._expediente_id,
            tipo=TipoObligacion.PUNTUAL,
            concepto=self.campo_concepto.text().strip(),
            categoria=self.combo_categoria.currentData(),
            fecha_origen=fecha_inicio,
            valor=valor,
            tasa_efectiva_anual=Decimal("0.00"),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            pagada=pagada,
            fecha_pago_total=fecha_pago_total,
            incluir_seguridad_social=incluir_seguridad_social,
            nivel_riesgo_arl=nivel_riesgo_arl,
        )
        session.add(obligacion)
        session.commit()
        obligacion_id = obligacion.id
        session.close()
        return obligacion_id

    def _guardar_tributario(self) -> int:
        categoria = self.combo_categoria.currentData()
        self._validar_concepto_no_vacio()

        qdate_origen = self.campo_fecha_origen.date()
        fecha_origen = date(qdate_origen.year(), qdate_origen.month(), qdate_origen.day())
        self._validar_fecha_no_posterior_a_corte(fecha_origen)

        valor = Decimal("0.00")
        base_sancion = None
        meses_extemporaneidad = None
        sancion_agravada = False
        ingresos_brutos = None
        devoluciones = None
        costos = None
        deducciones = None
        rentas_exentas = None

        if categoria == "IMPUESTO_A_CARGO":
            try:
                valor = Decimal(self.campo_valor.text())
            except InvalidOperation as error:
                raise ValueError("El valor del impuesto a cargo debe ser un numero valido.") from error

        elif categoria == "SANCION_EXTEMPORANEIDAD":
            try:
                base_sancion = Decimal(self.campo_base_sancion.text())
            except InvalidOperation as error:
                raise ValueError("La base de la sancion debe ser un numero valido.") from error
            meses_extemporaneidad = self.campo_meses_extemporaneidad.value()

        elif categoria in ("SANCION_INEXACTITUD", "SANCION_ERROR_ARITMETICO"):
            try:
                base_sancion = Decimal(self.campo_base_sancion.text())
            except InvalidOperation as error:
                raise ValueError("La base de la sancion debe ser un numero valido.") from error
            if categoria == "SANCION_INEXACTITUD":
                sancion_agravada = self.check_sancion_agravada.isChecked()

        elif categoria == "RENTA_LIQUIDA":
            try:
                ingresos_brutos = Decimal(self.campo_ingresos_brutos.text())
                devoluciones = Decimal(self.campo_devoluciones.text())
                costos = Decimal(self.campo_costos.text())
                deducciones = Decimal(self.campo_deducciones.text())
                rentas_exentas = Decimal(self.campo_rentas_exentas.text())
            except InvalidOperation as error:
                raise ValueError(
                    "Los 5 campos de renta liquida gravable deben ser numeros validos."
                ) from error

        session = session_module.get_session()
        obligacion = Obligacion(
            expediente_id=self._expediente_id,
            tipo=TipoObligacion.PUNTUAL,
            concepto=self.campo_concepto.text().strip(),
            categoria=categoria,
            fecha_origen=fecha_origen,
            valor=valor,
            tasa_efectiva_anual=Decimal("0.00"),
            base_sancion_tributaria=base_sancion,
            meses_extemporaneidad=meses_extemporaneidad,
            sancion_agravada=sancion_agravada,
            ingresos_brutos=ingresos_brutos,
            devoluciones_rebajas_descuentos=devoluciones,
            costos=costos,
            deducciones=deducciones,
            rentas_exentas=rentas_exentas,
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
