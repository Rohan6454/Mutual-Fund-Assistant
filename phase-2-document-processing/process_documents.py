"""
Extract text from raw HTML/PDF, clean, section-aware chunk, write JSON chunks.
Run from repo root context; paths are resolved against the repository root.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from pathlib import Path

from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter

_PHASE2 = Path(__file__).resolve().parent
REPO_ROOT = _PHASE2.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(_PHASE2))

import fitz  # PyMuPDF
import pdfplumber

import text_processing

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RAW_HTML = REPO_ROOT / "data" / "raw" / "html"
RAW_PDF = REPO_ROOT / "data" / "raw" / "pdf"
CHUNKS_DIR = REPO_ROOT / "data" / "processed" / "chunks"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 75


def _load_sidecar_meta(file_path: Path) -> dict:
    side = file_path.with_name(file_path.stem + ".meta.json")
    if not side.is_file():
        return {}
    return json.loads(side.read_text(encoding="utf-8"))


def _strip_noise_tags(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()
    for sel in ["nav", "footer"]:
        for tag in soup.find_all(sel):
            tag.decompose()


def _sections_from_html(soup: BeautifulSoup) -> list[tuple[str | None, str, bool]]:
    """
    Returns list of (section_title, text, is_table).
    Tables are emitted as separate logical blocks (single chunk target).
    """
    main = soup.find("main") or soup.find("article") or soup.find("body") or soup
    _strip_noise_tags(soup)
    blocks: list[tuple[str | None, str, bool]] = []

    for table in main.find_all("table"):
        flat = text_processing.table_to_flat_text(table)
        if flat.strip():
            blocks.append((None, text_processing.clean_text(flat), True))
        table.decompose()

    headings = main.find_all(["h2", "h3"])
    
    # 1. Capture Lead Text (everything before the first heading)
    first_h = headings[0] if headings else None
    lead_parts = []
    curr = main.find() # Start from first child
    while curr and curr != first_h:
        if curr.name == "table":
            t = text_processing.table_to_flat_text(curr)
            if t.strip():
                blocks.append(("General Information", text_processing.clean_text(t), True))
        elif hasattr(curr, "get_text") and curr.name not in ["h2", "h3"]:
            # Only get direct text or non-heading text
            t = curr.get_text("\n", strip=True)
            if t and t not in [b[1] for b in blocks]:
                lead_parts.append(t)
        curr = curr.next_sibling
    
    lead_body = "\n".join(lead_parts)
    if lead_body.strip():
        blocks.append(("Overview", text_processing.clean_text(lead_body), False))

    if not headings:
        # If we already got lead text, we might be done, but let's double check
        if not blocks:
            text = main.get_text("\n", strip=True)
            if text:
                blocks.append((None, text_processing.clean_text(text), False))
        return blocks

    # 2. Capture Headed Sections
    for h in headings:
        title = h.get_text(strip=True) or None
        parts: list[str] = []
        for sib in h.find_next_siblings():
            if getattr(sib, "name", None) in ("h2", "h3"):
                break
            if getattr(sib, "name", None) == "table":
                t = text_processing.table_to_flat_text(sib)
                if t.strip():
                    blocks.append((title, text_processing.clean_text(t), True))
                continue
            if hasattr(sib, "get_text"):
                t = sib.get_text("\n", strip=True)
                if t:
                    parts.append(t)
        body = "\n".join(parts)
        if body.strip():
            blocks.append((title, text_processing.clean_text(body), False))
    return blocks


def _pdf_to_text(pdf_path: Path) -> str:
    text_parts: list[str] = []
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
    except Exception as e:
        logger.warning("PyMuPDF failed for %s: %s", pdf_path, e)
    raw = "\n\n".join(text_parts)
    if len(raw.strip()) < 200:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                alt = []
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        alt.append(t)
            raw = "\n\n".join(alt)
        except Exception as e:
            logger.warning("pdfplumber fallback failed for %s: %s", pdf_path, e)
    return text_processing.clean_text(raw)


def _split_table_chunk(text: str) -> list[str]:
    if len(text) <= CHUNK_SIZE * 2:
        return [text]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE * 2,
        chunk_overlap=min(CHUNK_OVERLAP * 2, CHUNK_SIZE),
        separators=["\n", ". ", " "],
    )
    return splitter.split_text(text)


def _split_regular(section_text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "],
    )
    return splitter.split_text(section_text)


def _write_chunks_for_file(
    *,
    raw_path: Path,
    meta: dict,
    pieces: list[tuple[str | None, str, bool]],
) -> int:
    source_url = meta.get("url", "")
    source_id = meta.get("source_id", "")
    scheme = meta.get("scheme_name", "general")
    base_doc_type = meta.get("source_type", "unknown")
    last_updated = (meta.get("scraped_at") or "")[:10] or None

    buffer: list[tuple[str, dict]] = []

    for section, text, is_table in pieces:
        if not text.strip():
            continue
        if is_table:
            segments = _split_table_chunk(text)
            dt = "table"
        else:
            segments = _split_regular(text)
            dt = base_doc_type

        for seg in segments:
            if not seg.strip():
                continue
                
            prefix_parts = []
            if scheme and scheme != "general":
                prefix_parts.append(f"Scheme: {scheme}")
            if section:
                prefix_parts.append(f"Section: {section}")
            
            prefix = " | ".join(prefix_parts)
            enriched_seg = f"{prefix}\n{seg}" if prefix else seg
            
            chunk_id = str(uuid.uuid4())
            record = {
                "chunk_id": chunk_id,
                "text": enriched_seg,
                "metadata": {
                    "source_url": source_url,
                    "source_id": source_id,
                    "scheme_name": scheme,
                    "doc_type": dt,
                    "section": section,
                    "page_number": None,
                    "last_updated": last_updated,
                    "chunk_index": 0,
                    "total_chunks": 0,
                    "raw_file": str(raw_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                },
            }
            buffer.append((chunk_id, record))

    total = len(buffer)
    for i, (chunk_id, record) in enumerate(buffer):
        record["metadata"]["chunk_index"] = i
        record["metadata"]["total_chunks"] = total
        out = CHUNKS_DIR / f"{chunk_id}.json"
        out.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return total


def _clear_chunks_dir() -> None:
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    for p in CHUNKS_DIR.glob("*.json"):
        try:
            p.unlink()
        except PermissionError:
            logger.warning("Could not delete %s due to Windows file lock. Skipping.", p.name)


def process_html(path: Path, meta: dict) -> int:
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    blocks = _sections_from_html(soup)
    if not blocks:
        logger.warning("No text extracted from HTML %s", path.name)
        return 0
    return _write_chunks_for_file(raw_path=path, meta=meta, pieces=blocks)


def process_pdf(path: Path, meta: dict) -> int:
    text = _pdf_to_text(path)
    if not text.strip():
        logger.warning("No text extracted from PDF %s", path.name)
        return 0
    pieces = [(None, text, False)]
    return _write_chunks_for_file(raw_path=path, meta=meta, pieces=pieces)


def main() -> None:
    RAW_HTML.mkdir(parents=True, exist_ok=True)
    RAW_PDF.mkdir(parents=True, exist_ok=True)
    _clear_chunks_dir()

    total_chunks = 0
    for path in sorted(RAW_HTML.glob("*.html")):
        meta = _load_sidecar_meta(path)
        if not meta:
            logger.warning("Skipping %s (no %s.meta.json)", path.name, path.stem)
            continue
        try:
            total_chunks += process_html(path, meta)
        except Exception as e:
            logger.exception("Failed HTML %s: %s", path, e)

    for path in sorted(RAW_PDF.glob("*.pdf")):
        meta = _load_sidecar_meta(path)
        if not meta:
            logger.warning("Skipping %s (no %s.meta.json)", path.name, path.stem)
            continue
        try:
            total_chunks += process_pdf(path, meta)
        except Exception as e:
            logger.exception("Failed PDF %s: %s", path, e)

    logger.info("Wrote %s chunk files under %s", total_chunks, CHUNKS_DIR)


if __name__ == "__main__":
    main()
