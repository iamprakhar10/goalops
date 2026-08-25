"""
Manual entry point for resuming an existing GoalOps simulation run.

This script does not create a new SimulationRun.
It continues operating on the persisted business world for the
specified run ID.
"""

import asyncio

from app.operator.tool_runner import run_tool_operator


async def main() -> None:
    """
    Resume one existing active simulation run.
    """

    run_state = await run_tool_operator(
        run_id=341,
        max_tool_rounds=6,
    )

    print()
    print("=" * 50)
    print("RESUMED RUN FINISHED")
    print("=" * 50)

    print(
        "Run ID:",
        run_state.run_id,
    )

    print(
        "Final goal status:",
        run_state.final_goal_status,
    )


if __name__ == "__main__":
    asyncio.run(main())