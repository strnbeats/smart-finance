import re
from datetime import date
from decimal import Decimal

from backend.schemas import TransactionType


MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}


def suggest_category(description: str) -> str:
    text = description.lower()

    if any(word in text for word in ("яндекс go", "такси", "uber")):
        return "Транспорт"

    return "Без категории"


def parse_sber_operation_text(text: str) -> dict:
    text = (
        text.replace("\u00a0", " ")
        .replace("\u202f", " ")
        .replace("\u2007", " ")
        .replace("\x00", "")
    )

    date_match = re.search(
        r"Операция\s+совершена\s+"
        r"(\d{1,2})\s+([а-яё]+)\s+(\d{4})",
        text,
        re.IGNORECASE,
    )

    if not date_match:
        raise ValueError("Не удалось найти дату операции")

    day, month_name, year = date_match.groups()
    month = MONTHS.get(month_name.lower())

    if month is None:
        raise ValueError("Неизвестный месяц в дате операции")

    operation_date = date(int(year), month, int(day))

    description_match = re.search(
        r"Описание\s*(.*?)\s*Операция\s+совершена",
        text,
        re.DOTALL | re.IGNORECASE,
    )

    if not description_match:
        raise ValueError("Не удалось найти описание операции")

    description = " ".join(description_match.group(1).split())


    amount_match = re.search(
        r"Сумма в валюте сч[её]та\s*"
        r"([\d\s]+(?:[,.]\d{1,2})?)"
        r"(?=\s*(?:₽|Р|руб\.?|Сумма в валюте операции))",
        text,
        re.IGNORECASE,
    )

    if not amount_match:
        raise ValueError("Не удалось найти сумму операции")


    if not amount_match:
        raise ValueError("Не удалось найти сумму операции")

    amount_text = re.sub(r"\s+", "", amount_match.group(1))
    amount_text = amount_text.replace(",", ".")

    amount_in_kopecks = int(Decimal(amount_text) * 100)

    if amount_in_kopecks <= 0:
        raise ValueError("Сумма операции должна быть положительной")

    status_match = re.search(
        r"Статус операции\s*(.*?)"
        r"(?=\s*Тип операции|\s*Описание|\s*Операция совершена|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )

    if not status_match:
        raise ValueError("Не удалось определить статус операции")

    status = " ".join(status_match.group(1).split()).lower()

    if status not in ("платёж выполнен", "платеж выполнен"):
        raise ValueError(
            "Операция ещё не подтверждена или её статус не распознан"
        )


    if not status_match:
        raise ValueError("Не удалось определить статус операции")

    status = " ".join(status_match.group(1).split()).lower()

    if status not in ("платёж выполнен", "платеж выполнен"):
        raise ValueError(
            f"Неизвестный или неподтверждённый статус операции: {status!r}"
    )

    return {
        "date": operation_date,
        "amount": amount_in_kopecks,
        "type": TransactionType.EXPENSE,
        "category": suggest_category(description),
        "description": description,
    }
