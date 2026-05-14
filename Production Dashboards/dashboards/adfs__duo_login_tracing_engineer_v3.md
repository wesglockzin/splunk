# ADFS + Duo: Correlated Login Tracing

Session-level ADFS sign-ins with correlated Duo activity, classified by match type — matched, direct Duo, no match, and expected-state outcomes. Successor to the v2 engineer tracer; this version pre-correlates ADFS sessions with their Duo MFA events so the analyst doesn't have to do the join in their head.

## What problem this solves

Investigating an authentication issue often means cross-referencing two log streams: ADFS session events on the Windows side, and Duo authentication events on the Duo side. v2 surfaces both raw streams; v3 does the correlation up front and presents one row per session with the Duo outcome already attached. The classification (matched / direct / no match / expected state) makes it explicit when a session **should** have produced a Duo event but didn't — which is often the most diagnostic signal.

## Panels

- **SSO Total** — total session count in the filtered window.
- **SSO Outcome Distribution** — proportion of session outcomes.
- **Correlated Login Sessions** — per-session table with both the ADFS session detail and the matched Duo activity, including the classification: matched (ADFS+Duo paired), direct Duo (Duo without ADFS context), no match (ADFS without Duo where one was expected), expected state (ADFS without Duo and that's correct).
- **Login Outcomes Over Time** — outcomes plotted over time so trends within the window are visible alongside the per-session detail.

## Lookups

- `ADFS_friendly_names` — readable RP names in the correlated table.

## Data sources

- Duo authentication log index.
- Windows event log index — for ADFS-side session events.

## Notes

- The "no match" classification is the highest-signal outcome for security investigations. It means an ADFS session was expected to challenge Duo but didn't — possible indicators include policy misconfiguration, MFA-bypass attempts, or session-cache abuse. Worth filtering by this outcome periodically as a routine sweep.
