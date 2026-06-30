# 📚 DOCUMENTAÇÃO COMPLETA - CX BANCO DE DADOS

## 🎯 VISÃO GERAL

Sistema de banco de dados completo, em tempo real, com auto-sincronização para o CxIA.

---

## 📋 ÍNDICE

1. [Arquitetura](#arquitetura)
2. [Instalação](#instalação)
3. [Configuração](#configuração)
4. [API Reference](#api-reference)
5. [Admin Panel](#admin-panel)
6. [Deploy](#deploy)

---

## 🏗️ ARQUITETURA

### Tecnologias

- **Backend:** Python + FastAPI
- **Banco de Dados:** PostgreSQL (prod) / SQLite (dev)
- **ORM:** SQLAlchemy + Alembic
- **Cache:** Redis
- **WebSocket:** Tempo real
- **Autenticação:** JWT + API Keys
- **Pagamentos:** Stripe

### Estrutura do Projeto

```
cx-banco-de-dados/
├── app/
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Configurações
│   ├── database.py             # Conexão DB
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   ├── api/v1/                 # Rotas da API
│   ├── core/                   # Segurança, WebSocket
│   └── services/               # Lógica de negócio
├── admin-panel/
│   └── index.html              # Painel Admin
├── alembic/                    # Migrations
├── requirements.txt
├── .env
└── install-arch.sh             # Script instalação
```

---

## 🚀 INSTALAÇÃO

### Método 1: Script Automático (Arch Linux)

```bash
sudo ./install-arch.sh
```

### Método 2: Manual

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar ambiente
cp .env.example .env
# Edite .env com suas configurações

# 3. Rodar migrações
alembic upgrade head

# 4. Iniciar servidor
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Método 3: Docker

```bash
docker-compose up -d
```

---

## ⚙️ CONFIGURAÇÃO

### Variáveis de Ambiente (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/cxia_db

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=sua-chave-secreta-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_KEY_SECRET=sua-api-key-secret

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# CORS
ALLOWED_ORIGINS=http://localhost:5173,https://seusite.com

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

---

## 🔌 API REFERENCE

### Base URL
```
http://localhost:8000/api/v1
```

### Autenticação

#### Registrar Usuário
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@email.com",
  "password": "senha123",
  "full_name": "Nome Completo"
}

# Response:
{
  "id": 1,
  "email": "user@email.com",
  "api_key": "cxia_abc123...",
  "plan": "free"
}
```

#### Login
```bash
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@email.com&password=senha123

# Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {...}
}
```

### Endpoints Principais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/users` | Listar usuários (admin) |
| GET | `/users/{id}` | Detalhes do usuário |
| PUT | `/users/{id}/plan` | Mudar plano |
| GET | `/tokens/usage` | Uso de tokens |
| GET | `/conversations` | Listar conversas |
| POST | `/sync` | Auto-sync |
| WS | `/ws/{user_id}` | WebSocket |

### Documentação Interativa

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🎛️ ADMIN PANEL

### Acessando

O painel admin está em `admin-panel/index.html`.

Para rodar:
```bash
cd admin-panel
python -m http.server 3000
# Acesse: http://localhost:3000
```

### Funcionalidades

1. **Dashboard**
   - Total de usuários
   - Receita mensal (MRR)
   - Tokens usados em tempo real
   - Gráficos e estatísticas

2. **Gerenciamento de Usuários**
   - Listar todos os usuários
   - Buscar e filtrar
   - Mudar plano
   - Resetar tokens
   - Deletar usuários

3. **Monitoramento de Tokens**
   - Uso em tempo real
   - Top usuários
   - Custos estimados

4. **Assinaturas**
   - Planos ativos
   - Status Stripe
   - Próximas cobranças

5. **Configurações**
   - Modo manutenção
   - Limites de tokens
   - Feature flags
   - Webhooks Stripe

6. **Logs**
   - Visualização de logs
   - Filtros por nível
   - Exportação

---

## 💳 PLANOS

| Plano | Tokens/Dia | Preço |
|-------|------------|-------|
| FREE | 10.000 | Grátis |
| PRO | 50.000 | R$ 29,90/mês |
| MAX | 150.000 | R$ 99,90/mês |

---

## 🔄 AUTO-SYNC

O sistema suporta sincronização automática via WebSocket.

### Exemplo Frontend

```javascript
// Conectar WebSocket
const ws = new WebSocket(`ws://localhost:8000/ws/${userId}?token=${jwt}`);

// Enviar atualização
ws.send(JSON.stringify({
  type: "sync",
  entity: "user_settings",
  changes: { theme: "dark" }
}));

// Receber atualizações
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Sync recebido:", data);
};
```

---

## 📊 MODELOS DE DADOS

### Users
```python
User {
  id: int
  email: str
  hashed_password: str
  plan: enum (free/pro/max)
  tokens_used_today: int
  tokens_limit: int
  api_key: str
  stripe_customer_id: str
  created_at: datetime
}
```

### TokenUsage
```python
TokenUsage {
  id: int
  user_id: int
  input_tokens: int
  output_tokens: int
  total_tokens: int
  cost: float
  model_id: str
  created_at: datetime
}
```

### Conversation
```python
Conversation {
  id: int
  user_id: int
  title: str
  model_used: str
  message_count: int
  total_tokens: int
  created_at: datetime
}
```

---

## 🔐 SEGURANÇA

### JWT Token

```python
# Payload
{
  "sub": "user@email.com",
  "exp": datetime + 30min,
  "iat": datetime,
  "user_id": 123,
  "plan": "pro"
}
```

### API Keys

- Geradas automaticamente no registro
- Hash SHA-256 armazenado no DB
- Use header `X-API-Key` nas requisições

### Rate Limiting

Por plano:
- FREE: 10 req/min
- PRO: 30 req/min
- MAX: 60 req/min

---

## 🚀 DEPLOY

### Produção com PostgreSQL

1. Instale PostgreSQL
2. Crie database e usuário
3. Atualize `DATABASE_URL` no .env
4. Rode migrações: `alembic upgrade head`
5. Inicie com uvicorn/gunicorn

### Systemd Service

```ini
[Unit]
Description=CxIA Backend API
After=network.target

[Service]
WorkingDirectory=/opt/cxia
ExecStart=/opt/cxia/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.cxia.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # WebSocket
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 🧪 TESTES

```bash
# Rodar testes
pytest

# Com coverage
pytest --cov=app
```

---

## 📝 COMANDOS ÚTEIS

### Backend
```bash
# Iniciar servidor
python -m uvicorn app.main:app --reload

# Rodar migrations
alembic upgrade head

# Criar nova migration
alembic revision --autogenerate -m "description"

# Ver logs do DB
sqlite3 cx_ia.db ".log on"
```

### Admin Panel
```bash
# Servir arquivos estáticos
cd admin-panel && python -m http.server 3000
```

### Monitoramento
```bash
# Ver status do serviço
systemctl status cxia-backend

# Logs em tempo real
journalctl -u cxia-backend -f

# Restart
systemctl restart cxia-backend
```

---

## 🔧 TROUBLESHOOTING

### Erro: Database não conecta

```bash
# Verificar PostgreSQL
systemctl status postgresql

# Testar conexão
psql -U cxia -d cxia_db -h localhost
```

### Erro: Redis não disponível

```bash
# Iniciar Redis
systemctl start redis

# Testar conexão
redis-cli ping  # Deve retornar PONG
```

### Erro: Port already in use

```bash
# Matar processo na porta 8000
lsof -ti:8000 | xargs kill -9
```

---

## ✅ CHECKLIST DE IMPLANTAÇÃO

- [ ] Instalar dependências
- [ ] Configurar .env
- [ ] Setup PostgreSQL/Redis
- [ ] Rodar migrations
- [ ] Testar endpoints
- [ ] Configurar Stripe
- [ ] Setup Admin Panel
- [ ] Configurar Nginx
- [ ] SSL/HTTPS
- [ ] Backup automático
- [ ] Monitoramento

---

**Versão:** 1.0.0  
**Última atualização:** 2024
