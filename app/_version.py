"""Version de la aplicacion BASTIUM (Sprint 28).

Unica fuente de verdad para el numero de version -- se importa desde main.py
y, a futuro, desde cualquier pantalla que necesite mostrarlo (ej. un dialogo
"Acerca de", fuera de alcance de este sprint). No se usa setuptools_scm ni
un sistema de versionado automatico basado en tags: el proyecto todavia no
tiene un pyproject.toml de paquete instalable (solo el de configuracion de
ruff), asi que la version se actualiza a mano en este archivo y se etiqueta
con un tag de git ("git tag vX.Y.Z") en el mismo commit que la cambia.

0.1.0 es la primera version etiquetada del proyecto (Sprint 28): software
pre-1.0, en desarrollo activo, sin LICENSE definida todavia (ver Sprint 38).
"""

__version__ = "0.1.0"
