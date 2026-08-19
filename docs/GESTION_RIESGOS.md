# Gestión de riesgos — BASTIUM

> Registro de riesgos vigentes. La fuente de verdad del estado de cada sprint es
> [Pendientes.md](Pendientes.md) (estados 🔴/🔵/⚠️/📋/✅ en cada encabezado de sprint); este documento
> agrupa por **tipo de riesgo**, no por sprint, y no repite el detalle técnico de cada uno.

| # | Riesgo | Tipo | Probabilidad | Impacto | Mitigación | Estado |
|---|---|---|---|---|---|---|
| R1 | La indexación IPC de Civil/Familia interpola por cierre de año en vez de mes a mes — el despacho la calificó "jurídicamente inválida". | Legal / cálculo | Alta (se usa hoy en producción si `aplica_indexacion_ipc=True`) | Alto — monto de indexación incorrecto en una liquidación real | El motor mensual correcto ya está construido y probado (`get_ipc_interpolado_mensual_for_date`), bloqueado solo por falta de la tabla real de datos del DANE. Pregunta abierta: "Sprint 8 (seguimiento 2)" en [Preguntas-Para-Abogado-Abiertas.md](Preguntas-Para-Abogado-Abiertas.md). | 🔴 Vigente — Sprint 8 |
| R2 | Vigencia de leyes por año (Ley 100/1993, Ley 797/2003, Ley 2381/2024, transiciones CST/CPT) sin motor propio que resuelva qué norma aplica según la fecha del hecho. | Legal / cálculo | Media (afecta casos que cruzan una transición de ley) | Alto en los casos que aplican | Requiere decisión/confirmación del despacho antes de construir el motor. Pregunta abierta: "Sprint 70" en [Preguntas-Para-Abogado-Abiertas.md](Preguntas-Para-Abogado-Abiertas.md). | 🔵 Bloqueado — Sprint 70 |
| R3 | Módulo pensional (IBL, tasa de reemplazo, densidad de semanas) tiene el motor matemático correcto y probado, pero no está conectado a ninguna estrategia de liquidación ni a la GUI. | Alcance / funcional | Baja (no se usa en producción todavía) | Medio — expectativa del usuario de que "pensional ya funciona" si no se comunica el estado real | Documentado explícitamente como fuera de alcance actual en [Visión y alcance](VISION_Y_ALCANCE.md) y en README. | 📋 Backlog — Sprint 17 |
| R4 | Costas judiciales se ingresan como porcentaje manual; el cálculo automático por tabla de rangos existe en el motor pero no tiene campos propios en pantalla. | Alcance / funcional | Media | Bajo-Medio — cálculo manual más propenso a error humano que el automático | El motor por tabla ya existe (Sprint 18); falta exponerlo en la UI y confirmar con el despacho si reemplaza el porcentaje manual. | 🔵 Bloqueado — Sprint 18 |
| R5 | Pérdida de datos al usar "Restablecer datos de fábrica" (borra expedientes, obligaciones, abonos, eventos y parámetros propios en cascada). | Operacional | Baja (acción explícita, con confirmación) | Alto si ocurre sin backup | Backup automático de `bastium.db` en `backups/` antes de ejecutar, y confirmación textual ("RESTABLECER") obligatoria. Sin papelera ni deshacer más allá de restaurar ese backup a mano. | ✅ Mitigado — ver [Plan de mantenimiento y soporte](PLAN_MANTENIMIENTO_SOPORTE.md) |
| R6 | Auditorías históricas generadas antes del Sprint 9 no tienen el campo `rate_source`; una reconstrucción ingenua podría fallar o mentir sobre el origen de la tasa usada. | Integridad de datos | Baja (ya resuelto en código) | Medio si se reintrodujera | Reconstrucción usa `rate_source="N/A"` explícito para filas antiguas; `AuditLog.resultado_json` es append-only por diseño — ver [ADR-003](ARQUITECTURA_ADR.md#adr-003-auditlogresultado_json-append-only). | ✅ Mitigado |
| R7 | BASTIUM es una herramienta de apoyo, no un sustituto de asesoría legal — un usuario podría confiar en un resultado sin verificarlo contra la norma vigente. | Legal / responsabilidad | Media (depende del usuario final) | Alto (uso indebido en un proceso real) | Aviso legal explícito en README y en cada exportación PDF/Word; disclaimer completo en [SECURITY.md](SECURITY.md). | ✅ Mitigado (comunicacional, no técnico) |
| R8 | Sin telemetría remota: un error en producción en la máquina de un usuario puede pasar sin ser reportado. | Operacional | Media | Medio | Decisión de arquitectura deliberada (ver [ADR-005](ARQUITECTURA_ADR.md#adr-005-sin-telemetría-ni-analítica-remota)); depende de que el usuario reporte manualmente vía [SECURITY.md](SECURITY.md) o issue de GitHub. | Aceptado — riesgo residual conocido |

## Cómo se mantiene este registro

- Cuando un sprint de `Pendientes.md` pasa a 🔴 (bug confirmado) o 🔵 (bloqueado), agregar o actualizar su
  fila aquí.
- Cuando un riesgo se mitiga (el sprint pasa a ✅), actualizar el estado en vez de borrar la fila — el
  historial de qué riesgos existieron es útil para una auditoría futura.
- Este registro no incluye deuda técnica menor ni bugs de UI puntuales sin impacto jurídico o de
  integridad de datos — esos se siguen gestionando directamente como sprints en `Pendientes.md`.
