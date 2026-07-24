# Diseño — Sprint 16: Seguridad social, incapacidades y suspensiones contractuales (Laboral)

**Fecha:** 2026-07-24
**Origen:** `Pendientes.md`, sección "Sprint 16 — Seguridad social, incapacidades y suspensiones
contractuales (Laboral)".
**Estado:** Aprobado por el usuario, listo para plan de implementación.

## Contexto

El Sprint 3 (`LaboralStrategy`, ver `docs/superpowers/specs/2026-07-18-area-laboral-design.md`) implementó
la liquidación final de un contrato laboral (cesantías, intereses/cesantías, prima, vacaciones e
indemnización moratoria Art. 65 CST) pero dejó fuera, a propósito, la seguridad social (cotizaciones IBC,
pensión, salud, ARL, FSP) y los eventos de incapacidad/suspensión — con la nota explícita de que la
decisión de alcance (¿es esto parte de una liquidación judicial o un módulo de nómina corriente fuera de
BASTIUM?) quedaba pendiente de conversación con el usuario.

Este sprint retoma esa decisión. `Pendientes.md` ya señalaba un matiz nuevo a favor de incluirlo: la pág.
74 del PDF de requerimientos ("8) Reglas laborales") ubica "seguridad social" y los "eventos de suspensión
contractual, licencias no remuneradas e incapacidades comunes o laborales con sus pagadores y porcentajes"
dentro del catálogo EFDJ del motor de cálculo, no como un módulo de nómina aparte.

## Decisiones tomadas con el usuario

1. **Alcance: liquidación judicial de aportes/prestaciones dejados de pagar**, no un módulo de nómina
   corriente (PILA, afiliaciones periódicas). Se calcula cuánto debía haber cotizado/pagado el empleador y
   no lo hizo, como parte de la deuda laboral de un expediente — igual espíritu que el resto de BASTIUM.
   Esto confirma y cierra la nota abierta del Sprint 3.
2. **Modelo de datos: tabla nueva `eventos_laborales`**, no campos únicos en `Obligacion`. Las incapacidades
   y suspensiones son eventos de duración variable que pueden repetirse dentro de un mismo contrato (ej.
   dos incapacidades distintas + una suspensión), lo que no cabe en un par de columnas fijas.
3. **Activación de cotizaciones: checkbox opt-in por obligación** (`incluir_seguridad_social`), no
   automático para todo contrato Laboral. No todo caso reclama aportes no pagados — es un hecho específico
   que hay que alegar. Si no se marca, el expediente se liquida exactamente igual que hoy (sin regresión).
4. **Base de aporte: monto total (empleador + trabajador)**, no solo la porción del empleador. Es la
   lectura literal del PDF (los porcentajes de pensión y salud que cita ya son el total) y la interpretación
   más simple y defendible: si el empleador nunca cotizó, debe el total que tenía que consignar a la
   administradora.
5. **Tabla ARL completa (niveles I-V)**, usando el Decreto 1607/2002 para los niveles II-IV que el PDF no
   cita con número exacto (solo da I=0.522% y V=6.960%). Estos dos extremos coinciden exactamente con el
   Decreto, así que II-IV no son una suposición arriesgada — se documentan como fuente externa
   complementaria, no como invención.
6. **FSP: tabla progresiva completa por tramos de IBC en SMMLV** (Ley 797/2003 art. 8), no una tasa plana
   simplificada. El PDF describe "escala progresiva desde 1% hasta 2%" sin tramos exactos; se usa la escala
   oficial real (4-16, 16-17, 17-18, 18-19, 19-20, >20 SMMLV → 1%, 1.2%, 1.4%, 1.6%, 1.8%, 2%).
7. **Incapacidades: desglose informativo completo de todos los pagadores** (empleador, EPS, ARL) en la
   traza de liquidación, pero **solo el monto a cargo del empleador se suma a la deuda**. El sistema no
   asume automáticamente que el usuario reclama lo que le corresponde a la EPS o a la ARL — eso es un hecho
   distinto (ej. no afiliación), fuera de alcance de este sprint.
