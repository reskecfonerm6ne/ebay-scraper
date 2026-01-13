# ebay scraper

A small, production-style **ebay scraper** that collects structured listing data from eBay search pages with pacing, retries, and clean outputs.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install --with-deps
```

Run:

```bash
python scripts/run_scraper.py --query "wireless earbuds" --pages 3
```

Outputs are written to `output/`.
