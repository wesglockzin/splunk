#!/usr/bin/env python3
# splunk_session.py — get an authenticated Splunk session via Playwright browser login
# Used by export/import/lookup scripts in both Production/ and Development/
#
# Usage:
#   from splunk_session import get_session
#   s = get_session("https://host.example.gov")

import subprocess, sys, json
from pathlib import Path

VENV_PYTHON = "/tmp/splunk_pw_venv/bin/python3"

def get_session(host: str):
    """Return an authenticated requests.Session for the given Splunk host."""
    import requests, warnings
    warnings.filterwarnings('ignore')

    cookies = _get_cookies_via_playwright(host)

    s = requests.Session()
    s.verify = False
    for name, value in cookies.items():
        s.cookies.set(name, value, domain=host.replace("https://", ""))

    csrf = cookies.get("splunkweb_csrf_token_8443", "")
    s.headers.update({
        "X-Splunk-Form-Key": csrf,
        "X-Requested-With": "XMLHttpRequest",
        "Origin": host,
    })

    # Verify auth
    r = s.get(f"{host}/en-US/splunkd/services/authentication/current-context?output_mode=json")
    try:
        user = r.json()['entry'][0]['content']['username']
        print(f"  Logged in as: {user} @ {host}")
    except Exception:
        raise RuntimeError(f"Auth verification failed after login. HTTP {r.status_code}")

    return s


KEYCHAIN_SERVICE = "splunk-dashboard-export"
KEYCHAIN_ACCOUNT = "your-username"


def _get_credentials() -> tuple[str, str]:
    """Return (username, password) from macOS Keychain, falling back to interactive prompt."""
    result = subprocess.run(
        ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-a", KEYCHAIN_ACCOUNT, "-w"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        password = result.stdout.strip()
        print(f"  Using Keychain credentials for {KEYCHAIN_ACCOUNT}")
        return KEYCHAIN_ACCOUNT, password

    import getpass
    print("  (Keychain lookup failed — enter credentials manually)")
    username = input("  Username: ").strip()
    password = getpass.getpass("  Password: ")
    return username, password


def _get_cookies_via_playwright(host: str) -> dict:
    """Launch headless Chromium, log into Splunk, return session cookies."""
    print(f"Logging into {host} ...")
    username, password = _get_credentials()

    script = f"""
import asyncio, json
from playwright.async_api import async_playwright

async def login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(ignore_https_errors=True)
        page = await ctx.new_page()
        await page.goto("{host}/en-US/account/login", wait_until="networkidle")
        await page.fill('input[name="username"]', {json.dumps(username)})
        await page.fill('input[name="password"]', {json.dumps(password)})
        await page.click('input[type="submit"], button[type="submit"]')
        await page.wait_for_url(lambda url: "/account/login" not in url, timeout=15000)
        cookies = await ctx.cookies()
        await browser.close()
        result = {{c['name']: c['value'] for c in cookies}}
        print(json.dumps(result))

asyncio.run(login())
"""

    result = subprocess.run(
        [VENV_PYTHON, "-c", script],
        capture_output=True, text=True, timeout=30
    )

    if result.returncode != 0:
        raise RuntimeError(f"Playwright login failed:\n{result.stderr}")

    # Last line of stdout is the JSON cookie dict
    for line in reversed(result.stdout.strip().splitlines()):
        try:
            return json.loads(line)
        except Exception:
            continue

    raise RuntimeError("Could not parse cookies from Playwright output")


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "https://host.example.gov"
    s = get_session(host)
    print("Session ready.")
