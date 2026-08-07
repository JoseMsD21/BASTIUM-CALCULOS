# Sprint 38 — Elegir licencia de código abierto y publicar `LICENSE` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Decisión ya tomada por el usuario (2026-08-06):** Apache License 2.0. No hay ninguna decisión de diseño
pendiente en este plan — es trabajo puramente documental, sin tests de código nuevos.

**Goal:** Publicar el archivo `LICENSE` en la raíz con el texto completo de la Apache License 2.0
(reemplazando `[yyyy]`/`[name of copyright owner]` del boilerplate estándar por el año 2026 y el titular de
derechos que corresponda — usar "BASTIUM" o el nombre del autor si se puede inferir de `pyproject.toml`/
`README.md`; si no es inferible sin ambigüedad, usar un placeholder razonable y dejarlo anotado en el commit
para que el usuario lo confirme, sin bloquear el resto del sprint por esto). Actualizar el badge de
licencia en `README.md` (línea 5 actual: `![Licencia](https://img.shields.io/badge/licencia-por%20definir%20
(Sprint%2038)-lightgrey)`) para que apunte a Apache 2.0. Agregar la línea correspondiente en
`CONTRIBUTING.md` (línea ~90-91 actual, que hoy dice "La licencia definitiva todavía está pendiente de
elegir") confirmando que las contribuciones se licencian bajo Apache 2.0.

**Architecture:** No aplica (sin código). Usar el texto oficial completo de Apache License 2.0 (no un
resumen ni un enlace) en `LICENSE`, tal como GitHub lo reconoce automáticamente en la sección "About" del
repo cuando el archivo se llama exactamente `LICENSE` (sin extensión) en la raíz.

**Tech Stack:** Markdown/texto plano. Sin dependencias.

---

### Task 1: Archivo LICENSE

- [ ] Crear `LICENSE` en la raíz del repo con el texto completo y oficial de la Apache License 2.0 2004,
      incluyendo el apéndice "How to apply the Apache License to your work" completado con el año 2026 y
      el titular de copyright.

### Task 2: Badge de licencia en README.md

- [ ] Reemplazar el badge actual (`licencia-por%20definir...`) por uno que indique Apache 2.0 (ej.
      `![Licencia](https://img.shields.io/badge/licencia-Apache%202.0-blue)`) enlazado al archivo
      `LICENSE`.

### Task 3: Línea de licencia en CONTRIBUTING.md

- [ ] Reemplazar la frase "La licencia definitiva todavía está pendiente de elegir" por una confirmación de
      que las contribuciones se licencian bajo Apache 2.0, enlazando al archivo `LICENSE`.

### Task 4: Verificación final

- [ ] Confirmar que no queda ninguna referencia a "Sprint 38" o "por definir" respecto a la licencia en
      `README.md`/`CONTRIBUTING.md`.
- [ ] Suite completa de tests (`pytest`) en verde (no debería haber cambiado nada de código, pero confirmar
      igual que no se rompió nada).
