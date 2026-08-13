from app.services.restablecer_service import crear_backup_de_base_de_datos


def test_crear_backup_de_base_de_datos_copia_el_archivo(tmp_path):
    origen = tmp_path / "bastium.db"
    origen.write_bytes(b"contenido-de-prueba-sqlite")

    destino = crear_backup_de_base_de_datos(db_path=origen)

    assert destino.exists()
    assert destino.parent == tmp_path / "backups"
    assert destino.name.startswith("bastium.db.bak-")
    assert destino.read_bytes() == b"contenido-de-prueba-sqlite"


def test_crear_backup_de_base_de_datos_crea_la_carpeta_backups_si_no_existe(tmp_path):
    origen = tmp_path / "bastium.db"
    origen.write_bytes(b"x")
    assert not (tmp_path / "backups").exists()

    crear_backup_de_base_de_datos(db_path=origen)

    assert (tmp_path / "backups").is_dir()
