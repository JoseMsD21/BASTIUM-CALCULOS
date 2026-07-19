# Diseño: Cierre del Sprint 9 — Motor de auditoría / bitácora (wiring a GUI)

Fecha: 2026-07-19

## Contexto

El Sprint 9 (`Pendientes.md`) ya tenía la mayor parte de su infraestructura
construida y fusionada en `main` antes de esta sesión:

- `LiquidationItem.rate_source` y su propagación por tramo desde
  `RateProvider`/`MemoryRateProvider` y las estrategias de área (Tareas 1-5).
- El modelo `AuditLog` en `database/models.py` (Tarea 6): `expediente_id`,
  `usuario`, `fecha_ejecucion`, `fecha_corte`, `area_derecho`,
  `resultado_json`, con cascada de borrado desde `Expediente`.
- Serialización JSON exacta de `LiquidationResult` en
  `app/engine/audit/serialization.py` (Tarea 7): `serializar_resultado` /
  `deserializar_resultado`, ya probada en `tests/audit/test_serialization.py`.

La Tarea 8 (`app/engine/audit/service.py`: `registrar_liquidacion`,
`reconstruir_liquidacion`, `historial_de_expediente`, con tests en
`tests/audit/test_service.py`) existía completa y probada, pero solo en una
rama huérfana (`sprint9-task8-audit-service`, worktree en
`.claude/worktrees/`) nunca fusionada — el resto de `main` había avanzado con
otro trabajo (Sprint 4, exportación PDF/Word, navegación) mientras esa rama
quedó atrás. Se trajo (cherry-pick, sin conflictos) al inicio de esta sesión;
la suite completa quedó en verde (232 tests).

Lo que faltaba, y es el objeto de este documento: **nada en la GUI invoca
todavía el servicio de auditoría**. Si un usuario liquida un expediente desde
`ExpedienteDetallePage`, no se crea ningún `AuditLog`. El motor existe pero es
código muerto desde el punto de vista de la aplicación real.

## Alcance

Conectar `registrar_liquidacion` al flujo real de liquidación y exponer el
historial de auditoría (con reconstrucción) en la misma pantalla donde ya
viven Obligaciones y Abonos.

## 1. Registrar cada liquidación ejecutada

### Componente

`app/views/expediente_detalle.py` — `ExpedienteDetallePage._liquidar`.

### Diseño

Hoy `_liquidar` (línea 118) abre una sesión, lee `obligaciones`/`abonos`/
`fecha_corte`/`area`, la cierra, y luego llama
`estrategia.liquidar(...)` fuera de la sesión. Justo después de que
`resultado` se obtiene con éxito (antes de invocar `self._on_liquidado`), se
abre una nueva sesión corta (mismo patrón que el resto del archivo:
`session_module.get_session()` / `session.close()`) y se llama:

```python
registrar_liquidacion(
    session,
    expediente_id=self._expediente_id,
    area_derecho=area,
    fecha_corte=fecha_corte,
    resultado=resultado,
)
```

`usuario` y `fecha_ejecucion` se dejan en sus valores por defecto
(`getpass.getuser()` / `datetime.now()`) — BASTIUM no tiene sistema de
usuarios (excluido explícitamente del alcance del Sprint 9 en
`Pendientes.md`), así que el usuario del sistema operativo es la mejor
aproximación disponible sin construir autenticación.

No se agrega manejo de errores especial: si el `commit` fallara, se
propagaría igual que cualquier otra escritura a SQLite en este archivo (no
hay try/except alrededor de `session.add`/`commit` en ningún otro punto de
`expediente_detalle.py` u `obligaciones.py`/`abonos.py`; mantener
consistencia).

Después de registrar, se llama `self._refrescar_historial()` (ver sección 2)
para que la fila nueva aparezca de inmediato, y luego se continúa el flujo
existente (`self._on_liquidado(resultado, self._expediente_id)`) sin cambios.

## 2. Sección "Historial de auditoría"

### Componente

`app/views/expediente_detalle.py` — `ExpedienteDetallePage`.

### Diseño

Se agrega un tercer `QGroupBox("Historial de auditoría")` con su propio
`QTableWidget`, siguiendo exactamente el patrón ya usado por
`grupo_obligaciones`/`tabla_obligaciones` y `grupo_abonos`/`tabla_abonos`:

