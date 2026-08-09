from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

from app.core.exceptions import CuotaLitisExcedeTopeError
from app.domain.obligation.payment import Payment
from app.engine.costs.agencias_en_derecho import (
    Instancia,
    TipoProceso,
    calcular_agencias_en_derecho,
    validar_costas_pct_manual,
)
from app.engine.currency.converter import convertir_a_pesos
from app.engine.currency.trm_provider import ManualTRMProvider, SFCTRMProvider, TRMProvider
from app.engine.financial.rate import Rate
from app.engine.indexation.historical_index import get_ipc_interpolado_for_date, get_smlmv_for_year
from app.engine.indexation.ipc import IPCIndexation
from app.engine.indexation.smlmv_to_uvt import resolver_base_sancion
from app.engine.interest.provider import MemoryRateProvider
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.engine.interest.usury_validator import calcular_tope_usura
from app.engine.labor.incapacidad import IncapacidadCalculator
from app.engine.labor.moratory_indemnity import MoratoryIndemnityCalculator
from app.engine.labor.seguridad_social import SeguridadSocialCalculator
from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.engine.tax.actualizacion_867_1 import (
    aplica_actualizacion_867_1,
    calcular_indexacion_867_1,
    calcular_indexacion_867_1_topada,
)
from app.engine.tax.moratory_interest import (
    calcular_interes_moratorio_tributario,
    construir_rate_provider_moratorio_tributario,
)
from app.engine.tax.renta_liquida import depurar_renta_liquida_gravable
from app.engine.tax.sanciones import (
    calcular_sancion_error_aritmetico,
    calcular_sancion_extemporaneidad,
    calcular_sancion_inexactitud,
)
from app.engine.temporal.schedulers.base import Event
from app.engine.temporal.schedulers.family import FamilyScheduler
from app.engine.temporal.schedulers.labor import LaborScheduler
from app.engine.time.calendar import CalendarUtils
from app.services.motor_universal import UniversalLiquidationService
from app.services.parametro_service import cache_de_liquidacion, get_parametro


def _evento_costas_procesales(obligacion, pretensiones_reconocidas: Decimal) -> Event | None:
    """Costas procesales (agencias en derecho) para cualquier area de litigio
    judicial. costas_pct_manual (Sprint 4) tiene siempre prioridad sobre el
    calculo automatico del Acuerdo PSAA16-10554 (Sprint 18) -- si el auto
    judicial real ya fijo un porcentaje, ese manda, pero desde la correccion
    del Sprint 18 (2026-08-01) ese porcentaje manual se valida contra el rango
    permitido por cuantia (respuesta del despacho) y se RECHAZA (no se trunca)
    si esta fuera de rango -- ver validar_costas_pct_manual. Retorna None si la
    obligacion no tiene ninguno de los dos mecanismos activado (comportamiento
    identico al de antes de este sprint)."""
    if obligacion.costas_pct_manual is not None:
        validar_costas_pct_manual(
            obligacion.costas_pct_manual, pretensiones_reconocidas, obligacion.fecha_origen,
        )
        costas_monto = pretensiones_reconocidas * obligacion.costas_pct_manual / Decimal("100")
    elif obligacion.costas_tipo_proceso is not None and obligacion.costas_instancia is not None:
        costas_monto = calcular_agencias_en_derecho(
            tipo_proceso=TipoProceso(obligacion.costas_tipo_proceso),
            instancia=Instancia(obligacion.costas_instancia),
            pretensiones_reconocidas=pretensiones_reconocidas,
            fecha_radicacion=obligacion.fecha_origen,
        )
    else:
        return None

    return Event(
        date=obligacion.fecha_origen,
        payload={"amount": costas_monto, "label": f"Costas procesales - {obligacion.concepto}"},
        event_type="COSTAS_PROCESALES",
    )


def _liquidar_por_obligacion(
    obligaciones: list,
    abonos: list,
    fecha_corte: date,
    eventos_fn: Callable[[object], list[Event]],
    rate_provider_fn: Callable[[object, date], MemoryRateProvider],
    usar_suma_unica_fn: Callable[[object], bool] = lambda obligacion: False,
    monto_abono_fn: Callable[[object, object], Decimal] = lambda obligacion, abono: abono.monto,
) -> LiquidationResult:
    """Corre un LiquidationCore independiente por obligacion -- cada una con su propia
    tasa (via rate_provider_fn) y solo sus propios abonos (Abono.obligacion_id) -- y
    fusiona los historiales en una sola linea de tiempo consolidada para el reporte del
    expediente. Ver docs/superpowers/specs/2026-07-31-sprint21-multiples-tasas-design.md
    (Sprint 21): LiquidationCore mantiene un solo PendingDebt agregado por instancia, asi
    que la unica forma de que dos obligaciones acumulen interes a tasas distintas
    simultaneamente es correrlas en instancias separadas.

    usar_suma_unica_fn (Sprint 20, adaptado al Sprint 21): resuelve, por obligacion, si
    esa liquidacion individual debe usar el algoritmo "Suma Única" (interes sobre capital
    ya indexado). Default `False` para toda area que no lo soporte -- solo
    CivilFamiliaStrategy pasa una funcion real. Como cada obligacion ya corre en su propio
    LiquidationCore aislado, el criterio no necesita ser consistente entre obligaciones del
    mismo expediente.

    monto_abono_fn (Sprint 12, correccion 2026-08-01): resuelve el monto de cada abono
    antes de aplicarlo -- identidad por defecto (mismo comportamiento de siempre). Solo
    ComercialStrategy pasa una funcion real, para convertir a pesos con la TRM dinamica
    de la fecha de CADA abono (ver ComercialStrategy._monto_abono_en_pesos)."""
    ids_obligaciones = {obligacion.id for obligacion in obligaciones}
    for abono in abonos:
        if abono.obligacion_id not in ids_obligaciones:
            raise ValueError(
                f"El abono '{abono.referencia or abono.id}' (obligacion_id={abono.obligacion_id}) "
                f"no corresponde a ninguna obligacion de este expediente."
            )

    resultados = []
    for obligacion in obligaciones:
        abonos_obligacion = [abono for abono in abonos if abono.obligacion_id == obligacion.id]
        pagos = [
            Payment(
                date=abono.fecha, amount=monto_abono_fn(obligacion, abono),
                reference=abono.referencia or "",
            )
            for abono in abonos_obligacion
        ]
        service = UniversalLiquidationService()
        resultados.append(service.liquidar(
            eventos_causacion=eventos_fn(obligacion),
            pagos=pagos,
            fecha_corte=fecha_corte,
            rate_provider=rate_provider_fn(obligacion, fecha_corte),
            usar_suma_unica=usar_suma_unica_fn(obligacion),
        ))

    return _fusionar_resultados(resultados, fecha_corte)


