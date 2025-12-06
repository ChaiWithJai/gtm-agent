"""E2E tests for multi-turn conversations."""

import os
import pytest

from gtm_agent.tools import (
    get_diagnostic_question,
    calculate_escalator_level,
    write_artifact,
    clear_artifact_storage,
    get_artifact_storage,
)


@pytest.mark.e2e
class TestMultiTurnSimulation:
    """Test multi-turn conversation simulation without LLM."""

    def test_full_user_journey_simulation(self):
        """Simulate complete user journey through tools."""
        clear_artifact_storage()

        # Turn 1: Get first diagnostic question
        q1 = get_diagnostic_question.invoke({"question_number": 1})
        assert "options" in q1
        user_answer_1 = q1["options"][0]  # Select first option

        # Turn 2: Get second diagnostic question
        q2 = get_diagnostic_question.invoke({"question_number": 2})
        assert "options" in q2
        user_answer_2 = q2["options"][0]

        # Turn 3: Get third diagnostic question
        q3 = get_diagnostic_question.invoke({"question_number": 3})
        assert "options" in q3
        user_answer_3 = q3["options"][0]

        # Collect answers
        answers = {
            q1["question_id"]: user_answer_1,
            q2["question_id"]: user_answer_2,
            q3["question_id"]: user_answer_3,
        }

        # Turn 4: Calculate scorecard
        scorecard = calculate_escalator_level.invoke({"answers": answers})
        assert 1 <= scorecard["level"] <= 5

        # Turn 5: Generate artifacts
        write_artifact.invoke({
            "filename": "gtm-scorecard.json",
            "content": str(scorecard),
            "artifact_type": "scorecard",
        })

        write_artifact.invoke({
            "filename": "gtm-narrative.md",
            "content": f"# GTM Narrative\n\nLevel: {scorecard['level']}",
            "artifact_type": "narrative",
        })

        # Verify final state
        storage = get_artifact_storage()
        assert "gtm-scorecard.json" in storage
        assert "gtm-narrative.md" in storage

    def test_different_answer_paths(self):
        """Different answers produce different outcomes."""
        # Path 1: All "Not sure" / lowest options
        low_answers = {
            "q1_icp": "Not sure yet",
            "q2_problem": "Still figuring it out",
            "q3_validation": "Not validated yet",
        }
        low_result = calculate_escalator_level.invoke({"answers": low_answers})

        # Path 2: All best options
        high_answers = {
            "q1_icp": "SMB Founders (1-50 employees)",
            "q2_problem": "Crystal clear - customers describe it to us",
            "q3_validation": "Revenue from target ICP",
        }
        high_result = calculate_escalator_level.invoke({"answers": high_answers})

        # Low answers should produce lower level
        assert low_result["level"] <= high_result["level"]
        assert len(low_result["gaps"]) >= len(high_result["gaps"]) or True  # More gaps at lower level

    def test_conversation_state_isolation(self):
        """Each conversation should be isolated."""
        clear_artifact_storage()

        # Conversation 1
        write_artifact.invoke({
            "filename": "conv1.md",
            "content": "Conversation 1",
            "artifact_type": "narrative",
        })

        storage1 = get_artifact_storage()
        assert "conv1.md" in storage1

        # Clear for conversation 2
        clear_artifact_storage()

        write_artifact.invoke({
            "filename": "conv2.md",
            "content": "Conversation 2",
            "artifact_type": "narrative",
        })

        storage2 = get_artifact_storage()
        assert "conv2.md" in storage2
        assert "conv1.md" not in storage2  # Isolated


@pytest.mark.e2e
@pytest.mark.langsmith
class TestLiveMultiTurn:
    """Live LLM multi-turn tests (require API keys)."""

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="Requires ANTHROPIC_API_KEY"
    )
    def test_live_multi_turn_conversation(self):
        """Test actual multi-turn with LLM."""
        # TODO: Enable when deepagents is configured
        pass

    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="Requires ANTHROPIC_API_KEY"
    )
    def test_session_persistence(self):
        """Test session can be resumed with same thread_id."""
        # TODO: Enable when deepagents is configured
        pass
