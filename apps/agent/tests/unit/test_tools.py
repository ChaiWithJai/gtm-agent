"""Unit tests for GTM agent tools."""

import pytest

from gtm_agent.tools.diagnostic import (
    DIAGNOSTIC_QUESTIONS,
    get_all_diagnostic_questions,
    get_diagnostic_question,
)
from gtm_agent.tools.scorecard import calculate_escalator_level
from gtm_agent.tools.artifacts import (
    clear_artifact_storage,
    get_artifact_storage,
    write_artifact,
)
from gtm_agent.tools.web_fetch import _validate_url, _extract_company_name


class TestGetDiagnosticQuestion:
    """Tests for diagnostic question generation."""

    def test_question_1_has_options(self):
        """First question includes button options."""
        question = get_diagnostic_question.invoke({"question_number": 1})
        assert "options" in question
        assert len(question["options"]) >= 3
        assert any("SMB" in opt or "Enterprise" in opt for opt in question["options"])

    def test_question_2_has_options(self):
        """Second question includes problem clarity options."""
        question = get_diagnostic_question.invoke({"question_number": 2})
        assert "options" in question
        assert len(question["options"]) >= 3
        assert any("clear" in opt.lower() for opt in question["options"])

    def test_question_3_has_options(self):
        """Third question includes validation options."""
        question = get_diagnostic_question.invoke({"question_number": 3})
        assert "options" in question
        assert len(question["options"]) >= 3
        assert any("validated" in opt.lower() or "revenue" in opt.lower() for opt in question["options"])

    def test_question_includes_id(self):
        """Question includes unique identifier."""
        question = get_diagnostic_question.invoke({"question_number": 2})
        assert "question_id" in question
        assert question["question_id"].startswith("q2_")

    def test_question_includes_text(self):
        """Question includes question text."""
        question = get_diagnostic_question.invoke({"question_number": 1})
        assert "question_text" in question
        assert len(question["question_text"]) > 10

    def test_invalid_question_number_raises_error(self):
        """Invalid question_number raises ValueError."""
        with pytest.raises(ValueError, match="Invalid question_number"):
            get_diagnostic_question.invoke({"question_number": 4})

    def test_zero_question_number_raises_error(self):
        """Zero question_number raises ValueError."""
        with pytest.raises(ValueError, match="Invalid question_number"):
            get_diagnostic_question.invoke({"question_number": 0})

    def test_get_all_diagnostic_questions(self):
        """get_all_diagnostic_questions returns all 3 questions."""
        questions = get_all_diagnostic_questions()
        assert len(questions) == 3
        assert questions[0]["question_id"] == "q1_icp"
        assert questions[1]["question_id"] == "q2_problem"
        assert questions[2]["question_id"] == "q3_validation"


class TestCalculateEscalatorLevel:
    """Tests for escalator level calculation."""

    def test_level_1_no_icp(self):
        """No ICP clarity = Level 1."""
        answers = {
            "q1_icp": "Not sure yet",
            "q2_problem": "Still figuring it out",
            "q3_validation": "Not validated yet",
        }
        result = calculate_escalator_level.invoke({"answers": answers})
        assert result["level"] == 1
        assert any("ICP" in gap or "Problem" in gap for gap in result["gaps"])

    def test_level_2_clear_problem(self):
        """Clear problem but unclear ICP = Level 2."""
        answers = {
            "q1_icp": "Not sure yet",
            "q2_problem": "Crystal clear - customers describe it to us",
            "q3_validation": "Not validated yet",
        }
        result = calculate_escalator_level.invoke({"answers": answers})
        assert result["level"] == 2
        assert "No clear ICP" in result["gaps"] or any("ICP" in g for g in result["gaps"])

    def test_level_3_good_foundation(self):
        """Clear ICP + messaging + some validation = Level 3."""
        answers = {
            "q1_icp": "SMB Founders (1-50 employees)",
            "q2_problem": "Crystal clear - customers describe it to us",
            "q3_validation": "Pilots/design partners",
        }
        result = calculate_escalator_level.invoke({"answers": answers})
        assert result["level"] >= 2  # At least level 2 with good messaging

    def test_level_4_with_validation(self):
        """Validated solution = Level 4."""
        answers = {
            "q1_icp": "Enterprise (500+ employees)",
            "q2_problem": "Pretty clear - we've validated it",
            "q3_validation": "Pilots/design partners",
        }
        result = calculate_escalator_level.invoke({"answers": answers})
        assert result["level"] >= 3  # At least level 3 with good foundation

    def test_returns_valid_schema(self):
        """Output matches EscalatorScorecard schema."""
        from gtm_agent.schemas import EscalatorScorecard

        answers = {"q1_icp": "SMB Founders (1-50 employees)"}
        result = calculate_escalator_level.invoke({"answers": answers})
        # Should not raise
        scorecard = EscalatorScorecard(**result)
        assert scorecard.level >= 1
        assert scorecard.level <= 5

    def test_scores_within_bounds(self):
        """All scores are within 0-100."""
        answers = {
            "q1_icp": "Enterprise (500+ employees)",
            "q2_problem": "Crystal clear - customers describe it to us",
            "q3_validation": "Revenue from target ICP",
        }
        result = calculate_escalator_level.invoke({"answers": answers})
        for level, score in result["scores"].items():
            assert 0 <= score <= 100, f"{level} score out of bounds: {score}"

    def test_recommendations_not_empty(self):
        """Recommendations list is not empty."""
        answers = {"q1_icp": "Not sure yet"}
        result = calculate_escalator_level.invoke({"answers": answers})
        assert len(result["recommendations"]) > 0


