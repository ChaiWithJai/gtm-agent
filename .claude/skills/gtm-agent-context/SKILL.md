# GTM Deep Agent - Project Context Skill

## Description
This skill provides comprehensive context for continuing development on the GTM Deep Agent application. Use this when picking up development work, debugging issues, or understanding the architecture.

## Trigger Phrases
- "Help me understand the GTM agent codebase"
- "I need context on this project"
- "What's the current state of GTM agent?"
- "How does the GTM agent work?"

---

## Project Overview

**GTM Deep Agent** is an AI-powered Go-To-Market strategy assistant that guides founders through a diagnostic process and generates personalized GTM artifacts.

### Critical User Journey
1. User enters product URL or description
2. System analyzes the company/product
3. User answers 3 diagnostic questions about ICP, value proposition clarity, and success metrics
4. System shows GTM Level (1-5) and asks "Would you like to generate artifacts?"
5. User confirms → System generates scorecard + 4 artifacts (narrative, emails, LinkedIn posts, action plan)

---

## Architecture

```
gtm-agent/
├── apps/
│   ├── agent/                    # Python FastAPI backend
│   │   ├── src/gtm_agent/
│   │   │   ├── api.py           # Main FastAPI server (port 8000)
│   │   │   ├── graph.py         # LangGraph state machine
│   │   │   ├── tools.py         # LangGraph tools (website scraper, etc.)
│   │   │   └── prompts.py       # System prompts
│   │   ├── tests/
│   │   │   └── e2e/
│   │   │       └── test_critical_pathway.py  # E2E API tests
│   │   └── .env                 # API keys (ANTHROPIC_API_KEY, LANGSMITH_API_KEY)
│   │
│   └── web/                     # React/TypeScript frontend
│       ├── src/
│       │   ├── App.tsx          # Main app component
│       │   ├── components/
│       │   │   ├── StartScreen.tsx    # URL/description input
│       │   │   ├── ChatInterface.tsx  # Main chat UI
│       │   │   └── ArtifactPanel.tsx  # Artifact display/download
│       │   └── index.css        # Styles (Princeton branding)
│       └── vite.config.ts
```

### Tech Stack
- **Backend**: FastAPI + LangGraph + Anthropic Claude API
- **Frontend**: React + TypeScript + Vite
- **Communication**: Server-Sent Events (SSE) for streaming
- **Testing**: pytest (backend), Playwright (e2e browser tests)

### Key Ports
- `8000` - FastAPI server
- `2024` - LangGraph API (internal)
- `3000-3002` - Vite dev server (auto-increments if busy)

---

## Key Files Reference

### `apps/agent/src/gtm_agent/api.py`
Main API server. Key endpoints:
- `GET /` - Health check
- `POST /api/agent/start` - Start session with URL or description
- `POST /api/agent/message` - Send message/answer, returns SSE stream
- `GET /api/artifacts/{thread_id}/{filename}` - Download artifact
- `GET /api/session/{thread_id}` - Get session state

**Important**: Uses `python-dotenv` to load `.env` file. The dotenv loading happens at module import time:
```python
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)
```

### `apps/agent/tests/e2e/test_critical_pathway.py`
Comprehensive E2E tests for the critical pathway. 11 tests covering:
- API health
- Session start (URL and description)
- Complete diagnostic flow
- UX timing (scorecard appears only after confirmation)
- Artifact generation and download
- Edge cases (URL normalization, invalid thread, decline flow)

Run with:
```bash
cd apps/agent
ANTHROPIC_API_KEY=sk-... pytest tests/e2e/test_critical_pathway.py -v
```

---

## Recent Changes (As of Last Session)

### 1. API Key Loading Fix
**Problem**: Anthropic API calls failed with "Could not resolve authentication method"
**Solution**: Added python-dotenv loading at top of api.py

### 2. UX Timing Fix
**Problem**: Scorecard appeared immediately after 3rd question, before user confirmed
**Solution**: Moved scorecard event to only emit AFTER user clicks "Yes, build my artifacts"

The flow now works:
- After Q3 → Show "You're at Level X. Would you like to generate?" (NO scorecard yet)
- After "Yes" → THEN show scorecard + generate artifacts

### 3. E2E Tests
Created comprehensive test suite validating the entire critical pathway including the UX timing fix.

---

## Development Commands

### Start Backend
```bash
cd apps/agent
source .venv/bin/activate
python -m uvicorn gtm_agent.api:app --reload --port 8000
```

### Start Frontend
```bash
cd apps/web
npm run dev
```

### Run E2E Tests
```bash
cd apps/agent
ANTHROPIC_API_KEY=sk-... LANGSMITH_TRACING_V2=false pytest tests/e2e/test_critical_pathway.py -v
```

### Check API Health
```bash
curl http://localhost:8000/
# Returns: {"status": "ok", "service": "gtm-agent"}
```

---

## SSE Event Types

The `/api/agent/message` endpoint returns SSE events:

| Event | When | Data |
|-------|------|------|
| `message` | Assistant response | `{content: string}` |
| `options` | Multiple choice question | `{options: string[]}` |
| `scorecard` | After user confirms generation | `{scorecard: {level, gaps, recommendations}}` |
| `artifact` | Each generated artifact | `{filename, artifact_type, content}` |
| `company_context` | After URL analysis | `{name, description, features}` |
| `error` | On failure | `{message: string}` |

---

## Environment Variables

Required in `apps/agent/.env`:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
LANGSMITH_API_KEY=lsv2_... (optional, for tracing)
```

---

## Current State

**Working**:
- Full critical pathway (URL → diagnostic → artifacts)
- Real LLM-generated artifact content
- Correct UX timing (scorecard after confirmation)
- Artifact download
- Session state persistence
- E2E tests passing

**Frontend**:
- Princeton branding applied
- URL input with normalization
- Chat interface with options
- Artifact panel with download buttons

---

## Common Issues & Solutions

### "Could not resolve authentication method"
→ Check that `.env` file exists in `apps/agent/` with valid `ANTHROPIC_API_KEY`

### Tests skipped
→ Run with explicit env var: `ANTHROPIC_API_KEY=sk-... pytest ...`

### Port already in use
→ Kill existing process: `lsof -ti:8000 | xargs kill -9`

### Artifacts are empty/placeholder
→ Check API logs for LLM generation errors. Likely API key issue.

---

## Next Steps / Areas for Improvement

1. **Website scraper enhancement** - Better extraction of company features/pricing
2. **Artifact templates** - More customization options
3. **Session persistence** - Currently in-memory, could use Redis/DB
4. **Error handling** - More graceful frontend error states
5. **Loading states** - Better UX during artifact generation (can take 30-60s)
