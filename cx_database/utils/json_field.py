"""
Módulo de serialização/deserialização de campos JSON para o banco de dados CX SAAS.

Este módulo fornece funções para converter entre objetos Python (dict, list)
e strings JSON, simulando o comportamento do tipo JSONB do PostgreSQL no SQLite.

Funções disponíveis:
    - to_json(): Converte dict/list para string JSON
    - from_json(): Converte string JSON de volta para dict/list
"""

import json
from typing import Any, Optional, Union


def to_json(value: Optional[Union[dict, list]]) -> Optional[str]:
    """
    Serializa um objeto Python (dict ou list) para uma string JSON.

    Esta função é usada para armazenar dados estruturados em colunas TEXT
    do SQLite, simulando o comportamento do tipo JSONB do PostgreSQL.

    Args:
        value (dict | list | None): Objeto Python a ser serializado.
            Pode ser um dicionário, lista ou None.

    Returns:
        str | None: String JSON representando o objeto, ou None se value for None.

    Example:
        >>> to_json({"chave": "valor"})
        '{"chave": "valor"}'
        >>> to_json([1, 2, 3])
        '[1, 2, 3]'
        >>> to_json(None)
        None
    """
    if value is None:
        return None
    
    try:
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    except (TypeError, ValueError) as e:
        # Em caso de erro, retorna None e loga o erro
        print(f"Erro ao serializar JSON: {e}")
        return None


def from_json(value: Optional[str], default: Any = None) -> Any:
    """
    Deserializa uma string JSON para um objeto Python (dict ou list).

    Esta função é usada para recuperar dados estruturados armazenados em
    colunas TEXT do SQLite, convertendo-os de volta para objetos Python.

    Args:
        value (str | None): String JSON a ser deserializada.
        default (Any, optional): Valor padrão a ser retornado em caso de erro
            ou se value for None. Default: None.

    Returns:
        dict | list | Any: Objeto Python resultante da deserialização,
            ou o valor default em caso de erro.

    Example:
        >>> from_json('{"chave": "valor"}')
        {'chave': 'valor'}
        >>> from_json('[1, 2, 3]')
        [1, 2, 3]
        >>> from_json(None, default={})
        {}
        >>> from_json('invalido', default=[])
        []
    """
    if value is None:
        return default
    
    if not isinstance(value, str):
        return default
    
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError) as e:
        # Em caso de erro, retorna o valor default
        print(f"Erro ao deserializar JSON: {e}")
        return default


if __name__ == "__main__":
    print("=" * 50)
    print("=== TESTES DO MÓDULO json_field.py ===")
    print("=" * 50)

    print("\n[TESTE 1] Serializar dict para JSON:")
    dados_dict = {"nome": "João", "idade": 30, "ativo": True}
    json_str = to_json(dados_dict)
    print(f"  Original: {dados_dict}")
    print(f"  JSON: {json_str}")
    print(f"  Tipo: {type(json_str)}")

    print("\n[TESTE 2] Serializar list para JSON:")
    dados_list = [1, 2, 3, "texto", {"chave": "valor"}]
    json_str_list = to_json(dados_list)
    print(f"  Original: {dados_list}")
    print(f"  JSON: {json_str_list}")

    print("\n[TESTE 3] Serializar None:")
    none_result = to_json(None)
    print(f"  to_json(None) = {none_result}")

    print("\n[TESTE 4] Deserializar JSON para dict:")
    json_dict = '{"nome":"Maria","idade":25}'
    dict_result = from_json(json_dict)
    print(f"  JSON: {json_dict}")
    print(f"  Resultado: {dict_result}")
    print(f"  Tipo: {type(dict_result)}")

    print("\n[TESTE 5] Deserializar JSON para list:")
    json_list = '[1,2,3,"texto"]'
    list_result = from_json(json_list)
    print(f"  JSON: {json_list}")
    print(f"  Resultado: {list_result}")

    print("\n[TESTE 6] Deserializar None com default:")
    none_default = from_json(None, default={})
    print(f"  from_json(None, default={{}}) = {none_default}")

    print("\n[TESTE 7] Deserializar JSON inválido com default:")
    invalido = from_json('json-invalido', default=[])
    print(f"  from_json('json-invalido', default=[]) = {invalido}")

    print("\n[TESTE 8] Round-trip (serializar e deserializar):")
    original = {
        "interesses": ["tecnologia", "ciência"],
        "config": {"tema": "dark", "idioma": "pt-BR"},
        "numeros": [1, 2, 3]
    }
    serializado = to_json(original)
    deserializado = from_json(serializado)
    print(f"  Original: {original}")
    print(f"  Serializado: {serializado}")
    print(f"  Deserializado: {deserializado}")
    print(f"  São iguais: {original == deserializado}")

    print("\n" + "=" * 50)
    print("Todos os testes do json_field.py foram executados!")
    print("=" * 50)
