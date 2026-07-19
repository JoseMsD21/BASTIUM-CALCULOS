# BASTIUM — Ecosistema de Liquidación Forense

BASTIUM es una aplicación de escritorio para abogados y despachos jurídicos en Colombia. Permite
registrar un expediente, cargar las obligaciones (deudas) y los abonos (pagos) asociados, y calcular
automáticamente la liquidación — capital, intereses y saldo final — con el mismo rigor matemático y
legal que se usaría en un juzgado.

**¿Nuevo en el proyecto? Empieza por la [Guía de Usuario](docs/GUIA_USUARIO.md)** — está escrita paso a
paso, sin dar nada por sabido: qué instalar, cómo abrir el programa, cómo usar cada pantalla, y dónde
están los valores legales (como la tasa de interés) por si necesitas consultarlos o ajustarlos.

## Estado actual (2026-07-19)

✅ **Funcional hoy:** captura manual de expedientes y liquidación real de las áreas **Civil / Familia**
(interés del Art. 1617 del Código Civil, 6% anual, sobre obligaciones puntuales y recurrentes, con
abonos), **Comercial** (Art. 884 C.Co., tasas remuneratoria y moratoria pactadas por obligación con
split real antes/después del vencimiento, validación de tope de usura 1.5×IBC), **Sancionatorio**
(multas SIC/Penal/Ambiental/Urbano en SMLMV o UVT, Ley 1955/2019 art. 49 — solo cubre hechos anteriores
a 2020-01-01, porque todavía no hay tabla histórica de UVT cargada; hechos posteriores avisan "UVT no
disponible" en vez de arriesgar un valor incorrecto) y **Honorarios / Litigio** (cobro de honorarios
profesionales y cuota litis, validando simultáneamente el tope del 30% del beneficio obtenido para la
cuota litis sola y el tope del 50% para la suma de honorarios fijos + cuota litis; las costas judiciales
se ingresan como un porcentaje manual, porque no existe una tabla estructurada confiable de los rangos
del Consejo Superior de la Judicatura). El resultado de cualquier liquidación se puede exportar a **PDF**
y a **Word** desde la pantalla de Resultado de Liquidación.

🚧 **En desarrollo:** el área Laboral está registrada en el sistema pero todavía no calcula (el programa
avisa "Área no implementada" si se intenta usar). Indexación por IPC, prescripción/caducidad, anatocismo
comercial condicionado (Art. 886 C.Co.) y varios módulos más también están pendientes. Las series
históricas de SMLMV, IPC e IBC/Tasa de Usura (1984-2026, 1967-2025 y 1997-2026 respectivamente) ya están
cargadas en `app/engine/indexation/historical_index.py`, aunque todavía no están conectadas a todos los
cálculos que las necesitan (ej. IPC, y la tabla de UVT histórica) — esa conexión es trabajo de otros
sprints. El plan completo, sprint por sprint, está en
**[Pendientes.md](Pendientes.md)**.

## Instalación rápida

```
pip install -r requirements.txt
python main.py
```

Para el paso a paso completo (incluyendo un problema conocido de Windows con rutas largas y cómo
resolverlo), ver la [Guía de Usuario](docs/GUIA_USUARIO.md#2-instalación-paso-a-paso).

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
