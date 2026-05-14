#!/usr/bin/env python3
"""
sync_okta_inventory_to_splunk.py — Pull the canonical migration-unit registry
from the SSO Migration Schedule tracker and write it to the Splunk lookup
`okta_apps_inventory.csv`.

This script is the bridge between the SSO Migration Schedule (xlsx → ACA Flask
parsed view) and Splunk (the existing migration dashboards). It runs locally
on a the organization-intranet box (Mac launchd, Splunk forwarder host, or any cron-able
node that can reach BOTH the tracker URL AND the Splunk REST API).

Auth:
  - Tracker:  LOOKUP_TOKEN env var → query-param to the tracker.
  - Splunk:   Chrome session cookies via splunk_query.SplunkSession (same auth
              pattern as everything else in Splunk/Automation).

Output:
  Splunk lookup `okta_apps_inventory.csv` (use `| inputlookup okta_apps_inventory`
  or define a lookup in transforms.conf for `| lookup okta_apps_inventory ...`).

Usage:
  LOOKUP_TOKEN=<token> python3 sync_okta_inventory_to_splunk.py
  LOOKUP_TOKEN=<token> python3 sync_okta_inventory_to_splunk.py --tracker-url <url>
  LOOKUP_TOKEN=<token> python3 sync_okta_inventory_to_splunk.py --dry-run

  Add to crontab / launchd to refresh on a schedule.

One-time Splunk setup (run once via Splunk Web UI):
  Settings → Lookups → Lookup definitions → New
    Name:       okta_apps_inventory
    Lookup file: okta_apps_inventory.csv
    Permissions: All apps (sharing) so dashboards in any context can use it.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from io import StringIO

import requests

# Allow `python3 sync_okta_inventory_to_splunk.py` from any CWD by ensuring this
# directory is on sys.path so splunk_query imports cleanly.
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from splunk_query import SplunkSession  # noqa: E402

DEFAULT_TRACKER = "https://sso-schedule-tracker.your-env.eastus.azurecontainerapps.io/lookup/okta_apps_inventory.csv"
LOOKUP_NAME = "okta_apps_inventory"  # writes okta_apps_inventory.csv via outputlookup
COLUMNS = ["application", "uri", "friendly_name", "sso_type",
           "status", "date_completed", "team", "poc"]
SEP = "\x1f"  # ASCII unit separator — unlikely to appear in spreadsheet text


def fetch_inventory(tracker_url: str, token: str) -> list[dict]:
    """Pull the CSV from the tracker. Token via X-Lookup-Token header AND query
    param for belt-and-suspenders."""
    r = requests.get(
        tracker_url,
        headers={"X-Lookup-Token": token, "Accept": "text/csv"},
        params={"token": token},
        timeout=30,
        verify=True,
    )
    r.raise_for_status()
    rdr = csv.DictReader(StringIO(r.text))
    rows = list(rdr)
    if rows and set(rows[0].keys()) != set(COLUMNS):
        raise RuntimeError(
            f"Tracker CSV has unexpected columns. Expected {COLUMNS}, "
            f"got {sorted(rows[0].keys())}"
        )
    return rows


def _esc(v: str) -> str:
    """Escape a value for use inside an SPL double-quoted string literal."""
    return (v or "").replace("\\", "\\\\").replace('"', '\\"')


def build_spl(rows: list[dict], lookup_name: str) -> str:
    """Build an SPL statement that materializes `rows` as result-set events
    and writes them to the Splunk lookup. Pattern:
       | makeresults count=N
       | streamstats count as i
       | eval row=case(i==1, "...", i==2, "...", ...)
       | eval parts=split(row, "<SEP>")
       | eval c1=mvindex(parts, 0)  ...
       | fields c1 c2 ...
       | outputlookup okta_apps_inventory.csv
    """
    if not rows:
        # Empty inventory — still write an empty CSV (header only) so any
        # dashboards lookup-joining against it return zero matches cleanly.
        empty_evals = " ".join(f'| eval {c}=""' for c in COLUMNS)
        return (f"| makeresults count=1 {empty_evals} "
                f"| where 1=0 | fields {' '.join(COLUMNS)} "
                f"| outputlookup {lookup_name}.csv")

    encoded = [SEP.join(_esc(r.get(c, "") or "") for c in COLUMNS) for r in rows]
    case_pairs = ", ".join(f'i=={i+1}, "{row}"' for i, row in enumerate(encoded))

    parts = [
        f"| makeresults count={len(rows)}",
        "| streamstats count as i",
        f'| eval row=case({case_pairs})',
        f'| eval _parts=split(row, "{SEP}")',
    ]
    for idx, c in enumerate(COLUMNS):
        parts.append(f'| eval {c}=mvindex(_parts, {idx})')
    parts.append(f"| fields {' '.join(COLUMNS)}")
    parts.append(f"| outputlookup {lookup_name}.csv")
    return " ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tracker-url", default=os.environ.get("TRACKER_URL", DEFAULT_TRACKER))
    ap.add_argument("--lookup-name", default=os.environ.get("LOOKUP_NAME", LOOKUP_NAME))
    ap.add_argument("--splunk-host", default=os.environ.get("SPLUNK_HOST", "https://host.example.gov"))
    ap.add_argument("--dry-run", action="store_true", help="Print SPL, don't submit")
    args = ap.parse_args()

    token = os.environ.get("LOOKUP_TOKEN", "").strip()
    if not token:
        print("ERROR: LOOKUP_TOKEN env var required.", file=sys.stderr)
        return 2

    print(f"Fetching inventory from {args.tracker_url} ...", file=sys.stderr)
    rows = fetch_inventory(args.tracker_url, token)
    print(f"  {len(rows)} rows", file=sys.stderr)
    if rows:
        from collections import Counter
        counts = Counter(r["sso_type"] for r in rows)
        print(f"  by sso_type: {dict(counts)}", file=sys.stderr)

    spl = build_spl(rows, args.lookup_name)

    if args.dry_run:
        print("--- DRY RUN: SPL statement ---")
        print(spl[:1500] + ("..." if len(spl) > 1500 else ""))
        return 0

    print(f"Submitting outputlookup to {args.splunk_host} ...", file=sys.stderr)
    s = SplunkSession(host=args.splunk_host)
    result = s.search(spl, earliest="-1d", latest="now")
    print(f"  Done. {len(result)} results returned (typically empty for outputlookup).",
          file=sys.stderr)
    print(f"  Splunk lookup `{args.lookup_name}.csv` now has {len(rows)} rows.",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
