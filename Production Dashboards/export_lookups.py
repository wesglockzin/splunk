#!/usr/bin/env python3
# export_lookups.py — export lookup files + definitions owned by your-username (PROD)

import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from splunk_session import get_session

HOST = "https://host.example.gov"
OWNER = "your-username"
APP = "search"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "lookups")

s = get_session(HOST)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Export lookup definitions (transforms.conf stanzas) owned by this user
r = s.get(f"{HOST}/en-US/splunkd/servicesNS/{OWNER}/{APP}/data/transforms/lookups?output_mode=json&count=0")
defs = [e for e in r.json().get("entry", []) if e["acl"].get("owner") == OWNER]
def_map = {e["name"]: e["content"].get("filename", e["name"] + ".csv") for e in defs}
with open(os.path.join(OUTPUT_DIR, "_lookup_definitions.json"), "w") as f:
    json.dump(def_map, f, indent=2)
print(f"Exported {len(def_map)} lookup definitions → _lookup_definitions.json")

# Get list of lookup files owned by this user
r = s.get(f"{HOST}/en-US/splunkd/servicesNS/{OWNER}/{APP}/data/lookup-table-files?output_mode=json&count=0")
entries = [e for e in r.json().get("entry", []) if e["acl"].get("owner") == OWNER]
print(f"Found {len(entries)} lookup files\n")

def run_search(s, host, query):
    """Run a Splunk search and return results as CSV using streaming export (no scheduler queue)."""
    r = s.post(f"{host}/en-US/splunkd/__raw/servicesNS/-/search/search/jobs/export",
               data={"search": query, "output_mode": "csv", "count": 0})
    return r.text, r.status_code

ok, failed = 0, []
for e in entries:
    name = e["name"]
    csv_content, status = run_search(s, HOST, f"| inputlookup {name}")
    if csv_content and status == 200:
        fpath = os.path.join(OUTPUT_DIR, name)
        with open(fpath, "w") as f:
            f.write(csv_content)
        rows = csv_content.strip().count('\n')
        ok += 1
        print(f"  [{ok}/{len(entries)}] {name} ({rows} rows)")
    else:
        failed.append(f"{name}: {status}")
        print(f"  [FAIL] {name}: {status}")

print(f"\nDone. {ok}/{len(entries)} exported to {OUTPUT_DIR}/")
if failed:
    print("Failed:")
    for f in failed: print(f"  {f}")
