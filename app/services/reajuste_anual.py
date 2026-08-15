"""Sprint 41: genera y persiste las cuotas mensuales reales de una obligacion
RECURRENTE de Civil/Familia con reajuste anual activo (tipo_reajuste_anual
SMMLV/IPC). Cada cuota se guarda como una `Obligacion` PUNTUAL hija
(obligacion_padre_id apuntando a la obligacion RECURRENTE original), con
capital constante dentro de cada año calendario y reajustado el 1 de enero de
cada año siguiente al de origen, segun el indice elegido.

Ver la seccion "Architecture" del plan
(docs/superpowers/plans/2026-08-07-sprint41-familia-cuotas-reajuste-anual.md)
para el razonamiento completo -- en particular, punto 4: por que dejar que
estas cuotas, ya persistidas como Obligacion reales, corran por el motor de
liquidacion consolidado existente (via CivilFamiliaStrategy.liquidar(), Task 4)
produce el interes de mora correcto por cuota sin necesitar un motor de interes
"autonomo por cuota" nuevo.
"""

from datetime import date
from decimal import Decimal

import database.session as session_module
from app.engine.indexation.historical_index import get_ipc_for_date, get_smlmv_for_year
from app.engine.indexation.ipc import IPCIndexation
from app.engine.math.rounding import Rounding
from app.engine.time.calendar import CalendarUtils
from database.models import Obligacion, TipoObligacion, TipoReajusteAnual

_MESES_ES = {
    1: "ENERO",
    2: "FEBRERO",
    3: "MARZO",
    4: "ABRIL",
    5: "MAYO",
    6: "JUNIO",
    7: "JULIO",
    8: "AGOSTO",
    9: "SEPTIEMBRE",
    10: "OCTUBRE",
    11: "NOVIEMBRE",
    12: "DICIEMBRE",
}


def _pct_reajuste_smmlv(anio: int) -> Decimal:
    """(SMLMV(anio) - SMLMV(anio-1)) / SMLMV(anio-1) * 100 -- formula tal como
    la trajo el usuario en su reporte original (ver encabezado del plan del
    Sprint 41: pendiente de confirmacion formal del despacho, se implementa
    igual mientras tanto). Reutiliza get_smlmv_for_year (historical_index.py),
    ya usado por SancionatorioStrategy -- no reimplementa la resolucion del
    SMLMV por año."""
    smlmv_actual = get_smlmv_for_year(anio)
    smlmv_anterior = get_smlmv_for_year(anio - 1)
    return (smlmv_actual - smlmv_anterior) / smlmv_anterior * Decimal("100")


def reajustar_capital_anual(capital: Decimal, anio: int, tipo: TipoReajusteAnual) -> Decimal:
    """Capital reajustado al 1 de enero de `anio`, segun el indice elegido.
    SMMLV: aplica la formula del encabezado del plan
    (cuota_nueva = cuota_anterior + cuota_anterior * pct / 100) con el
    porcentaje de _pct_reajuste_smmlv, redondeado a centavos solo al final
    (mismo criterio que IPCIndexation/historical_index: alta precision
    interna, redondeo unicamente en el resultado). IPC: reutiliza
    IPCIndexation.calculate() tal cual (app/engine/indexation/ipc.py, el mismo
    motor que ya usa CivilFamiliaStrategy para indexacion) en vez de
    reimplementar el calculo de variacion anual -- calculate() ya retorna el
    delta de indexacion redondeado a centavos (o 0.00 si hay deflacion, mismo
    criterio jurisprudencial que el resto de la app).

    Publica (sin guion bajo) desde el Sprint 73: reutilizada tal cual por
    app/services/recurrencia_fechas_fijas.py::generar_cuotas_fechas_fijas para
    el reajuste anual OPCIONAL de una obligacion de fechas anuales fijas (a
    diferencia de generar_cuotas_mensuales, que exige tipo_reajuste_anual
    activo, generar_cuotas_fechas_fijas lo aplica solo si esta configurado)."""
    if tipo == TipoReajusteAnual.SMMLV:
        pct = _pct_reajuste_smmlv(anio)
        return Rounding.money(capital + capital * pct / Decimal("100"))
    if tipo == TipoReajusteAnual.IPC:
        delta = IPCIndexation.calculate(
            capital=capital,
            initial_index=get_ipc_for_date(date(anio - 1, 12, 31)),
            final_index=get_ipc_for_date(date(anio, 12, 31)),
        )
        return capital + delta
    raise ValueError(f"tipo_reajuste_anual '{tipo}' no soporta reajuste automatico de cuotas.")


