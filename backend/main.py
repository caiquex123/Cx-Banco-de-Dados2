"""
Aplicação principal FastAPI do backend CxIA.

Configura CORS, rotas e middleware de autenticação.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

load_dotenv()

# Importar routers
from routers import auth, conversas, mensagens, tokens
from database import init_db
from schemas import HealthResponse

# Carregar variáveis de ambiente
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
PORT = int(os.getenv("PORT", 8000))

# Criar aplicação FastAPI
app = FastAPI(
    title="CxIA Backend API",
    description="API para gerenciamento de banco de dados local do CxIA",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware global para tratamento de erros
@app.middleware("http")
async def error_handler(request: Request, call_next):
    """Middleware para capturar e logar erros."""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        print(f"[ERRO] Erro não tratado na requisição {request.url}: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Erro interno do servidor"}
        )


# Rota de health check
@app.get("/health", response_model=HealthResponse, tags=["Sistema"])
async def health_check():
    """
    Verifica se o backend está online e saudável.
    
    Returns:
        HealthResponse: Status e versão da API.
    """
    return HealthResponse(status="ok", version="1.0.0")


# Incluir routers
app.include_router(auth.router)
app.include_router(conversas.router)
app.include_router(mensagens.router)
app.include_router(tokens.router)


# Evento de inicialização
@app.on_event("startup")
async def startup_event():
    """Inicializa o banco de dados ao iniciar a aplicação."""
    print("[INFO] Iniciando CxIA Backend...")
    init_db()
    print("[INFO] Banco de dados inicializado com sucesso!")
    print(f"[INFO] Servidor rodando na porta {PORT}")
    print(f"[INFO] Origens CORS permitidas: {', '.join(ALLOWED_ORIGINS)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
