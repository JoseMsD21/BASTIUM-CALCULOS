"""Catalogo de tipos de proceso por rama del derecho (Sprint 105).

Fuente unica: respuesta del despacho del 16/11/2026, transcrita literalmente
de docs/Preguntas-Para-Abogado-Respondidas.md, seccion "Sprint 105 --
Catalogo de tipos de proceso, subtipos de caso y obligaciones predefinidas
para el intake de un expediente". El arbol es: rama -> [PUERTA LOGICA]
(pregunta si/no u orientadora) -> tipo de proceso -> descripcion. Los textos
de pregunta, respuesta, nombre y descripcion son copia literal de esa
respuesta; solo los `codigo` son de BASTIUM (identificadores estables que se
guardan en `expedientes.tipo_proceso`). No agregar, quitar ni reescribir
entradas sin una nueva respuesta del despacho -- las pruebas de
tests/services/test_catalogo_tipos_proceso.py fijan el arbol exacto.

Es un catalogo INFORMATIVO: clasifica el expediente en el intake y orienta al
abogado con la pregunta logica y la descripcion, pero no altera ningun
calculo ni regla del motor de liquidacion.

Mapeo rama del despacho -> AreaDerecho de BASTIUM (`RamaProceso.areas`):
- Civil y Comercial -> CIVIL_FAMILIA y COMERCIAL.
- Familia -> CIVIL_FAMILIA (BASTIUM agrupa Civil y Familia en una sola area).
- Laboral y de Seguridad Social -> LABORAL.
- Disciplinaria y Sancionatoria -> SANCIONATORIO.
- Penal y Contencioso Administrativa: BASTIUM no tiene esas areas; quedan
  catalogadas (areas vacias) pero no se ofrecen en ningun formulario.
- HONORARIOS y TRIBUTARIO no corresponden a ninguna rama de la respuesta, asi
  que no tienen tipos de proceso que ofrecer.

Pendiente (no definido por el despacho, NO inventar): la "checklist de
obligaciones predefinidas" por subtipo que describe Pendientes.md, Sprint 105.
"""

from __future__ import annotations

from dataclasses import dataclass

from database.models import AreaDerecho


@dataclass(frozen=True)
class RamaProceso:
    codigo: str
    nombre: str
    # Areas de BASTIUM en las que se ofrecen los tipos de proceso de esta
    # rama. Tupla vacia = rama catalogada sin area en BASTIUM.
    areas: tuple[AreaDerecho, ...]


@dataclass(frozen=True)
class TipoProceso:
    codigo: str
    rama: str
    pregunta_logica: str
    # Respuesta a la puerta logica que lleva a este tipo ("SÍ"/"NO" o la fase
    # penal). None cuando la respuesta del despacho no la explicita (puerta
    # con un unico desenlace).
    respuesta: str | None
    nombre: str
    descripcion: str


RAMAS_PROCESO: tuple[RamaProceso, ...] = (
    RamaProceso(
        "CIVIL_COMERCIAL",
        "Rama Civil y Comercial",
        (AreaDerecho.CIVIL_FAMILIA, AreaDerecho.COMERCIAL),
    ),
    RamaProceso("FAMILIA", "Rama de Familia", (AreaDerecho.CIVIL_FAMILIA,)),
    RamaProceso("LABORAL", "Rama Laboral y de Seguridad Social", (AreaDerecho.LABORAL,)),
    RamaProceso("PENAL", "Rama Penal", ()),
    RamaProceso("CONTENCIOSO_ADMINISTRATIVO", "Rama Contencioso Administrativa", ()),
    RamaProceso(
        "DISCIPLINARIO_SANCIONATORIO",
        "Rama Disciplinaria y Sancionatoria",
        (AreaDerecho.SANCIONATORIO,),
    ),
)

_PREGUNTA_CIVIL_EJECUTIVO_O_DECLARATIVO = (
    "¿La obligación dineraria es expresa, clara, exigible y no está siendo objetada "
    "por el deudor/aseguradora?"
)
_PREGUNTA_PENAL = "¿En qué etapa se encuentra la acción penal?"

