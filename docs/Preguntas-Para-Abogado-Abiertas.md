# Preguntas para el abogado — Abiertas — BASTIUM Cálculos

## Instrucciones de uso

**Para Mí como desarrollador JoseMsD (quien maneja este documento):**

1. Copia la sección que te interese y pégala en un Word, o envía el enlace directo a esta sección.
2. Envíalo al abogado o despacho correspondiente. Cada pregunta tiene un espacio en blanco
   ("**Respuesta del despacho:**") para que ellos escriban la respuesta directamente ahí.
3. Cuando llegue una respuesta que quede totalmente clara y sin conflicto con el código, muévela a
   [`Preguntas-Para-Abogado-Respondidas.md`](Preguntas-Para-Abogado-Respondidas.md) (dile a Claude Code
   "mueve la respuesta del Sprint N a Respondidas" y él se encarga de dejarlo consistente en ambos
   documentos y en `Pendientes.md`).
4. Este documento es un documento **vivo**: cada vez que un sprint nuevo tenga una decisión legal sin
   confirmar, una fuente que falte, o una respuesta que haya quedado en conflicto con lo ya construido, se
   le agrega una sección nueva siguiendo la plantilla del final.

**Para el abogado / despacho que responde:**

Este documento acompaña el desarrollo de BASTIUM, un software de liquidación de procesos judiciales
(cálculo de capital, intereses, indexación, prescripción, etc.) para uso interno de un despacho. Cada
sección de abajo es una pregunta que **sigue abierta** — o porque nunca se respondió, o porque la
respuesta que llegó no se pudo aplicar tal cual (falta un dato, o entra en conflicto con algo que el
software ya tenía construido) y necesita una aclaración adicional. No hace falta leer código ni tener
conocimientos técnicos.

Las preguntas ya resueltas (sin necesidad de volver a preguntarlas) están archivadas aparte, en
[`Preguntas-Para-Abogado-Respondidas.md`](Preguntas-Para-Abogado-Respondidas.md).

---

## Índice

