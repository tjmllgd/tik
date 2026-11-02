import os, re, sys, time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
PROFILE = "./tt_profile"
EMAIL = os.environ.get("TT_EMAIL", "").strip()
PASSWORD = os.environ.get("TT_PASSWORD", "").strip()


def is_logged_in(page):
    try:
        page.goto("https://www.tiktok.com/messages", wait_until="domcontentloaded")
        page.wait_for_timeout(4500)
        return "login" not in page.url
    except Exception:
        return False


def main():
    if not EMAIL or not PASSWORD:
        sys.exit("TT_EMAIL / TT_PASSWORD missing from .env")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE,
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.set_default_timeout(30000)

        if is_logged_in(page):
            print("Session already valid.")
        else:
            page.goto(
                "https://www.tiktok.com/login/phone-or-email/email",
                wait_until="domcontentloaded",
            )
            page.wait_for_selector('input[type="password"]', timeout=30000)

            user_box = page.locator('input[name="username"]')
            if user_box.count() == 0:
                user_box = page.get_by_placeholder(re.compile("email|username", re.I))
            user_box.first.fill(EMAIL)
            page.locator('input[type="password"]').first.fill(PASSWORD)
            page.wait_for_timeout(400)

            btn = page.locator('button[data-e2e="login-button"], button[type="submit"]')
            if btn.count() > 0:
                btn.first.click()
            else:
                page.keyboard.press("Enter")

            print("Solve the slider puzzle / 2FA in the window if prompted.")
            print("Waiting up to 3 minutes...")

            deadline = time.time() + 180
            ok = False
            while time.time() < deadline:
                if "login" not in page.url:
                    ok = True
                    break
                page.wait_for_timeout(2000)

            if not ok:
                sys.exit("Still on the login page. Check credentials / finish 2FA.")

        if not is_logged_in(page):
            sys.exit("Login did not persist. Not saving state.json.")

        ctx.storage_state(path="state.json")
        print("Saved state.json — commit and push it.")
        input("Press Enter to close the browser...")
        ctx.close()


if __name__ == "__main__":
    main()
