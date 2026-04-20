import json
import os
import time
from pathlib import Path

from agent.graph import build_graph


def main() -> None:
    graph = build_graph()
    sample_repo = "c0d3rb4b4/nato-phonetics"
    result = graph.invoke({"repo": sample_repo, "issue_number": 0, "phase": 0, "status": "new"})
    print(json.dumps({"worker": "started", "sample_result": result}, indent=2))

    logs_dir = Path("/app/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    heartbeat = logs_dir / "agent-heartbeat.log"

    while True:
        heartbeat.write_text(f"agent alive at {time.time()}\n", encoding="utf-8")
        time.sleep(30)


if __name__ == "__main__":
    main()
