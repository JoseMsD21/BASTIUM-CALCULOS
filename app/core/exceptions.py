class AreaNoImplementadaError(Exception):
    """Se lanza cuando se intenta liquidar un area del derecho aun no implementada."""


class TasaUsurariaError(Exception):
    """Se lanza cuando una tasa pactada (remuneratoria o moratoria) supera 1.5x el IBC vigente."""
