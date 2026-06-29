"""
Módulo de operações CRUD para conversas.

Este módulo gerencia todas as operações relacionadas a conversas com a IA,
incluindo criação, listagem, atualização e exclusão de conversas.

Funções disponíveis:
    - criar_conversa(): Cria uma nova conversa para um usuário
    - buscar_conversa_por_id(): Busca conversa pelo ID
    - listar_conversas_por_usuario(): Lista todas as conversas de um usuário
    - listar_conversas_por_projeto(): Lista conversas vinculadas a um projeto
    - atualizar_conversa(): Atualiza dados de uma conversa
    - deletar_conversa(): Remove uma conversa e suas mensagens
"""

import sqlite3
from typing import Optional

from cx_database.connection import get_connection
from cx_database.utils.helpers import gerar_id, agora


def criar_conversa(
    usuario_id: str,
    projeto_id: str = None,
    titulo: str = None
) -> Optional[dict]:
    """
    Cria uma nova conversa para um usuário.

    Args:
        usuario_id (str): ID do usuário proprietário da conversa.
        projeto_id (str, opcional): ID do projeto vinculado à conversa.
        titulo (str, opcional): Título da conversa. Se None, será "Conversa #X".

    Returns:
        dict: Dicionário com os dados da conversa criada, ou None em caso de erro.

    Example:
        >>> conversa = criar_conversa(usuario_id, projeto_id, "Planejamento do projeto")
        >>> if conversa:
        ...     print(f"Conversa criada: {conversa['titulo']}")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            conversa_id = gerar_id()
            criado_em = agora()

            # Gerar título automático se não fornecido
            if titulo is None or titulo.strip() == "":
                # Contar quantas conversas o usuário já tem
                cursor.execute("SELECT COUNT(*) FROM conversas WHERE usuario_id = ?", (usuario_id,))
                count = cursor.fetchone()[0] + 1
                titulo = f"Conversa #{count}"

            cursor.execute("""
                INSERT INTO conversas (id, usuario_id, projeto_id, titulo, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (conversa_id, usuario_id, projeto_id, titulo, criado_em, criado_em))

            conn.commit()

            return {
                "id": conversa_id,
                "usuario_id": usuario_id,
                "projeto_id": projeto_id,
                "titulo": titulo,
                "criado_em": criado_em,
                "atualizado_em": criado_em
            }

    except sqlite3.IntegrityError as e:
        print(f"[ERRO] Erro de integridade ao criar conversa: {e}")
        return None
    except sqlite3.OperationalError as e:
        print(f"[ERRO] Erro operacional ao criar conversa: {e}")
        return None
    except Exception as e:
        print(f"[ERRO] Erro inesperado ao criar conversa: {e}")
        return None


def buscar_conversa_por_id(conversa_id: str) -> Optional[dict]:
    """
    Busca uma conversa pelo seu ID único.

    Args:
        conversa_id (str): ID da conversa a ser buscada.

    Returns:
        dict: Dicionário com os dados da conversa, ou None se não encontrado.

    Example:
        >>> conversa = buscar_conversa_por_id("abc-123-def")
        >>> if conversa:
        ...     print(conversa["titulo"])
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM conversas WHERE id = ?", (conversa_id,))
            resultado = cursor.fetchone()

            if resultado:
                return dict(resultado)
            return None

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao buscar conversa por ID: {e}")
        return None


def listar_conversas_por_usuario(usuario_id: str) -> list:
    """
    Lista todas as conversas de um usuário específico.

    As conversas são ordenadas pela data de atualização (mais recentes primeiro).

    Args:
        usuario_id (str): ID do usuário proprietário das conversas.

    Returns:
        list: Lista de dicionários, cada um representando uma conversa.
              Retorna lista vazia se nenhuma conversa for encontrada.

    Example:
        >>> conversas = listar_conversas_por_usuario(usuario_id)
        >>> for c in conversas:
        ...     print(f"- {c['titulo']}")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM conversas
                WHERE usuario_id = ?
                ORDER BY atualizado_em DESC
            """, (usuario_id,))

            resultados = cursor.fetchall()
            return [dict(row) for row in resultados]

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao listar conversas do usuário: {e}")
        return []


def listar_conversas_por_projeto(projeto_id: str) -> list:
    """
    Lista todas as conversas vinculadas a um projeto específico.

    Args:
        projeto_id (str): ID do projeto vinculado às conversas.

    Returns:
        list: Lista de dicionários, cada um representando uma conversa.
              Retorna lista vazia se nenhuma conversa for encontrada.

    Example:
        >>> conversas = listar_conversas_por_projeto(projeto_id)
        >>> print(f"Conversas neste projeto: {len(conversas)}")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM conversas
                WHERE projeto_id = ?
                ORDER BY criado_em ASC
            """, (projeto_id,))

            resultados = cursor.fetchall()
            return [dict(row) for row in resultados]

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao listar conversas do projeto: {e}")
        return []


def atualizar_conversa(
    conversa_id: str,
    titulo: str = None
) -> Optional[dict]:
    """
    Atualiza os dados de uma conversa existente.

    Apenas os parâmetros fornecidos (não None) serão atualizados.

    Args:
        conversa_id (str): ID da conversa a ser atualizada.
        titulo (str, opcional): Novo título da conversa.

    Returns:
        dict: Dicionário com os dados atualizados da conversa, ou None se não encontrado/erro.

    Example:
        >>> atualizar_conversa(conversa_id, titulo="Novo Título da Conversa")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Verificar se a conversa existe
            cursor.execute("SELECT * FROM conversas WHERE id = ?", (conversa_id,))
            if not cursor.fetchone():
                print(f"[ERRO] Conversa com ID '{conversa_id}' não encontrada.")
                return None

            # Construir atualização dinâmica
            atualizacoes = []
            valores = []

            if titulo is not None:
                atualizacoes.append("titulo = ?")
                valores.append(titulo)

            if not atualizacoes:
                print("[ERRO] Nenhum campo para atualizar.")
                return None

            # Adicionar updated_at e ID
            atualizado_em = agora()
            atualizacoes.append("atualizado_em = ?")
            valores.append(atualizado_em)
            valores.append(conversa_id)

            # Executar atualização
            query = f"UPDATE conversas SET {', '.join(atualizacoes)} WHERE id = ?"
            cursor.execute(query, valores)
            conn.commit()

            # Retornar conversa atualizada
            cursor.execute("SELECT * FROM conversas WHERE id = ?", (conversa_id,))
            return dict(cursor.fetchone())

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao atualizar conversa: {e}")
        return None


