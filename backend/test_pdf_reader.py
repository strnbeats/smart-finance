import pymupdf
import pytest

from backend.importers.pdf_reader import extract_pdf_text


def test_extract_text_from_pdf(tmp_path):
    pdf_path = tmp_path / "sample.pdf"

    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Sber statement sample")
    document.save(pdf_path)
    document.close()

    text = extract_pdf_text(pdf_path)

    assert "Sber statement sample" in text


def test_missing_pdf_raises_error(tmp_path):
    pdf_path = tmp_path / "missing.pdf"

    with pytest.raises(FileNotFoundError):
        extract_pdf_text(pdf_path)


def test_empty_pdf_raises_error(tmp_path):
    pdf_path = tmp_path / "empty.pdf"

    document = pymupdf.open()
    document.new_page()
    document.save(pdf_path)
    document.close()

    with pytest.raises(ValueError, match="не найден текст"):
        extract_pdf_text(pdf_path)


def test_non_pdf_file_raises_error(tmp_path):
    file_path = tmp_path / "statement.txt"
    file_path.write_text("test", encoding="utf-8")

    with pytest.raises(ValueError, match="Ожидается PDF"):
        extract_pdf_text(file_path)
