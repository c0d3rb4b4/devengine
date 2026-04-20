#!/usr/bin/env bash
set -euo pipefail

REPO_URL="$1"
WORKDIR="$2"
ISSUE_NUMBER="$3"
BASE_BRANCH="${4:-develop}"

BRANCH="agent/issue-${ISSUE_NUMBER}-trial"

rm -rf "$WORKDIR"
git clone "$REPO_URL" "$WORKDIR"
cd "$WORKDIR"

git checkout "$BASE_BRANCH"
git pull origin "$BASE_BRANCH"
git checkout -b "$BRANCH"

DATE_UTC="$(date -u +%F)"
cat > AGENT_TRIAL.md <<EOT
# Agent Trial

Issue: #${ISSUE_NUMBER}
Date: ${DATE_UTC}

The repo agent trial completed successfully.
EOT

git add AGENT_TRIAL.md
git commit -m "agent: add AGENT_TRIAL.md for issue #${ISSUE_NUMBER}"
git push -u origin "$BRANCH"
