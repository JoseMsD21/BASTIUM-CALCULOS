"""Sprint 93: salarios y prestaciones sociales dejadas de percibir, con
reajuste anual IPC o SMMLV -- reabre la exclusion que el Sprint 75 dejo
explicita para el area Laboral (docs/Pendientes.md, Sprint 93).

Contexto (ver el propio sprint para el detalle completo): las plantillas del
despacho `L5...(incrementoinflacion).md`/`L6...(incremento-salario-minimo).md`
NO liquidan el finiquito de un contrato -- reconstruyen el salario y las
prestaciones sociales que un trabajador habria devengado durante un periodo en
que NO estuvo contratado (tipicamente reintegro por despido declarado nulo, o
"salarios caidos"), año calendario por año calendario, con el salario
reajustado el 1 de enero de cada año segun un indice (L5: IPC: L6: SMMLV), y
sumado todo en un "GRAN TOTAL".

Decision de diseno (Sprint 93, sin necesitar confirmacion del despacho -- ver
el docstring de LaboralStrategy._eventos_salarios_dejados_de_percibir en
app/services/area_strategy.py para el razonamiento completo sobre por que esto
no rompe el invariante "1 obligacion = 1 contrato" del Sprint 3): a diferencia
de `generar_cuotas_mensuales` (reajuste_anual.py, Sprint 41/75), que persiste
una Obligacion PUNTUAL hija por cada MES, este modulo no persiste nada -- los
bloques son ANUALES (no mensuales, esa es la estructura real de L5/L6) y se
recalculan en memoria en cada liquidacion a partir de los 4 campos que ya trae
la Obligacion RECURRENTE (fecha_inicio, fecha_fin, valor, tipo_reajuste_anual),
sin necesitar una tabla de hijas ni un boton "Generar cuotas" -- mucho mas
simple que el modelo de Civil/Familia porque aqui no hay pagos periodicos
reales que abonar mes a mes, solo una reconstruccion retroactiva que se
liquida de una sola vez.

Reutiliza sin reimplementar:
  - `reajustar_capital_anual` (app/services/reajuste_anual.py, Sprint 41/75):
    la formula de reajuste IPC/SMMLV es identica a la que ya usa Civil/Familia,
    aplicada aqui al salario en vez de a una cuota alimentaria.
  - `CalendarUtils.dias_comerciales_360` (Sprint 30): el mismo conteo "mes
    comercial de 30 dias" que ya usa LaboralStrategy para un finiquito normal.
  - `LaborScheduler` (app/engine/temporal/schedulers/labor.py, Sprint 3): los
    mismos divisores 360 (cesantias/intereses/prima) y 720 (vacaciones) que ya
    usa un finiquito normal, aplicados aqui bloque de año por bloque de año en
    vez de una unica vez al final del contrato -- cada bloque anual es, en los
    hechos, un "mini-finiquito" del tramo de ese año.

El salario mismo tambien se debe -- el titulo de L5/L6 es "SALARIOS Y
PRESTACIONES SOCIALES dejadas de percibir", no solo prestaciones -- por eso
cada bloque agrega ademas un evento SALARIO_DEJADO_DE_PERCIBIR =
salario_del_bloque * dias_bloque / 30 (la misma convencion de "mes comercial
de 30 dias" que dias_comerciales_360 ya usa para cesantias/prima, aplicada al
salario en vez de solo a las prestaciones -- con dias_bloque == 360 esto se
reduce, exactamente, a 12 meses de salario completo).
"""

from datetime import date
from decimal import Decimal

from app.engine.math.rounding import Rounding
from app.engine.temporal.schedulers.base import Event
from app.engine.temporal.schedulers.labor import LaborScheduler
from app.engine.time.calendar import CalendarUtils
from app.services.reajuste_anual import reajustar_capital_anual
from database.models import TipoReajusteAnual


def generar_eventos_salarios_dejados_de_percibir(
    salario_inicial: Decimal,
    fecha_inicio: date,
    fecha_fin: date,
    tipo_reajuste: TipoReajusteAnual,
) -> list[Event]:
    """Genera, en memoria (sin tocar la base de datos), la lista completa de
    eventos de capital (SALARIO_DEJADO_DE_PERCIBIR + CESANTIAS +
    INTERESES_CESANTIAS + PRIMA_JUNIO + PRIMA_DICIEMBRE + VACACIONES) de un
    bloque por cada año calendario entre `fecha_inicio` y `fecha_fin`
    (inclusive en ambos extremos), con el salario reajustado el 1 de enero de
    cada año siguiente al de `fecha_inicio` segun `tipo_reajuste`. Sumar
    `payload["amount"]` de todos los eventos retornados da el "GRAN TOTAL" de
    L5/L6.

    Con `tipo_reajuste == TipoReajusteAnual.NINGUNO` el salario permanece
    constante en todos los bloques (igual criterio que
    `generar_cuotas_mensuales`, Sprint 75 Task 1) -- reajustar_capital_anual
    sigue lanzando ValueError para NINGUNO (no le corresponde a ella decidir
    si reajusta, ver su propio docstring), asi que el guard vive aqui, igual
    que en `generar_cuotas_mensuales`.
    """
    if fecha_fin <= fecha_inicio:
        raise ValueError(
            f"'fecha_fin' ({fecha_fin}) debe ser posterior a 'fecha_inicio' ({fecha_inicio})."
        )
    if salario_inicial is None or salario_inicial <= Decimal("0.00"):
        raise ValueError("El salario base debe ser mayor que cero.")

    eventos: list[Event] = []
    salario_actual = salario_inicial
    anio_capital = fecha_inicio.year

    for anio in range(fecha_inicio.year, fecha_fin.year + 1):
        # Reajuste anual: se dispara exactamente una vez por año, al entrar a
        # un año distinto del ultimo ya reajustado -- mismo criterio de
        # `generar_cuotas_mensuales` (reajuste_anual.py), aqui por año
        # calendario en vez de por mes.
        if anio != anio_capital and tipo_reajuste != TipoReajusteAnual.NINGUNO:
            salario_actual = reajustar_capital_anual(salario_actual, anio, tipo_reajuste)
        anio_capital = anio

        bloque_desde = fecha_inicio if anio == fecha_inicio.year else date(anio, 1, 1)
        bloque_hasta = fecha_fin if anio == fecha_fin.year else date(anio, 12, 31)
        dias_bloque = CalendarUtils.dias_comerciales_360(bloque_desde, bloque_hasta)

        monto_salario_bloque = Rounding.money(
            salario_actual * Decimal(dias_bloque) / Decimal("30")
        )
        eventos.append(
            Event(
                date=bloque_hasta,
                payload={
                    "amount": monto_salario_bloque,
                    "label": (
                        f"Salario dejado de percibir {bloque_desde.isoformat()} a "
                        f"{bloque_hasta.isoformat()}"
                    ),
                },
                event_type="SALARIO_DEJADO_DE_PERCIBIR",
            )
        )
        eventos.extend(
            LaborScheduler(
                salario_base=salario_actual,
                dias_trabajados=dias_bloque,
                fecha_liquidacion=bloque_hasta,
            ).generate()
        )

    return eventos
