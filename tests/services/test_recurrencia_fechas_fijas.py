from datetime import date, datetime
from decimal import Decimal

import pytest

import database.session as session_module
from app.services.recurrencia_fechas_fijas import (
    deserializar_fechas_anuales,
    generar_cuotas_fechas_fijas,
    serializar_fechas_anuales,
)
from database.models import (
    AreaDerecho,
    Beneficiario,
    Expediente,
    Obligacion,
    ParametroLegal,
    TipoBeneficiario,
    TipoObligacion,
    TipoReajusteAnual,
    TipoRecurrencia,
)


def _expediente_civil(session) -> int:
    expediente = Expediente(
        radicado="2026-073",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2027, 12, 31),
    )
    session.add(expediente)
    session.flush()
    return expediente.id


def _obligacion_gastos_vestuario(
    session, expediente_id: int, *, fecha_inicio=date(2026, 1, 1), fecha_fin=None
) -> Obligacion:
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="GASTOS DE VESTUARIO",
        categoria="CHILD_SUPPORT",
        fecha_origen=fecha_inicio,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        valor=Decimal("150000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        tipo_recurrencia=TipoRecurrencia.FECHAS_ANUALES_FIJAS,
        fechas_anuales_fijas=serializar_fechas_anuales(["06-15", "12-15", "03-22"]),
    )
    session.add(obligacion)
    session.commit()
    return obligacion


# --- serializar_fechas_anuales / deserializar_fechas_anuales ---------------


def test_serializar_y_deserializar_fechas_anuales_hace_roundtrip():
    texto = serializar_fechas_anuales(["06-15", "12-15", "03-22"])
    assert deserializar_fechas_anuales(texto) == ["06-15", "12-15", "03-22"]


def test_deserializar_fechas_anuales_con_none_o_vacio_retorna_lista_vacia():
    assert deserializar_fechas_anuales(None) == []
    assert deserializar_fechas_anuales("") == []


def test_serializar_fechas_anuales_rechaza_lista_vacia():
    with pytest.raises(ValueError, match="al menos una fecha"):
        serializar_fechas_anuales([])


def test_serializar_fechas_anuales_rechaza_formato_invalido():
    with pytest.raises(ValueError, match="MM-DD"):
        serializar_fechas_anuales(["2026-06-15"])


def test_serializar_fechas_anuales_rechaza_mes_fuera_de_rango():
    with pytest.raises(ValueError):
        serializar_fechas_anuales(["13-01"])


def test_serializar_fechas_anuales_rechaza_dia_invalido_para_el_mes():
    with pytest.raises(ValueError):
        serializar_fechas_anuales(["02-30"])


def test_serializar_fechas_anuales_acepta_29_de_febrero():
    # 29 de febrero es una fecha MM-DD legitima (ej. cumpleanos de un nino
    # nacido en un año bisiesto) aunque no ocurra todos los años -- la
    # generacion real la topa a 28 en años no bisiestos (CalendarUtils).
    texto = serializar_fechas_anuales(["02-29"])
    assert deserializar_fechas_anuales(texto) == ["02-29"]


# --- generar_cuotas_fechas_fijas --------------------------------------------


def test_genera_exactamente_las_ocurrencias_configuradas_no_doce_cuotas_mensuales():
    """Definicion de Hecho del Sprint 73: una obligacion de gastos de
    vestuario con 3 fechas anuales fijas (junio, diciembre, "cumpleanos" del
    23 de marzo) genera exactamente esas 3 ocurrencias por año -- no 12
    cuotas mensuales."""
    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    obligacion = _obligacion_gastos_vestuario(
        session, expediente_id, fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 12, 31)
    )
    obligacion_id = obligacion.id
    session.close()

    session = session_module.get_session()
    padre = session.get(Obligacion, obligacion_id)
    cuotas = generar_cuotas_fechas_fijas(padre, fecha_corte=date(2026, 12, 31))
    session.close()

    assert len(cuotas) == 3
    fechas_generadas = {c.fecha_origen for c in cuotas}
    assert fechas_generadas == {date(2026, 3, 22), date(2026, 6, 15), date(2026, 12, 15)}
    assert all(c.tipo == TipoObligacion.PUNTUAL for c in cuotas)
    assert all(c.obligacion_padre_id == obligacion_id for c in cuotas)
    assert all(c.expediente_id == expediente_id for c in cuotas)
    assert all(c.valor == Decimal("150000.00") for c in cuotas)
    assert all(c.categoria == "CHILD_SUPPORT" for c in cuotas)


