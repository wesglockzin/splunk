#!/usr/bin/env python3
# import_dashboard.py — create or update a dashboard (PROD)
#
# Auth (in order of preference):
#   1. Browser cookies auto-extracted from Chrome via browser-cookie3
#   2. Playwright headless login (fallback, requires splunk_pw_venv)
#
# Usage:
#   python3 import_dashboard.py dashboards/my_dashboard.json
#   python3 import_dashboard.py dashboards/my_dashboard.json --name new_name

import json, os, sys, warnings
import requests
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HOST  = "https://host.example.gov"
OWNER = "your-username"
APP   = "search"

CHROME_PROFILES = [
    "Profile 7", "Profile 6", "Profile 5", "Profile 3", "Profile 2", "Default"
]

if len(sys.argv) < 2:
    print("Usage: python3 import_dashboard.py <path/to/dashboard.json> [--name override_name]")
    sys.exit(1)

src_file      = sys.argv[1]
name_override = sys.argv[sys.argv.index("--name") + 1] if "--name" in sys.argv else None


def _session_from_chrome() -> requests.Session | None:
    """Try to build an authenticated session from Chrome cookies."""
    try:
        import browser_cookie3
    except ImportError:
        return None

    chrome_base = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    for profile in CHROME_PROFILES:
        cookie_db = os.path.join(chrome_base, profile, "Cookies")
        if not os.path.exists(cookie_db):
            continue
        try:
            cj = browser_cookie3.chrome(cookie_file=cookie_db, domain_name="the organization.gov")
            cookies = {c.name: c.value for c in cj if c.domain == "host.example.gov"}
            if not cookies.get("splunkd_8443"):
                continue

            csrf = cookies.get("splunkweb_csrf_token_8443", "")
            s = requests.Session()
            s.verify = False
            for name, value in cookies.items():
                s.cookies.set(name, value, domain="host.example.gov")
            s.headers.update({
                "X-Splunk-Form-Key": csrf,
                "X-Requested-With": "XMLHttpRequest",
                "Origin": HOST,
            })

            r = s.get(f"{HOST}/en-US/splunkd/services/authentication/current-context?output_mode=json")
            if r.status_code == 200:
                user = r.json()["entry"][0]["content"]["username"]
                print(f"  Auth via Chrome ({profile}): {user}")
                return s
        except Exception:
            continue
    return None


def _session_from_playwright() -> requests.Session:
    """Fall back to Playwright headless login."""
    from splunk_session import get_session
    return get_session(HOST)


# Build session
s = _session_from_chrome()
if s is None:
    print("  Chrome cookies not valid — falling back to Playwright login")
    print("  (Tip: log into host.example.gov in Chrome first for faster auth)")
    s = _session_from_playwright()

# Load and push dashboard
with open(src_file) as f:
    exported = json.load(f)

entry          = exported["entry"][0]
dashboard_name = name_override or entry["name"]
eai_data       = entry["content"]["eai:data"]

check = s.get(f"{HOST}/en-US/splunkd/servicesNS/{OWNER}/{APP}/data/ui/views/{dashboard_name}?output_mode=json")
print(f"Dashboard:  {dashboard_name}")

if check.status_code == 200:
    print(f"Status:     exists → updating")
    # Use the ACL owner for the update URL — app-shared dashboards need "nobody", user-scoped need OWNER
    acl_owner = check.json()["entry"][0]["acl"].get("owner", OWNER)
    update_owner = "nobody" if check.json()["entry"][0]["acl"].get("sharing") == "app" else acl_owner
    url = f"{HOST}/en-US/splunkd/__raw/servicesNS/{update_owner}/{APP}/data/ui/views/{dashboard_name}"
    r = s.post(url, data={"eai:data": eai_data, "output_mode": "json"})
else:
    print(f"Status:     not found → creating")
    url = f"{HOST}/en-US/splunkd/__raw/servicesNS/{OWNER}/{APP}/data/ui/views?output_mode=json"
    r = s.post(url, data={"name": dashboard_name, "eai:data": eai_data})

if r.status_code in (200, 201):
    print(f"Done.       HTTP {r.status_code}")
    print(f"View at:    {HOST}/en-US/app/{APP}/{dashboard_name}")
else:
    print(f"Error:      HTTP {r.status_code}")
    print(r.text[:500])
