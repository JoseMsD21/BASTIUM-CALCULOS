# MVP: Captura manual de datos y liquidación (Área Civil/Familia)

Fecha: 2026-07-14

## Contexto

BASTIUM ya tiene un motor de cálculo jurídico funcional (`app/engine/**`, `app/services/motor_liquidacion.py`,
`app/services/motor_universal.py`) validado con tests, pero **no existe ninguna forma de que el usuario
capture datos manualmente**: `main.py` es un script de consola con datos de ejemplo hardcodeados; todos los
archivos de `app/views/*.py`, `app/ui/*.py` y `database/{models,database,session}.py` están vacíos (0 bytes).

Este documento define el MVP para cerrar esa brecha: una app de escritorio donde el usuario puede crear un
expediente, registrar sus obligaciones y abonos, y ver la liquidación calculada en pantalla — para el área
**Civil/Familia** únicamente. Las demás áreas del derecho (Comercial, Laboral, Sancionatorio, Honorarios) y
las reglas legales avanzadas (usura, anatocismo, prescripción/caducidad, calendario de días hábiles, datos
históricos IPC/SMLMV/UVT, reportes exportables) quedan fuera de este MVP y se documentan como backlog en
`Pendientes.md`.

## Objetivo

Permitir el flujo completo: **crear expediente → registrar obligaciones y abonos → liquidar → ver resultado**,
usando el motor de cálculo real (`LiquidationCore`), no cálculos ad-hoc.

## Alcance

### Incluido
- Persistencia SQLite vía SQLAlchemy: `Expediente`, `Obligacion`, `Abono`.
- GUI de escritorio en PySide6.
- Selección de área del derecho al crear el expediente (solo "Civil/Familia" habilitada para calcular; el
  resto visible mostrando "Próximamente").
- Dos tipos de obligación: **Puntual** (rubro con fecha y monto) y **Recurrente** (cuota mensual fija).
- Cálculo real vía `CivilFamiliaStrategy`, que usa `LiquidationCore` (interés fijo 6% anual, Art. 1617 C.C.)
  y opcionalmente indexación IPC (compatibles entre sí en esta área).
- Conversión de tasa efectiva anual → diaria: `i_diario = (1+i_EA)^(1/365) - 1`.
- Pantalla de resultado: tabla cronológica + totales (interés acumulado, pagos aplicados, saldo final).
- Completar `specifications/01_motor_temporal.md` … `07_motor_juridico_familia.md` con la documentación real
  de cada motor.
- Crear `Pendientes.md` en la raíz con el backlog fasado por sprint.

### Explícitamente fuera de alcance (va a `Pendientes.md`)
- Reglas Comercial (usura, 1.5×IBC), Laboral (Art. 65 CST, vacaciones), Sancionatorio (SMLMV→UVT), Honorarios
  (cuota litis).
- Calendario de días hábiles, suspensión/interrupción de términos, prescripción/caducidad.
- Carga de series históricas de IPC/SMLMV/UVT/IBC (hoy `historical_index.py` está vacío).
- Exportación a PDF/Word desde la GUI (existe `app/reports/pdf.py` pero no se conecta en este MVP).
- Resolver el motor de allocation huérfano `app/engine/allocation/allocator.py` (queda documentado como
  deuda técnica, no se toca en este MVP).

## Arquitectura

```
GUI (PySide6)  →  Servicios de aplicación  →  Motor de cálculo (ya existente)  →  Persistencia (SQLAlchemy/SQLite)
app/views/*        app/services/area_strategy.py   app/engine/liquidation/*        database/*
```

- La GUI **no calcula nada**. Solo captura datos, los persiste, y al pedir "Liquidar" arma `Event`s
  (causación) y `Payment`s (abonos) a partir de los registros guardados y se los pasa a
  `CivilFamiliaStrategy.liquidar(...)`.
- Las obligaciones **Recurrentes** se expanden primero con `FamilyScheduler.generate()` a eventos mensuales
  (`event_type="INSTALLMENT"` o `"CHILD_SUPPORT"` según categoría); las **Puntuales** se mapean directo a un
  único evento de capital. Ambos flujos convergen en la misma lista de eventos que procesa `LiquidationCore`
  — un solo motor para los dos tipos, sin duplicar lógica.
- Patrón Strategy (completa el esbozo existente en `app/engine/liquidation/registry.py`):
  - `AreaStrategy` (interfaz): `liquidar(obligaciones, abonos, fecha_corte) -> LiquidationResult`.
  - `CivilFamiliaStrategy`: única implementación real en este MVP.
  - `ComercialStrategy`, `LaboralStrategy`, `SancionatorioStrategy`, `HonorariosStrategy`: registradas pero
    lanzan `AreaNoImplementadaError` si se invocan; la GUI nunca las llama porque el selector las bloquea.

