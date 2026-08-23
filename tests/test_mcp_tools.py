"""
Tests for the GoalOps MCP tool implementation layer.

These tests verify that MCP-facing functions expose controlled access to
business analytics, interventions, persistent simulation runs, time
advancement, and goal evaluation.

The tests use the new run_id-based simulation design instead of the old
global in-memory simulation_state object.
"""

from app.mcp.tools import (
    business_goal,
    create_business_run,
    evaluate_business_goal,
    get_business_snapshot,
    list_available_interventions,
)
from app.simulation.interventions import (
    GUIDED_INTEGRATION_HELP,
)


def test_business_snapshot_exposes_baseline_metrics() -> None:
    """
    The MCP analytics boundary should expose the known benchmark baseline
    for one persistent simulation run.
    """

    # Create a fresh persistent simulation run.
    run = create_business_run(
        random_seed=42,
    )

    run_id = run["run_id"]

    snapshot = get_business_snapshot(
        run_id=run_id,
    )

    assert snapshot["current_day"] == 0
    assert snapshot["total_spend"] == 0.0
    assert snapshot["conversion_rate"] == 30.0

    assert (
        snapshot["onboarding_funnel"]["started_trial"]
        == 20
    )


def test_intervention_catalog_is_exposed() -> None:
    """
    The operator should receive a bounded list of allowed interventions.

    The intervention catalog itself does not belong to a specific
    simulation run, so no run_id is required here.
    """

    interventions = list_available_interventions()

    names = {
        intervention["name"]
        for intervention in interventions
    }

    assert GUIDED_INTEGRATION_HELP in names


def test_goal_is_exposed_through_tool_boundary() -> None:
    """
    Goal evaluation should be available for one specific simulation run
    without exposing evaluator internals to the operator.
    """

    run = create_business_run(
        random_seed=42,
    )

    run_id = run["run_id"]

    evaluation = evaluate_business_goal(
        run_id=run_id,
    )

    assert (
        evaluation["metric_name"]
        == business_goal.metric_name
    )

    assert (
        evaluation["target_value"]
        == business_goal.target_value
    )

    assert evaluation["current_value"] == 30.0
    assert evaluation["status"] == "in_progress"

    assert (
        evaluation["budget_remaining"]
        == business_goal.max_budget
    )

    assert (
        evaluation["days_remaining"]
        == business_goal.deadline_day
    )