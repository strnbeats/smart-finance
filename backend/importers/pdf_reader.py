from pathlib import Path

import pymupdf


def extract_pdf_text(file_path: str | Path) -> str:
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"PDF-файл не найден: {path}"
        )

    if path.suffix.lower() != ".pdf":
        raise ValueError("Ожидается PDF-файл")

    try:
        with pymupdf.open(path) as document:
            if document.is_encrypted:
                raise ValueError(
                    "PDF защищён паролем"
                )

            text = "\n".join(
                page.get_text()
                for page in document
            )

    except pymupdf.FileDataError as error:
        raise ValueError(
            "Не удалось прочитать PDF-файл"
        ) from error

    if not text.strip():
        raise ValueError(
            "В PDF не найден текст. "
            "Возможно, это скан и потребуется OCR."
        )

    return text
