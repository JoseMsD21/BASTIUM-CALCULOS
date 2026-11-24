# Revisión del aporte "BASTIUM PLATAFORMA" (17/11/2026)

Fecha de la revisión: 23/11/2026. Base de comparación: `main` en `53b856d` (Sprint 121, 2045 pruebas).
Material revisado: `bastium_plataforma_2026-11-17.patch` (154 archivos, ~15.000 líneas) y el ZIP con los
mismos archivos ya aplicados. No se modificó el repositorio; las pruebas se corrieron en dos copias
temporales (worktrees) que ya se borraron.

> **Estado (Sprint 130, 2026-11-23):** fases **0 y 1** hechas. La fase 1 (Sprint 130, ADR-008) dejó el motor
> importable sin base de datos, `holidays` ni Qt, sin cambiar cifras.
>
> **Estado (Sprint 122, 2026-11-23):** la **fase 0** ya se aplicó (`.gitignore`, `calculator.py` y
> `app/domain/radicado.py` con sus pruebas). El parche y el ZIP eran archivos temporales y se borraron de la raíz
> del repositorio; el material original sigue en la
> [carpeta de propuestas de Drive](https://drive.google.com/drive/folders/1ZYauFW9pEKFfjMCC1RIHtDJ2pwrut78f)
> (*AUDITORIA Y PRESENTACION V2*). Las fases 1 a 5 esperan las decisiones del equipo y del despacho de la
> sección 6; están en [Pendientes.md](Pendientes.md), Sprint 123, y en la tarjeta #64 del
> [tablero Kanban](https://github.com/users/JoseMsD21/projects/1).

---

## 0. Resumen en cinco frases

1. El aporte es, sobre todo, **un programa nuevo** dentro del repositorio: un **gestor de casos web local**
   (`bastium/`: clientes, casos, términos, vigilancia de la Rama Judicial, escritos `.docx`, corpus de
   conocimiento) más la **capa API** (`bastium_api/`, FastAPI + Docker) que ya conocíamos del paquete de
   noviembre.
2. **No reimplementa el cálculo de liquidaciones**: tanto el gestor como la API llaman al mismo
   `LiquidationCore` de `app/engine`. Pero **por defecto usan el redondeo "exacto por período"**, no el del
   escritorio, así que **las cifras del gestor/API no coinciden con las del escritorio** (pregunta 3 del
   Sprint 118, aún sin respuesta del despacho).
3. Los archivos **existentes** que modifica están hechos sobre el `main` del 17/11: aplicar el ZIP tal cual
   **borraría trabajo ya integrado** (costas sin intereses del Sprint 79, horas extra del 95, fruto civil
   del 100, Suma Única tramo a tramo del 104, CHANGELOG/README/Mapa de documentación de los Sprints 118-121)
   y **cambiaría plazos** (calendario propio con vacancia al 10 de enero y sin el festivo de Chiquinquirá).
4. Al revés también hay choque: el `main` actual hace que el motor arrastre SQLAlchemy, la base de datos y
   `holidays` (por la Suma Única del Sprint 104). Eso **rompe la promesa "API/gestor sin base de datos"**
   (2 pruebas de arquitectura fallan) y el contenedor Docker no arrancaría.
5. Recomendación: **no fusionar el paquete entero**. Integrar por fases: primero lo pequeño y seguro
   (radicado, `.gitignore`, `conftest` ya está), luego —si el equipo decide el punto #7— la API y el gestor
   como paquetes nuevos **sin tocar** `app/engine`, con el redondeo por defecto igual al del escritorio
   hasta que el despacho responda.

---

## 1. Qué trae el aporte (componentes nuevos)

### 1.1 El gestor de casos `bastium/` (~5.800 líneas + 208 pruebas)

Un "segundo programa" que convive con la aplicación de escritorio. Es un servidor web **local** (solo
`127.0.0.1`, puerto 8765) que se abre en el navegador; sin Qt, sin SQLAlchemy, sin IA, sin JavaScript. Los
datos viven fuera del repositorio (`%LOCALAPPDATA%\Bastium\bastium_gestor.db`). Se abre con `Bastium.bat`
(Windows) o `bastium.sh`; `Bastium.bat demo` crea una copia con datos ficticios. Capas:

| Capa | Archivos | Qué hace |
|---|---|---|
| `dominio/` | `asunto.py`, `estados.py`, `termino.py`, `actuacion.py`, `documentos.py`, `errores.py` | Reglas puras: tipos de asunto ("puertas" G1/G2: ¿trámite o caso?, ¿hay radicado?), máquinas de estado por tipo de asunto (Prospecto → … → Terminado), cálculo de términos con traza y semáforo (amarillo 10 / naranja 5 / rojo 3 días hábiles), actuaciones que solo nacen con confirmación humana (G3), listas de verificación de cada escrito con la norma citada (G5). |
| `aplicacion/` | `sistema.py`, `comandos.py`, `gestion.py`, `terminos.py`, `vigilancia.py`, `documental.py`, `conocimiento.py` | Casos de uso: clientes y casos (con chequeo de **conflicto de interés** y autorización de datos en borrador), términos y alertas, vigilancia de la Rama Judicial, liquidaciones selladas y escritos `.docx`, corpus de conocimiento con citas y "puente" manual a NotebookLM. Bandeja de salida transaccional y tareas que corren al abrir y cada minuto (sin cron). |
| `adaptadores/` | `persistencia.py`, `rama_judicial.py`, `documentos.py`, `plantillas.py`, `conocimiento.py`, `notificador.py` | Todo lo intercambiable: SQL directo con `sqlite3` (sin ORM, dinero como texto, `despacho_id` en todas las tablas), cliente HTTP del portal `consultaprocesos.ramajudicial.gov.co` (1 consulta/24 h por proceso, pausa 2 s; **contrato del portal no verificado con datos reales**), render `.docx` propio (Jinja2 + zipfile), búsqueda FTS5 por palabras, avisos internos y por Telegram opcional. |
| `plataforma/` | `bd.py`, `auditoria.py`, `config.py`, `reloj.py` | Esquema y migraciones por `PRAGMA user_version`, auditoría encadenada por hash, configuración por variables de entorno, reloj inyectable. |
| `presentacion/web/` | `app.py` + 19 plantillas HTML + CSS | Interfaz Starlette/Jinja2: tablero, clientes, casos, términos, vigilancia, liquidación, documentos, conocimiento, auditoría, ajustes. |
| raíz | `__main__.py`, `motor.py`, `demo.py` | Lanzador (`python -m bastium [demo|estado|respaldar|auditoria|plantillas]`), **única puerta al cálculo** (`motor.py`, que llama a `bastium_api.service` → `LiquidationCore`) y datos de demostración. |

Lo que el propio autor declara **no construido**: varios usuarios/roles/2FA, cifrado de la base, búsqueda
sin radicado, buzón de notificaciones por correo, IA, liquidaciones de otras áreas (el gestor solo liquida
mora civil art. 1617 y tasa pactada simple), instalador.

### 1.2 La capa API `bastium_api/` (~1.500 líneas + 95 pruebas)

Ya venía en el paquete de noviembre (fase 3 del plan, "decisión del equipo", tarjeta #7). Servicio FastAPI
con: contratos Pydantic (montos solo como texto, `extra="forbid"`), `service.py` (arma eventos y llama a
`LiquidationCore`), **sello SHA-256** reproducible (`canonico.py`, `verificacion.py`), generación de `.docx`
(`documentos.py`, `render_interno.py`, `plantilla.py`), almacén de documentos por hash (`almacen.py`),
clave de API obligatoria (`seguridad.py`), errores RFC 7807 (`problemas.py`) y parámetros legales en un
JSON propio (`data/parametros_v1.json`: 6 % anual, base 365). Endpoints: `GET /salud`, `GET /v1/version`,
`POST /v1/liquidaciones/mora`, `POST /v1/liquidaciones/mora/documento`, `GET /v1/documentos/{sha256}`.

### 1.3 Piezas sueltas en `app/`

| Archivo | Qué hace |
|---|---|
| `app/domain/radicado.py` | Valida y descompone el radicado de 23 dígitos (Acuerdo 201/1997). Puro, sin efectos. |
| `app/engine/time/calendario_procesal.py` | Calendario propio (festivos calculados a mano, vacancia 20-dic a **10**-ene, perfiles por despacho). **No trae el festivo de Chiquinquirá** (13/07/2026). Es el mismo bloqueado en la fase 4 del plan de noviembre. |

### 1.4 Despliegue, empaquetado y CI

| Pieza | Qué hace |
|---|---|
| `Dockerfile`, `docker-compose.yml`, `.dockerignore` | Imagen mínima de la API (usuario sin privilegios, solo lectura, sin capacidades). Compose publica solo en `127.0.0.1:8000`. |
| `empaquetado/` (`bastium.spec`, `arranque.py`, `construir.bat`, `LEEME.md`) | Receta **PyInstaller** para entregar `Bastium.exe` del gestor sin instalar Python. **Nunca se ejecutó** (lo dice el autor). |
| `Bastium.bat`, `bastium.sh` | Lanzadores del gestor; crean `.venv-gestor` e instalan `requirements-gestor.txt`. |
| `plantillas/*.docx` (5) | Plantillas de liquidación, demanda, memorial, poder especial y derecho de petición, generadas por código. |
| `scripts/verificar_sello.py` | Verifica (o reproduce con `--reproducir`) el sello de una liquidación emitida. |
| `scripts/exportar_contrato_api.py` | Regenera los esquemas JSON de `docs/api/`; con `--check` falla si están desactualizados. |
| `scripts/crear_plantilla_liquidacion.py` | Regenera `plantillas/plantilla_liquidacion.docx`. |
| `.github/workflows/ci-core.yml` | CI en Linux (3.13/3.14) del motor + API sin Qt: ruff, contrato al día, plantilla reproducible, pruebas puras. |
| `.github/workflows/ci-gestor.yml` | CI en Ubuntu y Windows del gestor con solo `requirements-gestor-dev.txt`, más un arranque real. |
| `requirements-api.txt`, `-api-dev`, `-gestor.txt`, `-gestor-dev` | Dependencias por capa (pydantic, fastapi, uvicorn, docxtpl, python-docx / starlette, jinja2, python-multipart, pypdf). |

### 1.5 Documentación nueva

| Documento | Contenido |
|---|---|
| `docs/GESTOR_PLATAFORMA.md` | Qué está construido, capas, "puertas" G1-G8, ADR-009 a 013, qué falta y qué no se verificó (portal real, Windows, empaquetado, ruff, Telegram). |
| `docs/GESTOR_GUIA_ABOGADO.md` | Guía de uso del gestor para el abogado. |
| `docs/GESTOR_PLAN_EQUIPO.md` | Tareas para el abogado (A1-A8), dev 1 (D1-1 a D1-7) y dev 2 (D2-1 a D2-7) con criterio de "hecho". |
| `docs/INTEGRACION_GESTOR_CASOS.md` | Hoja de ruta para integrar un sistema externo (Vue/Laravel/n8n) con la API; la clave de API nunca en el navegador. |
| `docs/API_CONTRATO.md`, `docs/api/*.json` | Contrato de la API y esquemas JSON generados + ejemplos. |
| `docs/AUDITORIA_MOTOR_CALCULO.md` | La auditoría del 12/11 (H1-H7), ya conocida y parcialmente integrada en el Sprint 118. |

Encaje con la visión del equipo (SaaS, n8n, "Bastium Core" determinista, PDFs sellados, gestor de casos,
Docker local-first): **encaja bien en la idea** (la IA no calcula; dinero en `Decimal`; sello SHA-256;
gestor de casos; Docker). Diferencias: el sello va sobre `.docx` + JSON, no PDF; y el gestor se construyó
**dentro** de este repositorio en Python/Starlette, mientras `INTEGRACION_GESTOR_CASOS.md` todavía describe
un gestor externo en Laravel/Vue + n8n. El equipo tiene que elegir uno de los dos caminos.

---

## 2. Archivos existentes que el aporte modifica (ZIP frente a `main` actual)

Leyenda: **(a)** ya está en `main` · **(b)** mejora segura, se puede tomar · **(c)** cambia cifras, plazos o
comportamiento jurídico (necesita al despacho) · **(d)** choca con trabajo que `main` hizo después del
17/11 (tomarlo **borraría** ese trabajo).

Cómo se hizo: se comparó cada archivo del ZIP contra `main:<archivo>` (no contra el parche, que está hecho
sobre un `main` viejo y por eso `git apply` falla).

| Archivo | Clase | Qué cambia exactamente |
|---|---|---|
| `app/engine/liquidation/engine.py` | **(a) + (d)** | Lo único nuevo del parche (parámetro `politica_causacion`, `CONTEXTO_FORENSE`) **ya está en `main`** (Sprint 118). Contra el `main` actual, el archivo del ZIP **quita**: costas como componente aparte sin intereses (Sprint 79; vuelven a ser capital y a generar interés), los conceptos `HORAS_EXTRA` (Sprint 95) y `FRUTO_CIVIL` (Sprint 100), y toda la causación tramo a tramo de Suma Única con abonos (Sprint 104). **No tomar.** |
| `app/engine/temporal/timeline.py` | **(a)** | Idéntico a `main` (el `Decimal` en vez de `float` ya entró en el Sprint 118). |
| `app/services/motor_universal.py` | **(a) + (d)** | El parámetro `politica_causacion` ya está; el ZIP **quita** `causacion_tramo_a_tramo` (Sprint 104). **No tomar.** |
| `config/decimal_config.py` | **(a)** | Idéntico a `main`. |
| `tests/conftest.py` | **(a)** | Idéntico a `main` (los `try/except` para entornos sin Qt/SQLAlchemy ya entraron). |
| `app/engine/liquidation/politica.py`, `tests/architecture/test_sin_float_en_el_motor.py`, `tests/core/test_decimal_config.py`, `tests/liquidation/test_politica_causacion.py`, `tests/architecture/__init__.py` | **(a)** | El parche los trae como "nuevos" pero ya existen en `main`, idénticos. |
| `app/reports/pdf.py` | **(a) + (d)** | El cambio del parche (totales en `Decimal`) ya está en `main`. Contra `main`, el ZIP **quita** las filas "Fruto Civil Causado" (Sprint 100) y "Costas Procesales (no generan interés)" (Sprint 79) del resumen del PDF. (El membrete con logo que `main` tiene sin commit no se evaluó.) **No tomar.** |
| `app/engine/liquidation/calculator.py` (`FamilyLawCalculator`) | **(b)** con nota | Cambia la tasa a 6 %/365 lineal y el redondeo a `ROUND_HALF_UP`. La clase **no tiene ningún consumidor** en `app/` y el despacho ya confirmó la fórmula lineal (Sprint 76), así que la tarjeta #10 se puede cerrar con este cambio. No mueve ninguna cifra real. |
| `app/engine/time/calendar.py` | **(c)** | Reemplaza la librería `holidays` por el calendario propio: vacancia hasta el **10** de enero (el despacho respondió 11) y **sin el festivo de Chiquinquirá** (13/07/2026, 12/07/2027). Cambia vencimientos. Es la fase 4 bloqueada (preguntas 1, 2 y 6 del Sprint 118). **No tomar.** |
| `tests/temporal/test_calendar.py`, `tests/temporal/test_terminos.py` | **(c)** | Solo cambian comentarios "11 → 10 de enero" para acompañar al calendario propio. |
| `docs/specifications/01_motor_temporal.md` | **(c) + (d)** | Cambia "11 → 10 de enero" y además **borra** los párrafos de los Sprints 73/106 (título ejecutivo, fechas anuales fijas, formato de fecha). |
| `CHANGELOG.md` | **(d)** | Agrega un párrafo del 17/11, pero el archivo base es viejo: **borra** las entradas de los Sprints 76, 79, 84, 95, 96, 100, 104-107, 110, 118-121. Tomar solo el párrafo nuevo, a mano y reescrito. |
| `README.md` | **(d)** | Agrega un aviso del gestor, pero **devuelve** "Estado actual" al 2026-08-20 (borra las novedades de noviembre) y quita la sección del tablero Kanban. Tomar solo el aviso, y solo si el gestor entra. |
| `docs/MAPA_DOCUMENTACION.md` | **(d)** + (b) | Agrega una tabla útil de documentos del gestor, pero **borra** las filas del tablero Kanban y del plan de integración de noviembre. Tomar solo la tabla nueva cuando entren esos documentos. |
| `docs/ARQUITECTURA_ADR.md` | **(d)** | Agrega ADR-007 (API), ADR-008 (sello) y ADR-009 a 013 (gestor). **Choque de numeración**: en `main` el ADR-007 ya es "Política decimal en todos los hilos". Renumerar si se toman. |
| `docs/Preguntas-Para-Abogado-Abiertas.md` | **(d)** + (c) | Agrega "Sprint 117-B" (5 preguntas de la API) y "Sprint 118" (10 decisiones del gestor). **Choque**: en `main` el "Sprint 118" ya es la integración de noviembre con sus 6 preguntas. Las 5 del 117-B están **casi todas repetidas** en el Sprint 118 de `main` (redondeo, pagos anticipados, vacancia por despacho, notificación). Las 10 del gestor sí son nuevas, pero solo tienen sentido si el gestor entra. |
| `requirements.txt` | decisión del equipo | Agrega `-r requirements-gestor.txt`: todo el que instale el escritorio arrastraría starlette, uvicorn, jinja2, python-multipart, pypdf… Mejor dejar `requirements.txt` igual y que el CI del gestor instale lo suyo. |
| `pyproject.toml` | **(b)** con nota | Agrega `bastium`, `bastium_api` a `known-first-party` (bien) y una excepción `E501` para todo `bastium/` "pendiente de quitar" (mejor no tomarla; ver §4). |
| `.gitignore` | **(b)** | Agrega `.venv-gestor/`, `almacen_documentos/`, `build/`, `dist/`, `*.sesion`. Inofensivo, se puede tomar ya. |

**Conclusión de esta sección:** de los archivos existentes, lo único que se puede tomar tal cual es
`.gitignore`, `calculator.py` y la mitad de `pyproject.toml`. Todo lo demás o ya está en `main`, o borraría
trabajo de los Sprints 76-121, o cambia plazos.

---

## 3. ¿Duplica el motor? ¿Calcula la API por su cuenta? ¿`float`? ¿Seguridad?

### 3.1 Relación con `app/engine`

- **No reimplementa la liquidación.** `bastium_api/service.py` arma eventos `INSTALLMENT`/`PAYMENT` y llama
  al mismo `LiquidationCore` del escritorio. El gestor solo toca el cálculo por `bastium/motor.py`, que a su
  vez llama a la API por función (no por HTTP). Una prueba de arquitectura lo exige.
- **Pero sí toma decisiones de cálculo propias**, y ahí está el riesgo:
  1. **Redondeo por defecto distinto.** El contrato de la API pone `politica_causacion =
     EXACTA_POR_PERIODO` por defecto, y el gestor no lo cambia. El escritorio usa `LEGADA_DIARIA_REDONDEADA`.
     Mismo caso → **cifras distintas** en gestor/API y escritorio (ejemplo de la auditoría: $601.643,84
     frente a $601.645,44). Es la pregunta 3 del Sprint 118, sin respuesta.
  2. **Segunda fuente de parámetros legales.** La tasa del 6 % sale de `bastium_api/data/parametros_v1.json`,
     no de la tabla `ParametroLegal` del escritorio (ADR-004). Hoy coinciden; mañana pueden divergir.
  3. **Alcance mínimo.** Solo mora civil art. 1617 y tasa pactada lineal: sin costas, indexación, usura ni
     Suma Única. Una liquidación del gestor para un caso con costas o indexación quedaría incompleta frente
     a la del escritorio.
  4. **Términos del gestor**: `bastium/motor.py` le entrega al gestor el **calendario propio**
     (`calendario_procesal.py`), no `CalendarUtils`. Aunque no toquemos `calendar.py`, los vencimientos del
     gestor seguirían la regla del 10 de enero y no tendrían el festivo de Chiquinquirá: **cambio de
     plazos**. El gestor además trae supuestos propios sin confirmar (notificación surtida a los 2 días
     hábiles, plazos en días calendario que no se prorrogan, semáforo 10/5/3/1).
- **Choque inverso con `main`:** desde el Sprint 104, `app/engine/liquidation/engine.py` importa
  `suma_unica_con_abonos` → `historical_index` → **SQLAlchemy + `database` + `holidays`**. Con el `main`
  actual, la API y el gestor **ya no son "sin base de datos"**: fallan 2 pruebas de arquitectura y el
  contenedor Docker (que no instala SQLAlchemy ni copia `database/`) no arrancaría. Hay que arreglarlo en
  `main` (import perezoso de `CausacionTramoATramo`, o un proveedor de IPC inyectado) antes de integrar
  cualquier capa headless.

### 3.2 `float` en rutas de dinero

No se encontró. `bastium_api/canonico.py` prohíbe `float` (lanza error), los contratos rechazan números
JSON, `parametros.py` lee con `parse_float=Decimal` y el gestor guarda dinero como texto. Los únicos `float`
del gestor son tiempos de espera del cliente HTTP (segundos), no dinero. Hay pruebas que lo exigen.

### 3.3 Seguridad

Bien resuelto:
- Sin secretos en el código: la clave de API (`BASTIUM_API_KEY`, mínimo 32 caracteres; la API **no
  arranca** sin ella; comparación en tiempo constante) y el token de Telegram vienen de variables de entorno.
- La API no habilita CORS (no lo necesita: la clave nunca va al navegador). `docker-compose` publica solo
  en `127.0.0.1:8000`; contenedor de solo lectura, sin capacidades, usuario sin privilegios.
- El gestor escucha solo en `127.0.0.1`, rechaza `Host` ajenos, usa llave de sesión aleatoria por arranque
  en cookie `HttpOnly` + `SameSite=Strict`, ficha anti-falsificación (HMAC) en todo POST y CSP sin scripts.
  SQL con parámetros y nombres de tabla/columna en lista blanca.

A revisar:
1. **El "sello" no es una firma.** Es un SHA-256 de datos públicos: prueba que el cálculo es
   reproducible, **no** que lo emitió Bastium (cualquiera puede cambiar los datos y recalcular el hash). No
   presentarlo ante un juez como "documento sellado/firmado" sin una firma real (clave privada o sellado de
   tiempo). Vale también para la idea de "PDFs sellados SHA-256" de la visión.
2. El `Dockerfile` corre uvicorn en `0.0.0.0` dentro del contenedor: correcto con el compose (que limita a
   `127.0.0.1`), pero un `docker run -p 8000:8000` la expone a toda la red (con clave, eso sí). Documentarlo.
3. La llave de sesión del gestor viaja en la URL (`/entrar?llave=…`) que abre el navegador: queda en el
   historial. Riesgo bajo (cambia en cada arranque).
4. `_ruta_local` acepta rutas tipo `/\otro-sitio`, que algunos navegadores tratan como `//otro-sitio`
   (redirección abierta). Menor.
5. El cliente de la Rama Judicial se identifica con el **correo del abogado** en el `User-Agent` (dato
   personal; decisión del despacho, punto 10 del gestor).
6. Datos de clientes del gestor en SQLite **sin cifrar** (el autor lo reconoce). Con datos reales, exigir
   cifrado de disco o decidir SQLCipher antes de usarlo.
7. Sin usuarios ni roles: cualquiera que use el equipo ve todo.

---

## 4. Pruebas ejecutadas

Entorno: copia limpia de `main` (`53b856d`) en worktrees temporales, `.venv` del repositorio (Python 3.13;
ya trae fastapi, httpx, pydantic, docxtpl, python-docx, starlette, uvicorn; **no** trae `python-multipart` ni
`pypdf`, y no se instalaron), `QT_QPA_PLATFORM=offscreen`. Los worktrees se borraron al terminar.

### Escenario A — `main` + solo los archivos **nuevos** del aporte (lo que integraríamos de verdad)

**2514 pruebas: 2492 pasan, 22 fallan** (3 min 17 s). Las 2045 de `main` siguen en verde. Las 22 fallas
son todas de pruebas nuevas:

| Fallas | Causa | ¿Grave? |
|---|---|---|
| 8 × `tests/bastium/test_web.py` | Falta `python-multipart` en el venv | No: dependencia sin instalar. |
| 2 × `tests/bastium/test_conocimiento.py` | Falta `pypdf` (opcional) | No. |
| 2 × `test_arquitectura.py` (red solo en adaptadores; SQL solo en persistencia) | La prueba compara rutas con `/` y en Windows salen con `\` | Error de la prueba en Windows (el autor no probó en Windows). Fácil. |
| 6 × plantillas `.docx` "reproducibles" (`test_documentos`, `test_documental` ×4, `test_lanzador`) | Los bytes del `.docx` generado en Windows difieren de los versionados (cambia el tamaño comprimido: depende de zlib) | Medio: la reproducibilidad "byte a byte" no se cumple entre sistemas operativos. |
| 1 × `test_almacen_seguridad::test_escrituras_concurrentes_del_mismo_contenido` | La escritura atómica del almacén falla en Windows (`PermissionError`) | Medio: ya se vio en noviembre. |
| 2 × `test_api_sin_ui_ni_base_de_datos`, `test_arrancar_la_plataforma_no_carga_qt_ni_orm…` | El motor de `main` (Sprint 104) arrastra SQLAlchemy, `database` y `holidays` | **Alto**: ver §3.1. |
| 1 × `test_coincide_con_la_libreria_holidays_1984_2100` | Al calendario propio le falta el 13/07/2026 (Chiquinquirá) | **Alto (jurídico)**: confirma el hallazgo de la fase 0 de noviembre; el autor no lo corrigió. |

`ruff check .` con el `pyproject.toml` del aporte: 4 errores (línea larga en `calendario_procesal.py`,
`UP047` en `comandos.py`, import sin usar y desordenado en `test_lanzador.py`). `ruff format --check`: 35
archivos sin formatear. El CI actual de `main` (`ruff check .`) fallaría.

### Escenario B — `main` + el ZIP completo encima ("copiar y pegar")

Sin `tests/views`: **1909 pruebas: 1748 pasan, 161 fallan**. Además `tests/views` **se cuelga** (se cortó a
los 15 minutos, con errores en varias pruebas de vistas). Las fallas extra son trabajo de `main` que el ZIP
borra: costas sin intereses (Sprint 79), Sprint 76 (Radicado 2224), fruto civil (100), horas extra (95),
Suma Única tramo a tramo (104), vista de sensibilidad (107), casi todo
`tests/services/test_area_strategy.py` y 2 de `tests/reports/test_pdf.py`. **Confirma que el paquete no se
puede aplicar tal cual.**

---

## 5. Recomendación: plan de integración por fases

Regla del equipo aplicada: se toman mejoras, no reemplazos; nada que cambie cifras o plazos entra sin el
despacho.

| Fase | Qué entra | Depende de | Esfuerzo (1 persona) |
|---|---|---|---|
| **0. Ya** | `.gitignore` (5 líneas), `calculator.py` (cierra la tarjeta #10; Sprint 76 ya respondido), `app/domain/radicado.py` + `tests/domain/test_radicado.py` (puro, útil también para el escritorio). | Nada | 0,5 día |
| **1. Preparar `main`** ✅ Hecho (Sprint 130) | Cortar la dependencia `engine.py` → `suma_unica_con_abonos` → SQLAlchemy/`holidays` (import perezoso o proveedor de IPC inyectado), sin cambiar ninguna cifra (las 2045 pruebas deben seguir iguales). | Nada | 1 día |
| **2. API (`bastium_api/`)** | Paquete nuevo + `tests/api`, `test_api_sin_ui_ni_base_de_datos`, `requirements-api*.txt`, `scripts/exportar_contrato_api.py`, `verificar_sello.py`, `docs/API_CONTRATO.md`, `docs/api/`, `ci-core.yml`, Docker. **Condiciones:** `politica_causacion` por defecto = `LEGADA_DIARIA_REDONDEADA` (igual al escritorio) hasta la respuesta 3; arreglar la escritura concurrente en Windows y la reproducibilidad del `.docx`; ruff limpio; ADR renumerado; no decir "firmado". | **Decisión #7 del equipo** + fase 1 | 2-3 días |
| **3. Gestor (`bastium/`)** | Paquete nuevo + `tests/bastium` + plantillas `.docx` + lanzadores + docs `GESTOR_*`. **Condiciones:** que el gestor use `CalendarUtils` (o un calendario propio que pase la validación contra `holidays` 1984-2100 y use la regla de vacancia que diga el despacho); redondeo igual al escritorio; arreglar las pruebas de Windows; quitar la excepción `E501` y formatear; no tocar `requirements.txt` del escritorio; renombrar sus "Sprint 117-B/118" a números libres. | Decisión del equipo (es un producto nuevo: ¿gestor dentro del repo en Python, o gestor externo Laravel/Vue + n8n como dice `INTEGRACION_GESTOR_CASOS.md`?) + fase 2 + respuestas del despacho para usarlo con casos reales | 5-8 días (más la prueba en Windows y el empaquetado, que nunca se ejecutaron) |
| **4. Calendario propio** | `calendario_procesal.py` como reemplazo de `holidays` en el escritorio. | Respuestas 1, 2 y 6 del Sprint 118 + agregar Chiquinquirá | 2 días + validación |
| **5. Redondeo exacto por defecto** | Cambiar el predeterminado a `EXACTA_POR_PERIODO` en todo el sistema. | Respuesta 3 del Sprint 118 | 2-3 días + revisión de liquidaciones emitidas |
| **No tomar nunca tal cual** | `engine.py`, `motor_universal.py`, `pdf.py`, `CHANGELOG.md`, `README.md`, `MAPA_DOCUMENTACION.md`, `01_motor_temporal.md`, `Preguntas-…-Abiertas.md`, `ARQUITECTURA_ADR.md` del ZIP. Los textos nuevos útiles se copian a mano. | — | — |

**Riesgos principales**
1. Cifras distintas entre escritorio y gestor/API para el mismo caso (redondeo, parámetros, alcance) → un
   abogado podría presentar dos liquidaciones diferentes del mismo crédito.
2. Plazos del gestor con un calendario que ya sabemos incompleto (Chiquinquirá) y con la vacancia que el
   despacho no aprobó → riesgo de vencimientos mal calculados.
3. Dos programas, dos bases de datos y dos fuentes de parámetros que mantener; el equipo es pequeño.
4. Nada del gestor se probó en Windows ni con el portal real de la Rama Judicial; el empaquetado nunca se
   ejecutó.
5. Datos de clientes reales sin cifrado ni control de usuarios.
6. El "sello" puede malinterpretarse como firma con valor probatorio.

---

## 6. Preguntas abiertas

### Para el despacho (solo jurídicas; no repetir las 6 del Sprint 118 que ya están en `main`)

Las preguntas 1 (vacancia 10/11 de enero), 3 (redondeo), 4 (pagos anticipados), 5 (notificación) y 6
(vacancia por despacho) del Sprint 118 **ya cubren** las 5 del "Sprint 117-B" del aporte y los puntos 1-3
de su lista del gestor. Solo son nuevas, y solo si el equipo decide adoptar el gestor:

1. **Plazos en días calendario que vencen en día inhábil:** ¿en qué casos se corren al siguiente día
   hábil? (Hoy el gestor no los corre; solo advierte.)
2. **Perfil de calendario por tipo de asunto:** ¿trámites administrativos, conciliaciones, arbitraje,
   disciplinarios y consultas cuentan solo sábados, domingos y festivos, sin vacancia judicial? ¿Cómo tratar
   el nuevo Código Procesal del Trabajo (Ley 2452 de 2025): fecha de vigencia y transición?
3. **Etapas de cada tipo de asunto** (`bastium/dominio/estados.py`): ¿qué etapa sobra, falta o está mal
   nombrada?
4. **Listas de verificación de escritos** (memorial, poder, derecho de petición, demanda, liquidación del
   crédito): ¿qué requisito debe bloquear y cuál solo advertir? (p. ej. juramento estimatorio y cuantía).
5. **Texto de autorización de tratamiento de datos** definitivo, canales (¿WhatsApp?) y tiempo de
   conservación.
6. **Conflicto de interés:** ¿quién puede autorizar continuar (¿solo un socio?) y hace falta "muro ético"?
7. **Consulta automática a la Rama Judicial:** ¿se acepta consultar cada 24 h por proceso identificándose
   con el correo del abogado?
8. **Umbrales del semáforo de términos** (10/5/3/1 días hábiles): ¿se ajustan?

### Para el equipo

1. **Decisión #7 (¿capa API?):** ¿se adopta `bastium_api` ahora, con qué redondeo por defecto y con qué
   fuente de parámetros (JSON propio o la tabla `ParametroLegal`)?
2. **¿Gestor dentro del repositorio (Python/Starlette, `bastium/`) o externo (Laravel/Vue + n8n)?** Los
   documentos del aporte dicen las dos cosas. Condiciona la visión SaaS.
3. ¿Aceptamos un segundo programa con su propia base de datos (SQLite sin ORM) junto al escritorio
   (SQLAlchemy)? ¿Quién lo mantiene?
4. ¿Se arregla primero en `main` la dependencia del motor con SQLAlchemy/`holidays` (fase 1)?
5. ¿El "sello" SHA-256 basta, o se necesita firma digital real antes de llamarlo "sellado" ante un juez?
6. Decisión #39 (NotebookLM): el aporte propone un puente **manual** (paquete de fuentes y notas ancladas),
   sin API ni envío automático de datos. ¿Se acepta ese alcance?
7. Pedir al autor: rebasar sobre el `main` actual (no sobre el del 17/11), quitar las modificaciones a
   archivos existentes y entregar los paquetes nuevos en PRs separados (radicado, API, gestor).
