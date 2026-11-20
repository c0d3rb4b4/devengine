import os
import time
from pathlib import Path
from typing import Any

import httpx
import jwt
from dotenv import load_dotenv

from devengine.config import resolve_app_path

load_dotenv()

GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/")
GITHUB_API_VERSION = "2022-11-28"


def resolve_private_key_path(private_key_path: str | os.PathLike[str] | None = None) -> Path:
    return resolve_app_path(
        private_key_path or os.getenv("GITHUB_PRIVATE_KEY_PATH", "/app/secrets/github-app.pem")
    )


def create_app_jwt(
    app_id: str | None = None,
    private_key_path: str | os.PathLike[str] | None = None,
) -> str:
    resolved_app_id = app_id or os.environ["GITHUB_APP_ID"]
    private_key = resolve_private_key_path(private_key_path).read_text(encoding="utf-8")
    now = int(time.time())

    return jwt.encode(
        {"iat": now - 60, "exp": now + 9 * 60, "iss": resolved_app_id},
        private_key,
        algorithm="RS256",
    )


def app_headers(app_jwt: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {app_jwt}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def installation_token_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }


def github_api_request(
    method: str,
    path: str,
    *,
    headers: dict[str, str],
    params: dict[str, Any] | None = None,
    json_body: Any | None = None,
    timeout: float = 30,
) -> Any:
    url = path if path.startswith("http") else f"{GITHUB_API_URL}/{path.lstrip('/')}"
    with httpx.Client(timeout=timeout) as client:
        response = client.request(method, url, headers=headers, params=params, json=json_body)
    response.raise_for_status()
    if not response.content:
        return None
    return response.json()


def get_app_installations() -> list[dict[str, Any]]:
    token = create_app_jwt()
    return github_api_request("GET", "/app/installations", headers=app_headers(token))


def get_repo_installation(repo_full_name: str) -> dict[str, Any]:
    token = create_app_jwt()
    return github_api_request(
        "GET",
        f"/repos/{repo_full_name}/installation",
        headers=app_headers(token),
    )


def get_owner_installation(owner_login: str) -> dict[str, Any]:
    installations = get_app_installations()
    for installation in installations:
        account = installation.get("account") or {}
        if account.get("login") == owner_login:
            return installation
    raise RuntimeError(f"Could not find GitHub App installation for {owner_login}")


def get_installation_token(
    repo_full_name: str | None = None,
    *,
    owner_login: str | None = None,
) -> str:
    app_jwt = create_app_jwt()
    headers = app_headers(app_jwt)

    if repo_full_name:
        installation = github_api_request(
            "GET",
            f"/repos/{repo_full_name}/installation",
            headers=headers,
        )
    elif owner_login:
        installation = get_owner_installation(owner_login)
    else:
        installations = github_api_request("GET", "/app/installations", headers=headers)
        if len(installations) != 1:
            raise RuntimeError("Pass repo_full_name or owner_login when multiple installations exist")
        installation = installations[0]

    token_response = github_api_request(
        "POST",
        f"/app/installations/{installation['id']}/access_tokens",
        headers=headers,
    )
    return token_response["token"]
