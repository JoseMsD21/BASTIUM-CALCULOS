"""La politica Decimal debe valer en TODO hilo, no solo en el que importo la configuracion."""

import contextvars
import threading
from concurrent.futures import ThreadPoolExecutor
from decimal import ROUND_HALF_UP, Decimal, getcontext, localcontext

import config.decimal_config as cfg


def _redondeo_implicito() -> tuple[str, str]:
    # quantize SIN `rounding=`: depende del contexto del hilo (HALF_UP -> 0.13; HALF_EVEN -> 0.12).
    return str(Decimal("0.125").quantize(Decimal("0.01"))), str(getcontext().rounding)


def test_hilo_nuevo_hereda_half_up():
    salida = {}
    hilo = threading.Thread(target=lambda: salida.update(v=_redondeo_implicito()))
    hilo.start()
    hilo.join()
    assert salida["v"] == ("0.13", ROUND_HALF_UP)


def test_pool_de_hilos_hereda_half_up():
    with ThreadPoolExecutor(max_workers=4) as pool:
        resultados = list(pool.map(lambda _: _redondeo_implicito(), range(8)))
    assert all(r == ("0.13", ROUND_HALF_UP) for r in resultados)


def test_hilo_con_contextvars_copiados_sigue_en_half_up():
    # anyio/FastAPI ejecutan endpoints sync con copy_context().run en un hilo del pool.
    contexto = contextvars.copy_context()
    salida = {}
    hilo = threading.Thread(target=lambda: salida.update(v=contexto.run(_redondeo_implicito)))
    hilo.start()
    hilo.join()
    assert salida["v"] == ("0.13", ROUND_HALF_UP)


def test_contexto_forense_es_explicito_y_de_alta_precision():
    with localcontext(cfg.CONTEXTO_FORENSE):
        assert getcontext().prec == 50
        assert getcontext().rounding == ROUND_HALF_UP
        assert Decimal(1) / Decimal(7) == Decimal(
            "0.14285714285714285714285714285714285714285714285714"
        )


def test_aplicar_politica_global_es_idempotente():
    cfg.aplicar_politica_global()
    cfg.aplicar_politica_global()
    assert getcontext().prec == 28 and getcontext().rounding == ROUND_HALF_UP
