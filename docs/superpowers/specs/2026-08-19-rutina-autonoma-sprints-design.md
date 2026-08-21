# Rutina autónoma para trabajar sprints de `Pendientes.md`

**Fecha:** 2026-08-19
**Estado:** Aprobado por el usuario, pendiente de configurar la rutina (`CronCreate`/`schedule`).

## Contexto y problema

El usuario no siempre tiene tiempo de sentarse a trabajar con Claude Code en BASTIUM, pero
`docs/Pendientes.md` ya tiene un backlog grande de sprints autocontenidos, la mayoría sin
depender de ninguna decisión externa para arrancar. El objetivo es que una rutina programada
trabaje esos sprints sin supervisión, avisando al usuario solo cuando aparece una decisión que
de verdad requiere su criterio (o del despacho), y sin interrumpirlo por decisiones operativas
(aprobar comandos, commits, etc.).

## Estados de sprint en `Pendientes.md`

Se agregan 2 estados nuevos a los 5 ya existentes (ver líneas 18-32 del archivo). El estado va
siempre pegado al título del sprint, nunca como marca separada dentro del cuerpo — igual que los
5 estados actuales:

```
## Sprint N — Nombre del sprint 🟡 En proceso
## Sprint N — Nombre del sprint 🟠 Reabierto
```

- **🟡 En proceso** — una corrida automática lo empezó (tiene worktree/rama propia) y no llegó a
  cerrarlo en esa ventana. La nota del sprint incluye el nombre de la rama.
- **🟠 Reabierto** — cubre dos casos con el mismo estado: (a) un 🔵 Bloqueado que el usuario ya
  respondió, o (b) un ✅ Completado donde apareció un bug/observación nueva después del cierre
  (mismo patrón que ya usó el Sprint 76 para hallazgos post-cierre).

### Orden de prioridad de la cola

1. 🟡 En proceso — nunca se abandona a medias por arrancar algo nuevo; se retoma la misma rama.
2. 🟠 Reabierto — una decisión ya contestada no debe esperar detrás de todo el backlog nuevo.
3. 🔴 Bug confirmado sin corregir — máxima prioridad de dominio si aparece uno nuevo.
4. 📋 Pendiente — por orden de número de sprint.

⚠️ Parcial y 🔵 Bloqueado nunca se toman directamente; ⚠️ Parcial solo se retoma cuando el sprint
al que se difirió su resto (que sí será 📋/🟠) lo trae de vuelta, y 🔵 Bloqueado solo se mueve
cuando el usuario o el despacho contestan (pasa entonces a 🟠 Reabierto).

## Disparo y cadencia

- Primer arranque: 2026-08-19 15:30 (reset de la ventana de 5h del usuario).
- Cadencia: cada 5h desde ese primer arranque (máxima frecuencia posible dentro de la ventana de
  uso).
- Reset semanal: viernes 10:00am. La cadencia máxima (cada 5h, 24/7) ya apunta a agotar el cupo
  semanal antes del jueves en la noche, sin necesidad de un mecanismo adicional — la única forma
  de dejar cupo sin usar sería que el backlog de sprints 📋/🟠 se agote antes que el cupo, lo cual
  se resuelve manteniendo el backlog alimentado, no con más lógica de scheduling.
- Guardia contra solapamiento (reforzada 2026-08-20 tras un caso real de 2 corridas tomando el
  mismo sprint — Sprint 102, 11:28 y 11:32 UTC): `git fetch origin` + `git log --all --since="20
  minutes ago"` sobre **todas** las ramas, no solo la del sprint elegido, antes de arrancar y de
  nuevo justo después de crear la rama y antes de escribir código. Si el `git push` final es
  rechazado por no-fast-forward, no se fuerza nada: se verifica si `origin/main` ya tiene un
  cierre equivalente y, si es así, se descarta la rama local sin generar bloqueo ni correo (es
  trabajo duplicado detectado a tiempo, no un fallo).

