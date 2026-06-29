"""
Módulo de operações CRUD para planos de assinatura.

Este módulo gerencia todas as operações relacionadas a planos no banco de dados,
incluindo criar, ler, atualizar e deletar planos de assinatura.

Funções disponíveis:
    - criar_plano(): Cria um novo plano
    - buscar_plano_por_id(): Busca um plano pelo ID
    - buscar_plano_por_nome(): Busca um plano pelo nome (ex: 'gratuito', 'pro')
    - listar_planos(): Lista todos os planos ativos ou todos
    - atualizar_plano(): Atualiza dados de um plano existente
    - deletar_plano(): Remove um plano do banco (soft delete por padrão)
"""

import sqlite3
from typing import Optional

from cx_database.connection import get_connection
from cx_database.utils.helpers import gerar_id, agora


def criar_plano(
    nome: str,
    limite_projetos: int = 3,
    limite_mensagens: int = 100,
    preco_mensal: float = 0.0,
    ativo: int = 1
) -> Optional[dict]:
    """
    Cria um novo plano de assinatura no banco de dados.

    Args:
        nome (str): Nome único do plano (ex: 'gratuito', 'pro', 'enterprise').
        limite_projetos (int): Número máximo de projetos permitidos. -1 para ilimitado.
        limite_mensagens (int): Número máximo de mensagens permitidas. -1 para ilimitado.
        preco_mensal (float): Preço mensal do plano em reais.
        ativo (int): 1 para plano ativo, 0 para inativo.

    Returns:
        dict: Dicionário com os dados do plano criado, ou None em caso de erro.

    Raises:
        sqlite3.IntegrityError: Se já existir um plano com o mesmo nome.

    Example:
        >>> plano = criar_plano("startup", limite_projetos=10, preco_mensal=19.90)
        >>> print(plano["nome"])
        'startup'
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            plano_id = gerar_id()
            criado_em = agora()

            cursor.execute("""
                INSERT INTO planos (id, nome, limite_projetos, limite_mensagens, preco_mensal, ativo, criado_em)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (plano_id, nome, limite_projetos, limite_mensagens, preco_mensal, ativo, criado_em))

            conn.commit()

            # Retornar o plano criado
            return {
                "id": plano_id,
                "nome": nome,
                "limite_projetos": limite_projetos,
                "limite_mensagens": limite_mensagens,
                "preco_mensal": preco_mensal,
                "ativo": ativo,
                "criado_em": criado_em
            }

    except sqlite3.IntegrityError as e:
        print(f"[ERRO] Plano com nome '{nome}' já existe: {e}")
        return None
    except sqlite3.OperationalError as e:
        print(f"[ERRO] Erro operacional ao criar plano: {e}")
        return None
    except Exception as e:
        print(f"[ERRO] Erro inesperado ao criar plano: {e}")
        return None


def buscar_plano_por_id(plano_id: str) -> Optional[dict]:
    """
    Busca um plano de assinatura pelo seu ID único.

    Args:
        plano_id (str): ID do plano a ser buscado.

    Returns:
        dict: Dicionário com os dados do plano, ou None se não encontrado.

    Example:
        >>> plano = buscar_plano_por_id("abc-123-def")
        >>> if plano:
        ...     print(plano["nome"])
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM planos WHERE id = ?", (plano_id,))
            resultado = cursor.fetchone()

            if resultado:
                return dict(resultado)
            return None

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao buscar plano por ID: {e}")
        return None


def buscar_plano_por_nome(nome: str) -> Optional[dict]:
    """
    Busca um plano de assinatura pelo seu nome.

    Args:
        nome (str): Nome do plano (ex: 'gratuito', 'pro', 'enterprise').

    Returns:
        dict: Dicionário com os dados do plano, ou None se não encontrado.

    Example:
        >>> plano = buscar_plano_por_nome("pro")
        >>> if plano:
        ...     print(f"Limite de projetos: {plano['limite_projetos']}")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM planos WHERE nome = ?", (nome,))
            resultado = cursor.fetchone()

            if resultado:
                return dict(resultado)
            return None

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao buscar plano por nome: {e}")
        return None


