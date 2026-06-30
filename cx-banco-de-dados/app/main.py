from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .api.v1 import auth, users, subscriptions, tokens, sync
from .config import get_settings
import uvicorn
from datetime import datetime

settings = get_settings()

# Cria tabelas (em produção, use Alembic migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CxIA Database API",
    description="API completa para o CxIA - Banco de Dados e Autenticação",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
origins = settings.ALLOWED_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(tokens.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "CxIA Database API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
