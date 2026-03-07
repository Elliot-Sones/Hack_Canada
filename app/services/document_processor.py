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

    if lower.endswith(".dxf"):
        return "cad_drawing"

    spreadsheet_exts = (".xlsx", ".xls", ".csv", ".ods")
    if any(lower.endswith(ext) for ext in spreadsheet_exts):
        return "spreadsheet"

    return "other"


def extract_pdf_vectors(file_bytes: bytes) -> list[dict] | None:
    """Try to extract vector geometry from PDF pages using PyMuPDF.

    Returns list of per-page geometry dicts, or None if extraction fails.
    """
    import fitz

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_geometry = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            drawings = page.get_drawings()

            if not drawings:
                pages_geometry.append(None)
                continue

            walls = []
            room_polygons = []

            for path in drawings:
                items = path.get("items", [])
                fill = path.get("fill")

                points = []
                for item in items:
                    if item[0] == "l":  # line
                        p1, p2 = item[1], item[2]
                        # Convert from points to metres (1 point = 1/72 inch = 0.000352778 m)
                        scale = 0.000352778
                        walls.append({
                            "start": [p1.x * scale, p1.y * scale],
                            "end": [p2.x * scale, p2.y * scale],
                            "thickness_m": (path.get("width", 1) or 1) * scale,
                            "type": "interior",
                        })
                    elif item[0] in ("c", "qu"):  # curve
                        pass  # skip curves for now

                    if item[0] == "l":
                        points.extend([item[1], item[2]])

                # If path is filled/closed, treat as room polygon
                if fill is not None and len(points) >= 6:
                    scale = 0.000352778
                    polygon = [(p.x * scale, p.y * scale) for p in points]
                    # Remove duplicates
                    seen = set()
                    unique = []
                    for pt in polygon:
                        key = (round(pt[0], 4), round(pt[1], 4))
                        if key not in seen:
                            seen.add(key)
                            unique.append(list(pt))
                    if len(unique) >= 3:
                        room_polygons.append(unique)

            if walls or room_polygons:
                pages_geometry.append({
                    "walls": walls,
                    "rooms": [{"polygon": poly, "name": f"Room {i+1}", "type": "other"} for i, poly in enumerate(room_polygons)],
                })
            else:
                pages_geometry.append(None)

        doc.close()

        # Return None if no pages had vector data
        if all(pg is None for pg in pages_geometry):
            return None

        return pages_geometry
    except Exception:
        return None


def compute_file_hash(file_bytes: bytes) -> str:
    """SHA-256 hash for dedup."""
    return hashlib.sha256(file_bytes).hexdigest()
