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
        salario_base=Decimal("1000000.00"),
        dias_trabajados=180,
        fecha_liquidacion=date(2025, 7, 15),
    )
    events = scheduler.generate()

    assert all(e.date == date(2025, 7, 15) for e in events)

    cesantias = next(e for e in events if e.event_type == "CESANTIAS")
    assert cesantias.payload["amount"] == Decimal("500000.00")  # (1M*180)/360

    vacaciones = next(e for e in events if e.event_type == "VACACIONES")
    assert vacaciones.payload["amount"] == Decimal("250000.00")  # (1M*180)/720


def test_labor_scheduler_auxilio_transporte_entra_en_base_de_cesantias_y_prima_no_vacaciones():
    # Sprint 96 (seguimiento), respuesta del despacho (23/08/2026): el auxilio
    # de transporte "forma parte obligatoria de la base de liquidacion para
    # cesantias y prima de servicios" -- no menciona vacaciones, que siguen
    # sobre el salario solo.
    # Salario 1.000.000 + auxilio 100.000 = base 1.100.000, 360 dias:
    #   cesantias  = 1.100.000 x 360 / 360        = 1.100.000,00
    #   intereses  = 1.100.000 x 360 x 0,12 / 360 =   132.000,00
    #   prima (x2) = 1.100.000 x 180 / 360        =   550.000,00
    #   vacaciones = 1.000.000 x 360 / 720        =   500.000,00 (sin auxilio)
    scheduler = LaborScheduler(
        salario_base=Decimal("1000000.00"),
        dias_trabajados=360,
        fecha_liquidacion=date(2025, 12, 31),
        auxilio_transporte=Decimal("100000.00"),
    )
    events = {e.event_type: e for e in scheduler.generate()}

    assert events["CESANTIAS"].payload["amount"] == Decimal("1100000.00")
    assert events["INTERESES_CESANTIAS"].payload["amount"] == Decimal("132000.00")
    assert events["PRIMA_JUNIO"].payload["amount"] == Decimal("550000.00")
    assert events["PRIMA_DICIEMBRE"].payload["amount"] == Decimal("550000.00")
    assert events["VACACIONES"].payload["amount"] == Decimal("500000.00")
    # Rastro de auditoria: la etiqueta de cesantias/prima declara el auxilio.
    assert "auxilio de transporte" in events["CESANTIAS"].payload["label"]
    assert "auxilio de transporte" in events["PRIMA_JUNIO"].payload["label"]
    assert "label" not in events["VACACIONES"].payload


def test_labor_scheduler_sin_auxilio_no_agrega_etiquetas():
    # Sin auxilio (por defecto), los eventos quedan exactamente como antes.
    events = LaborScheduler(
        salario_base=Decimal("1000000.00"),
        dias_trabajados=360,
        fecha_liquidacion=date(2025, 12, 31),
    ).generate()
    assert all("label" not in e.payload for e in events)
