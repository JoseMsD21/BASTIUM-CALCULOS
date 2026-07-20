# Diseño — Sprint 8: Conectar indexación IPC al área Civil/Familia

**Fecha:** 2026-07-19
**Origen:** `Pendientes.md`, sección "Sprint 8 — Conectar indexación IPC al área Civil/Familia".
**Estado:** Aprobado por el usuario, listo para plan de implementación.

## Contexto

`IPCIndexation.calculate(capital, initial_index, final_index)` (`app/engine/indexation/ipc.py`) ya
está implementado y probado: `Va = Vh × (IPC_final / IPC_inicial)`. `historical_index.py` (Sprint 5) ya
expone `get_ipc_for_date(fecha) -> Decimal` con el índice IPC acumulado de **cierre de año** (1967-2025).
Ninguno de los dos está conectado a `CivilFamiliaStrategy` todavía.

Hallazgo relevante durante el diseño: `LiquidationCore` (`app/engine/liquidation/engine.py`) **ya sabe
procesar un `event_type="INDEXATION"`** de forma genérica — lo suma a `PendingDebt.indexation` vía
`BalanceEngine.add_indexation`, y `AllocationEngine.allocate()` ya lo imputa en primer lugar (antes que
intereses, antes que capital). Esta infraestructura quedó construida en un sprint anterior pero **sin
ningún caller que la use** (`grep` de `INDEXATION` en `tests/` no arroja resultados). Este sprint no
necesita tocar el motor core — solo generar los eventos `INDEXATION` desde `CivilFamiliaStrategy`.

## Decisiones tomadas con el usuario

1. **Opt-in por obligación, no por área.** Nueva columna `Obligacion.aplica_indexacion_ipc: bool`
   (default `False`), con checkbox en `ObligacionFormDialog` (solo visible para Civil/Familia). El
   abogado decide caso por caso si la indexación aplica — es un juicio legal, no una regla técnica fija
   por categoría. El flag de área existente (`AreaStrategy.soporta_indexacion_ipc`) sigue siendo el
   gate de primer nivel (ya es `False` para Comercial/Laboral/Sancionatorio/Honorarios); el nuevo campo
   es el gate de segundo nivel, por obligación, solo relevante cuando el área ya lo soporta.

2. **Interpolación lineal entre índices de cierre de año.** La fuente del PDF (págs. 20-22) describe
   interpolación entre el IPC de un mes certificado y el siguiente (`Vo = (t1×V2 + t2×V1)/(t1+t2)`), pero
   `historical_index.py` (Sprint 5) **nunca tuvo datos mensuales** — el PDF fuente solo trae variación
   *anual* del IPC (pág. 62), no un desglose mes a mes del DANE. Se aplica la misma fórmula de
   interpolación, pero entre los dos índices de 31-dic que rodean la fecha (la granularidad real
   disponible), documentado explícitamente como aproximación — no es el IPC mensual exacto que
   certificaría el DANE.

3. **Fallback a 2025 para fechas ≥ 2026.** La serie de IPC no tiene el año 2026 (el PDF fuente no lo
   trae). Dado que la fecha actual del sistema ya es 2026-07-19, bloquear liquidaciones con indexación
   activada y `fecha_corte` en 2026+ haría el sprint inútil en la práctica. Se usa el índice de 2025
   (el último cerrado) como aproximación para cualquier fecha ≥ 2026-01-01, documentado como limitación
   explícita (subestima levemente la indexación real de 2026 en adelante).

4. **Regla "no doble indexación": documentada, no codificada como guard.** El PDF (pág. 20, "Cuándo no
   procede") solo excluye dos casos: (a) indexación + intereses comerciales — ya resuelto vía
   `ComercialStrategy.soporta_indexacion_ipc = False`; (b) créditos ya reajustados vía SMMLV — pero
   ningún campo de `Obligacion` usado por Civil/Familia representa "valor ya expresado en una unidad
   actualizada" (`cantidad_smlmv_uvt` es exclusivo de `Sancionatorio`, que ya tiene la indexación
   deshabilitada). La combinación que la regla prohíbe **no es alcanzable** con el modelo de datos actual
   de Civil/Familia, así que no hay nada que un guard en tiempo de ejecución pudiera atrapar. Se
   documenta esto explícitamente en el docstring de `CivilFamiliaStrategy` en vez de escribir código
   muerto.

5. **Migración manual de esquema (no recrear la BD).** `bastium.db` tiene 1 expediente / 1 obligación /
   1 abono existentes. Se agrega la columna con `ALTER TABLE obligaciones ADD COLUMN
   aplica_indexacion_ipc BOOLEAN NOT NULL DEFAULT 0` vía un script en `scripts/`, ejecutado una vez,
   preservando la fila existente (que queda con el valor default `False`, comportamiento idéntico al
   actual).

## Componentes técnicos

### 1. `database/models.py`

```python
class Obligacion(Base):
    ...
    aplica_indexacion_ipc: Mapped[bool] = mapped_column(Boolean, default=False)
```

### 2. `scripts/migrate_aplica_indexacion_ipc.py` (nuevo, ejecución única)

Script idempotente: verifica con `PRAGMA table_info(obligaciones)` si la columna ya existe antes de
correr el `ALTER TABLE`, para poder ejecutarse más de una vez sin error (ej. en CI o en la máquina de
otro desarrollador que aún no tiene la columna).

### 3. `app/engine/indexation/historical_index.py`

Nueva función, además de las tres que ya existen:

