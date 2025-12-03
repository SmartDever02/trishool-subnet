"""
Pytest configuration and shared fixtures.

This module imports all fixtures from utils/fixtures.py and utils/mocks.py
to make them available to all tests.
"""
# Import all fixtures from utils modules
from tests.utils.fixtures import (
    test_config,
    sample_agent_content,
    sample_seed_instruction,
    sample_models,
    sample_auditor,
    sample_judge,
    env_vars,
    sample_submission,
    sample_petri_config,
    sample_petri_output,
    sample_api_response,
    sample_weights,
)

from tests.utils.mocks import (
    mock_wallet,
    mock_platform_api_client,
    mock_sandbox_manager,
    mock_docker_client,
    patched_wallet,
)

# Make all fixtures available
__all__ = [
    # Configuration fixtures
    "test_config",
    "sample_agent_content",
    "sample_seed_instruction",
    "sample_models",
    "sample_auditor",
    "sample_judge",
    "env_vars",
    # Data fixtures
    "sample_submission",
    "sample_petri_config",
    "sample_petri_output",
    "sample_api_response",
    "sample_weights",
    # Mock fixtures
    "mock_wallet",
    "mock_platform_api_client",
    "mock_sandbox_manager",
    "mock_docker_client",
    "patched_wallet",
]
