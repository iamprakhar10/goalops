"""
Command-line entry point for the autonomous GoalOps operator.

Running this module starts one autonomous business-goal attempt using
Groq for decisions and MCP for all business observations and actions.
"""

import asyncio

from app.operator.runner import run_operator


def main() -> None:
    """
    Start one autonomous GoalOps run.
    """

    asyncio.run(
        run_operator(
            max_iterations=6,
        )
    )


if __name__ == "__main__":
    main()