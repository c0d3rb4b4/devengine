from typing import Literal, TypedDict


class AgentState(TypedDict, total=False):
    repo: str
    issue_number: int
    phase: int
    status: Literal["new", "design", "planning", "implementing", "done"]
    summary: str
