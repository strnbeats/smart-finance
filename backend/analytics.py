from collections import defaultdict
from datetime import date

from sqlalchemy import select
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


def get_recommendation_context(
    session: Session,
    start_date: date,
    end_date: date,
) -> dict:
    """Подготовить фактические показатели расходов для Recommendation Agent."""
    transactions = session.scalars(
        select(Transaction).where(
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.type == TransactionType.EXPENSE,
        )
    ).all()

    total_expenses = sum(transaction.amount for transaction in transactions)

    category_stats = defaultdict(
        lambda: {"amount": 0, "transaction_count": 0}
    )

    description_stats = {}

    for transaction in transactions:
        category_stat = category_stats[transaction.category]
        category_stat["amount"] += transaction.amount
        category_stat["transaction_count"] += 1

        description = transaction.description.strip()
        if not description:
            continue

        normalized_description = description.casefold()

        if normalized_description not in description_stats:
            description_stats[normalized_description] = {
                "description": description,
                "amount": 0,
                "transaction_count": 0,
                "categories": set(),
            }

        description_stat = description_stats[normalized_description]
        description_stat["amount"] += transaction.amount
        description_stat["transaction_count"] += 1
        description_stat["categories"].add(transaction.category)

    categories = [
        {
            "category": category,
            "amount": stats["amount"],
            "transaction_count": stats["transaction_count"],
            "share_percent": (
                round(stats["amount"] / total_expenses * 100, 1)
                if total_expenses > 0
                else 0
            ),
        }
        for category, stats in category_stats.items()
    ]
    categories.sort(key=lambda item: item["amount"], reverse=True)

    largest_expenses = sorted(
        transactions,
        key=lambda transaction: (transaction.amount, transaction.date),
        reverse=True,
    )[:5]

    repeated_operations = [
        {
            "description": stats["description"],
            "total_amount": stats["amount"],
            "transaction_count": stats["transaction_count"],
            "categories": sorted(stats["categories"]),
        }
        for stats in description_stats.values()
        if stats["transaction_count"] >= 2
    ]
    repeated_operations.sort(
        key=lambda item: item["total_amount"],
        reverse=True,
    )

    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "total_expenses": total_expenses,
        "expense_transactions_count": len(transactions),
        "categories": categories,
        "largest_expenses": [
            {
                "date": transaction.date.isoformat(),
                "amount": transaction.amount,
                "category": transaction.category,
                "description": transaction.description,
                "mcc": transaction.mcc,
            }
            for transaction in largest_expenses
        ],
        "repeated_operations": repeated_operations,
    }
