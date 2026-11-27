# Screenshots and the `pr-assets` branch

GitHub has no API for the drag-and-drop attachments (`user-attachments`) that people paste into PR bodies, so you can't upload a screenshot that way. Instead, each repo keeps one long-lived branch, `pr-assets`, that holds images. You commit screenshots to it through the GitHub API and link them from the description by commit SHA. Nothing opens a PR for it: the branch alone keeps the commits, and the images, alive.

## Capture

- Take the Before shot on the base branch and the After shot on this branch, with the same route, data, viewport and state, so the only difference is the change. A `git worktree` of the base keeps your working tree untouched.
- Use whatever browser tooling you have (Playwright, a browser MCP, `google-chrome --headless=new --screenshot`). Crop to the area that changed; a full page is fine when the change is the layout.
- Open each image and look at it before uploading: the change must be in frame and nothing clipped. Headless Chrome's viewport, for one, comes out shorter than `--window-size`.
- Save PNGs. For an interaction, a short GIF under about 10 MB; GitHub doesn't play repo-hosted videos inline.
- Never capture secrets, tokens, real customer data or anything else you wouldn't put in the repo. In a public repo, the images are public.
- If you can't capture a shot (no way to run the app, missing data or account), fall back to the placeholder comment and ask the user, as the writing rules say.

## Find or create the branch

Look it up on every run:

```sh
GH_PAGER=cat gh api repos/{owner}/{repo}/git/ref/heads/pr-assets --jq .object.sha
```

A 404 means it doesn't exist yet. Ask the user once before creating it ("This repo has no `pr-assets` branch yet. Create one to host PR screenshots?"). On a yes, branch it from the default branch and add a README with the upload command below, so anyone who finds the branch knows what it's for:

```sh
base_sha=$(gh api repos/{owner}/{repo}/git/ref/heads/<default-branch> --jq .object.sha)
gh api repos/{owner}/{repo}/git/refs -f ref=refs/heads/pr-assets -f sha="$base_sha"
```

The README (`pr-assets/README.md`) says, in two or three sentences, that the branch hosts screenshots linked from PR descriptions by commit SHA, and that deleting, rebasing or force-pushing it breaks those images.

Don't open a PR for the branch. If you can't push to the repo (you're working from a fork) or the user declines, skip this and use placeholders.

## Upload

Commit each image straight to `pr-assets` with the contents API, so your local checkout and branch never change. Use a new path every time; the API refuses to overwrite an existing path without its SHA, which protects images other PRs link to.

Path: `pr-assets/<head-branch>/<YYYYMMDD-HHMMSS>-<before|after>-<slug>.png`, with `/` in the branch name replaced by `-`.

```sh
b64=$(mktemp)
base64 < <image> | tr -d '\n' > "$b64"
gh api -X PUT "repos/{owner}/{repo}/contents/<path>" \
  -f message="Add <before|after> screenshot for <head-branch>" \
  -f branch=pr-assets -F content=@"$b64" --jq .commit.sha
```

The command prints the commit SHA to link to; each upload is its own commit, so each image has its own SHA. `-F content=@file` reads the base64 from the file, which keeps large images out of the command line. Never delete, force-push or rebase `pr-assets`, never merge it anywhere, and never delete files from it.

## Link

Link to the file at the commit SHA, not the branch name, so the image stays fixed:

```markdown
| Before                                                                                   | After                                                                                   |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| ![Before: <what it shows>](https://github.com/<owner>/<repo>/blob/<sha>/<path>?raw=true) | ![After: <what it shows>](https://github.com/<owner>/<repo>/blob/<sha>/<path>?raw=true) |
```

Use the `github.com/.../blob/<sha>/<path>?raw=true` form: GitHub redirects it to the raw file, and in a private repo it works for anyone signed in with access. `raw.githubusercontent.com` links don't render in private repos.

After `gh pr create` or `gh pr edit`, read the body back and check that each linked file exists at its SHA (`gh api "repos/{owner}/{repo}/contents/<path>?ref=<sha>" --jq .size`). Report the uploaded paths in chat.
