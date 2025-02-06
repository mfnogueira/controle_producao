from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List
from database.connection import get_connection, execute_query, DatabaseError

@dataclass
class Injetora:
    numero: str
    marca: str
    capacidade_ton: float
    status: str = 'Disponível'
    manutencao_proxima: Optional[date] = None
    data_ultima_manutencao: Optional[date] = None
    horimetro_atual: int = 0
    horimetro_proxima_manutencao: Optional[int] = None
    observacoes: Optional[str] = None
    id: Optional[int] = None
    data_cadastro: Optional[str] = None

    @staticmethod
    def criar(
        numero: str,
        marca: str,
        capacidade_ton: float,
        manutencao_proxima: Optional[date] = None,
        horimetro_proxima_manutencao: Optional[int] = None,
        observacoes: Optional[str] = None
    ) -> 'Injetora':
        """Cria uma nova injetora com validações."""
        if not numero or not numero.strip():
            raise ValueError("Número da injetora é obrigatório")

        if not marca or not marca.strip():
            raise ValueError("Marca é obrigatória")

        if capacidade_ton <= 0:
            raise ValueError("Capacidade deve ser maior que zero")

        return Injetora(
            numero=numero.strip(),
            marca=marca.strip(),
            capacidade_ton=capacidade_ton,
            manutencao_proxima=manutencao_proxima,
            horimetro_proxima_manutencao=horimetro_proxima_manutencao,
            observacoes=observacoes
        )

    def salvar(self) -> None:
        """Salva ou atualiza injetora no banco."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                if self.id is None:
                    # Nova injetora
                    cursor.execute("""
                        INSERT INTO injetoras (
                            numero, marca, capacidade_ton, status,
                            manutencao_proxima, horimetro_atual,
                            horimetro_proxima_manutencao, observacoes,
                            data_cadastro
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.numero, self.marca, self.capacidade_ton,
                        self.status, 
                        self.manutencao_proxima.strftime('%Y-%m-%d') if self.manutencao_proxima else None,
                        self.horimetro_atual,
                        self.horimetro_proxima_manutencao,
                        self.observacoes,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    conn.commit()
                    self.id = cursor.lastrowid
                else:
                    # Atualizar existente
                    cursor.execute("""
                        UPDATE injetoras SET
                            marca = ?,
                            capacidade_ton = ?,
                            status = ?,
                            manutencao_proxima = ?,
                            horimetro_atual = ?,
                            horimetro_proxima_manutencao = ?,
                            observacoes = ?
                        WHERE id = ?
                    """, (
                        self.marca, self.capacidade_ton, self.status,
                        self.manutencao_proxima.strftime('%Y-%m-%d') if self.manutencao_proxima else None,
                        self.horimetro_atual,
                        self.horimetro_proxima_manutencao,
                        self.observacoes,
                        self.id
                    ))
                    conn.commit()
        except Exception as e:
            raise DatabaseError(f"Erro ao salvar injetora: {str(e)}")

    @staticmethod
    def get_todos() -> List['Injetora']:
        """Retorna todas as injetoras."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM injetoras 
                    ORDER BY numero
                """)
                results = cursor.fetchall()
                
                return [Injetora(
                    id=row['id'],
                    numero=row['numero'],
                    marca=row['marca'],
                    capacidade_ton=row['capacidade_ton'],
                    status=row['status'],
                    manutencao_proxima=datetime.strptime(row['manutencao_proxima'], '%Y-%m-%d').date() if row['manutencao_proxima'] else None,
                    data_ultima_manutencao=datetime.strptime(row['data_ultima_manutencao'], '%Y-%m-%d').date() if row['data_ultima_manutencao'] else None,
                    horimetro_atual=row['horimetro_atual'],
                    horimetro_proxima_manutencao=row['horimetro_proxima_manutencao'],
                    observacoes=row['observacoes'],
                    data_cadastro=row['data_cadastro']
                ) for row in results]
        except Exception as e:
            print(f"Erro ao buscar injetoras: {str(e)}")
            return []

    @staticmethod
    def get_disponiveis() -> List['Injetora']:
        """Retorna todas as injetoras disponíveis."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM injetoras 
                    WHERE status = 'Disponível'
                    ORDER BY numero
                """)
                results = cursor.fetchall()
                
                return [Injetora(
                    id=row['id'],
                    numero=row['numero'],
                    marca=row['marca'],
                    capacidade_ton=row['capacidade_ton'],
                    status=row['status'],
                    manutencao_proxima=datetime.strptime(row['manutencao_proxima'], '%Y-%m-%d').date() if row['manutencao_proxima'] else None,
                    data_ultima_manutencao=datetime.strptime(row['data_ultima_manutencao'], '%Y-%m-%d').date() if row['data_ultima_manutencao'] else None,
                    horimetro_atual=row['horimetro_atual'],
                    horimetro_proxima_manutencao=row['horimetro_proxima_manutencao'],
                    observacoes=row['observacoes'],
                    data_cadastro=row['data_cadastro']
                ) for row in results]
        except Exception as e:
            print(f"Erro ao buscar injetoras disponíveis: {str(e)}")
            return []

    @staticmethod
    def get_by_id(id: int) -> Optional['Injetora']:
        """Busca uma injetora pelo ID."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM injetoras WHERE id = ?", (id,))
                row = cursor.fetchone()
                
                if row:
                    return Injetora(
                        id=row['id'],
                        numero=row['numero'],
                        marca=row['marca'],
                        capacidade_ton=row['capacidade_ton'],
                        status=row['status'],
                        manutencao_proxima=datetime.strptime(row['manutencao_proxima'], '%Y-%m-%d').date() if row['manutencao_proxima'] else None,
                        data_ultima_manutencao=datetime.strptime(row['data_ultima_manutencao'], '%Y-%m-%d').date() if row['data_ultima_manutencao'] else None,
                        horimetro_atual=row['horimetro_atual'],
                        horimetro_proxima_manutencao=row['horimetro_proxima_manutencao'],
                        observacoes=row['observacoes'],
                        data_cadastro=row['data_cadastro']
                    )
                return None
        except Exception as e:
            print(f"Erro ao buscar injetora por ID: {str(e)}")
            return None