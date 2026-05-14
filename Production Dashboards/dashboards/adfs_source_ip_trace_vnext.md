# ADFS: Source IP Trace vNext

Same investigation surface as Source IP Trace v2, with one important enrichment: True-Client-IP from EventCode 510 headers. Where v2 traces the IP that connected to ADFS directly, vNext sees through CDN/proxy layers to the actual originating client.

## What problem this solves

Modern ADFS deployments often sit behind a CDN (Akamai in this environment). The CDN's edge IPs are what ADFS sees as the source — useful for some questions, but useless when investigating which actual client behind the CDN initiated a session. EventCode 510 records the X-Forwarded-For / True-Client-IP header so the originating client is recoverable. vNext makes that visible alongside the v2-style session reconstruction, so a single investigation gets both the proxy-side and originating-client-side view without needing two queries.

## Panels

- **Total Sessions** — session count in the filtered window.
- **Tokens Issued** — count of successful token issuances.
- **Token Failures** — count of token-validation failures.
- **Top Source IP** — single most active source IP (or the filtered IP).
- **Unique Usernames** — distinct usernames touched.
- **Targeted Usernames** — table of usernames the source IP attempted to authenticate as.
- **Target Application** — single most-targeted app.
- **Target App Distribution** — proportion of targets across apps.
- **Session Timeline** — outcomes plotted over time.
- **Outcome Distribution** — full breakdown of session outcomes.
- **Protocol Distribution** — sessions split by authentication protocol.
- **Site Distribution** — which datacenter site processed the sessions.
- **Source IP Distribution** — proportion of sessions across source IPs.
- **User Agent Breakdown** — user-agent strings seen from the source IPs.
- **Session Details** — per-session detail table including the True-Client-IP enrichment from EventCode 510.

## Lookups

- `ADFS_friendly_names` — readable target-app names.

## Data sources

- Windows event log index — for ADFS session events including EventCode 510 with header enrichment.

## Notes

- vNext is the modern successor to v2; pick this one when investigating sessions that pass through the CDN. v2 stays around for investigations specifically focused on what ADFS itself observed (which is sometimes more useful when troubleshooting the CDN-to-ADFS path itself).
- Wildcards (`*`) work in both filter inputs for unfiltered views.