8. **Suspensión: excluye únicamente ARL** de la cotización (Salud y Pensión se mantienen), sobre los días
   exactos del evento, con una línea informativa de auditoría (monto 0) en la traza.

## Modelo de datos

### Tabla nueva `eventos_laborales` (sin migración — `Base.metadata.create_all` la crea)

```python
class TipoEventoLaboral(enum.Enum):
    SUSPENSION = "SUSPENSION"
    INCAPACIDAD_COMUN = "INCAPACIDAD_COMUN"
    INCAPACIDAD_LABORAL = "INCAPACIDAD_LABORAL"

class MotivoSuspension(enum.Enum):
    HUELGA = "HUELGA"
    LICENCIA_NO_REMUNERADA = "LICENCIA_NO_REMUNERADA"
    DISCIPLINARIA = "DISCIPLINARIA"

class EventoLaboral(Base):
    __tablename__ = "eventos_laborales"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    obligacion_id: Mapped[int] = mapped_column(ForeignKey("obligaciones.id"))
    tipo: Mapped[TipoEventoLaboral] = mapped_column(SAEnum(TipoEventoLaboral))
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    motivo_suspension: Mapped[MotivoSuspension | None] = mapped_column(SAEnum(MotivoSuspension), nullable=True)

    obligacion: Mapped["Obligacion"] = relationship(back_populates="eventos_laborales")
```

Tabla polimórfica única (no `Incapacidad`/`Suspension` separadas): `motivo_suspension` solo se llena cuando
`tipo == SUSPENSION`. `Obligacion` gana `eventos_laborales: Mapped[list["EventoLaboral"]]` con
`cascade="all, delete-orphan"`, igual patrón que `abonos`.

Validaciones de negocio (en `LaboralStrategy`, no en la columna): `fecha_inicio < fecha_fin`, ambas dentro
del rango `[obligacion.fecha_inicio, obligacion.fecha_fin]`, `motivo_suspension` obligatorio si y solo si
`tipo == SUSPENSION`.

### 2 columnas nuevas en `obligaciones` (requieren `scripts/migrate_seguridad_social_laboral.py`)

- `incluir_seguridad_social: Boolean, default False` — checkbox opt-in.
- `nivel_riesgo_arl: VARCHAR(2), nullable` — "I".."V"; requerido solo si `incluir_seguridad_social` es
  `True` (validado en `LaboralStrategy._validar_obligacion_laboral`, `ValueError` claro si falta).

Script idempotente, mismo patrón exacto que `scripts/migrate_moneda_trm.py` (Sprint 12): `PRAGMA
table_info(obligaciones)` para verificar antes de cada `ALTER TABLE`, para poder correrse más de una vez
sin fallar.

## Cálculos (nuevo paquete `app/engine/labor/`)

### `seguridad_social.py` — `SeguridadSocialCalculator`

