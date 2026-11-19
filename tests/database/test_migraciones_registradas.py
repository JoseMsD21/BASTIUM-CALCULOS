"""Guardia (Sprint 118): toda migracion en scripts/migrate_*.py debe estar registrada
en database.database.aplicar_migraciones_pendientes().

Origen: Sprint 117. `scripts/migrate_salario_domestico_sprint96.py` existia, pero
nadie la llamaba al arrancar, y una bastium.db anterior al Sprint 96 rompia la app con
`no such column: obligaciones.salario_diario`. Esta prueba hace que ese olvido falle
en CI en vez de en la maquina del usuario.
"""

import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def _funcion_aplicar_migraciones() -> ast.FunctionDef:
    arbol = ast.parse((RAIZ / "database" / "database.py").read_text(encoding="utf-8"))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.FunctionDef) and nodo.name == "aplicar_migraciones_pendientes":
            return nodo
    raise AssertionError("No se encontro aplicar_migraciones_pendientes en database.py")


def _alias_importados(funcion: ast.FunctionDef) -> dict[str, str]:
    """modulo scripts.migrate_* -> nombre local con el que se importa su `migrar`."""
    alias = {}
    for nodo in ast.walk(funcion):
        if (
            isinstance(nodo, ast.ImportFrom)
            and nodo.module
            and nodo.module.startswith("scripts.migrate_")
        ):
            for nombre in nodo.names:
                if nombre.name == "migrar":
                    alias[nodo.module.removeprefix("scripts.")] = nombre.asname or nombre.name
    return alias


def _nombres_llamados(funcion: ast.FunctionDef) -> set[str]:
    return {
        nodo.func.id
        for nodo in ast.walk(funcion)
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name)
    }


def test_toda_migracion_del_directorio_scripts_se_importa_al_arrancar():
    en_disco = {p.stem for p in (RAIZ / "scripts").glob("migrate_*.py")}
    importadas = set(_alias_importados(_funcion_aplicar_migraciones()))
    faltantes = sorted(en_disco - importadas)
    assert not faltantes, (
        "Migraciones que existen en scripts/ pero aplicar_migraciones_pendientes() no "
        f"importa (una bastium.db vieja se quedaria sin ellas): {faltantes}"
    )


def test_toda_migracion_importada_se_llama():
    funcion = _funcion_aplicar_migraciones()
    llamadas = _nombres_llamados(funcion)
    sin_llamar = sorted(
        modulo for modulo, alias in _alias_importados(funcion).items() if alias not in llamadas
    )
    assert not sin_llamar, f"Migraciones importadas pero nunca llamadas: {sin_llamar}"
