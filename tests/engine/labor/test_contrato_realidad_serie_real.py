"""Sprint 94: convencion de indexacion del contrato realidad contra la serie
IPC real sembrada por la migracion (sin fixture de indices inventados).

La plantilla L7 trae IPC(2025) = 144,88 e IPC(2026) = 152,27: su cociente
(1,0510) es la variacion del IPC de 2025 (5,10 %), es decir, el "IPC" del
año Y es el cierre del año Y-1. Con la serie del software (cierres
encadenados), un valor de 2025 indexado a 2026 debe crecer exactamente 5,10 %.
"""

from decimal import Decimal

from app.engine.labor.contrato_realidad import (
    AnioContratoRealidadPrivado,
    liquidar_contrato_realidad_privado,
)
from scripts.migrate_parametros_legales import migrar


def test_factor_2025_a_2026_es_la_variacion_ipc_2025():
    migrar()
    liq = liquidar_contrato_realidad_privado(
        [AnioContratoRealidadPrivado(2025, Decimal("1200000"), Decimal("12"))], anio_final=2026
    )
    fila = liq.filas[0]
    assert fila.factor_ipc == Decimal("1.051")
    # Cesantias 1.200.000 x 1,051 = 1.261.200.
    assert fila.cesantias_indexadas == Decimal("1261200.00")
    # Salud 100 % (12,5 %) sobre 14.400.000 x 1,051 = 15.134.400 -> 1.891.800.
    assert fila.aporte_salud == Decimal("1891800.00")
    # Pension 100 % (16 %) -> 2.421.504.
    assert fila.aporte_pension == Decimal("2421504.00")
