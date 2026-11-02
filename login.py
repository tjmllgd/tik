
import os
import re
import sys
import time

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

PROFILE = "./tt_profile"

EMAIL = os.environ.get("TT_EMAIL", "").strip()
PASSWORD = os.environ.get("TT_PASSWORD", "").strip()

LOGIN_URL = "https://www.tiktok.com/login/phone-or-email/email"
MESSAGES_URL = "https://www.tiktok.com/messages"


def get_login_error(page):
    errors = [
        "Maximum attempts reached",
        "Try again later",
        "Too many attempts",
        "Incorrect password",
        "Something went wrong",
    ]

    try:
        text = page.locator("body").inner_text(timeout=5000)

        for error in errors:
            if error.lower() in text.lower():
                return error

    except Exception:
        pass

    return None


def is_logged_in(page):
    try:
        page.goto(
            MESSAGES_URL,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        page.wait_for_timeout(3000)

        if "login" in page.url.lower():
            return False

        return True

    except Exception:
        return False


def main():
    if not EMAIL or not PASSWORD:
        sys.exit("ERROR: TT_EMAIL / TT_PASSWORD missing from .env")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE,
            headless=False,
            viewport={"width": 1280, "height": 900},
        )

        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(30000)

        try:
            if is_logged_in(page):
                print("Session already valid.")

            else:
                print("Opening TikTok login...")
                page.goto(
                    LOGIN_URL,
                    wait_until="domcontentloaded",
                )

                page.wait_for_selector(
                    'input[type="password"]',
                    timeout=30000,
                )

                user_box = page.locator('input[name="username"]')

                if user_box.count() == 0:
                    user_box = page.get_by_placeholder(
                        re.compile("email|username", re.I)
                    )

                user_box.first.fill(EMAIL)

                page.locator(
                    'input[type="password"]'
                ).first.fill(PASSWORD)

                print("Credentials entered.")
                print("Submitting login...")

                btn = page.locator(
                    'button[data-e2e="login-button"], '
                    'button[type="submit"]'
                )

                if btn.count() > 0:
                    btn.first.click()
                else:
                    page.keyboard.press("Enter")

                print("Waiting for TikTok response...")

                deadline = time.time() + 180
                ok = False

                while time.time() < deadline:
                    error = get_login_error(page)

                    if error:
                        print(f"LOGIN ERROR: {error}")
                        print("Stopping. No further attempts will be made.")
                        return

                    if "login" not in page.url.lower():
                        ok = True
                        break

                    page.wait_for_timeout(2000)

                if not ok:
                    print("Login was not confirmed.")
                    print("Check the browser for verification or 2FA.")
                    return

            print("Checking session...")

            if not is_logged_in(page):
                print("Session verification failed.")
                return

            ctx.storage_state(path="state.json")
            print("Successfully saved state.json.")

        finally:
            input("Press Enter to close the browser...")
            ctx.close()


if __name__ == "__main__":
    main()
