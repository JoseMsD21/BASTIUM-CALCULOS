# Motor de Indexacion (IPC)

## Que hace
Ajusta un capital historico a valor presente segun la variacion del Indice de Precios al Consumidor (IPC),
usando `Va = Vh * (IPC_final / IPC_inicial)`. Conectado a `CivilFamiliaStrategy` desde el Sprint 8, con
activacion opcional por obligacion.

## Componentes
- `app/engine/indexation/ipc.py`: `IPCIndexation.calculate(capital, initial_index, final_index)`. Si hay
  deflacion (`final_index <= initial_index`), retorna 0 -- la jurisprudencia no castiga al acreedor por
  deflacion.
- `app/engine/indexation/smmlv.py`: conversion de un valor expresado en SMMLV a pesos.
- `app/engine/indexation/historical_index.py`: series historicas de SMLMV (1984-2026), IPC (1967-2025,
  variacion anual + indice acumulado derivado) e IBC/Tasa de Usura (1997-07-01 a 2026-07-31). Expone
  `get_smlmv_for_year`, `get_ipc_for_date` (indice exacto de cierre de año), `get_ipc_interpolado_for_date`
  (Sprint 8: interpola entre cierres de año para cualquier fecha, con fallback al ultimo año disponible
  para fechas futuras), `get_ibc_usura_for_date`. UVT sigue pendiente (sin fuente completa).
- `app/services/area_strategy.py`, `CivilFamiliaStrategy._evento_indexacion` (Sprint 8): genera un evento
  `INDEXATION` por cada evento de capital cuando `Obligacion.aplica_indexacion_ipc` es `True` -- uno para
  obligaciones PUNTUAL, uno por cuota para RECURRENTE (tracto sucesivo).

## Estado
Conectado a `CivilFamiliaStrategy` (Sprint 8). Opt-in por obligacion via el campo
`aplica_indexacion_ipc`, expuesto como checkbox en `ObligacionFormDialog` solo para el area Civil/
Familia.

## Limitaciones conocidas (documentadas, no bloqueantes)
- La interpolacion es entre indices de **cierre de año**, no entre meses certificados como en la vida
  real (el DANE certifica mensualmente, pero la fuente transcrita en el Sprint 5 solo trae variacion
  anual) -- ver `get_ipc_interpolado_for_date`.
- Fechas de 2026 en adelante usan el indice de 2025 como aproximacion (la serie no tiene 2026).
- El interes (Art. 1617 C.C.) se sigue calculando solo sobre el capital, no sobre el capital ya
  indexado -- el algoritmo de "Suma Única" del PDF (pag. 22) pide interes sobre el valor indexado; eso
  requeriria cambiar `LiquidationCore`/`BalanceEngine` para las 5 areas, fuera de alcance de este sprint.
- UVT y UVR siguen sin cargar (fuera de alcance, ver Sprint 5).

Ver `Pendientes.md`, Sprint 8.
