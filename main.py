import asyncio
import argparse

from scraper import scrape_discussions

DEFAULT_PAGES = 500
DEFAULT_DB = "greekrank.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape into SQLite.")
    parser.add_argument(
        "--pages",
        type=int,
        default=DEFAULT_PAGES,
        help=f"Number of listing pages to scrape (default: {DEFAULT_PAGES})",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=DEFAULT_DB,
        help=f"Path to the SQLite database file (default: {DEFAULT_DB})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Starting scrape — pages: {args.pages}, db: {args.db}")
    asyncio.run(scrape_discussions(pages=args.pages, db_path=args.db))


if __name__ == "__main__":
    main()
