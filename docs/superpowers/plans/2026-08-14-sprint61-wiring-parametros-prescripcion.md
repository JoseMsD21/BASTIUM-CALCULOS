# Sprint 61 — Conectar los parámetros de prescripción/caducidad sin wiring a pantallas reales — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Conectar los 18 parámetros de prescripción/caducidad/tasa sin wiring (`docs/Pendientes.md`, Sprint 61) a pantallas reales, mediante un campo genérico único en `Obligacion`, la generalización de la alerta ya existente en el Dashboard, y un fallback automático de tasa para `CIVIL_ANNUAL_RATE`.

**Architecture:** Un campo nuevo `Obligacion.tipo_accion_proceso` (string nullable) unifica los dos catálogos existentes (`TipoAccion` de prescripción y las claves de `PLAZOS_CADUCIDAD_MESES_CONOCIDOS`). `app/services/areas_parametro.py` gana una función que filtra las opciones visibles por área reutilizando el mapeo ya aprobado del Sprint 57. `ObligacionFormDialog` gana un combo que guarda ese valor. `dashboard.py` deja de asumir `TipoAccion.EJECUTIVA` fijo y resuelve prescripción o caducidad según el campo de cada obligación. `CivilFamiliaStrategy` cae a `CIVIL_ANNUAL_RATE` cuando `tasa_efectiva_anual` es 0.

**Tech Stack:** Python, SQLAlchemy (Mapped/mapped_column), PySide6, pytest, sqlite3 (migraciones manuales).

**Spec:** `docs/superpowers/specs/2026-08-14-sprint61-wiring-parametros-prescripcion-design.md`

---

### Task 1: Migración — columna `tipo_accion_proceso` en `obligaciones`

**Files:**
- Create: `scripts/migrate_tipo_accion_proceso.py`
- Test: `tests/scripts/test_migrate_tipo_accion_proceso.py`
- Modify: `database/database.py` (dentro de `aplicar_migraciones_pendientes`, ver imports alfabéticos ~línea 28-52 y llamadas ~línea 53-85)

- [ ] **Step 1: Escribir el test que falla**

```python
import sqlite3

import pytest

from scripts.migrate_tipo_accion_proceso import migrar


@pytest.fixture
def db_sin_columna(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY, concepto TEXT)")
    con.execute("INSERT INTO obligaciones (id, concepto) VALUES (1, 'Capital pagare')")
    con.commit()
    con.close()
    return db_path


def test_migrar_agrega_la_columna_y_retorna_true(db_sin_columna):
    aplicada = migrar(db_sin_columna)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columna)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert "tipo_accion_proceso" in columnas


def test_migrar_preserva_las_filas_existentes_con_columna_nula(db_sin_columna):
    migrar(db_sin_columna)

    con = sqlite3.connect(db_sin_columna)
    fila = con.execute(
        "SELECT concepto, tipo_accion_proceso FROM obligaciones WHERE id = 1"
    ).fetchone()
    con.close()
    assert fila == ("Capital pagare", None)


def test_migrar_es_idempotente_segunda_corrida_retorna_false(db_sin_columna):
    primera = migrar(db_sin_columna)
    segunda = migrar(db_sin_columna)
    assert primera is True
    assert segunda is False
```

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pytest tests/scripts/test_migrate_tipo_accion_proceso.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'scripts.migrate_tipo_accion_proceso'`

- [ ] **Step 3: Crear el script de migración**

```python
"""Migracion de esquema (Sprint 61): agrega la columna tipo_accion_proceso a
la tabla obligaciones. Idempotente -- verifica con PRAGMA table_info antes de
alterar, mismo patron que scripts/migrate_aplica_indexacion_ipc.py. Columna
nullable sin DEFAULT: una obligacion sin este campo simplemente no se alerta
de prescripcion/caducidad no-ejecutiva (comportamiento identico al de hoy),
no es un caso de error -- ver docs/superpowers/specs/
2026-08-14-sprint61-wiring-parametros-prescripcion-design.md."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega la columna tipo_accion_proceso si no existe.
    Retorna True si aplico el ALTER TABLE, False si la columna ya existia."""
    con = sqlite3.connect(db_path)
    try:
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        if "tipo_accion_proceso" in columnas:
            return False
        con.execute("ALTER TABLE obligaciones ADD COLUMN tipo_accion_proceso TEXT")
        con.commit()
        return True
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columna tipo_accion_proceso agregada a obligaciones.")
    else:
        print("La columna tipo_accion_proceso ya existia, no se hizo nada.")
