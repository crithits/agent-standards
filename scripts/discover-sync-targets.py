#!/usr/bin/env python3
"""Find the repos that should receive the shared agent files.

A repo is a target when the sync GitHub App is installed on it, it isn't
archived, it isn't this repo, and it has the marker file (AGENTS.local.md by
default) at the root of its default branch.

The script masks every repo name it sees in the Actions logs before doing
anything else with it, and never prints names itself. It renders the sync
config from a template by replacing the __REPOS__ placeholder.

Usage:
  GH_TOKEN=<installation token> discover-sync-targets.py TEMPLATE OUTPUT

Environment:
  GH_TOKEN          GitHub App installation token (required)
  GITHUB_API_URL    API base (set by Actions; defaults to api.github.com)
  GITHUB_REPOSITORY This repo, excluded from targets (set by Actions)
  GITHUB_OUTPUT     If set, writes `count=<n>` for later steps
  SYNC_MARKER_FILE  Marker file name (default: AGENTS.local.md)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator
from typing import Any

PLACEHOLDER = "__REPOS__"
PAGE_SIZE = 100


def api_get(path: str) -> Any:
    base = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    request = urllib.request.Request(
        base + path,
        headers={
            "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def mask(value: str) -> None:
    # Workflow command: Actions replaces this value with *** in all later log output.
    print(f"::add-mask::{value}", flush=True)


def installation_repos() -> Iterator[dict[str, Any]]:
    page = 1
    while True:
        data = api_get(f"/installation/repositories?per_page={PAGE_SIZE}&page={page}")
        repos = data["repositories"]
        yield from repos
        if len(repos) < PAGE_SIZE:
            return
        page += 1


def has_marker(full_name: str, marker: str) -> bool:
    path = f"/repos/{full_name}/contents/{urllib.parse.quote(marker)}"
    try:
        api_get(path)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False
        # Don't let the default traceback print the URL (it contains the repo name).
        raise SystemExit(f"GitHub API error {error.code} while checking a repository for {marker}") from None
    return True


def render(template: str, repos: list[str]) -> str:
    """Replace the line consisting solely of the placeholder with one indented line per repo."""
    lines = template.splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines) if line.strip() == PLACEHOLDER]
    if len(matches) != 1:
        raise SystemExit(f"Template must have exactly one line containing only {PLACEHOLDER} (found {len(matches)})")
    index = matches[0]
    line = lines[index]
    indent = line[: len(line) - len(line.lstrip())]
    lines[index] = "".join(f"{indent}{repo}\n" for repo in repos)
    return "".join(lines)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    template_path, output_path = sys.argv[1], sys.argv[2]
    marker = os.environ.get("SYNC_MARKER_FILE", "AGENTS.local.md")
    this_repo = os.environ.get("GITHUB_REPOSITORY", "").lower()

    candidates: list[str] = []
    seen = 0
    for repo in installation_repos():
        seen += 1
        name, full_name = repo["name"], repo["full_name"]
        mask(name)
        mask(full_name)
        if repo.get("archived") or full_name.lower() == this_repo:
            continue
        candidates.append(full_name)

    targets = sorted(full_name for full_name in candidates if has_marker(full_name, marker))

    with open(template_path, encoding="utf-8") as file:
        template = file.read()
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(render(template, targets))

    print(f"App can reach {seen} repos; {len(targets)} have {marker} and will be synced.")
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as file:
            file.write(f"count={len(targets)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
