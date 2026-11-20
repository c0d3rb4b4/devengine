import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from devengine.github_app import get_app_installations

load_dotenv()


def main() -> None:
    installations = get_app_installations()
    print("Status: 200")
    print(json.dumps(installations, indent=2))


if __name__ == "__main__":
    main()
