from decimal import Decimal

from app.engine.financial.rate import Rate


class EffectiveRateConverter:
    """
    Convierte una tasa anual a una tasa de periodo equivalente que consume el
    motor. Desde el Sprint 76 hay DOS conversiones diarias conectadas al motor,
    y cada area elige explicitamente cual usa:

    1. Efectiva compuesta (`annual_to_daily`, "Opcion B"):
           i_diario = (1 + i_EA) ** (1/365) - 1
       Solo para tasas certificadas o pactadas como EFECTIVAS ANUALES:
       IBC/usura (Superfinanciera), tasas comerciales remuneratoria/moratoria
       (Art. 884 C.Co., topadas contra la usura EA), mora laboral con usura
       (Art. 65 CST), DTF (condena administrativa) y la tasa de Sancionatorio.
       (El E.T. 635 de Tributario tiene su propia conversion en
       `app/engine/tax/moratory_interest.py`.) Ninguna de estas cambia.

    2. Lineal simple (`annual_simple_to_daily`, "Opcion A"):
           i_diario = i_anual / 365
       Para el interes civil legal del 6 % (Art. 1617/2232 C.C.) y las tasas
       pactadas sin capitalizacion en obligaciones de dinero puro ("credito
       ordinario simple"). Mapeo por area (`app/services/area_strategy.py`):
         - Civil/Familia: tasa pactada de la obligacion y fallback
           CIVIL_ANNUAL_RATE.
         - Honorarios: tasa pactada y modo IPC + interes civil 6 %.
         - Comercial: SOLO el modo (b) de la regla XOR (IPC + interes civil
           puro 6 %); las tasas del Art. 884 siguen en la Opcion B.
       Fuente: respuesta del despacho del 16/11/2026 (Sprint 76,
       docs/Preguntas-Para-Abogado-Abiertas.md): "Obligacion Civil de Credito
       Ordinario (Simple): Debe usarse la Opcion A (Formula Lineal Simple:
       0.06 / 365). Usar formulas compuestas (Opcion C) en deuda civil pura
       viola la prohibicion de anatocismo de los Arts. 1617 y 2235 del C.C."
       La base es siempre 365 (tambien en anos bisiestos), literal de esa
       respuesta. La "tasa pura actuarial mensual" (0,0048676) que el despacho
       menciona para liquidacion de perjuicios NO se implementa aqui: ese
       dominio no existe todavia (ver Sprint 97 en docs/Pendientes.md). Desde
       el Sprint 104 si se usa en la liquidacion tramo a tramo de Suma Unica
       con abonos (`TASA_INTERES_MENSUAL_PURA`,
       app/engine/indexation/suma_unica_con_abonos.py), fuera de este conversor.

    Formula mensual (`annual_to_monthly`): i_mensual = (1 + i_EA) ** (1/12) - 1
    -- misma familia "efectiva compuesta" que la diaria, en base mensual. Es la
    convencion de las plantillas i1/i2/i7/i9/i13 del despacho (ej.
    i7.INTERESES-CIVILES-6-ANUAL.md: EA=6% -> tasa mensual "0,49%"), prorrateada
    linealmente sobre 30 dias fijos ("Opcion C", Sprint 83). NO esta conectada a
    ningun area: el despacho la descarto para deuda civil pura (16/11/2026).
    """

    @staticmethod
    def annual_to_daily(annual_percent: Decimal) -> Rate:
        """Opcion B, efectiva compuesta: `(1 + i_EA)^(1/365) - 1` (ver docstring
        de la clase para que tasas la usan)."""
        annual_fraction = Decimal(str(annual_percent)) / Decimal("100")
        daily_fraction = (Decimal("1") + annual_fraction) ** (
            Decimal("1") / Decimal("365")
        ) - Decimal("1")
        return Rate(daily_fraction)

    @staticmethod
    def annual_simple_to_daily(annual_percent: Decimal) -> Rate:
        """Opcion A, lineal simple sin anatocismo: `tasa_anual / 365`.

        Devuelve la tasa a precision completa (sin cuantizar): con la politica
        EXACTA_POR_PERIODO el motor reproduce al centavo `C x i x dias / 365`;
        con la politica legada (la predeterminada) `Rate.decimal()` la cuantiza
        a 12 decimales y el interes de CADA dia se redondea a centavos, lo que
        puede dejar unos centavos de diferencia (ej. $10.000.000 al 6 % por 30
        dias: 49.315,20 legado vs. 49.315,07 exacto -- ver PoliticaCausacion).
        """
        annual_fraction = Decimal(str(annual_percent)) / Decimal("100")
        return Rate(annual_fraction / Decimal("365"))

    @staticmethod
    def annual_to_monthly(annual_percent: Decimal) -> Rate:
        annual_fraction = Decimal(str(annual_percent)) / Decimal("100")
        monthly_fraction = (Decimal("1") + annual_fraction) ** (
            Decimal("1") / Decimal("12")
        ) - Decimal("1")
        return Rate(monthly_fraction)
