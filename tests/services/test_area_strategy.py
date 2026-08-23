from datetime import date, timedelta
from datetime import date as _date
from datetime import datetime as _dt
from decimal import Decimal
from decimal import Decimal as _Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.exceptions import CuotaLitisExcedeTopeError
from app.engine.indexation.historical_index import (
    _IPC_INDICE_ACUMULADO,
    _SMLMV_POR_ANIO,
    _TRAMOS_IBC_USURA,
    _UVT_POR_ANIO,
    get_ipc_interpolado_for_date,
    get_ipc_interpolado_mensual_for_date,
)
from app.engine.indexation.ipc import IPCIndexation
from app.engine.labor.dismissal_indemnity import DismissalIndemnityCalculator
from app.engine.labor.moratory_indemnity import MoratoryIndemnityCalculator
from app.engine.liquidation.engine import LiquidationCore
from app.engine.liquidation.registry import AreaRegistry
from app.services.area_strategy import (
    CivilFamiliaStrategy,
    ComercialStrategy,
    HonorariosStrategy,
    LaboralStrategy,
    SancionatorioStrategy,
    TributarioStrategy,
    _evento_costas_procesales,
)
from app.services.reajuste_anual import generar_cuotas_mensuales
from app.services.recurrencia_fechas_fijas import serializar_fechas_anuales
from database.models import (
    Abono,
    Base,
    Beneficiario,
    Obligacion,
    ParametroLegal,
    TipoBeneficiario,
    TipoContratoLaboral,
    TipoObligacion,
    TipoReajusteAnual,
    TipoRecurrencia,
)


@pytest.fixture(autouse=True)
def _parametros_legales_en_memoria(monkeypatch):
    # Fixture autouse global para todo el archivo: TestComercialStrategy ya
    # depende de calcular_tope_usura (Tarea 7, corregido Sprint 2), que ahora lee
    # USURA_MULTIPLICADOR via parametro_service en cada liquidar() -- si esta fixture solo sembrara
    # las claves de Honorarios, todos los tests de Comercial de este archivo
    # fallarian con ParametroNoDisponibleError. Se siembran aqui las claves
    # que cualquier test de este archivo puede necesitar. Valores/fechas de
    # USURA_MULTIPLICADOR calcados de tests/engine/test_usury_validator.py
    # (la fixture equivalente de la Tarea 7) para no divergir del valor real
    # sembrado en bastium.db por scripts/migrate_parametros_legales.py.
    #
    # SMLMV/IPC_INDICE_ACUMULADO (Tarea 12): SancionatorioStrategy (via
    # resolver_base_sancion -> get_smlmv_for_year) y CivilFamiliaStrategy (via
    # get_ipc_interpolado_for_date) ahora leen ambas claves de
    # parametro_service en cada liquidar(). Se siembran desde los mismos
    # diccionarios congelados que consume scripts/migrate_parametros_legales.py
    # (no se re-transcriben a mano) para no divergir del dato real y para no
    # tener que enumerar a mano que anios especificos necesita cada test.
    #
    # IBC_CONSUMO_ORDINARIO/USURA_CONSUMO_ORDINARIO (Tarea 13): LaboralStrategy
    # (via MoratoryIndemnityCalculator.calcular -> get_ibc_usura_for_date) ahora
    # lee ambas claves de parametro_service por dia de mora. Se siembran desde
    # la misma tabla congelada _TRAMOS_IBC_USURA que consume
    # scripts/migrate_parametros_legales.py, mismo criterio que SMLMV/IPC arriba.
    #
    # UVT (Tarea 14): SancionatorioStrategy (via resolver_base_sancion ->
    # get_uvt_for_year) ahora resuelve hechos posteriores a 2020-01-01 contra
    # la tabla historica de UVT en vez de lanzar UVTNoDisponibleError siempre.
    # Se siembra igual que SMLMV/IPC/IBC arriba, desde el mismo diccionario
    # congelado _UVT_POR_ANIO que consume scripts/migrate_parametros_legales.py.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )
    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave="USURA_MULTIPLICADOR",
            valor=_Decimal("1.5"),
            vigente_desde=_date(1997, 7, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=_dt.now(),
        )
    )
    session.add(
        ParametroLegal(
            clave="HONORARIOS_TOTAL_PCT",
            valor=_Decimal("50"),
            vigente_desde=_date(1900, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=_dt.now(),
        )
    )
    for anio, valor in _SMLMV_POR_ANIO.items():
        session.add(
            ParametroLegal(
                clave="SMLMV",
                valor=valor,
                vigente_desde=_date(anio, 1, 1),
                vigente_hasta=None,
                usuario="test",
                motivo=None,
                creado_en=_dt.now(),
            )
        )
    for anio, valor in _UVT_POR_ANIO.items():
        session.add(
            ParametroLegal(
                clave="UVT",
                valor=valor,
                vigente_desde=_date(anio, 1, 1),
                vigente_hasta=None,
                usuario="test",
                motivo=None,
                creado_en=_dt.now(),
            )
        )
    for clave, valor in {
        "EXTEMPORANEIDAD_PCT_MENSUAL": Decimal("5"),
        "INEXACTITUD_PCT": Decimal("160"),
        "INEXACTITUD_AGRAVADA_PCT": Decimal("200"),
        "ERROR_ARITMETICO_PCT": Decimal("30"),
        # ET635_PUNTOS_DESCUENTO (Sprint 15): faltaba en esta fixture porque ningun test de
        # TributarioStrategy anterior a la correccion del Art. 867-1 tenia mora real (todos
        # usaban fecha_corte == fecha_origen) -- construir_rate_provider_moratorio_tributario
        # nunca llegaba a leer esta clave. Los tests nuevos de mora > 3 anios si la necesitan.
        "ET635_PUNTOS_DESCUENTO": Decimal("2"),
        # CIVIL_ANNUAL_RATE (Sprint 43): HonorariosStrategy (segundo termino de su
        # formula IPC) y ComercialStrategy (modo b, capital indexado + interes civil
        # puro) ahora leen esta clave via AreaStrategy._tasa_civil_anual_pct. Valor
        # identico al que siembra scripts/migrate_parametros_legales.py
        # (LegalRates.CIVIL_ANNUAL_RATE, fraccion 0.06 = 6% anual).
        "CIVIL_ANNUAL_RATE": Decimal("0.06"),
    }.items():
        session.add(
            ParametroLegal(
                clave=clave,
                valor=valor,
                vigente_desde=_date(1900, 1, 1),
                vigente_hasta=None,
                usuario="test",
                motivo=None,
                creado_en=_dt.now(),
            )
        )
    for anio, valor in _IPC_INDICE_ACUMULADO.items():
        session.add(
            ParametroLegal(
                clave="IPC_INDICE_ACUMULADO",
                valor=valor,
                vigente_desde=_date(anio, 1, 1),
                vigente_hasta=None,
                usuario="test",
                motivo=None,
                creado_en=_dt.now(),
            )
        )
    for tramo in _TRAMOS_IBC_USURA:
        session.add(
            ParametroLegal(
                clave="IBC_CONSUMO_ORDINARIO",
                valor=tramo.ibc_anual,
                vigente_desde=tramo.inicio,
                vigente_hasta=tramo.fin,
                usuario="test",
                motivo=None,
                creado_en=_dt.now(),
            )
        )
        session.add(
            ParametroLegal(
                clave="USURA_CONSUMO_ORDINARIO",
                valor=tramo.usura_anual,
                vigente_desde=tramo.inicio,
                vigente_hasta=tramo.fin,
                usuario="test",
                motivo=None,
                creado_en=_dt.now(),
            )
        )
    session.add(
        ParametroLegal(
            clave="SS_PENSION_PCT",
            valor=_Decimal("0.16"),
            vigente_desde=_date(1900, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=_dt.now(),
        )
    )
    session.add(
        ParametroLegal(
            clave="SS_SALUD_PCT",
            valor=_Decimal("0.125"),
            vigente_desde=_date(1900, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=_dt.now(),
        )
    )
    for nivel, valor in {
        "I": _Decimal("0.00522"),
        "II": _Decimal("0.01044"),
        "III": _Decimal("0.02436"),
        "IV": _Decimal("0.04350"),
        "V": _Decimal("0.06960"),
    }.items():
        session.add(
            ParametroLegal(
                clave=f"SS_ARL_NIVEL_{nivel}_PCT",
                valor=valor,
                vigente_desde=_date(1900, 1, 1),
                vigente_hasta=None,
                usuario="test",
                motivo=None,
                creado_en=_dt.now(),
            )
        )
    for i, valor in enumerate(
        [
            _Decimal("0.01"),
            _Decimal("0.012"),
            _Decimal("0.014"),
            _Decimal("0.016"),
            _Decimal("0.018"),
            _Decimal("0.02"),
        ],
        start=1,
    ):
        session.add(
            ParametroLegal(
                clave=f"SS_FSP_TRAMO_{i}_PCT",
                valor=valor,
                vigente_desde=_date(1900, 1, 1),
                vigente_hasta=None,
                usuario="test",
                motivo=None,
                creado_en=_dt.now(),
            )
        )
    session.commit()
    session.close()


def test_registry_expone_las_6_areas():
    areas = AreaRegistry.get_available_areas()
    assert set(areas.keys()) == {
        "CIVIL_FAMILIA",
        "COMERCIAL",
        "LABORAL",
        "SANCIONATORIO",
        "HONORARIOS",
        "TRIBUTARIO",
    }


def test_civil_familia_es_la_unica_area_operable():
    strategy = AreaRegistry.get_strategy("CIVIL_FAMILIA")
    assert isinstance(strategy, CivilFamiliaStrategy)


def _obligacion_puntual(expediente_id=1, valor=Decimal("427900.00")):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Gastos medicos",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2025, 11, 20),
        valor=valor,
        tasa_efectiva_anual=Decimal("6.00"),
    )


def test_civil_familia_usa_civil_annual_rate_cuando_tasa_es_cero():
    # Sprint 61: fallback silencioso -- una obligacion Civil/Familia sin tasa
    # propia (0.00, el mismo criterio ya legitimo que usan Sancionatorio/
    # Honorarios para "no aplica") debe resolver su interes con la tasa legal
    # civil por defecto (CIVIL_ANNUAL_RATE, ya sembrada por la fixture autouse
    # de este archivo como fraccion 0.06 = 6% anual -- ver linea ~145), en vez
    # de generar 0% de interes.
    obligacion = _obligacion_puntual()
    obligacion.tasa_efectiva_anual = Decimal("0.00")

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
    )

    assert resultado.final_balance().interest > Decimal("0.00")


def test_civil_familia_respeta_tasa_propia_cuando_no_es_cero():
    # Con tasa propia > 0 (12%, el doble del 6% de CIVIL_ANNUAL_RATE sembrado
    # por la fixture autouse), el fallback no deberia activarse -- se compara
    # contra una obligacion identica con tasa explicita de 6% para confirmar
    # que el interes de la de 12% es realmente distinto (mayor), no que el
    # fallback silenciosamente sustituyo la tasa propia por la legal.
    obligacion_doce_pct = _obligacion_puntual()
    obligacion_doce_pct.tasa_efectiva_anual = Decimal("12.00")
    obligacion_seis_pct = _obligacion_puntual()
    obligacion_seis_pct.tasa_efectiva_anual = Decimal("6.00")

    resultado_doce = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_doce_pct], abonos=[], fecha_corte=date(2026, 1, 1)
    )
    resultado_seis = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_seis_pct], abonos=[], fecha_corte=date(2026, 1, 1)
    )

    assert resultado_doce.final_balance().interest > Decimal("0.00")
    assert resultado_doce.final_balance().interest > resultado_seis.final_balance().interest


def test_civil_familia_liquida_una_obligacion_puntual_sin_abonos():
    strategy = CivilFamiliaStrategy()
    obligacion = _obligacion_puntual()

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
    )

    # NOTA: `LiquidationResult.total_interest_accrued()` solo suma los items cuyo
    # `event_type` es explicitamente "INTEREST" (ver app/engine/liquidation/engine.py
    # LiquidationCore._process_event). El interes que se acumula dia a dia via
    # `_accrue_time_passage` NO pasa por ahi -- solo se refleja en `final_balance().interest`.
    # Verificado manualmente: para este mismo caso (427900.00 al 6% EA desde 2025-11-20
    # hasta 2026-01-01) el motor da total_interest_accrued() == 0.00 y
    # final_balance().interest == 2869.44. Por eso esta prueba verifica el saldo, no ese metodo.
    assert resultado.final_balance().principal == Decimal("427900.00")
    assert resultado.final_balance().interest > Decimal("0.00")
    assert resultado.total_payments_applied() == Decimal("0.00")


def test_civil_familia_aplica_un_abono_reduciendo_el_saldo():
    strategy = CivilFamiliaStrategy()
    obligacion = _obligacion_puntual()
    abono = Abono(
        id=1,
        obligacion_id=1,
        fecha=date(2025, 12, 1),
        monto=Decimal("100000.00"),
        referencia="ref-1",
    )

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2026, 1, 1)
    )

    assert resultado.total_payments_applied() == Decimal("100000.00")
    assert resultado.final_balance().total() < obligacion.valor


def test_civil_familia_expande_obligacion_recurrente_en_cuotas_mensuales():
    strategy = CivilFamiliaStrategy()
    obligacion = Obligacion(
        id=2,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 3, 5),
    )

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 5)
    )

    # 3 cuotas de 500000 causadas: enero, febrero, marzo
    assert resultado.final_balance().principal == Decimal("1500000.00")


def test_civil_familia_recurrente_nino_beneficiario_deja_de_causar_cuotas_al_cumplir_18():
    """Sprint 74: una obligacion RECURRENTE de Civil/Familia con un beneficiario
    NINO sin discapacidad deja de generar cuotas (ephemeral, RecurringScheduler)
    una vez el beneficiario cumple 18 anos, aunque la fecha de corte de la
    liquidacion sea muy posterior. Beneficiario nace 2010-01-05, cumple 18 el
    2028-01-05 -- cuota de dia_pago=5: la vigencia es inclusiva (mismo criterio
    que `Obligacion.fecha_fin` en el resto del motor), asi que la cuota que cae
    justo el dia del cumpleanos (2028-01-05) SI se causa; la de febrero 2028 ya
    no."""
    strategy = CivilFamiliaStrategy()
    obligacion = Obligacion(
        id=3,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2026, 1, 1),
        beneficiario=Beneficiario(
            nombre="Juan Perez",
            fecha_nacimiento=date(2010, 1, 5),
            tipo=TipoBeneficiario.NINO,
            estudia=False,
        ),
    )

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2030, 1, 1)
    )

    # 25 cuotas: enero 2026 a enero 2028 inclusive (la de enero 2028 coincide
    # con el cumpleanos 18, todavia vigente) -- sin el tope de vigencia, la
    # fecha de corte 2030-01-01 habria generado 49 cuotas (enero 2026 a enero
    # 2030).
    assert resultado.final_balance().principal == Decimal("500000.00") * 25


def test_civil_familia_recurrente_nino_discapacidad_permanente_no_se_corta_por_edad():
    """Contraparte del test anterior: un NINO_DISCAPACIDAD permanente es
    vitalicio -- la obligacion sigue generando cuotas hasta la fecha de corte,
    igual que si no tuviera beneficiario capturado."""
    strategy = CivilFamiliaStrategy()
    obligacion = Obligacion(
        id=4,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 3, 5),
        beneficiario=Beneficiario(
            nombre="Maria Perez",
            fecha_nacimiento=date(2000, 1, 1),
            tipo=TipoBeneficiario.NINO_DISCAPACIDAD,
            discapacidad_permanente=True,
        ),
    )

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 5)
    )

    assert resultado.final_balance().principal == Decimal("1500000.00")


def test_civil_familia_recurrente_conyuge_beneficiario_no_aplica_limite_de_edad():
    """Definicion de Hecho del Sprint 74, punto 2: un caso con beneficiario
    CONYUGE no debe aplicar el limite de edad de los ninos, sin importar que
    fecha de nacimiento tenga capturada."""
    strategy = CivilFamiliaStrategy()
    obligacion = Obligacion(
        id=5,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Alimentos conyuge",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 3, 5),
        beneficiario=Beneficiario(
            nombre="Ana Perez",
            # Si esta fecha se tratara como la de un NINO, ya tendria mas de 18
            # años en 2026 -- confirma que el tope de edad de NINO no se aplica.
            fecha_nacimiento=date(1990, 1, 1),
            tipo=TipoBeneficiario.CONYUGE,
        ),
    )

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 5)
    )

    assert resultado.final_balance().principal == Decimal("1500000.00")


def test_civil_familia_recurrente_con_reajuste_y_cuotas_generadas_no_duplica_capital():
    """Sprint 41, Task 4: si la obligacion RECURRENTE tiene tipo_reajuste_anual
    activo Y ya tiene cuotas hijas persistidas (obligacion_padre_id apuntando a
    ella, generadas por app/services/reajuste_anual.py), liquidar() debe usar
    SOLO esas cuotas hijas (como cualquier PUNTUAL normal) -- la obligacion
    padre no debe volver a expandirse con RecurringScheduler, o el capital de
    cada cuota contaria doble."""
    strategy = CivilFamiliaStrategy()
    padre = Obligacion(
        id=10,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 3, 5),
        tipo_reajuste_anual=TipoReajusteAnual.SMMLV,
    )
    cuota_enero = Obligacion(
        id=11,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Cuota alimentaria de enero 2026",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 5),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        obligacion_padre_id=10,
    )
    cuota_febrero = Obligacion(
        id=12,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Cuota alimentaria de febrero 2026",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 2, 5),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        obligacion_padre_id=10,
    )

    resultado = strategy.liquidar(
        obligaciones=[padre, cuota_enero, cuota_febrero], abonos=[], fecha_corte=date(2026, 3, 5)
    )

    # Solo las 2 cuotas hijas (500000 x 2 = 1000000) -- la obligacion padre no
    # aporta capital propio, ni las 3 cuotas fantasma que RecurringScheduler
    # habria generado por su cuenta (que habria dado 2500000: 1000000 de las
    # cuotas reales + 1500000 fantasma).
    assert resultado.final_balance().principal == Decimal("1000000.00")


def _obligacion_civil_familia_recurrente_persistida(
    valor: Decimal,
    fecha_inicio: date,
    tasa_efectiva_anual: Decimal,
    tipo_reajuste_anual: TipoReajusteAnual,
    expediente_id: int = 1,
) -> Obligacion:
    """Persiste una obligacion RECURRENTE de Civil/Familia en la sesion en memoria
    (fixture autouse `_parametros_legales_en_memoria` de este archivo) -- necesario
    porque `generar_cuotas_mensuales` (Sprint 41/75) requiere una obligacion con `id`
    real para poder generar y persistir las cuotas hijas."""
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
    )
    session.add(obligacion)
    session.commit()
    session.close()
    return obligacion


