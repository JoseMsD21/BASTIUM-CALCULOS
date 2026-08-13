# Parámetros: editar/eliminar de usuario, vigencia clara, unidad y tooltips Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir editar/eliminar valores de parámetro creados por un usuario (nunca los de sistema), aclarar en la UI cuándo aplica "Vigente hasta", convertir "Unidad" en un desplegable con opción "Otros", y homologar tooltips ⓘ en todo el formulario y la tabla de Parámetros.

**Architecture:** Todo el trabajo vive en 3 archivos: `database/models.py` (columna nueva `creado_por_sistema`), `app/services/parametro_service.py` (servicio: `editar_valor`/`eliminar_valor` nuevos, `agregar_valor` ajustado) y `app/views/configuracion.py` (`ParametroFormDialog` con modo edición, `HistorialParametroDialog` con Editar/Eliminar por fila, `ParametrosView` con tooltips de columna). Una migración nueva (`scripts/migrate_creado_por_sistema.py`) agrega la columna y hace backfill de las filas ya sembradas por sistema.

**⚠️ Este plan es prerequisito de otro:** el plan "Restablecer datos de fábrica" (`docs/superpowers/plans/2026-08-13-restablecer-datos-fabrica.md`) depende de la columna `creado_por_sistema` agregada en el Task 1 de este plan. Avisar/mergear este plan (al menos su Task 1) antes de que el otro llegue a su Task 2.

**Tech Stack:** SQLAlchemy ORM + `sqlite3` crudo (migración), PySide6 (QComboBox/QCheckBox/QDialog), pytest + pytest-qt.

---

### Task 1: Migración de esquema — columna `creado_por_sistema`

**Files:**
- Modify: `database/models.py:258-285` (clase `ParametroLegal`)
- Create: `scripts/migrate_creado_por_sistema.py`
- Modify: `database/database.py:28-109` (`aplicar_migraciones_pendientes`)
- Modify: `scripts/migrate_parametros_legales.py:92-103` (`_fila`)
- Modify: `scripts/migrate_ipc_variacion_anual.py:79-106` (`_sembrar`)
- Test: `tests/scripts/test_migrate_creado_por_sistema.py`

- [ ] **Step 1: Escribir el test que falla**

```python
import sqlite3
from datetime import date, datetime
from decimal import Decimal

import pytest

from scripts.migrate_creado_por_sistema import migrar


@pytest.fixture
def db_sin_columna(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute(
        """CREATE TABLE parametros_legales (
            id INTEGER PRIMARY KEY,
            clave TEXT,
            valor TEXT,
            vigente_desde TEXT,
            usuario TEXT,
            creado_en TEXT
        )"""
    )
    con.execute(
        "INSERT INTO parametros_legales (id, clave, valor, vigente_desde, usuario, creado_en) "
        "VALUES (1, 'SMLMV', '1000000', '2026-01-01', 'sistema', ?)",
        (datetime.now().isoformat(),),
    )
    con.execute(
        "INSERT INTO parametros_legales (id, clave, valor, vigente_desde, usuario, creado_en) "
        "VALUES (2, 'USURA_MULTIPLICADOR', '1.5', '2026-01-01', 'abogado1', ?)",
        (datetime.now().isoformat(),),
    )
    con.commit()
    con.close()
    return db_path


def test_migrar_agrega_la_columna_y_retorna_true(db_sin_columna):
    aplicada = migrar(db_sin_columna)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columna)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(parametros_legales)")}
    con.close()
    assert "creado_por_sistema" in columnas


def test_migrar_marca_como_sistema_solo_las_filas_con_usuario_sistema(db_sin_columna):
    migrar(db_sin_columna)

    con = sqlite3.connect(db_sin_columna)
    filas = dict(con.execute("SELECT id, creado_por_sistema FROM parametros_legales").fetchall())
    con.close()
    assert filas == {1: 1, 2: 0}


def test_migrar_es_idempotente_segunda_corrida_retorna_false(db_sin_columna):
    primera = migrar(db_sin_columna)
    segunda = migrar(db_sin_columna)
    assert primera is True
    assert segunda is False
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `pytest tests/scripts/test_migrate_creado_por_sistema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.migrate_creado_por_sistema'`

- [ ] **Step 3: Crear `scripts/migrate_creado_por_sistema.py`**

```python
"""Migracion de esquema: agrega la columna creado_por_sistema a
parametros_legales, para distinguir de verdad los valores sembrados por
scripts/migrate_parametros_legales.py y scripts/migrate_ipc_variacion_anual.py
(usuario='sistema' por convencion, pero eso era solo texto libre, nunca un
flag real) de los que un usuario carga desde ParametroFormDialog (Sprint
"Parametros: editar/eliminar de usuario"). Backfill: toda fila ya sembrada
con usuario='sistema' queda en creado_por_sistema=1; el resto en 0. Idempotente
-- verifica con PRAGMA table_info antes de alterar, mismo patron que
scripts/migrate_es_smmlv_laboral.py."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega la columna creado_por_sistema si no existe y hace el backfill
    por usuario='sistema'. Retorna True si aplico el ALTER TABLE, False si la
    columna ya existia (backfill no se repite en ese caso -- ya corrio la
    primera vez)."""
    con = sqlite3.connect(db_path)
    try:
        columnas_existentes = {
            fila[1] for fila in con.execute("PRAGMA table_info(parametros_legales)")
        }
        if "creado_por_sistema" in columnas_existentes:
            return False
        con.execute(
            "ALTER TABLE parametros_legales ADD COLUMN creado_por_sistema "
            "BOOLEAN NOT NULL DEFAULT 0"
        )
        con.execute(
            "UPDATE parametros_legales SET creado_por_sistema = 1 WHERE usuario = 'sistema'"
        )
        con.commit()
        return True
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columna creado_por_sistema agregada a parametros_legales.")
    else:
        print("La columna ya existia, no se hizo nada.")
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `pytest tests/scripts/test_migrate_creado_por_sistema.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Agregar la columna al modelo ORM**

En `database/models.py`, dentro de `class ParametroLegal` (después de la línea `unidad: Mapped[str | None] = mapped_column(String(30), nullable=True)`, línea 285):

```python
    # creado_por_sistema (Sprint "Parametros: editar/eliminar de usuario"):
    # True para las filas sembradas por scripts/migrate_parametros_legales.py
    # y scripts/migrate_ipc_variacion_anual.py, False para cualquier fila
    # creada desde ParametroFormDialog (la UI). Determina si la fila puede
    # editarse/eliminarse (ver editar_valor/eliminar_valor en
    # parametro_service.py) -- a diferencia de `usuario` (texto libre, solo
    # auditoria), este es un flag real que ningun camino de la UI puede
    # poner en True.
    creado_por_sistema: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
```

- [ ] **Step 6: Wirear la migración en `aplicar_migraciones_pendientes`**

En `database/database.py`, agregar el import junto a los demás `from scripts.migrate_*`:

```python
    from scripts.migrate_creado_por_sistema import migrar as migrar_creado_por_sistema
```

Y agregar la llamada junto a las demás, antes de `migrar_parametros_legales(ruta)` (debe correr antes: si una `bastium.db` real todavía no tiene la columna, `migrar_parametros_legales`/`migrar_ipc_variacion_anual` fallarían al construir `ParametroLegal(...)` con `creado_por_sistema=True` explícito, ver Steps 7-8, si la columna física no existe todavía):

```python
    migrar_creado_por_sistema(ruta)
    migrar_parametros_area_unidad(ruta)
    migrar_parametros_legales(ruta)
```

(la línea `migrar_parametros_area_unidad(ruta)` ya existe justo antes de `migrar_parametros_legales(ruta)` — solo se agrega `migrar_creado_por_sistema(ruta)` una línea antes de esa).

