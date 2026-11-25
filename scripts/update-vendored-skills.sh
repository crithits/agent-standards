#!/usr/bin/env bash
# Refresh the third-party skills vendored under agents/skills/.
# Run from the repo root, review the diff, and open a PR — merging it syncs
# the update to every repo in .github/sync.yml.
set -euo pipefail

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

git clone --quiet --depth 1 https://github.com/vercel-labs/agent-skills.git "$tmp/vercel"
sha="$(git -C "$tmp/vercel" rev-parse HEAD)"

for pair in "react-best-practices:vercel-react-best-practices" "composition-patterns:vercel-composition-patterns"; do
  src="${pair%%:*}"
  dest="agents/skills/${pair##*:}"
  rm -rf "$dest"
  cp -r "$tmp/vercel/skills/$src" "$dest"
done

cat > agents/skills/VENDORED.md <<EOF
# Vendored skills

| Skill | Source | Commit | License |
|---|---|---|---|
| vercel-react-best-practices | https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices | ${sha} | MIT |
| vercel-composition-patterns | https://github.com/vercel-labs/agent-skills/tree/main/skills/composition-patterns | ${sha} | MIT |

Refresh with \`scripts/update-vendored-skills.sh\`.
EOF

echo "Updated vendored skills to vercel-labs/agent-skills@${sha:0:7}"
