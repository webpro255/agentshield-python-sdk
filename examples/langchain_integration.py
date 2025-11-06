"""
AgentShield + LangChain Integration Example

Demonstrates how to secure a LangChain agent with AgentShield.
"""

from typing import Optional
from agentshield import SecureAgent, SecurityException

# Optional: Uncomment if you have LangChain installed
# from langchain.agents import AgentExecutor, create_openai_functions_agent
# from langchain.tools import Tool
# from langchain_openai import ChatOpenAI
# from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder


def web_search_tool(query: str) -> str:
    """Mock web search tool."""
    return f"Search results for: {query}"


def calculator_tool(expression: str) -> str:
    """Mock calculator tool."""
    try:
        result = eval(expression)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"


def weather_tool(location: str) -> str:
    """Mock weather tool."""
    return f"Weather in {location}: Sunny, 72°F"


def database_query_tool(query: str) -> str:
    """Mock database query tool."""
    return f"Query results: [data for: {query}]"


def email_tool(to: str, subject: str) -> str:
    """Mock email tool."""
    return f"Email sent to {to}: {subject}"


def main_with_langchain():
    """
    Example using actual LangChain (requires langchain package).
    Uncomment this function if you have LangChain installed.
    """
    # Uncomment and modify for real LangChain usage:
    """
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain.tools import Tool
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

    # Configuration
    SHIELD_KEY = "agsh_your_api_key_here"
    AGENT_ID = "langchain-assistant"
    OPENAI_API_KEY = "your_openai_api_key"

    # Define tools
    tools = [
        Tool(
            name="WebSearch",
            func=web_search_tool,
            description="Search the web for information"
        ),
        Tool(
            name="Calculator",
            func=calculator_tool,
            description="Perform mathematical calculations"
        ),
        Tool(
            name="Weather",
            func=weather_tool,
            description="Get weather information for a location"
        ),
        Tool(
            name="DatabaseQuery",
            func=database_query_tool,
            description="Query the database"
        ),
    ]

    # Create LangChain agent
    llm = ChatOpenAI(model="gpt-4", temperature=0, api_key=OPENAI_API_KEY)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Wrap with AgentShield
    secure_agent = SecureAgent(
        agent=agent_executor,
        shield_key=SHIELD_KEY,
        agent_id=AGENT_ID,
        debug=True
    )

    print("🛡️  LangChain agent secured with AgentShield")

    # Use the agent - all tool calls are now monitored
    try:
        result = secure_agent.invoke({
            "input": "What's the weather in San Francisco and calculate 25 * 4?"
        })
        print(f"✓ Result: {result}")
    except SecurityException as e:
        print(f"✗ Blocked: {e}")

    return secure_agent
    """
    pass


