# 08 — Catálogo de tipos de proceso (intake del expediente, Sprint 105)

## Propósito

Clasificar cada expediente, en su alta o edición, por **tipo de proceso** según el árbol
entregado por el despacho (respuesta del 16/11/2026, `docs/Preguntas-Para-Abogado-Respondidas.md`,
sección "Sprint 105"). Es un catálogo **informativo**: no altera ningún cálculo, regla ni
estrategia de liquidación.

## Fuente de datos

`app/services/catalogo_tipos_proceso.py` — datos Python inmutables (no texto libre):

- `RAMAS_PROCESO`: las 6 ramas de la respuesta, en su orden, con las áreas de BASTIUM
  (`AreaDerecho`) donde se ofrecen.
- `TIPOS_PROCESO`: los 13 tipos de proceso, cada uno con `codigo` (identificador estable de
  BASTIUM), `rama`, `pregunta_logica` (la "puerta lógica"), `respuesta` (SÍ/NO o la fase
  penal, si la respuesta la explicita), `nombre` y `descripcion`. Todos los textos son copia
  literal de la respuesta; `tests/services/test_catalogo_tipos_proceso.py` fija el árbol.

| Rama del despacho | Áreas de BASTIUM | Tipos de proceso |
|---|---|---|
| Civil y Comercial | Civil / Familia, Comercial | Ejecutivo (SÍ), Declarativo verbal o verbal sumario (NO), Divisorio, Insolvencia |
| Familia | Civil / Familia | Ejecutivo de Alimentos, Adjudicación Judicial de Apoyos |
| Laboral y de Seguridad Social | Laboral | Ordinario Laboral |
| Penal | — (sin área en BASTIUM; catalogada, no ofrecida) | Audiencias Preliminares, Juicio Oral / Preacuerdos, Incidente de Reparación Integral |
| Contencioso Administrativa | — (sin área en BASTIUM; catalogada, no ofrecida) | Medios de Control Ordinarios, Trámite de Pago Oficioso |
| Disciplinaria y Sancionatoria | Sancionatorio | Procedimiento Sancionatorio Contractual (Ley 1474) |

Honorarios / Litigio y Tributario no corresponden a ninguna rama de la respuesta: su combo
queda solo con "(Sin especificar)" y deshabilitado.

## Persistencia

`expedientes.tipo_proceso` — `VARCHAR(60)`, nullable, guarda el `codigo`. Migración idempotente
`scripts/migrate_tipo_proceso_expediente.py`, registrada en
`database.database.aplicar_migraciones_pendientes()`. Los expedientes anteriores quedan en
`NULL` ("Sin especificar") y funcionan igual que antes.

## Interfaz

- **Formulario del expediente** (`ExpedienteFormDialog`): debajo de "Area del derecho", un combo
  "Tipo de proceso" filtrado por el área elegida, con "(Sin especificar)" como primera opción.
  Debajo del combo, una ayuda con la rama, la pregunta orientadora (y su respuesta SÍ/NO o
  fase) y la descripción del tipo elegido; cada opción del combo lleva el mismo texto como
  tooltip. Cambiar de área repuebla el combo y vuelve a "(Sin especificar)".
- **Detalle del expediente** (`ExpedienteDetallePage`): línea "Tipo de proceso: <nombre>
  (<rama>)" con la pregunta y la descripción como tooltip, o "Sin especificar".

Se eligió un combo filtrado con ayuda (y no un asistente de preguntas sí/no encadenadas) porque
la respuesta del despacho no forma un árbol de decisión único: varias puertas son
independientes entre sí (ej. Divisorio e Insolvencia) y solo Civil/Comercial (SÍ/NO) y Penal
(fase) tienen varias salidas para la misma pregunta.

## Pendiente (no definido por el despacho)

La "checklist de obligaciones predefinidas" por subtipo descrita en `Pendientes.md` (Sprint 105)
no está en la respuesta del despacho y **no se implementó**: requiere la lista exacta de
obligaciones (nombre, periodicidad, obligatoria/opcional) y la respuesta a si se crean
automáticamente o quedan sugeridas.
