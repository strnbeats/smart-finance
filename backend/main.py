from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from backend.analytics import get_financial_summary
from backend.database import SessionLocal, init_db
from backend.importers.sber_import import parse_sber_pdf
from backend.models import Transaction
from backend.schemas import (
    TransactionCreate,
    TransactionType,
    TransactionUpdate,
)


MAX_PDF_SIZE = 10 * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Smart Finance API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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
def get_transactions(
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    type: TransactionType | None = None,
):
    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=400,
            detail="Начальная дата не может быть позже конечной",
        )

    with SessionLocal() as session:
        query = select(Transaction)

        if start_date is not None:
            query = query.where(Transaction.date >= start_date)

        if end_date is not None:
            query = query.where(Transaction.date <= end_date)

        if category is not None:
            query = query.where(Transaction.category == category)

        if type is not None:
            query = query.where(Transaction.type == type)

        transactions = session.scalars(
            query.order_by(
                Transaction.date.desc(),
                Transaction.id.desc(),
            )
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


@app.post("/imports/sber/pdf")
async def preview_sber_pdf(file: UploadFile = File(...)):
    if not file.filename or Path(file.filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Загрузи файл с расширением .pdf",
        )

    try:
        content = await file.read(MAX_PDF_SIZE + 1)

        if len(content) > MAX_PDF_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Размер PDF не должен превышать 10 МБ",
            )

        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "uploaded.pdf"
            pdf_path.write_bytes(content)

            transaction = parse_sber_pdf(pdf_path)

        return {
            "saved": False,
            "message": (
                "Операция распознана. "
                "Проверь данные перед сохранением."
            ),
            "transaction": {
                "date": transaction["date"].isoformat(),
                "amount": transaction["amount"],
                "type": transaction["type"].value,
                "category": transaction["category"],
                "description": transaction["description"],
            },
        }

    except HTTPException:
        raise

    except (ValueError, OSError) as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    finally:
        await file.close()
