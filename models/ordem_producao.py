from dataclasses import dataclass
from datetime import datetime, date, timedelta  # Adicionando timedelta aqui
from typing import Optional, List
from database.connection import get_connection, DatabaseError
from models.injetora import Injetora
from models.molde import Molde

@dataclass
class OrdemProducao:
    numero_pedido: str
    cliente: str
    injetora_id: int
    molde_id: int
    quantidade_total: int
    ciclo_segundos: float
    material: str
    percentual_master: float
    peso_peca: float
    data_inicio: date
    data_fim: Optional[date] = None
    quantidade_produzida: int = 0
    peso_total: Optional[float] = None
    status: str = 'Pendente'
    prioridade: int = 3
    observacoes: Optional[str] = None
    id: Optional[int] = None
    data_cadastro: Optional[str] = None

    @staticmethod
    def criar(
        numero_pedido: str,
        cliente: str,
        injetora_id: int,
        molde_id: int,
        quantidade_total: int,
        ciclo_segundos: float,
        material: str,
        percentual_master: float,
        peso_peca: float,
        data_inicio: date,
        prioridade: int = 3,
        observacoes: Optional[str] = None
    ) -> 'OrdemProducao':
        """Cria uma nova ordem de produção com validações."""
        # Validações básicas
        if not numero_pedido or not numero_pedido.strip():
            raise ValueError("Número do pedido é obrigatório")
        
        if not cliente or not cliente.strip():
            raise ValueError("Cliente é obrigatório")

        if quantidade_total <= 0:
            raise ValueError("Quantidade total deve ser maior que zero")

        if ciclo_segundos <= 0:
            raise ValueError("Ciclo deve ser maior que zero")

        if percentual_master < 0 or percentual_master > 100:
            raise ValueError("Percentual de master deve estar entre 0 e 100")

        if peso_peca <= 0:
            raise ValueError("Peso da peça deve ser maior que zero")

        if prioridade not in [1, 2, 3]:
            raise ValueError("Prioridade inválida")

        # Verificar se injetora e molde existem e estão disponíveis
        injetora = Injetora.get_by_id(injetora_id)
        if not injetora:
            raise ValueError("Injetora não encontrada")
        if injetora.status != 'Disponível':
            raise ValueError("Injetora não está disponível")

        molde = Molde.get_by_id(molde_id)
        if not molde:
            raise ValueError("Molde não encontrado")
        if molde.status != 'Disponível':
            raise ValueError("Molde não está disponível")

        # Calcular peso total considerando master
        peso_total = (quantidade_total * peso_peca / 1000) * (1 + percentual_master/100)

        # Calcular data estimada de fim
        ciclo_horas = ciclo_segundos / 3600
        num_ciclos = quantidade_total / molde.num_cavidades
        horas_totais = (ciclo_horas * num_ciclos) / 0.85  # Considerando 85% de eficiência
        dias_producao = max(1, round(horas_totais / 24))
        data_fim = data_inicio + timedelta(days=dias_producao)

        return OrdemProducao(
            numero_pedido=numero_pedido.strip(),
            cliente=cliente.strip(),
            injetora_id=injetora_id,
            molde_id=molde_id,
            quantidade_total=quantidade_total,
            ciclo_segundos=ciclo_segundos,
            material=material,
            percentual_master=percentual_master,
            peso_peca=peso_peca,
            peso_total=peso_total,
            data_inicio=data_inicio,
            data_fim=data_fim,
            prioridade=prioridade,
            observacoes=observacoes
        )

    def salvar(self) -> None:
        """Salva ou atualiza ordem de produção no banco."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                if self.id is None:
                    # Nova ordem
                    cursor.execute("""
                        INSERT INTO ordens_producao (
                            numero_pedido, cliente, injetora_id, molde_id,
                            quantidade_total, quantidade_produzida, ciclo_segundos,
                            material, percentual_master, peso_peca, peso_total,
                            data_inicio, data_fim, status, prioridade,
                            observacoes, data_cadastro
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.numero_pedido, self.cliente, self.injetora_id,
                        self.molde_id, self.quantidade_total, self.quantidade_produzida,
                        self.ciclo_segundos, self.material, self.percentual_master,
                        self.peso_peca, self.peso_total,
                        self.data_inicio.strftime('%Y-%m-%d'),
                        self.data_fim.strftime('%Y-%m-%d') if self.data_fim else None,
                        self.status, self.prioridade, self.observacoes,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    self.id = cursor.lastrowid

                    # Atualizar status da injetora e molde
                    cursor.execute(
                        "UPDATE injetoras SET status = 'Em Uso' WHERE id = ?",
                        (self.injetora_id,)
                    )
                    cursor.execute(
                        "UPDATE moldes SET status = 'Em Uso' WHERE id = ?",
                        (self.molde_id,)
                    )
                else:
                    # Atualizar existente
                    cursor.execute("""
                        UPDATE ordens_producao SET
                            cliente = ?,
                            quantidade_total = ?,
                            quantidade_produzida = ?,
                            ciclo_segundos = ?,
                            material = ?,
                            percentual_master = ?,
                            peso_peca = ?,
                            peso_total = ?,
                            data_inicio = ?,
                            data_fim = ?,
                            status = ?,
                            prioridade = ?,
                            observacoes = ?
                        WHERE id = ?
                    """, (
                        self.cliente, self.quantidade_total,
                        self.quantidade_produzida, self.ciclo_segundos,
                        self.material, self.percentual_master,
                        self.peso_peca, self.peso_total,
                        self.data_inicio.strftime('%Y-%m-%d'),
                        self.data_fim.strftime('%Y-%m-%d') if self.data_fim else None,
                        self.status, self.prioridade, self.observacoes,
                        self.id
                    ))
                
                conn.commit()
        except Exception as e:
            raise DatabaseError(f"Erro ao salvar ordem de produção: {str(e)}")

    @staticmethod
    def get_por_periodo(data_inicial: date, data_final: date) -> List['OrdemProducao']:
        """Retorna ordens de produção em um período específico."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM ordens_producao 
                    WHERE data_inicio BETWEEN ? AND ?
                    ORDER BY prioridade, data_inicio
                """, (
                    data_inicial.strftime('%Y-%m-%d'),
                    data_final.strftime('%Y-%m-%d')
                ))
                results = cursor.fetchall()
                
                return [OrdemProducao(
                    id=row['id'],
                    numero_pedido=row['numero_pedido'],
                    cliente=row['cliente'],
                    injetora_id=row['injetora_id'],
                    molde_id=row['molde_id'],
                    quantidade_total=row['quantidade_total'],
                    quantidade_produzida=row['quantidade_produzida'],
                    ciclo_segundos=row['ciclo_segundos'],
                    material=row['material'],
                    percentual_master=row['percentual_master'],
                    peso_peca=row['peso_peca'],
                    peso_total=row['peso_total'],
                    data_inicio=datetime.strptime(row['data_inicio'], '%Y-%m-%d').date(),
                    data_fim=datetime.strptime(row['data_fim'], '%Y-%m-%d').date() if row['data_fim'] else None,
                    status=row['status'],
                    prioridade=row['prioridade'],
                    observacoes=row['observacoes'],
                    data_cadastro=row['data_cadastro']
                ) for row in results]
        except Exception as e:
            print(f"Erro ao buscar ordens por período: {str(e)}")
            return []

    @staticmethod
    def get_em_producao() -> List['OrdemProducao']:
        """Retorna todas as ordens em produção."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM ordens_producao 
                    WHERE status IN ('Pendente', 'Em Produção')
                    ORDER BY prioridade, data_inicio
                """)
                results = cursor.fetchall()
                
                return [OrdemProducao(
                    id=row['id'],
                    numero_pedido=row['numero_pedido'],
                    cliente=row['cliente'],
                    injetora_id=row['injetora_id'],
                    molde_id=row['molde_id'],
                    quantidade_total=row['quantidade_total'],
                    quantidade_produzida=row['quantidade_produzida'],
                    ciclo_segundos=row['ciclo_segundos'],
                    material=row['material'],
                    percentual_master=row['percentual_master'],
                    peso_peca=row['peso_peca'],
                    peso_total=row['peso_total'],
                    data_inicio=datetime.strptime(row['data_inicio'], '%Y-%m-%d').date(),
                    data_fim=datetime.strptime(row['data_fim'], '%Y-%m-%d').date() if row['data_fim'] else None,
                    status=row['status'],
                    prioridade=row['prioridade'],
                    observacoes=row['observacoes'],
                    data_cadastro=row['data_cadastro']
                ) for row in results]
        except Exception as e:
            print(f"Erro ao buscar ordens em produção: {str(e)}")
            return []

    @staticmethod
    def get_by_id(id: int) -> Optional['OrdemProducao']:
        """Busca uma ordem de produção pelo ID."""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ordens_producao WHERE id = ?", (id,))
                row = cursor.fetchone()
                
                if row:
                    return OrdemProducao(
                        id=row['id'],
                        numero_pedido=row['numero_pedido'],
                        cliente=row['cliente'],
                        injetora_id=row['injetora_id'],
                        molde_id=row['molde_id'],
                        quantidade_total=row['quantidade_total'],
                        quantidade_produzida=row['quantidade_produzida'],
                        ciclo_segundos=row['ciclo_segundos'],
                        material=row['material'],
                        percentual_master=row['percentual_master'],
                        peso_peca=row['peso_peca'],
                        peso_total=row['peso_total'],
                        data_inicio=datetime.strptime(row['data_inicio'], '%Y-%m-%d').date(),
                        data_fim=datetime.strptime(row['data_fim'], '%Y-%m-%d').date() if row['data_fim'] else None,
                        status=row['status'],
                        prioridade=row['prioridade'],
                        observacoes=row['observacoes'],
                        data_cadastro=row['data_cadastro']
                    )
                return None
        except Exception as e:
            print(f"Erro ao buscar ordem por ID: {str(e)}")
            return None

    def verificar_atrasos(self) -> bool:
        """Verifica se a ordem está atrasada."""
        if self.status in ['Concluído', 'Cancelado']:
            return False
            
        hoje = date.today()
        if self.data_fim and hoje > self.data_fim:
            self.status = 'Atrasado'
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE ordens_producao SET status = ? WHERE id = ?",
                    ('Atrasado', self.id)
                )
                conn.commit()
            return True
        return False

    def cancelar(self, motivo: str) -> None:
        """Cancela a ordem de produção e libera recursos."""
        if not motivo:
            raise ValueError("Motivo do cancelamento é obrigatório")

        with get_connection() as conn:
            cursor = conn.cursor()
            
            self.status = 'Cancelado'
            self.observacoes = f"{self.observacoes}\nCancelado: {motivo}" if self.observacoes else f"Cancelado: {motivo}"
            
            cursor.execute("""
                UPDATE ordens_producao 
                SET status = ?, observacoes = ? 
                WHERE id = ?
            """, (self.status, self.observacoes, self.id))
            
            # Liberar recursos
            cursor.execute(
                "UPDATE injetoras SET status = 'Disponível' WHERE id = ?",
                (self.injetora_id,)
            )
            cursor.execute(
                "UPDATE moldes SET status = 'Disponível' WHERE id = ?",
                (self.molde_id,)
            )
            
            conn.commit()

    def get_eficiencia(self) -> float:
        """Calcula a eficiência da produção."""
        if self.quantidade_total == 0:
            return 0.0
        return (self.quantidade_produzida / self.quantidade_total) * 100