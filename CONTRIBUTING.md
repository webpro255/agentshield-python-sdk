# Contributing to AgentShield Python SDK

Thank you for your interest in contributing to AgentShield! We welcome contributions from the community.

## Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/your-username/agentshield-python-sdk.git
cd agentshield-python-sdk
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### 4. Run Tests

```bash
pytest
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write clean, documented code
- Add type hints
- Follow PEP 8 style guidelines
- Add docstrings to all functions/classes

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agentshield --cov-report=html

# Run specific test
pytest tests/test_client.py::TestAgentShieldClient::test_log_agent_call_allowed
```

### 4. Format Code

```bash
# Format with black
black agentshield tests examples

# Check with flake8
flake8 agentshield

# Type check with mypy
mypy agentshield
```

### 5. Update Documentation

- Update README.md if adding features
- Add docstrings to new code
- Update GETTING_STARTED.md if needed

### 6. Commit Changes

```bash
git add .
git commit -m "Add: Feature description"
```

Commit message format:
- `Add: New feature`
- `Fix: Bug description`
- `Update: Changes to existing feature`
- `Docs: Documentation updates`
- `Test: Test updates`

### 7. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

### Python Style

- Follow PEP 8
- Use type hints
- Line length: 88 characters (Black default)
- Use docstrings for all public functions/classes

### Example

```python
def log_agent_call(
    self,
    tool_name: str,
    tool_args: Dict[str, Any],
    execution_time_ms: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Log an agent call to AgentShield for policy evaluation.

    Args:
        tool_name: Name of the tool/function being called
        tool_args: Arguments passed to the tool
        execution_time_ms: Optional execution time in milliseconds

    Returns:
        Response from API with status and call information

    Raises:
        APIKeyError: If shield_key is invalid
        NetworkError: If network request fails
    """
    # Implementation
    pass
```

## Testing Guidelines

### Writing Tests

- Use pytest
- Mock external API calls
- Test edge cases
- Aim for 80%+ coverage

### Test Structure

```python
class TestFeature:
    """Test suite for Feature class."""

    def test_success_case(self):
        """Test successful operation."""
        # Arrange
        # Act
        # Assert
        pass

    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ExpectedException):
            # Code that should raise exception
            pass
```

## Adding New Features

### 1. Core Features

For core functionality (client, interceptor):
1. Discuss in GitHub issue first
2. Write comprehensive tests
3. Update documentation
4. Ensure backward compatibility

### 2. Integrations

For new framework integrations:
1. Create new file in `agentshield/integrations/`
2. Add tests in `tests/integrations/`
3. Add example in `examples/`
4. Document in README.md

### 3. Examples

For new examples:
1. Create file in `examples/`
2. Include clear comments
3. Make it runnable
4. Update README.md

## Release Process

1. Update version in `setup.py` and `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag -a v0.1.0 -m "Release v0.1.0"`
4. Push tag: `git push origin v0.1.0`
5. Build package: `python -m build`
6. Upload to PyPI: `twine upload dist/*`

## Questions?

- Open a GitHub issue
- Email: support@agent-shield.com
- Discord: [discord.gg/agentshield](https://discord.gg/agentshield)

Thank you for contributing! 🙏
