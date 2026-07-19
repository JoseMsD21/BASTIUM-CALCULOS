# Sprint 9 — Motor de auditoría: wiring a GUI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the already-built, already-tested audit service
(`app/engine/audit/service.py`: `registrar_liquidacion`,
`reconstruir_liquidacion`, `historial_de_expediente`) to the real liquidation
flow and the expediente detail screen, so every liquidation run gets logged
and a past one can be reconstructed and viewed with a double-click.

**Architecture:** All changes live in `app/views/expediente_detalle.py`
(`ExpedienteDetallePage`). A new `QGroupBox`/`QTableWidget` follows the exact
pattern already used for Obligaciones/Abonos in that file. `_liquidar()`
gains a call to `registrar_liquidacion` right after a successful calculation.
A `cellDoubleClicked` handler on the new table calls `reconstruir_liquidacion`
and routes the result through the existing `on_liquidado` callback — no new
display code.

**Tech Stack:** PySide6 (Qt widgets), SQLAlchemy (short-lived sessions via
`database.session.get_session()`), pytest + pytest-qt (`qtbot`).

**Design doc:** `docs/superpowers/specs/2026-07-19-motor-auditoria-gui-design.md`

---

### Task 1: "Historial de auditoría" table — display existing records

**Files:**
- Modify: `app/views/expediente_detalle.py`
- Test: `tests/views/test_expediente_detalle.py`

- [x] **Step 1: Write the failing test**

Add to the end of `tests/views/test_expediente_detalle.py`:

```python
from app.engine.audit.service import registrar_liquidacion
from app.engine.liquidation.registry import AreaRegistry


def test_cargar_expediente_muestra_historial_de_auditoria_existente(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    session = session_module.get_session()
    expediente = session.get(Expediente, expediente_id)
    obligaciones = list(expediente.obligaciones)
    estrategia = AreaRegistry.get_strategy(expediente.area_derecho.value)
    resultado = estrategia.liquidar(
        obligaciones=obligaciones, abonos=[], fecha_corte=expediente.fecha_corte_default
    )
    registrar_liquidacion(
        session,
        expediente_id=expediente_id,
        area_derecho=expediente.area_derecho.value,
        fecha_corte=expediente.fecha_corte_default,
        resultado=resultado,
        usuario="jsilva",
    )
    session.close()

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    assert page.tabla_historial.rowCount() == 1
    assert page.tabla_historial.item(0, 1).text() == "jsilva"
    assert page.tabla_historial.item(0, 2).text() == "CIVIL_FAMILIA"
    assert page.tabla_historial.item(0, 3).text() == "2026-06-01"
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/views/test_expediente_detalle.py::test_cargar_expediente_muestra_historial_de_auditoria_existente -v`
Expected: FAIL — `AttributeError: 'ExpedienteDetallePage' object has no attribute 'tabla_historial'`

- [x] **Step 3: Add the import**

In `app/views/expediente_detalle.py`, change:

```python
from app.engine.liquidation.registry import AreaRegistry
```

to:

```python
from app.engine.audit.service import historial_de_expediente
from app.engine.liquidation.registry import AreaRegistry
```

- [x] **Step 4: Add the table widget and group box in `__init__`**

Change:

```python
        boton_liquidar = QPushButton("Liquidar")
        boton_liquidar.clicked.connect(self._liquidar)

        columnas = QHBoxLayout()
        columnas.addWidget(grupo_obligaciones)
        columnas.addWidget(grupo_abonos)

        layout_principal = QVBoxLayout()
        layout_principal.addLayout(columnas)
        layout_principal.addWidget(boton_liquidar)
        self.setLayout(layout_principal)
```

to:

