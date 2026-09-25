#!/usr/bin/env bash
# Confirm the Mid-Autumn greeting is live: retries while the Pages CDN refreshes,
# then commits one screenshot of the live banner.
set -euo pipefail
python -m pip install -q playwright==1.55.0
python -m playwright install --with-deps chromium > /dev/null
python - <<'PY'
import time
from playwright.sync_api import sync_playwright
base = "https://create.gosim.org/survey26/platform/"
with sync_playwright() as p:
    browser = p.chromium.launch()
    for attempt in range(12):
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(base + f"?egg=midautumn&lang=zh&v={attempt}", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(1500)
        # The new build releases the rabbit into a card showing tonight's Moon on the survey strip.
        found = page.locator('[data-testid="mid-autumn-rabbit"]').count()
        print("attempt", attempt, "banner", found, flush=True)
        if found:
            page.click('[data-testid="mid-autumn-rabbit"]')
            card = page.locator('[data-testid="mid-autumn-sky"]')
            if card.count():
                page.wait_for_timeout(4500)
                print("card:", card.inner_text().replace("\n", " | "), flush=True)
                page.screenshot(path="ops-runner/results/egg-live.png", clip={"x": 0, "y": 0, "width": 1440, "height": 460})
                break
        page.close()
        time.sleep(30)
    else:
        raise SystemExit("sky card not live yet")
    browser.close()
PY
git config user.name "ops-runner"
git config user.email "ops-runner@users.noreply.github.com"
git add ops-runner/results/egg-live.png
git commit -q -m "Live Mid-Autumn sky card screenshot"
git push -q origin HEAD:claude/ops-runner
