"""
AgentShield Basic Usage Example

Demonstrates how to wrap basic Python functions with AgentShield security.
"""

from agentshield import SecureAgent, SecurityException


def web_search(query: str) -> str:
    """Simulates a web search function."""
    print(f"Searching for: {query}")
    return f"Results for '{query}': [result1, result2, result3]"


def database_query(sql: str) -> list:
    """Simulates a database query function."""
    print(f"Executing SQL: {sql}")
    return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]


def send_email(to: str, subject: str, body: str) -> bool:
    """Simulates sending an email."""
    print(f"Sending email to {to}: {subject}")
    return True


def main():
    """Main example demonstrating basic AgentShield usage."""

    # Configuration
    SHIELD_KEY = "agsh_your_api_key_here"  # Replace with your actual key
    AGENT_ID = "basic-example-agent"

    print("=" * 60)
    print("AgentShield Basic Usage Example")
    print("=" * 60)

    # Create a simple agent (mock object for this example)
    class SimpleAgent:
        """Mock agent for demonstration."""
        def __init__(self):
            self.name = "SimpleAgent"

    agent = SimpleAgent()

    # Wrap agent with AgentShield
    print(f"\n1. Initializing SecureAgent with agent_id: {AGENT_ID}")
    secure_agent = SecureAgent(
        agent=agent,
        shield_key=SHIELD_KEY,
        agent_id=AGENT_ID,
        debug=True,  # Enable debug logging
    )

    print("   ✓ SecureAgent initialized")

    # Example 1: Wrap and call a web search function
    print("\n2. Wrapping web_search function")
    secure_search = secure_agent.wrap_function(web_search, "web_search")

    try:
        print("\n   Calling secure_search('AI security')...")
        result = secure_search("AI security")
        print(f"   ✓ Success: {result}")
    except SecurityException as e:
        print(f"   ✗ BLOCKED: {e}")

    # Example 2: Wrap and call a database query function
    print("\n3. Wrapping database_query function")
    secure_db_query = secure_agent.wrap_function(database_query, "database_query")

    try:
        print("\n   Calling secure_db_query('SELECT * FROM users')...")
        result = secure_db_query("SELECT * FROM users")
        print(f"   ✓ Success: {result}")
    except SecurityException as e:
        print(f"   ✗ BLOCKED: {e}")
        print(f"      Policy: {e.policy_matched}")
        print(f"      Call ID: {e.call_id}")

    # Example 3: Wrap and call an email function
    print("\n4. Wrapping send_email function")
    secure_email = secure_agent.wrap_function(send_email, "send_email")

    try:
        print("\n   Calling secure_email(...)...")
        result = secure_email(
            to="admin@example.com",
            subject="Test Alert",
            body="This is a test email from AgentShield"
        )
        print(f"   ✓ Success: Email sent = {result}")
    except SecurityException as e:
        print(f"   ✗ BLOCKED: {e}")

    # Example 4: Demonstrating error handling
    print("\n5. Error Handling Example")
    print("\n   Testing with potentially sensitive operation...")

    def delete_data(user_id: int) -> bool:
        """Simulates deleting user data."""
        print(f"   Deleting user {user_id}...")
        return True

    secure_delete = secure_agent.wrap_function(delete_data, "delete_user_data")

    try:
        result = secure_delete(user_id=123)
        print(f"   ✓ Allowed: {result}")
    except SecurityException as e:
        print(f"   ✗ Security Policy Violation!")
        print(f"      Status: {e.status}")
        print(f"      Message: {e.message}")
        print(f"      Policy: {e.policy_matched}")
        print(f"      Call ID: {e.call_id}")
        print("\n   This call was logged in your AgentShield dashboard.")
        print("   Visit https://agent-shield.com to review.")

    print("\n" + "=" * 60)
    print("Example Complete!")
    print("=" * 60)
    print("\nNext Steps:")
    print("  1. Replace SHIELD_KEY with your actual API key")
    print("  2. Visit https://agent-shield.com to:")
    print("     - View all agent calls")
    print("     - Create security policies")
    print("     - Set up alerts")
    print("     - Monitor anomaly scores")


if __name__ == "__main__":
    # Run example
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("  - Check that your SHIELD_KEY is valid")
        print("  - Verify your network connection")
        print("  - Check API endpoint is accessible")
