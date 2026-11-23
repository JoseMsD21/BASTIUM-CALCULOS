# Funcionalidades de BASTIUM — detalle por área

> Detalle completo de lo que la aplicación hace hoy, área por área. El [README](../README.md) tiene el resumen; la
> [Guía de Usuario](GUIA_USUARIO.md) explica cómo usar cada pantalla; [Pendientes.md](Pendientes.md) tiene la
> historia técnica sprint por sprint. Este texto se movió del README el 2026-11-23 (Sprint 122) sin cambios de
> contenido, para que el README sea corto y fácil de leer.

## Novedades de noviembre de 2026

**Novedades de noviembre de 2026** (detalle en [CHANGELOG](../CHANGELOG.md) y en
[Pendientes.md](Pendientes.md), Sprints 117-120):

- **Interés civil del 6 % con fórmula lineal** (6 % ÷ 365), confirmada por el despacho; el caso real de prueba
  Radicado 2224 reproduce al centavo el valor del Excel del despacho.
- **Las costas procesales nunca generan intereses** y se pagan primero al imputar abonos, en todas las áreas.
- **Tasa de usura sin extrapolar:** si la fecha de corte supera el último mes certificado, el interés se calcula
  hasta ese día y el resto queda "Pendiente de Certificación Oficial", con alerta.
- **Laboral:** auxilio de transporte en trabajo doméstico por días; factores de horas extra de la Ley 2466 y
  vigencia pensional por fecha exacta e invalidez grado 1 en el motor (aún sin pantalla).
- **Expediente:** tipo de proceso según el catálogo del despacho, datos del título ejecutivo con fecha límite de
  prescripción calculada, y fechas en formato día/mes/año en toda la aplicación.
- **Resultados:** interruptor "Ver con/sin indexación" para análisis de sensibilidad, sin alterar lo guardado.
- **Tributario:** imputación proporcional de abonos (Art. 804 E.T.) y suspensión del interés por demanda
  contenciosa.
- **Laboral:** horas extra con los factores de la Ley 2466 en la pantalla; **Civil:** fruto civil (beneficio
  dejado de percibir) y Suma Única con abonos liquidada tramo a tramo, como pidió el despacho.
- **Motores nuevos (aún sin pantalla):** cálculo actuarial (Decreto 1296/2022), retroactivo pensional, contrato
  realidad y fruto civil.
