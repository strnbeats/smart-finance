from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_create_transaction():
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


def test_reject_zero_amount():
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


def test_transaction_not_found():
    response = client.get("/transactions/999999")

    assert response.status_code == 404