def test_civil_familia_cuota_hija_usa_capital_primero_en_su_propio_abono():
    # Sprint 75, Task 2: toda cuota-hija (Obligacion PUNTUAL generada por
    # generar_cuotas_mensuales, obligacion_padre_id seteado) debe liquidar sus
    # propios abonos con capital-primero -- sin este wiring, un abono directo
    # sobre la cuota (fuera de la cascada, ej. via AbonoFormDialog) usaria por
    # error el orden legal general (interes antes que capital).
    obligacion_recurrente = _obligacion_civil_familia_recurrente_persistida(
        valor=Decimal("150000.00"),
        fecha_inicio=date(2022, 4, 1),
        tasa_efectiva_anual=Decimal("12.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 4, 1))
    cuota_marzo = next(c for c in cuotas if c.fecha_origen == date(2024, 3, 1))
    assert cuota_marzo.obligacion_padre_id == obligacion_recurrente.id

    # Abono que cubre el capital de esa cuota individual (150000.00) mas solo una
    # parte de su interes de mora (aprox. 444.00 causados en 31 dias al 12% EA) --
    # calibrado para que el resultado sea distinto segun el orden de imputacion:
    # capital-primero deja saldo en INTERES; interes-primero (el orden legal
    # general) dejaria saldo en CAPITAL.
    abono = Abono(obligacion_id=cuota_marzo.id, fecha=date(2024, 4, 1), monto=Decimal("151000.00"))

    # Se liquida SOLO la cuota-hija (no el expediente completo con el padre y las
    # demas 24 cuotas hermanas) para poder verificar, sin ruido, el saldo final
    # propio de esta cuota -- liquidar el expediente completo consolida el
    # capital_base de TODAS las obligaciones del expediente en cada fila
    # (_fusionar_resultados), lo que enmascararia esta verificacion puntual.
    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[cuota_marzo],
        abonos=[abono],
        fecha_corte=date(2024, 4, 1),
    )

    saldo = resultado.final_balance()
    assert saldo.principal == Decimal("0.00")
    assert saldo.interest > Decimal("0.00")


def test_civil_familia_recurrente_sin_reajuste_y_cuotas_generadas_no_duplica_capital():
    """Bug encontrado en revision de codigo del Sprint 75 (Task 1 + Task 2):
    Task 1 hizo que generar_cuotas_mensuales funcione tambien para
    tipo_reajuste_anual = NINGUNO (antes solo SMMLV/IPC podian tener cuotas
    hijas reales). El guard de _eventos_de_obligacion que evita re-expandir
    una obligacion RECURRENTE padre que ya tiene cuotas hijas generadas
    exigia `reajuste_activo` (SMMLV/IPC) ademas de la membresia en
    ids_con_cuotas_generadas -- por lo que una obligacion NINGUNO con cuotas
    reales generadas NO se saltaba la expansion efimera de FamilyScheduler,
    duplicando el capital (una vez via las cuotas reales, otra vez via los
    eventos fantasma). Ver test analogo para SMMLV/IPC arriba:
    test_civil_familia_recurrente_con_reajuste_y_cuotas_generadas_no_duplica_capital."""
    obligacion_recurrente = _obligacion_civil_familia_recurrente_persistida(
        valor=Decimal("150000.00"),
        fecha_inicio=date(2024, 1, 1),
        tasa_efectiva_anual=Decimal("12.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 3, 1))
    assert len(cuotas) == 3
    for cuota in cuotas:
        assert cuota.obligacion_padre_id == obligacion_recurrente.id

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_recurrente, *cuotas],
        abonos=[],
        fecha_corte=date(2024, 3, 1),
    )

    # Solo las 3 cuotas hijas reales (150000 x 3 = 450000) -- la obligacion
    # padre no debe aportar capital propio via expansion efimera encima de
    # las cuotas ya generadas. Sin el fix, esto da 900000.00 (el doble).
    total_esperado = sum((cuota.valor for cuota in cuotas), Decimal("0.00"))
    assert total_esperado == Decimal("450000.00")
    assert resultado.final_balance().principal == total_esperado


def test_civil_familia_recurrente_con_reajuste_pero_sin_cuotas_generadas_usa_expansion_efimera():
    """Complemento del test anterior: si tipo_reajuste_anual esta activo pero
    TODAVIA no se generaron cuotas hijas (el usuario no presiono "Generar
    cuotas" en la UI), se preserva el comportamiento anterior a este sprint
    (expansion efimera con RecurringScheduler, capital constante) -- liquidar
    debe seguir funcionando, no producir un saldo en cero."""
    strategy = CivilFamiliaStrategy()
    padre = Obligacion(
        id=20,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 3, 5),
        tipo_reajuste_anual=TipoReajusteAnual.SMMLV,
    )

    resultado = strategy.liquidar(obligaciones=[padre], abonos=[], fecha_corte=date(2026, 3, 5))

    # 3 cuotas efimeras de 500000 (enero, febrero, marzo), igual que la obligacion
    # sin reajuste -- mismo comportamiento previo a este sprint.
    assert resultado.final_balance().principal == Decimal("1500000.00")


def test_civil_familia_fechas_fijas_sin_cuotas_generadas_usa_expansion_efimera_por_fechas():
    """Sprint 73: una obligacion RECURRENTE con tipo_recurrencia
    FECHAS_ANUALES_FIJAS, liquidada ANTES de presionar "Generar cuotas" (sin
    hijas persistidas todavia), debe expandirse efimeramente en las fechas
    MM-DD configuradas -- NUNCA en 12 cuotas mensuales (que es justo el bug
    que este sprint corrige: antes de este cambio, el fallback de
    _eventos_de_obligacion solo sabia expandir mensualmente)."""
    strategy = CivilFamiliaStrategy()
    obligacion = Obligacion(
        id=30,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Gastos de vestuario",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("150000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 12, 31),
        tipo_recurrencia=TipoRecurrencia.FECHAS_ANUALES_FIJAS,
        fechas_anuales_fijas=serializar_fechas_anuales(["06-15", "12-15", "03-22"]),
    )

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 12, 31)
    )

    # Exactamente 3 ocurrencias de 150000 (450000 total) -- no 12 cuotas
    # mensuales (que habrian dado 1800000).
    assert resultado.final_balance().principal == Decimal("450000.00")


def test_civil_familia_fechas_fijas_con_cuotas_generadas_no_duplica_capital():
    """Complemento del test anterior: una vez que existen cuotas hijas reales
    (obligacion_padre_id apuntando a la RECURRENTE padre), la obligacion padre
    no debe aportar capital propio -- mismo criterio ya probado para
    reajuste SMMLV/IPC (Sprint 41), ahora generalizado a cualquier obligacion
    con cuotas hijas persistidas, sin importar el generador que las creo."""
    strategy = CivilFamiliaStrategy()
    padre = Obligacion(
        id=31,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Gastos de vestuario",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("150000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 12, 31),
        tipo_recurrencia=TipoRecurrencia.FECHAS_ANUALES_FIJAS,
        fechas_anuales_fijas=serializar_fechas_anuales(["06-15", "12-15", "03-22"]),
    )
    cuota_marzo = Obligacion(
        id=32,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Gastos de vestuario - 22/03/2026",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 3, 22),
        valor=Decimal("150000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        obligacion_padre_id=31,
    )

    resultado = strategy.liquidar(
        obligaciones=[padre, cuota_marzo], abonos=[], fecha_corte=date(2026, 12, 31)
    )

    # Solo la cuota hija real (150000) -- ni las 3 fantasma de la expansion
    # efimera (450000), ni el capital propio de la obligacion padre.
    assert resultado.final_balance().principal == Decimal("150000.00")


def test_civil_familia_puntual_sin_indexacion_no_genera_evento_indexation():
    strategy = CivilFamiliaStrategy()
    obligacion = _obligacion_puntual()  # aplica_indexacion_ipc no seteado -> falsy

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
    )

    assert all(item.balance.event_type != "INDEXATION" for item in resultado.items)
    assert resultado.final_balance().indexation == Decimal("0.00")


def test_civil_familia_puntual_con_indexacion_genera_evento_indexation_con_monto_correcto():
    obligacion = Obligacion(
        id=3,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2024, 7, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=True,
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 31)
    )

    eventos_indexacion = [
        item for item in resultado.items if item.balance.event_type == "INDEXATION"
    ]
    assert len(eventos_indexacion) == 1
    # Sprint 80: ambas fechas (2024-07-01 y 2025-12-31) caen dentro del rango
    # cubierto por el indice IPC MENSUAL real (_IPC_MENSUAL, 2003-01 a
    # 2026-03), asi que CivilFamiliaStrategy ya usa
    # get_ipc_interpolado_mensual_for_date en vez de la anual -- el monto
    # cambio de 77,633.53 (formula anual, version pre-Sprint-80 de este test)
    # a 61,933.78 (formula mensual). Recalculado con el motor real, no a mano.
    assert eventos_indexacion[0].indexation_amount == Decimal("61933.78")
    assert eventos_indexacion[0].concept == "Indexación IPC — Dano emergente"
    assert resultado.final_balance().indexation == Decimal("61933.78")


def test_civil_familia_recurrente_con_indexacion_cada_cuota_indexa_desde_su_propia_fecha():
    obligacion = Obligacion(
        id=4,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2025, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2025, 1, 1),
        fecha_fin=date(2025, 2, 5),
        aplica_indexacion_ipc=True,
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 31)
    )

    eventos_indexacion = sorted(
        (item for item in resultado.items if item.balance.event_type == "INDEXATION"),
        key=lambda item: item.date,
    )
    # 2 cuotas (5-ene y 5-feb-2025), cada una con su propio monto de indexacion
    # porque cada una arranca a indexar desde una fecha distinta -- si ambas
    # dieran el mismo monto, seria señal de que se esta usando fecha_inicio de
    # la obligacion en vez de la fecha de cada cuota.
    assert len(eventos_indexacion) == 2
    assert eventos_indexacion[0].date == date(2025, 1, 5)
    assert eventos_indexacion[1].date == date(2025, 2, 5)
    # Sprint 80: ambas cuotas caen dentro del rango IPC mensual (2003-01 a
    # 2026-03), asi que se recalcularon con get_ipc_interpolado_mensual_for_date
    # en vez de la anual (valores previos: 25133.13/22869.89) -- recalculado
    # con el motor real.
    assert eventos_indexacion[0].indexation_amount == Decimal("24709.43")
    assert eventos_indexacion[1].indexation_amount == Decimal("19563.64")
    assert eventos_indexacion[0].indexation_amount != eventos_indexacion[1].indexation_amount


def test_civil_familia_indexacion_dentro_del_rango_mensual_usa_ipc_mensual_no_anual():
    # Sprint 80: ambas fechas (causacion y corte) caen dentro del rango
    # cubierto por _IPC_MENSUAL (2003-01 a 2026-03), asi que
    # CivilFamiliaStrategy._evento_indexacion debe usar
    # get_ipc_interpolado_mensual_for_date (exigido por el despacho, Sprint 8)
    # en vez de la interpolacion anual generica. Se compara contra el calculo
    # esperado usando la funcion mensual directamente, y se confirma que NO
    # coincide con lo que daria la interpolacion anual (para probar que
    # efectivamente cambio de una formula a otra, no solo que el motor sigue
    # sin tronar).
    obligacion = Obligacion(
        id=3,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2024, 7, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=True,
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 31)
    )

    esperado_mensual = IPCIndexation.calculate(
        capital=Decimal("1000000.00"),
        initial_index=get_ipc_interpolado_mensual_for_date(date(2024, 7, 1)),
        final_index=get_ipc_interpolado_mensual_for_date(date(2025, 12, 31)),
    )
    esperado_anual = IPCIndexation.calculate(
        capital=Decimal("1000000.00"),
        initial_index=get_ipc_interpolado_for_date(date(2024, 7, 1)),
        final_index=get_ipc_interpolado_for_date(date(2025, 12, 31)),
    )
    assert esperado_mensual != esperado_anual  # las dos formulas dan numeros distintos

    eventos_indexacion = [
        item for item in resultado.items if item.balance.event_type == "INDEXATION"
    ]
    assert len(eventos_indexacion) == 1
    assert eventos_indexacion[0].indexation_amount == esperado_mensual
    assert resultado.final_balance().indexation == esperado_mensual


def test_civil_familia_indexacion_fuera_del_rango_mensual_cae_a_interpolacion_anual():
    # Sprint 80: fecha_causacion (1999) es anterior al primer mes cargado en
    # _IPC_MENSUAL (2003-01) -- get_ipc_interpolado_mensual_for_date lanza
    # IPCMensualNoDisponibleError, y el fallback documentado en
    # CivilFamiliaStrategy._evento_indexacion debe usar la interpolacion anual
    # para AMBAS fechas (nunca mezclar un indice mensual con uno anual: son
    # series con bases distintas, y mezclarlas arruinaria la razon
    # final_index/initial_index).
    obligacion = Obligacion(
        id=3,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente antiguo",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(1999, 6, 15),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=True,
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 31)
    )

    esperado_anual = IPCIndexation.calculate(
        capital=Decimal("1000000.00"),
        initial_index=get_ipc_interpolado_for_date(date(1999, 6, 15)),
        final_index=get_ipc_interpolado_for_date(date(2025, 12, 31)),
    )

    eventos_indexacion = [
        item for item in resultado.items if item.balance.event_type == "INDEXATION"
    ]
    assert len(eventos_indexacion) == 1
    assert eventos_indexacion[0].indexation_amount == esperado_anual


def test_civil_familia_recurrente_con_indexacion_reutiliza_ipc_entre_cuotas_del_mismo_anio(
    monkeypatch,
):
    from app.services import parametro_service

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    obligacion = Obligacion(
        id=99,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2025, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2025, 1, 1),
        fecha_fin=date(2025, 12, 5),
        aplica_indexacion_ipc=True,
    )

    CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 5)
    )

    llamadas_ipc = [llamada for llamada in llamadas if llamada[0] == "IPC_INDICE_ACUMULADO"]
    # 12 cuotas (una por mes de 2025) todas resuelven IPC_INDICE_ACUMULADO
    # contra date(2025,1,1) (fecha_causacion, mismo año) y date(2025,1,1)
    # (fecha_corte 2025-12-05, tambien 2025) -- con la cache activa, ambas
    # colapsan a una sola consulta real en vez de hasta 24.
    assert len(llamadas_ipc) <= 2


def test_civil_familia_genera_evento_de_costas_si_esta_configurado():
    # valor = 123.500.000, fecha_origen forzada a 2024-06-01 (SMLMV 2024 =
    # 1.300.000.00): punto medio exacto del tier menor cuantia (52.000.000 a
    # 195.000.000) -> pct = 7% -> costas = 8.645.000,00. Mismo caso de
    # referencia usado en Tasks 4, 11, 13 y 14.
    # Sprint 61: tasa_efectiva_anual = 0.00 ahora activa el fallback a
    # CIVIL_ANNUAL_RATE (ya sembrada por la fixture autouse de este archivo) --
    # aunque este test no le importa el interes, fecha_corte == fecha_origen
    # asi que nunca se acumula ninguno de todas formas.
    obligacion = _obligacion_puntual(valor=_Decimal("123500000.00"))
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.tasa_efectiva_anual = _Decimal("0.00")
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"

    resultado = CivilFamiliaStrategy().liquidar(
        [obligacion],
        [],
        fecha_corte=obligacion.fecha_origen,
    )
    tipos_evento = {item.balance.event_type for item in resultado.items}
    assert "COSTAS_PROCESALES" in tipos_evento
    assert resultado.final_balance().principal == _Decimal(
        "132145000.00"
    )  # 123.500.000 + 8.645.000


def test_civil_familia_obligaciones_tasas_distintas_fechas_solapadas_usan_tasa_propia():
    fecha_corte = date(2026, 1, 11)
    obligacion_a = Obligacion(
        id=101,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Obligacion A",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("12.00"),
    )
    obligacion_b = Obligacion(
        id=102,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Obligacion B",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("24.00"),
    )

    resultado_combinado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
    )
    resultado_solo_a = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a], abonos=[], fecha_corte=fecha_corte
    )
    resultado_solo_b = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
    )

    assert resultado_combinado.final_balance().principal == Decimal("2000000.00")
    # El interes combinado debe ser exactamente la suma de cada obligacion liquidada con
    # su propia tasa por separado -- no depende de interacciones entre obligaciones porque
    # no hay abonos en este caso.
    interes_esperado = (
        resultado_solo_a.final_balance().interest + resultado_solo_b.final_balance().interest
    )
    assert resultado_combinado.final_balance().interest == interes_esperado
    # Si el bug de "toma la tasa de la primera obligacion para todo el expediente" siguiera
    # presente, el interes combinado seria 2 * interes_solo_a (ambas al 12%) en vez de la
    # suma de cada una a su propia tasa -- como B esta al doble de tasa que A, estos dos
    # valores son observablemente distintos, asi que esta asercion por si sola detecta el bug.
    assert (
        resultado_combinado.final_balance().interest
        != Decimal("2") * resultado_solo_a.final_balance().interest
    )


def test_civil_familia_abono_de_una_obligacion_no_afecta_el_saldo_de_otra():
    fecha_corte = date(2026, 1, 11)
    obligacion_a = Obligacion(
        id=103,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Obligacion A",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("12.00"),
    )
    obligacion_b = Obligacion(
        id=104,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Obligacion B",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("12.00"),
    )
    abono_a = Abono(
        id=201,
        obligacion_id=103,
        fecha=date(2026, 1, 5),
        monto=Decimal("300000.00"),
        referencia="pago-a",
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a, obligacion_b], abonos=[abono_a], fecha_corte=fecha_corte
    )
    resultado_solo_b_sin_abono = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
    )
    resultado_solo_a_con_abono = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a], abonos=[abono_a], fecha_corte=fecha_corte
    )

    assert resultado.total_payments_applied() == Decimal("300000.00")
    # El interes de B no debe verse afectado por el abono registrado contra A: el interes
    # combinado debe ser exactamente A-con-abono + B-sin-abono, no una mezcla donde el abono
    # de A tambien reduce lo que B acumula.
    interes_esperado = (
        resultado_solo_a_con_abono.final_balance().interest
        + resultado_solo_b_sin_abono.final_balance().interest
    )
    assert resultado.final_balance().interest == interes_esperado


def test_civil_familia_abono_con_obligacion_id_ajeno_al_expediente_lanza_value_error():
    obligacion = _obligacion_puntual()
    abono_huerfano = Abono(
        id=202,
        obligacion_id=999,
        fecha=date(2025, 12, 1),
        monto=Decimal("1000.00"),
        referencia="huerfano",
    )

    with pytest.raises(ValueError):
        CivilFamiliaStrategy().liquidar(
            obligaciones=[obligacion], abonos=[abono_huerfano], fecha_corte=date(2026, 1, 1)
        )


def test_civil_familia_dos_obligaciones_producen_una_sola_fila_de_cierre_consolidada():
    fecha_corte = date(2026, 1, 11)
    obligacion_a = Obligacion(
        id=105,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Obligacion A",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("12.00"),
    )
    obligacion_b = Obligacion(
        id=106,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Obligacion B",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("24.00"),
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
    )

    filas_de_cierre = [
        item for item in resultado.items if item.balance.event_type == "LIQUIDATION_CUTOFF"
    ]
    assert len(filas_de_cierre) == 1
    assert resultado.final_balance().principal == Decimal("2000000.00")


def test_capital_concepts_incluye_los_codigos_comerciales_nuevos():
    core = LiquidationCore()
    assert "CAPITAL_LETRA_CAMBIO" in core._capital_concepts
    assert "CAPITAL_CHEQUE" in core._capital_concepts
    assert "CAPITAL_FACTURA" in core._capital_concepts


def test_capital_concepts_incluye_los_codigos_sancionatorio_y_honorarios():
    core = LiquidationCore()
    assert "MULTA_SANCIONATORIA" in core._capital_concepts
    assert "HONORARIOS_PROFESIONALES" in core._capital_concepts
    assert "COSTAS_PROCESALES" in core._capital_concepts


def test_capital_concepts_incluye_vacaciones():
    core = LiquidationCore()
    assert "VACACIONES" in core._capital_concepts


def test_capital_concepts_incluye_seguridad_social_e_incapacidad():
    core = LiquidationCore()
    assert "COTIZACION_PENSION" in core._capital_concepts
    assert "COTIZACION_SALUD" in core._capital_concepts
    assert "COTIZACION_ARL" in core._capital_concepts
    assert "COTIZACION_FSP" in core._capital_concepts
    assert "INCAPACIDAD_EMPLEADOR" in core._capital_concepts
    assert "SUSPENSION_INFORMATIVA" in core._capital_concepts
    assert "INCAPACIDAD_INFORMATIVA" in core._capital_concepts


def _obligacion_comercial(
    expediente_id=1,
    valor=Decimal("1000000.00"),
    tasa_remuneratoria=Decimal("6.00"),
    tasa_moratoria=Decimal("24.00"),
    ibc=Decimal("20.00"),
    fecha_origen=date(2025, 1, 1),
    fecha_vencimiento=date(2025, 2, 1),
    anatocismo_demanda_judicial=False,
    anatocismo_fecha_acuerdo=None,
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Capital de pagare",
        categoria="CAPITAL_PAGARE",
        fecha_origen=fecha_origen,
        valor=valor,
        tasa_efectiva_anual=tasa_remuneratoria,
        tasa_moratoria_anual=tasa_moratoria,
        fecha_vencimiento=fecha_vencimiento,
        ibc_vigente_anual=ibc,
        anatocismo_demanda_judicial=anatocismo_demanda_judicial,
        anatocismo_fecha_acuerdo=anatocismo_fecha_acuerdo,
    )


class _TRMProviderDeCalendario:
    """Test double de TRMProvider (Sprint 12): retorna una TRM distinta por
    fecha exacta, para probar que la conversion es realmente dinamica -- nunca
    hace red."""

    def __init__(self, trm_por_fecha: dict):
        self._trm_por_fecha = trm_por_fecha

    def get_trm(self, fecha_referencia):
        return self._trm_por_fecha[fecha_referencia]


