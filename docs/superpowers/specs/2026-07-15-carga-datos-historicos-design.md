# Diseño — Sprint 5: Carga de datos históricos (IPC, SMLMV, IBC, Tasa de Usura)

**Fecha:** 2026-07-15
**Origen:** `Pendientes.md`, sección "Sprint 5 — Carga de datos históricos (IPC, SMLMV, IBC, Tasa de
Usura, UVT)".
**Estado:** Aprobado por el usuario, listo para plan de implementación.

## Contexto

`app/engine/indexation/historical_index.py` existe pero está vacío (0 bytes). Es la dependencia común
de los Sprints 2 (ya implementado, usa un IBC manual por ahora), 3, 4 y 8. Este sprint construye las
series históricas reales — transcritas y verificadas contra
`REQUERIMIENTOS DE CALCULO Y REGLAS LOGICAS - BASTIUM.pdf` — y expone tres funciones de consulta. No
conecta estas series a ningún motor de liquidación todavía (esa conexión, para IPC, es el Sprint 8;
para IBC automático en Comercial, un sprint futuro no asignado).

## Decisiones tomadas con el usuario

1. **Almacenamiento: constantes Python**, no tabla SQLite. Simple, versionado en git, sin tocar el
   esquema de base de datos. Coherente con que BASTIUM es una app de escritorio de un solo usuario sin
   backend.
2. **Línea de crédito para IBC/Usura: "Consumo y Ordinario"** (sucesora de "Comercial" desde 2007). Es
   la línea general que un juez usaría para una obligación sin clasificación específica de microcrédito
   o crédito rural. Microcrédito y Crédito Popular Productivo Rural quedan fuera de alcance, documentados
   como pendiente explícito, no como omisión.
3. **UVT: omitida este sprint.** El PDF no trae una tabla histórica completa (solo menciones dispersas,
   confirmado por búsqueda de texto completo en las 80 páginas). Se documenta en `Pendientes.md` como
   bloqueante parcial del Sprint 4 hasta conseguir la fuente real.

## Hallazgo relevante durante la verificación (no estaba en el alcance original tal como se describió)

