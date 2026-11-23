from collections.abc import Callable
from datetime import date, timedelta
from decimal import Decimal, localcontext

from app.engine.financial.rate import Rate
from app.engine.indexation.suma_unica_con_abonos import CausacionTramoATramo
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.provider import RateProvider
from app.engine.liquidation.allocation import AllocationEngine
from app.engine.liquidation.balance import BalanceEngine
from app.engine.liquidation.models import (
    LiquidationItem,
    PaymentAllocation,
    PendingDebt,
    RunningBalance,
)
from app.engine.liquidation.politica import PoliticaCausacion
from app.engine.liquidation.result import LiquidationResult
from app.engine.math.rounding import Rounding
from app.engine.temporal.schedulers.base import Event
from config.decimal_config import CONTEXTO_FORENSE

# Singleton de modulo (Sprint 48, B008): evita instanciar Rate(Decimal("0.0")) en cada
# definicion de LiquidationCore.__init__ -- Rate es inmutable, asi que reusar la misma
# instancia como default no cambia el comportamiento respecto a construirla en cada
# llamada.
_TASA_CERO = Rate(Decimal("0.0"))


class LiquidationCore:
    """
    Orquestador determinista de liquidaciones.
    Procesa eventos temporales secuenciales de cualquier dominio jurídico
    (Familia, Laboral, Civil, Comercial) e inyecta automáticamente
    causaciones de interés por el paso del tiempo.
    """

    def __init__(
        self,
        default_daily_rate: Rate = _TASA_CERO,
        rate_provider: RateProvider | None = None,
        usar_suma_unica: bool = False,
        estrategia_imputacion: Callable[
            [Decimal, PendingDebt, date], tuple[PaymentAllocation, PendingDebt, Decimal]
        ] = AllocationEngine.allocate,
        politica_causacion: PoliticaCausacion = PoliticaCausacion.LEGADA_DIARIA_REDONDEADA,
        causacion_tramo_a_tramo: CausacionTramoATramo | None = None,
    ):
        """`causacion_tramo_a_tramo` (Sprint 104): si se pasa, el paso del tiempo
        entre eventos ya no causa interes diario con el `rate_provider`, sino que
        aplica el algoritmo tramo a tramo del despacho (Suma Unica con abonos):
        reindexa `principal + indexation` desde el evento anterior y causa interes
        compuesto mensual sobre ese capital indexado (ver `CausacionTramoATramo`).
        None (default) deja el comportamiento de siempre, bit a bit."""
        self._politica_causacion = politica_causacion
        self._causacion_tramo_a_tramo = causacion_tramo_a_tramo
        self._current_debt = PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
        self._history: list[LiquidationItem] = []
        self._default_rate = default_daily_rate
        self._rate_provider = rate_provider
        self._usar_suma_unica = usar_suma_unica
        self._estrategia_imputacion = estrategia_imputacion
        self._last_event_date: date | None = None

        # Diccionario de rubros jurídicos reconocidos como Capital Base
        self._capital_concepts = {
            "INSTALLMENT",
            "CHILD_SUPPORT",
            "CLOTHING",
            "MULTA",
            "CESANTIAS",
            "INTERESES_CESANTIAS",
            "PRIMA_JUNIO",
            "PRIMA_DICIEMBRE",
            "SANCION_MORATORIA",
            # INDEMNIZACION_DESPIDO (Sprint 92): indemnizacion por despido
            # injustificado, Art. 64 CST -- concepto de capital distinto de
            # SANCION_MORATORIA (Art. 65 CST), pueden coexistir en el mismo
            # expediente. Ver LaboralStrategy.liquidar y
            # app/engine/labor/dismissal_indemnity.py.
            "INDEMNIZACION_DESPIDO",
            # HORAS_EXTRA (Sprint 95, conexion a la UI): horas extra
            # HED/HEN/HEFD/HEFN de un contrato Laboral, rubro propio -- ver
            # LaboralStrategy._eventos_horas_extra.
            "HORAS_EXTRA",
            "DANO_EMERGENTE",
            "LUCRO_CESANTE_CONSOLIDADO",
            "DANOS_MORALES",
            # FRUTO_CIVIL (Sprint 100): un evento por mes del periodo de
            # privacion con el fruto neto de ese mes (puede ser negativo si los
            # gastos de conservacion superan el canon). CivilFamiliaStrategy le
            # asigna tasa 0 -- no genera interes (decision no confirmada por el
            # despacho, ver _eventos_fruto_civil).
            "FRUTO_CIVIL",
            "CAPITAL_PAGARE",
            "CAPITAL_LETRA_CAMBIO",
            "CAPITAL_CHEQUE",
            "CAPITAL_FACTURA",
            "MULTA_SANCIONATORIA",
            "HONORARIOS_PROFESIONALES",
            # COSTAS_PROCESALES ya NO es capital (Sprint 79): va a su propio
            # componente PendingDebt.costas, que nunca genera interes -- ver
            # la rama dedicada en _process_event.
            "VACACIONES",
            "IMPUESTO_A_CARGO",
            # SALARIO_DEJADO_DE_PERCIBIR (Sprint 93): el salario mismo (no solo
            # las 4 prestaciones de arriba) de un bloque anual de la
            # reconstruccion de salarios/prestaciones dejados de percibir --
            # ver app/services/salarios_dejados_de_percibir.py y
            # LaboralStrategy._liquidar_salarios_dejados_de_percibir.
            "SALARIO_DEJADO_DE_PERCIBIR",
            # Preparacion para el wiring de seguridad social/incapacidades en LaboralStrategy
            # (Tasks 8/9 del Sprint 16) -- todavia sin productor propio en este task.
            # SUSPENSION_INFORMATIVA/INCAPACIDAD_INFORMATIVA siempre llevan amount=0.00,
            # mismo mecanismo que LIQUIDATION_CUTOFF (entradas de rastro/auditoria, no de capital).
            "COTIZACION_PENSION",
            "COTIZACION_SALUD",
            "COTIZACION_ARL",
            "COTIZACION_FSP",
            "INCAPACIDAD_EMPLEADOR",
            "SUSPENSION_INFORMATIVA",
            "INCAPACIDAD_INFORMATIVA",
        }

    def process(self, chronological_events: list[Event], cutoff_date: date) -> LiquidationResult:
        sorted_events = sorted(chronological_events, key=lambda e: e.date)

        for event in sorted_events:
            if event.date > cutoff_date:
                break

            interes_antes = self._current_debt.interest
            indexacion_antes = self._current_debt.indexation
            self._accrue_time_passage(event.date)
            interes_causado_periodo = self._current_debt.interest - interes_antes
            # Solo distinto de cero con causacion tramo a tramo (Sprint 104): en el
            # modo de siempre la indexacion entra unicamente por eventos INDEXATION.
            indexacion_causada_periodo = self._current_debt.indexation - indexacion_antes
            item = self._process_event(
                event, interes_causado_periodo, indexacion_causada_periodo
            )
            self._history.append(item)
            self._last_event_date = event.date

        interes_antes_cierre = self._current_debt.interest
        indexacion_antes_cierre = self._current_debt.indexation
        self._accrue_time_passage(cutoff_date)
        interes_causado_cierre = self._current_debt.interest - interes_antes_cierre
        indexacion_causada_cierre = self._current_debt.indexation - indexacion_antes_cierre

        if self._last_event_date and self._last_event_date < cutoff_date:
            closing_rb = RunningBalance(
                date=cutoff_date, debt=self._current_debt, event_type="LIQUIDATION_CUTOFF"
            )
            closing_item = LiquidationItem(
                date=cutoff_date,
                concept="Corte final de liquidación",
                capital_base=self._capital_base_actual(),
                interest_rate=self._get_rate_for_date(cutoff_date).percent(),
                interest_amount=interes_causado_cierre,
                indexation_amount=indexacion_causada_cierre,
                payment_amount=Decimal("0.00"),
                balance=closing_rb,
                rate_source=self._get_rate_source_for_date(cutoff_date),
            )
            self._history.append(closing_item)

        return LiquidationResult(self._history)

    def _capital_base_actual(self) -> Decimal:
        """Capital que efectivamente alimenta el interes diario en este instante --
        principal solo, o principal + indexacion bajo Suma Unica (nunca las costas
        procesales, que viven aparte en PendingDebt.costas -- Sprint 79). Se usa tanto para
        acumular interes (_accrue_time_passage) como para el LiquidationItem.capital_base
        que ve el juez al auditar la liquidacion (ver docstring de LiquidationItem): sin
        esto, el rubro auditado no coincidiria con la base que realmente generó el
        interes de esa fila bajo Suma Unica."""
        return self._current_debt.principal + (
            self._current_debt.indexation if self._usar_suma_unica else Decimal("0.00")
        )

    def _get_rate_for_date(self, target_date: date) -> Rate:
        if self._causacion_tramo_a_tramo is not None:
            # Tasa MENSUAL pura del tramo (no diaria): es la que realmente causo
            # el interes de la fila -- la fuente lo aclara.
            return Rate(self._causacion_tramo_a_tramo.tasa_interes_mensual)
        if self._rate_provider:
            return self._rate_provider.get_rate(target_date)
        return self._default_rate

    def _get_rate_source_for_date(self, target_date: date) -> str:
        if self._causacion_tramo_a_tramo is not None:
            return self._causacion_tramo_a_tramo.fuente
        if self._rate_provider:
            return self._rate_provider.get_rate_source(target_date)
        return "N/A"

    def _accrue_time_passage(self, target_date: date):
        if not self._last_event_date or target_date <= self._last_event_date:
            return

        capital_base = self._capital_base_actual()
        if capital_base <= Decimal("0.00"):
            return

        if self._causacion_tramo_a_tramo is not None:
            indexacion, interes = self._causacion_tramo_a_tramo.causar(
                capital_base, self._last_event_date, target_date
            )
            if indexacion > Decimal("0.00"):
                self._current_debt = BalanceEngine.add_indexation(self._current_debt, indexacion)
            if interes > Decimal("0.00"):
                self._current_debt = BalanceEngine.add_interest(self._current_debt, interes)
            return

        current_day = self._last_event_date + timedelta(days=1)
        total_interest_accumulated = Decimal("0.00")

        if self._politica_causacion is PoliticaCausacion.EXACTA_POR_PERIODO:
            # Un solo redondeo por tramo, con la tasa de precision completa (ver
            # PoliticaCausacion). El contexto forense hace el resultado independiente
            # del hilo y de la precision global del proceso.
            with localcontext(CONTEXTO_FORENSE):
                acumulado = Decimal("0")
                while current_day <= target_date:
                    acumulado += capital_base * self._get_rate_for_date(current_day).value
                    current_day += timedelta(days=1)
                total_interest_accumulated = Rounding.money(acumulado)
        else:
            while current_day <= target_date:
                daily_rate = self._get_rate_for_date(current_day)
                daily_interest = DailyInterest.calculate(
                    capital=capital_base, daily_rate=daily_rate, days=1
                )
                total_interest_accumulated += daily_interest
                current_day += timedelta(days=1)

        if total_interest_accumulated > Decimal("0.00"):
            self._current_debt = BalanceEngine.add_interest(
                self._current_debt, total_interest_accumulated
            )

    def _process_event(
        self,
        event: Event,
        interes_causado_periodo: Decimal = Decimal("0.00"),
        indexacion_causada_periodo: Decimal = Decimal("0.00"),
    ) -> LiquidationItem:
        concept = event.payload.get("label", event.event_type)
        payment_amount = Decimal("0.00")
        # Interés causado por el paso del tiempo (_accrue_time_passage) inmediatamente
        # antes de este evento -- ver Sprint 40. Se acumula aparte del interés inyectado
        # explícitamente por el (raro) evento tipo INTEREST, ambos son aditivos.
        interest_amount = interes_causado_periodo
        indexation_amount = indexacion_causada_periodo
        saldo_a_favor = Decimal("0.00")

        # Enrutador de impacto patrimonial
        if event.event_type in self._capital_concepts:
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            self._current_debt = BalanceEngine.add_principal(self._current_debt, amount)

        elif event.event_type == "COSTAS_PROCESALES":
            # Sprint 79 -- respuesta del despacho (16/11/2026): "las costas procesales
            # NO generan intereses ... la regla es general: aplica en cualquier area del
            # derecho y algoritmo" (con o sin Suma Unica). Se acumulan en un componente
            # aparte que _capital_base_actual() nunca suma, y entran "en seco" al total.
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            self._current_debt = BalanceEngine.add_costas(self._current_debt, amount)

        elif event.event_type == "INTEREST":
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            interest_amount += amount
            self._current_debt = BalanceEngine.add_interest(self._current_debt, amount)

        elif event.event_type in ("INDEXATION", "SANCION_TRIBUTARIA"):
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            indexation_amount += amount
            self._current_debt = BalanceEngine.add_indexation(self._current_debt, amount)

        elif event.event_type == "PAYMENT":
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            allocation, new_debt, remainder = self._estrategia_imputacion(
                amount, self._current_debt, event.date
            )
            self._current_debt = new_debt
            payment_amount = allocation.total_payment
            saldo_a_favor = remainder

        elif event.event_type == "CAPITALIZACION_INTERESES_ANATOCISMO":
            self._current_debt = BalanceEngine.capitalize_interest(self._current_debt)

        else:
            raise ValueError(
                f"Tipo de evento no reconocido: '{event.event_type}'. "
                "Debe ser uno de los conceptos de capital registrados en "
                "_capital_concepts, o bien 'COSTAS_PROCESALES', 'INTEREST', "
                "'INDEXATION' o 'PAYMENT'."
            )

        rb = RunningBalance(date=event.date, debt=self._current_debt, event_type=event.event_type)

        return LiquidationItem(
            date=event.date,
            concept=concept,
            capital_base=self._capital_base_actual(),
            interest_rate=self._get_rate_for_date(event.date).percent(),
            interest_amount=interest_amount,
            indexation_amount=indexation_amount,
            payment_amount=payment_amount,
            balance=rb,
            rate_source=self._get_rate_source_for_date(event.date),
            saldo_a_favor=saldo_a_favor,
        )
