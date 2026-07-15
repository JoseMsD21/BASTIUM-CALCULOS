from sqlalchemy.orm import Session, sessionmaker

from database.database import engine

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Session:
    return SessionLocal()
