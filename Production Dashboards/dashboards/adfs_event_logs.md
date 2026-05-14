# ADFS: Event Logs

Federation error log viewer for all ADFS servers. Categorizes authentication errors by type and application, covering both datacenter sites.

## What problem this solves

ADFS produces hundreds of error events daily under normal load — most are routine (expired tokens, retryable transient failures), some are signal (a relying party suddenly throwing a new error type, or one site producing failures the other isn't). This dashboard separates noise from signal by categorizing errors and surfacing top affected relying parties, so analysts can identify which apps are degraded without reading raw event streams.

## Panels

- **Total Errors** — overall error count in the window.
- **Unique Relying Parties Affected** — count of distinct RPs that produced any error. A useful breadth indicator: 200 errors against one RP is a different problem than 200 errors against 50 RPs.
- **Top Error Type** — single most-frequent error category in the window.
- **Errors by Site (site-a vs site-b)** — error split between the two datacenter sites. A persistent imbalance suggests a site-specific issue (config drift, capacity, networking).
- **Error Category Distribution** — full breakdown of error categories.
- **Top 10 Relying Parties by Errors** — ranked table of which apps are throwing the most errors. Drives focused investigation.
- **Error Timeline by Category** — error categories plotted over time. Spotting a category emerging or spiking is often the first warning of a new RP misconfiguration or a federation cert about to expire.
- **TABLE / STATS** — utility panels supporting the categorization views above.

## Lookups

- `ADFS_friendly_names` — readable RP names in the top-affected table.

## Data sources

- Windows event log index — error events from the federation service across all ADFS servers.

## Notes

- Site-vs-site error comparison is one of the most-used signals on this dashboard. The two datacenters should produce broadly similar error profiles under normal operation; sustained divergence is usually an early indicator of a site-specific config or hardware issue.