- [ ] **Step 7: Marcar como sistema las filas que siembra `scripts/migrate_parametros_legales.py`**

En `scripts/migrate_parametros_legales.py`, función `_fila` (líneas 92-103):

```python
def _fila(
    clave: str, valor: Decimal, vigente_desde: date, vigente_hasta: date | None = None
) -> ParametroLegal:
    return ParametroLegal(
        clave=clave,
        valor=valor,
        vigente_desde=vigente_desde,
        vigente_hasta=vigente_hasta,
        usuario=USUARIO_MIGRACION,
        motivo=MOTIVO_MIGRACION,
        creado_en=datetime.now(),
        creado_por_sistema=True,
    )
```

- [ ] **Step 8: Marcar como sistema las filas que siembra `scripts/migrate_ipc_variacion_anual.py`**

En `scripts/migrate_ipc_variacion_anual.py`, dentro de `_sembrar` (línea ~91-101), agregar `creado_por_sistema=True` al `ParametroLegal(...)`:

```python
            session.add(
                ParametroLegal(
                    clave=CLAVE,
                    valor=variacion,
                    vigente_desde=date(anio, 1, 1),
                    usuario=USUARIO_MIGRACION,
                    motivo=MOTIVO_MIGRACION,
                    creado_en=datetime.now(),
                    areas_derecho=areas_json,
                    unidad=unidad,
                    creado_por_sistema=True,
                )
            )
```

- [ ] **Step 9: Correr la suite completa relacionada para confirmar que nada se rompió**

Run: `pytest tests/scripts/ tests/services/test_parametro_service.py -q`
Expected: todos los tests pasan (los tests existentes de `migrate_parametros_legales`/`migrate_ipc_variacion_anual` no verifican `creado_por_sistema`, así que no deberían fallar; si alguno construye `ParametroLegal` a mano y compara campo por campo, revisar y ajustar si hace falta).

- [ ] **Step 10: Commit**

```bash
git add database/models.py database/database.py scripts/migrate_creado_por_sistema.py \
  scripts/migrate_parametros_legales.py scripts/migrate_ipc_variacion_anual.py \
  tests/scripts/test_migrate_creado_por_sistema.py
git commit -m "feat: agregar columna creado_por_sistema a parametros_legales con backfill"
```

---

### Task 2: `agregar_valor` marca `creado_por_sistema=False`; extraer validación compartida

**Files:**
- Modify: `app/services/parametro_service.py:1-16` (docstring del módulo)
- Modify: `app/services/parametro_service.py:491-563` (`agregar_valor`)
- Modify: `tests/services/test_parametro_service.py`

- [ ] **Step 1: Escribir el test que falla**

Este archivo importa cada función del servicio **dentro de cada test** (no a nivel de módulo — ver los `from app.services.parametro_service import agregar_valor` repetidos dentro de las funciones de test existentes), y hoy NO importa `AreaDerecho`. Primero agregar `AreaDerecho` al import ya existente de `database.models` en la cabecera del archivo (línea 9):

```python
from database.models import AreaDerecho, ParametroLegal
```

Luego agregar al final del archivo:

```python
def test_agregar_valor_marca_creado_por_sistema_false():
    from app.services.parametro_service import agregar_valor

    fila = agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1900, 1, 1),
        "abogado1",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
    )
    assert fila.creado_por_sistema is False


def test_agregar_valor_marca_creado_por_sistema_false_aunque_usuario_diga_sistema():
    from app.services.parametro_service import agregar_valor

    fila = agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1900, 1, 1),
        "sistema",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
    )
    assert fila.creado_por_sistema is False
```

- [ ] **Step 2: Correr el test para confirmar que falla**

Run: `pytest tests/services/test_parametro_service.py -k creado_por_sistema -v`
Expected: FAIL — `AttributeError: 'ParametroLegal' object has no attribute 'creado_por_sistema'` (si el Task 1 no corrió antes) o `assert None is False`/similar (si la columna existe pero `agregar_valor` no la setea todavía).

- [ ] **Step 3: Refactorizar `agregar_valor` — extraer validación compartida y setear el flag**

Reemplazar el docstring del módulo (líneas 12-15, dentro del docstring principal de `parametro_service.py`):

```python
Tabla append-only para las filas de sistema (sembradas por
scripts/migrate_parametros_legales.py / scripts/migrate_ipc_variacion_anual.py,
creado_por_sistema=True): nunca se editan ni se borran. Las filas creadas por
un usuario desde la GUI (creado_por_sistema=False) SI se pueden editar/borrar
-- ver editar_valor()/eliminar_valor() mas abajo -- excepcion deliberada,
acotada por ese flag. Las columnas usuario/motivo/creado_en de cada fila
siguen siendo la bitacora, ahora con la salvedad de que las filas de usuario
pueden cambiar de estado tras crearse.
```

Reemplazar la función completa `agregar_valor` (líneas 491-563) por:

```python
def _validar_y_preparar(
    clave: str,
    valor: Decimal,
    vigente_desde: date,
    areas_derecho: list[AreaDerecho],
    unidad: str,
    vigente_hasta: date | None,
    session,
    excluir_id: int | None = None,
) -> tuple[InfoParametro, str, str]:
    """Validación compartida por `agregar_valor` y `editar_valor`: reglas de
    modo/vigente_hasta, valor positivo, unidad no vacía y solapamiento de
    tramos TRAMO_CERRADO. `excluir_id` (usado solo por `editar_valor`) excluye
    la propia fila de la consulta de solapamiento -- si no se excluyera, una
    fila TRAMO_CERRADO siempre "se solaparía consigo misma" al editarla sin
    cambiar sus fechas. Retorna (info, areas_derecho_json, unidad_normalizada)
    listos para construir/actualizar la fila."""
    info = _validar_clave(clave)
    if info.modo == ModoResolucion.TRAMO_CERRADO and vigente_hasta is None:
        raise ValueError(f"'{clave}' requiere 'vigente_hasta' (modo TRAMO_CERRADO).")
    if info.modo != ModoResolucion.TRAMO_CERRADO and vigente_hasta is not None:
        raise ValueError(f"'{clave}' no admite 'vigente_hasta' (modo {info.modo.value}).")
    if valor <= Decimal("0") and clave not in CLAVES_VALOR_PUEDE_SER_NO_POSITIVO:
        raise ValueError("El valor debe ser positivo.")
    if vigente_hasta is not None and vigente_hasta < vigente_desde:
        raise ValueError("'vigente_hasta' no puede ser anterior a 'vigente_desde'.")
    areas_derecho_json = serializar_areas(areas_derecho)
    unidad = unidad.strip()
    if not unidad:
        raise ValueError("La unidad es obligatoria.")

    if info.modo == ModoResolucion.TRAMO_CERRADO:
        query = session.query(ParametroLegal).filter(
            ParametroLegal.clave == clave,
            ParametroLegal.vigente_desde <= vigente_hasta,
            ParametroLegal.vigente_hasta >= vigente_desde,
        )
        if excluir_id is not None:
            query = query.filter(ParametroLegal.id != excluir_id)
        tramo_solapado = query.first()
        if tramo_solapado is not None:
            raise ValueError(
                f"El tramo {vigente_desde} a {vigente_hasta} se solapa con un tramo "
                f"existente de '{clave}' ({tramo_solapado.vigente_desde} a "
                f"{tramo_solapado.vigente_hasta})."
            )
    return info, areas_derecho_json, unidad


def agregar_valor(
    clave: str,
    valor: Decimal,
    vigente_desde: date,
    usuario: str,
    areas_derecho: list[AreaDerecho],
    unidad: str,
    motivo: str | None = None,
    vigente_hasta: date | None = None,
) -> ParametroLegal:
    """Inserta una fila nueva creada por un usuario (creado_por_sistema=False
    siempre, sin importar lo que diga `usuario` -- ver docstring del modulo).
    Usada por la GUI (app/views/configuracion.py).

    areas_derecho/unidad (Sprint 57): obligatorias para toda fila creada por
    esta funcion -- se guardan por fila (no como metadato fijo en Python).
    El modelo las deja nullable a nivel de columna SQLite (ver
    database/models.py) precisamente para que esa obligatoriedad la exija
    esta funcion, no un CHECK/NOT NULL de la base de datos.

    `valor` debe ser positivo salvo para las claves listadas en
    CLAVES_VALOR_PUEDE_SER_NO_POSITIVO (hoy solo IPC_VARIACION_ANUAL, que
    puede ser 0 o negativa en un año de deflacion -- ver el comentario junto a
    esa constante)."""
    session = session_module.get_session()
    try:
        info, areas_derecho_json, unidad = _validar_y_preparar(
            clave, valor, vigente_desde, areas_derecho, unidad, vigente_hasta, session
        )
        fila = ParametroLegal(
            clave=clave,
            valor=valor,
            vigente_desde=vigente_desde,
            vigente_hasta=vigente_hasta,
            usuario=usuario,
            motivo=motivo,
            creado_en=datetime.now(),
            areas_derecho=areas_derecho_json,
            unidad=unidad,
            creado_por_sistema=False,
        )
        session.add(fila)
        session.commit()
        session.refresh(fila)
        return fila
    finally:
        session.close()
```

