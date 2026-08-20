"""
MCP client wrapper used by the Goalops autonomous operator

This module connects the operator to the GoalOps MCP server

The operator does not directly call analytics services, simulator functions,
or database code. It communicates with the simulated
business through MCP tools.
"""

from typing import Any
import json

from mcp import Client
from mcp.types import TextContent

from app.mcp.server import mcp







class GoalOpsMCPClient:
    """
    Wrapper around the MCP client used by the operator

    The client connects directly to the GoalOps MCP server in memory.

    Even though both pieces currently live in the same python project,
    communication still happens through MCP interface
    """
    def __init__(self) -> None:
        """
        Create the wrapper.

        The actual MCP connection is opened when entering
        the async context manager.
        """

        self._client_context = None
        self.client: Client | None = None


    async def __aenter__(
            self,
    ) -> 'GoalOpsMCPClient':
        """
        Open the MCP connection.
        """

        self._client_context = Client(mcp)
        self.client = await self._client_context.__aenter__()

        return self


    async def __aexit__(
            self, 
            exc_type, 
            exc_value, 
            traceback,):
        """
        Close the MCP connection.
        """

        if self._client_context is not None:
            await self._client_context.__aexit__(
                exc_type,
                exc_value,
                traceback,
            )


    async def call_tool(
            self, 
            tool_name: str,
            arguments: dict[str, Any] | None = None,
    ) -> Any:
        """
        Calls one MCP tool and returns it's structured result.

        Args:
            tool_name:
                Name of the MCP tool.

            arguments:
                Arguments given to that tool.

        Raises:
            RuntimeError:
                If the MCP tool reports an error.
        """

        if self.client is None:
            raise RuntimeError(
                "MCP client is not connected"
            )

        result = await self.client.call_tool(
            tool_name,
            arguments or {}
        )

        if result.is_error:
            error_messages: list[str] = []

            for block in result.content:

                if isinstance(
                    block,
                    TextContent,
                ):
                    error_messages.append(
                        block.text
                    )
            raise RuntimeError(
                f"MCP tool '{tool_name}' failed: "
                + " ".join(error_messages)
            )

        # -----------------------------------------------------
        # BEST CASE:
        # MCP returned real structured content.
        # -----------------------------------------------------

        if result.structured_content is not None:
            return result.structured_content

        # -----------------------------------------------------
        # FALLBACK:
        # MCP returned JSON as text instead.
        # -----------------------------------------------------

        text_blocks = [
            block.text
            for block in result.content
            if isinstance(
                block,
                TextContent,
            )
        ]

        if not text_blocks:
            raise RuntimeError(
                f"MCP tool '{tool_name}' returned no usable content"
            )

        text_result = "\n".join(
            text_blocks
        )
        try:
            return json.loads(
                text_result
            )

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"MCP tool '{tool_name}' returned "
                "non-JSON text instead of structured data: "
                f"{text_result}"
            ) from exc


#     So if MCP gives:

# '{"status":"in_progress","current_value":30.0,...}'

# we convert it into:

# {
#     "status": "in_progress",
#     "current_value": 30.0,
# }

# and then this works:

# goal_status["status"]