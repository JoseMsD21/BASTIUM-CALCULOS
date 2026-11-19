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
    # Sprint 79: parte del pago imputada a costas procesales (siempre primero,
    # ver AllocationEngine). Default 0.00 para no romper constructores previos.
    to_costas: Decimal = Decimal("0.00")

@dataclass(frozen=True)
class PendingDebt:
    """
    Representa el estado actual de la deuda en un instante T.
    No es un movimiento, es una fotografía del saldo insoluto.

    `costas` (Sprint 79): costas procesales aprobadas (expensas + agencias en
    derecho), separadas de `principal` porque NUNCA generan interes -- respuesta
    del despacho (16/11/2026): "las costas procesales NO generan intereses ... la
    regla es general: aplica en cualquier area del derecho y algoritmo. Las costas
    se suman 'en seco' al final: Gran_Total = Capital_Indexado + Intereses_Mora +
    Costas_Aprobadas". Por eso entran en `total()` pero nunca en la base de interes
    (`LiquidationCore._capital_base_actual`). Default 0.00: los constructores
    posicionales de 3 componentes previos a este sprint siguen siendo validos.
    """
    principal: Decimal
    interest: Decimal
    indexation: Decimal
    costas: Decimal = Decimal("0.00")

    def total(self) -> Decimal:
        """Retorna la suma total adeudada en este instante (costas en seco incluidas)."""
        return self.principal + self.interest + self.indexation + self.costas

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
    saldo_a_favor: Decimal = Decimal("0.00")
    # Sprint 42: True cuando la obligacion de origen de esta fila ya vencio su
    # plazo de prescripcion/caducidad a la fecha de corte (ver
    # app/engine/temporal/prescripcion.py y app/services/motor_universal.py,
    # que es quien puebla este campo). Puramente informativo -- decision del
    # despacho, ver docs/superpowers/plans/2026-08-07-sprint42-prescripcion-caducidad-wiring.md:
    # NO excluye la fila del calculo ni cambia ningun total, solo la marca
    # para que el abogado decida que hacer con esa informacion.
    prescrita: bool = False