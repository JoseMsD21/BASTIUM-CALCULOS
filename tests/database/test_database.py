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
