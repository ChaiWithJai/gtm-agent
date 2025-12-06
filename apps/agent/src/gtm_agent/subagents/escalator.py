"""Escalator diagnostician subagent for deep GTM analysis."""

from gtm_agent.prompts import ESCALATOR_SUBAGENT_PROMPT
from gtm_agent.tools.artifacts import write_artifact

# Escalator diagnostician subagent configuration
escalator_subagent = {
    "name": "escalator-diagnostician",
    "description": (
        "Provides deep GTM Escalator analysis with level-specific recommendations. "
        "Explains what's missing at current level and why not to skip ahead."
    ),
    "system_prompt": ESCALATOR_SUBAGENT_PROMPT,
    "tools": [write_artifact],
    "model": "anthropic:claude-sonnet-4-20250514",
}


# GTM Escalator Framework definitions
GTM_LEVELS = {
    1: {
        "name": "Problem-Solution Fit",
        "description": "Can articulate the problem clearly and have initial solution",
        "criteria": [
            "Can describe customer problem in one sentence",
            "Have talked to at least 5 potential customers",
            "Understand why current solutions fail",
        ],
        "common_gaps": [
            "Problem statement not clearly defined",
            "No customer validation of the problem",
            "Unable to articulate what you do in one sentence",
        ],
    },
    2: {
        "name": "Messaging Clarity",
        "description": "Have clear positioning and value proposition",
        "criteria": [
            "Positioning statement exists and tested",
            "Value proposition resonates with target audience",
            "Can explain differentiation vs alternatives",
        ],
        "common_gaps": [
            "No positioning statement",
            "Value proposition unclear or untested",
            "Messaging not tested with customers",
        ],
    },
    3: {
        "name": "ICP Definition",
        "description": "Know exactly who to target and why",
        "criteria": [
            "ICP defined with specific criteria",
            "Understand buyer triggers and timing",
            "Have psychographic profile of ideal customer",
        ],
        "common_gaps": [
            "ICP too broad or undefined",
            "No documented buyer triggers",
            "Missing psychographic profile",
        ],
    },
    4: {
        "name": "Channel Fit",
        "description": "Have 1-2 working acquisition channels",
        "criteria": [
            "At least one channel producing customers",
            "Understand unit economics per channel",
            "Can predict results from channel investment",
        ],
        "common_gaps": [
            "No repeatable channel identified",
            "No sales playbook or process",
            "Unable to delegate sales/marketing",
        ],
    },
    5: {
        "name": "Scale Ready",
        "description": "Ready to scale with documented playbooks",
        "criteria": [
            "Multiple channels working",
            "Playbooks for delegation exist",
            "Can hire and onboard sales/marketing",
        ],
        "common_gaps": [
            "No scale playbook documented",
            "Single channel dependency",
            "Founder still required for all deals",
        ],
    },
}


def build_escalator_context(
    diagnostic_answers: dict[str, str],
    company_name: str,
    product_description: str,
) -> dict:
    """Build context dict for escalator diagnostician subagent.

    Args:
        diagnostic_answers: Dict mapping question_id to selected_option
        company_name: Name of the company
        product_description: Description of the product

    Returns:
        Context dict to pass to escalator subagent
    """
    return {
        "diagnostic_answers": diagnostic_answers,
        "company_name": company_name,
        "product_description": product_description,
        "gtm_levels": GTM_LEVELS,
    }


def get_level_info(level: int) -> dict:
    """Get detailed information about a GTM level.

    Args:
        level: GTM level (1-5)

    Returns:
        Dict with level name, description, criteria, and common gaps
    """
    if level not in GTM_LEVELS:
        raise ValueError(f"Invalid level: {level}. Must be 1-5.")
    return GTM_LEVELS[level]


def get_level_up_criteria(current_level: int) -> str:
    """Get criteria to advance to next level.

    Args:
        current_level: Current GTM level

    Returns:
        String describing what's needed to level up
    """
    if current_level >= 5:
        return "You're at the highest level! Focus on optimization and scale."

    next_level = current_level + 1
    next_info = GTM_LEVELS[next_level]

    criteria = " AND ".join(next_info["criteria"][:2])
    return f"To reach Level {next_level} ({next_info['name']}): {criteria}"


ACTION_PLAN_TEMPLATE = """# GTM Action Plan

## Current State

**Level**: {level} - {level_name}

**Assessment Summary**: {summary}

## Priority Actions

### This Week
{weekly_actions}

### This Month
{monthly_actions}

## Level-Up Criteria

{level_up_criteria}

## Why This Matters

{rationale}

---

*Generated by GTM Deep Agent Escalator Diagnostician*
"""
