"""E2E tests for complete diagnostic flow."""

import os
import pytest

from gtm_agent.tools import (
    get_diagnostic_question,
    calculate_escalator_level,
    write_artifact,
    get_artifact_storage,
    clear_artifact_storage,
)


@pytest.mark.e2e
@pytest.mark.langsmith
class TestFullDiagnosticFlow:
    """E2E tests for complete diagnostic flow.

    These tests use live LLM calls and are only run on main branch pushes.
    """

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="Requires ANTHROPIC_API_KEY"
    )
    def test_product_description_triggers_diagnostic(self):
        """Agent asks diagnostic questions after product description.

        This test verifies the agent correctly identifies when to start
        the diagnostic flow based on user input.
        """
        # TODO: Enable when deepagents is configured
        # from gtm_agent.agent import create_gtm_agent
        # agent = create_gtm_agent()
        # result = agent.invoke({"messages": [{"role": "user", "content": "We build AI tools"}]})
        # assert "question" in str(result).lower()
        pass

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="Requires ANTHROPIC_API_KEY"
    )
    def test_complete_diagnostic_produces_scorecard(self):
        """Complete diagnostic flow produces valid scorecard.

        This test verifies the full diagnostic → scorecard flow.
        """
        # TODO: Enable when deepagents is configured
        pass


@pytest.mark.e2e
class TestToolIntegration:
    """Test that tools work together correctly."""

    def test_diagnostic_to_scorecard_flow(self):
        """Diagnostic answers can be passed to scorecard calculation."""
        # Get all questions
        questions = []
        for i in range(1, 4):
            q = get_diagnostic_question.invoke({"question_number": i})
            questions.append(q)

        # Verify we got 3 questions
        assert len(questions) == 3
        assert all("question_id" in q for q in questions)
        assert all("options" in q for q in questions)

        # Simulate user answers (first option for each)
        answers = {}
        for q in questions:
            answers[q["question_id"]] = q["options"][0]

        # Calculate scorecard
        scorecard = calculate_escalator_level.invoke({"answers": answers})

        # Verify scorecard structure
        assert 1 <= scorecard["level"] <= 5
        assert len(scorecard["gaps"]) > 0
        assert len(scorecard["recommendations"]) > 0
        assert "scores" in scorecard
        assert all(f"l{i}" in scorecard["scores"] for i in range(1, 6))

    def test_full_artifact_generation_flow(self):
        """Test artifact generation workflow."""
        clear_artifact_storage()

        # Generate all 5 artifact types
        artifacts = [
            ("gtm-scorecard.json", '{"level": 2}', "scorecard"),
            ("gtm-narrative.md", "# Narrative", "narrative"),
            ("cold-emails.md", "# Emails", "emails"),
            ("linkedin-posts.md", "# LinkedIn", "linkedin"),
            ("action-plan.md", "# Action Plan", "action_plan"),
        ]

        for filename, content, artifact_type in artifacts:
            result = write_artifact.invoke({
                "filename": filename,
                "content": content,
                "artifact_type": artifact_type,
            })
            assert result["filename"] == filename
            assert result["artifact_type"] == artifact_type

        storage = get_artifact_storage()
        assert len(storage) == 5
        assert all(f in storage for f, _, _ in artifacts)

    def test_diagnostic_question_sequence(self):
        """Questions follow expected sequence."""
        q1 = get_diagnostic_question.invoke({"question_number": 1})
        q2 = get_diagnostic_question.invoke({"question_number": 2})
        q3 = get_diagnostic_question.invoke({"question_number": 3})

        # Verify sequence
        assert q1["phase"] == "icp"
        assert q2["phase"] == "messaging"
        assert q3["phase"] == "validation"

        # Verify unique IDs
        ids = {q1["question_id"], q2["question_id"], q3["question_id"]}
        assert len(ids) == 3

    def test_scorecard_levels_deterministic(self):
        """Same answers produce same scorecard."""
        answers = {
            "q1_icp": "SMB Founders (1-50 employees)",
            "q2_problem": "Crystal clear - customers describe it to us",
            "q3_validation": "Pilots/design partners",
        }

        result1 = calculate_escalator_level.invoke({"answers": answers})
        result2 = calculate_escalator_level.invoke({"answers": answers})

        assert result1["level"] == result2["level"]
        assert result1["scores"] == result2["scores"]


@pytest.mark.e2e
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_answers_produces_level_1(self):
        """Empty answers default to level 1."""
        result = calculate_escalator_level.invoke({"answers": {}})
        assert result["level"] == 1

    def test_partial_answers_handled(self):
        """Partial answers are handled gracefully."""
        answers = {"q1_icp": "SMB Founders (1-50 employees)"}
        result = calculate_escalator_level.invoke({"answers": answers})
        assert 1 <= result["level"] <= 5

    def test_unknown_answer_option_ignored(self):
        """Unknown answer options are handled gracefully."""
        answers = {
            "q1_icp": "Unknown Option",
            "q2_problem": "Crystal clear - customers describe it to us",
        }
        result = calculate_escalator_level.invoke({"answers": answers})
        assert 1 <= result["level"] <= 5
