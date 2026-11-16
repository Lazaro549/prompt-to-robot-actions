# Contributing

Thanks for interest in **prompt-to-robot-actions**.

## Setup

```bash
git clone https://github.com/Lazaro549/prompt-to-robot-actions.git
cd prompt-to-robot-actions
pip install -e ".[dev]"
pytest -q
```

## Guidelines

1. Keep backends compatible with `src.backends.protocol.Backend`.
2. Add or update tests for planner, executor, safety, and validation changes.
3. Do not commit API keys or large binaries.
4. Prefer small PRs with a clear description.
5. Update `CHANGELOG.md` for user-visible changes.

## Code style

- Python 3.10+
- Type hints where practical
- `pytest` for tests; coverage gate is configured in `pyproject.toml`

## Reporting issues

Use the issue templates under `.github/ISSUE_TEMPLATE/`.
