"""Numero de radicacion judicial de 23 digitos (Acuerdo 201 de 1997 del C.S.J.).

Estructura (12 digitos de ubicacion + 11 del proceso, Circular PCSJC19-7):

    DANE(5) | Corporacion/juzgado(2) | Sala o especialidad(2) | Despacho(3)
    | Ano(4) | Consecutivo de radicacion(5) | Consecutivo de recursos(2)

Es validacion ESTRUCTURAL: comprueba longitud, digitos, departamento DANE y rangos; no
verifica que el despacho exista ni mapea los codigos de corporacion/especialidad (catalogo
pendiente de confirmar con el despacho, ver docs/Preguntas-Para-Abogado-Abiertas.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

LONGITUD = 23
ANIO_MINIMO, ANIO_MAXIMO = 1900, 2100

# Divipola (DANE): codigos de departamento (32) + Bogota D.C. (11).
DEPARTAMENTOS_DANE: dict[str, str] = {
    "05": "Antioquia",
    "08": "Atlántico",
    "11": "Bogotá D.C.",
    "13": "Bolívar",
    "15": "Boyacá",
    "17": "Caldas",
    "18": "Caquetá",
    "19": "Cauca",
    "20": "Cesar",
    "23": "Córdoba",
    "25": "Cundinamarca",
    "27": "Chocó",
    "41": "Huila",
    "44": "La Guajira",
    "47": "Magdalena",
    "50": "Meta",
    "52": "Nariño",
    "54": "Norte de Santander",
    "63": "Quindío",
    "66": "Risaralda",
    "68": "Santander",
    "70": "Sucre",
    "73": "Tolima",
    "76": "Valle del Cauca",
    "81": "Arauca",
    "85": "Casanare",
    "86": "Putumayo",
    "88": "San Andrés y Providencia",
    "91": "Amazonas",
    "94": "Guainía",
    "95": "Guaviare",
    "97": "Vaupés",
    "99": "Vichada",
}


class RadicadoInvalido(ValueError):
    """El texto no es un radicado de 23 digitos valido."""


@dataclass(frozen=True)
class Radicado:
    divipola: str
    corporacion: str
    especialidad: str
    despacho: str
    anio: str
    consecutivo: str
    recurso: str

    @property
    def departamento(self) -> str:
        return self.divipola[:2]

    @property
    def municipio(self) -> str:
        return self.divipola[2:]

    @property
    def nombre_departamento(self) -> str:
        return DEPARTAMENTOS_DANE[self.departamento]

    @property
    def compacto(self) -> str:
        """Los 23 digitos sin separadores: forma canonica para almacenar y comparar."""
        return (
            f"{self.divipola}{self.corporacion}{self.especialidad}{self.despacho}"
            f"{self.anio}{self.consecutivo}{self.recurso}"
        )

    @property
    def formateado(self) -> str:
        """Forma de lectura habitual en providencias: 41001-31-03-002-2024-00123-00."""
        return "-".join(
            (
                self.divipola,
                self.corporacion,
                self.especialidad,
                self.despacho,
                self.anio,
                self.consecutivo,
                self.recurso,
            )
        )

    def __str__(self) -> str:
        return self.compacto


_SEPARADORES = re.compile(r"[\s\-._/]")


def parsear_radicado(texto: str) -> Radicado:
    """Acepta los 23 digitos con o sin separadores (espacio, guion, punto, raya)."""
    if not isinstance(texto, str):
        raise RadicadoInvalido("El radicado debe ser texto.")
    digitos = _SEPARADORES.sub("", texto.strip())
    if digitos and (not digitos.isascii() or not digitos.isdigit()):
        raise RadicadoInvalido(
            "El radicado solo admite dígitos y separadores (espacio, guion, punto)."
        )
    if len(digitos) != LONGITUD:
        raise RadicadoInvalido(f"El radicado debe tener {LONGITUD} dígitos; tiene {len(digitos)}.")
    r = Radicado(
        divipola=digitos[0:5],
        corporacion=digitos[5:7],
        especialidad=digitos[7:9],
        despacho=digitos[9:12],
        anio=digitos[12:16],
        consecutivo=digitos[16:21],
        recurso=digitos[21:23],
    )
    if r.departamento not in DEPARTAMENTOS_DANE:
        raise RadicadoInvalido(f"Código de departamento DANE desconocido: {r.departamento}.")
    if r.municipio == "000":
        raise RadicadoInvalido("Código de municipio DANE inválido: 000.")
    if not (ANIO_MINIMO <= int(r.anio) <= ANIO_MAXIMO):
        raise RadicadoInvalido(f"Año de radicación fuera de rango: {r.anio}.")
    if int(r.consecutivo) == 0:
        raise RadicadoInvalido("El consecutivo de radicación no puede ser 00000.")
    if int(r.despacho) == 0:
        raise RadicadoInvalido("El consecutivo del despacho no puede ser 000.")
    return r


def es_radicado_valido(texto: str) -> bool:
    try:
        parsear_radicado(texto)
    except RadicadoInvalido:
        return False
    return True
