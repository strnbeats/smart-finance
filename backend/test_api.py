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


def test_create_transaction(client):
    response = client.post(
        "/transactions",
        json={
            "date": "2026-10-24",
            "amount": 135000,
            "type": "expense",
            "category": "Еда",
            "description": "Покупка продуктов",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] > 0
    assert data["amount"] == 135000
    assert data["category"] == "Еда"


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