class TestComercialStrategy:
    def test_liquida_una_obligacion_puntual_sin_abonos(self):
        strategy = ComercialStrategy()
        obligacion = _obligacion_comercial()

        resultado = strategy.liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        assert resultado.final_balance().principal == Decimal("1000000.00")
        assert resultado.final_balance().interest > Decimal("0.00")
        assert resultado.total_payments_applied() == Decimal("0.00")

    def test_aplica_un_abono_reduciendo_el_saldo(self):
        strategy = ComercialStrategy()
        obligacion = _obligacion_comercial()
        abono = Abono(
            id=1,
            obligacion_id=1,
            fecha=date(2025, 2, 15),
            monto=Decimal("200000.00"),
            referencia="ref-1",
        )

        resultado = strategy.liquidar(
            obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2025, 3, 1)
        )

        assert resultado.total_payments_applied() == Decimal("200000.00")
        assert resultado.final_balance().total() < obligacion.valor

    def test_usa_tasa_moratoria_tras_el_vencimiento_acumula_mas_interes_que_solo_remuneratoria(
        self,
    ):
        fecha_corte = date(2025, 3, 1)
        obligacion_comercial = _obligacion_comercial()
        resultado_comercial = ComercialStrategy().liquidar(
            obligaciones=[obligacion_comercial], abonos=[], fecha_corte=fecha_corte
        )

        # Misma obligacion liquidada solo con la tasa remuneratoria (6%) durante todo el periodo,
        # via CivilFamiliaStrategy, que unicamente lee tasa_efectiva_anual.
        obligacion_solo_remuneratoria = _obligacion_comercial()
        resultado_solo_remuneratoria = CivilFamiliaStrategy().liquidar(
            obligaciones=[obligacion_solo_remuneratoria], abonos=[], fecha_corte=fecha_corte
        )

        # La obligacion vence 2025-02-01 y la tasa moratoria (24%) es mayor que la
        # remuneratoria (6%), asi que el interes acumulado en Comercial (que aplica la
        # moratoria desde el vencimiento) debe ser mayor que si se hubiera usado la
        # remuneratoria durante todo el periodo.
        assert (
            resultado_comercial.final_balance().interest
            > resultado_solo_remuneratoria.final_balance().interest
        )

    def test_sin_mora_usa_solo_tasa_remuneratoria(self):
        fecha_corte = date(2025, 1, 20)  # antes del vencimiento (2025-02-01)

        obligacion_comercial = _obligacion_comercial()
        resultado_comercial = ComercialStrategy().liquidar(
            obligaciones=[obligacion_comercial], abonos=[], fecha_corte=fecha_corte
        )

        obligacion_civil = _obligacion_comercial()
        resultado_civil = CivilFamiliaStrategy().liquidar(
            obligaciones=[obligacion_civil], abonos=[], fecha_corte=fecha_corte
        )

        assert (
            resultado_comercial.final_balance().interest
            == resultado_civil.final_balance().interest
        )

    def test_tasa_moratoria_excede_tope_de_usura_no_lanza_error_y_aplica_sancion_doblada(self):
        # Respuesta del despacho (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 2): no se
        # rechaza ni se recorta la tasa silenciosamente. Se liquida con la tasa pactada, se
        # calcula el exceso de interes cobrado frente a la tasa de usura vigente, y se resta
        # del saldo el doble de ese exceso (sancion legal por usura, Ley 45/1990 art. 72).
        #
        # fecha_origen == fecha_vencimiento y tasa_remuneratoria == tasa_moratoria (35%): la
        # obligacion ya esta en mora desde el dia 1, asi que Comercial aplica una sola tasa
        # efectiva (35%) durante todo el periodo, igual que CivilFamiliaStrategy -- eso permite
        # verificar "Intereses_Cobrados" e "Intereses_Cobrados_Con_Tasa_Usura" con un motor
        # independiente (CivilFamiliaStrategy, que no aplica ninguna correccion de usura) en vez
        # de reutilizar el mecanismo interno de ComercialStrategy que se esta probando.
        fecha_corte = date(2025, 3, 1)
        fecha_origen = date(2025, 1, 1)
        obligacion_pactada = _obligacion_comercial(
            tasa_remuneratoria=Decimal("35.00"),
            tasa_moratoria=Decimal("35.00"),
            ibc=Decimal("20.00"),
            fecha_origen=fecha_origen,
            fecha_vencimiento=fecha_origen,
        )

        # Tope legal = 1.5 x 20 = 30%.
        intereses_cobrados = (
            CivilFamiliaStrategy()
            .liquidar(
                obligaciones=[
                    _obligacion_comercial(
                        tasa_remuneratoria=Decimal("35.00"),
                        fecha_origen=fecha_origen,
                        fecha_vencimiento=fecha_origen,
                    )
                ],
                abonos=[],
                fecha_corte=fecha_corte,
            )
            .final_balance()
            .interest
        )
        intereses_con_tasa_usura = (
            CivilFamiliaStrategy()
            .liquidar(
                obligaciones=[
                    _obligacion_comercial(
                        tasa_remuneratoria=Decimal("30.00"),
                        fecha_origen=fecha_origen,
                        fecha_vencimiento=fecha_origen,
                    )
                ],
                abonos=[],
                fecha_corte=fecha_corte,
            )
            .final_balance()
            .interest
        )

        exceso_esperado = intereses_cobrados - intereses_con_tasa_usura
        sancion_esperada = exceso_esperado * 2

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion_pactada], abonos=[], fecha_corte=fecha_corte
        )

        item_sancion = resultado.items[-1]
        assert "usura" in item_sancion.concept.lower()
        assert item_sancion.interest_amount == -sancion_esperada
        assert resultado.final_balance().interest == intereses_cobrados - sancion_esperada

    def test_tasa_remuneratoria_excede_tope_de_usura_no_lanza_error_y_aplica_sancion_doblada(self):
        fecha_corte = date(2025, 1, 20)  # antes del vencimiento: solo corre la remuneratoria
        obligacion_pactada = _obligacion_comercial(
            tasa_remuneratoria=Decimal("35.00"),
            tasa_moratoria=Decimal("6.00"),
            ibc=Decimal("20.00"),
        )

        # Tope legal = 1.5 x 20 = 30%. Antes del vencimiento, Comercial usa solo la tasa
        # remuneratoria -- exactamente lo mismo que CivilFamiliaStrategy con esa tasa (ver
        # test_sin_mora_usa_solo_tasa_remuneratoria arriba), asi que sirve de referencia
        # independiente para "Intereses_Cobrados"/"Intereses_Cobrados_Con_Tasa_Usura".
        intereses_cobrados = (
            CivilFamiliaStrategy()
            .liquidar(
                obligaciones=[_obligacion_comercial(tasa_remuneratoria=Decimal("35.00"))],
                abonos=[],
                fecha_corte=fecha_corte,
            )
            .final_balance()
            .interest
        )
        intereses_con_tasa_usura = (
            CivilFamiliaStrategy()
            .liquidar(
                obligaciones=[_obligacion_comercial(tasa_remuneratoria=Decimal("30.00"))],
                abonos=[],
                fecha_corte=fecha_corte,
            )
            .final_balance()
            .interest
        )

        exceso_esperado = intereses_cobrados - intereses_con_tasa_usura
        sancion_esperada = exceso_esperado * 2

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion_pactada], abonos=[], fecha_corte=fecha_corte
        )

        item_sancion = resultado.items[-1]
        assert "usura" in item_sancion.concept.lower()
        assert item_sancion.interest_amount == -sancion_esperada

    def test_tasa_muy_por_encima_del_tope_puede_dejar_saldo_a_favor_del_deudor(self):
        # La sancion (2x el exceso) puede superar el saldo restante de la obligacion --
        # el despacho es explicito en que eso genera un saldo a favor del deudor (numero
        # negativo), no un piso en cero.
        fecha_corte = date(2027, 1, 1)
        obligacion = _obligacion_comercial(
            valor=Decimal("10000.00"), tasa_moratoria=Decimal("1000.00"), ibc=Decimal("20.00")
        )

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado.final_balance().total() < Decimal("0.00")

    def test_tasas_dentro_del_tope_no_agregan_item_de_sancion(self):
        obligacion = _obligacion_comercial(tasa_moratoria=Decimal("24.00"), ibc=Decimal("20.00"))

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        assert all("usura" not in item.concept.lower() for item in resultado.items)

    def test_fecha_vencimiento_anterior_a_fecha_origen_lanza_value_error(self):
        obligacion = _obligacion_comercial(
            fecha_origen=date(2025, 2, 1), fecha_vencimiento=date(2025, 1, 1)
        )

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
            )

    @pytest.mark.parametrize(
        "campo",
        ["tasa_moratoria_anual", "fecha_vencimiento", "ibc_vigente_anual", "tasa_efectiva_anual"],
    )
    def test_falta_un_campo_comercial_obligatorio_lanza_value_error(self, campo):
        obligacion = _obligacion_comercial()
        setattr(obligacion, campo, None)

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
            )

    def test_recurrente_no_hace_split_usa_tasa_moratoria_unica(self):
        obligacion = Obligacion(
            id=2,
            expediente_id=1,
            tipo=TipoObligacion.RECURRENTE,
            concepto="Cuotas de pagare a plazos",
            categoria="CAPITAL_PAGARE",
            fecha_origen=date(2025, 1, 1),
            valor=Decimal("500000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
            tasa_moratoria_anual=Decimal("24.00"),
            fecha_vencimiento=date(2025, 1, 1),
            ibc_vigente_anual=Decimal("20.00"),
            dia_pago=5,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 3, 5),
        )

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 5)
        )

        # 3 cuotas de 500000 causadas: enero, febrero, marzo
        assert resultado.final_balance().principal == Decimal("1500000.00")

    def test_no_duplica_capital_del_padre_cuando_ya_tiene_cuotas_generadas(self):
        """Bug analogo al ya corregido en CivilFamiliaStrategy (Sprint 75, ver
        test_civil_familia_recurrente_sin_reajuste_y_cuotas_generadas_no_duplica_capital
        en este mismo archivo): ComercialStrategy soporta obligaciones RECURRENTE
        via FamilyScheduler (mismo mecanismo que Civil/Familia usaba antes del
        Sprint 41), pero -- antes de este fix -- no detecta cuando esa obligacion
        ya tiene cuotas-hija reales generadas y persistidas
        (generar_cuotas_mensuales, app/services/reajuste_anual.py, Sprint 75 Task 1
        extendio esta funcion para soportar tambien tipo_reajuste_anual = NINGUNO).
        Si el padre RECURRENTE y sus cuotas hijas reales se liquidan juntos (mismo
        expediente), el capital se duplicaba: una vez via cada cuota real (tratada
        como PUNTUAL independiente) y otra vez via la expansion efimera de
        FamilyScheduler sobre el padre."""
        session = session_module.get_session()
        obligacion_recurrente = Obligacion(
            expediente_id=1,
            tipo=TipoObligacion.RECURRENTE,
            concepto="CUOTAS DE PAGARE A PLAZOS",
            categoria="CAPITAL_PAGARE",
            fecha_origen=date(2024, 1, 1),
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=date(2024, 3, 1),
            dia_pago=1,
            valor=Decimal("500000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
            tasa_moratoria_anual=Decimal("24.00"),
            fecha_vencimiento=date(2024, 1, 1),
            ibc_vigente_anual=Decimal("20.00"),
            tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
        )
        session.add(obligacion_recurrente)
        session.commit()
        session.close()

        cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 3, 1))
        assert len(cuotas) == 3
        # generar_cuotas_mensuales (Sprint 41/75, fix posterior de revision de
        # codigo) ya copia tasa_moratoria_anual/ibc_vigente_anual del padre y
        # setea fecha_vencimiento == fecha_origen en cada cuota hija -- no hace
        # falta completarlos a mano (ver test_reajuste_anual.py::
        # test_genera_cuotas_copia_campos_requeridos_por_comercial).

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion_recurrente, *cuotas],
            abonos=[],
            fecha_corte=date(2024, 3, 1),
        )

        # Solo las 3 cuotas hijas reales (500000 x 3 = 1500000) -- el padre
        # RECURRENTE no debe aportar un capital fantasma adicional via
        # FamilyScheduler encima de las cuotas ya generadas. Sin el fix, esto da
        # 3000000.00 (el doble).
        total_esperado = sum((cuota.valor for cuota in cuotas), Decimal("0.00"))
        assert total_esperado == Decimal("1500000.00")
        assert resultado.final_balance().principal == total_esperado

    def test_no_duplica_sancion_de_usura_del_padre_cuando_ya_tiene_cuotas_generadas(self):
        """Hallazgo de revision de codigo posterior al fix de
        test_no_duplica_capital_del_padre_cuando_ya_tiene_cuotas_generadas (arriba): ese fix
        solo se aplico al path principal de liquidar() (la lambda eventos_fn que pasa
        ids_con_cuotas_generadas a _eventos_de_obligacion). _calcular_sancion_usura llama
        a self._eventos_de_obligacion(obligacion, fecha_corte) con solo 2 argumentos
        posicionales -- ids_con_cuotas_generadas nunca llega ahi, asi que para una
        obligacion RECURRENTE con cuotas hijas ya generadas y una tasa por encima del tope
        de usura, esa liquidacion sombra vuelve a expandir el padre via FamilyScheduler
        (capital fantasma) y produce una sancion adicional que se suma, via
        _aplicar_sanciones_usura, al MISMO resultado consolidado que ya incluye la sancion
        real de cada cuota hija -- la sancion de usura queda doblemente aplicada.

        tasa_moratoria_anual = 60% supera el tope (1.5 x ibc 20% = 30%); cada cuota hija
        vence el mismo dia que se causa (fecha_vencimiento == fecha_origen), asi que la
        tasa moratoria corre desde el dia 1 -- Comercial evalua la sancion de usura sobre
        cada cuota real. Sin el fix, el padre RECURRENTE contribuye una sancion fantasma
        extra encima de esas 3 sanciones reales."""
        session = session_module.get_session()
        obligacion_recurrente = Obligacion(
            expediente_id=1,
            tipo=TipoObligacion.RECURRENTE,
            concepto="CUOTAS DE PAGARE A PLAZOS",
            categoria="CAPITAL_PAGARE",
            fecha_origen=date(2024, 1, 1),
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=date(2024, 3, 1),
            dia_pago=1,
            valor=Decimal("500000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
            tasa_moratoria_anual=Decimal("60.00"),
            fecha_vencimiento=date(2024, 1, 1),
            ibc_vigente_anual=Decimal("20.00"),
            tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
        )
        session.add(obligacion_recurrente)
        session.commit()
        session.close()

        cuotas = generar_cuotas_mensuales(obligacion_recurrente, fecha_corte=date(2024, 3, 1))
        assert len(cuotas) == 3
        # generar_cuotas_mensuales ya copia tasa_moratoria_anual/ibc_vigente_anual
        # del padre y setea fecha_vencimiento == fecha_origen en cada cuota hija
        # (ver comentario equivalente en
        # test_no_duplica_capital_del_padre_cuando_ya_tiene_cuotas_generadas arriba).

        resultado_combinado = ComercialStrategy().liquidar(
            obligaciones=[obligacion_recurrente, *cuotas],
            abonos=[],
            fecha_corte=date(2024, 3, 1),
        )
        resultado_solo_cuotas = ComercialStrategy().liquidar(
            obligaciones=cuotas,
            abonos=[],
            fecha_corte=date(2024, 3, 1),
        )

        # El padre RECURRENTE no debe aportar capital NI sancion de usura adicional una
        # vez que sus cuotas hijas ya fueron generadas -- liquidar padre+cuotas debe dar
        # el mismo saldo final que liquidar solo las cuotas hijas. Sin el fix, el saldo
        # combinado tiene una sancion de usura extra (mas negativa / mas favorable al
        # deudor) que el de solo las cuotas.
        assert resultado_combinado.final_balance() == resultado_solo_cuotas.final_balance()

    def test_soporta_indexacion_ipc_es_false(self):
        assert ComercialStrategy().soporta_indexacion_ipc is False

    def test_aplica_indexacion_ipc_sin_pacto_expreso_lanza_value_error(self):
        # Sprint 43, regla XOR: la tasa comercial ya incorpora inflacion, asi que
        # marcar IPC sin un pacto expreso en el titulo se bloquea.
        obligacion = _obligacion_comercial()
        obligacion.aplica_indexacion_ipc = True
        obligacion.pacto_expreso_indexacion = False

        with pytest.raises(ValueError, match="[Pp]acto expreso"):
            ComercialStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
            )

    def test_modo_ipc_con_pacto_expreso_recurrente_lanza_value_error(self):
        # Sprint 43: el modo (b) queda reducido a PUNTUAL (mismo alcance que
        # anatocismo en esta clase) -- RECURRENTE no modela un pacto expreso por
        # cuota individual.
        obligacion = Obligacion(
            id=2,
            expediente_id=1,
            tipo=TipoObligacion.RECURRENTE,
            concepto="Cuotas de pagare a plazos",
            categoria="CAPITAL_PAGARE",
            fecha_origen=date(2025, 1, 1),
            valor=Decimal("500000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
            tasa_moratoria_anual=Decimal("24.00"),
            fecha_vencimiento=date(2025, 1, 1),
            ibc_vigente_anual=Decimal("20.00"),
            dia_pago=5,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 3, 5),
            aplica_indexacion_ipc=True,
            pacto_expreso_indexacion=True,
        )

        with pytest.raises(ValueError, match="PUNTUAL"):
            ComercialStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 5)
            )

    def test_modo_ipc_con_pacto_expreso_indexa_capital_y_usa_interes_civil_en_vez_de_comercial(
        self,
    ):
        # Sprint 43, modo (b): capital indexado por IPC + interes civil puro 6% anual
        # sobre el capital ya indexado, EN VEZ DE la tasa comercial (remuneratoria 6%/
        # moratoria 24%) que trae _obligacion_comercial(). Reutiliza tal cual
        # AreaStrategy._evento_indexacion_ipc (interpolacion ANUAL) -- el mismo
        # mecanismo compartido que usaban Comercial/Honorarios/Sancionatorio/Laboral Y
        # Civil/Familia antes del Sprint 80.
        #
        # Sprint 80 le dio a CivilFamiliaStrategy su PROPIA implementacion de
        # _evento_indexacion (indice IPC mensual real para fechas dentro de rango,
        # ver historical_index._IPC_MENSUAL) -- Comercial/Honorarios/Sancionatorio/
        # Laboral NO cambiaron, siguen en la anual. Por eso ya no sirve comparar en
        # vivo contra CivilFamiliaStrategy().liquidar(...) para este caso (fechas
        # dentro del rango mensual): darian numeros distintos a proposito, no por un
        # bug. Los valores de abajo (77,633.53 / 94,283.40) son los mismos que
        # CivilFamiliaStrategy daba para este capital/fechas ANTES del Sprint 80
        # (ver historial de test_civil_familia_puntual_con_indexacion_... y
        # test_civil_familia_suma_unica_activa_interes_es_mayor_que_legado) --
        # siguen siendo la referencia correcta para el modo (b) de Comercial, que no
        # cambio.
        obligacion = _obligacion_comercial(
            valor=Decimal("1000000.00"),
            fecha_origen=date(2024, 7, 1),
            fecha_vencimiento=date(2024, 8, 1),
        )
        obligacion.aplica_indexacion_ipc = True
        obligacion.pacto_expreso_indexacion = True

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 31)
        )

        assert resultado.final_balance().principal == Decimal("1000000.00")
        assert resultado.final_balance().indexation == Decimal("77633.53")
        assert resultado.final_balance().interest == Decimal("94283.40")

    def test_modo_ipc_activo_no_dispara_sancion_por_usura(self):
        # Sprint 43: la tasa realmente cobrada en modo (b) es la civil legal (nunca
        # usuraria), asi que tasa_efectiva_anual/tasa_moratoria_anual (aunque el
        # formulario las siga exigiendo como campos obligatorios) no deben disparar la
        # sancion por usura del Sprint 2 -- esa tasa nunca se usa para cobrar nada en
        # este modo.
        obligacion = _obligacion_comercial(
            valor=Decimal("1000000.00"),
            fecha_origen=date(2024, 7, 1),
            fecha_vencimiento=date(2024, 8, 1),
            tasa_remuneratoria=Decimal("9999.00"),  # muy por encima de cualquier usura
            tasa_moratoria=Decimal("9999.00"),
        )
        obligacion.aplica_indexacion_ipc = True
        obligacion.pacto_expreso_indexacion = True

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 9, 1)
        )

        assert all("usura" not in item.concept.lower() for item in resultado.items)

    def test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa(self):
        fecha_corte = date(2025, 1, 11)  # antes del vencimiento (2025-06-01) de ambas
        obligacion_a = _obligacion_comercial(
            fecha_origen=date(2025, 1, 1),
            fecha_vencimiento=date(2025, 6, 1),
            tasa_remuneratoria=Decimal("6.00"),
        )
        obligacion_a.id = 111
        obligacion_b = _obligacion_comercial(
            fecha_origen=date(2025, 1, 1),
            fecha_vencimiento=date(2025, 6, 1),
            tasa_remuneratoria=Decimal("18.00"),
        )
        obligacion_b.id = 112

        resultado_combinado = ComercialStrategy().liquidar(
            obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_a = ComercialStrategy().liquidar(
            obligaciones=[obligacion_a], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_b = ComercialStrategy().liquidar(
            obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado_combinado.final_balance().principal == Decimal("2000000.00")
        interes_esperado = (
            resultado_solo_a.final_balance().interest + resultado_solo_b.final_balance().interest
        )
        assert resultado_combinado.final_balance().interest == interes_esperado
        assert (
            resultado_combinado.final_balance().interest
            != Decimal("2") * resultado_solo_a.final_balance().interest
        )

    def test_items_tienen_rate_source_por_tramo(self):
        obligacion = _obligacion_comercial()

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        fuentes = {item.rate_source for item in resultado.items}
        assert "Tasa remuneratoria pactada (Art. 884 C.Co.)" in fuentes
        assert "Tasa moratoria pactada (Art. 884 C.Co.)" in fuentes

    def test_obligacion_en_usd_convierte_el_capital_a_pesos_antes_de_liquidar(self):
        obligacion_usd = _obligacion_comercial(valor=Decimal("10000.00"))
        obligacion_usd.moneda = "USD"
        obligacion_usd.trm_aplicable = Decimal("4000.0000")
        obligacion_usd.trm_fecha_referencia = date(2025, 1, 1)

        resultado_usd = ComercialStrategy().liquidar(
            obligaciones=[obligacion_usd], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        obligacion_cop = _obligacion_comercial(valor=Decimal("40000000.00"))
        resultado_cop = ComercialStrategy().liquidar(
            obligaciones=[obligacion_cop], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        assert resultado_usd.final_balance().principal == Decimal("40000000.00")
        assert resultado_usd.final_balance().interest == resultado_cop.final_balance().interest

    def test_obligacion_usd_sin_trm_aplicable_usa_el_proveedor_dinamico_en_la_fecha_de_origen(
        self,
    ):
        # Respuesta del despacho (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 12): "eliminar
        # la logica de TRM congelada al inicio" -- trm_aplicable ya NO es
        # obligatorio. Sin el, se usa el TRMProvider inyectado (en produccion,
        # SFCTRMProvider, la API en vivo de la SFC), consultado en la fecha real
        # del evento.
        obligacion = _obligacion_comercial(valor=Decimal("10000.00"))
        obligacion.moneda = "USD"
        proveedor = _TRMProviderDeCalendario({date(2025, 1, 1): Decimal("4000.0000")})

        resultado = ComercialStrategy(trm_provider=proveedor).liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        assert resultado.final_balance().principal == Decimal("40000000.00")

    def test_abono_en_usd_se_convierte_con_la_trm_de_su_propia_fecha_de_pago(self):
        # El nucleo de la correccion del Sprint 12: cada abono usa la TRM
        # vigente en SU PROPIA fecha, no la del origen de la obligacion (que
        # aqui usa una TRM distinta, 4000, para dejar clara la diferencia).
        obligacion = _obligacion_comercial(valor=Decimal("10000.00"))
        obligacion.moneda = "USD"
        proveedor = _TRMProviderDeCalendario(
            {
                date(2025, 1, 1): Decimal("4000.0000"),
                date(2025, 2, 1): Decimal("4200.0000"),
            }
        )
        abono = Abono(
            id=1,
            obligacion_id=1,
            fecha=date(2025, 2, 1),
            monto=Decimal("1000.00"),
            referencia="ref-1",
        )

        resultado = ComercialStrategy(trm_provider=proveedor).liquidar(
            obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2025, 3, 1)
        )

        # 1.000 USD x TRM del 2025-02-01 (4.200) = 4.200.000 COP aplicados --
        # NO 1.000 x TRM del origen (4.000) = 4.000.000, que habria sido el
        # resultado con la TRM "congelada" que corrige este sprint.
        assert resultado.total_payments_applied() == Decimal("4200000.00")

    def test_obligacion_usd_con_trm_aplicable_manual_ignora_el_proveedor_dinamico(self):
        # trm_aplicable sigue siendo una anulacion manual valida (compatibilidad):
        # si esta seteado, se usa ese valor fijo para todo, sin tocar el
        # proveedor dinamico -- ni siquiera se consulta.
        obligacion = _obligacion_comercial(valor=Decimal("10000.00"))
        obligacion.moneda = "USD"
        obligacion.trm_aplicable = Decimal("4000.0000")
        proveedor_que_no_deberia_usarse = _TRMProviderDeCalendario(
            {}
        )  # lanzaria KeyError si se consulta
        abono = Abono(
            id=1,
            obligacion_id=1,
            fecha=date(2025, 2, 1),
            monto=Decimal("1000.00"),
            referencia="ref-1",
        )

        resultado = ComercialStrategy(trm_provider=proveedor_que_no_deberia_usarse).liquidar(
            obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2025, 3, 1)
        )

        assert resultado.total_payments_applied() == Decimal("4000000.00")

    @pytest.mark.parametrize("trm_invalida", [Decimal("0.0000"), Decimal("-100.0000")])
    def test_obligacion_usd_con_trm_no_positiva_lanza_value_error(self, trm_invalida):
        obligacion = _obligacion_comercial()
        obligacion.moneda = "USD"
        obligacion.trm_aplicable = trm_invalida
        obligacion.trm_fecha_referencia = date(2025, 1, 1)

        with pytest.raises(ValueError, match="trm_aplicable"):
            ComercialStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
            )

    def test_obligacion_sin_moneda_seteada_se_trata_como_cop(self):
        obligacion = _obligacion_comercial()
        assert obligacion.moneda is None  # atributo no seteado en construccion directa, sin sesion

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        assert resultado.final_balance().principal == obligacion.valor

    def test_ambas_condiciones_de_anatocismo_a_la_vez_lanza_value_error(self):
        obligacion = _obligacion_comercial(
            anatocismo_demanda_judicial=True,
            anatocismo_fecha_acuerdo=date(2026, 2, 15),
        )

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 1)
            )

    def test_recurrente_con_anatocismo_activo_lanza_value_error(self):
        obligacion = Obligacion(
            id=2,
            expediente_id=1,
            tipo=TipoObligacion.RECURRENTE,
            concepto="Cuotas de pagare a plazos",
            categoria="CAPITAL_PAGARE",
            fecha_origen=date(2025, 1, 1),
            valor=Decimal("500000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
            tasa_moratoria_anual=Decimal("24.00"),
            fecha_vencimiento=date(2025, 1, 1),
            ibc_vigente_anual=Decimal("20.00"),
            dia_pago=5,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 3, 5),
            anatocismo_demanda_judicial=True,
        )

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 5)
            )

    def test_acuerdo_posterior_que_no_cumple_un_anio_lanza_value_error(self):
        # vencimiento 2025-02-01 + 365 dias = 2026-02-01; un acuerdo antes de esa fecha es
        # invalido.
        obligacion = _obligacion_comercial(anatocismo_fecha_acuerdo=date(2026, 1, 15))

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 1)
            )

    def test_acuerdo_posterior_que_cumple_exactamente_un_anio_no_lanza_error(self):
        obligacion = _obligacion_comercial(anatocismo_fecha_acuerdo=date(2026, 2, 1))

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 1)
        )

        assert resultado.final_balance().principal > obligacion.valor

    def test_anatocismo_se_activa_con_demanda_judicial_y_mora_mayor_a_un_anio(self):
        fecha_corte = date(2026, 3, 1)
        obligacion_anatocismo = _obligacion_comercial(anatocismo_demanda_judicial=True)
        resultado_anatocismo = ComercialStrategy().liquidar(
            obligaciones=[obligacion_anatocismo], abonos=[], fecha_corte=fecha_corte
        )

        obligacion_simple = _obligacion_comercial()
        resultado_simple = ComercialStrategy().liquidar(
            obligaciones=[obligacion_simple], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado_anatocismo.final_balance().principal > obligacion_anatocismo.valor
        assert (
            resultado_anatocismo.final_balance().total() > resultado_simple.final_balance().total()
        )

    def test_anatocismo_se_activa_con_acuerdo_posterior_valido(self):
        fecha_corte = date(2026, 3, 1)
        obligacion = _obligacion_comercial(anatocismo_fecha_acuerdo=date(2026, 2, 15))

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado.final_balance().principal > obligacion.valor

    def test_anatocismo_no_se_activa_sin_condicion_habilitante(self):
        fecha_corte = date(2026, 3, 1)
        obligacion = _obligacion_comercial()

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado.final_balance().principal == obligacion.valor

    def test_anatocismo_no_se_activa_si_fecha_corte_es_anterior_a_capitalizacion(self):
        fecha_corte = date(
            2025, 6, 1
        )  # vencimiento (2025-02-01) + 365 dias = 2026-02-01, aun no llega
        obligacion = _obligacion_comercial(anatocismo_demanda_judicial=True)

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado.final_balance().principal == obligacion.valor

    def test_timing_del_abono_relativo_a_la_capitalizacion_determina_cuanto_se_capitaliza(self):
        # Capitalizacion: 2026-02-01 (vencimiento 2025-02-01 + 365 dias).
        monto_abono = Decimal("50.00")  # deliberadamente pequeno: nunca llega a tocar el
        # capital, solo el bucket de interes -- eso es lo que hace la comparacion exacta.

        obligacion_abono_antes = _obligacion_comercial(anatocismo_demanda_judicial=True)
        abono_antes = Abono(
            id=1, obligacion_id=1, fecha=date(2026, 1, 31), monto=monto_abono, referencia="ref-1"
        )
        resultado_antes = ComercialStrategy().liquidar(
            obligaciones=[obligacion_abono_antes],
            abonos=[abono_antes],
            fecha_corte=date(2026, 3, 1),
        )

        obligacion_abono_despues = _obligacion_comercial(anatocismo_demanda_judicial=True)
        abono_despues = Abono(
            id=1, obligacion_id=1, fecha=date(2026, 2, 2), monto=monto_abono, referencia="ref-1"
        )
        resultado_despues = ComercialStrategy().liquidar(
            obligaciones=[obligacion_abono_despues],
            abonos=[abono_despues],
            fecha_corte=date(2026, 3, 1),
        )

        # Un abono un dia ANTES de la capitalizacion (2026-02-01) reduce el interes que
        # alcanza a capitalizarse (el monto es deliberadamente pequeno, nunca toca el
        # capital); el mismo abono un dia DESPUES ya no resta nada del monto ya
        # capitalizado -- la capitalizacion ya ocurrio. La diferencia de capital final
        # entre ambos escenarios debe ser exactamente el monto del abono: prueba que el
        # orden cronologico abono/capitalizacion se respeta de verdad, no solo que "un
        # abono reduce el total" (eso ya lo garantiza AllocationEngine sin necesidad de
        # anatocismo).
        diferencia = (
            resultado_despues.final_balance().principal - resultado_antes.final_balance().principal
        )
        assert diferencia == monto_abono

    def test_anatocismo_capitaliza_periodicamente_en_cada_aniversario(self):
        obligacion_antes_primera = _obligacion_comercial(anatocismo_demanda_judicial=True)
        resultado_antes_primera = ComercialStrategy().liquidar(
            obligaciones=[obligacion_antes_primera], abonos=[], fecha_corte=date(2026, 1, 31)
        )

        obligacion_despues_primera = _obligacion_comercial(anatocismo_demanda_judicial=True)
        resultado_despues_primera = ComercialStrategy().liquidar(
            obligaciones=[obligacion_despues_primera], abonos=[], fecha_corte=date(2027, 1, 31)
        )

        obligacion_despues_segunda = _obligacion_comercial(anatocismo_demanda_judicial=True)
        resultado_despues_segunda = ComercialStrategy().liquidar(
            obligaciones=[obligacion_despues_segunda], abonos=[], fecha_corte=date(2027, 2, 2)
        )

        principal_antes_primera = resultado_antes_primera.final_balance().principal
        principal_despues_primera = resultado_despues_primera.final_balance().principal
        principal_despues_segunda = resultado_despues_segunda.final_balance().principal

        # Antes de la primera capitalizacion (2026-02-01), el capital nunca crece por
        # anatocismo -- sigue igual al valor original.
        assert principal_antes_primera == obligacion_antes_primera.valor

        # Justo antes de la segunda capitalizacion (2027-02-01): ya paso la primera, el
        # capital creció una vez.
        assert principal_despues_primera > obligacion_despues_primera.valor

        # Justo despues de la segunda capitalizacion: el capital crece de nuevo, a partir
        # de la base YA aumentada por la primera -- no del valor original. Si la segunda
        # capitalizacion compusiera solo sobre el valor original (bug de "reset" en el
        # bucle), el segundo salto seria igual al primero; en compuesto real sobre una
        # base mayor, el segundo salto debe ser estrictamente mayor que el primero.
        primer_salto = principal_despues_primera - obligacion_despues_primera.valor
        segundo_salto = principal_despues_segunda - principal_despues_primera
        assert segundo_salto > primer_salto


def test_comercial_genera_evento_de_costas_si_esta_configurado():
    # Mismo caso de referencia que Tasks 4/11/12/14: 123.500.000 en el punto
    # medio del tier menor cuantia de 2024 -> costas = 8.645.000,00.
    obligacion = _obligacion_comercial(valor=Decimal("123500000.00"))
    obligacion.fecha_origen = date(2024, 6, 1)
    obligacion.fecha_vencimiento = date(2024, 7, 1)  # debe ser posterior a fecha_origen
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"

    resultado = ComercialStrategy().liquidar([obligacion], [], fecha_corte=obligacion.fecha_origen)
    tipos_evento = {item.balance.event_type for item in resultado.items}
    assert "COSTAS_PROCESALES" in tipos_evento
    assert resultado.final_balance().principal == Decimal(
        "132145000.00"
    )  # 123.500.000 + 8.645.000


def test_comercial_usd_calcula_costas_sobre_el_valor_convertido_a_pesos_no_sobre_el_valor_en_usd():
    # Regresion: confirma que las costas se calculan sobre valor_pesos (post
    # conversion TRM), no sobre obligacion.valor crudo en USD -- si alguien
    # revierte a pasar obligacion.valor, este test debe fallar.
    obligacion = _obligacion_comercial(valor=Decimal("30875.00"))
    obligacion.moneda = "USD"
    obligacion.trm_aplicable = Decimal("4000.00")
    obligacion.trm_fecha_referencia = date(2024, 6, 1)
    obligacion.fecha_origen = date(2024, 6, 1)
    obligacion.fecha_vencimiento = date(2024, 7, 1)
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"

    resultado = ComercialStrategy().liquidar([obligacion], [], fecha_corte=obligacion.fecha_origen)
    # 30.875 USD * 4.000 TRM = 123.500.000 pesos -> costas = 8.645.000,00 (7%,
    # punto medio del tier menor cuantia) -> total 132.145.000,00. Si el
    # calculo usara el valor crudo en USD (30.875) como pretensiones, el
    # resultado seria completamente distinto (y probablemente lanzaria
    # TarifaNoDisponibleError o un monto absurdo).
    assert resultado.final_balance().principal == Decimal("132145000.00")


def test_civil_familia_soporta_indexacion_ipc_es_true():
    assert CivilFamiliaStrategy().soporta_indexacion_ipc is True


def test_civil_familia_items_tienen_rate_source_poblado():
    strategy = CivilFamiliaStrategy()
    obligacion = _obligacion_puntual()

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
    )

    assert all(
        item.rate_source == "Tasa pactada en la obligación (Art. 1617 C.C.)"
        for item in resultado.items
    )


