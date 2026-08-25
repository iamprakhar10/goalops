"""
Deterministic tests for multi-run benchmark aggregation.

These tests do not call Groq, MCP, the simulator, or the database.

Instead, they construct known OperatorRunEvaluation objects and verify
that benchmark aggregation correctly handles:

- achieved runs
- failed runs
- in-progress runs
- execution errors
- averages
- success rate
- inspection behavior
- intervention counts
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
    Create a deterministic operator evaluation for benchmark tests.
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
    Aggregate metrics should be calculated correctly across
    achieved, failed, and in-progress runs.
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
            execution_status="completed",
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
            execution_status="completed",
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
            execution_status="completed",
        ),
        BenchmarkRunResult(
            random_seed=4,
            evaluation=make_evaluation(
                goal_status="in_progress",
                final_metric=35.0,
                total_spend=1500.0,
                days_used=14,
                decisions_made=9,
                interventions_launched=[
                    "guided_integration_help",
                    "onboarding_email",
                ],
            ),
            execution_status="completed",
        ),
    ]

    result = aggregate_benchmark_results(
        runs
    )

    assert result.total_runs == 4

    assert result.successful_runs == 2
    assert result.failed_runs == 1
    assert result.in_progress_runs == 1
    assert result.execution_error_runs == 0

    # 2 achieved out of 4 requested benchmark runs.
    assert result.success_rate == 50.0

    # (50 + 45 + 35 + 35) / 4
    assert result.average_final_metric == 41.25

    # (1200 + 1500 + 2000 + 1500) / 4
    assert result.average_spend == 1550.0

    # (7 + 7 + 30 + 14) / 4
    assert result.average_days_used == 14.5

    # (6 + 7 + 10 + 9) / 4
    assert result.average_tool_calls == 8.0

    assert result.inspected_business_rate == 100.0

    # Three of four inspected before taking the first intervention.
    assert result.inspected_before_action_rate == 75.0

    assert result.intervention_counts == {
        "guided_integration_help": 3,
        "onboarding_email": 2,
        "workflow_template": 1,
    }


def test_execution_error_is_recorded_without_crashing_aggregation() -> None:
    """
    A provider or execution error should be counted separately.

    It must not contribute fake values to completed-run averages.
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
            execution_status="completed",
        ),
        BenchmarkRunResult(
            random_seed=2,
            evaluation=make_evaluation(
                goal_status="failed",
                final_metric=35.0,
                total_spend=2000.0,
                days_used=30,
                decisions_made=10,
                interventions_launched=[
                    "workflow_template",
                ],
                inspected_before_first_intervention=False,
            ),
            execution_status="completed",
        ),
        BenchmarkRunResult(
            random_seed=3,
            evaluation=None,
            execution_status="error",
            error_message="provider error",
        ),
    ]

    result = aggregate_benchmark_results(
        runs
    )

    assert result.total_runs == 3

    assert result.successful_runs == 1
    assert result.failed_runs == 1
    assert result.in_progress_runs == 0
    assert result.execution_error_runs == 1

    # Success rate uses all requested runs:
    #
    # 1 achieved / 3 requested = 33.33%
    assert result.success_rate == 33.33

    # Averages use only the two completed runs.
    assert result.average_final_metric == 42.5
    assert result.average_spend == 1600.0
    assert result.average_days_used == 18.5
    assert result.average_tool_calls == 8.0

    assert result.inspected_business_rate == 100.0
    assert result.inspected_before_action_rate == 50.0

    assert result.intervention_counts == {
        "guided_integration_help": 1,
        "workflow_template": 1,
    }

    assert result.runs[2].execution_status == "error"
    assert result.runs[2].evaluation is None
    assert result.runs[2].error_message == "provider error"


def test_in_progress_run_is_not_counted_as_failed() -> None:
    """
    An unfinished run should remain distinct from an actual
    business-goal failure.
    """

    runs = [
        BenchmarkRunResult(
            random_seed=5,
            evaluation=make_evaluation(
                goal_status="in_progress",
                final_metric=35.0,
                total_spend=1500.0,
                days_used=21,
                decisions_made=9,
                interventions_launched=[
                    "guided_integration_help",
                    "onboarding_email",
                ],
            ),
            execution_status="completed",
        ),
    ]

    result = aggregate_benchmark_results(
        runs
    )

    assert result.total_runs == 1

    assert result.successful_runs == 0
    assert result.failed_runs == 0
    assert result.in_progress_runs == 1
    assert result.execution_error_runs == 0

    assert result.success_rate == 0.0

    assert result.average_final_metric == 35.0
    assert result.average_spend == 1500.0
    assert result.average_days_used == 21.0
    assert result.average_tool_calls == 9.0


def test_single_successful_run_aggregation() -> None:
    """
    Aggregation should work correctly with one successful run.
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
            execution_status="completed",
        ),
    ]

    result = aggregate_benchmark_results(
        runs
    )

    assert result.total_runs == 1

    assert result.successful_runs == 1
    assert result.failed_runs == 0
    assert result.in_progress_runs == 0
    assert result.execution_error_runs == 0

    assert result.success_rate == 100.0

    assert result.average_final_metric == 40.0
    assert result.average_spend == 300.0
    assert result.average_days_used == 7.0
    assert result.average_tool_calls == 6.0

    assert result.inspected_business_rate == 100.0
    assert result.inspected_before_action_rate == 100.0

    assert result.intervention_counts == {
        "onboarding_email": 1,
    }


def test_all_runs_can_be_execution_errors() -> None:
    """
    Aggregation should still return a valid benchmark result when
    every requested run ended because of execution errors.
    """

    runs = [
        BenchmarkRunResult(
            random_seed=1,
            evaluation=None,
            execution_status="error",
            error_message="provider error",
        ),
        BenchmarkRunResult(
            random_seed=2,
            evaluation=None,
            execution_status="error",
            error_message="another provider error",
        ),
    ]

    result = aggregate_benchmark_results(
        runs
    )

    assert result.total_runs == 2

    assert result.successful_runs == 0
    assert result.failed_runs == 0
    assert result.in_progress_runs == 0
    assert result.execution_error_runs == 2

    assert result.success_rate == 0.0

    # There are no completed evaluations from which to calculate
    # business averages.
    assert result.average_final_metric == 0.0
    assert result.average_spend == 0.0
    assert result.average_days_used == 0.0
    assert result.average_tool_calls == 0.0

    assert result.inspected_business_rate == 0.0
    assert result.inspected_before_action_rate == 0.0

    assert result.intervention_counts == {}


def test_empty_benchmark_is_rejected() -> None:
    """
    Benchmark aggregation requires at least one requested run.
    """

    try:
        aggregate_benchmark_results(
            []
        )

        assert False

    except ValueError:
        pass