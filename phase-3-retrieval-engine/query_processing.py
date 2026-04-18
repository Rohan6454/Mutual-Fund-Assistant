"""Query normalization, abbreviation expansion, and scheme name detection."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from config.prompts import KNOWN_SCHEMES

_ABBREV = {
    r"\ber\b": "expense ratio",
    r"\bnav\b": "net asset value",
    r"\baum\b": "assets under management",
    r"\bsip\b": "systematic investment plan",
    r"\bswp\b": "systematic withdrawal plan",
    r"\bstp\b": "systematic transfer plan",
    r"\belss\b": "equity linked savings scheme",
    r"\bkim\b": "key information memorandum",
    r"\bsid\b": "scheme information document",
}


def normalize_query(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"\s+", " ", t)
    return t


def expand_abbreviations(normalized: str) -> str:
    out = normalized
    for pattern, replacement in _ABBREV.items():
        out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
    return out


def detect_scheme_name(normalized_query: str) -> str | None:
    """
    Match a known scheme from config/prompts.py using substring and token overlap.
    Enhanced to handle more variations and AMC names.
    """
    q = normalized_query
    
    # First try exact substring match
    for scheme in KNOWN_SCHEMES:
        sk = scheme.lower()
        if sk in q:
            return scheme
    
    # Try AMC-based matching
    amc_keywords = {
        "icici": ["ICICI Prudential"],
        "hdfc": ["HDFC Mutual Fund"],
        "nippon": ["Nippon India Mutual Fund"],
        "nippon india": ["Nippon India Mutual Fund"]
    }
    
    detected_amc = None
    for keyword, amcs in amc_keywords.items():
        if keyword in q:
            detected_amc = amcs[0]
            break
    
    # Try token-based matching with lower threshold
    for scheme in KNOWN_SCHEMES:
        sk = scheme.lower()
        tokens = [t for t in re.split(r"[^\w]+", sk) if len(t) > 2]
        if len(tokens) < 2:
            continue
        
        # Count matching tokens
        hits = sum(1 for t in tokens if t in q)
        
        # Lower threshold for better matching
        min_hits = max(1, (len(tokens) + 1) // 2)
        if hits >= min_hits:
            return scheme
    
    # If AMC detected but no specific scheme, return None to trigger fallback
    if detected_amc:
        return None
    
    return None


def build_enhanced_query(normalized: str, scheme: str | None) -> str:
    """Text used for embedding (retrieval query)."""
    parts = [normalized]
    if scheme:
        parts.append(scheme.lower())
    return " ".join(parts)
