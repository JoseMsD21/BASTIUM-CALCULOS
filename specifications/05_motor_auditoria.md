# Motor de Auditoria

## Estado actual
`app/engine/audit/` solo contiene un `__init__.py` vacio. No hay ninguna logica de auditoria implementada
todavia (trazabilidad de cambios, log de quien liquido que expediente y cuando, versionado de liquidaciones
recalculadas, etc.).

## Que provee el motor de liquidacion hoy, sin ser "auditoria" formal
`LiquidationResult` (`app/engine/liquidation/result.py`) guarda el historial completo de `LiquidationItem`
por evento, lo que da trazabilidad matematica de como se llego al saldo final — pero no hay una capa que
registre quien ejecuto la liquidacion, cuando, ni permita comparar versiones.

## Pendiente (no implementado aun)
Todo. Ver `Pendientes.md` para cuando priorizarlo (no es parte de ningun sprint fasado explicito;
depende de si el usuario necesita multi-usuario o solo uso individual).
