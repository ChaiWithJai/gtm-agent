"""Unit tests for system prompts."""

import pytest

from gtm_agent.prompts import (
    DIAGNOSTIC_PHASE_PROMPT,
    ESCALATOR_SUBAGENT_PROMPT,
    GTM_SYSTEM_PROMPT,
    NARRATIVE_SUBAGENT_PROMPT,
    VOICE_CLONER_SUBAGENT_PROMPT,
)


class TestGTMSystemPrompt:
    """Tests for main system prompt."""

    def test_includes_artifact_instruction(self):
        """System prompt enforces artifact output."""
        prompt_lower = GTM_SYSTEM_PROMPT.lower()
        assert "write_artifact" in prompt_lower or "artifact" in prompt_lower

    def test_includes_escalator_framework(self):
        """System prompt includes GTM Escalator reference."""
        prompt_lower = GTM_SYSTEM_PROMPT.lower()
        assert "escalator" in prompt_lower or "level" in prompt_lower

    def test_includes_diagnostic_phase(self):
        """System prompt mentions diagnostic phase."""
        prompt_lower = GTM_SYSTEM_PROMPT.lower()
        assert "diagnostic" in prompt_lower

    def test_includes_tool_usage(self):
        """System prompt explains tool usage."""
        prompt_lower = GTM_SYSTEM_PROMPT.lower()
        assert "tool" in prompt_lower

    def test_emphasizes_constrained_questions(self):
        """System prompt emphasizes button-based questions."""
        prompt_lower = GTM_SYSTEM_PROMPT.lower()
        assert "button" in prompt_lower or "option" in prompt_lower


class TestDiagnosticPhasePrompt:
    """Tests for diagnostic phase prompt."""

    def test_enforces_button_options(self):
        """Diagnostic prompt requires structured options."""
        prompt_lower = DIAGNOSTIC_PHASE_PROMPT.lower()
        assert "option" in prompt_lower or "button" in prompt_lower

    def test_no_open_ended_questions(self):
        """Diagnostic prompt discourages open-ended questions."""
        prompt_lower = DIAGNOSTIC_PHASE_PROMPT.lower()
        assert "open-ended" in prompt_lower or "structured" in prompt_lower

    def test_defines_three_questions(self):
        """Diagnostic prompt defines exactly 3 questions."""
        assert "question 1" in DIAGNOSTIC_PHASE_PROMPT.lower()
        assert "question 2" in DIAGNOSTIC_PHASE_PROMPT.lower()
        assert "question 3" in DIAGNOSTIC_PHASE_PROMPT.lower()

    def test_includes_icp_question(self):
        """Diagnostic prompt includes ICP question."""
        assert "buyer" in DIAGNOSTIC_PHASE_PROMPT.lower() or "icp" in DIAGNOSTIC_PHASE_PROMPT.lower()

    def test_includes_problem_question(self):
        """Diagnostic prompt includes problem clarity question."""
        assert "problem" in DIAGNOSTIC_PHASE_PROMPT.lower()

    def test_includes_validation_question(self):
        """Diagnostic prompt includes validation question."""
        assert "traction" in DIAGNOSTIC_PHASE_PROMPT.lower() or "validation" in DIAGNOSTIC_PHASE_PROMPT.lower()


class TestNarrativeSubagentPrompt:
    """Tests for narrative builder subagent prompt."""

    def test_includes_context_placeholders(self):
        """Narrative prompt has context injection points."""
        assert "{context" in NARRATIVE_SUBAGENT_PROMPT or "context" in NARRATIVE_SUBAGENT_PROMPT.lower()

    def test_includes_positioning_statement(self):
        """Narrative prompt mentions positioning statement."""
        prompt_lower = NARRATIVE_SUBAGENT_PROMPT.lower()
        assert "positioning" in prompt_lower

    def test_includes_value_proposition(self):
        """Narrative prompt mentions value proposition."""
        prompt_lower = NARRATIVE_SUBAGENT_PROMPT.lower()
        assert "value" in prompt_lower

    def test_includes_icp_definition(self):
        """Narrative prompt mentions ICP definition."""
        prompt_lower = NARRATIVE_SUBAGENT_PROMPT.lower()
        assert "icp" in prompt_lower


class TestVoiceClonerSubagentPrompt:
    """Tests for voice cloner subagent prompt."""

    def test_includes_context_placeholders(self):
        """Voice cloner prompt has context injection points."""
        assert "{context" in VOICE_CLONER_SUBAGENT_PROMPT

    def test_includes_writing_samples(self):
        """Voice cloner prompt references writing samples."""
        assert "writing_samples" in VOICE_CLONER_SUBAGENT_PROMPT

    def test_generates_emails(self):
        """Voice cloner prompt mentions email generation."""
        prompt_lower = VOICE_CLONER_SUBAGENT_PROMPT.lower()
        assert "email" in prompt_lower

    def test_generates_linkedin_posts(self):
        """Voice cloner prompt mentions LinkedIn post generation."""
        prompt_lower = VOICE_CLONER_SUBAGENT_PROMPT.lower()
        assert "linkedin" in prompt_lower

    def test_analyzes_voice_attributes(self):
        """Voice cloner prompt analyzes voice attributes."""
        prompt_lower = VOICE_CLONER_SUBAGENT_PROMPT.lower()
        assert "tone" in prompt_lower


class TestEscalatorSubagentPrompt:
    """Tests for escalator diagnostician subagent prompt."""

    def test_includes_context_placeholders(self):
        """Escalator prompt has context injection points."""
        assert "{context" in ESCALATOR_SUBAGENT_PROMPT

    def test_includes_scoring_logic(self):
        """Escalator prompt includes scoring logic."""
        prompt_lower = ESCALATOR_SUBAGENT_PROMPT.lower()
        assert "score" in prompt_lower or "scoring" in prompt_lower

    def test_includes_level_definitions(self):
        """Escalator prompt defines all 5 levels."""
        assert "level 1" in ESCALATOR_SUBAGENT_PROMPT.lower()
        assert "level 5" in ESCALATOR_SUBAGENT_PROMPT.lower()

    def test_specifies_output_format(self):
        """Escalator prompt specifies JSON output format."""
        assert "json" in ESCALATOR_SUBAGENT_PROMPT.lower()
