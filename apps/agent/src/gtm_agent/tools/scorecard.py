"""GTM Escalator scorecard calculation tools."""

from langchain_core.tools import tool

from gtm_agent.schemas import EscalatorScorecard

# Scoring weights for each answer option
SCORING_MATRIX = {
    # Question 1: ICP Clarity
    "q1_icp": {
        "SMB Founders (1-50 employees)": {"l3": 20},
        "Mid-Market (50-500 employees)": {"l3": 20},
        "Enterprise (500+ employees)": {"l3": 20},
        "Consumer/B2C": {"l3": 20},
        "Not sure yet": {"l3": 0},
    },
    # Question 2: Problem Clarity
    "q2_problem": {
        "Crystal clear - customers describe it to us": {"l1": 30, "l2": 20},
        "Pretty clear - we've validated it": {"l1": 20, "l2": 10},
        "Somewhat clear - we think we know": {"l1": 10, "l2": 0},
        "Still figuring it out": {"l1": 0, "l2": 0},
    },
    # Question 3: Validation Status
    "q3_validation": {
        "Revenue from target ICP": {"l4": 30, "l3": 20},
        "Pilots/design partners": {"l4": 20, "l3": 10},
        "Interest/waitlist": {"l4": 10, "l3": 5},
        "Not validated yet": {"l4": 0, "l3": 0},
    },
}

# Gap definitions by level
LEVEL_GAPS = {
    1: [
        "Problem statement not clearly defined",
        "No customer validation of the problem",
        "Unable to articulate what you do in one sentence",
    ],
    2: [
        "No positioning statement",
        "Value proposition unclear",
        "Messaging not tested with customers",
    ],
    3: [
        "ICP too broad or undefined",
        "No documented buyer triggers",
        "Missing psychographic profile",
    ],
    4: [
        "No repeatable channel identified",
        "No sales playbook or process",
        "Unable to delegate sales/marketing",
    ],
    5: [
        "No scale playbook documented",
        "Single channel dependency",
        "Founder still required for all deals",
    ],
}

# Recommendations by level
LEVEL_RECOMMENDATIONS = {
    1: [
        "Interview 5 potential customers this week",
        "Write down the problem you solve in one sentence",
        "Document 3 specific pain points your customers have",
    ],
    2: [
        "Create a positioning statement using: For [ICP] who [pain], we [solution]",
        "Test your messaging with 3 customers",
        "Define your unique value vs alternatives",
    ],
    3: [
        "Define your ICP with 5 specific criteria",
        "Document the trigger events that make buyers ready",
        "Create an ideal customer profile document",
    ],
    4: [
        "Identify 2 channels where your ICP hangs out",
        "Run a small experiment in each channel",
        "Document what messaging works in each channel",
    ],
    5: [
        "Create a sales playbook for delegation",
        "Build a second channel for diversification",
        "Systematize your content creation process",
    ],
}


def _calculate_scores(answers: dict[str, str]) -> dict[str, int]:
    """Calculate scores per level from diagnostic answers.

    Args:
        answers: Dict mapping question_id to selected_option

    Returns:
        Dict with scores for l1-l5 (0-100 scale)
    """
    scores = {"l1": 50, "l2": 50, "l3": 0, "l4": 0, "l5": 0}  # Base scores

    for question_id, selected_option in answers.items():
        if question_id in SCORING_MATRIX:
            option_scores = SCORING_MATRIX[question_id].get(selected_option, {})
            for level, points in option_scores.items():
                scores[level] = scores.get(level, 0) + points

    # Cap scores at 100
    return {k: min(v, 100) for k, v in scores.items()}


def _determine_level(scores: dict[str, int]) -> int:
    """Determine current GTM level based on scores.

    Args:
        scores: Dict with l1-l5 scores

    Returns:
        Current level (1-5)
    """
    # Check from highest to lowest
    if scores.get("l5", 0) >= 60:
        return 5
    elif scores.get("l4", 0) >= 40:
        return 4
    elif scores.get("l3", 0) >= 30:
        return 3
    elif scores.get("l2", 0) >= 60:
        return 2
    else:
        return 1


