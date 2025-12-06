"""Integration tests for agent single-step decisions."""

import pytest


class TestSingleStepDecisions:
    """Integration tests for agent's single-step tool selection.

    These tests use VCR cassettes to record/replay API calls.
    """

    @pytest.mark.integration
    @pytest.mark.vcr
    def test_diagnostic_question_returns_structure(self):
        """Diagnostic tool returns proper structure."""
        from gtm_agent.tools import get_diagnostic_question

        result = get_diagnostic_question.invoke({"question_number": 1})

        assert "question_id" in result
        assert "question_text" in result
        assert "options" in result
        assert len(result["options"]) >= 3

    @pytest.mark.integration
    @pytest.mark.vcr
    def test_scorecard_calculation_with_answers(self):
        """Scorecard calculation produces valid output."""
        from gtm_agent.tools import calculate_escalator_level

        answers = {
            "q1_icp": "SMB Founders (1-50 employees)",
            "q2_problem": "Crystal clear - customers describe it to us",
            "q3_validation": "Pilots/design partners",
        }

        result = calculate_escalator_level.invoke({"answers": answers})

        assert "level" in result
        assert 1 <= result["level"] <= 5
        assert "scores" in result
        assert "gaps" in result
        assert "recommendations" in result

    @pytest.mark.integration
    @pytest.mark.vcr
    def test_artifact_write_and_retrieve(self):
        """Artifact writing and retrieval works correctly."""
        from gtm_agent.tools import write_artifact, get_artifact_storage, clear_artifact_storage

        clear_artifact_storage()

        content = "# Test Narrative\n\nThis is test content."
        result = write_artifact.invoke({
            "filename": "test-narrative.md",
            "content": content,
            "artifact_type": "narrative",
        })

        assert result["filename"] == "test-narrative.md"
        assert result["artifact_type"] == "narrative"

        storage = get_artifact_storage()
        assert "test-narrative.md" in storage
        assert storage["test-narrative.md"] == content
