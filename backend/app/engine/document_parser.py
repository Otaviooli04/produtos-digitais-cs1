import io
import pymupdf
from docx import Document


def parse_document(file_bytes: bytes, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        return _parse_pdf(file_bytes)
    if ext in ("docx", "doc"):
        return _parse_docx(file_bytes)

    raise ValueError(f"Formato não suportado: {ext}. Envie PDF ou DOCX.")


def _parse_pdf(file_bytes: bytes) -> str:
    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    return "\n".join(page.get_text() for page in doc).strip()


def _parse_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()