def listar_planos(apenas_ativos: bool = True) -> list:
    """
    Lista todos os planos de assinatura cadastrados.

    Args:
        apenas_ativos (bool): Se True, retorna apenas planos ativos.
                              Se False, retorna todos os planos.

    Returns:
        list: Lista de dicionários, cada um representando um plano.
              Retorna lista vazia se nenhum plano for encontrado.

    Example:
        >>> planos = listar_planos()
        >>> for plano in planos:
        ...     print(f"{plano['nome']}: R$ {plano['preco_mensal']}")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            if apenas_ativos:
                cursor.execute("SELECT * FROM planos WHERE ativo = 1 ORDER BY preco_mensal ASC")
            else:
                cursor.execute("SELECT * FROM planos ORDER BY preco_mensal ASC")

            resultados = cursor.fetchall()
            return [dict(row) for row in resultados]

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao listar planos: {e}")
        return []


def atualizar_plano(
    plano_id: str,
    nome: str = None,
    limite_projetos: int = None,
    limite_mensagens: int = None,
    preco_mensal: float = None,
    ativo: int = None
) -> Optional[dict]:
    """
    Atualiza os dados de um plano existente.

    Apenas os parâmetros fornecidos (não None) serão atualizados.

    Args:
        plano_id (str): ID do plano a ser atualizado.
        nome (str, opcional): Novo nome do plano.
        limite_projetos (int, opcional): Novo limite de projetos.
        limite_mensagens (int, opcional): Novo limite de mensagens.
        preco_mensal (float, opcional): Novo preço mensal.
        ativo (int, opcional): 1 para ativar, 0 para desativar.

    Returns:
        dict: Dicionário com os dados atualizados do plano, ou None se não encontrado/erro.

    Example:
        >>> atualizar_plano(plano_id, preco_mensal=39.90)
        >>> atualizar_plano(plano_id, ativo=0)  # Desativa o plano
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Verificar se o plano existe
            cursor.execute("SELECT * FROM planos WHERE id = ?", (plano_id,))
            if not cursor.fetchone():
                print(f"[ERRO] Plano com ID '{plano_id}' não encontrado.")
                return None

            # Construir atualização dinâmica
            atualizacoes = []
            valores = []

            if nome is not None:
                atualizacoes.append("nome = ?")
                valores.append(nome)
            if limite_projetos is not None:
                atualizacoes.append("limite_projetos = ?")
                valores.append(limite_projetos)
            if limite_mensagens is not None:
                atualizacoes.append("limite_mensagens = ?")
                valores.append(limite_mensagens)
            if preco_mensal is not None:
                atualizacoes.append("preco_mensal = ?")
                valores.append(preco_mensal)
            if ativo is not None:
                atualizacoes.append("ativo = ?")
                valores.append(ativo)

            if not atualizacoes:
                print("[ERRO] Nenhum campo para atualizar.")
                return None

            # Adicionar updated_at e ID
            atualizado_em = agora()
            atualizacoes.append("atualizado_em = ?")
            valores.append(atualizado_em)
            valores.append(plano_id)

            # Executar atualização
            query = f"UPDATE planos SET {', '.join(atualizacoes)} WHERE id = ?"
            cursor.execute(query, valores)
            conn.commit()

            # Retornar plano atualizado
            cursor.execute("SELECT * FROM planos WHERE id = ?", (plano_id,))
            return dict(cursor.fetchone())

    except sqlite3.IntegrityError as e:
        print(f"[ERRO] Violação de integridade ao atualizar plano: {e}")
        return None
    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao atualizar plano: {e}")
        return None


