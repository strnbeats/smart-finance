from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.database as database
import backend.main as main
from backend.schemas import TransactionType


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


def fake_pdf_transaction(
    description="Яндекс Go",
    category="Без категории",
    mcc=None,
):
    def parse_pdf(pdf_path):
        return {
            "date": date(2026, 10, 24),
            "amount": 3000,
            "type": TransactionType.EXPENSE,
            "category": category,
            "description": description,
            "mcc": mcc,
        }

    return parse_pdf


def upload_test_pdf(client):
    return client.post(
        "/imports/sber/pdf",
        files={
            "file": (
                "statement.pdf",
                b"%PDF-test",
                "application/pdf",
            )
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


def test_sber_pdf_preview_includes_mcc(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "parse_sber_pdf",
        fake_pdf_transaction(
            description="Яндекс Go",
            category="Транспорт",
        ),
    )

    response = upload_test_pdf(client)

    assert response.status_code == 200

    data = response.json()

    assert data["saved"] is False
    assert data["transaction"]["mcc"] is None
    assert data["transaction"]["category"] == "Транспорт"


def test_extract_merchant_key():
    result = main.extract_merchant_key(
        "Яндекс Go (YANDEX*4121*GO MOSCOW RUS)"
    )

    assert result == "яндекс go"


def test_generic_description_is_not_a_merchant():
    assert main.extract_merchant_key("Покупка продуктов") is None


def test_learn_category_rule_when_explicitly_enabled(client):
    response = client.post(
        "/transactions",
        json={
            "date": "2026-10-24",
            "amount": 3000,
            "type": "expense",
            "category": "Транспорт",
            "description": "Яндекс Go (YANDEX*4121*GO MOSCOW RUS)",
            "learn_category_rule": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["category_rule_saved"] is True


def test_category_rule_is_not_learned_without_consent(client):
    response = create_test_transaction(client)

    assert response.status_code == 201
    assert response.json()["category_rule_saved"] is False


def test_generic_description_does_not_create_category_rule(client):
    response = client.post(
        "/transactions",
        json={
            "date": "2026-10-24",
            "amount": 3000,
            "type": "expense",
            "category": "Еда",
            "description": "Покупка продуктов",
            "learn_category_rule": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["category_rule_saved"] is False


def test_learned_category_is_applied_to_next_pdf_preview(
    client,
    monkeypatch,
):
    saved = client.post(
        "/transactions",
        json={
            "date": "2026-10-24",
            "amount": 3000,
            "type": "expense",
            "category": "Транспорт",
            "description": "Яндекс Go (YANDEX*4121*GO MOSCOW RUS)",
            "learn_category_rule": True,
        },
    )

    assert saved.status_code == 201
    assert saved.json()["category_rule_saved"] is True

    monkeypatch.setattr(
        main,
        "parse_sber_pdf",
        fake_pdf_transaction(
            description="Яндекс Go (YANDEX*4121*GO MOSCOW RUS)",
            category="Без категории",
        ),
    )

    response = upload_test_pdf(client)

    assert response.status_code == 200

    data = response.json()

    assert data["category_source"] == "learned_rule"
    assert data["transaction"]["category"] == "Транспорт"


def test_mcc_has_priority_over_learned_category_rule(
    client,
    monkeypatch,
):
    saved = client.post(
        "/transactions",
        json={
            "date": "2026-10-24",
            "amount": 3000,
            "type": "expense",
            "category": "Транспорт",
            "description": "Яндекс Go (YANDEX*4121*GO MOSCOW RUS)",
            "learn_category_rule": True,
        },
    )

    assert saved.status_code == 201

    monkeypatch.setattr(
        main,
        "parse_sber_pdf",
        fake_pdf_transaction(
            description="Яндекс Go (YANDEX*4121*GO MOSCOW RUS)",
            category="Рестораны",
            mcc="5812",
        ),
    )

    response = upload_test_pdf(client)

    assert response.status_code == 200

    data = response.json()

    assert data["category_source"] == "mcc"
    assert data["transaction"]["mcc"] == "5812"
    assert data["transaction"]["category"] == "Рестораны"