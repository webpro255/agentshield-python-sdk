"""
AgentShield Python SDK

Security and monitoring for AI agents. Monitor agent behavior, enforce
policies, and get real-time alerts for suspicious activity.

Example:
    >>> from agentshield import SecureAgent
    >>> from langchain.agents import create_openai_functions_agent
    >>>
    >>> # Create your agent
    >>> agent = create_openai_functions_agent(llm, tools, prompt)
    >>>
    >>> # Wrap with AgentShield
    >>> secure_agent = SecureAgent(
    ...     agent=agent,
    ...     shield_key="agsh_...",
    ...     agent_id="my-assistant"
    ... )
    >>>
    >>> # Use normally - security is automatic
    >>> result = secure_agent.invoke({"input": "Search for AI security"})
"""

__version__ = "0.1.0"

from .interceptor import SecureAgent
from .client import AgentShieldClient
from .exceptions import (
    AgentShieldException,
    SecurityException,
    APIKeyError,
    NetworkError,
    PolicyEvaluationError,
    ConfigurationError,
)

__all__ = [
    "SecureAgent",
    "AgentShieldClient",
    "AgentShieldException",
    "SecurityException",
    "APIKeyError",
    "NetworkError",
    "PolicyEvaluationError",
    "ConfigurationError",
    "__version__",
]
