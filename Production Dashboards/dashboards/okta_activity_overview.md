# Okta Authentication Activity Overview

Okta-side authentication activity at a glance — sessions, SSO events, failures, and which users and applications are most active.

## What problem this solves

Once an application moves from ADFS to Okta, its operational visibility moves with it. This dashboard is the Okta-side counterpart to the ADFS executive trends dashboard: a default-open page for "is the Okta authentication path healthy, and what's it being used for?" Authentication volume, success/failure breakdown, top users, and top apps all on one page, framed for routine monitoring rather than incident investigation.

## Panels

- **Auth Events** — total authentication event count in the window.
- **Successful Logins** — count of successful login events.
- **Failed Logins** — count of failed login events.
- **Session Starts** — count of session-start events. A useful counterpart to login count: a single login can produce multiple sessions across apps.
- **Authentication Events Over Time** — time chart of authentication activity, color-coded by outcome.
- **Top Applications** — most-accessed applications via Okta SSO.
- **Top Users** — most-active users by authentication volume.
- **Outcome Breakdown** — proportion of authentication outcomes (success, failure types, MFA, etc.).
- **Recent Okta Authentication Events** — tail of the most recent events for live activity inspection.

## Data sources

- Okta system log (sourcetype `OktaIM2:log` in the Okta index).
