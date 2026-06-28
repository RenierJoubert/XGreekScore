import asyncio
import argparse

from scraper import scrape_discussions

DEFAULT_PAGES = 500
DEFAULT_DB = "greekrank.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape GreekRank discussions into SQLite.")
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
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="After scraping, mark posts absent from the listing as deleted. Only reliable on a full scrape.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(f"Starting scrape — pages: {args.pages}, db: {args.db}, sweep: {args.sweep}")
    asyncio.run(scrape_discussions(pages=args.pages, db_path=args.db, sweep=args.sweep))


if __name__ == "__main__":
    main()
