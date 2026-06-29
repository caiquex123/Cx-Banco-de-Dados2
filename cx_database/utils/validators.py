"""
Módulo de validação de dados para o banco de dados CX SaaS.

Este módulo contém funções para validar dados antes de serem inseridos
no banco de dados, garantindo integridade e segurança das informações.

Funções disponíveis:
    - validar_email(): Valida formato de email com regex
    - validar_senha_forca(): Verifica se senha atende requisitos mínimos
    - validar_campos_obrigatorios(): Checa presença de campos necessários
"""

import re


def validar_email(email: str) -> bool:
    """
    Valida o formato de um endereço de email usando expressão regular.

    A validação verifica:
    - Presença de caractere @ separando local e domínio
    - Domínio com pelo menos um ponto
    - Caracteres válidos em cada parte
    - TLD (top-level domain) com 2-6 caracteres

    Args:
        email (str): Endereço de email a ser validado.

    Returns:
        bool: True se o email tiver formato válido, False caso contrário.

    Example:
        >>> validar_email("usuario@exemplo.com")
        True
        >>> validar_email("email-invalido")
        False
        >>> validar_email("@exemplo.com")
        False
    """
    if not email or not isinstance(email, str):
        return False

    # Regex padrão para validação de email
    padrao_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao_email, email) is not None


def validar_senha_forca(senha: str) -> bool:
    """
    Verifica se uma senha atende aos requisitos mínimos de segurança.

    Requisitos obrigatórios:
    - Mínimo de 8 caracteres
    - Pelo menos 1 número (0-9)
    - Pelo menos 1 letra maiúscula (A-Z)
    - Pelo menos 1 letra minúscula (a-z)

    Args:
        senha (str): Senha em texto puro a ser validada.

    Returns:
        bool: True se a senha atender todos os requisitos, False caso contrário.

    Example:
        >>> validar_senha_forca("Senha123")
        True
        >>> validar_senha_forca("senha")
        False  # Sem maiúscula e sem número
        >>> validar_senha_forca("SENHA123")
        False  # Sem minúscula
    """
    if not senha or not isinstance(senha, str):
        return False

    # Verificar tamanho mínimo
    if len(senha) < 8:
        return False

    # Verificar presença de pelo menos 1 número
    if not re.search(r'[0-9]', senha):
        return False

    # Verificar presença de pelo menos 1 letra maiúscula
    if not re.search(r'[A-Z]', senha):
        return False

    # Verificar presença de pelo menos 1 letra minúscula
    if not re.search(r'[a-z]', senha):
        return False

    return True


def validar_campos_obrigatorios(dados: dict, campos: list) -> bool:
    """
    Verifica se todos os campos obrigatórios estão presentes e não vazios.

    Esta função valida um dicionário de dados contra uma lista de campos
    obrigatórios, garantindo que cada campo exista e tenha um valor válido
    (não None, não string vazia, não lista vazia).

    Args:
        dados (dict): Dicionário contendo os dados a serem validados.
        campos (list): Lista de strings com nomes dos campos obrigatórios.

    Returns:
        bool: True se todos os campos obrigatórios estiverem presentes e válidos,
              False caso contrário.

    Example:
        >>> dados = {"nome": "João", "email": "joao@email.com"}
        >>> validar_campos_obrigatorios(dados, ["nome", "email"])
        True
        >>> validar_campos_obrigatorios(dados, ["nome", "telefone"])
        False  # telefone não está presente
    """
    if not isinstance(dados, dict) or not isinstance(campos, list):
        return False

    for campo in campos:
        # Verificar se o campo existe no dicionário
        if campo not in dados:
            return False

        valor = dados[campo]

        # Verificar se o valor é None
        if valor is None:
            return False

        # Verificar se é string vazia
        if isinstance(valor, str) and valor.strip() == "":
            return False

        # Verificar se é lista vazia
        if isinstance(valor, list) and len(valor) == 0:
            return False

        # Verificar se é dict vazio
        if isinstance(valor, dict) and len(valor) == 0:
            return False

    return True


if __name__ == "__main__":
    print("=" * 50)
    print("=== TESTES DO MÓDULO validators.py ===")
    print("=" * 50)

    print("\n[TESTE 1] Validar emails válidos:")
    emails_validos = [
        "usuario@exemplo.com",
        "joao.silva@empresa.com.br",
        "teste+tag@mail.org",
        "user123@domain.co"
    ]
    for email in emails_validos:
        resultado = validar_email(email)
        print(f"  '{email}' → {resultado}")

    print("\n[TESTE 2] Validar emails inválidos:")
    emails_invalidos = [
        "email-sem-arroba",
        "@exemplo.com",
        "usuario@",
        "usuario@dominio",
        "",
        None
    ]
    for email in emails_invalidos:
        resultado = validar_email(email) if email is not None else validar_email(email)
        print(f"  '{email}' → {resultado}")

    print("\n[TESTE 3] Validar senhas fortes:")
    senhas_fortes = [
        "Senha123",
        "MinhaSenha456",
        "Abcdefg1",
        "Teste@2024"
    ]
    for senha in senhas_fortes:
        resultado = validar_senha_forca(senha)
        print(f"  '{senha}' → {resultado}")

    print("\n[TESTE 4] Validar senhas fracas:")
    senhas_fracas = [
        "senha",      # Sem maiúscula e número
        "SENHA123",   # Sem minúscula
        "Senha",      # Sem número
        "12345678",   # Sem letras
        "abc",        # Muito curta
        "",           # Vazia
        None          # None
    ]
    for senha in senhas_fracas:
        resultado = validar_senha_forca(senha) if senha is not None else validar_senha_forca(senha)
        print(f"  '{senha}' → {resultado}")

    print("\n[TESTE 5] Validar campos obrigatórios:")
    dados_completos = {
        "nome": "João Silva",
        "email": "joao@email.com",
        "idade": 25
    }
    dados_incompletos = {
        "nome": "João Silva",
        "email": ""
    }

    print(f"  Dados completos com ['nome', 'email']: {validar_campos_obrigatorios(dados_completos, ['nome', 'email'])}")
    print(f"  Dados completos com ['nome', 'email', 'idade']: {validar_campos_obrigatorios(dados_completos, ['nome', 'email', 'idade'])}")
    print(f"  Dados incompletos com ['nome', 'email']: {validar_campos_obrigatorios(dados_incompletos, ['nome', 'email'])}")
    print(f"  Dados completos com campo inexistente: {validar_campos_obrigatorios(dados_completos, ['nome', 'telefone'])}")

    print("\n" + "=" * 50)
    print("Todos os testes do validators.py foram executados!")
    print("=" * 50)
