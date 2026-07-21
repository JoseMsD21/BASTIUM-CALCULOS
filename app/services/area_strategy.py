from abc import ABC, abstractmethod
from datetime import date, timedelta
from decimal import Decimal
from typing import List

from app.core.exceptions import CuotaLitisExcedeTopeError
from app.domain.obligation.payment import Payment
from app.engine.financial.rate import Rate
from app.engine.interest.provider import MemoryRateProvider
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.engine.currency.converter import convertir_a_pesos
from app.engine.currency.trm_provider import ManualTRMProvider
from app.engine.labor.moratory_indemnity import MoratoryIndemnityCalculator
from app.engine.liquidation.result import LiquidationResult
from app.engine.temporal.schedulers.base import Event
from app.engine.temporal.schedulers.family import FamilyScheduler
from app.engine.temporal.schedulers.labor import LaborScheduler
from app.engine.interest.usury_validator import validar_tasa_usura
from app.engine.indexation.smlmv_to_uvt import resolver_base_sancion
from app.engine.indexation.historical_index import get_ipc_interpolado_for_date
from app.engine.indexation.ipc import IPCIndexation
from app.services.motor_universal import UniversalLiquidationService


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

        validar_tasa_usura(obligacion.tasa_efectiva_anual, obligacion.ibc_vigente_anual, "remuneratoria")
        validar_tasa_usura(obligacion.tasa_moratoria_anual, obligacion.ibc_vigente_anual, "moratoria")

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

    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> List[Event]:
        valor_pesos = self._valor_en_pesos(obligacion)
        if obligacion.tipo.value == "PUNTUAL":
            return [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": valor_pesos, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]

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

    Seguridad social (cotizaciones IBC, pension, salud, ARL, FSP) queda fuera
    de alcance de este sprint -- ver Pendientes.md, Sprint 3, y
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

        # fecha_pago_total (si existe) es cuando realmente se extinguio la
        # deuda; nunca puede ser posterior a fecha_corte para efectos de este
        # reporte -- si el pago real fue despues del corte elegido, la mora
        # se calcula solo hasta el corte (foto historica), no hasta el pago.
        if obligacion.fecha_pago_total is not None:
            fecha_referencia_mora = min(obligacion.fecha_pago_total, fecha_corte)
        else:
            fecha_referencia_mora = fecha_corte

        if fecha_referencia_mora > obligacion.fecha_fin:
            monto_adeudado = sum((e.payload["amount"] for e in eventos), Decimal("0.00"))
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


class SancionatorioStrategy(AreaStrategy):
    """
    Area Sancionatorio (multas SIC/Penal/Ambiental/Urbano en SMLMV o UVT, Ley 1955/2019
    art. 49). Cada obligacion es un hecho puntual: `cantidad_smlmv_uvt` se convierte a
    pesos segun la fecha del hecho (`fecha_origen`) via `resolver_base_sancion` -- SMLMV
    si es anterior a 2020-01-01, UVT (todavia no disponible) si es posterior.

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

        eventos_causacion = [self._evento_de_obligacion(obligacion) for obligacion in obligaciones]

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

    def _evento_de_obligacion(self, obligacion) -> Event:
        monto_pesos = resolver_base_sancion(obligacion.fecha_origen, obligacion.cantidad_smlmv_uvt)
        return Event(
            date=obligacion.fecha_origen,
            payload={"amount": monto_pesos, "label": obligacion.concepto},
            event_type=obligacion.categoria,
        )

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
    legales) y, si se pacto un porcentaje de costas, un evento adicional de costas
    procesales. No hay tabla hardcodeada de rangos del Consejo Superior de la
    Judicatura (Acuerdo PCSJA20-11556): el porcentaje de costas lo ingresa quien
    liquida, fijado por el juez en el auto respectivo (ver Pendientes.md).

    Tope de cuota litis (ambos simultaneos -- ver design spec 2026-07-17, el PDF trae
    un 50% en una seccion y un 30% en otra, se aplican los dos):
    - cuota litis sola <= 30% del beneficio obtenido (Ley 1123/2007, CPC).
    - honorarios fijos + cuota litis <= 50% del beneficio obtenido (limite
      jurisprudencial y etico).

    No soporta obligaciones RECURRENTE. No es compatible con indexacion IPC.
    """

    TOPE_CUOTA_LITIS_INDIVIDUAL_PCT = Decimal("30")
    TOPE_HONORARIOS_TOTAL_PCT = Decimal("50")

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
        tope_individual = obligacion.beneficio_obtenido * self.TOPE_CUOTA_LITIS_INDIVIDUAL_PCT / Decimal("100")
        if cuota_litis_monto > tope_individual:
            raise CuotaLitisExcedeTopeError(
                f"La cuota litis pactada ({obligacion.cuota_litis_pactada_pct}%) de "
                f"'{obligacion.concepto}' equivale a {cuota_litis_monto}, que excede el tope "
                f"del 30% del beneficio obtenido ({tope_individual})."
            )

        total_honorarios = obligacion.honorarios_fijos_pactados + cuota_litis_monto
        tope_total = obligacion.beneficio_obtenido * self.TOPE_HONORARIOS_TOTAL_PCT / Decimal("100")
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
        if obligacion.costas_pct_manual is not None:
            costas_monto = obligacion.beneficio_obtenido * obligacion.costas_pct_manual / Decimal("100")
            eventos.append(
                Event(
                    date=obligacion.fecha_origen,
                    payload={
                        "amount": costas_monto,
                        "label": f"Costas procesales - {obligacion.concepto}",
                    },
                    event_type="COSTAS_PROCESALES",
                )
            )
        return eventos

    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        fecha_mas_antigua = min(o.fecha_origen for o in obligaciones)
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligaciones[0].tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_mas_antigua - timedelta(days=1), end=fecha_corte, rate=tasa_diaria
        )
        return provider
