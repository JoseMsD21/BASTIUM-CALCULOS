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
    """

    def __init__(self, salario_base: Decimal, dias_trabajados: int, fecha_liquidacion: date):
        self.salario = salario_base
        self.dias = Decimal(str(dias_trabajados))
        self.fecha_liquidacion = fecha_liquidacion
        self.base_anual = Decimal("360")

    def generate(self, start: date = None, end: date = None) -> list[Event]:
        events = []

        # 1. Cesantias: 30 dias de salario por año laborado o proporcional.
        monto_cesantias = Rounding.money((self.salario * self.dias) / self.base_anual)
        events.append(
            Event(
                date=self.fecha_liquidacion,
                payload={"amount": monto_cesantias},
                event_type="CESANTIAS",
            )
        )

        # 2. Intereses a las cesantias: 12% anual sobre el saldo de cesantias,
        # prorrateado por los dias trabajados (formula verificada contra
        # REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf, pag. 51:
        # (Cesantias x 0.12 x dias) / 360 -- no habia bug aqui, Pendientes.md
        # sospechaba uno pero la propia cita del PDF ya coincidia con esto).
        monto_intereses = Rounding.money(
            (monto_cesantias * self.dias * Decimal("0.12")) / self.base_anual
        )
        events.append(
            Event(
                date=self.fecha_liquidacion,
                payload={"amount": monto_intereses},
                event_type="INTERESES_CESANTIAS",
            )
        )

        # 3. Prima de servicios: 15 dias por semestre (junio y diciembre).
        dias_semestre = self.dias / Decimal("2")
        monto_prima_semestral = Rounding.money((self.salario * dias_semestre) / self.base_anual)

        if self.dias > Decimal("0.00"):
            events.append(
                Event(
                    date=self.fecha_liquidacion,
                    payload={"amount": monto_prima_semestral},
                    event_type="PRIMA_JUNIO",
                )
            )
            events.append(
                Event(
                    date=self.fecha_liquidacion,
                    payload={"amount": monto_prima_semestral},
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
