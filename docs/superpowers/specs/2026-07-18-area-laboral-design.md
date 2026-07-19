# Diseño — Sprint 3: Área Laboral

**Fecha:** 2026-07-18
**Origen:** `Pendientes.md`, sección "Sprint 3 — Área Laboral".
**Estado:** Aprobado por el usuario, listo para plan de implementación.

## Contexto

`LaboralStrategy` existe como stub en `app/services/area_strategy.py` (línea ~223) y lanza
`AreaNoImplementadaError`. El área "LABORAL" ya está registrada en `AreaRegistry`
(`app/engine/liquidation/registry.py`, línea 40) y en el enum `AreaDerecho` de `database/models.py` —
solo falta la implementación real y habilitarla en `AREAS_DERECHO`.

Ya existe `LaborScheduler` (`app/engine/temporal/schedulers/labor.py`), cubierto por 2 tests
(`tests/temporal/test_labor.py`), que genera Cesantías, Intereses/Cesantías, Prima Junio y Prima
Diciembre — pero con fechas de calendario fijas (14-feb, 31-ene, 30-jun, 20-dic), pensadas para un
contrato *vigente*, no para una liquidación final. No genera Vacaciones. La indemnización moratoria
bifásica del Art. 65 CST no existe en ningún archivo.

## Verificación previa (Pendientes.md pedía confirmar antes de construir)

**No hay bug en `INTERESES_CESANTIAS`.** El PDF de requisitos (pág. 51) confirma la fórmula exacta que
ya implementa el código: `(Cesantías × 0.12 × días) / 360`. La sospecha de bug en `Pendientes.md` era
incorrecta — la propia cita del PDF que traía la nota ya coincidía con el código. No se modifica esta
fórmula, solo se documenta que quedó verificada.

## Decisiones tomadas con el usuario

1. **Seguridad social (cotizaciones IBC, pensión, salud, ARL, FSP) queda fuera de este sprint.**
   BASTIUM liquida procesos judiciales (deuda de un ex-empleado hacia el trabajador), no es un sistema
   de nómina corriente. Se documenta como pendiente explícito, igual que TRM quedó fuera del Sprint 2.
2. **Modelo de finiquito.** Las cinco prestaciones (Cesantías, Intereses/Cesantías, Prima Junio, Prima
   Diciembre, Vacaciones) se vuelven exigibles en la fecha de terminación del contrato, no en las
   fechas fijas de calendario que `LaborScheduler` usa hoy. Es la única forma en que el Art. 65 CST
   tiene sentido (la mora se cuenta desde el día siguiente a la terminación).
3. **Indemnización moratoria Art. 65 CST → cálculo aparte, no motor genérico de eventos.** La Fase 1
   es un monto fijo por día de retardo (no una tasa de interés), así que no encaja en el modelo
   genérico `Event + RateProvider`. Se calcula en una función pura (`MoratoryIndemnityCalculator`) y se
   inyecta como un único evento `SANCION_MORATORIA` (concepto ya reconocido como capital en
   `LiquidationCore._capital_concepts`, línea 30).
4. **`LaborScheduler` se reescribe** (nueva firma, sin modo "fechas fijas de calendario") en vez de
   mantener dos modos. No hay otro caller en producción hoy — solo sus 2 tests, que se actualizan.
5. **`dias_trabajados` = diferencia de calendario simple** (`(fecha_fin - fecha_inicio).days`), no la
   convención comercial exacta de meses de 30 días que usa la nómina real. Simplificación MVP
   documentada como limitación conocida (ver abajo), mismo espíritu que otras simplificaciones ya
   aceptadas en Sprints 2 y 5.
6. **Fase 2 del Art. 65 CST usa la tasa de usura histórica ya cargada** (`historical_index.
   get_ibc_usura_for_date()`, Sprint 5, ya implementado) en vez de pedir un campo nuevo o hardcodear un
   valor — es la "tasa máxima legal (SFC)" que menciona el PDF.

## Limitación conocida: convención de días trabajados

Colombia liquida prestaciones sociales con una convención comercial de "meses de 30 días" (30/360),
no con la diferencia real de calendario. Para un contrato de un año calendario completo (365/366 días
reales), calcular `dias_trabajados` como diferencia de calendario simple sobre-causa las prestaciones
en ~1-2% frente al valor exacto de nómina. Esta convención exacta (30/360 día a día) no existe hoy en
el código y no se construye en este sprint — se documenta como pendiente explícito, no como omisión
por descuido. Si un caso real exige precisión exacta de nómina, es un sprint aparte (una utilidad de
conteo 30/360, análoga a un day-count convention de mercado financiero).

