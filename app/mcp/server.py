"""
GoalOps MCP server

This module exposes controlled business analytics and simulator actiosn
as MCP tools for our autonomous business-goal operator

The MCP server doesn't contain business logic itself. It uses the implemetation
of app.mcp.tools
"""

from mcp.server import MCPServer
from typing import Any

from app.mcp.tools import (
    advance_simulation,
    evaluate_business_goal,
    get_business_snapshot,
    launch_intervention,
    list_available_interventions,
)



mcp = MCPServer(
    "goalops"
)









@mcp.tool()
def business_snapshot() -> dict[str, Any]:
    """
    Inspect the current observable state of business.

    Returns current conversion, onboarding funnel, product usage,
    support evidence, simulated day, and intervention spending
    """

    return get_business_snapshot()



@mcp.tool()
def available_interventions() -> list[dict[str, Any]]:
    """
    List the business interventions currently available to the operator
    """

    return list_available_interventions()




@mcp.tool()
def run_intervention(
    intervention_name: str,
) -> dict[str, Any]:
    """
    Launch one approved intervention.

    Args:
        intervention_name:
            Exact intervention name returned by available_interventions.
    """

    return launch_intervention(
        intervention_name
    )



@mcp.tool()
def advance_time(
    days: int,
) -> dict[str, Any]:
    """
    Advance simulated business time.

    Args:
        days:
            Number of simulated days to advance
    """

    return advance_simulation(
        days
    )





@mcp.tool()
def goal_status() -> dict[str, Any]:
    """
    Evaluate the current business goal.
    """

    return evaluate_business_goal()


if __name__ == "__main__":
    mcp.run(
        transport="stdio"
    )