```

- [ ] **Step 4: Correr el test y confirmar que pasa**

Run: `pytest tests/scripts/test_migrate_tipo_accion_proceso.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Registrar la migración en `aplicar_migraciones_pendientes`**

En `database/database.py`, agregar al bloque de imports (orden alfabético, junto a los demás `from scripts.migrate_X import migrar as migrar_x`):

```python
    from scripts.migrate_tipo_accion_proceso import migrar as migrar_tipo_accion_proceso
```

Y agregar la llamada al final de la secuencia de llamadas (junto a `migrar_es_smmlv(ruta)`):

```python
    migrar_tipo_accion_proceso(ruta)
```

- [ ] **Step 6: Confirmar que la suite completa de migraciones sigue en verde**

Run: `pytest tests/database/test_migrations.py tests/scripts/ -v`
Expected: PASS, sin regresiones

- [ ] **Step 7: Commit**

```bash
git add scripts/migrate_tipo_accion_proceso.py tests/scripts/test_migrate_tipo_accion_proceso.py database/database.py
git commit -m "feat(sprint61): migración tipo_accion_proceso en obligaciones"
```

---

### Task 2: Columna nueva en el modelo `Obligacion`

**Files:**
- Modify: `database/models.py` (clase `Obligacion`, junto a `obligacion_padre_id`, ~línea 183)
- Test: `tests/database/test_models.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_obligacion_admite_tipo_accion_proceso_nulo_y_con_valor(session_factory):
    session = session_factory()
    expediente = _crear_expediente_helper(session)  # usar el helper ya existente en el archivo
    obligacion_sin = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Capital pagare",
        fecha_origen=date(2024, 1, 1),
        valor=Decimal("1000000.00"),
    )
    obligacion_con = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Cheque impago",
        fecha_origen=date(2024, 1, 1),
        valor=Decimal("500000.00"),
        tipo_accion_proceso="CHEQUES",
    )
    session.add_all([obligacion_sin, obligacion_con])
    session.commit()

    assert obligacion_sin.tipo_accion_proceso is None
    assert obligacion_con.tipo_accion_proceso == "CHEQUES"
```

Nota para el implementador: usar el fixture/helper de sesión y creación de expediente ya existente en `tests/database/test_models.py` (seguir el patrón de los tests vecinos en ese archivo, no reinventar el setup).

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pytest tests/database/test_models.py::test_obligacion_admite_tipo_accion_proceso_nulo_y_con_valor -v`
Expected: FAIL con `TypeError: 'tipo_accion_proceso' is an invalid keyword argument for Obligacion`

- [ ] **Step 3: Agregar la columna al modelo**

En `database/models.py`, dentro de la clase `Obligacion`, inmediatamente después de la línea de `obligacion_padre_id` (~línea 183) y antes del bloque de `relationship()` (~línea 185):

```python
    # Sprint 61: tipo de accion (prescripcion, TipoAccion.value) o de proceso
    # (caducidad, clave de PLAZOS_CADUCIDAD_MESES_CONOCIDOS) aplicable a esta
    # obligacion -- nulo por defecto, no cambia el comportamiento de ninguna
    # obligacion existente. Ver areas_parametro.opciones_tipo_accion_proceso_por_area.
    tipo_accion_proceso: Mapped[str | None] = mapped_column(String(60), nullable=True)
```

- [ ] **Step 4: Correr el test y confirmar que pasa**

Run: `pytest tests/database/test_models.py::test_obligacion_admite_tipo_accion_proceso_nulo_y_con_valor -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add database/models.py tests/database/test_models.py
git commit -m "feat(sprint61): campo tipo_accion_proceso en el modelo Obligacion"
```

---

### Task 3: Catálogo unificado por área en `areas_parametro.py`

**Files:**
- Modify: `app/services/areas_parametro.py`
- Test: `tests/services/test_areas_parametro.py`

- [ ] **Step 1: Escribir el test que falla**

```python
from app.services.areas_parametro import opciones_tipo_accion_proceso_por_area
from database.models import AreaDerecho