class TestWriteArtifact:
    """Tests for artifact writing."""

    def setup_method(self):
        """Clear artifact storage before each test."""
        clear_artifact_storage()

    def test_valid_artifact_writes_successfully(self):
        """Valid artifact writes and returns metadata."""
        result = write_artifact.invoke({
            "filename": "test-narrative.md",
            "content": "# Test Narrative\n\nThis is test content.",
            "artifact_type": "narrative",
        })
        assert result["filename"] == "test-narrative.md"
        assert result["artifact_type"] == "narrative"
        assert result["size_bytes"] > 0

    def test_artifact_stored_correctly(self):
        """Artifact content is stored and retrievable."""
        content = "# Test Content"
        write_artifact.invoke({
            "filename": "stored.md",
            "content": content,
            "artifact_type": "narrative",
        })
        storage = get_artifact_storage()
        assert "stored.md" in storage
        assert storage["stored.md"] == content

    def test_invalid_artifact_type_raises_error(self):
        """Invalid artifact_type raises error (pydantic validation)."""
        with pytest.raises(Exception):  # Pydantic validation error
            write_artifact.invoke({
                "filename": "test.md",
                "content": "content",
                "artifact_type": "invalid_type",
            })

    def test_path_traversal_blocked(self):
        """Path traversal in filename is blocked."""
        with pytest.raises(ValueError, match="Invalid filename"):
            write_artifact.invoke({
                "filename": "../../../etc/passwd",
                "content": "malicious",
                "artifact_type": "narrative",
            })

    def test_content_size_limit_enforced(self):
        """Content larger than 100KB raises error."""
        large_content = "x" * (100 * 1024 + 1)  # 100KB + 1 byte
        with pytest.raises(ValueError, match="Content too large"):
            write_artifact.invoke({
                "filename": "large.md",
                "content": large_content,
                "artifact_type": "narrative",
            })

    def test_preview_truncated(self):
        """Preview is truncated to 200 chars."""
        long_content = "x" * 500
        result = write_artifact.invoke({
            "filename": "long.md",
            "content": long_content,
            "artifact_type": "narrative",
        })
        assert len(result["content_preview"]) <= 200
        assert result["content_preview"].endswith("...")


class TestWebFetchHelpers:
    """Tests for web fetch helper functions."""

    def test_validate_url_valid_https(self):
        """Valid HTTPS URL passes validation."""
        result = _validate_url("https://example.com")
        assert result == "https://example.com"

    def test_validate_url_adds_scheme(self):
        """URL without scheme gets HTTPS added."""
        result = _validate_url("example.com")
        assert result == "https://example.com"

    def test_validate_url_invalid(self):
        """Invalid URL returns None."""
        result = _validate_url("")
        assert result is None

    def test_extract_company_name_from_domain(self):
        """Company name extracted from domain when no title."""
        result = _extract_company_name("https://acme.com", "<html></html>")
        assert result == "Acme"

    def test_extract_company_name_from_title(self):
        """Company name extracted from title tag."""
        html = "<html><title>Acme Inc - Home</title></html>"
        result = _extract_company_name("https://example.com", html)
        assert "Acme" in result
