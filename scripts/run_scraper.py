from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml
from rich.logging import RichHandler

from scraper.pipeline import EbayScraper, ScraperConfig
from scraper.pipeline import SearchPageResult  # type: ignore
from scraper.pipeline import Listing  # type: ignore
from scraper import models
from scraper import pipeline as outpipe


def load_settings(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def setup_logging(level: str, logfile: str) -> logging.Logger:
    Path(logfile).parent.mkdir(parents=True, exist_ok=True)
    handlers = [RichHandler(rich_tracebacks=True), logging.FileHandler(logfile, encoding="utf-8")]
    logging.basicConfig(
        level=getattr(logging, (level or "INFO").upper(), logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers,
    )
    return logging.getLogger("ebay")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ebay scraper (search pages)")
    p.add_argument("--config", default="config/settings.yaml", help="Path to YAML settings")
    p.add_argument("--query", required=True, help="Search query")
    p.add_argument("--pages", type=int, default=1, help="Number of result pages to scrape")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings(args.config)

    s_cfg = settings.get("scraper", {}) or {}
    o_cfg = settings.get("output", {}) or {}
    l_cfg = settings.get("logging", {}) or {}

    log = setup_logging(l_cfg.get("level", "INFO"), l_cfg.get("file", "logs/scraper.log"))

    cfg = ScraperConfig(
        base_url=str(s_cfg.get("base_url") or "https://www.ebay.com/sch/i.html"),
        user_agent=str(s_cfg.get("user_agent") or "Mozilla/5.0"),
        headless=bool(s_cfg.get("headless", True)),
        request_delay_seconds=float(s_cfg.get("request_delay_seconds") or 1.2),
        retry_count=int(s_cfg.get("retry_count") or 3),
        retry_backoff_seconds=float(s_cfg.get("retry_backoff_seconds") or 2.0),
        timeout_ms=int(s_cfg.get("timeout_ms") or 30000),
    )

    out_dir = str(o_cfg.get("dir") or "output")
    formats: List[str] = list(o_cfg.get("formats") or ["jsonl"])

    scraper = EbayScraper(cfg, logger=log)
    results = scraper.scrape(args.query, pages=args.pages)

    stamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    safe_q = "".join([c if c.isalnum() else "-" for c in args.query.lower()]).strip("-")[:60] or "query"

    # Flatten listings for saving
    flat_rows = []
    flat_listings = []
    related_union = []
    for page_res in results:
        for r in page_res.related_searches:
            if r not in related_union:
                related_union.append(r)
        for it in page_res.listings:
            d = it.to_dict()
            d["query"] = page_res.query
            d["page"] = page_res.page
            flat_rows.append(d)
            flat_listings.append(it)

    if "jsonl" in [f.lower() for f in formats]:
        outpipe.write_jsonl(out_dir, f"{safe_q}_{stamp}.jsonl", flat_rows, log)

    if "csv" in [f.lower() for f in formats]:
        outpipe.write_csv(out_dir, f"{safe_q}_{stamp}.csv", flat_listings, log)

    # Write related searches
    related_path = Path(out_dir) / f"{safe_q}_{stamp}_related_searches.json"
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    related_path.write_text(yaml.safe_dump({"query": args.query, "related": related_union}, sort_keys=False), encoding="utf-8")
    log.info("Wrote related searches: %s", related_path)

    log.info("Done. Listings captured: %d", len(flat_listings))


if __name__ == "__main__":
    main()
