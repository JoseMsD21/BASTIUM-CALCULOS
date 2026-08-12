from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

import database.session as session_module
from app.core.exceptions import ParametroNoDisponibleError
from database.models import ParametroLegal


def _insertar(clave, valor, vigente_desde, vigente_hasta=None):
    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave=clave,
            valor=Decimal(valor),
            vigente_desde=vigente_desde,
            vigente_hasta=vigente_hasta,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    session.commit()
    session.close()


def _insertar_con_creado_en(clave, valor, vigente_desde, creado_en, vigente_hasta=None):
    """Como `_insertar`, pero con `creado_en` explicito -- necesario para
    reproducir un empate de `vigente_desde` desempatado por `creado_en`
    (test_resolver_fila_y_resolver_entre_filas_dan_el_mismo_resultado), algo
    que `_insertar` no puede garantizar de forma determinista con
    `datetime.now()`."""
    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave=clave,
            valor=Decimal(valor),
            vigente_desde=vigente_desde,
            vigente_hasta=vigente_hasta,
            usuario="test",
            motivo=None,
            creado_en=creado_en,
        )
    )
    session.commit()
    session.close()


def test_get_parametro_modo_abierto_toma_la_fila_mas_reciente_antes_de_la_fecha():
    from app.services.parametro_service import get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))
    _insertar("USURA_MULTIPLICADOR", "2.0", date(2030, 1, 1))

    assert get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20)) == Decimal("1.5")
    assert get_parametro("USURA_MULTIPLICADOR", date(2031, 1, 1)) == Decimal("2.0")


def test_get_parametro_modo_abierto_extrapola_hacia_adelante_sin_tope():
    from app.services.parametro_service import get_parametro

    _insertar("HONORARIOS_TOTAL_PCT", "50", date(2007, 1, 1))
    assert get_parametro("HONORARIOS_TOTAL_PCT", date(2099, 1, 1)) == Decimal("50")


def test_get_parametro_sin_ninguna_fila_anterior_a_la_fecha_lanza_error():
    from app.services.parametro_service import get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))
    with pytest.raises(ParametroNoDisponibleError):
        get_parametro("USURA_MULTIPLICADOR", date(1990, 1, 1))


def test_get_parametro_clave_desconocida_lanza_value_error():
    from app.services.parametro_service import get_parametro

    with pytest.raises(ValueError):
        get_parametro("NO_EXISTE", date(2026, 1, 1))


def test_get_parametro_modo_anual_exacto_requiere_el_mismo_anio():
    from app.services.parametro_service import get_parametro

    _insertar("SMLMV", "1750905.00", date(2026, 1, 1))
    _insertar("SMLMV", "1423500.00", date(2025, 1, 1))

    assert get_parametro("SMLMV", date(2026, 7, 20)) == Decimal("1750905.00")
    assert get_parametro("SMLMV", date(2025, 12, 31)) == Decimal("1423500.00")


def test_get_parametro_modo_anual_exacto_no_extrapola():
    from app.services.parametro_service import get_parametro

    _insertar("SMLMV", "1750905.00", date(2026, 1, 1))
    with pytest.raises(ParametroNoDisponibleError):
        get_parametro("SMLMV", date(2027, 1, 1))


def test_get_parametro_modo_tramo_cerrado_encuentra_el_tramo_correcto():
    from app.services.parametro_service import get_parametro

    _insertar("IBC_CONSUMO_ORDINARIO", "16.24", date(2026, 1, 1), vigente_hasta=date(2026, 1, 31))
    _insertar("IBC_CONSUMO_ORDINARIO", "16.82", date(2026, 2, 1), vigente_hasta=date(2026, 2, 28))

    assert get_parametro("IBC_CONSUMO_ORDINARIO", date(2026, 1, 15)) == Decimal("16.24")
    assert get_parametro("IBC_CONSUMO_ORDINARIO", date(2026, 2, 15)) == Decimal("16.82")


