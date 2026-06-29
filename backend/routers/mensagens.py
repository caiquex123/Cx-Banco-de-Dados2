"""
Rota de gerenciamento de mensagens para o backend CxIA.

Endpoints: GET /mensagens/{conversa_id}, POST /mensagens, DELETE /mensagens/{id}
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from schemas import CriarMensagemInput, MensagemResponse, ListarMensagensResponse
from routers.auth import get_current_user
from database import get_connection
from utils.helpers import gerar_id, agora

router = APIRouter(prefix="/mensagens", tags=["Mensagens"])


@router.get("/{conversa_id}", response_model=ListarMensagensResponse)
async def listar_mensagens(
    conversa_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Lista todas as mensagens de uma conversa específica.
    
    Args:
        conversa_id: ID da conversa.
        current_user: Usuário autenticado.
        
    Returns:
        ListarMensagensResponse: Lista de mensagens ordenadas por criado_em ASC.
        
    Raises:
        HTTPException 404: Se conversa não pertence ao usuário.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar se conversa pertence ao usuário
            cursor.execute("SELECT id FROM conversas WHERE id = ? AND user_id = ?", (conversa_id, current_user["user_id"]))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Conversa não encontrada")
            
            cursor.execute("""
                SELECT id, conversa_id, role, content, thinking_time, criado_em
                FROM mensagens
                WHERE conversa_id = ?
                ORDER BY criado_em ASC
            """, (conversa_id,))
            
            mensagens = [dict(row) for row in cursor.fetchall()]
            return ListarMensagensResponse(mensagens=mensagens)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRO] Erro ao listar mensagens: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar mensagens")


@router.post("", response_model=MensagemResponse)
async def criar_mensagem(
    dados: CriarMensagemInput,
    current_user: dict = Depends(get_current_user)
):
    """
    Cria uma nova mensagem em uma conversa.
    
    Args:
        dados: Dados da mensagem (conversa_id, role, content, thinking_time).
        current_user: Usuário autenticado.
        
    Returns:
        MensagemResponse: Mensagem criada.
        
    Raises:
        HTTPException 404: Se conversa não encontrada ou não pertence ao usuário.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar se conversa existe e pertence ao usuário
            cursor.execute("SELECT id FROM conversas WHERE id = ? AND user_id = ?", (dados.conversa_id, current_user["user_id"]))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Conversa não encontrada")
            
            mensagem_id = gerar_id()
            timestamp = agora()
            
            # Criar mensagem
            cursor.execute("""
                INSERT INTO mensagens (id, conversa_id, role, content, thinking_time, criado_em)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (mensagem_id, dados.conversa_id, dados.role, dados.content, dados.thinking_time, timestamp))
            
            # Atualizar atualizado_em da conversa
            cursor.execute("""
                UPDATE conversas SET atualizado_em = ? WHERE id = ?
            """, (timestamp, dados.conversa_id))
            
            conn.commit()
            
            return MensagemResponse(
                id=mensagem_id,
                conversa_id=dados.conversa_id,
                role=dados.role,
                content=dados.content,
                thinking_time=dados.thinking_time,
                criado_em=timestamp
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRO] Erro ao criar mensagem: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar mensagem")


@router.delete("/{mensagem_id}")
async def deletar_mensagem(
    mensagem_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Deleta uma mensagem específica.
    
    Args:
        mensagem_id: ID da mensagem.
        current_user: Usuário autenticado.
        
    Raises:
        HTTPException 404: Se mensagem não encontrada.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar se mensagem existe e a conversa pertence ao usuário
            cursor.execute("""
                SELECT m.id FROM mensagens m
                JOIN conversas c ON m.conversa_id = c.id
                WHERE m.id = ? AND c.user_id = ?
            """, (mensagem_id, current_user["user_id"]))
            
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Mensagem não encontrada")
            
            cursor.execute("DELETE FROM mensagens WHERE id = ?", (mensagem_id,))
            conn.commit()
            
            return {"mensagem": "Mensagem deletada com sucesso"}
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRO] Erro ao deletar mensagem: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar mensagem")
