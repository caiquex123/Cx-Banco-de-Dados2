"""
Serviço de gerenciamento de tokens para o backend CxIA.

Gerencia saldo, consumo atômico e reset de janela de tokens.
"""

import sqlite3
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from database import get_connection
from utils.helpers import gerar_id, agora


def get_or_create_tokens(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtém ou cria registro de tokens para um usuário.
    
    Args:
        user_id (str): ID do usuário.
        
    Returns:
        dict: Dados de tokens do usuário, ou None se erro.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Tentar buscar existente
            cursor.execute("""
                SELECT id, user_id, tokens_usados, limite_tokens, janela_inicio, plano, atualizado_em
                FROM tokens_usuarios
                WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            
            # Criar novo registro se não existir
            tokens_id = gerar_id()
            timestamp = agora()
            
            cursor.execute("""
                INSERT INTO tokens_usuarios (id, user_id, tokens_usados, limite_tokens, janela_inicio, plano, atualizado_em)
                VALUES (?, ?, 0, 50000, ?, 'free', ?)
            """, (tokens_id, user_id, timestamp, timestamp))
            
            conn.commit()
            
            return {
                "id": tokens_id,
                "user_id": user_id,
                "tokens_usados": 0,
                "limite_tokens": 50000,
                "janela_inicio": timestamp,
                "plano": "free",
                "atualizado_em": timestamp
            }
            
    except Exception as e:
        print(f"[ERRO] Erro ao obter/criar tokens: {e}")
        return None


def get_saldo(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtém saldo atual de tokens do usuário.
    
    Args:
        user_id (str): ID do usuário.
        
    Returns:
        dict: Saldo com tokens_usados, limite, restantes, etc.
    """
    tokens = get_or_create_tokens(user_id)
    if not tokens:
        return None
    
    tokens_restantes = tokens["limite_tokens"] - tokens["tokens_usados"]
    
    return {
        "tokens_usados": tokens["tokens_usados"],
        "limite_tokens": tokens["limite_tokens"],
        "tokens_restantes": tokens_restantes,
        "janela_inicio": tokens["janela_inicio"],
        "plano": tokens["plano"]
    }


def consumir_tokens(user_id: str, amount: int, descricao: str = "Uso de tokens") -> Dict[str, Any]:
    """
    Consome tokens de forma atômica e segura.
    Usa BEGIN IMMEDIATE para evitar race conditions.
    
    Args:
        user_id (str): ID do usuário.
        amount (int): Quantidade de tokens a consumir.
        descricao (str): Descrição do uso.
        
    Returns:
        dict: Resultado com allowed (bool), tokens_restantes, reset_in_ms se aplicável.
    """
    if amount <= 0:
        return {"allowed": False, "tokens_restantes": 0, "mensagem": "Quantidade inválida"}
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # BEGIN IMMEDIATE para lock exclusivo
            cursor.execute("BEGIN IMMEDIATE")
            
            try:
                # Buscar tokens do usuário
                cursor.execute("""
                    SELECT id, tokens_usados, limite_tokens, janela_inicio, plano
                    FROM tokens_usuarios
                    WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if not row:
                    conn.rollback()
                    return {"allowed": False, "tokens_restantes": 0, "mensagem": "Usuário não encontrado"}
                
                tokens_data = dict(row)
                tokens_usados = tokens_data["tokens_usados"]
                limite_tokens = tokens_data["limite_tokens"]
                janela_inicio_str = tokens_data["janela_inicio"]
                plano = tokens_data["plano"]
                
                # Verificar se janela de 8 horas já passou
                janela_inicio = datetime.fromisoformat(janela_inicio_str)
                agora_dt = datetime.now()
                horas_decorridas = (agora_dt - janela_inicio).total_seconds() / 3600
                
                # Se passaram mais de 8 horas, resetar contagem
                if horas_decorridas >= 8:
                    tokens_usados = 0
                    janela_inicio = agora_dt
                    cursor.execute("""
                        UPDATE tokens_usuarios
                        SET tokens_usados = 0, janela_inicio = ?, atualizado_em = ?
                        WHERE user_id = ?
                    """, (janela_inicio.strftime("%Y-%m-%dT%H:%M:%S"), agora(), user_id))
                
                tokens_restantes = limite_tokens - tokens_usados
                
                # Verificar se tem saldo suficiente
                if tokens_restantes < amount:
                    conn.rollback()
                    
                    # Calcular tempo até reset em milissegundos
                    tempo_ate_reset = timedelta(hours=8) - (agora_dt - janela_inicio)
                    reset_in_ms = int(tempo_ate_reset.total_seconds() * 1000)
                    if reset_in_ms < 0:
                        reset_in_ms = 0
                    
                    return {
                        "allowed": False,
                        "tokens_restantes": tokens_restantes,
                        "reset_in_ms": reset_in_ms,
                        "mensagem": f"Saldo insuficiente. Reset em {reset_in_ms}ms"
                    }
                
                # Consumir tokens
                novos_tokens_usados = tokens_usados + amount
                cursor.execute("""
                    UPDATE tokens_usuarios
                    SET tokens_usados = ?, atualizado_em = ?
                    WHERE user_id = ?
                """, (novos_tokens_usados, agora(), user_id))
                
                conn.commit()
                
                return {
                    "allowed": True,
                    "tokens_restantes": limite_tokens - novos_tokens_usados,
                    "mensagem": "Tokens consumidos com sucesso"
                }
                
            except Exception as e:
                conn.rollback()
                print(f"[ERRO] Erro ao consumir tokens: {e}")
                return {"allowed": False, "tokens_restantes": 0, "mensagem": f"Erro interno: {str(e)}"}
                
    except Exception as e:
        print(f"[ERRO] Erro de conexão ao consumir tokens: {e}")
        return {"allowed": False, "tokens_restantes": 0, "mensagem": f"Erro crítico: {str(e)}"}


def upgrade_plano(user_id: str, novo_plano: str) -> bool:
    """
    Faz upgrade ou downgrade do plano do usuário.
    
    Args:
        user_id (str): ID do usuário.
        novo_plano (str): Novo plano ('free' ou 'pro').
        
    Returns:
        bool: True se sucesso, False se erro.
    """
    limites = {
        "free": 50000,
        "pro": 500000
    }
    
    if novo_plano not in limites:
        return False
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE tokens_usuarios
                SET plano = ?, limite_tokens = ?, atualizado_em = ?
                WHERE user_id = ?
            """, (novo_plano, limites[novo_plano], agora(), user_id))
            
            conn.commit()
            return cursor.rowcount > 0
            
    except Exception as e:
        print(f"[ERRO] Erro ao fazer upgrade de plano: {e}")
        return False
