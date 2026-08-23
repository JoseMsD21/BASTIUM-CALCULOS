from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.engine.math.rounding import Rounding
from app.engine.time.calendar import CalendarUtils
from database.models import TipoContratoLaboral

DIAS_ANIO_COMERCIAL = Decimal("360")
PISO_DIAS_TERMINO_FIJO = Decimal("15")
MULTIPLICADOR_SMMLV_UMBRAL = Decimal("10")


@dataclass(frozen=True)
class DismissalIndemnityResult:
    regimen: str
    antiguedad_anios: Decimal
    dias_indemnizacion: Decimal
    salario_diario: Decimal
    total: Decimal


class DismissalIndemnityCalculator:
    """
    Indemnizacion por despido injustificado, Art. 64 CST (Sprint 92) --
    concepto legal distinto de la indemnizacion moratoria del Art. 65 CST
    (MoratoryIndemnityCalculator, mismo paquete): esta es compensacion por la
    terminacion sin justa causa del contrato, no por mora en el pago de
    prestaciones ya causadas. Los dos eventos son legalmente compatibles y
    pueden coexistir en el mismo expediente (ver LaboralStrategy, evento
    INDEMNIZACION_DESPIDO) -- este calculador nunca los suma automaticamente
    ni asume que uno excluye al otro.

    Regimenes soportados (respuesta del despacho, Sprint 92, 22/08/2026 --
    ver docs/Preguntas-Para-Abogado-Respondidas.md, "Sprint 92"):

    - INDEFINIDO, salario >= 10 SMMLV, ingreso desde el 27/12/2002 (Ley
      789/2002): 20 dias el primer año + 15 dias por cada año subsiguiente
      (y fraccion proporcional), tabla propia sin tramos adicionales.
    - INDEFINIDO, salario < 10 SMMLV (o salario >= 10 SMMLV con ingreso
      anterior al 27/12/2002, cuando la distincion por salario todavia no
      existia), ingreso desde el 01/01/1991 (Ley 50/1990): 30 dias el primer
      año + 20 dias por cada año subsiguiente, formula continua sin tramos
      adicionales.
    - INDEFINIDO, ingreso anterior al 01/01/1991 (Decreto 2351/1965): 45 dias
      el primer año; por cada año subsiguiente, una tasa fija segun la
      antiguedad TOTAL del contrato (no progresiva año a año): 15 dias/año si
      la antiguedad es menor a 5 años, 20 dias/año entre 5 y menos de 10
      años, 30 dias/año desde 10 años. El limite inferior de cada tramo es
      inclusivo (misma convencion que `semanas_minimas_requeridas`): exactamente
      5 años cae en el tramo de 20, exactamente 10 años cae en el tramo de 30.
    - FIJO/OBRA_LABOR (cualquier salario): valor de los salarios
      correspondientes al tiempo que faltare para cumplir el plazo pactado,
      con un piso de 15 dias de salario cuando ese tiempo restante sea menor.

    FECHAS DE CORTE (`FECHA_CORTE_LEY_50_1990` 1991-01-01,
    `FECHA_CORTE_LEY_789_2002` 2002-12-27): ambas confirmadas explicitamente
    por el despacho con esas fechas calendario. Los parametros
    `fecha_corte_regimen` y `fecha_corte_ley_789_2002` permiten
    sobreescribirlas sin tocar el codigo si mas adelante se detecta un caso
    real que exija otra fecha.
    """

    FECHA_CORTE_LEY_50_1990 = date(1991, 1, 1)
    FECHA_CORTE_LEY_789_2002 = date(2002, 12, 27)

    @staticmethod
    def calcular(
        *,
        tipo_contrato: TipoContratoLaboral,
        salario_mensual: Decimal,
        fecha_ingreso: date,
        fecha_terminacion: date,
        despido_injustificado: bool,
        smlmv_mensual: Decimal,
        fecha_fin_pactada: date | None = None,
        fecha_corte_regimen: date | None = None,
        fecha_corte_ley_789_2002: date | None = None,
    ) -> DismissalIndemnityResult:
        if not despido_injustificado:
            return DismissalIndemnityResult(
                regimen="NO_APLICA",
                antiguedad_anios=Decimal("0"),
                dias_indemnizacion=Decimal("0"),
                salario_diario=Decimal("0.00"),
                total=Decimal("0.00"),
            )

        salario_diario = salario_mensual / Decimal("30")

        if tipo_contrato in (TipoContratoLaboral.FIJO, TipoContratoLaboral.OBRA_LABOR):
            return DismissalIndemnityCalculator._calcular_termino_fijo(
                salario_diario=salario_diario,
                fecha_terminacion=fecha_terminacion,
                fecha_fin_pactada=fecha_fin_pactada,
            )

        return DismissalIndemnityCalculator._calcular_indefinido(
            salario_mensual=salario_mensual,
            salario_diario=salario_diario,
            fecha_ingreso=fecha_ingreso,
            fecha_terminacion=fecha_terminacion,
            smlmv_mensual=smlmv_mensual,
            fecha_corte_regimen=(
                fecha_corte_regimen
                if fecha_corte_regimen is not None
                else DismissalIndemnityCalculator.FECHA_CORTE_LEY_50_1990
            ),
            fecha_corte_ley_789_2002=(
                fecha_corte_ley_789_2002
                if fecha_corte_ley_789_2002 is not None
                else DismissalIndemnityCalculator.FECHA_CORTE_LEY_789_2002
            ),
        )

    @staticmethod
    def _calcular_termino_fijo(
        *,
        salario_diario: Decimal,
        fecha_terminacion: date,
        fecha_fin_pactada: date | None,
    ) -> DismissalIndemnityResult:
        if fecha_fin_pactada is None:
            raise ValueError(
                "fecha_fin_pactada es obligatoria para calcular la indemnizacion de un "
                "contrato a termino fijo/obra-labor (se necesita para saber el tiempo "
                "que faltaba para cumplir el plazo pactado)."
            )
        if fecha_fin_pactada <= fecha_terminacion:
            raise ValueError(
                "fecha_fin_pactada debe ser posterior a fecha_terminacion -- si el "
                "contrato ya habia cumplido su plazo pactado, no hay tiempo restante "
                "que indemnizar bajo esta formula."
            )

        dias_restantes = Decimal((fecha_fin_pactada - fecha_terminacion).days)
        dias_indemnizacion = max(dias_restantes, PISO_DIAS_TERMINO_FIJO)

        return DismissalIndemnityResult(
            regimen="TERMINO_FIJO_OBRA_LABOR",
            antiguedad_anios=Decimal("0"),
            dias_indemnizacion=dias_indemnizacion,
            salario_diario=salario_diario,
            total=Rounding.money(salario_diario * dias_indemnizacion),
        )

    @staticmethod
    def _calcular_indefinido(
        *,
        salario_mensual: Decimal,
        salario_diario: Decimal,
        fecha_ingreso: date,
        fecha_terminacion: date,
        smlmv_mensual: Decimal,
        fecha_corte_regimen: date,
        fecha_corte_ley_789_2002: date,
    ) -> DismissalIndemnityResult:
        if fecha_terminacion <= fecha_ingreso:
            raise ValueError(
                "fecha_terminacion debe ser posterior a fecha_ingreso para calcular la "
                "antiguedad del contrato."
            )

        # Antiguedad bajo la misma convencion "comercial" de año de 360 dias
        # (12 meses de 30 dias) ya usada por LaboralStrategy para prestaciones
        # sociales (CalendarUtils.dias_comerciales_360, Sprint 30) -- evita que
        # el conteo de años/dias subsiguientes quede distorsionado por años
        # bisiestos (calendario real) frente a la tabla de dias de la
        # plantilla, que esta pensada en meses de 30 dias. Se resta 1 porque
        # dias_comerciales_360 es inclusiva (+1, confirmada especificamente
        # para prestaciones sociales) y la antiguedad de un contrato no debe
        # sumar ese dia extra.
        dias_totales = Decimal(
            CalendarUtils.dias_comerciales_360(fecha_ingreso, fecha_terminacion) - 1
        )
        anios_completos = int(dias_totales // DIAS_ANIO_COMERCIAL)
        dias_resto = dias_totales - (Decimal(anios_completos) * DIAS_ANIO_COMERCIAL)
        antiguedad_anios = Decimal(anios_completos) + (dias_resto / DIAS_ANIO_COMERCIAL)

        umbral_10_smmlv = smlmv_mensual * MULTIPLICADOR_SMMLV_UMBRAL
        if salario_mensual >= umbral_10_smmlv and fecha_ingreso >= fecha_corte_ley_789_2002:
            regimen = "INDEFINIDO_UMBRAL_10_SMMLV_LEY_789_2002"
            dias_primer_anio = Decimal("20")
            dias_por_anio_subsiguiente = Decimal("15")
        elif fecha_ingreso < fecha_corte_regimen:
            regimen = "INDEFINIDO_PRE_LEY_50_1990"
            dias_primer_anio = Decimal("45")
            dias_por_anio_subsiguiente = (
                DismissalIndemnityCalculator._dias_subsiguiente_decreto_2351_1965(
                    antiguedad_anios
                )
            )
        else:
            regimen = "INDEFINIDO_POST_LEY_50_1990"
            dias_primer_anio = Decimal("30")
            dias_por_anio_subsiguiente = Decimal("20")

        if antiguedad_anios > Decimal("1"):
            anios_subsiguientes = antiguedad_anios - Decimal("1")
            dias_indemnizacion = dias_primer_anio + (
                dias_por_anio_subsiguiente * anios_subsiguientes
            )
        else:
            dias_indemnizacion = dias_primer_anio

        return DismissalIndemnityResult(
            regimen=regimen,
            antiguedad_anios=antiguedad_anios,
            dias_indemnizacion=dias_indemnizacion,
            salario_diario=salario_diario,
            total=Rounding.money(salario_diario * dias_indemnizacion),
        )

    @staticmethod
    def _dias_subsiguiente_decreto_2351_1965(antiguedad_anios: Decimal) -> Decimal:
        """Tasa de dias/año subsiguiente del regimen pre-Ley 50/1990 (Decreto
        2351/1965), segun la antiguedad TOTAL del contrato (respuesta del
        despacho, Sprint 92, 22/08/2026) -- una unica tasa aplicada a todos
        los años subsiguientes, no una escala progresiva año a año."""
        if antiguedad_anios < Decimal("5"):
            return Decimal("15")
        if antiguedad_anios < Decimal("10"):
            return Decimal("20")
        return Decimal("30")
