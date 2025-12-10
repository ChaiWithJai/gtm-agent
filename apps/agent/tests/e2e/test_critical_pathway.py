"""E2E tests for the critical pathway: URL → Diagnostic → Scorecard → Artifacts.

This test validates the complete user journey from entering a product URL
through to generating personalized GTM artifacts.
"""

import os
import pytest
import httpx
import json
from typing import Generator


# API URL - uses the FastAPI server (not LangGraph directly)
API_BASE = os.environ.get("GTM_API_URL", "http://localhost:8000")


def parse_sse_events(response_text: str) -> list[dict]:
    """Parse SSE events from response text."""
    events = []
    for line in response_text.split("\n"):
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                continue
    return events


@pytest.fixture
def api_client() -> Generator[httpx.Client, None, None]:
    """Create HTTP client for API tests."""
    with httpx.Client(base_url=API_BASE, timeout=120.0) as client:
        yield client


@pytest.mark.e2e
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Requires ANTHROPIC_API_KEY"
)
class TestCriticalPathway:
    """E2E tests for the complete critical pathway.

    Critical pathway:
    1. User enters product URL
    2. System analyzes website, shows company context
    3. User answers 3 diagnostic questions
    4. System shows "Would you like to generate?" prompt
    5. User clicks "Yes"
    6. System shows scorecard + generates artifacts
    """

    def test_api_health(self, api_client: httpx.Client):
        """Verify API is running."""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "gtm-agent"

    def test_start_session_with_url(self, api_client: httpx.Client):
        """Start session with product URL returns company context and first question."""
        response = api_client.post(
            "/api/agent/start",
            json={"product_url": "https://chaiwithjai.com"}
        )
        assert response.status_code == 200
        data = response.json()

        # Should have thread_id
        assert "thread_id" in data
        assert data["thread_id"]

        # Should have messages with company context
        assert "messages" in data
        assert len(data["messages"]) >= 1

        # First message should contain company analysis
        first_msg = data["messages"][0]
        assert "content" in first_msg
        assert "analyzing" in first_msg["content"].lower() or "jai" in first_msg["content"].lower()

        # Should have first question options
        last_msg = data["messages"][-1]
        assert "options" in last_msg
        assert len(last_msg["options"]) >= 3

    def test_start_session_with_description(self, api_client: httpx.Client):
        """Start session with product description returns first question."""
        response = api_client.post(
            "/api/agent/start",
            json={"product_description": "We build AI tools for founders"}
        )
        assert response.status_code == 200
        data = response.json()

        assert "thread_id" in data
        assert "messages" in data

        # Should have question with options
        last_msg = data["messages"][-1]
        assert "options" in last_msg
        assert len(last_msg["options"]) >= 3

    def test_complete_diagnostic_flow(self, api_client: httpx.Client):
        """Complete diagnostic returns scorecard prompt (but not scorecard itself)."""
        # Start session
        start_resp = api_client.post(
            "/api/agent/start",
            json={"product_url": "https://chaiwithjai.com"}
        )
        assert start_resp.status_code == 200
        thread_id = start_resp.json()["thread_id"]

        # Answer questions 1, 2, 3
        answers = [
            "SMB Founders (1-50 employees)",
            "Crystal clear - customers describe it to us",
            "Revenue from target ICP",
        ]

        for i, answer in enumerate(answers):
            response = api_client.post(
                "/api/agent/message",
                json={
                    "thread_id": thread_id,
                    "message": answer,
                    "selected_option": answer,
                }
            )
            assert response.status_code == 200

            # Parse SSE events
            events = parse_sse_events(response.text)

            if i < 2:
                # Questions 1 & 2: should get next question
                options_events = [e for e in events if e.get("event") == "options"]
                assert len(options_events) >= 1, f"Question {i+1}: No options event found"
            else:
                # Question 3: should get artifact prompt, NO scorecard yet
                message_events = [e for e in events if e.get("event") == "message"]
                assert len(message_events) >= 1, "No message event after Q3"

                # Message should ask about generating artifacts
                last_message = message_events[-1]["content"]
                assert "level" in last_message.lower() or "artifacts" in last_message.lower()

                # Should have Yes/No options
                options_events = [e for e in events if e.get("event") == "options"]
                assert len(options_events) >= 1
                options = options_events[-1]["options"]
                assert any("yes" in o.lower() or "build" in o.lower() for o in options)

                # Should NOT have scorecard event yet (UX fix)
                scorecard_events = [e for e in events if e.get("event") == "scorecard"]
                assert len(scorecard_events) == 0, "Scorecard should not appear before user confirms"

    def test_artifact_generation_after_confirmation(self, api_client: httpx.Client):
        """After confirming, scorecard and artifacts are generated."""
        # Start session
        start_resp = api_client.post(
            "/api/agent/start",
            json={"product_url": "https://chaiwithjai.com"}
        )
        thread_id = start_resp.json()["thread_id"]

        # Answer all 3 questions
        answers = [
            "SMB Founders (1-50 employees)",
            "Crystal clear - customers describe it to us",
            "Revenue from target ICP",
        ]

        for answer in answers:
            api_client.post(
                "/api/agent/message",
                json={
                    "thread_id": thread_id,
                    "message": answer,
                    "selected_option": answer,
                }
            )

        # Confirm artifact generation
        response = api_client.post(
            "/api/agent/message",
            json={
                "thread_id": thread_id,
                "message": "Yes, build my artifacts",
                "selected_option": "Yes, build my artifacts",
            }
        )
        assert response.status_code == 200

        events = parse_sse_events(response.text)

        # Should have scorecard event NOW
        scorecard_events = [e for e in events if e.get("event") == "scorecard"]
        assert len(scorecard_events) >= 1, "Scorecard should appear after confirmation"

        scorecard = scorecard_events[0]["scorecard"]
        assert "level" in scorecard
        assert 1 <= scorecard["level"] <= 5
        assert "gaps" in scorecard
        assert "recommendations" in scorecard

        # Should have artifact events
        artifact_events = [e for e in events if e.get("event") == "artifact"]
        assert len(artifact_events) >= 2, f"Expected at least 2 artifacts, got {len(artifact_events)}"

        # Check artifact filenames
        filenames = [e["filename"] for e in artifact_events]
        assert any("scorecard" in f.lower() for f in filenames), "Missing scorecard artifact"

    def test_artifact_download(self, api_client: httpx.Client):
        """Generated artifacts can be downloaded."""
        # Start session and complete flow
        start_resp = api_client.post(
            "/api/agent/start",
            json={"product_url": "https://chaiwithjai.com"}
        )
        thread_id = start_resp.json()["thread_id"]

        # Quick flow through
        for answer in ["SMB Founders (1-50 employees)", "Crystal clear - customers describe it to us", "Revenue from target ICP"]:
            api_client.post("/api/agent/message", json={"thread_id": thread_id, "message": answer, "selected_option": answer})

        # Confirm and generate
        response = api_client.post(
            "/api/agent/message",
            json={"thread_id": thread_id, "message": "Yes, build my artifacts", "selected_option": "Yes, build my artifacts"}
        )

        events = parse_sse_events(response.text)
        artifact_events = [e for e in events if e.get("event") == "artifact"]

        # Download first artifact
        if artifact_events:
            filename = artifact_events[0]["filename"]
            download_resp = api_client.get(f"/api/artifacts/{thread_id}/{filename}")
            assert download_resp.status_code == 200
            assert len(download_resp.content) > 0

    def test_session_state_persistence(self, api_client: httpx.Client):
        """Session state is maintained across requests."""
        # Start session
        start_resp = api_client.post(
            "/api/agent/start",
            json={"product_description": "We build AI tools"}
        )
        thread_id = start_resp.json()["thread_id"]

        # Get session state
        state_resp = api_client.get(f"/api/session/{thread_id}")
        assert state_resp.status_code == 200
        state = state_resp.json()

        assert state["thread_id"] == thread_id
        assert "current_question" in state
        assert "messages" in state


