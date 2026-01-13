from __future__ import annotations

import logging
import time
import urllib.parse
from dataclasses import dataclass
from typing import List, Optional

from .browser import BrowserConfig, BrowserSession
from .models import Listing, SearchPageResult
from .parser import parse_search_results, parse_related_searches


@dataclass(frozen=True)
class ScraperConfig:
    base_url: str
    user_agent: str
    headless: bool
    request_delay_seconds: float
    retry_count: int
    retry_backoff_seconds: float
    timeout_ms: int


class EbayScraper:
    def __init__(self, cfg: ScraperConfig, logger: Optional[logging.Logger] = None) -> None:
        self.cfg = cfg
        self.log = logger or logging.getLogger(__name__)

    def build_search_url(self, query: str, page: int = 1) -> str:
        params = {
            "_nkw": query,
            "_pgn": str(page),
        }
        return f"{self.cfg.base_url}?{urllib.parse.urlencode(params)}"

    def scrape(self, query: str, pages: int = 1) -> List[SearchPageResult]:
        pages = max(1, int(pages))
        results: List[SearchPageResult] = []

        bcfg = BrowserConfig(user_agent=self.cfg.user_agent, headless=self.cfg.headless, timeout_ms=self.cfg.timeout_ms)
        with BrowserSession(bcfg, logger=self.log) as sess:
            for p in range(1, pages + 1):
                url = self.build_search_url(query, page=p)
                html = self._fetch_with_retries(sess, url)
                listings = parse_search_results(html)
                related = parse_related_searches(html)

                results.append(SearchPageResult(query=query, page=p, listings=listings, related_searches=related))

                time.sleep(max(0.0, float(self.cfg.request_delay_seconds)))

        return results

    def _fetch_with_retries(self, sess: BrowserSession, url: str) -> str:
        for attempt in range(1, int(self.cfg.retry_count) + 1):
            try:
                return sess.get_html(url)
            except Exception as e:
                backoff = float(self.cfg.retry_backoff_seconds) * (attempt ** 1.5)
                self.log.warning("Fetch failed (attempt %d/%d) url=%s err=%s | backoff=%.1fs",
                                 attempt, self.cfg.retry_count, url, e, backoff)
                time.sleep(backoff)
        raise RuntimeError(f"Failed to fetch after retries: {url}")
