"""Diagnostic question tools for GTM assessment."""

from langchain_core.tools import tool

from gtm_agent.schemas import DiagnosticQuestion

# Define the 3 diagnostic questions with button options
DIAGNOSTIC_QUESTIONS = {
    1: DiagnosticQuestion(
        question_id="q1_icp",
        question_text="Who is your ideal customer?",
        options=[
            "SMB Founders (1-50 employees)",
            "Mid-Market (50-500 employees)",
            "Enterprise (500+ employees)",
            "Consumer/B2C",
            "Not sure yet",
        ],
        phase="icp",
    ),
    2: DiagnosticQuestion(
        question_id="q2_problem",
        question_text="How clear is the problem you solve?",
        options=[
            "Crystal clear - customers describe it to us",
            "Pretty clear - we've validated it",
            "Somewhat clear - we think we know",
            "Still figuring it out",
        ],
        phase="messaging",
    ),
    3: DiagnosticQuestion(
        question_id="q3_validation",
        question_text="How validated is your solution?",
        options=[
            "Revenue from target ICP",
            "Pilots/design partners",
            "Interest/waitlist",
            "Not validated yet",
        ],
        phase="validation",
    ),
}


@tool
def get_diagnostic_question(question_number: int) -> dict:
    """Get diagnostic question with button options.

    This tool returns a structured diagnostic question that should be
    presented to the user with button options. The user should select
    one of the provided options.

    Args:
        question_number: Which question (1, 2, or 3)

    Returns:
        Dict with question_id, question_text, options, and phase

    Raises:
        ValueError: If question_number is not 1, 2, or 3
    """
    if question_number not in DIAGNOSTIC_QUESTIONS:
        raise ValueError(f"Invalid question_number: {question_number}. Must be 1, 2, or 3.")

    question = DIAGNOSTIC_QUESTIONS[question_number]
    return question.model_dump()


def get_all_diagnostic_questions() -> list[dict]:
    """Get all diagnostic questions in order.

    Returns:
        List of all 3 diagnostic questions as dicts
    """
    return [DIAGNOSTIC_QUESTIONS[i].model_dump() for i in range(1, 4)]