def deletar_plano(plano_id: str, exclusao_fisica: bool = False) -> bool:
    """
    Remove um plano do banco de dados.

    Por padrão, realiza um "soft delete" (apenas desativa o plano).
    Se exclusao_fisica=True, remove permanentemente do banco.

    Args:
        plano_id (str): ID do plano a ser removido.
        exclusao_fisica (bool): Se True, remove permanentemente.
                                Se False, apenas desativa (soft delete).

    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário.

    Warning:
        Exclusão física pode violar chaves estrangeiras se houver usuários
        vinculados a este plano. Use com cautela.

    Example:
        >>> deletar_plano(plano_id)  # Soft delete (desativa)
        >>> deletar_plano(plano_id, exclusao_fisica=True)  # Remove permanentemente
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            if exclusao_fisica:
                # Exclusão permanente
                cursor.execute("DELETE FROM planos WHERE id = ?", (plano_id,))
            else:
                # Soft delete (apenas desativa)
                cursor.execute("""
                    UPDATE planos SET ativo = 0, atualizado_em = ? WHERE id = ?
                """, (agora(), plano_id))

            conn.commit()
            return cursor.rowcount > 0

    except sqlite3.IntegrityError as e:
        print(f"[ERRO] Não é possível excluir plano com usuários vinculados: {e}")
        return False
    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao deletar plano: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("=== TESTES DO MÓDULO modelos/planos.py ===")
    print("=" * 60)

    # Configurar o banco primeiro
    from cx_database.setup import criar_todas_as_tabelas, inserir_dados_iniciais
    criar_todas_as_tabelas()
    inserir_dados_iniciais()

    print("\n[TESTE 1] Listar todos os planos:")
    planos = listar_planos(apenas_ativos=False)
    for plano in planos:
        print(f"  - {plano['nome']}: R$ {plano['preco_mensal']:.2f}/mês")

    print("\n[TESTE 2] Buscar plano por nome ('gratuito'):")
    plano_gratuito = buscar_plano_por_nome("gratuito")
    if plano_gratuito:
        print(f"  ID: {plano_gratuito['id']}")
        print(f"  Limite projetos: {plano_gratuito['limite_projetos']}")
        print(f"  Limite mensagens: {plano_gratuito['limite_mensagens']}")

    print("\n[TESTE 3] Buscar plano por ID:")
    if plano_gratuito:
        plano_por_id = buscar_plano_por_id(plano_gratuito['id'])
        print(f"  Encontrado: {plano_por_id is not None}")

    print("\n[TESTE 4] Criar novo plano:")
    novo_plano = criar_plano(
        nome="teste_exclusivo",
        limite_projetos=50,
        limite_mensagens=5000,
        preco_mensal=79.90
    )
    if novo_plano:
        print(f"  Plano criado: {novo_plano['nome']}")
        print(f"  ID: {novo_plano['id']}")
    else:
        print("  Falha ao criar plano (pode já existir)")

    print("\n[TESTE 5] Atualizar plano:")
    if novo_plano:
        atualizado = atualizar_plano(
            novo_plano['id'],
            preco_mensal=59.90,
            limite_projetos=75
        )
        if atualizado:
            print(f"  Preço atualizado para: R$ {atualizado['preco_mensal']:.2f}")
            print(f"  Limite projetos atualizado para: {atualizado['limite_projetos']}")

    print("\n[TESTE 6] Deletar plano (soft delete):")
    if novo_plano:
        sucesso = deletar_plano(novo_plano['id'])
        print(f"  Soft delete realizado: {sucesso}")

        # Verificar se está desativado
        plano_verificacao = buscar_plano_por_id(novo_plano['id'])
        if plano_verificacao:
            print(f"  Plano ainda existe mas ativo={plano_verificacao['ativo']}")

    print("\n[TESTE 7] Listar apenas planos ativos:")
    ativos = listar_planos(apenas_ativos=True)
    print(f"  Planos ativos encontrados: {len(ativos)}")
    for plano in ativos:
        print(f"    - {plano['nome']}")

    print("\n" + "=" * 60)
    print("Todos os testes do planos.py foram executados!")
    print("=" * 60)
