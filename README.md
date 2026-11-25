# agent-standards

Shared standards for React + TypeScript repos, built so coding agents (Claude Code, Codex, Cursor, Copilot) write code the way we want, and lint catches it when they don't.

| Path | What | How it reaches repos |
|---|---|---|
| `packages/eslint-config-react` | `@crithits/eslint-config-react`: ESLint flat config with React Compiler rules, strict type-checked typescript-eslint, jsx-a11y | npm package (GitHub Packages) |
| `packages/tsconfig` | `@crithits/tsconfig`: strict base + React app tsconfig | npm package (GitHub Packages) |
| `agents/AGENTS.md`, `agents/CLAUDE.md` | Rules every agent reads | Synced by PR (overwritten) |
| `agents/AGENTS.local.md` | Stub for repo-specific notes; its presence opts a repo into syncing | Never synced: copy it into an existing repo to opt in |
| `agents/skills/` | Vendored Vercel skills (react-best-practices, composition-patterns) | Synced by PR to `.agents/skills/` and `.claude/skills/` |

Lint is the enforcement layer; AGENTS.md is the "do this instead" layer; skills are the on-demand deep reference.

## One-time setup

1. **Push** this repo to `github.com/crithits/agent-standards`.
2. **Packages:** `ci-publish.yml` publishes to GitHub Packages with the built-in `GITHUB_TOKEN` on every push to `main` (only versions not yet published). Both packages are **public**, so CI in any repo can install them with its own `GITHUB_TOKEN` and no per-repo access grant. A package added later starts private; make it public in its *Package settings → Danger Zone → Change visibility*.
3. **Sync bot:** create a GitHub App in the org (Settings → Developer settings → GitHub Apps) with repository permissions *Contents: read & write*, *Pull requests: read & write*, *Metadata: read*. Install it on the target repos. Then in this repo:
   - Variable `AGENT_SYNC_APP_ID` = the App ID
   - Secret `AGENT_SYNC_APP_PRIVATE_KEY` = the App's private key (.pem contents)
4. **Template repo** (`crithits/react-ts-template`): its lockfile is already committed. Mark it as a template in its repo Settings → *Template repository*.

## Day to day

**Change a lint rule:** edit `packages/eslint-config-react/index.js`, add or adjust a fixture and assertion in `test/`, bump `version` (semver: new error-level rules are a major bump), merge. Repos pick it up through Renovate/Dependabot.

**Change agent rules:** edit `agents/AGENTS.md`, merge. Every opted-in repo gets a PR.

**Which repos get synced:** there's no list. `scripts/discover-sync-targets.py` asks the sync App which repos it's installed on and keeps the ones with `AGENTS.local.md` at the root (archived repos and this repo are skipped). Repo names are masked in the Actions logs, so this repo can be public without revealing private or client repos. The workflow also runs weekly to catch repos created since the last change.

**Add a repo:** repos created from `react-ts-template` are opted in automatically. For an existing repo, copy `agents/AGENTS.local.md` to its root and fill it in, install the packages (below), and start with `effectRulesAsWarnings: true` if the effect rule floods it. Then run *Sync agent files* manually or wait for the next run.

**Remove a repo:** delete its `AGENTS.local.md`.

**Update vendored skills:** `./scripts/update-vendored-skills.sh`, review the diff, merge.

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
import { reactConfig } from '@crithits/eslint-config-react';

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
