# ADFS: Attack Surface Dashboard v2

Per-session sign-in detail oriented toward investigating specific users or incidents. Traces each login through ADFS and correlates with Duo MFA events, showing outcome, protocol, path, and timing — the operational view security and IAM engineers use to reconstruct what happened during a suspected attack or anomaly.

## What problem this solves

When credential spray, brute force, or suspicious activity is reported against ADFS, the question isn't "are auth volumes healthy?" — it's "what specifically did this attacker (or user) try, against which app, with what outcome?" This dashboard answers that. Filters by user and outcome let an investigator pivot quickly from "this account looks compromised" to "here are every session it touched and how each ended."

## Panels

- **SSO Total** — total session count in the filtered window.
- **SSO Outcome Distribution** — proportion of outcomes (success, credential failure, token failure, MFA failure, etc.).
- **SSO Details** — per-session table: user, target app, protocol, outcome, timing, source.
- **SSO Timeline** — sessions plotted over time, color-coded by outcome. Spikes or clusters indicate active attack patterns.
- **Duo MFA Details** — per-session Duo events correlated with the ADFS sessions above, including factor used and Duo outcome.

## Lookups

- `ADFS_friendly_names` — readable target-app names in the session detail.
- `adfs_event_codes` — translates raw ADFS event codes into outcome categories.

## Data sources

- Duo authentication log index.
- Windows event log index — for ADFS session events.

## Notes

- "Attack surface" framing: this dashboard is positioned as the security-investigation entry point. A typical workflow starts at the trends or executive dashboard (something looks off), pivots here to find specific suspect sessions, then drills into one of the engineer tracers (v2 or v3) for raw event detail.
