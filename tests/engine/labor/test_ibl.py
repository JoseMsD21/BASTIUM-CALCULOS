from datetime import date, datetime as _dt, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _ipc_en_memoria(monkeypatch):
    # calcular_ibl usa get_ipc_interpolado_for_date, que lee IPC_INDICE_ACUMULADO
    # via parametro_service en cada llamada -- misma fixture aislada de disco
    # que tests/engine/labor/test_seguridad_social.py.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    indices = {
        2017: Decimal("100"), 2018: Decimal("105"), 2019: Decimal("110"),
        2020: Decimal("115"), 2021: Decimal("120"), 2022: Decimal("125"),
        2023: Decimal("130"), 2024: Decimal("135"), 2025: Decimal("140"),
        2026: Decimal("145"),
    }
    for anio, valor in indices.items():
        session.add(ParametroLegal(
            clave="IPC_INDICE_ACUMULADO", valor=valor, vigente_desde=date(anio, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    session.commit()
    session.close()


def test_calcular_ibl_historial_10_anios_con_ipc_variable():
    from app.engine.labor.ibl import calcular_ibl

    historial = [(date(anio, 12, 31), Decimal("1000000.00")) for anio in range(2017, 2027)]

    resultado = calcular_ibl(historial, fecha_calculo=date(2026, 12, 31))

    assert resultado == Decimal("1200351.01")


def test_calcular_ibl_historial_vacio_lanza_error():
    from app.engine.labor.ibl import calcular_ibl

    with pytest.raises(ValueError):
        calcular_ibl([], fecha_calculo=date(2026, 12, 31))


def test_tasa_reemplazo_s_uno_sin_bono_toca_el_piso_exacto():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("1000000.00"), smlmv_vigente=Decimal("1000000.00"), semanas_cotizadas=1300,
    )

    assert resultado == Decimal("65.00")


def test_tasa_reemplazo_s_uno_con_bono_de_dos_bloques():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("1000000.00"), smlmv_vigente=Decimal("1000000.00"), semanas_cotizadas=1400,
    )

    assert resultado == Decimal("68.00")


def test_tasa_reemplazo_s_alto_sin_bono_no_baja_del_piso_65():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("10000000.00"), smlmv_vigente=Decimal("1000000.00"), semanas_cotizadas=1300,
    )

    assert resultado == Decimal("65.00")


def test_tasa_reemplazo_bono_grande_no_sube_del_techo_80():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("2000000.00"), smlmv_vigente=Decimal("1000000.00"), semanas_cotizadas=3800,
    )

    assert resultado == Decimal("80.00")


def test_tasa_reemplazo_smlmv_cero_lanza_error():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    with pytest.raises(ValueError):
        calcular_tasa_reemplazo(
            ibl=Decimal("1000000.00"), smlmv_vigente=Decimal("0.00"), semanas_cotizadas=1300,
        )


def test_densidad_semanas_calendario_real_vs_ano_comercial_360():
    from app.engine.labor.ibl import calcular_densidad_semanas

    periodo = [(date(2024, 1, 1), date(2025, 2, 1))]  # 13 meses cruzando un ano bisiesto (2024)

    semanas_calendario_real = calcular_densidad_semanas(periodo)

    # Metodo pre-SL138-2024 (ano comercial de 360, mes de 30 dias): 13*30=390 dias.
    dias_ano_comercial_360 = 13 * 30
    semanas_ano_comercial_360 = round(dias_ano_comercial_360 / 7)

    assert semanas_calendario_real == 57  # (2025-02-01 - 2024-01-01).days == 397; 397/7 = 56.71 -> 57
    assert semanas_ano_comercial_360 == 56
    assert semanas_calendario_real != semanas_ano_comercial_360  # documenta la diferencia real de 1 semana


def test_densidad_semanas_caso_real_sentencia_sl138_2024():
    from app.engine.labor.ibl import calcular_densidad_semanas

    inicio = date(2020, 1, 1)
    fin = inicio + timedelta(days=348)  # caso citado en la Sentencia SL138-2024

    resultado = calcular_densidad_semanas([(inicio, fin)])

    assert resultado == 50  # 348/7 = 49.71 -> redondea a 50 (segun la sentencia)


def test_densidad_semanas_periodos_solapados_no_se_cuentan_doble():
    from app.engine.labor.ibl import calcular_densidad_semanas

    periodos = [
        (date(2023, 1, 1), date(2023, 1, 31)),
        (date(2023, 1, 15), date(2023, 2, 15)),  # se solapa 17 dias con el anterior
    ]

    resultado = calcular_densidad_semanas(periodos)

    assert resultado == 6  # union (2023-01-01, 2023-02-15) = 45 dias -> 45/7 = 6.43 -> 6, no 9


def test_densidad_semanas_lista_vacia_retorna_cero():
    from app.engine.labor.ibl import calcular_densidad_semanas

    assert calcular_densidad_semanas([]) == 0


def test_densidad_semanas_periodo_invalido_lanza_error():
    from app.engine.labor.ibl import calcular_densidad_semanas

    with pytest.raises(ValueError):
        calcular_densidad_semanas([(date(2023, 2, 1), date(2023, 1, 1))])
