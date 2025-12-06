# Contributing to GTM Deep Agent

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Set up the development environment (see README.md)
4. Create a feature branch from `develop`

## Development Workflow

### Branch Naming

- `feature/<description>` - New features
- `fix/<description>` - Bug fixes
- `docs/<description>` - Documentation only
- `refactor/<description>` - Code refactoring
- `test/<description>` - Test additions/fixes

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting, no code change
- `refactor` - Code change that neither fixes bug nor adds feature
- `test` - Adding or fixing tests
- `chore` - Build process or auxiliary tool changes

**Scopes:**
- `agent` - Agent code
- `api` - API endpoints
- `web` - Frontend code
- `tools` - Agent tools
- `subagents` - Subagent code
- `tests` - Test infrastructure
- `ci` - CI/CD configuration
- `docs` - Documentation

**Examples:**
```
feat(agent): add diagnostic question tool

Implements the get_diagnostic_question tool that returns
structured questions with button options.

Closes #12
```

```
fix(api): handle URL scraping timeout gracefully

- Add 10 second timeout to web_fetch
- Fall back to manual description on timeout
- Show user-friendly error message

Fixes #45
```

### Pull Requests

1. Create PR against `develop` branch
2. Fill out the PR template
3. Ensure all CI checks pass
4. Request review from maintainers
5. Address feedback
6. Squash and merge when approved

### PR Title Format

Follow the same format as commits:
```
feat(agent): add diagnostic question tool
```

## Testing Requirements

### Unit Tests

- Required for all new code
- No LLM calls (mock everything)
- Fast execution (<1s per test)
- Located in `tests/unit/`

### Integration Tests

- Required for tool and subagent changes
- Use VCR cassettes for API calls
- Located in `tests/integration/`
- Run with `pytest tests/integration -v`

### E2E Tests

- Required for major features
- Use real LLM calls
- Run sparingly (cost consideration)
- Located in `tests/e2e/`
- Run with `pytest tests/e2e -v -m e2e`

## Code Style

### Python

- Format with `ruff format`
- Lint with `ruff check`
- Type hints required
- Docstrings for public functions

### TypeScript

- ESLint configuration in `apps/web`
- Strict TypeScript settings
- Functional React components

## Questions?

- Open an issue for bugs or feature requests
- Use discussions for questions
- Tag maintainers for urgent issues
