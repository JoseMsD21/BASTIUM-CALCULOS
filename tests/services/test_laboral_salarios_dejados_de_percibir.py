"""Sprint 93: integracion de la categoria SALARIOS_DEJADOS_DE_PERCIBIR con
LaboralStrategy.liquidar() -- valida que la validacion se relaja SOLO para
esta categoria (LIQUIDACION_CONTRATO_LABORAL sigue rechazando RECURRENTE), y
que el "GRAN TOTAL" que produce el motor de liquidacion consolidado
(final_balance().principal, incluida la resta de un abono) coincide con el
mismo caso sintetico ya verificado a mano en
tests/services/test_salarios_dejados_de_percibir.py (multiplicador 14,62 por
bloque de año calendario completo, ver el docstring de ese archivo)."""

from datetime import date, datetime
from decimal import Decimal

import pytest

import database.session as session_module
from app.services.area_strategy import LaboralStrategy
from database.models import (
    Abono,
    Obligacion,
    ParametroLegal,
    TipoContratoLaboral,
    TipoObligacion,
    TipoReajusteAnual,
)

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
    # Sprint 93 (respuesta del despacho, 22/08/2026): la eleccion del indice
    # ya no es discrecional -- _validar_obligacion_laboral consulta el SMLMV
    # del año de causacion para decidir si corresponde IPC o SMMLV, asi que
    # todo obligacion SALARIOS_DEJADOS_DE_PERCIBIR necesita este parametro
    # sembrado para el año de `fecha_inicio`, sin importar el indice elegido.
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


def _obligacion_salarios_dejados_de_percibir(
    *,
    salario=Decimal("1200000.00"),
    fecha_inicio=date(2022, 1, 1),
    fecha_fin=date(2024, 12, 31),
    tipo_reajuste_anual=TipoReajusteAnual.IPC,
    tipo=TipoObligacion.RECURRENTE,
    categoria="SALARIOS_DEJADOS_DE_PERCIBIR",
    despido_injustificado=False,
    incluir_seguridad_social=False,
) -> Obligacion:
    return Obligacion(
        id=1,
        expediente_id=1,
        tipo=tipo,
        concepto="Salarios y prestaciones dejadas de percibir (reintegro)",
        categoria=categoria,
        fecha_origen=fecha_inicio,
        valor=salario,
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        tipo_reajuste_anual=tipo_reajuste_anual,
        despido_injustificado=despido_injustificado,
        tipo_contrato_laboral=TipoContratoLaboral.INDEFINIDO,
        incluir_seguridad_social=incluir_seguridad_social,
    )


