# Parámetros (área/unidad/presentación), diálogos redimensionables, tooltips y CRUD de Obligaciones/Abonos — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar los Sprints 56-60 de `Pendientes.md`: diálogos redimensionables, columnas de
área/unidad por fila en Parámetros con migración de las 683 filas existentes, presentación inteligente
(vigencia, IPC crudo vs. calculado, enlace de historial), tooltips de ayuda en los 4 formularios
principales, y editar/eliminar Obligaciones y Abonos.

**Architecture:** Cambios acotados por archivo, siguiendo los patrones ya establecidos en el repo
(`form_utils.py` para helpers de UI compartidos, `scripts/migrate_*.py` idempotentes para cambios de
esquema, `AreaDerecho`/`ModoResolucion` ya existentes reutilizados sin duplicar). Cada sprint es
independiente en su Definición de Hecho pero se ejecutan en secuencia (56→57→58→59→60) porque 57/58/59
comparten `app/views/configuracion.py`.

**Tech Stack:** Python 3.14, PySide6 (Qt), SQLAlchemy 2.0, SQLite, pytest/pytest-qt.

**Spec de referencia:** `docs/superpowers/specs/2026-08-11-parametros-ux-dialogos-crud-design.md`
(diseño completo, ya aprobado, con la tabla de área/unidad por clave y el razonamiento de cada decisión —
léelo antes de tocar código, no repitas la investigación ahí documentada).

---

## Sprint 56 — Diálogos redimensionables/maximizables

### Task 1: Helper `hacer_redimensionable` en `form_utils.py`

**Files:**
- Modify: `app/views/form_utils.py`
- Test: `tests/views/test_form_utils.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_hacer_redimensionable_agrega_flags_de_minimizar_y_maximizar(qtbot):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QDialog
    from app.views.form_utils import hacer_redimensionable

    dialogo = QDialog()
    qtbot.addWidget(dialogo)
    hacer_redimensionable(dialogo)

    flags = dialogo.windowFlags()
    assert flags & Qt.WindowType.WindowMinimizeButtonHint
    assert flags & Qt.WindowType.WindowMaximizeButtonHint
```

- [ ] **Step 2: Correr el test, confirmar que falla** (`ImportError: cannot import name 'hacer_redimensionable'`)

Run: `.venv\Scripts\python.exe -m pytest tests/views/test_form_utils.py::test_hacer_redimensionable_agrega_flags_de_minimizar_y_maximizar -v`

- [ ] **Step 3: Implementar en `app/views/form_utils.py`**

```python
def hacer_redimensionable(dialog: QDialog) -> None:
    """Agrega minimizar/maximizar y redimensionado a un QDialog -- Qt no los
    incluye por defecto en Windows (Sprint 56). Llamar una vez en __init__,
    justo despues de super().__init__(parent)."""
    dialog.setWindowFlags(
        dialog.windowFlags()
        | Qt.WindowType.WindowMinimizeButtonHint
        | Qt.WindowType.WindowMaximizeButtonHint
    )
```

(agregar el import de `QDialog`/`Qt` que falte en el módulo; revisar los imports existentes de
`form_utils.py` antes de duplicar).

- [ ] **Step 4: Correr el test, confirmar que pasa**
- [ ] **Step 5: Commit** — `fix(sprint56): agregar helper hacer_redimensionable a form_utils`

### Task 2: Aplicar el helper a los 7 QDialog

**Files:**
- Modify: `app/views/abonos.py` (`AbonoFormDialog.__init__`)
- Modify: `app/views/configuracion.py` (`ParametroFormDialog.__init__`, `HistorialParametroDialog.__init__`)
- Modify: `app/views/descuentos_laborales.py` (`DescuentoLaboralFormDialog.__init__`)
- Modify: `app/views/eventos_laborales.py` (`EventoLaboralFormDialog.__init__`)
- Modify: `app/views/expedientes.py` (`ExpedienteFormDialog.__init__`)
- Modify: `app/views/obligaciones.py` (`ObligacionFormDialog.__init__`)
- Test: `tests/views/test_dialogos_redimensionables.py` (nuevo, parametrizado sobre los 7)

- [ ] **Step 1: Escribir el test parametrizado que falla**

