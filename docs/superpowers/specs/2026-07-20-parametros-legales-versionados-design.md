# Diseño: Parámetros legales versionados (reemplaza el alcance original del Sprint 13)

**Fecha:** 2026-07-20
**Origen:** Sprint 13 de `Pendientes.md` ("Arquitectura de motor de reglas versionado — EFDJ") fue
evaluado y cerrado sin construir el motor EFDJ completo (ver sección Sprint 13 de `Pendientes.md`). Esta
spec documenta el reemplazo de menor alcance que sí se decidió construir, tras una segunda conversación de
brainstorming donde el usuario aclaró la necesidad real: que un abogado sin conocimientos de Python pueda
modificar tasas, topes y porcentajes legales que cambian con el tiempo, sin depender de un desarrollador
ni de un redeploy.

## Motivación

BASTIUM tiene hoy dos clases de valores numéricos "legales" hardcodeados en Python:

1. **Series de indicadores oficiales** ya versionadas por fecha en `app/engine/indexation/historical_index.py`
   (SMLMV 1984-2026, IPC 1967-2025, IBC/tasa de usura 1997-2026) — construidas en el Sprint 5, pero solo
   editables cambiando código Python.
2. **Topes y porcentajes legales sueltos**, sin ningún concepto de vigencia, hardcodeados en 4 archivos
   distintos:
   - `app/engine/interest/usury_validator.py`: `TOPE_MULTIPLICADOR = 1.5` (multiplicador de usura, Ley
     45/1990 art. 72).
   - `app/services/area_strategy.py` (`HonorariosStrategy`): `TOPE_CUOTA_LITIS_INDIVIDUAL_PCT = 30`,
     `TOPE_HONORARIOS_TOTAL_PCT = 50` (Ley 1123/2007).
   - `app/engine/temporal/prescripcion.py`: `PLAZOS_PRESCRIPCION_MESES` (6 valores por `TipoAccion`) y
     `PLAZOS_CADUCIDAD_MESES_CONOCIDOS` (1 valor).
   - `app/engine/tax/moratory_interest.py`: `PUNTOS_DESCUENTO_ET_635 = 2` (E.T. art. 635).
   - `app/engine/interest/legal_rates.py`: `LegalRates.CIVIL_ANNUAL_RATE = 0.06` (Art. 1617 C.C.).

Ambas clases de valores pueden cambiar (la ley cambia, la jurisprudencia cambia, se publica el dato del
año siguiente) y hoy requieren que un desarrollador edite Python y despliegue de nuevo. El objetivo de
este sprint es que ambas clases vivan en una única tabla versionada, editable desde una pantalla nueva de
la GUI, sin tocar código.

## Decisiones tomadas con el usuario durante el brainstorming

- **Alcance del EFDJ completo (motor de reglas-como-datos con fórmulas y condiciones) queda descartado.**
  Lo que se necesita editar son solo valores/parámetros, no lógica ni condiciones — confirmado
  explícitamente por el usuario.
- **Alcance final: ambas clases de valores** (series de indicadores + topes legales sueltos), no solo una
  — el usuario prefirió una sola tabla y una sola pantalla en vez de resolver esto en dos features
  separadas.
- **Interfaz de edición: pantalla dentro de BASTIUM**, no un archivo YAML/JSON editado a mano — más
  amigable para alguien sin conocimientos técnicos.
- **No depende del motor de auditoría del Sprint 9** (`AuditLog`): esa tabla exige `expediente_id`
  (`NOT NULL`, `ForeignKey("expedientes.id")`), no sirve para un cambio de parámetro que no pertenece a
  ningún expediente. En vez de modificar su esquema, la tabla de parámetros es *append-only* (nunca se
  edita ni se borra una fila) y lleva sus propias columnas de responsabilidad (`usuario`, `motivo`,
  `creado_en`) — la bitácora es la tabla misma.

## Modelo de datos

Nueva tabla `parametros_legales` (`database/models.py`, mismo estilo SQLAlchemy 2.0 declarativo que el
resto del archivo — `Mapped`/`mapped_column`, `Decimal` vía `Numeric`):

