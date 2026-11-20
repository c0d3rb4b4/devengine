import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from devengine.config import load_repo_config
from devengine.github_app import (
    get_installation_token,
    get_repo_installation,
    github_api_request,
    installation_token_headers,
)

load_dotenv()

FALLBACK_TARGET_REPO = "c0d3rb4b4/nato-phonetics"


def _default_repo() -> str:
    configured_repos = load_repo_config().get("repos", {})
    enabled_repos = [
        repo_full_name
        for repo_full_name, repo_config in configured_repos.items()
        if repo_config.get("enabled", False)
    ]
    if enabled_repos:
        return enabled_repos[0]
    return os.getenv("TARGET_REPO", FALLBACK_TARGET_REPO)


def main() -> None:
    target_repo = os.getenv("TARGET_REPO", _default_repo())
    installation = get_repo_installation(target_repo)
    print(f"Installation ID: {installation['id']}")

    installation_token = get_installation_token(target_repo)
    headers = installation_token_headers(installation_token)

    repo = github_api_request("GET", f"/repos/{target_repo}", headers=headers)
    print("Repo status: 200")
    print("Repo full name:", repo["full_name"])
    print("Default branch:", repo["default_branch"])
    print("Private:", repo["private"])

    issues = github_api_request(
        "GET",
        f"/repos/{target_repo}/issues",
        headers=headers,
        params={"state": "open", "per_page": 5},
    )

    print("Issues status: 200")
    print(f"Open issues returned: {len(issues)}")
    for issue in issues:
        print(f"- #{issue['number']}: {issue['title']}")


if __name__ == "__main__":
    main()
