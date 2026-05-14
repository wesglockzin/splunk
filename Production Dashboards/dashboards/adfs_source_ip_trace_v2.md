# ADFS: Source IP Trace v2

Investigates external IP activity against ADFS infrastructure. Use to look up where a specific IP address has been connecting from, which users it targeted, and what applications were accessed.

## What problem this solves

When a security event flags a suspicious IP — abuse-team report, threat-intel match, anomaly detection — you need to answer three questions fast: have we seen this IP before, what did it try, and was it successful. This dashboard takes an IP filter and produces the full operational trace: which sessions came from it, which users it targeted, which apps it tried to access, and how each attempt resolved. It's also the dashboard you reach for when investigating a potentially compromised account, working from "this user's account is suspect" backward to "what IPs touched it."

## Panels

- **Total Sessions** — session count in the filtered window.
- **Tokens Issued** — count of successful token issuances. A token issued from a suspect IP is a meaningfully different signal than a token-validation failure.
- **Token Failures** — count of token-validation failures.
- **⚠ Failure Rate %** — failure percentage tile, with warning emoji on elevated values.
- **Top Source IP** — single most active source IP in the window (or the filtered IP itself if a filter is applied).
- **Unique Usernames** — distinct usernames touched. A high count from one IP indicates spray; a low count indicates targeting.
- **Targeted Usernames** — table of usernames the source IP attempted to authenticate as.
- **Target Application** — single most-targeted app.
- **Target App Distribution** — proportion of targets across apps.
- **Session Timeline — Success vs Failure** — outcomes plotted over time to identify burst patterns.
- **Outcome Distribution** — full breakdown of session outcomes.
- **Protocol Distribution** — sessions split by authentication protocol.
- **Site Distribution** — which datacenter site processed the sessions.
- **Source IP Distribution** — proportion of sessions across source IPs (when not filtered to a single IP).
- **User Agent Breakdown** — user-agent strings seen from the source IPs.
- **Session Details** — per-session detail table for deep investigation.

## Lookups

- `ADFS_friendly_names` — readable target-app names in the session detail and target-app distribution.

## Data sources

- Windows event log index — for the ADFS session and authentication events.

## Notes

- Wildcards (`*`) in the IP filter and user filter produce the unfiltered view across all IPs and users. Useful for exploratory analysis, but most investigations start with a specific IP.
