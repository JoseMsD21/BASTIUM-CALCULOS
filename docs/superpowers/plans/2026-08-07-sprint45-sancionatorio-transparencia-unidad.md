# Sprint 45 — Sancionatorio: transparencia de la unidad SMLMV/UVT y aclaración del caso de capital creciente Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Alcance de este plan: SOLO el punto 1 (transparencia de unidad).** El punto 2 (queja de "capital
creciendo exponencialmente") **no se codifica** — se revisó toda la cadena de cálculo
(`SancionatorioStrategy.liquidar()`, `LiquidationCore`, `BalanceEngine`, `DailyInterest`) sin lograr
reproducir el bug; el propio sprint dice explícitamente "no se codifica ningún fix hasta reproducir el caso
con datos reales — evitar 'arreglar' algo que no está roto en el código revisado". El punto 2 queda
documentado como pendiente en `Pendientes.md`, a la espera de que el usuario aporte el expediente o captura
de pantalla exacta donde vio el problema.

**Goal:** El formulario de Sancionatorio muestra explícitamente, junto al campo `cantidad_smlmv_uvt`, qué
unidad (SMLMV o UVT) se va a aplicar según la fecha capturada, sin cambiar el modelo de datos — la regla de
negocio ya es correcta (`app/engine/indexation/smlmv_to_uvt.py:8`, corte 2020-01-01 según Ley 1955/2019 art.
49), solo falta mostrarla.

**Architecture:** Un texto/indicador dinámico (`QLabel`, ej. "Se aplicará como: UVT" / "Se aplicará como:
SMLMV") junto al campo `campo_cantidad_smlmv_uvt` en `ObligacionFormDialog`
(`app/views/obligaciones.py`), actualizado cada vez que cambia `campo_fecha_origen` (conectar la señal
`dateChanged` si no está ya conectada a un método de actualización de visibilidad existente) — reutilizar
la misma función que ya decide la unidad en `app/engine/indexation/smlmv_to_uvt.py` en vez de duplicar la
fecha de corte 2020-01-01 en la UI.

**Tech Stack:** Python 3.14, PySide6 6.11, pytest + pytest-qt.

---

### Task 1: Indicador de unidad SMLMV/UVT

- [ ] `QLabel` dinámico junto a `campo_cantidad_smlmv_uvt` que muestra la unidad que se aplicará según
      `campo_fecha_origen`, reutilizando la función de decisión ya existente en `smlmv_to_uvt.py`.
- [ ] Se actualiza en vivo cuando el usuario cambia la fecha de origen, sin necesidad de guardar el
      formulario.
- [ ] Test de GUI: cambiar `campo_fecha_origen` a una fecha antes y después de 2020-01-01 y confirmar que el
      indicador muestra SMLMV/UVT correctamente en cada caso.

### Task 2: Verificación final

- [ ] Suite completa de tests (`pytest`) en verde.
- [ ] No se toca ningún archivo de `app/engine/` ni `app/services/area_strategy.py` relacionado con
      Sancionatorio en este sprint (el punto 2 queda fuera de alcance, solo UI).
