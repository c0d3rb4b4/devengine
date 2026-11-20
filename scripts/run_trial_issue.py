import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from devengine.config import load_repo_config
from runner.trial_issue import run_trial_issue

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
    parser = argparse.ArgumentParser(description="Run the DevEngine trial issue flow manually.")
    parser.add_argument("--repo", default=os.getenv("TARGET_REPO") or _default_repo())
    parser.add_argument("--issue", type=int, default=None)
    args = parser.parse_args()

    result = run_trial_issue(args.repo, args.issue)

    print()
    print("Done.")
    print(f"Repository: {result['repo']}")
    print(f"Issue: #{result['issue_number']}")
    print(f"Branch pushed: {result['branch']}")
    print(f"Workspace: {result['workspace']}")


if __name__ == "__main__":
    main()
