from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
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
from app.core.constants import (
    CATEGORIAS_CIVIL_FAMILIA,
    CATEGORIAS_COMERCIAL,
    CATEGORIAS_HONORARIOS,
    CATEGORIAS_LABORAL,
    CATEGORIAS_SANCIONATORIO,
    CATEGORIAS_TRIBUTARIO,
)
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
        self.check_anatocismo_demanda_judicial = QCheckBox(
            "Demanda judicial (habilita anatocismo, Art. 886 C.Co.)"
        )
        self.check_anatocismo_acuerdo = QCheckBox("¿Hay acuerdo posterior de capitalización?")
        self.campo_anatocismo_fecha_acuerdo = QDateEdit(QDate.currentDate())
        self.campo_anatocismo_fecha_acuerdo.setCalendarPopup(True)

        self.combo_moneda = QComboBox()
        self.combo_moneda.addItem("COP (peso colombiano)", userData="COP")
        self.combo_moneda.addItem("USD (dolar)", userData="USD")
        self.campo_trm_aplicable = QLineEdit()
        self.campo_trm_fecha_referencia = QDateEdit(QDate.currentDate())
        self.campo_trm_fecha_referencia.setCalendarPopup(True)

        self.campo_cantidad_smlmv_uvt = QLineEdit()

        self.campo_honorarios_fijos = QLineEdit()
        self.campo_cuota_litis_pct = QLineEdit()
        self.campo_beneficio_obtenido = QLineEdit()
        self.campo_costas_pct = QLineEdit()
        self.check_aplica_indexacion_ipc = QCheckBox("Aplica indexación IPC (corrección monetaria)")
        self.check_interes_sobre_capital_indexado = QCheckBox(
            "Interés sobre capital ya indexado (algoritmo Suma Única / Ley 80 de 1993)"
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

        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)

        self.layout_formulario = QFormLayout()
        self.layout_formulario.addRow("Tipo", self.combo_tipo)
        self.layout_formulario.addRow("Categoria", self.combo_categoria)
        self.layout_formulario.addRow("Concepto", self.campo_concepto)
        self.layout_formulario.addRow("Valor", self.campo_valor)
        self.layout_formulario.addRow("Tasa efectiva anual (%)", self.campo_tasa)
        self.layout_formulario.addRow("Fecha de origen (Puntual)", self.campo_fecha_origen)
        self.label_fecha_origen = self.layout_formulario.labelForField(self.campo_fecha_origen)
        self.layout_formulario.addRow("Fecha de inicio (Recurrente)", self.campo_fecha_inicio)
        self.layout_formulario.addRow("Dia de pago (Recurrente)", self.campo_dia_pago)
        self.layout_formulario.addRow("Tasa moratoria anual (%)", self.campo_tasa_moratoria)
        self.layout_formulario.addRow("Fecha de vencimiento", self.campo_fecha_vencimiento)
        self.layout_formulario.addRow("IBC vigente aplicable (%)", self.campo_ibc_vigente)
        self.layout_formulario.addRow(self.check_anatocismo_demanda_judicial)
        self.layout_formulario.addRow(self.check_anatocismo_acuerdo)
        self.layout_formulario.addRow("Fecha del acuerdo posterior", self.campo_anatocismo_fecha_acuerdo)
        self.layout_formulario.addRow("Moneda", self.combo_moneda)
        self.layout_formulario.addRow("TRM aplicable (COP por USD)", self.campo_trm_aplicable)
        self.layout_formulario.addRow("Fecha de referencia de la TRM", self.campo_trm_fecha_referencia)
        self.layout_formulario.addRow("Cantidad SMLMV/UVT (Sancionatorio)", self.campo_cantidad_smlmv_uvt)
        self.layout_formulario.addRow("Honorarios fijos pactados", self.campo_honorarios_fijos)
        self.layout_formulario.addRow("% Cuota litis pactada", self.campo_cuota_litis_pct)
        self.layout_formulario.addRow("Beneficio obtenido por el cliente", self.campo_beneficio_obtenido)
        self.layout_formulario.addRow("% Costas judiciales (opcional)", self.campo_costas_pct)
        self.layout_formulario.addRow(self.check_aplica_indexacion_ipc)
        self.layout_formulario.addRow(self.check_interes_sobre_capital_indexado)
        self.layout_formulario.addRow("Base de la sancion (impuesto a cargo o diferencia)", self.campo_base_sancion)
        self.layout_formulario.addRow("Meses o fraccion de atraso (extemporaneidad)", self.campo_meses_extemporaneidad)
        self.layout_formulario.addRow(self.check_sancion_agravada)
        self.layout_formulario.addRow("Ingresos brutos (Renta liquida)", self.campo_ingresos_brutos)
        self.layout_formulario.addRow("Devoluciones/rebajas/descuentos (Renta liquida)", self.campo_devoluciones)
        self.layout_formulario.addRow("Costos (Renta liquida)", self.campo_costos)
        self.layout_formulario.addRow("Deducciones (Renta liquida)", self.campo_deducciones)
        self.layout_formulario.addRow("Rentas exentas (Renta liquida)", self.campo_rentas_exentas)
        self.layout_formulario.addRow("Fecha de terminacion de contrato", self.campo_fecha_fin)
        self.layout_formulario.addRow(self.check_pagada)
        self.layout_formulario.addRow("Fecha de pago real", self.campo_fecha_pago_total)
        self.layout_formulario.addRow(self.check_incluir_seguridad_social)
        self.layout_formulario.addRow("Nivel de riesgo ARL", self.combo_nivel_riesgo_arl)
        self.layout_formulario.addRow(boton_guardar)
        self.setLayout(self.layout_formulario)

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
        self.campo_valor.setVisible(not es_sancionatorio and not es_honorarios and not es_tributario)

        # Laboral y Tributario son siempre PUNTUAL y no usan tasa efectiva anual pactada
        # (Tributario: el interes es automatico, E.T. art. 635, nunca se pacta).
        self.combo_tipo.setVisible(not es_laboral and not es_tributario)
        self.campo_tasa.setVisible(not es_laboral and not es_tributario)
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

        self._actualizar_campos_visibles()
        self._actualizar_visibilidad_trm()
        self._actualizar_campos_tributario()

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

        self.campo_valor.setVisible(es_impuesto)
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

    def _parse_decimales(self, campos: List[QLineEdit], mensaje_error: str) -> List[Decimal]:
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

    def _parse_campos_civil_familia(self) -> dict:
        return {}

    def _parse_campos_sancionatorio(self) -> dict:
        (cantidad_smlmv_uvt,) = self._parse_decimales(
            [self.campo_cantidad_smlmv_uvt], "Cantidad SMLMV/UVT debe ser un numero valido."
        )
        return {"cantidad_smlmv_uvt": cantidad_smlmv_uvt}

    def _parse_campos_honorarios(self) -> dict:
        honorarios_fijos, cuota_litis_pct, beneficio_obtenido = self._parse_decimales(
            [self.campo_honorarios_fijos, self.campo_cuota_litis_pct, self.campo_beneficio_obtenido],
            "Honorarios fijos, % cuota litis y beneficio obtenido deben ser numeros validos.",
        )
        costas_pct = None
        texto_costas = self.campo_costas_pct.text().strip()
        if texto_costas:
            (costas_pct,) = self._parse_decimales(
                [self.campo_costas_pct], "% Costas judiciales debe ser un numero valido."
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

        qdate_inicio = self.campo_fecha_origen.date()
        fecha_inicio = date(qdate_inicio.year(), qdate_inicio.month(), qdate_inicio.day())
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

        qdate_origen = self.campo_fecha_origen.date()
        fecha_origen = date(qdate_origen.year(), qdate_origen.month(), qdate_origen.day())

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