- [ ] **Step 4: Correr el test para confirmar que pasa**

Run: `pytest tests/services/test_parametro_service.py -v`
Expected: PASS (todos, incluidos los 2 nuevos — la extracción de `_validar_y_preparar` no cambia ningún mensaje de error ni comportamiento observable de `agregar_valor`, así que los tests existentes de validación siguen pasando sin cambios).

- [ ] **Step 5: Commit**

```bash
git add app/services/parametro_service.py tests/services/test_parametro_service.py
git commit -m "refactor: extraer validacion compartida de agregar_valor y marcar creado_por_sistema=False"
```

---

### Task 3: `editar_valor` y `eliminar_valor` en el servicio

**Files:**
- Modify: `app/services/parametro_service.py` (agregar después de `agregar_valor`)
- Modify: `tests/services/test_parametro_service.py`

- [ ] **Step 1: Escribir los tests que fallan**

Mismo criterio del Task 2: importar cada función del servicio dentro de cada test, no a nivel de módulo. `date`, `datetime`, `Decimal`, `pytest`, `session_module`, `ParametroLegal` y (tras el Task 2) `AreaDerecho` ya están disponibles a nivel de módulo en este archivo — `serializar_areas` no lo está, se importa local donde se usa.

```python
def test_editar_valor_actualiza_los_campos():
    from app.services.parametro_service import agregar_valor, editar_valor, historial

    fila = agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1900, 1, 1),
        "abogado1",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
    )

    fila_editada = editar_valor(
        fila.id,
        valor=Decimal("2.0"),
        vigente_desde=date(1900, 1, 1),
        usuario="abogado2",
        areas_derecho=[AreaDerecho.COMERCIAL, AreaDerecho.TRIBUTARIO],
        unidad="veces",
        motivo="correccion",
    )

    assert fila_editada.valor == Decimal("2.0")
    assert fila_editada.usuario == "abogado2"
    assert fila_editada.motivo == "correccion"
    assert len(historial("USURA_MULTIPLICADOR")) == 1  # UPDATE, no INSERT nuevo


def test_editar_valor_de_fila_de_sistema_lanza_value_error():
    from app.services.areas_parametro import serializar_areas
    from app.services.parametro_service import editar_valor

    session = session_module.get_session()
    fila_sistema = ParametroLegal(
        clave="USURA_MULTIPLICADOR",
        valor=Decimal("1.5"),
        vigente_desde=date(1900, 1, 1),
        usuario="sistema",
        creado_en=datetime.now(),
        areas_derecho=serializar_areas([AreaDerecho.COMERCIAL]),
        unidad="veces",
        creado_por_sistema=True,
    )
    session.add(fila_sistema)
    session.commit()
    session.refresh(fila_sistema)
    fila_id = fila_sistema.id
    session.close()

    with pytest.raises(ValueError, match="sistema"):
        editar_valor(
            fila_id,
            valor=Decimal("2.0"),
            vigente_desde=date(1900, 1, 1),
            usuario="abogado1",
            areas_derecho=[AreaDerecho.COMERCIAL],
            unidad="veces",
        )


def test_eliminar_valor_borra_la_fila():
    from app.services.parametro_service import agregar_valor, eliminar_valor, historial

    fila = agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1900, 1, 1),
        "abogado1",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
    )

    eliminar_valor(fila.id)

    assert historial("USURA_MULTIPLICADOR") == []


def test_eliminar_valor_de_fila_de_sistema_lanza_value_error():
    from app.services.areas_parametro import serializar_areas
    from app.services.parametro_service import eliminar_valor, historial

    session = session_module.get_session()
    fila_sistema = ParametroLegal(
        clave="USURA_MULTIPLICADOR",
        valor=Decimal("1.5"),
        vigente_desde=date(1900, 1, 1),
        usuario="sistema",
        creado_en=datetime.now(),
        areas_derecho=serializar_areas([AreaDerecho.COMERCIAL]),
        unidad="veces",
        creado_por_sistema=True,
    )
    session.add(fila_sistema)
    session.commit()
    session.refresh(fila_sistema)
    fila_id = fila_sistema.id
    session.close()

    with pytest.raises(ValueError, match="sistema"):
        eliminar_valor(fila_id)

    assert len(historial("USURA_MULTIPLICADOR")) == 1
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/services/test_parametro_service.py -k "editar_valor or eliminar_valor" -v`
Expected: FAIL — `ImportError: cannot import name 'editar_valor'`

- [ ] **Step 3: Implementar `editar_valor` y `eliminar_valor`, agregados después de `agregar_valor` en `app/services/parametro_service.py`**

```python
def editar_valor(
    parametro_id: int,
    valor: Decimal,
    vigente_desde: date,
    usuario: str,
    areas_derecho: list[AreaDerecho],
    unidad: str,
    motivo: str | None = None,
    vigente_hasta: date | None = None,
) -> ParametroLegal:
    """Actualiza en el sitio una fila existente creada por un usuario --
    excepcion deliberada al append-only historico (ver docstring del modulo),
    acotada a filas con creado_por_sistema=False. La clave (`clave`) NO es
    editable -- no se recibe como parametro, se conserva la de la fila
    existente; cambiar de clave equivaldria a borrar una fila y crear otra
    distinta, decision tomada con el usuario al diseñar este sprint."""
    session = session_module.get_session()
    try:
        fila = session.get(ParametroLegal, parametro_id)
        if fila is None:
            raise ValueError(f"No existe un parametro con id {parametro_id}.")
        if fila.creado_por_sistema:
            raise ValueError("No se puede editar un parametro creado por el sistema.")
        _info, areas_derecho_json, unidad = _validar_y_preparar(
            fila.clave,
            valor,
            vigente_desde,
            areas_derecho,
            unidad,
            vigente_hasta,
            session,
            excluir_id=parametro_id,
        )
        fila.valor = valor
        fila.vigente_desde = vigente_desde
        fila.vigente_hasta = vigente_hasta
        fila.usuario = usuario
        fila.motivo = motivo
        fila.areas_derecho = areas_derecho_json
        fila.unidad = unidad
        session.commit()
        session.refresh(fila)
        return fila
    finally:
        session.close()


def eliminar_valor(parametro_id: int) -> None:
    """Borra definitivamente una fila creada por un usuario -- excepcion
    deliberada al append-only historico, acotada a creado_por_sistema=False.
    Si `parametro_id` ya no existe (doble clic sobre una fila ya eliminada),
    no hace nada -- mismo criterio defensivo que
    ExpedienteDetallePage._eliminar_obligacion (Sprint 60, hotfix de
    produccion 2026-08-12)."""
    session = session_module.get_session()
    try:
        fila = session.get(ParametroLegal, parametro_id)
        if fila is None:
            return
        if fila.creado_por_sistema:
            raise ValueError("No se puede eliminar un parametro creado por el sistema.")
        session.delete(fila)
        session.commit()
    finally:
        session.close()
```

