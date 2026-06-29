#!/bin/bash

echo "============================================"
echo "  CxIA Backend - Iniciando servidor..."
echo "============================================"
echo ""

# Mudar para diretório do script
cd "$(dirname "$0")"

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python3 não encontrado! Instale Python 3.8+ primeiro."
    exit 1
fi

# Instalar dependências
echo "[INFO] Instalando dependências..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERRO] Falha ao instalar dependências!"
    exit 1
fi

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "[INFO] Criando arquivo .env padrão..."
    cat > .env << EOF
JWT_SECRET=sua_chave_secreta_muito_longa_aqui_troque_isso_em_producao_123456
DATABASE_PATH=./data/cxia.db
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
PORT=8000
EOF
fi

echo ""
echo "[INFO] Iniciando servidor FastAPI na porta 8000..."
echo "[INFO] Pressione Ctrl+C para parar"
echo ""

python3 main.py
