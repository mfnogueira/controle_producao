from database.connection import get_connection, DatabaseError

def table_exists(conn, table_name):
    """Verifica se uma tabela existe no banco de dados."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def criar_banco():
    """Cria todas as tabelas do banco de dados."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Tabela de Injetoras
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS injetoras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT UNIQUE,
                    marca TEXT,
                    capacidade_ton REAL,
                    status TEXT DEFAULT 'Disponível',
                    manutencao_proxima DATE,
                    data_ultima_manutencao DATE,
                    horimetro_atual INTEGER DEFAULT 0,
                    horimetro_proxima_manutencao INTEGER,
                    observacoes TEXT,
                    data_cadastro TEXT
                )
            ''')

            # Tabela de Moldes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS moldes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE,
                    fabricante TEXT,
                    num_cavidades INTEGER,
                    ciclos_total INTEGER DEFAULT 0,
                    ciclos_desde_manutencao INTEGER DEFAULT 0,
                    manutencao_proxima INTEGER,
                    data_ultima_manutencao DATE,
                    status TEXT DEFAULT 'Disponível',
                    observacoes TEXT,
                    data_cadastro TEXT
                )
            ''')

            # Tabela de Ordens de Produção
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ordens_producao (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_pedido TEXT UNIQUE,
                    cliente TEXT,
                    injetora_id INTEGER,
                    molde_id INTEGER,
                    quantidade_total INTEGER,
                    quantidade_produzida INTEGER DEFAULT 0,
                    ciclo_segundos REAL,
                    material TEXT,
                    percentual_master REAL,
                    peso_peca REAL,
                    peso_total REAL,
                    data_inicio TEXT,
                    data_fim TEXT,
                    status TEXT DEFAULT 'Pendente',
                    prioridade INTEGER DEFAULT 3,
                    observacoes TEXT,
                    data_cadastro TEXT,
                    FOREIGN KEY (injetora_id) REFERENCES injetoras (id),
                    FOREIGN KEY (molde_id) REFERENCES moldes (id)
                )
            ''')

            # Tabela de Produção Diária
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS producao_diaria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ordem_id INTEGER,
                    data DATE,
                    turno TEXT,
                    quantidade_produzida INTEGER,
                    refugo_kg REAL DEFAULT 0,
                    tempo_parado_minutos INTEGER DEFAULT 0,
                    motivo_parada TEXT,
                    operador TEXT,
                    observacoes TEXT,
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ordem_id) REFERENCES ordens_producao (id)
                )
            ''')

            # Tabela de Manutenções
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS manutencoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT,  -- 'injetora' ou 'molde'
                    equipamento_id INTEGER,
                    data_manutencao DATE,
                    tipo_manutencao TEXT,  -- 'preventiva' ou 'corretiva'
                    descricao TEXT,
                    tecnico TEXT,
                    custo REAL,
                    tempo_parado_horas REAL,
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Índices para melhor performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ordens_status ON ordens_producao(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_producao_data ON producao_diaria(data)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_manutencoes_data ON manutencoes(data_manutencao)')

            conn.commit()
            return True

    except Exception as e:
        print(f"Erro ao criar banco de dados: {str(e)}")
        return False

def verificar_atualizacoes():
    """Verifica e aplica atualizações necessárias no schema."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Primeiro verifica se a tabela producao_diaria existe
            if not table_exists(conn, 'producao_diaria'):
                return False
            
            # Verifica e adiciona coluna de turno se não existir
            cursor.execute("PRAGMA table_info(producao_diaria)")
            colunas = {col['name'] for col in cursor.fetchall()}
            
            if 'turno' not in colunas:
                cursor.execute('ALTER TABLE producao_diaria ADD COLUMN turno TEXT DEFAULT "A"')
            
            if 'refugo' in colunas and 'refugo_kg' not in colunas:
                # Criar nova coluna
                cursor.execute('ALTER TABLE producao_diaria ADD COLUMN refugo_kg REAL DEFAULT 0')
                # Copiar dados da coluna antiga
                cursor.execute('UPDATE producao_diaria SET refugo_kg = refugo')
                # Remover coluna antiga (SQLite não suporta DROP COLUMN diretamente)
                cursor.execute('''
                    CREATE TABLE producao_diaria_temp AS 
                    SELECT * FROM producao_diaria
                ''')
                cursor.execute('DROP TABLE producao_diaria')
                cursor.execute('''
                    CREATE TABLE producao_diaria AS 
                    SELECT id, ordem_id, data, turno, quantidade_produzida, 
                           refugo_kg, tempo_parado_minutos, motivo_parada, 
                           operador, observacoes, data_registro 
                    FROM producao_diaria_temp
                ''')
                cursor.execute('DROP TABLE producao_diaria_temp')
            
            conn.commit()
            return True

    except Exception as e:
        print(f"Erro ao atualizar schema: {str(e)}")
        return False