- [Sprint 8 (seguimiento 2) — Tabla real de índices IPC mensuales del DANE (doble base 2008/2018)](#sprint-8-seguimiento-2--tabla-real-de-índices-ipc-mensuales-del-dane-doble-base-20082018)
- [Sprint 18 (seguimiento 2) — ¿PCSJA20-11556 y PSAA16-10554 son el mismo acuerdo?](#sprint-18-seguimiento-2--pcsja20-11556-y-psaa16-10554-son-el-mismo-acuerdo)
- [Sprint 43 (seguimiento) — ¿Es válido cobrar interés civil sobre el capital ya indexado en Honorarios?](#sprint-43-seguimiento--es-válido-cobrar-interés-civil-sobre-el-capital-ya-indexado-en-honorarios)
- [Sprint 70 — Motor de vigencia de leyes por año (Ley 100/1993, Ley 797/2003, Ley 2381/2024 y transiciones CST/CPT)](#sprint-70--motor-de-vigencia-de-leyes-por-año-ley-1001993-ley-7972003-ley-23812024-y-transiciones-cstcpt)
- [Sprint 74 — Familia: tipos de beneficiario de alimentos y reglas de vigencia por tipo](#sprint-74--familia-tipos-de-beneficiario-de-alimentos-y-reglas-de-vigencia-por-tipo)
- [Sprint 76 — Fórmula de tasa diaria del Art. 1617 C.C.: ¿lineal (6%÷365) o efectiva compuesta?](#sprint-76--fórmula-de-tasa-diaria-del-art-1617-cc-lineal-6365-o-efectiva-compuesta)
- [Plantilla para sprints futuros](#plantilla-para-sprints-futuros)

---

## Sprint 8 (seguimiento 2) — Tabla real de índices IPC mensuales del DANE (doble base 2008/2018)

**Contexto:** el despacho ya confirmó la metodología exacta que debe usar el motor de IPC mensual (ver
Sprint 8 en `Preguntas-Para-Abogado-Respondidas.md`): operar siempre sobre el Número Índice (no variación
%), soportando dos bases (diciembre 2008 = 100 y diciembre 2018 = 100) enlazadas por un Factor de Enlace
calculado en el mes de traslape. Con esa metodología ya confirmada, sigue faltando el único insumo que el
desarrollo no puede producir por sí mismo: **los valores reales** del índice mes a mes. La página 62 del
PDF de requisitos (`REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`) solo trae la variación
**anual** 1967-2025 (ya transcrita en el software), no el índice mensual con sus dos bases.

**Pregunta:** ¿el despacho tiene acceso a la serie histórica mensual de IPC del DANE en las dos bases
(diciembre 2008 = 100 y diciembre 2018 = 100), por ejemplo vía Legis, Actualícese Premium, o la suscripción
de datos que use el despacho? Si es así, ¿pueden aportar esa tabla (Excel, CSV, o el enlace de descarga)?

**Qué necesito exactamente:** la tabla de índice IPC mensual (no variación %) con una columna que indique
a qué base pertenece cada valor (2008 o 2018), cubriendo desde el año más antiguo que el despacho necesite
liquidar hasta el mes más reciente certificado por el DANE. Si no se consigue la serie completa, sirve
acotar desde qué año en adelante hace falta — misma lógica que se usó con la UVT en el Sprint 14.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 18 (seguimiento 2) — ¿PCSJA20-11556 y PSAA16-10554 son el mismo acuerdo?

**Contexto:** el desarrollo había identificado y verificado directamente contra la fuente oficial
(ramajudicial.gov.co) que el Acuerdo **PSAA16-10554** del 5 de agosto de 2016 del Consejo Superior de la
Judicatura es el que regula las tarifas de agencias en derecho, y transcribió su tabla granular completa
(18 tipos de proceso × instancia). La respuesta más reciente del despacho, sobre cómo conviven la tabla
simple de 3 rangos con la tabla granular, cita en cambio el Acuerdo **PCSJA20-11556** como el que rige hoy.

**Pregunta:** ¿el PCSJA20-11556 es una actualización/reemplazo del PSAA16-10554 (en cuyo caso el desarrollo
necesitaría la tabla granular actualizada de ese acuerdo nuevo, no la de 2016), o son referencias al mismo
acuerdo con una numeración distinta por error de transcripción?

**Qué necesito exactamente:** confirmación de cuál de los dos números es el correcto, y si es un acuerdo
distinto al PSAA16-10554, la tabla granular actualizada (18 tipos de proceso × instancia, o los que
correspondan) del acuerdo vigente.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 43 (seguimiento) — ¿Es válido cobrar interés civil sobre el capital ya indexado en Honorarios?

**Contexto:** la respuesta del despacho para Honorarios (ver Sprint 43 en
`Preguntas-Para-Abogado-Respondidas.md`) trae la fórmula `Capital_Honorarios × (IPC_Final / IPC_Inicial) +
Interés_Civil_6%_Anual(Capital_Actualizado)` — es decir, el interés civil del 6% se calcula **sobre el
capital ya indexado**, no sobre el capital original. Esto es distinto de cómo funciona hoy el resto del
motor: en Civil/Familia (Sprint 8), el interés se calcula solo sobre el capital original, nunca sobre el
capital ya indexado — quedó documentado como limitación conocida en su momento, precisamente porque
combinar interés + indexación sobre la misma base puede considerarse una doble actualización no permitida
en algunos escenarios (revisado también en la respuesta del Sprint 15, sobre la prohibición de "doble
consideración" del componente inflacionario).

**Pregunta:** ¿es jurídicamente correcto que el interés civil del 6% anual en Honorarios se calcule sobre
el capital ya indexado (interés compuesto sobre la corrección monetaria), o el ordenamiento exige que el
interés se calcule siempre sobre el capital original, aplicándose la indexación como un rubro aparte que no
genera intereses sobre sí mismo?

**Qué necesito exactamente:** confirmación de una de las dos opciones, o la aclaración exacta si depende de
si el título ejecutivo pactó expresamente el interés sobre "capital actualizado" o no.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 70 — Motor de vigencia de leyes por año (Ley 100/1993, Ley 797/2003, Ley 2381/2024 y transiciones CST/CPT)

**Contexto:** hoy el software resuelve las fórmulas y cifras legales (tasa de reemplazo pensional,
porcentajes, topes) con una sola versión de cada fórmula, sin distinguir qué ley aplicaba en la fecha en
que ocurrió el hecho generador del caso. En la práctica, la ley que rige un caso depende de la fecha en que
el hecho ocurrió, no de la fecha actual: por ejemplo, quien se pensionó en 1997 se rige por la Ley 100 de
1993, quien se pensionó en 2024 por la Ley 797 de 2003, y quien se pensione desde que entró en vigencia la
Ley 2381 de 2024 se rige por esa ley nueva. Lo mismo aplica en Derecho Laboral y Seguridad Social, donde el
Código Sustantivo del Trabajo y el Código de Procedimiento del Trabajo han tenido varias modificaciones con
fechas de vigencia propias.

**Pregunta:** para las fórmulas y cifras que dependen de la ley vigente al momento del hecho (empezando por
la tasa de reemplazo pensional del Sprint 17, hoy implementada como una sola fórmula fija `r = 65.5 −
0.5·s` de la Ley 100/Ley 797), ¿pueden confirmar la lista de leyes relevantes con su fecha exacta de entrada
en vigencia y qué fórmula/cifra corresponde a cada una, empezando por: Ley 100 de 1993, Ley 797 de 2003, y
Ley 2381 de 2024? ¿Hay otras leyes/reformas del CST o del CPT con vigencias específicas que el motor deba
distinguir de la misma forma?

**Qué necesito exactamente:** una tabla de Ley → fecha de entrada en vigencia → fórmula o cifra que
corresponde → a qué módulo del software aplica (pensional, laboral, otro). No hace falta que sea exhaustiva
de una sola vez — puede empezar por las 3 leyes pensionales mencionadas y ampliarse después.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 74 — Familia: tipos de beneficiario de alimentos y reglas de vigencia por tipo

**Contexto:** hoy el software no distingue quién es el beneficiario de una obligación alimentaria más allá
de un campo de texto libre — no pregunta si es un niño, un niño con discapacidad, el cónyuge, los padres, u
otra persona (ej. donante), y por lo tanto no puede calcular automáticamente hasta cuándo es exigible cada
obligación. Según lo que el usuario describe: para niños sin discapacidad la obligación termina a los 18
años si no estudia una carrera profesional/técnica/tecnológica, o se extiende hasta los 25 años si estudia;
para niños con discapacidad permanente la obligación es vitalicia; para el cónyuge se debe hasta que supere
su condición de vulnerabilidad (ej. consiga trabajo); para los padres se debe hasta la muerte de cualquiera
de las partes; y para otros beneficiarios (abuelos, donantes) aplicarían reglas puntuales.

**Pregunta:** ¿pueden confirmar la lista completa de reglas de vigencia por tipo de beneficiario descritas
arriba, y las que falten (ej. ¿cómo se determina y se prueba en el proceso que un cónyuge "superó su
condición de vulnerabilidad"? ¿hay un tope de edad distinto si el niño sin discapacidad no estudia pero
tampoco puede sostenerse por otra razón?)? ¿Existen otras categorías de beneficiario además de las
mencionadas (niño, niño con discapacidad, cónyuge, padres, otros) que el software deba contemplar?

**Qué necesito exactamente:** confirmación de las reglas de vigencia por tipo de beneficiario, con la norma
que respalda cada una, para poder construir el árbol de decisión que el usuario pidió en el formulario de
captura del caso.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 76 — Fórmula de tasa diaria del Art. 1617 C.C.: ¿lineal (6%÷365) o efectiva compuesta?

**Contexto (explicado desde cero, para quien no haya visto el código):**

El Artículo 1617 del Código Civil dice que, cuando un contrato no pactó una tasa de interés, se debe el
**6% anual**. El software necesita liquidar día por día (para saber exactamente cuánto interés se debe
en cualquier fecha, no solo al cierre de cada año), así que ese 6% anual tiene que convertirse primero en
una **tasa diaria equivalente**. El problema es que existen dos formas matemáticas distintas — y
legalmente distintas — de hacer esa conversión, y dan números diferentes.

**Opción A — Lineal (o "nominal"), la fórmula que trae el documento de requisitos:**

Es la división simple: `tasa_diaria = 6% ÷ 365 = 0,016438...%` por día (el documento
`REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf` la redondea a `0,0164`). La idea detrás de esta
fórmula es que el 6% anual se "reparte" en partes iguales entre los 365 días del año — ningún día genera
más ni menos que los demás, y el interés de cada día se calcula siempre sobre el mismo porcentaje fijo.

**Opción B — Efectiva compuesta, la que usa BASTIUM hoy:**

`tasa_diaria = (1 + 6%)^(1/365) − 1 = 0,015965...%` por día — un poquito más baja que la Opción A. La idea
detrás de esta fórmula es distinta: en el mundo financiero/bancario colombiano, cuando una tasa se certifica
como "efectiva anual" (EA — así se certifican, por ejemplo, las tasas de usura de la Superfinanciera), se
asume que el interés se reinvierte (se capitaliza) cada día, y esta fórmula calcula la única tasa diaria
que, capitalizada 365 veces seguidas, reproduce exactamente ese 6% al cabo del año — ni un peso más, ni un
peso menos. Es la fórmula estándar para convertir una tasa "efectiva" (EA) a un plazo más corto.

**La tensión que hay que resolver:** el Art. 1617 nunca dice que el 6% sea una tasa "efectiva anual" en el
sentido técnico-financiero (con capitalización); podría leerse simplemente como "6% al año, repartido en
partes iguales" — que es la Opción A. Además, BASTIUM **no capitaliza** el interés día a día (el interés se
guarda aparte, nunca se le suma al capital para que genere más interés sobre sí mismo, salvo que exista
anatocismo pactado en Comercial) — así que usar hoy una tasa "diseñada para capitalizar" pero sin
capitalizar en la práctica es, como mínimo, una inconsistencia que vale la pena que el despacho confirme o
corrija.

**Ejemplo numérico simple, para entender la diferencia:** $10.000.000 de capital, 30 días, al 6% anual:

| Fórmula | Tasa diaria | Interés de 30 días |
|---|---|---|
| A — Lineal (6% ÷ 365) | 0,016438% | **$49.315,20** |
| B — Efectiva compuesta (fórmula actual de BASTIUM) | 0,015965% | **$47.896,20** |

Diferencia: **$1.419,00** (la Opción A da 2,96% más interés que la Opción B) sobre apenas 30 días y un
capital de $10 millones. La diferencia crece con el capital y con el tiempo transcurrido.

**Ejemplo con un caso real capturado en el software (Radicado 2224, prueba práctica del usuario, comparado
contra un Excel real del despacho):** cuota de $300.000/mes desde noviembre de 2023, reajustada cada 1° de
enero según el SMMLV (Sprint 41), sin indexación IPC, liquidada hasta el 31 de agosto de 2025 (~22 meses):

| | Excel del despacho | BASTIUM con la fórmula actual (B) | BASTIUM si usara la fórmula lineal (A) |
|---|---|---|---|
| Intereses | $423.063,74 | $410.700,80 | **$422.866,16** |
| Gran Total | **$7.999.230,14** | $7.990.356,08 | **$8.002.521,44** |
| Diferencia vs. el Excel | — | 0,11% por debajo | **0,04% por encima** |

Con la fórmula lineal (Opción A), BASTIUM queda casi 3 veces más cerca del resultado del Excel del despacho
que con la fórmula que usa hoy. El 0,04% que todavía quedaría de diferencia ya no sería por la tasa —
vendría de que el Excel del despacho aproxima el interés mes a mes con un 0,50% fijo (en vez de contar los
días exactos de cada mes) y redondea el porcentaje de reajuste del SMMLV (12,00%/9,53% en vez del dato
exacto 12,07%/9,50%).

**Pregunta:** para el interés civil del Art. 1617 (y, si aplica también a otras tasas pactadas por las
partes en Civil/Familia y Comercial, siempre que no se haya pactado capitalización/anatocismo), ¿la
conversión de la tasa anual a diaria debe hacerse con la fórmula **lineal** (`tasa_anual ÷ 365`, la que trae
el documento de requisitos) o con la fórmula **efectiva compuesta** (`(1+tasa_anual)^(1/365) − 1`, la que
usa el software hoy)? Y, relacionado: cuando el interés diario calculado NO se reinvierte en el capital
(comportamiento por defecto del software, sin anatocismo), ¿tiene sentido jurídico seguir usando una tasa
derivada asumiendo capitalización, o debería usarse siempre la lineal en ese caso?

**Qué necesito exactamente:** confirmación de cuál de las dos fórmulas (A o B) debe usar el software para
el interés del Art. 1617 y para las tasas pactadas sin capitalización explícita — y, si la respuesta es "depende"
(ej. depende de si la tasa fue certificada como "efectiva anual" en el título ejecutivo o no), una regla
clara de cuándo aplica cada una.

**Dónde vive esto en el código (para referencia del desarrollo, no hace falta leerlo para responder):**
`app/engine/interest/rate_conversion.py`, clase `EffectiveRateConverter`, método `annual_to_daily` —
implementa hoy la Opción B. Cambiarla afecta a las 6 áreas del derecho (todas pasan por el mismo motor),
no solo Civil/Familia.

**Respuesta del despacho:**


**Fecha:**

---

## Plantilla para sprints futuros

Copiar este bloque y completarlo cuando un sprint nuevo tenga una decisión legal sin confirmar, una fuente
que falte, o una respuesta que haya quedado en conflicto con el código ya construido:

```
## Sprint N — [Nombre del sprint]

**Contexto:** [Explicación en lenguaje llano de qué decisión se tomó o qué falta, y por qué importa.]

**Pregunta:** [Pregunta puntual, lo más cerrada posible — idealmente respondible con un sí/no o un dato
concreto.]

**Qué necesito exactamente:** [Formato exacto de la respuesta esperada: confirmación, corrección, tabla,
documento, ejemplo numérico, etc.]

**Respuesta del despacho:**


**Fecha:**
```
