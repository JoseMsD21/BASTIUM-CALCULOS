"""Sprint 105: catalogo de tipos de proceso por rama del derecho, transcrito de
la respuesta del despacho (docs/Preguntas-Para-Abogado-Respondidas.md,
seccion "Sprint 105"). Estas pruebas fijan el arbol EXACTO de esa respuesta
para que nadie lo altere sin una nueva respuesta del despacho."""

import pytest

from app.services.catalogo_tipos_proceso import (
    RAMAS_PROCESO,
    TIPOS_PROCESO,
    buscar_tipo_proceso,
    tipos_proceso_por_area,
)
from database.models import AreaDerecho


def test_catalogo_tiene_las_seis_ramas_del_despacho_en_orden():
    assert [rama.nombre for rama in RAMAS_PROCESO] == [
        "Rama Civil y Comercial",
        "Rama de Familia",
        "Rama Laboral y de Seguridad Social",
        "Rama Penal",
        "Rama Contencioso Administrativa",
        "Rama Disciplinaria y Sancionatoria",
    ]


def test_catalogo_tiene_exactamente_los_trece_tipos_de_proceso_del_despacho():
    assert [(t.rama, t.nombre) for t in TIPOS_PROCESO] == [
        ("CIVIL_COMERCIAL", "Proceso Ejecutivo"),
        ("CIVIL_COMERCIAL", "Proceso Declarativo (Verbal o Verbal Sumario)"),
        ("CIVIL_COMERCIAL", "Proceso Divisorio"),
        ("CIVIL_COMERCIAL", "Trámite de Insolvencia"),
        ("FAMILIA", "Ejecutivo de Alimentos"),
        ("FAMILIA", "Proceso de Adjudicación Judicial de Apoyos"),
        ("LABORAL", "Proceso Ordinario Laboral"),
        ("PENAL", "Audiencias Preliminares"),
        ("PENAL", "Juicio Oral / Preacuerdos"),
        ("PENAL", "Incidente de Reparación Integral"),
        ("CONTENCIOSO_ADMINISTRATIVO", "Medios de Control Ordinarios"),
        ("CONTENCIOSO_ADMINISTRATIVO", "Trámite de Pago Oficioso"),
        ("DISCIPLINARIO_SANCIONATORIO", "Procedimiento Sancionatorio Contractual (Ley 1474)"),
    ]


def test_codigos_son_unicos():
    codigos = [t.codigo for t in TIPOS_PROCESO]
    assert len(codigos) == len(set(codigos))


def test_puertas_logicas_y_respuestas_transcritas_literalmente():
    ejecutivo = buscar_tipo_proceso("CIVIL_COMERCIAL_EJECUTIVO")
    assert ejecutivo.pregunta_logica == (
        "¿La obligación dineraria es expresa, clara, exigible y no está siendo objetada "
        "por el deudor/aseguradora?"
    )
    assert ejecutivo.respuesta == "SÍ"
    declarativo = buscar_tipo_proceso("CIVIL_COMERCIAL_DECLARATIVO")
    assert declarativo.pregunta_logica == ejecutivo.pregunta_logica
    assert declarativo.respuesta == "NO"

    preliminares = buscar_tipo_proceso("PENAL_AUDIENCIAS_PRELIMINARES")
    assert preliminares.pregunta_logica == "¿En qué etapa se encuentra la acción penal?"
    assert preliminares.respuesta == "Fase Previa"
    assert buscar_tipo_proceso("PENAL_JUICIO_ORAL_PREACUERDOS").respuesta == "Fase Resolutiva"
    assert (
        buscar_tipo_proceso("PENAL_INCIDENTE_REPARACION_INTEGRAL").respuesta == "Fase Post-Condena"
    )

    alimentos = buscar_tipo_proceso("FAMILIA_EJECUTIVO_ALIMENTOS")
    assert alimentos.pregunta_logica == (
        "¿Se busca el pago de obligaciones de sustento incumplidas?"
    )
    assert alimentos.respuesta is None
    assert alimentos.descripcion == (
        "Ejecución que incluye la liquidación pormenorizada de capital vencido e intereses "
        "moratorios (0,5% mensual), permitiendo el embargo y la retención anticipada de "
        "depósitos judiciales."
    )

    sancionatorio = buscar_tipo_proceso("SANCIONATORIO_CONTRACTUAL_LEY_1474")
    assert sancionatorio.pregunta_logica == (
        "¿Se imputan faltas o incumplimientos a un contratista estatal?"
    )


def test_todos_los_tipos_tienen_pregunta_y_descripcion():
    for tipo in TIPOS_PROCESO:
        assert tipo.pregunta_logica.startswith("¿") and tipo.pregunta_logica.endswith("?")
        assert tipo.descripcion.endswith(".")


@pytest.mark.parametrize(
    ("area", "codigos_esperados"),
    [
        (
            AreaDerecho.CIVIL_FAMILIA,
            [
                "CIVIL_COMERCIAL_EJECUTIVO",
                "CIVIL_COMERCIAL_DECLARATIVO",
                "CIVIL_COMERCIAL_DIVISORIO",
                "CIVIL_COMERCIAL_INSOLVENCIA",
                "FAMILIA_EJECUTIVO_ALIMENTOS",
                "FAMILIA_ADJUDICACION_APOYOS",
            ],
        ),
        (
            AreaDerecho.COMERCIAL,
            [
                "CIVIL_COMERCIAL_EJECUTIVO",
                "CIVIL_COMERCIAL_DECLARATIVO",
                "CIVIL_COMERCIAL_DIVISORIO",
                "CIVIL_COMERCIAL_INSOLVENCIA",
            ],
        ),
        (AreaDerecho.LABORAL, ["LABORAL_ORDINARIO"]),
        (AreaDerecho.SANCIONATORIO, ["SANCIONATORIO_CONTRACTUAL_LEY_1474"]),
        (AreaDerecho.HONORARIOS, []),
        (AreaDerecho.TRIBUTARIO, []),
    ],
)
def test_tipos_proceso_por_area(area, codigos_esperados):
    assert [t.codigo for t in tipos_proceso_por_area(area)] == codigos_esperados


def test_ramas_penal_y_contencioso_no_se_ofrecen_en_ninguna_area():
    ofrecidos = {t.codigo for area in AreaDerecho for t in tipos_proceso_por_area(area)}
    for tipo in TIPOS_PROCESO:
        if tipo.rama in ("PENAL", "CONTENCIOSO_ADMINISTRATIVO"):
            assert tipo.codigo not in ofrecidos


def test_buscar_tipo_proceso_desconocido_o_vacio_devuelve_none():
    assert buscar_tipo_proceso(None) is None
    assert buscar_tipo_proceso("") is None
    assert buscar_tipo_proceso("NO_EXISTE") is None
