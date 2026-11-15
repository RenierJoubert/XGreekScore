import asyncio
import random
from urllib.parse import urljoin

from playwright.async_api import async_playwright

from db import init_db, insert_post, insert_reply, mark_deleted_posts

BASE_URL = "https://www.greekrank.net/uni/489/discussion/"

CONCURRENCY = 5

# Tells the scraper to stop after 3 empty pages
EMPTY_PAGE_LIMIT = 3

# In case the site is stuck in a loop
MAX_REPLY_PAGES = 50


async def get_text(el) -> str:
    """Return stripped inner text of an html element, or empty string on failure."""
    try:
        return ((await el.inner_text()) or "").strip()
    except Exception:
        return ""


async def get_attr(el, attr: str) -> str:
    """Returns the given attribute of a post, or empty string on failure."""
    try:
        return ((await el.get_attribute(attr)) or "").strip()
    except Exception:
        return ""


async def read_date(time_el) -> str:
    if time_el is None:
        return "Unknown Date"
    return (await get_attr(time_el, "datetime")) or (await get_text(time_el)) or "Unknown Date"


# Takes a page and returns its date and text
async def extract_original_post(page) -> tuple[str, str]:
    # A page has a root post and its replies. The original post is root (first) discussion box
    first_box = await page.query_selector("div.discussion-box.clearfix")
    if not first_box:
        return "Unknown Date", "No content"

    date = await read_date(await first_box.query_selector("time"))

    content = "No content"
    content_el = await first_box.query_selector(".discussion-box-content")
    if content_el:
        paragraphs = await content_el.query_selector_all("p")
        parts = [text for p in paragraphs if (text := await get_text(p))]
        content = "\n\n".join(parts) if parts else await get_text(content_el)

    return date, content


# Takes a page and returns a list of dict representative of the posts replies,
# each dict is a reply with 3 keys: author, date, and content.
async def extract_replies(page) -> list[dict]:
    replies = []
    # Replies are each wrapped in div.discussion-box-reply
    for reply_box in await page.query_selector_all("div.discussion-box-reply"):
        content_el = await reply_box.query_selector(".discussion-box-content p")
        content = await get_text(content_el) if content_el else ""
        if not content:
            continue

        author_el = await reply_box.query_selector("h5.discussion-box-head span span span")
        author = await get_text(author_el) if author_el else "Anonymous"
        date = await read_date(await reply_box.query_selector("h5.discussion-box-head time"))

        replies.append({"author": author, "date": date, "content": content})
    return replies

# Does the given page contain a link to the input url
async def has_link_to(page, url: str) -> bool:
    return await page.evaluate("url => [...document.links].some(a => a.href === url)", url)


# Handles a full post. Given a post url, returns a tuple of its date,
# content, and replies.
async def scrape_post_page(browser, link: str) -> tuple[str, str, list[dict]]:
    page = await browser.new_page()
    
    # make sure the page loads properly
    try:
        try:
            await page.goto(link, timeout=60_000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"failed to load {link}: {e}")
            return "Unknown Date", "No content", []

        date, content = await extract_original_post(page)
        replies = await extract_replies(page)

        # Replies can also span multiple pages, so iterate through all the replies
        page_num = 1
        while page_num < MAX_REPLY_PAGES:
            next_url = urljoin(link, f"page-{page_num + 1}/")
            # Have we gone through all the pages
            if not await has_link_to(page, next_url):
                break
            page_num += 1
            try:
                await page.goto(next_url, timeout=60_000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"failed to load reply page {page_num} of {link}: {e}")
                break
            replies += await extract_replies(page)

        return date, content, replies
    finally:
        await page.close()


# Given the semaphore, playwright browser, db, post title, and post url,
# scrape the post and update the db
async def scrape_and_save(sem, browser, conn, title, link):
    # wait for one of the 5 passes to open
    async with sem:
        # scrape the post
        date, content, replies = await scrape_post_page(browser, link)

        # insert the post and its replies
        post_id = insert_post(conn, title, link, date, content)
        for reply in replies:
            insert_reply(conn, post_id, reply["author"], reply["date"], reply["content"])


async def scrape_discussions(pages: int, db_path: str, sweep: bool = False) -> None:
   
    # link db, initialize semaphore with desired concurrency, initialize empty set of new urls
    conn = init_db(db_path)
    sem = asyncio.Semaphore(CONCURRENCY)
    found_links: set[str] = set()

    # reached_end = True when consecutive_empty = 3
    reached_end = False
    consecutive_empty = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        listing_page = await browser.new_page()

        # Iterate over all discussion posts
        for page_num in range(1, pages + 1):
            url = f"{BASE_URL}page-{page_num}/"
            print(f"\n[Page {page_num}] Fetching {url} ...")

            try:
                await listing_page.goto(url, timeout=60_000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"failed to load listing page {page_num}: {e}")
                break
            
            # boxes = every post on the current page
            boxes = await listing_page.query_selector_all("div.discussion-box.clearfix")
            if not boxes: # if the page has no posts
                consecutive_empty += 1
                print(f" no discussions ({consecutive_empty}/{EMPTY_PAGE_LIMIT} consecutive empty pages)")
                # If we have reached the end of the site
                if consecutive_empty >= EMPTY_PAGE_LIMIT:
                    print("reached end of listing")
                    reached_end = True
                    break
                continue

            consecutive_empty = 0
            print(f"Found {len(boxes)} posts, scraping {CONCURRENCY} at a time")

            # For each listing page, each post is a task
            tasks = []
            for box in boxes:

                # get the title link of the post
                a = await box.query_selector("h5.discussion-box-head a")
                href = await get_attr(a, "href") if a else ""
                if not href:
                    continue

                # get the full url of the post
                link = urljoin(BASE_URL, href)
                # get the title 
                title = await get_text(a)
                # record the post is still on the site
                found_links.add(link)
                # scrape this post and update the db
                tasks.append(scrape_and_save(sem, browser, conn, title, link))

            # unpacks the list of tasks (posts) and runs scrape and save with human timing
            await asyncio.gather(*tasks)
            await asyncio.sleep(random.uniform(0.5, 1.5))

        await browser.close()

    # If --sweep argument, update user on if end of listing was reached, number of links seen, 
    # number of newly deleted posts, number of restored posts, or if the sweep was not accomplished
    if sweep:
        end_note = "reached end of listing" if reached_end else "did not reach end of listing"
        print(f"\n Deletion sweep {len(found_links)} links seen ({end_note})")
        newly_deleted, restored = mark_deleted_posts(conn, found_links, reached_end)
        print(f"  {newly_deleted} newly marked deleted, {restored} restored")
    else:
        print("\n Deletion sweep skipped, run with --sweep on a full scrape")

    conn.close()
    print(f"\n Data saved to {db_path}")
