# Sprint 29 (refresco) — Auditoría de drift de documentación Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sprint 29 original (cerrado 2026-07-26) corrigió 7 hallazgos de documentación desactualizada.
Desde entonces cerraron ~12 sprints más (17-28) y se agregaron los Sprints 30-46 al backlog. Este plan
re-corre la misma metodología de auditoría (enlaces `specifications/`, numeración de `docs/GUIA_USUARIO.md`,
conteo de tests, 7 specs técnicos, marcadores 🚧 obsoletos, acrónimo EFDJ/jargon nuevo, TOC de
`Pendientes.md`) contra el estado *actual* del repo y corrige el drift real encontrado.

**Architecture:** Es una auditoría de documentación, no una feature de código — no hay TDD rojo/verde.
Cada tarea es "correr el check N contra el estado real del repo, y si hay drift, corregirlo" sobre
`README.md`, `docs/GUIA_USUARIO.md` y los 7 archivos de `docs/specifications/*.md`. `Pendientes.md` se
puede corregir por contenido roto (rutas, enlaces) pero **nunca** sus marcadores de estado/TOC — eso lo
hace el orquestador humano de forma centralizada tras fusionar 5 sprints paralelos.

**Tech Stack:** Markdown puro. Verificación con `grep`/lectura manual y `pytest` (venv compartido del repo
principal, no hay venv propio en este worktree).

**Investigación previa (ya hecha, resumen para los subagentes):**
- Check 1 (`specifications/` sin prefijo `docs/`): **sin drift**. La única aparición sin prefijo es
  `README.md:121`, dentro de un diagrama de árbol de directorios (`docs/` ya es el padre visual en el
  árbol) — no es un enlace roto, es una entrada de árbol de carpetas correcta.
- Check 2 (numeración duplicada / cross-refs rotos en `docs/GUIA_USUARIO.md`): **sin drift**. `### `
  headers van 2.1-2.6, 5.1-5.15, 7.1-7.8 (con 7.1.1 y 7.6.1), todos secuenciales sin duplicados. Todas las
  referencias `"sección X.Y"` (`grep -noE "sección [0-9]+(\.[0-9]+)?(\.[0-9]+)?"`) apuntan a secciones que
  existen.
