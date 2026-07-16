"""
Series historicas de indicadores economicos colombianos, transcritas y verificadas
contra REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf (paginas 55-62).

Ver docs/superpowers/specs/2026-07-15-carga-datos-historicos-design.md para el
detalle de como se extrajo y verifico cada serie (en particular, por que la tabla
de IBC/Usura requirio extraccion de tabla con reconocimiento de grilla en vez de
lectura de texto lineal).

Este modulo NO esta conectado a ningun motor de liquidacion todavia. Esa conexion
es responsabilidad de otros sprints (IPC: Sprint 8; IBC automatico en Comercial:
sprint futuro no asignado).
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# SMLMV (Salario Minimo Legal Mensual Vigente), 1984-2026.
# Transcrito de la pagina 55-57 del PDF. 2027 no esta incluido: el PDF lo lista
# como "Por definir" (el Gobierno aun no lo habia fijado a la fecha del documento).
# ---------------------------------------------------------------------------

_SMLMV_POR_ANIO: Dict[int, Decimal] = {
    1984: Decimal("11298.00"),
    1985: Decimal("13558.00"),
    1986: Decimal("16811.00"),
    1987: Decimal("20510.00"),
    1988: Decimal("25637.00"),
    1989: Decimal("32560.00"),
    1990: Decimal("41025.00"),
    1991: Decimal("51716.00"),
    1992: Decimal("65190.00"),
    1993: Decimal("81510.00"),
    1994: Decimal("98700.00"),
    1995: Decimal("118934.00"),
    1996: Decimal("142125.00"),
    1997: Decimal("172005.00"),
    1998: Decimal("203826.00"),
    1999: Decimal("236460.00"),
    2000: Decimal("260100.00"),
    2001: Decimal("286000.00"),
    2002: Decimal("309000.00"),
    2003: Decimal("332000.00"),
    2004: Decimal("358000.00"),
    2005: Decimal("381500.00"),
    2006: Decimal("408000.00"),
    2007: Decimal("433700.00"),
    2008: Decimal("461500.00"),
    2009: Decimal("496900.00"),
    2010: Decimal("515000.00"),
    2011: Decimal("535600.00"),
    2012: Decimal("566700.00"),
    2013: Decimal("589500.00"),
    2014: Decimal("616000.00"),
    2015: Decimal("644350.00"),
    2016: Decimal("689455.00"),
    2017: Decimal("737717.00"),
    2018: Decimal("781242.00"),
    2019: Decimal("828116.00"),
    2020: Decimal("877803.00"),
    2021: Decimal("908526.00"),
    2022: Decimal("1000000.00"),
    2023: Decimal("1160000.00"),
    2024: Decimal("1300000.00"),
    2025: Decimal("1423500.00"),
    2026: Decimal("1750905.00"),
}


def get_smlmv_for_year(anio: int) -> Decimal:
    """Retorna el Salario Minimo Legal Mensual Vigente para el año dado.
    Datos disponibles: 1984-2026 (2027 aun no definido por el Gobierno a la fecha
    del documento fuente)."""
    if anio not in _SMLMV_POR_ANIO:
        raise ValueError(
            f"No hay SMLMV configurado para el año {anio}. "
            f"Datos disponibles: {min(_SMLMV_POR_ANIO)}-{max(_SMLMV_POR_ANIO)}."
        )
    return _SMLMV_POR_ANIO[anio]


# ---------------------------------------------------------------------------
# IPC (Indice de Precios al Consumidor), 1967-2025.
# Transcrito de la pagina 62 del PDF. La fuente trae variacion porcentual ANUAL,
# no un indice acumulado -- IPCIndexation.calculate() (app/engine/indexation/ipc.py)
# espera un indice, asi que se deriva uno encadenando las variaciones anuales.
# ---------------------------------------------------------------------------

_IPC_VARIACION_ANUAL: Dict[int, Decimal] = {
    1967: Decimal("7.90"),
    1968: Decimal("6.46"),
    1969: Decimal("8.90"),
    1970: Decimal("7.06"),
    1971: Decimal("12.84"),
    1972: Decimal("13.53"),
    1973: Decimal("22.49"),
    1974: Decimal("25.00"),
    1975: Decimal("17.52"),
    1976: Decimal("25.60"),
    1977: Decimal("27.45"),
    1978: Decimal("19.75"),
    1979: Decimal("28.81"),
    1980: Decimal("25.96"),
    1981: Decimal("26.36"),
    1982: Decimal("24.03"),
    1983: Decimal("16.62"),
    1984: Decimal("18.28"),
    1985: Decimal("22.45"),
    1986: Decimal("20.95"),
    1987: Decimal("24.02"),
    1988: Decimal("28.12"),
    1989: Decimal("26.12"),
    1990: Decimal("32.36"),
    1991: Decimal("26.82"),
    1992: Decimal("25.13"),
    1993: Decimal("22.60"),
    1994: Decimal("22.59"),
    1995: Decimal("19.46"),
    1996: Decimal("21.63"),
    1997: Decimal("17.68"),
    1998: Decimal("16.70"),
    1999: Decimal("9.23"),
    2000: Decimal("8.75"),
    2001: Decimal("7.65"),
    2002: Decimal("6.99"),
    2003: Decimal("6.49"),
    2004: Decimal("5.50"),
    2005: Decimal("4.85"),
    2006: Decimal("4.48"),
    2007: Decimal("5.69"),
    2008: Decimal("7.67"),
    2009: Decimal("2.00"),
    2010: Decimal("3.17"),
    2011: Decimal("3.73"),
    2012: Decimal("2.44"),
    2013: Decimal("1.94"),
    2014: Decimal("3.66"),
    2015: Decimal("6.77"),
    2016: Decimal("5.75"),
    2017: Decimal("4.09"),
    2018: Decimal("3.18"),
    2019: Decimal("3.80"),
    2020: Decimal("1.61"),
    2021: Decimal("5.62"),
    2022: Decimal("13.12"),
    2023: Decimal("9.28"),
    2024: Decimal("5.20"),
    2025: Decimal("5.10"),
}


def _construir_indice_ipc_acumulado(variacion_anual: Dict[int, Decimal]) -> Dict[int, Decimal]:
    """Encadena la variacion porcentual anual en un indice acumulado de cierre de año
    (31-dic). Base 100 anclada antes del primer año de datos (indice implicito de
    1966 = 100). La eleccion de base no afecta IPCIndexation.calculate(), que solo
    usa la razon final/inicial entre dos años -- cualquier base consistente da el
    mismo resultado. No se redondean los indices intermedios: el redondeo a
    centavos ya ocurre en Rounding.money() dentro de IPCIndexation.calculate(), no
    aqui."""
    indice = Decimal("100")
    acumulado: Dict[int, Decimal] = {}
    for anio in sorted(variacion_anual):
        indice = indice * (Decimal("1") + variacion_anual[anio] / Decimal("100"))
        acumulado[anio] = indice
    return acumulado


_IPC_INDICE_ACUMULADO: Dict[int, Decimal] = _construir_indice_ipc_acumulado(_IPC_VARIACION_ANUAL)


def get_ipc_for_date(fecha: date) -> Decimal:
    """Retorna el indice IPC acumulado de cierre de año (31-dic) del año de `fecha`.
    Datos disponibles: 1967-2025. La fuente solo trae variacion ANUAL -- no hay
    granularidad mensual; interpolar a un mes especifico dentro del año es
    responsabilidad del Sprint 8 (indexacion IPC conectada a Civil/Familia)."""
    anio = fecha.year
    if anio not in _IPC_INDICE_ACUMULADO:
        raise ValueError(
            f"No hay indice IPC configurado para el año {anio}. "
            f"Datos disponibles: {min(_IPC_INDICE_ACUMULADO)}-{max(_IPC_INDICE_ACUMULADO)}."
        )
    return _IPC_INDICE_ACUMULADO[anio]


# ---------------------------------------------------------------------------
# IBC (Interes Bancario Corriente) y Tasa de Usura, 1997-07-01 a 2026-07-31.
# Transcrito de las paginas 58-61 del PDF, linea de credito "Comercial"
# (1997 - 4-ene-2007) que pasa a llamarse "Credito Comercial y de Consumo"
# (5-ene-2007 a 31-mar-2007) y luego "Credito de Consumo y Ordinario"
# (1-abr-2007 en adelante) -- es la linea general/por defecto que la SFC
# certifica hoy, la mas cercana a lo que aplicaria a una obligacion sin
# clasificacion especifica de microcredito o credito rural. Esas otras lineas
# (Microcredito, Credito Popular Productivo Rural) NO estan modeladas aqui --
# ver design spec, seccion "Fuera de alcance".
#
# Extraido con reconocimiento de grilla (no lectura de texto lineal, que
# mezcla las columnas de esta tabla especifica) y verificado: sin vacios en
# todo el rango, un solo solape real en la fuente (ver nota en septiembre de
# 2017 mas abajo), y usura_anual == 1.5 x ibc_anual en las 263 filas.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TramoIBCUsura:
    inicio: date
    fin: date
    ibc_anual: Decimal
    usura_anual: Decimal


_TRAMOS_IBC_USURA: List[TramoIBCUsura] = [
    TramoIBCUsura(date(1997, 7, 1), date(1997, 8, 31), Decimal("36.50"), Decimal("54.75")),
    TramoIBCUsura(date(1997, 9, 1), date(1997, 9, 30), Decimal("31.84"), Decimal("47.76")),
    TramoIBCUsura(date(1997, 10, 1), date(1997, 10, 31), Decimal("31.33"), Decimal("46.99")),
    TramoIBCUsura(date(1997, 11, 1), date(1997, 11, 30), Decimal("31.47"), Decimal("47.21")),
    TramoIBCUsura(date(1997, 12, 1), date(1997, 12, 31), Decimal("31.74"), Decimal("47.61")),
    TramoIBCUsura(date(1998, 1, 1), date(1998, 1, 31), Decimal("31.69"), Decimal("47.54")),
    TramoIBCUsura(date(1998, 2, 1), date(1998, 2, 28), Decimal("32.56"), Decimal("48.84")),
    TramoIBCUsura(date(1998, 3, 1), date(1998, 3, 31), Decimal("32.15"), Decimal("48.23")),
    TramoIBCUsura(date(1998, 4, 1), date(1998, 4, 30), Decimal("36.28"), Decimal("54.42")),
    TramoIBCUsura(date(1998, 5, 1), date(1998, 5, 31), Decimal("38.39"), Decimal("57.59")),
    TramoIBCUsura(date(1998, 6, 1), date(1998, 6, 30), Decimal("39.51"), Decimal("59.27")),
    TramoIBCUsura(date(1998, 7, 1), date(1998, 7, 31), Decimal("47.83"), Decimal("71.75")),
    TramoIBCUsura(date(1998, 8, 1), date(1998, 8, 31), Decimal("48.41"), Decimal("72.62")),
    TramoIBCUsura(date(1998, 9, 1), date(1998, 9, 30), Decimal("43.20"), Decimal("64.80")),
    TramoIBCUsura(date(1998, 10, 1), date(1998, 10, 31), Decimal("46.00"), Decimal("69.00")),
    TramoIBCUsura(date(1998, 11, 1), date(1998, 11, 30), Decimal("49.99"), Decimal("74.99")),
    TramoIBCUsura(date(1998, 12, 1), date(1998, 12, 31), Decimal("47.71"), Decimal("71.57")),
    TramoIBCUsura(date(1999, 1, 1), date(1999, 1, 31), Decimal("45.49"), Decimal("68.24")),
    TramoIBCUsura(date(1999, 2, 1), date(1999, 2, 28), Decimal("42.39"), Decimal("63.59")),
    TramoIBCUsura(date(1999, 3, 1), date(1999, 3, 14), Decimal("40.99"), Decimal("61.49")),
    TramoIBCUsura(date(1999, 3, 15), date(1999, 3, 31), Decimal("39.76"), Decimal("59.64")),
    TramoIBCUsura(date(1999, 4, 1), date(1999, 4, 30), Decimal("33.57"), Decimal("50.36")),
    TramoIBCUsura(date(1999, 5, 1), date(1999, 5, 31), Decimal("31.14"), Decimal("46.71")),
    TramoIBCUsura(date(1999, 6, 1), date(1999, 6, 30), Decimal("27.46"), Decimal("41.19")),
    TramoIBCUsura(date(1999, 7, 1), date(1999, 7, 31), Decimal("24.22"), Decimal("36.33")),
    TramoIBCUsura(date(1999, 8, 1), date(1999, 8, 31), Decimal("26.25"), Decimal("39.38")),
    TramoIBCUsura(date(1999, 9, 1), date(1999, 9, 30), Decimal("26.01"), Decimal("39.02")),
    TramoIBCUsura(date(1999, 10, 1), date(1999, 10, 31), Decimal("26.96"), Decimal("40.44")),
    TramoIBCUsura(date(1999, 11, 1), date(1999, 11, 30), Decimal("25.70"), Decimal("38.55")),
    TramoIBCUsura(date(1999, 12, 1), date(1999, 12, 31), Decimal("24.22"), Decimal("36.33")),
    TramoIBCUsura(date(2000, 1, 1), date(2000, 1, 31), Decimal("22.40"), Decimal("33.60")),
    TramoIBCUsura(date(2000, 2, 1), date(2000, 2, 29), Decimal("19.46"), Decimal("29.19")),
    TramoIBCUsura(date(2000, 3, 1), date(2000, 3, 31), Decimal("17.45"), Decimal("26.18")),
    TramoIBCUsura(date(2000, 4, 1), date(2000, 4, 30), Decimal("17.87"), Decimal("26.81")),
    TramoIBCUsura(date(2000, 5, 1), date(2000, 5, 31), Decimal("17.90"), Decimal("26.85")),
    TramoIBCUsura(date(2000, 6, 1), date(2000, 6, 30), Decimal("19.77"), Decimal("29.66")),
    TramoIBCUsura(date(2000, 7, 1), date(2000, 7, 31), Decimal("19.44"), Decimal("29.16")),
    TramoIBCUsura(date(2000, 8, 1), date(2000, 8, 31), Decimal("19.92"), Decimal("29.88")),
    TramoIBCUsura(date(2000, 9, 1), date(2000, 9, 30), Decimal("22.93"), Decimal("34.40")),
    TramoIBCUsura(date(2000, 10, 1), date(2000, 10, 31), Decimal("23.08"), Decimal("34.62")),
    TramoIBCUsura(date(2000, 11, 1), date(2000, 11, 30), Decimal("23.80"), Decimal("35.70")),
    TramoIBCUsura(date(2000, 12, 1), date(2000, 12, 31), Decimal("23.69"), Decimal("35.54")),
    TramoIBCUsura(date(2001, 1, 1), date(2001, 1, 31), Decimal("24.16"), Decimal("36.24")),
    TramoIBCUsura(date(2001, 2, 1), date(2001, 2, 28), Decimal("26.03"), Decimal("39.05")),
    TramoIBCUsura(date(2001, 3, 1), date(2001, 3, 31), Decimal("25.11"), Decimal("37.67")),
    TramoIBCUsura(date(2001, 4, 1), date(2001, 4, 30), Decimal("24.83"), Decimal("37.25")),
    TramoIBCUsura(date(2001, 5, 1), date(2001, 5, 31), Decimal("24.24"), Decimal("36.36")),
    TramoIBCUsura(date(2001, 6, 1), date(2001, 6, 30), Decimal("25.17"), Decimal("37.76")),
    TramoIBCUsura(date(2001, 7, 1), date(2001, 7, 31), Decimal("26.08"), Decimal("39.12")),
    TramoIBCUsura(date(2001, 8, 1), date(2001, 8, 31), Decimal("24.25"), Decimal("36.38")),
    TramoIBCUsura(date(2001, 9, 1), date(2001, 9, 30), Decimal("23.06"), Decimal("34.59")),
    TramoIBCUsura(date(2001, 10, 1), date(2001, 10, 31), Decimal("23.22"), Decimal("34.83")),
    TramoIBCUsura(date(2001, 11, 1), date(2001, 11, 30), Decimal("22.98"), Decimal("34.47")),
    TramoIBCUsura(date(2001, 12, 1), date(2001, 12, 31), Decimal("22.48"), Decimal("33.72")),
    TramoIBCUsura(date(2002, 1, 1), date(2002, 1, 31), Decimal("22.81"), Decimal("34.22")),
    TramoIBCUsura(date(2002, 2, 1), date(2002, 2, 28), Decimal("22.35"), Decimal("33.53")),
    TramoIBCUsura(date(2002, 3, 1), date(2002, 3, 31), Decimal("20.97"), Decimal("31.46")),
    TramoIBCUsura(date(2002, 4, 1), date(2002, 4, 30), Decimal("21.03"), Decimal("31.55")),
    TramoIBCUsura(date(2002, 5, 1), date(2002, 5, 31), Decimal("20.00"), Decimal("30.00")),
    TramoIBCUsura(date(2002, 6, 1), date(2002, 6, 30), Decimal("19.96"), Decimal("29.94")),
    TramoIBCUsura(date(2002, 7, 1), date(2002, 7, 31), Decimal("19.77"), Decimal("29.66")),
    TramoIBCUsura(date(2002, 8, 1), date(2002, 8, 31), Decimal("20.01"), Decimal("30.02")),
    TramoIBCUsura(date(2002, 9, 1), date(2002, 9, 30), Decimal("20.18"), Decimal("30.27")),
    TramoIBCUsura(date(2002, 10, 1), date(2002, 10, 31), Decimal("20.30"), Decimal("30.45")),
    TramoIBCUsura(date(2002, 11, 1), date(2002, 11, 30), Decimal("19.76"), Decimal("29.64")),
    TramoIBCUsura(date(2002, 12, 1), date(2002, 12, 31), Decimal("19.69"), Decimal("29.54")),
    TramoIBCUsura(date(2003, 1, 1), date(2003, 1, 31), Decimal("19.64"), Decimal("29.46")),
    TramoIBCUsura(date(2003, 2, 1), date(2003, 2, 28), Decimal("19.78"), Decimal("29.67")),
    TramoIBCUsura(date(2003, 3, 1), date(2003, 3, 31), Decimal("19.49"), Decimal("29.24")),
    TramoIBCUsura(date(2003, 4, 1), date(2003, 4, 30), Decimal("19.81"), Decimal("29.72")),
    TramoIBCUsura(date(2003, 5, 1), date(2003, 5, 31), Decimal("19.89"), Decimal("29.84")),
    TramoIBCUsura(date(2003, 6, 1), date(2003, 6, 30), Decimal("19.20"), Decimal("28.80")),
    TramoIBCUsura(date(2003, 7, 1), date(2003, 7, 31), Decimal("19.44"), Decimal("29.16")),
    TramoIBCUsura(date(2003, 8, 1), date(2003, 8, 31), Decimal("19.88"), Decimal("29.82")),
    TramoIBCUsura(date(2003, 9, 1), date(2003, 9, 30), Decimal("20.12"), Decimal("30.18")),
    TramoIBCUsura(date(2003, 10, 1), date(2003, 10, 31), Decimal("20.04"), Decimal("30.06")),
    TramoIBCUsura(date(2003, 11, 1), date(2003, 11, 30), Decimal("19.87"), Decimal("29.80")),
    TramoIBCUsura(date(2003, 12, 1), date(2003, 12, 31), Decimal("19.81"), Decimal("29.72")),
    TramoIBCUsura(date(2004, 1, 1), date(2004, 1, 31), Decimal("19.67"), Decimal("29.50")),
    TramoIBCUsura(date(2004, 2, 1), date(2004, 2, 29), Decimal("19.74"), Decimal("29.61")),
    TramoIBCUsura(date(2004, 3, 1), date(2004, 3, 31), Decimal("19.80"), Decimal("29.70")),
    TramoIBCUsura(date(2004, 4, 1), date(2004, 4, 30), Decimal("19.78"), Decimal("29.67")),
    TramoIBCUsura(date(2004, 5, 1), date(2004, 5, 31), Decimal("19.71"), Decimal("29.56")),
    TramoIBCUsura(date(2004, 6, 1), date(2004, 6, 30), Decimal("19.67"), Decimal("29.50")),
    TramoIBCUsura(date(2004, 7, 1), date(2004, 7, 31), Decimal("19.44"), Decimal("29.16")),
    TramoIBCUsura(date(2004, 8, 1), date(2004, 8, 31), Decimal("19.28"), Decimal("28.92")),
    TramoIBCUsura(date(2004, 9, 1), date(2004, 9, 30), Decimal("19.50"), Decimal("29.25")),
    TramoIBCUsura(date(2004, 10, 1), date(2004, 10, 31), Decimal("19.09"), Decimal("28.63")),
    TramoIBCUsura(date(2004, 11, 1), date(2004, 11, 30), Decimal("19.59"), Decimal("29.39")),
    TramoIBCUsura(date(2004, 12, 1), date(2004, 12, 31), Decimal("19.49"), Decimal("29.23")),
    TramoIBCUsura(date(2005, 1, 1), date(2005, 1, 31), Decimal("19.45"), Decimal("29.18")),
    TramoIBCUsura(date(2005, 2, 1), date(2005, 2, 28), Decimal("19.40"), Decimal("29.10")),
    TramoIBCUsura(date(2005, 3, 1), date(2005, 3, 31), Decimal("19.15"), Decimal("28.73")),
    TramoIBCUsura(date(2005, 4, 1), date(2005, 4, 30), Decimal("19.19"), Decimal("28.79")),
    TramoIBCUsura(date(2005, 5, 1), date(2005, 5, 31), Decimal("19.02"), Decimal("28.53")),
    TramoIBCUsura(date(2005, 6, 1), date(2005, 6, 30), Decimal("18.85"), Decimal("28.28")),
    TramoIBCUsura(date(2005, 7, 1), date(2005, 7, 31), Decimal("18.50"), Decimal("27.75")),
    TramoIBCUsura(date(2005, 8, 1), date(2005, 8, 31), Decimal("18.24"), Decimal("27.36")),
    TramoIBCUsura(date(2005, 9, 1), date(2005, 9, 30), Decimal("18.22"), Decimal("27.33")),
    TramoIBCUsura(date(2005, 10, 1), date(2005, 10, 31), Decimal("17.93"), Decimal("26.90")),
    TramoIBCUsura(date(2005, 11, 1), date(2005, 11, 30), Decimal("17.81"), Decimal("26.72")),
    TramoIBCUsura(date(2005, 12, 1), date(2005, 12, 31), Decimal("17.49"), Decimal("26.24")),
    TramoIBCUsura(date(2006, 1, 1), date(2006, 1, 31), Decimal("17.35"), Decimal("26.03")),
    TramoIBCUsura(date(2006, 2, 1), date(2006, 2, 28), Decimal("17.51"), Decimal("26.27")),
    TramoIBCUsura(date(2006, 3, 1), date(2006, 3, 31), Decimal("17.25"), Decimal("25.88")),
    TramoIBCUsura(date(2006, 4, 1), date(2006, 4, 30), Decimal("16.75"), Decimal("25.13")),
    TramoIBCUsura(date(2006, 5, 1), date(2006, 5, 31), Decimal("16.07"), Decimal("24.11")),
    TramoIBCUsura(date(2006, 6, 1), date(2006, 6, 30), Decimal("15.61"), Decimal("23.42")),
    TramoIBCUsura(date(2006, 7, 1), date(2006, 7, 31), Decimal("15.08"), Decimal("22.62")),
    TramoIBCUsura(date(2006, 8, 1), date(2006, 8, 31), Decimal("15.02"), Decimal("22.53")),
    TramoIBCUsura(date(2006, 9, 1), date(2006, 9, 30), Decimal("15.05"), Decimal("22.58")),
    TramoIBCUsura(date(2006, 10, 1), date(2006, 12, 31), Decimal("15.07"), Decimal("22.61")),
    TramoIBCUsura(date(2007, 1, 1), date(2007, 1, 4), Decimal("11.07"), Decimal("16.61")),
    TramoIBCUsura(date(2007, 1, 5), date(2007, 3, 31), Decimal("13.83"), Decimal("20.75")),
    TramoIBCUsura(date(2007, 4, 1), date(2007, 6, 30), Decimal("16.75"), Decimal("25.12")),
    TramoIBCUsura(date(2007, 7, 1), date(2007, 9, 30), Decimal("19.01"), Decimal("28.51")),
    TramoIBCUsura(date(2007, 10, 1), date(2007, 12, 31), Decimal("21.26"), Decimal("31.89")),
    TramoIBCUsura(date(2008, 1, 1), date(2008, 3, 31), Decimal("21.83"), Decimal("32.75")),
    TramoIBCUsura(date(2008, 4, 1), date(2008, 6, 30), Decimal("21.92"), Decimal("32.88")),
    TramoIBCUsura(date(2008, 7, 1), date(2008, 9, 30), Decimal("21.51"), Decimal("32.27")),
    TramoIBCUsura(date(2008, 10, 1), date(2008, 12, 31), Decimal("21.02"), Decimal("31.53")),
    TramoIBCUsura(date(2009, 1, 1), date(2009, 3, 31), Decimal("20.47"), Decimal("30.71")),
    TramoIBCUsura(date(2009, 4, 1), date(2009, 6, 30), Decimal("20.28"), Decimal("30.42")),
    TramoIBCUsura(date(2009, 7, 1), date(2009, 9, 30), Decimal("18.65"), Decimal("27.98")),
    TramoIBCUsura(date(2009, 10, 1), date(2009, 12, 31), Decimal("17.28"), Decimal("25.92")),
    TramoIBCUsura(date(2010, 1, 1), date(2010, 3, 31), Decimal("16.14"), Decimal("24.21")),
    TramoIBCUsura(date(2010, 4, 1), date(2010, 6, 30), Decimal("15.31"), Decimal("22.97")),
    TramoIBCUsura(date(2010, 7, 1), date(2010, 9, 30), Decimal("14.94"), Decimal("22.41")),
    TramoIBCUsura(date(2010, 10, 1), date(2010, 12, 31), Decimal("14.21"), Decimal("21.32")),
    TramoIBCUsura(date(2011, 1, 1), date(2011, 3, 31), Decimal("15.61"), Decimal("23.42")),
    TramoIBCUsura(date(2011, 4, 1), date(2011, 6, 30), Decimal("17.69"), Decimal("26.54")),
    TramoIBCUsura(date(2011, 7, 1), date(2011, 9, 30), Decimal("18.63"), Decimal("27.95")),
    TramoIBCUsura(date(2011, 10, 1), date(2011, 12, 31), Decimal("19.39"), Decimal("29.09")),
    TramoIBCUsura(date(2012, 1, 1), date(2012, 3, 31), Decimal("19.92"), Decimal("29.88")),
    TramoIBCUsura(date(2012, 4, 1), date(2012, 6, 30), Decimal("20.52"), Decimal("30.78")),
    TramoIBCUsura(date(2012, 7, 1), date(2012, 9, 30), Decimal("20.86"), Decimal("31.29")),
    TramoIBCUsura(date(2012, 10, 1), date(2012, 12, 31), Decimal("20.89"), Decimal("31.34")),
    TramoIBCUsura(date(2013, 1, 1), date(2013, 3, 31), Decimal("20.75"), Decimal("31.13")),
    TramoIBCUsura(date(2013, 4, 1), date(2013, 6, 30), Decimal("20.83"), Decimal("31.25")),
    TramoIBCUsura(date(2013, 7, 1), date(2013, 9, 30), Decimal("20.34"), Decimal("30.51")),
    TramoIBCUsura(date(2013, 10, 1), date(2013, 12, 31), Decimal("19.85"), Decimal("29.78")),
    TramoIBCUsura(date(2014, 1, 1), date(2014, 3, 31), Decimal("19.65"), Decimal("29.48")),
    TramoIBCUsura(date(2014, 4, 1), date(2014, 6, 30), Decimal("19.63"), Decimal("29.45")),
    TramoIBCUsura(date(2014, 7, 1), date(2014, 9, 30), Decimal("19.33"), Decimal("29.00")),
    TramoIBCUsura(date(2014, 10, 1), date(2014, 12, 31), Decimal("19.17"), Decimal("28.76")),
    TramoIBCUsura(date(2015, 1, 1), date(2015, 3, 31), Decimal("19.21"), Decimal("28.82")),
    TramoIBCUsura(date(2015, 4, 1), date(2015, 6, 30), Decimal("19.37"), Decimal("29.06")),
    TramoIBCUsura(date(2015, 7, 1), date(2015, 9, 30), Decimal("19.26"), Decimal("28.89")),
    TramoIBCUsura(date(2015, 10, 1), date(2015, 12, 31), Decimal("19.33"), Decimal("29.00")),
    TramoIBCUsura(date(2016, 1, 1), date(2016, 3, 31), Decimal("19.68"), Decimal("29.52")),
    TramoIBCUsura(date(2016, 4, 1), date(2016, 6, 30), Decimal("20.54"), Decimal("30.81")),
    TramoIBCUsura(date(2016, 7, 1), date(2016, 9, 30), Decimal("21.34"), Decimal("32.01")),
    TramoIBCUsura(date(2016, 10, 1), date(2016, 12, 31), Decimal("21.99"), Decimal("32.99")),
    TramoIBCUsura(date(2017, 1, 1), date(2017, 3, 31), Decimal("22.34"), Decimal("33.51")),
    TramoIBCUsura(date(2017, 4, 1), date(2017, 6, 30), Decimal("22.33"), Decimal("33.50")),
    TramoIBCUsura(date(2017, 7, 1), date(2017, 8, 31), Decimal("21.98"), Decimal("32.97")),
    TramoIBCUsura(date(2017, 9, 1), date(2017, 9, 30), Decimal("21.48"), Decimal("32.22")),
    TramoIBCUsura(date(2017, 10, 1), date(2017, 10, 31), Decimal("21.15"), Decimal("31.73")),
    TramoIBCUsura(date(2017, 11, 1), date(2017, 11, 30), Decimal("20.96"), Decimal("31.44")),
    TramoIBCUsura(date(2017, 12, 1), date(2017, 12, 31), Decimal("20.77"), Decimal("31.16")),
    TramoIBCUsura(date(2018, 1, 1), date(2018, 1, 31), Decimal("20.69"), Decimal("31.04")),
    TramoIBCUsura(date(2018, 2, 1), date(2018, 2, 28), Decimal("21.01"), Decimal("31.52")),
    TramoIBCUsura(date(2018, 3, 1), date(2018, 3, 31), Decimal("20.68"), Decimal("31.02")),
    TramoIBCUsura(date(2018, 4, 1), date(2018, 4, 30), Decimal("20.48"), Decimal("30.72")),
    TramoIBCUsura(date(2018, 5, 1), date(2018, 5, 31), Decimal("20.44"), Decimal("30.66")),
    TramoIBCUsura(date(2018, 6, 1), date(2018, 6, 30), Decimal("20.28"), Decimal("30.42")),
    TramoIBCUsura(date(2018, 7, 1), date(2018, 7, 31), Decimal("20.03"), Decimal("30.05")),
    TramoIBCUsura(date(2018, 8, 1), date(2018, 8, 31), Decimal("19.94"), Decimal("29.91")),
    TramoIBCUsura(date(2018, 9, 1), date(2018, 9, 30), Decimal("19.81"), Decimal("29.72")),
    TramoIBCUsura(date(2018, 10, 1), date(2018, 10, 31), Decimal("19.63"), Decimal("29.45")),
    TramoIBCUsura(date(2018, 11, 1), date(2018, 11, 30), Decimal("19.49"), Decimal("29.24")),
    TramoIBCUsura(date(2018, 12, 1), date(2018, 12, 31), Decimal("19.40"), Decimal("29.10")),
    TramoIBCUsura(date(2019, 1, 1), date(2019, 1, 31), Decimal("19.16"), Decimal("28.74")),
    TramoIBCUsura(date(2019, 2, 1), date(2019, 2, 28), Decimal("19.70"), Decimal("29.55")),
    TramoIBCUsura(date(2019, 3, 1), date(2019, 3, 31), Decimal("19.37"), Decimal("29.06")),
    TramoIBCUsura(date(2019, 4, 1), date(2019, 4, 30), Decimal("19.32"), Decimal("28.98")),
    TramoIBCUsura(date(2019, 5, 1), date(2019, 5, 31), Decimal("19.34"), Decimal("29.01")),
    TramoIBCUsura(date(2019, 6, 1), date(2019, 6, 30), Decimal("19.30"), Decimal("28.95")),
    TramoIBCUsura(date(2019, 7, 1), date(2019, 7, 31), Decimal("19.28"), Decimal("28.92")),
    TramoIBCUsura(date(2019, 8, 1), date(2019, 8, 31), Decimal("19.32"), Decimal("28.98")),
    TramoIBCUsura(date(2019, 9, 1), date(2019, 9, 30), Decimal("19.32"), Decimal("28.98")),
    TramoIBCUsura(date(2019, 10, 1), date(2019, 10, 31), Decimal("19.10"), Decimal("28.65")),
    TramoIBCUsura(date(2019, 11, 1), date(2019, 11, 30), Decimal("19.03"), Decimal("28.55")),
    TramoIBCUsura(date(2019, 12, 1), date(2019, 12, 31), Decimal("18.91"), Decimal("28.37")),
    TramoIBCUsura(date(2020, 1, 1), date(2020, 1, 31), Decimal("18.77"), Decimal("28.16")),
    TramoIBCUsura(date(2020, 2, 1), date(2020, 2, 29), Decimal("19.06"), Decimal("28.59")),
    TramoIBCUsura(date(2020, 3, 1), date(2020, 3, 31), Decimal("18.95"), Decimal("28.43")),
    TramoIBCUsura(date(2020, 4, 1), date(2020, 4, 30), Decimal("18.69"), Decimal("28.04")),
    TramoIBCUsura(date(2020, 5, 1), date(2020, 5, 31), Decimal("18.19"), Decimal("27.29")),
    TramoIBCUsura(date(2020, 6, 1), date(2020, 6, 30), Decimal("18.12"), Decimal("27.18")),
    TramoIBCUsura(date(2020, 7, 1), date(2020, 7, 31), Decimal("18.12"), Decimal("27.18")),
    TramoIBCUsura(date(2020, 8, 1), date(2020, 8, 31), Decimal("18.29"), Decimal("27.44")),
    TramoIBCUsura(date(2020, 9, 1), date(2020, 9, 30), Decimal("18.35"), Decimal("27.53")),
    TramoIBCUsura(date(2020, 10, 1), date(2020, 10, 31), Decimal("18.09"), Decimal("27.14")),
    TramoIBCUsura(date(2020, 11, 1), date(2020, 11, 30), Decimal("17.84"), Decimal("26.76")),
    TramoIBCUsura(date(2020, 12, 1), date(2020, 12, 31), Decimal("17.46"), Decimal("26.19")),
    TramoIBCUsura(date(2021, 1, 1), date(2021, 1, 31), Decimal("17.32"), Decimal("25.98")),
    TramoIBCUsura(date(2021, 2, 1), date(2021, 2, 28), Decimal("17.54"), Decimal("26.31")),
    TramoIBCUsura(date(2021, 3, 1), date(2021, 3, 31), Decimal("17.41"), Decimal("26.12")),
    TramoIBCUsura(date(2021, 4, 1), date(2021, 4, 30), Decimal("17.31"), Decimal("25.97")),
    TramoIBCUsura(date(2021, 5, 1), date(2021, 5, 31), Decimal("17.22"), Decimal("25.83")),
    TramoIBCUsura(date(2021, 6, 1), date(2021, 6, 30), Decimal("17.21"), Decimal("25.82")),
    TramoIBCUsura(date(2021, 7, 1), date(2021, 7, 31), Decimal("17.18"), Decimal("25.77")),
    TramoIBCUsura(date(2021, 8, 1), date(2021, 8, 31), Decimal("17.24"), Decimal("25.86")),
    TramoIBCUsura(date(2021, 9, 1), date(2021, 9, 30), Decimal("17.19"), Decimal("25.79")),
    TramoIBCUsura(date(2021, 10, 1), date(2021, 10, 31), Decimal("17.08"), Decimal("25.62")),
    TramoIBCUsura(date(2021, 11, 1), date(2021, 11, 30), Decimal("17.27"), Decimal("25.91")),
    TramoIBCUsura(date(2021, 12, 1), date(2021, 12, 31), Decimal("17.46"), Decimal("26.19")),
    TramoIBCUsura(date(2022, 1, 1), date(2022, 1, 31), Decimal("17.66"), Decimal("26.49")),
    TramoIBCUsura(date(2022, 2, 1), date(2022, 2, 28), Decimal("18.30"), Decimal("27.45")),
    TramoIBCUsura(date(2022, 3, 1), date(2022, 3, 31), Decimal("18.47"), Decimal("27.71")),
    TramoIBCUsura(date(2022, 4, 1), date(2022, 4, 30), Decimal("19.05"), Decimal("28.58")),
    TramoIBCUsura(date(2022, 5, 1), date(2022, 5, 31), Decimal("19.71"), Decimal("29.57")),
    TramoIBCUsura(date(2022, 6, 1), date(2022, 6, 30), Decimal("20.40"), Decimal("30.60")),
    TramoIBCUsura(date(2022, 7, 1), date(2022, 7, 31), Decimal("21.28"), Decimal("31.92")),
    TramoIBCUsura(date(2022, 8, 1), date(2022, 8, 31), Decimal("22.21"), Decimal("33.32")),
    TramoIBCUsura(date(2022, 9, 1), date(2022, 9, 30), Decimal("23.50"), Decimal("35.25")),
    TramoIBCUsura(date(2022, 10, 1), date(2022, 10, 31), Decimal("24.61"), Decimal("36.92")),
    TramoIBCUsura(date(2022, 11, 1), date(2022, 11, 30), Decimal("25.78"), Decimal("38.67")),
    TramoIBCUsura(date(2022, 12, 1), date(2022, 12, 31), Decimal("27.64"), Decimal("41.46")),
    TramoIBCUsura(date(2023, 1, 1), date(2023, 1, 31), Decimal("28.84"), Decimal("43.26")),
    TramoIBCUsura(date(2023, 2, 1), date(2023, 2, 28), Decimal("30.18"), Decimal("45.27")),
    TramoIBCUsura(date(2023, 3, 1), date(2023, 3, 31), Decimal("30.84"), Decimal("46.26")),
    TramoIBCUsura(date(2023, 4, 1), date(2023, 4, 30), Decimal("31.39"), Decimal("47.09")),
    TramoIBCUsura(date(2023, 5, 1), date(2023, 5, 31), Decimal("30.27"), Decimal("45.41")),
    TramoIBCUsura(date(2023, 6, 1), date(2023, 6, 30), Decimal("29.76"), Decimal("44.64")),
    TramoIBCUsura(date(2023, 7, 1), date(2023, 7, 31), Decimal("29.36"), Decimal("44.04")),
    TramoIBCUsura(date(2023, 8, 1), date(2023, 8, 31), Decimal("28.75"), Decimal("43.13")),
    TramoIBCUsura(date(2023, 9, 1), date(2023, 9, 30), Decimal("28.03"), Decimal("42.05")),
    TramoIBCUsura(date(2023, 10, 1), date(2023, 10, 31), Decimal("26.53"), Decimal("39.80")),
    TramoIBCUsura(date(2023, 11, 1), date(2023, 11, 30), Decimal("25.52"), Decimal("38.28")),
    TramoIBCUsura(date(2023, 12, 1), date(2023, 12, 31), Decimal("25.04"), Decimal("37.56")),
    TramoIBCUsura(date(2024, 1, 1), date(2024, 1, 31), Decimal("23.32"), Decimal("34.98")),
    TramoIBCUsura(date(2024, 2, 1), date(2024, 2, 29), Decimal("23.31"), Decimal("34.97")),
    TramoIBCUsura(date(2024, 3, 1), date(2024, 3, 31), Decimal("22.20"), Decimal("33.30")),
    TramoIBCUsura(date(2024, 4, 1), date(2024, 4, 30), Decimal("22.06"), Decimal("33.09")),
    TramoIBCUsura(date(2024, 5, 1), date(2024, 5, 31), Decimal("21.02"), Decimal("31.53")),
    TramoIBCUsura(date(2024, 6, 1), date(2024, 6, 30), Decimal("20.56"), Decimal("30.84")),
    TramoIBCUsura(date(2024, 7, 1), date(2024, 7, 31), Decimal("19.66"), Decimal("29.49")),
    TramoIBCUsura(date(2024, 8, 1), date(2024, 8, 31), Decimal("19.47"), Decimal("29.21")),
    TramoIBCUsura(date(2024, 9, 1), date(2024, 9, 30), Decimal("19.23"), Decimal("28.85")),
    TramoIBCUsura(date(2024, 10, 1), date(2024, 10, 31), Decimal("18.78"), Decimal("28.17")),
    TramoIBCUsura(date(2024, 11, 1), date(2024, 11, 30), Decimal("18.60"), Decimal("27.90")),
    TramoIBCUsura(date(2024, 12, 1), date(2024, 12, 31), Decimal("17.59"), Decimal("26.39")),
    TramoIBCUsura(date(2025, 1, 1), date(2025, 1, 31), Decimal("16.59"), Decimal("24.89")),
    TramoIBCUsura(date(2025, 2, 1), date(2025, 2, 28), Decimal("17.53"), Decimal("26.30")),
    TramoIBCUsura(date(2025, 3, 1), date(2025, 3, 31), Decimal("16.61"), Decimal("24.92")),
    TramoIBCUsura(date(2025, 4, 1), date(2025, 4, 30), Decimal("17.08"), Decimal("25.62")),
    TramoIBCUsura(date(2025, 5, 1), date(2025, 5, 31), Decimal("17.31"), Decimal("25.97")),
    TramoIBCUsura(date(2025, 6, 1), date(2025, 6, 30), Decimal("17.03"), Decimal("25.55")),
    TramoIBCUsura(date(2025, 7, 1), date(2025, 7, 31), Decimal("16.52"), Decimal("24.78")),
    TramoIBCUsura(date(2025, 8, 1), date(2025, 8, 31), Decimal("16.78"), Decimal("25.17")),
    TramoIBCUsura(date(2025, 9, 1), date(2025, 9, 30), Decimal("16.67"), Decimal("25.01")),
    TramoIBCUsura(date(2025, 10, 1), date(2025, 10, 31), Decimal("16.24"), Decimal("24.36")),
    TramoIBCUsura(date(2025, 11, 1), date(2025, 11, 30), Decimal("16.66"), Decimal("24.99")),
    TramoIBCUsura(date(2025, 12, 1), date(2025, 12, 31), Decimal("16.68"), Decimal("25.02")),
    TramoIBCUsura(date(2026, 1, 1), date(2026, 1, 31), Decimal("16.24"), Decimal("24.36")),
    TramoIBCUsura(date(2026, 2, 1), date(2026, 2, 28), Decimal("16.82"), Decimal("25.23")),
    TramoIBCUsura(date(2026, 3, 1), date(2026, 3, 31), Decimal("17.01"), Decimal("25.52")),
    TramoIBCUsura(date(2026, 4, 1), date(2026, 4, 30), Decimal("17.84"), Decimal("26.76")),
    TramoIBCUsura(date(2026, 5, 1), date(2026, 5, 31), Decimal("18.78"), Decimal("28.17")),
    TramoIBCUsura(date(2026, 6, 1), date(2026, 6, 30), Decimal("19.19"), Decimal("28.79")),
    TramoIBCUsura(date(2026, 7, 1), date(2026, 7, 31), Decimal("19.19"), Decimal("28.79")),
]


def get_ibc_usura_for_date(fecha: date) -> Tuple[Decimal, Decimal]:
    """Retorna (ibc_anual, usura_anual) certificados por la SFC para la linea
    'Consumo y Ordinario' (sucesora de 'Comercial' desde 2007) vigentes en `fecha`.
    Datos disponibles: 1997-07-01 a 2026-07-31."""
    for tramo in _TRAMOS_IBC_USURA:
        if tramo.inicio <= fecha <= tramo.fin:
            return (tramo.ibc_anual, tramo.usura_anual)
    raise ValueError(
        f"No hay tramo de IBC/Usura configurado para la fecha {fecha}. "
        f"Datos disponibles: {_TRAMOS_IBC_USURA[0].inicio} a {_TRAMOS_IBC_USURA[-1].fin}."
    )