```python
@dataclass(frozen=True)
class CotizacionesResult:
    ibc_mensual: Decimal
    monto_pension: Decimal
    monto_salud: Decimal
    monto_arl: Decimal
    monto_fsp: Decimal
    total: Decimal

class SeguridadSocialCalculator:
    @staticmethod
    def calcular(
        salario_base: Decimal, dias_trabajados: Decimal, dias_suspension: Decimal,
        nivel_riesgo_arl: str, fecha_referencia: date,
    ) -> CotizacionesResult:
        smmlv = get_parametro("SMLMV", date(fecha_referencia.year, 1, 1))
        ibc = min(max(salario_base, smmlv), smmlv * Decimal("25"))  # PDF pag. 51: IBC entre 1 y 25 SMMLV

        monto_pension = Rounding.money(ibc * get_parametro("SS_PENSION_PCT", fecha_referencia) * dias_trabajados / Decimal("30"))
        monto_salud = Rounding.money(ibc * get_parametro("SS_SALUD_PCT", fecha_referencia) * dias_trabajados / Decimal("30"))

        dias_con_arl = dias_trabajados - dias_suspension  # suspension excluye SOLO ARL, PDF pag. 52
        arl_pct = get_parametro(f"SS_ARL_NIVEL_{nivel_riesgo_arl}_PCT", fecha_referencia)
        monto_arl = Rounding.money(ibc * arl_pct * dias_con_arl / Decimal("30"))

        monto_fsp = Decimal("0.00")
        if ibc >= smmlv * Decimal("4"):
            fsp_pct = _resolver_tramo_fsp(ibc, smmlv, fecha_referencia)
            monto_fsp = Rounding.money(ibc * fsp_pct * dias_trabajados / Decimal("30"))

        total = monto_pension + monto_salud + monto_arl + monto_fsp
        return CotizacionesResult(ibc, monto_pension, monto_salud, monto_arl, monto_fsp, total)


def _resolver_tramo_fsp(ibc: Decimal, smmlv: Decimal, fecha: date) -> Decimal:
    # Tramos Ley 797/2003 art. 8, en multiplos de SMMLV del IBC
    tramos = [
        (Decimal("16"), "SS_FSP_TRAMO_1_PCT"),   # 4  - 16 SMMLV
        (Decimal("17"), "SS_FSP_TRAMO_2_PCT"),   # 16 - 17 SMMLV
        (Decimal("18"), "SS_FSP_TRAMO_3_PCT"),   # 17 - 18 SMMLV
        (Decimal("19"), "SS_FSP_TRAMO_4_PCT"),   # 18 - 19 SMMLV
        (Decimal("20"), "SS_FSP_TRAMO_5_PCT"),   # 19 - 20 SMMLV
    ]
    for limite_superior, clave in tramos:
        if ibc < smmlv * limite_superior:
            return get_parametro(clave, fecha)
    return get_parametro("SS_FSP_TRAMO_6_PCT", fecha)  # > 20 SMMLV
```

`dias_trabajados / 30` reutiliza la misma convención comercial de 30 días ya aceptada como simplificación
MVP en el Sprint 3 (no hay bucketing mes a mes ni tasas de interés involucradas, así que no aplica el
`RateProvider` de Civil/Comercial). `dias_suspension` = suma de `(fecha_fin - fecha_inicio).days` de todos
los eventos `SUSPENSION` de la obligación (pueden ser varios).

**Límite conocido:** el SMMLV usado es el vigente en `fecha_referencia` (año de `obligacion.fecha_fin`),
una sola fotografía — no un histórico mes a mes para contratos que abarcan varios años. Misma
simplificación ya documentada y aceptada en el Sprint 3 para `LaborScheduler` (que tampoco consume SMMLV
histórico).

### `incapacidad.py` — `IncapacidadCalculator`

