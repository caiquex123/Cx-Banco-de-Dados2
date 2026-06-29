"""
Módulo de configuração inicial do banco de dados CX SaaS.

Este módulo é responsável por criar todas as tabelas necessárias no banco
de dados, inserir dados iniciais (planos, admin padrão) e criar índices
para otimização de performance.

Tabelas criadas:
    - usuarios: Dados básicos de autenticação
    - perfis: Informações detalhadas do usuário (perfil, interesses, etc.)
    - conversas: Histórico de conversas com a IA
    - mensagens: Mensagens individuais dentro das conversas
    - projetos_ia: Projetos de IA dos usuários
    - configuracoes: Configurações por usuário (tema, idioma, preferences)
    - user_tokens: Saldo e controle de tokens
    - transacoes_tokens: Histórico de uso de tokens
    - assinaturas: Planos e status de assinatura
    - admins: Lista de administradores
    - sessoes: Sessões ativas (tokens de autenticação)

Funções principais:
    - criar_todas_as_tabelas(): Cria todas as tabelas se não existirem
    - criar_indices(): Cria índices para otimização
    - inserir_admin_padrao(): Cria admin com email adm123@gmail.com se não existir
    - setup_completo(): Executa todo o setup de uma vez
    - resetar_banco(): Apaga e recria tudo (apenas para desenvolvimento)

Uso:
    ```python
    from cx_database.setup import setup_completo
    setup_completo()
    ```

Ou execute diretamente:
    ```bash
    python setup.py
    ```
"""

import sqlite3
import os
from cx_database.connection import get_connection, obter_caminho_db
from cx_database.utils.helpers import gerar_id, agora, hash_senha


def criar_tabela_usuarios(conn: sqlite3.Connection) -> None:
    """
    Cria a tabela de usuários se não existir.

    Args:
        conn: Conexão ativa com o banco de dados SQLite.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            senha_hash TEXT,
            is_guest INTEGER DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            criado_em TEXT,
            atualizado_em TEXT
        )
    """)
    print("[SETUP] Tabela 'usuarios' verificada/criada.")


def criar_tabela_perfis(conn: sqlite3.Connection) -> None:
    """
    Cria a tabela de perfis se não existir.

    Args:
        conn: Conexão ativa com o banco de dados SQLite.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfis (
            id TEXT PRIMARY KEY REFERENCES usuarios(id),
            email TEXT,
            username TEXT,
            display_name TEXT,
            nome TEXT,
            idade INTEGER,
            interesses TEXT DEFAULT '[]',
            profile_picture_url TEXT,
            avatar_url TEXT,
            bio TEXT,
            response_style TEXT DEFAULT 'amigável',
            temporal_memory TEXT DEFAULT '{"keyEvents": []}',
            criado_em TEXT,
            atualizado_em TEXT
        )
    """)
    print("[SETUP] Tabela 'perfis' verificada/criada.")


def criar_tabela_conversas(conn: sqlite3.Connection) -> None:
    """
    Cria a tabela de conversas se não existir.

    Args:
        conn: Conexão ativa com o banco de dados SQLite.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversas (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            titulo TEXT,
            modo TEXT DEFAULT 'chat',
            active_agent_ids TEXT DEFAULT '[]',
            is_archived INTEGER DEFAULT 0,
            is_anonymous INTEGER DEFAULT 0,
            criado_em TEXT,
            ultima_modificacao TEXT
        )
    """)
    print("[SETUP] Tabela 'conversas' verificada/criada.")


def criar_tabela_mensagens(conn: sqlite3.Connection) -> None:
    """
    Cria a tabela de mensagens se não existir.

    Args:
        conn: Conexão ativa com o banco de dados SQLite.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id TEXT PRIMARY KEY,
            conversa_id TEXT NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,
            user_id TEXT REFERENCES usuarios(id) ON DELETE CASCADE,
            role TEXT CHECK(role IN ('user', 'assistant', 'system', 'model')) NOT NULL,
            content TEXT,
            attachment TEXT DEFAULT NULL,
            actions TEXT DEFAULT NULL,
            author TEXT DEFAULT NULL,
            image_urls TEXT DEFAULT '[]',
            criado_em TEXT
        )
    """)
    print("[SETUP] Tabela 'mensagens' verificada/criada.")


