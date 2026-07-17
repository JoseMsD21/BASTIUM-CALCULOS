from dataclasses import dataclass
from datetime import date
from decimal import Decimal

@dataclass(frozen=True)
class Installment:
    """
    Representa una obligación histórica individual.
    Ejemplo: Cuota de marzo, o el capital de un pagaré.
    """
    due_date: date
    principal: Decimal
    concept: str
    remaining: Decimal
    state: str = "PENDING"

@dataclass(frozen=True)
class PaymentAllocation:
    """
    Representa la decisión matemática y jurídica de cómo se aplicó un pago.
    Garantiza la trazabilidad exacta de cada peso.
    """
    payment_date: date
    total_payment: Decimal
    to_interest: Decimal
    to_indexation: Decimal
    to_principal: Decimal

@dataclass(frozen=True)
class PendingDebt:
    """
    Representa el estado actual de la deuda en un instante T.
    No es un movimiento, es una fotografía del saldo insoluto.
    """
    principal: Decimal
    interest: Decimal
    indexation: Decimal

    def total(self) -> Decimal:
        """Retorna la suma total adeudada en este instante."""
        return self.principal + self.interest + self.indexation

@dataclass(frozen=True)
class RunningBalance:
    """
    Representa el saldo histórico tras procesar un evento.
    Cada evento (cuota, pago, causación) produce un nuevo RunningBalance.
    """
    date: date
    debt: PendingDebt
    event_type: str

@dataclass(frozen=True)
class LiquidationItem:
    """
    Es la fila histórica definitiva. La salida (Output) que el motor 
    entregará al Result y posteriormente a la interfaz/PDF para que
    el juez pueda auditar la trazabilidad.
    """
    date: date
    concept: str
    capital_base: Decimal
    interest_rate: Decimal
    interest_amount: Decimal
    indexation_amount: Decimal
    payment_amount: Decimal
    balance: RunningBalance
    rate_source: str = "N/A"