| columna         | tipo      | notas                                                              |
|------------------|-----------|---------------------------------------------------------------------|
| `id`             | int PK    |                                                                     |
| `clave`          | str       | de un catálogo cerrado (ver abajo), no texto libre                |
| `valor`          | Numeric   | Decimal                                                             |
| `vigente_desde`  | Date      | fecha desde la cual este valor aplica                              |
| `usuario`        | str       | quién lo agregó (campo libre, BASTIUM no tiene autenticación hoy)  |
| `motivo`         | str, null | por qué se agregó/cambió (opcional pero recomendado en la GUI)     |
| `creado_en`      | DateTime  | timestamp de creación de la fila                                   |
| `vigente_hasta`  | Date, null| solo se usa en modo `TRAMO_CERRADO` (ver Adenda) — `NULL` siempre en los demás modos |

La resolución de "¿cuál es el valor de X vigente en la fecha Y?" toma, por defecto, la fila con `clave = X`
y el `vigente_desde` más reciente que sea `<= Y` (modo `ABIERTO`, ver Adenda de diseño más abajo para los
otros dos modos). Consecuencia directa para el modo por defecto: agregar un valor nuevo (ej. un tope legal
que cambia) es insertar una sola fila — nunca hace falta "cerrar" la fila anterior editando su fecha de
fin, lo que sería una operación más propensa a error para un usuario no técnico. Si se necesita corregir
retroactivamente un valor ya cargado, se agrega una fila nueva con `vigente_desde` en el pasado; la
resolución por fecha la recoge automáticamente para cualquier consulta en ese rango — es el comportamiento
correcto para una corrección genuina, y `usuario`/`motivo`/`creado_en` documentan quién y por qué.

### Adenda de diseño: modos de resolución (agregado durante la planificación técnica)

El diseño original de resolución ("última fila `<= fecha`, sin tope superior") es correcto para topes
legales (una ley no expira sola, es razonable seguir aplicándola hasta que algo la reemplace), pero es
peligroso para las 3 series de indicadores oficiales (SMLMV, IPC, IBC/usura): hoy `historical_index.py`
falla explícitamente fuera de su rango conocido (`ValueError`), a propósito, para no asumir en silencio
que un indicador no publicado sigue igual — comportamiento ya probado en
`tests/engine/test_historical_index.py`. Extrapolar el último valor conocido hacia el futuro produciría un
monto de liquidación incorrecto sin ninguna señal de alerta. Se agrega entonces un modo de resolución por
clave, declarado en código (`CATALOGO_PARAMETROS`, no en la base de datos):

- **`ABIERTO`** (default; las 5 claves de topes/tasas legales sueltas): última fila con
  `vigente_desde <= fecha`, sin tope superior. `vigente_hasta` siempre `NULL`.
- **`ANUAL_EXACTO`** (`SMLMV`, `IPC_INDICE_ACUMULADO`): exige una fila cuyo `vigente_desde` sea el 1 de
  enero del mismo año que `fecha`; si no existe, `ParametroNoDisponibleError`. Reproduce exactamente el
  comportamiento actual de `get_smlmv_for_year`/`get_ipc_for_date`.
- **`TRAMO_CERRADO`** (`IBC_CONSUMO_ORDINARIO`, `USURA_CONSUMO_ORDINARIO`): exige una fila con
  `vigente_desde <= fecha <= vigente_hasta` (`vigente_hasta` obligatorio para estas dos claves, en la
  siembra inicial y en cualquier fila nueva). Reproduce el comportamiento actual de
  `get_ibc_usura_for_date`/`get_tramos_ibc_usura_between`, incluyendo el caso de solape de septiembre de
  2017 (la migración transcribe los tramos ya resueltos de `_TRAMOS_IBC_USURA`, no vuelve a resolver el
  solape).

Las 6 claves de prescripción y la de caducidad usan `ABIERTO` (junto con los 5 topes/tasas legales
sueltos, son 12 claves en total en ese modo) — son plazos fijados por ley, no series de datos oficiales
publicados periódicamente, así que no expiran solas.

Consecuencia en la GUI: `ParametroFormDialog` muestra el campo `vigente_hasta` solo cuando la clave
elegida está en modo `TRAMO_CERRADO` (mismo patrón de visibilidad condicional que ya usa
`ObligacionFormDialog` para mostrar/ocultar campos según el área). Para las demás claves el campo queda
oculto y la fila se guarda con `vigente_hasta=NULL`.