def _get_gaps_for_level(level: int, answers: dict[str, str]) -> list[str]:
    """Get relevant gaps based on level and answers.

    Args:
        level: Current GTM level
        answers: Diagnostic answers

    Returns:
        List of gap descriptions
    """
    gaps = []

    # Add level-specific gaps
    if level in LEVEL_GAPS:
        gaps.extend(LEVEL_GAPS[level][:2])  # Top 2 gaps for current level

    # Add answer-specific gaps
    icp_answer = answers.get("q1_icp", "")
    problem_answer = answers.get("q2_problem", "")
    validation_answer = answers.get("q3_validation", "")

    if "Not sure yet" in icp_answer:
        gaps.append("No clear ICP defined")

    if "figuring" in problem_answer.lower():
        gaps.append("Problem clarity needs work")

    if "Not validated" in validation_answer:
        gaps.append("Solution not yet validated with customers")

    return gaps[:5]  # Max 5 gaps


def _get_recommendations_for_level(level: int) -> list[str]:
    """Get prioritized recommendations for current level.

    Args:
        level: Current GTM level

    Returns:
        List of actionable recommendations
    """
    recommendations = []

    # Primary recommendations from current level
    if level in LEVEL_RECOMMENDATIONS:
        recommendations.extend(LEVEL_RECOMMENDATIONS[level])

    # Add one recommendation from next level as stretch goal
    if level < 5 and (level + 1) in LEVEL_RECOMMENDATIONS:
        recommendations.append(f"Stretch: {LEVEL_RECOMMENDATIONS[level + 1][0]}")

    return recommendations[:5]


def _personalize_recommendations(
    recommendations: list[str],
    company_context: dict | None = None,
    answers: dict[str, str] | None = None,
) -> list[str]:
    """Personalize recommendations with company context.

    Args:
        recommendations: Base recommendations
        company_context: Optional dict with company_name, product_description, key_features
        answers: Diagnostic answers for additional context

    Returns:
        Personalized recommendations
    """
    if not company_context:
        return recommendations

    company_name = company_context.get("company_name", "your company")
    product_desc = company_context.get("product_description", "")
    features = company_context.get("key_features", [])

    personalized = []
    for rec in recommendations:
        # Add company-specific context
        if "ICP" in rec and answers:
            icp = answers.get("q1_icp", "")
            if icp and "Not sure" not in icp:
                rec = rec.replace("your ICP", icp).replace("ICP", icp)

        if "customers" in rec.lower() and product_desc:
            rec = f"{rec} (Focus on how {company_name} solves: {product_desc[:100]})"

        personalized.append(rec)

    # Add company-specific action items
    if features:
        personalized.append(
            f"Highlight {company_name}'s key differentiator: {features[0] if features else 'core feature'}"
        )

    return personalized[:5]


@tool
def calculate_escalator_level(
    answers: dict[str, str],
    company_context: dict | None = None,
) -> dict:
    """Calculate GTM Escalator level from diagnostic answers.

    This tool takes the user's diagnostic answers and calculates their
    current GTM Escalator level (1-5), along with identified gaps and
    prioritized recommendations. If company context is provided,
    recommendations are personalized to the specific company.

    Args:
        answers: Dict mapping question_id to selected_option
            Example: {"q1_icp": "SMB Founders", "q2_problem": "Crystal clear", "q3_validation": "Pilots"}
        company_context: Optional dict with company info from web_fetch
            Example: {"company_name": "Acme", "product_description": "...", "key_features": [...]}

    Returns:
        Dict matching EscalatorScorecard schema with level, scores, gaps, recommendations
    """
    scores = _calculate_scores(answers)
    level = _determine_level(scores)
    gaps = _get_gaps_for_level(level, answers)
    recommendations = _get_recommendations_for_level(level)

    # Personalize recommendations with company context
    recommendations = _personalize_recommendations(recommendations, company_context, answers)

    scorecard = EscalatorScorecard(
        level=level,
        scores=scores,
        gaps=gaps,
        recommendations=recommendations,
    )

    return scorecard.model_dump()
