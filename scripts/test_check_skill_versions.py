"""Tests for check_skill_versions.py against throwaway git repos.

Run: python3 -m unittest discover -s scripts
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_skill_versions as csv  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def skill_md(version: int | None, body: str = "Do the thing.") -> str:
    line = f"Skill version: {version}\n\n" if version is not None else ""
    return f"---\nname: demo\ndescription: x\n---\n\n# Demo\n\n{line}{body}\n"


def agents_md(**versions: int) -> str:
    lines = "\n".join(f"- `{name}` (version {v}) — does things." for name, v in versions.items())
    return f"# AGENTS.md\n\n## Skills\n\n- `vercel-react-best-practices` — no version.\n{lines}\n"


class Repo:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")

    def git(self, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True, text=True).stdout

    def write(self, path: str, text: str) -> None:
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text)

    def commit(self, message: str = "change") -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD").strip()

    def close(self) -> None:
        self._tmp.cleanup()


class CheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo()
        self.addCleanup(self.repo.close)
        self.repo.write("skills/demo/SKILL.md", skill_md(1))
        self.repo.write("skills/demo/references/notes.md", "notes\n")
        self.repo.write("agents/AGENTS.md", agents_md(demo=1))
        self.base = self.repo.commit("base")

    def check(self, base: str | None = None) -> list[str]:
        return csv.check(self.repo.root, base)

    def test_matching_versions_pass(self) -> None:
        self.assertEqual(self.check(), [])

    def test_missing_version_line(self) -> None:
        self.repo.write("skills/demo/SKILL.md", skill_md(None))
        self.assertEqual(self.check(), ["skills/demo/SKILL.md: add a `Skill version: N` line"])

    def test_skill_not_listed(self) -> None:
        self.repo.write("agents/AGENTS.md", agents_md())
        self.assertEqual(self.check(), ["agents/AGENTS.md: list `demo` as - `demo` (version 1)"])

    def test_listed_version_differs(self) -> None:
        self.repo.write("agents/AGENTS.md", agents_md(demo=2))
        self.assertEqual(
            self.check(), ["agents/AGENTS.md lists `demo` as version 2, but skills/demo/SKILL.md says 1"]
        )

    def test_listed_skill_that_does_not_exist(self) -> None:
        self.repo.write("agents/AGENTS.md", agents_md(demo=1, ghost=3))
        self.assertEqual(
            self.check(), ["agents/AGENTS.md lists a version for `ghost`, but skills/ghost/SKILL.md doesn't exist"]
        )

    def test_unchanged_skill_needs_no_bump(self) -> None:
        self.repo.write("README.md", "unrelated\n")
        self.repo.commit()
        self.assertEqual(self.check(self.base), [])

    def test_change_without_bump_fails(self) -> None:
        self.repo.write("skills/demo/references/notes.md", "new notes\n")
        self.repo.commit()
        self.assertEqual(
            self.check(self.base),
            ["skills/demo/ changed since " + self.base + ": raise its version above 1, "
             "in skills/demo/SKILL.md and agents/AGENTS.md"],
        )

    def test_change_with_bump_passes(self) -> None:
        self.repo.write("skills/demo/SKILL.md", skill_md(2, "Do the thing better."))
        self.repo.write("agents/AGENTS.md", agents_md(demo=2))
        self.repo.commit()
        self.assertEqual(self.check(self.base), [])

    def test_first_version_line_counts_as_a_bump(self) -> None:
        self.repo.write("skills/demo/SKILL.md", skill_md(None))
        base = self.repo.commit("no version yet")
        self.repo.write("skills/demo/SKILL.md", skill_md(1))
        self.repo.commit()
        self.assertEqual(self.check(base), [])

    def test_new_skill_needs_no_bump(self) -> None:
        self.repo.write("skills/fresh/SKILL.md", skill_md(1))
        self.repo.write("agents/AGENTS.md", agents_md(demo=1, fresh=1))
        self.repo.commit()
        self.assertEqual(self.check(self.base), [])

    def test_bad_base_ref_raises(self) -> None:
        with self.assertRaises(RuntimeError):
            self.check("no-such-ref")


class RealRepoTest(unittest.TestCase):
    def test_this_repo_is_consistent(self) -> None:
        self.assertEqual(csv.check(REPO_ROOT), [])


if __name__ == "__main__":
    unittest.main()
