"""
Rota de gerenciamento de conversas para o backend CxIA.

Endpoints: GET/POST /conversas, GET/PUT/DELETE /conversas/{id}
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List

from schemas import CriarConversaInput, AtualizarConversaInput, ConversaResponse, ListarConversasResponse
from routers.auth import get_current_user
from database import get_connection
from utils.helpers import gerar_id, agora

router = APIRouter(prefix="/conversas", tags=["Conversas"])


@router.get("", response_model=ListarConversasResponse)
async def listar_conversas(current_user: dict = Depends(get_current_user)):
    """
    Lista todas as conversas do usuário logado.
    
    Returns:
        ListarConversasResponse: Lista de conversas ordenadas por mais recente.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, titulo, is_private, criado_em, atualizado_em
                FROM conversas
                WHERE user_id = ?
                ORDER BY atualizado_em DESC
            """, (current_user["user_id"],))
            
            conversas = [dict(row) for row in cursor.fetchall()]
            return ListarConversasResponse(conversas=conversas)
            
    except Exception as e:
        print(f"[ERRO] Erro ao listar conversas: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar conversas")


@router.post("", response_model=ConversaResponse)
async def criar_conversa(
    dados: CriarConversaInput,
    current_user: dict = Depends(get_current_user)
):
    """
    Cria uma nova conversa para o usuário logado.
    
    Args:
        dados: Título da conversa.
        current_user: Usuário autenticado.
        
    Returns:
        ConversaResponse: Conversa criada.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            conversa_id = gerar_id()
            timestamp = agora()
            
            cursor.execute("""
                INSERT INTO conversas (id, user_id, titulo, is_private, criado_em, atualizado_em)
                VALUES (?, ?, ?, 0, ?, ?)
            """, (conversa_id, current_user["user_id"], dados.titulo, timestamp, timestamp))
            
            conn.commit()
            
            return ConversaResponse(
                id=conversa_id,
                user_id=current_user["user_id"],
                titulo=dados.titulo,
                is_private=False,
                criado_em=timestamp,
                atualizado_em=timestamp
            )
            
    except Exception as e:
        print(f"[ERRO] Erro ao criar conversa: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar conversa")


@router.get("/{conversa_id}", response_model=ConversaResponse)
async def obter_conversa(
    conversa_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Obtém detalhes de uma conversa específica.
    
    Args:
        conversa_id: ID da conversa.
        current_user: Usuário autenticado.
        
    Returns:
        ConversaResponse: Dados da conversa.
        
    Raises:
        HTTPException 404: Se conversa não encontrada ou não pertence ao usuário.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, user_id, titulo, is_private, criado_em, atualizado_em
                FROM conversas
                WHERE id = ? AND user_id = ?
            """, (conversa_id, current_user["user_id"]))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Conversa não encontrada")
            
            return ConversaResponse(**dict(row))
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRO] Erro ao obter conversa: {e}")
        raise HTTPException(status_code=500, detail="Erro ao obter conversa")


@router.put("/{conversa_id}", response_model=ConversaResponse)
async def atualizar_conversa(
    conversa_id: str,
    dados: AtualizarConversaInput,
    current_user: dict = Depends(get_current_user)
):
    """
    Atualiza dados de uma conversa existente.
    
    Args:
        conversa_id: ID da conversa.
        dados: Campos a atualizar (titulo, is_private).
        current_user: Usuário autenticado.
        
    Returns:
        ConversaResponse: Conversa atualizada.
        
    Raises:
        HTTPException 404: Se conversa não encontrada.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar se conversa existe e pertence ao usuário
            cursor.execute("SELECT id FROM conversas WHERE id = ? AND user_id = ?", (conversa_id, current_user["user_id"]))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Conversa não encontrada")
            
            campos_update = []
            valores = []
            
            if dados.titulo is not None:
                campos_update.append("titulo = ?")
                valores.append(dados.titulo)
            if dados.is_private is not None:
                campos_update.append("is_private = ?")
                valores.append(1 if dados.is_private else 0)
            
            if campos_update:
                valores.append(agora())
                valores.append(conversa_id)
                
                cursor.execute(f"""
                    UPDATE conversas
                    SET {', '.join(campos_update)}, atualizado_em = ?
                    WHERE id = ?
                """, valores)
                
                conn.commit()
            
            # Retornar conversa atualizada
            cursor.execute("""
                SELECT id, user_id, titulo, is_private, criado_em, atualizado_em
                FROM conversas
                WHERE id = ?
            """, (conversa_id,))
            
            row = cursor.fetchone()
            return ConversaResponse(**dict(row))
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRO] Erro ao atualizar conversa: {e}")
        raise HTTPException(status_code=500, detail="Erro ao atualizar conversa")


@router.delete("/{conversa_id}")
async def deletar_conversa(
    conversa_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Deleta uma conversa e todas as suas mensagens (CASCADE automático).
    
    Args:
        conversa_id: ID da conversa.
        current_user: Usuário autenticado.
        
    Raises:
        HTTPException 404: Se conversa não encontrada.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Verificar se conversa existe e pertence ao usuário
            cursor.execute("SELECT id FROM conversas WHERE id = ? AND user_id = ?", (conversa_id, current_user["user_id"]))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Conversa não encontrada")
            
            cursor.execute("DELETE FROM conversas WHERE id = ?", (conversa_id,))
            conn.commit()
            
            return {"mensagem": "Conversa deletada com sucesso"}
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERRO] Erro ao deletar conversa: {e}")
        raise HTTPException(status_code=500, detail="Erro ao deletar conversa")
