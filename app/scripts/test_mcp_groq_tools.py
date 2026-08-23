"""
Manual smoke test for MCP-to-Groq tool discovery.

This script verifies that GoalOps can:

1. discover tools from the MCP server,
2. convert those MCP definitions into Groq-compatible tool schemas.

No LLM request is made yet.
"""

import asyncio
import json

from app.mcp.client import GoalOpsMCPClient
from app.operator.tool_adapter import (
    mcp_tools_to_groq,
)


async def main() -> None:
    """
    Discover MCP tools and print their Groq representations.
    """

    async with GoalOpsMCPClient() as mcp_client:

        mcp_tools = await mcp_client.list_tools()

        groq_tools = mcp_tools_to_groq(
            mcp_tools
        )

        print(
            json.dumps(
                groq_tools,
                indent=2,
            )
        )


if __name__ == "__main__":
    asyncio.run(
        main()
    )