def test_genera_ocurrencias_de_varios_anios_respetando_fecha_inicio_parcial():
    """Si fecha_inicio cae despues de alguna(s) de las fechas MM-DD del primer
    año, esas fechas se omiten SOLO el primer año -- los años siguientes las
    incluyen todas."""
    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    # fecha_inicio 2026-07-01: la fecha "06-15" de 2026 ya paso, se omite ese
    # año; "12-15" de 2026 si aplica. 2027 incluye ambas.
    obligacion = _obligacion_gastos_vestuario(
        session, expediente_id, fecha_inicio=date(2026, 7, 1)
    )
    obligacion_id = obligacion.id
    session.close()

    session = session_module.get_session()
    padre = session.get(Obligacion, obligacion_id)
    cuotas = generar_cuotas_fechas_fijas(padre, fecha_corte=date(2027, 12, 31))
    session.close()

    fechas_generadas = {c.fecha_origen for c in cuotas}
    assert fechas_generadas == {
        date(2026, 12, 15),
        date(2027, 3, 22),
        date(2027, 6, 15),
        date(2027, 12, 15),
    }


def test_generar_cuotas_fechas_fijas_es_idempotente_no_duplica():
    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    obligacion = _obligacion_gastos_vestuario(
        session, expediente_id, fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 12, 31)
    )
    obligacion_id = obligacion.id
    session.close()

    session = session_module.get_session()
    padre = session.get(Obligacion, obligacion_id)
    primera_llamada = generar_cuotas_fechas_fijas(padre, fecha_corte=date(2026, 12, 31))
    session.close()

    session = session_module.get_session()
    padre = session.get(Obligacion, obligacion_id)
    segunda_llamada = generar_cuotas_fechas_fijas(padre, fecha_corte=date(2026, 12, 31))
    session.close()

    assert len(primera_llamada) == len(segunda_llamada)
    assert {c.id for c in primera_llamada} == {c.id for c in segunda_llamada}

    session = session_module.get_session()
    total_en_bd = (
        session.query(Obligacion).filter(Obligacion.obligacion_padre_id == obligacion_id).count()
    )
    session.close()
    assert total_en_bd == len(primera_llamada)


def test_generar_cuotas_fechas_fijas_respeta_fecha_fin_de_la_obligacion():
    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    obligacion = _obligacion_gastos_vestuario(
        session, expediente_id, fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 6, 15)
    )
    obligacion_id = obligacion.id
    session.close()

    session = session_module.get_session()
    padre = session.get(Obligacion, obligacion_id)
    cuotas = generar_cuotas_fechas_fijas(padre, fecha_corte=date(2027, 12, 31))
    session.close()

    assert len(cuotas) == 2
    assert {c.fecha_origen for c in cuotas} == {date(2026, 3, 22), date(2026, 6, 15)}


