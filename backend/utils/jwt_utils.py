"""
Utilitários para manipulação de tokens JWT.

Criação e verificação de tokens JWT para autenticação de usuários.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "sua_chave_secreta_padrao_troque_isso_em_producao")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 30


def criar_token(user_id: str, email: str) -> str:
    """
    Cria um token JWT para o usuário.
    
    Args:
        user_id (str): ID único do usuário.
        email (str): Email do usuário (incluído no payload).
        
    Returns:
        str: Token JWT codificado.
    """
    expiration = datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verificar_token(token: str) -> Optional[Dict]:
    """
    Verifica e decodifica um token JWT.
    
    Args:
        token (str): Token JWT a ser verificado.
        
    Returns:
        dict: Payload do token se válido, None se inválido ou expirado.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token expirado
        return None
    except jwt.InvalidTokenError:
        # Token inválido
        return None


def obter_expires_at(token: str) -> Optional[str]:
    """
    Obtém a data de expiração do token em formato ISO 8601.
    
    Args:
        token (str): Token JWT.
        
    Returns:
        str: Data de expiração no formato ISO 8601, ou None se inválido.
    """
    payload = verificar_token(token)
    if payload and "exp" in payload:
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
        return exp_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    return None
