from datetime import time

# Configurações do Banco de Dados
DATABASE_NAME = 'producao_injecao.db'

# Configurações dos Turnos
TURNOS = {
    'A': {
        'inicio': time(5, 40),
        'fim': time(14, 0),
        'descricao': 'Turno A (05:40 - 14:00)'
    },
    'B': {
        'inicio': time(14, 0),
        'fim': time(22, 20),
        'descricao': 'Turno B (14:00 - 22:20)'
    },
    'C': {
        'inicio': time(22, 20),
        'fim': time(5, 40),
        'descricao': 'Turno C (22:20 - 05:40)'
    }
}

# Configurações de Formatação
DECIMAL_SEPARATOR = ','
THOUSANDS_SEPARATOR = '.'

# Lista de Materiais
MATERIAIS = ['PE', 'PS', 'SAN', 'PP']

# Configurações de Status
STATUS_INJETORA = ['Disponível', 'Em Uso', 'Manutenção']
STATUS_MOLDE = ['Disponível', 'Em Uso', 'Manutenção']
STATUS_ORDEM = ['Pendente', 'Em Produção', 'Concluído', 'Atrasado']

# Configurações de Interface
PAGE_ICON = "🏭"
PAGE_TITLE = "Sistema de Gestão - Injeção Plástica"