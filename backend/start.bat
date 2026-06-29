@echo off
echo ============================================
echo   CxIA Backend - Iniciando servidor...
echo ============================================
echo.

cd /d %~dp0

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python não encontrado! Instale Python 3.8+ primeiro.
    pause
    exit /b 1
)

REM Instalar dependências
echo [INFO] Instalando dependências...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependências!
    pause
    exit /b 1
)

REM Criar arquivo .env se não existir
if not exist .env (
    echo [INFO] Criando arquivo .env padrão...
    echo JWT_SECRET=sua_chave_secreta_muito_longa_aqui_troque_isso_em_producao_123456 > .env
    echo DATABASE_PATH=./data/cxia.db >> .env
    echo ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000 >> .env
    echo PORT=8000 >> .env
)

echo.
echo [INFO] Iniciando servidor FastAPI na porta 8000...
echo [INFO] Pressione Ctrl+C para parar
echo.

python main.py

pause
