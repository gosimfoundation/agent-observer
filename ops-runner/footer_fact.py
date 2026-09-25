"""Screenshots of the footer's 900 S fact popup, opened by click, at desktop and mobile widths."""
import json, os, time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "https://create.gosim.org/survey26/platform"
OUT = Path("ops-runner/results/footer-fact") / time.strftime("%Y%m%d-%H%M%S")
OUT.mkdir(parents=True, exist_ok=True)
summary = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    for lang in ("zh", "en"):
        for view, w, h in (("desktop", 1440, 900), ("mobile", 390, 844)):
            ctx = browser.new_context(viewport={"width": w, "height": h}, is_mobile=view == "mobile", has_touch=view == "mobile")
            page = ctx.new_page()
            page.goto(f"{BASE}/?lang={lang}", wait_until="networkidle", timeout=45000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(800)
            btn = page.locator(".ticker-fact-btn").first
            row = {"lang": lang, "view": view, "button": btn.count() > 0}
            if row["button"]:
                btn.click()
                page.wait_for_timeout(600)
                row["fact_box"] = page.evaluate("""() => { const f = document.querySelector('.ticker-fact'); const c = document.querySelector('.cosmos-footer');
                  if (!f) return null; const r = f.getBoundingClientRect(); const s = getComputedStyle(c);
                  return {top: r.top, bottom: r.bottom, left: r.left, right: r.right, vw: innerWidth, overflowX: s.overflowX, overflowY: s.overflowY, text: f.innerText.slice(0, 200)} }""")
            row["h_scroll"] = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
            page.screenshot(path=str(OUT / f"footer.{lang}.{view}.png"))
            summary.append(row)
            ctx.close()
    browser.close()
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print(json.dumps(summary, ensure_ascii=False))
