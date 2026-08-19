# Mapa de documentación — BASTIUM

Punto de entrada único: qué documento cubre cada aspecto del proyecto, organizado por fase del ciclo de
vida del software. Si buscas "dónde está el documento de X" y no está aquí, probablemente no existe
todavía — créalo siguiendo el patrón conciso + enlaces de los documentos ya listados, no lo dupliques en
otro lugar.

| Fase | Documento | Propósito |
|---|---|---|
| Inicio | [Visión y alcance](VISION_Y_ALCANCE.md) | Objetivo del producto, público, beneficios, qué entra y qué queda fuera |
| Análisis | `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf` | Requisitos funcionales: alcance jurídico completo, todas las áreas y reglas |
| Análisis | [Requisitos no funcionales](REQUISITOS_NO_FUNCIONALES.md) | Cómo debe comportarse el sistema: plataforma, disponibilidad, integridad, seguridad |
| Diseño | [docs/specifications/](specifications/) | Qué hace cada motor interno hoy (uno por motor: temporal, financiero, indexación, pagos, auditoría, reportes, jurídico-familia) |
| Diseño | [Registro de Decisiones de Arquitectura (ADR)](ARQUITECTURA_ADR.md) | Por qué se tomó cada decisión de arquitectura relevante |
| Diseño | [Diseño UI/UX](DISENO_UI_UX.md) | Sistema de diseño visual, navegación, patrones de interacción, con enlaces a los specs de diseño puntuales |
| Planificación | [Pendientes.md](Pendientes.md) | Plan de proyecto / backlog / cronograma: todo el trabajo organizado en sprints autocontenidos, con su propio estado |
| Planificación | [Gestión de riesgos](GESTION_RIESGOS.md) | Riesgos vigentes agrupados por tipo, con mitigación y estado |
| Implementación | [Plan de calidad y pruebas (QA)](PLAN_CALIDAD_PRUEBAS.md) | Estrategia de pruebas, entornos, trazabilidad requisito→sprint→test, criterios de aceptación |
| Implementación | [CONTRIBUTING.md](../CONTRIBUTING.md) | Documentación técnica de desarrollo: entorno, comandos de prueba/lint, convención de commits, cómo proponer un sprint |
| Implementación | `docs/superpowers/plans/` y `docs/superpowers/specs/` | Histórico de ejecución: plan TDD tarea por tarea y diseño de cada sprint (no se edita, es un log) |
| Entrega | [README.md](../README.md) | Instalación, actualización, estructura del proyecto, estado actual funcional |
| Entrega | [Guía de Usuario](GUIA_USUARIO.md) | Manual paso a paso para cualquier persona, incluye FAQ y solución de problemas |
| Transversal | [Plan de mantenimiento y soporte](PLAN_MANTENIMIENTO_SOPORTE.md) | Versiones soportadas, proceso de actualización, backup/restauración, soporte, métricas y monitoreo |
| Transversal | [SECURITY.md](SECURITY.md) | Aviso legal y reporte de vulnerabilidades |
| Transversal | [Preguntas para el abogado — Abiertas](Preguntas-Para-Abogado-Abiertas.md) / [Respondidas](Preguntas-Para-Abogado-Respondidas.md) | Preguntas legales sin resolver / archivo de respuestas del despacho ya aplicadas |
| Transversal | [CHANGELOG.md](../CHANGELOG.md) | Registro de cambios y versiones (Keep a Changelog + SemVer) |
| Transversal | `LICENSE` | Apache License 2.0 |
| Operación | [Plan de mantenimiento y soporte](PLAN_MANTENIMIENTO_SOPORTE.md#métricas-y-monitoreo) | Métricas y monitoreo (documenta explícitamente por qué no existe telemetría) |

## Documentación privada (no se sube a GitHub)

- `docs/local/GUIA_PRESENTACION.md` — guion de presentación/demo comercial, en `.gitignore` deliberadamente.

## Regla de mantenimiento

Cada documento de la tabla de arriba se actualiza en el mismo sprint que cambia lo que describe — no
existe un "sprint de documentación" separado y periódico salvo auditorías puntuales ya documentadas en
[Pendientes.md](Pendientes.md) (Sprints 23-30). Si un documento nuevo no encaja en ninguna fila de esta
tabla, es una señal de que puede ser redundante con uno existente — revisar antes de crearlo.
