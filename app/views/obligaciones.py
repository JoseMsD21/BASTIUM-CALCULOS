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
from app.engine.indexation.historical_index import get_smlmv_for_year
from app.engine.indexation.smlmv_to_uvt import FECHA_CORTE_SMLMV_A_UVT
from app.views.form_utils import (
    agregar_ayuda,
    guardar_o_actualizar,
    hacer_redimensionable,
    set_row_visible,
)
from app.views.icons import icon
from database.models import Expediente, Obligacion, TipoObligacion, TipoReajusteAnual


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
        "tipo_reajuste_anual": TipoReajusteAnual.NINGUNO,
    }

    def __init__(
        self,
        expediente_id: int,
        area: str = "CIVIL_FAMILIA",
        parent=None,
        obligacion_id: int | None = None,
    ):
        super().__init__(parent)
        hacer_redimensionable(self)
        self.setWindowTitle("Editar obligacion" if obligacion_id else "Agregar obligacion")
        self._expediente_id = expediente_id
        self._area = area
        self._obligacion_id = obligacion_id
        self._iconos_advertencia: dict[QLineEdit, QLabel] = {}

        self.combo_tipo = QComboBox()
        self.combo_tipo.setToolTip(
            "Puntual: un solo hecho con fecha de origen (ej. una factura vencida). "
            "Recurrente: pagos periodicos con fecha de inicio y dia de pago fijo "
            "(ej. cuota alimentaria mensual)."
        )
        self.combo_tipo.addItem("Puntual", userData="PUNTUAL")
        if self._area not in ("SANCIONATORIO", "HONORARIOS", "LABORAL", "TRIBUTARIO"):
            # Una multa, un cobro de honorarios o una liquidacion de contrato laboral
            # es siempre un hecho puntual (ver SancionatorioStrategy/HonorariosStrategy/
            # LaboralStrategy en area_strategy.py, que rechazan RECURRENTE con ValueError)
            # -- no se ofrece la opcion en estas areas.
            self.combo_tipo.addItem("Recurrente", userData="RECURRENTE")

        self.combo_categoria = QComboBox()
        self.combo_categoria.setToolTip(
            "Categoria de la obligacion dentro del area elegida -- determina que reglas "
            "de liquidacion aplican (ej. 'Daño emergente' en Civil/Familia, 'Sancion por "
            "inexactitud' en Tributario)."
        )
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
        self.campo_fecha_origen.setToolTip(
            "Fecha en que se causo la obligacion puntual (ej. la fecha de la factura o "
            "del hecho dañoso). Los intereses se calculan desde este dia."
        )

        self.campo_fecha_inicio = QDateEdit(QDate.currentDate())
        self.campo_fecha_inicio.setCalendarPopup(True)
        self.campo_fecha_inicio.setToolTip(
            "Fecha del primer pago periodico. Ejemplo: 2024-01-05 si la primera cuota "
            "alimentaria vence ese dia."
        )
        self.campo_dia_pago = QSpinBox()
        self.campo_dia_pago.setRange(1, 28)
        self.campo_dia_pago.setValue(5)
        self.campo_dia_pago.setToolTip(
            "Dia del mes en que vence cada cuota periodica, entre 1 y 28. Ejemplo: 5 si "
            "la cuota alimentaria vence el dia 5 de cada mes."
        )

        # Reajuste anual (Sprint 41): solo aplica a una obligacion RECURRENTE de
        # Civil/Familia (cuota alimentaria) -- ver _actualizar_campos_visibles.
        # "Ninguno" primero y preseleccionado: mismo comportamiento que antes de
        # este sprint si el usuario no lo toca (default del modelo,
        # TipoReajusteAnual.NINGUNO).
        self.combo_tipo_reajuste_anual = QComboBox()
        self.combo_tipo_reajuste_anual.addItem("Ninguno", userData="NINGUNO")
        self.combo_tipo_reajuste_anual.addItem("SMMLV (Salario Minimo)", userData="SMMLV")
        self.combo_tipo_reajuste_anual.addItem(
            "IPC (Indice de Precios al Consumidor)", userData="IPC"
        )
        self.combo_tipo_reajuste_anual.setToolTip(
            "Si se activa, el capital de cada cuota mensual se reajusta el 1 de enero de "
            "cada año segun el indice elegido -- usar el boton 'Generar cuotas' del "
            "expediente despues de guardar para crear las cuotas mensuales reales."
        )

        self.campo_tasa_moratoria = QLineEdit("24.00")
        self.campo_tasa_moratoria.setToolTip(
            "Tasa de interes que se cobra automaticamente despues del vencimiento (mora), "
            "en porcentaje efectivo anual."
        )
        self.campo_fecha_vencimiento = QDateEdit(QDate.currentDate())
        self.campo_fecha_vencimiento.setCalendarPopup(True)
        self.campo_fecha_vencimiento.setToolTip(
            "Fecha pactada de pago de la obligacion comercial; despues de esta fecha se "
            "aplica la tasa moratoria en vez de la tasa efectiva anual pactada."
        )
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
        self.check_anatocismo_acuerdo.setToolTip(
            "Marca si existe un acuerdo posterior a la demanda que autoriza capitalizar "
            "intereses sobre intereses (anatocismo convencional, Art. 886 C.Co.)."
        )
        self.campo_anatocismo_fecha_acuerdo = QDateEdit(QDate.currentDate())
        self.campo_anatocismo_fecha_acuerdo.setCalendarPopup(True)
        self.campo_anatocismo_fecha_acuerdo.setToolTip(
            "Fecha del acuerdo posterior que autoriza el anatocismo; desde esa fecha "
            "empieza a capitalizarse el interes sobre interes."
        )

        self.combo_moneda = QComboBox()
        self.combo_moneda.setToolTip(
            "Moneda en que esta pactada la obligacion. Si elige USD, debe indicar la TRM "
            "aplicable para convertir a pesos."
        )
        self.combo_moneda.addItem("COP (peso colombiano)", userData="COP")
        self.combo_moneda.addItem("USD (dolar)", userData="USD")
        self.campo_trm_aplicable = QLineEdit()
        self.campo_trm_aplicable.setToolTip(
            "Tasa Representativa del Mercado (COP por USD) aplicable en la fecha de referencia."
        )
        self.campo_trm_fecha_referencia = QDateEdit(QDate.currentDate())
        self.campo_trm_fecha_referencia.setCalendarPopup(True)
        self.campo_trm_fecha_referencia.setToolTip(
            "Fecha de la TRM certificada por el Banco de la Republica que se usa para la "
            "conversion. Ejemplo: la fecha de origen de la obligacion."
        )

        self.campo_cantidad_smlmv_uvt = QLineEdit()
        self.campo_cantidad_smlmv_uvt.setToolTip(
            "Cantidad de Salarios Minimos Legales Mensuales Vigentes (SMLMV) o Unidades de "
            "Valor Tributario (UVT) sobre la que se calcula la multa."
        )
        # Indicador de transparencia (Sprint 45): la unidad (SMLMV o UVT) que se aplica
        # depende de la fecha de origen del hecho sancionatorio (Ley 1955/2019 art. 49,
        # corte 2020-01-01) -- ver `resolver_base_sancion` en
        # app/engine/indexation/smlmv_to_uvt.py, que ya resuelve esa regla para el
        # calculo. Aqui solo se muestra el resultado; se reutiliza la constante
        # `FECHA_CORTE_SMLMV_A_UVT` de ese modulo para no duplicar la fecha de corte.
        self.label_unidad_smlmv_uvt = QLabel()
        self.label_unidad_smlmv_uvt.setToolTip(
            "Segun la fecha de origen, la cantidad de arriba se interpreta como SMLMV "
            "(antes del 2020-01-01) o como UVT (desde esa fecha), segun la Ley 1955 de "
            "2019, art. 49."
        )

        self.campo_honorarios_fijos = QLineEdit()
        self.campo_honorarios_fijos.setToolTip(
            "Valor fijo pactado por honorarios, adicional a (o en vez de) la cuota "
            "litis. Ejemplo: $500.000 de anticipo de honorarios."
        )
        self.campo_cuota_litis_pct = QLineEdit()
        self.campo_cuota_litis_pct.setToolTip(
            "Porcentaje del beneficio obtenido por el cliente pactado como honorarios "
            "(cuota litis), entre 0% y 100%."
        )
        self.campo_beneficio_obtenido = QLineEdit()
        self.campo_beneficio_obtenido.setToolTip(
            "Valor del beneficio economico obtenido por el cliente en el proceso, base "
            "para calcular la cuota litis pactada. Ejemplo: $20.000.000 recuperados en "
            "la sentencia."
        )
        self.campo_costas_pct = QLineEdit()
        self.campo_costas_pct.setToolTip(
            "Porcentaje adicional por costas judiciales a cargo de la parte vencida, si se "
            "pacto o decreto."
        )
        self.check_aplica_indexacion_ipc = QCheckBox(
            "Aplica indexación IPC (corrección monetaria)"
        )
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
        self.campo_base_sancion.setToolTip(
            "Valor del impuesto a cargo o de la diferencia detectada por la DIAN sobre "
            "el que se calcula la sancion tributaria. Ejemplo: $2.000.000."
        )
        self.campo_meses_extemporaneidad = QSpinBox()
        self.campo_meses_extemporaneidad.setRange(1, 120)
        self.campo_meses_extemporaneidad.setValue(1)
        self.campo_meses_extemporaneidad.setToolTip(
            "Meses o fraccion de mes de atraso en la presentacion de la declaracion "
            "(Estatuto Tributario, art. 641). Ejemplo: 3 si se presento 2 meses y 10 "
            "dias tarde (se cuenta como 3 meses)."
        )
        self.check_sancion_agravada = QCheckBox(
            "Agravada (omision de activos o pasivos inexistentes)"
        )
        self.check_sancion_agravada.setToolTip(
            "Marca si la inexactitud incluyo activos o pasivos inexistentes, lo que "
            "duplica el porcentaje de la sancion (Estatuto Tributario, art. 648, "
            "paragrafo 1)."
        )
        self.campo_ingresos_brutos = QLineEdit()
        self.campo_ingresos_brutos.setToolTip(
            "Ingresos brutos del periodo gravable, antes de devoluciones y "
            "descuentos. Ejemplo: $80.000.000."
        )
        self.campo_devoluciones = QLineEdit()
        self.campo_devoluciones.setToolTip(
            "Devoluciones, rebajas y descuentos sobre los ingresos brutos del "
            "periodo. Ejemplo: $2.000.000."
        )
        self.campo_costos = QLineEdit()
        self.campo_costos.setToolTip(
            "Costos asociados a la actividad generadora de renta. Ejemplo: $30.000.000."
        )
        self.campo_deducciones = QLineEdit()
        self.campo_deducciones.setToolTip(
            "Deducciones fiscales aceptadas del periodo. Ejemplo: $5.000.000."
        )
        self.campo_rentas_exentas = QLineEdit()
        self.campo_rentas_exentas.setToolTip(
            "Rentas exentas del periodo, si aplica. Ejemplo: $1.000.000."
        )

        self.campo_fecha_fin = QDateEdit(QDate.currentDate())
        self.campo_fecha_fin.setCalendarPopup(True)
        self.campo_fecha_fin.setToolTip(
            "Fecha en que termino la relacion laboral; se usa para liquidar "
            "prestaciones sociales hasta ese dia."
        )
        # es_smmlv (Sprint 44, punto 1): cuando esta marcado, el salario base se
        # resuelve automaticamente desde el SMLMV vigente del año de inicio del
        # contrato (LaboralStrategy.liquidar) -- "Valor" deja de ser editable a
        # mano (ver _actualizar_campos_visibles).
        self.check_es_smmlv = QCheckBox("Salario = SMMLV (resolver automaticamente por año)")
        self.check_es_smmlv.setToolTip(
            "Resuelve el salario base desde el Salario Minimo Legal Mensual Vigente del "
            "año de inicio del contrato, en vez del valor digitado a mano."
        )
        self.check_pagada = QCheckBox("Prestaciones pagadas")
        self.check_pagada.setToolTip(
            "Marca si el empleador ya pago las prestaciones sociales liquidadas; "
            "habilita 'Fecha de pago real' para calcular intereses solo hasta esa fecha."
        )
        self.campo_fecha_pago_total = QDateEdit(QDate.currentDate())
        self.campo_fecha_pago_total.setCalendarPopup(True)
        self.campo_fecha_pago_total.setToolTip(
            "Fecha en que el empleador realmente pago las prestaciones sociales "
            "adeudadas (corta el calculo de intereses moratorios en esa fecha)."
        )
        self.check_incluir_seguridad_social = QCheckBox(
            "Incluir cotizaciones de seguridad social no pagadas"
        )
        self.check_incluir_seguridad_social.setToolTip(
            "Incluye el calculo de los aportes a seguridad social (pension, salud, "
            "ARL) que el empleador no pago durante la relacion laboral."
        )
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

        # Concepto/Valor/Tasa se envuelven con un icono de advertencia -- ver
        # _envolver_campo_con_iconos. A partir de aqui, ocultar/mostrar la FILA de
        # Valor/Tasa segun el area debe apuntar al contenedor devuelto, no al
        # QLineEdit interno (que solo controla su propia visibilidad, no la del
        # icono que lo acompaña).
        self._contenedor_campo_concepto = self._envolver_campo_con_iconos(self.campo_concepto)
        self._contenedor_campo_valor = self._envolver_campo_con_iconos(self.campo_valor)
        # Tasa ademas recibe el icono informativo del valor por defecto (Sprint 34),
        # ahora mediante el helper compartido `agregar_ayuda` (Sprint 59) en vez de un
        # parametro propio de _envolver_campo_con_iconos -- agrega tambien la fila al
        # layout, por eso no aparece un addRow("Tasa efectiva anual (%)", ...) separado
        # mas abajo, junto a las demas filas de "Tasas e intereses".
        self._contenedor_campo_tasa = agregar_ayuda(
            self.layout_tasas_intereses,
            "Tasa efectiva anual (%)",
            self._envolver_campo_con_iconos(self.campo_tasa),
            tooltip="Valor por defecto: interés civil legal, Art. 1617 C.C.",
        )

        self.layout_datos_basicos.addRow("Tipo", self.combo_tipo)
        self.layout_datos_basicos.addRow("Categoria", self.combo_categoria)
        self.layout_datos_basicos.addRow("Concepto", self._contenedor_campo_concepto)
        self.layout_datos_basicos.addRow("Valor", self._contenedor_campo_valor)
        self.layout_datos_basicos.addRow(self.check_es_smmlv)
        self.layout_datos_basicos.addRow("Fecha de origen (Puntual)", self.campo_fecha_origen)
        self.label_fecha_origen = self.layout_datos_basicos.labelForField(self.campo_fecha_origen)
        self.layout_datos_basicos.addRow("Fecha de inicio (Recurrente)", self.campo_fecha_inicio)
        self.layout_datos_basicos.addRow("Dia de pago (Recurrente)", self.campo_dia_pago)
        self.layout_datos_basicos.addRow(
            "Reajuste anual (Recurrente, Civil/Familia)", self.combo_tipo_reajuste_anual
        )
        self.layout_datos_basicos.addRow(
            "Cantidad SMLMV/UVT (Sancionatorio)", self.campo_cantidad_smlmv_uvt
        )
        self.layout_datos_basicos.addRow(
            "Unidad que se aplicara (Sancionatorio)", self.label_unidad_smlmv_uvt
        )
        self.layout_datos_basicos.addRow(
            "Base de la sancion (impuesto a cargo o diferencia)", self.campo_base_sancion
        )
        self.layout_datos_basicos.addRow(
            "Meses o fraccion de atraso (extemporaneidad)", self.campo_meses_extemporaneidad
        )
        self.layout_datos_basicos.addRow(self.check_sancion_agravada)
        self.layout_datos_basicos.addRow(
            "Ingresos brutos (Renta liquida)", self.campo_ingresos_brutos
        )
        self.layout_datos_basicos.addRow(
            "Devoluciones/rebajas/descuentos (Renta liquida)", self.campo_devoluciones
        )
        self.layout_datos_basicos.addRow("Costos (Renta liquida)", self.campo_costos)
        self.layout_datos_basicos.addRow("Deducciones (Renta liquida)", self.campo_deducciones)
        self.layout_datos_basicos.addRow(
            "Rentas exentas (Renta liquida)", self.campo_rentas_exentas
        )
        self.layout_datos_basicos.addRow("Fecha de terminacion de contrato", self.campo_fecha_fin)
        self.layout_datos_basicos.addRow(self.check_pagada)
        self.layout_datos_basicos.addRow("Fecha de pago real", self.campo_fecha_pago_total)
        self.layout_datos_basicos.addRow(self.check_incluir_seguridad_social)
        self.layout_datos_basicos.addRow("Nivel de riesgo ARL", self.combo_nivel_riesgo_arl)

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

        # Laboral y Tributario son siempre PUNTUAL y no usan tasa efectiva anual pactada
        # (Tributario: el interes es automatico, E.T. art. 635, nunca se pacta).
        self._aplicar_visibilidad_filas(
            self.layout_datos_basicos,
            {
                self.campo_cantidad_smlmv_uvt: es_sancionatorio,
                self.label_unidad_smlmv_uvt: es_sancionatorio,
                # "Valor" no aplica a Sancionatorio/Honorarios/Tributario (salvo
                # IMPUESTO_A_CARGO, ver _actualizar_campos_tributario): el monto se
                # calcula a partir de otros campos. Se oculta el CONTENEDOR (campo +
                # iconos), no el QLineEdit directamente, para que el icono de
                # advertencia tambien desaparezca junto con la fila.
                self._contenedor_campo_valor: not es_sancionatorio
                and not es_honorarios
                and not es_tributario,
                self.combo_tipo: not es_laboral and not es_tributario,
                self.campo_fecha_fin: es_laboral,
                self.combo_nivel_riesgo_arl: False,
                self.campo_base_sancion: False,
                self.campo_meses_extemporaneidad: False,
                self.campo_ingresos_brutos: False,
                self.campo_devoluciones: False,
                self.campo_costos: False,
                self.campo_deducciones: False,
                self.campo_rentas_exentas: False,
            },
        )
        self._aplicar_visibilidad_filas(
            self.layout_tasas_intereses,
            {
                self.campo_tasa_moratoria: es_comercial,
                self.campo_fecha_vencimiento: es_comercial,
                self.campo_ibc_vigente: es_comercial,
                self.combo_moneda: es_comercial,
                self._contenedor_campo_tasa: not es_laboral and not es_tributario,
            },
        )
        self._aplicar_visibilidad_filas(
            self.layout_honorarios_costas,
            {
                self.campo_honorarios_fijos: es_honorarios,
                self.campo_cuota_litis_pct: es_honorarios,
                self.campo_beneficio_obtenido: es_honorarios,
                self.campo_costas_pct: es_honorarios,
            },
        )

        # Estos checkboxes se agregaron con addRow(widget) de un solo argumento (sin
        # etiqueta de texto separada) -- QFormLayout no genera QLabel para ellos, asi
        # que no sufren el bug de fila huerfana y pueden seguir usando setVisible()
        # directo (Sprint 39).
        self.check_aplica_indexacion_ipc.setVisible(self._area == "CIVIL_FAMILIA")
        self.check_interes_sobre_capital_indexado.setVisible(self._area == "CIVIL_FAMILIA")
        self.check_es_smmlv.setVisible(es_laboral)
        self.check_pagada.setVisible(es_laboral)
        self.check_incluir_seguridad_social.setVisible(es_laboral)
        self.check_sancion_agravada.setVisible(False)

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
        self.check_es_smmlv.stateChanged.connect(self._actualizar_campos_visibles)
        self.check_pagada.stateChanged.connect(self._actualizar_campos_visibles)
        self.check_incluir_seguridad_social.stateChanged.connect(self._actualizar_campos_visibles)
        self.check_anatocismo_acuerdo.stateChanged.connect(self._actualizar_campos_visibles)
        self.combo_moneda.currentIndexChanged.connect(self._actualizar_visibilidad_trm)
        self.combo_categoria.currentIndexChanged.connect(self._actualizar_campos_tributario)
        self.campo_fecha_origen.dateChanged.connect(self._actualizar_indicador_unidad_smlmv_uvt)

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
        self._actualizar_indicador_unidad_smlmv_uvt()
        self._fijar_orden_de_tabulacion()

        if obligacion_id is not None:
            self._precargar_desde_obligacion(obligacion_id)

    def _precargar_desde_obligacion(self, obligacion_id: int) -> None:
        """Precarga todos los campos del formulario desde una `Obligacion` ya
        guardada (Sprint 44, punto 2) -- espejo, campo por campo, de lo que
        cada `guardar()`/`_guardar_laboral()`/`_guardar_tributario()` ya lee
        del formulario para construir sus kwargs. Se llama una sola vez, al
        final de `__init__`, despues de que la visibilidad de todos los
        campos condicionales del area ya quedo resuelta."""
        session = session_module.get_session()
        try:
            obligacion = session.get(Obligacion, obligacion_id)

            indice_tipo = self.combo_tipo.findData(obligacion.tipo.value)
            if indice_tipo >= 0:
                self.combo_tipo.setCurrentIndex(indice_tipo)
            indice_categoria = self.combo_categoria.findData(obligacion.categoria)
            if indice_categoria >= 0:
                self.combo_categoria.setCurrentIndex(indice_categoria)

            self.campo_concepto.setText(obligacion.concepto)
            self.campo_valor.setText(str(obligacion.valor))
            self.campo_tasa.setText(str(obligacion.tasa_efectiva_anual))

            def _qdate(valor):
                return QDate(valor.year, valor.month, valor.day) if valor else QDate.currentDate()

            if obligacion.tipo == TipoObligacion.RECURRENTE:
                self.campo_fecha_inicio.setDate(_qdate(obligacion.fecha_inicio))
                if obligacion.dia_pago:
                    self.campo_dia_pago.setValue(obligacion.dia_pago)
            else:
                self.campo_fecha_origen.setDate(_qdate(obligacion.fecha_origen))

            self.check_aplica_indexacion_ipc.setChecked(obligacion.aplica_indexacion_ipc)
            self.check_interes_sobre_capital_indexado.setChecked(
                obligacion.interes_sobre_capital_indexado
            )

            if self._area == "COMERCIAL":
                if obligacion.tasa_moratoria_anual is not None:
                    self.campo_tasa_moratoria.setText(str(obligacion.tasa_moratoria_anual))
                if obligacion.fecha_vencimiento is not None:
                    self.campo_fecha_vencimiento.setDate(_qdate(obligacion.fecha_vencimiento))
                if obligacion.ibc_vigente_anual is not None:
                    self.campo_ibc_vigente.setText(str(obligacion.ibc_vigente_anual))
                self.check_anatocismo_demanda_judicial.setChecked(
                    obligacion.anatocismo_demanda_judicial
                )
                if obligacion.anatocismo_fecha_acuerdo is not None:
                    self.check_anatocismo_acuerdo.setChecked(True)
                    self.campo_anatocismo_fecha_acuerdo.setDate(
                        _qdate(obligacion.anatocismo_fecha_acuerdo)
                    )
                indice_moneda = self.combo_moneda.findData(obligacion.moneda)
                if indice_moneda >= 0:
                    self.combo_moneda.setCurrentIndex(indice_moneda)
                if obligacion.trm_aplicable is not None:
                    self.campo_trm_aplicable.setText(str(obligacion.trm_aplicable))
                if obligacion.trm_fecha_referencia is not None:
                    self.campo_trm_fecha_referencia.setDate(
                        _qdate(obligacion.trm_fecha_referencia)
                    )

            elif self._area == "SANCIONATORIO":
                if obligacion.cantidad_smlmv_uvt is not None:
                    self.campo_cantidad_smlmv_uvt.setText(str(obligacion.cantidad_smlmv_uvt))

            elif self._area == "HONORARIOS":
                if obligacion.honorarios_fijos_pactados is not None:
                    self.campo_honorarios_fijos.setText(str(obligacion.honorarios_fijos_pactados))
                if obligacion.cuota_litis_pactada_pct is not None:
                    self.campo_cuota_litis_pct.setText(str(obligacion.cuota_litis_pactada_pct))
                if obligacion.beneficio_obtenido is not None:
                    self.campo_beneficio_obtenido.setText(str(obligacion.beneficio_obtenido))
                if obligacion.costas_pct_manual is not None:
                    self.campo_costas_pct.setText(str(obligacion.costas_pct_manual))

            elif self._area == "LABORAL":
                if obligacion.fecha_fin is not None:
                    self.campo_fecha_fin.setDate(_qdate(obligacion.fecha_fin))
                self.check_es_smmlv.setChecked(obligacion.es_smmlv)
                self.check_pagada.setChecked(obligacion.pagada)
                if obligacion.fecha_pago_total is not None:
                    self.campo_fecha_pago_total.setDate(_qdate(obligacion.fecha_pago_total))
                self.check_incluir_seguridad_social.setChecked(obligacion.incluir_seguridad_social)
                if obligacion.nivel_riesgo_arl:
                    indice_nivel = self.combo_nivel_riesgo_arl.findData(
                        obligacion.nivel_riesgo_arl
                    )
                    if indice_nivel >= 0:
                        self.combo_nivel_riesgo_arl.setCurrentIndex(indice_nivel)

            elif self._area == "TRIBUTARIO":
                if obligacion.base_sancion_tributaria is not None:
                    self.campo_base_sancion.setText(str(obligacion.base_sancion_tributaria))
                if obligacion.meses_extemporaneidad is not None:
                    self.campo_meses_extemporaneidad.setValue(obligacion.meses_extemporaneidad)
                self.check_sancion_agravada.setChecked(obligacion.sancion_agravada)
                if obligacion.ingresos_brutos is not None:
                    self.campo_ingresos_brutos.setText(str(obligacion.ingresos_brutos))
                if obligacion.devoluciones_rebajas_descuentos is not None:
                    self.campo_devoluciones.setText(
                        str(obligacion.devoluciones_rebajas_descuentos)
                    )
                if obligacion.costos is not None:
                    self.campo_costos.setText(str(obligacion.costos))
                if obligacion.deducciones is not None:
                    self.campo_deducciones.setText(str(obligacion.deducciones))
                if obligacion.rentas_exentas is not None:
                    self.campo_rentas_exentas.setText(str(obligacion.rentas_exentas))
        finally:
            session.close()

        # Reaplica la visibilidad condicional (checkboxes/combo_categoria ya
        # precargados) para que, por ejemplo, "Fecha de pago real" quede
        # visible de entrada si la obligacion ya estaba marcada como pagada.
        self._actualizar_campos_visibles()
        self._actualizar_visibilidad_trm()
        self._actualizar_campos_tributario()

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
            self.combo_tipo_reajuste_anual,
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
        for anterior, siguiente in zip(orden, orden[1:], strict=False):
            self.setTabOrder(anterior, siguiente)

    def _aplicar_visibilidad_filas(
        self, layout: QFormLayout, visibilidad_por_widget: dict[QWidget, bool]
    ) -> None:
        """Aplica `set_row_visible` a cada par (widget, visible) de `layout` de una
        sola vez (Sprint 39) -- evita repetir `widget.setVisible(...)` suelto por
        cada campo condicional, que es justo el patron que deja etiquetas huerfanas
        (la fila conserva su QLabel de QFormLayout.addRow(str, widget) visible
        aunque el widget se oculte). Centralizar la iteracion aqui tambien evita que
        el bug reaparezca al agregar un campo condicional nuevo."""
        for widget, visible in visibilidad_por_widget.items():
            set_row_visible(layout, widget, visible)

    def _actualizar_visibilidad_trm(self) -> None:
        es_comercial = self._area == "COMERCIAL"
        es_usd = self.combo_moneda.currentData() == "USD"
        self._aplicar_visibilidad_filas(
            self.layout_tasas_intereses,
            {
                self.campo_trm_aplicable: es_comercial and es_usd,
                self.campo_trm_fecha_referencia: es_comercial and es_usd,
            },
        )

    def _actualizar_indicador_unidad_smlmv_uvt(self) -> None:
        """Muestra junto a `campo_cantidad_smlmv_uvt` la unidad (SMLMV o UVT) que se va
        a aplicar segun `campo_fecha_origen` (Sprint 45), reutilizando la misma
        constante de corte (`FECHA_CORTE_SMLMV_A_UVT`) que ya usa
        `resolver_base_sancion` para el calculo real -- evita duplicar la fecha del
        2020-01-01 en la UI. Se conecta a `campo_fecha_origen.dateChanged` para
        actualizarse en vivo sin necesidad de guardar el formulario."""
        qdate_origen = self.campo_fecha_origen.date()
        fecha_origen = date(qdate_origen.year(), qdate_origen.month(), qdate_origen.day())
        unidad = "UVT" if fecha_origen >= FECHA_CORTE_SMLMV_A_UVT else "SMLMV"
        self.label_unidad_smlmv_uvt.setText(f"Se aplicará como: {unidad}")

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

        self._aplicar_visibilidad_filas(
            self.layout_datos_basicos,
            {
                self._contenedor_campo_valor: es_impuesto,
                self.campo_base_sancion: es_sancion,
                self.campo_meses_extemporaneidad: es_extemporaneidad,
                self.campo_ingresos_brutos: es_renta_liquida,
                self.campo_devoluciones: es_renta_liquida,
                self.campo_costos: es_renta_liquida,
                self.campo_deducciones: es_renta_liquida,
                self.campo_rentas_exentas: es_renta_liquida,
            },
        )
        # addRow(check_sancion_agravada) es de un solo argumento -- sin etiqueta
        # separada, no sufre el bug de fila huerfana (Sprint 39).
        self.check_sancion_agravada.setVisible(es_inexactitud)

    def _actualizar_campos_visibles(self) -> None:
        if self._area == "LABORAL":
            self._aplicar_visibilidad_filas(
                self.layout_datos_basicos,
                {
                    # reutilizado como "fecha de inicio del contrato"
                    self.campo_fecha_origen: True,
                    self.campo_fecha_inicio: False,
                    self.campo_dia_pago: False,
                    # es_smmlv (Sprint 44, punto 1): con el checkbox marcado, "Valor"
                    # se oculta -- el salario base se resuelve automaticamente al
                    # liquidar, digitarlo a mano no serviria de nada.
                    self._contenedor_campo_valor: not self.check_es_smmlv.isChecked(),
                    self.combo_tipo_reajuste_anual: False,
                    self.campo_fecha_pago_total: self.check_pagada.isChecked(),
                    self.combo_nivel_riesgo_arl: self.check_incluir_seguridad_social.isChecked(),
                },
            )
            self.check_anatocismo_demanda_judicial.setVisible(False)
            self.check_anatocismo_acuerdo.setVisible(False)
            set_row_visible(
                self.layout_tasas_intereses, self.campo_anatocismo_fecha_acuerdo, False
            )
            return

        es_recurrente = self.combo_tipo.currentData() == "RECURRENTE"
        self._aplicar_visibilidad_filas(
            self.layout_datos_basicos,
            {
                self.campo_fecha_pago_total: False,
                self.campo_fecha_origen: not es_recurrente,
                self.campo_fecha_inicio: es_recurrente,
                self.campo_dia_pago: es_recurrente,
                # Reajuste anual (Sprint 41): solo Civil/Familia -- Comercial tambien
                # admite RECURRENTE pero el reajuste SMMLV/IPC es exclusivo de cuotas
                # alimentarias (ver plan del Sprint 41, alcance excluido: Laboral queda
                # para otro sprint, Comercial nunca lo pidio).
                self.combo_tipo_reajuste_anual: es_recurrente and self._area == "CIVIL_FAMILIA",
            },
        )

        es_comercial = self._area == "COMERCIAL"
        mostrar_anatocismo = es_comercial and not es_recurrente
        self.check_anatocismo_demanda_judicial.setVisible(mostrar_anatocismo)
        self.check_anatocismo_acuerdo.setVisible(mostrar_anatocismo)
        set_row_visible(
            self.layout_tasas_intereses,
            self.campo_anatocismo_fecha_acuerdo,
            mostrar_anatocismo and self.check_anatocismo_acuerdo.isChecked(),
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
        obligacion_id = guardar_o_actualizar(
            session,
            Obligacion,
            self._obligacion_id,
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

    def _validar_rango(
        self, valor: Decimal, minimo: Decimal, maximo: Decimal, nombre_campo: str
    ) -> None:
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

    def _envolver_campo_con_iconos(self, campo: QLineEdit) -> QWidget:
        """Envuelve `campo` en un contenedor horizontal con un icono de
        advertencia oculto por defecto que `_marcar_campo_invalido` muestra
        cuando la validacion en tiempo real detecta un error. QFormLayout no
        admite dos widgets de "campo" en la misma fila sin este contenedor
        intermedio -- por eso las llamadas que antes ocultaban `campo`
        directamente (para ocultar/mostrar toda la fila segun el area) ahora
        deben apuntar al contenedor devuelto por este metodo, no al QLineEdit
        interno (ver __init__).

        El icono informativo de un valor por defecto (Sprint 34, antes tambien
        construido aqui via `icono_info=`) se extrajo al helper compartido
        `agregar_ayuda` (app/views/form_utils.py, Sprint 59) -- ver el call
        site de "Tasa efectiva anual" en __init__, que envuelve el contenedor
        que devuelve este metodo con `agregar_ayuda` para agregar ese icono
        y la fila al layout.
        """
        contenedor = QWidget()
        layout_fila = QHBoxLayout(contenedor)
        layout_fila.setContentsMargins(0, 0, 0, 0)
        layout_fila.addWidget(campo)
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
        if self.combo_tipo.currentData() != "RECURRENTE":
            return {}
        return {
            "tipo_reajuste_anual": TipoReajusteAnual(self.combo_tipo_reajuste_anual.currentData())
        }

    def _parse_campos_sancionatorio(self) -> dict:
        (cantidad_smlmv_uvt,) = self._parse_decimales(
            [self.campo_cantidad_smlmv_uvt], "Cantidad SMLMV/UVT debe ser un numero valido."
        )
        if cantidad_smlmv_uvt <= Decimal("0"):
            raise ValueError("La cantidad de SMLMV/UVT debe ser mayor que cero.")
        return {"cantidad_smlmv_uvt": cantidad_smlmv_uvt}

    def _parse_campos_honorarios(self) -> dict:
        honorarios_fijos, cuota_litis_pct, beneficio_obtenido = self._parse_decimales(
            [
                self.campo_honorarios_fijos,
                self.campo_cuota_litis_pct,
                self.campo_beneficio_obtenido,
            ],
            "Honorarios fijos, % cuota litis y beneficio obtenido deben ser numeros validos.",
        )
        self._validar_rango(
            cuota_litis_pct, Decimal("0"), Decimal("100"), "El % de cuota litis pactada"
        )
        costas_pct = None
        texto_costas = self.campo_costas_pct.text().strip()
        if texto_costas:
            (costas_pct,) = self._parse_decimales(
                [self.campo_costas_pct], "% Costas judiciales debe ser un numero valido."
            )
            self._validar_rango(
                costas_pct, Decimal("0"), Decimal("100"), "El % de costas judiciales"
            )
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
        self._validar_rango(
            tasa_moratoria, Decimal("0"), Decimal("1000"), "La tasa moratoria anual"
        )
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
        es_smmlv = self.check_es_smmlv.isChecked()
        qdate_inicio = self.campo_fecha_origen.date()
        fecha_inicio = date(qdate_inicio.year(), qdate_inicio.month(), qdate_inicio.day())

        if es_smmlv:
            # El salario se resuelve aqui mismo (no solo en LaboralStrategy)
            # para que la columna `valor` de la tabla de obligaciones muestre
            # de inmediato un numero con sentido -- LaboralStrategy lo vuelve a
            # resolver en cada liquidacion desde parametros_legales, asi que
            # esto es solo una foto inicial, no la fuente de verdad.
            valor = get_smlmv_for_year(fecha_inicio.year)
        else:
            try:
                valor = Decimal(self.campo_valor.text())
            except InvalidOperation as error:
                raise ValueError("El valor (salario base) debe ser un numero valido.") from error
            if valor <= Decimal("0"):
                raise ValueError("El valor de la obligacion debe ser mayor que cero.")
        self._validar_concepto_no_vacio()

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
        nivel_riesgo_arl = (
            self.combo_nivel_riesgo_arl.currentData() if incluir_seguridad_social else None
        )

        session = session_module.get_session()
        obligacion_id = guardar_o_actualizar(
            session,
            Obligacion,
            self._obligacion_id,
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
            es_smmlv=es_smmlv,
        )
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
                raise ValueError(
                    "El valor del impuesto a cargo debe ser un numero valido."
                ) from error

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
        obligacion_id = guardar_o_actualizar(
            session,
            Obligacion,
            self._obligacion_id,
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
        session.close()
        return obligacion_id

    def _guardar_y_cerrar(self) -> None:
        try:
            self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos invalidos", str(error))
