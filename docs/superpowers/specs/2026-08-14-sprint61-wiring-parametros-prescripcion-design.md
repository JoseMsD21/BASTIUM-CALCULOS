# Sprint 61 — Conectar los parámetros de prescripción/caducidad sin wiring a pantallas reales

**Fecha:** 2026-08-14
**Origen:** `docs/Pendientes.md`, sección "Sprint 61" (hallazgo del Sprint 57, área por parámetro).
Diseño discutido con el usuario en brainstorming el 2026-08-14 antes de codificar — bloqueado
explícitamente en Pendientes.md hasta esta conversación.

## Problema

18 de las 39 claves de `CATALOGO_PARAMETROS` (12 de prescripción/caducidad no-ejecutiva +
`CIVIL_ANNUAL_RATE`, más el uso parcial de `IBC_CONSUMO_ORDINARIO`) tienen motores completos y probados
(`app/engine/temporal/prescripcion.py`, `app/engine/interest/legal_rates.py`) pero ningún botón de la app
los dispara. Hoy solo `TipoAccion.EJECUTIVA` está conectado, vía una alerta hardcodeada en
`app/views/dashboard.py` (~líneas 206-236) que asume ese tipo fijo y toma `obligacion.fecha_origen`, sin
que el usuario elija el tipo de acción/proceso en ningún formulario. El sistema no puede inferir cuál de
los otros 17 aplica a una obligación — depende del tipo de documento/hecho jurídico (un cheque no es lo
mismo que un pagaré o una póliza).

## Decisiones de diseño tomadas con el usuario (2026-08-14)

1. **Campo genérico único**, no 17 decisiones de pantalla independientes: se agrega un solo campo nuevo al
   formulario de `Obligacion`, filtrado por área, en vez de UI a medida por figura legal.
2. **Alertas solo en el Dashboard**: se generaliza el mecanismo de alerta ya existente (hoy solo mira
   EJECUTIVA); no se agrega indicador nuevo en `ExpedienteDetallePage`.
3. **`CIVIL_ANNUAL_RATE` como fallback automático silencioso**: sin campo nuevo en la UI, se activa cuando
   `tasa_efectiva_anual == 0` en una obligación de Civil/Familia.

## Alcance

### 1. `database/models.py` + migración — campo nuevo en `Obligacion`

- Columna nueva `tipo_accion_proceso: str | None` (nullable, sin default — obligación sin este campo
  simplemente no se alerta, igual que hoy). Se guarda el `value` string de `TipoAccion` (ej.
  `"ordinaria"`) o la clave de caducidad tal cual (ej. `"CHEQUES"`) — ambos catálogos son distinguibles
  entre sí sin colisión (valores de `TipoAccion` son minúsculas, claves de caducidad son mayúsculas).
- Script `scripts/migrate_tipo_accion_proceso.py` (mismo patrón que
  `scripts/migrate_reajuste_anual_familia.py`: `ALTER TABLE obligaciones ADD COLUMN`, idempotente,
  registrado en `aplicar_migraciones_pendientes` de `database/database.py`).

### 2. `app/services/areas_parametro.py` — catálogo unificado por área

- Nueva función/diccionario que, para un `AreaDerecho` dado, devuelve la lista combinada de opciones
  visibles: los `TipoAccion` cuya `CLAVE_POR_TIPO_ACCION` esté en `AREA_UNIDAD_POR_CLAVE` para esa área, más
  las claves de `PLAZOS_CADUCIDAD_MESES_CONOCIDOS` cuya clave `CADUCIDAD_{clave}_MESES` esté en
  `AREA_UNIDAD_POR_CLAVE` para esa área. Reutiliza el mapeo ya aprobado del Sprint 57, no se reinventa.
- `EJECUTIVA` se incluye en la lista de Civil/Familia (y las demás áreas donde
  `PRESCRIPCION_EJECUTIVA_MESES` ya aplica) para que el campo nuevo también pueda representar el caso ya
  wireado hoy de forma implícita — unifica el mecanismo sin dejar un caso especial fuera.

### 3. `app/views/obligaciones.py` — dropdown nuevo en `ObligacionFormDialog`

- Combo "Tipo de acción/proceso (prescripción/caducidad)", opcional, poblado con la lista del punto 2
  según el área del expediente actual (mismo patrón de filtrado por área que ya usa `campo_categoria` u
  otros combos condicionados por área en este formulario). Guarda/lee `tipo_accion_proceso` en las mismas
  3 rutas de guardado (genérica, Laboral, Tributario) que ya tocó el Sprint 24 para otras validaciones.

