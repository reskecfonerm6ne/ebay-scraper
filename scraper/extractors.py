from __future__ import annotations

import re
from typing import Optional, Tuple


_PRICE_RE = re.compile(r"([A-Z]{0,3})\s*\$?\s*([0-9][0-9,]*\.?[0-9]*)")

def parse_price(text: str) -> Tuple[Optional[str], Optional[float]]:
    if not text:
        return None, None
    m = _PRICE_RE.search(text.replace("\u00a0", " ").strip())
    if not m:
        return None, None
    currency = (m.group(1) or "").strip() or None
    raw = m.group(2).replace(",", "")
    try:
        return currency, float(raw)
    except ValueError:
        return currency, None


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())
