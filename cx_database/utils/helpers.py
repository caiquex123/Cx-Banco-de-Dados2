"""
Módulo de funções auxiliares para o banco de dados CX SaaS.

Este módulo contém utilitários para geração de IDs, formatação de datas,
e manipulação segura de senhas usando hash SHA-256.

Funções disponíveis:
    - gerar_id(): Gera um UUID4 único
    - agora(): Retorna data/hora atual em formato ISO 8601
    - hash_senha(): Cria hash SHA-256 de uma senha
    - verificar_senha(): Compara senha com hash armazenado
"""

import uuid
import hashlib
import hmac
from datetime import datetime


def gerar_id() -> str:
    """
    Gera um identificador único universal (UUID) versão 4.

    Returns:
        str: String representando um UUID4 (ex: 'f47ac10b-58cc-4372-a567-0e02b2c3d479')

    Example:
        >>> id_gerado = gerar_id()
        >>> len(id_gerado) == 36  # UUID tem 36 caracteres incluindo hífens
        True
    """
    return str(uuid.uuid4())


def agora() -> str:
    """
    Retorna a data e hora atuais no formato ISO 8601.

    O formato retornado é compatível com ordenação cronológica em strings
    e pode ser usado diretamente em bancos de dados SQLite.

    Returns:
        str: Data/hora no formato 'YYYY-MM-DDTHH:MM:SS' (ex: '2025-01-20T14:30:00')

    Example:
        >>> timestamp = agora()
        >>> len(timestamp) == 19  # Formato fixo
        True
    """
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def hash_senha(senha: str) -> str:
    """
    Cria um hash SHA-256 seguro para uma senha fornecida.

    A senha é codificada em UTF-8 antes de aplicar o algoritmo de hash.
    Este método é determinístico: mesma senha sempre produz mesmo hash.

    Args:
        senha (str): Senha em texto puro a ser convertida para hash.

    Returns:
        str: Hash hexadecimal da senha (64 caracteres hexadecimais).

    Security Note:
        Para produção com requisitos de segurança elevados, considere usar
        bcrypt ou argon2. Esta implementação usa SHA-256 por ser nativa do Python.

    Example:
        >>> hash_senha("minhaSenha123")
        'a1b2c3...'  # 64 caracteres hexadecimais
    """
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()


def verificar_senha(senha: str, hash_salvo: str) -> bool:
    """
    Verifica se uma senha corresponde ao hash armazenado.

    Compara o hash da senha fornecida com o hash previamente armazenado
    no banco de dados. Usa comparação de tempo constante para evitar
    ataques de timing.

    Args:
        senha (str): Senha em texto puro fornecida pelo usuário.
        hash_salvo (str): Hash SHA-256 armazenado no banco de dados.

    Returns:
        bool: True se a senha corresponder ao hash, False caso contrário.

    Security Note:
        A comparação usa hmac.compare_digest para prevenir ataques de timing.

    Example:
        >>> senha_hash = hash_senha("minhaSenha123")
        >>> verificar_senha("minhaSenha123", senha_hash)
        True
        >>> verificar_senha("senhaErrada", senha_hash)
        False
    """
    senha_hash = hash_senha(senha)
    return hmac.compare_digest(senha_hash, hash_salvo)


if __name__ == "__main__":
    print("=" * 50)
    print("=== TESTES DO MÓDULO helpers.py ===")
    print("=" * 50)

    print("\n[TESTE 1] Gerar ID único:")
    id1 = gerar_id()
    id2 = gerar_id()
    print(f"  ID 1: {id1}")
    print(f"  ID 2: {id2}")
    print(f"  IDs são diferentes: {id1 != id2}")
    print(f"  Formato válido (36 chars): {len(id1) == 36}")

    print("\n[TESTE 2] Obter timestamp atual:")
    ts = agora()
    print(f"  Timestamp: {ts}")
    print(f"  Formato ISO 8601 válido: {'T' in ts and len(ts) == 19}")

    print("\n[TESTE 3] Hash de senha:")
    senha_teste = "MinhaSenhaSecreta123"
    hash_result = hash_senha(senha_teste)
    print(f"  Senha original: {senha_teste}")
    print(f"  Hash gerado: {hash_result}")
    print(f"  Tamanho do hash (64 hex chars): {len(hash_result) == 64}")

    print("\n[TESTE 4] Verificar senha correta:")
    resultado_correto = verificar_senha(senha_teste, hash_result)
    print(f"  Senha '{senha_teste}' confere com hash? {resultado_correto}")

    print("\n[TESTE 5] Verificar senha incorreta:")
    resultado_incorreto = verificar_senha("SenhaErrada", hash_result)
    print(f"  Senha 'SenhaErrada' confere com hash? {resultado_incorreto}")

    print("\n" + "=" * 50)
    print("Todos os testes do helpers.py foram executados!")
    print("=" * 50)
