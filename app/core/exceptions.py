class AreaNoImplementadaError(Exception):
    """Se lanza cuando se intenta liquidar un area del derecho aun no implementada."""


class UVTNoDisponibleError(Exception):
    """Se lanza cuando se necesita el valor de UVT para un año fuera del rango cargado
    (tabla historica 2006-2026, ver historical_index.get_uvt_for_year) -- por ejemplo,
    un hecho sancionatorio de 2027 en adelante, cuya UVT aun no ha sido publicada por
    la DIAN."""


class CuotaLitisExcedeTopeError(Exception):
    """Se lanza cuando honorarios fijos + cuota litis exceden el tope legal absoluto y
    definitivo del 50% del beneficio obtenido (Art. 35 Num. 4 Ley 1123/2007) -- un solo
    tope acumulado, no dos en cascada (corregido Sprint 4 tras respuesta del despacho)."""


class ParametroNoDisponibleError(Exception):
    """Se lanza cuando no hay un valor de un parametro legal versionado disponible
    para la fecha pedida (ver app/services/parametro_service.py)."""


class TarifaNoDisponibleError(Exception):
    """Se lanza cuando no hay una tarifa de agencias en derecho registrada (Acuerdo
    PSAA16-10554) para la combinacion tipo_proceso/instancia/cuantia pedida -- nunca
    se inventa un rango."""


class TarifaPreCGPNoDisponibleError(Exception):
    """Se lanza cuando la providencia que impone costas (fecha_providencia_costas) es
    anterior al 1 de enero de 2016 (entrada en vigencia del CGP, Ley 1564 de 2012) --
    Art. 624 CGP, regla de aplicacion inmediata / ultraactividad de la ley procesal
    anterior (CPC). El sistema solo tiene cargada la tabla del Acuerdo PSAA16-10554
    (vigente desde el CGP, 2016 en adelante); no existe ninguna tabla de tarifas
    pre-CGP (era CPC) en el proyecto -- ni el PDF de requisitos ni ninguna respuesta
    del despacho la trajo nunca. Nunca se aproxima ni se bloquea silenciosamente."""


class CostasFueraDeRangoError(Exception):
    """Se lanza cuando el porcentaje manual de costas procesales (costas_pct_manual)
    esta fuera del rango permitido para la cuantia del proceso (CGP art. 25 / respuesta
    del despacho, docs/Preguntas-Para-Abogado-Respondidas.md Sprint 18) -- el sistema
    rechaza el valor, nunca lo trunca al limite mas cercano."""


class TRMNoDisponibleError(Exception):
    """Se lanza cuando no se pudo obtener la TRM certificada por la Superintendencia
    Financiera para una fecha (falla de red, o la fecha no tiene TRM certificada) --
    ver app/engine/currency/trm_provider.py, SFCTRMProvider (Sprint 12, correccion
    2026-08-01: la TRM ya no se digita manualmente, se consulta en vivo)."""


class IPCMensualNoDisponibleError(Exception):
    """Se lanza cuando se necesita el indice IPC mensual real del DANE para un mes que
    no esta cargado en historical_index._IPC_MENSUAL -- tabla deliberadamente vacia
    desde el Sprint 8 (2026-08-01) a la espera de que el despacho aporte la fuente
    (ver docs/Preguntas-Para-Abogado-Respondidas.md); nunca se aproxima con la serie
    anual ni con el ultimo mes disponible."""


class DatoFaltanteError(ValueError):
    """Se lanza cuando LegalTextExtractor.validate_and_fill necesita un dato
    faltante (capital o fecha de exigibilidad) pero no hay una forma segura
    de pedirlo: no se inyecto un prompt_fn y tampoco hay stdin interactivo
    disponible (ver app/engine/text/nlp_extractor.py, Sprint 27) -- evita el
    bloqueo original en un ejecutable sin consola adjunta."""