def test_get_parametro_modo_tramo_cerrado_no_extrapola_mas_alla_del_ultimo_tramo():
    from app.services.parametro_service import get_parametro

    _insertar("IBC_CONSUMO_ORDINARIO", "16.24", date(2026, 1, 1), vigente_hasta=date(2026, 1, 31))
    with pytest.raises(ParametroNoDisponibleError):
        get_parametro("IBC_CONSUMO_ORDINARIO", date(2026, 2, 1))


def test_agregar_valor_modo_abierto_no_admite_vigente_hasta():
    from app.services.parametro_service import agregar_valor

    with pytest.raises(ValueError):
        agregar_valor(
            "USURA_MULTIPLICADOR",
            Decimal("1.5"),
            date(2026, 1, 1),
            "abogado1",
            vigente_hasta=date(2026, 12, 31),
        )


def test_agregar_valor_modo_tramo_cerrado_exige_vigente_hasta():
    from app.services.parametro_service import agregar_valor

    with pytest.raises(ValueError):
        agregar_valor("IBC_CONSUMO_ORDINARIO", Decimal("16.24"), date(2026, 8, 1), "abogado1")


def test_agregar_valor_guarda_y_queda_disponible_para_get_parametro():
    from app.services.parametro_service import agregar_valor, get_parametro

    agregar_valor(
        "SMLMV",
        Decimal("1900000.00"),
        date(2027, 1, 1),
        "abogado1",
        motivo="Publicado por el Gobierno",
    )
    assert get_parametro("SMLMV", date(2027, 3, 1)) == Decimal("1900000.00")


def test_historial_ordena_del_mas_reciente_al_mas_antiguo():
    from app.services.parametro_service import agregar_valor, historial

    agregar_valor("SMLMV", Decimal("1423500.00"), date(2025, 1, 1), "abogado1")
    agregar_valor("SMLMV", Decimal("1750905.00"), date(2026, 1, 1), "abogado1")

    filas = historial("SMLMV")
    assert [f.vigente_desde for f in filas] == [date(2026, 1, 1), date(2025, 1, 1)]


def test_valor_vigente_hoy_retorna_none_sin_datos():
    from app.services.parametro_service import valor_vigente_hoy

    assert valor_vigente_hoy("SMLMV") is None


def test_valor_vigente_hoy_retorna_la_fila_resuelta_para_hoy():
    from app.services.parametro_service import agregar_valor, valor_vigente_hoy

    agregar_valor("HONORARIOS_TOTAL_PCT", Decimal("50"), date(2007, 1, 1), "abogado1")
    fila = valor_vigente_hoy("HONORARIOS_TOTAL_PCT")
    assert fila is not None
    assert fila.valor == Decimal("50")


def test_ultimo_anio_disponible_retorna_el_mayor_anio_cargado():
    from app.services.parametro_service import agregar_valor, ultimo_anio_disponible

    agregar_valor("IPC_INDICE_ACUMULADO", Decimal("100"), date(1967, 1, 1), "sistema")
    agregar_valor("IPC_INDICE_ACUMULADO", Decimal("500"), date(2025, 1, 1), "sistema")
    assert ultimo_anio_disponible("IPC_INDICE_ACUMULADO") == 2025


def test_ultimo_anio_disponible_rechaza_claves_que_no_son_anuales():
    from app.services.parametro_service import ultimo_anio_disponible

    with pytest.raises(ValueError):
        ultimo_anio_disponible("USURA_MULTIPLICADOR")


def test_ultimo_anio_disponible_sin_datos_lanza_parametro_no_disponible():
    from app.services.parametro_service import ultimo_anio_disponible

    with pytest.raises(ParametroNoDisponibleError):
        ultimo_anio_disponible("SMLMV")


def test_agregar_valor_rechaza_valor_negativo():
    from app.services.parametro_service import agregar_valor

    with pytest.raises(ValueError):
        agregar_valor("USURA_MULTIPLICADOR", Decimal("-1.5"), date(2026, 1, 1), "abogado1")


def test_agregar_valor_rechaza_valor_cero():
    from app.services.parametro_service import agregar_valor

    with pytest.raises(ValueError):
        agregar_valor("USURA_MULTIPLICADOR", Decimal("0"), date(2026, 1, 1), "abogado1")


