# Contributing to Kapso WhatsApp Cloud API Python SDK

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Requests](#pull-requests)
- [Reporting Issues](#reporting-issues)

---

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributions from everyone regardless of experience level.

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- A GitHub account

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/whatsapp-cloud-api-python.git
cd whatsapp-cloud-api-python
```

3. Add the upstream remote:

```bash
git remote add upstream https://github.com/gokapso/whatsapp-cloud-api-python.git
```

---

## Development Setup

### Create Virtual Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using uv
uv venv
source .venv/bin/activate
```

### Install Dependencies

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev]"

# Or using uv
uv pip install -e ".[dev]"
```

### Verify Setup

```bash
# Run tests
pytest

# Run linting
ruff check src tests

# Run type checking
mypy src
```

---

## Making Changes

### Create a Branch

Create a feature branch from `main`:

```bash
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

### Branch Naming

Use descriptive branch names:
- `feature/add-new-message-type`
- `fix/rate-limit-handling`
- `docs/update-examples`
- `refactor/simplify-error-handling`

### Commit Messages

Write clear, descriptive commit messages:

```
feat: Add support for reaction messages

- Implement send_reaction() method
- Add ReactionInput type model
- Include tests for reaction functionality
```

Follow conventional commits when possible:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

---

## Code Style

### Python Style

We use [ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
ruff check src tests

# Auto-fix issues
ruff check src tests --fix

# Format code
ruff format src tests
```

### Key Style Guidelines

1. **Type annotations** - All public functions should have type hints
2. **Docstrings** - Use docstrings for public modules, classes, and functions
3. **Line length** - Maximum 100 characters
4. **Imports** - Sorted with isort (handled by ruff)

### Example Function

```python
async def send_text(
    self,
    phone_number_id: str,
    to: str,
    body: str,
    *,
    preview_url: bool = False,
    context_message_id: str | None = None,
) -> SendMessageResponse:
    """Send a text message.

    Args:
        phone_number_id: The WhatsApp Business phone number ID.
        to: Recipient phone number in E.164 format.
        body: Message text content.
        preview_url: Enable URL preview in message.
        context_message_id: Message ID to reply to.

    Returns:
        Response with message ID and status.

    Raises:
        ValidationError: If input parameters are invalid.
        RateLimitError: If rate limit is exceeded.
    """
    input_data = TextMessageInput(
        phone_number_id=phone_number_id,
        to=to,
        body=body,
        preview_url=preview_url,
    )
    # ... implementation
```

### Type Checking

Run mypy to check types:

```bash
mypy src
```

Ensure all public APIs are properly typed.

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_client.py

# Run specific test
pytest tests/test_client.py::TestClientInitialization::test_requires_auth

# Run with coverage
pytest --cov=kapso_whatsapp --cov-report=html
```

### Writing Tests

1. **Location** - Place tests in the `tests/` directory
2. **Naming** - Use `test_` prefix for test files and functions
3. **Organization** - Group related tests in classes
4. **Fixtures** - Use pytest fixtures for common setup

### Test Example

```python
"""Tests for messages resource."""

import pytest
from kapso_whatsapp import WhatsAppClient
from kapso_whatsapp.exceptions import ValidationError


class TestSendText:
    """Tests for send_text method."""

    async def test_sends_basic_message(self, client: WhatsAppClient) -> None:
        """Should send a basic text message."""
        response = await client.messages.send_text(
            phone_number_id="123456",
            to="+15551234567",
            body="Hello, World!",
        )
        assert response.message_id is not None

    async def test_rejects_empty_body(self, client: WhatsAppClient) -> None:
        """Should reject empty message body."""
        with pytest.raises(ValidationError):
            await client.messages.send_text(
                phone_number_id="123456",
                to="+15551234567",
                body="",
            )
```

### Test Fixtures

Common fixtures are in `tests/conftest.py`:

```python
import pytest
from kapso_whatsapp import WhatsAppClient


@pytest.fixture
def access_token() -> str:
    """Test access token."""
    return "test_access_token_123"


@pytest.fixture
def client(access_token: str) -> WhatsAppClient:
    """Test client instance."""
    return WhatsAppClient(access_token=access_token)
```

---

## Pull Requests

### Before Submitting

1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   pytest
   ruff check src tests
   mypy src
   ```

3. **Update documentation** if needed

### PR Description

Include in your PR description:
- **Summary** - What does this PR do?
- **Motivation** - Why is this change needed?
- **Changes** - List of specific changes
- **Testing** - How was this tested?
- **Breaking Changes** - Any breaking changes?

### PR Template

```markdown
## Summary

Brief description of the changes.

## Motivation

Why this change is needed.

## Changes

- Change 1
- Change 2
- Change 3

## Testing

- [ ] Added tests for new functionality
- [ ] All existing tests pass
- [ ] Linting passes
- [ ] Type checking passes

## Checklist

- [ ] Code follows project style guidelines
- [ ] Documentation updated (if applicable)
- [ ] CHANGELOG updated (for significant changes)
```

### Review Process

1. A maintainer will review your PR
2. Address any feedback or requested changes
3. Once approved, your PR will be merged

---

## Reporting Issues

### Bug Reports

Include:
- Python version
- Package version
- Minimal reproduction code
- Expected behavior
- Actual behavior
- Error messages/tracebacks

### Feature Requests

Include:
- Use case description
- Proposed API design
- Example usage code

### Issue Template

```markdown
## Bug Report / Feature Request

### Description

Clear description of the issue or feature.

### Environment

- Python version: 3.10.x
- Package version: 0.1.0
- Operating System: macOS/Linux/Windows

### Steps to Reproduce (for bugs)

1. Step one
2. Step two
3. Step three

### Expected Behavior

What should happen.

### Actual Behavior

What actually happens.

### Code Example

```python
# Minimal reproduction code
```

### Additional Context

Any other relevant information.
```

---

## Questions?

If you have questions about contributing:
- Open a [GitHub Discussion](https://github.com/gokapso/whatsapp-cloud-api-python/discussions)
- Check existing issues and PRs

Thank you for contributing!
