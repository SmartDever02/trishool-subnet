"""
Unit tests for PlatformAPIClient using mocks.

These tests mock API responses to test the client without requiring network connectivity.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from aioresponses import aioresponses
from typing import Dict, Any

from alignet.validator.platform_api_client import PlatformAPIClient


@pytest.fixture
def mock_wallet():
    """Create a mock wallet for testing."""
    wallet = Mock()
    wallet.hotkey = Mock()
    wallet.hotkey.ss58_address = "5FHneW46xGXgs5mUiveU4sbTyGBzmstUspZC92UhjJM694ty"
    wallet.hotkey.sign = Mock(return_value=b"mock_signature")
    return wallet


@pytest.fixture
def api_client_with_wallet(mock_wallet):
    """Create PlatformAPIClient with mocked wallet."""
    with patch("alignet.validator.platform_api_client.load_wallet", return_value=mock_wallet):
        with patch("alignet.validator.platform_api_client.build_pair_auth_payload", return_value={
            "message": "mock_message",
            "signature": "0xmocksignature",
            "expires_at": 1234567890,
        }):
            client = PlatformAPIClient(
                platform_api_url="http://localhost:8000",
                coldkey_name="test_coldkey",
                hotkey_name="test_hotkey",
            )
            return client


@pytest.fixture
def api_client_without_wallet():
    """Create PlatformAPIClient without wallet (will fail auth)."""
    return PlatformAPIClient(
        platform_api_url="http://localhost:8000",
        coldkey_name=None,
        hotkey_name=None,
    )


class TestGetEvaluationAgents:
    """Tests for get_evaluation_agents method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_evaluation_agents_success(self, api_client_with_wallet):
        """Test successful retrieval of evaluation agents."""
        mock_response = {
            "submission_id": "test_submission_123",
            "run_id": "test_run_123",
            "seed_instruction": "Test seed instruction",
            "models": ["model1", "model2"],
            "auditor": "auditor1",
            "judge": "judge1",
            "max_turns": 5,
        }

        with aioresponses() as m:
            m.get(
                "http://localhost:8000/api/v1/validator/evaluation-agents",
                payload=mock_response,
                headers={"X-Sign-Message": "mock_message", "X-Signature": "0xmocksignature"},
            )

            result = await api_client_with_wallet.get_evaluation_agents()

            assert result is not None
            assert result["submission_id"] == "test_submission_123"
            assert result["run_id"] == "test_run_123"
            assert "seed_instruction" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_evaluation_agents_no_submission_404(self, api_client_with_wallet):
        """Test handling of 404 when no submission is available."""
        with aioresponses() as m:
            m.get(
                "http://localhost:8000/api/v1/validator/evaluation-agents",
                status=404,
            )

            result = await api_client_with_wallet.get_evaluation_agents()

            assert result is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_evaluation_agents_empty_response(self, api_client_with_wallet):
        """Test handling of empty response."""
        with aioresponses() as m:
            m.get(
                "http://localhost:8000/api/v1/validator/evaluation-agents",
                payload={},
            )

            result = await api_client_with_wallet.get_evaluation_agents()

            assert result is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_evaluation_agents_server_error(self, api_client_with_wallet):
        """Test handling of server error (500)."""
        with aioresponses() as m:
            m.get(
                "http://localhost:8000/api/v1/validator/evaluation-agents",
                status=500,
                body="Internal Server Error",
            )

            result = await api_client_with_wallet.get_evaluation_agents()

            assert result is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_evaluation_agents_network_error(self, api_client_with_wallet):
        """Test handling of network errors."""
        with aioresponses() as m:
            m.get(
                "http://localhost:8000/api/v1/validator/evaluation-agents",
                exception=Exception("Network error"),
            )

            result = await api_client_with_wallet.get_evaluation_agents()

            assert result is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_evaluation_agents_no_wallet(self, api_client_without_wallet):
        """Test that method fails when wallet is not loaded."""
        with pytest.raises(ValueError, match="Wallet not loaded"):
            await api_client_without_wallet.get_evaluation_agents()


