from datetime import date

import pytest
from pydantic import ValidationError

from backend.schemas import TransactionCreate, TransactionType


def test_valid_expense():
    transaction = TransactionCreate(
        date=date(2026, 10, 24),
        amount=135000,
        type=TransactionType.EXPENSE,
        category="Еда",
        description="Покупка продуктов",
    )

    assert transaction.amount == 135000
    assert transaction.type == TransactionType.EXPENSE
    assert transaction.category == "Еда"


def test_zero_amount_is_invalid():
    with pytest.raises(ValidationError):
        TransactionCreate(
            date=date(2026, 10, 24),
            amount=0,
            type="expense",
            category="Еда",
        )


def test_empty_category_is_invalid():
    with pytest.raises(ValidationError):
        TransactionCreate(
            date=date(2026, 10, 24),
            amount=10000,
            type="income",
            category="",
        )
