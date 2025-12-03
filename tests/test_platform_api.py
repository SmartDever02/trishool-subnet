"""
Tests for platform API endpoints using pytest.

Tests for /upload and /evaluation-agents endpoints.
"""
import pytest
import json
import aiohttp
from tests.conftest import test_config, sample_agent_content
from alignet.cli.bts_signature import load_wallet, build_pair_auth_payload


class PlatformAPITester:
    """Test helper class for platform API endpoints."""

    def __init__(
        self,
        platform_api_url: str,
        coldkey_name: str,
        hotkey_name: str,
        network: str,
        netuid: int,
        slot: str,
    ):
        self.platform_api_url = platform_api_url.rstrip("/")
        self.coldkey_name = coldkey_name
        self.hotkey_name = hotkey_name
        self.network = network
        self.netuid = netuid
        self.slot = slot

    def _build_auth_payload(self):
        """Build authentication payload with signature."""
        wallet = load_wallet(self.coldkey_name, self.hotkey_name)
        payload = build_pair_auth_payload(
            network=self.network,
            netuid=self.netuid,
            slot=self.slot,
            wallet_name=self.coldkey_name,
            wallet_hotkey=self.hotkey_name,
        )
        return {
            "hotkey": wallet.hotkey.ss58_address,
            "message": payload["message"],
            "signature": payload["signature"],
            "expires_at": payload["expires_at"],
        }

    async def upload_agent(
        self, agent_content: str = None, filename: str = "agent.txt"
    ):
        """
        Upload a miner agent to the platform.

        Args:
            agent_content: Content of the agent file
            filename: Name of the file to upload (must be .txt)

        Returns:
            Response JSON from the API
        """
        if agent_content is None:
            agent_content = sample_agent_content()

        auth_data = self._build_auth_payload()

        form_data = aiohttp.FormData()
        form_data.add_field(
            "agent_file",
            agent_content.encode("utf-8"),
            filename=filename,
            content_type="text/plain",
        )
        form_data.add_field("message", auth_data["message"])
        form_data.add_field("expires_at", str(int(auth_data["expires_at"])))
        form_data.add_field("signature", auth_data["signature"])

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.platform_api_url}/api/v1/miner/upload",
                data=form_data,
            ) as response:
                response_json = await response.json()
                return {
                    "status_code": response.status,
                    "data": response_json,
                }

    async def get_evaluation_agents(self):
        """
        Get evaluation agents (Petri config) from the platform.

        Returns:
            Response JSON from the API (PetriConfigResponse or None)
        """
        auth_data = self._build_auth_payload()

        headers = {
            "X-Sign-Message": auth_data["message"],
            "X-Signature": auth_data["signature"],
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.platform_api_url}/api/v1/validator/evaluation-agents",
                headers=headers,
            ) as response:
                response_json = await response.json()
                return {
                    "status_code": response.status,
                    "data": response_json,
                }


@pytest.fixture
def api_tester(test_config):
    """Fixture providing PlatformAPITester instance."""
    return PlatformAPITester(
        platform_api_url=test_config["platform_api_url"],
        coldkey_name=test_config["coldkey_name"],
        hotkey_name=test_config["hotkey_name"],
        network=test_config["network"],
        netuid=test_config["netuid"],
        slot=test_config["slot"],
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_agent(api_tester, sample_agent_content):
    """Test uploading a miner agent to the platform."""
    result = await api_tester.upload_agent(agent_content=sample_agent_content)

    assert result["status_code"] in [200, 201], f"Expected 200/201, got {result['status_code']}"
    assert "data" in result
    # Check if response contains expected fields (may vary based on API)
    assert isinstance(result["data"], dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_evaluation_agents(api_tester):
    """Test getting evaluation agents from the platform."""
    result = await api_tester.get_evaluation_agents()

    assert result["status_code"] in [200, 404], f"Expected 200/404, got {result['status_code']}"
    assert "data" in result
    # If status is 200, check for expected fields
    if result["status_code"] == 200:
        # Response might be empty dict or contain submission data
        assert isinstance(result["data"], dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_agent_with_custom_content(api_tester):
    """Test uploading agent with custom content."""
    custom_content = "# Custom agent code\ndef custom_function():\n    return 'custom'\n"
    result = await api_tester.upload_agent(
        agent_content=custom_content, filename="custom_agent.txt"
    )

    assert result["status_code"] in [200, 201]
    assert "data" in result


@pytest.mark.asyncio
@pytest.mark.integration
async def test_upload_agent_authentication(api_tester, sample_agent_content):
    """Test that authentication is required for agent upload."""
    # This test verifies that the auth payload is built correctly
    auth_data = api_tester._build_auth_payload()

    assert "hotkey" in auth_data
    assert "message" in auth_data
    assert "signature" in auth_data
    assert "expires_at" in auth_data
    assert len(auth_data["signature"]) > 0

