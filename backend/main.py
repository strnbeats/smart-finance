from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import select

from backend.database import SessionLocal, init_db
from backend.models import Transaction
from backend.schemas import TransactionCreate


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Smart Finance API",
    lifespan=lifespan,
)


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

        return {
            "id": new_transaction.id,
            **transaction.model_dump(mode="json"),
        }


@app.get("/transactions")
def get_transactions():
    with SessionLocal() as session:
        transactions = session.scalars(
            select(Transaction).order_by(Transaction.id)
        ).all()

        return [
            {
                "id": transaction.id,
                "date": transaction.date.isoformat(),
                "amount": transaction.amount,
                "type": transaction.type.value,
                "category": transaction.category,
                "description": transaction.description,
            }
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

        return {
            "id": transaction.id,
            "date": transaction.date.isoformat(),
            "amount": transaction.amount,
            "type": transaction.type.value,
            "category": transaction.category,
            "description": transaction.description,
        }