- [ ] **Step 4: Correr los tests para confirmar que pasan**

Run: `pytest tests/services/test_parametro_service.py -v`
Expected: PASS (todos)

- [ ] **Step 5: Commit**

```bash
git add app/services/parametro_service.py tests/services/test_parametro_service.py
git commit -m "feat: agregar editar_valor y eliminar_valor, protegidos para filas de sistema"
```

---

### Task 4: "Vigente hasta" — aclaración de UI, sin tocar el motor de cálculo

**Files:**
- Modify: `app/views/configuracion.py:78-263` (`ParametroFormDialog`)
- Modify: `tests/views/test_configuracion.py`

- [ ] **Step 1: Actualizar los tests existentes que asumían que el campo se ocultaba**

Reemplazar `test_parametro_form_dialog_muestra_vigente_hasta_solo_para_tramo_cerrado` (líneas 152-161 al momento de escribir este plan) por:

```python
def test_parametro_form_dialog_vigente_hasta_deshabilitado_fuera_de_tramo_cerrado(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.show()

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    assert dialogo.campo_vigente_hasta.isVisible() is True
    assert dialogo.campo_vigente_hasta.isEnabled() is False

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("IBC_CONSUMO_ORDINARIO"))
    assert dialogo.campo_vigente_hasta.isVisible() is True
    assert dialogo.campo_vigente_hasta.isEnabled() is True
```

Reemplazar `test_parametro_form_dialog_label_vigente_hasta_no_queda_huerfana` (líneas 164-180) por:

```python
def test_parametro_form_dialog_nota_vigente_hasta_cambia_segun_el_modo(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.show()

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    assert "no vence en una fecha fija" in dialogo._nota_vigente_hasta.text()

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("IBC_CONSUMO_ORDINARIO"))
    assert dialogo._nota_vigente_hasta.text() == ""
```

Agregar un test nuevo para el checkbox "Indefinido":

```python
def test_parametro_form_dialog_checkbox_indefinido_siempre_deshabilitado(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.show()

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("IBC_CONSUMO_ORDINARIO"))
    assert dialogo.casilla_indefinido.isEnabled() is False
    assert dialogo.casilla_indefinido.isChecked() is False
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/views/test_configuracion.py -k vigente_hasta -v`
Expected: FAIL — `AttributeError: 'ParametroFormDialog' object has no attribute '_nota_vigente_hasta'` (y las 2 primeras assertions de visibilidad/habilitado fallan contra el comportamiento viejo de ocultar la fila).

- [ ] **Step 3: Modificar `ParametroFormDialog.__init__` en `app/views/configuracion.py`**

Reemplazar la construcción de `campo_vigente_hasta` (líneas 104-109):

```python
        self.campo_vigente_hasta = QDateEdit(QDate.currentDate())
        self.campo_vigente_hasta.setCalendarPopup(True)
        self.campo_vigente_hasta.setToolTip(
            "Fecha hasta la que este valor rige; solo aplica a parametros con un "
            "rango de vigencia cerrado (ej. tramos historicos de tasas certificadas)."
        )
        self.casilla_indefinido = QCheckBox("Indefinido")
        self.casilla_indefinido.setToolTip(
            "Este parametro requiere una fecha de fin (modo TRAMO_CERRADO) -- no puede "
            "quedar indefinido."
        )
        self._nota_vigente_hasta = QLabel()
        self._nota_vigente_hasta.setWordWrap(True)

        _contenedor_vigente_hasta = QWidget()
        _layout_vigente_hasta = QVBoxLayout(_contenedor_vigente_hasta)
        _layout_vigente_hasta.setContentsMargins(0, 0, 0, 0)
        _fila_fecha_e_indefinido = QHBoxLayout()
        _fila_fecha_e_indefinido.addWidget(self.campo_vigente_hasta)
        _fila_fecha_e_indefinido.addWidget(self.casilla_indefinido)
        _layout_vigente_hasta.addLayout(_fila_fecha_e_indefinido)
        _layout_vigente_hasta.addWidget(self._nota_vigente_hasta)
```

Reemplazar la línea `self._layout_formulario.addRow("Vigente hasta", self.campo_vigente_hasta)` (línea 165) por:

```python
        self._layout_formulario.addRow("Vigente hasta", _contenedor_vigente_hasta)
```

Reemplazar el método `_actualizar_visibilidad_vigente_hasta` (líneas 204-214) por:

```python
    def _actualizar_visibilidad_vigente_hasta(self) -> None:
        """Nombre del método sin cambios (evita re-cablear sus 2 call sites:
        __init__ y combo_clave.currentIndexChanged), pero el comportamiento sí
        cambió (Sprint "Parametros: editar/eliminar de usuario"): la fila
        "Vigente hasta" ya NO se oculta según el modo -- se deshabilita, con
        una nota explicando por qué,
        para que el usuario entienda la regla en vez de ver el campo
        desaparecer sin explicación. `casilla_indefinido` (TRAMO_CERRADO)
        queda siempre deshabilitada porque ese modo siempre exige una fecha
        real (agregar_valor la rechaza si falta) -- existe solo para que las
        3 combinaciones de modo compartan un mismo patrón visual (campo +
        nota), no porque hoy sea usable."""
        clave = self.combo_clave.currentData()
        info = CATALOGO_PARAMETROS[clave]
        es_tramo_cerrado = info.modo == ModoResolucion.TRAMO_CERRADO
        self.campo_vigente_hasta.setEnabled(es_tramo_cerrado)
        self.casilla_indefinido.setEnabled(False)
        if es_tramo_cerrado:
            self._nota_vigente_hasta.setText("")
        else:
            self._nota_vigente_hasta.setText(
                f"Este parámetro no vence en una fecha fija (modo {info.modo.value}) — "
                "el valor rige indefinidamente hasta que se cargue uno nuevo con una "
                "fecha 'Vigente desde' posterior."
            )
```

- [ ] **Step 4: Ajustar `guardar()` — ya no depende de visibilidad, sigue dependiendo del modo (sin cambios de lógica, solo confirmar que sigue leyendo `self.campo_vigente_hasta.date()` igual que antes)**

El bloque existente (líneas 234-237) no necesita cambios:

```python
        vigente_hasta = None
        if info.modo == ModoResolucion.TRAMO_CERRADO:
            qdate_hasta = self.campo_vigente_hasta.date()
            vigente_hasta = date(qdate_hasta.year(), qdate_hasta.month(), qdate_hasta.day())
```

Esto sigue siendo correcto: el campo ahora está siempre visible pero solo *habilitado* (interactuable) en `TRAMO_CERRADO`, así que su valor solo se lee quando ese es el modo — igual que antes.

- [ ] **Step 5: Agregar los imports que falten al inicio de `app/views/configuracion.py`**

`QHBoxLayout` ya está importado (línea 13). Confirmar que `QVBoxLayout` también lo está (línea 20) — ambos ya se usan en el archivo, no hace falta agregar imports nuevos.

- [ ] **Step 6: Correr los tests para confirmar que pasan**

Run: `pytest tests/views/test_configuracion.py -v`
Expected: PASS (todos, incluidos los 3 nuevos/actualizados de este task)

- [ ] **Step 7: Commit**

```bash
git add app/views/configuracion.py tests/views/test_configuracion.py
git commit -m "feat: aclarar en la UI cuando aplica Vigente hasta, sin tocar el motor de calculo"
```

