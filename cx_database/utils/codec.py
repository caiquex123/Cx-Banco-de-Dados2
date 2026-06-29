"""
Módulo de codificação/decodificação para o banco de dados CX SAAS.

Este módulo replica a função decodeActivationCode do frontend TypeScript,
usada para validar códigos de ativação de plano premium.

Funções disponíveis:
    - decode_activation_code(): Decodifica e valida códigos de ativação
    - generate_activation_code(): Gera códigos de ativação válidos
"""

import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Chave secreta para assinatura dos códigos de ativação
# Em produção, isso deveria vir de variável de ambiente
SECRET_KEY = "cx_saas_secret_activation_key_2025"


def generate_activation_code(plano: str = "premium", horas_validade: int = 168) -> str:
    """
    Gera um código de ativação válido para upgrade de plano.

    O código contém informações codificadas sobre o plano e data de expiração,
    além de uma assinatura HMAC para validação de integridade.

    Args:
        plano (str): Tipo de plano a ser ativado ('premium' ou 'premium_max').
            Default: 'premium'.
        horas_validade (int): Quantidade de horas que o código será válido.
            Default: 168 (7 dias).

    Returns:
        str: Código de ativação no formato 'CX-{payload}-{signature}'.

    Example:
        >>> code = generate_activation_code("premium", 24)
        >>> code.startswith("CX-")
        True
    """
    # Dados do payload
    expires_at = datetime.now() + timedelta(hours=horas_validade)
    payload_data = {
        "plano": plano,
        "expires": expires_at.strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    # Codificar payload em base64 URL-safe (usando hex para simplicidade)
    import base64
    payload_json = f"{payload_data['plano']}|{payload_data['expires']}"
    payload_encoded = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip('=')
    
    # Criar assinatura HMAC
    signature = hmac.new(
        SECRET_KEY.encode(),
        payload_encoded.encode(),
        hashlib.sha256
    ).hexdigest()[:16]
    
    return f"CX-{payload_encoded}-{signature}"


def decode_activation_code(codigo: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica e valida um código de ativação de plano premium.

    Esta função replica o comportamento da função decodeActivationCode
    do frontend TypeScript (utils/codec.ts).

    O código deve estar no formato: CX-{payload}-{signature}
    
    A função verifica:
    1. Formato válido do código
    2. Assinatura HMAC correta
    3. Código não expirado

    Args:
        codigo (str): Código de ativação fornecido pelo usuário.

    Returns:
        dict | None: Dicionário com informações do código se válido:
            - plano (str): Tipo de plano ('premium' ou 'premium_max')
            - expires (str): Data de expiração do código
            - valido (bool): Sempre True se retornou dict
            Retorna None se o código for inválido ou expirado.

    Example:
        >>> code = generate_activation_code("premium", 24)
        >>> result = decode_activation_code(code)
        >>> result is not None and result['plano'] == 'premium'
        True
        >>> decode_activation_code("CODIGO_INVALIDO")
        None
    """
    if not codigo or not isinstance(codigo, str):
        return None
    
    # Verificar formato básico
    if not codigo.startswith("CX-"):
        return None
    
    partes = codigo.split("-")
    if len(partes) != 3:
        return None
    
    _, payload_encoded, signature_provided = partes
    
    # Validar assinatura HMAC
    # Recriar a assinatura esperada
    signature_expected = hmac.new(
        SECRET_KEY.encode(),
        payload_encoded.encode(),
        hashlib.sha256
    ).hexdigest()[:16]
    
    # Comparar assinaturas de forma segura
    if not hmac.compare_digest(signature_provided, signature_expected):
        return None
    
    # Decodificar payload
    try:
        import base64
        # Adicionar padding se necessário
        padding = 4 - (len(payload_encoded) % 4)
        if padding != 4:
            payload_encoded += '=' * padding
        
        payload_decoded = base64.urlsafe_b64decode(payload_encoded).decode()
        partes_payload = payload_decoded.split("|")
        
        if len(partes_payload) != 2:
            return None
        
        plano, expires_str = partes_payload
        
        # Validar plano
        if plano not in ["premium", "premium_max"]:
            return None
        
        # Verificar se não expirou
        expires_at = datetime.strptime(expires_str, "%Y-%m-%dT%H:%M:%S")
        if datetime.now() > expires_at:
            return None
        
        return {
            "plano": plano,
            "expires": expires_str,
            "valido": True
        }
    
    except (ValueError, UnicodeDecodeError, Exception) as e:
        print(f"Erro ao decodificar código: {e}")
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("=== TESTES DO MÓDULO codec.py ===")
    print("=" * 50)

    print("\n[TESTE 1] Gerar código premium (24 horas):")
    code_premium = generate_activation_code("premium", 24)
    print(f"  Código gerado: {code_premium}")
    print(f"  Começa com 'CX-': {code_premium.startswith('CX-')}")

    print("\n[TESTE 2] Gerar código premium_max (7 dias):")
    code_premium_max = generate_activation_code("premium_max", 168)
    print(f"  Código gerado: {code_premium_max}")

    print("\n[TESTE 3] Decodificar código válido:")
    resultado = decode_activation_code(code_premium)
    print(f"  Resultado: {resultado}")
    if resultado:
        print(f"  Plano: {resultado['plano']}")
        print(f"  Válido: {resultado.get('valido', False)}")

    print("\n[TESTE 4] Decodificar código inválido:")
    invalido = decode_activation_code("CX-invalido-test")
    print(f"  Resultado: {invalido}")

    print("\n[TESTE 5] Decodigar código mal formatado:")
    mal_formatado = decode_activation_code("CODIGO_ERRADO")
    print(f"  Resultado: {mal_formatado}")

    print("\n[TESTE 6] Decodificar None:")
    none_result = decode_activation_code(None)
    print(f"  Resultado: {none_result}")

    print("\n[TESTE 7] Round-trip (gerar e decodificar):")
    code_test = generate_activation_code("premium_max", 48)
    decoded = decode_activation_code(code_test)
    print(f"  Código original: {code_test}")
    print(f"  Decodificado: {decoded}")
    if decoded:
        print(f"  Plano confere: {decoded['plano'] == 'premium_max'}")

    print("\n" + "=" * 50)
    print("Todos os testes do codec.py foram executados!")
    print("=" * 50)
