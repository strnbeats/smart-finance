from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionCreate(BaseModel):
    date: date
    amount: int = Field(gt=0, description="Сумма в копейках")
    type: TransactionType
    category: str = Field(min_length=1, max_length=50)
    description: str = Field(default="", max_length=500)


class TransactionUpdate(BaseModel):
    date: date
    amount: int = Field(gt=0, description="Сумма в копейках")
    type: TransactionType
    category: str = Field(min_length=1, max_length=50)
    description: str = Field(default="", max_length=500)
