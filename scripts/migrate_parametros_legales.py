"""Migracion de datos (no de esquema): siembra la tabla parametros_legales
(creada automaticamente por init_db(), ver database/database.py) con los
valores hoy hardcodeados en distintos motores, para que el sprint de
parametros legales versionados no cambie ningun resultado de calculo el dia
que se despliegue.

La mayoria de los valores se leen directamente de las constantes Python
existentes -- nunca retranscritos a mano -- porque esas constantes NO se
borran al re-cablear los motores que las usan (ver design spec, seccion
"Motores a re-cablear"): siguen siendo la transcripcion congelada y
verificada contra el PDF fuente, y esta migracion es la unica lectora que las
necesita despues del re-cableado. Esto sigue siendo cierto para
TOPE_MULTIPLICADOR (usury_validator), PUNTOS_DESCUENTO_ET_635
(moratory_interest), LegalRates.CIVIL_ANNUAL_RATE (legal_rates),
PLAZOS_PRESCRIPCION_MESES/PLAZOS_CADUCIDAD_MESES_CONOCIDOS (prescripcion) y
las 4 series historicas de historical_index.py (SMLMV, IPC, IBC/usura, UVT).

Excepcion: CUOTA_LITIS_INDIVIDUAL_PCT y HONORARIOS_TOTAL_PCT SI se
retranscriben a mano como Decimal("30")/Decimal("50") -- a diferencia de los
demas, esas dos constantes (antes HonorariosStrategy.TOPE_*) fueron borradas
de la clase al re-cablear HonorariosStrategy (Tarea 8 del sprint de
parametros legales versionados), asi que ya no hay una fuente viva de la que
leerlas. Los valores hardcodeados aqui son su ultimo valor conocido al
momento de esta migracion, no una lectura en vivo.

Igual pasa con EXTEMPORANEIDAD_PCT_MENSUAL, INEXACTITUD_PCT,
INEXACTITUD_AGRAVADA_PCT y ERROR_ARITMETICO_PCT (sanciones tributarias,
Sprint 15): se retranscriben a mano como Decimal("5")/Decimal("160")/
Decimal("200")/Decimal("30"). Su caso es distinto al de las dos anteriores
-- no hubo una constante Python que luego se borrara -- sino que
app/engine/tax/sanciones.py se escribio desde el inicio leyendolas solo via
get_parametro(), sin ningun Decimal a nivel de modulo que las acompañara.
El resultado practico es el mismo: no hay una fuente viva de la que leerlas
aqui, asi que se transcriben a mano su valor conocido al momento de esta
migracion.

Idempotente: si una clave ya tiene filas, no la vuelve a sembrar (mismo patron
que scripts/migrate_aplica_indexacion_ipc.py, Sprint 8)."""

import sys
from pathlib import Path

# Garantiza resolucion de 'database.*' y 'app.*' al invocar este archivo
# directamente (python scripts/migrate_parametros_legales.py) desde la raiz
# del proyecto, sin depender de que el caller use 'python -m'. Mismo patron
# que exports/scripts/generar_liquidacion_demo.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date, datetime
from decimal import Decimal

from database.database import init_db
from database.models import ParametroLegal
from database.session import get_session

from app.engine.indexation.historical_index import (
    _IPC_INDICE_ACUMULADO,
    _SMLMV_POR_ANIO,
    _TRAMOS_IBC_USURA,
    _UVT_POR_ANIO,
)
from app.engine.interest.legal_rates import LegalRates
from app.engine.interest.usury_validator import TOPE_MULTIPLICADOR
from app.engine.tax.moratory_interest import PUNTOS_DESCUENTO_ET_635
from app.engine.temporal.prescripcion import (
    PLAZOS_CADUCIDAD_MESES_CONOCIDOS,
    PLAZOS_PRESCRIPCION_MESES,
    TipoAccion,
)

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
            # Hardcodeados (no leidos en vivo): HonorariosStrategy.TOPE_CUOTA_LITIS_INDIVIDUAL_PCT/
            # TOPE_HONORARIOS_TOTAL_PCT fueron borrados de la clase al re-cablear
            # HonorariosStrategy (Tarea 8) -- ver docstring del modulo.
            ("CUOTA_LITIS_INDIVIDUAL_PCT", Decimal("30"), date(2007, 1, 1)),
            ("HONORARIOS_TOTAL_PCT", Decimal("50"), ANCLA_SIN_FECHA_NORMA),
            ("ET635_PUNTOS_DESCUENTO", PUNTOS_DESCUENTO_ET_635, ANCLA_SIN_FECHA_NORMA),
            ("CIVIL_ANNUAL_RATE", LegalRates.CIVIL_ANNUAL_RATE, ANCLA_SIN_FECHA_NORMA),
            # Hardcodeados (nunca hubo fuente viva): app/engine/tax/sanciones.py
            # (Sprint 15) lee estas 4 claves solo via get_parametro(), sin ningun
            # Decimal a nivel de modulo que las acompañe -- ver docstring del modulo.
            ("EXTEMPORANEIDAD_PCT_MENSUAL", Decimal("5"), ANCLA_SIN_FECHA_NORMA),
            ("INEXACTITUD_PCT", Decimal("160"), ANCLA_SIN_FECHA_NORMA),
            ("INEXACTITUD_AGRAVADA_PCT", Decimal("200"), ANCLA_SIN_FECHA_NORMA),
            ("ERROR_ARITMETICO_PCT", Decimal("30"), ANCLA_SIN_FECHA_NORMA),
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

        if not _clave_ya_sembrada(session, "UVT"):
            for anio, valor in _UVT_POR_ANIO.items():
                session.add(_fila("UVT", valor, date(anio, 1, 1)))
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
