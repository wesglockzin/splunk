# Okta: Policy Monitor

Auth policy evaluations, MFA challenge triggers, and IDP-authenticated sessions on the Okta side.

## What problem this solves

Okta's authentication policies decide who gets MFA-challenged, who gets passed through, and who gets denied. When those decisions don't match expectations — a user gets unexpectedly challenged, or doesn't get challenged when they should — the answer lives in policy evaluation events. This dashboard surfaces those evaluations alongside the MFA-trigger and IDP-session counts, so the question "did the policy do what we configured it to do?" can be answered without exporting raw events.

## Panels

- **Policy Evaluations** — total policy-evaluation event count in the window.
- **MFA Challenges** — count of MFA challenges triggered as policy outcomes.
- **Challenge Rate %** — percentage of evaluations that triggered a challenge.
- **Policy Denies** — count of evaluations that resulted in denied access.
- **Policy Evaluations Over Time** — time chart of policy activity, broken down by outcome.
- **Application × Policy Rule** — cross-tab showing which apps are being evaluated against which policy rules. A useful integrity check: an app showing up against an unexpected rule means the rule's matching criteria need review.
- **MFA Required by Policy Rule** — counts of MFA-required evaluations per rule.
- **IDP-Authenticated Sessions** — sessions where authentication was delegated to a federated IDP. Tracks the IDP-routing path independently from the local-Okta auth path.

## Data sources

- Okta system log (sourcetype `OktaIM2:log` in the Okta index).

## Notes

- The Application × Policy Rule cross-tab is the most-used panel for verifying policy changes. After publishing a new rule, this panel shows which apps the rule is actually catching — which is often different from what was intended at config time, and that gap is exactly what this dashboard exists to expose.
