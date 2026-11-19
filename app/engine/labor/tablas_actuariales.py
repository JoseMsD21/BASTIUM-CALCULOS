"""Tablas actuariales del Decreto 1296 de 2022 (Sprints 86/87).

Transcritas literalmente (extraidas por script, no a mano) de la respuesta
del despacho del 16/11/2026, `docs/Preguntas-Para-Abogado-Respondidas.md`,
seccion "Sprint 86/87 (seguimiento) -- Tabla actuarial completa (FAC1/FAC2),
serie DTF Pensional, y cual formula de FAC3 es la correcta":

- Tabla 2: factores actuariales FAC1 y FAC2 por edad (55-90) y sexo
  (Decreto 1296 de 2022, Art. 1, Tabla 2 -- Resolucion 1555 de 2010 SFC).
- Tabla 1: Salarios Medios Nacionales (SMN) por edad (12 a "71+"),
  expresados como indice con base 1.000000 a los 12 años (Decreto 1296 de
  2022, Art. 1, Tabla 1 -- Decreto 2779 de 1994 / Res. 1588 de 1994 DANE).

No se corrigio ni suavizo ningun valor. Observaciones sobre la fuente que se
dejan tal cual (reportadas al despacho, no "arregladas" aqui):
- La columna FAC1_Mujeres coincide, desplazada 5 años, con FAC1_Hombres
  (p. ej. FAC1_Mujeres(55) = FAC1_Hombres(60) = 243.005182).
- El SMN salta de 1.006649 (13 años) a 1.135599 (14 años), y de 2.941441
  (39) a 2.959570 (40), saltos que no siguen la curva suave del resto.

El consumo (interpolacion por dias) vive en `app.engine.labor.calculo_actuarial`.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class FactoresActuariales:
    fac1_hombres: Decimal
    fac1_mujeres: Decimal
    fac2_hombres: Decimal
    fac2_mujeres: Decimal


EDAD_MINIMA_FAC = 55
EDAD_MAXIMA_FAC = 90
EDAD_MINIMA_SMN = 12
EDAD_TOPE_SMN = 71  # la fila "71+" aplica a cualquier edad >= 71

FAC1_FAC2_POR_EDAD: dict[int, FactoresActuariales] = {
    55: FactoresActuariales(
        fac1_hombres=Decimal("258.712212"),
        fac1_mujeres=Decimal("243.005182"),
        fac2_hombres=Decimal("0.369543"),
        fac2_mujeres=Decimal("0.311687"),
    ),
    56: FactoresActuariales(
        fac1_hombres=Decimal("255.775386"),
        fac1_mujeres=Decimal("239.546338"),
        fac2_hombres=Decimal("0.381199"),
        fac2_mujeres=Decimal("0.322235"),
    ),
    57: FactoresActuariales(
        fac1_hombres=Decimal("252.738260"),
        fac1_mujeres=Decimal("235.977078"),
        fac2_hombres=Decimal("0.393132"),
        fac2_mujeres=Decimal("0.333081"),
    ),
    58: FactoresActuariales(
        fac1_hombres=Decimal("249.598775"),
        fac1_mujeres=Decimal("232.296362"),
        fac2_hombres=Decimal("0.405334"),
        fac2_mujeres=Decimal("0.344225"),
    ),
    59: FactoresActuariales(
        fac1_hombres=Decimal("246.355000"),
        fac1_mujeres=Decimal("228.506137"),
        fac2_hombres=Decimal("0.417797"),
        fac2_mujeres=Decimal("0.355667"),
    ),
    60: FactoresActuariales(
        fac1_hombres=Decimal("243.005182"),
        fac1_mujeres=Decimal("224.606020"),
        fac2_hombres=Decimal("0.430511"),
        fac2_mujeres=Decimal("0.367403"),
    ),
    61: FactoresActuariales(
        fac1_hombres=Decimal("239.546338"),
        fac1_mujeres=Decimal("220.596052"),
        fac2_hombres=Decimal("0.443465"),
        fac2_mujeres=Decimal("0.379431"),
    ),
    62: FactoresActuariales(
        fac1_hombres=Decimal("235.977078"),
        fac1_mujeres=Decimal("216.476560"),
        fac2_hombres=Decimal("0.456646"),
        fac2_mujeres=Decimal("0.391747"),
    ),
    63: FactoresActuariales(
        fac1_hombres=Decimal("232.296362"),
        fac1_mujeres=Decimal("212.248425"),
        fac2_hombres=Decimal("0.470038"),
        fac2_mujeres=Decimal("0.404345"),
    ),
    64: FactoresActuariales(
        fac1_hombres=Decimal("228.506137"),
        fac1_mujeres=Decimal("207.912956"),
        fac2_hombres=Decimal("0.483532"),
        fac2_mujeres=Decimal("0.417217"),
    ),
    65: FactoresActuariales(
        fac1_hombres=Decimal("224.606020"),
        fac1_mujeres=Decimal("203.471943"),
        fac2_hombres=Decimal("0.497111"),
        fac2_mujeres=Decimal("0.430356"),
    ),
    66: FactoresActuariales(
        fac1_hombres=Decimal("220.596052"),
        fac1_mujeres=Decimal("198.927674"),
        fac2_hombres=Decimal("0.510762"),
        fac2_mujeres=Decimal("0.443751"),
    ),
    67: FactoresActuariales(
        fac1_hombres=Decimal("216.476560"),
        fac1_mujeres=Decimal("194.283137"),
        fac2_hombres=Decimal("0.524466"),
        fac2_mujeres=Decimal("0.457390"),
    ),
    68: FactoresActuariales(
        fac1_hombres=Decimal("212.248425"),
        fac1_mujeres=Decimal("189.541818"),
        fac2_hombres=Decimal("0.538207"),
        fac2_mujeres=Decimal("0.471261"),
    ),
    69: FactoresActuariales(
        fac1_hombres=Decimal("207.912956"),
        fac1_mujeres=Decimal("184.707913"),
        fac2_hombres=Decimal("0.551966"),
        fac2_mujeres=Decimal("0.485348"),
    ),
    70: FactoresActuariales(
        fac1_hombres=Decimal("203.471943"),
        fac1_mujeres=Decimal("179.786208"),
        fac2_hombres=Decimal("0.565725"),
        fac2_mujeres=Decimal("0.499635"),
    ),
    71: FactoresActuariales(
        fac1_hombres=Decimal("198.927674"),
        fac1_mujeres=Decimal("174.782204"),
        fac2_hombres=Decimal("0.579465"),
        fac2_mujeres=Decimal("0.514104"),
    ),
    72: FactoresActuariales(
        fac1_hombres=Decimal("194.283137"),
        fac1_mujeres=Decimal("169.702078"),
        fac2_hombres=Decimal("0.593165"),
        fac2_mujeres=Decimal("0.528734"),
    ),
    73: FactoresActuariales(
        fac1_hombres=Decimal("189.541818"),
        fac1_mujeres=Decimal("164.552725"),
        fac2_hombres=Decimal("0.606808"),
        fac2_mujeres=Decimal("0.543503"),
    ),
    74: FactoresActuariales(
        fac1_hombres=Decimal("184.707913"),
        fac1_mujeres=Decimal("159.341662"),
        fac2_hombres=Decimal("0.620372"),
        fac2_mujeres=Decimal("0.558388"),
    ),
    75: FactoresActuariales(
        fac1_hombres=Decimal("179.786208"),
        fac1_mujeres=Decimal("154.077066"),
        fac2_hombres=Decimal("0.633837"),
        fac2_mujeres=Decimal("0.573365"),
    ),
    76: FactoresActuariales(
        fac1_hombres=Decimal("174.782204"),
        fac1_mujeres=Decimal("148.767735"),
        fac2_hombres=Decimal("0.647184"),
        fac2_mujeres=Decimal("0.588406"),
    ),
    77: FactoresActuariales(
        fac1_hombres=Decimal("169.702078"),
        fac1_mujeres=Decimal("143.423124"),
        fac2_hombres=Decimal("0.660392"),
        fac2_mujeres=Decimal("0.603484"),
    ),
    78: FactoresActuariales(
        fac1_hombres=Decimal("164.552725"),
        fac1_mujeres=Decimal("138.053206"),
        fac2_hombres=Decimal("0.673442"),
        fac2_mujeres=Decimal("0.618571"),
    ),
    79: FactoresActuariales(
        fac1_hombres=Decimal("159.341662"),
        fac1_mujeres=Decimal("132.668444"),
        fac2_hombres=Decimal("0.686313"),
        fac2_mujeres=Decimal("0.633634"),
    ),
    80: FactoresActuariales(
        fac1_hombres=Decimal("154.077066"),
        fac1_mujeres=Decimal("127.279561"),
        fac2_hombres=Decimal("0.698988"),
        fac2_mujeres=Decimal("0.648645"),
    ),
    81: FactoresActuariales(
        fac1_hombres=Decimal("148.767735"),
        fac1_mujeres=Decimal("121.897577"),
        fac2_hombres=Decimal("0.711448"),
        fac2_mujeres=Decimal("0.663572"),
    ),
    82: FactoresActuariales(
        fac1_hombres=Decimal("143.423124"),
        fac1_mujeres=Decimal("116.533716"),
        fac2_hombres=Decimal("0.723675"),
        fac2_mujeres=Decimal("0.678385"),
    ),
    83: FactoresActuariales(
        fac1_hombres=Decimal("138.053206"),
        fac1_mujeres=Decimal("111.199165"),
        fac2_hombres=Decimal("0.735655"),
        fac2_mujeres=Decimal("0.693051"),
    ),
    84: FactoresActuariales(
        fac1_hombres=Decimal("132.668444"),
        fac1_mujeres=Decimal("105.904739"),
        fac2_hombres=Decimal("0.747370"),
        fac2_mujeres=Decimal("0.707542"),
    ),
    85: FactoresActuariales(
        fac1_hombres=Decimal("127.279561"),
        fac1_mujeres=Decimal("100.661169"),
        fac2_hombres=Decimal("0.758807"),
        fac2_mujeres=Decimal("0.721827"),
    ),
    86: FactoresActuariales(
        fac1_hombres=Decimal("121.897577"),
        fac1_mujeres=Decimal("95.478330"),
        fac2_hombres=Decimal("0.769955"),
        fac2_mujeres=Decimal("0.735880"),
    ),
    87: FactoresActuariales(
        fac1_hombres=Decimal("116.533716"),
        fac1_mujeres=Decimal("90.365266"),
        fac2_hombres=Decimal("0.780801"),
        fac2_mujeres=Decimal("0.749677"),
    ),
    88: FactoresActuariales(
        fac1_hombres=Decimal("111.199165"),
        fac1_mujeres=Decimal("85.329825"),
        fac2_hombres=Decimal("0.791336"),
        fac2_mujeres=Decimal("0.763196"),
    ),
    89: FactoresActuariales(
        fac1_hombres=Decimal("105.904739"),
        fac1_mujeres=Decimal("80.378652"),
        fac2_hombres=Decimal("0.801555"),
        fac2_mujeres=Decimal("0.776422"),
    ),
    90: FactoresActuariales(
        fac1_hombres=Decimal("100.661169"),
        fac1_mujeres=Decimal("75.516659"),
        fac2_hombres=Decimal("0.811453"),
        fac2_mujeres=Decimal("0.789343"),
    ),
}

SALARIO_MEDIO_NACIONAL_POR_EDAD: dict[int, Decimal] = {
    12: Decimal("1.000000"),
    13: Decimal("1.006649"),
    14: Decimal("1.135599"),
    15: Decimal("1.206678"),
    16: Decimal("1.279752"),
    17: Decimal("1.354687"),
    18: Decimal("1.431251"),
    19: Decimal("1.509273"),
    20: Decimal("1.588504"),
    21: Decimal("1.668693"),
    22: Decimal("1.749612"),
    23: Decimal("1.830933"),
    24: Decimal("1.912388"),
    25: Decimal("1.993652"),
    26: Decimal("2.074416"),
    27: Decimal("2.154318"),
    28: Decimal("2.233031"),
    29: Decimal("2.310209"),
    30: Decimal("2.385489"),
    31: Decimal("2.458524"),
    32: Decimal("2.528971"),
    33: Decimal("2.596463"),
    34: Decimal("2.660676"),
    35: Decimal("2.721264"),
    36: Decimal("2.777921"),
    37: Decimal("2.830357"),
    38: Decimal("2.878287"),
    39: Decimal("2.941441"),
    40: Decimal("2.959570"),
    41: Decimal("2.992482"),
    42: Decimal("3.020004"),
    43: Decimal("3.041946"),
    44: Decimal("3.058210"),
    45: Decimal("3.068682"),
    46: Decimal("3.073323"),
    47: Decimal("3.072096"),
    48: Decimal("3.065019"),
    49: Decimal("3.052111"),
    50: Decimal("3.033468"),
    51: Decimal("3.009187"),
    52: Decimal("2.979401"),
    53: Decimal("2.944284"),
    54: Decimal("2.904026"),
    55: Decimal("2.858858"),
    56: Decimal("2.809030"),
    57: Decimal("2.754790"),
    58: Decimal("2.696446"),
    59: Decimal("2.634304"),
    60: Decimal("2.568691"),
    61: Decimal("2.499933"),
    62: Decimal("2.428355"),
    63: Decimal("2.354341"),
    64: Decimal("2.278237"),
    65: Decimal("2.200368"),
    66: Decimal("2.121119"),
    67: Decimal("2.040814"),
    68: Decimal("1.959800"),
    69: Decimal("1.878421"),
    70: Decimal("1.796985"),
    71: Decimal("1.715798"),  # "71+" en la fuente: aplica a toda edad >= 71
}
