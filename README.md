# BASTIUM — Ecosistema de Liquidación Forense

BASTIUM es una aplicación de escritorio para abogados y despachos jurídicos en Colombia. Permite
registrar un expediente, cargar las obligaciones (deudas) y los abonos (pagos) asociados, y calcular
automáticamente la liquidación — capital, intereses y saldo final — con el mismo rigor matemático y
legal que se usaría en un juzgado.

**¿Nuevo en el proyecto? Empieza por la [Guía de Usuario](docs/GUIA_USUARIO.md)** — está escrita paso a
paso, sin dar nada por sabido: qué instalar, cómo abrir el programa, cómo usar cada pantalla, y dónde
están los valores legales (como la tasa de interés) por si necesitas consultarlos o ajustarlos.

## Estado actual (2026-07-21)

✅ **Funcional hoy:** captura manual de expedientes y liquidación real de las áreas **Civil / Familia**
(interés del Art. 1617 del Código Civil, 6% anual, sobre obligaciones puntuales y recurrentes, con
abonos, indexación IPC opcional por obligación (Art. corrección monetaria; el abogado marca caso por caso si
aplica, con interpolación entre índices de cierre de año para fechas intermedias)), **Comercial** (Art. 884 C.Co., tasas remuneratoria y moratoria pactadas por obligación con
split real antes/después del vencimiento, validación de tope de usura 1.5×IBC, y obligaciones en USD
convertidas a pesos con la TRM ingresada por el abogado, Art. 874 C.Co.), **Sancionatorio**
(multas SIC/Penal/Ambiental/Urbano en SMLMV o UVT, Ley 1955/2019 art. 49, con la base convertida a pesos
según la fecha del hecho: SMLMV antes del 2020-01-01, UVT desde esa fecha, con tabla histórica de UVT
2006-2026 cargada), **Honorarios / Litigio** (cobro de honorarios
profesionales y cuota litis, validando simultáneamente el tope del 30% del beneficio obtenido para la
cuota litis sola y el tope del 50% para la suma de honorarios fijos + cuota litis; las costas judiciales
se ingresan como un porcentaje manual, porque no existe una tabla estructurada confiable de los rangos
del Consejo Superior de la Judicatura) y **Laboral** (liquidación final —finiquito— de un contrato:
cesantías, intereses a cesantías, prima de junio y diciembre, vacaciones, e indemnización moratoria
bifásica del Art. 65 CST si hubo retardo en el pago). El resultado de cualquier liquidación se puede
exportar a **PDF** y a **Word** desde la pantalla de Resultado de Liquidación. Cada liquidación ejecutada
queda registrada en un historial de auditoría por expediente (quién, cuándo, con qué área y fecha de
corte), con reconstrucción exacta de un cálculo pasado con solo hacer doble clic sobre su fila.

✅ **Parámetros legales versionados:** desde la pantalla "⚙ Parámetros" cualquier abogado puede consultar
y agregar, sin tocar código, los valores/tasas/topes que antes solo un desarrollador podía cambiar: el
multiplicador de usura, los topes de cuota litis, los plazos de prescripción/caducidad, el descuento del
interés moratorio tributario (E.T. art. 635), la tasa civil legal, y las series históricas de SMLMV, IPC
e IBC/Tasa de Usura. Cada valor queda con su fecha de vigencia, quién lo agregó y por qué — nunca se edita
ni se borra una fila, solo se agregan valores nuevos, así que el historial completo de cada parámetro
queda siempre disponible con doble clic.

