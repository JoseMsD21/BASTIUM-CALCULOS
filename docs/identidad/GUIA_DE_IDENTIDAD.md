# Guía de identidad de BASTIUM

> Resumen operativo del documento maestro del equipo
> [ESTILO_Y_LOGICA_DE_BASTIUM.pdf](ESTILO_Y_LOGICA_DE_BASTIUM.pdf) (131 páginas, 12-nov-2026). Si este resumen y el
> PDF difieren, manda el PDF. Lo que todavía no aplica la aplicación de escritorio está marcado como **pendiente**,
> con su estado en [Pendientes.md](../Pendientes.md) (Sprint 122 y siguientes).

## Qué hay en esta carpeta

| Archivo | Qué es |
|---|---|
| [ESTILO_Y_LOGICA_DE_BASTIUM.pdf](ESTILO_Y_LOGICA_DE_BASTIUM.pdf) | Documento maestro: identidad, UX, redacción, arquitectura y lógica jurídica |
| [mockups/](mockups/) | 5 pantallas de la plataforma propuesta (ver [Mockups](#mockups-de-la-plataforma)) |
| Este archivo | Resumen para aplicar la guía sin leer las 131 páginas |

Los logos no viven aquí sino en [`app/assets/marca/`](../../app/assets/marca/), porque la aplicación y los reportes
los usan directamente (ver [Logos](#logos)). El mapa de flujo del producto está en
[Visión y alcance](../VISION_Y_ALCANCE.md#mapa-de-flujo-del-producto).

## Cómo está organizado el PDF maestro

| Páginas | Contenido | Dónde se aplica en el repo |
|---|---|---|
| 1-3 | Identidad gráfica, UX del SaaS, estilo de redacción y layout del PDF | Esta guía |
| 4-6 | Arquitectura multi-agente (n8n, NotebookLM, Claude, Qwen) y código de ejemplo (FastAPI, flujo de documento) | [Visión y alcance](../VISION_Y_ALCANCE.md#visión-de-plataforma-a-futuro) y [ARQUITECTURA_ADR.md](../ARQUITECTURA_ADR.md) |
| 7-35 | Tablero de referencias visuales ("Human Scribble"): ilustraciones de terceros, solo como inspiración | No se copian al producto |
| 36-115 | Lógica jurídica: ciclo de la obligación, lógica procesal, indicadores, cambios normativos, intereses, indexación, unidades de tiempo, excepciones, obligaciones por área, tablas históricas, reglas de cálculo | Consolida [`REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf`](../REQUERIMIENTOS%20DE%20CALCULO%20Y%20REGLAS%20LOGICAS%20-%20BASTIUM.pdf), que ya es la fuente de los requisitos; ver [Lógica jurídica](#lógica-jurídica-páginas-36-131) |
| 116-131 | "Especificaciones Técnicas de Lexpress" (escaneado): entidades, máquinas de estado por área, semáforo de alertas, plantillas, roles y matriz de vacíos | Ver [Lógica jurídica](#lógica-jurídica-páginas-36-131) |

## Filosofía: "Lujo silencioso y Human Scribble"

BASTIUM debe dar **alivio cognitivo**: nada de interfaces densas ni grillas infinitas. Precisión del diseño suizo
con la calidez de un trazo a mano. El abogado **dirige** al software, nunca compite con él.

## Colores

| Token (guía) | Valor | Uso |
|---|---|---|
| `--bastium-bg-bone` | `#FAF9F6` | Fondo principal (papel hueso) |
| `--bastium-text-charcoal` | `#18181B` | Texto principal (carbón, no negro puro) |
| `--bastium-accent-red` | `#C82E2E` | **Solo** líneas de gráficos, alertas críticas y acentos |
| `--bastium-accent-blue` | `#2563EB` | Enlaces y botón primario en *hover* |
| `--bastium-muted-grid` | `#E5E5E5` | Divisiones de tablas, bordes, cuadrículas |

**Pendiente (decisión del equipo):** la aplicación de escritorio usa hoy la paleta del Sprint 31
([`app/core/theme_colors.py`](../../app/core/theme_colors.py)), parecida pero no igual:

| Rol | App hoy | Guía | Diferencia |
|---|---|---|---|
| Fondo | `#FAF8F4` | `#FAF9F6` | Casi idéntico |
| Texto | `#2B2320` (marrón oscuro) | `#18181B` (carbón) | Más neutro en la guía |
| Acento / primario | `#AE1C21` (borgoña) | `#C82E2E` (rojo ladrillo) | Distinto. Además, el despacho pidió el borgoña `#AE1C21` para gráficas (Sprint 109) |
| Bordes | `#D8CDBB` (beige) | `#E5E5E5` (gris) | Distinto |

Cambiar la paleta toca el tema claro, el oscuro, los `.qss`, PDF, Word y gráficas. Se propone como sprint propio
cuando el equipo confirme qué rojo manda (ver Pendientes, Sprint 122).

## Tipografía

- **Títulos y documentos:** serif con peso institucional (Ancizar o Garamond). Los mockups usan Playfair Display.
- **Interfaz y cuerpo:** sans-serif geométrica (Inter o Geist). La app usa **Ancizar Sans** (en
  [`app/assets/fonts/`](../../app/assets/fonts/)) desde el Sprint 31.
- **Cifras:** obligatorio alinear los números en columnas (`font-variant-numeric: tabular-nums` en web). En Qt y
  reportlab el equivalente es alinear a la derecha las columnas de montos y usar una fuente con dígitos de ancho
  fijo. **Hecho en pantalla** (Sprint 127, `app/views/celdas.py`), con separador de miles igual al PDF (Sprint 129,
  `app/core/formato.py`).
- Los mockups usan además **Caveat** (manuscrita) para notas al margen.

## Logos

Carpeta: [`app/assets/marca/`](../../app/assets/marca/). Rutas en código:
[`app/assets/logos.py`](../../app/assets/logos.py). Los originales tal como los entregó el equipo están en
[`app/assets/marca/originales/`](../../app/assets/marca/originales/).

| Archivo | Contenido | Dónde se usa |
|---|---|---|
| `bastium-logo-horizontal.png` | Mascota + "Bastium." + lema | **Membrete de PDF y Word** (arriba a la izquierda, todas las hojas) |
| `bastium-monograma.png` | "B." con punto rojo, fondo blanco | **Panel lateral** de la aplicación |
| `bastium-monograma-transparente.png` | El mismo monograma sin fondo | Fondos que no son blancos |
| `bastium-icono-256.png` / `bastium-icono.ico` | Monograma cuadrado | **Ícono de la ventana**; el `.ico` queda listo para el instalador |
| `bastium-mascota.png` | El oso con sombrero y corbata roja | Ilustraciones |
| `bastium-mascota-transparente.png` | La mascota sin fondo exterior | **Estados vacíos** (Inicio, listado de expedientes) |
| `bastium-wordmark.png` | Solo "Bastium" en serif | Portadas y encabezados sin mascota |
| `originales/bastium-logo-horizontal-v1-punto-rojo.png` | Versión anterior del logo horizontal (punto rojo, no borgoña) | Histórico |

**Lema oficial:** "La ciencia de resolver lo complejo" (constante `LEMA` en `app/assets/logos.py`).

Reglas:
- No deformar ni recolorear los logos. Si hace falta otro tamaño, generarlo desde `originales/`.
- En documentos para el juzgado, el logo va **sobrio**: arriba a la izquierda, pequeño (≈1 cm de alto).
- El monograma lleva fondo blanco propio para verse igual en modo claro y oscuro.

## Experiencia de usuario (UX)

- **Estructura:** menú lateral izquierdo (colapsable) en tono carbón; área de trabajo en fondo hueso.
- **Listados:** tablas minimalistas, **sin líneas verticales**, solo horizontales finas `#E5E5E5`.
- **Enrutamiento por área:** al abrir un caso, la pantalla cambia según el área (Familia muestra hitos del Defensor
  de Familia y cuotas; Civil muestra la liquidación de intereses). La app ya lo hace en parte con `AreaRegistry`.
- **Calendario de precisión:** alertas tipo semáforo. Rojo: crítico / vencimiento inminente. Amarillo: traslado en
  curso. Verde: informativo. Antelación base 10, 5, 3 y 1 día (escala única hasta que el despacho la diferencie).
- **Estados vacíos:** ilustración de trazo a mano (no íconos genéricos). **Hecho** (Sprint 128): la mascota con un
  mensaje en el Inicio y en el listado de expedientes (`app/views/estado_vacio.py`).
- **Gráficos:** precisión exacta en las alturas pero con aspecto dibujado a mano (bordes irregulares, sombreado
  cruzado). **Choca** con el estándar que pidió el despacho en el Sprint 109 (ejes negros, curva borgoña con
  degradado). Hasta que el despacho decida, se mantiene el estándar del Sprint 109.

## Redacción de documentos

- **Tono:** objetivo, riguroso, forense; empático en tutela y familia. Sin "abogadismo" decimonónico.
- **Gramática:** frases cortas (sujeto, verbo, predicado). Párrafos de 5-6 líneas como máximo.
- **Hechos:** listas numeradas puras (1, 2, 3).

## Layout del PDF generado

| Elemento | Estado |
|---|---|
| Membrete: logo sobrio arriba a la izquierda + lema | ✅ Hecho (Sprint 122), PDF y Word |
| Tablas de liquidación con bordes limpios, miles separados y decimales precisos | ✅ Ya existía (Sprints 50 y 108) |
| Sello criptográfico al final (QR + marca de agua + SHA-256) junto a la firma del apoderado | Pendiente. El parche de plataforma del 17-nov trae un sello SHA-256 (ver [revisión](../REVISION_PLATAFORMA_2026-11-17.md)) |

## Mockups de la plataforma

Pantallas compartidas por el equipo el 20-nov-2026 ("mockups de las ventanas desde el gestor de casos y los demás
servicios que se integrarán"). Las versiones HTML y la guía frontend están en la carpeta de Drive del equipo
(*MOCKUPS PROPUESTA*). **Son ilustrativos:** sus cifras no están validadas y no reemplazan los cálculos del motor.

| Archivo | Pantalla | Qué muestra |
|---|---|---|
| [01-pipeline-multiagente.jpeg](mockups/01-pipeline-multiagente.jpeg) | Pipeline multi-agente (Mockup B, el del oso, referencia canónica) | Entrada por WhatsApp/Telegram, 7 etapas (n8n, clasificador local, extracción, doble validación IA, cálculo determinista, redacción, PDF sellado) y vista previa del documento |
| [02-gestor-de-conocimiento.jpeg](mockups/02-gestor-de-conocimiento.jpeg) | Gestor de conocimiento (estilo NotebookLM) | Biblioteca de códigos, jurisprudencia y doctrina; conversación con citas; citas fijadas |
| [03-generador-documental.jpeg](mockups/03-generador-documental.jpeg) | Generador documental | Plantillas (demanda laboral, ejecutiva, alimentos, tutela, memoriales), variables Jinja2, vista previa y checklist CGP art. 82 + 422 |
| [04-detalle-del-caso.jpeg](mockups/04-detalle-del-caso.jpeg) | Detalle del caso | Partes, línea de tiempo, liquidación consolidada, seguridad social, calendario con semáforos y auditoría SHA-256 |
| [05-configuracion-parametros.jpeg](mockups/05-configuracion-parametros.jpeg) | Configuración de parámetros legales | Parámetros por categoría, versión y fuente; edición protegida con doble firma HMAC |

Cifras de los mockups que **no** coinciden con el motor (no usarlas como referencia):
- *Auxilio de transporte 2026 = $162.000* (mockup 05). Ese fue el valor de 2024; el motor tiene $249.095 para 2026.
- *Intereses moratorios sobre salarios y cesantías con 51 días de mora* (mockups 01-04). Según el art. 65 CST, en
  los primeros 24 meses corre un día de salario por día de retardo; los intereses moratorios empiezan después del
  mes 24.

## Lógica jurídica (páginas 36-131)

Esta parte consolida el documento de requerimientos que ya guía al motor. Lo nuevo y útil para el desarrollo:

- **Ciclo de vida de la obligación (p. 36-39):** 14 eventos (nacimiento, modificación, mora, pagos, conciliación,
  demanda, admisión, notificación, contestación, pruebas, sentencia, liquidación, recursos, archivo) con qué
  produce, qué modifica, qué cálculo afecta, qué fechas genera y qué soporte exige cada uno.
- **Estados del proceso sugeridos:** Pre-judicial, Admitido, Notificado, En Pruebas, Sentenciado, En Ejecución,
  Archivado. Estados mínimos de obligación y de liquidación en la p. 105.
- **Catálogo canónico de reglas (p. 112-114):** esquema `id_regla`, condiciones, vigencia, fuente, fórmula,
  redondeo, compatibilidades, eventos que suspenden/interrumpen/extinguen, y un catálogo inicial `R-CIV-001`...
  `R-PROC-...`. Base para un futuro motor de reglas versionado.
- **Requisitos de auditoría (p. 112):** cada liquidación debe exponer fórmula, fuente, fecha de consulta, vigencia,
  tramo y soporte; guardar "por qué" eligió cada regla; reconstruir una liquidación histórica aunque las tasas
  cambien.
- **Especificaciones de Lexpress (p. 116-131):** 14 entidades transversales con su ciclo de vida, máquinas de
  estado (expediente, penal Ley 906, familia de mutuo acuerdo con NNA, sincronización con la Rama Judicial),
  semáforo de alertas, *placeholders* de plantillas, roles (socio, litigante, paralegal, lectura), RBAC con muros
  éticos, auditoría inmutable de 2 años y una **matriz de vacíos** (Administrativo, Disciplinario, Societario y
  Tributario sin insumos suficientes). Conclusión del documento: priorizar Civil, Penal, Familia y Laboral.

Lo que el motor ya cumple de esta parte: interés civil 6 % lineal (÷365), conversión efectiva para tasas EA,
indexación IPC, imputación costas → intereses → capital, usura por tramos sin extrapolar, anatocismo apagado,
art. 65 CST bifásico. El código de ejemplo de la p. 4-5 (FastAPI) es ilustrativo: devuelve `float` en el detalle,
lo que la regla de "Decimal en toda ruta de dinero" del proyecto no permite.

## Derechos de las imágenes de referencia

Las páginas 7-35 del PDF reúnen ilustraciones y capturas de terceros como inspiración. No se copian al producto. El
repositorio es público: si el equipo prefiere no publicar ese tablero, se puede reemplazar el PDF por una versión
sin esas páginas.