def test_opciones_civil_familia_incluye_ejecutiva_y_ordinaria_no_cambiaria():
    valores = {valor for valor, _ in opciones_tipo_accion_proceso_por_area(AreaDerecho.CIVIL_FAMILIA)}
    assert "ejecutiva" in valores
    assert "ordinaria" in valores
    assert "cambiaria_directa" not in valores


def test_opciones_comercial_incluye_cambiarias_y_caducidades_no_ordinaria():
    valores = {valor for valor, _ in opciones_tipo_accion_proceso_por_area(AreaDerecho.COMERCIAL)}
    assert "cambiaria_directa" in valores
    assert "cambiaria_regreso_tenedor" in valores
    assert "cambiaria_regreso_entre_obligados" in valores
    assert "CHEQUES" in valores
    assert "IMPUGNACION_INEFICACIA_SOCIETARIA" in valores
    assert "ordinaria" not in valores


def test_opciones_honorarios_incluye_solo_su_prescripcion_propia():
    valores = {valor for valor, _ in opciones_tipo_accion_proceso_por_area(AreaDerecho.HONORARIOS)}
    assert "honorarios_profesionales" in valores
    assert "CHEQUES" not in valores


def test_cada_opcion_trae_una_etiqueta_legible_no_vacia():
    for valor, etiqueta in opciones_tipo_accion_proceso_por_area(AreaDerecho.COMERCIAL):
        assert etiqueta.strip() != ""
```

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pytest tests/services/test_areas_parametro.py -v`
Expected: FAIL con `ImportError: cannot import name 'opciones_tipo_accion_proceso_por_area'`

- [ ] **Step 3: Implementar la función en `areas_parametro.py`**

Agregar al final del archivo (después de `deserializar_areas`, y agregar los imports nuevos junto a los existentes al inicio del archivo):

```python
from app.engine.temporal.prescripcion import (
    CLAVE_POR_TIPO_ACCION,
    PLAZOS_CADUCIDAD_MESES_CONOCIDOS,
    TipoAccion,
)

_ETIQUETA_TIPO_ACCION: dict[TipoAccion, str] = {
    TipoAccion.EJECUTIVA: "Prescripción ejecutiva",
    TipoAccion.ORDINARIA: "Prescripción ordinaria",
    TipoAccion.HONORARIOS_PROFESIONALES: "Prescripción de honorarios profesionales",
    TipoAccion.CAMBIARIA_DIRECTA: "Prescripción cambiaria directa",
    TipoAccion.CAMBIARIA_REGRESO_TENEDOR: "Prescripción cambiaria de regreso (tenedor)",
    TipoAccion.CAMBIARIA_REGRESO_ENTRE_OBLIGADOS: (
        "Prescripción cambiaria de regreso (entre obligados)"
    ),
}

_ETIQUETA_CADUCIDAD: dict[str, str] = {
    "IMPUGNACION_INEFICACIA_SOCIETARIA": "Caducidad: impugnación de ineficacia societaria",
    "CHEQUES": "Caducidad: cheques",
    "ENRIQUECIMIENTO_SIN_CAUSA": "Caducidad: enriquecimiento sin causa",
    "TRANSPORTE": "Caducidad: transporte",
    "SEGURO_ORDINARIA": "Caducidad: seguro (ordinaria)",
    "SEGURO_EXTRAORDINARIA": "Caducidad: seguro (extraordinaria)",
    "IMPUGNACION_ACTAS_SOCIALES": "Caducidad: impugnación de actas sociales",
}


def opciones_tipo_accion_proceso_por_area(area: AreaDerecho) -> list[tuple[str, str]]:
    """(valor_a_guardar, etiqueta) para el combo "Tipo de acción/proceso" del
    formulario de Obligacion (Sprint 61), filtrado a lo relevante para `area`
    reutilizando el mapeo ya aprobado AREA_UNIDAD_POR_CLAVE (Sprint 57).
    `valor_a_guardar` es TipoAccion.value (prescripcion, minuscula) o la clave
    cruda de PLAZOS_CADUCIDAD_MESES_CONOCIDOS (caducidad, mayuscula) -- no hay
    colision posible entre los dos catalogos."""
    opciones: list[tuple[str, str]] = []
    for tipo_accion, clave in CLAVE_POR_TIPO_ACCION.items():
        areas_clave, _ = AREA_UNIDAD_POR_CLAVE.get(clave, ([], ""))
        if area in areas_clave:
            opciones.append((tipo_accion.value, _ETIQUETA_TIPO_ACCION[tipo_accion]))
    for clave_caducidad in PLAZOS_CADUCIDAD_MESES_CONOCIDOS:
        clave_parametro = f"CADUCIDAD_{clave_caducidad}_MESES"
        areas_clave, _ = AREA_UNIDAD_POR_CLAVE.get(clave_parametro, ([], ""))
        if area in areas_clave:
            opciones.append((clave_caducidad, _ETIQUETA_CADUCIDAD[clave_caducidad]))
    return opciones
```

