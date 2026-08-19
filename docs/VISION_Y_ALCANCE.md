# Visión y alcance — BASTIUM

> Documento de referencia rápida. Para el detalle sprint a sprint del alcance actual, ver la sección
> "Estado actual" de [README.md](../README.md); para el alcance jurídico completo previsto, ver
> `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`.

## Objetivo del producto

BASTIUM es una aplicación de escritorio para abogados y despachos jurídicos en Colombia. Reemplaza la
liquidación manual en Excel (capital, intereses, indexación, sanciones) por un motor que aplica las mismas
reglas legales de forma consistente, versionada y auditable, con el mismo rigor matemático y jurídico que
se usaría en un juzgado.

## Público objetivo

- Abogados litigantes y despachos jurídicos en Colombia que liquidan procesos en las áreas Civil/Familia,
  Comercial, Sancionatorio, Honorarios/Litigio, Laboral y Tributario.
- Uso previsto: **interno de un despacho**, un caso (expediente) a la vez — no es un producto multiusuario
  ni multi-despacho (ver [Requisitos no funcionales](REQUISITOS_NO_FUNCIONALES.md)).

## Beneficios de negocio

- **Reduce el error humano de cálculo** en liquidaciones con efectos jurídicos reales (intereses mal
  capitalizados, topes de usura no aplicados, fechas de prescripción pasadas por alto).
- **Trazabilidad legal:** cada liquidación queda en un historial de auditoría append-only (quién, cuándo,
  con qué parámetros), reconstruible en cualquier momento — ver
  [Registro de Decisiones de Arquitectura](ARQUITECTURA_ADR.md#adr-003-auditlogresultado_json-append-only).
- **Parámetros legales versionados sin depender de un desarrollador:** tasas, topes y plazos se agregan
  desde la interfaz, con fecha de vigencia e historial completo.
- **Un solo criterio entre las 6 áreas del derecho**, en vez de una hoja de cálculo distinta (y
  potencialmente inconsistente) por abogado o por caso.

## Alcance actual (lo que entra)

Funcional y en producción hoy (ver el detalle exacto, con artículos y sprints, en la sección "Estado
actual" del [README](../README.md)):

- Liquidación real de las áreas **Civil/Familia, Comercial, Sancionatorio, Honorarios/Litigio, Laboral y
  Tributario**, cada una con sus propias reglas de intereses, topes e imputación de pagos.
- Indexación IPC opcional por obligación, con las reglas de exclusión/coexistencia propias de cada área.
- Historial de auditoría por expediente, con reconstrucción exacta de cualquier liquidación pasada.
- Exportación de resultados a PDF y Word.
- Parámetros legales versionados y editables desde la interfaz (⚙ Configuraciones → Parámetros).
- Alerta de vencimiento (prescripción/caducidad) para 13 tipos de acción/proceso.

## Fuera de alcance (por ahora)

- **Módulo pensional:** existe en `docs/superpowers/specs/2026-07-26-sprint17-modulo-pensional-design.md`
  pero no está conectado a la liquidación real (Sprint 17, ver [Pendientes.md](Pendientes.md)).
- **Costas judiciales por tabla real de rangos:** hoy se ingresan como porcentaje manual; el cálculo
  automático por tabla ya existe en el motor pero no tiene campos propios en pantalla (Sprint 18,
  bloqueado pendiente de confirmación del despacho).
- **IPC mensual real del DANE:** el mecanismo de indexación mensual está construido y probado, pero la
  tabla de datos está vacía a la espera de que el despacho aporte la fuente oficial (Sprint 8, seguimiento
  2 en [Preguntas-Para-Abogado-Abiertas.md](Preguntas-Para-Abogado-Abiertas.md)).
- **Multiusuario, sincronización en la nube, o telemetría/analítica remota:** decisión explícita de
  arquitectura, no una limitación temporal — ver [ADR-005](ARQUITECTURA_ADR.md#adr-005-sin-telemetría-ni-analítica-remota).
- Cualquier otro punto marcado 📋/🔵/🔴 en [Pendientes.md](Pendientes.md), que es la fuente de verdad
  actualizada del backlog completo.

## Criterios de éxito

- Cada área jurídica implementada reproduce, para un caso de prueba real aportado por el despacho, el
  mismo resultado numérico que el despacho calculó manualmente (criterio ya aplicado en la "Auditoría
  cruzada contra las respuestas del despacho" documentada en `Pendientes.md`).
- Ninguna liquidación se exporta o audita sin que su cálculo sea reconstruible después, con los mismos
  parámetros vigentes en el momento en que se ejecutó.
- README y Guía de Usuario nunca quedan desactualizados respecto al código real (regla ya vigente, ver
  "Mantenimiento de esta documentación" en el [README](../README.md)).
