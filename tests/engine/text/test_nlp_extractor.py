from datetime import date
from decimal import Decimal

import pytest

from app.core.exceptions import DatoFaltanteError
from app.engine.text.nlp_extractor import LegalTextExtractor


def test_extract_facts_encuentra_capital_y_fecha():
    extractor = LegalTextExtractor()
    texto = "El deudor debe $ 5.000.000 desde el 15/03/2020."

    facts = extractor.extract_facts(texto)

    assert facts["capital"] == Decimal("5000000")
    assert facts["fecha_exigibilidad"] == date(2020, 3, 15)


def test_validate_and_fill_no_llama_prompt_fn_si_los_hechos_ya_estan_completos():
    extractor = LegalTextExtractor()
    facts = {"capital": Decimal("5000000"), "fecha_exigibilidad": date(2020, 3, 15)}

    def prompt_fn_que_no_deberia_llamarse(mensaje):
        raise AssertionError("No deberia pedirse nada si los hechos ya estan completos")

    resultado = extractor.validate_and_fill(facts, prompt_fn=prompt_fn_que_no_deberia_llamarse)

    assert resultado is facts


def test_validate_and_fill_usa_el_prompt_fn_inyectado_para_completar_datos_faltantes():
    extractor = LegalTextExtractor()
    facts = {"capital": None, "fecha_exigibilidad": None}
    respuestas = iter(["5.000.000", "15/03/2020"])

    resultado = extractor.validate_and_fill(facts, prompt_fn=lambda mensaje: next(respuestas))

    assert resultado["capital"] == Decimal("5000000")
    assert resultado["fecha_exigibilidad"] == date(2020, 3, 15)


def test_validate_and_fill_sin_prompt_fn_y_sin_stdin_interactivo_lanza_error_en_vez_de_bloquear(
    monkeypatch,
):
    from app.engine.text import nlp_extractor

    monkeypatch.setattr(nlp_extractor.sys.stdin, "isatty", lambda: False)
    extractor = LegalTextExtractor()
    facts = {"capital": None, "fecha_exigibilidad": None}

    with pytest.raises(DatoFaltanteError):
        extractor.validate_and_fill(facts)


def test_validate_and_fill_default_usa_rich_prompt_cuando_hay_stdin_interactivo(monkeypatch):
    from app.engine.text import nlp_extractor

    monkeypatch.setattr(nlp_extractor.sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(nlp_extractor.Prompt, "ask", lambda mensaje: "5.000.000")

    extractor = LegalTextExtractor()
    facts = {"capital": None, "fecha_exigibilidad": date(2020, 3, 15)}

    resultado = extractor.validate_and_fill(facts)

    assert resultado["capital"] == Decimal("5000000")
