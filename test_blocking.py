#!/usr/bin/env python3
"""
Test script to verify AgentShield properly blocks tool execution.

This test simulates the scenario:
1. Policy blocks calls containing 'production' keyword
2. Agent tries to call a database query tool with 'production'
3. SDK should raise SecurityException BEFORE the tool executes
4. The tool's actual function should NEVER run
"""

import logging
from unittest.mock import MagicMock, Mock
from agentshield.interceptor import SecureAgent
from agentshield.exceptions import SecurityException

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)


def test_blocking_prevents_execution():
    """Test that BLOCKED status prevents tool execution."""

    print("\n" + "="*70)
    print("TEST: Verify tool execution is blocked when policy says BLOCKED")
    print("="*70 + "\n")

    # Track if the dangerous function was called
    execution_tracker = {"was_executed": False}

    def dangerous_database_query(query: str):
        """Simulated dangerous function that should NEVER execute when blocked."""
        execution_tracker["was_executed"] = True
        print(f"❌ DANGER: Executing database query: {query}")
        return f"Results for: {query}"

    # Create a mock agent with a tool
    mock_agent = MagicMock()
    mock_tool = MagicMock()
    mock_tool.name = "database_query"
    mock_tool._run = dangerous_database_query
    mock_agent.tools = [mock_tool]

    # Create SecureAgent wrapper
    secure_agent = SecureAgent(
        agent=mock_agent,
        shield_key="test_key",
        agent_id="test_agent",
        debug=True,
        fail_open=False  # Important: fail closed for security
    )

    # Mock the API client to return BLOCKED status
    secure_agent.client.log_call = Mock(return_value={
        "status": "BLOCKED",
        "message": "Query contains blocked keyword: 'production'",
        "call_id": "test-call-123",
        "policy_matched": "block_production_queries",
        "success": True
    })

    # Try to execute the dangerous tool
    print("Attempting to execute: database_query('SELECT * FROM production.users')")
    print()

    try:
        # This should raise SecurityException and NOT execute the tool
        result = mock_tool._run("SELECT * FROM production.users")

        # If we get here, the test FAILED
        print("❌ TEST FAILED: Tool executed when it should have been blocked!")
        print(f"   Result: {result}")
        return False

    except SecurityException as e:
        print(f"✅ SecurityException raised (expected): {e.message}")
        print(f"   Policy: {e.policy_matched}")
        print(f"   Call ID: {e.call_id}")
        print(f"   Status: {e.status}")
        print()

        # Verify the dangerous function was NOT executed
        if execution_tracker["was_executed"]:
            print("❌ TEST FAILED: Tool was executed despite BLOCKED status!")
            return False
        else:
            print("✅ TEST PASSED: Tool was NOT executed (blocked successfully)")
            return True

    except Exception as e:
        print(f"❌ TEST FAILED: Unexpected exception: {type(e).__name__}: {e}")
        return False


def test_allowed_permits_execution():
    """Test that ALLOWED status permits tool execution."""

    print("\n" + "="*70)
    print("TEST: Verify tool execution is allowed when policy says ALLOWED")
    print("="*70 + "\n")

    execution_tracker = {"was_executed": False}

    def safe_database_query(query: str):
        """Safe function that should execute when allowed."""
        execution_tracker["was_executed"] = True
        print(f"✅ Executing safe query: {query}")
        return f"Results for: {query}"

    # Create mock agent
    mock_agent = MagicMock()
    mock_tool = MagicMock()
    mock_tool.name = "database_query"
    mock_tool._run = safe_database_query
    mock_agent.tools = [mock_tool]

    # Create SecureAgent wrapper
    secure_agent = SecureAgent(
        agent=mock_agent,
        shield_key="test_key",
        agent_id="test_agent",
        debug=True,
        fail_open=False
    )

    # Mock the API to return ALLOWED status
    secure_agent.client.log_call = Mock(return_value={
        "status": "ALLOWED",
        "message": "Query approved",
        "call_id": "test-call-456",
        "policy_matched": None,
        "success": True
    })

    print("Attempting to execute: database_query('SELECT * FROM development.users')")
    print()

    try:
        result = mock_tool._run("SELECT * FROM development.users")

        if execution_tracker["was_executed"]:
            print(f"✅ TEST PASSED: Tool was executed (allowed)")
            print(f"   Result: {result}")
            return True
        else:
            print("❌ TEST FAILED: Tool was not executed despite ALLOWED status!")
            return False

    except Exception as e:
        print(f"❌ TEST FAILED: Unexpected exception: {type(e).__name__}: {e}")
        return False


