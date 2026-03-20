---
name: feature-planner
description: >
  Plan a feature by creating a Forgejo milestone and a batch of LLM-executable issues.
  Use when breaking down a brief (docs/briefs/<feature>.md) into actionable work.
  Creates milestone, writes detailed issues with steps/acceptance-criteria that a
  lower-reasoning model can execute autonomously, and links everything together.
---

# Feature Planner

Turn a feature brief into a Forgejo milestone + a set of self-contained, LLM-executable issues.

## When to use

- You have a feature brief in `docs/briefs/<feature>.md`
- You need to break it into concrete work items
- Issues should be detailed enough for a sub-agent (lower-reasoning LLM) to pick up and execute without additional context

## Workflow

### 1. Read the brief

Read `docs/briefs/<feature>.md` to understand the goal, architecture, and open questions.

### 2. Create the milestone

Use the script to create a Forgejo milestone:

```bash
FORGEJO_TOKEN=... \
python3 ./skills/public/feature-planner/scripts/feature_planner.py milestone \
  --base-url <forgejo-base-url> \
  --owner <owner> --repo <repo> \
  --title "<milestone title>" \
  --description "See docs/briefs/<feature>.md"
```

Returns the milestone ID for use in issue creation.

### 3. Plan the issues

Before creating issues, plan them as a batch. Each issue needs:

| Field | Required | Description |
|-------|----------|-------------|
| title | ✅ | `<type>: <clear action>` (e.g. `feat: add --json output to script`) |
| goal | ✅ | One sentence: what does "done" look like? |
| context | ✅ | Files/systems involved, link to brief, relevant background |
| steps | ✅ | Numbered, concrete actions with file paths and commands |
| acceptance_criteria | ✅ | Checkboxes a reviewer can verify |
| depends_on | optional | Issue numbers that must complete first |

### 4. Create issues in batch

Write a JSON file with all issues, then create them:

```bash
FORGEJO_TOKEN=... \
python3 ./skills/public/feature-planner/scripts/feature_planner.py issues \
  --base-url <forgejo-base-url> \
  --owner <owner> --repo <repo> \
  --milestone-id <id> \
  --issues-file /path/to/issues.json
```

#### Issues JSON format

See `references/issues_example.json` for the full schema. Summary:

```json
[
  {
    "title": "feat: add --json output mode to process_downloads.py",
    "goal": "The script can output a structured JSON summary to stdout when invoked with --json.",
    "context": "Script: scripts/process_downloads.py\nBrief: docs/briefs/process-downloads-agent.md",
    "steps": [
      "Add an `--json` argparse flag to `scripts/process_downloads.py`.",
      "When `--json` is passed, collect all processing results into a list of dicts.",
      "At the end of the run, print the JSON array to stdout (one line, compact).",
      "Ensure the existing text log and audit JSONL are unaffected."
    ],
    "acceptance_criteria": [
      "Running `python3 scripts/process_downloads.py --json --dry-run` produces valid JSON on stdout",
      "Existing log output is unchanged when --json is not passed",
      "No secrets or absolute paths leak into the JSON output"
    ],
    "depends_on": [],
    "labels": ["feat"]
  }
]
```

### 5. Review

After creation, the script prints a summary of all issues created with their numbers and URLs. Review in Forgejo to confirm everything looks right.

## Issue body format (what gets created)

The script renders each issue body using this structure:

```markdown
## Goal
<goal>

## Context
<context>

Brief: docs/briefs/<feature>.md

## Steps
1. <step 1>
2. <step 2>
...

## Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>
...

## Dependencies
- Depends on #<N>
```

## Sizing guidance

| Project size | Issues | Examples |
|-------------|--------|----------|
| Tiny | 1–2 | Config tweak, doc update |
| Small | 3–5 | Add a flag to a script, new cron job |
| Medium | 5–12 | New agent feature, integration |
| Large | 12–20+ | Full system build-out |

## Labels (suggested)

- **Type:** `feat`, `fix`, `chore`, `docs`, `test`, `refactor`
- **Priority:** `p0-critical`, `p1-high`, `p2-normal`, `p3-low`
- **Status:** `blocked`, `needs-design`, `ready`

## Notes

- Always create the milestone first (you need the ID for issues).
- The script handles dependency text in issue bodies but does NOT enforce ordering — that's on the executing agent/human.
- If Forgejo is down, you can draft the issues JSON locally and create them later.
- Do not put secrets in issue bodies.
