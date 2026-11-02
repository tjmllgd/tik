# tik

Sends TikTok DMs from a list, via Playwright.

## Setup
    pip install -r requirements.txt
    playwright install chromium
    cp .env.example .env      # fill in credentials
    python login.py           # solve captcha, wait for the feed
    git add state.json && git commit -m "seed session" && git push

## Run
    python dm.py --dry-run    # opens chats, sends nothing
    python dm.py

## Notes
- `state.json` is a live session token. Repo should stay private.
- Session dies every few weeks: rerun `login.py`, commit, push.
- Keep under ~30 DMs/day. Rate limiting fails silently.
- Recipients with "Friends only" DMs will not receive anything.
