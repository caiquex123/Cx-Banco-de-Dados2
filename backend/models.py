"""
Definição de todas as tabelas do banco de dados CxIA.

Cria as tabelas: usuarios, conversas, mensagens, tokens_usuarios, sessoes.
"""

import sqlite3


def criar_todas_as_tabelas(conn: sqlite3.Connection) -> None:
    """
    Cria todas as tabelas do banco de dados se ainda não existirem.
    
    Args:
        conn: Conexão ativa com o banco de dados SQLite.
    """
    cursor = conn.cursor()
    
    # Tabela: usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT,
            photo_url TEXT,
            provider TEXT DEFAULT 'email',
            is_guest INTEGER DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            criado_em TEXT NOT NULL,
            atualizado_em TEXT NOT NULL
        )
    """)
    
    # Tabela: conversas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversas (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            titulo TEXT NOT NULL DEFAULT 'Nova conversa',
            is_private INTEGER DEFAULT 0,
            criado_em TEXT NOT NULL,
            atualizado_em TEXT NOT NULL
        )
    """)
    
    # Tabela: mensagens
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id TEXT PRIMARY KEY,
            conversa_id TEXT NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,
            role TEXT CHECK(role IN ('user', 'assistant', 'system')) NOT NULL,
            content TEXT NOT NULL,
            thinking_time REAL DEFAULT NULL,
            criado_em TEXT NOT NULL
        )
    """)
    
    # Tabela: tokens_usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens_usuarios (
            id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            tokens_usados INTEGER DEFAULT 0,
            limite_tokens INTEGER DEFAULT 50000,
            janela_inicio TEXT NOT NULL,
            plano TEXT DEFAULT 'free',
            atualizado_em TEXT NOT NULL
        )
    """)
    
    # Tabela: sessoes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessoes (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            criado_em TEXT NOT NULL
        )
    """)
    
    # Criar índices para melhor performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversas_user_id ON conversas(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mensagens_conversa_id ON mensagens(conversa_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_user_id ON tokens_usuarios(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessoes_token ON sessoes(token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessoes_expires_at ON sessoes(expires_at)")
