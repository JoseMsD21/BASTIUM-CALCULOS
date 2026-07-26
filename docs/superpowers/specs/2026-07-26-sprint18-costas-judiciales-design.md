# Diseño — Sprint 18: Costas judiciales con tabla real de rangos

**Fecha:** 2026-07-26
**Origen:** `Pendientes.md`, sección "Sprint 18 — Costas judiciales con tabla real de rangos (Acuerdo
PCSJA20-11556)".
**Estado:** Aprobado por el usuario, listo para plan de implementación.

## Contexto

El PDF de requerimientos de BASTIUM (pág. 9-10 y 55) y el cierre del Sprint 4 dejaron pendiente conseguir
la tabla real de rangos de costas judiciales (agencias en derecho) del Consejo Superior de la Judicatura,
citando el "Acuerdo PCSJA20-11556" como ejemplo ("3% al 7% de las pretensiones reconocidas"). Ese pendiente
también quedó registrado en `Preguntas-Para-Abogado.md` (sección Sprint 18).

**Hallazgo de este sprint: el número "PCSJA20-11556" no existe.** Se buscó en fuentes oficiales
(`ramajudicial.gov.co`) y de prensa jurídica (Ámbito Jurídico, Gerencie.com) sin encontrar ningún acuerdo
con ese número. El acuerdo real y vigente que regula tarifas de agencias en derecho es el **Acuerdo
PSAA16-10554** del 5 de agosto de 2016 ("Por el cual se establecen las tarifas de agencias en derecho"),
Consejo Superior de la Judicatura — texto oficial completo (8 páginas) descargado y leído íntegro desde
`ramajudicial.gov.co`. Se documenta esta corrección de cita al cerrar el sprint, sin ocultar el error del
PDF original de requisitos.

La estructura real del acuerdo es sustancialmente más rica que "una tabla de cuantía → un porcentaje":
organiza las tarifas por **tipo de proceso** (10 categorías, 16 sub-casos reales contando instancias y
cuantías), **instancia** (única/primera/segunda) y, cuando hay pretensión pecuniaria, **tier de cuantía**
(mínima/menor/mayor, definido no por este acuerdo sino por el art. 25 del Código General del Proceso). Para
pretensiones pecuniarias el acuerdo da un **rango** de porcentaje con "ponderación inversa" obligatoria
(Parágrafo 3° art. 3°: a mayor valor, menor porcentaje dentro del rango) — no un valor fijo. Para asuntos
sin cuantía, el rango es en S.M.M.L.V. Tope absoluto: nunca más de 20 S.M.M.L.V.

## Decisiones tomadas con el usuario

1. **Alcance: las 10 categorías completas del acuerdo**, no solo "procesos declarativos" (opción más
   pequeña que se ofreció primero). Implementación en fases dentro de la misma rama/plan, no dividida en
   sub-sprints separados: primero la estructura de datos + Declarativos, luego el resto.
2. **Umbrales de cuantía: constantes del CGP art. 25 + SMLMV histórico**, no un campo manual de tier. Los
   umbrales (verificados en 2 fuentes independientes — ver "Fuentes externas" al final) son: mínima cuantía
   ≤ 40 S.M.L.M.V., menor cuantía > 40 y ≤ 150 S.M.L.M.V., mayor cuantía > 150 S.M.L.M.V., tomando el SMLMV
   vigente al momento de la radicación de la demanda. Se resuelve reutilizando `get_smlmv_for_year`
   (Sprint 5).
3. **Ponderación inversa: interpolación lineal automática dentro del rango**, con `costas_pct_manual`
   como override siempre disponible cuando el auto judicial real ya fijó un valor distinto. El acuerdo
   exige el principio ("a mayor valor, menor porcentaje") pero no da la fórmula matemática exacta — es
   discreción del juez en la práctica; la interpolación lineal es una aproximación razonable y documentada,
   no una cita literal de la norma.
4. **Ubicación de los datos: módulo Python nuevo y separado**, no una extensión de `parametro_service`. Los
   3 modos existentes de `parametro_service` (`ABIERTO`, `ANUAL_EXACTO`, `TRAMO_CERRADO`) resuelven por
   fecha; esta tabla resuelve por tipo de proceso/instancia/cuantía, un eje distinto. Sigue el patrón ya
   usado en `historical_index.py` (Sprint 5) y la separación "regla nombrada con cita legal propia" vs.
   matemática genérica que quedó documentada al cerrar el Sprint 6.
