"""
Servicio de parametros legales versionados: valores/tasas/topes/plazos que
antes vivian como constantes Python sueltas (usura, cuota litis, prescripcion,
E.T. 635, tasa civil legal) o como series versionadas solo en codigo (SMLMV,
IPC, IBC/usura, ver historical_index.py) pasan a vivir en la tabla
parametros_legales, editable desde la GUI (app/views/configuracion.py) sin
tocar Python ni redesplegar.

Ver docs/superpowers/specs/2026-07-20-parametros-legales-versionados-design.md
para el diseno completo, en particular la Adenda de modos de resolucion.

Tabla append-only para las filas de sistema (sembradas por
scripts/migrate_parametros_legales.py / scripts/migrate_ipc_variacion_anual.py,
creado_por_sistema=True): nunca se editan ni se borran. Las filas creadas por
un usuario desde la GUI (creado_por_sistema=False) SI se pueden editar/borrar
-- ver editar_valor()/eliminar_valor() mas abajo -- excepcion deliberada,
acotada por ese flag. Las columnas usuario/motivo/creado_en de cada fila
siguen siendo la bitacora, ahora con la salvedad de que las filas de usuario
pueden cambiar de estado tras crearse.
"""

from __future__ import annotations

import enum
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime
from decimal import Decimal
from typing import NamedTuple

import database.session as session_module
from app.core.exceptions import ParametroNoDisponibleError
from app.services.areas_parametro import serializar_areas
from database.models import AreaDerecho, ParametroLegal


class ModoResolucion(enum.Enum):
    ABIERTO = "ABIERTO"
    ANUAL_EXACTO = "ANUAL_EXACTO"
    TRAMO_CERRADO = "TRAMO_CERRADO"


class InfoParametro(NamedTuple):
    descripcion: str
    categoria: str
    fuente_legal: str
    modo: ModoResolucion


