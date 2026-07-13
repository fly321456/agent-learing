class AgentError(Exception):
    """Base error for expected runtime failures."""


class LLMError(AgentError):
    """Raised when a model response cannot be obtained or normalized."""


class RetryableLLMError(LLMError):
    """Raised for temporary model failures that may succeed on retry."""


class ToolExecutionError(AgentError):
    """Raised when a tool ran but reported an unsuccessful result."""


class WorkspaceBoundaryError(AgentError):
    """Raised when a tool path escapes the configured workspace."""
