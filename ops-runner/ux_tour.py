"""Screenshot tour of the live site for a UX review.

Visitor pages are captured without an account. Signed-in pages use a hidden
audit account (marked as a platform test account, hidden from the wall) whose
password is regenerated for every run and never printed. Screenshots and a
summary of load times and browser errors go to ops-runner/results/ux-tour/.
"""
from __future__ import annotations

import json
import os
import secrets
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("UX_BASE", "https://create.gosim.org/survey26/platform").rstrip("/")
EMAIL = "ux-audit@create.gosim.org"
OUT = Path("ops-runner/results") / os.environ.get("UX_LABEL", "ux-tour") / time.strftime("%Y%m%d-%H%M%S")
PUBLIC = ["/", "/start", "/brief", "/rules", "/docs", "/faq", "/resources", "/leaderboard",
          "/announcements", "/teammates", "/register", "/register?mode=login", "/no-such-page"]
SIGNED_IN = ["/dashboard", "/compete", "/team", "/notifications", "/submissions", "/profile", "/teammates", "/"]
VIEWS = [("zh", "desktop", 1440, 900), ("zh", "mobile", 390, 844), ("en", "desktop", 1440, 900)]


def http(url: str, data=None, *, method: str | None = None, token: str, apikey: str | None = None):
    body = None if data is None else json.dumps(data).encode()
    headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
    if apikey:
        headers["apikey"] = apikey
    request = urllib.request.Request(url, data=body, method=method or ("POST" if body else "GET"), headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read()
        return json.loads(raw) if raw else None


def sql(query: str):
    return http("https://api.supabase.com/v1/projects/" + os.environ["SUPABASE_PROJECT_REF"] + "/database/query",
                {"query": query}, token=os.environ["SUPABASE_ACCESS_TOKEN"])


def ensure_account() -> str:
    """Create or reuse the hidden audit account and give it a fresh password."""
    service = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    base = os.environ["SUPABASE_URL"]
    password = secrets.token_urlsafe(24)
    print("::add-mask::" + password, flush=True)
    rows = sql("select id, raw_user_meta_data->>'observer_platform_e2e' as marker from auth.users where email='" + EMAIL + "'")
    if rows:
        if rows[0]["marker"] != "true":
            raise RuntimeError("refusing to modify an account that is not a platform test account")
        user = rows[0]["id"]
        http(base + "/auth/v1/admin/users/" + user, {"password": password}, method="PUT", token=service, apikey=service)
    else:
        user = http(base + "/auth/v1/admin/users", {
            "email": EMAIL, "password": password, "email_confirm": True,
            "user_metadata": {"full_name": "UX audit (hidden)", "observer_platform_e2e": True}}, token=service, apikey=service)["id"]
    sql("begin;update public.profiles set show_on_wall=false where id='" + user + "';"
        "insert into public.site_settings(key,value) values('excluded_accounts',jsonb_build_array('" + user + "'::text)) "
        "on conflict(key) do update set value=case when public.site_settings.value @> excluded.value "
        "then public.site_settings.value else public.site_settings.value || excluded.value end;commit;")
    return password


def with_lang(path: str, lang: str) -> str:
    return BASE + path + ("&" if "?" in path else "?") + "lang=" + lang


def shoot(page, path: str, lang: str, view: str, prefix: str, summary: list) -> None:
    errors: list[str] = []
    page.on("console", lambda message: errors.append("console: " + message.text[:300]) if message.type == "error" else None)
    page.on("pageerror", lambda error: errors.append("pageerror: " + str(error)[:300]))
    started = time.monotonic()
    try:
        response = page.goto(with_lang(path, lang), wait_until="networkidle", timeout=45000)
        status = response.status if response else None
    except Exception as exc:  # keep touring; record the failure
        status = "error: " + type(exc).__name__
    page.wait_for_timeout(1500)
    elapsed = round(time.monotonic() - started, 2)
    name = f"{prefix}{path.strip('/').replace('/', '_').replace('?', '_').replace('=', '-') or 'home'}.{lang}.{view}.jpg"
    page.screenshot(path=str(OUT / name), full_page=True, type="jpeg", quality=70)
    summary.append({"file": name, "path": path, "lang": lang, "view": view, "final_url": page.url.replace(BASE, ""),
                    "status": status, "seconds": elapsed, "errors": errors[:20]})


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    password = ensure_account()
    summary: list[dict] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for lang, view, width, height in VIEWS:
            mobile = view == "mobile"
            context = browser.new_context(viewport={"width": width, "height": height}, is_mobile=mobile,
                                          has_touch=mobile, locale="zh-CN" if lang == "zh" else "en-US")
            page = context.new_page()
            for path in PUBLIC:
                shoot(page, path, lang, view, "visitor-", summary)
            page.goto(with_lang("/register?mode=login", lang), wait_until="networkidle", timeout=45000)
            page.get_by_test_id("login-email").fill(EMAIL)
            page.get_by_test_id("login-password").fill(password)
            page.get_by_test_id("login-submit").click()
            page.wait_for_timeout(5000)
            summary.append({"file": None, "path": "login", "lang": lang, "view": view, "final_url": page.url.replace(BASE, "")})
            for path in SIGNED_IN:
                shoot(page, path, lang, view, "member-", summary)
            context.close()
        browser.close()
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    print(json.dumps({"screenshots": sum(1 for item in summary if item.get("file")), "out": str(OUT)}))


if __name__ == "__main__":
    main()
