"""Vista de sensibilidad "Ver con/sin indexación" (Sprint 107).

Respuesta del despacho (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 107):
implementacion hibrida. El checkbox de `ObligacionFormDialog` sigue fijando la
intencion juridica sustancial en la base de datos, y ADEMAS la pantalla de
resultados ofrece un interruptor de presentacion que recalcula la vista en tiempo
real (analisis de sensibilidad o debate pedagogico ante el juez) SIN alterar el
dato guardado de la obligacion.

Garantias de este modulo:

- Nunca escribe en la base de datos: no llama a `registrar_liquidacion` (el
  AuditLog solo guarda liquidaciones oficiales) ni hace `commit` de nada.
- Las obligaciones se cargan con una sesion propia que se cierra ANTES de liquidar
  (instancias detached) y ademas se envuelven en `ObligacionVistaSensibilidad`, un
  proxy de solo lectura que sobrescribe unicamente `aplica_indexacion_ipc` e
  `interes_sobre_capital_indexado` -- las instancias ORM originales nunca se
  modifican, asi que no hay cambio pendiente que un flush posterior pudiera
  persistir por accidente.
- Reutiliza exactamente la misma `AreaStrategy` (y por lo tanto el mismo
  `UniversalLiquidationService`) que la liquidacion oficial: no duplica ninguna
  regla de indexacion.

Semantica del interruptor (aplica a TODAS las obligaciones del expediente):

- Sin indexacion: `aplica_indexacion_ipc = False` e
  `interes_sobre_capital_indexado = False` (sin capital indexado no hay interes
  sobre capital indexado / Suma Unica).
- Con indexacion: `aplica_indexacion_ipc = True`; `interes_sobre_capital_indexado`
  conserva el valor guardado de cada obligacion (Suma Unica es una eleccion
  juridica distinta, Sprint 20, que el despacho no pidio forzar). Las validaciones
  propias de cada area se aplican igual que en la liquidacion oficial (ej.
  Comercial exige "Pacto expreso de indexación en el título"); si alguna falla, la
  vista de sensibilidad no se puede calcular y el error se informa tal cual.
"""

from datetime import date
from typing import Any

import database.session as session_module
from app.engine.liquidation.registry import AreaRegistry
from app.engine.liquidation.result import LiquidationResult
from database.models import Expediente


class ObligacionVistaSensibilidad:
    """Proxy de solo lectura sobre una `Obligacion` (detached) que sobrescribe las
    dos banderas de indexacion y delega cualquier otro atributo al original."""

    __slots__ = ("_original", "aplica_indexacion_ipc", "interes_sobre_capital_indexado")

    def __init__(
        self,
        original: Any,
        aplica_indexacion_ipc: bool,
        interes_sobre_capital_indexado: bool,
    ) -> None:
        object.__setattr__(self, "_original", original)
        object.__setattr__(self, "aplica_indexacion_ipc", aplica_indexacion_ipc)
        object.__setattr__(
            self, "interes_sobre_capital_indexado", interes_sobre_capital_indexado
        )

    def __getattr__(self, nombre: str) -> Any:
        return getattr(self._original, nombre)

    def __setattr__(self, nombre: str, valor: Any) -> None:
        raise AttributeError(
            "ObligacionVistaSensibilidad es de solo lectura: la vista de sensibilidad "
            "no puede modificar la obligacion."
        )


def obligaciones_para_vista_sensibilidad(
    obligaciones: list, con_indexacion: bool
) -> list[ObligacionVistaSensibilidad]:
    """Envuelve cada obligacion con las banderas de indexacion de la vista pedida
    (ver docstring del modulo)."""
    return [
        ObligacionVistaSensibilidad(
            obligacion,
            aplica_indexacion_ipc=con_indexacion,
            interes_sobre_capital_indexado=(
                bool(obligacion.interes_sobre_capital_indexado) if con_indexacion else False
            ),
        )
        for obligacion in obligaciones
    ]


def cargar_datos_de_liquidacion(expediente_id: int) -> tuple[list, list, str]:
    """Carga (obligaciones, abonos, area) de un expediente con una sesion propia y
    la cierra antes de retornar: las instancias quedan detached, con sus
    relaciones ya cargadas. Compartido con la liquidacion oficial
    (`app/views/expediente_detalle.py::_liquidar_en_hilo_de_fondo`)."""
    session = session_module.get_session()
    try:
        expediente = session.get(Expediente, expediente_id)
        obligaciones = list(expediente.obligaciones)
        abonos = [abono for obligacion in obligaciones for abono in obligacion.abonos]
        for obligacion in obligaciones:
            list(obligacion.eventos_laborales)  # fuerza el lazy-load antes de session.close()
            list(obligacion.descuentos_laborales)  # idem (Sprint 44, punto 3)
            # idem (Sprint 74): CivilFamiliaStrategy lee obligacion.beneficiario para
            # topar la vigencia de las cuotas RECURRENTE.
            _ = obligacion.beneficiario
        area = expediente.area_derecho.value
    finally:
        session.close()
    return obligaciones, abonos, area


def liquidar_vista_sensibilidad(
    expediente_id: int, fecha_corte: date, con_indexacion: bool
) -> LiquidationResult:
    """Recalcula en memoria la liquidacion del expediente con la indexacion IPC
    activada o desactivada para todas sus obligaciones. No escribe nada en la base
    de datos (ni obligaciones ni AuditLog)."""
    obligaciones, abonos, area = cargar_datos_de_liquidacion(expediente_id)
    estrategia = AreaRegistry.get_strategy(area)
    return estrategia.liquidar(
        obligaciones=obligaciones_para_vista_sensibilidad(obligaciones, con_indexacion),
        abonos=abonos,
        fecha_corte=fecha_corte,
    )