CATALOGO_PARAMETROS: dict[str, InfoParametro] = {
    "USURA_MULTIPLICADOR": InfoParametro(
        "Multiplicador del tope de usura sobre el IBC",
        "Topes legales",
        "Ley 45/1990, art. 72",
        ModoResolucion.ABIERTO,
    ),
    "HONORARIOS_TOTAL_PCT": InfoParametro(
        "Tope de honorarios fijos + cuota litis (% del beneficio obtenido)",
        "Topes legales",
        "Art. 35 Num. 4 Ley 1123/2007",
        ModoResolucion.ABIERTO,
    ),
    "ET635_PUNTOS_DESCUENTO": InfoParametro(
        "Puntos que se restan a la usura vigente para el interes moratorio tributario",
        "Topes legales",
        "Estatuto Tributario, art. 635",
        ModoResolucion.ABIERTO,
    ),
    "CIVIL_ANNUAL_RATE": InfoParametro(
        "Tasa de interes civil legal anual",
        "Topes legales",
        "Art. 1617 Codigo Civil",
        ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_EJECUTIVA_MESES": InfoParametro(
        "Plazo de prescripcion de la accion ejecutiva (meses)",
        "Plazos de prescripcion y caducidad",
        "PDF paginas 16/19, 42, 43, 45",
        ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_ORDINARIA_MESES": InfoParametro(
        "Plazo de prescripcion de la accion ordinaria (meses)",
        "Plazos de prescripcion y caducidad",
        "Art. 2536 Codigo Civil",
        ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_HONORARIOS_MESES": InfoParametro(
        "Plazo de prescripcion de honorarios profesionales (meses)",
        "Plazos de prescripcion y caducidad",
        "PDF pagina 35",
        ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_CAMBIARIA_DIRECTA_MESES": InfoParametro(
        "Plazo de prescripcion cambiaria directa (meses)",
        "Plazos de prescripcion y caducidad",
        "Art. 789 C.Co.",
        ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES": InfoParametro(
        "Plazo de prescripcion cambiaria de regreso del tenedor (meses)",
        "Plazos de prescripcion y caducidad",
        "Art. 790 C.Co.",
        ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES": InfoParametro(
        "Plazo de prescripcion cambiaria entre obligados de regreso (meses)",
        "Plazos de prescripcion y caducidad",
        "Art. 791 C.Co.",
        ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_IMPUGNACION_INEFICACIA_SOCIETARIA_MESES": InfoParametro(
        "Plazo de caducidad de impugnacion de ineficacia societaria (meses)",
        "Plazos de prescripcion y caducidad",
        "PDF pagina 40",
        ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_CHEQUES_MESES": InfoParametro(
        "Plazo de caducidad de la accion cambiaria del cheque (meses)",
        "Plazos de prescripcion y caducidad",
        "Respuesta del despacho, docs/Preguntas-Para-Abogado-Respondidas.md Sprint 7 (27/07/2026)",
        ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_ENRIQUECIMIENTO_SIN_CAUSA_MESES": InfoParametro(
        "Plazo de caducidad de la accion de enriquecimiento sin causa (meses)",
        "Plazos de prescripcion y caducidad",
        "Respuesta del despacho, docs/Preguntas-Para-Abogado-Respondidas.md Sprint 7 (27/07/2026)",
        ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_TRANSPORTE_MESES": InfoParametro(
        "Plazo de caducidad de la accion de transporte (meses)",
        "Plazos de prescripcion y caducidad",
        "Respuesta del despacho, docs/Preguntas-Para-Abogado-Respondidas.md Sprint 7 (27/07/2026)",
        ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_SEGURO_ORDINARIA_MESES": InfoParametro(
        "Plazo de prescripcion ordinaria del contrato de seguro (meses)",
        "Plazos de prescripcion y caducidad",
        "Respuesta del despacho, docs/Preguntas-Para-Abogado-Respondidas.md Sprint 7 (27/07/2026)",
        ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_SEGURO_EXTRAORDINARIA_MESES": InfoParametro(
        "Plazo de prescripcion extraordinaria del contrato de seguro (meses)",
        "Plazos de prescripcion y caducidad",
        "Respuesta del despacho, docs/Preguntas-Para-Abogado-Respondidas.md Sprint 7 (27/07/2026)",
        ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_IMPUGNACION_ACTAS_SOCIALES_MESES": InfoParametro(
        "Plazo de caducidad de impugnacion de actas sociales (meses)",
        "Plazos de prescripcion y caducidad",
        "Respuesta del despacho, docs/Preguntas-Para-Abogado-Respondidas.md Sprint 7 (27/07/2026)",
        ModoResolucion.ABIERTO,
    ),
    "SMLMV": InfoParametro(
        "Salario Minimo Legal Mensual Vigente",
        "Indicadores historicos",
        "PDF paginas 55-57",
        ModoResolucion.ANUAL_EXACTO,
    ),
    "IPC_INDICE_ACUMULADO": InfoParametro(
        "Indice de Precios al Consumidor acumulado (cierre de año, base 100 en 1966)",
        "Indicadores historicos",
        "PDF pagina 62",
        ModoResolucion.ANUAL_EXACTO,
    ),
    "IBC_CONSUMO_ORDINARIO": InfoParametro(
        "Interes Bancario Corriente, linea Consumo y Ordinario (% anual)",
        "Indicadores historicos",
        "PDF paginas 58-61 (SFC)",
        ModoResolucion.TRAMO_CERRADO,
    ),
    "USURA_CONSUMO_ORDINARIO": InfoParametro(
        "Tasa de usura, linea Consumo y Ordinario (% anual)",
        "Indicadores historicos",
        "PDF paginas 58-61 (SFC)",
        ModoResolucion.TRAMO_CERRADO,
    ),
    "UVT": InfoParametro(
        "Unidad de Valor Tributario (UVT)",
        "Indicadores historicos",
        "DIAN, resolucion anual (Ley 1111 de 2006)",
        ModoResolucion.ANUAL_EXACTO,
    ),
    "EXTEMPORANEIDAD_PCT_MENSUAL": InfoParametro(
        "Sanción por extemporaneidad, porcentaje mensual del impuesto a cargo",
        "Topes legales",
        "Estatuto Tributario (PDF pág. 39)",
        ModoResolucion.ABIERTO,
    ),
    "INEXACTITUD_PCT": InfoParametro(
        "Sanción por inexactitud, porcentaje de la diferencia (sin agravante)",
        "Topes legales",
        "Estatuto Tributario (PDF pág. 39)",
        ModoResolucion.ABIERTO,
    ),
    "INEXACTITUD_AGRAVADA_PCT": InfoParametro(
        "Sanción por inexactitud, porcentaje agravado (omisión de activos/pasivos inexistentes)",
        "Topes legales",
        "Estatuto Tributario (PDF pág. 39)",
        ModoResolucion.ABIERTO,
    ),
    "ERROR_ARITMETICO_PCT": InfoParametro(
        "Sanción por error aritmético, porcentaje de la diferencia generada",
        "Topes legales",
        "Estatuto Tributario (PDF pág. 39)",
        ModoResolucion.ABIERTO,
    ),
    # NOTA DE COORDINACION (Sprint 16, Task 3): las siguientes claves SS_* (13 en
    # total: SS_PENSION_PCT, SS_SALUD_PCT, SS_ARL_NIVEL_I..V_PCT y
    # SS_FSP_TRAMO_1..6_PCT) ya fueron agregadas en esta tarea con citas
    # verificadas contra Ley 100/1993 art. 20 (pension/salud), Decreto 1772/1994
    # (ARL) y Ley 797/2003 art. 8 (tramos FSP). Si una tarea posterior (p.ej.
    # Task 6) vuelve a tocar estas mismas claves con textos genericos tipo
    # "PDF pagina 51/52", NO sobrescribir sin mas: reconciliar con estas citas
    # mas precisas primero (los dict literals de Python dejan que la entrada
    # posterior gane en silencio).
    "SS_PENSION_PCT": InfoParametro(
        "Cotizacion total a pension (% del IBC, empleador + trabajador)",
        "Seguridad social",
        "Ley 100/1993, art. 20",
        ModoResolucion.ABIERTO,
    ),
    "SS_SALUD_PCT": InfoParametro(
        "Cotizacion total a salud (% del IBC, empleador + trabajador)",
        "Seguridad social",
        "Ley 100/1993, art. 204",
        ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_I_PCT": InfoParametro(
        "Cotizacion a ARL, nivel de riesgo I (% del IBC)",
        "Seguridad social",
        "Decreto 1772/1994",
        ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_II_PCT": InfoParametro(
        "Cotizacion a ARL, nivel de riesgo II (% del IBC)",
        "Seguridad social",
        "Decreto 1772/1994",
        ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_III_PCT": InfoParametro(
        "Cotizacion a ARL, nivel de riesgo III (% del IBC)",
        "Seguridad social",
        "Decreto 1772/1994",
        ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_IV_PCT": InfoParametro(
        "Cotizacion a ARL, nivel de riesgo IV (% del IBC)",
        "Seguridad social",
        "Decreto 1772/1994",
        ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_V_PCT": InfoParametro(
        "Cotizacion a ARL, nivel de riesgo V (% del IBC)",
        "Seguridad social",
        "Decreto 1772/1994",
        ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_1_PCT": InfoParametro(
        "Fondo de Solidaridad Pensional, tramo 1 (4-16 SMMLV, % del IBC)",
        "Seguridad social",
        "Ley 797/2003, art. 8",
        ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_2_PCT": InfoParametro(
        "Fondo de Solidaridad Pensional, tramo 2 (16-17 SMMLV, % del IBC)",
        "Seguridad social",
        "Ley 797/2003, art. 8",
        ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_3_PCT": InfoParametro(
        "Fondo de Solidaridad Pensional, tramo 3 (17-18 SMMLV, % del IBC)",
        "Seguridad social",
        "Ley 797/2003, art. 8",
        ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_4_PCT": InfoParametro(
        "Fondo de Solidaridad Pensional, tramo 4 (18-19 SMMLV, % del IBC)",
        "Seguridad social",
        "Ley 797/2003, art. 8",
        ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_5_PCT": InfoParametro(
        "Fondo de Solidaridad Pensional, tramo 5 (19-20 SMMLV, % del IBC)",
        "Seguridad social",
        "Ley 797/2003, art. 8",
        ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_6_PCT": InfoParametro(
        "Fondo de Solidaridad Pensional, tramo 6 (>20 SMMLV, % del IBC)",
        "Seguridad social",
        "Ley 797/2003, art. 8",
        ModoResolucion.ABIERTO,
    ),
    # Sprint 58: dato CRUDO del que se deriva IPC_INDICE_ACUMULADO --
    # indice = indice_anterior * (1 + variacion_anual / 100), ver
    # app/engine/indexation/historical_index.py::_construir_indice_ipc_acumulado.
    # NO se usa en ningun calculo de liquidacion (solo IPC_INDICE_ACUMULADO se
    # consulta desde get_ipc_for_date) -- existe solo para que
    # HistorialParametroDialog pueda mostrarla junto al indice ya calculado,
    # via CLAVE_CRUDA_DE (abajo). Sembrada por
    # scripts/migrate_ipc_variacion_anual.py.
    "IPC_VARIACION_ANUAL": InfoParametro(
        "Variacion porcentual anual del IPC (dato crudo, antes de acumular)",
        "Indicadores historicos",
        "PDF pagina 62",
        ModoResolucion.ANUAL_EXACTO,
    ),
}

