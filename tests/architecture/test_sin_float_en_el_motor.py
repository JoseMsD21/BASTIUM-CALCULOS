"""Regla inquebrantable: cero `float` en el motor, el dominio y la API (dinero y tasas).

Se prohiben: llamadas `float(...)`, anotaciones `: float` y literales flotantes de dinero.
Se permite UN uso defensivo: `isinstance(x, float)` (o dentro de una tupla), porque es la
guarda que RECHAZA floats en la frontera (contratos y canonizacion).
"""

import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIRECTORIOS = ("app/engine", "app/domain", "bastium_api")


def _nombres_en_guardas_isinstance(arbol: ast.AST) -> set[int]:
    """`id()` de los nodos Name que son el 2.o argumento de un isinstance (guarda de rechazo)."""
    permitidos: set[int] = set()
    for nodo in ast.walk(arbol):
        es_isinstance = (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Name)
            and nodo.func.id == "isinstance"
            and len(nodo.args) == 2
        )
        if es_isinstance:
            tipos = nodo.args[1]
            candidatos = tipos.elts if isinstance(tipos, ast.Tuple) else [tipos]
            permitidos.update(id(c) for c in candidatos if isinstance(c, ast.Name))
    return permitidos


def hallazgos_de_float(codigo: str, nombre: str = "<memoria>") -> list[str]:
    arbol = ast.parse(codigo)
    permitidos = _nombres_en_guardas_isinstance(arbol)
    hallazgos = []
    for nodo in ast.walk(arbol):
        es_llamada = (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Name)
            and nodo.func.id == "float"
        )
        es_nombre = (
            isinstance(nodo, ast.Name)
            and nodo.id == "float"
            and isinstance(nodo.ctx, ast.Load)
            and id(nodo) not in permitidos
        )
        if es_llamada or es_nombre:
            hallazgos.append(f"{nombre}:{nodo.lineno}")
    return hallazgos


def test_no_hay_float_en_motor_dominio_ni_api():
    violaciones = []
    for directorio in DIRECTORIOS:
        base = RAIZ / directorio
        if base.exists():
            for archivo in sorted(base.rglob("*.py")):
                violaciones += hallazgos_de_float(
                    archivo.read_text(encoding="utf-8"), str(archivo.relative_to(RAIZ))
                )
    assert violaciones == [], f"float prohibido en dinero/tasas: {violaciones}"


def test_el_detector_distingue_guarda_de_uso():
    """Autoprueba: la guarda isinstance se permite; llamada y anotacion se detectan."""
    assert hallazgos_de_float("isinstance(x, float)\nisinstance(x, (int, float))") == []
    assert hallazgos_de_float("y = float(x)") != []
    assert hallazgos_de_float("def f(a: float): ...") != []
    assert hallazgos_de_float("def f() -> float: ...") != []
    assert hallazgos_de_float("z = isinstance(x, float) and float(x)") != []
