# Test Suite

Pytest-based test suite for Trishool Subnet services.

## Running Tests

### Run all tests
```bash
pytest
```

### Run only unit tests (fast)
```bash
pytest -m unit
```

### Run only integration tests
```bash
pytest -m integration
```

### Run tests excluding slow tests
```bash
pytest -m "not slow"
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/test_platform_api.py
```

### Run specific test function
```bash
pytest tests/test_platform_api.py::test_upload_agent
```

## Test Structure

- `tests/test_platform_api.py` - Platform API endpoint tests
- `tests/test_sandbox.py` - Sandbox execution tests
- `tests/test_validator.py` - Validator functionality tests
- `tests/test_github_api.py` - GitHub API tests
- `tests/conftest.py` - Shared pytest fixtures and configuration
- `tests/utils/` - Test utilities and helpers

## Test Markers

Tests are marked with pytest markers for easy filtering:

- `@pytest.mark.unit` - Unit tests (fast, no external dependencies)
- `@pytest.mark.integration` - Integration tests (may require external services)
- `@pytest.mark.slow` - Slow running tests (may take a long time)
- `@pytest.mark.asyncio` - Async tests

## Fixtures

Common fixtures available in `conftest.py`:

- `test_config` - Test configuration from environment variables
- `sample_agent_content` - Sample agent code for testing
- `sample_seed_instruction` - Sample seed instruction
- `sample_models` - Sample model list
- `sample_auditor` - Sample auditor model
- `sample_judge` - Sample judge model
- `env_vars` - Environment variables for sandbox testing
- `api_tester` - PlatformAPITester instance
- `sandbox_manager` - SandboxManager instance
- `test_submission` - Test MinerSubmission instance
- `validator` - Validator instance

## Environment Variables

Tests use environment variables for configuration. Set these in your `.env` file:

- `COLDKEY_NAME` - Bittensor coldkey name
- `HOTKEY_NAME` - Bittensor hotkey name
- `PLATFORM_API_URL` - Platform API URL
- `NETWORK` - Bittensor network (default: finney)
- `NETUID` - Subnet UID (default: 35)
- `SLOT` - Slot number (default: 1)
- `ANTHROPIC_API_KEY` - Anthropic API key
- `OPENAI_API_KEY` - OpenAI API key
- `CHUTES_API_KEY` - Chutes API key
- `CHUTES_BASE_URL` - Chutes base URL
- `OPENAI_API_BASE` - OpenAI API base URL

## Adding New Tests

1. Create test file following naming convention: `test_*.py`
2. Use appropriate markers (`@pytest.mark.unit`, `@pytest.mark.integration`)
3. Use fixtures from `conftest.py` instead of hardcoding values
4. Follow existing test patterns
5. Use proper assertions with descriptive messages

## Example Test

```python
import pytest
from tests.conftest import sample_agent_content

@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_agent(api_tester, sample_agent_content):
    """Test uploading a miner agent to the platform."""
    result = await api_tester.upload_agent(agent_content=sample_agent_content)
    
    assert result["status_code"] in [200, 201]
    assert "data" in result
```