def generar_cuotas_mensuales(
    obligacion_recurrente: Obligacion, fecha_corte: date
) -> list[Obligacion]:
    """Genera y persiste una Obligacion PUNTUAL por cada mes entre
    `obligacion_recurrente.fecha_origen` (que para una obligacion RECURRENTE
    equivale a su fecha_inicio, ver ObligacionFormDialog.guardar()) y la fecha
    de corte (topada por `fecha_fin` si esta seteada). Idempotente: si esta
    obligacion ya tiene cuotas hijas persistidas (obligacion_padre_id
    apuntando a ella), las retorna tal cual en vez de generar duplicados --
    alcance excluido de este sprint es retro-generar/regenerar cuotas para una
    obligacion que cambio de fecha_corte despues de generarlas una vez.

    Abre y cierra su propia sesion de SQLAlchemy (igual que
    app/services/parametro_service.py): `obligacion_recurrente` puede venir de
    una sesion ya cerrada (ej. la GUI, que cierra su sesion antes de invocar
    servicios de fondo) -- todos los campos que se necesitan se leen a Python
    ANTES de abrir la sesion propia, para no depender de un lazy-load tardio
    sobre un objeto potencialmente detached.
    """
    if obligacion_recurrente.tipo != TipoObligacion.RECURRENTE:
        raise ValueError("Solo una obligacion RECURRENTE puede generar cuotas mensuales.")
    if obligacion_recurrente.tipo_reajuste_anual == TipoReajusteAnual.NINGUNO:
        raise ValueError(
            "La obligacion no tiene un tipo_reajuste_anual activo (SMMLV/IPC) -- "
            "generar_cuotas_mensuales no aplica a obligaciones sin reajuste."
        )
    if not obligacion_recurrente.dia_pago:
        raise ValueError("La obligacion RECURRENTE debe tener un dia_pago para generar cuotas.")

    obligacion_padre_id = obligacion_recurrente.id
    expediente_id = obligacion_recurrente.expediente_id
    concepto_base = obligacion_recurrente.concepto
    categoria = obligacion_recurrente.categoria
    tasa_efectiva_anual = obligacion_recurrente.tasa_efectiva_anual
    aplica_indexacion_ipc = obligacion_recurrente.aplica_indexacion_ipc
    interes_sobre_capital_indexado = obligacion_recurrente.interes_sobre_capital_indexado
    dia_pago = obligacion_recurrente.dia_pago
    fecha_inicio = obligacion_recurrente.fecha_origen
    fecha_fin = obligacion_recurrente.fecha_fin
    tipo_reajuste = obligacion_recurrente.tipo_reajuste_anual
    capital_inicial = obligacion_recurrente.valor

    session = session_module.get_session()
    try:
        cuotas_existentes = (
            session.query(Obligacion)
            .filter(Obligacion.obligacion_padre_id == obligacion_padre_id)
            .order_by(Obligacion.fecha_origen)
            .all()
        )
        if cuotas_existentes:
            return cuotas_existentes

        fin = min(fecha_fin, fecha_corte) if fecha_fin is not None else fecha_corte

        cuotas_nuevas: list[Obligacion] = []
        capital_actual = capital_inicial
        anio_capital = fecha_inicio.year
        anio_cursor = fecha_inicio.year
        mes_cursor = fecha_inicio.month
        while True:
            cuota_fecha = CalendarUtils.safe_create_date(anio_cursor, mes_cursor, dia_pago)
            if cuota_fecha > fin:
                break

            # Reajuste anual: se dispara la primera vez que el cursor mensual entra a
            # un año distinto del ultimo año ya reajustado -- iterando mes a mes esto
            # ocurre exactamente una vez por transicion de año (nunca se saltan años),
            # siempre en enero.
            if anio_cursor != anio_capital:
                capital_actual = reajustar_capital_anual(
                    capital_actual, anio_cursor, tipo_reajuste
                )
                anio_capital = anio_cursor

            concepto = f"{concepto_base} DE {_MESES_ES[mes_cursor]} {anio_cursor}"
            cuota = Obligacion(
                expediente_id=expediente_id,
                tipo=TipoObligacion.PUNTUAL,
                concepto=concepto,
                categoria=categoria,
                fecha_origen=cuota_fecha,
                valor=capital_actual,
                tasa_efectiva_anual=tasa_efectiva_anual,
                aplica_indexacion_ipc=aplica_indexacion_ipc,
                interes_sobre_capital_indexado=interes_sobre_capital_indexado,
                obligacion_padre_id=obligacion_padre_id,
            )
            session.add(cuota)
            cuotas_nuevas.append(cuota)

            mes_cursor += 1
            if mes_cursor > 12:
                mes_cursor = 1
                anio_cursor += 1

        session.commit()
        return cuotas_nuevas
    finally:
        session.close()
