import asyncio
import random

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from utils import get_text, get_attr
from db import init_db, insert_post, insert_reply, mark_deleted_posts

BASE_URL = "https://www.greekrank.net/uni/489/discussion/"

CONCURRENCY = 5


async def scrape_post_page(browser, link: str) -> tuple[str, str, list[dict]]:
    page = await browser.new_page()

    try:
        await page.goto(link, timeout=60_000, wait_until="domcontentloaded")
    except Exception as e:
        print(f"    ! failed to load {link}: {e}")
        await page.close()
        return "Unknown Date", "No content", []

    try:
        await page.wait_for_function(
            """() => {
                const ps = document.querySelectorAll('.discussion-box-content p');
                return [...ps].some(p => (p.innerText || '').trim().length > 0);
            }""",
            timeout=20_000,
        )
    except PWTimeout:
        pass

    # Original post is the first discussion-box on the page
    first_box = await page.query_selector("div.discussion-box.clearfix")

    content = "No content"
    if first_box:
        content_el = await first_box.query_selector(".discussion-box-content")
        if content_el:
            paragraphs = await content_el.query_selector_all("p")
            parts = [t for p in paragraphs if (t := await get_text(p))]
            content = "\n\n".join(parts) if parts else (await get_text(content_el))

    date = "Unknown Date"
    if first_box:
        date_el = await first_box.query_selector("time")
        if date_el:
            date = (await get_attr(date_el, "datetime")) or (await get_text(date_el)) or "Unknown Date"

    # Replies are each wrapped in div.discussion-box-reply
    replies = []
    for reply_box in await page.query_selector_all("div.discussion-box-reply"):
        head = await reply_box.query_selector("h5.discussion-box-head")
        author = "Anonymous"
        if head:
            author_span = await head.query_selector("span span span")
            if author_span:
                author = await get_text(author_span)

        time_el = await reply_box.query_selector("h5.discussion-box-head time")
        reply_date = "Unknown Date"
        if time_el:
            reply_date = (await get_attr(time_el, "datetime")) or (await get_text(time_el))

        content_el = await reply_box.query_selector(".discussion-box-content p")
        reply_content = (await get_text(content_el)) if content_el else ""

        if reply_content:
            replies.append({"author": author, "date": reply_date, "content": reply_content})

    await page.close()
    return date, content, replies


async def scrape_and_save(sem, browser, conn, title, link, idx):
    async with sem:
        print(f"  [{idx}] {title}")
        date, content, replies = await scrape_post_page(browser, link)

        post_id = insert_post(conn, title, link, date, content)
        if post_id is None:
            print(f"  [{idx}] ~ already in DB, skipping")
            return

        for reply in replies:
            insert_reply(conn, post_id, reply["author"], reply["date"], reply["content"])

        print(f"  [{idx}] saved (post_id={post_id}, {len(replies)} replies)")


async def scrape_discussions(pages: int, db_path: str, sweep: bool = False) -> None:
    conn = init_db(db_path)
    sem = asyncio.Semaphore(CONCURRENCY)
    found_links: set[str] = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        listing_page = await browser.new_page()

        for page_num in range(1, pages + 1):
            url = BASE_URL if page_num == 1 else f"{BASE_URL}page-{page_num}/"
            print(f"\n[Page {page_num}] Fetching {url} ...")

            try:
                await listing_page.goto(url, timeout=60_000, wait_until="domcontentloaded")
                await listing_page.wait_for_selector("h5.discussion-box-head a", timeout=15_000)
            except Exception as e:
                print(f"  ! failed to load listing page {page_num}: {e}")
                continue

            boxes = await listing_page.query_selector_all("div.discussion-box.clearfix")
            print(f"  Found {len(boxes)} discussions — scraping {CONCURRENCY} at a time")

            tasks = []
            for idx, box in enumerate(boxes, start=1):
                a = await box.query_selector("h5.discussion-box-head a")
                title = await get_text(a) if a else "No Title"
                link = await get_attr(a, "href") if a else ""
                if link and not link.startswith("http"):
                    link = "https://www.greekrank.net" + link
                if not link:
                    continue
                found_links.add(link)
                tasks.append(scrape_and_save(sem, browser, conn, title, link, idx))

            await asyncio.gather(*tasks)
            await asyncio.sleep(random.uniform(0.5, 1.5))

        await browser.close()

    if sweep:
        print(f"\n[Deletion sweep] {len(found_links)} links seen across {pages} pages")
        newly_deleted, restored = mark_deleted_posts(conn, found_links)
        print(f"  {newly_deleted} newly marked deleted, {restored} restored")
    else:
        print(f"\n[Deletion sweep] skipped (run with --sweep on a full scrape)")

    conn.close()
    print(f"\nDone. Data saved to {db_path}")
