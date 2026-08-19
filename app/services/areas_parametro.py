"""Area(s) del derecho y unidad de medida por cada clave de
CATALOGO_PARAMETROS (Sprint 57). Centraliza en un solo lugar:

- La (de)serializacion JSON de `ParametroLegal.areas_derecho` (lista de
  codigos `AreaDerecho`), usada tanto por `parametro_service.agregar_valor()`
  como por `scripts/migrate_parametros_area_unidad.py` como por
  `app/views/configuracion.py::ParametroFormDialog`, para no repetir
  `json.dumps`/`json.loads` en los tres lugares.
- `AREA_UNIDAD_POR_CLAVE`, el diccionario clave -> (areas, unidad) tal como
  se investigo leyendo el codigo real de que `AreaStrategy` usa cada clave y
  se reviso con el usuario -- ver
  docs/superpowers/specs/2026-08-11-parametros-ux-dialogos-crud-design.md,
  seccion "Sprint 57 -> Tabla de area propuesta por clave". NO se vuelve a
  derivar aqui: se copia tal cual esa tabla ya aprobada. Import de un solo
  lugar (no de scripts/, que es un paquete de scripts ejecutables, no una
  libreria) para que tanto la migracion (Task 4) como la UI (Task 5) lo
  importen sin duplicarlo.

Las claves de prescripcion/caducidad no-ejecutiva (mas CIVIL_ANNUAL_RATE) que
estuvieron "sin wiring a produccion" quedaron conectadas en el Sprint 61 via
`opciones_tipo_accion_proceso_por_area()` (el combo "Tipo de accion/proceso"
de `ObligacionFormDialog`) y el fallback automatico de `CivilFamiliaStrategy`
para CIVIL_ANNUAL_RATE -- ver docs/superpowers/specs/
2026-08-14-sprint61-wiring-parametros-prescripcion-design.md.
CADUCIDAD_ENRIQUECIMIENTO_SIN_CAUSA_MESES recibe deliberadamente 2 areas
(Civil/Familia y Comercial), por ser doctrina aplicable en las dos sin
evidencia de codigo que incline a una sola."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from database.models import AreaDerecho

if TYPE_CHECKING:
    from app.engine.temporal.prescripcion import TipoAccion

_CF = AreaDerecho.CIVIL_FAMILIA
_CO = AreaDerecho.COMERCIAL
_LA = AreaDerecho.LABORAL
_SA = AreaDerecho.SANCIONATORIO
_HO = AreaDerecho.HONORARIOS
_TR = AreaDerecho.TRIBUTARIO

_LAS_6_AREAS = [_CF, _CO, _LA, _SA, _HO, _TR]

# clave -> (areas_derecho, unidad). Ver docstring del modulo para la fuente.
AREA_UNIDAD_POR_CLAVE: dict[str, tuple[list[AreaDerecho], str]] = {
    # --- Grupo con area confirmada por codigo en ejecucion ---
    "USURA_MULTIPLICADOR": ([_CO], "veces"),
    "HONORARIOS_TOTAL_PCT": ([_HO], "%"),
    "ET635_PUNTOS_DESCUENTO": ([_TR], "puntos"),
    "PRESCRIPCION_EJECUTIVA_MESES": (_LAS_6_AREAS, "meses"),
    "SMLMV": ([_CF, _LA, _SA, _CO, _HO], "COP"),
    "IPC_INDICE_ACUMULADO": ([_CF, _TR], "índice"),
    "IBC_CONSUMO_ORDINARIO": ([_TR, _LA], "%"),
    "USURA_CONSUMO_ORDINARIO": ([_TR, _LA], "%"),
    "UVT": ([_TR, _SA], "COP"),
    "EXTEMPORANEIDAD_PCT_MENSUAL": ([_TR], "%"),
    "INEXACTITUD_PCT": ([_TR], "%"),
    "INEXACTITUD_AGRAVADA_PCT": ([_TR], "%"),
    "ERROR_ARITMETICO_PCT": ([_TR], "%"),
    "SS_PENSION_PCT": ([_LA], "%"),
    "SS_SALUD_PCT": ([_LA], "%"),
    "SS_ARL_NIVEL_I_PCT": ([_LA], "%"),
    "SS_ARL_NIVEL_II_PCT": ([_LA], "%"),
    "SS_ARL_NIVEL_III_PCT": ([_LA], "%"),
    "SS_ARL_NIVEL_IV_PCT": ([_LA], "%"),
    "SS_ARL_NIVEL_V_PCT": ([_LA], "%"),
    "SS_FSP_TRAMO_1_PCT": ([_LA], "%"),
    "SS_FSP_TRAMO_2_PCT": ([_LA], "%"),
    "SS_FSP_TRAMO_3_PCT": ([_LA], "%"),
    "SS_FSP_TRAMO_4_PCT": ([_LA], "%"),
    "SS_FSP_TRAMO_5_PCT": ([_LA], "%"),
    "SS_FSP_TRAMO_6_PCT": ([_LA], "%"),
    # --- Grupo sin wiring a produccion todavia (Sprint 61) ---
    "CIVIL_ANNUAL_RATE": ([_CF], "%"),
    "PRESCRIPCION_ORDINARIA_MESES": ([_CF], "meses"),
    "PRESCRIPCION_HONORARIOS_MESES": ([_HO], "meses"),
    "PRESCRIPCION_CAMBIARIA_DIRECTA_MESES": ([_CO], "meses"),
    "PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES": ([_CO], "meses"),
    "PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES": ([_CO], "meses"),
    "CADUCIDAD_IMPUGNACION_INEFICACIA_SOCIETARIA_MESES": ([_CO], "meses"),
    "CADUCIDAD_CHEQUES_MESES": ([_CO], "meses"),
    "CADUCIDAD_TRANSPORTE_MESES": ([_CO], "meses"),
    "CADUCIDAD_SEGURO_ORDINARIA_MESES": ([_CO], "meses"),
    "CADUCIDAD_SEGURO_EXTRAORDINARIA_MESES": ([_CO], "meses"),
    "CADUCIDAD_IMPUGNACION_ACTAS_SOCIALES_MESES": ([_CO], "meses"),
    "CADUCIDAD_ENRIQUECIMIENTO_SIN_CAUSA_MESES": ([_CF, _CO], "meses"),
    # Sprint 58: mismas areas que IPC_INDICE_ACUMULADO -- es el dato crudo del
    # que ese se deriva (ver CLAVE_CRUDA_DE en parametro_service.py).
    "IPC_VARIACION_ANUAL": ([_CF, _TR], "%"),
}


def serializar_areas(areas: list[AreaDerecho]) -> str:
    if not areas:
        raise ValueError("Debe seleccionarse al menos un area del derecho.")
    return json.dumps([area.value for area in areas])


def deserializar_areas(texto: str) -> list[AreaDerecho]:
    return [AreaDerecho(codigo) for codigo in json.loads(texto)]


_ETIQUETA_CADUCIDAD: dict[str, str] = {
    "IMPUGNACION_INEFICACIA_SOCIETARIA": "Caducidad: impugnación de ineficacia societaria",
    "CHEQUES": "Caducidad: cheques",
    "ENRIQUECIMIENTO_SIN_CAUSA": "Caducidad: enriquecimiento sin causa",
    "TRANSPORTE": "Caducidad: transporte",
    "SEGURO_ORDINARIA": "Caducidad: seguro (ordinaria)",
    "SEGURO_EXTRAORDINARIA": "Caducidad: seguro (extraordinaria)",
    "IMPUGNACION_ACTAS_SOCIALES": "Caducidad: impugnación de actas sociales",
}


def _etiqueta_tipo_accion(tipo_accion: TipoAccion) -> str:
    from app.engine.temporal.prescripcion import TipoAccion as _TipoAccion

    return {
        _TipoAccion.EJECUTIVA: "Prescripción ejecutiva",
        _TipoAccion.ORDINARIA: "Prescripción ordinaria",
        _TipoAccion.HONORARIOS_PROFESIONALES: "Prescripción de honorarios profesionales",
        _TipoAccion.CAMBIARIA_DIRECTA: "Prescripción cambiaria directa",
        _TipoAccion.CAMBIARIA_REGRESO_TENEDOR: "Prescripción cambiaria de regreso (tenedor)",
        _TipoAccion.CAMBIARIA_REGRESO_ENTRE_OBLIGADOS: (
            "Prescripción cambiaria de regreso (entre obligados)"
        ),
    }[tipo_accion]


def opciones_tipo_accion_proceso_por_area(area: AreaDerecho) -> list[tuple[str, str]]:
    """(valor_a_guardar, etiqueta) para el combo "Tipo de acción/proceso" del
    formulario de Obligacion (Sprint 61), filtrado a lo relevante para `area`
    reutilizando el mapeo ya aprobado AREA_UNIDAD_POR_CLAVE (Sprint 57).
    `valor_a_guardar` es TipoAccion.value (prescripcion, minuscula) o la clave
    cruda de PLAZOS_CADUCIDAD_MESES_CONOCIDOS (caducidad, mayuscula) -- no hay
    colision posible entre los dos catalogos.

    Import perezoso de app.engine.temporal.prescripcion (no al inicio del
    modulo): prescripcion.py importa app.services.parametro_service, que a su
    vez importa serializar_areas de este mismo modulo -- un import a nivel de
    modulo aqui crearia un ciclo (areas_parametro -> prescripcion ->
    parametro_service -> areas_parametro)."""
    from app.engine.temporal.prescripcion import (
        CLAVE_POR_TIPO_ACCION,
        PLAZOS_CADUCIDAD_MESES_CONOCIDOS,
    )

    opciones: list[tuple[str, str]] = []
    for tipo_accion, clave in CLAVE_POR_TIPO_ACCION.items():
        areas_clave, _ = AREA_UNIDAD_POR_CLAVE.get(clave, ([], ""))
        if area in areas_clave:
            opciones.append((tipo_accion.value, _etiqueta_tipo_accion(tipo_accion)))
    for clave_caducidad in PLAZOS_CADUCIDAD_MESES_CONOCIDOS:
        clave_parametro = f"CADUCIDAD_{clave_caducidad}_MESES"
        areas_clave, _ = AREA_UNIDAD_POR_CLAVE.get(clave_parametro, ([], ""))
        if area in areas_clave:
            opciones.append((clave_caducidad, _ETIQUETA_CADUCIDAD[clave_caducidad]))
    return opciones
