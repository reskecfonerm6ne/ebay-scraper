from __future__ import annotations

from bs4 import BeautifulSoup
from typing import List

from .models import Listing
from .extractors import parse_price, clean_text


def parse_search_results(html: str) -> List[Listing]:
    soup = BeautifulSoup(html, "html.parser")

    listings: List[Listing] = []
    # eBay commonly uses li.s-item for result cards
    for card in soup.select("li.s-item"):
        title_el = card.select_one(".s-item__title")
        link_el = card.select_one("a.s-item__link")
        price_el = card.select_one(".s-item__price")
        ship_el = card.select_one(".s-item__shipping, .s-item__logisticsCost")
        cond_el = card.select_one(".s-item__subtitle .SECONDARY_INFO")
        loc_el = card.select_one(".s-item__location")
        seller_el = card.select_one(".s-item__seller-info-text")
        meta_el = card.select_one(".s-item__dynamic .s-item__bids, .s-item__dynamic .s-item__watch-count")

        if not title_el or not link_el:
            continue

        title = clean_text(title_el.get_text())
        url = link_el.get("href") or ""
        if not title or title.lower() in {"shop on ebay"}:
            continue
        if not url:
            continue

        currency, price = parse_price(clean_text(price_el.get_text() if price_el else ""))

        listings.append(
            Listing(
                title=title,
                url=url,
                price=price,
                currency=currency,
                shipping=clean_text(ship_el.get_text() if ship_el else "" ) or None,
                condition=clean_text(cond_el.get_text() if cond_el else "" ) or None,
                location=clean_text(loc_el.get_text() if loc_el else "" ) or None,
                seller=clean_text(seller_el.get_text() if seller_el else "" ) or None,
                watchers_or_bids=clean_text(meta_el.get_text() if meta_el else "" ) or None,
            )
        )

    return listings


def parse_related_searches(html: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    related: List[str] = []

    # Related searches can appear in different blocks; try a few likely selectors.
    candidates = soup.select("a.srp-related-search__link, a.related-searches__item, a.srp-refine__link")
    for a in candidates:
        text = a.get_text(strip=True)
        if text and text not in related and len(related) < 12:
            related.append(text)

    return related