TIPOS_PROCESO: tuple[TipoProceso, ...] = (
    # 1. Rama Civil y Comercial
    TipoProceso(
        codigo="CIVIL_COMERCIAL_EJECUTIVO",
        rama="CIVIL_COMERCIAL",
        pregunta_logica=_PREGUNTA_CIVIL_EJECUTIVO_O_DECLARATIVO,
        respuesta="SÍ",
        nombre="Proceso Ejecutivo",
        descripcion=(
            "Trámite de cobro forzado. Requiere presentación del título y, en materia de "
            "seguros, acreditar la reclamación formal y el vencimiento de un mes sin "
            "objeción de la compañía."
        ),
    ),
    TipoProceso(
        codigo="CIVIL_COMERCIAL_DECLARATIVO",
        rama="CIVIL_COMERCIAL",
        pregunta_logica=_PREGUNTA_CIVIL_EJECUTIVO_O_DECLARATIVO,
        respuesta="NO",
        nombre="Proceso Declarativo (Verbal o Verbal Sumario)",
        descripcion=(
            "Resuelve controversias sustanciales o negociales donde el derecho está en "
            "debate (ej. objeción de pólizas, responsabilidad civil). Exige como requisito "
            "ineludible de procedibilidad la audiencia de conciliación extrajudicial."
        ),
    ),
    TipoProceso(
        codigo="CIVIL_COMERCIAL_DIVISORIO",
        rama="CIVIL_COMERCIAL",
        pregunta_logica="¿Se busca finiquitar la comunidad sobre un derecho real?",
        respuesta=None,
        nombre="Proceso Divisorio",
        descripcion=(
            "Liquidación material o venta del bien común al 100% del avalúo; está "
            "expresamente excluido de requerir conciliación previa."
        ),
    ),
    TipoProceso(
        codigo="CIVIL_COMERCIAL_INSOLVENCIA",
        rama="CIVIL_COMERCIAL",
        pregunta_logica="¿El deudor es persona natural (no comerciante) en cesación de pagos?",
        respuesta=None,
        nombre="Trámite de Insolvencia",
        descripcion=(
            "Procedimiento de negociación de deudas con salvaguardas legales que prohíben "
            "condonar impuestos e imponen una prelación estricta de pagos (1ra clase: "
            "alimentos, créditos laborales, fisco)."
        ),
    ),
    # 2. Rama de Familia
    TipoProceso(
        codigo="FAMILIA_EJECUTIVO_ALIMENTOS",
        rama="FAMILIA",
        pregunta_logica="¿Se busca el pago de obligaciones de sustento incumplidas?",
        respuesta=None,
        nombre="Ejecutivo de Alimentos",
        descripcion=(
            "Ejecución que incluye la liquidación pormenorizada de capital vencido e "
            "intereses moratorios (0,5% mensual), permitiendo el embargo y la retención "
            "anticipada de depósitos judiciales."
        ),
    ),
    TipoProceso(
        codigo="FAMILIA_ADJUDICACION_APOYOS",
        rama="FAMILIA",
        pregunta_logica=(
            "¿Una persona mayor de edad con discapacidad requiere formalizar asistencia jurídica?"
        ),
        respuesta=None,
        nombre="Proceso de Adjudicación Judicial de Apoyos",
        descripcion=(
            "Proceso de jurisdicción voluntaria o verbal sumario utilizado cuando los "
            "apoyos no han sido formalizados de mutuo acuerdo ante notario o centro de "
            "conciliación."
        ),
    ),
    # 3. Rama Laboral y de Seguridad Social
    TipoProceso(
        codigo="LABORAL_ORDINARIO",
        rama="LABORAL",
        pregunta_logica=(
            "¿Existe litigio sobre expectativas de derechos (ej. transición pensional, "
            "afiliaciones omitidas)?"
        ),
        respuesta=None,
        nombre="Proceso Ordinario Laboral",
        descripcion=(
            "Proceso que dirime controversias sustantivas (como el régimen de transición o "
            "cálculos actuariales), donde la conciliación extrajudicial es apenas "
            "potestativa y no un requisito de procedibilidad."
        ),
    ),
    # 4. Rama Penal
    TipoProceso(
        codigo="PENAL_AUDIENCIAS_PRELIMINARES",
        rama="PENAL",
        pregunta_logica=_PREGUNTA_PENAL,
        respuesta="Fase Previa",
        nombre="Audiencias Preliminares",
        descripcion=(
            "Trámites ante el juez de control de garantías para dictar medidas de "
            "aseguramiento, imputaciones o legalidad probatoria. Puede fenecer mediante "
            "archivo (orden del fiscal) o preclusión (decisión del juez)."
        ),
    ),
    TipoProceso(
        codigo="PENAL_JUICIO_ORAL_PREACUERDOS",
        rama="PENAL",
        pregunta_logica=_PREGUNTA_PENAL,
        respuesta="Fase Resolutiva",
        nombre="Juicio Oral / Preacuerdos",
        descripcion=(
            "Práctica de pruebas con inmediación, o bien, negociación de culpabilidad que "
            "requiere la verificación judicial para evitar vicios del consentimiento."
        ),
    ),
    TipoProceso(
        codigo="PENAL_INCIDENTE_REPARACION_INTEGRAL",
        rama="PENAL",
        pregunta_logica=_PREGUNTA_PENAL,
        respuesta="Fase Post-Condena",
        nombre="Incidente de Reparación Integral",
        descripcion=(
            "Trámite de naturaleza estrictamente civil extracontractual incrustado en el "
            "proceso penal. Requiere demanda en regla, formulación de pretensiones "
            "jurídicas directas e indirectas, y no admite variaciones oficiosas por el juez."
        ),
    ),
    # 5. Rama Contencioso Administrativa
    TipoProceso(
        codigo="CONTENCIOSO_MEDIOS_CONTROL_ORDINARIOS",
        rama="CONTENCIOSO_ADMINISTRATIVO",
        pregunta_logica=(
            "¿Se persigue una pretensión patrimonial o resarcimiento contra el Estado?"
        ),
        respuesta=None,
        nombre="Medios de Control Ordinarios",
        descripcion=(
            "Demandas (ej. reparación directa, nulidad y restablecimiento) que exigen la "
            "notificación personal y obligatoria a la entidad demandada, al Ministerio "
            "Público y a la Agencia Nacional de Defensa Jurídica del Estado."
        ),
    ),
    TipoProceso(
        codigo="CONTENCIOSO_PAGO_OFICIOSO",
        rama="CONTENCIOSO_ADMINISTRATIVO",
        pregunta_logica="¿Se busca el pago de una decisión ya en firme?",
        respuesta=None,
        nombre="Trámite de Pago Oficioso",
        descripcion=(
            "Procedimiento de cobro derivado de sentencias, laudos o conciliaciones ejecutoriadas."
        ),
    ),
    # 6. Rama Disciplinaria y Sancionatoria
    TipoProceso(
        codigo="SANCIONATORIO_CONTRACTUAL_LEY_1474",
        rama="DISCIPLINARIO_SANCIONATORIO",
        pregunta_logica="¿Se imputan faltas o incumplimientos a un contratista estatal?",
        respuesta=None,
        nombre="Procedimiento Sancionatorio Contractual (Ley 1474)",
        descripcion=(
            "Trámite que garantiza el derecho de uso de la palabra, la motivación de la "
            "decisión, y la posibilidad de finalizar por cesación del incumplimiento."
        ),
    ),
)