```python
import pytest
from PySide6.QtCore import Qt


@pytest.mark.parametrize(
    "construir_dialogo",
    [
        lambda qtbot: _abono_form_dialog(qtbot),
        lambda qtbot: _parametro_form_dialog(qtbot),
        lambda qtbot: _historial_parametro_dialog(qtbot),
        lambda qtbot: _descuento_laboral_form_dialog(qtbot),
        lambda qtbot: _evento_laboral_form_dialog(qtbot),
        lambda qtbot: _expediente_form_dialog(qtbot),
        lambda qtbot: _obligacion_form_dialog(qtbot),
    ],
)
def test_dialogo_tiene_flags_de_minimizar_y_maximizar(qtbot, construir_dialogo):
    dialogo = construir_dialogo(qtbot)
    flags = dialogo.windowFlags()
    assert flags & Qt.WindowType.WindowMinimizeButtonHint
    assert flags & Qt.WindowType.WindowMaximizeButtonHint
```

(las 7 funciones `_xxx_form_dialog(qtbot)` construyen cada diálogo con los argumentos mínimos que ya
usan los tests existentes de cada vista — revisa `tests/views/test_obligaciones.py`,
`test_expedientes.py`, `test_configuracion.py`, `test_eventos_laborales.py`,
`test_descuentos_laborales.py`, `test_abonos.py` para copiar exactamente cómo construyen cada diálogo hoy
en sus fixtures/tests existentes, en vez de adivinar los argumentos).

- [ ] **Step 2: Correr el test, confirmar que falla en los 7 casos**
- [ ] **Step 3: Agregar `hacer_redimensionable(self)` justo después de `super().__init__(parent)` en cada uno de los 7 `__init__`** (import `from app.views.form_utils import hacer_redimensionable` en cada archivo que no lo tenga ya)
- [ ] **Step 4: Correr el test, confirmar que pasa en los 7 casos**
- [ ] **Step 5: Correr la suite completa** (`pytest -q`) y `ruff check .`
- [ ] **Step 6: Commit** — `fix(sprint56): agregar minimizar/maximizar a los 7 dialogos del proyecto`

**Definición de Hecho del Sprint 56:** ver spec. Marcar Sprint 56 ✅ Completado en `Pendientes.md` al
cerrar (crear la entrada de sprint en `Pendientes.md` primero, con el texto de este plan + la spec, antes
de implementar — mismo patrón que los Sprints 52-55).

---

## Sprint 57 — Parámetros: columnas Área y Unidad por fila

### Task 1: Columnas nuevas en el modelo

**Files:**
- Modify: `database/models.py` (`class ParametroLegal`)
- Test: `tests/database/test_models.py`

- [ ] **Step 1: Test que falla** — confirmar que `ParametroLegal` tiene `areas_derecho`/`unidad` como
  columnas mapeadas (`assert "areas_derecho" in ParametroLegal.__table__.columns`, ídem `unidad`).
- [ ] **Step 2: Correr, confirmar que falla.**
- [ ] **Step 3: Agregar a `ParametroLegal`** (después de `creado_en`):

```python
    areas_derecho: Mapped[str] = mapped_column(String(200))
    unidad: Mapped[str] = mapped_column(String(30))
```

- [ ] **Step 4: Correr, confirmar que pasa.**
- [ ] **Step 5: Commit** — `feat(sprint57): agregar areas_derecho y unidad al modelo ParametroLegal`

### Task 2: Helpers de serialización de área

**Files:**
- Create: `app/services/areas_parametro.py`
- Test: `tests/services/test_areas_parametro.py`

Centraliza la serialización JSON (`areas_derecho` se guarda como lista JSON de códigos `AreaDerecho`,
decisión ya tomada en la spec) para que la use tanto la migración como `agregar_valor()` como la UI, sin
duplicar `json.dumps`/`json.loads` en 3 lugares.

- [ ] **Step 1: Test que falla**

```python
from database.models import AreaDerecho
from app.services.areas_parametro import serializar_areas, deserializar_areas


def test_serializar_y_deserializar_son_inversas():
    areas = [AreaDerecho.CIVIL_FAMILIA, AreaDerecho.LABORAL]
    texto = serializar_areas(areas)
    assert deserializar_areas(texto) == areas


def test_serializar_rechaza_lista_vacia():
    import pytest
    with pytest.raises(ValueError):
        serializar_areas([])
```

