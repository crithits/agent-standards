"""Tests for discover_sync_targets.py against a fake GitHub API.

Run: python3 -m unittest discover -s scripts
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest.mock
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, str(Path(__file__).parent))
import discover_sync_targets as dst  # noqa: E402

FILES_JSON = Path(__file__).parent.parent / ".github" / "sync-files.json"
TOKEN = "test-token"


def repo(name: str, archived: bool = False, branch: str = "main") -> dict[str, Any]:
    return {"name": name, "full_name": f"crithits/{name}", "archived": archived, "default_branch": branch}


class FakeGitHub:
    """Serves /installation/repositories and /repos/{r}/git/trees and /contents."""

    def __init__(self) -> None:
        self.repos: list[dict[str, Any]] = []
        self.trees: dict[str, list[str]] = {}  # full_name -> file paths
        self.truncated: set[str] = set()
        self.empty: set[str] = set()
        self.failing: set[str] = set()
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:
                pass

            def reply(self, status: int, body: Any) -> None:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(body).encode())

            def do_GET(self) -> None:
                if self.headers.get("Authorization") != f"Bearer {TOKEN}":
                    return self.reply(401, {})
                url = urlparse(self.path)
                if url.path == "/installation/repositories":
                    query = parse_qs(url.query)
                    size, page = int(query["per_page"][0]), int(query["page"][0])
                    chunk = fake.repos[(page - 1) * size : page * size]
                    return self.reply(200, {"total_count": len(fake.repos), "repositories": chunk})
                parts = [unquote(p) for p in url.path.split("/")]
                full = f"{parts[2]}/{parts[3]}"
                if full in fake.failing:
                    return self.reply(500, {"message": "boom"})
                if parts[4] == "git":
                    if full in fake.empty:
                        return self.reply(409, {"message": "Git Repository is empty."})
                    paths = fake.trees.get(full, [])
                    tree = [{"path": p, "type": "blob"} for p in paths]
                    return self.reply(200, {"tree": tree, "truncated": full in fake.truncated})
                if parts[4] == "contents":
                    wanted = "/".join(parts[5:])
                    found = wanted in fake.trees.get(full, [])
                    return self.reply(200 if found else 404, {})
                return self.reply(404, {})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.server.shutdown()


class DiscoverSyncTargetsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.api = FakeGitHub()
        self.tmp = tempfile.TemporaryDirectory()
        self.output = Path(self.tmp.name) / "sync.generated.json"
        self.gh_output = Path(self.tmp.name) / "github_output"
        self.env = {
            "GH_TOKEN": TOKEN,
            "GITHUB_API_URL": self.api.url,
            "GITHUB_REPOSITORY": "crithits/agent-standards",
            "GITHUB_OUTPUT": str(self.gh_output),
        }

    def tearDown(self) -> None:
        self.api.close()
        self.tmp.cleanup()

    def run_script(self) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        argv = ["discover_sync_targets.py", str(FILES_JSON), str(self.output)]
        with (
            unittest.mock.patch.dict(os.environ, self.env),
            unittest.mock.patch.object(sys, "argv", argv),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            code = dst.main()
        return code, stdout.getvalue(), stderr.getvalue()

    def groups(self) -> dict[str, list[str]]:
        """Map each group's AGENTS.md dest folder to its repos."""
        config = json.loads(self.output.read_text())
        result = {}
        for group in config["group"]:
            agents = next(f["dest"] for f in group["files"] if f["source"] == "agents/AGENTS.md")
            result[agents.removesuffix("AGENTS.md")] = group["repos"].split("\n")
        return result

    def test_root_and_subfolder_markers(self) -> None:
        self.api.repos = [repo("web-app"), repo("monorepo"), repo("no-marker")]
        self.api.trees = {
            "crithits/web-app": ["AGENTS.local.md", "src/App.tsx"],
            "crithits/monorepo": ["AGENTS.md", "apps/admin/frontend/AGENTS.local.md", "server/Main.java"],
            "crithits/no-marker": ["README.md"],
        }
        code, _, _ = self.run_script()
        self.assertEqual(code, 0)
        self.assertEqual(
            self.groups(),
            {"": ["crithits/web-app"], "apps/admin/frontend/": ["crithits/monorepo"]},
        )
        self.assertEqual(self.gh_output.read_text(), "count=2\n")

    def test_subfolder_dests_are_prefixed_and_skills_are_scoped(self) -> None:
        self.api.repos = [repo("monorepo")]
        self.api.trees = {"crithits/monorepo": ["apps/web/AGENTS.local.md"]}
        self.run_script()
        files = json.loads(self.output.read_text())["group"][0]["files"]
        dests = sorted(f["dest"] for f in files)
        self.assertIn("apps/web/CLAUDE.md", dests)
        self.assertIn("apps/web/.claude/skills/vercel-react-best-practices/", dests)
        # deleteOrphaned only ever applies to a single vendored skill folder,
        # never to a whole skills/ directory that might hold the repo's own skills.
        for entry in files:
            if entry.get("deleteOrphaned"):
                self.assertRegex(entry["dest"], r"skills/vercel-[a-z-]+/$")

    def test_skips_archived_self_empty_and_ignored_folders(self) -> None:
        self.api.repos = [
            repo("archived", archived=True),
            repo("agent-standards"),
            repo("empty"),
            repo("vendored"),
        ]
        self.api.trees = {
            "crithits/archived": ["AGENTS.local.md"],
            "crithits/agent-standards": ["AGENTS.local.md"],
            "crithits/vendored": ["node_modules/pkg/AGENTS.local.md", ".claude/x/AGENTS.local.md"],
        }
        self.api.empty = {"crithits/empty"}
        code, _, _ = self.run_script()
        self.assertEqual(code, 0)
        self.assertEqual(self.groups(), {})
        self.assertEqual(self.gh_output.read_text(), "count=0\n")

    def test_paginates_installation_repos(self) -> None:
        self.api.repos = [repo(f"filler-{i:03d}") for i in range(150)] + [repo("late")]
        self.api.trees = {"crithits/late": ["AGENTS.local.md"]}
        code, stdout, _ = self.run_script()
        self.assertEqual(code, 0)
        self.assertEqual(self.groups(), {"": ["crithits/late"]})
        self.assertIn("App can reach 151 repos; 1 opted in", stdout)

    def test_truncated_tree_falls_back_to_root_marker(self) -> None:
        self.api.repos = [repo("huge")]
        self.api.trees = {"crithits/huge": ["AGENTS.local.md", "deep/AGENTS.local.md"]}
        self.api.truncated = {"crithits/huge"}
        self.run_script()
        self.assertEqual(self.groups(), {"": ["crithits/huge"]})

    def test_names_are_masked_and_never_printed(self) -> None:
        self.api.repos = [repo("secret-client-app"), repo("broken-client")]
        self.api.trees = {"crithits/secret-client-app": ["AGENTS.local.md"]}
        self.api.failing = {"crithits/broken-client"}
        code, stdout, stderr = self.run_script()
        self.assertEqual(code, 1)  # API failure stops the run
        mask_lines = [line for line in stdout.splitlines() if line.startswith("::add-mask::")]
        self.assertIn("::add-mask::secret-client-app", mask_lines)
        self.assertIn("::add-mask::crithits/broken-client", mask_lines)
        visible = "\n".join(line for line in (stdout + stderr).splitlines() if not line.startswith("::add-mask::"))
        self.assertNotIn("secret-client", visible)
        self.assertNotIn("broken-client", visible)


if __name__ == "__main__":
    unittest.main()
