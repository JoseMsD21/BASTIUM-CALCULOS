# Preguntas para el abogado / despacho — BASTIUM Cálculos

## Instrucciones de uso

**Para Jose (quien maneja este documento):**

1. Copia todo este documento (o solo la sección del sprint que te interese) y pégalo en un Word.
2. Envíalo al abogado o despacho correspondiente. Cada pregunta tiene un espacio en blanco
   ("**Respuesta del despacho:**") para que ellos escriban la respuesta directamente ahí, sin tener que
   reformatear nada.
3. Cuando te devuelvan las respuestas, cada sección está identificada con el número de Sprint al que
   corresponde en `Pendientes.md` — busca ese mismo número de sprint en `Pendientes.md` (sección
   "**Estado:**" de cada sprint) y pega la respuesta ahí, o dile a Claude Code "actualiza el Sprint N con
   esta respuesta del abogado: [pega el texto]" y él se encarga de dejarlo consistente en ambos documentos.
4. Este documento es un documento **vivo**: cada vez que un sprint nuevo tenga una decisión legal sin
   confirmar o una fuente que falte, se le agrega una sección nueva siguiendo la plantilla del final. No
   hace falta reescribir las secciones ya respondidas.

**Para el abogado / despacho que responde:**

Este documento acompaña el desarrollo de BASTIUM, un software de liquidación de procesos judiciales
(cálculo de capital, intereses, indexación, prescripción, etc.) para uso interno de un despacho. Cada
sección de abajo describe, en lenguaje llano, una decisión de cálculo que el desarrollo tomó **sin tener
una fuente jurídica 100% confirmada**, o una pregunta puntual sobre cuál de varias reglas posibles debe
aplicar el software. No hace falta leer código ni tener conocimientos técnicos — cada pregunta está escrita
para responderse con una confirmación, una corrección, o el dato/documento que haga falta aportar.

---

## Índice