---

### Task 5: "Unidad" como `QComboBox` con opción "Otros"

**Files:**
- Modify: `app/views/configuracion.py` (`ParametroFormDialog`)
- Modify: `tests/views/test_configuracion.py`

- [ ] **Step 1: Escribir los tests que fallan**

```python
def test_parametro_form_dialog_unidad_es_combobox_con_opciones_conocidas(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)

    textos = [dialogo.campo_unidad.itemText(i) for i in range(dialogo.campo_unidad.count())]
    assert textos == ["%", "COP", "meses", "índice", "veces", "puntos", "Otros..."]


def test_parametro_form_dialog_unidad_preselecciona_segun_la_clave(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("SMLMV"))
    assert dialogo.campo_unidad.currentText() == "COP"


def test_parametro_form_dialog_unidad_otros_revela_campo_de_texto(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.show()

    assert dialogo._campo_unidad_otros.isVisible() is False
    dialogo.campo_unidad.setCurrentText("Otros...")
    assert dialogo._campo_unidad_otros.isVisible() is True


def test_parametro_form_dialog_guarda_unidad_otros(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")
    dialogo.campo_unidad.setCurrentText("Otros...")
    dialogo._campo_unidad_otros.setText("fracciones")

    dialogo.guardar()

    fila = historial("USURA_MULTIPLICADOR")[0]
    assert fila.unidad == "fracciones"
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/views/test_configuracion.py -k unidad -v`
Expected: FAIL — `AttributeError: 'QLineEdit' object has no attribute 'itemText'` (o similar, `campo_unidad` sigue siendo `QLineEdit`)

- [ ] **Step 3: Modificar `ParametroFormDialog.__init__`**

Reemplazar `self.campo_unidad = QLineEdit()` (línea 130) por:

```python
        self.campo_unidad = QComboBox()
        self.campo_unidad.addItems(["%", "COP", "meses", "índice", "veces", "puntos", "Otros..."])
        self._campo_unidad_otros = QLineEdit()
        self._campo_unidad_otros.setPlaceholderText("Escribe la unidad")
        self.campo_unidad.currentTextChanged.connect(self._actualizar_visibilidad_unidad_otros)
```

En el bloque de `agregar_ayuda` para "Unidad" (líneas 172-181), envolver también el campo "Otros" en el mismo contenedor. Reemplazar:

```python
        self._contenedor_campo_unidad = agregar_ayuda(
            self._layout_formulario,
            "Unidad",
            self.campo_unidad,
            tooltip=(
                "Unidad de medida del valor, sugerida automaticamente segun la clave "
                "elegida. No se puede editar despues de guardar."
            ),
            ejemplo="%, COP, meses, índice",
        )
```

por:

```python
        _contenedor_unidad_y_otros = QWidget()
        _layout_unidad_y_otros = QVBoxLayout(_contenedor_unidad_y_otros)
        _layout_unidad_y_otros.setContentsMargins(0, 0, 0, 0)
        _layout_unidad_y_otros.addWidget(self.campo_unidad)
        _layout_unidad_y_otros.addWidget(self._campo_unidad_otros)
        self._campo_unidad_otros.setVisible(False)
        self._contenedor_campo_unidad = agregar_ayuda(
            self._layout_formulario,
            "Unidad",
            _contenedor_unidad_y_otros,
            tooltip=(
                "Unidad de medida del valor, sugerida automaticamente segun la clave "
                "elegida. Elige 'Otros...' para escribir una unidad distinta."
            ),
            ejemplo="%, COP, meses, índice, veces, puntos",
        )
```

Agregar el nuevo método, junto a `_actualizar_area_unidad_sugeridas`:

```python
    def _actualizar_visibilidad_unidad_otros(self, texto: str) -> None:
        self._campo_unidad_otros.setVisible(texto == "Otros...")
```

- [ ] **Step 4: Ajustar `_actualizar_area_unidad_sugeridas` para usar el combo**

Reemplazar `self.campo_unidad.setText(unidad_sugerida)` (línea 202) por:

```python
        indice_unidad = self.campo_unidad.findText(unidad_sugerida)
        self.campo_unidad.setCurrentIndex(indice_unidad if indice_unidad >= 0 else 0)
```

- [ ] **Step 5: Ajustar `guardar()` para leer del combo o del campo "Otros"**

Reemplazar `unidad = self.campo_unidad.text().strip()` (línea 244) por:

```python
        if self.campo_unidad.currentText() == "Otros...":
            unidad = self._campo_unidad_otros.text().strip()
        else:
            unidad = self.campo_unidad.currentText()
```

- [ ] **Step 6: Correr los tests para confirmar que pasan**

Run: `pytest tests/views/test_configuracion.py -v`
Expected: PASS (todos, incluido `test_parametro_form_dialog_unidad_muestra_icono_informativo`, que sigue funcionando porque `agregar_ayuda` sigue envolviendo con el mismo mecanismo de ícono — ahora envuelve `_contenedor_unidad_y_otros` en vez del `QLineEdit` directo).

- [ ] **Step 7: Commit**

```bash
git add app/views/configuracion.py tests/views/test_configuracion.py
git commit -m "feat: unidad como desplegable con opcion Otros"
```

---

### Task 6: Tooltips ⓘ homologados en todos los campos + columnas de la tabla

**Files:**
- Modify: `app/views/configuracion.py` (`ParametroFormDialog`, `ParametrosView`)
- Modify: `tests/views/test_configuracion.py`

- [ ] **Step 1: Escribir los tests que fallan**

```python
def test_parametro_form_dialog_todos_los_campos_tienen_icono_informativo(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)

    for nombre_contenedor in (
        "_contenedor_combo_clave",
        "_contenedor_campo_valor",
        "_contenedor_campo_vigente_desde",
        "_contenedor_vigente_hasta_con_ayuda",
        "_contenedor_areas_con_ayuda",
        "_contenedor_campo_unidad",
        "_contenedor_campo_usuario",
        "_contenedor_campo_motivo",
    ):
        contenedor = getattr(dialogo, nombre_contenedor)
        iconos_info = [hijo for hijo in contenedor.findChildren(QLabel) if hijo.toolTip()]
        assert len(iconos_info) == 1, f"{nombre_contenedor} deberia tener 1 icono (i)"


def test_parametros_view_columnas_tienen_tooltip(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)

    for indice in range(vista.tabla.columnCount()):
        item = vista.tabla.horizontalHeaderItem(indice)
        assert item.toolTip() != "", f"Columna {indice} deberia tener tooltip"
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/views/test_configuracion.py -k "icono_informativo or columnas_tienen_tooltip" -v`
Expected: FAIL — `AttributeError: 'ParametroFormDialog' object has no attribute '_contenedor_combo_clave'`

- [ ] **Step 3: Envolver cada campo restante con `agregar_ayuda` en `ParametroFormDialog.__init__`**

Reemplazar cada `self._layout_formulario.addRow(...)` de un campo simple por su versión con `agregar_ayuda`, reusando el texto de tooltip que cada campo ya tiene (mismo texto, ahora también en el ícono). Reemplazar:

```python
        self._layout_formulario = QFormLayout()
        self._layout_formulario.addRow("Parametro", self.combo_clave)
        self._layout_formulario.addRow("Valor", self.campo_valor)
        self._layout_formulario.addRow("Vigente desde", self.campo_vigente_desde)
        self._layout_formulario.addRow("Vigente hasta", _contenedor_vigente_hasta)
        self._layout_formulario.addRow("Área(s) del derecho", self._contenedor_areas)
```

por:

