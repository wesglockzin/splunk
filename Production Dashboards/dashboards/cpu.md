# ADFS: Server Resource Monitor

CPU and memory utilization for all ADFS servers across both datacenters. Use to identify resource pressure during high-traffic periods or incidents.

## What problem this solves

When authentication latency spikes or sessions start failing, the first triage question is "is the ADFS infrastructure under load?" This dashboard answers that — per-host CPU and memory across all ADFS servers in both sites, with peak/average/lowest tiles for at-a-glance read. It's also the dashboard you check after a known traffic event (legislative session, mass-login, system maintenance) to confirm capacity headroom before the next one.

## Panels

- **Peak CPU Host** — single-value tile naming the host with the highest CPU peak in the window.
- **Avg CPU % by Host** — table of average CPU percentages per host.
- **CPU Utilization (%) by Host** — time chart of CPU utilization, one line per host.
- **Lowest Available Memory Host** — host with the lowest available memory at any point in the window.
- **Avg Available MBytes by Host** — table of average available memory per host.
- **Memory — Usage % and Available MBytes by Host** — combined memory view showing both percentage utilization and absolute available bytes per host.

## Data sources

- Performance monitor index (perfmon) — Windows performance counters for CPU and memory across ADFS hosts.
