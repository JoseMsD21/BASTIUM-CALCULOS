from datetime import date

from app.engine.temporal.terminos import (
    EstadoTermino,
    iniciar_termino,
    dias_restantes,
    esta_vencido,
    interrumpir,
    suspender,
    reanudar,
)

# Fechas elegidas deliberadamente fuera de la vacancia judicial de fin de año
# (20 dic - 11 ene) y de la Semana Santa extendida (Sprint 6, Pendientes.md) --
# esas exclusiones de calendario ya se prueban directamente en
# tests/temporal/test_calendar.py; aquí solo se ejercita la máquina de estados
# (interrupción/suspensión/reanudación), que es agnóstica a qué fechas exactas
# cuentan como hábiles.


def test_iniciar_termino_construye_estado_base():
    estado = iniciar_termino(date(2026, 2, 2), 10)
    assert estado == EstadoTermino(
        dias_totales=10,
        dias_consumidos=0,
        checkpoint=date(2026, 2, 2),
        suspendido=False,
    )


def test_iniciar_termino_rechaza_dias_totales_menor_a_uno():
    import pytest

    with pytest.raises(ValueError):
        iniciar_termino(date(2026, 2, 2), 0)


def test_dias_restantes_sin_modificadores():
    # Verificado independientemente con CalendarUtils: 9 días hábiles desde
    # 2026-02-02 (lunes) caen en 2026-02-13; el décimo, en 2026-02-16.
    estado = iniciar_termino(date(2026, 2, 2), 10)
    assert dias_restantes(estado, date(2026, 2, 13)) == 1
    assert dias_restantes(estado, date(2026, 2, 16)) == 0


def test_esta_vencido_sin_modificadores():
    estado = iniciar_termino(date(2026, 2, 2), 10)
    assert esta_vencido(estado, date(2026, 2, 13)) is False
    assert esta_vencido(estado, date(2026, 2, 16)) is True


def test_interrumpir_resetea_el_conteo():
    estado = iniciar_termino(date(2026, 2, 2), 10)
    # Avanza 4 días hábiles (verificado: 2026-02-03/04/05/06).
    fecha_interrupcion = date(2026, 2, 6)

    nuevo_estado = interrumpir(estado, fecha_interrupcion)

    assert nuevo_estado == EstadoTermino(
        dias_totales=10,
        dias_consumidos=0,
        checkpoint=fecha_interrupcion,
        suspendido=False,
    )
    # El estado original no se muta.
    assert estado.checkpoint == date(2026, 2, 2)


def test_interrumpir_reinicia_el_plazo_completo():
    estado = iniciar_termino(date(2026, 2, 2), 10)
    nuevo_estado = interrumpir(estado, date(2026, 2, 6))

    assert dias_restantes(nuevo_estado, date(2026, 2, 6)) == 10


def test_suspender_congela_los_dias_consumidos():
    estado = iniciar_termino(date(2026, 2, 2), 10)
    # 4 días hábiles corridos hasta el 2026-02-06 (03, 04, 05, 06).
    suspendido = suspender(estado, date(2026, 2, 6))

    assert suspendido.suspendido is True
    assert suspendido.dias_consumidos == 4
    assert suspendido.checkpoint == date(2026, 2, 6)


def test_suspender_congela_dias_restantes_pase_el_tiempo_que_pase():
    estado = iniciar_termino(date(2026, 2, 2), 10)
    suspendido = suspender(estado, date(2026, 2, 6))

    # Aunque pasen muchos días hábiles más, mientras esté suspendido no cambia.
    assert dias_restantes(suspendido, date(2026, 6, 1)) == 6
    assert dias_restantes(suspendido, date(2026, 9, 1)) == 6


def test_suspender_rechaza_termino_ya_suspendido():
    import pytest

    estado = iniciar_termino(date(2026, 2, 2), 10)
    suspendido = suspender(estado, date(2026, 2, 6))

    with pytest.raises(ValueError):
        suspender(suspendido, date(2026, 2, 11))


def test_reanudar_retoma_el_conteo_sin_perder_lo_congelado():
    estado = iniciar_termino(date(2026, 2, 2), 10)
    suspendido = suspender(estado, date(2026, 2, 6))  # 4 días congelados
    reanudado = reanudar(suspendido, date(2026, 2, 11))

    assert reanudado.suspendido is False
    assert reanudado.dias_consumidos == 4  # lo congelado no se toca
    assert reanudado.checkpoint == date(2026, 2, 11)

    # Desde el 2026-02-11 (miércoles), 2 días hábiles más son 2026-02-12 y 2026-02-13.
    assert dias_restantes(reanudado, date(2026, 2, 13)) == 10 - (4 + 2)


def test_reanudar_rechaza_termino_no_suspendido():
    import pytest

    estado = iniciar_termino(date(2026, 2, 2), 10)

    with pytest.raises(ValueError):
        reanudar(estado, date(2026, 2, 11))


def test_ciclo_completo_suspender_reanudar_hasta_vencer():
    # Verificado independientemente: reanudado con checkpoint 2026-02-11 y
    # 4 días ya congelados (de 10 totales) necesita 6 días hábiles más para
    # vencer. 6 días hábiles después de 2026-02-11 caen en 2026-02-19;
    # 5 días hábiles después caen en 2026-02-18 (un día antes de vencer).
    estado = iniciar_termino(date(2026, 2, 2), 10)
    suspendido = suspender(estado, date(2026, 2, 6))  # 4 congelados
    reanudado = reanudar(suspendido, date(2026, 2, 11))

    assert esta_vencido(reanudado, date(2026, 2, 18)) is False
    assert dias_restantes(reanudado, date(2026, 2, 18)) == 1
    assert esta_vencido(reanudado, date(2026, 2, 19)) is True


def test_dias_restantes_rechaza_fecha_anterior_al_checkpoint():
    import pytest

    estado = iniciar_termino(date(2026, 2, 2), 10)

    with pytest.raises(ValueError):
        dias_restantes(estado, date(2026, 1, 30))


def test_interrumpir_rechaza_fecha_anterior_al_checkpoint():
    import pytest

    estado = iniciar_termino(date(2026, 2, 2), 10)

    with pytest.raises(ValueError):
        interrumpir(estado, date(2026, 1, 30))


def test_reanudar_rechaza_fecha_anterior_al_checkpoint_de_suspension():
    import pytest

    estado = iniciar_termino(date(2026, 2, 2), 10)
    suspendido = suspender(estado, date(2026, 2, 6))

    with pytest.raises(ValueError):
        reanudar(suspendido, date(2026, 2, 4))
