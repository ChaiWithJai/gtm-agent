"""E2E tests for complete diagnostic flow."""

import pytest


@pytest.mark.e2e
@pytest.mark.langsmith
class TestFullDiagnosticFlow:
    """E2E tests for complete diagnostic flow.

    These tests use live LLM calls and are only run on main branch pushes.
    """

    @pytest.mark.skip(reason="Requires ANTHROPIC_API_KEY and deepagents")
    def test_product_description_triggers_diagnostic(self):
        """Agent asks diagnostic questions after product description."""
        # This test requires live API keys and will be enabled when ready
        pass

    @pytest.mark.skip(reason="Requires ANTHROPIC_API_KEY and deepagents")
    def test_complete_diagnostic_produces_scorecard(self):
        """Complete diagnostic flow produces valid scorecard."""
        # This test requires live API keys and will be enabled when ready
        pass


@pytest.mark.e2e
class TestToolIntegration:
    """Test that tools work together correctly."""

    def test_diagnostic_to_scorecard_flow(self):
        """Diagnostic answers can be passed to scorecard calculation."""
        from gtm_agent.tools import get_diagnostic_question, calculate_escalator_level

        # Get all questions
        questions = []
        for i in range(1, 4):
            q = get_diagnostic_question.invoke({"question_number": i})
            questions.append(q)

        # Simulate user answers (first option for each)
        answers = {}
        for q in questions:
            answers[q["question_id"]] = q["options"][0]

        # Calculate scorecard
        scorecard = calculate_escalator_level.invoke({"answers": answers})

        assert 1 <= scorecard["level"] <= 5
        assert len(scorecard["gaps"]) > 0
        assert len(scorecard["recommendations"]) > 0

    def test_full_artifact_generation_flow(self):
        """Test artifact generation workflow."""
        from gtm_agent.tools import (
            write_artifact,
            get_artifact_storage,
            clear_artifact_storage,
        )

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
            write_artifact.invoke({
                "filename": filename,
                "content": content,
                "artifact_type": artifact_type,
            })

        storage = get_artifact_storage()
        assert len(storage) == 5
        assert all(f in storage for f, _, _ in artifacts)