def _obligacion_sancionatoria(
    expediente_id=1,
    cantidad_smlmv_uvt=Decimal("2"),
    fecha_origen=date(2019, 6, 1),
    tasa_efectiva_anual=Decimal("0.00"),
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Multa SIC",
        categoria="MULTA_SANCIONATORIA",
        fecha_origen=fecha_origen,
        valor=Decimal("0.00"),
        tasa_efectiva_anual=tasa_efectiva_anual,
        cantidad_smlmv_uvt=cantidad_smlmv_uvt,
    )


class TestSancionatorioStrategy:
    def test_liquida_multa_pre_2020_convirtiendo_smlmv_a_pesos(self):
        obligacion = _obligacion_sancionatoria()

        resultado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2019, 6, 1)
        )

        # SMLMV 2019 = 828116.00 (ver historical_index.py); 2 SMLMV = 1656232.00.
        assert resultado.final_balance().principal == Decimal("1656232.00")

    def test_liquida_multa_posterior_a_2020_convirtiendo_uvt_a_pesos(self):
        obligacion = _obligacion_sancionatoria(fecha_origen=date(2021, 1, 1))

        resultado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        # UVT 2021 = 36308.00; cantidad_smlmv_uvt por defecto en el factory es 2.
        assert resultado.final_balance().principal == Decimal("72616.00")

    def test_falta_cantidad_smlmv_uvt_lanza_value_error(self):
        obligacion = _obligacion_sancionatoria(cantidad_smlmv_uvt=None)

        with pytest.raises(ValueError):
            SancionatorioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2019, 6, 1)
            )

    def test_obligacion_recurrente_lanza_value_error(self):
        obligacion = _obligacion_sancionatoria()
        obligacion.tipo = TipoObligacion.RECURRENTE

        with pytest.raises(ValueError):
            SancionatorioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2019, 6, 1)
            )

    def test_multa_impaga_acumula_interes_moratorio_si_se_pacto_tasa(self):
        obligacion = _obligacion_sancionatoria(tasa_efectiva_anual=Decimal("24.00"))

        resultado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2020, 6, 1)
        )

        assert resultado.final_balance().interest > Decimal("0.00")

    def test_soporta_indexacion_ipc_es_true(self):
        # Sprint 43: SancionatorioStrategy ahora SI soporta IPC (condicional,
        # la conversion SMLMV/UVT ya anclada a la fecha del hecho es siempre la
        # excepcion del despacho con el motor actual -- ver docstring de la clase).
        assert SancionatorioStrategy().soporta_indexacion_ipc is True

    def test_sin_indexacion_ipc_no_genera_evento_indexation(self):
        obligacion = _obligacion_sancionatoria()  # aplica_indexacion_ipc no seteado -> falsy

        resultado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2020, 6, 1)
        )

        assert resultado.final_balance().indexation == Decimal("0.00")
        assert all(item.balance.event_type != "INDEXATION" for item in resultado.items)

    def test_aplica_indexacion_ipc_indexa_el_capital_ya_convertido_a_pesos(self):
        # Sprint 43: la excepcion del despacho (multa anclada a SMLMV/UVT a la fecha
        # DEL HECHO) siempre aplica con este motor -- ver docstring de la clase. El
        # capital que se indexa es el YA CONVERTIDO a pesos (2 SMLMV 2019 =
        # 1,656,232.00, ver test_liquida_multa_pre_2020_convirtiendo_smlmv_a_pesos),
        # desde fecha_origen (exigibilidad) hasta la fecha de corte (pago efectivo).
        from app.engine.indexation.historical_index import get_ipc_interpolado_for_date
        from app.engine.indexation.ipc import IPCIndexation

        fecha_origen = date(2019, 6, 1)
        fecha_corte = date(2020, 6, 1)
        obligacion = _obligacion_sancionatoria(fecha_origen=fecha_origen)
        obligacion.aplica_indexacion_ipc = True

        resultado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        capital_convertido = Decimal("1656232.00")
        monto_esperado = IPCIndexation.calculate(
            capital=capital_convertido,
            initial_index=get_ipc_interpolado_for_date(fecha_origen),
            final_index=get_ipc_interpolado_for_date(fecha_corte),
        )
        eventos_indexacion = [
            item for item in resultado.items if item.balance.event_type == "INDEXATION"
        ]
        assert len(eventos_indexacion) == 1
        assert monto_esperado > Decimal("0.00")
        assert eventos_indexacion[0].indexation_amount == monto_esperado
        assert resultado.final_balance().indexation == monto_esperado
        assert resultado.final_balance().principal == capital_convertido

    def test_sancionatorio_genera_evento_de_costas_si_esta_configurado(self):
        # cantidad_smlmv_uvt=1000 con el fecha_origen por defecto del fixture
        # (2019-06-01, pre-2020 -> usa SMLMV, no UVT): monto_pesos = 1000 *
        # 828116.00 = 828.116.000,00 -- muy por encima de 150 SMLMV(2019) =
        # 124.217.400,00, cae en el tier "mayor cuantia" (sin techo), que siempre
        # usa el porcentaje minimo del rango (3%) sin necesidad de interpolar.
        # costas = 828.116.000 * 3% = 24.843.480,00, pero el tope de 20 SMLMV(2019)
        # = 16.562.320,00 es menor -> se aplica el tope. Este caso ademas ejercita
        # el tope de la Task 4 con un ejemplo end-to-end real.
        obligacion = _obligacion_sancionatoria(cantidad_smlmv_uvt=_Decimal("1000"))
        obligacion.costas_tipo_proceso = "declarativo_general"
        obligacion.costas_instancia = "primera"

        resultado = SancionatorioStrategy().liquidar(
            [obligacion], [], fecha_corte=obligacion.fecha_origen
        )
        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "COSTAS_PROCESALES" in tipos_evento
        assert resultado.final_balance().principal == _Decimal(
            "844678320.00"
        )  # 828.116.000 + 16.562.320

    def test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa(self):
        fecha_corte = date(2019, 6, 11)
        obligacion_a = _obligacion_sancionatoria(tasa_efectiva_anual=Decimal("12.00"))
        obligacion_a.id = 121
        obligacion_b = _obligacion_sancionatoria(tasa_efectiva_anual=Decimal("24.00"))
        obligacion_b.id = 122

        resultado_combinado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_a = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion_a], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_b = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
        )

        interes_esperado = (
            resultado_solo_a.final_balance().interest + resultado_solo_b.final_balance().interest
        )
        assert resultado_combinado.final_balance().interest == interes_esperado
        assert (
            resultado_combinado.final_balance().interest
            != Decimal("2") * resultado_solo_a.final_balance().interest
        )


