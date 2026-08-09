# Sprint 48 — Limpiar la deuda de `ruff` preexistente y agregar el chequeo de lint al pipeline de CI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Nota operativa de orquestación:** este sprint se ejecuta en su propio worktree igual que los demás, pero
**se revisa y mezcla a `main` al final**, después de que el resto de sprints de esta tanda ya estén
integrados — es un barrido que toca líneas dispersas por casi todo el repo (line-length, orden de imports),
así que mezclarlo primero o en paralelo real generaría conflictos de merge innecesarios contra archivos que
otros sprints también tocan. El agente debe implementar y commitear normalmente en su worktree; el momento
del merge lo decide el orquestador, no cambia nada de cómo se trabaja aquí.

**Estado real verificado (2026-08-09, `ruff check . --statistics`):** 447 errores, no ~400 como decía el
hallazgo original (el número subió por los Sprints 36-45 recientes, cada uno confirmó no agregar errores
*nuevos* pero el conteo total incluye código agregado que sí tenía deuda preexistente de estilo en archivos
que ya la tenían). Desglose real:

```
411  E501  line-too-long
 13  E402  module-import-not-at-top-of-file
  6  B905  zip-without-explicit-strict
  4  B011  assert-false
  4  UP042 replace-str-enum
  3  I001  unsorted-imports
  2  B904  raise-without-from-inside-except
  2  E741  ambiguous-variable-name
  1  B008  function-call-in-default-argument
  1  F841  unused-variable
```

**Goal:** `ruff check .` sobre el repo completo devuelve cero errores, y el workflow de CI
(`.github/workflows/ci.yml`, Sprint 28) incluye `ruff check .` como paso obligatorio.

**Architecture:** No cambiar reglas de `ruff` ni relajar `pyproject.toml` para que la deuda "desaparezca"
sin limpiarla (alcance explícitamente excluido). Limpiar por categoría, de más mecánico a más riesgoso:
1. `I001` (3, auto-fixable con `ruff check --fix`) y las 15 "hidden fixes" de `--unsafe-fixes` — revisar cada
   una individualmente antes de aplicar `--unsafe-fixes` (no aplicar en bloque sin revisar el diff).
2. `E501` (411, la gran mayoría) — reformatear manualmente cada línea larga (envolver strings, dividir
   llamadas), sin cambiar comportamiento. Alto volumen pero mecánico.
3. `E402` (13) — reordenar imports al tope del archivo; verificar caso por caso que no haya una razón
   intencional (ej. un import condicional tardío) antes de mover — si la hay, usar
   `# noqa: E402` con un comentario que explique por qué, no mover ciegamente.
4. `B905`, `B011`, `UP042`, `B904`, `E741`, `B008`, `F841` (23 combinados) — cada uno es una regla de
   comportamiento, no solo estilo (ej. `B904` es sobre manejo de excepciones, `F841` variable sin usar) —
   revisar cada ocurrencia individualmente, no aplicar un fix automático en bloque sin leer el contexto.

**Tech Stack:** `ruff` (ya configurado en `pyproject.toml`), GitHub Actions (`.github/workflows/ci.yml`).

---

### Contexto compartido entre tareas

- Correr `ruff check . --statistics` al empezar para confirmar el conteo real en el momento de arrancar
  (puede haber cambiado desde el número de arriba si el worktree parte de un commit distinto).
- La limpieza NO debe cambiar comportamiento — la suite completa de tests debe seguir en verde exactamente
  igual antes y después.
- Priorizar corregir de verdad sobre suprimir con `# noqa` — usar `# noqa` solo cuando el caso realmente lo
  amerite (ej. un import tardío intencional), con comentario explicando por qué, no como atajo para bajar el
  conteo.

### Task 1: Limpieza automática segura (I001 + revisión de unsafe-fixes)

- [ ] `ruff check --fix .` para los 3 `I001` (orden de imports, fixable seguro).
- [ ] Revisar una por una las 15 "hidden fixes" de `--unsafe-fixes` (`ruff check --unsafe-fixes --diff .`
      para ver el diff sin aplicar primero) — aplicar solo las que no cambian comportamiento.
- [ ] Suite completa en verde tras este paso.

### Task 2: E501 (line-too-long, 411 casos)

- [ ] Reformatear archivo por archivo (o por directorio, lo que sea más manejable) hasta que `ruff check .`
      no reporte más `E501`.
- [ ] Suite completa en verde tras este paso (commit intermedio recomendado, es el grueso del trabajo).

### Task 3: E402 (module-import-not-at-top-of-file, 13 casos)

- [ ] Revisar cada caso; mover el import al tope si no hay razón intencional, o dejar `# noqa: E402` con
      comentario si la hay.
- [ ] Suite completa en verde.

### Task 4: Reglas de comportamiento (B905, B011, UP042, B904, E741, B008, F841 — 23 casos combinados)

- [ ] Revisar y corregir cada ocurrencia individualmente, leyendo el contexto (estas reglas señalan
      problemas reales de código, no solo estilo — ej. `F841` variable nunca usada podría indicar un bug).
- [ ] Suite completa en verde.

### Task 5: CI

- [ ] Agregar `ruff check .` como paso obligatorio en `.github/workflows/ci.yml` (Sprint 28), después del
      paso de `pytest` o antes, decidir según convención del archivo actual.
- [ ] Confirmar `ruff check .` sobre el repo completo devuelve cero errores.

### Task 6: Verificación final

- [ ] `ruff check .` → 0 errores.
- [ ] Suite completa de tests (`pytest`) en verde, mismo conteo de tests que antes de empezar (la limpieza
      no debe agregar ni quitar ningún test).
