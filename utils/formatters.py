from decimal import Decimal, InvalidOperation
from datetime import datetime, time
from config.settings import DECIMAL_SEPARATOR, THOUSANDS_SEPARATOR, TURNOS

def format_decimal(value: float, precision: int = 2) -> str:
    """Formata número decimal usando configurações globais."""
    try:
        number = Decimal(str(value))
        formatted = f"{number:,.{precision}f}"
        return formatted.replace(',', 'X').replace('.', DECIMAL_SEPARATOR).replace('X', THOUSANDS_SEPARATOR)
    except (InvalidOperation, TypeError):
        return '0,00'

def parse_decimal(value: str) -> float:
    """Converte string em número decimal."""
    try:
        # Remove separador de milhares e converte vírgula em ponto
        cleaned = value.replace(THOUSANDS_SEPARATOR, '').replace(DECIMAL_SEPARATOR, '.')
        return float(cleaned)
    except (ValueError, AttributeError):
        return 0.0

def get_turno_atual() -> str:
    """Determina o turno atual baseado no horário."""
    now = datetime.now().time()
    
    # Caso especial para o turno C que cruza a meia-noite
    if now >= TURNOS['C']['inicio'] or now < TURNOS['C']['fim']:
        return 'C'
    
    for turno, horarios in TURNOS.items():
        if horarios['inicio'] <= now < horarios['fim']:
            return turno
            
    return 'A'  # Default para caso de erro

def format_peso(peso_kg: float) -> str:
    """Formata peso em kg."""
    return f"{format_decimal(peso_kg)} kg"