- [ ] **Step 2: Correr, confirmar que falla.**
- [ ] **Step 3: Implementar**

```python
import json

from database.models import AreaDerecho


def serializar_areas(areas: list[AreaDerecho]) -> str:
    if not areas:
        raise ValueError("Debe seleccionarse al menos un area del derecho.")
    return json.dumps([area.value for area in areas])


def deserializar_areas(texto: str) -> list[AreaDerecho]:
    return [AreaDerecho(codigo) for codigo in json.loads(texto)]
```

- [ ] **Step 4: Correr, confirmar que pasa.**
- [ ] **Step 5: Commit** — `feat(sprint57): agregar serializar_areas/deserializar_areas`

### Task 3: `agregar_valor()` exige área y unidad

**Files:**
- Modify: `app/services/parametro_service.py::agregar_valor`
- Test: `tests/services/test_parametro_service.py`

- [ ] **Step 1: Test que falla** — llamar `agregar_valor(...)` sin `areas_derecho`/`unidad` debe fallar
  en la firma (TypeError, argumentos requeridos nuevos); llamar con `areas_derecho=[]` debe lanzar
  `ValueError`; llamar con datos válidos debe persistir la fila con `areas_derecho`/`unidad` legibles vía
  `deserializar_areas`.
- [ ] **Step 2: Correr, confirmar que falla.**
- [ ] **Step 3: Implementar** — agregar `areas_derecho: list[AreaDerecho]` y `unidad: str` como
  parámetros requeridos de `agregar_valor()` (después de `usuario`, antes de `motivo` para no romper el
  orden posicional de los parámetros ya opcionales — revisa la firma actual antes de decidir dónde
  insertarlos); validar `unidad.strip()` no vacío; usar `serializar_areas(areas_derecho)` al construir la
  fila; pasar `unidad=unidad` directo.
- [ ] **Step 4: Correr, confirmar que pasa. Correr también los tests existentes de `agregar_valor` para
  confirmar que no rompiste ningún caller** (`tests/views/test_configuracion.py` seguramente llama
  `agregar_valor` indirectamente vía `ParametroFormDialog.guardar()` — ese caller se actualiza en la
  Task 5, así que es normal que falle hasta entonces; anótalo y sigue).
- [ ] **Step 5: Commit** — `feat(sprint57): agregar_valor exige areas_derecho y unidad`

### Task 4: Script de migración con la tabla de área/unidad por clave

**Files:**
- Create: `scripts/migrate_parametros_area_unidad.py`
- Modify: `database/database.py::aplicar_migraciones_pendientes`
- Test: `tests/database/test_migrations.py`

