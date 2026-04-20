import json
import os
import time
from pathlib import Path


def main() -> None:
    workspace_root = Path(os.getenv("BASE_WORKSPACE_DIR", "/app/workspace"))
    workspace_root.mkdir(parents=True, exist_ok=True)
    print(json.dumps({"runner": "started", "workspace_root": str(workspace_root)}, indent=2))

    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