```python
        boton_liquidar = QPushButton("Liquidar")
        boton_liquidar.clicked.connect(self._liquidar)

        self._audit_log_ids_por_fila = []
        self.tabla_historial = QTableWidget(0, 4)
        self.tabla_historial.setHorizontalHeaderLabels(
            ["Fecha ejecución", "Usuario", "Área", "Fecha corte"]
        )

        grupo_historial = QGroupBox("Historial de auditoría")
        layout_historial = QVBoxLayout()
        layout_historial.addWidget(self.tabla_historial)
        grupo_historial.setLayout(layout_historial)

        columnas = QHBoxLayout()
        columnas.addWidget(grupo_obligaciones)
        columnas.addWidget(grupo_abonos)

        layout_principal = QVBoxLayout()
        layout_principal.addLayout(columnas)
        layout_principal.addWidget(boton_liquidar)
        layout_principal.addWidget(grupo_historial)
        self.setLayout(layout_principal)
```

- [x] **Step 5: Add `_refrescar_historial` and wire it into `cargar_expediente`**

Change:

```python
    def cargar_expediente(self, expediente_id: int) -> None:
        self._expediente_id = expediente_id
        self._refrescar_obligaciones()
        self._refrescar_abonos()
```

to:

```python
    def cargar_expediente(self, expediente_id: int) -> None:
        self._expediente_id = expediente_id
        self._refrescar_obligaciones()
        self._refrescar_abonos()
        self._refrescar_historial()
```

Then add the new method right after `_refrescar_abonos` (before
`_abrir_dialogo_obligacion`):

```python
    def _refrescar_historial(self) -> None:
        session = session_module.get_session()
        historial = historial_de_expediente(session, self._expediente_id)

        self.tabla_historial.setRowCount(len(historial))
        self._audit_log_ids_por_fila = []
        for fila, registro in enumerate(historial):
            self.tabla_historial.setItem(
                fila, 0, QTableWidgetItem(registro.fecha_ejecucion.strftime("%Y-%m-%d %H:%M:%S"))
            )
            self.tabla_historial.setItem(fila, 1, QTableWidgetItem(registro.usuario))
            self.tabla_historial.setItem(fila, 2, QTableWidgetItem(registro.area_derecho))
            self.tabla_historial.setItem(fila, 3, QTableWidgetItem(registro.fecha_corte.isoformat()))
            self._audit_log_ids_por_fila.append(registro.id)
        session.close()
```

- [x] **Step 6: Run test to verify it passes**

Run: `python -m pytest tests/views/test_expediente_detalle.py::test_cargar_expediente_muestra_historial_de_auditoria_existente -v`
Expected: PASS

- [x] **Step 7: Run the full test file to check for regressions**

Run: `python -m pytest tests/views/test_expediente_detalle.py -v`
Expected: all tests PASS (existing + new)

- [x] **Step 8: Commit**

```bash
git add app/views/expediente_detalle.py tests/views/test_expediente_detalle.py
git commit -m "feat(expediente-detalle): show audit history table"
```

---

### Task 2: Register every liquidation run

**Files:**
- Modify: `app/views/expediente_detalle.py`
- Test: `tests/views/test_expediente_detalle.py`

- [x] **Step 1: Write the failing test**

Add to `tests/views/test_expediente_detalle.py`:

