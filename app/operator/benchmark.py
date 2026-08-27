"""
Multi-run benchmark utilities for the autonomous business operator

A benchmark executes the operator across multiple deterministic random
seeds and aggregates the resulting run evaluations

Only runs created during the benchmark are included in its statistics.
Historical simulation runs already present in the database are not included
"""

from dataclasses import dataclass, field

from app.operator.evaluation import (
    OperatorRunEvaluation,
    evaluate_tool_operator_run,
)
from app.operator.tool_runner import run_tool_operator
import asyncio

@dataclass
class BenchmarkRunResult:
    """
    Store the evaluation result for one benchmark seed.

    evaluation is None when the run could not comlpete because of an 
    execusion/provider error rather than a business outcome.

    a broken provider call can become:

    BenchmarkRunResult(
        random_seed=5,
        evaluation=None,
        execution_status="error",
        error_message="Groq BadRequestError...",
    )
    """

    random_seed: int
    evaluation: OperatorRunEvaluation | None
    execution_status: str = 'completed'
    error_message: str|None = None



@dataclass
class BenchmarkResult:
    """
    Aggregates result across multiple autonomous operator runs.
    """

    total_runs: int

    successful_runs: int
    failed_runs: int
    in_progress_runs: int

    execution_error_runs: int

    success_rate: float

    average_final_metric: float
    average_spend: float
    average_days_used: float
    average_tool_calls: float

    inspected_business_rate: float
    inspected_before_action_rate: float

    intervention_counts: dict[str, int]

    runs: list[BenchmarkRunResult] = field(
        default_factory=list
    )





async def run_benchmark(
        seeds: list[int],
        max_tool_rounds: int=12,
        delay_between_runs: float=45.0,
) -> BenchmarkResult:
    """
    Run the autonomous operator independently across multiple seeds

    Each seed creates a new isolated SimulationRun with its own
    0-company business world.

    Results are aggregated only from the runs created by this benchmark
    """
    if not seeds:
        raise ValueError(
            "Benchmark requires at leastone random seed."
        )

    run_results: list[BenchmarkRunResult] = []

    for index, seed in enumerate(seeds):
        print()
        print("=" * 60)
        print(f"BENCHMARK SEED {seed}")
        print("=" * 60)

        try:
            run_state = await run_tool_operator(
                random_seed=seed,
                max_tool_rounds=max_tool_rounds,
            )

            if run_state.run_id is None:
                raise ValueError(
                    "Operator run did not produce a simulation run id."
                )
            
            evaluation = evaluate_tool_operator_run(
                run_id=run_state.run_id,
            )

            run_results.append(
                BenchmarkRunResult(
                    random_seed=seed,
                    evaluation=evaluation,
                )
            )
            
        except Exception as exc:
            print()
            print(
                f"Benchmark run for seed {seed} "
                f"ended with an execution error:"
            )
            print(str(exc))
            run_results.append(
                BenchmarkRunResult(
                    random_seed=seed,
                    evaluation=None,
                    execution_status="error",
                    error_message=str(exc),
                )
            )

        # Avoid hammering the LLM provider between independent runs.
        if index < len(seeds) - 1:
            await asyncio.sleep(
                delay_between_runs
            )


    return aggregate_benchmark_results(
        run_results
    )




def aggregate_benchmark_results(
    run_results: list[BenchmarkRunResult],
) -> BenchmarkResult:
    """
    Aggregate benchmark run results.

    Completed business runs contribute to business metrics.

    Execution errors are counted separately and are excluded from
    averages that require a completed evaluation.
    """

    if not run_results:
        raise ValueError(
            "Benchmark requires at least one run."
        )

    total_runs = len(run_results)

    completed_results = [
        result
        for result in run_results
        if (
            result.execution_status == "completed"
            and result.evaluation is not None
        )
    ]

    successful_runs = sum(
        1
        for result in completed_results
        if result.evaluation.goal_status == "achieved"
    )

    failed_runs = sum(
        1
        for result in completed_results
        if result.evaluation.goal_status == "failed"
    )

    in_progress_runs = sum(
        1
        for result in completed_results
        if result.evaluation.goal_status == "in_progress"
    )

    execution_error_runs = sum(
        1
        for result in run_results
        if result.execution_status == "error"
    )

    # Success rate is measured against every requested benchmark run.
    #
    # Example:
    # 8 achieved + 2 execution errors out of 10 requested runs
    # = 80% overall success rate.
    success_rate = (
        successful_runs / total_runs
    ) * 100

    if completed_results:
        completed_count = len(
            completed_results
        )

        average_final_metric = sum(
            result.evaluation.final_metric
            for result in completed_results
        ) / completed_count

        average_spend = sum(
            result.evaluation.total_spend
            for result in completed_results
        ) / completed_count

        average_days_used = sum(
            result.evaluation.days_used
            for result in completed_results
        ) / completed_count

        average_tool_calls = sum(
            result.evaluation.decisions_made
            for result in completed_results
        ) / completed_count

        inspected_business_count = sum(
            1
            for result in completed_results
            if result.evaluation.inspected_business
        )

        inspected_before_action_count = sum(
            1
            for result in completed_results
            if (
                result.evaluation
                .inspected_before_first_intervention
            )
        )

        inspected_business_rate = (
            inspected_business_count
            / completed_count
        ) * 100

        inspected_before_action_rate = (
            inspected_before_action_count
            / completed_count
        ) * 100

    else:
        average_final_metric = 0.0
        average_spend = 0.0
        average_days_used = 0.0
        average_tool_calls = 0.0
        inspected_business_rate = 0.0
        inspected_before_action_rate = 0.0

    intervention_counts: dict[str, int] = {}

    for result in completed_results:
        for intervention_name in (
            result.evaluation.interventions_launched
        ):
            intervention_counts[
                intervention_name
            ] = (
                intervention_counts.get(
                    intervention_name,
                    0,
                )
                + 1
            )

    return BenchmarkResult(
        total_runs=total_runs,
        successful_runs=successful_runs,
        failed_runs=failed_runs,
        in_progress_runs=in_progress_runs,
        execution_error_runs=execution_error_runs,
        success_rate=round(
            success_rate,
            2,
        ),
        average_final_metric=round(
            average_final_metric,
            2,
        ),
        average_spend=round(
            average_spend,
            2,
        ),
        average_days_used=round(
            average_days_used,
            2,
        ),
        average_tool_calls=round(
            average_tool_calls,
            2,
        ),
        inspected_business_rate=round(
            inspected_business_rate,
            2,
        ),
        inspected_before_action_rate=round(
            inspected_before_action_rate,
            2,
        ),
        intervention_counts=intervention_counts,
        runs=run_results,
    )