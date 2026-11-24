
import re
import uuid


DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 200


def clean_text(text: str) -> str:
    """Clean extracted text while preserving paragraph boundaries."""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove excessive spaces and tabs
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> list[str]:
    """
    Split text into overlapping chunks.

    Attempts to end chunks at sentence boundaries.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be >= 0 and smaller than chunk_size."
        )

    text = clean_text(text)

    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(start + chunk_size, text_length)

        # If this is not the final chunk, find a sentence boundary
        if end < text_length:
            boundary = max(
                text.rfind(". ", start, end),
                text.rfind("? ", start, end),
                text.rfind("! ", start, end),
                text.rfind("\n\n", start, end)
            )

            # Use the boundary only if it is reasonably far into the chunk
            if boundary > start + chunk_size // 2:
                end = boundary + 1

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        # Move forward while retaining overlap
        next_start = max(start + 1, end - chunk_overlap)

        # Avoid starting in the middle of a word
        while (
            next_start < end
            and not text[next_start - 1].isspace()
        ):
            next_start += 1

        start = next_start

    return chunks


def chunk_document(
    pages: list[dict],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> list[dict]:
    """
    Convert extracted document pages into chunks.

    Each chunk contains:
        chunk_id
        chunk_index
        page_number
        text
    """

    generated_chunks = []

    for page in pages:

        page_text = page.get("text", "")
        page_number = page.get("page_number")

        page_chunks = split_into_chunks(
            page_text,
            chunk_size,
            chunk_overlap
        )

        for chunk in page_chunks:
            generated_chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "chunk_index": len(generated_chunks),
                "page_number": page_number,
                "text": chunk
            })

    return generated_chunks
