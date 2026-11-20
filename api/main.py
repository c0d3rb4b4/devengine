import hashlib
import hmac
import json
import logging
import os
from typing import Any

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from devengine.config import load_repo_config
from runner.trial_issue import run_trial_issue

app = FastAPI(title="devengine-api")
logger = logging.getLogger(__name__)


def _load_repo_config() -> dict[str, Any]:
    return load_repo_config()


def _verify_signature(signature_256: str | None, body: bytes) -> bool:
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if not secret:
        return False
    if not signature_256 or not signature_256.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_256)


def _issue_label_names(issue: dict[str, Any]) -> set[str]:
    labels = issue.get("labels") or []
    names: set[str] = set()
    for label in labels:
        if isinstance(label, dict) and label.get("name"):
            names.add(str(label["name"]))
        elif isinstance(label, str):
            names.add(label)
    return names


def _ignored_response(
    *,
    event: str | None,
    action: str | None,
    repo: str | None,
    reason: str,
) -> dict[str, Any]:
    logger.info(
        "Ignored GitHub webhook event=%s action=%s repo=%s reason=%s",
        event,
        action,
        repo,
        reason,
    )
    return {
        "ok": True,
        "status": "ignored",
        "event": event,
        "action": action,
        "repo": repo,
        "reason": reason,
    }


def _run_trial_issue_background(repo_full_name: str, issue_number: int) -> None:
    try:
        logger.info(
            "Background trial issue runner starting repo=%s issue=%s",
            repo_full_name,
            issue_number,
        )
        result = run_trial_issue(repo_full_name, issue_number)
        logger.info(
            "Background trial issue runner completed repo=%s issue=%s branch=%s",
            repo_full_name,
            issue_number,
            result.get("branch"),
        )
    except Exception:
        logger.exception(
            "Background trial issue runner failed repo=%s issue=%s",
            repo_full_name,
            issue_number,
        )


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
    background_tasks: BackgroundTasks,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
):
    body = await request.body()

    if not _verify_signature(x_hub_signature_256, body):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    repo = payload.get("repository", {}).get("full_name")
    action = payload.get("action")

    if x_github_event != "issues":
        return _ignored_response(
            event=x_github_event,
            action=action,
            repo=repo,
            reason="unsupported_event",
        )

    if action not in {"opened", "labeled"}:
        return _ignored_response(
            event=x_github_event,
            action=action,
            repo=repo,
            reason="unsupported_issue_action",
        )

    issue = payload.get("issue") or {}
    issue_number = issue.get("number")
    if not repo or not issue_number:
        return _ignored_response(
            event=x_github_event,
            action=action,
            repo=repo,
            reason="missing_repo_or_issue",
        )

    config = _load_repo_config()
    repo_config = config.get("repos", {}).get(repo)
    if not repo_config:
        return _ignored_response(
            event=x_github_event,
            action=action,
            repo=repo,
            reason="repo_not_configured",
        )

    if not repo_config.get("enabled", False):
        return _ignored_response(
            event=x_github_event,
            action=action,
            repo=repo,
            reason="repo_disabled",
        )

    labels = _issue_label_names(issue)
    allowed_labels = {str(label) for label in repo_config.get("allowed_labels", [])}
    matching_labels = sorted(labels.intersection(allowed_labels))
    if not matching_labels:
        return _ignored_response(
            event=x_github_event,
            action=action,
            repo=repo,
            reason="missing_allowed_label",
        )

    background_tasks.add_task(_run_trial_issue_background, repo, int(issue_number))
    logger.info(
        "Accepted GitHub issues webhook repo=%s issue=%s action=%s labels=%s",
        repo,
        issue_number,
        action,
        ",".join(matching_labels),
    )
    return JSONResponse(
        status_code=202,
        content={
            "ok": True,
            "status": "accepted",
            "event": x_github_event,
            "action": action,
            "repo": repo,
            "issue_number": int(issue_number),
            "labels": matching_labels,
        },
    )
