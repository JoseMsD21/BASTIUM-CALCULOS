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

Las 18 claves marcadas en la spec como "sin wiring a produccion todavia"
reciben la misma mejor-propuesta por nombre/articulo legal que el resto: si
la inferencia resulta incorrecta se corrige cuando esa clave se conecte a una
pantalla real (Sprint 61, placeholder). CADUCIDAD_ENRIQUECIMIENTO_SIN_CAUSA_MESES
recibe deliberadamente 2 areas (Civil/Familia y Comercial), por ser doctrina
aplicable en las dos sin evidencia de codigo que incline a una sola."""

from __future__ import annotations

import json

from database.models import AreaDerecho

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
    # Sprint 43: IPC_INDICE_ACUMULADO ahora tambien alimenta la indexacion IPC de
    # Honorarios (incondicional), Laboral/Sancionatorio (condicional) y Comercial
    # (modo b, pacto expreso) -- ver app/services/area_strategy.py. Tributario ya
    # estaba en la lista (Art. 867-1 E.T., Sprint 15). Las 6 areas usan la clave
    # ahora, de ahi _LAS_6_AREAS en vez de enumerarlas a mano.
    "IPC_INDICE_ACUMULADO": (_LAS_6_AREAS, "índice"),
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
    # Sprint 43: CIVIL_ANNUAL_RATE ahora tambien alimenta la tasa civil fija del
    # segundo termino de la formula de indexacion IPC de Honorarios y el modo (b)
    # de Comercial (capital indexado + interes civil puro) -- ver
    # AreaStrategy._tasa_civil_anual_pct en app/services/area_strategy.py.
    "CIVIL_ANNUAL_RATE": ([_CF, _CO, _HO], "%"),
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
    # que ese se deriva (ver CLAVE_CRUDA_DE en parametro_service.py). Actualizado
    # en el Sprint 43 junto con IPC_INDICE_ACUMULADO (ver arriba).
    "IPC_VARIACION_ANUAL": (_LAS_6_AREAS, "%"),
}


def serializar_areas(areas: list[AreaDerecho]) -> str:
    if not areas:
        raise ValueError("Debe seleccionarse al menos un area del derecho.")
    return json.dumps([area.value for area in areas])


def deserializar_areas(texto: str) -> list[AreaDerecho]:
    return [AreaDerecho(codigo) for codigo in json.loads(texto)]
