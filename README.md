# BASTIUM — Ecosistema de Liquidación Forense

BASTIUM es una aplicación de escritorio para abogados y despachos jurídicos en Colombia. Permite
registrar un expediente, cargar las obligaciones (deudas) y los abonos (pagos) asociados, y calcular
automáticamente la liquidación — capital, intereses y saldo final — con el mismo rigor matemático y
legal que se usaría en un juzgado.

**¿Nuevo en el proyecto? Empieza por la [Guía de Usuario](docs/GUIA_USUARIO.md)** — está escrita paso a
paso, sin dar nada por sabido: qué instalar, cómo abrir el programa, cómo usar cada pantalla, y dónde
están los valores legales (como la tasa de interés) por si necesitas consultarlos o ajustarlos.

## Estado actual (2026-07-15)

✅ **Funcional hoy:** captura manual de expedientes y liquidación real del área **Civil / Familia**
(interés del Art. 1617 del Código Civil, 6% anual, sobre obligaciones puntuales y recurrentes, con
abonos).

🚧 **En desarrollo:** las áreas Comercial, Laboral, Sancionatorio y Honorarios están registradas en el
sistema pero todavía no calculan (el programa avisa "Área no implementada" si se intentan usar).
Indexación por IPC, exportación a PDF/Word, prescripción/caducidad y varios módulos más también están
pendientes. El plan completo, sprint por sprint, está en **[Pendientes.md](Pendientes.md)**.

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