### 4. `app/views/dashboard.py` — generalizar la alerta

- Reemplazar el bloque hardcodeado a `TipoAccion.EJECUTIVA` (~líneas 206-236) por un bucle que, para cada
  obligación con `tipo_accion_proceso` no nulo: si el valor coincide con un `TipoAccion.value`, llama
  `calcular_prescripcion` (con `precargar_parametro(CLAVE_POR_TIPO_ACCION[...])` igual que hoy); si
  coincide con una clave de `PLAZOS_CADUCIDAD_MESES_CONOCIDOS`, llama `calcular_caducidad` (con
  `precargar_parametro(f"CADUCIDAD_{clave}_MESES")`). Mismo widget/formato de alerta visual ya existente,
  sin UI nueva.

### 5. `app/services/area_strategy.py` — `CIVIL_ANNUAL_RATE`

- `CivilFamiliaStrategy._construir_rate_provider_obligacion` (`area_strategy.py:429-440`): si
  `obligacion.tasa_efectiva_anual == Decimal("0.00")`, resolver la tasa con
  `get_parametro("CIVIL_ANNUAL_RATE", fecha_corte)` en vez de usar `0` directo. Sin cambios de UI — el
  campo de tasa (`campo_tasa`, default `"6.00"`) ya permite guardar 0 explícitamente hoy (mismo patrón
  legítimo que Sancionatorio/Honorarios, confirmado en el Sprint 24).

### 6. `app/services/areas_parametro.py` — quitar el aviso de "sin wiring" para las 13 claves ahora conectadas

- El comentario de módulo y el bloque "Grupo sin wiring a produccion todavia" se actualizan para reflejar
  que ya están conectadas (documentación interna, no afecta comportamiento).

## Manejo de errores

- Obligación sin `tipo_accion_proceso`: comportamiento idéntico a hoy (no se alertan prescripción/
  caducidad ajenas a EJECUTIVA) — no es un error, es el valor por defecto (nulo).
- Parámetro sin valor vigente cargado para la clave resuelta (ej. usuario no cargó
  `PRESCRIPCION_ORDINARIA_MESES` en Parámetros): mismo comportamiento ya existente para EJECUTIVA hoy —
  `precargar_parametro`/`get_parametro` ya manejan la ausencia (no se agrega manejo nuevo).

## Pruebas

- Unitarias: `areas_parametro` devuelve la lista correcta de `tipo_accion_proceso` disponibles por área
  (ej. Comercial incluye las 3 cambiarias + 7 caducidades propias, Civil/Familia incluye ORDINARIA +
  EJECUTIVA, sin mezclar claves de otras áreas).
- Unitarias: guardar una obligación con cada uno de los 12 valores nuevos de `tipo_accion_proceso`
  persiste y recupera el campo correctamente en las 3 rutas de guardado.
- Unitarias: `CivilFamiliaStrategy` con `tasa_efectiva_anual = 0` resuelve la tasa diaria a partir de
  `CIVIL_ANNUAL_RATE`; con `tasa_efectiva_anual > 0` sigue usando el valor propio de la obligación (cero
  regresión).
- Integración: Dashboard genera alerta correcta para al menos un caso de prescripción (ej. ORDINARIA) y
  uno de caducidad (ej. CHEQUES) además del caso EJECUTIVA ya existente, verificando que no se rompe la
  alerta EJECUTIVA actual.
- Migración: `aplicar_migraciones_pendientes` sobre una base anterior a este sprint agrega la columna sin
  fallar y sin duplicar si se corre dos veces (idempotente, mismo criterio que las migraciones existentes).
- Suite completa en verde, `ruff check .` limpio.

## Definición de Hecho

- Las 12 claves de prescripción/caducidad (más `CIVIL_ANNUAL_RATE`) dejan de estar "sin wiring": son
  alcanzables desde una pantalla real (`ObligacionFormDialog` para el tipo, Dashboard para la alerta,
  resolución automática de tasa para `CIVIL_ANNUAL_RATE`).
- Ninguna obligación existente cambia de comportamiento sin que el usuario elija explícitamente un
  `tipo_accion_proceso` nuevo (para prescripción/caducidad) o dejando la tasa en 0 (para
  `CIVIL_ANNUAL_RATE`) — regresión cero por defecto.
- Suite completa en verde.
