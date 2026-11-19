from datetime import date
from decimal import Decimal

from app.engine.math.rounding import Rounding
from app.engine.temporal.schedulers.base import Event, Scheduler


class LaborScheduler(Scheduler):
    """
    Generador de las prestaciones sociales estatutarias de un contrato laboral
    colombiano, en el modelo de liquidacion final (finiquito): las cinco
    prestaciones (Cesantias, Intereses/Cesantias, Prima Junio, Prima
    Diciembre, Vacaciones) se vuelven exigibles TODAS en la fecha de
    terminacion del contrato (Art. 65 CST), no en las fechas de calendario
    que aplicarian a un contrato vigente (14-feb, 31-ene, 30-jun, 20-dic).

    `auxilio_transporte` (Sprint 96, seguimiento; opcional, 0 por defecto):
    auxilio de transporte mensual que se SUMA a `salario_base` solo en la
    base de cesantias (y por lo tanto de sus intereses) y de la prima de
    servicios -- respuesta del despacho (23/08/2026): "este auxilio forma
    parte obligatoria de la base de liquidacion para cesantias y prima de
    servicios". Vacaciones siguen liquidandose sobre el salario solo (la
    respuesta no las menciona). Con auxilio 0 los eventos son identicos a
    los de antes de este cambio (sin etiqueta extra).
    """

    def __init__(
        self,
        salario_base: Decimal,
        dias_trabajados: int,
        fecha_liquidacion: date,
        auxilio_transporte: Decimal = Decimal("0.00"),
    ):
        self.salario = salario_base
        self.auxilio_transporte = Decimal(str(auxilio_transporte))
        if self.auxilio_transporte < 0:
            raise ValueError("El auxilio de transporte no puede ser negativo.")
        self.dias = Decimal(str(dias_trabajados))
        self.fecha_liquidacion = fecha_liquidacion
        self.base_anual = Decimal("360")

    def _payload(self, monto: Decimal, concepto: str) -> dict:
        """Payload de cesantias/prima: con auxilio de transporte agrega una
        etiqueta que deja visible en la liquidacion que la base lo incluye
        (rastro de auditoria); sin auxilio, solo el monto (igual que antes)."""
        if self.auxilio_transporte <= Decimal("0.00"):
            return {"amount": monto}
        return {
            "amount": monto,
            "label": (
                f"{concepto} (base: salario ${self.salario:,.2f} + auxilio de "
                f"transporte ${self.auxilio_transporte:,.2f})"
            ),
        }

    def generate(self, start: date = None, end: date = None) -> list[Event]:
        events = []
        base_cesantias_prima = self.salario + self.auxilio_transporte

        # 1. Cesantias: 30 dias de salario por año laborado o proporcional.
        monto_cesantias = Rounding.money((base_cesantias_prima * self.dias) / self.base_anual)
        events.append(
            Event(
                date=self.fecha_liquidacion,
                payload=self._payload(monto_cesantias, "Cesantias"),
                event_type="CESANTIAS",
            )
        )

        # 2. Intereses a las cesantias: 12% anual sobre el saldo de cesantias,
        # prorrateado por los dias trabajados (formula verificada contra
        # REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf, pag. 51:
        # (Cesantias x 0.12 x dias) / 360 -- no habia bug aqui, docs/Pendientes.md
        # sospechaba uno pero la propia cita del PDF ya coincidia con esto).
        monto_intereses = Rounding.money(
            (monto_cesantias * self.dias * Decimal("0.12")) / self.base_anual
        )
        events.append(
            Event(
                date=self.fecha_liquidacion,
                payload=self._payload(monto_intereses, "Intereses a las cesantias"),
                event_type="INTERESES_CESANTIAS",
            )
        )

        # 3. Prima de servicios: 15 dias por semestre (junio y diciembre).
        dias_semestre = self.dias / Decimal("2")
        monto_prima_semestral = Rounding.money(
            (base_cesantias_prima * dias_semestre) / self.base_anual
        )

        if self.dias > Decimal("0.00"):
            events.append(
                Event(
                    date=self.fecha_liquidacion,
                    payload=self._payload(monto_prima_semestral, "Prima de servicios (junio)"),
                    event_type="PRIMA_JUNIO",
                )
            )
            events.append(
                Event(
                    date=self.fecha_liquidacion,
                    payload=self._payload(
                        monto_prima_semestral, "Prima de servicios (diciembre)"
                    ),
                    event_type="PRIMA_DICIEMBRE",
                )
            )

        # 4. Vacaciones: descanso remunerado, NO es tecnicamente una
        # prestacion social, por eso su divisor es 720 (el doble del año
        # comercial de 360).
        monto_vacaciones = Rounding.money((self.salario * self.dias) / Decimal("720"))
        events.append(
            Event(
                date=self.fecha_liquidacion,
                payload={"amount": monto_vacaciones},
                event_type="VACACIONES",
            )
        )

        return sorted(events, key=lambda e: e.date)
