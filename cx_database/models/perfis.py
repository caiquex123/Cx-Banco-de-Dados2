"""
Módulo de modelos para perfis de usuário no banco de dados CX SAAS.

Este módulo gerencia a tabela 'perfis' que armazena informações detalhadas
dos usuários como nome, idade, interesses, avatar, bio e configurações de resposta.

Funções disponíveis:
    - criar_perfil(): Cria um novo perfil
    - buscar_perfil_por_user_id(): Busca perfil pelo ID do usuário
    - atualizar_perfil(): Atualiza dados do perfil
    - deletar_perfil(): Remove um perfil
"""

import sqlite3
from typing import Optional, Dict, Any, List
from cx_database.connection import get_connection
from cx_database.utils.helpers import gerar_id, agora
from cx_database.utils.json_field import to_json, from_json


def criar_perfil(
    user_id: str,
    email: str,
    username: str = None,
    display_name: str = None,
    nome: str = None,
    idade: int = None,
    interesses: List[str] = None,
    profile_picture_url: str = None,
    avatar_url: str = None,
    bio: str = None,
    response_style: str = "amigável"
) -> Optional[Dict[str, Any]]:
    """
    Cria um novo perfil de usuário no banco de dados.

    Args:
        user_id (str): ID do usuário (deve existir na tabela usuarios).
        email (str): Email do usuário.
        username (str, optional): Nome de usuário único. Default: None.
        display_name (str, optional): Nome de exibição. Default: None.
        nome (str, optional): Nome completo. Default: None.
        idade (int, optional): Idade do usuário. Default: None.
        interesses (list, optional): Lista de interesses. Default: None.
        profile_picture_url (str, optional): URL da foto de perfil. Default: None.
        avatar_url (str, optional): URL do avatar. Default: None.
        bio (str, optional): Biografia/resumo. Default: None.
        response_style (str, optional): Estilo de resposta da IA. Default: "amigável".

    Returns:
        dict: Dicionário com os dados do perfil criado, ou None em caso de erro.
    """
    if not user_id or not email:
        print("[ERRO] user_id e email são obrigatórios para criar perfil.")
        return None
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            perfil_id = gerar_id()
            timestamp = agora()
            
            # Converter interesses para JSON
            interesses_json = to_json(interesses if interesses else [])
            
            cursor.execute("""
                INSERT INTO perfis (
                    id, user_id, email, username, display_name, nome, idade,
                    interesses, profile_picture_url, avatar_url, bio,
                    response_style, temporal_memory, criado_em, atualizado_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                perfil_id,
                user_id,
                email,
                username,
                display_name,
                nome,
                idade,
                interesses_json,
                profile_picture_url,
                avatar_url,
                bio,
                response_style,
                to_json({"keyEvents": []}),
                timestamp,
                timestamp
            ))
            
            conn.commit()
            
            # Retornar perfil criado
            return buscar_perfil_por_user_id(user_id)
            
    except sqlite3.IntegrityError as e:
        print(f"[ERRO] Integridade violada ao criar perfil: {e}")
        return None
    except sqlite3.OperationalError as e:
        print(f"[ERRO] Erro operacional ao criar perfil: {e}")
        return None
    except Exception as e:
        print(f"[ERRO] Erro inesperado ao criar perfil: {e}")
        return None


def buscar_perfil_por_user_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca um perfil pelo ID do usuário.

    Args:
        user_id (str): ID do usuário.

    Returns:
        dict: Dicionário com os dados do perfil, ou None se não encontrado.
    """
    if not user_id:
        return None
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM perfis WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            # Converter para dict e desserializar campos JSON
            perfil = dict(row)
            perfil["interesses"] = from_json(perfil.get("interesses"), default=[])
            perfil["temporal_memory"] = from_json(perfil.get("temporal_memory"), default={"keyEvents": []})
            
            return perfil
            
    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao buscar perfil: {e}")
        return None


def atualizar_perfil(
    user_id: str,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Atualiza campos específicos de um perfil existente.

    Args:
        user_id (str): ID do usuário cujo perfil será atualizado.
        **kwargs: Campos a serem atualizados (username, display_name, nome,
                  idade, interesses, profile_picture_url, avatar_url, bio, response_style).

    Returns:
        dict: Dicionário com os dados atualizados do perfil, ou None em caso de erro.
    """
    if not user_id:
        return None
    
    # Mapeamento de campos válidos
    campos_validos = [
        "username", "display_name", "nome", "idade", "interesses",
        "profile_picture_url", "avatar_url", "bio", "response_style"
    ]
    
    # Filtrar apenas campos válidos
    atualizacoes = {k: v for k, v in kwargs.items() if k in campos_validos}
    
    if not atualizacoes:
        print("[AVISO] Nenhum campo válido para atualizar.")
        return buscar_perfil_por_user_id(user_id)
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Construir query dinâmica
            campos_set = []
            valores = []
            
            for campo, valor in atualizacoes.items():
                campos_set.append(f"{campo} = ?")
                # Converter campos JSON
                if campo == "interesses":
                    valor = to_json(valor)
                valores.append(valor)
            
            # Adicionar updated_at e WHERE
            valores.append(agora())
            valores.append(user_id)
            
            query = f"""
                UPDATE perfis 
                SET {', '.join(campos_set)}, atualizado_em = ?
                WHERE user_id = ?
            """
            
            cursor.execute(query, valores)
            conn.commit()
            
            if cursor.rowcount == 0:
                print(f"[AVISO] Nenhum perfil encontrado para user_id={user_id}")
                return None
            
            return buscar_perfil_por_user_id(user_id)
            
    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao atualizar perfil: {e}")
        return None


def deletar_perfil(user_id: str) -> bool:
    """
    Remove um perfil do banco de dados.

    Args:
        user_id (str): ID do usuário cujo perfil será removido.

    Returns:
        bool: True se removido com sucesso, False caso contrário.
    """
    if not user_id:
        return False
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM perfis WHERE user_id = ?", (user_id,))
            conn.commit()
            
            return cursor.rowcount > 0
            
    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao deletar perfil: {e}")
        return False


if __name__ == "__main__":
    from cx_database.setup import setup_completo
    setup_completo()
    
    print("=" * 50)
    print("=== TESTES DO MÓDULO perfis.py ===")
    print("=" * 50)
    
    # Criar usuário de teste primeiro
    from cx_database.models.usuarios import criar_usuario
    test_user = criar_usuario("teste@email.com", "Senha123", "Teste User")
    
    if test_user:
        user_id = test_user["id"]
        
        print("\n[TESTE 1] Criar perfil:")
        perfil = criar_perfil(
            user_id=user_id,
            email="teste@email.com",
            username="testuser",
            display_name="Usuário Teste",
            nome="Teste da Silva",
            idade=28,
            interesses=["tecnologia", "ciência", "IA"],
            bio="Desenvolvedor apaixonado por tecnologia"
        )
        print(f"  Perfil criado: {perfil is not None}")
        if perfil:
            print(f"  Username: {perfil['username']}")
            print(f"  Interesses: {perfil['interesses']}")
        
        print("\n[TESTE 2] Buscar perfil por user_id:")
        buscado = buscar_perfil_por_user_id(user_id)
        print(f"  Perfil encontrado: {buscado is not None}")
        
        print("\n[TESTE 3] Atualizar perfil:")
        atualizado = atualizar_perfil(
            user_id=user_id,
            bio="Nova biografia atualizada",
            idade=29
        )
        print(f"  Atualização bem-sucedida: {atualizado is not None}")
        if atualizado:
            print(f"  Nova idade: {atualizado['idade']}")
            print(f"  Nova bio: {atualizado['bio']}")
        
        print("\n[TESTE 4] Deletar perfil:")
        deletado = deletar_perfil(user_id)
        print(f"  Perfil deletado: {deletado}")
        
        # Verificar se foi deletado
        verificado = buscar_perfil_por_user_id(user_id)
        print(f"  Perfil após deleção: {verificado}")
    
    print("\n" + "=" * 50)
    print("Todos os testes do perfis.py foram executados!")
    print("=" * 50)
