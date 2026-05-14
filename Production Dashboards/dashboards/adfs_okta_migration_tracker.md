# ADFS → Okta: Migration Tracker

Operational counterpart to the executive summary — the dashboard engineers and migration coordinators actually run queries against. Same auth-volume burn-down (ADFS declining, Okta growing) but with deeper drill-downs into specific relying parties, protocols, and recent authentication detail.

## What problem this solves

Migrating an RP from ADFS to Okta isn't done when the ticket closes — it's done when authentication volume actually shifts. This dashboard is how you verify that. When a migration coordinator says "we cut over App X yesterday," you open this and check whether App X's ADFS volume dropped to zero and Okta's picked up. It's also the place to find the next migration target: highest-volume RPs still on ADFS get top-of-table billing.

## Panels

- **ADFS Sessions** — single-value count of ADFS auth sessions in the time window.
- **Okta Authentications** — single-value count of Okta auth events in the time window.
- **Migration Progress (Okta %)** — Okta's share of total authentication volume. Tracks the volume-weighted version of "% complete."
- **Auth Volume Over Time: ADFS vs Okta** — time chart of the burn-down. Leading indicator of migration velocity.
- **Top ADFS Relying Parties (Migration Targets)** — ranked list of apps still on ADFS by auth volume. Picks the next migration target.
- **Auth Protocol & IDP Breakdown** — split of auth events by protocol (SAML, OIDC, WS-Fed) and IDP. Useful for spotting protocol-specific migration patterns.
- **Top Okta Apps** — most-used apps on the Okta side. Sanity-checks whether expected migrations are landing where they should.
- **Recent Authentications** — tail of the most recent auth events across both platforms. For real-time debugging during cutovers.

## Lookups

- `ADFS_friendly_names` — readable RP names for the migration target table.
- `okta_internal_apps` — restricts the Okta side to the in-scope migration cohort.

## Data sources

- Okta system log (sourcetype `OktaIM2:log` in the Okta index).
- Windows event log index — for ADFS-side authentication events.

## Notes

- Migration Progress here is **volume-weighted** (auth events), unlike the executive view's **count-weighted** (app inventory). The two often differ — one high-volume app moving to Okta can spike the volume percentage well ahead of the count percentage.
