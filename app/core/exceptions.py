class AreaNoImplementadaError(Exception):
    """Se lanza cuando se intenta liquidar un area del derecho aun no implementada."""


class TasaUsurariaError(Exception):
    """Se lanza cuando una tasa pactada (remuneratoria o moratoria) supera 1.5x el IBC vigente."""


class UVTNoDisponibleError(Exception):
    """Se lanza cuando se necesita el valor de UVT para una fecha posterior a 2020-01-01
    y no hay tabla historica cargada (ver Pendientes.md Sprint 5)."""


class CuotaLitisExcedeTopeError(Exception):
    """Se lanza cuando honorarios fijos + cuota litis exceden el tope legal (30% cuota
    litis sola, 50% suma total del beneficio obtenido)."""
