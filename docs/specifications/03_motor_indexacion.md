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
  para fechas futuras -- **el despacho calificó esto de jurídicamente inválido**, ver "Limitaciones
  conocidas" abajo), `get_ibc_usura_for_date`. Desde la corrección del Sprint 8 (2026-08-01) también expone
  `get_ipc_mensual_for_month`/`get_ipc_interpolado_mensual_for_date` (interpolación lineal por días entre
  el índice de cierre del mes anterior y el del mes de la fecha, tal como exige el despacho) — la tabla de
  datos (`_IPC_MENSUAL`) queda deliberadamente vacía hasta conseguir la fuente real del DANE, y **no está
  conectada todavía a `CivilFamiliaStrategy`** (ver "Limitaciones conocidas"). UVT sigue pendiente (sin
  fuente completa, ver Sprint 5).
- `app/services/area_strategy.py`, `CivilFamiliaStrategy._evento_indexacion` (Sprint 8): genera un evento
  `INDEXATION` por cada evento de capital cuando `Obligacion.aplica_indexacion_ipc` es `True` -- uno para
  obligaciones PUNTUAL, uno por cuota para RECURRENTE (tracto sucesivo).
- `LiquidationCore` (`app/engine/liquidation/engine.py`, Sprint 20): recibe `usar_suma_unica: bool` en el
  constructor; cuando es `True`, `_accrue_time_passage` calcula el interes diario sobre
  `principal + indexation` en vez de solo `principal` (y `LiquidationItem.capital_base` refleja esa misma
  base, para que el rubro auditado no diverja del interes reportado). `CivilFamiliaStrategy._resolver_suma_unica`
  (`app/services/area_strategy.py`) deriva el flag desde `Obligacion.interes_sobre_capital_indexado`, por
  obligacion -- desde el Sprint 21 cada obligacion corre en su propio `LiquidationCore`
  (`_liquidar_por_obligacion`), asi que el criterio puede variar libremente entre obligaciones del mismo
  expediente sin ambiguedad.

## Estado
Conectado a `CivilFamiliaStrategy` (Sprint 8). Opt-in por obligacion via el campo
`aplica_indexacion_ipc`, expuesto como checkbox en `ObligacionFormDialog` solo para el area Civil/
Familia.

## Limitaciones conocidas
- **⚠️ Bloqueante, verificado contra la respuesta del despacho (Sprint 8, 2026-08-01):** la interpolacion
  entre indices de **cierre de año** (en vez de entre meses certificados) y el uso del indice del año
  anterior para fechas del año en curso fueron calificados por el despacho como "jurídicamente inválido...
  será objetado por un juez". La corrección exige IPC **mensual** del DANE con interpolación lineal de
  días — la función correcta (`get_ipc_interpolado_mensual_for_date`) ya existe y está probada, pero la
  tabla de datos reales (`_IPC_MENSUAL`) sigue vacía (no se consiguió la fuente completa 1967-2025 del
  DANE) y `CivilFamiliaStrategy._evento_indexacion` **sigue usando la interpolación anual** mientras tanto
  — cambiar de una a otra sin datos reales rompería toda indexación IPC existente. Pregunta de seguimiento
  agregada a `Preguntas-Para-Abogado.md` pidiendo al despacho la fuente/tabla real.
- El interes (Art. 1617 C.C.) se calcula sobre el capital ya indexado ("Suma Única", PDF pag. 21-22) solo
  cuando `Obligacion.interes_sobre_capital_indexado` esta activo (ademas de `aplica_indexacion_ipc`) --
  opt-in explicito por obligacion, Sprint 20. Sin ese flag, el comportamiento es el mismo de antes: interes
  solo sobre el capital historico.
- UVT y UVR siguen sin cargar (fuera de alcance, ver Sprint 5).

Ver `Pendientes.md`, Sprints 8 y 20.
