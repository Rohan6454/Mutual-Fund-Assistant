"""
Download every URL in data/sources.json; save HTML/PDF under data/raw/ with .meta.json sidecars.
Factsheet index pages: discover same-party PDF links and download up to SCRAPE_MAX_PDFS_PER_PAGE each.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from config.settings import settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SOURCES_JSON = REPO_ROOT / "data" / "sources.json"
RAW_HTML = REPO_ROOT / "data" / "raw" / "html"
RAW_PDF = REPO_ROOT / "data" / "raw" / "pdf"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 "
    "MutualFund-FAQ-Assistant/1.0 (+https://github.com/)"
)


def slugify(name: str) -> str:
    s = (name or "").lower()
    s = re.sub(r"[\(\)]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "x"


def registrable_root(host: str) -> str:
    parts = host.lower().split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host.lower()


def same_party(base_url: str, target_url: str) -> bool:
    b, u = urlparse(base_url).netloc, urlparse(target_url).netloc
    if not b or not u:
        return False
    if b == u:
        return True
    return registrable_root(b) == registrable_root(u)


def today_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def html_filename(entry: dict, date_str: str) -> str:
    st = entry.get("source_type", "doc")
    source_id = entry.get("id", "src")
    parsed = urlparse(entry.get("url", ""))
    url_part = slugify(parsed.path.strip("/") or "root")[:60]
    return f"{st}_{source_id}_{url_part}_{date_str}.html"


def extract_pdf_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    found: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#"):
            continue
        full = urljoin(base_url, href)
        path = urlparse(full).path.lower().split("?")[0]
        if path.endswith(".pdf") and same_party(base_url, full):
            found.append(full)
    out: list[str] = []
    seen = set()
    for u in found:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def write_sidecar(raw_file: Path, meta: dict) -> None:
    side = raw_file.with_name(raw_file.stem + ".meta.json")
    side.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch(url: str) -> requests.Response:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
    }
    return requests.get(url, headers=headers, timeout=settings.SCRAPE_REQUEST_TIMEOUT)

def fetch_html_playwright(url: str) -> str:
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            # Use a slightly more realistic context
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()
            # Add extra headers to look more like a real user
            page.set_extra_http_headers({
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            })
            page.goto(url, wait_until="networkidle", timeout=(settings.SCRAPE_REQUEST_TIMEOUT * 1000))
            # Wait a few seconds for late-loading React/Angular tables
            time.sleep(3)
            content = page.content()
            browser.close()
            return content
    except Exception as e:
        logger.warning("Playwright failed for %s: %s. Falling back to requests content if possible.", url, e)
        return ""

def download_pdf(url: str) -> bytes:
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=settings.SCRAPE_REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.content


def scrape_pdf_for_parent(
    *,
    pdf_url: str,
    parent: dict,
    date_str: str,
    index: int,
) -> None:
    amc = parent.get("amc") or parent.get("batch", "amc")
    path_part = unquote(urlparse(pdf_url).path.split("/")[-1] or "factsheet")
    base_pdf = re.sub(r"\.pdf$", "", path_part, flags=re.I)
    safe = slugify(base_pdf)[:80] or "factsheet"
    fname = f"factsheet_{slugify(amc)}_{safe}_{date_str}_{index:02d}.pdf"
    out = RAW_PDF / fname
    data = download_pdf(pdf_url)
    out.write_bytes(data)
    meta = {
        "source_id": f"{parent['id']}_pdf_{index:02d}",
        "parent_source_id": parent["id"],
        "url": pdf_url,
        "source_type": parent.get("source_type", "factsheet"),
        "document_format": "pdf",
        "batch": parent.get("batch"),
        "scheme_name": parent.get("scheme_name", "general"),
        "amc": parent.get("amc"),
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "category": parent.get("category"),
    }
    write_sidecar(out, meta)
    logger.info("Saved PDF %s", fname)


def scrape_html_entry(entry: dict, date_str: str) -> None:
    url = entry["url"]
    name = html_filename(entry, date_str)
    out = RAW_HTML / name
    try:
        r = fetch(url)
        r.raise_for_status()
        ctype = (r.headers.get("Content-Type") or "").lower()
        if "pdf" in ctype:
            RAW_PDF.mkdir(parents=True, exist_ok=True)
            pdf_name = name.replace(".html", ".pdf")
            pout = RAW_PDF / pdf_name
            pout.write_bytes(r.content)
            meta = {
                "source_id": entry["id"],
                "url": url,
                "source_type": entry.get("source_type"),
                "document_format": "pdf",
                "batch": entry.get("batch"),
                "scheme_name": entry.get("scheme_name", "general"),
                "amc": entry.get("amc"),
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "category": entry.get("category"),
                "notes": entry.get("notes"),
            }
            write_sidecar(pout, meta)
            entry["last_scraped"] = meta["scraped_at"]
            entry["scrape_status"] = "ok"
            logger.info("Saved PDF (direct) %s", pdf_name)
            return

        req_text = r.text
        text = fetch_html_playwright(url)
        if not text or len(text.strip()) < 500:
            logger.info("Playwright returned empty or too short content, using requests text instead.")
            text = req_text
            
        if len(text.strip()) < 200:
            raise ValueError("response body too short for HTML even with requests fallback")
        out.write_text(text, encoding="utf-8", errors="replace")
        meta = {
            "source_id": entry["id"],
            "url": url,
            "source_type": entry.get("source_type"),
            "document_format": "html",
            "batch": entry.get("batch"),
            "scheme_name": entry.get("scheme_name", "general"),
            "amc": entry.get("amc"),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "category": entry.get("category"),
            "notes": entry.get("notes"),
        }
        write_sidecar(out, meta)
        entry["last_scraped"] = meta["scraped_at"]
        entry["scrape_status"] = "ok"
        logger.info("Saved HTML %s", name)

        if entry.get("batch") == "factsheets":
            RAW_PDF.mkdir(parents=True, exist_ok=True)
            links = extract_pdf_links(text, url)[: settings.SCRAPE_MAX_PDFS_PER_PAGE]
            for i, pdf_url in enumerate(links, start=1):
                try:
                    scrape_pdf_for_parent(pdf_url=pdf_url, parent=entry, date_str=date_str, index=i)
                    time.sleep(settings.SCRAPE_DELAY_SECONDS)
                except Exception as e:
                    logger.warning("PDF download failed %s: %s", pdf_url, e)

    except Exception as e:
        entry["scrape_status"] = "failed"
        entry["last_scraped"] = datetime.now(timezone.utc).isoformat()
        logger.error("Failed %s (%s): %s", entry.get("id"), url, e)


def clear_previous_raw_outputs() -> None:
    for folder, ext in ((RAW_HTML, "*.html"), (RAW_HTML, "*.meta.json"), (RAW_PDF, "*.pdf"), (RAW_PDF, "*.meta.json")):
        for p in folder.glob(ext):
            p.unlink(missing_ok=True)


def main() -> None:
    RAW_HTML.mkdir(parents=True, exist_ok=True)
    RAW_PDF.mkdir(parents=True, exist_ok=True)
    clear_previous_raw_outputs()

    data = json.loads(SOURCES_JSON.read_text(encoding="utf-8"))
    sources = data.get("sources", [])
    date_str = today_stamp()

    for entry in sources:
        time.sleep(settings.SCRAPE_DELAY_SECONDS)
        scrape_html_entry(entry, date_str)

    data["sources"] = sources
    if "metadata" in data:
        data["metadata"]["total_sources"] = len(sources)
    tmp = SOURCES_JSON.with_name(SOURCES_JSON.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(SOURCES_JSON)
    logger.info("Updated %s", SOURCES_JSON)


if __name__ == "__main__":
    main()
