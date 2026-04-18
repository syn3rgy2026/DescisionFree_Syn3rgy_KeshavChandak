# OWNER: Person 2
"""
scraper_tool.py
---------------
Unified smart web scraper with automatic fallback.
Tries static scraping first (fast), falls back to dynamic Playwright (slow but complete).
"""

import requests
from bs4 import BeautifulSoup
import time
import asyncio
from playwright.async_api import async_playwright
from smolagents import tool


def _scrape_static(url: str, delay: int = 2) -> tuple[bool, str]:
    """Internal: Try static scraping with requests + BeautifulSoup.
    Returns (success, content)
    """
    try:
        time.sleep(delay)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Check if we got meaningful content (more than just a few words)
        if len(text.strip()) > 100:
            return True, text
        else:
            return False, "Minimal content detected, may need dynamic scraping"
            
    except Exception as e:
        return False, str(e)


async def _scrape_dynamic(url: str, wait_time: int = 3) -> str:
    """Internal: Scrape with Playwright for JavaScript-rendered sites."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until='networkidle', timeout=60000)
            except Exception:
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            await asyncio.sleep(wait_time)
            
            text_content = await page.evaluate('''() => {
                const scripts = document.querySelectorAll('script, style, noscript');
                scripts.forEach(el => el.remove());
                return document.body.innerText;
            }''')
            
            await browser.close()
            return text_content.strip()
            
    except Exception as e:
        return f"Dynamic scraping failed: {str(e)}"


@tool
def scrape_website(url: str, force_dynamic: bool = False) -> str:
    """
    Smart web scraper that automatically handles both static and JavaScript-rendered websites.
    
    This tool first tries fast static scraping. If that fails or returns minimal content,
    it automatically falls back to dynamic scraping with a headless browser.
    
    Args:
        url: The full URL of the website to scrape
        force_dynamic: Set to True to skip static and use dynamic scraping directly (default: False)
    
    Returns:
        str: Clean text content extracted from the webpage
    """
    if not force_dynamic:
        # Try static scraping first (fast)
        success, content = _scrape_static(url, delay=2)
        
        if success:
            return f"Successfully scraped {url} (static method)\n\nContent:\n{content[:5000]}"
    
    # Fall back to dynamic scraping (or if forced)
    try:
        content = asyncio.run(_scrape_dynamic(url, wait_time=3))
        
        if "failed" in content.lower():
            return f"Error scraping {url}: {content}"
        
        return f"Successfully scraped {url} (dynamic method)\n\nContent:\n{content[:5000]}"
        
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"


@tool
def scrape_website_structured(url: str, selector: str, force_dynamic: bool = False) -> str:
    """
    Extract specific elements from a website using CSS selectors.
    Automatically handles both static and JavaScript-rendered sites.
    
    Args:
        url: The full URL of the website to scrape
        selector: CSS selector to target elements (e.g., 'h1', '.article-title', '#main-content')
        force_dynamic: Set to True to use dynamic scraping directly (default: False)
    
    Returns:
        str: Extracted content from the specified elements
    """
    if not selector:
        return "Error: Please provide a CSS selector to extract specific elements"
    
    # Try static first
    if not force_dynamic:
        try:
            time.sleep(2)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            elements = soup.select(selector)
            
            if elements:
                results = []
                for i, elem in enumerate(elements[:50], 1):
                    text = elem.get_text(strip=True)
                    if text:
                        results.append(f"{i}. {text}")
                
                if results:
                    return f"Found {len(results)} elements matching '{selector}' on {url} (static):\n\n" + "\n".join(results)
        except:
            pass  # Fall through to dynamic
    
    # Fall back to dynamic
    async def scrape_dynamic_selector():
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = await context.new_page()
                
                try:
                    await page.goto(url, wait_until='networkidle', timeout=60000)
                except Exception:
                    await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                await asyncio.sleep(3)
                
                elements = await page.query_selector_all(selector)
                
                if not elements:
                    await browser.close()
                    return f"No elements found matching selector '{selector}' on {url}"
                
                results = []
                for i, elem in enumerate(elements[:50], 1):
                    text = await elem.inner_text()
                    if text.strip():
                        results.append(f"{i}. {text.strip()}")
                
                await browser.close()
                
                return f"Found {len(results)} elements matching '{selector}' on {url} (dynamic):\n\n" + "\n".join(results)
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    try:
        return asyncio.run(scrape_dynamic_selector())
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"


# Test block
if __name__ == "__main__":
    print("Testing smart scraper with static site...")
    result = scrape_website("https://example.com")
    print(result)
    print("\n" + "="*50 + "\n")
    
    print("Testing smart scraper with JavaScript site...")
    result = scrape_website("https://datahack.djss4ds.in/")
    print(result)
    print("\n" + "="*50 + "\n")
    
    print("Testing structured scraping...")
    result = scrape_website_structured("https://example.com", "h1")
    print(result)
