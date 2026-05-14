# ADFS: WS-Trust Endpoint Activity

Monitors activity against all WS-Trust authentication endpoints. Tracks which endpoints are being hit, by whom, and from where. Includes a security indicator that alerts when high-risk endpoints receive any traffic.

## What problem this solves

WS-Trust endpoints on ADFS are a known attack surface for credential spray and brute force — particularly the `usernamemixed`, `certificatemixed`, `issuedtokenmixed`, and `mex` endpoints, which accept username/password authentication directly without the browser-flow protections that protect other auth paths. Most environments don't actively use these endpoints; in many cases they should receive zero legitimate traffic. This dashboard tracks all WS-Trust activity and explicitly alerts on the high-risk subset, so any hits against unused endpoints surface immediately.

## Panels

- **Total Hits** — total WS-Trust endpoint requests in the window.
- **Unique Source IPs** — distinct IP count making WS-Trust requests.
- **Unique Endpoints Hit** — distinct WS-Trust endpoint paths receiving traffic.
- **Top Source IP** — single most active source IP.
- **Hit Timeline by Endpoint** — endpoint activity plotted over time, color-coded per endpoint.
- **Endpoint × Source IP × User × Server FQDN — Hit Matrix** — multi-dimensional cross-tab of activity. Identifies which (IP, user, endpoint) combinations are seeing traffic.
- **Endpoint Distribution** — proportion of hits across endpoints.
- **Site Distribution** — hits split between datacenter sites.
- **Top Users by Endpoint** — user accounts being authenticated against each endpoint.
- **⚠ Risky Endpoint Hits — usernamemixed / certificatemixed / issuedtokenmixed / mex** — explicit alert panel surfacing any traffic against the high-risk endpoints.

## Data sources

- Windows event log index — for ADFS WS-Trust endpoint event records.

## Notes

- The "Risky Endpoint Hits" alert is the headline panel: in normal operation it should be empty or near-empty. Any sustained traffic warrants investigation as a potential credential-spray attempt or misconfigured automation.
- The hit matrix exists because a single dimension (IP, user, or endpoint alone) often misses the pattern. Spray tends to show up as `(many users) × (one IP) × (one endpoint)`; brute force is `(one user) × (many IPs) × (one endpoint)`. The matrix layout makes both patterns visible at a glance.
