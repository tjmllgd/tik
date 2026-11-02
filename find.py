import csv, json, os, random, re, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

STATE = Path("state.json")
SENT = Path("sent.json")
TARGETS = Path("targets.csv")
KEYWORDS = Path("keywords.txt")
TEMPLATES = Path("templates.txt")

MAX_FOLLOWERS = int(os.getenv("MAX_FOLLOWERS", "100"))
MIN_FOLLOWERS = int(os.getenv("MIN_FOLLOWERS", "0"))
MAX_ADD = int(os.getenv("MAX_ADD", "25"))
MAX_CANDIDATES = int(os.getenv("MAX_CANDIDATES", "150"))
HEADLESS = os.getenv("HEADLESS") == "1"
PROXY = os.getenv("PROXY_URL") or None


def parse_count(txt):
    if not txt:
        return None
    t = txt.strip().upper().replace(",", "").replace("+", "")
    m = re.match(r"^([\d.]+)\s*([KM]?)$", t)
    if not m:
        return None
    mult = {"": 1, "K": 1_000, "M": 1_000_000}[m.group(2)]
    return int(float(m.group(1)) * mult)


def load_lines(path):
    if not path.exists():
        return []
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def known_users():
    known = set()
    if SENT.exists():
        try:
            known |= set(json.loads(SENT.read_text()))
        except Exception:
            pass
    if TARGETS.exists():
        for r in csv.DictReader(open(TARGETS, encoding="utf-8")):
            u = (r.get("username") or "").strip().lstrip("@").lower()
            if u:
                known.add(u)
    return known


def append_target(user, message):
    new = not TARGETS.exists()
    with open(TARGETS, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["username", "message"])
        w.writerow([user, message])


def collect(page, keyword, limit=60):
    found = []
    page.goto(
        f"https://www.tiktok.com/search/user?q={keyword.replace(' ', '%20')}",
        wait_until="domcontentloaded",
    )
    page.wait_for_timeout(4000)
    for _ in range(3):
        page.mouse.wheel(0, 2200)
        page.wait_for_timeout(1800)

    try:
        hrefs = page.eval_on_selector_all(
            'a[href^="/@"]', "els => els.map(e => e.getAttribute('href'))"
        )
    except Exception:
        return found

    for h in hrefs:
        if not h:
            continue
        u = h.split("/@")[-1].split("?")[0].split("/")[0].strip().lower()
        if u and u not in found:
            found.append(u)
        if len(found) >= limit:
            break
    return found


def followers(page, user):
    page.goto(f"https://www.tiktok.com/@{user}", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    for sel in ('strong[data-e2e="followers-count"]', '[data-e2e="followers-count"]'):
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                return parse_count(el.inner_text(timeout=3000))
        except Exception:
            pass
    return None


def main():
    if not STATE.exists():
        sys.exit("state.json missing — run login.py first")
    keywords = load_lines(KEYWORDS)
    templates = load_lines(TEMPLATES)
    if not keywords:
        sys.exit("keywords.txt is empty")
    if not templates:
        templates = ["hey! saw your page and wanted to say hi"]

    known = known_users()
    candidates = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS,
            proxy={"server": PROXY} if PROXY else None,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = browser.new_context(
            storage_state=str(STATE), viewport={"width": 1280, "height": 900}
        )
        page = ctx.new_page()
        page.set_default_timeout(20000)

        for kw in keywords:
            print(f"searching: {kw}")
            for u in collect(page, kw):
                if u not in known and u not in candidates:
                    candidates.append((u, kw))
            time.sleep(random.uniform(4, 9))
            if len(candidates) >= MAX_CANDIDATES:
                break

        print(f"{len(candidates)} candidates to screen")
        added = 0
        checked = 0

        for user, kw in candidates:
            if added >= MAX_ADD:
                break
            checked += 1
            try:
                n = followers(page, user)
            except Exception as e:
                print(f"  {user}: error {e}")
                n = None

            if n is None:
                print(f"  {user}: count unreadable")
            elif n < MIN_FOLLOWERS:
                print(f"  {user}: {n} — too small")
            elif n > MAX_FOLLOWERS:
                print(f"  {user}: {n} — too big")
            else:
                msg = random.choice(templates).format(username=user, keyword=kw)
                append_target(user, msg)
                added += 1
                print(f"  {user}: {n} — ADDED")

            time.sleep(random.uniform(5, 12))

        ctx.storage_state(path=str(STATE))
        browser.close()

    print(f"\nchecked {checked}, added {added} to targets.csv")


if __name__ == "__main__":
    main()
