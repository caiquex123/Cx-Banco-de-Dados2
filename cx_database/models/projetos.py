"""
Módulo de operações CRUD para projetos.

Este módulo gerencia todas as operações relacionadas a projetos dos usuários,
incluindo criação, listagem, atualização e exclusão de projetos.

Funções disponíveis:
    - criar_projeto(): Cria um novo projeto para um usuário
    - buscar_projeto_por_id(): Busca projeto pelo ID
    - listar_projetos_por_usuario(): Lista todos os projetos de um usuário
    - listar_todos_projetos(): Lista todos os projetos do sistema
    - atualizar_projeto(): Atualiza dados de um projeto
    - deletar_projeto(): Remove um projeto
"""

import sqlite3
from typing import Optional

from cx_database.connection import get_connection
from cx_database.utils.helpers import gerar_id, agora


def criar_projeto(
    usuario_id: str,
    titulo: str,
    descricao: str = None,
    status: str = "rascunho"
) -> Optional[dict]:
    """
    Cria um novo projeto para um usuário.

    Args:
        usuario_id (str): ID do usuário proprietário do projeto.
        titulo (str): Título do projeto.
        descricao (str, opcional): Descrição detalhada do projeto.
        status (str, opcional): Status inicial. Opções: 'rascunho', 'em_andamento', 'concluido', 'arquivado'.

    Returns:
        dict: Dicionário com os dados do projeto criado, ou None em caso de erro.

    Example:
        >>> projeto = criar_projeto(usuario_id, "Meu Startup", "Descrição do projeto")
        >>> if projeto:
        ...     print(f"Projeto '{projeto['titulo']}' criado!")
    """
    # Validar status
    statuses_validos = ["rascunho", "em_andamento", "concluido", "arquivado"]
    if status not in statuses_validos:
        print(f"[ERRO] Status inválido '{status}'. Use: {', '.join(statuses_validos)}")
        return None

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            projeto_id = gerar_id()
            criado_em = agora()

            cursor.execute("""
                INSERT INTO projetos (id, usuario_id, titulo, descricao, status, criado_em, atualizado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (projeto_id, usuario_id, titulo, descricao, status, criado_em, criado_em))

            conn.commit()

            return {
                "id": projeto_id,
                "usuario_id": usuario_id,
                "titulo": titulo,
                "descricao": descricao,
                "status": status,
                "criado_em": criado_em,
                "atualizado_em": criado_em
            }

    except sqlite3.IntegrityError as e:
        print(f"[ERRO] Erro de integridade ao criar projeto: {e}")
        return None
    except sqlite3.OperationalError as e:
        print(f"[ERRO] Erro operacional ao criar projeto: {e}")
        return None
    except Exception as e:
        print(f"[ERRO] Erro inesperado ao criar projeto: {e}")
        return None


def buscar_projeto_por_id(projeto_id: str) -> Optional[dict]:
    """
    Busca um projeto pelo seu ID único.

    Args:
        projeto_id (str): ID do projeto a ser buscado.

    Returns:
        dict: Dicionário com os dados do projeto, ou None se não encontrado.

    Example:
        >>> projeto = buscar_projeto_por_id("abc-123-def")
        >>> if projeto:
        ...     print(projeto["titulo"])
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projetos WHERE id = ?", (projeto_id,))
            resultado = cursor.fetchone()

            if resultado:
                return dict(resultado)
            return None

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao buscar projeto por ID: {e}")
        return None


def listar_projetos_por_usuario(
    usuario_id: str,
    status: str = None
) -> list:
    """
    Lista todos os projetos de um usuário específico.

    Args:
        usuario_id (str): ID do usuário proprietário dos projetos.
        status (str, opcional): Filtrar por status específico.
                                Opções: 'rascunho', 'em_andamento', 'concluido', 'arquivado'.

    Returns:
        list: Lista de dicionários, cada um representando um projeto.
              Retorna lista vazia se nenhum projeto for encontrado.

    Example:
        >>> projetos = listar_projetos_por_usuario(usuario_id)
        >>> for p in projetos:
        ...     print(f"- {p['titulo']} ({p['status']})")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            if status:
                cursor.execute("""
                    SELECT * FROM projetos
                    WHERE usuario_id = ? AND status = ?
                    ORDER BY atualizado_em DESC
                """, (usuario_id, status))
            else:
                cursor.execute("""
                    SELECT * FROM projetos
                    WHERE usuario_id = ?
                    ORDER BY atualizado_em DESC
                """, (usuario_id,))

            resultados = cursor.fetchall()
            return [dict(row) for row in resultados]

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao listar projetos do usuário: {e}")
        return []


def listar_todos_projetos(status: str = None) -> list:
    """
    Lista todos os projetos do sistema (admin).

    Args:
        status (str, opcional): Filtrar por status específico.

    Returns:
        list: Lista de dicionários, cada um representando um projeto.

    Example:
        >>> projetos = listar_todos_projetos(status="em_andamento")
        >>> print(f"Projetos em andamento: {len(projetos)}")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            if status:
                cursor.execute("""
                    SELECT * FROM projetos
                    WHERE status = ?
                    ORDER BY criado_em DESC
                """, (status,))
            else:
                cursor.execute("SELECT * FROM projetos ORDER BY criado_em DESC")

            resultados = cursor.fetchall()
            return [dict(row) for row in resultados]

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao listar todos os projetos: {e}")
        return []


def atualizar_projeto(
    projeto_id: str,
    titulo: str = None,
    descricao: str = None,
    status: str = None
) -> Optional[dict]:
    """
    Atualiza os dados de um projeto existente.

    Apenas os parâmetros fornecidos (não None) serão atualizados.

    Args:
        projeto_id (str): ID do projeto a ser atualizado.
        titulo (str, opcional): Novo título do projeto.
        descricao (str, opcional): Nova descrição do projeto.
        status (str, opcional): Novo status do projeto.

    Returns:
        dict: Dicionário com os dados atualizados do projeto, ou None se não encontrado/erro.

    Example:
        >>> atualizar_projeto(projeto_id, status="em_andamento")
        >>> atualizar_projeto(projeto_id, titulo="Novo Título")
    """
    # Validar status se fornecido
    if status is not None:
        statuses_validos = ["rascunho", "em_andamento", "concluido", "arquivado"]
        if status not in statuses_validos:
            print(f"[ERRO] Status inválido '{status}'. Use: {', '.join(statuses_validos)}")
            return None

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Verificar se o projeto existe
            cursor.execute("SELECT * FROM projetos WHERE id = ?", (projeto_id,))
            if not cursor.fetchone():
                print(f"[ERRO] Projeto com ID '{projeto_id}' não encontrado.")
                return None

            # Construir atualização dinâmica
            atualizacoes = []
            valores = []

            if titulo is not None:
                atualizacoes.append("titulo = ?")
                valores.append(titulo)
            if descricao is not None:
                atualizacoes.append("descricao = ?")
                valores.append(descricao)
            if status is not None:
                atualizacoes.append("status = ?")
                valores.append(status)

            if not atualizacoes:
                print("[ERRO] Nenhum campo para atualizar.")
                return None

            # Adicionar updated_at e ID
            atualizado_em = agora()
            atualizacoes.append("atualizado_em = ?")
            valores.append(atualizado_em)
            valores.append(projeto_id)

            # Executar atualização
            query = f"UPDATE projetos SET {', '.join(atualizacoes)} WHERE id = ?"
            cursor.execute(query, valores)
            conn.commit()

            # Retornar projeto atualizado
            cursor.execute("SELECT * FROM projetos WHERE id = ?", (projeto_id,))
            return dict(cursor.fetchone())

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao atualizar projeto: {e}")
        return None


def deletar_projeto(projeto_id: str) -> bool:
    """
    Remove um projeto do banco de dados.

    Nota: A exclusão de um projeto pode afetar conversas vinculadas a ele.
    As conversas associadas terão projeto_id = NULL após a exclusão.

    Args:
        projeto_id (str): ID do projeto a ser removido.

    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário.

    Example:
        >>> deletar_projeto(projeto_id)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Primeiro, desvincular conversas deste projeto
            cursor.execute("""
                UPDATE conversas SET projeto_id = NULL WHERE projeto_id = ?
            """, (projeto_id,))

            # Agora excluir o projeto
            cursor.execute("DELETE FROM projetos WHERE id = ?", (projeto_id,))

            conn.commit()
            return cursor.rowcount > 0

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao deletar projeto: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("=== TESTES DO MÓDULO modelos/projetos.py ===")
    print("=" * 60)

    # Configurar o banco primeiro
    from cx_database.setup import criar_todas_as_tabelas, inserir_dados_iniciais
    from cx_database.models.usuarios import criar_usuario, buscar_usuario_por_email

    criar_todas_as_tabelas()
    inserir_dados_iniciais()

    # Criar usuário de teste
    print("\n[PREPARAÇÃO] Criando usuário de teste...")
    usuario_teste = criar_usuario(
        nome="Usuario Teste Projetos",
        email="teste.projetos@email.com",
        senha="Senha1234"
    )
    if not usuario_teste:
        usuario_teste = buscar_usuario_por_email("teste.projetos@email.com")
    usuario_id = usuario_teste["id"]
    print(f"  Usuário criado/encontrado: {usuario_id}")

    print("\n[TESTE 1] Criar projeto:")
    projeto1 = criar_projeto(
        usuario_id=usuario_id,
        titulo="Meu Primeiro Projeto",
        descricao="Descrição detalhada do meu projeto incrível",
        status="rascunho"
    )
    if projeto1:
        print(f"  Projeto criado: {projeto1['titulo']}")
        print(f"  ID: {projeto1['id']}")
        print(f"  Status: {projeto1['status']}")
    else:
        print("  Falha ao criar projeto")

    print("\n[TESTE 2] Criar mais projetos com diferentes status:")
    projeto2 = criar_projeto(usuario_id, "Projeto em Andamento", status="em_andamento")
    projeto3 = criar_projeto(usuario_id, "Projeto Concluído", status="concluido")
    print(f"  Projeto 2 criado: {projeto2['titulo'] if projeto2 else 'Falha'}")
    print(f"  Projeto 3 criado: {projeto3['titulo'] if projeto3 else 'Falha'}")

    print("\n[TESTE 3] Buscar projeto por ID:")
    if projeto1:
        projeto_busca = buscar_projeto_por_id(projeto1['id'])
        if projeto_busca:
            print(f"  Encontrado: {projeto_busca['titulo']}")

    print("\n[TESTE 4] Listar projetos do usuário:")
    projetos_usuario = listar_projetos_por_usuario(usuario_id)
    print(f"  Total de projetos do usuário: {len(projetos_usuario)}")
    for p in projetos_usuario:
        print(f"    - {p['titulo']} ({p['status']})")

    print("\n[TESTE 5] Listar projetos filtrando por status:")
    projetos_em_andamento = listar_projetos_por_usuario(usuario_id, status="em_andamento")
    print(f"  Projetos em andamento: {len(projetos_em_andamento)}")

    print("\n[TESTE 6] Atualizar projeto:")
    if projeto1:
        atualizado = atualizar_projeto(
            projeto1['id'],
            titulo="Meu Projeto Atualizado",
            status="em_andamento"
        )
        if atualizado:
            print(f"  Título atualizado para: {atualizado['titulo']}")
            print(f"  Status atualizado para: {atualizado['status']}")

    print("\n[TESTE 7] Listar todos os projetos do sistema:")
    todos_projetos = listar_todos_projetos()
    print(f"  Total de projetos no sistema: {len(todos_projetos)}")

    print("\n[TESTE 8] Deletar projeto:")
    if projeto3:
        sucesso = deletar_projeto(projeto3['id'])
        print(f"  Projeto deletado: {sucesso}")

        # Verificar se foi removido
        projeto_verificacao = buscar_projeto_por_id(projeto3['id'])
        print(f"  Projeto ainda existe: {projeto_verificacao is not None} (esperado: False)")

    print("\n[TESTE 9] Tentar criar projeto com status inválido:")
    projeto_invalido = criar_projeto(usuario_id, "Projeto Inválido", status="invalido")
    print(f"  Resultado: {projeto_invalido is None} (esperado: True)")

    print("\n" + "=" * 60)
    print("Todos os testes do projetos.py foram executados!")
    print("=" * 60)
