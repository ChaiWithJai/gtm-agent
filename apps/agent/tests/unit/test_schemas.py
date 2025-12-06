"""Unit tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from gtm_agent.schemas import (
    ArtifactMetadata,
    DiagnosticAnswer,
    DiagnosticQuestion,
    EscalatorScorecard,
    GTMLevel,
    SessionState,
)


class TestGTMLevel:
    """Tests for GTMLevel enum."""

    def test_level_values(self):
        """Level values match expected integers."""
        assert GTMLevel.PROBLEM_SOLUTION == 1
        assert GTMLevel.MESSAGING_CLARITY == 2
        assert GTMLevel.ICP_DEFINITION == 3
        assert GTMLevel.CHANNEL_FIT == 4
        assert GTMLevel.SCALE_READY == 5


class TestEscalatorScorecard:
    """Tests for EscalatorScorecard schema validation."""

    def test_valid_scorecard(self, sample_scorecard):
        """Valid scorecard passes validation."""
        scorecard = EscalatorScorecard(**sample_scorecard)
        assert scorecard.level == 3
        assert scorecard.scores["l1"] == 85

    def test_level_lower_bound(self):
        """Level must be at least 1."""
        with pytest.raises(ValidationError):
            EscalatorScorecard(
                level=0,
                scores={"l1": 80},
                gaps=[],
                recommendations=[],
            )

    def test_level_upper_bound(self):
        """Level must be at most 5."""
        with pytest.raises(ValidationError):
            EscalatorScorecard(
                level=6,
                scores={"l1": 80},
                gaps=[],
                recommendations=[],
            )

    def test_json_schema_export(self):
        """Schema exports valid JSON schema."""
        schema = EscalatorScorecard.model_json_schema()
        assert "level" in schema["properties"]
        assert "scores" in schema["properties"]
        assert "gaps" in schema["properties"]
        assert "recommendations" in schema["properties"]


class TestDiagnosticAnswer:
    """Tests for DiagnosticAnswer schema."""

    def test_valid_answer(self):
        """Valid answer with default confidence."""
        answer = DiagnosticAnswer(
            question_id="q1_icp",
            selected_option="SMB Founders",
        )
        assert answer.confidence == 1.0

    def test_valid_answer_with_confidence(self):
        """Valid answer with explicit confidence."""
        answer = DiagnosticAnswer(
            question_id="q1_icp",
            selected_option="SMB Founders",
            confidence=0.9,
        )
        assert answer.confidence == 0.9

    def test_confidence_lower_bound(self):
        """Confidence must be at least 0."""
        with pytest.raises(ValidationError):
            DiagnosticAnswer(
                question_id="q1",
                selected_option="Option A",
                confidence=-0.1,
            )

    def test_confidence_upper_bound(self):
        """Confidence must be at most 1."""
        with pytest.raises(ValidationError):
            DiagnosticAnswer(
                question_id="q1",
                selected_option="Option A",
                confidence=1.5,
            )


class TestDiagnosticQuestion:
    """Tests for DiagnosticQuestion schema."""

    def test_valid_question(self):
        """Valid question with options."""
        question = DiagnosticQuestion(
            question_id="q1_icp",
            question_text="Who is your primary buyer?",
            options=["SMB Founders", "Mid-Market", "Enterprise", "Consumers"],
            phase="icp",
        )
        assert len(question.options) == 4
        assert question.phase == "icp"

    def test_invalid_phase(self):
        """Phase must be valid literal."""
        with pytest.raises(ValidationError):
            DiagnosticQuestion(
                question_id="q1",
                question_text="Test?",
                options=["A", "B"],
                phase="invalid_phase",
            )


class TestArtifactMetadata:
    """Tests for ArtifactMetadata schema."""

    def test_valid_artifact(self):
        """Valid artifact metadata."""
        artifact = ArtifactMetadata(
            filename="narrative.md",
            artifact_type="narrative",
            size_bytes=1024,
            content_preview="# Strategic Narrative...",
        )
        assert artifact.filename == "narrative.md"
        assert artifact.artifact_type == "narrative"

    def test_content_preview_max_length(self):
        """Content preview must not exceed 200 characters."""
        with pytest.raises(ValidationError):
            ArtifactMetadata(
                filename="test.md",
                artifact_type="narrative",
                size_bytes=1024,
                content_preview="x" * 201,
            )

    def test_invalid_artifact_type(self):
        """Artifact type must be valid literal."""
        with pytest.raises(ValidationError):
            ArtifactMetadata(
                filename="test.md",
                artifact_type="invalid_type",
                size_bytes=1024,
                content_preview="Test",
            )


class TestSessionState:
    """Tests for SessionState schema."""

    def test_default_state(self):
        """Default state has expected defaults."""
        state = SessionState(thread_id="test-123")
        assert state.diagnostic_complete is False
        assert state.diagnostic_answers == []
        assert state.scorecard is None
        assert state.artifacts == []
        assert state.voice_profile is None

    def test_state_with_data(self, sample_scorecard):
        """State with full data."""
        state = SessionState(
            thread_id="test-123",
            diagnostic_complete=True,
            diagnostic_answers=[
                DiagnosticAnswer(question_id="q1", selected_option="SMB"),
            ],
            scorecard=EscalatorScorecard(**sample_scorecard),
            artifacts=[
                ArtifactMetadata(
                    filename="scorecard.json",
                    artifact_type="scorecard",
                    size_bytes=512,
                    content_preview='{"level": 3}',
                )
            ],
        )
        assert state.diagnostic_complete is True
        assert len(state.diagnostic_answers) == 1
        assert state.scorecard.level == 3
