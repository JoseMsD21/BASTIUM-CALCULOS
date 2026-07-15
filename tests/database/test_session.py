from datetime import date

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import AreaDerecho, Base, Expediente


def test_get_session_returns_a_working_sqlalchemy_session(tmp_path, monkeypatch):
    test_engine = create_engine(f"sqlite:///{tmp_path / 'inline.db'}")
    Base.metadata.create_all(test_engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=test_engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="X-1",
            demandante="A",
            demandado="B",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()

    assert session.query(Expediente).count() == 1
    session.close()


def test_init_db_creates_the_expedientes_table(tmp_path, monkeypatch):
    import database.database as database_module

    test_path = tmp_path / "test_bastium.db"
    test_engine = create_engine(f"sqlite:///{test_path}")
    monkeypatch.setattr(database_module, "engine", test_engine)

    database_module.init_db()

    assert "expedientes" in inspect(test_engine).get_table_names()
