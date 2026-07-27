# Diseño — Sprint 19: Anatocismo comercial condicionado (Art. 886 C.Co.)

**Fecha:** 2026-07-26
**Origen:** `Pendientes.md`, sección "Sprint 19 — Anatocismo comercial condicionado (Art. 886 C.Co.)".
**Estado:** Aprobado por el usuario, listo para plan de implementación.

## Contexto

El PDF de requerimientos (pág. 45, 10, 52-53) exige que el anatocismo (interés sobre interés) en el área
Comercial solo se active si: 1) hay demanda judicial, o 2) hay acuerdo posterior al vencimiento, siempre que
los intereses debidos lleven al menos un año de anterioridad. El default siempre debe seguir siendo interés
simple. El motor `CompoundInterest.calculate(capital, period_rate, periods)`
(`app/engine/interest/compound_interest.py`) ya existe, probado, huérfano desde antes del MVP — el Pendientes
original suponía que este sprint era "100% wiring" de esa función.

## Decisión de arquitectura (cambio respecto al Pendientes original)

Durante el diseño se identificó que un cálculo cerrado de una sola pasada
(`CompoundInterest.calculate()` aplicado a todo el tramo de mora capitalizable de una vez) no puede manejar
con precisión un abono que caiga a mitad de ese tramo: el monto compuesto ya estaría fijado antes de que el
abono se aplicara. El usuario decidió explícitamente priorizar el manejo correcto de abonos intermedios
sobre el uso literal de `CompoundInterest.calculate()`.

**Solución adoptada:** el motor sigue acumulando interés simple día a día (mecanismo ya existente y
probado, que ya maneja abonos correctamente vía `AllocationEngine`), y se insertan **eventos de
capitalización periódica** que trasladan el interés ya devengado al capital cada aniversario desde la fecha
de capitalización. Repetir esto anualmente reproduce el efecto de interés compuesto exacto, con abonos
intermedios resueltos automáticamente porque siguen pasando por la maquinaria existente.

**Consecuencia:** `CompoundInterest.calculate()` deja de usarse en este sprint. No se borra el archivo (no
es parte del pedido); queda documentado aquí que sigue huérfano y por qué. Esto es la única desviación
respecto al texto original de `Pendientes.md`, y se documentará también al cerrar el sprint.

## Modelo de datos (`database/models.py`)

- `Obligacion.anatocismo_demanda_judicial: bool` (`Boolean`, default `False`).
- `Obligacion.anatocismo_fecha_acuerdo: date | None` (`Date`, nullable).
- Migración nueva `scripts/migrate_anatocismo_comercial.py`, mismo patrón idempotente (`PRAGMA
  table_info`, sin Alembic) que `scripts/migrate_aplica_indexacion_ipc.py` (Sprint 8) y
  `scripts/migrate_moneda_trm.py` (Sprint 12).
- Si ambos campos están en su default (`False`/`None`), el comportamiento es exactamente el actual: interés
  simple, sin ningún evento de capitalización.

## Validación (`ComercialStrategy._validar_obligacion_comercial`)

Reglas nuevas, aplicadas solo cuando algún campo de anatocismo está activo:

1. **Solo `tipo == PUNTUAL`.** `RECURRENTE` no modela vencimiento por cuota individual (ver docstring
   existente de `ComercialStrategy`), así que no hay una fecha de referencia clara para medir "un año de
   mora". Si `tipo == RECURRENTE` y cualquiera de los dos campos está activo → `ValueError` explícito.
2. **Mutuamente excluyentes.** Si `anatocismo_demanda_judicial=True` **y** `anatocismo_fecha_acuerdo` no es
   `None` a la vez → `ValueError` (una obligación solo declara una vía habilitante).
3. **El acuerdo debe cumplir el año de anterioridad por sí mismo.** Si `anatocismo_fecha_acuerdo` no es
   `None`: debe cumplirse `anatocismo_fecha_acuerdo >= fecha_vencimiento + 365 días`; si no, `ValueError`
   (un acuerdo firmado antes de que los intereses lleven un año vencido no es válido bajo el Art. 886).

## Fecha de capitalización (`ComercialStrategy`, nuevo helper `_fecha_capitalizacion_anatocismo`)

- `anatocismo_demanda_judicial=True` → `fecha_vencimiento + 365 días`.
- `anatocismo_fecha_acuerdo` no `None` → `anatocismo_fecha_acuerdo` (ya validada ≥ vencimiento + 365 días).
- Ninguna condición activa → `None` (sin anatocismo).

Si la fecha resultante es posterior a `fecha_corte`, el anatocismo aún no ha "empezado a correr" para esta
liquidación — no se genera ningún evento de capitalización (se comporta como si no estuviera activo, sin
error: es simplemente que la condición temporal todavía no se cumple a la fecha de corte elegida).

## Eventos de capitalización (`ComercialStrategy._eventos_de_obligacion`)

Cuando hay fecha de capitalización y `fecha_capitalizacion <= fecha_corte`, se agregan eventos con
`event_type="CAPITALIZACION_INTERESES_ANATOCISMO"` en:

```
fecha_capitalizacion, fecha_capitalizacion + 365, fecha_capitalizacion + 730, ...
```

mientras la fecha resultante sea `<= fecha_corte`. No se modifica `_construir_rate_provider`: el periodo de
tasa moratoria sigue siendo un único tramo continuo desde `fecha_vencimiento + 1` hasta `fecha_corte`, igual
que hoy. La capitalización periódica sobre ese tramo continuo es lo que produce el efecto compuesto.

