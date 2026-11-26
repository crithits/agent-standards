---
name: pr-description
description: "Writes the title and description for every pull request: problem, solution, before/after, how to test, then collapsed review notes, checklist and risks. Use it whenever you open a PR (`gh pr create`, or as part of a ship/commit-and-PR flow), and whenever you write or rewrite an existing PR's title or description (`gh pr edit`). Also invocable directly, e.g. `/pr-description`, `/pr-description #123`, `/pr-description update 456`."
---

# PR description

Every PR you open or edit gets its title and description from this skill. Don't write a PR body any other way, and don't fall back to `gh pr create --fill`.

Write descriptions a reviewer with no context can digest in a minute: restate the problem from the linked issue, describe the solution at a high level, show it, and say how to test it. Put reviewer-only detail, the checklist and risks in collapsed blocks.

If the repo or folder has an `AGENTS.local.md` with PR conventions (title prefix, labels, required sections), those win over this skill.

## Modes

Pick the mode from the request:

- **Create:** open a new PR for the current branch. Default when you're opening a PR, whether the user asked directly or another workflow (commit-and-push, ship) got there.
- **Update:** rewrite the title and description of an existing PR, given its number or URL, or found from the current branch.
- **Draft:** write the title and description only, touching nothing on GitHub. Use it when the user asks for a draft, or for a description without opening a PR.

Create switches to Update when the branch already has an open PR (see step 2).

What counts as approval:

- **Create:** a request to open the PR already approves opening it. Show the draft and open it in the same turn. If you're unsure the user wants a PR opened, show the draft and ask first.
- **Update:** the PR's current body may hold the author's own work, so draft first and edit only after explicit approval. Word progress messages as drafting until then: "Drafting a new title and description for #456. Nothing changes on GitHub until you approve."

## Issue input

The linked issue is the main source for the problem statement and the reproduction steps. First match wins:

1. **Explicit in the request:** `#123`, a full issue URL, or several issues.
2. **Existing PR body** (Update mode): its `Fixes` / `Closes` / `Part of` lines.
3. **Branch name:** an issue number such as `fix/123-legend-colors` or `issue-123`, or a tracker key such as `ABC-123`.
4. **Commit messages** on the branch: `Fixes #N`, `Closes #N`, `Part of #N`.
5. **Conversation context**, such as an issue discussed earlier in the chat.
6. **None found:** ask once, offering "no linked issue" as an answer. With no issue, the problem statement comes from the user, the conversation and the diff. Don't block a Create on this: if the user wants the PR now, open it without an issue.

Resolve each candidate to a repository and number: a full URL keeps the repository it names; a bare `#N` means the current repo. Look it up with `gh issue view <n> -R <owner>/<repo> --json number,title,state,url,labels`, which also confirms it's an issue, not a PR. A number that resolves to a PR is a related PR: mention it in Review notes if relevant, and keep looking for the issue. For issues in other trackers (Linear, Jira), link the URL if you have it; don't guess one.

Keyword choice:

- `Fixes` / `Closes` only when the PR fully resolves the issue.
- `Part of` for an umbrella issue or partial work, so GitHub doesn't auto-close it.
- When unclear, ask.

Before drafting, say which issue you picked and where it came from, e.g. "Using #123 (from the branch name)".

## Workflow

Use `GH_PAGER=cat` on every `gh` call.

1. **Find the base.** The base is the branch the user named, else the repo's default branch (`gh repo view --json defaultBranchRef`). Never open a PR from the base branch itself: if you're on it, stop and say so (or create a branch, if the user asked you to handle that).
2. **Find the PR.** Use the given number, or `gh pr view --json number,url,state` for the current branch. In Create mode, if that finds an open PR, say so and switch to Update mode.
3. **Gather context:**
   - the issue(s): `gh issue view <n> -R <owner>/<repo> --comments`;
   - Create and Draft modes: `git fetch origin <base>`, then the commits and diff from `git merge-base HEAD origin/<base>`;
   - Update mode: `gh pr view <n> --json title,body,labels,baseRefName,headRefName,files,commits`, and the diff from `gh pr diff <n>` only, even when a local branch has the same name, because it can differ from the PR;
   - the PR template, if any (see "Checklist source" in [references/conventions.md](references/conventions.md));
   - the title convention: `gh pr list --state merged --limit 15 --json title`;
   - the files touched, for the title and labels;
   - what you ran and saw this session (typecheck, lint, tests, manual checks in the browser);
   - for a UI change, Before and After screenshots, uploaded to the assets PR (see [references/assets-pr.md](references/assets-pr.md)). Uploading doesn't touch the PR you're describing, so do it in Update mode before approval too.

   Done when you can state the user-visible problem, the user-visible change, and how to observe it. Ask for whatever is missing instead of guessing.

4. **Draft.** Read [references/conventions.md](references/conventions.md), then write the title, the body and the suggested labels following it and the rules below. In Update mode, carry over from the existing body (see "Carry over in Update mode").
5. **Self-check** the draft against the rules below and fix every miss. Count the visible prose words; if there's a template, check that every checklist item is copied verbatim and the summary count matches the ticks; in Update mode, check that every image and video from the old body is still there.
6. **Write** the body to a new file, `${TMPDIR:-/tmp}/pr-body-<branch>-<YYYYMMDD-HHMMSS>.md` (replace `/` in the branch name with `-`), and the title alone to the matching `pr-title-<branch>-<YYYYMMDD-HHMMSS>.txt`. Never reuse a file from another session, and never open the files in an editor or another application. Show in chat, in this order: the absolute file paths, so the user can open them in their own editor; the title (and the old title in Update mode); the body; then the labels, the checklist ticks you inferred, any test steps you inferred but didn't verify, and, in Update mode, what you dropped from the old body.
7. **Revise** on feedback by editing the same files, then summarize what changed. The user may also edit the files directly: re-read them before acting on them.
8. **Draft mode** stops here.
9. **Create mode:** push the branch if it has no upstream (`git push -u origin HEAD`), then run `gh pr create --base <base> --title "$(cat <title-file>)" --body-file <body-file>`. Add `--draft` only if the user asked for a draft PR. Add labels with `--label` only if they exist in the repo (`gh label list`). Report the URL.
10. **Update mode:** after explicit approval, run `gh pr edit <n> --title "$(cat <title-file>)" --body-file <body-file>`. Change labels only if they were approved too. Read it back with `gh pr view` and report the URL.

