"""Sprint 75: reproduce el ejemplo numerico exacto dado por el usuario --
cuotas de $150.000 mensuales desde el 1-abr-2022, abono de $500.000 el
1-abr-2024. Corre sobre Comercial (no Civil/Familia) a proposito, para
probar la generalizacion del Sprint 75 (Tasks 1/3), no solo el mecanismo que
ya existia en Familia desde el Sprint 41. Usa el mismo camino que recorreria
PagoPorRangoDialog en la UI real (deuda_pendiente_cuota +
distribuir_pago_en_cascada), sin mocks del motor de liquidacion."""

from datetime import date
from decimal import Decimal

import database.session as session_module
from app.services.area_strategy import ComercialStrategy
from app.services.cascada_cuotas import deuda_pendiente_cuota, distribuir_pago_en_cascada
from app.services.reajuste_anual import generar_cuotas_mensuales
from database.models import Obligacion, TipoObligacion, TipoReajusteAnual


def test_ejemplo_del_usuario_en_comercial():
    """El usuario describio cuotas de $150.000 mensuales "desde el 1 de abril
    de 2022" (todas impagas hasta el abono) y un pago de $500.000 el
    1-abr-2024 que cubre capital+intereses de las cuotas mas recientes y solo
    una parte de los intereses de la mas antigua que alcanza a tocar. Con las
    25 cuotas reales (abr-2022 a abr-2024, inclusive) generadas por
    generar_cuotas_mensuales, el pago de $500.000 no alcanza a cubrir ni
    siquiera el capital de las 25 (25 x 150.000 = 3.750.000) -- se agota antes,
    dejando cuotas mas antiguas
    sin tocar en absoluto, exactamente el comportamiento que describe el
    ejemplo (no se asume de antemano cuantas cuotas toca; se verifica la
    mecanica, no un numero de cuotas fijo)."""
    session = session_module.get_session()
    obligacion_recurrente = Obligacion(
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota mensual pagare comercial",
        categoria="CAPITAL_PAGARE",
        fecha_origen=date(2022, 4, 1),
        fecha_inicio=date(2022, 4, 1),
        dia_pago=1,
        valor=Decimal("150000.00"),
        tasa_efectiva_anual=Decimal("12.00"),
        tasa_moratoria_anual=Decimal("24.00"),
        fecha_vencimiento=date(2022, 4, 1),
        ibc_vigente_anual=Decimal("20.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    session.add(obligacion_recurrente)
    session.commit()
    obligacion_id = obligacion_recurrente.id
    session.close()

    session = session_module.get_session()
    obligacion_recurrente = session.get(Obligacion, obligacion_id)
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 4, 1))
    session.close()

    # generar_cuotas_mensuales (Task 1/3) ya copia tasa_moratoria_anual/
    # ibc_vigente_anual del padre y setea fecha_vencimiento == fecha_origen en
    # cada cuota -- no hace falta completar campos a mano.
    assert len(cuotas) == 25  # abr-2022 a abr-2024 inclusive, 25 meses
    cuotas_ordenadas = sorted(cuotas, key=lambda c: c.fecha_origen, reverse=True)
    assert cuotas_ordenadas[0].fecha_origen == date(2024, 4, 1)
    assert cuotas_ordenadas[-1].fecha_origen == date(2022, 4, 1)

    strategy = ComercialStrategy()
    fecha_pago = date(2024, 4, 1)
    cuotas_y_deuda = []
    for cuota in cuotas_ordenadas:
        rate_provider = strategy._construir_rate_provider_obligacion(cuota, fecha_pago)
        deuda = deuda_pendiente_cuota(cuota, [], fecha_pago, rate_provider)
        cuotas_y_deuda.append((cuota, deuda))

    asignaciones, remanente = distribuir_pago_en_cascada(
        cuotas_y_deuda, Decimal("500000.00"), fecha_pago
    )

    # El pago de 500.000 no alcanza para las 24 cuotas (capital solo ya suma
    # 3.600.000) -- se reparte completo entre las cuotas mas recientes, sin
    # remanente sobrante (nunca llega a "sobrar" plata, se acaba tocando
    # alguna cuota antes de llegar a la mas antigua).
    assert sum(monto for _, monto in asignaciones) == Decimal("500000.00")
    assert remanente == Decimal("0.00")
    assert len(asignaciones) < len(cuotas_ordenadas)

    monto_abril = next(m for c, m in asignaciones if c.fecha_origen == date(2024, 4, 1))
    monto_marzo = next(m for c, m in asignaciones if c.fecha_origen == date(2024, 3, 1))

    # Abril: nace ese mismo dia, sin mora -- solo su capital, exacto.
    assert monto_abril == Decimal("150000.00")
    # Marzo: capital completo + 1 mes de mora al 24% anual (tasa_moratoria_anual,
    # unica tasa que aplica una vez pasado fecha_vencimiento == fecha_origen de
    # cada cuota) -- mayor que el capital solo.
    assert monto_marzo > Decimal("150000.00")

    # Orden capital-antes-que-interes: toda cuota tocada ANTES de la ultima
    # (la mas antigua que alcanzo a recibir algo) recibio como minimo su
    # capital completo (150.000) -- la cascada nunca deja el capital de una
    # cuota mas reciente parcialmente cubierto mientras paga interes de una
    # mas antigua. Solo la ultima cuota tocada (donde el pago se agota) puede
    # recibir menos de 150.000, si ni siquiera alcanza para su capital completo.
    for _, monto in asignaciones[:-1]:
        assert monto >= Decimal("150000.00")
    assert asignaciones[-1][1] > Decimal("0.00")

    # La cuota mas antigua efectivamente tocada por el pago (la ultima con
    # monto > 0) recibe capital completo + una parte de sus intereses -- el
    # resto de esos intereses queda debido (no se prueba aqui directamente,
    # ya lo prueba test_ejemplo_del_usuario_abril_marzo_febrero en
    # tests/services/test_cascada_cuotas.py con numeros de control). Las
    # cuotas mas antiguas que la ultima tocada no reciben nada.
    cuotas_tocadas = {c.fecha_origen for c, _ in asignaciones}
    cuotas_no_tocadas = {c.fecha_origen for c in cuotas_ordenadas} - cuotas_tocadas
    assert cuotas_no_tocadas, "el pago debe agotarse antes de llegar a abril-2022"
    assert min(cuotas_tocadas) > min(c.fecha_origen for c in cuotas_ordenadas)


def test_ejemplo_del_usuario_reproducido_por_civil_familia_da_el_mismo_capital_total():
    """Control cruzado: el mismo escenario en Civil/Familia (el area que ya
    tenia este mecanismo desde el Sprint 41) debe repartir el mismo capital
    total que Comercial arriba -- confirma que Task 1/3 generalizaron el
    mecanismo sin introducir una diferencia de comportamiento entre areas."""
    from app.services.area_strategy import CivilFamiliaStrategy

    session = session_module.get_session()
    obligacion_recurrente = Obligacion(
        expediente_id=2,
        tipo=TipoObligacion.RECURRENTE,
        concepto="CUOTA ALIMENTARIA",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2022, 4, 1),
        fecha_inicio=date(2022, 4, 1),
        dia_pago=1,
        valor=Decimal("150000.00"),
        tasa_efectiva_anual=Decimal("12.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    session.add(obligacion_recurrente)
    session.commit()
    obligacion_id = obligacion_recurrente.id
    session.close()

    session = session_module.get_session()
    obligacion_recurrente = session.get(Obligacion, obligacion_id)
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 4, 1))
    session.close()

    cuotas_ordenadas = sorted(cuotas, key=lambda c: c.fecha_origen, reverse=True)

    strategy = CivilFamiliaStrategy()
    fecha_pago = date(2024, 4, 1)
    cuotas_y_deuda = []
    for cuota in cuotas_ordenadas:
        rate_provider = strategy._construir_rate_provider_obligacion(cuota, fecha_pago)
        deuda = deuda_pendiente_cuota(cuota, [], fecha_pago, rate_provider)
        cuotas_y_deuda.append((cuota, deuda))

    asignaciones, remanente = distribuir_pago_en_cascada(
        cuotas_y_deuda, Decimal("500000.00"), fecha_pago
    )

    assert sum(monto for _, monto in asignaciones) == Decimal("500000.00")
    assert remanente == Decimal("0.00")
    monto_abril = next(m for c, m in asignaciones if c.fecha_origen == date(2024, 4, 1))
    assert monto_abril == Decimal("150000.00")
