"""
Modelos Pydantic para validação de dados nas rotas da API.

Define schemas para requisições e respostas.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ==================== AUTH ====================

class RegistroInput(BaseModel):
    """Dados para registro de novo usuário."""
    nome: str = Field(..., min_length=1, max_length=100)
    email: str
    senha: str = Field(..., min_length=6)


class LoginInput(BaseModel):
    """Dados para login de usuário."""
    email: str
    senha: str


class AuthResponse(BaseModel):
    """Resposta de autenticação bem-sucedida."""
    user_id: str
    nome: str
    email: str
    token: str
    expires_at: str


# ==================== USUÁRIOS ====================

class UsuarioResponse(BaseModel):
    """Dados públicos do usuário."""
    id: str
    nome: str
    email: str
    photo_url: Optional[str] = None
    provider: str = "email"
    is_guest: bool = False
    criado_em: str
    atualizado_em: str


class UsuarioUpdateInput(BaseModel):
    """Dados para atualização do perfil do usuário."""
    nome: Optional[str] = None
    photo_url: Optional[str] = None


# ==================== CONVERSAS ====================

class CriarConversaInput(BaseModel):
    """Dados para criar nova conversa."""
    titulo: str = Field(default="Nova conversa", max_length=200)


class AtualizarConversaInput(BaseModel):
    """Dados para atualizar conversa existente."""
    titulo: Optional[str] = Field(None, max_length=200)
    is_private: Optional[bool] = None


class ConversaResponse(BaseModel):
    """Resposta com dados de uma conversa."""
    id: str
    user_id: str
    titulo: str
    is_private: bool
    criado_em: str
    atualizado_em: str


class ListarConversasResponse(BaseModel):
    """Resposta com lista de conversas."""
    conversas: List[ConversaResponse]


# ==================== MENSAGENS ====================

class CriarMensagemInput(BaseModel):
    """Dados para criar nova mensagem."""
    conversa_id: str
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    thinking_time: Optional[float] = None


class MensagemResponse(BaseModel):
    """Resposta com dados de uma mensagem."""
    id: str
    conversa_id: str
    role: str
    content: str
    thinking_time: Optional[float] = None
    criado_em: str


class ListarMensagensResponse(BaseModel):
    """Resposta com lista de mensagens."""
    mensagens: List[MensagemResponse]


# ==================== TOKENS ====================

class TokenSaldoResponse(BaseModel):
    """Resposta com saldo de tokens do usuário."""
    tokens_usados: int
    limite_tokens: int
    tokens_restantes: int
    janela_inicio: str
    plano: str


class ConsumirTokensInput(BaseModel):
    """Dados para consumir tokens."""
    amount: int = Field(..., gt=0)
    descricao: str = Field(default="Uso de tokens")


class ConsumoResult(BaseModel):
    """Resultado da tentativa de consumo de tokens."""
    allowed: bool
    tokens_restantes: int
    reset_in_ms: Optional[int] = None
    mensagem: Optional[str] = None


class UpgradePlanoInput(BaseModel):
    """Dados para upgrade de plano."""
    novo_plano: str = Field(..., pattern="^(free|pro)$")


# ==================== HEALTH CHECK ====================

class HealthResponse(BaseModel):
    """Resposta do health check."""
    status: str
    version: str
