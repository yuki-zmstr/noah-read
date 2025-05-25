from typing import Dict, List, Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from .nodes import (
    detect_intent,
    process_request,
    format_response,
    AgentState
)

# Define the agent state type


class AgentStateDict(TypedDict):
    chat_history: List[BaseMessage]
    user_input: str
    current_book: Dict | None
    last_recommendations: List[Dict]
    intent_data: Dict | None
    action_result: Dict | None


def create_agent_workflow() -> StateGraph:
    """Create the agent workflow using LangGraph."""

    # Create the workflow graph
    workflow = StateGraph(AgentStateDict)

    # Add nodes to the graph
    workflow.add_node("detect_intent", detect_intent)
    workflow.add_node("process_request", process_request)
    workflow.add_node("format_response", format_response)

    # Define the edges
    workflow.add_edge("detect_intent", "process_request")
    workflow.add_edge("process_request", "format_response")
    workflow.add_edge("format_response", END)

    # Set the entry point
    workflow.set_entry_point("detect_intent")

    return workflow.compile()


def create_initial_state() -> AgentStateDict:
    """Create initial state for the workflow."""
    return AgentStateDict(
        chat_history=[],
        user_input="",
        current_book=None,
        last_recommendations=[],
        intent_data=None,
        action_result=None
    )
