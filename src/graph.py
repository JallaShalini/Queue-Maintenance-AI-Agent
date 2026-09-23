import sqlite3
import json
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langsmith import traceable

from src.state import AgentState
from src.trust_engine import check_trust, increment_trust
from src.operations import execute_mutation
import config.settings as settings

def perceive_node(state: AgentState) -> Dict[str, Any]:
    """Reads the current queue state."""
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM content_queue")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"queue_snapshot": rows}

from src.agent import plan_node

@traceable
def check_trust_node(state: AgentState) -> Dict[str, Any]:
    """Checks if proposed actions require human approval based on trust metrics."""
    proposed_actions = state.get("proposed_actions", [])
    requires_approval = False
    
    for action in proposed_actions:
        action_type = action.get("type", "")
        if not check_trust(action_type):
            requires_approval = True
            break
            
    return {"requires_approval": requires_approval}

@traceable
def human_review_node(state: AgentState) -> Dict[str, Any]:
    """Interrupts execution to ask for human approval."""
    actions = state.get("proposed_actions", [])
    
    # Pause graph execution and wait for input
    human_decision = interrupt({
        "message": f"The agent proposes the following actions: {actions}. Do you approve?",
        "options": ["Y", "N"]
    })
    
    if human_decision == "Y":
        return {"human_feedback": "approved"}
    else:
        return {"human_feedback": "rejected"}

@traceable
def execute_node(state: AgentState) -> Dict[str, Any]:
    """Executes the proposed actions and increments trust on success."""
    proposed_actions = state.get("proposed_actions", [])
    results = []
    
    for action in proposed_actions:
        action_type = action.get("type")
        row_ids = action.get("row_ids", [])
        if "row_id" in action:
            row_ids = [action["row_id"]]
            
        action_results = []
        for target_id in row_ids:
            if action_type == "mark_posted":
                action_results.append(execute_mutation(action_type, target_id, {"status": "posted"}, settings.DATABASE_PATH))
            elif action_type == "retry_row":
                action_results.append(execute_mutation(action_type, target_id, {"status": "pending"}, settings.DATABASE_PATH))
            elif action_type == "purge_stale":
                action_results.append(execute_mutation(action_type, target_id, {}, settings.DATABASE_PATH))
        
        # Check if all row mutations for this action were successful
        if len(action_results) > 0 and all(res.get("success", False) for res in action_results):
            increment_trust(action_type)
            results.append({"type": action_type, "status": "success", "action_ids": [r.get("action_id") for r in action_results]})
        else:
            results.append({"type": action_type, "status": "failed", "details": action_results})
            
    return {"final_result": json.dumps(results)}

def route_trust(state: AgentState) -> str:
    """Routes to human review or execute node based on trust."""
    if state.get("requires_approval", False):
        return "human_review"
    return "execute"

def route_human_review(state: AgentState) -> str:
    """Routes to execute or end based on human review."""
    feedback = state.get("human_feedback")
    if feedback == "approved":
        return "execute"
    return "reject"

def build_graph() -> StateGraph:
    """Builds and compiles the LangGraph state machine."""
    builder = StateGraph(AgentState)
    
    builder.add_node("perceive_node", perceive_node)
    builder.add_node("plan_node", plan_node)
    builder.add_node("check_trust_node", check_trust_node)
    builder.add_node("human_review_node", human_review_node)
    builder.add_node("execute_node", execute_node)
    
    builder.add_edge(START, "perceive_node")
    builder.add_edge("perceive_node", "plan_node")
    builder.add_edge("plan_node", "check_trust_node")
    
    builder.add_conditional_edges(
        "check_trust_node",
        route_trust,
        {
            "human_review": "human_review_node",
            "execute": "execute_node"
        }
    )
    
    builder.add_conditional_edges(
        "human_review_node",
        route_human_review,
        {
            "execute": "execute_node",
            "reject": END
        }
    )
    
    builder.add_edge("execute_node", END)
    
    return builder
