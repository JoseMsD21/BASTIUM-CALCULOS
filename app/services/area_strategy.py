from abc import ABC, abstractmethod
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from app.core.exceptions import CuotaLitisExcedeTopeError
from app.domain.obligation.payment import Payment
from app.engine.costs.agencias_en_derecho import Instancia, TipoProceso, calcular_agencias_en_derecho
from app.engine.financial.rate import Rate
from app.engine.interest.provider import MemoryRateProvider
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.engine.currency.converter import convertir_a_pesos
from app.engine.currency.trm_provider import ManualTRMProvider
from app.engine.labor.incapacidad import IncapacidadCalculator
from app.engine.labor.moratory_indemnity import MoratoryIndemnityCalculator
from app.engine.labor.seguridad_social import SeguridadSocialCalculator
from app.engine.liquidation.result import LiquidationResult
from app.engine.temporal.schedulers.base import Event
from app.engine.temporal.schedulers.family import FamilyScheduler
from app.engine.temporal.schedulers.labor import LaborScheduler
from app.engine.interest.usury_validator import validar_tasa_usura
from app.engine.indexation.smlmv_to_uvt import resolver_base_sancion
from app.engine.indexation.historical_index import get_ipc_interpolado_for_date
from app.engine.indexation.ipc import IPCIndexation
from app.services.motor_universal import UniversalLiquidationService
from app.services.parametro_service import get_parametro
from app.engine.tax.moratory_interest import construir_rate_provider_moratorio_tributario
from app.engine.tax.renta_liquida import depurar_renta_liquida_gravable
from app.engine.tax.sanciones import (
    calcular_sancion_error_aritmetico,
    calcular_sancion_extemporaneidad,
    calcular_sancion_inexactitud,
)


def _evento_costas_procesales(obligacion, pretensiones_reconocidas: Decimal) -> Event | None:
    """Costas procesales (agencias en derecho) para cualquier area de litigio
    judicial. costas_pct_manual (Sprint 4) tiene siempre prioridad sobre el
    calculo automatico del Acuerdo PSAA16-10554 (Sprint 18) -- si el auto
    judicial real ya fijo un porcentaje, ese manda. Retorna None si la
    obligacion no tiene ninguno de los dos mecanismos activado (comportamiento
    identico al de antes de este sprint)."""
    if obligacion.costas_pct_manual is not None:
        costas_monto = pretensiones_reconocidas * obligacion.costas_pct_manual / Decimal("100")
    elif obligacion.costas_tipo_proceso is not None and obligacion.costas_instancia is not None:
        costas_monto = calcular_agencias_en_derecho(
            tipo_proceso=TipoProceso(obligacion.costas_tipo_proceso),
            instancia=Instancia(obligacion.costas_instancia),
            pretensiones_reconocidas=pretensiones_reconocidas,
            fecha_radicacion=obligacion.fecha_origen,
        )
    else:
        return None

    return Event(
        date=obligacion.fecha_origen,
        payload={"amount": costas_monto, "label": f"Costas procesales - {obligacion.concepto}"},
        event_type="COSTAS_PROCESALES",
    )


class AreaStrategy(ABC):
    """Contrato comun para el calculo de liquidacion por area del derecho."""

    soporta_indexacion_ipc: bool = True

    @abstractmethod
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise NotImplementedError