```python
        self._layout_formulario = QFormLayout()
        self._contenedor_combo_clave = agregar_ayuda(
            self._layout_formulario,
            "Parametro",
            self.combo_clave,
            tooltip=(
                "Clave del parametro legal a versionar; la descripcion entre parentesis "
                "identifica que mide (ej. 'Tasa de interes civil legal anual "
                "(CIVIL_ANNUAL_RATE)')."
            ),
        )
        self._contenedor_campo_valor = agregar_ayuda(
            self._layout_formulario,
            "Valor",
            self.campo_valor,
            tooltip=(
                "Valor numerico vigente para la clave elegida, en la unidad indicada abajo. "
                "Ejemplo: 6.00 para una tasa del 6%, o 1300000 para un SMLMV en pesos."
            ),
        )
        self._contenedor_campo_vigente_desde = agregar_ayuda(
            self._layout_formulario,
            "Vigente desde",
            self.campo_vigente_desde,
            tooltip=(
                "Fecha desde la que este valor empieza a regir (normalmente la fecha del "
                "decreto o resolucion). Ejemplo: 2024-01-01."
            ),
        )
        self._contenedor_vigente_hasta_con_ayuda = agregar_ayuda(
            self._layout_formulario,
            "Vigente hasta",
            _contenedor_vigente_hasta,
            tooltip=(
                "Fecha hasta la que este valor rige; solo aplica a parametros con un "
                "rango de vigencia cerrado (ej. tramos historicos de tasas certificadas)."
            ),
        )
        self._contenedor_areas_con_ayuda = agregar_ayuda(
            self._layout_formulario,
            "Área(s) del derecho",
            self._contenedor_areas,
            tooltip=(
                "Area(s) del derecho a las que aplica este valor (puede marcar varias). Se "
                "preselecciona segun la clave elegida; no se puede editar despues de guardar."
            ),
        )
```

Ya no hace falta el `.setToolTip(...)` suelto en `combo_clave`/`campo_valor`/`campo_vigente_desde`/`_contenedor_areas` (líneas 85-89, 94-97, 100-103, 119-122) — quitar esas 4 llamadas, `agregar_ayuda` ya deja el tooltip en el ícono. **Excepción:** dejar `self.campo_vigente_hasta.setToolTip(...)` y `self.casilla_indefinido.setToolTip(...)` (agregados en el Task 4) tal cual — esos siguen siendo tooltips directos sobre esos 2 widgets puntuales, independientes del ícono de la fila completa.

Reemplazar `self._layout_formulario.addRow("Usuario", self.campo_usuario)` y `self._layout_formulario.addRow("Motivo (opcional)", self.campo_motivo)` por:

```python
        self._contenedor_campo_usuario = agregar_ayuda(
            self._layout_formulario,
            "Usuario",
            self.campo_usuario,
            tooltip=(
                "Nombre de quien registra este valor, para la bitacora de auditoria del "
                "parametro (no se puede editar ni borrar despues)."
            ),
        )
        self._contenedor_campo_motivo = agregar_ayuda(
            self._layout_formulario,
            "Motivo (opcional)",
            self.campo_motivo,
            tooltip=(
                "Justificacion o fuente del cambio, para dejar constancia del porque de "
                "este valor. Ejemplo: 'Decreto 2613 de 2023, ajuste SMLMV 2024'."
            ),
        )
```

Quitar también las líneas sueltas `self.campo_usuario.setToolTip(...)` (133-136) y `self.campo_motivo.setToolTip(...)` (138-141) — mismo motivo, ahora el tooltip vive en el ícono vía `agregar_ayuda`.

**Importante:** el test `test_parametro_form_dialog_campos_no_autoexplicativos_tienen_tooltip` (ya existente, líneas 77-91) verifica `widget.toolTip() != ""` sobre el **widget mismo** (`combo_clave`, `campo_valor`, etc.), no sobre el ícono — como `agregar_ayuda` NO copia el tooltip al `campo` que envuelve, ese test se rompería. Actualizar ese test para que en cambio verifique el ícono del contenedor, igual que los tests nuevos de este Task — reemplazarlo por:

```python
def test_parametro_form_dialog_campos_no_autoexplicativos_tienen_tooltip(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)

    for nombre_contenedor in (
        "_contenedor_combo_clave",
        "_contenedor_campo_valor",
        "_contenedor_campo_vigente_desde",
        "_contenedor_campo_usuario",
        "_contenedor_campo_motivo",
        "_contenedor_areas_con_ayuda",
    ):
        contenedor = getattr(dialogo, nombre_contenedor)
        iconos_info = [hijo for hijo in contenedor.findChildren(QLabel) if hijo.toolTip()]
        assert len(iconos_info) == 1, f"{nombre_contenedor} deberia tener tooltip"
```

(esto deja el test redundante con `test_parametro_form_dialog_todos_los_campos_tienen_icono_informativo` del Step 1 — es intencional, se puede eliminar este test viejo en vez de reescribirlo, ya que el nuevo lo cubre por completo. Preferir **eliminarlo** para no duplicar cobertura.)

- [ ] **Step 4: Agregar tooltips a los encabezados de columna de `ParametrosView`**

En `ParametrosView.__init__`, después de `self.tabla.setHorizontalHeaderLabels(columnas)`:

```python
        _tooltips_columnas = [
            "Grupo temático del parámetro (Topes legales, Plazos de prescripción y "
            "caducidad, Indicadores históricos, Seguridad social).",
            "Nombre del parámetro legal versionado.",
            "Valor resuelto para la fecha de hoy, según el modo de resolución de la clave.",
            "Fecha desde la que rige el valor vigente hoy.",
            "Fecha hasta la que rige el valor vigente hoy (o 'Indefinido' si no aplica).",
            "Área(s) del derecho a las que aplica este parámetro.",
            "Unidad de medida del valor (%, COP, meses, índice, veces, puntos).",
        ]
        for indice, texto in enumerate(_tooltips_columnas):
            self.tabla.horizontalHeaderItem(indice).setToolTip(texto)
```

- [ ] **Step 5: Correr los tests para confirmar que pasan**

Run: `pytest tests/views/test_configuracion.py -v`
Expected: PASS (todos)

- [ ] **Step 6: Commit**

```bash
git add app/views/configuracion.py tests/views/test_configuracion.py
git commit -m "feat: homologar tooltips (i) en todos los campos del formulario y columnas de la tabla"
```

---

### Task 7: `ParametroFormDialog` soporta modo edición (`parametro_id`)

**Files:**
- Modify: `app/views/configuracion.py` (`ParametroFormDialog`)
- Modify: `tests/views/test_configuracion.py`

- [ ] **Step 1: Escribir los tests que fallan**

```python
def test_parametro_form_dialog_modo_edicion_precarga_los_campos(qtbot):
    fila = agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1900, 1, 1),
        "abogado1",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
        motivo="motivo original",
    )

    dialogo = ParametroFormDialog(parametro_id=fila.id)
    qtbot.addWidget(dialogo)

    assert dialogo.windowTitle() == "Editar valor de parametro"
    assert dialogo.combo_clave.currentData() == "USURA_MULTIPLICADOR"
    assert dialogo.combo_clave.isEnabled() is False
    assert dialogo.campo_valor.text() == "1.5"
    assert dialogo.campo_usuario.text() == "abogado1"
    assert dialogo.campo_motivo.text() == "motivo original"
    assert dialogo.casillas_area[AreaDerecho.COMERCIAL].isChecked() is True


def test_parametro_form_dialog_modo_edicion_guarda_actualiza_no_crea(qtbot):
    fila = agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1900, 1, 1),
        "abogado1",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
    )

    dialogo = ParametroFormDialog(parametro_id=fila.id)
    qtbot.addWidget(dialogo)
    dialogo.campo_valor.setText("9.9")
    dialogo.guardar()

    filas = historial("USURA_MULTIPLICADOR")
    assert len(filas) == 1
    assert filas[0].valor == Decimal("9.9")
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/views/test_configuracion.py -k modo_edicion -v`
Expected: FAIL — `TypeError: ParametroFormDialog.__init__() got an unexpected keyword argument 'parametro_id'`

