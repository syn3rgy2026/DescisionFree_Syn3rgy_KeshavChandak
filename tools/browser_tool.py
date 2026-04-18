# OWNER: Person 2
"""
browser_tool.py
---------------
Provides web browsing capabilities to the agent using Playwright and
browser-use. Supports navigating to URLs, extracting page text, clicking
elements, and taking screenshots.
"""

from playwright.async_api import async_playwright


async def navigate(url: str) -> str:
    """
    Open a URL in a headless browser and return the page's text content.

    Args:
        url (str): Fully-qualified URL to navigate to.

    Returns:
        str: Visible text content of the loaded page.
    """
    raise NotImplementedError("Person 2 will implement this")


async def click(selector: str, url: str) -> str:
    """
    Navigate to a URL, click an element matching the CSS selector,
    and return the resulting page text.

    Args:
        selector (str): CSS selector of the element to click.
        url (str): Page URL to load before clicking.

    Returns:
        str: Page text after the click action.
    """
    raise NotImplementedError("Person 2 will implement this")


async def screenshot(url: str, output_path: str) -> str:
    """
    Capture a full-page screenshot of the given URL.

    Args:
        url (str): Page to screenshot.
        output_path (str): File path to save the PNG screenshot.

    Returns:
        str: Absolute path to the saved screenshot file.
    """
    raise NotImplementedError("Person 2 will implement this")


async def extract_links(url: str) -> list:
    """
    Return all hyperlinks found on the given page.

    Args:
        url (str): Page URL to scrape links from.

    Returns:
        list[str]: List of href values found on the page.
    """
    raise NotImplementedError("Person 2 will implement this")
