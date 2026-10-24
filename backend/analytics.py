from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models import Transaction
from backend.schemas import TransactionType


def get_financial_summary(
    session: Session,
    start_date: date,
    end_date: date,
):
    transactions = session.scalars(
        select(Transaction).where(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
        )
    ).all()

    income = sum(
        transaction.amount
        for transaction in transactions
        if transaction.type == TransactionType.INCOME
    )

    expenses = sum(
        transaction.amount
        for transaction in transactions
        if transaction.type == TransactionType.EXPENSE
    )

    expenses_by_category = {}

    for transaction in transactions:
        if transaction.type == TransactionType.EXPENSE:
            category = transaction.category

            expenses_by_category[category] = (
                expenses_by_category.get(category, 0)
                + transaction.amount
            )

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_income": income,
        "total_expenses": expenses,
        "balance": income - expenses,
        "expenses_by_category": expenses_by_category,
        "transactions_count": len(transactions),
    }
