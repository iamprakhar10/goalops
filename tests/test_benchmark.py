"""
Deterministic tests for multi-run benchmark aggregation.

These tests do not call Groq or run the autonomous operator.

Instead, they construct known OperatorRunEvaluation objects and verify
that benchmark aggregation calculates metrics correctly.
"""

from app.operator.benchmark import (
    BenchmarkRunResult,
    aggregate_benchmark_results,
)
from app.operator.evaluation import OperatorRunEvaluation


def make_evaluation(
    *,
    goal_status: str,
    final_metric: float,
    total_spend: float,
    days_used: int,
    decisions_made: int,
    interventions_launched: list[str],
    inspected_business: bool = True,
    inspected_before_first_intervention: bool = True,
) -> OperatorRunEvaluation:
    """
    Create a small deterministic operator evaluation for benchmark tests.
    """

    return OperatorRunEvaluation(
        goal_status=goal_status,
        final_metric=final_metric,
        target_value=40.0,
        total_spend=total_spend,
        days_used=days_used,
        decisions_made=decisions_made,
        interventions_launched=interventions_launched,
        inspected_business=inspected_business,
        inspected_before_first_intervention=(
            inspected_before_first_intervention
        ),
    )


def test_benchmark_aggregation() -> None:
    """
    Aggregate metrics should be calculated correctly across runs.
    """

    runs = [
        BenchmarkRunResult(
            random_seed=1,
            evaluation=make_evaluation(
                goal_status="achieved",
                final_metric=50.0,
                total_spend=1200.0,
                days_used=7,
                decisions_made=6,
                interventions_launched=[
                    "guided_integration_help",
                ],
            ),
        ),
        BenchmarkRunResult(
            random_seed=2,
            evaluation=make_evaluation(
                goal_status="achieved",
                final_metric=45.0,
                total_spend=1500.0,
                days_used=7,
                decisions_made=7,
                interventions_launched=[
                    "guided_integration_help",
                    "onboarding_email",
                ],
            ),
        ),
        BenchmarkRunResult(
            random_seed=3,
            evaluation=make_evaluation(
                goal_status="failed",
                final_metric=35.0,
                total_spend=2000.0,
                days_used=30,
                decisions_made=10,
                interventions_launched=[
                    "workflow_template",
                ],
                inspected_business=True,
                inspected_before_first_intervention=False,
            ),
        ),
    ]

    result = aggregate_benchmark_results(
        runs
    )

    assert result.total_runs == 3

    assert result.successful_runs == 2
    assert result.failed_runs == 1

    assert result.success_rate == 66.67

    assert result.average_final_metric == 43.33

    assert result.average_spend == 1566.67

    assert result.average_days_used == 14.67

    assert result.average_tool_calls == 7.67

    assert result.inspected_business_rate == 100.0

    assert result.inspected_before_action_rate == 66.67

    assert result.intervention_counts == {
        "guided_integration_help": 2,
        "onboarding_email": 1,
        "workflow_template": 1,
    }


def test_single_run_benchmark_aggregation() -> None:
    """
    Aggregation should also work correctly with only one run.
    """

    runs = [
        BenchmarkRunResult(
            random_seed=42,
            evaluation=make_evaluation(
                goal_status="achieved",
                final_metric=40.0,
                total_spend=300.0,
                days_used=7,
                decisions_made=6,
                interventions_launched=[
                    "onboarding_email",
                ],
            ),
        )
    ]

    result = aggregate_benchmark_results(
        runs
    )

    assert result.total_runs == 1
    assert result.successful_runs == 1
    assert result.failed_runs == 0

    assert result.success_rate == 100.0

    assert result.average_final_metric == 40.0
    assert result.average_spend == 300.0
    assert result.average_days_used == 7.0
    assert result.average_tool_calls == 6.0

    assert result.intervention_counts == {
        "onboarding_email": 1,
    }


def test_empty_benchmark_is_rejected() -> None:
    """
    Benchmark aggregation requires at least one completed run.
    """

    try:
        aggregate_benchmark_results(
            []
        )

        assert False

    except ValueError:
        pass