from app.reports.header import build_encabezado


def test_build_encabezado_incluye_radicado_partes_y_juzgado():
    encabezado = build_encabezado("2026-030", "Ana", "Luis", "Juzgado 5 Civil del Circuito")

    assert encabezado == {
        "radicado": "2026-030",
        "partes": "Ana vs. Luis",
        "juzgado": "Juzgado 5 Civil del Circuito",
    }


def test_build_encabezado_sin_juzgado_queda_en_none():
    encabezado = build_encabezado("2026-030", "Ana", "Luis", None)

    assert encabezado["juzgado"] is None
    assert encabezado["partes"] == "Ana vs. Luis"
