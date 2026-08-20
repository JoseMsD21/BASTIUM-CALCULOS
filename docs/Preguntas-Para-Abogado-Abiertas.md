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

### Cómo guardar tu respuesta en GitHub (paso a paso)

Una vez hayas escrito tus respuestas directamente en este documento dentro de GitHub, sigue estos pasos
para guardarlas correctamente. Esto deja tu respuesta lista para que yo (JoseMsD) la revise y la apruebe
antes de que quede incorporada de forma definitiva — no se publica sola apenas la guardas.

1. **Abre el archivo en GitHub.** Entra al repositorio y ubica `docs/Preguntas-Para-Abogado-Abiertas.md`.
   Verás el documento en modo lectura, con las pestañas **Preview / Code / Blame** arriba del contenido.

   ![Vista del archivo en GitHub en modo lectura](resources/guia-commit-abogado/1-ver-archivo.png)

2. **Haz clic en el ícono del lápiz (✏️)**, ubicado en la esquina superior derecha del visor de archivo
   (junto a los íconos de copiar/descargar). Al pasar el mouse por encima aparece el mensaje
   "**Edit this file**". Haz clic ahí para entrar al modo de edición.

   ![Ícono de lápiz con el tooltip "Edit this file"](resources/guia-commit-abogado/2-boton-editar.png)

3. **Escribe tu respuesta** en el espacio en blanco que dice "**Respuesta del despacho:**", justo debajo de
   cada pregunta que estés contestando. No borres ni modifiques las preguntas, encabezados o enlaces del
   resto del documento — agrega tu texto únicamente en el espacio indicado. Puedes usar la pestaña
   **Preview** (arriba del editor) para revisar cómo se ve tu respuesta antes de continuar.

   ![Editor de texto de GitHub con el botón "Commit changes..."](resources/guia-commit-abogado/3-editor.png)

4. **Cuando termines, haz clic en el botón verde "Commit changes..."** (arriba a la derecha del editor).
   Se abrirá una ventana emergente para confirmar el guardado.

5. **En el campo "Commit message"**, borra el texto que sugiere GitHub y escribe algo que identifique
   claramente qué respondiste, por ejemplo:
   `Respuestas Sprint 82 y 90 - [tu nombre o el del despacho]`
   En "Extended description" puedes agregar, opcionalmente, una nota breve como "Se respondieron 2
   preguntas pendientes."

6. **Muy importante — selecciona la segunda opción**, "**Create a new branch for this commit and start a
   pull request**" (en vez de "Commit directly to the main branch", que viene marcada por defecto). Esto
   es lo que permite que yo vea tu respuesta como una propuesta de cambio y la apruebe antes de que se una
   al documento oficial. Puedes dejar el nombre de rama que GitHub sugiere automáticamente.

   ![Ventana "Commit changes" con la opción "Create a new branch for this commit and start a pull request" marcada](resources/guia-commit-abogado/4-commit-changes.png)

7. **Haz clic en "Propose changes"** para confirmar. GitHub te llevará automáticamente a la pantalla de
   creación del Pull Request — ahí haz clic en "**Create pull request**" para enviarlo.

8. **Listo.** Recibiré una notificación del Pull Request y podré revisar exactamente qué agregaste
   (resaltado en verde frente al texto original). Si la respuesta queda clara y sin conflicto con el
   código, la apruebo y la fusiono ("merge") al documento oficial. Si necesito una aclaración adicional, te
   la pido ahí mismo como comentario dentro del mismo Pull Request.

---

## Índice

