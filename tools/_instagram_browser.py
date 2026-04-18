#!/usr/bin/env python3
"""
_instagram_browser.py
---------------------
Standalone script for Instagram browser automation via Playwright.
Called as a subprocess by instagram_tool.py to avoid threading conflicts.

Usage:
    python _instagram_browser.py login
    python _instagram_browser.py post <image_path> <caption>
"""

import sys
import os
import json
import time

COOKIE_FILE = os.path.join(os.path.dirname(__file__), ".instagram_cookies.json")


def do_login():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Load existing cookies if available
        if os.path.exists(COOKIE_FILE):
            with open(COOKIE_FILE, "r") as f:
                cookies = json.load(f)
            context.add_cookies(cookies)

        page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        time.sleep(4)

        # Dismiss cookie banner if present
        try:
            btns = page.locator("button:has-text('Allow essential and optional cookies')")
            if btns.count() > 0 and btns.first.is_visible(timeout=3000):
                btns.first.click()
                time.sleep(1)
        except Exception:
            pass

        # Check if already logged in
        already_in = False
        try:
            if page.locator("svg[aria-label='Home']").is_visible(timeout=5000):
                already_in = True
        except Exception:
            pass

        if not already_in:
            # Wait for user to log in — poll every 3 seconds for up to 5 minutes
            print("WAITING_FOR_LOGIN", flush=True)
            deadline = time.time() + 300  # 5 min max
            while time.time() < deadline:
                try:
                    if page.locator("svg[aria-label='Home']").is_visible(timeout=2000):
                        already_in = True
                        break
                except Exception:
                    pass
                time.sleep(3)

        if already_in:
            # Save cookies for future use
            cookies = context.cookies()
            with open(COOKIE_FILE, "w") as f:
                json.dump(cookies, f)
            print(json.dumps({"status": "success", "message": "Instagram login successful"}))
        else:
            print(json.dumps({"status": "failed", "message": "Login timed out after 5 minutes"}))

        browser.close()


def do_post(image_path, caption):
    from playwright.sync_api import sync_playwright

    if not os.path.exists(image_path):
        print(json.dumps({"status": "failed", "message": f"Image not found: {image_path}"}))
        return

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()

        # Load saved cookies
        if os.path.exists(COOKIE_FILE):
            with open(COOKIE_FILE, "r") as f:
                cookies = json.load(f)
            context.add_cookies(cookies)
        else:
            print(json.dumps({"status": "auth_required", "message": "No saved session. Call login first."}))
            browser.close()
            return

        page = context.new_page()
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        time.sleep(4)

        # Dismiss "Turn on Notifications" popup if it appears
        try:
            not_now_btn = page.locator("button:has-text('Not Now')")
            if not_now_btn.count() > 0 and not_now_btn.first.is_visible(timeout=4000):
                not_now_btn.first.click()
                time.sleep(1)
        except Exception:
            pass

        # Verify we're logged in
        try:
            page.locator("svg[aria-label='Home']").wait_for(timeout=10000)
        except Exception:
            print(json.dumps({"status": "auth_required", "message": "Session expired. Login again."}))
            browser.close()
            return

        try:
            # Click "New Post" / Create button
            try:
                create_btn = page.locator("svg[aria-label='New post']").first
                create_btn.click()
            except Exception:
                # Fallback: look for the create link in nav
                page.locator("[aria-label='New post']").first.click()
            time.sleep(3)

            # Upload the image
            file_input = page.locator("input[type='file']").first
            file_input.set_input_files(image_path)
            time.sleep(4)

            # Click Next (crop screen)
            try:
                page.locator("div[role='button']:has-text('Next')").first.click()
                time.sleep(2)
            except Exception:
                pass

            # Click Next (filter screen)
            try:
                page.locator("div[role='button']:has-text('Next')").first.click()
                time.sleep(2)
            except Exception:
                pass

            # Type caption
            try:
                caption_area = page.locator("div[aria-label='Write a caption...']").first
                caption_area.click()
                page.keyboard.type(caption, delay=20)
                time.sleep(1)
            except Exception:
                try:
                    caption_area = page.locator("textarea[aria-label='Write a caption...']").first
                    caption_area.fill(caption)
                except Exception:
                    pass

            # Click Share — aggressive multi-strategy approach
            share_clicked = False
            time.sleep(2)

            # Strategy 1: XPath — find any element whose text is exactly "Share"
            try:
                share_el = page.locator("xpath=//div[text()='Share']").first
                if share_el.is_visible(timeout=3000):
                    share_el.click(force=True)
                    share_clicked = True
            except Exception:
                pass

            # Strategy 2: XPath — look for a span with "Share" text
            if not share_clicked:
                try:
                    share_el = page.locator("xpath=//span[text()='Share']").first
                    if share_el.is_visible(timeout=2000):
                        share_el.click(force=True)
                        share_clicked = True
                except Exception:
                    pass

            # Strategy 3: Use JavaScript to find and click Share
            if not share_clicked:
                try:
                    share_clicked = page.evaluate("""() => {
                        // Look through all elements for the Share button
                        const elements = document.querySelectorAll('div[role="button"], button, span, div');
                        for (const el of elements) {
                            const text = el.textContent.trim();
                            if (text === 'Share' && el.offsetParent !== null) {
                                el.click();
                                return true;
                            }
                        }
                        return false;
                    }""")
                except Exception:
                    share_clicked = False

            # Strategy 4: Playwright CSS text selector with force click
            if not share_clicked:
                css_selectors = [
                    "div[role='button']:has-text('Share')",
                    "button:has-text('Share')",
                    "[role='button'] >> text=Share",
                ]
                for sel in css_selectors:
                    try:
                        btn = page.locator(sel).first
                        if btn.is_visible(timeout=2000):
                            btn.click(force=True)
                            share_clicked = True
                            break
                    except Exception:
                        continue

            # Strategy 5: Tab to the Share button and press Enter
            if not share_clicked:
                try:
                    for _ in range(5):
                        page.keyboard.press("Tab")
                        time.sleep(0.2)
                    page.keyboard.press("Enter")
                    share_clicked = True
                except Exception:
                    pass

            # Wait for post to finish uploading
            time.sleep(10)

            # Check for "Post shared" or similar confirmation
            try:
                page.locator("img[alt='Animated checkmark']").wait_for(timeout=15000)
            except Exception:
                pass
            time.sleep(3)

            # Save updated cookies
            cookies = context.cookies()
            with open(COOKIE_FILE, "w") as f:
                json.dump(cookies, f)

            print(json.dumps({
                "status": "posted",
                "image": image_path,
                "platform": "instagram",
                "type": "post",
                "caption": caption
            }))

        except Exception as e:
            print(json.dumps({"status": "failed", "message": str(e)}))

        browser.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"status": "failed", "message": "Usage: login | post <image> <caption>"}))
        sys.exit(1)

    action = sys.argv[1]

    if action == "login":
        do_login()
    elif action == "post" and len(sys.argv) >= 4:
        do_post(sys.argv[2], sys.argv[3])
    else:
        print(json.dumps({"status": "failed", "message": f"Unknown action: {action}"}))