Actualizar también el comentario de módulo (líneas 19-24 del archivo) que hoy dice "sin wiring a produccion todavia" para las 12 claves de prescripción/caducidad no-ejecutiva — ya no aplica una vez cerrado este sprint; ajustar el texto para reflejar que se conectan vía `opciones_tipo_accion_proceso_por_area` (Sprint 61).

- [ ] **Step 4: Correr el test y confirmar que pasa**

Run: `pytest tests/services/test_areas_parametro.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add app/services/areas_parametro.py tests/services/test_areas_parametro.py
git commit -m "feat(sprint61): catálogo unificado de tipo_accion_proceso por área"
```

---

### Task 4: Combo nuevo en `ObligacionFormDialog`

**Files:**
- Modify: `app/views/obligaciones.py` (constructor ~línea 66-161, carga de valores existentes ~línea 627, las 3 rutas de guardado ~línea 923-966, 1250, 1326)
- Test: `tests/views/test_obligaciones.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_guarda_y_recupera_tipo_accion_proceso(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)  # usar el helper ya existente en el archivo
    expediente = _crear_expediente_helper(area=AreaDerecho.COMERCIAL)

    dialogo = ObligacionFormDialog(expediente_id=expediente.id, area="COMERCIAL")
    qtbot.addWidget(dialogo)

    indice = dialogo.combo_tipo_accion_proceso.findData("CHEQUES")
    assert indice >= 0, "CHEQUES debe estar disponible para Comercial"
    dialogo.combo_tipo_accion_proceso.setCurrentIndex(indice)

    dialogo.campo_concepto.setText("Cheque impago")
    dialogo.campo_valor.setText("500000")
    dialogo.campo_fecha_origen.setDate(QDate(2024, 1, 1))
    dialogo.guardar()

    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(concepto="Cheque impago").one()
    assert obligacion.tipo_accion_proceso == "CHEQUES"
    session.close()


def test_combo_tipo_accion_proceso_no_ofrece_opciones_de_otra_area(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    expediente = _crear_expediente_helper(area=AreaDerecho.HONORARIOS)

    dialogo = ObligacionFormDialog(expediente_id=expediente.id, area="HONORARIOS")
    qtbot.addWidget(dialogo)

    assert dialogo.combo_tipo_accion_proceso.findData("CHEQUES") == -1
    assert dialogo.combo_tipo_accion_proceso.findData("honorarios_profesionales") >= 0
```

