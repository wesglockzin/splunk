# ADFS + Duo: Login Tracing [Engineer] v2

Session-level ADFS login detail with rawer event context, enriched with Duo match classification. Built for engineering investigation — the dashboard you open when one specific user has one specific complaint and you need to reconstruct exactly what happened.

## What problem this solves

When a user reports "I tried to log in and it didn't work" or security flags a suspicious session, executive trend dashboards aren't enough. You need the actual session: which ADFS server processed it, what protocol was used, when Duo was challenged, what the outcome was, and how it correlated with the raw Windows event data underneath. This dashboard surfaces that level of detail with filters by user and outcome, so a single investigation session takes seconds rather than building ad-hoc SPL.

## Panels

- **SSO Total** — total session count in the filtered window.
- **SSO Outcome Distribution** — proportion of session outcomes (success / fail / various failure reasons).
- **SSO Details** — per-session table: user, app, protocol, outcome, timestamp.
- **SSO Timeline** — sessions plotted over time, color-coded by outcome.
- **Raw Duo Events** — the underlying Duo authentication events that correspond to the SSO sessions, classified by match type (matched, direct Duo, no match, expected state).

## Lookups

- `ADFS_friendly_names` — readable RP names in session detail.
- `adfs_event_codes` — translates raw ADFS event codes into outcome classifications.

## Data sources

- Duo authentication log index.
- Windows event log index — for raw ADFS session events.

## Notes

- "Engineer" tier deliberately keeps the raw Duo events visible alongside the classified outcomes. The classified outcome is often what someone reports ("MFA failed"), but the raw event is what tells you whether it was a timeout, a denial, a wrong factor, or never reached Duo at all. v3 (the correlated tracer) hides this layer for cleanliness — open this v2 when you specifically need the rawer view.
