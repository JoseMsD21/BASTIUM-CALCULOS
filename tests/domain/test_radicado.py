import pytest

from app.domain.radicado import RadicadoInvalido, es_radicado_valido, parsear_radicado

# Huila/Neiva, circuito (31), civil (03), despacho 002, 2024, consecutivo 123, sin recurso
NEIVA = "41001310300220240012300"


def test_parsea_los_23_digitos_y_expone_cada_campo():
    r = parsear_radicado(NEIVA)
    assert (r.divipola, r.corporacion, r.especialidad, r.despacho) == ("41001", "31", "03", "002")
    assert (r.anio, r.consecutivo, r.recurso) == ("2024", "00123", "00")
    assert r.departamento == "41" and r.municipio == "001" and r.nombre_departamento == "Huila"
    assert r.compacto == NEIVA and str(r) == NEIVA
    assert r.formateado == "41001-31-03-002-2024-00123-00"


@pytest.mark.parametrize(
    "texto",
    [
        "41001-31-03-002-2024-00123-00",
        "41001 31 03 002 2024 00123 00",
        " 41001.31.03.002.2024.00123.00 ",
    ],
)
def test_acepta_separadores_y_los_normaliza(texto):
    assert parsear_radicado(texto).compacto == NEIVA


@pytest.mark.parametrize(
    ("texto", "fragmento"),
    [
        ("4100131030022024001230", "tiene 22"),  # 22
        ("410013103002202400123000", "tiene 24"),  # 24
        ("41001310300220240012A00", "solo admite dígitos"),
        ("00001310300220240012300", "departamento"),
        ("41000310300220240012300", "municipio"),
        ("41001310300220240000000", "consecutivo"),
        ("41001310300020240012300", "despacho"),
        ("41001310300218990012300", "Año"),
        ("", "tiene 0"),
    ],
)
def test_rechaza_con_mensaje_especifico(texto, fragmento):
    with pytest.raises(RadicadoInvalido, match=fragmento):
        parsear_radicado(texto)


def test_es_radicado_valido_no_lanza():
    assert es_radicado_valido(NEIVA) is True
    assert es_radicado_valido("2024-001") is False
    assert es_radicado_valido(None) is False  # type: ignore[arg-type]
