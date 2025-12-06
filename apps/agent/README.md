# GTM Agent

Python backend for the GTM Deep Agent, built with LangGraph and deepagents.

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

```python
from gtm_agent.agent import create_gtm_agent

agent = create_gtm_agent()
result = agent.invoke({"messages": [{"role": "user", "content": "We build AI tools"}]})
```

## Testing

```bash
pytest tests/unit -v        # Unit tests
pytest tests/integration -v # Integration tests
pytest tests/e2e -v -m e2e  # E2E tests (requires API keys)
```

## Tools

- `get_diagnostic_question` - Get structured diagnostic questions
- `calculate_escalator_level` - Calculate GTM Escalator level
- `web_fetch` - Scrape product information from URLs
- `write_artifact` - Save generated artifacts

## Subagents

- `narrative-builder` - Creates GTM narrative documents
- `voice-cloner` - Generates voice-matched content
- `escalator-diagnostician` - Deep GTM level analysis
