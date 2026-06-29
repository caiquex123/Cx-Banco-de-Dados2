"""
Módulo de conexão com o banco de dados SQLite para o CX SaaS.

Este módulo gerencia todas as conexões com o banco de dados SQLite,
implementando um context manager para garantir que as conexões sejam
sempre abertas e fechadas corretamente.

Configurações:
    - O caminho do arquivo .db é configurável via variável de ambiente DATABASE_PATH
    - Fallback padrão: ./cx_database/data/cx_saas.db
    - Suporte a múltiplas threads com check_same_thread=False
    - Resultados acessíveis como dicionários via row_factory

Uso recomendado:
    ```python
    from cx_database.connection import get_connection
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios")
        resultados = cursor.fetchall()
    ```
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Generator


# Caminho padrão do banco de dados
DEFAULT_DB_PATH = "./cx_database/data/cx_saas.db"


def obter_caminho_db() -> str:
    """
    Obtém o caminho do arquivo de banco de dados.

    Verifica primeiro a variável de ambiente DATABASE_PATH.
    Se não estiver definida, usa o caminho padrão.
    Garante que o diretório exista, criando-o se necessário.

    Returns:
        str: Caminho absoluto para o arquivo .db

    Side Effects:
        Cria o diretório pai se ele não existir.
    """
    db_path = os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)

    # Converter para caminho absoluto se for relativo
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(db_path)

    # Garantir que o diretório existe
    diretorio = os.path.dirname(db_path)
    if diretorio and not os.path.exists(diretorio):
        os.makedirs(diretorio, exist_ok=True)
        print(f"[INFO] Diretório criado: {diretorio}")

    return db_path


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager para gerenciar conexões com o banco de dados SQLite.

    Este context manager garante que:
    1. A conexão seja aberta corretamente com configurações apropriadas
    2. A conexão seja sempre fechada, mesmo em caso de exceção
    3. Múltiplas threads possam acessar o banco (check_same_thread=False)
    4. Os resultados das consultas sejam acessíveis como dicionários

    Yields:
        sqlite3.Connection: Conexão ativa com o banco de dados

    Raises:
        sqlite3.Error: Se houver erro ao conectar ou operar no banco

    Example:
        >>> with get_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT * FROM usuarios")
        ...     resultados = cursor.fetchall()
    """
    db_path = obter_caminho_db()
    conn = None
    try:
        # Criar conexão com SQLite
        conn = sqlite3.connect(
            database=db_path,
            check_same_thread=False,  # Permitir múltiplas threads (necessário para FastAPI)
            timeout=30.0  # Timeout de 30 segundos para operações bloqueadas
        )

        # Configurar para retornar resultados como dicionários (acesso por nome de coluna)
        conn.row_factory = sqlite3.Row

        # Habilitar foreign keys para integridade referencial
        conn.execute("PRAGMA foreign_keys = ON")

        # Habilitar WAL mode para melhor concorrência (leituras não bloqueiam escritas)
        conn.execute("PRAGMA journal_mode = WAL")

        yield conn

    except sqlite3.Error as e:
        print(f"[ERRO SQLite] Erro na conexão ou operação: {e}")
        raise
    finally:
        if conn:
            conn.close()


def testar_conexao() -> bool:
    """
    Testa se a conexão com o banco de dados está funcionando.

    Executa uma consulta simples para verificar se o banco está acessível.

    Returns:
        bool: True se a conexão estiver funcionando, False caso contrário.

    Example:
        >>> if testar_conexao():
        ...     print("Banco de dados OK!")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            resultado = cursor.fetchone()
            return resultado is not None and resultado[0] == 1
    except sqlite3.Error as e:
        print(f"[ERRO] Falha ao testar conexão: {e}")
        return False


def obter_info_banco() -> dict:
    """
    Obtém informações sobre o banco de dados atual.

    Returns:
        dict: Dicionário com informações do banco:
            - caminho (str): Caminho completo do arquivo .db
            - existe (bool): Se o arquivo existe no disco
            - tamanho_bytes (int): Tamanho do arquivo em bytes (0 se não existir)
    """
    db_path = obter_caminho_db()
    existe = os.path.exists(db_path)
    tamanho = os.path.getsize(db_path) if existe else 0

    return {
        "caminho": db_path,
        "existe": existe,
        "tamanho_bytes": tamanho
    }


if __name__ == "__main__":
    print("=" * 50)
    print("=== TESTES DO MÓDULO connection.py ===")
    print("=" * 50)

    print("\n[TESTE 1] Obter caminho do banco de dados:")
    caminho = obter_caminho_db()
    print(f"  Caminho configurado: {caminho}")

    print("\n[TESTE 2] Informações do banco:")
    info = obter_info_banco()
    print(f"  Caminho: {info['caminho']}")
    print(f"  Existe: {info['existe']}")
    print(f"  Tamanho: {info['tamanho_bytes']} bytes")

    print("\n[TESTE 3] Testar conexão:")
    conexao_ok = testar_conexao()
    print(f"  Conexão bem-sucedida: {conexao_ok}")

    print("\n[TESTE 4] Usar context manager para consulta:")
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as teste, 'ola' as mensagem")
            resultado = cursor.fetchone()
            print(f"  Resultado da consulta: teste={resultado['teste']}, mensagem='{resultado['mensagem']}'")
            print(f"  Acesso por nome de coluna funcionou: {resultado.keys() is not None}")
    except Exception as e:
        print(f"  Erro: {e}")

    print("\n[TESTE 5] Variável de ambiente DATABASE_PATH:")
    # Salvar valor original
    original = os.environ.get("DATABASE_PATH")

    # Testar com caminho customizado
    os.environ["DATABASE_PATH"] = "./teste_custom.db"
    caminho_custom = obter_caminho_db()
    print(f"  Com DATABASE_PATH='./teste_custom.db': {caminho_custom}")

    # Restaurar original
    if original:
        os.environ["DATABASE_PATH"] = original
    elif "DATABASE_PATH" in os.environ:
        del os.environ["DATABASE_PATH"]

    # Limpar arquivo de teste
    if os.path.exists("./teste_custom.db"):
        os.remove("./teste_custom.db")
        print("  Arquivo de teste removido.")

    print("\n" + "=" * 50)
    print("Todos os testes do connection.py foram executados!")
    print("=" * 50)
