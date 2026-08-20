"""Sprint 73: genera y persiste las cuotas reales de una obligacion RECURRENTE
de Civil/Familia con tipo_recurrencia FECHAS_ANUALES_FIJAS -- un patron de
recurrencia distinto del mensual del Sprint 41 (app/services/reajuste_anual.py),
reportado por el usuario para gastos que no se repiten mes a mes sino en
fechas puntuales de cada año (ej. gastos de vestuario en junio, diciembre, y
el cumpleaños del niño beneficiario).

Por que un modulo separado en vez de una rama dentro de reajuste_anual.py: la
regla de generacion de fechas es genuinamente distinta (una lista arbitraria
de "MM-DD" por año, no un cursor mes a mes de 1 a 12) y el bucle principal de
generar_cuotas_mensuales() esta escrito asumiendo cadencia mensual (avanza
mes_cursor de 1 en 1, calcula la fecha con dia_pago fijo) -- forzar ambas
cadencias dentro de la misma funcion habria requerido una rama condicional que
oscurece las dos, en vez de aclarar. Lo que SI se reutiliza tal cual (no se
duplica) es lo que es genuinamente compartido:
- `reajustar_capital_anual` (Sprint 41, hecha publica para este sprint) --
  misma formula de reajuste SMMLV/IPC, aplicada aqui de forma OPCIONAL (a
  diferencia de generar_cuotas_mensuales, que exige tipo_reajuste_anual
  activo, este generador funciona igual de bien con NINGUNO -- el caso mas
  comun para gastos de vestuario, que no necesariamente reajustan cada año).
- El patron de Obligacion PUNTUAL hija con `obligacion_padre_id` apuntando a
  la RECURRENTE padre, la idempotencia (retorna las cuotas ya persistidas en
  vez de duplicar), y el manejo de sesion (abre/cierra la propia, lee todos
  los campos del padre a Python ANTES de abrir su sesion) -- exactamente el
  mismo contrato que generar_cuotas_mensuales, para que
  CivilFamiliaStrategy._eventos_de_obligacion (app/services/area_strategy.py)
  y el boton "Generar cuotas" de ExpedienteDetallePage puedan tratar el
  resultado de cualquiera de los dos generadores exactamente igual (cuotas
  hijas reales, sistema de abonos por cuota del Sprint 41 sin cambios).

Limitacion conocida (Sprint 74): el cumpleaños del beneficiario se sigue
ingresando aqui como una entrada "MM-DD" manual mas dentro de la lista -- NO
se deriva automaticamente de `Beneficiario.fecha_nacimiento` (la entidad SI
existe desde el Sprint 74, ver database/models.py, pero esa derivacion
automatica -- ej. agregar la fecha MM-DD del cumpleaños solo con marcar el
beneficiario -- queda fuera del alcance de ese sprint). Lo que SI se agrego en
el Sprint 74 es el tope de vigencia: si la obligacion tiene un Beneficiario
NINO sin discapacidad, la generacion se corta en su fecha de fin de vigencia
(18/25 años segun si estudia), igual que generar_cuotas_mensuales -- ver
fecha_fin_efectiva_recurrente mas abajo.
"""

from __future__ import annotations

import calendar
import json
import re
from datetime import date

import database.session as session_module
from app.engine.time.calendar import CalendarUtils
from app.services.reajuste_anual import reajustar_capital_anual
from app.services.vigencia_alimentos import fecha_fin_efectiva_recurrente
from database.models import (
    Beneficiario,
    Obligacion,
    TipoObligacion,
    TipoReajusteAnual,
    TipoRecurrencia,
)

_PATRON_MM_DD = re.compile(r"^\d{2}-\d{2}$")
# 2000 es bisiesto -- se usa solo como año de referencia para validar que el
# dia exista en ese mes, sin rechazar "02-29" (fecha MM-DD legitima aunque no
# ocurra todos los años; CalendarUtils.safe_create_date la topa a 28 en años
# no bisiestos al generar la cuota real, igual que ya hace con dia_pago=31).
_ANIO_BISIESTO_REFERENCIA = 2000


def _validar_formato_mm_dd(fecha_mm_dd: str) -> None:
    if not _PATRON_MM_DD.match(fecha_mm_dd):
        raise ValueError(
            f"Fecha '{fecha_mm_dd}' invalida -- use el formato MM-DD (ej. '06-15')."
        )
    mes, dia = (int(parte) for parte in fecha_mm_dd.split("-"))
    if not 1 <= mes <= 12:
        raise ValueError(f"Fecha '{fecha_mm_dd}' invalida -- el mes debe estar entre 01 y 12.")
    _, ultimo_dia_real = calendar.monthrange(_ANIO_BISIESTO_REFERENCIA, mes)
    if not 1 <= dia <= ultimo_dia_real:
        raise ValueError(f"Fecha '{fecha_mm_dd}' invalida -- el mes {mes:02d} no tiene dia {dia}.")


def serializar_fechas_anuales(fechas: list[str]) -> str:
    """Valida y serializa una lista de fechas "MM-DD" a JSON, para guardarlas
    en `Obligacion.fechas_anuales_fijas` -- mismo patron de "lista JSON en
    columna String" que ya usa `ParametroLegal.areas_derecho`
    (app/services/areas_parametro.py, Sprint 57)."""
    if not fechas:
        raise ValueError("Debe indicarse al menos una fecha anual fija (formato MM-DD).")
    for fecha_mm_dd in fechas:
        _validar_formato_mm_dd(fecha_mm_dd)
    return json.dumps(fechas)


