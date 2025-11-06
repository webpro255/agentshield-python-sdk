"""
AgentShield Tool Interceptor

Wraps agent tools to intercept calls, enforce security policies,
and log activity to AgentShield.
"""

import time
import logging
import functools
from typing import Any, Callable, Optional, Dict

from .client import AgentShieldClient
from .exceptions import SecurityException, ConfigurationError

logger = logging.getLogger(__name__)


class SecureAgent:
    """
    Wraps an AI agent to add security monitoring and policy enforcement.

    SecureAgent intercepts tool/function calls, sends them to AgentShield
    for evaluation, and enforces policy decisions (BLOCK/ALLOW/FLAG).

    Works transparently with any agent framework (LangChain, OpenAI, custom).
    """

    def __init__(
        self,
        agent: Any,
        shield_key: str,
        agent_id: str,
        api_url: Optional[str] = None,
        timeout: int = 30,
        debug: bool = False,
        fail_open: bool = False,
    ):
        """
        Initialize SecureAgent wrapper.

        Args:
            agent: The agent to wrap (LangChain agent, OpenAI assistant, etc.)
            shield_key: Your AgentShield API key (starts with 'agsh_')
            agent_id: Unique identifier for this agent
            api_url: Optional custom API endpoint
            timeout: API request timeout in seconds (default: 30)
            debug: Enable debug logging (default: False)
            fail_open: If True, allow calls when API is unavailable (default: False)

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not shield_key:
            raise ConfigurationError("shield_key is required")

        if not agent_id:
            raise ConfigurationError("agent_id is required")

        self.agent = agent
        self.shield_key = shield_key
        self.agent_id = agent_id
        self.fail_open = fail_open
        self.debug = debug

        # Initialize API client
        self.client = AgentShieldClient(
            shield_key=shield_key,
            agent_id=agent_id,
            api_url=api_url,
            timeout=timeout,
            debug=debug,
        )

        # Wrap agent tools
        self._wrap_agent_tools()

        logger.info(f"SecureAgent initialized: agent_id={agent_id}")

    def _wrap_agent_tools(self):
        """
        Detect and wrap agent tools based on agent type.
        """
        # Try LangChain AgentExecutor
        if hasattr(self.agent, "tools"):
            logger.debug("Detected LangChain agent with tools")
            self._wrap_langchain_tools()

        # Try LangChain LCEL Runnable
        elif hasattr(self.agent, "invoke") and hasattr(self.agent, "batch"):
            logger.debug("Detected LangChain LCEL runnable")
            self._wrap_lcel_invoke()

        # Try OpenAI Assistant
        elif hasattr(self.agent, "create") or hasattr(self.agent, "run"):
            logger.debug("Detected OpenAI-style agent")
            # OpenAI assistants are wrapped at the function call level
            pass

        else:
            logger.warning(
                "Could not detect agent type. Manual tool wrapping may be required."
            )

    def _wrap_langchain_tools(self):
        """Wrap LangChain tools."""
        if not hasattr(self.agent, "tools"):
            return

        original_tools = self.agent.tools
        wrapped_tools = []

        for tool in original_tools:
            # Wrap the tool's _run or _arun method
            if hasattr(tool, "_run"):
                original_run = tool._run
                tool._run = self._create_wrapped_sync_function(
                    original_run,
                    tool_name=getattr(tool, "name", tool.__class__.__name__)
                )

            if hasattr(tool, "_arun"):
                original_arun = tool._arun
                tool._arun = self._create_wrapped_async_function(
                    original_arun,
                    tool_name=getattr(tool, "name", tool.__class__.__name__)
                )

            wrapped_tools.append(tool)

        self.agent.tools = wrapped_tools
        logger.debug(f"Wrapped {len(wrapped_tools)} LangChain tools")

    def _wrap_lcel_invoke(self):
        """Wrap LangChain LCEL runnable invoke method."""
        if hasattr(self.agent, "invoke"):
            original_invoke = self.agent.invoke
            self.agent.invoke = self._create_wrapped_sync_function(
                original_invoke,
                tool_name="invoke"
            )
            logger.debug("Wrapped LCEL invoke method")

    def _create_wrapped_sync_function(
        self,
        func: Callable,
        tool_name: str
    ) -> Callable:
        """
        Create a wrapped version of a synchronous function.

        Args:
            func: Original function to wrap
            tool_name: Name of the tool for logging

        Returns:
            Wrapped function that enforces AgentShield policies
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract arguments for logging
            tool_args = self._extract_args(args, kwargs)

            # Call AgentShield API for policy check
            start_time = time.time()

            try:
                response = self.client.log_agent_call(
                    tool_name=tool_name,
                    tool_args=tool_args,
                )

                status = response.get("status", "ALLOWED")
                call_id = response.get("call_id")
                policy_matched = response.get("policy_matched")
                message = response.get("message", "")

                logger.debug(
                    f"Policy check: tool={tool_name}, status={status}, "
                    f"call_id={call_id}"
                )

                # Handle BLOCKED
                if status == "BLOCKED":
                    logger.warning(
                        f"Tool call BLOCKED: {tool_name} | {message}"
                    )
                    raise SecurityException(
                        message=message or f"Tool '{tool_name}' blocked by security policy",
                        policy_matched=policy_matched,
                        call_id=call_id,
                        status=status,
                    )

                # Handle FLAGGED
                if status == "FLAGGED":
                    logger.warning(
                        f"Tool call FLAGGED: {tool_name} | {message}"
                    )
                    # Continue execution but log warning

                # Handle PENDING_APPROVAL
                if status == "PENDING_APPROVAL":
                    logger.info(
                        f"Tool call requires approval: {tool_name} | {message}"
                    )
                    raise SecurityException(
                        message=message or f"Tool '{tool_name}' requires manual approval",
                        policy_matched=policy_matched,
                        call_id=call_id,
                        status=status,
                    )

                # ALLOWED - execute the tool
                result = func(*args, **kwargs)

                # Log execution time
                execution_time_ms = int((time.time() - start_time) * 1000)
                logger.debug(
                    f"Tool executed: {tool_name} | {execution_time_ms}ms"
                )

                return result

            except (SecurityException, Exception) as e:
                # Re-raise security exceptions
                if isinstance(e, SecurityException):
                    raise

                # Handle network/API errors based on fail_open setting
                logger.error(f"AgentShield API error: {str(e)}")

                if self.fail_open:
                    logger.warning(
                        f"Fail-open mode: executing {tool_name} despite API error"
                    )
                    return func(*args, **kwargs)
                else:
                    # Fail closed - block execution
                    raise SecurityException(
                        message=f"Cannot verify security policy due to API error: {str(e)}",
                        policy_matched=None,
                        call_id=None,
                        status="ERROR",
                    )

        return wrapper

    def _create_wrapped_async_function(
        self,
        func: Callable,
        tool_name: str
    ) -> Callable:
        """
        Create a wrapped version of an async function.

        Args:
            func: Original async function to wrap
            tool_name: Name of the tool for logging

        Returns:
            Wrapped async function that enforces AgentShield policies
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract arguments for logging
            tool_args = self._extract_args(args, kwargs)

            # Call AgentShield API for policy check (sync call in async context)
            start_time = time.time()

            try:
                response = self.client.log_agent_call(
                    tool_name=tool_name,
                    tool_args=tool_args,
                )

                status = response.get("status", "ALLOWED")
                call_id = response.get("call_id")
                policy_matched = response.get("policy_matched")
                message = response.get("message", "")

                logger.debug(
                    f"Policy check (async): tool={tool_name}, status={status}, "
                    f"call_id={call_id}"
                )

                # Handle BLOCKED
                if status == "BLOCKED":
                    logger.warning(
                        f"Tool call BLOCKED: {tool_name} | {message}"
                    )
                    raise SecurityException(
                        message=message or f"Tool '{tool_name}' blocked by security policy",
                        policy_matched=policy_matched,
                        call_id=call_id,
                        status=status,
                    )

                # Handle FLAGGED
                if status == "FLAGGED":
                    logger.warning(
                        f"Tool call FLAGGED: {tool_name} | {message}"
                    )

                # Handle PENDING_APPROVAL
                if status == "PENDING_APPROVAL":
                    logger.info(
                        f"Tool call requires approval: {tool_name} | {message}"
                    )
                    raise SecurityException(
                        message=message or f"Tool '{tool_name}' requires manual approval",
                        policy_matched=policy_matched,
                        call_id=call_id,
                        status=status,
                    )

                # ALLOWED - execute the tool
                result = await func(*args, **kwargs)

                # Log execution time
                execution_time_ms = int((time.time() - start_time) * 1000)
                logger.debug(
                    f"Tool executed (async): {tool_name} | {execution_time_ms}ms"
                )

                return result

            except (SecurityException, Exception) as e:
                # Re-raise security exceptions
                if isinstance(e, SecurityException):
                    raise

                # Handle network/API errors based on fail_open setting
                logger.error(f"AgentShield API error: {str(e)}")

                if self.fail_open:
                    logger.warning(
                        f"Fail-open mode: executing {tool_name} despite API error"
                    )
                    return await func(*args, **kwargs)
                else:
                    # Fail closed - block execution
                    raise SecurityException(
                        message=f"Cannot verify security policy due to API error: {str(e)}",
                        policy_matched=None,
                        call_id=None,
                        status="ERROR",
                    )

        return wrapper

    def _extract_args(self, args: tuple, kwargs: dict) -> Dict[str, Any]:
        """
        Extract and serialize arguments for logging.

        Args:
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Dictionary of serialized arguments
        """
        tool_args = {}

        # Add positional args
        if args:
            for i, arg in enumerate(args):
                tool_args[f"arg_{i}"] = self._serialize_value(arg)

        # Add keyword args
        if kwargs:
            for key, value in kwargs.items():
                tool_args[key] = self._serialize_value(value)

        return tool_args

    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize a value for JSON transmission.

        Args:
            value: Value to serialize

        Returns:
            JSON-serializable value
        """
        # Handle common types
        if isinstance(value, (str, int, float, bool, type(None))):
            return value

        if isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]

        if isinstance(value, dict):
            return {
                str(k): self._serialize_value(v)
                for k, v in value.items()
            }

        # Convert other types to string
        return str(value)

    def wrap_function(self, func: Callable, tool_name: Optional[str] = None) -> Callable:
        """
        Manually wrap a function with AgentShield security.

        Use this method to wrap custom functions or tools that weren't
        automatically detected.

        Args:
            func: Function to wrap
            tool_name: Optional name for the tool (defaults to function name)

        Returns:
            Wrapped function

        Example:
            >>> secure_agent = SecureAgent(agent, shield_key, agent_id)
            >>> secure_search = secure_agent.wrap_function(google_search, "web_search")
            >>> result = secure_search("AI security")
        """
        name = tool_name or func.__name__
        logger.debug(f"Manually wrapping function: {name}")
        return self._create_wrapped_sync_function(func, name)

    def __getattr__(self, name: str) -> Any:
        """
        Proxy attribute access to wrapped agent.

        Allows SecureAgent to be used as a drop-in replacement for the
        original agent.
        """
        return getattr(self.agent, name)

    def __del__(self):
        """Cleanup on deletion."""
        if hasattr(self, "client"):
            self.client.close()
