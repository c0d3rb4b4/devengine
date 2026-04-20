import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request

app = FastAPI(title="devengine-api")


def _load_repo_config() -> dict[str, Any]:
    path = Path("/app/config/repos.json")
    if not path.exists():
        return {"repos": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_signature(signature_256: str | None, body: bytes) -> bool:
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        return False
    if not signature_256 or not signature_256.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_256)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "devengine-api",
        "repos_configured": len(_load_repo_config().get("repos", {})),
    }


@app.get("/debug/config")
def debug_config() -> dict[str, Any]:
    config = _load_repo_config()
    return {
        "repo_count": len(config.get("repos", {})),
        "repos": list(config.get("repos", {}).keys()),
    }


@app.post("/github/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
):
    body = await request.body()

    if not _verify_signature(x_hub_signature_256, body):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(body.decode("utf-8"))
    repo = payload.get("repository", {}).get("full_name")
    action = payload.get("action")

    return {
        "ok": True,
        "event": x_github_event,
        "action": action,
        "repo": repo,
        "note": "Webhook received. Task dispatch not implemented yet.",
    }
