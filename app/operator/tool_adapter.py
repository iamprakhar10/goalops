"""
Adapters betwen MCP tool definitions and Groq tool definition

MCP and Groq both describes callable tools using names and descriptions,
and JSON shemas, but their outer data structures are different

This module converts dynimacally discovered MCP tools into the format
expected by Groq's local tool-calling API
"""

from typing import Any




def mcp_tools_to_groq(
    mcp_tools,
):
    """
    Converts MCP-dicovered tools into Groq function definitions

    Args:
        mcp_tools:
            The tools returned by MCP client's list_tools() call

    Returns:
        Tool definition that can be passed directly to Groq
    """

    groq_tools: list[dict[str, Any]] = []

    for tool in mcp_tools:

        groq_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": (
                        tool.description or ""
                    ),
                    "parameters": tool.input_schema,
                },
            }
        )

    return groq_tools
