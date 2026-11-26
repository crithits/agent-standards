# PR conventions

## Title

- **Follow the repo first.** Look at the recent merged titles. If most use a pattern (a `[Area]` prefix, Conventional Commits such as `fix(cart):`, a ticket key), use the same one. `AGENTS.local.md` overrides both.
- **Default, with no pattern:** a short human sentence that could stand as a changelog line.
- **Sentence:** start with an action verb such as Add, Fix, Improve, Show or Prevent, and say where the change is. Present tense, sentence case, no trailing period, under 72 characters.
- **Fixes:** describe the symptom the user saw, not the code fix: `Fix cart total ignoring discount codes`, not `Await applyDiscount in useCartTotal`.
- **Features:** describe what users can now do: `Add CSV export to the orders table`.
- **Leave out:** issue numbers and file or function names, unless the repo's pattern includes them.
- **When rewriting:** propose a new title only if the current one breaks these rules, and show the old one next to it.

## Body order

1. `## Summary`
2. `Fixes <issue URL>` (full URL; `Part of` for partial work; leave the line out with no issue)
3. Problem, then solution, then Before and After
4. `## How to test` (reproduction link or steps, then verification steps)
5. `## Impact` and `## Action`: add them for breaking changes (see "Breaking changes"), and keep any the existing body already has
6. Optional `## Release note`
7. `## Review notes`, content collapsed
8. `## Checklist`, content collapsed (only when the repo has a PR template)
9. `## Identify risks`, content collapsed

Skeleton:

```markdown
## Summary

Fixes https://github.com/<owner>/<repo>/issues/N

<problem as the user sees it, 1-3 sentences>

<solution at a high level, 1-3 sentences>

| Before | After |
| --- | --- |
| <!-- screenshot or video --> | <!-- screenshot or video --> |

## How to test

**Reproduce on `main`** (or: Reproduction steps: <link to the issue or comment>)

1. ...

**Verify on this branch**

1. ...

## Review notes

<details>
<summary>Where to start, intended behavior, extra changes, open items</summary>

#### Start here

...

#### Intended behavior

- ...

#### Also in this PR

- ...

#### Open

- ...

</details>

## Checklist

<details>
<summary>N of M checked. The others don't apply: ...</summary>

<template checklist items, verbatim, ticked where verified>

</details>

## Identify risks

<details>
<summary>Low|Medium|High: <main risk></summary>

<risk, severity, mitigation>

</details>
```

Every collapsed section keeps its visible `##` heading, and its `<summary>` is one line of plain text that is useful without expanding. An `<h2>` inside `<summary>` gets GitHub's fixed heading margins, which leave large gaps between stacked blocks.

## Checklist source

Read the repo's PR template on every run, so the description tracks the current one. Look in this order and use the first found: `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `pull_request_template.md`, `docs/pull_request_template.md`, then a single file in `.github/PULL_REQUEST_TEMPLATE/` (with several, ask which applies). Match file names case-insensitively.

Copy every checklist item verbatim (including links), as a `- [ ]` / `- [x]` list. If the template has its own risk section, replace its checkboxes with the prose in `## Identify risks`. Leave out the template's HTML comments and instructional sentences. Any other section the template requires goes in the body order where it fits best; don't drop it.

## Breaking changes

For breaking API, schema, config or contract changes, and for deprecations, add visible `## Impact` (who and what breaks) and `## Action` (what consumers must do) sections after `## How to test`, and say so in the title or the risk summary.

## Labels

Suggest labels in chat, never inside the body, and only labels that exist in the repo (`gh label list --limit 200`). Prefer labels recent merged PRs use for similar changes. Don't create labels.

In Create mode, apply them with `--label`. In Update mode, apply them with `gh pr edit --add-label` only after approval, and remove the ones that no longer apply in the same command with `--remove-label`.
