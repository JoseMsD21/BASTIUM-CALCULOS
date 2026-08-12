# Parámetros (área/unidad/presentación), diálogos redimensionables, tooltips de ayuda y CRUD de Obligaciones/Abonos

**Fecha:** 2026-08-11
**Origen:** reporte directo del usuario tras probar la app (capturas de pantalla), en la misma sesión que
cerró los Sprints 52-55. Brainstorming completo con el usuario, incluyendo mockups visuales del
companion de brainstorming, antes de escribir este documento.

## Resumen

6 sprints relacionados, descubiertos en la misma conversación pero con alcance independiente cada uno.
Se agrupan aquí porque comparten contexto de diseño (varios tocan `app/views/configuracion.py` o el
patrón de tooltips), pero cada uno tiene su propio "Código nuevo a crear"/"Definición de Hecho" y se
implementa como sprint separado, en este orden: **56 → 57 → 58 → 59 → 60** (61 queda como placeholder,
sin implementar).

---

## Sprint 56 — Diálogos redimensionables/maximizables

### Problema

Los 7 `QDialog` del proyecto (`AbonoFormDialog`, `ParametroFormDialog`, `HistorialParametroDialog`,
`DescuentoLaboralFormDialog`, `EventoLaboralFormDialog`, `ExpedienteFormDialog`, `ObligacionFormDialog`)
usan los flags por defecto de Qt en Windows, que solo muestran el botón de cerrar — sin minimizar ni
maximizar, y aunque técnicamente se pueden redimensionar arrastrando el borde, no es evidente para el
usuario. Es más notorio en `HistorialParametroDialog`, que puede mostrar cientos de filas (IPC: 683) sin
ninguna forma cómoda de agrandar la ventana. El usuario confirmó que quiere el fix en los 7, no solo en
el que más lo necesita hoy, por consistencia.

### Diseño

Un helper nuevo en `app/views/form_utils.py` (donde ya vive `set_row_visible`, Sprint 39):

```python
def hacer_redimensionable(dialog: QDialog) -> None:
    """Agrega minimizar/maximizar y redimensionado a un QDialog -- Qt no los
    incluye por defecto en Windows. Llamar una vez en __init__, despues de
    super().__init__()."""
    dialog.setWindowFlags(
        dialog.windowFlags()
        | Qt.WindowType.WindowMinimizeButtonHint
        | Qt.WindowType.WindowMaximizeButtonHint
    )
```

Se llama `hacer_redimensionable(self)` en el `__init__` de cada uno de los 7 diálogos, justo después de
`super().__init__(parent)`. No cambia tamaño mínimo/inicial de ninguno — solo agrega la capacidad.

### Testing

Un test por diálogo (o parametrizado sobre los 7) que confirme
`dialog.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint` (y `WindowMinimizeButtonHint`) están
activos tras construir el diálogo.

### Definición de Hecho

- Los 7 `QDialog` tienen los flags de minimizar/maximizar activos, verificado con test.
- Ningún diálogo cambia su tamaño inicial ni su contenido.
- Suite completa en verde.

---

## Sprint 57 — Parámetros: columnas Área y Unidad por fila

### Problema

`ParametroLegal` (`database/models.py`) no tiene ningún campo que indique a qué área(s) del derecho
pertenece un valor, ni su unidad de medida (COP, %, meses, días, veces, índice). El usuario decidió,
tras revisar una tabla de las 39 claves que se investigó leyendo el código real, que ambos datos deben
**guardarse por fila** (no como metadato fijo en Python) y **no ser editables después de creados**.

### Decisiones tomadas con el usuario (no re-derivar)

- **Multi-área**: casillas de verificación en el formulario, guardadas como lista (no como texto con
  guiones) — ver "Modelo de datos" abajo para el formato exacto.