class CivilFamiliaStrategy(AreaStrategy):
    """
    Unica area operable en el MVP original; ahora tambien soporta indexacion IPC
    opcional por obligacion (Sprint 8). Interes fijo por obligacion (tasa
    efectiva anual pactada/legal, Art. 1617 C.C.), convertido a tasa diaria.
    Indexacion (Art. corrección monetaria, PDF pag. 20-22): solo se activa por
    obligacion via `aplica_indexacion_ipc` -- es un juicio legal del abogado, no
    una regla automatica por categoria. La regla "no doble indexacion" del PDF
    (incompatible con SMMLV ya actualizado) no requiere un guard en tiempo de
    ejecucion: ningun campo de Obligacion usado por Civil/Familia representa un
    valor ya anclado a SMMLV (eso es exclusivo de Sancionatorio, que ya tiene
    soporta_indexacion_ipc=False), asi que la combinacion que la regla prohibe
    no es alcanzable con el modelo de datos actual.
    """

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        usar_suma_unica = self._resolver_suma_unica(obligaciones)

        eventos_causacion: List[Event] = []
        for obligacion in obligaciones:
            eventos_causacion.extend(self._eventos_de_obligacion(obligacion, fecha_corte))

        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos
        ]

        rate_provider = self._construir_rate_provider(obligaciones, fecha_corte)

        service = UniversalLiquidationService()
        return service.liquidar(
            eventos_causacion=eventos_causacion,
            pagos=pagos,
            fecha_corte=fecha_corte,
            rate_provider=rate_provider,
            usar_suma_unica=usar_suma_unica,
        )

    def _resolver_suma_unica(self, obligaciones: List) -> bool:
        """Determina si el expediente completo liquida con el algoritmo "Suma
        Única" (interes sobre capital ya indexado, PDF pag. 21-22, incluye la
        variante Ley 80/1993 para contratos estatales -- misma mecanica, sin
        campo propio) en vez del legado (interes solo sobre capital historico).
        El interes se acumula sobre un unico PendingDebt para todo el
        expediente, asi que el criterio no puede variar obligacion por
        obligacion dentro del mismo expediente -- si dos obligaciones
        indexadas traen valores distintos de interes_sobre_capital_indexado,
        es un error de captura, no una combinacion valida."""
        valores = {
            bool(o.interes_sobre_capital_indexado)
            for o in obligaciones
            if o.aplica_indexacion_ipc
        }
        if len(valores) > 1:
            raise ValueError(
                "Todas las obligaciones con indexación IPC del expediente deben usar el mismo "
                "criterio de interés (Suma Única o legado); no se puede mezclar dentro del mismo "
                "expediente."
            )
        return valores == {True}

    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> List[Event]:
        if obligacion.tipo.value == "PUNTUAL":
            eventos = [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": obligacion.valor, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]
            if obligacion.aplica_indexacion_ipc:
                eventos.append(
                    self._evento_indexacion(
                        fecha_causacion=obligacion.fecha_origen,
                        capital=obligacion.valor,
                        concepto=obligacion.concepto,
                        fecha_corte=fecha_corte,
                    )
                )
            evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=obligacion.valor)
            if evento_costas is not None:
                eventos.append(evento_costas)
            return eventos

        # RECURRENTE
        scheduler = FamilyScheduler()
        scheduler.add_monthly_obligation(
            amount=obligacion.valor,
            concept=obligacion.concepto,
            due_day=obligacion.dia_pago,
            category=obligacion.categoria,
        )
        fin = obligacion.fecha_fin or fecha_corte
        eventos_capital = scheduler.generate(start=obligacion.fecha_inicio, end=fin)

        if not obligacion.aplica_indexacion_ipc:
            return eventos_capital

        eventos = list(eventos_capital)
        for cuota in eventos_capital:
            eventos.append(
                self._evento_indexacion(
                    fecha_causacion=cuota.date,
                    capital=cuota.payload["amount"],
                    concepto=obligacion.concepto,
                    fecha_corte=fecha_corte,
                )
            )
        return eventos

    def _evento_indexacion(
        self, fecha_causacion: date, capital: Decimal, concepto: str, fecha_corte: date
    ) -> Event:
        monto = IPCIndexation.calculate(
            capital=capital,
            initial_index=get_ipc_interpolado_for_date(fecha_causacion),
            final_index=get_ipc_interpolado_for_date(fecha_corte),
        )
        return Event(
            date=fecha_causacion,
            payload={"amount": monto, "label": f"Indexación IPC — {concepto}"},
            event_type="INDEXATION",
        )

    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        fecha_mas_antigua = min(
            o.fecha_origen if o.tipo.value == "PUNTUAL" else o.fecha_inicio for o in obligaciones
        )
        # Usamos la tasa de la primera obligacion como tasa unica del expediente.
        # (Multiples tasas simultaneas por obligacion quedan fuera de alcance de este sprint.)
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligaciones[0].tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_mas_antigua - timedelta(days=1),
            end=fecha_corte,
            rate=tasa_diaria,
            source="Tasa pactada en la obligación (Art. 1617 C.C.)",
        )
        return provider


