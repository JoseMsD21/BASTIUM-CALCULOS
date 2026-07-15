from enum import Enum


class ObligationStatus(Enum):

    PENDING = "pending"

    PARTIAL = "partial"

    PAID = "paid"

    OVERDUE = "overdue"