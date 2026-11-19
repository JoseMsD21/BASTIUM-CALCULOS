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
- [Sprint 13 — Guía de uso de "Parámetros" para el despacho](#sprint-13--guía-de-uso-de-parámetros-para-el-despacho)
- [Sprint 15 — Tributario: sanciones e imputación](#sprint-15--tributario-sanciones-e-imputación)
- [Sprint 16 — Seguridad social e incapacidades laborales](#sprint-16--seguridad-social-e-incapacidades-laborales)
- [Sprint 17 — Módulo pensional (IBL, tasa de reemplazo, semanas)](#sprint-17--módulo-pensional-ibl-tasa-de-reemplazo-semanas)
- [Sprint 18 — Costas judiciales: tabla simple de rangos vs. tabla granular del Acuerdo PSAA16-10554](#sprint-18--costas-judiciales-tabla-simple-de-rangos-vs-tabla-granular-del-acuerdo-psaa16-10554)
- [Sprint 30 — Posible error de un día](#sprint-30--posible-error-de-un-día)
- [Sprint 33 — Tipo de acción procesal para las alertas de prescripción del Dashboard](#sprint-33--tipo-de-acción-procesal-para-las-alertas-de-prescripción-del-dashboard)
- [Sprint 41 — Fórmula de reajuste anual de la cuota alimentaria](#sprint-41--fórmula-de-reajuste-anual-de-la-cuota-alimentaria)
- [Sprint 43 — Indexación IPC en Comercial, Laboral, Honorarios, Sancionatorio y Tributario](#sprint-43--indexación-ipc-en-comercial-laboral-honorarios-sancionatorio-y-tributario)
- [Sprint 47 — Recalcular liquidaciones históricas con las correcciones del Sprint 30](#sprint-47--recalcular-liquidaciones-históricas-con-las-correcciones-del-sprint-30)
- [Sprint 8 (seguimiento 3) — Tabla real de IPC mensual anterior a enero de 2003](#sprint-8-seguimiento-3--tabla-real-de-ipc-mensual-anterior-a-enero-de-2003)
- [Sprint 70/91 (seguimiento) — Fechas exactas de vigencia por régimen, invalidez Grado 1, y "régimen de transición"](#sprint-7091-seguimiento--fechas-exactas-de-vigencia-por-régimen-invalidez-grado-1-y-régimen-de-transición)
- [Sprint 76 — Fórmula de tasa del Art. 1617/2232 C.C.: ¿lineal diaria, efectiva compuesta diaria, o mensual con prorrateo de 30 días?](#sprint-76--fórmula-de-tasa-del-art-16172232-cc-lineal-diaria-efectiva-compuesta-diaria-o-mensual-con-prorrateo-de-30-días)
- [Sprint 79 — ¿Las costas procesales deben generar interés civil del 6% junto con el capital (Suma Única)?](#sprint-79--las-costas-procesales-deben-generar-interés-civil-del-6-junto-con-el-capital-suma-única)
- [Sprint 82 (seguimiento) — ¿En qué área de BASTIUM vive el calculador de condenas administrativas (DTF)?](#sprint-82-seguimiento--en-qué-área-de-bastium-vive-el-calculador-de-condenas-administrativas-dtf)
- [Sprint 84 (seguimiento) — Imputación proporcional (Art. 804 E.T.) y tope suspensivo por demanda contenciosa](#sprint-84-seguimiento--imputación-proporcional-art-804-et-y-tope-suspensivo-por-demanda-contenciosa)
- [Sprint 85 — Retroactivo pensional: tasa de mora del Art. 141 Ley 100, y vigencia del incremento 14%/7%](#sprint-85--retroactivo-pensional-tasa-de-mora-del-art-141-ley-100-y-vigencia-del-incremento-147)
- [Sprint 86/87 (seguimiento) — Tabla actuarial completa (FAC1/FAC2), serie DTF Pensional, y cuál fórmula de FAC3 es la correcta](#sprint-8687-seguimiento--tabla-actuarial-completa-fac1fac2-serie-dtf-pensional-y-cuál-fórmula-de-fac3-es-la-correcta)
- [Sprint 94 (seguimiento) — aporte a salud en contrato realidad, y si el Decreto 0320/2026 reemplaza la regla de bonificación por servicio de la plantilla L8](#sprint-94-seguimiento--aporte-a-salud-en-contrato-realidad-y-si-el-decreto-03202026-reemplaza-la-regla-de-bonificación-por-servicio-de-la-plantilla-l8)
- [Sprint 95 (seguimiento) — porcentajes de los 4 conceptos "Horas Extras..." (HED, HEN, HEFD, HEFN) tras la Ley 2466/2025](#sprint-95-seguimiento--porcentajes-de-los-4-conceptos-horas-extras-hed-hen-hefd-hefn-tras-la-ley-24662025)
- [Sprint 96 (seguimiento) — auxilio de transporte pactado por día en trabajo doméstico](#sprint-96-seguimiento--auxilio-de-transporte-pactado-por-día-en-trabajo-doméstico)
- [Sprint 97 (seguimiento) — decisión de arquitectura pendiente: ¿séptima área de derecho o submodo de Civil/Familia?, ¿cuáles variantes usa el despacho?, y tabla de mortalidad completa (hombres/mujeres inválidos)](#sprint-97-seguimiento--decisión-de-arquitectura-pendiente-séptima-área-de-derecho-o-submodo-de-civilfamilia-cuáles-variantes-usa-el-despacho-y-tabla-de-mortalidad-completa-hombresmujeres-inválidos)
- [Sprint 105 — Catálogo de tipos de proceso, subtipos de caso y obligaciones predefinidas para el intake de un expediente](#sprint-105--catálogo-de-tipos-de-proceso-subtipos-de-caso-y-obligaciones-predefinidas-para-el-intake-de-un-expediente)
- [Sprint 106 — Widget del campo de fechas anuales fijas, y modelo de datos para el año/fecha de vigencia del acta o título](#sprint-106--widget-del-campo-de-fechas-anuales-fijas-y-modelo-de-datos-para-el-añofecha-de-vigencia-del-acta-o-título)
- [Sprint 107 — ¿Mover el checkbox de indexación IPC/interés sobre capital indexado a después de proyectar la liquidación, o agregar un control posterior de solo presentación?](#sprint-107--mover-el-checkbox-de-indexación-ipcinterés-sobre-capital-indexado-a-después-de-proyectar-la-liquidación-o-agregar-un-control-posterior-de-solo-presentación)
- [Sprint 104 (seguimiento) — cablear la liquidación tramo por tramo a AreaStrategy, y aclarar su relación con la tasa de interés de Suma Única (Sprint 76/83)](#sprint-104-seguimiento--cablear-la-liquidación-tramo-por-tramo-a-areastrategy-y-aclarar-su-relación-con-la-tasa-de-interés-de-suma-única-sprint-7683)
- [Sprint 89 (seguimiento) — ¿Renta Vitalicia (mesada mensual RAIS) o Retiro Programado/SPM? La Resolución 3023/2017 no parece cubrir lo que pedía el sprint original](#sprint-89-seguimiento--renta-vitalicia-mesada-mensual-rais-o-retiro-programadospm-la-resolución-30232017-no-parece-cubrir-lo-que-pedía-el-sprint-original)
- [Sprint 110 — ¿Extrapolar la tasa de usura del último tramo certificado, o topar el cálculo de interés al último dato disponible?](#sprint-110--extrapolar-la-tasa-de-usura-del-último-tramo-certificado-o-topar-el-cálculo-de-interés-al-último-dato-disponible)

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

**Respuesta a la pregunta de seguimiento (fuente del IPC mensual del DANE):**
El motor debe operar siempre sobre el Número Índice (no variación porcentual) para evitar errores de
redondeo acumulado en liquidaciones de larga duración.

Instrucciones de Desarrollo:
- Gestión de bases históricas (empalme): el DANE maneja bases distintas. El sistema debe soportar
  múltiples bases y aplicar un Factor de Enlace (FE) para que la serie sea matemáticamente continua.
- Bases a configurar: Base Actual (diciembre 2018 = 100) y Base Anterior (diciembre 2008 = 100).
- Fórmula de conversión: `Índice_Base2018 = Índice_Base2008 × FE`. El FE se calcula como el cociente entre
  el índice nuevo y el antiguo en el mes de traslape (diciembre 2018).
- Estructura de base de datos: crear tabla `sys_ipc_indices` con campos `periodo_mes` (Date),
  `base_referencia` (String/Enum), `valor_indice` (Decimal).
- Motor de cálculo: `ValorActual = ValorOriginal × (IPC_Final / IPC_Inicial)`; si la fecha de cálculo no es
  cierre de mes, aplicar interpolación lineal de días entre los dos índices mensuales adyacentes.

**Fecha:** (no especificada por el despacho al copiar la respuesta)

**Estado en el código (actualizado 2026-08-13):** el despacho confirmó la metodología exacta (Número
Índice, no variación %; doble base 2008/2018 con Factor de Enlace), pero **todavía no aportó la tabla real
de datos** — el índice mensual certificado por el DANE mes a mes sigue sin llegar. Sigue siendo la misma
solicitud de información del Sprint 8 (seguimiento), ahora con el diseño técnico ya confirmado. Falta: (1)
extender `historical_index.py` para soportar doble base + Factor de Enlace (hoy `_IPC_MENSUAL` es un
diccionario plano `{(año, mes): valor}` de una sola base, sin ese campo), (2) decidir si `sys_ipc_indices`
se modela como tabla nueva en `database/models.py` o como claves versionadas dentro de `parametros_legales`
(mismo patrón que el resto de series, Sprint 13), y (3) conseguir la tabla real. La página 62 del PDF de
requisitos (`REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`) solo trae variación **anual**
1967-2025 (la misma fuente ya transcrita en `_IPC_VARIACION_ANUAL`) — no resuelve este punto, es
exactamente el hueco que motivó esta pregunta.

**Respuesta a la pregunta de seguimiento 2 (tabla real de índices IPC mensuales, doble base 2008/2018):**
La serie histórica aplicable no es la de 2018, sino la consolidada bajo la base de Diciembre 2008 = 100, la cual tiene continuidad ininterrumpida desde décadas anteriores a 2003. No existe un vacío real en los datos mensuales.
Posibles cambios:
Base de Datos: Podría parametrizarse la tabla oficial del DANE con la constante de enlace diciembre 2008 = 100. 
Límite de Vacío Absoluto: Para fechas previas a la estadística nacional, inyectar un control de flujo: if fecha_corte < datetime.date(1954, 8, 1):
    indice_ipc = 1.000000
Interpolación Obligatoria: Si la fecha requerida no es el último día del mes, el sistema no puede tomar el mes completo. Podría aplicar la fórmula: V0 = (d1×V2 + d2×V1) / (d1+d2) (donde V1 es el IPC del mes anterior, V2 el del mes posterior, d1 días transcurridos y d2 días faltantes).
Estimación Futura: Si se requiere un mes no certificado aún por el DANE, aplicar la media geométrica de los últimos 12 meses conocidos: VIPC_estimada = [prod(1 + VIPC_m/100) para m en los ultimos 12 meses]^(1/12) - 1, expresada en porcentaje.

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** el despacho aportó las fórmulas de "Límite de Vacío
Absoluto" y "Estimación Futura" — ambas ya construidas y probadas (Sprint 8, rama
`sprint-8-estimacion-futura-y-floor-ipc-mensual`): `get_ipc_interpolado_for_date` retorna `1.000000` para
fechas anteriores al 01/08/1954, y `get_ipc_mensual_for_month` estima con media geométrica compuesta
cualquier mes posterior al último certificado en `_IPC_MENSUAL`, en vez de bloquear la liquidación. La
sugerencia de reparametrizar a la base Diciembre-2008=100 no requirió ningún cambio: `_IPC_MENSUAL` ya es
la serie única que el DANE enlazó (ver Sprint 80), y `IPCIndexation.calculate` solo usa la razón entre dos
índices de la misma base — cualquier base consistente da el mismo resultado dentro del rango ya cargado
(2003-2026). **Sigue sin resolver**: los valores mensuales reales anteriores a 2003 que el despacho da por
existentes en su fuente (base Dic-2008=100, continuidad desde antes de 2003) — esta rutina no tiene acceso
a esos valores en ningún archivo commiteado ni en `docs/datos_publicos_fuente/` (que solo cubre 2003-2026,
ver su README). Es un bloqueo de infraestructura (falta el archivo/dato accesible), no una decisión
pendiente — ver la pregunta de seguimiento 3 en
[`Preguntas-Para-Abogado-Abiertas.md`](Preguntas-Para-Abogado-Abiertas.md#sprint-8-seguimiento-3--tabla-real-de-ipc-mensual-anterior-a-enero-de-2003)
y Sprint 8 en `Pendientes.md`.

---

## Sprint 80 — Cobertura parcial de la serie mensual de IPC (2003-2026) y qué hacer con fechas anteriores

**Contexto:** ya conseguimos la tabla real de índices IPC mensuales que el despacho pidió (ver respuesta al
Sprint 8), pero con dos particularidades frente a lo que se había pedido: (1) viene en una sola base
continua (diciembre 2018 = 100), ya "enlazada" oficialmente por el DANE, en vez de las dos bases separadas
(2008 y 2018) con un Factor de Enlace que el software calculara; y (2) solo cubre desde enero de 2003 en
adelante — no hay índice mensual disponible para fechas anteriores a 2003.

**Pregunta:** (1) ¿La serie ya enlazada por el DANE en una sola base (diciembre 2018 = 100) es aceptable
para indexar, o el despacho necesita específicamente las dos bases separadas con el Factor de Enlace
calculado por el software? (2) Para liquidaciones con `fecha_origen` anterior a enero de 2003, ¿el
software debe (a) bloquear la indexación IPC exigiendo que el usuario indique manualmente el índice, (b)
usar la variación % anual ya cargada (interpolación anual), o (c) alguna otra solución?

**Respuesta del despacho:** la misma respuesta que contestó la pregunta de seguimiento 2 del Sprint 8 (ver
arriba) — la serie aplicable es la de base Diciembre-2008=100 con continuidad "desde décadas anteriores a
2003", más las fórmulas de "Límite de Vacío Absoluto" y "Estimación Futura".

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** resuelta junto con el Sprint 8 (misma respuesta del
despacho, mismo commit). La frontera de fechas posteriores al último mes certificado ya no cae al fallback
de interpolación anual — se estima con la media geométrica. La frontera anterior a 2003 sigue usando el
fallback a interpolación anual documentado: es la única opción posible sin el dato real, que el despacho
da por existente pero que esta rutina no tiene forma de obtener (bloqueo de infraestructura, no de
decisión — ver Sprint 8 (seguimiento 3) en `Preguntas-Para-Abogado-Abiertas.md`).

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

## Sprint 13 — Guía de uso de "Parámetros" para el despacho

**Contexto:** el software permite editar tasas, topes y plazos legales (usura, cuota litis, SMLMV, IPC,
etc.) desde la pantalla "⚙ Configuraciones → Parámetros", pensada para que alguien del despacho pueda
actualizarlos sin depender de un programador.

**Pregunta:** si en el futuro alguien del despacho va a actualizar los parámetros legales directamente
desde esa pantalla, ¿hace falta una guía de uso corta para esa persona, y a qué perfil debe estar dirigida?

**Respuesta del despacho:**
SÍ. Es imperativa una guía. Las variables macroeconómicas (usura, IPC, SMLMV) cambian constantemente.

Instrucciones de Desarrollo:
- Perfil de usuario: la guía debe estar redactada para un Abogado Junior / Estudiante de Consultorio
  Jurídico.
- Lenguaje de la guía: debe usar "campos de hecho" (ej. "Fecha de exigibilidad", "Tasa pactada") con
  enfoque pedagógico, para que el usuario traduzca el título ejecutivo al software sin errores que generen
  responsabilidad disciplinaria.

**Fecha:** (no especificada por el despacho al copiar la respuesta)

**Estado en el código:** `docs/GUIA_USUARIO.md` ya documenta la pantalla de Parámetros (Sprints 57/58/68),
pero en tono general de manual de usuario, no dirigido específicamente a un "Abogado Junior / Estudiante de
Consultorio Jurídico" ni centrado en "campos de hecho" con enfoque pedagógico de traducción del título
ejecutivo. Pendiente: sección dedicada (o ajuste de tono) en `GUIA_USUARIO.md` — ver `Pendientes.md`,
Sprint 13.

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

## Sprint 18 — Costas judiciales: tabla simple de rangos vs. tabla granular del Acuerdo PSAA16-10554

**Contexto:** el PDF de BASTIUM cita un acuerdo del Consejo Superior de la Judicatura para costas
judiciales/agencias en derecho sin transcribir la tabla completa. El desarrollo ya tenía construida una
tabla granular (18 tipos de proceso × instancia, transcrita del Acuerdo PSAA16-10554 del 5 de agosto de
2016, verificada contra ramajudicial.gov.co). El despacho aportó además una tabla simple de 3 rangos por
cuantía que no coincide numéricamente con la granular, lo que generó una pregunta de seguimiento sobre si
una reemplaza a la otra.

**Pregunta 1:** ¿pueden aportar el texto completo o la tabla de rangos de cuantía y porcentaje del acuerdo
del Consejo Superior de la Judicatura vigente hoy para costas judiciales?

**Pregunta 2 (seguimiento):** ¿la tabla simple de 3 rangos es (a) una síntesis que reemplaza la tabla
granular, o (b) un tope general que solo aplica al porcentaje manual, quedando la tabla granular como
fuente del cálculo automático?

**Respuesta del despacho:**
Existe una tabla de rangos de cuantía estricta que limita lo que el juez puede fijar.

Instrucción de Desarrollo:
- Implementar tabla de validación cruzada basada en las pretensiones del proceso: Mínima Cuantía (hasta 40
  SMMLV) → 0% al 10%; Menor Cuantía (>40 hasta 150 SMMLV) → 3% al 7%; Mayor Cuantía (>150 SMMLV) → 1% al
  5%.
- El sistema debe restringir el input del usuario: si el proceso es de Mayor Cuantía, no puede ingresar un
  8% de agencias en derecho (error de validación).

**Respuesta a la pregunta de seguimiento:**
Opción (b). La tabla simple es un "Hard Cap" (filtro de seguridad) para inputs manuales; la tabla granular
gobierna el cálculo automático. Rige el Acuerdo PCSJA20-11556 (que actualiza el PSAA16-10554).

Instrucción de Desarrollo:
- Cálculo automático: usar la tabla granular del Acuerdo PCSJA20-11556 (18 tipos de proceso × instancia)
  como base de datos maestra.
- Validación de input manual: tabla simple como restricción estricta (los 3 rangos de arriba).
- Ultraactividad (tránsito CPC → CGP, Art. 624 CGP): validar la fecha de la providencia que impone costas;
  si es posterior al CGP (1° de enero de 2016, o gradualidad por distrito), aplicar la tabla granular
  nueva; si la etapa de alegatos concluyó antes del cambio normativo, respetar el trámite de la ley
  anterior, pero la liquidación futura se rige por la nueva.

**Fecha:** (no especificada por el despacho al copiar la respuesta)

**Estado en el código (actualizado 2026-08-14):** `costas_pct_manual` (validación de input manual, Sprint
4) ya usa la tabla simple de 3 rangos como tope — implementado provisionalmente el 2026-08-01 mientras se
esperaba esta respuesta. La tabla granular (`app/engine/costs/agencias_en_derecho.py`, 18 categorías) ya
gobierna el cálculo automático desde el cierre original del sprint, sin cambios. La ultraactividad CPC→CGP
(Art. 624 CGP) ya se implementó el 2026-08-14 (`validar_ultraactividad_cgp`). Seguía pendiente confirmar
si "Acuerdo PCSJA20-11556" y "Acuerdo PSAA16-10554" son la misma norma — ver respuesta de seguimiento
abajo.

**Respuesta a la pregunta de seguimiento 2 (¿PCSJA20-11556 y PSAA16-10554 son el mismo acuerdo?):**
Por ahora se sabe que el marco tarifario unificado obligatorio se rige por el Acuerdo PSAA16-10554. Las agencias en derecho se tasan según el Acuerdo con una ponderación inversa: a mayor valor, menor porcentaje, respetando los topes.

Qué podría hacerse?:
El módulo TasacionCostas debe mapear las siguientes tarifas duras:

Procesos Declarativos: Única Instancia (Pecu): min 0.05, max 0.15. Única Instancia (No Pecu): min 1 SMMLV,
max 8 SMMLV. Primera Instancia (Menor Cuantía): min 0.04, max 0.10. Primera Instancia (Mayor Cuantía): min
0.03, max 0.075. Segunda Instancia: min 1 SMMLV, max 6 SMMLV.

Procesos Ejecutivos: Mínima Cuantía: min 0.05, max 0.15. Menor Cuantía: min 0.04, max 0.10. Mayor
Cuantía: min 0.03, max 0.075. Segunda Instancia: min 1 SMMLV, max 6 SMMLV.

Sucesiones y Liquidaciones (Objeciones e Inventarios): Mínima: min 0.05, max 0.15. Menor: min 0.04, max
0.10. Mayor: min 0.03, max 0.075.

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** confirmado — el Acuerdo **PSAA16-10554** rige, exactamente
lo que ya está implementado y verificado contra la fuente oficial (ramajudicial.gov.co); no requirió ningún
cambio de código. La "ponderación inversa" también quedó confirmada tal cual ya la implementa
`_interpolar_dentro_de_rango`, citando el mismo fundamento (Parágrafo 3, Art. 3 del Acuerdo). La tabla de
"tarifas duras" que trae la respuesta, en cambio, no coincide numéricamente con la tabla granular ya
verificada — esta rutina NO la usó para sobrescribir el motor de cálculo (más detalle, y la pregunta de
seguimiento 3 pendiente, en
[`Preguntas-Para-Abogado-Abiertas.md`](Preguntas-Para-Abogado-Abiertas.md#sprint-18-seguimiento-3--discrepancia-numérica-entre-la-tabla-granular-verificada-psaa16-10554-y-las-tarifas-duras-que-aportó-el-despacho)).
Ver `Pendientes.md`, Sprint 18.

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

---

## Sprint 33 — Tipo de acción procesal para las alertas de prescripción del Dashboard

**Contexto:** el Dashboard avisa cuando una obligación está por prescribir. Para calcular la fecha límite,
el sistema necesita saber qué tipo de acción judicial aplica (ejecutiva, ordinaria, cambiaria, etc.), pero
no existe un campo para capturarlo — se estaba usando "acción ejecutiva" para las 6 áreas por igual, como
aproximación provisional.

**Pregunta:** ¿es correcto usar "acción ejecutiva" para las 6 áreas, o cada área necesita un tipo de acción
distinto con plazos diferentes?

**Respuesta del despacho:**
NO. La acción ejecutiva no es transversal. El motor debe diferenciar prescripción (alegable) de caducidad
(de oficio).

Instrucción de Desarrollo:
- Implementar tabla determinista (enum/BD):
  - Civil: Ejecutiva (5 años, Art. 2536 CC) | Ordinaria (10 años, Art. 2536 CC) | Rescisoria (4 años, Art.
    1954 CC).
  - Comercial: Cambiaria Directa (3 años, Art. 789 C.Co) | Cambiaria Regreso (1 año, Art. 790 C.Co) |
    Cheque (6 meses, Art. 730 C.Co).
  - Laboral: Ordinaria/Ejecutiva (3 años, Art. 488 CST).
  - Familia: Alimentos/cada cuota (5 años, Art. 2536 CC).
  - Sancionatorio: Disciplinaria (5 años, Ley 1952 de 2019).
  - Honorarios: Cobro (3 años, Art. 488 CST / Art. 2542 CC).
  - Administrativo (CPACA): Reparación Directa (2 años, Art. 164) | Nulidad y Restablecimiento (4 meses,
    Art. 164).
- Selector en UI: al elegir "Área", el sistema autocompleta el plazo según la tabla.
- Cómputo "fecha a fecha" en calendario gregoriano (Art. 118 CGP); si el día de vencimiento no existe (29
  de febrero), vence el último día del mes.
- Alertas: disparar "Caducidad Inminente" cuando falten 30 días; considerar el término de 1 año para
  notificar el auto admisorio (inoperancia de la caducidad).
- Ultraactividad: si el término empezó a correr bajo CPC/Ley 794 de 2003, sigue bajo esa ley, salvo que el
  CGP establezca un plazo más corto (se cuenta desde su vigencia, a menos que el plazo viejo venza primero).

**Fecha:** (no especificada por el despacho al copiar la respuesta)

**Estado en el código:** `UniversalLiquidationService` sigue usando `TipoAccion.EJECUTIVA` como default
único para las 6 áreas (mismo default "provisional" que reutilizó el Sprint 42 para marcar obligaciones
prescritas). Con esta respuesta ya no está bloqueado por falta de decisión legal — falta: (1) la tabla
área→tipo de acción→plazo con la norma citada, (2) el selector en UI que autocomplete el plazo al elegir
área, y (3) la lógica de ultraactividad CPC→CGP. Ver `Pendientes.md`, Sprint 33 (y Sprint 61, que ya
identificó que la mayoría de estos plazos existen como parámetro en `parametros_legales` pero sin wiring a
ninguna pantalla real).

---

## Sprint 41 — Fórmula de reajuste anual de la cuota alimentaria

**Contexto:** el software automatiza el reajuste anual de la cuota alimentaria (capital constante dentro
del año, reajustado cada 1° de enero) con la fórmula `cuota_nueva = cuota_anterior + (cuota_anterior ×
porcentaje_variación_anual / 100)`, usando el índice que indique el acta o título ejecutivo (SMMLV o IPC).

**Pregunta:** ¿es correcta esa fórmula para cualquier acta/título que fije un reajuste "según el SMMLV" o
"según el IPC", o hay casos donde difiere (tope máximo, redondeo específico, mes de corte distinto a enero,
porcentaje parcial)?

**Respuesta del despacho:**
La fórmula `CN = CA + (CA × %V / 100)` es correcta como regla general, pero requiere parametrización de
excepciones para no fallar.

Instrucción de Desarrollo:
- Regla base: reajuste automático cada 1° de enero (Art. 129 Ley 1098/2006). Índice por defecto: IPC del
  año anterior, a menos que el acta indique SMMLV u otro.
- Tope de coerción: ningún embargo por alimentos puede exceder el 50% del salario/prestaciones del deudor
  (validación obligatoria en UI).
- Redondeo: precisión decimal completa; PROHIBIDO redondear a múltiplos de $1.000 automáticamente, salvo
  que el título especifique "ajustado al peso".
- Mes de corte: campo `Fecha_Base_Titulo`; si el acta dice "12 meses desde la firma" (ej. agosto), el
  incremento se calcula en agosto, no en enero.
- Porcentaje parcial: variable `Factor_Ponderación` (float, default 1.0); si el acta pacta "50% del
  incremento", el factor es 0.5.
- Fórmulas alternativas (mora y cascada): si hay cuotas adeudadas de varios años, `C_final = C_base ×
  Π(1+i_t)` (producto de los intereses de cada año transcurrido); interés moratorio 0.5% mensual (6%
  anual) sobre el capital indexado en mora.
- Imputación de pagos (orden jerárquico estricto): 1° intereses moratorios → 2° gastos de
  cobranza/costas → 3° capital (mes más antiguo).

**Fecha:** (no especificada por el despacho al copiar la respuesta)

**Estado en el código:** `app/services/reajuste_anual.py::generar_cuotas_mensuales()` (Sprint 41, cerrado
2026-08-09) ya implementa la fórmula base confirmada arriba, con capital constante dentro del año y
reajuste el 1° de enero. Verificado que **no existe** en el motor ninguna validación del tope del 50% de
embargo por alimentos. Pendiente: (1) construir ese tope de coerción, (2) el campo `Fecha_Base_Titulo` para
reajustes con mes de corte distinto a enero (hoy fijo al 1° de enero), (3) `Factor_Ponderación` para
reajustes parciales, y (4) verificar la imputación jerárquica exacta (intereses moratorios → costas →
capital del mes más antiguo) contra el motor de imputación general (`AllocationEngine`). Ver
`Pendientes.md`, Sprint 41.

---

## Sprint 43 — Indexación IPC en Comercial, Laboral, Honorarios, Sancionatorio y Tributario

**Contexto:** la indexación IPC ya está construida y probada, pero solo está disponible para Civil/Familia
— en las otras 5 áreas el checkbox correspondiente ni siquiera aparece. Tributario y Sancionatorio ya
tienen su propio mecanismo de actualización monetaria (Art. 867-1 E.T. y conversión SMLMV/UVT), así que
activar IPC ahí podría duplicar el ajuste.

**Pregunta:** ¿en cuáles de las 5 áreas (Comercial, Laboral, Honorarios, Sancionatorio, Tributario) tiene
sentido jurídico ofrecer indexación IPC como opción adicional a la que ya tiene el área hoy?

**Respuesta del despacho:**

**Tributario:** SÍ se ofrece IPC, pero no como opción paralela libre — está intrínsecamente ligado al Art.
867-1 E.T.; son mutuamente excluyentes en su componente inflacionario para evitar doble actualización.
- Trigger de morosidad: si mora > 36 meses, aplicar el algoritmo del Art. 867-1 E.T. (serie IPC del Sprint
  8).
- Sanciones: bloquear el interés de mora y aplicar exclusivamente el factor IPC (Art. 867-1 E.T.).
- Impuestos: aplicar intereses de mora + actualización IPC (Art. 867-1 E.T.).
- Validación de techo de usura: la tasa efectiva combinada (interés de mora + factor de indexación) no
  puede superar la tasa de usura certificada por la Superfinanciera; si la supera, topearla y alertar.
- Prohibición de doble cobro: si se detecta una tasa que ya incorpora protección inflacionaria (ej. UVR),
  bloquear y lanzar error si se intenta aplicar IPC sobre el capital.

**Comercial:** NO (como regla general acumulable a intereses).
- Regla de exclusión (XOR): prohibir activar simultáneamente "Interés Comercial (mora/remuneratorio)" e
  "Indexación IPC".
- El usuario elige: (a) tasa comercial (ya incluye inflación) o (b) capital indexado + interés civil puro
  (6% anual), esto último solo si existe pacto expreso en el título.

**Honorarios:** SÍ (compatible con intereses civiles).
- Habilitar IPC por defecto.
- Fórmula: `Capital_Honorarios × (IPC_Final / IPC_Inicial) + Interés_Civil_6%_Anual(Capital_Actualizado)`.
- El IPC_Inicial es el del mes en que se hizo exigible la obligación o se presentó la cuenta de cobro.
- De oficio (automática): en etapa declarativa (sentencia de condena) y restitución de mutuos, el motor
  calcula IPC sin checkbox.
- A petición de parte (checkbox): en etapa ejecutiva; si el título no previó IPC y se cobran intereses
  comerciales, alertar "Improcedente por acumulación".

**Laboral:** IPC y la regla de 360 días cumplen funciones distintas y complementarias, pero IPC es
excluyente con intereses moratorios.
- El conteo de días (regla 360 días inclusiva) cuantifica la base temporal; el IPC actualiza el valor
  resultante.
- Regla de exclusión: permitir elegir IPC o intereses moratorios, pero alertar "Doble Actualización
  Prohibida" si se marcan ambos sobre el mismo rubro en el mismo periodo.
- Excepción: aplicar IPC solo si no hay moratorios (buena fe probada) o en reliquidaciones pensionales
  (traer IBL a valor presente).

**Sancionatorio:** la conversión SMLMV/UVT prevalece; IPC es excluyente con el SMLMV actual.
- Prohibición: bloquear IPC si el rubro está parametrizado en UVT/SMLMV actualizado a la fecha de pago (el
  incremento anual del SMMLV ya absorbe la inflación).
- Excepción: IPC sí es válido si el valor de la multa se ancló a UVT/SMLMV a la fecha del hecho (faltas
  antiguas); se aplica desde la exigibilidad (firmeza del acto) hasta el pago efectivo.

**Fecha:** (no especificada por el despacho al copiar la respuesta)

**Estado en el código (actualizado 2026-08-17):** implementado en las 5 áreas — ver `Pendientes.md`, Sprint
43, "Cierre de implementación (2026-08-17)". La fórmula de Honorarios quedó implementada tal cual
(`Capital × IPC_Final/IPC_Inicial + Interés_Civil_6%(Capital_Actualizado)`), pero quedó una pregunta de
seguimiento sobre si es jurídicamente válido cobrar interés civil sobre un capital ya indexado (en vez de
sobre el capital original) — ver respuesta abajo.

**Respuesta a la pregunta de seguimiento (¿es válido el interés civil sobre el capital ya indexado en
Honorarios?):**
El cobro de interés civil del 6% sobre el capital de honorarios ya indexado es jurídicamente válido, pues la indexación restituye el poder adquisitivo (el valor real) y el interés resarce la privación del dinero (el lucro). No constituye anatocismo.

Qué puede hacerse?
Para la estrategia Suma Única - Honorarios, el orden de las operaciones en el motor debe ser:

Capital_Actualizado = Capital_Original * (IPC_Final / IPC_Inicial)

Intereses_Mora = CalcularInteresCivil(Base=Capital_Actualizado, Tasa=0.06)

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** confirma exactamente la fórmula ya implementada desde el
2026-08-17 — no requirió ningún cambio de código. La misma respuesta trajo además una regla sobre costas
procesales ("NUNCA generan intereses, se suman al final en seco") que resultó ser la respuesta directa a
una pregunta distinta y ya existente, la del Sprint 79 — ver esa sección de `Pendientes.md` para el cambio
de código correspondiente.

---

## Sprint 47 — Recalcular liquidaciones históricas con las correcciones del Sprint 30

**Contexto:** el Sprint 30 corrigió dos cómputos de fecha/conteo (prescripción fecha-a-fecha real, y
conteo inclusivo de días de prestaciones en Laboral), pero por diseño no tocó ninguna liquidación ya
guardada antes de esa fecha.

**Pregunta:** ¿existe alguna liquidación ya entregada a un cliente o presentada ante un juzgado con la
lógica vieja? Si existe, ¿se recalcula, y con qué alcance?

**Respuesta del despacho:**
SÍ. Existen liquidaciones entregadas con lógica defectuosa. Se rechaza mantener el error técnico. Es
obligatorio recalcular por principios de verdad real y primacía de la realidad (Art. 53 CP).

Instrucción de Desarrollo:
- Auditoría y marcado (BD): marcar con flag "OBSOLETO - REQUIERE RECÁLCULO" todas las liquidaciones
  generadas antes del cierre del Sprint 30.
- Log de diferencias: mostrar al abogado un comparativo numérico ("Diferencia recuperada: +X días / +Y
  semanas / +$Z pesos").
- Protocolo de recálculo según estado procesal:
  - Expedientes activos (en trámite): recálculo obligatorio; permitir generar un "Memorial de
    Actualización/Corrección" para presentar antes del fallo de instancia.
  - Presentadas en juzgado/CPACA: generar memorial de corrección de error aritmético (Art. 151 CPACA).
  - En cosa juzgada (fallo en firme): NO recalcular; mantener el valor por seguridad jurídica, salvo
    recurso de revisión por error de hecho manifiesto.
- Priorización: el recálculo automatizado debe priorizar los expedientes donde la alerta de prescripción
  esté a menos de 30 días de ocurrir.
- Estandarización pensional: implementar la Sentencia SL138-2024 como estándar por defecto (días calendario
  reales), eliminando la base comercial de 360 días exclusivamente para el módulo de densidad pensional.

**Fecha:** (no especificada por el despacho al copiar la respuesta)

**Estado en el código:** Implementado (Sprint 47, partes A y B). Parte A (commits `3147d62`/`5eb57bd`,
2026-08-14): (1) el script de identificación/marcado de liquidaciones afectadas vía `AuditLog`
(`app/services/recalculo_historico.py`, `scripts/recalcular_historicas_sprint30.py`), (2) los documentos de
"Memorial de Actualización/Corrección" y de "corrección de error aritmético" (`app/engine/reports/memoriales.py`),
y (3) el log de diferencias numérico, todos ya construidos y con el enforcer de cosa-juzgada corregido en
revisión de código. Parte B (2026-08-18, este cierre): punto (4) confirmado **sin necesidad de corrección de
código** — `calcular_densidad_semanas` (`app/engine/labor/ibl.py`) ya usa días calendario reales (365/366,
`(fin - inicio).days`) desde que se creó en el Sprint 17, nunca la base comercial de 360 días; es una función
aislada, sin conectar a `LaboralStrategy` ni a ninguna GUI (misma nota del Sprint 3), así que no había
ninguna ruta de código real usando la base incorrecta para densidad pensional. Ya existía (y sigue en verde)
`tests/engine/labor/test_ibl.py::test_densidad_semanas_calendario_real_vs_ano_comercial_360`, que compara
explícitamente el resultado en calendario real contra el año comercial de 360 sobre un caso que cruza un año
bisiesto (57 semanas vs. 56), documentando la diferencia numérica exigida por la Sentencia SL138-2024. La
base de 360 días de `LaboralStrategy.liquidar` (prestaciones sociales, Sprint 30) no se tocó — es un rubro
distinto y sigue siendo la base correcta para ese caso, por diseño (ver Sprint 3). Con esto, el script de
recálculo histórico del Sprint 47a no necesita una fecha de corte adicional: no hubo cambio de código que
afecte liquidaciones ya guardadas.

---

## Sprint 70/91 — Tasa de reemplazo pensional: regímenes históricos e invalidez

**Contexto:** `calcular_tasa_reemplazo` (`app/engine/labor/ibl.py`, Sprint 17) solo implementa la fórmula
`r = 65.5 − 0.5·s` de la Ley 797/2003, vigente desde 2004. Una plantilla comercial del despacho (P9,
hallada en el Sprint 91) sugirió que existen al menos 4 fórmulas más: dos regímenes históricos anteriores
(1993-2003 y "régimen de transición"), y pensión de invalidez grados 1 y 2 — esta última con cifras que sí
se pudieron extraer completas de la plantilla (grado 1: base 45%, +1,5%/50 semanas desde 500, tope **75%**;
grado 2: base 54%, +2%/50 semanas desde 800, tope 75%).

**Pregunta:** ¿pueden confirmar la fórmula exacta de cada régimen histórico (con su fecha exacta de
vigencia), y las cifras de invalidez grados 1 y 2?

**Respuesta del despacho:**
La coexistencia de regímenes necesita un patrón Factory que pueda enrutar el cálculo según la fecha de los hechos jurídicamente relevantes y el régimen de transición del afiliado.

Podría implementarse una lógica de Tasa de Reemplazo (r):

Régimen 1985-1989 (Ley 33/85 y Ley 71/88): r = 75.0% fijo. Sin variables dinámicas.
Régimen ISS Pre-Ley 100 (Acuerdo 049/1990):
Base: 45% (500 semanas) o 75% (1.000 semanas).
Incremento: +3.0% por cada grupo de 50 semanas adicionales a las 1.000.
Tope algorítmico: min(r, 90.0).

Régimen Ley 100 Original (1994-2003):
Base: 65% (1.000 semanas).
Incrementos: +2.0% / 50 sem (entre 1.000 y 1.200). +3.0% / 50 sem (entre 1.200 y 1.400).
Tope algorítmico: min(r, 85.0).

Régimen Ley 797/2003 y Ley 2381/2024:
Variable s = IBL / SMMLV_vigente.
Fórmula base decreciente: r = 65.5 - (0.5 * s).
Límite de control: Nunca inferior a 55% ni superior a 65.5%.
Incremento: +1.5% por cada 50 semanas adicionales a las 1.300.
Tope algorítmico: min(r_final, 80.0).

Pensión de Invalidez (Grado I - 50% a 65% PCL): r = 45.0 + (math.floor((semanas - 500) / 50) * 1.5).
Tope: 60%.

Pensión de Invalidez (Grado II - ≥ 66% PCL): r = 54.0 + (math.floor((semanas - 800) / 50) * 2.0).
Tope: 75%.

(Más el pseudocódigo Python completo de las 4 fórmulas y las 2 pensiones de invalidez — ver la copia
íntegra en el historial de `Preguntas-Para-Abogado-Abiertas.md` si hace falta releerlo literal.)

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** implementadas y probadas como funciones aisladas en
`app/engine/labor/ibl.py` — `calcular_tasa_reemplazo_regimen_1985_1989`,
`calcular_tasa_reemplazo_iss_pre_ley_100`, `calcular_tasa_reemplazo_ley_100_original` y
`calcular_tasa_reemplazo_invalidez_grado_2` (tests en `tests/engine/labor/test_ibl.py`, verificados contra
las fórmulas exactas de esta respuesta). **Dos puntos quedan sin resolver, documentados como pregunta de
seguimiento, no adivinados:**
1. **Invalidez Grado 1**: el tope que trae esta respuesta (60%) NO coincide con el que ya había confirmado
   la plantilla P9 con cifras concretas (75%, Sprint 91) — no se implementó ninguna función para este grado
   hasta que el despacho aclare cuál de los dos toques es el correcto.
2. **Router por fecha de causación**: el patrón "Factory" que pidió el despacho para elegir automáticamente
   el régimen aplicable no se construyó — la respuesta da fórmulas pero no las fechas exactas de entrada en
   vigencia de cada régimen (cuándo empieza y termina cada uno; "1985-1989" y "Pre-Ley 100" no traen día
   exacto). Enrutar mal una liquidación real a un régimen equivocado por una fecha de corte mal supuesta es
   un error de dominio grave — se prefirió dejar las funciones sin conectar antes que adivinar una fecha de
   corte. Tampoco se abordó explícitamente el "régimen de transición" (Art. 36 Ley 100/1993, 75%/90%/"la
   que corresponda") que preguntaba originalmente el Sprint 91 — la respuesta no lo menciona por ese
   nombre.

Ver la pregunta de seguimiento en
[`Preguntas-Para-Abogado-Abiertas.md`](Preguntas-Para-Abogado-Abiertas.md#sprint-7091-seguimiento--fechas-exactas-de-vigencia-por-régimen-invalidez-grado-1-y-régimen-de-transición)
y `Pendientes.md`, Sprints 70 y 91.

---

## Sprint 74 — Familia: tipos de beneficiario de alimentos y reglas de vigencia por tipo

**Contexto:** el software no distinguía quién es el beneficiario de una obligación alimentaria más allá de
un campo de texto libre. El reporte del usuario (2026-08-13) ya afirmaba como hecho conocido las reglas de
Niño (18/25 años según si estudia) y Niño con discapacidad permanente (vitalicio) — la rutina autónoma
implementó esas dos sin esperar respuesta (2026-08-20). Quedaba sin confirmar el criterio para Cónyuge,
Padres, y Otro (donante, abuelos, etc.).

**Pregunta:** ¿pueden confirmar la lista completa de reglas de vigencia por tipo de beneficiario, y las que
falten (ej. ¿cómo se determina que un cónyuge "superó su condición de vulnerabilidad"?)? ¿Existen otras
categorías de beneficiario además de las mencionadas?

**Respuesta del despacho:**
El motor no puede presumir el fin de la vulnerabilidad para cónyuges, padres o donantes, pues depende de hechos externos como el matrimonio, un empleo, la muerte, etc.

Qué puede hacerse?
Implementar el siguiente árbol de decisión en la clase AlimentosVigencia:

if tipo == 'HIJO' and estudia == False: Vigencia hasta los 18 años.

if tipo == 'HIJO' and estudia == True: Vigencia hasta los 25 años.

if tipo == 'HIJO' and discapacidad_permanente == True: Vigencia Vitalicia.

if tipo in ['CONYUGE', 'PADRES', 'DONANTES', 'OTROS']: El software debe arrojar Vigencia = No determinable automáticamente (Porque requiere una fecha de exoneración dictada por la autoridad). El usuario debe proveer la fecha de corte obligatoriamente.

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** confirma exactamente lo que ya estaba implementado para
Niño/Niño con discapacidad permanente (sin cambios), y para Cónyuge/Padres/Otro confirma "no determinable
automáticamente" (también ya implementado) — con una instrucción nueva y accionable: la fecha de corte
debe ser **obligatoria** cuando la vigencia no es determinable. Implementado en
`app/services/vigencia_alimentos.py` (`validar_fecha_corte_beneficiario_obligatoria`,
`FechaCorteAlimentosRequeridaError`) y `ObligacionFormDialog` (`app/views/obligaciones.py`): para una
obligación RECURRENTE con beneficiario no determinable, un checkbox + fecha se vuelven visibles y
obligatorios — "Guardar" bloquea sin ellos. La respuesta sigue sin dar un criterio operacional para "cuándo
un cónyuge superó su vulnerabilidad" (el reemplazo es que la autoridad fije la fecha, no que el software la
calcule) — no hace falta esa regla ahora que la fecha es manual. Ver `Pendientes.md`, Sprint 74.

---

## Sprint 78 — Conteo de días para densidad pensional (semanas cotizadas): ¿aplica el "+1" inclusivo?

**Contexto:** el software cuenta días con la fórmula inclusiva `Dias = (Fecha_Fin - Fecha_Inicio) + 1` para
prestaciones sociales (Sprint 3), pero `calcular_densidad_semanas` (densidad pensional, Sprint 17) usaba
una resta simple sin el "+1" — verificado contra un caso de prueba judicial real (348 días → 50 semanas),
sin confirmar si ahí el "+1" también debía aplicar o si era, a propósito, la excepción.

**Pregunta:** para contar los días que se convierten en "semanas cotizadas" de pensión, ¿debe sumarse 1 día
al resultado de la resta de fechas (igual que para prestaciones), o el conteo sin ese "+1" es correcto para
este cálculo específico?

**Respuesta del despacho:**
En materia de pensiones, la Corte Suprema de Justicia en la sentencia SL138-2024 prohibió el uso del año comercial de 360 días para el cómputo de las semanas de pensión.

Qué puede hacerse?

Para prestaciones sociales como primas y cesantías: Resta inclusiva ((Fin - Inicio) + 1) sobre base de 360 días anuales.

Para semanas pensionales: No se usa el factor de año, sino que se suman los días calendario reales con resta inclusiva y se divide estrictamente entre 7. Semanas_Reales = sumatoria_dias_calendario_totales / 7

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** confirmado — sí aplica el "+1" inclusivo. Implementado en
`calcular_densidad_semanas` (`app/engine/labor/ibl.py`): cada período fusionado suma `(fin - inicio).days +
1` antes de dividir por 7. El caso de prueba judicial ya citado (348 días) sigue dando 50 semanas con el
+1 (349/7 = 49,86 → 50) — no era una excepción real, solo una coincidencia de redondeo. El caso de períodos
solapados sí cambió de resultado (6 → 7 semanas), documentado en el test correspondiente. Función aislada,
sigue sin conectar a ningún flujo real de liquidación (mismo estado que antes de este sprint). Ver
`Pendientes.md`, Sprint 78.

---

## Sprint 82 — ¿El despacho litiga contra entidades públicas (condenas administrativas con intereses a la tasa DTF)?

**Contexto:** una plantilla del despacho (`i10.INTERESES-TASADOS-A-LA-DTF-CONDENAS-ADMINISTRATIVAS.md`)
liquida intereses de mora en condenas o conciliaciones contra el Estado, a una tasa equivalente a la DTF
durante los primeros 10 meses después de la ejecutoria (Art. 195 núm. 4 Ley 1437/2011), y luego a la tasa
comercial. Ninguna de las 6 áreas actuales de BASTIUM contempla explícitamente litigios contra entidades
públicas.

**Pregunta:** ¿el despacho maneja casos de este tipo? Si es así, ¿en cuál de las áreas actuales de BASTIUM
encajarían, o se necesitaría un área/flujo nuevo?

**Respuesta del despacho:**
El Artículo 195 del CPACA instauró un régimen dual (DTF transitoria seguida de tasa comercial).

Qué puede hacerse?
El cálculo es iterativo día a día:

limite_gracia_dias = 304  # Promedio 10 meses reales
for dia in rango(1, dias_transcurridos + 1):
    if dia <= limite_gracia_dias:
        # Tramo A (DTF)
        tasa_diaria = (1 + DTF_EA_histórica) ** (1/365) - 1
    else:
        # Tramo B (Comercial)
        tasa_diaria = (1 + (1.5 * IBC_EA_histórica)) ** (1/365) - 1

Como consejo que puede ponerse en la interfaz, debe invitarse a validar si transcurren 3 meses inactivos sin cobro tras la ejecutoria, en ese caso el contador de intereses se congela por suspensión total de devengo.

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** la respuesta trae la fórmula completa, pero no contesta
la pregunta original (si el despacho tiene estos casos y en qué área deberían vivir). Se implementó la
fórmula como función aislada y probada
(`calcular_interes_dtf_condena_administrativa`, `app/engine/interest/condena_administrativa_dtf.py`) —
régimen dual DTF/1,5x IBC, interés simple diario — sin conectarla a ninguna `AreaStrategy`, porque esa
decisión de arquitectura (a qué área asignarla, o si hace falta una nueva) sigue sin resolver. El "consejo"
de congelar el conteo tras 3 meses de inactividad no se implementó: es una sugerencia de interfaz, no una
regla obligatoria, y necesitaría un dato (fecha del último cobro/actuación) que el modelo actual no
captura. Pregunta de seguimiento (solo la asignación de área) en `Preguntas-Para-Abogado-Abiertas.md`. Ver
`Pendientes.md`, Sprint 82.

---

## Sprint 84 — Interés moratorio tributario (E.T. art. 635): ¿366 días lineal (convención DIAN) o 365 compuesto (fórmula actual de BASTIUM)?

**Contexto:** el interés moratorio tributario (E.T. art. 635) se calcula tomando la tasa de usura vigente
menos 2 puntos porcentuales, y esa tasa anual se convierte a diaria para liquidar día por día. BASTIUM
usaba la fórmula "efectiva compuesta" de 365 días (`(1+i)^(1/365)-1`, la misma que el interés civil del
6%), mientras que las plantillas i4/i4A del despacho dividen la tasa **linealmente entre 366 días**
(`tasa_anual / 366`) — el propio archivo del despacho llama a esto "la ilógica matemática de la DIAN".

**Pregunta:** ¿BASTIUM debe replicar la convención literal de la DIAN (366 días, lineal) o mantener la
fórmula financiera "correcta" (365 días, compuesta)?

**Respuesta del despacho:**
A diferencia del sistema financiero NIIF, el Estatuto Tributario exige la liquidación por interés simple y división lineal para igualar los cálculos oficiales de la DIAN y evitar el anatocismo tributario.

Qué se puede hacer?
Fórmula Diaria: tasa_diaria = tasa_usura_anual / (365 o 366) (Estricta división lineal).

Imputación Proporcional: Cuando haya un abono a la deuda, invalidar la regla civil de restar primero intereses. Allí se aplica el Art. 804 del Estatuto Tributario: el abono se distribuye de forma prorrateada calculando el porcentaje que pesa el capital, la sanción y el interés frente a la deuda total, rebajando los tres rubros simultáneamente.

Tope Suspensivo: A los 24 meses de admitida la demanda contenciosa, la variable intereses_acumulando se establece en False hasta el 11° día posterior a la sentencia.

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** confirmado — división lineal, no compuesta. Implementado
en `calcular_interes_moratorio_tributario`/`construir_rate_provider_moratorio_tributario`
(`app/engine/tax/moratory_interest.py`, nueva función compartida `tasa_diaria_lineal_tributaria`) y también
en `calcular_interes_usura_plena` (`app/engine/tax/actualizacion_867_1.py`, el techo del Art. 867-1/Sprint
15) — mezclar la fórmula lineal nueva del interés con la compuesta antigua del techo rompía la invariante
de que el interés (tasa más baja) siempre debe quedar por debajo del techo (tasa más alta): con solo el
interés cambiado, un caso real de 5 años de mora daba un interés MAYOR que el techo, un artefacto de
mezclar dos convenciones, no un resultado legal real. Con ambos en la misma convención, la invariante se
restaura. Tests actualizados con los nuevos montos (el caso real del despacho, Sprint 15, pasa de un
interés de $123.160.595,20 a $140.031.700,20, y la indexación topada de $7.773.307,41 a $10.000.000,66).
Las dos reglas adicionales de esta respuesta (imputación proporcional Art. 804 E.T., tope suspensivo por
demanda contenciosa) NO se implementaron — van más allá de la pregunta original, y requieren datos que el
modelo de `Obligacion` no captura. Ver pregunta de seguimiento en `Preguntas-Para-Abogado-Abiertas.md`,
"Sprint 84 (seguimiento)", y `Pendientes.md`, Sprint 84.

---

## Sprint 86/87 — Bono pensional y cálculo actuarial de cotizaciones omisas: factores de reserva y tabla DTF Pensional

**Contexto:** las plantillas comerciales (P10, P12, P13, P14) usan una fórmula de reserva actuarial
(Decreto 1296/2022) actualizada con la DTF Pensional (Decreto 1299/1994). El desarrollo no pudo extraer con
certeza los factores F1/F2/F3 ni la serie histórica de DTF Pensional de la exportación a texto de esas
plantillas.

**Pregunta:** ¿puede el despacho aportar la definición exacta de los factores, la tabla histórica de DTF
Pensional, o los archivos Excel originales sin convertir?

**Respuesta del despacho:**
El Decreto 1296 de 2022 actualizó los componentes matemáticos obligatorios para liquidar la reserva actuarial.

Qué lógica puede seguirse?
El motor debe programar la ecuación exacta del decreto: VRA = [FAC1 × PR + FAC2 × AR] × FAC3; VR = VRA / (1 - 0.005). PR: Pensión de Referencia. AR: Auxilio Funerario (si PR < 5 SMMLV: AR = 5 SMMLV; si 5 <= PR <= 10 SMMLV: AR = PR). FAC1 y FAC2: valores extraídos de la Tabla 2 (ej. a los 55 años, Hombres FAC1=258.712212, FAC2=0.369543). FAC3: factor de capitalización (nota del despacho: "el PDF oficial presenta corrupción de caracteres en su impresión... la parametrización debe utilizar el estándar actuarial derivado: FAC3 = ((1.03^t) - 1) / ((1.03^(t1+n)) - 1) o la variación técnica corregida"). Interpolación Salario Medio Nacional (SMN): fórmula de interpolación lineal estándar.

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** respuesta parcial — da la estructura de la fórmula y un
único punto de ejemplo de la Tabla 2 (FAC1/FAC2 a los 55 años, hombres), pero sigue sin la tabla completa
(todas las edades y ambos sexos), sin la serie DTF Pensional, y sin el SMN. El propio despacho admite
incertidumbre sobre la fórmula exacta de FAC3 (dos variantes posibles, por corrupción de caracteres en el
PDF oficial). No se implementó ningún código: construir el motor con solo un punto de la tabla y una
fórmula que el despacho mismo no confirma arriesgaría calcular mal un bono pensional real. Pregunta de
seguimiento acotada (los 4 datos que faltan) en `Preguntas-Para-Abogado-Abiertas.md`, "Sprint 86/87
(seguimiento)". Ver `Pendientes.md`, Sprints 86 y 87.

---

## Sprint 90 — Fundamento legal de la fórmula IBL de últimas 100/150 semanas (régimen ISS anterior a 1994)

**Contexto:** las plantillas P15 e P16 calculan el IBL de un régimen distinto al de la Ley 100 (últimas 100
o 150 semanas cotizadas, con un factor fijo de 4.33 y topes de 90%), pero ninguna de las dos cita el
Acuerdo/Decreto específico que respalda esa fórmula ni el origen del factor 4.33.

**Pregunta:** ¿cuál es la norma exacta (probablemente un Acuerdo del ISS anterior a la Ley 100 de 1993) que
respalda la fórmula de IBL de 100/150 semanas con el factor 4.33 y el tope del 90%? ¿El despacho sigue
liquidando casos bajo este régimen histórico?

**Respuesta del despacho:**
El régimen aplicable es el Acuerdo 049 de 1990, con topes fijos en su estructura de tasas. El factor "4.33"
(semanas/mes) no se exige legalmente como constante pura del IBL histórico, el sistema debe limitarse al
45% - 90% liquidado con las fórmulas de semanas del Sprint 70.

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** cerrado sin cambios de código. La respuesta rechaza el
mecanismo distinto de las plantillas P15/P16 (promedio de últimas 100/150 semanas × factor 4.33) y remite
al régimen 45%-90% del Acuerdo 049/1990 que el Sprint 70/91 ya había implementado y probado como
`calcular_tasa_reemplazo_iss_pre_ley_100` (`app/engine/labor/ibl.py:108-126`, misma cita normativa, mismo
rango 45%-90%). Ver `Pendientes.md`, Sprint 90.

---

## Sprint 93 — Laboral: ¿en qué procesos se usa reajuste por IPC vs. por SMMLV para salarios dejados de percibir?

**Contexto:** el Sprint 93 implementó la categoría "Salarios y prestaciones dejadas de percibir", que
reconstruye salario + prestaciones para un período sin contrato vigente (reintegro, salarios caídos), con
reajuste anual IPC o SMMLV — las dos variantes que separaban las plantillas `L5` (IPC) y `L6` (SMMLV) del
despacho. El software ya ofrecía ambas opciones y dejaba que el abogado eligiera cuál aplica caso por caso;
no se había implementado ninguna regla automática que decidiera cuál usar, porque no bloqueaba la
Definición de Hecho original del sprint.

**Pregunta:** ¿en qué tipo de proceso se usa cada variante (reintegro con salarios caídos, contrato
realidad con un período sin reconocimiento, u otro), y la elección entre IPC y SMMLV es discrecional del
abogado según el caso, o depende de una regla fija? ¿Hay algún caso en que se deban aplicar ambos reajustes
combinados?

**Qué necesito exactamente:** confirmación de si la elección de índice es siempre discrecional, o una regla
concreta que determine cuál índice corresponde a cada escenario.

**Nota adicional (limitación del entorno de desarrollo):** los archivos
`L5.SALARIOS-Y-PRESTACIONES-SOCIALES-DEJADAS-DE-PERCIBIR(incrementoinflacion).md` y
`L6...(incremento-salario-minimo).md` citados como fuente del sprint no estaban disponibles en el entorno
cloud donde se desarrolló (carpeta `docs/Archivos de referencia abogado/` excluida de git por copyright del
despacho). La lógica de bloques anuales + reajuste + divisores 360/720 se implementó siguiendo la estructura
descrita por escrito en `docs/Pendientes.md` y se verificó con casos sintéticos calculados a mano
(`tests/services/test_salarios_dejados_de_percibir.py`), pero **no** se reconcilió línea por línea contra la
planilla real de L5/L6. Se recomienda un chequeo cruzado manual del "GRAN TOTAL" contra un caso real antes
de usar esta categoría en producción.

**Respuesta del despacho:**
La elección del índice para salarios dejados de percibir no es discrecional.

Podría implementarse este código:

if salario_base == SMMLV_del_año_de_causacion:
    indice_aplicable = "VARIACION_SMMLV"
else:
    indice_aplicable = "IPC_DANE"

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** implementado como
`determinar_tipo_reajuste_salarios_dejados_de_percibir` (`app/services/salarios_dejados_de_percibir.py`),
wireado como validación obligatoria en `LaboralStrategy._validar_obligacion_laboral`
(`app/services/area_strategy.py`): si el `tipo_reajuste_anual` elegido no coincide con lo que exige la
regla (comparando el salario base contra el SMLMV del año de `fecha_inicio`), la liquidación lanza
`ValueError` explícito. Ver `Pendientes.md`, Sprint 93.

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

**Estado del software (2026-08-21):** ya se implementaron, aisladas y probadas, las dos piezas que NO
dependen de esta respuesta: `calcular_aporte_contrato_realidad` (base × porcentaje) y
`calcular_bonificacion_por_servicio_escalonada` (porcentaje condicionado a un tope), ambas en
`app/engine/labor/contrato_realidad.py`, sin ningún porcentaje ni condición hardcodeada. No están cableadas
a ningún formulario, `parametro_service` ni `LaboralStrategy` todavía, ni existe el motor de consolidado
multi-año de contrato realidad: eso queda condicionado a esta respuesta.

**Respuesta del despacho:**
En un contrato realidad, el empleador sancionado debe cubrir el 100% del cálculo actuarial de pensión. No puede descontar el 4% retrospectivo del trabajador.

Cómo puede aplicarse la bonificación del Decreto 0320 de 2026:

Para liquidaciones de servidores territoriales, a partir del 1° de enero de 2026:

Si Asignación_Básica + Gastos_Representación <= 2,968,262: Bonificación = 53%.

Si supera dicho tope: Bonificación = 38%.

Control de Vigencia: A partir de 2027, las tasas cambian a 54% y 39% respectivamente.

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** sigue bloqueado — la respuesta no da un porcentaje/base
simple de pensión, revela que requiere el mismo cálculo actuarial (FAC1/FAC2/FAC3, DTF Pensional) bloqueado
en el Sprint 86/87; no menciona el aporte a salud; y la regla de bonificación (Decreto 0320/2026) no
coincide con la que citaba textualmente la plantilla L8 (35%/50%, tope 2 SMMLV) — sin confirmar si la
reemplaza o es un concepto distinto. No se implementó código nuevo. Pregunta de seguimiento en
`Preguntas-Para-Abogado-Abiertas.md`, "Sprint 94 (seguimiento)". Ver `Pendientes.md`, Sprint 94.

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

**Estado del software (2026-08-21):** ya se implementó, aislada y probada, la parte que NO depende de esta
respuesta: la fórmula aritmética de "hora extra" (`app/engine/labor/horas_extra.py:calcular_hora_extra`) y
de "recargo" (`calcular_recargo`), sin ningún porcentaje del CST ni tabla de vigencia hardcodeada. No está
cableada a ningún formulario, `parametro_service` ni `LaboralStrategy` todavía: eso queda condicionado a la
tabla de transición de la Ley 2466/2025 que pide esta pregunta.

**Respuesta del despacho:**
La reforma laboral establece recargos progresivos para festivos, pero vigencia inmediata para el horario nocturno.

Qué puede hacerse?

Jornada Nocturna: Si fecha_hecho >= "2025-12-25", el horario nocturno (recargo 35%) inicia a las 19:00 (7:00 PM). Antes de esa fecha, el nocturno empieza a las 21:00.

Dominicales/Festivos:

< "2025-07-01": 75%

>= "2025-07-01" y < "2026-07-01": 80%

>= "2026-07-01" y < "2027-07-01": 90%

>= "2027-07-01": 100%

Hard Caps Suplementarios:
if horas_extras_diarias > 2 or horas_extras_semanales > 12: raise Exception("Supera límite legal de la Ley 2466 de 2025").

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** implementado en `app/engine/labor/horas_extra.py` para 3
de los 7 conceptos: `hora_inicio_jornada_nocturna` (vigencia inmediata desde 25/12/2025), la constante
`PORCENTAJE_RECARGO_NOCTURNO` (35%, sin cambio), `porcentaje_recargo_dominical_festivo` (tabla progresiva
75%/80%/90%/100%) y `validar_limite_horas_extra_ley_2466` (topes 2h/día, 12h/semana). Los 4 conceptos
"Horas Extras..." (HED/HEN/HEFD/HEFN) siguen sin porcentaje confirmado — pregunta de seguimiento en
`Preguntas-Para-Abogado-Abiertas.md`, "Sprint 95 (seguimiento)". Ver `Pendientes.md`, Sprint 95.

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

**Estado del software (2026-08-20):** ya se implementó, aislada y probada, la parte que NO depende de esta
respuesta: el conversor puro `salario_diario_a_mensual` (`app/engine/labor/salario_domestico.py`,
fórmula `salario_diario × días_laborados_semana / 7 × 30`). No está cableado a ningún formulario ni a
`LaboralStrategy` todavía: eso queda condicionado a esta respuesta (si no hay diferencia de fórmula, el
resto del Sprint 96 es solo agregar la captura de datos al formulario Laboral; si la hay, hay que
identificarla antes de construir).

**Respuesta del despacho:**
No existe diferencia algebraica en las fórmulas de liquidación tras la Ley 1788.

Qué puede hacerse?
Reutilizar la clase general de LiquidacionPrestaciones, utilizando la base mensual.
Agregar la validación: IBC_Seguridad_Social = max(Salario_Proporcional, 1_SMMLV).

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** implementado en `app/services/area_strategy.py`
(`LaboralStrategy.liquidar`) y `app/engine/labor/salario_domestico.py`: la conversión salario_diario→mensual
se aplica antes de reutilizar `LaborScheduler` sin cambios, y el piso de IBC (`max(salario_proporcional,
1_SMMLV)`) se aplica solo a la base de `SeguridadSocialCalculator`. Columnas nuevas
`salario_diario`/`dias_laborados_semana` en `Obligacion`, migración en
`scripts/migrate_salario_domestico_sprint96.py`. Sigue sin cablear al formulario de UI (queda como pieza
pendiente, no una pregunta al despacho) y sin implementar el auxilio de transporte (no existe ningún
concepto de auxilio de transporte en el motor todavía) — pregunta de seguimiento en
`Preguntas-Para-Abogado-Abiertas.md`, "Sprint 96 (seguimiento)". Ver `Pendientes.md`, Sprint 96.

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
La liquidación de perjuicios requiere de las dos fórmulas actuariales (Consolidado y Futuro) y las Tablas de Mortalidad de la Resolución 1555 de 2010.

Para la mortalidad y los perjuicios:

Fórmulas Matrices: Consolidado = Ra × ((1+i)^n - 1)/i ; Futuro = Ra × ((1+i)^n - 1)/(i × (1+i)^n)

Carga de Tabla de Supervivencia (Base de Datos a inyectar):
Usando los datos oficiales de la Resolución 1555 de 2010, el diccionario a codificar para las expectativas de vida (e°x) es: hombres_validos: {15: 64.8, 16: 63.9, 17: 62.9, 20: 60.0, 30: 50.3, 40: 40.8, 50: 31.6, 60: 23.0, 70: 15.3, 80: 9.3, 90: 5.1, 100: 2.4, 110: 0.5}. mujeres_validas: {15: 70.0, 16: 69.1, 17: 68.1, 20: 65.1, 30: 55.4, 40: 45.7, 50: 36.2, 60: 27.0, 70: 18.6, 80: 11.3, 90: 5.8, 100: 2.5, 110: 0.5}. hombres_invalidos: {1: 43.47, 15: 38.09, 20: 35.95, 25: 33.70... 90: 3.68, 100: 1.89, 110: 1.0}.

Interpolación Actuarial de Edades: Si la víctima tiene "33 años y 7 meses", el sistema interpolará matemáticamente entre la expectativa a los 33 y a los 34.

Cálculo Futuro: El valor devuelto de la tabla (años) se multiplica estrictamente por 12 para convertirse en la variable n (meses) de la ecuación.

CONCRETAMENTE:
```
# 1. FORMULAS MATRICES
# Ra = Renta Actualizada Mensual
# i = Tasa mensual pura (0.0048676)
# n = Tiempo en meses exactos

# A. Lucro Cesante Consolidado (Pasado/Vencido)
LCC = Ra * (((1.0 + i) ** n) - 1.0) / i

# B. Lucro Cesante Futuro (Anticipado)
LCF = Ra * (((1.0 + i) ** n) - 1.0) / (i * ((1.0 + i) ** n))

# 2. EXPECTATIVA DE VIDA (Conversion de Tablas a variable 'n')
# El valor de la tabla de mortalidad de la Superfinanciera viene en AÑOS.
# El desarrollador debe multiplicarlo obligatoriamente por 12.
n_meses_futuros = Expectativa_Vida_En_Anios_Segun_Tabla * 12.0
```

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** la respuesta no contestó la pregunta de arquitectura que
se hizo (área nueva vs. submodo, ni qué variantes usa el despacho) — trajo en su lugar las fórmulas
matemáticas. Las fórmulas de anualidad (Consolidado/Futuro) y la interpolación de edades sí quedaron
completas y se implementaron como funciones aisladas, sin conectar a ningún área ni modelo de datos, en
`app/engine/civil/lucro_cesante_actuarial.py` (`tests/engine/civil/test_lucro_cesante_actuarial.py`). La
tabla de mortalidad que trajo la respuesta viene incompleta (`hombres_invalidos` truncada con "...", y no
incluye ninguna tabla `mujeres_invalidas`) — no se hardcodeó. Pregunta de seguimiento (arquitectura, alcance,
y las dos tablas de inválidos faltantes) en `Preguntas-Para-Abogado-Abiertas.md`, "Sprint 97 (seguimiento)".
Ver `Pendientes.md`, Sprint 97.

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

**Respuesta del despacho:** (el campo de respuesta llegó vacío; el despacho repitió el mismo bloque de
fórmulas y pseudocódigo que trajo bajo la pregunta del Sprint 97 en la misma ronda, sin la tabla de
mortalidad completa que pedía esta pregunta específicamente — la tabla parcial que sí llegó, con datos
reales, quedó registrada bajo la respuesta del Sprint 97, ver arriba.)

```
# 1. FORMULAS MATRICES
# Ra = Renta Actualizada Mensual
# i = Tasa mensual pura (0.0048676)
# n = Tiempo en meses exactos

# A. Lucro Cesante Consolidado (Pasado/Vencido)
LCC = Ra * (((1.0 + i) ** n) - 1.0) / i

# B. Lucro Cesante Futuro (Anticipado)
LCF = Ra * (((1.0 + i) ** n) - 1.0) / (i * ((1.0 + i) ** n))

# 2. EXPECTATIVA DE VIDA (Conversion de Tablas a variable 'n')
# El valor de la tabla de mortalidad de la Superfinanciera viene en AÑOS.
# El desarrollador debe multiplicarlo obligatoriamente por 12.
n_meses_futuros = Expectativa_Vida_En_Anios_Segun_Tabla * 12.0
```

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** sigue bloqueado — la tabla de mortalidad completa que
pedía este sprint no llegó (el contenido con datos reales de tabla llegó bajo el Sprint 97, y sigue
incompleto: `hombres_invalidos` truncada, `mujeres_invalidas` ausente). Las fórmulas de anualidad ya se
implementaron bajo el Sprint 97 (`app/engine/civil/lucro_cesante_actuarial.py`). No se duplicó la pregunta
de seguimiento — la ya registrada en "Sprint 97 (seguimiento)" cubre lo que falta aquí también. Ver
`Pendientes.md`, Sprint 98.

---

## Sprint 102 — Ejemplo numérico resuelto de indexación con abonos (X9)

**Contexto (actualizado 2026-08-20, rutina autónoma):** la plantilla `X9.INDEXACION-CON-ABONOS.md` documenta
un algoritmo de indexar un capital único, aplicar abonos parciales sucesivos, y reindexar el saldo restante
tras cada abono. El Sprint 102 verificó con un caso sintético
(`test_civil_familia_suma_unica_con_abonos_no_reproduce_el_patron_x9`, `tests/services/test_area_strategy.py`)
que el motor actual de BASTIUM **NO** reproduce este patrón — ver Sprint 104 en `Pendientes.md` para el
detalle técnico completo y la cifra exacta de la brecha ($29.084,08 de diferencia en un caso de $1.000.000
con 2 abonos). Ya no se necesitaba el ejemplo del despacho para *confirmar* si había discrepancia (ya estaba
probada con IPC real); hacía falta para decidir **cuál** de los dos comportamientos es el correcto.

**Pregunta:** confirmado que hoy BASTIUM indexa una sola vez (todo el delta hasta la fecha de corte final,
aplicado desde el día de origen) en vez de reindexar el saldo después de cada abono como describe X9 — ¿cuál
de los dos es el criterio correcto para liquidar una obligación con Suma Única y abonos parciales? Si es el
de X9 (reindexar en cada abono), ¿el despacho tiene un caso real (o puede construir uno) con capital inicial,
2-3 abonos en fechas distintas e IPC de cada fecha, ya resuelto en su Excel, para validar la reescritura del
motor antes de darla por buena?

**Qué necesito exactamente:** confirmación de cuál mecánica aplica (indexación única a la fecha de corte
final, o reindexación progresiva en cada abono) y, si es la segunda, capital inicial + fecha, cada abono con
su fecha y monto, los IPC usados en cada corte, y el resultado final esperado — igual que se hizo con el
caso real usado para validar el Sprint 76.

**Respuesta del despacho:**
La indexación global restando abonos al final es un error matemático y jurídico que genera enriquecimiento
sin causa y expone al cliente a daños y al abogado a sanciones. El Artículo 1653 del Código Civil obliga a
imputar el pago primero a intereses y luego a capital. Por lo tanto, debe liquidarse tramo por tramo.

Cómo podría hacerse?

```
def liquidar_obligacion_con_abonos(capital_historico_inicial, fecha_origen, ipc_series, abonos, fecha_liquidacion_final, tasa_interes_mensual_pura=0.0048676):
    """
    abonos: Lista de objetos o diccionarios con { 'fecha': datetime.date, 'monto': float } ordenados por fecha ascendente.
    ipc_series: Diccionario o función que retorna el índice IPC dado un mes y año.
    """
    capital_base = capital_historico_inicial
    fecha_corte_anterior = fecha_origen
    intereses_acumulados_pendientes = 0.0
    total_intereses_pagados = 0.0
    total_capital_amortizado = 0.0

    # BUCLE DE TRAMOS (CASCADA)
    for abono in abonos:
        # 1. Indexar el capital desde el corte anterior hasta el mes del abono
        ipc_anterior = ipc_series.obtener_indice(fecha_corte_anterior)
        ipc_abono = ipc_series.obtener_indice(abono.fecha)

        coeficiente_indexacion = ipc_abono / ipc_anterior
        capital_indexado = capital_base * coeficiente_indexacion

        # 2. Calcular los intereses moratorios generados SOLO en este tramo
        # Convertimos los días a meses comerciales (mes de 30 días, año de 360)
        dias_tramo = calcular_dias_comerciales_reales(fecha_corte_anterior, abono.fecha)
        meses_tramo = dias_tramo / 30.0

        intereses_del_tramo = capital_indexado * (((1.0 + tasa_interes_mensual_pura) ** meses_tramo) - 1.0)
        total_intereses_adeudados_a_la_fecha = intereses_acumulados_pendientes + intereses_del_tramo

        # 3. Imputación legal del abono (Art. 1653 Código Civil)
        if abono.monto >= total_intereses_adeudados_a_la_fecha:
            # El abono cubre todos los intereses adeudados y sobra dinero para reducir el capital
            remanente_para_capital = abono.monto - total_intereses_adeudados_a_la_fecha

            total_intereses_pagados += total_intereses_adeudados_a_la_fecha
            total_capital_amortizado += remanente_para_capital

            intereses_acumulados_pendientes = 0.0
            # El capital se reduce, creando la nueva base histórica para el siguiente tramo
            capital_base = capital_indexado - remanente_para_capital
        else:
            # El abono NO alcanza a cubrir los intereses. El capital indexado queda intacto.
            total_intereses_pagados += abono.monto
            intereses_acumulados_pendientes = total_intereses_adeudados_a_la_fecha - abono.monto

            capital_base = capital_indexado

        # 4. Actualizar la fecha pivote para el siguiente ciclo
        fecha_corte_anterior = abono.fecha

    # 5. TRAMO FINAL: Desde el último abono hasta la fecha de liquidación final exigida por el juez
    ipc_ultimo_corte = ipc_series.obtener_indice(fecha_corte_anterior)
    ipc_final = ipc_series.obtener_indice(fecha_liquidacion_final)

    capital_indexado_final = capital_base * (ipc_final / ipc_ultimo_corte)

    dias_tramo_final = calcular_dias_comerciales_reales(fecha_corte_anterior, fecha_liquidacion_final)
    meses_tramo_final = dias_tramo_final / 30.0

    intereses_tramo_final = capital_indexado_final * (((1.0 + tasa_interes_mensual_pura) ** meses_tramo_final) - 1.0)

    intereses_totales_al_cierre = intereses_acumulados_pendientes + intereses_tramo_final
    gran_total_adeudado = capital_indexado_final + intereses_totales_al_cierre

    return {
        "capital_insoluto_indexado": capital_indexado_final,
        "intereses_pendientes_cobro": intereses_totales_al_cierre,
        "gran_total_adeudado": gran_total_adeudado
    }
```

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** implementado como función aislada, traducción fiel a
Decimal, en `app/engine/indexation/suma_unica_con_abonos.py`
(`liquidar_obligacion_con_abonos_tramo_por_tramo`), probada con 8 tests
(`tests/engine/indexation/test_suma_unica_con_abonos.py`). Sin cablear a `AreaStrategy` todavía — requiere
un cambio de arquitectura del pipeline de eventos y se solapa con la tasa de interés todavía sin confirmar
del Sprint 76/83. Pregunta de seguimiento en `Preguntas-Para-Abogado-Abiertas.md`, "Sprint 104
(seguimiento)". Ver `Pendientes.md`, Sprint 104.

---

## Sprint 92 — Laboral: ¿fecha de corte real entre régimen Ley 50/1990 y Ley 789/2002 para la indemnización por despido, fórmula para salario ≥10 SMMLV, y coexistencia con la sanción moratoria?

**Contexto:** la plantilla comercial `L4.INDEMNIZACIONPORDESPIDOLABORALYSANCIONMORATORIA.md` que usa el
despacho trae dos regímenes de indemnización por despido injustificado según cuándo ingresó el trabajador,
pero cita la misma fecha ("27 de diciembre de 1.992") para ambos regímenes, atribuyéndosela una vez a la
Ley 789 de 2002 y otra vez a la Ley 50 de 1990 — que es de 1990, no de 1992. El Sprint 92 (implementado,
`app/engine/labor/dismissal_indemnity.py::DismissalIndemnityCalculator`) ya construyó el cálculo con lo que
sí quedó confirmado con cifras exactas por el propio backlog, dejando 3 puntos condicionados/sin calcular en
vez de adivinar:

1. **Fecha de corte del régimen** (45+15 días vs. 30+20 días): el software usa por defecto el 1° de enero de
   1991 (entrada en vigencia real y citable de la Ley 50 de 1990) mientras no se confirme lo contrario.
2. **Salario ≥10 SMMLV**: el backlog solo confirmó que este umbral existe y distingue tablas, pero no trajo
   la fórmula/días exactos de esa tabla — el software **no calcula** la indemnización en este caso (lanza un
   error explícito, `RegimenNoSoportadoError`, y la liquidación sigue con una alerta en vez de bloquearse).
3. **Tramos del régimen pre-Ley 50/1990 más allá de la fórmula continua confirmada** (45 días primer año + 15
   días por cada año subsiguiente): el backlog advierte que la plantilla original "trae varios regímenes por
   estos tramos" (probablemente una tasa distinta a partir de 5 o 10 años de antigüedad, como en el régimen
   del Decreto 2351/1965 anterior a la Ley 50), pero solo transcribió una cifra — el software aplica la
   fórmula continua de 15 días/año sin importar la antigüedad, lo que podría **subestimar** la indemnización
   en contratos muy antiguos si el régimen real escalona la tasa en tramos más altos.

Adicionalmente, `INDEMNIZACION_DESPIDO` (Art. 64 CST, este sprint) y `SANCION_MORATORIA` (Art. 65 CST, ya
implementada) quedaron conectadas de forma **independiente** en `LaboralStrategy`: ambas pueden coexistir en
el mismo expediente (el usuario decide si marca una, la otra, o las dos), sin que el software las sume con
ningún supuesto oculto ni bloquee su coexistencia — el backlog dice que son legalmente compatibles pero pide
confirmarlo explícitamente antes de tratarlas como una regla automática.

**Pregunta:** (a) ¿el corte entre el régimen "favorable" (45 días primer año + 15/20 días subsiguientes) y el
régimen posterior (30 días primer año + 20 días subsiguientes) es el 1° de enero de 1991 (entrada en
vigencia de la Ley 50 de 1990), o es realmente el 27 de diciembre de 1992 como cita la plantilla? (b) ¿cuál
es la fórmula/tabla completa de días de indemnización para un trabajador con salario ≥10 SMMLV (a término
indefinido)? (c) ¿el régimen anterior a la Ley 50/1990 escalona la tasa de días/año subsiguiente en tramos
de antigüedad (ej. una tasa distinta a partir de 5 o 10 años), o los 15 días/año se mantienen fijos sin
importar la antigüedad total? (d) ¿confirma que la indemnización por despido injustificado (Art. 64 CST) y
la indemnización moratoria (Art. 65 CST) pueden coexistir y liquidarse juntas en el mismo expediente sin
ninguna regla de exclusión o compensación entre ellas?

**Qué necesito exactamente:** la fecha exacta de corte; la tabla completa de días de indemnización para
salario ≥10 SMMLV (a término indefinido); la tabla completa por tramos de antigüedad del régimen anterior a
la Ley 50/1990 (si existe más de un tramo); y una confirmación sí/no de la coexistencia con la sanción
moratoria.

**Respuesta del despacho:**
Las fechas de corte son las que dictan el régimen aplicable. La convivencia de la indemnización por despido y la sanción moratoria es plena e independiente.

Qué puede hacerse:

Corte 1 (Ley 50/1990): Aplica desde el 01-Enero-1991.

Corte 2 (Ley 789/2002): Aplica desde el 27-Diciembre-2002.

Indefinidos $\ge$ 10 SMMLV:
Primer año: 20 días.
Subsiguientes: 15 días/año.

Tramos Pre-1991 (Decreto 2351/65):
Primer año: 45 días.
Subsiguientes: 15 días (si antigüedad < 5 años), 20 días (5 a <10 años), 30 días (>10 años).

**Fecha:** 22/08/2026

**Estado en el código (actualizado 2026-08-23):** implementado en `app/engine/labor/dismissal_indemnity.py`.
Las dos fechas de corte quedaron como constantes (`FECHA_CORTE_LEY_50_1990` 1991-01-01,
`FECHA_CORTE_LEY_789_2002` 2002-12-27, ambas overridable); la tabla de salario ≥10 SMMLV (20+15 días) solo
aplica a contratos con `fecha_ingreso >= 27-Dic-2002` (antes de esa fecha no existía la distinción por
salario, así que ese caso cae en el régimen general por fecha de ingreso); el régimen Decreto 2351/1965 pasó
de una tasa continua de 15 días/año a la tasa escalonada confirmada (15/20/30 días/año según la antigüedad
total del contrato, con límite inferior de cada tramo inclusivo — exactamente 5 y exactamente 10 años caen
en el tramo superior). `RegimenNoSoportadoError` se retiró (ya no existe ninguna combinación sin fórmula
confirmada). Ver `Pendientes.md`, Sprint 92.

## Sprint 8 (seguimiento 3) — Tabla real de IPC mensual anterior a enero de 2003

**Contexto:** el despacho ya respondió la pregunta de seguimiento 2 (ver
`Preguntas-Para-Abogado-Respondidas.md`, Sprint 8) con las fórmulas de "Límite de Vacío Absoluto" (fechas
anteriores al 01/08/1954 → índice 1.000000) y "Estimación Futura" (media geométrica de los últimos 12
meses para fechas posteriores al último mes certificado) — ambas ya implementadas y probadas. La
respuesta también afirma que la serie bajo la base Diciembre 2008 = 100 "tiene continuidad ininterrumpida
desde décadas anteriores a 2003" y que "no existe un vacío real en los datos mensuales". Sin embargo, el
único archivo con datos reales de IPC mensual accesible para el desarrollo (`ipc_mensual_dane_2003_2026.csv`
en `docs/datos_publicos_fuente/`, extraído programáticamente del Excel que aportó el despacho) solo cubre
enero de 2003 en adelante, base Diciembre 2018 = 100. Para fechas anteriores a 2003 (y, en particular,
para el tramo 1954-08 a 1966, donde tampoco hay variación anual cargada en `_IPC_VARIACION_ANUAL`), el
software sigue sin ningún índice mensual real, y la interpolación anual (que cubre 1967-2025) tampoco
llega hasta 1954.

**Pregunta:** ¿puede el despacho aportar la tabla real de índices IPC mensuales (base Diciembre 2008 = 100,
o cualquier base con su factor de enlace) para el período 01/08/1954 a diciembre de 2002 — el mismo tipo
de archivo (Excel/CSV) que ya aportaron para 2003-2026?

**Qué necesito exactamente:** igual que con la serie 2003-2026, un archivo con un valor de índice por mes
(no variación %), cubriendo desde agosto de 1954 (o el año más antiguo disponible) hasta diciembre de
2002. Si la fuente exacta que menciona el despacho no está en un archivo descargable, sirve la referencia
(nombre de la publicación DANE, o el enlace) para extraerla directamente.

**Respuesta del despacho:** Sólo se cuenta con el histórico del IPC desde 2003.

**Fecha:** 16/11/2026

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** sin cambio de código: no existe serie mensual oficial antes de 2003, así que se mantiene la interpolación anual como respaldo antes de 2003-01 (Sprint 8).

---

## Sprint 70/91 (seguimiento) — Fechas exactas de vigencia por régimen, invalidez Grado 1, y "régimen de transición"

**Contexto:** la respuesta del despacho del 22/08/2026 (ver `Preguntas-Para-Abogado-Respondidas.md`,
"Sprint 70/91") confirmó 4 fórmulas de tasa de reemplazo pensional que ya se implementaron y probaron como
funciones aisladas en `app/engine/labor/ibl.py` (régimen 1985-1989, ISS Pre-Ley 100/Acuerdo 049-1990, Ley
100 original 1994-2003, e invalidez grado 2). Quedaron 3 puntos sin resolver que esta rutina no adivinó:

1. **Fechas exactas de vigencia de cada régimen** — la respuesta pidió un patrón "Factory" que enrute el
   cálculo por fecha de los hechos, pero no dio el día exacto en que empieza/termina cada régimen (solo
   rangos aproximados como "1985-1989" o "Pre-Ley 100"). Sin esa fecha exacta, no se construyó el router:
   enrutar una liquidación real a un régimen equivocado por una fecha de corte mal supuesta sería un error
   de dominio grave.
2. **Invalidez Grado 1** — esta respuesta da un tope de 60%, pero una fuente anterior (plantilla comercial
   P9 del despacho, con cifras concretas verificadas: 500 semanas→45,0%, ...,1500 semanas→75,0%, Sprint 91)
   ya había confirmado un tope de 75% para el mismo grado. No se implementó ninguna función para Grado 1
   mientras esta discrepancia no se resuelva.
3. **"Régimen de transición"** (Art. 36 Ley 100 de 1993, tasa fija "75%/90%/la que corresponda") — la
   pregunta original del Sprint 91 lo pedía por ese nombre; la respuesta del 22/08 no lo menciona
   explícitamente. No está claro si "Régimen 1985-1989" es la respuesta a esto, o si sigue sin contestar.

**Pregunta:** (1) ¿cuál es la fecha exacta de entrada en vigencia y de cese de cada régimen (1985-1989, ISS
Pre-Ley 100/Acuerdo 049 de 1990, Ley 100 original, Ley 797/2003)? (2) Para invalidez Grado 1, ¿el tope
correcto es 60% (esta respuesta) o 75% (la plantilla P9)? (3) ¿El "régimen de transición" del Art. 36 Ley
100/1993 (con sus reglas propias de quién puede acogerse) es un régimen aparte de los ya confirmados, o se
resuelve con la tabla de "Régimen 1985-1989"/"ISS Pre-Ley 100" ya dada?

**Qué necesito exactamente:** una tabla de régimen → fecha desde → fecha hasta (o "vigente"), la
confirmación del tope de invalidez Grado 1, y la aclaración sobre el régimen de transición.

**Respuesta del despacho:** Fechas exactas:
Ley 33 de 1985: 13 de febrero de 1985.
Ley 71 de 1988: 28 de enero de 1989.
Acuerdo 049 de 1990 (Dec. 758/1990): 18 de abril de 1990.
Ley 100 de 1993: 1° de abril de 1994 (sector privado/nacional), hasta el 30 de junio de 1995 (orden territorial).
Ley 797 de 2003: 29 de enero de 2003.
Invalidez Grado 1: El tope correcto es el 60% del IBL (45% base por 500 semanas + 1.5% por cada 50 semanas adicionales, alcanzando el tope a las 1.000 semanas). El 75% corresponde a la Invalidez Grado 2.
Régimen de transición (Art. 36 Ley 100/1993): NO es un régimen aparte. Es un mecanismo de remisión normativa que solo preserva tres elementos del régimen anterior: Edad, Tiempo/Semanas y Monto (Tasa de Reemplazo). Todas las demás condiciones (reglas de IBL, prescripción, intereses, topes) se rigen por las normas generales de la Ley 100 de 1993 y el Acto Legislativo 01 de 2005.

**Fecha:** 16/11/2026

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 70/91 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

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
En obligaciones de dinero puro y litigios comerciales simples, el cobro del 6% se hace con la fórmula lineal de interés simple sin anatocismo. Aunque en la tasación de perjuicios y daño emergente/lucro cesante, las Altas Cortes exigen la tasa técnica mensual equivalente derivada de la E.A. Depende de la naturaleza de la obligación, resolviendo la contradicción así:
Obligación Civil de Crédito Ordinario (Simple): Debe usarse la Opción A (Fórmula Lineal Simple: 0.06 / 365). Usar fórmulas compuestas (Opción C) en deuda civil pura viola la prohibición de anatocismo de los Arts. 1617 y 2235 del C.C.
Liquidación de Perjuicios (Daño emergente/Lucro cesante en sentencias declarativas): Debe usarse la tasa pura actuarial mensual (0.0048676), conforme a la doctrina de la Sala de Casación Civil de la CSJ para fórmulas de descuento a valor presente. Podría estudiarse si se deja lineal simple para ejecución de títulos civiles y una tasa pura actuarial mensual (0.0048676) para cuantificación de perjuicios.

Qué podría hacerse?
El sistema puede tener un conmutador (flag en UI):

Si es Obligación Civil de Crédito Ordinario (Simple): tasa_diaria = 0.06 / 365

Si es Liquidación de Perjuicios / Valor (Fórmula de Cortes): tasa_mensual_pura = 0.0048676
El tiempo se puede convertir todo a meses comerciales: n = (Años * 12) + Meses + (Dias_Restantes / 30).
Fórmula de liquidación: Capital * (1 + 0.0048676)^n.

CONCRETAMENTE:
# OPCIÓN A: OBLIGACIÓN CIVIL DE CRÉDITO COMÚN (Interés Lineal / Simple)
# Se usa división simple de la tasa anual. No hay capitalización.
tasa_diaria_simple = 0.06 / 365.0
Intereses = Capital * tasa_diaria_simple * Dias_Mora_Reales

# OPCIÓN B: LIQUIDACIÓN DE PERJUICIOS JUDICIALES (Fórmula de las Cortes)
# Exige convertir el tiempo a meses comerciales exactos y usar tasa efectiva.
tasa_mensual_pura = 0.0048676  # Constante matemática inmutable (0.48676% expresado en decimal)

# Cálculo de la variable n (tiempo en meses)
n_meses = (Anios_Transcurridos * 12) + Meses_Enteros_Transcurridos + (Dias_Sobrantes / 30.0)

# Aplicación sobre el capital
Capital_Actualizado = Capital_Historico * (IPC_Final / IPC_Inicial)
Gran_Total = Capital_Actualizado * ((1.0 + tasa_mensual_pura) ** n_meses)

**Fecha:**
22/08/2026

**Bloqueado, pendiente del USUARIO (no del despacho) — 2026-08-23:** esta respuesta ya resuelve la pregunta
legal (qué fórmula usar según el tipo de obligación), pero la implementación que propone (un "conmutador"
que bifurca el motor central de tasas — usado por las 6 áreas — entre esta fórmula y la lineal, con un
régimen de conteo de tiempo nuevo de "meses comerciales") es demasiado grande y de demasiado impacto
retroactivo para que la rutina autónoma la ejecute sola. Ver `Pendientes.md`, Sprint 76, sección "Bloqueo
no previsto" para el detalle completo de por qué se detuvo, y qué necesita confirmar el usuario antes de
que se pueda programar (el mapeo exacto de "crédito ordinario simple" vs. "liquidación de perjuicios" a
los datos que ya captura BASTIUM, y si aplica con o sin recálculo retroactivo de liquidaciones existentes).

**Decisión del usuario (2026-08-25):** (1) el riesgo retroactivo queda descartado — se verificó el único
expediente real en la base de datos local (Radicado 2224, 10 liquidaciones del 13-14/08/2026) y el usuario
confirmó que fue exclusivamente para probar el software contra el Excel del despacho, nunca se entregó a un
cliente ni se presentó ante el juzgado 521; no aplica ningún protocolo de recálculo histórico (Sprint 47).
(2) El usuario pide volver a preguntarle al despacho señalando la contradicción exacta, en vez de elegir
entre A y C a ciegas.

**Pregunta de seguimiento:** para el interés civil ordinario del 6% (Art. 1617/2232 C.C., "obligación de
dinero puro" — el caso de uso mayoritario hoy en Civil/Familia, Comercial y Honorarios, ya que el dominio de
"liquidación de perjuicios" que menciona esta misma respuesta todavía no existe en BASTIUM, ver Sprint 97),
la respuesta escrita del 22/08/2026 confirma la fórmula **lineal simple** (Opción A, `6%/365`). Pero al
revisar `i7.INTERESES-CIVILES-6-ANUAL.xlsm` — la propia plantilla comercial del despacho para este mismo
interés — encontramos que esa plantilla usa una fórmula distinta (Opción C, mensual nominal con prorrateo de
30 días, verificada cifra por cifra contra su propio ejemplo: $24.500,00 en junio/30 días, $25.316,67 =
$24.500×31/30 en julio/31 días). ¿Cuál de las dos deben usar las obligaciones de dinero puro: la que
confirmaron por escrito (A), o la que su propia plantilla demuestra en la práctica (C)? Necesitamos que
resuelvan esta contradicción explícitamente antes de tocar el motor central de tasas, que afecta a las 6
áreas.

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 76 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

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
Las costas procesales como expensas y agencias en derecho son una sanción de moralización, no son un capital de crédito. Es decir, las costas procesales NO generan intereses.

Qué se debe hacer:
Un SÍ a que la regla es general: aplica en cualquier área del derecho y algoritmo. Las costas se suman "en seco" al final: Gran_Total = Capital_Indexado + Intereses_Mora + Costas_Aprobadas.
Prelación de pagos (imputación): 1°) Costas procesales aprobadas y gastos de cobro; 2°) Intereses moratorios causados; 3°) Indexación/Reajuste de capital; 4°) Capital principal (Arts. 1629, 1653, 2495 C.C. y 446 CGP). Las costas procesales NO deben incluirse en la base que genera el interés civil del 6% bajo el algoritmo de Suma Única. Se suman al final, en seco: Gran_Total = Capital_Indexado + Intereses_Mora_Calculados + Costas_Aprobadas.

En síntesis:
# 1. HONORARIOS (Interés civil sobre capital indexado)
Capital_Indexado = Capital_Original * (IPC_Final / IPC_Inicial)

# El interés se calcula usando el Capital_Indexado como base
Interes_Mora = Calcular_Interes_Civil(Base=Capital_Indexado, Tasa_Anual=0.06)

# 2. COSTAS PROCESALES (Suma plana al final, NUNCA generan intereses)
Gran_Total_Liquidacion = Capital_Indexado + Interes_Mora + Costas_Aprobadas

**Fecha:**
22/08/2026

**Bloqueado, pendiente del USUARIO (no del despacho) — 2026-08-23:** esta respuesta ya resuelve la pregunta
legal, pero implementarla exige tocar el modelo central de deuda (`PendingDebt`, 3 componentes hoy:
principal/interés/indexación) para agregar costas como un 4° componente que nunca genera interés — y la
respuesta no dice en qué posición de la prelación de pago (imputación) entra costas frente a
indexación/intereses/capital, una decisión que ninguna respuesta anterior (tampoco el Sprint 18) cubrió.
Además, la propia fórmula de síntesis sugiere que el alcance real es más amplio que "solo bajo Suma
Única" (el código de hoy ya genera interés sobre costas incluso SIN Suma Única, porque están mezcladas con
`principal`). Ver `Pendientes.md`, Sprint 79, sección "Bloqueo no previsto" para el detalle completo y lo
que necesita confirmar el usuario.

**Decisión del usuario (2026-08-25):** prefiere que ambos puntos se le devuelvan al despacho en vez de
decidirlos sin ellos.

**Pregunta de seguimiento:** (a) ¿la regla "las costas nunca generan interés civil" es general — aplica en
cualquier área y con cualquier algoritmo de liquidación — o es específica del algoritmo "Suma Única" (interés
sobre capital ya indexado)? Hoy el motor de BASTIUM genera interés sobre las costas **siempre**, con o sin
Suma Única activa, porque comparten el mismo componente de capital — necesitamos saber si eso también hay
que corregirlo en el caso general. (b) Cuando se hace un abono/pago parcial, ¿en qué posición de la
prelación de pago entran las costas frente a la indexación, los intereses y el capital — se pagan de
últimas (después de indexación → intereses → capital), de primeras, o en otra posición?

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 79 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---

## Sprint 82 (seguimiento) — ¿En qué área de BASTIUM vive el calculador de condenas administrativas (DTF)?

**Contexto:** la respuesta del despacho (22/08/2026, ver `Preguntas-Para-Abogado-Respondidas.md`, Sprint
82) dio la fórmula completa del interés de mora en condenas contra el Estado (Art. 195 núm. 4 Ley
1437/2011, régimen dual DTF/1,5x IBC), ya implementada y probada como función aislada
(`app/engine/interest/condena_administrativa_dtf.py`). Pero la pregunta original — la que en realidad
bloqueaba conectar esta fórmula a una liquidación real — nunca se contestó: ¿el despacho maneja casos de
litigio contra entidades públicas, y si es así, en cuál de las 6 áreas actuales de BASTIUM (Civil/Familia,
Comercial, Laboral, Sancionatorio, Honorarios, Tributario) deberían vivir, o hace falta un área/flujo
nuevo?

**Pregunta:** ¿pueden confirmar (1) si el despacho realmente tiene o espera tener casos de este tipo, y (2)
en qué área de BASTIUM debería aparecer el formulario/cálculo (o si se necesita una séptima área nueva)?

**Qué necesito exactamente:** un sí/no sobre si es relevante para el despacho, y la asignación de área para
poder conectar la fórmula (ya lista) a una pantalla y a una liquidación real.

**Respuesta del despacho:** Sí, a futuro mediano se espera tener este tipo de casos, por ello la maxima prioridad es desarrollar primero los cálculos en derecho de familia, civil y laboral, este tipo de casos de derecho administrativo pueden venir paulatinamente a la firma. Sí, es relevante para litigio contra entidades públicas. Debe residir en un módulo independiente y aislado (ej. una 7ª área o submódulo específico de "Condenas Estado CPACA"). No puede mezclarse con el motor civil/comercial/tributario porque posee un régimen dual único (10 meses a tasa DTF, luego 1.5x IBC) y una causal de cese de intereses a los 3 meses por inactividad del acreedor (Art. 192.4 CPACA), lo que rompería la lógica de los otros motores.

**Fecha:** 16/11/2026

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** no se implementa todavía por prioridad del propio despacho (familia, civil y laboral primero). Queda como módulo independiente futuro "Condenas Estado CPACA" (7ª área o submódulo aislado). Ver `Pendientes.md`, Sprint 82.

---

## Sprint 84 (seguimiento) — Imputación proporcional (Art. 804 E.T.) y tope suspensivo por demanda contenciosa

**Contexto:** la respuesta del despacho a la pregunta original del Sprint 84 (¿366 días lineal o 365
compuesto para el interés moratorio tributario?) ya se implementó — ver
`Preguntas-Para-Abogado-Respondidas.md`, Sprint 84. La misma respuesta trajo además dos reglas que van más
allá de esa pregunta y quedaron sin implementar:

1. **Imputación proporcional (Art. 804 E.T.):** cuando hay un abono, en vez de la regla civil (intereses
   primero, luego capital), el abono se reparte proporcionalmente entre capital/sanción/interés según el
   peso de cada uno en la deuda total. Hoy `calcular_interes_moratorio_tributario` no maneja abonos en
   absoluto ("Capital fijo, sin abonos ni imputación de pagos -- eso es Sprint 11b", según su propio
   docstring) — implementar esto requiere construir esa imputación desde cero, con su propio diseño.
2. **Tope suspensivo:** a los 24 meses de admitida una demanda contenciosa, el interés deja de causarse
   hasta 11 días después de la sentencia. Esto necesita datos que el modelo de `Obligacion` no captura hoy
   (fecha de admisión de la demanda, fecha de la sentencia).

**Pregunta:** ¿estas dos reglas aplican de forma general a toda obligación Tributaria, o solo a un
escenario específico (ej. solo cuando ya existe un proceso contencioso administrativo en curso)? ¿Qué
campos nuevos necesitaría capturar el formulario de Obligación Tributaria para poder calcularlas (fecha de
admisión de demanda, fecha de sentencia, u otros)?

**Qué necesito exactamente:** confirmación de si estas reglas son prioritarias para el despacho ahora
mismo, y si es así, los campos exactos que hacen falta capturar para implementarlas correctamente.

**Respuesta del despacho:** Ambas reglas aplican de forma general a toda obligación tributaria. La imputación proporcional es imperativa (no se imputa primero a intereses como en lo civil). Campos nuevos obligatorios en el formulario: fecha_admision_demanda, fecha_tope_24m (calculado: admisión + 24 meses), fecha_notificacion_sentencia y fecha_reanudacion_interes (calculado: notificación + 11 días).

**Fecha:** 16/11/2026

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 84 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---

## Sprint 85 — Retroactivo pensional: tasa de mora del Art. 141 Ley 100, y vigencia del incremento 14%/7%

**Contexto:** el retroactivo y reliquidación pensional (mesada por mesada, con incrementos e intereses de
mora) es la funcionalidad más solicitada de las 16 plantillas de referencia del despacho (4 de 16 la
necesitan). Dos piezas de esta funcionalidad requieren confirmación legal antes de poder programarse — el
recálculo mesada a mesada contra el SMLMV histórico y la indexación IPC de cada mesada (Art. 21 Ley 100) no
dependen de ninguna de las dos preguntas de abajo y se documentan aparte como la pieza aislable de este
sprint.

**Pregunta 1 — tasa del interés de mora (Art. 141 Ley 100):** el Art. 141 de la Ley 100 de 1993 dice que, en
caso de mora en el pago de mesadas pensionales, la entidad debe reconocer "la tasa máxima de interés
moratorio vigente en el momento en que se efectúe el pago". BASTIUM ya calcula un tope de usura vigente por
fecha (`calcular_tope_usura`, `app/engine/interest/usury_validator.py`, usado para el techo del Art. 867-1
E.T., Sprint 15). ¿Es esa la misma tasa que exige el Art. 141 Ley 100, o es una tasa distinta (por ejemplo,
el interés bancario corriente puro, sin el multiplicador de usura)?

**Pregunta 2 — vigencia del incremento 14%/7%:** la plantilla `P1A.RETROACTIVO-PENSIONAL-SALARIO-MINIMO-INDEXADO-O-INCREMENTO-PENSIONAL-DEL-14-o-7.md`
trae un incremento pensional del 14% (cónyuge) o 7% (hijo) sobre la mesada, citando las sentencias SU-140-19
y SL-2334-19 como referencia de vigencia — pero la propia plantilla marca esa vigencia como dudosa, sin
confirmarla. ¿Sigue vigente hoy ese incremento, o ya no aplica?

**Qué necesito exactamente:** (1) confirmación de si el interés de mora del Art. 141 es la misma tasa de
usura que ya calcula BASTIUM, o el fundamento y la tabla de la tasa correcta si es distinta; (2) un sí/no
sobre la vigencia actual del incremento 14%/7%, con la norma/sentencia que lo respalde si sigue vigente.

**Respuesta del despacho:** 1. Tasa de mora: Es la tasa máxima de interés moratorio vigente (tasa de usura) certificada por la Superfinanciera. Excepción: Si la entidad prueba buena fe estricta o cambio jurisprudencial, solo aplica la indexación por IPC, sin intereses de usura.
2. Incremento 14%/7%: NO sigue vigente. La Corte Constitucional (SU-140 de 2019) determinó que no aplican para pensiones causadas con posterioridad a la Ley 100 de 1993 o al Acto Legislativo 01 de 2005.

**Fecha:** 16/11/2026

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 85 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---

## Sprint 86/87 (seguimiento) — Tabla actuarial completa (FAC1/FAC2), serie DTF Pensional, y cuál fórmula de FAC3 es la correcta

**Contexto:** la respuesta del despacho del 22/08/2026 (ver `Preguntas-Para-Abogado-Respondidas.md`, Sprint
86/87) dio la estructura de la fórmula de reserva actuarial y la regla de Auxilio Funerario, pero no lo que
realmente pedía la pregunta original:

1. **FAC1/FAC2**: solo se dio UN punto de la Tabla 2 (hombres, 55 años: FAC1=258.712212, FAC2=0.369543) —
   se necesita la tabla completa (todas las edades relevantes, ambos sexos).
2. **DTF Pensional**: la serie histórica mensual desde enero de 1994 sigue sin llegar.
3. **FAC3**: el propio despacho señaló que el PDF oficial tiene "corrupción de caracteres" en la fórmula, y
   ofreció dos posibles lecturas ("el estándar actuarial derivado" o "la variación técnica corregida") sin
   confirmar cuál es la correcta.
4. **Salario Medio Nacional (SMN)**: se dio la fórmula de interpolación pero no la tabla de valores.

**Pregunta:** ¿puede el despacho aportar (1) la tabla completa de FAC1/FAC2 por edad y sexo (Tabla 2), (2)
la serie DTF Pensional mensual desde 1994, (3) la fórmula exacta de FAC3 sin la corrupción de caracteres
del PDF (o confirmar cuál de las dos variantes propuestas es la correcta), y (4) la tabla de Salario Medio
Nacional? Alternativamente, ¿pueden aportar los archivos Excel originales de P10/P12/P13/P14 sin convertir?

**Qué necesito exactamente:** los 4 datos/tablas de arriba, o el archivo Excel original.

**Respuesta del despacho:** Al tratarse de datos de entidades oficiales, dificilmente creo que pueden generarse por fórmula dinámica. Podríamos importarlas como tablas de datos parametrizadas (.csv / DB Table) con interpolación lineal. Sólo se tienen los siguientes datos:

1. TABLA 2: FACTORES ACTUARIALES FAC1 Y FAC2 POR EDAD Y SEXO (Fuente: Decreto 1296 de 2022, Artículo 1, Tabla 2 - Resolución 1555 de 2010 SFC)

| Edad | FAC1_Hombres | FAC1_Mujeres | FAC2_Hombres | FAC2_Mujeres |
|---|---|---|---|---|
| 55 | 258.712212 | 243.005182 | 0.369543 | 0.311687 |
| 56 | 255.775386 | 239.546338 | 0.381199 | 0.322235 |
| 57 | 252.738260 | 235.977078 | 0.393132 | 0.333081 |
| 58 | 249.598775 | 232.296362 | 0.405334 | 0.344225 |
| 59 | 246.355000 | 228.506137 | 0.417797 | 0.355667 |
| 60 | 243.005182 | 224.606020 | 0.430511 | 0.367403 |
| 61 | 239.546338 | 220.596052 | 0.443465 | 0.379431 |
| 62 | 235.977078 | 216.476560 | 0.456646 | 0.391747 |
| 63 | 232.296362 | 212.248425 | 0.470038 | 0.404345 |
| 64 | 228.506137 | 207.912956 | 0.483532 | 0.417217 |
| 65 | 224.606020 | 203.471943 | 0.497111 | 0.430356 |
| 66 | 220.596052 | 198.927674 | 0.510762 | 0.443751 |
| 67 | 216.476560 | 194.283137 | 0.524466 | 0.457390 |
| 68 | 212.248425 | 189.541818 | 0.538207 | 0.471261 |
| 69 | 207.912956 | 184.707913 | 0.551966 | 0.485348 |
| 70 | 203.471943 | 179.786208 | 0.565725 | 0.499635 |
| 71 | 198.927674 | 174.782204 | 0.579465 | 0.514104 |
| 72 | 194.283137 | 169.702078 | 0.593165 | 0.528734 |
| 73 | 189.541818 | 164.552725 | 0.606808 | 0.543503 |
| 74 | 184.707913 | 159.341662 | 0.620372 | 0.558388 |
| 75 | 179.786208 | 154.077066 | 0.633837 | 0.573365 |
| 76 | 174.782204 | 148.767735 | 0.647184 | 0.588406 |
| 77 | 169.702078 | 143.423124 | 0.660392 | 0.603484 |
| 78 | 164.552725 | 138.053206 | 0.673442 | 0.618571 |
| 79 | 159.341662 | 132.668444 | 0.686313 | 0.633634 |
| 80 | 154.077066 | 127.279561 | 0.698988 | 0.648645 |
| 81 | 148.767735 | 121.897577 | 0.711448 | 0.663572 |
| 82 | 143.423124 | 116.533716 | 0.723675 | 0.678385 |
| 83 | 138.053206 | 111.199165 | 0.735655 | 0.693051 |
| 84 | 132.668444 | 105.904739 | 0.747370 | 0.707542 |
| 85 | 127.279561 | 100.661169 | 0.758807 | 0.721827 |
| 86 | 121.897577 | 95.478330 | 0.769955 | 0.735880 |
| 87 | 116.533716 | 90.365266 | 0.780801 | 0.749677 |
| 88 | 111.199165 | 85.329825 | 0.791336 | 0.763196 |
| 89 | 105.904739 | 80.378652 | 0.801555 | 0.776422 |
| 90 | 100.661169 | 75.516659 | 0.811453 | 0.789343 |

2. FORMULACIÓN DE LA SERIE Y ACTUALIZACIÓN CON DTF PENSIONAL (Fuente: Decreto 1296 de 2022, Artículo 1)

Para actualizar la Reserva Actuarial ($VR$) a la fecha de cálculo con el DTF Pensional, se utiliza una Tasa Real de Rendimiento (TIRR) del 3% ($1.03$).

La fórmula de cálculo del DTF Pensional por período anual es:

```
DTF_Pensional_i = 1.03 * (1 + (INF_i / 100))
```

Donde:
- INF_i: Variación anual del Índice de Precios al Consumidor (IPC) certificado por el DANE para el año calendario inmediatamente anterior.
- Prorrateo: Se prorratea según la cantidad de días efectivamente transcurridos dentro de cada período.

3. FÓRMULA EXACTA DEL FACTOR ACTUARIAL 3 (FAC3) (Fuente: Decreto 1296 de 2022, Artículo 1)

Ambas variantes propuestas en la normativa son correctas y complementarias, dependiendo de si el trabajador registra cotizaciones o tiempos reconocidos previos al período omitido objeto del cálculo actuarial:

Variante 1: Estándar (Sin tiempos cotizados previos al período omitido). Se utiliza cuando $t$ corresponde únicamente al tiempo a convalidar del período omitido actual:

```
FAC3 = ( (1.03^t) - 1 ) / ( (1.03^(t + n)) - 1 )
```

Variante 2: Con tiempo acumulado previo ($t_1$). Se utiliza cuando existe sumatoria de tiempos cotizados u omitidos previos ($t_1 = t + \text{tiempos previos}$):

```
FAC3 = [ ((1.03^t1) - 1) / t1 ] / [ ((1.03^(t1 + n)) - 1) / (t1 + n) ]
```

Donde:
- t: Tiempo de convalidación a la fecha de corte (en años y fracción, redondeado a 6 decimales).
- n: Tiempo faltante desde la fecha de corte ($FC$) hasta la edad de referencia ($FR$).
- t1: Sumatoria del tiempo omitido actual más los tiempos cotizados u omitidos previos de los que exista un pago.

4. TABLA 1: SALARIOS MEDIOS NACIONALES (SMN) (Fuente: Decreto 1296 de 2022, Artículo 1, Tabla 1 - Decreto 2779 de 1994 / Res. 1588 de 1994 DANE)

Expresada en términos de índice con base 1.000000 a los 12 años:

| Edad | Salario_Medio | Edad | Salario_Medio |
|---|---|---|---|
| 12 | 1.000000 | 42 | 3.020004 |
| 13 | 1.006649 | 43 | 3.041946 |
| 14 | 1.135599 | 44 | 3.058210 |
| 15 | 1.206678 | 45 | 3.068682 |
| 16 | 1.279752 | 46 | 3.073323 |
| 17 | 1.354687 | 47 | 3.072096 |
| 18 | 1.431251 | 48 | 3.065019 |
| 19 | 1.509273 | 49 | 3.052111 |
| 20 | 1.588504 | 50 | 3.033468 |
| 21 | 1.668693 | 51 | 3.009187 |
| 22 | 1.749612 | 52 | 2.979401 |
| 23 | 1.830933 | 53 | 2.944284 |
| 24 | 1.912388 | 54 | 2.904026 |
| 25 | 1.993652 | 55 | 2.858858 |
| 26 | 2.074416 | 56 | 2.809030 |
| 27 | 2.154318 | 57 | 2.754790 |
| 28 | 2.233031 | 58 | 2.696446 |
| 29 | 2.310209 | 59 | 2.634304 |
| 30 | 2.385489 | 60 | 2.568691 |
| 31 | 2.458524 | 61 | 2.499933 |
| 32 | 2.528971 | 62 | 2.428355 |
| 33 | 2.596463 | 63 | 2.354341 |
| 34 | 2.660676 | 64 | 2.278237 |
| 35 | 2.721264 | 65 | 2.200368 |
| 36 | 2.777921 | 66 | 2.121119 |
| 37 | 2.830357 | 67 | 2.040814 |
| 38 | 2.878287 | 68 | 1.959800 |
| 39 | 2.941441 | 69 | 1.878421 |
| 40 | 2.959570 | 70 | 1.796985 |
| 41 | 2.992482 | 71+ | 1.715798 |

Regla de Interpolación para Edades No Enteras:

```
v0 = (d1 * v2 + d2 * v1) / (d1 + d2)
```

- v0: Salario Medio Nacional interpolado a la fecha intermedia.
- v1: SMN a la edad en años cumplidos.
- v2: SMN a la edad posterior.
- d1: Días transcurridos desde el último cumpleaños.
- d2: Días faltantes para el siguiente cumpleaños.

5. REGISTRO DIRECTO DE LOS APARTADOS P10/P12/P13/P14 (Fuente: Decreto 1296 de 2022, Art. 1, incisos de cálculo actuarial)

Los parámetros correspondientes a las secciones técnicas sin convertir expresan:

Fórmula del Valor de la Reserva Actuarial (VRA):

```
VRA = [ (FAC1 * PR) + (FAC2 * AR) ] * FAC3
```

Comisión de Administración (CA) y Valor Final de la Reserva (VR):

```
CA = 0.005 * VRA   (0.5% del valor de la reserva)
VR = VRA / (1 - CA) = VRA / 0.995
```

Salario de Referencia (SR):

```
SR = SB * ( SMN_FR / SMN_FC )
```

- SB: Salario Base de Liquidación actualizado a la fecha de corte.
- SMN_FR: Salario Medio Nacional a la edad de referencia.
- SMN_FC: Salario Medio Nacional a la edad a la fecha de corte.

Auxilio Funerario de Referencia (AR):

```
Si PR < 5 SMLV   => AR = 5 SMLV
Si 5 SMLV <= PR <= 10 SMLV => AR = PR
Si PR > 10 SMLV  => AR = 10 SMLV
```

**Fecha:** 16/11/2026

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 86/87 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---

## Sprint 94 (seguimiento) — aporte a salud en contrato realidad, y si el Decreto 0320/2026 reemplaza la regla de bonificación por servicio de la plantilla L8

**Contexto:** la primera ronda de esta pregunta (ver `Preguntas-Para-Abogado-Respondidas.md`, "Sprint 94")
obtuvo respuesta el 22/08/2026, pero deja dos puntos sin resolver:

1. **Aporte a salud**: la respuesta solo habla de pensión ("el empleador sancionado debe cubrir el 100% del
   cálculo actuarial de pensión"), sin mencionar salud en absoluto. Además, esa respuesta revela que el
   aporte a pensión de contrato realidad no es un simple porcentaje sobre una base, sino un **cálculo
   actuarial** — que depende de los mismos datos que siguen bloqueando el Sprint 86/87 (factores
   FAC1/FAC2/FAC3 completos por edad/sexo, y la serie DTF Pensional). No es una pregunta nueva, es el mismo
   bloqueo de fondo del Sprint 86/87.
2. **Bonificación por servicio**: la respuesta trae una regla del "Decreto 0320 de 2026" para "servidores
   territoriales" (53%/38% desde 2026, 54%/39% desde 2027, tope $2.968.262 sobre Asignación Básica + Gastos
   de Representación) que no coincide en nada — ni porcentajes, ni base, ni condición del tope — con la
   regla que citaba textualmente la plantilla L8 del despacho (35%/50%, tope 2 SMMLV). ¿El Decreto
   0320/2026 reemplaza/actualiza la regla que traía L8, o son dos bonificaciones distintas y la pregunta
   original sigue sin responder?

**Pregunta:** (a) ¿qué porcentaje(s) de aporte a salud son reclamables en un contrato realidad (total o solo
la porción del empleador)? (b) ¿el Decreto 0320/2026 es la norma que reemplaza la regla 35%/50% de la
plantilla L8, o es una bonificación distinta? Si reemplaza la regla de L8, ¿aplica también al contrato
realidad del sector privado (L7) o es exclusiva de "servidores territoriales"?

**Qué necesito exactamente:** el porcentaje de aporte a salud reclamable, y una confirmación explícita de
si el Decreto 0320/2026 sustituye la regla de bonificación de L8 o es un concepto aparte.

**Respuesta del despacho:** 1. Salud en contrato realidad: El empleador sancionado debe cubrir el 100% del cálculo actuarial o de la cotización omisa. No puede descontar retroactivamente la porción del 4% a cargo del trabajador, pues sería beneficiarse de su propia culpa.
2. Decreto 0320/2026: Es una bonificación exclusiva para servidores públicos y empleados territoriales. NO reemplaza ni aplica a las relaciones de trabajo del sector privado (plantilla L8), donde rigen las reglas del CST y la prohibición de bonificaciones pensionales extralegales posteriores a julio de 2010.

**Fecha:** 23/08/2026 (reformulación tras respuesta no concluyente del 22/08/2026)

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 94 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---

## Sprint 95 (seguimiento) — porcentajes de los 4 conceptos "Horas Extras..." (HED, HEN, HEFD, HEFN) tras la Ley 2466/2025

**Contexto:** la primera ronda de esta pregunta (ver `Preguntas-Para-Abogado-Respondidas.md`, "Sprint 95")
obtuvo respuesta el 22/08/2026, confirmando la vigencia de 3 de los 7 conceptos de la plantilla L3: horario
de inicio de la jornada nocturna (`hora_inicio_jornada_nocturna`), porcentaje del recargo nocturno (35%,
constante) y la tabla progresiva del recargo dominical/festivo (`porcentaje_recargo_dominical_festivo`),
todos implementados en `app/engine/labor/horas_extra.py`. La respuesta NO restableció los porcentajes de los
otros 4 conceptos — "Horas Extras Ordinarias Diurnas", "Horas Extras Ordinarias Nocturnas", "Horas Extras
Festivas Diurnas", "Horas Extras Festivas Nocturnas" (HED/HEN/HEFD/HEFN) — que combinan hora extra con
festivo/nocturno, y no es evidente si estos se calculan aplicando directamente los porcentajes tradicionales
del CST (25%/75%/100%/150%) sin cambio, o si también están sujetos a alguna transición de la Ley 2466/2025
(en particular HEFD/HEFN, que incorporan el recargo festivo que SÍ cambia progresivamente).

**Pregunta:** ¿cuáles son los porcentajes vigentes (y su vigencia por fecha, si aplica) de los 4 conceptos
"Horas Extras..." de la plantilla L3 — diurna/nocturna, ordinaria/festiva? En particular, ¿las horas extra
festivas (HEFD/HEFN) incorporan la misma tabla progresiva del recargo dominical/festivo (75%→80%→90%→100%),
o tienen su propio porcentaje fijo?

**Qué necesito exactamente:** el porcentaje (o tabla de vigencia) de cada uno de los 4 conceptos.

**Respuesta del despacho:** Las horas extra festivas SÍ incorporan la tabla progresiva del recargo dominical/festivo. HED: 25% (Factor 1.25).
HEN: 75% (Factor 1.75).
HEFD y HEFN (Tramo 1: Jul 2025 - Jun 2026, recargo festivo 80%): HEFD = 105% (Factor 2.05); HEFN = 155% (Factor 2.55).
HEFD y HEFN (Tramo 2: Jul 2026 - Jun 2027, recargo festivo 90%): HEFD = 115% (Factor 2.15); HEFN = 165% (Factor 2.65).
HEFD y HEFN (Tramo 3: Jul 2027 en adelante, recargo festivo 100%): HEFD = 125% (Factor 2.25); HEFN = 175% (Factor 2.75).

**Fecha:** 23/08/2026 (reformulación tras respuesta parcial del 22/08/2026)

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 95 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---

## Sprint 96 (seguimiento) — auxilio de transporte pactado por día en trabajo doméstico

**Contexto:** la primera ronda de esta pregunta (ver `Preguntas-Para-Abogado-Respondidas.md`, "Sprint 96")
confirmó que no hay diferencia de fórmula para las prestaciones sociales (cesantías/intereses/prima/
vacaciones) del trabajo doméstico, y ya se implementó la conversión salario_diario→mensual y el piso de IBC
de seguridad social. La plantilla L2A también menciona un "auxilio de transporte" pactado por día con la
misma lógica de conversión, pero **el motor de liquidación no tiene ningún concepto de auxilio de
transporte hoy** (no existe en ninguna parte de `app/engine/`) — construirlo desde cero (cuándo aplica, con
qué tope de salarios, cómo se indexa) está fuera del alcance de la respuesta ya recibida.

**Pregunta:** ¿el auxilio de transporte es un concepto que el despacho necesita liquidar en un contrato de
trabajo doméstico? Si es así, ¿bajo qué regla se causa (tope de salarios, valor vigente por año) y se
liquida junto con las demás prestaciones?

**Qué necesito exactamente:** confirmación de si esta funcionalidad es necesaria, y si lo es, la regla
completa del auxilio de transporte a implementar.

**Nota adicional (resuelta 2026-08-26):** la captura de `salario_diario`/`dias_laborados_semana` en el
formulario Laboral (`app/views/obligaciones.py`) ya se conectó — no dependía de ninguna respuesta adicional
del despacho, era solo trabajo de UI pendiente (ver `Pendientes.md`, Sprint 96, "Cierre"). Esta nota queda
solo como registro histórico; la única pregunta que sigue abierta en esta sección es la del auxilio de
transporte, arriba.

**Respuesta del despacho:** Sí, es un concepto que debe liquidarse. Aplica para salarios de hasta 2 SMMLV. Para trabajo doméstico por días o jornadas fraccionadas, se liquida estricta y proporcionalmente a los días efectivamente laborados en el mes (Auxilio_Mensual / 30) * Días_Trabajados. Además, este auxilio forma parte obligatoria de la base de liquidación para cesantías y prima de servicios.

**Fecha:** 23/08/2026 (seguimiento tras respuesta del 22/08/2026)

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 96 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---

## Sprint 97 (seguimiento) — decisión de arquitectura pendiente: ¿séptima área de derecho o submodo de Civil/Familia?, ¿cuáles variantes usa el despacho?, y tabla de mortalidad completa (hombres/mujeres inválidos)

**Contexto:** la primera ronda de esta pregunta (ver `Preguntas-Para-Abogado-Respondidas.md`, "Sprint 97")
obtuvo respuesta el 22/08/2026, pero la respuesta no contestó la pregunta que se hizo — en vez de la decisión
de arquitectura y el alcance real de uso, trajo las fórmulas matemáticas de anualidad (ya implementadas de
forma aislada, sin conectar: `app/engine/civil/lucro_cesante_actuarial.py`) y una tabla de mortalidad
parcial. La pregunta original sigue exactamente igual de abierta:

1. **Arquitectura**: ¿este motor se construye como una séptima área de derecho separada, o como una
   extensión de Civil/Familia?
2. **Alcance real**: ¿cuáles de las 6 variantes de reparto de beneficiario (víctima incapacitada, cónyuge e
   hijos, padres de víctima adulta, padres de hijo menor, pensionado de fondo privado, beneficio dejado de
   percibir) litiga realmente el despacho?
3. **Tabla de mortalidad incompleta**: la respuesta trajo `hombres_validos` y `mujeres_validas` completas
   (edades 15-110), pero `hombres_invalidos` llegó truncada ("...25: 33.70... 90: 3.68...", con un salto sin
   explicar entre esos dos puntos) y **no incluye ninguna tabla `mujeres_invalidas`** — necesaria para
   cualquier víctima incapacitada mujer.
4. **Doctrina de "fruto civil" (Sprint 100, ligado a esta misma decisión de arquitectura):** el "beneficio
   dejado de percibir como fruto civil" (`X6.LIQUIDACION-BENEFICIO-DEJADO-DE-PERCIBIR-COMO-FRUTO-CIVIL.md`)
   usa una mecánica casi idéntica a la de cuotas recurrentes + reajuste anual que BASTIUM ya tiene construida
   para Civil/Familia (Sprint 41/75: `IBL × tasa de reemplazo` como cuota inicial, reajustada una vez al año
   e indexada por IPC mes a mes). El usuario prefiere que el despacho confirme la doctrina exacta antes de
   conectar ese mecanismo existente a este nuevo caso de uso, en vez de asumirlo por similitud estructural.

**Pregunta:** (a) ¿nueva área de derecho o submodo de Civil/Familia? (b) ¿cuáles variantes construir
primero? (c) ¿pueden completar la tabla `hombres_invalidos` (todas las edades, sin saltos) y aportar la
tabla `mujeres_invalidas` completa? (d) Para el "beneficio dejado de percibir como fruto civil": ¿el
mecanismo de cuota recurrente (`IBL × tasa de reemplazo`, reajustada anualmente e indexada mes a mes por
IPC) reproduce fielmente esta figura, o hay algo en la doctrina de "fruto civil" que la distinga de una
cuota alimentaria/pensional a efectos de cómo se calcula o se reporta?

**Qué necesito exactamente:** la decisión de arquitectura y alcance, las dos tablas de mortalidad de
inválidos completas, y la confirmación sobre la mecánica de "fruto civil".

**Respuesta del despacho:** 1. Arquitectura: El módulo de "Fruto Civil" debe residir en el área Civil (acciones reivindicatorias, resolución de contratos), no como submodo de familia.
2. Fruto Civil: NO debe usar el mecanismo de cuota recurrente pensional (IBL × tasa de reemplazo). Eso es un error de derecho sustancial. El fruto civil se calcula sobre el rendimiento financiero u operativo real del activo (ej. canon de arrendamiento de mercado), indexado mes a mes por IPC, deduciendo solo gastos ordinarios de conservación (Art. 964 C.C.).
3. Tablas de mortalidad: Las tablas completas de hombres y mujeres inválidos son dependencias de datos externos (SFC) que deben importarse como tablas parametrizadas, no generarse por fórmula.

**Fecha:** 23/08/2026 (reformulación tras respuesta no concluyente del 22/08/2026); punto (d) agregado
2026-08-25 tras revisión con el usuario.

---

Nota: la pregunta del Sprint 98 (tabla completa de mortalidad de rentistas) recibió la misma respuesta que
llegó bajo la pregunta del Sprint 97 en la misma ronda (22/08/2026) — ver
`Preguntas-Para-Abogado-Respondidas.md`, "Sprint 98", y el seguimiento ya consolidado en "Sprint 97
(seguimiento)" arriba, que cubre exactamente lo que sigue faltando (tabla `hombres_invalidos` completa y
`mujeres_invalidas`, ausente por completo).

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 97 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---

## Sprint 105 — Catálogo de tipos de proceso, subtipos de caso y obligaciones predefinidas para el intake de un expediente

**Contexto:** el despacho pidió (2026-08-13/2026-08-22) que al crear un expediente, después de elegir el
área del derecho, aparezca un campo de tipo de proceso (declarativo, monitorio, ejecutivo) y, según ese tipo,
una lista de subtipos de caso (ej. Civil/Familia + Ejecutivo → "Ejecutivo de alimentos"); al elegir el
subtipo, el sistema ya debería tener preparadas las obligaciones típicas de ese subtipo (para un ejecutivo de
alimentos: la cuota de alimentos recurrente siempre está, opcionalmente subsidios/vestuario/50% de
educación-salud). Hoy no existe ningún campo de tipo de proceso ni de subtipo de caso en el sistema — es
alcance enteramente nuevo, y el catálogo exacto es un catálogo jurídico, no una decisión de UI.

**Pregunta:** (a) ¿cuál es el catálogo completo de tipos de proceso por área del derecho, y de subtipos de
caso por cada tipo de proceso? Empezando por el ejemplo dado (Civil/Familia + Ejecutivo → "Ejecutivo de
alimentos"), ¿cuáles son los demás subtipos que el despacho maneja regularmente? (b) para cada subtipo, ¿cuál
es la lista exacta de obligaciones predefinidas (nombre, periodicidad, si es obligatoria u opcional)? (c)
cuando el abogado elige un subtipo, ¿las obligaciones predefinidas deben crearse automáticamente, o solo
quedar sugeridas/marcables en una lista para que el abogado confirme cuáles aplican a ese caso?

**Qué necesito exactamente:** el catálogo completo (tipo de proceso → subtipo → obligaciones predefinidas),
empezando por Civil/Familia si es el área de mayor volumen, y la respuesta a (c).

**Respuesta del despacho:** Se plantea la siguiente estructura general de procesos por area jurídica, aunque puede nutrirse más adelante:

**1. Rama Civil y Comercial**

- [PUERTA LÓGICA] ¿La obligación dineraria es expresa, clara, exigible y no está siendo objetada por el deudor/aseguradora?
  - SÍ: Proceso Ejecutivo. Descripción: Trámite de cobro forzado. Requiere presentación del título y, en materia de seguros, acreditar la reclamación formal y el vencimiento de un mes sin objeción de la compañía.
  - NO: Proceso Declarativo (Verbal o Verbal Sumario). Descripción: Resuelve controversias sustanciales o negociales donde el derecho está en debate (ej. objeción de pólizas, responsabilidad civil). Exige como requisito ineludible de procedibilidad la audiencia de conciliación extrajudicial.
- [PUERTA LÓGICA] ¿Se busca finiquitar la comunidad sobre un derecho real?
  - Proceso Divisorio. Descripción: Liquidación material o venta del bien común al 100% del avalúo; está expresamente excluido de requerir conciliación previa.
- [PUERTA LÓGICA] ¿El deudor es persona natural (no comerciante) en cesación de pagos?
  - Trámite de Insolvencia. Descripción: Procedimiento de negociación de deudas con salvaguardas legales que prohíben condonar impuestos e imponen una prelación estricta de pagos (1ra clase: alimentos, créditos laborales, fisco).

**2. Rama de Familia**

- [PUERTA LÓGICA] ¿Se busca el pago de obligaciones de sustento incumplidas?
  - Ejecutivo de Alimentos. Descripción: Ejecución que incluye la liquidación pormenorizada de capital vencido e intereses moratorios (0,5% mensual), permitiendo el embargo y la retención anticipada de depósitos judiciales.
- [PUERTA LÓGICA] ¿Una persona mayor de edad con discapacidad requiere formalizar asistencia jurídica?
  - Proceso de Adjudicación Judicial de Apoyos. Descripción: Proceso de jurisdicción voluntaria o verbal sumario utilizado cuando los apoyos no han sido formalizados de mutuo acuerdo ante notario o centro de conciliación.

**3. Rama Laboral y de Seguridad Social**

- [PUERTA LÓGICA] ¿Existe litigio sobre expectativas de derechos (ej. transición pensional, afiliaciones omitidas)?
  - Proceso Ordinario Laboral. Descripción: Proceso que dirime controversias sustantivas (como el régimen de transición o cálculos actuariales), donde la conciliación extrajudicial es apenas potestativa y no un requisito de procedibilidad.

**4. Rama Penal**

- [PUERTA LÓGICA] ¿En qué etapa se encuentra la acción penal?
  - Fase Previa: Audiencias Preliminares. Descripción: Trámites ante el juez de control de garantías para dictar medidas de aseguramiento, imputaciones o legalidad probatoria. Puede fenecer mediante archivo (orden del fiscal) o preclusión (decisión del juez).
  - Fase Resolutiva: Juicio Oral / Preacuerdos. Descripción: Práctica de pruebas con inmediación, o bien, negociación de culpabilidad que requiere la verificación judicial para evitar vicios del consentimiento.
  - Fase Post-Condena: Incidente de Reparación Integral. Descripción: Trámite de naturaleza estrictamente civil extracontractual incrustado en el proceso penal. Requiere demanda en regla, formulación de pretensiones jurídicas directas e indirectas, y no admite variaciones oficiosas por el juez.

**5. Rama Contencioso Administrativa**

- [PUERTA LÓGICA] ¿Se persigue una pretensión patrimonial o resarcimiento contra el Estado?
  - Medios de Control Ordinarios. Descripción: Demandas (ej. reparación directa, nulidad y restablecimiento) que exigen la notificación personal y obligatoria a la entidad demandada, al Ministerio Público y a la Agencia Nacional de Defensa Jurídica del Estado.
- [PUERTA LÓGICA] ¿Se busca el pago de una decisión ya en firme?
  - Trámite de Pago Oficioso. Descripción: Procedimiento de cobro derivado de sentencias, laudos o conciliaciones ejecutoriadas.

**6. Rama Disciplinaria y Sancionatoria**

- [PUERTA LÓGICA] ¿Se imputan faltas o incumplimientos a un contratista estatal?
  - Procedimiento Sancionatorio Contractual (Ley 1474). Descripción: Trámite que garantiza el derecho de uso de la palabra, la motivación de la decisión, y la posibilidad de finalizar por cesación del incumplimiento.

**Fecha:** 26/08/2026

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 105 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---

## Sprint 106 — Widget del campo de fechas anuales fijas, y modelo de datos para el año/fecha de vigencia del acta o título

**Contexto:** el despacho pidió (2026-08-22) un solo formato de fecha (día/mes/año) en todo el sistema, y que
el año en que entró en vigencia el acta/título del caso se capture una sola vez en los datos del expediente
en vez de repetirse en cada obligación. La parte mecánica (`setDisplayFormat("dd/MM/yyyy")` en todos los
`QDateEdit`, y cambiar el placeholder `MM-DD` del campo de fechas anuales fijas a `DD-MM`) no necesita
confirmación, pero dos piezas sí:

**Pregunta:** (a) el campo de fechas anuales fijas (Sprint 73) hoy es texto libre (`QLineEdit` con formato
`MM-DD`) — ¿debe pasar a un widget estructurado (ej. 2 `QSpinBox` día/mes) para eliminar la ambigüedad de
raíz, o basta con cambiar el placeholder/tooltip a `DD-MM` manteniendo el texto libre? (b) ¿qué campo(s)
exactos necesita `Expediente` para "tipo de título y su fecha/año de vigencia" (ej. Sentencia, Acta de
Conciliación, Resolución — con año y fecha exacta), y esto depende del catálogo de tipos de proceso del
Sprint 105 o es independiente?

**Qué necesito exactamente:** confirmación de (a) y la lista de campos exactos para (b).

**Respuesta del despacho:** En lugar de solo texto debería ser un widget estructurado (Día/Mes). Un campo de texto libre es inviable por la gestión de años bisiestos, el cómputo de días hábiles/festivos (Art. 118 CGP) y la necesidad de indexación en base de datos.
Campos exactos para el título: tipo_titulo (Enum: Sentencia, Acta, Laudo, etc.), numero_identificador_titulo, fecha_expedicion_otorgamiento, fecha_exigibilidad, es_primera_copia_ejecutiva (Boolean), fecha_ejecutoria, termino_prescripcion_anos y fecha_limite_prescripcion (calculado).

**Fecha:** 26/08/2026

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 106 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---

## Sprint 107 — ¿Mover el checkbox de indexación IPC/interés sobre capital indexado a después de proyectar la liquidación, o agregar un control posterior de solo presentación?

**Contexto:** el despacho pidió (2026-08-10) que la casilla de indexación IPC (y la de interés sobre capital
indexado, Suma Única) aparezca cuando la liquidación ya esté hecha (indexando por defecto), y solo después,
sobre el resultado ya proyectado, se pueda decidir presentar también una versión sin indexar con fines
pedagógicos ante el juez. Hoy ambos checkboxes viven en `ObligacionFormDialog` (se marcan antes de liquidar,
quedan fijos en la base de datos) y no existe ningún control en la pantalla de resultado para alternarlos
sobre una liquidación ya calculada.

**Pregunta:** ¿la liquidación debe indexar por defecto siempre que la obligación lo permita (sin checkbox
previo en el formulario de captura), moviendo el control por completo a la pantalla de resultado como un
toggle que recalcula in situ (ej. "Ver sin indexación (pedagógico)")? ¿O el checkbox de captura se mantiene
como está hoy, y se agrega un segundo control posterior, puramente de presentación, que no cambia el dato
guardado en la obligación?

**Qué necesito exactamente:** una respuesta entre las dos opciones — determina si `ObligacionFormDialog`
pierde el checkbox actual o lo conserva.

**Respuesta del despacho:** Implementación Híbrida. Mantener el checkbox en el formulario de captura (ObligacionFormDialog) para fijar la intención jurídica sustancial en la base de datos, Y ADEMÁS agregar un Toggle In-Situ de presentación en la pantalla de resultados ("Ver con/sin indexación"). Esto permite recalcular la vista en tiempo real para análisis de sensibilidad o debate pedagógico ante el juez, sin alterar el dato guardado de la obligación.

**Fecha:** 26/08/2026

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 107 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---

## Sprint 104 (seguimiento) — cablear la liquidación tramo por tramo a AreaStrategy, y aclarar su relación con la tasa de interés de Suma Única (Sprint 76/83)

**Contexto:** la primera ronda de esta pregunta (registrada bajo "Sprint 102", ver
`Preguntas-Para-Abogado-Respondidas.md`) confirmó que la reindexación tramo por tramo (patrón X9) es el
criterio correcto, con imputación Art. 1653 C.C., y aportó el algoritmo completo. Ya se implementó como
función aislada y probada (`app/engine/indexation/suma_unica_con_abonos.py`), pero **no se cableó** a
`AreaStrategy`/`LaboralStrategy` todavía por dos razones:

1. **Cambio de arquitectura**: `_eventos_de_obligacion` necesita conocer las fechas de los abonos al generar
   los eventos de causación, algo que hoy no hace (los abonos solo llegan después, al motor de liquidación
   consolidado) — es un cambio real del pipeline, no una corrección mecánica.
2. **Solapamiento con el Sprint 76/83**: el algoritmo del despacho integra el cálculo de intereses junto con
   la indexación (usando una tasa mensual, `tasa_interes_mensual_pura`), pero Suma Única
   (`interes_sobre_capital_indexado`) todavía no está conectada a ningún área real, y la fórmula de interés
   exacta que le corresponde sigue sin confirmar (ver Sprint 76/83).

**Pregunta:** (a) ¿la tasa `tasa_interes_mensual_pura` de este algoritmo es la misma tasa que debe resolver
el Sprint 76/83 para Suma Única, o son conceptos distintos? (b) ¿confirma que el cableado a producción puede
esperar a que esas dos piezas (arquitectura del pipeline, tasa de interés) estén resueltas, o hay urgencia de
un caso real pendiente que dependa de esto ahora mismo?

**Qué necesito exactamente:** confirmación de si la tasa de este algoritmo y la del Sprint 76/83 son la
misma pieza, y si hay urgencia real de cablear esto a producción antes de resolver ambos puntos.

**Respuesta del despacho:** Sí, la tasa_interes_mensual_pura del algoritmo tramo a tramo es exactamente la misma pieza (0.0048676) que debe usarse para la "Liquidación de Perjuicios / Valor" confirmada en el Sprint 76/83. Se puede usar lineal simple para ejecución de títulos civiles, y la tasa pura mensual (0.0048676) para cuantificación de perjuicios y algoritmos de suma única con abonos.

**Fecha:** 23/08/2026 (seguimiento tras respuesta del 22/08/2026)

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 104 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---

## Sprint 89 (seguimiento) — ¿Renta Vitalicia (mesada mensual RAIS) o Retiro Programado/SPM? La Resolución 3023/2017 no parece cubrir lo que pedía el sprint original

**Contexto:** el 2026-08-25 se decidió pedir "la fórmula oficial completa de la Resolución 3023 de 2017"
en vez de la anualidad simplificada de la plantilla `P11.MONTO-MENSUAL-DE-PENSION-REGIMEN-AHORRO-INDIVIDUAL.md`
(`MMP = VP × i × (1+i)^n / ((1+i)^n - 1)`, Renta Vitalicia con tasa técnica del 4% EA y tabla de mortalidad
de rentistas). Al investigar esa resolución (búsqueda web pública; el acceso directo a los sitios oficiales
`funcionpublica.gov.co`, `alcaldiabogota.gov.co` y a `vlex.com.co` está bloqueado por el proxy de red del
entorno donde corre esta rutina — no se pudo leer el texto completo palabra por palabra), varias fuentes
independientes coinciden en que la norma que la acompaña/modifica (Resolución 3099 de 2015 del Ministerio de
Hacienda, sobre RAIS) regula dos cosas que **no son** una mesada mensual de Renta Vitalicia:

1. El **Saldo de Pensión Mínima (SPM)** — una prueba de si el afiliado tiene capital suficiente para acceder
   a la Garantía de Pensión Mínima (Art. 35 Ley 100/1993), con variables propias (factor de gastos 5%, factor
   de seguridad μ=0,6%, Δ=incremento esperado del SMLMV, número de beneficiarios a considerar).
2. Los **parámetros técnicos del Retiro Programado** — una modalidad de pago administrada por el propio fondo
   de pensiones, con recálculo periódico del saldo restante, distinta de la Renta Vitalicia (un producto de
   seguro con tasa técnica fija y tabla de mortalidad, pagado por una aseguradora).

Es decir: parece que la resolución que se pidió replicar responde una pregunta distinta a la que el sprint
original planteaba ("¿cuánto le queda mensualmente a alguien con Renta Vitalicia?"). Construir el código de
SPM/Retiro Programado y llamarlo "monto mensual de pensión RAIS" arriesgaría entregar un cálculo
jurídicamente distinto al que promete el título del sprint.

**Pregunta:** (a) ¿el despacho necesita liquidar RAIS bajo la modalidad **Renta Vitalicia** (la anualidad de
P11, o su versión más precisa), bajo **Retiro Programado** (los parámetros técnicos de la Resolución
3099/2015 y su modificatoria), o ambas? (b) Si es Retiro Programado y/o el SPM/Garantía de Pensión Mínima,
¿puede el despacho aportar el texto completo de la resolución (PDF o copia), dado que el entorno de esta
rutina no tiene acceso directo a los sitios oficiales colombianos para verificarlo por su cuenta?

**Qué necesito exactamente:** confirmación de cuál modalidad de RAIS (Renta Vitalicia / Retiro Programado /
ambas) debe implementar este sprint, y si aplica, el texto de la norma correspondiente.

**Respuesta del despacho:** La Resolución 3023/2017 y 3099/2015 regulan el Saldo de Pensión Mínima (SPM) y parámetros de Retiro Programado, NO la mesada mensual de Renta Vitalicia. Bajo ninguna circunstancia la fórmula del Saldo de Pensión Mínima (SPM) ni los parámetros del Retiro Programado de la Resolución 3099 de 2015 (y su modificatoria la Resolución 3023 de 2017) equivalen o representan el cálculo de una mesada pensional bajo la modalidad de Renta Vitalicia Inmediata.

Denominar el resultado del cálculo de retiro programado o la prueba de suficiencia del saldo de pensión mínima (SPM) como "Monto Mensual de Renta Vitalicia RAIS" sería un vicio de tipicidad pensional y una incorrección actuarial grave. En el ordenamiento jurídico colombiano, la Renta Vitalicia y el Retiro Programado son productos jurídicos y financieros sustancialmente distintos, administrados por entidades diferentes y sujetos a regímenes de riesgo y recálculo contrapuestos. Se pueden implementar mejor estos modulos:

Módulo 1: Renta Vitalicia Inmediata (Anualidad P11 / Cálculo de Aseguradora): Este módulo calcula la mesada fija e irrevocable que otorgaría una compañía de seguros a partir del capital total aportado, utilizando la fórmula actuarial de prima única (factor de capital necesario $\text{FAC1}$ / tablas de mortalidad de la Superintendencia Financiera).

Módulo 2: Retiro Programado y Test de Suficiencia de Saldo (Res. 3099/2015 y Res. 3023/2017): Este módulo liquida la mesada variable para el primer año de Retiro Programado y efectúa la prueba del Saldo de Pensión Mínima (SPM) para verificar si el afiliado califica para la Garantía Estatal de Pensión Mínima del artículo 65 de la Ley 100 de 1993.

**1. Fórmulas de Evaluación del Saldo de Pensión Mínima (SPM)**

El documento establece matemáticamente cómo calcular si el saldo de la cuenta individual es suficiente para cubrir una pensión mínima vitalicia. La fórmula principal para el Saldo de Pensión Mínima ($SPM$) según el mes de cálculo ($s$) es:

$$SPM(s) = \frac{VA[SMM, \Omega(x,y,...), r, f, \Delta, \mu, TM^{\Omega}, s] + AF(SMM, x, r, f, \Delta, TM^x, s)}{(1 - g)}$$

Donde:
- $s$: Mes de cálculo (0 = enero, 1 = febrero, ..., 11 = diciembre).
- $VA$: Valor presente actuarial de la renta vitalicia para el causante y beneficiarios.
- $AF$: Valor presente actuarial del auxilio funerario.
- $g$: Factor de gastos, fijado en 5% ($0.05$).
- $SMM$: Salario Mínimo Mensual vigente.

Despliegue del Valor Presente Actuarial ($VA$) y Auxilio Funerario ($AF$). Para enero ($s=0$):

$VA = SMM \left[ \sum_{k=1}^{w(\Omega)} \sum_{t=1}^{12} \frac{M_t \cdot (1+f)^{k-1}(1+\Delta)^{k-1}}{(1+i)^{k-1+t/12}} {}_{k-1+t/12}p_{\Omega} \right] (1+\mu)$

$AF = 5 \cdot SMM \sum_{k=1}^{w-x} \frac{(1+f)^{k-1}(1+\Delta)^{k-1}}{(1+i)^{k-1/2}} {}_{k-1\vert{}q_x}$

Tasa de descuento compuesta: $1+i = (1+f) \cdot (1+r)$

Para los demás meses ($s = 1, 2, ..., 11$):

$VA = SMM \left[ \sum_{k=1}^{w(\Omega)} \sum_{t=1}^{12} \frac{M_t(1+f)^{k-1}(1+\Delta)^{k-1}}{(1+i)^{k-1+t/12}} {}_{k-1+t/12}p_{\Omega} - \sum_{t=1}^{s} \frac{M_t}{(1+i)^{t/12}} {}_{t/12}p_{\Omega} \right] \frac{(1+i)^{s/12}}{{}_{s/12}p_{\Omega}} (1+\mu)$

$AF = (1 - \frac{s}{12}) \cdot AF[..., 0] + \frac{s}{12} \cdot AF[SMM(1+\Delta), x+1, ..., 0]$

Variables Paramétricas para el Motor de Cálculo:
- $M_t$ (Mesadas): 2 en junio (14 mesadas), 2 en diciembre (13 y 14 mesadas), 1 en los demás meses.
- $r$ (Tasa de interés real): Fijada inicialmente en 3.81% efectivo anual, pero actualizada semestralmente por el Ministerio de Hacienda.
- $f$ (Inflación): Promedio móvil ponderado de la inflación de los últimos 3 años: $f = \frac{3 \cdot f_{A-1} + 2 \cdot f_{A-2} + f_{A-3}}{6}$.
- $\Delta$: Incremento real esperado del salario mínimo.
- $\mu$ (Factor de seguridad): Estimado en 0.6%, revisado semestralmente.
- Mortalidad ($p$ y $q$): Basada en las Tablas de Mortalidad ($TM$) de la Superintendencia Financiera, considerando causante ($x$) y hasta 2 beneficiarios ($y, z$).

**2. Retiro Programado**

Nota Crítica para el Desarrollador: La Resolución 3023 de 2017 no provee una ecuación universal para liquidar la mesada en la modalidad de Retiro Programado.

En su lugar, establece la siguiente regla de negocio algorítmica:
- Si el capital en la cuenta individual es mayor o igual al $SPM$ calculado, la Administradora de Fondos de Pensiones (AFP) debe verificar si alcanza para un Retiro Programado.
- Para hacer este cálculo, la AFP debe emplear su propia fórmula de cálculo según su nota técnica particular, la cual debe estar depositada y no objetada ante la Superintendencia Financiera.

Impacto en Bastium: No se puede programar una única "fórmula de retiro programado de la Ley" basada en este documento, porque el cálculo dependerá de la estructura financiera y las bases técnicas específicas de la AFP correspondiente.

**3. Renta Vitalicia Inmediata (Seguro de Anualidad)**

La resolución define la Renta Vitalicia como una de las modalidades de pensión que el afiliado puede elegir. Su comportamiento dentro del flujo de la resolución es el siguiente:
- El cálculo del SPM se usa como referente consultando los precios de las pólizas de Renta Vitalicia vigentes en el mercado.
- Si el capital del afiliado es insuficiente para acceder a un Retiro Programado (según los cálculos de la AFP), la AFP está obligada a iniciar un proceso de cotización en el mercado asegurador para modalidades como la Renta Vitalicia.
- Si ninguna Compañía Aseguradora de Vida presenta una oferta (es decir, el saldo es muy bajo para comprar la renta vitalicia), la AFP guarda el soporte de las cotizaciones fallidas e inicia el estudio para acceder a la Garantía de Pensión Mínima (si cumple edad y 1.150 semanas).

**Fecha:** 20/09/2026

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 89 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---

## Sprint 110 — ¿Extrapolar la tasa de usura del último tramo certificado, o topar el cálculo de interés al último dato disponible?

**Contexto:** `_TRAMOS_IBC_USURA` (`app/engine/indexation/historical_index.py`) es la tabla de tasas de IBC/
usura certificadas mes a mes por la Superfinanciera; hoy termina el 2026-07-31 porque nadie la actualiza
mes a mes todavía. Cualquier liquidación con una fecha de corte posterior a esa fecha — que incluye "hoy"
en cualquier liquidación normal — necesita una tasa de usura que la tabla no tiene.

Auditoría de código (2026-08-25) confirmó que esto ya no es un caso borde: **cualquier indemnización
moratoria Laboral (Art. 65 CST) cuya fase 2 cruce esa fecha, y cualquier liquidación Tributaria de un
`IMPUESTO_A_CARGO` con mora, corridas con la fecha de hoy, lanzaban una excepción sin capturar**. El caso
Laboral y la actualización IPC del Art. 867-1 Tributario ya quedaron con una alerta no bloqueante en vez de
tumbar la liquidación (`docs/Pendientes.md`, Sprint 110, cierre parcial 2026-08-27) — pero el interés E.T.
635 **base** de Tributario (`TributarioStrategy._construir_rate_provider_obligacion` →
`construir_rate_provider_moratorio_tributario`, `app/engine/tax/moratory_interest.py`) sigue rompiéndose:
ahí no hay un rubro aislado que se pueda omitir, es la construcción del `rate_provider` de toda la
liquidación.

**Pregunta:** cuando la fecha de corte de una liquidación es posterior al último tramo de tasa de usura
certificado, ¿el sistema debe:
(a) **extrapolar** la tasa del último tramo conocido hacia adelante indefinidamente (mismo criterio que ya
se usa para el IPC desde el Sprint 8, vía `get_ipc_interpolado_for_date`/`ultimo_anio_disponible`), o
(b) **limitarse a calcular intereses solo hasta el último dato certificado**, mostrando una advertencia
clara de que el período posterior queda pendiente de liquidar hasta que se actualice la tabla?

**Qué necesito exactamente:** una respuesta sí/no a cuál de las dos opciones (a o b) es la correcta desde
el punto de vista jurídico — la tasa de usura es un techo legal certificado, no un índice que se pueda
inferir como el IPC, así que no es una decisión que el código pueda tomar por su cuenta.

**Respuesta del despacho:** NUNCA extrapolar. Opción (b). El sistema debe calcular intereses moratorios con precisión quirúrgica únicamente hasta el último día calendario con tasa de usura oficialmente certificada por la Superfinanciera. Para el período posterior, el sistema debe dejar el rubro como "Pendiente de Certificación Oficial" y emitir una alerta explícita en la interfaz y el reporte PDF, advirtiendo que el cálculo se suspende hasta la actualización de la tabla, en cumplimiento del principio de legalidad y certeza tributaria (Art. 338 C.P.).

**Fecha:** 26/08/2026

**Movida a Respondidas (2026-11-19):** respuesta del despacho del 16/11/2026 clara y sin conflicto con lo ya construido.

**Estado en el código:** ver `Pendientes.md`, Sprint 110 (fuente de verdad del avance) y su tarjeta en el tablero Kanban.

---