# Sprint 58: clave calculada -> clave cruda de la que se deriva, para que
# HistorialParametroDialog pueda mostrar el dato crudo junto al calculado sin
# hardcodear "si clave == IPC_INDICE_ACUMULADO" en la UI. Mecanismo generico,
# extensible si en el futuro aparece otro parametro con formula -- confirmado
# con el usuario que por ahora solo IPC_INDICE_ACUMULADO aplica (de los otros
# 4 "indicadores historicos" -- SMLMV, UVT, IBC, USURA -- ninguno se deriva de
# otra clave, son tablas planas transcritas directo).
CLAVE_CRUDA_DE: dict[str, str] = {"IPC_INDICE_ACUMULADO": "IPC_VARIACION_ANUAL"}

# Revision final de integracion (Sprints 56-60): agregar_valor() exige
# 'valor > 0' para las claves normales (topes, tasas, plazos -- ver el bloque
# de abajo), pero IPC_VARIACION_ANUAL (Sprint 58) es la unica excepcion: es la
# variacion % anual CRUDA del IPC, un dato historico real que legitimamente
# puede ser 0% o negativa en un año de deflacion -- no es un error de captura.
# La migracion (scripts/migrate_ipc_variacion_anual.py) siembra los 59 valores
# historicos saltandose agregar_valor() (inserta directo por ORM), pero un
# usuario agregando un valor nuevo desde ParametroFormDialog si pasa por aqui.
# Set en vez de un campo nuevo en InfoParametro: hoy es un caso unico: si
# aparecen mas claves con la misma necesidad, generalizar a ese punto.
CLAVES_VALOR_PUEDE_SER_NO_POSITIVO: frozenset[str] = frozenset({"IPC_VARIACION_ANUAL"})


