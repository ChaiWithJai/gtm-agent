"""FastAPI endpoints for GTM Deep Agent."""

import json
import uuid
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from gtm_agent.tools import (
    get_diagnostic_question,
    calculate_escalator_level,
    write_artifact,
    get_artifact_storage,
    clear_artifact_storage,
)

app = FastAPI(
    title="GTM Deep Agent API",
    description="API for GTM diagnostic and artifact generation",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (use Redis/DB in production)
sessions: dict[str, dict] = {}


# Request/Response models
class StartInput(BaseModel):
    """Input for starting a new session."""

    product_url: str | None = None
    product_description: str | None = None


class MessageInput(BaseModel):
    """Input for sending a message."""

    thread_id: str
    message: str
    selected_option: str | None = None


class ApprovalInput(BaseModel):
    """Input for HITL approval."""

    thread_id: str
    tool_call_id: str
    decision: str  # "approve" | "edit" | "reject"


class SessionState(BaseModel):
    """Session state response."""

    thread_id: str
    messages: list[dict]
    diagnostic_complete: bool
    current_question: int
    scorecard: dict | None
    artifacts: list[str]


# Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "gtm-agent"}


@app.post("/api/agent/start")
async def start_session(input: StartInput) -> dict:
    """Initialize new GTM session.

    Args:
        input: Product URL or description

    Returns:
        Thread ID and initial messages
    """
    if not input.product_url and not input.product_description:
        raise HTTPException(
            status_code=400,
            detail="Provide either product_url or product_description",
        )

    thread_id = str(uuid.uuid4())

    # Initialize session state
    sessions[thread_id] = {
        "messages": [],
        "diagnostic_complete": False,
        "current_question": 0,
        "answers": {},
        "scorecard": None,
        "artifacts": [],
        "product_url": input.product_url,
        "product_description": input.product_description,
    }

    # Get first diagnostic question
    question = get_diagnostic_question.invoke({"question_number": 1})
    sessions[thread_id]["current_question"] = 1

    # Build initial message
    if input.product_url:
        intro = f"Thanks for sharing your product URL: {input.product_url}"
    else:
        intro = f"Thanks for describing your product: {input.product_description[:100]}..."

    messages = [
        {"role": "assistant", "content": intro},
        {
            "role": "assistant",
            "content": question["question_text"],
            "options": question["options"],
            "question_id": question["question_id"],
        },
    ]
    sessions[thread_id]["messages"] = messages

    return {"thread_id": thread_id, "messages": messages}


@app.post("/api/agent/message")
async def send_message(input: MessageInput) -> StreamingResponse:
    """Send user response, get agent response via SSE.

    Args:
        input: Thread ID and user message/selection

    Returns:
        SSE stream of events
    """
    if input.thread_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[input.thread_id]

    async def event_stream() -> AsyncGenerator[str, None]:
        # Record user's answer
        message_content = input.selected_option or input.message
        current_q = session["current_question"]

        if current_q > 0 and current_q <= 3:
            question = get_diagnostic_question.invoke({"question_number": current_q})
            session["answers"][question["question_id"]] = message_content

            # Add user message
            session["messages"].append({"role": "user", "content": message_content})
            yield f"data: {json.dumps({'event': 'user_message', 'content': message_content})}\n\n"

        if current_q < 3:
            # Get next question
            next_q = current_q + 1
            question = get_diagnostic_question.invoke({"question_number": next_q})
            session["current_question"] = next_q

            response = {
                "role": "assistant",
                "content": question["question_text"],
                "options": question["options"],
                "question_id": question["question_id"],
            }
            session["messages"].append(response)

            yield f"data: {json.dumps({'event': 'message', 'content': question['question_text']})}\n\n"
            yield f"data: {json.dumps({'event': 'options', 'options': question['options']})}\n\n"

        elif current_q == 3 and not session["diagnostic_complete"]:
            # Calculate scorecard
            scorecard = calculate_escalator_level.invoke({"answers": session["answers"]})
            session["scorecard"] = scorecard
            session["diagnostic_complete"] = True

            yield f"data: {json.dumps({'event': 'scorecard', 'scorecard': scorecard})}\n\n"

            # Save scorecard artifact
            write_artifact.invoke({
                "filename": "gtm-scorecard.json",
                "content": json.dumps(scorecard, indent=2),
                "artifact_type": "scorecard",
            })
            session["artifacts"].append("gtm-scorecard.json")

            yield f"data: {json.dumps({'event': 'artifact', 'filename': 'gtm-scorecard.json'})}\n\n"

            # Prompt for artifact generation
            response = {
                "role": "assistant",
                "content": f"Based on your answers, you're at GTM Level {scorecard['level']}. Would you like me to generate your GTM artifacts?",
                "options": ["Yes, build my artifacts", "Not now"],
            }
            session["messages"].append(response)

            yield f"data: {json.dumps({'event': 'message', 'content': response['content']})}\n\n"
            yield f"data: {json.dumps({'event': 'options', 'options': response['options']})}\n\n"

        elif session["diagnostic_complete"] and "build" in message_content.lower():
            # Generate artifacts
            yield f"data: {json.dumps({'event': 'status', 'content': 'Generating artifacts...'})}\n\n"

            artifacts = [
                ("gtm-narrative.md", "# GTM Narrative\n\nYour strategic narrative...", "narrative"),
                ("cold-email-sequence.md", "# Cold Email Sequence\n\n## Email 1...", "emails"),
                ("linkedin-posts.md", "# LinkedIn Posts\n\n## Post 1...", "linkedin"),
                ("action-plan.md", "# Action Plan\n\n## This Week...", "action_plan"),
            ]

            for filename, content, artifact_type in artifacts:
                write_artifact.invoke({
                    "filename": filename,
                    "content": content,
                    "artifact_type": artifact_type,
                })
                session["artifacts"].append(filename)
                yield f"data: {json.dumps({'event': 'artifact', 'filename': filename})}\n\n"

            response = {
                "role": "assistant",
                "content": "I've generated all 5 GTM artifacts for you. You can download them below.",
            }
            session["messages"].append(response)
            yield f"data: {json.dumps({'event': 'message', 'content': response['content']})}\n\n"

        yield f"data: {json.dumps({'event': 'done'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/agent/state/{thread_id}")
