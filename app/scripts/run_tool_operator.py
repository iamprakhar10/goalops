"""
Command-line entry point for the MCP-native GoalOps operator.

This script runs one autonomous GoalOps attempt using MCP-discovered
tools and Groq native tool calling, then prints the run evaluation.
"""

import asyncio
from dataclasses import asdict
import json

from app.operator.evaluation import (
    evaluate_tool_operator_run,
)
from app.operator.tool_runner import (
    run_tool_operator,
)


async def main() -> None:
    """
    Run GoalOps once using MCP-native tool calling and print evaluation.
    """

    run_state = await run_tool_operator(
        max_tool_rounds=3,
        random_seed=42,
    )

    if run_state.run_id is None:
        raise ValueError(
            "Operator run did not produce a simulation run id."
        )

    evaluation = evaluate_tool_operator_run(
        run_state
    )

    print(
        "\n"
        "========================================"
    )

    print(
        "       OPERATOR RUN EVALUATION"
    )

    print(
        "========================================"
    )

    print(
        json.dumps(
            asdict(evaluation),
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )