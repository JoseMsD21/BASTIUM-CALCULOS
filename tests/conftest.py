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
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )
