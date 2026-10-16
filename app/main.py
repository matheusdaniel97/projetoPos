from contextlib import asynccontextmanager
from collections.abc import Iterator

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, select

from app.database import engine
from app.models import Produto, ProdutoBase


def obter_sessao(request: Request) -> Iterator[Session]:
    """Fornece uma sessão ligada ao banco desta aplicação."""
    with Session(request.app.state.database_engine) as session:
        yield session


def criar_aplicacao(database_engine: Engine = engine) -> FastAPI:
    """Cria a API e prepara as tabelas no banco informado ao iniciar."""

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        SQLModel.metadata.create_all(database_engine)
        yield

    app = FastAPI(
        title="API de Produtos",
        description="API REST CRUD para cadastro de produtos.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.database_engine = database_engine

    @app.post("/produtos", response_model=Produto, status_code=status.HTTP_201_CREATED)
    def criar_produto(
        dados: ProdutoBase,
        session: Session = Depends(obter_sessao),
    ) -> Produto:
        """Valida e salva um produto novo."""
        produto = Produto.model_validate(dados)
        session.add(produto)
        session.commit()
        session.refresh(produto)
        return produto

    @app.get("/produtos", response_model=list[Produto])
    def listar_produtos(
        session: Session = Depends(obter_sessao),
    ) -> list[Produto]:
        """Lista os produtos em ordem crescente de ID."""
        return list(session.exec(select(Produto).order_by(Produto.id)).all())

    @app.get("/produtos/{produto_id}", response_model=Produto)
    def consultar_produto(
        produto_id: int,
        session: Session = Depends(obter_sessao),
    ) -> Produto:
        """Busca um produto pelo ID ou responde com 404."""
        produto = session.get(Produto, produto_id)
        if produto is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        return produto

    @app.put("/produtos/{produto_id}", response_model=Produto)
    def atualizar_produto(
        produto_id: int,
        dados: ProdutoBase,
        session: Session = Depends(obter_sessao),
    ) -> Produto:
        """Substitui os campos editáveis de um produto existente."""
        produto = session.get(Produto, produto_id)
        if produto is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")

        produto.nome = dados.nome
        produto.descricao = dados.descricao
        produto.preco = dados.preco
        session.add(produto)
        session.commit()
        session.refresh(produto)
        return produto

    @app.delete(
        "/produtos/{produto_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def excluir_produto(
        produto_id: int,
        session: Session = Depends(obter_sessao),
    ) -> Response:
        """Exclui um produto ou responde com 404 se não existir."""
        produto = session.get(Produto, produto_id)
        if produto is None:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        session.delete(produto)
        session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = criar_aplicacao()