async def get_state(thread_id: str) -> SessionState:
    """Get session state for UI hydration.

    Args:
        thread_id: Session thread ID

    Returns:
        Current session state
    """
    if thread_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[thread_id]
    return SessionState(
        thread_id=thread_id,
        messages=session["messages"],
        diagnostic_complete=session["diagnostic_complete"],
        current_question=session["current_question"],
        scorecard=session["scorecard"],
        artifacts=session["artifacts"],
    )


@app.get("/api/artifacts/{thread_id}/{filename}")
async def download_artifact(thread_id: str, filename: str) -> StreamingResponse:
    """Download generated artifact.

    Args:
        thread_id: Session thread ID
        filename: Artifact filename

    Returns:
        File download response
    """
    if thread_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    storage = get_artifact_storage()
    if filename not in storage:
        raise HTTPException(status_code=404, detail="Artifact not found")

    content = storage[filename]

    # Determine content type
    if filename.endswith(".json"):
        media_type = "application/json"
    elif filename.endswith(".md"):
        media_type = "text/markdown"
    else:
        media_type = "application/octet-stream"

    return StreamingResponse(
        iter([content.encode()]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/diagnostic/questions")
async def get_all_questions() -> dict:
    """Get all diagnostic questions.

    Returns:
        All 3 diagnostic questions
    """
    questions = []
    for i in range(1, 4):
        q = get_diagnostic_question.invoke({"question_number": i})
        questions.append(q)

    return {"questions": questions}


@app.post("/api/agent/approve")
async def approve_action(input: ApprovalInput) -> dict:
    """HITL approval for sensitive actions.

    Args:
        input: Approval decision

    Returns:
        Result of approval
    """
    if input.thread_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # In production, this would resume the agent with the approval
    return {
        "status": "approved" if input.decision == "approve" else "rejected",
        "thread_id": input.thread_id,
    }


# Development server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
