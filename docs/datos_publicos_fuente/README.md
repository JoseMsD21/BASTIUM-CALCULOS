# Datos públicos de fuente — extraídos para desbloquear la rutina autónoma en la nube

**Por qué existe esta carpeta:** `docs/Archivos de referencia abogado/` está en `.gitignore`
(contiene plantillas Excel propietarias del despacho y al menos un caso real de cliente
identificado por nombre — nunca debe subirse a git). El problema es que esa carpeta, al no
estar en git, tampoco existe en el sandbox de la nube donde corre la rutina autónoma
(`docs/superpowers/specs/2026-08-19-rutina-autonoma-sprints-design.md`) — así que los Sprints
80, 81 y 82 de `Pendientes.md`, que necesitan esos datos, quedaban permanentemente inalcanzables
para ella.

**Qué contiene esta carpeta y por qué es seguro commitearla:** son series numéricas públicas
oficiales (índices y tasas de interés certificados por DANE, Superintendencia Financiera y Banco
de la República) — el mismo tipo de dato que ya está cargado a mano en
`app/engine/indexation/historical_index.py`. No hay nada propietario ni confidencial en un
número de IPC o una tasa DTF publicada oficialmente. **No se incluyó ninguna plantilla de
cálculo del despacho, ni el caso de cliente, ni el correo electrónico** que también viven en la
carpeta gitignoreada — esos siguen fuera de git.

**Cómo se generaron (extracción programática, no transcripción manual):** el script que las
generó leyó directamente los archivos fuente originales (`Historico IPC.xlsx`,
`Historicocertificacionsuperfinancieratasasdeinteres.xls`, `historicodtf.xlsx`) con
`openpyxl`/`xlrd`, sin interpretar ni redondear nada — son los valores tal cual vienen en la
celda. Fecha de extracción: 2026-08-20.

## Archivos

- **`ipc_mensual_dane_2003_2026.csv`** — `anio, mes, mes_nombre, indice_ipc_base_dic2018_100`.
  279 filas, enero-2003 a marzo-2026 (152.27 en dic-2025, sube a 154.07/155.73/156.94 en
  ene/feb/mar-2026; abril-2026 en adelante todavía no certificado). Fuente: DANE.
  **Corrección sobre lo que dice hoy el Sprint 80:** el propio sprint afirma que la tabla llega
  hasta "Abril-2026 (Abril=149.66)" — extrayendo directamente del `.xlsx` esto es incorrecto:
  149.66 es **abril-2025**, no 2026 (encaja entre marzo-2025=148.68 y mayo-2025=150.14). El
  último mes real disponible es **marzo-2026=156.94**. Quien trabaje el Sprint 80 debe usar este
  CSV como fuente de verdad, no la cita textual del sprint.

- **`tasas_certificadas_superfinanciera_1971_2026.csv`** — `resolucion, fecha, vigencia_desde,
  vigencia_hasta, corriente, bancario_corriente, creditos_ordinarios_libre_asignacion`. 424
  filas, 29-oct-1971 a 30-abr-2026, **verbatim** (sin decidir qué columna mapea a "IBC" en cada
  época — esa decisión de diseño la sigue necesitando el Sprint 81, documentada en
  `Preguntas-Para-Abogado-Abiertas.md`, no la resuelve este CSV). Fuente: Superintendencia
  Financiera de Colombia.

- **`dtf_semanal_banrep_1984_2026.csv`** — `fecha, dtf_90_dias_pct, cdt_180_dias_pct,
  cdt_360_dias_pct`. 2198 filas, 1984-01-20 a 2026-02-27. Fuente: Banco de la República.

## Para quien trabaje los Sprints 80/81/82

Usar estos CSV en vez de `docs/Archivos de referencia abogado/` como fuente de datos — son
accesibles tanto en local como en el sandbox de la rutina autónoma en la nube. La carpeta
original gitignoreada sigue siendo la fuente primaria para auditoría/verificación manual si hace
falta releer el documento original completo (con su formato, resoluciones citadas, etc.), pero
ya no es necesaria para cargar los datos al motor.
