from datetime import date, datetime
from decimal import Decimal

import database.session as session_module
from app.engine.indexation.historical_index import _IPC_INDICE_ACUMULADO
from app.engine.liquidation.models import PendingDebt
from app.services.area_strategy import CivilFamiliaStrategy
from app.services.cascada_cuotas import deuda_pendiente_cuota, distribuir_pago_en_cascada
from app.services.reajuste_anual import generar_cuotas_mensuales
from database.models import Obligacion, ParametroLegal, TipoObligacion, TipoReajusteAnual


def _deuda(principal: str, interest: str) -> PendingDebt:
    return PendingDebt(
        principal=Decimal(principal), interest=Decimal(interest), indexation=Decimal("0.00")
    )


def _obligacion_civil_familia_recurrente_persistida(
    valor: Decimal,
    fecha_inicio: date,
    tasa_efectiva_anual: Decimal,
    tipo_reajuste_anual: TipoReajusteAnual,
    expediente_id: int = 1,
    aplica_indexacion_ipc: bool = False,
) -> Obligacion:
    """Persiste una obligacion RECURRENTE de Civil/Familia en la sesion en memoria
    (fixture autouse `_db_en_memoria_por_defecto` de tests/conftest.py) -- necesario
    porque `generar_cuotas_mensuales` (Sprint 41/75) requiere una obligacion con `id`
    real para poder generar y persistir las cuotas hijas. Mismo patron que
    tests/services/test_area_strategy.py::_obligacion_civil_familia_recurrente_persistida."""
    session = session_module.get_session()
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="CUOTA ALIMENTARIA",
        categoria="CHILD_SUPPORT",
        fecha_origen=fecha_inicio,
        fecha_inicio=fecha_inicio,
        dia_pago=fecha_inicio.day,
        valor=valor,
        tasa_efectiva_anual=tasa_efectiva_anual,
        tipo_reajuste_anual=tipo_reajuste_anual,
        aplica_indexacion_ipc=aplica_indexacion_ipc,
    )
    session.add(obligacion)
    session.commit()
    session.close()
    return obligacion


def test_ejemplo_del_usuario_abril_marzo_febrero():
    # Reproduce la mecanica del ejemplo del usuario (capital de la cuota mas
    # reciente primero, luego capital+interes de las anteriores, y solo una
    # parte de los intereses de la cuota mas antigua si el pago no alcanza
    # para todo) con montos elegidos a mano para que la aritmetica cierre
    # exacto -- no se derivan de una tasa anual real, eso se prueba aparte en
    # el test de integracion (Task 6).
    cuotas_y_deuda = [
        ("abril", _deuda("150000.00", "0.00")),
        ("marzo", _deuda("150000.00", "20000.00")),
        ("febrero", _deuda("150000.00", "45000.00")),
    ]
    asignaciones, remanente = distribuir_pago_en_cascada(
        cuotas_y_deuda, Decimal("500000.00"), date(2024, 4, 1)
    )

    # abril: 150.000 de capital, interes 0 (recien nace ese dia).
    # marzo: 150.000 capital + 20.000 interes completo = 170.000.
    # febrero: 150.000 capital + solo 30.000 de sus 45.000 de interes = 180.000
    #          (los 15.000 restantes de interes de febrero quedan debidos, pero
    #          su capital ya esta pagado y no genera intereses nuevos).
    assert asignaciones[0][1] == Decimal("150000.00")  # abril
    assert asignaciones[1][1] == Decimal("170000.00")  # marzo
    assert asignaciones[2][1] == Decimal("180000.00")  # febrero
    assert sum(monto for _, monto in asignaciones) == Decimal("500000.00")
    assert remanente == Decimal("0.00")


def test_pago_exacto_para_una_sola_cuota_no_toca_la_siguiente():
    cuotas_y_deuda = [
        ("marzo", _deuda("150000.00", "0.00")),
        ("febrero", _deuda("150000.00", "3000.00")),
    ]
    asignaciones, remanente = distribuir_pago_en_cascada(
        cuotas_y_deuda, Decimal("150000.00"), date(2024, 3, 1)
    )
    assert len(asignaciones) == 1
    assert asignaciones[0][1] == Decimal("150000.00")
    assert remanente == Decimal("0.00")


