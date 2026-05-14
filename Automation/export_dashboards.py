#!/usr/bin/env python3
# export_dashboards.py — export dashboards owned by your-username

import json, os, ssl, urllib.request

HOST = "https://host.example.gov"
OWNER = "your-username"
APP = "search"
OUTPUT_DIR = "./dashboards"

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

os.makedirs(OUTPUT_DIR, exist_ok=True)

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        return json.loads(r.read())

# Get dashboards owned by this user
url = f"{HOST}/en-US/splunkd/servicesNS/{OWNER}/{APP}/data/ui/views?output_mode=json&count=0&search=isDashboard%3D1"
data = fetch(url)
dashboards = [(e["name"], e["acl"]["app"]) for e in data["entry"]
              if e["content"].get("isDashboard", False) and e["acl"].get("owner") == OWNER]

print(f"Found {len(dashboards)} dashboards owned by {OWNER}\n")

ok, failed = 0, []
for name, app in dashboards:
    url = f"{HOST}/en-US/splunkd/servicesNS/{OWNER}/{app}/data/ui/views/{name}?output_mode=json"
    try:
        result = fetch(url)
        fpath = os.path.join(OUTPUT_DIR, f"{name}.json")
        with open(fpath, "w") as f:
            json.dump(result, f, indent=2)
        ok += 1
        print(f"  [{ok}/{len(dashboards)}] {name}")
    except Exception as e:
        failed.append(f"{name}: {e}")
        print(f"  [FAIL] {name}: {e}")

print(f"\nDone. {ok}/{len(dashboards)} exported to {OUTPUT_DIR}/")
if failed:
    print("Failed:")
    for f in failed:
        print(f"  {f}")
