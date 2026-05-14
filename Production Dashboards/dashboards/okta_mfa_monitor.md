# Okta: MFA Monitor

MFA challenge outcomes, factor usage breakdown, failures by user, and enrollment activity on the Okta side.

## What problem this solves

When users report MFA problems on Okta — "I'm not getting the push," "my factor isn't accepted," "I keep getting locked out" — this dashboard is the place to triage the report. It shows MFA challenges per outcome, which factors are being used, which users are seeing the most failures, and what enrollment activity has been happening. Most reports resolve to one of: factor expired, user trying the wrong factor, or genuine Okta-side issue — and the dashboard distinguishes among them.

## Panels

- **MFA Challenges** — total MFA challenge event count in the window.
- **Failures** — count of failed MFA challenges.
- **Abandoned** — count of MFA challenges the user did not complete (timed out without answering).
- **Failure Rate %** — percentage of MFA challenges that ended in failure.
- **MFA Challenges Over Time** — time chart of MFA activity, color-coded by outcome.
- **Factor Breakdown** — proportion of MFA challenges by factor type (push, TOTP, SMS, hardware, etc.).
- **Failures by User & Factor** — table of users with failure counts split by factor. Identifies users repeatedly failing on a specific factor.
- **Enrollment Activity** — record of factor-enrollment events. New enrollments and de-enrollments are useful context for "this factor isn't working" reports.
- **Recent MFA Failures** — tail of the most recent MFA failure events for live inspection.

## Data sources

- Okta system log (sourcetype `OktaIM2:log` in the Okta index).

## Notes

- "Abandoned" is a distinct outcome from "failure" and worth treating that way. A failure is a denied challenge; abandoned is a challenge the user never answered. Mass abandonment can indicate notification delivery problems (push not arriving) rather than authentication problems.
