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
        except InvalidOperation as err:
            raise ValueError(f"Formato numérico inválido: {value_str}") from err

    @staticmethod
    def parse_money(text: str) -> Decimal:
        """Convierte un monto en texto a Decimal exacto.

        Detecta el separador decimal en vez de asumir siempre el formato
        colombiano de forma incondicional (bug corregido en el Sprint 27: un
        monto en formato US como "5000000.00" se interpretaba 100x más
        grande al remover el punto como si fuera separador de miles).
        Reglas de detección (formato colombiano como valor por defecto en
        los casos ambiguos, igual que antes):

        - Si el texto trae punto Y coma, el que aparece más a la derecha es
          el separador decimal (ej. "5.000.000,50" -> colombiano;
          "5,000,000.50" -> US).
        - Si solo trae coma, se asume coma decimal (formato colombiano,
          ej. "5000000,50").
        - Si solo trae punto:
            - más de un punto -> son separadores de miles colombianos
              (ej. "5.000.000" -> 5000000).
            - un solo punto con exactamente 3 dígitos después -> separador
              de miles colombiano sin parte decimal (ej. "5.000" -> 5000).
            - un solo punto con 1, 2 o 4+ dígitos después -> punto decimal
              (ej. "5000000.00" -> 5000000.00).
        - Sin punto ni coma -> el texto ya es un número plano.
        """
        clean_text = text.replace('$', '').replace(' ', '').strip()

        has_dot = '.' in clean_text
        has_comma = ',' in clean_text

        if has_dot and has_comma:
            if clean_text.rfind(',') > clean_text.rfind('.'):
                normalized = clean_text.replace('.', '').replace(',', '.')
            else:
                normalized = clean_text.replace(',', '')
        elif has_comma:
            normalized = clean_text.replace(',', '.')
        elif has_dot:
            partes = clean_text.split('.')
            if len(partes) > 2 or len(partes[-1]) == 3:
                normalized = clean_text.replace('.', '')
            else:
                normalized = clean_text
        else:
            normalized = clean_text

        try:
            return Decimal(normalized)
        except InvalidOperation as error:
            raise ValueError(f"Monto financiero inválido: {text}") from error