def _obligacion_honorarios(
    expediente_id=1,
    honorarios_fijos_pactados=Decimal("1000000.00"),
    cuota_litis_pactada_pct=Decimal("20.00"),
    beneficio_obtenido=Decimal("10000000.00"),
    costas_pct_manual=None,
    fecha_origen=date(2026, 1, 1),
    tasa_efectiva_anual=Decimal("0.00"),
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Honorarios proceso ejecutivo",
        categoria="HONORARIOS_PROFESIONALES",
        fecha_origen=fecha_origen,
        valor=Decimal("0.00"),
        tasa_efectiva_anual=tasa_efectiva_anual,
        honorarios_fijos_pactados=honorarios_fijos_pactados,
        cuota_litis_pactada_pct=cuota_litis_pactada_pct,
        beneficio_obtenido=beneficio_obtenido,
        costas_pct_manual=costas_pct_manual,
    )


def test_honorarios_liquidar_reutiliza_honorarios_total_pct_entre_obligaciones_con_la_misma_fecha(
    monkeypatch,
):
    from app.services import parametro_service

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    obligaciones = [
        _obligacion_honorarios(fecha_origen=date(2026, 1, 1)),
        _obligacion_honorarios(fecha_origen=date(2026, 1, 1)),
        _obligacion_honorarios(fecha_origen=date(2026, 1, 1)),
    ]
    for indice, obligacion in enumerate(obligaciones, start=1):
        obligacion.id = indice

    HonorariosStrategy().liquidar(
        obligaciones=obligaciones, abonos=[], fecha_corte=date(2026, 1, 1)
    )

    llamadas_honorarios = [
        llamada for llamada in llamadas if llamada[0] == "HONORARIOS_TOTAL_PCT"
    ]
    assert len(llamadas_honorarios) == 1


def test_evento_costas_procesales_usa_costas_pct_manual_si_esta_presente():
    obligacion = _obligacion_honorarios(costas_pct_manual=_Decimal("5.00"))
    evento = _evento_costas_procesales(
        obligacion, pretensiones_reconocidas=_Decimal("10000000.00")
    )
    assert evento is not None
    assert evento.payload["amount"] == _Decimal("500000.00")
    assert evento.event_type == "COSTAS_PROCESALES"


def test_evento_costas_procesales_usa_calculo_automatico_si_hay_tipo_e_instancia():
    # fecha_origen se fuerza a 2024-06-01 (SMLMV 2024 = 1.300.000.00) para que
    # 123.500.000 caiga exactamente en el punto medio del tier menor cuantia
    # (52.000.000 a 195.000.000) -> pct = 10 - 0.5*6 = 7%. El default de
    # _obligacion_honorarios (fecha_origen=2026-01-01) tambien funcionaria,
    # pero forzar el año mantiene el mismo caso de referencia usado en el
    # resto del plan (Tasks 4, 12, 13).
    obligacion = _obligacion_honorarios()
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"
    evento = _evento_costas_procesales(
        obligacion, pretensiones_reconocidas=_Decimal("123500000.00")
    )
    assert evento is not None
    assert evento.payload["amount"] == _Decimal("8645000.00")


def test_evento_costas_procesales_manual_gana_sobre_automatico():
    # 5% (no 7%, el automatico) -- dentro del rango permitido para menor cuantia
    # (3%-7%, respuesta del despacho Sprint 18) para que la validacion nueva no falle.
    obligacion = _obligacion_honorarios(costas_pct_manual=_Decimal("5.00"))
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"
    evento = _evento_costas_procesales(
        obligacion, pretensiones_reconocidas=_Decimal("123500000.00")
    )
    assert evento.payload["amount"] == _Decimal("6175000.00")  # 5% manual, no el 7% automatico


def test_evento_costas_procesales_manual_fuera_de_rango_lanza_error():
    # Respuesta del despacho (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 18): mayor cuantia
    # (>150 SMMLV) permite 1%-5% -- el sistema debe rechazar, no truncar, un valor
    # fuera de ese rango (ejemplo textual del despacho: "el usuario no podra ingresar
    # un 8% de agencias en derecho" en un proceso de Mayor Cuantia).
    from app.core.exceptions import CostasFueraDeRangoError

    obligacion = _obligacion_honorarios(
        costas_pct_manual=_Decimal("8.00"), fecha_origen=_date(2026, 1, 1)
    )
    # SMLMV 2026 = 1.750.905 -> 300.000.000 / 1.750.905 = ~171 SMMLV -> Mayor Cuantia.
    with pytest.raises(CostasFueraDeRangoError):
        _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("300000000.00"))


def test_evento_costas_procesales_manual_dentro_de_rango_no_lanza_error():
    obligacion = _obligacion_honorarios(
        costas_pct_manual=_Decimal("3.00"), fecha_origen=_date(2026, 1, 1)
    )

    evento = _evento_costas_procesales(
        obligacion, pretensiones_reconocidas=_Decimal("300000000.00")
    )

    assert evento is not None
    assert evento.payload["amount"] == _Decimal("9000000.00")


def test_evento_costas_procesales_sin_ninguno_de_los_dos_retorna_none():
    obligacion = _obligacion_honorarios()
    evento = _evento_costas_procesales(
        obligacion, pretensiones_reconocidas=_Decimal("10000000.00")
    )
    assert evento is None


def test_evento_costas_procesales_providencia_pre_cgp_lanza_error():
    # Sprint 18 (ultraactividad CPC->CGP, Art. 624 CGP): la providencia que
    # impone costas es anterior al 1/1/2016 -- el sistema no tiene tabla de
    # tarifas pre-CGP, debe rechazar en vez de aproximar.
    from app.core.exceptions import TarifaPreCGPNoDisponibleError

    obligacion = _obligacion_honorarios()
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"
    obligacion.fecha_providencia_costas = _date(2015, 6, 1)

    with pytest.raises(TarifaPreCGPNoDisponibleError):
        _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("123500000.00"))


def test_evento_costas_procesales_providencia_none_no_cambia_el_comportamiento():
    # Regresion: fecha_providencia_costas=None (default del modelo, campo
    # aditivo no capturado hoy) da exactamente el mismo resultado que antes
    # de este sprint.
    obligacion = _obligacion_honorarios()
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"
    assert obligacion.fecha_providencia_costas is None

    evento = _evento_costas_procesales(
        obligacion, pretensiones_reconocidas=_Decimal("123500000.00")
    )
    assert evento is not None
    assert evento.payload["amount"] == _Decimal("8645000.00")


def test_evento_costas_procesales_providencia_posterior_a_cgp_no_cambia_el_resultado():
    obligacion = _obligacion_honorarios()
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"
    obligacion.fecha_providencia_costas = _date(2024, 5, 1)

    evento = _evento_costas_procesales(
        obligacion, pretensiones_reconocidas=_Decimal("123500000.00")
    )
    assert evento is not None
    assert evento.payload["amount"] == _Decimal("8645000.00")


