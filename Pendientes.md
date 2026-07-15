# Pendientes de BASTIUM

Backlog fasado de todo lo que quedo fuera del MVP de captura manual (área Civil/Familia). Ver
`docs/superpowers/specs/2026-07-14-mvp-captura-liquidacion-civil-familia-design.md` para el contexto
completo de lo que SI se construyo.

## Sprint 2 — Área Comercial
- Interes moratorio comercial = 1.5x IBC (Art. 884 C.Co.) cuando no se pacta.
- Validacion de tope de usura: lanzar error o truncar si la tasa pactada supera 1.5x IBC (Art. 72 Ley 45
  de 1990).
- Conversion general EA -> diaria ya existe (`app/engine/interest/rate_conversion.py`), reutilizable aqui.
- Regla de incompatibilidad: en Comercial, interes e indexacion IPC no pueden cobrarse simultaneamente.
- Implementar `ComercialStrategy` en `app/services/area_strategy.py` (hoy lanza `AreaNoImplementadaError`).

## Sprint 3 — Área Laboral
- Prestaciones sociales (cesantias, prima, vacaciones) basadas en SMLMV/Auxilio de Transporte vigente al
  momento de la causacion.
- Indemnizacion moratoria Art. 65 CST: un dia de salario por dia de retardo hasta el mes 25 (dia 721);
  desde ahi, interes moratorio a la tasa maxima legal (SFC) sobre salarios y cesantias adeudadas.
- Implementar `LaboralStrategy` (hoy lanza `AreaNoImplementadaError`). Hay un scheduler laboral parcial en
  `app/engine/temporal/schedulers/labor.py` que se puede extender.

## Sprint 4 — Área Sancionatorio y Honorarios
- Conversion SMLMV -> UVT por vigencia historica (Ley 1955 de 2019): si el hecho es anterior al
  2020-01-01 se usa el SMLMV de ese año; si es posterior, la UVT historica de la DIAN.
- Cuota litis: validar que honorarios fijos + cuota litis no superen el 50% del beneficio obtenido.
- Implementar `SancionatorioStrategy` y `HonorariosStrategy` (hoy lanzan `AreaNoImplementadaError`).

## Backlog transversal (sin sprint asignado aun)
- Calendario de dias habiles / festivos y motor de suspension-interrupcion de terminos procesales.
- Motor de prescripcion y caducidad.
- Carga de series historicas de IPC / SMLMV / UVT / IBC (`app/engine/indexation/historical_index.py` esta
  vacio) — bloquea conectar la indexacion IPC a `CivilFamiliaStrategy`.
- Conectar indexacion IPC al area Civil/Familia una vez exista la fuente de datos historica.
- Exportar la liquidacion a PDF/Word desde la GUI (`app/reports/pdf.py` existe pero no esta conectado;
  `app/reports/word.py` esta vacio).
- Resolver el motor de allocation huerfano `app/engine/allocation/allocator.py`
  (`raise NotImplementedError`, modelo de dominio distinto al usado por `LiquidationCore`) — decidir si se
  completa o se elimina.
- Motor de auditoria (`app/engine/audit/`) — hoy no existe ninguna logica (quien liquido que expediente,
  cuando, versionado de recalculos).
- Multiples tasas de interes simultaneas dentro de un mismo expediente (hoy `CivilFamiliaStrategy` usa una
  sola tasa por expediente, tomada de la primera obligacion).
- ~~Validar/enable Windows "Long Paths" en la maquina de desarrollo~~ — resuelto: se habilito
  `LongPathsEnabled=1` en el registro para poder instalar PySide6 dentro de la ruta profunda de OneDrive.
- Confirmar si conviene excluir `.venv/` de la sincronizacion de OneDrive (hoy esta en `.gitignore` pero
  OneDrive igual intenta sincronizar carpetas no versionadas dentro de la carpeta del proyecto).
