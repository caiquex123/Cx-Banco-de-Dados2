#!/bin/bash
# =============================================================================
# Script de Instalação do CxIA Banco de Dados - Arch Linux
# =============================================================================
# Este script instala e configura todo o sistema CxIA DB no Arch Linux
# Inclui: PostgreSQL, Redis, Python dependencies, Nginx, systemd services
# =============================================================================

set -e  # Para execução em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de log
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCESSO]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[ATENÇÃO]${NC} $1"; }
log_error() { echo -e "${RED}[ERRO]${NC} $1"; }

# Verificar se está rodando como root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Este script deve ser executado como root (use sudo)"
        exit 1
    fi
}

# Atualizar sistema
update_system() {
    log_info "Atualizando pacotes do sistema..."
    pacman -Syu --noconfirm
    log_success "Sistema atualizado"
}

# Instalar dependências do sistema
install_dependencies() {
    log_info "Instalando dependências do sistema..."
    
    # Banco de dados e cache
    pacman -S --noconfirm postgresql postgresql-contrib redis
    
    # Python e ferramentas
    pacman -S --noconfirm python python-pip python-virtualenv python-pipx
    
    # Web server
    pacman -S --noconfirm nginx
    
    # Utilitários
    pacman -S --noconfirm git curl wget nano htop net-tools
    
    log_success "Dependências instaladas"
}

# Configurar PostgreSQL
setup_postgresql() {
    log_info "Configurando PostgreSQL..."
    
    # Inicializar cluster do PostgreSQL
    if [ ! -d "/var/lib/postgres/data" ]; then
        sudo -i -u postgres initdb -D /var/lib/postgres/data
    fi
    
    # Iniciar serviço
    systemctl enable postgresql
    systemctl start postgresql
    
    # Criar banco de dados e usuário
    sudo -i -u postgres psql -c "CREATE DATABASE cxia_db;" || true
    sudo -i -u postgres psql -c "CREATE USER cxia_user WITH PASSWORD 'cxia_secure_password_2024';" || true
    sudo -i -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cxia_db TO cxia_user;" || true
    
    log_success "PostgreSQL configurado"
}

# Configurar Redis
setup_redis() {
    log_info "Configurando Redis..."
    
    systemctl enable redis
    systemctl start redis
    
    log_success "Redis configurado"
}

# Configurar ambiente Python
setup_python_env() {
    log_info "Configurando ambiente Python..."
    
    cd /workspace/cx-banco-de-dados
    
    # Criar virtualenv
    python -m venv venv
    
    # Ativar e instalar dependências
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_success "Ambiente Python configurado"
}

# Configurar variáveis de ambiente
setup_env() {
    log_info "Configurando variáveis de ambiente..."
    
    cd /workspace/cx-banco-de-dados
    
    # Gerar chave secreta
    SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    API_KEY_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Criar arquivo .env
    cat > .env << EOF
# Database
DATABASE_URL=postgresql://cxia_user:cxia_secure_password_2024@localhost:5432/cxia_db

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_KEY_SECRET=${API_KEY_SECRET}

# Stripe (preencher com seus dados)
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,https://seusite.com

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False
EOF
    
    log_success "Variáveis de ambiente configuradas"
}

# Criar migrations do Alembic
setup_migrations() {
    log_info "Configurando migrations do Alembic..."
    
    cd /workspace/cx-banco-de-dados
    source venv/bin/activate
    
    # Inicializar Alembic se não existir
    if [ ! -d "alembic" ]; then
        alembic init alembic
    fi
    
    # Rodar migrations
    alembic upgrade head
    
    log_success "Migrations configuradas"
}

# Configurar systemd service para o backend
setup_systemd_backend() {
    log_info "Configurando systemd service para o backend..."
    
    cat > /etc/systemd/system/cxia-backend.service << EOF
[Unit]
Description=CxIA Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/workspace/cx-banco-de-dados
Environment="PATH=/workspace/cx-banco-de-dados/venv/bin"
ExecStart=/workspace/cx-banco-de-dados/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable cxia-backend
    systemctl start cxia-backend
    
    log_success "Systemd service do backend configurado"
}

