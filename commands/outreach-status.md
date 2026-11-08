---
description: Show the supervisor tracker and who is due a follow-up. Can also record sent emails and replies.
argument-hint: "[mark <slug> sent|replied [YYYY-MM-DD]]"
allowed-tools: Read, Edit, Write, Grep, Glob
---

Input: $ARGUMENTS

Tracker: `${CLAUDE_PLUGIN_ROOT}/data/tracker.csv`. Drafts: `${CLAUDE_PLUGIN_ROOT}/data/drafts/`.

## If the input starts with `mark`

Update that slug's row:
- `sent`: set status `sent` and `sent_date` to the given date, or today.
- `replied`: set status `replied`.

Keep CSV quoting intact. Say what changed, then continue below.

## Show the tracker

Show the count per status, then a table: name, university, status, fit score, verdict, sent date, draft file. Sort by status, with `drafted` first. Keep notes out of the table, except any row whose notes flag a missing email or a failed step.

## Follow-ups

List anyone with status `sent`, no `followup_date`, and a `sent_date` more than 7 days ago. Show how many days it has been. Rows at 7 to 10 days are due now, and rows past 10 are overdue.

If anyone is listed, offer to write follow-ups. Do not write them until I say yes. When I do, for each person:
- Read their draft file and every `## Follow-up` section in `data/drafts/` so no wording repeats.
- Write two plain lines for the same thread. Mention one specific thing from the original email. Ask once, without pressure and without apology.
- Same language rules as the emails: no em dashes, no flattery, no stock phrases such as "just following up" or "circling back".
- Append it to their draft file under `## Follow-up`, and set `followup_date` only when I tell you it was sent.

Only one follow-up per person. Never send anything.
