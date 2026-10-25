from datetime import date
from pathlib import Path

import pymupdf
import pytest

from backend.importers.sber_import import parse_sber_pdf
from backend.importers.sber_pdf import (
    parse_sber_operation_text,
    suggest_category,
)
from backend.schemas import TransactionType


SAMPLE_TEXT = """
Справка по операции
Описание
Яндекс Go
(YANDEX*4121*GO MOSCOW RUS)
Операция совершена
24 октября 2026 в 20:57
Статус операции
Платёж выполнен
Тип операции
Оплата товаров и услуг
Сумма в валюте счёта
30 ₽
Сумма в валюте операции
30 ₽
"""


def find_cyrillic_font() -> Path:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/Library/Fonts/Arial.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ]

    for path in candidates:
        if path.is_file():
            return path

    raise FileNotFoundError(
        "Не найден системный шрифт с поддержкой кириллицы. "
        "Укажи путь к Arial.ttf или другому подходящему шрифту."
    )


def test_parse_sber_operation():
    result = parse_sber_operation_text(SAMPLE_TEXT)

    assert result["date"] == date(2026, 10, 24)
    assert result["amount"] == 3000
    assert result["type"] == TransactionType.EXPENSE
    assert result["category"] == "Транспорт"
    assert result["description"] == (
        "Яндекс Go (YANDEX*4121*GO MOSCOW RUS)"
    )


def test_reject_unconfirmed_operation():
    text = SAMPLE_TEXT.replace(
        "Платёж выполнен",
        "Операция обрабатывается",
    )

    with pytest.raises(ValueError, match="не подтверждена"):
        parse_sber_operation_text(text)


def test_suggest_category_uses_mcc():
    assert suggest_category("Неизвестный магазин", "5411") == "Еда"


def test_suggest_category_falls_back_to_description():
    assert suggest_category("YANDEX GO", None) == "Транспорт"


def test_parse_sber_pdf_end_to_end(tmp_path):
    pdf_path = tmp_path / "sber_statement.pdf"
    font_path = find_cyrillic_font()

    document = pymupdf.open()
    page = document.new_page()

    page.insert_font(
        fontname="CyrillicFont",
        fontfile=str(font_path),
    )

    page.insert_textbox(
        pymupdf.Rect(50, 50, 550, 750),
        SAMPLE_TEXT,
        fontsize=11,
        fontname="CyrillicFont",
    )

    document.save(pdf_path)
    document.close()

    result = parse_sber_pdf(pdf_path)

    assert result["date"] == date(2026, 10, 24)
    assert result["amount"] == 3000
    assert result["type"] == TransactionType.EXPENSE
    assert result["category"] == "Транспорт"


def test_parse_sber_pdf_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_sber_pdf(tmp_path / "missing.pdf")