## `LaborScheduler` — rediseño

`app/engine/temporal/schedulers/labor.py`, reemplaza el constructor y `generate()` actuales:

```python
class LaborScheduler(Scheduler):
    def __init__(self, salario_base: Decimal, dias_trabajados: int, fecha_liquidacion: date):
        self.salario = salario_base
        self.dias = Decimal(str(dias_trabajados))
        self.fecha_liquidacion = fecha_liquidacion
        self.base_anual = Decimal("360")

    def generate(self, start: date = None, end: date = None) -> List[Event]:
        # Los 5 eventos (CESANTIAS, INTERESES_CESANTIAS, PRIMA_JUNIO, PRIMA_DICIEMBRE, VACACIONES)
        # se generan TODOS con date=self.fecha_liquidacion.
        # Formulas identicas a las actuales (verificadas contra el PDF) + VACACIONES nueva:
        #   monto_vacaciones = Rounding.money((self.salario * self.dias) / Decimal("720"))
```

- `anio` desaparece del constructor: ya no aporta nada si todas las fechas son `fecha_liquidacion`.
- Fórmulas de Cesantías, Intereses/Cesantías y Prima (junio/diciembre) se mantienen exactamente iguales
  a hoy — ya verificadas contra el PDF, solo cambia la fecha asignada a cada `Event`.
