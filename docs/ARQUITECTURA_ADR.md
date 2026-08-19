# Registro de Decisiones de Arquitectura (ADR) — BASTIUM

> Este documento recoge el **por qué** de las decisiones de arquitectura ya tomadas y vigentes en el
> código. Para el **qué hace cada motor**, ver [docs/specifications/](specifications/); para el detalle de
> implementación sprint a sprint, ver [Pendientes.md](Pendientes.md). Formato por decisión: Contexto →
> Decisión → Alternativas consideradas → Consecuencias.

Cada decisión nueva y relevante para la arquitectura (no un detalle de UI o un bugfix puntual) debe
agregarse aquí como un ADR nuevo — ver la referencia en [CONTRIBUTING.md](../CONTRIBUTING.md).

---

### ADR-001: Aplicación de escritorio offline (PySide6), no web ni SaaS

**Contexto:** BASTIUM procesa datos jurídicos sensibles (expedientes, montos de deuda, datos personales de
las partes) para uso interno de un despacho, no para un público masivo.

**Decisión:** Desktop nativo con PySide6 (Qt), base de datos local SQLite, sin backend remoto ni cuenta de
usuario en la nube.

**Alternativas consideradas:** Aplicación web (requeriría hosting, autenticación multiusuario y manejo de
datos jurídicos sensibles en un servidor remoto — riesgo y costo no justificados para un despacho pequeño
que trabaja con un caso a la vez).

**Consecuencias:** Instalación simple (`pip install` + `python main.py`, o el `.bat` de un clic), datos
nunca salen de la máquina del usuario, pero sin colaboración multiusuario ni acceso remoto — ver
[ADR-005](#adr-005-sin-telemetría-ni-analítica-remota).

---

### ADR-002: SQLite + SQLAlchemy con migraciones idempotentes automáticas, no Alembic

**Contexto:** El esquema de la base de datos cambia con frecuencia (un campo nuevo por sprint, en
promedio), y los usuarios finales no son desarrolladores — no se les puede pedir correr comandos de
migración.

**Decisión:** `main.py` corre `aplicar_migraciones_pendientes()` en cada arranque: compara el esquema real
contra el modelo actual y agrega solo lo que falte (columnas, índices, siembra de
`parametros_legales`), sin tocar datos existentes. Reemplaza los ~9 scripts `scripts/migrate_*.py`
manuales que existían antes (Sprint 51).

**Alternativas consideradas:** Alembic (herramienta estándar de migraciones versionadas para SQLAlchemy) —
descartada por requerir que el usuario corra comandos a mano; los scripts `migrate_*.py` individuales se
conservan en `scripts/` por si hace falta auditar o correr uno de forma aislada.

**Consecuencias:** Actualizar BASTIUM es tan simple como `git pull` + `pip install` + abrir la app.
Contrapartida: la lógica de "qué migrar" vive en código propio (`database/database.py`), no en un
framework externo — cualquier cambio de esquema nuevo debe ser explícitamente idempotente.

---

### ADR-003: AuditLog.resultado_json append-only

**Contexto:** Una liquidación jurídica ejecutada debe poder reconstruirse exactamente después, incluso si
las reglas de cálculo cambian en un sprint futuro (nuevas tasas, campos nuevos como `rate_source`).

**Decisión:** Cada liquidación ejecutada queda registrada en `AuditLog.resultado_json` y esa fila **nunca
se reescribe**. Si falta un campo introducido después (ej. `rate_source`, agregado tras el Sprint 9), la
reconstrucción usa un valor por defecto explícito (`"N/A"`) en vez de fallar o de editar el histórico.

**Alternativas consideradas:** Backfill de campos nuevos sobre filas históricas — descartada explícitamente
(ver README, "Nota sobre auditorías históricas") por romper la garantía de append-only, que es lo que hace
el historial confiable ante una auditoría o un proceso judicial real.

**Consecuencias:** El historial de auditoría es confiable como prueba, pero el código de reconstrucción
debe tolerar campos ausentes de auditorías antiguas indefinidamente.

---

### ADR-004: Parámetros legales versionados en base de datos, no hardcodeados

**Contexto:** Tasas, topes de usura, plazos de prescripción y series históricas (SMLMV, IPC, IBC/Usura,
UVT) cambian por ley cada cierto tiempo, y antes solo un desarrollador podía actualizarlos.

**Decisión:** Todos esos valores viven en la tabla `parametros_legales`, editables desde ⚙ Configuraciones
→ Parámetros por cualquier abogado, con fecha de vigencia y trazabilidad de quién agregó cada valor. Los
valores de fábrica nunca se editan ni se borran, solo se agregan valores nuevos.

**Alternativas consideradas:** Constantes en código (`app/core/`) — es el patrón que existía antes de que
este sistema se generalizara; se mantiene solo para el valor de emergencia (`CIVIL_ANNUAL_RATE`) como
*fallback* silencioso si la tabla de parámetros no tiene una tasa vigente (Sprint 61).

**Consecuencias:** Ningún cambio de tasa legal requiere una nueva versión de la aplicación, pero el motor
de cálculo debe resolver siempre "cuál era el valor vigente en la fecha del evento", no "cuál es el valor
actual" — ver `docs/specifications/02_motor_financiero.md`.

---

### ADR-005: Sin telemetría ni analítica remota

**Contexto:** Los datos que procesa BASTIUM son jurídicos y potencialmente sensibles (montos de deuda,
datos de las partes de un proceso).

**Decisión:** La aplicación no envía datos de uso, errores ni analítica a ningún servicio externo. El único
mecanismo de diagnóstico es el log local en `logs/` — ver
[Plan de mantenimiento y soporte](PLAN_MANTENIMIENTO_SOPORTE.md#métricas-y-monitoreo).

**Alternativas consideradas:** Telemetría de errores tipo Sentry — descartada por el riesgo de que un
reporte de error incluya, sin querer, datos de un expediente real.

**Consecuencias:** No hay visibilidad remota de cómo se usa la app en producción ni de errores no
reportados manualmente por el usuario; el reporte de bugs depende de que el usuario abra un issue (ver
[SECURITY.md](SECURITY.md)) o escriba directamente.