- [ ] **Step 3: Modificar `ParametroFormDialog.__init__`**

Reemplazar la firma y las primeras líneas:

```python
class ParametroFormDialog(QDialog):
    def __init__(self, parent=None, parametro_id: int | None = None):
        super().__init__(parent)
        hacer_redimensionable(self)
        self._parametro_id = parametro_id
        self.setWindowTitle("Editar valor de parametro" if parametro_id else "Agregar valor de parametro")
```

Al final de `__init__` (después de `self._actualizar_area_unidad_sugeridas()`), agregar:

```python
        if parametro_id is not None:
            self._precargar_desde_parametro(parametro_id)
```

Agregar el nuevo método `_precargar_desde_parametro`, junto a `_actualizar_area_unidad_sugeridas`:

```python
    def _precargar_desde_parametro(self, parametro_id: int) -> None:
        session = session_module.get_session()
        fila = session.get(ParametroLegal, parametro_id)
        clave, valor, vigente_desde = fila.clave, fila.valor, fila.vigente_desde
        vigente_hasta, usuario, motivo = fila.vigente_hasta, fila.usuario, fila.motivo
        unidad, areas = fila.unidad, deserializar_areas(fila.areas_derecho or "[]")
        session.close()

        # Se fija DESPUES de _actualizar_area_unidad_sugeridas() (disparado por
        # este mismo setCurrentIndex) para pisar la propuesta automatica con
        # los valores REALES ya guardados en la fila -- mismo orden que usa
        # ObligacionFormDialog._precargar_desde_obligacion.
        self.combo_clave.setCurrentIndex(self.combo_clave.findData(clave))
        self.combo_clave.setEnabled(False)
        self.campo_valor.setText(str(valor))
        self.campo_vigente_desde.setDate(QDate(vigente_desde.year, vigente_desde.month, vigente_desde.day))
        if vigente_hasta is not None:
            self.campo_vigente_hasta.setDate(
                QDate(vigente_hasta.year, vigente_hasta.month, vigente_hasta.day)
            )
        self.campo_usuario.setText(usuario)
        self.campo_motivo.setText(motivo or "")
        areas_set = set(areas)
        for area, casilla in self.casillas_area.items():
            casilla.setChecked(area in areas_set)
        if unidad is not None:
            indice_unidad = self.campo_unidad.findText(unidad)
            if indice_unidad >= 0:
                self.campo_unidad.setCurrentIndex(indice_unidad)
            else:
                self.campo_unidad.setCurrentText("Otros...")
                self._campo_unidad_otros.setText(unidad)
```

Necesita el import `import database.session as session_module` al inicio de `app/views/configuracion.py` (revisar si ya existe — si no, agregarlo junto a los demás imports).

- [ ] **Step 4: Modificar `guardar()` para branch a `editar_valor` en modo edición**

Reemplazar el `return agregar_valor(...)` final de `guardar()` (líneas 246-255) por:

```python
        if self._parametro_id is not None:
            return editar_valor(
                self._parametro_id,
                valor=valor,
                vigente_desde=vigente_desde,
                usuario=usuario,
                areas_derecho=areas_derecho,
                unidad=unidad,
                motivo=motivo,
                vigente_hasta=vigente_hasta,
            )
        return agregar_valor(
            clave=clave,
            valor=valor,
            vigente_desde=vigente_desde,
            usuario=usuario,
            areas_derecho=areas_derecho,
            unidad=unidad,
            motivo=motivo,
            vigente_hasta=vigente_hasta,
        )
```

Agregar `editar_valor` al import existente de `app.services.parametro_service` (línea 26-34).

- [ ] **Step 5: Correr los tests para confirmar que pasan**

Run: `pytest tests/views/test_configuracion.py -v`
Expected: PASS (todos)

- [ ] **Step 6: Commit**

```bash
git add app/views/configuracion.py tests/views/test_configuracion.py
git commit -m "feat: ParametroFormDialog soporta modo edicion via parametro_id"
```

---

### Task 8: Editar/Eliminar por fila en `HistorialParametroDialog`

**Files:**
- Modify: `app/views/configuracion.py` (`HistorialParametroDialog`, `ParametrosView._abrir_historial`)
- Modify: `tests/views/test_configuracion.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar `serializar_areas` al import ya existente de `app.services.areas_parametro` en la cabecera del archivo (hoy solo importa `AREA_UNIDAD_POR_CLAVE, deserializar_areas`):

```python
from app.services.areas_parametro import AREA_UNIDAD_POR_CLAVE, deserializar_areas, serializar_areas
```

```python
def test_historial_parametro_dialog_fila_de_usuario_tiene_botones(qtbot):
    agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1900, 1, 1),
        "abogado1",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
    )
    dialogo = HistorialParametroDialog("USURA_MULTIPLICADOR")
    qtbot.addWidget(dialogo)

    assert dialogo.tabla.cellWidget(0, 5) is not None  # Editar
    assert dialogo.tabla.cellWidget(0, 6) is not None  # Eliminar


def test_historial_parametro_dialog_fila_de_sistema_no_tiene_botones(qtbot):
    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave="USURA_MULTIPLICADOR",
            valor=Decimal("1.5"),
            vigente_desde=date(1900, 1, 1),
            usuario="sistema",
            creado_en=datetime.now(),
            areas_derecho=serializar_areas([AreaDerecho.COMERCIAL]),
            unidad="veces",
            creado_por_sistema=True,
        )
    )
    session.commit()
    session.close()

    dialogo = HistorialParametroDialog("USURA_MULTIPLICADOR")
    qtbot.addWidget(dialogo)

    assert dialogo.tabla.cellWidget(0, 5) is None
    assert dialogo.tabla.cellWidget(0, 6) is None


def test_historial_parametro_dialog_eliminar_borra_y_refresca(qtbot, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    fila = agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1900, 1, 1),
        "abogado1",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
    )
    monkeypatch.setattr(
        QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes
    )
    dialogo = HistorialParametroDialog("USURA_MULTIPLICADOR")
    qtbot.addWidget(dialogo)

    dialogo._eliminar_valor(fila.id)

    assert dialogo.tabla.rowCount() == 0
    assert historial("USURA_MULTIPLICADOR") == []