class ComercialStrategy(AreaStrategy):
    """
    Area Comercial (Art. 884 C.Co.). Cada obligacion debe traer su propia tasa
    remuneratoria (tasa_efectiva_anual), tasa moratoria (tasa_moratoria_anual),
    fecha de vencimiento y el IBC vigente aplicable (ibc_vigente_anual) -- no hay
    fallback automatico a un IBC de referencia en este sprint (ver Pendientes.md,
    Sprint 2 y Sprint 5).

    Split real de tasa remuneratoria (antes del vencimiento) / moratoria (despues)
    solo aplica a obligaciones PUNTUAL. RECURRENTE usa una sola tasa moratoria para
    todo el periodo, igual que CivilFamiliaStrategy, porque el vencimiento de cada
    cuota individual no esta modelado (ver docs/superpowers/specs/2026-07-15-area-comercial-design.md).

    No es compatible con indexacion IPC (soporta_indexacion_ipc = False).
    """

    soporta_indexacion_ipc = False

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_comercial(obligacion)

        eventos_causacion: List[Event] = []
        for obligacion in obligaciones:
            eventos_causacion.extend(self._eventos_de_obligacion(obligacion, fecha_corte))

        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos
        ]

        rate_provider = self._construir_rate_provider(obligaciones, fecha_corte)

        service = UniversalLiquidationService()
        return service.liquidar(
            eventos_causacion=eventos_causacion,
            pagos=pagos,
            fecha_corte=fecha_corte,
            rate_provider=rate_provider,
        )

    def _validar_obligacion_comercial(self, obligacion) -> None:
        campos_requeridos = {
            "tasa_efectiva_anual": obligacion.tasa_efectiva_anual,
            "tasa_moratoria_anual": obligacion.tasa_moratoria_anual,
            "fecha_vencimiento": obligacion.fecha_vencimiento,
            "ibc_vigente_anual": obligacion.ibc_vigente_anual,
        }
        for nombre_campo, valor in campos_requeridos.items():
            if valor is None:
                raise ValueError(
                    f"La obligacion comercial '{obligacion.concepto}' necesita el campo "
                    f"'{nombre_campo}' para liquidar."
                )

        if obligacion.fecha_vencimiento < obligacion.fecha_origen:
            raise ValueError(
                f"La obligacion comercial '{obligacion.concepto}' tiene fecha_vencimiento "
                f"({obligacion.fecha_vencimiento}) anterior a fecha_origen ({obligacion.fecha_origen})."
            )

        validar_tasa_usura(
            obligacion.tasa_efectiva_anual, obligacion.ibc_vigente_anual, "remuneratoria",
            obligacion.fecha_origen,
        )
        validar_tasa_usura(
            obligacion.tasa_moratoria_anual, obligacion.ibc_vigente_anual, "moratoria",
            obligacion.fecha_origen,
        )

        if obligacion.moneda not in (None, "COP"):
            if obligacion.trm_aplicable is None:
                raise ValueError(
                    f"La obligacion comercial '{obligacion.concepto}' esta en "
                    f"{obligacion.moneda} y necesita el campo 'trm_aplicable' para liquidar."
                )
            if obligacion.trm_aplicable <= 0:
                raise ValueError(
                    f"La obligacion comercial '{obligacion.concepto}' tiene 'trm_aplicable' "
                    f"({obligacion.trm_aplicable}) que no es un valor positivo."
                )
            if obligacion.trm_fecha_referencia is None:
                raise ValueError(
                    f"La obligacion comercial '{obligacion.concepto}' esta en "
                    f"{obligacion.moneda} y necesita el campo 'trm_fecha_referencia' para liquidar."
                )

        if obligacion.anatocismo_demanda_judicial and obligacion.anatocismo_fecha_acuerdo is not None:
            raise ValueError(
                f"La obligacion comercial '{obligacion.concepto}' no puede tener "
                f"'anatocismo_demanda_judicial' y 'anatocismo_fecha_acuerdo' activos a la vez "
                f"(son dos vias habilitantes excluyentes del Art. 886 C.Co.)."
            )

        anatocismo_activo = (
            obligacion.anatocismo_demanda_judicial or obligacion.anatocismo_fecha_acuerdo is not None
        )
        if anatocismo_activo and obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion comercial '{obligacion.concepto}' tiene anatocismo activo, pero "
                f"el anatocismo solo aplica a obligaciones PUNTUAL (RECURRENTE no modela un "
                f"vencimiento por cuota individual)."
            )

        if obligacion.anatocismo_fecha_acuerdo is not None:
            fecha_minima_acuerdo = obligacion.fecha_vencimiento + timedelta(days=365)
            if obligacion.anatocismo_fecha_acuerdo < fecha_minima_acuerdo:
                raise ValueError(
                    f"La obligacion comercial '{obligacion.concepto}' tiene 'anatocismo_fecha_acuerdo' "
                    f"({obligacion.anatocismo_fecha_acuerdo}) que no cumple el año de anterioridad "
                    f"exigido por el Art. 886 C.Co. (debe ser >= {fecha_minima_acuerdo})."
                )

    def _valor_en_pesos(self, obligacion) -> Decimal:
        if obligacion.moneda in (None, "COP"):
            return obligacion.valor
        provider = ManualTRMProvider(obligacion.trm_aplicable)
        return convertir_a_pesos(
            valor=obligacion.valor,
            moneda=obligacion.moneda,
            provider=provider,
            fecha_referencia=obligacion.trm_fecha_referencia,
        )

    def _fecha_capitalizacion_anatocismo(self, obligacion) -> Optional[date]:
        if obligacion.anatocismo_demanda_judicial:
            return obligacion.fecha_vencimiento + timedelta(days=365)
        if obligacion.anatocismo_fecha_acuerdo is not None:
            return obligacion.anatocismo_fecha_acuerdo
        return None

    def _eventos_anatocismo(self, obligacion, fecha_corte: date) -> List[Event]:
        fecha_capitalizacion = self._fecha_capitalizacion_anatocismo(obligacion)
        if fecha_capitalizacion is None or fecha_capitalizacion > fecha_corte:
            return []

        eventos: List[Event] = []
        fecha_evento = fecha_capitalizacion
        while fecha_evento <= fecha_corte:
            eventos.append(
                Event(
                    date=fecha_evento,
                    payload={
                        "label": "Capitalización de intereses (Art. 886 C.Co. — anatocismo comercial)"
                    },
                    event_type="CAPITALIZACION_INTERESES_ANATOCISMO",
                )
            )
            fecha_evento += timedelta(days=365)
        return eventos

    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> List[Event]:
        valor_pesos = self._valor_en_pesos(obligacion)
        if obligacion.tipo.value == "PUNTUAL":
            eventos = [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": valor_pesos, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]
            eventos.extend(self._eventos_anatocismo(obligacion, fecha_corte))
            evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=valor_pesos)
            if evento_costas is not None:
                eventos.append(evento_costas)
            return eventos

        # RECURRENTE
        scheduler = FamilyScheduler()
        scheduler.add_monthly_obligation(
            amount=valor_pesos,
            concept=obligacion.concepto,
            due_day=obligacion.dia_pago,
            category=obligacion.categoria,
        )
        fin = obligacion.fecha_fin or fecha_corte
        return scheduler.generate(start=obligacion.fecha_inicio, end=fin)

    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        provider = MemoryRateProvider()

        for obligacion in obligaciones:
            tasa_moratoria_diaria = EffectiveRateConverter.annual_to_daily(obligacion.tasa_moratoria_anual)

            if obligacion.tipo.value == "PUNTUAL":
                tasa_remuneratoria_diaria = EffectiveRateConverter.annual_to_daily(obligacion.tasa_efectiva_anual)
                inicio_remuneratorio = obligacion.fecha_origen - timedelta(days=1)
                fin_remuneratorio = min(obligacion.fecha_vencimiento, fecha_corte)
                provider.add_rate_period(
                    start=inicio_remuneratorio,
                    end=fin_remuneratorio,
                    rate=tasa_remuneratoria_diaria,
                    source="Tasa remuneratoria pactada (Art. 884 C.Co.)",
                )
                if obligacion.fecha_vencimiento < fecha_corte:
                    inicio_moratorio = obligacion.fecha_vencimiento + timedelta(days=1)
                    provider.add_rate_period(
                        start=inicio_moratorio,
                        end=fecha_corte,
                        rate=tasa_moratoria_diaria,
                        source="Tasa moratoria pactada (Art. 884 C.Co.)",
                    )
            else:
                # RECURRENTE: sin split por cuota individual (alcance reducido, ver spec).
                inicio = obligacion.fecha_inicio - timedelta(days=1)
                provider.add_rate_period(
                    start=inicio,
                    end=fecha_corte,
                    rate=tasa_moratoria_diaria,
                    source="Tasa moratoria pactada (Art. 884 C.Co.)",
                )

        return provider


