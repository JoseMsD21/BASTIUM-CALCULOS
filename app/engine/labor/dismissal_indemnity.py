from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.engine.math.rounding import Rounding
from app.engine.time.calendar import CalendarUtils
from database.models import TipoContratoLaboral

DIAS_ANIO_COMERCIAL = Decimal("360")
PISO_DIAS_TERMINO_FIJO = Decimal("15")
MULTIPLICADOR_SMMLV_UMBRAL = Decimal("10")


class RegimenNoSoportadoError(ValueError):
    """La combinacion de datos pedida no tiene una formula confirmada por el
    despacho todavia -- ver docs/Preguntas-Para-Abogado-Abiertas.md, seccion
    Sprint 92. Se lanza en vez de adivinar una cifra."""


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

    Regimenes soportados, con los numeros exactos transcritos en el sprint
    (docs/Pendientes.md, Sprint 92) a partir de
    `L4.INDEMNIZACIONPORDESPIDOLABORALYSANCIONMORATORIA.md`:

    - INDEFINIDO, salario < 10 SMMLV, regimen posterior a la Ley 50/1990
      (modificado por la Ley 789/2002): 30 dias de salario basico el primer
      año + 20 dias por cada año subsiguiente (y fraccion proporcional).
      Formula continua (sin tramos adicionales por 5/10 años) -- asi la trae
      el Art. 64 CST vigente, y el sprint no cita ningun quiebre distinto
      para este regimen.
    - INDEFINIDO, salario < 10 SMMLV, regimen anterior a la Ley 50/1990: 45
      dias el primer año + 15 dias por cada año subsiguiente (misma formula
      continua, unico dato que el sprint transcribe con cifras exactas para
      este regimen).
    - FIJO/OBRA_LABOR (cualquier salario): valor de los salarios
      correspondientes al tiempo que faltare para cumplir el plazo pactado,
      con un piso de 15 dias de salario cuando ese tiempo restante sea menor.

    Deliberadamente NO soportado (lanza RegimenNoSoportadoError en vez de
    inventar una cifra -- ver docs/Preguntas-Para-Abogado-Abiertas.md, Sprint
    92):

    - INDEFINIDO con salario >= 10 SMMLV: el sprint solo confirma que este
      umbral existe y distingue tablas, pero no transcribe la formula/dias
      exactos de la tabla "salario >= 10 SMMLV" (la plantilla original del
      despacho, `L4...md`, no esta en este checkout).
    - Cualquier tramo del regimen pre-Ley 50/1990 mas alla de la formula
      continua de arriba (ej. una tasa distinta de dias/año subsiguiente a
      partir de 5 o 10 años de antiguedad): el propio backlog advierte que la
      plantilla original "trae varios regimenes por estos tramos", pero solo
      transcribe una cifra (45+15) -- no se asume que esa tasa se mantiene
      igual en tramos mas altos.

    FECHA DE CORTE DEL REGIMEN (`FECHA_CORTE_LEY_50_1990`, default
    1991-01-01): la plantilla original del despacho trae una inconsistencia
    no resuelta (dos secciones citan "27 de diciembre de 1.992" para el
    corte, pero una la atribuye a la Ley 789/2002 y la otra a la Ley 50 de
    1990 -- que es de 1990, no de 1992). Este calculador usa por defecto el
    1 de enero de 1991 (entrada en vigencia real y citable de la Ley 50 de
    1990, publicada el 28 de diciembre de 1990) mientras el despacho no
    confirme la fecha real -- ver docs/Preguntas-Para-Abogado-Abiertas.md,
    seccion "Sprint 92". El parametro `fecha_corte_regimen` permite
    sobreescribir este valor asumido sin tocar el codigo en cuanto llegue la
    confirmacion.
    """

    FECHA_CORTE_LEY_50_1990 = date(1991, 1, 1)

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
    ) -> DismissalIndemnityResult:
        if fecha_terminacion <= fecha_ingreso:
            raise ValueError(
                "fecha_terminacion debe ser posterior a fecha_ingreso para calcular la "
                "antiguedad del contrato."
            )

        umbral_10_smmlv = smlmv_mensual * MULTIPLICADOR_SMMLV_UMBRAL
        if salario_mensual >= umbral_10_smmlv:
            raise RegimenNoSoportadoError(
                f"Salario mensual ({salario_mensual}) >= 10 SMMLV ({umbral_10_smmlv}): "
                "la formula de indemnizacion por despido para este umbral no esta "
                "confirmada por el despacho todavia (ver "
                "docs/Preguntas-Para-Abogado-Abiertas.md, seccion Sprint 92) -- no se "
                "calcula para evitar inventar una cifra."
            )

        if fecha_ingreso < fecha_corte_regimen:
            regimen = "INDEFINIDO_PRE_LEY_50_1990"
            dias_primer_anio = Decimal("45")
            dias_por_anio_subsiguiente = Decimal("15")
        else:
            regimen = "INDEFINIDO_POST_LEY_50_1990"
            dias_primer_anio = Decimal("30")
            dias_por_anio_subsiguiente = Decimal("20")

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
