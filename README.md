# GTM Deep Agent

> Stop scattered. Start shipping.

A Deep Agent that helps founders transform scattered GTM thinking into concrete, actionable artifacts in under 15 minutes.

## What It Does

The GTM Deep Agent solves three interconnected problems founders face:

1. **PMM Narrative Gap**: Can't articulate "what do you do?" in one sentence
2. **Communications Bottleneck**: Every email, deck, and post requires the founder's voice
3. **GTM Escalator Inversion**: Jumping to Level 5 tactics without Level 1-4 foundation

## Artifacts Generated

- GTM Escalator Scorecard (PDF/MD)
- Strategic Narrative Doc (1-pager)
- Outbound Email Sequence (3 emails)
- LinkedIn Post Templates (5 posts)
- 30-Day Action Plan (checklist)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Anthropic API key
- LangSmith API key (optional, for tracing)

### Installation

```bash
# Clone the repository
git clone https://github.com/ChaiWithJai/gtm-agent.git
cd gtm-agent

# Set up Python environment
cd apps/agent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Set up frontend
cd ../web
npm install

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running Locally

```bash
# Start the agent backend (LangGraph dev server)
langgraph dev

# In another terminal, start the frontend
cd apps/web
npm run dev
```

### Running Tests

```bash
# Unit tests (fast, no LLM calls)
pytest tests/unit -v

# Integration tests (uses VCR cassettes)
pytest tests/integration -v

# E2E tests (live LLM calls, slow)
pytest tests/e2e -v -m e2e
```

## Architecture

```
gtm-agent/
├── apps/
│   ├── agent/              # Python backend (LangGraph)
│   │   ├── src/gtm_agent/
│   │   │   ├── agent.py    # Main agent factory
│   │   │   ├── prompts.py  # System prompts
│   │   │   ├── schemas.py  # Pydantic schemas
│   │   │   ├── tools/      # Agent tools
│   │   │   ├── subagents/  # Specialized subagents
│   │   │   └── memories/   # Domain knowledge
│   │   └── tests/
│   └── web/                # React frontend
├── langgraph.json          # LangGraph deployment config
└── .github/workflows/      # CI/CD pipelines
```

## Development

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: Feature branches
- `fix/*`: Bug fix branches

### Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(agent): add diagnostic question tool
fix(api): handle URL scraping timeout
test(e2e): add multi-turn conversation tests
docs(readme): update installation instructions
```

### CI/CD Pipeline

- **On PR**: Run unit + integration tests
- **On merge to main**: Run full test suite + deploy to staging
- **On release tag**: Deploy to production

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
