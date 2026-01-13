from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import sync_playwright, Browser, Page


@dataclass(frozen=True)
class BrowserConfig:
    user_agent: str
    headless: bool = True
    timeout_ms: int = 30000


class BrowserSession:
    def __init__(self, cfg: BrowserConfig, logger: Optional[logging.Logger] = None) -> None:
        self.cfg = cfg
        self.log = logger or logging.getLogger(__name__)
        self._pw = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None

    def __enter__(self) -> "BrowserSession":
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self.cfg.headless)
        context = self._browser.new_context(user_agent=self.cfg.user_agent)
        self._page = context.new_page()
        self._page.set_default_timeout(self.cfg.timeout_ms)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self._browser:
                self._browser.close()
        finally:
            if self._pw:
                self._pw.stop()

    @property
    def page(self) -> Page:
        if not self._page:
            raise RuntimeError("BrowserSession is not started")
        return self._page

    def get_html(self, url: str) -> str:
        self.log.debug("GET %s", url)
        self.page.goto(url, wait_until="domcontentloaded")
        # A short wait helps on pages that lazy-render parts of the DOM.
        time.sleep(0.3)
        return self.page.content()
