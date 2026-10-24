from pathlib import Path

from backend.importers.pdf_reader import extract_pdf_text
from backend.importers.sber_pdf import parse_sber_operation_text


def parse_sber_pdf(file_path: str | Path) -> dict:
    text = extract_pdf_text(file_path)
    return parse_sber_operation_text(text)