- Nueva `VACACIONES`: divisor 720 (PDF pág. 51: "las vacaciones no son técnicamente una prestación
  social, sino un descanso remunerado, por lo que su divisor es 720, doble del año comercial de 360").
- `tests/temporal/test_labor.py` se reescribe: 5 eventos (no 4), todos con
  `date == fecha_liquidacion`, y se agrega la verificación del monto de `VACACIONES`.

## `MoratoryIndemnityCalculator` — Art. 65 CST bifásico

Nuevo archivo `app/engine/labor/moratory_indemnity.py` (nuevo paquete `app/engine/labor/`):

```python
@dataclass(frozen=True)
class MoratoryIndemnityResult:
    dias_retardo: int
    dias_fase1: int
    monto_fase1: Decimal
    dias_fase2: int
    monto_fase2: Decimal
    total: Decimal

class MoratoryIndemnityCalculator:
    LIMITE_FASE1_DIAS = 720  # 24 meses, PDF pag. 51 y 3427-3433

    @staticmethod
    def calcular(
        salario_mensual: Decimal,
        monto_adeudado: Decimal,
        fecha_terminacion: date,
        fecha_pago_o_corte: date,
    ) -> MoratoryIndemnityResult:
        ...
```

Lógica:
- `dias_retardo = (fecha_pago_o_corte - fecha_terminacion).days`. Si `<= 0`, retorna todo en cero (no
  hay mora — se pagó a tiempo o antes de terminar el contrato).
- **Fase 1** (día 1 a 720): `salario_diario = salario_mensual / 30`;
  `monto_fase1 = Rounding.money(salario_diario * min(dias_retardo, 720))`.
- **Fase 2** (día 721 en adelante, solo si `dias_retardo > 720`): interés diario simple sobre
  `monto_adeudado`, día por día desde el día 721 hasta `fecha_pago_o_corte`, usando
  `EffectiveRateConverter.annual_to_daily(usura)` donde `usura` viene de
  `historical_index.get_ibc_usura_for_date(fecha_del_dia)` — misma fórmula EA→diaria que usan
  Civil/Comercial, sin introducir un flag nuevo de 360 vs 365 días.
- `total = monto_fase1 + monto_fase2`.

**Tests explícitos del punto de quiebre** (`tests/engine/labor/test_moratory_indemnity.py`, nuevo):
pagado a tiempo (todo cero), exactamente día 720 (solo fase 1, `monto_fase1 = salario_diario * 720`,
`monto_fase2 = 0`), día 721 (fase 1 tope + 1 día de fase 2), varios meses en fase 2 cruzando tramos de
usura distintos.

## `LaboralStrategy`

`app/services/area_strategy.py`, reemplaza el stub actual (línea ~223-227):

```python
class LaboralStrategy(AreaStrategy):
    soporta_indexacion_ipc = False  # prestaciones laborales no son indexables por IPC en este alcance

    def liquidar(self, obligaciones, abonos, fecha_corte) -> LiquidationResult:
        if len(obligaciones) != 1:
            raise ValueError(
                "El area Laboral liquida un solo contrato (una obligacion) por expediente."
            )
        obligacion = obligaciones[0]
        self._validar_obligacion_laboral(obligacion)

        dias_trabajados = (obligacion.fecha_fin - obligacion.fecha_inicio).days
        eventos = LaborScheduler(
            salario_base=obligacion.valor,
            dias_trabajados=dias_trabajados,
            fecha_liquidacion=obligacion.fecha_fin,
        ).generate()

        fecha_referencia_mora = obligacion.fecha_pago_total or fecha_corte
        if fecha_referencia_mora > obligacion.fecha_fin:
            monto_adeudado = sum(e.payload["amount"] for e in eventos)
            mora = MoratoryIndemnityCalculator.calcular(
                salario_mensual=obligacion.valor,
                monto_adeudado=monto_adeudado,
                fecha_terminacion=obligacion.fecha_fin,
                fecha_pago_o_corte=fecha_referencia_mora,
            )
            if mora.total > Decimal("0.00"):
                eventos.append(Event(
                    date=fecha_referencia_mora,
                    payload={"amount": mora.total, "label": "Indemnizacion moratoria Art. 65 CST"},
                    event_type="SANCION_MORATORIA",
                ))

        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos
        ]
        return UniversalLiquidationService().liquidar(
            eventos_causacion=eventos, pagos=pagos, fecha_corte=fecha_corte,
        )
        # Sin rate_provider: tasa diaria generica queda en 0 (default de UniversalLiquidationService).
        # Toda la mora del area Laboral ya esta resuelta en el evento SANCION_MORATORIA -- pasar un
        # rate_provider aqui duplicaria el castigo por mora.

    def _validar_obligacion_laboral(self, obligacion) -> None:
        # tipo == PUNTUAL, valor > 0, fecha_inicio y fecha_fin no nulos, fecha_fin > fecha_inicio,
        # y si pagada es True, fecha_pago_total no puede ser None (no se puede marcar pagada sin fecha).
        ...
```

Notas:
- Restricción de alcance: una obligación Laboral = un contrato completo. `tipo` debe ser `PUNTUAL`
  (`RECURRENTE` no aplica a prestaciones sociales — se rechaza con `ValueError` si llega).
  `LaboralStrategy` exige exactamente 1 obligación por expediente en este sprint.
  Si el pago real fue *antes* o el mismo día de `fecha_fin` (`fecha_pago_total <= fecha_fin`), no hay
  mora — se omite el evento `SANCION_MORATORIA`.

## Modelo de datos — sin migración

Se reutilizan columnas existentes de `Obligacion` (`database/models.py`) que hoy ningún código lee ni
escribe (confirmado por grep en todo `app/`):

| Campo existente | Uso para Laboral |
|---|---|
| `valor` | Salario base mensual |
| `fecha_inicio` | Inicio del contrato |
| `fecha_fin` | Terminación del contrato (dispara el finiquito y la mora) |
| `fecha_origen` (NOT NULL) | Se guarda igual a `fecha_inicio` — satisface la restricción de la columna, no se usa en el cálculo |
| `tasa_efectiva_anual` (NOT NULL) | Sin uso real en Laboral — se guarda `Decimal("0.00")` |
| `pagada` | Se activa: `True` si el empleador pagó la liquidación completa |
| `fecha_pago_total` | Fecha real de pago, si `pagada` es `True`; si es `None`, la mora corre hasta `fecha_corte` |
| `categoria` | Valor único nuevo `"LIQUIDACION_CONTRATO_LABORAL"` — solo etiqueta de UI, no dirige el `event_type` (lo define `LaborScheduler` internamente, a diferencia de Civil/Comercial) |

`app/core/constants.py`: nueva lista `CATEGORIAS_LABORAL = [("LIQUIDACION_CONTRATO_LABORAL",
"Liquidación de contrato laboral")]`.

## GUI

`app/views/obligaciones.py` (`ObligacionFormDialog`), que ya recibe `area` en el constructor y ya tiene
el patrón condicional de Comercial (`es_comercial`):

- Nuevo widget `QDateEdit` para `fecha_fin` (hoy la clase no tiene ningún widget para este campo — se
  guarda siempre `None`), etiqueta "Fecha de terminación de contrato". Visible solo si `area == "LABORAL"`.
- Nuevo checkbox "Prestaciones pagadas" + `QDateEdit` "Fecha de pago real", visibles solo si
  `area == "LABORAL"`. Escriben `pagada` / `fecha_pago_total` (hoy sin ningún control en la GUI).
- Cuando `area == "LABORAL"`:
  - `combo_categoria` usa `CATEGORIAS_LABORAL`.
  - `combo_tipo` se fija en "Puntual" y se oculta (Laboral no admite Recurrente).
  - Se ocultan los campos propios de Comercial (ya ocultos por default) y el campo de tasa efectiva
    (se envía `Decimal("0.00")` sin mostrar el widget).
  - El campo "Fecha de origen (Puntual)", ya visible para tipo Puntual, se reutiliza como "fecha de
    inicio del contrato" (mismo widget, mapeado también a `fecha_inicio` al guardar).
- `guardar()`: cuando `area == "LABORAL"`, arma el `Obligacion(...)` con `fecha_inicio` = valor del
  campo fecha de origen, `fecha_fin` = valor del nuevo campo, `fecha_origen` = igual a `fecha_inicio`,
  `tasa_efectiva_anual = Decimal("0.00")`, `pagada` y `fecha_pago_total` según el checkbox.

`app/core/constants.py`: `AREAS_DERECHO` → tercer valor de `("LABORAL", "Laboral", False)` a `True`.

No se requieren cambios en `app/views/expediente_detalle.py`: `_abrir_dialogo_obligacion` ya pasa
`area=area` al diálogo, y `_liquidar()` ya captura `ValueError` genérico (línea 131) — `LaboralStrategy`
no introduce ninguna excepción de dominio nueva, solo usa `ValueError`.

`registry.py` no requiere cambios: `LaboralStrategy` ya está registrada (línea 40).

## Fuera de alcance (explícito)

- Seguridad social / cotizaciones (confirmado con el usuario, ver decisión #1).
- Incapacidades comunes/laborales y eventos de suspensión contractual (SLN) — PDF sección 4, no
  mencionados en el alcance incluido de `Pendientes.md`.
- Régimen de Prima Media, IBL y pensiones — PDF sección 5, dominio aparte según `Pendientes.md`.
- Conteo real de calendario (365/366) para densidad de semanas de pensión (Sentencia SL138-2024) — no
  aplica, ya que este sprint no toca pensiones.
- Convención exacta 30/360 para `dias_trabajados` (ver limitación conocida arriba).
- Contratos que abarcan múltiples años con SMLMV histórico variable — `LaborScheduler` no consume
  SMLMV en absoluto (recibe el salario ya en pesos), así que esto no bloquea el sprint, pero un
  contrato de varios años se liquida hoy como un solo bloque de días trabajados, no año por año.
- Múltiples obligaciones Laborales por expediente (un expediente = un contrato, ver restricción de
  alcance de `LaboralStrategy`).

## Testing

- `tests/temporal/test_labor.py`: reescrito para el nuevo constructor de `LaborScheduler`; verifica 5
  eventos, todos con `date == fecha_liquidacion`, y el monto de `VACACIONES`.
- `tests/engine/labor/test_moratory_indemnity.py` (nuevo): pagado a tiempo, día exacto 720, día 721
  (punto de quiebre), varios meses en fase 2 con tramos de usura distintos.
- `tests/services/test_area_strategy.py`:
  - Quitar `("LABORAL", LaboralStrategy)` del parametrize de
    `test_areas_no_implementadas_lanzan_error_claro_al_liquidar`.
  - Nueva clase `TestLaboralStrategy`: liquidación completa sin mora (pagado a tiempo), con mora solo
    fase 1, con mora cruzando a fase 2, con abonos parciales, con más de una obligación (`ValueError`),
    con `tipo == RECURRENTE` (`ValueError`).
- `tests/views/test_obligaciones.py`: caso que guarda una obligación Laboral con `fecha_fin`,
  `pagada`/`fecha_pago_total`.
- Smoke test manual (mismo patrón que Tarea 17 del MVP / Sprint 2): crear expediente Laboral, agregar
  obligación con fecha de terminación en el pasado (para forzar mora), liquidar, confirmar que aparece
  `SANCION_MORATORIA` en el resultado, exportar a PDF/Word.

## Definición de hecho

- `LaboralStrategy` liquida con TDD (cesantías + intereses + prima + vacaciones + indemnización
  moratoria bifásica cuando aplica).
- Test específico del punto de quiebre día 720/721 del Art. 65 CST, pasando.
- Área "Laboral" seleccionable y operable end-to-end desde la GUI (smoke test manual).
- Suite completa sigue en verde.
- `README.md` y `docs/GUIA_USUARIO.md` actualizados: sacar Laboral de "🚧 no todavía" y documentar cómo
  capturar una obligación laboral (salario, fechas de contrato, estado de pago), igual que se
  documentó Civil/Familia y Comercial.
- `Pendientes.md`: marcar seguridad social, incapacidades y convención 30/360 como pendientes
  explícitos separados (no resueltos en este sprint, decisión tomada con el usuario, no un olvido).
