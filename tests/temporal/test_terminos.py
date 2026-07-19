from datetime import date

from app.engine.temporal.terminos import (
    EstadoTermino,
    iniciar_termino,
    dias_restantes,
    esta_vencido,
    interrumpir,
    suspender,
)


def test_iniciar_termino_construye_estado_base():
    estado = iniciar_termino(date(2025, 12, 22), 10)
    assert estado == EstadoTermino(
        dias_totales=10,
        dias_consumidos=0,
        checkpoint=date(2025, 12, 22),
        suspendido=False,
    )


def test_iniciar_termino_rechaza_dias_totales_menor_a_uno():
    import pytest

    with pytest.raises(ValueError):
        iniciar_termino(date(2025, 12, 22), 0)


def test_dias_restantes_sin_modificadores():
    # Mismo escenario verificado en Task 3: 10 días hábiles desde
    # 2025-12-22 caen exactamente en 2026-01-07.
    estado = iniciar_termino(date(2025, 12, 22), 10)
    assert dias_restantes(estado, date(2026, 1, 6)) == 1
    assert dias_restantes(estado, date(2026, 1, 7)) == 0


def test_esta_vencido_sin_modificadores():
    estado = iniciar_termino(date(2025, 12, 22), 10)
    assert esta_vencido(estado, date(2026, 1, 6)) is False
    assert esta_vencido(estado, date(2026, 1, 7)) is True


def test_interrumpir_resetea_el_conteo():
    estado = iniciar_termino(date(2025, 12, 22), 10)
    # Avanza 3 días hábiles (verificado en Task 3: Dec23, Dec24, Dec26).
    fecha_interrupcion = date(2025, 12, 26)

    nuevo_estado = interrumpir(estado, fecha_interrupcion)

    assert nuevo_estado == EstadoTermino(
        dias_totales=10,
        dias_consumidos=0,
        checkpoint=fecha_interrupcion,
        suspendido=False,
    )
    # El estado original no se muta.
    assert estado.checkpoint == date(2025, 12, 22)


def test_interrumpir_reinicia_el_plazo_completo():
    estado = iniciar_termino(date(2025, 12, 22), 10)
    nuevo_estado = interrumpir(estado, date(2025, 12, 26))

    assert dias_restantes(nuevo_estado, date(2025, 12, 26)) == 10


def test_suspender_congela_los_dias_consumidos():
    estado = iniciar_termino(date(2025, 12, 22), 10)
    # 3 días hábiles corridos hasta el 2025-12-26 (Dec23, Dec24, Dec26).
    suspendido = suspender(estado, date(2025, 12, 26))

    assert suspendido.suspendido is True
    assert suspendido.dias_consumidos == 3
    assert suspendido.checkpoint == date(2025, 12, 26)


def test_suspender_congela_dias_restantes_pase_el_tiempo_que_pase():
    estado = iniciar_termino(date(2025, 12, 22), 10)
    suspendido = suspender(estado, date(2025, 12, 26))

    # Aunque pasen muchos días hábiles más, mientras esté suspendido no cambia.
    assert dias_restantes(suspendido, date(2026, 3, 1)) == 7
    assert dias_restantes(suspendido, date(2026, 6, 1)) == 7


def test_suspender_rechaza_termino_ya_suspendido():
    import pytest

    estado = iniciar_termino(date(2025, 12, 22), 10)
    suspendido = suspender(estado, date(2025, 12, 26))

    with pytest.raises(ValueError):
        suspender(suspendido, date(2026, 1, 5))
