# Contribuir a BASTIUM

Gracias por tu interés en contribuir a BASTIUM. Esta guía explica cómo levantar el entorno de
desarrollo, correr las pruebas, la convención de commits del repositorio y cómo proponer un sprint
nuevo.

> Antes de contribuir código, lee el aviso legal en [SECURITY.md](docs/SECURITY.md) y en la parte
> superior de este [README](README.md): BASTIUM calcula montos con efectos jurídicos reales.

## Levantar el entorno

Requiere Python 3.12 o más nuevo; **recomendado 3.15** (`py -3.15 -m venv .venv`). La CI corre en 3.13, 3.14
y 3.15. Si `pip install` de `PySide6` se queda sin avanzar, borra el `.venv` y créalo de nuevo con 3.15 o 3.13.

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
`pyproject.toml`: line-length 99, target Python 3.15, reglas `E`/`F`/`I`/`UP`/`B`):

```bash
python -m ruff check .
python -m ruff format .
```

## Flujo de trabajo del equipo (paso a paso)

`main` está protegida: **nadie sube cambios directamente a `main`**. Todo cambio entra mediante un
Pull Request (PR) que el responsable del proyecto (@JoseMsD21) revisa y aprueba antes de integrarse.
La CI (ruff + pytest con cobertura mínima de 90%) también debe estar en verde.

### Una sola vez (configuración inicial)

1. Acepta la invitación al repositorio que llega a tu correo de GitHub.
2. Clona el repositorio y levanta el entorno (sección "Levantar el entorno" arriba).
3. Configura tu identidad en git (los commits quedan firmados con estos datos):

   ```bash
   git config user.name "Tu Nombre"
   git config user.email "tu-correo-de-github@ejemplo.com"
   ```

### Cada vez que vayas a hacer un cambio

1. **Parte siempre de `main` actualizada:**

   ```bash
   git checkout main
   git pull origin main
   ```

2. **Crea una rama nueva** con un nombre que diga qué haces (`tipo/descripcion-corta`):

   ```bash
   git checkout -b fix/redondeo-intereses-laboral
   ```

3. **Haz tus cambios y pruébalos localmente** antes de commitear:

   ```bash
   python -m ruff check .
   python -m pytest
   ```

