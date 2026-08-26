# Requisitos no funcionales — BASTIUM

> Los requisitos **funcionales** (qué calcula cada área del derecho, con qué reglas y artículos) viven en
> `REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf` y en [docs/specifications/](specifications/).
> Este documento cubre exclusivamente los requisitos **no funcionales**: cómo debe comportarse el sistema,
> no qué debe calcular.

| Categoría | Requisito | Estado / verificación |
|---|---|---|
| **Plataforma** | Windows con Python 3.14 instalado (el programa se desarrolló y se prueba en Windows — ver [GUIA_USUARIO.md, sección 2.1](GUIA_USUARIO.md#21-qué-necesitas-tener-instalado-antes-de-empezar)). | Sin dependencias nativas fuera de `requirements.txt` (PySide6, SQLAlchemy, reportlab, python-docx, matplotlib, holidays); nada impide correrlo en macOS/Linux en la práctica, pero no está probado ahí. |
| **Instalación** | Sin instalador empaquetado; `pip install -r requirements.txt` + `python main.py`, o doble clic en `Iniciar BASTIUM.bat` en Windows. | Ver [README](../README.md#instalación-rápida). |
| **Disponibilidad** | 100% offline — ninguna función crítica (captura, liquidación, exportación) depende de conexión a internet. | Única excepción conocida: la consulta de TRM en vivo del área Comercial (Superintendencia Financiera), con opción de anulación manual si no hay red. |
| **Persistencia de datos** | Los datos del usuario (expedientes, obligaciones, abonos, parámetros agregados por el usuario) nunca se pierden entre versiones. | Migraciones automáticas idempotentes en cada arranque (Sprint 51) — ver [ADR-002](ARQUITECTURA_ADR.md#adr-002-sqlite--sqlalchemy-con-migraciones-idempotentes-automáticas-no-alembic). |
| **Integridad del historial** | Una liquidación ya auditada no se altera nunca, aunque el motor de cálculo cambie después. | `AuditLog.resultado_json` append-only — ver [ADR-003](ARQUITECTURA_ADR.md#adr-003-auditlogresultado_json-append-only). |
| **Seguridad de datos** | Sin transmisión de datos jurídicos a terceros; sin telemetría. | Ver [ADR-005](ARQUITECTURA_ADR.md#adr-005-sin-telemetría-ni-analítica-remota) y [SECURITY.md](SECURITY.md). |
| **Recuperación ante desastre** | Antes de cualquier operación destructiva masiva (Restablecer datos de fábrica), debe existir un backup automático previo. | Implementado — backup automático en `backups/` antes de restablecer (ver [Plan de mantenimiento y soporte](PLAN_MANTENIMIENTO_SOPORTE.md)). |
| **Consistencia visual** | Modo oscuro/claro persistido entre sesiones; un solo sistema de diseño (color, tipografía, íconos) en toda la GUI. | Sprint 31, ver [Diseño UI/UX](DISENO_UI_UX.md). |
| **Accesibilidad básica** | Los 4 formularios principales de captura tienen ayuda contextual (tooltips ⓘ) en los campos no autoexplicativos. | Sprint 34, ver [Diseño UI/UX](DISENO_UI_UX.md). |
| **Trazabilidad de parámetros** | Todo valor legal (tasa, tope, plazo) debe quedar con fecha de vigencia y autor, consultable con doble clic. | Implementado — ver README, sección "Parámetros legales versionados". |
| **Concurrencia / multiusuario** | Fuera de alcance — un despacho, un expediente a la vez, sin bloqueo optimista ni sincronización entre instalaciones. | Decisión de arquitectura, ver [ADR-001](ARQUITECTURA_ADR.md#adr-001-aplicación-de-escritorio-offline-pyside6-no-web-ni-saas). |
| **Calidad de código** | Lint sin violaciones (`ruff check .`) y suite de pruebas en verde antes de cerrar cualquier sprint. | Verificado en CI (`.github/workflows/ci.yml`) en cada push — ver [Plan de calidad y pruebas](PLAN_CALIDAD_PRUEBAS.md). |
| **Internacionalización** | Fuera de alcance actual — la aplicación y todos sus textos están en español (Colombia), sin soporte multi-idioma previsto. | No hay sprint que lo contemple en [Pendientes.md](Pendientes.md). |

## Notas

- Ninguno de estos requisitos tiene, hoy, un umbral numérico de rendimiento (ej. "arranque < 3s") medido
  formalmente — el proyecto es una aplicación de escritorio de un solo usuario con un volumen de datos por
  despacho que no ha planteado problemas de rendimiento hasta la fecha. Si esto cambia, agregar aquí el
  umbral y el sprint que lo mide.
- Cualquier requisito no funcional nuevo debe agregarse a esta tabla en el mismo sprint que lo introduce,
  igual que exige la regla de mantenimiento de README/Guía de Usuario.