def _validar_clave(clave: str) -> InfoParametro:
    info = CATALOGO_PARAMETROS.get(clave)
    if info is None:
        raise ValueError(f"'{clave}' no es una clave de parametro reconocida.")
    return info


def _resolver_fila(clave: str, fecha: date) -> ParametroLegal | None:
    """Resuelve `clave` en SQL para una sola `fecha`. Existe una segunda
    implementacion del mismo criterio de filtrado/orden, `_resolver_entre_filas`
    (mas abajo en este archivo), que lo replica en memoria para resolver muchas
    fechas de una clave sin una consulta por fecha (Sprint 53, precargar_parametro).
    Si cambias el criterio de filtrado/orden aqui (los `if info.modo == ...` de
    abajo o el `order_by`), actualiza tambien `_resolver_entre_filas` --
    test_resolver_fila_y_resolver_entre_filas_dan_el_mismo_resultado en
    tests/services/test_parametro_service.py compara ambas contra los mismos
    datos y falla si se desincronizan."""
    info = _validar_clave(clave)
    session = session_module.get_session()
    try:
        query = session.query(ParametroLegal).filter(ParametroLegal.clave == clave)
        if info.modo == ModoResolucion.ANUAL_EXACTO:
            query = query.filter(ParametroLegal.vigente_desde == date(fecha.year, 1, 1))
        elif info.modo == ModoResolucion.TRAMO_CERRADO:
            query = query.filter(
                ParametroLegal.vigente_desde <= fecha,
                ParametroLegal.vigente_hasta.is_not(None),
                ParametroLegal.vigente_hasta >= fecha,
            )
        else:
            query = query.filter(ParametroLegal.vigente_desde <= fecha)
        return query.order_by(
            ParametroLegal.vigente_desde.desc(), ParametroLegal.creado_en.desc()
        ).first()
    finally:
        session.close()