class LaboralStrategy(AreaStrategy):
    """
    Area Laboral. Liquidacion final (finiquito) de UN contrato de trabajo por
    expediente: cesantias, intereses a cesantias, prima (junio/diciembre) y
    vacaciones (LaborScheduler), mas la indemnizacion moratoria bifasica del
    Art. 65 CST (MoratoryIndemnityCalculator) si el pago real o la fecha de
    corte quedan despues de la fecha de terminacion del contrato.

    No es compatible con indexacion IPC (soporta_indexacion_ipc = False): las
    prestaciones sociales se liquidan sobre el salario nominal vigente al
    momento de la causacion, no se indexan por perdida de poder adquisitivo.

    Seguridad social (cotizaciones IBC, pension, salud, ARL, FSP) es opt-in
    via el flag `incluir_seguridad_social` de la obligacion (requiere ademas
    `nivel_riesgo_arl`, I-V) -- ver Pendientes.md, Sprint 16, y
    docs/superpowers/specs/2026-07-18-area-laboral-design.md.
    """

    soporta_indexacion_ipc = False

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")
        if len(obligaciones) != 1:
            raise ValueError(
                "El area Laboral liquida un solo contrato (una obligacion) por expediente."
            )

        obligacion = obligaciones[0]
        self._validar_obligacion_laboral(obligacion)

        dias_trabajados = (obligacion.fecha_fin - obligacion.fecha_inicio).days
        eventos = LaborScheduler(
            salario_base=obligacion.valor,
            dias_trabajados=dias_trabajados,
            fecha_liquidacion=obligacion.fecha_fin,
        ).generate()

        monto_prestaciones = sum((e.payload["amount"] for e in eventos), Decimal("0.00"))

        evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=monto_prestaciones)
        if evento_costas is not None:
            eventos.append(evento_costas)

        if obligacion.incluir_seguridad_social:
            dias_suspension = sum(
                (evento.fecha_fin - evento.fecha_inicio).days
                for evento in obligacion.eventos_laborales
                if evento.tipo.value == "SUSPENSION"
            )
            cotizaciones = SeguridadSocialCalculator.calcular(
                salario_base=obligacion.valor,
                dias_trabajados=dias_trabajados,
                dias_suspension=dias_suspension,
                nivel_riesgo_arl=obligacion.nivel_riesgo_arl,
                fecha_referencia=obligacion.fecha_fin,
            )
            for concepto, monto, etiqueta in [
                ("COTIZACION_PENSION", cotizaciones.monto_pension, "Cotizacion Pension (seguridad social no pagada)"),
                ("COTIZACION_SALUD", cotizaciones.monto_salud, "Cotizacion Salud (seguridad social no pagada)"),
                ("COTIZACION_ARL", cotizaciones.monto_arl, "Cotizacion ARL (seguridad social no pagada)"),
                ("COTIZACION_FSP", cotizaciones.monto_fsp, "Cotizacion FSP (Fondo de Solidaridad Pensional)"),
            ]:
                if monto > Decimal("0.00"):
                    eventos.append(Event(
                        date=obligacion.fecha_fin,
                        payload={"amount": monto, "label": etiqueta},
                        event_type=concepto,
                    ))

            for evento in obligacion.eventos_laborales:
                if evento.tipo.value == "SUSPENSION":
                    eventos.append(Event(
                        date=evento.fecha_fin,
                        payload={
                            "amount": Decimal("0.00"),
                            "label": (
                                f"Suspension ({evento.motivo_suspension.value}) "
                                f"{evento.fecha_inicio}-{evento.fecha_fin}: no causa ARL"
                            ),
                        },
                        event_type="SUSPENSION_INFORMATIVA",
                    ))
                else:
                    dias_incapacidad = (evento.fecha_fin - evento.fecha_inicio).days
                    desglose = IncapacidadCalculator.calcular(
                        tipo=evento.tipo, ibc_mensual=cotizaciones.ibc_mensual,
                        dias_incapacidad=dias_incapacidad,
                    )
                    for tramo in desglose.tramos:
                        es_empleador = tramo.pagador == "EMPLEADOR"
                        eventos.append(Event(
                            date=evento.fecha_fin,
                            payload={
                                "amount": tramo.monto if es_empleador else Decimal("0.00"),
                                "label": (
                                    f"Incapacidad {evento.tipo.value} dias {tramo.dias} - "
                                    f"{tramo.pagador} ({tramo.porcentaje:.2%}): ${tramo.monto:,.2f}"
                                ),
                            },
                            event_type="INCAPACIDAD_EMPLEADOR" if es_empleador else "INCAPACIDAD_INFORMATIVA",
                        ))

        # fecha_pago_total (si existe) es cuando realmente se extinguio la
        # deuda; nunca puede ser posterior a fecha_corte para efectos de este
        # reporte -- si el pago real fue despues del corte elegido, la mora
        # se calcula solo hasta el corte (foto historica), no hasta el pago.
        if obligacion.fecha_pago_total is not None:
            fecha_referencia_mora = min(obligacion.fecha_pago_total, fecha_corte)
        else:
            fecha_referencia_mora = fecha_corte

        if fecha_referencia_mora > obligacion.fecha_fin:
            monto_adeudado = monto_prestaciones
            mora = MoratoryIndemnityCalculator.calcular(
                salario_mensual=obligacion.valor,
                monto_adeudado=monto_adeudado,
                fecha_terminacion=obligacion.fecha_fin,
                fecha_pago_o_corte=fecha_referencia_mora,
            )
            if mora.total > Decimal("0.00"):
                eventos.append(Event(
                    date=fecha_referencia_mora,
                    payload={"amount": mora.total, "label": "Indemnizacion moratoria Art. 65 CST"},
                    event_type="SANCION_MORATORIA",
                ))

        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos
        ]

        service = UniversalLiquidationService()
        return service.liquidar(
            eventos_causacion=eventos,
            pagos=pagos,
            fecha_corte=fecha_corte,
        )
        # Sin rate_provider: la tasa diaria generica de UniversalLiquidationService
        # queda en 0 por defecto. Toda la mora del area Laboral ya esta resuelta
        # en el evento SANCION_MORATORIA -- pasar un rate_provider aqui
        # duplicaria el castigo por mora.

    def _validar_obligacion_laboral(self, obligacion) -> None:
        if obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                "El area Laboral solo admite obligaciones de tipo PUNTUAL "
                "(un contrato completo); RECURRENTE no aplica a prestaciones sociales."
            )
        if obligacion.valor is None or obligacion.valor <= Decimal("0.00"):
            raise ValueError("El salario base de la obligacion laboral debe ser mayor que cero.")
        if obligacion.fecha_inicio is None or obligacion.fecha_fin is None:
            raise ValueError(
                "La obligacion laboral necesita 'fecha_inicio' y 'fecha_fin' del contrato."
            )
        if obligacion.fecha_fin <= obligacion.fecha_inicio:
            raise ValueError(
                f"La fecha de terminacion ({obligacion.fecha_fin}) debe ser posterior a la "
                f"fecha de inicio del contrato ({obligacion.fecha_inicio})."
            )
        if obligacion.pagada and obligacion.fecha_pago_total is None:
            raise ValueError(
                "Una obligacion marcada como pagada debe tener 'fecha_pago_total'."
            )
        if obligacion.incluir_seguridad_social and not obligacion.nivel_riesgo_arl:
            raise ValueError(
                "Si se incluyen cotizaciones de seguridad social, 'nivel_riesgo_arl' "
                "(I-V) es obligatorio."
            )
        if obligacion.eventos_laborales and not obligacion.incluir_seguridad_social:
            raise ValueError(
                "Hay eventos contractuales (suspension/incapacidad) registrados, pero "
                "'incluir_seguridad_social' no esta activado. Marca la casilla 'Incluir "
                "cotizaciones de seguridad social no pagadas' para que estos eventos se "
                "reflejen en la liquidacion."
            )

        for evento in obligacion.eventos_laborales:
            if evento.fecha_inicio < obligacion.fecha_inicio or evento.fecha_fin > obligacion.fecha_fin:
                raise ValueError(
                    f"El evento contractual del {evento.fecha_inicio} al {evento.fecha_fin} "
                    "cae fuera del rango del contrato "
                    f"({obligacion.fecha_inicio} a {obligacion.fecha_fin})."
                )

        eventos_ordenados = sorted(obligacion.eventos_laborales, key=lambda e: e.fecha_inicio)
        for anterior, siguiente in zip(eventos_ordenados, eventos_ordenados[1:]):
            if anterior.fecha_fin > siguiente.fecha_inicio:
                raise ValueError(
                    "Dos eventos contractuales se solapan en el tiempo: "
                    f"{anterior.fecha_inicio}-{anterior.fecha_fin} y "
                    f"{siguiente.fecha_inicio}-{siguiente.fecha_fin}."
                )


