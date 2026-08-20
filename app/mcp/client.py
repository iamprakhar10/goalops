"""
MCP client wrapper used by the Goalops autonomous operator

This module connects the operator to the GoalOps MCP server

The operator does not directly call analytics services, simulator functions,
or database code. It communicates with the simulated
business through MCP tools.
"""

from typing import Any

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

        return result.structured_content