class TestSalariosDejadosDePercibirLaboralStrategy:
    def test_gran_total_via_liquidar_coincide_con_el_caso_sintetico_verificado_a_mano(self):
        # Mismo caso sintetico IPC de
        # test_salarios_dejados_de_percibir.py::test_l5_ipc_tres_anios_completos...
        # (3 años calendario completos, IPC +10%/+10%): GRAN TOTAL = 58.070.640,00.
        _sembrar_ipc(
            {2022: Decimal("100.00"), 2023: Decimal("110.00"), 2024: Decimal("121.00")}
        )
        # SMLMV(2022) != 1.200.000,00 (el salario base) -- confirma que IPC
        # sigue siendo el indice correcto bajo la regla del despacho.
        _sembrar_smlmv({2022: Decimal("1000000.00")})
        obligacion = _obligacion_salarios_dejados_de_percibir()

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 12, 31)
        )

        assert resultado.final_balance().principal == Decimal("58070640.00")

    def test_un_abono_reduce_el_gran_total(self):
        _sembrar_ipc(
            {2022: Decimal("100.00"), 2023: Decimal("110.00"), 2024: Decimal("121.00")}
        )
        _sembrar_smlmv({2022: Decimal("1000000.00")})
        obligacion = _obligacion_salarios_dejados_de_percibir()
        abono = Abono(
            id=1,
            obligacion_id=1,
            fecha=date(2025, 1, 5),
            monto=Decimal("1000000.00"),
            referencia="Pago parcial reintegro",
        )

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2025, 6, 1)
        )

        assert resultado.total_payments_applied() == Decimal("1000000.00")
        assert resultado.final_balance().principal == Decimal("58070640.00") - Decimal(
            "1000000.00"
        )

    def test_smmlv_tambien_liquida_correcto_via_liquidar(self):
        # Salario base == SMLMV(2023) exactamente -- unico caso en que la
        # regla del despacho (Sprint 93) exige el indice SMMLV. 3 años
        # completos, SMLMV +10%/+10%:
        # salario_2023 = 1.000.000,00 (base, == SMLMV del año de causacion)
        # salario_2024 = 1.000.000,00 * 1.10 = 1.100.000,00
        # salario_2025 = 1.100.000,00 * 1.10 = 1.210.000,00
        # GRAN TOTAL = 14,62 * (1.000.000 + 1.100.000 + 1.210.000)
        #            = 14,62 * 3.310.000,00 = 48.392.200,00
        _sembrar_smlmv(
            {
                2023: Decimal("1000000.00"),
                2024: Decimal("1100000.00"),
                2025: Decimal("1210000.00"),
            }
        )

        obligacion = _obligacion_salarios_dejados_de_percibir(
            salario=Decimal("1000000.00"),
            fecha_inicio=date(2023, 1, 1),
            fecha_fin=date(2025, 12, 31),
            tipo_reajuste_anual=TipoReajusteAnual.SMMLV,
        )

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 31)
        )

        assert resultado.final_balance().principal == Decimal("48392200.00")

    def test_categoria_salarios_dejados_de_percibir_rechaza_puntual(self):
        obligacion = _obligacion_salarios_dejados_de_percibir(tipo=TipoObligacion.PUNTUAL)

        with pytest.raises(ValueError, match="RECURRENTE"):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 12, 31)
            )

    def test_categoria_liquidacion_contrato_laboral_sigue_rechazando_recurrente(self):
        # Regresion: el Sprint 93 NO abre RECURRENTE al resto del area, solo a
        # la categoria SALARIOS_DEJADOS_DE_PERCIBIR.
        obligacion = _obligacion_salarios_dejados_de_percibir(
            categoria="LIQUIDACION_CONTRATO_LABORAL"
        )

        with pytest.raises(ValueError, match="PUNTUAL"):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 12, 31)
            )

    def test_rechaza_despido_injustificado_marcado(self):
        obligacion = _obligacion_salarios_dejados_de_percibir(despido_injustificado=True)

        with pytest.raises(ValueError, match="despido"):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 12, 31)
            )

    def test_rechaza_incluir_seguridad_social_marcado(self):
        obligacion = _obligacion_salarios_dejados_de_percibir(incluir_seguridad_social=True)

        with pytest.raises(ValueError, match="seguridad social"):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 12, 31)
            )

    def test_rechaza_smmlv_cuando_el_salario_no_coincide_con_el_smlmv_del_anio(self):
        # Sprint 93 (respuesta del despacho, 22/08/2026): la eleccion del
        # indice no es discrecional. Salario 1.200.000,00 != SMLMV(2022)
        # 1.000.000,00 -> corresponde IPC, no SMMLV.
        _sembrar_smlmv({2022: Decimal("1000000.00")})
        obligacion = _obligacion_salarios_dejados_de_percibir(
            tipo_reajuste_anual=TipoReajusteAnual.SMMLV
        )

        with pytest.raises(ValueError, match="no es discrecional"):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 12, 31)
            )

    def test_rechaza_ipc_cuando_el_salario_coincide_con_el_smlmv_del_anio(self):
        # Caso inverso: salario == SMLMV(2023) exactamente -> corresponde
        # SMMLV, no IPC.
        _sembrar_smlmv({2023: Decimal("1160000.00")})
        obligacion = _obligacion_salarios_dejados_de_percibir(
            salario=Decimal("1160000.00"),
            fecha_inicio=date(2023, 1, 1),
            fecha_fin=date(2024, 12, 31),
            tipo_reajuste_anual=TipoReajusteAnual.IPC,
        )

        with pytest.raises(ValueError, match="no es discrecional"):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 12, 31)
            )
