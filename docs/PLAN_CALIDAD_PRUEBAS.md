# Plan de calidad y pruebas (QA) — BASTIUM

> Los comandos exactos para correr pruebas y lint viven en [CONTRIBUTING.md](../CONTRIBUTING.md) y no se
> repiten aquí. Este documento formaliza la **estrategia**: qué se prueba, cómo, y cuándo un sprint se
> considera terminado.

## Estrategia de pruebas

| Tipo | Herramienta | Alcance |
|---|---|---|
| Unitarias | `pytest` | Motores de cálculo puros (`app/engine/`): interés, indexación, prescripción, pensional, tributario — funciones sin efectos secundarios, verificables contra un cálculo manual con la fórmula legal exacta. |
| Integración | `pytest` | Estrategias de liquidación por área (`app/services/`), acceso a base de datos (`database/`), migraciones idempotentes. |
| Interfaz (GUI) | `pytest-qt` | Vistas PySide6 (`app/views/`) — instancian widgets reales; requieren `QT_QPA_PLATFORM=offscreen` en entornos sin display (CI, WSL sin X). |
| Regresión | `pytest` (suite completa) | Se corre completa antes de cerrar cualquier sprint — ver "Definición de Hecho" de cada sprint en [Pendientes.md](Pendientes.md). |
| Estilo / estático | `ruff check .` | Reglas `E`, `F`, `I`, `UP`, `B` (`pyproject.toml`), obligatorio en CI antes de correr pruebas. |
| Auditoría transversal | Revisión manual dirigida | Barridos periódicos de calidad de código y documentación (ej. Sprints 23-30) y QA real con casos de usuario sobre un módulo recién cerrado (ej. Sprints 39-45) — no automatizados, se agendan como sprints propios. |
| Verificación cruzada contra el despacho | Revisión manual | Comparar la implementación real (no solo el texto del sprint) contra la respuesta jurídica del despacho en `Preguntas-Para-Abogado-Respondidas.md`, caso por caso — ver ejemplo en "Auditoría cruzada" dentro de [Pendientes.md](Pendientes.md). |

## Entornos

- Local: `python -m pytest` (Windows/macOS/Linux, Python 3.14, con display para las pruebas de GUI).
- CI (GitHub Actions, `.github/workflows/ci.yml`): `windows-latest`, corre `ruff check .` y luego
  `pytest -q` con `QT_QPA_PLATFORM=offscreen`, en cada push y pull request a `main`.

## Trazabilidad requisito → sprint → prueba

Cada sprint de `Pendientes.md` sigue el mismo patrón obligatorio (ver
[CONTRIBUTING.md](../CONTRIBUTING.md#cómo-proponer-un-sprint-nuevo)):

1. **Hallazgos** — el problema o requisito, con evidencia concreta (archivo, línea, comportamiento
   observado), no una intuición.
2. **Código nuevo a crear** — lista concreta de archivos/módulos.
3. **Definición de Hecho** — condiciones verificables: tests en verde + comportamiento específico
   confirmado (a menudo contra un caso numérico real aportado por el despacho o el usuario).

Esto hace que cada requisito jurídico implementado tenga, por construcción, al menos un test que lo
verifica — no existe un requisito "implementado" sin su condición de aceptación correspondiente en el
propio sprint que lo cerró.

## Criterios de aceptación generales

- Suite completa en verde (`pytest -q`) y sin violaciones de `ruff check .` antes de cualquier merge a
  `main`.
- Todo resultado numérico de un motor de cálculo nuevo se verifica contra un cálculo manual con la fórmula
  legal exacta (citando artículo y página del PDF de requisitos cuando aplica), no solo contra el propio
  código que se está probando.
- Cuando existe un caso de prueba real aportado por el despacho o un usuario, ese caso se vuelve un test
  explícito (ej. Sentencia SL138-2024 en el módulo pensional, casos reales de alimentos en Familia) — no
  solo datos sintéticos.
- Ningún sprint se marca ✅ Completado en `Pendientes.md` sin que su Definición de Hecho se haya verificado
  literalmente, no asumido.

## Qué no cubre este plan

- Pruebas de carga/rendimiento formales — no se han planteado como necesarias para una app de escritorio de
  un solo usuario (ver [Requisitos no funcionales](REQUISITOS_NO_FUNCIONALES.md)).
- Pruebas de penetración/seguridad automatizadas — el canal de reporte de vulnerabilidades es manual, ver
  [SECURITY.md](SECURITY.md).