- [Sprint 8 (seguimiento 2) — Tabla real de índices IPC mensuales del DANE (doble base 2008/2018)](#sprint-8-seguimiento-2--tabla-real-de-índices-ipc-mensuales-del-dane-doble-base-20082018)
- [Sprint 18 (seguimiento 2) — ¿PCSJA20-11556 y PSAA16-10554 son el mismo acuerdo?](#sprint-18-seguimiento-2--pcsja20-11556-y-psaa16-10554-son-el-mismo-acuerdo)
- [Sprint 43 (seguimiento) — ¿Es válido cobrar interés civil sobre el capital ya indexado en Honorarios?](#sprint-43-seguimiento--es-válido-cobrar-interés-civil-sobre-el-capital-ya-indexado-en-honorarios)
- [Sprint 70 — Motor de vigencia de leyes por año (Ley 100/1993, Ley 797/2003, Ley 2381/2024 y transiciones CST/CPT)](#sprint-70--motor-de-vigencia-de-leyes-por-año-ley-1001993-ley-7972003-ley-23812024-y-transiciones-cstcpt)
- [Sprint 74 — Familia: tipos de beneficiario de alimentos y reglas de vigencia por tipo](#sprint-74--familia-tipos-de-beneficiario-de-alimentos-y-reglas-de-vigencia-por-tipo)
- [Sprint 76 — Fórmula de tasa del Art. 1617/2232 C.C.: ¿lineal diaria, efectiva compuesta diaria, o mensual con prorrateo de 30 días?](#sprint-76--fórmula-de-tasa-del-art-16172232-cc-lineal-diaria-efectiva-compuesta-diaria-o-mensual-con-prorrateo-de-30-días)
- [Sprint 78 — Conteo de días para densidad pensional (semanas cotizadas): ¿aplica el "+1" inclusivo?](#sprint-78--conteo-de-días-para-densidad-pensional-semanas-cotizadas-aplica-el-1-inclusivo)
- [Sprint 79 — ¿Las costas procesales deben generar interés civil del 6% junto con el capital (Suma Única)?](#sprint-79--las-costas-procesales-deben-generar-interés-civil-del-6-junto-con-el-capital-suma-única)
- [Sprint 80 — Cobertura parcial de la serie mensual de IPC (2003-2026) y qué hacer con fechas anteriores](#sprint-80--cobertura-parcial-de-la-serie-mensual-de-ipc-2003-2026-y-qué-hacer-con-fechas-anteriores)
- [Sprint 82 — ¿El despacho litiga contra entidades públicas (condenas administrativas con intereses a la tasa DTF)?](#sprint-82--el-despacho-litiga-contra-entidades-públicas-condenas-administrativas-con-intereses-a-la-tasa-dtf)
- [Sprint 86/87 — Bono pensional y cálculo actuarial de cotizaciones omisas: factores de reserva y tabla DTF Pensional](#sprint-8687--bono-pensional-y-cálculo-actuarial-de-cotizaciones-omisas-factores-de-reserva-y-tabla-dtf-pensional)
- [Sprint 90 — Fundamento legal de la fórmula IBL de últimas 100/150 semanas (régimen ISS anterior a 1994)](#sprint-90--fundamento-legal-de-la-fórmula-ibl-de-últimas-100150-semanas-régimen-iss-anterior-a-1994)
- [Sprint 91 (seguimiento del Sprint 70) — Tabla completa de tasa de reemplazo por régimen: 1993-2003, régimen de transición e invalidez](#sprint-91-seguimiento-del-sprint-70--tabla-completa-de-tasa-de-reemplazo-por-régimen-1993-2003-régimen-de-transición-e-invalidez)
- [Sprint 92 — Laboral: ¿fecha de corte real entre régimen Ley 50/1990 y Ley 789/2002 para la indemnización por despido?](#sprint-92--laboral-fecha-de-corte-real-entre-régimen-ley-501990-y-ley-7892002-para-la-indemnización-por-despido)
- [Sprint 93 — Laboral: ¿en qué procesos se usa reajuste por IPC vs. por SMMLV para salarios dejados de percibir?](#sprint-93--laboral-en-qué-procesos-se-usa-reajuste-por-ipc-vs-por-smmlv-para-salarios-dejados-de-percibir)
- [Sprint 94 — Laboral: base de aportes a salud/pensión reclamables en contrato realidad, y regla de la bonificación por servicio](#sprint-94--laboral-base-de-aportes-a-saludpensión-reclamables-en-contrato-realidad-y-regla-de-la-bonificación-por-servicio)
- [Sprint 95 — Laboral: tabla de transición de la Ley 2466 de 2025 (horario nocturno y recargo dominical/festivo)](#sprint-95--laboral-tabla-de-transición-de-la-ley-2466-de-2025-horario-nocturno-y-recargo-dominicalfestivo)
- [Sprint 96 — Laboral: ¿hay diferencia de fórmula (no solo de captura) para trabajo doméstico tras la Ley 1788/2016?](#sprint-96--laboral-hay-diferencia-de-fórmula-no-solo-de-captura-para-trabajo-doméstico-tras-la-ley-17882016)
- [Sprint 97 — ¿Nueva área de derecho o submodo de Civil/Familia para indemnización de perjuicios?](#sprint-97--nueva-área-de-derecho-o-submodo-de-civilfamilia-para-indemnización-de-perjuicios)
- [Sprint 98 — Tabla completa de mortalidad de rentistas (Resolución 1555 de 2010, Superfinanciera)](#sprint-98--tabla-completa-de-mortalidad-de-rentistas-resolución-1555-de-2010-superfinanciera)
- [Sprint 102 — Ejemplo numérico resuelto de indexación con abonos (X9)](#sprint-102--ejemplo-numérico-resuelto-de-indexación-con-abonos-x9)
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

**Actualización (2026-08-19) — borrador de punto de partida encontrado en una plantilla comercial del
despacho, para confirmar o corregir (no tomar como definitivo):** `P9.TASA-DE-REEMPLAZO-LEY-797-2003.md`
trae, además de la fórmula que ya implementa BASTIUM (`r = 65.5 − 0.5·s`, vigente "desde el año 2004 en
adelante"), otras 2 tablas de tasa de reemplazo que el código de hoy NO cubre: una para "Ley 797 de 2003,
desde 1993 hasta 2003" y otra para el "Régimen de Transición" (tasa fija 75%/90%/"la que corresponda"). La
plantilla no deja ver la fórmula matemática completa de esas 2 tablas con datos de ejemplo, así que este
hallazgo no reemplaza la pregunta original — solo confirma con una fuente adicional que faltan al menos 2
fórmulas más, y da un punto de partida concreto para pedirlas. Ver Sprint 91 en `Pendientes.md`, que
también añade a la lista 2 tablas de tasa de reemplazo para pensión de invalidez (grados 1 y 2) con cifras
que sí se pudieron extraer completas de la misma plantilla (base 45%/54% + incrementos de 1,5%/2% cada 50
semanas, tope 75%) — inclúyanlas también en la respuesta si aplican al alcance de BASTIUM.

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

## Sprint 76 — Fórmula de tasa del Art. 1617/2232 C.C.: ¿lineal diaria, efectiva compuesta diaria, o mensual con prorrateo de 30 días?

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

**Actualización (2026-08-19, Sprint 83) — aparece una tercera opción, y es la que usa el propio despacho:**
al revisar la plantilla comercial que el despacho usa para este mismo interés civil del 6% (Art. 2232 C.C.,
gemelo del Art. 1617), `i7.INTERESES-CIVILES-6-ANUAL.xlsm` de Ediciones Sistematizadas Equidad, encontramos
que su fórmula real no es la A ni la B de arriba:

**Opción C — Tasa mensual nominal con prorrateo de 30 días, la que usa la plantilla del despacho:**

`tasa_mensual = [(1+6%)^(1/12) − 1] × 12 = 0,4867%` mensual, y el interés de cada período se calcula como
`capital × tasa_mensual × (días_del_período / 30)` — es decir, convierte el 6% EA a una tasa **mensual**
(no diaria) usando la fórmula compuesta, pero luego reparte esa tasa mensual **linealmente** entre los días
del mes, siempre sobre una base de 30 días fijos (no 28/29/30/31 reales). Verificado numéricamente contra
la propia tabla de ejemplo de la plantilla: capital $5.000.000, interés de junio/2025 (30 días) =
$24.500,00, interés de julio/2025 (31 días) = $24.500 × 31/30 = $25.316,67 — cifras que solo cuadran con
esta fórmula, no con la A ni con la B.

**Pregunta:** para el interés civil del Art. 1617/2232 C.C. (y, si aplica también a otras tasas pactadas por
las partes en Civil/Familia y Comercial, siempre que no se haya pactado capitalización/anatocismo), ¿la
conversión de la tasa anual debe hacerse con la fórmula **lineal diaria** (Opción A, `tasa_anual ÷ 365`, la
que trae el documento de requisitos), la **efectiva compuesta diaria** (Opción B, `(1+tasa_anual)^(1/365) −
1`, la que usa el software hoy), o la **mensual nominal con prorrateo de 30 días** (Opción C,
`[(1+tasa_anual)^(1/12)−1]×12` repartida entre `días/30`, la que usa la propia plantilla comercial del
despacho)? Y, relacionado: cuando el interés diario calculado NO se reinvierte en el capital (comportamiento
por defecto del software, sin anatocismo), ¿tiene sentido jurídico seguir usando una tasa derivada asumiendo
capitalización, o debería usarse siempre la lineal en ese caso?

**Qué necesito exactamente:** confirmación de cuál de las tres fórmulas (A, B o C) debe usar el software
para el interés del Art. 1617/2232 y para las tasas pactadas sin capitalización explícita — y, si la
respuesta es "depende" (ej. depende de si la tasa fue certificada como "efectiva anual" en el título
ejecutivo o no), una regla clara de cuándo aplica cada una. Ver también Sprint 83 en `Pendientes.md` para
el detalle técnico completo de la Opción C.

**Dónde vive esto en el código (para referencia del desarrollo, no hace falta leerlo para responder):**
`app/engine/interest/rate_conversion.py`, clase `EffectiveRateConverter`, método `annual_to_daily` —
implementa hoy la Opción B. Cambiarla afecta a las 6 áreas del derecho (todas pasan por el mismo motor),
no solo Civil/Familia.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 78 — Conteo de días para densidad pensional (semanas cotizadas): ¿aplica el "+1" inclusivo?

**Contexto:** el software cuenta días trabajados con la fórmula `Dias = (Fecha_Fin - Fecha_Inicio) + 1`
(conteo inclusivo, el primer día cuenta) para prestaciones sociales y en general, según ya confirmaron
ustedes en la respuesta del Sprint 3. Pero el módulo que calcula las semanas cotizadas para pensión (para
saber si alguien cumple las 1.300 semanas mínimas) usa una resta simple de fechas, sin el "+1". Este cálculo
ya está verificado contra un caso de prueba real citado en la documentación de la fórmula pensional (348 días
→ 50 semanas, no 349) — es decir, no parece un error, pero tampoco está confirmado explícitamente si la regla
general del "+1" también debería aplicar aquí o si el cálculo de semanas es, a propósito, la excepción.

**Pregunta:** para contar los días que se convierten en "semanas cotizadas" de pensión, ¿debe sumarse 1 día
al resultado de la resta de fechas (igual que para prestaciones), o el conteo sin ese "+1" es el correcto
para este cálculo específico?

**Qué necesito exactamente:** un sí/no sobre si aplica el "+1" a este cálculo puntual, y si la respuesta es
"depende", una aclaración de cuándo sí y cuándo no.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 79 — ¿Las costas procesales deben generar interés civil del 6% junto con el capital (Suma Única)?

**Contexto:** cuando una obligación tiene marcado "Interés sobre capital ya indexado" (algoritmo Suma
Única, disponible en Civil/Familia y ahora también en Comercial y Honorarios) y además tiene costas
procesales, el software hoy suma las costas al mismo monto de capital que genera el interés civil del 6%
anual — es decir, las costas también generan ese interés, no solo el capital original de la obligación.

**Pregunta:** ¿es correcto que las costas procesales generen interés junto con el capital bajo este
algoritmo, o las costas deberían sumarse al final del cálculo sin generar interés adicional?

**Qué necesito exactamente:** un sí/no sobre si las costas deben incluirse en la base que genera interés
bajo Suma Única.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 80 — Cobertura parcial de la serie mensual de IPC (2003-2026) y qué hacer con fechas anteriores

**Contexto:** ya conseguimos la tabla real de índices IPC mensuales que el despacho pidió (ver respuesta al Sprint 8), pero con dos particularidades frente a lo que se había pedido: (1) viene en una sola base continua (diciembre 2018 = 100), ya "enlazada" oficialmente por el DANE, en vez de las dos bases separadas (2008 y 2018) con un Factor de Enlace que el software calculara; y (2) solo cubre desde enero de 2003 en adelante — no hay índice mensual disponible para fechas anteriores a 2003.

**Pregunta:** (1) ¿La serie ya enlazada por el DANE en una sola base (diciembre 2018 = 100) es aceptable para indexar, o el despacho necesita específicamente las dos bases separadas con el Factor de Enlace calculado por el software? (2) Para liquidaciones con `fecha_origen` anterior a enero de 2003, ¿el software debe (a) bloquear la indexación IPC exigiendo que el usuario indique manualmente el índice, (b) usar la variación % anual ya cargada (interpolación anual, la misma que el despacho calificó de "jurídicamente inválida" para fechas recientes, pero aplicada aquí solo por falta de alternativa), o (c) alguna otra solución?

**Qué necesito exactamente:** una confirmación de sí/no sobre la base única, y una instrucción clara sobre qué hacer con fechas anteriores a 2003 (aceptar el hueco, usar la variación anual como aproximación documentada, o conseguir otra fuente).

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 82 — ¿El despacho litiga contra entidades públicas (condenas administrativas con intereses a la tasa DTF)?

**Contexto:** encontramos que una de las plantillas del despacho (`i10.INTERESES-TASADOS-A-LA-DTF-CONDENAS-ADMINISTRATIVAS.md`) liquida intereses de mora en condenas o conciliaciones contra el Estado, a una tasa equivalente a la DTF durante los primeros 10 meses después de la ejecutoria (Art. 195 núm. 4 de la Ley 1437 de 2011), y luego a la tasa comercial. Ninguna de las 6 áreas actuales de BASTIUM (Civil/Familia, Comercial, Laboral, Sancionatorio, Honorarios, Tributario) contempla explícitamente litigios contra entidades públicas de esta naturaleza.

**Pregunta:** ¿el despacho maneja casos de este tipo (demandas o conciliaciones contra el Estado con condena en dinero)? Si es así, ¿en cuál de las áreas actuales de BASTIUM encajarían, o se necesitaría un área/flujo nuevo?

**Qué necesito exactamente:** un sí/no sobre si este escenario es relevante para el despacho, y si es así, a qué área debería asignarse (o confirmación de que se necesita una nueva).

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 86/87 — Bono pensional y cálculo actuarial de cotizaciones omisas: factores de reserva y tabla DTF Pensional

**Contexto:** las plantillas comerciales de referencia (Ediciones Sistematizadas Equidad) para bono pensional (P12, P13, P14) y cálculo actuarial de
cotizaciones omisas (P10) usan una fórmula de "Reserva Actuarial = (PR x F1 + AF x F2) x F3" basada en el Decreto 1296 de 2022, actualizada con la DTF
Pensional (Decreto 1299 de 1994, Decreto 1887 de 1994). El desarrollo no pudo extraer con certeza, de la exportación a texto de esas plantillas, la
definición exacta de los factores F1, F2, F3, ni la tabla histórica completa de tasas DTF Pensional mes a mes desde 1994.

**Pregunta:** ¿puede el despacho aportar la definición exacta de los factores F1, F2 y F3 de la fórmula de reserva actuarial (Decreto 1296/2022), la
definición de "AF", y la tabla histórica de DTF Pensional mensual desde enero de 1994? Alternativamente, ¿puede aportar los archivos Excel originales de
estas plantillas (no la versión ya convertida a texto) para que el desarrollo los revise directamente?

**Qué necesito exactamente:** la fórmula completa con cada factor definido, o el archivo Excel original de P12/P13/P14/P10 sin convertir.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 90 — Fundamento legal de la fórmula IBL de últimas 100/150 semanas (régimen ISS anterior a 1994)

**Contexto:** las plantillas P15 e P16 calculan el IBL de un régimen distinto al de la Ley 100 (últimas 100 o 150 semanas cotizadas, con un factor fijo de
4.33 y topes de 90%), pero ninguna de las dos cita el Acuerdo/Decreto específico que respalda esa fórmula ni el origen del factor 4.33.

**Pregunta:** ¿cuál es la norma exacta (probablemente un Acuerdo del ISS anterior a la Ley 100 de 1993) que respalda la fórmula de IBL de 100/150 semanas
con el factor 4.33 y el tope del 90%? ¿El despacho sigue liquidando casos bajo este régimen histórico?

**Qué necesito exactamente:** cita de la norma exacta (número de Acuerdo/Decreto y artículo), y confirmación de si es una funcionalidad que el despacho
realmente necesita hoy.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 91 (seguimiento del Sprint 70) — Tabla completa de tasa de reemplazo por régimen: 1993-2003, régimen de transición e invalidez

**Contexto:** la plantilla comercial P9 (Tasa de Reemplazo Ley 797/2003) trae, además de la fórmula que ya implementa BASTIUM (r = 65.5 − 0.5·s, vigente
desde 2004), otras 3 tablas para: el período 1993-2003, el régimen de transición (tasa fija 75%/90%/"la que corresponda"), y pensión de invalidez grados 1 y
2 (bases 45%/54% con incrementos de 1,5%/2% cada 50 semanas). El desarrollo pudo extraer las cifras exactas de invalidez (confirmadas contra la propia
tabla numérica de la plantilla), pero no la fórmula matemática completa de los otros dos regímenes (1993-2003 y transición), que la plantilla no deja ver
con datos de ejemplo.

**Pregunta:** ¿puede el despacho confirmar (a) la fórmula exacta de tasa de reemplazo aplicable a causantes de pensión entre 1993 y 2003, (b) la regla
exacta de cuándo aplica 75% vs. 90% vs. "la que corresponda" en el régimen de transición, y (c) si las cifras de invalidez que trae la plantilla comercial
(grado 1: 45% + 1,5%/50 semanas sobre 500, tope 75%; grado 2: 54% + 2%/50 semanas sobre 800, tope 75%) son correctas?

**Qué necesito exactamente:** las 2 fórmulas faltantes con su fundamento normativo exacto, y una confirmación sí/no de las cifras de invalidez citadas.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 92 — Laboral: ¿fecha de corte real entre régimen Ley 50/1990 y Ley 789/2002 para la indemnización por despido?

**Contexto:** la plantilla comercial `L4.INDEMNIZACIONPORDESPIDOLABORALYSANCIONMORATORIA.md` que usa el
despacho trae dos regímenes de indemnización por despido injustificado según cuándo ingresó el trabajador,
pero cita la misma fecha ("27 de diciembre de 1.992") para ambos regímenes, atribuyéndosela una vez a la
Ley 789 de 2002 y otra vez a la Ley 50 de 1990 — que es de 1990, no de 1992. Antes de programar las tablas
de días de indemnización, necesito saber cuál es la fecha de corte legal real.

**Pregunta:** ¿el corte entre el régimen "favorable" (45 días primer año + 15/20 días subsiguientes) y el
régimen posterior (30 días primer año + 20 días subsiguientes) es el 1° de enero de 1991 (entrada en
vigencia de la Ley 50 de 1990), o es realmente el 27 de diciembre de 1992 como cita la plantilla?

**Qué necesito exactamente:** la fecha exacta de corte, y si aplica alguna fecha adicional distinta para el
régimen de trabajadores con salario ≥10 SMMLV.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 93 — Laboral: ¿en qué procesos se usa reajuste por IPC vs. por SMMLV para salarios dejados de percibir?

**Contexto:** el despacho tiene dos plantillas casi idénticas para liquidar salarios y prestaciones dejadas
de percibir durante un período sin contrato vigente — una reajusta el salario año a año según la inflación
(IPC) y la otra según el incremento del salario mínimo (SMMLV). El software ya tiene ambos mecanismos de
reajuste construidos (Sprint 41/75, para otras áreas), pero antes de conectarlos a Laboral necesito saber
cuándo se usa cada uno.

**Pregunta:** ¿la elección entre reajustar por IPC o por SMMLV depende del tipo de proceso (ej. reintegro
por despido nulo vs. contrato realidad), es una decisión discrecional del abogado según lo que pida en la
demanda, o depende de otro criterio? ¿Hay algún caso en que se deban aplicar ambos reajustes combinados?

**Qué necesito exactamente:** una regla clara (o confirmación de que es libre elección del abogado) sobre
cuándo usar cada índice.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 94 — Laboral: base de aportes a salud/pensión reclamables en contrato realidad, y regla de la bonificación por servicio

**Contexto:** en las plantillas de "contrato realidad" (privado y sector público), el aporte a salud/pensión
reclamable se calcula con porcentajes (8.5%/12% en la privada, 8%/12% en la pública) distintos de los que ya
usa el software para seguridad social laboral general (16% pensión + 12.5% salud, que corresponde al aporte
total empleador+trabajador, confirmado con el despacho en el Sprint 16). Además, la plantilla del sector
público trae una regla de la bonificación por servicio ("corresponde al 35%, pero hasta 2 smmlv, escriba
50%") sin explicar de dónde sale ni sobre qué base se aplica.

**Pregunta:** (1) en un reclamo de contrato realidad, ¿los aportes a salud/pensión que se reclaman son el
total (empleador + trabajador, igual que el Sprint 16) o solo la porción a cargo del empleador (8.5%/8% y
12%)? (2) ¿cuál es la regla completa de la bonificación por servicio del sector público (base de cálculo,
por qué cambia de 35% a 50% con el tope de 2 SMMLV, y la norma que la respalda)?

**Qué necesito exactamente:** confirmación del porcentaje/base de aportes aplicable, y la regla completa
(con norma) de la bonificación por servicio.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 95 — Laboral: tabla de transición de la Ley 2466 de 2025 (horario nocturno y recargo dominical/festivo)

**Contexto:** el software no tiene hoy ningún cálculo de horas extra ni recargos, y antes de construirlo
necesito los porcentajes vigentes. La reciente Ley 2466 de 2025 modificó progresivamente (2025-2027) tanto
el horario que se considera "nocturno" como el porcentaje del recargo dominical/festivo, así que no basta
con un solo porcentaje fijo — hace falta saber qué aplica según la fecha del hecho, igual que ya se hace con
otras tasas legales del sistema (ej. tasa de usura).

**Pregunta:** ¿pueden confirmar la tabla completa de transición de la Ley 2466/2025 — fechas de corte,
horario nocturno vigente en cada tramo, y porcentaje del recargo dominical/festivo en cada tramo hasta
2027 — y los porcentajes de horas extra (diurna/nocturna, ordinaria/festiva) que siguen vigentes sin cambio?

**Qué necesito exactamente:** una tabla de fecha de corte → porcentaje/horario aplicable, para cada uno de
los 7 conceptos de la plantilla L3 (horas extra diurnas/nocturnas ordinarias, recargo nocturno, horas extra
diurnas/nocturnas festivas, recargo festivo diurno/nocturno).

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 96 — Laboral: ¿hay diferencia de fórmula (no solo de captura) para trabajo doméstico tras la Ley 1788/2016?

**Contexto:** la plantilla de liquidación de prestaciones para empleada doméstica que usa el despacho tiene
la misma estructura de cálculo (cesantías, intereses, prima, vacaciones) que la plantilla general — la única
diferencia visible es que convierte un salario diario y días laborados por semana a un equivalente mensual
antes de aplicar las mismas fórmulas. Antes de construir esto como un simple conversor de datos (sin motor
nuevo), necesito confirmar que no hay ninguna diferencia de fórmula que la plantilla no esté mostrando.

**Pregunta:** después de la Ley 1788 de 2016 (que unificó la prima de servicios para el servicio doméstico
con el régimen general), ¿queda alguna diferencia de fórmula entre las prestaciones sociales de un
trabajador doméstico y el régimen general de cesantías/intereses/prima/vacaciones, o son exactamente las
mismas fórmulas aplicadas sobre una base salarial calculada distinto (diario→mensual)?

**Qué necesito exactamente:** un sí/no sobre si hay diferencia de fórmula, y si la hay, cuál es.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 97 — ¿Nueva área de derecho o submodo de Civil/Familia para indemnización de perjuicios?

**Contexto:** el despacho envió 8 plantillas comerciales (daño emergente, lucro cesante en 6 variantes de
beneficiario, y beneficio dejado de percibir como fruto civil) que usan una fórmula actuarial completa
(anualidad + tabla de mortalidad de rentistas) que hoy no existe en BASTIUM. Lo que existe hoy en el
software (categorías "Daño emergente" y "Lucro cesante consolidado" dentro de Civil/Familia) es solo una
etiqueta de un capital plano con interés simple e indexación IPC — no reproduce ninguna de las fórmulas de
las plantillas.

**Pregunta:** ¿el despacho litiga habitualmente casos de responsabilidad civil extracontractual (daño
emergente, lucro cesante de víctima incapacitada, de cónyuge/hijos o de padres de víctima fallecida), y
quiere que BASTIUM construya este motor como una séptima área de derecho, o prefiere que se integre como
una extensión de Civil/Familia? ¿De las 6 variantes de lucro cesante que trajeron las plantillas (víctima
incapacitado, cónyuge e hijos, padres de víctima adulta, padres de hijo menor, pensionado de fondo privado,
beneficio dejado de percibir), cuáles usa realmente el despacho?

**Qué necesito exactamente:** confirmación de si esto es una prioridad real de uso (no solo material de
referencia que llegó junto con las demás plantillas), y si es así, cuál de las 6 variantes conviene construir
primero.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 98 — Tabla completa de mortalidad de rentistas (Resolución 1555 de 2010, Superfinanciera)

**Contexto:** las plantillas de lucro cesante futuro (víctima incapacitada, cónyuge e hijos, padres,
pensionado de fondo privado) necesitan la expectativa de vida de la víctima según su edad y sexo, tomada de
la tabla de mortalidad de rentistas de la Resolución 1555 de 2010 de la Superintendencia Financiera. Las
plantillas traen esta tabla incrustada como referencia (hoja `TablasMortalidad`), pero el material revisado
solo cubre edades desde 15 hasta cerca de 38 años — no se confirmó si la tabla incrustada en las plantillas
llega hasta la edad máxima que puede necesitarse (ej. hasta 100+ años) ni si hay alguna actualización
posterior a 2010 que el despacho use en su lugar.

**Pregunta:** ¿pueden aportar la tabla completa de mortalidad de rentistas de la Resolución 1555 de 2010
(hombres y mujeres, todas las edades), o confirmar si el despacho usa una fuente/versión distinta?

**Qué necesito exactamente:** la tabla completa (edad → años de expectativa de vida, separada por sexo)
desde la edad mínima relevante hasta la máxima, en cualquier formato (Excel, PDF, o el enlace oficial de la
Superfinanciera).

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 102 — Ejemplo numérico resuelto de indexación con abonos (X9)

**Contexto:** la plantilla `X9.INDEXACION-CON-ABONOS.md` documenta un algoritmo de indexar un capital único,
aplicar abonos parciales sucesivos, y reindexar el saldo restante tras cada abono. El desarrollo cree que el
motor actual de BASTIUM (Suma Única + abonos, ya usado en Civil/Familia desde el Sprint 75) ya reproduce
este comportamiento, pero la plantilla en sí no trae ningún ejemplo con cifras reales resueltas — solo el
formulario vacío — así que no hay forma de verificarlo sin datos.

**Pregunta:** ¿el despacho tiene un caso real (o puede construir uno de ejemplo) con un capital inicial,
2-3 abonos en fechas distintas, e IPC de cada fecha, ya resuelto en su Excel, para poder comparar contra el
resultado de BASTIUM?

**Qué necesito exactamente:** capital inicial + fecha, cada abono con su fecha y monto, los IPC usados en
cada corte, y el resultado final esperado — igual que se hizo con el caso real usado para validar el
Sprint 76.

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
