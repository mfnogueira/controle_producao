from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List
from database.connection import get_connection, DatabaseError

@dataclass
class Molde:
    nome: str
    fabricante: str
    num_cavidades: int
    ciclos_total: int = 0
    ciclos_desde_manutencao: int = 0
    manutencao_proxima: Optional[int] = None
    data_ultima_manutencao: Optional[date] = None
    status: str = 'Disponível'
    observacoes: Optional[str] = None
    id: Optional[int] = None
    data_cadastro: Optional[str] = None

    @staticmethod
    def criar(
        nome: str,
        fabricante: str,
        num_cavidades: int,
        manutencao_proxima: Optional[int] = None,
        observacoes: Optional[str] = None
    ) -> 'Molde':
        """Cria um novo molde com validações."""
        if not nome or not nome.strip():
            raise ValueError("Nome do molde é obrigatório")

        if not fabricante or not fabricante.strip():
            raise ValueError("Fabricante é obrigatório")

        if num_cavidades <= 0:
            raise ValueError("Número de cavidades deve ser maior que zero")

        if manutencao_proxima is not None and manutencao_proxima <= 0:
            raise ValueError("Ciclos para manutenção deve ser maior que zero")

        return Molde(
            nome=nome.strip(),
            fabricante=fabricante.strip(),
            num_cavidades=num_cavidades,
            manutencao_proxima=manutencao_proxima,
            observacoes=observacoes
        )

    def salvar(self) -> None:
        """Salva ou atualiza molde no banco."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                if self.id is None:
                    # Novo molde
                    cursor.execute("""
                        INSERT INTO moldes (
                            nome, fabricante, num_cavidades, ciclos_total,
                            ciclos_desde_manutencao, manutencao_proxima,
                            data_ultima_manutencao, status, observacoes,
                            data_cadastro
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.nome, self.fabricante, self.num_cavidades,
                        self.ciclos_total, self.ciclos_desde_manutencao,
                        self.manutencao_proxima,
                        self.data_ultima_manutencao.strftime('%Y-%m-%d') if self.data_ultima_manutencao else None,
                        self.status, self.observacoes,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    conn.commit()
                    self.id = cursor.lastrowid
                else:
                    # Atualizar existente
                    cursor.execute("""
                        UPDATE moldes SET
                            fabricante = ?,
                            num_cavidades = ?,
                            ciclos_total = ?,
                            ciclos_desde_manutencao = ?,
                            manutencao_proxima = ?,
                            data_ultima_manutencao = ?,
                            status = ?,
                            observacoes = ?
                        WHERE id = ?
                    """, (
                        self.fabricante, self.num_cavidades,
                        self.ciclos_total, self.ciclos_desde_manutencao,
                        self.manutencao_proxima,
                        self.data_ultima_manutencao.strftime('%Y-%m-%d') if self.data_ultima_manutencao else None,
                        self.status, self.observacoes,
                        self.id
                    ))
                    conn.commit()
        except Exception as e:
            raise DatabaseError(f"Erro ao salvar molde: {str(e)}")

    @staticmethod
    def get_todos() -> List['Molde']:
        """Retorna todos os moldes."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM moldes 
                    ORDER BY nome
                """)
                results = cursor.fetchall()
                
                return [Molde(
                    id=row['id'],
                    nome=row['nome'],
                    fabricante=row['fabricante'],
                    num_cavidades=row['num_cavidades'],
                    ciclos_total=row['ciclos_total'],
                    ciclos_desde_manutencao=row['ciclos_desde_manutencao'],
                    manutencao_proxima=row['manutencao_proxima'],
                    data_ultima_manutencao=datetime.strptime(row['data_ultima_manutencao'], '%Y-%m-%d').date() if row['data_ultima_manutencao'] else None,
                    status=row['status'],
                    observacoes=row['observacoes'],
                    data_cadastro=row['data_cadastro']
                ) for row in results]
        except Exception as e:
            print(f"Erro ao buscar moldes: {str(e)}")
            return []

    @staticmethod
    def get_disponiveis() -> List['Molde']:
        """Retorna todos os moldes disponíveis."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM moldes 
                    WHERE status = 'Disponível'
                    ORDER BY nome
                """)
                results = cursor.fetchall()
                
                return [Molde(
                    id=row['id'],
                    nome=row['nome'],
                    fabricante=row['fabricante'],
                    num_cavidades=row['num_cavidades'],
                    ciclos_total=row['ciclos_total'],
                    ciclos_desde_manutencao=row['ciclos_desde_manutencao'],
                    manutencao_proxima=row['manutencao_proxima'],
                    data_ultima_manutencao=datetime.strptime(row['data_ultima_manutencao'], '%Y-%m-%d').date() if row['data_ultima_manutencao'] else None,
                    status=row['status'],
                    observacoes=row['observacoes'],
                    data_cadastro=row['data_cadastro']
                ) for row in results]
        except Exception as e:
            print(f"Erro ao buscar moldes disponíveis: {str(e)}")
            return []

    @staticmethod
    def get_by_id(id: int) -> Optional['Molde']:
        """Busca um molde pelo ID."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM moldes WHERE id = ?", (id,))
                row = cursor.fetchone()
                
                if row:
                    return Molde(
                        id=row['id'],
                        nome=row['nome'],
                        fabricante=row['fabricante'],
                        num_cavidades=row['num_cavidades'],
                        ciclos_total=row['ciclos_total'],
                        ciclos_desde_manutencao=row['ciclos_desde_manutencao'],
                        manutencao_proxima=row['manutencao_proxima'],
                        data_ultima_manutencao=datetime.strptime(row['data_ultima_manutencao'], '%Y-%m-%d').date() if row['data_ultima_manutencao'] else None,
                        status=row['status'],
                        observacoes=row['observacoes'],
                        data_cadastro=row['data_cadastro']
                    )
                return None
        except Exception as e:
            print(f"Erro ao buscar molde por ID: {str(e)}")
            return None

    def registrar_manutencao(
        self,
        data: date,
        tipo_manutencao: str,
        descricao: str,
        tecnico: str,
        custo: float,
        tempo_parado: float
    ) -> None:
        """Registra uma manutenção para o molde."""
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Registrar manutenção
            cursor.execute("""
                INSERT INTO manutencoes (
                    tipo, equipamento_id, data_manutencao,
                    tipo_manutencao, descricao, tecnico,
                    custo, tempo_parado_horas
                ) VALUES ('molde', ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.id, data, tipo_manutencao, descricao,
                tecnico, custo, tempo_parado
            ))
            
            # Atualizar dados do molde
            cursor.execute("""
                UPDATE moldes SET
                    data_ultima_manutencao = ?,
                    ciclos_desde_manutencao = 0,
                    status = 'Disponível'
                WHERE id = ?
            """, (data, self.id))
            
            conn.commit()