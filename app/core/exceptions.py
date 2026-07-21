class AreaNoImplementadaError(Exception):
    """Se lanza cuando se intenta liquidar un area del derecho aun no implementada."""


class TasaUsurariaError(Exception):
    """Se lanza cuando una tasa pactada (remuneratoria o moratoria) supera 1.5x el IBC vigente."""


class UVTNoDisponibleError(Exception):
    """Se lanza cuando se necesita el valor de UVT para un año fuera del rango cargado
    (tabla historica 2006-2026, ver historical_index.get_uvt_for_year) -- por ejemplo,
    un hecho sancionatorio de 2027 en adelante, cuya UVT aun no ha sido publicada por
    la DIAN."""


class CuotaLitisExcedeTopeError(Exception):
    """Se lanza cuando honorarios fijos + cuota litis exceden el tope legal (30% cuota
    litis sola, 50% suma total del beneficio obtenido)."""


class ParametroNoDisponibleError(Exception):
    """Se lanza cuando no hay un valor de un parametro legal versionado disponible
    para la fecha pedida (ver app/services/parametro_service.py)."""