- **Claves sin wiring a producción todavía** (18 de las 39 — ver tabla completa abajo): se les asigna la
  mejor propuesta por nombre/artículo legal igual que al resto; si la inferencia resulta incorrecta se
  corrige cuando esa clave por fin se conecte a una pantalla real (Sprint 61).
- **`CADUCIDAD_ENRIQUECIMIENTO_SIN_CAUSA_MESES`**: se le asignan ambas áreas (Civil/Familia y Comercial),
  por ser doctrina aplicable en las dos sin evidencia de código que incline a una sola.
- **Unidad**: incluida en el mismo alcance que área — también por fila, también capturable en el
  formulario, también inmutable tras crearse.

### Modelo de datos

Dos columnas nuevas en `parametros_legales`:

- `areas_derecho: Mapped[str]` — lista de códigos de `AreaDerecho` (reutilizar el enum ya existente en
  `database/models.py`, no crear uno nuevo) serializada como JSON (`'["CIVIL_FAMILIA", "LABORAL"]'`) en
  un `String`. Se decidió JSON (no un separador de texto) porque el usuario pidió explícitamente que se
  guarde "como lista", pensando en filtros/búsquedas futuras por área.
- `unidad: Mapped[str]` — texto libre corto (`String(30)`), ej. `"COP"`, `"%"`, `"meses"`, `"días"`,
  `"veces"`, `"índice"`.

Ambas `NOT NULL` para filas nuevas; las 683 filas existentes se completan en la migración (ver abajo).
Ninguna reemplaza nada existente — son columnas puramente aditivas, mismo patrón que los 9 scripts
`migrate_*.py` anteriores.

### Tabla de área propuesta por clave (verificada leyendo el código real, revisada con el usuario)

Grupos con área confirmada por código en ejecución (21 claves):

| Clave(s) | Área(s) |
|---|---|
| USURA_MULTIPLICADOR | COMERCIAL |
| HONORARIOS_TOTAL_PCT | HONORARIOS |
| ET635_PUNTOS_DESCUENTO | TRIBUTARIO |
| PRESCRIPCION_EJECUTIVA_MESES | las 6 áreas (default de `UniversalLiquidationService`) |
| SMLMV | CIVIL_FAMILIA, LABORAL, SANCIONATORIO, COMERCIAL, HONORARIOS |
| IPC_INDICE_ACUMULADO | CIVIL_FAMILIA, TRIBUTARIO |
| IBC_CONSUMO_ORDINARIO | TRIBUTARIO, LABORAL |
| USURA_CONSUMO_ORDINARIO | TRIBUTARIO, LABORAL |
| UVT | TRIBUTARIO, SANCIONATORIO |
| EXTEMPORANEIDAD_PCT_MENSUAL, INEXACTITUD_PCT, INEXACTITUD_AGRAVADA_PCT, ERROR_ARITMETICO_PCT | TRIBUTARIO |
| SS_PENSION_PCT, SS_SALUD_PCT, SS_ARL_NIVEL_I/II/III/IV/V_PCT, SS_FSP_TRAMO_1/2/3/4/5/6_PCT (13 claves) | LABORAL |

Grupos sin wiring a producción todavía (18 claves, área por nombre/fuente legal, a confirmar cuando se
conecten en el Sprint 61):

| Clave(s) | Área(s) propuesta(s) |
|---|---|
| CIVIL_ANNUAL_RATE | CIVIL_FAMILIA |
| PRESCRIPCION_ORDINARIA_MESES | CIVIL_FAMILIA |
| PRESCRIPCION_HONORARIOS_MESES | HONORARIOS |
| PRESCRIPCION_CAMBIARIA_DIRECTA_MESES, PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES, PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES | COMERCIAL |
| CADUCIDAD_IMPUGNACION_INEFICACIA_SOCIETARIA_MESES, CADUCIDAD_CHEQUES_MESES, CADUCIDAD_TRANSPORTE_MESES, CADUCIDAD_SEGURO_ORDINARIA_MESES, CADUCIDAD_SEGURO_EXTRAORDINARIA_MESES, CADUCIDAD_IMPUGNACION_ACTAS_SOCIALES_MESES | COMERCIAL |
| CADUCIDAD_ENRIQUECIMIENTO_SIN_CAUSA_MESES | CIVIL_FAMILIA, COMERCIAL |

