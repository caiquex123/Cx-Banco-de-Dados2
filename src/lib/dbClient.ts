/**
 * Cliente HTTP para comunicação com o backend CxIA.
 * 
 * Este arquivo substitui o uso do localStorage para dados persistentes,
 * fazendo chamadas HTTP para a DATABASE_URL configurada no .env.
 * 
 * Uso:
 * - Configure VITE_DATABASE_URL no .env do frontend
 * - Importe as funções necessárias e use no lugar do localStorage
 */

const DATABASE_URL = import.meta.env.VITE_DATABASE_URL || '';

// Tipos TypeScript
export interface User {
  id: string;
  nome: string;
  email: string;
  photo_url?: string;
  provider: string;
  is_guest: boolean;
  criado_em: string;
  atualizado_em: string;
}

export interface AuthResponse {
  user_id: string;
  nome: string;
  email: string;
  token: string;
  expires_at: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  titulo: string;
  is_private: boolean;
  criado_em: string;
  atualizado_em: string;
}

export interface Message {
  id: string;
  conversa_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  thinking_time?: number;
  criado_em: string;
}

export interface TokenUsage {
  tokens_usados: number;
  limite_tokens: number;
  tokens_restantes: number;
  janela_inicio: string;
  plano: string;
}

export interface ConsumoResult {
  allowed: boolean;
  tokens_restantes: number;
  reset_in_ms?: number;
  mensagem?: string;
}

// ==================== FUNÇÕES AUXILIARES ====================

/**
 * Salva token JWT no localStorage (único dado que fica no client).
 */
export function salvarToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('cxia_auth_token', token);
  }
}

/**
 * Obtém token JWT do localStorage.
 */
export function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('cxia_auth_token');
  }
  return null;
}

/**
 * Remove token JWT do localStorage.
 */
export function removerToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('cxia_auth_token');
  }
}

/**
 * Função base para todas as chamadas à API.
 * Adiciona automaticamente o token de autorização se disponível.
 */
async function apiCall(endpoint: string, options: RequestInit = {}): Promise<any> {
  if (!DATABASE_URL) {
    console.error('[CxIA DB] VITE_DATABASE_URL não configurado. Configure no .env');
    throw new Error('DATABASE_URL não configurado');
  }

  const url = `${DATABASE_URL}${endpoint}`;
  const token = getToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers as HeadersInit),
  };

  // Adicionar token de autorização se disponível
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    
    if (response.status === 401) {
      console.warn('[CxIA DB] Token inválido ou expirado');
      removerToken();
      throw new Error('Não autorizado');
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erro HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`[CxIA DB] Erro na chamada ${endpoint}:`, error);
    throw error;
  }
}

// ==================== AUTH ====================

/**
 * Registra um novo usuário no sistema.
 */
export async function registrar(nome: string, email: string, senha: string): Promise<AuthResponse> {
  const data = await apiCall('/auth/registro', {
    method: 'POST',
    body: JSON.stringify({ nome, email, senha }),
  });
  
  // Salvar token automaticamente
  if (data.token) {
    salvarToken(data.token);
  }
  
  return data;
}

/**
 * Realiza login de usuário existente.
 */
export async function login(email: string, senha: string): Promise<AuthResponse> {
  const data = await apiCall('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, senha }),
  });
  
  // Salvar token automaticamente
  if (data.token) {
    salvarToken(data.token);
  }
  
  return data;
}

/**
 * Cria um usuário guest (convidado).
 */
export async function loginGuest(): Promise<AuthResponse> {
  const data = await apiCall('/auth/guest', {
    method: 'POST',
  });
  
  if (data.token) {
    salvarToken(data.token);
  }
  
  return data;
}

/**
 * Realiza logout removendo o token local.
 */
export async function logout(): Promise<void> {
  removerToken();
  // Opcional: chamar endpoint de logout no backend se existir
}

/**
 * Obtém dados do usuário atualmente logado.
 */
export async function getUsuarioAtual(): Promise<User | null> {
  try {
    const data = await apiCall('/auth/me');
    return data;
  } catch (error) {
    return null;
  }
}

// ==================== CONVERSAS ====================

/**
 * Lista todas as conversas do usuário logado.
 */
export async function listarConversas(): Promise<Conversation[]> {
  try {
    const data = await apiCall('/conversas');
    return data.conversas || [];
  } catch (error) {
    console.error('[CxIA DB] Erro ao listar conversas:', error);
    return [];
  }
}

/**
 * Cria uma nova conversa.
 */
export async function criarConversa(titulo: string = 'Nova conversa'): Promise<Conversation> {
  const data = await apiCall('/conversas', {
    method: 'POST',
    body: JSON.stringify({ titulo }),
  });
  return data;
}

/**
 * Atualiza dados de uma conversa existente.
 */
export async function atualizarConversa(
  id: string,
  dados: { titulo?: string; is_private?: boolean }
): Promise<Conversation> {
  const data = await apiCall(`/conversas/${id}`, {
    method: 'PUT',
    body: JSON.stringify(dados),
  });
  return data;
}

/**
 * Deleta uma conversa e todas as suas mensagens.
 */
export async function deletarConversa(id: string): Promise<void> {
  await apiCall(`/conversas/${id}`, {
    method: 'DELETE',
  });
}

// ==================== MENSAGENS ====================

/**
 * Lista todas as mensagens de uma conversa.
 */
export async function listarMensagens(conversaId: string): Promise<Message[]> {
  try {
    const data = await apiCall(`/mensagens/${conversaId}`);
    return data.mensagens || [];
  } catch (error) {
    console.error('[CxIA DB] Erro ao listar mensagens:', error);
    return [];
  }
}

/**
 * Cria uma nova mensagem em uma conversa.
 */
export async function criarMensagem(dados: {
  conversa_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  thinking_time?: number;
}): Promise<Message> {
  const data = await apiCall('/mensagens', {
    method: 'POST',
    body: JSON.stringify(dados),
  });
  return data;
}

/**
 * Deleta uma mensagem específica.
 */
export async function deletarMensagem(id: string): Promise<void> {
  await apiCall(`/mensagens/${id}`, {
    method: 'DELETE',
  });
}

// ==================== TOKENS ====================

/**
 * Obtém saldo atual de tokens do usuário.
 */
export async function getSaldo(): Promise<TokenUsage> {
  const data = await apiCall('/tokens/saldo');
  return data;
}

/**
 * Consome tokens do usuário.
 */
export async function consumirTokens(amount: number, descricao: string = 'Uso de tokens'): Promise<ConsumoResult> {
  const data = await apiCall('/tokens/consumir', {
    method: 'POST',
    body: JSON.stringify({ amount, descricao }),
  });
  return data;
}

/**
 * Faz upgrade do plano do usuário.
 */
export async function upgradePro(novoPlano: 'free' | 'pro' = 'pro'): Promise<void> {
  await apiCall('/tokens/upgrade', {
    method: 'POST',
    body: JSON.stringify({ novo_plano: novoPlano }),
  });
}

// ==================== UTILITÁRIOS ====================

/**
 * Verifica se o backend está online.
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${DATABASE_URL}/health`);
    const data = await response.json();
    return data.status === 'ok';
  } catch (error) {
    console.error('[CxIA DB] Backend offline:', error);
    return false;
  }
}
