from fastapi import FastAPI, HTTPException

from backend.schemas import TransactionCreate


app = FastAPI(title="Smart Finance API")

transactions: list[dict] = []
next_transaction_id = 1


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
    global next_transaction_id

    new_transaction = {
        "id": next_transaction_id,
        **transaction.model_dump(mode="json"),
    }

    transactions.append(new_transaction)
    next_transaction_id += 1

    return new_transaction


@app.get("/transactions")
def get_transactions():
    return transactions


@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: int):
    for transaction in transactions:
        if transaction["id"] == transaction_id:
            return transaction

    raise HTTPException(
        status_code=404,
        detail="Транзакция не найдена",
    )
