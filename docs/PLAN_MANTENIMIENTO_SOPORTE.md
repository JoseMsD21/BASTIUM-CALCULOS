# Plan de mantenimiento y soporte — BASTIUM

## Versiones soportadas y vulnerabilidades

BASTIUM es software pre-1.0 en desarrollo activo. Mientras no exista una versión 1.0 estable, solo la
última versión etiquetada en `main` recibe correcciones. Proceso de reporte de vulnerabilidades (privado,
no como issue público) en [SECURITY.md](SECURITY.md).

## Proceso de actualización

Actualizar una instalación existente es `git pull origin main` + `pip install -r requirements.txt` +
abrir la app — sin pasos manuales de migración, sin borrar `bastium.db` ni perder datos capturados. Detalle
completo en [README.md](../README.md#actualizar-a-una-versión-nueva) y en la
[Guía de Usuario](GUIA_USUARIO.md#27-actualizar-a-una-versión-nueva-si-ya-tenías-bastium-instalado).

Esto es posible porque las migraciones de esquema son automáticas e idempotentes en cada arranque — ver
[ADR-002](ARQUITECTURA_ADR.md#adr-002-sqlite--sqlalchemy-con-migraciones-idempotentes-automáticas-no-alembic).

## Backup y restauración

- **Automático:** antes de ejecutar "⚙ Configuraciones → Restablecer" (que borra expedientes, obligaciones,
  abonos, eventos, descuentos y parámetros propios en cascada), la app crea automáticamente un backup de
  `bastium.db` en `backups/`.
- **Restauración:** no hay un flujo de restauración automatizado en la UI — restaurar significa reemplazar
  `bastium.db` por el archivo de `backups/` correspondiente a mano, con la app cerrada.
- **Recomendación al usuario:** además del backup automático antes de restablecer, se recomienda copiar
  `bastium.db` periódicamente fuera de la carpeta del proyecto (ej. a una carpeta sincronizada con la nube
  del despacho) — la app no lo hace de forma automática ni programada.

## Soporte

- Canal de soporte y reporte de bugs no relacionados con seguridad: issue público con la plantilla de
  [reporte de bug](../.github/ISSUE_TEMPLATE/bug_report.md), o correo a **jmsd2125@gmail.com**.
- No hay SLA formal de tiempo de respuesta — proyecto en desarrollo activo por un mantenedor único.

## Métricas y monitoreo

BASTIUM no envía telemetría, analítica de uso ni reportes de error a ningún servicio externo — decisión
deliberada de arquitectura por la sensibilidad de los datos jurídicos que procesa, ver
[ADR-005](ARQUITECTURA_ADR.md#adr-005-sin-telemetría-ni-analítica-remota).

El único mecanismo de diagnóstico disponible hoy es el log local en `logs/`, generado en la máquina del
propio usuario y nunca transmitido. No existen dashboards, alertas ni KPIs de producción — esto es
apropiado para una app offline de un solo usuario y no se considera una brecha a cerrar, salvo que el
proyecto evolucione hacia un modelo con más de un despacho o instancia (fuera del alcance actual, ver
[Visión y alcance](VISION_Y_ALCANCE.md)).

## Regla de mantenimiento de la documentación

Cada vez que se completa un sprint de [Pendientes.md](Pendientes.md), `README.md` y
[GUIA_USUARIO.md](GUIA_USUARIO.md) deben actualizarse el mismo sprint — regla ya vigente y aplicada en
cada cierre. Este documento y el resto de los documentos de gobierno (`VISION_Y_ALCANCE.md`,
`REQUISITOS_NO_FUNCIONALES.md`, `ARQUITECTURA_ADR.md`, `DISENO_UI_UX.md`, `GESTION_RIESGOS.md`,
`PLAN_CALIDAD_PRUEBAS.md`) siguen la misma regla: se actualizan cuando el sprint que cierran cambia algo
que describen, no en un barrido separado.
