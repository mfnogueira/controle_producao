import sqlite3
import base64
import pandas as pd
from sqlite3 import Connection, Cursor
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, date
import logging
from config.settings import DATABASE_NAME

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def dict_factory(cursor: Cursor, row: tuple) -> dict:
    """Converte as linhas do SQLite para dicionário."""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def adapt_datetime(dt: datetime) -> str:
    """Adapta objeto datetime para string SQLite."""
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def adapt_date(d: date) -> str:
    """Adapta objeto date para string SQLite."""
    return d.strftime('%Y-%m-%d')

def get_table_download_link(df: pd.DataFrame, filename: str) -> str:
    """
    Gera um link HTML para download de DataFrame como CSV.
    
    Args:
        df: DataFrame para download
        filename: Nome do arquivo sem extensão
    
    Returns:
        String HTML com link para download
    """
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    b64 = base64.b64encode(csv.encode('utf-8-sig')).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">📥 Download {filename}</a>'
    return href

# Registrar adaptadores
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_adapter(date, adapt_date)

class DatabaseError(Exception):
    """Exceção personalizada para erros de banco de dados."""
    pass

@contextmanager
def get_connection() -> Connection:
    """
    Gerencia a conexão com o banco de dados.
    
    Returns:
        Connection: Conexão SQLite configurada
    
    Raises:
        DatabaseError: Se houver erro ao conectar ou configurar
    """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = dict_factory
        
        # Configurações importantes
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('PRAGMA encoding = "UTF-8"')
        conn.execute('PRAGMA journal_mode = WAL')  # Write-Ahead Logging
        conn.execute('PRAGMA busy_timeout = 5000')  # 5 segundos
        
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Erro ao conectar ao banco: {str(e)}")
        raise DatabaseError(f"Erro de conexão: {str(e)}")
    finally:
        conn.close()

def execute_query(
    query: str,
    params: Optional[Union[tuple, dict]] = None,
    fetch_one: bool = False
) -> Union[List[Dict[str, Any]], Dict[str, Any], None]:
    """
    Executa uma query e retorna os resultados.
    
    Args:
        query: Query SQL
        params: Parâmetros para a query
        fetch_one: Se True, retorna apenas um resultado
    
    Returns:
        Resultado da query (lista de dicts, dict único ou None)
    
    Raises:
        DatabaseError: Se houver erro na execução
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Erro ao executar query: {str(e)}\nQuery: {query}\nParams: {params}")
        raise DatabaseError(f"Erro na query: {str(e)}")

def execute_many(
    query: str,
    params_list: List[Union[tuple, dict]]
) -> None:
    """
    Executa múltiplas queries em uma transação.
    
    Args:
        query: Query SQL
        params_list: Lista de parâmetros
    
    Raises:
        DatabaseError: Se houver erro na execução
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Erro ao executar multiple queries: {str(e)}")
        raise DatabaseError(f"Erro em execute_many: {str(e)}")

def execute_transaction(
    queries: List[Tuple[str, Union[tuple, dict]]]
) -> None:
    """
    Executa múltiplas queries em uma única transação.
    
    Args:
        queries: Lista de tuplas (query, params)
    
    Raises:
        DatabaseError: Se houver erro na transação
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                for query, params in queries:
                    cursor.execute(query, params)
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise DatabaseError(f"Erro na transação: {str(e)}")
    except sqlite3.Error as e:
        logger.error(f"Erro ao executar transação: {str(e)}")
        raise DatabaseError(f"Erro de conexão na transação: {str(e)}")

def get_table_info(table_name: str) -> List[Dict[str, Any]]:
    """
    Retorna informações sobre uma tabela.
    
    Args:
        table_name: Nome da tabela
    
    Returns:
        Lista com informações das colunas
    """
    return execute_query("PRAGMA table_info(?)", (table_name,))

def backup_database(backup_path: str) -> None:
    """
    Cria um backup do banco de dados.
    
    Args:
        backup_path: Caminho para salvar o backup
    
    Raises:
        DatabaseError: Se houver erro no backup
    """
    try:
        with get_connection() as conn:
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
    except sqlite3.Error as e:
        logger.error(f"Erro ao criar backup: {str(e)}")
        raise DatabaseError(f"Erro no backup: {str(e)}")

def insert_returning_id(
    table: str,
    data: Dict[str, Any]
) -> int:
    """
    Insere dados e retorna o ID gerado.
    
    Args:
        table: Nome da tabela
        data: Dicionário com dados para inserir
    
    Returns:
        ID do registro inserido
    
    Raises:
        DatabaseError: Se houver erro na inserção
    """
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(data.values()))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Erro ao inserir em {table}: {str(e)}")
        raise DatabaseError(f"Erro na inserção: {str(e)}")

def update_by_id(
    table: str,
    id: int,
    data: Dict[str, Any]
) -> None:
    """
    Atualiza registro por ID.
    
    Args:
        table: Nome da tabela
        id: ID do registro
        data: Dicionário com dados para atualizar
    
    Raises:
        DatabaseError: Se houver erro na atualização
    """
    set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE id = ?"
    params = tuple(data.values()) + (id,)
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Erro ao atualizar {table}: {str(e)}")
        raise DatabaseError(f"Erro na atualização: {str(e)}")

def delete_by_id(table: str, id: int) -> None:
    """
    Remove registro por ID.
    
    Args:
        table: Nome da tabela
        id: ID do registro
    
    Raises:
        DatabaseError: Se houver erro na remoção
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Erro ao deletar de {table}: {str(e)}")
        raise DatabaseError(f"Erro na remoção: {str(e)}")