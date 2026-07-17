# Motor de Indexacion (IPC)

## Que hace
Ajusta un capital historico a valor presente segun la variacion del Indice de Precios al Consumidor (IPC),
usando `Va = Vh * (IPC_final / IPC_inicial)`.

## Componentes
- `app/engine/indexation/ipc.py`: `IPCIndexation.calculate(capital, initial_index, final_index)`. Si hay
  deflacion (`final_index <= initial_index`), retorna 0 — la jurisprudencia no castiga al acreedor por
  deflacion.
- `app/engine/indexation/smmlv.py`: conversion de un valor expresado en SMMLV a pesos.
- `app/engine/indexation/historical_index.py` (Sprint 5, implementado): series historicas de SMLMV
  (1984-2026), IPC (1967-2025, variacion anual + indice acumulado derivado) e IBC/Tasa de Usura
  (1997-07-01 a 2026-07-31, linea "Consumo y Ordinario"). Expone `get_smlmv_for_year`,
  `get_ipc_for_date`, `get_ibc_usura_for_date`. UVT sigue pendiente (sin fuente completa). Todavia **no
  esta conectado** a ningun motor de liquidacion -- solo provee los datos, ver mas abajo.

## Estado en el MVP
`IPCIndexation` esta implementado y probado, pero **no esta conectado a `CivilFamiliaStrategy` en este
sprint**: aunque `historical_index.py` ya tiene los datos reales de IPC (Sprint 5), todavia falta el
trabajo de conexion (resolver `initial_index`/`final_index` a partir de una fecha e invocar
`IPCIndexation` desde la estrategia). El expediente Civil/Familia de este MVP calcula solo interes, no
indexacion.

## Pendiente (no implementado aun)
- Conectar `IPCIndexation` a `CivilFamiliaStrategy` usando las series ya cargadas en
  `historical_index.py` (Sprint 8).
- Interpolacion cuando la fecha de corte no coincide con un mes certificado (Sprint 8).
- Cargar la serie historica de UVT en `historical_index.py` una vez se consiga la fuente (sin tabla
  completa en el PDF maestro).

Ver `Pendientes.md`.
