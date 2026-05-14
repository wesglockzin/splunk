#!/usr/bin/env python3
"""
push_with_cookies.py — Push a dashboard JSON to PROD Splunk using browser cookies.

Usage:
  1. Log into host.example.gov in your browser
  2. Open DevTools → Application → Cookies → copy values for:
       splunkweb_csrf_token_8443
       splunkd_8443
       session_id_8443  (if present)
  3. Paste them into COOKIES dict below
  4. Run: python3 push_with_cookies.py <path/to/dashboard.json>
"""

import json, os, sys, warnings
import requests
warnings.filterwarnings('ignore')

HOST  = "https://host.example.gov"
OWNER = "your-username"
APP   = "search"

# --- PASTE COOKIES HERE ---
COOKIES = {
    "splunkweb_csrf_token_8443": "",
    "splunkd_8443": "",
    # "session_id_8443": "",  # uncomment if present
}
# --------------------------

if len(sys.argv) < 2:
    print("Usage: python3 push_with_cookies.py <path/to/dashboard.json>")
    sys.exit(1)

if not any(COOKIES.values()):
    print("ERROR: Paste your Splunk browser cookies into COOKIES dict in this script first.")
    sys.exit(1)

with open(sys.argv[1]) as f:
    exported = json.load(f)

entry          = exported["entry"][0]
dashboard_name = entry["name"]
eai_data       = entry["content"]["eai:data"]

csrf = COOKIES.get("splunkweb_csrf_token_8443", "")

s = requests.Session()
s.verify = False
for name, value in COOKIES.items():
    if value:
        s.cookies.set(name, value, domain="host.example.gov")
s.headers.update({
    "X-Splunk-Form-Key": csrf,
    "X-Requested-With": "XMLHttpRequest",
    "Origin": HOST,
})

# Check if exists (use owner namespace for read, nobody for write on existing)
check = s.get(f"{HOST}/en-US/splunkd/servicesNS/{OWNER}/{APP}/data/ui/views/{dashboard_name}?output_mode=json")
print(f"Dashboard:  {dashboard_name}")

if check.status_code == 200:
    print(f"Status:     exists → updating")
    url = f"{HOST}/en-US/splunkd/__raw/servicesNS/{OWNER}/{APP}/data/ui/views/{dashboard_name}?output_mode=json"
    r = s.post(url, data={"eai:data": eai_data})
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