def _resolver_entre_filas(
    info: InfoParametro, fecha: date, filas: list[ParametroLegal]
) -> ParametroLegal | None:
    """Aplica en memoria el mismo criterio de filtrado que `_resolver_fila` usa
    en SQL, sobre `filas` ya cargadas para una clave (ver `precargar_parametro`).
    Requiere que `filas` venga ordenada (vigente_desde desc, creado_en desc) --
    el mismo orden que retorna `historial()` -- para que el primer match sea
    equivalente a `.order_by(...).first()`."""
    if info.modo == ModoResolucion.ANUAL_EXACTO:
        objetivo = date(fecha.year, 1, 1)
        return next((fila for fila in filas if fila.vigente_desde == objetivo), None)
    if info.modo == ModoResolucion.TRAMO_CERRADO:
        return next(
            (
                fila
                for fila in filas
                if fila.vigente_desde <= fecha
                and fila.vigente_hasta is not None
                and fila.vigente_hasta >= fecha
            ),
            None,
        )
    return next((fila for fila in filas if fila.vigente_desde <= fecha), None)


_cache_liquidacion_activa: ContextVar[dict[tuple[str, date], Decimal] | None] = ContextVar(
    "_cache_liquidacion_activa", default=None
)

_filas_precargadas_activa: ContextVar[dict[str, list[ParametroLegal]] | None] = ContextVar(
    "_filas_precargadas_activa", default=None
)


@contextmanager
def cache_de_liquidacion():
    """Activa una cache en memoria de get_parametro, valida solo por la
    duracion de este bloque -- nunca persiste entre llamadas, asi que un
    agregar_valor hecho desde la GUI (app/views/configuracion.py) entre dos
    liquidaciones nunca puede servir un valor desactualizado. Evita reabrir
    una sesion SQLAlchemy por cada (clave, fecha) repetido dentro de la misma
    liquidacion (Sprint 25, hallazgos 2/3: HonorariosStrategy consulta
    HONORARIOS_TOTAL_PCT una vez por obligacion; historical_index consulta
    IPC_INDICE_ACUMULADO/SMLMV una vez por cuota mensual, pero la clave de
    resolucion es por año -- todas las cuotas de un mismo año colapsan a la
    misma entrada de cache). contextlib.contextmanager hereda de
    ContextDecorator, asi que este mismo objeto tambien sirve como decorador
    (@cache_de_liquidacion()) -- cada invocacion decorada abre su propio
    bloque nuevo, nunca comparte cache con otra llamada.

    Tambien habilita el espacio para `precargar_parametro` (Sprint 53): la
    cache de arriba solo ayuda cuando se repite la MISMA (clave, fecha) exacta
    -- no sirve cuando N llamadas comparten clave pero cada una tiene una
    fecha distinta (ej. N obligaciones con N fechas_origen distintas). Ese
    caso requiere precargar_parametro(clave), que trae todas las filas de la
    clave en una sola consulta y las deja aqui para que get_parametro resuelva
    cualquier fecha en memoria."""
    token = _cache_liquidacion_activa.set({})
    token_precarga = _filas_precargadas_activa.set({})
    try:
        yield
    finally:
        _cache_liquidacion_activa.reset(token)
        _filas_precargadas_activa.reset(token_precarga)


