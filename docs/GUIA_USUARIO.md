# Guía de Usuario de BASTIUM

> Esta guía está escrita para que cualquier persona pueda instalar y usar BASTIUM sin conocimientos
> técnicos previos. Si en algún punto algo no funciona como se describe aquí, revisa la sección
> [9. Preguntas frecuentes y solución de problemas](#9-preguntas-frecuentes-y-solución-de-problemas)
> antes que nada.
>
> **Última actualización:** 2026-07-15 — refleja el estado del MVP de Civil/Familia. Cada vez que se
> complete un sprint nuevo de [`Pendientes.md`](../Pendientes.md), esta guía se actualiza para que nunca
> quede desactualizada respecto al programa real.

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

Hoy en día, BASTIUM sabe calcular liquidaciones del área **Civil y de Familia** (por ejemplo: cuotas de
alimentos, gastos médicos, deudas civiles con interés). Otras áreas del derecho (Comercial, Laboral,
Sancionatorio, Honorarios) están planeadas pero **todavía no calculan** — más detalle en la
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
`81 passed` (un número seguido de "passed", sin ningún "failed"), significa que todo está instalado y
funcionando correctamente. Si ves errores, revisa la [sección 9](#9-preguntas-frecuentes-y-solución-de-problemas).

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

BASTIUM tiene **3 pantallas**, y te mueves entre ellas automáticamente según lo que hagas (no hay un menú
de navegación separado):

1. **Lista de Expedientes** — la pantalla con la que arranca el programa. Muestra una tabla con todos los
   expedientes que ya creaste (radicado, demandante, demandado, área) y un botón **"Nuevo expediente"**.
   Si haces doble clic sobre una fila, entras al detalle de ese expediente.

2. **Detalle de Expediente** — se abre al hacer doble clic en un expediente de la lista. Aquí ves dos
   tablas lado a lado: **Obligaciones** (las deudas del expediente) y **Abonos** (los pagos hechos), cada
   una con su botón de "Agregar". Abajo hay un botón grande **"Liquidar"**.

3. **Resultado de Liquidación** — se abre automáticamente después de presionar "Liquidar". Muestra una
   tabla con el detalle día por día de cómo se acumuló el interés, y al final tres totales: interés
   acumulado, pagos aplicados y saldo final.

No hay botón de "volver atrás" todavía entre pantallas — para volver a la lista, cierra y vuelve a abrir
el programa (esto es una limitación conocida, ver [sección 8](#8-funciones-pendientes-o-en-desarrollo)).

---

## 5. Cómo usar cada función, paso a paso

### 5.1. Crear un expediente nuevo

1. Abre el programa (ver [sección 3](#3-cómo-iniciar-el-programa)).
2. En la pantalla de Lista de Expedientes, haz clic en el botón **"Nuevo expediente"**.
3. Se abre una ventana con un formulario. Llena estos campos:
   - **Radicado**: el número o referencia interna del caso (ej. `2026-00123`). Es obligatorio.
   - **Demandante**: nombre de quien reclama.
   - **Demandado**: nombre de quien debe.
   - **Área del derecho**: por ahora deja seleccionada **"Civil / Familia"** (es la única opción activa;
     las demás aparecen "grises" con la nota "Próximamente" porque todavía no calculan, ver
     [sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy)).
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

---

## 6. Áreas del derecho: cuáles funcionan hoy

Al crear un expediente, el campo "Área del derecho" muestra 5 opciones, pero **solo una calcula de
verdad hoy**:

| Área | ¿Funciona? |
|---|---|
| Civil / Familia | ✅ Sí — interés del Art. 1617 C.C. (6% anual o la tasa que se pacte), sobre obligaciones puntuales y recurrentes, con abonos. |
| Comercial | 🚧 No todavía — aparece "gris" en el formulario, no se puede seleccionar. Planeado en `Pendientes.md`, Sprint 2. |
| Laboral | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 3. |
| Sancionatorio | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 4. |
| Honorarios / Litigio | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 4. |

Si en algún momento estas áreas se habilitan en el selector y se intenta liquidar antes de que su lógica
esté lista, el programa muestra el mensaje "Área no implementada" en vez de calcular — nunca da un
resultado numérico inventado o incorrecto.

---

## 7. Valores legales y parámetros: dónde están y cómo consultarlos o cambiarlos

Todos los valores fijos que usa el programa (tasas legales, categorías disponibles, áreas habilitadas)
están guardados en archivos de texto dentro del código, **no** escondidos ni cifrados. Aquí está
exactamente dónde encontrarlos y qué significa cada uno:

### 7.1. Tasa de interés civil (6% anual, Art. 1617 C.C.)

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación", el campo **"Tasa efectiva
  anual (%)"** viene pre-llenado con `6.00`, pero es editable por cada obligación — no hace falta tocar
  código para usar una tasa distinta en un caso puntual.
- **Dónde vive el valor por defecto en el código**: `app/views/obligaciones.py`, línea del campo
  `self.campo_tasa = QLineEdit("6.00")`.
- **Cómo se convierte esa tasa anual a diaria**: `app/engine/interest/rate_conversion.py`, clase
  `EffectiveRateConverter`, usando la fórmula `i_diario = (1 + i_anual)^(1/365) - 1`.

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

---

## 8. Funciones pendientes o en desarrollo

Estas funciones están planeadas pero **todavía no existen o no están conectadas**. El detalle técnico
completo de cada una (qué construir, qué documentos consultar, en qué orden) está en
[`Pendientes.md`](../Pendientes.md), organizado en sprints. Aquí un resumen en lenguaje simple:

- 🚧 **Cálculo en las áreas Comercial, Laboral, Sancionatorio y Honorarios** — hoy solo funciona Civil/
  Familia (`Pendientes.md`, Sprints 2, 3 y 4).
- 🚧 **Indexación por IPC** (ajustar un monto histórico por inflación) — el motor matemático ya existe y
  está probado, pero todavía no está conectado a la pantalla de liquidación (`Pendientes.md`, Sprint 8,
  depende del Sprint 5 de datos históricos).
- 🚧 **Exportar la liquidación a PDF o Word** — hoy el resultado solo se ve en pantalla, no se puede
  guardar como archivo todavía (`Pendientes.md`, Sprint 10).
- 🚧 **Prescripción y caducidad** (saber si una deuda ya "venció" el plazo legal para cobrarla) — no
  existe ese cálculo todavía (`Pendientes.md`, Sprint 7).
- 🚧 **Calendario de días hábiles** para contar plazos legales — hoy el programa no distingue días
  hábiles de festivos (`Pendientes.md`, Sprint 6).
- 🚧 **Botón para volver de una pantalla a otra** sin cerrar el programa — navegación de "regresar" no
  implementada todavía.
- 🚧 **Auditoría** (quién liquidó cada expediente y cuándo) — no existe todavía (`Pendientes.md`, Sprint 9).
- 🚧 **Derecho Tributario, TRM/moneda extranjera, motor de reglas configurable** — dominios nuevos, de
  menor prioridad, ver `Pendientes.md`, Sprints 11, 12 y 13.

---

## 9. Preguntas frecuentes y solución de problemas

**"Al instalar me sale un error de rutas largas / Long Path."**
Ver [sección 2.5](#25-problema-conocido-rutas-largas-en-windows).

**"No sé si el programa quedó bien instalado."**
Corre `.venv\Scripts\python.exe -m pytest -q` (ver [sección 2.6](#26-verificar-que-todo-quedó-instalado-correctamente-opcional-recomendado)).
Si todo termina en "N passed" sin "failed", está bien.

**"Seleccioné Comercial/Laboral/Sancionatorio/Honorarios y no me deja."**
Es esperado — esas áreas todavía no calculan, por eso aparecen deshabilitadas en el formulario. Ver
[sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy).

**"Presioné Liquidar y no pasó nada / me salió un mensaje de error."**
Revisa que el expediente tenga al menos una obligación cargada. Si el mensaje dice "Área no
implementada", es porque el área seleccionada aún no calcula (ver sección 6). Si dice "No se pudo
liquidar" con otro texto, anota el mensaje exacto — puede ser una validación de datos.

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

Para entender la arquitectura del código, empezar por `specifications/` (un archivo por motor interno) y
`docs/superpowers/specs/2026-07-14-mvp-captura-liquidacion-civil-familia-design.md` (diseño del MVP). El
trabajo futuro está en [`Pendientes.md`](../Pendientes.md), organizado en sprints autocontenidos.