def _fusionar_resultados(resultados: list[LiquidationResult], fecha_corte: date) -> LiquidationResult:
    """Intercala los items de N LiquidationResult (uno por obligacion) en una sola linea
    de tiempo cronologica, recalculando el saldo consolidado del expediente en cada fila.
    Colapsa a la identidad cuando hay una sola obligacion (garantiza que los expedientes
    de una sola obligacion no cambien de resultado)."""
    if len(resultados) == 1:
        return resultados[0]

    filas_regulares = []
    for indice_obligacion, resultado in enumerate(resultados):
        for posicion, item in enumerate(resultado.items):
            if item.balance.event_type == "LIQUIDATION_CUTOFF":
                continue
            filas_regulares.append((item.date, indice_obligacion, posicion, item))
    # Empate de fecha -> orden de la obligacion en la lista recibida, luego orden de
    # emision original dentro de esa obligacion (determinista, sort() es estable).
    filas_regulares.sort(key=lambda fila: (fila[0], fila[1], fila[2]))

    saldo_cero = PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
    ultimo_estado = {indice: saldo_cero for indice in range(len(resultados))}
    items_fusionados: list[LiquidationItem] = []
    for _fecha, indice_obligacion, _posicion, item in filas_regulares:
        ultimo_estado[indice_obligacion] = item.balance.debt
        saldo_consolidado = PendingDebt(
            principal=sum((estado.principal for estado in ultimo_estado.values()), Decimal("0.00")),
            interest=sum((estado.interest for estado in ultimo_estado.values()), Decimal("0.00")),
            indexation=sum((estado.indexation for estado in ultimo_estado.values()), Decimal("0.00")),
        )
        items_fusionados.append(replace(
            item,
            capital_base=saldo_consolidado.principal,
            balance=RunningBalance(
                date=item.date, debt=saldo_consolidado, event_type=item.balance.event_type
            ),
        ))

    # Misma condicion que usa LiquidationCore.process() para agregar su propia fila de
    # cierre (last_event_date < cutoff_date): si al menos una obligacion la disparo, se
    # sintetiza una sola fila de cierre consolidada en vez de N filas individuales.
    hubo_cierre = any(
        any(item.balance.event_type == "LIQUIDATION_CUTOFF" for item in resultado.items)
        for resultado in resultados
    )
    if hubo_cierre:
        saldo_final = PendingDebt(
            principal=sum((r.final_balance().principal for r in resultados), Decimal("0.00")),
            interest=sum((r.final_balance().interest for r in resultados), Decimal("0.00")),
            indexation=sum((r.final_balance().indexation for r in resultados), Decimal("0.00")),
        )
        items_fusionados.append(LiquidationItem(
            date=fecha_corte,
            concept="Corte final de liquidación",
            capital_base=saldo_final.principal,
            interest_rate=Decimal("0.00"),
            interest_amount=Decimal("0.00"),
            indexation_amount=Decimal("0.00"),
            payment_amount=Decimal("0.00"),
            balance=RunningBalance(date=fecha_corte, debt=saldo_final, event_type="LIQUIDATION_CUTOFF"),
            rate_source="Varias tasas — ver detalle por fila arriba",
        ))

    return LiquidationResult(items_fusionados)


class AreaStrategy(ABC):
    """Contrato comun para el calculo de liquidacion por area del derecho."""

    soporta_indexacion_ipc: bool = True

    @abstractmethod
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
        raise NotImplementedError

    @staticmethod
    def _rate_provider_tasa_plana(
        fecha_inicio: date, fecha_corte: date, tasa_efectiva_anual: Decimal, source: str = "N/A"
    ) -> MemoryRateProvider:
        """Un solo tramo de tasa diaria plana desde `fecha_inicio` hasta `fecha_corte` --
        patron compartido por Sancionatorio, Honorarios y Civil/Familia (Sprint 22,
        deduplicacion de `_construir_rate_provider_obligacion`)."""
        tasa_diaria = EffectiveRateConverter.annual_to_daily(tasa_efectiva_anual)
        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_inicio - timedelta(days=1), end=fecha_corte, rate=tasa_diaria, source=source,
        )
        return provider


class CivilFamiliaStrategy(AreaStrategy):
    """
    Unica area operable en el MVP original; ahora tambien soporta indexacion IPC
    opcional por obligacion (Sprint 8). Interes fijo por obligacion (tasa
    efectiva anual pactada/legal, Art. 1617 C.C.), convertido a tasa diaria.
    Indexacion (Art. corrección monetaria, PDF pag. 20-22): solo se activa por
    obligacion via `aplica_indexacion_ipc` -- es un juicio legal del abogado, no
    una regla automatica por categoria. La regla "no doble indexacion" del PDF
    (incompatible con SMMLV ya actualizado) no requiere un guard en tiempo de
    ejecucion: ningun campo de Obligacion usado por Civil/Familia representa un
    valor ya anclado a SMMLV (eso es exclusivo de Sancionatorio, que ya tiene
    soporta_indexacion_ipc=False), asi que la combinacion que la regla prohibe
    no es alcanzable con el modelo de datos actual.
    """

    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        return _liquidar_por_obligacion(
            obligaciones=obligaciones,
            abonos=abonos,
            fecha_corte=fecha_corte,
            eventos_fn=lambda obligacion: self._eventos_de_obligacion(obligacion, fecha_corte),
            rate_provider_fn=self._construir_rate_provider_obligacion,
            usar_suma_unica_fn=self._resolver_suma_unica,
        )

    def _resolver_suma_unica(self, obligacion) -> bool:
        """Determina si esta obligacion liquida con el algoritmo "Suma Única"
        (interes sobre capital ya indexado, PDF pag. 21-22, incluye la variante
        Ley 80/1993 para contratos estatales -- misma mecanica, sin campo
        propio) en vez del legado (interes solo sobre capital historico).
        Desde el Sprint 21, cada obligacion corre en su propio LiquidationCore
        (PendingDebt independiente, ver _liquidar_por_obligacion) -- ya no hay
        un unico saldo compartido a nivel de expediente, asi que el criterio
        puede variar libremente obligacion por obligacion sin ambiguedad; no
        hace falta validar consistencia entre obligaciones (a diferencia de la
        version original de este metodo, escrita antes del Sprint 21)."""
        return bool(obligacion.aplica_indexacion_ipc) and bool(obligacion.interes_sobre_capital_indexado)

    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> list[Event]:
        if obligacion.tipo.value == "PUNTUAL":
            eventos = [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": obligacion.valor, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]
            if obligacion.aplica_indexacion_ipc:
                eventos.append(
                    self._evento_indexacion(
                        fecha_causacion=obligacion.fecha_origen,
                        capital=obligacion.valor,
                        concepto=obligacion.concepto,
                        fecha_corte=fecha_corte,
                    )
                )
            evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=obligacion.valor)
            if evento_costas is not None:
                eventos.append(evento_costas)
            return eventos

        # RECURRENTE
        scheduler = FamilyScheduler()
        scheduler.add_monthly_obligation(
            amount=obligacion.valor,
            concept=obligacion.concepto,
            due_day=obligacion.dia_pago,
            category=obligacion.categoria,
        )
        fin = obligacion.fecha_fin or fecha_corte
        eventos_capital = scheduler.generate(start=obligacion.fecha_inicio, end=fin)

        if not obligacion.aplica_indexacion_ipc:
            return eventos_capital

        eventos = list(eventos_capital)
        for cuota in eventos_capital:
            eventos.append(
                self._evento_indexacion(
                    fecha_causacion=cuota.date,
                    capital=cuota.payload["amount"],
                    concepto=obligacion.concepto,
                    fecha_corte=fecha_corte,
                )
            )
        return eventos

    def _evento_indexacion(
        self, fecha_causacion: date, capital: Decimal, concepto: str, fecha_corte: date
    ) -> Event:
        monto = IPCIndexation.calculate(
            capital=capital,
            initial_index=get_ipc_interpolado_for_date(fecha_causacion),
            final_index=get_ipc_interpolado_for_date(fecha_corte),
        )
        return Event(
            date=fecha_causacion,
            payload={"amount": monto, "label": f"Indexación IPC — {concepto}"},
            event_type="INDEXATION",
        )

    def _construir_rate_provider_obligacion(self, obligacion, fecha_corte: date) -> MemoryRateProvider:
        fecha_inicio = (
            obligacion.fecha_origen if obligacion.tipo.value == "PUNTUAL" else obligacion.fecha_inicio
        )
        return self._rate_provider_tasa_plana(
            fecha_inicio, fecha_corte, obligacion.tasa_efectiva_anual,
            source="Tasa pactada en la obligación (Art. 1617 C.C.)",
        )