# Configurar Nginx
setup_nginx() {
    log_info "Configurando Nginx..."
    
    cat > /etc/nginx/conf.d/cxia.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket endpoint
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Admin Panel
    location /admin {
        alias /workspace/cx-banco-de-dados/admin-panel;
        index index.html;
        try_files $uri $uri/ /admin/index.html;
    }
    
    # API Docs
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /redoc {
        proxy_pass http://localhost:8000/redoc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF
    
    # Testar configuração
    nginx -t
    
    # Habilitar e iniciar
    systemctl enable nginx
    systemctl start nginx
    
    log_success "Nginx configurado"
}

# Configurar firewall
setup_firewall() {
    log_info "Configurando firewall..."
    
    # Verificar se ufw está instalado
    if command -v ufw &> /dev/null; then
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 22/tcp
        ufw --force enable
        log_success "Firewall configurado"
    else
        log_warning "UFW não instalado. Configure o firewall manualmente."
    fi
}

# Criar script de backup
create_backup_script() {
    log_info "Criando script de backup..."
    
    mkdir -p /opt/cxia/backups
    
    cat > /opt/cxia/backups/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/cxia/backups"

# Backup do PostgreSQL
pg_dump -U cxia_user -h localhost cxia_db > ${BACKUP_DIR}/cxia_db_${DATE}.sql
gzip ${BACKUP_DIR}/cxia_db_${DATE}.sql

# Manter apenas últimos 7 dias
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +7 -delete

echo "Backup realizado: ${BACKUP_DIR}/cxia_db_${DATE}.sql.gz"
EOF
    
    chmod +x /opt/cxia/backups/backup.sh
    
    # Adicionar ao crontab (backup diário às 3am)
    echo "0 3 * * * /opt/cxia/backups/backup.sh" | crontab -
    
    log_success "Script de backup criado"
}

# Mostrar informações finais
show_summary() {
    echo ""
    echo "============================================================================="
    echo -e "${GREEN}INSTALAÇÃO CONCLUÍDA COM SUCESSO!${NC}"
    echo "============================================================================="
    echo ""
    echo -e "${BLUE}Serviços iniciados:${NC}"
    echo "  ✓ PostgreSQL (porta 5432)"
    echo "  ✓ Redis (porta 6379)"
    echo "  ✓ Backend FastAPI (porta 8000)"
    echo "  ✓ Nginx (porta 80)"
    echo ""
    echo -e "${BLUE}Acessos:${NC}"
    echo "  • API:           http://localhost/api/"
    echo "  • Swagger Docs:  http://localhost/docs"
    echo "  • ReDoc:         http://localhost/redoc"
    echo "  • Admin Panel:   http://localhost/admin"
    echo ""
    echo -e "${BLUE}Comandos úteis:${NC}"
    echo "  • Ver logs do backend:  journalctl -u cxia-backend -f"
    echo "  • Reiniciar backend:    systemctl restart cxia-backend"
    echo "  • Parar backend:        systemctl stop cxia-backend"
    echo "  • Status dos serviços:  systemctl status cxia-backend postgresql redis nginx"
    echo ""
    echo -e "${YELLOW}Próximos passos:${NC}"
    echo "  1. Configure suas chaves do Stripe no arquivo .env"
    echo "  2. Registre um usuário via API (/api/v1/auth/register)"
    echo "  3. Guarde a API key retornada"
    echo "  4. Para produção, configure SSL com Let's Encrypt"
    echo ""
    echo "============================================================================="
}

# Executar instalação
main() {
    echo ""
    echo "============================================================================="
    echo -e "${BLUE}CxIA Banco de Dados - Instalação no Arch Linux${NC}"
    echo "============================================================================="
    echo ""
    
    check_root
    
    log_warning "Este script irá instalar e configurar todo o sistema CxIA DB."
    log_warning "Isso pode levar alguns minutos. Deseja continuar? (s/n)"
    read -r response
    
    if [[ ! "$response" =~ ^([sS][iI][mM]|[sS])$ ]]; then
        log_info "Instalação cancelada"
        exit 0
    fi
    
    update_system
    install_dependencies
    setup_postgresql
    setup_redis
    setup_python_env
    setup_env
    setup_migrations
    setup_systemd_backend
    setup_nginx
    setup_firewall
    create_backup_script
    show_summary
}

# Executar main
main "$@"
