"""Interes de mora en condenas o conciliaciones contra el Estado (Art. 195
num. 4 de la Ley 1437 de 2011, CPACA) -- Sprint 82, respuesta del despacho
(22/08/2026): regimen dual, DTF durante los primeros 10 meses desde la
ejecutoria y luego tasa comercial (1,5x el IBC certificado, equivalente a
la tasa de usura del Art. 884 C.Co.).

Funcion AISLADA, sin conectar a ninguna AreaStrategy: el area de BASTIUM
donde deberia vivir este calculador (litigio contra una entidad publica)
sigue sin confirmar -- la respuesta del despacho dio la formula pero no
contesto la pregunta original del Sprint 82 (si el despacho maneja este
tipo de casos y en que area encajarian). Ver docs/Pendientes.md, Sprint 82,
y la pregunta de seguimiento en docs/Preguntas-Para-Abogado-Abiertas.md.

El "consejo" del despacho de congelar el conteo tras 3 meses de inactividad
sin cobro NO esta implementado: es una sugerencia de interfaz ("puede
ponerse"), no una regla obligatoria, y requeriria un dato (fecha del ultimo
cobro/actuacion) que el modelo de datos actual no captura."""

from datetime import date, timedelta
from decimal import Decimal

from app.engine.financial.rate import Rate
from app.engine.indexation.historical_dtf import get_dtf_for_date
from app.engine.indexation.historical_index import get_ibc_usura_for_date
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.engine.math.rounding import Rounding

LIMITE_GRACIA_DIAS = 304  # Art. 195 num. 4 Ley 1437/2011: promedio de 10 meses reales.
MULTIPLICADOR_TASA_COMERCIAL = Decimal("1.5")  # 1.5x IBC, equivalente a la tasa de usura.


def _tasa_diaria_para(fecha: date, dias_transcurridos: int) -> Rate:
    if dias_transcurridos <= LIMITE_GRACIA_DIAS:
        dtf_anual_pct = get_dtf_for_date(fecha)
    else:
        ibc_anual_pct, _usura_anual_pct = get_ibc_usura_for_date(fecha)
        dtf_anual_pct = MULTIPLICADOR_TASA_COMERCIAL * ibc_anual_pct
    return EffectiveRateConverter.annual_to_daily(dtf_anual_pct)


def calcular_interes_dtf_condena_administrativa(
    capital: Decimal, fecha_ejecutoria: date, fecha_corte: date
) -> Decimal:
    """Interes de mora, dia a dia, sobre `capital` desde `fecha_ejecutoria`
    hasta `fecha_corte` (ambas inclusive del primer dia, exclusive del
    ultimo -- el interes del dia de corte mismo no se causa, mismo criterio
    que el resto del motor cuenta "dias transcurridos"). Tramo A (DTF)
    durante los primeros 304 dias; Tramo B (1,5x IBC) de ahi en adelante.
    Interes simple diario (no compuesto sobre saldo creciente), igual que
    el resto del motor de liquidacion (DailyInterest.calculate).

    Lanza ValueError si fecha_corte es anterior a fecha_ejecutoria."""
    if fecha_corte < fecha_ejecutoria:
        raise ValueError(
            f"fecha_corte ({fecha_corte}) no puede ser anterior a "
            f"fecha_ejecutoria ({fecha_ejecutoria})."
        )

    total_interes = Decimal("0.00")
    dia_actual = fecha_ejecutoria
    dias_transcurridos = 0
    while dia_actual < fecha_corte:
        dias_transcurridos += 1
        tasa_diaria = _tasa_diaria_para(dia_actual, dias_transcurridos)
        total_interes += DailyInterest.calculate(capital, tasa_diaria, days=1)
        dia_actual += timedelta(days=1)

    return Rounding.money(total_interes)
