import os
import time
import jwt
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

app_id = os.environ["GITHUB_APP_ID"]
private_key_path = os.environ.get(
    "GITHUB_PRIVATE_KEY_PATH",
    "/app/secrets/github-app.pem",
)

# When running on host, translate container path to local path.
if private_key_path.startswith("/app/"):
    private_key_path = private_key_path.replace("/app/", "./", 1)

private_key = Path(private_key_path).read_text()

now = int(time.time())

payload = {
    "iat": now - 60,
    "exp": now + (9 * 60),
    "iss": app_id,
}

encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")

headers = {
    "Authorization": f"Bearer {encoded_jwt}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

response = requests.get(
    "https://api.github.com/app/installations",
    headers=headers,
    timeout=30,
)

print("Status:", response.status_code)
print(response.text)
response.raise_for_status()