**Catálogo cerrado de claves**: no vive en la base de datos, vive en código (ej.
`app/services/parametro_service.py::CATALOGO_PARAMETROS`), como un diccionario `clave -> (descripcion,
categoria, fuente_legal)`. La GUI ofrece un desplegable con este catálogo — el abogado nunca escribe una
`clave` a mano, solo elige de la lista y aporta valor + fecha + motivo. Agregar una clave nueva al catálogo
(ej. un parámetro legal que hoy no existe) sigue siendo trabajo de desarrollador, porque implica que algún
motor la consuma — lo que deja de requerir código es *cambiar el valor* de una clave que ya existe.

Claves iniciales del catálogo (16 en total: 12 topes/plazos legales en modo `ABIERTO` + 4 claves de
series de indicadores, 2 en modo `ANUAL_EXACTO` y 2 en modo `TRAMO_CERRADO`):
- `USURA_MULTIPLICADOR`, `CUOTA_LITIS_INDIVIDUAL_PCT`, `HONORARIOS_TOTAL_PCT`, `ET635_PUNTOS_DESCUENTO`,
  `CIVIL_ANNUAL_RATE`
- `PRESCRIPCION_EJECUTIVA_MESES`, `PRESCRIPCION_ORDINARIA_MESES`, `PRESCRIPCION_HONORARIOS_MESES`,
  `PRESCRIPCION_CAMBIARIA_DIRECTA_MESES`, `PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES`,
  `PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES`, `CADUCIDAD_IMPUGNACION_INEFICACIA_SOCIETARIA_MESES`
- `SMLMV` (una fila por año, 1984-2026 sembradas), `IPC_INDICE_ACUMULADO` (una fila por año, 1967-2025
  sembradas), `IBC_CONSUMO_ORDINARIO` y `USURA_CONSUMO_ORDINARIO` (una fila por tramo de
  `TramoIBCUsura`, ~260 filas sembradas — reemplazan la lista `_TRAMOS_IBC_USURA`, que hoy junta IBC y
  usura en un mismo registro; se separan en dos claves porque el modelo de parámetro es de un solo `valor`
  por fila).

## Servicio de consulta (`app/services/parametro_service.py`)

- `get_parametro(clave: str, fecha: date) -> Decimal` — resuelve el valor vigente según el
  `modo_resolucion` de la clave (`ABIERTO`/`ANUAL_EXACTO`/`TRAMO_CERRADO`, ver Adenda de diseño); lanza
  `ParametroNoDisponibleError` (nueva excepción en `app/core/exceptions.py`, mismo patrón que
  `UVTNoDisponibleError` del Sprint 4) si no hay ninguna fila aplicable.
- `agregar_valor(clave, valor, vigente_desde, usuario, motivo=None, vigente_hasta=None) -> ParametroLegal`
  — usado por la GUI; valida que `clave` exista en `CATALOGO_PARAMETROS` y que `vigente_hasta` venga
  informado si (y solo si) el modo de la clave es `TRAMO_CERRADO`.
- `historial(clave: str) -> list[ParametroLegal]` — todas las filas de una clave, ordenadas por
  `vigente_desde` descendente; alimenta la vista de historial de la GUI.
- `valor_vigente_hoy(clave: str) -> ParametroLegal | None` — para la tabla resumen de la GUI.
- `ultimo_anio_disponible(clave: str) -> int` — máximo `vigente_desde.year` con datos para una clave en
  modo `ANUAL_EXACTO`; lo usa `get_ipc_interpolado_for_date` para su aproximación ya documentada (Sprint 8,
  decisión 3: fechas posteriores al último año disponible usan el índice de ese último año).

## Motores a re-cablear

Cada uno cambia su constante Python por una llamada a `get_parametro(clave, fecha)`. La mayoría ya recibe
una fecha de negocio reutilizable como fecha de resolución (`prescripcion.py`, `moratory_interest.py`,
`historical_index.py`), así que no cambia su firma pública (patrón "adaptador", igual que el Sprint 10).
Dos excepciones puntuales sí necesitan una `fecha` nueva porque hoy no reciben ninguna: `validar_tasa_usura`
(la obtiene su único llamador, `area_strategy.py`, de `obligacion.fecha_origen`, ya disponible ahí) y
`LegalRates.get_civil_daily_rate` (sin llamadores hoy en todo el motor — confirmado por grep — así que el
cambio no rompe nada existente).

