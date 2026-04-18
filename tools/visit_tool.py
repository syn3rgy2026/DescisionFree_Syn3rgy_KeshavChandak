# OWNER: Person 2
"""
visit_tool.py
-------------
Provides web browsing and search capabilities to the agent.

All functions are synchronous smolagents @tool functions.
Uses requests + BeautifulSoup for speed and reliability.
Playwright is reserved for fill_and_submit_form (JS-dependent).

Tools exported:
  visit_url            — fetch a URL and return clean article text
  search_web           — DuckDuckGo search, returns top result URLs
  get_page_links       — list all href links on a page
  fill_and_submit_form — fill and submit an HTML form (Playwright, always confirms)

NOTE: This file was separated from browser_tool.py which retains its
original Playwright-based async stubs (owned by Person 2 for JS navigation).
"""

import time
import json
import requests
from bs4 import BeautifulSoup
from smolagents import tool
from tools.human_confirm import ask_human_confirmation

# ── Constants ─────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# HTML tags that are purely navigation/chrome — strip them before reading
NOISE_TAGS = [
    "script", "style", "noscript", "nav", "footer", "header",
    "aside", "form", "iframe", "svg", "button", "advertisement",
    "cookie", "banner", "popup",
]

# Max characters returned per page — protects the LLM context window
MAX_PAGE_CHARS = 4000

# Polite delay between requests (seconds)
REQUEST_DELAY = 1


# ── Internal helpers ──────────────────────────────────────────────────

def _fetch_soup(url: str) -> BeautifulSoup | None:
    """
    Fetch a URL and return a BeautifulSoup object.
    Returns None on any network or HTTP error.
    """
    try:
        time.sleep(REQUEST_DELAY)
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.content, "html.parser")
    except Exception:
        return None


def _extract_clean_text(soup: BeautifulSoup) -> str:
    """
    Aggressively strip noise tags, then extract readable text.
    Prefers <main> or <article> blocks; falls back to <body>.
    """
    # Remove all noise tags in-place
    for tag in soup(NOISE_TAGS):
        tag.decompose()

    # Prefer semantic content blocks
    content_block = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id="content")
        or soup.find(id="main-content")
        or soup.find(class_="content")
        or soup.find(class_="article")
        or soup.body
    )

    if content_block is None:
        return "(no readable content found)"

    # Extract text, collapse excessive whitespace
    raw = content_block.get_text(separator="\n")
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    return "\n".join(lines)


# ── Public @tool functions ────────────────────────────────────────────

@tool
def visit_url(url: str) -> str:
    """Visit any URL and return only the clean, readable article text — navbars,
    footers, scripts, and CSS are stripped out. Output is capped at 4000
    characters to protect the agent's context window during deep research.

    Args:
        url: The full URL to visit (must start with http:// or https://).

    Returns:
        str: Clean article text from the page, or an error message.
    """
    soup = _fetch_soup(url)
    if soup is None:
        return f"Error: Could not fetch '{url}'. The site may be unreachable or blocking requests."

    text = _extract_clean_text(soup)

    if not text or len(text) < 50:
        return f"Warning: '{url}' returned very little readable content. It may be paywalled or JS-only."

    # Truncate to protect context window
    if len(text) > MAX_PAGE_CHARS:
        text = text[:MAX_PAGE_CHARS] + f"\n\n[...truncated — {len(text)} total chars]"

    return f"Content from {url}:\n\n{text}"


@tool
def get_page_links(url: str) -> str:
    """Get all hyperlinks found on a webpage. Useful for discovering related
    pages or articles to visit during research.

    Args:
        url: The full URL of the page to extract links from.

    Returns:
        str: Newline-separated list of absolute URLs found on the page.
    """
    soup = _fetch_soup(url)
    if soup is None:
        return f"Error: Could not fetch '{url}'."

    base = "/".join(url.split("/")[:3])  # e.g. https://example.com
    links = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        if href.startswith("http"):
            links.add(href)
        elif href.startswith("/"):
            links.add(base + href)

    if not links:
        return f"No links found on '{url}'."

    sorted_links = sorted(links)
    return f"Links found on {url} ({len(sorted_links)} total):\n\n" + "\n".join(sorted_links)


@tool
def fill_and_submit_form(url: str, form_data: str) -> str:
    """Fill and submit an HTML form on a webpage using a headless browser.
    form_data must be a JSON string of field names mapped to values,
    e.g. '{\"email\": \"user@example.com\", \"message\": \"Hello\"}'.
    ALWAYS asks for human confirmation before submitting — form submission
    is irreversible.

    Args:
        url: URL of the page containing the form.
        form_data: JSON string of field_name → value pairs to fill in.

    Returns:
        str: Success or failure message after submission attempt.
    """
    # Always confirm before submitting any form
    response = ask_human_confirmation(
        action=f"Fill and submit a form on: {url}",
        reason="Form submission can create accounts, send messages, or place orders.",
        risk_level="HIGH",
        details=json.dumps({"URL": url, "Fields": form_data}),
    )
    if response.strip().upper() != "YES":
        return f"Form submission cancelled by user. (Response: '{response}')"

    # Parse form data
    try:
        fields = json.loads(form_data)
    except json.JSONDecodeError as e:
        return f"Error: form_data is not valid JSON — {e}"

    # Use Playwright for form interaction
    try:
        import asyncio
        from playwright.async_api import async_playwright

        async def _submit():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=30000)

                for field_name, value in fields.items():
                    try:
                        locator = (
                            page.locator(f"[name='{field_name}']").first
                            or page.locator(f"#{field_name}").first
                        )
                        await locator.fill(str(value))
                    except Exception:
                        pass  # Skip fields that can't be found

                await page.locator("button[type=submit], input[type=submit]").first.click()
                await page.wait_for_load_state("networkidle", timeout=15000)
                result_text = await page.inner_text("body")
                await browser.close()
                return result_text[:1000]

        result = asyncio.run(_submit())
        return f"Form submitted successfully. Page response:\n\n{result}"

    except Exception as e:
        return f"Form submission failed: {e}"


# ── TEST BLOCK ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("TESTING VISIT TOOL")
    print("=" * 50 + "\n")

    print("--- Test 1: visit_url (example.com) ---")
    print(visit_url("https://example.com"))
    print()

    print("--- Test 2: search_web ---")
    print(search_web("smolagents python framework"))
    print()

    print("--- Test 3: get_page_links ---")
    print(get_page_links("https://example.com"))
    print()