def deletar_conversa(conversa_id: str) -> bool:
    """
    Remove uma conversa e todas as suas mensagens associadas.

    Esta operação exclui em cascata todas as mensagens vinculadas à conversa.

    Args:
        conversa_id (str): ID da conversa a ser removida.

    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário.

    Warning:
        Esta operação é irreversível. Todas as mensagens da conversa serão perdidas.

    Example:
        >>> deletar_conversa(conversa_id)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Primeiro, excluir todas as mensagens desta conversa
            cursor.execute("DELETE FROM mensagens WHERE conversa_id = ?", (conversa_id,))

            # Agora excluir a conversa
            cursor.execute("DELETE FROM conversas WHERE id = ?", (conversa_id,))

            conn.commit()
            return cursor.rowcount > 0

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao deletar conversa: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("=== TESTES DO MÓDULO modelos/conversas.py ===")
    print("=" * 60)

    # Configurar o banco primeiro
    from cx_database.setup import criar_todas_as_tabelas, inserir_dados_iniciais
    from cx_database.models.usuarios import criar_usuario, buscar_usuario_por_email
    from cx_database.models.projetos import criar_projeto

    criar_todas_as_tabelas()
    inserir_dados_iniciais()

    # Criar usuário e projeto de teste
    print("\n[PREPARAÇÃO] Criando usuário e projeto de teste...")
    usuario_teste = criar_usuario(
        nome="Usuario Teste Conversas",
        email="teste.conversas@email.com",
        senha="Senha1234"
    )
    if not usuario_teste:
        usuario_teste = buscar_usuario_por_email("teste.conversas@email.com")
    usuario_id = usuario_teste["id"]
    print(f"  Usuário: {usuario_id}")

    projeto_teste = criar_projeto(usuario_id, "Projeto para Conversas")
    projeto_id = projeto_teste["id"] if projeto_teste else None
    print(f"  Projeto: {projeto_id}")

    print("\n[TESTE 1] Criar conversa sem título (automático):")
    conversa1 = criar_conversa(usuario_id)
    if conversa1:
        print(f"  Conversa criada: {conversa1['titulo']}")
        print(f"  ID: {conversa1['id']}")
    else:
        print("  Falha ao criar conversa")

    print("\n[TESTE 2] Criar conversa com título personalizado:")
    conversa2 = criar_conversa(usuario_id, projeto_id, "Discussão sobre arquitetura")
    if conversa2:
        print(f"  Conversa criada: {conversa2['titulo']}")
        print(f"  Vinculada ao projeto: {conversa2['projeto_id']}")

    print("\n[TESTE 3] Criar mais conversas:")
    conversa3 = criar_conversa(usuario_id, projeto_id, "Brainstorming inicial")
    conversa4 = criar_conversa(usuario_id, None, "Ideias gerais")
    print(f"  Conversa 3: {conversa3['titulo'] if conversa3 else 'Falha'}")
    print(f"  Conversa 4: {conversa4['titulo'] if conversa4 else 'Falha'}")

    print("\n[TESTE 4] Buscar conversa por ID:")
    if conversa2:
        conversa_busca = buscar_conversa_por_id(conversa2['id'])
        if conversa_busca:
            print(f"  Encontrada: {conversa_busca['titulo']}")

    print("\n[TESTE 5] Listar todas as conversas do usuário:")
    conversas_usuario = listar_conversas_por_usuario(usuario_id)
    print(f"  Total de conversas: {len(conversas_usuario)}")
    for c in conversas_usuario:
        projeto_info = f"(Projeto: {c['projeto_id'][-8:]})" if c['projeto_id'] else "(Sem projeto)"
        print(f"    - {c['titulo']} {projeto_info}")

    print("\n[TESTE 6] Listar conversas por projeto:")
    if projeto_id:
        conversas_projeto = listar_conversas_por_projeto(projeto_id)
        print(f"  Conversas vinculadas ao projeto: {len(conversas_projeto)}")
        for c in conversas_projeto:
            print(f"    - {c['titulo']}")

    print("\n[TESTE 7] Atualizar conversa:")
    if conversa1:
        atualizada = atualizar_conversa(conversa1['id'], titulo="Minha Primeira Conversa")
        if atualizada:
            print(f"  Título atualizado para: {atualizada['titulo']}")

    print("\n[TESTE 8] Deletar conversa:")
    if conversa4:
        sucesso = deletar_conversa(conversa4['id'])
        print(f"  Conversa deletada: {sucesso}")

        # Verificar se foi removida
        conversa_verificacao = buscar_conversa_por_id(conversa4['id'])
        print(f"  Conversa ainda existe: {conversa_verificacao is not None} (esperado: False)")

    print("\n" + "=" * 60)
    print("Todos os testes do conversas.py foram executados!")
    print("=" * 60)
