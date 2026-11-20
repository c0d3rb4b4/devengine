import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from devengine.config import get_repo_settings, resolve_app_path
from devengine.github_app import (
    get_installation_token,
    github_api_request,
    installation_token_headers,
)

logger = logging.getLogger(__name__)

DEFAULT_TRIAL_LABEL = "agent:trial"


def _redact_arg(value: str) -> str:
    return re.sub(r"x-access-token:[^@]+@", "x-access-token:***@", value)


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    logger.info("Running command: %s", " ".join(_redact_arg(part) for part in cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:40] or "trial"


def _label_names(issue: dict[str, Any]) -> set[str]:
    labels = issue.get("labels") or []
    names: set[str] = set()
    for label in labels:
        if isinstance(label, dict) and label.get("name"):
            names.add(str(label["name"]))
        elif isinstance(label, str):
            names.add(label)
    return names


def _workspace_root() -> Path:
    return resolve_app_path(os.getenv("BASE_WORKSPACE_DIR", "/app/workspace"))


def _allowed_labels(repo_config: dict[str, Any] | None) -> list[str]:
    if not repo_config:
        return [DEFAULT_TRIAL_LABEL]
    labels = repo_config.get("allowed_labels") or [DEFAULT_TRIAL_LABEL]
    return [str(label) for label in labels]


def _fetch_issue(token: str, repo_full_name: str, issue_number: int) -> dict[str, Any]:
    return github_api_request(
        "GET",
        f"/repos/{repo_full_name}/issues/{issue_number}",
        headers=installation_token_headers(token),
    )


def _find_trial_issue(token: str, repo_full_name: str, label: str) -> dict[str, Any]:
    issues = github_api_request(
        "GET",
        f"/repos/{repo_full_name}/issues",
        headers=installation_token_headers(token),
        params={"state": "open", "labels": label, "per_page": 10},
    )
    real_issues = [issue for issue in issues if "pull_request" not in issue]
    if not real_issues:
        raise RuntimeError(f"No open issue found with label {label}")
    return real_issues[0]


def run_trial_issue(repo_full_name: str, issue_number: int | None = None) -> dict[str, Any]:
    repo_config = get_repo_settings(repo_full_name)
    allowed_labels = _allowed_labels(repo_config)
    trial_label = allowed_labels[0]
    base_branch = (
        (repo_config or {}).get("base_branch")
        or os.getenv("DEFAULT_BASE_BRANCH")
        or "develop"
    )
    repo_name = repo_full_name.split("/", 1)[-1]
    workspace_subdir = (repo_config or {}).get("workspace_subdir") or repo_name

    logger.info(
        "Starting trial issue runner for repo=%s issue=%s base_branch=%s",
        repo_full_name,
        issue_number or "first-open",
        base_branch,
    )

    token = get_installation_token(repo_full_name)
    issue = (
        _fetch_issue(token, repo_full_name, issue_number)
        if issue_number is not None
        else _find_trial_issue(token, repo_full_name, trial_label)
    )

    labels = _label_names(issue)
    matching_labels = sorted(labels.intersection(allowed_labels))
    if not matching_labels:
        raise RuntimeError(
            f"Issue #{issue['number']} does not include an allowed trial label: {allowed_labels}"
        )

    issue_number = int(issue["number"])
    issue_slug = _slugify(issue["title"])
    branch = f"agent/issue-{issue_number}-{issue_slug}"
    workspace = _workspace_root() / f"{workspace_subdir}-trial-issue-{issue_number}"
    clone_url = f"https://x-access-token:{token}@github.com/{repo_full_name}.git"

    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.parent.mkdir(parents=True, exist_ok=True)

    _run(["git", "clone", clone_url, str(workspace)])
    _run(["git", "checkout", base_branch], cwd=workspace)
    _run(["git", "pull", "origin", base_branch], cwd=workspace)
    _run(["git", "checkout", "-b", branch], cwd=workspace)

    marker = workspace / "AGENT_TRIAL.md"
    marker.write_text(
        f"""# DevEngine Trial

Repository: {repo_full_name}
Issue: #{issue_number}
Title: {issue["title"]}
Accepted label: {matching_labels[0]}

DevEngine successfully read a GitHub issue, created a branch, committed a file, and pushed the branch.

This is still a safe trial step. No autonomous implementation logic has run yet.
""",
        encoding="utf-8",
    )

    _run(["git", "config", "user.name", "DevEngine"], cwd=workspace)
    _run(
        ["git", "config", "user.email", "devengine-local[bot]@users.noreply.github.com"],
        cwd=workspace,
    )
    _run(["git", "add", "AGENT_TRIAL.md"], cwd=workspace)
    _run(["git", "commit", "-m", f"agent: trial marker for issue #{issue_number}"], cwd=workspace)
    _run(["git", "push", "-u", "origin", branch], cwd=workspace)

    logger.info(
        "Trial issue runner completed for repo=%s issue=%s branch=%s",
        repo_full_name,
        issue_number,
        branch,
    )
    return {
        "repo": repo_full_name,
        "issue_number": issue_number,
        "branch": branch,
        "workspace": str(workspace),
    }
