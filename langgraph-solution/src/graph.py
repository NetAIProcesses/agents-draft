"""LangGraph workflow for the multi-agent energy processes system."""

import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.agents.meter_reading_agent import meter_reading_agent, METER_READING_TOOLS
from src.agents.prepayment_agent import prepayment_agent, PREPAYMENT_TOOLS
from src.agents.faq_agent import faq_agent, FAQ_TOOLS
from src.agents.supervisor_agent import supervisor_agent


# ============ State Definition ============

class AgentState(TypedDict):
    """State shared between agents in the workflow."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_agent: str
    current_agent: str
    context: dict


# ============ Node Functions ============

def create_agent_node(agent_info: dict, llm):
    """Create a node function for an agent."""
    agent_chain = agent_info["create_agent"](llm)
    
    async def agent_node(state: AgentState) -> dict:
        """Execute the agent with the current state."""
        messages = state["messages"]
        
        # Invoke the agent
        response = await agent_chain.ainvoke({"messages": messages})
        
        return {
            "messages": [response],
            "current_agent": agent_info["name"],
            "next_agent": "",
            "context": state.get("context", {}),
        }
    
    return agent_node


def create_supervisor_node(llm):
    """Create the supervisor node that routes between agents."""
    supervisor_chain = supervisor_agent["create_chain"](llm)
    
    async def supervisor_node(state: AgentState) -> dict:
        """Determine which agent should handle the request."""
        messages = state["messages"]
        
        # Get routing decision from supervisor
        response = await supervisor_chain.ainvoke({"messages": messages})
        
        # Parse the JSON response
        try:
            content = response.content
            # Try to extract JSON from the response
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            routing = json.loads(json_str)
            next_agent = routing.get("next_agent", "FINISH")
        except (json.JSONDecodeError, IndexError):
            # Default to FINISH if parsing fails
            next_agent = "FINISH"
        
        return {
            "messages": [],
            "next_agent": next_agent,
            "current_agent": "supervisor",
            "context": state.get("context", {}),
        }
    
    return supervisor_node


# ============ Routing Functions ============

def route_from_supervisor(state: AgentState) -> str:
    """Route from supervisor to the next agent."""
    next_agent = state.get("next_agent", "FINISH")
    if next_agent == "meter_reading_agent":
        return "meter_reading"
    elif next_agent == "prepayment_agent":
        return "prepayment"
    elif next_agent == "faq_agent":
        return "faq"
    else:
        return "end"


def should_continue_meter_reading(state: AgentState) -> str:
    """Determine if meter reading agent should continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1] if messages else None
    
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "supervisor"


def should_continue_prepayment(state: AgentState) -> str:
    """Determine if prepayment agent should continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1] if messages else None
    
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "supervisor"


def should_continue_faq(state: AgentState) -> str:
    """Determine if FAQ agent should continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1] if messages else None
    
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "supervisor"


# ============ Workflow Builder ============

def build_workflow(llm):
    """Build and return the complete LangGraph workflow."""
    
    # Create the workflow graph
    workflow = StateGraph(AgentState)
    
    # Create agent nodes
    meter_reading_node = create_agent_node(meter_reading_agent, llm)
    prepayment_node = create_agent_node(prepayment_agent, llm)
    faq_node = create_agent_node(faq_agent, llm)
    supervisor_node = create_supervisor_node(llm)
    
    # Create tool nodes
    meter_reading_tool_node = ToolNode(METER_READING_TOOLS)
    prepayment_tool_node = ToolNode(PREPAYMENT_TOOLS)
    faq_tool_node = ToolNode(FAQ_TOOLS)
    
    # Add nodes to the workflow
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("meter_reading", meter_reading_node)
    workflow.add_node("prepayment", prepayment_node)
    workflow.add_node("faq", faq_node)
    workflow.add_node("meter_reading_tools", meter_reading_tool_node)
    workflow.add_node("prepayment_tools", prepayment_tool_node)
    workflow.add_node("faq_tools", faq_tool_node)
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    # Add conditional edges from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "meter_reading": "meter_reading",
            "prepayment": "prepayment",
            "faq": "faq",
            "end": END,
        }
    )
    
    # Add conditional edges from meter reading agent
    workflow.add_conditional_edges(
        "meter_reading",
        should_continue_meter_reading,
        {
            "tools": "meter_reading_tools",
            "supervisor": "supervisor",
        }
    )
    
    # Add conditional edges from prepayment agent
    workflow.add_conditional_edges(
        "prepayment",
        should_continue_prepayment,
        {
            "tools": "prepayment_tools",
            "supervisor": "supervisor",
        }
    )
    
    # Add conditional edges from FAQ agent
    workflow.add_conditional_edges(
        "faq",
        should_continue_faq,
        {
            "tools": "faq_tools",
            "supervisor": "supervisor",
        }
    )
    
    # Route from tools back to agents
    workflow.add_edge("meter_reading_tools", "meter_reading")
    workflow.add_edge("prepayment_tools", "prepayment")
    workflow.add_edge("faq_tools", "faq")
    
    # Compile the workflow
    return workflow.compile()


# ============ Convenience Functions ============

async def run_workflow(user_input: str, llm, state: AgentState = None) -> AgentState:
    """Run the workflow with a user input."""
    workflow = build_workflow(llm)
    
    if state is None:
        state = {
            "messages": [HumanMessage(content=user_input)],
            "next_agent": "",
            "current_agent": "",
            "context": {},
        }
    else:
        # Add the new message to existing state
        state["messages"] = list(state["messages"]) + [HumanMessage(content=user_input)]
    
    # Run the workflow
    result = await workflow.ainvoke(state)
    
    return result
