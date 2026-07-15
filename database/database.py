from pathlib import Path

from sqlalchemy import create_engine

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"
engine = create_engine(f"sqlite:///{DB_PATH}")


def init_db() -> None:
    from database.models import Base

    Base.metadata.create_all(engine)