## Modelo de datos (SQLAlchemy)

**Expediente**
- `id`, `radicado` (str, referencia interna/judicial), `demandante`, `demandado`, `area_derecho` (enum:
  CIVIL_FAMILIA, COMERCIAL, LABORAL, SANCIONATORIO, HONORARIOS — solo CIVIL_FAMILIA operable), `juzgado`
  (opcional), `fecha_corte_default` (date).

**Obligacion**
- `id`, `expediente_id` (FK), `tipo` (enum: PUNTUAL, RECURRENTE), `concepto` (str), `categoria` (una de las
  reconocidas por `LiquidationCore._capital_concepts`, ej. `CHILD_SUPPORT`, `DANO_EMERGENTE`), `fecha_origen`
  (date — cuándo se originó la obligación), `valor` (Decimal), `tasa_efectiva_anual` (Decimal, %), `pagada`
  (bool), `fecha_pago_total` (date, nullable).
- Solo si `tipo == RECURRENTE`: `dia_pago` (int 1-31), `fecha_inicio` (date), `fecha_fin` (date, nullable →
  si es null, corre hasta la fecha de corte del expediente).

**Abono**
- `id`, `obligacion_id` (FK), `fecha` (date), `monto` (Decimal), `referencia` (str, opcional).

## Flujo de la GUI

1. **Lista de Expedientes** (pantalla inicial) — tabla con radicado/partes/área, botón "Nuevo expediente".
2. **Nuevo expediente** — formulario: radicado, demandante, demandado, área del derecho (selector con 4 de
   5 opciones deshabilitadas + tooltip "Próximamente"), juzgado, fecha de corte por defecto.
3. **Detalle de Expediente** — dos tablas con botón "Agregar":
   - **Obligaciones**: al agregar, primero se elige Puntual o Recurrente, luego el formulario correspondiente.
   - **Abonos**: fecha, monto, referencia, obligación asociada (dropdown).
4. Botón **"Liquidar"** en el detalle del expediente → ejecuta `CivilFamiliaStrategy.liquidar(...)` y navega
   a:
5. **Resultado de Liquidación** — tabla cronológica (una fila por `LiquidationItem`: fecha, concepto, base
   de capital, tasa, interés, indexación, pago, saldo) + panel de totales (`total_interest_accrued()`,
   `total_payments_applied()`, `final_balance()`).

## Manejo de errores

- Validación de formularios en la GUI (campos requeridos, montos positivos, fechas coherentes: `fecha_origen
  <= fecha_corte`, `fecha_inicio <= fecha_fin`) antes de persistir.
- Si se intenta liquidar un expediente de un área no implementada, la acción está deshabilitada en la UI (no
  es un error en tiempo de ejecución que el usuario deba interpretar).
- Errores del motor (ej. `ValueError` de `LiquidationCore._process_event` por tipo de evento no reconocido)
  se capturan en el servicio y se muestran como mensaje claro en la GUI, no como traceback.

## Testing

- Tests unitarios de los nuevos servicios (`CivilFamiliaStrategy`, mapeo Obligacion/Abono → Event/Payment)
  siguiendo el patrón ya usado en `tests/liquidation/` e `tests/integration/`.
- Tests de los modelos SQLAlchemy (creación, relaciones, cascada al borrar expediente).
- No se agregan tests de UI automatizados en este MVP (fuera de alcance); verificación manual del flujo
  completo antes de cerrar el sprint.

## Documentación

- Completar los 7 archivos de `specifications/*.md` (hoy vacíos) con la documentación real de cada motor:
  parámetros, fórmulas, supuestos y ejemplos, reflejando lo efectivamente implementado.
- Crear `Pendientes.md` en la raíz del proyecto con el backlog fasado:
  - **Sprint 2 — Comercial**: interés 1.5×IBC, validación de tope de usura, conversión EA→diaria general.
  - **Sprint 3 — Laboral**: Art. 65 CST (quiebre mes 25/día 721), vacaciones, seguridad social.
  - **Sprint 4 — Sancionatorio/Honorarios**: conversión SMLMV→UVT por vigencia histórica, cuota litis con
    tope 50%.
  - **Backlog transversal**: calendario de días hábiles, motor de prescripción/caducidad, carga de series
    históricas (IPC/SMLMV/UVT/IBC), reportes PDF/Word desde la GUI, resolución del motor de allocation
    huérfano (`app/engine/allocation/allocator.py`).
