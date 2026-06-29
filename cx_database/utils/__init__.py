"""
Módulo __init__ para o pacote utils do CX SaaS.

Exporta todas as funções utilitárias para facilitar a importação.
"""

from cx_database.utils.helpers import (
    gerar_id,
    agora,
    hash_senha,
    verificar_senha
)

from cx_database.utils.validators import (
    validar_email,
    validar_senha_forca,
    validar_campos_obrigatorios
)

from cx_database.utils.json_field import (
    to_json,
    from_json
)

from cx_database.utils.codec import (
    decode_activation_code,
    generate_activation_code
)

__all__ = [
    # helpers.py
    "gerar_id",
    "agora",
    "hash_senha",
    "verificar_senha",
    # validators.py
    "validar_email",
    "validar_senha_forca",
    "validar_campos_obrigatorios",
    # json_field.py
    "to_json",
    "from_json",
    # codec.py
    "decode_activation_code",
    "generate_activation_code"
]
