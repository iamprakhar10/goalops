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


@dataclass
class BenchmarkRunResult:
    """
    Store the evaluation result for one benchmark seed.
    """

    random_seed: int
    evaluation: OperatorRunEvaluation



@dataclass
class BenchmarkResult:
    """
    Aggregates result across multiple autonomous operator runs.
    """

    total_runs: int

    successful_runs: int
    failed_runs: int

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

    for seed in seeds:
        print()
        print("=" * 60)
        print(f"BENCHMARK SEED {seed}")
        print("=" * 60)

        run_state = await run_tool_operator(
            random_seed=seed,
            max_tool_rounds=max_tool_rounds,
        )

        evaluation = evaluate_tool_operator_run(
            run_state=run_state,
        )

        run_results.append(
            BenchmarkRunResult(
                random_seed=seed,
                evaluation=evaluation,
            )
        )

    total_runs = len(run_results)

    successful_runs = sum(
        1
        for result in run_results
        if result.evaluation.goal_status == 'achieved'
    )

    failed_runs = sum(
        1
        for result in run_results
        if result.evaluation.goal_status == 'failed'
    )

    success_rate = (
        successful_runs/total_runs
    )*100

    average_final_metric = sum(
        result.evaluation.final_metric
        for result in run_results
    )/total_runs

    average_spend = sum(
        result.evaluation.total_spend
        for result in run_results
    ) / total_runs

    average_days_used = sum(
        result.evaluation.days_used
        for result in run_results
    ) / total_runs

    average_tool_calls = sum(
        result.evaluation.decisions_made
        for result in run_results
    ) / total_runs

    inspected_business_count = sum(
        1
        for result in run_results
        if result.evaluation.inspected_business
    )

    inspected_before_action_count = sum(
        1
        for result in run_results
        if result.evaluation.inspected_before_first_intervention
    )

    inspected_business_rate = (
        inspected_business_count
        / total_runs
    ) * 100

    inspected_before_action_rate = (
        inspected_before_action_count
        / total_runs
    ) * 100

    intervention_counts: dict[str, int] = {}

    for result in run_results:
        for intervention_name in (
            result.evaluation.interventions_launched
        ):
            intervention_counts[
                intervention_name
            ] = (
                intervention_counts.get(
                    intervention_name,
                    0
                )
                + 1
            )

    return BenchmarkResult(
        total_runs=total_runs,
        successful_runs=successful_runs,
        failed_runs=failed_runs,
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