class SancionatorioStrategy(AreaStrategy):
    """
    Area Sancionatorio (multas SIC/Penal/Ambiental/Urbano en SMLMV o UVT, Ley 1955/2019
    art. 49). Cada obligacion es un hecho puntual: `cantidad_smlmv_uvt` se convierte a
    pesos segun la fecha del hecho (`fecha_origen`) via `resolver_base_sancion` -- SMLMV
    si es anterior a 2020-01-01, UVT (tabla historica 2006-2026) si es posterior.

    No soporta obligaciones RECURRENTE (una multa es un hecho unico).
    No es compatible con indexacion IPC: el monto ya esta expresado en una unidad
    actualizada (SMLMV/UVT), indexarlo otra vez seria doble indexacion.
    """

    soporta_indexacion_ipc = False

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_sancionatoria(obligacion)

        eventos_causacion = []
        for obligacion in obligaciones:
            eventos_causacion.extend(self._eventos_de_obligacion(obligacion))

        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos
        ]

        rate_provider = self._construir_rate_provider(obligaciones, fecha_corte)

        service = UniversalLiquidationService()
        return service.liquidar(
            eventos_causacion=eventos_causacion,
            pagos=pagos,
            fecha_corte=fecha_corte,
            rate_provider=rate_provider,
        )

    def _validar_obligacion_sancionatoria(self, obligacion) -> None:
        if obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion sancionatoria '{obligacion.concepto}' debe ser PUNTUAL "
                f"(una multa es un hecho unico, no admite RECURRENTE)."
            )
        if obligacion.cantidad_smlmv_uvt is None:
            raise ValueError(
                f"La obligacion sancionatoria '{obligacion.concepto}' necesita el campo "
                f"'cantidad_smlmv_uvt' para liquidar."
            )

    def _eventos_de_obligacion(self, obligacion) -> List[Event]:
        monto_pesos = resolver_base_sancion(obligacion.fecha_origen, obligacion.cantidad_smlmv_uvt)
        eventos = [
            Event(
                date=obligacion.fecha_origen,
                payload={"amount": monto_pesos, "label": obligacion.concepto},
                event_type=obligacion.categoria,
            )
        ]
        evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=monto_pesos)
        if evento_costas is not None:
            eventos.append(evento_costas)
        return eventos

    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        fecha_mas_antigua = min(o.fecha_origen for o in obligaciones)
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligaciones[0].tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_mas_antigua - timedelta(days=1), end=fecha_corte, rate=tasa_diaria
        )
        return provider