4. **Commitea** siguiendo la [convención de commits](#convención-de-commits):

   ```bash
   git add archivo1.py tests/test_archivo1.py
   git commit -m "fix: corregir redondeo de intereses moratorios en liquidacion laboral"
   ```

   Agrega los archivos por nombre (no uses `git add .` a ciegas): así evitas subir por error
   `bastium.db`, respaldos o archivos locales.

5. **Sube tu rama** (nunca `main`):

   ```bash
   git push -u origin fix/redondeo-intereses-laboral
   ```

6. **Abre el Pull Request** en GitHub: entra al repositorio, pulsa "Compare & pull request" y llena
   la plantilla (qué cambia, por qué, cómo lo probaste y el checklist). Si tu cambio toca un cálculo
   legal, cita la norma o el artículo.

7. **Espera la revisión.** El responsable puede pedir cambios: hazlos en la misma rama, repite los
   pasos 3-5 (el PR se actualiza solo) y avísale. Cuando lo apruebe y la CI esté en verde, él
   integra el PR.

8. **Limpia tu entorno** después de que se integre:

   ```bash
   git checkout main
   git pull origin main
   git branch -d fix/redondeo-intereses-laboral
   ```

### Tablero Kanban

El trabajo se organiza en el tablero [BASTIUM - Kanban](https://github.com/users/JoseMsD21/projects/1)
(GitHub Projects). Columnas: Backlog → Listo → En progreso → En revisión → Hecho, más Bloqueado para lo que
espera algo externo (normalmente el despacho).

- **Una tarjeta = un issue = una rama = un PR.** En la descripción del PR escribe `Closes #N` con el número
  del issue, para que la tarjeta se cierre sola al integrarse.
- **Límites WIP:** Listo 5, En progreso 1–2 por persona, En revisión 3. Si "En revisión" está llena, revisa
  un PR ajeno antes de empezar algo nuevo.
- Mueve tu tarjeta a "En progreso" al crear la rama y a "En revisión" al abrir el PR.
- Una tarjeta bloqueada dice qué espera y de quién; si es una pregunta al despacho, enlaza su sección en
  `docs/Preguntas-Para-Abogado-Abiertas.md`.

El tablero es **público**: cualquiera puede **verlo** sin pedir acceso. Los colaboradores del equipo tienen rol
**Write** en el tablero para mover tarjetas (ver [Permisos](#permisos-y-reglas-de-main)).

### Google Drive del equipo

- [Actas y avances](https://drive.google.com/drive/project/1Vf9_sVuHZXNbO3Z8IKPsw2zZyB8jVodV): actas de reunión, avances semanales, soporte de las respuestas del despacho.
- [Propuestas, mockups y auditorías](https://drive.google.com/drive/folders/1ZYauFW9pEKFfjMCC1RIHtDJ2pwrut78f): material de trabajo del equipo.

Drive es para conversar y proponer; **el repositorio es la fuente de verdad**. Lo que se decide en Drive se pasa a un
issue del tablero o a la documentación del repo.

Detalle y ritmo de reuniones en [docs/PLAN_INTEGRACION_NOVIEMBRE.md](docs/PLAN_INTEGRACION_NOVIEMBRE.md#5-forma-de-trabajo-kanban).

### Reglas importantes

- **Un PR = un cambio con un solo propósito.** PRs pequeños se revisan más rápido.
- **No subas datos reales de clientes ni expedientes.** Este repositorio es público. Tampoco subas
  `bastium.db` (ni ningún `*.db`), `backups/`, PDFs/Excel generados con datos reales ni la carpeta
  `.venv` (ya están en `.gitignore`; si git te los ofrece, detente y consulta).
- **No subas secretos** (contraseñas, tokens, claves).
- **No reescribas el historial** de una rama ya publicada (`push --force`) sin acordarlo antes.
- Si tu rama quedó atrás de `main` (GitHub no deja integrar hasta ponerla al día) o avisa de conflictos, trae los cambios con
  `git fetch origin` y `git merge origin/main` en tu rama, resuelve los conflictos, vuelve a correr
  los tests y haz `git push`. Si no sabes resolverlos, pide ayuda antes de forzar nada.
- Si la CI falla, abre el detalle del check fallido en el PR, corrige en tu rama y vuelve a subir.

### Permisos y reglas de `main`

Configuración real en GitHub, verificada el 2026-11-23. Si cambias algo en *Settings*, actualiza esta sección en el
mismo PR.

**Roles en el repositorio:**

| Persona | Rol | Puede | No puede |
|---|---|---|---|
| @JoseMsD21 | Admin (responsable del proyecto) | Todo, incluida la configuración | — |
| Colaboradores del equipo | **Write** | Crear ramas, subir a sus ramas, abrir y comentar PR, gestionar issues | Subir a `main`, cambiar la configuración, saltarse las reglas |

**Regla "Main"** (*Settings → Rules → Rulesets → Main*), activa sobre la rama principal:

- Todo cambio entra por **Pull Request**; nadie sube directo a `main`.
- No se puede borrar `main` ni reescribir su historia (`push --force`).
- **1 aprobación del dueño del código** (`.github/CODEOWNERS`: @JoseMsD21). La aprobación se invalida si se suben
  cambios nuevos, la última subida necesita aprobación propia y todos los comentarios deben quedar resueltos.
- **Checks obligatorios:** `test (3.13)`, `test (3.14)` y `test (3.15)` (ruff + pytest con cobertura ≥ 90 %). El 3.15
  se agregó el 2026-11-23 al volverse la versión principal.
- **La rama debe estar al día con `main`** antes de integrar (activado el 2026-11-23). Si `main` avanzó después de
  abrir tu PR, GitHub muestra el botón **"Update branch"**: púlsalo (o haz `git merge origin/main` en tu rama) y
  espera a que la CI vuelva a pasar. Así la CI prueba exactamente el código que va a quedar en `main` (evita
  errores como el del Sprint 104, cuando una combinación "sin conflicto" dejó código en la función equivocada).
- **Quién puede saltarse la regla:** solo el rol Admin, y solo al integrar un PR (`gh pr merge --admin`), nunca subiendo
  directo.

**Excepción vigente — "opción B" para los PR del responsable:** como @JoseMsD21 es el único dueño del código y
GitHub no deja aprobar el PR propio, sus PR se integran con `--admin` **después de que la CI esté en verde**. Así se
integraron sus PR desde noviembre de 2026. Condiciones: la CI completa en verde (las tres versiones), el PR documenta qué cambia y
por qué, y nunca se usa para PR de otras personas (esos esperan la aprobación normal). Decisión del 2026-11-23: se
mantiene "por ahora"; para cumplir la regla de "aprobación de otra persona" sin excepción, basta agregar un
compañero en `.github/CODEOWNERS` (por ejemplo `* @JoseMsD21 @usuario`).

**Tablero Kanban:** que el proyecto sea público solo permite verlo. Para mover tarjetas, cada colaborador debe estar
en *tablero → ⋯ → Settings → Manage access* con rol **Write**. Desde el 2026-11-23 los colaboradores del repositorio
están agregados al tablero con **Write**. Al sumar a alguien nuevo al equipo, agrégalo en los dos lugares:
repositorio (*Settings → Collaborators*) y tablero (*Manage access*).

**Cómo verificarlo tú mismo:**

```bash
gh api repos/JoseMsD21/BASTIUM-CALCULOS/collaborators --jq '.[] | {login, role_name}'
gh api repos/JoseMsD21/BASTIUM-CALCULOS/rulesets/27289585 --jq '.rules'
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

Si tu sprint introduce o cambia una **decisión de arquitectura** (no un detalle de UI ni un bugfix
puntual — ej. una librería nueva, un cambio en cómo se persisten los datos, una decisión de seguridad),
agrégala como un ADR nuevo en [docs/ARQUITECTURA_ADR.md](docs/ARQUITECTURA_ADR.md).

## Al contribuir

Al enviar una contribución (issue, pull request, o cualquier otro aporte), aceptas que se licencie
bajo los mismos términos del proyecto: [Apache License 2.0](LICENSE).
