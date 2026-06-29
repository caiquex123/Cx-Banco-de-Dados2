"""
Módulo __init__ para o pacote models do CX SaaS.

Exporta todas as funções dos modelos para facilitar a importação.
"""

from cx_database.models.planos import (
    criar_plano,
    buscar_plano_por_id,
    buscar_plano_por_nome,
    listar_planos,
    atualizar_plano,
    deletar_plano
)

from cx_database.models.usuarios import (
    criar_usuario,
    buscar_usuario_por_id,
    buscar_usuario_por_email,
    listar_usuarios,
    atualizar_usuario,
    deletar_usuario,
    autenticar_usuario
)

from cx_database.models.projetos import (
    criar_projeto,
    buscar_projeto_por_id,
    listar_projetos_por_usuario,
    listar_todos_projetos,
    atualizar_projeto,
    deletar_projeto
)

from cx_database.models.conversas import (
    criar_conversa,
    buscar_conversa_por_id,
    listar_conversas_por_usuario,
    listar_conversas_por_projeto,
    atualizar_conversa,
    deletar_conversa
)

from cx_database.models.mensagens import (
    criar_mensagem,
    buscar_mensagem_por_id,
    listar_mensagens_por_conversa,
    listar_mensagens_paginadas,
    atualizar_mensagem,
    deletar_mensagem,
    contar_mensagens_por_usuario,
    contar_mensagens_por_papel
)

__all__ = [
    # planos.py
    "criar_plano",
    "buscar_plano_por_id",
    "buscar_plano_por_nome",
    "listar_planos",
    "atualizar_plano",
    "deletar_plano",
    # usuarios.py
    "criar_usuario",
    "buscar_usuario_por_id",
    "buscar_usuario_por_email",
    "listar_usuarios",
    "atualizar_usuario",
    "deletar_usuario",
    "autenticar_usuario",
    # projetos.py
    "criar_projeto",
    "buscar_projeto_por_id",
    "listar_projetos_por_usuario",
    "listar_todos_projetos",
    "atualizar_projeto",
    "deletar_projeto",
    # conversas.py
    "criar_conversa",
    "buscar_conversa_por_id",
    "listar_conversas_por_usuario",
    "listar_conversas_por_projeto",
    "atualizar_conversa",
    "deletar_conversa",
    # mensagens.py
    "criar_mensagem",
    "buscar_mensagem_por_id",
    "listar_mensagens_por_conversa",
    "listar_mensagens_paginadas",
    "atualizar_mensagem",
    "deletar_mensagem",
    "contar_mensagens_por_usuario",
    "contar_mensagens_por_papel"
]
