from pathlib import Path


def repo_workspace(root: str, repo_slug: str, run_id: str) -> Path:
    safe_slug = repo_slug.replace("/", "__")
    return Path(root) / safe_slug / run_id
