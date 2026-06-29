"""
Módulo de operações CRUD para mensagens.

Este módulo gerencia todas as operações relacionadas a mensagens individuais
dentro das conversas com a IA, incluindo criação, listagem e exclusão.

Funções disponíveis:
    - criar_mensagem(): Adiciona uma nova mensagem a uma conversa
    - buscar_mensagem_por_id(): Busca mensagem pelo ID
    - listar_mensagens_por_conversa(): Lista todas as mensagens de uma conversa
    - atualizar_mensagem(): Atualiza o conteúdo de uma mensagem
    - deletar_mensagem(): Remove uma mensagem
    - contar_mensagens_por_usuario(): Conta total de mensagens de um usuário
"""

import sqlite3
from typing import Optional

from cx_database.connection import get_connection
from cx_database.utils.helpers import gerar_id, agora


def criar_mensagem(
    conversa_id: str,
    papel: str,
    conteudo: str
) -> Optional[dict]:
    """
    Cria uma nova mensagem em uma conversa.

    Args:
        conversa_id (str): ID da conversa onde a mensagem será adicionada.
        papel (str): Quem enviou a mensagem. Opções: 'usuario' ou 'assistente'.
        conteudo (str): Conteúdo textual da mensagem.

    Returns:
        dict: Dicionário com os dados da mensagem criada, ou None em caso de erro.

    Example:
        >>> msg = criar_mensagem(conversa_id, "usuario", "Olá, preciso de ajuda!")
        >>> if msg:
        ...     print(f"Mensagem criada em {msg['criado_em']}")
    """
    # Validar papel
    papeis_validos = ["usuario", "assistente"]
    if papel not in papeis_validos:
        print(f"[ERRO] Papel inválido '{papel}'. Use: {', '.join(papeis_validos)}")
        return None

    # Validar conteúdo
    if not conteudo or conteudo.strip() == "":
        print("[ERRO] Conteúdo da mensagem não pode ser vazio.")
        return None

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            mensagem_id = gerar_id()
            criado_em = agora()

            cursor.execute("""
                INSERT INTO mensagens (id, conversa_id, papel, conteudo, criado_em)
                VALUES (?, ?, ?, ?, ?)
            """, (mensagem_id, conversa_id, papel, conteudo, criado_em))

            # Atualizar o timestamp da conversa para indicar atividade recente
            cursor.execute("""
                UPDATE conversas SET atualizado_em = ? WHERE id = ?
            """, (criado_em, conversa_id))

            conn.commit()

            return {
                "id": mensagem_id,
                "conversa_id": conversa_id,
                "papel": papel,
                "conteudo": conteudo,
                "criado_em": criado_em
            }

    except sqlite3.IntegrityError as e:
        print(f"[ERRO] Erro de integridade ao criar mensagem: {e}")
        return None
    except sqlite3.OperationalError as e:
        print(f"[ERRO] Erro operacional ao criar mensagem: {e}")
        return None
    except Exception as e:
        print(f"[ERRO] Erro inesperado ao criar mensagem: {e}")
        return None


