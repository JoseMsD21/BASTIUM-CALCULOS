"""
Servicio de parametros legales versionados: valores/tasas/topes/plazos que
antes vivian como constantes Python sueltas (usura, cuota litis, prescripcion,
E.T. 635, tasa civil legal) o como series versionadas solo en codigo (SMLMV,
IPC, IBC/usura, ver historical_index.py) pasan a vivir en la tabla
parametros_legales, editable desde la GUI (app/views/configuracion.py) sin
tocar Python ni redesplegar.

Ver docs/superpowers/specs/2026-07-20-parametros-legales-versionados-design.md
para el diseno completo, en particular la Adenda de modos de resolucion.

Tabla append-only: nunca se edita ni se borra una fila existente. Una
correccion o un cambio de vigencia se hace agregando una fila nueva -- las
columnas usuario/motivo/creado_en de cada fila son, en conjunto, la bitacora
completa (no depende de AuditLog, que exige un expediente_id).
"""

from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import NamedTuple

import database.session as session_module
from app.core.exceptions import ParametroNoDisponibleError
from database.models import ParametroLegal


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
        "Multiplicador del tope de usura sobre el IBC", "Topes legales",
        "Ley 45/1990, art. 72", ModoResolucion.ABIERTO,
    ),
    "HONORARIOS_TOTAL_PCT": InfoParametro(
        "Tope de honorarios fijos + cuota litis (% del beneficio obtenido)", "Topes legales",
        "Art. 35 Num. 4 Ley 1123/2007", ModoResolucion.ABIERTO,
    ),
    "ET635_PUNTOS_DESCUENTO": InfoParametro(
        "Puntos que se restan a la usura vigente para el interes moratorio tributario",
        "Topes legales", "Estatuto Tributario, art. 635", ModoResolucion.ABIERTO,
    ),
    "CIVIL_ANNUAL_RATE": InfoParametro(
        "Tasa de interes civil legal anual", "Topes legales",
        "Art. 1617 Codigo Civil", ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_EJECUTIVA_MESES": InfoParametro(
        "Plazo de prescripcion de la accion ejecutiva (meses)", "Plazos de prescripcion y caducidad",
        "PDF paginas 16/19, 42, 43, 45", ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_ORDINARIA_MESES": InfoParametro(
        "Plazo de prescripcion de la accion ordinaria (meses)", "Plazos de prescripcion y caducidad",
        "Art. 2536 Codigo Civil", ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_HONORARIOS_MESES": InfoParametro(
        "Plazo de prescripcion de honorarios profesionales (meses)", "Plazos de prescripcion y caducidad",
        "PDF pagina 35", ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_CAMBIARIA_DIRECTA_MESES": InfoParametro(
        "Plazo de prescripcion cambiaria directa (meses)", "Plazos de prescripcion y caducidad",
        "Art. 789 C.Co.", ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES": InfoParametro(
        "Plazo de prescripcion cambiaria de regreso del tenedor (meses)",
        "Plazos de prescripcion y caducidad", "Art. 790 C.Co.", ModoResolucion.ABIERTO,
    ),
    "PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES": InfoParametro(
        "Plazo de prescripcion cambiaria entre obligados de regreso (meses)",
        "Plazos de prescripcion y caducidad", "Art. 791 C.Co.", ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_IMPUGNACION_INEFICACIA_SOCIETARIA_MESES": InfoParametro(
        "Plazo de caducidad de impugnacion de ineficacia societaria (meses)",
        "Plazos de prescripcion y caducidad", "PDF pagina 40", ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_CHEQUES_MESES": InfoParametro(
        "Plazo de caducidad de la accion cambiaria del cheque (meses)",
        "Plazos de prescripcion y caducidad",
        "Respuesta del despacho, Preguntas-Para-Abogado.md Sprint 7 (27/07/2026)", ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_ENRIQUECIMIENTO_SIN_CAUSA_MESES": InfoParametro(
        "Plazo de caducidad de la accion de enriquecimiento sin causa (meses)",
        "Plazos de prescripcion y caducidad",
        "Respuesta del despacho, Preguntas-Para-Abogado.md Sprint 7 (27/07/2026)", ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_TRANSPORTE_MESES": InfoParametro(
        "Plazo de caducidad de la accion de transporte (meses)",
        "Plazos de prescripcion y caducidad",
        "Respuesta del despacho, Preguntas-Para-Abogado.md Sprint 7 (27/07/2026)", ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_SEGURO_ORDINARIA_MESES": InfoParametro(
        "Plazo de prescripcion ordinaria del contrato de seguro (meses)",
        "Plazos de prescripcion y caducidad",
        "Respuesta del despacho, Preguntas-Para-Abogado.md Sprint 7 (27/07/2026)", ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_SEGURO_EXTRAORDINARIA_MESES": InfoParametro(
        "Plazo de prescripcion extraordinaria del contrato de seguro (meses)",
        "Plazos de prescripcion y caducidad",
        "Respuesta del despacho, Preguntas-Para-Abogado.md Sprint 7 (27/07/2026)", ModoResolucion.ABIERTO,
    ),
    "CADUCIDAD_IMPUGNACION_ACTAS_SOCIALES_MESES": InfoParametro(
        "Plazo de caducidad de impugnacion de actas sociales (meses)",
        "Plazos de prescripcion y caducidad",
        "Respuesta del despacho, Preguntas-Para-Abogado.md Sprint 7 (27/07/2026)", ModoResolucion.ABIERTO,
    ),
    "SMLMV": InfoParametro(
        "Salario Minimo Legal Mensual Vigente", "Indicadores historicos",
        "PDF paginas 55-57", ModoResolucion.ANUAL_EXACTO,
    ),
    "IPC_INDICE_ACUMULADO": InfoParametro(
        "Indice de Precios al Consumidor acumulado (cierre de año, base 100 en 1966)",
        "Indicadores historicos", "PDF pagina 62", ModoResolucion.ANUAL_EXACTO,
    ),
    "IBC_CONSUMO_ORDINARIO": InfoParametro(
        "Interes Bancario Corriente, linea Consumo y Ordinario (% anual)",
        "Indicadores historicos", "PDF paginas 58-61 (SFC)", ModoResolucion.TRAMO_CERRADO,
    ),
    "USURA_CONSUMO_ORDINARIO": InfoParametro(
        "Tasa de usura, linea Consumo y Ordinario (% anual)",
        "Indicadores historicos", "PDF paginas 58-61 (SFC)", ModoResolucion.TRAMO_CERRADO,
    ),
    "UVT": InfoParametro(
        "Unidad de Valor Tributario (UVT)", "Indicadores historicos",
        "DIAN, resolucion anual (Ley 1111 de 2006)", ModoResolucion.ANUAL_EXACTO,
    ),
    "EXTEMPORANEIDAD_PCT_MENSUAL": InfoParametro(
        "Sanción por extemporaneidad, porcentaje mensual del impuesto a cargo", "Topes legales",
        "Estatuto Tributario (PDF pág. 39)", ModoResolucion.ABIERTO,
    ),
    "INEXACTITUD_PCT": InfoParametro(
        "Sanción por inexactitud, porcentaje de la diferencia (sin agravante)", "Topes legales",
        "Estatuto Tributario (PDF pág. 39)", ModoResolucion.ABIERTO,
    ),
    "INEXACTITUD_AGRAVADA_PCT": InfoParametro(
        "Sanción por inexactitud, porcentaje agravado (omisión de activos/pasivos inexistentes)",
        "Topes legales", "Estatuto Tributario (PDF pág. 39)", ModoResolucion.ABIERTO,
    ),
    "ERROR_ARITMETICO_PCT": InfoParametro(
        "Sanción por error aritmético, porcentaje de la diferencia generada", "Topes legales",
        "Estatuto Tributario (PDF pág. 39)", ModoResolucion.ABIERTO,
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
        "Cotizacion total a pension (% del IBC, empleador + trabajador)", "Seguridad social",
        "Ley 100/1993, art. 20", ModoResolucion.ABIERTO,
    ),
    "SS_SALUD_PCT": InfoParametro(
        "Cotizacion total a salud (% del IBC, empleador + trabajador)", "Seguridad social",
        "Ley 100/1993, art. 204", ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_I_PCT": InfoParametro(
        "Cotizacion a ARL, nivel de riesgo I (% del IBC)", "Seguridad social",
        "Decreto 1772/1994", ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_II_PCT": InfoParametro(
        "Cotizacion a ARL, nivel de riesgo II (% del IBC)", "Seguridad social",
        "Decreto 1772/1994", ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_III_PCT": InfoParametro(
        "Cotizacion a ARL, nivel de riesgo III (% del IBC)", "Seguridad social",
        "Decreto 1772/1994", ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_IV_PCT": InfoParametro(
        "Cotizacion a ARL, nivel de riesgo IV (% del IBC)", "Seguridad social",
        "Decreto 1772/1994", ModoResolucion.ABIERTO,
    ),
    "SS_ARL_NIVEL_V_PCT": InfoParametro(
        "Cotizacion a ARL, nivel de riesgo V (% del IBC)", "Seguridad social",
        "Decreto 1772/1994", ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_1_PCT": InfoParametro(
        "Fondo de Solidaridad Pensional, tramo 1 (4-16 SMMLV, % del IBC)",
        "Seguridad social", "Ley 797/2003, art. 8", ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_2_PCT": InfoParametro(
        "Fondo de Solidaridad Pensional, tramo 2 (16-17 SMMLV, % del IBC)",
        "Seguridad social", "Ley 797/2003, art. 8", ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_3_PCT": InfoParametro(
        "Fondo de Solidaridad Pensional, tramo 3 (17-18 SMMLV, % del IBC)",
        "Seguridad social", "Ley 797/2003, art. 8", ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_4_PCT": InfoParametro(
        "Fondo de Solidaridad Pensional, tramo 4 (18-19 SMMLV, % del IBC)",
        "Seguridad social", "Ley 797/2003, art. 8", ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_5_PCT": InfoParametro(
        "Fondo de Solidaridad Pensional, tramo 5 (19-20 SMMLV, % del IBC)",
        "Seguridad social", "Ley 797/2003, art. 8", ModoResolucion.ABIERTO,
    ),
    "SS_FSP_TRAMO_6_PCT": InfoParametro(
        "Fondo de Solidaridad Pensional, tramo 6 (>20 SMMLV, % del IBC)",
        "Seguridad social", "Ley 797/2003, art. 8", ModoResolucion.ABIERTO,
    ),
}