5. **Wiring: todas las áreas de litigio judicial, no solo Honorarios** — Civil/Familia, Comercial, Laboral,
   Sancionatorio y Honorarios. **Tributario queda excluido**: sus "costas" son en realidad sanciones
   administrativas de la DIAN (extemporaneidad, inexactitud), no agencias en derecho de un proceso
   judicial — dominio distinto, el acuerdo no aplica ahí.
6. **`costas_pct_manual` no se toca ni se reemplaza** — sigue siendo el override manual del Sprint 4.
   Cuando está presente en una obligación, manda sobre el cálculo automático nuevo.

## Estructura de datos (`app/engine/legal/agencias_en_derecho.py`, nuevo)

Constantes Python estructuradas (no SQLite), replicando el art. 5° del Acuerdo PSAA16-10554 exactamente
como está transcrito arriba (ver documento fuente citado en "Fuentes externas").

```python
class TipoProceso(str, Enum):
    DECLARATIVO_GENERAL = "declarativo_general"
    EXPROPIACION = "expropiacion"
    DESLINDE_AMOJONAMIENTO = "deslinde_amojonamiento"
    DIVISORIO = "divisorio"
    MONITORIO = "monitorio"
    EJECUTIVO = "ejecutivo"
    SUCESION = "sucesion"
    LIQUIDACION_SOCIEDAD_CONYUGAL = "liquidacion_sociedad_conyugal"
    LIQUIDACION_SOCIEDADES = "liquidacion_sociedades"
    INSOLVENCIA_PERSONA_NATURAL = "insolvencia_persona_natural"
    OTROS_LIQUIDACION = "otros_liquidacion"
    JURISDICCION_VOLUNTARIA = "jurisdiccion_voluntaria"
    RECURSO_CONTRA_AUTOS = "recurso_contra_autos"
    INCIDENTE = "incidente"
    RECURSO_EXTRAORDINARIO = "recurso_extraordinario"
    EXEQUATUR = "exequatur"


class Instancia(str, Enum):
    UNICA = "unica"
    PRIMERA = "primera"
    SEGUNDA = "segunda"


class CuantiaTier(str, Enum):
    MINIMA = "minima"
    MENOR = "menor"
    MAYOR = "mayor"
    SIN_CUANTIA = "sin_cuantia"


class UnidadTarifa(str, Enum):
    PORCENTAJE = "porcentaje"
    SMLMV = "smlmv"


@dataclass(frozen=True)
class RangoTarifa:
    minimo: Decimal
    maximo: Decimal
    unidad: UnidadTarifa


# Clave: (TipoProceso, Instancia, CuantiaTier | None) -> RangoTarifa
# CuantiaTier es None para los tramos que el acuerdo no distingue por cuantia
# (ej. segunda instancia de casi todas las categorias: "Entre 1 y 6 S.M.M.L.V.").
TARIFAS_AGENCIAS_EN_DERECHO: dict[tuple[TipoProceso, Instancia, CuantiaTier | None], RangoTarifa] = {
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.UNICA, CuantiaTier.SIN_CUANTIA):
        RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.UNICA, None):  # sin pretension pecuniaria
        RangoTarifa(Decimal("1"), Decimal("8"), UnidadTarifa.SMLMV),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, CuantiaTier.MENOR):
        RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, CuantiaTier.MAYOR):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, None):
        RangoTarifa(Decimal("1"), Decimal("10"), UnidadTarifa.SMLMV),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.SEGUNDA, None):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
    # ... resto de las 16 categorias, transcritas 1:1 del art. 5 (ver spec self-review /
    # plan de implementacion para el listado completo fase por fase).
}

TOPE_MAXIMO_SMLMV = Decimal("20")  # Paragrafo 3, articulo 3 -- nunca se supera, sin importar la categoria.

UMBRAL_MINIMA_CUANTIA_SMLMV = Decimal("40")   # CGP art. 25
UMBRAL_MENOR_CUANTIA_SMLMV = Decimal("150")   # CGP art. 25
```

Notas de diseño:
- El diccionario completo (16 sub-casos × hasta 3 instancias × hasta 2 tiers de cuantía) se transcribe
  íntegro durante la implementación, fase por fase según el plan — el bloque de arriba es un extracto
  ilustrativo de "Procesos Declarativos en General", no la tabla completa.
