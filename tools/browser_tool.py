# OWNER: Person 2
"""
browser_tool.py
---------------
Provides web browsing capabilities to the agent using Playwright.
Supports navigating to URLs, extracting page text, clicking elements,
typing into inputs, checking element existence, and taking screenshots.

All functions run Playwright synchronously via asyncio.run() so they
work as regular smolagents @tool functions.
"""

import asyncio
import os
from datetime import datetime
from smolagents import tool


def _ensure_output_dir():
    os.makedirs("./output", exist_ok=True)


async def _run_in_browser(action_fn, url, timeout=30000):
    """Shared helper: launch browser, navigate, run action_fn(page), close."""
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        except Exception:
            await page.goto(url, timeout=timeout)
        await page.wait_for_timeout(1500)
        result = await action_fn(page)
        await browser.close()
        return result


@tool
def browser_navigate(url: str) -> str:
    """Open a URL in a headless browser and return the visible text content.
    Use this to read a webpage, check if a site loads, or verify a deployed app.

    Args:
        url: Fully-qualified URL to navigate to (e.g. https://example.com).

    Returns:
        str: The visible text content of the page (first 5000 chars).
    """
    async def action(page):
        text = await page.inner_text("body")
        return text[:5000] if text else "(empty page)"
    try:
        return asyncio.run(_run_in_browser(action, url))
    except Exception as e:
        return f"ERROR navigating to {url}: {e}"


@tool
def browser_click(url: str, selector: str) -> str:
    """Navigate to a URL, click an element by CSS selector, and return the
    resulting page text. Useful for clicking buttons, links, or menu items.

    Args:
        url: Page URL to load.
        selector: CSS selector of the element to click (e.g. 'button#submit', 'a.nav-link').

    Returns:
        str: Page text after clicking (first 5000 chars).
    """
    async def action(page):
        await page.click(selector, timeout=10000)
        await page.wait_for_timeout(2000)
        text = await page.inner_text("body")
        return text[:5000] if text else "(empty page after click)"
    try:
        return asyncio.run(_run_in_browser(action, url))
    except Exception as e:
        return f"ERROR clicking '{selector}' on {url}: {e}"


@tool
def browser_type(url: str, selector: str, text: str) -> str:
    """Navigate to a URL, type text into an input field, and return the page text.
    Useful for filling forms, search boxes, or login fields.

    Args:
        url: Page URL to load.
        selector: CSS selector of the input element (e.g. 'input[name=email]', '#search').
        text: Text to type into the field.

    Returns:
        str: Page text after typing (first 5000 chars).
    """
    async def action(page):
        await page.fill(selector, text, timeout=10000)
        await page.wait_for_timeout(1000)
        body = await page.inner_text("body")
        return body[:5000] if body else "(page after typing)"
    try:
        return asyncio.run(_run_in_browser(action, url))
    except Exception as e:
        return f"ERROR typing into '{selector}' on {url}: {e}"


@tool
def browser_screenshot(url: str, output_path: str = "") -> str:
    """Take a full-page screenshot of a URL. Saves to output/ by default.
    Use this to visually verify a webpage, debug layout issues, or document results.

    Args:
        url: URL to screenshot.
        output_path: Optional custom save path. If empty, saves to output/screenshot_TIMESTAMP.png.

    Returns:
        str: Absolute path to the saved screenshot.
    """
    async def action(page):
        _ensure_output_dir()
        if output_path:
            save_path = output_path
        else:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"./output/screenshot_{ts}.png"
        await page.screenshot(path=save_path, full_page=True)
        return os.path.abspath(save_path)
    try:
        result = asyncio.run(_run_in_browser(action, url))
        return f"Screenshot saved: {result}"
    except Exception as e:
        return f"ERROR taking screenshot of {url}: {e}"


@tool
def browser_check_element(url: str, selector: str) -> str:
    """Check if a specific element exists on a webpage and return its text.
    Useful for verifying that a deployed app shows the right content,
    or that a form/button/heading exists.

    Args:
        url: Page URL to check.
        selector: CSS selector to look for (e.g. 'h1', '.error', '#app').

    Returns:
        str: Element text if found, or 'NOT FOUND' message.
    """
    async def action(page):
        el = await page.query_selector(selector)
        if el:
            text = await el.inner_text()
            return f"FOUND '{selector}': {text[:1000]}"
        else:
            return f"NOT FOUND: no element matching '{selector}'"
    try:
        return asyncio.run(_run_in_browser(action, url))
    except Exception as e:
        return f"ERROR checking '{selector}' on {url}: {e}"


@tool
def browser_extract_links(url: str) -> str:
    """Extract all hyperlinks from a webpage. Returns a newline-separated list
    of link text and href pairs.

    Args:
        url: Page URL to extract links from.

    Returns:
        str: All links found, formatted as 'text → href' (max 100 links).
    """
    async def action(page):
        links = await page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({text: e.innerText.trim().substring(0,80), href: e.href})).slice(0,100)"
        )
        if not links:
            return "No links found on page."
        lines = [f"{l['text']} → {l['href']}" for l in links if l['href']]
        return "\n".join(lines)
    try:
        return asyncio.run(_run_in_browser(action, url))
    except Exception as e:
        return f"ERROR extracting links from {url}: {e}"


BROWSER_TOOLS = [
    browser_navigate,
    browser_click,
    browser_type,
    browser_screenshot,
    browser_check_element,
    browser_extract_links,
]
