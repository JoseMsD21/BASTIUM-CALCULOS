import re
from decimal import Decimal, InvalidOperation

class FinancialParser:
    """
    Sanitizador implacable de entradas financieras.
    Convierte textos sucios ('0,0164%', '$ 5.000.000,00') en Decimales puros.
    """
    @staticmethod
    def parse_percentage(text: str) -> Decimal:
        if not text:
            return Decimal("0.00")
            
        # 1. Limpiar espacios y convertir comas a puntos (estándar computacional)
        clean_text = text.strip().replace(',', '.')
        
        # 2. Extraer solo los números y el punto decimal usando expresiones regulares
        match = re.search(r'[\d\.]+', clean_text)
        if not match:
            raise ValueError(f"No se pudo extraer un valor numérico de: {text}")
            
        value_str = match.group(0)
        
        try:
            value = Decimal(value_str)
            # 3. Si el usuario escribió el símbolo '%', ya lo asumimos como porcentaje.
            # Si escribió '0.0164' pero era un porcentaje, la lógica de negocio debe saberlo.
            # Aquí garantizamos que el número es un Decimal exacto.
            return value
        except InvalidOperation:
            raise ValueError(f"Formato numérico inválido: {value_str}")

    @staticmethod
    def parse_money(text: str) -> Decimal:
        # Remueve símbolos de moneda y separadores de miles (puntos), cambia coma decimal a punto
        clean_text = text.replace('$', '').replace(' ', '')
        # Si el formato colombiano es 5.000.000,00 -> removemos puntos y cambiamos coma a punto
        clean_text = clean_text.replace('.', '').replace(',', '.')
        try:
            return Decimal(clean_text)
        except InvalidOperation:
            raise ValueError(f"Monto financiero inválido: {text}")