def buscar_mensagem_por_id(mensagem_id: str) -> Optional[dict]:
    """
    Busca uma mensagem pelo seu ID único.

    Args:
        mensagem_id (str): ID da mensagem a ser buscada.

    Returns:
        dict: Dicionário com os dados da mensagem, ou None se não encontrado.

    Example:
        >>> msg = buscar_mensagem_por_id("abc-123-def")
        >>> if msg:
        ...     print(msg["conteudo"])
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mensagens WHERE id = ?", (mensagem_id,))
            resultado = cursor.fetchone()

            if resultado:
                return dict(resultado)
            return None

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao buscar mensagem por ID: {e}")
        return None


def listar_mensagens_por_conversa(conversa_id: str) -> list:
    """
    Lista todas as mensagens de uma conversa em ordem cronológica.

    As mensagens são ordenadas pela data de criação (mais antigas primeiro),
    simulando o fluxo natural de uma conversa.

    Args:
        conversa_id (str): ID da conversa cujas mensagens serão listadas.

    Returns:
        list: Lista de dicionários, cada um representando uma mensagem.
              Retorna lista vazia se nenhuma mensagem for encontrada.

    Example:
        >>> mensagens = listar_mensagens_por_conversa(conversa_id)
        >>> for m in mensagens:
        ...     print(f"{m['papel']}: {m['conteudo'][:50]}...")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM mensagens
                WHERE conversa_id = ?
                ORDER BY criado_em ASC
            """, (conversa_id,))

            resultados = cursor.fetchall()
            return [dict(row) for row in resultados]

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao listar mensagens da conversa: {e}")
        return []


def listar_mensagens_paginadas(
    conversa_id: str,
    limite: int = 50,
    offset: int = 0
) -> list:
    """
    Lista mensagens de uma conversa com paginação.

    Útil para conversas longas onde não se deseja carregar todas as mensagens
    de uma vez.

    Args:
        conversa_id (str): ID da conversa.
        limite (int): Número máximo de mensagens a retornar.
        offset (int): Quantidade de mensagens a pular (para paginação).

    Returns:
        list: Lista de dicionários com as mensagens paginadas.

    Example:
        >>> # Primeira página (50 mensagens)
        >>> msgs1 = listar_mensagens_paginadas(conversa_id, limite=50, offset=0)
        >>> # Segunda página (próximas 50)
        >>> msgs2 = listar_mensagens_paginadas(conversa_id, limite=50, offset=50)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM mensagens
                WHERE conversa_id = ?
                ORDER BY criado_em DESC
                LIMIT ? OFFSET ?
            """, (conversa_id, limite, offset))

            resultados = cursor.fetchall()
            # Inverter para ordem cronológica
            return [dict(row) for row in reversed(resultados)]

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao listar mensagens paginadas: {e}")
        return []


def atualizar_mensagem(
    mensagem_id: str,
    conteudo: str
) -> Optional[dict]:
    """
    Atualiza o conteúdo de uma mensagem existente.

    Nota: Apenas o conteúdo pode ser atualizado. O papel e a conversa
    são imutáveis após a criação.

    Args:
        mensagem_id (str): ID da mensagem a ser atualizada.
        conteudo (str): Novo conteúdo da mensagem.

    Returns:
        dict: Dicionário com os dados atualizados da mensagem, ou None se não encontrado/erro.

    Example:
        >>> atualizar_mensagem(mensagem_id, "Conteúdo corrigido")
    """
    if not conteudo or conteudo.strip() == "":
        print("[ERRO] Conteúdo não pode ser vazio.")
        return None

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Verificar se a mensagem existe
            cursor.execute("SELECT * FROM mensagens WHERE id = ?", (mensagem_id,))
            if not cursor.fetchone():
                print(f"[ERRO] Mensagem com ID '{mensagem_id}' não encontrada.")
                return None

            # Atualizar conteúdo
            cursor.execute("""
                UPDATE mensagens SET conteudo = ? WHERE id = ?
            """, (conteudo, mensagem_id))

            conn.commit()

            # Retornar mensagem atualizada
            cursor.execute("SELECT * FROM mensagens WHERE id = ?", (mensagem_id,))
            return dict(cursor.fetchone())

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao atualizar mensagem: {e}")
        return None


def deletar_mensagem(mensagem_id: str) -> bool:
    """
    Remove uma mensagem do banco de dados.

    Args:
        mensagem_id (str): ID da mensagem a ser removida.

    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário.

    Example:
        >>> deletar_mensagem(mensagem_id)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM mensagens WHERE id = ?", (mensagem_id,))
            conn.commit()
            return cursor.rowcount > 0

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao deletar mensagem: {e}")
        return False


def contar_mensagens_por_usuario(usuario_id: str) -> int:
    """
    Conta o total de mensagens de um usuário específico.

    Esta função percorre todas as conversas do usuário e soma suas mensagens.
    Útil para verificar limites de uso do plano.

    Args:
        usuario_id (str): ID do usuário.

    Returns:
        int: Total de mensagens do usuário. Retorna 0 em caso de erro.

    Example:
        >>> total = contar_mensagens_por_usuario(usuario_id)
        >>> print(f"Usuário tem {total} mensagens")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Contar mensagens através das conversas do usuário
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM mensagens m
                INNER JOIN conversas c ON m.conversa_id = c.id
                WHERE c.usuario_id = ?
            """, (usuario_id,))

            resultado = cursor.fetchone()
            return resultado["total"] if resultado else 0

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao contar mensagens do usuário: {e}")
        return 0


def contar_mensagens_por_papel(conversa_id: str, papel: str) -> int:
    """
    Conta quantas mensagens de um determinado papel existem em uma conversa.

    Args:
        conversa_id (str): ID da conversa.
        papel (str): Papel a contar ('usuario' ou 'assistente').

    Returns:
        int: Quantidade de mensagens do papel especificado.

    Example:
        >>> msgs_assistente = contar_mensagens_por_papel(conversa_id, "assistente")
        >>> print(f"Assistente enviou {msgs_assistente} mensagens")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM mensagens
                WHERE conversa_id = ? AND papel = ?
            """, (conversa_id, papel))

            resultado = cursor.fetchone()
            return resultado["total"] if resultado else 0

    except sqlite3.Error as e:
        print(f"[ERRO] Erro ao contar mensagens por papel: {e}")
        return 0


