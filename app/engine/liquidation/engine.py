from datetime import date, timedelta
from decimal import Decimal

from app.engine.financial.rate import Rate
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.provider import RateProvider
from app.engine.liquidation.allocation import AllocationEngine
from app.engine.liquidation.balance import BalanceEngine
from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.engine.temporal.schedulers.base import Event


class LiquidationCore:
    """
    Orquestador determinista de liquidaciones.
    Procesa eventos temporales secuenciales de cualquier dominio jurídico
    (Familia, Laboral, Civil, Comercial) e inyecta automáticamente
    causaciones de interés por el paso del tiempo.
    """

    def __init__(
        self,
        default_daily_rate: Rate = Rate(Decimal("0.0")),
        rate_provider: RateProvider | None = None,
        usar_suma_unica: bool = False,
    ):
        self._current_debt = PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
        self._history: list[LiquidationItem] = []
        self._default_rate = default_daily_rate
        self._rate_provider = rate_provider
        self._usar_suma_unica = usar_suma_unica
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
            "DANO_EMERGENTE",
            "LUCRO_CESANTE_CONSOLIDADO",
            "DANOS_MORALES",
            "CAPITAL_PAGARE",
            "CAPITAL_LETRA_CAMBIO",
            "CAPITAL_CHEQUE",
            "CAPITAL_FACTURA",
            "MULTA_SANCIONATORIA",
            "HONORARIOS_PROFESIONALES",
            "COSTAS_PROCESALES",
            "VACACIONES",
            "IMPUESTO_A_CARGO",
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
            self._accrue_time_passage(event.date)
            interes_causado_periodo = self._current_debt.interest - interes_antes
            item = self._process_event(event, interes_causado_periodo)
            self._history.append(item)
            self._last_event_date = event.date

        interes_antes_cierre = self._current_debt.interest
        self._accrue_time_passage(cutoff_date)
        interes_causado_cierre = self._current_debt.interest - interes_antes_cierre

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
                indexation_amount=Decimal("0.00"),
                payment_amount=Decimal("0.00"),
                balance=closing_rb,
                rate_source=self._get_rate_source_for_date(cutoff_date),
            )
            self._history.append(closing_item)

        return LiquidationResult(self._history)

    def _capital_base_actual(self) -> Decimal:
        """Capital que efectivamente alimenta el interes diario en este instante --
        principal solo, o principal + indexacion bajo Suma Unica. Se usa tanto para
        acumular interes (_accrue_time_passage) como para el LiquidationItem.capital_base
        que ve el juez al auditar la liquidacion (ver docstring de LiquidationItem): sin
        esto, el rubro auditado no coincidiria con la base que realmente generó el
        interes de esa fila bajo Suma Unica."""
        return self._current_debt.principal + (
            self._current_debt.indexation if self._usar_suma_unica else Decimal("0.00")
        )

    def _get_rate_for_date(self, target_date: date) -> Rate:
        if self._rate_provider:
            return self._rate_provider.get_rate(target_date)
        return self._default_rate

    def _get_rate_source_for_date(self, target_date: date) -> str:
        if self._rate_provider:
            return self._rate_provider.get_rate_source(target_date)
        return "N/A"

    def _accrue_time_passage(self, target_date: date):
        if not self._last_event_date or target_date <= self._last_event_date:
            return

        capital_base = self._capital_base_actual()
        if capital_base <= Decimal("0.00"):
            return

        current_day = self._last_event_date + timedelta(days=1)
        total_interest_accumulated = Decimal("0.00")

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
        self, event: Event, interes_causado_periodo: Decimal = Decimal("0.00")
    ) -> LiquidationItem:
        concept = event.payload.get("label", event.event_type)
        payment_amount = Decimal("0.00")
        # Interés causado por el paso del tiempo (_accrue_time_passage) inmediatamente
        # antes de este evento -- ver Sprint 40. Se acumula aparte del interés inyectado
        # explícitamente por el (raro) evento tipo INTEREST, ambos son aditivos.
        interest_amount = interes_causado_periodo
        indexation_amount = Decimal("0.00")
        saldo_a_favor = Decimal("0.00")

        # Enrutador de impacto patrimonial
        if event.event_type in self._capital_concepts:
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            self._current_debt = BalanceEngine.add_principal(self._current_debt, amount)

        elif event.event_type == "INTEREST":
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            interest_amount += amount
            self._current_debt = BalanceEngine.add_interest(self._current_debt, amount)

        elif event.event_type in ("INDEXATION", "SANCION_TRIBUTARIA"):
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            indexation_amount = amount
            self._current_debt = BalanceEngine.add_indexation(self._current_debt, amount)

        elif event.event_type == "PAYMENT":
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            allocation, new_debt, remainder = AllocationEngine.allocate(
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
                "_capital_concepts, o bien 'INTEREST', 'INDEXATION' o 'PAYMENT'."
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
