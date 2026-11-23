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

- [Sprint 18 (seguimiento 3) — Discrepancia numérica entre la tabla granular verificada (PSAA16-10554) y las "tarifas duras" que aportó el despacho](#sprint-18-seguimiento-3--discrepancia-numérica-entre-la-tabla-granular-verificada-psaa16-10554-y-las-tarifas-duras-que-aportó-el-despacho)
- [Sprint 79 (repregunta) — Prelación de pagos: ¿intereses antes que indexación? Contradice la regla general vigente](#sprint-79-repregunta--prelación-de-pagos-intereses-antes-que-indexación-contradice-la-regla-general-vigente)
- [Sprint 97/98 (datos pendientes) — Tablas completas de mortalidad de inválidos (hombres y mujeres) de la Superfinanciera](#sprint-9798-datos-pendientes--tablas-completas-de-mortalidad-de-inválidos-hombres-y-mujeres-de-la-superfinanciera)
- [Sprint 118 — Paquete de noviembre: seis reglas que cambiarían resultados (vacancia, festivo nuevo, redondeo, pagos anticipados, notificación y vacancia por despacho)](#sprint-118--paquete-de-noviembre-seis-reglas-que-cambiarían-resultados-vacancia-festivo-nuevo-redondeo-pagos-anticipados-notificación-y-vacancia-por-despacho)
- [Sprint 119 — Cinco dudas que surgieron al aplicar las respuestas del 16/11/2026](#sprint-119--cinco-dudas-que-surgieron-al-aplicar-las-respuestas-del-16112026)
- [Sprint 120 — Dudas surgidas al implementar los Sprints 84, 85, 86/87, 94, 100, 105, 106 y 107](#sprint-120--dudas-surgidas-al-implementar-los-sprints-84-85-8687-94-100-105-106-y-107)
- [Sprint 121 — Horas extra, fruto civil y Suma Única con abonos: cuatro confirmaciones](#sprint-121--horas-extra-fruto-civil-y-suma-única-con-abonos-cuatro-confirmaciones)
- [Plantilla para sprints futuros](#plantilla-para-sprints-futuros)

---

## Sprint 18 (seguimiento 3) — Discrepancia numérica entre la tabla granular verificada (PSAA16-10554) y las "tarifas duras" que aportó el despacho

**Contexto:** la pregunta de seguimiento 2 (¿PCSJA20-11556 y PSAA16-10554 son el mismo acuerdo?) ya se
contestó (22/08/2026, ver `Preguntas-Para-Abogado-Respondidas.md`, Sprint 18): el despacho confirmó que
"el marco tarifario unificado obligatorio se rige por el Acuerdo PSAA16-10554" — coincide exactamente con
lo ya implementado y verificado contra la fuente oficial (ramajudicial.gov.co), así que no hubo que tocar
código por ese punto. La misma respuesta también confirmó, sin ambigüedad, que las agencias en derecho se
tasan con "ponderación inversa: a mayor valor, menor porcentaje, respetando los topes" — exactamente la
aproximación que ya usa `_interpolar_dentro_de_rango` (`app/engine/costs/agencias_en_derecho.py`), citando
el mismo fundamento (Parágrafo 3, Art. 3 del Acuerdo). Ninguno de esos dos puntos requiere cambio de
código.

La respuesta agregó además, bajo el encabezado "Qué podría hacerse", una tabla de "tarifas duras" para 3
categorías (Procesos Declarativos, Procesos Ejecutivos, Sucesiones y Liquidaciones) con rangos min/max que
**no coinciden** con los ya transcritos en `TARIFAS_AGENCIAS_EN_DERECHO` desde el texto oficial del Acuerdo
(ej. la respuesta da "Procesos Declarativos, Primera Instancia, Mayor Cuantía: 0.03-0.075", un rango
distinto al que trae la tabla granular actual para esa misma categoría). Como la tabla granular actual fue
verificada independientemente contra la fuente oficial del acuerdo, y como el propio despacho ya se
equivocó una vez citando un número de acuerdo inexistente ("PCSJA20-11556", Sprint 18 original) y ahora
enmarca esta tabla como una sugerencia tentativa ("por ahora se sabe", "qué **podría** hacerse", no una
instrucción categórica de reemplazo), esta rutina NO sobrescribió la tabla ya verificada con estos números
nuevos — el riesgo de introducir una cifra legal incorrecta sin una fuente primaria que la respalde es
mayor que el de dejar la pregunta abierta.

**Pregunta:** ¿la tabla de "tarifas duras" de la respuesta del 22/08/2026 debe **reemplazar** la tabla
granular ya implementada (transcrita y verificada contra el texto oficial del Acuerdo PSAA16-10554 en
ramajudicial.gov.co), o es una aproximación/resumen que no debe usarse tal cual? Si debe reemplazarla,
¿pueden confirmar la fuente exacta de esos números (para volver a verificarlos contra el texto oficial
antes de tocar el motor de cálculo)?

**Qué necesito exactamente:** un sí/no sobre si se reemplaza la tabla granular actual, y si es sí, el
artículo/página exacto del Acuerdo (o la fuente que corresponda) de donde salen esos rangos, para
verificarlos igual que se hizo con la tabla que ya está implementada.

**Respuesta del despacho:** No, la tabla de "tarifas duras" NO debe reemplazar la tabla granular oficial. La tabla granular del Acuerdo PCSJA20-11556 (que actualizó al PSAA16-10554) es el motor maestro obligatorio (Art. 366, num. 4, CGP). El rango sugerido (ej. 3% a 7.5%) corresponde exclusivamente al Artículo 2, numeral 1 para "Procesos Declarativos Verbales en Primera Instancia con pretensiones pecuniarias de Mayor Cuantía". El software debe usar la tabla granular como base y, si se permite un override manual, emitir una alerta de validación si se sale de los rangos del Acuerdo.

**Fecha:** 16/11/2026

**Repregunta (2026-11-19) — por qué:** la primera parte de la respuesta es clara y ya coincide con el software
(la tabla granular manda; las "tarifas duras" no la reemplazan; no hay cambio de código por eso). Pero la
respuesta llama a la tabla "del Acuerdo **PCSJA20-11556** (que actualizó al PSAA16-10554)", y el 22/08/2026 el
mismo despacho confirmó por escrito que el marco vigente es el **PSAA16-10554**, que es el que está
transcrito y verificado contra ramajudicial.gov.co. Si de verdad existe un acuerdo posterior que modificó
las tarifas, el software podría estar usando porcentajes desactualizados.

**Qué necesito exactamente:** (a) ¿existe el Acuerdo PCSJA20-11556 y modificó las tarifas de agencias en
derecho del PSAA16-10554? Si es así, el texto oficial (enlace o PDF) para transcribir y verificar la tabla
nueva. Si fue una confusión de número, basta con "rige el PSAA16-10554". (b) Sobre el "override manual con
alerta": confirmar que se puede permitir un porcentaje manual de agencias en derecho siempre que el software
muestre una alerta cuando quede fuera del rango del Acuerdo (sin bloquear).

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 79 (repregunta) — Prelación de pagos: ¿intereses antes que indexación? Contradice la regla general vigente

**Contexto:** el 16/11/2026 el despacho respondió el Sprint 79 (ver `Preguntas-Para-Abogado-Respondidas.md`):
las costas nunca generan intereses (regla general) y la prelación de pagos es **1° costas, 2° intereses
moratorios, 3° indexación/reajuste, 4° capital**. La parte de las costas se está implementando.

**Por qué se repregunta:** desde el inicio del proyecto el software imputa cada abono en el orden
**indexación → intereses → capital**, en **todas** las áreas (es el "orden legal general" del motor). La
respuesta pone los intereses **antes** que la indexación. Cambiarlo altera el resultado de cualquier
liquidación con abonos e indexación, en las 6 áreas. Además, en Tributario el software usa ese mismo primer
lugar para las **sanciones** (orden sanciones → intereses → impuesto), aunque el Sprint 84 ya confirmó que en
Tributario la imputación debe ser proporcional (Art. 804 E.T.).

**Pregunta:** ¿confirman que, después de las costas, el abono debe ir primero a **intereses** y luego a
**indexación**, en todas las áreas (salvo Tributario, que va proporcional)? ¿O el orden indexación → intereses
→ capital que usa hoy el software es correcto y la respuesta del 16/11 fue un orden ilustrativo?

**Qué necesito exactamente:** "intereses antes que indexación" o "indexación antes que intereses", y si hay
áreas con orden distinto, cuáles.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 97/98 (datos pendientes) — Tablas completas de mortalidad de inválidos (hombres y mujeres) de la Superfinanciera

**Contexto:** el 16/11/2026 el despacho respondió el Sprint 97 (ver `Preguntas-Para-Abogado-Respondidas.md`):
el fruto civil va en el área Civil, sobre el rendimiento real del activo indexado por IPC, y las tablas de
mortalidad de inválidos "son dependencias de datos externos (SFC) que deben importarse como tablas
parametrizadas".

**Por qué se sigue preguntando:** la respuesta confirma cómo usarlas, pero el software todavía **no tiene los
datos**: la tabla de hombres inválidos está incompleta y la de mujeres inválidas no existe. Sin ellas no se
pueden programar los cálculos que dependen de la mortalidad de inválidos (Sprints 97/98 y la renta vitalicia
del Sprint 89).

**Qué necesito exactamente:** el archivo oficial (PDF o Excel de la Superintendencia Financiera, Resolución
1555 de 2010 o la vigente) con las tablas completas de mortalidad de inválidos, hombres y mujeres, por edad.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 118 — Paquete de noviembre: seis reglas que cambiarían resultados (vacancia, festivo nuevo, redondeo, pagos anticipados, notificación y vacancia por despacho)

**Contexto (explicado desde cero):** el equipo recibió un paquete de cambios al motor de cálculo ("BASTIUM
VERSION NOVIEMBRE", auditoría del 12/11/2026). Se integraron solo las mejoras que **no cambian ninguna cifra**
(ver `Pendientes.md`, Sprint 118). Las seis reglas de abajo **sí cambiarían plazos o montos**, así que no se
aplican hasta que el despacho las confirme. Cada pregunta explica por qué se hace.

**Pregunta 1 — Último día de la vacancia judicial de fin de año (repregunta del Sprint 6).**
El 27/07/2026 el despacho respondió por escrito: *"Excluir del 20 de diciembre al **11** de enero de cada año
(inclusive). El 12 de enero es hábil"*, y así funciona hoy el software. El paquete de noviembre sostiene que la
norma (Ley 31 de 1971, art. 1) fija la vacancia del 20 de diciembre al **10** de enero, inclusive.
*Por qué se vuelve a preguntar:* las dos fuentes se contradicen, y la diferencia mueve vencimientos reales. Por
ejemplo, un término de 5 días hábiles contado desde el 05/01/2028 vence hoy el **18/01/2028**; con la regla del
10 de enero vencería el **17/01/2028**. Pasa en los años en que el 11 de enero cae entre semana y no es festivo
(2024, 2028, …).
¿Cuál es el último día de vacancia: el 10 o el 11 de enero?

**Pregunta 2 — Festivo nuevo: Día de Nuestra Señora del Rosario de Chiquinquirá.**
La librería de festivos que usa el software (versión 0.108) incluye desde 2026 este festivo, trasladado al
lunes: 13/07/2026, 12/07/2027. El calendario propio que traía el paquete **no lo tiene**.
*Por qué se pregunta:* si es un festivo oficial vigente, el software ya lo aplica bien y el calendario del
paquete está desactualizado; si no lo es, hoy el software estaría corriendo plazos un día de más. Por ejemplo,
3 días hábiles desde el 09/07/2026 vencen hoy el **15/07/2026**; sin ese festivo vencerían el **14/07/2026**.
¿Es un festivo nacional oficial desde 2026? Si es posible, indiquen la norma.

**Pregunta 3 — Redondeo del interés: ¿por día o una sola vez?**
Hoy el software calcula el interés de cada día y lo redondea a centavos antes de sumarlo. El paquete propone
sumar sin redondear y redondear una sola vez por tramo, que es lo que da una calculadora o un Excel. Ejemplo del
paquete ($10.000.000 al 6 % anual, abono de $300.000 el 01/06/2024, corte 01/01/2025): intereses causados
**$599.879,94** hoy frente a **$599.880,11** redondeando una vez, que es el valor verificado a mano.
*Por qué se pregunta:* la diferencia es de centavos o pocos pesos, pero hace que la liquidación no se pueda
reproducir exactamente a mano por el juez o la contraparte. Cambiarlo altera todas las liquidaciones.
¿El despacho liquida (a) redondeando solo el total del período, o (b) redondeando cada día? Si no hay
criterio, ¿se adopta (a)?

**Pregunta 4 — Pagos anticipados.**
Un abono hecho **antes** del primer vencimiento, cuando todavía no hay nada exigible: ¿se imputa a las cuotas
que vencen después (reduce el capital futuro) o queda como saldo a favor del deudor hasta que exista una
obligación exigible? El paquete lo trata como saldo a favor con una alerta.
*Por qué se pregunta:* ninguna respuesta anterior lo cubre, y cada opción da un saldo distinto.

**Pregunta 5 — Notificación por mensaje de datos.**
El software asume que la notificación digital se entiende surtida **2 días hábiles después del envío** (regla
tomada del documento de requisitos, pág. 4), sin citar artículo.
*Por qué se pregunta:* el paquete la marca como supuesto no confirmado. ¿Cuál es la norma exacta (¿art. 8 de la
Ley 2213 de 2022?) y el cómputo: los dos días, ¿empiezan al día hábil siguiente al envío? Un ejemplo con fechas
ayudaría.

**Pregunta 6 — ¿La vacancia aplica igual en todos los despachos?**
Hoy la vacancia (fin de año y Semana Santa) se aplica a todos los términos por igual. El paquete señala que no
aplica igual a tutela, hábeas corpus, algunos despachos penales ni a términos administrativos.
*Por qué se pregunta:* si el bufete lleva procesos donde los términos corren en vacancia, el software los
estaría alargando.
¿Con qué tipos de proceso o despacho trabaja el bufete en los que la vacancia **no** suspende los términos?

**Relacionado (no se repite aquí):** la convención de tasa del art. 1617 C.C. (lineal 6 %/365 frente a la
plantilla mensual) sigue abierta en la sección Sprint 76 de este archivo. El paquete también la necesita.

**Qué necesito exactamente:** una respuesta corta por pregunta: (1) "10" u "11"; (2) sí/no y la norma; (3) "a"
o "b"; (4) "imputar" o "saldo a favor"; (5) el artículo y un ejemplo con fechas; (6) la lista de tipos de
proceso o despacho en los que la vacancia no suspende términos, o "ninguno".

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 119 — Cinco dudas que surgieron al aplicar las respuestas del 16/11/2026

**Contexto:** con las respuestas del 16/11/2026 se implementaron los Sprints 70/91, 76, 79, 95, 96 y 110 (ver
`Pendientes.md`, Sprint 119). Al programarlos aparecieron cinco puntos que las respuestas no cubren. En todos se
aplicó la opción más conservadora y se dejó anotada aquí; nada de esto bloquea el uso actual.

**Pregunta 1 — Horas extra festivas antes del 1-jul-2025 (Sprint 95).**
El despacho dio los factores de HEFD/HEFN desde el 1-jul-2025 (tramos de la Ley 2466). *Por qué se pregunta:* para
horas causadas antes de esa fecha el software no tiene un factor confirmado y hoy exige que el usuario lo ingrese a
mano. La práctica tradicional (recargo festivo del 75 %) daría HEFD = 2,00 y HEFN = 2,50. ¿Se usan esos factores
antes del 1-jul-2025?

**Pregunta 2 — Auxilio de transporte en trabajo doméstico por días (Sprint 96).**
*Por qué se pregunta:* la respuesta fija la fórmula, pero no estos detalles, que cambian el resultado:
(a) el tope de 2 SMMLV, ¿se compara contra el salario mensual **proporcional** a los días trabajados (lo que hace hoy
el software) o contra el salario de tiempo completo (salario diario × 30)?; (b) ¿aplica también a contratos con
salario **mensual** (hoy solo se aplica al salario pactado por día)?; (c) ¿entra en la base de **vacaciones** (hoy
solo cesantías y prima, como dice la respuesta)?; (d) por favor verificar la serie de valores anuales cargada, de
$61.500 (2010) a $249.095 (2026), contra los decretos.

**Pregunta 3 — Vigencia de la Ley 797/2003 (Sprint 70).**
La respuesta fija su vigencia el **29/01/2003**. *Por qué se pregunta:* la plantilla P9 del despacho y la versión
anterior del software aplicaban la fórmula de la Ley 797 "desde 2004". Con la fecha nueva, una pensión causada entre
el 29/01/2003 y el 31/12/2003 cambia de fórmula. ¿Se confirma el 29/01/2003?

**Pregunta 4 — Indexación IPC del Art. 867-1 E.T. después del último mes de usura certificado (Sprint 110).**
Se aplicó "nunca extrapolar": el interés se calcula solo hasta el último día certificado. *Por qué se pregunta:* la
indexación IPC del rubro de impuesto está topada por la usura plena, y sin tasa certificada no se puede comprobar ese
tope, así que también se suspendió. ¿Es correcto suspender la indexación, o debe seguir corriendo sin tope hasta el
corte?

**Pregunta 5 — Tasas comerciales pactadas (Art. 884 C.Co.) (Sprint 76).**
El interés civil del 6 % y las tasas pactadas simples ya usan la fórmula lineal. *Por qué se pregunta:* las tasas
remuneratorias y moratorias **pactadas** en Comercial se dejaron en efectiva compuesta, porque se pactan como
efectivas anuales y se comparan contra la usura. La respuesta habla del "cobro del 6 % en litigios comerciales
simples" pero no de las tasas pactadas. ¿Las tasas pactadas en Comercial siguen en efectiva compuesta?

**Qué necesito exactamente:** (1) sí/no a 2,00/2,50; (2) a: "proporcional" o "tiempo completo", b: sí/no, c: sí/no,
d: confirmación o valores corregidos; (3) sí/no; (4) "suspender" o "seguir sin tope"; (5) sí/no.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 120 — Dudas surgidas al implementar los Sprints 84, 85, 86/87, 94, 100, 105, 106 y 107

**Contexto:** con las respuestas del 16/11/2026 se implementaron 8 sprints más (ver `Pendientes.md`, Sprint 120).
En cada punto de abajo el software aplicó la opción más prudente y la dejó documentada; nada de esto impide usar
lo ya construido, pero cada respuesta puede cambiar una cifra.

**Pregunta 1 — Tope suspensivo tributario (Sprint 84).** *Por qué:* la respuesta dio las fórmulas (admisión + 24
meses; notificación + 11 días) pero no los bordes. Hoy: (a) el día del tope y el día de reanudación **sí** causan
interés (solo se suspenden los días intermedios); (b) los "11 días" son calendario; (c) para marcar la demanda se
exige también la fecha de notificación de la sentencia, así que no se puede registrar una demanda en curso sin
sentencia. ¿Es correcto (a), (b) y cómo se liquida una demanda todavía sin sentencia?

**Pregunta 2 — Retroactivo pensional (Sprint 85).** *Por qué:* (a) el Art. 141 habla de la tasa "vigente en el
momento en que se efectúe el pago"; el software aplica la usura certificada de **cada día** de mora. ¿Cuál se
usa? (b) Se supuso que cada mesada es exigible el último día de su mes y la mora corre desde el día siguiente.
(c) El reajuste anual de la mesada (Art. 14 Ley 100) no está confirmado: hoy el usuario digita el porcentaje de
cada año. ¿Se usa el IPC del año anterior? (d) El primer mes se prorratea sobre 30 días.

**Pregunta 3 — Cálculo actuarial (Sprints 86/87).** *Por qué:* (a) la respuesta no dice cómo se obtiene la pensión
de referencia (PR), que hoy se digita; (b) no dice la base de días para pasar fechas a años en `t`, `n` y `t1`;
(c) el prorrateo de la DTF pensional se aplicó como exponente (DTF^(días/días del año)); ¿o es lineal?; (d) en
la tabla entregada, FAC1 de mujeres es exactamente FAC1 de hombres corrida 5 años, y el Salario Medio Nacional
salta de 1,006649 (13 años) a 1,135599 (14 años). ¿Pueden confirmar que la tabla está bien transcrita?

**Pregunta 4 — Contrato realidad (Sprint 94).** *Por qué:* (a) para el Decreto 0320/2026 solo se dio el tope de
2026 ($2.968.262); desde 2027 el software pide el tope. ¿Cuál es? (b) ¿El porcentaje de la bonificación se aplica
sobre asignación básica + gastos de representación? (c) ¿Aplica a todo el sector público o solo a territoriales?
(d) Salud (12,5 %) y pensión (16 %) no tienen vigencias históricas cargadas; los años anteriores a 2007/2008 usan
esos mismos porcentajes. ¿Pueden dar los históricos?

**Pregunta 5 — Fruto civil (Sprint 100).** *Por qué:* se usó el IPC de cierre de cada mes, gastos de conservación
por su valor nominal (sin indexar) y prorrateo por días calendario; el período lo fija el usuario. ¿Es correcto?
¿Y cómo se aplica la distinción del Art. 964 entre poseedor de buena y mala fe (desde cuándo se deben los frutos)?

**Pregunta 6 — Catálogo de procesos (Sprint 105).** *Por qué:* (a) la "checklist de obligaciones predefinidas"
por tipo de proceso no se definió: ¿qué obligaciones trae cada tipo? (b) El "Procedimiento Sancionatorio
Contractual (Ley 1474)" se asoció al área Sancionatorio, que hoy calcula multas en SMLMV/UVT. ¿Es correcto?

**Pregunta 7 — Título ejecutivo (Sprint 106).** *Por qué:* la fecha límite de prescripción se cuenta desde la
**fecha de exigibilidad** y las obligaciones nuevas usan esa misma fecha por defecto. ¿Es la fecha correcta en
ambos casos (o la de ejecutoria)?

**Pregunta 8 — Vista "Ver con/sin indexación" (Sprint 107).** *Por qué:* en modo "Con indexación" se enciende la
indexación IPC pero no se fuerza el interés sobre capital indexado (Suma Única). ¿Debería encenderse también?

**Qué necesito exactamente:** una respuesta corta por pregunta y letra; donde se piden datos (topes, históricos,
checklist), el valor o el documento fuente.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 121 — Horas extra, fruto civil y Suma Única con abonos: cuatro confirmaciones

**Contexto:** ya están en la aplicación las horas extra de Laboral, el fruto civil en Civil y la Suma Única con
abonos tramo a tramo (ver `Pendientes.md`, Sprint 121). Estas cuatro decisiones las tomó el software de forma
prudente y pueden cambiar cifras.

**Pregunta 1 — Horas extra en la base de prestaciones (Sprint 95).** *Por qué:* hoy las horas extra se pagan como
rubro aparte y **no** entran en la base de cesantías, prima, vacaciones ni de la sanción moratoria. Si son
habituales, el Art. 127 CST podría exigir incluirlas. ¿Se incluyen? ¿Siempre o solo si son habituales?

**Pregunta 2 — Fruto civil con costas (Sprint 100).** *Por qué:* si la obligación de fruto civil tiene costas, hoy
se calculan sobre el total del fruto. ¿Es la base correcta?

**Pregunta 3 — Suma Única con abonos y tasa pactada (Sprint 104).** *Por qué:* el algoritmo tramo a tramo usa
siempre la tasa pura mensual 0,48676 % (6 % EA) que fijó el despacho; si la obligación tenía otra tasa pactada, no
se aplica y el software avisa. ¿Es correcto ignorar la tasa pactada en este algoritmo?

**Pregunta 4 — Mes comercial en el tramo a tramo (Sprint 104).** *Por qué:* los días de cada tramo se cuentan como
días comerciales (mes de 30 días, año de 360), como en el pseudocódigo del despacho. ¿Se confirma esa convención
de conteo?

**Qué necesito exactamente:** sí/no por pregunta y, en la 1, desde cuándo una hora extra se considera habitual.

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
