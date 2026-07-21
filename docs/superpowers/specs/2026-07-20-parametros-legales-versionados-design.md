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

**No hay columna `vigente_hasta`.** La resolución de "¿cuál es el valor de X vigente en la fecha Y?" toma
la fila con `clave = X` y el `vigente_desde` más reciente que sea `<= Y`. Consecuencia directa: agregar un
valor nuevo (ej. SMLMV 2027) es insertar una sola fila — nunca hace falta "cerrar" la fila anterior editando
su fecha de fin, lo que sería una operación más propensa a error para un usuario no técnico. Si se necesita
corregir retroactivamente un valor ya cargado, se agrega una fila nueva con `vigente_desde` en el pasado;
la resolución por fecha la recoge automáticamente para cualquier consulta en ese rango — es el
comportamiento correcto para una corrección genuina, y `usuario`/`motivo`/`creado_en` documentan quién y
por qué.

**Catálogo cerrado de claves**: no vive en la base de datos, vive en código (ej.
`app/services/parametro_service.py::CATALOGO_PARAMETROS`), como un diccionario `clave -> (descripcion,
categoria, fuente_legal)`. La GUI ofrece un desplegable con este catálogo — el abogado nunca escribe una
`clave` a mano, solo elige de la lista y aporta valor + fecha + motivo. Agregar una clave nueva al catálogo
(ej. un parámetro legal que hoy no existe) sigue siendo trabajo de desarrollador, porque implica que algún
motor la consuma — lo que deja de requerir código es *cambiar el valor* de una clave que ya existe.

Claves iniciales del catálogo (11 en total, una por cada constante identificada en la Motivación, más 3
series):
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

- `get_parametro(clave: str, fecha: date) -> Decimal` — resuelve el valor vigente; lanza
  `ParametroNoDisponibleError` (nueva excepción en `app/core/exceptions.py`, mismo patrón que
  `UVTNoDisponibleError` del Sprint 4) si no hay ninguna fila con `vigente_desde <= fecha` para esa clave.
- `agregar_valor(clave, valor, vigente_desde, usuario, motivo=None) -> ParametroLegal` — usado por la GUI;
  valida que `clave` exista en `CATALOGO_PARAMETROS`.
- `historial(clave: str) -> list[ParametroLegal]` — todas las filas de una clave, ordenadas por
  `vigente_desde` descendente; alimenta la vista de historial de la GUI.
- `valor_vigente_hoy(clave: str) -> ParametroLegal | None` — para la tabla resumen de la GUI.

## Motores a re-cablear

Cada uno cambia su constante Python por una llamada a `get_parametro(clave, fecha)`, sin cambiar su firma
pública (mismo patrón "adaptador" que ya usó el Sprint 10 para no romper a los llamadores):

- `usury_validator.py` → `get_parametro("USURA_MULTIPLICADOR", fecha)`.
- `area_strategy.py::HonorariosStrategy` → `CUOTA_LITIS_INDIVIDUAL_PCT`, `HONORARIOS_TOTAL_PCT`.
- `prescripcion.py` → las 6 claves de prescripción + la de caducidad conocida, indexadas por
  `TipoAccion`/`tipo_proceso` igual que hoy indexan sobre los diccionarios Python.
- `moratory_interest.py` → `ET635_PUNTOS_DESCUENTO`.
- `legal_rates.py::LegalRates.CIVIL_ANNUAL_RATE` → se convierte de atributo de clase a método/propiedad
  que consulta el parámetro (rompe compatibilidad con el uso actual como atributo estático — revisar
  todos los usos de `LegalRates.CIVIL_ANNUAL_RATE` al implementar).
- `historical_index.py::get_smlmv_for_year`, `get_ipc_for_date`, `get_ibc_usura_for_date` — se quedan con
  la misma firma pública; internamente pasan a consultar la tabla en vez de los diccionarios/listas
  módulo-nivel `_SMLMV_POR_ANIO`, `_IPC_INDICE_ACUMULADO`, `_TRAMOS_IBC_USURA` (que se eliminan del código
  una vez migrados sus datos).

## Migración y siembra

Script nuevo `scripts/migrate_parametros_legales.py` (mismo patrón que
`scripts/migrate_aplica_indexacion_ipc.py` del Sprint 8):
1. Crea la tabla `parametros_legales` si no existe.
2. Siembra las 8 claves de topes/plazos legales con su valor actual y `vigente_desde` = fecha de vigencia
   de la norma citada (ej. Ley 1123/2007 para cuota litis → `2007-01-01`; donde el código fuente no cite
   fecha de norma, usar `1900-01-01` como ancla neutra documentada en el script).
3. Transcribe las 3 series de `historical_index.py` a filas individuales (`SMLMV` × 43 años,
   `IPC_INDICE_ACUMULADO` × 59 años, `IBC_CONSUMO_ORDINARIO` + `USURA_CONSUMO_ORDINARIO` × ~260 tramos
   cada una).
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
