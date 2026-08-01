# Diseño — Sprint 20: Indexación sobre capital ya indexado (algoritmo "Suma Única")

**Fecha:** 2026-07-31
**Origen:** `Pendientes.md`, sección "Sprint 20 — Indexación sobre capital ya indexado (algoritmo
'Suma Única')".
**Estado:** Aprobado por el usuario, listo para plan de implementación.

## Contexto

Desde el Sprint 8, `CivilFamiliaStrategy` (única área con `soporta_indexacion_ipc = True`) emite un
evento `INDEXATION` por obligación indexada, con el delta calculado por `IPCIndexation.calculate()`.
Ese monto cae en `PendingDebt.indexation`, un bucket separado de `PendingDebt.principal`.

`LiquidationCore._accrue_time_passage()` (`app/engine/liquidation/engine.py:88-109`) calcula el interés
diario usando únicamente `self._current_debt.principal` como base — el bucket `indexation` nunca genera
interés. El PDF de requisitos (pág. 21-22, "Caso de Suma Única") exige lo contrario: primero indexar
(obtener `Va`), luego aplicar el interés civil puro (6% EA) **sobre `Va`**, no sobre el capital histórico
sin indexar. El Sprint 8 documentó esta brecha deliberadamente como fuera de alcance (ver su design doc,
sección "Fuera de alcance", punto 1).

**Hallazgo del diseño, no documentado en `Pendientes.md`:** el bucket `PendingDebt.indexation` está
compartido entre dos usos distintos: indexación IPC real (`CivilFamiliaStrategy`, event_type
`"INDEXATION"`) y sanciones tributarias (`TributarioStrategy`, event_type `"SANCION_TRIBUTARIA"` —
`app/services/area_strategy.py:127`). `TributarioStrategy` reutiliza deliberadamente ese bucket solo por
el orden de prelación de pago que ya aplica `AllocationEngine.allocate()` (indexación/sanciones →
intereses → capital), **no** porque las sanciones deban generar interés compuesto sobre sí mismas (ver
docstring de `TributarioStrategy`, línea 806). Un cambio ingenuo a `_accrue_time_passage` que sume
`principal + indexation` sin distinción habría hecho que Tributario empezara a cobrar interés E.T. art.
635 compuesto sobre sanciones — comportamiento no pedido por el PDF y ajeno al alcance de este sprint.

## Decisiones tomadas con el usuario

1. **Se migra al algoritmo exacto, no se deja como simplificación del MVP.** El comportamiento actual
   (interés solo sobre capital sin indexar) pasa a ser incorrecto por defecto disponible; el algoritmo
   "Suma Única" queda disponible como opción explícita por obligación (ver punto 3).

2. **Sin recompute de liquidaciones auditadas — confirmado que no hace falta un guard especial.**
   `reconstruir_liquidacion()` (`app/engine/audit/service.py:35-40`) deserializa el `resultado_json`
   guardado en `AuditLog` en el momento de la ejecución; nunca vuelve a calcular desde las obligaciones.
   Cambiar el algoritmo del motor no afecta liquidaciones ya auditadas porque estas son fotos congeladas,
   no se re-derivan. El riesgo que anticipaba `Pendientes.md` en su sección "Riesgos" ya está resuelto por
   el diseño existente del Sprint 9.

3. **Flag explícito por obligación, no reemplazo global ni parámetro a nivel de expediente.** Nuevo campo
   `Obligacion.interes_sobre_capital_indexado: bool` (default `False`), mismo patrón que
   `aplica_indexacion_ipc` (juicio del abogado, no regla automática). Solo tiene efecto cuando
   `aplica_indexacion_ipc` también es `True`. Un expediente con obligaciones mezclando `True`/`False` en
   este campo (entre las que sí tienen indexación activa) es un error de captura — se rechaza con
   `ValueError` explícito en vez de aplicar el criterio de una sola obligación a todo el expediente en
   silencio (ver "Componentes técnicos", punto 4).

4. **No se toca el modelo de dominio compartido (`PendingDebt`/`BalanceEngine`/`AllocationEngine`).** En
   vez de separar el bucket `indexation` en dos (real vs. sanciones tributarias), el flag "Suma Única" se
   resuelve **por llamada a `liquidar()`** a nivel de `LiquidationCore`. Como `TributarioStrategy` nunca
   emite eventos `INDEXATION` (solo `SANCION_TRIBUTARIA`) y nunca activa el flag, las sanciones tributarias
   nunca entran a la base de interés aunque compartan el bucket — sin necesidad de tocar código usado por
   las 5 áreas. Reduce drásticamente el blast radius frente a la alternativa de redefinir `PendingDebt`.

