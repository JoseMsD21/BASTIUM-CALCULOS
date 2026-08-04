
# Sprint 28 — CI/CD, versionado, housekeeping de repositorio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Profesionalizar el repositorio de cara a su publicación pública en GitHub: pipeline de CI
mínimo que corre `pytest` en cada push/PR, primera versión etiquetada (`__version__` + tag de git),
ruta de `bastium.db` configurable sin editar código fuente, fixture de sesión en memoria centralizada
en un `conftest.py` raíz (elimina 13+ duplicados), y los documentos estándar que GitHub reconoce
(`CONTRIBUTING.md`, `SECURITY.md`, plantillas de Issues/PR, `CHANGELOG.md`) más badges y un aviso
legal visible en `README.md`.

**Architecture:** Cambios puntuales y de bajo riesgo, sin dependencias nuevas (todo usa la librería
estándar y lo que ya está en `requirements.txt`). El pipeline de CI es un único workflow de GitHub
Actions (`windows-latest`, coherente con que es una app de escritorio Windows) que instala
`requirements.txt` y corre `python -m pytest` con `QT_QPA_PLATFORM=offscreen` (validado localmente
antes de escribir el plan: la suite completa pasa igual con esa variable puesta). El versionado vive
en un módulo dedicado (`app/_version.py`) para no acoplarlo a `main.py` ni a `app/views/about.py`
(fuera de alcance, Sprint 30). La ruta de la base de datos se resuelve en una función pura
(`_resolve_db_path()`) que lee `BASTIUM_DB_PATH` del entorno, testeable sin necesidad de recargar el
módulo. La fixture centralizada se llama igual que la que ya existía en `tests/views/conftest.py`
(`_db_en_memoria_por_defecto`) y se "mueve" (no se duplica) a `tests/conftest.py`, ampliada para
también parchear `database.database.engine` (necesario para los tests que invocan
`scripts/migrate_parametros_legales.migrar()`, que llama a `init_db()` y por lo tanto lee ese engine
directamente) — así cubre tanto el patrón simple (solo `SessionLocal`) como el patrón con
`migrar()`, sin necesitar dos fixtures distintas.

**Tech Stack:** Python 3.14, pytest + pytest-qt, SQLAlchemy, GitHub Actions (YAML), ruff.

**Verificado antes de escribir este plan:**
- Baseline actual: `pytest -q` → `687 passed, 1 skipped in ~25s` (el skip es
  `tests/services/test_area_strategy.py::test_areas_no_implementadas_lanzan_error_claro_al_liquidar`,
  propiedad del Sprint 27 — no se toca en este plan).
- `QT_QPA_PLATFORM=offscreen pytest -q` → mismo resultado, `687 passed, 1 skipped`. Confirma que el
  workflow de CI puede forzar esa variable sin romper nada.
