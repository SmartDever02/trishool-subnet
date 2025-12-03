"""
Mock objects and helpers for testing.

This module provides mock objects for external dependencies and services.
"""
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional, List
import pytest


class MockWallet:
    """Mock Bittensor wallet for testing."""

    def __init__(self, coldkey_name: str = "test_coldkey", hotkey_name: str = "test_hotkey"):
        self.name = coldkey_name
        self.hotkey = MockHotkey()
        self.coldkey = Mock()


class MockHotkey:
    """Mock Bittensor hotkey for testing."""

    def __init__(self):
        self.ss58_address = "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty"

    def sign(self, message_bytes: bytes) -> bytes:
        """Mock signature generation."""
        return b"mock_signature_" + message_bytes[:10]


class MockPlatformAPIClient:
    """Mock PlatformAPIClient for testing."""

    def __init__(self, platform_api_url: str = "http://localhost:8000"):
        self.platform_api_url = platform_api_url
        self.coldkey_name = "test_coldkey"
        self.hotkey_name = "test_hotkey"
        self.network = "finney"
        self.netuid = 35
        self.wallet = None

    def _build_auth_headers(self) -> Dict[str, str]:
        """Mock authentication headers."""
        return {
            "X-Sign-Message": "mock_message",
            "X-Signature": "mock_signature",
            "Content-Type": "application/json",
        }

    async def get_evaluation_agents(self) -> Optional[Dict[str, Any]]:
        """Mock get_evaluation_agents method."""
        return {
            "submission_id": "test_submission_123",
            "run_id": "test_run_123",
            "seed_instruction": "Test seed instruction",
            "models": ["model1", "model2"],
            "auditor": "auditor1",
            "judge": "judge1",
            "max_turns": 5,
        }

    async def submit_petri_output(
        self, submission_id: str, petri_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock submit_petri_output method."""
        return {
            "status": "success",
            "message": "Petri output submitted successfully",
            "run_id": petri_output.get("run_id", ""),
        }

    async def get_weights(self) -> Optional[Dict[str, float]]:
        """Mock get_weights method."""
        return {
            "0": 0.1,
            "1": 0.2,
            "2": 0.15,
        }

    async def healthcheck(self) -> bool:
        """Mock healthcheck method."""
        return True


class MockSandboxManager:
    """Mock SandboxManager for testing."""

    def __init__(self):
        self.sandboxes = {}
        self.docker = Mock()

    def create_sandbox(
        self,
        petri_config: Dict[str, Any],
        env_vars: Dict[str, str],
        on_finish: callable,
        timeout: int = 600,
    ) -> str:
        """Mock create_sandbox method."""
        sandbox_id = f"mock_sandbox_{len(self.sandboxes)}"
        mock_sandbox = Mock()
        mock_sandbox.sandbox_id = sandbox_id
        self.sandboxes[sandbox_id] = mock_sandbox
        return sandbox_id

    def run_sandbox(self, sandbox_id: str):
        """Mock run_sandbox method."""
        if sandbox_id in self.sandboxes:
            # Simulate successful completion
            result = {
                "status": "success",
                "output_json": {
                    "run_id": "test_run_123",
                    "summary": {"overall_metrics": {"mean_score": 0.8}},
                },
            }
            # Call on_finish callback if sandbox has one
            sandbox = self.sandboxes[sandbox_id]
            if hasattr(sandbox, "on_finish"):
                sandbox.on_finish(result)

    def cleanup_sandbox(self, sandbox_id: str):
        """Mock cleanup_sandbox method."""
        if sandbox_id in self.sandboxes:
            del self.sandboxes[sandbox_id]

    def cleanup_all(self):
        """Mock cleanup_all method."""
        self.sandboxes.clear()


@pytest.fixture
def mock_wallet():
    """Fixture providing a mock Bittensor wallet."""
    return MockWallet()


@pytest.fixture
def mock_platform_api_client():
    """Fixture providing a mock PlatformAPIClient."""
    return MockPlatformAPIClient()


@pytest.fixture
def mock_sandbox_manager():
    """Fixture providing a mock SandboxManager."""
    return MockSandboxManager()


@pytest.fixture
def mock_docker_client():
    """Fixture providing a mock Docker client."""
    mock_client = MagicMock()
    mock_client.images.build.return_value = (MagicMock(), [])
    mock_client.containers.run.return_value = MagicMock()
    return mock_client


def create_mock_submission(
    submission_id: str = "test_submission_123",
    run_id: str = "test_run_123",
    seed_instruction: str = "Test instruction",
    models: List[str] = None,
    status: str = "submitted",
) -> Dict[str, Any]:
    """
    Create a mock submission dictionary.

    Args:
        submission_id: Submission ID
        run_id: Run ID
        seed_instruction: Seed instruction text
        models: List of models
        status: Submission status

    Returns:
        Mock submission dictionary
    """
    if models is None:
        models = ["model1", "model2"]

    return {
        "submission_id": submission_id,
        "run_id": run_id,
        "seed_instruction": seed_instruction,
        "models": models,
        "auditor": "auditor1",
        "judge": "judge1",
        "max_turns": 5,
        "status": status,
    }


def create_mock_api_response(
    status: str = "success",
    submission_id: str = "test_submission_123",
    data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Create a mock API response dictionary.

    Args:
        status: Response status
        submission_id: Submission ID
        data: Additional response data

    Returns:
        Mock API response dictionary
    """
    response = {
        "status": status,
        "submission_id": submission_id,
    }
    if data:
        response.update(data)
    return response


def patch_wallet_load(monkeypatch, mock_wallet=None):
    """
    Patch wallet loading functions for testing.

    Args:
        monkeypatch: pytest monkeypatch fixture
        mock_wallet: Optional mock wallet to use
    """
    if mock_wallet is None:
        mock_wallet = MockWallet()

    def mock_load_wallet(wallet_name: str, wallet_hotkey: str):
        return mock_wallet

    def mock_build_pair_auth_payload(
        *,
        network: str,
        netuid: int,
        slot: str,
        wallet_name: str,
        wallet_hotkey: str,
    ) -> Dict[str, Any]:
        return {
            "message": f"mock_message|network:{network}|netuid:{netuid}",
            "signature": "0xmocksignature",
            "expires_at": 1234567890,
        }

    monkeypatch.setattr(
        "alignet.cli.bts_signature.load_wallet",
        mock_load_wallet,
    )
    monkeypatch.setattr(
        "alignet.cli.bts_signature.build_pair_auth_payload",
        mock_build_pair_auth_payload,
    )


@pytest.fixture
def patched_wallet(monkeypatch):
    """Fixture that patches wallet loading functions."""
    patch_wallet_load(monkeypatch)
    yield

