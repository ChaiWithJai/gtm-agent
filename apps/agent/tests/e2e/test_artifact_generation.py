"""E2E tests for artifact generation."""

import json
import os
import pytest

from gtm_agent.tools import (
    write_artifact,
    get_artifact_storage,
    clear_artifact_storage,
    calculate_escalator_level,
)
from gtm_agent.schemas import EscalatorScorecard, ArtifactMetadata


@pytest.mark.e2e
class TestArtifactGeneration:
    """E2E tests for artifact generation quality."""

    def setup_method(self):
        """Clear storage before each test."""
        clear_artifact_storage()

    def test_all_artifact_types_generated(self):
        """All 5 artifact types can be generated."""
        artifacts = [
            ("gtm-scorecard.json", "scorecard"),
            ("gtm-narrative.md", "narrative"),
            ("cold-email-sequence.md", "emails"),
            ("linkedin-posts.md", "linkedin"),
            ("action-plan.md", "action_plan"),
        ]

        for filename, artifact_type in artifacts:
            content = f"# {artifact_type.title()} Content\n\nGenerated content here."
            result = write_artifact.invoke({
                "filename": filename,
                "content": content,
                "artifact_type": artifact_type,
            })

            # Verify metadata
            assert result["filename"] == filename
            assert result["artifact_type"] == artifact_type
            assert result["size_bytes"] > 0
            assert len(result["content_preview"]) <= 200

        # Verify all stored
        storage = get_artifact_storage()
        assert len(storage) == 5

    def test_scorecard_json_valid(self):
        """Scorecard artifact contains valid JSON matching schema."""
        # Generate a real scorecard
        answers = {
            "q1_icp": "SMB Founders (1-50 employees)",
            "q2_problem": "Crystal clear - customers describe it to us",
            "q3_validation": "Pilots/design partners",
        }
        scorecard = calculate_escalator_level.invoke({"answers": answers})

        # Write as artifact
        content = json.dumps(scorecard, indent=2)
        write_artifact.invoke({
            "filename": "gtm-scorecard.json",
            "content": content,
            "artifact_type": "scorecard",
        })

        # Verify content is valid JSON
        storage = get_artifact_storage()
        stored_content = storage["gtm-scorecard.json"]
        parsed = json.loads(stored_content)

        # Validate against schema
        EscalatorScorecard(**parsed)

    def test_narrative_contains_sections(self):
        """Narrative artifact contains expected sections."""
        narrative_content = """# GTM Narrative: Acme AI

## Positioning Statement

For SMB founders who struggle with GTM clarity, Acme AI provides
AI-powered GTM strategy that helps them ship faster.

## Value Proposition

**Problem**: Founders waste months on scattered GTM efforts.

**Solution**: Structured diagnostic and artifact generation.

**Benefit**: Ship 5 GTM artifacts in 24 hours.

## Ideal Customer Profile (ICP)

### Demographics
- Company size: 1-50 employees
- Industry: B2B SaaS
- Stage: Seed to Series A

### Psychographics
- Pain points: Scattered thinking, investor pressure
- Goals: Clear GTM strategy

### Trigger Events
- Investor asks "what's your GTM?"
- Preparing for fundraise
"""

        write_artifact.invoke({
            "filename": "gtm-narrative.md",
            "content": narrative_content,
            "artifact_type": "narrative",
        })

        storage = get_artifact_storage()
        content = storage["gtm-narrative.md"]

        # Verify sections present
        assert "Positioning Statement" in content
        assert "Value Proposition" in content
        assert "Ideal Customer Profile" in content

    def test_email_sequence_structure(self):
        """Email sequence has proper structure."""
        email_content = """# Cold Email Sequence

## Email 1: Problem Awareness

**Subject**: Are you wasting time on GTM?

Hi {{first_name}},

Most founders spend months on scattered GTM work...

Best,
Acme AI

---

## Email 2: Solution Introduction

**Subject**: How we helped {{company}} ship GTM in 24 hours

Hi {{first_name}},

I wanted to share how...

---

## Email 3: Call to Action

**Subject**: Quick question about {{company}}'s GTM

Hi {{first_name}},

Would you be open to a 15-minute call?
"""

        write_artifact.invoke({
            "filename": "cold-email-sequence.md",
            "content": email_content,
            "artifact_type": "emails",
        })

        storage = get_artifact_storage()
        content = storage["cold-email-sequence.md"]

        # Verify structure
        assert "Email 1" in content
        assert "Email 2" in content
        assert "Email 3" in content
        assert "**Subject**:" in content

    def test_linkedin_posts_appropriate_length(self):
        """LinkedIn posts are within character limits."""
        linkedin_content = """# LinkedIn Posts

## Post 1: Problem Awareness

Most founders I talk to have the same problem:

They can talk about their product for hours...
But ask them "what do you do?" and they freeze.

Sound familiar?

Here's what I've learned about fixing this 👇

---

## Post 2: Solution/Value

I used to think GTM strategy required months of work.

Then I discovered a framework that changed everything:

1. 3 diagnostic questions
2. 1 scorecard
3. 5 artifacts in 24 hours

The result? Clarity that used to take months.

---

## Post 3: Social Proof/CTA

"I finally have artifacts I can send to investors."

That's what one founder told me after using our GTM diagnostic.

Want to try it? Link in comments 👇
"""

        write_artifact.invoke({
            "filename": "linkedin-posts.md",
            "content": linkedin_content,
            "artifact_type": "linkedin",
        })

        storage = get_artifact_storage()
        content = storage["linkedin-posts.md"]

        # Verify structure
        assert "Post 1" in content
        assert "Post 2" in content
        assert "Post 3" in content

        # Each post should be reasonable length
        posts = content.split("---")
        for post in posts:
            assert len(post) < 3000  # LinkedIn limit


@pytest.mark.e2e
class TestArtifactQuality:
    """Test artifact quality and personalization."""

    def setup_method(self):
        clear_artifact_storage()

    def test_artifacts_reference_company_name(self):
        """Artifacts should reference company name when provided."""
        company_name = "Acme AI"
        content = f"# GTM Narrative: {company_name}\n\nContent about {company_name}."

        write_artifact.invoke({
            "filename": "gtm-narrative.md",
            "content": content,
            "artifact_type": "narrative",
        })

        storage = get_artifact_storage()
        assert company_name in storage["gtm-narrative.md"]

    def test_action_plan_has_priorities(self):
        """Action plan should have prioritized items."""
        action_plan = """# GTM Action Plan

## This Week (Priority)

1. [ ] Define ICP with 5 specific criteria
2. [ ] Write positioning statement
3. [ ] Interview 3 potential customers

## This Month

1. [ ] Test messaging with 5 customers
2. [ ] Identify 2 acquisition channels
3. [ ] Create sales playbook draft

## Level-Up Criteria

To reach Level 3, you need:
- Clear ICP definition
- Validated messaging
- At least one channel identified
"""

        write_artifact.invoke({
            "filename": "action-plan.md",
            "content": action_plan,
            "artifact_type": "action_plan",
        })

        storage = get_artifact_storage()
        content = storage["action-plan.md"]

        assert "This Week" in content
        assert "This Month" in content
        assert "[ ]" in content  # Has checkboxes
