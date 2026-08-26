from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

from app.core.exceptions import CuotaLitisExcedeTopeError, IPCMensualNoDisponibleError
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
from app.engine.indexation.historical_index import (
    get_ipc_interpolado_for_date,
    get_ipc_interpolado_mensual_for_date,
    get_smlmv_for_year,
)
from app.engine.indexation.ipc import IPCIndexation
from app.engine.indexation.smlmv_to_uvt import resolver_base_sancion
from app.engine.interest.provider import MemoryRateProvider
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.engine.interest.usury_validator import calcular_tope_usura
from app.engine.labor.dismissal_indemnity import DismissalIndemnityCalculator
from app.engine.labor.incapacidad import IncapacidadCalculator
from app.engine.labor.moratory_indemnity import MoratoryIndemnityCalculator
from app.engine.labor.salario_domestico import (
    calcular_ibc_seguridad_social_domestico,
    salario_diario_a_mensual,
)
from app.engine.labor.seguridad_social import SeguridadSocialCalculator
from app.engine.liquidation.allocation import AllocationEngine
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
from app.services.recurrencia_fechas_fijas import deserializar_fechas_anuales
from app.services.salarios_dejados_de_percibir import (
    determinar_tipo_reajuste_salarios_dejados_de_percibir,
    generar_eventos_salarios_dejados_de_percibir,
)
from app.services.vigencia_alimentos import fecha_fin_efectiva_recurrente

# Sprint 93: categoria de Laboral que reabre, SOLO para ella, la exclusion de
# TipoObligacion.RECURRENTE que el Sprint 75 dejo explicita para toda el area
# -- ver LaboralStrategy._validar_obligacion_laboral/
# _liquidar_salarios_dejados_de_percibir mas abajo y el modulo
# app/services/salarios_dejados_de_percibir.py. Constante en vez de repetir el
# string literal en los 2 puntos donde se usa (mismo criterio que
# app.core.constants.CATEGORIAS_LABORAL, que trae el mismo codigo para el
# combo de la UI).
CATEGORIA_SALARIOS_DEJADOS_DE_PERCIBIR = "SALARIOS_DEJADOS_DE_PERCIBIR"


def _evento_costas_procesales(obligacion, pretensiones_reconocidas: Decimal) -> Event | None:
    """Costas procesales (agencias en derecho) para cualquier area de litigio
    judicial. costas_pct_manual (Sprint 4) tiene siempre prioridad sobre el
    calculo automatico del Acuerdo PSAA16-10554 (Sprint 18) -- si el auto
    judicial real ya fijo un porcentaje, ese manda, pero desde la correccion
    del Sprint 18 (2026-08-01) ese porcentaje manual se valida contra el rango
    permitido por cuantia (respuesta del despacho) y se RECHAZA (no se trunca)
    si esta fuera de rango -- ver validar_costas_pct_manual. En la rama
    automatica se propaga obligacion.fecha_providencia_costas (campo aditivo,
    Sprint 18 ultraactividad CPC->CGP): si esta definida y es anterior al
    1/1/2016, calcular_agencias_en_derecho lanza TarifaPreCGPNoDisponibleError
    en vez de aplicar la tabla granular del CGP; si es None (no capturada, el
    caso normal hoy) el comportamiento es identico al de antes de este sprint.
    Retorna None si la obligacion no tiene ninguno de los dos mecanismos
    activado (comportamiento identico al de antes de este sprint)."""
    if obligacion.costas_pct_manual is not None:
        validar_costas_pct_manual(
            obligacion.costas_pct_manual,
            pretensiones_reconocidas,
            obligacion.fecha_origen,
        )
        costas_monto = pretensiones_reconocidas * obligacion.costas_pct_manual / Decimal("100")
    elif obligacion.costas_tipo_proceso is not None and obligacion.costas_instancia is not None:
        costas_monto = calcular_agencias_en_derecho(
            tipo_proceso=TipoProceso(obligacion.costas_tipo_proceso),
            instancia=Instancia(obligacion.costas_instancia),
            pretensiones_reconocidas=pretensiones_reconocidas,
            fecha_radicacion=obligacion.fecha_origen,
            fecha_providencia_costas=obligacion.fecha_providencia_costas,
        )
    else:
        return None

    return Event(
        date=obligacion.fecha_origen,
        payload={"amount": costas_monto, "label": f"Costas procesales - {obligacion.concepto}"},
        event_type="COSTAS_PROCESALES",
    )


def _estrategia_imputacion_por_obligacion(obligacion):
    """Capital-primero para toda cuota-hija generada por recurrencia
    (obligacion_padre_id no nulo, Sprint 75); orden legal general
    (indexacion->interes->capital) para el resto -- ver decision 2 de
    docs/superpowers/specs/2026-08-14-sprint75-cuotas-recurrentes-cascada-design.md."""
    if obligacion.obligacion_padre_id is not None:
        return AllocationEngine.allocate_capital_primero
    return AllocationEngine.allocate


def _liquidar_por_obligacion(
    obligaciones: list,
    abonos: list,
    fecha_corte: date,
    eventos_fn: Callable[[object], list[Event]],
    rate_provider_fn: Callable[[object, date], MemoryRateProvider],
    usar_suma_unica_fn: Callable[[object], bool] = lambda obligacion: False,
    monto_abono_fn: Callable[[object, object], Decimal] = lambda obligacion, abono: abono.monto,
    estrategia_imputacion_fn: Callable[[object], Callable] = _estrategia_imputacion_por_obligacion,
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
                date=abono.fecha,
                amount=monto_abono_fn(obligacion, abono),
                reference=abono.referencia or "",
            )
            for abono in abonos_obligacion
        ]
        service = UniversalLiquidationService()
        resultados.append(
            service.liquidar(
                eventos_causacion=eventos_fn(obligacion),
                pagos=pagos,
                fecha_corte=fecha_corte,
                rate_provider=rate_provider_fn(obligacion, fecha_corte),
                usar_suma_unica=usar_suma_unica_fn(obligacion),
                estrategia_imputacion=estrategia_imputacion_fn(obligacion),
            )
        )

    return _fusionar_resultados(resultados, fecha_corte)