Unidad por grupo: `_PCT`→"%", `_MESES`→"meses", `SMLMV`/`UVT`→"COP" (valor monetario resultante, no la
unidad abstracta), `IPC_INDICE_ACUMULADO`→"índice", `USURA_MULTIPLICADOR`→"veces",
`ET635_PUNTOS_DESCUENTO`→"puntos", `IBC_CONSUMO_ORDINARIO`/`USURA_CONSUMO_ORDINARIO`→"%".

### Código nuevo a crear

- `database/models.py::ParametroLegal`: agregar `areas_derecho`/`unidad`.
- `scripts/migrate_parametros_legales_area_unidad.py` (script nuevo, mismo patrón idempotente que los
  10 anteriores): agrega las 2 columnas si no existen (`PRAGMA table_info`), y para cada fila sin
  `areas_derecho`/`unidad` asignado, las llena según la tabla de arriba (diccionario clave → (áreas,
  unidad) embebido en el propio script, documentado con la evidencia de código citada arriba).
- `database/database.py::aplicar_migraciones_pendientes()`: agregar la llamada a este script nuevo
  (import diferido, mismo patrón que los otros 11).
- `app/services/parametro_service.py::agregar_valor()`: nuevos parámetros requeridos `areas_derecho:
  list[str]` y `unidad: str`; valida que `areas_derecho` no esté vacío y que cada código sea un
  `AreaDerecho` válido.
- `app/views/configuracion.py::ParametroFormDialog`: casillas de verificación (una por `AreaDerecho`,
  reutilizando `AREAS_DERECHO`/las etiquetas ya usadas en `app/core/constants.py`) preseleccionadas según
  la clave elegida (tabla de arriba, expuesta como diccionario en el propio módulo o importada de donde
  viva la migración) — el usuario puede ajustar antes de guardar; campo de texto para unidad, también
  pre-rellenado y editable antes de guardar. Ambos obligatorios.
- `app/views/configuracion.py::ParametrosView`: 2 columnas nuevas en la tabla ("Área", "Unidad"),
  pobladas desde la fila vigente hoy de cada clave.

### Alcance explícitamente excluido

- No se agrega ninguna forma de editar área/unidad de una fila ya creada (ni doble clic ni ningún otro
  mecanismo) — decisión explícita del usuario.
- No se conecta ninguno de los 18 parámetros sin wiring a una pantalla real (eso es el Sprint 61).

### Definición de Hecho

- Las 683 filas existentes de `parametros_legales` quedan con `areas_derecho`/`unidad` según la tabla de
  arriba, verificado con un test de migración (mismo patrón que `tests/database/test_migrations.py`).
- `ParametroFormDialog` exige área(s) y unidad para guardar un valor nuevo.
- La tabla de Parámetros muestra las 2 columnas nuevas.
- Suite completa en verde.

---

## Sprint 58 — Parámetros: presentación inteligente (vigencia, IPC crudo vs. calculado, historial)

### Problema (3 hallazgos independientes, mismo archivo)

1. La columna "Vigente hasta" aparece vacía para la mayoría de los parámetros. Para los que
   estructuralmente no tienen fecha de fin (`ModoResolucion.ABIERTO`, ej. `USURA_MULTIPLICADOR` vigente
   desde 1990 sin límite) el vacío es correcto. Pero para los que el gobierno fija año a año
   (`ModoResolucion.ANUAL_EXACTO`: `SMLMV`, `IPC_INDICE_ACUMULADO`, `UVT`) el vacío es engañoso — cada
   valor solo rige ese año calendario (ej. el SMLMV de 2025 rigió del 1 de enero al 31 de diciembre de
   2025, decreto nuevo cada año). Confirmado con el usuario mediante ejemplo concreto.