def precargar_parametro(clave: str) -> None:
    """Trae TODAS las filas de `clave` en una sola consulta (mismo query que
    `historial()`) y las deja disponibles para que `get_parametro` resuelva
    cualquier fecha de esa clave sin una consulta nueva por fecha (Sprint 53,
    hallazgo 1 del Dashboard: N obligaciones no pagadas con N fechas_origen
    distintas resolviendo PRESCRIPCION_EJECUTIVA_MESES abrian N sesiones
    SQLAlchemy, porque la cache por (clave, fecha) de `cache_de_liquidacion`
    solo colapsa fechas EXACTAMENTE iguales -- aqui se resuelve cualquier
    fecha en memoria contra las filas ya cargadas, vía `_resolver_entre_filas`,
    con el mismo criterio de filtrado/orden que `_resolver_fila` usa en SQL).

    Requiere un bloque `cache_de_liquidacion()` activo -- sin uno, no hay
    donde guardar la precarga y esta funcion no hace nada: `get_parametro`
    simplemente sigue consultando la base de datos por fecha, el
    comportamiento de siempre.

    Trae TODAS las filas de `clave` sin limite -- para claves de crecimiento
    acotado (ej. plazos de prescripcion, topes legales, que agregan filas
    nuevas rara vez) el costo es despreciable, pero para series historicas que
    crecen cada año (ej. SMLMV, IBC_CONSUMO_ORDINARIO) conviene medir el costo
    antes de precargarlas en un bucle grande."""
    _validar_clave(clave)
    filas_precargadas = _filas_precargadas_activa.get()
    if filas_precargadas is None:
        return
    filas_precargadas[clave] = historial(clave)


def get_parametro(clave: str, fecha: date) -> Decimal:
    """Resuelve el valor de `clave` vigente en `fecha`, segun el modo_resolucion
    declarado en CATALOGO_PARAMETROS (ver Adenda de diseno de la spec). Si hay
    una cache de liquidacion activa (cache_de_liquidacion), reutiliza el valor
    ya resuelto para el mismo (clave, fecha) en vez de abrir una sesion
    SQLAlchemy nueva. Si ademas `clave` fue precargada (precargar_parametro),
    resuelve `fecha` en memoria contra esas filas en vez de consultar la base
    de datos, sin importar si `fecha` ya se habia visto antes."""
    cache = _cache_liquidacion_activa.get()
    clave_cache = (clave, fecha)
    if cache is not None and clave_cache in cache:
        return cache[clave_cache]

    filas_precargadas = _filas_precargadas_activa.get()
    if filas_precargadas is not None and clave in filas_precargadas:
        info = _validar_clave(clave)
        fila = _resolver_entre_filas(info, fecha, filas_precargadas[clave])
    else:
        fila = _resolver_fila(clave, fecha)

    if fila is None:
        info = _validar_clave(clave)
        raise ParametroNoDisponibleError(
            f"No hay valor configurado para '{info.descripcion}' (clave '{clave}') "
            f"en la fecha {fecha}."
        )
    if cache is not None:
        cache[clave_cache] = fila.valor
    return fila.valor


def _validar_y_preparar(
    clave: str,
    valor: Decimal,
    vigente_desde: date,
    areas_derecho: list[AreaDerecho],
    unidad: str,
    vigente_hasta: date | None,
    session,
    excluir_id: int | None = None,
) -> tuple[InfoParametro, str, str]:
    """Validacion compartida por `agregar_valor` y `editar_valor`: reglas de
    modo/vigente_hasta, valor positivo, unidad no vacia y solapamiento de
    tramos TRAMO_CERRADO. `excluir_id` (usado solo por `editar_valor`) excluye
    la propia fila de la consulta de solapamiento -- si no se excluyera, una
    fila TRAMO_CERRADO siempre "se solaparia consigo misma" al editarla sin
    cambiar sus fechas. Retorna (info, areas_derecho_json, unidad_normalizada)
    listos para construir/actualizar la fila."""
    info = _validar_clave(clave)
    if info.modo == ModoResolucion.TRAMO_CERRADO and vigente_hasta is None:
        raise ValueError(f"'{clave}' requiere 'vigente_hasta' (modo TRAMO_CERRADO).")
    if info.modo != ModoResolucion.TRAMO_CERRADO and vigente_hasta is not None:
        raise ValueError(f"'{clave}' no admite 'vigente_hasta' (modo {info.modo.value}).")
    if valor <= Decimal("0") and clave not in CLAVES_VALOR_PUEDE_SER_NO_POSITIVO:
        raise ValueError("El valor debe ser positivo.")
    if vigente_hasta is not None and vigente_hasta < vigente_desde:
        raise ValueError("'vigente_hasta' no puede ser anterior a 'vigente_desde'.")
    areas_derecho_json = serializar_areas(areas_derecho)
    unidad = unidad.strip()
    if not unidad:
        raise ValueError("La unidad es obligatoria.")

    if info.modo == ModoResolucion.TRAMO_CERRADO:
        query = session.query(ParametroLegal).filter(
            ParametroLegal.clave == clave,
            ParametroLegal.vigente_desde <= vigente_hasta,
            ParametroLegal.vigente_hasta >= vigente_desde,
        )
        if excluir_id is not None:
            query = query.filter(ParametroLegal.id != excluir_id)
        tramo_solapado = query.first()
        if tramo_solapado is not None:
            raise ValueError(
                f"El tramo {vigente_desde} a {vigente_hasta} se solapa con un tramo "
                f"existente de '{clave}' ({tramo_solapado.vigente_desde} a "
                f"{tramo_solapado.vigente_hasta})."
            )
    return info, areas_derecho_json, unidad


