from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List


@dataclass
class Listing:
    title: str
    url: str
    price: Optional[float] = None
    currency: Optional[str] = None
    shipping: Optional[str] = None
    condition: Optional[str] = None
    location: Optional[str] = None
    seller: Optional[str] = None
    watchers_or_bids: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SearchPageResult:
    query: str
    page: int
    listings: List[Listing]
    related_searches: List[str]
