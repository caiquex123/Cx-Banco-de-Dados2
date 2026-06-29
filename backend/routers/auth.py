"""
Rota de autenticação para o backend CxIA.

Endpoints: POST /auth/registro, POST /auth/login, GET /auth/me
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional

from schemas import RegistroInput, LoginInput, AuthResponse, UsuarioResponse
from services.auth_service import registrar_usuario, login_usuario, buscar_usuario_por_id, criar_usuario_guest
from utils.jwt_utils import verificar_token

router = APIRouter(prefix="/auth", tags=["Autenticação"])


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Dependência para obter usuário atual a partir do token JWT.
    
    Args:
        authorization: Header Authorization com Bearer token.
        
    Returns:
        dict: Payload do token com user_id e email.
        
    Raises:
        HTTPException 401: Se token ausente ou inválido.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Token de autorização não fornecido")
    
    # Extrair token do formato "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Formato de autorização inválido")
    
    token = parts[1]
    payload = verificar_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    
    return payload


@router.post("/registro", response_model=AuthResponse)
async def registro(dados: RegistroInput):
    """
    Registra um novo usuário no sistema.
    
    Args:
        dados: Nome, email e senha do usuário.
        
    Returns:
        AuthResponse: Dados do usuário com token de sessão.
        
    Raises:
        HTTPException 400: Se email já cadastrado.
    """
    resultado = registrar_usuario(dados.nome, dados.email, dados.senha)
    
    if not resultado:
        raise HTTPException(status_code=400, detail="Email já cadastrado ou erro ao registrar")
    
    return AuthResponse(**resultado)


@router.post("/login", response_model=AuthResponse)
async def login(dados: LoginInput):
    """
    Realiza login de usuário existente.
    
    Args:
        dados: Email e senha do usuário.
        
    Returns:
        AuthResponse: Dados do usuário com token de sessão.
        
    Raises:
        HTTPException 401: Se credenciais inválidas.
    """
    resultado = login_usuario(dados.email, dados.senha)
    
    if not resultado:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    return AuthResponse(**resultado)


@router.post("/guest", response_model=AuthResponse)
async def login_guest():
    """
    Cria um usuário convidado (guest) temporário.
    
    Returns:
        AuthResponse: Dados do usuário guest com token.
    """
    resultado = criar_usuario_guest()
    
    if not resultado:
        raise HTTPException(status_code=500, detail="Erro ao criar usuário guest")
    
    return AuthResponse(**resultado)


@router.get("/me", response_model=UsuarioResponse)
async def obter_usuario_atual(current_user: dict = Depends(get_current_user)):
    """
    Obtém dados do usuário atualmente logado.
    
    Args:
        current_user: Usuário extraído do token JWT.
        
    Returns:
        UsuarioResponse: Dados públicos do usuário.
        
    Raises:
        HTTPException 404: Se usuário não encontrado.
    """
    usuario = buscar_usuario_por_id(current_user["user_id"])
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return UsuarioResponse(**usuario)
