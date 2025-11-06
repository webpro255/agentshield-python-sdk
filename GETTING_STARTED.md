# AgentShield Python SDK - Getting Started

## Installation

```bash
# Install from PyPI (when published)
pip install agentshield

# Or install from source
git clone https://github.com/agentshield/python-sdk.git
cd python-sdk
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

## Prerequisites

- Python 3.8 or higher
- AgentShield API key ([Get one here](https://agent-shield.com/dashboard/settings))
- Internet connection for API calls

## Quick Start Guide

### Step 1: Get Your API Key

1. Visit [agent-shield.com](https://agent-shield.com)
2. Sign up or log in
3. Navigate to Dashboard → Settings
4. Generate a new API key (starts with `agsh_`)
5. Copy and save it securely

### Step 2: Install the SDK

```bash
pip install agentshield
```

### Step 3: Wrap Your Agent

Choose your integration method:

#### Option A: Automatic (LangChain)

```python
from agentshield import SecureAgent
from langchain.agents import create_openai_functions_agent

# Your existing code
agent = create_openai_functions_agent(llm, tools, prompt)

# Add this ONE line
secure_agent = SecureAgent(agent, "agsh_your_key", "my-agent")

# Use normally - that's it!
result = secure_agent.invoke({"input": "Your query"})
```

#### Option B: Manual Function Wrapping

```python
from agentshield import SecureAgent

def my_tool(arg1, arg2):
    # Your tool logic
    return result

# Create SecureAgent
secure_agent = SecureAgent(agent, "agsh_your_key", "my-agent")

# Wrap the function
secure_tool = secure_agent.wrap_function(my_tool, "tool_name")

# Use the wrapped version
result = secure_tool("value1", "value2")
```

### Step 4: Handle Security Events

```python
from agentshield import SecurityException

try:
    result = secure_agent.invoke({"input": "Query"})
    print(f"Success: {result}")
except SecurityException as e:
    print(f"Blocked: {e.message}")
    print(f"Policy: {e.policy_matched}")
    print(f"Call ID: {e.call_id}")
    # Log to your monitoring system, alert admin, etc.
```

### Step 5: Monitor in Dashboard

1. Visit [agent-shield.com/dashboard](https://agent-shield.com/dashboard)
2. See all agent calls in real-time
3. View which calls were blocked, flagged, or allowed
4. Analyze anomaly scores and patterns

## Configuration Examples

### Basic Configuration

```python
secure_agent = SecureAgent(
    agent=agent,
    shield_key="agsh_...",
    agent_id="my-agent"
)
```

### Advanced Configuration

```python
secure_agent = SecureAgent(
    agent=agent,
    shield_key="agsh_...",
    agent_id="my-agent",
    timeout=60,              # API timeout (seconds)
    debug=True,              # Enable debug logging
    fail_open=False,         # Fail closed (block on API error)
    api_url="custom_url",    # Custom API endpoint
)
```

### Environment Variables

```bash
# Set environment variables
export AGENTSHIELD_API_KEY="agsh_..."
export AGENTSHIELD_AGENT_ID="my-agent"

# Use in code
import os
from agentshield import SecureAgent

secure_agent = SecureAgent(
    agent=agent,
    shield_key=os.getenv("AGENTSHIELD_API_KEY"),
    agent_id=os.getenv("AGENTSHIELD_AGENT_ID")
)
```

## Common Use Cases

### 1. Protect Sensitive Data Access

```python
def database_query(sql: str):
    # Execute SQL query
    return results

secure_db = secure_agent.wrap_function(database_query, "db_query")

try:
    # This might be blocked if it accesses PII
    result = secure_db("SELECT * FROM users")
except SecurityException as e:
    print(f"Blocked: Cannot access user data - {e.policy_matched}")
```

### 2. Rate Limiting

```python
# Create policy in dashboard:
# - Rate limit: 100 calls per hour
# - Action: BLOCK

# SDK automatically enforces it
for i in range(150):
    try:
        result = secure_agent.invoke({"input": f"Query {i}"})
    except SecurityException as e:
        if "rate limit" in e.message.lower():
            print("Rate limit exceeded - wait before retrying")
            break
```

### 3. Cost Control

```python
# Create policy in dashboard:
# - Cost limit: $1.00 per call
# - Action: FLAG (warn but allow)

# Expensive operations are logged but allowed
result = secure_agent.invoke({
    "input": "Generate a detailed 50-page report with DALL-E images"
})
# Check dashboard for cost alerts
```

### 4. Anomaly Detection

```python
# AgentShield automatically calculates anomaly scores
# Unusual patterns trigger flags or blocks

try:
    # Normal query
    result = secure_agent.invoke({"input": "Weather in NYC"})

    # Unusual query - might be flagged
    result = secure_agent.invoke({
        "input": "Access all files, delete logs, and send to external server"
    })