2. `IPC_INDICE_ACUMULADO` es el único parámetro calculado con una fórmula
   (`indice = indice_anterior * (1 + variacion_anual / 100)`,
   `app/engine/indexation/historical_index.py::_construir_indice_ipc_acumulado`) a partir de una tabla
   cruda (`_IPC_VARIACION_ANUAL`, la variación % anual tal como está en el PDF del abogado) que hoy NO se
   siembra en la base de datos — solo el resultado ya calculado. El usuario quiere ver el dato crudo
   junto al calculado, con una explicación de cómo se llegó al segundo. Confirmado que ningún otro de los
   39 parámetros usa una fórmula (los otros 4 "indicadores históricos" — SMLMV, UVT, IBC, USURA — son
   tablas planas transcritas directo).
3. Cuando un parámetro tiene muchas filas históricas (IPC: 683 en total sumando todas las series; SMLMV:
   ~60 años), la tabla principal de Parámetros muestra un solo valor "vigente hoy" — hoy sin ninguna
   forma visible de saber que hay más allá de hacer doble clic (comportamiento no documentado). El
   usuario quiere un enlace/acción explícita.

### Diseño

**Vigencia inteligente** — regla de presentación pura, sin tocar ningún dato guardado ni ningún cálculo
de liquidación:

```python
def vigencia_hasta_mostrar(fila: ParametroLegal, info: InfoParametro) -> str:
    if fila.vigente_hasta is not None:
        return fila.vigente_hasta.isoformat()
    if info.modo == ModoResolucion.ANUAL_EXACTO:
        return f"{date(fila.vigente_desde.year, 12, 31).isoformat()} (calculado)"
    return "Indefinido"
```

Aplica tanto en `ParametrosView.tabla` como en `HistorialParametroDialog.tabla`.

**IPC crudo vs. calculado** — sembrar una clave nueva `IPC_VARIACION_ANUAL` (misma tabla `parametros_legales`,
`ModoResolucion.ANUAL_EXACTO`, unidad "%", derivada de `_IPC_VARIACION_ANUAL` ya existente en
`historical_index.py`) en el mismo script de migración del Sprint 57 o en uno propio (a decidir en la
fase de planificación, según cómo quede de grande el script del 57). En `HistorialParametroDialog`, si la
clave abierta es `IPC_INDICE_ACUMULADO`, agregar una columna extra "Variación anual (%)" que resuelva y
muestre `IPC_VARIACION_ANUAL` para el mismo año de cada fila, con una nota fija visible en el diálogo:
*"Índice = índice del año anterior × (1 + variación anual / 100). Fuente: tabla de variación % anual del
PDF de requerimientos, transcrita en `historical_index.py`."* Mecanismo genérico (no hardcodeado a IPC en
la UI): un diccionario `CLAVE_CRUDA_DE = {"IPC_INDICE_ACUMULADO": "IPC_VARIACION_ANUAL"}` que se puede
extender si en el futuro aparece otro parámetro con fórmula (confirmado con el usuario: por ahora, solo
IPC).

**Enlace "Ver historial"** — en `ParametrosView.tabla`, cuando una clave tiene más de 1 fila en
`parametros_legales`, reemplazar el valor plano de la celda "Valor vigente hoy" por
`"{valor} — Ver N valores históricos →"` (texto con estilo de enlace, o un botón pequeño en la celda,
según lo que sea más simple de implementar con `QTableWidget`), que abre el mismo
`HistorialParametroDialog` que ya abre el doble clic (no se duplica lógica, solo se hace descubrible).

### Definición de Hecho

- SMLMV/IPC/UVT muestran "31 de diciembre de {año} (calculado)" en vez de vacío; el resto de parámetros
  sin fecha de fin real muestran "Indefinido"; los que sí tienen `vigente_hasta` real (`TRAMO_CERRADO`) no
  cambian.