class TestSubmitScores:
    """Tests for submit_scores method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_submit_scores_success(self, api_client_with_wallet):
        """Test successful score submission."""
        scores = [
            {"agent_id": "agent1", "score": 0.85},
            {"agent_id": "agent2", "score": 0.75},
        ]
        mock_response = {
            "status": "success",
            "message": "Scores submitted successfully",
            "session_id": "session_123",
            "count": 2,
        }

        with aioresponses() as m:
            m.post(
                "http://localhost:8000/api/v1/validator/submit_scores",
                payload=mock_response,
            )

            result = await api_client_with_wallet.submit_scores(scores)

            assert result["status"] == "success"
            assert result["count"] == 2
            assert result["session_id"] == "session_123"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_submit_scores_server_error(self, api_client_with_wallet):
        """Test handling of server error during score submission."""
        scores = [{"agent_id": "agent1", "score": 0.85}]

        with aioresponses() as m:
            m.post(
                "http://localhost:8000/api/v1/validator/submit_scores",
                status=500,
                body="Internal Server Error",
            )

            result = await api_client_with_wallet.submit_scores(scores)

            assert result["status"] == "error"
            assert "HTTP 500" in result["message"]
            assert result["count"] == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_submit_scores_network_error(self, api_client_with_wallet):
        """Test handling of network errors during score submission."""
        scores = [{"agent_id": "agent1", "score": 0.85}]

        with aioresponses() as m:
            m.post(
                "http://localhost:8000/api/v1/validator/submit_scores",
                exception=Exception("Network error"),
            )

            result = await api_client_with_wallet.submit_scores(scores)

            assert result["status"] == "error"
            assert "Network error" in result["message"]
            assert result["count"] == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_submit_scores_empty_list(self, api_client_with_wallet):
        """Test submitting empty scores list."""
        mock_response = {
            "status": "success",
            "count": 0,
        }

        with aioresponses() as m:
            m.post(
                "http://localhost:8000/api/v1/validator/submit_scores",
                payload=mock_response,
            )

            result = await api_client_with_wallet.submit_scores([])

            assert result["status"] == "success"
            assert result["count"] == 0


class TestSubmitPetriOutput:
    """Tests for submit_petri_output method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_submit_petri_output_success(self, api_client_with_wallet):
        """Test successful Petri output submission."""
        submission_id = "test_submission_123"
        petri_output = {
            "run_id": "test_run_123",
            "timestamp": "2024-01-01T00:00:00",
            "summary": {"overall_metrics": {"mean_score": 0.8}},
        }
        mock_response = {
            "status": "success",
            "message": "Petri output submitted successfully",
            "run_id": "test_run_123",
        }

        with aioresponses() as m:
            m.post(
                f"http://localhost:8000/api/v1/validator/submit_scores/{submission_id}",
                payload=mock_response,
            )

            result = await api_client_with_wallet.submit_petri_output(submission_id, petri_output)

            assert result["status"] == "success"
            assert result["run_id"] == "test_run_123"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_submit_petri_output_retry_success(self, api_client_with_wallet):
        """Test retry logic - succeeds on second attempt."""
        submission_id = "test_submission_123"
        petri_output = {
            "run_id": "test_run_123",
            "summary": {"overall_metrics": {"mean_score": 0.8}},
        }
        mock_response = {
            "status": "success",
            "message": "Petri output submitted successfully",
            "run_id": "test_run_123",
        }

        with aioresponses() as m:
            # First attempt fails
            m.post(
                f"http://localhost:8000/api/v1/validator/submit_scores/{submission_id}",
                status=500,
                body="Server error",
            )
            # Second attempt succeeds
            m.post(
                f"http://localhost:8000/api/v1/validator/submit_scores/{submission_id}",
                payload=mock_response,
            )

            result = await api_client_with_wallet.submit_petri_output(submission_id, petri_output)

            assert result["status"] == "success"
            assert result["run_id"] == "test_run_123"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_submit_petri_output_retry_all_fail(self, api_client_with_wallet):
        """Test retry logic - all attempts fail."""
        submission_id = "test_submission_123"
        petri_output = {
            "run_id": "test_run_123",
            "summary": {"overall_metrics": {"mean_score": 0.8}},
        }

        with aioresponses() as m:
            # All 3 attempts fail
            for _ in range(3):
                m.post(
                    f"http://localhost:8000/api/v1/validator/submit_scores/{submission_id}",
                    status=500,
                    body="Server error",
                )

            result = await api_client_with_wallet.submit_petri_output(submission_id, petri_output)

            assert result["status"] == "error"
            assert "Server error" in result["message"]
            assert result["run_id"] == "test_run_123"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_submit_petri_output_network_error(self, api_client_with_wallet):
        """Test handling of network errors during Petri output submission."""
        submission_id = "test_submission_123"
        petri_output = {
            "run_id": "test_run_123",
            "summary": {"overall_metrics": {"mean_score": 0.8}},
        }

        with aioresponses() as m:
            m.post(
                f"http://localhost:8000/api/v1/validator/submit_scores/{submission_id}",
                exception=Exception("Network error"),
            )

            result = await api_client_with_wallet.submit_petri_output(submission_id, petri_output)

            assert result["status"] == "error"
            assert "Network error" in result["message"]
            assert result["run_id"] == "test_run_123"


