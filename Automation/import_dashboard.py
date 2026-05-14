#!/usr/bin/env python3
# import_dashboard.py — create or update a Splunk dashboard from an exported JSON file
#
# Usage:
#   python3 import_dashboard.py dashboards/my_dashboard.json
#   python3 import_dashboard.py dashboards/my_dashboard.json --name new_dashboard_name

import json, os, ssl, sys, urllib.request, urllib.parse

HOST = "https://host.example.gov"
OWNER = "your-username"
APP = "search"

COOKIES = (
    "splunkd_8443=BE^M2Ajo7RDcPWpgeEJm_EQp0pBMrlSXccyn3TGP4m4F3VM1ogt2MimN0b6F9iXv"
    "^DiRHKMDvUmMrIfKtItUXLRbKkzW9WtYk1ZVy8iTRcma^RsG2ZwFQP4EumZHibt23g9pORx^; "
    "session_id_8443=dd85e0e6fadfe3135134d0776332d2427ce4f7c5; "
    "splunkweb_csrf_token_8443=12021983208227396472"
)
HEADERS = {
    "Cookie": COOKIES,
    "X-Splunk-Form-Key": "12021983208227396472",
    "X-Requested-With": "XMLHttpRequest",
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url, data=None, method=None):
    req = urllib.request.Request(url, headers=HEADERS, data=data, method=method)
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return r.status, json.loads(r.read())

def dashboard_exists(name):
    url = f"{HOST}/en-US/splunkd/servicesNS/{OWNER}/{APP}/data/ui/views/{name}?output_mode=json"
    try:
        status, _ = fetch(url)
        return status == 200
    except urllib.error.HTTPError as e:
        return e.code != 404

# --- Parse args ---
if len(sys.argv) < 2:
    print("Usage: python3 import_dashboard.py <path/to/dashboard.json> [--name override_name]")
    sys.exit(1)

src_file = sys.argv[1]
name_override = None
if "--name" in sys.argv:
    name_override = sys.argv[sys.argv.index("--name") + 1]

# --- Load exported JSON ---
with open(src_file) as f:
    exported = json.load(f)

entry = exported["entry"][0]
original_name = entry["name"]
dashboard_name = name_override or original_name
eai_data = entry["content"]["eai:data"]

print(f"Source:    {src_file}")
print(f"Dashboard: {dashboard_name}")

# --- Create or update ---
if dashboard_exists(dashboard_name):
    print("Status:    exists → updating")
    url = f"{HOST}/en-US/splunkd/servicesNS/{OWNER}/{APP}/data/ui/views/{dashboard_name}?output_mode=json"
    payload = urllib.parse.urlencode({"eai:data": eai_data}).encode()
    status, resp = fetch(url, data=payload, method="POST")
else:
    print("Status:    not found → creating")
    url = f"{HOST}/en-US/splunkd/servicesNS/{OWNER}/{APP}/data/ui/views?output_mode=json"
    payload = urllib.parse.urlencode({"name": dashboard_name, "eai:data": eai_data}).encode()
    status, resp = fetch(url, data=payload, method="POST")

if status in (200, 201):
    print(f"Done.      HTTP {status} — {dashboard_name} saved.")
    print(f"View at:   {HOST}/en-US/app/{APP}/{dashboard_name}")
else:
    print(f"Error:     HTTP {status}")
    print(json.dumps(resp, indent=2))