def _fusionar_resultados(
    resultados: list[LiquidationResult], fecha_corte: date
) -> LiquidationResult:
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
            principal=sum(
                (estado.principal for estado in ultimo_estado.values()), Decimal("0.00")
            ),
            interest=sum((estado.interest for estado in ultimo_estado.values()), Decimal("0.00")),
            indexation=sum(
                (estado.indexation for estado in ultimo_estado.values()), Decimal("0.00")
            ),
        )
        items_fusionados.append(
            replace(
                item,
                capital_base=saldo_consolidado.principal,
                balance=RunningBalance(
                    date=item.date, debt=saldo_consolidado, event_type=item.balance.event_type
                ),
            )
        )

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
        # Cada obligacion aislada ya causo su propio interes de cierre (el que corre
        # entre su ultimo evento y fecha_corte, ver LiquidationCore.process()) en su
        # propio LiquidationItem de tipo LIQUIDATION_CUTOFF -- pero ese item se
        # descarta arriba (filas_regulares excluye LIQUIDATION_CUTOFF) para no
        # mostrar N filas de cierre. Sin sumar ese interes aqui, el total que ve el
        # abogado en "Interes acumulado"/"Intereses Generados"
        # (LiquidationResult.total_interest_accrued(), que solo suma la columna
        # interest_amount fila por fila) queda por debajo del interes real de la
        # liquidacion en cualquier expediente con 2+ obligaciones, aunque el saldo
        # final (basado en balance.debt, no en esta columna) siempre fue correcto.
        interes_cierre_consolidado = sum(
            (
                item.interest_amount
                for resultado in resultados
                for item in resultado.items
                if item.balance.event_type == "LIQUIDATION_CUTOFF"
            ),
            Decimal("0.00"),
        )
        items_fusionados.append(
            LiquidationItem(
                date=fecha_corte,
                concept="Corte final de liquidación",
                capital_base=saldo_final.principal,
                interest_rate=Decimal("0.00"),
                interest_amount=interes_cierre_consolidado,
                indexation_amount=Decimal("0.00"),
                payment_amount=Decimal("0.00"),
                balance=RunningBalance(
                    date=fecha_corte, debt=saldo_final, event_type="LIQUIDATION_CUTOFF"
                ),
                rate_source="Varias tasas — ver detalle por fila arriba",
            )
        )

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
            start=fecha_inicio - timedelta(days=1),
            end=fecha_corte,
            rate=tasa_diaria,
            source=source,
        )
        return provider

    @staticmethod
    def _evento_indexacion_ipc(
        fecha_causacion: date, capital: Decimal, concepto: str, fecha_corte: date
    ) -> Event:
        """Evento de indexacion IPC generico (Sprint 8, promovido a la clase base en
        el Sprint 43 para que Honorarios/Sancionatorio/Laboral/Comercial lo reutilicen
        tal cual en vez de reimplementar la misma formula -- interpolacion ANUAL,
        siempre. CivilFamiliaStrategy._evento_indexacion fue un alias de este metodo
        desde el Sprint 43 hasta el Sprint 80: desde el Sprint 80 tiene su propia
        implementacion (indice IPC MENSUAL real dentro de rango, con fallback
        documentado a esta misma interpolacion anual fuera de rango) -- ya NO es un
        alias, ver el docstring de CivilFamiliaStrategy._evento_indexacion para el
        detalle. `IPCIndexation.calculate` ya redondea y ya devuelve 0 si hay
        deflacion o si el capital es 0/negativo -- ver docstring de esa funcion."""
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

    @staticmethod
    def _tasa_civil_anual_pct(fecha: date) -> Decimal:
        """Tasa de interes civil legal anual (Art. 1617 C.C.), en forma porcentual
        (ej. Decimal("6.00")) lista para `EffectiveRateConverter.annual_to_daily`/
        `_rate_provider_tasa_plana`. Consulta la clave versionada CIVIL_ANNUAL_RATE
        via `get_parametro` (fuente unica, `app/engine/interest/legal_rates.py`) en
        vez de hardcodear un 6% nuevo -- esa clave guarda la tasa en forma fraccion
        (0.06), de ahi el x100. Sprint 43: reutilizada por HonorariosStrategy (segundo
        termino de su formula) y por ComercialStrategy en el modo (b) de la regla XOR
        (capital indexado + interes civil puro, solo con pacto expreso)."""
        return get_parametro("CIVIL_ANNUAL_RATE", fecha) * Decimal("100")

    @staticmethod
    def _agregar_alerta(resultado: LiquidationResult, mensaje: str) -> LiquidationResult:
        """Adjunta un mensaje de advertencia NO bloqueante a `resultado` (Sprint 43) --
        ver docstring de `LiquidationResult.alertas`. La vista los muestra con
        `mostrar_toast(tipo="warning")` (mismo mecanismo del Sprint 36), reutilizado
        aqui en vez de inventar un segundo canal de alertas."""
        return replace(resultado, alertas=[*resultado.alertas, mensaje])


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

        # Sprint 41: ids de obligaciones RECURRENTE que ya tienen al menos una cuota
        # hija persistida (generar_cuotas_mensuales, app/services/reajuste_anual.py --
        # Obligacion PUNTUAL con obligacion_padre_id apuntando a ellas). `obligaciones`
        # ya trae esas cuotas como filas independientes (el mismo expediente), asi que
        # basta con leer obligacion_padre_id de cada una -- no requiere una consulta
        # aparte.
        ids_con_cuotas_generadas = {
            obligacion.obligacion_padre_id
            for obligacion in obligaciones
            if obligacion.obligacion_padre_id is not None
        }

        return _liquidar_por_obligacion(
            obligaciones=obligaciones,
            abonos=abonos,
            fecha_corte=fecha_corte,
            eventos_fn=lambda obligacion: self._eventos_de_obligacion(
                obligacion, fecha_corte, ids_con_cuotas_generadas
            ),
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
        return bool(obligacion.aplica_indexacion_ipc) and bool(
            obligacion.interes_sobre_capital_indexado
        )

    def _eventos_de_obligacion(
        self, obligacion, fecha_corte: date, ids_con_cuotas_generadas: set[int] | None = None
    ) -> list[Event]:
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
            evento_costas = _evento_costas_procesales(
                obligacion, pretensiones_reconocidas=obligacion.valor
            )
            if evento_costas is not None:
                eventos.append(evento_costas)
            return eventos

        # RECURRENTE
        # Sprint 41/75 -- si esta obligacion ya tiene cuotas mensuales reales
        # generadas y persistidas (Obligacion PUNTUAL hijas, ver
        # app/services/reajuste_anual.py::generar_cuotas_mensuales), esas cuotas ya
        # vienen incluidas en `obligaciones` como filas independientes -- cada una se
        # procesa con su propio capital (reajustado o no, ver Sprint 75 Task 1) y su
        # propia fecha, exactamente como cualquier obligacion PUNTUAL normal (branch
        # de arriba). Esta obligacion RECURRENTE padre NO debe generar NINGUN evento
        # de capital propio en ese caso: hacerlo duplicaria el capital (una vez via
        # la expansion efimera de RecurringScheduler de abajo, otra vez via cada
        # cuota hija real). Ver Architecture punto 5 del plan del Sprint 41 y la
        # verificacion matematica de la Task 3
        # (tests/family/test_interes_autonomo_por_cuota.py), que confirma que dejar
        # que el motor consolidado procese las cuotas como obligaciones
        # independientes ya produce el interes de mora correcto por cuota. Si
        # todavia no se han generado cuotas (obligacion.id no aparece en
        # ids_con_cuotas_generadas), se preserva el comportamiento anterior a este
        # sprint (expansion efimera, capital constante, sin reajuste) -- el reajuste
        # solo aplica una vez que el usuario genera las cuotas explicitamente.
        # Cualquier obligacion RECURRENTE con cuotas hijas reales ya persistidas
        # (obligacion_padre_id apuntando a ella, sin importar si las genero
        # generar_cuotas_mensuales -- reajuste SMMLV/IPC/NINGUNO, Sprints 41/75 -- o
        # generar_cuotas_fechas_fijas -- fechas anuales fijas, Sprint 73) se procesa
        # exclusivamente a traves de esas cuotas. El criterio de skip es
        # unicamente la membresia en ids_con_cuotas_generadas -- ya NO depende de
        # tipo_reajuste_anual: hasta el Sprint 75 solo SMMLV/IPC podian tener cuotas
        # hijas reales generadas, asi que exigir reajuste activo ademas de la
        # membresia era redundante-pero-inofensivo; desde que generar_cuotas_mensuales
        # (Sprint 75 Task 1) tambien soporta NINGUNO, esa condicion extra volvio el
        # guard incorrecto -- una obligacion NINGUNO con cuotas ya generadas dejaba
        # de saltarse la expansion efimera y duplicaba el capital (bug encontrado en
        # revision de codigo, ver test
        # test_civil_familia_recurrente_sin_reajuste_y_cuotas_generadas_no_duplica_capital).
        # Igual de valido para la generalizacion del Sprint 73 (fechas anuales fijas):
        # ids_con_cuotas_generadas solo puede contener el id de esta obligacion si
        # alguno de los dos generadores ya corrio y persistio cuotas reales, asi que
        # basta con la pertenencia al set, sin repetir ninguna condicion de tipo de
        # recurrencia/reajuste.
        if obligacion.id in (ids_con_cuotas_generadas or set()):
            return []

        # tipo_recurrencia puede venir en None en un objeto Obligacion transitorio
        # nunca pasado por session.commit() (el default de columna 'MENSUAL' solo
        # lo aplica SQLAlchemy al hacer flush/insert) -- se trata igual que
        # MENSUAL, mismo criterio tolerante que tipo_reajuste_anual/None de abajo.
        es_fechas_fijas = (
            obligacion.tipo_recurrencia is not None
            and obligacion.tipo_recurrencia.value == "FECHAS_ANUALES_FIJAS"
        )

        scheduler = FamilyScheduler()
        if es_fechas_fijas:
            # Expansion efimera (sin cuotas hijas generadas todavia) para una
            # obligacion de fechas anuales fijas (ej. gastos de vestuario en
            # junio/diciembre/cumpleanos) -- reutiliza
            # FamilyScheduler.add_yearly_obligation, ya existente y probado
            # (tests/temporal/test_schedulers.py), una vez por cada fecha MM-DD
            # configurada, en vez de add_monthly_obligation. Sin este branch, una
            # obligacion de este tipo liquidada antes de presionar "Generar
            # cuotas" caeria en el fallback mensual de abajo (12 cuotas en vez de
            # las fechas puntuales pactadas) -- exactamente el bug que reporto el
            # usuario en el Sprint 73.
            for fecha_mm_dd in deserializar_fechas_anuales(obligacion.fechas_anuales_fijas):
                mes, dia = (int(parte) for parte in fecha_mm_dd.split("-"))
                scheduler.add_yearly_obligation(
                    amount=obligacion.valor,
                    concept=obligacion.concepto,
                    month=mes,
                    day=dia,
                    category=obligacion.categoria,
                )
        else:
            scheduler.add_monthly_obligation(
                amount=obligacion.valor,
                concept=obligacion.concepto,
                due_day=obligacion.dia_pago,
                category=obligacion.categoria,
            )
        # Vigencia por tipo de beneficiario (Sprint 74): si esta obligacion tiene un
        # Beneficiario capturado (getattr por compatibilidad con Obligacion
        # transitorias que nunca pasaron por la relationship, ej. algunos tests
        # legados que no la referencian), topa la generacion de cuotas con el
        # minimo entre `fecha_fin` manual y la fecha de fin de vigencia
        # automatica calculada (NINO: 18/25 anos segun si estudia). NINO_DISCAPACIDAD
        # permanente (vitalicio) y CONYUGE/PADRES/OTRO (sin criterio confirmado, ver
        # docstring de vigencia_alimentos.py) NUNCA aportan una fecha aqui -- para
        # esos casos el comportamiento es identico al de antes de este sprint (topado
        # solo por fecha_fin manual o fecha_corte).
        fin = fecha_fin_efectiva_recurrente(
            obligacion.fecha_fin, getattr(obligacion, "beneficiario", None), fecha_corte
        )
        fin = fin or fecha_corte
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

    @staticmethod
    def _evento_indexacion(
        fecha_causacion: date, capital: Decimal, concepto: str, fecha_corte: date
    ) -> Event:
        """Evento de indexacion IPC de Civil/Familia (Sprint 8; conectado al indice
        MENSUAL real del DANE en el Sprint 80). Hasta el Sprint 80 este metodo era un
        simple alias de `AreaStrategy._evento_indexacion_ipc` (el helper generico que
        Honorarios/Sancionatorio/Laboral/Comercial siguen usando tal cual, con la
        interpolacion ANUAL) -- ahora tiene su propia implementacion, exclusiva de
        Civil/Familia, que usa `get_ipc_interpolado_mensual_for_date` (interpolacion
        lineal por dias DENTRO del mes, la formula que el despacho exigio como la
        unica juridicamente valida -- ver Sprint 8 en
        docs/Preguntas-Para-Abogado-Respondidas.md) en vez de la interpolacion anual
        generica, siempre que la tabla `_IPC_MENSUAL` (historical_index.py) cubra
        AMBAS fechas (causacion y corte).

        Si CUALQUIERA de las dos fechas es ANTERIOR a enero de 2003 (primer mes
        cargado en `_IPC_MENSUAL`), `get_ipc_interpolado_mensual_for_date` lanza
        `IPCMensualNoDisponibleError` -- en ese caso se hace *fallback* COMPLETO
        a la interpolacion anual (`get_ipc_interpolado_for_date`) para AMBAS fechas,
        nunca solo para la que fallo: el indice mensual (base Diciembre-2018 = 100) y
        el indice anual acumulado (ancla implicita en 1966 = 100, ver
        `_construir_indice_ipc_acumulado`) son series con bases distintas, y
        `IPCIndexation.calculate` solo mira la razon `final_index / initial_index` --
        mezclar un indice de una serie con el de la otra arruinaria esa razon y daria
        un monto de indexacion sin sentido. Este fallback es intencional, decidido en
        el Sprint 80 para blindar con el indice mensual real la gran mayoria de los
        casos (todo lo posterior a 2003) sin dejar fuera silenciosamente los casos
        historicos anteriores -- que siguen recibiendo exactamente la misma
        interpolacion anual que usaban TODAS las obligaciones antes de este sprint.

        Una `fecha_corte` posterior al ultimo mes que el DANE haya certificado
        YA NO cae en este fallback (Sprint 8, respuesta del despacho 22/08/2026):
        `get_ipc_mensual_for_month` estima ese mes con la formula de "Estimacion
        Futura" que exigio el despacho en vez de lanzar la excepcion -- ver
        docstring de esa funcion en `historical_index.py`.

        `IPCIndexation.calculate` ya redondea y ya devuelve 0 si hay deflacion o si el
        capital es 0/negativo -- ver docstring de esa funcion."""
        try:
            initial_index = get_ipc_interpolado_mensual_for_date(fecha_causacion)
            final_index = get_ipc_interpolado_mensual_for_date(fecha_corte)
        except IPCMensualNoDisponibleError:
            initial_index = get_ipc_interpolado_for_date(fecha_causacion)
            final_index = get_ipc_interpolado_for_date(fecha_corte)

        monto = IPCIndexation.calculate(
            capital=capital,
            initial_index=initial_index,
            final_index=final_index,
        )
        return Event(
            date=fecha_causacion,
            payload={"amount": monto, "label": f"Indexación IPC — {concepto}"},
            event_type="INDEXATION",
        )

    def _construir_rate_provider_obligacion(
        self, obligacion, fecha_corte: date
    ) -> MemoryRateProvider:
        fecha_inicio = (
            obligacion.fecha_origen
            if obligacion.tipo.value == "PUNTUAL"
            else obligacion.fecha_inicio
        )
        # Sprint 61: fallback silencioso a CIVIL_ANNUAL_RATE cuando la obligacion
        # no trae tasa propia (0.00 -- mismo patron legitimo que ya usan
        # Sancionatorio/Honorarios para "el campo de tasa no aplica", confirmado
        # en el Sprint 24). Sin UI nueva: el campo de tasa del formulario ya
        # acepta guardar 0 explicitamente hoy. Reutiliza _tasa_civil_anual_pct
        # (Sprint 43, AreaStrategy) en vez de leer get_parametro directo: esa
        # clave se guarda como fraccion (0.06, ver scripts/migrate_parametros_legales.py)
        # y _tasa_civil_anual_pct ya hace la conversion x100 a forma porcentual
        # que espera _rate_provider_tasa_plana -- llamar get_parametro aqui
        # directo habria sido un error de unidades de 100x (bug real encontrado
        # al fusionar con el Sprint 43, corregido antes del merge a main).
        tasa = obligacion.tasa_efectiva_anual
        source = "Tasa pactada en la obligación (Art. 1617 C.C.)"
        if not tasa:
            tasa = self._tasa_civil_anual_pct(fecha_corte)
            source = "Tasa legal civil por defecto (CIVIL_ANNUAL_RATE, Art. 1617 C.C.)"
        return self._rate_provider_tasa_plana(
            fecha_inicio,
            fecha_corte,
            tasa,
            source=source,
        )


class ComercialStrategy(AreaStrategy):
    """
    Area Comercial (Art. 884 C.Co.). Cada obligacion debe traer su propia tasa
    remuneratoria (tasa_efectiva_anual), tasa moratoria (tasa_moratoria_anual),
    fecha de vencimiento y el IBC vigente aplicable (ibc_vigente_anual) -- no hay
    fallback automatico a un IBC de referencia en este sprint (ver docs/Pendientes.md,
    Sprint 2 y Sprint 5).

    Split real de tasa remuneratoria (antes del vencimiento) / moratoria (despues)
    solo aplica a obligaciones PUNTUAL. RECURRENTE usa una sola tasa moratoria para
    todo el periodo, igual que CivilFamiliaStrategy, porque el vencimiento de cada
    cuota individual no esta modelado
    (ver docs/superpowers/specs/2026-07-15-area-comercial-design.md).

    Indexacion IPC (Sprint 43, respuesta del despacho -- XOR estricto, NO como
    opcion libre acumulable a los intereses comerciales): `soporta_indexacion_ipc`
    se mantiene en `False` -- la tasa comercial (remuneratoria/moratoria) ya
    incorpora un componente inflacionario, asi que combinarla con IPC seria doble
    actualizacion. El abogado elige exactamente uno de los dos modos:
      (a) [default] tasa comercial pactada (remuneratoria antes del vencimiento,
          moratoria despues) -- comportamiento identico a antes de este sprint.
      (b) `aplica_indexacion_ipc` marcado + `pacto_expreso_indexacion` marcado:
          capital indexado por IPC (desde `fecha_origen` hasta la fecha de corte)
          + interes civil puro del 6% anual (Art. 1617 C.C., `_tasa_civil_anual_pct`)
          sobre el capital YA indexado (Suma Unica, `usar_suma_unica`) EN VEZ DE la
          tasa comercial -- solo valido si existe pacto expreso en el titulo que lo
          autorice (Art. 884 C.Co. es supletivo, no imperativo). Marcar
          `aplica_indexacion_ipc` SIN `pacto_expreso_indexacion` bloquea la
          liquidacion con ValueError (ver `_validar_obligacion_comercial`) -- ese es
          el mecanismo real del XOR: nunca se liquida con tasa comercial + IPC a la
          vez para la misma obligacion. Alcance reducido a PUNTUAL (mismo criterio
          que el anatocismo de esta clase): RECURRENTE no modela un pacto expreso
          por cuota individual, se rechaza con ValueError si se intenta.

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

        # Sprint 75 Task 3 -- mismo patron que CivilFamiliaStrategy (ver
        # docstring de _eventos_de_obligacion abajo): ids de obligaciones
        # RECURRENTE que ya tienen al menos una cuota hija persistida
        # (generar_cuotas_mensuales, app/services/reajuste_anual.py). `obligaciones`
        # ya trae esas cuotas como filas independientes del mismo expediente, asi
        # que basta con leer obligacion_padre_id de cada una.
        ids_con_cuotas_generadas = {
            obligacion.obligacion_padre_id
            for obligacion in obligaciones
            if obligacion.obligacion_padre_id is not None
        }

        resultado = _liquidar_por_obligacion(
            obligaciones=obligaciones,
            abonos=abonos,
            fecha_corte=fecha_corte,
            eventos_fn=lambda obligacion: self._eventos_de_obligacion(
                obligacion, fecha_corte, ids_con_cuotas_generadas
            ),
            rate_provider_fn=self._construir_rate_provider_obligacion,
            usar_suma_unica_fn=self._modo_ipc_activo,
            monto_abono_fn=self._monto_abono_en_pesos,
        )

        ajustes_usura = []
        for obligacion in obligaciones:
            # Modo (b) -- IPC + civil 6% (Sprint 43): la tasa realmente cobrada ya no
            # es tasa_efectiva_anual/tasa_moratoria_anual (ver
            # _construir_rate_provider_obligacion), es la civil legal fija, que nunca
            # es usuraria -- comparar esos dos campos (no usados para cobrar nada en
            # este modo) contra el tope de usura no tendria sentido y podria generar
            # una "sancion por usura" fantasma sobre una tasa que nunca se aplico.
            if self._modo_ipc_activo(obligacion):
                continue
            abonos_obligacion = [abono for abono in abonos if abono.obligacion_id == obligacion.id]
            ajuste = self._calcular_sancion_usura(
                obligacion, abonos_obligacion, fecha_corte, ids_con_cuotas_generadas
            )
            if ajuste is not None:
                ajustes_usura.append(ajuste)

        if ajustes_usura:
            resultado = self._aplicar_sanciones_usura(resultado, ajustes_usura, fecha_corte)

        return resultado

    def _modo_ipc_activo(self, obligacion) -> bool:
        """True si esta obligacion liquida en el modo (b) de la regla XOR del
        Sprint 43: capital indexado por IPC + interes civil puro, EN VEZ DE la tasa
        comercial -- solo cuando ambos flags estan marcados (ver docstring de la
        clase y `_validar_obligacion_comercial`, que bloquea la combinacion
        aplica_indexacion_ipc=True sin pacto_expreso_indexacion=True antes de
        llegar aqui)."""
        return bool(obligacion.aplica_indexacion_ipc) and bool(
            obligacion.pacto_expreso_indexacion
        )

    def _calcular_sancion_usura(
        self,
        obligacion,
        abonos: list,
        fecha_corte: date,
        ids_con_cuotas_generadas: set | None = None,
    ) -> dict | None:
        """Respuesta del despacho (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 2): una tasa
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
        excede el tope.

        `ids_con_cuotas_generadas` (hallazgo de revision de codigo posterior al Sprint 75
        Task 3): se propaga tal cual a _eventos_de_obligacion, igual que en liquidar(),
        para que esta liquidacion sombra tambien salte la expansion efimera via
        FamilyScheduler de una obligacion RECURRENTE que ya tiene cuotas hijas reales
        generadas -- de lo contrario la sancion se calcularia dos veces: una vez sobre el
        capital fantasma del padre (aqui) y otra vez sobre cada cuota hija real."""
        tope = calcular_tope_usura(obligacion.ibc_vigente_anual, obligacion.fecha_origen)
        if obligacion.tasa_efectiva_anual <= tope and obligacion.tasa_moratoria_anual <= tope:
            return None

        eventos = self._eventos_de_obligacion(obligacion, fecha_corte, ids_con_cuotas_generadas)
        pagos = [
            Payment(
                date=abono.fecha,
                amount=self._monto_abono_en_pesos(obligacion, abono),
                reference=abono.referencia or "",
            )
            for abono in abonos
        ]

        intereses_cobrados = (
            UniversalLiquidationService()
            .liquidar(
                eventos_causacion=eventos,
                pagos=pagos,
                fecha_corte=fecha_corte,
                rate_provider=self._construir_rate_provider_obligacion(obligacion, fecha_corte),
            )
            .final_balance()
            .interest
        )

        intereses_con_tasa_usura = (
            UniversalLiquidationService()
            .liquidar(
                eventos_causacion=eventos,
                pagos=pagos,
                fecha_corte=fecha_corte,
                rate_provider=self._construir_rate_provider_obligacion(
                    obligacion, fecha_corte, tope=tope
                ),
            )
            .final_balance()
            .interest
        )

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
            items.append(
                LiquidationItem(
                    date=fecha_corte,
                    concept=(
                        f"Sanción por usura (Art. 72 Ley 45/1990) — "
                        f"{ajuste['obligacion'].concepto}: "
                        f"exceso cobrado {ajuste['exceso']} x 2, devuelto doblado al deudor"
                    ),
                    capital_base=saldo.principal,
                    interest_rate=Decimal("0.00"),
                    interest_amount=-ajuste["sancion"],
                    indexation_amount=Decimal("0.00"),
                    payment_amount=Decimal("0.00"),
                    balance=RunningBalance(
                        date=fecha_corte, debt=saldo, event_type="SANCION_USURA"
                    ),
                    rate_source=f"Tope de usura vigente: {ajuste['tope']}% (Ley 45/1990 art. 72)",
                )
            )
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
                f"({obligacion.fecha_vencimiento}) anterior a fecha_origen "
                f"({obligacion.fecha_origen})."
            )

        # Una tasa pactada por encima del tope de usura ya NO se rechaza aqui (ver
        # respuesta del despacho, docs/Preguntas-Para-Abogado-Respondidas.md Sprint 2): se liquida
        # igual y la sancion legal (perdida del exceso, doblado) se calcula y resta
        # del saldo en liquidar() -> _calcular_sancion_usura/_aplicar_sanciones_usura.

        # Indexacion IPC (Sprint 43): el XOR real. aplica_indexacion_ipc marcado
        # implica que la obligacion abandona la tasa comercial en favor del modo (b)
        # -- eso solo es valido con pacto expreso en el titulo (ver docstring de la
        # clase). Bloquear aqui, no en tiempo de calculo, evita liquidar con un modo
        # que el titulo no autoriza.
        if obligacion.aplica_indexacion_ipc and not obligacion.pacto_expreso_indexacion:
            raise ValueError(
                f"La obligacion comercial '{obligacion.concepto}' marca 'Aplica indexación "
                f"IPC' sin 'Pacto expreso de indexación en el título': la tasa comercial "
                f"(Art. 884 C.Co.) ya incorpora un componente inflacionario, asi que no se "
                f"puede acumular con IPC salvo que el titulo autorice expresamente el modo "
                f"capital indexado + interés civil puro 6% anual en su lugar."
            )
        if self._modo_ipc_activo(obligacion) and obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion comercial '{obligacion.concepto}' tiene el modo de indexación "
                f"IPC (pacto expreso) activo, pero ese modo solo aplica a obligaciones PUNTUAL "
                f"(RECURRENTE no modela un pacto expreso por cuota individual, alcance "
                f"reducido del Sprint 43)."
            )

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

        if (
            obligacion.anatocismo_demanda_judicial
            and obligacion.anatocismo_fecha_acuerdo is not None
        ):
            raise ValueError(
                f"La obligacion comercial '{obligacion.concepto}' no puede tener "
                f"'anatocismo_demanda_judicial' y 'anatocismo_fecha_acuerdo' activos a la vez "
                f"(son dos vias habilitantes excluyentes del Art. 886 C.Co.)."
            )

        anatocismo_activo = (
            obligacion.anatocismo_demanda_judicial
            or obligacion.anatocismo_fecha_acuerdo is not None
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
                    f"La obligacion comercial '{obligacion.concepto}' tiene "
                    f"'anatocismo_fecha_acuerdo' "
                    f"({obligacion.anatocismo_fecha_acuerdo}) que no cumple el año de "
                    f"anterioridad exigido por el Art. 886 C.Co. "
                    f"(debe ser >= {fecha_minima_acuerdo})."
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
                        "label": (
                            "Capitalización de intereses "
                            "(Art. 886 C.Co. — anatocismo comercial)"
                        )
                    },
                    event_type="CAPITALIZACION_INTERESES_ANATOCISMO",
                )
            )
            fecha_evento += timedelta(days=365)
        return eventos

    def _eventos_de_obligacion(
        self, obligacion, fecha_corte: date, ids_con_cuotas_generadas: set | None = None
    ) -> list[Event]:
        valor_pesos = self._valor_en_pesos(obligacion)
        if obligacion.tipo.value == "PUNTUAL":
            eventos = [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": valor_pesos, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]
            # Modo (b) -- IPC + civil 6% (Sprint 43): en vez de la tasa comercial, se
            # indexa el capital por IPC (ver docstring de la clase). Solo llega aqui
            # si _validar_obligacion_comercial ya confirmo el pacto expreso.
            if self._modo_ipc_activo(obligacion):
                eventos.append(
                    self._evento_indexacion_ipc(
                        fecha_causacion=obligacion.fecha_origen,
                        capital=valor_pesos,
                        concepto=obligacion.concepto,
                        fecha_corte=fecha_corte,
                    )
                )
            eventos.extend(self._eventos_anatocismo(obligacion, fecha_corte))
            evento_costas = _evento_costas_procesales(
                obligacion, pretensiones_reconocidas=valor_pesos
            )
            if evento_costas is not None:
                eventos.append(evento_costas)
            return eventos

        # RECURRENTE
        # Sprint 75 Task 3 -- mismo patron y misma razon que
        # CivilFamiliaStrategy._eventos_de_obligacion (ver el comentario extenso
        # de esa clase mas arriba en este archivo): si esta obligacion ya tiene
        # cuotas mensuales reales generadas y persistidas (Obligacion PUNTUAL
        # hijas, generar_cuotas_mensuales), esas cuotas ya vienen incluidas en
        # `obligaciones` como filas independientes -- la obligacion RECURRENTE
        # padre NO debe generar NINGUN evento de capital propio en ese caso,
        # o el capital se duplicaria (una vez via la expansion efimera de
        # FamilyScheduler de abajo, otra vez via cada cuota hija real). El
        # criterio de skip es unicamente la membresia en
        # ids_con_cuotas_generadas (obligacion_padre_id real, ver liquidar()
        # arriba) -- NO depende de tipo_reajuste_anual: ComercialStrategy
        # tambien puede tener cuotas hijas generadas con tipo_reajuste_anual =
        # NINGUNO (Sprint 75 Task 1), asi que exigir reajuste activo ademas de
        # la membresia reintroduciria el mismo bug ya corregido en
        # CivilFamiliaStrategy (ver
        # test_civil_familia_recurrente_sin_reajuste_y_cuotas_generadas_no_duplica_capital).
        if obligacion.id in (ids_con_cuotas_generadas or set()):
            return []

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
        real que se devuelve al usuario.

        Modo (b) -- IPC + civil 6% (Sprint 43): la tasa comercial pactada
        (remuneratoria/moratoria) NO se usa en absoluto -- se reemplaza por una sola
        tasa civil legal plana (Art. 1617 C.C.) para todo el periodo, sobre el
        capital ya indexado (`usar_suma_unica`, ver liquidar()). `tope` no aplica
        aqui: la sancion de usura ya se salta esta obligacion por completo (ver
        liquidar())."""
        if self._modo_ipc_activo(obligacion):
            return self._rate_provider_tasa_plana(
                obligacion.fecha_origen,
                fecha_corte,
                self._tasa_civil_anual_pct(obligacion.fecha_origen),
                source="Interés civil puro (Art. 1617 C.C.) — pacto expreso de indexación IPC",
            )

        tasa_remuneratoria_anual = obligacion.tasa_efectiva_anual
        tasa_moratoria_anual = obligacion.tasa_moratoria_anual
        if tope is not None:
            tasa_remuneratoria_anual = min(tasa_remuneratoria_anual, tope)
            tasa_moratoria_anual = min(tasa_moratoria_anual, tope)

        provider = MemoryRateProvider()
        tasa_moratoria_diaria = EffectiveRateConverter.annual_to_daily(tasa_moratoria_anual)

        if obligacion.tipo.value == "PUNTUAL":
            tasa_remuneratoria_diaria = EffectiveRateConverter.annual_to_daily(
                tasa_remuneratoria_anual
            )
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

    Indexacion IPC (Sprint 43, respuesta del despacho -- condicional, excluyente
    con la indemnizacion moratoria del Art. 65 CST sobre el mismo rubro/periodo):
    el conteo de 360 dias (arriba) cuantifica la base temporal de las prestaciones;
    IPC actualiza ese valor resultante por perdida de poder adquisitivo -- son
    complementarios en concepto, pero el despacho exige elegir uno u otro, nunca
    los dos a la vez sobre el mismo saldo:
      - `aplica_indexacion_ipc` marcado + SIN mora (buena fe probada, excepcion 1
        del despacho): se indexa `monto_prestaciones` por IPC desde `fecha_fin`
        (cuando las prestaciones se hacen exigibles) hasta la fecha de corte.
      - `aplica_indexacion_ipc` marcado + CON mora: la indemnizacion moratoria del
        Art. 65 CST prevalece (via legal especifica, mas gravosa que IPC) y el IPC
        NO se aplica -- se agrega una alerta NO bloqueante "Doble Actualización
        Prohibida" a `LiquidationResult.alertas` en vez de bloquear la liquidacion
        (mismo mecanismo del Sprint 36, ver `_agregar_alerta`).
      - `aplica_indexacion_ipc` sin marcar: comportamiento identico a antes de este
        sprint (sin IPC, la mora se resuelve exclusivamente via SANCION_MORATORIA).

    Excepcion 2 del despacho (reliquidaciones pensionales, traer el IBL a valor
    presente) queda documentada como limitacion conocida, NO implementada: revisando
    `app/engine/labor/ibl.py` (Sprint 17), `calcular_ibl` ya indexa por IPC cada
    salario historico, pero es una funcion de calculo aislada, nunca conectada a
    `AreaRegistry`/`LiquidationResult` -- no existe hoy un concepto de "reliquidacion"
    como operacion de liquidar() distinta de una liquidacion normal sobre la que
    enganchar esta excepcion sin construir esa infraestructura desde cero (fuera de
    alcance de este sprint, ver "Alcance explícitamente excluido").

    Seguridad social (cotizaciones IBC, pension, salud, ARL, FSP) es opt-in
    via el flag `incluir_seguridad_social` de la obligacion (requiere ademas
    `nivel_riesgo_arl`, I-V) -- ver docs/Pendientes.md, Sprint 16, y
    docs/superpowers/specs/2026-07-18-area-laboral-design.md.

    Salarios y prestaciones dejadas de percibir (Sprint 93, categoria
    `SALARIOS_DEJADOS_DE_PERCIBIR`, ver `app.core.constants.CATEGORIAS_LABORAL`):
    submodo enteramente distinto del finiquito de arriba, para reconstruir el
    salario + las 4 prestaciones estatutarias que un trabajador habria
    devengado durante un periodo en que NO estuvo contratado (reintegro por
    despido declarado nulo, "salarios caidos"), año calendario por año
    calendario, con el salario reajustado el 1 de enero de cada año por IPC o
    SMMLV. `liquidar()` desvia a `_liquidar_salarios_dejados_de_percibir` para
    esta categoria ANTES de llegar a la logica de finiquito de abajo (que no
    aplica: no hay "fecha de terminacion" ni mora del Art. 65 CST sobre un
    contrato que nunca estuvo vigente en ese periodo).

    Decision de diseno (sin necesitar confirmacion del despacho, ver
    docs/Pendientes.md Sprint 93): esta categoria nueva coexiste con
    `LIQUIDACION_CONTRATO_LABORAL` sin romper el invariante "1 obligacion = 1
    contrato" del Sprint 3 -- una obligacion `SALARIOS_DEJADOS_DE_PERCIBIR` no
    representa un contrato, representa la reconstruccion de un periodo SIN
    contrato, asi que modelarla como una obligacion propia (RECURRENTE, con
    `fecha_inicio`/`fecha_fin` marcando el periodo completo, en vez de una
    serie de "cuotas" mensuales reales como Civil/Familia) es coherente con lo
    que el dato representa, no una excepcion al invariante. `_validar_
    obligacion_laboral` reabre `TipoObligacion.RECURRENTE` (que el Sprint 75
    dejo bloqueado con ValueError para toda el area) EXCLUSIVAMENTE para esta
    categoria, y bloquea a proposito `despido_injustificado`/
    `incluir_seguridad_social` en ella (conceptos de finiquito que no aplican
    a un periodo sin contrato vigente -- fuera de alcance de este sprint, no
    un olvido).
    """

    soporta_indexacion_ipc = True

    @cache_de_liquidacion()
    def liquidar(self, obligaciones: list, abonos: list, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")
        if len(obligaciones) != 1:
            raise ValueError(
                "El area Laboral liquida un solo contrato (una obligacion) por expediente."
            )

        obligacion = obligaciones[0]
        self._resolver_valor_pactado(obligacion)
        self._validar_obligacion_laboral(obligacion)

        # Sprint 93: SALARIOS_DEJADOS_DE_PERCIBIR se desvia por completo antes
        # de la logica de finiquito de abajo -- ver el docstring de la clase
        # (arriba) para el porque. Bloqueada explicitamente por
        # `_validar_obligacion_laboral`: `despido_injustificado`,
        # `incluir_seguridad_social` (asi que tampoco hay eventos_laborales/
        # incapacidades que procesar) y toda la mora del Art. 65 CST (no hay
        # "fecha de terminacion" de un contrato que nunca estuvo vigente en
        # este periodo).
        if obligacion.categoria == CATEGORIA_SALARIOS_DEJADOS_DE_PERCIBIR:
            return self._liquidar_salarios_dejados_de_percibir(obligacion, abonos, fecha_corte)

        # dias_trabajados (calendario real, resta simple, SIN +1): sigue
        # alimentando la seguridad social/incapacidades mas abajo en este
        # metodo -- fuera de alcance del Sprint 30 (la confirmacion del
        # despacho de conteo inclusivo aplico especificamente a prestaciones
        # sociales, no se extendio a cotizaciones de seguridad social en
        # este sprint).
        dias_trabajados = (obligacion.fecha_fin - obligacion.fecha_inicio).days
        eventos, monto_prestaciones = self._eventos_prestaciones_sociales(obligacion)

        if obligacion.incluir_seguridad_social:
            self._eventos_seguridad_social(obligacion, dias_trabajados, eventos)

        # fecha_pago_total (si existe) es cuando realmente se extinguio la
        # deuda; nunca puede ser posterior a fecha_corte para efectos de este
        # reporte -- si el pago real fue despues del corte elegido, la mora
        # se calcula solo hasta el corte (foto historica), no hasta el pago.
        hay_mora = self._eventos_mora_articulo_65(
            obligacion, fecha_corte, monto_prestaciones, eventos
        )

        # Indemnizacion por despido injustificado, Art. 64 CST (Sprint 92) --
        # concepto legal distinto de la moratoria de arriba (Art. 65 CST):
        # compensa la terminacion sin justa causa, no la mora en el pago de
        # prestaciones ya causadas. Deliberadamente independiente del bloque
        # de mora de arriba (ninguno excluye al otro): el despacho confirmo
        # que ambos son compatibles y pueden coexistir en el mismo expediente
        # (ver docs/Preguntas-Para-Abogado-Abiertas.md, Sprint 92), asi que el
        # evento se agrega solo si `despido_injustificado` esta marcado, sin
        # depender de `hay_mora`.
        self._eventos_despido_injustificado(obligacion, eventos)

        # Indexacion IPC (Sprint 43): ver docstring de la clase. Solo se agrega el
        # evento de indexacion cuando NO hay mora (excepcion 1, buena fe probada) --
        # si hay mora, la moratoria prevalece y se registra una alerta no bloqueante
        # despues de liquidar (ver mas abajo, necesita el LiquidationResult final).
        aplica_ipc_sin_mora = (
            obligacion.aplica_indexacion_ipc
            and not hay_mora
            and monto_prestaciones > Decimal("0.00")
        )
        if aplica_ipc_sin_mora:
            eventos.append(
                self._evento_indexacion_ipc(
                    fecha_causacion=obligacion.fecha_fin,
                    capital=monto_prestaciones,
                    concepto="Prestaciones sociales",
                    fecha_corte=fecha_corte,
                )
            )

        # Descuentos del empleador (Sprint 44, punto 3): se inyectan como
        # eventos PAYMENT mas -- mismo mecanismo de pagos/allocation que ya
        # usan los abonos (AllocationEngine.allocate, via LiquidationCore),
        # no uno nuevo. `es_legal` es solo metadata descriptiva para que el
        # reporte distinga un descuento autorizado de uno que no lo fue (la
        # etiqueta queda en el concepto de la fila); matematicamente ambos
        # reducen el neto adeudado exactamente igual.
        self._eventos_descuentos_empleador(obligacion, eventos)

        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos
        ]

        service = UniversalLiquidationService()
        resultado = service.liquidar(
            eventos_causacion=eventos,
            pagos=pagos,
            fecha_corte=fecha_corte,
        )
        # Sin rate_provider: la tasa diaria generica de UniversalLiquidationService
        # queda en 0 por defecto. Toda la mora del area Laboral ya esta resuelta
        # en el evento SANCION_MORATORIA -- pasar un rate_provider aqui
        # duplicaria el castigo por mora.

        if obligacion.aplica_indexacion_ipc and hay_mora:
            resultado = self._agregar_alerta(
                resultado,
                "Doble Actualización Prohibida: hay indemnización moratoria (Art. 65 CST) "
                "vigente sobre las prestaciones sociales de este contrato -- la indexación "
                "IPC no se aplicó sobre el mismo rubro/periodo (la moratoria prevalece).",
            )
        return resultado

    def _resolver_valor_pactado(self, obligacion) -> None:
        """Sprint 44/96: `obligacion.valor` digitado a mano se descarta y se
        resuelve en memoria (nunca se persiste aqui -- eso lo hace el
        formulario al guardar), para que la liquidacion siempre use el dato
        mas actualizado.

        es_smmlv (Sprint 44, punto 1): se resuelve desde el SMLMV vigente del
        año de origen del contrato, incluso si se corrigio despues de que la
        obligacion se guardo.

        salario_diario/dias_laborados_semana (Sprint 96): mismo patron que
        es_smmlv arriba, pero para trabajo domestico por dias/jornada
        parcial -- se resuelve desde el salario pactado por dia via
        salario_diario_a_mensual. Respuesta del despacho (22/08/2026): "no
        existe diferencia algebraica en las formulas de liquidacion tras la
        Ley 1788" -- se reutiliza LaborScheduler sin cambios, solo con esta
        base convertida.
        """
        if obligacion.es_smmlv:
            obligacion.valor = get_smlmv_for_year(obligacion.fecha_origen.year)
        if obligacion.salario_diario is not None and obligacion.dias_laborados_semana is not None:
            obligacion.valor = salario_diario_a_mensual(
                obligacion.salario_diario, obligacion.dias_laborados_semana
            )

    def _eventos_prestaciones_sociales(self, obligacion) -> tuple[list, Decimal]:
        """Genera los eventos de capital de las 4 prestaciones estatutarias
        (cesantias/intereses/prima/vacaciones) via LaborScheduler mas costas
        procesales, si aplican.

        dias_trabajados_prestaciones (Sprint 30, corregido 2026-08-03):
        conteo inclusivo (+1) sobre base comercial de 360 dias (12 meses de
        30 dias) -- confirmado por el despacho para cesantias/intereses/
        prima/vacaciones (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 3).
        NO es el mismo valor que `dias_trabajados` (calendario real) que usa
        seguridad social.
        """
        dias_trabajados_prestaciones = CalendarUtils.dias_comerciales_360(
            obligacion.fecha_inicio, obligacion.fecha_fin
        )
        eventos = LaborScheduler(
            salario_base=obligacion.valor,
            dias_trabajados=dias_trabajados_prestaciones,
            fecha_liquidacion=obligacion.fecha_fin,
        ).generate()

        monto_prestaciones = sum((e.payload["amount"] for e in eventos), Decimal("0.00"))

        evento_costas = _evento_costas_procesales(
            obligacion, pretensiones_reconocidas=monto_prestaciones
        )
        if evento_costas is not None:
            eventos.append(evento_costas)

        return eventos, monto_prestaciones

    def _eventos_seguridad_social(self, obligacion, dias_trabajados: int, eventos: list) -> None:
        """Cotizaciones IBC (pension, salud, ARL, FSP) e incapacidades --
        opt-in via `obligacion.incluir_seguridad_social` (ver
        docs/Pendientes.md, Sprint 16, y
        docs/superpowers/specs/2026-07-18-area-laboral-design.md). Muta
        `eventos` directamente en vez de retornar una lista nueva.
        """
        dias_suspension = sum(
            (evento.fecha_fin - evento.fecha_inicio).days
            for evento in obligacion.eventos_laborales
            if evento.tipo.value == "SUSPENSION"
        )
        # IBC_Seguridad_Social = max(salario_proporcional, 1 SMMLV) --
        # solo para trabajo domestico por dias/jornada parcial (Sprint
        # 96, respuesta del despacho 22/08/2026): la cotizacion a
        # seguridad social nunca puede basarse en un IBC menor a 1 SMMLV,
        # aunque el salario proporcional real si sea menor. NO se aplica
        # este piso a las prestaciones sociales de arriba (cesantias/
        # prima/vacaciones), que siguen usando el salario proporcional
        # real -- ni al resto de contratos Laborales (salario_diario
        # None), fuera del alcance de esta respuesta.
        base_seguridad_social = obligacion.valor
        if obligacion.salario_diario is not None:
            base_seguridad_social = calcular_ibc_seguridad_social_domestico(
                salario_proporcional=obligacion.valor,
                smmlv_mensual=get_smlmv_for_year(obligacion.fecha_fin.year),
            )
        cotizaciones = SeguridadSocialCalculator.calcular(
            salario_base=base_seguridad_social,
            dias_trabajados=dias_trabajados,
            dias_suspension=dias_suspension,
            nivel_riesgo_arl=obligacion.nivel_riesgo_arl,
            fecha_referencia=obligacion.fecha_fin,
        )
        for concepto, monto, etiqueta in [
            (
                "COTIZACION_PENSION",
                cotizaciones.monto_pension,
                "Cotizacion Pension (seguridad social no pagada)",
            ),
            (
                "COTIZACION_SALUD",
                cotizaciones.monto_salud,
                "Cotizacion Salud (seguridad social no pagada)",
            ),
            (
                "COTIZACION_ARL",
                cotizaciones.monto_arl,
                "Cotizacion ARL (seguridad social no pagada)",
            ),
            (
                "COTIZACION_FSP",
                cotizaciones.monto_fsp,
                "Cotizacion FSP (Fondo de Solidaridad Pensional)",
            ),
        ]:
            if monto > Decimal("0.00"):
                eventos.append(
                    Event(
                        date=obligacion.fecha_fin,
                        payload={"amount": monto, "label": etiqueta},
                        event_type=concepto,
                    )
                )

        for evento in obligacion.eventos_laborales:
            if evento.tipo.value == "SUSPENSION":
                eventos.append(
                    Event(
                        date=evento.fecha_fin,
                        payload={
                            "amount": Decimal("0.00"),
                            "label": (
                                f"Suspension ({evento.motivo_suspension.value}) "
                                f"{evento.fecha_inicio}-{evento.fecha_fin}: no causa ARL"
                            ),
                        },
                        event_type="SUSPENSION_INFORMATIVA",
                    )
                )
            else:
                dias_incapacidad = (evento.fecha_fin - evento.fecha_inicio).days
                desglose = IncapacidadCalculator.calcular(
                    tipo=evento.tipo,
                    ibc_mensual=cotizaciones.ibc_mensual,
                    dias_incapacidad=dias_incapacidad,
                )
                for tramo in desglose.tramos:
                    es_empleador = tramo.pagador == "EMPLEADOR"
                    eventos.append(
                        Event(
                            date=evento.fecha_fin,
                            payload={
                                "amount": tramo.monto if es_empleador else Decimal("0.00"),
                                "label": (
                                    f"Incapacidad {evento.tipo.value} dias {tramo.dias} - "
                                    f"{tramo.pagador} ({tramo.porcentaje:.2%}): "
                                    f"${tramo.monto:,.2f}"
                                ),
                            },
                            event_type="INCAPACIDAD_EMPLEADOR"
                            if es_empleador
                            else "INCAPACIDAD_INFORMATIVA",
                        )
                    )

    def _eventos_mora_articulo_65(
        self, obligacion, fecha_corte: date, monto_prestaciones: Decimal, eventos: list
    ) -> bool:
        """Indemnizacion moratoria Art. 65 CST -- muta `eventos` y retorna
        `hay_mora`, que el resto de `liquidar()` necesita para la exclusion
        mutua con la indexacion IPC (ver docstring de la clase).
        """
        if obligacion.fecha_pago_total is not None:
            fecha_referencia_mora = min(obligacion.fecha_pago_total, fecha_corte)
        else:
            fecha_referencia_mora = fecha_corte

        hay_mora = False
        if fecha_referencia_mora > obligacion.fecha_fin:
            monto_adeudado = monto_prestaciones
            mora = MoratoryIndemnityCalculator.calcular(
                salario_mensual=obligacion.valor,
                monto_adeudado=monto_adeudado,
                fecha_terminacion=obligacion.fecha_fin,
                fecha_pago_o_corte=fecha_referencia_mora,
            )
            if mora.total > Decimal("0.00"):
                hay_mora = True
                eventos.append(
                    Event(
                        date=fecha_referencia_mora,
                        payload={
                            "amount": mora.total,
                            "label": "Indemnizacion moratoria Art. 65 CST",
                        },
                        event_type="SANCION_MORATORIA",
                    )
                )
        return hay_mora

    def _eventos_despido_injustificado(self, obligacion, eventos: list) -> None:
        """Indemnizacion por despido injustificado, Art. 64 CST (Sprint 92).
        Muta `eventos` directamente; no-op si `despido_injustificado` no esta
        marcado.
        """
        if obligacion.despido_injustificado:
            indemnizacion_despido = DismissalIndemnityCalculator.calcular(
                tipo_contrato=obligacion.tipo_contrato_laboral,
                salario_mensual=obligacion.valor,
                fecha_ingreso=obligacion.fecha_inicio,
                fecha_terminacion=obligacion.fecha_fin,
                despido_injustificado=True,
                smlmv_mensual=get_smlmv_for_year(obligacion.fecha_fin.year),
                fecha_fin_pactada=obligacion.fecha_fin_pactada,
            )
            if indemnizacion_despido.total > Decimal("0.00"):
                eventos.append(
                    Event(
                        date=obligacion.fecha_fin,
                        payload={
                            "amount": indemnizacion_despido.total,
                            "label": (
                                "Indemnizacion por despido injustificado Art. 64 CST "
                                f"({indemnizacion_despido.regimen}, "
                                f"{indemnizacion_despido.dias_indemnizacion} dias)"
                            ),
                        },
                        event_type="INDEMNIZACION_DESPIDO",
                    )
                )

    def _eventos_descuentos_empleador(self, obligacion, eventos: list) -> None:
        """Descuentos del empleador (Sprint 44, punto 3): se inyectan como
        eventos PAYMENT mas -- mismo mecanismo de pagos/allocation que ya
        usan los abonos. `es_legal` es solo metadata descriptiva.
        """
        for descuento in obligacion.descuentos_laborales:
            calificacion = "legal" if descuento.es_legal else "ilegal"
            etiqueta = f"Descuento del empleador ({calificacion})"
            if descuento.motivo:
                etiqueta += f": {descuento.motivo}"
            eventos.append(
                Event(
                    date=descuento.fecha,
                    payload={"amount": descuento.monto, "label": etiqueta},
                    event_type="PAYMENT",
                )
            )

    def _liquidar_salarios_dejados_de_percibir(
        self, obligacion, abonos: list, fecha_corte: date
    ) -> LiquidationResult:
        """Sprint 93. `obligacion` ya paso `_validar_obligacion_laboral` (tipo
        RECURRENTE, fecha_inicio/fecha_fin pobladas, sin despido_injustificado
        ni incluir_seguridad_social) cuando `liquidar()` desvia aqui. Genera
        los eventos de capital (SALARIO_DEJADO_DE_PERCIBIR + las 4
        prestaciones, un bloque por año calendario) via
        `generar_eventos_salarios_dejados_de_percibir` -- ese modulo hace todo
        el trabajo de dominio (bloques anuales, reajuste IPC/SMMLV, divisores
        360/720); esta funcion solo lo conecta con costas procesales/abonos y
        el motor de liquidacion consolidado, igual patron que el resto de
        AreaStrategy.

        Sin rate_provider (igual que el finiquito de arriba): no hay mora del
        Art. 65 CST sobre un periodo sin contrato vigente, asi que la tasa
        diaria generica de UniversalLiquidationService se queda en 0 -- el
        "GRAN TOTAL" es la suma de los eventos de capital, reducida solo por
        los abonos que se hayan registrado.
        """
        eventos = generar_eventos_salarios_dejados_de_percibir(
            salario_inicial=obligacion.valor,
            fecha_inicio=obligacion.fecha_inicio,
            fecha_fin=obligacion.fecha_fin,
            tipo_reajuste=obligacion.tipo_reajuste_anual,
        )

        gran_total = sum((e.payload["amount"] for e in eventos), Decimal("0.00"))
        evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=gran_total)
        if evento_costas is not None:
            eventos.append(evento_costas)

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

    def _validar_obligacion_laboral(self, obligacion) -> None:
        es_salarios_dejados = obligacion.categoria == CATEGORIA_SALARIOS_DEJADOS_DE_PERCIBIR
        if es_salarios_dejados:
            if obligacion.tipo.value != "RECURRENTE":
                raise ValueError(
                    "La categoria 'Salarios y prestaciones dejadas de percibir' debe ser "
                    "RECURRENTE -- representa un periodo entero sin contrato vigente "
                    "(fecha_inicio/fecha_fin del periodo), no un hecho puntual."
                )
            if obligacion.despido_injustificado or obligacion.incluir_seguridad_social:
                raise ValueError(
                    "La categoria 'Salarios y prestaciones dejadas de percibir' no admite "
                    "indemnizacion por despido injustificado ni cotizaciones de seguridad "
                    "social (Sprint 93, fuera de alcance) -- desmarcar esas casillas."
                )
        elif obligacion.tipo.value != "PUNTUAL":
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
        if es_salarios_dejados:
            # La eleccion del indice de reajuste NO es discrecional del
            # abogado (respuesta del despacho, Sprint 93, 22/08/2026): se
            # deriva del salario base y el año de causacion.
            tipo_esperado = determinar_tipo_reajuste_salarios_dejados_de_percibir(
                salario_base=obligacion.valor,
                anio_causacion=obligacion.fecha_inicio.year,
            )
            if obligacion.tipo_reajuste_anual != tipo_esperado:
                raise ValueError(
                    "El indice de reajuste para 'Salarios y prestaciones dejadas de percibir' "
                    "no es discrecional (respuesta del despacho, Sprint 93): para este salario "
                    f"base y año de causacion corresponde {tipo_esperado.value}, no "
                    f"{obligacion.tipo_reajuste_anual.value}."
                )
        if obligacion.pagada and obligacion.fecha_pago_total is None:
            raise ValueError("Una obligacion marcada como pagada debe tener 'fecha_pago_total'.")
        if obligacion.incluir_seguridad_social and not obligacion.nivel_riesgo_arl:
            raise ValueError(
                "Si se incluyen cotizaciones de seguridad social, 'nivel_riesgo_arl' "
                "(I-V) es obligatorio."
            )
        # despido_injustificado/tipo_contrato_laboral/fecha_fin_pactada (Sprint 92):
        # un contrato a termino fijo/obra-labor con despido injustificado necesita
        # el plazo pactado para que DismissalIndemnityCalculator pueda calcular el
        # tiempo restante -- se valida aqui para dar un mensaje claro antes de
        # llegar al calculador (que tambien lo exige, ver dismissal_indemnity.py).
        if (
            obligacion.despido_injustificado
            and obligacion.tipo_contrato_laboral.value in ("FIJO", "OBRA_LABOR")
            and obligacion.fecha_fin_pactada is None
        ):
            raise ValueError(
                "Un contrato a termino fijo/obra-labor con despido injustificado "
                "necesita 'fecha_fin_pactada' (el plazo originalmente pactado) para "
                "calcular la indemnizacion del Art. 64 CST."
            )
        if obligacion.eventos_laborales and not obligacion.incluir_seguridad_social:
            raise ValueError(
                "Hay eventos contractuales (suspension/incapacidad) registrados, pero "
                "'incluir_seguridad_social' no esta activado. Marca la casilla 'Incluir "
                "cotizaciones de seguridad social no pagadas' para que estos eventos se "
                "reflejen en la liquidacion."
            )

        for evento in obligacion.eventos_laborales:
            if (
                evento.fecha_inicio < obligacion.fecha_inicio
                or evento.fecha_fin > obligacion.fecha_fin
            ):
                raise ValueError(
                    f"El evento contractual del {evento.fecha_inicio} al {evento.fecha_fin} "
                    "cae fuera del rango del contrato "
                    f"({obligacion.fecha_inicio} a {obligacion.fecha_fin})."
                )

        eventos_ordenados = sorted(obligacion.eventos_laborales, key=lambda e: e.fecha_inicio)
        for anterior, siguiente in zip(eventos_ordenados, eventos_ordenados[1:], strict=False):
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

    Indexacion IPC (Sprint 43, respuesta del despacho -- condicional, la conversion
    SMLMV/UVT prevalece): la prohibicion general del despacho ("bloquear IPC si el
    rubro esta parametrizado en UVT/SMLMV actualizado a la fecha de pago") no es
    alcanzable con el motor actual -- `resolver_base_sancion` (arriba) SIEMPRE
    resuelve la unidad SMLMV/UVT segun `fecha_origen` (la fecha DEL HECHO, no la de
    pago; no existe en este motor un modo que reconvierta la multa a la unidad
    vigente en la fecha de pago/corte), asi que toda obligacion sancionatoria cae
    siempre en la EXCEPCION del despacho ("el valor de la multa se anclo a UVT/SMLMV
    a la fecha del hecho -- faltas antiguas"), donde IPC SI es valido, desde la
    exigibilidad (aqui, `fecha_origen`, a falta de un campo propio de "firmeza del
    acto") hasta el pago efectivo (aqui, la fecha de corte). Mismo criterio que
    `CivilFamiliaStrategy` ya documenta para su propia combinacion inalcanzable: no
    se agrega un guard en tiempo de ejecucion para una rama que el modelo de datos
    actual no puede producir. Si en el futuro se modela una reconversion a la
    unidad vigente en la fecha de pago, esta nota deja de ser valida y hay que
    revisar este bloqueo.
    """

    soporta_indexacion_ipc = True

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
            eventos_fn=lambda obligacion: self._eventos_de_obligacion(obligacion, fecha_corte),
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

    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> list[Event]:
        monto_pesos = resolver_base_sancion(obligacion.fecha_origen, obligacion.cantidad_smlmv_uvt)
        eventos = [
            Event(
                date=obligacion.fecha_origen,
                payload={"amount": monto_pesos, "label": obligacion.concepto},
                event_type=obligacion.categoria,
            )
        ]
        if obligacion.aplica_indexacion_ipc:
            eventos.append(
                self._evento_indexacion_ipc(
                    fecha_causacion=obligacion.fecha_origen,
                    capital=monto_pesos,
                    concepto=obligacion.concepto,
                    fecha_corte=fecha_corte,
                )
            )
        evento_costas = _evento_costas_procesales(obligacion, pretensiones_reconocidas=monto_pesos)
        if evento_costas is not None:
            eventos.append(evento_costas)
        return eventos

    def _construir_rate_provider_obligacion(
        self, obligacion, fecha_corte: date
    ) -> MemoryRateProvider:
        return self._rate_provider_tasa_plana(
            obligacion.fecha_origen, fecha_corte, obligacion.tasa_efectiva_anual
        )


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
    respuesta del despacho en docs/Preguntas-Para-Abogado-Respondidas.md: el PDF trae un 50% en una
    seccion y un 30% en otra, pero el tope legal absoluto y definitivo es el 50%
    acumulado, no ambos a la vez):
    - honorarios fijos + cuota litis <= 50% del beneficio obtenido. Si se excede,
      se bloquea la liquidacion con una alerta de riesgo disciplinario ("Honorarios
      Desproporcionados - Art. 35 Num. 4 Ley 1123/2007").

    No soporta obligaciones RECURRENTE.

    Indexacion IPC (Sprint 43, respuesta del despacho -- SI, habilitada por defecto
    [checkbox visible, no oculto], compatible con el interes civil): formula EXACTA
    exigida por el despacho --
        Capital_Honorarios x (IPC_Final / IPC_Inicial)
            + Interés_Civil_6%_Anual(Capital_Actualizado)
    -- IPC_Inicial es el indice del mes en que la obligacion se hizo exigible o se
    presento la cuenta de cobro, que en este modelo es `fecha_origen` (mismo campo
    que ya representa esa fecha para el resto de esta clase). Implementacion:
    cuando `aplica_indexacion_ipc` esta marcado, se agrega un evento de indexacion
    IPC sobre `total_honorarios` (primer termino) y la liquidacion corre en modo
    Suma Unica (`usar_suma_unica`, interes sobre capital YA indexado) con una tasa
    civil FIJA del 6% anual (`_tasa_civil_anual_pct`, Art. 1617 C.C. -- NO la
    `tasa_efectiva_anual` pactada de esta obligacion, que el despacho no menciona en
    la formula) para el segundo termino. Sin el checkbox marcado, el comportamiento
    es identico a antes de este sprint (tasa pactada, sin indexar).

    Limitaciones conocidas, documentadas en vez de construidas (fuera de alcance
    razonable de este sprint, ver docs/Pendientes.md Sprint 43):
    - "De oficio" (automatico, sin checkbox, en etapa declarativa/restitucion de
      mutuos) vs. "a peticion de parte" (con checkbox, en etapa ejecutiva): este
      modelo no tiene un concepto de "etapa procesal" del expediente, asi que el
      checkbox queda siempre a discrecion del abogado (equivalente al caso "a
      peticion de parte") en vez de auto-marcarse en la etapa declarativa.
    - Alerta "Improcedente por acumulación" (titulo sin IPC previsto + intereses
      comerciales cobrados en etapa ejecutiva): esta clase no distingue "tipo de
      interes" (civil vs. comercial) ni tiene un campo de "IPC previsto en el
      titulo", asi que esta alerta especifica no se genera.
    - La pregunta de seguimiento sobre si es juridicamente valido cobrar el interes
      civil SOBRE el capital ya indexado sigue abierta
      (`Preguntas-Para-Abogado-Abiertas.md`, "Sprint 43 (seguimiento)") -- esta
      clase implementa la formula tal cual la dio el despacho, sin ajustes
      especulativos.
    """

    soporta_indexacion_ipc = True

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
            eventos_fn=lambda obligacion: self._eventos_de_obligacion(obligacion, fecha_corte),
            rate_provider_fn=self._construir_rate_provider_obligacion,
            usar_suma_unica_fn=lambda obligacion: bool(obligacion.aplica_indexacion_ipc),
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
                f"excede el tope legal del {tope_total_pct}% del beneficio obtenido "
                f"({tope_total})."
            )

    def _cuota_litis_monto(self, obligacion) -> Decimal:
        return obligacion.beneficio_obtenido * obligacion.cuota_litis_pactada_pct / Decimal("100")

    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> list[Event]:
        cuota_litis_monto = self._cuota_litis_monto(obligacion)
        total_honorarios = obligacion.honorarios_fijos_pactados + cuota_litis_monto

        eventos = [
            Event(
                date=obligacion.fecha_origen,
                payload={"amount": total_honorarios, "label": obligacion.concepto},
                event_type=obligacion.categoria,
            )
        ]
        if obligacion.aplica_indexacion_ipc:
            eventos.append(
                self._evento_indexacion_ipc(
                    fecha_causacion=obligacion.fecha_origen,
                    capital=total_honorarios,
                    concepto=obligacion.concepto,
                    fecha_corte=fecha_corte,
                )
            )
        evento_costas = _evento_costas_procesales(
            obligacion, pretensiones_reconocidas=obligacion.beneficio_obtenido
        )
        if evento_costas is not None:
            eventos.append(evento_costas)
        return eventos

    def _construir_rate_provider_obligacion(
        self, obligacion, fecha_corte: date
    ) -> MemoryRateProvider:
        # Sprint 43: con IPC activo, el segundo termino de la formula del despacho es
        # una tasa civil FIJA del 6% anual (Art. 1617 C.C.), no la tasa_efectiva_anual
        # pactada de esta obligacion -- ver docstring de la clase.
        if obligacion.aplica_indexacion_ipc:
            return self._rate_provider_tasa_plana(
                obligacion.fecha_origen,
                fecha_corte,
                self._tasa_civil_anual_pct(obligacion.fecha_origen),
                source="Interés civil puro (Art. 1617 C.C.) — capital ya indexado por IPC",
            )
        return self._rate_provider_tasa_plana(
            obligacion.fecha_origen, fecha_corte, obligacion.tasa_efectiva_anual
        )


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

    Indexacion IPC (Sprint 43, respuesta del despacho -- SI, pero intrinsecamente
    ligada al Art. 867-1 E.T., NO como opcion paralela libre): a diferencia de
    Civil/Familia, aqui no hay un checkbox manual -- IPC se activa automaticamente
    por el trigger de mora (`aplica_actualizacion_867_1`, mora > 3 años / 1095 dias,
    equivalente a la "mora > 36 meses" del despacho) y es mutuamente excluyente con
    el interes de mora en su componente inflacionario:
    - "Sanciones" (SANCION_*): bloquea el interes de mora, aplica EXCLUSIVAMENTE el
      factor IPC (ver `_construir_rate_provider_obligacion`, ya devuelve 0% para
      este caso desde el Sprint 15).
    - "Impuesto" (IMPUESTO_A_CARGO): intereses de mora + actualizacion IPC (AMBOS),
      topando la tasa combinada al techo de usura PLENA -- `calcular_indexacion_867_1_topada`
      (Sprint 15, ya implementado y aprobado por el despacho con su propio calculo de
      usura basado en tramos historicos de IBC, `calcular_interes_usura_plena`, NO
      `usury_validator.calcular_tope_usura` -- ese motor exige `ibc_vigente_anual`,
      un campo que Tributario no captura; se reutiliza el mecanismo de techo que YA
      existe para esta area en vez de duplicar otro). Lo que agrega este sprint es
      la ALERTA no bloqueante cuando el techo realmente recorta la indexacion (ver
      `liquidar()`, "Techo de usura alcanzado").
    - Prohibicion de doble cobro: si la obligacion ya incorpora su propia proteccion
      inflacionaria (`protegida_inflacion_uvr`, ej. UVR), se bloquea con ValueError
      si ademas se dispararia la indexacion IPC del Art. 867-1 (ver `liquidar()`).
    - Mora <= 3 años: sin cambios para ningun rubro (solo interes E.T. 635, sin IPC).

    Esto exige que cada obligacion corra en su propio LiquidationCore (via
    _liquidar_por_obligacion, mismo patron que Comercial/CivilFamilia desde el Sprint 21):
    un solo PendingDebt/rate provider compartido para todo el expediente no puede darle
    0% de interes a una sancion y la tasa E.T. 635 al impuesto al mismo tiempo.
    """

    soporta_indexacion_ipc = True

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
            # Prohibicion de doble cobro (Sprint 43): si esta obligacion ya incorpora su
            # propia proteccion inflacionaria (ej. UVR), no se puede ademas indexar por
            # IPC via el Art. 867-1 sobre el mismo capital.
            if obligacion.protegida_inflacion_uvr and aplica_actualizacion_867_1(
                obligacion.fecha_origen, fecha_corte
            ):
                raise ValueError(
                    f"La obligacion tributaria '{obligacion.concepto}' ya incorpora "
                    f"protección inflacionaria propia (ej. UVR) -- no se puede aplicar "
                    f"ADEMÁS la indexación IPC del Art. 867-1 E.T. sobre el mismo capital "
                    f"(prohibición de doble cobro)."
                )

        resultado = _liquidar_por_obligacion(
            obligaciones=obligaciones_deuda,
            abonos=abonos,
            fecha_corte=fecha_corte,
            eventos_fn=lambda obligacion: self._eventos_de_obligacion(obligacion, fecha_corte),
            rate_provider_fn=self._construir_rate_provider_obligacion,
        )

        for obligacion in obligaciones_deuda:
            alerta = self._alerta_techo_usura_867_1(obligacion, fecha_corte)
            if alerta is not None:
                resultado = self._agregar_alerta(resultado, alerta)

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

    def _alerta_techo_usura_867_1(self, obligacion, fecha_corte: date) -> str | None:
        """Detecta si el techo de usura (Art. 867-1 E.T., `calcular_indexacion_867_1_topada`)
        realmente recorto la indexacion IPC de esta obligacion -- solo aplica al rubro
        "Impuesto" (unico que suma interes de mora + IPC, ver docstring de la clase). Retorna
        el mensaje de alerta si hubo recorte, None si no aplica o si la indexacion bruta no
        excedia el techo. Sprint 43: el recorte en si ya lo hacia
        `calcular_indexacion_867_1_topada` desde el Sprint 15 -- esto solo agrega la
        alerta no bloqueante que pedia el despacho."""
        if obligacion.categoria != "IMPUESTO_A_CARGO":
            return None
        if not aplica_actualizacion_867_1(obligacion.fecha_origen, fecha_corte):
            return None

        capital = obligacion.valor
        interes_ya_liquidado = calcular_interes_moratorio_tributario(
            capital, obligacion.fecha_origen, fecha_corte
        )
        indexacion_bruta = calcular_indexacion_867_1(capital, obligacion.fecha_origen, fecha_corte)
        indexacion_topada = calcular_indexacion_867_1_topada(
            capital, obligacion.fecha_origen, fecha_corte, interes_ya_liquidado
        )
        if indexacion_topada >= indexacion_bruta:
            return None
        return (
            f"Techo de usura alcanzado en '{obligacion.concepto}': la indexación IPC "
            f"(Art. 867-1 E.T.) se topó de {indexacion_bruta} a {indexacion_topada} para que "
            f"la tasa combinada (interés de mora + indexación) no supere la tasa de usura "
            f"plena."
        )

    def _validar_obligacion_tributaria(self, obligacion) -> None:
        if obligacion.tipo.value != "PUNTUAL":
            raise ValueError(
                f"La obligacion tributaria '{obligacion.concepto}' debe ser PUNTUAL "
                f"(un hecho tributario es un evento unico, no admite RECURRENTE)."
            )

        if obligacion.categoria == "IMPUESTO_A_CARGO":
            if obligacion.valor is None or obligacion.valor <= Decimal("0.00"):
                raise ValueError(
                    f"El impuesto a cargo '{obligacion.concepto}' debe tener 'valor' mayor "
                    "que cero."
                )
            return

        if obligacion.categoria == "SANCION_EXTEMPORANEIDAD":
            if (
                obligacion.base_sancion_tributaria is None
                or obligacion.meses_extemporaneidad is None
            ):
                raise ValueError(
                    f"La sancion por extemporaneidad '{obligacion.concepto}' necesita "
                    f"'base_sancion_tributaria' y 'meses_extemporaneidad'."
                )
            return

        if obligacion.categoria == "SANCION_INEXACTITUD":
            if obligacion.base_sancion_tributaria is None:
                raise ValueError(
                    f"La sancion por inexactitud '{obligacion.concepto}' necesita "
                    "'base_sancion_tributaria' (la diferencia entre el saldo determinado "
                    "y el declarado)."
                )
            return

        if obligacion.categoria == "SANCION_ERROR_ARITMETICO":
            if obligacion.base_sancion_tributaria is None:
                raise ValueError(
                    f"La sancion por error aritmetico '{obligacion.concepto}' necesita "
                    f"'base_sancion_tributaria' (la diferencia generada por el error)."
                )
            return

        raise ValueError(f"Categoria tributaria desconocida: '{obligacion.categoria}'.")

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
            payload={
                "amount": monto,
                "label": f"Actualización Art. 867-1 E.T. — {obligacion.concepto}",
            },
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

    def _construir_rate_provider_obligacion(
        self, obligacion, fecha_corte: date
    ) -> MemoryRateProvider:
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
                source=(
                    "Sin interés moratorio: mora > 3 años, reemplazado por actualización "
                    "IPC (Art. 867-1 E.T.)"
                ),
            )
            return provider

        provider = construir_rate_provider_moratorio_tributario(
            obligacion.fecha_origen, fecha_corte
        )
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