class ComercialStrategy(AreaStrategy):
    """
    Area Comercial (Art. 884 C.Co.). Cada obligacion debe traer su propia tasa
    remuneratoria (tasa_efectiva_anual), tasa moratoria (tasa_moratoria_anual),
    fecha de vencimiento y el IBC vigente aplicable (ibc_vigente_anual) -- no hay
    fallback automatico a un IBC de referencia en este sprint (ver Pendientes.md,
    Sprint 2 y Sprint 5).

    Split real de tasa remuneratoria (antes del vencimiento) / moratoria (despues)
    solo aplica a obligaciones PUNTUAL. RECURRENTE usa una sola tasa moratoria para
    todo el periodo, igual que CivilFamiliaStrategy, porque el vencimiento de cada
    cuota individual no esta modelado (ver docs/superpowers/specs/2026-07-15-area-comercial-design.md).

    No es compatible con indexacion IPC (soporta_indexacion_ipc = False).

    TRM (Sprint 12, correccion 2026-08-01): respuesta del despacho -- "eliminar
    la logica de TRM congelada al inicio". Por defecto, cada obligacion en
    moneda extranjera se convierte a pesos con la TRM certificada por la
    Superintendencia Financiera EN LA FECHA DE CADA EVENTO (capital: fecha de
    origen; cada abono: su propia fecha de pago), consultada en vivo via
    `SFCTRMProvider`. Si la obligacion trae `trm_aplicable` seteado (flujo
    manual anterior a este sprint, conservado por compatibilidad y como
    respaldo si la API no responde), esa obligacion usa ese valor fijo para
    todo en vez de la API -- es la unica TRM "congelada" que sobrevive, y es
    una eleccion explicita del abogado por obligacion, no el comportamiento
    por defecto.
    """

    soporta_indexacion_ipc = False

    def __init__(self, trm_provider: TRMProvider | None = None):
        self._trm_provider_default = trm_provider or SFCTRMProvider()

    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_comercial(obligacion)

        resultado = _liquidar_por_obligacion(
            obligaciones=obligaciones,
            abonos=abonos,
            fecha_corte=fecha_corte,
            eventos_fn=lambda obligacion: self._eventos_de_obligacion(obligacion, fecha_corte),
            rate_provider_fn=self._construir_rate_provider_obligacion,
            monto_abono_fn=self._monto_abono_en_pesos,
        )

        ajustes_usura = []
        for obligacion in obligaciones:
            abonos_obligacion = [abono for abono in abonos if abono.obligacion_id == obligacion.id]
            ajuste = self._calcular_sancion_usura(obligacion, abonos_obligacion, fecha_corte)
            if ajuste is not None:
                ajustes_usura.append(ajuste)

        if ajustes_usura:
            resultado = self._aplicar_sanciones_usura(resultado, ajustes_usura, fecha_corte)

        return resultado

    def _calcular_sancion_usura(self, obligacion, abonos: list, fecha_corte: date) -> dict | None:
        """Respuesta del despacho (Preguntas-Para-Abogado.md, Sprint 2): una tasa
        pactada por encima de la usura NO se rechaza ni se recorta silenciosamente.
        Se liquida con la tasa realmente pactada y, aparte, se calcula:
          Intereses_Cobrados_En_Exceso = Intereses_Cobrados - Intereses_Cobrados_Con_Tasa_Usura
          Sancion = Intereses_Cobrados_En_Exceso x 2
        restando la sancion del saldo total (puede dejar saldo a favor del deudor).

        "Intereses_Cobrados_Con_Tasa_Usura" se obtiene corriendo la misma obligacion
        (mismos eventos, mismos abonos) por el motor con las tasas que excedan el tope
        recortadas a ese tope -- una liquidacion sombra que nunca se devuelve al
        usuario, solo se usa como referencia de cuanto interes habria causado la tasa
        legal. Retorna None si ninguna de las dos tasas (remuneratoria/moratoria)
        excede el tope."""
        tope = calcular_tope_usura(obligacion.ibc_vigente_anual, obligacion.fecha_origen)
        if obligacion.tasa_efectiva_anual <= tope and obligacion.tasa_moratoria_anual <= tope:
            return None

        eventos = self._eventos_de_obligacion(obligacion, fecha_corte)
        pagos = [
            Payment(
                date=abono.fecha, amount=self._monto_abono_en_pesos(obligacion, abono),
                reference=abono.referencia or "",
            )
            for abono in abonos
        ]

        intereses_cobrados = UniversalLiquidationService().liquidar(
            eventos_causacion=eventos,
            pagos=pagos,
            fecha_corte=fecha_corte,
            rate_provider=self._construir_rate_provider_obligacion(obligacion, fecha_corte),
        ).final_balance().interest

        intereses_con_tasa_usura = UniversalLiquidationService().liquidar(
            eventos_causacion=eventos,
            pagos=pagos,
            fecha_corte=fecha_corte,
            rate_provider=self._construir_rate_provider_obligacion(obligacion, fecha_corte, tope=tope),
        ).final_balance().interest

        exceso = intereses_cobrados - intereses_con_tasa_usura
        return {
            "obligacion": obligacion,
            "exceso": exceso,
            "sancion": exceso * Decimal("2"),
            "tope": tope,
        }

    def _aplicar_sanciones_usura(
        self, resultado: LiquidationResult, ajustes: list[dict], fecha_corte: date
    ) -> LiquidationResult:
        items = list(resultado.items)
        saldo = resultado.final_balance()
        for ajuste in ajustes:
            saldo = PendingDebt(
                principal=saldo.principal,
                interest=saldo.interest - ajuste["sancion"],
                indexation=saldo.indexation,
            )
            items.append(LiquidationItem(
                date=fecha_corte,
                concept=(
                    f"Sanción por usura (Art. 72 Ley 45/1990) — {ajuste['obligacion'].concepto}: "
                    f"exceso cobrado {ajuste['exceso']} x 2, devuelto doblado al deudor"
                ),
                capital_base=saldo.principal,
                interest_rate=Decimal("0.00"),
                interest_amount=-ajuste["sancion"],
                indexation_amount=Decimal("0.00"),
                payment_amount=Decimal("0.00"),
                balance=RunningBalance(date=fecha_corte, debt=saldo, event_type="SANCION_USURA"),
                rate_source=f"Tope de usura vigente: {ajuste['tope']}% (Ley 45/1990 art. 72)",
            ))
        return LiquidationResult(items, renta_liquida=resultado.renta_liquida)

    def _validar_obligacion_comercial(self, obligacion) -> None:
        campos_requeridos = {
            "tasa_efectiva_anual": obligacion.tasa_efectiva_anual,
            "tasa_moratoria_anual": obligacion.tasa_moratoria_anual,
            "fecha_vencimiento": obligacion.fecha_vencimiento,
            "ibc_vigente_anual": obligacion.ibc_vigente_anual,
        }
        for nombre_campo, valor in campos_requeridos.items():
            if valor is None:
                raise ValueError(
                    f"La obligacion comercial '{obligacion.concepto}' necesita el campo "
                    f"'{nombre_campo}' para liquidar."
                )

        if obligacion.fecha_vencimiento < obligacion.fecha_origen:
            raise ValueError(
                f"La obligacion comercial '{obligacion.concepto}' tiene fecha_vencimiento "
                f"({obligacion.fecha_vencimiento}) anterior a fecha_origen ({obligacion.fecha_origen})."
            )

        # Una tasa pactada por encima del tope de usura ya NO se rechaza aqui (ver
        # respuesta del despacho, Preguntas-Para-Abogado.md Sprint 2): se liquida
        # igual y la sancion legal (perdida del exceso, doblado) se calcula y resta
        # del saldo en liquidar() -> _calcular_sancion_usura/_aplicar_sanciones_usura.

        # trm_aplicable/trm_fecha_referencia ya NO son obligatorios (Sprint 12,
        # correccion 2026-08-01): por defecto la TRM se consulta en vivo, por fecha,
        # via SFCTRMProvider -- ver docstring de la clase. trm_aplicable sigue siendo
        # una anulacion manual valida si el abogado la aporta, pero debe ser positiva.
        if obligacion.moneda not in (None, "COP") and obligacion.trm_aplicable is not None:
            if obligacion.trm_aplicable <= 0:
                raise ValueError(
                    f"La obligacion comercial '{obligacion.concepto}' tiene 'trm_aplicable' "
                    f"({obligacion.trm_aplicable}) que no es un valor positivo."
                )

        if obligacion.anatocismo_demanda_judicial and obligacion.anatocismo_fecha_acuerdo is not None:
            raise ValueError(
                f"La obligacion comercial '{obligacion.concepto}' no puede tener "
                f"'anatocismo_demanda_judicial' y 'anatocismo_fecha_acuerdo' activos a la vez "
                f"(son dos vias habilitantes excluyentes del Art. 886 C.Co.)."
            )

        anatocismo_activo = (
            obligacion.anatocismo_demanda_judicial or obligacion.anatocismo_fecha_acuerdo is not None
        )
        if anatocismo_activo and obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion comercial '{obligacion.concepto}' tiene anatocismo activo, pero "
                f"el anatocismo solo aplica a obligaciones PUNTUAL (RECURRENTE no modela un "
                f"vencimiento por cuota individual)."
            )

        if obligacion.anatocismo_fecha_acuerdo is not None:
            fecha_minima_acuerdo = obligacion.fecha_vencimiento + timedelta(days=365)
            if obligacion.anatocismo_fecha_acuerdo < fecha_minima_acuerdo:
                raise ValueError(
                    f"La obligacion comercial '{obligacion.concepto}' tiene 'anatocismo_fecha_acuerdo' "
                    f"({obligacion.anatocismo_fecha_acuerdo}) que no cumple el año de anterioridad "
                    f"exigido por el Art. 886 C.Co. (debe ser >= {fecha_minima_acuerdo})."
                )

    def _resolver_trm_provider(self, obligacion) -> TRMProvider:
        """`trm_aplicable` (si el abogado lo diligencio) es una anulacion manual
        fija para TODOS los eventos de esa obligacion -- comportamiento anterior
        a este sprint, conservado por compatibilidad. Sin esa anulacion, se usa
        el proveedor en vivo (SFCTRMProvider por defecto), consultado por fecha
        en cada llamada -- ver docstring de la clase."""
        if obligacion.trm_aplicable is not None:
            return ManualTRMProvider(obligacion.trm_aplicable)
        return self._trm_provider_default

    def _valor_en_pesos_en_fecha(self, valor: Decimal, obligacion, fecha: date) -> Decimal:
        return convertir_a_pesos(
            valor=valor,
            moneda=obligacion.moneda,
            provider=self._resolver_trm_provider(obligacion),
            fecha_referencia=fecha,
        )

    def _valor_en_pesos(self, obligacion) -> Decimal:
        return self._valor_en_pesos_en_fecha(obligacion.valor, obligacion, obligacion.fecha_origen)

    def _monto_abono_en_pesos(self, obligacion, abono) -> Decimal:
        """Respuesta del despacho (Sprint 12, correccion 2026-08-01): "eliminar
        la logica de TRM congelada al inicio" -- cada abono se convierte con la
        TRM vigente en SU PROPIA fecha de pago, no con la del origen de la
        obligacion. Para obligaciones en COP (o sin moneda), retorna el monto
        sin tocar -- identico al comportamiento de siempre."""
        return self._valor_en_pesos_en_fecha(abono.monto, obligacion, abono.fecha)

    def _fecha_capitalizacion_anatocismo(self, obligacion) -> date | None:
        if obligacion.anatocismo_demanda_judicial:
            return obligacion.fecha_vencimiento + timedelta(days=365)
        if obligacion.anatocismo_fecha_acuerdo is not None:
            return obligacion.anatocismo_fecha_acuerdo
        return None

    def _eventos_anatocismo(self, obligacion, fecha_corte: date) -> list[Event]:
        fecha_capitalizacion = self._fecha_capitalizacion_anatocismo(obligacion)
        if fecha_capitalizacion is None or fecha_capitalizacion > fecha_corte:
            return []

        eventos: list[Event] = []
        fecha_evento = fecha_capitalizacion
        while fecha_evento <= fecha_corte:
            eventos.append(
                Event(
                    date=fecha_evento,
                    payload={
                        "label": "Capitalización de intereses (Art. 886 C.Co. — anatocismo comercial)"
                    },
                    event_type="CAPITALIZACION_INTERESES_ANATOCISMO",
                )
            )
            fecha_evento += timedelta(days=365)
        return eventos

    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> list[Event]:
        valor_pesos = self._valor_en_pesos(obligacion)
        if obligacion.tipo.value == "PUNTUAL":
            eventos = [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": valor_pesos, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]
            eventos.extend(self._eventos_anatocismo(obligacion, fecha_corte))
            evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=valor_pesos)
            if evento_costas is not None:
                eventos.append(evento_costas)
            return eventos

        # RECURRENTE
        scheduler = FamilyScheduler()
        scheduler.add_monthly_obligation(
            amount=valor_pesos,
            concept=obligacion.concepto,
            due_day=obligacion.dia_pago,
            category=obligacion.categoria,
        )
        fin = obligacion.fecha_fin or fecha_corte
        return scheduler.generate(start=obligacion.fecha_inicio, end=fin)

    def _construir_rate_provider_obligacion(
        self, obligacion, fecha_corte: date, tope: Decimal | None = None
    ) -> MemoryRateProvider:
        """`tope` (Sprint 2, sancion de usura): si se pasa, recorta ambas tasas
        (remuneratoria y moratoria) a ese tope antes de convertirlas a diarias --
        usado unicamente por _calcular_sancion_usura para la liquidacion sombra de
        referencia ("Intereses_Cobrados_Con_Tasa_Usura"), nunca en la liquidacion
        real que se devuelve al usuario."""
        tasa_remuneratoria_anual = obligacion.tasa_efectiva_anual
        tasa_moratoria_anual = obligacion.tasa_moratoria_anual
        if tope is not None:
            tasa_remuneratoria_anual = min(tasa_remuneratoria_anual, tope)
            tasa_moratoria_anual = min(tasa_moratoria_anual, tope)

        provider = MemoryRateProvider()
        tasa_moratoria_diaria = EffectiveRateConverter.annual_to_daily(tasa_moratoria_anual)

        if obligacion.tipo.value == "PUNTUAL":
            tasa_remuneratoria_diaria = EffectiveRateConverter.annual_to_daily(tasa_remuneratoria_anual)
            inicio_remuneratorio = obligacion.fecha_origen - timedelta(days=1)
            fin_remuneratorio = min(obligacion.fecha_vencimiento, fecha_corte)
            provider.add_rate_period(
                start=inicio_remuneratorio,
                end=fin_remuneratorio,
                rate=tasa_remuneratoria_diaria,
                source="Tasa remuneratoria pactada (Art. 884 C.Co.)",
            )
            if obligacion.fecha_vencimiento < fecha_corte:
                inicio_moratorio = obligacion.fecha_vencimiento + timedelta(days=1)
                provider.add_rate_period(
                    start=inicio_moratorio,
                    end=fecha_corte,
                    rate=tasa_moratoria_diaria,
                    source="Tasa moratoria pactada (Art. 884 C.Co.)",
                )
        else:
            # RECURRENTE: sin split por cuota individual (alcance reducido, ver spec).
            inicio = obligacion.fecha_inicio - timedelta(days=1)
            provider.add_rate_period(
                start=inicio,
                end=fecha_corte,
                rate=tasa_moratoria_diaria,
                source="Tasa moratoria pactada (Art. 884 C.Co.)",
            )

        return provider


