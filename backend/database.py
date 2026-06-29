"""
Gerenciamento de conexão com o banco de dados SQLite.

Configura conexão thread-safe com WAL mode e foreign keys habilitadas.
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv

load_dotenv()

# Caminho do arquivo de banco de dados (configurável via variável de ambiente)
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/cxia.db")


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager para obter conexão com o banco de dados.
    
    Configurações aplicadas automaticamente:
    - row_factory = sqlite3.Row (retorna resultados como dicionários)
    - PRAGMA journal_mode=WAL (suporta múltiplas leituras/escritas simultâneas)
    - PRAGMA foreign_keys=ON (garante integridade referencial)
    
    Yields:
        sqlite3.Connection: Conexão com o banco de dados.
    
    Example:
        >>> with get_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM usuarios")
    """
    # Criar diretório do banco de dados se não existir
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    try:
        # Habilitar WAL mode para melhor concorrência
        conn.execute("PRAGMA journal_mode=WAL")
        # Habilitar foreign keys
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """
    Inicializa o banco de dados criando todas as tabelas necessárias.
    Deve ser chamado apenas uma vez na inicialização da aplicação.
    """
    from models import criar_todas_as_tabelas
    
    with get_connection() as conn:
        criar_todas_as_tabelas(conn)
        conn.commit()
