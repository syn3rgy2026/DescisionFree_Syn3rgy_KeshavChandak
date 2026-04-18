# OWNER: Person 2
"""
web_screenshot.py
-----------------
Captures full-page screenshots of websites using Playwright.
"""

import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright
from smolagents import tool


@tool
def capture_website_screenshot(url: str, output_path: str = None) -> str:
    """
    Capture a full-page screenshot of any website.
    
    This tool launches a headless browser, navigates to the URL, and captures
    a full-page screenshot. Useful for visual verification or documentation.
    
    Args:
        url: The full URL of the website to screenshot
        output_path: Optional custom path to save the screenshot. 
                    If not provided, saves to ./output/screenshot_TIMESTAMP.png
    
    Returns:
        str: Path to the saved screenshot file
    """
    async def capture():
        try:
            # Determine save path
            if not output_path:
                os.makedirs('./output', exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                save_path = f'./output/screenshot_{timestamp}.png'
            else:
                save_path = output_path
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
                
                # Navigate with fallback strategy
                try:
                    await page.goto(url, wait_until='networkidle', timeout=60000)
                except Exception:
                    await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # Wait for page to stabilize
                await asyncio.sleep(2)
                
                # Take full page screenshot
                await page.screenshot(path=save_path, full_page=True)
                
                await browser.close()
                
                abs_path = os.path.abspath(save_path)
                return f"Screenshot saved successfully at: {abs_path}"
                
        except Exception as e:
            return f"Error taking screenshot of {url}: {str(e)}"
    
    return asyncio.run(capture())


# Test block
if __name__ == "__main__":
    print("Testing screenshot capture...")
    result = capture_website_screenshot("https://example.com")
    print(result)