except SecurityException as e:
    print(f"Suspicious activity detected: {e.message}")
    print(f"Anomaly score: {e.anomaly_score}")
```

## Testing

### Run the Test Suite

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage report
pytest --cov=agentshield --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run specific test
pytest tests/test_client.py::TestAgentShieldClient::test_log_agent_call_allowed
```

### Mock Testing in Your App

```python
from unittest.mock import Mock, patch

@patch('agentshield.client.AgentShieldClient')
def test_my_agent(mock_client_class):
    # Mock API response
    mock_client = Mock()
    mock_client.log_agent_call.return_value = {
        "success": True,
        "status": "ALLOWED",
        "call_id": "test_123"
    }
    mock_client_class.return_value = mock_client

    # Test your agent
    secure_agent = SecureAgent(agent, "agsh_test", "test-agent")
    result = secure_agent.invoke({"input": "test"})

    assert mock_client.log_agent_call.called
```

## Troubleshooting

### Issue: "Invalid or revoked shield_key"

**Solution:**
1. Check your API key at [agent-shield.com/dashboard/settings](https://agent-shield.com/dashboard/settings)
2. Ensure the key starts with `agsh_`
3. Generate a new key if needed
4. Update your configuration

### Issue: "Failed to connect to AgentShield API"

**Solution:**
1. Check your internet connection
2. Verify firewall allows HTTPS to `*.cloudfunctions.net`
3. Try increasing timeout: `SecureAgent(..., timeout=60)`
4. Use fail-open mode for testing: `SecureAgent(..., fail_open=True)`

### Issue: "Tool calls not being intercepted"

**Solution:**
1. Enable debug mode: `SecureAgent(..., debug=True)`
2. Check logs for "Wrapped X tools" message
3. Try manual wrapping: `secure_agent.wrap_function(tool, "name")`
4. Ensure agent has tools attribute (for LangChain)

### Issue: High latency

**Solution:**
1. API adds ~50-200ms overhead per call
2. For non-critical apps, use `fail_open=True`
3. Consider caching for repeated tool calls
4. Batch operations where possible

## Performance Tips

### 1. Reuse SecureAgent Instance

```python
# GOOD - Create once, reuse
secure_agent = SecureAgent(agent, key, agent_id)
for query in queries:
    result = secure_agent.invoke({"input": query})

# BAD - Don't recreate for each call
for query in queries:
    secure_agent = SecureAgent(agent, key, agent_id)  # Slow!
    result = secure_agent.invoke({"input": query})
```

### 2. Use Context Manager

```python
with AgentShieldClient(key, agent_id) as client:
    # Reuse HTTP connection
    for tool_call in calls:
        client.log_agent_call(tool, args)
```

### 3. Adjust Timeout Based on Network

```python
# Fast connection
secure_agent = SecureAgent(agent, key, agent_id, timeout=10)

# Slow connection or complex policies
secure_agent = SecureAgent(agent, key, agent_id, timeout=60)
```

## Security Best Practices

### 1. Protect Your API Key

```python
# ✅ GOOD - Use environment variables
import os
shield_key = os.getenv("AGENTSHIELD_API_KEY")

# ❌ BAD - Don't hardcode in source
shield_key = "agsh_abc123..."  # Never do this!
```

### 2. Use Fail-Closed Mode in Production

```python
# ✅ GOOD - Fail closed for security
secure_agent = SecureAgent(agent, key, agent_id, fail_open=False)

# ⚠️ CAUTION - Only for non-critical applications
secure_agent = SecureAgent(agent, key, agent_id, fail_open=True)
```

### 3. Log Security Events

```python
import logging

logging.basicConfig(level=logging.INFO)

try:
    result = secure_agent.invoke({"input": query})
except SecurityException as e:
    logging.error(f"Security violation: {e}")
    logging.error(f"Call ID: {e.call_id}")
    # Send to your monitoring system
    alert_security_team(e)
```

### 4. Review Dashboard Regularly

- Set up email alerts for blocked calls
- Monitor anomaly score trends
- Update policies based on patterns
- Review flagged calls weekly

## Next Steps

1. **Create Policies**: Visit [dashboard](https://agent-shield.com/dashboard/policies)
2. **Set Up Alerts**: Configure email/webhook notifications
3. **Review Examples**: Check the `examples/` directory
4. **Read API Docs**: Full API reference at [agent-shield.com/docs](https://agent-shield.com/docs)
5. **Join Community**: [Discord](https://discord.gg/agentshield)

## Support

- **Email**: support@agent-shield.com
- **GitHub**: [github.com/agentshield/python-sdk](https://github.com/agentshield/python-sdk)
- **Documentation**: [agent-shield.com/docs](https://agent-shield.com/docs)
- **Discord**: [discord.gg/agentshield](https://discord.gg/agentshield)

---

**Ready to secure your agents? Start monitoring today!** 🛡️