- [Sprint 2 — Área Comercial](#sprint-2--área-comercial)
- [Sprint 3 — Área Laboral](#sprint-3--área-laboral)
- [Sprint 4 — Sancionatorio y Honorarios](#sprint-4--sancionatorio-y-honorarios)
- [Sprint 5 — Datos históricos (UVT)](#sprint-5--datos-históricos-uvt)
- [Sprint 6 — Calendario de días hábiles](#sprint-6--calendario-de-días-hábiles)
- [Sprint 7 — Prescripción y caducidad](#sprint-7--prescripción-y-caducidad)
- [Sprint 8 — Indexación IPC Civil/Familia](#sprint-8--indexación-ipc-civilfamilia)
- [Sprint 11 — Derecho Tributario (DIAN)](#sprint-11--derecho-tributario-dian)
- [Sprint 12 — TRM y moneda extranjera](#sprint-12--trm-y-moneda-extranjera)
- [Sprint 13 — Motor de reglas / parámetros legales](#sprint-13--motor-de-reglas--parámetros-legales)
- [Sprint 15 — Tributario: sanciones e imputación](#sprint-15--tributario-sanciones-e-imputación)
- [Sprint 16 — Seguridad social e incapacidades laborales](#sprint-16--seguridad-social-e-incapacidades-laborales)
- [Sprint 17 — Módulo pensional (IBL, tasa de reemplazo, semanas)](#sprint-17--módulo-pensional-ibl-tasa-de-reemplazo-semanas)
- [Sprint 18 — Costas judiciales (tabla de rangos)](#sprint-18--costas-judiciales-tabla-de-rangos)
- [Sprint 30 — Posible error de un día](#sprint-30--posible-error-de-un-día)
- [Plantilla para sprints futuros](#plantilla-para-sprints-futuros)

---

## Sprint 2 — Área Comercial

**Contexto:** Cuando alguien pacta un interés más alto que la tasa de usura permitida, la ley dice que ese
exceso no es válido. Pero hay dos formas posibles de que el software reaccione: (a) rechazar de plano la
liquidación con un error, obligando a corregir la tasa antes de continuar, o (b) aceptar la liquidación
pero recortar automáticamente la tasa al máximo legal permitido y seguir calculando con ese tope. El PDF de
requisitos de BASTIUM menciona las dos variantes en secciones distintas, sin decidir cuál usar.

**Pregunta:** ¿Cuál de las dos debe hacer el software cuando detecta una tasa pactada por encima de la
usura: rechazar con error, o recortar automáticamente al tope legal y continuar?

**Qué necesito exactamente:** Una de las dos opciones (rechazar / recortar automáticamente), o una tercera
si aplica (ej. "depende de si hay o no acción judicial ya iniciada").

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 3 — Área Laboral

**Contexto:** Ya resuelto en su mayoría — quedan dos puntos documentados como pendientes explícitos (no
olvidos) al cerrar el sprint, que siguen sin confirmación jurídica formal.

**Pregunta 1:** ¿Al calcular los días trabajados de un contrato para efecto de cesantías/prestaciones,
el primer día de labor debe contarse como "trabajado" (conteo inclusivo) o no (resta simple de fechas)?
Hoy el software usa resta simple (ej. contrato de 1-ene a 31-dic de un año bisiesto da 365 días, no 366).
Esta misma pregunta aplica también al Sprint 17 y al Sprint 30 — es una sola convención que se necesita
para todo el sistema, no una por sprint.

**Qué necesito exactamente:** Confirmar si la convención actual (no inclusiva) es la correcta según la
práctica laboral colombiana, o si debe cambiarse a inclusiva.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 4 — Sancionatorio y Honorarios

**Contexto:** El PDF de requisitos de BASTIUM tiene una inconsistencia interna: en una sección dice que la
suma de honorarios fijos + cuota litis no puede superar el 50% del beneficio obtenido por el cliente, y en
otra sección (dedicada específicamente a "Litigio y Cobro de Honorarios") dice 30%. El desarrollo decidió
—junto con Jose, no de forma unilateral— aplicar **ambos topes simultáneamente**: 30% individual sobre la
cuota litis sola, y 50% total sobre honorarios fijos + cuota litis juntos. Es una interpretación razonable
para no elegir un número al azar, pero no ha sido confirmada por un abogado.

**Pregunta:** ¿Es correcto aplicar ambos topes simultáneamente (30% a la cuota litis sola, 50% al total), o
debería ser solo uno de los dos como tope único?

**Qué necesito exactamente:** Confirmación de la interpretación actual, o la regla correcta con su fuente
normativa si es distinta.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 5 — Datos históricos (UVT)

**Contexto:** El software ya tiene cargadas las series históricas de Salario Mínimo, IPC e Interés Bancario
Corriente/Usura desde 1997-2024 en adelante (verificadas contra el PDF y fuentes externas). La UVT (Unidad
de Valor Tributario, usada por la DIAN) también quedó cargada completa 2006-2026, pero **no viene del PDF
de BASTIUM** — el PDF solo menciona un valor aislado que en realidad correspondía a otro año. La serie que
hoy usa el software se armó cruzando 3 fuentes externas independientes.

**Pregunta:** ¿Pueden confirmar que la tabla de UVT que usamos (2006 = $20.000 ... 2026 = $52.374,
resolución DIAN de cada año) coincide con sus registros, o tienen una fuente oficial distinta que debamos
usar?

**Qué necesito exactamente:** Un sí/no de confirmación, o la tabla corregida si encuentran alguna
diferencia con sus registros.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 6 — Calendario de días hábiles

**Contexto:** El software calcula días hábiles judiciales (excluyendo sábados, domingos y festivos
colombianos) usando una librería de código abierto (`holidays`, país Colombia) en vez de una tabla propia
transcrita a mano. El PDF menciona que existen "vacancias judiciales" (pausas del sistema judicial, ej. fin
de año) pero no da fechas exactas, así que el software **no las modela** — solo excluye fines de semana y
festivos oficiales.

**Pregunta:** Para el cómputo de términos procesales, ¿hace falta modelar también las vacancias judiciales
como días no hábiles adicionales, o basta con festivos + fines de semana como está hoy?

**Qué necesito exactamente:** Sí/no, y si la respuesta es sí, las fechas exactas de vacancia judicial que
deban aplicar (son fijas cada año, ej. mediados de diciembre a mediados de enero).

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 7 — Prescripción y caducidad

**Contexto:** El software calcula plazos de prescripción/caducidad para varios tipos de acción. Un caso
puntual: la ley cambiaria (letras, cheques, pagarés) tiene tres plazos distintos según el tipo de acción
(directa: 3 años; de regreso del tenedor: 1 año; entre obligados de regreso: 6 meses). El PDF menciona el
plazo de 6 meses en una sección distinta a los otros dos, y el desarrollo interpretó que es un tercer
supuesto real (no un error del documento). Además, cualquier tipo de caducidad que no sea el único caso que
trae el PDF con plazo confirmado (impugnación de ineficacia societaria, 5 años) exige que el usuario
ingrese el plazo manualmente — el software no lo asume.

**Pregunta:** ¿Confirman los tres plazos cambiarios (3 años / 1 año / 6 meses) tal como están descritos
arriba? ¿Hay otros tipos de proceso con plazo de caducidad fijo y conocido que debamos precargar en el
software en vez de pedir que se ingrese manualmente cada vez?

**Qué necesito exactamente:** Confirmación de los 3 plazos cambiarios, y opcionalmente una lista de otros
plazos de caducidad frecuentes en la práctica del despacho.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 8 — Indexación IPC Civil/Familia

**Contexto:** Cuando se actualiza un capital histórico con el IPC, la fórmula del PDF supone que existe
una certificación mensual del IPC. En la práctica, la fuente que tenemos solo trae variación **anual**, así
que el software interpola entre los índices de cierre de año (31 de diciembre de cada año) en vez de entre
meses. Además, para fechas del año en curso (donde aún no hay IPC de cierre de año publicado), el software
usa el IPC del año anterior como aproximación.

**Pregunta:** ¿Esta aproximación (interpolar entre cierres de año en vez de entre meses, y usar el IPC del
año anterior para el año en curso) es aceptable para el uso que le da el despacho, o hace falta una fuente
de IPC mensual más precisa?

**Qué necesito exactamente:** Sí/no de aceptación, o la fuente de IPC mensual si se necesita mayor
precisión.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 11 — Derecho Tributario (DIAN)

**Contexto:** Este fue el primer sprint que agregó liquidaciones tributarias (DIAN) al software, un
dominio completamente nuevo para BASTIUM. La decisión de negocio (ya tomada) fue construir únicamente
interés moratorio tributario y depuración de Renta Líquida Gravable en una primera etapa, dejando sanciones
e imputación para un sprint posterior (ya completado en el Sprint 15, ver abajo).

**Pregunta:** No hay pregunta pendiente de este sprint puntual — se deja la sección aquí solo como
referencia, por si el despacho quiere confirmar que el área Tributaria en general sí es prioritaria para el
producto (ya se construyó, pero es bueno tener la confirmación explícita).

**Qué necesito exactamente:** Nada urgente — opcional.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 12 — TRM y moneda extranjera

**Contexto:** Para obligaciones comerciales en dólares, el software convierte el monto a pesos usando la
Tasa Representativa del Mercado (TRM) que el abogado ingresa manualmente por cada obligación (no hay una
tabla histórica automática de TRM diaria, porque el PDF de requisitos no la trae). La conversión se hace
una sola vez, al inicio de la liquidación, no de forma continua con cada abono.

**Pregunta:** ¿Es correcto que la conversión a pesos se haga una sola vez al inicio (con la TRM de la
fecha de la obligación), o debería recalcularse con la TRM vigente en la fecha de cada pago/abono?

**Qué necesito exactamente:** Confirmación de cuál de las dos formas es la jurídicamente correcta (Art.
874 C.Co.).

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 13 — Motor de reglas / parámetros legales

**Contexto:** Este sprint fue una decisión de arquitectura (no una pregunta legal): se decidió que las
tasas, topes y porcentajes legales (usura, cuota litis, SMLMV, IPC, etc.) vivan en una tabla editable desde
la pantalla de "Parámetros" del software, para que puedan actualizarse sin necesitar un programador. No hay
pregunta jurídica pendiente aquí.

**Pregunta:** Ninguna — sección informativa. Si en el futuro alguien del despacho va a ser quien actualice
esos parámetros directamente desde la pantalla de Parámetros, avisar para preparar una guía de uso corta.

**Qué necesito exactamente:** Nada urgente — opcional.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 15 — Tributario: sanciones e imputación

**Contexto:** El software calcula 3 sanciones tributarias (extemporaneidad, inexactitud, error aritmético)
con un piso legal de 10 UVT, y aplica el orden de pago que exige el PDF para tributario (sanciones →
intereses → impuesto). El PDF (pág. 40) además advierte que "no se pueden cobrar simultáneamente intereses
moratorios y actualización monetaria si esto conduce a una tasa usuraria o doble pago por el mismo
concepto" — esta validación quedó **documentada como advertencia**, no como un bloqueo automático en el
software, porque hoy no hay ningún caso de uso real que combine ambas cosas en el mismo expediente
tributario.

**Pregunta:** ¿Existen casos reales del despacho donde sí se combinen intereses moratorios y actualización
monetaria en un mismo proceso tributario? Si es así, necesitamos un ejemplo real para poder construir la
validación automática correctamente.

**Qué necesito exactamente:** Sí/no, y si es sí, un caso de ejemplo (montos, fechas, tipo de sanción).

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 16 — Seguridad social e incapacidades laborales

**Contexto:** Ya resuelto en su mayoría con confirmación del usuario, pero dos tablas de porcentajes se
completaron con **fuentes externas al PDF** (verificadas, no inventadas) porque el PDF de BASTIUM solo da
los valores extremos:
- Niveles de riesgo ARL II, III y IV (el PDF solo da el nivel I y el nivel V) — se usó el Decreto
  1607/2002: II = 1.044%, III = 2.436%, IV = 4.350%.
- Tramos del Fondo de Solidaridad Pensional -FSP- (el PDF solo dice "escala progresiva desde 1% hasta 2%",
  sin tramos exactos) — se usó la Ley 797/2003 art. 8: de 4 a 16 SMMLV = 1%, 16-17 = 1.2%, 17-18 = 1.4%,
  18-19 = 1.6%, 19-20 = 1.8%, más de 20 = 2%.

**Pregunta:** ¿Confirman que estos dos porcentajes/tablas (ARL II-IV del Decreto 1607/2002, y FSP de la
Ley 797/2003 art. 8) son los vigentes y correctos a la fecha?

**Qué necesito exactamente:** Sí/no de confirmación, o la tabla corregida si alguna norma posterior cambió
estos porcentajes.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 17 — Módulo pensional (IBL, tasa de reemplazo, semanas)

**Contexto:** Este es el sprint en curso — el de mayor incertidumbre de dominio de todo el desarrollo. El
PDF de BASTIUM solo trae la fórmula base de la tasa de reemplazo (`r = 65.5 − 0.5·s`), pero en la práctica
real colombiana (Ley 100 de 1993, art. 34) esa fórmula tiene además: un piso de 65%, un techo de 80%, y un
bono de +1.5% por cada 50 semanas cotizadas por encima de 1.300. Se implementó la fórmula completa
(verificada con fuentes externas, no solo la línea literal del PDF), pero sin confirmación directa de un
despacho jurídico.

**Pregunta 1:** ¿Confirman que la fórmula completa de tasa de reemplazo es correcta tal como está descrita
arriba (piso 65%, techo 80%, bono +1.5% cada 50 semanas sobre 1.300)?

**Pregunta 2:** ¿Tienen algún caso pensional real (de Colpensiones o de un proceso ya resuelto) con IBL,
semanas cotizadas y tasa de reemplazo ya calculados, que podamos usar como caso de prueba adicional al que
ya usamos (Sentencia SL138-2024, sobre el conteo de semanas)?

**Pregunta 3 (compartida con Sprint 3 y Sprint 30):** Para contar días de un periodo cotizado (ej. de una
fecha a otra), ¿el primer día debe contarse como cotizado (conteo inclusivo) o no (resta simple de
fechas)? Es la misma pregunta del Sprint 3, la respuesta aplica a los tres sprints por igual.

**Qué necesito exactamente:** Confirmación de la fórmula completa (pregunta 1); un caso real si existe
(pregunta 2, opcional); y la convención de conteo de días (pregunta 3).

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 18 — Costas judiciales (tabla de rangos)

**Contexto:** El PDF de BASTIUM menciona que las costas judiciales (agencias en derecho) se fijan según
rangos de porcentaje del Consejo Superior de la Judicatura (cita el Acuerdo PCSJA20-11556 como ejemplo,
"3% al 7% de las pretensiones reconocidas"), pero **no transcribe la tabla completa de rangos**. Este
acuerdo tampoco se consiguió durante los Sprints 4 ni 18 buscando en fuentes públicas. Hoy el software solo
permite ingresar el porcentaje de costas manualmente por cada obligación, sin calcularlo automáticamente
por rango de cuantía.

**Pregunta:** ¿Pueden aportar el texto completo (o al menos la tabla de rangos de cuantía y porcentaje) del
Acuerdo del Consejo Superior de la Judicatura que esté vigente hoy para costas judiciales/agencias en
derecho?

**Qué necesito exactamente:** El documento o la tabla completa (rango de cuantía desde/hasta → porcentaje
aplicable), o el nombre/número exacto del acuerdo vigente si no es el PCSJA20-11556.

**Respuesta del despacho:**


**Fecha:**

---

## Sprint 30 — Posible error de un día

**Contexto:** Una revisión de código encontró dos posibles errores sutiles de "un día" en el sistema, y
ambos necesitan confirmación jurídica antes de decidir si se corrigen (ya que corregirlos cambiaría el
resultado numérico de liquidaciones existentes):

1. Para decidir si una notificación de demanda "retrotrae" el efecto interruptor de la prescripción a la
   fecha de la demanda, el software hoy compara si pasaron `365 días o menos` entre la radicación y la
   notificación. En años bisiestos, 365 días puede ser un día calendario menos que "un año" real,
   activando la regla un día antes de lo que correspondería.
2. Para contar los días trabajados de un contrato (cesantías/prestaciones), el software resta las fechas
   sin sumar 1 (ej. un contrato de 1-ene a 31-dic de un año bisiesto da 365 días, no 366). Es la misma
   pregunta del Sprint 3 y el Sprint 17 sobre conteo inclusivo vs. no inclusivo.

**Pregunta 1:** Para prescripción, ¿"dentro de un año" debe interpretarse como fecha-a-fecha (ej. de
1-mar-2023 a 1-mar-2024, sin importar si hay bisiesto en medio), o como una cuenta fija de 365 días
corridos?

**Pregunta 2:** Ver Sprint 3/17 — es la misma pregunta de conteo inclusivo de días.

**Qué necesito exactamente:** La interpretación correcta para prescripción (pregunta 1). La pregunta 2 ya
está cubierta en la sección del Sprint 3.

**Respuesta del despacho:**


**Fecha:**

---

## Plantilla para sprints futuros

Copiar este bloque y completarlo cuando un sprint nuevo tenga una decisión legal sin confirmar o una fuente
que falte:

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
