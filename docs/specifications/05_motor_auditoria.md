# Motor de Auditoria

## Estado actual

`app/engine/audit/` implementa el motor completo de auditoria:

- `serialization.py` — `serializar_resultado(resultado) -> str` /
  `deserializar_resultado(json_str) -> LiquidationResult`: snapshot JSON
  exacto de un `LiquidationResult`, sin perder precision (Decimal como
  string, fechas ISO).
- `service.py`:
  - `registrar_liquidacion(session, *, expediente_id, area_derecho,
    fecha_corte, resultado, usuario=None, fecha_ejecucion=None) ->
    AuditLog` — crea una fila append-only en `AuditLog` (modelo en
    `database/models.py`) con el snapshot serializado. `usuario` por
    defecto es el usuario del sistema operativo (`getpass.getuser()`),
    porque BASTIUM no tiene sistema de autenticacion propio.
  - `reconstruir_liquidacion(session, audit_log_id) -> LiquidationResult` —
    reconstruye exactamente el resultado de una ejecucion pasada a partir
    del snapshot, sin recalcular (por lo tanto inmune a que las tasas
    hayan cambiado desde entonces).
  - `historial_de_expediente(session, expediente_id) -> list[AuditLog]` —
    liquidaciones ejecutadas para un expediente, mas recientes primero.

## Conexion a la GUI

`ExpedienteDetallePage` (`app/views/expediente_detalle.py`) tiene una
seccion "Historial de auditoria":

- Cada clic en "Liquidar" que termina en un resultado valido llama a
  `registrar_liquidacion` automaticamente.
- La tabla de historial se refresca al abrir el expediente y despues de
  cada liquidacion nueva.
- Doble clic en una fila del historial llama a `reconstruir_liquidacion` y
  muestra ese resultado pasado en la pantalla de Resultado de Liquidacion,
  reutilizando el mismo callback `on_liquidado` que una liquidacion nueva.

## Trazabilidad de tasa/indice por tramo

`LiquidationItem.rate_source` (`app/engine/liquidation/models.py`) se
completa por tramo desde `RateProvider.get_rate_source()` y las
estrategias de area (`app/services/area_strategy.py`), y queda incluido en
el snapshot serializado — asi que la reconstruccion de una liquidacion
historica tambien preserva que tasa/fuente se uso en cada tramo.

## Pendiente

- No hay sistema de usuarios/roles: `usuario` es el usuario del sistema
  operativo, no un login de la aplicacion (decision de alcance, ver
  `docs/Pendientes.md`, Sprint 9).