## Mecánica dentro de una ventana

- La condición para seguir encadenando sprints es **cupo de tokens restante**, no tiempo de
  reloj — puede sobrar tiempo de la ventana de 5h pero agotarse el cupo antes; en ese caso para.
- **Ciclo obligatorio (reforzado 2026-08-20 tras observar que la rutina paraba después de un solo
  sprint sin agotar cupo):** cerrar o bloquear un sprint no termina la corrida. Los únicos 2
  motivos válidos para mandar el correo resumen y terminar son (a) no queda ningún sprint
  elegible en toda la cola, o (b) la sesión se corta sola por límite real de uso — nunca una
  decisión propia de "ya hice suficiente". Mientras haya cola y cupo, se sigue encadenando sprint
  tras sprint.
- Cada sprint sigue el mismo estándar que el resto del backlog: TDD, tests pasando, y la regla ya
  obligatoria de actualizar `README.md`/`docs/GUIA_USUARIO.md` al cerrar.
- Datos públicos que antes solo existían en `docs/Archivos de referencia abogado/` (gitignoreada,
  invisible para el sandbox en la nube) para los Sprints 80/81/82 ahora están extraídos
  programáticamente en `docs/datos_publicos_fuente/` (sí commiteada) — ver el README de esa
  carpeta. Solo se extrajeron series numéricas públicas (IPC/DTF/tasas certificadas), nunca las
  plantillas propietarias del despacho ni el caso de cliente que también viven en esa carpeta.

## Cierre de un sprint

Si el sprint cumple su Definición de Hecho completa (sin criterio especial por ser autónomo):

1. Se marca `✅ Completado` en `Pendientes.md`.
2. Se mergea automáticamente a `main` — réplica exacta del flujo manual actual del usuario
   (worktree → trabajo → merge a `main` al cerrar y documentar), sin gate de aprobación
   adicional.

## Bloqueo no previsto durante el trabajo

Si aparece una decisión crítica no anticipada (mismo patrón que ya exigieron los Sprints
13/16/20/41):

1. Se documenta en el propio sprint: fecha, pregunta exacta, y **si la decisión es del usuario o
   del despacho** (mismo lenguaje que ya usa la leyenda de estados del archivo).
2. Se commitea esa documentación.
3. El sprint pasa a `🔵 Bloqueado`.
4. Se notifica por `PushNotification`.
5. La rutina sigue con el siguiente sprint elegible de la cola — nunca espera bloqueada.

## Notificaciones

Vía `PushNotification` (llega al celular solo si el usuario no está activo en la terminal —
verificado: si está presente, la herramienta se salta el envío porque sería redundante con lo que
ya está viendo):

1. **Al crear/reactivar un 🔵 Bloqueado** — sprint, tipo de decisión (usuario/despacho), pregunta
   exacta.
2. **Al cerrar cada ventana de 5h** — resumen corto: qué se completó, qué quedó 🟡/🔵, qué sigue.

Requiere que el usuario tenga Remote Control conectado en el celular — sin eso no hay a dónde
entregar el push aunque el resto del mecanismo funcione. Pendiente de confirmación definitiva por
parte del usuario ("creo que lo tengo conectado").

## Gestión de la rutina

La rutina se administra en `claude.ai/code/routines` (activar/desactivar/editar horario/eliminar
desde la web) o directamente en sesión pidiéndole a Claude que use `CronList`/`CronCreate`/
`CronDelete`.

## Fuera de alcance / no resuelto en este diseño

- Los límites exactos de la ventana de 5h y semanal no están documentados públicamente para
  planes Pro/Max de claude.ai — los valores usados acá (15:30 / viernes 10am) son los que reportó
  el usuario directamente desde `claude.ai/settings/usage`, no una API verificable.
- No hay forma confirmada de que la rutina misma consulte cupo restante programáticamente antes
  de intentar trabajar; se apoya en que el propio entorno de ejecución falle/no arranque si no
  hay cupo.
