# Okta: Security Monitor

Failed logins, lockouts, credential spray detection, and API token activity. The Okta-side security investigation surface.

## What problem this solves

Most Okta authentication monitoring focuses on legitimate user activity. This dashboard inverts that — it surfaces the failure side: what's failing, who's getting locked out, which IPs are producing failures across multiple users (the credential-spray fingerprint), and what's happening on the API/token side that might indicate automation abuse. It's the dashboard you pin during active incident response and the one you sweep through periodically as a hygiene check.

## Panels

- **Failed Logins** — total failed login event count in the window.
- **Account Lockouts** — count of account lockout events.
- **Suspicious IPs (3+ users failed)** — count of source IPs that produced authentication failures against three or more distinct users. This is the credential-spray fingerprint: one IP failing against many accounts in quick succession.
- **API Calls (Programmatic)** — count of programmatic (API-token-driven) Okta API calls. A jump here can indicate either expected automation or token compromise.
- **Failed Auth Events Over Time** — time chart of failure activity. Bursts and sustained elevated failure rates are both visible.
- **Top Failed Login Users** — ranked table of users with the most failures.
- **Top Failure Source IPs (Spray Risk)** — ranked table of IPs with the most failures across distinct users. The investigation entry point for spray detection.
- **API Activity by Actor & Action** — breakdown of API calls by which token (actor) made them and what action was taken. Anomalous actors or unusual action patterns surface here.
- **Recent Lockouts & Unlocks** — tail of recent lockout and unlock events for live inspection during active incidents.

## Data sources

- Okta system log (sourcetype `OktaIM2:log` in the Okta index).

## Notes

- The "Suspicious IPs (3+ users failed)" tile uses a deliberately conservative threshold. A real spray will typically blow far past three; the threshold is set low so the panel surfaces emerging patterns before they're already a confirmed attack.
- API activity panels exist because API token compromise is a different attack surface from user credential compromise, and the two need separate visibility. A burst of failed user logins is one signal; a burst of unusual API calls is a different signal that wouldn't show up in the user-failure panels.
