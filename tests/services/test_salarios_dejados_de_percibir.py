"""Sprint 93: salarios y prestaciones sociales dejadas de percibir, con
reajuste anual IPC (L5) o SMMLV (L6). Los archivos de referencia del despacho
NO estan disponibles en este entorno (docs/Pendientes.md, Sprint 93, nota de
la rutina autonoma) -- estos tests usan casos sinteticos con cifras redondas,
verificados a mano (con una calculadora Decimal auxiliar, NO llamando al
propio codigo bajo prueba) contra la formula legal descrita en el docstring
de app/services/salarios_dejados_de_percibir.py, no contra la planilla real.

Formula verificada a mano para un bloque de un año calendario COMPLETO (365/6
dias reales, pero 360 dias "comerciales" -- ver CalendarUtils.dias_comerciales_360):
con dias_bloque == 360, cada componente se reduce a un multiplo exacto y
verificable del salario del bloque (sin decimales periodicos que dependan del
redondeo):
  - SALARIO_DEJADO_DE_PERCIBIR = salario * dias/30      = salario * 12    (12 meses)
  - CESANTIAS                  = salario * dias/360     = salario * 1     (30 dias/año)
  - INTERESES_CESANTIAS        = CESANTIAS * dias*0.12/360 = salario * 0.12  (12% de un mes)
  - PRIMA_JUNIO + PRIMA_DICIEMBRE = 2 * salario*(dias/2)/360 = salario * 1.0 (15+15 dias)
  - VACACIONES                 = salario * dias/720     = salario * 0.5  (15 dias)
Multiplicador total del "GRAN TOTAL" por bloque de año completo:
  12 + 1 + 0.12 + 1.0 + 0.5 = 14.62
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

import database.session as session_module
from app.services.salarios_dejados_de_percibir import (
    determinar_tipo_reajuste_salarios_dejados_de_percibir,
    generar_eventos_salarios_dejados_de_percibir,
)
from database.models import ParametroLegal, TipoReajusteAnual

_MULTIPLICADOR_ANIO_COMPLETO = Decimal("14.62")


def _sembrar_ipc(valores: dict[int, Decimal]) -> None:
    session = session_module.get_session()
    for anio, valor in valores.items():
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


def _sembrar_smlmv(valores: dict[int, Decimal]) -> None:
    session = session_module.get_session()
    for anio, valor in valores.items():
        session.add(
            ParametroLegal(
                clave="SMLMV",
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


def _gran_total(eventos) -> Decimal:
    return sum((e.payload["amount"] for e in eventos), Decimal("0.00"))


def test_l5_ipc_tres_anios_completos_gran_total_verificado_a_mano():
    """Caso sintetico L5 (reajuste IPC): 3 años calendario COMPLETOS
    (2022/2023/2024), IPC sube 10% cada año (cifras redondas sinteticas, no la
    serie real -- ver docstring del modulo). Salario inicial 1'200.000,00.

    salario_2022 = 1.200.000,00 (año de origen, sin reajustar)
    salario_2023 = 1.200.000,00 * 1.10 = 1.320.000,00
    salario_2024 = 1.320.000,00 * 1.10 = 1.452.000,00

    GRAN TOTAL = 14,62 * (1.200.000 + 1.320.000 + 1.452.000)
               = 14,62 * 3.972.000,00 = 58.070.640,00
    """
    _sembrar_ipc(
        {
            2022: Decimal("100.00"),
            2023: Decimal("110.00"),
            2024: Decimal("121.00"),
        }
    )

    eventos = generar_eventos_salarios_dejados_de_percibir(
        salario_inicial=Decimal("1200000.00"),
        fecha_inicio=date(2022, 1, 1),
        fecha_fin=date(2024, 12, 31),
        tipo_reajuste=TipoReajusteAnual.IPC,
    )

    salarios_esperados = [Decimal("1200000.00"), Decimal("1320000.00"), Decimal("1452000.00")]
    gran_total_esperado = sum(
        (s * _MULTIPLICADOR_ANIO_COMPLETO for s in salarios_esperados), Decimal("0.00")
    )
    assert gran_total_esperado == Decimal("58070640.00")

    assert _gran_total(eventos) == gran_total_esperado

    # Verificacion linea por linea (no solo el total agregado): un evento
    # SALARIO_DEJADO_DE_PERCIBIR + 5 eventos de LaborScheduler por cada uno de
    # los 3 bloques anuales = 18 eventos.
    assert len(eventos) == 18
    tipos_por_fecha = {}
    for e in eventos:
        tipos_por_fecha.setdefault(e.date, {})[e.event_type] = e.payload["amount"]

    assert tipos_por_fecha[date(2022, 12, 31)]["SALARIO_DEJADO_DE_PERCIBIR"] == Decimal(
        "14400000.00"
    )
    assert tipos_por_fecha[date(2022, 12, 31)]["CESANTIAS"] == Decimal("1200000.00")
    assert tipos_por_fecha[date(2023, 12, 31)]["SALARIO_DEJADO_DE_PERCIBIR"] == Decimal(
        "15840000.00"
    )
    assert tipos_por_fecha[date(2024, 12, 31)]["SALARIO_DEJADO_DE_PERCIBIR"] == Decimal(
        "17424000.00"
    )
    assert tipos_por_fecha[date(2024, 12, 31)]["VACACIONES"] == Decimal("726000.00")


def test_l6_smmlv_tres_anios_completos_gran_total_verificado_a_mano():
    """Caso sintetico L6 (reajuste SMMLV): 3 años calendario COMPLETOS
    (2023/2024/2025), SMLMV sube 10% cada año (cifras redondas sinteticas).
    Salario inicial 2'000.000,00.

    salario_2023 = 2.000.000,00 (año de origen, sin reajustar)
    salario_2024 = 2.000.000,00 * 1.10 = 2.200.000,00
    salario_2025 = 2.200.000,00 * 1.10 = 2.420.000,00

    GRAN TOTAL = 14,62 * (2.000.000 + 2.200.000 + 2.420.000)
               = 14,62 * 6.620.000,00 = 96.784.400,00
    """
    _sembrar_smlmv(
        {
            2023: Decimal("1000000.00"),
            2024: Decimal("1100000.00"),
            2025: Decimal("1210000.00"),
        }
    )

    eventos = generar_eventos_salarios_dejados_de_percibir(
        salario_inicial=Decimal("2000000.00"),
        fecha_inicio=date(2023, 1, 1),
        fecha_fin=date(2025, 12, 31),
        tipo_reajuste=TipoReajusteAnual.SMMLV,
    )

    salarios_esperados = [Decimal("2000000.00"), Decimal("2200000.00"), Decimal("2420000.00")]
    gran_total_esperado = sum(
        (s * _MULTIPLICADOR_ANIO_COMPLETO for s in salarios_esperados), Decimal("0.00")
    )
    assert gran_total_esperado == Decimal("96784400.00")

    assert _gran_total(eventos) == gran_total_esperado
    assert len(eventos) == 18


def test_l5_ipc_bloques_parciales_desde_hasta_gran_total_verificado_a_mano():
    """Caso sintetico L5 con el primer y ultimo bloque PARCIALES (no años
    calendario completos) -- ejercita la columna "DESDE/HASTA por año" real de
    L5/L6 (un contrato que no empieza/termina exactamente el 1-ene/31-dic).

    Periodo: 2021-07-15 a 2023-03-20 (3 bloques: 2021 parcial, 2022 completo,
    2023 parcial). Salario inicial 1'000.000,00, IPC sube 10% cada año.

    Cada bloque se verifico a mano por separado con una calculadora Decimal
    auxiliar (ROUND_HALF_UP a centavos, igual criterio que Rounding.money) --
    ver el comentario junto a cada assert para la aritmetica exacta.
    """
    _sembrar_ipc(
        {
            2021: Decimal("100.00"),
            2022: Decimal("110.00"),
            2023: Decimal("121.00"),
        }
    )

    eventos = generar_eventos_salarios_dejados_de_percibir(
        salario_inicial=Decimal("1000000.00"),
        fecha_inicio=date(2021, 7, 15),
        fecha_fin=date(2023, 3, 20),
        tipo_reajuste=TipoReajusteAnual.IPC,
    )

    por_fecha = {}
    for e in eventos:
        por_fecha.setdefault(e.date, {})[e.event_type] = e.payload["amount"]

    # Bloque 1: 2021-07-15 a 2021-12-31, dias_comerciales_360 = 166 (dia_fin
    # 31 se topa a 30: (2021-2021)*360 + (12-7)*30 + (30-15) + 1 = 166),
    # salario sin reajustar (1.000.000,00).
    assert set(por_fecha[date(2021, 12, 31)]) == {
        "SALARIO_DEJADO_DE_PERCIBIR",
        "CESANTIAS",
        "INTERESES_CESANTIAS",
        "PRIMA_JUNIO",
        "PRIMA_DICIEMBRE",
        "VACACIONES",
    }
    bloque1 = por_fecha[date(2021, 12, 31)]
    # 1.000.000 * 166/30 = 5.533.333,3333... -> 5.533.333,33
    assert bloque1["SALARIO_DEJADO_DE_PERCIBIR"] == Decimal("5533333.33")
    # 1.000.000 * 166/360 = 461.111,1111... -> 461.111,11
    assert bloque1["CESANTIAS"] == Decimal("461111.11")
    # 461.111,11 * 166 * 0,12/360 = 25.514,8147... -> 25.514,81
    assert bloque1["INTERESES_CESANTIAS"] == Decimal("25514.81")
    # 1.000.000 * 83/360 = 230.555,5555... -> 230.555,56 (dias_semestre=83)
    assert bloque1["PRIMA_JUNIO"] == Decimal("230555.56")
    assert bloque1["PRIMA_DICIEMBRE"] == Decimal("230555.56")
    # 1.000.000 * 166/720 = 230.555,5555... -> 230.555,56
    assert bloque1["VACACIONES"] == Decimal("230555.56")
    total_bloque1 = sum(bloque1.values(), Decimal("0.00"))
    assert total_bloque1 == Decimal("6711625.93")

    # Bloque 2: 2022-01-01 a 2022-12-31 (año completo, dias=360), salario
    # reajustado +10% -> 1.100.000,00. Multiplicador de año completo (14,62).
    bloque2 = por_fecha[date(2022, 12, 31)]
    total_bloque2 = sum(bloque2.values(), Decimal("0.00"))
    assert total_bloque2 == Decimal("1100000.00") * _MULTIPLICADOR_ANIO_COMPLETO
    assert total_bloque2 == Decimal("16082000.00")

    # Bloque 3: 2023-01-01 a 2023-03-20, dias_comerciales_360 = 80
    # ((3-1)*30 + (20-1) + 1 = 80), salario reajustado +10% sobre 1.100.000
    # -> 1.210.000,00.
    bloque3 = por_fecha[date(2023, 3, 20)]
    # 1.210.000 * 80/30 = 3.226.666,6666... -> 3.226.666,67
    assert bloque3["SALARIO_DEJADO_DE_PERCIBIR"] == Decimal("3226666.67")
    # 1.210.000 * 80/360 = 268.888,8888... -> 268.888,89
    assert bloque3["CESANTIAS"] == Decimal("268888.89")
    total_bloque3 = sum(bloque3.values(), Decimal("0.00"))
    assert total_bloque3 == Decimal("3906059.25")

    gran_total_esperado = total_bloque1 + total_bloque2 + total_bloque3
    assert gran_total_esperado == Decimal("26699685.18")
    assert _gran_total(eventos) == gran_total_esperado


def test_no_reajuste_con_ninguno_mantiene_salario_constante():
    eventos = generar_eventos_salarios_dejados_de_percibir(
        salario_inicial=Decimal("1000000.00"),
        fecha_inicio=date(2023, 1, 1),
        fecha_fin=date(2024, 12, 31),
        tipo_reajuste=TipoReajusteAnual.NINGUNO,
    )
    por_fecha = {e.date: e.payload["amount"] for e in eventos if e.event_type == "CESANTIAS"}
    assert por_fecha[date(2023, 12, 31)] == Decimal("1000000.00")
    assert por_fecha[date(2024, 12, 31)] == Decimal("1000000.00")


def test_rechaza_fecha_fin_anterior_o_igual_a_fecha_inicio():
    with pytest.raises(ValueError, match="fecha_fin"):
        generar_eventos_salarios_dejados_de_percibir(
            salario_inicial=Decimal("1000000.00"),
            fecha_inicio=date(2023, 1, 1),
            fecha_fin=date(2023, 1, 1),
            tipo_reajuste=TipoReajusteAnual.NINGUNO,
        )


def test_rechaza_salario_cero_o_negativo():
    with pytest.raises(ValueError, match="salario"):
        generar_eventos_salarios_dejados_de_percibir(
            salario_inicial=Decimal("0.00"),
            fecha_inicio=date(2023, 1, 1),
            fecha_fin=date(2023, 12, 31),
            tipo_reajuste=TipoReajusteAnual.NINGUNO,
        )


class TestDeterminarTipoReajusteSalariosDejadosDePercibir:
    """Sprint 93 (respuesta del despacho, 22/08/2026): la eleccion del indice
    de reajuste no es discrecional -- se deriva del salario base y el SMLMV
    del año de causacion."""

    def test_salario_igual_al_smlmv_del_anio_usa_smmlv(self):
        _sembrar_smlmv({2023: Decimal("1160000.00")})
        resultado = determinar_tipo_reajuste_salarios_dejados_de_percibir(
            salario_base=Decimal("1160000.00"), anio_causacion=2023
        )
        assert resultado == TipoReajusteAnual.SMMLV

    def test_salario_distinto_al_smlmv_del_anio_usa_ipc(self):
        _sembrar_smlmv({2023: Decimal("1160000.00")})
        resultado = determinar_tipo_reajuste_salarios_dejados_de_percibir(
            salario_base=Decimal("3000000.00"), anio_causacion=2023
        )
        assert resultado == TipoReajusteAnual.IPC

    def test_salario_apenas_por_encima_del_smlmv_usa_ipc(self):
        _sembrar_smlmv({2023: Decimal("1160000.00")})
        resultado = determinar_tipo_reajuste_salarios_dejados_de_percibir(
            salario_base=Decimal("1160000.01"), anio_causacion=2023
        )
        assert resultado == TipoReajusteAnual.IPC
