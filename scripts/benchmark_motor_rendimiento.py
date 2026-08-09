"""Benchmark manual (Sprint 25, Definicion de Hecho): mide el tiempo de una
liquidacion con muchos anios de mora, para comparar antes/despues de los
hallazgos 1 y 3 del audit de rendimiento (scan lineal de MemoryRateProvider,
reconsulta de get_parametro por cuota). No es una prueba automatizada -- se
corre a mano con `python scripts/benchmark_motor_rendimiento.py` antes y
despues de aplicar los cambios de este sprint, y los dos numeros impresos se
registran en Pendientes.md al cerrar el sprint (ver Task 6 del plan)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.services.area_strategy import CivilFamiliaStrategy
from database.models import Base, Obligacion, ParametroLegal, TipoObligacion


def _preparar_db_en_memoria() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_module.SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_module.get_session()
    for anio in range(1997, 2027):
        session.add(
            ParametroLegal(
                clave="IPC_INDICE_ACUMULADO",
                valor=Decimal("100") * Decimal("1.05") ** (anio - 1997),
                vigente_desde=date(anio, 1, 1),
                vigente_hasta=None,
                usuario="benchmark",
                motivo=None,
                creado_en=datetime.now(),
            )
        )
    session.commit()
    session.close()


def _benchmark_mora_larga() -> float:
    """Hallazgo 1: MemoryRateProvider.get_rate escaneado dia a dia durante 29
    anios de mora (1997-01-01 a 2026-12-31, ~10950 llamadas)."""
    obligacion = Obligacion(
        id=1,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Benchmark mora larga",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(1997, 1, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    inicio = time.perf_counter()
    CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 12, 31)
    )
    return time.perf_counter() - inicio


def _benchmark_recurrente_con_indexacion() -> float:
    """Hallazgos 2/3: get_ipc_interpolado_for_date consultado una vez por
    cuota mensual (348 cuotas = 29 anios x 12 meses)."""
    obligacion = Obligacion(
        id=2,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Benchmark cuotas con indexacion",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(1997, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(1997, 1, 1),
        fecha_fin=date(2025, 12, 5),
        aplica_indexacion_ipc=True,
    )
    inicio = time.perf_counter()
    CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 5)
    )
    return time.perf_counter() - inicio


if __name__ == "__main__":
    _preparar_db_en_memoria()
    tiempo_mora = _benchmark_mora_larga()
    tiempo_recurrente = _benchmark_recurrente_con_indexacion()
    print(f"Mora larga (29 anios, ~10950 dias): {tiempo_mora:.3f}s")
    print(f"Recurrente con indexacion (348 cuotas): {tiempo_recurrente:.3f}s")
