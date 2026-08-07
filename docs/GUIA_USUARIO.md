# Guía de Usuario de BASTIUM

> Esta guía está escrita para que cualquier persona pueda instalar y usar BASTIUM sin conocimientos
> técnicos previos. Si en algún punto algo no funciona como se describe aquí, revisa la sección
> [9. Preguntas frecuentes y solución de problemas](#9-preguntas-frecuentes-y-solución-de-problemas)
> antes que nada.
>
> **Última actualización:** 2026-08-06 — refleja el estado de Civil/Familia, Comercial, Sancionatorio,
> Honorarios/Litigio, Laboral, Tributario, exportación de liquidaciones a PDF/Word, los botones de
> navegación (Volver/Inicio/Parámetros) con íconos y estado activo, el breadcrumb de contexto y los
> atajos de teclado de navegación y de los formularios, la edición/eliminación de expediente, la
> pantalla de parámetros legales versionados, y el Dashboard de inicio con resumen de expedientes y
> alertas de vencimiento. Cada vez que se complete un sprint nuevo de
> [`Pendientes.md`](../Pendientes.md), esta guía se actualiza para que nunca quede desactualizada
> respecto al programa real.

## Índice

1. [¿Qué es BASTIUM?](#1-qué-es-bastium)
2. [Instalación paso a paso](#2-instalación-paso-a-paso)
3. [Cómo iniciar el programa](#3-cómo-iniciar-el-programa)
4. [Tour de la aplicación](#4-tour-de-la-aplicación)
5. [Cómo usar cada función, paso a paso](#5-cómo-usar-cada-función-paso-a-paso)
6. [Áreas del derecho: cuáles funcionan hoy](#6-áreas-del-derecho-cuáles-funcionan-hoy)
7. [Valores legales y parámetros: dónde están y cómo consultarlos o cambiarlos](#7-valores-legales-y-parámetros-dónde-están-y-cómo-consultarlos-o-cambiarlos)
8. [Funciones pendientes o en desarrollo](#8-funciones-pendientes-o-en-desarrollo)
9. [Preguntas frecuentes y solución de problemas](#9-preguntas-frecuentes-y-solución-de-problemas)
10. [Para quien programa: comandos útiles](#10-para-quien-programa-comandos-útiles)

---

## 1. ¿Qué es BASTIUM?

BASTIUM es un programa de computador (una aplicación de escritorio, como Word o Excel, pero hecha a la
medida) que ayuda a un abogado a calcular cuánto dinero debe una persona en un proceso legal, incluyendo
los intereses que se acumulan con el tiempo.

En vez de calcular esto a mano con calculadora (algo lento y donde es fácil equivocarse), BASTIUM lo hace
de forma automática, siguiendo exactamente las reglas que dicta la ley colombiana.

Hoy en día, BASTIUM sabe calcular liquidaciones de las áreas **Civil y de Familia** (por ejemplo: cuotas
de alimentos, gastos médicos, deudas civiles con interés), **Comercial** (pagarés, letras de cambio,
cheques y facturas, con tasa remuneratoria y moratoria), **Sancionatorio** (multas administrativas
expresadas en SMLMV o UVT), **Honorarios / Litigio** (cobro de honorarios profesionales y cuota litis,
con costas judiciales opcionales) y **Laboral** (liquidación final de un contrato de trabajo: cesantías,
intereses a cesantías, prima, vacaciones e indemnización moratoria) — más detalle en la
[sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy).

---

## 2. Instalación paso a paso

### 2.1. Qué necesitas tener instalado antes de empezar

- **Windows** (el programa se desarrolló y probó en Windows).
- **Python 3.14** (o una versión cercana). Si no sabes si lo tienes instalado, abre una terminal
  (`PowerShell`) y escribe:
  ```
  python --version
  ```
  Si te muestra algo como `Python 3.14.6`, ya lo tienes. Si te da un error, necesitas instalar Python
  primero desde [python.org](https://www.python.org/downloads/) (marca la casilla "Add Python to PATH"
  durante la instalación).

### 2.2. Ubicar la carpeta del proyecto

Todo el programa vive en una sola carpeta, llamada `BASTIUM CALCULOS`. Abre una terminal dentro de esa
carpeta (en el explorador de archivos de Windows, haz clic derecho dentro de la carpeta y elige "Abrir en
Terminal" o "Abrir ventana de PowerShell aquí").

### 2.3. Crear el entorno virtual (una sola vez)

Un "entorno virtual" es una carpeta especial (`.venv`) donde se instalan todos los programas auxiliares
que BASTIUM necesita, sin mezclarlos con el resto de tu computador. Si la carpeta `.venv` ya existe
dentro del proyecto, sáltate este paso.

```
python -m venv .venv
```

### 2.4. Instalar lo que BASTIUM necesita para funcionar

Con la terminal abierta en la carpeta del proyecto, escribe:

```
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Esto puede tardar unos minutos la primera vez — está descargando e instalando todas las piezas que
BASTIUM usa por dentro (el motor de la interfaz gráfica, la base de datos, etc.). El archivo
`requirements.txt` es la lista exacta de esas piezas; **no lo borres**, es necesario para poder instalar
o reinstalar el programa en cualquier momento.

### 2.5. Problema conocido: "rutas largas" en Windows

Si al instalar te aparece un error mencionando `Long Path` o `WinError`, es porque Windows por defecto no
permite rutas de archivo muy largas, y este proyecto vive dentro de una carpeta de OneDrive con una ruta
profunda. La solución (ya aplicada en esta máquina el 2026-07-15) es habilitar el soporte de rutas largas
de Windows:

1. Abre PowerShell **como Administrador**.
2. Ejecuta:
   ```
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWord -Force
   ```
3. Vuelve a intentar el paso 2.4.

Si instalas BASTIUM en otro computador y te aparece este mismo error, repite estos 3 pasos ahí.

### 2.6. Verificar que todo quedó instalado correctamente (opcional, recomendado)

```
.venv\Scripts\python.exe -m pytest -q
```

Este comando corre todas las pruebas automáticas del programa. Si al final ves algo como
`687 passed, 1 skipped` (un número seguido de "passed", sin ningún "failed"), significa que todo está
instalado y funcionando correctamente. El número exacto sube con cada sprint nuevo, así que no te
preocupes si no coincide exactamente — lo que importa es que no aparezca ningún "failed". Si ves errores,
revisa la [sección 9](#9-preguntas-frecuentes-y-solución-de-problemas).

### 2.7. Actualizar a una versión nueva (si ya tenías BASTIUM instalado)

Si ya tenías el programa instalado en tu computador y quieres pasar a una versión más nueva —o si
alguien te comparte una copia y no sabes de qué tan atrás viene—, **no hace falta repetir la
instalación completa ni borrar nada**. Con la terminal abierta en la carpeta del proyecto:

```
git pull origin main
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

- `git pull origin main` trae el código más reciente. Si no clonaste el proyecto con Git sino que
  descargaste el ZIP desde GitHub, la alternativa es descargar el ZIP nuevo y reemplazar todos los
  archivos **excepto** tu `bastium.db` — ese archivo es tu base de datos con todos tus expedientes,
  no lo sobrescribas.
- El segundo comando instala cualquier pieza nueva que se haya agregado en sprints recientes (no
  afecta lo que ya tienes instalado).
- Al abrir el programa con el tercer comando, **no necesitas correr ningún script de migración a
  mano**: `main.py` revisa automáticamente tu `bastium.db` contra la estructura más reciente y le
  agrega lo que le falte (columnas, índices, valores legales), sin importar de qué sprint venga tu
  base ni si ya está al día — en ese caso simplemente no hace nada. Tus datos capturados
  (expedientes, obligaciones, abonos) nunca se borran ni se sobrescriben en este proceso.

Solo necesitas la instalación completa de la [sección 2.1 a 2.6](#2-instalación-paso-a-paso) si es
la primera vez que instalas BASTIUM en ese computador.

---

## 3. Cómo iniciar el programa

Con la terminal abierta en la carpeta del proyecto, escribe:

```
.venv\Scripts\python.exe main.py
```

Se abrirá una ventana titulada **"BASTIUM - Ecosistema de Liquidacion Forense"**. Esa es la aplicación.
Para cerrarla, simplemente cierra la ventana como cualquier programa de Windows.

La primera vez que la abras, el programa crea automáticamente un archivo llamado `bastium.db` dentro de
la carpeta del proyecto — ahí es donde se guardan **todos** los expedientes, obligaciones y abonos que
captures. Ese archivo queda en tu computador; si lo borras, pierdes todos los datos capturados (no se
sube a internet ni se comparte con nadie).

---

## 4. Tour de la aplicación

BASTIUM tiene **5 pantallas**. Te mueves entre la mayoría automáticamente según lo que hagas (no hay un
menú de navegación separado); a la de Parámetros se entra con un botón de la barra superior:

1. **Dashboard (Inicio)** — la pantalla con la que arranca el programa (Sprint 33). Muestra el total de
   expedientes y su conteo por área, una tabla de **"Plazos próximos a vencer"** (obligaciones no pagadas
   cuya prescripción vence dentro de los próximos 90 días, o ya vencida — doble clic sobre una fila abre
   ese expediente), y una tabla de **"Actividad reciente"** con las últimas liquidaciones ejecutadas en
   cualquier expediente. El botón **"Ver todos los expedientes"** lleva a la Lista de Expedientes.

2. **Lista de Expedientes** — se abre desde el botón "Ver todos los expedientes" del Dashboard. Muestra
   una tabla con todos los expedientes que ya creaste (radicado, demandante, demandado, área, y botones de
   **Editar** y **Eliminar** por fila) y un botón **"Nuevo expediente"**. Si haces doble clic sobre una
   fila, entras al detalle de ese expediente.

3. **Detalle de Expediente** — se abre al hacer doble clic en un expediente de la lista o de la tabla de
   alertas del Dashboard. Aquí ves dos tablas lado a lado: **Obligaciones** (las deudas del expediente) y
   **Abonos** (los pagos hechos), cada una con su botón de "Agregar". Abajo hay un botón grande
   **"Liquidar"**.

4. **Resultado de Liquidación** — se abre automáticamente después de presionar "Liquidar". Muestra una
   tabla con el detalle día por día de cómo se acumuló el interés, y al final tres totales: interés
   acumulado, pagos aplicados y saldo final.

5. **⚙ Parámetros** — la pantalla de parámetros legales versionados (tasas, topes, plazos e indicadores
   históricos). Se abre desde el botón **"⚙ Parámetros"** de la barra superior, disponible siempre, sin
   importar en qué otra pantalla estés. Ver [sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros)
   para el detalle completo.

En la parte superior de la ventana hay una barra de navegación con tres botones y, a su derecha, un
texto de "breadcrumb" que muestra en qué expediente y pantalla estás parado en cada momento (por
ejemplo, "Expedientes › Radicado 2026-00123 › Liquidación"):

- **Volver** — regresa a la pantalla anterior (por ejemplo, de Resultado de Liquidación a Detalle de
  Expediente, y de ahí al Dashboard o a la Lista de Expedientes, según por dónde hayas entrado). Recuerda
  el orden exacto en que navegaste, no solo "la pantalla anterior en general". Está oculto cuando no hay a
  dónde volver (por ejemplo, recién abierto el programa). Atajo de teclado: **Alt+Izquierda** o
  **Retroceso (Backspace)**.
- **Inicio** — regresa directo al Dashboard sin importar en qué pantalla estés, y refresca sus datos.
  Está oculto cuando ya estás en el Dashboard. Atajo de teclado: **Ctrl+Inicio**.
- **Parámetros** — siempre visible, en cualquier pantalla; te lleva a la pantalla de parámetros legales
  versionados (ver punto 5 arriba). Se resalta con el color de marca de BASTIUM mientras estás dentro de
  esa pantalla, para que sea evidente cuál tienes abierta.

En los formularios (Nuevo expediente, Agregar obligación, Agregar abono, Agregar evento contractual,
Agregar valor de parámetro): **Ctrl+S** guarda y cierra el formulario (equivale a hacer clic en
"Guardar"), y **Esc** lo cierra sin guardar nada.

---

## 5. Cómo usar cada función, paso a paso

### 5.1. Crear un expediente nuevo

1. Abre el programa (ver [sección 3](#3-cómo-iniciar-el-programa)).
2. En la pantalla de Lista de Expedientes, haz clic en el botón **"Nuevo expediente"**.
3. Se abre una ventana con un formulario. Llena estos campos:
   - **Radicado**: el número o referencia interna del caso (ej. `2026-00123`). Es obligatorio.
   - **Demandante**: nombre de quien reclama.
   - **Demandado**: nombre de quien debe.
   - **Área del derecho**: elige **"Civil / Familia"**, **"Comercial"**, **"Sancionatorio"**,
     **"Honorarios / Litigio"**, **"Laboral"** o **"Tributario"** (las seis opciones calculan de verdad
     hoy, ver [sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy)). Si eliges Comercial, Sancionatorio,
     Honorarios, Laboral o Tributario, el formulario de "Agregar obligación" muestra campos adicionales —
     ver [sección 5.7](#57-agregar-una-obligación-comercial),
     [5.9](#59-agregar-una-obligación-sancionatoria),
     [5.10](#510-agregar-una-obligación-de-honorarios--litigio),
     [5.11](#511-agregar-una-obligación-laboral-y-liquidar-un-contrato-terminado) o
     [5.15](#515-agregar-una-obligación-tributaria) según el área.
   - **Juzgado**: opcional, el juzgado donde está el proceso, si aplica.
   - **Fecha de corte**: la fecha hasta la cual se va a calcular el interés (normalmente, hoy o la fecha
     en que se necesita presentar la liquidación).
4. Haz clic en **"Guardar"**.
5. El expediente aparece ahora en la tabla de la Lista de Expedientes.

Si dejas el Radicado vacío, el programa te avisa "Datos incompletos" y no te deja guardar hasta que lo
llenes.

### 5.2. Abrir un expediente existente

En la Lista de Expedientes, haz **doble clic** sobre la fila del expediente que quieres abrir. Se abre la
pantalla de Detalle de ese expediente.

### 5.3. Agregar una obligación puntual (una deuda de una sola vez)

Usa este tipo cuando la deuda es un monto único con una sola fecha (ej. "gastos médicos de una vez").

1. Dentro del Detalle de un expediente, haz clic en **"Agregar obligación"** (en el recuadro de la
   izquierda, "Obligaciones").
2. En **Tipo**, deja seleccionado **"Puntual"**.
3. Llena:
   - **Categoría**: elige de la lista (ej. "Dano emergente", "Cuota alimentaria", "Danos morales", etc. —
     ver la lista completa en la [sección 7](#7-valores-legales-y-parámetros-dónde-están-y-cómo-consultarlos-o-cambiarlos)).
   - **Concepto**: una descripción corta (ej. "Gastos médicos de urgencia").
   - **Valor**: el monto de la deuda en pesos, con decimales si aplica (ej. `427900.00`).
   - **Tasa efectiva anual (%)**: la tasa de interés anual, en porcentaje. Por defecto ya viene puesto
     `6.00` (el 6% anual que ordena el Artículo 1617 del Código Civil), pero puedes cambiarlo si el caso
     tiene una tasa distinta pactada.
   - **Fecha de origen**: la fecha en que nació esa deuda (ej. la fecha de la factura o el hecho).
   - **Aplica indexación IPC**: marca esta casilla si la obligación debe corregirse monetariamente por
     inflación (indexación, Art. corrección monetaria) además del interés. Es una decisión del abogado
     caso por caso — no todas las obligaciones se indexan. Ver
     [sección 7.7](#77-indexación-ipc-corrección-monetaria) para el detalle de cómo se calcula.
   - **Interés sobre capital ya indexado**: marca esta casilla, además de "Aplica indexación IPC", si
     quieres el algoritmo "Suma Única" del PDF (pág. 21-22): primero se indexa el capital por IPC, y el
     interés del 6% se calcula sobre ese valor ya indexado, no sobre el capital histórico. Sin esta
     casilla, el interés se sigue calculando solo sobre el capital histórico (comportamiento anterior a
     este sprint). Ver [sección 7.7](#77-indexación-ipc-corrección-monetaria) para el detalle.
4. Haz clic en **"Guardar"**.

Si pones un valor negativo o cero, el programa te avisa "Datos inválidos" y no deja guardar.

### 5.4. Agregar una obligación recurrente (una cuota que se repite cada mes)

Usa este tipo para deudas que se pagan mes a mes (ej. cuota de alimentos mensual).

1. Igual que arriba, haz clic en **"Agregar obligación"**.
2. En **Tipo**, elige **"Recurrente"** — el formulario cambia y te pide otros campos:
   - **Categoría**, **Concepto**, **Valor** (el monto de CADA cuota mensual) y **Tasa efectiva anual (%)**
     — igual que en Puntual.
   - **Fecha de inicio (Recurrente)**: desde qué mes empieza a causarse la cuota.
   - **Día de pago (Recurrente)**: el día del mes en que vence cada cuota (ej. `5` = el día 5 de cada
     mes).
   - **Aplica indexación IPC**: igual que en obligaciones Puntuales (ver
     [sección 5.3](#53-agregar-una-obligación-puntual-una-deuda-de-una-sola-vez)), puedes marcar esta
     casilla para que la obligación se indexe por IPC. En Recurrente, cada cuota se indexa
     individualmente desde su propia fecha de vencimiento, no todas desde el inicio de la obligación —
     ver [sección 7.7](#77-indexación-ipc-corrección-monetaria) para el detalle.
   - **Interés sobre capital ya indexado**: marca esta casilla, además de "Aplica indexación IPC", si
     quieres el algoritmo "Suma Única" del PDF (pág. 21-22): primero se indexa el capital por IPC, y el
     interés del 6% se calcula sobre ese valor ya indexado, no sobre el capital histórico. Sin esta
     casilla, el interés se sigue calculando solo sobre el capital histórico (comportamiento anterior a
     este sprint). Ver [sección 7.7](#77-indexación-ipc-corrección-monetaria) para el detalle.
3. Haz clic en **"Guardar"**.

El programa genera automáticamente una cuota por cada mes, desde la fecha de inicio hasta la fecha de
corte del expediente.

### 5.5. Agregar un abono (registrar un pago)

1. Dentro del Detalle de un expediente, **selecciona primero la fila de la obligación** a la que se le
   va a abonar (haz clic sobre ella en la tabla de Obligaciones).
2. Haz clic en **"Agregar abono"** (en el recuadro de la derecha, "Abonos"). Si no seleccionaste una
   obligación primero, el programa te avisa "Selección requerida".
3. Llena:
   - **Fecha**: el día en que se hizo el pago.
   - **Monto**: cuánto se pagó.
   - **Referencia**: opcional, ej. número de consignación o comprobante.
4. Haz clic en **"Guardar"**.

Si el monto es cero o negativo, el programa avisa "Datos inválidos".

### 5.6. Liquidar el expediente y leer el resultado

1. Con al menos una obligación cargada, haz clic en el botón grande **"Liquidar"** al final de la
   pantalla de Detalle.
2. El programa calcula automáticamente y te lleva a la pantalla de Resultado de Liquidación, con:
   - Una **tabla** con una fila por cada evento (cada obligación causada, cada abono aplicado), mostrando
     fecha, concepto, capital base, tasa, interés, pago y saldo en ese punto del tiempo.
   - **Interés acumulado**: la suma total de intereses generados.
   - **Pagos aplicados**: la suma total de abonos que se descontaron.
   - **Saldo final**: lo que queda por pagar hoy (capital + interés pendiente, después de restar los
     abonos).

Si el expediente no tiene ninguna obligación cargada, el botón "Liquidar" te muestra el mensaje
"No se pudo liquidar" en vez de calcular.

### 5.7. Agregar una obligación comercial

Cuando el expediente tiene **Área del derecho = Comercial**, el formulario de "Agregar obligación"
muestra varios campos adicionales, específicos de esta área — y dos más si la obligación está pactada en
dólares:

1. Dentro del Detalle de un expediente Comercial, haz clic en **"Agregar obligación"**.
2. Llena los campos comunes (Tipo, Categoría, Concepto, Valor, Tasa efectiva anual, Fecha de origen)
   igual que en Civil/Familia — ver [sección 5.3](#53-agregar-una-obligación-puntual-una-deuda-de-una-sola-vez).
   La "Tasa efectiva anual (%)" aquí representa la **tasa remuneratoria** pactada.
3. Llena además:
   - **Tasa moratoria anual (%)**: la tasa que aplica después de que la obligación vence y no se paga.
     Si no se pactó una distinta, la ley comercial (Art. 884 C.Co.) sugiere 1.5× el IBC vigente, pero el
     campo siempre se diligencia manualmente — no hay cálculo automático todavía (ver `Pendientes.md`,
     Sprint 5).
   - **Fecha de vencimiento**: la fecha en que la obligación se hace exigible. Para obligaciones
     **Puntuales**, antes de esta fecha se usa la tasa remuneratoria y después la moratoria. Para
     obligaciones **Recurrentes**, este split todavía no aplica por cuota — se usa la tasa moratoria
     durante todo el período (alcance reducido de este sprint, ver `Pendientes.md`, Sprint 2). El campo
     igual es obligatorio para ambos tipos.
   - **IBC vigente aplicable (%)**: el Interés Bancario Corriente certificado por la Superintendencia
     Financiera para la fecha del caso. Se usa únicamente para validar que ninguna de las dos tasas
     pactadas supere el tope legal de usura (1.5× este valor).
   - **Moneda**: "COP" por defecto. Si la obligación está pactada en dólares, elige "USD" — aparecen dos
     campos adicionales (ver punto 4).
4. Si elegiste **Moneda = USD**, los campos **"TRM aplicable"** y **"Fecha de referencia de la TRM"**
   son **opcionales** desde el Sprint 12 (corregido 2026-08-01): si los dejas vacíos, el programa consulta
   automáticamente la TRM certificada por la Superintendencia Financiera para la fecha real de cada
   evento (el capital, en la fecha de origen; cada abono, en su propia fecha de pago) — ver
   [sección 7.8](#78-trm-y-obligaciones-en-moneda-extranjera). Solo diligencia **"TRM aplicable"** si
   quieres forzar un valor fijo (por ejemplo, si no hay conexión a internet, o quieres reproducir una
   liquidación anterior a este sprint) — en ese caso ese valor se usa para todo, sin consultar nada
   automáticamente.
5. Haz clic en **"Guardar"**.

Si alguna tasa pactada (remuneratoria o moratoria) supera 1.5× el IBC que ingresaste, el programa **no**
rechaza la liquidación ni recorta la tasa silenciosamente: liquida con la tasa realmente pactada y agrega
un rubro adicional al final del resultado — "Sanción por usura (Art. 72 Ley 45/1990)" — que resta del
saldo el doble del exceso de interés cobrado frente al tope legal. Esa sanción puede dejar un saldo a
favor del deudor (número negativo) si es mayor que lo que aún se le debe.

**Anatocismo condicionado (Art. 886 C.Co.):** por defecto, el interés siempre es simple. Si tu caso
cumple una de las dos condiciones legales que permiten cobrar interés sobre interés, marca uno de estos
dos campos (nunca ambos a la vez):

- **"Demanda judicial (habilita anatocismo, Art. 886 C.Co.)"**: si ya existe una demanda judicial. La
  capitalización empieza automáticamente un año después de la fecha de vencimiento.
- **"¿Hay acuerdo posterior de capitalización?"** + **"Fecha del acuerdo posterior"**: si en cambio hay un
  acuerdo entre las partes para capitalizar intereses, marca esta casilla e ingresa la fecha del acuerdo.
  Esa fecha debe ser al menos un año posterior a la fecha de vencimiento — si ingresas una fecha más
  temprana, el programa no deja liquidar y muestra el motivo.

Cuando el anatocismo está activo, el capital se recalcula capitalizando los intereses vencidos cada año
(desde la fecha habilitante) hasta la fecha de corte de la liquidación — el interés generado antes de ese
punto sigue siendo simple. Estos dos campos solo aparecen para obligaciones **Puntuales** — el anatocismo
no aplica a obligaciones Recurrentes, porque estas no modelan una fecha de vencimiento individual por
cuota.

### 5.8. Exportar la liquidación a PDF o Word

Desde la pantalla de **Resultado de Liquidación** (después de hacer clic en "Liquidar"), al final hay dos
botones: **"Exportar a PDF"** y **"Exportar a Word"**.

1. Haz clic en el botón del formato que necesites.
2. Se abre un diálogo de "Guardar como" con un nombre sugerido (ej. `Liquidacion_2026-030.pdf`) — puedes
   cambiar el nombre y la carpeta antes de guardar.
3. El documento generado incluye: el radicado del expediente, las partes (demandante vs. demandado) y el
   juzgado (si se registró), la tabla resumen (total de abonos aplicados, intereses generados, saldo
   final desglosado en capital e intereses, y el gran total adeudado) y la tabla cronológica completa con
   la misma información que ves en pantalla, más el desglose del saldo en capital, interés y total (fecha,
   concepto, capital base, tasa, interés, pago, saldo de capital, saldo de interés y saldo total).
4. Si el archivo no se pudo guardar (ej. ya está abierto en otro programa, o no tienes permiso de
   escritura en esa carpeta), el programa muestra el mensaje "No se pudo exportar" con el motivo, en vez
   de fallar sin explicación.

El documento Word tiene la misma información que el PDF, pero con un estilo visual más simple (Word no
soporta el mismo nivel de personalización de reportlab) — útil cuando necesitas editar el texto antes de
presentarlo.

### 5.9. Agregar una obligación sancionatoria

Cuando el expediente tiene **Área del derecho = Sancionatorio**, el formulario de "Agregar obligación"
solo permite el tipo **Puntual** (una multa es un hecho único, no admite "Recurrente") y muestra un
campo adicional en vez del campo "Valor":

1. Dentro del Detalle de un expediente Sancionatorio, haz clic en **"Agregar obligación"**.
2. En **Categoría**, la única opción es "Multa sancionatoria (SMLMV/UVT)".
3. Llena:
   - **Concepto**: una descripción corta (ej. "Multa SIC", "Multa Policía Ambiental").
   - **Tasa efectiva anual (%)**: normalmente `0.00` — una multa sancionatoria por lo general no causa
     interés adicional sobre sí misma; déjalo en `0.00` salvo que el caso concreto sí lo requiera.
   - **Fecha de origen**: la fecha del hecho que originó la multa (ej. la fecha de la resolución
     sancionatoria).
   - **Cantidad SMLMV/UVT (Sancionatorio)**: cuántos Salarios Mínimos Legales Mensuales Vigentes o
     Unidades de Valor Tributario ordena la sanción (ej. `2` si la multa es de 2 SMLMV). El programa
     convierte automáticamente esa cantidad a pesos según la fecha del hecho.
4. Haz clic en **"Guardar"**. El campo "Valor" no aparece para esta área — el monto en pesos se calcula
   al liquidar, no al capturar el dato.

La conversión a pesos usa el SMLMV vigente en el año del hecho si la fecha de origen es **anterior al
2020-01-01**, y la UVT vigente en el año del hecho si es **igual o posterior** a esa fecha (tabla
histórica UVT 2006-2026, ver [sección 7.5](#75-conversión-smlmvuvt-para-multas-sancionatorias)). Si el
hecho es de un año para el que todavía no exista UVT publicada por la DIAN (por ejemplo, un año futuro
que la DIAN aún no ha fijado), el programa muestra el mensaje "UVT no disponible" en vez de arriesgar un
valor incorrecto.

### 5.10. Agregar una obligación de honorarios / litigio

Cuando el expediente tiene **Área del derecho = Honorarios / Litigio**, el formulario de "Agregar
obligación" también se limita al tipo **Puntual** y reemplaza el campo "Valor" por cuatro campos
propios de esta área:

1. Dentro del Detalle de un expediente de Honorarios, haz clic en **"Agregar obligación"**.
2. En **Categoría**, la única opción es "Honorarios profesionales (fijo + cuota litis)".
3. Llena:
   - **Concepto**: una descripción corta (ej. "Honorarios proceso ejecutivo").
   - **Tasa efectiva anual (%)**: normalmente `0.00`, salvo que se haya pactado interés adicional sobre
     los honorarios mismos.
   - **Fecha de origen**: la fecha en que se causa el cobro de honorarios.
   - **Honorarios fijos pactados**: la parte fija de la tarifa, en pesos (ej. `1000000.00`).
   - **% Cuota litis pactada**: el porcentaje adicional pactado sobre lo que el cliente efectivamente
     recupere (ej. `10.00` para 10%).
   - **Beneficio obtenido por el cliente**: el monto en pesos que el cliente recuperó o ganó en el
     proceso — es la base sobre la que se calculan tanto la cuota litis como los topes legales.
   - **% Costas judiciales (opcional)**: si el juez condenó en costas y quieres incluirlas como un evento
     de capital separado, ingresa aquí el porcentaje que corresponda (ej. `5.00`). Déjalo vacío si no
     aplica. Este campo (`costas_pct_manual`) es siempre el valor que usa el programa cuando se
     diligencia — es el porcentaje que efectivamente fijó el juez en el auto, **validado contra el rango
     legal permitido según la cuantía del proceso** (corregido 2026-08-01, ver
     [sección 7.6.1](#761-rango-legal-de-costas-manuales-por-cuantía)): 0%-10% en mínima cuantía (hasta 40
     SMMLV), 3%-7% en menor cuantía (40 a 150 SMMLV), 1%-5% en mayor cuantía (más de 150 SMMLV). Si el
     porcentaje que ingresaste no cabe en ese rango, el programa muestra "Costas fuera de rango" al hacer
     clic en "Liquidar" y no calcula nada — no lo recorta al límite más cercano. El motor de cálculo
     automático de costas por tabla de tarifas (Acuerdo PSAA16-10554/2016 del Consejo Superior de la
     Judicatura) ya existe internamente, pero por ahora solo se activa por los campos `costas_tipo_proceso`
     y `costas_instancia` a nivel de base de datos — todavía no hay campos de formulario en esta pantalla
     para diligenciarlos (ver [sección 8](#8-funciones-pendientes-o-en-desarrollo)).
4. Haz clic en **"Guardar"**.

Al liquidar, el programa valida automáticamente que la suma de honorarios fijos + cuota litis no exceda
el 50% del "Beneficio obtenido" (ver
[sección 7.6](#76-tope-de-honorarios-50-acumulado-del-beneficio-obtenido)). Si se excede, el programa
muestra el mensaje "Cuota litis excede el tope" al hacer clic en "Liquidar" y no calcula nada. Si
diligenciaste el porcentaje de costas, el resultado de la liquidación trae dos filas de capital
separadas: una de honorarios profesionales y otra de costas procesales.

### 5.11. Agregar una obligación laboral y liquidar un contrato terminado

Cuando el expediente tiene **Área del derecho = Laboral**, el formulario de "Agregar obligación" cambia
de forma: representa un contrato de trabajo completo, no una deuda puntual o una cuota recurrente — por
eso el campo "Tipo" se oculta (siempre se guarda como Puntual) y la "Tasa efectiva anual (%)" tampoco
aplica (se guarda en 0, sin mostrarse). El campo que en las demás áreas se llama "Fecha de origen
(Puntual)" aquí se muestra como **"Fecha de inicio del contrato"**.

1. Dentro del Detalle de un expediente Laboral, haz clic en **"Agregar obligación"**.
2. Llena:
   - **Concepto**: por ejemplo, "Liquidación de contrato — Juan Pérez".
   - **Valor**: el salario base mensual.
   - **Fecha de inicio del contrato**: el día en que empezó el contrato.
   - **Fecha de terminación de contrato**: el día en que el contrato terminó. A partir de esta fecha se
     calculan las prestaciones (todas se vuelven exigibles ese mismo día — es una liquidación final, no
     un contrato en curso) y, si hubo retardo en el pago, empieza a correr la indemnización moratoria del
     Art. 65 CST.
   - **Prestaciones pagadas** (casilla): si el empleador ya pagó la liquidación completa, marca esta
     casilla y llena **Fecha de pago real** con el día en que se pagó. Si no se ha pagado, deja la
     casilla sin marcar — el programa calculará la mora hasta la fecha de corte del expediente.
3. Haz clic en **"Guardar"**.
4. Haz clic en **"Liquidar"**. El resultado incluye: Cesantías, Intereses/Cesantías, Prima Junio, Prima
   Diciembre, Vacaciones y, si hubo retardo en el pago, un rubro "Indemnización moratoria Art. 65 CST".

**Sobre la indemnización moratoria (Art. 65 CST):** si el pago se hizo (o el corte del expediente cae)
más de 720 días (24 meses) después de la terminación del contrato, el programa cambia automáticamente de
fase — hasta el día 720 cobra un día de salario por cada día de retardo; del día 721 en adelante, cobra
intereses sobre lo adeudado a la tasa de usura histórica certificada por la Superintendencia Financiera
(la misma serie de datos que usa el área Comercial). No hay nada que configurar manualmente para esto.

**Cotizaciones de seguridad social no pagadas (opcional):** si el caso incluye una reclamación de
aportes que el empleador nunca consignó, marca la casilla **"Incluir cotizaciones de seguridad social no
pagadas"** y elige el **Nivel de riesgo ARL** (I a V, según la actividad). El resultado agrega Pensión
(16%), Salud (12.5%), ARL (según el nivel elegido) y, si el salario base es de al menos 4 salarios
mínimos, el Fondo de Solidaridad Pensional (FSP). Si no marcas la casilla, el expediente se liquida
exactamente igual que antes (solo prestaciones sociales y, si aplica, la indemnización moratoria).

**Suspensiones e incapacidades (opcional, requiere la casilla anterior activada):** en el Detalle del
expediente, el grupo **"Eventos contractuales"** permite registrar suspensiones (huelga, licencia no
remunerada, disciplinaria) e incapacidades (común o laboral) del contrato. Una suspensión excluye el
aporte a ARL de esos días (Salud y Pensión se siguen cotizando). Una incapacidad muestra en la
liquidación el desglose completo de quién paga cada tramo de días (empleador, EPS o ARL, según las reglas
legales) — solo la porción a cargo del empleador se suma a la deuda del expediente.

**Ejemplo numérico completo:** un contrato con salario base de **$1.300.000** y **180 días trabajados**
liquida así (base de 360 días/año, 720 para vacaciones):
- Cesantías: `1.300.000 × 180 / 360 = $650.000`.
- Intereses a las cesantías (12% anual, prorrateado): `650.000 × 180 × 0,12 / 360 = $39.000`.
- Prima de junio y prima de diciembre (15 días por semestre cada una): `1.300.000 × 90 / 360 = $325.000`
  cada una.
- Vacaciones: `1.300.000 × 180 / 720 = $325.000`.
- Total de prestaciones (sin mora, sin seguridad social): `$1.664.000`.

**Qué NO calcula todavía esta área:** régimen pensional (IBL, densidad de semanas, tasa de reemplazo) —
ver [sección 8](#8-funciones-pendientes-o-en-desarrollo).

### 5.12. Editar o eliminar un expediente

En la Lista de Expedientes, cada fila tiene dos botones al final: **Editar** y **Eliminar**.

**Editar:**

1. Haz clic en el botón **"Editar"** de la fila del expediente que quieres modificar.
2. Se abre el mismo formulario que al crear un expediente, pero ya lleno con los datos actuales
   (radicado, demandante, demandado, área del derecho, juzgado y fecha de corte). Todos los campos se
   pueden cambiar, incluido el radicado.
3. Haz clic en **"Guardar"** para aplicar los cambios, o cierra la ventana sin guardar para descartarlos.

**Eliminar:**

Eliminar un expediente también borra **todas** sus obligaciones, abonos y registros de auditoría
asociados, de forma permanente — por eso el programa pide confirmación en dos pasos:

1. Haz clic en el botón **"Eliminar"** de la fila del expediente.
2. Aparece una ventana de advertencia preguntando si estás seguro; explica que se borrará el expediente
   junto con todos sus datos asociados y que la acción no se puede deshacer. Haz clic en **"Sí"** para
   continuar, o en "No" para cancelar sin borrar nada.
3. Si confirmaste, aparece una segunda ventana pidiéndote **escribir el radicado exacto** del expediente
   como confirmación adicional. Si lo que escribes no coincide exactamente con el radicado (o cierras esa
   ventana sin escribir nada), el programa avisa "Eliminación cancelada" y **no borra nada**.
4. Si el radicado coincide, el expediente se elimina de inmediato y desaparece de la tabla.

### 5.13. Ver el historial de auditoría y reconstruir una liquidación pasada

Cada vez que liquidas un expediente, el programa guarda automáticamente un
registro: quién lo hizo, cuándo, con qué área del derecho y con qué fecha de
corte. Esto queda visible en la pantalla de Detalle, debajo del botón
"Liquidar", en la sección **"Historial de auditoría"**.

1. Cada fila muestra: fecha y hora de ejecución, usuario del computador que
   liquidó, área del derecho, y fecha de corte usada.
2. Las liquidaciones más recientes aparecen primero.
3. Para volver a ver el resultado exacto de una liquidación anterior (aunque
   las tasas hayan cambiado desde entonces), haz **doble clic** en esa fila:
   el programa te lleva a la pantalla de Resultado de Liquidación mostrando
   ese cálculo tal como quedó guardado, sin recalcularlo.

El historial de auditoría es de solo lectura: no se puede editar ni borrar
una fila individualmente (solo desaparece si se elimina el expediente
completo, ver [sección 5.12](#512-editar-o-eliminar-un-expediente)).

### 5.14. Editar tasas y topes legales (pantalla "⚙ Parámetros")

Antes, si el multiplicador de usura, un tope de cuota litis, un plazo de prescripción o el valor del
SMLMV de un año nuevo cambiaban, había que pedirle a un programador que editara el código. Ya no: desde
la pantalla **"⚙ Parámetros"** cualquier abogado puede consultar y agregar esos valores directamente.

**Dónde está:** haz clic en el botón **"⚙ Parámetros"** de la barra superior — está siempre visible, sin
importar en qué pantalla estés (Lista de Expedientes, Detalle de Expediente o Resultado de Liquidación).

**Qué muestra la tabla principal:** una fila por cada parámetro que el programa sabe manejar, con cuatro
columnas:

- **Categoría**: agrupa los parámetros en "Topes legales", "Plazos de prescripción y caducidad" o
  "Indicadores históricos".
- **Parámetro**: el nombre del valor (ej. "Multiplicador del tope de usura sobre el IBC", "Salario
  Mínimo Legal Mensual Vigente").
- **Valor vigente hoy**: el valor que el programa usaría si liquidara algo hoy mismo. Si dice
  "(sin dato)", es que todavía no se ha cargado ningún valor para ese parámetro (o ninguno aplica a la
  fecha de hoy).
- **Vigente desde**: la fecha desde la que rige ese valor vigente.

**Cómo agregar un valor nuevo:**

1. Haz clic en el botón **"+ Agregar valor nuevo"**, encima de la tabla.
2. En el formulario que se abre, llena:
   - **Parámetro**: elige de la lista cuál de los valores legales estás actualizando.
   - **Valor**: el número nuevo (ej. `1.5` para el multiplicador de usura, o `1300000` para un SMLMV).
   - **Vigente desde**: la fecha a partir de la cual rige este valor (para SMLMV, IPC o UVT, lee la
     advertencia más abajo **antes** de guardar).
   - **Vigente hasta**: **este campo solo aparece para dos parámetros** — el Interés Bancario Corriente
     (IBC, línea Consumo y Ordinario) y la Tasa de Usura de esa misma línea, dentro de "Indicadores
     históricos". Para todos los demás parámetros el campo está oculto y no aplica: el valor rige desde
     "Vigente desde" hacia adelante, sin fecha de corte, hasta que se agregue un valor más nuevo.
   - **Usuario**: tu nombre o usuario, para que quede registrado quién hizo el cambio. Es obligatorio.
   - **Motivo (opcional)**: por qué se agrega este valor (ej. "Actualización SMLMV 2027, Decreto XXXX").
     No es obligatorio, pero se recomienda diligenciarlo — queda guardado para siempre junto con el valor.
3. Haz clic en **"Guardar"**.

> **⚠️ Importante — el SMLMV, el índice IPC acumulado y la UVT son estrictos con la fecha, y no avisan si
> te equivocas:**
>
> Los tres parámetros de "Indicadores históricos" marcados como series **anuales** — el **SMLMV**, el
> **índice IPC acumulado** y la **UVT** — solo quedan "vigentes" para un año si el campo **"Vigente desde" es
> exactamente el 1 de enero de ese año**. Por ejemplo, para cargar el SMLMV del 2027, "Vigente desde"
> tiene que ser `01/01/2027` — ni un día antes ni un día después, y tampoco sirve una fecha del 2026 con
> la idea de que "ya queda lista para cuando llegue el 2027".
>
> Si pones cualquier otra fecha (ej. `15/01/2027` o `01/01/2026` con la intención de que cubra el 2027),
> el programa **guarda el valor sin ningún mensaje de error**, pero ese valor nunca va a aparecer como
> "vigente" para ningún cálculo — la columna "Valor vigente hoy" seguirá mostrando el valor anterior (o
> "(sin dato)"), y cualquier liquidación que necesite ese SMLMV seguirá usando el año anterior, en
> silencio. Si cargaste un SMLMV o un IPC nuevo y no ves que cambie el "Valor vigente hoy", lo primero que
> hay que revisar es que "Vigente desde" haya quedado exactamente en el 1 de enero del año correcto —
> ábrelo con doble clic en la tabla para confirmar la fecha exacta con la que quedó guardado, y si está
> mal, simplemente agrega un valor nuevo con la fecha correcta (no hace falta ni se puede "corregir" la
> fila anterior).
>
> Esto **no** les pasa a los demás parámetros: los topes legales (usura, cuota litis, honorarios) y los
> plazos de prescripción/caducidad rigen desde cualquier fecha que pongas en "Vigente desde" hacia
> adelante, sin exigir que sea un 1 de enero. El IBC y la Tasa de Usura (los dos parámetros con "Vigente
> hasta") tampoco exigen una fecha exacta — rigen dentro del rango completo que hayas escrito entre
> "Vigente desde" y "Vigente hasta".

Si dejas el campo Usuario vacío, o escribes un valor que no es un número, el programa avisa "Datos
inválidos" y no deja guardar.

**Nada se edita ni se borra — solo se agrega:** cuando cambias un valor legal, no estás corrigiendo la
fila anterior, estás agregando una fila nueva. La fila vieja se queda intacta para siempre, para que
cualquier liquidación calculada en el pasado (ver [sección 5.13](#513-ver-el-historial-de-auditoría-y-reconstruir-una-liquidación-pasada))
se pueda reconstruir exactamente con el valor que estaba vigente en ese momento, no con el valor de hoy.
Para ver el historial completo de un parámetro (todos los valores que ha tenido, con su fecha de
vigencia, quién lo agregó y el motivo), haz **doble clic** sobre su fila en la tabla principal.

### 5.15. Agregar una obligación tributaria

Cuando el expediente tiene **Área del derecho = Tributario**, el formulario de "Agregar obligación"
oculta el campo "Tipo" (toda obligación tributaria se guarda como Puntual — un impuesto o una sanción es
un hecho único, no una cuota que se repite cada mes) y la "Tasa efectiva anual (%)" tampoco aplica (el
interés de esta área nunca se pacta manualmente, ver más abajo). En su lugar, el campo **Categoría**
ofrece 5 opciones, y cada una muestra sus propios campos:

1. Dentro del Detalle de un expediente Tributario, haz clic en **"Agregar obligación"**.
2. En **Categoría**, elige una de las 5 opciones:
   - **Impuesto a cargo**: el impuesto ya determinado (por la DIAN o por el propio contribuyente). Llena
     **Concepto**, **Fecha de origen** (la fecha del hecho que genera el cobro) y **Valor** (el monto del
     impuesto en pesos). El programa no calcula una tarifa sobre una base gravable — el valor que
     ingreses aquí ya es el impuesto determinado.
   - **Sanción por extemporaneidad**: la multa por declarar o pagar tarde. Llena **Concepto**, **Fecha de
     origen**, **Base de la sanción (impuesto a cargo o diferencia)** (el monto en pesos sobre el que se
     calcula el 5% mensual) y **Meses o fracción de atraso (extemporaneidad)** (cuántos meses de atraso
     hubo; cualquier fracción de mes se cobra como un mes completo).
   - **Sanción por inexactitud**: la multa por declarar un valor distinto al que correspondía. Llena
     **Concepto**, **Fecha de origen** y **Base de la sanción (impuesto a cargo o diferencia)** (la
     diferencia entre lo declarado y lo que se determinó). Si el contribuyente omitió activos o incluyó
     pasivos inexistentes, marca la casilla **"Agravada (omisión de activos o pasivos inexistentes)"** —
     la sanción sube de 160% a 200% de esa diferencia.
   - **Sanción por error aritmético**: la multa por un error de cálculo en la declaración. Llena
     **Concepto**, **Fecha de origen** y **Base de la sanción (impuesto a cargo o diferencia)** (la
     diferencia generada por el error).
   - **Depuración de renta líquida gravable**: el cálculo informativo de la base gravable de un período.
     Llena **Concepto**, **Fecha de origen** y los 5 campos de depuración, todos en pesos: **Ingresos
     brutos**, **Devoluciones/rebajas/descuentos**, **Costos**, **Deducciones** y **Rentas exentas**.
3. Haz clic en **"Guardar"**.

**El piso de 10 UVT:** al liquidar, ninguna de las tres sanciones (extemporaneidad, inexactitud, error
aritmético) puede quedar por debajo de 10 UVT del año del hecho — si el 5%, el 160%/200% o el 30%
calculado da un monto menor a esas 10 UVT, el programa cobra 10 UVT en su lugar. Este piso se aplica
automáticamente; no hay nada que marcar en el formulario para activarlo.

**La renta líquida gravable no es una deuda:** a diferencia del impuesto a cargo y las tres sanciones, la
obligación "Depuración de renta líquida gravable" no se suma al saldo de la liquidación — es informativa,
y el resultado la muestra en un bloque aparte. Un expediente tributario admite como máximo una obligación
de este tipo (un solo período gravable por expediente); si intentas liquidar un expediente con dos, el
programa avisa el error en vez de calcular algo incorrecto.

**El interés es automático, nunca pactado:** a diferencia de Comercial (donde tú ingresas la tasa
remuneratoria y moratoria pactadas), en Tributario el interés moratorio del E.T. art. 635 (usura vigente
menos dos puntos, resuelta automáticamente por tramos históricos) se aplica solo al **impuesto a cargo**;
las sanciones nunca lo acumulan por sí solas — por eso el campo "Tasa efectiva anual (%)" ni siquiera
aparece en el formulario de esta área.

**Mora superior a 3 años (Art. 867-1 E.T., corregido 2026-08-01):** si al momento de liquidar han pasado
más de 3 años desde la fecha de origen de una obligación tributaria, el programa agrega automáticamente
una actualización por IPC, sin nada que marcar en el formulario:
- **Impuesto a cargo**: conserva el interés E.T. 635 de siempre y además se indexa por IPC — si la suma de
  ambos superaría lo que produciría la tasa de usura plena (sin el descuento de los 2 puntos) sobre el
  mismo capital y período, el programa recorta automáticamente la indexación para no pasarse de ese techo.
- **Sanciones**: no acumulan interés (nunca lo hicieron) y en su lugar se indexan por IPC — la corrección
  hace que esa indexación sí quede reflejada en el resultado a partir de los 3 años.

**Cada obligación se liquida por separado:** desde esta misma corrección, cada obligación tributaria del
expediente (el impuesto, cada sanción) corre en su propia liquidación aislada — es la única forma de que
una sanción no acumule interés mientras el impuesto sí lo hace. Esto significa que **cada abono queda
ligado a la obligación desde la que lo registraste** (seleccionas la fila de la obligación en la tabla y
haces clic en "Agregar abono", igual que en las demás áreas) y solo se aplica a esa obligación: ya no
existe un orden automático de "primero sanciones, luego intereses, luego impuesto" que reparta un mismo
abono entre varias obligaciones — si quieres pagar tanto una sanción como el impuesto, registra un abono
para cada una desde su propia fila.

---

## 6. Áreas del derecho: cuáles funcionan hoy

Al crear un expediente, el campo "Área del derecho" muestra 6 opciones, y **las seis calculan de verdad
hoy**:

| Área | ¿Funciona? |
|---|---|
| Civil / Familia | ✅ Sí — interés del Art. 1617 C.C. (6% anual o la tasa que se pacte), sobre obligaciones puntuales y recurrentes, con abonos. |
| Comercial | ✅ Sí — Art. 884 C.Co., tasa remuneratoria antes del vencimiento y tasa moratoria después. Si alguna tasa supera el tope de usura (1.5× el IBC que ingreses), se liquida igual y se resta del saldo la sanción legal (doble del exceso cobrado). Ver [sección 5.7](#57-agregar-una-obligación-comercial). |
| Laboral | ✅ Sí — liquidación final (finiquito) de un contrato: cesantías, intereses a cesantías, prima, vacaciones, indemnización moratoria bifásica del Art. 65 CST, y opcionalmente cotizaciones de seguridad social (pensión, salud, ARL, FSP) más incapacidades y suspensiones contractuales. Ver [sección 5.11](#511-agregar-una-obligación-laboral-y-liquidar-un-contrato-terminado). |
| Sancionatorio | ✅ Sí — multas en SMLMV o UVT (Ley 1955/2019 art. 49): SMLMV para hechos anteriores al 2020-01-01, UVT (tabla histórica 2006-2026) desde esa fecha en adelante. Ver [sección 5.9](#59-agregar-una-obligación-sancionatoria). |
| Honorarios / Litigio | ✅ Sí — honorarios profesionales y cuota litis, validando el tope único del 50% acumulado del beneficio obtenido; las costas judiciales se ingresan como un porcentaje manual (el que haya fijado el juez en el auto). Ver [sección 5.10](#510-agregar-una-obligación-de-honorarios--litigio). |
| Tributario | ✅ Sí — impuesto a cargo (interés E.T. 635), sanciones por extemporaneidad/inexactitud/error aritmético (con piso de 10 UVT), actualización IPC adicional para mora superior a 3 años (Art. 867-1 E.T.), y depuración de Renta Líquida Gravable informativa. Cada obligación liquida y recibe abonos por separado. Ver [sección 5.15](#515-agregar-una-obligación-tributaria). |

Si en algún momento se intenta liquidar un área cuya lógica todavía no esté lista (ver
[sección 8](#8-funciones-pendientes-o-en-desarrollo)), el programa muestra el mensaje "Área no
implementada" en vez de calcular — nunca da un resultado numérico inventado o incorrecto.

---

## 7. Valores legales y parámetros: dónde están y cómo consultarlos o cambiarlos

Todos los valores fijos que usa el programa (tasas legales, categorías disponibles, áreas habilitadas)
están guardados en archivos de texto dentro del código, **no** escondidos ni cifrados. Aquí está
exactamente dónde encontrarlos y qué significa cada uno.

**Nota:** varios de los valores descritos abajo (el multiplicador de usura, los topes de cuota litis, los
plazos de prescripción/caducidad, la tasa civil legal, el descuento del interés moratorio tributario, y
las series de SMLMV/IPC/IBC-Usura) ya no requieren tocar código para cambiarse — se administran desde la
pantalla **"⚙ Parámetros"**, ver [sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros).
Lo que sigue documenta además dónde vive cada valor por dentro, para quien programa.

### 7.1. Tasa de interés civil (6% anual, Art. 1617 C.C.)

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación", el campo **"Tasa efectiva
  anual (%)"** viene pre-llenado con `6.00`, pero es editable por cada obligación — no hace falta tocar
  código para usar una tasa distinta en un caso puntual.
- **Dónde vive el valor por defecto en el código**: `app/views/obligaciones.py`, línea del campo
  `self.campo_tasa = QLineEdit("6.00")`.
- **Cómo se convierte esa tasa anual a diaria**: `app/engine/interest/rate_conversion.py`, clase
  `EffectiveRateConverter`, usando la fórmula `i_diario = (1 + i_anual)^(1/365) - 1`.
- **Ejemplo numérico completo**: con la tasa por defecto del 6% anual, `i_diario = (1.06)^(1/365) - 1 ≈
  0,00015965` (0,015965% diario). Sobre un capital de **$10.000.000** durante **30 días**, el interés es
  `I = C × i × t = 10.000.000 × 0,00015965 × 30 ≈ $47.896`.

### 7.1.1. Tope de usura comercial (1.5x IBC, Ley 45/1990 art. 72)

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente Comercial,
  el campo **"IBC vigente aplicable (%)"** — lo diligencias tú con el IBC certificado por la
  Superfinanciera para la fecha del caso, no hay un valor por defecto.
- **Dónde vive la lógica en el código**: `app/engine/interest/usury_validator.py`, función
  `calcular_tope_usura`, más `ComercialStrategy._calcular_sancion_usura`/`_aplicar_sanciones_usura` en
  `app/services/area_strategy.py`. Se evalúa automáticamente al liquidar, tanto para la tasa
  remuneratoria como para la moratoria.
- **Qué pasa si se excede el tope**: el programa **no** rechaza la liquidación ni recorta la tasa. Calcula
  cuánto interés se cobró de más frente al tope legal, dobla ese exceso (sanción del Art. 72 Ley 45/1990)
  y lo resta del saldo total como un rubro adicional visible en el resultado — puede dejar saldo a favor
  del deudor.

### 7.2. Categorías de obligación disponibles (área Civil/Familia)

- **Dónde se ven**: en el desplegable "Categoría" del formulario de "Agregar obligación".
- **Dónde se editan**: `app/core/constants.py`, lista `CATEGORIAS_CIVIL_FAMILIA`. Cada línea es una
  categoría con su código interno y su nombre visible (ej. `("CHILD_SUPPORT", "Cuota alimentaria")`).
  Agregar una categoría nueva ahí la hace aparecer automáticamente en el formulario — no requiere tocar
  ningún otro archivo, **pero** el código de la categoría debe coincidir con uno de los reconocidos por
  el motor de cálculo (`app/engine/liquidation/engine.py`, variable `_capital_concepts`), o el programa
  no sabrá procesarla.

### 7.3. Áreas del derecho habilitadas

- **Dónde se editan**: `app/core/constants.py`, lista `AREAS_DERECHO`. Cada línea tiene el código del
  área, su nombre visible, y `True`/`False` según si está habilitada para calcular. Cambiar un `False` a
  `True` ahí **no hace que el área funcione** — solo la deja seleccionable en el formulario; la lógica de
  cálculo real de esa área tiene que estar implementada primero (ver [sección 8](#8-funciones-pendientes-o-en-desarrollo)
  y `Pendientes.md`).

### 7.4. Dónde queda guardada toda la información capturada

- Archivo `bastium.db`, en la raíz del proyecto. Es una base de datos SQLite — se puede abrir con
  cualquier programa visor de SQLite si alguna vez necesitas revisar los datos crudos, pero no es
  necesario para el uso normal del programa.

### 7.5. Conversión SMLMV→UVT para multas sancionatorias

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente
  Sancionatorio, el campo **"Cantidad SMLMV/UVT (Sancionatorio)"** — ver
  [sección 5.9](#59-agregar-una-obligación-sancionatoria). No hay valores por defecto: cada multa trae su
  propia cantidad de salarios mínimos o UVT.
- **Dónde vive la lógica en el código**: `app/engine/indexation/smlmv_to_uvt.py`, función
  `resolver_base_sancion`. Se invoca automáticamente al liquidar (`SancionatorioStrategy.liquidar()` en
  `app/services/area_strategy.py`). Los valores de SMLMV y de UVT por año están en
  `app/engine/indexation/historical_index.py` (funciones `get_smlmv_for_year` y `get_uvt_for_year`), y
  también se pueden consultar o corregir desde la pantalla "⚙ Parámetros" (claves `SMLMV` y `UVT`, ver
  [sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros)).
- **Qué pasa si el hecho es posterior al 2020-01-01**: la ley pasó de expresar estas multas en SMLMV a
  expresarlas en UVT a partir de esa fecha; el programa ya tiene cargada la tabla histórica de UVT
  (2006-2026, ver `Pendientes.md`, Sprint 14) y convierte automáticamente. Solo lanza el error "UVT no
  disponible" si el hecho es de un año que la DIAN todavía no ha publicado (por ejemplo, un año futuro
  aún sin resolución) — en ese caso, en vez de adivinar un valor, no calcula nada.

### 7.6. Tope de honorarios (50% acumulado del beneficio obtenido)

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente de
  Honorarios, los campos **"% Cuota litis pactada"** y **"Beneficio obtenido por el cliente"** — ver
  [sección 5.10](#510-agregar-una-obligación-de-honorarios--litigio). No hay valores por defecto.
- **Dónde vive la lógica en el código**: `app/services/area_strategy.py`, clase `HonorariosStrategy`,
  método `_validar_obligacion_honorarios`. El tope ya no es una constante fija en el código — desde el
  Sprint 13 se lee como parámetro legal versionado (`get_parametro("HONORARIOS_TOTAL_PCT", ...)`),
  consultable y editable desde la pantalla "⚙ Parámetros" (ver
  [sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros)) sin tocar código.
  **Corregido en el Sprint 4 (2026-08-01)** tras confirmación del despacho: no existen dos topes en
  cascada (30% individual + 50% total) — el único tope legal es el 50% acumulado de honorarios fijos +
  cuota litis sobre el beneficio obtenido. Una cuota litis alta por sí sola ya no bloquea nada si el
  total se mantiene dentro del 50%.
- **Qué pasa si se excede el tope**: el programa bloquea la liquidación con el error "Cuota litis excede
  el tope" al hacer clic en "Liquidar", citando "Honorarios Desproporcionados - Art. 35 Num. 4 Ley
  1123/2007" (alerta de riesgo disciplinario) — la validación ocurre al calcular, no al capturar el
  dato.
- **Nota (Sprint 24):** esto no impide que el mismo campo "% Cuota litis pactada" tenga, además, un chequeo
  de sanidad numérica independiente (rango 0%-100%, no el tope legal del 50%) que sí corre al hacer clic en
  "Guardar" en el formulario de la obligación (`ObligacionFormDialog._parse_campos_honorarios` en
  `app/views/obligaciones.py`) — son dos validaciones distintas, con propósitos y momentos diferentes.

### 7.6.1. Rango legal de costas manuales por cuantía

Corregido en el Sprint 18 (2026-08-01), respuesta del despacho: el porcentaje de costas manual
(`costas_pct_manual`, cualquier área que admita costas — ver sección 5.7-5.11) ya no acepta cualquier
número. Se valida contra el rango legal permitido según la cuantía de las pretensiones reconocidas (CGP
art. 25), en SMLMV vigentes en la fecha de origen de la obligación:

| Cuantía | Rango de pretensiones | % permitido |
|---|---|---|
| Mínima | Hasta 40 SMLMV | 0% – 10% |
| Menor | Más de 40 hasta 150 SMLMV | 3% – 7% |
| Mayor | Más de 150 SMLMV | 1% – 5% |

Si el porcentaje ingresado no cabe en el rango de su cuantía, el programa muestra "Costas fuera de rango"
al hacer clic en "Liquidar" y no calcula nada — **rechaza, no recorta** el valor al límite más cercano.
Esta tabla es distinta (más simple, y con rangos propios) de la tabla granular por tipo de proceso del
Acuerdo PSAA16-10554 que ya usa el cálculo automático (`costas_tipo_proceso`/`costas_instancia`, ver
[sección 8](#8-funciones-pendientes-o-en-desarrollo)) — solo aplica al porcentaje manual. Queda una
pregunta de seguimiento con el despacho (`Preguntas-Para-Abogado-Abiertas.md`, Sprint 18) sobre si esta tabla simple
en realidad reemplaza a la granular en vez de solo acotar el valor manual.

**Nota (Sprint 24):** igual que con la cuota litis (sección 7.6), el campo "% Costas judiciales" tiene
además un chequeo de sanidad numérica independiente (rango 0%-100%, no el rango legal por cuantía de la
tabla anterior) que corre al hacer clic en "Guardar" en el formulario de la obligación
(`ObligacionFormDialog._parse_campos_honorarios` en `app/views/obligaciones.py`) — son dos validaciones
distintas, con propósitos y momentos diferentes.

### 7.7. Indexación IPC (corrección monetaria)

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente Civil/
  Familia, la casilla **"Aplica indexación IPC (corrección monetaria)"** — ver
  [sección 5.3](#53-agregar-una-obligación-puntual-una-deuda-de-una-sola-vez). No viene marcada por
  defecto: el abogado decide caso por caso si la obligación debe indexarse, además de generar intereses.
- **Dónde vive la lógica en el código**: `app/engine/indexation/ipc.py` (`IPCIndexation.calculate`) y
  `app/engine/indexation/historical_index.py` (`get_ipc_interpolado_for_date`), invocados desde
  `CivilFamiliaStrategy._evento_indexacion` en `app/services/area_strategy.py`.
- **Cómo se calcula**: `Va = Vh × (IPC_final / IPC_inicial)`. Para una obligación **Puntual**, se indexa
  una sola vez desde la fecha de origen hasta la fecha de corte del expediente. Para una obligación
  **Recurrente** (cuotas mensuales), cada cuota se indexa individualmente desde su propia fecha de
  vencimiento — no todas desde el inicio de la obligación — porque cada cuota se deprecia un tiempo
  distinto.
- **Ejemplo numérico completo**: una obligación Puntual de **$5.000.000** con fecha de origen cuando el
  IPC acumulado era **100** (IPC_inicial), liquidada a una fecha de corte donde el IPC acumulado es
  **110** (IPC_final), queda indexada en `Va = 5.000.000 × (110 / 100) = $5.500.000` — el rubro de
  indexación que se suma a la liquidación es la diferencia, `$500.000`.
- **Limitación conocida**: la fuente de datos (Sprint 5) solo trae el IPC de cierre de cada año, no mes a
  mes como certifica el DANE en la vida real. Para una fecha intermedia dentro del año, el programa
  interpola linealmente entre el índice de cierre del año anterior y el del año actual — es una
  aproximación razonable, pero no es el valor mensual exacto que certificaría el DANE. Para fechas de
  2026 en adelante (la serie no llega hasta ahí), se usa el índice de 2025 como aproximación.
- **Interés sobre capital ya indexado (algoritmo "Suma Única")**: desde el Sprint 20, marcando la casilla
  adicional **"Interés sobre capital ya indexado (algoritmo Suma Única / Ley 80 de 1993)"** junto a "Aplica
  indexación IPC", el interés del 6% (Art. 1617 C.C.) se calcula sobre el capital ya indexado (`Va`), no
  sobre el capital histórico — el algoritmo "Suma Única" del PDF (pág. 21-22), que también aplica a los
  intereses de la Ley 80 de 1993 para contratos estatales (misma mecánica, sin campo propio). Sin esta
  casilla marcada, el comportamiento es el mismo de antes de este sprint (interés solo sobre el capital
  histórico). Cada obligación decide por sí sola: un mismo expediente puede tener obligaciones con y sin
  esta casilla marcada, cada una liquida con su propio criterio (Art. 1617 C.C., Sprint 21: cada obligación
  se liquida por separado con su propia tasa).

### 7.8. TRM y obligaciones en moneda extranjera

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente Comercial,
  el campo **"Moneda"** y, si se elige "USD", los campos opcionales **"TRM aplicable (COP por USD)"** y
  **"Fecha de referencia de la TRM"** — ver [sección 5.7](#57-agregar-una-obligación-comercial).
- **Dónde vive la lógica en el código**: `app/engine/currency/converter.py` (`convertir_a_pesos`) y
  `app/engine/currency/trm_provider.py` (`SFCTRMProvider`, el proveedor en vivo; `ManualTRMProvider`, la
  anulación manual), invocados desde `ComercialStrategy._valor_en_pesos_en_fecha` en
  `app/services/area_strategy.py`.
- **Corregido en el Sprint 12 (2026-08-01)** tras respuesta del despacho: antes, el capital se convertía a
  pesos **una sola vez** con una TRM digitada por el abogado, y esa misma cifra en pesos se usaba durante
  toda la liquidación sin volver a considerar el tipo de cambio — el despacho calificó esto de "TRM
  congelada" y exigió eliminarla (Art. 874 C.Co.: la conversión debe hacerse según la tasa de cambio
  vigente en la fecha real de cada evento, no una sola vez al inicio).
- **Cómo se calcula ahora**: cada evento se convierte a pesos con la TRM de **su propia fecha**, consultada
  en vivo a la Superintendencia Financiera (`SFCTRMProvider`, vía el dataset abierto de datos.gov.co que
  espeja el servicio oficial de la SFC) — el capital, con la TRM de la fecha de origen de la obligación;
  **cada abono, con la TRM de su propia fecha de pago** (el cambio central de este sprint: dos abonos en
  fechas distintas de la misma obligación en USD pueden convertirse a un número distinto de pesos por
  dólar, según cómo se haya movido la TRM entre esas fechas).
- **Ejemplo numérico**: una obligación de USD 1.000 se paga con un abono de USD 1.000 el 2025-02-01. Si la
  TRM de esa fecha certificada por la SFC es $4.200/USD, el abono aplica $4.200.000 — sin importar qué TRM
  tenía la obligación cuando nació (la TRM "congelada" que ya no se usa por defecto).
- **Anulación manual (opcional)**: si diligencias **"TRM aplicable"**, ese valor fijo se usa para *todos*
  los eventos de esa obligación (capital y abonos), sin consultar la API — útil sin conexión a internet, o
  para reproducir exactamente una liquidación hecha antes de este sprint. Si lo dejas vacío (el caso
  normal desde este sprint), el programa siempre consulta la TRM real por fecha.
- **Qué pasa si la API no responde**: el programa muestra el mensaje "TRM no disponible" al hacer clic en
  "Liquidar" y no calcula nada — no aproxima ni usa un valor viejo en su lugar. En ese caso, diligencia la
  TRM manualmente como respaldo (ver punto anterior).
- **Qué NO hace todavía**: no soporta otras monedas extranjeras distintas de USD.

---

## 8. Funciones pendientes o en desarrollo

Estas funciones están planeadas pero **todavía no existen o no están conectadas**. El detalle técnico
completo de cada una (qué construir, qué documentos consultar, en qué orden) está en
[`Pendientes.md`](../Pendientes.md), organizado en sprints. Aquí un resumen en lenguaje simple:

- ✅ **Seguridad social, incapacidades y suspensiones en el área Laboral** — cotizaciones de pensión,
  salud, ARL y FSP, más incapacidades (común/laboral) y suspensiones contractuales, ya calculan como
  parte de la liquidación judicial de un contrato Laboral. Ver
  [sección 5.11](#511-agregar-una-obligación-laboral-y-liquidar-un-contrato-terminado)
  (`Pendientes.md`, Sprint 16).
- ✅ **Tabla histórica de UVT** (2006-2026) ya está cargada y conectada — el área Sancionatorio convierte
  a pesos tanto los hechos anteriores al 2020-01-01 (vía SMLMV) como los posteriores (vía UVT). Ver
  [sección 7.5](#75-conversión-smlmvuvt-para-multas-sancionatorias) (`Pendientes.md`, Sprint 14).
- ✅ **Costas judiciales (agencias en derecho) por tabla real de tarifas** — el motor de cálculo
  automático según el Acuerdo PSAA16-10554/2016 del Consejo Superior de la Judicatura (las 18 categorías
  de proceso de su art. 5°) ya existe y está conectado en Civil/Familia, Comercial, Laboral,
  Sancionatorio y Honorarios (`Pendientes.md`, Sprint 18). El porcentaje manual (`costas_pct_manual`, el
  que haya fijado el juez en el auto) sigue siendo la única forma de fijar costas desde esta pantalla, y
  solo está disponible en el formulario de Honorarios/Litigio (ver
  [sección 5.10](#510-agregar-una-obligación-de-honorarios--litigio)) — activar el cálculo automático por
  tabla de tarifas requiere todavía fijar `costas_tipo_proceso`/`costas_instancia` a nivel de datos, sin
  campos propios en ningún formulario de esta versión.
- ✅ **Anatocismo comercial condicionado (Art. 886 C.Co.)** — el área Comercial ya aplica interés sobre
  interés cuando se cumple una de las dos condiciones legales (demanda judicial o acuerdo posterior de
  capitalización, con al menos un año de intereses vencidos), capitalizando periódicamente cada
  aniversario desde la fecha de capitalización; el resto de la liquidación sigue en interés simple
  (`Pendientes.md`, Sprint 19). Ver [sección 5.7](#57-agregar-una-obligación-comercial).
- ✅ **Indexación por IPC** ya está conectada a Civil/Familia (Sprint 8) — ver
  [sección 7.7](#77-indexación-ipc-corrección-monetaria).
- 🚧 **Prescripción y caducidad** (saber si una deuda ya "venció" el plazo legal para cobrarla) — el
  motor de cálculo ya existe y está probado (`app/engine/temporal/prescripcion.py`: fechas límite por
  tipo de acción, prescripción parcial cuota a cuota para cuotas alimentarias, e interrupción por
  demanda), pero todavía no está conectado a ninguna pantalla ni bloquea la liquidación de un expediente
  (`Pendientes.md`, Sprint 7).
- 🚧 **Calendario de días hábiles y términos procesales** — el motor ya existe y está probado
  (`CalendarUtils.es_dia_habil/sumar_dias_habiles/dias_habiles_entre/notificacion_surtida_el/
  vencimiento_calendario` en `app/engine/time/calendar.py`, y el modelador de términos con
  interrupción/suspensión/reanudación en `app/engine/temporal/terminos.py`), pero todavía no está
  conectado a ninguna pantalla — hoy sirve como base interna para el motor de prescripción y caducidad
  del Sprint 7 (`Pendientes.md`, Sprint 6).
- ✅ **Derecho Tributario** ya está conectado como sexta área operable: impuesto a cargo, las tres
  sanciones (extemporaneidad, inexactitud, error aritmético, con piso legal de 10 UVT), interés moratorio
  automático del E.T. art. 635 sobre el impuesto, actualización IPC adicional para mora superior a 3 años
  (Art. 867-1 E.T., cada obligación liquidada y pagada por separado) y depuración de Renta Líquida
  Gravable informativa. Ver [sección 5.15](#515-agregar-una-obligación-tributaria)
  y [sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy) (`Pendientes.md`, Sprint 15). **Qué queda
  explícitamente fuera de alcance:** el cálculo de la tarifa del impuesto sobre la renta líquida gravable
  (el usuario ingresa el impuesto a cargo ya determinado, el programa no aplica una tarifa
  automáticamente sobre la base gravable), la compensación de pérdidas fiscales de años anteriores, la
  integración en vivo con la DIAN, y varios períodos gravables en un mismo expediente (un expediente
  tributario admite una sola obligación "Depuración de renta líquida gravable" — un solo período gravable
  por expediente).
- ✅ **TRM y obligaciones en moneda extranjera** ya está conectada al área Comercial (Sprint 12) — ver
  [sección 7.8](#78-trm-y-obligaciones-en-moneda-extranjera).
- ✅ **Parámetros legales versionados** (pantalla "⚙ Parámetros") — el Sprint 13, planeado originalmente
  como un motor de reglas configurable de alcance mucho mayor, se reemplazó por este dominio más acotado:
  tasas, topes, plazos e indicadores históricos editables desde la GUI, con historial completo. Ver
  [sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros).

---

## 9. Preguntas frecuentes y solución de problemas

**"Al instalar me sale un error de rutas largas / Long Path."**
Ver [sección 2.5](#25-problema-conocido-rutas-largas-en-windows).

**"No sé si el programa quedó bien instalado."**
Corre `.venv\Scripts\python.exe -m pytest -q` (ver [sección 2.6](#26-verificar-que-todo-quedó-instalado-correctamente-opcional-recomendado)).
Si todo termina en "N passed" sin "failed", está bien.

**"Presioné Liquidar y no pasó nada / me salió un mensaje de error."**
Revisa que el expediente tenga al menos una obligación cargada. Si el mensaje dice "Área no
implementada", es porque el área seleccionada aún no calcula (ver sección 6). Si dice "No se pudo
liquidar" con otro texto, anota el mensaje exacto — puede ser una validación de datos.

**"Al liquidar un expediente Sancionatorio me sale 'UVT no disponible'."**
Desde el Sprint 14, esto solo ocurre si la "Fecha de origen" de la multa cae en un año para el que la
DIAN todavía no ha publicado la UVT (por ejemplo, un año futuro sin resolución vigente) — la tabla
histórica cubre 2006-2026. Revisa la fecha de origen, o agrega el valor de UVT del año faltante desde la
pantalla "⚙ Parámetros" en cuanto la DIAN lo publique (ver
[sección 7.5](#75-conversión-smlmvuvt-para-multas-sancionatorias)).

**"Cargué el SMLMV/IPC nuevo pero la liquidación sigue usando el valor del año pasado."**
Casi siempre es un problema de fecha, no del programa: el SMLMV y el índice IPC acumulado solo se
reconocen como vigentes si "Vigente desde" quedó en **exactamente el 1 de enero** del año que querías
cargar (ej. `01/01/2027`, no el `15/01/2027` ni el `01/01/2026`). El programa guarda el valor igual, sin
avisar del error — ábrelo con doble clic en la tabla de "⚙ Parámetros" para revisar la fecha exacta con
la que quedó, y si está mal, agrega un valor nuevo con la fecha correcta. Ver la advertencia completa en
[sección 5.14](#514-editar-tasas-y-topes-legales-pantalla--parámetros).

**"¿Dónde quedan guardados mis expedientes si cierro el programa?"**
En el archivo `bastium.db` dentro de la carpeta del proyecto. No lo borres si quieres conservar la
información.

**"¿Necesito internet para usar BASTIUM?"**
No. Todo el cálculo y almacenamiento ocurre en tu computador.

---

## 10. Para quien programa: comandos útiles

```
# Instalar/reinstalar dependencias
.venv\Scripts\python.exe -m pip install -r requirements.txt

# Iniciar la aplicación
.venv\Scripts\python.exe main.py

# Correr toda la suite de pruebas
.venv\Scripts\python.exe -m pytest -q

# Correr solo las pruebas de un módulo (ejemplo: la vista de expedientes)
.venv\Scripts\python.exe -m pytest tests/views/test_expedientes.py -v
```

Para entender la arquitectura del código, empezar por `docs/specifications/` (un archivo por motor interno) y
`docs/superpowers/specs/2026-07-14-mvp-captura-liquidacion-civil-familia-design.md` (diseño del MVP). El
trabajo futuro está en [`Pendientes.md`](../Pendientes.md), organizado en sprints autocontenidos.
