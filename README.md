# agent-standards

Shared standards for React + TypeScript repos, built so coding agents (Claude Code, Codex, Cursor, Copilot) write code the way we want, and lint catches it when they don't.

| Path                                                       | What                                                                                                                                                                                                                                       | How it reaches repos                                                                                                                 |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| `packages/eslint-config-react`                             | `@crithits/eslint-config-react`: ESLint flat config with React Compiler rules, strict type-checked typescript-eslint, jsx-a11y                                                                                                             | npm package (GitHub Packages)                                                                                                        |
| `packages/tsconfig`                                        | `@crithits/tsconfig`: strict base + React app tsconfig                                                                                                                                                                                     | npm package (GitHub Packages)                                                                                                        |
| `agents/AGENTS.md`, `agents/CLAUDE.md`                     | Rules every agent reads                                                                                                                                                                                                                    | Synced by PR (overwritten)                                                                                                           |
| `agents/AGENTS.local.md`                                   | Stub for project-specific notes; its presence opts a folder into syncing                                                                                                                                                                   | Never synced: copy it into a repo (or a monorepo subfolder) to opt in                                                                |
| Vercel skills (react-best-practices, composition-patterns) | Deeper React guidance for agents                                                                                                                                                                                                           | Not synced. Installed once per machine; `AGENTS.md` tells agents to prompt for the install when they're missing (below)              |
| `skills/pr-description`                                    | Skill agents always use to write PR titles and descriptions (problem, solution, before/after, how to test, collapsed review notes, checklist and risks). Adapted from Kibana's [`appex-pr`](https://github.com/elastic/kibana/pull/306197) | Not synced. Installed once per machine from this repo, same prompt as the Vercel skills                                              |
| Ponytail skills (ponytail, -review, -audit, -debt)         | From [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail): smallest-change coding mode, plus change review, repo audit and a ledger of deferred shortcuts                                                                 | Not synced. Installed once per machine, same prompt as the Vercel skills. Skills only, not the plugin, which adds hooks and settings |
| `unslop`                                                   | From [heydamir/unslop](https://github.com/heydamir/unslop) (CC BY 4.0): turns generic, AI-looking UI into a designed interface                                                                                                             | Not synced. Installed once per machine, same prompt as the Vercel skills                                                             |
| `security-audit`                                           | From [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill): security guidance, focused reviews, and a full audit on request                                                                                | Not synced. Installed once per machine, same prompt as the Vercel skills                                                             |
| `tdd`, `diagnosing-bugs`                                   | From [mattpocock/skills](https://github.com/mattpocock/skills): a test-first loop, and a diagnosis loop for hard bugs. Only these two of the repo's skills                                                                                 | Not synced. Installed once per machine, same prompt as the Vercel skills                                                             |

Lint is the enforcement layer; AGENTS.md is the "do this instead" layer; skills are the on-demand deep reference.

## One-time setup

1. **Push** this repo to `github.com/crithits/agent-standards`.
2. **Packages:** `ci-publish.yml` publishes to GitHub Packages with the built-in `GITHUB_TOKEN` on every push to `main` (only versions not yet published). Both packages are **public**, so CI in any repo can install them with its own `GITHUB_TOKEN` and no per-repo access grant. A package added later starts private; make it public in its _Package settings → Danger Zone → Change visibility_.
3. **Sync bot:** create a GitHub App in the org (Settings → Developer settings → GitHub Apps) with repository permissions _Contents: read & write_, _Pull requests: read & write_, _Metadata: read_. Install it on the target repos. Then in this repo:
   - Variable `AGENT_SYNC_APP_ID` = the App ID
   - Secret `AGENT_SYNC_APP_PRIVATE_KEY` = the App's private key (.pem contents)
4. **Template repo** (`crithits/react-ts-template`): its lockfile is already committed. Mark it as a template in its repo Settings → _Template repository_.

## Day to day

**Change a lint rule:** edit `packages/eslint-config-react/index.js`, add or adjust a fixture and assertion in `test/`, bump `version` (semver: new error-level rules are a major bump), merge. Repos pick it up through Renovate/Dependabot.

**Change agent rules:** edit `agents/AGENTS.md`, run `pnpm format`, merge. Every opted-in repo gets a PR. CI fails on Markdown that isn't Prettier-formatted (default settings), so the synced files pass in repos that format Markdown.

**Which repos get synced:** there's no list. `scripts/discover_sync_targets.py` asks the sync App which repos it's installed on and looks for `AGENTS.local.md` anywhere in each (archived repos, this repo, and `node_modules`/`.claude`/`.agents` folders are skipped). The shared files go into the folder holding the marker:

- `AGENTS.local.md` at the root: a React app, e.g. one made from the template. Files land at the root.
- `apps/web/AGENTS.local.md`: a monorepo where only that folder is React. Files land in `apps/web/`, and the repo's own root `AGENTS.md`/`CLAUDE.md` are untouched. Agents read the nested files when working in that folder, on top of the root ones.

What gets synced is listed in `.github/sync-files.json` (paths relative to the marker's folder). Repo names are masked in the Actions logs, so this repo can be public without revealing private or client repos. The workflow also runs weekly to catch repos created since the last change. Discovery has tests: `python3 -m unittest discover -s scripts`.

**Add a repo:** repos created from `react-ts-template` are opted in automatically. For an existing repo, copy `agents/AGENTS.local.md` into the React app's folder (the root, or a subfolder in a monorepo) and fill it in. To also use the lint/tsconfig packages, install them (below), and start with `effectRulesAsWarnings: true` if the effect rule floods it. Then run _Sync agent files_ manually or wait for the next run. If the repo runs Prettier over Markdown, add `AGENTS.md` and `CLAUDE.md` to the `.prettierignore` covering that folder: they're overwritten on every sync, and the repo's own Prettier settings may differ from the defaults used here.

**Remove a repo or folder:** delete its `AGENTS.local.md`. The already-synced files stay until you delete them.

**Skills:** each developer installs them once per machine (agents prompt for it when they're missing):

```sh
npx skills add vercel-labs/agent-skills --skill vercel-react-best-practices --skill vercel-composition-patterns -g -a claude-code -a codex -y
npx skills add crithits/agent-standards --skill pr-description -g -a claude-code -a codex -y
npx skills add DietrichGebert/ponytail --skill ponytail --skill ponytail-review --skill ponytail-audit --skill ponytail-debt -g -a claude-code -a codex -y
npx skills add heydamir/unslop --skill unslop -g -a claude-code -a codex -y
npx skills add cloudflare/security-audit-skill --skill security-audit -g -a claude-code -a codex -y
npx skills add mattpocock/skills --skill tdd --skill diagnosing-bugs -g -a claude-code -a codex -y
```

`npx skills update -g` pulls the latest of all of them. Every skill except `pr-description` comes from another repo and needs nothing from us. `pr-description` lives in `skills/pr-description/` here: edit it and merge, and developers get it on their next update. Every change must raise its `Skill version:` line and the matching `(version N)` in `agents/AGENTS.md`; CI fails otherwise. That number syncs to every repo with `AGENTS.md`, and agents that load an older installed copy tell the developer to update. `agents/AGENTS.md` makes it mandatory for every PR. To add or swap a skill for everyone, change the list and commands in `agents/AGENTS.md`.

**Ponytail plugin (opt-in, Claude Code):** we install only ponytail's skills because they're prompts, not code. Its Claude Code plugin also runs Node hooks on every session start and prompt. These hooks:

- load ponytail's rules into every session and subagent;
- add a short map of the project's existing functions and exports;
- remember the level you set with `/ponytail lite|full|ultra|off`;
- show a cost and test band above the prompt.

The plugin also writes files under `~/.claude` and `~/.config/ponytail`, and reads your Claude Code transcripts for the band. To use it, run these as two separate prompts in Claude Code (Node.js must be on your PATH):

```
/plugin marketplace add DietrichGebert/ponytail
```

```
/plugin install ponytail@ponytail
```

In its plugin options, the _Task board_ log is on by default: it writes a row per turn to `~/.config/ponytail/band/<project>.csv`. Turn it off if you don't want those files. Leave _Webhook URL_ empty unless you mean to send each task's row, including the task's name, to another server. On first run it may offer to add a status line to `~/.claude/settings.json`, and you can decline. The plugin brings its own copies of the skills (`ponytail:ponytail` and so on). Keeping the skills-only install as well is harmless, or remove it with `npx skills remove`. Uninstall with `/plugin remove ponytail`. That leaves some state files behind; the [Uninstall section of ponytail's INSTALL.md](https://github.com/DietrichGebert/ponytail/blob/main/INSTALL.md#uninstall) says how to clean them up, which must happen first.

## Using the packages in a repo

`.npmrc`:

```
@crithits:registry=https://npm.pkg.github.com
```

GitHub Packages requires a token even for public packages. Developers need a classic token with `read:packages` in `~/.npmrc` (`//npm.pkg.github.com/:_authToken=...`); CI uses `GITHUB_TOKEN` (with `permissions: packages: read`).

```sh
pnpm add -D @crithits/eslint-config-react @crithits/tsconfig eslint typescript@~6.0
```

`eslint.config.js`:

```js
import { reactConfig } from "@crithits/eslint-config-react";

export default reactConfig({
  tsconfigRootDir: import.meta.dirname,
  // effectRulesAsWarnings: true, // while migrating an existing repo
});
```

`tsconfig.json`:

```json
{ "extends": "@crithits/tsconfig/react-app.json", "include": ["src"] }
```

pnpm users: `eslint-plugin-jsx-a11y` hasn't widened its peer range to ESLint 10 yet but works fine (covered by tests). Silence the warning in `package.json`:

```json
"pnpm": { "peerDependencyRules": { "allowedVersions": { "eslint-plugin-jsx-a11y>eslint": "10" } } }
```

## Why TypeScript 6.0, not 7

typescript-eslint supports `typescript >=4.8.4 <6.1`. Move to TS 7 when typescript-eslint does; the peer range in `eslint-config-react` will tell you.
