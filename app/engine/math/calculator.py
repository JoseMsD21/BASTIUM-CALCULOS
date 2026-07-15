from decimal import Decimal


class Calculator:

    @staticmethod
    def add(a, b):

        return Decimal(str(a)) + Decimal(str(b))

    @staticmethod
    def subtract(a, b):

        return Decimal(str(a)) - Decimal(str(b))

    @staticmethod
    def multiply(a, b):

        return Decimal(str(a)) * Decimal(str(b))

    @staticmethod
    def divide(a, b):

        return Decimal(str(a)) / Decimal(str(b))