def test_agregar_valor_rechaza_vigente_hasta_anterior_a_vigente_desde():
    from app.services.parametro_service import agregar_valor

    with pytest.raises(ValueError):
        agregar_valor(
            "IBC_CONSUMO_ORDINARIO",
            Decimal("16.24"),
            date(2026, 2, 1),
            "abogado1",
            vigente_hasta=date(2026, 1, 1),
        )


def test_agregar_valor_rechaza_tramo_cerrado_solapado():
    from app.services.parametro_service import agregar_valor

    agregar_valor(
        "IBC_CONSUMO_ORDINARIO",
        Decimal("16.24"),
        date(2026, 1, 1),
        "abogado1",
        vigente_hasta=date(2026, 1, 31),
    )
    with pytest.raises(ValueError):
        agregar_valor(
            "IBC_CONSUMO_ORDINARIO",
            Decimal("16.50"),
            date(2026, 1, 15),
            "abogado1",
            vigente_hasta=date(2026, 2, 15),
        )


def test_agregar_valor_permite_tramo_cerrado_consecutivo_sin_solape():
    from app.services.parametro_service import agregar_valor

    agregar_valor(
        "IBC_CONSUMO_ORDINARIO",
        Decimal("16.24"),
        date(2026, 1, 1),
        "abogado1",
        vigente_hasta=date(2026, 1, 31),
    )
    fila = agregar_valor(
        "IBC_CONSUMO_ORDINARIO",
        Decimal("16.82"),
        date(2026, 2, 1),
        "abogado1",
        vigente_hasta=date(2026, 2, 28),
    )
    assert fila.valor == Decimal("16.82")


def test_cache_de_liquidacion_evita_reconsultar_la_misma_clave_y_fecha(monkeypatch):
    from app.services import parametro_service
    from app.services.parametro_service import cache_de_liquidacion, get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    with cache_de_liquidacion():
        primero = get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))
        segundo = get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))

    assert primero == segundo == Decimal("1.5")
    assert len(llamadas) == 1


def test_cache_de_liquidacion_no_persiste_entre_bloques(monkeypatch):
    from app.services import parametro_service
    from app.services.parametro_service import cache_de_liquidacion, get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    with cache_de_liquidacion():
        get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))
    with cache_de_liquidacion():
        get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))

    assert len(llamadas) == 2


def test_get_parametro_sin_cache_activa_sigue_consultando_cada_vez(monkeypatch):
    from app.services import parametro_service
    from app.services.parametro_service import get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))
    get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))

    assert len(llamadas) == 2


def test_cache_de_liquidacion_usada_como_decorador_crea_bloque_nuevo_por_llamada(monkeypatch):
    from app.services import parametro_service
    from app.services.parametro_service import cache_de_liquidacion, get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    @cache_de_liquidacion()
    def _dos_consultas_iguales():
        get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))
        get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20))

    _dos_consultas_iguales()
    _dos_consultas_iguales()

    assert len(llamadas) == 2  # 1 por invocacion de _dos_consultas_iguales, no 4


# --- Sprint 53: precargar_parametro (resuelve N fechas distintas sin N consultas) ---


def test_precargar_parametro_resuelve_fechas_distintas_sin_reconsultar(monkeypatch):
    """A diferencia de la cache por (clave, fecha) de cache_de_liquidacion (que
    solo evita repetir la MISMA fecha exacta), precargar_parametro debe cubrir
    N fechas DISTINTAS de la misma clave con una sola consulta -- el caso real
    del Dashboard (N obligaciones con N fechas_origen distintas)."""
    from app.services import parametro_service
    from app.services.parametro_service import (
        cache_de_liquidacion,
        get_parametro,
        precargar_parametro,
    )

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))
    _insertar("USURA_MULTIPLICADOR", "2.0", date(2030, 1, 1))

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    with cache_de_liquidacion():
        precargar_parametro("USURA_MULTIPLICADOR")
        valores = [
            get_parametro("USURA_MULTIPLICADOR", date(2026, 1, 1) + timedelta(days=indice))
            for indice in range(10)
        ]

    assert valores == [Decimal("1.5")] * 10
    assert len(llamadas) == 0  # ninguna consulta por fecha: todo resuelto en memoria


