"""Helper compartido para tests/views/ (Sprint 114, hallazgo 1): centraliza
el bloque "engine SQLite en memoria nuevo + monkeypatch de SessionLocal" que
8 archivos de este directorio repetian literalmente, cada uno bajo su propio
helper local (`_sesion_en_memoria`, o embebido directo en un helper de
siembra de datos como `_obligacion_de_prueba`/`_expediente_de_prueba`).

No reemplaza la fixture autouse `_db_en_memoria_por_defecto` de
`tests/conftest.py` (Sprint 28) -- esa ya deja `session_module.SessionLocal`
listo antes de CADA test, pero varios archivos de `tests/views/` necesitan
ademas un helper explicito que un test pueda llamar a mitad de su cuerpo
(a veces mas de una vez, ej. `test_abonos.py`) para levantar un engine
nuevo y sembrar datos propios -- este modulo es ese helper, sin cambiar el
comportamiento de ninguno de los 8 archivos que lo usaban por su cuenta."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import Base


def crear_sesion_en_memoria(monkeypatch):
    """Crea un engine SQLite en memoria nuevo, migra el esquema completo
    (`Base.metadata.create_all`) y parchea `session_module.SessionLocal`
    para que todo el codigo de produccion (vistas, servicios) opere sobre
    el. Retorna una sesion ya abierta contra ese engine, lista para sembrar
    datos de prueba -- los llamadores que no necesitan la sesion de vuelta
    simplemente ignoran el valor de retorno."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )
    return session_module.get_session()