Nota para el implementador: adaptar los nombres de los helpers (`_sesion_en_memoria`, `_crear_expediente_helper`, nombres exactos de `campo_concepto`/`campo_valor`/`campo_fecha_origen`) a los que ya existen en `tests/views/test_obligaciones.py` — seguir el patrón de los tests vecinos en ese archivo para el setup de sesión en memoria y creación de expediente/diálogo.

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pytest tests/views/test_obligaciones.py -k tipo_accion_proceso -v`
Expected: FAIL con `AttributeError: 'ObligacionFormDialog' object has no attribute 'combo_tipo_accion_proceso'`

- [ ] **Step 3: Agregar el combo, poblarlo por área y guardarlo/cargarlo**

En el constructor de `ObligacionFormDialog` (`app/views/obligaciones.py`), junto a la creación de `combo_tipo_reajuste_anual` (~línea 151-161), agregar:

```python
        self.combo_tipo_accion_proceso = QComboBox()
        self.combo_tipo_accion_proceso.addItem("(Ninguno)", userData=None)
        for valor, etiqueta in opciones_tipo_accion_proceso_por_area(AreaDerecho(self._area)):
            self.combo_tipo_accion_proceso.addItem(etiqueta, userData=valor)
        self.combo_tipo_accion_proceso.setToolTip(
            "Tipo de acción (prescripción) o de proceso (caducidad) aplicable a esta "
            "obligación. Determina qué plazo usa la alerta de vencimiento del Dashboard. "
            "Opcional: si se deja en (Ninguno), la obligación no se alerta."
        )
```

Agregar el import correspondiente al inicio del archivo:

```python
from app.services.areas_parametro import opciones_tipo_accion_proceso_por_area
```

Agregar la fila al formulario, junto a donde se agrega `combo_tipo_reajuste_anual` al layout (mismo `QFormLayout`):

```python
        self.layout_datos_basicos.addRow("Tipo de acción/proceso", self.combo_tipo_accion_proceso)
```

En la carga de valores de una obligación existente (junto al bloque que hace `self.campo_tasa.setText(...)`, ~línea 627):

```python
        indice_tipo_accion = self.combo_tipo_accion_proceso.findData(
            obligacion.tipo_accion_proceso
        )
        self.combo_tipo_accion_proceso.setCurrentIndex(max(indice_tipo_accion, 0))
```

En las 3 rutas de guardado (`guardar()` genérica ~línea 923-966, `_guardar_laboral()` ~línea 1250, `_guardar_tributario()` ~línea 1326), agregar el campo al kwargs de construcción/actualización de `Obligacion`:

```python
            tipo_accion_proceso=self.combo_tipo_accion_proceso.currentData(),
```

- [ ] **Step 4: Correr el test y confirmar que pasa**

Run: `pytest tests/views/test_obligaciones.py -k tipo_accion_proceso -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Correr toda la suite de `test_obligaciones.py` para confirmar cero regresión**

Run: `pytest tests/views/test_obligaciones.py -v`
Expected: PASS, todos los tests existentes siguen en verde

- [ ] **Step 6: Commit**

```bash
git add app/views/obligaciones.py tests/views/test_obligaciones.py
git commit -m "feat(sprint61): combo tipo_accion_proceso en ObligacionFormDialog"
```

---

### Task 5: Generalizar la alerta del Dashboard

**Files:**
- Modify: `app/views/dashboard.py` (método `_refrescar_alertas_vencimiento`, ~línea 203-257)
- Test: `tests/views/test_dashboard.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_dashboard_alerta_prescripcion_ordinaria_no_solo_ejecutiva(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro(session, "PRESCRIPCION_ORDINARIA_MESES", Decimal("120"))
    expediente = _crear_expediente(session, "2026-020", AreaDerecho.CIVIL_FAMILIA)
    _crear_obligacion(
        session, expediente.id, date(2016, 1, 4), tipo_accion_proceso="ordinaria"
    )

    fecha_limite = calcular_prescripcion(date(2016, 1, 4), TipoAccion.ORDINARIA)
    hoy = fecha_limite - timedelta(days=30)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)
    view.refrescar(hoy=hoy)

    assert view.tabla_alertas.rowCount() == 1
    assert view.tabla_alertas.item(0, 2).text() == fecha_limite.isoformat()


def test_dashboard_alerta_caducidad_cheques(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro(session, "CADUCIDAD_CHEQUES_MESES", Decimal("6"))
    expediente = _crear_expediente(session, "2026-021", AreaDerecho.COMERCIAL)
    _crear_obligacion(
        session, expediente.id, date(2026, 3, 1), tipo_accion_proceso="CHEQUES"
    )

    fecha_limite = calcular_caducidad(date(2026, 3, 1), "CHEQUES")
    hoy = fecha_limite - timedelta(days=10)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)
    view.refrescar(hoy=hoy)

    assert view.tabla_alertas.rowCount() == 1
    assert view.tabla_alertas.item(0, 2).text() == fecha_limite.isoformat()
```

