"""Politica de causacion de interes de `LiquidationCore`."""

from enum import Enum


class PoliticaCausacion(Enum):
    """Como se acumula y redondea el interes entre dos eventos.

    LEGADA_DIARIA_REDONDEADA (default; comportamiento historico, bit a bit):
        cada dia se calcula `capital * tasa_diaria` con la tasa cuantizada a 12 decimales
        (`Rate.decimal()`) y el resultado de CADA DIA se redondea a centavos antes de
        sumarse. Medido en la auditoria 2026-11-12 (capital COP 10.000.000, 6 % anual
        lineal, 366 dias): el motor daba 601.645,44 frente a 601.643,84 de la formula
        `capital x 6 % x 366/365` (+1,60); con COP 1.000.000 daba -1,30. El sesgo es de
        pesos, pero hace que la liquidacion no sea reproducible a mano por el juez o la
        contraparte.

    EXACTA_POR_PERIODO:
        se suma `capital * tasa_diaria` SIN redondear (tasa de precision completa, contexto
        forense de 50 digitos) y se redondea UNA sola vez por tramo entre eventos, a
        centavos con ROUND_HALF_UP. Es lo que reproduce una hoja de calculo o un calculo
        manual de `capital x tasa x dias / base`.
    """

    LEGADA_DIARIA_REDONDEADA = "LEGADA_DIARIA_REDONDEADA"
    EXACTA_POR_PERIODO = "EXACTA_POR_PERIODO"
