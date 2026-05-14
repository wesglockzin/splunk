# Okta: Policy & MFA Monitor

Sign-on policy evaluations, routing rule hits, MFA factor usage and failures — combined into a single operational view.

## What problem this solves

The Policy Monitor answers "did the policy do what we configured?" and the MFA Monitor answers "are MFA challenges resolving correctly?" Both questions often get asked together: "is the policy triggering MFA, and when it does, are users completing it?" This dashboard combines them so that flow can be inspected end-to-end without switching dashboards.

## Panels

- **Policy Evaluations** — total policy-evaluation event count in the window.
- **Policy Denies** — count of evaluations that resulted in denied access.
- **MFA Challenges** — count of MFA challenges triggered.
- **MFA Failures** — count of failed MFA challenges.
- **Policy Evaluations Over Time** — time chart of policy activity by outcome.
- **Apps Evaluated by Auth Policy** — table of applications and which auth policy each was evaluated against.
- **Auth Policy Rules Hit** — ranked list of which policy rules are being matched most often.
- **MFA Factor Breakdown** — proportion of MFA challenges by factor type.
- **MFA Failures by User & Factor** — table of users with failure counts split by factor.
- **Recent Policy Denies** — tail of the most recent policy-deny events for live inspection.

## Data sources

- Okta system log (sourcetype `OktaIM2:log` in the Okta index).

## Notes

- Where the standalone Policy Monitor and MFA Monitor are tactical (one focused investigation each), this combined dashboard is the broader operational view — the one to open when a stakeholder asks "show me the policy + MFA picture" rather than drilling into a specific issue.
