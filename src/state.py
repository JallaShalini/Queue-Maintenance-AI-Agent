from typing import TypedDict, List, Dict, Any, Optional
from typing import Annotated
import operator

class AgentState(TypedDict):
    """
    Represents the state of the LangGraph agent.
    
    Fields:
        messages: A list of message dictionaries.
        queue_snapshot: The state of the queue perceived by the agent.
        proposed_actions: A list of dicts representing actions proposed by the planner.
        requires_approval: Boolean flag indicating if the proposed actions need human review.
        human_feedback: String containing the human's response ("approved", "rejected", etc.).
        final_result: Result of the execution or rejection.
        error: Information about any recoverable errors.
    """
    messages: Annotated[List[Dict[str, Any]], operator.add]
    queue_snapshot: List[Dict[str, Any]]
    proposed_actions: List[Dict[str, Any]]
    requires_approval: bool
    human_feedback: Optional[str]
    final_result: Optional[str]
    error: Optional[str]
