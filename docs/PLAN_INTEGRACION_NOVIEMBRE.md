# Plan de integración del paquete "BASTIUM VERSION NOVIEMBRE" y forma de trabajo del equipo

Última actualización: 2026-11-19 (Sprints 118 y 119).

Este documento explica qué traía el paquete de cambios de noviembre, qué se integró, qué no y por qué, y cómo
seguimos trabajando en equipo (Kanban + Drive). El detalle técnico está en [`Pendientes.md`](Pendientes.md),
Sprint 118. Las preguntas al despacho están en
[`Preguntas-Para-Abogado-Abiertas.md`](Preguntas-Para-Abogado-Abiertas.md), Sprint 118.

---

## 1. Qué es el paquete

`BASTIUM VERSION NOVIEMBRE.zip` (65 archivos, fechado 12/11/2026) **no es una versión completa de la
aplicación**. No trae la interfaz, la base de datos ni la mayor parte de `app/`. Es un conjunto de cambios para
superponer sobre este repositorio, producto de una auditoría del motor de cálculo:

| Bloque | Qué contiene |
|---|---|
| Mejoras de precisión | Política decimal en todos los hilos, `Decimal` en vez de `float` en PDF y línea de tiempo |
| Política de causación | Opción de redondear el interés una vez por tramo en vez de cada día |
| Calendario procesal propio | Festivos y vacancias sin la librería `holidays`, con perfiles por despacho |
| Capa API (`bastium_api`) | Servicio HTTP (FastAPI) para usar el motor desde otros sistemas, sello forense SHA-256, generación de `.docx`, Docker |
| Documentación | Auditoría del motor, contrato de la API, integración con un gestor de casos, 5 preguntas al despacho |

## 2. Comparación con la versión del repositorio

| | Repositorio (`main`) | Paquete de noviembre |
|---|---|---|
| Producto | Aplicación de escritorio completa, en uso | Cambios parciales; no se ejecuta solo |
| Motor de cálculo | Funciona; reglas confirmadas por el despacho | Más riguroso en precisión y reproducibilidad |
| Integración con otros sistemas | Ninguna (solo la UI) | API HTTP con contrato versionado |
| Reglas jurídicas | Confirmadas por escrito (p. ej. vacancia hasta el 11-ene) | Cambia algunas sin confirmación del despacho |
| Pruebas | ~1.640 | +~280 propias; 3 fallan en Windows |

Conclusión: no son versiones rivales. El paquete es una mejora para incorporar **por partes** sobre el
repositorio.

## 3. Criterio de integración

Decisión del usuario (2026-11-19):

1. Entra ya todo lo que **mejora sin cambiar ninguna cifra**.
2. Lo que **reemplaza un comportamiento** y cambia plazos o montos va como pregunta al despacho, con el porqué.
3. Las respuestas que generen dudas se vuelven a preguntar, explicando la contradicción.

## 4. Estado por fase

| Fase | Contenido | Estado | Dónde |
|---|---|---|---|
| 0. Diagnóstico | Suite completa con el paquete superpuesto: 1912 aprobadas, 3 fallidas | ✅ Hecho | `Pendientes.md`, Sprint 118 |
| 1. Precisión decimal | `decimal_config`, `Decimal` en PDF y línea de tiempo, `conftest` | ✅ Integrado | PR #18 |
| 2. Política de causación | Parámetro nuevo; el predeterminado es el comportamiento actual | ✅ Integrado (sin activar) | PR #18 |
| 2b. Guardia de migraciones | Prueba que exige registrar toda migración al arrancar | ✅ Integrado | PR #27 |
| 3. Capa API + Docker | `bastium_api`, `requirements-api.txt`, CI `ci-core` | ⏸ Decisión del equipo | Tarjeta #7 |
| 4. Calendario propio | Vacancia 10-ene, festivos a mano | 🔵 Bloqueado: despacho (preguntas 1, 2 y 6) | Tarjeta #8 |
| 5. Redondeo exacto por defecto | Cambia todas las liquidaciones | 🔵 Bloqueado: despacho (pregunta 3) | Tarjeta #9 |
| — | Tasa de `FamilyLawCalculator` | 🔵 Bloqueado: Sprint 76 | Tarjeta #10 |
| — | Pagos anticipados, notificación digital | 🔵 Bloqueado: despacho (preguntas 4 y 5) | Tarjetas #11 y #12 |

**Hallazgo clave de la fase 0:** el calendario propio del paquete **no incluye el festivo del Día de Nuestra
Señora del Rosario de Chiquinquirá** (13/07/2026, 12/07/2027), que la librería `holidays` sí trae. Con ese
calendario, todo plazo que cruce esa fecha vencería un día antes. Por eso el calendario no se integra sin
validación año por año.

### Estimación del trabajo restante

| Pendiente | Esfuerzo (una persona) | Depende de |
|---|---|---|
| Capa API (fase 3) | 2–3 días, más arreglar 2 pruebas en Windows | Decisión del equipo |
| Calendario (fase 4) | 2 días, más validación contra `holidays` 1984–2100 | Respuestas 1, 2 y 6 |
| Redondeo exacto (fase 5) | 2–3 días, más revisión de liquidaciones emitidas | Respuesta 3 |
| `Numeric` sobre SQLite guarda `float` (deuda señalada por la auditoría) | 2–3 días con migración | Nada; sprint propio |

## 5. Forma de trabajo: Kanban

