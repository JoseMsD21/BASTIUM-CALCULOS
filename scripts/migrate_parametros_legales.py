"""Migracion de datos (no de esquema): siembra la tabla parametros_legales
(creada automaticamente por init_db(), ver database/database.py) con los
valores hoy hardcodeados en distintos motores, para que el sprint de
parametros legales versionados no cambie ningun resultado de calculo el dia
que se despliegue.

Los valores se leen directamente de las constantes Python existentes -- nunca
retranscritos a mano -- porque esas constantes NO se borran al re-cablear los
motores que las usan (ver design spec, seccion "Motores a re-cablear"): siguen
siendo la transcripcion congelada y verificada contra el PDF fuente, y esta
migracion es la unica lectora que las necesita despues del re-cableado.

Idempotente: si una clave ya tiene filas, no la vuelve a sembrar (mismo patron
que scripts/migrate_aplica_indexacion_ipc.py, Sprint 8)."""

from datetime import date, datetime
from decimal import Decimal

from database.database import init_db
from database.models import ParametroLegal
from database.session import get_session

from app.engine.indexation.historical_index import (
    _IPC_INDICE_ACUMULADO,
    _SMLMV_POR_ANIO,
    _TRAMOS_IBC_USURA,
)
from app.engine.interest.legal_rates import LegalRates
from app.engine.interest.usury_validator import TOPE_MULTIPLICADOR
from app.engine.tax.moratory_interest import PUNTOS_DESCUENTO_ET_635
from app.engine.temporal.prescripcion import (
    PLAZOS_CADUCIDAD_MESES_CONOCIDOS,
    PLAZOS_PRESCRIPCION_MESES,
    TipoAccion,
)
from app.services.area_strategy import HonorariosStrategy

USUARIO_MIGRACION = "sistema"
MOTIVO_MIGRACION = (
    "Dato migrado automaticamente al implementar parametros legales versionados."
)
ANCLA_SIN_FECHA_NORMA = date(1900, 1, 1)

_CLAVE_POR_TIPO_ACCION = {
    TipoAccion.EJECUTIVA: "PRESCRIPCION_EJECUTIVA_MESES",
    TipoAccion.ORDINARIA: "PRESCRIPCION_ORDINARIA_MESES",
    TipoAccion.HONORARIOS_PROFESIONALES: "PRESCRIPCION_HONORARIOS_MESES",
    TipoAccion.CAMBIARIA_DIRECTA: "PRESCRIPCION_CAMBIARIA_DIRECTA_MESES",
    TipoAccion.CAMBIARIA_REGRESO_TENEDOR: "PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES",
    TipoAccion.CAMBIARIA_REGRESO_ENTRE_OBLIGADOS: "PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES",
}


def _fila(clave: str, valor: Decimal, vigente_desde: date, vigente_hasta: date | None = None) -> ParametroLegal:
    return ParametroLegal(
        clave=clave, valor=valor, vigente_desde=vigente_desde, vigente_hasta=vigente_hasta,
        usuario=USUARIO_MIGRACION, motivo=MOTIVO_MIGRACION, creado_en=datetime.now(),
    )


def _clave_ya_sembrada(session, clave: str) -> bool:
    return session.query(ParametroLegal).filter(ParametroLegal.clave == clave).first() is not None


def migrar() -> int:
    """Siembra parametros_legales. Retorna cuantas claves se sembraron (0 si
    ya estaban todas cargadas)."""
    init_db()
    session = get_session()
    sembradas = 0
    try:
        valores_unicos = [
            ("USURA_MULTIPLICADOR", TOPE_MULTIPLICADOR, ANCLA_SIN_FECHA_NORMA),
            ("CUOTA_LITIS_INDIVIDUAL_PCT", HonorariosStrategy.TOPE_CUOTA_LITIS_INDIVIDUAL_PCT, date(2007, 1, 1)),
            ("HONORARIOS_TOTAL_PCT", HonorariosStrategy.TOPE_HONORARIOS_TOTAL_PCT, ANCLA_SIN_FECHA_NORMA),
            ("ET635_PUNTOS_DESCUENTO", PUNTOS_DESCUENTO_ET_635, ANCLA_SIN_FECHA_NORMA),
            ("CIVIL_ANNUAL_RATE", LegalRates.CIVIL_ANNUAL_RATE, ANCLA_SIN_FECHA_NORMA),
        ]
        for clave, valor, vigente_desde in valores_unicos:
            if _clave_ya_sembrada(session, clave):
                continue
            session.add(_fila(clave, valor, vigente_desde))
            sembradas += 1

        for tipo_accion, clave in _CLAVE_POR_TIPO_ACCION.items():
            if _clave_ya_sembrada(session, clave):
                continue
            session.add(_fila(clave, Decimal(PLAZOS_PRESCRIPCION_MESES[tipo_accion]), ANCLA_SIN_FECHA_NORMA))
            sembradas += 1

        for tipo_proceso, meses in PLAZOS_CADUCIDAD_MESES_CONOCIDOS.items():
            clave = f"CADUCIDAD_{tipo_proceso}_MESES"
            if _clave_ya_sembrada(session, clave):
                continue
            session.add(_fila(clave, Decimal(meses), ANCLA_SIN_FECHA_NORMA))
            sembradas += 1

        if not _clave_ya_sembrada(session, "SMLMV"):
            for anio, valor in _SMLMV_POR_ANIO.items():
                session.add(_fila("SMLMV", valor, date(anio, 1, 1)))
            sembradas += 1

        if not _clave_ya_sembrada(session, "IPC_INDICE_ACUMULADO"):
            for anio, valor in _IPC_INDICE_ACUMULADO.items():
                session.add(_fila("IPC_INDICE_ACUMULADO", valor, date(anio, 1, 1)))
            sembradas += 1

        if not _clave_ya_sembrada(session, "IBC_CONSUMO_ORDINARIO"):
            for tramo in _TRAMOS_IBC_USURA:
                session.add(_fila("IBC_CONSUMO_ORDINARIO", tramo.ibc_anual, tramo.inicio, tramo.fin))
            sembradas += 1

        if not _clave_ya_sembrada(session, "USURA_CONSUMO_ORDINARIO"):
            for tramo in _TRAMOS_IBC_USURA:
                session.add(_fila("USURA_CONSUMO_ORDINARIO", tramo.usura_anual, tramo.inicio, tramo.fin))
            sembradas += 1

        session.commit()
        return sembradas
    finally:
        session.close()


if __name__ == "__main__":
    n = migrar()
    if n:
        print(f"Se sembraron {n} claves nuevas en parametros_legales.")
    else:
        print("parametros_legales ya estaba sembrada, no se hizo nada.")
