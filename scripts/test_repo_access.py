import os
import time
from pathlib import Path

import jwt
import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.environ["GITHUB_APP_ID"]
PRIVATE_KEY_PATH = os.environ.get("GITHUB_PRIVATE_KEY_PATH", "/app/secrets/github-app.pem")
TARGET_REPO = "c0d3rb4b4/nato-phonetics"

if PRIVATE_KEY_PATH.startswith("/app/"):
    PRIVATE_KEY_PATH = PRIVATE_KEY_PATH.replace("/app/", "./", 1)

private_key = Path(PRIVATE_KEY_PATH).read_text()

now = int(time.time())
payload = {
    "iat": now - 60,
    "exp": now + (9 * 60),
    "iss": APP_ID,
}

app_jwt = jwt.encode(payload, private_key, algorithm="RS256")

app_headers = {
    "Authorization": f"Bearer {app_jwt}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

installations_response = requests.get(
    "https://api.github.com/app/installations",
    headers=app_headers,
    timeout=30,
)
installations_response.raise_for_status()

installations = installations_response.json()

installation = None
for item in installations:
    if item["account"]["login"] == "c0d3rb4b4":
        installation = item
        break

if not installation:
    raise RuntimeError("Could not find installation for c0d3rb4b4")

installation_id = installation["id"]
print(f"Installation ID: {installation_id}")

token_response = requests.post(
    f"https://api.github.com/app/installations/{installation_id}/access_tokens",
    headers=app_headers,
    timeout=30,
)
print("Token status:", token_response.status_code)
print(token_response.text)
token_response.raise_for_status()

installation_token = token_response.json()["token"]

repo_headers = {
    "Authorization": f"Bearer {installation_token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

repo_response = requests.get(
    f"https://api.github.com/repos/{TARGET_REPO}",
    headers=repo_headers,
    timeout=30,
)

print("Repo status:", repo_response.status_code)
repo_response.raise_for_status()

repo = repo_response.json()
print("Repo full name:", repo["full_name"])
print("Default branch:", repo["default_branch"])
print("Private:", repo["private"])

issues_response = requests.get(
    f"https://api.github.com/repos/{TARGET_REPO}/issues",
    headers=repo_headers,
    params={"state": "open", "per_page": 5},
    timeout=30,
)

print("Issues status:", issues_response.status_code)
issues_response.raise_for_status()

issues = issues_response.json()
print(f"Open issues returned: {len(issues)}")
for issue in issues:
    print(f"- #{issue['number']}: {issue['title']}")