def agregar_valor(
    clave: str,
    valor: Decimal,
    vigente_desde: date,
    usuario: str,
    areas_derecho: list[AreaDerecho],
    unidad: str,
    motivo: str | None = None,
    vigente_hasta: date | None = None,
) -> ParametroLegal:
    """Inserta una fila nueva creada por un usuario (creado_por_sistema=False
    siempre, sin importar lo que diga `usuario` -- ver docstring del modulo).
    Usada por la GUI (app/views/configuracion.py).

    areas_derecho/unidad (Sprint 57): obligatorias para toda fila creada por
    esta funcion -- se guardan por fila (no como metadato fijo en Python). El
    modelo las deja nullable a nivel de columna SQLite (ver database/models.py)
    precisamente para que esa obligatoriedad la exija esta funcion, no un
    CHECK/NOT NULL de la base de datos.

    `valor` debe ser positivo salvo para las claves listadas en
    CLAVES_VALOR_PUEDE_SER_NO_POSITIVO (hoy solo IPC_VARIACION_ANUAL, que
    puede ser 0 o negativa en un año de deflacion -- ver el comentario junto a
    esa constante)."""
    session = session_module.get_session()
    try:
        info, areas_derecho_json, unidad = _validar_y_preparar(
            clave, valor, vigente_desde, areas_derecho, unidad, vigente_hasta, session
        )
        fila = ParametroLegal(
            clave=clave,
            valor=valor,
            vigente_desde=vigente_desde,
            vigente_hasta=vigente_hasta,
            usuario=usuario,
            motivo=motivo,
            creado_en=datetime.now(),
            areas_derecho=areas_derecho_json,
            unidad=unidad,
            creado_por_sistema=False,
        )
        session.add(fila)
        session.commit()
        session.refresh(fila)
        return fila
    finally:
        session.close()


def editar_valor(
    parametro_id: int,
    valor: Decimal,
    vigente_desde: date,
    usuario: str,
    areas_derecho: list[AreaDerecho],
    unidad: str,
    motivo: str | None = None,
    vigente_hasta: date | None = None,
) -> ParametroLegal:
    """Actualiza en el sitio una fila existente creada por un usuario --
    excepcion deliberada al append-only historico (ver docstring del modulo),
    acotada a filas con creado_por_sistema=False. La clave (`clave`) NO es
    editable -- no se recibe como parametro, se conserva la de la fila
    existente; cambiar de clave equivaldria a borrar una fila y crear otra
    distinta, decision tomada con el usuario al diseñar este sprint."""
    session = session_module.get_session()
    try:
        fila = session.get(ParametroLegal, parametro_id)
        if fila is None:
            raise ValueError(f"No existe un parametro con id {parametro_id}.")
        if fila.creado_por_sistema:
            raise ValueError("No se puede editar un parametro creado por el sistema.")
        _info, areas_derecho_json, unidad = _validar_y_preparar(
            fila.clave,
            valor,
            vigente_desde,
            areas_derecho,
            unidad,
            vigente_hasta,
            session,
            excluir_id=parametro_id,
        )
        fila.valor = valor
        fila.vigente_desde = vigente_desde
        fila.vigente_hasta = vigente_hasta
        fila.usuario = usuario
        fila.motivo = motivo
        fila.areas_derecho = areas_derecho_json
        fila.unidad = unidad
        session.commit()
        session.refresh(fila)
        return fila
    finally:
        session.close()