def criar_tabela_projetos_ia(conn: sqlite3.Connection) -> None:
    """
    Cria a tabela de projetos de IA se não existir.

    Args:
        conn: Conexão ativa com o banco de dados SQLite.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projetos_ia (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            nome TEXT,
            descricao TEXT,
            icone TEXT,
            files TEXT DEFAULT '[]',
            chat_history TEXT DEFAULT '[]',
            criado_em TEXT,
            atualizado_em TEXT,
            ultima_modificacao TEXT
        )
    """)
    print("[SETUP] Tabela 'projetos_ia' verificada/criada.")


def criar_tabela_configuracoes(conn: sqlite3.Connection) -> None:
    """
    Cria a tabela de configurações se não existir.

    Args:
        conn: Conexão ativa com o banco de dados SQLite.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            tema TEXT DEFAULT 'dark',
            idioma TEXT DEFAULT 'pt-BR',
            preferences TEXT DEFAULT '{}',
            criado_em TEXT,
            atualizado_em TEXT
        )
    """)
    print("[SETUP] Tabela 'configuracoes' verificada/criada.")


def criar_tabela_user_tokens(conn: sqlite3.Connection) -> None:
    """
    Cria a tabela de controle de tokens se não existir.

    Args:
        conn: Conexão ativa com o banco de dados SQLite.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            balance INTEGER DEFAULT 0,
            initial_tokens INTEGER DEFAULT 500,
            total_used INTEGER DEFAULT 0,
            total_received INTEGER DEFAULT 500,
            last_usage_at TEXT,
            last_refill_at TEXT,
            next_refill_at TEXT,
            waiting_refill INTEGER DEFAULT 0,
            criado_em TEXT,
            atualizado_em TEXT
        )
    """)
    print("[SETUP] Tabela 'user_tokens' verificada/criada.")


def criar_tabela_transacoes_tokens(conn: sqlite3.Connection) -> None:
    """
    Cria a tabela de histórico de transações de tokens se não existir.

    Args:
        conn: Conexão ativa com o banco de dados SQLite.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            tipo TEXT CHECK(tipo IN ('usage','refill','bonus','admin_adjustment','initial_grant')) NOT NULL,
            amount INTEGER NOT NULL,
            balance_before INTEGER,
            balance_after INTEGER,
            descricao TEXT,
            criado_em TEXT
        )
    """)
    print("[SETUP] Tabela 'transacoes_tokens' verificada/criada.")


def criar_tabela_assinaturas(conn: sqlite3.Connection) -> None:
    """
    Cria a tabela de assinaturas se não existir.

    Args:
        conn: Conexão ativa com o banco de dados SQLite.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assinaturas (
            id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            plano TEXT DEFAULT 'free',
            status TEXT DEFAULT 'active',
            expires_at TEXT,
            premium_until TEXT,
            used_codes TEXT DEFAULT '[]',
            criado_em TEXT,
            atualizado_em TEXT
        )
    """)
    print("[SETUP] Tabela 'assinaturas' verificada/criada.")


def criar_tabela_admins(conn: sqlite3.Connection) -> None:
    """
    Cria a tabela de administradores se não existir.

    Args:
        conn: Conexão ativa com o banco de dados SQLite.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            email TEXT UNIQUE NOT NULL,
            criado_em TEXT
        )
    """)
    print("[SETUP] Tabela 'admins' verificada/criada.")


def criar_tabela_sessoes(conn: sqlite3.Connection) -> None:
    """
    Cria a tabela de sessões se não existir.

    Args:
        conn: Conexão ativa com o banco de dados SQLite.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessoes (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            criado_em TEXT
        )
    """)
    print("[SETUP] Tabela 'sessoes' verificada/criada.")


def criar_todas_as_tabelas() -> bool:
    """
    Cria todas as tabelas do banco de dados em ordem correta.

    A ordem de criação respeita as dependências de chaves estrangeiras.

    Returns:
        bool: True se todas as tabelas foram criadas com sucesso, False caso contrário.
    """
    try:
        with get_connection() as conn:
            # Tabelas sem dependências primeiro
            criar_tabela_usuarios(conn)
            
            # Tabelas que dependem apenas de usuarios
            criar_tabela_perfis(conn)
            criar_tabela_configuracoes(conn)
            criar_tabela_user_tokens(conn)
            criar_tabela_assinaturas(conn)
            criar_tabela_admins(conn)
            criar_tabela_sessoes(conn)
            
            # Tabelas de domínio
            criar_tabela_conversas(conn)
            criar_tabela_mensagens(conn)
            criar_tabela_projetos_ia(conn)
            criar_tabela_transacoes_tokens(conn)
            
            conn.commit()
            print("\n[SETUP] Todas as tabelas foram criadas com sucesso!")
            return True
    except sqlite3.Error as e:
        print(f"[ERRO] Falha ao criar tabelas: {e}")
        return False


