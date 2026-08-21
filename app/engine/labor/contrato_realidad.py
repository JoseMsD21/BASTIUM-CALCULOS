from decimal import Decimal

from app.engine.math.rounding import Rounding


def calcular_aporte_contrato_realidad(base, porcentaje) -> Decimal:
    """Liquida un aporte a salud o pension reclamado en un contrato realidad
    (relacion laboral disfrazada de prestacion de servicios): `base x
    porcentaje/100`.

    Aplica al concepto "APORTE SALUD"/"APORTE PENSION" de las plantillas del
    despacho `L7.LIQUIDACIONDEPRESTACIONESSOCIALESENCONTRATOREALIDAD.md`
    (privado, 8.5%/12%) y `L8...PUBLICOCONTRATOREALIDAD.md` (publico, 8%/12%).

    Deliberadamente NO trae hardcodeado ningun porcentaje: la plantilla usa
    cifras distintas a las que ya confirmo el despacho para seguridad social
    laboral general (16% pension + 12.5% salud, total empleador+trabajador,
    Sprint 16), y sigue pendiente de confirmacion si en un contrato realidad
    lo reclamable es ese mismo total o solo la porcion a cargo del empleador
    (ver docs/Pendientes.md, Sprint 94, y
    docs/Preguntas-Para-Abogado-Abiertas.md). Esta funcion solo formaliza,
    con tests, la formula aritmetica -- no esta cableada a ningun formulario,
    `parametro_service` ni `LaboralStrategy`.
    """
    base = Decimal(str(base))
    porcentaje = Decimal(str(porcentaje))
    if base < 0:
        raise ValueError("La base no puede ser negativa.")
    if porcentaje < 0:
        raise ValueError("El porcentaje no puede ser negativo.")

    return Rounding.money(base * porcentaje / Decimal("100"))


def calcular_bonificacion_por_servicio_escalonada(
    base, aplica_porcentaje_elevado, porcentaje_estandar, porcentaje_elevado
) -> Decimal:
    """Liquida la bonificacion por servicio del sector publico en un contrato
    realidad, cuyo porcentaje cambia segun una condicion de tope: `base x
    porcentaje/100`, usando `porcentaje_elevado` si `aplica_porcentaje_elevado`
    es verdadero, o `porcentaje_estandar` en caso contrario.

    Formaliza la estructura "escalonada por tope" de la anotacion de la
    plantilla del despacho `L8...PUBLICOCONTRATOREALIDAD.md` ("corresponde al
    35%, pero hasta 2 smmlv, escriba 50%"), sin decidir la condicion exacta:
    sigue pendiente de confirmacion del despacho tanto la norma que respalda
    la regla como que exactamente activa el porcentaje elevado (si es el
    propio `base` el que debe compararse contra 2 SMMLV, o algun otro monto -
    ver docs/Pendientes.md, Sprint 94, y
    docs/Preguntas-Para-Abogado-Abiertas.md). El llamador decide
    `aplica_porcentaje_elevado`; esta funcion solo formaliza, con tests, la
    formula aritmetica resultante -- no esta cableada a ningun formulario,
    `parametro_service` ni `LaboralStrategy`.
    """
    base = Decimal(str(base))
    porcentaje_estandar = Decimal(str(porcentaje_estandar))
    porcentaje_elevado = Decimal(str(porcentaje_elevado))
    if base < 0:
        raise ValueError("La base no puede ser negativa.")
    if porcentaje_estandar < 0 or porcentaje_elevado < 0:
        raise ValueError("El porcentaje no puede ser negativo.")

    porcentaje = porcentaje_elevado if aplica_porcentaje_elevado else porcentaje_estandar
    return Rounding.money(base * porcentaje / Decimal("100"))