- Las claves con `CuantiaTier | None = None` representan los tramos "sin pretensión pecuniaria" o los que
  el acuerdo no distingue por cuantía (ej. casi todas las segundas instancias, incidentes, recursos).
  `CuantiaTier.SIN_CUANTIA` (con S.M.M.L.V. como unidad) es distinto del caso "no aplica cuantía" — se usa
  únicamente en los pocos tramos donde el acuerdo sí ofrece una tarifa en % *y* una en SMLMV según si la
  pretensión es pecuniaria o no (ej. única instancia de Declarativos).

## Función de cálculo (`app/engine/legal/agencias_en_derecho.py`)

```python
def calcular_agencias_en_derecho(
    tipo_proceso: TipoProceso,
    instancia: Instancia,
    pretensiones_reconocidas: Decimal,
    fecha_radicacion: date,
    tiene_pretension_pecuniaria: bool = True,
) -> Decimal:
    """Calcula el valor de agencias en derecho segun el Acuerdo PSAA16-10554,
    interpolando linealmente dentro del rango aplicable (ponderacion inversa,
    Paragrafo 3 art. 3: a mayor valor, menor porcentaje) y aplicando el tope
    de 20 SMLMV. Lanza TarifaNoDisponibleError si la combinacion tipo_proceso/
    instancia/cuantia no esta en la tabla -- nunca inventa un rango."""
```

- Si `tiene_pretension_pecuniaria`: resuelve el `CuantiaTier` con `pretensiones_reconocidas` contra los
  umbrales del CGP art. 25 (convertidos a pesos con el SMLMV de `fecha_radicacion.year`), busca el
  `RangoTarifa`, e interpola linealmente: valor en el piso del tier → porcentaje máximo del rango; valor en
  el techo del tier → porcentaje mínimo del rango.
- Si no tiene pretensión pecuniaria, o el rango resuelto está en S.M.M.L.V.: usa el punto medio del rango
  como valor por defecto (no hay "posición dentro del tier" que interpolar) — documentado como
  aproximación, siempre puede sobreescribirse con `costas_pct_manual`.
- Convierte el resultado a pesos y aplica el tope de 20 S.M.M.L.V. (`min(resultado, 20 × smlmv_vigente)`).
- `TarifaNoDisponibleError` (nueva, `app/core/exceptions.py`, mismo patrón que `UVTNoDisponibleError` del
  Sprint 4) si la combinación no existe en la tabla.

## Campos nuevos en `Obligacion` + migración

- `costas_tipo_proceso: str | None` (nombre del `TipoProceso`, nullable).
- `costas_instancia: str | None` (nombre de `Instancia`, nullable).
- Migración nueva (`scripts/migrate_costas_tipo_proceso.py`), mismo patrón que
  `scripts/migrate_aplica_indexacion_ipc.py` (Sprint 8) y `scripts/migrate_moneda_trm.py` (Sprint 12).
- Si ambos campos son `None`, no hay cálculo automático — el comportamiento es exactamente el de hoy
  (solo `costas_pct_manual` si está presente). Esto es lo que garantiza que el Sprint 4 no se rompe.
- `pretensiones_reconocidas` **no es un campo nuevo**: se resuelve reutilizando `obligacion.valor` para
  Civil/Familia, Comercial, Laboral y Sancionatorio, y `obligacion.beneficio_obtenido` para Honorarios
  (campo ya usado ahí para el tope de cuota litis, semánticamente es "lo reconocido en el proceso").
- `fecha_radicacion` **no es un campo nuevo**: se aproxima con `obligacion.fecha_origen` — el modelo de
  datos actual no distingue "fecha de radicación de la demanda" de "fecha del hecho generador". Se
  documenta como aproximación (mismo criterio que otras aproximaciones de fecha ya aceptadas en sprints
  anteriores, ej. Sprint 8 con años ≥2026).

## Wiring en las 5 estrategias

En `app/services/area_strategy.py`, cada `liquidar()` de `CivilFamiliaStrategy`, `ComercialStrategy`,
`LaboralStrategy`, `SancionatorioStrategy` y `HonorariosStrategy`: si la obligación tiene
`costas_tipo_proceso` y `costas_instancia` pero **no** tiene `costas_pct_manual`, calcula automáticamente
vía `calcular_agencias_en_derecho(...)` y agrega un evento `COSTAS_PROCESALES` (mismo patrón que ya existe
en `HonorariosStrategy`, línea ~679). Si `costas_pct_manual` está presente, ese manda — el cálculo
automático nunca lo sobreescribe.

`TributarioStrategy` no se toca.

## Manejo de errores