class LaboralStrategy(AreaStrategy):
    """
    Area Laboral. Liquidacion final (finiquito) de UN contrato de trabajo por
    expediente: cesantias, intereses a cesantias, prima (junio/diciembre) y
    vacaciones (LaborScheduler), mas la indemnizacion moratoria bifasica del
    Art. 65 CST (MoratoryIndemnityCalculator) si el pago real o la fecha de
    corte quedan despues de la fecha de terminacion del contrato.

    No es compatible con indexacion IPC (soporta_indexacion_ipc = False): las
    prestaciones sociales se liquidan sobre el salario nominal vigente al
    momento de la causacion, no se indexan por perdida de poder adquisitivo.

    Seguridad social (cotizaciones IBC, pension, salud, ARL, FSP) es opt-in
    via el flag `incluir_seguridad_social` de la obligacion (requiere ademas
    `nivel_riesgo_arl`, I-V) -- ver Pendientes.md, Sprint 16, y
    docs/superpowers/specs/2026-07-18-area-laboral-design.md.
    """

    soporta_indexacion_ipc = False

    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")
        if len(obligaciones) != 1:
            raise ValueError(
                "El area Laboral liquida un solo contrato (una obligacion) por expediente."
            )

        obligacion = obligaciones[0]
        # es_smmlv (Sprint 44, punto 1): el valor digitado a mano se descarta y
        # se resuelve en memoria (nunca se persiste aqui -- eso lo hace el
        # formulario al guardar) desde el SMLMV vigente del año de origen del
        # contrato, para que la liquidacion siempre use el SMLMV mas
        # actualizado en parametros_legales, incluso si se corrigio despues
        # de que la obligacion se guardo.
        if obligacion.es_smmlv:
            obligacion.valor = get_smlmv_for_year(obligacion.fecha_origen.year)
        self._validar_obligacion_laboral(obligacion)

        # dias_trabajados (calendario real, resta simple, SIN +1): sigue
        # alimentando la seguridad social/incapacidades mas abajo en este
        # metodo -- fuera de alcance del Sprint 30 (la confirmacion del
        # despacho de conteo inclusivo aplico especificamente a prestaciones
        # sociales, no se extendio a cotizaciones de seguridad social en
        # este sprint).
        dias_trabajados = (obligacion.fecha_fin - obligacion.fecha_inicio).days
        # dias_trabajados_prestaciones (Sprint 30, corregido 2026-08-03):
        # conteo inclusivo (+1) sobre base comercial de 360 dias (12 meses de
        # 30 dias) -- confirmado por el despacho para cesantias/intereses/
        # prima/vacaciones (Preguntas-Para-Abogado-Respondidas.md, Sprint 3).
        # NO es el mismo valor que dias_trabajados de arriba.
        dias_trabajados_prestaciones = CalendarUtils.dias_comerciales_360(
            obligacion.fecha_inicio, obligacion.fecha_fin
        )
        eventos = LaborScheduler(
            salario_base=obligacion.valor,
            dias_trabajados=dias_trabajados_prestaciones,
            fecha_liquidacion=obligacion.fecha_fin,
        ).generate()

        monto_prestaciones = sum((e.payload["amount"] for e in eventos), Decimal("0.00"))

        evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=monto_prestaciones)
        if evento_costas is not None:
            eventos.append(evento_costas)

        if obligacion.incluir_seguridad_social:
            dias_suspension = sum(
                (evento.fecha_fin - evento.fecha_inicio).days
                for evento in obligacion.eventos_laborales
                if evento.tipo.value == "SUSPENSION"
            )
            cotizaciones = SeguridadSocialCalculator.calcular(
                salario_base=obligacion.valor,
                dias_trabajados=dias_trabajados,
                dias_suspension=dias_suspension,
                nivel_riesgo_arl=obligacion.nivel_riesgo_arl,
                fecha_referencia=obligacion.fecha_fin,
            )
            for concepto, monto, etiqueta in [
                ("COTIZACION_PENSION", cotizaciones.monto_pension, "Cotizacion Pension (seguridad social no pagada)"),
                ("COTIZACION_SALUD", cotizaciones.monto_salud, "Cotizacion Salud (seguridad social no pagada)"),
                ("COTIZACION_ARL", cotizaciones.monto_arl, "Cotizacion ARL (seguridad social no pagada)"),
                ("COTIZACION_FSP", cotizaciones.monto_fsp, "Cotizacion FSP (Fondo de Solidaridad Pensional)"),
            ]:
                if monto > Decimal("0.00"):
                    eventos.append(Event(
                        date=obligacion.fecha_fin,
                        payload={"amount": monto, "label": etiqueta},
                        event_type=concepto,
                    ))

            for evento in obligacion.eventos_laborales:
                if evento.tipo.value == "SUSPENSION":
                    eventos.append(Event(
                        date=evento.fecha_fin,
                        payload={
                            "amount": Decimal("0.00"),
                            "label": (
                                f"Suspension ({evento.motivo_suspension.value}) "
                                f"{evento.fecha_inicio}-{evento.fecha_fin}: no causa ARL"
                            ),
                        },
                        event_type="SUSPENSION_INFORMATIVA",
                    ))
                else:
                    dias_incapacidad = (evento.fecha_fin - evento.fecha_inicio).days
                    desglose = IncapacidadCalculator.calcular(
                        tipo=evento.tipo, ibc_mensual=cotizaciones.ibc_mensual,
                        dias_incapacidad=dias_incapacidad,
                    )
                    for tramo in desglose.tramos:
                        es_empleador = tramo.pagador == "EMPLEADOR"
                        eventos.append(Event(
                            date=evento.fecha_fin,
                            payload={
                                "amount": tramo.monto if es_empleador else Decimal("0.00"),
                                "label": (
                                    f"Incapacidad {evento.tipo.value} dias {tramo.dias} - "
                                    f"{tramo.pagador} ({tramo.porcentaje:.2%}): ${tramo.monto:,.2f}"
                                ),
                            },
                            event_type="INCAPACIDAD_EMPLEADOR" if es_empleador else "INCAPACIDAD_INFORMATIVA",
                        ))

        # fecha_pago_total (si existe) es cuando realmente se extinguio la
        # deuda; nunca puede ser posterior a fecha_corte para efectos de este
        # reporte -- si el pago real fue despues del corte elegido, la mora
        # se calcula solo hasta el corte (foto historica), no hasta el pago.
        if obligacion.fecha_pago_total is not None:
            fecha_referencia_mora = min(obligacion.fecha_pago_total, fecha_corte)
        else:
            fecha_referencia_mora = fecha_corte

        if fecha_referencia_mora > obligacion.fecha_fin:
            monto_adeudado = monto_prestaciones
            mora = MoratoryIndemnityCalculator.calcular(
                salario_mensual=obligacion.valor,
                monto_adeudado=monto_adeudado,
                fecha_terminacion=obligacion.fecha_fin,
                fecha_pago_o_corte=fecha_referencia_mora,
            )
            if mora.total > Decimal("0.00"):
                eventos.append(Event(
                    date=fecha_referencia_mora,
                    payload={"amount": mora.total, "label": "Indemnizacion moratoria Art. 65 CST"},
                    event_type="SANCION_MORATORIA",
                ))

        # Descuentos del empleador (Sprint 44, punto 3): se inyectan como
        # eventos PAYMENT mas -- mismo mecanismo de pagos/allocation que ya
        # usan los abonos (AllocationEngine.allocate, via LiquidationCore),
        # no uno nuevo. `es_legal` es solo metadata descriptiva para que el
        # reporte distinga un descuento autorizado de uno que no lo fue (la
        # etiqueta queda en el concepto de la fila); matematicamente ambos
        # reducen el neto adeudado exactamente igual.
        for descuento in obligacion.descuentos_laborales:
            calificacion = "legal" if descuento.es_legal else "ilegal"
            etiqueta = f"Descuento del empleador ({calificacion})"
            if descuento.motivo:
                etiqueta += f": {descuento.motivo}"
            eventos.append(Event(
                date=descuento.fecha,
                payload={"amount": descuento.monto, "label": etiqueta},
                event_type="PAYMENT",
            ))

        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos
        ]

        service = UniversalLiquidationService()
        return service.liquidar(
            eventos_causacion=eventos,
            pagos=pagos,
            fecha_corte=fecha_corte,
        )
        # Sin rate_provider: la tasa diaria generica de UniversalLiquidationService
        # queda en 0 por defecto. Toda la mora del area Laboral ya esta resuelta
        # en el evento SANCION_MORATORIA -- pasar un rate_provider aqui
        # duplicaria el castigo por mora.

    def _validar_obligacion_laboral(self, obligacion) -> None:
        if obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                "El area Laboral solo admite obligaciones de tipo PUNTUAL "
                "(un contrato completo); RECURRENTE no aplica a prestaciones sociales."
            )
        if obligacion.valor is None or obligacion.valor <= Decimal("0.00"):
            raise ValueError("El salario base de la obligacion laboral debe ser mayor que cero.")
        if obligacion.fecha_inicio is None or obligacion.fecha_fin is None:
            raise ValueError(
                "La obligacion laboral necesita 'fecha_inicio' y 'fecha_fin' del contrato."
            )
        if obligacion.fecha_fin <= obligacion.fecha_inicio:
            raise ValueError(
                f"La fecha de terminacion ({obligacion.fecha_fin}) debe ser posterior a la "
                f"fecha de inicio del contrato ({obligacion.fecha_inicio})."
            )
        if obligacion.pagada and obligacion.fecha_pago_total is None:
            raise ValueError(
                "Una obligacion marcada como pagada debe tener 'fecha_pago_total'."
            )
        if obligacion.incluir_seguridad_social and not obligacion.nivel_riesgo_arl:
            raise ValueError(
                "Si se incluyen cotizaciones de seguridad social, 'nivel_riesgo_arl' "
                "(I-V) es obligatorio."
            )
        if obligacion.eventos_laborales and not obligacion.incluir_seguridad_social:
            raise ValueError(
                "Hay eventos contractuales (suspension/incapacidad) registrados, pero "
                "'incluir_seguridad_social' no esta activado. Marca la casilla 'Incluir "
                "cotizaciones de seguridad social no pagadas' para que estos eventos se "
                "reflejen en la liquidacion."
            )

        for evento in obligacion.eventos_laborales:
            if evento.fecha_inicio < obligacion.fecha_inicio or evento.fecha_fin > obligacion.fecha_fin:
                raise ValueError(
                    f"El evento contractual del {evento.fecha_inicio} al {evento.fecha_fin} "
                    "cae fuera del rango del contrato "
                    f"({obligacion.fecha_inicio} a {obligacion.fecha_fin})."
                )

        eventos_ordenados = sorted(obligacion.eventos_laborales, key=lambda e: e.fecha_inicio)
        for anterior, siguiente in zip(eventos_ordenados, eventos_ordenados[1:]):
            if anterior.fecha_fin > siguiente.fecha_inicio:
                raise ValueError(
                    "Dos eventos contractuales se solapan en el tiempo: "
                    f"{anterior.fecha_inicio}-{anterior.fecha_fin} y "
                    f"{siguiente.fecha_inicio}-{siguiente.fecha_fin}."
                )