Tablero: **[BASTIUM - Kanban](https://github.com/users/JoseMsD21/projects/1)** (GitHub Projects, privado).

| Columna | Significado | Límite WIP |
|---|---|---|
| Backlog | Ideas y pendientes sin priorizar | — |
| Listo | Priorizado, con criterio de "hecho" claro | 5 |
| En progreso | Alguien trabaja en ello, con su rama | 1–2 por persona |
| En revisión | PR abierta esperando aprobación | 3 |
| Bloqueado | Espera algo externo, normalmente el despacho | — |
| Hecho | Integrado a `main` con CI en verde | — |

Reglas:

- **Una tarjeta = un issue = una rama = un PR.** El PR menciona su issue (`Closes #N`).
- **Definición de "hecho":** CI en verde (ruff + pytest con cobertura ≥ 90 %), documentación actualizada
  (`Pendientes.md`, `CHANGELOG.md` y lo que aplique) y la aprobación de otra persona.
- **Respetar los límites WIP.** Si "En revisión" está llena, se revisa antes de empezar algo nuevo.
- **Bloqueado no es Backlog.** Toda tarjeta bloqueada dice qué espera y de quién.
- **Ritmo:** una revisión semanal corta para priorizar (Backlog → Listo) y repasar Bloqueado.
- `Pendientes.md` sigue siendo la historia técnica detallada; el tablero es la vista de qué se hace ahora.

## 6. Carpeta del equipo en Google Drive

Proyecto de Drive "BASTIUM" del equipo. Uso acordado:

- **Drive:** actas de reunión, avances semanales y el soporte formal de las respuestas del despacho.
- **Repositorio:** todo lo que el código necesita. Cuando el despacho responde, la respuesta se transcribe a
  `Preguntas-Para-Abogado-Respondidas.md` (o se mantiene en Abiertas con repregunta si genera dudas) con un
  enlace al acta de Drive.

Nombres sugeridos para las actas: `AAAA-MM-DD - Acta - <tema>` y `AAAA-MM-DD - Avance semanal`.

## 7. Próximos pasos

**Actualización 2026-11-19 (Sprint 119):** el despacho respondió el 16/11 las preguntas antiguas (Sprints 76 y 79
incluidos). Se implementaron los Sprints 76, 79, 95, 96, 70/91 y 110, y las preguntas quedaron ordenadas en
Respondidas y Abiertas. Ver `Pendientes.md`, Sprint 119.

1. Enviar al despacho lo que sigue abierto en `Preguntas-Para-Abogado-Abiertas.md`: las 6 preguntas del Sprint 118
   (paquete de noviembre), las 5 del Sprint 119, y las repreguntas de los Sprints 18, 79 (orden intereses vs.
   indexación) y 97/98 (tablas de mortalidad de inválidos).
2. Implementar los sprints desbloqueados (columna "Listo" del tablero): 84, 85, 86/87, 89, 94, 97/100, 104, 105,
   106, 107, y conectar a la pantalla Laboral lo de los Sprints 70/91 y 95.
3. Decidir en equipo si se integra la capa API (fase 3) y si se adopta NotebookLM (sección 8).
4. Programar como sprint propio la corrección de `Numeric` sobre SQLite (tarjeta #38).

## 8. Herramienta evaluada: NotebookLM como gestor de conocimiento (2026-11-19)

Propuesta del equipo: usar Google NotebookLM con `notebooklm-py` para que Claude Code consulte la base de
conocimiento del proyecto.

| Aspecto | Resultado |
|---|---|
| Qué es `notebooklm-py` | Librería **no oficial** (github.com/teng-lin/notebooklm-py, MIT, un solo mantenedor). Usa endpoints internos de la web de NotebookLM con las **cookies de la cuenta**; trae servidor MCP y skill para Claude Code. Su propio README la recomienda solo para prototipos. |
| API oficial | Solo en NotebookLM Enterprise (Google Cloud), en *preview*; permite gestionar cuadernos y fuentes, pero no documenta un endpoint para hacer preguntas. |
| Costo (3–5 personas) | Gratis con Gmail; ~US$5/persona/mes con Google AI Plus; ~US$14/persona/mes con Workspace Business Standard (cifra de terceros); Enterprise ~US$9/licencia con mínimo de 15 (sin precio oficial confirmado). |
| Límites | Gratis: 100 cuadernos y 50 fuentes por cuaderno; Plus: 200/100; Pro: 500/300 (página oficial de ayuda, sujetos a cambios). |
| Escalabilidad | Los límites alcanzan por bastante tiempo. El cuello de botella es **mantener las fuentes sincronizadas**: los Docs de Drive se actualizan solos, pero PDFs y archivos subidos no, y los `.md` del repositorio nunca. |
| Riesgos | Posible incumplimiento de los términos de Google y roturas sin aviso (endpoints no oficiales); exposición de credenciales completas de la cuenta; documentos jurídicos en cuentas personales (con Workspace no hay revisión humana ni entrenamiento). |

**Recomendación:** no conectar `notebooklm-py` ni MCP no oficiales a cuentas con documentos reales. La base de
conocimiento principal para Claude Code son los `.md` del repositorio (siempre al día, sin costo) más el conector
de Google Drive para actas. NotebookLM puede usarse **manualmente desde la web, con cuentas Workspace**, como
herramienta de consulta para el abogado y quienes no programan, alimentado con Google Docs de Drive. Si se quiere
probar la integración, que sea con una cuenta dedicada y solo documentos no sensibles. Decisión pendiente del
equipo (tarjeta en Backlog).
