# DUO: MFA Trends v2

Duo multi-factor authentication trends over time. Breaks down MFA success and failure rates by reason, authentication factor, device OS, and application.

## What problem this solves

The ADFS+Duo and Okta+Duo dashboards both show MFA outcomes in their broader sign-in context, but sometimes the question is just about Duo: which factors are people actually using, what's the success/failure mix per factor, are particular OS versions failing more, are specific applications producing different outcomes. This dashboard isolates those questions and provides flexible group-by controls so the same data can be sliced multiple ways without rewriting queries.

## Panels

- **Total MFA Events** — total Duo authentication event count in the window.
- **MFA Trends Over Time** — time chart of MFA outcomes, colored by the active group-by dimension.
- **Breakdown** — categorical breakdown of MFA outcomes by the active group-by dimension.
- **Detail Table** — per-row Duo event detail for filtered subsets.

## Data sources

- Duo authentication log index.

## Notes

- The Group By selector switches the dashboard's lens: by reason, by factor, by OS, by application. Same underlying data, four different framings. Useful for pivoting between "what's happening" (factor breakdown) and "why is it happening" (failure-reason breakdown) without leaving the dashboard.