class HonorariosStrategy(AreaStrategy):
    """
    Area Honorarios / Litigio (cobro de honorarios profesionales y costas judiciales).
    Cada obligacion es un hecho puntual que resulta en 1 o 2 eventos de capital:
    honorarios profesionales (tarifa fija + cuota litis, validados contra ambos topes
    legales) y, si aplica, un evento adicional de costas procesales. Costas procesales:
    `costas_pct_manual` (si el juez ya fijo un porcentaje en el auto) tiene prioridad;
    si no esta seteado, se calcula automaticamente segun el Acuerdo PSAA16-10554 (tabla
    completa en `app/engine/costs/agencias_en_derecho.py`) cuando la obligacion trae
    `costas_tipo_proceso`/`costas_instancia`.

    Tope de cuota litis (ambos simultaneos -- ver design spec 2026-07-17, el PDF trae
    un 50% en una seccion y un 30% en otra, se aplican los dos):
    - cuota litis sola <= 30% del beneficio obtenido (Ley 1123/2007, CPC).
    - honorarios fijos + cuota litis <= 50% del beneficio obtenido (limite
      jurisprudencial y etico).

    No soporta obligaciones RECURRENTE. No es compatible con indexacion IPC.
    """

    soporta_indexacion_ipc = False

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_honorarios(obligacion)

        eventos_causacion: List[Event] = []
        for obligacion in obligaciones:
            eventos_causacion.extend(self._eventos_de_obligacion(obligacion))

        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos
        ]

        rate_provider = self._construir_rate_provider(obligaciones, fecha_corte)

        service = UniversalLiquidationService()
        return service.liquidar(
            eventos_causacion=eventos_causacion,
            pagos=pagos,
            fecha_corte=fecha_corte,
            rate_provider=rate_provider,
        )

    def _validar_obligacion_honorarios(self, obligacion) -> None:
        if obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion de honorarios '{obligacion.concepto}' debe ser PUNTUAL."
            )
        campos_requeridos = {
            "honorarios_fijos_pactados": obligacion.honorarios_fijos_pactados,
            "cuota_litis_pactada_pct": obligacion.cuota_litis_pactada_pct,
            "beneficio_obtenido": obligacion.beneficio_obtenido,
        }
        for nombre_campo, valor in campos_requeridos.items():
            if valor is None:
                raise ValueError(
                    f"La obligacion de honorarios '{obligacion.concepto}' necesita el campo "
                    f"'{nombre_campo}' para liquidar."
                )

        cuota_litis_monto = self._cuota_litis_monto(obligacion)
        tope_individual_pct = get_parametro("CUOTA_LITIS_INDIVIDUAL_PCT", obligacion.fecha_origen)
        tope_individual = obligacion.beneficio_obtenido * tope_individual_pct / Decimal("100")
        if cuota_litis_monto > tope_individual:
            raise CuotaLitisExcedeTopeError(
                f"La cuota litis pactada ({obligacion.cuota_litis_pactada_pct}%) de "
                f"'{obligacion.concepto}' equivale a {cuota_litis_monto}, que excede el tope "
                f"del 30% del beneficio obtenido ({tope_individual})."
            )

        total_honorarios = obligacion.honorarios_fijos_pactados + cuota_litis_monto
        tope_total_pct = get_parametro("HONORARIOS_TOTAL_PCT", obligacion.fecha_origen)
        tope_total = obligacion.beneficio_obtenido * tope_total_pct / Decimal("100")
        if total_honorarios > tope_total:
            raise CuotaLitisExcedeTopeError(
                f"La suma de honorarios fijos + cuota litis de '{obligacion.concepto}' "
                f"({total_honorarios}) excede el tope del 50% del beneficio obtenido ({tope_total})."
            )

    def _cuota_litis_monto(self, obligacion) -> Decimal:
        return obligacion.beneficio_obtenido * obligacion.cuota_litis_pactada_pct / Decimal("100")

    def _eventos_de_obligacion(self, obligacion) -> List[Event]:
        cuota_litis_monto = self._cuota_litis_monto(obligacion)
        total_honorarios = obligacion.honorarios_fijos_pactados + cuota_litis_monto

        eventos = [
            Event(
                date=obligacion.fecha_origen,
                payload={"amount": total_honorarios, "label": obligacion.concepto},
                event_type=obligacion.categoria,
            )
        ]
        evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=obligacion.beneficio_obtenido)
        if evento_costas is not None:
            eventos.append(evento_costas)
        return eventos

    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        fecha_mas_antigua = min(o.fecha_origen for o in obligaciones)
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligaciones[0].tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_mas_antigua - timedelta(days=1), end=fecha_corte, rate=tasa_diaria
        )
        return provider


