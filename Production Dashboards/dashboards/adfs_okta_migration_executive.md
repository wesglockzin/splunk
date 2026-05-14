# ADFS → Okta Migration: Executive Summary

Executive-level view of the SSO migration program — how many applications have been moved to Okta, how many remain on ADFS, and how authentication volume is shifting from one platform to the other over time.

## What problem this solves

A multi-year migration from ADFS to Okta touches hundreds of relying parties, and progress is hard to communicate without a single canonical view. This dashboard answers four questions a non-technical audience repeatedly asks:

- How many apps have we moved so far?
- How many are left?
- What does the trendline look like — are we accelerating or stalling?
- Which remaining apps still carry the most authentication traffic, so we know where to focus?

It's the dashboard you open when leadership asks "where are we?" and you have ninety seconds.

## Panels

- **Apps Migrated** — single-value count of applications now authenticating via Okta.
- **Apps Remaining** — single-value count of applications still authenticating via ADFS.
- **% Complete** — migration progress as a percentage of the total inventory.
- **ADFS vs Okta Auth Volume Over Time** — area chart showing the daily auth-volume crossover. ADFS line declines, Okta line grows; the visual telegraphs migration velocity in one glance.
- **Migrated Applications** — table of every application now on Okta, with friendly names from the lookup so non-engineers can recognize them.
- **Top Remaining ADFS Applications** — table of the apps still on ADFS, ranked by auth volume. Identifies the highest-leverage remaining migrations.

## Lookups

- `ADFS_friendly_names` — translates raw ADFS RP identifiers into readable application names for the migration tables.
- `okta_internal_apps` — used to filter Okta's app catalog down to the in-scope applications for this migration.

## Data sources

- Okta system log (sourcetype `OktaIM2:log` in the Okta index) — for Okta-side authentication events.
- Windows event log index — for ADFS-side authentication events.

## Notes

- The "% Complete" calculation is based on the apps inventory recorded in the lookup tables. It tracks **app count**, not weighted authentication volume — by design, since exec audiences read counts more easily than weighted percentages.
- Panel ordering goes scoreboard-first (counts and %), then trend (volume crossover), then operational lists (what's done, what's next). Layout is meant to be readable top-to-bottom in 60 seconds.
