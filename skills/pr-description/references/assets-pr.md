# Screenshots and the assets PR

GitHub has no API for the drag-and-drop attachments (`user-attachments`) that people paste into PR bodies, so you can't upload a screenshot that way. Instead, each repo keeps one long-lived draft PR, the **assets PR**, whose branch holds images. You commit screenshots to that branch through the GitHub API and link them from the description by commit SHA.

## Capture

- Take the Before shot on the base branch and the After shot on this branch, with the same route, data, viewport and state, so the only difference is the change. A `git worktree` of the base keeps your working tree untouched.
- Use whatever browser tooling you have (Playwright, a browser MCP). Crop to the area that changed; a full page is fine when the change is the layout.
- Save PNGs. For an interaction, a short GIF under about 10 MB; GitHub doesn't play repo-hosted videos inline.
- Never capture secrets, tokens, real customer data or anything else you wouldn't put in the repo. In a public repo, the images are public.
- If you can't capture a shot (no way to run the app, missing data or account), fall back to the placeholder comment and ask the user, as the writing rules say.

## Find or create the assets PR

The assets PR has head branch `pr-assets`, targets the default branch, and stays open as a draft forever. Look it up on every run:

```sh
GH_PAGER=cat gh pr list --head pr-assets --state open --json number,url
```

If there's none, ask the user once before creating it ("This repo has no assets PR yet. Create a draft PR on branch `pr-assets` to host screenshots?"). On a yes:

```sh
base_sha=$(gh api repos/{owner}/{repo}/git/ref/heads/<default-branch> --jq .object.sha)
gh api repos/{owner}/{repo}/git/refs -f ref=refs/heads/pr-assets -f sha="$base_sha"
```

Then commit a `pr-assets/README.md` with the upload command below (GitHub won't open a PR with no commits), and open it:

```sh
gh pr create --draft --base <default-branch> --head pr-assets \
  --title "PR assets (do not merge)" --body-file <file>
```

The body says, in two or three sentences, that the branch hosts screenshots linked from other PR descriptions, and that merging, closing it or deleting the branch breaks those images.

If you can't push to the repo (you're working from a fork) or the user declines, skip this and use placeholders.

## Upload

Commit each image straight to `pr-assets` with the contents API, so your local checkout and branch never change. Use a new path every time; the API refuses to overwrite an existing path without its SHA, which protects images other PRs link to.

Path: `pr-assets/<head-branch>/<YYYYMMDD-HHMMSS>-<before|after>-<slug>.png`, with `/` in the branch name replaced by `-`.

```sh
dir=$(mktemp -d)
base64 < <image> | tr -d '\n' > "$dir/content.b64"
jq -n --arg message "Add <before|after> screenshot for <head-branch>" \
  --arg branch pr-assets --rawfile content "$dir/content.b64" \
  '{message: $message, branch: $branch, content: $content}' > "$dir/body.json"
gh api -X PUT "repos/{owner}/{repo}/contents/<path>" --input "$dir/body.json" --jq .commit.sha
```

The command prints the commit SHA to link to. Never force-push, rebase, merge or close the assets PR, and never delete files from it.

## Link

Link to the file at the commit SHA, not the branch name, so the image stays fixed:

```markdown
| Before                                                                                   | After                                                                                   |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| ![Before: <what it shows>](https://github.com/<owner>/<repo>/blob/<sha>/<path>?raw=true) | ![After: <what it shows>](https://github.com/<owner>/<repo>/blob/<sha>/<path>?raw=true) |
```

Use the `github.com/.../blob/<sha>/<path>?raw=true` form: it renders in private repos for anyone with access. `raw.githubusercontent.com` links don't render in private repos.

After `gh pr create` or `gh pr edit`, read the body back and check that each linked file exists at its SHA (`gh api "repos/{owner}/{repo}/contents/<path>?ref=<sha>" --jq .size`). Report the uploaded paths in chat.
