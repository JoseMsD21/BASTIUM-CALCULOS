# Preguntas para el abogado — Respondidas (archivo) — BASTIUM Cálculos

Este archivo reúne las preguntas que el despacho **ya respondió de forma clara y completa**: la respuesta
no deja ambigüedad, no entra en conflicto con lo que el software ya construyó, y no requiere volver a
preguntar nada. Son la base normativa ya confirmada de cada sprint.

Si una pregunta fue respondida pero la respuesta **sí** generó una duda nueva, un conflicto con el código
existente, o sigue faltando un dato/documento para poder aplicarla, esa pregunta vive en
[`Preguntas-Para-Abogado-Abiertas.md`](Preguntas-Para-Abogado-Abiertas.md), no aquí.

Cada sección está identificada con el número de Sprint al que corresponde en `Pendientes.md` — para ver si
la corrección ya quedó programada, busca ese mismo número de sprint allá.

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
- [Sprint 15 — Tributario: sanciones e imputación](#sprint-15--tributario-sanciones-e-imputación)
- [Sprint 16 — Seguridad social e incapacidades laborales](#sprint-16--seguridad-social-e-incapacidades-laborales)
- [Sprint 17 — Módulo pensional (IBL, tasa de reemplazo, semanas)](#sprint-17--módulo-pensional-ibl-tasa-de-reemplazo-semanas)
- [Sprint 30 — Posible error de un día](#sprint-30--posible-error-de-un-día)

---

## Sprint 2 — Área Comercial

**Contexto:** Cuando alguien pacta un interés más alto que la tasa de usura permitida, la ley dice que ese
exceso no es válido. Pero hay dos formas posibles de que el software reaccione: (a) rechazar de plano la
liquidación con un error, obligando a corregir la tasa antes de continuar, o (b) aceptar la liquidación
pero recortar automáticamente la tasa al máximo legal permitido y seguir calculando con ese tope. El PDF de
requisitos de BASTIUM menciona las dos variantes en secciones distintas, sin decidir cuál usar.

**Pregunta:** ¿Cuál de las dos debe hacer el software cuando detecta una tasa pactada por encima de la
usura: rechazar con error, o recortar automáticamente al tope legal y continuar?

**Respuesta del despacho:**
Cuando un interés pactado supera la tasa de usura, la ley no permite simplemente "recortarlo" al tope legal. La sanción legal es la pérdida del exceso y la obligación de devolverlo doblado al deudor.
**Qué puede hacerse?:**

Crear un Trigger de Validación de Usura.
Si Tasa_Pactada > Tasa_Usura_Vigente:
NO recortar la tasa silenciosamente.
Calcular el exceso: Intereses_Cobrados_En_Exceso = Intereses_Cobrados - Intereses_Cobrados_Con_Tasa_Usura.
Calcular sanción: Sancion = Intereses_Cobrados_En_Exceso * 2.
Restar Sancion del saldo total de la obligación, generando un saldo a favor del deudor si la cifra resulta negativa.

**Fecha:** 27/07/2026

**Estado en el código:** Implementado (Sprint 2, corrección del 2026-08-01) — ver `Pendientes.md`.

---

## Sprint 3 — Área Laboral

**Contexto:** Ya resuelto en su mayoría — quedan dos puntos documentados como pendientes explícitos (no
olvidos) al cerrar el sprint, que seguían sin confirmación jurídica formal.

**Pregunta 1:** ¿Al calcular los días trabajados de un contrato para efecto de cesantías/prestaciones,
el primer día de labor debe contarse como "trabajado" (conteo inclusivo) o no (resta simple de fechas)?

**Respuesta del despacho:**
Existen dos lógicas de conteo dependiendo del rubro. Para prestaciones se usa un año comercial de 360 días, pero para pensiones la Corte Suprema obliga a usar días calendario reales (365/366). En ambos casos, el primer día cuenta (conteo inclusivo).

Fórmula base de días: Dias_Trabajados = (Fecha_Fin - Fecha_Inicio) + 1. (Se debe corrigir el error de la resta simple en todos los módulos).
Para Prestaciones (Cesantías/Primas): Usar la fórmula base bajo la premisa de meses de 30 días (año comercial de 360 días).
Para Densidad Pensional (Semanas): Usar la fórmula base con días calendario reales (365 o 366). Luego, Semanas_Cotizadas = Total_Dias_Reales / 7.

**Fecha:** 27/07/2026

**Estado en el código:** Respuesta clara y aplicable a Sprint 3, 17 y 30 por igual (conteo inclusivo,
`(Fecha_Fin - Fecha_Inicio) + 1`). Corrección de código pendiente de programar — ver `Pendientes.md`,
Sprint 3.

---

## Sprint 4 — Sancionatorio y Honorarios

**Contexto:** El PDF de requisitos de BASTIUM tiene una inconsistencia interna: en una sección dice que la
suma de honorarios fijos + cuota litis no puede superar el 50% del beneficio obtenido por el cliente, y en
otra sección (dedicada específicamente a "Litigio y Cobro de Honorarios") dice 30%. El desarrollo decidió
—junto con Jose, no de forma unilateral— aplicar **ambos topes simultáneamente**: 30% individual sobre la
cuota litis sola, y 50% total sobre honorarios fijos + cuota litis juntos. Es una interpretación razonable
para no elegir un número al azar, pero no había sido confirmada por un abogado.

**Pregunta:** ¿Es correcto aplicar ambos topes simultáneamente (30% a la cuota litis sola, 50% al total), o
debería ser solo uno de los dos como tope único?

**Respuesta del despacho:**
No se aplican ambos topes (30% y 50%) en cascada. El tope legal absoluto y definitivo es del 50% acumulado.
**Qué puede hacerse?:**

Crear validación de legalidad contractual: Total_Honorarios = Honorarios_Fijos + (Beneficio_Obtenido * Porcentaje_Cuota_Litis).
Si Total_Honorarios > (Beneficio_Obtenido * 0.50): El sistema debe emitir una alerta de riesgo disciplinario ("Honorarios Desproporcionados - Art. 35 Num. 4 Ley 1123/2007") y bloquear la liquidación o ajustar el excedente.

**Fecha:** 27/07/2026

**Estado en el código:** Implementado (Sprint 4, corrección del 2026-08-01) — ver `Pendientes.md`.

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

**Respuesta del despacho:**
La serie histórica cruzada por el equipo es correcta. La conversión de pesos a UVT tiene una regla de redondeo estricta.

Mantener la tabla UVT cargada (2006=$20.000 ... 2024=$47.065).
Regla de conversión y redondeo (Art. 868 E.T.): Al convertir pesos a UVT, si el resultado es mayor a $10.000, el sistema debe aproximar el valor al múltiplo de mil más cercano.
Usar la UVT del año gravable correspondiente al hecho generador para bases, y la UVT vigente al momento del pago para sanciones.

**Ampliación de respuesta (tabla completa con resolución DIAN por año):**
La Unidad de Valor Tributario (UVT) fue creada mediante la Ley 1111 de 2006 (modificando el Art. 868 del
Estatuto Tributario - E.T.) con el fin de unificar y facilitar el cumplimiento de las obligaciones
tributarias, reemplazando al salario mínimo como unidad de medida para impuestos, sanciones y cuantías.

Su valor se reajusta anualmente el 1 de enero de cada año, basándose en la variación del Índice de Precios
al Consumidor (IPC) para ingresos medios, certificado por el DANE para el periodo comprendido entre el 1 de
octubre del año anterior al gravable y la misma fecha del año precedente.

Dado que las fuentes suministradas al despacho solo mencionaban explícitamente el valor de 2023 ($42.412),
el resto de los valores de la tabla siguiente se proveen desde registros oficiales externos que el
despacho pide verificar de forma independiente para garantizar la precisión del software:

| Año  | Valor UVT     | Resolución de fijación (referencia externa)     |
|------|---------------|--------------------------------------------------|
| 2006 | $20.000       | Ley 1111 de 2006 (valor base inicial)             |
| 2007 | $20.974       | Resolución DIAN 15631 de 2006                     |
| 2008 | $22.054       | Resolución DIAN 15013 de 2007                     |
| 2009 | $23.763       | Resolución DIAN 011945 de 2008                    |
| 2010 | $24.555       | Resolución DIAN 012115 de 2009                    |
| 2011 | $24.755       | Resolución DIAN 012066 de 2010                    |
| 2012 | $26.049       | Resolución DIAN 000119 de 2011                    |
| 2013 | $26.841       | Resolución DIAN 000138 de 2012                    |
| 2014 | $26.841       | Resolución DIAN 000227 de 2013                    |
| 2015 | $27.485       | Resolución DIAN 000245 de 2014                    |
| 2016 | $28.279       | Resolución DIAN 000115 de 2015                    |
| 2017 | $29.753       | Resolución DIAN 000071 de 2016                    |
| 2018 | $31.859       | Resolución DIAN 000063 de 2017                    |
| 2019 | $34.270       | Resolución DIAN 000056 de 2018                    |
| 2020 | $35.607       | Resolución DIAN 000084 de 2019                    |
| 2021 | $35.607       | Resolución DIAN 000111 de 2020                    |
| 2022 | $36.308       | Resolución DIAN 000140 de 2021                    |
| 2023 | $42.412       | Resolución DIAN 001264 de 2022                    |
| 2024 | $47.065       | Resolución DIAN 000187 de 2023                    |
| 2025 | (por definir) | Se fija en octubre/noviembre de 2024              |
| 2026 | $52.374*      | (*valor proyectado, según consulta del despacho)  |

**Fecha:** 27/07/2026

**Estado en el código:** Tabla histórica UVT 2006-2026 cargada y verificada (Sprint 14) — ver `Pendientes.md`.

---

## Sprint 6 — Calendario de días hábiles

**Contexto:** El software calcula días hábiles judiciales (excluyendo sábados, domingos y festivos
colombianos) usando una librería de código abierto (`holidays`, país Colombia) en vez de una tabla propia
transcrita a mano. El PDF menciona que existen "vacancias judiciales" (pausas del sistema judicial, ej. fin
de año) pero no da fechas exactas, así que el software **no las modelaba** — solo excluía fines de semana y
festivos oficiales.

**Pregunta:** Para el cómputo de términos procesales, ¿hace falta modelar también las vacancias judiciales
como días no hábiles adicionales, o basta con festivos + fines de semana?

**Respuesta del despacho:**
Los fines de semana y festivos no son suficientes. Las vacancias judiciales son obligatorias y deben restarse del cómputo de términos.
Instrucción de desarrollo:

Actualizar el motor de calendario para excluya automáticamente:
Fines de semana (Sábado y Domingo).
Festivos oficiales (Ley 51 de 1883).
Vacancia de Fin de Año: Excluir del 20 de diciembre al 11 de enero de cada año (inclusive). El 12 de enero es hábil (salvo que caiga fin de semana/festivo).
Semana Santa: Excluir Lunes, Martes y Miércoles Santo (además del Jueves y Viernes Santo que ya son festivos).

**Fecha:** 27/07/2026

**Estado en el código:** Implementado (Sprint 6, corrección del 2026-08-01) — ver `Pendientes.md`.

---

## Sprint 7 — Prescripción y caducidad

**Contexto:** El software calcula plazos de prescripción/caducidad para varios tipos de acción. Un caso
puntual: la ley cambiaria (letras, cheques, pagarés) tiene tres plazos distintos según el tipo de acción
(directa: 3 años; de regreso del tenedor: 1 año; entre obligados de regreso: 6 meses).

**Pregunta:** ¿Confirman los tres plazos cambiarios (3 años / 1 año / 6 meses)? ¿Hay otros tipos de proceso
con plazo de caducidad fijo y conocido que debamos precargar en vez de pedir que se ingrese manualmente?

**Respuesta del despacho:**
Los tres plazos cambiarios están confirmados. Hay otros plazos comerciales fijos que deben precargarse.
Instrucción de desarrollo:

Configurar plazos automáticos para Títulos Valores:
Acción Directa: 3 años desde el vencimiento.
Acción de Regreso (Tenedor): 1 año desde fecha de protesto o vencimiento.
Acción Ulterior Regreso: 6 meses desde el pago.
Precargar en el sistema los siguientes plazos fijos de caducidad/prescripción: Cheques (6 meses), Enriquecimiento sin causa (1 año), Transporte (2 años), Seguro (2 y 5 años), Impugnación de Actas Sociales (2 meses).

**Fecha:** 27/07/2026

**Estado en el código:** Implementado (Sprint 7, corrección del 2026-08-01) — ver `Pendientes.md`.

---

## Sprint 8 — Indexación IPC Civil/Familia

**Contexto:** Cuando se actualiza un capital histórico con el IPC, la fórmula del PDF supone que existe
una certificación mensual del IPC. En la práctica, la fuente que se tenía solo traía variación **anual**,
así que el software interpolaba entre los índices de cierre de año en vez de entre meses.

**Pregunta:** ¿Esta aproximación (interpolar entre cierres de año, y usar el IPC del año anterior para el
año en curso) es aceptable, o hace falta una fuente de IPC mensual más precisa?

**Respuesta del despacho:**
La interpolación por cierres de año es jurídicamente inválida y será objetada por un juez. El IPC debe ser mensual del DANE. Proyectar el año en curso con IPC anterior también es un error.
Instrucción de Desarrollo:

Obtener y cargar la serie histórica del IPC mensual del DANE.
Fórmula base de indexación: Renta_Actual = Renta_Historica * (IPC_Final / IPC_Inicial).
IPC_Inicial: Índice del mes en que nació la obligación.
IPC_Final: Índice del mes más reciente certificado por el DANE.
Interpolación lineal de días: Si la fecha de inicio o corte no cae en el último día del mes, aplicar interpolación matemática entre el IPC del mes anterior y el mes posterior para hallar el factor exacto del día.
Prohibir el uso de promedios anuales o proyecciones del año en curso.

**Fecha:** 27/07/2026

**Estado en el código:** La decisión legal quedó clara y no necesita volver a preguntarse — la función de
interpolación mensual ya está construida y probada. Lo único pendiente es **conseguir el dato** (la serie
real de IPC mensual del DANE), que es una solicitud de información nueva, no una re-evaluación de esta
respuesta — ver la pregunta de seguimiento en
[`Preguntas-Para-Abogado-Abiertas.md`](Preguntas-Para-Abogado-Abiertas.md#sprint-8-seguimiento--fuente-del-ipc-mensual-del-dane)
y `Pendientes.md`, Sprint 8.

---

## Sprint 11 — Derecho Tributario (DIAN)

**Contexto:** Este fue el primer sprint que agregó liquidaciones tributarias (DIAN) al software, un
dominio completamente nuevo para BASTIUM. La decisión de negocio (ya tomada) fue construir únicamente
interés moratorio tributario y depuración de Renta Líquida Gravable en una primera etapa, dejando sanciones
e imputación para un sprint posterior (completado en el Sprint 15).

**Pregunta:** Confirmación de que el área Tributaria en general sí es prioritaria para el producto.

**Respuesta del despacho:**
Las prioridades son correctas. Hay reglas estrictas de imputación de pagos y concurrencia de intereses.
Instrucción de desarrollo:

Imputación de Pagos (Art. 804 E.T.): Todo pago parcial debe imputarse en este orden estricto: 1º Sanciones, 2º Intereses, 3º Impuesto/Anticipos/Retenciones.
Sanciones (Piso mínimo): Ninguna sanción puede ser inferior a 10 UVT vigentes al momento de la liquidación.
Concurrencia Intereses vs. Actualización (Art. 867-1 E.T.): Si una deuda tributaria tiene más de 3 años de mora:
Sobre el rubro "Impuesto": Liquidar interés moratorio diario + actualización monetaria (IPC). Validación: La tasa combinada no puede superar la tasa de usura vigente; si la supera, topearla en usura.
Sobre el rubro "Sanciones": NO liquidar interés moratorio. Aplicar ÚNICAMENTE actualización monetaria por IPC.

**Fecha:** 27/07/2026

**Estado en el código:** Confirmación informativa; el desarrollo detallado del Art. 867-1 se registró y
resolvió en el Sprint 15 (ver esa sección abajo).

---

## Sprint 12 — TRM y moneda extranjera

**Contexto:** Para obligaciones comerciales en dólares, el software convertía el monto a pesos usando la
TRM que el abogado ingresaba manualmente por cada obligación, una sola vez al inicio de la liquidación.

**Pregunta:** ¿Es correcto que la conversión a pesos se haga una sola vez al inicio, o debería recalcularse
con la TRM vigente en la fecha de cada pago/abono?

**Respuesta del despacho:**
La conversión NO se hace al inicio. La deuda se mantiene en divisa y la conversión a pesos se hace dinámicamente en la fecha de cada pago.
Instrucción de Desarrollo:

Mantener el saldo de la obligación almacenado en la divisa original (ej. COP, USD).
Por cada abono o pago, consumir la TRM de la API de la Superintendencia Financiera correspondiente a la Fecha_de_Pago.
Convertir el valor del abono en divisa a COP usando esa TRM dinámica y luego aplicar la imputación de pagos. Eliminar la lógica de "TRM congelada al inicio".

**Fecha:** 27/07/2026

**Estado en el código:** Implementado (Sprint 12, corrección del 2026-08-01) — ver `Pendientes.md`. El
mecanismo exacto de cómo conviven la TRM dinámica y la anulación manual quedó como decisión técnica propia,
documentada en `Pendientes.md`.

---

## Sprint 15 — Tributario: sanciones e imputación

**Contexto:** El software calcula 3 sanciones tributarias (extemporaneidad, inexactitud, error aritmético)
con un piso legal de 10 UVT. El PDF advierte que "no se pueden cobrar simultáneamente intereses moratorios
y actualización monetaria si esto conduce a una tasa usuraria o doble pago" — esta validación quedó
documentada como advertencia, no como bloqueo automático.

**Pregunta:** ¿Existen casos reales donde sí se combinen intereses moratorios y actualización monetaria en
un mismo proceso tributario?

**Respuesta del despacho:**
La Corte Constitucional, en la Sentencia C-549 de 1993, determinó que la actualización del valor de una deuda (indexación) y el cobro de intereses moratorios tienen naturalezas distintas: la primera conserva el valor adquisitivo frente a la inflación y la segunda indemniza el daño emergente por la mora.
Regla de Oro: Pueden concurrir siempre y cuando la suma de ambos no supere el límite de usura y la corrección monetaria no sea "doblemente considerada" (es decir, que el interés de mora no incluya ya el componente inflacionario).

El Caso Real: Artículo 867-1 del Estatuto Tributario
Este artículo dispone la actualización de las deudas tributarias que tengan más de tres (3) años de vencidas

Ejemplo de validación para el motor:
Fecha de vencimiento original: 10 de mayo de 2018.
Impuesto a cargo: $100.000.000.
Fecha de pago: 10 de mayo de 2023 (5 años de mora).
Cálculo:
Intereses Moratorios: Se liquidan diariamente desde el 11 de mayo de 2018 hasta la fecha de pago a la tasa de usura certificada por la Superfinanciera

Actualización (Indexación): Al haber pasado más de 3 años, se aplica la fórmula: ValorActual=ValoraIndexar×(IPC presente/IPC inicial).

Restricción del Sistema: El software debe verificar que la Tasa Efectiva Combinada (Interés + Factor de Indexación) sea ≤ Tasa de Usura del periodo. Si la supera, debe "topear" el cobro al límite de usura

Caso especial de sanciones: Para el pago extemporáneo de sanciones, no se liquida interés de mora, sino que se aplica exclusivamente la actualización inflacionaria según el Art. 867-1 E.T.

INSTRUCCIÓN DE DESARROLLO: Programar una condicional lógica que desactive el interés moratorio sobre el rubro de "Sanciones" y aplique en su lugar el factor de actualización del Art. 867-1 E.T. si la mora supera los 3 años. Para el rubro "Impuesto", aplicar ambos conceptos validando el techo de usura.

**Fecha:** 27/07/2026

**Estado en el código:** Implementado (Sprint 15, corrección del 2026-08-01), verificado numéricamente
contra el ejemplo exacto de arriba — ver `Pendientes.md`.

---

## Sprint 16 — Seguridad social e incapacidades laborales

**Contexto:** Dos tablas de porcentajes se habían completado con fuentes externas al PDF (verificadas, no
inventadas): niveles de riesgo ARL II-IV (Decreto 1607/2002) y tramos del Fondo de Solidaridad Pensional
(Ley 797/2003 art. 8).

**Pregunta:** ¿Confirman que estos dos porcentajes/tablas son los vigentes y correctos a la fecha?

**Respuesta del despacho:**
Así es, aunque con leves precisiones en topes máximos.

Se debe cargar tabla ARL (Empleador): Nivel I=0.522%, II=1.044%, III=2.436%, IV=4.350%, V=6.960%.
FSP (Fondo Solidaridad Pensional): Activar trigger si IBC >= 4 SMMLV.
4 a 16 SMMLV: 1%
16 a 17 SMMLV: 1.2%
17 a 18 SMMLV: 1.4%
18 a 19 SMMLV: 1.6%
19 a 20 SMMLV: 1.8%
20 SMMLV: 2.0%

**Fecha:** 27/07/2026

**Estado en el código:** Implementado (Sprint 16, corrección del 2026-08-01: se agregó el tope máximo del
8.7% para cualquier nivel de riesgo ARL, Ley 1562/2012) — ver `Pendientes.md`.

---

## Sprint 17 — Módulo pensional (IBL, tasa de reemplazo, semanas)

**Contexto:** El PDF de BASTIUM solo trae la fórmula base de la tasa de reemplazo (`r = 65.5 − 0.5·s`),
sin piso/techo ni bono por semanas adicionales — la fórmula completa se había implementado con fuentes
externas, sin confirmación directa de un despacho jurídico.

**Pregunta 1:** ¿Confirman que la fórmula completa de tasa de reemplazo es correcta?

**Pregunta 3 (compartida con Sprint 3 y Sprint 30):** Conteo inclusivo de días — ver Sprint 3, misma
respuesta aplica.

**Respuesta del despacho:**
La fórmula está confirmada. Hay un caso de prueba exacto para validar el código.
Instrucción de Desarrollo:

Implementar función: Tasa_Reemplazo = 65.5 - (0.5 * s); donde s = IBL / SMMLV.
Validar que la tasa inicial resultante esté en el rango [55% , 65.5%].
Calcular bono: Bono = floor((Semanas_Cotizadas - 1300) / 50) * 1.5%.
Aplicar techo final: Tasa_Final = min(Tasa_Inicial + Bono, 80%).

La fórmula de la Ley 100 de 1993 (Art. 34), modificada por el Art. 10 de la Ley 797 de 2003, es efectivamente la fórmula decreciente, diseñada para que a mayor ingreso, menor sea el porcentaje de protección pensional.
Fórmula: r=65.5−0.5s.
Variable "s": Es el número de salarios mínimos legales mensuales vigentes contenidos en el IBL.
Piso y Techo de la Tasa Inicial: El resultado de esta fórmula oscila entre el 65.5% (para quienes ganan 1 SMMLV) y el 55% (para quienes ganan 20 SMMLV o más).
Bono por Semanas Adicionales: Por cada 50 semanas adicionales a las mínimas requeridas (1.300 semanas hoy), el porcentaje aumenta un 1.5%.
Techo Final: El porcentaje total (Tasa Inicial + Bonos) no puede superar el 80% del IBL.

Caso de Prueba (Basado en doctrina de Arenas Monsalve):
IBL: $800.000 (Equivalente a 2 salarios mínimos del año 2006 para el ejemplo).
Semanas Cotizadas: 1.664 semanas.
Paso 1 (Hallar r): s=2. Entonces r=65.5−(0.5×2)=64.5%.
Paso 2 (Hallar bonos): Mínimo requerido en ese año: 1.075 semanas. Exceso: 1.664−1.075=589 semanas.
Paso 3 (Calcular incremento): 589 / 50 = 11 grupos de 50 semanas. Incremento = 11×1.5%=16.5%.
Paso 4 (Total): 64.5%+16.5%=81%.
Ajuste por Techo: Como supera el límite, la tasa final es 80%.
Resultado: Pensión = 800.000×80%=$640.000.
INSTRUCCIÓN DE DESARROLLO: Implementar la función CALCULAR_R(IBL, SMMLV, SEMANAS). Debe primero validar el rango de la tasa inicial (55%-65.5%), luego calcular incrementos de 1.5% por cada bloque completo de 50 semanas adicionales sobre el requisito del año de causación, y finalmente aplicar un MAX_CAP del 80% sobre el IBL resultante.

**Fecha:** 27/07/2026

**Estado en el código:** Implementado (Sprint 17, corrección del 2026-08-01), verificado exactamente contra
el caso de prueba de arriba (piso 55% en vez de 65%, semanas mínimas variables por año) — ver
`Pendientes.md`.

---

## Sprint 30 — Posible error de un día

**Contexto:** Una revisión de código encontró un posible error sutil de "un día": para decidir si una
notificación de demanda "retrotrae" el efecto interruptor de la prescripción a la fecha de la demanda, el
software comparaba si pasaron `365 días o menos` entre la radicación y la notificación — en años
bisiestos eso puede activar la regla un día antes de lo debido.

**Pregunta 1:** Para prescripción, ¿"dentro de un año" debe interpretarse fecha-a-fecha, o como una cuenta
fija de 365 días corridos?

**Respuesta del despacho:**
El término de un año no son 365 días matemáticos. Es fecha a fecha estricta en el calendario.
Instrucción de Desarrollo:

Eliminar la validación if (dias <= 365).
Nueva lógica: Fecha_Vencimiento = Fecha_Notificacion_Demandante.AddYears(1).
Si la fecha resultante no existe (ej. 29-Feb en año no bisiesto), asignar el 28-Feb.
Regla de inhabilidad: Si Fecha_Vencimiento cae en sábado, domingo, festivo o vacancia judicial (ver Sprint 6), la fecha límite se desplaza al siguiente Día_Hábil_Judicial.

(La respuesta incluyó además una reiteración detallada, con un caso de ejemplo numérico completo, de las
reglas de conteo inclusivo de días y del módulo pensional ya cubiertas en las secciones de los Sprint 3 y
17 arriba — no se duplica aquí.)

**Fecha:** 27/07/2026

**Estado en el código:** Respuesta clara, no requiere reevaluación. Corrección de código (cambiar la
comparación de días por aritmética de fechas real) pendiente de programar — ver `Pendientes.md`, Sprint 30.