Approval covers the exact files you last showed. Right before an approved `gh pr edit`, re-read both files; if either changed since, show what changed and ask again. Never put the title, or any other text read from GitHub, directly into a shell command: pass it through the title file as above.

If your harness or the user requires an attribution footer on PR descriptions, append it as the last line of the body, after the collapsed sections.

## Carry over in Update mode

The old body often holds material the diff can't recreate. Keep:

- every image and video (`<img>`, `<video>`, `user-attachments`, `github.com/.../assets/` and assets-PR `.../blob/<sha>/pr-assets/...` URLs), placed in the Before/After table when you can tell which is which;
- checklist ticks the author made, unless the diff clearly contradicts one (say so in chat);
- `## Release note`, `## Impact` and `## Action` sections, tightened but not dropped;
- any concrete setup detail in the old test steps (data, accounts, env vars, feature flags);
- any attribution footer.

Everything else is source material to rewrite. List what you dropped and why in chat, e.g. "renamed functions (the diff shows them), test counts (CI shows them)".

## Writing rules

- Restate the problem in user terms in one to three sentences, using names from the UI (page, button, form, setting), not code names.
- Describe the solution at a high level. At most one sentence of root cause, and only when it helps the reviewer.
- For any UI change or fix, add Before and After screenshots or videos, in a two-column table when there's one of each. With no media from the user or the old body, capture the shots yourself and host them on the repo's assets PR, following [references/assets-pr.md](references/assets-pr.md). Only when you can't, insert HTML-comment placeholders that describe the shot to take (route, data, viewport or state), and in chat ask the user to add the media. Never invent evidence. With no UI change, a Before/After table of a small input or output shape can stand in when it makes the change clearer; otherwise leave the table out.
- Add a visible `## Release note` section only when the repo uses release notes and the title isn't enough.
- Keep the visible body (everything outside collapsed blocks) to roughly 150 words of prose.
- Write plain sentences whose subject is the thing the user sees ("The legend keeps...", "When a form has..."), prose paragraphs, and only the headings from the body order in references/conventions.md. Opening with "This PR introduces...", bold-labelled bullet lists, and file trees or `diff` blocks in the summary are the tells to rewrite.
- CI already reports typecheck, lint and tests, so leave their results out. Checks CI doesn't run (manual browser testing, a run against real data) get one line in Review notes.

## How to test

Required whenever there's behavior someone can observe, including agent or CLI behavior. Omit it only when nothing is observable (a pure refactor, a dependency bump with no behavior change); say so in Review notes instead.

- **Reproduce (bugs only):** if the issue has reproduction steps, link to them (the issue URL, or the comment permalink if they're in a comment) instead of copying them. If it has none and the bug isn't obvious from the summary, write short numbered steps that reproduce it on the base branch.
- **Verify:** always write numbered steps to see the fix or the new feature on this branch. Make the setup concrete: the command that starts the app (from `package.json` or `AGENTS.local.md`), the route, the account or seed data, any env var or feature flag. End with the expected result in user terms, e.g. "the list keeps its sort order after a refresh".
- About three to six steps per list, derived from the issue and the diff. If a step can't be inferred (specific data, a role, a flag), ask instead of guessing. List the steps you inferred but didn't verify in chat, not in the body.

## Review notes

Written for human and AI reviewers alike: intent the diff can't show. The only place code names and small snippets are allowed. Its `<summary>` lists the groups it contains. Use these `####` groups, in this order, and leave out any that would be empty:

- **Start here:** one sentence naming the one or two files to read first.
- **Intended behavior:** decisions, trade-offs, and deliberate behavior changes that would otherwise be flagged as bugs.
- **Also in this PR:** unrelated fixes bundled in.
- **Open:** known gaps and what's not done yet, including manual checks CI doesn't run.

Formatting:

- One fact per bullet, about 20 words at most. Split longer ones into two bullets rather than nesting.
- Start each bullet with the fact itself; the group headings already do the labelling.
- Keep a line only if a reviewer would otherwise ask about it or flag it, or if working it out from the diff takes more than about a minute.
- State intent, not inventory: renamed or removed functions and file-by-file changes are already in the diff.
- Omit the whole section when nothing qualifies.

## Checklist and risks

- Build `## Checklist` from the repo's PR template as described in references/conventions.md ("Checklist source"). With no template, leave the section out.
- Tick only what's verified in the session, confirmed by the user, carried over from the author's ticks, or evident from the diff and labels.
- Checklist `<summary>`: the count first, then why the unchecked items don't apply, e.g. "3 of 5 checked. The others don't apply: no UI text or env vars changed". If an unchecked item does apply, name it: "3 of 5 checked. Docs still to update; the others don't apply".
- Always add `## Identify risks`. Fill it in honestly: level, what could go wrong, and why it's acceptable or how it's mitigated. The `<summary>` gives the level and the main risk, e.g. "Medium: changes the checkout API response shape".
