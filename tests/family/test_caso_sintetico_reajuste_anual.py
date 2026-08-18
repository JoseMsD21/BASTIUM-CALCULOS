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

Actualizado en el Sprint 75 (Task 2, orden de imputacion intercambiable): el
abono de este escenario recae sobre una cuota-hija real (obligacion_padre_id
seteado), asi que desde ese sprint se liquida con capital-primero
(AllocationEngine.allocate_capital_primero) en vez de la imputacion legal
general (indexacion -> intereses -> capital) -- ver el comentario junto al
abono mas abajo.
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
    # deliberadamente menor tanto al interes ya causado como al capital de esa
    # cuota (ver la asercion mas abajo). Antes del Sprint 75 esto habria
    # importado para garantizar que la imputacion legal general (indexacion ->
    # intereses -> capital) dejara el abono integramente en intereses -- pero
    # desde el Sprint 75 (Task 2), toda cuota-hija (Obligacion PUNTUAL generada
    # por generar_cuotas_mensuales, obligacion_padre_id seteado, como
    # cuota_noviembre aqui) liquida sus propios abonos con capital-primero
    # (AllocationEngine.allocate_capital_primero), sin importar el monto: el
    # abono se aplica integramente al capital (5000.00 < 500000.00 de capital),
    # el interes ya causado queda intacto ("congelado").
    cuota_noviembre = por_fecha[date(2023, 11, 5)]
    fecha_abono = date(2024, 1, 15)
    monto_abono = Decimal("5000.00")
    interes_causado_cuota_noviembre_al_abono = _interes_aislado_dia_a_dia(
        cuota_noviembre.valor, cuota_noviembre.fecha_origen, fecha_abono
    )
    assert monto_abono < interes_causado_cuota_noviembre_al_abono
    assert monto_abono < cuota_noviembre.valor

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
    # tiene cuotas hijas generadas). Desde el Sprint 75 (Task 2), el abono se
    # absorbe integramente en CAPITAL (capital-primero para cuotas-hija) --
    # el capital consolidado de las 4 cuotas queda reducido exactamente en el
    # monto del abono.
    capital_esperado = sum((cuota.valor for cuota in cuotas), Decimal("0.00"))
    assert capital_esperado == Decimal("2100000.00")
    assert resultado.final_balance().principal == capital_esperado - monto_abono

    # Mora independiente por cuota: el interes final consolidado debe ser la
    # suma de los 4 calculos aislados por cuota -- las otras 3 cuotas no se
    # tocan (ni su capital ni su propio interes). La cuota de noviembre es la
    # unica excepcion: como el abono (capital-primero) redujo SU capital de
    # 500000.00 a 495000.00 desde fecha_abono en adelante, su interes aislado
    # se calcula en dos tramos (capital pleno hasta fecha_abono, capital
    # reducido de fecha_abono a fecha_corte) -- el interes ya causado antes
    # del abono no se ve afectado (capital-primero lo deja "congelado", ver
    # AllocationEngine.allocate_capital_primero), pero el interes que sigue
    # corriendo DESPUES del abono si corre sobre el capital ya reducido. Este
    # es el mismo principio verificado en la Task 3
    # (tests/family/test_interes_autonomo_por_cuota.py), aqui extendido a un
    # escenario con reajuste anual real y un abono parcial de por medio.
    interes_noviembre_antes_del_abono = _interes_aislado_dia_a_dia(
        cuota_noviembre.valor, cuota_noviembre.fecha_origen, fecha_abono
    )
    interes_noviembre_despues_del_abono = _interes_aislado_dia_a_dia(
        cuota_noviembre.valor - monto_abono, fecha_abono, fecha_corte
    )
    interes_otras_cuotas = sum(
        (
            _interes_aislado_dia_a_dia(cuota.valor, cuota.fecha_origen, fecha_corte)
            for cuota in cuotas
            if cuota.id != cuota_noviembre.id
        ),
        Decimal("0.00"),
    )
    interes_consolidado_esperado = (
        interes_noviembre_antes_del_abono
        + interes_noviembre_despues_del_abono
        + interes_otras_cuotas
    )
    assert resultado.final_balance().interest == interes_consolidado_esperado
    # Cifra concreta (verificada a mano, ver el comentario del modulo): sirve
    # de ancla adicional si algun cambio futuro en el motor altera el redondeo
    # dia a dia sin que ninguna de las asercions de arriba lo capture.
    assert resultado.final_balance().interest == Decimal("14999.13")
