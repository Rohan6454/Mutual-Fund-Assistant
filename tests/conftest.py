"""Pytest path setup for hyphenated phase folders (not Python packages)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASE3 = ROOT / "phase-3-retrieval-engine"

# Phase 3 modules use flat imports (enums, guardrails, …)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PHASE3))