def main_mock_example():
    """
    Mock example demonstrating the pattern without requiring LangChain.
    Shows how SecureAgent works with agent-like objects.
    """

    print("=" * 70)
    print("AgentShield + LangChain Integration Example (Mock)")
    print("=" * 70)

    # Configuration
    SHIELD_KEY = "agsh_your_api_key_here"  # Replace with your actual key
    AGENT_ID = "langchain-example-agent"

    # Create a mock agent that simulates LangChain's structure
    class MockLangChainAgent:
        """Mock LangChain agent for demonstration."""

        def __init__(self, tools):
            self.tools = tools
            self.name = "MockLangChainAgent"

        def invoke(self, input_dict: dict) -> dict:
            """Simulate agent invocation."""
            user_input = input_dict.get("input", "")
            print(f"\nAgent processing: {user_input}")

            # Simulate tool usage
            if "search" in user_input.lower():
                result = self.tools[0]._run("AI security")
                return {"output": result}
            elif "calculate" in user_input.lower():
                result = self.tools[1]._run("10 + 5")
                return {"output": result}
            else:
                return {"output": "I can help with searches and calculations."}

    # Create mock tools (simulating LangChain Tool objects)
    class MockTool:
        def __init__(self, name, func):
            self.name = name
            self._run = func

    mock_tools = [
        MockTool("search", web_search_tool),
        MockTool("calculator", calculator_tool),
        MockTool("weather", weather_tool),
    ]

    # Create the agent
    print(f"\n1. Creating LangChain agent with {len(mock_tools)} tools...")
    agent = MockLangChainAgent(tools=mock_tools)
    print("   ✓ Agent created")

    # Wrap with AgentShield
    print(f"\n2. Securing agent with AgentShield (agent_id: {AGENT_ID})...")
    secure_agent = SecureAgent(
        agent=agent,
        shield_key=SHIELD_KEY,
        agent_id=AGENT_ID,
        debug=True,
        fail_open=False,  # Fail closed for security
    )
    print("   ✓ Agent secured - all tool calls will be monitored")

    # Example 1: Safe query
    print("\n3. Example 1: Safe Query")
    print("-" * 70)
    try:
        result = secure_agent.invoke({
            "input": "Search for information about AI safety"
        })
        print(f"   ✓ Success: {result}")
    except SecurityException as e:
        print(f"   ✗ BLOCKED by policy: {e}")

    # Example 2: Potentially sensitive query
    print("\n4. Example 2: Potentially Sensitive Query")
    print("-" * 70)
    try:
        result = secure_agent.invoke({
            "input": "Calculate the risk score for user data"
        })
        print(f"   ✓ Success: {result}")
    except SecurityException as e:
        print(f"   ✗ BLOCKED by policy: {e}")
        print(f"      Policy: {e.policy_matched}")
        print(f"      Call ID: {e.call_id}")

    print("\n" + "=" * 70)
    print("Key Features Demonstrated:")
    print("=" * 70)
    print("""
    1. ✅ Transparent Integration
       - SecureAgent works as a drop-in replacement
       - No changes to agent code required
       - All tool calls automatically monitored

    2. ✅ Policy Enforcement
       - Calls are checked against your policies
       - BLOCKED calls throw SecurityException
       - FLAGGED calls are logged but allowed

    3. ✅ Complete Visibility
       - Every tool call logged to dashboard
       - Real-time monitoring and alerts
       - Anomaly detection for suspicious behavior

    4. ✅ Production Ready
       - Configurable fail-open/fail-closed modes
       - Retry logic for API calls
       - Comprehensive error handling
    """)

    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("""
    1. Install LangChain: pip install langchain langchain-openai
    2. Replace SHIELD_KEY with your actual API key
    3. Uncomment main_with_langchain() for real usage
    4. Visit https://agent-shield.com to:
       - View all agent tool calls in real-time
       - Create custom security policies
       - Set up alerts for specific patterns
       - Monitor agent behavior and anomalies
    """)


def example_with_custom_tools():
    """Example showing how to secure custom LangChain tools."""

    print("\n" + "=" * 70)
    print("Custom Tools Example")
    print("=" * 70)

    SHIELD_KEY = "agsh_your_api_key_here"
    AGENT_ID = "custom-tools-agent"

    # Mock agent
    class SimpleAgent:
        pass

    agent = SimpleAgent()

    # Wrap with AgentShield
    secure_agent = SecureAgent(
        agent=agent,
        shield_key=SHIELD_KEY,
        agent_id=AGENT_ID
    )

    # Manually wrap individual tools
    print("\nWrapping custom tools:")

    # Wrap search tool
    secure_search = secure_agent.wrap_function(web_search_tool, "web_search")
    print("  ✓ web_search_tool wrapped")

    # Wrap calculator tool
    secure_calc = secure_agent.wrap_function(calculator_tool, "calculator")
    print("  ✓ calculator_tool wrapped")

    # Wrap database tool
    secure_db = secure_agent.wrap_function(database_query_tool, "database_query")
    print("  ✓ database_query_tool wrapped")

    print("\n  All tools are now secured!")
    print("  Try calling them:")

    try:
        result = secure_search("machine learning")
        print(f"\n  search result: {result}")
    except SecurityException as e:
        print(f"\n  ✗ Search blocked: {e}")

    try:
        result = secure_calc("100 * 50")
        print(f"  calc result: {result}")
    except SecurityException as e:
        print(f"  ✗ Calculation blocked: {e}")


if __name__ == "__main__":
    # Run the mock example
    main_mock_example()

    # Run custom tools example
    example_with_custom_tools()

    print("\n" + "=" * 70)
    print("For production use with real LangChain:")
    print("  1. Uncomment main_with_langchain() function")
    print("  2. Install: pip install langchain langchain-openai")
    print("  3. Set your OpenAI API key")
    print("  4. Replace shield_key with your AgentShield key")
    print("=" * 70 + "\n")
