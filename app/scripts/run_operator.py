"""
Command-line entry point for the autonomous GoalOps operator.

This script executes one autonomous business-goal run and prints an
objective evaluation after the run finishes.
"""

import asyncio
from dataclasses import asdict
import json

from app.operator.evaluation import evaluate_operator_run
from app.operator.runner import run_operator


async def main() -> None:
    """
    Run GoalOps once and print its evaluation.
    """

    run_state = await run_operator(
        max_iterations=8,
    )

    evaluation = evaluate_operator_run(
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