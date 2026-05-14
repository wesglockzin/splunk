#!/usr/bin/env python3
# export_dashboards.py — export dashboards owned by your-username (PROD)

import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from splunk_session import get_session

HOST = "https://host.example.gov"
OWNER = "your-username"
APP = "search"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "dashboards")

s = get_session(HOST)
os.makedirs(OUTPUT_DIR, exist_ok=True)

url = f"{HOST}/en-US/splunkd/servicesNS/{OWNER}/{APP}/data/ui/views?output_mode=json&count=0&search=isDashboard%3D1"
data = s.get(url).json()
dashboards = [(e["name"], e["acl"]["app"]) for e in data["entry"]
              if e["content"].get("isDashboard", False) and e["acl"].get("owner") == OWNER]

print(f"Found {len(dashboards)} dashboards\n")
ok, failed = 0, []

for name, app in dashboards:
    r = s.get(f"{HOST}/en-US/splunkd/servicesNS/{OWNER}/{app}/data/ui/views/{name}?output_mode=json")
    if r.status_code == 200:
        fpath = os.path.join(OUTPUT_DIR, f"{name}.json")
        with open(fpath, "w") as f:
            json.dump(r.json(), f, indent=2)
        ok += 1
        print(f"  [{ok}/{len(dashboards)}] {name}")
    else:
        failed.append(f"{name}: HTTP {r.status_code}")
        print(f"  [FAIL] {name}: HTTP {r.status_code}")

print(f"\nDone. {ok}/{len(dashboards)} exported to {OUTPUT_DIR}/")
if failed:
    print("Failed:")
    for f in failed: print(f"  {f}")
