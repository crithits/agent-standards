#!/usr/bin/env python3
"""Find where the shared agent files should go, and write the sync config.

A target is a folder containing the marker file (AGENTS.local.md by default)
in a repo that the sync GitHub App is installed on, that isn't archived, and
that isn't this repo. A marker at the repo root syncs the files to the root.
A marker in a subfolder, such as apps/web/AGENTS.local.md, syncs them into
that folder, for monorepos where only one part is React + TypeScript.

Every repo name is masked in the Actions logs before anything else is done
with it, and the script never prints names itself.

The files to sync come from FILES_JSON (a list of repo-file-sync-action file
entries with paths relative to the target folder). The output is a
repo-file-sync-action config, written as JSON (which is valid YAML).

Usage:
  GH_TOKEN=<installation token> discover_sync_targets.py FILES_JSON OUTPUT

Environment:
  GH_TOKEN          GitHub App installation token (required)
  GITHUB_API_URL    API base (set by Actions; defaults to api.github.com)
  GITHUB_REPOSITORY This repo, excluded from targets (set by Actions)
  GITHUB_OUTPUT     If set, writes `count=<n>` (number of target folders)
  SYNC_MARKER_FILE  Marker file name (default: AGENTS.local.md)
"""

from __future__ import annotations

import json
import os
import posixpath
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator
from typing import Any

PAGE_SIZE = 100
# Folders a marker is never honored in.
IGNORED_DIRS = {"node_modules", ".git", ".agents", ".claude"}


class ApiError(Exception):
    def __init__(self, status: int) -> None:
        super().__init__(f"GitHub API returned {status}")
        self.status = status


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
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        # Re-raise without the URL, which contains the repo name.
        raise ApiError(error.code) from None


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


def is_marker_path(path: str, marker: str) -> bool:
    parts = path.split("/")
    return parts[-1] == marker and not IGNORED_DIRS.intersection(parts[:-1])


def marker_folders(repo: dict[str, Any], marker: str) -> list[str]:
    """Folders ("" for the root) that contain the marker on the default branch."""
    full_name = repo["full_name"]
    branch = urllib.parse.quote(repo.get("default_branch") or "HEAD", safe="")
    try:
        tree = api_get(f"/repos/{full_name}/git/trees/{branch}?recursive=1")
    except ApiError as error:
        if error.status in (404, 409):  # no default branch yet / empty repo
            return []
        raise

    if not tree.get("truncated"):
        return sorted(
            posixpath.dirname(entry["path"])
            for entry in tree.get("tree", [])
            if entry.get("type") == "blob" and is_marker_path(entry["path"], marker)
        )

    # Very large repo: the recursive tree was cut off, so only honor a root marker.
    print("::warning::A repository's file tree was too large to scan; only a root marker is checked there.")
    try:
        api_get(f"/repos/{full_name}/contents/{urllib.parse.quote(marker)}")
    except ApiError as error:
        if error.status == 404:
            return []
        raise
    return [""]


def build_config(files: list[dict[str, Any]], targets: list[tuple[str, str]]) -> dict[str, Any]:
    """One group per folder path; each group's file dests are prefixed with that folder."""
    by_folder: dict[str, list[str]] = {}
    for full_name, folder in targets:
        by_folder.setdefault(folder, []).append(full_name)

    groups = []
    for folder in sorted(by_folder):
        prefix = f"{folder}/" if folder else ""
        groups.append(
            {
                "files": [{**entry, "dest": prefix + entry["dest"]} for entry in files],
                "repos": "\n".join(sorted(by_folder[folder])),
            }
        )
    return {"group": groups}


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    files_path, output_path = sys.argv[1], sys.argv[2]
    marker = os.environ.get("SYNC_MARKER_FILE", "AGENTS.local.md")
    this_repo = os.environ.get("GITHUB_REPOSITORY", "").lower()

    with open(files_path, encoding="utf-8") as file:
        files: list[dict[str, Any]] = json.load(file)

    try:
        candidates: list[dict[str, Any]] = []
        seen = 0
        for repo in installation_repos():
            seen += 1
            mask(repo["name"])
            mask(repo["full_name"])
            if repo.get("archived") or repo["full_name"].lower() == this_repo:
                continue
            candidates.append(repo)

        targets = [
            (repo["full_name"], folder)
            for repo in candidates
            for folder in marker_folders(repo, marker)
        ]
    except ApiError as error:
        print(f"::error::{error} while discovering sync targets", file=sys.stderr)
        return 1

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(build_config(files, targets), file, indent=2)
        file.write("\n")

    repo_count = len({full_name for full_name, _ in targets})
    print(
        f"App can reach {seen} repos; {repo_count} opted in "
        f"({len(targets)} folder{'s' if len(targets) != 1 else ''} with {marker})."
    )
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as file:
            file.write(f"count={len(targets)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
