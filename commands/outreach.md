---
description: Find supervisors at a university or country, study their work, check fit, and draft personal emails. Never sends.
argument-hint: "<university or country> [field] [max N] [include maybe] [tracker <path>] [refresh style]"
allowed-tools: Agent, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

Input: $ARGUMENTS

You run a team of four agents. Paths:
- DATA = the absolute path of `outreach-data` inside the current working directory. This holds the applicant's own data. Never use the plugin folder for it: Claude Code blocks writes there, and plugin updates replace it.
- TEMPLATES = `${CLAUDE_PLUGIN_ROOT}/templates`
- CHECKER = `${CLAUDE_PLUGIN_ROOT}/scripts/check_draft.py`

Work moves between agents through files in DATA, not chat. Give each agent only: the DATA path (and CHECKER for the task handler), plus the options below. Do not paste profiles, reviews or drafts into prompts.

The team never sends email. Drafts only. If the input is empty, ask for a university or country and stop.

## First-run setup

Create anything missing in DATA:
- `DATA/tracker.csv`: create it containing only this header line:
  `slug,name,title,university,department,country,email,faculty_page,lab_page,scholar_or_dblp,recruiting,source,status,fit_score,verdict,draft_file,sent_date,followup_date,notes`
- `DATA/style-guide.md`: copy it from `TEMPLATES/style-guide.md`.
- `DATA/me.md`: copy `TEMPLATES/me.example.md` there, tell me to fill it in, and stop.

## Options

Read these options from the input:
- place: one university, a country, or a list of universities
- field: optional
- max N: new professors to find this run, default 8
- include maybe: also draft for `maybe` verdicts
- tracker <path>: an existing tracker spreadsheet to skip people from
- refresh style: re-run step 0

## Step 0: style guide

Run this only if the input says `refresh style`. Otherwise use the copy that setup put in DATA.

Search the web for advice on emailing prospective supervisors. Use university and faculty pages first (graduate school "contacting a supervisor" pages, professors' own "read this before emailing me" pages), not blogs selling services. Read 6 to 10 of them. Write `DATA/style-guide.md` with:
- the points most sources agree on
- the things professors say annoy them
- the source links

## Steps 1 to 4

Run in order, one agent at a time. Each stage works on every tracker row in its input status, so a run also finishes rows an earlier run left behind.

1. `supervisor-outreach-team:administrator`: pass DATA, place, field, max N, tracker path. Adds rows with status `found`.
2. `supervisor-outreach-team:researcher`: pass DATA. Moves `found` to `profiled`.
3. `supervisor-outreach-team:reviewer`: pass DATA. Moves `profiled` to `reviewed` or `skip - fit`.
4. `supervisor-outreach-team:task-handler`: pass DATA, CHECKER, and whether to include maybe. Moves `reviewed` to `drafted`.

If an agent fails, note it in the tracker and carry on with whatever the next stage can still do.

## Report

Read `DATA/tracker.csv` and show a table of the rows touched this run: name, university, fit score, verdict, draft file. Include skipped rows and why.

Then list everything I need to check: missing emails, failed pages, each draft's "Check before sending" notes, and any draft that did not pass the checker.

Add one line reminding me that nothing was sent, and that once I send one I can record it with `/outreach-status mark <slug> sent`.