def eliminar_valor(parametro_id: int) -> None:
    """Borra definitivamente una fila creada por un usuario -- excepcion
    deliberada al append-only historico, acotada a creado_por_sistema=False.
    Si `parametro_id` ya no existe (doble clic sobre una fila ya eliminada),
    no hace nada -- mismo criterio defensivo que
    ExpedienteDetallePage._eliminar_obligacion (Sprint 60, hotfix de
    produccion 2026-08-12)."""
    session = session_module.get_session()
    try:
        fila = session.get(ParametroLegal, parametro_id)
        if fila is None:
            return
        if fila.creado_por_sistema:
            raise ValueError("No se puede eliminar un parametro creado por el sistema.")
        session.delete(fila)
        session.commit()
    finally:
        session.close()


def historial(clave: str) -> list[ParametroLegal]:
    """Todas las filas de una clave, mas reciente primero -- alimenta la vista
    de historial de la GUI."""
    _validar_clave(clave)
    session = session_module.get_session()
    try:
        return (
            session.query(ParametroLegal)
            .filter(ParametroLegal.clave == clave)
            .order_by(ParametroLegal.vigente_desde.desc(), ParametroLegal.creado_en.desc())
            .all()
        )
    finally:
        session.close()


def vigencia_hasta_mostrar(fila: ParametroLegal, info: InfoParametro) -> str:
    """Texto de PRESENTACION para la columna "Vigente hasta" de la GUI
    (ParametrosView.tabla, HistorialParametroDialog.tabla) -- Sprint 58.
    Regla de presentacion pura: no modifica `fila` ni ningun dato guardado, y
    no participa de get_parametro()/_resolver_fila() (el calculo real de
    liquidacion sigue exactamente igual).

    - Si `fila.vigente_hasta` ya esta guardado (modo TRAMO_CERRADO), se
      muestra tal cual, en ISO.
    - Si el modo de la clave es ANUAL_EXACTO y no hay `vigente_hasta` (el
      gobierno fija un valor nuevo cada año -- SMLMV, IPC_INDICE_ACUMULADO,
      UVT -- pero la fila nunca guarda una fecha de cierre explicita, solo
      `vigente_desde`), se calcula "31 de diciembre del año de
      vigente_desde": el mismo año calendario que ya usa
      _resolver_fila/_resolver_entre_filas para resolver ese modo
      (vigente_desde == date(fecha.year, 1, 1)), asi que el texto nunca
      contradice lo que get_parametro() realmente resuelve.
    - En cualquier otro caso (modo ABIERTO -- ej. USURA_MULTIPLICADOR, que
      estructuralmente no tiene fecha de fin -- sin `vigente_hasta`), se
      muestra "Indefinido" en vez de dejar la celda vacia."""
    if fila.vigente_hasta is not None:
        return fila.vigente_hasta.isoformat()
    if info.modo == ModoResolucion.ANUAL_EXACTO:
        return f"{date(fila.vigente_desde.year, 12, 31).isoformat()} (calculado)"
    return "Indefinido"


def valor_vigente_hoy(clave: str) -> ParametroLegal | None:
    """Fila resuelta para la fecha de hoy -- alimenta la tabla resumen de la GUI."""
    return _resolver_fila(clave, date.today())


def ultimo_anio_disponible(clave: str) -> int:
    """Maximo ano con datos cargados para una clave ANUAL_EXACTO. Usado por
    get_ipc_interpolado_for_date (historical_index.py) para su aproximacion ya
    documentada: fechas posteriores al ultimo ano disponible usan el indice de
    ese ultimo ano (Sprint 8, decision 3)."""
    info = _validar_clave(clave)
    if info.modo != ModoResolucion.ANUAL_EXACTO:
        raise ValueError(f"'{clave}' no es una serie anual (modo {info.modo.value}).")
    session = session_module.get_session()
    try:
        fila = (
            session.query(ParametroLegal)
            .filter(ParametroLegal.clave == clave)
            .order_by(ParametroLegal.vigente_desde.desc())
            .first()
        )
        if fila is None:
            raise ParametroNoDisponibleError(f"No hay ningun valor cargado para '{clave}'.")
        return fila.vigente_desde.year
    finally:
        session.close()