- Columnas: `Fecha ejecución | Usuario | Área | Fecha corte`.
- Se añade a `layout_principal`, debajo de `columnas` (la fila
  Obligaciones/Abonos) y del botón "Liquidar" — ancho completo, ya que puede
  crecer con muchas filas a lo largo del tiempo.
- `self._audit_log_ids_por_fila: list[int]`, mismo mecanismo que
  `self._obligacion_ids_por_fila`, para mapear fila → `AuditLog.id`.

`_refrescar_historial(self) -> None`:

```python
session = session_module.get_session()
historial = historial_de_expediente(session, self._expediente_id)
# poblar tabla_historial (ya viene ordenado más reciente primero)
session.close()
```

Se invoca desde:
- `cargar_expediente()` (junto a `_refrescar_obligaciones`/`_refrescar_abonos`),
  para que el historial ya exista al abrir un expediente con liquidaciones
  previas.
- El final de `_liquidar()` tras un registro exitoso (sección 1).

## 3. Reconstrucción al hacer doble clic

### Diseño

`tabla_historial.cellDoubleClicked.connect(self._reconstruir_desde_historial)`.

```python
def _reconstruir_desde_historial(self, fila: int, columna: int) -> None:
    audit_log_id = self._audit_log_ids_por_fila[fila]
    session = session_module.get_session()
    resultado = reconstruir_liquidacion(session, audit_log_id)
    session.close()
    if self._on_liquidado:
        self._on_liquidado(resultado, self._expediente_id)
```

Esto reutiliza el callback ya existente (el mismo que usa una liquidación
recién calculada) para mostrar el resultado en `ResultadoLiquidacionView` —
no se crea ningún mecanismo de presentación nuevo. Es lo que hace real el
requisito del PDF (pág. 77) de "reconstrucción exacta de una liquidación
histórica": queda accesible con un doble clic, no solo demostrado en un test
aislado.

## 4. Tests (TDD)

Nuevos casos en `tests/views/test_expediente_detalle.py`, siguiendo el patrón
ya establecido en ese archivo (SQLite en memoria + `monkeypatch.setattr(
session_module, "SessionLocal", ...)`):

1. `test_liquidar_registra_auditoria_y_refresca_historial` — tras
   `page._liquidar()`, `tabla_historial.rowCount() == 1` y su contenido
   coincide con área/fecha de corte esperados.
2. `test_doble_clic_en_historial_reconstruye_liquidacion` — liquidar una vez,
   simular doble clic en la fila del historial, verificar que el callback
   `on_liquidado` recibe un `LiquidationResult` cuyo `final_balance()`
   coincide con el original.
3. `test_cargar_expediente_carga_historial_existente` — pre-sembrar un
   `AuditLog` vía `registrar_liquidacion` directamente, luego
   `cargar_expediente()`, verificar que la fila aparece sin necesidad de
   liquidar en la sesión de prueba.

## 5. Documentación (regla de cierre de sprint)

- `Pendientes.md`: marcar Sprint 9 como `✅ Completado`, con nota de
  ejecución real (rama huérfana recuperada por cherry-pick, wiring a GUI
  agregado en esta sesión).
- `docs/GUIA_USUARIO.md`: describir la sección "Historial de auditoría" (qué
  muestra, cómo reconstruir una liquidación pasada con doble clic), siguiendo
  el mismo estilo usado para documentar Obligaciones/Abonos.
- `README.md`: sacar "Motor de auditoría" de cualquier lista de
  pendientes/en desarrollo si existe una entrada así.
- `docs/specifications/05_motor_auditoria.md`: reemplazar el estado
  "Todo (no implementado aún)" por una descripción real de
  `registrar_liquidacion`/`reconstruir_liquidacion`/`historial_de_expediente`
  y su punto de entrada en la GUI.

## Fuera de alcance

- Sistema de usuarios/roles (excluido explícitamente en `Pendientes.md`;
  `usuario` sigue siendo el usuario del sistema operativo vía `getpass`).
- Comparación visual entre dos liquidaciones históricas (side-by-side) — el
  doble clic reemplaza el contenido de `ResultadoLiquidacionView`, no abre
  una vista comparativa.
- Botón para "eliminar" un registro de auditoría — `AuditLog` es
  append-only por diseño (ya reflejado en los tests de la Tarea 8:
  `test_historial_de_expediente_ordena_mas_reciente_primero_y_es_append_only`).
- Limpieza de la rama/worktree huérfana `sprint9-task8-audit-service` — se
  maneja como paso operativo aparte al cerrar la sesión, no como parte del
  plan de implementación.
