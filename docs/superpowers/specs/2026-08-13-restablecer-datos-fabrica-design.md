# Restablecer datos de fábrica — diseño

## Contexto

El usuario quiere una forma de volver la app al estado "recién instalado"
desde la propia UI, sin tener que borrar `bastium.db` a mano. Motivación
concreta: estuvo cargando parámetros de prueba en Parámetros que no le
gustaron/quedaron mal, y no tiene ninguna forma de deshacer eso a nivel
global (la Sección 3, "Parámetros: formulario y tabla", agrega
editar/eliminar por fila, pero un reset total es un caso de uso distinto:
"quiero empezar de cero").

Esta pantalla vive dentro de `ConfiguracionesView`
(`app/views/configuraciones.py`, Sprint 66), que ya tiene el patrón de
submenú lateral + `QStackedWidget` para alternar entre secciones
("Parámetros", "Apariencia"). Este sprint agrega una tercera sección,
"Restablecer".

Modelos de datos existentes relevantes (`database/models.py`):
`expedientes` (tabla raíz), con `obligaciones`/`abonos`/`eventos_laborales`/
`descuentos_laborales`/`audit_logs` colgando de ella por relación
(`cascade="all, delete-orphan"` en `Expediente`, confirmado en el Sprint 60);
y `parametros_legales`, independiente de `Expediente`, con la nueva columna
`creado_por_sistema` (ver spec de la Sección 3).

No existe hoy ningún backup automático en el código (confirmado: grep de
`.bak-`/`shutil.copy` sobre `*.py` sin resultados, ver cierre del Sprint 64)
— los 5 `bastium.db.bak-*` en `backups/` son todos manuales.

## Objetivo

Una acción, disponible en Configuraciones › Restablecer, que:
1. Genera un backup automático de la base de datos activa antes de tocar nada.
2. Borra todos los expedientes (y en cascada: obligaciones, abonos, eventos
   laborales, descuentos laborales, audit logs) y todos los parámetros
   legales con `creado_por_sistema=False`.
3. Restaura el tema visual a claro (el valor por defecto).
4. Dejar la app usable de inmediato, sin reiniciar el proceso.

## Diseño

### 1. Nueva sección "Restablecer" en `ConfiguracionesView`

Tercer botón en el submenú lateral (`app/views/configuraciones.py`), junto a
"Parámetros" y "Apariencia", siguiendo el mismo patrón `SECCION_*` /
`_ETIQUETA_POR_SECCION` / `mostrar_*()` que ya usa esa clase (Sprint 66). El
breadcrumb en `main_window.py` gana una tercera variante:
`"Configuraciones › Restablecer"`.

### 2. `RestablecerView` (nueva)

Nuevo archivo `app/views/restablecer.py` (o agregado a `configuraciones.py`
si se mantiene pequeño — decisión de implementación). Contenido:

- Texto explicativo claro de qué hace la acción y qué NO se puede deshacer
  (salvo restaurando el backup manualmente).
- Botón "Restablecer datos de fábrica" con estilo destructivo (misma clase
  `class="destructive"` que ya usan los botones "Eliminar" existentes en
  `resources/theme.qss`/`theme_dark.qss`, colores `#D32F2F`/`#E57373`).

### 3. Diálogo de confirmación

Al pulsar el botón: `QDialog` (o `QInputDialog`-like custom) con:
- El texto de advertencia repetido, listando explícitamente qué se borra.
- Un `QLineEdit` donde el usuario debe escribir exactamente `RESTABLECER`
  (mayúsculas, sin espacios extra) para habilitar el botón de confirmar —
  el botón de confirmar arranca deshabilitado y se activa solo cuando el
  texto coincide exactamente (`campo.textChanged.connect(...)` comparando
  contra la constante).
- Botón "Cancelar" siempre habilitado.

### 4. Lógica de reset (`app/services/` — nueva función, p.ej.
`app/services/restablecer_service.py::restablecer_datos_fabrica()`)

Pasos, en este orden, dentro de la misma operación:

1. **Backup:** copiar el archivo de base de datos activo (ruta ya conocida
   por `database/database.py`) a
   `backups/bastium.db.bak-<YYYYMMDD-HHMMSS>`, mismo patrón de nombre que
   los backups manuales ya presentes en esa carpeta. Si la copia falla
   (permiso, disco lleno), abortar todo el reset sin borrar nada y mostrar
   el error — nunca continuar sin backup exitoso.
2. **Borrado de expedientes:** `session.query(Expediente).delete()` (o
   iterar y `session.delete()` para que las relaciones en cascada de
   SQLAlchemy se disparen correctamente — usar el mismo mecanismo que ya
   usa `_eliminar_obligacion`/equivalentes en vez de un `DELETE FROM` crudo,
   para no tener que reimplementar la cascada a mano).
3. **Borrado de parámetros de usuario:**
   `session.query(ParametroLegal).filter_by(creado_por_sistema=False).delete()`.
4. **Reset de apariencia:** llamar `guardar_modo_tema(MODO_CLARO)` y
   `aplicar_tema(app, MODO_CLARO)` (mismas funciones de
   `app/core/apariencia.py` que ya usa `AparienciaView`) para que el cambio
   se aplique en caliente sin reiniciar, igual que el toggle manual.
5. Refrescar cualquier vista visible en ese momento que dependa de datos
   ahora borrados (dashboard, tabla de parámetros) — mismo criterio que ya
   usan otras pantallas tras una eliminación.

### 5. Mensaje de resultado

Tras completar, `QMessageBox` de éxito indicando la ruta del backup creado
(para que el usuario sepa dónde recuperar los datos si se equivocó).

## Fuera de alcance

- No hay "deshacer" del reset — el backup automático es la única red de
  seguridad, mismo criterio que el Sprint 60 (sin papelera) y el Sprint 64
  (los backups son responsabilidad manual del usuario, aquí automatizado
  solo para este caso puntual).
- No se restaura automáticamente ningún backup — restaurar uno es una
  operación manual fuera de la app (reemplazar `bastium.db`), como ya es hoy.
- No se toca la lógica de migraciones (`aplicar_migraciones_pendientes`) ni
  el sembrado original de `parametros_legales` — el reset borra hasta dejar
  solo las filas `creado_por_sistema=True` ya existentes, no re-siembra
  desde cero ni reinstala el esquema.
