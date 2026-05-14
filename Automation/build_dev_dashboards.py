#!/usr/bin/env python3
# build_dev_dashboards.py — clone prod dashboards with dev-specific substitutions
# Phase 1: transform only. Review output in Development/dashboards/ before Phase 2 upload.

import json, os, re

SRC_DIR = "Production/dashboards"
DST_DIR = "Development/dashboards"

REPLACEMENTS = [
    # Host wildcards — add 'd' suffix before the wildcard
    (r'\*-ess-sen-adf5\*',     '*-ess-sen-adf5d*'),
    (r's-ess-sen-sso1\*',      's-ess-sen-sso1d*'),
    (r's-ess-sen-sso2\*',      's-ess-sen-sso2d*'),
    # ADFS URL
    (r'adfs\.the organization\.gov',     'host.example.gov'),
]

os.makedirs(DST_DIR, exist_ok=True)

changed = []
unchanged = []

for fname in sorted(os.listdir(SRC_DIR)):
    if not fname.endswith('.json'):
        continue

    src_path = os.path.join(SRC_DIR, fname)
    dst_path = os.path.join(DST_DIR, fname)

    with open(src_path) as f:
        data = json.load(f)

    eai = data['entry'][0]['content'].get('eai:data', '')
    original = eai
    hits = []

    for pattern, replacement in REPLACEMENTS:
        new_eai, count = re.subn(pattern, replacement, eai)
        if count:
            hits.append(f"{pattern} → {replacement} ({count}x)")
            eai = new_eai

    data['entry'][0]['content']['eai:data'] = eai

    with open(dst_path, 'w') as f:
        json.dump(data, f, indent=2)

    name = fname.replace('.json', '')
    if hits:
        changed.append((name, hits))
    else:
        unchanged.append(name)

print("=== Phase 1 Complete — Dev dashboards written to Development/dashboards/ ===\n")

print(f"Modified ({len(changed)}):")
for name, hits in changed:
    print(f"  {name}")
    for h in hits:
        print(f"    {h}")

print(f"\nUnchanged ({len(unchanged)}):")
for name in unchanged:
    print(f"  {name}")

print("\nReview Development/dashboards/ then run Phase 2 to upload.")
