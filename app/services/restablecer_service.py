"""Servicio de "Restablecer datos de fábrica" (Configuraciones › Restablecer):
borra expedientes y parametros legales de usuario, dejando la app como recien
instalada. Ver docs/superpowers/specs/2026-08-13-restablecer-datos-fabrica-design.md.

Dos funciones deliberadamente separadas (en vez de una sola que haga todo):
`crear_backup_de_base_de_datos` es I/O de archivo puro, sin sesion SQLAlchemy
-- se puede testear con cualquier archivo temporal, sin la fixture de base en
memoria. `restablecer_datos_fabrica` es ORM puro, sin tocar el sistema de
archivos -- se testea con la misma fixture en memoria que el resto de
tests/services/. El llamador (RestablecerView) orquesta ambas en el orden
correcto: primero el backup, y solo si tuvo exito, el borrado."""

import shutil
from datetime import datetime
from pathlib import Path

import database.session as session_module
from database.database import DB_PATH
from database.models import Expediente, ParametroLegal


def crear_backup_de_base_de_datos(db_path: Path | None = None) -> Path:
    """Copia el archivo de base de datos a `<carpeta-del-archivo>/backups/`,
    con el mismo patron de nombre (`<nombre>.bak-<timestamp>`) que ya usan los
    backups manuales existentes en esa carpeta (Sprint 64). `db_path` es
    opcional (default: `database.database.DB_PATH`, la base activa real) --
    los tests lo pasan explicito para nunca tocar el archivo real.

    Puede lanzar OSError (permiso denegado, disco lleno, etc.) -- el llamador
    debe abortar el resto del restablecimiento si esto falla, para nunca
    borrar datos sin backup exitoso."""
    origen = db_path if db_path is not None else DB_PATH
    carpeta_backups = origen.parent / "backups"
    carpeta_backups.mkdir(parents=True, exist_ok=True)
    marca_de_tiempo = datetime.now().strftime("%Y%m%d-%H%M%S")
    destino = carpeta_backups / f"{origen.name}.bak-{marca_de_tiempo}"
    shutil.copy2(origen, destino)
    return destino


def restablecer_datos_fabrica() -> None:
    """Borra TODOS los expedientes (obligaciones/abonos/eventos_laborales/
    descuentos_laborales/audit_logs se van en cascada, cascade="all,
    delete-orphan" en Expediente -- ver database/models.py) y todos los
    parametros_legales creados por un usuario (creado_por_sistema=False); los
    de sistema quedan intactos. No crea backup ni toca el tema -- eso es
    responsabilidad del llamador (RestablecerView), que orquesta backup +
    este borrado + reset de tema en el orden correcto."""
    session = session_module.get_session()
    try:
        for expediente in session.query(Expediente).all():
            session.delete(expediente)
        session.query(ParametroLegal).filter(
            ParametroLegal.creado_por_sistema.is_(False)
        ).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()
