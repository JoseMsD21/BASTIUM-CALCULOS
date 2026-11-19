from decimal import Decimal

from app.engine.math.rounding import Rounding

DIAS_MES_COMERCIAL = Decimal("30")
DIAS_SEMANA = Decimal("7")
# Respuesta del despacho (Sprint 96, seguimiento): el auxilio de transporte
# "aplica para salarios de hasta 2 SMMLV".
TOPE_SMMLV_AUXILIO_TRANSPORTE = Decimal("2")


def salario_diario_a_mensual(salario_diario, dias_laborados_semana) -> Decimal:
    """Convierte un salario pactado por dia a su equivalente mensual para efectos
    de prestaciones sociales, segun la formula de la plantilla del despacho
    `L2A.COMPROBANTEDELIQUIDACIONDEPRESTACIONESSOCIALES...EMPLEADADOMESTICA.md`
    (Sprint 96): salario_diario x dias_laborados_semana / 7 x 30.

    La plantilla aclara que, a efectos de prestaciones, el mes se contabiliza
    siempre como de 30 dias (mes comercial), independientemente de los dias
    calendario reales. Sirve tanto para el salario como para el auxilio de
    transporte pactado por dia (misma formula).

    Respuesta del despacho (Sprint 96, 22/08/2026): "no existe diferencia
    algebraica en las formulas de liquidacion tras la Ley 1788" -- confirma
    que las prestaciones se calculan reutilizando `LaborScheduler` (la misma
    clase general) sobre esta base mensual convertida, sin motor nuevo. Ver
    `calcular_ibc_seguridad_social_domestico` para el piso adicional que la
    misma respuesta agrego para la base de seguridad social.
    """
    salario_diario = Decimal(str(salario_diario))
    dias_laborados_semana = Decimal(str(dias_laborados_semana))

    if salario_diario < 0:
        raise ValueError("El salario diario no puede ser negativo.")
    if not (Decimal("1") <= dias_laborados_semana <= DIAS_SEMANA):
        raise ValueError(
            "Los dias laborados en la semana deben estar entre 1 y 7 "
            f"(recibido: {dias_laborados_semana})."
        )

    base_mensual = salario_diario * dias_laborados_semana / DIAS_SEMANA * DIAS_MES_COMERCIAL
    return Rounding.money(base_mensual)


def calcular_ibc_seguridad_social_domestico(salario_proporcional, smmlv_mensual) -> Decimal:
    """IBC (Ingreso Base de Cotizacion) para seguridad social de un contrato
    de trabajo domestico por dias/jornada parcial: nunca puede ser inferior a
    1 SMMLV, aunque el salario proporcional efectivamente devengado (via
    `salario_diario_a_mensual`) sea menor -- respuesta del despacho (Sprint
    96, 22/08/2026): "IBC_Seguridad_Social = max(Salario_Proporcional,
    1_SMMLV)".

    Aplica SOLO a la base de cotizacion de seguridad social (pension/salud/
    ARL) -- las prestaciones sociales (cesantias, prima, vacaciones) se
    siguen liquidando sobre el salario proporcional real, sin este piso."""
    salario_proporcional = Decimal(str(salario_proporcional))
    smmlv_mensual = Decimal(str(smmlv_mensual))

    if salario_proporcional < 0:
        raise ValueError("El salario proporcional no puede ser negativo.")
    if smmlv_mensual <= 0:
        raise ValueError("El SMMLV mensual debe ser mayor que cero.")

    return max(salario_proporcional, smmlv_mensual)


def dias_laborados_mes(dias_laborados_semana) -> Decimal:
    """Dias efectivamente laborados en el mes (comercial de 30 dias) a partir
    de los dias laborados por semana -- la misma conversion de la plantilla
    L2A que usa `salario_diario_a_mensual`: dias_laborados_semana / 7 x 30.
    Sin redondear (puede ser fraccionario, p.ej. 3 dias/semana = 12,857...):
    se redondea solo el monto en pesos que se calcule con ella."""
    dias_laborados_semana = Decimal(str(dias_laborados_semana))
    if not (Decimal("1") <= dias_laborados_semana <= DIAS_SEMANA):
        raise ValueError(
            "Los dias laborados en la semana deben estar entre 1 y 7 "
            f"(recibido: {dias_laborados_semana})."
        )
    return dias_laborados_semana / DIAS_SEMANA * DIAS_MES_COMERCIAL


def auxilio_transporte_domestico(
    auxilio_mensual, dias_laborados_semana, salario_mensual_equivalente, smmlv_mensual
) -> Decimal:
    """Auxilio de transporte mensual de un contrato de trabajo domestico por
    dias/jornada parcial (Sprint 96, seguimiento). Respuesta del despacho
    (23/08/2026): "Si, es un concepto que debe liquidarse. Aplica para
    salarios de hasta 2 SMMLV. Para trabajo domestico por dias o jornadas
    fraccionadas, se liquida estricta y proporcionalmente a los dias
    efectivamente laborados en el mes (Auxilio_Mensual / 30) * Dias_Trabajados.
    Ademas, este auxilio forma parte obligatoria de la base de liquidacion
    para cesantias y prima de servicios."

    - `auxilio_mensual`: auxilio de transporte mensual vigente (pleno).
    - Dias_Trabajados: se derivan de `dias_laborados_semana` con
      `dias_laborados_mes` (dias/7 x 30, misma conversion de la plantilla
      L2A que ya se usa para el salario) -- supuesto de implementacion: el
      formulario no captura los dias del mes, solo los de la semana.
    - Tope "hasta 2 SMMLV" (inclusive): se compara contra
      `salario_mensual_equivalente`, el salario mensual proporcional que
      produce `salario_diario_a_mensual` (el mismo `valor` sobre el que se
      liquidan las prestaciones). Si lo supera, retorna 0,00.
    """
    auxilio_mensual = Decimal(str(auxilio_mensual))
    salario_mensual_equivalente = Decimal(str(salario_mensual_equivalente))
    smmlv_mensual = Decimal(str(smmlv_mensual))

    if auxilio_mensual < 0:
        raise ValueError("El auxilio de transporte mensual no puede ser negativo.")
    if salario_mensual_equivalente < 0:
        raise ValueError("El salario mensual equivalente no puede ser negativo.")
    if smmlv_mensual <= 0:
        raise ValueError("El SMMLV mensual debe ser mayor que cero.")

    dias_mes = dias_laborados_mes(dias_laborados_semana)
    if salario_mensual_equivalente > TOPE_SMMLV_AUXILIO_TRANSPORTE * smmlv_mensual:
        return Decimal("0.00")
    return Rounding.money(auxilio_mensual / DIAS_MES_COMERCIAL * dias_mes)