def test_precargar_parametro_respeta_el_valor_vigente_por_fecha():
    from app.services.parametro_service import (
        cache_de_liquidacion,
        get_parametro,
        precargar_parametro,
    )

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))
    _insertar("USURA_MULTIPLICADOR", "2.0", date(2030, 1, 1))

    with cache_de_liquidacion():
        precargar_parametro("USURA_MULTIPLICADOR")
        assert get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20)) == Decimal("1.5")
        assert get_parametro("USURA_MULTIPLICADOR", date(2031, 1, 1)) == Decimal("2.0")


def test_precargar_parametro_respeta_modo_anual_exacto():
    from app.services.parametro_service import (
        cache_de_liquidacion,
        get_parametro,
        precargar_parametro,
    )

    _insertar("SMLMV", "1750905.00", date(2026, 1, 1))
    _insertar("SMLMV", "1423500.00", date(2025, 1, 1))

    with cache_de_liquidacion():
        precargar_parametro("SMLMV")
        assert get_parametro("SMLMV", date(2026, 7, 20)) == Decimal("1750905.00")
        assert get_parametro("SMLMV", date(2025, 12, 31)) == Decimal("1423500.00")
        with pytest.raises(ParametroNoDisponibleError):
            get_parametro("SMLMV", date(2027, 1, 1))


def test_precargar_parametro_respeta_modo_tramo_cerrado():
    from app.services.parametro_service import (
        cache_de_liquidacion,
        get_parametro,
        precargar_parametro,
    )

    _insertar("IBC_CONSUMO_ORDINARIO", "16.24", date(2026, 1, 1), vigente_hasta=date(2026, 1, 31))
    _insertar("IBC_CONSUMO_ORDINARIO", "16.82", date(2026, 2, 1), vigente_hasta=date(2026, 2, 28))

    with cache_de_liquidacion():
        precargar_parametro("IBC_CONSUMO_ORDINARIO")
        assert get_parametro("IBC_CONSUMO_ORDINARIO", date(2026, 1, 15)) == Decimal("16.24")
        assert get_parametro("IBC_CONSUMO_ORDINARIO", date(2026, 2, 15)) == Decimal("16.82")
        with pytest.raises(ParametroNoDisponibleError):
            get_parametro("IBC_CONSUMO_ORDINARIO", date(2026, 3, 1))


def test_precargar_parametro_sin_cache_de_liquidacion_activa_no_hace_nada(monkeypatch):
    """Sin un bloque cache_de_liquidacion() activo no hay donde guardar la
    precarga -- precargar_parametro no debe fallar, simplemente no tiene
    efecto y get_parametro sigue consultando la base de datos por fecha."""
    from app.services import parametro_service
    from app.services.parametro_service import get_parametro, precargar_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))

    llamadas = []
    original = parametro_service._resolver_fila

    def _contando(clave, fecha):
        llamadas.append((clave, fecha))
        return original(clave, fecha)

    monkeypatch.setattr(parametro_service, "_resolver_fila", _contando)

    precargar_parametro("USURA_MULTIPLICADOR")  # no-op: ningun cache_de_liquidacion() activo
    assert get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20)) == Decimal("1.5")
    assert len(llamadas) == 1


def test_precargar_parametro_clave_desconocida_lanza_value_error():
    from app.services.parametro_service import cache_de_liquidacion, precargar_parametro

    with cache_de_liquidacion(), pytest.raises(ValueError):
        precargar_parametro("NO_EXISTE")