Nota para el implementador: usar los helpers `_sembrar_parametro_prescripcion_ejecutiva`/`_crear_expediente`/`_crear_obligacion` ya existentes en `tests/views/test_dashboard.py` (líneas 44-56 y vecinas) como base — `_sembrar_parametro` generaliza el existente para aceptar `clave`/`valor` arbitrarios, y `_crear_obligacion` gana un parámetro opcional `tipo_accion_proceso: str | None = None` que pasa directo al constructor de `Obligacion`. Ajustar esos helpers en el mismo archivo si hace falta, siguiendo su patrón actual.

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pytest tests/views/test_dashboard.py -k "ordinaria_no_solo_ejecutiva or caducidad_cheques" -v`
Expected: FAIL — la alerta no aparece porque el método sigue asumiendo `TipoAccion.EJECUTIVA` fijo

- [ ] **Step 3: Generalizar `_refrescar_alertas_vencimiento`**

Agregar el import de `calcular_caducidad` y `PLAZOS_CADUCIDAD_MESES_CONOCIDOS` (`app/engine/temporal/prescripcion.py`) junto al import ya existente de `calcular_prescripcion`/`CLAVE_POR_TIPO_ACCION`/`TipoAccion` en `dashboard.py`.

Agregar, en el mismo módulo `dashboard.py` (fuera de la clase, junto a otras constantes de módulo):

```python
_VALORES_TIPO_ACCION = {tipo.value for tipo in TipoAccion}


def _fecha_limite_obligacion(obligacion) -> date | None:
    """Resuelve la fecha limite de prescripcion/caducidad de `obligacion` segun
    su tipo_accion_proceso (Sprint 61). Si es None, se asume TipoAccion.EJECUTIVA
    -- mismo comportamiento que antes de este sprint (unico caso conectado).
    Retorna None si el tipo no es reconocido o el parametro no esta configurado
    (mismo criterio que el ParametroNoDisponibleError que ya se ignoraba)."""
    tipo = obligacion.tipo_accion_proceso
    try:
        if tipo is None:
            return calcular_prescripcion(obligacion.fecha_origen, TipoAccion.EJECUTIVA)
        if tipo in _VALORES_TIPO_ACCION:
            return calcular_prescripcion(obligacion.fecha_origen, TipoAccion(tipo))
        if tipo in PLAZOS_CADUCIDAD_MESES_CONOCIDOS:
            return calcular_caducidad(obligacion.fecha_origen, tipo)
        return None
    except ParametroNoDisponibleError:
        return None
```

Reemplazar el cuerpo de `_refrescar_alertas_vencimiento` (~línea 203-257) por:

```python
    def _refrescar_alertas_vencimiento(
        self, expedientes: list[Expediente], hoy: date
    ) -> None:
        """Alerta si la prescripcion/caducidad aplicable (segun
        `obligacion.tipo_accion_proceso`, o TipoAccion.EJECUTIVA por defecto si
        es None -- Sprint 61 generaliza lo que antes solo cubria EJECUTIVA) de
        alguna obligacion no pagada cae dentro de los proximos
        DIAS_ALERTA_VENCIMIENTO dias, o ya vencio."""
        limite = hoy + timedelta(days=DIAS_ALERTA_VENCIMIENTO)
        alertas = []
        with cache_de_liquidacion():
            claves_necesarias = {CLAVE_POR_TIPO_ACCION[TipoAccion.EJECUTIVA]}
            for expediente in expedientes:
                for obligacion in expediente.obligaciones:
                    tipo = obligacion.tipo_accion_proceso
                    if tipo in _VALORES_TIPO_ACCION:
                        claves_necesarias.add(CLAVE_POR_TIPO_ACCION[TipoAccion(tipo)])
                    elif tipo in PLAZOS_CADUCIDAD_MESES_CONOCIDOS:
                        claves_necesarias.add(f"CADUCIDAD_{tipo}_MESES")
            for clave in claves_necesarias:
                precargar_parametro(clave)

            for expediente in expedientes:
                for obligacion in expediente.obligaciones:
                    if obligacion.pagada:
                        continue
                    fecha_limite = _fecha_limite_obligacion(obligacion)
                    if fecha_limite is None or fecha_limite > limite:
                        continue
                    dias_restantes = (fecha_limite - hoy).days
                    if dias_restantes < 0:
                        estado = "Vencido"
                    else:
                        estado = f"Vence en {dias_restantes} días"
                    alertas.append((expediente, obligacion, fecha_limite, estado))

        alertas.sort(key=lambda item: item[2])

        self.tabla_alertas.setRowCount(len(alertas))
        self._expediente_ids_por_fila_alerta = []
        for fila, (expediente, obligacion, fecha_limite, estado) in enumerate(alertas):
            self.tabla_alertas.setItem(fila, 0, QTableWidgetItem(expediente.radicado))
            self.tabla_alertas.setItem(fila, 1, QTableWidgetItem(obligacion.concepto))
            self.tabla_alertas.setItem(fila, 2, QTableWidgetItem(fecha_limite.isoformat()))
            self.tabla_alertas.setItem(fila, 3, QTableWidgetItem(estado))
            self._expediente_ids_por_fila_alerta.append(expediente.id)
