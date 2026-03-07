"""PDF processing and file classification utilities."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class PageResult:
    page_number: int
    png_bytes: bytes
    width: int
    height: int


def process_pdf(file_bytes: bytes) -> list[PageResult]:
    """Convert PDF to per-page PNGs at 200 DPI using PyMuPDF."""
    import fitz  # PyMuPDF

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    results = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # 200 DPI: default is 72 DPI, so scale factor = 200/72 ≈ 2.78
        mat = fitz.Matrix(200 / 72, 200 / 72)
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        results.append(PageResult(
            page_number=page_num + 1,
            png_bytes=png_bytes,
            width=pix.width,
            height=pix.height,
        ))
    doc.close()
    return results


def get_file_category(filename: str, content_type: str) -> str:
    """Classify file type based on extension and mime type."""
    lower = filename.lower()

    if content_type == "application/pdf" or lower.endswith(".pdf"):
        # Heuristic: correction letters often have "correction" or "comment" in filename
        for keyword in ("correction", "comment", "response", "deficiency", "letter"):
            if keyword in lower:
                return "correction_letter"
        return "architectural_plan"

    if content_type.startswith("image/"):
        return "site_photo"

    spreadsheet_exts = (".xlsx", ".xls", ".csv", ".ods")
    if any(lower.endswith(ext) for ext in spreadsheet_exts):
        return "spreadsheet"

    return "other"


def compute_file_hash(file_bytes: bytes) -> str:
    """SHA-256 hash for dedup."""
    return hashlib.sha256(file_bytes).hexdigest()
