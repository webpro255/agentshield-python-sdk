"""
Tests for AgentShield Tool Interceptor
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from agentshield.interceptor import SecureAgent
from agentshield.exceptions import (
    SecurityException,
    ConfigurationError,
)


class TestSecureAgent:
    """Test SecureAgent interceptor functionality."""

    def test_initialization_success(self):
        """Test successful SecureAgent initialization."""
        agent = Mock()
        secure_agent = SecureAgent(
            agent=agent,
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        assert secure_agent.agent == agent
        assert secure_agent.shield_key == "agsh_test123"
        assert secure_agent.agent_id == "test-agent"
        assert secure_agent.client is not None

    def test_initialization_missing_shield_key(self):
        """Test that missing shield_key raises ConfigurationError."""
        agent = Mock()

        with pytest.raises(ConfigurationError):
            SecureAgent(
                agent=agent,
                shield_key="",
                agent_id="test-agent"
            )

    def test_initialization_missing_agent_id(self):
        """Test that missing agent_id raises ConfigurationError."""
        agent = Mock()

        with pytest.raises(ConfigurationError):
            SecureAgent(
                agent=agent,
                shield_key="agsh_test123",
                agent_id=""
            )

    @patch('agentshield.interceptor.AgentShieldClient')
    def test_wrap_function_allowed(self, mock_client_class):
        """Test wrapping a function that is allowed to execute."""
        # Mock API response - ALLOWED
        mock_client = Mock()
        mock_client.log_agent_call.return_value = {
            "success": True,
            "status": "ALLOWED",
            "call_id": "call_123",
            "message": "Allowed",
        }
        mock_client_class.return_value = mock_client

        # Create test function
        def test_function(x, y):
            return x + y

        # Wrap with SecureAgent
        agent = Mock()
        secure_agent = SecureAgent(
            agent=agent,
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        wrapped_func = secure_agent.wrap_function(test_function, "add")

        # Call wrapped function
        result = wrapped_func(2, 3)

        # Verify function executed
        assert result == 5

        # Verify API was called
        assert mock_client.log_agent_call.called
        call_args = mock_client.log_agent_call.call_args
        assert call_args.kwargs["tool_name"] == "add"

    @patch('agentshield.interceptor.AgentShieldClient')
    def test_wrap_function_blocked(self, mock_client_class):
        """Test wrapping a function that is blocked."""
        # Mock API response - BLOCKED
        mock_client = Mock()
        mock_client.log_agent_call.return_value = {
            "success": True,
            "status": "BLOCKED",
            "call_id": "call_456",
            "policy_matched": "Block PII",
            "message": "Blocked by policy",
        }
        mock_client_class.return_value = mock_client

        # Create test function
        def sensitive_function(data):
            return f"Processing: {data}"

        # Wrap with SecureAgent
        agent = Mock()
        secure_agent = SecureAgent(
            agent=agent,
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        wrapped_func = secure_agent.wrap_function(sensitive_function, "process_data")

        # Call wrapped function - should raise SecurityException
        with pytest.raises(SecurityException) as exc_info:
            wrapped_func("sensitive data")

        # Verify exception details
        exception = exc_info.value
        assert exception.status == "BLOCKED"
        assert exception.policy_matched == "Block PII"
        assert exception.call_id == "call_456"

        # Verify API was called
        assert mock_client.log_agent_call.called

    @patch('agentshield.interceptor.AgentShieldClient')
    def test_wrap_function_flagged(self, mock_client_class):
        """Test wrapping a function that is flagged but allowed."""
        # Mock API response - FLAGGED
        mock_client = Mock()
        mock_client.log_agent_call.return_value = {
            "success": True,
            "status": "FLAGGED",
            "call_id": "call_789",
            "policy_matched": "Suspicious Activity",
            "message": "Flagged for review",
        }
        mock_client_class.return_value = mock_client

        # Create test function
        def test_function(x):
            return x * 2

        # Wrap with SecureAgent
        agent = Mock()
        secure_agent = SecureAgent(
            agent=agent,
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        wrapped_func = secure_agent.wrap_function(test_function, "multiply")

        # Call wrapped function - should execute despite flag
        result = wrapped_func(5)

        # Verify function executed
        assert result == 10

        # Verify API was called
        assert mock_client.log_agent_call.called

    @patch('agentshield.interceptor.AgentShieldClient')
    def test_wrap_function_pending_approval(self, mock_client_class):
        """Test wrapping a function that requires approval."""
        # Mock API response - PENDING_APPROVAL
        mock_client = Mock()
        mock_client.log_agent_call.return_value = {
            "success": True,
            "status": "PENDING_APPROVAL",
            "call_id": "call_999",
            "message": "Requires manual approval",
        }
        mock_client_class.return_value = mock_client

        # Create test function
        def critical_function():
            return "executed"

        # Wrap with SecureAgent
        agent = Mock()
        secure_agent = SecureAgent(
            agent=agent,
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        wrapped_func = secure_agent.wrap_function(critical_function, "critical_op")

        # Call wrapped function - should raise SecurityException
        with pytest.raises(SecurityException) as exc_info:
            wrapped_func()

        # Verify exception details
        exception = exc_info.value
        assert exception.status == "PENDING_APPROVAL"

    @patch('agentshield.interceptor.AgentShieldClient')
    def test_fail_open_mode(self, mock_client_class):
        """Test fail-open mode allows execution on API error."""
        # Mock API error
        mock_client = Mock()
        mock_client.log_agent_call.side_effect = Exception("API unavailable")
        mock_client_class.return_value = mock_client

        # Create test function
        def test_function():
            return "success"

        # Wrap with SecureAgent in fail-open mode
        agent = Mock()
        secure_agent = SecureAgent(
            agent=agent,
            shield_key="agsh_test123",
            agent_id="test-agent",
            fail_open=True
        )

        wrapped_func = secure_agent.wrap_function(test_function, "test")

        # Call wrapped function - should execute despite API error
        result = wrapped_func()

        # Verify function executed
        assert result == "success"

    @patch('agentshield.interceptor.AgentShieldClient')
    def test_fail_closed_mode(self, mock_client_class):
        """Test fail-closed mode blocks execution on API error."""
        # Mock API error
        mock_client = Mock()
        mock_client.log_agent_call.side_effect = Exception("API unavailable")
        mock_client_class.return_value = mock_client

        # Create test function
        def test_function():
            return "success"

        # Wrap with SecureAgent in fail-closed mode (default)
        agent = Mock()
        secure_agent = SecureAgent(
            agent=agent,
            shield_key="agsh_test123",
            agent_id="test-agent",
            fail_open=False
        )

        wrapped_func = secure_agent.wrap_function(test_function, "test")

        # Call wrapped function - should raise SecurityException
        with pytest.raises(SecurityException) as exc_info:
            wrapped_func()

        # Verify exception mentions API error
        assert "API error" in str(exc_info.value)

    @patch('agentshield.interceptor.AgentShieldClient')
    def test_wrap_langchain_agent(self, mock_client_class):
        """Test wrapping LangChain agent tools."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Create mock LangChain agent with tools
        tool1 = Mock()
        tool1.name = "search"
        tool1._run = Mock(return_value="search result")

        tool2 = Mock()
        tool2.name = "calculator"
        tool2._run = Mock(return_value=42)

        agent = Mock()
        agent.tools = [tool1, tool2]

        # Wrap agent
        secure_agent = SecureAgent(
            agent=agent,
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        # Verify tools were wrapped
        assert len(secure_agent.agent.tools) == 2

    @patch('agentshield.interceptor.AgentShieldClient')
    def test_extract_args(self, mock_client_class):
        """Test argument extraction and serialization."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        agent = Mock()
        secure_agent = SecureAgent(
            agent=agent,
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        # Test various argument types
        args = (42, "hello", [1, 2, 3])
        kwargs = {"key1": "value1", "key2": {"nested": "dict"}}

        extracted = secure_agent._extract_args(args, kwargs)

        # Verify extraction
        assert extracted["arg_0"] == 42
        assert extracted["arg_1"] == "hello"
        assert extracted["arg_2"] == [1, 2, 3]
        assert extracted["key1"] == "value1"
        assert extracted["key2"]["nested"] == "dict"

    @patch('agentshield.interceptor.AgentShieldClient')
    def test_serialize_value(self, mock_client_class):
        """Test value serialization for JSON."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        agent = Mock()
        secure_agent = SecureAgent(
            agent=agent,
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        # Test primitive types
        assert secure_agent._serialize_value("string") == "string"
        assert secure_agent._serialize_value(42) == 42
        assert secure_agent._serialize_value(3.14) == 3.14
        assert secure_agent._serialize_value(True) is True
        assert secure_agent._serialize_value(None) is None

        # Test collections
        assert secure_agent._serialize_value([1, 2, 3]) == [1, 2, 3]
        assert secure_agent._serialize_value({"a": 1}) == {"a": 1}

        # Test object conversion to string
        class CustomObject:
            def __str__(self):
                return "custom"

        obj = CustomObject()
        assert secure_agent._serialize_value(obj) == "custom"

    @patch('agentshield.interceptor.AgentShieldClient')
    def test_proxy_attribute_access(self, mock_client_class):
        """Test that attributes are proxied to wrapped agent."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Create agent with custom attributes
        agent = Mock()
        agent.custom_method = Mock(return_value="result")
        agent.custom_attr = "value"

        secure_agent = SecureAgent(
            agent=agent,
            shield_key="agsh_test123",
            agent_id="test-agent"
        )

        # Access attributes through SecureAgent
        assert secure_agent.custom_attr == "value"
        assert secure_agent.custom_method() == "result"
