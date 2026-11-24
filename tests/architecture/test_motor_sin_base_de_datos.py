"""Sprint 130 (fase 1 del parche de plataforma, tarjeta #64).

El motor de liquidacion debe poder importarse sin la base de datos (SQLAlchemy,
`database`), sin la libreria `holidays` y sin Qt. Es el requisito para exponerlo por
una API headless (`bastium_api`, decision #7) sin arrastrar la aplicacion de
escritorio. Desde el Sprint 104 `engine.py` importaba la causacion tramo a tramo al
inicio del archivo y con ella `historical_index` (SQLAlchemy + `database`) y
`calendar` (`holidays`).

Se corre en un proceso aparte para que los modulos ya cargados por otros tests no
oculten el problema.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
PROHIBIDOS = ("sqlalchemy", "database", "holidays", "PySide6")

_SCRIPT = """
import json, sys
sys.path.insert(0, {raiz!r})
import {modulo}
print(json.dumps(sorted(m for m in {prohibidos!r} if m in sys.modules)))
"""


@pytest.mark.parametrize(
    "modulo",
    [
        "app.engine.liquidation.engine",
        "app.engine.liquidation.politica",
        "app.engine.liquidation.result",
    ],
)
def test_el_motor_se_importa_sin_base_de_datos_ni_holidays_ni_qt(modulo):
    script = _SCRIPT.format(raiz=str(RAIZ), modulo=modulo, prohibidos=PROHIBIDOS)
    salida = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
        cwd=RAIZ,
    )
    cargados = json.loads(salida.stdout.strip().splitlines()[-1])
    assert cargados == [], f"{modulo} arrastra {cargados}"
