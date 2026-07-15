import pytest
from datetime import date
from decimal import Decimal
from app.services.motor_liquidacion import AlimentosLiquidationService
from app.domain.obligation.payment import Payment

def test_liquidar_expediente_alimentos_completo():
    # DATOS DE LA DEMANDA (Mundo Real)
    fecha_inicio = date(2026, 1, 1)
    fecha_corte = date(2026, 4, 30)
    cuota_fija = Decimal("300000.00")
    dia_pago = 5 # Los 5 de cada mes
    tasa_diaria_mora = Decimal("0.1") # 0.1% diario
    
    # EL PADRE HIZO UN ÚNICO ABONO EN ABRIL
    abonos = [
        Payment(date=date(2026, 4, 15), amount=Decimal("500000.00"), reference="Consignación Juzgado")
    ]
    
    servicio = AlimentosLiquidationService()
    resultado = servicio.liquidar(
        fecha_inicio=fecha_inicio,
        fecha_corte=fecha_corte,
        cuota_mensual=cuota_fija,
        dia_pago=dia_pago,
        tasa_diaria_porcentaje=tasa_diaria_mora,
        pagos=abonos
    )
    
    # AUDITORÍA MATEMÁTICA DEL JUEZ:
    # 1. Enero 5: Cuota 1 ($300k)
    # 2. Febrero 5: Cuota 2 ($300k)
    # 3. Marzo 5: Cuota 3 ($300k)
    # 4. Abril 5: Cuota 4 ($300k) -> Total Capital = $1,200,000
    # 5. Abril 15: Pago de $500,000. Se aplica primero a los intereses generados por los 4 meses, el resto a capital.
    # 6. Abril 30: Corte, liquida intereses de los últimos 15 días sobre el saldo restante.
    
    assert resultado.is_empty() is False
    assert len(resultado.items) > 0
    
    balance_final = resultado.final_balance()
    
    # El capital final debe ser menor a 1,200,000 porque el abono alcanzó a morder capital
    assert balance_final.principal < Decimal("1200000.00")
    # Tienen que haberse aplicado los 500k del pago
    assert resultado.total_payments_applied() == Decimal("500000.00")