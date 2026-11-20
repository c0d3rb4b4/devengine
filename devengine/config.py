import json
import os
from pathlib import Path
from typing import Any


def resolve_app_path(raw_path: str | os.PathLike[str]) -> Path:
    path = Path(raw_path)
    if path.exists():
        return path

    raw = str(raw_path)
    if raw.startswith("/app/"):
        host_path = Path.cwd() / raw.removeprefix("/app/")
        if host_path.exists():
            return host_path

    return path


def load_repo_config(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    config_path = resolve_app_path(path or os.getenv("DEVENGINE_REPOS_CONFIG", "/app/config/repos.json"))
    if not config_path.exists():
        return {"repos": {}}
    return json.loads(config_path.read_text(encoding="utf-8"))


def get_repo_settings(
    repo_full_name: str,
    path: str | os.PathLike[str] | None = None,
) -> dict[str, Any] | None:
    return load_repo_config(path).get("repos", {}).get(repo_full_name)
