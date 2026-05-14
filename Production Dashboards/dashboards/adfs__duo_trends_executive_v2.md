# ADFS + DUO: Trends [Executive] v2

High-level overview of sign-in and MFA activity across the ADFS+Duo authentication stack. Daily login volumes, success and failure rates, MFA factor breakdowns, and which applications are being accessed — all rolled up for an audience that wants the headline numbers, not the per-session detail.

## What problem this solves

The ADFS+Duo authentication path produces a firehose of session events. Engineers can drill into any one event, but executives, security leads, and migration coordinators need a steady-state read on the system: are sign-ins healthy? Are MFA failures spiking? Are people authenticating against the apps we expect? This dashboard collapses the firehose into trend tiles and proportion charts, framed for at-a-glance consumption.

## Panels

- **Total SSO Sessions** — overall sign-in volume tile.
- **Successful SSO Sessions** — successful logins tile.
- **SSO Total VPN Logins** — VPN-routed login volume.
- **SSO + MFA (Fresh) Sessions** — sessions where MFA was challenged fresh (not cached).
- **SSO + MFA (cached) sessions** — sessions where Duo cached an existing factor and skipped a fresh challenge.
- **SSO + DUO (Fresh / Cached) Distribution** — proportion split between fresh and cached MFA.
- **SSO Results Distribution** — breakdown of session outcomes (success / fail / timeout / etc.).
- **SSO Site Distribution** — sessions split between datacenter sites.
- **SSO Site Distribution Timeline** — the same site split over time, to spot routing or capacity drift.
- **SSO Protocol Distribution** — sign-ins by protocol (SAML, WS-Fed, OIDC).
- **SSO External/Internal Distribution** — sessions originating outside the corporate network vs. inside.
- **Top 10 SSO Application Distribution** — most-accessed applications via SSO.
- **SSO Credential Failures** — count of credential-failure events.
- **SSO Token Failures** — count of token-validation-failure events.
- **DUO Top Success Factor** — most-used Duo factor among successful authentications (push, hardware token, etc.).
- **DUO Success Factor Distribution** — full breakdown of success factors.
- **DUO Top Failure Reason** — single most common Duo failure reason in the window.
- **DUO Failure Reason Distribution** — full breakdown of failure reasons.
- **DUO Access Device Distribution** — what devices are being used for Duo authentication.

## Lookups

- `ADFS_friendly_names` — readable application names for the top-apps table.
- `adfs_event_codes` — translates raw ADFS event codes into outcome categories (used to classify sessions as credential failures, token failures, etc.).

## Data sources

- Duo authentication log index.
- Windows event log index — for ADFS-side session events.

## Notes

- "Fresh" vs "cached" MFA is a meaningful operational distinction: a sudden jump in fresh MFA challenges relative to cached ones can indicate a session-management issue, a Duo policy change, or a mass logout event. Worth eyeballing as a leading indicator.