class TestHonorariosStrategy:
    def test_liquida_honorarios_dentro_del_tope_total(self):
        # cuota litis = 10M * 20% = 2M. total = 1M + 2M = 3M (30% <= 50% tope total, OK).
        obligacion = _obligacion_honorarios()

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
        )

        assert resultado.final_balance().principal == Decimal("3000000.00")

    def test_cuota_litis_sola_por_encima_de_30_por_ciento_no_lanza_error_si_el_total_no_excede_50(
        self,
    ):
        # Respuesta del despacho (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 4): no se
        # aplican dos topes en cascada -- el unico tope legal es el 50% acumulado. cuota litis =
        # 10M * 35% = 3.5M (35% individual, por encima de lo que antes era un tope
        # propio de 30%), pero honorarios_fijos=0 asi que el total (3.5M) sigue por
        # debajo del 50% (5M) -> ya no debe fallar.
        obligacion = _obligacion_honorarios(
            honorarios_fijos_pactados=Decimal("0.00"), cuota_litis_pactada_pct=Decimal("35.00")
        )

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
        )

        assert resultado.final_balance().principal == Decimal("3500000.00")

    def test_suma_total_excede_50_por_ciento_lanza_error_citando_ley_1123_de_2007(self):
        # cuota litis = 10M * 45% = 4.5M. total = 1M + 4.5M = 5.5M > 5M (50% de 10M).
        obligacion = _obligacion_honorarios(
            honorarios_fijos_pactados=Decimal("1000000.00"),
            cuota_litis_pactada_pct=Decimal("45.00"),
        )

        with pytest.raises(CuotaLitisExcedeTopeError, match="Ley 1123/2007"):
            HonorariosStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
            )

    def test_genera_evento_de_costas_si_costas_pct_manual_esta_seteado(self):
        # honorarios = 1M + (10M*10%=1M) = 2M. costas = 10M * 5% = 500000.
        obligacion = _obligacion_honorarios(
            cuota_litis_pactada_pct=Decimal("10.00"), costas_pct_manual=Decimal("5.00")
        )

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
        )

        assert resultado.final_balance().principal == Decimal("2500000.00")

    def test_sin_costas_pct_manual_no_genera_evento_de_costas(self):
        obligacion = _obligacion_honorarios(cuota_litis_pactada_pct=Decimal("10.00"))

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
        )

        # honorarios = 1M + (10M*10%=1M) = 2M, sin costas.
        assert resultado.final_balance().principal == Decimal("2000000.00")

    @pytest.mark.parametrize(
        "campo", ["honorarios_fijos_pactados", "cuota_litis_pactada_pct", "beneficio_obtenido"]
    )
    def test_falta_un_campo_obligatorio_lanza_value_error(self, campo):
        obligacion = _obligacion_honorarios()
        setattr(obligacion, campo, None)

        with pytest.raises(ValueError):
            HonorariosStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
            )

    def test_obligacion_recurrente_lanza_value_error(self):
        obligacion = _obligacion_honorarios()
        obligacion.tipo = TipoObligacion.RECURRENTE

        with pytest.raises(ValueError):
            HonorariosStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
            )

    def test_soporta_indexacion_ipc_es_true(self):
        # Sprint 43: HonorariosStrategy ahora SI soporta IPC, habilitado por
        # defecto (incondicional, compatible con el interes civil).
        assert HonorariosStrategy().soporta_indexacion_ipc is True

    def test_sin_indexacion_ipc_usa_la_tasa_pactada_sin_indexar(self):
        # Regresion: sin el checkbox marcado, comportamiento identico a antes del
        # Sprint 43 (tasa pactada, capital nominal, sin evento INDEXATION).
        obligacion = _obligacion_honorarios(
            honorarios_fijos_pactados=Decimal("1000000.00"),
            cuota_litis_pactada_pct=Decimal("0.00"),
            fecha_origen=date(2024, 7, 1),
            tasa_efectiva_anual=Decimal("12.00"),
        )

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 31)
        )

        assert resultado.final_balance().indexation == Decimal("0.00")
        assert all(item.balance.event_type != "INDEXATION" for item in resultado.items)

    def test_aplica_indexacion_ipc_sigue_la_formula_exacta_del_despacho(self):
        # Sprint 43, formula EXACTA:
        #   Capital_Honorarios x (IPC_Final / IPC_Inicial)
        #     + Interés_Civil_6%_Anual(Capital_Actualizado)
        # honorarios_fijos_pactados=1,000,000 + cuota_litis 0% = total_honorarios
        # 1,000,000. Reutiliza tal cual AreaStrategy._evento_indexacion_ipc (anual) --
        # Honorarios no cambio en el Sprint 80 (solo CivilFamiliaStrategy tiene su
        # propia implementacion mensual desde entonces, ver el comentario del test
        # del modo (b) de Comercial mas arriba en este archivo -- clase
        # TestComercialStrategy, metodo test_modo_ipc_con_pacto_expreso... -- para
        # el detalle completo de por que ya no se compara en vivo contra
        # CivilFamiliaStrategy para este rango de fechas). Los valores de abajo
        # (77,633.53 / mismo interes que la version pre-Sprint-80 de
        # test_civil_familia_suma_unica_activa_interes_es_mayor_que_legado) siguen
        # siendo la referencia correcta porque el modo Suma Unica + tasa civil
        # plana de Honorarios no cambio.
        # tasa_efectiva_anual=99.00 (deliberadamente distinta del 6% civil) prueba que la
        # formula usa la tasa civil FIJA, no la tasa pactada de esta obligacion.
        obligacion = _obligacion_honorarios(
            honorarios_fijos_pactados=Decimal("1000000.00"),
            cuota_litis_pactada_pct=Decimal("0.00"),
            fecha_origen=date(2024, 7, 1),
            tasa_efectiva_anual=Decimal("99.00"),
        )
        obligacion.aplica_indexacion_ipc = True

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 31)
        )

        assert resultado.final_balance().principal == Decimal("1000000.00")
        assert resultado.final_balance().indexation == Decimal("77633.53")
        assert resultado.final_balance().interest == Decimal("94283.40")

    def test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa(self):
        fecha_corte = date(2026, 1, 11)
        obligacion_a = _obligacion_honorarios(
            cuota_litis_pactada_pct=Decimal("10.00"), tasa_efectiva_anual=Decimal("12.00")
        )
        obligacion_a.id = 131
        obligacion_b = _obligacion_honorarios(
            cuota_litis_pactada_pct=Decimal("10.00"), tasa_efectiva_anual=Decimal("24.00")
        )
        obligacion_b.id = 132

        resultado_combinado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_a = HonorariosStrategy().liquidar(
            obligaciones=[obligacion_a], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_b = HonorariosStrategy().liquidar(
            obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
        )

        interes_esperado = (
            resultado_solo_a.final_balance().interest + resultado_solo_b.final_balance().interest
        )
        assert resultado_combinado.final_balance().interest == interes_esperado
        assert (
            resultado_combinado.final_balance().interest
            != Decimal("2") * resultado_solo_a.final_balance().interest
        )


def _obligacion_laboral(
    expediente_id=1,
    salario=Decimal("3000000.00"),
    fecha_inicio=date(2020, 1, 1),
    fecha_fin=date(2020, 12, 31),
    pagada=False,
    fecha_pago_total=None,
    tipo=TipoObligacion.PUNTUAL,
    despido_injustificado=False,
    tipo_contrato_laboral=TipoContratoLaboral.INDEFINIDO,
    fecha_fin_pactada=None,
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=tipo,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=fecha_inicio,
        valor=salario,
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        pagada=pagada,
        fecha_pago_total=fecha_pago_total,
        despido_injustificado=despido_injustificado,
        tipo_contrato_laboral=tipo_contrato_laboral,
        fecha_fin_pactada=fecha_fin_pactada,
    )


class TestLaboralStrategy:
    def test_liquida_sin_mora_si_se_pago_el_mismo_dia_de_terminacion(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SANCION_MORATORIA" not in tipos_evento
        # dias_trabajados_prestaciones = 360 (2020-01-01 a 2020-12-31, año
        # comercial completo de 12 meses de 30 dias, conteo inclusivo --
        # Sprint 30): cesantias 3000000.00 + intereses 360000.00 + prima x2
        # 3000000.00 + vacaciones 1500000.00 = 7860000.00.
        assert resultado.final_balance().principal == Decimal("7860000.00")

    def test_liquida_con_mora_solo_fase1(self):
        # Pagado 30 dias despues de terminar el contrato -- solo fase 1.
        obligacion = _obligacion_laboral(fecha_pago_total=date(2021, 1, 30))

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SANCION_MORATORIA" in tipos_evento
        # salario_diario = 3M/30 = 100000; 30 dias de retardo = 3000000.00
        assert resultado.final_balance().principal == Decimal(
            "10860000.00"
        )  # 7860000.00 + 3000000.00

    def test_liquida_con_mora_cruzando_a_fase2(self):
        # Sin pagar: fecha_corte muy posterior a la terminacion del contrato,
        # suficiente para cruzar a fase 2 (mas de 720 dias de retardo).
        obligacion = _obligacion_laboral()
        fecha_corte = obligacion.fecha_fin + timedelta(days=800)

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        monto_prestaciones = Decimal("7860000.00")
        mora_esperada = MoratoryIndemnityCalculator.calcular(
            salario_mensual=obligacion.valor,
            monto_adeudado=monto_prestaciones,
            fecha_terminacion=obligacion.fecha_fin,
            fecha_pago_o_corte=fecha_corte,
        )
        assert mora_esperada.dias_fase2 > 0
        assert resultado.final_balance().principal == monto_prestaciones + mora_esperada.total

    def test_aplica_un_abono_reduciendo_el_saldo(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        abono = Abono(
            id=1,
            obligacion_id=1,
            fecha=date(2021, 1, 15),
            monto=Decimal("1000000.00"),
            referencia="ref-1",
        )

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2021, 6, 1)
        )

        assert resultado.total_payments_applied() == Decimal("1000000.00")
        assert resultado.final_balance().total() < Decimal("7860000.00")

    def test_mas_de_una_obligacion_lanza_value_error(self):
        obligacion_1 = _obligacion_laboral(expediente_id=1)
        obligacion_2 = _obligacion_laboral(expediente_id=1)

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion_1, obligacion_2], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_tipo_recurrente_lanza_value_error(self):
        obligacion = _obligacion_laboral(tipo=TipoObligacion.RECURRENTE)

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_fecha_fin_anterior_a_fecha_inicio_lanza_value_error(self):
        obligacion = _obligacion_laboral(
            fecha_inicio=date(2020, 12, 31), fecha_fin=date(2020, 1, 1)
        )

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_pagada_true_sin_fecha_pago_total_lanza_value_error(self):
        # pagada=True sin fecha_pago_total es un estado inconsistente: si se
        # dejara pasar, liquidar() trataria la obligacion como no pagada y
        # correria la mora hasta fecha_corte, sobrestimandola silenciosamente.
        obligacion = _obligacion_laboral(pagada=True, fecha_pago_total=None)

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_fecha_pago_total_posterior_a_fecha_corte_se_recorta_al_corte(self):
        # "Foto historica": si el pago real ocurrio despues del corte elegido
        # para este reporte, la mora se calcula solo hasta fecha_corte, no
        # hasta la fecha de pago real (que todavia esta en el futuro respecto
        # al corte).
        fecha_corte = date(2021, 3, 1)
        obligacion = _obligacion_laboral(fecha_pago_total=date(2022, 1, 1))

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        monto_prestaciones = Decimal("7860000.00")
        mora_esperada = MoratoryIndemnityCalculator.calcular(
            salario_mensual=obligacion.valor,
            monto_adeudado=monto_prestaciones,
            fecha_terminacion=obligacion.fecha_fin,
            fecha_pago_o_corte=fecha_corte,
        )
        assert resultado.final_balance().principal == monto_prestaciones + mora_esperada.total

    def test_soporta_indexacion_ipc_es_true(self):
        # Sprint 43: LaboralStrategy ahora SI soporta IPC (condicional,
        # excluyente con la indemnizacion moratoria del Art. 65 CST).
        assert LaboralStrategy().soporta_indexacion_ipc is True

    def test_sin_mora_con_indexacion_ipc_indexa_las_prestaciones(self):
        # Sprint 43, excepcion 1 (buena fe probada): pagado el mismo dia de
        # terminacion -> sin mora (ver
        # test_liquida_sin_mora_si_se_pago_el_mismo_dia_de_terminacion,
        # mismo monto_prestaciones ya verificado ahi: 7,860,000.00). Con
        # aplica_indexacion_ipc marcado, se indexa ese valor desde fecha_fin
        # (2020-12-31) hasta la fecha de corte (2021-06-01).
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.aplica_indexacion_ipc = True

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SANCION_MORATORIA" not in tipos_evento
        assert "INDEXATION" in tipos_evento
        assert resultado.final_balance().indexation > Decimal("0.00")
        assert resultado.alertas == []

    def test_con_mora_e_indexacion_ipc_alerta_doble_actualizacion_prohibida(self):
        # Sprint 43, regla de exclusion: pagado 30 dias tarde -> SI hay mora (ver
        # test_liquida_con_mora_solo_fase1). Con aplica_indexacion_ipc marcado a la
        # vez, la moratoria prevalece (no se indexa el mismo rubro/periodo dos
        # veces) y se agrega la alerta no bloqueante "Doble Actualización
        # Prohibida" -- la liquidacion NO se bloquea.
        obligacion = _obligacion_laboral(fecha_pago_total=date(2021, 1, 30))
        obligacion.aplica_indexacion_ipc = True

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SANCION_MORATORIA" in tipos_evento
        assert "INDEXATION" not in tipos_evento
        assert resultado.final_balance().indexation == Decimal("0.00")
        assert len(resultado.alertas) == 1
        assert "Doble Actualización Prohibida" in resultado.alertas[0]
        # El saldo (mora incluida) es identico al caso sin IPC marcado -- la
        # alerta es puramente informativa, no cambia ningun numero.
        assert resultado.final_balance().principal == Decimal("10860000.00")

    def test_incluir_seguridad_social_sin_nivel_riesgo_lanza_value_error(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = None

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_incluir_seguridad_social_agrega_cotizaciones_a_la_deuda(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "COTIZACION_PENSION" in tipos_evento
        assert "COTIZACION_SALUD" in tipos_evento
        assert "COTIZACION_ARL" in tipos_evento
        # 7860000.00 (prestaciones existentes, Sprint 30: dias_trabajados_
        # prestaciones=360, base comercial) + cotizaciones sobre 365 dias
        # reales (SIN cambios en este sprint -- fuera de alcance, ver
        # LaboralStrategy.liquidar), IBC 3000000.00, nivel I, sin suspension
        # ni FSP (ver SeguridadSocialCalculator):
        # pension = 3000000*0.16*365/30 = 5840000.00
        # salud   = 3000000*0.125*365/30 = 4562500.00
        # arl     = 3000000*0.00522*365/30 = 190530.00
        assert resultado.final_balance().principal == Decimal("18453030.00")

    def test_sin_incluir_seguridad_social_no_hay_regresion(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        # incluir_seguridad_social queda en su default (False)

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "COTIZACION_PENSION" not in tipos_evento
        assert resultado.final_balance().principal == Decimal("7860000.00")

    def test_incapacidad_comun_agrega_solo_el_monto_del_empleador_a_la_deuda(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [
            EventoLaboral(
                obligacion_id=1,
                tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2020, 5, 1),
                fecha_fin=date(2020, 5, 4),  # 3 dias
            )
        ]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "INCAPACIDAD_EMPLEADOR" in tipos_evento
        assert "INCAPACIDAD_INFORMATIVA" in tipos_evento
        # IBC = 3000000.00 (sin suspension, sin FSP); dias 1-2 empleador
        # 66.67% = 133340.00; dia 3 EPS 66.67% = 66670.00 (informativo, no suma).
        eventos_incapacidad_empleador = [
            item for item in resultado.items if item.balance.event_type == "INCAPACIDAD_EMPLEADOR"
        ]
        assert eventos_incapacidad_empleador[0].capital_base >= Decimal("133340.00")

    def test_incapacidad_laboral_no_agrega_nada_a_la_deuda_pero_deja_traza(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [
            EventoLaboral(
                obligacion_id=1,
                tipo=TipoEventoLaboral.INCAPACIDAD_LABORAL,
                fecha_inicio=date(2020, 5, 1),
                fecha_fin=date(2020, 5, 11),  # 10 dias
            )
        ]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "INCAPACIDAD_INFORMATIVA" in tipos_evento
        assert "INCAPACIDAD_EMPLEADOR" not in tipos_evento

    def test_suspension_excluye_arl_de_esos_dias_y_deja_traza(self):
        from database.models import EventoLaboral, MotivoSuspension, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [
            EventoLaboral(
                obligacion_id=1,
                tipo=TipoEventoLaboral.SUSPENSION,
                fecha_inicio=date(2020, 3, 1),
                fecha_fin=date(2020, 3, 31),  # 30 dias
                motivo_suspension=MotivoSuspension.HUELGA,
            )
        ]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SUSPENSION_INFORMATIVA" in tipos_evento
        assert "COTIZACION_ARL" in tipos_evento
        eventos_arl = [
            item for item in resultado.items if item.balance.event_type == "COTIZACION_ARL"
        ]
        # dias_trabajados=365, dias_suspension=30: arl = 3000000*0.00522*(365-30)/30
        assert eventos_arl[0].capital_base > Decimal("0.00")

    def test_suspension_e_incapacidad_combinadas_en_el_mismo_contrato(self):
        from database.models import EventoLaboral, MotivoSuspension, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [
            EventoLaboral(
                obligacion_id=1,
                tipo=TipoEventoLaboral.SUSPENSION,
                fecha_inicio=date(2020, 3, 1),
                fecha_fin=date(2020, 3, 31),
                motivo_suspension=MotivoSuspension.HUELGA,
            ),
            EventoLaboral(
                obligacion_id=1,
                tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2020, 5, 1),
                fecha_fin=date(2020, 5, 4),
            ),
        ]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SUSPENSION_INFORMATIVA" in tipos_evento
        assert "INCAPACIDAD_EMPLEADOR" in tipos_evento
        assert "INCAPACIDAD_INFORMATIVA" in tipos_evento
        assert "COTIZACION_ARL" in tipos_evento

    def test_mora_fase2_no_incluye_cotizaciones_de_seguridad_social_en_la_base(self):
        # Regresion: con incluir_seguridad_social=True y retardo suficiente
        # para cruzar a fase 2 del Art. 65 CST, la base de la indemnizacion
        # moratoria (monto_adeudado) debe seguir siendo solo prestaciones
        # sociales -- NO debe incluir las cotizaciones de seguridad social no
        # pagadas (esas tienen consecuencias legales separadas, fuera de
        # alcance de este sprint).
        obligacion = _obligacion_laboral()
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        fecha_corte = obligacion.fecha_fin + timedelta(days=800)

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        monto_prestaciones = Decimal("7860000.00")
        mora_esperada = MoratoryIndemnityCalculator.calcular(
            salario_mensual=obligacion.valor,
            monto_adeudado=monto_prestaciones,
            fecha_terminacion=obligacion.fecha_fin,
            fecha_pago_o_corte=fecha_corte,
        )
        assert mora_esperada.dias_fase2 > 0

        # prestaciones (7860000.00, Sprint 30: dias_trabajados_prestaciones=
        # 360, base comercial) + cotizaciones (pension+salud+arl sobre 365
        # dias reales, IBC 3000000.00, nivel I, sin suspension/FSP -- mismo
        # valor que test_incluir_seguridad_social_agrega_cotizaciones_a_la_
        # deuda) + mora calculada SOLO sobre prestaciones (el fix, sin
        # relacion con el Sprint 30).
        monto_prestaciones_y_cotizaciones = Decimal("18453030.00")
        assert (
            resultado.final_balance().principal
            == monto_prestaciones_y_cotizaciones + mora_esperada.total
        )

        # Si la mora hubiera usado (bug) prestaciones+cotizaciones como base,
        # el total de la mora seria mayor -- confirma que el fix realmente
        # cambia el resultado y no es una coincidencia numerica.
        mora_con_bug = MoratoryIndemnityCalculator.calcular(
            salario_mensual=obligacion.valor,
            monto_adeudado=monto_prestaciones_y_cotizaciones,
            fecha_terminacion=obligacion.fecha_fin,
            fecha_pago_o_corte=fecha_corte,
        )
        assert mora_con_bug.total > mora_esperada.total

    def test_cotizacion_pension_expone_label_amigable_como_concept(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        eventos_pension = [
            item for item in resultado.items if item.balance.event_type == "COTIZACION_PENSION"
        ]
        assert len(eventos_pension) == 1
        assert "COTIZACION_PENSION" not in eventos_pension[0].concept
        assert "Pension" in eventos_pension[0].concept

    def test_eventos_laborales_sin_incluir_seguridad_social_lanza_value_error(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        # incluir_seguridad_social queda en su default (False) a proposito.
        obligacion.eventos_laborales = [
            EventoLaboral(
                obligacion_id=1,
                tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2020, 5, 1),
                fecha_fin=date(2020, 5, 4),
            )
        ]

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_evento_laboral_con_fecha_fuera_del_contrato_lanza_value_error(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [
            EventoLaboral(
                obligacion_id=1,
                tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2021, 1, 1),
                fecha_fin=date(2021, 1, 5),  # posterior a fecha_fin del contrato (2020-12-31)
            )
        ]

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_evento_laboral_con_fecha_inicio_anterior_al_contrato_lanza_value_error(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [
            EventoLaboral(
                obligacion_id=1,
                tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2019, 12, 20),
                fecha_fin=date(2019, 12, 25),  # anterior a fecha_inicio del contrato (2020-01-01)
            )
        ]

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_dos_eventos_laborales_solapados_lanza_value_error(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [
            EventoLaboral(
                obligacion_id=1,
                tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2020, 5, 1),
                fecha_fin=date(2020, 5, 10),
            ),
            EventoLaboral(
                obligacion_id=1,
                tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2020, 5, 5),
                fecha_fin=date(2020, 5, 15),  # se solapa con el anterior (5/5 - 5/10)
            ),
        ]

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_eventos_laborales_consecutivos_no_solapados_no_lanza_error(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [
            EventoLaboral(
                obligacion_id=1,
                tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2020, 5, 1),
                fecha_fin=date(2020, 5, 10),
            ),
            EventoLaboral(
                obligacion_id=1,
                tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2020, 5, 10),
                fecha_fin=date(
                    2020, 5, 15
                ),  # empieza justo cuando termina el anterior, no se solapa
            ),
        ]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        assert resultado is not None  # no lanza error

    def test_laboral_genera_evento_de_costas_si_esta_configurado(self):
        from app.engine.costs.agencias_en_derecho import (
            Instancia,
            TipoProceso,
            calcular_agencias_en_derecho,
        )
        from app.engine.temporal.schedulers.labor import LaborScheduler

        # _obligacion_laboral no acepta 'valor' como parametro (usa 'salario'), y
        # LaboralStrategy genera varios eventos ademas de costas (cesantias,
        # prima, vacaciones) -- final_balance().principal mezclaria todo. Se aisla
        # el monto de costas comparando el capital_base acumulado justo antes y
        # justo despues del item de costas, en vez de sumar todo el saldo.
        # Nota: COSTAS_PROCESALES se fecha en obligacion.fecha_origen (=
        # fecha_inicio), anterior a fecha_fin (fecha de cesantias/prima/
        # vacaciones) -- por eso siempre ordena de primero (indice 0) y la
        # rama "capital_previo" con indice_costas > 0 no se ejercita en este
        # caso particular; se deja la forma generica (delta entre item actual
        # y el anterior) porque es la misma tecnica usada en las demas
        # strategies y sigue siendo correcta (capital_previo = 0.00 cuando
        # costas es el primer item).
        obligacion = _obligacion_laboral(
            salario=Decimal("123500000.00"),
            fecha_inicio=date(2024, 1, 1),
            fecha_fin=date(2024, 6, 1),
        )
        obligacion.costas_tipo_proceso = "declarativo_general"
        obligacion.costas_instancia = "primera"

        resultado = LaboralStrategy().liquidar([obligacion], [], fecha_corte=obligacion.fecha_fin)

        tipos_evento = [item.balance.event_type for item in resultado.items]
        assert "COSTAS_PROCESALES" in tipos_evento
        indice_costas = tipos_evento.index("COSTAS_PROCESALES")
        capital_previo = (
            resultado.items[indice_costas - 1].capital_base
            if indice_costas > 0
            else Decimal("0.00")
        )
        monto_costas = resultado.items[indice_costas].capital_base - capital_previo

        # La base de costas es monto_prestaciones (cesantias + intereses +
        # prima + vacaciones para todo el contrato), NO obligacion.valor (que
        # es solo el salario mensual) -- ver LaboralStrategy.liquidar. Se
        # recalcula aqui, de forma independiente, con el mismo LaborScheduler
        # que usa produccion, para no depender de una constante "magica" sin
        # trazabilidad. dias_trabajados usa la misma formula comercial de
        # 360 dias que produccion (Sprint 30) -- ver CalendarUtils.
        # dias_comerciales_360.
        from app.engine.time.calendar import CalendarUtils

        dias_trabajados = CalendarUtils.dias_comerciales_360(
            obligacion.fecha_inicio, obligacion.fecha_fin
        )
        eventos_prestaciones = LaborScheduler(
            salario_base=obligacion.valor,
            dias_trabajados=dias_trabajados,
            fecha_liquidacion=obligacion.fecha_fin,
        ).generate()
        monto_prestaciones = sum(
            (e.payload["amount"] for e in eventos_prestaciones), Decimal("0.00")
        )
        assert monto_prestaciones == Decimal("132110808.78")

        # fecha_origen (= fecha_inicio) 2024-01-01 -> SMLMV 2024 = 1.300.000,00
        # -> declarativo_general / primera instancia, tier MENOR cuantia
        # (52.000.000-195.000.000): interpolacion lineal Paragrafo 3 art. 3
        # (Acuerdo PSAA16-10554) da porcentaje = ~6.6387% ->
        # 132.110.808,78 * ese % = 8.770.449,94 -- verificado tambien llamando
        # calcular_agencias_en_derecho directamente con pretensiones_reconocidas
        # = monto_prestaciones.
        assert monto_costas == Decimal("8770449.94")
        assert monto_costas == calcular_agencias_en_derecho(
            tipo_proceso=TipoProceso("declarativo_general"),
            instancia=Instancia("primera"),
            pretensiones_reconocidas=monto_prestaciones,
            fecha_radicacion=obligacion.fecha_inicio,
        )

    def test_costas_procesales_no_afecta_la_indemnizacion_moratoria(self):
        # Regresion critica: costas procesales debe aparecer como evento
        # independiente, pero NUNCA debe alimentar monto_adeudado (la base del
        # Art. 65 CST para SANCION_MORATORIA) -- ver LaboralStrategy.liquidar,
        # donde monto_prestaciones se captura en un Decimal ANTES de appendear
        # el evento de costas a `eventos`. Si costas se hubiera insertado antes
        # de esa linea (bug), monto_adeudado incluiria costas y la mora
        # calculada seria mayor -- PERO SOLO en fase 2 (dias_retardo > 720):
        # fase 1 (Art. 65 CST) es "un dia de salario por cada dia de retardo",
        # no usa monto_adeudado en absoluto (ver MoratoryIndemnityCalculator.
        # calcular), asi que un escenario de solo fase 1 no detectaria este
        # bug. Se usa el mismo patron de
        # test_mora_fase2_no_incluye_cotizaciones_de_seguridad_social_en_la_base
        # (retardo de 800 dias, cruza a fase 2) para que la comparacion sea
        # realmente sensible al bug.
        #
        # Se corre el mismo escenario (mismo salario, mismas fechas, mora
        # fase 2) dos veces -- una sin costas configuradas y otra con -- y se
        # compara el monto exacto de SANCION_MORATORIA (aislado via delta de
        # capital_base, igual tecnica que para costas arriba) entre ambas
        # corridas: deben ser identicos.
        def _liquidar_y_aislar_mora(con_costas: bool) -> Decimal:
            # fecha_fin=2024-05-01 (en vez de 2024-06-01, usado en el test de
            # costas de arriba) para que fecha_fin + 800 dias (2026-07-10)
            # siga cayendo dentro de los tramos IBC/Usura sembrados por la
            # fixture (hasta 2026-07-31) -- con 2024-06-01 el retardo de 800
            # dias cae en 2026-08, fuera de rango, y ademas monto_prestaciones
            # (105.448.531,01 para este contrato mas corto) debe seguir
            # cayendo en el tier MENOR cuantia de declarativo_general/primera
            # (52M-195M) para que costas se pueda calcular sin
            # TarifaNoDisponibleError (el acuerdo no tiene tarifa para tier
            # MINIMA en primera instancia -- las cuantias minimas se tramitan
            # en unica instancia, no en dos instancias).
            obligacion = _obligacion_laboral(
                salario=Decimal("123500000.00"),
                fecha_inicio=date(2024, 1, 1),
                fecha_fin=date(2024, 5, 1),
            )
            if con_costas:
                obligacion.costas_tipo_proceso = "declarativo_general"
                obligacion.costas_instancia = "primera"
            # 800 dias de retardo: cruza a fase 2 (limite fase 1 = 720 dias),
            # donde monto_adeudado si entra en el calculo de intereses.
            fecha_corte = obligacion.fecha_fin + timedelta(days=800)

            resultado = LaboralStrategy().liquidar([obligacion], [], fecha_corte=fecha_corte)

            tipos_evento = [item.balance.event_type for item in resultado.items]
            assert "SANCION_MORATORIA" in tipos_evento
            if con_costas:
                assert "COSTAS_PROCESALES" in tipos_evento
            indice_mora = tipos_evento.index("SANCION_MORATORIA")
            capital_previo = (
                resultado.items[indice_mora - 1].capital_base
                if indice_mora > 0
                else Decimal("0.00")
            )
            return resultado.items[indice_mora].capital_base - capital_previo

        monto_mora_sin_costas = _liquidar_y_aislar_mora(con_costas=False)
        monto_mora_con_costas = _liquidar_y_aislar_mora(con_costas=True)

        assert monto_mora_sin_costas > Decimal("0.00")  # sanity: la mora si se disparo
        assert monto_mora_con_costas == monto_mora_sin_costas

    def test_es_smmlv_resuelve_el_valor_desde_el_smlmv_del_anio_del_contrato(self):
        # Sprint 44, punto 1: con es_smmlv=True, LaboralStrategy debe ignorar
        # el 'valor' capturado a mano (aqui deliberadamente distinto del SMLMV
        # real, para que el test detecte si el override no se aplico) y
        # resolver el salario base desde get_smlmv_for_year(fecha_origen.year)
        # -- _SMLMV_POR_ANIO[2020] = 877803.00 (sembrado por la fixture
        # autouse de este archivo).
        obligacion = _obligacion_laboral(
            salario=Decimal("1.00"),
            fecha_inicio=date(2020, 1, 1),
            fecha_fin=date(2020, 12, 31),
        )
        obligacion.es_smmlv = True

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=obligacion.fecha_fin
        )

        assert obligacion.valor == Decimal("877803.00")
        # cesantias (salario) + intereses cesantias (12% del salario) +
        # prima (salario, sumando junio+diciembre) + vacaciones (salario/2),
        # sobre el SMLMV resuelto, no sobre 1.00 -- misma proporcion
        # (multiplicador 2.62) que test_liquida_sin_mora_si_se_pago_el_mismo_dia_de_terminacion
        # verifica para un salario de 3000000.00 (7860000.00 = 3000000.00 * 2.62).
        assert resultado.final_balance().principal == Decimal("2299843.86")

    def test_es_smmlv_false_conserva_el_valor_digitado(self):
        obligacion = _obligacion_laboral(
            salario=Decimal("3000000.00"),
            fecha_inicio=date(2020, 1, 1),
            fecha_fin=date(2020, 12, 31),
        )
        obligacion.es_smmlv = False

        LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=obligacion.fecha_fin
        )

        assert obligacion.valor == Decimal("3000000.00")

    def test_descuento_laboral_reduce_el_neto_adeudado(self):
        from database.models import DescuentoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.descuentos_laborales = [
            DescuentoLaboral(
                id=1,
                obligacion_id=1,
                fecha=date(2021, 1, 15),
                monto=Decimal("1000000.00"),
                es_legal=True,
                motivo="Prestamo cooperativa",
            )
        ]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        assert resultado.total_payments_applied() == Decimal("1000000.00")
        assert resultado.final_balance().total() == Decimal("7860000.00") - Decimal("1000000.00")

    def test_descuento_laboral_aparece_en_el_reporte_con_etiqueta_propia(self):
        from database.models import DescuentoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.descuentos_laborales = [
            DescuentoLaboral(
                id=1,
                obligacion_id=1,
                fecha=date(2021, 1, 15),
                monto=Decimal("1000000.00"),
                es_legal=True,
                motivo="Prestamo cooperativa",
            )
        ]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        conceptos = [item.concept for item in resultado.items]
        coincidencias = [c for c in conceptos if "Descuento" in c]
        assert len(coincidencias) == 1
        assert "legal" in coincidencias[0].lower()
        assert "Prestamo cooperativa" in coincidencias[0]

    def test_descuento_laboral_ilegal_tambien_reduce_el_neto_y_se_marca_distinto(self):
        # es_legal es metadata descriptiva para el reporte (para que el
        # abogado distinga un descuento autorizado de uno que no lo fue) --
        # no cambia el calculo: ambos reutilizan el mismo mecanismo de
        # pagos/allocation ya existente (ver LaboralStrategy.liquidar).
        from database.models import DescuentoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.descuentos_laborales = [
            DescuentoLaboral(
                id=1,
                obligacion_id=1,
                fecha=date(2021, 1, 15),
                monto=Decimal("500000.00"),
                es_legal=False,
                motivo=None,
            )
        ]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        assert resultado.total_payments_applied() == Decimal("500000.00")
        conceptos = [item.concept for item in resultado.items]
        coincidencias = [c for c in conceptos if "Descuento" in c]
        assert len(coincidencias) == 1
        assert "ilegal" in coincidencias[0].lower()

    def test_varios_descuentos_laborales_se_suman(self):
        from database.models import DescuentoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.descuentos_laborales = [
            DescuentoLaboral(
                id=1,
                obligacion_id=1,
                fecha=date(2021, 1, 15),
                monto=Decimal("500000.00"),
                es_legal=True,
            ),
            DescuentoLaboral(
                id=2,
                obligacion_id=1,
                fecha=date(2021, 2, 1),
                monto=Decimal("300000.00"),
                es_legal=True,
            ),
        ]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        assert resultado.total_payments_applied() == Decimal("800000.00")

    def test_despido_injustificado_indefinido_agrega_evento_indemnizacion_despido(self):
        # 2020-01-01 a 2020-12-31 (360 dias comerciales, 1 año exacto) -- regimen
        # post-Ley 50/1990 (fecha_ingreso posterior al corte 1991-01-01): 30 dias
        # flat (ver DismissalIndemnityCalculator).
        obligacion = _obligacion_laboral(
            fecha_pago_total=date(2020, 12, 31), despido_injustificado=True
        )

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "INDEMNIZACION_DESPIDO" in tipos_evento
        salario_diario = obligacion.valor / Decimal("30")
        indemnizacion_esperada = (salario_diario * Decimal("30")).quantize(Decimal("0.01"))
        # 7860000.00 = prestaciones (ver test de mas arriba) + la indemnizacion.
        esperado = Decimal("7860000.00") + indemnizacion_esperada
        assert resultado.final_balance().principal == esperado

    def test_despido_con_justa_causa_no_agrega_evento_indemnizacion_despido(self):
        obligacion = _obligacion_laboral(
            fecha_pago_total=date(2020, 12, 31), despido_injustificado=False
        )

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "INDEMNIZACION_DESPIDO" not in tipos_evento

    def test_despido_injustificado_coexiste_con_sancion_moratoria(self):
        # Sin pago (mora, fase 1) y despido injustificado a la vez -- el sprint
        # confirma que son conceptos compatibles, ninguno excluye al otro (ver
        # docs/Preguntas-Para-Abogado-Abiertas.md, Sprint 92): ambos eventos
        # deben coexistir en el mismo expediente.
        obligacion = _obligacion_laboral(fecha_pago_total=None, despido_injustificado=True)

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 1, 30)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SANCION_MORATORIA" in tipos_evento
        assert "INDEMNIZACION_DESPIDO" in tipos_evento

    def test_despido_injustificado_termino_fijo_usa_fecha_fin_pactada(self):
        obligacion = _obligacion_laboral(
            fecha_inicio=date(2020, 1, 1),
            fecha_fin=date(2020, 6, 1),
            fecha_pago_total=date(2020, 6, 1),
            despido_injustificado=True,
            tipo_contrato_laboral=TipoContratoLaboral.FIJO,
            fecha_fin_pactada=date(2021, 1, 1),
        )

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "INDEMNIZACION_DESPIDO" in tipos_evento
        esperado = DismissalIndemnityCalculator.calcular(
            tipo_contrato=TipoContratoLaboral.FIJO,
            salario_mensual=obligacion.valor,
            fecha_ingreso=obligacion.fecha_inicio,
            fecha_terminacion=obligacion.fecha_fin,
            despido_injustificado=True,
            smlmv_mensual=Decimal("877803.00"),  # SMLMV 2020
            fecha_fin_pactada=obligacion.fecha_fin_pactada,
        )
        assert esperado.total > Decimal("0.00")

    def test_despido_injustificado_termino_fijo_sin_fecha_fin_pactada_lanza_value_error(self):
        obligacion = _obligacion_laboral(
            despido_injustificado=True,
            tipo_contrato_laboral=TipoContratoLaboral.FIJO,
            fecha_fin_pactada=None,
        )

        with pytest.raises(ValueError, match="fecha_fin_pactada"):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_despido_injustificado_salario_10_smmlv_usa_tabla_ley_789_2002(self):
        # SMLMV 2020 = 877803.00 -> 10 SMMLV = 8778030.00. Formula confirmada
        # por el despacho (Sprint 92, 22/08/2026): 20 dias primer año + 15
        # dias/año subsiguiente para salario >= 10 SMMLV con ingreso posterior
        # al 27/12/2002 (aqui, 2020-01-01) -- ya no es un regimen no soportado.
        obligacion = _obligacion_laboral(
            salario=Decimal("9000000.00"),
            fecha_pago_total=date(2020, 12, 31),
            despido_injustificado=True,
        )

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "INDEMNIZACION_DESPIDO" in tipos_evento
        salario_diario = obligacion.valor / Decimal("30")
        indemnizacion_esperada = (salario_diario * Decimal("20")).quantize(Decimal("0.01"))
        assert indemnizacion_esperada == Decimal("6000000.00")

    def test_salario_diario_convierte_a_mensual_y_liquida_prestaciones_sobre_ese_valor(self):
        # Sprint 96 (respuesta del despacho, 22/08/2026): "no existe
        # diferencia algebraica en las formulas" -- se reutiliza
        # LaborScheduler sobre la base convertida. 100.000/dia x 7 dias/semana
        # equivale exactamente a 3.000.000,00/mes (mismo caso ya verificado en
        # test_liquida_sin_mora_si_se_pago_el_mismo_dia_de_terminacion:
        # 3000000 * 2.62 = 7860000.00).
        obligacion = _obligacion_laboral(
            salario=Decimal("1.00"),  # distinto, para detectar si no se sobreescribe
            fecha_inicio=date(2020, 1, 1),
            fecha_fin=date(2020, 12, 31),
        )
        obligacion.salario_diario = Decimal("100000.00")
        obligacion.dias_laborados_semana = 7

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=obligacion.fecha_fin
        )

        assert obligacion.valor == Decimal("3000000.00")
        assert resultado.final_balance().principal == Decimal("7860000.00")

    def test_seguridad_social_domestico_usa_ibc_minimo_1_smmlv_no_el_salario_proporcional(self):
        # Sprint 96 (respuesta del despacho, 22/08/2026):
        # IBC_Seguridad_Social = max(Salario_Proporcional, 1_SMMLV) -- solo
        # para la base de cotizacion, NO para las prestaciones sociales
        # (cesantias/prima/vacaciones), que siguen usando el salario
        # proporcional real, sin piso.
        from app.engine.labor.salario_domestico import salario_diario_a_mensual
        from app.engine.labor.seguridad_social import SeguridadSocialCalculator
        from app.engine.temporal.schedulers.labor import LaborScheduler

        obligacion = _obligacion_laboral(
            salario=Decimal("1.00"),
            fecha_inicio=date(2020, 1, 1),
            fecha_fin=date(2020, 12, 31),
        )
        obligacion.salario_diario = Decimal("50000.00")
        obligacion.dias_laborados_semana = 3
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=obligacion.fecha_fin
        )

        salario_proporcional = salario_diario_a_mensual(Decimal("50000.00"), Decimal("3"))
        assert salario_proporcional == Decimal("642857.14")
        smlmv_2020 = Decimal("877803.00")
        assert salario_proporcional < smlmv_2020  # confirma que el piso SI aplica aqui

        # Prestaciones sobre el salario proporcional REAL (sin piso).
        eventos_prestaciones = LaborScheduler(
            salario_base=salario_proporcional,
            dias_trabajados=360,
            fecha_liquidacion=obligacion.fecha_fin,
        ).generate()
        monto_prestaciones = sum(
            (e.payload["amount"] for e in eventos_prestaciones), Decimal("0.00")
        )

        # Cotizaciones sobre el IBC con piso de 1 SMMLV (877803.00, no
        # 642857.14).
        cotizaciones = SeguridadSocialCalculator.calcular(
            salario_base=smlmv_2020,
            dias_trabajados=365,
            dias_suspension=0,
            nivel_riesgo_arl="I",
            fecha_referencia=obligacion.fecha_fin,
        )
        monto_cotizaciones = (
            cotizaciones.monto_pension + cotizaciones.monto_salud + cotizaciones.monto_arl
        )

        assert resultado.final_balance().principal == monto_prestaciones + monto_cotizaciones


