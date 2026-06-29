"""
CX Database - Sistema de Banco de Dados para CX SaaS

Este pacote fornece um sistema completo de banco de dados SQLite para o SaaS CX,
com módulos organizados por responsabilidade e funções CRUD prontas para uso.

Estrutura do pacote:
    - connection.py: Gerencia conexões com o SQLite
    - setup.py: Configuração inicial do banco (cria tabelas e dados iniciais)
    - models/: Módulos CRUD para cada entidade (usuarios, projetos, conversas, etc.)
    - utils/: Funções auxiliares (helpers e validadores)

Uso básico:
    ```python
    # 1. Configurar o banco pela primeira vez
    from cx_database.setup import criar_todas_as_tabelas, inserir_dados_iniciais
    criar_todas_as_tabelas()
    inserir_dados_iniciais()

    # 2. Usar as funções dos modelos
    from cx_database.models.usuarios import criar_usuario, autenticar_usuario
    from cx_database.models.projetos import criar_projeto

    # Criar usuário
    usuario = criar_usuario("João Silva", "joao@email.com", "Senha123")

    # Autenticar
    usuario_logado = autenticar_usuario("joao@email.com", "Senha123")

    # Criar projeto
    projeto = criar_projeto(usuario["id"], "Meu Projeto")
    ```

Integração com FastAPI:
    ```python
    from fastapi import FastAPI, HTTPException
    from cx_database.models.usuarios import criar_usuario, autenticar_usuario
    from cx_database.utils.validators import validar_email

    app = FastAPI()

    @app.post("/registro")
    def registrar(nome: str, email: str, senha: str):
        if not validar_email(email):
            raise HTTPException(400, "Email inválido")

        usuario = criar_usuario(nome, email, senha)
        if not usuario:
            raise HTTPException(400, "Erro ao criar usuário")

        return {"mensagem": "Usuário criado com sucesso", "usuario": usuario}

    @app.post("/login")
    def login(email: str, senha: str):
        usuario = autenticar_usuario(email, senha)
        if not usuario:
            raise HTTPException(401, "Email ou senha incorretos")

        return {"mensagem": "Login bem-sucedido", "usuario": usuario}
    ```

Variáveis de ambiente:
    DATABASE_PATH: Caminho personalizado para o arquivo .db
                   Padrão: ./cx_database/data/cx_saas.db

Autor: CX SaaS Team
Versão: 1.0.0
"""

from cx_database.connection import get_connection, obter_caminho_db, testar_conexao
from cx_database import utils
from cx_database import models

__version__ = "1.0.0"
__author__ = "CX SaaS Team"

__all__ = [
    "get_connection",
    "obter_caminho_db",
    "testar_conexao",
    "utils",
    "models"
]
