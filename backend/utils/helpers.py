"""
Utilitários auxiliares para o backend CxIA.

Funções para geração de UUID, datetime, hash de senha e verificação.
"""

import uuid
import hashlib
import hmac
from datetime import datetime


def gerar_id() -> str:
    """
    Gera um UUID4 único como string.
    
    Returns:
        str: UUID no formato padrão (ex: '550e8400-e29b-41d4-a716-446655440000')
    """
    return str(uuid.uuid4())


def agora() -> str:
    """
    Retorna a data/hora atual no formato ISO 8601.
    
    Returns:
        str: Datetime no formato 'YYYY-MM-DDTHH:MM:SS'
    """
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def hash_senha(senha: str) -> str:
    """
    Gera hash SHA-256 da senha.
    
    Args:
        senha (str): Senha em texto puro.
        
    Returns:
        str: Hash da senha em hexadecimal.
    """
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()


def verificar_senha(senha: str, hash_salvo: str) -> bool:
    """
    Verifica se a senha fornecida corresponde ao hash salvo.
    Usa comparação segura contra timing attacks.
    
    Args:
        senha (str): Senha em texto puro para verificar.
        hash_salvo (str): Hash armazenado no banco de dados.
        
    Returns:
        bool: True se a senha corresponder, False caso contrário.
    """
    hash_gerado = hash_senha(senha)
    return hmac.compare_digest(hash_gerado, hash_salvo)
