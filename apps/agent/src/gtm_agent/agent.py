"""GTM Deep Agent - Main agent factory."""

import os

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph

from gtm_agent.prompts import GTM_SYSTEM_PROMPT
from gtm_agent.schemas import ArtifactMetadata, DiagnosticAnswer, EscalatorScorecard

# Check if running in LangGraph API environment
# LangGraph API sets various env vars - check common ones
running_in_langgraph_api = (
    os.environ.get("LANGGRAPH_API") == "true"
    or os.environ.get("LANGGRAPH_API_URL") is not None
    or "langgraph" in os.environ.get("_", "").lower()
)


class GTMState(MessagesState):
    """State for GTM Deep Agent.

    Extends MessagesState with GTM-specific fields for tracking
    the diagnostic flow and artifact generation.
    """

    # Diagnostic state
    diagnostic_complete: bool = False
    diagnostic_answers: list[DiagnosticAnswer] = []
    current_question: int = 0

    # Scorecard state
    scorecard: EscalatorScorecard | None = None

    # Artifact state
    artifacts: list[ArtifactMetadata] = []

    # Voice profile (optional)
    voice_profile: dict | None = None

    # Company context
    company_name: str | None = None
    product_description: str | None = None


def create_gtm_agent(
    model: str = "anthropic:claude-sonnet-4-20250514",
    use_memory: bool = True,
):
    """Create GTM Deep Agent with subagents and tools.

    Args:
        model: The model to use for the agent
        use_memory: Whether to enable checkpointing for session persistence

    Returns:
        A configured deep agent instance
    """
    # Import here to allow module to load without deepagents installed
    from deepagents import create_deep_agent

    # Import subagents
    from gtm_agent.subagents import (
        escalator_subagent,
        narrative_subagent,
        voice_cloner_subagent,
    )

    # Import tools
    from gtm_agent.tools import (
        calculate_escalator_level,
        get_diagnostic_question,
        web_fetch,
        write_artifact,
    )

    # Tools available to the agent
    tools = [
        # Diagnostic tools
        get_diagnostic_question,
        calculate_escalator_level,
        # Artifact tools
        write_artifact,
        # Web tools
        web_fetch,
    ]

    # Subagents available to the agent
    subagents = [
        narrative_subagent,
        voice_cloner_subagent,
        escalator_subagent,
    ]

    # Configure checkpointer based on environment
    checkpointer = None
    if use_memory and not running_in_langgraph_api:
        checkpointer = MemorySaver()

    return create_deep_agent(
        model=model,
        tools=tools,
        subagents=subagents,
        system_prompt=GTM_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


def create_gtm_graph(use_memory: bool = True):
    """Create GTM agent as a LangGraph StateGraph.

    This is an alternative to create_deep_agent that gives more control
    over the agent's execution flow.

    Args:
        use_memory: Whether to enable checkpointing

    Returns:
        Compiled StateGraph
    """
    from langchain_anthropic import ChatAnthropic

    from gtm_agent.tools import (
        calculate_escalator_level,
        get_diagnostic_question,
        web_fetch,
        write_artifact,
    )

    # Initialize the model
    model = ChatAnthropic(model="claude-sonnet-4-20250514")

    # Bind tools to model
    tools = [
        get_diagnostic_question,
        calculate_escalator_level,
        write_artifact,
        web_fetch,
    ]
    model_with_tools = model.bind_tools(tools)

    # Define the agent node
    def agent_node(state: GTMState):
        """Main agent node that processes messages and calls tools."""
        messages = state["messages"]
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    # Define the tool execution node
    def tool_node(state: GTMState):
        """Execute tools called by the agent."""
        from langgraph.prebuilt import ToolNode

        tool_executor = ToolNode(tools)
        return tool_executor.invoke(state)

    # Define routing logic
    def should_continue(state: GTMState):
        """Determine whether to continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]

        # If there are tool calls, execute them
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        # Otherwise, end
        return END

    # Build the graph
    workflow = StateGraph(GTMState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)

    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")

    # Compile with optional checkpointer
    checkpointer = MemorySaver() if use_memory and not running_in_langgraph_api else None
    return workflow.compile(checkpointer=checkpointer)


# Default agent instance for LangGraph deployment
# Don't pass checkpointer - LangGraph API provides persistence automatically
agent = create_gtm_agent(use_memory=False)
