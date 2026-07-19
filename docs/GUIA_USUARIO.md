# Guía de Usuario de BASTIUM

> Esta guía está escrita para que cualquier persona pueda instalar y usar BASTIUM sin conocimientos
> técnicos previos. Si en algún punto algo no funciona como se describe aquí, revisa la sección
> [9. Preguntas frecuentes y solución de problemas](#9-preguntas-frecuentes-y-solución-de-problemas)
> antes que nada.
>
> **Última actualización:** 2026-07-19 — refleja el estado de Civil/Familia, Comercial, Sancionatorio,
> Honorarios/Litigio y exportación de liquidaciones a PDF/Word. Cada vez que se complete un sprint nuevo
> de [`Pendientes.md`](../Pendientes.md), esta guía se actualiza para que nunca quede desactualizada
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
expresadas en SMLMV o UVT) y **Honorarios / Litigio** (cobro de honorarios profesionales y cuota litis,
con costas judiciales opcionales). El área **Laboral** está planeada pero **todavía no calcula** — más
detalle en la [sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy).

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
   - **Área del derecho**: elige **"Civil / Familia"**, **"Comercial"**, **"Sancionatorio"** u
     **"Honorarios / Litigio"** (las cuatro opciones activas hoy; "Laboral" aparece "gris" con la nota
     "Próximamente" porque todavía no calcula, ver [sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy)).
     Si eliges Comercial, Sancionatorio u Honorarios, el formulario de "Agregar obligación" muestra
     campos adicionales — ver [sección 5.7](#57-agregar-una-obligación-comercial),
     [5.9](#59-agregar-una-obligación-sancionatoria) o
     [5.10](#510-agregar-una-obligación-de-honorarios--litigio) según el área.
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

### 5.7. Agregar una obligación comercial

Cuando el expediente tiene **Área del derecho = Comercial**, el formulario de "Agregar obligación"
muestra tres campos adicionales, específicos de esta área:

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
4. Haz clic en **"Guardar"**.

Si alguna tasa pactada (remuneratoria o moratoria) supera 1.5× el IBC que ingresaste, el programa no
deja liquidar el expediente y muestra el mensaje "Tasa usuraria" al hacer clic en "Liquidar" — no al
guardar la obligación (la validación ocurre al calcular, no al capturar el dato).

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
2020-01-01**; para fechas posteriores necesitaría la tabla histórica de UVT, que todavía no está cargada
(ver [sección 7.5](#75-conversión-smlmvuvt-para-multas-sancionatorias)). Si intentas liquidar un hecho
posterior a esa fecha, el programa muestra el mensaje "UVT no disponible" en vez de arriesgar un valor
incorrecto.

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
     aplica.
4. Haz clic en **"Guardar"**.

Al liquidar, el programa valida automáticamente que la cuota litis pactada no exceda el 30% del
"Beneficio obtenido", y que la suma de honorarios fijos + cuota litis no exceda el 50% del mismo
beneficio (ver [sección 7.6](#76-tope-de-cuota-litis-y-honorarios-30--50-del-beneficio-obtenido)). Si
alguno de los dos topes se excede, el programa muestra el mensaje "Cuota litis excede el tope" al hacer
clic en "Liquidar" y no calcula nada. Si diligenciaste el porcentaje de costas, el resultado de la
liquidación trae dos filas de capital separadas: una de honorarios profesionales y otra de costas
procesales.

---

## 6. Áreas del derecho: cuáles funcionan hoy

Al crear un expediente, el campo "Área del derecho" muestra 5 opciones, y **cuatro calculan de verdad
hoy**:

| Área | ¿Funciona? |
|---|---|
| Civil / Familia | ✅ Sí — interés del Art. 1617 C.C. (6% anual o la tasa que se pacte), sobre obligaciones puntuales y recurrentes, con abonos. |
| Comercial | ✅ Sí — Art. 884 C.Co., tasa remuneratoria antes del vencimiento y tasa moratoria después, validación de tope de usura (1.5× el IBC que ingreses). Ver [sección 5.7](#57-agregar-una-obligación-comercial). |
| Laboral | 🚧 No todavía. Planeado en `Pendientes.md`, Sprint 3. |
| Sancionatorio | ✅ Sí, con una limitación — multas en SMLMV o UVT (Ley 1955/2019 art. 49), pero solo para hechos **anteriores al 2020-01-01**: todavía no hay tabla histórica de UVT cargada, y el programa se rehúsa a adivinar el valor para hechos posteriores ("UVT no disponible"). Ver [sección 5.9](#59-agregar-una-obligación-sancionatoria). |
| Honorarios / Litigio | ✅ Sí, con una limitación — honorarios profesionales y cuota litis, validando el tope del 30% (cuota litis sola) y del 50% (total) del beneficio obtenido; las costas judiciales se ingresan como un porcentaje manual porque no existe una tabla estructurada confiable del Consejo Superior de la Judicatura. Ver [sección 5.10](#510-agregar-una-obligación-de-honorarios--litigio). |

Si en algún momento el área Laboral se intenta liquidar antes de que su lógica esté lista, el programa
muestra el mensaje "Área no implementada" en vez de calcular — nunca da un resultado numérico inventado
o incorrecto.

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

### 7.1.1. Tope de usura comercial (1.5x IBC, Ley 45/1990 art. 72)

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente Comercial,
  el campo **"IBC vigente aplicable (%)"** — lo diligencias tú con el IBC certificado por la
  Superfinanciera para la fecha del caso, no hay un valor por defecto.
- **Dónde vive la lógica en el código**: `app/engine/interest/usury_validator.py`, función
  `validar_tasa_usura`. Se invoca automáticamente al liquidar (`ComercialStrategy.liquidar()` en
  `app/services/area_strategy.py`), tanto para la tasa remuneratoria como para la moratoria.
- **Qué pasa si se excede el tope**: el programa lanza el error "Tasa usuraria" y no calcula nada —
  nunca trunca la tasa silenciosamente.

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
  `app/services/area_strategy.py`). Los valores de SMLMV por año están en
  `app/engine/indexation/historical_index.py`.
- **Qué pasa si el hecho es posterior al 2020-01-01**: la ley pasó de expresar estas multas en SMLMV a
  expresarlas en UVT a partir de esa fecha, y todavía no existe una tabla histórica de UVT cargada en el
  programa (ver `Pendientes.md`, Sprint 5). En vez de adivinar un valor, el programa lanza el error "UVT
  no disponible" y no calcula nada.

### 7.6. Tope de cuota litis y honorarios (30% / 50% del beneficio obtenido)

- **Dónde se ve/edita en la app**: en el formulario de "Agregar obligación" de un expediente de
  Honorarios, los campos **"% Cuota litis pactada"** y **"Beneficio obtenido por el cliente"** — ver
  [sección 5.10](#510-agregar-una-obligación-de-honorarios--litigio). No hay valores por defecto.
- **Dónde vive la lógica en el código**: `app/services/area_strategy.py`, clase `HonorariosStrategy`,
  constantes `TOPE_CUOTA_LITIS_INDIVIDUAL_PCT` (30) y `TOPE_HONORARIOS_TOTAL_PCT` (50), validadas en
  `_validar_obligacion_honorarios`. Ambos topes se aplican **simultáneamente** (no son alternativos):
  la cuota litis sola no puede superar el 30% del beneficio obtenido, y la suma de honorarios fijos +
  cuota litis no puede superar el 50% del mismo beneficio.
- **Qué pasa si se excede alguno de los dos topes**: el programa lanza el error "Cuota litis excede el
  tope" al hacer clic en "Liquidar" y no calcula nada — igual que con la tasa usuraria, la validación
  ocurre al calcular, no al capturar el dato.

---

## 8. Funciones pendientes o en desarrollo

Estas funciones están planeadas pero **todavía no existen o no están conectadas**. El detalle técnico
completo de cada una (qué construir, qué documentos consultar, en qué orden) está en
[`Pendientes.md`](../Pendientes.md), organizado en sprints. Aquí un resumen en lenguaje simple:

- 🚧 **Cálculo en el área Laboral** — hoy funcionan Civil/Familia, Comercial, Sancionatorio y
  Honorarios/Litigio (`Pendientes.md`, Sprint 3).
- 🚧 **Tabla histórica de UVT** — el área Sancionatorio solo convierte a pesos los hechos anteriores al
  2020-01-01 (vía SMLMV); los hechos posteriores necesitan una tabla histórica de UVT que todavía no
  está cargada, y por ahora el programa avisa "UVT no disponible" en vez de calcular (`Pendientes.md`,
  Sprint 5).
- 🚧 **Anatocismo comercial condicionado (Art. 886 C.Co.)** — el motor de interés compuesto
  (`CompoundInterest`) existe pero no está conectado; requiere modelar si hubo demanda judicial o
  acuerdo posterior de capitalización, algo que el modelo de datos todavía no captura (`Pendientes.md`,
  Sprint 2, nota de alcance diferido).
- 🚧 **Indexación por IPC** (ajustar un monto histórico por inflación) — el motor matemático ya existe y
  está probado, y desde el Sprint 5 también existen los datos históricos reales de IPC que necesita, pero
  todavía no está conectado a la pantalla de liquidación (`Pendientes.md`, Sprint 8).
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

**"Seleccioné Laboral y no me deja."**
Es esperado — esa área todavía no calcula, por eso aparece deshabilitada en el formulario. Civil/Familia,
Comercial, Sancionatorio y Honorarios/Litigio sí están habilitadas. Ver
[sección 6](#6-áreas-del-derecho-cuáles-funcionan-hoy).

**"Presioné Liquidar y no pasó nada / me salió un mensaje de error."**
Revisa que el expediente tenga al menos una obligación cargada. Si el mensaje dice "Área no
implementada", es porque el área seleccionada aún no calcula (ver sección 6). Si dice "No se pudo
liquidar" con otro texto, anota el mensaje exacto — puede ser una validación de datos.

**"Al liquidar un expediente Sancionatorio me sale 'UVT no disponible'."**
Es esperado si la "Fecha de origen" de la multa es **posterior al 2020-01-01**: desde esa fecha, la ley
expresa estas multas en UVT en vez de SMLMV, y todavía no hay una tabla histórica de UVT cargada en el
programa (ver [sección 7.5](#75-conversión-smlmvuvt-para-multas-sancionatorias) y `Pendientes.md`,
Sprint 5). Por ahora, esta área solo liquida hechos anteriores a esa fecha.

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
