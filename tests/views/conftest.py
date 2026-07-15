import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import Base


@pytest.fixture(autouse=True)
def _db_en_memoria_por_defecto(monkeypatch):
    """
    Las vistas (ej. ExpedientesListView) consultan la base de datos al construirse
    (refrescar() en __init__). Sin esta fixture, tests que no configuran su propia
    sesion en memoria (ej. test_main_window.py) fallarian contra el archivo real
    bastium.db, que no tiene las tablas creadas en el entorno de test.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
