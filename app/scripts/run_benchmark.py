"""
Manual entry point for running the multi-seed GoalOps benchmark
"""

import asyncio
import json
from dataclasses import asdict

from app.operator.benchmark import run_benchmark


async def main() -> None:
    """
    Run a small multi-seed benchmark and print aggrgate results
    """

    benchmark = await run_benchmark(
        seeds=[
            1,
            2,
            5,
        ],
        max_tool_rounds=4,
        max_sessions_per_run=3,
        delay_between_runs=15.0,
    )

    print()
    print("=" * 60)
    print("GOALOPS BENCHMARK RESULTS")
    print("=" * 60)

    # Keep the per-run details available, but print the complete
    # benchmark as structured JSON for now
    print(
        json.dumps(
            asdict(benchmark),
            indent=2,
        )
    )



if __name__ == "__main__":
    asyncio.run(main())
