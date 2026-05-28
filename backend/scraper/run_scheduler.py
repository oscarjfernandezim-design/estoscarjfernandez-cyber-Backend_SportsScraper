"""
Scheduler for periodic scraping jobs. Defaults to dry-run; enable persistence with
environment variable `ENABLE_PERSIST=1`.

Usage:
  python run_scheduler.py --interval 3600 --brands adidas,nike,puma

This uses APScheduler to run the job at fixed intervals.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import Any

from apscheduler.schedulers.blocking import BlockingScheduler

from .scrappy_adidad import CATEGORIES, scrape_brand_category, save_products_to_db


def job_run(brands: list[str], max_items: int, persist: bool, output_dir: str, pages: int = 2) -> None:
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    all_products: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}

    for brand in brands:
        summary[brand] = {}
        for category in CATEGORIES:
            prods, src = scrape_brand_category(brand, category, max_items=max_items, pages=pages)
            summary[brand][category] = {"count": len(prods), "source_url": src}
            all_products.extend(prods)
            if persist and prods:
                save_products_to_db(prods)

    out = {"timestamp": timestamp, "summary": summary, "count": len(all_products)}
    os.makedirs(output_dir, exist_ok=True)
    outfile = os.path.join(output_dir, f"scrape_{timestamp}.json")
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump({**out, "products": all_products}, f, indent=2, ensure_ascii=False)
    print(f"[{datetime.utcnow().isoformat()}] Job finished: wrote {len(all_products)} products to {outfile}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run periodic scraping jobs")
    parser.add_argument("--interval", type=int, default=3600, help="Interval seconds between runs")
    parser.add_argument("--brands", type=str, default="adidas,nike,puma", help="Comma-separated brands to run")
    parser.add_argument("--max-items", type=int, default=5, help="Max items per brand/category")
    parser.add_argument("--pages", type=int, default=2, help="Pages per search URL to scrape")
    parser.add_argument("--output-dir", type=str, default="scrape_runs", help="Directory to write run outputs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    brands = [b.strip().lower() for b in args.brands.split(",") if b.strip()]
    persist = os.getenv("ENABLE_PERSIST", "0") in ("1", "true", "True")

    scheduler = BlockingScheduler()
    scheduler.add_job(lambda: job_run(brands, args.max_items, persist, args.output_dir, pages=args.pages), "interval", seconds=args.interval)
    print(f"Scheduler started: interval={args.interval}s brands={brands} persist={persist}")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped")


if __name__ == "__main__":
    main()