`Pendientes.md` advertía "ojo con los tramos que cambian de columna a partir de 2007" pero subestimaba
la complejidad real: desde 2007 la Superintendencia Financiera certifica **varias líneas de crédito en
paralelo** (Comercial → "Consumo y Ordinario", Microcrédito, y desde ~2023 "Crédito Popular Productivo
Rural"), con rangos de fecha que se solapan entre líneas distintas. La extracción de texto lineal
(usada para leer las demás secciones del PDF) mezcla las columnas de estas tablas de forma ambigua y
es **inapropiada** para esta tabla específica — se verificó visualmente contra las páginas renderizadas
del PDF y se re-extrajo con reconocimiento de grilla (`page.find_tables()` de PyMuPDF, que respeta las
líneas reales de la tabla) para evitar errores de transcripción en una cifra que alimenta cálculos
jurídicos reales.

Con la línea "Consumo y Ordinario" aislada correctamente, la serie resultante (263 tramos, 1997-07-01 a
2026-07-31) no tiene ningún vacío de fechas, y tiene **un solo solape real en la fuente misma**:
septiembre de 2017 aparece tanto en un tramo trimestral (`2017-07-01` a `2017-09-30`, IBC 21.98%) como
en un tramo mensual nuevo (`2017-09-01` a `2017-09-30`, IBC 21.48%) — la SFC transicionó de
certificación trimestral a mensual ese mes. Se resuelve truncando el tramo trimestral a
`2017-07-01`–`2017-08-31` y dejando el tramo mensual de septiembre como la fuente autoritativa para ese
mes (el dato más específico/reciente prevalece). Esto se documenta como comentario inline en el dato,
no silenciosamente.

## Estructura de datos

`app/engine/indexation/historical_index.py`, tres estructuras:

### 1. SMLMV

```python
_SMLMV_POR_ANIO: Dict[int, Decimal]  # 1984-2026, transcripción directa. 2027 excluido ("Por definir" en el PDF).

def get_smlmv_for_year(anio: int) -> Decimal:
    """Lanza ValueError si el año no está en 1984-2026."""
```

### 2. IPC

Dos estructuras: la variación porcentual anual cruda (tal como aparece en el PDF, para trazabilidad) y
el índice acumulado derivado (lo que consume `IPCIndexation.calculate`, que espera un índice, no un
porcentaje).

```python
_IPC_VARIACION_ANUAL: Dict[int, Decimal]  # 1967-2025, transcripción directa del PDF (% de variación anual).
_IPC_INDICE_ACUMULADO: Dict[int, Decimal]  # derivado en tiempo de import, ver fórmula abajo.

def get_ipc_for_date(fecha: date) -> Decimal:
    """Retorna el índice acumulado de cierre de año (31-dic) del año de `fecha`.
    Lanza ValueError si el año no está en 1967-2025."""
```

**Fórmula de derivación** (ejecutada una vez al importar el módulo, no en cada llamada):
`índice[año] = índice[año-1] × (1 + variación[año]/100)`, con índice base `100` anclado antes de 1967
(es decir, `índice[1966] = 100`, implícito, no se almacena). La elección del valor base no afecta el
resultado de `IPCIndexation.calculate()` porque esa fórmula solo usa la razón `final/inicial` — cualquier
base consistente da el mismo resultado. Se usa precisión `Decimal` alta (sin redondear los índices
intermedios) para no acumular error de redondeo a través de 58 años de multiplicación encadenada; el
redondeo a centavos ya ocurre en `Rounding.money()` dentro de `IPCIndexation.calculate()`, no aquí.

**Convención de fecha:** cada índice representa el cierre de año (31 de diciembre). No hay granularidad
mensual en la fuente (el PDF solo trae variación *anual*). La interpolación a un mes específico dentro
del año es responsabilidad del Sprint 8 (que ya tiene ese alcance descrito: "Interpolación cuando
`fecha_corte` no coincide con el cierre de un mes certificado").

### 3. IBC / Tasa de Usura

```python
@dataclass(frozen=True)
class TramoIBCUsura:
    inicio: date
    fin: date
    ibc_anual: Decimal      # % efectivo anual, tal como lo certifica la SFC
    usura_anual: Decimal    # % efectivo anual = 1.5 × ibc_anual (viene ya calculado en el PDF)

_TRAMOS_IBC_USURA: List[TramoIBCUsura]  # 263 tramos, 1997-07-01 a 2026-07-31, línea "Consumo y Ordinario"
                                          # (llamada "Comercial" antes del 5-ene-2007). Sin vacíos ni solapes.

def get_ibc_usura_for_date(fecha: date) -> Tuple[Decimal, Decimal]:
    """Retorna (ibc_anual, usura_anual) para la fecha dada.
    Lanza ValueError si la fecha cae fuera de 1997-07-01 a 2026-07-31."""
```

Nota: `usura_anual` en la fuente siempre es exactamente `1.5 × ibc_anual` (confirmado en las 263 filas
transcritas) — se almacena el valor tal como aparece en el PDF en vez de recalcularlo, para que el dato
crudo siga siendo auditable contra la fuente sin depender de que el multiplicador legal (`1.5`) nunca
cambie.

## Fuera de alcance (explícito)

- UVT histórica (sin fuente completa en el PDF — pendiente).
- Líneas de crédito Microcrédito y Popular Productivo Rural (solo se modela "Consumo y Ordinario").
- Conexión de estas series a `CivilFamiliaStrategy`, `ComercialStrategy`, o `IPCIndexation` en tiempo de
  liquidación — eso es Sprint 8 (IPC) y un sprint futuro no asignado (IBC automático en Comercial,
  reemplazando el campo manual `ibc_vigente_anual` que el usuario diligencia hoy).
- Automatización de actualización mensual/anual vía scraping o API (DANE/SFC/Banco de la República).

## Testing

- Valores puntuales conocidos citados explícitamente en `Pendientes.md`: SMLMV 2026 = $1.750.905, IPC
  2025 (variación cruda) = 5.10%.
- `get_smlmv_for_year`/`get_ipc_for_date`/`get_ibc_usura_for_date` fuera de rango → `ValueError` con
  mensaje claro.
- Tramo de IBC/Usura en el límite del solape de septiembre de 2017: `2017-08-31` debe devolver el tramo
  trimestral (21.98%), `2017-09-01` debe devolver el tramo mensual (21.48%).
- Continuidad: test que recorre todos los `_TRAMOS_IBC_USURA` y confirma que no hay vacíos ni solapes
  (guarda contra una futura edición manual de los datos que rompa la propiedad ya verificada).
- `_IPC_INDICE_ACUMULADO` es estrictamente creciente año a año (la inflación en Colombia nunca fue
  negativa en esta serie — sirve de guarda de sanidad contra un error de transcripción en la variación
  cruda).

## Definición de hecho

- `historical_index.py` deja de estar vacío, con datos verificables contra el PDF (páginas 55-62).
- Las tres funciones de consulta (`get_smlmv_for_year`, `get_ipc_for_date`, `get_ibc_usura_for_date`)
  existen, están probadas, y lanzan errores claros fuera de rango.
- `Pendientes.md` documenta la UVT como pendiente explícito y anota que Sprint 5 quedó completo para
  SMLMV/IPC/IBC-Usura.
- Suite completa en verde.
