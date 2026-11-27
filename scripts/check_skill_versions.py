#!/usr/bin/env python3
"""Check that each skill's version is stated, listed in AGENTS.md, and bumped.

Agents compare the `Skill version: N` line in an installed skill with the
version agents/AGENTS.md lists for it, and prompt the user to update when the
installed one is older. That only works if:

- every skills/<name>/SKILL.md has a `Skill version: N` line;
- agents/AGENTS.md lists the skill as `` - `<name>` (version N) `` with the same N;
- with --base, any change under skills/<name>/ since that ref raises N.

Usage:
  check_skill_versions.py [--base REF] [ROOT]

ROOT defaults to the repo root. Exits 1 and prints one line per problem.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SKILL_VERSION = re.compile(r"^Skill version: (\d+)\s*$", re.MULTILINE)
LISTED_VERSION = re.compile(r"^- `([A-Za-z0-9_-]+)` \(version (\d+)\)", re.MULTILINE)


def skill_version(text: str) -> int | None:
    match = SKILL_VERSION.search(text)
    return int(match.group(1)) if match else None


def listed_versions(agents_md: str) -> dict[str, int]:
    return {name: int(version) for name, version in LISTED_VERSION.findall(agents_md)}


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def base_version(root: Path, base: str, name: str) -> int | None:
    """The skill's version at base: None if the skill didn't exist, 0 if it had no line."""
    shown = git(root, "show", f"{base}:skills/{name}/SKILL.md")
    if shown.returncode != 0:
        return None
    return skill_version(shown.stdout) or 0


def changed_since(root: Path, base: str, name: str) -> bool:
    diff = git(root, "diff", "--name-only", base, "HEAD", "--", f"skills/{name}/")
    if diff.returncode != 0:
        raise RuntimeError(f"git diff against {base} failed: {diff.stderr.strip()}")
    return bool(diff.stdout.strip())


def check(root: Path, base: str | None = None) -> list[str]:
    problems: list[str] = []
    listed = listed_versions((root / "agents" / "AGENTS.md").read_text())
    skills = sorted(p.parent.name for p in (root / "skills").glob("*/SKILL.md"))

    for name in skills:
        path = f"skills/{name}/SKILL.md"
        version = skill_version((root / path).read_text())
        if version is None:
            problems.append(f"{path}: add a `Skill version: N` line")
            continue
        if name not in listed:
            problems.append(f"agents/AGENTS.md: list `{name}` as - `{name}` (version {version})")
        elif listed[name] != version:
            problems.append(
                f"agents/AGENTS.md lists `{name}` as version {listed[name]}, but {path} says {version}"
            )
        if base is not None and changed_since(root, base, name):
            before = base_version(root, base, name)
            if before is not None and version <= before:
                problems.append(
                    f"skills/{name}/ changed since {base}: raise its version above {before}, "
                    f"in {path} and agents/AGENTS.md"
                )

    for name in sorted(set(listed) - set(skills)):
        problems.append(f"agents/AGENTS.md lists a version for `{name}`, but skills/{name}/SKILL.md doesn't exist")

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", help="git ref to compare against; skills changed since then must raise their version")
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parent.parent))
    args = parser.parse_args(argv)

    problems = check(Path(args.root), args.base)
    for problem in problems:
        print(problem)
    if not problems:
        print("Skill versions OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