def _obligacion_tributaria(
    expediente_id=1,
    categoria="IMPUESTO_A_CARGO",
    fecha_origen=date(2024, 3, 1),
    valor=Decimal("0.00"),
    base_sancion_tributaria=None,
    meses_extemporaneidad=None,
    sancion_agravada=False,
    ingresos_brutos=None,
    devoluciones_rebajas_descuentos=None,
    costos=None,
    deducciones=None,
    rentas_exentas=None,
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Impuesto de renta 2024",
        categoria=categoria,
        fecha_origen=fecha_origen,
        valor=valor,
        tasa_efectiva_anual=Decimal("0.00"),
        base_sancion_tributaria=base_sancion_tributaria,
        meses_extemporaneidad=meses_extemporaneidad,
        sancion_agravada=sancion_agravada,
        ingresos_brutos=ingresos_brutos,
        devoluciones_rebajas_descuentos=devoluciones_rebajas_descuentos,
        costos=costos,
        deducciones=deducciones,
        rentas_exentas=rentas_exentas,
    )


class TestTributarioStrategy:
    def test_impuesto_a_cargo_sin_sanciones_ni_abonos_liquida_el_valor(self):
        obligacion = _obligacion_tributaria(
            categoria="IMPUESTO_A_CARGO", valor=Decimal("10000000.00")
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
        )

        assert resultado.final_balance().principal == Decimal("10000000.00")

    def test_sancion_extemporaneidad_liquida_el_monto_calculado(self):
        obligacion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD",
            base_sancion_tributaria=Decimal("10000000.00"),
            meses_extemporaneidad=2,
            fecha_origen=date(2024, 3, 1),
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
        )

        # 5% x 2 meses = 10% de 10,000,000 = 1,000,000 (por encima del piso de 10 UVT).
        assert resultado.final_balance().indexation == Decimal("1000000.00")

    def test_falta_categoria_no_reconocida_lanza_value_error(self):
        obligacion = _obligacion_tributaria(categoria="CATEGORIA_INEXISTENTE")

        with pytest.raises(ValueError):
            TributarioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
            )

    def test_falta_base_sancion_en_extemporaneidad_lanza_value_error(self):
        obligacion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD",
            base_sancion_tributaria=None,
            meses_extemporaneidad=2,
        )

        with pytest.raises(ValueError):
            TributarioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
            )

    def test_obligacion_recurrente_lanza_value_error(self):
        obligacion = _obligacion_tributaria(categoria="IMPUESTO_A_CARGO", valor=Decimal("100.00"))
        obligacion.tipo = TipoObligacion.RECURRENTE

        with pytest.raises(ValueError):
            TributarioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
            )

    def test_orden_de_imputacion_sanciones_intereses_impuesto(self):
        # Desde el Sprint 15 (correccion del Art. 867-1 E.T., 2026-08-01), TributarioStrategy
        # liquida cada obligacion en su propio LiquidationCore aislado (mismo patron que
        # Comercial/CivilFamilia desde el Sprint 21, ver _liquidar_por_obligacion) -- es la
        # unica forma de darle 0% de interes a una sancion con mora > 3 anios mientras el
        # impuesto sigue acumulando el interes E.T. 635. Efecto secundario aceptado y
        # documentado (docs/Pendientes.md, Sprint 15): un abono ya no se imputa automaticamente
        # contra el saldo combinado del expediente (sanciones primero, impuesto despues) --
        # cada abono debe indicar explicitamente, via `obligacion_id`, cual obligacion paga,
        # igual que en las demas areas desde el Sprint 21. Dentro de CADA obligacion, el
        # orden de imputacion (indexacion/sancion -> interes -> capital) sigue vigente,
        # simplemente ya no hay una bolsa compartida entre obligaciones distintas.
        impuesto = _obligacion_tributaria(
            categoria="IMPUESTO_A_CARGO",
            valor=Decimal("1000000.00"),
            fecha_origen=date(2024, 3, 1),
        )
        impuesto.id = 1
        sancion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD",
            base_sancion_tributaria=Decimal("1000000.00"),
            meses_extemporaneidad=1,
            fecha_origen=date(2024, 3, 1),
        )
        sancion.id = 2
        # Sancion efectiva: 5% x 1 mes = 50,000, muy por debajo del piso de 10 UVT 2024
        # (470,650.00) -> queda en 470,650.00. El abono a la sancion la paga por completo
        # y sobra 29,350 (que en la liquidacion aislada de esa obligacion no tiene a donde
        # ir, ya que no hay otro bucket dentro de la misma obligacion).
        abono_sancion = Abono(
            id=1,
            obligacion_id=2,
            fecha=date(2024, 3, 1),
            monto=Decimal("500000.00"),
            referencia="Abono a la sancion",
        )
        abono_impuesto = Abono(
            id=2,
            obligacion_id=1,
            fecha=date(2024, 3, 1),
            monto=Decimal("200000.00"),
            referencia="Abono al impuesto",
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[impuesto, sancion],
            abonos=[abono_sancion, abono_impuesto],
            fecha_corte=date(2024, 3, 1),
        )

        saldo = resultado.final_balance()
        # Sin intereses (mismo dia, cero dias transcurridos): impuesto 1,000,000 - 200,000 =
        # 800,000 (bucket 'principal'); sancion 470,650 - 470,650 = 0 (pagada de sobra, el
        # exceso de 29,350 no reduce el impuesto porque ya no comparten balance).
        assert saldo.indexation == Decimal("0.00")
        assert saldo.interest == Decimal("0.00")
        assert saldo.principal == Decimal("800000.00")

    def test_renta_liquida_no_genera_evento_y_queda_en_resultado_renta_liquida(self):
        obligacion = _obligacion_tributaria(
            categoria="RENTA_LIQUIDA",
            ingresos_brutos=Decimal("100000000.00"),
            devoluciones_rebajas_descuentos=Decimal("0.00"),
            costos=Decimal("40000000.00"),
            deducciones=Decimal("20000000.00"),
            rentas_exentas=Decimal("5000000.00"),
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
        )

        assert resultado.is_empty()
        assert resultado.renta_liquida is not None
        assert resultado.renta_liquida.renta_liquida_gravable == Decimal("35000000.00")
        assert resultado.final_balance().total() == Decimal("0.00")

    def test_impuesto_con_mora_mayor_a_3_anios_indexa_y_topa_al_interes_de_usura_plena(self):
        # Caso real del despacho (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 15):
        # impuesto de $100.000.000 vencido el 2018-05-10, liquidado el 2023-05-10 (5 anios
        # de mora).
        # Sprint 84 (respuesta del despacho, 22/08/2026): el interes E.T. 635 y el techo de
        # usura plena ahora usan division lineal 365/366 (no la formula compuesta anterior)
        # -- el interes E.T. 635 (140.031.700,20) mas la indexacion IPC sin topar
        # (32.814.627,80) superarian el techo de usura plena (150.031.700,86) -- la
        # indexacion debe recortarse a 10.000.000,66 (verificado independientemente en
        # tests/engine/tax/test_actualizacion_867_1.py, mismo caso).
        impuesto = _obligacion_tributaria(
            categoria="IMPUESTO_A_CARGO",
            valor=Decimal("100000000.00"),
            fecha_origen=date(2018, 5, 10),
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[impuesto], abonos=[], fecha_corte=date(2023, 5, 10)
        )

        saldo = resultado.final_balance()
        assert saldo.principal == Decimal("100000000.00")
        assert saldo.interest == Decimal("140031700.20")
        assert saldo.indexation == Decimal("10000000.66")
        assert saldo.interest + saldo.indexation == Decimal(
            "150031700.86"
        )  # == techo de usura plena
        # Sprint 43: el recorte anterior ya existia desde el Sprint 15 -- lo nuevo es la
        # alerta no bloqueante que pide el despacho cuando el techo realmente recorta.
        assert len(resultado.alertas) == 1
        assert "Techo de usura alcanzado" in resultado.alertas[0]

    def test_impuesto_protegido_por_uvr_bloquea_indexacion_867_1_con_error(self):
        # Sprint 43, prohibicion de doble cobro: mismo caso de mora > 3 anios de arriba,
        # pero la obligacion ya trae su propia proteccion inflacionaria (ej. UVR) -- no se
        # puede aplicar ADEMAS la indexacion IPC del Art. 867-1 sobre el mismo capital.
        impuesto = _obligacion_tributaria(
            categoria="IMPUESTO_A_CARGO",
            valor=Decimal("100000000.00"),
            fecha_origen=date(2018, 5, 10),
        )
        impuesto.protegida_inflacion_uvr = True

        with pytest.raises(ValueError, match="protección inflacionaria"):
            TributarioStrategy().liquidar(
                obligaciones=[impuesto], abonos=[], fecha_corte=date(2023, 5, 10)
            )

    def test_impuesto_protegido_por_uvr_sin_mora_larga_liquida_normal(self):
        # protegida_inflacion_uvr no bloquea nada si el Art. 867-1 nunca se dispara
        # (mora <= 3 anios) -- no hay indexacion IPC con la que colisionar.
        impuesto = _obligacion_tributaria(
            categoria="IMPUESTO_A_CARGO",
            valor=Decimal("100000000.00"),
            fecha_origen=date(2020, 5, 10),
        )
        impuesto.protegida_inflacion_uvr = True

        resultado = TributarioStrategy().liquidar(
            obligaciones=[impuesto], abonos=[], fecha_corte=date(2023, 5, 10)
        )

        assert resultado.final_balance().principal == Decimal("100000000.00")
        assert resultado.alertas == []

    def test_impuesto_con_mora_de_3_anios_o_menos_no_indexa(self):
        impuesto = _obligacion_tributaria(
            categoria="IMPUESTO_A_CARGO",
            valor=Decimal("100000000.00"),
            fecha_origen=date(2020, 5, 10),
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[impuesto],
            abonos=[],
            fecha_corte=date(2023, 5, 10),  # exactamente 3 anios
        )

        assert resultado.final_balance().indexation == Decimal("0.00")

    def test_sancion_con_mora_mayor_a_3_anios_no_acumula_interes_solo_indexacion(self):
        # Respuesta del despacho (Sprint 15): "para el pago extemporaneo de sanciones, no
        # se liquida interes de mora, sino que se aplica exclusivamente la actualizacion
        # inflacionaria".
        sancion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD",
            base_sancion_tributaria=Decimal("10000000.00"),
            meses_extemporaneidad=2,
            fecha_origen=date(2018, 5, 10),
        )
        # Sancion efectiva: 5% x 2 meses = 10% de 10.000.000 = 1.000.000.

        resultado = TributarioStrategy().liquidar(
            obligaciones=[sancion], abonos=[], fecha_corte=date(2023, 5, 10)
        )

        saldo = resultado.final_balance()
        # Las sanciones caen en el bucket 'indexation', nunca 'principal' -- estructuralmente
        # nunca acumulan interes por si solas (ver nota del siguiente test). El efecto
        # verificable de la correccion es que la indexacion queda por encima del monto
        # nominal de la sancion (1.000.000), por el 867-1 adicional.
        assert saldo.interest == Decimal("0.00")
        assert saldo.indexation > Decimal("1000000.00")

    def test_sancion_con_mora_de_3_anios_o_menos_no_agrega_indexacion(self):
        # Nota: las sanciones caen en el bucket 'indexation' (no 'principal'), asi que
        # nunca acumulan interes por si solas (LiquidationCore._accrue_time_passage solo
        # acumula interes sobre 'principal', salvo Suma Unica -- comportamiento estructural
        # del motor, no algo que este sprint cambie). El unico efecto verificable de la
        # correccion del Art. 867-1 sobre una sancion es si se agrega o no el evento de
        # indexacion adicional.
        sancion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD",
            base_sancion_tributaria=Decimal("10000000.00"),
            meses_extemporaneidad=2,
            fecha_origen=date(2020, 5, 10),
        )
        # Sancion efectiva: 5% x 2 meses = 10% de 10.000.000 = 1.000.000.

        resultado = TributarioStrategy().liquidar(
            obligaciones=[sancion],
            abonos=[],
            fecha_corte=date(2023, 5, 10),  # exactamente 3 anios
        )

        saldo = resultado.final_balance()
        assert saldo.interest == Decimal("0.00")
        assert saldo.indexation == Decimal("1000000.00")  # sin el 867-1 adicional

    def test_dos_obligaciones_renta_liquida_en_el_mismo_expediente_lanza_value_error(self):
        renta_1 = _obligacion_tributaria(
            categoria="RENTA_LIQUIDA",
            ingresos_brutos=Decimal("1.00"),
            devoluciones_rebajas_descuentos=Decimal("0.00"),
            costos=Decimal("0.00"),
            deducciones=Decimal("0.00"),
            rentas_exentas=Decimal("0.00"),
        )
        renta_2 = _obligacion_tributaria(
            categoria="RENTA_LIQUIDA",
            ingresos_brutos=Decimal("2.00"),
            devoluciones_rebajas_descuentos=Decimal("0.00"),
            costos=Decimal("0.00"),
            deducciones=Decimal("0.00"),
            rentas_exentas=Decimal("0.00"),
        )

        with pytest.raises(ValueError):
            TributarioStrategy().liquidar(
                obligaciones=[renta_1, renta_2], abonos=[], fecha_corte=date(2024, 3, 1)
            )

    def test_soporta_indexacion_ipc_es_true(self):
        # Sprint 43: TributarioStrategy ahora SI soporta IPC -- ligada al Art.
        # 867-1 E.T. (automatica por el trigger de mora, sin checkbox propio).
        assert TributarioStrategy().soporta_indexacion_ipc is True


