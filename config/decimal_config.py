"""
Politica global de precision y redondeo Decimal de BASTIUM.

NUNCA utilizar float para calculos financieros.

Hallazgo de auditoria (2026-11-12): el modulo `decimal` guarda su contexto POR HILO.
Antes, este modulo solo fijaba el contexto del hilo que lo importaba (el principal);
cualquier hilo creado despues (hilos de trabajo de FastAPI/anyio, QThread de la app de
escritorio, ThreadPoolExecutor) arrancaba con `decimal.DefaultContext`, es decir, con
ROUND_HALF_EVEN. Ejemplo medido: `Decimal("0.125").quantize(Decimal("0.01"))` daba 0.13
en el hilo principal y 0.12 en un hilo de trabajo. El codigo del motor siempre pasa
`rounding=ROUND_HALF_UP` de forma explicita, asi que el dinero ya estaba protegido, pero
cualquier operacion implicita (quantize sin rounding, `round()`, `to_integral_value`)
cambiaba de resultado segun el hilo. Se corrige en dos capas:

1. `DefaultContext` -- plantilla de todo hilo nuevo -- recibe la misma politica.
2. `CONTEXTO_FORENSE` -- contexto explicito de alta precision para la capa API y para la
   causacion exacta (`PoliticaCausacion.EXACTA_POR_PERIODO`): se activa con
   `localcontext(CONTEXTO_FORENSE)`, de modo que el resultado no depende del hilo ni del
   estado global del proceso.
"""

import decimal
from decimal import (
    ROUND_HALF_UP,
    Context,
    DivisionByZero,
    InvalidOperation,
    Overflow,
    getcontext,
    setcontext,
)

PRECISION_LEGADA = 28
PRECISION_FORENSE = 50

CONTEXTO_FORENSE = Context(
    prec=PRECISION_FORENSE,
    rounding=ROUND_HALF_UP,
    Emin=-999_999,
    Emax=999_999,
    capitals=1,
    clamp=0,
    flags=[],
    traps=[InvalidOperation, DivisionByZero, Overflow],
)


def aplicar_politica_global() -> None:
    """Fija la politica en el hilo actual Y en la plantilla de hilos futuros. Idempotente."""
    contexto_actual = getcontext()
    contexto_actual.prec = PRECISION_LEGADA
    contexto_actual.rounding = ROUND_HALF_UP
    plantilla = decimal.DefaultContext
    plantilla.prec = PRECISION_LEGADA
    plantilla.rounding = ROUND_HALF_UP
    # Reasignar el contexto actual garantiza que el cambio quede registrado en la
    # ContextVar interna del hilo que importa este modulo.
    setcontext(contexto_actual)


aplicar_politica_global()