```python
@dataclass(frozen=True)
class TramoIncapacidad:
    dias: int
    pagador: str          # "EMPLEADOR" | "EPS" | "ARL"
    porcentaje: Decimal
    monto: Decimal

@dataclass(frozen=True)
class IncapacidadResult:
    tramos: list[TramoIncapacidad]
    monto_a_cargo_empleador: Decimal   # unico monto que se suma a la deuda del expediente

class IncapacidadCalculator:
    @staticmethod
    def calcular(tipo: TipoEventoLaboral, ibc_mensual: Decimal, dias_incapacidad: int) -> IncapacidadResult:
        ibc_diario = ibc_mensual / Decimal("30")

        if tipo == TipoEventoLaboral.INCAPACIDAD_LABORAL:
            monto = Rounding.money(ibc_diario * dias_incapacidad)  # ARL paga 100% desde dia 1
            tramo = TramoIncapacidad(dias_incapacidad, "ARL", Decimal("1.00"), monto)
            return IncapacidadResult([tramo], Decimal("0.00"))

        # INCAPACIDAD_COMUN: dias 1-2 empleador 66.67%, 3-90 EPS 66.67%, 91-180 EPS 50%
        tramos = []
        dias_1_2 = min(dias_incapacidad, 2)
        if dias_1_2 > 0:
            monto = Rounding.money(ibc_diario * Decimal("0.6667") * dias_1_2)
            tramos.append(TramoIncapacidad(dias_1_2, "EMPLEADOR", Decimal("0.6667"), monto))

        dias_3_90 = max(0, min(dias_incapacidad, 90) - 2)
        if dias_3_90 > 0:
            monto = Rounding.money(ibc_diario * Decimal("0.6667") * dias_3_90)
            tramos.append(TramoIncapacidad(dias_3_90, "EPS", Decimal("0.6667"), monto))

        dias_91_180 = max(0, min(dias_incapacidad, 180) - 90)
        if dias_91_180 > 0:
            monto = Rounding.money(ibc_diario * Decimal("0.50") * dias_91_180)
            tramos.append(TramoIncapacidad(dias_91_180, "EPS", Decimal("0.50"), monto))

        monto_empleador = next((t.monto for t in tramos if t.pagador == "EMPLEADOR"), Decimal("0.00"))
        return IncapacidadResult(tramos, monto_empleador)
```

**Límite conocido:** incapacidades comunes de más de 180 días (transición a pensión de invalidez) no se
modelan — fuera de alcance, no mencionado en el PDF ni en `Pendientes.md`.

## Wiring en `LaboralStrategy.liquidar()`

```python
eventos = LaborScheduler(...).generate()  # ya existente

if obligacion.incluir_seguridad_social:
    dias_suspension = sum(
        (e.fecha_fin - e.fecha_inicio).days
        for e in obligacion.eventos_laborales if e.tipo == TipoEventoLaboral.SUSPENSION
    )
    cotiz = SeguridadSocialCalculator.calcular(
        salario_base=obligacion.valor, dias_trabajados=Decimal(str(dias_trabajados)),
        dias_suspension=Decimal(str(dias_suspension)), nivel_riesgo_arl=obligacion.nivel_riesgo_arl,
        fecha_referencia=obligacion.fecha_fin,
    )
    for concepto, monto in [
        ("COTIZACION_PENSION", cotiz.monto_pension), ("COTIZACION_SALUD", cotiz.monto_salud),
        ("COTIZACION_ARL", cotiz.monto_arl), ("COTIZACION_FSP", cotiz.monto_fsp),
    ]:
        if monto > Decimal("0.00"):
            eventos.append(Event(date=obligacion.fecha_fin, payload={"amount": monto}, event_type=concepto))

    for e in obligacion.eventos_laborales:
        if e.tipo == TipoEventoLaboral.SUSPENSION:
            eventos.append(Event(
                date=e.fecha_fin,
                payload={"amount": Decimal("0.00"),
                         "label": f"Suspension ({e.motivo_suspension.value}) {e.fecha_inicio}-{e.fecha_fin}: no causa ARL"},
                event_type="SUSPENSION_INFORMATIVA",
            ))
        else:
            resultado = IncapacidadCalculator.calcular(
                e.tipo, cotiz.ibc_mensual, (e.fecha_fin - e.fecha_inicio).days
            )
            for tramo in resultado.tramos:
                es_empleador = tramo.pagador == "EMPLEADOR"
                eventos.append(Event(
                    date=e.fecha_fin,
                    payload={
                        "amount": tramo.monto if es_empleador else Decimal("0.00"),
                        "label": f"Incapacidad {e.tipo.value} dias {tramo.dias} - {tramo.pagador} ({tramo.porcentaje:.2%}): ${tramo.monto}",
                    },
                    event_type="INCAPACIDAD_EMPLEADOR" if es_empleador else "INCAPACIDAD_INFORMATIVA",
                ))
```