@pytest.mark.e2e
class TestCriticalPathwayEdgeCases:
    """Edge cases for the critical pathway."""

    def test_url_normalization(self, api_client: httpx.Client):
        """Various URL formats are handled correctly."""
        # Test without https://
        response = api_client.post(
            "/api/agent/start",
            json={"product_url": "chaiwithjai.com"}
        )
        # Should either succeed or return clear error
        assert response.status_code in [200, 400, 422]

    def test_empty_product_url(self, api_client: httpx.Client):
        """Empty URL is rejected gracefully."""
        response = api_client.post(
            "/api/agent/start",
            json={"product_url": ""}
        )
        # Should either handle gracefully or return error
        assert response.status_code in [200, 400, 422]

    def test_invalid_thread_id(self, api_client: httpx.Client):
        """Invalid thread ID returns appropriate error."""
        response = api_client.post(
            "/api/agent/message",
            json={
                "thread_id": "nonexistent-thread-id",
                "message": "Hello",
            }
        )
        assert response.status_code in [400, 404, 422]

    def test_decline_artifact_generation(self, api_client: httpx.Client):
        """User can decline artifact generation."""
        # Start and answer questions
        start_resp = api_client.post(
            "/api/agent/start",
            json={"product_description": "We build AI tools"}
        )
        thread_id = start_resp.json()["thread_id"]

        for answer in ["SMB Founders (1-50 employees)", "Crystal clear - customers describe it to us", "Revenue from target ICP"]:
            api_client.post("/api/agent/message", json={"thread_id": thread_id, "message": answer, "selected_option": answer})

        # Decline
        response = api_client.post(
            "/api/agent/message",
            json={"thread_id": thread_id, "message": "Not now", "selected_option": "Not now"}
        )
        assert response.status_code == 200

        events = parse_sse_events(response.text)

        # Should NOT generate artifacts
        artifact_events = [e for e in events if e.get("event") == "artifact"]
        assert len(artifact_events) == 0, "Artifacts should not be generated when user declines"