- `ruff check .` → **412 errores preexistentes** en el repo (en su mayoría `E501` líneas largas en
  archivos de test que no toca este sprint). Por eso el pipeline de CI de este sprint **no** incluye
  un paso de `ruff check` — un `pytest`-only workflow es lo que pide el texto del sprint ("Pipeline de
  CI mínimo... que corra pytest"), y agregar ruff lo dejaría en rojo desde el primer push por deuda
  técnica que no es de este sprint arreglar.
- `act` (para simular GitHub Actions localmente) no está instalado en este entorno — el YAML se
  valida a mano, sintaxis y lógica, no con una corrida real.
- Remoto `origin` ya apunta a `https://github.com/JoseMsD21/BASTIUM-CALCULOS.git` — se usa esa URL
  para el badge de CI en `README.md`.
- Los 13 archivos con el bloque duplicado `create_engine("sqlite:///:memory:")` +
  `monkeypatch.setattr(session_module, "SessionLocal", ...)` fuera de `tests/views/` (confirmado con
  `grep -rl "sqlite:///:memory:" tests/`, excluyendo `tests/views/` y `tests/services/test_area_strategy.py`,
  que pertenece al Sprint 27):
  1. `tests/temporal/test_prescripcion.py`
  2. `tests/engine/tax/test_actualizacion_867_1.py`
  3. `tests/engine/tax/test_moratory_interest.py`
  4. `tests/engine/tax/test_sanciones.py`
  5. `tests/engine/labor/test_ibl.py`
  6. `tests/services/test_parametro_service.py`
  7. `tests/engine/costs/test_agencias_en_derecho.py`
  8. `tests/engine/test_historical_index.py`
  9. `tests/engine/test_usury_validator.py`
  10. `tests/engine/test_smlmv_to_uvt.py`
  11. `tests/engine/labor/test_moratory_indemnity.py`
  12. `tests/engine/labor/test_seguridad_social.py`
  13. `tests/scripts/test_migrate_parametros_legales.py`

  `tests/audit/test_service.py` y `tests/database/test_models.py` también usan
  `create_engine("sqlite:///:memory:")`, pero con un patrón **distinto** (una fixture `session` no
  autouse que se pasa explícitamente como parámetro a cada test, sin tocar
  `database.session.SessionLocal`) — no es el patrón que describe el hallazgo del sprint, así que se
  dejan intactos para no cambiar su semántica fuera de alcance.

---

### Task 1: Versión de la aplicación (`__version__` + wiring en `main.py`)

**Files:**
- Create: `app/_version.py`
- Create: `tests/test_version.py`
- Modify: `main.py`

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_version.py`:

```python
from app._version import __version__


def test_version_sigue_el_formato_semver():
    partes = __version__.split(".")
    assert len(partes) == 3
    assert all(parte.isdigit() for parte in partes)


def test_version_actual_es_0_1_0():
    assert __version__ == "0.1.0"
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `python -m pytest tests/test_version.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'app._version'`

- [ ] **Step 3: Crear el módulo de versión**

Crear `app/_version.py`:

```python
"""Version de la aplicacion BASTIUM (Sprint 28).

Unica fuente de verdad para el numero de version -- se importa desde main.py
y, a futuro, desde cualquier pantalla que necesite mostrarlo (ej. un dialogo
"Acerca de", fuera de alcance de este sprint). No se usa setuptools_scm ni
un sistema de versionado automatico basado en tags: el proyecto todavia no
tiene un pyproject.toml de paquete instalable (solo el de configuracion de
ruff), asi que la version se actualiza a mano en este archivo y se etiqueta
con un tag de git ("git tag vX.Y.Z") en el mismo commit que la cambia.

0.1.0 es la primera version etiquetada del proyecto (Sprint 28): software
pre-1.0, en desarrollo activo, sin LICENSE definida todavia (ver Sprint 38).
"""

__version__ = "0.1.0"
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `python -m pytest tests/test_version.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Usar la versión en `main.py`**

En `main.py`, cambiar:

```python
import sys

from PySide6.QtWidgets import QApplication

from app.views.main_window import MainWindow
from database.database import init_db


def main() -> None:
    init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

por:

```python
import sys

from PySide6.QtWidgets import QApplication

from app._version import __version__
from app.views.main_window import MainWindow
from database.database import init_db


def main() -> None:
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("BASTIUM")
    app.setApplicationVersion(__version__)
    window = MainWindow()
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Correr la suite completa para verificar que nada se rompió**

Run: `python -m pytest -q`
Expected: `687 passed, 1 skipped` (mismo baseline, más 2 tests nuevos de `test_version.py` ⇒
`689 passed, 1 skipped`)

- [ ] **Step 7: Commit**

```bash
git add app/_version.py tests/test_version.py main.py
git commit -m "feat: agregar __version__ (0.1.0) como primera version etiquetada del proyecto"
```

---

### Task 2: Ruta de `bastium.db` configurable vía `BASTIUM_DB_PATH`

**Files:**
- Modify: `database/database.py`
- Create: `tests/database/test_database.py`

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/database/test_database.py`:

```python
from pathlib import Path

import database.database as database_module


def test_resolve_db_path_usa_bastium_db_en_la_raiz_por_defecto(monkeypatch):
    monkeypatch.delenv("BASTIUM_DB_PATH", raising=False)

    ruta = database_module._resolve_db_path()

    assert ruta.name == "bastium.db"
    assert ruta == Path(database_module.__file__).resolve().parent.parent / "bastium.db"


def test_resolve_db_path_respeta_la_variable_de_entorno(tmp_path, monkeypatch):
    ruta_personalizada = tmp_path / "otra_carpeta" / "custom.db"
    monkeypatch.setenv("BASTIUM_DB_PATH", str(ruta_personalizada))

    assert database_module._resolve_db_path() == ruta_personalizada


def test_resolve_db_path_ignora_una_variable_de_entorno_vacia(monkeypatch):
    monkeypatch.setenv("BASTIUM_DB_PATH", "")

    ruta = database_module._resolve_db_path()

    assert ruta.name == "bastium.db"
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `python -m pytest tests/database/test_database.py -v`
Expected: FAIL con `AttributeError: module 'database.database' has no attribute '_resolve_db_path'`

- [ ] **Step 3: Implementar `_resolve_db_path()`**

En `database/database.py`, cambiar el contenido completo de:

```python
from pathlib import Path

from sqlalchemy import create_engine

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


def init_db() -> None:
    from database.models import Base

    Base.metadata.create_all(engine)
```

por:

```python
import os
from pathlib import Path

from sqlalchemy import create_engine


def _resolve_db_path() -> Path:
    """Ruta del archivo bastium.db. Por defecto vive en la raiz del repo;
    la variable de entorno BASTIUM_DB_PATH permite apuntar a otra ubicacion
    (ej. una base de pruebas manual o una ruta compartida) sin editar
    codigo fuente (Sprint 28, hallazgo 3)."""
    ruta_personalizada = os.environ.get("BASTIUM_DB_PATH")
    if ruta_personalizada:
        return Path(ruta_personalizada)
    return Path(__file__).resolve().parent.parent / "bastium.db"


DB_PATH = _resolve_db_path()
engine = create_engine(f"sqlite:///{DB_PATH}")


def init_db() -> None:
    from database.models import Base

    Base.metadata.create_all(engine)
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `python -m pytest tests/database/test_database.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Correr la suite completa**

Run: `python -m pytest -q`
Expected: `692 passed, 1 skipped` (689 del paso anterior + 3 nuevos)

- [ ] **Step 6: Commit**

```bash
git add database/database.py tests/database/test_database.py
git commit -m "feat: permitir configurar la ruta de bastium.db via BASTIUM_DB_PATH"
```

---

### Task 3: `conftest.py` raíz compartido — elimina la fixture duplicada en 13 archivos

**Files:**
- Create: `tests/conftest.py`
- Delete: `tests/views/conftest.py`
- Modify: `tests/temporal/test_prescripcion.py`
- Modify: `tests/engine/tax/test_actualizacion_867_1.py`
- Modify: `tests/engine/tax/test_moratory_interest.py`
- Modify: `tests/engine/tax/test_sanciones.py`
- Modify: `tests/engine/labor/test_ibl.py`
- Modify: `tests/services/test_parametro_service.py`
- Modify: `tests/engine/costs/test_agencias_en_derecho.py`
- Modify: `tests/engine/test_historical_index.py`
- Modify: `tests/engine/test_usury_validator.py`
- Modify: `tests/engine/test_smlmv_to_uvt.py`
- Modify: `tests/engine/labor/test_moratory_indemnity.py`
- Modify: `tests/engine/labor/test_seguridad_social.py`
- Modify: `tests/scripts/test_migrate_parametros_legales.py`

- [ ] **Step 1: Crear `tests/conftest.py`**

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.database as database_module
import database.session as session_module
from database.models import Base


@pytest.fixture(autouse=True)
def _db_en_memoria_por_defecto(monkeypatch):
    """
    Aisla cada test de bastium.db (el archivo real en disco, gitignored y de
    estado no garantizado en un checkout limpio o en CI): crea un engine
    SQLite en memoria nuevo por test, crea el esquema completo, y parchea
    tanto database.database.engine como database.session.SessionLocal para
    que todo el codigo de produccion (incluidos scripts como
    migrate_parametros_legales.migrar(), que llama a init_db() y por lo
    tanto lee database.database.engine directamente) opere sobre esa base
    aislada.

    Sprint 28 (hallazgo 7): antes de esto, este mismo bloque
    (create_engine(...) + monkeypatch.setattr(session_module,
    "SessionLocal", ...)) estaba duplicado literalmente en 13+ archivos de
    test fuera de tests/views/. Movida aqui desde tests/views/conftest.py
    (donde vivia con este mismo nombre, sin el parche de
    database.database.engine -- innecesario para las vistas, que solo pasan
    por session_module) para que aplique a todo el arbol de tests.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
```

- [ ] **Step 2: Eliminar `tests/views/conftest.py`**

Su única fixture (`_db_en_memoria_por_defecto`, sin el parche de `database_module.engine`) queda
cubierta por el conftest raíz (superconjunto: además parchea `database_module.engine`, lo cual no
afecta a las vistas porque ellas solo pasan por `session_module.get_session()`).

```bash
git rm tests/views/conftest.py
```

- [ ] **Step 3: Correr la suite completa antes de tocar los 13 archivos**

Run: `python -m pytest -q`
Expected: `692 passed, 1 skipped` — el conftest raíz ya cubre `tests/views/` con el mismo
comportamiento; los 13 archivos siguen con su propia fixture duplicada por ahora, así que nada debería
romperse todavía (dos fixtures autouse haciendo lo mismo es redundante pero no incorrecto).

- [ ] **Step 4: Migrar los 2 archivos cuya fixture queda 100% redundante (borrar la fixture completa)**

**`tests/services/test_parametro_service.py`** — la fixture no hace nada que el conftest raíz no
haga ya (crea el engine, crea las tablas, parchea `SessionLocal`, y su valor de retorno `engine` no
lo usa ningún test). Borrar por completo estas líneas:

```python
@pytest.fixture(autouse=True)
def _db_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    return engine


```

y en los imports del encabezado, quitar `from sqlalchemy import create_engine`,
`from sqlalchemy.orm import sessionmaker`, y cambiar `from database.models import Base, ParametroLegal`
por `from database.models import ParametroLegal` (Base ya no se usa en el archivo). Dejar intacto
`import database.session as session_module` (lo sigue usando `_insertar`).

**`tests/scripts/test_migrate_parametros_legales.py`** — su fixture solo prepara el engine vacío (el
sembrado real lo hace cada test llamando a `migrar()` explícitamente); el conftest raíz ya deja un
engine en memoria con `database_module.engine` y `session_module.SessionLocal` parcheados antes de
que arranque cada test, así que la fixture es enteramente redundante. Borrar por completo:

```python
@pytest.fixture(autouse=True)
def _db_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    return engine


```

y en los imports, quitar `from sqlalchemy import create_engine`, `from sqlalchemy.orm import sessionmaker`,
y `import database.database as database_module`. Dejar intactos `import database.session as
session_module`, `from database.models import ParametroLegal` y el resto del archivo (los `migrar()`
explícitos dentro de cada test no cambian).

- [ ] **Step 5: Correr esos 2 archivos**

Run: `python -m pytest tests/services/test_parametro_service.py tests/scripts/test_migrate_parametros_legales.py -v`
Expected: todos PASS, mismo conteo que antes de tocarlos.

- [ ] **Step 6: Simplificar los 2 archivos que siembran vía `migrar()` (dejar solo la llamada a `migrar()`)**

**`tests/engine/tax/test_actualizacion_867_1.py`** — cambiar:

```python
@pytest.fixture(autouse=True)
def _parametros_legales_reales_en_memoria(monkeypatch):
    # Usa la siembra real (scripts/migrate_parametros_legales.migrar()) en vez
    # de una fixture con datos de prueba: el caso de ejemplo del despacho
    # (Preguntas-Para-Abogado.md, Sprint 15) cae dentro del rango historico
    # real de IPC/IBC-usura (1997-2026 / 1967-2025), asi que se verifica
    # contra los datos reales del sistema, no contra datos inventados.
    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    from scripts.migrate_parametros_legales import migrar
    migrar()
```

por:

```python
@pytest.fixture(autouse=True)
def _parametros_legales_reales_en_memoria():
    # Usa la siembra real (scripts/migrate_parametros_legales.migrar()) en vez
    # de una fixture con datos de prueba: el caso de ejemplo del despacho
    # (Preguntas-Para-Abogado.md, Sprint 15) cae dentro del rango historico
    # real de IPC/IBC-usura (1997-2026 / 1967-2025), asi que se verifica
    # contra los datos reales del sistema, no contra datos inventados. El
    # engine en memoria y los parches de database_module.engine /
    # session_module.SessionLocal ya los deja listos el conftest.py raiz
    # (Sprint 28) antes de que esta fixture arranque.
    from scripts.migrate_parametros_legales import migrar
    migrar()
```

y quitar del encabezado `from sqlalchemy import create_engine`, `from sqlalchemy.orm import sessionmaker`,
`import database.database as database_module`, `import database.session as session_module` (ninguno
se usa ya en el resto del archivo).

**`tests/engine/test_historical_index.py`** — cambiar:

```python
@pytest.fixture(autouse=True)
def _parametros_legales_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    from scripts.migrate_parametros_legales import migrar
    migrar()
```

por:

```python
@pytest.fixture(autouse=True)
def _parametros_legales_en_memoria():
    # El engine en memoria y los parches de database_module.engine /
    # session_module.SessionLocal ya los deja listos el conftest.py raiz
    # (Sprint 28) antes de que esta fixture arranque.
    from scripts.migrate_parametros_legales import migrar
    migrar()
```

y quitar del encabezado `from sqlalchemy import create_engine`, `from sqlalchemy.orm import sessionmaker`,
`import database.database as database_module`, `import database.session as session_module`.
Verificado al escribir este plan (`grep -n "database_module|session_module"
tests/engine/test_historical_index.py`): las 4 únicas apariciones de ambos nombres en todo el archivo
(~270 líneas, incluye otra fixture no-autouse más abajo para un caso de IPC de octubre) son las 2
líneas de `import` y las 2 líneas de `monkeypatch.setattr(...)` que se están borrando — ningún otro
lugar del archivo los usa, así que ambos imports quedan 100% libres para eliminar sin revisar nada
más.

- [ ] **Step 7: Correr esos 2 archivos**

Run: `python -m pytest tests/engine/tax/test_actualizacion_867_1.py tests/engine/test_historical_index.py -v`
Expected: todos PASS, mismo conteo que antes.

- [ ] **Step 8: Simplificar los 9 archivos que siembran filas de `ParametroLegal` a mano (quitar solo las 3 líneas de setup redundante)**

En cada uno de estos 9 archivos, dentro de la fixture autouse existente, borrar exactamente estas 3
líneas (idénticas letra por letra en los 9 archivos):

```python
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
```

...dejando el resto del cuerpo de la fixture (el sembrado de `ParametroLegal`, `session.commit()`,
`session.close()`, comentarios) intacto. Como ya no queda ningún uso de `monkeypatch` dentro de la
fixture, quitarlo también de la firma (`def _nombre_fixture(monkeypatch):` → `def _nombre_fixture():`).
En el encabezado de cada archivo, quitar `from sqlalchemy import create_engine`,
`from sqlalchemy.orm import sessionmaker`, y cambiar `from database.models import Base, ParametroLegal`
por `from database.models import ParametroLegal` (verificar primero que `Base` no se use en ningún otro
lugar del archivo — no debería, según el grep hecho al escribir este plan). Dejar intacto
`import database.session as session_module` (lo sigue usando el resto de la fixture vía
`session_module.get_session()`).

Los 9 archivos:

1. `tests/temporal/test_prescripcion.py` — fixture `_parametros_prescripcion_en_memoria`
2. `tests/engine/tax/test_moratory_interest.py` — fixture `_parametro_et635_en_memoria`
3. `tests/engine/tax/test_sanciones.py` — fixture `_parametros_sanciones_en_memoria`
4. `tests/engine/labor/test_ibl.py` — fixture `_ipc_en_memoria`
5. `tests/engine/costs/test_agencias_en_derecho.py` — fixture `_db_en_memoria`
6. `tests/engine/test_usury_validator.py` — fixture `_db_en_memoria`
7. `tests/engine/test_smlmv_to_uvt.py` — fixture `_db_en_memoria`
8. `tests/engine/labor/test_moratory_indemnity.py` — fixture `_parametros_ibc_usura_en_memoria`
9. `tests/engine/labor/test_seguridad_social.py` — fixture `_parametros_seguridad_social_en_memoria`
   (**ojo**: este archivo además usa `session_module.get_session()` en un test más abajo, fuera de la
   fixture — no tocar esa línea, solo las 3 de setup dentro de la fixture)

- [ ] **Step 9: Correr esos 9 archivos**

Run:
```bash
python -m pytest tests/temporal/test_prescripcion.py tests/engine/tax/test_moratory_interest.py tests/engine/tax/test_sanciones.py tests/engine/labor/test_ibl.py tests/engine/costs/test_agencias_en_derecho.py tests/engine/test_usury_validator.py tests/engine/test_smlmv_to_uvt.py tests/engine/labor/test_moratory_indemnity.py tests/engine/labor/test_seguridad_social.py -v
```
Expected: todos PASS, mismo conteo que antes de tocarlos.

- [ ] **Step 10: Correr la suite completa y ruff sobre los archivos tocados**

Run: `python -m pytest -q`
Expected: `692 passed, 1 skipped` (mismo conteo total que al final de la Task 2 — esta task no agrega
ni quita tests, solo centraliza la fixture).

Run: `python -m ruff check tests/conftest.py tests/temporal/test_prescripcion.py tests/engine/tax/test_actualizacion_867_1.py tests/engine/tax/test_moratory_interest.py tests/engine/tax/test_sanciones.py tests/engine/labor/test_ibl.py tests/services/test_parametro_service.py tests/engine/costs/test_agencias_en_derecho.py tests/engine/test_historical_index.py tests/engine/test_usury_validator.py tests/engine/test_smlmv_to_uvt.py tests/engine/labor/test_moratory_indemnity.py tests/engine/labor/test_seguridad_social.py tests/scripts/test_migrate_parametros_legales.py`
Expected: sin errores nuevos introducidos por este task (los 412 preexistentes en el resto del repo
no son responsabilidad de este comando porque solo apunta a los archivos tocados).

- [ ] **Step 11: Commit**

```bash
git add tests/conftest.py tests/views/conftest.py tests/temporal/test_prescripcion.py tests/engine/tax/test_actualizacion_867_1.py tests/engine/tax/test_moratory_interest.py tests/engine/tax/test_sanciones.py tests/engine/labor/test_ibl.py tests/services/test_parametro_service.py tests/engine/costs/test_agencias_en_derecho.py tests/engine/test_historical_index.py tests/engine/test_usury_validator.py tests/engine/test_smlmv_to_uvt.py tests/engine/labor/test_moratory_indemnity.py tests/engine/labor/test_seguridad_social.py tests/scripts/test_migrate_parametros_legales.py
git commit -m "test: centralizar la fixture de sesion en memoria en tests/conftest.py raiz"
```

---

### Task 4: Pipeline de CI (GitHub Actions)

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Crear el workflow**

Crear `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: windows-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.14"

      - name: Instalar dependencias
        run: pip install -r requirements.txt

      - name: Correr pytest
        env:
          QT_QPA_PLATFORM: offscreen
        run: python -m pytest -q
```

- [ ] **Step 2: Validar la sintaxis YAML localmente**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml', encoding='utf-8'))" `
Expected: sin errores (si `pyyaml` no está instalado en el venv, usar en su lugar:
`python -m pytest --collect-only -q` sobre el propio comando `python -m pytest -q` del workflow para
confirmar que es exactamente el comando que ya se validó en el baseline de este plan — no hace falta
instalar `pyyaml` solo para esto, revisar el archivo a mano contra la guía de sintaxis de GitHub
Actions es suficiente si `pyyaml` no está disponible).

- [ ] **Step 3: Revisar manualmente contra la corrida local**

Confirmar que `pip install -r requirements.txt` seguido de `QT_QPA_PLATFORM=offscreen python -m
pytest -q` es exactamente la secuencia que se corrió localmente en la fase de investigación de este
plan (resultado: `687 passed, 1 skipped`, o el conteo actualizado tras las Tasks 1-3 de este mismo
plan). No hay manera de confirmar una corrida real de GitHub Actions sin hacer push — este paso deja
constancia de que la lógica del workflow replica exactamente lo que ya se validó a mano.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "chore: agregar pipeline de CI minimo (GitHub Actions) que corre pytest en cada push/PR"
```

---

### Task 5: `CONTRIBUTING.md`

**Files:**
- Create: `CONTRIBUTING.md`

- [ ] **Step 1: Crear el archivo**

Crear `CONTRIBUTING.md` en la raíz:

```markdown
# Contribuir a BASTIUM

Gracias por tu interés en contribuir a BASTIUM. Esta guía explica cómo levantar el entorno de
desarrollo, correr las pruebas, la convención de commits del repositorio y cómo proponer un sprint
nuevo.

> Antes de contribuir código, lee el aviso legal en [SECURITY.md](SECURITY.md) y en la parte
> superior de este [README](README.md): BASTIUM calcula montos con efectos jurídicos reales.

## Levantar el entorno

Requiere Python 3.14 (la versión usada por el entorno de desarrollo del proyecto).

```bash
# 1. Clona el repositorio y entra a la carpeta
git clone https://github.com/JoseMsD21/BASTIUM-CALCULOS.git
cd BASTIUM-CALCULOS

# 2. Crea y activa un entorno virtual
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 3. Instala las dependencias
pip install -r requirements.txt
```

## Correr las pruebas

```bash
python -m pytest
```

Para correr solo un archivo o un test puntual:

```bash
python -m pytest tests/engine/test_legal_rates.py -v
python -m pytest -k "nombre_del_test"
```

Las pruebas de vistas (PySide6) instancian widgets reales y necesitan un display; si corres en un
entorno sin uno (una terminal remota, WSL sin X, o CI), exporta `QT_QPA_PLATFORM=offscreen` antes de
correr `pytest`.

## Lint

El repositorio usa [ruff](https://docs.astral.sh/ruff/) como linter/formatter (configurado en
`pyproject.toml`: line-length 99, target Python 3.14, reglas `E`/`F`/`I`/`UP`/`B`):

```bash
python -m ruff check .
python -m ruff format .
```

## Convención de commits

Los commits siguen un prefijo según el tipo de cambio, seguido de un resumen corto en español que
explica el *por qué* del cambio, no solo el *qué*:

- `feat:` — funcionalidad nueva.
- `fix:` — corrección de un bug.
- `docs:` — cambios de documentación únicamente.
- `test:` — cambios que solo agregan o corrigen pruebas.
- `chore:` — tareas de mantenimiento (dependencias, configuración, housekeeping) que no cambian
  comportamiento de la aplicación.

Ejemplo: `fix: corregir redondeo de intereses moratorios en liquidacion laboral`.

## Cómo proponer un sprint nuevo

El trabajo del proyecto se organiza en "sprints" documentados en [`Pendientes.md`](Pendientes.md).
Para proponer uno nuevo, agrega una sección al final del archivo siguiendo el mismo formato que los
sprints existentes:

- Un encabezado `## Sprint N — Título corto`.
- **Hallazgos:** qué problema o carencia motiva el sprint, con evidencia concreta (archivo, línea,
  comportamiento observado — no una intuición vaga).
- **Código nuevo a crear:** lista concreta de archivos o módulos a crear/modificar.
- **Definición de Hecho:** condiciones verificables (tests en verde, comportamiento específico
  confirmado) que indican que el sprint terminó.

No edites sprints ya cerrados salvo para corregir un hallazgo de su propio cierre; si encuentras un
problema nuevo relacionado con un sprint cerrado, ábrelo como un hallazgo dentro de un sprint futuro
en vez de reabrir el ya cerrado.

## Al contribuir

Al enviar una contribución (issue, pull request, o cualquier otro aporte), aceptas que se licencie
bajo los mismos términos del proyecto. La licencia definitiva todavía está pendiente de elegir — ver
el Sprint 38 en [`Pendientes.md`](Pendientes.md).
```

- [ ] **Step 2: Commit**

```bash
git add CONTRIBUTING.md
git commit -m "docs: agregar CONTRIBUTING.md para colaboradores externos"
```

---

### Task 6: `SECURITY.md`

**Files:**
- Create: `SECURITY.md`

- [ ] **Step 1: Crear el archivo**

Crear `SECURITY.md` en la raíz:

```markdown
# Seguridad

## Aviso legal

BASTIUM es una **herramienta de apoyo** para el cálculo de liquidaciones jurídicas (civil, laboral,
comercial, sancionatorio, tributario, pensional) en Colombia. **No sustituye la asesoría de un
abogado colegiado ni garantiza exactitud jurídica.** Los resultados que produce dependen de los datos
que se le ingresen y de los parámetros legales vigentes cargados en el sistema — antes de usar
cualquier resultado en un proceso judicial o administrativo real, quien lo use **debe verificarlo
contra la norma vigente** y contra el criterio de un profesional del derecho. El proyecto y sus
autores no asumen responsabilidad por decisiones tomadas con base en los cálculos que produce.

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
[reporte de bug](.github/ISSUE_TEMPLATE/bug_report.md) — salvo que el error de cálculo derive de una
falla de seguridad (ej. datos corruptos por una inyección).

## Versiones soportadas

BASTIUM es software pre-1.0 en desarrollo activo. Mientras no exista una versión 1.0 estable, solo la
última versión etiquetada en la rama `main` recibe correcciones de seguridad.
```

- [ ] **Step 2: Commit**

```bash
git add SECURITY.md
git commit -m "docs: agregar SECURITY.md con aviso legal y proceso de reporte de vulnerabilidades"
```

---

### Task 7: Badges y aviso legal corto en `README.md`

**Files:**
- Modify: `README.md:1-2`

- [ ] **Step 1: Insertar badges y aviso legal justo después del título**

En `README.md`, cambiar las líneas 1-3 (título + línea en blanco + primer párrafo) de:

```markdown
# BASTIUM — Ecosistema de Liquidación Forense

BASTIUM es una aplicación de escritorio para abogados y despachos jurídicos en Colombia. Permite
```

por:

```markdown
# BASTIUM — Ecosistema de Liquidación Forense

[![CI](https://github.com/JoseMsD21/BASTIUM-CALCULOS/actions/workflows/ci.yml/badge.svg)](https://github.com/JoseMsD21/BASTIUM-CALCULOS/actions/workflows/ci.yml)
![Versión](https://img.shields.io/badge/versi%C3%B3n-0.1.0-blue)
![Licencia](https://img.shields.io/badge/licencia-por%20definir%20(Sprint%2038)-lightgrey)

> ⚠️ **Aviso legal:** BASTIUM es una herramienta de apoyo para el cálculo de liquidaciones — **no
> sustituye la asesoría de un abogado colegiado ni garantiza exactitud jurídica**. Verifica los
> resultados contra la norma vigente antes de usarlos en un proceso real. Ver
> [SECURITY.md](SECURITY.md#aviso-legal) para el detalle.

BASTIUM es una aplicación de escritorio para abogados y despachos jurídicos en Colombia. Permite
```

No tocar nada del resto del archivo — el resto de `README.md` (estado del proyecto, áreas
implementadas, etc.) pertenece a otros sprints en paralelo y debe quedar exactamente igual para no
generar conflictos de merge innecesarios.

- [ ] **Step 2: Confirmar el diff es mínimo**

Run: `git diff README.md`
Expected: solo se agregan las 8 líneas nuevas (3 badges + línea en blanco + 4 líneas de blockquote +
línea en blanco) entre el título y el párrafo original; ninguna línea existente se modifica ni se
borra.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: agregar badges de CI/version/licencia y aviso legal corto en README"
```

---

### Task 8: Plantillas de Issues y Pull Request

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/ISSUE_TEMPLATE/feature_request.md`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`

- [ ] **Step 1: Crear la plantilla de reporte de bug**

Crear `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Reporte de bug
about: Reporta un cálculo incorrecto, un error de la aplicación o un comportamiento inesperado
title: "[BUG] "
labels: bug
---

## Descripción

Describe el problema de forma clara y concisa.

## Pasos para reproducir

1. Ir a '...'
2. Ingresar '...'
3. Ver el error

## Comportamiento esperado

Qué esperabas que pasara (si es un cálculo, indica el valor esperado y la norma/artículo en que te
basas).

## Comportamiento actual

Qué pasó en realidad (valor obtenido, mensaje de error, captura de pantalla si aplica).

## Entorno

- Versión de BASTIUM: <!-- ver app/_version.py -->
- Sistema operativo:
- Área del derecho afectada (si aplica): <!-- Civil/Familia, Laboral, Comercial, Sancionatorio, Tributario, Pensional -->

## Contexto adicional

Cualquier otra información relevante (expediente de ejemplo, referencia normativa citada, etc).
```

- [ ] **Step 2: Crear la plantilla de solicitud de funcionalidad**

Crear `.github/ISSUE_TEMPLATE/feature_request.md`:

```markdown
---
name: Solicitud de funcionalidad
about: Propón una funcionalidad nueva o una mejora
title: "[FEATURE] "
labels: enhancement
---

## Problema que resuelve

¿Qué limitación o carencia actual motiva esta solicitud?

## Solución propuesta

Describe la funcionalidad que te gustaría ver.

## Alternativas consideradas

¿Consideraste alguna otra forma de resolver el mismo problema?

## Contexto adicional

Norma legal, artículo o caso de uso concreto que respalda la solicitud — BASTIUM calcula montos con
efectos jurídicos reales, así que las solicitudes con respaldo normativo se priorizan más fácil.
```

- [ ] **Step 3: Crear la plantilla de Pull Request**

Crear `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## Descripción

Describe qué cambia este PR y por qué.

## Tipo de cambio

- [ ] `feat` — funcionalidad nueva
- [ ] `fix` — corrección de un bug
- [ ] `docs` — documentación
- [ ] `test` — pruebas
- [ ] `chore` — mantenimiento / housekeeping

## Cómo se probó

Describe cómo verificaste el cambio (comandos de `pytest` corridos, pasos manuales, etc).

## Checklist

- [ ] `python -m pytest` pasa localmente.
- [ ] `python -m ruff check .` no agrega errores nuevos en los archivos que toqué.
- [ ] Si el cambio afecta un cálculo legal, cité la norma/artículo relevante en la descripción o en
      comentarios del código.
- [ ] Actualicé `Pendientes.md`/`CHANGELOG.md` si aplica.
```

- [ ] **Step 4: Commit**

```bash
git add .github/ISSUE_TEMPLATE/bug_report.md .github/ISSUE_TEMPLATE/feature_request.md .github/PULL_REQUEST_TEMPLATE.md
git commit -m "docs: agregar plantillas de Issues y Pull Request"
```

---

### Task 9: `CHANGELOG.md`

**Files:**
- Create: `CHANGELOG.md`

- [ ] **Step 1: Crear el archivo**

Crear `CHANGELOG.md` en la raíz:

```markdown
# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/), y este proyecto usa
[Versionado Semántico](https://semver.org/lang/es/).

## [0.1.0] - 2026-08-03

Primera versión etiquetada del proyecto. BASTIUM ya calcula liquidaciones completas en las áreas
Civil/Familia, Comercial, Sancionatorio, Honorarios/Litigio, Laboral y Tributario, con exportación a
PDF/Word, historial de auditoría por expediente, y parámetros legales versionados editables desde la
interfaz. Este sprint (28) no agrega funcionalidad de cálculo — profesionaliza el repositorio de cara
a su publicación pública en GitHub.

### Added
- Integración continua (GitHub Actions) que corre la suite de `pytest` en cada push/PR a `main`.
- `__version__` (`app/_version.py`), primera versión etiquetada del proyecto.
- Variable de entorno `BASTIUM_DB_PATH` para configurar la ruta de `bastium.db` sin editar código
  fuente.
- `conftest.py` raíz en `tests/` con la fixture de sesión en memoria compartida, reemplazando su
  duplicación en 13+ archivos de test.
- `CONTRIBUTING.md`, `SECURITY.md` (con aviso legal), plantillas de Issues/PR
  (`.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`).
- Badges de CI, versión y licencia, y aviso legal corto, en `README.md`.

[0.1.0]: https://github.com/JoseMsD21/BASTIUM-CALCULOS/releases/tag/v0.1.0
```

- [ ] **Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: agregar CHANGELOG.md arrancando en la version 0.1.0"
```

---

### Task 10: Tag de git para la primera versión

**Files:** (ninguno — solo un tag de git, sin cambios de archivos)

- [ ] **Step 1: Confirmar que el árbol de trabajo está limpio**

Run: `git status`
Expected: `nothing to commit, working tree clean` (todas las tasks anteriores ya están commiteadas)

- [ ] **Step 2: Correr la suite completa una última vez**

Run: `python -m pytest -q`
Expected: mismo conteo final que al cierre de la Task 3 (692 passed, 1 skipped, salvo que Tasks 4-9
hayan agregado tests — no deberían, son solo documentación/CI).

- [ ] **Step 3: Crear el tag anotado**

```bash
git tag -a v0.1.0 -m "BASTIUM v0.1.0 - primera version etiquetada del proyecto (Sprint 28)"
```

- [ ] **Step 4: Verificar el tag**

Run: `git tag -l -n9 v0.1.0`
Expected: muestra el tag `v0.1.0` con el mensaje del paso anterior. **No hacer `git push --tags`** —
el orquestador decide si se empuja al remoto.

---

## Notas para el orquestador (no son tareas de este plan)

- Las 3 ramas locales huérfanas del hallazgo 5 (`specs-en-progreso`,
  `sprint10-exportacion-pdf-word-backup`, `sprint3-4-docs-recuperados`) ya no existen en el repo —
  confirmado con `git branch -a` al ejecutar este plan. El hallazgo está obsoleto y puede marcarse
  como resuelto en `Pendientes.md` al fusionar.
- El test "1 skipped" (`tests/services/test_area_strategy.py`) sigue apareciendo en la suite de esta
  rama porque su corrección es del Sprint 27, que corre en paralelo en otro worktree — esperado, no
  es un defecto de este plan.
- El tag `v0.1.0` se crea localmente en esta rama; el orquestador decide si lo empuja a `origin`.