class SancionatorioStrategy(AreaStrategy):
    """
    Area Sancionatorio (multas SIC/Penal/Ambiental/Urbano en SMLMV o UVT, Ley 1955/2019
    art. 49). Cada obligacion es un hecho puntual: `cantidad_smlmv_uvt` se convierte a
    pesos segun la fecha del hecho (`fecha_origen`) via `resolver_base_sancion` -- SMLMV
    si es anterior a 2020-01-01, UVT (tabla historica 2006-2026) si es posterior.

    No soporta obligaciones RECURRENTE (una multa es un hecho unico).
    No es compatible con indexacion IPC: el monto ya esta expresado en una unidad
    actualizada (SMLMV/UVT), indexarlo otra vez seria doble indexacion.
    """

    soporta_indexacion_ipc = False

    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_sancionatoria(obligacion)

        return _liquidar_por_obligacion(
            obligaciones=obligaciones,
            abonos=abonos,
            fecha_corte=fecha_corte,
            eventos_fn=self._eventos_de_obligacion,
            rate_provider_fn=self._construir_rate_provider_obligacion,
        )

    def _validar_obligacion_sancionatoria(self, obligacion) -> None:
        if obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion sancionatoria '{obligacion.concepto}' debe ser PUNTUAL "
                f"(una multa es un hecho unico, no admite RECURRENTE)."
            )
        if obligacion.cantidad_smlmv_uvt is None:
            raise ValueError(
                f"La obligacion sancionatoria '{obligacion.concepto}' necesita el campo "
                f"'cantidad_smlmv_uvt' para liquidar."
            )

    def _eventos_de_obligacion(self, obligacion) -> list[Event]:
        monto_pesos = resolver_base_sancion(obligacion.fecha_origen, obligacion.cantidad_smlmv_uvt)
        eventos = [
            Event(
                date=obligacion.fecha_origen,
                payload={"amount": monto_pesos, "label": obligacion.concepto},
                event_type=obligacion.categoria,
            )
        ]
        evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=monto_pesos)
        if evento_costas is not None:
            eventos.append(evento_costas)
        return eventos

    def _construir_rate_provider_obligacion(self, obligacion, fecha_corte: date) -> MemoryRateProvider:
        return self._rate_provider_tasa_plana(obligacion.fecha_origen, fecha_corte, obligacion.tasa_efectiva_anual)


