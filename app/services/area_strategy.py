from abc import ABC, abstractmethod
from datetime import date, timedelta
from decimal import Decimal
from typing import List

from app.core.exceptions import AreaNoImplementadaError, CuotaLitisExcedeTopeError
from app.domain.obligation.payment import Payment
from app.engine.financial.rate import Rate
from app.engine.interest.provider import MemoryRateProvider
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.engine.liquidation.result import LiquidationResult
from app.engine.temporal.schedulers.base import Event
from app.engine.temporal.schedulers.family import FamilyScheduler
from app.engine.interest.usury_validator import validar_tasa_usura
from app.engine.indexation.smlmv_to_uvt import resolver_base_sancion
from app.services.motor_universal import UniversalLiquidationService


class AreaStrategy(ABC):
    """Contrato comun para el calculo de liquidacion por area del derecho."""

    soporta_indexacion_ipc: bool = True

    @abstractmethod
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise NotImplementedError


class CivilFamiliaStrategy(AreaStrategy):
    """
    Unica area operable en este sprint.
    Interes fijo por obligacion (tasa efectiva anual pactada/legal, Art. 1617 C.C.),
    convertido a tasa diaria. No aplica indexacion IPC en este sprint (Ver Pendientes.md:
    depende de la carga de series historicas de IPC, que aun no existe).
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
            return [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": obligacion.valor, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]

        # RECURRENTE
        scheduler = FamilyScheduler()
        scheduler.add_monthly_obligation(
            amount=obligacion.valor,
            concept=obligacion.concepto,
            due_day=obligacion.dia_pago,
            category=obligacion.categoria,
        )
        fin = obligacion.fecha_fin or fecha_corte
        return scheduler.generate(start=obligacion.fecha_inicio, end=fin)

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

    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> List[Event]:
        if obligacion.tipo.value == "PUNTUAL":
            return [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": obligacion.valor, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]

        # RECURRENTE
        scheduler = FamilyScheduler()
        scheduler.add_monthly_obligation(
            amount=obligacion.valor,
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
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise AreaNoImplementadaError(
            "El area Laboral (Art. 65 CST, vacaciones) esta pendiente. Ver Pendientes.md."
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
