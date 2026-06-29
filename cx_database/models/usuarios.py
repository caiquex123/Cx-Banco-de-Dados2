"""
Módulo de operações CRUD para usuários no banco de dados CX SAAS.

Este módulo gerencia todas as operações relacionadas a usuários no banco de dados,
incluindo criação, autenticação, atualização e gerenciamento de contas.

Tabela: usuarios (id, email, senha_hash, is_guest, ativo, criado_em, atualizado_em)

Funções disponíveis:
    - criar_usuario(): Cria um novo usuário com senha hash
    - buscar_usuario_por_id(): Busca usuário pelo ID
    - buscar_usuario_por_email(): Busca usuário pelo email
    - listar_usuarios(): Lista todos ou apenas ativos
    - atualizar_usuario(): Atualiza dados do usuário
    - deletar_usuario(): Remove ou desativa usuário
    - usuario_existe(): Verifica se email já está cadastrado
"""

import sqlite3
from typing import Optional, List, Dict, Any

from cx_database.connection import get_connection
from cx_database.utils.helpers import gerar_id, agora, hash_senha, verificar_senha
from cx_database.utils.validators import validar_email, validar_senha_forca


def criar_usuario(
    email: str,
    senha: str,
    is_guest: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Cria um novo usuário no banco de dados.

    A senha é automaticamente convertida para hash SHA-256 antes de ser salva.
    Validações são realizadas para email e força da senha.

    Args:
        email (str): Email único do usuário.
        senha (str): Senha em texto puro (será convertida para hash internamente).
        is_guest (bool, optional): Se True, cria usuário convidado sem senha. Default: False.

    Returns:
        dict: Dicionário com os dados do usuário criado, ou None em caso de erro.
    """
    if not validar_email(email):
        print(f"[ERRO] Email inválido: {email}")
        return None
    
    if not is_guest and not validar_senha_forca(senha):
        print(f"[ERRO] Senha fraca. Requisitos: 8+ caracteres, 1 número, 1 maiúscula, 1 minúscula")
        return None
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
            if cursor.fetchone() is not None:
                print(f"[ERRO] Email já cadastrado: {email}")
                return None
            
            usuario_id = gerar_id()
            timestamp = agora()
            senha_hash = None if is_guest else hash_senha(senha)
            
            cursor.execute("""
                INSERT INTO usuarios (id, email, senha_hash, is_guest, ativo, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (usuario_id, email, senha_hash, 1 if is_guest else 0, 1, timestamp, timestamp))
            
            conn.commit()
            
            return buscar_usuario_por_id(usuario_id)
            
    except sqlite3.IntegrityError as e:
        print(f"[ERRO] Integridade violada ao criar usuário: {e}")
        return None
    except Exception as e:
        print(f"[ERRO] Erro inesperado ao criar usuário: {e}")
        return None


def buscar_usuario_por_id(usuario_id: str) -> Optional[Dict[str, Any]]:
    """Busca um usuário pelo seu ID único."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, is_guest, ativo, criado_em, atualizado_em
                FROM usuarios WHERE id = ?
            """, (usuario_id,))
            resultado = cursor.fetchone()
            return dict(resultado) if resultado else None
    except Exception as e:
        print(f"[ERRO] Erro ao buscar usuário por ID: {e}")
        return None


def buscar_usuario_por_email(email: str) -> Optional[Dict[str, Any]]:
    """Busca um usuário pelo email."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, email, senha_hash, is_guest, ativo, criado_em, atualizado_em
                FROM usuarios WHERE email = ?
            """, (email,))
            resultado = cursor.fetchone()
            return dict(resultado) if resultado else None
    except Exception as e:
        print(f"[ERRO] Erro ao buscar usuário por email: {e}")
        return None


def listar_usuarios(ativos_apenas: bool = True) -> List[Dict[str, Any]]:
    """Lista todos os usuários."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            if ativos_apenas:
                cursor.execute("SELECT id, email, is_guest, ativo, criado_em FROM usuarios WHERE ativo = 1 ORDER BY email")
            else:
                cursor.execute("SELECT id, email, is_guest, ativo, criado_em FROM usuarios ORDER BY email")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"[ERRO] Erro ao listar usuários: {e}")
        return []


def atualizar_usuario(usuario_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Atualiza campos específicos de um usuário."""
    campos_validos = ["ativo"]
    atualizacoes = {k: v for k, v in kwargs.items() if k in campos_validos}
    
    if not atualizacoes:
        return buscar_usuario_por_id(usuario_id)
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            campos_set = [f"{k} = ?" for k in atualizacoes.keys()]
            valores = list(atualizacoes.values()) + [agora(), usuario_id]
            
            cursor.execute(f"""
                UPDATE usuarios SET {', '.join(campos_set)}, atualizado_em = ?
                WHERE id = ?
            """, valores)
            conn.commit()
            
            return buscar_usuario_por_id(usuario_id) if cursor.rowcount > 0 else None
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar usuário: {e}")
        return None


def deletar_usuario(usuario_id: str) -> bool:
    """Remove um usuário do banco de dados."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"[ERRO] Erro ao deletar usuário: {e}")
        return False


def usuario_existe(email: str) -> bool:
    """Verifica se um email já está cadastrado."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM usuarios WHERE email = ? LIMIT 1", (email,))
            return cursor.fetchone() is not None
    except Exception:
        return False


if __name__ == "__main__":
    from cx_database.setup import setup_completo
    setup_completo()
    
    print("=" * 50)
    print("=== TESTES DO MÓDULO usuarios.py ===")
    print("=" * 50)
    
    print("\n[TESTE 1] Criar usuário:")
    user = criar_usuario("teste@email.com", "Senha123")
    print(f"  Usuário criado: {user is not None}")
    
    if user:
        print("\n[TESTE 2] Buscar por ID:")
        buscado = buscar_usuario_por_id(user["id"])
        print(f"  Encontrado: {buscado is not None}")
        
        print("\n[TESTE 3] Buscar por email:")
        por_email = buscar_usuario_por_email("teste@email.com")
        print(f"  Encontrado: {por_email is not None}")
        
        print("\n[TESTE 4] Verificar existência:")
        existe = usuario_existe("teste@email.com")
        print(f"  Existe: {existe}")
        
        print("\n[TESTE 5] Listar usuários:")
        lista = listar_usuarios()
        print(f"  Total: {len(lista)}")
        
        print("\n[TESTE 6] Deletar usuário:")
        deletado = deletar_usuario(user["id"])
        print(f"  Deletado: {deletado}")
    
    print("\n" + "=" * 50)
    print("Todos os testes do usuarios.py foram executados!")
    print("=" * 50)