```

Nota: el filtro `fecha_limite > limite` reemplaza al `if fecha_limite <= limite:` que envolvía el resto del cuerpo en la versión original — mismo efecto (`continue` cuando no aplica), reescrito para que quepa el chequeo adicional de `fecha_limite is None`.

- [ ] **Step 4: Correr los tests nuevos y confirmar que pasan**

Run: `pytest tests/views/test_dashboard.py -k "ordinaria_no_solo_ejecutiva or caducidad_cheques" -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Correr toda la suite de `test_dashboard.py` para confirmar cero regresión (en particular el caso EJECUTIVA original)**

Run: `pytest tests/views/test_dashboard.py -v`
Expected: PASS, incluyendo `test_dashboard_muestra_alerta_de_obligacion_proxima_a_prescribir`

- [ ] **Step 6: Commit**

```bash
git add app/views/dashboard.py tests/views/test_dashboard.py
git commit -m "feat(sprint61): generalizar alerta de vencimiento a los 12 tipos nuevos"
```

---

### Task 6: `CIVIL_ANNUAL_RATE` como fallback silencioso

**Files:**
- Modify: `app/services/area_strategy.py` (`CivilFamiliaStrategy._construir_rate_provider_obligacion`, ~línea 429-442)
- Test: `tests/services/test_area_strategy.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_civil_familia_usa_civil_annual_rate_cuando_tasa_es_cero(monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro(session, "CIVIL_ANNUAL_RATE", Decimal("6.00"))
    session.close()

    obligacion = _obligacion_civil_familia_helper(
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_origen=date(2024, 1, 1),
    )
    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 1, 1)
    )

    # Con 6% anual sobre 1 año, el interes generado debe ser > 0 (equivalente
    # al mismo calculo que produce un interes pactado explicito del 6%, no 0).
    saldo = resultado.final_balance()
    assert saldo.interest > Decimal("0.00")


def test_civil_familia_respeta_tasa_propia_cuando_no_es_cero(monkeypatch):
    _sesion_en_memoria(monkeypatch)
    obligacion_con_tasa = _obligacion_civil_familia_helper(
        tasa_efectiva_anual=Decimal("12.00"),
        fecha_origen=date(2024, 1, 1),
    )
    obligacion_sin_parametro_cargado = obligacion_con_tasa
    # Sin sembrar CIVIL_ANNUAL_RATE en Parametros: si la obligacion ya trae su
    # propia tasa (12%), get_parametro no deberia ni consultarse -- este test
    # falla con ParametroNoDisponibleError si el fallback se activa quando no debe.
    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_sin_parametro_cargado],
        abonos=[],
        fecha_corte=date(2025, 1, 1),
    )
    assert resultado.final_balance().interest > Decimal("0.00")
```

Nota para el implementador: usar los helpers de sesión en memoria/siembra de parámetro y de construcción de `Obligacion` Civil/Familia ya existentes en `tests/services/test_area_strategy.py` (adaptar nombres exactos al patrón del archivo).