5. **Ley 80/1993 (contratos estatales): documentación, no código nuevo.** El PDF (pág. 22, "Coexistencia
   con Intereses") confirma que es la misma mecánica de Suma Única con fuente normativa propia para
   contratación estatal. Se documenta como variante en el docstring de `CivilFamiliaStrategy` y del nuevo
   campo; no requiere una rama de código distinta.

## Componentes técnicos

### 1. `database/models.py`

```python
class Obligacion(Base):
    ...
    interes_sobre_capital_indexado: Mapped[bool] = mapped_column(Boolean, default=False)
```
Ubicado junto a `aplica_indexacion_ipc` (línea 118). Sin campo separado para Ley 80/1993 — mismo flag,
documentado como variante en el docstring de la clase.

### 2. `scripts/migrate_interes_sobre_capital_indexado.py` (nuevo, ejecución única)

Mismo patrón que `scripts/migrate_aplica_indexacion_ipc.py`: idempotente vía `PRAGMA table_info`,
`ALTER TABLE obligaciones ADD COLUMN interes_sobre_capital_indexado BOOLEAN NOT NULL DEFAULT 0`.

### 3. `app/engine/liquidation/engine.py` → `LiquidationCore`

- `__init__` recibe un nuevo parámetro `usar_suma_unica: bool = False`, guardado como
  `self._usar_suma_unica`.
- `_accrue_time_passage` (línea 101) cambia la base de capital de:
  ```python
  capital=self._current_debt.principal
  ```
  a:
  ```python
  capital=self._current_debt.principal + (
      self._current_debt.indexation if self._usar_suma_unica else Decimal("0.00")
  )
  ```
- Ningún otro método de `LiquidationCore` cambia. `PendingDebt`, `BalanceEngine`, `AllocationEngine`
  quedan intactos — el orden de imputación de pagos no depende de dónde se computa el interés.

### 4. `app/services/motor_universal.py` → `UniversalLiquidationService`

`liquidar()` recibe el mismo parámetro `usar_suma_unica: bool = False` y lo reenvía al constructor de
`LiquidationCore`. Todas las demás estrategias (`ComercialStrategy`, `LaboralStrategy`,
`SancionatorioStrategy`, `HonorariosStrategy`, `TributarioStrategy`) siguen llamando a `liquidar()` sin
pasar este argumento — quedan en el default `False`, comportamiento idéntico al actual.

### 5. `app/services/area_strategy.py` → `CivilFamiliaStrategy`

Antes de llamar a `UniversalLiquidationService().liquidar(...)`, deriva el flag:

```python
def _resolver_suma_unica(self, obligaciones: List) -> bool:
    valores = {
        o.interes_sobre_capital_indexado for o in obligaciones if o.aplica_indexacion_ipc
    }
    if len(valores) > 1:
        raise ValueError(
            "Todas las obligaciones con indexación IPC del expediente deben usar el mismo "
            "criterio de interés (Suma Única o legado); no se puede mezclar dentro del mismo "
            "expediente."
        )
    return valores == {True}
```

`liquidar()` pasa `usar_suma_unica=self._resolver_suma_unica(obligaciones)` a
`UniversalLiquidationService().liquidar(...)`.

### 6. GUI — `app/views/obligaciones.py` (`ObligacionFormDialog`)

- Nuevo checkbox `check_interes_sobre_capital_indexado`, hermano de `check_aplica_indexacion_ipc`
  (creado cerca de la línea 94), mismo texto de patrón: `"Interés sobre capital ya indexado (algoritmo
  Suma Única / Ley 80 de 1993)"`.
- Agregado al layout con `self.layout_formulario.addRow(self.check_interes_sobre_capital_indexado)`
  (sin label separado, igual que los demás checkboxes).
- Visibilidad: `self.check_interes_sobre_capital_indexado.setVisible(self._area == "CIVIL_FAMILIA")`,
  junto a la visibilidad ya existente de `check_aplica_indexacion_ipc` (línea ~179). No se acopla su
  habilitación a que el otro checkbox esté marcado — si el abogado lo marca sin `aplica_indexacion_ipc`,
  simplemente no tiene efecto (mismo criterio de tolerancia que ya aplica el formulario a otras
  combinaciones no aplicables).
- `guardar()` lee `interes_sobre_capital_indexado=self.check_interes_sobre_capital_indexado.isChecked()`
  junto a la lectura existente del otro checkbox (línea ~386).

## Fuera de alcance (explícito)

- Migrar automáticamente liquidaciones históricas ya registradas en `AuditLog` al nuevo algoritmo — la
  reconstrucción de una liquidación pasada sigue siendo la foto congelada guardada en su momento (ver
  decisión 2).
- Separar `PendingDebt.indexation` en dos buckets (indexación real vs. sanciones tributarias) — resuelto
  sin tocar el modelo de dominio (ver decisión 4).
- Cualquier cambio a `TributarioStrategy`, `ComercialStrategy`, `LaboralStrategy`, `SancionatorioStrategy`,
  `HonorariosStrategy` — ninguna pasa `usar_suma_unica=True`, comportamiento idéntico al actual.
- Cambiar el mecanismo de acumulación de interés (`DailyInterest` + `EffectiveRateConverter`, interés
  simple diario con tasa diaria equivalente a la EA) por una fórmula cerrada tipo `Dec = Va×(1+i)^n`. Es
  el mecanismo preexistente usado por las 5 áreas, validado desde sprints anteriores; este sprint solo
  cambia *qué capital* alimenta ese mecanismo, no *cómo* acumula el interés día a día.
- Campo o rama de código separada para Ley 80/1993 — mismo flag, documentado como variante (decisión 5).

## Testing

- **Regresión:** toda la suite existente debe seguir en verde sin cambios de resultado — todas las
  llamadas existentes a `liquidar()`/`LiquidationCore()` usan el default `usar_suma_unica=False`.
- **Interés sobre capital indexado:** obligación PUNTUAL con `aplica_indexacion_ipc=True` y
  `interes_sobre_capital_indexado=True`, verificando que el interés final es mayor que el que resultaría
  con el flag en `False` (mismo capital, mismo periodo, mismo `IPCIndexation.calculate()`), y que la
  diferencia coincide con recomputar manualmente la acumulación diaria sobre `principal + indexation`.
- **Ejemplo numérico del PDF (pág. 69):** capital $50.000.000 de 1/1/2010 (IPC=140) a 1/1/2025 (IPC=200).
  El PDF solo certifica el resultado de la indexación (`Va = 50.000.000 × (200/140) = $71.428.571`), no
  el resultado combinado con interés — la fórmula de la pág. 21-22 (`Dec = Va×(1+i)^n`) es un formulón de
  una sola aplicación, mientras que el motor ya usa acumulación diaria de interés simple con tasa diaria
  equivalente (mecanismo preexistente, fuera de alcance, ver arriba). El test verifica `Va` contra el
  valor exacto del PDF y el interés resultante contra un cálculo independiente que replica la misma
  mecánica día-a-día del motor (no la fórmula cerrada), con un comentario explicando la distinción —
  mismo criterio de "cálculo manual documentado" que ya usan los tests existentes de indexación en
  `tests/services/test_area_strategy.py`.
- **Validación de consistencia:** expediente con dos obligaciones con `aplica_indexacion_ipc=True`, una
  con `interes_sobre_capital_indexado=True` y otra `False`, debe lanzar `ValueError` con el mensaje
  específico. Un expediente con una obligación indexada y otra sin indexar (esta última con cualquier
  valor del nuevo campo, irrelevante porque `aplica_indexacion_ipc=False`) no debe lanzar error.
- **Migración:** test que corre el script dos veces sobre una base de datos temporal, confirma
  idempotencia y que la columna queda con default `False`.
- Suite completa (hoy en verde) sigue pasando.

## Definición de hecho

- `LiquidationCore` calcula el interés sobre `principal + indexation` cuando `usar_suma_unica=True`,
  sobre `principal` solo cuando es `False` (default).
- `CivilFamiliaStrategy` deriva el flag por expediente desde `Obligacion.interes_sobre_capital_indexado`
  y rechaza combinaciones inconsistentes dentro del mismo expediente.
- Checkbox operable end-to-end desde la GUI (smoke test manual).
- Test que reproduce el ejemplo numérico del PDF (pág. 69) y verifica el resultado contra el cálculo
  manual, documentando la distinción entre la fórmula cerrada del PDF y la mecánica diaria del motor.
- Ninguna liquidación existente (Comercial, Laboral, Sancionatorio, Honorarios, Tributario, o
  Civil/Familia con el flag nuevo en `False`) cambia de resultado numérico.
- `bastium.db` migrado con la columna nueva sin perder las filas existentes.
- `README.md` y `docs/GUIA_USUARIO.md` actualizados (regla obligatoria de `Pendientes.md` al cerrar
  cualquier sprint).
- Suite completa en verde.
