from dataclasses import replace
from datetime import date
from decimal import Decimal

from app.core.exceptions import ParametroNoDisponibleError
from app.domain.obligation.payment import Payment
from app.engine.financial.rate import Rate
from app.engine.interest.provider import RateProvider
from app.engine.liquidation.engine import LiquidationCore
from app.engine.liquidation.result import LiquidationResult
from app.engine.temporal.prescripcion import TipoAccion, filtrar_cuotas_prescritas
from app.engine.temporal.schedulers.base import Event


class UniversalLiquidationService:
    """
    Fachada de Integración Universal.
    Acepta eventos jurídicos de cualquier rama del derecho (Laboral, Civil, Comercial, Familia)
    los fusiona con pagos realizados en la vida real, y acciona el núcleo determinista.

    Es el unico punto por el que pasan las 6 AreaStrategy para invocar LiquidationCore
    (directo o via area_strategy._liquidar_por_obligacion) -- por eso Sprint 42 centraliza
    aqui el wiring del motor de prescripcion/caducidad (app/engine/temporal/prescripcion.py)
    en vez de repetirlo en cada AreaStrategy.
    """

    def liquidar(
        self,
        eventos_causacion: list[Event],
        pagos: list[Payment],
        fecha_corte: date,
        tasa_estatica: Decimal = Decimal("0.0"),
        rate_provider: RateProvider | None = None,
        usar_suma_unica: bool = False,
        tipo_accion: TipoAccion = TipoAccion.EJECUTIVA,
    ) -> LiquidationResult:

        # 1. Configurar la política de mora
        tasa_mora = Rate.from_percent(tasa_estatica)

        # 2. Conversión de abonos físicos a eventos financieros inmutables
        eventos_pago = []
        for pago in pagos:
            if pago.date <= fecha_corte:
                eventos_pago.append(Event(
                    date=pago.date,
                    payload={"amount": pago.amount, "reference": pago.reference},
                    event_type="PAYMENT"
                ))

        # 3. Fusión del historial: Nacimiento de la deuda + Amortizaciones
        historia_completa = eventos_causacion + eventos_pago

        # 4. Instanciación del Motor Core con inyección de dependencias
        motor_calculo = LiquidationCore(
            default_daily_rate=tasa_mora,
            rate_provider=rate_provider,
            usar_suma_unica=usar_suma_unica
        )

        # 5. Ejecución del procesamiento temporal implacable
        resultado = motor_calculo.process(
            chronological_events=historia_completa,
            cutoff_date=fecha_corte
        )

        # 6. Sprint 42: marcar (sin excluir) las filas cuya obligacion de origen ya
        # vencio su plazo de prescripcion/caducidad a la fecha de corte. Decision del
        # despacho (ver docs/superpowers/plans/2026-08-07-sprint42-prescripcion-caducidad-wiring.md):
        # la obligacion prescrita se sigue calculando exactamente igual (el total NO
        # cambia), solo se marca informativamente para que el abogado decida.
        return self._marcar_obligaciones_prescritas(
            resultado, eventos_causacion, fecha_corte, tipo_accion
        )

    def _marcar_obligaciones_prescritas(
        self,
        resultado: LiquidationResult,
        eventos_causacion: list[Event],
        fecha_corte: date,
        tipo_accion: TipoAccion,
    ) -> LiquidationResult:
        # filtrar_cuotas_prescritas separa eventos_causacion en vivos/prescritos, pero
        # aqui se reutiliza SOLO para detectar cuales estan prescritos -- ambos grupos
        # ya fueron procesados igual por LiquidationCore en el paso 5, sin excluir nada.
        try:
            _vivas, prescritas = filtrar_cuotas_prescritas(eventos_causacion, fecha_corte, tipo_accion)
        except ParametroNoDisponibleError:
            # Sin el plazo de prescripcion configurado en Parametros no se puede
            # determinar el estado de ninguna fila -- se omite la marca en vez de
            # tumbar la liquidacion completa (mismo criterio de fallo abierto que usa
            # _refrescar_alertas_vencimiento en app/views/dashboard.py, Sprint 33).
            return resultado

        if not prescritas:
            return resultado

        # Las filas de LiquidationItem no guardan una referencia al Event que las
        # origino, asi que se reconstruye la firma (fecha, concepto) con la misma
        # logica que LiquidationCore._process_event usa para poblar `concept`
        # (event.payload.get("label", event.event_type)). eventos_pago (PAYMENT)
        # nunca entran aqui porque filtrar_cuotas_prescritas solo recibe
        # eventos_causacion -- un pago nunca puede quedar marcado como prescrito.
        firmas_prescritas = {
            (evento.date, evento.payload.get("label", evento.event_type))
            for evento in prescritas
        }

        items_marcados = [
            replace(item, prescrita=True) if (item.date, item.concept) in firmas_prescritas else item
            for item in resultado.items
        ]
        return replace(resultado, items=items_marcados)