def _validar_clave(clave: str) -> InfoParametro:
    info = CATALOGO_PARAMETROS.get(clave)
    if info is None:
        raise ValueError(f"'{clave}' no es una clave de parametro reconocida.")
    return info


def _resolver_fila(clave: str, fecha: date) -> ParametroLegal | None:
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


def get_parametro(clave: str, fecha: date) -> Decimal:
    """Resuelve el valor de `clave` vigente en `fecha`, segun el modo_resolucion
    declarado en CATALOGO_PARAMETROS (ver Adenda de diseno de la spec)."""
    fila = _resolver_fila(clave, fecha)
    if fila is None:
        info = _validar_clave(clave)
        raise ParametroNoDisponibleError(
            f"No hay valor configurado para '{info.descripcion}' (clave '{clave}') "
            f"en la fecha {fecha}."
        )
    return fila.valor


def agregar_valor(
    clave: str,
    valor: Decimal,
    vigente_desde: date,
    usuario: str,
    motivo: str | None = None,
    vigente_hasta: date | None = None,
) -> ParametroLegal:
    """Inserta una fila nueva (append-only: nunca modifica ni borra filas
    existentes). Usada por la GUI (app/views/configuracion.py)."""
    info = _validar_clave(clave)
    if info.modo == ModoResolucion.TRAMO_CERRADO and vigente_hasta is None:
        raise ValueError(f"'{clave}' requiere 'vigente_hasta' (modo TRAMO_CERRADO).")
    if info.modo != ModoResolucion.TRAMO_CERRADO and vigente_hasta is not None:
        raise ValueError(f"'{clave}' no admite 'vigente_hasta' (modo {info.modo.value}).")

    session = session_module.get_session()
    try:
        fila = ParametroLegal(
            clave=clave,
            valor=valor,
            vigente_desde=vigente_desde,
            vigente_hasta=vigente_hasta,
            usuario=usuario,
            motivo=motivo,
            creado_en=datetime.now(),
        )
        session.add(fila)
        session.commit()
        session.refresh(fila)
        return fila
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