- **Precisión:** redondeo `ROUND_HALF_UP` garantizado en todos los hilos y `Decimal` en vez de `float` en PDF.
- **Instalación:** `Iniciar BASTIUM.bat` crea el entorno e instala las dependencias solo.
- **Equipo:** tablero [Kanban](https://github.com/users/JoseMsD21/projects/1) y
  [plan de integración](PLAN_INTEGRACION_NOVIEMBRE.md). Preguntas pendientes al despacho en
  [Preguntas Abiertas](Preguntas-Para-Abogado-Abiertas.md).

✅ **Funcional hoy:** captura manual de expedientes y liquidación real de las áreas **Civil / Familia**
(interés del Art. 1617 del Código Civil, 6% anual, sobre obligaciones puntuales y recurrentes, con
abonos, indexación IPC opcional por obligación (Art. corrección monetaria; el abogado marca caso por caso si
aplica, con interpolación entre índices de cierre de año para fechas intermedias), con la opción de aplicar
el algoritmo "Suma Única" (Art. corrección monetaria + interés civil, PDF pág. 21-22: interés sobre el
capital ya indexado en vez de sobre el capital histórico, también válido para intereses de la Ley 80 de
1993 en contratos estatales); las obligaciones recurrentes admiten reajuste anual del capital según SMMLV
o IPC cada 1 de enero, con cuotas mensuales generadas y abonables por separado — o, desde el Sprint 75,
con capital constante (sin reajuste) igual de generables como cuotas reales); desde el Sprint 74, una
obligación recurrente de Familia admite capturar el beneficiario de la cuota alimentaria (nombre, fecha de
nacimiento, y tipo — niño, niño con discapacidad, cónyuge, padres u otro, con los campos siguientes
cambiando según esa respuesta como un árbol de decisión), y el software calcula automáticamente si la
obligación sigue vigente: un niño sin discapacidad hasta los 18 años, o hasta los 25 si estudia una carrera
profesional/técnica/tecnológica (deja de causar cuotas nuevas solo con superar la edad, sin necesitar fijar
una fecha de fin a mano); un niño con discapacidad marcada como permanente, de forma vitalicia. Para
cónyuge, padres, otro beneficiario, o un niño con discapacidad sin marcar como permanente, el software
declara explícitamente que la vigencia "no es determinable automáticamente — requiere evaluación caso a
caso" y nunca aplica el límite de edad de un niño ni inventa una fecha de fin — el criterio operacional
exacto de esos casos (ej. cómo se prueba que un cónyuge superó su condición de vulnerabilidad) sigue
pendiente de confirmación del despacho, **Comercial** (Art. 884
C.Co., tasas remuneratoria y moratoria pactadas por obligación con
split real antes/después del vencimiento, sanción del doble por exceso sobre el tope de usura 1.5×IBC
(Ley 45/1990 art. 72, sin rechazar ni truncar la liquidación), obligaciones en USD
convertidas a pesos con la TRM certificada por la Superintendencia Financiera en vivo, consultada por la
fecha real de cada evento — capital en la fecha de origen, cada abono en su propia fecha de pago, sin TRM
congelada (Art. 874 C.Co.); admite una TRM manual como anulación opcional, anatocismo condicionado
(Art. 886 C.Co.: interés sobre interés, activado solo con demanda judicial o acuerdo posterior con al
menos un año de intereses vencidos, capitalizado periódicamente — nunca por defecto), y, desde el Sprint
75, obligaciones recurrentes con cuotas mensuales reales igual que Civil/Familia). Civil/Familia y
Comercial comparten, desde el Sprint 75, un botón "Pagar cuotas seleccionadas" para pagar un rango de
cuotas consecutivas con un solo abono, repartido en cascada (capital de la cuota más reciente primero,
luego capital+interés de las anteriores). **Sancionatorio**
(multas SIC/Penal/Ambiental/Urbano en SMLMV o UVT, Ley 1955/2019 art. 49, con la base convertida a pesos
según la fecha del hecho: SMLMV antes del 2020-01-01 y UVT desde esa fecha (tabla histórica de UVT
2006-2026 ya cargada)), **Honorarios / Litigio** (cobro de honorarios
profesionales y cuota litis, validando el tope único del 50% acumulado del beneficio obtenido para la
suma de honorarios fijos + cuota litis (alerta "Honorarios Desproporcionados - Art. 35 Num. 4 Ley
1123/2007" si se excede); las costas judiciales se ingresan como porcentaje manual, el que fijó el juez —
ver nota de "en desarrollo" más abajo),
**Laboral** (liquidación final —finiquito— de un contrato:
cesantías, intereses a cesantías, prima de junio y diciembre, vacaciones, indemnización moratoria
bifásica del Art. 65 CST si hubo retardo en el pago, indemnización por despido injustificado del Art. 64
CST —30 días de salario el primer año + 20 días por cada año subsiguiente para contratos posteriores a la
Ley 50/1990, o 45 + 15 días para contratos anteriores, con piso de 15 días para término fijo/obra-labor;
coexiste con la moratoria sin excluirla, y el umbral de salario ≥10 SMMLV queda pendiente de confirmación
del despacho, ver Sprint 92 en `docs/Pendientes.md`— y, opcionalmente, cotizaciones de seguridad social
—pensión, salud, ARL, FSP— más incapacidades y suspensiones contractuales, con checkbox de salario =
SMMLV automático por año, descuentos del empleador propios, y edición de obligaciones/eventos ya
guardados sin borrar y recrear; además, desde el Sprint 93, una segunda categoría —"Salarios y
prestaciones dejadas de percibir"— reconstruye salario + prestaciones para un período SIN contrato
vigente (reintegro, salarios caídos), año calendario por año calendario, con el salario reajustado
anualmente por IPC o SMMLV, reutilizando el mismo motor de reajuste anual de Civil/Familia) y
**Tributario** (impuesto a
cargo; sanciones por extemporaneidad, inexactitud y error aritmético, todas con un piso legal de 10 UVT
sin importar el cálculo porcentual; imputación de pagos propia del área —sanciones → intereses →
impuesto, distinta del orden civil de intereses → capital—; interés automático del E.T. art. 635 —usura
vigente menos dos puntos—, que nunca se pacta manualmente; y depuración de Renta Líquida Gravable
informativa, que se muestra aparte y no se suma al saldo de la deuda). Sancionatorio muestra en pantalla,
de forma transparente, si la multa se aplicará como SMLMV o UVT según la fecha del hecho. Cualquier
obligación cuyo plazo de prescripción/caducidad ya venció se marca (sin excluirla del cálculo) con
advertencia visual en pantalla, PDF y Word — desde el Sprint 61, la alerta de vencimiento del Dashboard
cubre 13 tipos de acción/proceso (antes solo la prescripción ejecutiva), elegibles por obligación desde un
campo opcional en el formulario de captura. El resultado de cualquier
liquidación se puede
exportar a **PDF** y a **Word** desde la pantalla de Resultado de Liquidación, incluido el saldo a favor
del deudor cuando un pago superó la deuda. Cada liquidación ejecutada
queda registrada en un historial de auditoría por expediente (quién, cuándo, con qué área y fecha de
corte), con reconstrucción exacta de un cálculo pasado con solo hacer doble clic sobre su fila.

La interfaz tiene navegación por panel lateral fijo, modo oscuro/claro alternable desde "⚙ Configuraciones
→ Apariencia" (persistido entre sesiones), notificaciones no bloqueantes tipo toast para confirmaciones de
bajo riesgo,
y una gráfica de expedientes por área en el Dashboard de inicio. Los 7 diálogos de formulario del
proyecto (agregar/editar Obligación, Expediente, Abono, Parámetro, Evento contractual, Descuento laboral,
y el historial de un Parámetro) se pueden minimizar, maximizar y redimensionar arrastrando sus bordes —
las ventanas de confirmación (ej. "¿Eliminar esta obligación?") no tienen esa capacidad, son mensajes
simples. Los 4 formularios principales de captura (Obligación, Expediente, Abono, Parámetro) tienen
tooltips ⓘ de ayuda en los campos que no se explican solos, con un ejemplo concreto. Desde el Detalle de
un expediente también se pueden editar y eliminar Obligaciones y Abonos ya guardados (con confirmación
antes de borrar, y borrado en cascada de las cuotas mensuales generadas por reajuste anual si aplica),
además de los Eventos contractuales laborales que ya lo permitían.

ℹ️ **Nota sobre auditorías históricas:** las liquidaciones auditadas antes de que el campo
`rate_source` se agregara al motor (posterior al Sprint 9) se reconstruyen con `rate_source="N/A"`
en vez de fallar — `AuditLog.resultado_json` es append-only por diseño, esas filas nunca se
reescriben, así que no existe (ni se planea) un script de backfill que edite el JSON histórico sin
romper esa garantía de append-only (Sprint 23).

✅ **Parámetros legales versionados:** desde "⚙ Configuraciones → Parámetros" cualquier abogado puede consultar
y agregar, sin tocar código, los valores/tasas/topes que antes solo un desarrollador podía cambiar: el
multiplicador de usura, los topes de cuota litis, los plazos de prescripción/caducidad, el descuento del
interés moratorio tributario (E.T. art. 635), la tasa civil legal, y las series históricas de SMLMV, IPC,
IBC/Tasa de Usura y UVT. Cada valor queda con su fecha de vigencia, quién lo agregó y por qué — los valores
que trae la app de fábrica nunca se editan ni se borran, solo se agregan valores nuevos, así que el
historial completo de cada parámetro queda siempre disponible con doble clic; los valores que un usuario
agrega sí puede editarlos o eliminarlos él mismo después, desde ese mismo historial. La tabla de Parámetros
muestra también, por fila, el Área del derecho (una o varias) y la Unidad de medida del valor (ej. "%",
"COP", "meses"), asignadas al agregar el valor — fijas para los valores de fábrica, editables después para
los que agrega un usuario (ver el párrafo siguiente). Para SMLMV, IPC y
UVT — que el gobierno fija año a año — la columna "Vigente hasta" calcula automáticamente el 31 de
diciembre del año correspondiente en vez de mostrarse vacía; el resto de parámetros sin fecha de cierre
real muestra "Indefinido". El índice IPC acumulado, el único parámetro calculado con fórmula, muestra en su
historial la variación % anual cruda junto al índice ya calculado, con la fórmula explicada.

✅ **Editar/eliminar de parámetros propios y desplegable de Unidad:** desde el historial de una clave en
Configuraciones → Parámetros, cada valor que un usuario haya cargado tiene sus propios botones
"Editar"/"Eliminar" (los del sistema quedan protegidos, sin esos botones); el campo "Unidad" del formulario
de agregar valor es ahora un desplegable con las unidades ya usadas y una opción "Otros..." para escribir
cualquier otra; y los formularios/columnas de Parámetros tienen tooltips ⓘ homologados en todos los campos.

✅ **Restablecer datos de fábrica:** desde "⚙ Configuraciones → Restablecer" cualquier abogado puede borrar,
con un solo botón, todos los expedientes (y sus obligaciones/abonos/eventos/descuentos en cascada) y los
parámetros legales que él mismo haya cargado — los parámetros de sistema quedan intactos y el tema visual
vuelve a claro. Antes de borrar se crea automáticamente un backup de la base de datos en `backups/`, y hay
que escribir "RESTABLECER" para habilitar la confirmación; no hay papelera ni deshacer más allá de
restaurar ese backup a mano.

🚧 **En desarrollo:** varios módulos más también están pendientes. La indexación IPC ya está disponible en
las 6 áreas (Sprint 43), cada una con su propia regla de exclusión/coexistencia confirmada por el
despacho — Comercial exige pacto expreso y es excluyente con la tasa comercial, Tributario la aplica
automáticamente vía Art. 867-1 E.T. sin casilla manual, Laboral y Sancionatorio son condicionales. Las
costas judiciales se ingresan como porcentaje manual (el que fijó el juez); el cálculo automático por tabla
ya existe en el motor pero aún no tiene campos propios en pantalla — ver [Guía de Usuario](GUIA_USUARIO.md#8-funciones-pendientes-o-en-desarrollo).
El recálculo de liquidaciones históricas anteriores a las correcciones del Sprint 30 ya está construido
(Sprint 47: identificación/marcado, recálculo no destructivo, memoriales, log de diferencias), a la espera
de correrse contra la base de datos real de producción con supervisión manual. Las
series históricas de SMLMV, IPC, IBC/Tasa de Usura y UVT (1984-2026, 1967-2025 en variación anual **más
una serie mensual real 2003-2026 del DANE ya conectada a la indexación mensual desde el Sprint 80**,
1971-2026 desde el Sprint 81 y 2006-2026 respectivamente) ya están cargadas en
`app/engine/indexation/historical_index.py` (más `app/engine/indexation/historical_dtf.py` para la serie
semanal de DTF del Banco de la República 1984-2026, Sprint 82, cargada y consultable pero todavía sin
calculador conectado — ver Sprint 82 en `Pendientes.md`) — IBC/Usura se usa en Comercial y en la fase 2 de
la indemnización moratoria laboral, IPC ya está conectado a la indexación mensual real de Civil/Familia
para fechas 2003-01 en adelante — real hasta el último mes certificado por el DANE, estimado con media
geométrica de los últimos 12 meses para fechas posteriores (Sprint 8, respuesta del despacho del
22/08/2026), interpolación anual como respaldo solo antes de 2003-01 — y al reajuste anual
de cuota alimentaria en Familia (Sprint 41), y UVT ya está
conectada a la conversión SMLMV→UVT del área Sancionatorio (Sprint 14) y al piso legal de 10 UVT de las
sanciones tributarias (Sprint 15); SMLMV ya se usa en el reajuste anual de Familia y en el checkbox
"salario = SMMLV" de Laboral (Sprint 44). El plan completo, sprint por sprint, está en
**[Pendientes.md](Pendientes.md)**.
