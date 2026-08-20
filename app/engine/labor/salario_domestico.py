from decimal import Decimal

from app.engine.math.rounding import Rounding

DIAS_MES_COMERCIAL = Decimal("30")
DIAS_SEMANA = Decimal("7")


def salario_diario_a_mensual(salario_diario, dias_laborados_semana) -> Decimal:
    """Convierte un salario pactado por dia a su equivalente mensual para efectos
    de prestaciones sociales, segun la formula de la plantilla del despacho
    `L2A.COMPROBANTEDELIQUIDACIONDEPRESTACIONESSOCIALES...EMPLEADADOMESTICA.md`
    (Sprint 96): salario_diario x dias_laborados_semana / 7 x 30.

    La plantilla aclara que, a efectos de prestaciones, el mes se contabiliza
    siempre como de 30 dias (mes comercial), independientemente de los dias
    calendario reales. Sirve tanto para el salario como para el auxilio de
    transporte pactado por dia (misma formula).

    Alcance deliberadamente limitado (ver docs/Pendientes.md, Sprint 96, y la
    pregunta abierta en docs/Preguntas-Para-Abogado-Abiertas.md): esta funcion
    solo resuelve la CONVERSION de salario diario a base mensual. No decide si el
    regimen prestacional del trabajo domestico difiere en FORMULA del regimen
    general tras la Ley 1788 de 2016 -- esa confirmacion del despacho sigue
    pendiente, y hasta tenerla no se cablea esta conversion a ningun formulario ni
    a LaboralStrategy.
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
