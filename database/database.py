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
