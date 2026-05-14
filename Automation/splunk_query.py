#!/usr/bin/env python3
"""
splunk_query.py — Run SPL queries against Splunk using Chrome session cookies.

Auth: auto-extracted from Chrome via browser-cookie3 (no API token needed).
Requires: pip install browser-cookie3 requests

Usage (CLI):
    python3 splunk_query.py "index=okta sourcetype=OktaIM2:log | head 5"
    python3 splunk_query.py "index=okta | stats count by eventType" --host host.example.gov

Usage (import):
    from splunk_query import SplunkSession
    s = SplunkSession()
    results = s.search("index=okta | stats count by eventType")
    for row in results:
        print(row)
"""

import json
import os
import sys
import time
import warnings
import requests

warnings.filterwarnings("ignore")

DEFAULT_HOST = "https://host.example.gov"
CHROME_PROFILES = ["Profile 7", "Profile 6", "Profile 5", "Profile 3", "Profile 2", "Default"]


class SplunkSession:
    def __init__(self, host: str = DEFAULT_HOST):
        self.host = host.rstrip("/")
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        try:
            import browser_cookie3
        except ImportError:
            raise RuntimeError("browser-cookie3 not installed: pip install browser-cookie3")

        chrome_base = os.path.expanduser("~/Library/Application Support/Google/Chrome")

        domain = self.host.replace("https://", "")
        for profile in CHROME_PROFILES:
            cookie_db = os.path.join(chrome_base, profile, "Cookies")
            if not os.path.exists(cookie_db):
                continue
            try:
                cj = browser_cookie3.chrome(cookie_file=cookie_db, domain_name="the organization.gov")
                # Filter to exact domain to avoid splunklab cookies overwriting prod cookies
                cookies = {c.name: c.value for c in cj if c.domain == domain}
                if not cookies.get("splunkd_8443"):
                    continue

                s = requests.Session()
                s.verify = False
                for name, value in cookies.items():
                    s.cookies.set(name, value, domain=domain)

                csrf = cookies.get("splunkweb_csrf_token_8443", "")
                s.headers.update({
                    "X-Splunk-Form-Key": csrf,
                    "X-Requested-With": "XMLHttpRequest",
                    "Origin": self.host,
                })

                # Verify
                r = s.get(f"{self.host}/en-US/splunkd/services/authentication/current-context?output_mode=json")
                if r.status_code == 200:
                    user = r.json()["entry"][0]["content"]["username"]
                    print(f"  Auth OK — {user} @ {self.host} (via Chrome {profile})", file=sys.stderr)
                    return s
            except Exception:
                continue

        raise RuntimeError(
            "No valid Splunk session found in Chrome. "
            "Log into Splunk in Chrome and try again."
        )

    def search(
        self,
        spl: str,
        earliest: str = "-24h",
        latest: str = "now",
        max_results: int = 1000,
    ) -> list[dict]:
        """
        Run a blocking SPL search and return results as a list of dicts.
        """
        owner = "your-username"
        app = "search"
        base = f"{self.host}/en-US/splunkd/__raw/servicesNS/{owner}/{app}"

        # Submit job
        r = self.session.post(
            f"{base}/search/jobs",
            data={
                "search": f"search {spl}" if not spl.strip().startswith("search") else spl,
                "earliest_time": earliest,
                "latest_time": latest,
                "output_mode": "json",
                "exec_mode": "normal",
            },
        )
        r.raise_for_status()
        sid = r.json()["sid"]

        # Poll until done
        poll_url = f"{self.host}/en-US/splunkd/__raw/servicesNS/{owner}/{app}/search/jobs/{sid}?output_mode=json"
        while True:
            r = self.session.get(poll_url)
            r.raise_for_status()
            state = r.json()["entry"][0]["content"]
            if state["isDone"]:
                break
            time.sleep(0.5)

        # Fetch results
        r = self.session.get(
            f"{self.host}/en-US/splunkd/__raw/servicesNS/{owner}/{app}/search/jobs/{sid}/results",
            params={"output_mode": "json", "count": max_results},
        )
        r.raise_for_status()
        return r.json().get("results", [])

    def search_table(self, spl: str, **kwargs) -> None:
        """Run search and print results as an aligned table."""
        results = self.search(spl, **kwargs)
        if not results:
            print("  (no results)")
            return

        # Collect columns (preserve order, skip internal _ fields unless only fields)
        all_keys = list(results[0].keys())
        cols = [k for k in all_keys if not k.startswith("_")] or all_keys

        # Column widths
        widths = {c: len(c) for c in cols}
        for row in results:
            for c in cols:
                widths[c] = max(widths[c], len(str(row.get(c, ""))))

        # Header
        header = "  ".join(c.ljust(widths[c]) for c in cols)
        print(header)
        print("-" * len(header))
        for row in results:
            print("  ".join(str(row.get(c, "")).ljust(widths[c]) for c in cols))

        print(f"\n{len(results)} row(s)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run SPL queries against Splunk")
    parser.add_argument("query", help="SPL query string")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Splunk host URL")
    parser.add_argument("--earliest", default="-24h", help="Earliest time (default: -24h)")
    parser.add_argument("--latest", default="now", help="Latest time (default: now)")
    parser.add_argument("--count", type=int, default=100, help="Max results (default: 100)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of table")
    args = parser.parse_args()

    s = SplunkSession(host=args.host)

    if args.json:
        results = s.search(args.query, earliest=args.earliest, latest=args.latest, max_results=args.count)
        print(json.dumps(results, indent=2))
    else:
        s.search_table(args.query, earliest=args.earliest, latest=args.latest, max_results=args.count)
