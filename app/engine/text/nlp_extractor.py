import re
import sys
from collections.abc import Callable
from datetime import datetime

from rich.prompt import Prompt

from app.core.exceptions import DatoFaltanteError
from app.engine.math.parsers import FinancialParser


def _prompt_interactivo(mensaje: str) -> str:
    """Prompt por defecto de `validate_and_fill`: usa `rich.prompt.Prompt.ask`,
    pero solo si hay un stdin interactivo conectado. En un ejecutable Windows
    sin consola adjunta (o en cualquier proceso no interactivo, ej. si esta
    clase se conecta a la GUI sin cambiarla primero) `sys.stdin` no es
    interactivo -- ahi se lanza `DatoFaltanteError` en vez de bloquear
    esperando una entrada que nunca llega (Sprint 27)."""
    if not sys.stdin or not sys.stdin.isatty():
        raise DatoFaltanteError(
            f"No hay stdin interactivo disponible para solicitar: {mensaje!r}. "
            "Proporcione prompt_fn para completar este dato desde otro origen "
            "(ej. un dialogo de la GUI)."
        )
    return Prompt.ask(f"[bold red]{mensaje}[/bold red]")


class LegalTextExtractor:
    """Motor determinista para extraer hechos jurídicos de texto natural.

    NOTA (Sprint 27): módulo huérfano hoy -- nada en `app/` lo importa
    todavía. Se conserva intencionalmente para una futura integración (ej.
    importar hechos desde texto libre pegado en la GUI). `validate_and_fill`
    acepta un `prompt_fn` inyectable para que un futuro caller decida cómo
    pedir un dato faltante (diálogo de Qt, valor por defecto, etc.); sin
    `prompt_fn`, usa `rich` solo si hay stdin interactivo real (ver
    `_prompt_interactivo`), evitando el cuelgue original si esta clase se
    conectara a la GUI sin cambiarla primero.
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
                pass  # Fallback si el formato no coincide

        return facts

    def validate_and_fill(
        self, facts: dict, prompt_fn: Callable[[str], str] = _prompt_interactivo
    ) -> dict:
        """Verifica qué datos faltan. Si falta la fecha o el capital, los
        pide con `prompt_fn(mensaje) -> str` (por defecto, `_prompt_interactivo`,
        que solo bloquea si hay stdin interactivo real)."""
        if not facts["capital"]:
            raw_cap = prompt_fn("Capital no detectado en el texto. Ingrese el monto histórico")
            facts["capital"] = FinancialParser.parse_money(raw_cap)

        if not facts["fecha_exigibilidad"]:
            raw_date = prompt_fn("Fecha de inicio no detectada. Ingrese fecha (DD/MM/YYYY)")
            facts["fecha_exigibilidad"] = datetime.strptime(raw_date, "%d/%m/%Y").date()

        return facts
