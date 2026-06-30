#!/bin/bash
#===============================================================================
# CXIA BANCO DE DADOS - SCRIPT DE INSTALAÇÃO PARA ARCH LINUX
#===============================================================================
# Este script instala e configura todo o sistema CxIA Database no Arch Linux
#===============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}=============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Por favor, execute como root ou use sudo"
        exit 1
    fi
}

#===============================================================================
# MAIN INSTALLATION
#===============================================================================

print_header "CXIA DATABASE - INSTALAÇÃO NO ARCH LINUX"

# Check if running as root
check_root

# Step 1: Update system
print_header "PASSO 1: Atualizando sistema..."
pacman -Syu --noconfirm
print_success "Sistema atualizado"

# Step 2: Install base dependencies
print_header "PASSO 2: Instalando dependências básicas..."
pacman -S --noconfirm python python-pip python-venv postgresql redis git
print_success "Dependências básicas instaladas"

# Step 3: Setup PostgreSQL
print_header "PASSO 3: Configurando PostgreSQL..."
systemctl enable postgresql
systemctl start postgresql

# Create database user and database
sudo -u postgres psql <<EOF
CREATE USER cxia WITH PASSWORD 'cxia_secure_password_2024';
CREATE DATABASE cxia_db OWNER cxia;
GRANT ALL PRIVILEGES ON DATABASE cxia_db TO cxia;
EOF
print_success "PostgreSQL configurado"

# Step 4: Setup Redis
print_header "PASSO 4: Configurando Redis..."
systemctl enable redis
systemctl start redis
print_success "Redis configurado"

# Step 5: Create application directory
print_header "PASSO 5: Criando diretório da aplicação..."
APP_DIR="/opt/cxia"
mkdir -p $APP_DIR
cd $APP_DIR
print_success "Diretório criado: $APP_DIR"

# Step 6: Clone or copy application
print_header "PASSO 6: Configurando aplicação..."
if [ -d "/workspace/cx-banco-de-dados" ]; then
    cp -r /workspace/cx-banco-de-dados/* $APP_DIR/
    print_success "Aplicação copiada do workspace"
else
    print_warning "Diretório workspace não encontrado. Clone o repositório manualmente."
fi

# Step 7: Create virtual environment
print_header "PASSO 7: Criando ambiente virtual Python..."
python -m venv venv
source venv/bin/activate
print_success "Ambiente virtual criado"

# Step 8: Install Python dependencies
print_header "PASSO 8: Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt
print_success "Dependências Python instaladas"

# Step 9: Create .env file
print_header "PASSO 9: Criando arquivo de configuração..."
cat > .env <<EOF
# Database
DATABASE_URL=postgresql://cxia:cxia_secure_password_2024@localhost:5432/cxia_db

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_KEY_SECRET=$(openssl rand -hex 32)

# Stripe (preencha com suas chaves)
STRIPE_SECRET_KEY=sk_test_YOUR_STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,https://seusite.com

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False
EOF
print_success "Arquivo .env criado"

# Step 10: Run migrations
print_header "PASSO 10: Executando migrações do banco de dados..."
alembic upgrade head
print_success "Migrações executadas"

# Step 11: Create systemd service
print_header "PASSO 11: Criando serviço systemd..."
cat > /etc/systemd/system/cxia-backend.service <<EOF
[Unit]
Description=CxIA Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable cxia-backend
print_success "Serviço systemd criado"

# Step 12: Setup Nginx (optional)
print_header "PASSO 12: Configurando Nginx (opcional)..."
if command -v nginx &> /dev/null; then
    cat > /etc/nginx/conf.d/cxia.conf <<EOF
server {
    listen 80;
    server_name api.cxia.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

server {
    listen 80;
    server_name admin.cxia.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF
    systemctl enable nginx
    systemctl restart nginx
    print_success "Nginx configurado"
else
    print_warning "Nginx não instalado. Pulando configuração."
fi

# Step 13: Setup firewall
print_header "PASSO 13: Configurando firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8000/tcp
    print_success "Firewall configurado"
else
    print_warning "UFW não instalado. Configure o firewall manualmente."
fi

# Step 14: Start services
print_header "PASSO 14: Iniciando serviços..."
systemctl start cxia-backend
print_success "Serviços iniciados"

# Final summary
print_header "INSTALAÇÃO CONCLUÍDA!"
echo ""
echo -e "${GREEN}✓ Backend rodando em:${NC} http://localhost:8000"
echo -e "${GREEN}✓ API Docs:${NC} http://localhost:8000/docs"
echo -e "${GREEN}✓ Admin Panel:${NC} http://localhost:3000 (após iniciar)"
echo ""
echo -e "${YELLOW}Próximos passos:${NC}"
echo "1. Acesse http://localhost:8000/docs"
echo "2. Registre um usuário admin via API"
echo "3. Inicie o admin panel: cd $APP_DIR/admin-panel && python -m http.server 3000"
echo "4. Configure suas chaves do Stripe no arquivo .env"
echo ""
echo -e "${BLUE}Comandos úteis:${NC}"
echo "  systemctl status cxia-backend  # Ver status do serviço"
echo "  journalctl -u cxia-backend -f  # Ver logs em tempo real"
echo "  systemctl restart cxia-backend # Reiniciar serviço"
echo ""

print_success "Instalação concluída com sucesso!"