```python
def test_liquidar_registra_auditoria_y_refresca_historial(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    page._liquidar()

    assert page.tabla_historial.rowCount() == 1
    assert page.tabla_historial.item(0, 2).text() == "CIVIL_FAMILIA"
    assert page.tabla_historial.item(0, 3).text() == "2026-06-01"
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/views/test_expediente_detalle.py::test_liquidar_registra_auditoria_y_refresca_historial -v`
Expected: FAIL — `assert 0 == 1` (the table is still empty because `_liquidar` doesn't register anything yet)

- [x] **Step 3: Add the import**

Change:

```python
from app.engine.audit.service import historial_de_expediente
```

to:

```python
from app.engine.audit.service import historial_de_expediente, registrar_liquidacion
```

- [x] **Step 4: Call `registrar_liquidacion` after a successful calculation**

In `_liquidar`, change:

```python
        except ValueError as error:
            QMessageBox.warning(self, "No se pudo liquidar", str(error))
            return

        if self._on_liquidado:
            self._on_liquidado(resultado, self._expediente_id)
```

to:

```python
        except ValueError as error:
            QMessageBox.warning(self, "No se pudo liquidar", str(error))
            return

        session = session_module.get_session()
        registrar_liquidacion(
            session,
            expediente_id=self._expediente_id,
            area_derecho=area,
            fecha_corte=fecha_corte,
            resultado=resultado,
        )
        session.close()
        self._refrescar_historial()

        if self._on_liquidado:
            self._on_liquidado(resultado, self._expediente_id)
```

- [x] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/views/test_expediente_detalle.py::test_liquidar_registra_auditoria_y_refresca_historial -v`
Expected: PASS

- [x] **Step 6: Run the full test file to check for regressions**

Run: `python -m pytest tests/views/test_expediente_detalle.py -v`
Expected: all tests PASS

- [x] **Step 7: Commit**

```bash
git add app/views/expediente_detalle.py tests/views/test_expediente_detalle.py
git commit -m "feat(expediente-detalle): register every liquidation run in the audit log"
```

---

### Task 3: Reconstruct a past liquidation on double-click

**Files:**
- Modify: `app/views/expediente_detalle.py`
- Test: `tests/views/test_expediente_detalle.py`

- [x] **Step 1: Write the failing test**

Add to `tests/views/test_expediente_detalle.py`:

```python
def test_doble_clic_en_historial_reconstruye_liquidacion(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)
    page._liquidar()
    resultados_recibidos.clear()

    page._reconstruir_desde_historial(0, 0)

    assert len(resultados_recibidos) == 1
    resultado, exp_id = resultados_recibidos[0]
    assert exp_id == expediente_id
    assert resultado.final_balance().principal == Decimal("427900.00")
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/views/test_expediente_detalle.py::test_doble_clic_en_historial_reconstruye_liquidacion -v`
Expected: FAIL — `AttributeError: 'ExpedienteDetallePage' object has no attribute '_reconstruir_desde_historial'`

- [x] **Step 3: Add the import**

Change:

```python
from app.engine.audit.service import historial_de_expediente, registrar_liquidacion
```

to:

```python
from app.engine.audit.service import historial_de_expediente, reconstruir_liquidacion, registrar_liquidacion
```

- [x] **Step 4: Connect the double-click signal in `__init__`**

Change:

```python
        self._audit_log_ids_por_fila = []
        self.tabla_historial = QTableWidget(0, 4)
        self.tabla_historial.setHorizontalHeaderLabels(
            ["Fecha ejecución", "Usuario", "Área", "Fecha corte"]
        )
```

to:

```python
        self._audit_log_ids_por_fila = []
        self.tabla_historial = QTableWidget(0, 4)
        self.tabla_historial.setHorizontalHeaderLabels(
            ["Fecha ejecución", "Usuario", "Área", "Fecha corte"]
        )
        self.tabla_historial.cellDoubleClicked.connect(self._reconstruir_desde_historial)
```

- [x] **Step 5: Add the handler method**

Add right after `_refrescar_historial`:

```python
    def _reconstruir_desde_historial(self, fila: int, columna: int) -> None:
        audit_log_id = self._audit_log_ids_por_fila[fila]
        session = session_module.get_session()
        resultado = reconstruir_liquidacion(session, audit_log_id)
        session.close()
        if self._on_liquidado:
            self._on_liquidado(resultado, self._expediente_id)
```

- [x] **Step 6: Run test to verify it passes**

Run: `python -m pytest tests/views/test_expediente_detalle.py::test_doble_clic_en_historial_reconstruye_liquidacion -v`
Expected: PASS

- [x] **Step 7: Run the full test file to check for regressions**

Run: `python -m pytest tests/views/test_expediente_detalle.py -v`
Expected: all tests PASS

- [x] **Step 8: Commit**

```bash
git add app/views/expediente_detalle.py tests/views/test_expediente_detalle.py
git commit -m "feat(expediente-detalle): reconstruct a past liquidation on double-click"
```

---

### Task 4: Full suite check

**Files:** none (verification only)

- [x] **Step 1: Run the entire suite**

Run: `python -m pytest -q`
Expected: all tests PASS (235 = the 232 already green + the 3 new tests from Tasks 1-3), 0 failures

- [x] **Step 2: If anything fails, stop and fix before continuing**

Do not proceed to Task 5 with a red suite.

---

### Task 5: Update documentation (sprint-closing rule)

**Files:**
- Modify: `Pendientes.md`
- Modify: `docs/GUIA_USUARIO.md`
- Modify: `README.md`
- Modify: `docs/specifications/05_motor_auditoria.md`

- [x] **Step 1: Update `docs/specifications/05_motor_auditoria.md`**

Replace the entire file content with:

```markdown
# Motor de Auditoria

## Estado actual

`app/engine/audit/` implementa el motor completo de auditoria:

- `serialization.py` — `serializar_resultado(resultado) -> str` /
  `deserializar_resultado(json_str) -> LiquidationResult`: snapshot JSON
  exacto de un `LiquidationResult`, sin perder precision (Decimal como
  string, fechas ISO).
- `service.py`:
  - `registrar_liquidacion(session, *, expediente_id, area_derecho,
    fecha_corte, resultado, usuario=None, fecha_ejecucion=None) ->
    AuditLog` — crea una fila append-only en `AuditLog` (modelo en
    `database/models.py`) con el snapshot serializado. `usuario` por
    defecto es el usuario del sistema operativo (`getpass.getuser()`),
    porque BASTIUM no tiene sistema de autenticacion propio.
  - `reconstruir_liquidacion(session, audit_log_id) -> LiquidationResult` —
    reconstruye exactamente el resultado de una ejecucion pasada a partir
    del snapshot, sin recalcular (por lo tanto inmune a que las tasas
    hayan cambiado desde entonces).
  - `historial_de_expediente(session, expediente_id) -> list[AuditLog]` —
    liquidaciones ejecutadas para un expediente, mas recientes primero.

## Conexion a la GUI

`ExpedienteDetallePage` (`app/views/expediente_detalle.py`) tiene una
seccion "Historial de auditoria":

- Cada clic en "Liquidar" que termina en un resultado valido llama a
  `registrar_liquidacion` automaticamente.
- La tabla de historial se refresca al abrir el expediente y despues de
  cada liquidacion nueva.
- Doble clic en una fila del historial llama a `reconstruir_liquidacion` y
  muestra ese resultado pasado en la pantalla de Resultado de Liquidacion,
  reutilizando el mismo callback `on_liquidado` que una liquidacion nueva.

## Trazabilidad de tasa/indice por tramo

`LiquidationItem.rate_source` (`app/engine/liquidation/models.py`) se
completa por tramo desde `RateProvider.get_rate_source()` y las
estrategias de area (`app/services/area_strategy.py`), y queda incluido en
el snapshot serializado — asi que la reconstruccion de una liquidacion
historica tambien preserva que tasa/fuente se uso en cada tramo.

## Pendiente

- No hay sistema de usuarios/roles: `usuario` es el usuario del sistema
  operativo, no un login de la aplicacion (decision de alcance, ver
  `Pendientes.md`, Sprint 9).
```

- [x] **Step 2: Update `Pendientes.md`**

Change the Sprint 9 header:

```
## Sprint 9 — Motor de auditoría / bitácora 🟡 En proceso
```

to:

```
## Sprint 9 — Motor de auditoría / bitácora ✅ Completado
```

Then, right before the closing `---` of the Sprint 9 section (after the
existing "Definición de Hecho" bullets), add:

```markdown

**Estado:** Implementado (2026-07-19). La infraestructura (rate_source por
tramo, modelo `AuditLog`, serialización JSON exacta,
`registrar_liquidacion`/`reconstruir_liquidacion`/`historial_de_expediente`)
se había construido en sesiones previas; la última pieza
(`registrar_liquidacion`/`reconstruir_liquidacion`/`historial_de_expediente`)
quedó completa y probada en una rama huérfana (`sprint9-task8-audit-service`)
que nunca se fusionó — se recuperó por cherry-pick al inicio de esta sesión.
Lo que faltaba y se agregó ahora es el wiring a la GUI:
`ExpedienteDetallePage` registra cada liquidación ejecutada y muestra un
historial de auditoría con reconstrucción de una liquidación pasada al
hacer doble clic (ver
`docs/superpowers/plans/2026-07-19-motor-auditoria-gui-wiring.md` y
`docs/superpowers/specs/2026-07-19-motor-auditoria-gui-design.md`).
```

- [x] **Step 3: Update `docs/GUIA_USUARIO.md` — remove from pending list**

Change:

```
- 🚧 **Auditoría** (quién liquidó cada expediente y cuándo) — no existe todavía (`Pendientes.md`, Sprint 9).
```

Delete that line entirely (it moves to section 5, see next step).

- [x] **Step 4: Update `docs/GUIA_USUARIO.md` — add usage section**

Add a new subsection after "5.11. Editar o eliminar un expediente" (before
the `---` that starts section 6):

```markdown

### 5.12. Ver el historial de auditoría y reconstruir una liquidación pasada

Cada vez que liquidas un expediente, el programa guarda automáticamente un
registro: quién lo hizo, cuándo, con qué área del derecho y con qué fecha de
corte. Esto queda visible en la pantalla de Detalle, debajo del botón
"Liquidar", en la sección **"Historial de auditoría"**.

1. Cada fila muestra: fecha y hora de ejecución, usuario del computador que
   liquidó, área del derecho, y fecha de corte usada.
2. Las liquidaciones más recientes aparecen primero.
3. Para volver a ver el resultado exacto de una liquidación anterior (aunque
   las tasas hayan cambiado desde entonces), haz **doble clic** en esa fila:
   el programa te lleva a la pantalla de Resultado de Liquidación mostrando
   ese cálculo tal como quedó guardado, sin recalcularlo.

El historial de auditoría es de solo lectura: no se puede editar ni borrar
una fila individualmente (solo desaparece si se elimina el expediente
completo, ver [sección 5.11](#511-editar-o-eliminar-un-expediente)).
```

- [x] **Step 5: Update `README.md`**

Change:

```
del Consejo Superior de la Judicatura). El resultado de cualquier liquidación se puede exportar a **PDF**
y a **Word** desde la pantalla de Resultado de Liquidación.
```

to:

```
del Consejo Superior de la Judicatura). El resultado de cualquier liquidación se puede exportar a **PDF**
y a **Word** desde la pantalla de Resultado de Liquidación. Cada liquidación ejecutada queda registrada en
un historial de auditoría por expediente (quién, cuándo, con qué área y fecha de corte), con reconstrucción
exacta de un cálculo pasado con solo hacer doble clic sobre su fila.
```

- [x] **Step 6: Commit**

```bash
git add Pendientes.md README.md docs/GUIA_USUARIO.md docs/specifications/05_motor_auditoria.md
git commit -m "docs: close Sprint 9 (motor de auditoría GUI wiring)"
```

---

### Task 6: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Run the entire suite one more time**

Run: `python -m pytest -q`
Expected: all tests PASS, 0 failures

- [ ] **Step 2: Manual smoke test**

Run: `python main.py`

1. Open or create an expediente in area Civil/Familia with at least one
   obligación.
2. Click "Liquidar" — confirm the result screen appears as before.
3. Go back to the expediente detail screen — confirm a new row appears in
   "Historial de auditoría" with today's date, your OS username, "CIVIL_FAMILIA",
   and the fecha de corte used.
4. Double-click that row — confirm it opens the Resultado de Liquidación
   screen showing the same numbers.

- [ ] **Step 3: Report back**

Confirm to the user: suite is green, manual smoke test passed, Sprint 9 is
closed. Mention the orphaned worktree `.claude/worktrees/sprint9-task8-audit-service`
(branch `sprint9-task8-audit-service`) is now fully merged into `main` and
can be removed — ask before deleting it, since removing a worktree/branch is
a destructive operation.