- `usury_validator.py` → `get_parametro("USURA_MULTIPLICADOR", fecha)`, nuevo parámetro `fecha` en
  `validar_tasa_usura`.
- `area_strategy.py::HonorariosStrategy` → `CUOTA_LITIS_INDIVIDUAL_PCT`, `HONORARIOS_TOTAL_PCT`.
- `prescripcion.py` → las 6 claves de prescripción + la de caducidad conocida, indexadas por
  `TipoAccion`/`tipo_proceso` igual que hoy indexan sobre los diccionarios Python.
- `moratory_interest.py` → `ET635_PUNTOS_DESCUENTO`.
- `legal_rates.py::LegalRates.CIVIL_ANNUAL_RATE` → se convierte de atributo de clase a método que consulta
  el parámetro. Verificado por grep: `LegalRates` no tiene ningún llamador hoy en el motor (huérfano, igual
  que `CompoundInterest` antes del Sprint 2) — el cambio de firma no rompe nada existente, pero se hace
  igual para que quede consistente en cuanto alguien lo conecte.
- `historical_index.py::get_smlmv_for_year`, `get_ipc_for_date`, `get_ipc_interpolado_for_date`,
  `get_ibc_usura_for_date`, `get_tramos_ibc_usura_between` — se quedan con la misma firma pública;
  internamente pasan a consultar la tabla en vez de los diccionarios/listas módulo-nivel. **Estos
  diccionarios/listas (`_SMLMV_POR_ANIO`, `_IPC_VARIACION_ANUAL`, `_IPC_INDICE_ACUMULADO`,
  `_TRAMOS_IBC_USURA`) NO se borran** — se quedan en el módulo como la transcripción congelada y
  verificada contra el PDF (con todo su historial de git y comentarios, incluyendo la resolución del
  solape de septiembre de 2017), que es precisamente lo que el script de migración usa como fuente para
  sembrar la tabla. Separación deliberada: el módulo Python es la fuente-de-verdad-como-documento (nunca
  cambia, es auditable), la tabla es la fuente-de-verdad-como-valor-vivo (la consulta el motor, la edita
  el abogado). La misma decisión aplica a las 5 constantes sueltas de `usury_validator.py`,
  `area_strategy.py`, `prescripcion.py`, `moratory_interest.py`, `legal_rates.py`: se quedan como están,
  solo cambian las funciones/métodos que las consumían para llamar a `get_parametro(...)` en su lugar.

## Migración y siembra

Script nuevo `scripts/migrate_parametros_legales.py` (mismo patrón que
`scripts/migrate_aplica_indexacion_ipc.py` del Sprint 8, adaptado: no altera columnas existentes, crea una
tabla nueva vía `init_db()` y la siembra):
1. Llama a `init_db()` para asegurar que la tabla `parametros_legales` exista.
2. Siembra las 12 claves de topes/plazos legales (`ABIERTO`) con su valor actual y `vigente_desde` = fecha
   de vigencia de la norma citada (ej. Ley 1123/2007 para cuota litis → `2007-01-01`; donde el código
   fuente no cite fecha de norma, usar `1900-01-01` como ancla neutra documentada en el script) — los
   valores se **importan directamente de las constantes Python existentes** (`usury_validator.TOPE_MULTIPLICADOR`,
   `HonorariosStrategy.TOPE_CUOTA_LITIS_INDIVIDUAL_PCT`/`TOPE_HONORARIOS_TOTAL_PCT`,
   `prescripcion.PLAZOS_PRESCRIPCION_MESES`/`PLAZOS_CADUCIDAD_MESES_CONOCIDOS`,
   `moratory_interest.PUNTOS_DESCUENTO_ET_635`, `LegalRates.CIVIL_ANNUAL_RATE`), nunca re-transcritos a
   mano — el código fuente ya es la fuente verificada, transcribir de nuevo solo introduciría riesgo de
   error humano.
