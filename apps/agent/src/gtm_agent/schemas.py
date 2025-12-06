"""Pydantic schemas for GTM Deep Agent."""

from enum import IntEnum
from typing import Literal

from pydantic import BaseModel, Field


class GTMLevel(IntEnum):
    """GTM Escalator levels 1-5."""

    PROBLEM_SOLUTION = 1
    MESSAGING_CLARITY = 2
    ICP_DEFINITION = 3
    CHANNEL_FIT = 4
    SCALE_READY = 5


class DiagnosticAnswer(BaseModel):
    """Single diagnostic question answer."""

    question_id: str = Field(description="Unique question identifier")
    selected_option: str = Field(description="User's selected button option")
    confidence: float = Field(ge=0, le=1, default=1.0)


class EscalatorScorecard(BaseModel):
    """GTM Escalator Scorecard output."""

    level: int = Field(ge=1, le=5, description="Current GTM level (1-5)")
    scores: dict[str, int] = Field(
        description="Score per level (0-100)",
        examples=[{"l1": 80, "l2": 40, "l3": 20, "l4": 0, "l5": 0}],
    )
    gaps: list[str] = Field(
        description="Identified gaps at current level",
        examples=[["No ICP definition", "No positioning doc"]],
    )
    recommendations: list[str] = Field(description="Prioritized next actions")


class ArtifactMetadata(BaseModel):
    """Metadata for generated artifact."""

    filename: str
    artifact_type: Literal["scorecard", "narrative", "emails", "linkedin", "action_plan"]
    size_bytes: int
    content_preview: str = Field(max_length=200)


class DiagnosticQuestion(BaseModel):
    """A diagnostic question with button options."""

    question_id: str = Field(description="Unique question identifier")
    question_text: str = Field(description="The question to ask the user")
    options: list[str] = Field(description="Button options for the user to select")
    phase: Literal["icp", "messaging", "validation"] = Field(
        description="Which GTM phase this question assesses"
    )


class SessionState(BaseModel):
    """Agent session state for checkpointing."""

    thread_id: str
    diagnostic_complete: bool = False
    diagnostic_answers: list[DiagnosticAnswer] = Field(default_factory=list)
    scorecard: EscalatorScorecard | None = None
    artifacts: list[ArtifactMetadata] = Field(default_factory=list)
    voice_profile: dict | None = None
