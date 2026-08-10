"""Task 5 del Sprint 41 (verificacion final): escenario sintetico equivalente
al caso Aranda reportado por el usuario -- cuota alimentaria base, reajuste
SMMLV a traves de un cambio de año, y mora calculada por cuota individual,
incluyendo un abono parcial sobre UNA sola cuota. No reproduce el PDF real de
la demanda (no esta disponible, ver el encabezado del plan del Sprint 41) --
usa la misma mecanica (tasa fija, reajuste SMMLV anual) con cifras sinteticas
redondas para poder verificar el resultado exacto a mano.

Ejercita el pipeline COMPLETO de este sprint de punta a punta:
Task 1 (schema) -> Task 2 (generar_cuotas_mensuales, persistencia real) ->
Task 4 (CivilFamiliaStrategy usa las cuotas hijas reales, sin duplicar el
capital de la obligacion padre) -> abono capturado contra el obligacion_id de
UNA cuota especifica (mismo mecanismo que usa AbonoFormDialog, sin campo
nuevo en Abono).
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import database.session as session_module
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.services.area_strategy import CivilFamiliaStrategy
from app.services.reajuste_anual import generar_cuotas_mensuales
from database.models import (
    Abono,
    AreaDerecho,
    Expediente,
    Obligacion,
    ParametroLegal,
    TipoObligacion,
    TipoReajusteAnual,
)

_TASA_EFECTIVA_ANUAL = Decimal("6.00")


def _interes_aislado_dia_a_dia(capital: Decimal, fecha_origen: date, fecha_fin: date) -> Decimal:
    """Misma reproduccion fiel de LiquidationCore._accrue_time_passage que usa
    tests/family/test_interes_autonomo_por_cuota.py (Task 3): interes diario
    redondeado a centavos dia por dia, sumado desde el dia siguiente a
    fecha_origen hasta fecha_fin inclusive."""
    daily_rate = EffectiveRateConverter.annual_to_daily(_TASA_EFECTIVA_ANUAL)
    total = Decimal("0.00")
    dia = fecha_origen + timedelta(days=1)
    while dia <= fecha_fin:
        total += DailyInterest.calculate(capital=capital, daily_rate=daily_rate, days=1)
        dia += timedelta(days=1)
    return total


def _sembrar_smlmv_sintetico(session) -> None:
    # Cifras redondas sinteticas (no la serie SMLMV real -- ver docstring del
    # modulo): 2023 -> 2024 sube 10%, para poder verificar a mano el capital
    # reajustado de cada año.
    session.add(
        ParametroLegal(
            clave="SMLMV",
            valor=Decimal("1000000.00"),
            vigente_desde=date(2023, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    session.add(
        ParametroLegal(
            clave="SMLMV",
            valor=Decimal("1100000.00"),
            vigente_desde=date(2024, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )


def _crear_expediente_y_obligacion_recurrente(session) -> tuple[int, int]:
    expediente = Expediente(
        radicado="2026-041-ARANDA-SINTETICO",
        demandante="Demandante sintetico",
        demandado="Demandado sintetico",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2024, 2, 5),
    )
    session.add(expediente)
    session.flush()
    padre = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="CUOTA ALIMENTARIA",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2023, 11, 5),
        fecha_inicio=date(2023, 11, 5),
        dia_pago=5,
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=_TASA_EFECTIVA_ANUAL,
        tipo_reajuste_anual=TipoReajusteAnual.SMMLV,
    )
    session.add(padre)
    session.commit()
    return expediente.id, padre.id


def test_caso_sintetico_capital_correcto_por_anio_y_mora_independiente_con_abono_en_una_cuota():
    fecha_corte = date(2024, 2, 5)

    session = session_module.get_session()
    _sembrar_smlmv_sintetico(session)
    expediente_id, padre_id = _crear_expediente_y_obligacion_recurrente(session)
    session.close()

    # --- Task 2: generar y persistir las cuotas reales -----------------------
    session = session_module.get_session()
    padre = session.get(Obligacion, padre_id)
    cuotas = generar_cuotas_mensuales(padre, fecha_corte=fecha_corte)
    session.close()

    # 4 cuotas: nov/dic 2023 (año de origen, sin reajustar) + ene/feb 2024
    # (reajustadas +10%, capital constante el resto del año).
    assert len(cuotas) == 4
    por_fecha = {c.fecha_origen: c for c in cuotas}
    assert por_fecha[date(2023, 11, 5)].valor == Decimal("500000.00")
    assert por_fecha[date(2023, 12, 5)].valor == Decimal("500000.00")
    assert por_fecha[date(2024, 1, 5)].valor == Decimal("550000.00")
    assert por_fecha[date(2024, 2, 5)].valor == Decimal("550000.00")

    # --- Abono parcial sobre UNA sola cuota (la de noviembre 2023) -----------
    # Capturado contra el obligacion_id de esa cuota especifica -- mismo
    # mecanismo que AbonoFormDialog, sin ningun campo nuevo en Abono. Monto
    # deliberadamente menor al interes ya causado por esa cuota en la fecha del
    # abono (ver la asercion mas abajo), para que la imputacion legal
    # (indexacion -> intereses -> capital, AllocationEngine) quede
    # integramente en intereses y el capital de la cuota no se toque -- asi la
    # comparacion contra el calculo aislado es exacta y no depende de
    # reconstruir la prelacion de pagos a mano.
    cuota_noviembre = por_fecha[date(2023, 11, 5)]
    fecha_abono = date(2024, 1, 15)
    monto_abono = Decimal("5000.00")
    interes_causado_cuota_noviembre_al_abono = _interes_aislado_dia_a_dia(
        cuota_noviembre.valor, cuota_noviembre.fecha_origen, fecha_abono
    )
    assert monto_abono < interes_causado_cuota_noviembre_al_abono

    session = session_module.get_session()
    session.add(
        Abono(
            obligacion_id=cuota_noviembre.id,
            fecha=fecha_abono,
            monto=monto_abono,
            referencia="Abono parcial",
        )
    )
    session.commit()
    session.close()

    # --- Task 4: liquidar el expediente completo (padre + 4 cuotas + abono) --
    session = session_module.get_session()
    expediente = session.get(Expediente, expediente_id)
    obligaciones = list(expediente.obligaciones)
    abonos = [abono for obligacion in obligaciones for abono in obligacion.abonos]
    session.close()

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=obligaciones, abonos=abonos, fecha_corte=fecha_corte
    )

    # El abono se aplico (a la cuota correcta, no se perdio ni se duplico).
    assert resultado.total_payments_applied() == monto_abono

    # Capital: la obligacion RECURRENTE padre no aporta nada (Task 4 -- ya
    # tiene cuotas hijas generadas), y el abono se absorbio integramente en
    # intereses -- el capital de las 4 cuotas queda intacto.
    capital_esperado = sum((cuota.valor for cuota in cuotas), Decimal("0.00"))
    assert capital_esperado == Decimal("2100000.00")
    assert resultado.final_balance().principal == capital_esperado

    # Mora independiente por cuota: el interes final consolidado debe ser
    # exactamente la suma de los 4 calculos aislados por cuota, MENOS el
    # monto del abono (que redujo integramente el interes ya causado de la
    # cuota de noviembre, sin afectar en nada a las otras 3 -- ni su capital
    # ni su propio interes, que sigue acumulando sobre el mismo capital sin
    # importar cuando se pago el interes de OTRA cuota. Este es el mismo
    # principio verificado en la Task 3
    # (tests/family/test_interes_autonomo_por_cuota.py), aqui extendido a un
    # escenario con reajuste anual real y un abono parcial de por medio.
    interes_aislado_total_sin_abonos = sum(
        (
            _interes_aislado_dia_a_dia(cuota.valor, cuota.fecha_origen, fecha_corte)
            for cuota in cuotas
        ),
        Decimal("0.00"),
    )
    interes_consolidado_esperado = interes_aislado_total_sin_abonos - monto_abono
    assert resultado.final_balance().interest == interes_consolidado_esperado
    # Cifra concreta (verificada a mano, ver el comentario del modulo): sirve
    # de ancla adicional si algun cambio futuro en el motor altera el redondeo
    # dia a dia sin que ninguna de las asercions de arriba lo capture.
    assert resultado.final_balance().interest == Decimal("10015.93")