```

- [ ] **Step 2: Correr los tests para confirmar que fallan**

Run: `pytest tests/views/test_configuracion.py -k historial_parametro_dialog -v`
Expected: FAIL — la tabla hoy tiene 5 columnas (`Valor, Vigente desde, Vigente hasta, Usuario, Motivo`, sin contar la columna opcional de dato crudo), no 7; `cellWidget(0, 5)` no existe todavía.

- [ ] **Step 3: Modificar `HistorialParametroDialog` en `app/views/configuracion.py`**

Reemplazar el bloque de construcción de columnas y la carga de filas (desde `columnas = ["Valor", "Vigente desde", "Vigente hasta", "Usuario", "Motivo"]` hasta el final del `for fila_idx, fila in enumerate(filas):`) por:

```python
        columnas = ["Valor", "Vigente desde", "Vigente hasta", "Usuario", "Motivo"]
        if etiqueta_columna_cruda is not None:
            columnas = [*columnas, etiqueta_columna_cruda]
        columnas = [*columnas, "Editar", "Eliminar"]
        self._indice_columna_editar = len(columnas) - 2
        self._indice_columna_eliminar = len(columnas) - 1
        self.tabla = QTableWidget(0, len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self._clave = clave
        self._info = info
        self._clave_cruda = clave_cruda
        self._variacion_por_anio: dict[int, str] = {}
        if clave_cruda is not None:
            self._variacion_por_anio = {
                fila_cruda.vigente_desde.year: str(fila_cruda.valor)
                for fila_cruda in historial(clave_cruda)
            }
        self._refrescar()

        layout = QVBoxLayout()
        layout.addWidget(self.tabla)
        if formula_texto is not None:
            nota_formula = QLabel(formula_texto)
            nota_formula.setWordWrap(True)
            layout.addWidget(nota_formula)
        self.setLayout(layout)

    def _refrescar(self) -> None:
        filas = historial(self._clave)
        self.tabla.setRowCount(len(filas))
        for fila_idx, fila in enumerate(filas):
            self.tabla.setItem(fila_idx, 0, QTableWidgetItem(str(fila.valor)))
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(fila.vigente_desde.isoformat()))
            self.tabla.setItem(
                fila_idx, 2, QTableWidgetItem(vigencia_hasta_mostrar(fila, self._info))
            )
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(fila.usuario))
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(fila.motivo or ""))
            if self._clave_cruda is not None:
                variacion = self._variacion_por_anio.get(fila.vigente_desde.year, "")
                self.tabla.setItem(fila_idx, 5, QTableWidgetItem(variacion))
            if not fila.creado_por_sistema:
                boton_editar = QPushButton("Editar")
                boton_editar.setProperty("class", "secondary")
                boton_editar.clicked.connect(
                    lambda _checked=False, id_=fila.id: self._editar_valor(id_)
                )
                self.tabla.setCellWidget(fila_idx, self._indice_columna_editar, boton_editar)

                boton_eliminar = QPushButton("Eliminar")
                boton_eliminar.setIcon(icon("delete"))
                boton_eliminar.setProperty("class", "destructive")
                boton_eliminar.clicked.connect(
                    lambda _checked=False, id_=fila.id: self._eliminar_valor(id_)
                )
                self.tabla.setCellWidget(fila_idx, self._indice_columna_eliminar, boton_eliminar)

    def _editar_valor(self, parametro_id: int) -> None:
        dialogo = ParametroFormDialog(self, parametro_id=parametro_id)
        if dialogo.exec():
            self._refrescar()

    def _eliminar_valor(self, parametro_id: int) -> None:
        respuesta = QMessageBox.question(
            self,
            "Eliminar valor de parámetro",
            "¿Eliminar este valor de parámetro? Esta acción no se puede deshacer.",
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        eliminar_valor(parametro_id)
        self._refrescar()
```

(Esto elimina el bloque original `self.tabla.setRowCount(len(filas)) ... for fila_idx, fila in enumerate(filas): ...` — todo ese contenido pasa a vivir dentro de `_refrescar()`.)

Agregar `eliminar_valor` al import de `app.services.parametro_service` (ya se agregó `editar_valor` en el Task 7, agregar también `eliminar_valor` en la misma línea).

- [ ] **Step 4: Refrescar `ParametrosView.tabla` siempre al cerrar el historial (haya habido edición o no)**

Reemplazar `_abrir_historial` (líneas 412-414):

```python
    def _abrir_historial(self, fila: int, _columna: int) -> None:
        clave = self._claves_por_fila[fila]
        HistorialParametroDialog(clave, self).exec()
        self.refrescar()
```

- [ ] **Step 5: Correr los tests para confirmar que pasan**

Run: `pytest tests/views/test_configuracion.py -v`
Expected: PASS (todos)

- [ ] **Step 6: Commit**

```bash
git add app/views/configuracion.py tests/views/test_configuracion.py
git commit -m "feat: agregar Editar/Eliminar por fila en HistorialParametroDialog"
```

---

### Task 9: Documentación (README, GUIA_USUARIO, CHANGELOG)

**Files:**
- Modify: `docs/GUIA_USUARIO.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: `docs/GUIA_USUARIO.md`** — en la sección "5.14. Editar tasas y topes legales (Configuraciones → Parámetros)" (línea ~619 al momento de escribir este plan), agregar al final un nuevo subtítulo:

```markdown

**Editar y eliminar valores que tú mismo cargaste:** dentro del historial de una clave (doble clic sobre
su fila en la tabla), cada valor que tú hayas agregado tiene sus propios botones "Editar" y "Eliminar" —
los valores que trae la app de fábrica no los tienen, para que nunca se puedan tocar por accidente.
Editar permite cambiar el valor, las fechas de vigencia, las áreas del derecho, la unidad, el usuario y el
motivo (no la clave del parámetro); eliminar borra el valor definitivamente, sin papelera.

**Vigente hasta / Indefinido:** al agregar un valor nuevo, el campo "Vigente hasta" ahora explica por qué
está deshabilitado cuando no aplica — solo los parámetros de "rango cerrado" (ej. tramos históricos de
IBC/usura) piden una fecha de fin real; el resto queda vigente indefinidamente hasta que cargues un valor
nuevo.

**Unidad:** ahora es un desplegable con las unidades ya usadas (%, COP, meses, índice, veces, puntos); si
ninguna aplica, elige "Otros..." para escribir la que corresponda.
```

- [ ] **Step 2: `README.md`** — buscar la mención de Sprint 59/60 (tooltips, editar/eliminar) y agregar una línea equivalente sobre este sprint, siguiendo el mismo formato de lista que ya usa el archivo para features recientes.

- [ ] **Step 3: `CHANGELOG.md`** — agregar en `[Unreleased]` (o crear la sección si no existe):

```markdown
### Added
- Editar y eliminar valores de parámetro creados por un usuario (los del sistema quedan protegidos),
  desde el historial de cada clave en Configuraciones → Parámetros.
- Campo "Unidad" como desplegable (con opción "Otros...") al agregar un valor de parámetro.
- Tooltips ⓘ en todos los campos del formulario de parámetros y en las columnas de la tabla.

### Changed
- El campo "Vigente hasta" ahora explica en la propia UI por qué está deshabilitado quando el parámetro
  no usa fecha de fin, en vez de desaparecer sin explicación.
```

- [ ] **Step 4: Commit**

```bash
git add docs/GUIA_USUARIO.md README.md CHANGELOG.md
git commit -m "docs: documentar editar/eliminar de parametros de usuario, vigencia y unidad"
```

---

### Task 10: Suite completa + verificación manual

- [ ] **Step 1: Correr la suite completa**

Run: `pytest -q`
Expected: todos los tests pasan.

- [ ] **Step 2: Correr `ruff check .`**

Run: `ruff check .`
Expected: "All checks passed!"

- [ ] **Step 3: Verificación manual**

Run: `python main.py`. Ir a Configuraciones › Parámetros:
1. "+ Agregar valor nuevo" con una clave `ABIERTO` (ej. USURA_MULTIPLICADOR) — confirmar que "Vigente hasta" aparece deshabilitado con la nota explicativa, y que "Unidad" es un desplegable; elegir "Otros..." y confirmar que aparece el campo de texto.
2. Repetir con una clave `TRAMO_CERRADO` (ej. IBC_CONSUMO_ORDINARIO) — confirmar que "Vigente hasta" se habilita y el checkbox "Indefinido" aparece deshabilitado.
3. Confirmar que todos los campos del formulario (Parámetro, Valor, Vigente desde, Vigente hasta, Área(s), Unidad, Usuario, Motivo) muestran el ícono ⓘ.
4. Guardar un valor de prueba, abrir su historial (doble clic en la fila de la tabla resumen), confirmar que esa fila tiene botones "Editar"/"Eliminar", editar el valor y confirmar que se actualiza sin crear una fila nueva, luego eliminarlo y confirmar que desaparece.
5. Abrir el historial de una clave con datos de sistema (ej. SMLMV) y confirmar que esas filas NO tienen botones Editar/Eliminar.
6. Pasar el mouse sobre los encabezados de columna de la tabla resumen de Parámetros y confirmar que muestran tooltip.

- [ ] **Step 4: Commit final (si la verificación manual encontró algo que corregir)**

Si el Step 3 no encontró ningún problema, no hay nada que commitear en este task.
