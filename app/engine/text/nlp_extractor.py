import re
from datetime import datetime
from rich.prompt import Prompt
from app.engine.math.parsers import FinancialParser

class LegalTextExtractor:
    """
    Motor determinista para extraer hechos jurídicos de texto natural.
    """
    def __init__(self):
        # Patrones para buscar dinero y fechas
        self.money_pattern = r'\$\s*[\d\.\,]+'
        self.date_pattern = r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})'

    def extract_facts(self, natural_text: str) -> dict:
        facts = {
            "capital": None,
            "fecha_exigibilidad": None,
        }

        # 1. Extraer Capital
        money_matches = re.findall(self.money_pattern, natural_text)
        if money_matches:
            # Tomamos la primera coincidencia monetaria como capital base
            facts["capital"] = FinancialParser.parse_money(money_matches[0])

        # 2. Extraer Fecha
        date_matches = re.findall(self.date_pattern, natural_text)
        if date_matches:
            # Intentamos parsear la fecha (asumiendo formato DD/MM/YYYY)
            raw_date = date_matches[0].replace('-', '/')
            try:
                facts["fecha_exigibilidad"] = datetime.strptime(raw_date, "%d/%m/%Y").date()
            except ValueError:
                pass # Fallback si el formato no coincide

        return facts

    def validate_and_fill(self, facts: dict) -> dict:
        """
        Verifica qué datos faltan. Si falta la fecha o el capital, lo pide.
        """
        if not facts["capital"]:
            raw_cap = Prompt.ask("[bold red]Capital no detectado en el texto.[/bold red] Ingrese el monto histórico")
            facts["capital"] = FinancialParser.parse_money(raw_cap)
            
        if not facts["fecha_exigibilidad"]:
            raw_date = Prompt.ask("[bold red]Fecha de inicio no detectada.[/bold red] Ingrese fecha (DD/MM/YYYY)")
            facts["fecha_exigibilidad"] = datetime.strptime(raw_date, "%d/%m/%Y").date()
            
        return facts