- Check 3 (conteo de tests, sección 2.6): **drift encontrado**. La guía dice `489 passed, 1 skipped`;
  `pytest -q` real hoy da `687 passed, 1 skipped`. La frase de la nota ("El número exacto sube con cada
  sprint nuevo, así que no te preocupes si no coincide exactamente") sigue siendo válida y debe
  conservarse, pero el número de referencia debe actualizarse — 489 vs. 687 es una brecha de ~40%, no un
  desfase menor de "un par de sprints".
- Check 4 (specs técnicos desactualizados): **drift encontrado en 3 de 7**:
  - `docs/specifications/01_motor_temporal.md`: sección "Pendiente (no implementado aun)" lista "Modulo
    pensional (IBL, tasa de reemplazo, densidad de semanas) — ver Pendientes.md, Sprint 17" como si no
    existiera. El Sprint 17 (cerrado 2026-07-26, con corrección urgente 2026-08-01) sí implementó
    `app/engine/labor/ibl.py` (`calcular_ibl`, `calcular_tasa_reemplazo`, `calcular_densidad_semanas`,
    `semanas_minimas_requeridas`) como funciones puras probadas — standalone, sin `PensionalStrategy` ni
    wiring de GUI todavía (mismo patrón que `app/engine/tax/*` del Sprint 11a, ya documentado así en
    `02_motor_financiero.md`).
  - `docs/specifications/02_motor_financiero.md`: sección "Pendiente (no implementado aun)" lista (a)
    "Anatocismo comercial condicionado... ver Sprint 19" y (b) "Multiples tasas de interes simultaneas...
    ver Sprint 21" como no implementados. Ambos sprints están `✅ Completado`: Sprint 19 (2026-07-26) agregó
    el evento `CAPITALIZACION_INTERESES_ANATOCISMO` en `LiquidationCore`/`BalanceEngine`, cableado en
    `ComercialStrategy`; Sprint 21 (2026-07-31) hizo que cada obligación corra su propio `LiquidationCore`
    (`_liquidar_por_obligacion`) para soportar tasas distintas simultáneas por expediente.
  - `docs/specifications/07_motor_juridico_familia.md`: mismo hallazgo de pensional que en `01` (línea 41,
    idéntica redacción).
  - Los otros 4 (`03_motor_indexacion.md`, `04_motor_pagos.md`, `05_motor_auditoria.md`,
    `06_motor_reportes.md`) se leyeron completos: **sin drift** — sus listas de "Pendiente" citan sprints
    que siguen genuinamente sin cerrar (Sprint 25/26 en `06`, imputación alternativa/pago anómalo en `04`,
    sin sprint asociado aún), y el resto del contenido coincide con el código actual.
- Check 5 (🚧 obsoletos en README/GUIA): **drift encontrado en 1 lugar**. `docs/GUIA_USUARIO.md` sección 8
  (línea ~921) marca "🚧 Anatocismo comercial condicionado (Art. 886 C.Co.)" como pendiente ("el motor de
  interés compuesto existe pero no está conectado"), pero el Sprint 19 ya lo conectó (ver check 4). Las
  otras dos entradas 🚧 de esa misma sección ("Prescripción y caducidad", "Calendario de días hábiles y
  términos procesales") siguen siendo ciertas — el Sprint 42 (que conectaría prescripción/caducidad al
  flujo real) sigue sin cerrar, y no existe ningún sprint que conecte el calendario a una pantalla.
  `README.md` no tiene drift: su párrafo "🚧 En desarrollo" (línea 64) solo menciona prescripción/caducidad
  (correcto, sigue sin conectar) y el bloque "Comercial" del párrafo "✅ Funcional hoy" ya describe el
  anatocismo condicionado como implementado.
- Check 6 (EFDJ + jargon nuevo): **sin drift**. "EFDJ" sigue definido la primera vez que aparece en
  `Pendientes.md` (línea ~24-27, sin cambios desde el cierre original). Se revisaron los Sprints 30-46
  agregados después del cierre original buscando acrónimos/jerga nueva sin explicar (SL138-2024, RAIS,
  FSP, IBL, QFormLayout, etc.) — todos se explican inline en el propio texto donde aparecen por primera
  vez, ninguno necesita glosario aparte.
- Check 7 (TOC de `Pendientes.md`): **stale, pero NO se edita aquí** (guardrail del orquestador). Todos los
  45 sprints (2-46) tienen entrada en el índice en el orden correcto, y los anchors (`#sprint-N--...`)
  apuntan correctamente incluso cuando el texto visible del enlace es una versión acortada del título real
  (Sprints 43 y 45: el anchor coincide con el título completo, el texto visible es solo más corto —
  cosmético, no roto). El hallazgo real: la entrada de TOC del Sprint 23 (línea 124) no tiene el sufijo
  "✅ Completado" que el encabezado real (línea 2010) sí tiene — desincronización simple de que el TOC no
  se tocó cuando el Sprint 23 cerró. Se reporta al orquestador para su pase de consolidación central, no se
  toca en este plan.

---

### Task 1: Corregir sección 2.6 de `docs/GUIA_USUARIO.md` (conteo de tests) y la fecha de "Última actualización"

**Files:**
- Modify: `docs/GUIA_USUARIO.md:8` (banner "Última actualización")
- Modify: `docs/GUIA_USUARIO.md:107-116` (sección 2.6)

- [ ] **Step 1: Confirmar el conteo real de tests**

Run (usar el Python del venv compartido del repo principal, este worktree no tiene venv propio):
```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q
```
Expected: termina en `N passed, 1 skipped` (al momento de escribir este plan, `N=687`; si al ejecutar este
paso el número es distinto porque se fusionó trabajo nuevo en el worktree, usar el número real que arroje
el comando, no el 687 de este plan).

- [ ] **Step 2: Actualizar el número en la sección 2.6**

En `docs/GUIA_USUARIO.md`, la sección `### 2.6. Verificar que todo quedó instalado correctamente...`
contiene actualmente:

```
Este comando corre todas las pruebas automáticas del programa. Si al final ves algo como
`489 passed, 1 skipped` (un número seguido de "passed", sin ningún "failed"), significa que todo está
instalado y funcionando correctamente. El número exacto sube con cada sprint nuevo, así que no te
preocupes si no coincide exactamente — lo que importa es que no aparezca ningún "failed". Si ves errores,
revisa la [sección 9](#9-preguntas-frecuentes-y-solución-de-problemas).
```

Cambiar `489 passed, 1 skipped` por el número real obtenido en el Step 1 (ej. `687 passed, 1 skipped`),
dejando el resto de la frase (incluida la advertencia de que el número sube con cada sprint) intacta.

- [ ] **Step 3: Actualizar el banner de "Última actualización"**

En `docs/GUIA_USUARIO.md:8`, cambiar:

```
> **Última actualización:** 2026-07-27 — refleja el estado de Civil/Familia, Comercial, Sancionatorio,
```

por la fecha real de esta edición (usar la fecha de hoy del entorno, ej. `2026-08-03`), manteniendo el
resto de la frase igual — el contenido que describe (áreas operables, exportación, parámetros) sigue
siendo correcto, solo la fecha estaba desactualizada.

- [ ] **Step 4: Commit**

```bash
git add docs/GUIA_USUARIO.md
git commit -m "$(cat <<'EOF'
docs(sprint29): actualizar conteo de tests y fecha de la guia de usuario

EOF
)"
```

---

### Task 2: Corregir el marcador 🚧 obsoleto de "Anatocismo comercial" en `docs/GUIA_USUARIO.md` sección 8

**Files:**
- Modify: `docs/GUIA_USUARIO.md:921-924`

- [ ] **Step 1: Localizar el bloque actual**

En `docs/GUIA_USUARIO.md`, sección `## 8. Funciones pendientes o en desarrollo`, el bloque es:

```
- 🚧 **Anatocismo comercial condicionado (Art. 886 C.Co.)** — el motor de interés compuesto
  (`CompoundInterest`) existe pero no está conectado; requiere modelar si hubo demanda judicial o
  acuerdo posterior de capitalización, algo que el modelo de datos todavía no captura (`Pendientes.md`,
  Sprint 2, nota de alcance diferido).
```

- [ ] **Step 2: Reemplazar por el bloque actualizado**

Cambiar el bloque de arriba por (mismo formato `✅` que las demás entradas ya implementadas de esa
sección, referenciando el cierre real del Sprint 19):

```
- ✅ **Anatocismo comercial condicionado (Art. 886 C.Co.)** — el área Comercial ya aplica interés sobre
  interés cuando se cumplen las dos condiciones legales (demanda judicial y/o acuerdo posterior de
  capitalización, con al menos un año de intereses vencidos), capitalizando periódicamente cada
  aniversario desde la fecha de capitalización; el resto de la liquidación sigue en interés simple
  (`Pendientes.md`, Sprint 19). Ver [sección 5.7](#57-agregar-una-obligación-comercial).
```

(Nota: verificar antes de guardar que la sección 5.7 realmente documenta los campos de anatocismo en el
formulario Comercial; si no los documenta explícitamente, quitar la referencia de sección del enlace y
dejar solo el texto sin el link, para no introducir un enlace que no aporte información nueva.)

- [ ] **Step 3: Commit**

```bash
git add docs/GUIA_USUARIO.md
git commit -m "$(cat <<'EOF'
docs(sprint29): marcar anatocismo comercial como implementado en la guia de usuario

EOF
)"
```

---

### Task 3: Corregir `docs/specifications/01_motor_temporal.md` (módulo pensional ya implementado)

**Files:**
- Modify: `docs/specifications/01_motor_temporal.md:38-43`

- [ ] **Step 1: Localizar el bloque "Pendiente" actual**

```
## Pendiente (no implementado aun)
- Modulo pensional (IBL, tasa de reemplazo, densidad de semanas) — ver `Pendientes.md`, Sprint 17.
- `EstadoTermino`/`terminos.py` todavia no esta conectado a ninguna pantalla de la GUI — hoy sirve como base
  interna para el motor de prescripcion y caducidad.

Ver `Pendientes.md` para el orden de implementacion.
```

- [ ] **Step 2: Mover el módulo pensional a "Componentes" (implementado, sin GUI) y dejar solo lo
  genuinamente pendiente en "Pendiente"**

Agregar una línea nueva al final de la sección `## Componentes` (después de la línea de
`app/engine/temporal/prescripcion.py`):

```
- `app/engine/labor/ibl.py`: `calcular_ibl`, `calcular_tasa_reemplazo`, `calcular_densidad_semanas` y
  `semanas_minimas_requeridas` — modulo pensional (IBL, tasa de reemplazo, densidad de semanas
  post-SL138-2024) implementado como funciones puras probadas (Sprint 17), standalone: sin
  `PensionalStrategy` ni wiring a ninguna pantalla todavia (mismo patron que `app/engine/tax/*`).
```

Y cambiar el bloque "Pendiente" a:

```
## Pendiente (no implementado aun)
- Wiring del modulo pensional (`app/engine/labor/ibl.py`) a una `PensionalStrategy`/pantalla de GUI —
  hoy solo es invocable como funciones puras (`Pendientes.md`, Sprint 17, nota de alcance).
- `EstadoTermino`/`terminos.py` todavia no esta conectado a ninguna pantalla de la GUI — hoy sirve como base
  interna para el motor de prescripcion y caducidad.

Ver `Pendientes.md` para el orden de implementacion.
```

- [ ] **Step 3: Commit**

```bash
git add docs/specifications/01_motor_temporal.md
git commit -m "$(cat <<'EOF'
docs(sprint29): reflejar que el modulo pensional del Sprint 17 ya esta implementado

EOF
)"
```

---

### Task 4: Corregir `docs/specifications/02_motor_financiero.md` (anatocismo y múltiples tasas ya implementados)

**Files:**
- Modify: `docs/specifications/02_motor_financiero.md:40-46`

- [ ] **Step 1: Localizar el bloque "Pendiente" actual**

```
## Pendiente (no implementado aun)
- Anatocismo comercial condicionado (Art. 886 C.Co.) — el motor actual no aplica interes sobre interes en
  ningun caso (comportamiento correcto para Civil, pero el area Comercial lo necesitara bajo condiciones) —
  ver `Pendientes.md`, Sprint 19.
- Multiples tasas de interes simultaneas por expediente — ver `Pendientes.md`, Sprint 21.

Ver `Pendientes.md`.
```

- [ ] **Step 2: Mover ambos ítems a "Componentes" y vaciar (o reducir) "Pendiente"**

Agregar al final de la sección `## Componentes` (después de la línea de
`app/engine/liquidation/engine.py: LiquidationCore`):

```
- Anatocismo comercial condicionado (Art. 886 C.Co., Sprint 19): `LiquidationCore`/`BalanceEngine` ganaron
  el evento `CAPITALIZACION_INTERESES_ANATOCISMO`, que traslada el interes simple ya devengado al capital
  en cada aniversario desde la fecha de capitalizacion (en vez de usar `CompoundInterest.calculate()`,
  que sigue huerfano). `ComercialStrategy` lo activa solo si hay demanda judicial y/o acuerdo posterior de
  capitalizacion con al menos un año de intereses vencidos; el resto de la liquidacion sigue en interes
  simple.
- Multiples tasas de interes simultaneas por expediente (Sprint 21): cada `Obligacion` corre su propio
  `LiquidationCore` independiente (`_liquidar_por_obligacion` en `app/services/area_strategy.py`), con su
  propia tasa y solo sus propios abonos, y los historiales se fusionan en una sola linea de tiempo
  consolidada. Aplica a `CivilFamiliaStrategy`, `ComercialStrategy`, `SancionatorioStrategy`,
  `HonorariosStrategy` (no a `LaboralStrategy`/`TributarioStrategy`, que no tienen tasa por obligacion).
```

Y cambiar el bloque `## Pendiente` a:

```
## Pendiente (no implementado aun)
- `CompoundInterest.calculate()` (`app/engine/interest/compound_interest.py`) sigue huerfano: el
  anatocismo comercial (arriba) se resolvio con eventos de capitalizacion periodica en vez de esta
  formula cerrada de una sola pasada.

Ver `Pendientes.md`.
```

- [ ] **Step 3: Commit**

```bash
git add docs/specifications/02_motor_financiero.md
git commit -m "$(cat <<'EOF'
docs(sprint29): reflejar que anatocismo comercial y multiples tasas ya estan implementados

EOF
)"
```

---

### Task 5: Corregir `docs/specifications/07_motor_juridico_familia.md` (módulo pensional ya implementado)

**Files:**
- Modify: `docs/specifications/07_motor_juridico_familia.md:40-43`

- [ ] **Step 1: Localizar el bloque "Pendiente" actual**

```
## Pendiente (no implementado aun)
- Modulo pensional (IBL, tasa de reemplazo, densidad de semanas) — ver `Pendientes.md`, Sprint 17.
- Costas judiciales con tabla real de rangos (hoy se ingresan como porcentaje manual en Honorarios) — ver
  `Pendientes.md`, Sprint 18.
```

- [ ] **Step 2: Reemplazar solo la línea de pensional (la de costas judiciales sigue vigente — Sprint 18
  está `⚠️ Parcial`, no se toca)**

Cambiar:

```
- Modulo pensional (IBL, tasa de reemplazo, densidad de semanas) — ver `Pendientes.md`, Sprint 17.
```

por:

```
- Wiring del modulo pensional (`app/engine/labor/ibl.py`, implementado como funciones puras standalone
  desde el Sprint 17: `calcular_ibl`, `calcular_tasa_reemplazo`, `calcular_densidad_semanas`,
  `semanas_minimas_requeridas`) a una `PensionalStrategy`/pantalla de GUI — hoy no es una de las 6 areas
  operables listadas arriba.
```

- [ ] **Step 3: Commit**

```bash
git add docs/specifications/07_motor_juridico_familia.md
git commit -m "$(cat <<'EOF'
docs(sprint29): reflejar que el modulo pensional del Sprint 17 ya esta implementado (spec familia)

EOF
)"
```

---

### Task 6: Verificación final — checks sin drift, suite completa y reporte de TOC

**Files:** ninguno (solo verificación, sin cambios)

- [ ] **Step 1: Re-confirmar checks 1, 2 y 6 (ya verificados sin drift antes de escribir este plan, pero
  se re-corren después de las Tasks 1-5 por si alguna edición introdujo una regresión)**

Run:
```bash
grep -rn "specifications/" README.md docs/GUIA_USUARIO.md Pendientes.md
```
Expected: todas las apariciones tienen el prefijo `docs/`, excepto `README.md:121` (entrada de árbol de
directorios, no un enlace).

Run:
```bash
grep -n "^### " docs/GUIA_USUARIO.md
```
Expected: sin números duplicados (2.1-2.6, 5.1-5.15, 7.1/7.1.1/7.2-7.8/7.6.1).

Run:
```bash
grep -n "EFDJ" Pendientes.md | head -5
```
Expected: la primera aparición (línea ~24-27) sigue trayendo la definición completa ("Especificación
Funcional del Dominio Jurídico").

- [ ] **Step 2: Correr la suite completa del proyecto**

Run:
```bash
"C:/Users/USER/OneDrive/Documents/CODIGO-PORTAFOLIO-PAGINAS-APP-CREACIONES/BASTIUM CALCULOS/.venv/Scripts/python.exe" -m pytest -q
```
Expected: mismo resultado que en la Task 1 (este sprint es documentación pura, no debe cambiar ningún
resultado de test).

- [ ] **Step 3: No hay commit en este task** — es solo verificación. El hallazgo de la Task 7 original
  (TOC de `Pendientes.md` desincronizado: la entrada del Sprint 23 en el índice no tiene el sufijo
  "✅ Completado" que sí tiene su encabezado real) se reporta en el resumen final al orquestador, **no se
  edita** (guardrail: el TOC y los marcadores de estado de `Pendientes.md` los corrige el orquestador de
  forma centralizada).

---

## Self-review notes

- **Cobertura de los 7 checks del encargo:** Task 1 cubre check 3 (conteo de tests); Task 2 cubre check 5
  (🚧 obsoleto); Tasks 3-5 cubren check 4 (specs desactualizados: 01, 02, 07); Task 6 reconfirma checks 1,
  2 y 6 (sin drift, se documentan como tal) y deja check 7 (TOC) como hallazgo reportado sin editar, tal
  como exige el guardrail del encargo.
- **Sin placeholders:** cada paso trae el texto exacto a pegar (antes/después), no descripciones genéricas.
- **No se toca `Pendientes.md`:** ninguna task de este plan modifica `Pendientes.md` — todo el drift
  encontrado vive en `docs/GUIA_USUARIO.md` y `docs/specifications/*.md`. Si алgún subagente encontrara
  contenido roto dentro de `Pendientes.md` al ejecutar Task 6 que no estuviera ya cubierto por el
  guardrail, debe reportarlo en vez de editarlo y seguir con el resto del plan.
- **Fecha de "hoy" usada en Task 1:** el paso 3 pide usar la fecha real del entorno al momento de editar,
  no un valor fijo — el subagente que ejecute Task 1 debe tomarla del entorno (`currentDate` del sistema)
  en vez de asumir la fecha de escritura de este plan.
- **Alcance:** no se tocan `requirements.txt`, `app/`, CI/CD, ni ningún archivo fuera de
  `docs/GUIA_USUARIO.md` y `docs/specifications/*.md`.
