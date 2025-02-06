import re
from datetime import datetime, date
from typing import Optional
from database.connection import get_connection

def validate_numero_injetora(numero: str) -> None:
    """
    Valida o número da injetora.
    Regras:
    - Não pode estar vazio
    - Deve ser alfanumérico
    - Não pode já existir no banco
    """
    if not numero:
        raise ValueError("Número da injetora não pode estar vazio")
    
    if not numero.strip():
        raise ValueError("Número da injetora não pode conter apenas espaços")
    
    if not re.match(r'^[A-Za-z0-9-]+$', numero):
        raise ValueError("Número da injetora deve conter apenas letras, números e hífen")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM injetoras WHERE numero = ?", (numero,))
        if cursor.fetchone():
            raise ValueError(f"Injetora com número {numero} já existe")

def validate_nome_molde(nome: str) -> None:
    """
    Valida o nome do molde.
    Regras:
    - Não pode estar vazio
    - Deve ter entre 3 e 50 caracteres
    - Não pode já existir no banco
    """
    if not nome:
        raise ValueError("Nome do molde não pode estar vazio")
    
    if not nome.strip():
        raise ValueError("Nome do molde não pode conter apenas espaços")
    
    if len(nome) < 3:
        raise ValueError("Nome do molde deve ter pelo menos 3 caracteres")
    
    if len(nome) > 50:
        raise ValueError("Nome do molde deve ter no máximo 50 caracteres")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM moldes WHERE nome = ?", (nome,))
        if cursor.fetchone():
            raise ValueError(f"Molde com nome {nome} já existe")

def validate_numero_pedido(numero: str) -> None:
    """
    Valida o número do pedido.
    Regras:
    - Não pode estar vazio
    - Deve ter formato válido (PED-YYYYMMDD-XXX)
    - Não pode já existir no banco
    """
    if not numero:
        raise ValueError("Número do pedido não pode estar vazio")
    
    # Validar formato PED-YYYYMMDD-XXX
    pattern = r'^PED-\d{8}-\d{3}$'
    if not re.match(pattern, numero):
        raise ValueError("Número do pedido deve ter o formato PED-YYYYMMDD-XXX")
    
    # Validar data no número do pedido
    try:
        data_str = numero.split('-')[1]
        datetime.strptime(data_str, '%Y%m%d')
    except ValueError:
        raise ValueError("Data no número do pedido é inválida")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM ordens_producao WHERE numero_pedido = ?", (numero,))
        if cursor.fetchone():
            raise ValueError(f"Pedido {numero} já existe")

def validate_quantidade(valor: float, campo: str) -> None:
    """
    Valida quantidade numérica.
    Regras:
    - Deve ser maior que zero
    """
    if valor <= 0:
        raise ValueError(f"{campo} deve ser maior que zero")

def validate_datas_producao(data_inicio: date, data_fim: Optional[date] = None) -> None:
    """
    Valida datas de produção.
    Regras:
    - Data início não pode ser no passado
    - Data fim (se fornecida) deve ser posterior à data início
    """
    hoje = date.today()
    
    if data_inicio < hoje:
        raise ValueError("Data de início não pode ser no passado")
    
    if data_fim and data_fim <= data_inicio:
        raise ValueError("Data de término deve ser posterior à data de início")

def validate_percentual(valor: float, campo: str) -> None:
    """
    Valida valor percentual.
    Regras:
    - Deve estar entre 0 e 100
    """
    if valor < 0 or valor > 100:
        raise ValueError(f"{campo} deve estar entre 0 e 100")

def validate_peso(valor: float, campo: str) -> None:
    """
    Valida peso em kg.
    Regras:
    - Deve ser maior que zero
    - Deve ser menor que 100kg (valor arbitrário, ajuste conforme necessário)
    """
    if valor <= 0:
        raise ValueError(f"{campo} deve ser maior que zero")
    
    if valor > 100:
        raise ValueError(f"{campo} parece muito alto. Verifique se a unidade está em kg")

def validate_ciclo(valor: float) -> None:
    """
    Valida tempo de ciclo.
    Regras:
    - Deve ser maior que zero
    - Deve ser menor que 3600 segundos (1 hora)
    """
    if valor <= 0:
        raise ValueError("Tempo de ciclo deve ser maior que zero")
    
    if valor > 3600:
        raise ValueError("Tempo de ciclo não pode ser maior que 1 hora")

def validate_hora(hora: str, campo: str) -> None:
    """
    Valida formato de hora.
    Regras:
    - Deve estar no formato HH:MM
    - Deve ser hora válida
    """
    try:
        hora_obj = datetime.strptime(hora, '%H:%M')
    except ValueError:
        raise ValueError(f"{campo} deve estar no formato HH:MM")

def validate_turno(turno: str) -> None:
    """
    Valida turno de trabalho.
    Regras:
    - Deve ser A, B ou C
    """
    if turno not in ['A', 'B', 'C']:
        raise ValueError("Turno deve ser A, B ou C")

def validate_operador(operador: str) -> None:
    """
    Valida nome do operador.
    Regras:
    - Não pode estar vazio
    - Deve ter entre 3 e 100 caracteres
    - Deve conter apenas letras e espaços
    """
    if not operador:
        raise ValueError("Nome do operador não pode estar vazio")
    
    if not operador.strip():
        raise ValueError("Nome do operador não pode conter apenas espaços")
    
    if len(operador) < 3:
        raise ValueError("Nome do operador deve ter pelo menos 3 caracteres")
    
    if len(operador) > 100:
        raise ValueError("Nome do operador deve ter no máximo 100 caracteres")
    
    if not re.match(r'^[A-Za-zÀ-ÿ\s]+$', operador):
        raise ValueError("Nome do operador deve conter apenas letras e espaços")