_TIPO_POR_CODIGO: dict[str, TipoProceso] = {t.codigo: t for t in TIPOS_PROCESO}
_RAMA_POR_CODIGO: dict[str, RamaProceso] = {r.codigo: r for r in RAMAS_PROCESO}


def buscar_tipo_proceso(codigo: str | None) -> TipoProceso | None:
    """TipoProceso para `codigo`, o None si es vacio o no esta en el catalogo."""
    if not codigo:
        return None
    return _TIPO_POR_CODIGO.get(codigo)


def nombre_rama(codigo_rama: str) -> str:
    return _RAMA_POR_CODIGO[codigo_rama].nombre


def tipos_proceso_por_area(area: AreaDerecho) -> list[TipoProceso]:
    """Tipos de proceso que se ofrecen para `area`, en el orden del catalogo
    (ramas en el orden de la respuesta del despacho)."""
    ramas = {r.codigo for r in RAMAS_PROCESO if area in r.areas}
    return [t for t in TIPOS_PROCESO if t.rama in ramas]


def texto_ayuda(tipo: TipoProceso) -> str:
    """Texto de ayuda de un tipo: rama, puerta logica (con su respuesta, si la
    hay) y descripcion. Lo usan el formulario y el detalle del expediente."""
    pregunta = tipo.pregunta_logica
    if tipo.respuesta:
        pregunta = f"{pregunta} → {tipo.respuesta}"
    return (
        f"{nombre_rama(tipo.rama)}\n"
        f"Pregunta orientadora: {pregunta}\n"
        f"Descripción: {tipo.descripcion}"
    )