La tabla completa clave → (áreas, unidad) está en la spec
(`docs/superpowers/specs/2026-08-11-parametros-ux-dialogos-crud-design.md`, sección "Tabla de área
propuesta por clave") — cópiala tal cual, no la vuelvas a derivar. Mismo patrón idempotente que los 11
scripts anteriores: `PRAGMA table_info` para las columnas, y por fila sin `areas_derecho`/`unidad`
asignado (`IS NULL` o `== ''`), completar según la clave de esa fila.

- [ ] **Step 1: Test que falla** — mismo patrón que `test_aplicar_migraciones_pendientes_agrega_es_smmlv`
  en `tests/database/test_migrations.py`: crear una BD temporal con el esquema completo, quitar
  `areas_derecho`/`unidad` (o dejarlas `NULL` si `ALTER TABLE` con `NOT NULL` sin default falla en
  SQLite — usa `NULL` como estado "sin migrar" y agrega la restricción `NOT NULL` solo a nivel de
  aplicación/ORM, no de columna SQLite, si hace falta para que el `ALTER TABLE ADD COLUMN` funcione sin
  un valor por defecto), sembrar 2-3 filas de prueba de claves conocidas (ej. `SMLMV`, `USURA_MULTIPLICADOR`),
  llamar `migrar(db_path)`, y confirmar que esas filas quedan con el área/unidad esperado según la tabla
  de la spec.
- [ ] **Step 2: Correr, confirmar que falla.**
- [ ] **Step 3: Implementar el script** (estructura: diccionario `AREA_UNIDAD_POR_CLAVE: dict[str, tuple[list[str], str]]`
  con las 39 claves tal como están en la tabla de la spec, función `migrar(db_path: Path = DB_PATH) -> bool`
  que agrega las 2 columnas si faltan y completa `areas_derecho`/`unidad` fila por fila con
  `UPDATE parametros_legales SET areas_derecho = ?, unidad = ? WHERE clave = ? AND (areas_derecho IS NULL OR areas_derecho = '')`.
  Reutiliza `serializar_areas`/`AreaDerecho` de la Task 2 para construir el JSON, no repitas `json.dumps` a mano.
- [ ] **Step 4: Correr, confirmar que pasa.**
- [ ] **Step 5: Agregar la llamada en `aplicar_migraciones_pendientes()`** (`database/database.py`),
  import diferido igual que los otros 11, después de `migrar_es_smmlv(ruta)`.
- [ ] **Step 6: Test de integración** — correr `aplicar_migraciones_pendientes(db_tmp)` sobre una BD
  nueva completa (`Base.metadata.create_all` + las 39 claves sembradas vía `migrate_parametros_legales`) y
  confirmar que las 683 filas quedan con `areas_derecho`/`unidad` no vacíos.
- [ ] **Step 7: Correr la suite completa, confirmar 0 regresiones.**
- [ ] **Step 8: Commit** — `feat(sprint57): migracion de areas_derecho/unidad para las 39 claves`

### Task 5: UI — `ParametroFormDialog` y `ParametrosView`

**Files:**
- Modify: `app/views/configuracion.py`
- Test: `tests/views/test_configuracion.py`

- [ ] **Step 1: Test que falla** — `ParametroFormDialog` con una clave conocida (ej. `SMLMV`) debe traer
  preseleccionadas las casillas de área correctas (según la tabla de la spec) y el campo de unidad
  pre-rellenado; `guardar()` sin ninguna casilla marcada debe lanzar `ValueError`; `guardar()` con datos
  válidos debe persistir `areas_derecho`/`unidad` correctos (verificar leyendo la fila creada).
  `ParametrosView.tabla` debe tener 6 columnas (las 4 actuales + "Área" + "Unidad") con los valores de la
  fila vigente de cada clave.
- [ ] **Step 2: Correr, confirmar que falla.**
- [ ] **Step 3: Implementar**
  - `ParametroFormDialog`: un `QCheckBox` por `AreaDerecho` (reutiliza las etiquetas de
    `app/core/constants.py::AREAS_DERECHO`, no inventes texto nuevo), preseleccionados según
    `AREA_UNIDAD_POR_CLAVE` (importado de `scripts/migrate_parametros_area_unidad.py` — si genera un
    import raro por ser un script en `scripts/`, mueve el diccionario a un módulo compartido, ej.
    `app/services/areas_parametro.py` de la Task 2, e impórtalo desde ahí en el script de migración
    también, para no duplicarlo); `QLineEdit` para unidad, pre-rellenado igual. `guardar()` recolecta las
    casillas marcadas y llama `agregar_valor(..., areas_derecho=[...], unidad=texto)`.
  - `ParametrosView.tabla`: agregar columnas "Área" (texto separado por coma de las etiquetas humanas,
    no los códigos crudos) y "Unidad", pobladas en el método que ya llena la tabla hoy.
- [ ] **Step 4: Correr, confirmar que pasa.**
- [ ] **Step 5: Correr la suite completa (`pytest -q`) y `ruff check .`.**
- [ ] **Step 6: Commit** — `feat(sprint57): UI de area y unidad en ParametroFormDialog y ParametrosView`

**Definición de Hecho del Sprint 57:** ver spec.

---

## Sprint 58 — Parámetros: presentación inteligente

### Task 1: `vigencia_hasta_mostrar`

**Files:**
- Modify: `app/services/parametro_service.py`
- Test: `tests/services/test_parametro_service.py`

- [ ] **Step 1: Test que falla** — 3 casos: fila con `vigente_hasta` real → se muestra tal cual; fila
  `ANUAL_EXACTO` sin `vigente_hasta` → `"31 de diciembre de {año} (calculado)"` (o el formato ISO que
  decidas, pero consistente); fila `ABIERTO` sin `vigente_hasta` → `"Indefinido"`.
- [ ] **Step 2: Correr, confirmar que falla.**
- [ ] **Step 3: Implementar** (código exacto ya está en la spec, sección "Vigencia inteligente" — cópialo).
- [ ] **Step 4: Correr, confirmar que pasa.**
- [ ] **Step 5: Commit** — `feat(sprint58): agregar vigencia_hasta_mostrar`

### Task 2: Aplicar en `ParametrosView` y `HistorialParametroDialog`

**Files:**
- Modify: `app/views/configuracion.py`
- Test: `tests/views/test_configuracion.py`

- [ ] **Step 1: Test que falla** — la columna "Vigente hasta" de `ParametrosView.tabla` para SMLMV
  muestra el texto calculado, no vacío; ídem la columna correspondiente de `HistorialParametroDialog`.
- [ ] **Step 2: Correr, confirmar que falla.**
- [ ] **Step 3: Implementar** — reemplazar el llenado directo de la celda por
  `vigencia_hasta_mostrar(fila, info)`.
- [ ] **Step 4: Correr, confirmar que pasa.**
- [ ] **Step 5: Commit** — `feat(sprint58): mostrar vigencia inteligente en Parametros e Historial`

### Task 3: `IPC_VARIACION_ANUAL` sembrada y mostrada junto al índice

**Files:**
- Modify: `scripts/migrate_parametros_area_unidad.py` (o script propio nuevo — decide según cuánto creció
  el de la Task 4 del Sprint 57; si ya es grande, crea `scripts/migrate_ipc_variacion_anual.py` como
  script hermano, mismo patrón, y agrégalo a `aplicar_migraciones_pendientes()`)
- Modify: `app/services/parametro_service.py` (`CATALOGO_PARAMETROS`: nueva entrada `IPC_VARIACION_ANUAL`,
  `ModoResolucion.ANUAL_EXACTO`, categoría "Indicadores historicos")
- Modify: `app/views/configuracion.py::HistorialParametroDialog`
- Test: `tests/database/test_migrations.py`, `tests/views/test_configuracion.py`

- [ ] **Step 1: Test que falla** — tras migrar, `historial("IPC_VARIACION_ANUAL")` devuelve una fila por
  año con el mismo valor que `_IPC_VARIACION_ANUAL[año]` de `historical_index.py`.
- [ ] **Step 2: Correr, confirmar que falla.**
- [ ] **Step 3: Implementar la siembra** — para cada `(año, variacion)` en
  `app/engine/indexation/historical_index.py::_IPC_VARIACION_ANUAL`, insertar una fila
  `IPC_VARIACION_ANUAL` con `vigente_desde=date(año, 1, 1)`, área/unidad iguales a las de
  `IPC_INDICE_ACUMULADO` (Civil/Familia + Tributario, unidad "%"). Agregar la entrada en
  `CATALOGO_PARAMETROS`.
- [ ] **Step 4: Correr, confirmar que pasa.**
- [ ] **Step 5: Test que falla (UI)** — `HistorialParametroDialog("IPC_INDICE_ACUMULADO")` muestra una
  columna extra "Variación anual (%)" con el valor de `IPC_VARIACION_ANUAL` del mismo año, y un texto fijo
  visible con la fórmula (`"Índice = índice del año anterior × (1 + variación anual / 100)."`).
  `HistorialParametroDialog` para cualquier otra clave NO muestra esa columna extra (no rompas el caso
  general).
- [ ] **Step 6: Correr, confirmar que falla.**
- [ ] **Step 7: Implementar** — diccionario `CLAVE_CRUDA_DE = {"IPC_INDICE_ACUMULADO": "IPC_VARIACION_ANUAL"}`
  (ubícalo en `app/services/parametro_service.py`, junto a `CATALOGO_PARAMETROS`); si
  `clave in CLAVE_CRUDA_DE`, `HistorialParametroDialog` consulta también `historial(CLAVE_CRUDA_DE[clave])`,
  arma un diccionario `{año: variacion}` y agrega la columna + el texto de la fórmula.
- [ ] **Step 8: Correr, confirmar que pasa. Suite completa + ruff.**
- [ ] **Step 9: Commit** — `feat(sprint58): sembrar IPC_VARIACION_ANUAL y mostrarla junto al indice`

### Task 4: Enlace "Ver historial" en la tabla principal

**Files:**
- Modify: `app/views/configuracion.py::ParametrosView`
- Test: `tests/views/test_configuracion.py`

- [ ] **Step 1: Test que falla** — para una clave con más de 1 fila (ej. `SMLMV`), la celda de "Valor
  vigente hoy" en `ParametrosView.tabla` incluye el texto "Ver" (o el texto exacto que decidas) además del
  valor; para una clave con exactamente 1 fila, no lo incluye.
- [ ] **Step 2: Correr, confirmar que falla.**
- [ ] **Step 3: Implementar** — al poblar la tabla, contar filas de `historial(clave)`; si `> 1`, usar
  `QTableWidgetItem(f"{valor} — Ver {n} valores históricos")` y mantener el `cellDoubleClicked` ya
  conectado a `_abrir_historial` (no hace falta un widget de botón nuevo si el doble clic ya funciona —
  solo hace falta que el texto sea descubrible; si prefieres un botón real en la celda en vez de solo
  texto más largo, usa `setCellWidget` con un `QPushButton` estilo "link", pero justifica la elección en
  el commit si te desvías del texto simple).
- [ ] **Step 4: Correr, confirmar que pasa. Suite completa + ruff.**
- [ ] **Step 5: Commit** — `feat(sprint58): enlace visible a Ver historial para parametros con multiples valores`

**Definición de Hecho del Sprint 58:** ver spec.

---

## Sprint 59 — Tooltips ⓘ de ayuda en los 4 formularios principales

### Task 1: Extraer `agregar_ayuda` a `form_utils.py`

**Files:**
- Modify: `app/views/form_utils.py`
- Modify: `app/views/obligaciones.py` (eliminar el helper privado duplicado, usar el compartido)
- Test: `tests/views/test_form_utils.py`

- [ ] **Step 1: Leer el helper privado actual de `obligaciones.py`** (línea ~892, el método que construye
  el ícono `icono_info`) para no perder ningún detalle de comportamiento al moverlo (ej. cómo posiciona el
  ícono respecto al campo, si usa `QHBoxLayout` o `QFormLayout.addRow` con un contenedor).
- [ ] **Step 2: Test que falla** — `agregar_ayuda(layout, "Campo", widget, tooltip="...", ejemplo="...")`
  agrega una fila a `layout` (un `QFormLayout` real de prueba) donde el widget resultante tiene el
  tooltip combinado (`"{tooltip}\nEjemplo: {ejemplo}"` o el formato que ya use el helper original — no
  inventes uno nuevo, copia el formato exacto que ya está en producción).
- [ ] **Step 3: Correr, confirmar que falla.**
- [ ] **Step 4: Mover el helper a `form_utils.py`** como función pública `agregar_ayuda`, con la misma
  lógica exacta que tenía el método privado de `obligaciones.py` (renombra parámetros si hace falta para
  que sea reutilizable fuera de esa clase, pero no cambies el comportamiento visual).
- [ ] **Step 5: Actualizar `obligaciones.py`** para llamar `agregar_ayuda` del módulo compartido en vez
  del método privado eliminado, en el único call site que ya lo usaba ("Tasa efectiva anual").
- [ ] **Step 6: Correr el test nuevo y toda la suite de `tests/views/test_obligaciones.py`, confirmar 0
  regresiones** (el campo "Tasa efectiva anual" debe verse exactamente igual que antes).
- [ ] **Step 7: Commit** — `refactor(sprint59): extraer agregar_ayuda a form_utils, compartido`

### Task 2: Tooltips en `ObligacionFormDialog` (resto de campos)

**Files:**
- Modify: `app/views/obligaciones.py`
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Listar los campos de `ObligacionFormDialog` que hoy NO tienen tooltip** (usa el listado de
  `addRow(...)` de la spec/investigación previa: Tipo, Categoria, Concepto, Valor, Fecha de origen, Fecha
  de inicio, Dia de pago, Tasa moratoria anual, Fecha de vencimiento, IBC vigente aplicable, Moneda, TRM
  aplicable, % Cuota litis pactada, Costos/Deducciones renta líquida, Fecha de terminación de contrato,
  Fecha de pago real, Nivel de riesgo ARL — excluye los que son autoexplicativos como "Concepto", que no
  necesitan tooltip según la spec).
- [ ] **Step 2: Test que falla** — para cada campo no autoexplicativo elegido, el widget correspondiente
  tiene un `toolTip()` no vacío tras construir el diálogo.
- [ ] **Step 3: Correr, confirmar que falla.**
- [ ] **Step 4: Redactar el contenido de cada tooltip** (una frase corta + ejemplo concreto, mismo estilo
  que el ya existente de "Tasa efectiva anual": *"Valor por defecto: interés civil legal, Art. 1617
  C.C."*) y aplicar `agregar_ayuda`/`setToolTip` según corresponda a cada campo, citando el artículo legal
  relevante cuando el campo mapea a una clave de `CATALOGO_PARAMETROS` (ej. "IBC vigente aplicable" →
  cita `IBC_CONSUMO_ORDINARIO`/`USURA_CONSUMO_ORDINARIO`).
- [ ] **Step 5: Correr, confirmar que pasa. Suite completa + ruff.**
- [ ] **Step 6: Commit** — `feat(sprint59): tooltips de ayuda en el resto de campos de ObligacionFormDialog`

### Task 3: Tooltips en `ExpedienteFormDialog`, `AbonoFormDialog`, `ParametroFormDialog`

**Files:**
- Modify: `app/views/expedientes.py`
- Modify: `app/views/abonos.py`
- Modify: `app/views/configuracion.py`
- Test: `tests/views/test_expedientes.py`, `tests/views/test_abonos.py`, `tests/views/test_configuracion.py`

- [ ] **Step 1: Listar los campos de cada uno de los 3 diálogos** (revisa sus `addRow`/`QFormLayout`
  actuales).
- [ ] **Step 2: Test que falla por diálogo** — mismo patrón que Task 2 (campos no autoexplicativos tienen
  tooltip).
- [ ] **Step 3: Correr, confirmar que falla en los 3.**
- [ ] **Step 4: Redactar y aplicar `agregar_ayuda` en los 3 diálogos**, mismo criterio que Task 2 (frase
  corta + ejemplo, citar fuente legal cuando aplique — para `ParametroFormDialog`, las casillas de área y
  el campo de unidad del Sprint 57 también reciben su tooltip aquí si no lo tenían ya).
- [ ] **Step 5: Correr, confirmar que pasa en los 3. Suite completa + ruff.**
- [ ] **Step 6: Commit** — `feat(sprint59): tooltips de ayuda en ExpedienteFormDialog, AbonoFormDialog y ParametroFormDialog`

**Definición de Hecho del Sprint 59:** ver spec.

---

## Sprint 60 — Editar/eliminar Obligaciones y Abonos

### Task 1: Eliminar Obligación (con cascada de cuotas hijas)

**Files:**
- Modify: `app/views/expediente_detalle.py`
- Test: `tests/views/test_expediente_detalle.py`

- [ ] **Step 1: Test que falla (caso simple)** — una obligación sin abonos/cuotas hijas: llamar
  `_eliminar_obligacion(id)` (simulando la confirmación con `monkeypatch` de `QMessageBox.question` →
  `Yes`, mismo patrón que el test existente de `_eliminar_evento_laboral`) borra la fila de
  `tabla_obligaciones` y la fila real en la base de datos.
- [ ] **Step 2: Test que falla (caso con abonos)** — una obligación con 2 abonos: al eliminarla, los
  abonos también desaparecen de la base (cascada del modelo, no código nuevo, pero el test lo confirma).
- [ ] **Step 3: Test que falla (caso con cuotas hijas)** — una obligación RECURRENTE con reajuste anual
  que ya generó cuotas (`obligacion_padre_id` apuntando a ella): al eliminar el padre, las cuotas hijas
  también desaparecen de la base.
- [ ] **Step 4: Correr los 3, confirmar que fallan** (columna "Eliminar" todavía no existe).
- [ ] **Step 5: Implementar** — agregar columna "Eliminar" a `tabla_obligaciones` (ampliar de 4 a 5
  columnas, `["Concepto", "Tipo", "Valor", "Editar", "Eliminar"]`), botón `destructive` por fila (mismo
  patrón que `tabla_eventos_laborales`, línea ~294-300 de `expediente_detalle.py` — cópialo). Implementar
  `_eliminar_obligacion(obligacion_id)`:

```python
def _eliminar_obligacion(self, obligacion_id: int) -> None:
    session = session_module.get_session()
    hijas = (
        session.query(Obligacion)
        .filter(Obligacion.obligacion_padre_id == obligacion_id)
        .all()
    )
    mensaje = "¿Eliminar esta obligación? Esta acción no se puede deshacer."
    if hijas:
        mensaje += f" Esto también eliminará sus {len(hijas)} cuota(s) generada(s)."
    respuesta = QMessageBox.question(self, "Eliminar obligación", mensaje)
    if respuesta != QMessageBox.StandardButton.Yes:
        session.close()
        return

    for hija in hijas:
        session.delete(hija)
    obligacion = session.get(Obligacion, obligacion_id)
    session.delete(obligacion)
    session.commit()
    session.close()
    self._refrescar_obligaciones()
```

- [ ] **Step 6: Correr los 3 tests, confirmar que pasan. Suite completa + ruff.**
- [ ] **Step 7: Commit** — `feat(sprint60): eliminar obligacion con cascada de cuotas hijas`

### Task 2: Editar y eliminar Abono

**Files:**
- Modify: `app/views/abonos.py` (`AbonoFormDialog` acepta `abono_id` opcional para editar)
- Modify: `app/views/expediente_detalle.py`
- Test: `tests/views/test_abonos.py`, `tests/views/test_expediente_detalle.py`

- [ ] **Step 1: Test que falla (editar)** — `AbonoFormDialog(obligacion_id=X, parent=..., abono_id=Y)`
  precarga los campos del abono `Y` existente; guardar actualiza esa fila en vez de crear una nueva.
- [ ] **Step 2: Correr, confirmar que falla.**
- [ ] **Step 3: Implementar `abono_id` opcional en `AbonoFormDialog`** — mismo patrón que
  `ObligacionFormDialog(obligacion_id=...)`/`EventoLaboralFormDialog(evento_id=...)` ya soportan (revisa
  su `__init__` y `guardar()` para copiar la forma exacta: si `abono_id` es `None` crea, si no,
  actualiza la fila existente).
- [ ] **Step 4: Correr, confirmar que pasa.**
- [ ] **Step 5: Test que falla (columnas de la tabla)** — `tabla_abonos` tiene 5 columnas
  (`["Fecha", "Monto", "Referencia", "Editar", "Eliminar"]`), con botones por fila.
- [ ] **Step 6: Correr, confirmar que falla.**
- [ ] **Step 7: Implementar en `expediente_detalle.py`** — ampliar `tabla_abonos` a 5 columnas, agregar
  `_editar_abono(abono_id)` (abre `AbonoFormDialog` con `abono_id`) y `_eliminar_abono(abono_id)` (mismo
  patrón de confirmación + `session.delete` + `commit` que `_eliminar_evento_laboral`).
- [ ] **Step 8: Correr, confirmar que pasa. Suite completa + ruff.**
- [ ] **Step 9: Commit** — `feat(sprint60): editar y eliminar abonos`

**Definición de Hecho del Sprint 60:** ver spec.

---

## Cierre de cada sprint

Antes de fusionar cada sprint a `main`: crear su entrada en `Pendientes.md` (texto basado en este plan +
la spec, mismo formato que los Sprints 52-55: Prioridad, Depende de, Hallazgos/Contexto, Código nuevo a
crear, Alcance excluido, Definición de Hecho), implementar vía Subagent-Driven Development en un
worktree aislado (implementador + revisor de spec + revisor de calidad por task, re-revisión si hay
hallazgos), correr la suite completa y `ruff check .`, marcar ✅ Completado con nota de cierre, actualizar
`CHANGELOG.md`, y fusionar a `main` — mismo procedimiento exacto que ya se usó para los Sprints 52-55.
