import os
import re
import subprocess
import time
from pathlib import Path

import jwt
import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.environ["GITHUB_APP_ID"]
PRIVATE_KEY_PATH = os.environ.get("GITHUB_PRIVATE_KEY_PATH", "/app/secrets/github-app.pem")
TARGET_REPO = "c0d3rb4b4/nato-phonetics"
BASE_BRANCH = "develop"
WORKSPACE = Path("./workspace/nato-phonetics-trial")

if PRIVATE_KEY_PATH.startswith("/app/"):
    PRIVATE_KEY_PATH = PRIVATE_KEY_PATH.replace("/app/", "./", 1)


def run(cmd, cwd=None):
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def get_installation_token():
    private_key = Path(PRIVATE_KEY_PATH).read_text()
    now = int(time.time())

    app_jwt = jwt.encode(
        {"iat": now - 60, "exp": now + 9 * 60, "iss": APP_ID},
        private_key,
        algorithm="RS256",
    )

    headers = {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    installs = requests.get(
        "https://api.github.com/app/installations",
        headers=headers,
        timeout=30,
    )
    installs.raise_for_status()

    install = next(
        x for x in installs.json()
        if x["account"]["login"] == "c0d3rb4b4"
    )

    token_res = requests.post(
        f"https://api.github.com/app/installations/{install['id']}/access_tokens",
        headers=headers,
        timeout=30,
    )
    token_res.raise_for_status()
    return token_res.json()["token"]


def get_trial_issue(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    res = requests.get(
        f"https://api.github.com/repos/{TARGET_REPO}/issues",
        headers=headers,
        params={
            "state": "open",
            "labels": "agent:trial",
            "per_page": 10,
        },
        timeout=30,
    )
    res.raise_for_status()

    issues = [
        i for i in res.json()
        if "pull_request" not in i
    ]

    if not issues:
        raise RuntimeError("No open issue found with label agent:trial")

    issue = issues[0]
    print(f"Using issue #{issue['number']}: {issue['title']}")
    return issue


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:40]


def main():
    token = get_installation_token()
    issue = get_trial_issue(token)

    issue_number = issue["number"]
    issue_slug = slugify(issue["title"])
    branch = f"agent/issue-{issue_number}-{issue_slug}"

    clone_url = f"https://x-access-token:{token}@github.com/{TARGET_REPO}.git"

    if WORKSPACE.exists():
        run(["rm", "-rf", str(WORKSPACE)])

    WORKSPACE.parent.mkdir(parents=True, exist_ok=True)

    run(["git", "clone", clone_url, str(WORKSPACE)])
    run(["git", "checkout", BASE_BRANCH], cwd=WORKSPACE)
    run(["git", "pull", "origin", BASE_BRANCH], cwd=WORKSPACE)
    run(["git", "checkout", "-b", branch], cwd=WORKSPACE)

    marker = WORKSPACE / "AGENT_TRIAL.md"
    marker.write_text(
        f"""# DevEngine Trial

Issue: #{issue_number}
Title: {issue["title"]}

DevEngine successfully read a GitHub issue, created a branch, committed a file, and pushed the branch.

This is still a safe trial step. No autonomous implementation logic has run yet.
""",
        encoding="utf-8",
    )

    run(["git", "config", "user.name", "DevEngine"])
    run(["git", "config", "user.email", "devengine-local[bot]@users.noreply.github.com"])
    run(["git", "add", "AGENT_TRIAL.md"], cwd=WORKSPACE)
    run(["git", "commit", "-m", f"agent: trial marker for issue #{issue_number}"], cwd=WORKSPACE)
    run(["git", "push", "-u", "origin", branch], cwd=WORKSPACE)

    print()
    print("Done.")
    print(f"Branch pushed: {branch}")


if __name__ == "__main__":
    main()
