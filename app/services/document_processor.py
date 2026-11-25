
from pathlib import Path

import pymupdf

from docx import Document


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class DocumentExtractionError(Exception):
    pass


def extract_pdf(file_path):
    """Extract text page by page from a PDF."""
    pages = []

    try:
        with pymupdf.open(file_path) as pdf:
            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text("text")

                if text.strip():
                    pages.append({
                        "page_number": page_number,
                        "text": text.strip()
                    })

    except Exception as e:
        raise DocumentExtractionError(
            f"PDF extraction failed: {e}"
        ) from e

    return pages


def extract_docx(file_path):
    """Extract paragraphs and tables from a DOCX file."""
    try:
        doc = Document(file_path)

        content = []

        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()

            if text:
                content.append(text)

        # Extract table content as well
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(
                    cell.text.strip() for cell in row.cells
                )

                if row_text.strip():
                    content.append(row_text)

        text = "\n\n".join(content)

        return [{
            "page_number": None,
            "text": text
        }] if text else []

    except Exception as e:
        raise DocumentExtractionError(
            f"DOCX extraction failed: {e}"
        ) from e


def extract_text_file(file_path):
    """Extract text from TXT or Markdown files."""
    try:
        text = Path(file_path).read_text(encoding="utf-8-sig")

        return [{
            "page_number": None,
            "text": text.strip()
        }] if text.strip() else []

    except UnicodeDecodeError as e:
        raise DocumentExtractionError(
            "Unsupported text file encoding. Expected UTF-8."
        ) from e
    except Exception as e:
        raise DocumentExtractionError(
            f"Text extraction failed: {e}"
        ) from e


def extract_document(file_path):
    """
    Extract text from a supported document.

    Returns:
        List of dictionaries containing page_number and text.
    """
    path = Path(file_path)

    if not path.exists() or not path.is_file():
        raise DocumentExtractionError("File does not exist.")

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise DocumentExtractionError(
            f"Unsupported file format: {extension}"
        )

    if extension == ".pdf":
        pages = extract_pdf(path)

    elif extension == ".docx":
        pages = extract_docx(path)

    else:
        pages = extract_text_file(path)

    if not pages:
        raise DocumentExtractionError(
            "No extractable text found in the document. "
            "The PDF may be scanned and require OCR."
        )

    return pages
