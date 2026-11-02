import csv, json, os, random, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

STATE = Path("state.json")
SENT = Path("sent.json")
DELAY_RANGE = (30, 75)
MAX_SENDS = int(os.getenv("MAX_SENDS", "20"))
HEADLESS = os.getenv("HEADLESS") == "1"
PROXY = os.getenv("PROXY_URL") or None
DRY_RUN = os.getenv("DRY_RUN") == "1" or "--dry-run" in sys.argv

MESSAGE_SELECTORS = (
    'button[data-e2e="message-button"]',
    'button:has-text("Message")',
    'a[data-e2e="message-button"]',
)
COMPOSER_SELECTORS = (
    'div[data-e2e="message-input-area"]',
    'div[contenteditable="true"]',
)


def load_sent():
    if not SENT.exists():
        return set()
    try:
        return set(json.loads(SENT.read_text()))
    except Exception:
        return set()


def save_sent(s):
    SENT.write_text(json.dumps(sorted(s), indent=1))


def first_visible(page, selectors, timeout=4000):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=timeout):
                return loc
        except Exception:
            continue
    return None


def open_chat(page, username):
    page.goto(f"https://www.tiktok.com/@{username}", wait_until="domcontentloaded")
    page.wait_for_timeout(3500)

    btn = first_visible(page, MESSAGE_SELECTORS)
    if btn:
        btn.click()
        page.wait_for_timeout(4000)
        return True

    page.goto("https://www.tiktok.com/messages", wait_until="domcontentloaded")
    page.wait_for_timeout(3500)
    try:
        box = page.locator(
            'input[placeholder*="Search"], input[data-e2e="search-user"]'
        ).first
        box.click()
        box.fill(username)
        page.wait_for_timeout(3500)
        page.locator(f'text=@{username}').first.click()
        page.wait_for_timeout(3500)
        return True
    except Exception:
        return False


def session_dead(page):
    if "login" in page.url:
        return True
    try:
        return page.locator('button[data-e2e="login-button"]').count() > 0
    except Exception:
        return False


def main():
    if not STATE.exists():
        sys.exit("state.json missing — run login.py locally and commit it")
    if not Path("targets.csv").exists():
        sys.exit("targets.csv missing")

    rows = list(csv.DictReader(open("targets.csv", encoding="utf-8")))
    sent = load_sent()
    todo = []
    for r in rows:
        u = (r.get("username") or "").strip().lstrip("@").lower()
        m = (r.get("message") or "").strip()
        if u and m and u not in sent:
            todo.append((u, m))
    todo = todo[:MAX_SENDS]

    print(f"{len(todo)} to send (cap {MAX_SENDS}, {len(sent)} already done)")
    if DRY_RUN:
        print("DRY RUN — nothing will be sent or recorded")
    if not todo:
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            proxy={"server": PROXY} if PROXY else None,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            storage_state=str(STATE),
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()
        page.set_default_timeout(20000)

        for i, (user, msg) in enumerate(todo, 1):
            print(f"[{i}/{len(todo)}] {user}")
            try:
                if not open_chat(page, user):
                    print("   ! conversation not opened")
                    continue
                if session_dead(page):
                    print("   ! SESSION EXPIRED — rerun login.py and commit state.json")
                    ctx.storage_state(path=str(STATE))
                    browser.close()
                    sys.exit(2)

                box = first_visible(page, COMPOSER_SELECTORS, timeout=8000)
                if box is None:
                    print("   ! composer not found")
                    continue

                box.click()
                page.wait_for_timeout(500)
                box.type(msg, delay=random.randint(30, 90))
                page.wait_for_timeout(random.randint(500, 1400))
                page.keyboard.press("Enter")
                page.wait_for_timeout(2800)

                if DRY_RUN:
                    print("   (dry run)")
                else:
                    sent.add(user)
                    save_sent(sent)
                    print("   sent")
            except Exception as e:
                print(f"   ! failed: {e}")

            time.sleep(random.uniform(*DELAY_RANGE))

        try:
            ctx.storage_state(path=str(STATE))
        except Exception:
            pass
        browser.close()


if __name__ == "__main__":
    main()