def test_flagged_permits_with_warning():
    """Test that FLAGGED status permits execution but logs warning."""

    print("\n" + "="*70)
    print("TEST: Verify tool execution is allowed with warning when FLAGGED")
    print("="*70 + "\n")

    execution_tracker = {"was_executed": False}

    def suspicious_query(query: str):
        """Function that gets flagged but should still execute."""
        execution_tracker["was_executed"] = True
        print(f"⚠️  Executing flagged query: {query}")
        return f"Results for: {query}"

    # Create mock agent
    mock_agent = MagicMock()
    mock_tool = MagicMock()
    mock_tool.name = "database_query"
    mock_tool._run = suspicious_query
    mock_agent.tools = [mock_tool]

    # Create SecureAgent wrapper
    secure_agent = SecureAgent(
        agent=mock_agent,
        shield_key="test_key",
        agent_id="test_agent",
        debug=True,
        fail_open=False
    )

    # Mock the API to return FLAGGED status
    secure_agent.client.log_call = Mock(return_value={
        "status": "FLAGGED",
        "message": "Query contains suspicious pattern",
        "call_id": "test-call-789",
        "policy_matched": "flag_suspicious_queries",
        "success": True
    })

    print("Attempting to execute: database_query('SELECT * FROM users WHERE admin=1')")
    print()

    try:
        result = mock_tool._run("SELECT * FROM users WHERE admin=1")

        if execution_tracker["was_executed"]:
            print(f"✅ TEST PASSED: Flagged tool was executed (with warning)")
            print(f"   Result: {result}")
            return True
        else:
            print("❌ TEST FAILED: Flagged tool was not executed!")
            return False

    except Exception as e:
        print(f"❌ TEST FAILED: Unexpected exception: {type(e).__name__}: {e}")
        return False


def test_missing_status_fails_closed():
    """Test that missing status fails closed (blocks execution)."""

    print("\n" + "="*70)
    print("TEST: Verify missing status fails closed (blocks execution)")
    print("="*70 + "\n")

    execution_tracker = {"was_executed": False}

    def dangerous_function():
        """Function that should NOT execute when status is missing."""
        execution_tracker["was_executed"] = True
        print("❌ DANGER: Function executed despite missing status!")
        return "result"

    # Create mock agent
    mock_agent = MagicMock()
    mock_tool = MagicMock()
    mock_tool.name = "dangerous_tool"
    mock_tool._run = dangerous_function
    mock_agent.tools = [mock_tool]

    # Create SecureAgent wrapper
    secure_agent = SecureAgent(
        agent=mock_agent,
        shield_key="test_key",
        agent_id="test_agent",
        debug=True,
        fail_open=False
    )

    # Mock the API to return response WITHOUT status field
    secure_agent.client.log_call = Mock(return_value={
        "call_id": "test-call-999",
        "success": True
        # NOTE: No "status" field!
    })

    print("Attempting to execute tool with API response missing 'status' field")
    print()

    try:
        result = mock_tool._run()

        # If we get here, the test FAILED
        print("❌ TEST FAILED: Tool executed despite missing status!")
        return False

    except SecurityException as e:
        print(f"✅ SecurityException raised (expected): {e.message}")
        print(f"   Status: {e.status}")
        print()

        if execution_tracker["was_executed"]:
            print("❌ TEST FAILED: Tool was executed despite missing status!")
            return False
        else:
            print("✅ TEST PASSED: Tool was NOT executed (failed closed)")
            return True

    except Exception as e:
        print(f"❌ TEST FAILED: Unexpected exception: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "#"*70)
    print("# AgentShield Interceptor Blocking Test Suite")
    print("#"*70)

    results = []

    # Run all tests
    results.append(("Blocking prevents execution", test_blocking_prevents_execution()))
    results.append(("Allowed permits execution", test_allowed_permits_execution()))
    results.append(("Flagged permits with warning", test_flagged_permits_with_warning()))
    results.append(("Missing status fails closed", test_missing_status_fails_closed()))

    # Print summary
    print("\n" + "#"*70)
    print("# Test Results Summary")
    print("#"*70 + "\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! The interceptor correctly enforces blocking.")
        exit(0)
    else:
        print("\n❌ Some tests failed! The interceptor may not be blocking correctly.")
        exit(1)
