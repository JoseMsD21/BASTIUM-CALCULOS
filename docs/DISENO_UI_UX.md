# Diseño UI/UX — BASTIUM

> Resumen del sistema de diseño y los patrones de interacción ya construidos. El detalle de decisión por
> pantalla vive en cada sprint de [Pendientes.md](Pendientes.md) y, cuando existe, en su spec de diseño
> dentro de [docs/superpowers/specs/](superpowers/specs/) — este documento no repite ese contenido, lo
> indexa.

## Sistema de diseño visual (Sprint 31)

Tema, color, tipografía e íconos unificados en toda la GUI, con modo oscuro/claro alternable desde
⚙ Configuraciones → Apariencia y persistido entre sesiones (spec de diseño:
`2026-08-13-configuraciones-apariencia-design.md`).

## Navegación (Sprint 32)

Panel lateral fijo, breadcrumb y atajos de teclado. La navegación y el CRUD de expediente base se
diseñaron primero en `2026-07-19-navegacion-y-crud-expediente-design.md`; el breadcrumb y los atajos son
una capa posterior sobre esa base (Sprint 32).

## Dashboard de inicio (Sprint 33)

Pantalla de inicio con resumen, alertas de vencimiento (prescripción/caducidad) y una gráfica de
expedientes por área.

## Formularios (Sprint 34, Sprint 24)

- Agrupación por secciones, ayuda contextual (tooltips ⓘ con ejemplo concreto) y feedback en tiempo real
  en los 4 formularios principales de captura (Obligación, Expediente, Abono, Parámetro).
- Validación de datos (rechazo de valores absurdos) — `2026-08-01-sprint24-validacion-datos-design.md`.
- CRUD y UX de diálogos de Parámetros — `2026-08-11-parametros-ux-dialogos-crud-design.md` y
  `2026-08-13-parametros-crud-usuario-design.md`.
- Indicador visible de checkbox — `2026-08-13-checkbox-indicador-visible-design.md`.

## Búsqueda, filtros y estados vacíos (Sprint 35)

Búsqueda y filtros en listados, con un estado vacío explícito en vez de una tabla en blanco sin contexto.

## Feedback y jerarquía de botones (Sprint 36)

Notificaciones no bloqueantes tipo toast para confirmaciones de bajo riesgo, y jerarquía visual clara entre
acción primaria/secundaria/destructiva en los botones.

## Patrones de interacción transversales

- Los 7 diálogos de formulario del proyecto (Obligación, Expediente, Abono, Parámetro, Evento contractual,
  Descuento laboral, historial de un Parámetro) se pueden minimizar, maximizar y redimensionar; los
  diálogos de confirmación (ej. "¿Eliminar esta obligación?") no, son mensajes simples.
- Restablecer datos de fábrica requiere escribir "RESTABLECER" para confirmar, con backup automático previo
  — `2026-08-13-restablecer-datos-fabrica-design.md`.

## Convención hacia adelante

Cualquier sprint que introduzca un patrón de UI reutilizable en más de una pantalla (no una pantalla
puntual) debe agregarse a este documento como una línea nueva, citando el sprint y, si existe, su spec de
diseño — igual que el resto de la documentación, no debe quedar desactualizado respecto a la GUI real.