def test_remanente_sobrante_cuando_el_pago_excede_todas_las_cuotas():
    cuotas_y_deuda = [("marzo", _deuda("150000.00", "0.00"))]
    asignaciones, remanente = distribuir_pago_en_cascada(
        cuotas_y_deuda, Decimal("200000.00"), date(2024, 3, 1)
    )
    assert asignaciones[0][1] == Decimal("150000.00")
    assert remanente == Decimal("50000.00")


def test_deuda_pendiente_cuota_refleja_capital_e_interes_reales():
    obligacion_recurrente = _obligacion_civil_familia_recurrente_persistida(
        valor=Decimal("150000.00"),
        fecha_inicio=date(2024, 1, 1),
        tasa_efectiva_anual=Decimal("12.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 3, 1))
    cuota_enero = next(c for c in cuotas if c.fecha_origen == date(2024, 1, 1))

    rate_provider = CivilFamiliaStrategy()._construir_rate_provider_obligacion(
        cuota_enero, date(2024, 3, 1)
    )
    deuda = deuda_pendiente_cuota(
        cuota_enero, abonos_existentes=[], fecha_pago=date(2024, 3, 1), rate_provider=rate_provider
    )
    assert deuda.principal == Decimal("150000.00")
    assert deuda.interest > Decimal("0.00")  # 2 meses de mora al 12% anual


def _sembrar_ipc_indice_acumulado() -> None:
    """CivilFamiliaStrategy._evento_indexacion (app/services/area_strategy.py) lee
    IPC_INDICE_ACUMULADO via parametro_service en cada liquidar() -- se siembra desde
    el mismo diccionario congelado que consume scripts/migrate_parametros_legales.py,
    mismo patron que tests/services/test_area_strategy.py::_parametros_legales_en_memoria."""
    session = session_module.get_session()
    for anio, valor in _IPC_INDICE_ACUMULADO.items():
        session.add(
            ParametroLegal(
                clave="IPC_INDICE_ACUMULADO",
                valor=valor,
                vigente_desde=date(anio, 1, 1),
                vigente_hasta=None,
                usuario="test",
                motivo=None,
                creado_en=datetime.now(),
            )
        )
    session.commit()
    session.close()


def test_deuda_pendiente_cuota_incluye_indexacion_ipc_cuando_aplica():
    # generar_cuotas_mensuales copia aplica_indexacion_ipc del padre RECURRENTE a
    # cada cuota-hija (es un juicio legal del abogado, independiente de
    # tipo_reajuste_anual -- ver app/services/reajuste_anual.py). Una cuota con
    # tipo_reajuste_anual=NINGUNO puede igual tener aplica_indexacion_ipc=True, y
    # CivilFamiliaStrategy._eventos_de_obligacion (rama PUNTUAL) le agrega un
    # segundo evento INDEXATION ademas del capital base -- deuda_pendiente_cuota
    # debe reflejar eso mismo en su proyeccion, o "proyectado" y "liquidado de
    # verdad" divergen (ver docstring del modulo).
    _sembrar_ipc_indice_acumulado()
    obligacion_recurrente = _obligacion_civil_familia_recurrente_persistida(
        valor=Decimal("150000.00"),
        fecha_inicio=date(2024, 1, 1),
        tasa_efectiva_anual=Decimal("12.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
        aplica_indexacion_ipc=True,
    )
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 3, 1))
    cuota_enero = next(c for c in cuotas if c.fecha_origen == date(2024, 1, 1))
    assert cuota_enero.aplica_indexacion_ipc is True

    rate_provider = CivilFamiliaStrategy()._construir_rate_provider_obligacion(
        cuota_enero, date(2024, 3, 1)
    )
    deuda = deuda_pendiente_cuota(
        cuota_enero, abonos_existentes=[], fecha_pago=date(2024, 3, 1), rate_provider=rate_provider
    )

    # La misma cuota, liquidada de verdad por la estrategia de produccion (la
    # unica obligacion en la lista -> _fusionar_resultados colapsa a identidad,
    # ver app/services/area_strategy.py::_fusionar_resultados) debe llegar
    # exactamente al mismo PendingDebt que proyecto deuda_pendiente_cuota.
    resultado_real = CivilFamiliaStrategy().liquidar(
        obligaciones=[cuota_enero], abonos=[], fecha_corte=date(2024, 3, 1)
    )
    esperado = resultado_real.final_balance()

    assert deuda.indexation > Decimal("0.00")
    assert deuda == esperado
