import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import create_engine

from app.main import criar_aplicacao


@pytest.fixture
def client():
    """Cria uma aplicação de teste com um banco SQLite somente em memória."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_app = criar_aplicacao(test_engine)
    with TestClient(test_app) as test_client:
        yield test_client


def test_criar_produto(client):
    resposta = client.post(
        "/produtos",
        json={
            "nome": "Caderno",
            "descricao": "Caderno universitário",
            "preco": 19.9,
        },
    )

    assert resposta.status_code == 201
    assert resposta.json() == {
        "id": 1,
        "nome": "Caderno",
        "descricao": "Caderno universitário",
        "preco": 19.9,
    }


def test_criar_produto_sem_descricao(client):
    resposta = client.post("/produtos", json={"nome": "Caneta", "preco": 2.5})

    assert resposta.status_code == 201
    assert resposta.json()["descricao"] is None


@pytest.mark.parametrize(
    "dados",
    [
        {"nome": "", "preco": 10},
        {"nome": "   ", "preco": 10},
        {"nome": "Produto", "preco": 0},
        {"nome": "Produto", "preco": -1},
        {"nome": "Produto"},
    ],
)
def test_criar_produto_com_dados_invalidos(client, dados):
    resposta = client.post("/produtos", json=dados)

    assert resposta.status_code == 422


def test_listar_produtos(client):
    client.post("/produtos", json={"nome": "Produto A", "preco": 10})
    client.post("/produtos", json={"nome": "Produto B", "preco": 20})

    resposta = client.get("/produtos")

    assert resposta.status_code == 200
    assert [produto["nome"] for produto in resposta.json()] == [
        "Produto A",
        "Produto B",
    ]


def test_consultar_produto_existente(client):
    criado = client.post(
        "/produtos",
        json={"nome": "Produto", "preco": 12.5},
    ).json()

    resposta = client.get(f"/produtos/{criado['id']}")

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Produto"


def test_consultar_produto_inexistente_retorna_404(client):
    resposta = client.get("/produtos/999")

    assert resposta.status_code == 404


def test_atualizar_produto_existente(client):
    criado = client.post(
        "/produtos",
        json={"nome": "Antigo", "preco": 10},
    ).json()

    resposta = client.put(
        f"/produtos/{criado['id']}",
        json={"nome": "Novo", "descricao": "Atualizado", "preco": 15},
    )

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Novo"
    assert resposta.json()["descricao"] == "Atualizado"
    assert resposta.json()["preco"] == 15


def test_atualizar_produto_inexistente_retorna_404(client):
    resposta = client.put(
        "/produtos/999",
        json={"nome": "Novo", "preco": 15},
    )

    assert resposta.status_code == 404


def test_atualizar_produto_com_preco_invalido_retorna_422(client):
    criado = client.post(
        "/produtos",
        json={"nome": "Produto", "preco": 10},
    ).json()

    resposta = client.put(
        f"/produtos/{criado['id']}",
        json={"nome": "Produto", "preco": 0},
    )

    assert resposta.status_code == 422


def test_excluir_produto_existente(client):
    criado = client.post(
        "/produtos",
        json={"nome": "Produto", "preco": 10},
    ).json()

    resposta = client.delete(f"/produtos/{criado['id']}")

    assert resposta.status_code == 204
    assert client.get(f"/produtos/{criado['id']}").status_code == 404


def test_excluir_produto_inexistente_retorna_404(client):
    resposta = client.delete("/produtos/999")

    assert resposta.status_code == 404