def deserializar_fechas_anuales(texto: str | None) -> list[str]:
    """Inverso de `serializar_fechas_anuales`. Tolerante a None/cadena vacia
    (obligacion RECURRENTE mensual que nunca configuro esta columna, o fila
    legada anterior al Sprint 73) -- retorna lista vacia en vez de lanzar."""
    if not texto:
        return []
    return json.loads(texto)


def generar_cuotas_fechas_fijas(
    obligacion_recurrente: Obligacion, fecha_corte: date
) -> list[Obligacion]:
    """Genera y persiste una Obligacion PUNTUAL por cada fecha "MM-DD" de
    `obligacion_recurrente.fechas_anuales_fijas`, una vez por cada año entre
    `fecha_origen` (equivalente a fecha_inicio para una obligacion RECURRENTE,
    ver ObligacionFormDialog.guardar()) y la fecha de corte (topada por
    `fecha_fin` si esta seteada) -- igual que generar_cuotas_mensuales
    (Sprint 41), pero con una lista arbitraria de fechas por año en vez de un
    cursor mensual fijo. Idempotente: si esta obligacion ya tiene cuotas hijas
    persistidas, las retorna tal cual en vez de generar duplicados.

    El reajuste anual (SMMLV/IPC) es OPCIONAL aqui -- a diferencia de
    generar_cuotas_mensuales, que rechaza tipo_reajuste_anual NINGUNO, este
    generador funciona igual de bien sin reajuste (el caso tipico de gastos
    de vestuario, que no necesariamente aumentan cada año) y lo aplica si esta
    configurado, reutilizando reajustar_capital_anual tal cual.

    Abre y cierra su propia sesion de SQLAlchemy (mismo patron que
    generar_cuotas_mensuales/parametro_service.py)."""
    if obligacion_recurrente.tipo != TipoObligacion.RECURRENTE:
        raise ValueError("Solo una obligacion RECURRENTE puede generar cuotas de fechas fijas.")
    if obligacion_recurrente.tipo_recurrencia != TipoRecurrencia.FECHAS_ANUALES_FIJAS:
        raise ValueError(
            "La obligacion no tiene tipo_recurrencia FECHAS_ANUALES_FIJAS -- "
            "generar_cuotas_fechas_fijas no aplica a la cadencia MENSUAL (ver "
            "generar_cuotas_mensuales en app/services/reajuste_anual.py)."
        )

    fechas_mm_dd = deserializar_fechas_anuales(obligacion_recurrente.fechas_anuales_fijas)
    if not fechas_mm_dd:
        raise ValueError(
            "La obligacion debe tener al menos una fecha anual fija (MM-DD) configurada."
        )

    obligacion_padre_id = obligacion_recurrente.id
    expediente_id = obligacion_recurrente.expediente_id
    concepto_base = obligacion_recurrente.concepto
    categoria = obligacion_recurrente.categoria
    tasa_efectiva_anual = obligacion_recurrente.tasa_efectiva_anual
    aplica_indexacion_ipc = obligacion_recurrente.aplica_indexacion_ipc
    interes_sobre_capital_indexado = obligacion_recurrente.interes_sobre_capital_indexado
    fecha_inicio = obligacion_recurrente.fecha_origen
    fecha_fin = obligacion_recurrente.fecha_fin
    tipo_reajuste = obligacion_recurrente.tipo_reajuste_anual
    capital_inicial = obligacion_recurrente.valor

    fechas_ordenadas = sorted(
        (int(mm_dd.split("-")[0]), int(mm_dd.split("-")[1])) for mm_dd in fechas_mm_dd
    )
    aplica_reajuste = tipo_reajuste is not None and tipo_reajuste != TipoReajusteAnual.NINGUNO

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

        # Vigencia por tipo de beneficiario (Sprint 74) -- mismo criterio que
        # generar_cuotas_mensuales (app/services/reajuste_anual.py): se consulta
        # directo por obligacion_padre_id dentro de esta misma sesion (evita
        # depender de la relationship sobre un objeto potencialmente detached).
        beneficiario = (
            session.query(Beneficiario).filter_by(obligacion_id=obligacion_padre_id).first()
        )
        fin_vigencia = fecha_fin_efectiva_recurrente(fecha_fin, beneficiario, fecha_corte)
        fin = min(fin_vigencia, fecha_corte) if fin_vigencia is not None else fecha_corte

        cuotas_nuevas: list[Obligacion] = []
        capital_actual = capital_inicial
        anio_capital = fecha_inicio.year
        anio_cursor = fecha_inicio.year

        while date(anio_cursor, 1, 1) <= fin:
            # Reajuste anual OPCIONAL: mismo criterio de "una sola vez por
            # transicion de año" que generar_cuotas_mensuales, pero por año
            # completo (no por mes) porque aqui el cursor avanza en años.
            if anio_cursor != anio_capital:
                if aplica_reajuste:
                    capital_actual = reajustar_capital_anual(
                        capital_actual, anio_cursor, tipo_reajuste
                    )
                anio_capital = anio_cursor

            for mes, dia in fechas_ordenadas:
                cuota_fecha = CalendarUtils.safe_create_date(anio_cursor, mes, dia)
                if cuota_fecha < fecha_inicio or cuota_fecha > fin:
                    continue
                concepto = f"{concepto_base} - {cuota_fecha.strftime('%d/%m/%Y')}"
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

            anio_cursor += 1

        session.commit()
        return cuotas_nuevas
    finally:
        session.close()