def criar_indices() -> bool:
    """
    Cria índices para otimização de consultas frequentes.

    Índices criados:
    - conversas.user_id: Busca de conversas por usuário
    - mensagens.conversa_id: Busca de mensagens por conversa
    - transacoes_tokens.user_id: Histórico de tokens por usuário
    - sessoes.token: Lookup de sessão por token
    - sessoes.expires_at: Limpeza de sessões expiradas
    - usuarios.email: Login por email

    Returns:
        bool: True se todos os índices foram criados com sucesso, False caso contrário.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            indices = [
                "CREATE INDEX IF NOT EXISTS idx_conversas_user_id ON conversas(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_mensagens_conversa_id ON mensagens(conversa_id)",
                "CREATE INDEX IF NOT EXISTS idx_transacoes_user_id ON transacoes_tokens(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_sessoes_token ON sessoes(token)",
                "CREATE INDEX IF NOT EXISTS idx_sessoes_expires_at ON sessoes(expires_at)",
                "CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)",
                "CREATE INDEX IF NOT EXISTS idx_perfis_username ON perfis(username)",
                "CREATE INDEX IF NOT EXISTS idx_assinaturas_user_id ON assinaturas(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_projetos_ia_user_id ON projetos_ia(user_id)",
            ]
            
            for indice_sql in indices:
                cursor.execute(indice_sql)
            
            conn.commit()
            print(f"[SETUP] {len(indices)} índices criados/atualizados.")
            return True
            
    except sqlite3.Error as e:
        print(f"[ERRO] Falha ao criar índices: {e}")
        return False


def inserir_admin_padrao() -> bool:
    """
    Cria o usuário administrador padrão se não existir.

    O admin padrão tem email 'adm123@gmail.com' e recebe automaticamente:
    - Plano 'premium_max'
    - Registro na tabela admins
    - 500 tokens iniciais

    Returns:
        bool: True se o admin foi criado ou já existe, False em caso de erro.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar se admin já existe
            cursor.execute("SELECT id FROM usuarios WHERE email = ?", ("adm123@gmail.com",))
            if cursor.fetchone() is not None:
                print("[SETUP] Admin 'adm123@gmail.com' já existe.")
                return True
            
            # Criar usuário admin
            admin_id = gerar_id()
            senha_hash = hash_senha("Admin@123")  # Senha padrão (deve ser trocada)
            timestamp = agora()
            
            cursor.execute("""
                INSERT INTO usuarios (id, email, senha_hash, is_guest, ativo, criado_em, atualizado_em)
                VALUES (?, ?, ?, 0, 1, ?, ?)
            """, (admin_id, "adm123@gmail.com", senha_hash, timestamp, timestamp))
            
            # Criar perfil
            cursor.execute("""
                INSERT INTO perfis (id, email, username, display_name, nome, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (admin_id, "adm123@gmail.com", "adm123", "Administrador", "Admin Principal", timestamp, timestamp))
            
            # Criar configurações
            config_id = gerar_id()
            cursor.execute("""
                INSERT INTO configuracoes (id, user_id, tema, idioma, preferences, criado_em, atualizado_em)
                VALUES (?, ?, 'dark', 'pt-BR', '{}', ?, ?)
            """, (config_id, admin_id, timestamp, timestamp))
            
            # Criar assinatura premium_max
            assinatura_id = gerar_id()
            cursor.execute("""
                INSERT INTO assinaturas (id, user_id, plano, status, criado_em, atualizado_em)
                VALUES (?, ?, 'premium_max', 'active', ?, ?)
            """, (assinatura_id, admin_id, timestamp, timestamp))
            
            # Criar tokens
            tokens_id = gerar_id()
            cursor.execute("""
                INSERT INTO user_tokens (id, user_id, balance, initial_tokens, total_used, total_received, 
                                        last_refill_at, criado_em, atualizado_em)
                VALUES (?, ?, 500, 500, 0, 500, ?, ?, ?)
            """, (tokens_id, admin_id, timestamp, timestamp, timestamp))
            
            # Registrar transação inicial
            transacao_id = gerar_id()
            cursor.execute("""
                INSERT INTO transacoes_tokens (id, user_id, tipo, amount, balance_before, balance_after, descricao, criado_em)
                VALUES (?, ?, 'initial_grant', 500, 0, 500, 'Tokens iniciais - Admin', ?)
            """, (transacao_id, admin_id, timestamp))
            
            # Registrar como admin
            admin_record_id = gerar_id()
            cursor.execute("""
                INSERT INTO admins (id, user_id, email, criado_em)
                VALUES (?, ?, ?, ?)
            """, (admin_record_id, admin_id, "adm123@gmail.com", timestamp))
            
            conn.commit()
            
            print("[SETUP] Admin 'adm123@gmail.com' criado com plano 'premium_max' e 500 tokens.")
            return True
            
    except sqlite3.Error as e:
        print(f"[ERRO] Falha ao criar admin padrão: {e}")
        return False


def setup_completo() -> bool:
    """
    Executa todo o setup do banco de dados.

    Esta função chama:
    1. criar_todas_as_tabelas()
    2. criar_indices()
    3. inserir_admin_padrao()

    Returns:
        bool: True se todo o setup foi concluído com sucesso, False caso contrário.
    """
    print("=" * 60)
    print("=== CONFIGURAÇÃO INICIAL DO BANCO DE DADOS CX SAAS ===")
    print("=" * 60)
    
    caminho = obter_caminho_db()
    print(f"\nCaminho do banco: {caminho}")
    
    print("\n" + "-" * 60)
    print("Etapa 1: Criando tabelas...")
    print("-" * 60)
    
    if not criar_todas_as_tabelas():
        print("\n❌ Falha ao criar tabelas.")
        return False
    
    print("\n" + "-" * 60)
    print("Etapa 2: Criando índices de otimização...")
    print("-" * 60)
    
    if not criar_indices():
        print("\n❌ Falha ao criar índices.")
        return False
    
    print("\n" + "-" * 60)
    print("Etapa 3: Inserindo admin padrão...")
    print("-" * 60)
    
    if not inserir_admin_padrao():
        print("\n❌ Falha ao criar admin padrão.")
        return False
    
    print("\n" + "=" * 60)
    print("✅ CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print("\nO banco de dados está pronto para uso.")
    print("\nResumo:")
    print("  - 11 tabelas criadas")
    print("  - 9 índices de otimização")
    print("  - Admin padrão: adm123@gmail.com (senha: Admin@123)")
    print("\nVocê pode começar a usar os módulos em cx_database/models/")
    
    return True


def resetar_banco(confirmar: bool = False) -> bool:
    """
    Apaga todas as tabelas e recria o banco do zero.

    ATENÇÃO: Esta função remove TODOS os dados permanentemente!
    Use apenas em ambiente de desenvolvimento.

    Args:
        confirmar (bool): Se True, executa o reset sem pedir confirmação.

    Returns:
        bool: True se o reset foi realizado com sucesso, False caso contrário.

    Warning:
        Esta operação é IRREVERSÍVEL. Todos os dados serão perdidos.
    """
    if not confirmar:
        print("[ALERTA] Para resetar o banco, chame resetar_banco(confirmar=True)")
        return False

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Desabilitar foreign keys temporariamente
            cursor.execute("PRAGMA foreign_keys = OFF")

            # Obter lista de todas as tabelas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelas = cursor.fetchall()

            # Dropar cada tabela
            for tabela in tabelas:
                nome_tabela = tabela["name"]
                if nome_tabela != 'sqlite_sequence':  # Não dropar tabelas internas
                    cursor.execute(f"DROP TABLE IF EXISTS {nome_tabela}")
                    print(f"[RESET] Tabela '{nome_tabela}' removida.")

            # Dropar índices também
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
            indices = cursor.fetchall()
            for indice in indices:
                nome_indice = indice["name"]
                cursor.execute(f"DROP INDEX IF EXISTS {nome_indice}")
                print(f"[RESET] Índice '{nome_indice}' removido.")

            conn.commit()

            # Reabilitar foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")

            print("\n[RESET] Todas as tabelas e índices foram removidos.")
            print("[RESET] Recriando estrutura do zero...\n")

            # Recriar tudo
            return setup_completo()

    except sqlite3.Error as e:
        print(f"[ERRO] Falha ao resetar banco: {e}")
        return False


if __name__ == "__main__":
    setup_completo()