- El historial de IPC muestra la variación % anual cruda junto al índice acumulado, con la fórmula
  explicada en el diálogo.
- Cualquier clave con más de 1 fila tiene una acción visible (no solo doble clic) para ver su historial.
- Ningún cálculo de liquidación cambia de resultado (verificar con la suite completa, especialmente
  `tests/family/`, `tests/engine/` de indexación).
- Suite completa en verde.

---

## Sprint 59 — Tooltips ⓘ de ayuda en los 4 formularios principales

### Problema

`ObligacionFormDialog` (`app/views/obligaciones.py`) tiene un helper privado que agrega un ícono ⓘ con
tooltip y ejemplo junto a un campo (`icono_info=`), pero **solo se usa en 1 de sus ~15 campos** ("Tasa
efectiva anual"). `ExpedienteFormDialog`, `AbonoFormDialog` y `ParametroFormDialog` no tienen ninguno. El
usuario quiere el patrón aplicado de forma consistente en los 4 formularios principales de captura de
datos (Parámetros, Expediente, Obligación, Abono) — no solo en Parámetros como se planteó originalmente.

### Diseño

Extraer el helper de `obligaciones.py` a `app/views/form_utils.py` (mismo módulo del Sprint 56), como
función reutilizable en vez de método privado de una sola clase:

```python
def agregar_ayuda(
    layout: QFormLayout, etiqueta: str, campo: QWidget, *, tooltip: str, ejemplo: str | None = None
) -> QWidget:
    """Agrega una fila a `layout` con `campo` y un icono (i) al lado, con
    tooltip explicativo (mas un ejemplo concreto si se da). Retorna el
    contenedor (fila + icono) para que el caller lo use como el widget de la
    fila si necesita ocultarlo despues con set_row_visible."""
```

Se llama con el mismo criterio en los 4 formularios: cada campo captura un dato jurídico/financiero no
obvio (tasas, fechas de corte, tipos de obligación, unidades) recibe un tooltip con una frase corta +
ejemplo concreto (mismo estilo que el que ya existe: *"Valor por defecto: interés civil legal, Art. 1617
C.C."*). Campos autoexplicativos (ej. "Concepto", un campo de texto libre) no necesitan tooltip — se
decide caso por caso al escribir el contenido, no se fuerza en el 100% de los campos.

**Contenido de los tooltips**: se redacta durante la implementación, citando el mismo tipo de fuente legal
que ya usa el catálogo de parámetros (`CATALOGO_PARAMETROS`, campo `fuente_legal`) cuando el campo
corresponde a una clave versionada, o una explicación práctica corta cuando no.

### Alcance explícitamente excluido

- No se agregan tooltips a pantallas de solo lectura (listados, resultado de liquidación) — solo a los 4
  formularios de captura donde el usuario decide qué escribir.

### Definición de Hecho

- Los 4 formularios usan el helper compartido `agregar_ayuda` (no queda ninguna implementación duplicada
  del ícono ⓘ).
- Cada campo no autoexplicativo de los 4 formularios tiene tooltip con ejemplo.
- Suite completa en verde.

---

## Sprint 60 — Editar/eliminar Obligaciones y Abonos

### Problema

`tabla_obligaciones` (`app/views/expediente_detalle.py`) tiene botón "Editar" por fila (Sprint 44) pero
no "Eliminar". `tabla_abonos` no tiene ni "Editar" ni "Eliminar", solo "Agregar". `tabla_eventos_laborales`
ya tiene ambos (Sprint 44, punto 4) — es el patrón de referencia a replicar.

### Diseño

Mismo patrón exacto que `_eliminar_evento_laboral`/columnas de `tabla_eventos_laborales`:

- `tabla_obligaciones`: agregar columna "Eliminar" (además de la "Editar" ya existente) con botón
  `destructive` por fila. `_eliminar_obligacion(obligacion_id)`: diálogo de confirmación
  (`QMessageBox.question`, mismo texto que eventos: *"¿Eliminar esta obligación? Esta acción no se puede
  deshacer."*, ajustado con una segunda línea si tiene cuotas hijas: *"Esto también eliminará sus N
  cuotas generadas."*), luego `session.delete(obligacion)` + `commit()`. `abonos`/`eventos_laborales`/
  `descuentos_laborales` se eliminan solos vía `cascade="all, delete-orphan"` (ya configurado en el
  modelo, confirmado leyendo `database/models.py:178-186`). **Caso especial**: si la obligación es
  RECURRENTE con reajuste anual y tiene cuotas hijas (`Obligacion.obligacion_padre_id == id`) — esa
  relación NO es un `relationship()` de SQLAlchemy (comentario en el propio modelo, línea ~166, explica
  por qué), así que no se borran solas: `_eliminar_obligacion` debe consultarlas explícitamente
  (`session.query(Obligacion).filter(Obligacion.obligacion_padre_id == obligacion_id)`) y borrarlas en la
  misma transacción antes de borrar el padre. Decisión ya tomada con el usuario: se eliminan juntas, no se
  bloquea la eliminación.
- `tabla_abonos`: agregar columnas "Editar" y "Eliminar" (hoy solo tiene 3 columnas de datos).
  `_editar_abono(abono_id)` abre `AbonoFormDialog` con un `abono_id` opcional (mismo patrón que
  `ObligacionFormDialog`/`EventoLaboralFormDialog` ya soportan edición vía un id opcional en el
  constructor — replicar esa forma en `AbonoFormDialog`, hoy solo soporta creación).
  `_eliminar_abono(abono_id)`: mismo patrón de confirmación + `session.delete` + `commit`.

### Definición de Hecho

- `tabla_obligaciones` tiene botones "Editar" y "Eliminar" por fila; eliminar una obligación con cuotas
  hijas las elimina a todas en la misma operación, verificado con test.
- `tabla_abonos` tiene botones "Editar" y "Eliminar" por fila.
- Suite completa en verde.

---

## Sprint 61 (futuro, sin implementar todavía) — Conectar los parámetros de prescripción/caducidad sin wiring

Placeholder solicitado explícitamente por el usuario. Las 18 claves listadas en el Sprint 57 como "sin
wiring a producción" (12 de prescripción/caducidad no-ejecutiva + `CIVIL_ANNUAL_RATE`, más el uso real de
`IBC_CONSUMO_ORDINARIO`) tienen motores completos y probados (`app/engine/temporal/prescripcion.py`,
`app/engine/interest/legal_rates.py`) pero ningún botón de la app los dispara. Conectarlos requiere
decidir, área por área, desde qué pantalla/flujo se debería invocar cada `TipoAccion`/`TipoProceso` — no
se puede inferir solo del código como se hizo para el Sprint 57 (que era solo etiquetado informativo, sin
riesgo si la inferencia es imperfecta). Queda pendiente de una conversación de alcance dedicada, mismo
patrón que otros gaps grandes de este proyecto (Sprints 13/16/20/41). No se toca código en este sprint.

---

## Notas de implementación transversales

- Los Sprints 57, 58 y 59 tocan `app/views/configuracion.py` — se implementan **secuencialmente**, no en
  paralelo, para evitar conflictos (mismo criterio que ya se usó para los Sprints 52-55).
- El Sprint 60 toca `app/views/expediente_detalle.py` y `app/views/abonos.py`, sin overlap con los
  anteriores.
- El Sprint 56 toca los 7 archivos de vista con diálogos, pero solo agrega una línea (`hacer_redimensionable(self)`)
  a cada `__init__` — bajo riesgo de conflicto incluso si se solapara con otro sprint, pero se mantiene el
  orden secuencial de todas formas.
