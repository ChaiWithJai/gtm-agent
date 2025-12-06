"""GTM Deep Agent - Main agent factory."""

import os

from langgraph.checkpoint.memory import MemorySaver

from gtm_agent.prompts import GTM_SYSTEM_PROMPT

# Check if running in LangGraph API environment
running_in_langgraph_api = os.environ.get("LANGGRAPH_API") == "true"


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

    # Import tools (will be implemented in subsequent PRs)
    from gtm_agent.tools import (
        # get_diagnostic_question,
        # calculate_escalator_level,
        # generate_narrative,
        # generate_emails,
        # generate_linkedin_posts,
        # generate_action_plan,
        # web_fetch,
        # write_artifact,
    )

    # Import subagents (will be implemented in subsequent PRs)
    from gtm_agent.subagents import (
        # narrative_subagent,
        # voice_cloner_subagent,
        # escalator_subagent,
    )

    # Tools to be added as they are implemented
    tools = [
        # Diagnostic tools
        # get_diagnostic_question,
        # calculate_escalator_level,
        # Artifact tools
        # generate_narrative,
        # generate_emails,
        # generate_linkedin_posts,
        # generate_action_plan,
        # write_artifact,
        # Web tools
        # web_fetch,
    ]

    # Subagents to be added as they are implemented
    subagents = [
        # narrative_subagent,
        # voice_cloner_subagent,
        # escalator_subagent,
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


# Default agent instance for LangGraph deployment
agent = create_gtm_agent()