- [ ] **Step 2: Correr el test y confirmar que falla**

Run: `pytest tests/services/test_area_strategy.py -k civil_annual_rate -v`
Expected: FAIL — con tasa 0 el interés generado es 0 (comportamiento actual, sin fallback)

- [ ] **Step 3: Implementar el fallback**

Reemplazar `_construir_rate_provider_obligacion` en `CivilFamiliaStrategy` (`area_strategy.py:429-442`):

```python
    def _construir_rate_provider_obligacion(
        self, obligacion, fecha_corte: date
    ) -> MemoryRateProvider:
        fecha_inicio = (
            obligacion.fecha_origen
            if obligacion.tipo.value == "PUNTUAL"
            else obligacion.fecha_inicio
        )
        tasa = obligacion.tasa_efectiva_anual
        source = "Tasa pactada en la obligación (Art. 1617 C.C.)"
        if not tasa:
            tasa = get_parametro("CIVIL_ANNUAL_RATE", fecha_corte)
            source = "Tasa legal civil por defecto (CIVIL_ANNUAL_RATE, Art. 1617 C.C.)"
        return self._rate_provider_tasa_plana(
            fecha_inicio, fecha_corte, tasa, source=source
        )
```

Agregar el import de `get_parametro` en `area_strategy.py` si no está ya presente:

```python
from app.services.parametro_service import get_parametro
```

- [ ] **Step 4: Correr los tests y confirmar que pasan**

Run: `pytest tests/services/test_area_strategy.py -k civil_annual_rate -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Correr toda la suite de `test_area_strategy.py` para confirmar cero regresión**

Run: `pytest tests/services/test_area_strategy.py -v`
Expected: PASS, todos los tests existentes de Civil/Familia (con tasa propia > 0) siguen igual

- [ ] **Step 6: Commit**

```bash
git add app/services/area_strategy.py tests/services/test_area_strategy.py
git commit -m "feat(sprint61): fallback silencioso a CIVIL_ANNUAL_RATE cuando tasa es 0"
```

---

### Task 7: Documentación (README, GUIA_USUARIO, CHANGELOG)

**Files:**
- Modify: `README.md`
- Modify: `docs/GUIA_USUARIO.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Documentar en `docs/GUIA_USUARIO.md`**

Agregar una sección nueva (siguiendo el estilo/nivel de detalle de las secciones de Parámetros y del formulario de Obligación ya existentes) que explique: el combo "Tipo de acción/proceso" en el formulario de obligación (qué hace, que es opcional, que alimenta la alerta del Dashboard); que el Dashboard ahora alerta también prescripción ordinaria/honorarios/cambiarias y las 7 caducidades comerciales, no solo la ejecutiva; que Civil/Familia usa automáticamente la tasa legal (`CIVIL_ANNUAL_RATE`) cuando se deja la tasa pactada en 0.

- [ ] **Step 2: Documentar en `README.md`**

En la sección "Estado actual" (o equivalente donde se listan funciones por sprint), agregar una línea resumiendo el Sprint 61: wiring de los 18 parámetros de prescripción/caducidad/tasa a pantallas reales.

- [ ] **Step 3: Agregar entrada en `CHANGELOG.md`**

Bajo un encabezado `### Added` (o el que corresponda a la fecha de cierre), agregar una entrada describiendo el campo nuevo `tipo_accion_proceso`, la generalización de la alerta del Dashboard, y el fallback de `CIVIL_ANNUAL_RATE`.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/GUIA_USUARIO.md CHANGELOG.md
git commit -m "docs(sprint61): documentar wiring de parámetros de prescripción/caducidad"
```

---

## Definición de Hecho (verificación final)

- [ ] Suite completa en verde: `pytest`
- [ ] `ruff check .` limpio
- [ ] Las 12 claves de prescripción/caducidad + `CIVIL_ANNUAL_RATE` son alcanzables desde `ObligacionFormDialog` (el campo) y el Dashboard (la alerta) o la resolución automática de tasa.
- [ ] Ninguna obligación existente (creada antes de este sprint, con `tipo_accion_proceso = NULL` y `tasa_efectiva_anual != 0`) cambia de comportamiento.
