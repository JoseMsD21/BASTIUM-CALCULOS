"""
Series historicas de indicadores economicos colombianos, transcritas y verificadas
contra REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf (paginas 55-61).

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