# --- Equivalencia _resolver_fila (SQL) vs _resolver_entre_filas (memoria) ---
#
# `_resolver_fila` y `_resolver_entre_filas` (app/services/parametro_service.py)
# implementan el mismo criterio de filtrado/orden por separado -- una golpea
# la base de datos, la otra resuelve en memoria sobre filas precargadas
# (precargar_parametro). Los tests de arriba verifican el camino de memoria
# contra valores esperados escritos a mano; este test en cambio compara
# ambas implementaciones directamente entre si sobre los mismos datos, para
# que un cambio futuro en una (ej. una condicion nueva en el modo ABIERTO)
# que no se replique en la otra falle aqui en vez de depender de que un
# reviewer humano lo note.
_CASOS_EQUIVALENCIA = [
    # ABIERTO (USURA_MULTIPLICADOR): dos filas con vigente_desde=1997-07-01
    # empatado (creado_en distinto, la 1.6 mas reciente debe ganar) y una
    # tercera en 2030-01-01.
    ("USURA_MULTIPLICADOR", date(2026, 7, 20)),  # entre el empate y la fila de 2030
    ("USURA_MULTIPLICADOR", date(1997, 7, 1)),  # exactamente en el borde del empate
    ("USURA_MULTIPLICADOR", date(1990, 1, 1)),  # antes de cualquier fila -> None
    ("USURA_MULTIPLICADOR", date(2050, 1, 1)),  # despues de la fila mas reciente
    # ANUAL_EXACTO (SMLMV): filas en 2025-01-01 y 2026-01-01.
    ("SMLMV", date(2025, 12, 31)),  # resuelve contra el año anterior
    ("SMLMV", date(2026, 1, 1)),  # borde exacto del año siguiente
    ("SMLMV", date(2027, 1, 1)),  # sin fila para ese año -> None
    # TRAMO_CERRADO (IBC_CONSUMO_ORDINARIO): tramos [ene, ene] y [feb, feb].
    ("IBC_CONSUMO_ORDINARIO", date(2026, 1, 1)),  # borde inicial del primer tramo
    ("IBC_CONSUMO_ORDINARIO", date(2026, 1, 31)),  # borde final del primer tramo
    ("IBC_CONSUMO_ORDINARIO", date(2026, 2, 1)),  # borde inicial del segundo tramo
    ("IBC_CONSUMO_ORDINARIO", date(2026, 3, 1)),  # fuera de cualquier tramo -> None
]


@pytest.mark.parametrize("clave, fecha", _CASOS_EQUIVALENCIA)
def test_resolver_fila_y_resolver_entre_filas_dan_el_mismo_resultado(clave, fecha):
    from app.services import parametro_service
    from app.services.parametro_service import CATALOGO_PARAMETROS, historial

    # ABIERTO, con un empate deliberado de vigente_desde desempatado por
    # creado_en -- el caso donde el orden importa y que ninguna otra prueba
    # de este archivo ejercitaba antes.
    _insertar_con_creado_en(
        "USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1), datetime(2020, 1, 1, 8, 0, 0)
    )
    _insertar_con_creado_en(
        "USURA_MULTIPLICADOR", "1.6", date(1997, 7, 1), datetime(2020, 1, 1, 9, 0, 0)
    )
    _insertar_con_creado_en(
        "USURA_MULTIPLICADOR", "2.0", date(2030, 1, 1), datetime(2020, 1, 1, 8, 0, 0)
    )

    # ANUAL_EXACTO
    _insertar("SMLMV", "1750905.00", date(2026, 1, 1))
    _insertar("SMLMV", "1423500.00", date(2025, 1, 1))

    # TRAMO_CERRADO
    _insertar("IBC_CONSUMO_ORDINARIO", "16.24", date(2026, 1, 1), vigente_hasta=date(2026, 1, 31))
    _insertar("IBC_CONSUMO_ORDINARIO", "16.82", date(2026, 2, 1), vigente_hasta=date(2026, 2, 28))

    info = CATALOGO_PARAMETROS[clave]
    filas_precargadas = historial(clave)

    fila_sql = parametro_service._resolver_fila(clave, fecha)
    fila_memoria = parametro_service._resolver_entre_filas(info, fecha, filas_precargadas)

    if fila_sql is None:
        assert fila_memoria is None
    else:
        assert fila_memoria is not None
        assert fila_memoria.valor == fila_sql.valor
        assert fila_memoria.vigente_desde == fila_sql.vigente_desde
        assert fila_memoria.creado_en == fila_sql.creado_en
