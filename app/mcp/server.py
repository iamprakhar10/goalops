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
    create_business_run
)



mcp = MCPServer(
    "goalops"
)





# dict[str, Any]
# provides a proper generic object type from which the MCP server can
# construct an output schema. Current MCP documentation describes
# structured_content as the JSON form matching the tool's declared 
# output schema

@mcp.tool()
def business_snapshot(
    run_id: int,
) -> dict[str, Any]:
    """
    Inspect the current observable state of business.

    Returns current conversion, onboarding funnel, product usage,
    support evidence, simulated day, and intervention spending
    """

    return get_business_snapshot(
        run_id
    )




@mcp.tool()
def create_run(
    random_seed: int = 42,
) -> dict[str, Any]:
    """
    Creates a new persistent GoalOps simulation run
    """

    return create_business_run(random_seed=random_seed)





@mcp.tool()
def available_interventions() -> list[dict[str, Any]]:
    """
    List the business interventions currently available to the operator
    """

    return list_available_interventions()




@mcp.tool()
def run_intervention(
    intervention_name: str,
    run_id: int,
) -> dict[str, Any]:
    """
    Launch one approved intervention.

    Args:
        intervention_name:
            Exact intervention name returned by available_interventions.
    """

    return launch_intervention(
        intervention_name=intervention_name,
        run_id=run_id
    )



@mcp.tool()
def advance_time(
    days: int,
    run_id: int,
) -> dict[str, Any]:
    """
    Advance simulated business time.

    Args:
        days:
            Number of simulated days to advance
    """

    return advance_simulation(
        days=days,
        run_id=run_id,
    )





@mcp.tool()
def goal_status(
    run_id: int,
) -> dict[str, Any]:
    """
    Evaluate the current business goal.
    """

    return evaluate_business_goal(
        run_id=run_id,
    )


if __name__ == "__main__":
    mcp.run(
        transport="stdio"
    )
    