```python
def get_ipc_interpolado_for_date(fecha: date) -> Decimal:
    """Retorna el indice IPC interpolado linealmente para una fecha cualquiera,
    usando los dos indices de cierre de año (31-dic) que la rodean. Si `fecha.year`
    es posterior al ultimo año disponible en la serie, retorna el indice del ultimo
    año como aproximacion (ver Sprint 8 design doc, decision 3)."""
```

Lógica:
- `anio_max = max(_IPC_INDICE_ACUMULADO)` (2025 hoy). Si `fecha.year > anio_max`: retorna
  `_IPC_INDICE_ACUMULADO[anio_max]` directo (sin interpolar).
- En otro caso: `v1 = índice[fecha.year - 1]` (o `Decimal("100")` si `fecha.year - 1 < 1967`, el ancla
  implícita), `v2 = índice[fecha.year]`. `t1 = (fecha - date(fecha.year - 1, 12, 31)).days`,
  `t2 = (date(fecha.year, 12, 31) - fecha).days`. `Vo = (t1×v2 + t2×v1) / (t1 + t2)`. Si `t1 + t2 == 0`
  (fecha es exactamente 31-dic), retorna `v2` directo.
- Si `fecha.year < 1967`: propaga el mismo `ValueError` de rango que ya usa `get_ipc_for_date`.

### 4. `app/services/area_strategy.py` → `CivilFamiliaStrategy`

- `_eventos_de_obligacion` pasa a generar, además de los eventos de capital existentes, los eventos de
  indexación correspondientes cuando `obligacion.aplica_indexacion_ipc` es `True`:
  - **PUNTUAL**: un evento `INDEXATION` en la misma fecha que el evento de capital
    (`obligacion.fecha_origen`), con `amount = IPCIndexation.calculate(capital=obligacion.valor,
    initial_index=get_ipc_interpolado_for_date(obligacion.fecha_origen),
    final_index=get_ipc_interpolado_for_date(fecha_corte))`.
  - **RECURRENTE**: un evento `INDEXATION` por cada cuota generada por `FamilyScheduler` (tracto
    sucesivo — PDF pág. 20: "la operación debe realizarse mes a mes"), fechado igual que la cuota, con
    `initial_index` resuelto en la fecha de esa cuota específica (no en `fecha_inicio` de la obligación).
- `payload["label"]` del evento de indexación: `f"Indexación IPC — {concepto}"`, para que quede
  distinguible en `LiquidationItem.concept` frente al evento de capital que lo origina.
- Si `IPCIndexation.calculate()` retorna `Decimal("0.00")` (deflación, ver `ipc.py` línea 21-22), el
  evento se emite igual con `amount=0` — no se omite, para mantener trazabilidad completa de que la
  indexación se evaluó y dio cero, no que se saltó.

### 5. GUI — `app/views/obligaciones.py` (`ObligacionFormDialog`)

- Nuevo checkbox "Aplica indexación IPC (Art. corrección monetaria)", visible solo cuando el área del
  expediente es Civil/Familia (mismo patrón condicional que ya usan los campos específicos de
  Comercial/Sancionatorio/Honorarios).
- `guardar()` mapea el checkbox a `aplica_indexacion_ipc` en el objeto `Obligacion`.

## Fuera de alcance (explícito)

- Cambiar cómo `DailyInterest`/`LiquidationCore` calculan intereses para que corran sobre
  `principal + indexación` en vez de solo `principal` (el algoritmo "Suma Única" del PDF pág. 22 pide
  interés sobre el valor ya indexado). Es un cambio en el motor core que afecta las 5 áreas, no algo que
  "conectar indexación a Civil/Familia" implique. Se documenta como limitación conocida heredada.
- Indexación para áreas distintas a Civil/Familia (ya excluidas a nivel de área).
- IPC mensual real (requeriría una fuente de datos distinta a la ya transcrita en Sprint 5).
- UVR, UVT, TRM (otros índices mencionados en la misma sección del PDF, fuera del alcance de este
  sprint — IPC es el único índice que Civil/Familia usa).

## Testing

- `get_ipc_interpolado_for_date`: valor exacto en un 31-dic (debe igualar `get_ipc_for_date`), valor en
  un punto medio del año (verificado contra cálculo manual de la fórmula), fallback para una fecha en
  2026 (debe igualar el índice de 2025), `ValueError` para una fecha anterior a 1967.
- `CivilFamiliaStrategy`: obligación PUNTUAL con `aplica_indexacion_ipc=True` vs `False` (mismo capital,
  resultado distinto), obligación RECURRENTE con indexación activada verificando que cada cuota indexa
  desde su propia fecha (no todas desde `fecha_inicio`), caso de deflación (evento con `amount=0`
  presente en el historial), verificación numérica contra un cálculo manual con la fórmula del PDF.
- Migración: test que corre el script dos veces sobre una base de datos temporal y confirma que no
  falla la segunda vez (idempotencia) y que la columna queda con default `False`.
- Suite completa (hoy en verde) sigue pasando.

## Definición de hecho

- `CivilFamiliaStrategy` genera eventos `INDEXATION` reales cuando la obligación lo tiene activado, con
  el monto calculado por `IPCIndexation` usando los índices resueltos por `get_ipc_interpolado_for_date`.
- Checkbox operable end-to-end desde la GUI (smoke test manual).
- `bastium.db` migrado con la columna nueva sin perder la fila existente.
- `README.md` y `docs/GUIA_USUARIO.md` actualizados (regla obligatoria de `Pendientes.md` al cerrar
  cualquier sprint).
- Suite completa en verde.
