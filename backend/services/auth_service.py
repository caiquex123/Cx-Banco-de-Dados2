"""
Serviço de autenticação para o backend CxIA.

Gerencia registro, login, logout e validação de usuários.
"""

import sqlite3
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from database import get_connection
from utils.helpers import gerar_id, agora, hash_senha, verificar_senha
from utils.jwt_utils import criar_token, obter_expires_at


def registrar_usuario(nome: str, email: str, senha: str) -> Optional[Dict[str, Any]]:
    """
    Registra um novo usuário no banco de dados.
    
    Args:
        nome (str): Nome completo do usuário.
        email (str): Email único do usuário.
        senha (str): Senha em texto puro (será hasheada internamente).
        
    Returns:
        dict: Dados do usuário criado com token de sessão, ou None se erro.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar se email já existe
            cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
            if cursor.fetchone():
                print(f"[ERRO] Email já cadastrado: {email}")
                return None
            
            user_id = gerar_id()
            timestamp = agora()
            senha_hash = hash_senha(senha)
            
            # Criar usuário
            cursor.execute("""
                INSERT INTO usuarios (id, nome, email, senha_hash, provider, is_guest, ativo, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, 'email', 0, 1, ?, ?)
            """, (user_id, nome, email, senha_hash, timestamp, timestamp))
            
            # Criar registro de tokens (50k padrão para free)
            tokens_id = gerar_id()
            janela_inicio = timestamp
            cursor.execute("""
                INSERT INTO tokens_usuarios (id, user_id, tokens_usados, limite_tokens, janela_inicio, plano, atualizado_em)
                VALUES (?, ?, 0, 50000, ?, 'free', ?)
            """, (tokens_id, user_id, janela_inicio, timestamp))
            
            conn.commit()
            
            # Gerar token JWT
            token = criar_token(user_id, email)
            expires_at = obter_expires_at(token) or (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
            
            return {
                "user_id": user_id,
                "nome": nome,
                "email": email,
                "token": token,
                "expires_at": expires_at
            }
            
    except Exception as e:
        print(f"[ERRO] Erro ao registrar usuário: {e}")
        return None


def login_usuario(email: str, senha: str) -> Optional[Dict[str, Any]]:
    """
    Realiza login de usuário verificando email e senha.
    
    Args:
        email (str): Email do usuário.
        senha (str): Senha em texto puro.
        
    Returns:
        dict: Dados do usuário com token de sessão, ou None se credenciais inválidas.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Buscar usuário por email
            cursor.execute("""
                SELECT id, nome, email, senha_hash, photo_url, provider, is_guest, criado_em, atualizado_em
                FROM usuarios
                WHERE email = ? AND ativo = 1
            """, (email,))
            
            row = cursor.fetchone()
            if not row:
                print(f"[ERRO] Usuário não encontrado: {email}")
                return None
            
            usuario = dict(row)
            
            # Se for guest, não verifica senha
            if usuario["is_guest"]:
                # Para guest, apenas gera token
                pass
            else:
                # Verificar senha
                if not verificar_senha(senha, usuario["senha_hash"]):
                    print(f"[ERRO] Senha incorreta para: {email}")
                    return None
            
            # Gerar token JWT
            token = criar_token(usuario["id"], usuario["email"])
            expires_at = obter_expires_at(token) or (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
            
            return {
                "user_id": usuario["id"],
                "nome": usuario["nome"],
                "email": usuario["email"],
                "photo_url": usuario["photo_url"],
                "provider": usuario["provider"],
                "is_guest": bool(usuario["is_guest"]),
                "token": token,
                "expires_at": expires_at
            }
            
    except Exception as e:
        print(f"[ERRO] Erro ao fazer login: {e}")
        return None


def buscar_usuario_por_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca dados de um usuário pelo ID.
    
    Args:
        user_id (str): ID do usuário.
        
    Returns:
        dict: Dados do usuário, ou None se não encontrado.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nome, email, photo_url, provider, is_guest, criado_em, atualizado_em
                FROM usuarios
                WHERE id = ? AND ativo = 1
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
    except Exception as e:
        print(f"[ERRO] Erro ao buscar usuário: {e}")
        return None


def atualizar_usuario(user_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Atualiza dados de um usuário.
    
    Args:
        user_id (str): ID do usuário.
        **kwargs: Campos a atualizar (nome, photo_url).
        
    Returns:
        dict: Dados atualizados do usuário, ou None se erro.
    """
    campos_validos = ["nome", "photo_url"]
    atualizacoes = {k: v for k, v in kwargs.items() if k in campos_validos}
    
    if not atualizacoes:
        return buscar_usuario_por_id(user_id)
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            campos_set = []
            valores = []
            for campo, valor in atualizacoes.items():
                campos_set.append(f"{campo} = ?")
                valores.append(valor)
            
            valores.append(agora())  # atualizado_em
            valores.append(user_id)
            
            cursor.execute(f"""
                UPDATE usuarios
                SET {', '.join(campos_set)}, atualizado_em = ?
                WHERE id = ?
            """, valores)
            
            conn.commit()
            
            return buscar_usuario_por_id(user_id)
            
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar usuário: {e}")
        return None


def criar_usuario_guest() -> Optional[Dict[str, Any]]:
    """
    Cria um usuário convidado (guest) temporário.
    
    Returns:
        dict: Dados do usuário guest com token, ou None se erro.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            user_id = gerar_id()
            email = f"guest_{user_id}@temp.local"
            nome = "Convidado"
            timestamp = agora()
            
            # Criar usuário guest (sem senha)
            cursor.execute("""
                INSERT INTO usuarios (id, nome, email, senha_hash, provider, is_guest, ativo, criado_em, atualizado_em)
                VALUES (?, ?, ?, NULL, 'guest', 1, 1, ?, ?)
            """, (user_id, nome, email, timestamp, timestamp))
            
            # Criar registro de tokens
            tokens_id = gerar_id()
            cursor.execute("""
                INSERT INTO tokens_usuarios (id, user_id, tokens_usados, limite_tokens, janela_inicio, plano, atualizado_em)
                VALUES (?, ?, 0, 50000, ?, 'free', ?)
            """, (tokens_id, user_id, timestamp, timestamp))
            
            conn.commit()
            
            # Gerar token JWT
            token = criar_token(user_id, email)
            expires_at = obter_expires_at(token) or (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
            
            return {
                "user_id": user_id,
                "nome": nome,
                "email": email,
                "token": token,
                "expires_at": expires_at,
                "is_guest": True
            }
            
    except Exception as e:
        print(f"[ERRO] Erro ao criar usuário guest: {e}")
        return None
