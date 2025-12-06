"""Pytest fixtures for GTM Agent tests."""

import os
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a clean temporary directory per test."""
    return tmp_path


@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration for recording/replaying HTTP interactions."""
    return {
        "filter_headers": ["authorization", "x-api-key", "anthropic-api-key"],
        "record_mode": "once",
        "cassette_library_dir": str(Path(__file__).parent / "cassettes"),
        "decode_compressed_response": True,
    }


@pytest.fixture
def sample_diagnostic_answers():
    """Sample diagnostic answers for testing."""
    return {
        "q1_icp": "SMB Founders (<50 employees)",
        "q2_problem": "Crystal clear - customers describe it the same way",
        "q3_validation": "Paying customers who came organically",
    }


@pytest.fixture
def sample_scorecard():
    """Sample scorecard for testing."""
    return {
        "level": 3,
        "scores": {"l1": 85, "l2": 70, "l3": 60, "l4": 30, "l5": 0},
        "gaps": ["Channel strategy undefined", "No repeatable acquisition motion"],
        "recommendations": [
            "Document where your best customers came from",
            "Test 2-3 acquisition channels with small budget",
        ],
    }


@pytest.fixture
def mock_agent_config():
    """Configuration for mock agent in tests."""
    return {"configurable": {"thread_id": "test-thread-1"}}


# Environment setup for tests
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    # Disable LangSmith tracing for unit tests unless explicitly enabled
    if os.environ.get("LANGSMITH_TEST_TRACKING") != "true":
        monkeypatch.setenv("LANGSMITH_TRACING_V2", "false")
