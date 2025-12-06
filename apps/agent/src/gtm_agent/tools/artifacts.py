"""Artifact writing tools for GTM document generation."""

import re
from typing import Literal

from langchain_core.tools import tool

from gtm_agent.schemas import ArtifactMetadata

# Maximum artifact size (100KB)
MAX_ARTIFACT_SIZE = 100 * 1024

# Valid artifact types
ArtifactType = Literal["scorecard", "narrative", "emails", "linkedin", "action_plan"]

# Default filename patterns for each artifact type
ARTIFACT_FILENAMES = {
    "scorecard": "gtm-scorecard.json",
    "narrative": "gtm-narrative.md",
    "emails": "cold-email-sequence.md",
    "linkedin": "linkedin-posts.md",
    "action_plan": "action-plan.md",
}


def _validate_filename(filename: str) -> bool:
    """Validate filename for security.

    Args:
        filename: Filename to validate

    Returns:
        True if valid, False otherwise
    """
    # Check for path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        return False

    # Check for valid characters
    if not re.match(r"^[\w\-\.]+$", filename):
        return False

    # Check length
    if len(filename) > 100:
        return False

    return True


def _truncate_preview(content: str, max_length: int = 200) -> str:
    """Truncate content for preview.

    Args:
        content: Content to truncate
        max_length: Maximum preview length

    Returns:
        Truncated content with ellipsis if needed
    """
    if len(content) <= max_length:
        return content
    return content[: max_length - 3] + "..."


# Global artifact storage (in production, this would be in state)
_artifact_storage: dict[str, str] = {}


def get_artifact_storage() -> dict[str, str]:
    """Get the current artifact storage.

    Returns:
        Dict mapping filenames to content
    """
    return _artifact_storage.copy()


def clear_artifact_storage() -> None:
    """Clear the artifact storage."""
    global _artifact_storage
    _artifact_storage = {}


@tool
def write_artifact(
    filename: str,
    content: str,
    artifact_type: ArtifactType,
) -> dict:
    """Write artifact to session state.

    This tool saves a generated artifact (scorecard, narrative, emails,
    linkedin posts, or action plan) to the session. The artifact can then
    be downloaded by the user.

    Args:
        filename: Name for the artifact file (e.g., "gtm-narrative.md")
        content: Full content to write
        artifact_type: Type of artifact being written (scorecard, narrative, emails, linkedin, action_plan)

    Returns:
        ArtifactMetadata dict with filename, type, size, and preview

    Raises:
        ValueError: If filename is invalid, content too large, or artifact_type invalid
    """
    # Validate filename
    if not _validate_filename(filename):
        raise ValueError(
            f"Invalid filename: {filename}. "
            "Filenames must be alphanumeric with dashes, underscores, and dots only."
        )

    # Validate artifact type
    valid_types = ["scorecard", "narrative", "emails", "linkedin", "action_plan"]
    if artifact_type not in valid_types:
        raise ValueError(f"Invalid artifact_type: {artifact_type}. Must be one of: {valid_types}")

    # Validate content size
    content_bytes = len(content.encode("utf-8"))
    if content_bytes > MAX_ARTIFACT_SIZE:
        raise ValueError(
            f"Content too large: {content_bytes} bytes. Maximum is {MAX_ARTIFACT_SIZE} bytes."
        )

    # Store the artifact
    global _artifact_storage
    _artifact_storage[filename] = content

    # Create metadata
    metadata = ArtifactMetadata(
        filename=filename,
        artifact_type=artifact_type,
        size_bytes=content_bytes,
        content_preview=_truncate_preview(content),
    )

    return metadata.model_dump()


def get_default_filename(artifact_type: ArtifactType) -> str:
    """Get the default filename for an artifact type.

    Args:
        artifact_type: The type of artifact

    Returns:
        Default filename for that type
    """
    return ARTIFACT_FILENAMES.get(artifact_type, f"{artifact_type}.md")
