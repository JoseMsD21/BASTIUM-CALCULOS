"""Task 3 del Sprint 41 (bloqueante para la Task 4 / UI, ver el plan
docs/superpowers/plans/2026-08-07-sprint41-familia-cuotas-reajuste-anual.md,
seccion "Architecture" punto 4): verifica que el interes de mora de cada cuota
generada por app/services/reajuste_anual.py queda calculado correctamente
"de forma autonoma" (capital propio de esa cuota x sus propios dias de mora)
una vez que las cuotas se persisten como Obligacion PUNTUAL reales y se dejan
liquidar por el motor consolidado existente (CivilFamiliaStrategy.liquidar()),
SIN que haga falta construir un motor de interes nuevo "por cuota".

Razonamiento (ver Architecture punto 4 del plan): desde el Sprint 21,
CivilFamiliaStrategy.liquidar() ya corre cada Obligacion en su PROPIO
LiquidationCore aislado (ver _liquidar_por_obligacion en area_strategy.py) y
solo despues funde los N resultados en una sola linea de tiempo consolidada
(_fusionar_resultados), sumando el interes de cada obligacion en cada fila.
Esto significa que, para N cuotas sin abonos, el interes final consolidado
de LiquidationCore YA ES, por construccion, la suma de N calculos de interes
completamente independientes -- uno por cuota, sobre su propio capital y sus
propios dias de mora. Este test lo verifica con numeros concretos.

Nota de metodologia (hallazgo de esta tarea): la comparacion "aislada" debe
reproducir el mismo bucle dia-a-dia que usa
LiquidationCore._accrue_time_passage (que llama a DailyInterest.calculate
UNA VEZ POR DIA y redondea a centavos cada dia, antes de sumar) -- NO basta
con llamar a DailyInterest.calculate(capital, tasa_diaria, dias=N) una sola
vez con el total de dias. Se verifico empiricamente (ver bash scratch del
sprint) que para este mismo escenario de 3 cuotas la variante "un solo
calculo por cuota" da $9,157.49 mientras que el motor consolidado da
$9,158.12 -- una diferencia de $0.63 que es puramente un artefacto de
granularidad de redondeo (rediondear una vez el total de ~200 dias de interes
no es lo mismo que redondear a centavos cada uno de esos ~200 dias y sumar),
no una discrepancia en la arquitectura de "cuotas como Obligacion
independientes". La reproduccion dia-a-dia de abajo SI coincide de forma
exacta con el motor, porque es literalmente el mismo calculo.
"""

from datetime import date, timedelta
from decimal import Decimal

import database.session as session_module
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.services.area_strategy import CivilFamiliaStrategy
from database.models import AreaDerecho, Expediente, Obligacion, TipoObligacion


def _interes_aislado_dia_a_dia(
    capital: Decimal, tasa_efectiva_anual: Decimal, fecha_origen: date, fecha_corte: date
) -> Decimal:
    """Reproduce EXACTAMENTE el bucle de LiquidationCore._accrue_time_passage
    (engine.py) para una sola obligacion sin abonos: interes diario calculado
    y redondeado a centavos dia por dia (DailyInterest.calculate con days=1),
    acumulado desde el dia siguiente a fecha_origen hasta fecha_corte
    inclusive. Este es el calculo "autonomo" real de la cuota, aislado de
    cualquier otra obligacion del expediente."""
    daily_rate = EffectiveRateConverter.annual_to_daily(tasa_efectiva_anual)
    total = Decimal("0.00")
    dia = fecha_origen + timedelta(days=1)
    while dia <= fecha_corte:
        total += DailyInterest.calculate(capital=capital, daily_rate=daily_rate, days=1)
        dia += timedelta(days=1)
    return total


def _expediente_con_tres_cuotas(session) -> tuple[int, list[tuple[Decimal, date]]]:
    expediente = Expediente(
        radicado="2026-041-A",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2025, 6, 1),
    )
    session.add(expediente)
    session.flush()

    # 3 "cuotas" (capital distinto cada una, como si vinieran de
    # generar_cuotas_mensuales con reajuste SMMLV entre 2024 y 2025) creadas a
    # mano como Obligacion PUNTUAL -- equivalente sintetico permitido por el
    # plan (no depende del servicio de la Task 2 para aislar la verificacion
    # matematica de esta Task 3).
    datos = [
        (Decimal("100000.00"), date(2024, 11, 5)),
        (Decimal("110000.00"), date(2024, 12, 5)),
        (Decimal("115500.00"), date(2025, 1, 5)),
    ]
    for capital, fecha in datos:
        session.add(
            Obligacion(
                expediente_id=expediente.id,
                tipo=TipoObligacion.PUNTUAL,
                concepto=f"Cuota {fecha.isoformat()}",
                categoria="CHILD_SUPPORT",
                fecha_origen=fecha,
                valor=capital,
                tasa_efectiva_anual=Decimal("6.00"),
            )
        )
    session.commit()
    return expediente.id, datos


def test_interes_consolidado_coincide_con_suma_de_interes_aislado_por_cuota():
    session = session_module.get_session()
    expediente_id, datos = _expediente_con_tres_cuotas(session)
    fecha_corte = date(2025, 6, 1)
    obligaciones = list(session.get(Expediente, expediente_id).obligaciones)
    session.close()

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=obligaciones, abonos=[], fecha_corte=fecha_corte
    )
    interes_consolidado = resultado.final_balance().interest

    interes_aislado_total = sum(
        (
            _interes_aislado_dia_a_dia(capital, Decimal("6.00"), fecha, fecha_corte)
            for capital, fecha in datos
        ),
        Decimal("0.00"),
    )

    # La afirmacion central de la Task 3: el interes que produce el motor
    # consolidado real (3 obligaciones en el mismo expediente, fundidas por
    # _fusionar_resultados) es EXACTAMENTE igual a la suma de 3 calculos de
    # interes completamente aislados, cada uno sobre su propio capital y sus
    # propios dias de mora. Si esto fallara, generar cuotas como Obligacion
    # reales y dejarlas liquidar por el motor existente NO seria equivalente
    # a un motor de interes "autonomo por cuota" -- habria que escalar antes
    # de construir la Task 4 (UI). Coincide exactamente: $9,158.12 en ambos
    # lados para este escenario.
    assert interes_consolidado == interes_aislado_total
    assert interes_consolidado == Decimal("9158.12")


def test_interes_de_cada_cuota_individual_no_se_contamina_con_el_capital_de_las_otras():
    """Complemento del test anterior: el capital_base de la PRIMERA fila (la
    causacion de la cuota de noviembre 2024) debe ser solo el capital de esa
    cuota (100000.00), no la suma de las 3 -- confirma que, antes de que la
    segunda/tercera cuota exista, el interes de la primera se calculo sin
    contaminacion del capital de las que todavia no se habian causado (la
    propiedad "aditiva por tramos" descrita en Architecture punto 4 del
    plan)."""
    session = session_module.get_session()
    expediente_id, _datos = _expediente_con_tres_cuotas(session)
    fecha_corte = date(2025, 6, 1)
    obligaciones = list(session.get(Expediente, expediente_id).obligaciones)
    session.close()

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=obligaciones, abonos=[], fecha_corte=fecha_corte
    )

    primera_fila = min(
        (item for item in resultado.items if item.balance.event_type == "CHILD_SUPPORT"),
        key=lambda item: item.date,
    )
    assert primera_fila.date == date(2024, 11, 5)
    assert primera_fila.balance.debt.principal == Decimal("100000.00")
