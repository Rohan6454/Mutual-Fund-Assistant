"""Text cleaning and normalization for document processing."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def collapse_whitespace(text: str) -> str:
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


_DATE_PATTERNS = (
    (re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b"), r"\3-\2-\1"),  # loose; best-effort
)


def normalize_dates(text: str) -> str:
    for pattern, _ in _DATE_PATTERNS:
        pass  # keep text as-is unless we add safe ISO conversion per locale
    return text


def remove_repeated_lines(text: str, min_repeat: int = 4) -> str:
    """Drop lines that appear many times (common disclaimers / footers)."""
    lines = text.splitlines()
    if len(lines) < min_repeat * 2:
        return text
    counts = Counter(line.strip() for line in lines if line.strip())
    frequent = {line for line, c in counts.items() if c >= min_repeat and len(line) > 40}
    if not frequent:
        return text
    kept = [ln for ln in lines if ln.strip() not in frequent]
    return "\n".join(kept)


def clean_text(text: str) -> str:
    text = normalize_unicode(text)
    text = collapse_whitespace(text)
    text = normalize_dates(text)
    text = remove_repeated_lines(text)
    return text


def table_to_flat_text(table_soup) -> str:
    """Flatten a BeautifulSoup table to readable lines."""
    rows = []
    for tr in table_soup.find_all("tr"):
        cells = [c.get_text(separator=" ", strip=True) for c in tr.find_all(["th", "td"])]
        cells = [c for c in cells if c]
        if cells:
            rows.append(": ".join(cells) if len(cells) == 2 else " | ".join(cells))
    return "\n".join(rows)
