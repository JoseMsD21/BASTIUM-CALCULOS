import json
import urllib.error
from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest

from app.core.exceptions import TRMNoDisponibleError
from app.engine.currency.trm_provider import ManualTRMProvider, SFCTRMProvider, TRMProvider


def test_manual_trm_provider_retorna_el_valor_sembrado():
    provider = ManualTRMProvider(Decimal("4150.2500"))
    assert provider.get_trm(date(2025, 1, 1)) == Decimal("4150.2500")


def test_manual_trm_provider_retorna_el_mismo_valor_para_cualquier_fecha():
    provider = ManualTRMProvider(Decimal("4000.0000"))
    assert provider.get_trm(date(2020, 1, 1)) == Decimal("4000.0000")
    assert provider.get_trm(date(2026, 12, 31)) == Decimal("4000.0000")


def test_trm_provider_es_abstracto_no_se_puede_instanciar():
    with pytest.raises(TypeError):
        TRMProvider()


class _RespuestaFalsa:
    def __init__(self, payload: bytes):
        self._buffer = BytesIO(payload)

    def read(self):
        return self._buffer.read()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_sfc_trm_provider_parsea_el_valor_de_la_respuesta_json(monkeypatch):
    payload = json.dumps([{
        "valor": "4150.25", "unidad": "COP",
        "vigenciadesde": "2026-01-01T00:00:00.000", "vigenciahasta": "2026-01-01T00:00:00.000",
    }]).encode("utf-8")

    monkeypatch.setattr(
        "app.engine.currency.trm_provider.urllib.request.urlopen",
        lambda url, timeout: _RespuestaFalsa(payload),
    )

    provider = SFCTRMProvider()
    assert provider.get_trm(date(2026, 1, 1)) == Decimal("4150.25")


def test_sfc_trm_provider_lista_vacia_lanza_trm_no_disponible(monkeypatch):
    monkeypatch.setattr(
        "app.engine.currency.trm_provider.urllib.request.urlopen",
        lambda url, timeout: _RespuestaFalsa(b"[]"),
    )

    provider = SFCTRMProvider()
    with pytest.raises(TRMNoDisponibleError):
        provider.get_trm(date(2026, 1, 1))


def test_sfc_trm_provider_error_de_red_lanza_trm_no_disponible(monkeypatch):
    def _lanzar_error(url, timeout):
        raise urllib.error.URLError("sin conexion")

    monkeypatch.setattr("app.engine.currency.trm_provider.urllib.request.urlopen", _lanzar_error)

    provider = SFCTRMProvider()
    with pytest.raises(TRMNoDisponibleError):
        provider.get_trm(date(2026, 1, 1))
