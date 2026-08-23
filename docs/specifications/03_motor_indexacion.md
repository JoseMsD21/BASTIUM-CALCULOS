# Motor de Indexacion (IPC)

## Que hace
Ajusta un capital historico a valor presente segun la variacion del Indice de Precios al Consumidor (IPC),
usando `Va = Vh * (IPC_final / IPC_inicial)`. Conectado a `CivilFamiliaStrategy` desde el Sprint 8, con
activacion opcional por obligacion; desde el Sprint 80 usa el **indice IPC mensual real del DANE** para
fechas desde 2003-01 en adelante (real hasta el ultimo mes certificado, **estimado** con la formula del
despacho para meses posteriores — Sprint 8, respuesta 22/08/2026), con *fallback* documentado a la
interpolacion anual solo para fechas anteriores a 2003-01 (ver "Estado" y "Limitaciones conocidas" abajo).

## Componentes
- `app/engine/indexation/ipc.py`: `IPCIndexation.calculate(capital, initial_index, final_index)`. Si hay
  deflacion (`final_index <= initial_index`), retorna 0 -- la jurisprudencia no castiga al acreedor por
  deflacion.
- `app/engine/indexation/smmlv.py`: conversion de un valor expresado en SMMLV a pesos.
- `app/engine/indexation/historical_index.py`: series historicas de SMLMV (1984-2026), IPC (1967-2025,
  variacion anual + indice acumulado derivado, MAS el indice mensual real 2003-01/2026-03 desde el Sprint
  80) e IBC/Tasa de Usura (1997-07-01 a 2026-07-31). Expone `get_smlmv_for_year`, `get_ipc_for_date`
  (indice exacto de cierre de año), `get_ipc_interpolado_for_date` (Sprint 8: interpola entre cierres de
  año para cualquier fecha, con fallback al ultimo año disponible para fechas futuras -- **el despacho
  calificó esto de jurídicamente inválido para uso general**, ver "Limitaciones conocidas" abajo; desde el
  Sprint 8, respuesta 22/08/2026, retorna `1.000000` para fechas anteriores al 01/08/1954 — "límite de
  vacío absoluto" — en vez de lanzar `ValueError`), `get_ibc_usura_for_date`. Desde el Sprint 8 tambien
  expone `get_ipc_mensual_for_month`/`get_ipc_interpolado_mensual_for_date` (interpolación lineal por días
  entre el índice de cierre del mes anterior y el del mes de la fecha, tal como exige el despacho) -- **desde
  el Sprint 80, la tabla de datos (`_IPC_MENSUAL`) ya está poblada** con la serie real del DANE (279
  valores, enero de 2003 a marzo de 2026, transcritos programáticamente de
  `docs/Archivos de referencia abogado/_markdown/Historico IPC.md`, base Diciembre-2018 = 100, ya enlazada
  por el DANE en una sola base). Antes de 2003-01, ambas funciones siguen lanzando
  `IPCMensualNoDisponibleError` deliberadamente (hueco histórico real, sin dato ni tasa de la que
  extrapolar). Después del último mes certificado, en cambio, **ya no lanzan la excepción** (Sprint 8,
  respuesta 22/08/2026, "Estimación Futura"): `get_ipc_mensual_for_month` estima el mes con la media
  geométrica de la variación mensual de los últimos 12 meses conocidos, compuesta mes a mes desde el
  último índice real. La UVT, por su parte, ya está cargada
  (`_UVT_POR_ANIO`, tabla histórica 2006-2026) y en producción desde los Sprints 5 y 14, conectada a
  `SancionatorioStrategy` (conversión SMLMV→UVT) y al piso legal de 10 UVT de `TributarioStrategy` — ver
  `docs/specifications/` de esas áreas.
- `app/services/area_strategy.py`, `CivilFamiliaStrategy._evento_indexacion` (Sprint 8; implementación
  propia desde el Sprint 80): genera un evento `INDEXATION` por cada evento de capital cuando
  `Obligacion.aplica_indexacion_ipc` es `True` -- uno para obligaciones PUNTUAL, uno por cuota para
  RECURRENTE (tracto sucesivo). Desde el Sprint 80, este método ya NO es un alias del helper genérico
  `AreaStrategy._evento_indexacion_ipc` (el que Comercial/Honorarios/Sancionatorio/Laboral siguen
  reutilizando tal cual, con la interpolación anual): tiene su propia lógica que intenta primero
  `get_ipc_interpolado_mensual_for_date` para `fecha_causacion` y `fecha_corte`; si CUALQUIERA de las dos
  fechas es ANTERIOR a 2003-01 (`IPCMensualNoDisponibleError`), hace *fallback* COMPLETO a
  `get_ipc_interpolado_for_date` (anual) para AMBAS fechas — nunca mezcla un índice mensual (base
  Dic-2018=100) con uno anual (ancla implícita 1966=100): son series con bases distintas, y mezclarlas
  arruinaría la razón `final_index/initial_index` que usa `IPCIndexation.calculate`. Una fecha posterior al
  último mes certificado ya NO activa este fallback (Sprint 8, respuesta 22/08/2026): se resuelve con el
  mes estimado, no con la interpolación anual.
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
Familia. Desde 2003-01 en adelante usa el índice IPC **mensual** real del DANE (la fórmula que el despacho
exige) — real hasta el último mes certificado, **estimado** con media geométrica para meses posteriores
(Sprint 8, respuesta 22/08/2026, ver "Limitaciones conocidas"); solo antes de 2003-01 cae de vuelta a la
interpolación anual — exactamente el mismo comportamiento que tenían el 100% de las obligaciones antes del
Sprint 80, ahora acotado a ese único hueco histórico real.

## Limitaciones conocidas
- **Resuelto para prácticamente todos los casos (Sprint 80, 2026-08-19; ampliado Sprint 8, respuesta
  22/08/2026):** el despacho calificó la interpolación entre índices de **cierre de año** de
  "jurídicamente inválida... será objetado por un juez" (Sprint 8, respuesta 2026-08-01). El Sprint 80
  consiguió la tabla real de índices IPC **mensuales** del DANE
  (`docs/Archivos de referencia abogado/_markdown/Historico IPC.md`) y pobló `_IPC_MENSUAL` (2003-01 a
  2026-03), conectando `CivilFamiliaStrategy._evento_indexacion` a `get_ipc_interpolado_mensual_for_date`.
  La respuesta del despacho del 22/08/2026 resolvió los dos puntos que quedaban pendientes de ese cierre:
  (1) fechas **posteriores** al último mes certificado ya no caen a la interpolación anual — se estiman con
  la media geométrica de la variación mensual de los últimos 12 meses conocidos ("Estimación Futura",
  fórmula exacta del despacho), aplicada de forma compuesta desde el último índice real; (2) fechas
  anteriores al 01/08/1954 usan índice `1.000000` ("límite de vacío absoluto", también fórmula del
  despacho) en vez de lanzar error. La sugerencia del despacho de reparametrizar a la base
  Diciembre-2008=100 no cambia ningún resultado dentro del rango cargado — `IPCIndexation.calculate` solo
  usa la razón entre dos índices de la misma base, y la serie ya es la que el DANE enlazó en una única base
  continua — así que no se aplicó. **Sigue sin resolver**: el índice mensual real entre el 01/08/1954 y
  2003-01 (el propio despacho da por hecho que esa serie existe sin huecos, pero esta rutina no tiene
  acceso a esos valores en ningún archivo commiteado ni en `docs/datos_publicos_fuente/` — bloqueo de
  infraestructura, no de decisión, ver Sprint 8 en `docs/Pendientes.md`); para ese tramo intermedio
  (1954-08 a 1966, donde tampoco hay variación anual cargada) y para antes de 1967 en general, la
  interpolación anual sigue sin dato y lanza `ValueError` igual que siempre.
- El interes (Art. 1617 C.C.) se calcula sobre el capital ya indexado ("Suma Única", PDF pag. 21-22) solo
  cuando `Obligacion.interes_sobre_capital_indexado` esta activo (ademas de `aplica_indexacion_ipc`) --
  opt-in explicito por obligacion, Sprint 20. Sin ese flag, el comportamiento es el mismo de antes: interes
  solo sobre el capital historico.
- Comercial/Honorarios/Sancionatorio/Laboral (via `AreaStrategy._evento_indexacion_ipc`, no tocado en el
  Sprint 80) siguen usando exclusivamente la interpolación anual, incluso para fechas dentro del rango
  mensual cargado -- solo `CivilFamiliaStrategy` tiene la conexión al índice mensual por ahora (alcance
  acotado del Sprint 80, ver `docs/Pendientes.md`).
- La UVT ya está cargada y conectada en producción (Sprints 5 y 14 — ver arriba, "Componentes"); solo la
  **UVR** sigue sin cargar (fuera de alcance).

Ver `docs/Pendientes.md`, Sprints 8, 20 y 80.
