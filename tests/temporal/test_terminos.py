from datetime import date

from app.engine.temporal.terminos import (
    EstadoTermino,
    iniciar_termino,
    dias_restantes,
    esta_vencido,
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
