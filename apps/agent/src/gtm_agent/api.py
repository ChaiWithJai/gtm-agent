"""FastAPI endpoints for GTM Deep Agent.

This API serves as a bridge between the React frontend and the LangGraph agent.
It handles session management and proxies requests to the LangGraph API for
actual LLM-powered responses and artifact generation.
"""

import asyncio
import json
import os
import time
import uuid
from pathlib import Path
from typing import AsyncGenerator

import anthropic
import httpx
from dotenv import load_dotenv

# Load .env file from the apps/agent directory
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from gtm_agent.tools import (
    calculate_escalator_level,
    get_artifact_storage,
    get_diagnostic_question,
    web_fetch,
    write_artifact,
)

# LangGraph API configuration
LANGGRAPH_API_URL = "http://localhost:2024"
ASSISTANT_ID = "gtm-agent"

# Initialize Anthropic client for direct artifact generation
# Explicitly get API key from environment to ensure it's available
api_key = os.environ.get("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=api_key) if api_key else None


async def generate_artifact_content(
    artifact_type: str,
    company_name: str,
    description: str,
    features: list[str],
    level: int,
    gaps: list[str],
    icp: str,
) -> str:
    """Generate personalized artifact content using Claude API directly."""

    prompts = {
        "narrative": f"""Create a strategic narrative document for {company_name}.

Company Context:
- Description: {description}
- Key Features: {', '.join(features) if features else 'Not specified'}
- Target Customer: {icp}
- GTM Level: {level}
- Key Gaps: {', '.join(gaps) if gaps else 'None identified'}

Generate a concise, actionable strategic narrative with:
1. **Positioning Statement** - One sentence: For [specific ICP] who [specific problem], {company_name} is a [category] that [key benefit based on their features].
2. **ICP Definition** - Who exactly buys, what role, company size, and buying triggers
3. **Value Proposition** - 3 specific bullets based on their actual features
4. **Key Messages** - Elevator pitch, detailed pitch, and social proof message

Be specific to {company_name}. No placeholders like [your X]. Use actual details.""",

        "emails": f"""Create a 3-email cold outreach sequence for {company_name}.

Company Context:
- Description: {description}
- Key Features: {', '.join(features) if features else 'Not specified'}
- Target Customer: {icp}

Generate 3 emails:
1. **Email 1: Introduction** - Short, personalized opener referencing a specific pain point
2. **Email 2: Value** - Share a specific insight or quick win related to their problem
3. **Email 3: Breakup** - Final attempt with clear CTA

Each email should have: Subject line, Body (under 100 words), and CTA.
Be specific to {company_name}'s offering. No generic templates.""",

        "linkedin": f"""Create 5 LinkedIn posts for {company_name}.

Company Context:
- Description: {description}
- Key Features: {', '.join(features) if features else 'Not specified'}
- Target Customer: {icp}

Generate 5 different posts:
1. **Problem Awareness** - Highlight a pain point {icp} faces
2. **Solution Teaser** - Introduce {company_name}'s approach without being salesy
3. **Social Proof/Story** - Customer success or behind-the-scenes insight
4. **Industry Insight** - Thought leadership on a relevant trend
5. **Call to Action** - Direct ask with clear value proposition

Each post should be 100-150 words, include a hook, and feel authentic. Use emojis sparingly.""",

        "action_plan": f"""Create a 30-day GTM action plan for {company_name} at Level {level}.

Company Context:
- Description: {description}
- Target Customer: {icp}
- Current Gaps: {', '.join(gaps) if gaps else 'Foundation building needed'}

Generate a week-by-week plan:
**Week 1: Foundation**
- 3-4 specific tasks to address their identified gaps

**Week 2: Outreach Setup**
- 3-4 tasks to prepare outreach infrastructure

**Week 3: Launch & Learn**
- 3-4 tasks to start outbound and gather feedback

**Week 4: Iterate & Scale**
- 3-4 tasks to optimize based on learnings

Each task should be specific and completable in 1-2 hours. Include metrics to track.""",
    }

    prompt = prompts.get(artifact_type)
    if not prompt:
        return ""

    if not anthropic_client:
        raise ValueError("ANTHROPIC_API_KEY not set")

    # Use Claude API directly for content generation - run sync client in thread pool
    def call_claude():
        return anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

    response = await asyncio.to_thread(call_claude)
    return response.content[0].text

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

    When a URL is provided, we fetch and analyze it to understand the company's
    "Point A" - their current state, product, and market position. This context
    is used throughout the diagnostic to provide personalized recommendations.

    Args:
        input: Product URL or description

    Returns:
        Thread ID and initial messages with company context
    """
    if not input.product_url and not input.product_description:
        raise HTTPException(
            status_code=400,
            detail="Provide either product_url or product_description",
        )

    thread_id = str(uuid.uuid4())

    # Initialize session state
    company_context = None

    # If URL provided, fetch and analyze the website to understand "Point A"
    if input.product_url:
        try:
            company_context = web_fetch.invoke({"url": input.product_url})
        except Exception as e:
            company_context = {
                "success": False,
                "error": str(e),
                "company_name": None,
                "product_description": None,
                "key_features": [],
            }

    sessions[thread_id] = {
        "messages": [],
        "diagnostic_complete": False,
        "current_question": 0,
        "answers": {},
        "scorecard": None,
        "artifacts": [],
        "product_url": input.product_url,
        "product_description": input.product_description,
        "company_context": company_context,
    }

    # Get first diagnostic question
    question = get_diagnostic_question.invoke({"question_number": 1})
    sessions[thread_id]["current_question"] = 1

    # Build personalized intro message based on company context
    if company_context and company_context.get("success"):
        company_name = company_context.get("company_name", "your company")
        description = company_context.get("product_description", "")
        features = company_context.get("key_features", [])

        intro_parts = [f"**Analyzing {company_name}**"]

        if description:
            intro_parts.append(f"\nI see you're building: *{description[:200]}*")

        if features:
            intro_parts.append(f"\n\nKey areas I identified: {', '.join(features[:3])}")

        intro_parts.append("\n\nLet me assess where you are in your GTM journey so I can generate personalized artifacts for you.")
        intro = "".join(intro_parts)
    elif input.product_url:
        intro = f"I'll help you with GTM strategy for **{input.product_url}**.\n\nLet me assess your current GTM readiness."
    else:
        intro = f"Thanks for describing your product.\n\n*{input.product_description[:150]}...*\n\nLet me assess your GTM readiness."

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

    return {"thread_id": thread_id, "messages": messages, "company_context": company_context}


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
            # Calculate scorecard with company context for personalized recommendations
            # But don't show it yet - wait for user to click "Yes, build my artifacts"
            company_context = session.get("company_context", {})
            scorecard = calculate_escalator_level.invoke({
                "answers": session["answers"],
                "company_context": company_context if company_context and company_context.get("success") else None,
            })
            session["scorecard"] = scorecard
            session["diagnostic_complete"] = True

            # Prompt for artifact generation (show scorecard AFTER user confirms)
            response = {
                "role": "assistant",
                "content": f"Based on your answers, you're at GTM Level {scorecard['level']}. Would you like me to generate your GTM artifacts?",
                "options": ["Yes, build my artifacts", "Not now"],
            }
            session["messages"].append(response)

            yield f"data: {json.dumps({'event': 'message', 'content': response['content']})}\n\n"
            yield f"data: {json.dumps({'event': 'options', 'options': response['options']})}\n\n"

        elif session["diagnostic_complete"] and "build" in message_content.lower():
            # User confirmed - now show scorecard and generate artifacts
            scorecard = session.get("scorecard", {})
            company_context = session.get("company_context", {})

            # Send scorecard to frontend first
            yield f"data: {json.dumps({'event': 'scorecard', 'scorecard': scorecard})}\n\n"

            # Save scorecard artifact
            write_artifact.invoke(
                {
                    "filename": "gtm-scorecard.json",
                    "content": json.dumps(scorecard, indent=2),
                    "artifact_type": "scorecard",
                }
            )
            session["artifacts"].append("gtm-scorecard.json")
            yield f"data: {json.dumps({'event': 'artifact', 'filename': 'gtm-scorecard.json'})}\n\n"

            # Generate other artifacts using LangGraph API for real LLM-generated content
            yield f"data: {json.dumps({'event': 'status', 'content': 'Generating personalized GTM artifacts...'})}\n\n"

            # Use the LangGraph API to generate real artifacts
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    # Create a thread in LangGraph
                    thread_resp = await client.post(f"{LANGGRAPH_API_URL}/threads", json={})
                    lg_thread_id = thread_resp.json()["thread_id"]

                    # Build the artifact generation prompt - handle None values properly
                    company_name = (company_context.get("company_name") if company_context else None) or "the company"
                    description = (company_context.get("product_description") if company_context else None) or ""
                    features = (company_context.get("key_features") if company_context else None) or []
                    level = (scorecard.get("level") if scorecard else None) or 1
                    gaps = (scorecard.get("gaps") if scorecard else None) or []
                    recommendations = (scorecard.get("recommendations") if scorecard else None) or []

                    prompt = f"""Generate the complete GTM artifacts for {company_name}.

Company Context:
- Description: {description}
- Key Features: {', '.join(features) if features else 'Not specified'}
- Current GTM Level: {level}
- Identified Gaps: {', '.join(gaps) if gaps else 'None specified'}
- Recommendations: {', '.join(recommendations) if recommendations else 'None specified'}

Please generate all 5 GTM artifacts now:
1. GTM Escalator Scorecard
2. Strategic Narrative Document
3. Outbound Email Sequence (3 emails)
4. LinkedIn Post Templates (5 posts)
5. 30-Day Action Plan

Make each artifact specific to {company_name} and their Level {level} status. Use write_artifact for each one."""

                    # Start the run
                    run_resp = await client.post(
                        f"{LANGGRAPH_API_URL}/threads/{lg_thread_id}/runs",
                        json={
                            "assistant_id": ASSISTANT_ID,
                            "input": {"messages": [{"role": "user", "content": prompt}]},
                        },
                    )
                    run_id = run_resp.json()["run_id"]

                    # Poll for completion
                    for _ in range(60):
                        status_resp = await client.get(
                            f"{LANGGRAPH_API_URL}/threads/{lg_thread_id}/runs/{run_id}"
                        )
                        status = status_resp.json().get("status")
                        if status == "success":
                            break
                        elif status == "error":
                            raise Exception("Agent run failed")
                        await asyncio.sleep(2)

                    # Get the generated artifacts from state
                    state_resp = await client.get(
                        f"{LANGGRAPH_API_URL}/threads/{lg_thread_id}/state"
                    )
                    state_data = state_resp.json()

                    # Extract artifacts from the agent's tool calls
                    messages = state_data.get("values", {}).get("messages", [])
                    generated_artifacts = []

                    for msg in messages:
                        if msg.get("type") == "ai":
                            content = msg.get("content", [])
                            if isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and item.get("name") == "write_artifact":
                                        artifact_input = item.get("input", {})
                                        filename = artifact_input.get("filename")
                                        if filename:
                                            generated_artifacts.append(filename)

                    # Also check tool messages for artifact metadata
                    for msg in messages:
                        if msg.get("type") == "tool" and msg.get("name") == "write_artifact":
                            try:
                                result = json.loads(msg.get("content", "{}"))
                                if result.get("filename"):
                                    generated_artifacts.append(result["filename"])
                            except json.JSONDecodeError:
                                pass

                    # Deduplicate and notify frontend
                    seen = set()
                    for filename in generated_artifacts:
                        if filename not in seen:
                            seen.add(filename)
                            session["artifacts"].append(filename)
                            yield f"data: {json.dumps({'event': 'artifact', 'filename': filename})}\n\n"

                    artifact_count = len(seen)
                    response = {
                        "role": "assistant",
                        "content": f"I've generated {artifact_count} personalized GTM artifacts for **{company_name}**. Each artifact is tailored to your Level {level} status and specific gaps. Download them below!",
                    }

            except Exception as e:
                # Fallback to direct Claude API artifact generation
                yield f"data: {json.dumps({'event': 'status', 'content': 'Generating personalized artifacts directly...'})}\n\n"

                # Handle None values - use 'or' to catch both missing key and None value
                company_name = (company_context.get("company_name") if company_context else None) or "Your Company"
                description = (company_context.get("product_description") if company_context else None) or ""
                features = (company_context.get("key_features") if company_context else None) or []
                level = scorecard.get("level", 1) if scorecard else 1
                gaps = scorecard.get("gaps", []) if scorecard else []
                icp = session.get("answers", {}).get("q1", "your target customers")

                # Generate scorecard (simple, no LLM needed)
                scorecard_content = f"# GTM Scorecard for {company_name}\n\n## Current Level: {level}\n\n### Gaps to Address:\n" + "\n".join(f"- {g}" for g in gaps)
                write_artifact.invoke({"filename": "gtm-scorecard.md", "content": scorecard_content, "artifact_type": "scorecard"})
                session["artifacts"].append("gtm-scorecard.md")
                yield f"data: {json.dumps({'event': 'artifact', 'filename': 'gtm-scorecard.md'})}\n\n"

                # Generate LLM-powered artifacts
                artifact_configs = [
                    ("gtm-narrative.md", "narrative", "Strategic Narrative"),
                    ("cold-emails.md", "emails", "Cold Emails"),
                    ("linkedin-posts.md", "linkedin", "LinkedIn Posts"),
                    ("30-day-plan.md", "action_plan", "30-Day Plan"),
                ]

                for filename, artifact_type, label in artifact_configs:
                    yield f"data: {json.dumps({'event': 'status', 'content': f'Creating {label}...'})}\n\n"
                    try:
                        print(f"[DEBUG] Generating {artifact_type} for {company_name}")
                        content = await generate_artifact_content(
                            artifact_type=artifact_type,
                            company_name=company_name,
                            description=description,
                            features=features,
                            level=level,
                            gaps=gaps,
                            icp=icp,
                        )
                        print(f"[DEBUG] Generated content length: {len(content)}")
                        # Add title header
                        full_content = f"# {label}: {company_name}\n\n{content}"
                        write_artifact.invoke({"filename": filename, "content": full_content, "artifact_type": artifact_type})
                        session["artifacts"].append(filename)
                        yield f"data: {json.dumps({'event': 'artifact', 'filename': filename})}\n\n"
                    except Exception as gen_error:
                        # Log the error and create fallback artifact
                        print(f"[ERROR] Failed to generate {artifact_type}: {gen_error}")
                        fallback_content = f"# {label}: {company_name}\n\n[Content generation in progress - please refresh or try again]"
                        write_artifact.invoke({"filename": filename, "content": fallback_content, "artifact_type": artifact_type})
                        session["artifacts"].append(filename)
                        yield f"data: {json.dumps({'event': 'artifact', 'filename': filename})}\n\n"

                response = {
                    "role": "assistant",
                    "content": f"I've generated personalized GTM artifacts for **{company_name}**. Each artifact is tailored to your Level {level} status and specific gaps. Download them below!",
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
