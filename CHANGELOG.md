# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/), y este proyecto usa
[Versionado Semántico](https://semver.org/lang/es/).

## [0.1.0] - 2026-08-04

Primera versión etiquetada del proyecto. BASTIUM ya calcula liquidaciones completas en las áreas
Civil/Familia, Comercial, Sancionatorio, Honorarios/Litigio, Laboral y Tributario, con exportación a
PDF/Word, historial de auditoría por expediente, y parámetros legales versionados editables desde la
interfaz. Este sprint (28) no agrega funcionalidad de cálculo — profesionaliza el repositorio de cara
a su publicación pública en GitHub.

### Added
- Integración continua (GitHub Actions) que corre la suite de `pytest` en cada push/PR a `main`.
- `__version__` (`app/_version.py`), primera versión etiquetada del proyecto.
- Variable de entorno `BASTIUM_DB_PATH` para configurar la ruta de `bastium.db` sin editar código
  fuente.
- `conftest.py` raíz en `tests/` con la fixture de sesión en memoria compartida, reemplazando su
  duplicación en 13+ archivos de test.
- `CONTRIBUTING.md`, `SECURITY.md` (con aviso legal), plantillas de Issues/PR
  (`.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`).
- Badges de CI, versión y licencia, y aviso legal corto, en `README.md`.

[0.1.0]: https://github.com/JoseMsD21/BASTIUM-CALCULOS/releases/tag/v0.1.0