class HonorariosStrategy(AreaStrategy):
    """
    Area Honorarios / Litigio (cobro de honorarios profesionales y costas judiciales).
    Cada obligacion es un hecho puntual que resulta en 1 o 2 eventos de capital:
    honorarios profesionales (tarifa fija + cuota litis, validados contra ambos topes
    legales) y, si aplica, un evento adicional de costas procesales. Costas procesales:
    `costas_pct_manual` (si el juez ya fijo un porcentaje en el auto) tiene prioridad;
    si no esta seteado, se calcula automaticamente segun el Acuerdo PSAA16-10554 (tabla
    completa en `app/engine/costs/agencias_en_derecho.py`) cuando la obligacion trae
    `costas_tipo_proceso`/`costas_instancia`.

    Tope de cuota litis (un solo tope, no dos en cascada -- corregido Sprint 4, ver
    respuesta del despacho en Preguntas-Para-Abogado.md: el PDF trae un 50% en una
    seccion y un 30% en otra, pero el tope legal absoluto y definitivo es el 50%
    acumulado, no ambos a la vez):
    - honorarios fijos + cuota litis <= 50% del beneficio obtenido. Si se excede,
      se bloquea la liquidacion con una alerta de riesgo disciplinario ("Honorarios
      Desproporcionados - Art. 35 Num. 4 Ley 1123/2007").

    No soporta obligaciones RECURRENTE. No es compatible con indexacion IPC.
    """

    soporta_indexacion_ipc = False

    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        for obligacion in obligaciones:
            self._validar_obligacion_honorarios(obligacion)

        return _liquidar_por_obligacion(
            obligaciones=obligaciones,
            abonos=abonos,
            fecha_corte=fecha_corte,
            eventos_fn=self._eventos_de_obligacion,
            rate_provider_fn=self._construir_rate_provider_obligacion,
        )

    def _validar_obligacion_honorarios(self, obligacion) -> None:
        if obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion de honorarios '{obligacion.concepto}' debe ser PUNTUAL."
            )
        campos_requeridos = {
            "honorarios_fijos_pactados": obligacion.honorarios_fijos_pactados,
            "cuota_litis_pactada_pct": obligacion.cuota_litis_pactada_pct,
            "beneficio_obtenido": obligacion.beneficio_obtenido,
        }
        for nombre_campo, valor in campos_requeridos.items():
            if valor is None:
                raise ValueError(
                    f"La obligacion de honorarios '{obligacion.concepto}' necesita el campo "
                    f"'{nombre_campo}' para liquidar."
                )

        cuota_litis_monto = self._cuota_litis_monto(obligacion)
        total_honorarios = obligacion.honorarios_fijos_pactados + cuota_litis_monto
        tope_total_pct = get_parametro("HONORARIOS_TOTAL_PCT", obligacion.fecha_origen)
        tope_total = obligacion.beneficio_obtenido * tope_total_pct / Decimal("100")
        if total_honorarios > tope_total:
            raise CuotaLitisExcedeTopeError(
                f"Honorarios Desproporcionados - Art. 35 Num. 4 Ley 1123/2007: la suma de "
                f"honorarios fijos + cuota litis de '{obligacion.concepto}' ({total_honorarios}) "
                f"excede el tope legal del {tope_total_pct}% del beneficio obtenido ({tope_total})."
            )

    def _cuota_litis_monto(self, obligacion) -> Decimal:
        return obligacion.beneficio_obtenido * obligacion.cuota_litis_pactada_pct / Decimal("100")

    def _eventos_de_obligacion(self, obligacion) -> list[Event]:
        cuota_litis_monto = self._cuota_litis_monto(obligacion)
        total_honorarios = obligacion.honorarios_fijos_pactados + cuota_litis_monto

        eventos = [
            Event(
                date=obligacion.fecha_origen,
                payload={"amount": total_honorarios, "label": obligacion.concepto},
                event_type=obligacion.categoria,
            )
        ]
        evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=obligacion.beneficio_obtenido)
        if evento_costas is not None:
            eventos.append(evento_costas)
        return eventos

    def _construir_rate_provider_obligacion(self, obligacion, fecha_corte: date) -> MemoryRateProvider:
        return self._rate_provider_tasa_plana(obligacion.fecha_origen, fecha_corte, obligacion.tasa_efectiva_anual)


