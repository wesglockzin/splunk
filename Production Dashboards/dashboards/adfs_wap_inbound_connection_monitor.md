# ADFS: WAP Inbound Connection Monitor

Monitors inbound TCP connections to the Web Application Proxy (WAP) VIPs at both datacenter sites, sourced from Cisco ASA firewall logs. Designed to detect connections that bypass the expected CDN entry path.

## What problem this solves

Legitimate ADFS traffic in this environment is fronted by a CDN — Akamai edge nodes terminate user requests and forward them to the WAP layer in front of ADFS. Any inbound connection to the WAP VIPs that **doesn't** originate from Akamai is, by construction, a CDN bypass. That's almost always either a misconfigured tool, a security probe, or a deliberate attempt to skip CDN controls. This dashboard surfaces non-Akamai connections immediately so they can be investigated, while the legitimate Akamai traffic is auditable in the same view.

## Panels

- **Total Inbound Connections** — connection count in the time window.
- **Unique Source IPs** — distinct source IP count. Spikes can indicate scanning or distributed traffic.
- **⚠ Non-Akamai Connections** — count of connections from sources outside the Akamai CDN ranges. The headline security tile.
- **Top Source IP** — single most active source IP.
- **Source Organization Distribution** — sources broken down by WHOIS organization. Akamai should dominate; outliers warrant investigation.
- **Source IP Distribution** — proportion of connections across source IPs.
- **Site Distribution (site-a vs site-b)** — connection split between the two WAP-VIP sites. Persistent imbalance can indicate routing or capacity issues.
- **Connection Timeline** — connections over time, broken down by source category.
- **⚠ Non-Akamai Connection Detail** — per-connection table for the non-Akamai subset. The investigation surface for any flagged traffic.
- **All Connection Detail** — full per-connection table including Akamai-sourced traffic.

## Data sources

- Firewall log index — Cisco ASA firewall logs from the WAP front-end.

## Notes

- The "non-Akamai" classification is the highest-value alert on this dashboard. In normal operation it should be near-zero. Sustained non-zero values are the first place to check when CDN-bypass attempts are suspected.
- The two WAP VIPs serve different datacenter sites; the site-distribution panel exists to detect traffic-routing anomalies (one site getting all the load, or one site missing legitimate traffic).
