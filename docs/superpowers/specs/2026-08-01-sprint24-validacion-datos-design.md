# Sprint 24 — Validación de datos: formularios de obligaciones y parámetros legales versionados

**Fecha:** 2026-08-01
**Origen:** `Pendientes.md`, sección "Sprint 24 — Validación de datos: formularios de obligaciones y
parámetros legales versionados" (hallazgos de la auditoría de código 2026-07-21).

## Problema

1. `ObligacionFormDialog.guardar()` (`app/views/obligaciones.py`) solo valida que
   `tasa_efectiva_anual`, `tasa_moratoria_anual`, `ibc_vigente_anual`, `cuota_litis_pactada_pct` y
   `costas_pct_manual` sean `Decimal` parseables — nunca rechaza negativos ni valores absurdamente altos
   (ej. 99999%). `cantidad_smlmv_uvt` no valida signo/positividad. No hay comparación entre
   `fecha_origen`/`fecha_inicio` de la obligación y `fecha_corte_default` del expediente. `concepto` se
   guarda con `.strip()` pero nunca se valida no-vacío (inconsistente con `radicado` en
   `expedientes.py`, que sí lo exige). El único control real hoy es `valor <= 0` rechazado.
2. `parametro_service.agregar_valor()` no valida signo/rango de `valor` para ninguna clave, ni que un
   tramo nuevo `TRAMO_CERRADO` no se solape con uno ya cargado de la misma clave. La validación
   `vigente_hasta >= vigente_desde` solo existe en la GUI (`configuracion.py`), no en el service — cualquier
   otro caller puede insertar datos inconsistentes.

## Alcance

Solo las validaciones de sentido común listadas abajo. **Explícitamente fuera de alcance** (ya lo dice
Pendientes.md): no se propone un catálogo de rangos por campo tipo EFDJ, ni se mueve la validación de
usura (`usury_validator.py`) del momento de liquidar al momento de guardar.

### 1. `app/views/obligaciones.py`

Nuevo helper privado `_validar_rango(valor: Decimal, minimo, maximo, nombre_campo: str) -> None` que
lanza `ValueError` con mensaje `"{nombre_campo} debe estar entre {minimo} y {maximo}."` si está fuera de
rango. Aplicado a:

- `tasa_efectiva_anual`, `tasa_moratoria_anual`, `ibc_vigente_anual`: rango `[0, 1000]` (en unidades de
  porcentaje, ej. `6.00` = 6%). Permite 0 explícitamente porque Sancionatorio/Honorarios ya guardan
  `tasa_efectiva_anual = 0.00` de forma legítima hoy (el campo de tasa está oculto para esas áreas y no se
  usa en el cálculo — ver `test_guarda_obligacion_sancionatoria` / `test_guarda_obligacion_honorarios_*`
  en `tests/views/test_obligaciones.py`, que ya guardan con `campo_tasa = "0.00"`). El tope de 1000% es
  una cota de sentido común para atrapar errores de tecleo, no una regla legal — la regla legal (tope de
  usura) sigue viviendo solo en `usury_validator.py` y corriendo al liquidar.
- `cuota_litis_pactada_pct`, `costas_pct_manual` (si se llenó — sigue siendo opcional en Honorarios):
  rango `[0, 100]`.
- `cantidad_smlmv_uvt`: debe ser estrictamente `> 0` (no solo no-negativo — una sanción de "0 SMLMV" no
  tiene sentido).

Nuevo helper privado `_validar_fecha_no_posterior_a_corte(fecha: date) -> None`: consulta
`Expediente.fecha_corte_default` vía `session.get(Expediente, self._expediente_id)` (convención ya usada
en `expedientes.py`/`expediente_detalle.py`/`liquidaciones.py`, no `.query().get()`) y lanza
`ValueError` si `fecha` es posterior. Se llama con `fecha_origen` (tipo Puntual) o `fecha_inicio` (tipo
Recurrente) en las **3 rutas de guardado** (`guardar()` genérica, `_guardar_laboral()`,
`_guardar_tributario()`) — decisión tomada con el usuario: aplica a todas las áreas por igual, incluyendo
Laboral (donde `campo_fecha_origen` se reutiliza como "fecha de inicio del contrato") y Tributario, no
solo Civil/Familia y Comercial como sugería literalmente el hallazgo.

Nueva validación `concepto` no vacío (mismo patrón que `radicado` en `expedientes.py`): aplicada en las
mismas 3 rutas de guardado, antes de construir el `Obligacion`.

Todas estas validaciones lanzan `ValueError`, que ya captura `_guardar_y_cerrar()` y muestra en un
`QMessageBox` — no se toca ese mecanismo.

### 2. `app/services/parametro_service.py`

En `agregar_valor()`, agregar (en este orden, antes del `session.add`):

- `valor <= 0` → `ValueError` ("El valor debe ser positivo."). Ninguna clave del catálogo actual (tasas,
  SMLMV, IPC, UVT, plazos en meses, puntos de descuento) tiene sentido en cero o negativo — decisión
  tomada con el usuario: rechazar `<= 0` para todas las claves por igual, sin distinción por clave.
- `vigente_hasta is not None and vigente_hasta < vigente_desde` → `ValueError` (mover esta validación
  desde `configuracion.py`, que hoy es el único lugar que la aplica).
- Si `info.modo == ModoResolucion.TRAMO_CERRADO`: consultar filas existentes de la misma `clave` y
  rechazar si `[vigente_desde, vigente_hasta]` se solapa con `[fila.vigente_desde, fila.vigente_hasta]`
  de cualquier fila existente (condición de solapamiento de intervalos cerrados:
  `vigente_desde <= fila.vigente_hasta and vigente_hasta >= fila.vigente_desde`) → `ValueError` con
  mensaje que cite el tramo existente en conflicto (fechas).

`app/views/configuracion.py`: se elimina el chequeo local `if vigente_hasta < vigente_desde: raise
ValueError(...)` (ahora vive en el service; la GUI ya deja burbujear cualquier `ValueError` del service
hacia `_guardar_y_cerrar()` sin cambios).

## Testing

- `tests/views/test_obligaciones.py`: casos nuevos — tasa negativa, tasa > 1000%, porcentaje (cuota
  litis / costas) fuera de `[0,100]`, `cantidad_smlmv_uvt` <= 0, `concepto` vacío, fecha de origen/inicio
  posterior a la fecha de corte (un caso por área representativa: Civil/Familia, Laboral, Tributario).
- `tests/services/test_parametro_service.py`: `valor` negativo y cero rechazados, tramo `TRAMO_CERRADO`
  solapado rechazado, `vigente_hasta < vigente_desde` rechazado directamente en el service (sin pasar por
  la GUI).
- `tests/views/test_configuracion.py`: verificar que el test existente de fecha invertida sigue pasando
  (ahora vía el service, no vía el chequeo local eliminado).
- Suite completa en verde.

## Fuera de alcance (explícito)

- Catálogo de rangos por campo tipo EFDJ.
- Mover la validación de usura de "al liquidar" a "al guardar".
- Validar rangos de `honorarios_fijos_pactados` / `beneficio_obtenido` (no mencionados en el hallazgo
  original; son montos en pesos sin un tope de sentido común obvio, a diferencia de un porcentaje).
