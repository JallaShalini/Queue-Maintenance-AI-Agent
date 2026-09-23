import os
from langchain_openai import ChatOpenAI
from src.state import AgentState
from src.tools import tools
from langsmith import traceable

@traceable
def plan_node(state: AgentState) -> dict:
    if os.environ.get("MOCK_LLM") == "true":
        return {"proposed_actions": state.get("proposed_actions", [])}
        
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(tools)
    
    messages = state.get("messages", [])
    queue_snapshot = state.get("queue_snapshot", [])
    
    system_msg = {
        "role": "system",
        "content": (
            "You are a queue-maintenance AI agent safely managing state mutations. "
            f"Here is the current queue state: {queue_snapshot}. "
            "Use the tools provided to respond to user requests."
        )
    }
    
    res = llm_with_tools.invoke([system_msg] + messages)
    
    proposed_actions = []
    if hasattr(res, "tool_calls") and res.tool_calls:
        for call in res.tool_calls:
            # Langchain tool calls map the class name perfectly
            action = {"type": None, "row_ids": []}
            if call["name"] == "MarkPosted":
                action["type"] = "mark_posted"
                action["row_id"] = call["args"]["row_id"]
                action["row_ids"] = [call["args"]["row_id"]]
            elif call["name"] == "RetryRow":
                action["type"] = "retry_row"
                action["row_id"] = call["args"]["row_id"]
                action["row_ids"] = [call["args"]["row_id"]]
            elif call["name"] == "PurgeStale":
                action["type"] = "purge_stale"
                action["row_ids"] = call["args"]["row_ids"]
                
            proposed_actions.append(action)
            
    # Accumulate messages properly
    return {"proposed_actions": proposed_actions, "messages": [res]}
