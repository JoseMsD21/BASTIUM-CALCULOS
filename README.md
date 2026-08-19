# BASTIUM — Ecosistema de Liquidación Forense

[![CI](https://github.com/JoseMsD21/BASTIUM-CALCULOS/actions/workflows/ci.yml/badge.svg)](https://github.com/JoseMsD21/BASTIUM-CALCULOS/actions/workflows/ci.yml)
![Versión](https://img.shields.io/badge/versi%C3%B3n-0.1.0-blue)
[![Licencia](https://img.shields.io/badge/licencia-Apache%202.0-blue)](LICENSE)

> ⚠️ **Aviso legal:** BASTIUM es una herramienta de apoyo para el cálculo de liquidaciones — **no
> sustituye la asesoría de un abogado colegiado ni garantiza exactitud jurídica**. Verifica los
> resultados contra la norma vigente antes de usarlos en un proceso real. Ver
> [SECURITY.md](docs/SECURITY.md#aviso-legal) para el detalle.

BASTIUM es una aplicación de escritorio para abogados y despachos jurídicos en Colombia. Permite
registrar un expediente, cargar las obligaciones (deudas) y los abonos (pagos) asociados, y calcular
automáticamente la liquidación — capital, intereses y saldo final — con el mismo rigor matemático y
legal que se usaría en un juzgado.

**¿Nuevo en el proyecto? Empieza por la [Guía de Usuario](docs/GUIA_USUARIO.md)** — está escrita paso a
paso, sin dar nada por sabido: qué instalar, cómo abrir el programa, cómo usar cada pantalla, y dónde
están los valores legales (como la tasa de interés) por si necesitas consultarlos o ajustarlos.

## Estado actual (2026-08-18)

✅ **Funcional hoy:** captura manual de expedientes y liquidación real de las áreas **Civil / Familia**
(interés del Art. 1617 del Código Civil, 6% anual, sobre obligaciones puntuales y recurrentes, con
abonos, indexación IPC opcional por obligación (Art. corrección monetaria; el abogado marca caso por caso si
aplica, con interpolación entre índices de cierre de año para fechas intermedias), con la opción de aplicar
el algoritmo "Suma Única" (Art. corrección monetaria + interés civil, PDF pág. 21-22: interés sobre el
capital ya indexado en vez de sobre el capital histórico, también válido para intereses de la Ley 80 de
1993 en contratos estatales); las obligaciones recurrentes admiten reajuste anual del capital según SMMLV
o IPC cada 1 de enero, con cuotas mensuales generadas y abonables por separado — o, desde el Sprint 75,
con capital constante (sin reajuste) igual de generables como cuotas reales), **Comercial** (Art. 884
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
bifásica del Art. 65 CST si hubo retardo en el pago y, opcionalmente, cotizaciones de seguridad social
—pensión, salud, ARL, FSP— más incapacidades y suspensiones contractuales, con checkbox de salario =
SMMLV automático por año, descuentos del empleador propios, y edición de obligaciones/eventos ya
guardados sin borrar y recrear) y **Tributario** (impuesto a
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
ya existe en el motor pero aún no tiene campos propios en pantalla — ver [Guía de Usuario](docs/GUIA_USUARIO.md#8-funciones-pendientes-o-en-desarrollo).
El recálculo de liquidaciones históricas anteriores a las correcciones del Sprint 30 ya está construido
(Sprint 47: identificación/marcado, recálculo no destructivo, memoriales, log de diferencias), a la espera
de correrse contra la base de datos real de producción con supervisión manual. Las advertencias legales no
bloqueantes que puede generar una liquidación (ej. "Doble Actualización Prohibida") todavía no llegan a los
PDF/Word exportados, solo a la pantalla — ver Sprint 77 en Pendientes.md. Las
series históricas de SMLMV, IPC, IBC/Tasa de Usura y UVT (1984-2026, 1967-2025, 1997-2026 y 2006-2026
respectivamente) ya están cargadas en `app/engine/indexation/historical_index.py` — IBC/Usura se usa en
Comercial y en la fase 2 de la indemnización moratoria laboral, IPC ya está conectado a la indexación de
Civil/Familia (Sprint 8) y al reajuste anual de cuota alimentaria en Familia (Sprint 41), y UVT ya está
conectada a la conversión SMLMV→UVT del área Sancionatorio (Sprint 14) y al piso legal de 10 UVT de las
sanciones tributarias (Sprint 15); SMLMV ya se usa en el reajuste anual de Familia y en el checkbox
"salario = SMMLV" de Laboral (Sprint 44). El plan completo, sprint por sprint, está en
**[Pendientes.md](docs/Pendientes.md)**.

## Instalación rápida

```
pip install -r requirements.txt
python main.py
```

Para el paso a paso completo (incluyendo un problema conocido de Windows con rutas largas y cómo
resolverlo), ver la [Guía de Usuario](docs/GUIA_USUARIO.md#2-instalación-paso-a-paso).

Una vez instalado, la forma más simple de abrir el programa es haciendo **doble clic en
`Iniciar BASTIUM.bat`** (en la raíz del repo) — no requiere abrir ninguna terminal. El comando
`python main.py` de arriba sigue funcionando igual si prefieres la terminal.

**No hace falta ningún paso manual de migración.** `main.py` corre `aplicar_migraciones_pendientes()`
automáticamente en cada arranque (Sprint 51) — agrega cualquier columna/índice que un `bastium.db` viejo
todavía no tenga y siembra `parametros_legales` si está vacía, comparando el esquema real contra el
modelo actual antes de tocar nada. Es idempotente y no afecta datos existentes: si ya está todo al día no
hace nada; si te falta algo, lo agrega solo. Esto reemplaza los ~9 scripts `scripts/migrate_*.py` que
antes había que recordar correr a mano uno por uno según de qué sprint viniera tu `bastium.db` — ya no
hace falta, aunque los scripts individuales se conservan (`scripts/`) y siguen siendo idempotentes por si
alguna vez hace falta correr uno de forma aislada o auditar qué hace cada uno.

## Actualizar a una versión nueva

Si ya tenías BASTIUM instalado, actualizar es igual de simple — no importa de qué tan atrás venga tu
copia:

```
git pull origin main
pip install -r requirements.txt
python main.py
```

No hay que correr ningún script de migración a mano ni borrar `bastium.db`: el paso 3 lo actualiza solo
(ver la nota de arriba) y tus datos capturados nunca se sobrescriben. Detalle completo, incluyendo qué
hacer si descargaste un ZIP en vez de clonar con Git, en la
[Guía de Usuario](docs/GUIA_USUARIO.md#27-actualizar-a-una-versión-nueva-si-ya-tenías-bastium-instalado).

## Estructura del proyecto

```
app/                    Código fuente (motor de cálculo, GUI, servicios)
  engine/                Motores matemáticos (interés, indexación, tiempo, liquidación)
  services/              Estrategias de liquidación por área del derecho
  views/                 Pantallas de la interfaz (PySide6)
  core/                  Constantes y excepciones compartidas
database/               Modelos y acceso a la base de datos (SQLite)
tests/                  Suite de pruebas automatizadas (pytest)
docs/
  GUIA_USUARIO.md         Guía de uso completa, para cualquier persona
  specifications/         Documentación técnica de cada motor interno
  superpowers/specs/      Documento de diseño del MVP
  superpowers/plans/      Plan de implementación tarea por tarea (histórico)
  Pendientes.md           Backlog de trabajo futuro, organizado en sprints
  REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf
                          Documento maestro de requisitos jurídicos (alcance completo del producto)
```

## Ejecutar las pruebas

```
python -m pytest -q
```

## Verificar estilo de código (lint)

```
python -m ruff check .
```

Configurado en `pyproject.toml` (línea máxima 99, reglas en `[tool.ruff.lint]`). VS Code lo aplica
automáticamente al guardar si abres la carpeta del proyecto (ver `.vscode/settings.json`) y tienes
instalada la extensión `charliermarsh.ruff`. El pipeline de CI corre `ruff check .` antes de la suite de
pruebas y falla si hay alguna violación.

## Mantenimiento de esta documentación

Cada vez que se completa un sprint de `docs/Pendientes.md` y un módulo pasa de "🚧 en desarrollo" a
funcional, este README y la [Guía de Usuario](docs/GUIA_USUARIO.md) deben actualizarse para reflejarlo.
No deben quedar desactualizados respecto al código real.