if __name__ == "__main__":
    print("=" * 60)
    print("=== TESTES DO MÓDULO modelos/mensagens.py ===")
    print("=" * 60)

    # Configurar o banco primeiro
    from cx_database.setup import criar_todas_as_tabelas, inserir_dados_iniciais
    from cx_database.models.usuarios import criar_usuario, buscar_usuario_por_email
    from cx_database.models.conversas import criar_conversa

    criar_todas_as_tabelas()
    inserir_dados_iniciais()

    # Criar usuário e conversa de teste
    print("\n[PREPARAÇÃO] Criando usuário e conversa de teste...")
    usuario_teste = criar_usuario(
        nome="Usuario Teste Mensagens",
        email="teste.mensagens@email.com",
        senha="Senha1234"
    )
    if not usuario_teste:
        usuario_teste = buscar_usuario_por_email("teste.mensagens@email.com")
    usuario_id = usuario_teste["id"]
    print(f"  Usuário: {usuario_id}")

    conversa_teste = criar_conversa(usuario_id, titulo="Conversa de Teste")
    conversa_id = conversa_teste["id"]
    print(f"  Conversa: {conversa_id}")

    print("\n[TESTE 1] Criar mensagem do usuário:")
    msg1 = criar_mensagem(conversa_id, "usuario", "Olá! Preciso de ajuda com meu projeto.")
    if msg1:
        print(f"  Mensagem criada: {msg1['conteudo'][:40]}...")
        print(f"  Papel: {msg1['papel']}")
    else:
        print("  Falha ao criar mensagem")

    print("\n[TESTE 2] Criar mensagem do assistente:")
    msg2 = criar_mensagem(conversa_id, "assistente", "Claro! Estou aqui para ajudar. Me conte mais sobre seu projeto.")
    if msg2:
        print(f"  Resposta criada: {msg2['conteudo'][:40]}...")

    print("\n[TESTE 3] Criar mais mensagens:")
    msg3 = criar_mensagem(conversa_id, "usuario", "Estou criando um SaaS de consultoria.")
    msg4 = criar_mensagem(conversa_id, "assistente", "Excelente! Vamos estruturar isso juntos.")
    print(f"  Mensagem 3: {'Criada' if msg3 else 'Falha'}")
    print(f"  Mensagem 4: {'Criada' if msg4 else 'Falha'}")

    print("\n[TESTE 4] Buscar mensagem por ID:")
    if msg1:
        msg_busca = buscar_mensagem_por_id(msg1['id'])
        if msg_busca:
            print(f"  Encontrada: {msg_busca['conteudo'][:40]}...")

    print("\n[TESTE 5] Listar todas as mensagens da conversa:")
    mensagens = listar_mensagens_por_conversa(conversa_id)
    print(f"  Total de mensagens: {len(mensagens)}")
    for m in mensagens:
        emoji = "👤" if m['papel'] == 'usuario' else "🤖"
        print(f"    {emoji} {m['papel']}: {m['conteudo'][:50]}...")

    print("\n[TESTE 6] Contar mensagens por papel:")
    count_usuario = contar_mensagens_por_papel(conversa_id, "usuario")
    count_assistente = contar_mensagens_por_papel(conversa_id, "assistente")
    print(f"  Mensagens do usuário: {count_usuario}")
    print(f"  Mensagens do assistente: {count_assistente}")

    print("\n[TESTE 7] Contar total de mensagens do usuário:")
    total_usuario = contar_mensagens_por_usuario(usuario_id)
    print(f"  Total geral do usuário: {total_usuario}")

    print("\n[TESTE 8] Atualizar mensagem:")
    if msg1:
        atualizada = atualizar_mensagem(msg1['id'], "Olá! Preciso de ajuda com meu startup.")
        if atualizada:
            print(f"  Conteúdo atualizado: {atualizada['conteudo'][:40]}...")

    print("\n[TESTE 9] Deletar mensagem:")
    if msg4:
        sucesso = deletar_mensagem(msg4['id'])
        print(f"  Mensagem deletada: {sucesso}")

        # Verificar se foi removida
        msg_verificacao = buscar_mensagem_por_id(msg4['id'])
        print(f"  Mensagem ainda existe: {msg_verificacao is not None} (esperado: False)")

    print("\n[TESTE 10] Tentar criar mensagem com papel inválido:")
    msg_invalida = criar_mensagem(conversa_id, "admin", "Mensagem inválida")
    print(f"  Resultado: {msg_invalida is None} (esperado: True)")

    print("\n[TESTE 11] Listar mensagens paginadas:")
    # Criar mais mensagens para testar paginação
    for i in range(10):
        criar_mensagem(conversa_id, "usuario", f"Mensagem de teste {i}")
        criar_mensagem(conversa_id, "assistente", f"Resposta {i}")

    pag1 = listar_mensagens_paginadas(conversa_id, limite=5, offset=0)
    pag2 = listar_mensagens_paginadas(conversa_id, limite=5, offset=5)
    print(f"  Página 1 (5 msgs): {len(pag1)} mensagens")
    print(f"  Página 2 (5 msgs): {len(pag2)} mensagens")

    print("\n" + "=" * 60)
    print("Todos os testes do mensagens.py foram executados!")
    print("=" * 60)