## Motor (`app/engine/liquidation/balance.py` y `app/engine/liquidation/engine.py`)

- Nuevo método `BalanceEngine.capitalize_interest(debt: PendingDebt) -> PendingDebt`: retorna
  `PendingDebt(principal=debt.principal + debt.interest, interest=Decimal("0.00"), indexation=debt.indexation)`.
- Nuevo caso en `LiquidationCore._process_event` para `"CAPITALIZACION_INTERESES_ANATOCISMO"`: aplica
  `BalanceEngine.capitalize_interest`, con `interest_amount=Decimal("0.00")` en el `LiquidationItem`
  resultante (no se está *añadiendo* interés nuevo, solo trasladando lo ya devengado; `capital_base` en esa
  fila ya refleja el capital aumentado, mismo patrón que la fila `LIQUIDATION_CUTOFF`).
- Si el interés acumulado en el momento de capitalizar es `Decimal("0.00")` (ej. ya fue pagado por un abono
  previo), el evento sigue siendo válido — no hace nada, capital y interés quedan igual.

## GUI (`app/views/obligaciones.py`)

Siguiendo el patrón ya usado para `fecha_vencimiento`/`tasa_moratoria_anual` (visibles solo si
`área == COMERCIAL`):

- `QCheckBox` "Demanda judicial (habilita anatocismo)" → `anatocismo_demanda_judicial`.
- `QCheckBox` "¿Hay acuerdo posterior de capitalización?" + `QDateEdit` "Fecha del acuerdo" (el checkbox
  controla si se envía `None` o la fecha del `QDateEdit`, mismo patrón ya usado para
  `check_pagada`/`campo_fecha_pago_total` en Laboral).
- Ambos widgets visibles solo si `área == COMERCIAL` **y** `tipo == PUNTUAL` (se ocultan si se cambia el
  combo a Recurrente, mismo mecanismo que ya dispara `_actualizar_campos_visibles`).

## Testing

- `tests/engine/liquidation/test_engine.py` (o archivo equivalente ya existente): test unitario de
  `BalanceEngine.capitalize_interest` y del nuevo caso en `LiquidationCore._process_event`.
- `tests/services/test_area_strategy.py`:
  - Anatocismo se activa con `anatocismo_demanda_judicial=True` + mora > 1 año: el capital final refleja
    la capitalización (mayor que el interés simple equivalente).
  - Anatocismo se activa con `anatocismo_fecha_acuerdo` válido (≥ vencimiento + 365 días).
  - Anatocismo se **deniega** (sigue en interés simple puro) cuando no se cumple ninguna de las dos
    condiciones habilitantes, aunque haya mora > 1 año.
  - Anatocismo se **deniega** cuando la condición existe pero la mora no llega a 1 año todavía (fecha de
    corte anterior a la fecha de capitalización).
  - `ValueError` para `RECURRENTE` con anatocismo activo.
  - `ValueError` para ambas condiciones activas a la vez.
  - `ValueError` para `anatocismo_fecha_acuerdo` que no cumple el año de anterioridad.
  - Test con un abono registrado dentro del tramo de anatocismo, verificando que la capitalización
    posterior a ese abono opera sobre el saldo ya reducido (no sobre el saldo original).
- `tests/scripts/test_migrate_anatocismo_comercial.py`: mismo patrón que los tests de migración existentes.
- `tests/views/test_obligaciones.py`: visibilidad condicional de los campos nuevos.
- Suite completa en verde.

## Fuera de alcance (explícito)

- Anatocismo civil (Art. 1617 C.C. lo prohíbe de forma general) y anatocismo tributario/laboral — ninguno
  mencionado en el PDF para esas áreas (ya estaba en el Pendientes original).
- Expedientes con **varias** obligaciones comerciales donde solo algunas cumplen las condiciones de
  anatocismo: el motor consolida todas las obligaciones del expediente en un solo saldo corriente
  (`LiquidationCore` procesa un único `PendingDebt` por expediente, no uno por obligación). Un evento de
  capitalización capitaliza **todo** el interés acumulado en ese momento, sin distinguir de qué obligación
  proviene. Esta es una limitación heredada de la arquitectura ya existente (compartida por todos los tipos
  de evento, no introducida por este sprint) — se documenta, no se resuelve aquí.
- `CompoundInterest.calculate()` queda huérfano (ver "Decisión de arquitectura" arriba); no se elimina el
  archivo ni se le agregan tests nuevos en este sprint.

## Definición de hecho

- Migración de esquema corrida contra el `bastium.db` real del equipo.
- `ComercialStrategy` sigue liquidando en interés simple por defecto cuando no se cumplen las condiciones
  (ninguna obligación existente cambia de comportamiento).
- Test que activa anatocismo con demanda judicial + >1 año de mora, y otro que lo deniega sin alguna de las
  dos condiciones (mínimo exigido por `Pendientes.md`), más los casos adicionales listados en "Testing".
- GUI actualizada y probada (visibilidad condicional).
- Suite completa en verde.
- `Pendientes.md`: marcar Sprint 19 como completado, documentando la desviación de arquitectura (eventos de
  capitalización periódica en vez de `CompoundInterest.calculate()` de una sola pasada) y por qué.
- `README.md`/`docs/GUIA_USUARIO.md` actualizados si corresponde (regla de cierre de sprint ya seguida en
  sprints anteriores).
