# Motor de Indexacion (IPC)

## Que hace
Ajusta un capital historico a valor presente segun la variacion del Indice de Precios al Consumidor (IPC),
usando `Va = Vh * (IPC_final / IPC_inicial)`.

## Componentes
- `app/engine/indexation/ipc.py`: `IPCIndexation.calculate(capital, initial_index, final_index)`. Si hay
  deflacion (`final_index <= initial_index`), retorna 0 — la jurisprudencia no castiga al acreedor por
  deflacion.
- `app/engine/indexation/smmlv.py`: conversion de un valor expresado en SMMLV a pesos.
- `app/engine/indexation/historical_index.py`: **vacio**. Deberia contener las series historicas de IPC
  (y SMLMV/UVT/IBC) necesarias para resolver `initial_index`/`final_index` a partir de una fecha.

## Estado en el MVP
`IPCIndexation` esta implementado y probado, pero **no esta conectado a `CivilFamiliaStrategy` en este
sprint**: sin datos historicos de IPC (`historical_index.py` vacio) no hay forma de resolver los indices
inicial/final automaticamente. El expediente Civil/Familia de este MVP calcula solo interes, no indexacion.

## Pendiente (no implementado aun)
- Cargar series historicas de IPC/SMLMV/UVT/IBC en `historical_index.py` (o en una tabla de base de datos
  equivalente a `indicator_historical_rates`).
- Conectar `IPCIndexation` a `CivilFamiliaStrategy` una vez exista la fuente de datos.
- Interpolacion cuando la fecha de corte no coincide con un mes certificado.

Ver `Pendientes.md`.