`app/engine/liquidation/engine.py`, `_capital_concepts` gana 6 entradas: `COTIZACION_PENSION`,
`COTIZACION_SALUD`, `COTIZACION_ARL`, `COTIZACION_FSP`, `INCAPACIDAD_EMPLEADOR`,
`SUSPENSION_INFORMATIVA`, `INCAPACIDAD_INFORMATIVA` (las 2 últimas siempre con `amount=0.00` — no alteran
el saldo, solo dejan traza auditable para el juez, mismo espíritu que el evento de corte
`LIQUIDATION_CUTOFF` ya existente).

`_validar_obligacion_laboral` gana una regla: si `incluir_seguridad_social` es `True`,
`nivel_riesgo_arl` no puede ser `None` (`ValueError` claro).

**No se toca el motor genérico** (`LiquidationCore`, `BalanceEngine`, `AllocationEngine`): todo el trabajo
nuevo vive en los calculadores puros y en el ensamblaje de eventos dentro de `LaboralStrategy`, exactamente
igual al patrón ya usado por `MoratoryIndemnityCalculator`.

## Catálogo de parámetros (`app/services/parametro_service.py`, modo `ABIERTO`)

12 claves nuevas en `CATALOGO_PARAMETROS`:

| Clave | Valor inicial | Fuente |
|---|---|---|
| `SS_PENSION_PCT` | 16% | PDF pág. 51 |
| `SS_SALUD_PCT` | 12.5% | PDF pág. 51 |
| `SS_ARL_NIVEL_I_PCT` | 0.522% | PDF pág. 52 |
| `SS_ARL_NIVEL_II_PCT` | 1.044% | Decreto 1607/2002 (PDF solo da extremos I y V) |
| `SS_ARL_NIVEL_III_PCT` | 2.436% | Decreto 1607/2002 |
| `SS_ARL_NIVEL_IV_PCT` | 4.350% | Decreto 1607/2002 |
| `SS_ARL_NIVEL_V_PCT` | 6.960% | PDF pág. 52 |
| `SS_FSP_TRAMO_1_PCT` (4-16 SMMLV) | 1% | Ley 797/2003 art. 8 (PDF solo da "desde 1% hasta 2%") |
| `SS_FSP_TRAMO_2_PCT` (16-17 SMMLV) | 1.2% | Ley 797/2003 art. 8 |
| `SS_FSP_TRAMO_3_PCT` (17-18 SMMLV) | 1.4% | Ley 797/2003 art. 8 |
| `SS_FSP_TRAMO_4_PCT` (18-19 SMMLV) | 1.6% | Ley 797/2003 art. 8 |
| `SS_FSP_TRAMO_5_PCT` (19-20 SMMLV) | 1.8% | Ley 797/2003 art. 8 |
| `SS_FSP_TRAMO_6_PCT` (>20 SMMLV) | 2% | Ley 797/2003 art. 8 |

Todas modo `ABIERTO` (cambian por reforma normativa, no por vigencia calendario anual — mismo modo que
`USURA_MULTIPLICADOR`, `CIVIL_ANNUAL_RATE`, etc.). Se cargan vía `agregar_valor()` desde la GUI de
configuración existente (`app/views/configuracion.py`), no requieren código nuevo en esa vista.

## GUI

- `app/views/obligaciones.py` (`ObligacionFormDialog`): cuando `area == "LABORAL"`, checkbox "Incluir
  cotizaciones de seguridad social no pagadas" + combo "Nivel de riesgo ARL" (I-V), visible solo si el
  checkbox está activo. `guardar()` escribe `incluir_seguridad_social` y `nivel_riesgo_arl`.
