import re
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
from backend.models import CategoryRule, Transaction
from backend.schemas import (
    TransactionCreate,
    TransactionType,
    TransactionUpdate,
)

from backend.expense_graph import run_expense_graph


MAX_PDF_SIZE = 10 * 1024 * 1024

GENERIC_DESCRIPTIONS = {
    "покупка",
    "покупка продуктов",
    "оплата",
    "оплата товаров и услуг",
    "перевод",
    "пополнение",
    "снятие наличных",
    "без категории",
    "неизвестный магазин",
}


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
        "mcc": transaction.mcc,
    }


def extract_merchant_key(description: str) -> str | None:
    text = " ".join(description.split()).strip()

    if not text:
        return None

    # Например:
    # "Яндекс Go (YANDEX*4121*GO MOSCOW RUS)"
    # превратится в "яндекс go".
    merchant = text.split("(", maxsplit=1)[0].strip()
    merchant = merchant.strip(" -–—:,.").lower().replace("ё", "е")
    merchant = re.sub(r"\s+", " ", merchant)

    if merchant in GENERIC_DESCRIPTIONS:
        return None

    if len(merchant) < 3:
        return None

    return merchant[:200]


def find_category_rule(session, merchant_key: str) -> CategoryRule | None:
    return session.scalar(
        select(CategoryRule).where(
            CategoryRule.merchant_key == merchant_key
        )
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
    data = transaction.model_dump()
    learn_category_rule = data.pop("learn_category_rule", False)

    with SessionLocal() as session:
        new_transaction = Transaction(**data)
        session.add(new_transaction)

        category_rule_saved = False

        if learn_category_rule:
            merchant_key = extract_merchant_key(
                new_transaction.description
            )

            if merchant_key is not None:
                rule = find_category_rule(session, merchant_key)

                if rule is None:
                    rule = CategoryRule(
                        merchant_key=merchant_key,
                        category=new_transaction.category,
                    )
                    session.add(rule)
                else:
                    rule.category = new_transaction.category

                category_rule_saved = True

        # Сохраняем транзакцию и правило одним commit.
        session.commit()
        session.refresh(new_transaction)

        result = transaction_to_dict(new_transaction)
        result["category_rule_saved"] = category_rule_saved

        return result


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


@app.post("/ai/analyze-expenses")
def ai_analyze_expenses(
    start_date: date,
    end_date: date,
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="Начальная дата не может быть позже конечной",
        )

    with SessionLocal() as session:
        summary = get_financial_summary(
            session=session,
            start_date=start_date,
            end_date=end_date,
        )

    try:
        graph_result = run_expense_graph(summary)

        if graph_result["validation_errors"]:
            print(
                "Предупреждения проверки AI-анализа:",
                "; ".join(graph_result["validation_errors"]),
            )

        analysis = graph_result["analysis"]
        review = graph_result["review"]

        if review.strip():
            analysis += "\n\n---\n\n### Проверка отчёта AI-ревьюером\n\n"
            analysis += review
    except Exception as error:
        # Не раскрываем клиенту технические детали и настройки API.
        print(
            "Ошибка AI-анализа:",
            type(error).__name__,
        )
        raise HTTPException(
            status_code=503,
            detail="AI-анализ временно недоступен. Попробуй позже.",
        ) from error

    return {
        "period": {
            "start_date": summary["start_date"],
            "end_date": summary["end_date"],
        },
        "summary": summary,
        "analysis": analysis,
    }

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

        merchant_key = extract_merchant_key(
            transaction["description"]
        )
        category_source = "heuristic"

        # MCC приоритетнее пользовательского правила.
        if transaction.get("mcc") is not None:
            category_source = "mcc"
        elif merchant_key is not None:
            with SessionLocal() as session:
                rule = find_category_rule(session, merchant_key)

                if rule is not None:
                    transaction["category"] = rule.category
                    category_source = "learned_rule"

        return {
            "saved": False,
            "message": (
                "Операция распознана. "
                "Проверь данные перед сохранением."
            ),
            "merchant_key": merchant_key,
            "category_source": category_source,
            "transaction": {
                "date": transaction["date"].isoformat(),
                "amount": transaction["amount"],
                "type": transaction["type"].value,
                "category": transaction["category"],
                "description": transaction["description"],
                "mcc": transaction.get("mcc"),
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
