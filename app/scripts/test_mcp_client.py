"""
Manual MCP client smoke test for GoalOps.

This script verifies two things:

1. The GoalOps MCP client can connect to the in-process MCP server.
2. The goal_status tool returns structured Python data.

It also prints the MCP tools exposed by the server so we can inspect
their names, descriptions, input schemas, and output schemas.
"""

import asyncio

from app.mcp.client import GoalOpsMCPClient


async def main() -> None:
    """
    Connect to the GoalOps MCP server and inspect its tools.
    """

    async with GoalOpsMCPClient() as client:
        # ---------------------------------------------------------
        # TEST 1: CALL goal_status
        # ---------------------------------------------------------
        goal_status = await client.call_tool(
            "goal_status"
        )

        print("\n=== GOAL STATUS RESULT ===")
        print(goal_status)

        print("\n=== GOAL STATUS PYTHON TYPE ===")
        print(type(goal_status))

        # ---------------------------------------------------------
        # TEST 2: DISCOVER MCP TOOLS
        # ---------------------------------------------------------
        if client.client is None:
            raise RuntimeError(
                "Underlying MCP client is not connected"
            )

        tools_result = await client.client.list_tools()

        print("\n=== AVAILABLE MCP TOOLS ===")

        for tool in tools_result.tools:
            print(f"\nTOOL: {tool.name}")
            print(f"DESCRIPTION: {tool.description}")
            print(f"INPUT SCHEMA: {tool.input_schema}")
            print(f"OUTPUT SCHEMA: {tool.output_schema}")


if __name__ == "__main__":
    asyncio.run(main())