3. Transcribe las 3 series de `historical_index.py` a filas individuales (`SMLMV` × 43 años,
   `IPC_INDICE_ACUMULADO` × 59 años, `IBC_CONSUMO_ORDINARIO` + `USURA_CONSUMO_ORDINARIO` × ~260 tramos
   cada una, con `vigente_desde`/`vigente_hasta` = `tramo.inicio`/`tramo.fin`) — **también importados
   directamente** de `_SMLMV_POR_ANIO`, `_IPC_INDICE_ACUMULADO`, `_TRAMOS_IBC_USURA` (los tres nombres con
   guión bajo, aceptable en un script de migración de un solo uso), no retranscritos.
4. Idempotente: si la tabla ya tiene filas para una clave, no la vuelve a sembrar (permite correr el
   script más de una vez sin duplicar datos, igual que otros scripts de migración del proyecto).

Debe documentarse en `README.md` (sección "Instalación rápida") igual que se hizo con el script de
migración del Sprint 8, para quien clone el repo con un `bastium.db` anterior a este sprint.

## GUI (`app/views/configuracion.py`, hoy vacío)

- `ParametrosView(QWidget)`: sigue el patrón de `ExpedienteDetallePage` — `QTableWidget` con una fila por
  clave mostrando su valor vigente hoy y desde cuándo, agrupada visualmente por categoría (`Topes
  legales` / `Plazos de prescripción y caducidad` / `Indicadores históricos`).
- Botón "+ Agregar valor nuevo" abre `ParametroFormDialog` (mismo patrón que `ObligacionFormDialog`):
  `QComboBox` con el catálogo cerrado de claves, `QLineEdit`/spin para el valor, `QDateEdit` para
  `vigente_desde`, `QLineEdit` libre y obligatorio para `usuario` (BASTIUM no tiene autenticación, así que
  es un campo de confianza, no validado contra ninguna lista), `QLineEdit` opcional para `motivo`.
- Doble clic en una fila abre el historial completo de esa clave (`historial()`), en una tabla de solo
  lectura ordenada por fecha.
- Entrada nueva "Parámetros" en el menú de navegación de `main_window.py`.

## Manejo de errores

- `agregar_valor` con una `clave` fuera del catálogo → `ValueError` (error de programación, no debería
  ocurrir vía GUI porque el combo solo ofrece claves válidas).
- `get_parametro` sin ninguna fila `vigente_desde <= fecha` → `ParametroNoDisponibleError`, que cada motor
  deja propagar (mismo patrón que `UVTNoDisponibleError`: no hay un valor razonable para inventar, mejor
  fallar explícito que asumir).

## Testing

- Unitarios de `ParametroService`: resolución por fecha con múltiples vigencias, error sin dato, catálogo
  cerrado.
- Migración: spot-check contra los mismos valores puntuales que el Sprint 5 ya verificó contra el PDF
  (SMLMV 2026 = $1.750.905, IPC 2025 = 5.10%, etc.), más los 8 topes/plazos legales contra su cita
  normativa.
- Regresión: cada motor re-cableado (`usury_validator`, `HonorariosStrategy`, `prescripcion`,
  `moratory_interest`, `legal_rates`, `historical_index`) debe dar exactamente el mismo resultado que
  antes de la migración, usando una base de datos SQLite en memoria sembrada con los valores de hoy —
  garantiza que el re-cableado no alteró ningún cálculo.
- Smoke test manual: agregar un valor nuevo desde la GUI, confirmar que aparece en el historial y que una
  liquidación nueva calculada después de esa fecha lo usa.

## Alcance explícitamente excluido

- Autenticación/roles de usuario real (BASTIUM no la tiene hoy; el campo `usuario` es de confianza, no
  validado).
- Migrar UVT histórica (sigue sin existir una tabla completa, mismo bloqueo documentado en el Sprint 5).
- Cualquier forma de editar lógica/condiciones/fórmulas — eso sigue siendo el alcance del EFDJ completo,
  descartado en este sprint.
- Permitir borrar o editar una fila ya creada desde la GUI (append-only estricto; una corrección se hace
  agregando una fila nueva, nunca mutando una existente).
