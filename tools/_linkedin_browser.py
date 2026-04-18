#!/usr/bin/env python3
"""
_linkedin_browser.py
--------------------
Standalone script for LinkedIn browser automation via Playwright.
Called as a subprocess by linkedin_tool.py to avoid threading conflicts.

Usage:
    python _linkedin_browser.py login
    python _linkedin_browser.py post <image_path> <caption>
"""

import sys
import os
import json
import time

COOKIE_FILE = os.path.join(os.path.dirname(__file__), ".linkedin_cookies.json")


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

        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        time.sleep(4)

        # Check if already logged in (redirected to feed)
        already_in = False
        if "feed" in page.url:
            already_in = True

        if not already_in:
            # Wait for user to log in — poll every 3 seconds for up to 5 minutes
            print("WAITING_FOR_LOGIN", flush=True)
            deadline = time.time() + 300  # 5 min max
            while time.time() < deadline:
                if "feed" in page.url:
                    already_in = True
                    break
                time.sleep(3)

        if already_in:
            # Save cookies for future use
            cookies = context.cookies()
            with open(COOKIE_FILE, "w") as f:
                json.dump(cookies, f)
            print(json.dumps({"status": "success", "message": "LinkedIn login successful"}))
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
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        time.sleep(4)

        # Verify we're logged in
        if "login" in page.url:
            print(json.dumps({"status": "auth_required", "message": "Session expired. Login again."}))
            browser.close()
            return

        try:
            # Click "Start a post" button
            try:
                start_btn = page.locator("button.share-box-feed-entry__trigger").first
                start_btn.click()
            except Exception:
                page.locator("button:has-text('Start a post')").first.click()
            time.sleep(3)

            # Click the media/image upload button
            try:
                media_btn = page.locator("button[aria-label='Add media']").first
                media_btn.click()
            except Exception:
                try:
                    media_btn = page.locator("button:has-text('Media')").first
                    media_btn.click()
                except Exception:
                    page.locator("button[aria-label='Add a photo']").first.click()
            time.sleep(2)

            # Upload the image
            file_input = page.locator("input[type='file']").first
            file_input.set_input_files(image_path)
            time.sleep(4)

            # Click "Done" if present
            try:
                done_btn = page.locator("button:has-text('Done')")
                if done_btn.count() > 0 and done_btn.first.is_visible(timeout=3000):
                    done_btn.first.click()
                    time.sleep(2)
            except Exception:
                pass

            # Type caption
            try:
                editor = page.locator("div.ql-editor[data-placeholder]").first
                editor.click()
                page.keyboard.type(caption, delay=15)
            except Exception:
                try:
                    editor = page.locator("div[role='textbox']").first
                    editor.click()
                    page.keyboard.type(caption, delay=15)
                except Exception:
                    pass
            time.sleep(1)

            # Click Post
            try:
                post_btn = page.locator("button.share-actions__primary-action").first
                post_btn.click()
            except Exception:
                page.locator("button:has-text('Post')").first.click()
            time.sleep(8)

            # Save updated cookies
            cookies = context.cookies()
            with open(COOKIE_FILE, "w") as f:
                json.dump(cookies, f)

            print(json.dumps({
                "status": "posted",
                "image": image_path,
                "platform": "linkedin",
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