def test_generar_cuotas_fechas_fijas_se_topa_por_la_vigencia_del_beneficiario_nino():
    """Sprint 74: mismo criterio que generar_cuotas_mensuales -- un Beneficiario
    NINO sin discapacidad topa la generacion en su fecha de fin de vigencia
    (18 anos, no estudia), sin necesitar fecha_fin manual."""
    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    obligacion = _obligacion_gastos_vestuario(
        session, expediente_id, fecha_inicio=date(2026, 1, 1), fecha_fin=None
    )
    session.add(
        Beneficiario(
            obligacion_id=obligacion.id,
            nombre="Juan Perez",
            # Cumple 18 el 2026-06-15 -- coincide exactamente con una ocurrencia.
            fecha_nacimiento=date(2008, 6, 15),
            tipo=TipoBeneficiario.NINO,
            estudia=False,
        )
    )
    session.commit()
    obligacion_id = obligacion.id
    session.close()

    session = session_module.get_session()
    padre = session.get(Obligacion, obligacion_id)
    cuotas = generar_cuotas_fechas_fijas(padre, fecha_corte=date(2027, 12, 31))
    session.close()

    # 06-15 coincide con el cumpleanos 18 (inclusive, todavia vigente); 12-15 ya
    # no. Sin el tope de vigencia, fecha_corte 2027-12-31 habria generado 6
    # cuotas (2 anios x 3 fechas).
    assert len(cuotas) == 2
    assert {c.fecha_origen for c in cuotas} == {date(2026, 3, 22), date(2026, 6, 15)}


def test_generar_cuotas_fechas_fijas_rechaza_obligacion_puntual():
    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("100000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.commit()
    session.close()

    with pytest.raises(ValueError, match="RECURRENTE"):
        generar_cuotas_fechas_fijas(obligacion, fecha_corte=date(2027, 1, 1))


def test_generar_cuotas_fechas_fijas_rechaza_tipo_recurrencia_mensual():
    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        fecha_inicio=date(2026, 1, 1),
        dia_pago=5,
        valor=Decimal("100000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        tipo_recurrencia=TipoRecurrencia.MENSUAL,
    )
    session.add(obligacion)
    session.commit()
    session.close()

    with pytest.raises(ValueError, match="FECHAS_ANUALES_FIJAS"):
        generar_cuotas_fechas_fijas(obligacion, fecha_corte=date(2027, 1, 1))


def test_generar_cuotas_fechas_fijas_rechaza_lista_de_fechas_vacia():
    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Gastos de vestuario",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        fecha_inicio=date(2026, 1, 1),
        valor=Decimal("100000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        tipo_recurrencia=TipoRecurrencia.FECHAS_ANUALES_FIJAS,
        fechas_anuales_fijas=None,
    )
    session.add(obligacion)
    session.commit()
    session.close()

    with pytest.raises(ValueError, match="al menos una fecha"):
        generar_cuotas_fechas_fijas(obligacion, fecha_corte=date(2027, 1, 1))


def test_generar_cuotas_fechas_fijas_aplica_reajuste_smmlv_opcional():
    """A diferencia de generar_cuotas_mensuales (exige reajuste activo), este
    generador lo aplica solo si esta configurado -- confirma que, cuando SI
    esta activo, reutiliza reajustar_capital_anual (misma formula que el
    Sprint 41) en vez de reimplementarla."""
    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    session.add(
        ParametroLegal(
            clave="SMLMV",
            valor=Decimal("1000000.00"),
            vigente_desde=date(2026, 1, 1),
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
            vigente_desde=date(2027, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="GASTOS DE VESTUARIO",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        fecha_inicio=date(2026, 1, 1),
        valor=Decimal("150000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        tipo_recurrencia=TipoRecurrencia.FECHAS_ANUALES_FIJAS,
        fechas_anuales_fijas=serializar_fechas_anuales(["06-15"]),
        tipo_reajuste_anual=TipoReajusteAnual.SMMLV,
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()

    session = session_module.get_session()
    padre = session.get(Obligacion, obligacion_id)
    cuotas = generar_cuotas_fechas_fijas(padre, fecha_corte=date(2027, 12, 31))
    session.close()

    por_fecha = {c.fecha_origen: c.valor for c in cuotas}
    assert por_fecha[date(2026, 6, 15)] == Decimal("150000.00")
    # 2027: reajustado +10% sobre 150000 -> 165000.00.
    assert por_fecha[date(2027, 6, 15)] == Decimal("165000.00")
