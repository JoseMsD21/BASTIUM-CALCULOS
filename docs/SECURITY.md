# Seguridad

## Aviso legal

BASTIUM es una **herramienta de apoyo** para el cálculo de liquidaciones jurídicas (civil, laboral,
comercial, sancionatorio, tributario, pensional) en Colombia. **No sustituye la asesoría de un
abogado colegiado ni garantiza exactitud jurídica.** Los resultados que produce dependen de los datos
que se le ingresen y de los parámetros legales vigentes cargados en el sistema — antes de usar
cualquier resultado en un proceso judicial o administrativo real, quien lo use **debe verificarlo
contra la norma vigente** y contra el criterio de un profesional del derecho. BASTIUM se distribuye
"tal cual", sin garantías de ningún tipo, expresas o implícitas. El proyecto y sus autores no asumen
responsabilidad por ningún daño, pérdida o perjuicio derivado del uso del software o de sus
resultados, incluyendo decisiones tomadas con base en los cálculos que produce.

## Riesgo conocido: `bastium.db` sin cifrado en reposo

`bastium.db` (SQLite) contiene datos reales de clientes del despacho (nombres, radicados, montos) y
**no está cifrado en disco**. Si esa carpeta se sincroniza a un servicio en la nube (ej. OneDrive,
Google Drive, Dropbox) o vive en un equipo compartido, cualquier persona con acceso a esa cuenta o a
ese equipo puede abrir el archivo directamente con cualquier lector de SQLite y leer los datos en texto
plano — incluidos los backups automáticos en `backups/` (ver Sprint 64/69), que son copias exactas del
mismo archivo sin cifrado.

Esto es un riesgo real de protección de datos personales (Ley 1581/2012, Habeas Data) para un despacho
jurídico, no una vulnerabilidad de la aplicación en sí (no hay inyección ni fuga por un input
malicioso) — es una decisión de arquitectura todavía sin resolver entre dos caminos, con costos y
alcance muy distintos:

1. **Cifrado a nivel de aplicación** (ej. SQLCipher): la base queda cifrada sin importar dónde viva el
   archivo, pero exige cambiar el driver de SQLAlchemy y gestionar una clave/contraseña maestra (¿dónde
   se guarda esa clave? ¿la pide la app al abrir? — decisiones de UX y de recuperación ante clave
   perdida que todavía no se han tomado).
2. **Cifrado a nivel de sistema de archivos** (ej. BitLocker/EFS de Windows sobre la carpeta donde vive
   `bastium.db`): no requiere tocar código, pero solo protege el archivo en reposo en ESE equipo — si la
   carpeta se sincroniza a la nube sin cifrado adicional del lado del proveedor, el riesgo original
   persiste igual.

**Mitigación mientras se decide:** no ubicar `bastium.db` (ni la carpeta `backups/`) dentro de una
carpeta sincronizada automáticamente a un servicio en la nube sin cifrado propio del lado del cliente;
si el equipo lo permite, activar cifrado de disco completo (BitLocker en Windows) como mínimo razonable
mientras no exista una decisión sobre cifrado a nivel de aplicación.

## Reportar una vulnerabilidad

Si encuentras una vulnerabilidad de seguridad en el código (por ejemplo: inyección SQL, ejecución de
código arbitrario, exposición de datos sensibles, o cualquier forma de que un input malicioso
comprometa la aplicación o los datos de un expediente), repórtala de forma privada:

1. **No abras un issue público** describiendo la vulnerabilidad — los issues son visibles para
   cualquiera de inmediato.
2. Envía un correo a **jmsd2125@gmail.com** con:
   - Una descripción del problema y su impacto potencial.
   - Pasos para reproducirlo (o una prueba de concepto).
   - La versión de BASTIUM afectada (ver `app/_version.py` o `git describe --tags`).
3. Recibirás una confirmación de recepción en un plazo razonable. Una vez confirmada y corregida la
   vulnerabilidad, se coordinará contigo la divulgación pública (si aplica) y el crédito por el
   hallazgo, si lo deseas.

No reportes vulnerabilidades sobre los cálculos jurídicos en sí por este canal — esos se reportan
como bugs normales, vía issue público con la plantilla de
[reporte de bug](../.github/ISSUE_TEMPLATE/bug_report.md) — salvo que el error de cálculo derive de una
falla de seguridad (ej. datos corruptos por una inyección).

## Versiones soportadas

BASTIUM es software pre-1.0 en desarrollo activo. Mientras no exista una versión 1.0 estable, solo la
última versión etiquetada en la rama `main` recibe correcciones de seguridad.