class TributarioStrategy(AreaStrategy):
    """
    Area Tributario (cierre del Sprint 11b): impuesto a cargo, 3 sanciones (extemporaneidad,
    inexactitud, error aritmetico) y Renta Liquida Gravable informativa.

    Reutiliza el motor generico de liquidacion (UniversalLiquidationService/LiquidationCore)
    en vez de un motor de imputacion dedicado: el impuesto a cargo cae en el bucket
    'principal' (event_type = obligacion.categoria = "IMPUESTO_A_CARGO", agregado a
    _capital_concepts igual que cada area anterior), las 3 sanciones se normalizan a un unico
    event_type "SANCION_TRIBUTARIA" que cae en el bucket 'indexation'. El orden de pago que
    ya aplica AllocationEngine (indexacion -> interes -> capital) coincide exactamente con el
    orden exigido para tributario (sanciones -> intereses -> impuesto) -- ver design spec,
    seccion "Arquitectura".

    El interes automatico (E.T. art. 635, nunca pactado) reutiliza
    construir_rate_provider_moratorio_tributario del Sprint 11a.

    "RENTA_LIQUIDA" no genera ningun evento de causacion -- es informativo (base gravable,
    no una deuda exigible) y se adjunta aparte en LiquidationResult.renta_liquida. Un
    expediente admite como maximo una obligacion "RENTA_LIQUIDA" (un solo periodo gravable
    por liquidacion).

    No es compatible con indexacion IPC (soporta_indexacion_ipc = False). El PDF (pag. 40)
    advierte que no se pueden cobrar simultaneamente intereses moratorios y actualizacion
    monetaria si eso conduce a una tasa usuraria o doble pago por el mismo concepto (mismo
    criterio ya exigido en Sprint 2 para la incompatibilidad interes-comercial + IPC). Aqui
    esa combinacion no requiere un guard en tiempo de ejecucion: el formulario de la GUI
    oculta el checkbox "aplica indexacion IPC" para el area TRIBUTARIO (ver obligaciones.py)
    y _evento_de_obligacion, a diferencia de CivilFamiliaStrategy, nunca lee
    obligacion.aplica_indexacion_ipc -- por lo que ninguna obligacion tributaria puede
    generar a la vez el interes automatico E.T. 635 y un evento de correccion monetaria IPC
    sobre el mismo hecho. La advertencia del PDF no aplica por construccion, no por una
    validacion explicita en tiempo de ejecucion.

    Concurrencia especial para mora > 3 años (Art. 867-1 E.T., corregido Sprint 15,
    2026-08-01, respuesta del despacho -- Sentencia C-549/1993: interes moratorio e
    indexacion tienen naturalezas distintas y SI pueden concurrir):
    - "Impuesto" (IMPUESTO_A_CARGO): conserva el interes E.T. 635 y ADEMAS se indexa por
      IPC, topando la suma (interes + indexacion) al interes que produciria la tasa de
      usura PLENA (sin el descuento de 2 puntos del art. 635) sobre el mismo capital y
      periodo -- ver app/engine/tax/actualizacion_867_1.py.
    - "Sanciones" (SANCION_*): NO se liquida interes moratorio -- se reemplaza
      integramente por la indexacion IPC.
    - Mora <= 3 años: sin cambios para ningun rubro.

    Esto exige que cada obligacion corra en su propio LiquidationCore (via
    _liquidar_por_obligacion, mismo patron que Comercial/CivilFamilia desde el Sprint 21):
    un solo PendingDebt/rate provider compartido para todo el expediente no puede darle
    0% de interes a una sancion y la tasa E.T. 635 al impuesto al mismo tiempo.
    """

    soporta_indexacion_ipc = False

    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        obligaciones_renta_liquida = [o for o in obligaciones if o.categoria == "RENTA_LIQUIDA"]
        if len(obligaciones_renta_liquida) > 1:
            raise ValueError(
                "Un expediente tributario admite una sola obligacion 'RENTA_LIQUIDA' "
                "(un solo periodo gravable por liquidacion)."
            )

        obligaciones_deuda = [o for o in obligaciones if o.categoria != "RENTA_LIQUIDA"]
        for obligacion in obligaciones_deuda:
            self._validar_obligacion_tributaria(obligacion)

        resultado = _liquidar_por_obligacion(
            obligaciones=obligaciones_deuda,
            abonos=abonos,
            fecha_corte=fecha_corte,
            eventos_fn=lambda obligacion: self._eventos_de_obligacion(obligacion, fecha_corte),
            rate_provider_fn=self._construir_rate_provider_obligacion,
        )

        if obligaciones_renta_liquida:
            obligacion_renta = obligaciones_renta_liquida[0]
            renta_liquida = depurar_renta_liquida_gravable(
                ingresos_brutos=obligacion_renta.ingresos_brutos,
                devoluciones_rebajas_descuentos=obligacion_renta.devoluciones_rebajas_descuentos,
                costos=obligacion_renta.costos,
                deducciones=obligacion_renta.deducciones,
                rentas_exentas=obligacion_renta.rentas_exentas,
            )
            resultado = replace(resultado, renta_liquida=renta_liquida)

        return resultado

    def _validar_obligacion_tributaria(self, obligacion) -> None:
        if obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion tributaria '{obligacion.concepto}' debe ser PUNTUAL "
                f"(un hecho tributario es un evento unico, no admite RECURRENTE)."
            )

        if obligacion.categoria == "IMPUESTO_A_CARGO":
            if obligacion.valor is None or obligacion.valor <= Decimal("0.00"):
                raise ValueError(
                    f"El impuesto a cargo '{obligacion.concepto}' debe tener 'valor' mayor que cero."
                )
            return

        if obligacion.categoria == "SANCION_EXTEMPORANEIDAD":
            if obligacion.base_sancion_tributaria is None or obligacion.meses_extemporaneidad is None:
                raise ValueError(
                    f"La sancion por extemporaneidad '{obligacion.concepto}' necesita "
                    f"'base_sancion_tributaria' y 'meses_extemporaneidad'."
                )
            return

        if obligacion.categoria == "SANCION_INEXACTITUD":
            if obligacion.base_sancion_tributaria is None:
                raise ValueError(
                    f"La sancion por inexactitud '{obligacion.concepto}' necesita "
                    f"'base_sancion_tributaria' (la diferencia entre el saldo determinado y el declarado)."
                )
            return

        if obligacion.categoria == "SANCION_ERROR_ARITMETICO":
            if obligacion.base_sancion_tributaria is None:
                raise ValueError(
                    f"La sancion por error aritmetico '{obligacion.concepto}' necesita "
                    f"'base_sancion_tributaria' (la diferencia generada por el error)."
                )
            return

        raise ValueError(
            f"Categoria tributaria desconocida: '{obligacion.categoria}'."
        )

    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> list[Event]:
        eventos = [self._evento_de_obligacion(obligacion)]
        if aplica_actualizacion_867_1(obligacion.fecha_origen, fecha_corte):
            eventos.append(self._evento_actualizacion_867_1(obligacion, fecha_corte))
        return eventos

    def _evento_de_obligacion(self, obligacion) -> Event:
        if obligacion.categoria == "IMPUESTO_A_CARGO":
            return Event(
                date=obligacion.fecha_origen,
                payload={"amount": obligacion.valor, "label": obligacion.concepto},
                event_type=obligacion.categoria,
            )

        monto_sancion = self._calcular_monto_sancion(obligacion)
        return Event(
            date=obligacion.fecha_origen,
            payload={"amount": monto_sancion, "label": obligacion.concepto},
            event_type="SANCION_TRIBUTARIA",
        )

    def _evento_actualizacion_867_1(self, obligacion, fecha_corte: date) -> Event:
        """Art. 867-1 E.T. (Sprint 15, correccion 2026-08-01): indexacion IPC
        adicional cuando la mora supera 3 años -- ver docstring de la clase y
        app/engine/tax/actualizacion_867_1.py."""
        if obligacion.categoria == "IMPUESTO_A_CARGO":
            capital = obligacion.valor
            interes_ya_liquidado = calcular_interes_moratorio_tributario(
                capital, obligacion.fecha_origen, fecha_corte
            )
            monto = calcular_indexacion_867_1_topada(
                capital, obligacion.fecha_origen, fecha_corte, interes_ya_liquidado
            )
        else:
            capital = self._calcular_monto_sancion(obligacion)
            monto = calcular_indexacion_867_1(capital, obligacion.fecha_origen, fecha_corte)

        return Event(
            date=obligacion.fecha_origen,
            payload={"amount": monto, "label": f"Actualización Art. 867-1 E.T. — {obligacion.concepto}"},
            event_type="INDEXATION",
        )

    def _calcular_monto_sancion(self, obligacion) -> Decimal:
        if obligacion.categoria == "SANCION_EXTEMPORANEIDAD":
            return calcular_sancion_extemporaneidad(
                impuesto_a_cargo=obligacion.base_sancion_tributaria,
                meses_o_fraccion=obligacion.meses_extemporaneidad,
                fecha_referencia=obligacion.fecha_origen,
            )
        if obligacion.categoria == "SANCION_INEXACTITUD":
            return calcular_sancion_inexactitud(
                diferencia=obligacion.base_sancion_tributaria,
                agravada=bool(obligacion.sancion_agravada),
                fecha_referencia=obligacion.fecha_origen,
            )
        # SANCION_ERROR_ARITMETICO (unica categoria de sancion restante, ya validada arriba)
        return calcular_sancion_error_aritmetico(
            diferencia=obligacion.base_sancion_tributaria,
            fecha_referencia=obligacion.fecha_origen,
        )

    def _construir_rate_provider_obligacion(self, obligacion, fecha_corte: date) -> MemoryRateProvider:
        provider = MemoryRateProvider()

        if obligacion.categoria != "IMPUESTO_A_CARGO" and aplica_actualizacion_867_1(
            obligacion.fecha_origen, fecha_corte
        ):
            # Sanciones con mora > 3 años (Art. 867-1 E.T., Sprint 15): sin interes
            # moratorio -- reemplazado integramente por la indexacion IPC (ver
            # _evento_actualizacion_867_1).
            provider.add_rate_period(
                start=obligacion.fecha_origen,
                end=fecha_corte,
                rate=Rate(Decimal("0.0")),
                source="Sin interés moratorio: mora > 3 años, reemplazado por actualización IPC (Art. 867-1 E.T.)",
            )
            return provider

        provider = construir_rate_provider_moratorio_tributario(obligacion.fecha_origen, fecha_corte)
        # construir_rate_provider_moratorio_tributario solo cubre desde el dia siguiente a la
        # exigibilidad (inicio_mora = fecha_origen + 1 dia, la mora nunca corre el mismo
        # dia en que nace la obligacion -- ver docstring del modulo). LiquidationCore, sin
        # embargo, consulta la tasa del propio dia de cada evento (incluyendo el evento de
        # causacion del capital/sancion, que cae justo en fecha_origen) solo para
        # trazabilidad/metadata, no para acumular interes ese dia. Sin este relleno, un
        # MemoryRateProvider vacio (caso comun: fecha_corte == fecha_origen, sin mora
        # todavia) lanzaria ValueError al liquidar. 0% es la tasa correcta para ese dia: no hay
        # mora antes de que empiece a correr.
        provider.add_rate_period(
            start=obligacion.fecha_origen,
            end=obligacion.fecha_origen,
            rate=Rate(Decimal("0.0")),
            source="Sin mora (fecha de exigibilidad, aun no corre el interes del E.T. art. 635)",
        )
        return provider
