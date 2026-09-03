from __future__ import annotations

import fitz


def extract_pdf_text(
    content: bytes,
) -> str:
    document = fitz.open(
        stream=content,
        filetype="pdf",
    )

    pages: list[str] = []

    for page in document:
        text = page.get_text("text")

        if text:
            pages.append(text)

    document.close()

    result = "\n".join(pages).strip()

    if len(result) < 100:
        raise ValueError(
            "Не удалось нормально извлечь текст из PDF"
        )

    return result