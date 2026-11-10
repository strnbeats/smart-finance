import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.database as database
import backend.main as main


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_database_path = tmp_path / "analytics_test.db"

    test_engine = create_engine(
        f"sqlite:///{test_database_path}",
        connect_args={"check_same_thread": False},
    )

    test_session_local = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(main, "SessionLocal", test_session_local)

    with TestClient(main.app) as test_client:
        yield test_client

    test_engine.dispose()


def add_transaction(
    client,
    transaction_date,
    amount,
    transaction_type,
    category,
):
    return client.post(
        "/transactions",
        json={
            "date": transaction_date,
            "amount": amount,
            "type": transaction_type,
            "category": category,
            "description": "",
        },
    )


def test_analytics_summary(client):
    add_transaction(
        client, "2026-10-05", 300000, "income", "Зарплата"
    )
    add_transaction(
        client, "2026-10-06", 50000, "expense", "Еда"
    )
    add_transaction(
        client, "2026-10-07", 20000, "expense", "Еда"
    )
    add_transaction(
        client, "2026-10-08", 10000, "expense", "Транспорт"
    )

    response = client.get(
        "/analytics/summary",
        params={
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_income"] == 300000
    assert data["total_expenses"] == 80000
    assert data["balance"] == 220000
    assert data["transactions_count"] == 4
    assert data["expenses_by_category"] == {
        "Еда": 70000,
        "Транспорт": 10000,
    }


def test_analytics_filters_by_date(client):
    add_transaction(
        client, "2026-09-30", 100000, "income", "Зарплата"
    )
    add_transaction(
        client, "2026-10-15", 25000, "expense", "Еда"
    )
    add_transaction(
        client, "2026-11-01", 50000, "expense", "Покупки"
    )

    response = client.get(
        "/analytics/summary",
        params={
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_income"] == 0
    assert data["total_expenses"] == 25000
    assert data["balance"] == -25000
    assert data["transactions_count"] == 1


def test_analytics_rejects_invalid_date_range(client):
    response = client.get(
        "/analytics/summary",
        params={
            "start_date": "2026-10-31",
            "end_date": "2026-10-01",
        },
    )

    assert response.status_code == 400


def test_analytics_empty_period(client):
    response = client.get(
        "/analytics/summary",
        params={
            "start_date": "2026-10-01",
            "end_date": "2026-10-31",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_income"] == 0
    assert data["total_expenses"] == 0
    assert data["balance"] == 0
    assert data["transactions_count"] == 0
    assert data["expenses_by_category"] == {}


def test_recommendation_context(client):
    from datetime import date

    from backend.analytics import get_recommendation_context

    transactions = [
        {
            "date": "2026-10-05",
            "amount": 50000,
            "type": "expense",
            "category": "Еда",
            "description": "Супермаркет",
        },
        {
            "date": "2026-10-07",
            "amount": 30000,
            "type": "expense",
            "category": "Еда",
            "description": "Супермаркет",
        },
        {
            "date": "2026-10-08",
            "amount": 20000,
            "type": "expense",
            "category": "Транспорт",
            "description": "Такси",
        },
        {
            "date": "2026-10-09",
            "amount": 10000,
            "type": "expense",
            "category": "Развлечения",
            "description": "Кино",
        },
        {
            "date": "2026-10-10",
            "amount": 90000,
            "type": "income",
            "category": "Зарплата",
            "description": "Зарплата",
        },
    ]

    for transaction in transactions:
        response = client.post("/transactions", json=transaction)
        assert response.status_code in (200, 201)

    with main.SessionLocal() as session:
        context = get_recommendation_context(
            session,
            date(2026, 10, 1),
            date(2026, 10, 31),
        )

    assert context["total_expenses"] == 110000
    assert context["expense_transactions_count"] == 4

    assert context["categories"] == [
        {
            "category": "Еда",
            "amount": 80000,
            "transaction_count": 2,
            "share_percent": 72.7,
        },
        {
            "category": "Транспорт",
            "amount": 20000,
            "transaction_count": 1,
            "share_percent": 18.2,
        },
        {
            "category": "Развлечения",
            "amount": 10000,
            "transaction_count": 1,
            "share_percent": 9.1,
        },
    ]

    assert context["largest_expenses"][0]["amount"] == 50000
    assert context["largest_expenses"][0]["description"] == "Супермаркет"

    assert context["repeated_operations"] == [
        {
            "description": "Супермаркет",
            "total_amount": 80000,
            "transaction_count": 2,
            "categories": ["Еда"],
        }
    ]


def test_recommendation_context_empty_period(client):
    from datetime import date

    from backend.analytics import get_recommendation_context

    with main.SessionLocal() as session:
        context = get_recommendation_context(
            session,
            date(2026, 10, 1),
            date(2026, 10, 31),
        )

    assert context["total_expenses"] == 0
    assert context["expense_transactions_count"] == 0
    assert context["categories"] == []
    assert context["largest_expenses"] == []
    assert context["repeated_operations"] == []
