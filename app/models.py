from sqlmodel import Field, SQLModel
from pydantic import field_validator


class ProdutoBase(SQLModel):
    nome: str = Field(min_length=1, description="Nome obrigatório do produto")
    descricao: str | None = Field(default=None, description="Descrição opcional")
    preco: float = Field(gt=0, description="Preço maior que zero")

    @field_validator("nome", mode="before")
    @classmethod
    def limpar_nome(cls, valor: str) -> str:
        """Remove espaços externos para que nomes em branco sejam rejeitados."""
        if isinstance(valor, str):
            return valor.strip()
        return valor


class Produto(ProdutoBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
