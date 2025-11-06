"""
Tests for AgentShield API Client
"""

import pytest
from unittest.mock import Mock, patch
import requests

from agentshield.client import AgentShieldClient
from agentshield.exceptions import (
    APIKeyError,
    NetworkError,
    PolicyEvaluationError,
    ConfigurationError,
)


class TestAgentShieldClient:
    """Test AgentShieldClient functionality."""

    def test_initialization_success(self):
        """Test successful client initialization."""
        client = AgentShieldClient(
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        assert client.shield_key == "agsh_test123"
        assert client.agent_id == "test-agent"
        assert client.api_url == AgentShieldClient.DEFAULT_API_URL
        assert client.timeout == AgentShieldClient.DEFAULT_TIMEOUT

    def test_initialization_custom_url(self):
        """Test initialization with custom API URL."""
        custom_url = "https://custom.api.com/logAgentCall"
        client = AgentShieldClient(
            shield_key="agsh_test123",
            agent_id="test-agent",
            api_url=custom_url
        )

        assert client.api_url == custom_url

    def test_initialization_missing_shield_key(self):
        """Test that missing shield_key raises ConfigurationError."""
        with pytest.raises(ConfigurationError):
            AgentShieldClient(
                shield_key="",
                agent_id="test-agent"
            )

    def test_initialization_missing_agent_id(self):
        """Test that missing agent_id raises ConfigurationError."""
        with pytest.raises(ConfigurationError):
            AgentShieldClient(
                shield_key="agsh_test123",
                agent_id=""
            )

    @patch('agentshield.client.requests.Session.post')
    def test_log_agent_call_allowed(self, mock_post):
        """Test successful API call with ALLOWED status."""
        # Mock successful response - Cloud Functions v2 format wraps in 'result'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "success": True,
                "status": "ALLOWED",
                "message": "Agent call allowed",
                "call_id": "call_123",
                "policy_matched": None,
                "anomaly_score": 15.5,
            }
        }
        mock_post.return_value = mock_response

        client = AgentShieldClient(
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        result = client.log_agent_call(
            tool_name="web_search",
            tool_args={"query": "test query"}
        )

        assert result["success"] is True
        assert result["status"] == "ALLOWED"
        assert result["call_id"] == "call_123"
        assert mock_post.called

    @patch('agentshield.client.requests.Session.post')
    def test_log_agent_call_blocked(self, mock_post):
        """Test API call with BLOCKED status."""
        # Cloud Functions v2 format wraps in 'result'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "success": True,
                "status": "BLOCKED",
                "message": "Blocked by security policy",
                "call_id": "call_456",
                "policy_matched": "Block PII Access",
                "anomaly_score": 95.0,
            }
        }
        mock_post.return_value = mock_response

        client = AgentShieldClient(
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        result = client.log_agent_call(
            tool_name="database_query",
            tool_args={"query": "SELECT * FROM users"}
        )

        assert result["status"] == "BLOCKED"
        assert result["policy_matched"] == "Block PII Access"

    @patch('agentshield.client.requests.Session.post')
    def test_log_agent_call_invalid_api_key(self, mock_post):
        """Test that invalid API key raises APIKeyError."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = '{"message": "Invalid or revoked shield_key"}'
        mock_response.json.return_value = {
            "message": "Invalid or revoked shield_key"
        }
        mock_post.return_value = mock_response

        client = AgentShieldClient(
            shield_key="agsh_invalid",
            agent_id="test-agent"
        )

        with pytest.raises(APIKeyError) as exc_info:
            client.log_agent_call(
                tool_name="test_tool",
                tool_args={}
            )

        assert "Invalid or revoked" in str(exc_info.value)

    @patch('agentshield.client.requests.Session.post')
    def test_log_agent_call_network_timeout(self, mock_post):
        """Test that timeout raises NetworkError."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        client = AgentShieldClient(
            shield_key="agsh_test123",
            agent_id="test-agent",
            timeout=5
        )

        with pytest.raises(NetworkError) as exc_info:
            client.log_agent_call(
                tool_name="test_tool",
                tool_args={}
            )

        assert "timed out" in str(exc_info.value)

    @patch('agentshield.client.requests.Session.post')
    def test_log_agent_call_connection_error(self, mock_post):
        """Test that connection error raises NetworkError."""
        mock_post.side_effect = requests.exceptions.ConnectionError(
            "Failed to connect"
        )

        client = AgentShieldClient(
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        with pytest.raises(NetworkError) as exc_info:
            client.log_agent_call(
                tool_name="test_tool",
                tool_args={}
            )

        assert "Failed to connect" in str(exc_info.value)

    @patch('agentshield.client.requests.Session.post')
    def test_log_agent_call_server_error(self, mock_post):
        """Test that server error raises PolicyEvaluationError."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = '{"message": "Internal server error"}'
        mock_response.json.return_value = {
            "message": "Internal server error"
        }
        mock_post.return_value = mock_response

        client = AgentShieldClient(
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        with pytest.raises(PolicyEvaluationError) as exc_info:
            client.log_agent_call(
                tool_name="test_tool",
                tool_args={}
            )

        assert "Internal server error" in str(exc_info.value)

    @patch('agentshield.client.requests.Session.post')
    def test_log_agent_call_with_execution_time(self, mock_post):
        """Test API call with execution time."""
        # Cloud Functions v2 format wraps in 'result'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "success": True,
                "status": "ALLOWED",
                "call_id": "call_789",
            }
        }
        mock_post.return_value = mock_response

        client = AgentShieldClient(
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        result = client.log_agent_call(
            tool_name="compute",
            tool_args={"input": "data"},
            execution_time_ms=1250
        )

        # Check that execution_time_ms was sent in 'data' wrapper
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        assert "data" in payload
        assert payload["data"]["execution_time_ms"] == 1250

    def test_context_manager(self):
        """Test client can be used as context manager."""
        with AgentShieldClient(
            shield_key="agsh_test123",
            agent_id="test-agent"
        ) as client:
            assert client is not None
            assert client.session is not None

    @patch('agentshield.client.requests.Session.post')
    def test_payload_structure(self, mock_post):
        """Test that request payload has correct structure (Cloud Functions v2 format)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "success": True,
                "status": "ALLOWED",
                "call_id": "test_id",
            }
        }
        mock_post.return_value = mock_response

        client = AgentShieldClient(
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        client.log_agent_call(
            tool_name="test_tool",
            tool_args={"arg1": "value1", "arg2": 42}
        )

        # Verify payload structure - Cloud Functions v2 wraps in 'data'
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]

        # Check outer structure
        assert "data" in payload

        # Check inner data structure
        data = payload["data"]
        assert "shield_key" in data
        assert "agent_id" in data
        assert "tool_name" in data
        assert "tool_args" in data
        assert "timestamp" in data

        assert data["shield_key"] == "agsh_test123"
        assert data["agent_id"] == "test-agent"
        assert data["tool_name"] == "test_tool"
        assert data["tool_args"] == {"arg1": "value1", "arg2": 42}