- Nuevo `app/views/eventos_laborales.py` → `EventoLaboralFormDialog`, mismo patrón que
  `app/views/abonos.py::AbonoFormDialog`: combo tipo (Suspensión / Incapacidad común / Incapacidad
  laboral), `QDateEdit` fecha inicio, `QDateEdit` fecha fin, combo motivo (habilitado solo si tipo ==
  Suspensión).
- `app/views/expediente_detalle.py`: nuevo `QGroupBox` "Eventos contractuales" (tabla + botón "Agregar
  evento"), visible solo si `expediente.area_derecho == AreaDerecho.LABORAL` — mismo patrón que el grupo
  de Abonos ya existente (`_refrescar_eventos_laborales()` análogo a `_refrescar_abonos()`).

## Fuera de alcance (explícito)

- Módulo de nómina corriente (PILA, afiliaciones periódicas) — confirmado con el usuario, decisión 1.
- Reclamación de las porciones EPS/ARL de incapacidad como deuda del empleador (ej. por no afiliación) —
  hecho distinto, ver PDF pág. 52 punto 6 ("No Afiliación a Pensiones"), no mencionado en el alcance
  incluido de `Pendientes.md` para este sprint.
- Régimen pensional (IBL, densidad de semanas, tasa de reemplazo) — Sprint 17.
- Incapacidades comunes de más de 180 días (transición a pensión de invalidez).
- Historial de SMMLV mes a mes para contratos multi-año (se usa una sola fotografía en `fecha_fin`, misma
  simplificación ya aceptada en Sprint 3).
- Contratos Laborales múltiples por expediente (restricción heredada del Sprint 3, no se toca).

## Testing

- `tests/engine/labor/test_seguridad_social.py`: cotización sin suspensión, con suspensión parcial (ARL
  excluido en esos días exactos), FSP activado en cada tramo (incluyendo el límite exacto de cada
  frontera de SMMLV) y no activado (IBC < 4 SMMLV), cada nivel ARL I-V, clamp de IBC en los límites 1 y 25
  SMMLV.
- `tests/engine/labor/test_incapacidad.py`: incapacidad común de 1, 2, 3, 90, 91 y 180 días (puntos de
  quiebre exactos de cada tramo), incapacidad laboral de cualquier duración (siempre 0 a cargo del
  empleador).
- `tests/services/test_area_strategy.py::TestLaboralStrategy`: casos combinados (contrato con seguridad
  social + suspensión + incapacidad simultáneas), validación de `nivel_riesgo_arl` faltante cuando
  `incluir_seguridad_social=True`, y el caso sin checkbox marcado (comportamiento idéntico al actual, sin
  regresión frente al Sprint 3).
- `tests/scripts/test_migrate_seguridad_social_laboral.py`: mismo patrón que
  `tests/scripts/test_migrate_moneda_trm.py` (idempotencia, columnas correctas).
- `tests/views/test_obligaciones.py` y un nuevo `tests/views/test_eventos_laborales.py`.
- Smoke test manual: expediente Laboral con seguridad social activada, un evento de suspensión y uno de
  incapacidad común cruzando el tramo 3-90, liquidar, confirmar que aparecen las líneas de cotización y
  las líneas informativas en el resultado, exportar a PDF/Word.

## Definición de hecho

- `SeguridadSocialCalculator` e `IncapacidadCalculator` con TDD, tests de los puntos de quiebre exactos
  (días 2/3, 90/91, 180, y fronteras de tramos FSP en SMMLV).
- `LaboralStrategy` liquida seguridad social + incapacidades + suspensiones cuando la obligación las tiene
  registradas, sin romper el comportamiento existente (Sprint 3) cuando no las tiene.
- Área Laboral con seguridad social operable end-to-end desde la GUI (smoke test manual).
- Suite completa en verde.
- `README.md` / `docs/GUIA_USUARIO.md` actualizados: documentar cómo capturar cotizaciones no pagadas,
  suspensiones e incapacidades en un expediente Laboral.
- `Pendientes.md`: marcar Sprint 16 como completado.
