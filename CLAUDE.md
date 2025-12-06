# GTM Deep Agent - Claude Code Instructions

## Project Overview

GTM Deep Agent helps founders transform scattered GTM thinking into concrete, actionable artifacts. It uses LangGraph for agent orchestration and deploys via LangGraph Cloud.

## Tech Stack

- **Backend**: Python 3.11+, LangGraph, LangChain, deepagents
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS
- **Testing**: pytest, VCR.py, LangSmith
- **Deployment**: LangGraph Cloud

## Project Structure

```
gtm-agent/
├── apps/
│   ├── agent/           # Python backend
│   │   ├── src/gtm_agent/
│   │   │   ├── agent.py    # Main agent factory
│   │   │   ├── prompts.py  # System prompts
│   │   │   ├── schemas.py  # Pydantic schemas
│   │   │   ├── tools/      # Agent tools
│   │   │   └── subagents/  # Specialized subagents
│   │   └── tests/
│   └── web/             # React frontend
├── langgraph.json       # LangGraph deployment config
└── .github/workflows/   # CI/CD
```

## Development Commands

```bash
# Backend
cd apps/agent
pip install -e ".[dev]"
pytest tests/unit -v                    # Fast unit tests
pytest tests/integration -v             # VCR-recorded tests
pytest tests/e2e -v -m e2e             # Live LLM tests
ruff check src/                         # Linting
ruff format src/                        # Formatting

# Local development server
langgraph dev

# Frontend
cd apps/web
npm install
npm run dev
npm run build
npm run test
```

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(agent): add diagnostic question tool
fix(api): handle URL scraping timeout
test(e2e): add multi-turn conversation tests
docs(readme): update installation instructions
refactor(schemas): simplify scorecard validation
```

Scopes: `agent`, `api`, `web`, `tools`, `subagents`, `tests`, `ci`, `docs`

## Branch Strategy

- `main` - Production-ready code, protected
- `develop` - Integration branch
- `feature/<name>` - New features
- `fix/<name>` - Bug fixes

## Testing Philosophy

1. **Unit tests** (no LLM): Test schemas, prompts, individual functions
2. **Integration tests** (VCR): Test tool invocation, subagent spawning
3. **E2E tests** (live LLM): Test full user journeys, multi-turn conversations

## Key Patterns

### Agent Factory Pattern

```python
from deepagents import create_deep_agent

def create_gtm_agent(model="anthropic:claude-sonnet-4-20250514"):
    return create_deep_agent(
        model=model,
        tools=[...],
        subagents=[...],
        system_prompt=GTM_SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )
```

### Tool Definition Pattern

```python
from langchain_core.tools import tool

@tool
def get_diagnostic_question(question_number: int) -> dict:
    """Get diagnostic question with button options.

    Args:
        question_number: Which question (1, 2, or 3)

    Returns:
        Dict with question_id, question_text, and options
    """
    ...
```

### Subagent Pattern

```python
narrative_subagent = {
    "name": "narrative-builder",
    "description": "Builds strategic narrative from diagnostic context",
    "system_prompt": NARRATIVE_SUBAGENT_PROMPT,
    "tools": [write_artifact],
}
```

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangSmith Pytest](https://docs.langchain.com/langsmith/pytest)
- [deepagents Library](https://github.com/langchain-ai/deepagents)
- Reference implementation: `../priw/`
