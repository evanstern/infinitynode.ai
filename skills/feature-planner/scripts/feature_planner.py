#!/usr/bin/env python3
"""Feature Planner: create Forgejo milestones and batches of LLM-executable issues.

Subcommands:
  milestone  — Create a milestone
  issues     — Create issues from a JSON file and attach to a milestone

Auth: set FORGEJO_TOKEN env var or pass --token.

Examples:
  # Create milestone
  FORGEJO_TOKEN=... python3 feature_planner.py milestone \
    --base-url http://forgejo.local.infinity-node.win \
    --owner infinitynode --repo infinitynode.ai \
    --title "process-downloads-agent" \
    --description "See docs/briefs/process-downloads-agent.md"

  # Create issues
  FORGEJO_TOKEN=... python3 feature_planner.py issues \
    --base-url http://forgejo.local.infinity-node.win \
    --owner infinitynode --repo infinitynode.ai \
    --milestone-id 1 \
    --issues-file /path/to/issues.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError


# ---------------------------------------------------------------------------
# Forgejo API helpers
# ---------------------------------------------------------------------------

def api(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/json",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"

    req = Request(url, data=data, method=method, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"API error {e.code} {method} {url}: {body[:500]}", file=sys.stderr)
        raise SystemExit(1)


def base_api(args) -> str:
    return f"{args.base_url.rstrip('/')}/api/v1/repos/{args.owner}/{args.repo}"


def get_token(args) -> str:
    token = getattr(args, "token", None) or os.environ.get("FORGEJO_TOKEN")
    if not token:
        raise SystemExit("Missing token. Set FORGEJO_TOKEN or pass --token.")
    return token


# ---------------------------------------------------------------------------
# Issue body renderer
# ---------------------------------------------------------------------------

def render_issue_body(issue: dict) -> str:
    lines: list[str] = []

    lines.append("## Goal")
    lines.append(issue["goal"])
    lines.append("")

    lines.append("## Context")
    lines.append(issue["context"])
    lines.append("")

    lines.append("## Steps")
    for i, step in enumerate(issue["steps"], 1):
        lines.append(f"{i}. {step}")
    lines.append("")

    lines.append("## Acceptance Criteria")
    for ac in issue["acceptance_criteria"]:
        lines.append(f"- [ ] {ac}")
    lines.append("")

    deps = issue.get("depends_on") or []
    if deps:
        lines.append("## Dependencies")
        for d in deps:
            lines.append(f"- Depends on #{d}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Subcommand: milestone
# ---------------------------------------------------------------------------

def cmd_milestone(args):
    token = get_token(args)
    url = f"{base_api(args)}/milestones"
    payload = {"title": args.title}
    if args.description:
        payload["description"] = args.description
    if args.due_date:
        payload["due_on"] = args.due_date

    ms = api("POST", url, token, payload)
    ms_id = ms.get("id")
    ms_title = ms.get("title")
    print(f"Created milestone #{ms_id}: {ms_title}")
    print(f"Use --milestone-id {ms_id} when creating issues.")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: issues
# ---------------------------------------------------------------------------

def cmd_issues(args):
    token = get_token(args)
    issues_path = Path(args.issues_file)
    if not issues_path.exists():
        raise SystemExit(f"Issues file not found: {issues_path}")

    issues = json.loads(issues_path.read_text())
    if not isinstance(issues, list):
        raise SystemExit("Issues file must be a JSON array.")

    url_base = f"{base_api(args)}/issues"

    # First pass: create all issues (without dependency cross-refs that need real numbers).
    # We'll track a mapping from list index → issue number for dependency patching.
    created: list[dict] = []
    index_to_number: dict[int, int] = {}

    for i, issue_def in enumerate(issues):
        body = render_issue_body(issue_def)
        payload: dict = {
            "title": issue_def["title"],
            "body": body,
        }
        if args.milestone_id:
            payload["milestone"] = int(args.milestone_id)

        labels = issue_def.get("labels")
        if labels and args.resolve_labels:
            # Labels need IDs in Forgejo; for now we skip label resolution
            # and note them in the body. Future: resolve label names → IDs.
            pass

        result = api("POST", url_base, token, payload)
        number = result.get("number")
        html_url = result.get("html_url", "")
        index_to_number[i] = number
        created.append(result)
        print(f"  #{number}: {issue_def['title']}  →  {html_url}")

        # Be polite to the API
        if i < len(issues) - 1:
            time.sleep(0.3)

    # Second pass: patch issues that have depends_on referencing other issues
    # in the same batch (by list index). We use a convention: if depends_on
    # contains integers that match list indices (0-based), resolve them.
    # If they look like existing issue numbers (> len(issues)), leave as-is.
    for i, issue_def in enumerate(issues):
        deps = issue_def.get("depends_on") or []
        if not deps:
            continue

        resolved_deps = []
        for d in deps:
            if isinstance(d, int) and d < len(issues):
                # Could be a list index reference — resolve to real number
                resolved_deps.append(index_to_number[d])
            else:
                resolved_deps.append(d)

        # Rebuild body with resolved deps
        issue_def_copy = dict(issue_def)
        issue_def_copy["depends_on"] = resolved_deps
        new_body = render_issue_body(issue_def_copy)

        number = index_to_number[i]
        patch_url = f"{base_api(args)}/issues/{number}"
        api("PATCH", patch_url, token, {"body": new_body})
        time.sleep(0.2)

    print(f"\nCreated {len(created)} issues under milestone {args.milestone_id or '(none)'}.")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Feature Planner: milestones + LLM-executable issues")
    parser.add_argument("--base-url", required=True, help="Forgejo base URL")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--token", default=None)

    sub = parser.add_subparsers(dest="command")

    # milestone
    ms = sub.add_parser("milestone", help="Create a milestone")
    ms.add_argument("--title", required=True)
    ms.add_argument("--description", default="")
    ms.add_argument("--due-date", default=None, help="ISO date, e.g. 2026-04-01T00:00:00Z")

    # issues
    iss = sub.add_parser("issues", help="Create issues from JSON file")
    iss.add_argument("--milestone-id", type=int, default=None)
    iss.add_argument("--issues-file", required=True, help="Path to JSON array of issues")
    iss.add_argument("--resolve-labels", action="store_true", help="(future) Resolve label names to IDs")

    args = parser.parse_args()

    if args.command == "milestone":
        return cmd_milestone(args)
    elif args.command == "issues":
        return cmd_issues(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
