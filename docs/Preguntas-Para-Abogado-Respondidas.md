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
