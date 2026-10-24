from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, HTTPException
from sqlalchemy import select

from backend.analytics import get_financial_summary
from backend.database import SessionLocal, init_db
from backend.models import Transaction
from backend.schemas import TransactionCreate, TransactionUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Smart Finance API",
    lifespan=lifespan,
)


def transaction_to_dict(transaction: Transaction):
    return {
        "id": transaction.id,
        "date": transaction.date.isoformat(),
        "amount": transaction.amount,
        "type": transaction.type.value,
        "category": transaction.category,
        "description": transaction.description,
    }


@app.get("/")
def read_root():
    return {
        "message": "Smart Finance API работает",
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/transactions", status_code=201)
def create_transaction(transaction: TransactionCreate):
    with SessionLocal() as session:
        new_transaction = Transaction(**transaction.model_dump())
        session.add(new_transaction)
        session.commit()
        session.refresh(new_transaction)

        return transaction_to_dict(new_transaction)


@app.get("/transactions")
def get_transactions():
    with SessionLocal() as session:
        transactions = session.scalars(
            select(Transaction).order_by(Transaction.id)
        ).all()

        return [
            transaction_to_dict(transaction)
            for transaction in transactions
        ]


@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: int):
    with SessionLocal() as session:
        transaction = session.get(Transaction, transaction_id)

        if transaction is None:
            raise HTTPException(
                status_code=404,
                detail="Транзакция не найдена",
            )

        return transaction_to_dict(transaction)


@app.put("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    updated_data: TransactionUpdate,
):
    with SessionLocal() as session:
        transaction = session.get(Transaction, transaction_id)

        if transaction is None:
            raise HTTPException(
                status_code=404,
                detail="Транзакция не найдена",
            )

        for field, value in updated_data.model_dump().items():
            setattr(transaction, field, value)

        session.commit()
        session.refresh(transaction)

        return transaction_to_dict(transaction)


@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int):
    with SessionLocal() as session:
        transaction = session.get(Transaction, transaction_id)

        if transaction is None:
            raise HTTPException(
                status_code=404,
                detail="Транзакция не найдена",
            )

        session.delete(transaction)
        session.commit()

        return {
            "message": "Транзакция удалена",
            "id": transaction_id,
        }


@app.get("/analytics/summary")
def analytics_summary(
    start_date: date,
    end_date: date,
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Начальная дата не может быть позже конечной",
        )

    with SessionLocal() as session:
        return get_financial_summary(
            session=session,
            start_date=start_date,
            end_date=end_date,
        )