🚧 **En desarrollo:** seguridad social (cotizaciones a pensión, salud, ARL, fondo de solidaridad
pensional) en el área Laboral, anatocismo comercial condicionado (Art. 886 C.Co.) y varios módulos más
también están pendientes. El motor de prescripción y caducidad
(`app/engine/temporal/prescripcion.py`) ya existe y está probado — calcula fechas límite por tipo de
acción (ejecutiva, ordinaria, honorarios profesionales, cambiaria directa/de regreso), soporta
prescripción parcial cuota a cuota en obligaciones de tracto sucesivo e interrupción por demanda — pero
todavía no está conectado a ninguna pantalla ni al motor de liquidación (`Pendientes.md`, Sprint 7). Dos
motores de cálculo tributario también existen y están probados sin estar conectados a ninguna
pantalla: interés moratorio tributario (`app/engine/tax/moratory_interest.py`, E.T. art. 635, usura
vigente menos dos puntos, resuelto por tramos históricos) y depuración de Renta Líquida Gravable
(`app/engine/tax/renta_liquida.py`, pipeline de 8 pasos) (`Pendientes.md`, Sprint 11). Las
series históricas de SMLMV, IPC, IBC/Tasa de Usura y UVT (1984-2026, 1967-2025, 1997-2026 y 2006-2026
respectivamente) ya están cargadas en `app/engine/indexation/historical_index.py` — IBC/Usura se usa en
Comercial y en la fase 2 de la indemnización moratoria laboral, IPC ya está conectado a la indexación de
Civil/Familia (Sprint 8), y UVT ya está conectada a la conversión SMLMV→UVT del área Sancionatorio
(Sprint 14); SMLMV sigue sin un consumidor propio. El plan completo, sprint por sprint, está en
**[Pendientes.md](Pendientes.md)**.

## Instalación rápida

```
pip install -r requirements.txt
python main.py
```

Para el paso a paso completo (incluyendo un problema conocido de Windows con rutas largas y cómo
resolverlo), ver la [Guía de Usuario](docs/GUIA_USUARIO.md#2-instalación-paso-a-paso).

**Si ya tenías `bastium.db` creado antes del Sprint 8**, corre una vez
`python scripts/migrate_aplica_indexacion_ipc.py` antes de abrir la app — agrega la columna
`aplica_indexacion_ipc` que la indexación IPC necesita. `init_db()` (creación de tablas nuevas) no
altera tablas existentes, así que sin este paso la app falla al leer o guardar cualquier obligación. El
script es idempotente (se puede correr de más sin riesgo) y solo hace falta una vez por instalación.

**Si ya tenías `bastium.db` creado antes del Sprint 12**, corre una vez
`python scripts/migrate_moneda_trm.py` antes de abrir la app — agrega las columnas `moneda`,
`trm_aplicable` y `trm_fecha_referencia` que necesitan las obligaciones comerciales en moneda extranjera.
Igual que el script del Sprint 8, es idempotente y solo hace falta una vez por instalación.

**Si ya tenías `bastium.db` creado antes de este sprint**, corre una vez
`python scripts/migrate_parametros_legales.py` antes de abrir la app — crea y siembra la tabla
`parametros_legales` con los valores hoy vigentes (usura, cuota litis, prescripción/caducidad, SMLMV,
IPC, IBC/usura), para que la pantalla "⚙ Parámetros" y todos los motores que ahora la consultan tengan
datos desde el primer arranque. Es idempotente y solo hace falta una vez por instalación.

## Estructura del proyecto

```
app/                    Código fuente (motor de cálculo, GUI, servicios)
  engine/                Motores matemáticos (interés, indexación, tiempo, liquidación)
  services/              Estrategias de liquidación por área del derecho
  views/                 Pantallas de la interfaz (PySide6)
  core/                  Constantes y excepciones compartidas
database/               Modelos y acceso a la base de datos (SQLite)
tests/                  Suite de pruebas automatizadas (pytest)
docs/
  GUIA_USUARIO.md         Guía de uso completa, para cualquier persona
  superpowers/specs/      Documento de diseño del MVP
  superpowers/plans/      Plan de implementación tarea por tarea (histórico)
specifications/         Documentación técnica de cada motor interno
Pendientes.md            Backlog de trabajo futuro, organizado en sprints
REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf
                          Documento maestro de requisitos jurídicos (alcance completo del producto)
```

## Ejecutar las pruebas

```
python -m pytest -q
```

## Mantenimiento de esta documentación

Cada vez que se completa un sprint de `Pendientes.md` y un módulo pasa de "🚧 en desarrollo" a
funcional, este README y la [Guía de Usuario](docs/GUIA_USUARIO.md) deben actualizarse para reflejarlo.
No deben quedar desactualizados respecto al código real.