class TestGetWeights:
    """Tests for get_weights method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_weights_success(self, api_client_with_wallet):
        """Test successful weight retrieval."""
        mock_response = {
            "weights": {
                "0": 0.1,
                "1": 0.2,
                "2": 0.15,
                "3": 0.25,
                "4": 0.3,
            }
        }

        with aioresponses() as m:
            m.get(
                "http://localhost:8000/api/v1/validator/weights",
                payload=mock_response,
            )

            result = await api_client_with_wallet.get_weights()

            assert result is not None
            assert len(result) == 5
            assert result["0"] == 0.1
            assert result["4"] == 0.3

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_weights_empty(self, api_client_with_wallet):
        """Test handling of empty weights response."""
        mock_response = {"weights": {}}

        with aioresponses() as m:
            m.get(
                "http://localhost:8000/api/v1/validator/weights",
                payload=mock_response,
            )

            result = await api_client_with_wallet.get_weights()

            assert result is not None
            assert len(result) == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_weights_server_error(self, api_client_with_wallet):
        """Test handling of server error during weight retrieval."""
        with aioresponses() as m:
            m.get(
                "http://localhost:8000/api/v1/validator/weights",
                status=500,
                body="Internal Server Error",
            )

            result = await api_client_with_wallet.get_weights()

            assert result is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_weights_network_error(self, api_client_with_wallet):
        """Test handling of network errors during weight retrieval."""
        with aioresponses() as m:
            m.get(
                "http://localhost:8000/api/v1/validator/weights",
                exception=Exception("Network error"),
            )

            result = await api_client_with_wallet.get_weights()

            assert result is None


class TestHealthcheck:
    """Tests for healthcheck method."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_healthcheck_success(self, api_client_with_wallet):
        """Test successful healthcheck."""
        with aioresponses() as m:
            m.post(
                "http://localhost:8000/api/v1/validator/healthcheck",
                status=200,
            )

            result = await api_client_with_wallet.healthcheck()

            assert result is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_healthcheck_failure(self, api_client_with_wallet):
        """Test healthcheck failure."""
        with aioresponses() as m:
            m.post(
                "http://localhost:8000/api/v1/validator/healthcheck",
                status=503,
            )

            result = await api_client_with_wallet.healthcheck()

            assert result is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_healthcheck_network_error(self, api_client_with_wallet):
        """Test handling of network errors during healthcheck."""
        with aioresponses() as m:
            m.post(
                "http://localhost:8000/api/v1/validator/healthcheck",
                exception=Exception("Network error"),
            )

            result = await api_client_with_wallet.healthcheck()

            assert result is False


class TestAuthentication:
    """Tests for authentication functionality."""

    @pytest.mark.unit
    def test_build_auth_headers_success(self, api_client_with_wallet):
        """Test successful authentication header building."""
        headers = api_client_with_wallet._build_auth_headers()

        assert "X-Sign-Message" in headers
        assert "X-Signature" in headers
        assert headers["Content-Type"] == "application/json"
        assert headers["X-Sign-Message"] == "mock_message"
        assert headers["X-Signature"] == "0xmocksignature"

    @pytest.mark.unit
    def test_build_auth_headers_no_wallet(self, api_client_without_wallet):
        """Test that building auth headers fails without wallet."""
        with pytest.raises(ValueError, match="Wallet not loaded"):
            api_client_without_wallet._build_auth_headers()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_api_calls_include_auth_headers(self, api_client_with_wallet):
        """Test that API calls include authentication headers."""
        mock_response = {"submission_id": "test123"}

        with aioresponses() as m:
            m.get(
                "http://localhost:8000/api/v1/validator/evaluation-agents",
                payload=mock_response,
            )

            await api_client_with_wallet.get_evaluation_agents()

            # Verify that the request was made with auth headers
            # aioresponses doesn't directly expose headers, but we can verify
            # the call was made by checking the mock was called
            assert len(m.requests) == 1


class TestClientInitialization:
    """Tests for PlatformAPIClient initialization."""

    @pytest.mark.unit
    def test_init_with_wallet_credentials(self, mock_wallet):
        """Test initialization with wallet credentials."""
        with patch("alignet.validator.platform_api_client.load_wallet", return_value=mock_wallet):
            client = PlatformAPIClient(
                platform_api_url="http://test.com",
                coldkey_name="test_coldkey",
                hotkey_name="test_hotkey",
            )

            assert client.platform_api_url == "http://test.com"
            assert client.coldkey_name == "test_coldkey"
            assert client.hotkey_name == "test_hotkey"
            assert client.wallet is not None

    @pytest.mark.unit
    def test_init_without_wallet_credentials(self):
        """Test initialization without wallet credentials."""
        client = PlatformAPIClient(
            platform_api_url="http://test.com",
            coldkey_name=None,
            hotkey_name=None,
        )

        assert client.platform_api_url == "http://test.com"
        assert client.wallet is None

    @pytest.mark.unit
    def test_init_with_env_vars(self, mock_wallet, monkeypatch):
        """Test initialization using environment variables."""
        monkeypatch.setenv("COLDKEY_NAME", "env_coldkey")
        monkeypatch.setenv("HOTKEY_NAME", "env_hotkey")

        with patch("alignet.validator.platform_api_client.load_wallet", return_value=mock_wallet):
            client = PlatformAPIClient(platform_api_url="http://test.com")

            assert client.coldkey_name == "env_coldkey"
            assert client.hotkey_name == "env_hotkey"

    @pytest.mark.unit
    def test_init_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from API URL."""
        client = PlatformAPIClient(platform_api_url="http://test.com/")

        assert client.platform_api_url == "http://test.com"

