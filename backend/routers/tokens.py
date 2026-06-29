"""
Rota de gerenciamento de tokens para o backend CxIA.

Endpoints: GET /tokens/saldo, POST /tokens/consumir, POST /tokens/upgrade
"""

from fastapi import APIRouter, HTTPException, Depends

from schemas import TokenSaldoResponse, ConsumirTokensInput, ConsumoResult, UpgradePlanoInput
from routers.auth import get_current_user
from services.token_service import get_saldo, consumir_tokens as consumir_tokens_service, upgrade_plano

router = APIRouter(prefix="/tokens", tags=["Tokens"])


@router.get("/saldo", response_model=TokenSaldoResponse)
async def obter_saldo(current_user: dict = Depends(get_current_user)):
    """
    Obtém saldo atual de tokens do usuário logado.
    
    Returns:
        TokenSaldoResponse: Saldo com tokens_usados, limite, restantes, etc.
    """
    saldo = get_saldo(current_user["user_id"])
    
    if not saldo:
        raise HTTPException(status_code=500, detail="Erro ao obter saldo de tokens")
    
    return TokenSaldoResponse(**saldo)


@router.post("/consumir", response_model=ConsumoResult)
async def consumir_tokens(
    dados: ConsumirTokensInput,
    current_user: dict = Depends(get_current_user)
):
    """
    Consome tokens do usuário de forma atômica.
    
    Args:
        dados: amount (quantidade) e descricao do uso.
        current_user: Usuário autenticado.
        
    Returns:
        ConsumoResult: allowed (bool), tokens_restantes, reset_in_ms se aplicável.
    """
    resultado = consumir_tokens_service(
        user_id=current_user["user_id"],
        amount=dados.amount,
        descricao=dados.descricao
    )
    
    return ConsumoResult(**resultado)


@router.post("/upgrade")
async def upgrade_de_plano(
    dados: UpgradePlanoInput,
    current_user: dict = Depends(get_current_user)
):
    """
    Faz upgrade ou downgrade do plano do usuário.
    
    Args:
        dados: novo_plano ('free' ou 'pro').
        current_user: Usuário autenticado.
        
    Returns:
        dict: Mensagem de sucesso.
        
    Raises:
        HTTPException 400: Se plano inválido.
    """
    sucesso = upgrade_plano(current_user["user_id"], dados.novo_plano)
    
    if not sucesso:
        raise HTTPException(status_code=400, detail="Erro ao atualizar plano")
    
    return {"mensagem": f"Plano atualizado para {dados.novo_plano} com sucesso"}