- Combinación `tipo_proceso`/`instancia`/cuantía no cubierta por la tabla → `TarifaNoDisponibleError`,
  nunca se asume un valor.
- `pretensiones_reconocidas` ausente o ≤ 0 cuando se pide cálculo automático → `ValueError` explícito.

## Testing

- `tests/engine/legal/test_agencias_en_derecho.py`: al menos 1-2 casos reales por cada uno de los 16
  sub-tipos, verificados contra el texto del Acuerdo PSAA16-10554 (transcrito en este spec y en el archivo
  fuente).
- Test del tope de 20 S.M.M.L.V. (caso donde el porcentaje calculado lo superaría).
- Test de interpolación en los dos extremos exactos de un tier (piso → % máximo, techo → % mínimo) y en el
  punto medio.
- Test de resolución de `CuantiaTier` contra los umbrales del CGP art. 25 (40 y 150 SMLMV), incluyendo los
  valores límite exactos.
- Test de `TarifaNoDisponibleError` para una combinación no cubierta.
- Tests de wiring en las 5 estrategias: con `costas_tipo_proceso`/`costas_instancia` (cálculo automático),
  con `costas_pct_manual` (override, verificando que gana sobre el automático), y sin ninguno de los dos
  (sin evento de costas — comportamiento idéntico al de antes del sprint).
- Test de migración.
- Suite completa en verde.

## Fuera de alcance (explícito)

- `TributarioStrategy` — dominio distinto (sanciones DIAN, no agencias en derecho judiciales).
- Modelar "condena en costas parcial" (Parágrafo 5° art. 3°: si la demanda prospera solo parcialmente, el
  juez puede abstenerse de condenar en costas o hacerlo parcialmente) — la obligación de BASTIUM no tiene
  hoy un concepto de "porcentaje de prosperidad de la demanda"; se documenta como limitación conocida.
- El "criterio de valoración favorable para víctimas de violencia de género" (Parágrafo art. 2°) — no hay
  forma de capturar esa circunstancia en el modelo de datos actual; se documenta como limitación conocida,
  no se inventa un campo nuevo sin que el usuario lo pida.

## Definición de hecho

- Tabla completa de las 16 categorías/sub-casos transcrita y verificada contra el texto oficial del
  Acuerdo PSAA16-10554.
- `calcular_agencias_en_derecho` con TDD, cubriendo interpolación, tope, tiers de cuantía y error de tarifa
  no disponible.
- Las 5 estrategias de área calculan costas automáticamente cuando corresponde, y siguen respetando
  `costas_pct_manual` como override — el comportamiento del Sprint 4 no se rompe.
- Migración de esquema corrida contra el `bastium.db` real del equipo.
- Suite completa en verde.
- `Preguntas-Para-Abogado.md`: actualizar la sección Sprint 18 — la pregunta original ya no aplica (se
  encontró la fuente), se reemplaza por las aproximaciones que sí quedan abiertas: uso de
  `valor`/`beneficio_obtenido` como "pretensiones reconocidas", `fecha_origen` como aproximación de
  "fecha de radicación", y la interpolación lineal como aproximación de la "ponderación inversa" del
  Parágrafo 3°.
- `Pendientes.md`: marcar Sprint 18 como completado, corrigiendo el título de "Acuerdo PCSJA20-11556" a
  "Acuerdo PSAA16-10554" y documentando el hallazgo.
- `README.md`/`docs/GUIA_USUARIO.md` actualizados (regla obligatoria de cierre de sprint).

## Fuentes externas verificadas (no vienen del PDF de BASTIUM)

- Acuerdo PSAA16-10554, 5 de agosto de 2016, Consejo Superior de la Judicatura — texto oficial completo
  descargado de `https://www.gerencie.com/wp-content/uploads/acuerdo-agencias-derecho.pdf` (copia del texto
  publicado originalmente en `ramajudicial.gov.co`), leído íntegro (8 páginas) durante este sprint.
- Código General del Proceso (Ley 1564 de 2012), artículo 25 — umbrales de cuantía (40 y 150 SMLMV)
  verificados de forma independiente en `https://leyes.co/codigo_general_del_proceso/25.htm` y
  `https://procesal.uexternado.edu.co/codigo-general/articulo-25-cuantia/`.
- Confirmado que "Acuerdo PCSJA20-11556" (citado en el PDF de requisitos de BASTIUM) no corresponde a
  ningún acuerdo real localizable del Consejo Superior de la Judicatura.
