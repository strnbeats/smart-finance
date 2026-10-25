import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.database as database
import backend.main as main


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_database_path = tmp_path / "test.db"

    test_engine = create_engine(
        f"sqlite:///{test_database_path}",
        connect_args={"check_same_thread": False},
    )

    TestSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(main, "SessionLocal", TestSessionLocal)

    with TestClient(main.app) as test_client:
        yield test_client

    test_engine.dispose()


def create_test_transaction(client):
    return client.post(
        "/transactions",
        json={
            "date": "2026-10-24",
            "amount": 135000,
            "type": "expense",
            "category": "Еда",
            "description": "Покупка продуктов",
        },
    )


def test_create_transaction(client):
    response = create_test_transaction(client)

    assert response.status_code == 201

    data = response.json()

    assert data["id"] > 0
    assert data["amount"] == 135000
    assert data["category"] == "Еда"
    assert data["mcc"] is None


def test_reject_zero_amount(client):
    response = client.post(
        "/transactions",
        json={
            "date": "2026-10-24",
            "amount": 0,
            "type": "expense",
            "category": "Еда",
        },
    )

    assert response.status_code == 422


def test_transaction_not_found(client):
    response = client.get("/transactions/999999")

    assert response.status_code == 404


def test_update_transaction(client):
    created = create_test_transaction(client).json()

    response = client.put(
        f"/transactions/{created['id']}",
        json={
            "date": "2026-10-25",
            "amount": 200000,
            "type": "expense",
            "category": "Транспорт",
            "description": "Такси",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["amount"] == 200000
    assert data["category"] == "Транспорт"
    assert data["description"] == "Такси"
    assert data["mcc"] is None


def test_update_missing_transaction(client):
    response = client.put(
        "/transactions/999999",
        json={
            "date": "2026-10-25",
            "amount": 200000,
            "type": "expense",
            "category": "Транспорт",
            "description": "Такси",
        },
    )

    assert response.status_code == 404


def test_delete_transaction(client):
    created = create_test_transaction(client).json()

    response = client.delete(f"/transactions/{created['id']}")

    assert response.status_code == 200

    get_response = client.get(
        f"/transactions/{created['id']}"
    )

    assert get_response.status_code == 404


def test_delete_missing_transaction(client):
    response = client.delete("/transactions/999999")

    assert response.status_code == 404


def test_create_transaction_with_mcc(client):
    response = client.post(
        "/transactions",
        json={
            "date": "2026-10-25",
            "amount": 15000,
            "type": "expense",
            "category": "Еда",
            "description": "Покупка продуктов",
            "mcc": "5411",
        },
    )

    assert response.status_code == 201
    assert response.json()["mcc"] == "5411"


def test_create_transaction_without_mcc(client):
    response = create_test_transaction(client)

    assert response.status_code == 201
    assert response.json()["mcc"] is None


def test_reject_invalid_mcc(client):
    response = client.post(
        "/transactions",
        json={
            "date": "2026-10-25",
            "amount": 15000,
            "type": "expense",
            "category": "Еда",
            "mcc": "abc",
        },
    )

    assert response.status_code == 422