import io


def extract_text(filename: str, data: bytes) -> str:
    """PDF -> plain text; anything else is decoded as UTF-8 text."""
    if filename.lower().endswith(".pdf") or data[:5] == b"%PDF-":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    else:
        text = data.decode("utf-8", errors="replace")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def guess_name(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:80] if len(line.split()) <= 5 else fallback
    return fallback