def test_civil_familia_suma_unica_activa_interes_es_mayor_que_legado():
    obligacion_legado = Obligacion(
        id=6,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2024, 7, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=False,
    )
    obligacion_suma_unica = Obligacion(
        id=7,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2024, 7, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=True,
    )

    resultado_legado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_legado], abonos=[], fecha_corte=date(2025, 12, 31)
    )
    resultado_suma_unica = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_suma_unica], abonos=[], fecha_corte=date(2025, 12, 31)
    )

    # Mismo capital, misma indexacion (61933.78 desde el Sprint 80 -- IPC mensual,
    # ver test_civil_familia_puntual_con_indexacion_...), misma tasa y periodo --
    # la unica diferencia es la base del interes. El interes del legado
    # (87488.20) no cambio con el Sprint 80 porque se calcula solo sobre el
    # capital original, independiente del monto de indexacion; el de Suma
    # Unica si cambio (94283.40 -> 92907.92) porque se calcula sobre
    # principal+indexation.
    assert resultado_legado.final_balance().indexation == Decimal("61933.78")
    assert resultado_suma_unica.final_balance().indexation == Decimal("61933.78")
    assert resultado_legado.final_balance().interest == Decimal("87488.20")
    assert resultado_suma_unica.final_balance().interest == Decimal("92907.92")
    assert (
        resultado_suma_unica.final_balance().interest > resultado_legado.final_balance().interest
    )


def test_civil_familia_suma_unica_mezclada_liquida_cada_obligacion_con_su_criterio():
    # Desde el Sprint 21, cada obligacion corre en su propio LiquidationCore
    # (PendingDebt independiente, ver _liquidar_por_obligacion), asi que ya no
    # hay un unico saldo compartido a nivel de expediente -- mezclar criterios
    # de Suma Unica entre obligaciones del mismo expediente ya no es un error
    # de captura (a diferencia de la version original de este test, escrita
    # antes del Sprint 21): cada obligacion simplemente liquida con su propio
    # criterio, y _fusionar_resultados suma los saldos individuales.
    obligacion_a = Obligacion(
        id=8,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente A",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2024, 7, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=True,
    )
    obligacion_b = Obligacion(
        id=9,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente B",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2024, 7, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=False,
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=date(2025, 12, 31)
    )

    # Verificado contra el motor real (Sprint 80: IPC mensual para
    # CivilFamiliaStrategy): obligacion_a sola (Suma Unica) da
    # indexation=61933.78/interest=92907.92; obligacion_b sola (legado) da
    # indexation=30966.89/interest=43746.84. El resultado fusionado del
    # expediente es la suma exacta de ambos saldos independientes.
    fb = resultado.final_balance()
    assert fb.principal == Decimal("1500000.00")
    assert fb.indexation == Decimal("92900.67")
    assert fb.interest == Decimal("136654.76")


def test_civil_familia_suma_unica_ignora_obligaciones_sin_indexacion_activa():
    obligacion_indexada = Obligacion(
        id=10,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2024, 7, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=True,
    )
    obligacion_sin_indexar = Obligacion(
        id=11,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Otro concepto",
        categoria="DANOS_MORALES",
        fecha_origen=date(2024, 7, 1),
        valor=Decimal("200000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=False,
        interes_sobre_capital_indexado=False,
    )

    # La obligacion sin indexacion activa no aporta indexation al saldo fusionado,
    # sin importar su propio valor de interes_sobre_capital_indexado (Suma Unica
    # solo tiene efecto cuando aplica_indexacion_ipc tambien es True).
    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_indexada, obligacion_sin_indexar],
        abonos=[],
        fecha_corte=date(2025, 12, 31),
    )
    # Sprint 80: 61933.78 (IPC mensual), ver test_civil_familia_puntual_con_indexacion_...
    assert resultado.final_balance().indexation == Decimal("61933.78")


def test_pdf_pagina_69_ejemplo_credito_indexado_50_millones_2010_a_2025():
    # PDF pag. 69, "Actualizacion por IPC": capital $50.000.000 firmado el 1/1/2010,
    # liquidado el 1/1/2025. El PDF usa indices ilustrativos (140 -> 200, Va=$71.428.571)
    # solo como ejemplo pedagogico; este test usa la serie IPC real del motor
    # (historical_index.py, transcrita de las paginas 55-62 del mismo PDF) para las
    # mismas fechas y el mismo capital, por lo que el resultado numerico es distinto
    # del ilustrativo de la pag. 69 -- ver docstring del test y spec de este sprint.
    obligacion = Obligacion(
        id=12,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Credito indexado",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2010, 1, 1),
        valor=Decimal("50000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=True,
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 1, 1)
    )

    fb = resultado.final_balance()
    # Va (capital ya indexado) = principal + indexation, calculado con la serie IPC
    # real: Va = 50.000.000 x (IPC(2025-01-01) / IPC(2010-01-01)).
    # Sprint 80: ambas fechas (2010-01-01 y 2025-01-01) caen dentro del rango
    # cubierto por el indice IPC mensual real (2003-01 a 2026-03), asi que
    # CivilFamiliaStrategy ya usa get_ipc_interpolado_mensual_for_date en vez de
    # la anual -- indexation/interest recalculados con el motor real (valores
    # previos, formula anual: indexation=51762113.73, interest=89015614.51).
    assert fb.principal == Decimal("50000000.00")
    assert fb.indexation == Decimal("51749792.77")
    va = fb.principal + fb.indexation
    assert va == Decimal("101749792.77")
    # Paso 2 (Suma Unica): interes civil 6% EA aplicado sobre Va, no sobre el capital
    # historico -- verificado independientemente replicando la acumulacion diaria del
    # motor (DailyInterest + EffectiveRateConverter) con capital=Va constante durante
    # todo el periodo (la indexacion se causa el mismo dia que el capital).
    assert fb.interest == Decimal("89004820.88")

    # Contraste: con el algoritmo legado (interes solo sobre el capital historico),
    # el mismo caso da un interes bastante menor -- confirma que Suma Unica
    # efectivamente cambia el resultado, no solo que el motor no truena.
    obligacion_legado = Obligacion(
        id=13,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Credito indexado",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2010, 1, 1),
        valor=Decimal("50000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=False,
    )
    resultado_legado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_legado], abonos=[], fecha_corte=date(2025, 1, 1)
    )
    assert resultado_legado.final_balance().interest == Decimal("43737103.72")
    assert fb.interest > resultado_legado.final_balance().interest


def test_civil_familia_suma_unica_con_abonos_no_reproduce_el_patron_x9():
    """Sprint 102 -- verificacion (no motor nuevo): Pendientes.md documenta el
    patron de X9.INDEXACION-CON-ABONOS.md como "indexar -> restar abono ->
    reindexar el residuo hasta el siguiente abono -> restar..." y pide
    confirmar si el motor ya lo reproduce via Suma Unica
    (interes_sobre_capital_indexado) + AllocationEngine (Sprint 75). Este test
    prueba que NO lo reproduce: `_evento_indexacion_ipc`
    (app/services/area_strategy.py) emite un UNICO evento INDEXATION, fechado
    en `fecha_causacion`, cuyo monto ya es el delta COMPLETO hasta el
    `fecha_corte` GLOBAL de la liquidacion -- no hasta la fecha del siguiente
    abono. AllocationEngine.allocate() (indexacion -> interes -> capital)
    consume de ese bucket ya inflado, pero nunca vuelve a llamar
    IPCIndexation.calculate() en la fecha de cada abono. El resultado es un
    numero de negocio distinto (no un error de redondeo) al que produce
    reindexar paso a paso como exige X9.

    Escenario sintetico (capital $1.000.000, fecha_origen=2024-07-01,
    2 abonos, fecha_corte=2025-12-31; tasa=0.0001% para que el interes
    civil redondee a $0.00 y el caso aisle unicamente el mecanismo de
    indexacion+abonos):

    Calculo manual paso a paso siguiendo la mecanica de X9, usando
    `get_ipc_interpolado_mensual_for_date` -- desde el Sprint 80 esta es la
    misma funcion que usa realmente el motor para fechas dentro del rango
    2003-01 a 2026-03 (interpolacion mensual real DANE, no la interpolacion
    anual que se usaba antes de ese sprint):
      1. Indexar 1.000.000,00 de 2024-07-01 a 2025-01-01 (primer abono):
         +10.701,74 -> 1.010.701,74. Restar abono ($400.000,00) -> 610.701,74.
      2. Reindexar 610.701,74 de 2025-01-01 a 2025-06-01 (segundo abono):
         +22.002,97 -> 632.704,71. Restar abono ($300.000,00) -> 332.704,71.
      3. Reindexar 332.704,71 de 2025-06-01 a 2025-12-31 (corte): +4.708,02
         -> saldo final X9 = 337.412,73.

    El motor (via CivilFamiliaStrategy, Suma Unica activa) da un resultado
    distinto: indexa de una sola vez 1.000.000,00 desde 2024-07-01 hasta
    2025-12-31 (+61.933,78, con la misma interpolacion mensual), disponible
    integramente desde el primer dia. El primer abono ($400.000,00) consume
    parte de esos 61.933,78 de indexacion y el resto contra capital; el
    segundo abono ($300.000,00) va integro a capital. Saldo final del motor
    = 1.000.000,00 + 61.933,78 - 400.000,00 - 300.000,00 = 361.933,78.

    Brecha real: 361.933,78 (motor) vs. 337.412,73 (X9) = $24.521,05 de
    diferencia -- no es ruido de redondeo, es un algoritmo distinto (single
    evento de indexacion vs. reindexacion progresiva en cada abono). Gap
    documentado como Sprint 104 en Pendientes.md y pregunta nueva en
    Preguntas-Para-Abogado-Abiertas.md; no se corrige aqui (rediseñar el
    mecanismo de indexacion para reindexar en cada abono es un cambio de
    motor que requiere decision del despacho sobre la mecanica exacta a
    replicar, no una correccion mecanica). Los montos de este test se
    recalcularon el 2026-08-20 al fusionar el Sprint 80 (indexacion mensual
    real conectada en Civil/Familia), que cambio el resultado numerico del
    motor -- la brecha conceptual frente a X9 sigue existiendo igual,
    aunque el monto exacto cambio."""
    fecha_origen = date(2024, 7, 1)
    fecha_abono_1 = date(2025, 1, 1)
    fecha_abono_2 = date(2025, 6, 1)
    fecha_corte = date(2025, 12, 31)
    capital = Decimal("1000000.00")

    # -- Calculo manual X9: indexar -> restar -> reindexar -> restar -> reindexar --
    # Sprint 80 (2026-08-20): usa la misma funcion mensual que ahora usa el motor real.
    idx_origen = get_ipc_interpolado_mensual_for_date(fecha_origen)
    idx_abono_1 = get_ipc_interpolado_mensual_for_date(fecha_abono_1)
    idx_abono_2 = get_ipc_interpolado_mensual_for_date(fecha_abono_2)
    idx_corte = get_ipc_interpolado_mensual_for_date(fecha_corte)

    indexacion_1 = IPCIndexation.calculate(capital, idx_origen, idx_abono_1)
    assert indexacion_1 == Decimal("10701.74")
    saldo_tras_abono_1 = capital + indexacion_1 - Decimal("400000.00")
    assert saldo_tras_abono_1 == Decimal("610701.74")

    indexacion_2 = IPCIndexation.calculate(saldo_tras_abono_1, idx_abono_1, idx_abono_2)
    assert indexacion_2 == Decimal("22002.97")
    saldo_tras_abono_2 = saldo_tras_abono_1 + indexacion_2 - Decimal("300000.00")
    assert saldo_tras_abono_2 == Decimal("332704.71")

    indexacion_3 = IPCIndexation.calculate(saldo_tras_abono_2, idx_abono_2, idx_corte)
    assert indexacion_3 == Decimal("4708.02")
    saldo_final_x9 = saldo_tras_abono_2 + indexacion_3
    assert saldo_final_x9 == Decimal("337412.73")

    # -- Motor real (CivilFamiliaStrategy, Suma Unica + 2 abonos) --
    obligacion = Obligacion(
        id=500,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Prueba Sprint 102 (X9)",
        categoria="DANO_EMERGENTE",
        fecha_origen=fecha_origen,
        valor=capital,
        tasa_efectiva_anual=Decimal("0.0001"),
        aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=True,
    )
    abonos = [
        Abono(
            id=1,
            obligacion_id=500,
            fecha=fecha_abono_1,
            monto=Decimal("400000.00"),
            referencia="a1",
        ),
        Abono(
            id=2,
            obligacion_id=500,
            fecha=fecha_abono_2,
            monto=Decimal("300000.00"),
            referencia="a2",
        ),
    ]

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=abonos, fecha_corte=fecha_corte
    )

    saldo_final_motor = resultado.final_balance().total()
    assert saldo_final_motor == Decimal("361933.78")
    assert saldo_final_motor != saldo_final_x9
    assert saldo_final_motor - saldo_final_x9 == Decimal("24521.05")


# --- Sprint 42: wiring del motor de prescripcion/caducidad -----------------
#
# Centralizado en UniversalLiquidationService.liquidar() (ver
# app/services/motor_universal.py), NO repetido en cada AreaStrategy -- estos
# tests confirman que las 6 areas heredan el wiring automaticamente (via
# liquidar()/_liquidar_por_obligacion, que siempre pasa por
# UniversalLiquidationService) y que la marca es puramente informativa: el
# saldo final liquidado es identico este configurado o no el plazo legal de
# PRESCRIPCION_EJECUTIVA_MESES en Parametros.


def _sembrar_prescripcion_ejecutiva(meses=60):
    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave="PRESCRIPCION_EJECUTIVA_MESES",
            valor=_Decimal(meses),
            vigente_desde=date(1900, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=_dt.now(),
        )
    )
    session.commit()
    session.close()


def test_civil_familia_marca_obligacion_prescrita_sin_cambiar_el_total():
    obligacion = _obligacion_puntual()
    obligacion.fecha_origen = date(2015, 1, 1)
    fecha_corte = date(2026, 1, 1)  # 11 años despues -> prescrita bajo EJECUTIVA (5 años)

    referencia = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
    )
    assert all(not item.prescrita for item in referencia.items)

    _sembrar_prescripcion_ejecutiva()
    marcado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
    )

    assert any(item.prescrita for item in marcado.items)
    assert marcado.final_balance() == referencia.final_balance()


def test_comercial_marca_obligacion_prescrita_sin_cambiar_el_total():
    obligacion = _obligacion_comercial(
        fecha_origen=date(2015, 1, 1), fecha_vencimiento=date(2015, 2, 1)
    )
    fecha_corte = date(2026, 1, 1)

    referencia = ComercialStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
    )
    assert all(not item.prescrita for item in referencia.items)

    _sembrar_prescripcion_ejecutiva()
    marcado = ComercialStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
    )

    assert any(item.prescrita for item in marcado.items)
    assert marcado.final_balance() == referencia.final_balance()


def test_sancionatorio_marca_obligacion_prescrita_sin_cambiar_el_total():
    obligacion = _obligacion_sancionatoria(fecha_origen=date(2015, 6, 1))
    fecha_corte = date(2026, 6, 1)

    referencia = SancionatorioStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
    )
    assert all(not item.prescrita for item in referencia.items)

    _sembrar_prescripcion_ejecutiva()
    marcado = SancionatorioStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
    )

    assert any(item.prescrita for item in marcado.items)
    assert marcado.final_balance() == referencia.final_balance()


def test_honorarios_marca_obligacion_prescrita_sin_cambiar_el_total():
    obligacion = _obligacion_honorarios(fecha_origen=date(2015, 1, 1))
    fecha_corte = date(2026, 1, 1)

    referencia = HonorariosStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
    )
    assert all(not item.prescrita for item in referencia.items)

    _sembrar_prescripcion_ejecutiva()
    marcado = HonorariosStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
    )

    assert any(item.prescrita for item in marcado.items)
    assert marcado.final_balance() == referencia.final_balance()


def test_laboral_marca_obligacion_prescrita_sin_cambiar_el_total():
    obligacion = _obligacion_laboral(fecha_inicio=date(2010, 1, 1), fecha_fin=date(2010, 12, 31))
    fecha_corte = date(2026, 1, 1)

    referencia = LaboralStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
    )
    assert all(not item.prescrita for item in referencia.items)

    _sembrar_prescripcion_ejecutiva()
    marcado = LaboralStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
    )

    assert any(item.prescrita for item in marcado.items)
    assert marcado.final_balance() == referencia.final_balance()


def test_tributario_marca_obligacion_prescrita_sin_cambiar_el_total():
    obligacion = _obligacion_tributaria(
        categoria="IMPUESTO_A_CARGO", valor=Decimal("10000000.00"), fecha_origen=date(2015, 1, 1)
    )
    fecha_corte = date(2026, 1, 1)

    referencia = TributarioStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
    )
    assert all(not item.prescrita for item in referencia.items)

    _sembrar_prescripcion_ejecutiva()
    marcado = TributarioStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
    )

    assert any(item.prescrita for item in marcado.items)
    assert marcado.final_balance() == referencia.final_balance()


