# WorkspaceOne: Operations Overview

Operational health for the on-prem WorkspaceOne / AirWatch stack: device check-ins, HTTP health on the WS1 console, top API endpoints, failing requests, Tunnel latency, and service-side errors.

## What problem this solves

When something looks off with WS1 — devices not checking in, console feeling slow, Tunnel users complaining — this is the first dashboard to open. It pulls signal from the noisiest streams in `index=airwatch` (IIS access logs, AWCM, Tunnel/Kestrel JSON, the various .NET service logs) and reduces them to a small set of operator-grade panels. Most reports resolve to one of: a small number of devices with stale MDM identity certs, a Tunnel latency tail driven by a single endpoint, or a backend service throwing a parser error on a specific Apple message — and the dashboard separates those from healthy noise.

## Panels

- **Events Ingested** — total event count across all `index=airwatch` sourcetypes in the window. Sanity check that ingestion is alive.
- **Distinct Devices** — count of unique `deviceId` values seen in IIS query strings. The closest thing to "how many devices talked to us today."
- **HTTP Success %** — percentage of IIS responses with status 2xx or 3xx, calculated against responses with `status > 0` (status=0 = client disconnected before response, excluded so disconnects don't drag the metric down).
- **HTTP 5xx** — count of true server errors. Low single digits is normal; a spike is the loudest signal.
- **Events by Host** — stacked area of event volume per server (WOC1/WOC2/WOD1/WOD2/AWC1/AWC2). Shows whether the cluster is balanced and whether one node is silent.
- **HTTP Status (15-min buckets)** — stacked column trend of 1xx-0 / 2xx / 3xx / 4xx / 5xx. The "1xx/0" bucket tracks client disconnects — bursts here usually mean an upstream / TLS / balancer issue rather than a server problem.
- **Top API Endpoints** — request volume by method and URI, with the chatty `/api/system/groups/<uuid>` cache-validation calls collapsed to a single row so they don't crowd out interesting endpoints.
- **Top Failing Endpoints (status >= 400)** — table of the loudest 4xx/5xx URIs. The recurring `406` on `AppleMDM/Processor.aspx` and `AppleMDM/CheckIn.aspx` is the clearest signal of devices with stale MDM identity certs.
- **Device Platform Mix (from User-Agent)** — pie chart of platform breakdown for **device check-ins only** (filtered to events where `deviceId` is set, so internal service-to-service calls don't drown out the picture). Apple devices using the native MDM protocol identify only as `MDM/1.0`, so they're labeled "Apple (MDM protocol)" rather than rolled into iOS/macOS.
- **WS1 Tunnel API Latency p95/p99** — line chart of percentile response time for Tunnel/Kestrel requests, from the `context.elapsed` field in the JSON-formatted Tunnel logs. The p99 tail is where slow user-perceived sessions show up.
- **Service-Side Errors** — table of `level=Error` events from the .NET service logs (DeviceServices, Compliance, Messaging, IntegrationService, etc.), grouped by sourcetype × method. Different shape of signal from IIS — these are server-internal exceptions, not HTTP failures.

## Data sources

- `index=airwatch` only. No external lookups.
- IIS sourcetype: `iis` (W3C extended log format, fields auto-extracted: `status`, `cs_method`, `cs_uri_stem`, `cs_User_Agent`, `c_ip`, `deviceId`, etc.).
- WS1 Tunnel sourcetypes: `*ws1.tunnel.kestrel*` (pure JSON, parsed via `spath`).
- .NET service log sourcetypes: `ComplianceService`, `DeviceServicesLog-*`, `AW.IntegrationService-*`, `MessagingServiceLog-*`, `ChangeEventOutboundQueueService`, `EntityReconcileService-*`, `InterrogatorQueueService-*`, `VMware.UEM.DesiredStateManagement`, `AirWatch.UEM.MetadataTransformService-*` — all use the same TSV-prefix format with `level` and `method` extracted via inline `rex`.

## Notes

- **Why the success % uses `status > 0`**: WS1 IIS records ~17% of all requests with `status=0`, meaning the client disconnected before a response was generated. Treating those as failures buries the real metric (responded requests are ~99.6% successful). The 1xx/0 bucket on the status trend chart is the place to watch disconnects directly.
- **`MDM/1.0` is Apple by protocol**: when an Apple device speaks the native MDM protocol, the `User-Agent` is just `MDM/1.0` with no OS marker. These show up as the dominant slice of the platform pie. iOS/macOS slices reflect only requests from agents (Hub, AWBrowser, Tunnel, etc.) that put the OS in their UA string.
- **`/api/system/groups/<uuid>` collapse**: the WS1 console hammers this endpoint for cache validation; left raw, it dominates the top-URI table with hundreds of distinct UUIDs. Collapsing to `/api/system/groups/` gives one accurate aggregate row.

## Build / push

The dashboard is generated from `build_workspaceone_operations.py` rather than hand-edited:

```bash
cd "Splunk/Production Dashboards/dashboards"
python3 build_workspaceone_operations.py
cd ..
python3 import_dashboard.py dashboards/workspaceone_operations_overview.json
```

If the dashboard is edited in the Splunk UI, re-export it before the next build/push or the UI changes will be overwritten.
