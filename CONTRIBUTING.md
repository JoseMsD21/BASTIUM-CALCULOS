# Contribuir a BASTIUM

Gracias por tu interés en contribuir a BASTIUM. Esta guía explica cómo levantar el entorno de
desarrollo, correr las pruebas, la convención de commits del repositorio y cómo proponer un sprint
nuevo.

> Antes de contribuir código, lee el aviso legal en [SECURITY.md](docs/SECURITY.md) y en la parte
> superior de este [README](README.md): BASTIUM calcula montos con efectos jurídicos reales.

## Levantar el entorno

Requiere Python 3.14 (la versión usada por el entorno de desarrollo del proyecto).

```bash
# 1. Clona el repositorio y entra a la carpeta
git clone https://github.com/JoseMsD21/BASTIUM-CALCULOS.git
cd BASTIUM-CALCULOS

# 2. Crea y activa un entorno virtual
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 3. Instala las dependencias
pip install -r requirements.txt
```

## Correr las pruebas

```bash
python -m pytest
```

Para correr solo un archivo o un test puntual:

```bash
python -m pytest tests/engine/test_legal_rates.py -v
python -m pytest -k "nombre_del_test"
```

Las pruebas de vistas (PySide6) instancian widgets reales y necesitan un display; si corres en un
entorno sin uno (una terminal remota, WSL sin X, o CI), exporta `QT_QPA_PLATFORM=offscreen` antes de
correr `pytest`.

## Lint

El repositorio usa [ruff](https://docs.astral.sh/ruff/) como linter/formatter (configurado en
`pyproject.toml`: line-length 99, target Python 3.14, reglas `E`/`F`/`I`/`UP`/`B`):

```bash
python -m ruff check .
python -m ruff format .
```

## Convención de commits

Los commits siguen un prefijo según el tipo de cambio, seguido de un resumen corto en español que
explica el *por qué* del cambio, no solo el *qué*:

- `feat:` — funcionalidad nueva.
- `fix:` — corrección de un bug.
- `docs:` — cambios de documentación únicamente.
- `test:` — cambios que solo agregan o corrigen pruebas.
- `chore:` — tareas de mantenimiento (dependencias, configuración, housekeeping) que no cambian
  comportamiento de la aplicación.
- `merge:` — cierre de un sprint completo, integrando en `main` el trabajo ya revisado de una rama o
  worktree de sprint (es el prefijo que usan casi todos los sprints recientes al cerrarse).
- `refactor:` — reestructuración de código existente sin cambiar su comportamiento observable.
- `perf:` — mejora de rendimiento (ej. resolver un patrón N+1 de consultas) sin cambiar comportamiento.
- `style:` — cambios de formato/estilo de código (espaciado, orden de imports) sin efecto funcional.
- `build:` — cambios al empaquetado, dependencias o pipeline de build/CI.

Ejemplo: `fix: corregir redondeo de intereses moratorios en liquidacion laboral`.

## Cómo proponer un sprint nuevo

El trabajo del proyecto se organiza en "sprints" documentados en [`Pendientes.md`](docs/Pendientes.md).
Para proponer uno nuevo, agrega una sección al final del archivo siguiendo el mismo formato que los
sprints existentes:

- Un encabezado `## Sprint N — Título corto`.
- **Hallazgos:** qué problema o carencia motiva el sprint, con evidencia concreta (archivo, línea,
  comportamiento observado — no una intuición vaga).
- **Código nuevo a crear:** lista concreta de archivos o módulos a crear/modificar.
- **Definición de Hecho:** condiciones verificables (tests en verde, comportamiento específico
  confirmado) que indican que el sprint terminó.

No edites sprints ya cerrados salvo para corregir un hallazgo de su propio cierre; si encuentras un
problema nuevo relacionado con un sprint cerrado, ábrelo como un hallazgo dentro de un sprint futuro
en vez de reabrir el ya cerrado.

## Al contribuir

Al enviar una contribución (issue, pull request, o cualquier otro aporte), aceptas que se licencie
bajo los mismos términos del proyecto: [Apache License 2.0](LICENSE).
