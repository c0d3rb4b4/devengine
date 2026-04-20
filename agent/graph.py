from langgraph.graph import END, StateGraph

from agent.state import AgentState


def seed_node(state: AgentState) -> AgentState:
    repo = state.get("repo", "unknown")
    issue_number = state.get("issue_number", 0)
    return {
        **state,
        "status": "design",
        "summary": f"Ready to process repo={repo} issue=#{issue_number}",
    }



def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("seed", seed_node)
    graph.set_entry_point("seed")
    graph.add_edge("seed", END)
    return graph.compile()