class TributarioStrategy(AreaStrategy):
    """
    Area Tributario (cierre del Sprint 11b): impuesto a cargo, 3 sanciones (extemporaneidad,
    inexactitud, error aritmetico) y Renta Liquida Gravable informativa.

    Reutiliza el motor generico de liquidacion (UniversalLiquidationService/LiquidationCore)
    en vez de un motor de imputacion dedicado: el impuesto a cargo cae en el bucket
    'principal' (event_type = obligacion.categoria = "IMPUESTO_A_CARGO", agregado a
    _capital_concepts igual que cada area anterior), las 3 sanciones se normalizan a un unico
    event_type "SANCION_TRIBUTARIA" que cae en el bucket 'indexation'. El orden de pago que
    ya aplica AllocationEngine (indexacion -> interes -> capital) coincide exactamente con el
    orden exigido para tributario (sanciones -> intereses -> impuesto) -- ver design spec,
    seccion "Arquitectura".

    El interes automatico (E.T. art. 635, nunca pactado) reutiliza
    construir_rate_provider_moratorio_tributario del Sprint 11a.

    "RENTA_LIQUIDA" no genera ningun evento de causacion -- es informativo (base gravable,
    no una deuda exigible) y se adjunta aparte en LiquidationResult.renta_liquida. Un
    expediente admite como maximo una obligacion "RENTA_LIQUIDA" (un solo periodo gravable
    por liquidacion).

    No es compatible con indexacion IPC (soporta_indexacion_ipc = False). El PDF (pag. 40)
    advierte que no se pueden cobrar simultaneamente intereses moratorios y actualizacion
    monetaria si eso conduce a una tasa usuraria o doble pago por el mismo concepto (mismo
    criterio ya exigido en Sprint 2 para la incompatibilidad interes-comercial + IPC). Aqui
    esa combinacion no requiere un guard en tiempo de ejecucion: el formulario de la GUI
    oculta el checkbox "aplica indexacion IPC" para el area TRIBUTARIO (ver obligaciones.py)
    y _evento_de_obligacion, a diferencia de CivilFamiliaStrategy, nunca lee
    obligacion.aplica_indexacion_ipc -- por lo que ninguna obligacion tributaria puede
    generar a la vez el interes automatico E.T. 635 y un evento de correccion monetaria IPC
    sobre el mismo hecho. La advertencia del PDF no aplica por construccion, no por una
    validacion explicita en tiempo de ejecucion.
    """

    soporta_indexacion_ipc = False

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        obligaciones_renta_liquida = [o for o in obligaciones if o.categoria == "RENTA_LIQUIDA"]
        if len(obligaciones_renta_liquida) > 1:
            raise ValueError(
                "Un expediente tributario admite una sola obligacion 'RENTA_LIQUIDA' "
                "(un solo periodo gravable por liquidacion)."
            )

        obligaciones_deuda = [o for o in obligaciones if o.categoria != "RENTA_LIQUIDA"]
        for obligacion in obligaciones_deuda:
            self._validar_obligacion_tributaria(obligacion)

        eventos_causacion = [self._evento_de_obligacion(o) for o in obligaciones_deuda]

        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos
        ]

        rate_provider = self._construir_rate_provider(obligaciones_deuda, fecha_corte)

        service = UniversalLiquidationService()
        resultado = service.liquidar(
            eventos_causacion=eventos_causacion,
            pagos=pagos,
            fecha_corte=fecha_corte,
            rate_provider=rate_provider,
        )

        if obligaciones_renta_liquida:
            obligacion_renta = obligaciones_renta_liquida[0]
            renta_liquida = depurar_renta_liquida_gravable(
                ingresos_brutos=obligacion_renta.ingresos_brutos,
                devoluciones_rebajas_descuentos=obligacion_renta.devoluciones_rebajas_descuentos,
                costos=obligacion_renta.costos,
                deducciones=obligacion_renta.deducciones,
                rentas_exentas=obligacion_renta.rentas_exentas,
            )
            resultado = replace(resultado, renta_liquida=renta_liquida)

        return resultado

    def _validar_obligacion_tributaria(self, obligacion) -> None:
        if obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion tributaria '{obligacion.concepto}' debe ser PUNTUAL "
                f"(un hecho tributario es un evento unico, no admite RECURRENTE)."
            )

        if obligacion.categoria == "IMPUESTO_A_CARGO":
            if obligacion.valor is None or obligacion.valor <= Decimal("0.00"):
                raise ValueError(
                    f"El impuesto a cargo '{obligacion.concepto}' debe tener 'valor' mayor que cero."
                )
            return

        if obligacion.categoria == "SANCION_EXTEMPORANEIDAD":
            if obligacion.base_sancion_tributaria is None or obligacion.meses_extemporaneidad is None:
                raise ValueError(
                    f"La sancion por extemporaneidad '{obligacion.concepto}' necesita "
                    f"'base_sancion_tributaria' y 'meses_extemporaneidad'."
                )
            return

        if obligacion.categoria == "SANCION_INEXACTITUD":
            if obligacion.base_sancion_tributaria is None:
                raise ValueError(
                    f"La sancion por inexactitud '{obligacion.concepto}' necesita "
                    f"'base_sancion_tributaria' (la diferencia entre el saldo determinado y el declarado)."
                )
            return

        if obligacion.categoria == "SANCION_ERROR_ARITMETICO":
            if obligacion.base_sancion_tributaria is None:
                raise ValueError(
                    f"La sancion por error aritmetico '{obligacion.concepto}' necesita "
                    f"'base_sancion_tributaria' (la diferencia generada por el error)."
                )
            return

        raise ValueError(
            f"Categoria tributaria desconocida: '{obligacion.categoria}'."
        )

    def _evento_de_obligacion(self, obligacion) -> Event:
        if obligacion.categoria == "IMPUESTO_A_CARGO":
            return Event(
                date=obligacion.fecha_origen,
                payload={"amount": obligacion.valor, "label": obligacion.concepto},
                event_type=obligacion.categoria,
            )

        monto_sancion = self._calcular_monto_sancion(obligacion)
        return Event(
            date=obligacion.fecha_origen,
            payload={"amount": monto_sancion, "label": obligacion.concepto},
            event_type="SANCION_TRIBUTARIA",
        )

    def _calcular_monto_sancion(self, obligacion) -> Decimal:
        if obligacion.categoria == "SANCION_EXTEMPORANEIDAD":
            return calcular_sancion_extemporaneidad(
                impuesto_a_cargo=obligacion.base_sancion_tributaria,
                meses_o_fraccion=obligacion.meses_extemporaneidad,
                fecha_referencia=obligacion.fecha_origen,
            )
        if obligacion.categoria == "SANCION_INEXACTITUD":
            return calcular_sancion_inexactitud(
                diferencia=obligacion.base_sancion_tributaria,
                agravada=bool(obligacion.sancion_agravada),
                fecha_referencia=obligacion.fecha_origen,
            )
        # SANCION_ERROR_ARITMETICO (unica categoria de sancion restante, ya validada arriba)
        return calcular_sancion_error_aritmetico(
            diferencia=obligacion.base_sancion_tributaria,
            fecha_referencia=obligacion.fecha_origen,
        )

    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        if not obligaciones:
            return MemoryRateProvider()
        fecha_mas_antigua = min(o.fecha_origen for o in obligaciones)
        provider = construir_rate_provider_moratorio_tributario(fecha_mas_antigua, fecha_corte)
        # construir_rate_provider_moratorio_tributario solo cubre desde el dia siguiente a la
        # exigibilidad (inicio_mora = fecha_mas_antigua + 1 dia, la mora nunca corre el mismo
        # dia en que nace la obligacion -- ver docstring del modulo). LiquidationCore, sin
        # embargo, consulta la tasa del propio dia de cada evento (incluyendo el evento de
        # causacion del capital/sancion, que cae justo en fecha_mas_antigua) solo para
        # trazabilidad/metadata, no para acumular interes ese dia. Sin este relleno, un
        # MemoryRateProvider vacio (caso comun: fecha_corte == fecha_mas_antigua, sin mora
        # todavia) lanzaria ValueError al liquidar. 0% es la tasa correcta para ese dia: no hay
        # mora antes de que empiece a correr.
        provider.add_rate_period(
            start=fecha_mas_antigua,
            end=fecha_mas_antigua,
            rate=Rate(Decimal("0.0")),
            source="Sin mora (fecha de exigibilidad, aun no corre el interes del E.T. art. 635)",
        )
        return provider
