from datetime import date
from decimal import Decimal

from app.engine.temporal.schedulers.labor import LaborScheduler


def test_labor_scheduler_liquidacion_final_contrato_de_un_anio_completo():
    # Escenario: contrato de un año completo (360 dias trabajados en la
    # convencion comercial), terminado el 2025-12-31. En el modelo de
    # finiquito, TODAS las prestaciones son exigibles ese mismo dia.
    salario = Decimal("1500000.00")
    dias_trabajados = 360
    fecha_liquidacion = date(2025, 12, 31)

    scheduler = LaborScheduler(
        salario_base=salario, dias_trabajados=dias_trabajados, fecha_liquidacion=fecha_liquidacion
    )
    events = scheduler.generate()

    assert len(events) == 5
    assert all(e.date == fecha_liquidacion for e in events)

    cesantias = next(e for e in events if e.event_type == "CESANTIAS")
    assert cesantias.payload["amount"] == Decimal("1500000.00")

    int_cesantias = next(e for e in events if e.event_type == "INTERESES_CESANTIAS")
    assert int_cesantias.payload["amount"] == Decimal("180000.00")  # 1.5M * 12%

    prima_junio = next(e for e in events if e.event_type == "PRIMA_JUNIO")
    assert prima_junio.payload["amount"] == Decimal("750000.00")

    prima_dic = next(e for e in events if e.event_type == "PRIMA_DICIEMBRE")
    assert prima_dic.payload["amount"] == Decimal("750000.00")

    vacaciones = next(e for e in events if e.event_type == "VACACIONES")
    assert vacaciones.payload["amount"] == Decimal("750000.00")  # (1.5M*360)/720


def test_labor_scheduler_dias_proporcionales():
    # Escenario: trabajo parcial de 180 dias, contrato terminado el 2025-07-15.
    scheduler = LaborScheduler(
        salario_base=Decimal("1000000.00"), dias_trabajados=180, fecha_liquidacion=date(2025, 7, 15)
    )
    events = scheduler.generate()

    assert all(e.date == date(2025, 7, 15) for e in events)

    cesantias = next(e for e in events if e.event_type == "CESANTIAS")
    assert cesantias.payload["amount"] == Decimal("500000.00")  # (1M*180)/360

    vacaciones = next(e for e in events if e.event_type == "VACACIONES")
    assert vacaciones.payload["amount"] == Decimal("250000.00")  # (1M*180)/720
